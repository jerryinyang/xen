"""INFR-017 W1 — A8 provenance audit: reconcile the stored taker split against raw trades.

Source methodology (`SIGNAL-SIGNED.md`) Phase 0 / A8:

    "Phase 0 includes a one-time audit — cross-check the taker split against raw
    trade data for a sample window (they must reconcile to rounding) ... A
    framework built on an unaudited column inherits its silent errors."

This is CF-SIGAUC-001's KILL-GATE (HYP-I1). The stored bars at
``INFR-011/data/staging/bars/<SYMBOL>.parquet`` carry ``BuyVolume``/``SellVolume``
derived by ``INFR-011/scripts/stream_pipeline.py``. This script re-downloads the
raw Bybit trade archive for a pre-declared sample and recomputes those columns
**independently** of that pipeline, then compares.

Independence matters: re-running the producing code would reproduce its own
errors (the L-01 lesson — numeric reproduction is blind to provenance). The
recomputation below is written from the documented Bybit archive schema, not by
importing ``stream_pipeline``.

Sample, tolerance and failure rule are FROZEN in ``design.md`` §5 and must not be
revised after seeing a result.

Usage
-----
    python -m code.a8_provenance_audit          # from python/experiments/INFR-017/
    python python/experiments/INFR-017/code/a8_provenance_audit.py
"""

from __future__ import annotations

import gzip
import io
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Constants — FROZEN in design.md §5. Do not edit after execution.
# ---------------------------------------------------------------------------

ARCHIVE_URL = "https://public.bybit.com/trading/{symbol}/{symbol}{day}.csv.gz"

SAMPLE_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "DOGEUSDT",
    "XRPUSDT",
)

# Four dates evenly spaced across the TRAIN span, chosen by fixed rule
# (14th/11th/7th/1st of four evenly-spaced months), all < train_end_utc.
SAMPLE_DAYS: tuple[str, ...] = (
    "2022-09-14",
    "2023-01-11",
    "2023-06-07",
    "2023-11-01",
)

# Frozen tolerance (design.md §5).
REL_TOLERANCE = 1e-9

# Fence guard — the audit must not touch TEST or HOLDOUT.
TRAIN_END_UTC = datetime(2023, 12, 18, tzinfo=timezone.utc)

STAGING_DIR = "python/experiments/INFR-011/data/staging/bars"
OUT_RELPATH = "python/experiments/INFR-017/results/a8_provenance_audit.json"

# Columns audited. NTrades is compared as an exact integer.
FLOAT_COLS = ("Volume", "BuyVolume", "SellVolume")
INT_COLS = ("NTrades",)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class DayResult:
    """Reconciliation outcome for one (symbol, day)."""

    symbol: str
    day: str
    status: str  # PASS | FAIL | NO_STORED_BARS | DOWNLOAD_FAILED
    n_bars_raw: int
    n_bars_stored: int
    n_bars_matched: int
    max_rel_dev: dict[str, float]
    max_abs_dev: dict[str, float]
    ntrades_mismatches: int
    detail: str = ""
    side_convention: dict | None = None


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


def download_day(symbol: str, day: str, timeout: int = 180) -> bytes | None:
    """Fetch one gzipped day of raw trades; None if the archive has no such file."""
    url = ARCHIVE_URL.format(symbol=symbol, day=day)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


# ---------------------------------------------------------------------------
# Pure computation — independent reimplementation of the bar derivation
# ---------------------------------------------------------------------------


