"""Re-derive the high-consequence claims in checkpoint-018's evidence inventory."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
CRYPTO_PATH = ROOT / "python/experiments/SPDR-018/results/analyst_per_cell_magnitudes.parquet"
CTRADER_PATH = ROOT / "python/experiments/SPDR-018B/results/analyst_per_cell_magnitudes.parquet"


def scalar(value: object) -> int | float:
    if isinstance(value, (np.integer, int)):
        return int(value)
    return float(value)


def baseline(frame: pd.DataFrame) -> dict[str, object]:
    powered = frame.loc[frame["at_parent_target_precision"].fillna(False)].copy()
    mirror = (1.0 - powered["gross_p"]) / powered["gross_p"]
    log_r = np.log(powered["gross_W_L"]) - np.log(mirror)
    identity_residual = (
        powered["gross_p"] * powered["gross_W"]
        - (1.0 - powered["gross_p"]) * powered["gross_L"]
        - powered["gross_mean"]
    )
    mirror_log = np.log(mirror)
    observed_log = np.log(powered["gross_W_L"])
    slope, intercept = np.polyfit(mirror_log, observed_log, 1)
    r_squared = np.corrcoef(mirror_log, observed_log)[0, 1] ** 2
    mirror_covered = (mirror >= powered["gross_W_L_ci_low"]) & (
        mirror <= powered["gross_W_L_ci_high"]
    )
    gross_clear = powered["gross_mean"] > 0.0
    net_clear = powered["net_mean"] > 0.0
    negative_tail = powered["gross_mean_ci_high"] < 0.0
    positive_tail = powered["gross_mean_ci_low"] > 0.0

    return {
        "powered_cells": len(powered),
        "median": {
            column: scalar(powered[column].median())
            for column in (
                "gross_p",
                "gross_p_be",
                "gross_W",
                "gross_L",
                "gross_W_L",
                "gross_p_be_net",
                "gross_edge",
                "gross_mean",
                "net_mean",
                "gross_median",
                "gross_trimmed_mean_10",
                "gross_cost_bps",
            )
        },
        "mean": {
            column: scalar(powered[column].mean())
            for column in (
                "gross_p",
                "gross_p_be",
                "gross_W",
                "gross_L",
                "gross_W_L",
                "gross_p_be_net",
                "gross_edge",
            )
        },
        "gross_clear": int(gross_clear.sum()),
        "net_clear": int(net_clear.sum()),
        "negative_mean_ci_tail": int(negative_tail.sum()),
        "positive_mean_ci_tail": int(positive_tail.sum()),
        "identity_vs_all_leg_mean_max_abs_gap_bps": scalar(identity_residual.abs().max()),
        "mirror": {
            "log_r_median": scalar(log_r.median()),
            "log_r_mean": scalar(log_r.mean()),
            "log_r_sd_population": scalar(log_r.std(ddof=0)),
            "positive_cells": int((log_r > 0.0).sum()),
            "positive_share": scalar((log_r > 0.0).mean()),
            "covered_cells": int(mirror_covered.sum()),
            "covered_share": scalar(mirror_covered.mean()),
            "fitted_slope": scalar(slope),
            "fitted_intercept": scalar(intercept),
            "fitted_r_squared": scalar(r_squared),
            "wl_min": scalar(powered["gross_W_L"].min()),
            "wl_max": scalar(powered["gross_W_L"].max()),
            "p_min": scalar(powered["gross_p"].min()),
            "p_max": scalar(powered["gross_p"].max()),
        },
        "descriptive_wl_min": scalar(frame["gross_W_L"].min()),
        "descriptive_wl_max": scalar(frame["gross_W_L"].max()),
        "powered_exit_counts": {
            str(key): int(value)
            for key, value in powered.loc[powered["arm"] == "B", "exit_mode"]
            .value_counts()
            .sort_index()
            .items()
        },
        "event_type_median_gross_mean_bps": {
            str(key): scalar(value)
            for key, value in powered.loc[powered["arm"] == "C"]
            .groupby("event_type")["gross_mean"]
            .median()
            .sort_index()
            .items()
        },
    }


def main() -> None:
    crypto = pd.read_parquet(CRYPTO_PATH)
    ctrader = pd.read_parquet(CTRADER_PATH)
    result = {"crypto": baseline(crypto), "ctrader": baseline(ctrader)}

    assert result["crypto"]["powered_cells"] == 1_413
    assert result["ctrader"]["powered_cells"] == 315
    assert result["crypto"]["net_clear"] == 0
    assert result["ctrader"]["net_clear"] == 0
    assert result["crypto"]["negative_mean_ci_tail"] == 129
    assert result["crypto"]["positive_mean_ci_tail"] == 1
    assert result["crypto"]["powered_exit_counts"] == {"combined": 478, "signalflip": 401}
    assert result["ctrader"]["event_type_median_gross_mean_bps"]["E-HORIZON"] > result[
        "ctrader"
    ]["event_type_median_gross_mean_bps"]["E-TOUCH"]

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
