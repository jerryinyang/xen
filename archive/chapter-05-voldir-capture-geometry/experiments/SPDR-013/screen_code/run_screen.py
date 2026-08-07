"""SPDR-013 orchestrator — direction expectancy (SMA + ZigZag) under §4 TF capture geometry
with EXIT-MODE decomposition (AMENDMENT-A3) and the future-destroy tripwire demoted to
informative (DEV-1, operator-signed 2026-07-23).

TRAIN-only. Recomputes + asserts the top-25 universe pin, builds H1 and M15 decision clocks per
symbol, runs each direction signal (6 D-SMA cells + D-ZZ) under 5 exit modes {combined, stop,
trail, time, signalflip} on the DESIGN (primary) and CONFIRM (verify) bands, applies partial
costs, decomposes expectancy (§5 + medians), attaches date-block CIs + §7.2 bands (thirds-gated
SUPPORTED), runs the controls (§6), the ZZ next-move forecast heads (§3.3), and emits every result
artifact (§10) plus the integrity self-check and golden traces.

Usage:
    python run_screen.py                 # full run
    python run_screen.py --limit 3       # first 3 universe symbols (BTC/ETH/SOL)
    python run_screen.py --skip-matched-random
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
from capture import horizon_excursion, simulate_signal
from catalog_io import aggregate_clock, load_minute_bars
from config import (
    BANDS,
    CLOCK_ORDER,
    CLOCKS,
    CONFIRM_END,
    DESIGN_START,
    DEVIATIONS,
    EXIT_MODE_RANDOM_GEOM,
    EXIT_MODES,
    INTERPRETATION_NOTES,
    PLOTS_DIR,
    PRIMARY_BAND,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
    UNIT_PIN,
    ZZ_STRUCTURAL_EXIT_MODE,
)
from controls import (
    build_random_cache,
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
_TRIPWIRE_SIGNAL = "D-SMA14_angle-off"   # design §6 metric = expectancy_partial on D-SMA14
_TRIPWIRE_EXIT = "combined"              # the actual strategy (full §4 stack)


# --------------------------------------------------- per-symbol prep ----


def prepare_clock(symbol: str, clock: str, manifest) -> dict | None:
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


# ------------------------------------------------------- cell record ----


def _cell_record(eps: list[dict], clock: str, band: str, arm_key: str, signal_key: str,
                 exit_mode: str, symbol: str, lo: int, hi: int) -> dict:
    gross = np.array([e["gross_bps"] for e in eps], float)
    partial = np.array([e["partial_net_bps"] for e in eps], float)
    dates = np.array([e["entry_ts"] // _DAY_NS for e in eps]) if eps else np.array([])
    dec = decomposition(gross, partial)
    boot = boot_mean(partial, dates) if eps else None
    ci_low = boot.ci_low if boot else float("nan")
    ci_high = boot.ci_high if boot else float("nan")
    se = boot.se if boot else float("nan")
    n_dates = boot.n_dates if boot else 0
    thirds_sign = _thirds_sign(eps, lo, hi, dec["expectancy_partial"])
    label = band_expectancy(dec["expectancy_partial"], ci_low, ci_high,
                            dec["n_episodes"], n_dates, se, thirds_sign)
    return {
        "symbol": symbol, "signal": signal_key, "exit_mode": exit_mode,
        "symbol_arm": arm_key, "clock": clock, "band": band, **dec,
        "ci_low": ci_low, "ci_high": ci_high, "se": se, "mde_bps": mde_from_se(se),
        "n_dates": n_dates, "thirds_sign_agree": thirds_sign, "band_label": label,
        "avail_vs_damage": (abs(dec["avail_when_right"]) - abs(dec["damage_when_wrong"])),
    }


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


# --------------------------------------------------- per-symbol worker ----


def process_symbol(symbol: str, geoms: list, skip_matched_random: bool) -> dict:
    """All work for one symbol (independent unit; safe to run in a forked worker). Returns partial
    result lists/dicts merged by the parent. Fixed seeds → order-independent, deterministic."""
    manifest = load_fence_manifest()
    cell_records: list[dict] = []
    all_episodes: list[dict] = []
    controls_out: dict = {}
    zz_features_rows: list[dict] = []
    zz_forecast_out: dict = {}
    golden: dict = {}
    for clock in CLOCK_ORDER:
        prep = prepare_clock(symbol, clock, manifest)
        if prep is None:
            continue
        cap = CLOCKS[clock]["time_cap_bars"]
        ss_full = prep["slot_start"]
        if symbol == "BTCUSDT" and clock == "H1":
            golden["G1"] = g1_sma_flip(prep["close"], prep["open"], ss_full, prep["atr_lag"])
            golden["engine_parity_BTC_H1"] = engine_parity(
                prep["open"], prep["high"], prep["low"], prep["atr"], ss_full)
        if symbol == "SOLUSDT" and clock == "H1":
            golden["G3"] = g3_zz_swing(prep["high"], prep["low"], prep["close"])

        sws = prep["swings"]
        for i, sw in enumerate(sws):
            nxt = sws[i + 1] if i + 1 < len(sws) else None
            zz_features_rows.append({
                "symbol": symbol, "clock": clock,
                "confirm_ts": int(ss_full[min(sw.confirm_idx, ss_full.size - 1)]),
                "direction": sw.direction, "magnitude_bps": sw.magnitude_bps,
                "angle_bps_per_bar": sw.angle_bps_per_bar, "path_noise_atr": sw.path_noise_atr,
                "bars_in_swing": sw.bars_in_swing,
                "next_magnitude_bps": (nxt.magnitude_bps if nxt else None),
                "next_path_noise_atr": (nxt.path_noise_atr if nxt else None),
                "next_direction": (nxt.direction if nxt else None),
            })
        zz_forecast_out[f"{symbol}__{clock}"] = walk_forward(sws)

        block_bars = max(1, 60 // CLOCKS[clock]["minutes"])
        for band in BANDS:
            blo = int(BANDS[band][0].timestamp() * 1e9)
            bhi = int(BANDS[band][1].timestamp() * 1e9)
            nsub = int((ss_full < bhi).sum())
            if nsub <= prep["start"] + 5:
                continue
            sl = slice(0, nsub)
            ss = ss_full[sl]
            op, hi_, lo_, at = prep["open"][sl], prep["high"][sl], prep["low"][sl], prep["atr"][sl]
            cache = ({} if skip_matched_random
                     else build_random_cache(op, hi_, lo_, at, prep["start"], geoms, cap))
            for signal_key, sig_full in prep["signals"].items():
                sig = sig_full[:nsub].copy()
                sig[ss < blo] = 0.0
                for mode, flags in EXIT_MODES.items():
                    arm_key = f"{symbol}__{signal_key}__exit-{mode}"
                    eps = apply_costs(simulate_signal(
                        ss, op, hi_, lo_, at, sig, cap, prep["start"], **flags))
                    if eps:   # fixed-horizon availability ceiling (MFE/MAE over entry..entry+cap)
                        ei = np.array([e["entry_idx"] for e in eps])
                        sd = np.array([e["side"] for e in eps])
                        hz = horizon_excursion(op, hi_, lo_, ei, sd, cap)
                        for i, e in enumerate(eps):
                            e["horizon_mfe_oo_bps"] = float(hz["horizon_mfe_oo_bps"][i])
                            e["horizon_mae_oo_bps"] = float(hz["horizon_mae_oo_bps"][i])
                            e["horizon_mfe_hi_bps"] = float(hz["horizon_mfe_hi_bps"][i])
                    for e in eps:
                        e["symbol_arm"] = arm_key
                    cell_records.append(_cell_record(
                        eps, clock, band, arm_key, signal_key, mode, symbol, blo, bhi))
                    for e in eps:
                        all_episodes.append({**e, "symbol": symbol, "clock": clock,
                                             "band": band, "signal": signal_key,
                                             "exit_mode": mode})
                    ckey = f"{arm_key}__{clock}__{band}"
                    cinfo = {"derangement": direction_derangement(eps, blo, bhi)}
                    if signal_key == _TRIPWIRE_SIGNAL and mode == _TRIPWIRE_EXIT:
                        cinfo["tripwire_path_future_destroy"] = path_future_destroy(eps, blo, bhi)
                    if not skip_matched_random:
                        cinfo["matched_random"] = matched_random_entry(
                            ss, at, eps, prep["start"], blo, bhi,
                            cache[EXIT_MODE_RANDOM_GEOM[mode]], block_bars)
                    controls_out[ckey] = cinfo
    return {"cells": cell_records, "episodes": all_episodes, "controls": controls_out,
            "zzfeat": zz_features_rows, "zzfore": zz_forecast_out, "golden": golden}


def _process_symbol_star(args_tuple) -> dict:
    return process_symbol(*args_tuple)


# ------------------------------------------------------------- main ----


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-matched-random", action="store_true")
    ap.add_argument("--jobs", type=int, default=1, help="parallel symbol workers (fork pool)")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    manifest = load_fence_manifest()

    print("recomputing universe (top-25 pin assert)...")
    recomputed = recompute_universe(manifest)
    pin_report = assert_pin(recomputed)
    (RESULTS_DIR / "universe_recomputed.json").write_text(json.dumps(recomputed, indent=2))
    universe = recomputed["symbols"]
    if args.limit:
        universe = universe[: args.limit]

    geoms = sorted(set(EXIT_MODE_RANDOM_GEOM.values()))
    golden = {"interpretation_notes": [n["id"] for n in INTERPRETATION_NOTES],
              "G3_independent": g3_independent_fixture()}

    # Symbols are fully independent (fixed seeds, per-symbol-local caches) → embarrassingly
    # parallel. --jobs N forks a process pool over symbols (safe: no shared mutable state, results
    # merged in the parent; row order is not statistically meaningful). --jobs 1 = sequential.
    work = [(s, geoms, bool(args.skip_matched_random)) for s in universe]
    if args.jobs and args.jobs > 1:
        import multiprocessing as mp
        # SPAWN, not fork: the parent has already run multithreaded numpy/polars/pyarrow work
        # (universe recompute) before this pool, and fork-after-threads deadlocks the children.
        # Spawn starts fresh interpreters; they inherit the parent's sys.path + PYTHONPATH so the
        # sibling modules and `xen` import cleanly, and each worker reloads the fence manifest.
        ctx = mp.get_context("spawn")
        with ctx.Pool(min(args.jobs, len(work))) as pool:
            parts = list(tqdm(pool.imap(_process_symbol_star, work),
                              total=len(work), desc=f"symbols x{args.jobs}"))
    else:
        parts = [process_symbol(*w) for w in tqdm(work, desc="symbols")]

    cell_records: list[dict] = []
    all_episodes: list[dict] = []
    controls_out: dict = {}
    zz_features_rows: list[dict] = []
    zz_forecast_out: dict = {}
    for p in parts:
        cell_records.extend(p["cells"])
        all_episodes.extend(p["episodes"])
        controls_out.update(p["controls"])
        zz_features_rows.extend(p["zzfeat"])
        zz_forecast_out.update(p["zzfore"])
        golden.update(p["golden"])   # only BTC/SOL workers populate G1/G3/parity

    # SMA benchmark deltas (ZZ combined vs SMA14/SMA25 angle-off combined)
    rec_by_key = {(r["symbol_arm"], r["clock"], r["band"]): r for r in cell_records}
    bench = {}
    for symbol in universe:
        for clock in CLOCK_ORDER:
            for band in BANDS:
                zz = rec_by_key.get((f"{symbol}__D-ZZ__exit-combined", clock, band))
                for ref in ("D-SMA14_angle-off", "D-SMA25_angle-off"):
                    sm = rec_by_key.get((f"{symbol}__{ref}__exit-combined", clock, band))
                    if zz and sm:
                        bench[f"{symbol}__{clock}__{band}__ZZ_vs_{ref}"] = sma_benchmark_delta(
                            zz, sm)
    controls_out["sma_benchmark_delta"] = bench

    _emit(cell_records, all_episodes, zz_features_rows, controls_out, zz_forecast_out,
          golden, pin_report, universe, t0)


def _emit(cell_records, all_episodes, zz_features_rows, controls_out, zz_forecast_out,
          golden, pin_report, universe, t0) -> None:
    pl.DataFrame(cell_records).write_parquet(RESULTS_DIR / "expectancy_by_cell.parquet")
    if all_episodes:
        pl.DataFrame(all_episodes).write_parquet(RESULTS_DIR / "episodes.parquet")
    if zz_features_rows:
        pl.DataFrame(zz_features_rows).write_parquet(RESULTS_DIR / "zz_features.parquet")
    (RESULTS_DIR / "controls.json").write_text(json.dumps(controls_out, indent=2, default=float))
    (RESULTS_DIR / "zz_forecast.json").write_text(json.dumps(zz_forecast_out, indent=2,
                                                             default=float))
    (RESULTS_DIR / "golden_traces.json").write_text(json.dumps(golden, indent=2, default=float))
    integ = _integrity(all_episodes, golden, pin_report, controls_out)
    (RESULTS_DIR / "integrity_selfcheck.json").write_text(json.dumps(integ, indent=2, default=float))
    print(f"\nDONE in {time.time()-t0:.0f}s | cells={len(cell_records)} "
          f"episodes={len(all_episodes)} | integrity PASS={integ['all_pass']}")
    if not integ["all_pass"]:
        print("  FAILED CHECKS:", [k for k, v in integ["checks"].items() if not v])


def _integrity(all_episodes, golden, pin_report, controls_out) -> dict:
    train_end_ns = int(CONFIRM_END.timestamp() * 1e9)
    holdout_ns = int(datetime(2025, 1, 8, tzinfo=timezone.utc).timestamp() * 1e9)
    exits = np.array([e["exit_ts"] for e in all_episodes]) if all_episodes else np.array([0])
    entries_dec_ok = all(e["entry_idx"] > 0 for e in all_episodes)
    # future-destroy tripwire: INFORMATIVE only (DEV-1). Applicability-correct residual HARD check:
    # no cell CLAIMING a positive edge (live>0) may survive above the destroyed-null p95.
    tw = [v["tripwire_path_future_destroy"] for v in controls_out.values()
          if isinstance(v, dict) and "tripwire_path_future_destroy" in v]
    tw_pow = [t for t in tw if t.get("powered")]
    positive_edge_survivors = [t for t in tw_pow if t.get("hard_concern_positive_edge_survives")]
    checks = {
        "train_only_max_exit_lt_train_end": bool(exits.max() < train_end_ns),
        "no_holdout_contact": bool(exits.max() < holdout_ns),
        "entry_after_signal_bar": bool(entries_dec_ok),
        "universe_pin_set_equal": bool(pin_report.get("set_equal_all", False)),
        "g1_sma_match": bool(golden.get("G1", {}).get("sma_match", False)),
        "g1_side_confirms": bool(golden.get("G1", {}).get("side_confirms", False)),
        "g2_stop_next_open": bool(g2_stop_rule().get("exit_is_next_open_after_touch", False)),
        "g3_zz_features_match": bool(golden.get("G3", {}).get("match", False)),
        "g3_independent_fixture_match": bool(golden.get("G3_independent", {}).get("match", False)),
        "engine_parity": bool(golden.get("engine_parity_BTC_H1", {}).get("parity_ok", False)),
        "all_deviations_operator_signed": all(d.get("operator_sign_off") for d in DEVIATIONS),
        "no_positive_edge_future_destroy_concern": (len(positive_edge_survivors) == 0),
    }
    return {
        "checks": checks, "all_pass": all(checks.values()),
        "max_exit_ts": int(exits.max()), "train_end_ns": train_end_ns,
        "tripwire_gating": "INFORMATIVE_ONLY_DEV1",
        "tripwire_powered_cells": len(tw_pow),
        "tripwire_survivors_any": sum(1 for t in tw_pow
                                      if t.get("live_survives_above_null_p95")),
        "tripwire_positive_edge_survivors": len(positive_edge_survivors),
        "deviations": [d["id"] for d in DEVIATIONS],
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE, "unit_pin": UNIT_PIN,
        "interpretation_notes": [n["id"] for n in INTERPRETATION_NOTES],
        "primary_band": PRIMARY_BAND,
    }


if __name__ == "__main__":
    main()
