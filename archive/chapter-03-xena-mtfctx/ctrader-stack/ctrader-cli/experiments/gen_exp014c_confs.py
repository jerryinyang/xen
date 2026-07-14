#!/usr/bin/env python3
"""Generate the EXP-014c (CF-MR-004 / HYP-004 lean bracket exit-set) cTrader-CLI conf matrix.

amendment-004: 4h only, single-leg, S8 only. NEW axis = EXIT SET (--CisExitSet):
  e1 = frozen_tp     (TP frozen at the entry-time anchor; no SL, no time-stop, form-1 disabled)
  e2 = frozen_tp_sl  (e1 + SL frozen at the symmetric outward barrier o±D)
  e3 = bracket       (e2 + time-stop ceil(3*HL_entry) domain bars, cap 48)
E0 (moving-mean baseline) is NOT emitted here — analysis reuses the EXP-014b 4h emissions.
Reentry {none,allow,extend} and z* {2.0,1.5} retained as characterisation axes.
PRIMARY = (e3, none, z20) on JP225+EURUSD; its phase-shift twin (--BasketPhaseShiftHours=60)
is the binding leak tripwire. Fence = EXP-013 first-49% TRAIN cutoffs verbatim. 0 counted reads.

Run:  python3 gen_exp014c_confs.py   (from tools/ctrader-cli/experiments/)
"""
from pathlib import Path

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
S8_SYMS = FX + IDX
SERIES = "S8_RVINDEX"
DOMAIN = "4h"
EXITS = {"e1": "frozen_tp", "e2": "frozen_tp_sl", "e3": "bracket"}
REENTRY = ["none", "allow", "extend"]
ZSTARS = {"z20": "2.0", "z15": "1.5"}


def class_mates(sym: str) -> list[str]:
    cls = FX if sym in FX else IDX
    return [m for m in cls if m != sym]


HEADER = """# EXP-014c — CF-MR-004/HYP-004 lean bracket exit-set (amendment-004). PRICE-PRIMARY (4h).
# {desc}
# Series S8_RVINDEX; 4h; exit_set={exit_mode} ({etag}); reentry={reentry}; z*={zval}.{shift_note}
# Native cTrader pending orders (Mode=3=NativeOrders); m1 fills. E1-E3: per-leg bracket FROZEN at
# the entry fill tick (TP at the entry-time anchor; E2/E3 + SL at outward barrier o+/-D; E3 + hard
# time-stop ceil(3*HL_entry) cap 48). Same-bar TP/SL fills required (no next-bar activation lag).
# form-1 + moving form-2 fully bypassed for E1-E3. Fence = EXP-013 first-49% TRAIN cutoffs.
# 0 counted reads, holdout sealed. Analysis-only Python on this emission (L-01).

MODE=3
BALANCE=100000000
STRATEGY="cross_instrument_spread_mr"
STRATEGY_VALUE="5"
"""


def emit(etag: str, reentry: str, ztag: str, shift: bool = False) -> str:
    zval = ZSTARS[ztag]
    exit_mode = EXITS[etag]
    extra = f"--CisReentry={reentry} --CisZStar={zval} --CisExitSet={exit_mode}"
    shift_note = ""
    if shift:
        extra += " --BasketPhaseShiftHours=60"
        shift_note = ("\n# PHASE-SHIFT LEAK TRIPWIRE twin (BasketPhaseShiftHours=60): binding per-cell "
                      "net-collapse control for any Holm-admitting PRIMARY cell (design SS5).")
    is_primary = etag == "e3" and reentry == "none" and ztag == "z20"
    desc = ("BINDING PRIMARY family: exit=e3 bracket, reentry=none, z*=2.0 "
            "(prespecified primary cells: JP225, EURUSD)" if is_primary
            else f"disclosure/characterisation: exit={etag}, reentry={reentry}, z*={zval}")
    lines = [HEADER.format(desc=desc, exit_mode=exit_mode, etag=etag, reentry=reentry,
                           zval=zval, shift_note=shift_note)]
    lines.append("SYMBOLS=(" + " ".join(S8_SYMS) + ")")
    lines.append(f"DOMAINS=({DOMAIN})\n")
    lines.append("ANALYSIS_END=(")
    for s in S8_SYMS:
        lines.append(f'  [{s}]="{CUTOFF_ISO[s]}"')
    lines.append(")")
    lines.append("BACKTEST_END=(")
    for s in S8_SYMS:
        lines.append(f'  [{s}]="{CUTOFF_BT[s]}"')
    lines.append(")\n")
    lines.append("MODEL_ARGS_BY_SYMBOL=(")
    for s in S8_SYMS:
        mate_str = ";".join(class_mates(s))
        lines.append(f'  [{s}]="--CisSeries={SERIES} --BasketMates={mate_str} {extra}"')
    lines.append(")\n")
    lines.append("MODEL_ARGS=()  # constants are frozen model constants — no global params.")
    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    written = []
    for etag in EXITS:
        for reentry in REENTRY:
            for ztag in ZSTARS:
                path = out_dir / f"EXP-014c-4h-s8-{etag}-{reentry}-{ztag}.conf"
                path.write_text(emit(etag, reentry, ztag))
                written.append(path.name)
    shift_path = out_dir / "EXP-014c-4h-s8-e3-none-z20-shift.conf"
    shift_path.write_text(emit("e3", "none", "z20", shift=True))
    written.append(shift_path.name)
    print(f"wrote {len(written)} confs (3 exits x 3 reentry x 2 z* + PRIMARY shift twin; "
          f"{len(S8_SYMS)} symbols each = {len(written) * len(S8_SYMS)} runs).")
    for name in written:
        print(f"  {name}")


if __name__ == "__main__":
    main()
