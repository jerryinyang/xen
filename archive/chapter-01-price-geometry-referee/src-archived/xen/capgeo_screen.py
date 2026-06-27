"""TRAIN-only candidate-screen kernels for CF-CAPGEO-001 (Phase 018 / EXP-083, HYP-004a).

This module is the reusable, pure-computation harness behind the EXP-083 TRAIN-only screen
(D0-amendment-001). It (a) resolves a triple-barrier / trailing / fixed-horizon / partial exit on a
frozen-entry event's **real-OHLC forward path** to a realized **ATR-unit** return, (b) provides the
moving-block bootstrap inference (one-sample one-sided lower bounds, two-sample independent difference
CIs, paired same-event difference CIs) the G-018a screen + separability gate use, and (c) implements the
binding separability legs S1 (attribution decomposition + ``m_cell``-calibrated matched-control edge-call)
and S2 (post-exit tail non-residual). It applies **no exit selection or tuning**: the candidate barriers
are supplied by the caller (the derived ones come from the sha256-pinned ``xen.capgeo_exits.derive_barriers``;
the benchmark grid is the frozen enumerated surface).

Discipline (binding): all returns on **real prices** in **ATR units**; first-touch scans are causal
(read only entry+1..cap, fenced to ``n_bars-1``); the intrabar tie-break is **adverse-first** (the
EXP-054 P15 worst-case fill standard) so no look-ahead optimism manufactures edge; an event whose window
is truncated by the TRAIN edge before any touch is ``CENSORED`` (excluded with record, never marked at the
edge). No I/O, no globals, no RNG state outside the passed ``Generator`` — deterministic.

Verdict legs (frozen D4/D9 constants, passed by the caller; defaults mirror the bite-check freeze):
``K_TAIL=3.0``, ``TAU_TAIL=0.06``, ``DELTA=0.40`` ATR, S2 floor ``N_S2_FLOOR=120``; ``m_cell`` is the
per-cell synthetic-null ``Q95(diff CI_low)`` (EXP-027/070 standard). ``N_BOOT`` defaults to 10_000.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xen.capgeo_geometry import K_TAIL, tail_stats

# --------------------------------------------------------------------------- #
# Frozen constants (D4 / D9 bite-check GREEN 2026-06-21; defaults — caller may pass through)
# --------------------------------------------------------------------------- #
TAU_TAIL: float = 0.06          # S2 post-exit tailmass ceiling
DELTA: float = 0.40             # S2 relative-q05 tolerance (ATR)
N_S2_FLOOR: int = 120           # S2 operating floor; below -> S2 deferred + disclosed
N_BOOT: int = 10_000            # bootstrap resamples
BOOT_BATCH: int = 2_000         # vectorized bootstrap batch
NULL_REPS: int = 1_000          # m_cell synthetic-null replications
EVENT_FLOOR: int = 30           # usable/resolved-event floor to form a candidate

# Resolution classes
CLASS_FAV: int = 1
CLASS_ADV: int = -1
CLASS_TIMECAP: int = 0
CLASS_CENSORED: int = -9        # window truncated by the TRAIN edge before any touch -> excluded

_INF_STOP: float = float("inf")  # sentinel adverse distance for no-stop arms


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Resolution:
    """Per-event realized exit of one candidate on one substrate-cell (ATR units)."""

    ret: np.ndarray          # realized ATR return; NaN for excluded/censored events
    cls: np.ndarray          # CLASS_* per event
    resolved: np.ndarray     # bool mask of events that produced a finite return
    n_resolved: int
    n_censored: int


@dataclass(frozen=True)
class GateRow:
    """G-018a + separability outcome for one {substrate x cell x candidate}."""

    n_usable: int
    n_resolved: int
    gross_exp: float
    gross_exp_lo: float
    gross_med: float
    gross_med_lo: float
    matched_exp_excess_lo: float
    matched_med_excess_lo: float
    g018a_pass: bool
    guard_i_defer: bool
    x_full: float
    x_fav: float
    x_tail: float
    x_fav_excess_lo: float
    m_cell: float
    s1_pass: bool
    tailmass_post: float
    q05_post: float
    q05_control: float
    s2_pass: bool
    s2_deferred: bool
    valid: bool
    fail_leg: str            # "" | "g018a" | "s1" | "s2"


# --------------------------------------------------------------------------- #
# Pure computation — exit resolution on the real-OHLC forward path (causal)
# --------------------------------------------------------------------------- #
def resolve_static_barrier(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    t_fav: np.ndarray, s_adv: np.ndarray, h_cap: np.ndarray, n_bars: int,
) -> Resolution:
    """First-touch triple-barrier resolution to realized ATR returns (adverse-first tie-break).

    ``t_fav``/``s_adv`` are per-event favourable/adverse **ATR distances** (``s_adv = inf`` -> no stop);
    ``h_cap`` is per-event bars. FAV touch -> ``+t_fav``; ADV touch -> ``-s_adv``; full time-cap with no
    touch -> mark-to-close ``d*(close[cap]-c0)/atr``; window truncated by the TRAIN edge before any touch
    -> ``CENSORED`` (excluded). ATR-undefined / clipped-empty events are excluded (NaN return).
    """
    m = int(entry_idx.shape[0])
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        tf = float(t_fav[j])
        if not np.isfinite(tf) or tf <= 0.0:          # invalid favourable target (e.g. VP on the
            continue                                  # adverse side) -> excluded with record
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        has_stop = np.isfinite(s_adv[j])
        fav_lvl = c0 + d * tf * a
        adv_lvl = c0 - d * float(s_adv[j]) * a if has_stop else np.nan
        lo = i + 1
        cap_end = i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        hit = _scan_static(high, low, lo, hi, d, fav_lvl, adv_lvl, has_stop)
        if hit == CLASS_ADV:
            cls[j] = CLASS_ADV
            ret[j] = -float(s_adv[j])
        elif hit == CLASS_FAV:
            cls[j] = CLASS_FAV
            ret[j] = float(t_fav[j])
        elif hi < cap_end:
            cls[j] = CLASS_CENSORED                      # truncated by TRAIN edge, no touch
        else:
            cls[j] = CLASS_TIMECAP
            ret[j] = d * (float(close[hi]) - c0) / a
    return _resolution(ret, cls)


def _scan_static(
    high: np.ndarray, low: np.ndarray, lo: int, hi: int, d: int,
    fav_lvl: float, adv_lvl: float, has_stop: bool,
) -> int | None:
    """Bounded causal first-touch scan of one window; adverse-first on a same-bar tie (P15)."""
    for k in range(lo, hi + 1):
        if d == 1:
            fav = high[k] >= fav_lvl
            adv = has_stop and low[k] <= adv_lvl
        else:
            fav = low[k] <= fav_lvl
            adv = has_stop and high[k] >= adv_lvl
        if adv:
            return CLASS_ADV
        if fav:
            return CLASS_FAV
    return None


def resolve_trailing(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    k_atr: float, h_cap: np.ndarray, n_bars: int,
) -> Resolution:
    """ATR trailing-stop exit (``/EXIT-TRAIL``): stop ratchets ``k_atr*ATR`` behind the running
    favourable extreme, initial stop ``k_atr*ATR`` from entry; exit at the trailing-stop touch (worst
    case: the bar's adverse extreme), else mark-to-close at the time cap. Realized ATR return at exit.
    """
    m = int(entry_idx.shape[0])
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        gap = k_atr * a
        lo, cap_end = i + 1, i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        best = c0                                       # running favourable extreme price
        exit_ret, exited = np.nan, False
        for k in range(lo, hi + 1):
            stop = best - d * gap
            adv_px = low[k] if d == 1 else high[k]
            if (d == 1 and adv_px <= stop) or (d == -1 and adv_px >= stop):
                exit_ret = d * (stop - c0) / a          # filled at the trailing stop
                exited = True
                break
            fav_px = high[k] if d == 1 else low[k]
            if (d == 1 and fav_px > best) or (d == -1 and fav_px < best):
                best = fav_px
        if exited:
            cls[j] = CLASS_ADV
            ret[j] = exit_ret
        elif hi < cap_end:
            cls[j] = CLASS_CENSORED
        else:
            cls[j] = CLASS_TIMECAP
            ret[j] = d * (float(close[hi]) - c0) / a
    return _resolution(ret, cls)


def resolve_struct_trail(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    window: int, h_cap: np.ndarray, n_bars: int,
) -> Resolution:
    """Market-structure trailing-stop exit (``/EXIT-TRAIL`` structure arm): the stop trails behind the
    most recent swing extreme — the rolling ``window``-bar low (longs) / high (shorts) of the bars seen
    so far in the trade — exited when the bar's adverse extreme breaches it, else mark-to-close at the
    cap. A conventional swing-lookback proxy for a ZigZag-pivot trail (disclosed; screen-stage).
    """
    m = int(entry_idx.shape[0])
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    w = max(1, int(window))
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        lo, cap_end = i + 1, i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        exit_ret, exited = np.nan, False
        for k in range(lo, hi + 1):
            wlo = max(i, k - w)                      # swing window within the trade (causal)
            stop = float(np.min(low[wlo:k])) if d == 1 else float(np.max(high[wlo:k]))
            if k > lo:                               # need a prior bar to define a swing stop
                adv_px = low[k] if d == 1 else high[k]
                if (d == 1 and adv_px <= stop) or (d == -1 and adv_px >= stop):
                    exit_ret = d * (stop - c0) / a
                    exited = True
                    break
        if exited:
            cls[j] = CLASS_ADV
            ret[j] = exit_ret
        elif hi < cap_end:
            cls[j] = CLASS_CENSORED
        else:
            cls[j] = CLASS_TIMECAP
            ret[j] = d * (float(close[hi]) - c0) / a
    return _resolution(ret, cls)


def resolve_partial_two_leg(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    t_fav: np.ndarray, s_adv: np.ndarray, h_cap: np.ndarray, n_bars: int,
    leg_frac: float = 0.5,
) -> Resolution:
    """Two-leg favourable-scaling exit (``/EXIT-PARTIAL`` V2A-style): ``leg_frac`` of the position
    exits at the favourable target ``t_fav``; the remainder runs to the stop ``s_adv`` or the time cap.
    Realized ATR return = ``leg_frac*ret_leg1 + (1-leg_frac)*ret_leg2`` on the same path (causal).
    """
    m = int(entry_idx.shape[0])
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        tf = float(t_fav[j])
        if not np.isfinite(tf) or tf <= 0.0:
            continue
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        has_stop = np.isfinite(s_adv[j])
        fav_lvl = c0 + d * tf * a
        adv_lvl = c0 - d * float(s_adv[j]) * a if has_stop else np.nan
        lo, cap_end = i + 1, i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        leg1, taken1 = np.nan, False
        leg2, done2 = np.nan, False
        for k in range(lo, hi + 1):
            if d == 1:
                fav, adv = high[k] >= fav_lvl, has_stop and low[k] <= adv_lvl
            else:
                fav, adv = low[k] <= fav_lvl, has_stop and high[k] >= adv_lvl
            if adv:                                      # adverse-first: stops both remaining legs
                if not taken1:
                    leg1, taken1 = -float(s_adv[j]), True
                leg2, done2 = -float(s_adv[j]), True
                break
            if fav and not taken1:
                leg1, taken1 = float(t_fav[j]), True     # leg 1 scales out at the target
        if not done2:
            if hi < cap_end and not taken1:
                cls[j] = CLASS_CENSORED                  # neither leg resolved before the edge
                continue
            tail_ret = d * (float(close[hi]) - c0) / a   # leg 2 (and leg 1 if never hit) at the cap
            leg2 = tail_ret
            if not taken1:
                leg1 = tail_ret
        cls[j] = CLASS_FAV if taken1 else CLASS_TIMECAP
        ret[j] = leg_frac * float(leg1) + (1.0 - leg_frac) * float(leg2)
    return _resolution(ret, cls)


def resolve_fixed_horizon(
    close: np.ndarray, atr_entry: np.ndarray, entry_idx: np.ndarray, direction: np.ndarray,
    h_cap: np.ndarray, n_bars: int,
) -> Resolution:
    """Fixed-horizon exit (``/EXIT-PARTIAL`` AVWAP-FH arm): no price targets; mark-to-close at
    ``min(entry+h_cap, last)``. Censored only if the horizon bar is unavailable (entry at the edge).
    """
    m = int(entry_idx.shape[0])
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        i = int(entry_idx[j])
        cap_end = i + int(h_cap[j])
        if i + 1 > last:
            continue
        hi = min(cap_end, last)
        cls[j] = CLASS_TIMECAP if hi == cap_end else CLASS_CENSORED
        if cls[j] == CLASS_TIMECAP:
            ret[j] = int(direction[j]) * (float(close[hi]) - float(close[i])) / a
    return _resolution(ret, cls)


def _resolution(ret: np.ndarray, cls: np.ndarray) -> Resolution:
    resolved = np.isfinite(ret)
    return Resolution(ret=ret, cls=cls, resolved=resolved,
                      n_resolved=int(np.count_nonzero(resolved)),
                      n_censored=int(np.count_nonzero(cls == CLASS_CENSORED)))


# --------------------------------------------------------------------------- #
# Pure computation — moving-block bootstrap inference
# --------------------------------------------------------------------------- #
def _block_indices(m: int, rng: np.random.Generator, k: int) -> np.ndarray:
    """``k`` moving-block resample index matrices of length ``m`` (block ``b=max(1,round(m**1/3))``)."""
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
    return (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :m]


def _stat_distribution(
    x: np.ndarray, rng: np.random.Generator, statfn, n_boot: int, batch: int,
) -> np.ndarray:
    """Moving-block bootstrap distribution of ``statfn`` over the entry-ordered sample ``x``."""
    m = int(x.shape[0])
    out = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        idx = _block_indices(m, rng, k)
        out[done:done + k] = statfn(x[idx], axis=1)
        done += k
    return out


def one_sided_lo(
    x: np.ndarray, rng: np.random.Generator, kind: str = "mean",
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float]:
    """One-sided 95% lower bound of mean/median of ``x`` (point, ci_low_1s). NaN if ``m == 0``."""
    if x.shape[0] == 0:
        return float("nan"), float("nan")
    statfn = np.mean if kind == "mean" else np.median
    dist = _stat_distribution(x, rng, statfn, n_boot, batch)
    return float(statfn(x)), float(np.percentile(dist, 5.0))


def two_sample_diff_lo(
    a: np.ndarray, b: np.ndarray, rng: np.random.Generator, kind: str = "mean",
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> float:
    """One-sided 95% lower bound of ``stat(a) - stat(b)`` for **independent** samples (different
    entries), each moving-block resampled. NaN if either is empty.
    """
    if a.shape[0] == 0 or b.shape[0] == 0:
        return float("nan")
    statfn = np.mean if kind == "mean" else np.median
    da = _stat_distribution(a, rng, statfn, n_boot, batch)
    db = _stat_distribution(b, rng, statfn, n_boot, batch)
    return float(np.percentile(da - db, 5.0))


def m_cell_margin(
    control: np.ndarray, n_candidate: int, rng: np.random.Generator, kind: str = "mean",
    null_reps: int = NULL_REPS, n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> float:
    """Per-cell synthetic-null margin ``m_cell = Q95(null diff ci_low)`` (EXP-027/070 standard).

    Under the null (candidate has no edge over its matched-random control), both arms are draws from the
    control distribution. Repeatedly draws a synthetic candidate of size ``n_candidate`` and a synthetic
    control of size ``len(control)`` from ``control`` (block-resampled), computes the two-sample diff
    ``ci_low``, and returns its 95th percentile — the threshold that holds the edge-call FPR <= 0.05.
    """
    nc = int(control.shape[0])
    if nc == 0 or n_candidate == 0:
        return float("nan")
    statfn = np.mean if kind == "mean" else np.median
    lows = np.empty(null_reps, dtype=np.float64)
    for r in range(null_reps):
        ia = _block_indices(nc, rng, 1)[0][:n_candidate] if nc >= n_candidate else \
            rng.integers(0, nc, size=n_candidate)
        ib = _block_indices(nc, rng, 1)[0]
        syn_a, syn_b = control[ia], control[ib]
        da = _stat_distribution(syn_a, rng, statfn, n_boot, batch)
        db = _stat_distribution(syn_b, rng, statfn, n_boot, batch)
        lows[r] = float(np.percentile(da - db, 5.0))
    return float(np.percentile(lows, 95.0))


# --------------------------------------------------------------------------- #
# Pure computation — separability legs S1 / S2
# --------------------------------------------------------------------------- #
def s2_tail_residual(
    outcome: np.ndarray, control_outcome: np.ndarray,
    tau_tail: float = TAU_TAIL, delta: float = DELTA, k_tail: float = K_TAIL,
) -> tuple[float, float, float, bool]:
    """S2 — post-exit tail non-residual. PASS iff ``tailmass <= tau_tail`` AND
    ``q05 >= q05_control - delta``. Returns ``(tailmass, q05, q05_control, pass)``.
    """
    ts = tail_stats(outcome, k_tail=k_tail)
    tc = tail_stats(control_outcome, k_tail=k_tail)
    passed = bool((ts.tailmass <= tau_tail) and (ts.q05 >= tc.q05 - delta))
    return ts.tailmass, ts.q05, tc.q05, passed


# --------------------------------------------------------------------------- #
# Output schema helpers
# --------------------------------------------------------------------------- #
def gate_row_dict(instrument: str, domain: str, substrate: str, candidate: str,
                  row: GateRow) -> dict:
    """Flatten a GateRow to a result record (one {substrate x cell x candidate})."""
    rec = {"instrument": instrument, "domain": domain, "substrate": substrate,
           "candidate": candidate}
    rec.update(row.__dict__)
    return rec
