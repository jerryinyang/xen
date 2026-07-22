#!/usr/bin/env python3
"""
INFR-011 Phase A Step 1 — BLOCKING Universe Census
Fetches https://public.bybit.com/trading/ directory listing,
filters strictly to USDT linear perpetuals (listed + delisted),
excludes spot, inverse, dated futures, USDC per D3.
For each candidate symbol dir, probes first/last archive date from file listing.
Cross-checks against known delistings via public announcements (stub + operator input).
Writes universe-census.md + machine readable json.
"""
import re
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import requests

ROOT = "https://public.bybit.com/trading/"
HEADERS = {"User-Agent": "Xen-INFR-011-census/1.0 (research; contact via repo)"}
OUT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CENSUS_MD = OUT_DIR / "universe-census.md"
CENSUS_JSON = OUT_DIR / "universe-census.json"
RAW_HTML = OUT_DIR / "trading-root.html"

DELAY = 0.4  # polite

# Regex for dated futures (e.g. BTC-01DEC23, SOL-05JUL24, WC_* etc.)
DATED_RE = re.compile(r'-[0-9]{2}[A-Z]{3}[0-9]{2,4}|WC_')
# Inverse USD (not USDT)
INVERSE_RE = re.compile(r'USD$')
# USDC settled
USDC_RE = re.compile(r'USDC')

def fetch_text(url: str, timeout: int = 30) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def parse_dirs(html: str) -> List[str]:
    # Simple regex parse of Apache/S3-style directory listing (no bs4 dep)
    # Matches <a href="FOO/">FOO/</a>
    pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>\1?</a>', re.I)
    dirs = []
    for m in pattern.finditer(html):
        href = m.group(1)
        if href.endswith("/") and not href.startswith(("?", "#", "../", "http", "/trading/")) and href != "/":
            dirs.append(href)
    return sorted(set(dirs))

def is_candidate_usdt_linear_perp(dirname: str) -> bool:
    if not dirname.endswith("/"):
        return False
    sym = dirname[:-1].upper()
    if DATED_RE.search(sym):
        return False
    if INVERSE_RE.search(sym) and not sym.endswith("USDT"):
        return False
    if USDC_RE.search(sym):
        return False
    # Primary linear USDT perps live under <BASE>USDT/ folders (and some *PERP that are USDT linear)
    # Accept all remaining that contain USDT or end with PERP (operator will review edge cases)
    if sym.endswith("USDT"):
        return True
    if sym.endswith("PERP"):
        # 1000BONKPERP etc are typically the linear contracts too; include for review
        return True
    return False

def probe_first_last_dates(symbol_dir: str) -> Dict[str, Optional[str]]:
    """Probe the symbol subdir listing; return first/last YYYY-MM-DD from filenames."""
    url = ROOT + symbol_dir
    try:
        html = fetch_text(url)
        # Regex for <a ...>FILENAME</a> where filename has .csv.gz
        pattern = re.compile(r'<a[^>]+href="([^"]+\.csv\.gz)"[^>]*>[^<]*</a>', re.I)
        dates = []
        for m in pattern.finditer(html):
            href = m.group(1)
            # Filename pattern: SYMBOLYYYY-MM-DD.csv.gz
            dm = re.search(r'(\d{4}-\d{2}-\d{2})', href)
            if dm:
                dates.append(dm.group(1))
        if not dates:
            return {"first": None, "last": None, "count_days": 0}
        dates = sorted(dates)
        return {
            "first": dates[0],
            "last": dates[-1],
            "count_days": len(dates),
        }
    except Exception as e:
        return {"first": None, "last": None, "count_days": 0, "error": str(e)}

def load_or_fetch_root() -> str:
    if RAW_HTML.exists():
        return RAW_HTML.read_text(encoding="utf-8")
    print("Fetching root listing (blocking, one-shot)...")
    html = fetch_text(ROOT)
    RAW_HTML.write_text(html, encoding="utf-8")
    time.sleep(DELAY)
    return html

