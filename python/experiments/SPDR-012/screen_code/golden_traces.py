"""Hand-checkable golden traces G1-G3 (design §8).

Each trace re-derives a screen number from first principles on a named row and compares it
with the pipeline output. Values are emitted in full so an operator can redo the arithmetic.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_minute_bars
from config import CONFIRM_END, DESIGN_START, NS, RV_WINDOW, SHUFFLE_SEEDS
from features import add_regime_states, build_features
from pipeline import prepare_cell
from stats_core import spearman

G1_AFTER = datetime(2022, 9, 14, tzinfo=timezone.utc)


def _iso(ns: int) -> str:
    return datetime.fromtimestamp(int(ns) / NS, tz=timezone.utc).isoformat()


def trace_g1(manifest) -> dict:
    """G1 — BTCUSDT H4 rv20 recomputed by hand from 20 prior H4 log closes (rel tol 1e-9)."""
    minutes = load_minute_bars("BTCUSDT", DESIGN_START, CONFIRM_END, manifest=manifest)
    bars = aggregate_clock(minutes, "H4")
    feats = build_features(bars, "H4")
    after = int(G1_AFTER.timestamp() * NS)
    sel = feats.filter(
        (pl.col("slot_start") >= after)
        & pl.col("rv20").is_not_null()
        & pl.col("rv20").is_not_nan()
    )
    if sel.height == 0:
        return {"pass": False, "reason": "no eligible H4 bar"}
    i = int(np.flatnonzero(feats["slot_start"].to_numpy() == sel["slot_start"][0])[0])
    closes = feats["close"].to_numpy()
    r = np.log(closes[i - RV_WINDOW + 1 : i + 1] / closes[i - RV_WINDOW : i])
    manual = float(np.sqrt(np.mean(r**2)))
    screen = float(feats["rv20"][i])
    rel = abs(manual - screen) / max(abs(manual), 1e-18)
    return {
        "pass": bool(rel < 1e-9),
        "symbol": "BTCUSDT", "clock": "H4",
        "bar_slot_start_utc": _iso(feats["slot_start"][i]),
        "bar_slot_end_utc": _iso(feats["slot_end"][i]),
        "closes_used": closes[i - RV_WINDOW : i + 1].tolist(),
        "log_returns": r.tolist(),
        "rv20_manual": manual, "rv20_screen": screen, "rel_error": rel,
    }


def trace_g2(manifest) -> dict:
    """G2 — ETHUSDT H1 V-LEVEL origin: feature vector uses no bar at or after the target."""
    cell = prepare_cell("ETHUSDT", "H1", manifest)
    d = cell.design.filter(pl.col("oos")) if cell.design.height else cell.design
    if d.height == 0:
        return {"pass": False, "reason": "no ETHUSDT H1 DESIGN origin"}
    row = d.row(d.height // 2, named=True)
    span = 3600 * NS
    checks = {
        "origin_is_bar_close": row["slot_end"] == row["slot_start"] + span,
        "target_bar_starts_at_origin": row["target_slot_start"] == row["slot_end"],
        "features_precede_target_bar": row["slot_end"] <= row["target_slot_start"],
    }
    return {
        "pass": all(checks.values()),
        "symbol": "ETHUSDT", "clock": "H1",
        "origin_slot_start_utc": _iso(row["slot_start"]),
        "origin_slot_end_utc": _iso(row["slot_end"]),
        "target_bar_start_utc": _iso(row["target_slot_start"]),
        "feature_vector": {k: row[k] for k in ("rv20", "ewma_vol", "parkinson", "gk")},
        "target_abs_oo_bps": row["target_abs_oo"],
        "origin_known_variant_oo_move_bps": row["oo_move"],
        "checks": checks,
        "note": (
            "features are realised measures of bars ending at or before slot_end; the target "
            "is the open-to-open move of the NEXT bar, entered at that bar's open"
        ),
    }


def trace_g3(manifest) -> dict:
    """G3 — SOLUSDT time-shuffle seed 101 changes the IC away from the live value."""
    cell = prepare_cell("SOLUSDT", "H4", manifest)
    if cell.design.height == 0:
        return {"pass": False, "reason": "no SOLUSDT H4 DESIGN origins"}
    d = cell.design.filter(pl.col("oos"))
    pred = d["pred__vlevel_ridge__target_abs_oo"].to_numpy()
    y = d["target_abs_oo"].to_numpy()
    m = np.isfinite(pred) & np.isfinite(y)
    pred, y = pred[m], y[m]
    live = spearman(pred, y)
    rng = np.random.default_rng(SHUFFLE_SEEDS[0])
    k = int(rng.integers(1, pred.size))
    shuffled = spearman(np.roll(pred, k), y)
    return {
        "pass": bool(np.isfinite(live) and np.isfinite(shuffled) and live != shuffled),
        "symbol": "SOLUSDT", "clock": "H4", "seed": int(SHUFFLE_SEEDS[0]),
        "n_obs": int(pred.size), "circular_shift": k,
        "live_ic": live, "shuffled_ic": shuffled, "delta": live - shuffled,
        "note": "CIRCULAR_SHIFT has no fixed-point concept; the check is that the IC moves",
    }


def run_golden_traces(manifest) -> dict:
    return {"G1": trace_g1(manifest), "G2": trace_g2(manifest), "G3": trace_g3(manifest)}
