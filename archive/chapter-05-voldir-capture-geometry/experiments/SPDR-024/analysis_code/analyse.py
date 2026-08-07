#!/usr/bin/env python3
"""Analyse one completed SPDR-024 cell. Descriptive only - no verdict, no family action.

Order matters here. The paired-difference dependence diagnostic (P-5) runs FIRST, before any
effect is read, because it is a property of the apparatus and reading it after the estimates
would invite choosing a variance treatment that flatters a result - which D12 forbids.

Every headline carries all three variance treatments; the most conservative governs the band.
The per-symbol ladder is always printed beside any pooled figure (OD-9 / OD-10), and the
per-notional bps lens is emitted labelled DIAGNOSTIC and barred from every sizing claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import uuid

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402

from xen.adaptive_management.analysis import analyse_run  # noqa: E402
from xen.adaptive_management.contracts import SIGNAL_DOMAIN_HOURS  # noqa: E402
from xen.adaptive_management.spdr024_analysis import (  # noqa: E402
    BOOTSTRAP_DRAWS,
    STEP3_OBSERVED_EFFECT_SIGMA_MAX,
    STEP3_OBSERVED_EFFECT_SIGMA_MIN,
    TREATMENTS,
    baseline_characterisation,
    pool_filter_ladder,
    scale_channel_estimates,
    selection_channel_estimates,
)
from xen.adaptive_management.spdr024 import REGIME_LABEL_SHARED_WITH_ARM  # noqa: E402
from xen.adaptive_management.spdr024_emission import build_episode_table  # noqa: E402

EXPERIMENT_ID = "SPDR-024"


def paired_difference_dependence(
    episodes: pl.DataFrame,
    *,
    domain_hours: int,
) -> dict:
    """P-5 (i): does the paired arm-difference series carry dependence the baseline lacks?"""
    del domain_hours
    report: dict[str, dict] = {}
    comparator = episodes.filter(pl.col("arm_id") == "FIXED_SIZE_UNIT").select(
        "symbol", "origin_id", "entry_ts",
        pl.col("capital_normalised_return_bps").alias("_base"),
    )
    arms = sorted(
        set(
            episodes.filter(
                (pl.col("device") == "SIZE") & (pl.col("arm_id") != "FIXED_SIZE_UNIT")
            )["arm_id"].to_list()
        )
    )
    baseline = _acf_by_symbol(comparator.rename({"_base": "_value"}))
    for arm_id in arms:
        arm = episodes.filter(pl.col("arm_id") == arm_id).select(
            "symbol", "origin_id",
            pl.col("capital_normalised_return_bps").alias("_arm"),
        )
        paired = (
            comparator.join(arm, on=["symbol", "origin_id"], how="inner")
            .drop_nulls(["_base", "_arm"])
            .with_columns((pl.col("_arm") - pl.col("_base")).alias("_value"))
        )
        report[arm_id] = _acf_by_symbol(paired)
    return {
        "baseline_series": baseline,
        "paired_difference_series": report,
        "reading": (
            "compare max|acf| against each series' own 95% noise band; a difference series "
            "above the band where the baseline sits inside it is dependence the baseline "
            "measurement did not cover"
        ),
    }


def _dependence_premise(dependence: dict) -> dict:
    """Does this run's own P-5 measurement support design section 10's dependence premise?

    Design section 10 argues the Step-3 fixed 24-bar block was inherited rather than derived,
    because no serial dependence is detectable in the baseline trade series. That premise is
    testable on this run's own numbers, and it is stated here rather than left for a reader to
    reconstruct - including when it does NOT hold.
    """
    def _summarise(block: dict) -> dict:
        outside = [
            symbol for symbol, item in block.items() if item.get("outside_band")
        ]
        return {"symbols": len(block), "outside_noise_band": sorted(outside)}

    baseline = _summarise(dependence.get("baseline_series", {}))
    paired = {
        arm: _summarise(block)
        for arm, block in dependence.get("paired_difference_series", {}).items()
    }
    paired_outside = sorted(
        {symbol for item in paired.values() for symbol in item["outside_noise_band"]}
    )
    return {
        "baseline_series": baseline,
        "paired_difference_symbols_outside_band": paired_outside,
        "premise": (
            "design section 10 assumes no detectable serial dependence in the trade series"
        ),
        "verdict": (
            "SUPPORTED_BY_THIS_RUN"
            if not baseline["outside_noise_band"] and not paired_outside
            else "NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS"
        ),
        "consequence_if_not_supported": (
            "V-A's unchunked treatment would overstate resolution; V-B and V-C remain, and the "
            "most conservative still governs every band"
        ),
    }


def _acf_by_symbol(frame: pl.DataFrame) -> dict:
    out: dict[str, dict] = {}
    if frame.is_empty() or "_value" not in frame.columns:
        return out
    for symbol, group in frame.sort(["symbol", "entry_ts"]).group_by("symbol"):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        values = group["_value"].drop_nulls().to_numpy().astype(float)
        if values.size < 30 or float(np.std(values)) == 0.0:
            out[str(name)] = {"n": int(values.size), "max_abs_acf_lag_1_20": None}
            continue
        centred = values - values.mean()
        denominator = float(np.dot(centred, centred))
        acf = [
            float(np.dot(centred[:-lag], centred[lag:]) / denominator)
            for lag in range(1, min(21, values.size))
        ]
        out[str(name)] = {
            "n": int(values.size),
            "max_abs_acf_lag_1_20": float(np.max(np.abs(acf))),
            "noise_band_95": float(1.96 / np.sqrt(values.size)),
            "outside_band": bool(np.max(np.abs(acf)) > 1.96 / np.sqrt(values.size)),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--n-boot", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument(
        "--skip-device-tables",
        action="store_true",
        help="skip the inherited SPDR-021 device/native tables (risk-shape diagnostics)",
    )
    args = parser.parse_args(argv)

    config = json.loads((args.run / "config.json").read_text(encoding="utf-8"))
    if config.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError(f"{EXPERIMENT_ID} wrapper received a different experiment run")
    if config.get("band") != "TRAIN":
        raise ValueError("SPDR-024 analysis accepts TRAIN runs only")
    domain = str(config.get("signal_domain", "H1"))
    domain_hours = SIGNAL_DOMAIN_HOURS[domain]

    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite analysis: {output}")
    workspace = output.parent / f".{output.name}.tmp-{uuid.uuid4().hex}"
    workspace.mkdir(parents=True)
    try:
        episodes = build_episode_table(args.run)
        episodes.write_parquet(workspace / "episodes.parquet")

        # P-5 (i) FIRST: apparatus before effects.
        dependence = paired_difference_dependence(episodes, domain_hours=domain_hours)
        (workspace / "paired_difference_dependence.json").write_text(
            json.dumps(dependence, indent=2, sort_keys=True, default=str) + "\n"
        )

        # OD-3 / design section 6A: the baseline characterised alone, and FIRST. It is the
        # level every later comparison is read against, so it is emitted before them.
        baseline = baseline_characterisation(episodes)
        baseline.write_parquet(workspace / "baseline_characterisation.parquet")

        scale = scale_channel_estimates(
            episodes, domain_hours=domain_hours, n_boot=args.n_boot
        )
        selection = selection_channel_estimates(
            episodes, domain_hours=domain_hours
        )
        # OD-9 step (iii) is not channel-specific: the concentration ladder covers both.
        ladder = pl.concat(
            [pool_filter_ladder(scale), pool_filter_ladder(selection, value_column="contrast_bps")],
            how="diagonal_relaxed",
        )
        for name, table in (
            ("scale_channel_estimates", scale),
            ("selection_channel_estimates", selection),
            ("pool_filter_ladder", ladder),
        ):
            table.write_parquet(workspace / f"{name}.parquet")

        closed = episodes.filter(pl.col("exit_ts").is_not_null())
        summary = {
            "experiment_id": EXPERIMENT_ID,
            "universe": config.get("universe"),
            "signal_domain": domain,
            "band": "TRAIN",
            "interpretation": "DESCRIPTIVE_ONLY_NO_VERDICT",
            "hold_cap_bars": config.get("hold_cap_bars"),
            "future_shift_bars": config.get("future_shift_bars"),
            "primary_estimand": "capital_normalised_episode_return (E6)",
            "diagnostic_estimand": "outcome_bps (per-notional; BARRED from sizing claims)",
            "variance_treatments": list(TREATMENTS),
            "governing_rule": (
                "most conservative treatment by fewest blocks / highest coherent R2 floor"
            ),
            "labels": {
                "result_labels_emitted": "NONE",
                "rule": (
                    "every row is described by estimate, uncertainty, population count, "
                    "effective count and optional R2 MDE, and by nothing else"
                ),
                "authority": (
                    "adaptive-management-design.md section 1 ('power labels do not decide "
                    "which rows are shown or how they are described') and section 9 ('Emit "
                    "event count, effective count, CI and MDE for every row. These are "
                    "informative diagnostics, not verdict labels or pruning rules'); "
                    "SPDR-024 AMENDMENT-7 R1–R5"
                ),
            },
            "floor_contract": {
                "row_floor": "mde = MDE_Z * bootstrap_SE of the same estimator as the CI",
                "forbidden_row_floor": "MDE_Z / sqrt(effective_blocks)",
                "mde_z_role": "sample-size planning only; not a pass mark on realised |estimate|",
                "scale_sigma_denominator": "paired_delta",
                "selection_sigma_denominator": "outcome_level_bps",
            },
            "reference_effect_range_sigma": {
                "step3_observed_sizing_effects_historical_only": [
                    STEP3_OBSERVED_EFFECT_SIGMA_MIN,
                    STEP3_OBSERVED_EFFECT_SIGMA_MAX,
                ],
                "use": (
                    "HISTORICAL CONTEXT ONLY under AMENDMENT-7 R1. Never a gate, resolve "
                    "ladder, preflight yardstick, or column-derived classification"
                ),
            },
            "dependence_premise_check": _dependence_premise(dependence),
            "od14_coverage": {
                "continuous_and_discrete_head_to_head": ["RANGE_SCALE", "SWING_SCALE"],
                "discrete_only": [
                    "LEVEL_NOW", "LEVEL_FORECAST_K4", "LEVEL_FORECAST_K12",
                    "SHOCK", "SWING_GT_CUR", "TAIL_RISK",
                ],
                "reason": (
                    "the continuous rule needs a numeric scale and its calibration median; the "
                    "design declares no continuous schedule for a categorical state component, "
                    "and inventing one would be a new mechanism"
                ),
            },
            "regime_label_shared_with_arm": REGIME_LABEL_SHARED_WITH_ARM,
            "estimand_validation_physicality_scope": {
                "scope": "WHOLE_38_ARM_LATTICE_NOT_THE_STRATEGY",
                "warning": (
                    "occupancy, annualised return and Sharpe in estimand_validation.json are "
                    "computed over every arm's positions together. They are an apparatus "
                    "figure and must never be quoted as the baseline strategy's own"
                ),
                "baseline_occupancy_is_reported_separately_in": "analysis.md baseline section",
            },
            "rows": {
                "episodes": episodes.height,
                "closed_episodes": closed.height,
                "censored_episodes": int(episodes["censored"].sum()),
                "distinct_origins": int(episodes["origin_id"].n_unique()),
                "distinct_baseline_trades": int(
                    episodes.filter(
                        (pl.col("arm_id") == "FIXED_SIZE_UNIT")
                        & pl.col("exit_ts").is_not_null()
                    ).height
                ),
                "arms": int(episodes["arm_id"].n_unique()),
            },
            "row_vs_trade_note": (
                "one row per arm per origin; a sample-size statement uses distinct trades, "
                "never row counts"
            ),
            "spread_cost_disclosure": config.get("spread_cost_disclosure"),
            "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
            "artifacts": [
                "episodes.parquet",
                "paired_difference_dependence.json",
                "baseline_characterisation.parquet",
                "scale_channel_estimates.parquet",
                "selection_channel_estimates.parquet",
                "pool_filter_ladder.parquet",
            ],
        }
        (workspace / "analysis_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n"
        )

        if not args.skip_device_tables:
            # The inherited SPDR-021/022/023 analyser supplies the risk-shape diagnostics
            # (drawdown, dispersion, tail loss, concentration). Retained, not rewritten (OD-6).
            analyse_run(args.run, workspace / "inherited", jobs=args.jobs)
        workspace.replace(output)
    except BaseException:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
