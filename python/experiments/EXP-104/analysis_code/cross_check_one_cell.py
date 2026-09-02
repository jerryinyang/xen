"""One-cell raw cross-check for EXP-104. Does not import analysis.py. No bootstrap."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[4]
CELL = ROOT / "data/nautilus_runs/EXP-100/full/ctrader-eurusd-15m-breakout_bar-1h-previous_1d"
LIVE = ROOT / "python/experiments/EXP-104/results/analysis_results.json"
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000
OUT = Path(__file__).with_name("cross_check_one_cell.json")


def main() -> None:
    live = json.loads(LIVE.read_text())
    raids = pl.read_parquet(CELL / "raids.parquet")
    raids = raids.filter(
        pl.col("endpoint_ts_ns").is_null() | (pl.col("endpoint_ts_ns") <= TRAIN_END_NS)
    )
    later = raids.filter(
        (pl.col("status") == "COMPLETED")
        & pl.col("primary_attribution").fill_null(False)
        & pl.col("primary_completed").fill_null(False)
    )
    marks = pl.read_parquet(CELL / "bar_marks.parquet", columns=["ts_event_ns", "regime"]).sort(
        "ts_event_ns"
    )
    marks = marks.with_columns(
        pl.col("regime").shift(1).alias("causal_regime"),
        pl.col("ts_event_ns").shift(1).alias("src"),
    )
    joined = raids.join(
        marks.select("ts_event_ns", "causal_regime", "src"),
        left_on="sweep_ts_ns",
        right_on="ts_event_ns",
        how="left",
    )
    duration_mismatch = raids.filter(
        pl.col("swing_duration_ns").is_not_null()
        & pl.col("duration_ns").is_not_null()
        & (pl.col("swing_duration_ns") != pl.col("duration_ns"))
    ).height
    provenance = {
        "n_raids": raids.height,
        "n_later": later.height,
        "duration_mismatch": duration_mismatch,
        "regime_mismatch": joined.filter(
            pl.col("raid_regime").is_not_null()
            & pl.col("causal_regime").is_not_null()
            & (pl.col("raid_regime") != pl.col("causal_regime"))
        ).height,
        "missing_preceding": joined.filter(pl.col("src").is_null()).height,
        "unique_raid_id": raids.select("raid_id").n_unique(),
        "later_by_side_regime": later.group_by(["side", "raid_regime"]).agg(pl.len().alias("n")).to_dicts(),
    }
    checks = []
    for channel, column, atr_excl in (
        ("swing_atr", "swing_atr", True),
        ("swing_duration_ns", "swing_duration_ns", False),
        ("strong_move", "strong_move", True),
        ("swing_price", "swing_price", False),
        ("swing_bps", "swing_bps", False),
    ):
        frame = later
        if atr_excl:
            frame = frame.filter(
                pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED"
            )
        frame = frame.with_columns(pl.col(column).cast(pl.Float64).alias("v")).filter(
            pl.col("v").is_not_null() & pl.col("v").is_finite()
        )
        grouped = frame.group_by(["side", "raid_regime"]).agg(
            pl.len().alias("n"), pl.col("v").mean().alias("mean")
        )
        lookup = {(r["side"], r["raid_regime"]): r for r in grouped.to_dicts()}
        for rec in live["value_rows"]:
            st = rec["stratum"]
            if not (
                st.get("archive_symbol") == "EURUSD"
                and st.get("timeframe") == "15m"
                and st.get("confirmation_method") == "BREAKOUT_BAR"
                and st.get("confirmation_reference") == "1H"
                and st.get("config") == "PREVIOUS_1D"
                and rec["channel"] == channel
            ):
                continue
            arm = rec["arm"]
            side = st["side"]
            obs = rec["observed"]
            arm_row = lookup.get((side, arm))
            mid_row = lookup.get((side, "MID"))
            raw_est = None if arm_row is None or mid_row is None else arm_row["mean"] - mid_row["mean"]
            checks.append(
                {
                    "channel": channel,
                    "side": side,
                    "arm": arm,
                    "raw_n": None if arm_row is None else int(arm_row["n"]),
                    "raw_mid_n": None if mid_row is None else int(mid_row["n"]),
                    "live_n": obs.get("arm_n"),
                    "live_mid_n": obs.get("comparator_n"),
                    "raw_estimate": raw_est,
                    "live_estimate": obs.get("estimate"),
                    "n_match": arm_row is not None
                    and mid_row is not None
                    and int(arm_row["n"]) == obs.get("arm_n")
                    and int(mid_row["n"]) == obs.get("comparator_n"),
                    "estimate_match": raw_est is not None
                    and obs.get("estimate") == obs.get("estimate")
                    and abs(raw_est - float(obs.get("estimate"))) < 1e-8,
                }
            )
    eligible = marks.filter(pl.col("causal_regime").is_not_null())
    exposure = {
        str(r): int(n)
        for r, n in eligible.group_by("causal_regime").agg(pl.len().alias("n")).iter_rows()
    }
    all_starts = {
        (r["side"], r["raid_regime"]): int(r["starts"])
        for r in joined.group_by(["side", "raid_regime"])
        .agg(pl.col("raid_id").n_unique().alias("starts"))
        .to_dicts()
    }
    freq = []
    for rec in live["extra"]["frequency_census"][0]["census"]:
        if not (
            rec.get("archive_symbol") == "EURUSD"
            and rec.get("timeframe") == "15m"
            and rec.get("confirmation_method") == "BREAKOUT_BAR"
            and rec.get("confirmation_reference") == "1H"
            and rec.get("config") == "PREVIOUS_1D"
        ):
            continue
        regime = rec["causal_regime"]
        side = rec["side"]
        exp = exposure.get(regime, 0)
        starts_all = all_starts.get((side, regime), 0)
        rate_all = None if exp == 0 else 1000.0 * starts_all / exp
        pooled = sum(all_starts.get((s, regime), 0) for s in ("LOW", "HIGH"))
        rate_pooled = None if exp == 0 else 1000.0 * pooled / exp
        freq.append(
            {
                "side": side,
                "regime": regime,
                "raw_exposure": exp,
                "live_exposure": rec["exposure"],
                "raw_starts_all_raids": starts_all,
                "live_starts": rec["starts"],
                "raw_rate_all_raids_per_side": rate_all,
                "raw_rate_pooled_sides": rate_pooled,
                "live_rate": rec["rate_per_1000"],
                "exposure_match": exp == rec["exposure"],
                "starts_match_all_raids": starts_all == rec["starts"],
                "rate_match_pooled": rate_pooled is not None
                and abs(rate_pooled - float(rec["rate_per_1000"])) < 1e-8,
            }
        )
    payload = {
        "cell": CELL.name,
        "provenance": provenance,
        "outcome_checks": checks,
        "outcome_n_ok": sum(1 for c in checks if c["n_match"] and c["estimate_match"]),
        "outcome_n_checks": len(checks),
        "frequency": freq,
        "exposure": exposure,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(OUT), "outcome_ok": payload["outcome_n_ok"], "n": payload["outcome_n_checks"]}, indent=2))


if __name__ == "__main__":
    main()
