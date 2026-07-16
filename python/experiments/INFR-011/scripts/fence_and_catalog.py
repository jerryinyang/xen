#!/usr/bin/env python3
"""INFR-011 A6 + A4 — global calendar fence + ParquetDataCatalog ingest.

Subcommands
-----------
``fence``   A6: compute the global calendar fence from the ADMITTED range in
            ``artifacts/admission-ledger.jsonl`` and write the hash-pinned
            ``artifacts/fence-manifest.json`` (absolute dates, nested 70/30).
``ingest``  A4: instruments (CryptoPerpetual, specs from
            ``artifacts/instrument-specs.json``) + 1m Bar objects into the
            ``ParquetDataCatalog`` at ``data/catalog/`` under pin
            nautilus_trader==1.230.0. InstrumentId ``{sym}-LINEAR.BYBIT``.

Notes
-----
- Engine stays costless (Xen convention): instrument maker/taker fees = 0;
  costs are analyst-injected at analysis time (`xen.evaluation`).
- Bar ``ts_event = ts_init = CloseTime`` (bar confirmed at close; decisions at
  next open use ≤ t-1 bars).
- Pseudo-quote spread series (SpreadAbs/SpreadBps/MeanBuy/MeanSell) are NOT
  Nautilus Bar fields; they stay in the staging/mirror bar parquets, which are
  retained as the T1 spread source for analyst-side cost injection.
- SPEC_INCOMPLETE symbols are ingested with encoding precision inferred from
  observed decimals (NOT a contract-spec claim — return-level reads only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

INFR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
assert (REPO / ".git").exists(), f"repo root miscomputed: {REPO}"
ART = INFR / "artifacts"
LEDGER = ART / "admission-ledger.jsonl"
SPECS = ART / "instrument-specs.json"
FENCE = ART / "fence-manifest.json"
CATALOG_DIR = REPO / "data" / "catalog"
MIRROR_BARS = INFR / "data" / "remote-mirror" / "bars"
STAGING_BARS = INFR / "data" / "staging" / "bars"

ANALYSIS_FRAC = 0.70   # first 70% of calendar span = analysis set (TRAIN+TEST)
TRAIN_FRAC = 0.70      # first 70% of the analysis set = TRAIN
NAUTILUS_PIN = "1.230.0"
READABLE = ("ADMITTED", "SPEC_INCOMPLETE")


def load_ledger() -> list[dict]:
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def bar_path(symbol: str) -> Path:
    p = STAGING_BARS / f"{symbol}.parquet"
    return p if p.exists() else MIRROR_BARS / f"{symbol}.parquet"


# --------------------------------------------------------------------------- A6 fence

def cmd_fence() -> int:
    rows = [r for r in load_ledger() if r.get("admission") in READABLE]
    if not rows:
        print("no admitted rows — run admission_gate.py first", file=sys.stderr)
        return 1
    start = min(datetime.fromisoformat(r["first_bar"]) for r in rows)
    end = max(datetime.fromisoformat(r["last_bar"]) for r in rows)
    span = end - start
    # Floor to whole UTC days: clean absolute calendar dates, conservative
    # (holdout starts strictly no later than the exact 70% point).
    train_end = _floor_day(start + span * (ANALYSIS_FRAC * TRAIN_FRAC))
    holdout_start = _floor_day(start + span * ANALYSIS_FRAC)

    ledger_sha = hashlib.sha256(LEDGER.read_bytes()).hexdigest()
    manifest = {
        "schema": "xen-fence-manifest/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_start_utc": _z(start),
        "train_end_utc": _z(train_end),
        "holdout_start_utc": _z(holdout_start),
        "data_end_utc": _z(end),
        "split": {"analysis_frac": ANALYSIS_FRAC, "train_frac_within_analysis": TRAIN_FRAC},
        "source": {
            "admission_ledger": str(LEDGER.relative_to(REPO)),
            "admission_ledger_sha256": ledger_sha,
            "n_readable_symbols": len(rows),
        },
        "nautilus_pin": NAUTILUS_PIN,
        "note": "HOLDOUT (holdout_start_utc onward) is never queried; both "
                "lifetime shots are governance events. Reads go through "
                "xen.nautilus.catalog_fence.fenced_bar_query.",
    }
    blob = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    FENCE.write_text(blob)
    sha = hashlib.sha256(blob.encode()).hexdigest()
    print(f"fence-manifest.json written (sha256 {sha})")
    for k in ("analysis_start_utc", "train_end_utc", "holdout_start_utc", "data_end_utc"):
        print(f"  {k}: {manifest[k]}")
    return 0


def _floor_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _z(dt: datetime) -> str:
    return dt.replace(tzinfo=None).isoformat() + "Z"


# --------------------------------------------------------------------------- A4 ingest

def _currency(code: str):
    from nautilus_trader.model.currencies import USDT
    from nautilus_trader.model.objects import Currency
    from nautilus_trader.core.rust.model import CurrencyType

    if code == "USDT":
        return USDT
    return Currency(code=code, precision=8, iso4217=0, name=code,
                    currency_type=CurrencyType.CRYPTO)


def _precision_of(inc: float) -> int:
    s = f"{inc:.10f}".rstrip("0")
    return max(0, len(s.split(".")[1])) if "." in s else 0


def _infer_encoding_precision(df: pl.DataFrame) -> tuple[float, float]:
    """Fallback tick/lot for SPEC_INCOMPLETE: smallest observed decimal step."""
    def dec(col: str) -> int:
        vals = df[col].drop_nulls().head(50_000).to_list()
        d = 0
        for v in vals:
            s = f"{v:.10f}".rstrip("0")
            if "." in s:
                d = max(d, len(s.split(".")[1]))
        return min(d, 9)
    return 10 ** -dec("Close"), 10 ** -dec("Volume")


def make_instrument(symbol: str, spec: dict | None, df: pl.DataFrame):
    from nautilus_trader.model.identifiers import InstrumentId, Symbol
    from nautilus_trader.model.instruments import CryptoPerpetual
    from nautilus_trader.model.objects import Price, Quantity

    from xen.nautilus.instrument_ids import archive_symbol_to_instrument_id_str

    if spec is not None:
        tick, lot = float(spec["tick_size"]), float(spec["lot_step"])
    else:
        tick, lot = _infer_encoding_precision(df)

    base = symbol[: -len("USDT")]
    iid = InstrumentId.from_str(archive_symbol_to_instrument_id_str(symbol))
    pp, sp = _precision_of(tick), _precision_of(lot)
    return CryptoPerpetual(
        instrument_id=iid,
        raw_symbol=Symbol(symbol),
        base_currency=_currency(base),
        quote_currency=_currency("USDT"),
        settlement_currency=_currency("USDT"),
        is_inverse=False,
        price_precision=pp,
        size_precision=sp,
        price_increment=Price(tick, pp),
        size_increment=Quantity(lot, sp),
        margin_init=0,
        margin_maint=0,
        maker_fee=0,      # engine costless — costs analyst-injected (xen convention)
        taker_fee=0,
        ts_event=0,
        ts_init=0,
    )


def ingest_symbol(catalog, symbol: str, spec: dict | None) -> dict:
    from nautilus_trader.model.data import BarType
    from nautilus_trader.persistence.wranglers import BarDataWrangler

    df = pl.read_parquet(
        bar_path(symbol),
        columns=["OpenTime", "CloseTime", "Open", "High", "Low", "Close", "Volume"],
    )
    instrument = make_instrument(symbol, spec, df)
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

    pdf = (
        df.select(
            timestamp=pl.col("CloseTime"),
            open=pl.col("Open"), high=pl.col("High"), low=pl.col("Low"),
            close=pl.col("Close"), volume=pl.col("Volume"),
        )
        .to_pandas()
        .set_index("timestamp")
    )
    # Cython wrangler needs writable buffers; polars→pandas is zero-copy
    # read-only and pandas .copy() preserves the read-only flag.
    for col in pdf.columns:
        pdf[col] = np.array(pdf[col].to_numpy(), copy=True)
    bars = BarDataWrangler(bar_type, instrument).process(pdf)
    catalog.write_data([instrument])
    catalog.write_data(bars)
    return {"symbol": symbol, "n_bars": len(bars), "bar_type": str(bar_type),
            "spec_source": (spec or {}).get("source", "ENCODING_ONLY")}


def cmd_ingest(resume: bool, limit: int) -> int:
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    specs = json.loads(SPECS.read_text())["specs"]
    rows = [r for r in load_ledger() if r.get("admission") in READABLE]
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    catalog = ParquetDataCatalog(str(CATALOG_DIR))

    done: set[str] = set()
    manifest_path = ART / "catalog-ingest.jsonl"
    if resume and manifest_path.exists():
        done = {json.loads(l)["symbol"] for l in manifest_path.read_text().splitlines()
                if l.strip()}
    todo = [r for r in rows if r["symbol"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"ingest: {len(todo)} todo / {len(rows)} readable ({len(done)} done)", flush=True)

    n_fail = 0
    with manifest_path.open("a") as mf:
        for r in tqdm(todo, desc="ingest"):
            sym = r["symbol"]
            try:
                rec = ingest_symbol(catalog, sym, specs.get(sym))
                rec["ts"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:  # noqa: BLE001
                rec = {"symbol": sym, "error": str(e)[:300],
                       "ts": datetime.now(timezone.utc).isoformat()}
                n_fail += 1
            mf.write(json.dumps(rec) + "\n")
            mf.flush()
    print(f"ingest done: {len(todo) - n_fail} ok, {n_fail} failed", flush=True)
    return 1 if n_fail else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fence")
    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("--no-resume", action="store_true")
    p_ing.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if args.cmd == "fence":
        return cmd_fence()
    return cmd_ingest(resume=not args.no_resume, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
