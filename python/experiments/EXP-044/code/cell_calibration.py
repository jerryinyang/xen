"""EXP-044 per-cell calibration substrate + single-cell frozen inference.

Pure, deterministic helpers for the EXP-044 calibration (see analysis-plan.md).
The only new logic in EXP-044 lives here:

  * a per-cell sparse placebo substrate — placement at the cell's **realized
    TRAIN event count** (direction mix matched to the realized bull/bear split)
    inside the cell's real frozen-baseline regimes, with real trigger bars
    excluded from placement and control pools; an N2 block-permuted null; and
    an additive per-event planted drift applied as a pure shift downstream; and
  * the **single-cell** application of the frozen EXP-027 decision pipeline —
    matched controls, regime-cluster bootstrap CI, stratified paired
    sign-permutation — with the instrument-aggregation (``domain_effect``) and
    Holm steps removed per the approved plan (single instrument, single cell).

Discipline enforced here (each maps to a documented prior failure mode):

  * **per-EVENT** unit only — denominators are reportable matched events and
    reportable draws, never bars; no per-bar floor or suite is referenced;
  * **anti-overfitting** — real trigger *locations* enter only as exclusions;
    real event outcomes are never computed or read; the signal under test is
    entirely synthetic (placebo + planted drift);
  * **look-ahead-safe** — placement/matching use only bar-time regime, anchor,
    and trigger-location info; forward returns are outcomes only;
  * **zero-baseline** — the null per-event excess is exactly 0 bps; rates carry
    Wilson intervals; a non-recovered MDE is non-finite, never 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen method constants (EXP-027 values; EXP-044 plan fixes H_CAL = 8)
# --------------------------------------------------------------------------- #
H_CAL: int = 8                     # calibration outcome window (domain bars)

MAX_CONTROLS: int = 5
MIN_CONTROLS: int = 3
EXCLUSION_BARS: int = 6

MIN_REPORTABLE_EVENTS: int = 30    # per-draw reportability (per-cell analog)
MIN_DIRECTION_EVENTS: int = 8      # of the EXP-021 rule; instrument leg removed

PYRAMID_FRAC: float = 0.5          # EXP-027 structural clustering parameters
PYRAMID_SPAN: int = 6


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellPrecompute:
    """Draw-independent precompute for one (instrument, domain) cell.

    All arrays are real TRAIN-stratum quantities computed once; a draw reduces
    to index selection + gather. ``regime_pool`` holds each regime's eligible
    interior indices (real trigger bars already excluded).
    """

    instrument: str
    domain: str
    n: int
    log_close: np.ndarray               # (n,) log real Close
    bar_log_returns: np.ndarray         # (n-1,) per-bar real log returns
    block_length: int                   # TRAIN-estimated block length (N2)
    regime_id: np.ndarray               # (R,) int
    regime_dir: np.ndarray              # (R,) int in {-1, +1}
    regime_pool: tuple[np.ndarray, ...]  # (R,) eligible interior index arrays
    real_trigger: np.ndarray            # (n,) bool — frozen baseline triggers
    dlog_real: np.ndarray               # (n,) real forward H_CAL log diff (NaN at real triggers)
    regime_alloc: np.ndarray            # (R,) exact per-regime placement counts
    n_target_bull: int                  # realized TRAIN counts (EXP-043)
    n_target_bear: int


@dataclass
class CellDraw:
    """Reportable matched placebo events from one cell draw (paired diffs at g=0)."""

    paired_diff: np.ndarray            # (E,) event minus control-mean, bps
    direction: np.ndarray              # (E,) int {-1, +1}
    regime: np.ndarray                 # (E,) regime id
    n_bull: int                        # reportable matched events per direction
    n_bear: int
    n_placed_bull: int                 # placed placebo triggers per direction
    n_placed_bear: int

    @property
    def n_events(self) -> int:
        return int(self.paired_diff.shape[0])

    @property
    def reportable(self) -> bool:
        return (
            self.n_events >= MIN_REPORTABLE_EVENTS
            and self.n_bull >= MIN_DIRECTION_EVENTS
            and self.n_bear >= MIN_DIRECTION_EVENTS
        )


# --------------------------------------------------------------------------- #
# Forward returns (outcomes only)
# --------------------------------------------------------------------------- #
def forward_logdiff_from_close(log_close: np.ndarray, h: int) -> np.ndarray:
    """Forward h-bar log difference per bar; NaN where future bars run out."""
    n = log_close.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if h < n:
        out[: n - h] = log_close[h:] - log_close[: n - h]
    return out


def forward_logdiff_from_returns(returns: np.ndarray, h: int, n: int) -> np.ndarray:
    """Forward h-bar log diff reconstructed from a per-bar return series (N2)."""
    level = np.concatenate([[0.0], np.cumsum(returns)]) if returns.size else np.zeros(n)
    out = np.full(n, np.nan, dtype=float)
    if h < n:
        out[: n - h] = level[h:] - level[: n - h]
    return out


def block_permute_returns(
    returns: np.ndarray, block_length: int, rng: np.random.Generator
) -> np.ndarray:
    """Circular moving-block bootstrap of a return series (the N2 null)."""
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
# Placement at realized counts (look-ahead-safe; clustered as in EXP-027)
# --------------------------------------------------------------------------- #
def regime_interior_pool(
    start: int, end: int, n: int, real_trigger: np.ndarray
) -> np.ndarray:
    """Eligible interior indices of one regime for placement/control candidacy.

    ``(start, min(end, n-1-H_CAL)]`` so every placed event/control has a valid
    H_CAL outcome window, minus the cell's **real** frozen-baseline trigger
    bars (scope: real trigger locations are exclusions, never candidates).
    """
    hi = min(int(end), n - 1 - H_CAL)
    lo = int(start) + 1
    if hi < lo:
        return np.empty(0, dtype=np.int64)
    cand = np.arange(lo, hi + 1, dtype=np.int64)
    return cand[~real_trigger[cand]]


def allocate_pool_targets(pool_sizes: np.ndarray, target: int) -> np.ndarray:
    """Largest-remainder allocation of ``target`` placements across regime pools.

    Deterministic (no randomness): quotas proportional to pool size, floors
    assigned first, remainders ranked stably. Each allocation is capped at its
    pool size; any cap-induced shortfall is redistributed to pools with slack.
    The returned counts sum to ``min(target, sum(pool_sizes))`` exactly.
    """
    alloc = np.zeros(pool_sizes.shape[0], dtype=np.int64)
    total = int(pool_sizes.sum())
    if total <= 0 or target <= 0:
        return alloc
    target = min(int(target), total)
    quota = target * pool_sizes / total
    alloc = np.floor(quota).astype(np.int64)
    remainder = target - int(alloc.sum())
    if remainder > 0:
        order = np.argsort(-(quota - alloc), kind="stable")
        alloc[order[:remainder]] += 1
    alloc = np.minimum(alloc, pool_sizes)
    shortfall = target - int(alloc.sum())
    while shortfall > 0:
        slack = pool_sizes - alloc
        j = int(np.argmax(slack))
        if slack[j] <= 0:
            break
        add = min(shortfall, int(slack[j]))
        alloc[j] += add
        shortfall -= add
    return alloc


def place_pool_triggers(
    pool: np.ndarray, n_trig: int, rng: np.random.Generator
) -> np.ndarray:
    """Place exactly ``n_trig`` placebo triggers in one regime's pool.

    EXP-027 clustering mechanism: uniform seeds plus ``PYRAMID_FRAC`` follow-ons
    within ``±PYRAMID_SPAN`` of a seed. Pyramid candidates are restricted to
    membership in **this regime's pool** (never an adjacent regime); collisions
    and out-of-pool candidates are topped up with uniform picks from the
    remaining pool so the placed count is exact. Sorted unique indices of size
    ``min(n_trig, pool_size)``.
    """
    pool_size = pool.shape[0]
    if pool_size == 0 or n_trig <= 0:
        return np.empty(0, dtype=np.int64)
    n_trig = min(int(n_trig), pool_size)
    n_seed = min(max(1, int(round(n_trig * (1.0 - PYRAMID_FRAC)))), pool_size)
    seeds = rng.choice(pool, size=n_seed, replace=False)
    n_pyr = n_trig - n_seed
    if n_pyr > 0:
        base = seeds[rng.integers(0, n_seed, size=n_pyr * 2)]
        off = rng.integers(-PYRAMID_SPAN, PYRAMID_SPAN + 1, size=base.size)
        cand = base + off
        cand = cand[off != 0]
        loc = np.searchsorted(pool, cand)
        in_pool = (loc < pool_size) & (pool[np.minimum(loc, pool_size - 1)] == cand)
        chosen = np.unique(np.concatenate([seeds, cand[in_pool]]))
    else:
        chosen = np.unique(seeds)
    if chosen.size > n_trig:
        chosen = np.sort(rng.choice(chosen, size=n_trig, replace=False))
    elif chosen.size < n_trig:
        remaining = np.setdiff1d(pool, chosen, assume_unique=True)
        extra = rng.choice(remaining, size=n_trig - chosen.size, replace=False)
        chosen = np.sort(np.concatenate([chosen, extra]))
    return chosen.astype(np.int64)


def build_near_trigger(n: int, triggers: np.ndarray) -> np.ndarray:
    """Mask of bars within ``EXCLUSION_BARS`` of any placebo trigger (vectorized)."""
    near = np.zeros(n, dtype=bool)
    if triggers.size == 0:
        return near
    for offset in range(-EXCLUSION_BARS, EXCLUSION_BARS + 1):
        pos = triggers + offset
        pos = pos[(pos >= 0) & (pos < n)]
        near[pos] = True
    return near


# --------------------------------------------------------------------------- #
# Matched-control selection (frozen EXP-027/EXP-021 semantics)
# --------------------------------------------------------------------------- #
def nearest_controls(
    eligible_c: np.ndarray, events_t: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized nearest-``MAX_CONTROLS`` control selection within a regime.

    Causally equivalent to EXP-021 ``select_controls``: within one regime the
    anchor-age and timestamp keys both reduce to ``|c - t|`` (one anchor per
    regime), so selection is nearest eligible bars by index, ties to the lower
    index. Returns ``(controls[E, MAX_CONTROLS] padded -1, counts[E])``.
    """
    e = events_t.shape[0]
    out = np.full((e, MAX_CONTROLS), -1, dtype=np.int64)
    c = eligible_c.shape[0]
    if e == 0 or c == 0:
        return out, np.zeros(e, dtype=np.int64)
    pos = np.searchsorted(eligible_c, events_t)
    left = pos - 1
    right = pos
    big = np.iinfo(np.int64).max
    for k in range(MAX_CONTROLS):
        has_left = left >= 0
        has_right = right < c
        d_left = np.where(has_left, events_t - eligible_c[np.clip(left, 0, c - 1)], big)
        d_right = np.where(has_right, eligible_c[np.clip(right, 0, c - 1)] - events_t, big)
        choose_left = has_left & (d_left <= d_right)
        choose_right = (~choose_left) & has_right
        out[:, k] = np.where(
            choose_left,
            eligible_c[np.clip(left, 0, c - 1)],
            np.where(choose_right, eligible_c[np.clip(right, 0, c - 1)], -1),
        )
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
    """Assert the vectorized selection equals the EXP-021-style reference.

    Self-contained guard (no market data); fails loudly before any draw runs.

    Raises
    ------
    ValueError
        On any mismatch between the vectorized and reference selection.
    """
    cases: list[tuple[np.ndarray, int]] = [
        (np.array([10, 11, 12, 13, 14]), 5),
        (np.array([10, 11, 12, 13, 14]), 20),
        (np.array([8, 9, 11, 12]), 10),
        (np.array([1, 3, 5, 7, 9, 11, 13]), 8),
        (np.array([10, 11]), 5),
    ]
    for eligible, t in cases:
        elig = eligible.astype(np.int64)
        controls, _ = nearest_controls(elig, np.array([t], dtype=np.int64))
        got = [int(c) for c in controls[0] if c >= 0]
        expected = reference_select_controls(elig, int(t))
        if got != expected:
            raise ValueError(
                f"control-matching equivalence FAILED for eligible={elig.tolist()} "
                f"t={t}: vectorized={got} != reference={expected}"
            )
    return True


