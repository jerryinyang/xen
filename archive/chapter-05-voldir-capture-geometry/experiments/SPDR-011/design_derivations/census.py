"""Outcome-isolated event census for SPDR-011.

This stage locates completed four-hour range breaks and emits only causal state,
event timestamps, directions, ranks, and counts. It never computes execution
prices, forward paths, returns, excursions, costs, or P&L.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python/src"))

from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest  # noqa: E402


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT")
BAR_TYPE = "{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"
DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)
DESIGN_ELIGIBLE_START = datetime(2022, 9, 14, tzinfo=timezone.utc)
MIN_DAILY_RETURNS = 60
RV_WINDOW = 20
BETA_WINDOW = 60
PERCENTILE_LOOKBACK = 252
OUT = Path(__file__).resolve().parents[1] / "results"

ALLOWED_EVENT_COLUMNS = {
    "event_id",
    "symbol",
    "band",
    "trigger_ts",
    "entry_ts",
    "exit_ts",
    "trade_day",
    "utc_slot",
    "utc_week",
    "calendar_third",
    "direction",
    "rv20",
    "vol_pct",
    "vol_tercile",
    "drift20",
    "beta60",
    "cross_rank",
    "cross_eligible",
    "top2",
    "state_source_day",
    "state_known_ts",
    "range_source_day",
    "range_known_ts",
}
FORBIDDEN_COLUMN_TOKENS = (
    "price",
    "return",
    "gross",
    "net",
    "pnl",
    "mfe",
    "mae",
    "excursion",
    "path",
    "realopen",
    "realhigh",
    "reallow",
    "realclose",
)


def midrank_percentile(value: float, history: Sequence[float]) -> float:
    """Empirical midrank of ``value`` against prior observations only."""
    if not history:
        raise ValueError("percentile history is empty")
    arr = np.asarray(history, dtype=float)
    return float((np.count_nonzero(arr < value) + 0.5 * np.count_nonzero(arr == value)) / len(arr))


def vol_tercile(percentile: float) -> str:
    if percentile >= 2.0 / 3.0:
        return "HIGH"
    if percentile >= 1.0 / 3.0:
        return "MID"
    return "LOW"


def one_sample_mde_bps(n_effective_dates: int, sigma_bps: float) -> float:
    """Approximate two-sided 5% / 80%-power MDE using independent UTC dates."""
    if n_effective_dates <= 0:
        return math.inf
    return 2.8 * float(sigma_bps) / math.sqrt(n_effective_dates)


def two_sample_mde_bps(n_a_dates: int, n_b_dates: int, sigma_bps: float) -> float:
    if n_a_dates <= 0 or n_b_dates <= 0:
        return math.inf
    return 2.8 * float(sigma_bps) * math.sqrt(1.0 / n_a_dates + 1.0 / n_b_dates)


def assert_outcome_isolated(events: pl.DataFrame) -> None:
    extra = set(events.columns) - ALLOWED_EVENT_COLUMNS
    forbidden = sorted(
        column
        for column in events.columns
        if any(token in column.lower() for token in FORBIDDEN_COLUMN_TOKENS)
    )
    if extra or forbidden:
        raise ValueError(
            "outcome-isolation violation: "
            f"unexpected={sorted(extra)} forbidden={forbidden}"
        )


def state_records_frame(records: list[dict]) -> pl.DataFrame:
    """Materialise state records after inspecting nullable ranks across all rows."""
    return pl.DataFrame(records, infer_schema_length=None)


def locate_breakouts(bars_4h: pl.DataFrame, states: pl.DataFrame) -> pl.DataFrame:
    """Locate causal breakouts; emitted prices are deliberately discarded."""
    joined = (
        bars_4h.filter(pl.col("boundary_complete"))
        .with_columns(pl.col("slot_start").dt.date().alias("trade_day"))
        .join(states, on=["symbol", "trade_day"], how="inner")
        .filter(
            (pl.col("close") > pl.col("prior_day_high"))
            | (pl.col("close") < pl.col("prior_day_low"))
        )
        .with_columns(
            pl.when(pl.col("close") > pl.col("prior_day_high"))
            .then(1)
            .otherwise(-1)
            .cast(pl.Int8)
            .alias("direction"),
            pl.col("slot_end").alias("trigger_ts"),
            pl.col("slot_end").alias("entry_ts"),
            (pl.col("slot_end") + pl.duration(hours=4)).alias("exit_ts"),
            pl.col("slot_start").dt.hour().alias("utc_slot"),
        )
        .sort(["symbol", "trigger_ts"])
    )
    return joined


def _bars_to_frame(bars: Iterable[object], symbol: str) -> pl.DataFrame:
    rows = [
        {
            "symbol": symbol,
            "ts_event": datetime.fromtimestamp(bar.ts_event / 1_000_000_000, tz=timezone.utc),
            "open": bar.open.as_double(),
            "high": bar.high.as_double(),
            "low": bar.low.as_double(),
            "close": bar.close.as_double(),
        }
        for bar in bars
    ]
    if not rows:
        return pl.DataFrame(
            schema={
                "symbol": pl.String,
                "ts_event": pl.Datetime("ns", "UTC"),
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
            }
        )
    return pl.DataFrame(rows).with_columns(pl.col("ts_event").cast(pl.Datetime("ns", "UTC")))


def aggregate_inputs(
    minutes: pl.DataFrame, *, coverage_attested: bool = False
) -> tuple[pl.DataFrame, pl.DataFrame]:
    marked = minutes.sort("ts_event").with_columns(
        (pl.col("ts_event") - pl.duration(minutes=1)).alias("open_ts")
    ).with_columns(
        pl.col("open_ts").dt.date().alias("day"),
        pl.col("open_ts").dt.truncate("4h").alias("slot_start"),
    )
    daily = (
        marked.group_by(["symbol", "day"])
        .agg(
            pl.col("ts_event").max().alias("last_close_ts"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").sort_by("ts_event").last().alias("close"),
            pl.len().alias("n_print_minutes"),
        )
        .with_columns(
            (
                pl.lit(True)
                if coverage_attested
                else (
                    pl.col("last_close_ts")
                    == pl.col("day").cast(pl.Datetime("ns")).dt.replace_time_zone("UTC")
                    + pl.duration(days=1)
                )
            ).alias("boundary_complete")
        )
        .sort("day")
    )
    bars_4h = (
        marked.group_by(["symbol", "slot_start"])
        .agg(
            pl.col("ts_event").max().alias("last_close_ts"),
            pl.col("close").sort_by("ts_event").last().alias("close"),
            pl.len().alias("n_print_minutes"),
        )
        .with_columns((pl.col("slot_start") + pl.duration(hours=4)).alias("slot_end"))
        .with_columns(
            (
                pl.lit(True)
                if coverage_attested
                else (pl.col("last_close_ts") == pl.col("slot_end"))
            ).alias("boundary_complete")
        )
        .sort("slot_start")
    )
    return daily, bars_4h


def _daily_maps(daily_by_symbol: dict[str, pl.DataFrame]) -> tuple[dict, dict]:
    metadata: dict[str, dict[date, dict]] = {}
    returns: dict[str, dict[date, float]] = {}
    for symbol, frame in daily_by_symbol.items():
        rows = {row["day"]: row for row in frame.iter_rows(named=True) if row["boundary_complete"]}
        metadata[symbol] = rows
        ret: dict[date, float] = {}
        for day in sorted(rows):
            previous = day - timedelta(days=1)
            if previous in rows:
                ret[day] = math.log(float(rows[day]["close"]) / float(rows[previous]["close"]))
        returns[symbol] = ret
    return metadata, returns


def build_states(daily_by_symbol: dict[str, pl.DataFrame]) -> pl.DataFrame:
    metadata, returns = _daily_maps(daily_by_symbol)
    records: list[dict] = []
    btc_returns = returns["BTCUSDT"]
    for symbol in SYMBOLS:
        rv_by_day: dict[date, float] = {}
        return_days = sorted(returns[symbol])
        for day in return_days:
            window_days = [day - timedelta(days=offset) for offset in range(RV_WINDOW - 1, -1, -1)]
            if all(d in returns[symbol] for d in window_days):
                values = [returns[symbol][d] for d in window_days]
                rv_by_day[day] = math.sqrt(float(np.mean(np.square(values))))

        for source_day in return_days:
            sixty = [
                source_day - timedelta(days=offset)
                for offset in range(MIN_DAILY_RETURNS - 1, -1, -1)
            ]
            if not all(d in returns[symbol] and d in btc_returns for d in sixty):
                continue
            if source_day not in rv_by_day:
                continue
            prior_rv = [
                rv_by_day[d]
                for d in sorted(rv_by_day)
                if d < source_day
            ][-PERCENTILE_LOOKBACK:]
            if not prior_rv:
                continue
            last20 = sixty[-RV_WINDOW:]
            drift20 = float(sum(returns[symbol][d] for d in last20))
            if symbol == "BTCUSDT":
                beta60 = 1.0
            else:
                x = np.asarray([btc_returns[d] for d in sixty], dtype=float)
                y = np.asarray([returns[symbol][d] for d in sixty], dtype=float)
                variance = float(np.var(x))
                if variance <= 0:
                    continue
                beta60 = float(np.cov(y, x, ddof=0)[0, 1] / variance)
            percentile = midrank_percentile(rv_by_day[source_day], prior_rv)
            trade_day = source_day + timedelta(days=1)
            source = metadata[symbol][source_day]
            records.append(
                {
                    "symbol": symbol,
                    "trade_day": trade_day,
                    "prior_day_high": float(source["high"]),
                    "prior_day_low": float(source["low"]),
                    "rv20": rv_by_day[source_day],
                    "vol_pct": percentile,
                    "vol_tercile": vol_tercile(percentile),
                    "drift20": drift20,
                    "beta60": beta60,
                    "state_source_day": source_day,
                    "state_known_ts": datetime.combine(trade_day, time.min, tzinfo=timezone.utc),
                    "range_source_day": source_day,
                    "range_known_ts": datetime.combine(trade_day, time.min, tzinfo=timezone.utc),
                }
            )

    by_day: dict[date, list[dict]] = defaultdict(list)
    for record in records:
        by_day[record["trade_day"]].append(record)
    for day_records in by_day.values():
        complete = len(day_records) == len(SYMBOLS)
        order = sorted(day_records, key=lambda row: (-row["vol_pct"], row["symbol"]))
        ranks = {row["symbol"]: rank for rank, row in enumerate(order, start=1)}
        for row in day_records:
            row["cross_eligible"] = complete
            row["cross_rank"] = ranks[row["symbol"]] if complete else None
    return state_records_frame(records).sort(["trade_day", "symbol"])


def _calendar_third(ts: datetime, band: str) -> int:
    start, end = (
        (DESIGN_ELIGIBLE_START, DESIGN_END)
        if band == "DESIGN"
        else (DESIGN_END, CONFIRM_END)
    )
    fraction = (ts - start).total_seconds() / (end - start).total_seconds()
    return min(3, max(1, int(fraction * 3) + 1))


def finalise_events(raw: pl.DataFrame) -> pl.DataFrame:
    records = []
    for row in raw.iter_rows(named=True):
        entry_ts = row["entry_ts"]
        if DESIGN_START <= entry_ts < DESIGN_END:
            band = "DESIGN"
        elif DESIGN_END <= entry_ts < CONFIRM_END:
            band = "CONFIRM"
        else:
            continue
        event_id = f"{row['symbol']}::{entry_ts.isoformat()}::{row['direction']:+d}"
        records.append(
            {
                "event_id": event_id,
                "symbol": row["symbol"],
                "band": band,
                "trigger_ts": row["trigger_ts"],
                "entry_ts": entry_ts,
                "exit_ts": row["exit_ts"],
                "trade_day": row["trade_day"],
                "utc_slot": row["utc_slot"],
                "utc_week": entry_ts.strftime("%G-W%V"),
                "calendar_third": _calendar_third(entry_ts, band),
                "direction": row["direction"],
                "rv20": row["rv20"],
                "vol_pct": row["vol_pct"],
                "vol_tercile": row["vol_tercile"],
                "drift20": row["drift20"],
                "beta60": row["beta60"],
                "cross_rank": row["cross_rank"],
                "cross_eligible": row["cross_eligible"],
                "top2": bool(row["cross_eligible"] and row["cross_rank"] <= 2),
                "state_source_day": row["state_source_day"],
                "state_known_ts": row["state_known_ts"],
                "range_source_day": row["range_source_day"],
                "range_known_ts": row["range_known_ts"],
            }
        )
    events = state_records_frame(records).sort(["entry_ts", "symbol"])
    assert_outcome_isolated(events)
    return events


def _counts(events: pl.DataFrame) -> dict:
    rows = events.iter_rows(named=True)
    nested: dict[str, dict] = {}
    material = list(rows)
    for band in ("DESIGN", "CONFIRM"):
        band_rows = [row for row in material if row["band"] == band]
        nested[band] = {
            "events": len(band_rows),
            "unique_dates": len({row["trade_day"] for row in band_rows}),
            "unique_weeks": len({row["utc_week"] for row in band_rows}),
            "by_symbol": dict(sorted(Counter(row["symbol"] for row in band_rows).items())),
            "by_tercile": dict(sorted(Counter(row["vol_tercile"] for row in band_rows).items())),
            "by_direction": {
                "LONG": sum(row["direction"] == 1 for row in band_rows),
                "SHORT": sum(row["direction"] == -1 for row in band_rows),
            },
            "by_calendar_third": dict(
                sorted(Counter(str(row["calendar_third"]) for row in band_rows).items())
            ),
            "cross_eligible": sum(bool(row["cross_eligible"]) for row in band_rows),
            "top2": sum(bool(row["top2"]) for row in band_rows),
        }
        clusters = Counter(row["entry_ts"].isoformat() for row in band_rows)
        nested[band]["same_timestamp_clusters"] = {
            "n_clustered_timestamps": sum(size > 1 for size in clusters.values()),
            "max_cluster_size": max(clusters.values(), default=0),
            "cluster_size_distribution": dict(sorted(Counter(clusters.values()).items())),
        }
        mde = {}
        for symbol in (*SYMBOLS, "POOLED_DISCLOSURE"):
            sample = band_rows if symbol == "POOLED_DISCLOSURE" else [
                row for row in band_rows if row["symbol"] == symbol
            ]
            high_dates = {row["trade_day"] for row in sample if row["vol_tercile"] == "HIGH"}
            control_dates = {
                row["trade_day"] for row in sample if row["vol_tercile"] in {"MID", "LOW"}
            }
            all_dates = {row["trade_day"] for row in sample}
            mde[symbol] = {
                "effective_dates_all": len(all_dates),
                "effective_dates_high": len(high_dates),
                "effective_dates_mid_low": len(control_dates),
                "one_sample_mde_bps": {
                    str(sigma): one_sample_mde_bps(len(high_dates), sigma)
                    for sigma in (50, 100, 200)
                },
                "high_vs_mid_low_mde_bps": {
                    str(sigma): two_sample_mde_bps(len(high_dates), len(control_dates), sigma)
                    for sigma in (50, 100, 200)
                },
            }
        nested[band]["prospective_mde"] = mde
    return nested


def _signed_data_status() -> dict:
    source_root = (
        ROOT
        / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/data/staging/bars"
    )
    source_paths = {
        symbol: source_root / f"{symbol}.parquet" for symbol in SYMBOLS
    }
    raw_readable = all(path.is_file() for path in source_paths.values())
    catalog_root = ROOT / "data/catalog_sigbar/train"
    catalog_file_count = (
        sum(path.is_file() for path in catalog_root.rglob("*"))
        if catalog_root.exists()
        else 0
    )
    attestation_path = OUT / "signed_train_attestation.json"
    attestation = (
        json.loads(attestation_path.read_text(encoding="utf-8"))
        if attestation_path.exists()
        else {}
    )
    catalog_verified = (
        attestation.get("status") == "VERIFIED"
        and tuple(attestation.get("symbols", ())) == SYMBOLS
        and all(
            attestation.get("per_symbol", {}).get(symbol, {}).get("status") == "VERIFIED"
            for symbol in SYMBOLS
        )
        and catalog_file_count > 0
    )
    ready = raw_readable and catalog_verified
    return {
        "raw_source_readable": raw_readable,
        "train_catalog_verified": catalog_verified,
        "ready": ready,
        "per_symbol_source_paths": {
            symbol: str(path.relative_to(ROOT)) for symbol, path in source_paths.items()
        },
        "catalog_root": str(catalog_root.relative_to(ROOT)),
        "catalog_file_count": catalog_file_count,
        "catalog_tree_sha256": attestation.get("catalog_tree_sha256"),
        "attestation_path": str(attestation_path.relative_to(ROOT)),
        "attestation_status": attestation.get("status", "MISSING"),
        "execution_consequence": (
            "signed-data preparation cleared; outcome execution still requires runner QA and "
            "separate operator authorisation"
            if ready
            else "outcome execution blocked until the five-symbol TRAIN signed catalog is verified"
        ),
    }


def _core_admission_attestation() -> dict:
    path = (
        ROOT
        / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/"
        "admission-ledger.jsonl"
    )
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("symbol") in SYMBOLS:
            rows[row["symbol"]] = row
    missing = sorted(set(SYMBOLS) - set(rows))
    failures = {
        symbol: {
            "admission": row.get("admission"),
            "collection_gap_minutes": row.get("collection_gap_minutes"),
            "outage_minutes": row.get("outage_minutes"),
            "unresolved_error_days": row.get("unresolved_error_days"),
        }
        for symbol, row in rows.items()
        if row.get("admission") != "ADMITTED"
        or row.get("collection_gap_minutes") != 0
        or row.get("outage_minutes") != 0
        or row.get("unresolved_error_days") != 0
    }
    if missing or failures:
        raise RuntimeError(f"core admission coverage failed: missing={missing} failures={failures}")
    return {
        symbol: {
            "first_bar": rows[symbol]["first_bar"],
            "last_bar": rows[symbol]["last_bar"],
            "no_trade_minutes": rows[symbol]["no_trade_minutes"],
            "collection_gap_minutes": 0,
            "outage_minutes": 0,
            "unresolved_error_days": 0,
        }
        for symbol in SYMBOLS
    }


def run_census() -> tuple[pl.DataFrame, dict]:
    manifest = load_fence_manifest()
    if manifest.train_end_utc != CONFIRM_END:
        raise RuntimeError("registered CONFIRM end does not equal the pinned TRAIN fence")
    catalog = ParquetDataCatalog(ROOT / "data/catalog")
    admission = _core_admission_attestation()
    daily_by_symbol: dict[str, pl.DataFrame] = {}
    four_hour_by_symbol: dict[str, pl.DataFrame] = {}
    coverage = {}
    for symbol in SYMBOLS:
        bars = fenced_bar_query(
            catalog,
            [BAR_TYPE.format(symbol=symbol)],
            start=manifest.analysis_start_utc,
            end=manifest.train_end_utc,
            band="TRAIN",
            manifest=manifest,
        )
        minutes = _bars_to_frame(bars, symbol)
        daily, bars_4h = aggregate_inputs(minutes, coverage_attested=True)
        daily_by_symbol[symbol] = daily
        four_hour_by_symbol[symbol] = bars_4h
        coverage[symbol] = {
            "n_minute_bars": minutes.height,
            "first_ts_event": str(minutes["ts_event"].min()),
            "last_ts_event": str(minutes["ts_event"].max()),
            "n_daily_boundary_complete": daily.filter("boundary_complete").height,
            "n_4h_boundary_complete": bars_4h.filter("boundary_complete").height,
        }
    states = build_states(daily_by_symbol)
    raw = pl.concat(
        [locate_breakouts(four_hour_by_symbol[symbol], states) for symbol in SYMBOLS],
        how="diagonal_relaxed",
    )
    events = finalise_events(raw)
    counts = _counts(events)
    high = events.filter(pl.col("vol_tercile") == "HIGH")
    golden = (
        high.sort(["symbol", "entry_ts"])
        .group_by("symbol", maintain_order=True)
        .first()
        .sort("symbol")
        .head(3)
        .select(["event_id", "symbol", "trigger_ts", "entry_ts", "exit_ts", "direction"])
        .to_dicts()
    )
    payload = {
        "item": "SPDR-011",
        "stage": "OUTCOME_ISOLATED_CENSUS",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "bands": {
            "DESIGN": f"[{DESIGN_START.isoformat()}, {DESIGN_END.isoformat()})",
            "DESIGN_EFFECTIVE_ELIGIBLE": (
                f"[{DESIGN_ELIGIBLE_START.isoformat()}, {DESIGN_END.isoformat()})"
            ),
            "CONFIRM": f"[{DESIGN_END.isoformat()}, {CONFIRM_END.isoformat()})",
            "TEST": "NOT_QUERIED",
            "HOLDOUT": "NOT_QUERIED",
        },
        "fence_manifest_sha256": manifest.sha256,
        "query_band": "TRAIN",
        "max_query_end": manifest.train_end_utc.isoformat(),
        "source_data_class": "Nautilus Bar OHLCV only",
        "outcome_isolation": {
            "status": "PASS",
            "allowed_event_columns": sorted(ALLOWED_EVENT_COLUMNS),
            "forbidden_fields_absent": True,
            "entry_exit_prices_loaded": False,
            "forward_path_loaded": False,
            "returns_or_pnl_computed": False,
            "post_event_completeness_filter_applied": False,
        },
        "coverage": coverage,
        "admission_coverage_attestation": admission,
        "counts": counts,
        "prospective_mde_note": (
            "Count-only normal approximation at 5% two-sided / 80% power; independent unit is "
            "unique UTC date and sigma grid is assumed, not estimated from outcomes. Final MDE uses "
            "date-block resampling after authorised emission."
        ),
        "golden_event_keys_no_prices": golden,
        "signed_data": _signed_data_status(),
    }
    return events, payload


def main() -> None:
    events, payload = run_census()
    OUT.mkdir(parents=True, exist_ok=True)
    event_path = OUT / "census_event_keys.parquet"
    result_path = OUT / "census.json"
    events.write_parquet(event_path)
    result_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"events": events.height, "result": str(result_path)}, indent=2))


if __name__ == "__main__":
    main()
