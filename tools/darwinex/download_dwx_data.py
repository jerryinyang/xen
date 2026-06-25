#!/usr/bin/env python3
"""Download tick data from Darwinex FTP, aggregate to 1-min OHLC, save as parquet.

Usage:
    DWX_FTP_USER=your_user DWX_FTP_PASS=your_pass python download_dwx_data.py

Reads env vars or a .env file in the same directory.
"""

import os
import sys
import gzip
import ssl
from io import BytesIO
from ftplib import FTP_TLS
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HOST = "tickdata.darwinex.com"

HERE = Path(__file__).parent
ENV_FILE = HERE / ".env"
PROJECT_DATA = HERE.parent.parent / "data" / "timebars"

SYMBOL = os.environ.get("DWX_SYMBOL", "EURUSD")
DATE = os.environ.get("DWX_DATE", "2024-01-10")
HOURS = list(range(0, 24))

DT_FORMATS = [
    ("%d/%m/%Y", "DD/MM/YYYY"),
    ("%Y-%m-%d", "YYYY-MM-DD"),
]


def find_date_format(date_str):
    from datetime import datetime
    for fmt, label in DT_FORMATS:
        try:
            datetime.strptime(date_str, fmt)
            return fmt, label
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def parse_date(date_str, fmt):
    from datetime import datetime
    return pd.Timestamp(datetime.strptime(date_str, fmt))


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


def download_hour(ftp, symbol, date, hour):
    file_name = f"{symbol}_ASK_{date}_{hour:02d}.log.gz"
    remote_path = f"{symbol}/{file_name}"
    buf = BytesIO()
    try:
        ftp.retrbinary(f"RETR {remote_path}", buf.write)
    except Exception as e:
        print(f"  [SKIP] {remote_path}: {e}")
        return None
    buf.seek(0)
    with gzip.open(buf) as f:
        lines = [line.strip().decode().split(",") for line in f]
    ts_utc = [pd.Timestamp(int(l[0]), unit="ms", tz="UTC") for l in lines]
    ts_naive = [t.tz_localize(None) for t in ts_utc]
    prices = [float(l[1]) for l in lines]
    sizes = [float(l[2]) for l in lines]
    return pd.DataFrame(
        {"price": prices, "size": sizes}, index=pd.DatetimeIndex(ts_naive, name="Time")
    )


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


def main():
    load_env()

    date_fmt, date_label = find_date_format(DATE)
    date_dt = parse_date(DATE, date_fmt)

    print(f"Connecting to {HOST} ...")
    ftp = get_ftp()
    print(f"Connected. Downloading {SYMBOL} on {DATE} ({date_label})")

    frames = []
    for h in HOURS:
        df = download_hour(ftp, SYMBOL, DATE, h)
        if df is not None:
            frames.append(df)
            print(f"  {h:02d}:00 — {len(df)} ticks")

    ftp.quit()

    if not frames:
        print("No data downloaded.")
        sys.exit(1)

    all_ticks = pd.concat(frames)
    all_ticks = all_ticks.sort_index()

    print(f"\nTotal ticks: {len(all_ticks)}")
    print(f"Range: {all_ticks.index[0]} to {all_ticks.index[-1]}")

    bars = aggregate_ohlc(all_ticks, SYMBOL)
    print(f"1-min bars: {len(bars)}")

    symbol_lc = SYMBOL.lower()
    date_str = date_dt.strftime("%Y%m%d")
    out_name = f"timebars_{symbol_lc}_{date_str}_000000_{date_str}_235959_dwx.parquet"
    out_path = PROJECT_DATA / out_name

    schema = pa.schema([
        pa.field("Symbol", pa.string(), nullable=True),
        pa.field("OpenTime", pa.timestamp("ns"), nullable=False),
        pa.field("CloseTime", pa.timestamp("ns"), nullable=False),
        pa.field("Open", pa.float64(), nullable=False),
        pa.field("High", pa.float64(), nullable=False),
        pa.field("Low", pa.float64(), nullable=False),
        pa.field("Close", pa.float64(), nullable=False),
        pa.field("TickVolume", pa.int64(), nullable=False),
    ])
    table = pa.Table.from_pandas(bars, schema=schema, preserve_index=False)
    pq.write_table(table, out_path)

    print(f"\nSaved: {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
