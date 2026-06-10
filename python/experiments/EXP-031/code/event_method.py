"""EXP-027 event-level evaluation method: sparse-event substrate + reused inference.

Pure, deterministic helpers for the EXP-027 calibration (see analysis-plan.md).
This module holds the only new logic in EXP-027:

  * a synthetic **sparse-event** substrate — placebo event placement inside real
    EXP-020 regimes, a structurally different block-permuted null, and an additive
    per-event planted drift; and
  * the per-draw **event-level** decision pipeline, which reuses the EXP-021
    inference *unchanged in structure* (instrument-averaged equal-weight effect,
    regime-cluster bootstrap CI, stratified paired sign-permutation, Holm across
    domains, Evidence-FOR rule) but operates on per-draw NumPy arrays for speed.

Discipline enforced here (each maps to a documented prior-run failure mode):

  * **per-EVENT** unit only — denominators are reportable matched events, never
    bars; no per-bar floor or frozen per-bar suite is referenced anywhere;
  * **anti-overfitting** — the signal under test is entirely synthetic; this module
    never touches real AVWAP event outcomes;
  * **look-ahead-safe** — placement/matching use only bar-time regime/anchor info;
    forward returns are outcomes; the planted drift is added to outcomes only;
  * **zero-baseline** — the null per-event excess is exactly 0 bps; rates use Wilson
    intervals; a non-recovered MDE is non-finite, never 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Method constants (the frozen event-level method definition)
# --------------------------------------------------------------------------- #
HORIZONS: tuple[int, ...] = (1, 3, 6)          # registered EXP-021 horizon family
PRIMARY_HORIZON: int = 3                        # confirmatory horizon
MAX_HORIZON: int = max(HORIZONS)

MAX_CONTROLS: int = 5
MIN_CONTROLS: int = 3
EXCLUSION_BARS: int = 6

MIN_REPORTABLE_EVENTS: int = 30
MIN_DIRECTION_EVENTS: int = 8
DOMAIN_MIN_INSTRUMENTS: int = 3

CI_PERCENTILES: tuple[float, float] = (2.5, 97.5)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellPrecompute:
    """Draw-independent precompute for one (instrument, domain) cell.

    All arrays are real first-70% analysis-set quantities computed once. A draw
    reduces to index selection + gather over these.
    """

    instrument: str
    domain: str
    n: int
    log_close: np.ndarray              # (n,) log real Close
    bar_log_returns: np.ndarray        # (n-1,) per-bar real log returns
    block_length: int                  # train-estimated block length (N2 null)
    regime_id: np.ndarray              # (R,) int
    regime_dir: np.ndarray             # (R,) int in {-1, +1}
    regime_start: np.ndarray           # (R,) int (== confirm_idx)
    regime_end: np.ndarray             # (R,) int
    regime_anchor: np.ndarray          # (R,) int
    dlog_real: dict[int, np.ndarray]   # h -> (n,) forward log diff (nan past end)


@dataclass
class CellEvents:
    """Reportable matched placebo events from one cell/draw."""

    idx: np.ndarray                    # (E,) trigger indices
    direction: np.ndarray              # (E,) int {-1,+1}
    regime: np.ndarray                 # (E,) regime id
    paired_diff: dict[int, np.ndarray] # h -> (E,) event-minus-control-mean bps (g=0)
    event_primary_bps: np.ndarray      # (E,) direction-signed primary event return (g=0)
    control_primary_bps: np.ndarray    # (E,) matched-control mean primary return
    n_bull: int
    n_bear: int


# --------------------------------------------------------------------------- #
# Forward returns (outcomes only)
# --------------------------------------------------------------------------- #
def forward_logdiff_from_close(log_close: np.ndarray, h: int) -> np.ndarray:
    """Forward h-bar log difference per bar; non-finite where future bars run out."""
    n = log_close.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if h < n:
        out[: n - h] = log_close[h:] - log_close[: n - h]
    return out


def forward_logdiff_from_returns(returns: np.ndarray, h: int, n: int) -> np.ndarray:
    """Forward h-bar log diff reconstructed from a per-bar return series (N2 null).

    ``returns`` has length ``n-1``; cumulative log level ``L`` has length ``n`` with
    ``L[0]=0``. ``dlog[i] = L[i+h]-L[i] = sum(returns[i:i+h])`` for ``i+h <= n-1``.
    """
    level = np.concatenate([[0.0], np.cumsum(returns)]) if returns.size else np.zeros(n)
    out = np.full(n, np.nan, dtype=float)
    if h < n:
        out[: n - h] = level[h:] - level[: n - h]
    return out


def block_permute_returns(returns: np.ndarray, block_length: int, rng: np.random.Generator) -> np.ndarray:
    """Circular moving-block bootstrap of a return series (vectorized).

    Preserves short-range autocorrelation/volatility scale while destroying the
    original index->return association — the structurally different N2 null.
    """
    n = returns.shape[0]
    if n == 0:
        return returns.copy()
    bl = max(1, min(int(block_length), n))
    n_blocks = int(math.ceil(n / bl))
    starts = rng.integers(0, n, size=n_blocks)
    offsets = np.arange(bl)
    idx = ((starts[:, None] + offsets[None, :]) % n).reshape(-1)[:n]
    return np.asarray(returns[idx], dtype=float)


# --------------------------------------------------------------------------- #
# Sparse placebo placement (look-ahead-safe; clustered to emulate pyramids)
# --------------------------------------------------------------------------- #
def place_regime_triggers(
    start: int,
    end: int,
    n: int,
    p_trig: float,
    pyramid_frac: float,
    pyramid_span: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Deterministically place placebo triggers in one regime's eligible interior.

    Eligible interior is ``(start, min(end, n-1-MAX_HORIZON)]`` so every placed
    event has valid future bars at all horizons. ``n_trig = round(p_trig*pool)``
    is split into uniformly placed seeds and ``pyramid_frac`` follow-ons placed
    within ``±pyramid_span`` of a seed (clustering that the regime-cluster
    bootstrap must absorb). Returns a sorted unique int index array.
    """
    hi = min(int(end), n - 1 - MAX_HORIZON)
    lo = int(start) + 1
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    pool = np.arange(lo, hi + 1, dtype=np.int64)
    pool_size = pool.shape[0]
    n_trig = int(round(p_trig * pool_size))
    if n_trig <= 0:
        return np.empty(0, dtype=np.int64)
    n_trig = min(n_trig, pool_size)
    n_seed = min(max(1, int(round(n_trig * (1.0 - pyramid_frac)))), pool_size)
    seeds = rng.choice(pool, size=n_seed, replace=False)
    n_pyr = n_trig - n_seed
    if n_pyr > 0:
        base = seeds[rng.integers(0, n_seed, size=n_pyr * 2)]   # over-generate, dedup absorbs collisions
        off = rng.integers(-pyramid_span, pyramid_span + 1, size=base.size)
        cand = base + off
        pyr = cand[(off != 0) & (cand >= lo) & (cand <= hi)]
        chosen = np.unique(np.concatenate([seeds, pyr]))
    else:
        chosen = np.unique(seeds)
    if chosen.size > n_trig:                                    # deterministic random trim to target
        chosen = np.sort(rng.choice(chosen, size=n_trig, replace=False))
    return chosen.astype(np.int64)