def _control_mean(controls: np.ndarray, counts: np.ndarray, signed: np.ndarray) -> np.ndarray:
    """Mean signed return over each event's matched controls (segment mean)."""
    e = controls.shape[0]
    flat = controls.reshape(-1)
    valid = flat >= 0
    event_ids = np.repeat(np.arange(e), MAX_CONTROLS)[valid]
    sums = np.bincount(event_ids, weights=signed[flat[valid]], minlength=e)
    denom = np.where(counts > 0, counts, 1)
    out = sums / denom
    out[counts == 0] = np.nan
    return out


# --------------------------------------------------------------------------- #
# One cell draw: placement -> controls -> paired diffs (g = 0)
# --------------------------------------------------------------------------- #
def simulate_cell_draw(
    pre: CellPrecompute, dlog: np.ndarray, rng: np.random.Generator
) -> CellDraw:
    """Place placebo events at the cell's realized counts and pair with controls.

    Pure given ``rng``. ``dlog`` is the active forward-return array (real for
    N1; block-permuted for N2). No planted edge here — the additive edge is a
    pure shift of the paired differences applied downstream. Placement is exact
    per regime (``pre.regime_alloc``); placed counts per direction are recorded
    so target fidelity is auditable per draw.
    """
    n = pre.n
    trig_lists = [
        place_pool_triggers(pool, int(alloc), rng)
        for pool, alloc in zip(pre.regime_pool, pre.regime_alloc)
    ]
    placed_bull = int(sum(t.size for t, d in zip(trig_lists, pre.regime_dir) if int(d) == 1))
    placed_bear = int(sum(t.size for t, d in zip(trig_lists, pre.regime_dir) if int(d) == -1))
    triggers = (
        np.unique(np.concatenate(trig_lists)) if trig_lists else np.empty(0, dtype=np.int64)
    )
    if triggers.size == 0:
        empty = np.empty(0)
        return CellDraw(empty, empty.astype(np.int64), empty.astype(np.int64),
                        0, 0, placed_bull, placed_bear)

    is_trigger = np.zeros(n, dtype=bool)
    is_trigger[triggers] = True
    near = build_near_trigger(n, triggers)

    pd_acc, dir_acc, reg_acc = [], [], []
    for r, pool in enumerate(pre.regime_pool):
        if pool.size == 0:
            continue
        reg_trig = pool[is_trigger[pool]]
        if reg_trig.size == 0:
            continue
        elig = pool[~is_trigger[pool] & ~near[pool]]
        controls, counts = nearest_controls(elig, reg_trig)
        reportable = counts >= MIN_CONTROLS
        if not reportable.any():
            continue
        rt = reg_trig[reportable]
        direction = int(pre.regime_dir[r])
        signed = direction * dlog * 10_000.0
        ctrl_mean = _control_mean(controls[reportable], counts[reportable], signed)
        pd_acc.append(signed[rt] - ctrl_mean)
        dir_acc.append(np.full(rt.shape[0], direction, dtype=np.int64))
        reg_acc.append(np.full(rt.shape[0], int(pre.regime_id[r]), dtype=np.int64))
    if not pd_acc:
        empty = np.empty(0)
        return CellDraw(empty, empty.astype(np.int64), empty.astype(np.int64),
                        0, 0, placed_bull, placed_bear)
    direction = np.concatenate(dir_acc)
    return CellDraw(
        np.concatenate(pd_acc),
        direction,
        np.concatenate(reg_acc),
        int((direction == 1).sum()),
        int((direction == -1).sum()),
        placed_bull,
        placed_bear,
    )


