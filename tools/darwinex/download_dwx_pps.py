#!/usr/bin/env python3
"""Download EXP-095/096 portfolio instruments from Darwinex FTP.

Maps Xen symbols to Darwinex symbols:
  EURUSD → EURUSD    XAUUSD → XAUUSD    USDCHF → USDCHF
  AUDJPY → AUDJPY    EURJPY → EURJPY    GBPJPY → GBPJPY
  USTEC  → NDXm
  US2000 → not available at Darwinex (skipped)

Downloads tick data, aggregates to 1-min OHLC, saves one combined parquet
per symbol to data/timebars/drwx/.

Resumable: tracks completed dates per symbol in a checkpoint file.

Usage:
  DWX_FTP_USER=user DWX_FTP_PASS=pass python download_dwx_pps.py
  DWX_START=2021-06-01 DWX_END=2026-06-21 python download_dwx_pps.py
  python download_dwx_pps.py --symbols EURUSD,XAUUSD
"""

import os
import sys
import json
import gzip
import ssl
import argparse
from io import BytesIO
from ftplib import FTP_TLS, error_temp, error_perm
from pathlib import Path
from datetime import datetime, timedelta, date, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HOST = "tickdata.darwinex.com"

HERE = Path(__file__).parent
ENV_FILE = HERE / ".env"
OUTPUT_DIR = HERE.parent.parent / "data" / "timebars" / "drwx"
CHECKPOINT_FILE = OUTPUT_DIR / ".checkpoint.json"

DWX_SYMBOL_MAP = {
    "EURUSD": "EURUSD",
    "XAUUSD": "XAUUSD",
    "USDCHF": "USDCHF",
    "AUDJPY": "AUDJPY",
    "EURJPY": "EURJPY",
    "GBPJPY": "GBPJPY",
    "USTEC": "NDXm",
}

MAX_WORKERS = int(os.environ.get("DWX_MAX_WORKERS", "8"))


def load_env():
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def get_ftp():
    user = os.environ.get("DWX_FTP_USER")
    pwd = os.environ.get("DWX_FTP_PASS")
    if not user or not pwd:
        print("ERROR: Set DWX_FTP_USER and DWX_FTP_PASS env vars or .env file.")
        sys.exit(1)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = FTP_TLS(HOST, context=ctx)
    ftp.login(user, pwd)
    return ftp


def download_hour(ftp, dwx_symbol, date_str, hour):
    file_name = f"{dwx_symbol}_ASK_{date_str}_{hour:02d}.log.gz"
    remote_path = f"{dwx_symbol}/{file_name}"
    buf = BytesIO()
    try:
        ftp.retrbinary(f"RETR {remote_path}", buf.write)
    except Exception:
        return None
    buf.seek(0)
    with gzip.open(buf) as f:
        lines = [line.strip().decode().split(",") for line in f]
    if not lines:
        return None
    ts_utc = [pd.Timestamp(int(l[0]), unit="ms", tz="UTC") for l in lines]
    ts_naive = [t.tz_localize(None) for t in ts_utc]
    prices = [float(l[1]) for l in lines]
    sizes = [float(l[2]) for l in lines]
    return pd.DataFrame(
        {"price": prices, "size": sizes},
        index=pd.DatetimeIndex(ts_naive, name="Time"),
    )


def download_day(ftp, dwx_symbol, date_str):
    frames = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_to_hour = {
            pool.submit(download_hour, ftp, dwx_symbol, date_str, h): h
            for h in range(24)
        }
        for fut in as_completed(fut_to_hour):
            df = fut.result()
            if df is not None:
                frames.append(df)
    if not frames:
        return None
    return pd.concat(frames).sort_index()