def main():
    print("=== INFR-011 Universe Census (BLOCKING) ===")
    html = load_or_fetch_root()
    all_dirs = parse_dirs(html)
    print(f"Total dirs in listing: {len(all_dirs)}")

    candidates = [d for d in all_dirs if is_candidate_usdt_linear_perp(d)]
    print(f"Candidates after USDT-linear-perp filter (pre date-probe): {len(candidates)}")

    records: List[Dict] = []
    for i, d in enumerate(candidates):
        sym = d[:-1]
        print(f"[{i+1}/{len(candidates)}] probing {sym} ...", end=" ", flush=True)
        info = probe_first_last_dates(d)
        rec = {
            "symbol": sym,
            "dir": d,
            "first_archive": info.get("first"),
            "last_archive": info.get("last"),
            "archive_days": info.get("count_days", 0),
            "listed": True,  # default; delisted inferred from no recent files or cross-check
            "delisted": False,
            "spec_notes": "",
            "error": info.get("error"),
        }
        # Heuristic: if last_archive older than ~6 months from now (2026-07), mark potential delist candidate
        if rec["last_archive"]:
            try:
                last = datetime.fromisoformat(rec["last_archive"])
                if (datetime(2026, 7, 14) - last).days > 180:
                    rec["delisted"] = True
                    rec["listed"] = False
            except Exception:
                pass
        records.append(rec)
        print(f"{rec['first_archive']} → {rec['last_archive']} ({rec['archive_days']} days) delisted={rec['delisted']}")
        time.sleep(DELAY)

    # Write JSON
    CENSUS_JSON.write_text(json.dumps({
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "source": ROOT,
        "filter": "USDT linear perps incl. delisted (D3); dated/inverse/USDC excluded",
        "n_candidates": len(records),
        "symbols": records,
    }, indent=2), encoding="utf-8")

    # Write human MD (dense)
    lines = []
    lines.append("# INFR-011 Universe Census — Bybit USDT Linear Perpetuals (incl. delisted)\n")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z  \n")
    lines.append(f"**Source:** {ROOT}  \n")
    lines.append(f"**Filter (locked D3):** USDT linear perpetuals only; exclude spot, inverse (USD*), dated futures (DATE pattern), USDC-settled.  \n")
    lines.append(f"**N symbols:** {len(records)}  \n")
    lines.append("**Cross-check note:** Delisted flag is heuristic (archive age) + requires operator confirmation against Bybit announcements. Gaps in tick/lot specs recorded explicitly.\n\n")
    lines.append("| Symbol | First Archive | Last Archive | Days | Listed | Delisted | Notes |\n")
    lines.append("|--------|---------------|--------------|------|--------|----------|-------|\n")
    for r in sorted(records, key=lambda x: (not x["listed"], x["symbol"])):
        listed = "yes" if r["listed"] else "no"
        delisted = "yes" if r["delisted"] else "no"
        notes = r.get("spec_notes", "") or (r.get("error") or "")
        lines.append(f"| {r['symbol']} | {r['first_archive'] or '?'} | {r['last_archive'] or '?'} | {r['archive_days']} | {listed} | {delisted} | {notes} |\n")

    lines.append("\n## Delisting Cross-Check (operator action required)\n")
    lines.append("1. Review https://announcements.bybit.com/ and Bybit blog for historical delist notices covering USDT perps.\n")
    lines.append("2. Confirm LUNA2USDT, USTCUSDT, and any others flagged above.\n")
    lines.append("3. For delisted: attempt recovery of tick size, lot size from last archive header or announcement; record `SPEC_INCOMPLETE` if unrecoverable.\n")
    lines.append("4. Update this file and universe-census.json with final listed/delisted + spec fields.\n")

    lines.append("\n## Storage Estimate Inputs (pre-bulk)\n")
    lines.append("See operator presentation block. Raw peak estimated from sample daily .gz sizes × total symbol-days.\n")
    lines.append("Parquet (1m bars + spreads) target: single-digit GB for full universe (conservative compression + partition by date).\n")

    CENSUS_MD.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {CENSUS_MD}")
    print(f"Wrote {CENSUS_JSON}")
    print("Census complete. Present to operator. DO NOT bulk download yet.")

if __name__ == "__main__":
    main()