"""SPDR-012 analyst — script 5: what are the two regime arms actually partitioning?

V-REGIME  = rolling-median split of rv20 (a slow LEVEL classifier).
V-REGIME-HMM = 2-state Gaussian HMM on the clock log-return series, causal forward filter.

Probes, all on the per-origin emission:
  1. cross-tab of the two states, per clock/band.
  2. what each state responds to: mean/median of rv20 percentile, |r_t| percentile,
     parkinson percentile in each state.
  3. how well |r_t| alone (last bar's magnitude) reproduces each state (AUC).
  4. run-length distributions.
  5. the HMM gap decomposed: is the extra separation coming from a smaller HIGH state
     (more selective) rather than a better one?
  6. state-conditional next-|move| distributions incl. medians and tails.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"

pl.Config.set_tbl_rows(100)
pl.Config.set_tbl_width_chars(250)


def auc(score, label):
    ok = np.isfinite(score) & np.isfinite(label)
    s, l = score[ok], label[ok]
    if len(np.unique(l)) < 2:
        return float("nan")
    r = stats.rankdata(s)
    n1 = (l == 1).sum(); n0 = (l == 0).sum()
    return float((r[l == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def runlen(states):
    out = {}
    s = states[states >= 0]
    if len(s) == 0:
        return {0: np.nan, 1: np.nan}
    chg = np.flatnonzero(np.diff(s) != 0)
    bounds = np.concatenate([[-1], chg, [len(s) - 1]])
    lens = np.diff(bounds)
    vals = s[bounds[1:]]
    for k in (0, 1):
        m = vals == k
        out[k] = float(np.mean(lens[m])) if m.any() else np.nan
    return out


def main() -> None:
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    rows = []
    for (sym, clock, band), g in v.group_by(["symbol", "clock", "band"], maintain_order=True):
        g = g.sort("slot_start")
        rs = g["regime_state"].to_numpy()
        hs = g["hmm_state"].to_numpy()
        ok = (rs >= 0) & (hs >= 0)
        if ok.sum() < 100:
            continue
        rs2, hs2 = rs[ok], hs[ok]
        y = g["target_abs_oo"].to_numpy()[ok]
        rv = g["rv20"].to_numpy()[ok]
        ar = g["abs_r"].to_numpy()[ok]
        pk = g["parkinson"].to_numpy()[ok]
        pct = lambda a: stats.rankdata(a) / len(a)
        rl_r, rl_h = runlen(rs2), runlen(hs2)
        r = {
            "symbol": sym, "clock": clock, "band": band, "n": int(ok.sum()),
            "frac_high_markov": float(rs2.mean()), "frac_high_hmm": float(hs2.mean()),
            "agreement": float((rs2 == hs2).mean()),
            "markov_high_rv20pct": float(np.mean(pct(rv)[rs2 == 1])),
            "hmm_high_rv20pct": float(np.mean(pct(rv)[hs2 == 1])),
            "markov_high_absrpct": float(np.mean(pct(ar)[rs2 == 1])),
            "hmm_high_absrpct": float(np.mean(pct(ar)[hs2 == 1])),
            "markov_high_parkpct": float(np.mean(pct(pk)[rs2 == 1])),
            "hmm_high_parkpct": float(np.mean(pct(pk)[hs2 == 1])),
            "auc_rv20_for_markov": auc(rv, rs2),
            "auc_rv20_for_hmm": auc(rv, hs2),
            "auc_absr_for_markov": auc(ar, rs2),
            "auc_absr_for_hmm": auc(ar, hs2),
            "mean_runlen_markov_high": rl_r[1], "mean_runlen_markov_low": rl_r[0],
            "mean_runlen_hmm_high": rl_h[1], "mean_runlen_hmm_low": rl_h[0],
            "gap_markov": float(np.nanmean(y[rs2 == 1]) - np.nanmean(y[rs2 == 0])),
            "gap_hmm": float(np.nanmean(y[hs2 == 1]) - np.nanmean(y[hs2 == 0])),
            "medgap_markov": float(np.nanmedian(y[rs2 == 1]) - np.nanmedian(y[rs2 == 0])),
            "medgap_hmm": float(np.nanmedian(y[hs2 == 1]) - np.nanmedian(y[hs2 == 0])),
            "mean_y": float(np.nanmean(y)),
            "ic_markov_state": float(stats.spearmanr(rs2, y, nan_policy="omit").statistic),
            "ic_hmm_state": float(stats.spearmanr(hs2, y, nan_policy="omit").statistic),
            # 4-way cross-tab conditional means
            "y_HH": float(np.nanmean(y[(rs2 == 1) & (hs2 == 1)])) if ((rs2 == 1) & (hs2 == 1)).sum() > 10 else np.nan,
            "y_HL": float(np.nanmean(y[(rs2 == 1) & (hs2 == 0)])) if ((rs2 == 1) & (hs2 == 0)).sum() > 10 else np.nan,
            "y_LH": float(np.nanmean(y[(rs2 == 0) & (hs2 == 1)])) if ((rs2 == 0) & (hs2 == 1)).sum() > 10 else np.nan,
            "y_LL": float(np.nanmean(y[(rs2 == 0) & (hs2 == 0)])) if ((rs2 == 0) & (hs2 == 0)).sum() > 10 else np.nan,
            "n_HH": int(((rs2 == 1) & (hs2 == 1)).sum()), "n_HL": int(((rs2 == 1) & (hs2 == 0)).sum()),
            "n_LH": int(((rs2 == 0) & (hs2 == 1)).sum()), "n_LL": int(((rs2 == 0) & (hs2 == 0)).sum()),
        }
        rows.append(r)
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "out_regime_partition.csv")

    print("=== what each arm calls HIGH (median over cells) ===")
    print(df.group_by(["band", "clock"]).agg([
        pl.len().alias("cells"),
        pl.col("frac_high_markov").median().round(3),
        pl.col("frac_high_hmm").median().round(3),
        pl.col("agreement").median().round(3),
        pl.col("markov_high_rv20pct").median().round(3),
        pl.col("hmm_high_rv20pct").median().round(3),
        pl.col("markov_high_absrpct").median().round(3),
        pl.col("hmm_high_absrpct").median().round(3),
    ]).sort(["clock", "band"]).to_pandas().to_string())

    print("\n=== which single variable reproduces each state (AUC) ===")
    print(df.group_by(["band", "clock"]).agg([
        pl.col("auc_rv20_for_markov").median().round(3),
        pl.col("auc_absr_for_markov").median().round(3),
        pl.col("auc_rv20_for_hmm").median().round(3),
        pl.col("auc_absr_for_hmm").median().round(3),
    ]).sort(["clock", "band"]).to_pandas().to_string())

    print("\n=== persistence: mean run length in bars ===")
    print(df.group_by(["band", "clock"]).agg([
        pl.col("mean_runlen_markov_high").median().round(2),
        pl.col("mean_runlen_markov_low").median().round(2),
        pl.col("mean_runlen_hmm_high").median().round(2),
        pl.col("mean_runlen_hmm_low").median().round(2),
    ]).sort(["clock", "band"]).to_pandas().to_string())

    print("\n=== separation: mean gap, median gap, gap relative to the cell's own mean |move| ===")
    d2 = df.with_columns([
        (pl.col("gap_markov") / pl.col("mean_y")).alias("relgap_markov"),
        (pl.col("gap_hmm") / pl.col("mean_y")).alias("relgap_hmm"),
        (pl.col("medgap_markov") / pl.col("mean_y")).alias("relmedgap_markov"),
        (pl.col("medgap_hmm") / pl.col("mean_y")).alias("relmedgap_hmm"),
    ])
    print(d2.group_by(["band", "clock"]).agg([
        pl.col("gap_markov").median().round(1), pl.col("gap_hmm").median().round(1),
        pl.col("medgap_markov").median().round(1), pl.col("medgap_hmm").median().round(1),
        pl.col("relgap_markov").median().round(3), pl.col("relgap_hmm").median().round(3),
        pl.col("relmedgap_markov").median().round(3), pl.col("relmedgap_hmm").median().round(3),
        pl.col("ic_markov_state").median().round(3), pl.col("ic_hmm_state").median().round(3),
    ]).sort(["clock", "band"]).to_pandas().to_string())

    print("\n=== 2x2 cross-tab: mean next |move| by (markov, hmm) state ===")
    print(d2.group_by(["band", "clock"]).agg([
        pl.col("y_LL").median().round(1), pl.col("y_LH").median().round(1),
        pl.col("y_HL").median().round(1), pl.col("y_HH").median().round(1),
        pl.col("n_LL").median(), pl.col("n_LH").median(),
        pl.col("n_HL").median(), pl.col("n_HH").median(),
    ]).sort(["clock", "band"]).to_pandas().to_string())

    print("\n=== per-cell detail (CONFIRM H1) ===")
    print(d2.filter((pl.col("band") == "CONFIRM") & (pl.col("clock") == "H1"))
          .select("symbol", "frac_high_markov", "frac_high_hmm", "agreement",
                  "gap_markov", "gap_hmm", "medgap_markov", "medgap_hmm",
                  "ic_markov_state", "ic_hmm_state", "mean_y").to_pandas().to_string())


if __name__ == "__main__":
    main()
