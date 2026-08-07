#!/usr/bin/env python3
"""INFR-021 — ingest chapter-03 cTrader 1m timebars into data/catalog_ctrader/.

Symbols: EURUSD, XAUUSD, USTEC.
Venue / InstrumentId: {SYMBOL}.CTrader
Separate catalog root from Bybit data/catalog/ (INFR-011).

For plain OHLCV strategies (no signed aggressor volumes), this catalog is
interchangeable with data/catalog/ (Bybit): same ParquetDataCatalog + Bar
contract; only catalog path, InstrumentId, and fence pin differ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

INFR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
assert (REPO / ".git").exists(), f"repo root miscomputed: {REPO}"

ART = INFR / "artifacts"
RESULTS = INFR / "results"
CATALOG_DIR = REPO / "data" / "catalog_ctrader"
SOURCE_DIR = REPO / "archive" / "chapter-03-xena-mtfctx" / "data" / "timebars"

NAUTILUS_PIN = "1.230.0"
ANALYSIS_FRAC = 0.70
TRAIN_FRAC = 0.70
VENUE = "CTrader"

# Longest 5y collection per symbol (INFR-003 era files).
SOURCES: dict[str, str] = {
    "EURUSD": "timebars_eurusd_20210602_000000_20260621_183431.parquet",
    "XAUUSD": "timebars_xauusd_20210602_000000_20260621_190824.parquet",
    "USTEC": "timebars_ustec_20210602_000000_20260621_190833.parquet",
}

# Encoding / FTMO-aligned contract sizes (engine fees always 0).
SPECS: dict[str, dict] = {
    "EURUSD": {
        "kind": "currency_pair",
        "price_precision": 5,
        "tick": "0.00001",
        "size_precision": 2,
        "size_step": "0.01",
        "lot_size": 100_000,
        "asset_class": None,
    },
    "XAUUSD": {
        "kind": "cfd",
        "price_precision": 2,
        "tick": "0.01",
        "size_precision": 2,
        "size_step": "0.01",
        "lot_size": 100,
        "asset_class": "COMMODITY",
    },
    "USTEC": {
        "kind": "cfd",
        "price_precision": 2,
        "tick": "0.01",
        "size_precision": 2,
        "size_step": "0.01",
        "lot_size": 1,
        "asset_class": "INDEX",
    },
}


def instrument_id_str(symbol: str) -> str:
    return f"{symbol.upper()}.{VENUE}"


def source_path(symbol: str) -> Path:
    return SOURCE_DIR / SOURCES[symbol]


def _floor_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def _as_dt(v) -> datetime:
    """Polars scalar or plain datetime → naive datetime."""
    if hasattr(v, "to_pydatetime"):
        v = v.to_pydatetime()
    if isinstance(v, datetime):
        return v.replace(tzinfo=None) if v.tzinfo is not None else v
    raise TypeError(f"expected datetime, got {type(v)}")


def _z(dt: datetime) -> str:
    dt = _as_dt(dt)
    return dt.isoformat() + "Z"


def make_instrument(symbol: str):
    from nautilus_trader.model.currencies import EUR, USD
    from nautilus_trader.model.enums import AssetClass
    from nautilus_trader.model.identifiers import InstrumentId, Symbol
    from nautilus_trader.model.instruments import Cfd, CurrencyPair
    from nautilus_trader.model.objects import Price, Quantity

    spec = SPECS[symbol]
    iid = InstrumentId.from_str(instrument_id_str(symbol))
    pp = int(spec["price_precision"])
    sp = int(spec["size_precision"])
    common = dict(
        instrument_id=iid,
        raw_symbol=Symbol(symbol),
        price_precision=pp,
        size_precision=sp,
        price_increment=Price.from_str(spec["tick"]),
        size_increment=Quantity.from_str(spec["size_step"]),
        lot_size=Quantity.from_int(int(spec["lot_size"])),
        margin_init=Decimal("0"),
        margin_maint=Decimal("0"),
        maker_fee=Decimal("0"),
        taker_fee=Decimal("0"),
        ts_event=0,
        ts_init=0,
    )
    if spec["kind"] == "currency_pair":
        # EURUSD only in this ingest batch.
        return CurrencyPair(
            base_currency=EUR,
            quote_currency=USD,
            **common,
        )
    ac = getattr(AssetClass, str(spec["asset_class"]))
    return Cfd(
        asset_class=ac,
        quote_currency=USD,
        **common,
    )


def check_invariants(df: pl.DataFrame, symbol: str) -> list[str]:
    errs: list[str] = []
    if df.is_empty():
        return [f"{symbol}: empty"]
    ct = df["CloseTime"]
    if not ct.is_sorted():
        # strict increase: no ties either
        errs.append(f"{symbol}: CloseTime not sorted")
    if ct.n_unique() != len(df):
        errs.append(f"{symbol}: CloseTime not unique ({ct.n_unique()} unique / {len(df)})")
    bad_h = df.filter(pl.col("High") < pl.max_horizontal("Open", "Close")).height
    bad_l = df.filter(pl.col("Low") > pl.min_horizontal("Open", "Close")).height
    if bad_h:
        errs.append(f"{symbol}: {bad_h} High < max(Open,Close)")
    if bad_l:
        errs.append(f"{symbol}: {bad_l} Low > min(Open,Close)")
    nulls = df.select(
        pl.col("Open", "High", "Low", "Close", "TickVolume").null_count()
    ).row(0)
    if any(nulls):
        errs.append(f"{symbol}: nulls in OHLC/TickVolume {nulls}")
    if df.filter(pl.col("TickVolume") < 0).height:
        errs.append(f"{symbol}: negative TickVolume")
    return errs


def load_bars(symbol: str) -> pl.DataFrame:
    path = source_path(symbol)
    if not path.exists():
        raise FileNotFoundError(path)
    df = pl.read_parquet(
        path,
        columns=["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"],
    )
    # Normalise types; ensure ns datetime without tz.
    df = df.with_columns(
        pl.col("CloseTime").cast(pl.Datetime("ns")),
        pl.col("OpenTime").cast(pl.Datetime("ns")),
        pl.col("Open", "High", "Low", "Close").cast(pl.Float64),
        pl.col("TickVolume").cast(pl.Float64),
    ).sort("CloseTime")
    return df


def wrangle_bars(symbol: str, df: pl.DataFrame, instrument):
    from nautilus_trader.model.data import BarType
    from nautilus_trader.persistence.wranglers import BarDataWrangler

    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")
    pdf = (
        df.select(
            timestamp=pl.col("CloseTime"),
            open=pl.col("Open"),
            high=pl.col("High"),
            low=pl.col("Low"),
            close=pl.col("Close"),
            volume=pl.col("TickVolume"),
        )
        .to_pandas()
        .set_index("timestamp")
    )
    # Cython wrangler needs writable buffers (INFR-011 lesson).
    for col in pdf.columns:
        pdf[col] = np.array(pdf[col].to_numpy(), copy=True)
    bars = BarDataWrangler(bar_type, instrument).process(pdf)
    return bar_type, bars


def ingest_symbol(catalog, symbol: str) -> dict:
    df = load_bars(symbol)
    errs = check_invariants(df, symbol)
    if errs:
        return {
            "symbol": symbol,
            "instrument_id": instrument_id_str(symbol),
            "ok": False,
            "errors": errs,
            "source": str(source_path(symbol).relative_to(REPO)),
            "source_sha256": hashlib.sha256(source_path(symbol).read_bytes()).hexdigest(),
        }

    instrument = make_instrument(symbol)
    bar_type, bars = wrangle_bars(symbol, df, instrument)
    if len(bars) != len(df):
        return {
            "symbol": symbol,
            "instrument_id": instrument_id_str(symbol),
            "ok": False,
            "errors": [f"wrangle count {len(bars)} != source {len(df)}"],
        }

    catalog.write_data([instrument])
    catalog.write_data(bars)

    first_ct = _as_dt(df["CloseTime"][0])
    last_ct = _as_dt(df["CloseTime"][-1])
    return {
        "symbol": symbol,
        "instrument_id": str(instrument.id),
        "bar_type": str(bar_type),
        "kind": SPECS[symbol]["kind"],
        "n_bars": len(bars),
        "first_close_time": _z(first_ct),
        "last_close_time": _z(last_ct),
        "source": str(source_path(symbol).relative_to(REPO)),
        "source_sha256": hashlib.sha256(source_path(symbol).read_bytes()).hexdigest(),
        "volume_field": "TickVolume",
        "ok": True,
    }


def verify_symbol(catalog, rec: dict) -> dict:
    """Round-trip count + first/last ts from catalog."""
    if not rec.get("ok"):
        return {"verified": False, "reason": "ingest failed"}
    from nautilus_trader.model.data import BarType

    bt = BarType.from_str(rec["bar_type"])
    loaded = catalog.bars(bar_types=[str(bt)])
    n = len(loaded)
    if n == 0:
        return {"verified": False, "reason": "zero bars loaded", "n_loaded": 0}
    first_ts = loaded[0].ts_event
    last_ts = loaded[-1].ts_event
    # Compare ISO from rec (ns precision may truncate in iso); compare counts primarily.
    ok = n == rec["n_bars"]
    return {
        "verified": ok,
        "n_loaded": n,
        "n_expected": rec["n_bars"],
        "first_ts_event_ns": first_ts,
        "last_ts_event_ns": last_ts,
    }


def cmd_ingest(symbols: list[str], verify: bool) -> int:
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    ART.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    catalog = ParquetDataCatalog(str(CATALOG_DIR))

    manifest_path = RESULTS / "catalog-ingest.jsonl"
    n_fail = 0
    records: list[dict] = []
    with manifest_path.open("w") as mf:
        for sym in tqdm(symbols, desc="ingest"):
            try:
                rec = ingest_symbol(catalog, sym)
            except Exception as e:  # noqa: BLE001
                rec = {
                    "symbol": sym,
                    "ok": False,
                    "errors": [str(e)[:500]],
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            if verify and rec.get("ok"):
                rec["verify"] = verify_symbol(catalog, rec)
                if not rec["verify"].get("verified"):
                    rec["ok"] = False
            rec["ts"] = datetime.now(timezone.utc).isoformat()
            rec["nautilus_pin"] = NAUTILUS_PIN
            rec["catalog"] = str(CATALOG_DIR.relative_to(REPO))
            mf.write(json.dumps(rec) + "\n")
            mf.flush()
            records.append(rec)
            status = "ok" if rec.get("ok") else "FAIL"
            print(f"  {sym}: {status} n={rec.get('n_bars')} {rec.get('errors') or ''}", flush=True)
            if not rec.get("ok"):
                n_fail += 1

    # Fence over successfully ingested symbols (or all with readable ranges).
    ok_recs = [r for r in records if r.get("ok")]
    if ok_recs:
        write_fence(ok_recs)
    print(f"ingest done: {len(symbols) - n_fail} ok, {n_fail} failed", flush=True)
    print(f"catalog: {CATALOG_DIR}", flush=True)
    return 1 if n_fail else 0


def write_fence(ok_recs: list[dict]) -> Path:
    starts = [datetime.fromisoformat(r["first_close_time"].rstrip("Z")) for r in ok_recs]
    ends = [datetime.fromisoformat(r["last_close_time"].rstrip("Z")) for r in ok_recs]
    start = min(starts)
    end = max(ends)
    span = end - start
    train_end = _floor_day(start + span * (ANALYSIS_FRAC * TRAIN_FRAC))
    holdout_start = _floor_day(start + span * ANALYSIS_FRAC)

    sources = {
        r["symbol"]: {
            "path": r["source"],
            "sha256": r["source_sha256"],
            "n_bars": r["n_bars"],
            "instrument_id": r["instrument_id"],
        }
        for r in ok_recs
    }
    manifest = {
        "schema": "xen-fence-manifest/v1",
        "universe": "ctrader-chapter03",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_start_utc": _z(start),
        "train_end_utc": _z(train_end),
        "holdout_start_utc": _z(holdout_start),
        "data_end_utc": _z(end),
        "split": {
            "analysis_frac": ANALYSIS_FRAC,
            "train_frac_within_analysis": TRAIN_FRAC,
        },
        "source": {
            "catalog": str(CATALOG_DIR.relative_to(REPO)),
            "symbols": sorted(sources.keys()),
            "files": sources,
            "note": "Chapter-03 cTrader 1m timebars; TickVolume as bar volume; "
            "HOLDOUT (holdout_start_utc onward) never queried.",
        },
        "nautilus_pin": NAUTILUS_PIN,
        "instrument_id_convention": "{SYMBOL}.CTrader",
        "note": "Independent of Bybit INFR-011 fence. Holdout obligations on "
        "chapter-03 data remain binding.",
    }
    path = ART / "fence-manifest.json"
    blob = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    path.write_text(blob)
    sha = hashlib.sha256(blob.encode()).hexdigest()
    print(f"fence-manifest.json written (sha256 {sha})")
    for k in ("analysis_start_utc", "train_end_utc", "holdout_start_utc", "data_end_utc"):
        print(f"  {k}: {manifest[k]}")
    (ART / "fence-manifest.sha256").write_text(sha + "\n")
    return path


def cmd_fence_only() -> int:
    """Rebuild fence from existing ingest log (no re-write of catalog)."""
    path = RESULTS / "catalog-ingest.jsonl"
    if not path.exists():
        print("no catalog-ingest.jsonl — run ingest first", file=sys.stderr)
        return 1
    ok_recs = [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip() and json.loads(line).get("ok")
    ]
    if not ok_recs:
        print("no successful ingest rows", file=sys.stderr)
        return 1
    write_fence(ok_recs)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_ing = sub.add_parser("ingest", help="Write instruments + bars into catalog_ctrader")
    p_ing.add_argument(
        "--symbols",
        nargs="+",
        default=list(SOURCES.keys()),
        choices=list(SOURCES.keys()),
    )
    p_ing.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip post-write catalog round-trip (faster; default is verify)",
    )
    sub.add_parser("fence", help="Rebuild fence from ingest log")
    args = ap.parse_args()
    if args.cmd == "fence":
        return cmd_fence_only()
    return cmd_ingest(symbols=args.symbols, verify=not args.no_verify)


if __name__ == "__main__":
    sys.exit(main())
