"""SPDR-013 orchestrator — direction expectancy (SMA + ZigZag) under §4 TF capture geometry.

TRAIN-only. Recomputes + asserts the top-25 universe pin, builds H1 and M15 decision clocks per
symbol, runs the D-SMA (3 periods x 2 angle) and D-ZZ arms through the frozen capture engine on the
DESIGN (primary) and CONFIRM (verify) bands, applies partial costs, decomposes expectancy (§5),
attaches date-block CIs + §7.2 bands, runs the controls (§6), the ZZ next-move forecast heads
(§3.3), and emits every result artifact (§10) plus the integrity self-check and golden traces.

Usage:
    python run_screen.py                 # full run (25 symbols, both clocks, all controls)
    python run_screen.py --limit 2       # smoke on first 2 universe symbols
    python run_screen.py --skip-matched-random   # skip the expensive matched-random control
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

import numpy as np
import polars as pl
from tqdm import tqdm

from xen.nautilus.catalog_fence import load_fence_manifest

from arms import sma_cells, zz_signal
from capture import simulate_signal
from catalog_io import aggregate_clock, load_minute_bars
from config import (
    BANDS,
    CLOCK_ORDER,
    CLOCKS,
    CONFIRM_END,
    DESIGN_START,
    DEVIATIONS,
    INTERPRETATION_NOTES,
    PLOTS_DIR,
    PRIMARY_BAND,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
    THIRDS_SIGN_MIN,
    UNIT_PIN,
)
from controls import (
    direction_derangement,
    matched_random_entry,
    path_future_destroy,
    sma_benchmark_delta,
)
from expectancy import apply_costs, decomposition
from golden_traces import (
    engine_parity,
    g1_sma_flip,
    g2_stop_rule,
    g3_independent_fixture,
    g3_zz_swing,
)
from indicators import atr_zigzag, wilder_atr
from stats_core import band_expectancy, boot_mean, mde_from_se
from universe import assert_pin, recompute_universe
from zz_forecast import walk_forward

_DAY_NS = 86_400_000_000_000


# --------------------------------------------------- per-symbol prep ----


def prepare_clock(symbol: str, clock: str, manifest) -> dict | None:
    """Load fenced 1m bars over [DESIGN_START, CONFIRM_END), aggregate to ``clock`` complete bars,
    build ATR/lagged-ATR and the arm signals. Returns arrays or None if too sparse."""
    minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)
    if minutes.height == 0:
        return None
    bars = aggregate_clock(minutes, clock).filter(pl.col("complete"))
    if bars.height < CLOCKS[clock]["warmup_bars"] + 10:
        return None
    slot_start = bars["slot_start"].to_numpy().astype(np.int64)
    open_ = bars["open"].to_numpy().astype(float)
    high = bars["high"].to_numpy().astype(float)
    low = bars["low"].to_numpy().astype(float)
    close = bars["close"].to_numpy().astype(float)
    atr = wilder_atr(high, low, close)
    atr_lag = np.concatenate([[np.nan], atr[:-1]])
    start = int(np.argmax(np.isfinite(atr)))
    swings = atr_zigzag(close, atr, start)
    signals = {f"D-SMA{p}_angle-{m}": s for (p, m), s in sma_cells(close, atr_lag).items()}
    signals["D-ZZ"] = zz_signal(close.size, swings)
    return {
        "slot_start": slot_start, "open": open_, "high": high, "low": low, "close": close,
        "atr": atr, "atr_lag": atr_lag, "start": start, "swings": swings, "signals": signals,
    }


# ------------------------------------------------------- cell compute ----


def compute_cell(prep: dict, clock: str, band: str, arm_key: str, signal: np.ndarray) -> dict:
    """Run one (symbol, clock, band, arm-cell) through capture -> costs -> decomposition ->
    bootstrap CI -> §7.2 band -> thirds sign stability. Returns cell record + episodes."""
    lo, hi = (int(BANDS[band][0].timestamp() * 1e9), int(BANDS[band][1].timestamp() * 1e9))
    ss = prep["slot_start"]
    sub = ss < hi
    n_sub = int(sub.sum())
    sig_band = signal[:n_sub].copy()
    sig_band[ss[:n_sub] < lo] = 0.0
    eps = simulate_signal(
        ss[:n_sub], prep["open"][:n_sub], prep["high"][:n_sub], prep["low"][:n_sub],
        prep["atr"][:n_sub], sig_band, CLOCKS[clock]["time_cap_bars"], prep["start"],
    )
    eps = apply_costs(eps)
    for e in eps:
        e["symbol_arm"] = arm_key
    gross = np.array([e["gross_bps"] for e in eps], float)
    partial = np.array([e["partial_net_bps"] for e in eps], float)
    dates = np.array([e["entry_ts"] // _DAY_NS for e in eps]) if eps else np.array([])
    dec = decomposition(gross, partial)
    boot = boot_mean(partial, dates) if eps else None
    ci_low = boot.ci_low if boot else float("nan")
    ci_high = boot.ci_high if boot else float("nan")
    se = boot.se if boot else float("nan")
    n_dates = boot.n_dates if boot else 0
    # thirds sign stability (§7.1) — gates SUPPORTED eligibility
    thirds_sign = _thirds_sign(eps, lo, hi, dec["expectancy_partial"])
    label = band_expectancy(dec["expectancy_partial"], ci_low, ci_high,
                            dec["n_episodes"], n_dates, se, thirds_sign)
    rec = {
        "symbol_arm": arm_key, "clock": clock, "band": band, **dec,
        "ci_low": ci_low, "ci_high": ci_high, "se": se, "mde_bps": mde_from_se(se),
        "n_dates": n_dates, "thirds_sign_agree": thirds_sign,
        "band_label": label,
        "avail_vs_damage": (abs(dec["avail_when_right"]) - abs(dec["damage_when_wrong"])),
    }
    return {"record": rec, "episodes": eps, "boot": boot,
            "band_lo": lo, "band_hi": hi, "n_sub": n_sub}


def _thirds_sign(eps: list[dict], lo: int, hi: int, overall: float) -> int:
    if not eps or not np.isfinite(overall) or overall == 0:
        return 0
    span = max(1, hi - lo)
    signs = []
    for t in (0, 1, 2):
        vals = [e["partial_net_bps"] for e in eps
                if int(((e["entry_ts"] - lo) / span) * 3) == t]
        if vals:
            signs.append(np.sign(np.mean(vals)))
    if not signs:
        return 0
    return int(sum(1 for s in signs if s == np.sign(overall)))


# ------------------------------------------------------------- main ----


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="first N universe symbols (0=all)")
    ap.add_argument("--skip-matched-random", action="store_true")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    manifest = load_fence_manifest()

    # ---- universe pin (design §0.1) ----
    print("recomputing universe (top-25 pin assert)...")
    recomputed = recompute_universe(manifest)
    pin_report = assert_pin(recomputed)
    (RESULTS_DIR / "universe_recomputed.json").write_text(json.dumps(recomputed, indent=2))
    universe = recomputed["symbols"]
    if args.limit:
        universe = universe[: args.limit]

    cell_records: list[dict] = []
    all_episodes: list[dict] = []
    controls_out: dict = {}
    zz_features_rows: list[dict] = []
    zz_forecast_out: dict = {}
    golden = {"interpretation_notes": [n["id"] for n in INTERPRETATION_NOTES]}
    golden["G3_independent"] = g3_independent_fixture()

    for si, symbol in enumerate(tqdm(universe, desc="symbols")):
        preps = {}
        for clock in CLOCK_ORDER:
            prep = prepare_clock(symbol, clock, manifest)
            if prep is None:
                continue
            preps[clock] = prep
            # golden traces (once, on the designated symbols/clock)
            if symbol == "BTCUSDT" and clock == "H1":
                golden["G1"] = g1_sma_flip(prep["close"], prep["open"], prep["slot_start"],
                                           prep["atr_lag"])
                golden["engine_parity_BTC_H1"] = engine_parity(
                    prep["open"], prep["high"], prep["low"], prep["atr"], prep["slot_start"])
            if symbol == "SOLUSDT" and clock == "H1":
                golden["G3"] = g3_zz_swing(prep["high"], prep["low"], prep["close"])

            # ---- ZZ features + NEXT-swing targets (§10 schema) + forecast heads ----
            sws = prep["swings"]
            for i, sw in enumerate(sws):
                nxt = sws[i + 1] if i + 1 < len(sws) else None
                zz_features_rows.append({
                    "symbol": symbol, "clock": clock, "confirm_ts": int(prep["slot_start"][
                        min(sw.confirm_idx, prep["slot_start"].size - 1)]),
                    "direction": sw.direction, "magnitude_bps": sw.magnitude_bps,
                    "angle_bps_per_bar": sw.angle_bps_per_bar, "path_noise_atr": sw.path_noise_atr,
                    "bars_in_swing": sw.bars_in_swing,
                    # next-swing forecast targets (mag = magnitude head; vol = path_noise head)
                    "next_magnitude_bps": (nxt.magnitude_bps if nxt else None),
                    "next_path_noise_atr": (nxt.path_noise_atr if nxt else None),
                    "next_direction": (nxt.direction if nxt else None),
                })
            zz_forecast_out[f"{symbol}__{clock}"] = walk_forward(prep["swings"])

            for band in BANDS:
                for arm_key_suffix, signal in prep["signals"].items():
                    arm_key = f"{symbol}__{arm_key_suffix}"
                    cell = compute_cell(prep, clock, band, arm_key, signal)
                    cell_records.append(cell["record"])
                    for e in cell["episodes"]:
                        e2 = dict(e)
                        e2.update({"symbol": symbol, "clock": clock, "band": band,
                                   "arm": arm_key_suffix})
                        all_episodes.append(e2)
                    # ---- controls (primary band = DESIGN; also CONFIRM for disclosure) ----
                    eps = cell["episodes"]
                    ckey = f"{arm_key}__{clock}__{band}"
                    cinfo = {"derangement": direction_derangement(eps, cell["band_lo"],
                                                                  cell["band_hi"])}
                    if arm_key_suffix == "D-SMA14_angle-off":
                        cinfo["tripwire_path_future_destroy"] = path_future_destroy(
                            eps, cell["band_lo"], cell["band_hi"])
                    if not args.skip_matched_random:
                        block_bars = max(1, 60 // CLOCKS[clock]["minutes"])   # +-1h in bars
                        cinfo["matched_random"] = matched_random_entry(
                            prep["open"][:cell["n_sub"]], prep["high"][:cell["n_sub"]],
                            prep["low"][:cell["n_sub"]], prep["atr"][:cell["n_sub"]],
                            prep["slot_start"][:cell["n_sub"]], eps,
                            CLOCKS[clock]["time_cap_bars"], prep["start"],
                            cell["band_lo"], cell["band_hi"], block_bars)
                    controls_out[ckey] = cinfo

    # ---- SMA benchmark deltas (ZZ vs SMA14/SMA25 angle-off), per symbol x clock x band ----
    rec_by_key = {(r["symbol_arm"], r["clock"], r["band"]): r for r in cell_records}
    bench = {}
    for symbol in universe:
        for clock in CLOCK_ORDER:
            for band in BANDS:
                zz = rec_by_key.get((f"{symbol}__D-ZZ", clock, band))
                for ref in ("D-SMA14_angle-off", "D-SMA25_angle-off"):
                    sm = rec_by_key.get((f"{symbol}__{ref}", clock, band))
                    if zz and sm:
                        bench[f"{symbol}__{clock}__{band}__ZZ_vs_{ref}"] = sma_benchmark_delta(
                            zz, sm)
    controls_out["sma_benchmark_delta"] = bench

    # ---- emit ----
    _emit(cell_records, all_episodes, zz_features_rows, controls_out, zz_forecast_out,
          golden, pin_report, recomputed, universe, args, t0)


def _emit(cell_records, all_episodes, zz_features_rows, controls_out, zz_forecast_out,
          golden, pin_report, recomputed, universe, args, t0) -> None:
    pl.DataFrame(cell_records).write_parquet(RESULTS_DIR / "expectancy_by_cell.parquet")
    if all_episodes:
        pl.DataFrame(all_episodes).write_parquet(RESULTS_DIR / "episodes.parquet")
    if zz_features_rows:
        pl.DataFrame(zz_features_rows).write_parquet(RESULTS_DIR / "zz_features.parquet")
    (RESULTS_DIR / "controls.json").write_text(json.dumps(controls_out, indent=2, default=float))
    (RESULTS_DIR / "zz_forecast.json").write_text(json.dumps(zz_forecast_out, indent=2,
                                                             default=float))
    (RESULTS_DIR / "golden_traces.json").write_text(json.dumps(golden, indent=2, default=float))

    # integrity self-check
    integ = _integrity(all_episodes, golden, pin_report, universe, controls_out)
    (RESULTS_DIR / "integrity_selfcheck.json").write_text(json.dumps(integ, indent=2, default=float))

    print(f"\nDONE in {time.time()-t0:.0f}s | cells={len(cell_records)} "
          f"episodes={len(all_episodes)} | integrity PASS={integ['all_pass']}")
    if not integ["all_pass"]:
        print("  FAILED CHECKS:", [k for k, v in integ["checks"].items() if not v])


def _integrity(all_episodes, golden, pin_report, universe, controls_out) -> dict:
    train_end_ns = int(CONFIRM_END.timestamp() * 1e9)
    holdout_ns = int(datetime(2025, 1, 8, tzinfo=timezone.utc).timestamp() * 1e9)
    exits = np.array([e["exit_ts"] for e in all_episodes]) if all_episodes else np.array([0])
    entries_dec_ok = all(e["entry_idx"] > 0 for e in all_episodes)   # entry uses open after signal
    # HARD future-destroy tripwire (§11): no powered D-SMA14 cell may survive above the
    # destroyed-null p95, and the +30 bps paired plant must collapse into the null envelope.
    tw = [v["tripwire_path_future_destroy"] for v in controls_out.values()
          if isinstance(v, dict) and "tripwire_path_future_destroy" in v]
    tw_pow = [t for t in tw if t.get("powered")]
    tripwire_ok = all(t.get("tripwire_pass", False) for t in tw_pow) if tw_pow else True
    checks = {
        "train_only_max_exit_lt_train_end": bool(exits.max() < train_end_ns),   # §8 strict <
        "no_holdout_contact": bool(exits.max() < holdout_ns),
        "entry_after_signal_bar": bool(entries_dec_ok),
        "universe_pin_set_equal": bool(pin_report.get("set_equal_all", False)),
        "g1_sma_match": bool(golden.get("G1", {}).get("sma_match", False)),
        "g1_side_confirms": bool(golden.get("G1", {}).get("side_confirms", False)),
        "g2_stop_next_open": bool(g2_stop_rule().get("exit_is_next_open_after_touch", False)),
        "g3_zz_features_match": bool(golden.get("G3", {}).get("match", False)),
        "g3_independent_fixture_match": bool(golden.get("G3_independent", {}).get("match", False)),
        "engine_parity": bool(golden.get("engine_parity_BTC_H1", {}).get("parity_ok", False)),
        "no_authorised_deviations": (len(DEVIATIONS) == 0),
        "tripwire_path_future_destroy_pass": bool(tripwire_ok),
    }
    return {
        "checks": checks, "all_pass": all(checks.values()),
        "max_exit_ts": int(exits.max()), "train_end_ns": train_end_ns,
        "tripwire_powered_cells": len(tw_pow),
        "tripwire_survivors": [i for i, t in enumerate(tw_pow)
                               if not t.get("tripwire_pass", False)][:20],
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE, "unit_pin": UNIT_PIN,
        "interpretation_notes": [n["id"] for n in INTERPRETATION_NOTES],
        "primary_band": PRIMARY_BAND,
    }


if __name__ == "__main__":
    main()
