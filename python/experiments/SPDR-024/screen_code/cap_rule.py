#!/usr/bin/env python3
"""Apply the design section 7 CAP-RULE to arm B's realised duration distribution.

The cap is read off DURATIONS only. Reading it off outcomes would be selection on the estimand
and would void the run; reading it off the previous experiment's arms would calibrate it
against that experiment's own arbitrary choice (design section 7, why no cap can be read off
the completed runs).

The rule is applied mechanically and its result is reported as it falls out - including
`NOT_APPLICABLE` when no declared grid value satisfies it. It is never relaxed to produce a
number, and the safety-ceiling bind rate is reported whether or not it is comfortable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402

from xen.adaptive_management.contracts import UNCAPPED_ARM_ID  # noqa: E402
from xen.adaptive_management.spdr024 import hold_cap_from_durations  # noqa: E402
from xen.adaptive_management.spdr024_emission import build_episode_table  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path, help="the arm A/B hold-phase run")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    episodes = build_episode_table(args.run)
    arm_b = episodes.filter(pl.col("arm_id") == UNCAPPED_ARM_ID)
    if arm_b.is_empty():
        raise SystemExit(f"{UNCAPPED_ARM_ID} produced no rows in {args.run}")
    closed = arm_b.filter(pl.col("hold_bars_realised").is_not_null())
    durations = closed["hold_bars_realised"].to_numpy().astype(float)

    payload = hold_cap_from_durations(durations)
    payload.update(
        {
            "run_path": str(Path(args.run).resolve()),
            "arm_rows": arm_b.height,
            "filled_positions": int(arm_b["entry_ts"].is_not_null().sum()),
            "closed_positions": int(closed.height),
            "censored_positions": int(arm_b["censored"].sum()),
            "per_symbol_closed": {
                str(row["symbol"]): int(row["n"])
                for row in closed.group_by("symbol").agg(pl.len().alias("n")).iter_rows(
                    named=True
                )
            },
            "duration_basis": "signal-domain bars from engine entry to engine close",
            "outcome_never_consulted": True,
        }
    )
    if payload["status"] == "NOT_APPLICABLE":
        payload["operator_note"] = (
            "No declared grid value binds at or below the declared fraction. The rule is "
            "reported as it fell out; the cap is NOT set, and the comparison arms keep the "
            "declared baseline hold. The decay curve remains descriptive (H3)."
        )
    if payload["safety_ceiling_flagged"]:
        payload["operator_note_ceiling"] = (
            "The safety ceiling binds above its declared 2% tolerance, so it is not acting "
            "purely as a valve. Design section 7 requires this be flagged to the operator "
            "rather than reinterpreted."
        )
    # The decay curve (H3): mean outcome as a function of bars held. Descriptive only; it sets
    # no cap in this run and calibrates the run after this one.
    if closed.height:
        bucket = np.clip(np.floor(durations).astype(int), 0, None)
        curve = (
            closed.with_columns(pl.Series("bars_held", bucket))
            .group_by("bars_held")
            .agg(
                pl.len().alias("n"),
                pl.col("outcome_bps").mean().alias("mean_outcome_bps"),
                pl.col("capital_normalised_return_bps").mean().alias("mean_primary_bps"),
            )
            .sort("bars_held")
        )
        payload["decay_curve"] = curve.to_dicts()
        payload["decay_curve_class"] = "DESCRIPTIVE_SETS_NO_CAP_IN_THIS_RUN"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "decay_curve"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
