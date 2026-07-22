#!/usr/bin/env python3
"""
INFR-011 (2+3) Streaming downloader + in-stream derivation (amended 2026-07-14).

Key rules:
- Streaming/raw-less: download → decompress in-stream → 1m OHLCV + pseudo spreads → Parquet staging → discard. One file in flight.
- 4-year trailing cap per symbol.
- Resumable + checksum manifest required.
- Keep-forever raw: only BTCUSDT/ETHUSDT/SOLUSDT.
- Nautilus at catalog ingest only.
- Bulk approved only after corrected 910 USDT-only census.

SKELETON — implement streaming path; do not persist raw except the exception.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime
import urllib.request

ROOT = "https://public.bybit.com/trading/"
OUT_ROOT = Path("data/bybit_trades_raw")  # transient; final catalog elsewhere
MANIFEST = Path("python/experiments/INFR-011/artifacts/checksum-manifest.json")

KEEP_FOREVER = {"BTCUSDT", "ETHUSDT", "SOLUSDT"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def download_one(symbol: str, ymd: str, dest: Path, polite: float = 0.3) -> dict:
    url = f"{ROOT}{symbol}/{symbol}{ymd}.csv.gz"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Xen-INFR-011-scraper/0.1"})
        with urllib.request.urlopen(req, timeout=120) as r, dest.open("wb") as f:
            f.write(r.read())
        cs = sha256_file(dest)
        time.sleep(polite)
        return {"ok": True, "checksum": cs, "path": str(dest)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="python/experiments/INFR-011/artifacts/candidate_symbols.txt")
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--dry-run", action="store_true", help="List work only; no network")
    ap.add_argument("--limit", type=int, default=0, help="Limit symbols for test (0=all)")
    args = ap.parse_args()

    syms = Path(args.symbols).read_text().splitlines()
    if args.limit:
        syms = syms[:args.limit]
    print(f"Scraper skeleton — {len(syms)} symbols (DRY={args.dry_run})")
    print("GATE: Do not execute bulk until operator approval post-census.")
    # TODO: load prior manifest, compute missing (symbol, day) pairs, download, update manifest atomically.
    # After all for a symbol: optionally trigger derive step per symbol.
    print("Skeleton complete. Implement resumable loop + manifest I/O before first real run.")

if __name__ == "__main__":
    main()