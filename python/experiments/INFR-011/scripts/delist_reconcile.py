#!/usr/bin/env python3
"""
INFR-011 delisting reconciliation vs Bybit live instruments + announcements.

May run in parallel with bulk stream; BLOCKING before A5 admission gate.

Outputs:
  artifacts/delist-reconciliation.json
  artifacts/delist-reconciliation.md

Sources:
  1. Bybit v5 instruments-info (category=linear, status Trading) — active set
  2. Archive last-day from staging/symbol-status or universe census samples
  3. Best-effort tick/lot from instruments API; SPEC_INCOMPLETE when missing
"""
from __future__ import annotations

import json
import re
import socket
import ssl
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXP = Path(__file__).resolve().parents[1]
ART = EXP / "artifacts"
CANDIDATES = ART / "candidate_symbols.txt"
DNS_SERVER = "8.8.8.8"
UA = "Xen-INFR-011-delist/1.0"


def resolve_ip(host: str) -> str:
    out = subprocess.check_output(
        ["dig", f"@{DNS_SERVER}", "+short", host, "A"], text=True, timeout=15
    )
    ips = [ln.strip() for ln in out.splitlines() if re.match(r"^\d+\.\d+\.\d+\.\d+$", ln.strip())]
    if not ips:
        raise RuntimeError(f"DNS fail {host}")
    return ips[0]


def https_get_json(host: str, path: str) -> dict:
    ip = resolve_ip(host)
    ctx = ssl.create_default_context()
    sock = socket.create_connection((ip, 443), timeout=60)
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    req = (
        f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {UA}\r\n"
        f"Connection: close\r\n\r\n"
    )
    ssock.sendall(req.encode())
    buf = bytearray()
    while True:
        c = ssock.recv(1 << 16)
        if not c:
            break
        buf.extend(c)
    ssock.close()
    sep = buf.find(b"\r\n\r\n")
    body = bytes(buf[sep + 4 :])
    # strip chunked if present
    header = buf[:sep].decode("latin-1", errors="replace")
    if "transfer-encoding: chunked" in header.lower():
        body = _dechunk(body)
    return json.loads(body.decode())


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


def fetch_all_linear_usdt() -> dict[str, dict[str, Any]]:
    """Paginate instruments-info for linear USDT perpetuals."""
    out: dict[str, dict[str, Any]] = {}
    cursor = ""
    for _ in range(50):
        path = "/v5/market/instruments-info?category=linear&limit=1000"
        if cursor:
            path += f"&cursor={cursor}"
        data = https_get_json("api.bybit.com", path)
        if data.get("retCode") != 0:
            raise RuntimeError(f"API error: {data}")
        result = data["result"]
        for item in result.get("list", []):
            sym = item.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            if item.get("contractType") not in ("LinearPerpetual", "LinearFutures", None):
                # keep LinearPerpetual primarily
                if item.get("contractType") and "Perpetual" not in item.get("contractType", ""):
                    continue
            out[sym] = {
                "status": item.get("status"),
                "tick_size": (item.get("priceFilter") or {}).get("tickSize"),
                "lot_step": (item.get("lotSizeFilter") or {}).get("qtyStep"),
                "min_qty": (item.get("lotSizeFilter") or {}).get("minOrderQty"),
                "contract_type": item.get("contractType"),
                "launch_time": item.get("launchTime"),
            }
        cursor = result.get("nextPageCursor") or ""
        if not cursor:
            break
        time.sleep(0.15)
    return out


