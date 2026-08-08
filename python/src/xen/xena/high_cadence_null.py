"""P0′ high-cadence random-entry null universe (INFR-009 / consolidated-03 §5).

Prerequisite emission for LCB coverage at high cadence (P3 CAL). XENA-001/002 are
low-cadence; XENA-003 is high-cadence but **not** zero-edge — so no high-cadence
zero-edge anchor existed. This module builds a production-scale synthetic null:

* zero entry-level predictive content (coin-flip direction; E[gross]=0)
* high trade density matching the 003 class (~thousands of legs / candidate)
* matched candidate count, domain/hold grid shape, search budget hooks, and
  execution contract (bar-grid fills; finite StopDistance)

No search tuning. No calibration numbers frozen here. Engine-emitted twin (cTrader
random-entry model at 003 density) remains an operator-run option for live-price
CAL; this generator unblocks unit tests + offline CAL design now.

Verify: entry edge ≈ 0; median legs/candidate in the 003 density band.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream

NS = 1_000_000_000

# Observed live cadence bands (descriptive anchors from XENA-001 vs XENA-003 emissions)
LOW_CADENCE_LEGS_BAND = (50, 2_000)       # 001-class per candidate over ~21 mo search
HIGH_CADENCE_LEGS_BAND = (2_000, 15_000)  # 003-class


@dataclass(frozen=True)
class HighCadenceNullSpec:
    """Matched production-scale null layout (procedure, not a frozen score)."""
    n_candidates: int = 96          # smaller than 2736 for unit use; scale up for CAL
    n_bars: int = 50_000            # ~dense LTF grid
    bar_seconds: int = 60
    target_legs_per_candidate: int = 5_000
    hold_bars: int = 12
    stop_price_units: float = 1.0
    cost_bps: float = 0.0           # zero-cost model (INFR-022): inert pin; default 0
    money_per_unit: float = 1.0
    edge_bps: float = 0.0           # zero entry-level predictive content
    noise_bps: float = 8.0
    seed: int = 20260713


def _candidate_stream(cid: str, *, opens: np.ndarray, times: np.ndarray,
                      entry_idx: np.ndarray, direction: np.ndarray,
                      hold_bars: int, stop: float, cost_bps: float,
                      money_per_unit: float, symbol: str = "USTEC",
                      edge_bps: float = 0.0) -> CandidateStream:
    n = len(times)
    rows = []
    for ei, d in zip(entry_idx, direction):
        xi = min(int(ei) + hold_bars, n - 1)
        ep = float(opens[int(ei)])
        raw_exit = float(opens[xi])
        # Planted edge (P-BF bite): favourable exit shift along direction (path_universe style).
        # Zero-edge: direction independent of path → E[gross]=0.
        xp = raw_exit * (1.0 + float(d) * float(edge_bps) / 1e4)
        rows.append({
            "EntryTime": int(times[int(ei)]),
            "ExitTime": int(times[xi]),
            "Direction": float(d),
            "EntryPrice": ep,
            "ExitPrice": xp,
            "StopDistance": float(stop),
            "Censored": False,
        })
    trades = pl.DataFrame(rows, schema={
        "EntryTime": pl.Int64, "ExitTime": pl.Int64, "Direction": pl.Float64,
        "EntryPrice": pl.Float64, "ExitPrice": pl.Float64,
        "StopDistance": pl.Float64, "Censored": pl.Boolean,
    })
    marks = pl.DataFrame({"CloseTime": times, "Open": opens})
    return CandidateStream(cid, symbol, trades, marks, float(cost_bps),
                           float(money_per_unit))


def build_high_cadence_null(spec: HighCadenceNullSpec = HighCadenceNullSpec()
                            ) -> list[CandidateStream]:
    """Build a high-cadence zero-edge universe on one shared path (correlated noise).

    Shared path ⇒ harder null (cross-candidate correlation), matching calibration
    path_universe discipline. Directions are coin-flips independent of path.
    """
    rng = np.random.default_rng(spec.seed)
    # mild GBM path — direction coin-flip kills drift edge
    rets = rng.normal(0.0, spec.noise_bps / 1e4, size=spec.n_bars)
    opens = 100.0 * np.exp(np.cumsum(rets))
    opens = np.maximum(opens, 1e-6)
    times = np.arange(spec.n_bars, dtype=np.int64) * spec.bar_seconds * NS

    streams: list[CandidateStream] = []
    # leave margin at ends for holds
    lo, hi = 50, spec.n_bars - spec.hold_bars - 5
    n_slots = hi - lo
    for i in range(spec.n_candidates):
        # staggered dense entries; slight per-candidate phase so not identical bitmasks
        phase = int(rng.integers(0, max(1, n_slots // spec.target_legs_per_candidate)))
        step = max(1, n_slots // spec.target_legs_per_candidate)
        idx = np.arange(lo + phase, hi, step, dtype=int)
        if len(idx) > spec.target_legs_per_candidate:
            idx = idx[: spec.target_legs_per_candidate]
        direction = rng.choice([-1.0, 1.0], size=len(idx))
        domains = ["1H5M", "4H15M", "1D1H"]
        holds = ["H05X", "H1X", "H2X", "H4X"]
        variants = ["V00", "V01", "V02", "V03"]
        dom = domains[i % len(domains)]
        hold = holds[(i // len(domains)) % len(holds)]
        var = variants[(i // (len(domains) * len(holds))) % len(variants)]
        prefix = "HCPLANT" if abs(spec.edge_bps) > 0 else "HCNULL"
        cid = f"{prefix}-USTEC-{dom}-{hold}-{var}-{i:04d}"
        streams.append(_candidate_stream(
            cid, opens=opens, times=times, entry_idx=idx, direction=direction,
            hold_bars=spec.hold_bars, stop=spec.stop_price_units,
            cost_bps=spec.cost_bps, money_per_unit=spec.money_per_unit,
            edge_bps=spec.edge_bps,
        ))
    return streams


def null_diagnostics(streams: list[CandidateStream]) -> dict[str, Any]:
    """Verify zero entry-edge and 003-class cadence (descriptive)."""
    means = []
    n_legs = []
    for s in streams:
        tr = s.trades
        if tr.height == 0:
            continue
        d = tr.get_column("Direction").to_numpy()
        ep = tr.get_column("EntryPrice").to_numpy()
        xp = tr.get_column("ExitPrice").to_numpy()
        bps = d * (xp - ep) / ep * 1e4
        means.append(float(np.mean(bps)))
        n_legs.append(int(tr.height))
    means_a = np.array(means, dtype=float) if means else np.array([0.0])
    legs_a = np.array(n_legs, dtype=float) if n_legs else np.array([0.0])
    med_legs = float(np.median(legs_a))
    return {
        "n_candidates": len(streams),
        "entry_edge_mean_of_means_bps": float(np.mean(means_a)),
        "entry_edge_median_of_means_bps": float(np.median(means_a)),
        "entry_edge_abs_p95_bps": float(np.quantile(np.abs(means_a), 0.95)),
        "legs_per_candidate_median": med_legs,
        "legs_per_candidate_p05": float(np.quantile(legs_a, 0.05)),
        "legs_per_candidate_p95": float(np.quantile(legs_a, 0.95)),
        "cadence_class": (
            "high" if med_legs >= HIGH_CADENCE_LEGS_BAND[0] else
            ("low" if med_legs <= LOW_CADENCE_LEGS_BAND[1] else "mid")
        ),
        "zero_edge_ok": bool(abs(float(np.mean(means_a))) < 1.0),  # <1 bps sampling
        "high_cadence_ok": bool(med_legs >= HIGH_CADENCE_LEGS_BAND[0]),
        "predictive_content": "none (coin-flip direction on shared path)",
        "search_tuning": False,
        "role": "P0_prime_prerequisite_for_P3_CAL",
        "binding_scores_frozen": False,
    }