# --------------------------------------------------------------------------- #
# Single-cell inference (frozen EXP-027 structure; aggregation/Holm removed)
# --------------------------------------------------------------------------- #
def build_cell_strata(draw: CellDraw) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Per-direction regime-level (sum, count) of paired diffs for one cell."""
    strata: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for d in (1, -1):
        mask = draw.direction == d
        if not mask.any():
            continue
        _, inv = np.unique(draw.regime[mask], return_inverse=True)
        sums = np.bincount(inv, weights=draw.paired_diff[mask])
        cnts = np.bincount(inv).astype(float)
        strata[d] = (sums, cnts)
    return strata


def bootstrap_cell_distribution(
    strata: dict[int, tuple[np.ndarray, np.ndarray]],
    rng: np.random.Generator,
    n_boot: int,
    chunk: int,
) -> np.ndarray:
    """Regime-cluster bootstrap distribution of the cell's event-weighted mean.

    Resamples regime clusters with replacement within each direction stratum —
    identical resampling structure to EXP-027/EXP-021, single instrument — and
    returns the distribution so a planted edge shifts the CI by a pure offset.
    """
    num = np.zeros(n_boot)
    den = np.zeros(n_boot)
    for reg_sum, reg_cnt in strata.values():
        r = reg_sum.size
        if r == 0:
            continue
        for start in range(0, n_boot, chunk):
            size = min(chunk, n_boot - start)
            sel = rng.integers(0, r, size=(size, r))
            num[start : start + size] += reg_sum[sel].sum(axis=1)
            den[start : start + size] += reg_cnt[sel].sum(axis=1)
    return np.divide(num, den, out=np.full(n_boot, np.nan), where=den > 0)


def permutation_p_cell(
    diffs: np.ndarray,
    observed: float,
    rng: np.random.Generator,
    n_perm: int,
    chunk: int,
) -> float:
    """One-sided paired sign-permutation p for the cell mean (null: 0 excess)."""
    ge = 0
    for start in range(0, n_perm, chunk):
        size = min(chunk, n_perm - start)
        signs = rng.integers(0, 2, size=(size, diffs.size)).astype(np.int8) * 2 - 1
        ge += int(np.sum((signs * diffs).mean(axis=1) >= observed))
    return (1 + ge) / (1 + n_perm)


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval ``(low, high, half_width)`` for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    phat = k / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))) / denom
    return (center - half, center + half, half)
