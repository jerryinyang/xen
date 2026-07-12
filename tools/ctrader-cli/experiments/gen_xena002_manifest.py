"""Generate the XENA-002 universe manifest (design.md §3 grid, 2,736 candidates).

Writes ``data/strategy_runs/XENA-002/universe_manifest.json`` in the
``xen.xena.ingest`` format: one row per candidate with ``candidate_id``,
``run_dir`` (relative to the manifest), ``symbol``, ``cost_bps``,
``money_per_unit``. Run dirs are the deterministic lowercase candidate IDs the
MtfCtxMomentumModel emits — no timestamp suffix.

cost_bps = FTMO commission-only round trip (design §4). Spread pins are an
OPERATOR pre-gate item; when pinned, regenerate this manifest with spread
added (selection is cost-free regardless — gross amendment A-1).

money_per_unit: design §4 pins (TRAIN-window FX medians / HKD peg — inherited
verbatim from XENA-001 QA run 1 amendment 4; same instruments, same window).

Usage:  python tools/ctrader-cli/experiments/gen_xena002_manifest.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "data" / "strategy_runs" / "XENA-002"

# Broker symbol -> (commission-only cost_bps RT, money_per_unit) — design.md §4.
SYMBOL_PINS: dict[str, tuple[float, float]] = {
    "USTEC":   (0.0, 1.0),
    "US500":   (0.0, 1.0),
    "US2000":  (0.0, 1.0),
    "US30":    (0.0, 1.0),
    "JP225":   (0.0, 0.006968),   # JPY->USD = 1/143.516 (USDJPY TRAIN median)
    "AUS200":  (0.0, 0.66197),    # AUDUSD TRAIN median
    "STOXX50": (0.0, 1.08418),    # EU50, EUR quote — EURUSD TRAIN median
    "DE40":    (0.0, 1.08418),    # GER40, EUR quote
    "HK50":    (0.0, 0.128205),   # HKD peg mid 7.80
    "UK100":   (0.0, 1.25292),    # GBPUSD TRAIN median
    "XAUUSD":  (0.28, 1.0),       # 0.0014%/side x2
    "BTCUSD":  (13.0, 1.0),       # 0.065%/side x2
}

DOMAIN_PAIRS = ("1D1H", "4H15M", "1H5M")
HOLD_LABELS = ("H05X", "H1X", "H2X", "H4X")
N_VARIANTS = 19


def main() -> None:
    candidates = []
    for symbol, (cost_bps, mpu) in SYMBOL_PINS.items():
        for pair in DOMAIN_PAIRS:
            for hold in HOLD_LABELS:
                for v in range(N_VARIANTS):
                    cid = f"C2-{symbol}-{pair}-{hold}-V{v:02d}"
                    candidates.append({
                        "candidate_id": cid,
                        "run_dir": cid.lower(),
                        "symbol": symbol,
                        "cost_bps": cost_bps,
                        "money_per_unit": mpu,
                    })
    assert len(candidates) == 2736, len(candidates)
    manifest = {
        "universe_id": "XENA-002",
        "family": "CF-MTFCTX-001",
        "model": "MtfCtxMomentum (CTRL-02 NAIVE MOMENTUM, 3-bar breakout)",
        "analysis_end_utc": "2024-12-11T08:19:00Z",
        "registry_sha256": "537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6",
        "cost_note": "commission-only RT; operator spread pins pending (pre-gate blocker)",
        "candidates": candidates,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "universe_manifest.json"
    path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"wrote {path} ({len(candidates)} candidates)")


if __name__ == "__main__":
    main()
