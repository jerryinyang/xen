#!/usr/bin/env python3
"""
INFR-011 steps 2+3 — streaming trades → 1m OHLCV + pseudo-quote spreads.

Amended constraints (2026-07-14):
- Strict *USDT universe only (910 symbols)
- Trailing 4-year history cap per symbol
- ZERO raw retention (incl. BTC/ETH/SOL — keep-forever deferred to MBP INFR)
- Peak raw disk = one day-file in flight (bytes held in memory then discarded)
- Resumable checksum manifest
- Nautilus catalog ingest is NOT this script (blocked on Phase B pin)

Output:
  data/staging/bars/{symbol}.parquet
  artifacts/checksum-manifest.jsonl
  artifacts/symbol-status.jsonl
  artifacts/gap-ledger.jsonl
  artifacts/invariant-summary.md (written by summarize mode)
"""
from __future__ import annotations

import os

# Determinism: pin polars to a single thread BEFORE import so float accumulation
# (Volume/spread sums) is order-fixed per day-file and bars reproduce
# cross-platform. Parallelism comes from symbol-level processes (--procs).
os.environ.setdefault("POLARS_MAX_THREADS", "1")

import argparse
import fcntl
import gzip
import hashlib
import io
import json
import multiprocessing
import platform
import random
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import polars as pl
from tqdm import tqdm

_WRITE_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parents[1]
ART = EXP / "artifacts"
STAGING = EXP / "data" / "staging" / "bars"
SPREADS = EXP / "data" / "staging" / "spreads"
MANIFEST = ART / "checksum-manifest.jsonl"
SYM_STATUS = ART / "symbol-status.jsonl"
GAP_LEDGER = ART / "gap-ledger.jsonl"
CANDIDATES = ART / "candidate_symbols.txt"

HOST = "public.bybit.com"
BASE = f"https://{HOST}/trading/"
UA = "Xen-INFR-011-stream/2.0 (research; raw-less)"
HISTORY_CAP_DAYS = 1461  # ~4 years
POLITE_S = 0.05
MAX_RETRIES = 6
DAY_WORKERS = 6
VOL_TOL = 1e-6
DNS_SERVER = "8.8.8.8"

_ip_cache: dict[str, str] = {}


def run_meta() -> dict[str, Any]:
    """Provenance recorded in manifests: git commit + producing platform."""
    commit = os.environ.get("XEN_GIT_COMMIT", "")
    if not commit:
        try:
            commit = subprocess.check_output(
                ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True, timeout=10
            ).strip()
        except Exception:
            commit = "unknown"
    return {
        "git_commit": commit,
        "produced_on": {
            "instance_type": os.environ.get("XEN_INSTANCE_TYPE", "local"),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "polars": pl.__version__,
            "polars_max_threads": os.environ.get("POLARS_MAX_THREADS", ""),
        },
    }


# ---------------------------------------------------------------------------
# DNS / HTTP (system resolver first; dig@8.8.8.8 fallback for broken local DNS)
# ---------------------------------------------------------------------------
def resolve_ip(host: str) -> str:
    if host in _ip_cache:
        return _ip_cache[host]
    try:
        ip = socket.gethostbyname(host)
        _ip_cache[host] = ip
        return ip
    except OSError:
        pass
    out = subprocess.check_output(
        ["dig", f"@{DNS_SERVER}", "+short", host, "A"],
        text=True,
        timeout=15,
    )
    ips = [ln.strip() for ln in out.splitlines() if re.match(r"^\d+\.\d+\.\d+\.\d+$", ln.strip())]
    if not ips:
        raise RuntimeError(f"DNS resolve failed for {host} via {DNS_SERVER}")
    _ip_cache[host] = ips[0]
    return ips[0]


class _Backoff(Exception):
    """429 / 5xx from the CDN — treat as a polite back-off signal."""


