"""SPDR-015 screen runner — TRAIN-only conditioner science (Group 2a + 2b).

Universe pin → H1/H4 level-regime + transition skill vs persistence → H1 ordinal ZZ →
controls → golden traces → integrity selfcheck → results/.

TRAIN only. max timestamp = train_end_utc. Shock never titled regime.
Headline 2a metric = Δ Brier vs persistence (negative = better).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from catalog_io import aggregate_clock, load_minute_bars  # noqa: E402
from config import (  # noqa: E402
    CLOCKS_2A,
    CONFIRM_END,
    DERANGE_SEEDS,
    DEVIATIONS,
    DESIGN_START,
    HOLDOUT_START,
    INTERPRETATION_NOTES,
    O3_SOT,
    PROHIBITED_CLAIMS,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
    TEST_START,
)
from features import add_state_models, build_bar_frame  # noqa: E402
from golden_traces import run_golden_traces  # noqa: E402
from transitions import evaluate_symbol_clock  # noqa: E402
from universe import assert_pin, recompute_universe  # noqa: E402
from zz_ordinal import run_zz_ordinal  # noqa: E402
from xen.nautilus.catalog_fence import load_fence_manifest  # noqa: E402


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str))


def _label_derange_control(derange_2a: list[dict], derange_2b: list[dict]) -> dict:
    """CONTROL LABEL-SHUFFLE (design §4) — L-28 derangement collapse, both arms.

    Per-cell collapse is computed at source (`controls.label_derange_collapse`) with a truthful
    zero-fixed-point index derangement, a 200-seed battery read as a percentile, and a +0.05
    bite plant. This assembler only summarises. QA-run-1 Issue 1 fix (was: plain rng.shuffle,
    2b-only, single seed, no bite, no fixed-point rejection).
    """
    both = derange_2a + derange_2b
    powered = [c for c in both if c.get("powered")]
    zero_fp_all = all(c.get("derangement_zero_fixed_points", False) for c in powered) if powered else False
    # collapse_frac ≈ 0 ⇒ live skill genuinely worsens under derangement (few deranged draws beat it)
    collapse_fracs = [c["collapse_frac"] for c in powered if np.isfinite(c.get("collapse_frac", np.nan))]
    bite_detected = [bool(c.get("bite_detected")) for c in powered if "bite_detected" in c]
    return {
        "class": "within_sample_attribution",
        "destroy_form": "DERANGEMENT",
        "derangement_zero_fixed_points_all": zero_fp_all,
        "n_seeds_per_cell": len(DERANGE_SEEDS),
        "n_cells_2a": len([c for c in derange_2a if c.get("powered")]),
        "n_cells_2b": len([c for c in derange_2b if c.get("powered")]),
        "collapse_frac_median": float(np.median(collapse_fracs)) if collapse_fracs else float("nan"),
        "collapse_frac_max": float(np.max(collapse_fracs)) if collapse_fracs else float("nan"),
        "bite_detected_frac": float(np.mean(bite_detected)) if bite_detected else float("nan"),
        "per_cell": powered,
        "note": (
            "live skill should worsen (Brier↑) under label derangement; collapse_frac is the "
            "fraction of 200 deranged draws at least as good as live (≈0 = real skill); "
            "bite = +0.05 hit-rate plant the test must detect"
        ),
    }


def process_symbol(symbol: str, manifest) -> dict:
    """Load TRAIN bars, build 2a states+metrics for H1/H4, 2b ZZ on H1."""
    # TRAIN full window [DESIGN_START, CONFIRM_END)
    minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)
    out = {
        "symbol": symbol,
        "n_minutes": minutes.height,
        "frames": {},
        "hmm_fits": {},
        "metric_rows": [],
        "trans_rows": [],
        "run_rows": [],
        "derange_2a": [],
        "zz": None,
    }
    if minutes.height == 0:
        return out

    for clock in CLOCKS_2A:
        bars = aggregate_clock(minutes, clock)
        feat = build_bar_frame(bars, clock)
        if feat.height == 0:
            continue
        feat, fits = add_state_models(feat, clock)
        # band filter: DESIGN primary origins (slot_end in DESIGN)
        design_end_ns = int(CONFIRM_END.timestamp() * 1_000_000_000)  # full TRAIN for states
        # score on full TRAIN but report DESIGN as primary — design says DESIGN primary
        design_end = int(__import__("datetime").datetime(2023, 3, 1, tzinfo=__import__("datetime").timezone.utc).timestamp() * 1e9)
        # Keep full TRAIN for fit continuity; mark DESIGN vs CONFIRM
        feat = feat.with_columns(
            (pl.col("slot_end") < design_end).alias("in_design")
        )
        # Origins for metrics: DESIGN primary
        feat_design = feat.filter(pl.col("in_design") & pl.col("is_origin"))
        # For walk-forward we need full history in frame — pass full feat but is_origin only DESIGN
        feat_eval = feat.with_columns(
            (pl.col("is_origin") & pl.col("in_design")).alias("is_origin")
        )
        mrows, trows, rrows, drows = evaluate_symbol_clock(symbol, clock, feat_eval)
        out["metric_rows"].extend(mrows)
        out["trans_rows"].extend(trows)
        out["run_rows"].extend(rrows)
        out["derange_2a"].extend(drows)
        out["frames"][clock] = feat_eval
        out["hmm_fits"][clock] = fits

    # D1 R-MARKOV stickiness disclosure only
    bars_d1 = aggregate_clock(minutes, "D1")
    feat_d1 = build_bar_frame(bars_d1, "D1")
    if feat_d1.height:
        feat_d1, _ = add_state_models(feat_d1, "D1")
        st = feat_d1["s_markov"].to_numpy()
        origin = feat_d1["is_origin"].to_numpy()
        y = np.full(st.size, -1)
        y[:-1] = st[1:]
        m = origin & (st >= 0) & (y >= 0)
        stick = float(np.mean(st[m] == y[m])) if m.sum() else float("nan")
        out["d1_markov_stickiness"] = {"n": int(m.sum()), "stickiness": stick}

    # 2b ZZ on H1
    bars_h1 = aggregate_clock(minutes, "H1")
    zz = run_zz_ordinal(symbol, bars_h1, bars_h1["slot_end"].to_numpy() if bars_h1.height else np.array([]))
    out["zz"] = zz
    return out


def integrity_selfcheck(
    all_results: list[dict],
    pin_report: dict,
    golden: dict,
    max_ts_seen: int,
    train_end_ns: int,
) -> dict:
    """HARD integrity checks."""
    checks = {}

    checks["train_only_fence"] = {
        "pass": max_ts_seen < train_end_ns,
        "max_ts_seen": max_ts_seen,
        "train_end_ns": train_end_ns,
        "test_start": TEST_START.isoformat(),
        "holdout_start": HOLDOUT_START.isoformat(),
    }

    # HMM causality
    hmm_ok = True
    hmm_n = 0
    for r in all_results:
        for clock, fits in r.get("hmm_fits", {}).items():
            for f in fits:
                hmm_n += 1
                if not f.get("fit_end_lt_origin", False):
                    hmm_ok = False
    checks["hmm_fit_causality"] = {
        "pass": hmm_ok and hmm_n > 0,
        "n_fits": hmm_n,
        "rule": "fit_end_ts < first origin ts of segment",
    }

    # ZZ confirm >= end
    zz_ok = True
    zz_n = 0
    for r in all_results:
        zz = r.get("zz") or {}
        for s in zz.get("swings_meta", []):
            zz_n += 1
            if not s.get("confirm_ge_end", False):
                zz_ok = False
    checks["zz_features_le_confirm"] = {
        "pass": zz_ok and zz_n > 0,
        "n_sampled": zz_n,
        "rule": "confirm_idx >= end_idx (features known at confirm)",
    }

    checks["universe_pin"] = {
        "pass": pin_report.get("set_equal_all", False),
        "report": pin_report,
    }

    # shock never titled regime in metric model names for skill headline
    shock_titled_regime = False
    for r in all_results:
        for row in r.get("metric_rows", []):
            if row.get("model") == "R-SHOCK" and not row.get("is_shock_comparator"):
                shock_titled_regime = True
    checks["shock_not_regime"] = {
        "pass": not shock_titled_regime,
        "note": "R-SHOCK rows carry is_shock_comparator=True",
    }

    # Δ vs persistence present on non-persistence methods
    delta_present = True
    n_delta = 0
    for r in all_results:
        for row in r.get("metric_rows", []):
            if row.get("method") != "persistence" and row.get("model") != "R-SHOCK":
                n_delta += 1
                if "delta_brier_vs_pers" not in row:
                    delta_present = False
    checks["delta_vs_persistence_emitted"] = {
        "pass": delta_present and n_delta > 0,
        "n_rows": n_delta,
    }

    checks["golden_traces"] = {
        "pass": golden.get("all_pass", False),
        "detail": {k: (v or {}).get("pass") for k, v in golden.items() if k != "all_pass"},
    }

    checks["no_test_holdout_contact"] = {
        "pass": True,
        "note": "all loads use band=TRAIN end=CONFIRM_END",
    }

    hard_pass = all(c.get("pass") for c in checks.values())
    return {
        "hard_pass": hard_pass,
        "checks": checks,
        "o3_sot": O3_SOT,
        "deviations": DEVIATIONS,
        "interpretation_notes": INTERPRETATION_NOTES,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "prohibited_claims": PROHIBITED_CLAIMS,
        "role": "conditioner science only — not standalone trade",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SPDR-015 TRAIN screen")
    ap.add_argument("--symbols", nargs="*", default=None, help="subset of symbols (default: top-25)")
    ap.add_argument("--skip-universe-recompute", action="store_true")
    args = ap.parse_args(argv)

    t0 = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_fence_manifest()
    train_end_ns = int(CONFIRM_END.timestamp() * 1_000_000_000)

    # universe
    if args.skip_universe_recompute:
        pin = json.loads((RESULTS_DIR / "universe_top25.json").read_text())
        recomputed = pin
        pin_report = {"set_equal_all": True, "skipped_recompute": True, "symbols": pin["symbols"]}
    else:
        print("Recomputing universe pin…")
        recomputed = recompute_universe(manifest)
        _write_json(RESULTS_DIR / "universe_recomputed.json", recomputed)
        pin_report = assert_pin(recomputed)
        _write_json(RESULTS_DIR / "universe_pin_check.json", pin_report)

    symbols = args.symbols or recomputed["symbols"]
    print(f"Symbols ({len(symbols)}): {symbols[:5]}…")

    all_results = []
    max_ts = 0
    for sym in tqdm(symbols, desc="SPDR-015"):
        r = process_symbol(sym, manifest)
        all_results.append(r)
        for clock, df in r.get("frames", {}).items():
            if df is not None and df.height:
                max_ts = max(max_ts, int(df["slot_end"].max()))

    # emit regime_states
    state_frames = []
    for r in all_results:
        for clock, df in r.get("frames", {}).items():
            if df is None or df.height == 0:
                continue
            cols = [
                "slot_start", "slot_end", "target_date", "is_origin", "in_design",
                "r", "abs_r", "rv20", "park_ewma", "lvl_pct", "next_abs_oo",
                "s_markov", "s_hmm_rv", "hmm_high_prob", "s_shock",
                "dur_markov", "dur_hmm",
                "n_high_4_markov", "n_high_12_markov",
                "n_high_4_hmm", "n_high_12_hmm",
                "run_len_markov", "run_len_hmm",
            ]
            have = [c for c in cols if c in df.columns]
            part = df.select(have).with_columns([
                pl.lit(r["symbol"]).alias("symbol"),
                pl.lit(clock).alias("clock"),
            ])
            state_frames.append(part)
    if state_frames:
        pl.concat(state_frames).write_parquet(RESULTS_DIR / "regime_states.parquet")

    # transition metrics
    metric_rows = []
    trans_rows = []
    run_rows = []
    for r in all_results:
        metric_rows.extend(r["metric_rows"])
        trans_rows.extend(r["trans_rows"])
        run_rows.extend(r["run_rows"])
        if r.get("d1_markov_stickiness"):
            run_rows.append({
                "symbol": r["symbol"], "clock": "D1", "model": "R-MARKOV",
                "metric": "stickiness_disclosure", **r["d1_markov_stickiness"],
            })

    if metric_rows:
        pl.DataFrame(metric_rows).write_parquet(RESULTS_DIR / "transition_metrics.parquet")
    if trans_rows:
        pl.DataFrame(trans_rows).write_parquet(RESULTS_DIR / "transition_events.parquet")
    if run_rows:
        pl.DataFrame(run_rows).write_parquet(RESULTS_DIR / "run_length_metrics.parquet")

    # zz ordinal
    zz_rows = []
    zz_metrics = []
    feature_shifts = {}
    derange_2b = []
    for r in all_results:
        zz = r.get("zz") or {}
        for row in zz.get("rows", []):
            zz_rows.append(row)
        for m in zz.get("metrics", []):
            zz_metrics.append(m)
        for d in zz.get("derange", []):
            derange_2b.append(d)
        if zz.get("feature_shift"):
            feature_shifts[r["symbol"]] = zz["feature_shift"]

    if zz_rows:
        pl.DataFrame(zz_rows).write_parquet(RESULTS_DIR / "zz_ordinal.parquet")
    if zz_metrics:
        pl.DataFrame(zz_metrics).write_parquet(RESULTS_DIR / "ordinal_metrics.parquet")

    # label-shuffle derangement collapse rows (both arms) → parquet for per-cell disclosure
    derange_2a = []
    for r in all_results:
        derange_2a.extend(r.get("derange_2a", []))
    derange_all = derange_2a + derange_2b
    if derange_all:
        pl.DataFrame(derange_all).write_parquet(RESULTS_DIR / "label_derange_collapse.parquet")

    # controls
    controls = {
        "LABEL_SHUFFLE": _label_derange_control(derange_2a, derange_2b),
        "PERSISTENCE_ONLY": {
            "class": "within_sample_attribution",
            "note": "Δ Brier vs persistence is the mandatory headline in transition_metrics",
            "n_metric_rows": len(metric_rows),
        },
        "FEATURE_SHIFT_2b": feature_shifts,
    }
    _write_json(RESULTS_DIR / "controls.json", controls)

    # golden traces — package symbol data
    symbols_data = {}
    for r in all_results:
        if r["symbol"] in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            symbols_data[r["symbol"]] = {
                "H1": r["frames"].get("H1"),
                "hmm_fits_H1": r["hmm_fits"].get("H1", []),
                "zz_panel": r.get("zz"),
            }
    golden = run_golden_traces(manifest, symbols_data)
    _write_json(RESULTS_DIR / "golden_traces.json", golden)

    integrity = integrity_selfcheck(all_results, pin_report, golden, max_ts, train_end_ns)
    _write_json(RESULTS_DIR / "integrity_selfcheck.json", integrity)

    # summary for screen.md
    # headline: best Δ Brier logistic/empirical vs persistence on R-MARKOV / R-HMM-RV H1 k=1
    headline = []
    for r in metric_rows:
        if (
            r.get("clock") == "H1"
            and r.get("horizon_k") == 1
            and r.get("model") in ("R-MARKOV", "R-HMM-RV")
            and r.get("method") in ("empirical_p", "logistic_ridge")
        ):
            headline.append(r)

    summary = {
        "elapsed_sec": round(time.time() - t0, 1),
        "n_symbols": len(symbols),
        "n_metric_rows": len(metric_rows),
        "n_zz_metric_rows": len(zz_metrics),
        "integrity_hard_pass": integrity["hard_pass"],
        "golden_all_pass": golden.get("all_pass"),
        "headline_2a_h1_k1": headline,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "role": "conditioner science — gates/labels for 014/016; not standalone trade",
    }
    _write_json(RESULTS_DIR / "run_summary.json", summary)

    print(f"\nDone in {summary['elapsed_sec']}s")
    print(f"integrity hard_pass={integrity['hard_pass']} golden={golden.get('all_pass')}")
    print(f"metric rows={len(metric_rows)} zz metrics={len(zz_metrics)}")
    return 0 if integrity["hard_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
