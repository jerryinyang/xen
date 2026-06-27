"""EXP-046 pure helpers: gross horizon returns, cluster SE, clearance rule.

All thresholds are Phase 012 D0 predeclarations restated by the approved scope;
nothing here is tunable. Functions are pure (no I/O, no printing).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import polars as pl

# ----------------------------------------------------------------------------- #
# Frozen constants (Phase 012 D0)
# ----------------------------------------------------------------------------- #
HORIZONS: tuple[int, ...] = (4, 8, 16)          # P3 reference horizons
H_BINDING = 8                                   # P3 binding horizon
H_MAX = max(HORIZONS)                           # evaluability fence
MARGIN_SE_MULT = 1.0                            # P5 clearance margin (×SE)
EVENT_FLOOR = 30                                # P7 minimum evaluable events
G1_MIN_CELLS = 5                                # P6 composition threshold
G1_MIN_INSTRUMENTS = 3                          # P6 composition threshold
DOMAIN_HOURS: dict[str, int] = {"1h": 1, "2h": 2, "4h": 4}


@dataclass(frozen=True)
class Variant:
    """One OAT entry-parameter variant (P1/P2 grids)."""

    name: str
    alpha: float
    fast_ma: int
    slow_ma: int
    axis: str  # "baseline" | "alpha" | "ma"


# P1/P2 OAT variant set — 7 incl. baseline; order fixed (baseline first).
VARIANTS: tuple[Variant, ...] = (
    Variant("baseline", 0.75, 20, 50, "baseline"),
    Variant("alpha_0.0", 0.0, 20, 50, "alpha"),
    Variant("alpha_0.375", 0.375, 20, 50, "alpha"),
    Variant("alpha_1.0", 1.0, 20, 50, "alpha"),
    Variant("ma_10_25", 0.75, 10, 25, "ma"),
    Variant("ma_40_100", 0.75, 40, 100, "ma"),
    Variant("ma_60_150", 0.75, 60, 150, "ma"),
)


def cost_floor_bps(rt_bps: float, financing_bps_day: float, domain: str) -> float:
    """P4 floor: ``RT + financing × days(H=8, d)`` with days = 8·hours(d)/24."""
    return rt_bps + financing_bps_day * (H_BINDING * DOMAIN_HOURS[domain] / 24.0)


def evaluable_mask(trigger_idx: np.ndarray, n_bars: int) -> np.ndarray:
    """One population per cell×variant: the H_MAX window must end in TRAIN."""
    return trigger_idx + H_MAX <= n_bars - 1


def gross_at_horizons(
    close: np.ndarray, trigger_idx: np.ndarray, direction: np.ndarray
) -> dict[int, np.ndarray]:
    """Direction-signed gross log-bps at each reference horizon.

    Callers must pass already-evaluable events (``evaluable_mask`` applied),
    so ``trigger_idx + H`` never leaves the TRAIN frame.
    """
    log_close = np.log(close)
    return {
        h: direction * (log_close[trigger_idx + h] - log_close[trigger_idx]) * 10_000.0
        for h in HORIZONS
    }


def cluster_bootstrap_se(
    values: np.ndarray,
    direction: np.ndarray,
    regime: np.ndarray,
    rng: np.random.Generator,
    n_boot: int = 1_000,
) -> float:
    """Regime-cluster bootstrap SE of the per-event mean (frozen EXP-027
    structure; identical to the EXP-045 implementation): regime clusters
    resampled with replacement within direction strata, event-weighted
    combined mean."""
    num = np.zeros(n_boot)
    den = np.zeros(n_boot)
    for d in (1, -1):
        mask = direction == d
        if not mask.any():
            continue
        _, inv = np.unique(regime[mask], return_inverse=True)
        sums = np.bincount(inv, weights=values[mask])
        cnts = np.bincount(inv).astype(float)
        r = sums.shape[0]
        sel = rng.integers(0, r, size=(n_boot, r))
        num += sums[sel].sum(axis=1)
        den += cnts[sel].sum(axis=1)
    means = np.divide(num, den, out=np.full(n_boot, np.nan), where=den > 0)
    finite = means[np.isfinite(means)]
    return float(finite.std(ddof=1)) if finite.size > 1 else float("nan")


def events_digest(events: pl.DataFrame) -> str:
    """Stable fingerprint of an event population over every field used by
    scoring (trigger index/time, direction, regime, anchor). Determinism
    itself is asserted by full-frame equality; this digest is the persisted
    audit fingerprint."""
    payload = "|".join(
        f"{i}:{t}:{d}:{r}:{a}" for i, t, d, r, a in zip(
            events.get_column("trigger_idx").to_list(),
            events.get_column("trigger_time").to_list(),
            events.get_column("direction").to_list(),
            events.get_column("regime_id").to_list(),
            events.get_column("anchor_idx").to_list(),
        )
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def clearance_verdict(
    n_evaluable: int,
    gross_means: dict[int, float],
    se_binding: float,
    floor: float,
    determinism_pass: bool,
) -> tuple[str, float]:
    """Mechanical D0 clearance rule; returns ``(verdict, margin_bps)``.

    ``margin = gross(H=8) − floor − 1×SE`` (reported for every eligible row).
    Verdicts: CLEAR / NO_CLEAR / BELOW_FLOOR / DETERMINISM_FAIL.
    """
    if not determinism_pass:
        return "DETERMINISM_FAIL", float("nan")
    if n_evaluable < EVENT_FLOOR:
        return "BELOW_FLOOR", float("nan")
    margin = gross_means[H_BINDING] - floor - MARGIN_SE_MULT * se_binding
    clears = (
        np.isfinite(se_binding)
        and margin >= 0.0
        and gross_means[4] > 0.0
        and gross_means[16] > 0.0
    )
    return ("CLEAR" if clears else "NO_CLEAR"), float(margin)


def variant_rollup(rows: list[dict]) -> list[dict]:
    """Per-variant mechanical G1 readout + ordering keys (scope §6)."""
    out = []
    for v in VARIANTS:
        cleared = [r for r in rows if r["variant"] == v.name and r["verdict"] == "CLEAR"]
        instruments = sorted({r["instrument"] for r in cleared})
        margins = [r["margin_bps"] for r in cleared]
        out.append({
            "variant": v.name,
            "axis": v.axis,
            "n_clear": len(cleared),
            "n_instruments": len(instruments),
            "instruments": ";".join(instruments),
            "sum_margin_bps": float(np.sum(margins)) if margins else 0.0,
            "composition_met": (
                v.axis != "baseline"
                and len(cleared) >= G1_MIN_CELLS
                and len(instruments) >= G1_MIN_INSTRUMENTS
            ),
        })
    return out