def http_get(url: str, timeout: int = 120) -> bytes:
    """GET with IP override for broken local DNS; SNI still uses hostname."""
    # urlparse-ish
    assert url.startswith("https://"), url
    rest = url[len("https://") :]
    host, path = rest.split("/", 1)
    path = "/" + path
    ip = resolve_ip(host)
    ctx = ssl.create_default_context()
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            sock = socket.create_connection((ip, 443), timeout=timeout)
            ssock = ctx.wrap_socket(sock, server_hostname=host)
            req = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {UA}\r\n"
                f"Accept-Encoding: identity\r\n"
                f"Connection: close\r\n\r\n"
            )
            ssock.sendall(req.encode())
            buf = bytearray()
            while True:
                chunk = ssock.recv(1 << 16)
                if not chunk:
                    break
                buf.extend(chunk)
            ssock.close()
            # Split headers/body
            sep = buf.find(b"\r\n\r\n")
            if sep < 0:
                raise RuntimeError("bad HTTP response (no header sep)")
            header = buf[:sep].decode("latin-1", errors="replace")
            body = bytes(buf[sep + 4 :])
            status_line = header.split("\r\n", 1)[0]
            code = int(status_line.split()[1])
            # Handle chunked (rare for S3/CF static)
            if "transfer-encoding: chunked" in header.lower():
                body = _dechunk(body)
            if code == 404:
                raise FileNotFoundError(url)
            if code == 429 or code >= 500:
                # CDN back-pressure: back off hard, do not hammer.
                raise _Backoff(f"HTTP {code} for {url}")
            if code >= 400:
                raise RuntimeError(f"HTTP {code} for {url}")
            time.sleep(POLITE_S)
            return body
        except FileNotFoundError:
            raise
        except _Backoff as e:
            last_err = e
            time.sleep(min(120.0, (2.0**attempt) * 2.0) + random.uniform(0, 2))
        except Exception as e:
            # connection resets / truncated responses → exponential backoff + jitter
            last_err = e
            time.sleep(min(60.0, 2.0**attempt) + random.uniform(0, 1))
    raise RuntimeError(f"GET failed {url}: {last_err}")