def aggregate_ohlc(df, symbol):
    if df is None or df.empty:
        return None
    ohlc = df["price"].resample("1min").ohlc()
    vol = df["size"].resample("1min").sum().to_frame("TickVolume")
    result = ohlc.join(vol)
    result = result.dropna(subset=["open"])
    result = result.astype({"TickVolume": "int64"})
    result.columns = ["Open", "High", "Low", "Close", "TickVolume"]
    result.index.name = "OpenTime"
    result = result.reset_index()
    result["CloseTime"] = result["OpenTime"] + pd.Timedelta(minutes=1)
    result["Symbol"] = symbol
    return result[["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]]


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2, sort_keys=True)


def date_range(start_str, end_str):
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


SCHEMA = pa.schema([
    pa.field("Symbol", pa.string(), nullable=True),
    pa.field("OpenTime", pa.timestamp("ns"), nullable=False),
    pa.field("CloseTime", pa.timestamp("ns"), nullable=False),
    pa.field("Open", pa.float64(), nullable=False),
    pa.field("High", pa.float64(), nullable=False),
    pa.field("Low", pa.float64(), nullable=False),
    pa.field("Close", pa.float64(), nullable=False),
    pa.field("TickVolume", pa.int64(), nullable=False),
])


def symbol_done(checkpoint, symbol, d):
    return symbol in checkpoint and d.isoformat() in checkpoint[symbol]


def collect_symbol(xen_symbol, dwx_symbol, start_date, end_date, checkpoint, max_days=0):
    print(f"\n=== {xen_symbol} ({dwx_symbol}) ===")
    output_path = OUTPUT_DIR / f"timebars_{xen_symbol.lower()}_{start_date.replace('-', '')}_{end_date.replace('-', '')}_dwx.parquet"

    pending = [d for d in date_range(start_date, end_date)
               if not symbol_done(checkpoint, xen_symbol, d)]
    if max_days > 0:
        pending = pending[:max_days]
    if not pending:
        print(f"  All dates already collected. Skipping.")
        return

    print(f"  {len(pending)} days to download")
    all_bars = []
    last_commit = 0
    consecutive_errors = 0

    for i, d in enumerate(pending):
        date_str = d.isoformat()
        for attempt in range(3):
            try:
                ftp = get_ftp()
                ticks = download_day(ftp, dwx_symbol, date_str)
                ftp.quit()
                consecutive_errors = 0
                break
            except (OSError, error_temp, EOFError) as e:
                ftp.quit() if ftp else None
                consecutive_errors += 1
                if consecutive_errors >= 10:
                    print(f"  Too many connection errors. Stopping.")
                    save_checkpoint(checkpoint)
                    return
                sleep(5 * (attempt + 1))
        else:
            print(f"  {date_str} — connection failed after 3 attempts")
            continue

        bars = None
        if ticks is not None:
            bars = aggregate_ohlc(ticks, xen_symbol)
        n_bars = len(bars) if bars is not None else 0
        print(f"  {date_str} — {n_bars} bars")

        if bars is not None:
            all_bars.append(bars)

        if xen_symbol not in checkpoint:
            checkpoint[xen_symbol] = []
        checkpoint[xen_symbol].append(date_str)
        last_commit += 1
        if last_commit >= 10:
            save_checkpoint(checkpoint)
            last_commit = 0

    save_checkpoint(checkpoint)

    if all_bars:
        combined = pd.concat(all_bars, ignore_index=True)
        combined = combined.sort_values("OpenTime").reset_index(drop=True)
        table = pa.Table.from_pandas(combined, schema=SCHEMA, preserve_index=False)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, output_path)
        n = len(combined)
        span = f"{combined['OpenTime'].min()} → {combined['OpenTime'].max()}"
        print(f"  Saved: {output_path} ({n} bars, {span})")
    else:
        print(f"  No data collected for {xen_symbol}")


def main():
    load_env()

    parser = argparse.ArgumentParser(description="Download PPS instruments from Darwinex FTP")
    parser.add_argument("--symbols", help="Comma-separated symbols to download")
    parser.add_argument("--start", default=os.environ.get("DWX_START", "2021-06-01"),
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=os.environ.get("DWX_END", "2026-06-21"),
                        help="End date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=0,
                        help="Max days per symbol (for testing)")
    args = parser.parse_args()

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = sorted(DWX_SYMBOL_MAP.keys())

    available = [(s, DWX_SYMBOL_MAP[s]) for s in symbols if s in DWX_SYMBOL_MAP]
    missing = [s for s in symbols if s not in DWX_SYMBOL_MAP]
    if missing:
        print(f"Skipped (not at Darwinex): {', '.join(missing)}")
    if not available:
        print("No available symbols to download.")
        sys.exit(1)

    print(f"Darwinex PPS collection: {len(available)} instruments")
    print(f"  Range: {args.start} → {args.end}")
    print(f"  Output: {OUTPUT_DIR}/\n")

    checkpoint = load_checkpoint()

    for xen_symbol, dwx_symbol in available:
        collect_symbol(xen_symbol, dwx_symbol, args.start, args.end, checkpoint, max_days=args.days)

    print(f"\nDone. All files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