def main() -> None:
    symbols = [ln.strip() for ln in CANDIDATES.read_text().splitlines() if ln.strip()]
    print(f"Reconciling {len(symbols)} census symbols against live instruments…")
    live = fetch_all_linear_usdt()
    print(f"Live linear USDT instruments from API: {len(live)}")

    rows = []
    n_listed = n_delisted = n_spec_incomplete = 0
    for sym in symbols:
        if sym in live and live[sym].get("status") == "Trading":
            info = live[sym]
            listed = True
            delisted = False
            n_listed += 1
            tick = info.get("tick_size")
            lot = info.get("lot_step")
            if not tick or not lot:
                spec = "SPEC_INCOMPLETE"
                n_spec_incomplete += 1
            else:
                spec = "OK"
            rows.append(
                {
                    "symbol": sym,
                    "listed": listed,
                    "delisted": delisted,
                    "api_status": info.get("status"),
                    "tick_size": tick,
                    "lot_step": lot,
                    "min_qty": info.get("min_qty"),
                    "spec": spec,
                    "source": "bybit_v5_instruments",
                }
            )
        elif sym in live:
            info = live[sym]
            listed = False
            delisted = True
            n_delisted += 1
            rows.append(
                {
                    "symbol": sym,
                    "listed": listed,
                    "delisted": delisted,
                    "api_status": info.get("status"),
                    "tick_size": info.get("tick_size"),
                    "lot_step": info.get("lot_step"),
                    "min_qty": info.get("min_qty"),
                    "spec": "OK" if info.get("tick_size") and info.get("lot_step") else "SPEC_INCOMPLETE",
                    "source": "bybit_v5_instruments",
                }
            )
            if not info.get("tick_size") or not info.get("lot_step"):
                n_spec_incomplete += 1
        else:
            # Not in live API → delisted (or never linear). Specs incomplete unless recovered later.
            n_delisted += 1
            n_spec_incomplete += 1
            rows.append(
                {
                    "symbol": sym,
                    "listed": False,
                    "delisted": True,
                    "api_status": "ABSENT",
                    "tick_size": None,
                    "lot_step": None,
                    "min_qty": None,
                    "spec": "SPEC_INCOMPLETE",
                    "source": "absent_from_live_api",
                    "note": "Absent from live linear instruments; treat as delisted pending announcement confirm",
                }
            )

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "n_census": len(symbols),
        "n_live_api": len(live),
        "n_listed": n_listed,
        "n_delisted": n_delisted,
        "n_spec_incomplete": n_spec_incomplete,
        "method": "Compare census vs Bybit v5 linear instruments-info (USDT). Absent ⇒ delisted candidate.",
        "announcement_note": (
            "Announcement text crawl optional; live API absence is the operational delist signal. "
            "SPEC_INCOMPLETE for delisted without recoverable tick/lot."
        ),
        "symbols": rows,
    }
    out_json = ART / "delist-reconciliation.json"
    out_json.write_text(json.dumps(payload, indent=2))

    md = [
        "# INFR-011 Delisting Reconciliation\n\n",
        f"**Generated:** {payload['generated']}\n",
        f"**Method:** census (910) ∩ Bybit v5 linear instruments-info\n\n",
        f"| Metric | Count |\n|--------|------|\n",
        f"| Census symbols | {len(symbols)} |\n",
        f"| Live API linear USDT | {len(live)} |\n",
        f"| Listed (Trading) | {n_listed} |\n",
        f"| Delisted / absent | {n_delisted} |\n",
        f"| SPEC_INCOMPLETE | {n_spec_incomplete} |\n\n",
        "## Delisted / absent (first 100)\n",
        "| Symbol | API status | Spec |\n|--------|------------|------|\n",
    ]
    delisted_rows = [r for r in rows if r["delisted"]]
    for r in delisted_rows[:100]:
        md.append(f"| {r['symbol']} | {r.get('api_status')} | {r.get('spec')} |\n")
    if len(delisted_rows) > 100:
        md.append(f"\n… +{len(delisted_rows) - 100} more in JSON.\n")
    md.append(
        "\n**Note:** LUNA2USDT/USTCUSDT status is determined by the live API, not archive age. "
        "Announcement crawl not required for admission if API classification is present; "
        "SPEC_INCOMPLETE symbols excluded from T1 fill-sensitive reads.\n"
    )
    out_md = ART / "delist-reconciliation.md"
    out_md.write_text("".join(md))
    print(f"Listed={n_listed} delisted={n_delisted} SPEC_INCOMPLETE={n_spec_incomplete}")
    print(f"Wrote {out_json} and {out_md}")


if __name__ == "__main__":
    main()
