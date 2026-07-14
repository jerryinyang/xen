#!/usr/bin/env python3
"""Generate the EXP-014 (CF-MR-004 / HYP-002) cTrader-CLI conf matrix.

Reproducible generator for the faithful full-exit cross-instrument MR run set. Writes
`EXP-014-<series>-<arm>.conf` for series {S5,S6,S7,S8} × arms {noneR (binding primary),
noneS (A/B static), allowR, extendR}. All arms reuse the EXP-013 first-49% TRAIN fence
(identical dataset/cutoffs). S8 is BASKET-based (design F-fix: was pair-median-60 → basket-
median-90), so it shares S5/S7's class-mate structure. Phase-shift leak-tripwire confs are
generated on demand only for an admitting cell (Stage 4), not up front.

Run:  python3 gen_exp014_confs.py   (from tools/ctrader-cli/experiments/)
"""
from pathlib import Path

# --- shared first-49% TRAIN fence (per symbol) — reused verbatim from EXP-013 -------------- #
CUTOFF_ISO = {
    "EURUSD": "2024-08-25T22:19:00Z", "GBPUSD": "2024-09-08T22:09:00Z",
    "USDJPY": "2024-09-06T12:28:00Z", "USDCHF": "2024-09-09T00:05:00Z",
    "USDCAD": "2024-09-06T16:23:00Z", "AUDUSD": "2024-09-06T14:40:00Z",
    "NZDUSD": "2024-09-06T05:42:00Z", "USTEC": "2024-08-26T01:06:00Z",
    "US500": "2024-09-17T17:26:00Z", "US2000": "2024-09-10T09:33:00Z",
    "JP225": "2024-09-23T04:40:00Z",
}
CUTOFF_BT = {
    "EURUSD": "25/08/2024 22:19", "GBPUSD": "08/09/2024 22:09", "USDJPY": "06/09/2024 12:28",
    "USDCHF": "09/09/2024 00:05", "USDCAD": "06/09/2024 16:23", "AUDUSD": "06/09/2024 14:40",
    "NZDUSD": "06/09/2024 05:42", "USTEC": "26/08/2024 01:06", "US500": "17/09/2024 17:26",
    "US2000": "10/09/2024 09:33", "JP225": "23/09/2024 04:40",
}

FX = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"]
IDX = ["USTEC", "US500", "US2000", "JP225"]


def class_mates(sym: str) -> list[str]:
    """Equal-weight class-mate basket = class members minus self (S5/S7/S8)."""
    cls = FX if sym in FX else IDX
    return [m for m in cls if m != sym]


# series -> (symbols, per-symbol mates). S8 == S7 structure (basket F-fix).
BASKET_SYMS = FX + IDX
S6_PAIRS = {"EURUSD": ["GBPUSD"], "AUDUSD": ["NZDUSD"], "USDCHF": ["USDCAD"],
            "USTEC": ["US500"], "US500": ["US2000"]}
SERIES = {
    "S5_SPREAD": (BASKET_SYMS, {s: class_mates(s) for s in BASKET_SYMS}),
    "S6_PAIR":   (list(S6_PAIRS), S6_PAIRS),
    "S7_BASKET": (BASKET_SYMS, {s: class_mates(s) for s in BASKET_SYMS}),
    "S8_RVINDEX": (BASKET_SYMS, {s: class_mates(s) for s in BASKET_SYMS}),
}

# arm -> (file-suffix, extra cBot args). none/R is the binding PRIMARY; the rest are disclosure.
ARMS = {
    "noneR":   ("--CisReentry=none", "BINDING PRIMARY: faithful full-exit, reentry=none, refresh R"),
    "noneS":   ("--CisReentry=none --CisStaticArm=true", "A/B disclosure: reentry=none, STATIC arm S"),
    "allowR":  ("--CisReentry=allow", "disclosure: reentry=allow (refill base band), refresh R"),
    "extendR": ("--CisReentry=extend", "disclosure: reentry=extend (z*∈{2.0,2.5,3.0} ladder), refresh R"),
}
SERIES_SHORT = {"S5_SPREAD": "s5", "S6_PAIR": "s6", "S7_BASKET": "s7", "S8_RVINDEX": "s8"}

HEADER = """# EXP-014 — CF-MR-004/HYP-002: FAITHFUL full-exit cross-instrument spread MR. PRICE-PRIMARY (4h).
# {arm_desc}
# Series {series}; arm {arm}. Native cTrader pending orders (Mode=3=NativeOrders); m1 fills own
# resolution. Faithful exit set = form-1 event-reversion + REFRESHING form-2 anchor-mean limit +
# horizon last-resort (min(48,3*HL) 4h bars). Multi-leg netting engine (reentry none|allow|extend).
# MR screen (6-stage) + native reversion estimands = analysis-only Python on this emission (L-01).
# Cutoffs = EXP-013 first-49% TRAIN fence (identical dataset). 0 counted reads, holdout sealed.

MODE=3
BALANCE=100000000
STRATEGY="cross_instrument_spread_mr"
STRATEGY_VALUE="5"
"""


def emit(series: str, arm: str) -> str:
    syms, mates = SERIES[series]
    extra, desc = ARMS[arm]
    lines = [HEADER.format(arm_desc=desc, series=series, arm=arm)]
    lines.append("SYMBOLS=(" + " ".join(syms) + ")")
    lines.append("DOMAINS=(4h)\n")
    lines.append("ANALYSIS_END=(")
    for s in syms:
        lines.append(f'  [{s}]="{CUTOFF_ISO[s]}"')
    lines.append(")")
    lines.append("BACKTEST_END=(")
    for s in syms:
        lines.append(f'  [{s}]="{CUTOFF_BT[s]}"')
    lines.append(")\n")
    lines.append("MODEL_ARGS_BY_SYMBOL=(")
    for s in syms:
        mate_str = ";".join(mates[s])
        lines.append(f'  [{s}]="--CisSeries={series} --BasketMates={mate_str} {extra}"')
    lines.append(")\n")
    lines.append("MODEL_ARGS=()  # constants are frozen model constants — no global params.")
    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    written = []
    for series in SERIES:
        for arm in ARMS:
            path = out_dir / f"EXP-014-{SERIES_SHORT[series]}-{arm}.conf"
            path.write_text(emit(series, arm))
            written.append(path.name)
    print(f"wrote {len(written)} confs:")
    for name in written:
        print(f"  {name}")


if __name__ == "__main__":
    main()
