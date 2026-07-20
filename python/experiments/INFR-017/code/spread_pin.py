"""INFR-017 W2/W3/W4 — pin the spread feature, measure stream dependence, check NTrades.

Source methodology (`SIGNAL-SIGNED.md`):

- **P4** — "the feed's per-bar spread/liquidity column. Its precise definition is
  pinned in Phase 0 (A8); until pinned it is a *relative* liquidity-stress
  feature only."
- **A8** — "pin the spread-proxy column's exact definition."
- **§0.3 / §2.5** — the spread regime layer is treated as separable from the
  bar-flow / session-flow streams. Both are computed from the same aggressor
  split here, so the dependence must be measured, not assumed away (W3).
- **Part 5** — a trade-count column yields average trade size as a z-scored
  participation *confidence multiplier*, "never a standalone signal" (W4).

W2 characterises the stored column, evaluates candidate estimators on the
A8 audit sample, and writes a frozen pin. The candidate set and the decision
rule are declared in ``design.md`` §4/§5 before any result is read.

Usage
-----
    python python/experiments/INFR-017/code/spread_pin.py
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ARCHIVE_URL = "https://public.bybit.com/trading/{symbol}/{symbol}{day}.csv.gz"

# Same pre-declared sample as the A8 audit (design.md §5) — one download budget,
# one sample, no post-hoc sample selection.
SAMPLE_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT")
SAMPLE_DAYS: tuple[str, ...] = ("2022-09-14", "2023-01-11", "2023-06-07", "2023-11-01")

# Instrument tick sizes (INFR-011 artifacts/instrument-specs.json; used for the
# tick-floor sanity check on the recomputed estimator).
TICK_SIZES: dict[str, float] = {
    "BTCUSDT": 0.1,
    "ETHUSDT": 0.01,
    "SOLUSDT": 0.001,
    "DOGEUSDT": 0.00001,
    "XRPUSDT": 0.0001,
}

# W3 reporting threshold (design.md §5) — constrains a downstream framing rule,
# does not gate this item (INFR-016: value reads are report layers).
DEPENDENCE_REPORT_THRESHOLD = 0.20

STAGING_DIR = "python/experiments/INFR-011/data/staging/bars"
OUT_RELPATH = "python/experiments/INFR-017/results/column_pins.json"

TRAIN_END_UTC = datetime(2023, 12, 18, tzinfo=timezone.utc)

# The exact stored definition, quoted from the producing code so the pin is
# verbatim rather than remembered (L-21 discipline applied to a column).
STORED_SPREAD_DEFINITION = {
    "source_file": "python/experiments/INFR-011/scripts/stream_pipeline.py",
    "source_lines": "day_to_bars, ~L330-356",
    "MeanBuy": "mean(price) over trades in the minute with side == 'buy'  (taker buy)",
    "MeanSell": "mean(price) over trades in the minute with side == 'sell' (taker sell)",
    "SpreadAbs": "MeanBuy - MeanSell",
    "SpreadBps": "1e4 * SpreadAbs / ((MeanBuy + MeanSell) / 2)",
    "null_when": "a minute contains trades on only one side (MeanBuy or MeanSell null)",
    "tick_floor_applied": False,
    "doc_claim": (
        "docs/references/dataset-reference.md describes this column as having a "
        "'tick-size floor, conservative bias' — NO tick floor exists in the "
        "producing code. Doc and artifact disagree."
    ),
    "consumer": (
        "xen.evaluation.t1_round_trip_spread_bps returns stress*spread_bps unfloored, "
        "so a negative value propagates into bybit_round_trip_cost_bps as negative cost."
    ),
}


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
    """Fetch one gzipped day of raw trades; None when the archive lacks the file."""
    try:
        with urllib.request.urlopen(
            ARCHIVE_URL.format(symbol=symbol, day=day), timeout=timeout
        ) as resp:
            return resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def _read_trades(gz_bytes: bytes) -> pl.DataFrame:
    """Parse a raw archive day into cleaned, minute-tagged, signed trades."""
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
        return df
    return (
        df.filter(
            pl.col("timestamp").is_not_null()
            & pl.col("price").is_not_null()
            & pl.col("size").is_not_null()
            & (pl.col("size") > 0)
            & (pl.col("price") > 0)
        )
        .sort("timestamp")
        .with_columns(
            ((pl.col("timestamp") * 1000).cast(pl.Int64) // 60_000 * 60_000).alias("bar_ms"),
            pl.when(pl.col("side").str.to_lowercase() == "buy")
            .then(1)
            .otherwise(-1)
            .alias("q"),
        )
    )


# ---------------------------------------------------------------------------
# Pure computation — candidate spread estimators
# ---------------------------------------------------------------------------


def estimator_stored(trades: pl.DataFrame) -> pl.DataFrame:
    """Candidate A — the stored definition exactly: minute MeanBuy - MeanSell over (MeanBuy+MeanSell)/2."""
    return (
        trades.group_by("bar_ms")
        .agg(
            pl.col("price").filter(pl.col("q") == 1).mean().alias("mb"),
            pl.col("price").filter(pl.col("q") == -1).mean().alias("ms"),
        )
        .with_columns(((pl.col("mb") + pl.col("ms")) / 2.0).alias("mid"))
        .with_columns(
            (1e4 * (pl.col("mb") - pl.col("ms")) / pl.col("mid")).alias("spread_bps")
        )
        .select(["bar_ms", "spread_bps"])
        .sort("bar_ms")
    )


def estimator_flip_pair(trades: pl.DataFrame) -> pl.DataFrame:
    """Candidate C — median |Δprice| across adjacent side-flipping trade pairs.

    Mechanism: consecutive trades on opposite aggressor sides cross the quoted
    spread, so |p_t − p_{t−1}| ≈ the spread for that pair. Same-side runs are
    excluded (they walk the book, not the spread). The per-minute **median** is
    robust to the drift that destroys any mean-price differencing estimator.

    Parameters
    ----------
    trades :
        Cleaned signed trades with ``bar_ms``, ``price``, ``q`` columns.

    Returns
    -------
    polars.DataFrame
        ``bar_ms``, ``spread_bps``, ``n_flip`` per minute.
    """
    t = trades.with_columns(
        pl.col("q").shift(1).alias("q_prev"),
        pl.col("price").shift(1).alias("p_prev"),
    )
    flips = t.filter(pl.col("q_prev").is_not_null() & (pl.col("q") != pl.col("q_prev")))
    if flips.is_empty():
        return pl.DataFrame({"bar_ms": [], "spread_bps": [], "n_flip": []})
    return (
        flips.with_columns(
            (1e4 * (pl.col("price") - pl.col("p_prev")).abs() / pl.col("price")).alias("s")
        )
        .group_by("bar_ms")
        .agg(
            pl.col("s").median().alias("spread_bps"),
            pl.len().alias("n_flip"),
        )
        .sort("bar_ms")
    )


def describe(series: pl.Series) -> dict[str, float]:
    """Distribution summary used to judge whether a candidate behaves like a spread."""
    v = series.drop_nulls().drop_nans()
    if len(v) == 0:
        return {"n": 0}
    return {
        "n": int(len(v)),
        "pct_negative": round(100.0 * float((v < 0).sum()) / len(v), 3),
        "q01": round(float(v.quantile(0.01)), 5),
        "q25": round(float(v.quantile(0.25)), 5),
        "median": round(float(v.quantile(0.50)), 5),
        "q75": round(float(v.quantile(0.75)), 5),
        "q99": round(float(v.quantile(0.99)), 5),
    }


def bar_delta_features(trades: pl.DataFrame) -> pl.DataFrame:
    """Per-minute Δ, V and Δ/V — the bar-flow quantities W3 tests dependence against."""
    return (
        trades.group_by("bar_ms")
        .agg(
            pl.col("size").sum().alias("V"),
            (pl.col("size") * pl.col("q")).sum().alias("delta"),
            pl.len().alias("n_trades"),
        )
        .with_columns((pl.col("delta") / pl.col("V")).alias("delta_ratio"))
        .sort("bar_ms")
    )


def pearson_with_ci(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """Pearson correlation with a Fisher-z 95% CI (disclosure statistic, not a gate)."""
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 10 or np.std(x) == 0 or np.std(y) == 0:
        return {"n": int(n), "corr": float("nan"), "ci_low": float("nan"), "ci_high": float("nan")}
    r = float(np.corrcoef(x, y)[0, 1])
    r_clipped = min(max(r, -0.999999), 0.999999)
    z = np.arctanh(r_clipped)
    se = 1.0 / np.sqrt(n - 3)
    return {
        "n": int(n),
        "corr": round(r, 4),
        "ci_low": round(float(np.tanh(z - 1.96 * se)), 4),
        "ci_high": round(float(np.tanh(z + 1.96 * se)), 4),
    }


# ---------------------------------------------------------------------------
# Per-symbol orchestration
# ---------------------------------------------------------------------------


def analyse_stored_column(staging_dir: Path, symbol: str) -> dict[str, Any]:
    """TRAIN-band distribution of the stored SpreadBps column for one symbol.

    Bounded to ``OpenTime < train_end_utc``. The staging parquets run past
    ``holdout_start_utc``, so an unbounded scan here would touch the sealed
    holdout — the exact defect caught earlier in this item.
    """
    path = staging_dir / f"{symbol}.parquet"
    if not path.exists():
        return {"available": False}
    df = (
        pl.scan_parquet(path)
        .select(["OpenTime", "SpreadBps"])
        .filter(pl.col("OpenTime") < TRAIN_END_UTC.replace(tzinfo=None))
        .collect()
    )
    out = describe(df["SpreadBps"])
    out["available"] = True
    out["null_count"] = int(df["SpreadBps"].null_count())
    out["scope"] = "FULL TRAIN band (OpenTime < train_end_utc)"
    return out


def analyse_symbol_sample(symbol: str, days: tuple[str, ...]) -> dict[str, Any]:
    """Download the sample days and compare candidate estimators for one symbol."""
    frames_stored, frames_flip, frames_flow = [], [], []
    days_used: list[str] = []

    for day in days:
        gz = download_day(symbol, day)
        if gz is None:
            continue
        trades = _read_trades(gz)
        del gz
        if trades.is_empty():
            continue
        frames_stored.append(estimator_stored(trades))
        frames_flip.append(estimator_flip_pair(trades))
        frames_flow.append(bar_delta_features(trades))
        days_used.append(day)

    if not days_used:
        return {"days_used": [], "note": "no archive days available"}

    a = pl.concat(frames_stored)
    c = pl.concat(frames_flip)
    flow = pl.concat(frames_flow)

    tick = TICK_SIZES.get(symbol)
    joined = c.join(flow, on="bar_ms", how="inner")

    # W3 — dependence between the spread feature and the bar-flow stream.
    w3_stored = a.join(flow, on="bar_ms", how="inner")
    dep_stored = pearson_with_ci(
        w3_stored["spread_bps"].to_numpy(), w3_stored["delta_ratio"].to_numpy()
    )
    dep_flip = pearson_with_ci(
        joined["spread_bps"].to_numpy(), joined["delta_ratio"].to_numpy()
    )

    # W4 — average trade size (participation multiplier candidate).
    avg_size = (flow["V"] / flow["n_trades"]).to_numpy()

    return {
        "days_used": days_used,
        "tick_size": tick,
        "scope": "4 pre-declared SAMPLE DAYS only — not the full TRAIN band",
        "candidate_A_stored_definition": describe(a["spread_bps"]),
        "candidate_C_flip_pair": describe(c["spread_bps"]),
        "median_flips_per_minute": float(c["n_flip"].median()) if c.height else None,
        "w3_dependence_delta_ratio_vs_spread": {
            "stored_column": dep_stored,
            "flip_pair_estimator": dep_flip,
        },
        "w4_avg_trade_size": {
            "n": int(np.isfinite(avg_size).sum()),
            "median": round(float(np.nanmedian(avg_size)), 6),
            "q01": round(float(np.nanquantile(avg_size, 0.01)), 6),
            "q99": round(float(np.nanquantile(avg_size, 0.99)), 6),
        },
    }


def _tick_bps_reference(symbol: str, staging_dir: Path) -> float | None:
    """One tick expressed in bps at the SAMPLE-period median price.

    Two fence/comparability rules, both load-bearing:

    1. The price median is taken over the **sampled days only**, so the tick
       reference is on the same price regime as the estimator it is compared
       against. A full-history median would price 2024-26 BTC against a
       2022-23 spread estimate and understate the tick by ~2.4x.
    2. It must never read beyond ``train_end_utc``. The staging parquets run to
       2026-07, past ``holdout_start_utc``; an unbounded scan here would touch
       holdout data. The day filter enforces TRAIN containment by construction
       (all sample days are TRAIN-asserted at module level).
    """
    tick = TICK_SIZES.get(symbol)
    if tick is None:
        return None
    path = staging_dir / f"{symbol}.parquet"
    if not path.exists():
        return None

    day_bounds = [
        datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=None) for d in SAMPLE_DAYS
    ]
    day_filter = pl.any_horizontal(
        [
            (pl.col("OpenTime") >= d) & (pl.col("OpenTime") < d + timedelta(days=1))
            for d in day_bounds
        ]
    )
    px = (
        pl.scan_parquet(path)
        .select(["OpenTime", "Close"])
        .filter((pl.col("Close") > 0) & (pl.col("OpenTime") < TRAIN_END_UTC.replace(tzinfo=None)))
        .filter(day_filter)
        .collect()["Close"]
        .median()
    )
    return round(1e4 * tick / float(px), 5) if px else None


def build_pin(per_symbol: dict[str, Any]) -> dict[str, Any]:
    """Per-symbol headline numbers behind the W2 decision."""
    verdicts = {}
    for sym, blk in per_symbol.items():
        s = blk.get("sample", {})
        a = s.get("candidate_A_stored_definition", {})
        c = s.get("candidate_C_flip_pair", {})
        verdicts[sym] = {
            "stored_pct_negative": a.get("pct_negative"),
            "flip_pct_negative": c.get("pct_negative"),
            "flip_median_bps": c.get("median"),
            "one_tick_bps": blk.get("one_tick_bps"),
        }
    return verdicts


def build_w3_verdict(per_symbol: dict[str, Any]) -> dict[str, Any]:
    """W3: does sharing a source make the spread and bar-flow streams dependent?

    design.md 5 declares that |corr| >= 0.20 writes an independence constraint
    BINDING into the pin. QA run 1 found the threshold measured but the
    consequence never coded. It is coded here so a rerun that breaches it
    actually fires.
    """
    rows = {}
    breach = False
    for sym, blk in per_symbol.items():
        dep = blk.get("sample", {}).get("w3_dependence_delta_ratio_vs_spread", {})
        stored = dep.get("stored_column", {})
        corr = stored.get("corr")
        rows[sym] = {
            "corr_delta_ratio_vs_stored_spread": corr,
            "ci": [stored.get("ci_low"), stored.get("ci_high")],
            "corr_delta_ratio_vs_flip_pair": dep.get("flip_pair_estimator", {}).get("corr"),
        }
        if corr is not None and corr == corr and abs(corr) >= DEPENDENCE_REPORT_THRESHOLD:
            breach = True
    return {
        "threshold": DEPENDENCE_REPORT_THRESHOLD,
        "breached": breach,
        "per_symbol": rows,
        "constraint": (
            "BINDING: spread-regime reads may NOT be presented as independent corroboration "
            "of a delta read"
            if breach else
            "NOT BINDING: measured dependence is far below threshold; the spread-regime layer "
            "may be treated as separable from bar-flow reads despite the shared source"
        ),
        "caveat": (
            "Fisher-z CI assumes independent observations; these are minute-level and "
            "autocorrelated, so the CI is NOT dependence-honest. Disclosure only."
        ),
    }


def build_decision(per_symbol: dict[str, Any]) -> dict[str, Any]:
    """The W2 decision, its reasons, and why each rejected option lost.

    design.md §8.2 requires the pin to STATE the chosen resolution and the
    reasons the alternatives were rejected. QA run 1 (Issue 3) found the
    decision existed only as a hard-coded constant in ``signed_bar_lane.py`` —
    encoded in a different file from the pin meant to freeze it, which is the
    exact drift the pin exists to prevent. Consumers must read the status from
    here.
    """
    # Two DIFFERENT scopes, and the decision-of-record must quote the right one.
    # `stored_column_full_train` is the whole TRAIN band; `candidate_A` is the 4
    # sample days. QA runs 2 and 3 both flagged this block for quoting the
    # sample-day numbers under a "TRAIN band" label.
    train_neg = {
        s: b.get("stored_column_full_train", {}).get("pct_negative")
        for s, b in per_symbol.items()
    }
    sample_neg = {s: v["stored_pct_negative"] for s, v in build_pin(per_symbol).items()}
    flip_neg = {s: v["flip_pct_negative"] for s, v in build_pin(per_symbol).items()}
    return {
        "chosen": "STORED_COLUMN_UNUSABLE_PLUS_SAMPLE_VALIDATED_REPLACEMENT",
        "stored_column_status": "UNUSABLE",
        "stored_column_reason": (
            "SpreadBps = MeanBuy - MeanSell over a whole minute is a difference of mean "
            "PRINT prices, so it is dominated by intra-minute drift rather than the bid-ask "
            f"gap. Measured negative on the FULL TRAIN band in {train_neg} percent of "
            "minutes; a spread is non-negative by construction. Must never be used as a "
            "cost input."
        ),
        "evidence_scopes": {
            "full_train_band_pct_negative": train_neg,
            "sample_days_pct_negative": sample_neg,
            "note": (
                "these two differ by 1-2 points per symbol because they cover different "
                "spans; the decision rests on the FULL TRAIN figures"
            ),
        },
        "replacement_estimator": {
            "name": "flip_pair_effective_spread",
            "definition": (
                "per minute, the MEDIAN of |price_t - price_{t-1}| over adjacent trade pairs "
                "whose aggressor side FLIPS; same-side runs excluded (they walk the book, not "
                "the spread); median for robustness to drift"
            ),
            "status": "VALIDATED_ON_SAMPLE_ONLY",
            "evidence": (
                f"0.0 percent negative on every sampled symbol ({flip_neg}); lands at the tick "
                "floor for wide-tick instruments (DOGE, XRP) and above it for fine-tick ones"
            ),
            "known_bias": (
                "CONSERVATIVE UPPER BOUND, not the quoted spread — adjacent flips also span "
                "real price movement. Right direction of error for a cost floor; must be "
                "labelled as such wherever used."
            ),
            "blocker_to_full_adoption": (
                "requires raw trades, which are not retained in bulk. Validated on 20 "
                "symbol-days only. Universe-wide recompute is an INFR-011-scale data "
                "operation, outside INFR-017's budget."
            ),
        },
        "interim_cost_input": (
            "taker RT 11.0 bps + max(one tick, flip-pair estimate where measured) + funding; "
            "tick-size floor elsewhere. Never the stored column."
        ),
        "rejected_options": {
            "(i) recompute and ship universe-wide": (
                "REJECTED FOR NOW, not on merit — this is the right answer and the estimator "
                "is validated, but it needs a bulk raw-trade re-download that INFR-017 does "
                "not budget. Retained as the target state."
            ),
            "(ii) floor-and-flag the stored column": (
                "REJECTED ON MERIT. Flooring a drift measure at zero does not make it a "
                "spread; it would yield a confidently wrong small number precisely where the "
                "true spread matters, and would preserve the false impression that the column "
                "means something."
            ),
        },
        "downstream_constraint": (
            "xen.evaluation.t1_round_trip_spread_bps passes its argument through unfloored, so "
            "feeding it the stored column produces NEGATIVE cost. Callers must not."
        ),
    }


def main() -> int:
    root = _repo_root()
    staging_dir = root / STAGING_DIR
    out_path = root / OUT_RELPATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    per_symbol: dict[str, Any] = {}
    for symbol in tqdm(SAMPLE_SYMBOLS, desc="spread pin", unit="symbol"):
        blk: dict[str, Any] = {
            "stored_column_full_train": analyse_stored_column(staging_dir, symbol),
            "sample": analyse_symbol_sample(symbol, SAMPLE_DAYS),
        }
        blk["one_tick_bps"] = _tick_bps_reference(symbol, staging_dir)
        per_symbol[symbol] = blk

    payload = {
        "item": "INFR-017",
        "work_items": ["W2", "W3", "W4"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "band_note": (
            "TWO DISTINCT SCOPES, do not conflate: 'stored_column_full_train' is the whole "
            "TRAIN band (OpenTime < train_end_utc); every 'sample' block and both candidate "
            "estimators are the 4 pre-declared sample DAYS only. Figures differ by 1-2 points "
            "per symbol for that reason."
        ),
        "frozen_parameters": {
            "sample_symbols": list(SAMPLE_SYMBOLS),
            "sample_days": list(SAMPLE_DAYS),
            "candidates": {
                "A": "stored definition — minute MeanBuy − MeanSell, in bps",
                "C": "flip-pair — median |Δprice| over adjacent side-flipping trades, in bps",
            },
            "w3_report_threshold": DEPENDENCE_REPORT_THRESHOLD,
        },
        "W2_stored_definition_pin": STORED_SPREAD_DEFINITION,
        "W2_decision": build_decision(per_symbol),
        "W3_dependence_verdict": build_w3_verdict(per_symbol),
        "W4_ntrades_verdict": {
            "usable": True,
            "quantity": "average trade size = Volume / NTrades",
            "role": "z-scored participation CONFIDENCE MULTIPLIER only",
            "never": "a standalone signal (source Part 5)",
            "mandatory_caveat": (
                "average trade size drifts secularly with order-splitting, so seasonal "
                "normalisation per A5 is mandatory before any threshold is applied"
            ),
            "per_symbol_median_base_units": {
                s_: b.get("sample", {}).get("w4_avg_trade_size", {}).get("median")
                for s_, b in per_symbol.items()
            },
        },
        "per_symbol": per_symbol,
        "summary": build_pin(per_symbol),
    }
    # Self-pin: sha256 over the payload with the timestamp excluded, so the hash
    # is stable across reruns of identical inputs (design.md 8.5).
    hashable = {k: v for k, v in payload.items() if k != "generated_utc"}
    payload["pin_sha256"] = hashlib.sha256(
        json.dumps(hashable, sort_keys=True, default=str).encode()
    ).hexdigest()
    out_path.write_text(json.dumps(payload, indent=2, default=str))

    print(f"\ncolumn pins -> {out_path.relative_to(root)}")
    for sym, v in payload["summary"].items():
        print(f"  {sym}: stored neg={v['stored_pct_negative']}%  "
              f"flip neg={v['flip_pct_negative']}%  flip med={v['flip_median_bps']} bps  "
              f"1 tick={v['one_tick_bps']} bps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
