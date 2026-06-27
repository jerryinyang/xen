"""EXP-047 pure helpers: lifetime MFE/MAE, bootstrap medians, P5 shift rule.

All thresholds are Phase 013 D0 predeclarations restated by the approved scope;
nothing here is tunable. Functions are pure (no I/O, no printing).
"""
from __future__ import annotations

import hashlib

import numpy as np
import polars as pl

# ----------------------------------------------------------------------------- #
# Frozen constants (Phase 013 D0)
# ----------------------------------------------------------------------------- #
ANCHOR_ATR_PERIOD = 14          # P1 (fixed, never swept)
ANCHOR_PROMINENCE_K = 1.0       # P1 (ratified)
FLOOR_MULTIPLE_M = 2.0          # P5 leg 2 (ratified)
SE_MULT = 1.0                   # P5 leg 1 noise guard
EVENT_FLOOR = 30                # P2/P5 leg 4
G1_MIN_CELLS = 5                # P6 composition threshold
G1_MIN_INSTRUMENTS = 3          # P6 composition threshold
DOMAIN_HOURS: dict[str, int] = {"1h": 1, "2h": 2, "4h": 4}
N_BOOT = 10_000                 # descriptive bootstrap (frozen EXP-027 layer)
CONTROL_MAX = 2_000             # bounded matched-control sample per cell

# EXP-046 reconciliation conventions (baseline-row anchor, frozen Phase 012).
RECON_HORIZONS: tuple[int, ...] = (4, 8, 16)
RECON_H_BINDING = 8
RECON_H_MAX = 16
RECON_TOL_BPS = 1e-9


def lifetime_end(
    trigger_idx: np.ndarray, confirm_idx: np.ndarray, n_bars: int
) -> tuple[np.ndarray, np.ndarray]:
    """EXP-022 lifetime boundary per event: the next regime-confirmation bar
    after the trigger, or the analysis-set end (censored).

    Parameters
    ----------
    trigger_idx : np.ndarray
        Event trigger bar indices (any order).
    confirm_idx : np.ndarray
        Sorted regime confirmation bar indices.
    n_bars : int
        Number of domain bars in the TRAIN frame.

    Returns
    -------
    (end_idx, censored) : tuple[np.ndarray, np.ndarray]
        Lifetime end bar per event and a boolean censoring flag (no trend
        change before the analysis-set end).
    """
    pos = np.searchsorted(confirm_idx, trigger_idx, side="right")
    censored = pos >= confirm_idx.size
    end_idx = np.where(censored, n_bars - 1, confirm_idx[np.minimum(pos, confirm_idx.size - 1)])
    return end_idx.astype(np.int64), censored


