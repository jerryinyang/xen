#!/usr/bin/env python3
"""INFR-011 collection repair — re-download day-level `error` days and merge.

Why: the EC2 bulk run left 23,450 day-files as `error` (HTTP 403, CDN/IP block)
across 740 symbols while still marking the symbols `ok` — the retry pass only
caught symbol-level failures. Those 403s are transient: the files download fine
from a local IP. Operator approved full local repair 2026-07-16.

Targets: all census symbols except the 5 truly-failed (MYRIA/SFP/TAC/TRIA/UNI —
no data at all) and DATAOLD01USDT (no_bars). The 9 K-cluster symbols are
included (operator admitted them 2026-07-16 — their data is complete and the
'failed both passes' premise was wrong; see admission report).

Per symbol with error days:
  download each error day (stream_pipeline.http_get: retries + dig@8.8.8.8 DNS
  fallback) → stream_pipeline.day_to_bars (identical derivation, POLARS single-
  thread determinism pin inherited via import) → merge into the authoritative
  parquet (staging preferred, else remote-mirror) → unique(OpenTime, keep=last)
  → sort → atomic rewrite IN PLACE → re-run invariants + gap report.

Appends:
  artifacts/patch-manifest.jsonl   (day rows: ok/missing/error + sha256)
  artifacts/symbol-status.jsonl    (new ok rows with patched=True — these become
                                    the latest-ok rows the admission gate reads)
  artifacts/gap-ledger.jsonl       (refreshed rows for patched symbols)

Run:  cd python && uv run python experiments/INFR-011/scripts/patch_missing_days.py \
          [--procs 8] [--workers 3] [--limit N]
Resume-safe: a day already `ok` in patch-manifest.jsonl is skipped; a symbol
whose error days are all resolved is skipped entirely.

EC2 emit-only mode (2026-07-16, operator: downloads must happen on instance
internet, local pull ≈ 1 GB):
  --days-file days.json --patch-dir <dir>
downloads each symbol's listed days and writes ONLY the new bars to
``<dir>/{sym}.parquet`` (no authoritative parquet needed on the box, no merge).
The local merge then runs with ``--from-patch-dir <pulled dir>`` which merges
those patch parquets instead of downloading.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import stream_pipeline as sp  # noqa: E402  (sets POLARS_MAX_THREADS=1 pre-import)

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import polars as pl  # noqa: E402
from tqdm import tqdm  # noqa: E402

INFR = Path(__file__).resolve().parents[1]
ART = INFR / "artifacts"
MIRROR_BARS = INFR / "data" / "remote-mirror" / "bars"
STAGING_BARS = INFR / "data" / "staging" / "bars"
REMOTE_MANIFEST = INFR / "data" / "remote-mirror" / "artifacts" / "checksum-manifest.jsonl"
LOCAL_MANIFEST = ART / "checksum-manifest.jsonl"
PATCH_MANIFEST = ART / "patch-manifest.jsonl"

EXCLUDED = {"MYRIAUSDT", "SFPUSDT", "TACUSDT", "TRIAUSDT", "UNIUSDT", "DATAOLD01USDT"}


def day_rows_last_wins(paths: list[Path]) -> dict[tuple[str, str], dict]:
    rows: dict[tuple[str, str], dict] = {}
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "symbol" in r and "day" in r:
                rows[(r["symbol"], r["day"])] = r
    return rows


def error_days_by_symbol() -> dict[str, list[str]]:
    """(symbol → sorted error days) after overlaying patch-manifest resolutions."""
    rows = day_rows_last_wins([REMOTE_MANIFEST, LOCAL_MANIFEST, PATCH_MANIFEST])
    out: dict[str, list[str]] = {}
    for (sym, day), r in rows.items():
        if sym in EXCLUDED:
            continue
        if r["status"] == "error":
            out.setdefault(sym, []).append(day)
    return {s: sorted(d) for s, d in out.items()}


def bar_path(symbol: str) -> Path | None:
    for base in (STAGING_BARS, MIRROR_BARS):
        p = base / f"{symbol}.parquet"
        if p.exists():
            return p
    return None


def fetch_day(symbol: str, day: str) -> tuple[str, pl.DataFrame | None, dict]:
    url = f"{sp.BASE}{symbol}/{symbol}{day}.csv.gz"
    ts = datetime.now(timezone.utc).isoformat()
    try:
        gz = sp.http_get(url)
        sha = hashlib.sha256(gz).hexdigest()
        try:
            bars = sp.day_to_bars(symbol, day, gz)
        except pl.exceptions.NoDataError:
            bars = pl.DataFrame()  # legitimately empty day-file (no trades printed)
        del gz
        status = "ok" if bars.height > 0 else "empty"
        return day, bars, {"status": status, "symbol": symbol, "day": day,
                           "sha256": sha, "n_bars": bars.height, "ts": ts}
    except FileNotFoundError:
        return day, None, {"status": "missing", "symbol": symbol, "day": day, "ts": ts}
    except Exception as e:  # noqa: BLE001
        return day, None, {"status": "error", "symbol": symbol, "day": day,
                           "error": str(e)[:300], "ts": ts}


def emit_symbol(symbol: str, days: list[str], workers: int, patch_dir: Path) -> dict:
    """EC2 mode: download days → write ONLY the new bars to patch_dir/{sym}.parquet."""
    t0 = time.time()
    out = patch_dir / f"{symbol}.parquet"
    if out.exists():
        return {"symbol": symbol, "status": "skip_existing", "path": str(out)}
    frames: list[pl.DataFrame] = []
    day_recs: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fetch_day, symbol, d) for d in days]
        for fut in as_completed(futs):
            _day, bars, rec = fut.result()
            day_recs.append(rec)
            sp.append_jsonl(PATCH_MANIFEST, rec)
            if bars is not None and bars.height > 0:
                frames.append(bars)
    n_unresolved = sum(1 for r in day_recs if r["status"] == "error")
    if frames:
        merged = (
            pl.concat(frames, how="diagonal_relaxed")
            .unique(subset=["OpenTime"], keep="last")
            .sort("OpenTime")
            .drop("VolumeCheck", strict=False)
        )
        tmp = out.with_suffix(".parquet.tmp")
        merged.write_parquet(tmp, compression="zstd")
        tmp.rename(out)
        n_bars = merged.height
    else:
        n_bars = 0
    rec = {"symbol": symbol, "status": "emitted" if frames else "no_new_bars",
           "n_patch_days": len(days),
           "n_patch_ok": sum(1 for r in day_recs if r["status"] == "ok"),
           "n_patch_unresolved": n_unresolved, "n_bars": n_bars,
           "elapsed_s": round(time.time() - t0, 2),
           "ts": datetime.now(timezone.utc).isoformat()}
    sp.append_jsonl(ART / "patch-emit-status.jsonl", rec)
    return rec


def patch_symbol(symbol: str, days: list[str], workers: int,
                 from_patch_dir: Path | None = None) -> dict:
    t0 = time.time()
    path = bar_path(symbol)
    if path is None:
        rec = {"symbol": symbol, "status": "patch_error", "error": "no authoritative parquet",
               "ts": datetime.now(timezone.utc).isoformat()}
        sp.append_jsonl(sp.SYM_STATUS, rec)
        return rec

    frames: list[pl.DataFrame] = []
    if from_patch_dir is not None:
        # merge a pulled EC2 patch parquet instead of downloading
        pp = from_patch_dir / f"{symbol}.parquet"
        if pp.exists():
            frames.append(pl.read_parquet(pp))
        n_ok = frames[0].height if frames else 0
        n_unresolved = 0 if frames else len(days)
    else:
        day_recs: list[dict] = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(fetch_day, symbol, d) for d in days]
            for fut in as_completed(futs):
                _day, bars, rec = fut.result()
                day_recs.append(rec)
                sp.append_jsonl(PATCH_MANIFEST, rec)
                if bars is not None and bars.height > 0:
                    frames.append(bars)
        n_ok = sum(1 for r in day_recs if r["status"] == "ok")
        # empty (no trades) and missing (404, absent from archive) are resolved
        n_unresolved = sum(1 for r in day_recs if r["status"] == "error")

    try:
        prev = pl.read_parquet(path)
        if frames:
            merged = (
                pl.concat([prev, *frames], how="diagonal_relaxed")
                .unique(subset=["OpenTime"], keep="last")
                .sort("OpenTime")
                .drop("VolumeCheck", strict=False)
            )
            tmp = path.with_suffix(".parquet.tmp")
            merged.write_parquet(tmp, compression="zstd")
            tmp.rename(path)
        else:
            merged = prev

        inv_df = merged.with_columns(pl.col("Volume").alias("VolumeCheck"))
        inv = sp.check_invariants(inv_df)
        gaps = sp.gap_report(symbol, merged)
        sp.append_jsonl(sp.GAP_LEDGER, gaps)
        first_day = str(merged["OpenTime"].min().date())
        last_day = str(merged["OpenTime"].max().date())
        status = "ok" if inv["vol_ok"] and inv["mono_ok"] and inv["ohlc_ok"] else "invariant_fail"
        rec = {
            "symbol": symbol, "status": status, "patched": True,
            "n_patch_days": len(days), "n_patch_ok": n_ok,
            "n_patch_unresolved": n_unresolved,
            "n_days": None, "first_day": first_day, "last_day": last_day,
            "invariants": inv, "gaps": gaps, "path": str(path),
            "bytes": path.stat().st_size,
            "elapsed_s": round(time.time() - t0, 2),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:  # noqa: BLE001
        rec = {"symbol": symbol, "status": "patch_error", "error": str(e)[:500],
               "elapsed_s": round(time.time() - t0, 2),
               "ts": datetime.now(timezone.utc).isoformat()}
    sp.append_jsonl(sp.SYM_STATUS, rec)
    return rec


def _mp_entry(args: tuple) -> dict:
    mode, s, d, workers, extra = args
    if mode == "emit":
        return emit_symbol(s, d, workers, Path(extra))
    return patch_symbol(s, d, workers, Path(extra) if extra else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--symbol", default="")
    ap.add_argument("--days-file", default="", help="json {symbol: [days]} (EC2 mode input)")
    ap.add_argument("--patch-dir", default="", help="EC2 emit-only mode: write patch parquets here")
    ap.add_argument("--from-patch-dir", default="", help="local merge from pulled patch parquets")
    args = ap.parse_args()

    if args.days_file:
        todo = {k: v for k, v in json.loads(Path(args.days_file).read_text()).items()}
    else:
        todo = error_days_by_symbol()
    if args.symbol:
        todo = {args.symbol: todo[args.symbol]}
    items = sorted(todo.items(), key=lambda kv: -len(kv[1]))  # big symbols first
    if args.limit:
        items = items[: args.limit]
    n_days = sum(len(d) for _, d in items)

    mode = "emit" if args.patch_dir else "merge"
    extra = args.patch_dir or args.from_patch_dir
    if args.patch_dir:
        Path(args.patch_dir).mkdir(parents=True, exist_ok=True)
    print(f"patch[{mode}]: {len(items)} symbols, {n_days} error days "
          f"(procs={args.procs} workers={args.workers})", flush=True)

    results = []
    if args.procs > 1:
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.procs, mp_context=ctx) as ex:
            futs = {ex.submit(_mp_entry, (mode, s, d, args.workers, extra)): s
                    for s, d in items}
            for fut in tqdm(as_completed(futs), total=len(items), desc="patch"):
                r = fut.result()
                results.append(r)
                print(f"{r['symbol']}: {r['status']} "
                      f"+{r.get('n_patch_ok', 0)}/{r.get('n_patch_days', 0)} days "
                      f"unresolved={r.get('n_patch_unresolved', '?')} "
                      f"{r.get('elapsed_s')}s", flush=True)
    else:
        for s, d in tqdm(items, desc="patch"):
            results.append(_mp_entry((mode, s, d, args.workers, extra)))

    ok_status = {"ok", "emitted", "no_new_bars", "skip_existing"}
    n_bad = sum(1 for r in results
                if r["status"] not in ok_status or r.get("n_patch_unresolved"))
    print(f"done: {len(results)} symbols, {n_bad} with unresolved days / failures", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
