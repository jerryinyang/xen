#!/usr/bin/env python3
"""Generate the EXP-014b (CF-MR-004 / HYP-002 redo) cTrader-CLI conf matrix.

EXP-014b is the proposal-faithful redo of EXP-014 (downgraded CONFOUNDED): the unspecified
horizon time-stop is REMOVED (newer.md: "no other exit methods enforced on the positions"),
and the form-2 exit becomes a first-class /TRAIL axis — OFF = fixed entry-referential exit
(EntryFill·exp(dir·band), locked at open; the faithful design) / ON = trailing moving-anchor
mean (the EXP-014 refresh, kept as disclosure). Exit set = form-1 event-reversion + form-2
(fixed|trailing). Still-open legs at the fence are emitted censored (open_at_end).

FULL-CROSS arm matrix (operator decision): reentry {none,allow,extend} × entry-recalc {R,S} ×
trail {fix,trail} = 12 arms/series. Binding PRIMARY = none-R-fix. All arms reuse the EXP-013
first-49% TRAIN fence (identical dataset/cutoffs). Phase-shift leak-tripwire confs generated on
demand only for an admitting cell (Stage 4).

Run:  python3 gen_exp014b_confs.py   (from tools/ctrader-cli/experiments/)
"""
from itertools import product
from pathlib import Path

# --- shared first-49% TRAIN fence (per symbol) — reused verbatim from EXP-013/EXP-014 ------- #
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
SERIES_SHORT = {"S5_SPREAD": "s5", "S6_PAIR": "s6", "S7_BASKET": "s7", "S8_RVINDEX": "s8"}

# --- full-cross arm matrix: reentry × recalc × trail = 12 arms ------------------------------ #
REENTRY = {"none": "", "allow": "", "extend": ""}   # value via --CisReentry
RECALC = {"R": "", "S": "--CisStaticArm=true"}       # R = refresh/bar (default), S = place-once
TRAIL = {"fix": "", "trail": "--CisTrail=true"}      # fix = entry-referential locked, trail = moving anchor
PRIMARY = ("none", "R", "fix")


def arm_name(reentry: str, recalc: str, trail: str) -> str:
    return f"{reentry}{recalc}-{trail}"


def arm_args(reentry: str, recalc: str, trail: str) -> str:
    parts = [f"--CisReentry={reentry}", RECALC[recalc], TRAIL[trail]]
    return " ".join(p for p in parts if p)


HEADER = """# EXP-014b — CF-MR-004/HYP-002 REDO: proposal-faithful cross-instrument spread MR. PRICE-PRIMARY (4h).
# {arm_desc}
# Series {series}; arm {arm}. Native cTrader pending orders (Mode=3=NativeOrders); m1 fills own
# resolution. Faithful exit set = form-1 event-reversion + form-2 ({trail_desc}). NO horizon
# (newer.md: no other exits). Still-open legs at the fence emitted censored (open_at_end).
# Multi-leg netting engine (reentry none|allow|extend). MR screen (6-stage) + native reversion
# estimands = analysis-only Python on this emission (L-01). Cutoffs = EXP-013 first-49% TRAIN
# fence (identical dataset). 0 counted reads, holdout sealed.

MODE=3
BALANCE=100000000
STRATEGY="cross_instrument_spread_mr"
STRATEGY_VALUE="5"
"""


def emit(series: str, reentry: str, recalc: str, trail: str) -> str:
    syms, mates = SERIES[series]
    arm = arm_name(reentry, recalc, trail)
    extra = arm_args(reentry, recalc, trail)
    is_primary = (reentry, recalc, trail) == PRIMARY
    desc = ("BINDING PRIMARY: faithful, reentry=none, refresh R, FIXED exit" if is_primary
            else f"disclosure: reentry={reentry}, {'refresh R' if recalc == 'R' else 'STATIC S'}, "
                 f"{'FIXED' if trail == 'fix' else 'TRAILING'} exit")
    trail_desc = "fixed entry-referential" if trail == "fix" else "trailing moving-anchor"
    lines = [HEADER.format(arm_desc=desc, series=series, arm=arm, trail_desc=trail_desc)]
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
        for reentry, recalc, trail in product(REENTRY, RECALC, TRAIL):
            arm = arm_name(reentry, recalc, trail)
            path = out_dir / f"EXP-014b-{SERIES_SHORT[series]}-{arm}.conf"
            path.write_text(emit(series, reentry, recalc, trail))
            written.append(path.name)
    print(f"wrote {len(written)} confs ({len(SERIES)} series x 12 arms):")
    for name in written:
        print(f"  {name}")


if __name__ == "__main__":
    main()