def excursions(
    high: np.ndarray,
    low: np.ndarray,
    trigger_close: np.ndarray,
    trigger_idx: np.ndarray,
    end_idx: np.ndarray,
    direction: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-event gross MFE and MAE in direction-signed log bps (real prices).

    The excursion window is ``trigger_idx + 1 .. end_idx`` (bars strictly after
    entry at the trigger close, through the lifetime boundary). The lifetime
    path includes the entry point itself, whose excursion is zero, so both MFE
    and MAE are floored at 0.0 (standard excursion convention): a path that
    only moves adversely has MFE = 0, and a path that only moves favorably has
    MAE = 0. Events with an empty window report 0.0 for both.

    Returns
    -------
    (mfe_bps, mae_bps) : both >= 0
    """
    log_high = np.log(high)
    log_low = np.log(low)
    n_events = trigger_idx.size
    mfe = np.zeros(n_events, dtype=float)
    mae = np.zeros(n_events, dtype=float)
    log_c0 = np.log(trigger_close)
    for e in range(n_events):  # bounded: a few hundred events per cell
        a, b = int(trigger_idx[e]) + 1, int(end_idx[e]) + 1
        if a >= b:
            continue
        if direction[e] == 1:
            mfe[e] = max(0.0, (log_high[a:b].max() - log_c0[e]) * 10_000.0)
            mae[e] = max(0.0, (log_c0[e] - log_low[a:b].min()) * 10_000.0)
        else:
            mfe[e] = max(0.0, (log_c0[e] - log_low[a:b].min()) * 10_000.0)
            mae[e] = max(0.0, (log_high[a:b].max() - log_c0[e]) * 10_000.0)
    return mfe, mae


CONTROLS_PER_EVENT = 5    # EXP-021/027: up to 5 controls per event ...
CONTROLS_MIN = 3          # ... with a minimum of 3 for the event to contribute
TRIGGER_EXCLUSION = 6     # EXP-021/027: 6-bar exclusion window around triggers


def matched_controls(
    regimes: pl.DataFrame,
    event_regime_ids: np.ndarray,
    trigger_idx: np.ndarray,
    n_bars: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Matched-control bars under the EXP-021/027 convention, adapted to the
    lifetime statistic: candidates share the event's ``regime_id`` (fixing
    instrument, domain, and regime direction), are not bounce trigger bars,
    sit outside a ``TRIGGER_EXCLUSION``-bar window around any trigger in the
    cell, and carry the same lifetime-boundary semantics. Per event, up to
    ``CONTROLS_PER_EVENT`` candidates are selected by nearest anchor age
    (equivalently nearest bar index within the shared-anchor regime, ties to
    the earlier bar); events with fewer than ``CONTROLS_MIN`` eligible
    candidates contribute no controls. Controls are unique within an event;
    reuse across events within the same regime is allowed. Fully
    deterministic; total bounded by ``CONTROL_MAX``.

    Returns
    -------
    (bar_idx, end_idx, direction)
    """
    trig_sorted = np.sort(trigger_idx.astype(np.int64))
    pools: dict[int, tuple[np.ndarray, int, int]] = {}
    for r in regimes.sort("confirm_idx").to_dicts():
        c, e, d = int(r["confirm_idx"]), int(r["regime_end_idx"]), int(r["direction"])
        boundary = min(e + 1, n_bars - 1)
        cand = np.arange(c + 1, min(e, boundary - 1) + 1, dtype=np.int64)
        if cand.size and trig_sorted.size:
            pos = np.searchsorted(trig_sorted, cand)
            near_right = np.where(pos < trig_sorted.size,
                                  np.abs(trig_sorted[np.minimum(pos, trig_sorted.size - 1)] - cand),
                                  np.iinfo(np.int64).max)
            near_left = np.where(pos > 0,
                                 np.abs(cand - trig_sorted[np.maximum(pos - 1, 0)]),
                                 np.iinfo(np.int64).max)
            cand = cand[np.minimum(near_right, near_left) >= TRIGGER_EXCLUSION]
        pools[int(r["regime_id"])] = (cand, boundary, d)
    bars: list[int] = []
    ends: list[int] = []
    dirs: list[int] = []
    for rid, trig in zip(event_regime_ids, trigger_idx):
        cand, boundary, d = pools.get(int(rid), (np.empty(0, np.int64), 0, 0))
        if cand.size < CONTROLS_MIN:
            continue
        order = np.lexsort((cand, np.abs(cand - int(trig))))
        for j in order[:CONTROLS_PER_EVENT]:
            bars.append(int(cand[j]))
            ends.append(boundary)
            dirs.append(d)
        if len(bars) >= CONTROL_MAX:
            break
    if not bars:
        return (np.empty(0, np.int64),) * 3  # type: ignore[return-value]
    return (
        np.asarray(bars[:CONTROL_MAX], dtype=np.int64),
        np.asarray(ends[:CONTROL_MAX], dtype=np.int64),
        np.asarray(dirs[:CONTROL_MAX], dtype=np.int64),
    )


def bootstrap_median_se(values: np.ndarray, rng: np.random.Generator) -> float:
    """Bootstrap SE of the median (descriptive, frozen EXP-027 layer)."""
    n = values.size
    if n < 2:
        return float("nan")
    idx = rng.integers(0, n, size=(N_BOOT, n))
    return float(np.median(values[idx], axis=1).std(ddof=1))


def bootstrap_median_diff_se(
    a: np.ndarray, b: np.ndarray, rng: np.random.Generator
) -> float:
    """Bootstrap SE of ``median(a) - median(b)`` for two unpaired populations
    (independent resampling per replicate)."""
    if a.size < 2 or b.size < 2:
        return float("nan")
    med_a = np.median(a[rng.integers(0, a.size, size=(N_BOOT, a.size))], axis=1)
    med_b = np.median(b[rng.integers(0, b.size, size=(N_BOOT, b.size))], axis=1)
    return float((med_a - med_b).std(ddof=1))


def cost_floor_bps(
    rt_bps: float, financing_bps_day: float, domain: str, median_lifetime_bars: float
) -> float:
    """P4 floor: ``RT + financing × days(L, d)`` with ``days = L·hours(d)/24``."""
    return rt_bps + financing_bps_day * (median_lifetime_bars * DOMAIN_HOURS[domain] / 24.0)


def shift_verdict(
    n_anchor: int,
    median_mfe_anchor: float,
    median_mfe_base: float,
    se_diff: float,
    floor_bps: float,
    delta_median_mae: float,
    delta_median_mfe: float,
    determinism_pass: bool,
) -> tuple[str, dict[str, bool]]:
    """Mechanical P5 classification; returns ``(verdict, leg states)``."""
    legs = {
        "leg1_shift": bool(
            np.isfinite(se_diff)
            and median_mfe_anchor >= median_mfe_base + SE_MULT * se_diff
        ),
        "leg2_floor": bool(median_mfe_anchor >= FLOOR_MULTIPLE_M * floor_bps),
        "leg3_mae": bool(delta_median_mae <= delta_median_mfe),
        "leg4_floor_n": bool(n_anchor >= EVENT_FLOOR),
        "leg5_determinism": bool(determinism_pass),
    }
    return ("SHIFTED_VIABLE" if all(legs.values()) else "NOT_SHIFTED"), legs


def composition_readout(rows: list[dict]) -> dict:
    """Per-phase mechanical G1b input (adjudication itself is checkpoint desk
    work): SHIFTED_VIABLE cell count and distinct-instrument span."""
    shifted = [r for r in rows if r["verdict"] == "SHIFTED_VIABLE"]
    instruments = sorted({r["instrument"] for r in shifted})
    return {
        "n_shifted_viable": len(shifted),
        "n_instruments": len(instruments),
        "instruments": ";".join(instruments),
        "composition_met": (
            len(shifted) >= G1_MIN_CELLS and len(instruments) >= G1_MIN_INSTRUMENTS
        ),
        # Threshold-sensitivity disclosure (non-binding): would the composition
        # have been met at relaxed thresholds? Informs the checkpoint operator
        # about the robustness of the G1b readout; the binding rule is P6.
        "sensitivity_met_4cells_2instruments": (
            len(shifted) >= 4 and len(instruments) >= 2
        ),
        "sensitivity_met_3cells_2instruments": (
            len(shifted) >= 3 and len(instruments) >= 2
        ),
    }


def recon_gross_h8(
    close: np.ndarray, trigger_idx: np.ndarray, direction: np.ndarray
) -> tuple[int, float]:
    """EXP-046 baseline-row reconciliation quantity: evaluable count and the
    H=8 direction-signed gross log-bps mean under the identical evaluability
    fence (``trigger + H_MAX`` inside TRAIN)."""
    keep = trigger_idx + RECON_H_MAX <= close.size - 1
    t = trigger_idx[keep]
    if t.size == 0:
        return 0, float("nan")
    log_close = np.log(close)
    g = direction[keep] * (log_close[t + RECON_H_BINDING] - log_close[t]) * 10_000.0
    return int(t.size), float(g.mean())


def events_digest(events: pl.DataFrame) -> str:
    """Stable audit fingerprint of an event population (EXP-046 convention,
    extended with the fallback disclosure)."""
    payload = "|".join(
        f"{i}:{t}:{d}:{r}:{a}:{f}" for i, t, d, r, a, f in zip(
            events.get_column("trigger_idx").to_list(),
            events.get_column("trigger_time").to_list(),
            events.get_column("direction").to_list(),
            events.get_column("regime_id").to_list(),
            events.get_column("anchor_idx").to_list(),
            events.get_column("anchor_fallback").to_list(),
        )
    )
    return hashlib.sha256(payload.encode()).hexdigest()
