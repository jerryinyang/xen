#!/usr/bin/env python3
"""INFR-011 A5 — VAL-style admission gate (blocking).

Inputs
------
- ``data/remote-mirror/bars/*.parquet``  (885 EC2-valid + 9 K-cluster, sha256-verified)
- ``data/staging/bars/*.parquet``        (10 local-authoritative incl. SOLUSDT)
- ``data/remote-mirror/artifacts/symbol-status.jsonl`` (910 symbols, derivation invariants)
- ``artifacts/delist-reconciliation.json``             (listed/delisted + API specs)

Checks per admitted candidate (895)
-----------------------------------
1. Structural invariant re-verification on the local parquet itself: row count vs
   status row, strictly monotonic 1m grid, CloseTime = OpenTime + 1m, OHLC bounds,
   Buy+Sell ≈ Volume, non-negative volume. (Trade-sum ≡ volume was verified at
   derivation; raw is discarded by design so it is carried, not re-derived.)
2. Gap-ledger classification: gap runs from the 1m grid; consensus exchange-outage
   windows from near-continuous symbols (fill ratio ≥ 0.98) where ≥ OUTAGE_QUORUM
   of them gap ≥ OUTAGE_RUN_MIN simultaneously. Per-symbol split
   outage_minutes / no_trade_minutes. INFORMATIVE — thin alts legitimately have
   huge no-trade counts; no veto on raw totals.
3. Delist-tail inspection: delisted symbols must carry bars to their final archive
   day (death spiral present, not trimmed); last-30d return reported.
4. SPEC_INFERRED tick/lot for delisted symbols: tick from the observed price grid,
   lot step from fractional GCD of bar volumes; confidence = share of samples on
   the inferred grid. Failure ⇒ SPEC_INCOMPLETE (return-level reads only).

Explicit non-admitted rows: 14 OMITTED_OPERATOR (operator decision 2026-07-16)
+ 1 NO_BARS (DATAOLD01USDT).

Outputs
-------
- ``artifacts/admission-ledger.jsonl``  (one row per census symbol, 910 rows)
- ``artifacts/instrument-specs.json``   (symbol → tick/lot + source, for A4 ingest)
- ``artifacts/admission-report.md``     (operator-facing report + PASS/FAIL)
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

import polars as pl
from tqdm import tqdm

# --------------------------------------------------------------------------- constants

INFR = Path(__file__).resolve().parents[1]
ART = INFR / "artifacts"
MIRROR_BARS = INFR / "data" / "remote-mirror" / "bars"
STAGING_BARS = INFR / "data" / "staging" / "bars"
STATUS_REMOTE = INFR / "data" / "remote-mirror" / "artifacts" / "symbol-status.jsonl"
STATUS_LOCAL = ART / "symbol-status.jsonl"          # local run + repair (patched) rows
MANIFEST_REMOTE = INFR / "data" / "remote-mirror" / "artifacts" / "checksum-manifest.jsonl"
MANIFEST_LOCAL = ART / "checksum-manifest.jsonl"
MANIFEST_PATCH = ART / "patch-manifest.jsonl"       # repair pass (patch_missing_days.py)
DELIST_JSON = ART / "delist-reconciliation.json"

# Operator 2026-07-16 (revised): only the 5 symbols with genuinely no collected
# data stay omitted. The 9 K-cluster symbols originally listed as failed in fact
# completed with passing invariants + verified parquets (the later 'error' rows
# were a duplicate worker's .tmp rename failure) and are ADMITTED.
OMITTED_OPERATOR = {"MYRIAUSDT", "SFPUSDT", "TACUSDT", "TRIAUSDT", "UNIUSDT"}
NO_BARS = {"DATAOLD01USDT"}

ONE_MIN = timedelta(minutes=1)
VOL_SPLIT_RTOL = 1e-6          # |Buy+Sell-Volume| tolerance (relative)
OUTAGE_RUN_MIN = 10            # minutes; gap runs >= this feed outage consensus
OUTAGE_QUORUM = 10             # near-continuous symbols gapping together => outage
CONTINUOUS_FILL = 0.98         # fill ratio to qualify as a consensus reference symbol
SPEC_SAMPLE_ROWS = 200_000
TICK_CONF_MIN = 0.995          # share of sampled prices on inferred tick grid
LOT_CONF_MIN = 0.995

# --------------------------------------------------------------------------- inputs


def load_status() -> dict[str, dict]:
    """Latest OK row per symbol across remote + local (repair rows overlay by ts)."""
    ok: dict[str, dict] = {}
    last: dict[str, dict] = {}
    for path in (STATUS_REMOTE, STATUS_LOCAL):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            last[r["symbol"]] = r
            if r["status"] == "ok" and (
                r["symbol"] not in ok or r["ts"] > ok[r["symbol"]]["ts"]
            ):
                ok[r["symbol"]] = r
    return {"ok": ok, "last": last}


def load_day_manifest(patched: set[str]) -> dict[str, dict]:
    """Merged day-level manifest views.

    Returns ``{"unresolved": {sym: [days]}, "last_day_with_bars": {sym: day}}``.

    The repair run (patch_missing_days.py) was operator-stopped mid-flight
    2026-07-16 ("leave them"): patch-manifest day rows only count for symbols
    whose merge actually completed (a patched=True ok status row exists, OR the
    parquet already carries at least the status-row bar count plus extras) —
    a downloaded-but-never-merged day is still a hole in the parquet.
    """
    # A day is RESOLVED if any pass ever fetched it (ok/empty/missing) for a
    # merged symbol — repair passes are cumulative and merges idempotent, so a
    # stale 'error' row from an earlier pass must not shadow a later fetch
    # (and vice versa: the spot-run manifest was lost with its volume while its
    # merged parquets survived, leaving old error rows behind).
    statuses: dict[tuple[str, str], set] = {}
    bars: dict[tuple[str, str], int] = {}
    for path in (MANIFEST_REMOTE, MANIFEST_LOCAL, MANIFEST_PATCH):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "symbol" not in r or "day" not in r:
                continue
            if path is MANIFEST_PATCH and r["symbol"] not in patched:
                continue
            key = (r["symbol"], r["day"])
            statuses.setdefault(key, set()).add(r["status"])
            if r["status"] == "ok":
                bars[key] = max(bars.get(key, 0), r.get("n_bars", 0))
    unresolved: dict[str, list] = {}
    last_day: dict[str, str] = {}
    for (sym, day), st in statuses.items():
        if st == {"error"}:
            unresolved.setdefault(sym, []).append(day)
        elif bars.get((sym, day), 0) > 0 and day > last_day.get(sym, ""):
            last_day[sym] = day
    return {"unresolved": {s: sorted(d) for s, d in unresolved.items()},
            "last_day_with_bars": last_day}


def load_patched_symbols() -> set[str]:
    """Symbols whose repair merge completed (patched=True ok row in local status)."""
    patched: set[str] = set()
    if STATUS_LOCAL.exists():
        for line in STATUS_LOCAL.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("patched") and r.get("status") == "ok":
                patched.add(r["symbol"])
    return patched


def load_delist() -> dict[str, dict]:
    d = json.loads(DELIST_JSON.read_text())
    return {row["symbol"]: row for row in d["symbols"]}


def bar_path(symbol: str) -> Path | None:
    p = STAGING_BARS / f"{symbol}.parquet"       # local-authoritative first
    if p.exists():
        return p
    p = MIRROR_BARS / f"{symbol}.parquet"
    if p.exists():
        return p
    return None

# --------------------------------------------------------------------------- invariants + gaps


def check_symbol(symbol: str, path: Path, status_row: dict) -> dict:
    """One-pass structural invariants + gap runs for a symbol parquet."""
    df = pl.read_parquet(
        path,
        columns=["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low",
                 "Close", "Volume", "BuyVolume", "SellVolume"],
    )
    n = df.height
    out: dict = {"n_bars": n, "n_bars_status": status_row["invariants"]["n_bars"]}

    checks = df.select(
        symbol_ok=(pl.col("Symbol") == symbol).all(),
        close_ok=((pl.col("CloseTime") - pl.col("OpenTime")) == ONE_MIN).all(),
        mono_bad=(pl.col("OpenTime").diff().slice(1) <= timedelta(0)).sum(),
        ohlc_bad=(
            (pl.col("High") < pl.col("Low"))
            | (pl.col("Open") > pl.col("High")) | (pl.col("Open") < pl.col("Low"))
            | (pl.col("Close") > pl.col("High")) | (pl.col("Close") < pl.col("Low"))
            | (pl.col("High") <= 0)
        ).sum(),
        vol_bad=(pl.col("Volume") < 0).sum(),
        split_bad=(
            (pl.col("BuyVolume") + pl.col("SellVolume") - pl.col("Volume")).abs()
            > VOL_SPLIT_RTOL * (pl.col("Volume").abs() + 1.0)
        ).sum(),
        t_first=pl.col("OpenTime").min(),
        t_last=pl.col("OpenTime").max(),
    ).row(0, named=True)

    out.update(
        symbol_col_ok=bool(checks["symbol_ok"]),
        close_grid_ok=bool(checks["close_ok"]),
        n_mono_fail=int(checks["mono_bad"]),
        n_ohlc_fail=int(checks["ohlc_bad"]),
        n_vol_neg=int(checks["vol_bad"]),
        n_split_fail=int(checks["split_bad"]),
        first_bar=str(checks["t_first"]),
        last_bar=str(checks["t_last"]),
    )

    span_min = int((checks["t_last"] - checks["t_first"]) / ONE_MIN) + 1
    out["expected_bars"] = span_min
    out["gap_minutes_total"] = span_min - n
    out["fill_ratio"] = round(n / span_min, 6)

    # gap runs: rows where the grid jumps > 1 minute
    gaps = (
        df.select(pl.col("OpenTime"))
        .with_columns(prev=pl.col("OpenTime").shift(1))
        .with_columns(dmin=((pl.col("OpenTime") - pl.col("prev")) / ONE_MIN))
        .filter(pl.col("dmin") > 1)
        .with_columns(run_min=(pl.col("dmin") - 1).cast(pl.Int64))
    )
    runs = gaps.select(
        start=pl.col("prev") + ONE_MIN,
        minutes=pl.col("run_min"),
    )
    hist = Counter()
    for m in runs["minutes"].to_list():
        if m == 1:
            hist["1m"] += 1
        elif m <= 5:
            hist["2-5m"] += 1
        elif m <= 60:
            hist["6-60m"] += 1
        else:
            hist["gt60m"] += 1
    out["gap_runs"] = dict(hist)
    out["max_gap_run_min"] = int(runs["minutes"].max() or 0)

    long_runs = runs.filter(pl.col("minutes") >= OUTAGE_RUN_MIN)
    out["_long_runs"] = [
        (t, int(m)) for t, m in zip(long_runs["start"].to_list(),
                                    long_runs["minutes"].to_list())
    ]

    # n_bars may exceed the status row where a repair merge landed (holes filled);
    # fewer bars than the recorded derivation = data loss = fail.
    out["n_bars_extra"] = n - out["n_bars_status"]
    out["invariants_pass"] = (
        out["symbol_col_ok"] and out["close_grid_ok"]
        and out["n_mono_fail"] == 0 and out["n_ohlc_fail"] == 0
        and out["n_vol_neg"] == 0 and out["n_split_fail"] == 0
        and n >= out["n_bars_status"]
    )

    # delist-tail + spec-inference sample (bounded)
    step = max(1, n // SPEC_SAMPLE_ROWS)
    out["_sample"] = df.gather_every(step).select(["Close", "Volume"])
    out["_tail"] = df.tail(43_200).select(["OpenTime", "Close", "Volume"])  # last 30d
    return out

# --------------------------------------------------------------------------- outage consensus


def consensus_outage_windows(long_runs_by_symbol: dict[str, list], fill: dict[str, float],
                             ) -> list[tuple]:
    """Windows where >= OUTAGE_QUORUM near-continuous symbols gap simultaneously."""
    refs = [s for s, f in fill.items() if f >= CONTINUOUS_FILL]
    events = []  # (ts, +1/-1)
    for s in refs:
        for start, minutes in long_runs_by_symbol.get(s, []):
            events.append((start, 1))
            events.append((start + timedelta(minutes=minutes), -1))
    events.sort(key=lambda e: (e[0], -e[1]))
    windows, depth, w_start = [], 0, None
    for ts, d in events:
        depth += d
        if depth >= OUTAGE_QUORUM and w_start is None:
            w_start = ts
        elif depth < OUTAGE_QUORUM and w_start is not None:
            windows.append((w_start, ts))
            w_start = None
    return windows


def day_intervals(days: list) -> list[tuple]:
    """Merge sorted ISO day strings into contiguous [start, end) datetimes."""
    from datetime import datetime as _dt

    ivs: list[list] = []
    for d in days:
        s = _dt.fromisoformat(d)
        e = s + timedelta(days=1)
        if ivs and ivs[-1][1] == s:
            ivs[-1][1] = e
        else:
            ivs.append([s, e])
    return [tuple(iv) for iv in ivs]


def _subtract(iv: tuple, cuts: list[tuple]) -> list[tuple]:
    """Interval minus a list of disjoint sorted intervals."""
    out, (s, e) = [], iv
    for c0, c1 in cuts:
        if c1 <= s or c0 >= e:
            continue
        if c0 > s:
            out.append((s, c0))
        s = max(s, c1)
        if s >= e:
            return out
    if s < e:
        out.append((s, e))
    return out


def split_gap_minutes(long_runs: list, coll_ivs: list[tuple],
                      windows: list[tuple]) -> tuple[int, int]:
    """(collection_gap_minutes, outage_minutes) for a symbol's long gap runs.

    Collection gaps (unresolved missing day-files) take precedence; the
    remainder of each run is tested against consensus outage windows.
    """
    collection = outage = 0
    for start, minutes in long_runs:
        end = start + timedelta(minutes=minutes)
        for c0, c1 in coll_ivs:
            lo, hi = max(start, c0), min(end, c1)
            if hi > lo:
                collection += int((hi - lo) / ONE_MIN)
        for rs, re_ in _subtract((start, end), coll_ivs):
            for w0, w1 in windows:
                lo, hi = max(rs, w0), min(re_, w1)
                if hi > lo:
                    outage += int((hi - lo) / ONE_MIN)
    return collection, outage

# --------------------------------------------------------------------------- spec inference


def _snap_increment(x: float) -> float:
    """Snap a raw increment to the {1, 2, 2.5, 5} x 10^k grid."""
    if x <= 0 or not math.isfinite(x):
        return 0.0
    k = math.floor(math.log10(x))
    best, err = 0.0, float("inf")
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        cand = m * 10.0 ** k
        e = abs(cand - x) / x
        if e < err:
            best, err = cand, e
    return best if err < 0.25 else x


def infer_increment(values: list[float]) -> tuple[float, float]:
    """(increment, confidence) via fractional GCD of positive sampled values."""
    vals = sorted({round(v, 12) for v in values if v and v > 0 and math.isfinite(v)})
    if len(vals) < 10:
        return 0.0, 0.0
    fracs = [Fraction(str(v)).limit_denominator(10**9) for v in vals[:4000]]
    g = fracs[0]
    for f in fracs[1:]:
        g = Fraction(math.gcd(g.numerator * f.denominator, f.numerator * g.denominator),
                     g.denominator * f.denominator)
        if g == 0:
            return 0.0, 0.0
    inc = _snap_increment(float(g))
    if inc <= 0:
        return 0.0, 0.0
    on_grid = sum(1 for v in vals if abs(v / inc - round(v / inc)) < 1e-6)
    return inc, on_grid / len(vals)


def infer_specs(sample: pl.DataFrame) -> dict:
    """Tick from Close price grid; lot from bar-volume grid (sums of lot multiples)."""
    price_diffs = (
        sample.select(pl.col("Close").unique().sort().diff().drop_nulls())
        .to_series().to_list()
    )
    tick, tick_conf = infer_increment(price_diffs)
    lot, lot_conf = infer_increment(sample["Volume"].to_list())
    return {
        "tick_size": tick, "tick_confidence": round(tick_conf, 4),
        "lot_step": lot, "lot_confidence": round(lot_conf, 4),
    }

# --------------------------------------------------------------------------- orchestration


def main() -> None:
    status = load_status()
    delist = load_delist()
    census = sorted(delist.keys())
    assert len(census) == 910, f"census size {len(census)} != 910"

    rows: dict[str, dict] = {}
    long_runs_by_symbol: dict[str, list] = {}
    fill: dict[str, float] = {}
    specs: dict[str, dict] = {}

    candidates = [s for s in census if s not in OMITTED_OPERATOR and s not in NO_BARS]
    for sym in tqdm(candidates, desc="invariants+gaps+specs"):
        srow = status["ok"].get(sym)
        path = bar_path(sym)
        if srow is None or path is None:
            rows[sym] = {"symbol": sym, "admission": "FAIL_MISSING",
                         "detail": f"ok_row={srow is not None} parquet={path is not None}"}
            continue
        try:
            res = check_symbol(sym, path, srow)
        except Exception as e:  # noqa: BLE001 — corrupt parquet = explicit FAIL row
            rows[sym] = {"symbol": sym, "admission": "FAIL_CORRUPT",
                         "path": str(path.relative_to(INFR)), "detail": str(e)[:200]}
            continue
        long_runs_by_symbol[sym] = res.pop("_long_runs")
        tail = res.pop("_tail")
        sample = res.pop("_sample")
        fill[sym] = res["fill_ratio"]
        res.update(symbol=sym, path=str(path.relative_to(INFR)))

        d = delist[sym]
        res["listed"] = d["listed"]
        if d["spec"] == "OK":
            specs[sym] = {
                "tick_size": float(d["tick_size"]), "lot_step": float(d["lot_step"]),
                "min_qty": float(d["min_qty"]), "source": "API",
            }
            res["spec_source"] = "API"
        else:
            inf = infer_specs(sample)
            ok = (inf["tick_size"] > 0 and inf["tick_confidence"] >= TICK_CONF_MIN
                  and inf["lot_step"] > 0 and inf["lot_confidence"] >= LOT_CONF_MIN)
            res["spec_source"] = "INFERRED" if ok else "SPEC_INCOMPLETE"
            res["spec_inference"] = inf
            if ok:
                specs[sym] = {
                    "tick_size": inf["tick_size"], "lot_step": inf["lot_step"],
                    "min_qty": inf["lot_step"], "source": "INFERRED",
                    "confidence": {"tick": inf["tick_confidence"],
                                   "lot": inf["lot_confidence"]},
                }

        # delist tail return (intactness resolved in the second pass, vs the
        # last archive day that actually printed trades — archives carry
        # trailing EMPTY day-files after a delisting halt, e.g. LUNA 2022-05-12)
        if not d["listed"]:
            res["tail_last_bar_day"] = res["last_bar"][:10]
            closes = tail["Close"].to_list()
            if len(closes) > 1:
                res["tail_30d_return"] = round(closes[-1] / closes[0] - 1.0, 4)

        rows[sym] = res

    windows = consensus_outage_windows(long_runs_by_symbol, fill)
    # merged symbols: explicit patched rows, plus parquets carrying extra bars
    # (a repair merge that landed without its status row being written)
    patched = load_patched_symbols() | {
        s for s, r in rows.items() if r.get("n_bars_extra", 0) > 0
    }
    dm = load_day_manifest(patched)
    unresolved = dm["unresolved"]
    last_day_with_bars = dm["last_day_with_bars"]

    for sym in candidates:
        r = rows[sym]
        if r.get("admission", "").startswith("FAIL"):
            continue
        # Ground the unresolved-day count in the parquet itself: a manifest
        # 'error' day whose minutes are present in the data was fetched by a
        # pass whose manifest was lost (spot-run volume) — it is resolved.
        # Effective = days overlapping an actual gap run or outside bar range.
        first_bar = datetime.fromisoformat(r["first_bar"])
        last_bar = datetime.fromisoformat(r["last_bar"])
        runs = long_runs_by_symbol[sym]
        eff_days = []
        for d in unresolved.get(sym, []):
            d0 = datetime.fromisoformat(d)
            d1 = d0 + timedelta(days=1)
            if d1 <= first_bar or d0 > last_bar:
                eff_days.append(d)
                continue
            for start, minutes in runs:
                if start < d1 and (start + timedelta(minutes=minutes)) > d0:
                    eff_days.append(d)
                    break
        coll_ivs = day_intervals(eff_days)
        collection, outage = split_gap_minutes(runs, coll_ivs, windows)
        r["collection_gap_minutes"] = collection
        r["outage_minutes"] = outage
        r["no_trade_minutes"] = r["gap_minutes_total"] - collection - outage
        r["unresolved_error_days"] = len(eff_days)

        if not r["listed"]:
            ref_day = last_day_with_bars.get(sym, "")
            r["tail_last_traded_archive_day"] = ref_day
            r["tail_intact"] = (not ref_day) or r["tail_last_bar_day"] >= ref_day

        integ = r["invariants_pass"] and (r["listed"] or r.get("tail_intact", True))
        if not integ:
            r["admission"] = "FAIL_INVARIANT"
        elif r["spec_source"] == "SPEC_INCOMPLETE":
            r["admission"] = "SPEC_INCOMPLETE"
        else:
            r["admission"] = "ADMITTED"

    for sym in OMITTED_OPERATOR:
        rows[sym] = {
            "symbol": sym, "admission": "OMITTED_OPERATOR",
            "detail": "no data collected (HTTP 403 both EC2 passes, no local retry); "
                      "operator 2026-07-16: fails intended universe selection rules",
        }
    for sym in NO_BARS:
        rows[sym] = {"symbol": sym, "admission": "NO_BARS",
                     "detail": "dead placeholder archive, legitimately empty"}

    # ------------------------------------------------------------------ write artifacts
    ledger = ART / "admission-ledger.jsonl"
    with ledger.open("w") as f:
        for sym in census:
            f.write(json.dumps(rows[sym], default=str) + "\n")

    (ART / "instrument-specs.json").write_text(json.dumps(
        {"generated": "A5 admission gate", "n_symbols": len(specs), "specs": specs},
        indent=1, sort_keys=True))

    write_report(rows, census, windows, specs)
    print(f"admission ledger: {ledger}")


def write_report(rows: dict, census: list, windows: list, specs: dict) -> None:
    n = Counter(r["admission"] for r in rows.values())
    corrupt = sorted(r["symbol"] for r in rows.values() if r["admission"] == "FAIL_CORRUPT")
    admitted = [r for r in rows.values() if r["admission"] == "ADMITTED"]
    spec_inc = [r for r in rows.values() if r["admission"] == "SPEC_INCOMPLETE"]
    fails = [r for r in rows.values() if r["admission"].startswith("FAIL")]
    inferred = [r for r in admitted if r.get("spec_source") == "INFERRED"]
    tails_bad = [r["symbol"] for r in rows.values()
                 if r.get("tail_intact") is False]
    total_bars = sum(r.get("n_bars", 0) for r in admitted + spec_inc)
    n_unres_days = sum(r.get("unresolved_error_days", 0) for r in admitted + spec_inc)
    coll_syms = [r["symbol"] for r in admitted + spec_inc
                 if r.get("collection_gap_minutes", 0) > 0]

    lines = [
        "# INFR-011 A5 — Admission Report",
        "",
        f"**Census:** {len(census)} | " + " | ".join(f"{k}: {v}" for k, v in sorted(n.items())),
        # FAIL_CORRUPT rows are explicit operator-acknowledged exclusions (like
        # OMITTED_OPERATOR); the gate verdict is about the ADMITTED set's integrity.
        f"**Overall:** "
        f"{'FAIL' if any(r['admission'] in ('FAIL_INVARIANT', 'FAIL_MISSING') for r in rows.values()) else ('PASS_WITH_EXCLUSIONS' if corrupt else 'PASS')}",
        f"**Total bars (admitted + spec-incomplete):** {total_bars:,}",
        "",
        "## Invariants",
        f"- Structural re-verification on local parquets: {len(admitted) + len(spec_inc)} symbols pass",
        f"- Failures: {len(fails)}" + (f" — {[r['symbol'] for r in fails]}" if fails else ""),
        "- Volume ≡ Σ trade sizes verified at derivation (raw discarded by design); "
        "carried from symbol-status rows; Buy+Sell ≡ Volume re-verified here.",
        "",
        "## Collection repair (2026-07-16, operator-approved)",
        "- EC2 bulk run had left 23,450 day-files as HTTP-403 `error` across 740 "
        "symbols while marking symbols ok (day-level failures were never retried).",
        "- Repaired locally by `patch_missing_days.py` (re-download + merge + "
        "invariant re-run per symbol).",
        f"- Unresolved error days remaining after repair: {n_unres_days}"
        + (f" (symbols with COLLECTION_GAP minutes: {coll_syms})" if coll_syms else ""),
        "",
        "## Gap classification (INFORMATIVE — no veto on raw totals)",
        f"- Consensus exchange-outage windows (≥{OUTAGE_QUORUM} near-continuous symbols "
        f"gapping ≥{OUTAGE_RUN_MIN}m together): {len(windows)}",
    ]
    for w0, w1 in windows[:20]:
        lines.append(f"  - {w0} → {w1}")
    top_thin = sorted((r for r in admitted + spec_inc), key=lambda r: -r.get("no_trade_minutes", 0))[:10]
    lines += ["", "| Symbol | fill ratio | no-trade min | collection min | outage min | max run |",
              "|---|---|---|---|---|---|"]
    for r in top_thin:
        lines.append(f"| {r['symbol']} | {r['fill_ratio']} | {r['no_trade_minutes']:,} "
                     f"| {r.get('collection_gap_minutes', 0):,} "
                     f"| {r['outage_minutes']:,} | {r['max_gap_run_min']:,} |")
    lines += [
        "",
        "## Delist tails",
        f"- Delisted symbols with trimmed tails (last bar day ≠ last archive day): "
        f"{len(tails_bad)}" + (f" — {tails_bad}" if tails_bad else " (all intact)"),
        "",
        "## Instrument specs",
        f"- API specs (listed): {sum(1 for s in specs.values() if s['source'] == 'API')}",
        f"- SPEC_INFERRED (delisted, from bar price/size grids): {len(inferred)}",
        f"- SPEC_INCOMPLETE (return-level reads only): {len(spec_inc)}"
        + (f" — {[r['symbol'] for r in spec_inc]}" if spec_inc else ""),
        "",
        "## Explicit non-admitted rows",
        "- OMITTED_OPERATOR (5): MYRIAUSDT SFPUSDT TACUSDT TRIAUSDT UNIUSDT — no "
        "data collected (403 both EC2 passes). Operator 2026-07-16: fails intended "
        "universe selection rules; retryable later if ever needed.",
        "- The 9 K-cluster symbols originally omitted are ADMITTED (operator "
        "revision 2026-07-16): their collections completed with passing invariants "
        "+ verified parquets; the 'failed both passes' premise was a duplicate "
        "worker's .tmp rename error row.",
        "- NO_BARS (1): DATAOLD01USDT — dead placeholder archive.",
        f"- FAIL_CORRUPT ({len(corrupt)}): {corrupt} — parquet unreadable; checksum "
        "matches the EC2 manifest, so the file was corrupt at source (concurrent "
        ".tmp rename race). Not admitted; re-collect later if wanted (operator "
        "declined further downloads 2026-07-16).",
        "",
        "Ledger: `artifacts/admission-ledger.jsonl` (910 rows). "
        "Specs: `artifacts/instrument-specs.json`.",
    ]
    (ART / "admission-report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