def build_near_trigger(n: int, triggers: np.ndarray) -> np.ndarray:
    """Boolean mask: bars within ``EXCLUSION_BARS`` of any placebo trigger (vectorized)."""
    near = np.zeros(n, dtype=bool)
    if triggers.size == 0:
        return near
    for offset in range(-EXCLUSION_BARS, EXCLUSION_BARS + 1):   # 13 vectorized writes, not per-trigger
        pos = triggers + offset
        pos = pos[(pos >= 0) & (pos < n)]
        near[pos] = True
    return near


def eligible_controls(start: int, end: int, n: int, is_trigger: np.ndarray, near: np.ndarray) -> np.ndarray:
    """Sorted eligible control indices in ``(start, end]``: not a trigger, outside the
    exclusion window, and with valid future bars at every horizon."""
    hi = min(int(end), n - 1 - MAX_HORIZON)
    lo = int(start) + 1
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    cand = np.arange(lo, hi + 1, dtype=np.int64)
    keep = ~is_trigger[cand] & ~near[cand]
    return cand[keep]


def nearest_controls(eligible_c: np.ndarray, events_t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized nearest-``MAX_CONTROLS`` control selection within a regime.

    Causally equivalent to EXP-021 ``select_controls``: within a regime the
    anchor-age key and the timestamp key both reduce to ``|c - t|`` (one anchor per
    regime), so selection is the nearest eligible bars by index with ties broken by
    the lower index. Two-pointer expansion (<= MAX_CONTROLS steps, vectorized over
    events). Returns ``(controls[E, MAX_CONTROLS] padded -1, counts[E])``.
    """
    e = events_t.shape[0]
    out = np.full((e, MAX_CONTROLS), -1, dtype=np.int64)
    c = eligible_c.shape[0]
    if e == 0 or c == 0:
        return out, np.zeros(e, dtype=np.int64)
    pos = np.searchsorted(eligible_c, events_t)     # first eligible >= t (t is a trigger, never eligible)
    left = pos - 1
    right = pos
    big = np.iinfo(np.int64).max
    for k in range(MAX_CONTROLS):
        has_left = left >= 0
        has_right = right < c
        d_left = np.where(has_left, events_t - eligible_c[np.clip(left, 0, c - 1)], big)
        d_right = np.where(has_right, eligible_c[np.clip(right, 0, c - 1)] - events_t, big)
        choose_left = has_left & (d_left <= d_right)        # tie -> left (lower index)
        choose_right = (~choose_left) & has_right
        sel = np.where(
            choose_left,
            eligible_c[np.clip(left, 0, c - 1)],
            np.where(choose_right, eligible_c[np.clip(right, 0, c - 1)], -1),
        )
        out[:, k] = sel
        left = np.where(choose_left, left - 1, left)
        right = np.where(choose_right, right + 1, right)
    counts = (out >= 0).sum(axis=1)
    return out, counts


def reference_select_controls(eligible_c: np.ndarray, t: int) -> list[int]:
    """Reference (EXP-021-style) nearest-control selection for the equivalence check."""
    if eligible_c.size == 0:
        return []
    keys = [(abs(int(cc) - t), int(cc)) for cc in eligible_c]
    order = sorted(range(eligible_c.size), key=lambda k: keys[k])
    return [int(eligible_c[k]) for k in order[:MAX_CONTROLS]]


def verify_control_matching() -> bool:
    """Assert the vectorized ``nearest_controls`` equals the EXP-021-style reference.

    Self-contained equivalence guard (no market data). The vectorized two-pointer is
    the linchpin of the reused inference, so this check fails loudly before any draw
    runs. Cases cover: (a) candidates only on one side of the trigger (boundary),
    (b) two-sided equal-distance ties (must resolve to the lower index),
    (c) a normal interior trigger that fills MAX_CONTROLS, and a fewer-than-MAX case.

    Returns
    -------
    bool
        ``True`` if every case matches the reference exactly.

    Raises
    ------
    ValueError
        On any mismatch between the vectorized and reference selection.
    """
    cases: list[tuple[np.ndarray, int]] = [
        (np.array([10, 11, 12, 13, 14]), 5),       # (a) candidates only above
        (np.array([10, 11, 12, 13, 14]), 20),      # (a) candidates only below
        (np.array([8, 9, 11, 12]), 10),            # (b) two-sided equal-distance ties
        (np.array([1, 3, 5, 7, 9, 11, 13]), 8),    # (c) interior, full MAX_CONTROLS
        (np.array([10, 11]), 5),                   # fewer than MAX_CONTROLS available
    ]
    for eligible, t in cases:
        elig = eligible.astype(np.int64)
        controls, _counts = nearest_controls(elig, np.array([t], dtype=np.int64))
        got = [int(c) for c in controls[0] if c >= 0]
        expected = reference_select_controls(elig, int(t))
        if got != expected:
            raise ValueError(
                f"control-matching equivalence FAILED for eligible={elig.tolist()} "
                f"t={t}: vectorized={got} != reference={expected}"
            )
    return True


# --------------------------------------------------------------------------- #
# Per-cell simulation (one instrument/domain, one draw)
# --------------------------------------------------------------------------- #
def _control_mean(controls: np.ndarray, counts: np.ndarray, signed: np.ndarray) -> np.ndarray:
    """Mean signed return over each event's matched controls (segment mean)."""
    e = controls.shape[0]
    flat = controls.reshape(-1)
    valid = flat >= 0
    event_ids = np.repeat(np.arange(e), MAX_CONTROLS)[valid]
    vals = signed[flat[valid]]
    sums = np.bincount(event_ids, weights=vals, minlength=e)
    denom = np.where(counts > 0, counts, 1)
    out = sums / denom
    out[counts == 0] = np.nan
    return out


def simulate_cell(
    pre: CellPrecompute,
    dlog: dict[int, np.ndarray],
    p_trig: float,
    rng: np.random.Generator,
    pyramid_frac: float,
    pyramid_span: int,
) -> CellEvents:
    """Place placebo events in one cell, match controls, compute per-event paired diffs.

    Pure given ``rng``. ``dlog`` carries the active forward-return arrays (real for
    N1; block-permuted for N2). No planted edge here — the additive edge is applied
    downstream as a pure shift of the paired differences.
    """
    n = pre.n
    # 1. placement (per regime, look-ahead-safe interior)
    trig_lists = [
        place_regime_triggers(int(s), int(e), n, p_trig, pyramid_frac, pyramid_span, rng)
        for s, e in zip(pre.regime_start, pre.regime_end)
    ]
    triggers = np.concatenate(trig_lists) if trig_lists else np.empty(0, dtype=np.int64)
    triggers = np.unique(triggers)
    if triggers.size == 0:
        empty = np.empty(0)
        return CellEvents(empty.astype(np.int64), empty.astype(np.int64), empty.astype(np.int64),
                          {h: empty for h in HORIZONS}, empty, empty, 0, 0)
    is_trigger = np.zeros(n, dtype=bool)
    is_trigger[triggers] = True
    near = build_near_trigger(n, triggers)

    # 2. per-regime matched controls + per-event paired diffs
    ev_idx, ev_dir, ev_reg = [], [], []
    pd_acc: dict[int, list[np.ndarray]] = {h: [] for h in HORIZONS}
    ev_prim_acc, ctrl_prim_acc = [], []
    for r in range(pre.regime_id.shape[0]):
        s, e, direction, rid = (int(pre.regime_start[r]), int(pre.regime_end[r]),
                                int(pre.regime_dir[r]), int(pre.regime_id[r]))
        reg_trig = triggers[(triggers > s) & (triggers <= e)]
        if reg_trig.size == 0:
            continue
        elig = eligible_controls(s, e, n, is_trigger, near)
        controls, counts = nearest_controls(elig, reg_trig)
        reportable = counts >= MIN_CONTROLS
        if not reportable.any():
            continue
        rt = reg_trig[reportable]
        rc = controls[reportable]
        rk = counts[reportable]
        ev_idx.append(rt)
        ev_dir.append(np.full(rt.shape[0], direction, dtype=np.int64))
        ev_reg.append(np.full(rt.shape[0], rid, dtype=np.int64))
        for h in HORIZONS:
            signed = direction * dlog[h] * 10_000.0
            ev_ret = signed[rt]
            ctrl_mean = _control_mean(rc, rk, signed)
            pd_acc[h].append(ev_ret - ctrl_mean)
            if h == PRIMARY_HORIZON:
                ev_prim_acc.append(ev_ret)
                ctrl_prim_acc.append(ctrl_mean)
    if not ev_idx:
        empty = np.empty(0)
        return CellEvents(empty.astype(np.int64), empty.astype(np.int64), empty.astype(np.int64),
                          {h: empty for h in HORIZONS}, empty, empty, 0, 0)
    idx = np.concatenate(ev_idx)
    direction = np.concatenate(ev_dir)
    regime = np.concatenate(ev_reg)
    paired = {h: np.concatenate(pd_acc[h]) for h in HORIZONS}
    return CellEvents(
        idx, direction, regime, paired,
        np.concatenate(ev_prim_acc), np.concatenate(ctrl_prim_acc),
        int((direction == 1).sum()), int((direction == -1).sum()),
    )


# --------------------------------------------------------------------------- #
# Inference (REUSED from EXP-021, unchanged in structure; array-based)
# --------------------------------------------------------------------------- #
def domain_effect(diffs: np.ndarray, inst_labels: np.ndarray, instruments: list[str]) -> float:
    """Instrument-averaged effect: equal-weight mean of per-instrument event means."""
    per_inst = [float(diffs[inst_labels == i].mean()) for i in instruments if (inst_labels == i).any()]
    return float(np.mean(per_inst)) if per_inst else float("nan")


def build_strata(
    diffs: np.ndarray, inst_labels: np.ndarray, dir_labels: np.ndarray,
    regime_labels: np.ndarray, instruments: list[str],
) -> dict[tuple[str, int], tuple[np.ndarray, np.ndarray]]:
    """Per-(instrument, direction) regime-level (sum, count) of paired diffs."""
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}
    for inst in instruments:
        for d in (1, -1):
            mask = (inst_labels == inst) & (dir_labels == d)
            if not mask.any():
                continue
            reg = regime_labels[mask]
            uniq, inv = np.unique(reg, return_inverse=True)
            sums = np.bincount(inv, weights=diffs[mask], minlength=uniq.size)
            cnts = np.bincount(inv, minlength=uniq.size).astype(float)
            strata[(inst, d)] = (sums, cnts)
    return strata


