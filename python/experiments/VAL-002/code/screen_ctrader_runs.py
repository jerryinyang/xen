"""VAL-002 behavioral closure: screen real cTrader StrategyHost runs (design.md v2, A6).

This is the *binding* v2 closure (analysis-plan §B), distinct from ``run_experiment.py``'s
console smoke. The cTrader cAlgo emitted ``positions.parquet`` (with the real OHLC it
executed on) for all 12 cells (4 instruments x 3 domains). Each run is routed through the
**unchanged** frozen referee suite via ``xen.signals.screen_emitted_run``:

- returns are built from the **emitted** ``RealClose`` (fence #4 — self-consistent on
  cTrader's own feed, not re-aggregated from a local Parquet);
- the EXP-004 within-analysis split is reproduced by passing the per-instrument
  ``train_end_ts`` (from the first-70% analysis slice) as ``train_end_utc``;
- seeding is the EXP-004 seeding (``seed_for("EXP-004", instrument, domain, "ma_20_50")``),
  applied by ``screen_emitted_run`` itself.

Each verdict is then classified against the EXP-003 MDE map with the *same* helpers
``run_experiment.py`` uses for the console smoke (``consistency_status``,
``classify_location``), so the real-engine table is directly comparable to
``results/suite_reproduction.csv``. The holdout fence is re-asserted per run.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import polars as pl
from tqdm.auto import tqdm

# Reuse the console-smoke classification logic verbatim so the two tables are comparable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_experiment import (  # noqa: E402
    ALPHA0,
    BOOTSTRAP_RESAMPLES,
    classify_location,
    consistency_status,
    load_mde_map,
)

from xen.referee_calibration import list_timebar_files, load_analysis_data, write_json
from xen.signals import assert_run_within_holdout, load_emitted_run, screen_emitted_run

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
STRATEGY_RUNS_DIR = DATA_DIR / "strategy_runs"
RESULTS_DIR = PROJECT_ROOT / "python" / "experiments" / "VAL-002" / "results"
SUITE_CSV = RESULTS_DIR / "suite_reproduction_ctrader.csv"
CLOSURE_META = RESULTS_DIR / "ctrader_closure_metadata.json"

INSTRUMENT_ORDER = {"BTCUSD": 0, "EURUSD": 1, "USTEC": 2, "XAUUSD": 3}
DOMAIN_ORDER = {"5m": 0, "1h": 1, "4h": 2}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def build_train_end_map() -> dict[str, Any]:
    """Per-instrument EXP-004 split boundary from the first-70% analysis slice.

    Loads only the analysis slice (``load_analysis_data`` never reads the holdout),
    so this re-derives the exact ``train_end_ts`` the calibration used.
    """
    train_end: dict[str, Any] = {}
    for path in list_timebar_files(DATA_DIR):
        data = load_analysis_data(path)
        train_end[data.instrument.upper()] = data.train_end_ts
    return train_end


def screen_one_run(run_dir: Path, train_end_ts: Any, mde_map: dict) -> list[dict[str, Any]]:
    """Screen a single emitted run dir and classify its verdicts vs the MDE map."""
    run = load_emitted_run(run_dir)
    instrument = str(run.metadata.get("symbol", "")).upper()
    domain = str(run.positions.get_column("Domain")[0])

    # Re-assert the holdout fence on the emitted data (fail-closed).
    analysis_end_utc = run.metadata.get("analysis_end_utc")
    if analysis_end_utc is not None:
        assert_run_within_holdout(run.positions, analysis_end_utc)

    verdicts = screen_emitted_run(
        run,
        train_end_utc=train_end_ts,
        seed_tag="EXP-004",
        alpha_values=(ALPHA0,),
        n_bootstrap=BOOTSTRAP_RESAMPLES,
    )

    rows: list[dict[str, Any]] = []
    for verdict in verdicts:
        referee = str(verdict["referee"])
        mde = mde_map.get((domain, referee), {})
        mde_bps = float(mde.get("mde_bps", math.nan))
        uncertainty_bps = float(mde.get("mde_grid_uncertainty_bps", math.nan))
        status, reason = consistency_status(
            verdict=str(verdict["verdict"]),
            effect_bps=float(verdict["effect_bps"]),
            ci_lower_bps=float(verdict["ci_lower_bps"]),
            mde_bps=mde_bps,
            uncertainty_bps=uncertainty_bps,
        )
        location = classify_location(
            float(verdict["effect_bps"]),
            float(verdict["ci_upper_bps"]),
            mde_bps,
            uncertainty_bps,
        )
        is_gate_stack = referee == "gate_stack"
        suite_pass = (
            verdict["verdict"] == "REJECT"
            and status == "PASS"
            and reason == "matched_reject"
            and (not is_gate_stack or location == "below_MDE")
        )
        rows.append(
            {
                "instrument": instrument,
                "domain": domain,
                "strategy": "ma_20_50",
                "referee": referee,
                "alpha": verdict["alpha"],
                "verdict": verdict["verdict"],
                "effect_bps": verdict["effect_bps"],
                "ci_lower_bps": verdict["ci_lower_bps"],
                "ci_upper_bps": verdict["ci_upper_bps"],
                "effective_n": verdict["effective_n"],
                "block_length": verdict["block_length"],
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": uncertainty_bps,
                "exp004_consistency_status": status,
                "exp009_location_vs_mde": location,
                "suite_reproduction_status": "PASS" if suite_pass else "FAIL",
                "n_positions": run.positions.height,
                "max_source_close_time": str(run.positions.get_column("SourceCloseTime").max()),
                "analysis_end_utc": str(analysis_end_utc),
                "run_dir": run_dir.name,
            }
        )
    return rows


def sort_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return (
        INSTRUMENT_ORDER.get(row["instrument"], 99),
        DOMAIN_ORDER.get(row["domain"], 99),
        0 if row["referee"] == "minimal_baseline" else 1,
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    run_dirs = sorted(p for p in STRATEGY_RUNS_DIR.iterdir() if (p / "positions.parquet").exists())
    if not run_dirs:
        raise FileNotFoundError(f"No emitted runs under {STRATEGY_RUNS_DIR}")

    train_end_map = build_train_end_map()
    mde_map = load_mde_map()

    all_rows: list[dict[str, Any]] = []
    for run_dir in tqdm(run_dirs, desc="VAL-002 cTrader closure"):
        run_meta = load_emitted_run(run_dir)
        instrument = str(run_meta.metadata.get("symbol", "")).upper()
        train_end_ts = train_end_map.get(instrument)
        if train_end_ts is None:
            raise KeyError(f"No analysis-slice train_end for {instrument} (run {run_dir.name})")
        all_rows.extend(screen_one_run(run_dir, train_end_ts, mde_map))

    all_rows.sort(key=sort_key)
    pl.DataFrame(all_rows).write_csv(SUITE_CSV)

    cells = {(r["instrument"], r["domain"]) for r in all_rows}
    gate_rows = [r for r in all_rows if r["referee"] == "gate_stack"]
    failures = [r for r in all_rows if r["suite_reproduction_status"] != "PASS"]
    fence_ok = all(r["max_source_close_time"] < r["analysis_end_utc"] for r in all_rows)
    overall = "PASS" if not failures and len(cells) == 12 and fence_ok else "FAIL"

    write_json(
        CLOSURE_META,
        {
            "validation_id": "VAL-002",
            "closure_type": "behavioral_ctrader_engine",
            "source": "data/strategy_runs (real cTrader StrategyHost runs)",
            "alpha0": ALPHA0,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "seed_tag": "EXP-004",
            "cells_screened": len(cells),
            "suite_rows": len(all_rows),
            "suite_failures": len(failures),
            "gate_stack_all_reject_below_mde": all(
                r["verdict"] == "REJECT" and r["exp009_location_vs_mde"] == "below_MDE"
                for r in gate_rows
            ),
            "holdout_fence_ok": fence_ok,
            "overall_status": overall,
            "run_dirs": [r.name for r in run_dirs],
        },
    )

    print(f"\ncTrader behavioral closure: {overall}")
    print(f"  cells: {len(cells)}/12 | rows: {len(all_rows)} | failures: {len(failures)} | fence_ok: {fence_ok}")
    print(f"  wrote {SUITE_CSV.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {CLOSURE_META.relative_to(PROJECT_ROOT)}")
    if overall != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