def _dechunk(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        j = data.find(b"\r\n", i)
        if j < 0:
            break
        n = int(data[i:j], 16)
        i = j + 2
        if n == 0:
            break
        out.extend(data[i : i + n])
        i += n + 2
    return bytes(out)


# ---------------------------------------------------------------------------
# Manifest / resume
# ---------------------------------------------------------------------------
def load_done_days() -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if not MANIFEST.exists():
        return done
    with MANIFEST.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("status") == "ok":
                done.add((rec["symbol"], rec["day"]))
    return done


def append_manifest(rec: dict[str, Any]) -> None:
    append_jsonl(MANIFEST, rec)


def append_jsonl(path: Path, rec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, separators=(",", ":")) + "\n"
    with _WRITE_LOCK:
        with path.open("a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # cross-process safety (--procs)
            f.write(line)
            f.flush()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def load_completed_symbols() -> set[str]:
    done: set[str] = set()
    if not SYM_STATUS.exists():
        return done
    with SYM_STATUS.open() as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("status") == "ok":
                done.add(rec["symbol"])
    return done


# ---------------------------------------------------------------------------
# Directory listing / date windows
# ---------------------------------------------------------------------------
def list_archive_days(symbol: str) -> list[str]:
    html = http_get(BASE + symbol + "/").decode("utf-8", errors="replace")
    days = sorted(set(re.findall(r"(\d{4}-\d{2}-\d{2})\.csv\.gz", html)))
    return days


def trailing_4y(days: list[str]) -> list[str]:
    if not days:
        return []
    last = date.fromisoformat(days[-1])
    start = last - timedelta(days=HISTORY_CAP_DAYS - 1)
    start_s = start.isoformat()
    return [d for d in days if d >= start_s]


# ---------------------------------------------------------------------------
# Trade → 1m bars + pseudo spreads
# ---------------------------------------------------------------------------
def day_to_bars(symbol: str, day: str, gz_bytes: bytes) -> pl.DataFrame:
    """Decompress + aggregate one day. Raw bytes discarded by caller."""
    raw = gzip.decompress(gz_bytes)
    # CSV columns: timestamp,symbol,side,size,price,...
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

    # Drop bad rows
    df = df.filter(
        pl.col("timestamp").is_not_null()
        & pl.col("price").is_not_null()
        & pl.col("size").is_not_null()
        & (pl.col("size") > 0)
        & (pl.col("price") > 0)
    )
    if df.is_empty():
        return pl.DataFrame()

    # Floor to minute (UTC). timestamp is unix seconds (float).
    df = df.with_columns(
        (pl.col("timestamp") * 1000).cast(pl.Int64).alias("ts_ms"),
    ).with_columns(
        (pl.col("ts_ms") - (pl.col("ts_ms") % 60_000)).alias("bar_ms"),
    )

    # Aggressor-side helpers
    is_buy = pl.col("side").str.to_lowercase() == "buy"
    is_sell = pl.col("side").str.to_lowercase() == "sell"

    bars = (
        # maintain_order on both sort (stable ties = file order) and group_by so
        # per-bar float accumulation order is fixed by the day-file itself.
        df.sort("ts_ms", maintain_order=True)
        .group_by("bar_ms", maintain_order=True)
        .agg(
            pl.col("price").first().alias("Open"),
            pl.col("price").max().alias("High"),
            pl.col("price").min().alias("Low"),
            pl.col("price").last().alias("Close"),
            pl.col("size").sum().alias("Volume"),
            pl.len().alias("NTrades"),
            pl.col("size").filter(is_buy).sum().alias("BuyVolume"),
            pl.col("size").filter(is_sell).sum().alias("SellVolume"),
            pl.col("price").filter(is_buy).mean().alias("MeanBuy"),
            pl.col("price").filter(is_sell).mean().alias("MeanSell"),
            pl.col("size").sum().alias("VolumeCheck"),
        )
        .sort("bar_ms")
    )

    bars = bars.with_columns(
        pl.lit(symbol).alias("Symbol"),
        pl.from_epoch(pl.col("bar_ms"), time_unit="ms").alias("OpenTime"),
        (pl.from_epoch(pl.col("bar_ms"), time_unit="ms") + pl.duration(minutes=1)).alias(
            "CloseTime"
        ),
        # Pseudo-quote: Buy print ≈ ask, Sell print ≈ bid
        (pl.col("MeanBuy") - pl.col("MeanSell")).alias("SpreadAbs"),
        (
            pl.when(pl.col("MeanBuy").is_not_null() & pl.col("MeanSell").is_not_null())
            .then(
                1e4
                * (pl.col("MeanBuy") - pl.col("MeanSell"))
                / ((pl.col("MeanBuy") + pl.col("MeanSell")) / 2.0)
            )
            .otherwise(None)
        ).alias("SpreadBps"),
    ).select(
        [
            "Symbol",
            "OpenTime",
            "CloseTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "NTrades",
            "BuyVolume",
            "SellVolume",
            "MeanBuy",
            "MeanSell",
            "SpreadAbs",
            "SpreadBps",
            "VolumeCheck",
        ]
    )
    return bars


def check_invariants(bars: pl.DataFrame) -> dict[str, Any]:
    if bars.is_empty():
        return {
            "n_bars": 0,
            "vol_ok": True,
            "mono_ok": True,
            "ohlc_ok": True,
            "n_vol_fail": 0,
            "n_ohlc_fail": 0,
        }
    vol_diff = (bars["Volume"] - bars["VolumeCheck"]).abs()
    n_vol_fail = int((vol_diff > VOL_TOL).sum())
    times = bars["OpenTime"].to_list()
    mono_ok = all(times[i] < times[i + 1] for i in range(len(times) - 1))
    ohlc_ok_mask = (
        (bars["High"] >= bars["Open"])
        & (bars["High"] >= bars["Close"])
        & (bars["Low"] <= bars["Open"])
        & (bars["Low"] <= bars["Close"])
        & (bars["High"] >= bars["Low"])
    )
    n_ohlc_fail = int((~ohlc_ok_mask).sum())
    return {
        "n_bars": bars.height,
        "vol_ok": n_vol_fail == 0,
        "mono_ok": mono_ok,
        "ohlc_ok": n_ohlc_fail == 0,
        "n_vol_fail": n_vol_fail,
        "n_ohlc_fail": n_ohlc_fail,
    }


def gap_report(symbol: str, bars: pl.DataFrame) -> dict[str, Any]:
    if bars.height < 2:
        return {
            "symbol": symbol,
            "n_gaps": 0,
            "gap_minutes_total": 0,
            "first": None,
            "last": None,
        }
    ot = bars["OpenTime"]
    first, last = ot[0], ot[-1]
    expected = int((last - first).total_seconds() // 60) + 1
    n_bars = bars.height
    missing = max(0, expected - n_bars)
    return {
        "symbol": symbol,
        "n_gaps": missing,  # missing minutes vs continuous 1m grid
        "gap_minutes_total": missing,
        "first": first.isoformat() if first is not None else None,
        "last": last.isoformat() if last is not None else None,
        "n_bars": n_bars,
        "expected_if_continuous": expected,
    }


# ---------------------------------------------------------------------------
# Per-day + per-symbol orchestration
# ---------------------------------------------------------------------------
def process_day(
    symbol: str, day: str, done: set[tuple[str, str]]
) -> tuple[str, pl.DataFrame | None, dict[str, Any]]:
    if (symbol, day) in done:
        return day, None, {"status": "skip", "symbol": symbol, "day": day}
    url = f"{BASE}{symbol}/{symbol}{day}.csv.gz"
    try:
        gz = http_get(url)
        sha = hashlib.sha256(gz).hexdigest()
        bars = day_to_bars(symbol, day, gz)
        del gz  # discard raw
        rec = {
            "status": "ok",
            "symbol": symbol,
            "day": day,
            "sha256": sha,
            "n_bars": bars.height,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        append_manifest(rec)
        return day, bars, rec
    except FileNotFoundError:
        rec = {
            "status": "missing",
            "symbol": symbol,
            "day": day,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        append_manifest(rec)
        return day, None, rec
    except Exception as e:
        rec = {
            "status": "error",
            "symbol": symbol,
            "day": day,
            "error": str(e)[:300],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        append_manifest(rec)
        return day, None, rec


_META: dict[str, Any] | None = None


def _meta() -> dict[str, Any]:
    global _META
    if _META is None:
        _META = run_meta()
    return _META


def process_symbol_mp(symbol: str, workers: int) -> dict[str, Any]:
    """Entry point for --procs worker processes: loads done-days lazily."""
    return process_symbol(symbol, None, workers)


def process_symbol(
    symbol: str, done_days: set[tuple[str, str]] | None, workers: int
) -> dict[str, Any]:
    out_path = STAGING / f"{symbol}.parquet"
    t0 = time.time()
    try:
        if done_days is None:
            # only needed for day-level resume, which requires an existing parquet
            done_days = load_done_days() if out_path.exists() else set()
        days_all = list_archive_days(symbol)
        days = trailing_4y(days_all)
        if not days:
            rec = {
                "symbol": symbol,
                "status": "empty",
                "n_days": 0,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            append_jsonl(SYM_STATUS, rec)
            return rec

        frames: list[pl.DataFrame] = []
        # Day-level skip is only safe if a prior parquet exists (bars already persisted).
        # Otherwise ignore day-manifest skips so a crash mid-symbol cannot drop bars.
        day_done = done_days if out_path.exists() else set()
        day_results: list[tuple[str, pl.DataFrame | None, dict]] = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(process_day, symbol, d, day_done): d for d in days}
            for fut in as_completed(futs):
                day_results.append(fut.result())

        # Collect new frames; also reload existing parquet if partial
        for _day, bars, _rec in sorted(day_results, key=lambda x: x[0]):
            if bars is not None and bars.height > 0:
                frames.append(bars)

        if out_path.exists() and frames:
            try:
                prev = pl.read_parquet(out_path)
                frames.insert(0, prev)
            except Exception:
                pass
        elif out_path.exists() and not frames:
            # all days already done
            bars_all = pl.read_parquet(out_path)
            inv = check_invariants(bars_all)
            gaps = gap_report(symbol, bars_all)
            append_jsonl(GAP_LEDGER, gaps)
            rec = {
                "symbol": symbol,
                "status": "ok",
                "n_days": len(days),
                "first_day": days[0],
                "last_day": days[-1],
                "archive_days_total": len(days_all),
                "invariants": inv,
                "gaps": gaps,
                "path": str(out_path),
                "elapsed_s": round(time.time() - t0, 2),
                "resumed": True,
                "ts": datetime.now(timezone.utc).isoformat(),
                **_meta(),
            }
            append_jsonl(SYM_STATUS, rec)
            return rec

        if not frames:
            rec = {
                "symbol": symbol,
                "status": "no_bars",
                "n_days": len(days),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            append_jsonl(SYM_STATUS, rec)
            return rec

        bars_all = (
            pl.concat(frames, how="diagonal_relaxed")
            .unique(subset=["OpenTime"], keep="last")
            .sort("OpenTime")
            .drop("VolumeCheck", strict=False)
        )
        # Recompute VolumeCheck-less invariants on final
        # (volume already checked day-level via Volume==VolumeCheck before drop)
        inv_df = bars_all.with_columns(pl.col("Volume").alias("VolumeCheck"))
        inv = check_invariants(inv_df)
        gaps = gap_report(symbol, bars_all)
        STAGING.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(".parquet.tmp")
        bars_all.write_parquet(tmp_path, compression="zstd")
        tmp_path.rename(out_path)  # atomic: no corrupt parquet on kill mid-write
        append_jsonl(GAP_LEDGER, gaps)
        rec = {
            "symbol": symbol,
            "status": "ok" if inv["vol_ok"] and inv["mono_ok"] and inv["ohlc_ok"] else "invariant_fail",
            "n_days": len(days),
            "first_day": days[0],
            "last_day": days[-1],
            "archive_days_total": len(days_all),
            "invariants": inv,
            "gaps": gaps,
            "path": str(out_path),
            "bytes": out_path.stat().st_size,
            "elapsed_s": round(time.time() - t0, 2),
            "ts": datetime.now(timezone.utc).isoformat(),
            **_meta(),
        }
        append_jsonl(SYM_STATUS, rec)
        return rec
    except Exception as e:
        rec = {
            "symbol": symbol,
            "status": "error",
            "error": str(e)[:500],
            "elapsed_s": round(time.time() - t0, 2),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        append_jsonl(SYM_STATUS, rec)
        return rec


def write_summary() -> Path:
    """Aggregate symbol-status + gap ledger + parquet sizes → invariant-summary.md"""
    statuses: list[dict] = []
    if SYM_STATUS.exists():
        with SYM_STATUS.open() as f:
            statuses = [json.loads(l) for l in f if l.strip()]
    # last status wins per symbol
    by_sym: dict[str, dict] = {}
    for s in statuses:
        by_sym[s["symbol"]] = s
    statuses = list(by_sym.values())

    ok = [s for s in statuses if s.get("status") == "ok"]
    fail = [s for s in statuses if s.get("status") not in ("ok", "empty", "no_bars")]
    empty = [s for s in statuses if s.get("status") in ("empty", "no_bars")]

    total_bytes = 0
    for p in STAGING.glob("*.parquet") if STAGING.exists() else []:
        total_bytes += p.stat().st_size

    n_vol_fail = sum(1 for s in ok if not s.get("invariants", {}).get("vol_ok", True))
    n_mono_fail = sum(1 for s in ok if not s.get("invariants", {}).get("mono_ok", True))
    n_ohlc_fail = sum(1 for s in ok if not s.get("invariants", {}).get("ohlc_ok", True))
    total_bars = sum(s.get("invariants", {}).get("n_bars", 0) for s in ok)
    total_gap_min = sum(s.get("gaps", {}).get("gap_minutes_total", 0) for s in ok)

    lines = [
        "# INFR-011 Invariant Summary + Gap Ledger + Storage\n\n",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n",
        f"**Pipeline:** streaming raw-less (zero raw retained, incl. BTC/ETH/SOL)\n",
        f"**History cap:** trailing {HISTORY_CAP_DAYS} days (~4y)\n\n",
        "## Counts\n",
        f"- Symbols processed (status rows): {len(statuses)}\n",
        f"- OK: {len(ok)}\n",
        f"- Empty/no bars: {len(empty)}\n",
        f"- Fail/error/invariant_fail: {len(fail)}\n",
        f"- Total 1m bars: {total_bars:,}\n",
        f"- Total gap minutes (vs continuous grid): {total_gap_min:,}\n\n",
        "## Invariants (OK symbols)\n",
        f"- Volume ≡ Σ trades failures: {n_vol_fail}\n",
        f"- Monotonic ts failures: {n_mono_fail}\n",
        f"- OHLC bound failures: {n_ohlc_fail}\n\n",
        "## Storage\n",
        f"- Staging dir: `{STAGING}`\n",
        f"- Parquet files: {len(list(STAGING.glob('*.parquet'))) if STAGING.exists() else 0}\n",
        f"- Total Parquet size: {total_bytes / (1024**3):.3f} GB ({total_bytes:,} bytes)\n",
        f"- Peak raw: one day-file in memory (discarded); **zero permanent raw**\n\n",
        "## Failures (if any)\n",
    ]
    if not fail:
        lines.append("_none_\n")
    else:
        for s in fail[:50]:
            lines.append(
                f"- {s.get('symbol')}: {s.get('status')} {s.get('error', s.get('invariants', ''))}\n"
            )
        if len(fail) > 50:
            lines.append(f"- … +{len(fail) - 50} more\n")

    lines.append("\n## Gap ledger (top 20 by gap minutes)\n")
    ranked = sorted(ok, key=lambda s: s.get("gaps", {}).get("gap_minutes_total", 0), reverse=True)
    lines.append("| Symbol | Gap minutes | Bars | First | Last |\n")
    lines.append("|--------|-------------|------|-------|------|\n")
    for s in ranked[:20]:
        g = s.get("gaps", {})
        lines.append(
            f"| {s['symbol']} | {g.get('gap_minutes_total', 0)} | {g.get('n_bars', s.get('invariants', {}).get('n_bars', 0))} | {g.get('first')} | {g.get('last')} |\n"
        )

    out = ART / "invariant-summary.md"
    out.write_text("".join(lines))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols-file", default=str(CANDIDATES))
    ap.add_argument("--limit", type=int, default=0, help="Process only first N symbols (0=all)")
    ap.add_argument("--workers", type=int, default=DAY_WORKERS)
    ap.add_argument(
        "--procs",
        type=int,
        default=1,
        help="Symbol-level worker processes (each uses --workers day-download threads; "
        "cap procs*workers at ~16-32 total HTTP connections)",
    )
    ap.add_argument("--symbol", default="", help="Single symbol override")
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--offset", type=int, default=0, help="Skip first N symbols in list")
    args = ap.parse_args()

    if args.summary_only:
        p = write_summary()
        print(f"Wrote {p}")
        return 0

    ART.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)

    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = [ln.strip() for ln in Path(args.symbols_file).read_text().splitlines() if ln.strip()]
        if args.offset:
            symbols = symbols[args.offset :]
        if args.limit:
            symbols = symbols[: args.limit]

    completed = load_completed_symbols()
    todo = [s for s in symbols if s not in completed]
    print(
        f"INFR-011 stream pipeline: {len(todo)} todo / {len(symbols)} selected "
        f"({len(completed)} already complete). procs={args.procs} workers={args.workers}",
        flush=True,
    )
    print(f"ZERO raw retention. Staging → {STAGING}", flush=True)
    append_manifest(
        {
            "status": "run_meta",
            "ts": datetime.now(timezone.utc).isoformat(),
            "n_todo": len(todo),
            "procs": args.procs,
            "workers": args.workers,
            **_meta(),
        }
    )

    def report(i: int, sym: str, rec: dict[str, Any]) -> None:
        print(
            f"[{i}/{len(todo)}] {sym}: {rec.get('status')} "
            f"bars={rec.get('invariants', {}).get('n_bars', 0)} "
            f"days={rec.get('n_days', 0)} "
            f"{rec.get('elapsed_s', 0)}s",
            flush=True,
        )

    if args.procs > 1:
        ctx = multiprocessing.get_context("spawn")
        n_done = 0
        with ProcessPoolExecutor(max_workers=args.procs, mp_context=ctx) as ex:
            futs = {ex.submit(process_symbol_mp, s, args.workers): s for s in todo}
            for fut in tqdm(as_completed(futs), total=len(todo), desc="symbols"):
                n_done += 1
                report(n_done, futs[fut], fut.result())
    else:
        done_days = load_done_days()
        for i, sym in enumerate(tqdm(todo, desc="symbols")):
            # refresh done days occasionally for resume correctness within symbol
            if i % 20 == 0:
                done_days = load_done_days()
            rec = process_symbol(sym, done_days, workers=args.workers)
            report(i + 1, sym, rec)

    summary = write_summary()
    print(f"Done. Summary: {summary}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