def bootstrap_effect_distribution(
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]],
    instruments: list[str], rng: np.random.Generator, n_boot: int, chunk: int,
) -> np.ndarray:
    """Regime-cluster bootstrap distribution of the instrument-averaged effect.

    Resamples regime clusters with replacement within each (instrument, direction)
    stratum, recomputes each instrument's event-weighted mean, averages across
    instruments. Identical resampling structure to EXP-021 ``bootstrap_ci``; returns
    the bootstrap distribution so a planted edge shifts the CI by a pure offset.
    """
    num = {i: np.zeros(n_boot) for i in instruments}
    den = {i: np.zeros(n_boot) for i in instruments}
    for (inst, _d), (reg_sum, reg_cnt) in strata.items():
        r = reg_sum.size
        if r == 0:
            continue
        for start in range(0, n_boot, chunk):
            size = min(chunk, n_boot - start)
            sel = rng.integers(0, r, size=(size, r))
            num[inst][start : start + size] += reg_sum[sel].sum(axis=1)
            den[inst][start : start + size] += reg_cnt[sel].sum(axis=1)
    means = [np.divide(num[i], den[i], out=np.full(n_boot, np.nan), where=den[i] > 0) for i in instruments]
    return np.nanmean(np.vstack(means), axis=0)


def permutation_p(
    diffs: np.ndarray, inst_index: np.ndarray, counts: np.ndarray,
    observed: float, rng: np.random.Generator, n_perm: int, chunk: int,
) -> float:
    """One-sided stratified paired sign-permutation p-value (null: 0 advantage)."""
    k = counts.size
    masks = [inst_index == j for j in range(k)]
    ge = 0
    for start in range(0, n_perm, chunk):
        size = min(chunk, n_perm - start)
        signs = rng.integers(0, 2, size=(size, diffs.size)).astype(np.int8) * 2 - 1
        signed = signs * diffs
        per_inst = np.empty((size, k))
        for j, mask in enumerate(masks):
            per_inst[:, j] = signed[:, mask].sum(axis=1) / counts[j]
        ge += int(np.sum(per_inst.mean(axis=1) >= observed))
    return (1 + ge) / (1 + n_perm)


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment over a family of domain primary p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (domain, p) in enumerate(items):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[domain] = running
    return adjusted


