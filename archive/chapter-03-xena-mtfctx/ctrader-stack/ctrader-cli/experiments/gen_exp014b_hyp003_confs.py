#!/usr/bin/env python3
"""Generate the EXP-014b (CF-MR-004 / HYP-003 streamlined S8 rerun) cTrader-CLI conf matrix.

amendment-003 (supersedes the HYP-002 EXP-014b confs — archive those). Changes:
  * S8 only (basket−RollingMedian_90), 11 cells.
  * DOMAIN axis {1h, 4h} — one conf per (domain, arm); DOMAINS=(<domain>) inside.
  * Single-leg exit = moving-mean form-2 + form-1 (NO horizon, NO fix/trail split — CisTrail
    deprecated/ignored). Reentry {none, allow, extend}, R only (no --CisStaticArm).
  * Both-leg variant (--CisBothLeg=true, reentry forced none): short A + long the equal-weight
    basket as a grouped spread position (audit-2 architecture; ~N× cost).

Conf basename == cTrader-CLI EXP_ID == output dir data/strategy_runs/<basename>/, so it MUST equal
lib.run_root: EXP-014b-{domain}-s8-{arm}. Fence = the EXP-013/014 first-49% TRAIN cutoffs, reused
verbatim (timestamp-based → identical for 1h and 4h). Phase-shift leak-tripwire confs generated on
demand only for an admitting cell (Stage 4). 0 counted reads, holdout sealed.

Run:  python3 gen_exp014b_hyp003_confs.py   (from tools/ctrader-cli/experiments/)
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
DOMAINS = ["1h", "4h"]
# Deviation-magnitude axis: z* tag -> value. z20 faithful default, z15 aggressive/less-extreme.
ZSTARS = {"z20": "2.0", "z15": "1.5"}
# Single-leg arms (reentry {none,allow,extend}, R only, moving-mean exit). Both-leg (2 entry
# mechanisms: limit-cancel-on-partial / market) is added by the Increment-B generator once the C#
# grouped-spread logic lands — not emitted here (would reference unimplemented --CisBothLeg* args).
ARMS = {
    "none":   "--CisReentry=none",
    "allow":  "--CisReentry=allow",
    "extend": "--CisReentry=extend",
}


def class_mates(sym: str) -> list[str]:
    cls = FX if sym in FX else IDX
    return [m for m in cls if m != sym]


HEADER = """# EXP-014b — CF-MR-004/HYP-003 streamlined S8 rerun (amendment-003). PRICE-PRIMARY ({domain}).
# {arm_desc}
# Series S8_RVINDEX (basket-median-90); domain {domain}; arm {arm}; z*={zval} (deviation magnitude).
# Native cTrader pending orders (Mode=3=NativeOrders); m1 fills own resolution. Exit set = form-1
# event-reversion + form-2 MOVING-MEAN limit (refresh to exp(anchorLog) each bar); NO horizon, NO
# fix/trail split. Entry band = z*·σ; reentry ladder derived {{z*, z*+0.5, z*+1.0}}.
# Availability = symmetry two-barrier (null 0.5) + tradability = frozen {domain} referee, analysis-only
# Python on this emission (L-01). Fence = EXP-013 first-49% TRAIN cutoffs. 0 counted reads, holdout sealed.

MODE=3
BALANCE=100000000
STRATEGY="cross_instrument_spread_mr"
STRATEGY_VALUE="5"
"""


def emit(domain: str, arm: str, ztag: str) -> str:
    zval = ZSTARS[ztag]
    extra = f"{ARMS[arm]} --CisZStar={zval}"
    is_primary = arm == "none" and ztag == "z20"
    desc = ("BINDING PRIMARY: single-leg, reentry=none, moving-mean exit, z*=2.0" if is_primary
            else f"disclosure: single-leg reentry={arm}, z*={zval}")
    lines = [HEADER.format(domain=domain, arm=arm, arm_desc=desc, zval=zval)]
    lines.append("SYMBOLS=(" + " ".join(S8_SYMS) + ")")
    lines.append(f"DOMAINS=({domain})\n")
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
    for domain in DOMAINS:
        for arm in ARMS:
            for ztag in ZSTARS:
                path = out_dir / f"EXP-014b-{domain}-s8-{arm}-{ztag}.conf"
                path.write_text(emit(domain, arm, ztag))
                written.append(path.name)
    print(f"wrote {len(written)} confs ({len(DOMAINS)} domains x {len(ARMS)} single-leg arms x "
          f"{len(ZSTARS)} z*, {len(S8_SYMS)} symbols each = {len(written) * len(S8_SYMS)} runs). "
          f"Both-leg confs added by the Increment-B generator.")
    for name in written:
        print(f"  {name}")


if __name__ == "__main__":
    main()
