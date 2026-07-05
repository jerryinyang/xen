"""EXP-018 data-analyst interrogation (analyst's own code; canonical xen estimands only).

Outputs python/experiments/EXP-018/results/analysis_summary.json with every number used in
analysis.md. Per-leg/episode/per-bar objects come from xen.adjudication; stats from
xen.evaluation. No local accounting (RealizedBps is the engine's; cost applied per leg L-02).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from xen.adjudication import assemble_multileg_bps, build_episodes, per_leg_net  # noqa: E402
from xen.evaluation import (block_bootstrap_ci, collapse_fraction, cost_sensitivity,  # noqa: E402
                            exposure_metrics, mde, split_by)

ROOT = Path(__file__).resolve().parents[3].parent  # repo root
RUNS = ROOT / "data" / "strategy_runs"
OUT = ROOT / "python/experiments/EXP-018/results/analysis_summary.json"

COST = {"US2000": 5.0, "NZDUSD": 2.0, "US500": 3.0, "USTEC": 4.0, "JP225": 4.0}
EP_BLOCK = 5   # design §6: moving-block bootstrap over time-ordered episodes, block 5
SEED = 18

CELLS = {  # cell key -> (conf stem, symbol, both_leg)
    "US2000_A_extend": ("EXP-018-4h-A-extend", "US2000", False),
    "NZDUSD_A_extend_negctl": ("EXP-018-4h-A-extend", "NZDUSD", False),
    "US2000_A_allow": ("EXP-018-4h-A-allow", "US2000", False),
    "US2000_B_extend": ("EXP-018-4h-B-extend", "US2000", False),
    "US500_blmkt_A": ("EXP-018-4h-blmkt-A", "US500", True),
}
ARMS = {"live": "", "rt": "-rt", "delay1": "-delay1", "shift": "-shift"}
HAS_SHIFT = {"US2000_A_extend", "NZDUSD_A_extend_negctl", "US2000_B_extend"}


def newest(stem: str, sym: str) -> Path:
    c = sorted((RUNS / stem).glob(f"cross_instrument_spread_mr_{sym.lower()}_4h_*"))
    if not c:
        raise SystemExit(f"missing run: {stem} {sym}")
    return c[-1]


def load(stem: str, sym: str):
    d = newest(stem, sym)
    return (pl.read_parquet(d / "positions.parquet").sort("SourceCloseTime"),
            pl.read_parquet(d / "cis_trades.parquet"), str(d))


def as_dt(col: pl.Series) -> np.ndarray:
    """build_episodes emits start/end times as ns-epoch floats — normalize to datetime64[ns]."""
    a = col.to_numpy()
    return a if np.issubdtype(a.dtype, np.datetime64) else a.astype("int64").astype("datetime64[ns]")


def ep_stats(ep: pl.DataFrame, label: str) -> dict:
    """Episode-level primary: completed (non-censored) episode nets, time-ordered."""
    comp = ep.filter(~pl.col("censored"))
    x = comp.get_column("net_bps").to_numpy()
    r = block_bootstrap_ci(x, block=EP_BLOCK, seed=SEED)
    return {
        "label": label, "n_episodes": int(comp.height), "n_censored_episodes": int(ep.height - comp.height),
        "mean_net_bps": r["stat"], "ci": r["ci"], "median_net_bps": float(np.median(x)) if len(x) else None,
        "mde_bps": mde(x, block=EP_BLOCK, seed=SEED) if len(x) > 1 else None,
        "total_net_bps": float(x.sum()) if len(x) else 0.0,
        "legs_per_episode_med": float(comp.get_column("n_legs").median()) if comp.height else None,
        "max_open_legs": int(ep.get_column("max_open_legs").max()) if ep.height else 0,
        "duration_bars_med": float(comp.get_column("n_bars").median()) if comp.height else None,
        "worst_mae_bps": float(ep.get_column("mae_bps").min()) if ep.height else None,
    }


def paired_destroy(x_live: np.ndarray, x_ctl: np.ndarray) -> dict:
    """Design §6: bootstrap each series, difference of mean draws + collapse fraction."""
    rng = np.random.default_rng(SEED)

    def draws(x):
        n = len(x)
        nb = int(np.ceil(n / EP_BLOCK))
        starts = rng.integers(0, max(n - EP_BLOCK, 1), size=(2000, nb))
        out = np.empty(2000)
        for b in range(2000):
            idx = (starts[b][:, None] + np.arange(EP_BLOCK)[None, :]).ravel()[:n] % n
            out[b] = x[idx].mean()
        return out

    dl, dc = draws(x_live), draws(x_ctl)
    diff = dl - dc
    return {"live_mean": float(x_live.mean()), "control_mean": float(x_ctl.mean()),
            "diff_mean": float(x_live.mean() - x_ctl.mean()),
            "diff_ci": [float(np.quantile(diff, .025)), float(np.quantile(diff, .975))],
            "collapse_fraction": collapse_fraction(float(x_live.mean()), float(x_ctl.mean()))}


def single_leg_cell(stem: str, sym: str) -> dict:
    out = {}
    pos, cis, rundir = load(stem, sym)
    out["run_dir"] = rundir
    cost = COST[sym]
    series = assemble_multileg_bps(pos, cis, cost_bps=cost)
    ep = build_episodes(pos, cis, cost_bps=cost)
    out["episodes"] = ep_stats(ep, f"{sym} live")
    out["exposure"] = exposure_metrics(series, real_open=pos.get_column("RealOpen").to_numpy())
    out["censored_mtm_bps"] = series.censored_mtm_bps
    out["n_censored_legs"] = series.n_censored

    # per-leg lens
    legs = per_leg_net(cis.filter(pl.col("RealizedBps").is_finite()), cost_bps=cost)
    g = legs.get_column("RealizedBps").to_numpy()
    nl = legs.get_column("NetBps").to_numpy()
    out["per_leg"] = {"n": len(nl), "gross_mean": float(g.mean()), "net_mean": float(nl.mean()),
                      "net_median": float(np.median(nl)),
                      "q01": float(np.quantile(nl, .01)), "q05": float(np.quantile(nl, .05)),
                      "q95": float(np.quantile(nl, .95)), "q99": float(np.quantile(nl, .99)),
                      "by_level": {str(k): {"n": int(v.height), "net_mean": float(v.get_column("NetBps").mean())}
                                   for k, v in legs.group_by("LadderLevel")}}
    out["exit_reasons"] = {r["ExitReason"]: r["len"]
                           for r in cis.group_by("ExitReason").agg(pl.len()).to_dicts()}
    # cost curve (per leg)
    out["cost_curve"] = cost_sensitivity(g, [0.5 * cost, cost, 2 * cost, 3 * cost],
                                         block=EP_BLOCK, seed=SEED)
    # concentration: episode nets without top winners
    comp = ep.filter(~pl.col("censored")).get_column("net_bps").to_numpy()
    s = np.sort(comp)[::-1]
    out["concentration"] = {"total": float(comp.sum()),
                            "minus_top1": float(comp.sum() - s[:1].sum()),
                            "minus_top3": float(comp.sum() - s[:3].sum()),
                            "minus_top5": float(comp.sum() - s[:5].sum())}
    # year + regime splits (episode start regime from emitted <=t-1 state; year by episode END §2)
    compdf = ep.filter(~pl.col("censored"))
    x = compdf.get_column("net_bps").to_numpy()
    years = as_dt(compdf.get_column("end_time")).astype("datetime64[Y]").astype(str)
    out["year_split"] = split_by(x, years, block=EP_BLOCK, seed=SEED)
    pt = pos.select(["SourceCloseTime", "TrendZ", "VolRegime"])
    pt_times = pt.get_column("SourceCloseTime").to_numpy().astype("datetime64[ns]")
    starts = as_dt(compdf.get_column("start_time"))
    j = np.clip(np.searchsorted(pt_times, starts), 0, pt.height - 1)
    tz = np.abs(pt.get_column("TrendZ").to_numpy()[j])
    vol = pt.get_column("VolRegime").to_numpy()[j]
    fin = np.isfinite(tz)
    if fin.sum() >= 6:
        terc = np.digitize(tz[fin], np.quantile(tz[fin], [1 / 3, 2 / 3]))
        out["trend_tercile_split"] = split_by(x[fin], terc.astype(str), block=EP_BLOCK, seed=SEED)
    out["vol_regime_split"] = split_by(x, vol.astype(str), block=EP_BLOCK, seed=SEED)
    out["_ep_net_completed"] = comp.tolist()
    return out


def bothleg_cell(stem: str, sym: str) -> dict:
    """US500 both-leg: episode == spread group (reentry none). Group net = A_bps +
    mean(mate_bps) − weighted cost (A cost + mean mate cost), matching the engine's
    spread-weighted MTM convention (A weight 1, each mate 1/n)."""
    out = {}
    pos, cis, rundir = load(stem, sym)
    out["run_dir"] = rundir
    live = cis.filter(pl.col("RealizedBps").is_finite())
    groups = []
    for (gid,), gdf in live.group_by("SpreadPositionId", maintain_order=True):
        a = gdf.filter(pl.col("LegSymbol") == sym)
        m = gdf.filter(pl.col("LegSymbol") != sym)
        if a.height != 1 or m.height == 0:
            continue
        a_bps = float(a.get_column("RealizedBps")[0])
        m_bps = float(m.get_column("RealizedBps").mean())
        mate_cost = float(np.mean([COST[s] for s in m.get_column("LegSymbol").to_list()]))
        net = a_bps + m_bps - (COST[sym] + mate_cost)
        groups.append({"gid": gid, "net": net, "gross": a_bps + m_bps,
                       "end": a.get_column("ExitTime")[0], "n_legs": int(gdf.height),
                       "reason": a.get_column("ExitReason")[0],
                       "bars": int(a.get_column("BarsHeld")[0])})
    gdf = pl.DataFrame(groups).sort("end")
    x = gdf.get_column("net").to_numpy()
    r = block_bootstrap_ci(x, block=EP_BLOCK, seed=SEED)
    out["episodes"] = {"label": f"{sym} both-leg live", "n_episodes": len(x),
                       "mean_net_bps": r["stat"], "ci": r["ci"],
                       "median_net_bps": float(np.median(x)),
                       "mde_bps": mde(x, block=EP_BLOCK, seed=SEED),
                       "total_net_bps": float(x.sum()),
                       "duration_bars_med": float(gdf.get_column("bars").median())}
    out["exit_reasons"] = {r["reason"]: r["len"]
                           for r in gdf.group_by("reason").agg(pl.len()).to_dicts()}
    g = gdf.get_column("gross").to_numpy()
    base = COST[sym] + float(np.mean([COST[s] for s in ("USTEC", "US2000", "JP225")]))
    out["cost_curve"] = cost_sensitivity(g, [0.5 * base, base, 2 * base, 3 * base],
                                         block=EP_BLOCK, seed=SEED)
    years = gdf.get_column("end").dt.year().to_numpy().astype(str)
    out["year_split"] = split_by(x, years, block=EP_BLOCK, seed=SEED)
    s = np.sort(x)[::-1]
    out["concentration"] = {"total": float(x.sum()), "minus_top1": float(x.sum() - s[:1].sum()),
                            "minus_top3": float(x.sum() - s[:3].sum()),
                            "minus_top5": float(x.sum() - s[:5].sum())}
    out["n_censored_groups"] = int(cis.filter(pl.col("Censored") == 1).get_column("SpreadPositionId").n_unique())
    out["_ep_net_completed"] = x.tolist()
    return out


def control_eps(stem_arm: str, sym: str, both: bool) -> np.ndarray:
    pos, cis, _ = load(stem_arm, sym)
    if not both:
        ep = build_episodes(pos, cis, cost_bps=COST[sym])
        return ep.filter(~pl.col("censored")).get_column("net_bps").to_numpy()
    live = cis.filter(pl.col("RealizedBps").is_finite())
    nets = []
    for (gid,), gdf in live.group_by("SpreadPositionId", maintain_order=True):
        a = gdf.filter(pl.col("LegSymbol") == sym)
        m = gdf.filter(pl.col("LegSymbol") != sym)
        if a.height != 1 or m.height == 0:
            continue
        mate_cost = float(np.mean([COST[s] for s in m.get_column("LegSymbol").to_list()]))
        nets.append(float(a.get_column("RealizedBps")[0]) + float(m.get_column("RealizedBps").mean())
                    - (COST[sym] + mate_cost))
    return np.array(nets)


def main() -> None:
    summary = {}
    for key, (stem, sym, both) in CELLS.items():
        cell = bothleg_cell(stem, sym) if both else single_leg_cell(stem, sym)
        x_live = np.array(cell.pop("_ep_net_completed"))
        for arm, suffix in (("rt", "-rt"), ("delay1", "-delay1"), ("shift", "-shift")):
            if arm == "shift" and key not in HAS_SHIFT:
                continue
            x_ctl = control_eps(stem + suffix, sym, both)
            cell[f"{arm}_read"] = paired_destroy(x_live, x_ctl) | {"n_control_episodes": len(x_ctl)}
        summary[key] = cell
        print(key, "done:", cell["episodes"]["n_episodes"], "episodes,",
              round(cell["episodes"]["mean_net_bps"], 1), "bps/ep, CI",
              [round(v, 1) for v in cell["episodes"]["ci"]])
    OUT.write_text(json.dumps(summary, indent=1, default=str))
    print("->", OUT)


if __name__ == "__main__":
    main()
