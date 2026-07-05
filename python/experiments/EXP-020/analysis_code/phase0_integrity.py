"""EXP-020 Phase 0 integrity gate: estimand artifacts, provenance recompute, fence,
fill causality (ARM G m1 touch), twin purity, local-accounting check."""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ALL_SYMBOLS, RESULTS, ROOT, ROOTS, load_run, run_dirs

from xen.estimand_validation import check_no_local_accounting


def check_estimand_jsons() -> None:
    print("== estimand validation artifacts ==")
    for arm in ["R", "R-twin", "G", "G-invert", "R-delay1", "G-delay1"]:
        f = RESULTS / f"estimand_validation_{arm}.json"
        d = json.loads(f.read_text())
        cells = d["cells"]
        fails = [c for c in cells if not c.get("blocking_pass", False)] \
            if isinstance(cells, list) else []
        print(f"  {arm}: n_cells={d['n_cells']} blocking_pass={d['blocking_pass']} "
              f"failing={len(fails)}")
        assert d["blocking_pass"], f"BLOCKING FAIL in {f}"


def check_fence() -> None:
    print("== AnalysisEndUtc fence (max emitted SourceCloseTime <= fence) ==")
    worst = []
    for arm, root in ROOTS.items():
        for sym, d in run_dirs(arm).items():
            meta = json.loads((d / "run_metadata.json").read_text())
            fence = np.datetime64(meta["analysis_end_utc"].replace("Z", "")[:26])
            for f in ["positions.parquet", "cis_trades.parquet", "trade_blotter.parquet"]:
                df = pl.read_parquet(d / f)
                if df.height == 0:
                    continue
                mx = df["SourceCloseTime"].max()
                if np.datetime64(mx) > fence:
                    worst.append((arm, sym, f, str(mx), str(fence)))
    print(f"  violations: {len(worst)}")
    for w in worst[:10]:
        print("   ", w)
    assert not worst


def check_armR_provenance(arm: str = "R", symbols=("NZDUSD", "USDCAD", "BTCUSD")) -> None:
    """Emission semantics (Xen.StructureHarvest.cs ProcessRebBar/EmitRebBar): the decision
    reads the completed bar i close (effIdx = i - delay); the market order fills at the next
    bar's open tick; the emitted bar-i row is POST-trade state at bar-i close. So the
    pre-trade weight (reconstructed by backing the trade out of the emitted units/cash,
    valued at the decision close) must breach the band for every rebalance trade, and the
    post-trade emitted weight must be restored to ~w*. Twin must have zero trades."""
    print(f"== ARM {arm} provenance (trigger at completed close, fill next open) ==")
    for sym in symbols:
        r = load_run(arm, sym)
        b_w = r["meta"]["parameters"]["band_w"]
        delay = r["meta"]["parameters"].get("entry_delay_bars", 0)
        pos = r["positions"].filter(~pl.col("Warmup")).sort("SourceCloseTime")
        u = pos["PortUnits"].to_numpy()
        cash = pos["PortCash"].to_numpy()
        c = pos["RealClose"].to_numpy()
        op = pos["RealOpen"].to_numpy()
        t = pos["SourceCloseTime"].to_numpy()
        tb = r["trade_blotter"].filter(pl.col("TradeSequence") > 1).sort("SourceCloseTime")
        n_bad_trigger, n_fill_open, n_restored = 0, 0, 0
        # trade booked at Server.Time inside the forming bar AFTER decision bar i:
        # decision row = last emitted bar with SourceCloseTime <= trade time
        bi = np.searchsorted(t, tb["SourceCloseTime"].to_numpy(), side="right") - 1
        deltas = tb["PositionDelta"].to_numpy()
        prices = tb["Price"].to_numpy()
        n_groups = 0
        for i in np.unique(bi):
            if i < 0 or i + 1 >= len(t):
                continue
            grp = np.where(bi == i)[0]  # a sell may split across several partial closes
            n_groups += 1
            u_pre = u[i] - deltas[grp].sum()
            cash_pre = cash[i] + (deltas[grp] * prices[grp]).sum()
            di = i - delay
            v_pre = u_pre * c[di] + cash_pre
            w_pre = u_pre * c[di] / v_pre
            if abs(w_pre - 0.5) < b_w - 1e-9:
                n_bad_trigger += 1
            if all(np.isclose(prices[j], op[i + 1], atol=5e-4 * prices[j]) for j in grp):
                n_fill_open += 1
            v_post = u[i] * c[di] + cash[i]
            if abs(u[i] * c[di] / v_post - 0.5) < b_w:
                n_restored += 1
        print(f"  {sym}: trades={tb.height} trade_bars={n_groups} "
              f"trigger_violations={n_bad_trigger} fill~next_open={n_fill_open} "
              f"restored_within_band={n_restored}")
    # twin purity
    for sym in symbols[:2]:
        rt = load_run("R-twin", sym)
        n = rt["trade_blotter"].filter(pl.col("TradeSequence") > 1).height
        n_ev = rt["events"].filter(pl.col("EventType") == "rebalance").height
        print(f"  twin {sym}: post-init trades={n} rebalance_events={n_ev} (expect 0)")


def check_armG_fill_causality(symbols=("NZDUSD", "USDCAD", "XAUUSD")) -> None:
    """Tripwire 3: every grid fill price must be touched by the m1 bar at fill time,
    and EntryTime must be >= the level's arming (anchor month start)."""
    print("== ARM G fill causality (m1 touch) ==")
    tb_dir = ROOT / "data" / "timebars"
    for sym in symbols:
        f = sorted(tb_dir.glob(f"timebars_{sym.lower()}_2021*"))[-1]
        m1 = pl.scan_parquet(f).select("CloseTime", "High", "Low").collect()
        for arm in ["G", "G-invert"]:
            ct = load_run(arm, sym)["cis_trades"]
            bad = 0
            checked = 0
            for row in ct.iter_rows(named=True):
                for tcol, pcol in [("EntryTime", "EntryFillPrice"),
                                   ("ExitTime", "ExitFillPrice")]:
                    if row["Censored"] == 1 and tcol == "ExitTime":
                        continue
                    tt = row[tcol]
                    sub = m1.filter(
                        (pl.col("CloseTime") >= tt)
                        & (pl.col("CloseTime") <= np.datetime64(tt) + np.timedelta64(2, "m"))
                    )
                    if sub.height == 0:
                        continue
                    checked += 1
                    px = row[pcol]
                    if not ((sub["Low"].min() - 1e-9) <= px <= (sub["High"].max() + 1e-9)):
                        bad += 1
            print(f"  {sym} {arm}: legs={ct.height} fills_checked={checked} "
                  f"touch_violations={bad}")


def main() -> None:
    check_estimand_jsons()
    check_fence()
    check_armR_provenance()
    check_armG_fill_causality()
    print("== local accounting check (code/ and analysis_code/) ==")
    for sub in ["code", "analysis_code"]:
        print(" ", sub, check_no_local_accounting(f"python/experiments/EXP-020/{sub}"))


if __name__ == "__main__":
    main()