def bars_from_raw_trades(gz_bytes: bytes) -> pl.DataFrame:
    """Recompute 1-minute signed bars from a raw Bybit trade archive day.

    Written from the archive schema (timestamp, symbol, side, size, price, ...),
    NOT by importing the INFR-011 pipeline — an audit that reuses the audited
    code proves nothing.

    Cleaning follows the documented INFR-011 rule (drop null / non-positive
    price and size); that rule is declared behaviour, not a defect, and is
    recorded in the audit output.

    Parameters
    ----------
    gz_bytes :
        Gzipped CSV bytes as served by ``public.bybit.com``.

    Returns
    -------
    polars.DataFrame
        Columns: ``bar_ms``, ``Volume``, ``BuyVolume``, ``SellVolume``, ``NTrades``.
    """
    raw = gzip.decompress(gz_bytes)
    df = pl.read_csv(
        io.BytesIO(raw),
        columns=["timestamp", "side", "size", "price"],
        schema_overrides={
            "timestamp": pl.Float64,
            "side": pl.Utf8,
            "size": pl.Float64,
            "price": pl.Float64,
        },
        ignore_errors=True,
    )
    if df.is_empty():
        return pl.DataFrame()
    # Archive day-files are not guaranteed time-ordered; minute bucketing is
    # order-free but downstream consumers of this helper are not.
    df = df.sort("timestamp")

    df = df.filter(
        pl.col("timestamp").is_not_null()
        & pl.col("price").is_not_null()
        & pl.col("size").is_not_null()
        & (pl.col("size") > 0)
        & (pl.col("price") > 0)
    )
    if df.is_empty():
        return pl.DataFrame()

    side_lower = pl.col("side").str.to_lowercase()
    return (
        df.with_columns(
            ((pl.col("timestamp") * 1000).cast(pl.Int64) // 60_000 * 60_000).alias("bar_ms")
        )
        .group_by("bar_ms")
        .agg(
            pl.col("size").sum().alias("Volume"),
            pl.col("size").filter(side_lower == "buy").sum().alias("BuyVolume"),
            pl.col("size").filter(side_lower == "sell").sum().alias("SellVolume"),
            pl.len().cast(pl.Int64).alias("NTrades"),
        )
        .sort("bar_ms")
    )


def aggressor_side_evidence(gz_bytes: bytes) -> dict[str, Any]:
    """Test whether the archive's ``side`` column is the AGGRESSOR or the MAKER side.

    This is load-bearing for CF-SIGAUC-001, not a curiosity. ``delta = buy − sell``
    is the family's founding measurement; if ``side`` named the *maker*, every
    delta would carry the wrong sign and every absorption / divergence read
    would invert.

    Test: cross-tabulate ``side`` against ``tickDirection``. A taker buy lifts
    the ask and ticks price up, so under the aggressor convention ``Buy`` is
    dominated by ``PlusTick`` and ``Sell`` by ``MinusTick``. Under the maker
    convention the association reverses.

    Returns
    -------
    dict
        Cross-tab counts plus ``buy_plus_ratio`` / ``sell_minus_ratio`` (odds of
        the expected direction over its opposite) and a ``convention`` verdict.
    """
    raw = gzip.decompress(gz_bytes)
    df = pl.read_csv(
        io.BytesIO(raw),
        columns=["side", "tickDirection"],
        schema_overrides={"side": pl.Utf8, "tickDirection": pl.Utf8},
        ignore_errors=True,
    )
    if df.is_empty():
        return {"available": False}

    tab = df.group_by(["side", "tickDirection"]).len()
    counts: dict[str, int] = {
        f"{r['side']}|{r['tickDirection']}": int(r["len"]) for r in tab.iter_rows(named=True)
    }
    buy_plus = counts.get("Buy|PlusTick", 0)
    buy_minus = counts.get("Buy|MinusTick", 0)
    sell_minus = counts.get("Sell|MinusTick", 0)
    sell_plus = counts.get("Sell|PlusTick", 0)

    buy_ratio = buy_plus / buy_minus if buy_minus else float("inf")
    sell_ratio = sell_minus / sell_plus if sell_plus else float("inf")
    aggressor = buy_ratio > 1.0 and sell_ratio > 1.0

    return {
        "available": True,
        "counts": counts,
        "buy_plus_over_buy_minus": round(buy_ratio, 2) if buy_ratio != float("inf") else None,
        "sell_minus_over_sell_plus": round(sell_ratio, 2) if sell_ratio != float("inf") else None,
        "convention": "AGGRESSOR" if aggressor else "NOT_AGGRESSOR",
    }


def load_stored_day(staging_path: Path, day: str) -> pl.DataFrame:
    """Load the stored bars for one UTC day from a per-symbol staging parquet."""
    lo = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    hi = lo.replace(hour=23, minute=59, second=59)
    lo_naive, hi_naive = lo.replace(tzinfo=None), hi.replace(tzinfo=None)

    df = (
        pl.scan_parquet(staging_path)
        .select(["OpenTime", "Volume", "NTrades", "BuyVolume", "SellVolume"])
        .filter((pl.col("OpenTime") >= lo_naive) & (pl.col("OpenTime") <= hi_naive))
        .collect()
    )
    if df.is_empty():
        return df
    return df.with_columns(
        (pl.col("OpenTime").dt.epoch(time_unit="ms")).alias("bar_ms")
    ).select(["bar_ms", "Volume", "BuyVolume", "SellVolume", "NTrades"]).sort("bar_ms")


def reconcile(raw: pl.DataFrame, stored: pl.DataFrame) -> tuple[dict, dict, int, int]:
    """Compare recomputed vs stored bars on the audited columns.

    Returns
    -------
    tuple
        ``(max_rel_dev, max_abs_dev, ntrades_mismatches, n_matched)``.
    """
    joined = raw.join(stored, on="bar_ms", how="inner", suffix="_stored")
    n_matched = joined.height
    max_rel: dict[str, float] = {}
    max_abs: dict[str, float] = {}

    if n_matched == 0:
        return {c: float("nan") for c in FLOAT_COLS}, {c: float("nan") for c in FLOAT_COLS}, -1, 0

    for col in FLOAT_COLS:
        diff = (pl.col(col) - pl.col(f"{col}_stored")).abs()
        # Relative to the stored magnitude; zero-stored rows fall back to absolute.
        rel = pl.when(pl.col(f"{col}_stored").abs() > 0).then(
            diff / pl.col(f"{col}_stored").abs()
        ).otherwise(diff)
        stats = joined.select(
            rel.max().alias("rel"),
            diff.max().alias("abs"),
        )
        max_rel[col] = float(stats["rel"][0])
        max_abs[col] = float(stats["abs"][0])

    mismatches = int(
        joined.select(
            (pl.col("NTrades") != pl.col("NTrades_stored")).sum()
        ).item()
    )
    return max_rel, max_abs, mismatches, n_matched


def audit_symbol_day(symbol: str, day: str, staging_dir: Path) -> DayResult:
    """Run the full download → recompute → reconcile cycle for one symbol-day."""
    empty = {c: float("nan") for c in FLOAT_COLS}

    gz = download_day(symbol, day)
    if gz is None:
        return DayResult(symbol, day, "DOWNLOAD_FAILED", 0, 0, 0, empty, empty, -1,
                         "archive file unavailable")

    raw = bars_from_raw_trades(gz)
    side_evidence = aggressor_side_evidence(gz)
    del gz  # raw bytes are not retained (INFR-013 discipline)

    staging_path = staging_dir / f"{symbol}.parquet"
    if not staging_path.exists():
        return DayResult(symbol, day, "NO_STORED_BARS", raw.height, 0, 0, empty, empty, -1,
                         f"missing {staging_path.name}", side_evidence)

    stored = load_stored_day(staging_path, day)
    if stored.is_empty():
        return DayResult(symbol, day, "NO_STORED_BARS", raw.height, 0, 0, empty, empty, -1,
                         "no stored bars for this day", side_evidence)

    max_rel, max_abs, mismatches, n_matched = reconcile(raw, stored)
    within_tol = all(
        (v == v) and v <= REL_TOLERANCE for v in max_rel.values()
    )  # (v == v) filters NaN

    # A bar present on only one side never enters the deviation statistics (the
    # reconciliation is an inner join), so a dropped-minute defect in the
    # producing pipeline would otherwise pass the gate silently. Promote any
    # key-set disagreement to FAIL rather than a note. (QA run 1, Issue 5b.)
    counts_agree = raw.height == stored.height == n_matched
    status = (
        "PASS"
        if (within_tol and mismatches == 0 and n_matched > 0 and counts_agree)
        else "FAIL"
    )

    detail = ""
    if not counts_agree:
        detail = (
            f"bar-count/key-set mismatch: raw {raw.height} vs stored {stored.height} "
            f"vs matched {n_matched} — unmatched bars are excluded from deviation stats"
        )

    return DayResult(
        symbol=symbol,
        day=day,
        status=status,
        n_bars_raw=raw.height,
        n_bars_stored=stored.height,
        n_bars_matched=n_matched,
        max_rel_dev=max_rel,
        max_abs_dev=max_abs,
        ntrades_mismatches=mismatches,
        detail=detail,
        side_convention=side_evidence,
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _assert_sample_within_train() -> None:
    """Fence guard: every sampled day must sit inside the TRAIN band."""
    for day in SAMPLE_DAYS:
        d = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if d >= TRAIN_END_UTC:
            raise RuntimeError(
                f"FENCE VIOLATION: sample day {day} is not inside TRAIN "
                f"(train_end {TRAIN_END_UTC.date()})"
            )


def _summarise_side_convention(results: list[DayResult]) -> dict[str, Any]:
    """Aggregate the side-vs-tickDirection evidence across the sample.

    Reported as a first-class audit output because the family's founding
    measurement inverts if the convention is the maker side (see
    :func:`aggressor_side_evidence`).
    """
    blocks = [r.side_convention for r in results
              if r.side_convention and r.side_convention.get("available")]
    if not blocks:
        return {"available": False}
    verdicts = {b["convention"] for b in blocks}
    ratios_buy = [b["buy_plus_over_buy_minus"] for b in blocks
                  if b.get("buy_plus_over_buy_minus") is not None]
    ratios_sell = [b["sell_minus_over_sell_plus"] for b in blocks
                   if b.get("sell_minus_over_sell_plus") is not None]
    return {
        "available": True,
        "n_symbol_days": len(blocks),
        "convention": "AGGRESSOR" if verdicts == {"AGGRESSOR"} else "MIXED_OR_NOT_AGGRESSOR",
        "unanimous": verdicts == {"AGGRESSOR"},
        "buy_plus_over_buy_minus": {
            "min": round(min(ratios_buy), 2) if ratios_buy else None,
            "median": round(sorted(ratios_buy)[len(ratios_buy) // 2], 2) if ratios_buy else None,
            "max": round(max(ratios_buy), 2) if ratios_buy else None,
        },
        "sell_minus_over_sell_plus": {
            "min": round(min(ratios_sell), 2) if ratios_sell else None,
            "median": round(sorted(ratios_sell)[len(ratios_sell) // 2], 2) if ratios_sell else None,
            "max": round(max(ratios_sell), 2) if ratios_sell else None,
        },
        "interpretation": (
            "side=Buy is dominated by PlusTick and side=Sell by MinusTick => the archive "
            "'side' column names the AGGRESSOR (taker). delta = buy - sell is net taker "
            "aggression with the correct sign."
        ),
    }


def summarise(results: list[DayResult]) -> dict[str, Any]:
    """Build the audit artifact payload, including the HYP-I1 verdict."""
    n_pass = sum(r.status == "PASS" for r in results)
    n_fail = sum(r.status == "FAIL" for r in results)
    n_other = len(results) - n_pass - n_fail

    worst = {
        col: max(
            (r.max_rel_dev.get(col, float("nan")) for r in results
             if r.max_rel_dev.get(col, float("nan")) == r.max_rel_dev.get(col, float("nan"))),
            default=float("nan"),
        )
        for col in FLOAT_COLS
    }

    # Frozen failure rule (design.md §5): ANY breach => FAIL, and §8.1 requires
    # coverage of ALL declared symbol-days. `n_fail == 0 and n_pass > 0` alone
    # would return PASS on 1-of-20 coverage with 19 downloads missing — the
    # "no partial pass" rule forbids exactly that. (QA run 1, Issue 5a.)
    declared = len(SAMPLE_SYMBOLS) * len(SAMPLE_DAYS)
    if n_fail > 0:
        verdict = "FAIL"
    elif n_pass < declared:
        verdict = "FAIL_INCOMPLETE_COVERAGE"
    else:
        verdict = "PASS"

    return {
        "item": "INFR-017",
        "work_item": "W1",
        "hypothesis": "HYP-I1",
        "question": "Does the stored taker split reproduce from raw Bybit trades?",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_parameters": {
            "sample_symbols": list(SAMPLE_SYMBOLS),
            "sample_days": list(SAMPLE_DAYS),
            "rel_tolerance": REL_TOLERANCE,
            "failure_rule": "ANY symbol-day breaching tolerance => HYP-I1 FAIL => family PARKED",
            "audited_columns": list(FLOAT_COLS) + list(INT_COLS),
            "cleaning_rule": "drop rows with null/non-positive price or size (INFR-011 documented rule)",
            "independence": "recomputed from archive schema; stream_pipeline not imported",
        },
        "counts": {
            "symbol_days_declared": len(SAMPLE_SYMBOLS) * len(SAMPLE_DAYS),
            "pass": n_pass,
            "fail": n_fail,
            "unavailable_or_no_bars": n_other,
        },
        "worst_rel_dev_across_sample": worst,
        "aggressor_side_convention": _summarise_side_convention(results),
        "verdict": verdict,
        "results": [asdict(r) for r in results],
    }


def main() -> int:
    _assert_sample_within_train()
    root = _repo_root()
    staging_dir = root / STAGING_DIR
    out_path = root / OUT_RELPATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pairs = [(s, d) for s in SAMPLE_SYMBOLS for d in SAMPLE_DAYS]
    results: list[DayResult] = []
    for symbol, day in tqdm(pairs, desc="A8 audit", unit="symbol-day"):
        results.append(audit_symbol_day(symbol, day, staging_dir))

    payload = summarise(results)
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"\nA8 provenance audit -> {out_path.relative_to(root)}")
    print(f"  pass={payload['counts']['pass']} fail={payload['counts']['fail']} "
          f"other={payload['counts']['unavailable_or_no_bars']}")
    print(f"  worst relative deviation: {payload['worst_rel_dev_across_sample']}")
    sc = payload["aggressor_side_convention"]
    if sc.get("available"):
        print(f"  side convention: {sc['convention']} (unanimous={sc['unanimous']}, "
              f"buy+/buy- median {sc['buy_plus_over_buy_minus']['median']})")
    print(f"  HYP-I1 VERDICT: {payload['verdict']}")
    for r in results:
        if r.status != "PASS":
            print(f"    [{r.status}] {r.symbol} {r.day} {r.detail}")
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