def decide_label(effect: float, ci_low: float, ci_high: float, holm_p: float,
                 alpha: float, effect_h1: float, effect_h6: float) -> str:
    """Per-domain verdict via the EXP-021 Evidence-FOR rule (unchanged in structure)."""
    for_flag = effect > 0 and ci_low > 0 and holm_p <= alpha
    sec_neg = effect_h1 < 0 and effect_h6 < 0
    if for_flag and not sec_neg:
        return "EVIDENCE_FOR"
    if for_flag and sec_neg:
        return "INCONCLUSIVE_SECONDARY_UNSTABLE"
    if ci_high <= 0:
        return "EVIDENCE_AGAINST"
    return "INCONCLUSIVE_SPANS_ZERO"


# --------------------------------------------------------------------------- #
# Rates, MDE, equity companion
# --------------------------------------------------------------------------- #
def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval (center-half, center+half, half_width) for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    phat = k / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))) / denom
    return (center - half, center + half, half)


def sortino_ratio(returns: np.ndarray) -> float:
    """Sortino-style ratio: mean / downside deviation (non-finite if no downside)."""
    arr = returns[np.isfinite(returns)]
    if arr.size == 0:
        return float("nan")
    downside = arr[arr < 0.0]
    if downside.size == 0:
        return float("nan")
    dd = math.sqrt(float(np.mean(downside ** 2)))
    if dd == 0.0:
        return float("nan")
    return float(np.mean(arr) / dd)


def equity_advantage(
    event_bps: np.ndarray, control_bps: np.ndarray, inst_labels: np.ndarray,
    instruments: list[str], planted_g: float,
) -> tuple[float, float]:
    """Exposure-matched equity companion (non-gating).

    Strategy per-trade returns are the (planted) per-event returns; the
    exposure-matched baseline takes the **same number of trades** at each event's
    matched-control mean. Returns ``(instrument-averaged cumulative log-equity
    advantage in bps, instrument-averaged Sortino difference)``. Buy-hold is not
    used as the comparator (it would reintroduce the exposure mismatch); it is drawn
    only as annotated context in the plot.
    """
    adv, sortino_diff = [], []
    strat = event_bps + planted_g
    for inst in instruments:
        m = inst_labels == inst
        if not m.any():
            continue
        adv.append(float(np.nansum(strat[m]) - np.nansum(control_bps[m])))
        sortino_diff.append(sortino_ratio(strat[m]) - sortino_ratio(control_bps[m]))
    cum = float(np.mean(adv)) if adv else float("nan")
    sd = float(np.nanmean(sortino_diff)) if sortino_diff else float("nan")
    return cum, sd
