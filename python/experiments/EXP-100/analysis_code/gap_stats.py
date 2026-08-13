"""Value-gap stats across all 264 cells — analyst-owned, raw TPO profiles only.

Reports gap presence, width (ATR and as fraction of VA width), tightness,
and selected-bin counts for DEFINED profiles. No experiment-local imports.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

REPO = Path(__file__).resolve().parents[4]
EMISSION_ROOT = REPO / "data/nautilus_runs/EXP-100/full"
OUT_DIR = REPO / "python/experiments/EXP-100/results/analysis"

COLS = [
    "profile_status",
    "undefined_reason",
    "gap_span",
    "gap_span_atr",
    "gap_span_va",
    "va_width",
    "va_mass",
    "tight_gap",
    "gap_mask",
]


def _parse_cell(name: str) -> dict[str, str]:
    parts = name.split("-")
    return {
        "cell_id": name,
        "symbol": parts[1].upper(),
        "timeframe": parts[2],
        "method": parts[3],
        "confirm_ref": parts[4],
        "level_config": "_".join(parts[5:]).upper(),
    }


def _q(series: pl.Series, qs: list[float]) -> dict[str, float]:
    out = {}
    vals = series.quantile(qs)
    for q, v in zip(qs, vals, strict=True):
        out[f"p{int(q*100)}"] = float(v)
    return out


def main() -> None:
    frames = []
    cells = []
    for cell_dir in sorted(p for p in EMISSION_ROOT.iterdir() if p.is_dir()):
        ident = _parse_cell(cell_dir.name)
        df = pl.read_parquet(cell_dir / "tpo_profiles.parquet", columns=COLS)
        defined = df.filter(pl.col("profile_status") == "DEFINED")
        undefined = df.filter(pl.col("profile_status") == "UNDEFINED")
        sel = (
            defined["gap_mask"]
            .str.extract(r'"selected_count":(\d+)')
            .cast(pl.Int64)
        )
        frames.append(
            defined.with_columns(sel.alias("selected_bins")).with_columns(
                pl.lit(ident["level_config"]).alias("level_config"),
                pl.lit(ident["symbol"]).alias("symbol"),
                pl.lit(ident["timeframe"]).alias("timeframe"),
            )
        )
        cells.append(
            {
                **ident,
                "n_defined": defined.height,
                "n_undefined": undefined.height,
                "n_gap_undefined": int(
                    undefined.filter(pl.col("undefined_reason") == "GAP_UNDEFINED").height
                ),
                "n_tight": int(defined["tight_gap"].sum()),
                "tight_frac": (
                    float(defined["tight_gap"].mean()) if defined.height else None
                ),
            }
        )

    allf = pl.concat(frames)
    n = allf.height
    tight = allf["tight_gap"]

    by_config = (
        allf.group_by("level_config")
        .agg(
            [
                pl.len().alias("n_defined"),
                pl.col("tight_gap").sum().alias("n_tight"),
                (pl.col("tight_gap").mean()).alias("tight_frac"),
                pl.col("gap_span_atr").median().alias("median_gap_atr"),
                pl.col("gap_span_va").median().alias("median_gap_va"),
                pl.col("gap_span_va").quantile(0.25).alias("q25_gap_va"),
                pl.col("gap_span_va").quantile(0.75).alias("q75_gap_va"),
                pl.col("selected_bins").median().alias("median_selected_bins"),
                pl.col("selected_bins").max().alias("max_selected_bins"),
            ]
        )
        .sort("level_config")
    )

    by_symbol = (
        allf.group_by("symbol")
        .agg(
            [
                pl.len().alias("n_defined"),
                (pl.col("tight_gap").mean()).alias("tight_frac"),
                pl.col("gap_span_atr").median().alias("median_gap_atr"),
                pl.col("gap_span_va").median().alias("median_gap_va"),
                pl.col("selected_bins").median().alias("median_selected_bins"),
            ]
        )
        .sort("symbol")
    )

    by_tf = (
        allf.group_by("timeframe")
        .agg(
            [
                pl.len().alias("n_defined"),
                (pl.col("tight_gap").mean()).alias("tight_frac"),
                pl.col("gap_span_atr").median().alias("median_gap_atr"),
                pl.col("gap_span_va").median().alias("median_gap_va"),
            ]
        )
        .sort("timeframe")
    )

    summary = {
        "n_cells": len(cells),
        "n_defined_total": int(allf.height),
        "n_undefined_total": int(sum(c["n_undefined"] for c in cells)),
        "n_gap_undefined_total": int(sum(c["n_gap_undefined"] for c in cells)),
        "n_tight_total": int(tight.sum()),
        "tight_frac": float(tight.mean()),
        "tight_frac_cell_range": [
            min(c["tight_frac"] for c in cells),
            max(c["tight_frac"] for c in cells),
        ],
        "gap_span_atr_quantiles": _q(
            allf["gap_span_atr"], [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
        ),
        "gap_span_va_quantiles": _q(
            allf["gap_span_va"], [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
        ),
        "va_width_atr_quantiles": _q(
            (allf["gap_span_atr"] / allf["gap_span_va"]).clip(
                lower_bound=0
            ),
            [0.25, 0.50, 0.75],
        ),
        "va_mass_quantiles": _q(allf["va_mass"], [0.01, 0.25, 0.50, 0.75, 0.99]),
        "selected_bins_quantiles": _q(
            allf["selected_bins"], [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
        ),
        "selected_bins_min": int(allf["selected_bins"].min()),
        "selected_bins_max": int(allf["selected_bins"].max()),
        "gap_span_va_ge_1_frac": float((allf["gap_span_va"] >= 1.0 - 1e-12).mean()),
        "gap_span_va_lt_0_5_frac": float((allf["gap_span_va"] < 0.5).mean()),
    }

    (OUT_DIR / "gap_stats.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    by_config.write_csv(OUT_DIR / "gap_stats_by_config.csv")
    by_symbol.write_csv(OUT_DIR / "gap_stats_by_symbol.csv")
    by_tf.write_csv(OUT_DIR / "gap_stats_by_tf.csv")
    pl.DataFrame(cells).write_csv(OUT_DIR / "gap_stats_by_cell.csv")

    print(json.dumps(summary, indent=2))
    print("\n=== by_config ===")
    print(by_config)
    print("\n=== by_symbol ===")
    print(by_symbol)
    print("\n=== by_tf ===")
    print(by_tf)


if __name__ == "__main__":
    main()
