"""The eight mandatory first-pass arms (design §4, AMENDMENT-A2).

Every arm emits long-format metric rows per (symbol, clock, band). Nothing is dropped for
being small: a thin cell reports its numbers and carries an UNPOWERED label (design §6.3/§6.5).
Interpretation bands are labels, never gates.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from config import (
    DESIGN_END,
    DESIGN_START,
    NS,
    PERSIST_LAGS,
    V_LEVEL_PRIMARY_MODEL,
    V_LEVEL_PRIMARY_TARGET,
)
from pipeline import MEASURES, TARGETS, Cell
from stats_core import (
    ar1_half_life,
    autocorr,
    band_gap,
    band_gap_detected,
    band_ic,
    band_ic_detected,
    boot_group_mean_diff,
    boot_mean,
    boot_rank_corr,
    mde_from_se,
    mde_ic,
    r2_oos,
    spearman,
)

PRIMARY_MODEL_KEY = f"vlevel_{V_LEVEL_PRIMARY_MODEL}__{V_LEVEL_PRIMARY_TARGET}"
_MODEL_KEYS = ("vlevel_ridge", "vlevel_ols", "vlevel_ewma")


def _row(cell: Cell, band: str, arm: str, metric: str, value, **kw) -> dict:
    out = {
        "symbol": cell.symbol, "clock": cell.clock, "band": band, "arm": arm,
        "metric": metric, "model": kw.pop("model", ""), "target": kw.pop("target", ""),
        "value": float(value) if value is not None and np.isfinite(value) else None,
        "ci_low": None, "ci_high": None, "se": None, "se_median": None,
        "n_obs": kw.pop("n_obs", None), "n_dates": kw.pop("n_dates", None),
        "mde": None, "band_label": kw.pop("band_label", ""),
        "band_label_detected": kw.pop("band_label_detected", ""),
        "target_overlaps_feature": kw.pop("target_overlaps_feature", False),
        "note": kw.pop("note", ""),
    }
    boot = kw.pop("boot", None)
    if boot is not None:
        out["ci_low"] = _f(boot.ci_low)
        out["ci_high"] = _f(boot.ci_high)
        out["se"] = _f(boot.se)
        out["se_median"] = _f(boot.se_median)
        out["n_obs"] = boot.n_obs
        out["n_dates"] = boot.n_dates
        out["_ci_grid"] = boot.grid          # stripped into results/ci_grid.json (QA F-6)
    if "mde" in kw:
        out["mde"] = _f(kw.pop("mde"))
    if kw:
        raise TypeError(f"unexpected row fields {sorted(kw)}")
    return out


def _f(v) -> float | None:
    return float(v) if v is not None and np.isfinite(v) else None


def _frame(cell: Cell, band: str) -> pl.DataFrame:
    return cell.design if band == "DESIGN" else cell.confirm


def _oos_arrays(df: pl.DataFrame, key: str, target: str):
    """OOS subset arrays: prediction, actual, unconditional baseline, target dates, contiguity."""
    pcol, bcol = f"pred__{key}", f"base__{key}"
    if pcol not in df.columns:
        return None
    d = df.filter(pl.col("oos")) if "oos" in df.columns else df
    pred = d[pcol].to_numpy()
    y = d[target].to_numpy()
    base = d[bcol].to_numpy() if bcol in d.columns else np.full(y.size, np.nan)
    dates = d["target_date"].to_numpy()
    contig = (
        d["target_contiguous"].to_numpy()
        if "target_contiguous" in d.columns else np.ones(y.size, dtype=bool)
    )
    m = np.isfinite(pred) & np.isfinite(y)
    if m.sum() < 3:
        return None
    return pred[m], y[m], base[m], dates[m], contig[m]


# ------------------------------------------------------------ V-PERSIST ----


def arm_persist(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    rows: list[dict] = []
    if df.height < 10:
        return rows
    abs_r = df["abs_r"].to_numpy()
    rv20 = df["rv20"].to_numpy()
    dates = df["target_date"].to_numpy()

    for lag in PERSIST_LAGS:
        rows.append(_row(cell, band, "V-PERSIST", f"autocorr_abs_r_lag{lag}",
                         autocorr(abs_r, lag), n_obs=df.height))
        rows.append(_row(cell, band, "V-PERSIST", f"autocorr_rv20_lag{lag}",
                         autocorr(rv20, lag), n_obs=df.height))
    slope, hl = ar1_half_life(abs_r)
    rows.append(_row(cell, band, "V-PERSIST", "ar1_slope_abs_r", slope, n_obs=df.height))
    rows.append(_row(cell, band, "V-PERSIST", "half_life_abs_r_bars", hl, n_obs=df.height,
                     note="bars of this clock; NaN when AR(1) slope outside (0,1)"))

    # lag-1 predictor IC (design §4 primary metric): rv20_i vs next-bar |move|
    y = df["target_abs_oo"].to_numpy()
    b = boot_rank_corr(rv20, y, dates)
    rows.append(_row(cell, band, "V-PERSIST", "ic_lag1_rv20_vs_target", b.point, boot=b,
                     mde=mde_ic(b.n_dates),
                     band_label=band_ic(b.point, b.ci_low, b.ci_high, b.n_dates),
                     band_label_detected=band_ic_detected(
                         b.point, b.ci_low, b.ci_high, b.n_dates)))
    # persistence ICs of the vol objects themselves
    b2 = boot_rank_corr(rv20, df["rv_next"].to_numpy(), dates)
    rows.append(_row(cell, band, "V-PERSIST", "ic_rv20_vs_rv_next", b2.point, boot=b2,
                     mde=mde_ic(b2.n_dates), target="rv_next", target_overlaps_feature=True,
                     note="rv20 windows overlap 19/20 with this target -> mechanical "
                          "persistence, not forecast skill"))
    if df.height > 2:
        b3 = boot_rank_corr(abs_r[:-1], abs_r[1:], dates[:-1])
        rows.append(_row(cell, band, "V-PERSIST", "ic_abs_r_lag1_persist", b3.point, boot=b3,
                         mde=mde_ic(b3.n_dates)))

    # HAR walk-forward OOS (design §4 "HAR OOS R2")
    for tgt in TARGETS:
        for mdl in ("ridge", "ols"):
            key = f"vpersist_har_{mdl}__{tgt}"
            rows += _forecast_rows(cell, band, "V-PERSIST", key, tgt, f"har_{mdl}",
                                   primary=False)
    return rows


# -------------------------------------------------------------- V-LEVEL ----


def _forecast_rows(
    cell: Cell, band: str, arm: str, key: str, target: str, model: str, *, primary: bool
) -> list[dict]:
    """OOS IC / MAE / R2 / dMAE-vs-unconditional rows for one forecast model."""
    df = _frame(cell, band)
    got = _oos_arrays(df, key, target)
    if got is None:
        return []
    pred, y, base, dates, contig = got
    rows: list[dict] = []
    # rv_next_i = rv20_{i+1} shares 19 of its 20 return terms with the rv20 feature at origin i.
    # EVERY metric on that target is mechanical, not forecast skill — flag them all (QA/analysis
    # finding 8.1; flagging only oos_ic left an unflagged OOS R2 of 0.967).
    overlap = target == "rv_next"
    overlap_note = ("rv20 windows overlap 19/20 with this target -> mechanical persistence, "
                    "not forecast skill")

    b = boot_rank_corr(pred, y, dates)
    label = band_ic(b.point, b.ci_low, b.ci_high, b.n_dates) if primary else ""
    label_d = band_ic_detected(b.point, b.ci_low, b.ci_high, b.n_dates) if primary else ""
    note = "PRIMARY V-LEVEL band cell" if primary else ""
    if overlap:
        note = (note + "; " + overlap_note).strip("; ")
    rows.append(_row(cell, band, arm, "oos_ic", b.point, boot=b, model=model, target=target,
                     mde=mde_ic(b.n_dates), band_label=label, band_label_detected=label_d,
                     target_overlaps_feature=overlap, note=note))

    if primary:
        rows.append(_row(cell, band, arm, "target_contiguous_frac", float(contig.mean()),
                         model=model, target=target, n_obs=int(y.size),
                         note="fraction of targets whose horizon is exactly one clock bar"))
        if contig.sum() >= 30:
            rows.append(_row(cell, band, arm, "oos_ic_contiguous_subset",
                             spearman(pred[contig], y[contig]), model=model, target=target,
                             n_obs=int(contig.sum()),
                             note="same IC restricted to exactly-one-bar horizons (QA F-8 "
                                  "confound check); compare with oos_ic"))

    mae = float(np.mean(np.abs(y - pred)))
    rows.append(_row(cell, band, arm, "oos_mae", mae, model=model, target=target,
                     n_obs=int(y.size), target_overlaps_feature=overlap,
                     note=overlap_note if overlap else ""))
    if np.isfinite(base).any():
        mae_b = float(np.nanmean(np.abs(y - base)))
        rows.append(_row(cell, band, arm, "oos_mae_uncond_baseline", mae_b, model=model,
                         target=target, n_obs=int(y.size), target_overlaps_feature=overlap,
                         note=overlap_note if overlap else ""))
        d = np.abs(y - base) - np.abs(y - pred)      # >0 => model beats constant forecast
        bd = boot_mean(d, dates)
        rows.append(_row(cell, band, arm, "dmae_vs_uncond", bd.point, boot=bd, model=model,
                         target=target, mde=mde_from_se(bd.se),
                         target_overlaps_feature=overlap,
                         note=("positive = model MAE below unconditional-mean MAE"
                               + ("; " + overlap_note if overlap else ""))))
        rows.append(_row(cell, band, arm, "oos_r2_vs_uncond",
                         r2_oos(y, pred, base), model=model, target=target, n_obs=int(y.size),
                         target_overlaps_feature=overlap,
                         note=overlap_note if overlap else ""))
    return rows


def arm_level(cell: Cell, band: str) -> list[dict]:
    rows: list[dict] = []
    for tgt in TARGETS:
        for mdl in _MODEL_KEYS:
            key = f"{mdl}__{tgt}"
            primary = key == PRIMARY_MODEL_KEY
            rows += _forecast_rows(cell, band, "V-LEVEL", key, tgt,
                                   mdl.replace("vlevel_", ""), primary=primary)
    return rows


# ------------------------------------------------------------- V-REGIME ----


def _regime_rows(cell: Cell, band: str, arm: str, state: np.ndarray, df: pl.DataFrame) -> list[dict]:
    rows: list[dict] = []
    y = df["target_abs_oo"].to_numpy()
    dates = df["target_date"].to_numpy()
    m = (state >= 0) & np.isfinite(y)
    if m.sum() < 10:
        return rows
    s, yv, dv = state[m].astype(float), y[m], dates[m]
    hi, lo = yv[s == 1], yv[s == 0]
    if hi.size < 3 or lo.size < 3:
        return rows

    b = boot_group_mean_diff(yv, s, dv)
    rows.append(_row(cell, band, arm, "gap_high_low_bps", b.point, boot=b,
                     mde=mde_from_se(b.se),
                     band_label=band_gap(b.point, b.ci_low, b.ci_high, b.n_dates, b.se),
                     band_label_detected=band_gap_detected(
                         b.point, b.ci_low, b.ci_high, b.n_dates, b.se)))
    rows.append(_row(cell, band, arm, "mean_abs_oo_high_bps", float(hi.mean()),
                     n_obs=int(hi.size)))
    rows.append(_row(cell, band, arm, "mean_abs_oo_low_bps", float(lo.mean()),
                     n_obs=int(lo.size)))
    rows.append(_row(cell, band, arm, "median_abs_oo_high_bps", float(np.median(hi)),
                     n_obs=int(hi.size)))
    rows.append(_row(cell, band, arm, "median_abs_oo_low_bps", float(np.median(lo)),
                     n_obs=int(lo.size)))
    rows.append(_row(cell, band, arm, "state_frac_high", float((s == 1).mean()),
                     n_obs=int(s.size)))

    # transition persistence (design §4)
    a, b2 = s[:-1], s[1:]
    n_hh = float(((a == 1) & (b2 == 1)).sum())
    n_h = float((a == 1).sum())
    n_ll = float(((a == 0) & (b2 == 0)).sum())
    n_l = float((a == 0).sum())
    rows.append(_row(cell, band, arm, "p_high_given_high", n_hh / n_h if n_h else np.nan,
                     n_obs=int(n_h)))
    rows.append(_row(cell, band, arm, "p_low_given_low", n_ll / n_l if n_l else np.nan,
                     n_obs=int(n_l)))
    # regime state as a magnitude predictor
    bi = boot_rank_corr(s, yv, dv)
    rows.append(_row(cell, band, arm, "ic_state_vs_target", bi.point, boot=bi,
                     mde=mde_ic(bi.n_dates)))
    return rows


def arm_regime(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    if df.height == 0 or "regime_state" not in df.columns:
        return []
    return _regime_rows(cell, band, "V-REGIME", df["regime_state"].to_numpy(), df)


def arm_regime_hmm(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    if df.height == 0 or "hmm_state" not in df.columns:
        return []
    state = df["hmm_state"].to_numpy()
    rows = _regime_rows(cell, band, "V-REGIME-HMM", state, df)
    if not rows:
        return rows
    mk = df["regime_state"].to_numpy()
    m = (state >= 0) & (mk >= 0)
    if m.sum() > 10:
        rows.append(_row(cell, band, "V-REGIME-HMM", "agreement_with_markov",
                         float((state[m] == mk[m]).mean()), n_obs=int(m.sum()),
                         note="fraction of origins where HMM and rolling-median states agree"))
    if cell.hmm_final is not None:
        p = cell.hmm_final
        rows.append(_row(cell, band, "V-REGIME-HMM", "hmm_sigma_high",
                         float(p.sigma[p.high]), note="band-final fitted params"))
        rows.append(_row(cell, band, "V-REGIME-HMM", "hmm_sigma_low",
                         float(p.sigma[1 - p.high])))
        rows.append(_row(cell, band, "V-REGIME-HMM", "hmm_p_stay_high",
                         float(p.A[p.high, p.high])))
        rows.append(_row(cell, band, "V-REGIME-HMM", "hmm_p_stay_low",
                         float(p.A[1 - p.high, 1 - p.high])))
    return rows


# ------------------------------------------------------------ V-MEASURE ----


def arm_measure(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    rows: list[dict] = []
    if df.height < 10:
        return rows
    dates = df["target_date"].to_numpy()
    y = df["target_abs_oo"].to_numpy()
    vals = {m: df[m].to_numpy() for m in MEASURES}
    vals["ewma_vol"] = df["ewma_vol"].to_numpy()

    names = list(vals)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            rows.append(_row(cell, band, "V-MEASURE", f"rankcorr_{a}_{b}",
                             spearman(vals[a], vals[b]), n_obs=df.height))
    for name, v in vals.items():
        bt = boot_rank_corr(v, y, dates)
        rows.append(_row(cell, band, "V-MEASURE", f"ic_{name}_vs_target", bt.point, boot=bt,
                         model=name, target="target_abs_oo", mde=mde_ic(bt.n_dates),
                         band_label=band_ic(bt.point, bt.ci_low, bt.ci_high, bt.n_dates),
                         band_label_detected=band_ic_detected(
                             bt.point, bt.ci_low, bt.ci_high, bt.n_dates)))
    for meas in MEASURES:
        for tgt in TARGETS:
            rows += _forecast_rows(cell, band, "V-MEASURE", f"vmeasure_{meas}__{tgt}", tgt,
                                   f"ridge_{meas}", primary=False)
    return rows


# -------------------------------------------------------------- V-CLOCK ----


def arm_clock(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    rows: list[dict] = []
    if df.height < 10:
        return rows
    base = _oos_arrays(df, PRIMARY_MODEL_KEY, "target_abs_oo")
    if base is None:
        return rows
    pred0, y0, uncond0, _, _ = base
    r2_level = r2_oos(y0, pred0, uncond0)

    for key, name in (
        ("vclock_full__target_abs_oo", "session+dow"),
        ("vclock_session__target_abs_oo", "session"),
        ("vclock_dow__target_abs_oo", "dow"),
    ):
        got = _oos_arrays(df, key, "target_abs_oo")
        if got is None:
            continue
        p, y, u, _, _ = got
        r2 = r2_oos(y, p, u)
        note = ""
        if cell.clock == "D1" and "session" in name:
            note = "SESSION DEGENERATE ON D1 (all D1 bars start 00:00 UTC) — not an edge read"
        rows.append(_row(cell, band, "V-CLOCK", f"oos_r2_vlevel_plus_{name}", r2,
                         model=name, target="target_abs_oo", n_obs=int(y.size), note=note))
        rows.append(_row(cell, band, "V-CLOCK", f"incr_r2_{name}",
                         r2 - r2_level if np.isfinite(r2) and np.isfinite(r2_level) else np.nan,
                         model=name, target="target_abs_oo", n_obs=int(y.size),
                         note=note or "incremental OOS R2 over V-LEVEL alone; not a standalone "
                                      "edge claim (design §4)"))
    rows.append(_row(cell, band, "V-CLOCK", "oos_r2_vlevel_only", r2_level,
                     model="vlevel_ridge", target="target_abs_oo", n_obs=int(y0.size)))

    # descriptive residual structure by calendar bucket
    d = df.filter(pl.col("oos")) if "oos" in df.columns else df
    pcol = f"pred__{PRIMARY_MODEL_KEY}"
    resid = d["target_abs_oo"].to_numpy() - d[pcol].to_numpy()
    sess = d["session"].to_numpy()
    dow = d["dow"].to_numpy()
    for s in (0, 1, 2):
        m = (sess == s) & np.isfinite(resid)
        if m.sum() >= 5:
            rows.append(_row(cell, band, "V-CLOCK", f"mean_resid_session_{s}",
                             float(resid[m].mean()), n_obs=int(m.sum()),
                             note="UTC 0-8 / 8-16 / 16-24 bucket of the forecast bar"))
    for k in range(7):
        m = (dow == k) & np.isfinite(resid)
        if m.sum() >= 5:
            rows.append(_row(cell, band, "V-CLOCK", f"mean_resid_dow_{k}",
                             float(resid[m].mean()), n_obs=int(m.sum()),
                             note="0=Sunday (UTC epoch convention)"))
    return rows


# ---------------------------------------------------------------- V-TAIL ----


def arm_tail(cell: Cell, band: str) -> list[dict]:
    df = _frame(cell, band)
    rows: list[dict] = []
    if df.height < 20 or "regime_state" not in df.columns:
        return rows
    y = df["target_abs_oo"].to_numpy()
    st = df["regime_state"].to_numpy()
    dates = df["target_date"].to_numpy()
    m = (st >= 0) & np.isfinite(y)
    if m.sum() < 20:
        return rows
    yv, sv, dv = y[m], st[m], dates[m]
    hi, lo = yv[sv == 1], yv[sv == 0]
    if hi.size < 10 or lo.size < 10:
        return rows

    for q in (90, 95):
        rows.append(_row(cell, band, "V-TAIL", f"p{q}_abs_oo_high_bps",
                         float(np.percentile(hi, q)), n_obs=int(hi.size)))
        rows.append(_row(cell, band, "V-TAIL", f"p{q}_abs_oo_low_bps",
                         float(np.percentile(lo, q)), n_obs=int(lo.size)))
        thr = float(np.percentile(yv, q))
        exc = (yv > thr).astype(float)
        rows.append(_row(cell, band, "V-TAIL", f"exceed_p{q}_high",
                         float(exc[sv == 1].mean()), n_obs=int(hi.size),
                         note=f"unconditional p{q} threshold = {thr:.2f} bps"))
        rows.append(_row(cell, band, "V-TAIL", f"exceed_p{q}_low",
                         float(exc[sv == 0].mean()), n_obs=int(lo.size)))
        b = boot_group_mean_diff(exc, sv.astype(float), dv)
        rows.append(_row(cell, band, "V-TAIL", f"exceed_diff_p{q}", b.point, boot=b,
                         mde=mde_from_se(b.se),
                         note="HIGH-state exceedance rate minus LOW-state exceedance rate"))
    return rows


# ------------------------------------------- time-third stability (§6.2) ----


def stability_rows(cell: Cell) -> list[dict]:
    """V-LEVEL primary OOS IC inside chronological DESIGN thirds.

    Both readings are emitted (interpretation IN-2): ``calendar`` thirds of the literal
    DESIGN band ``[2021-06-29, 2023-03-01)``, and ``sample`` thirds of equal elapsed time
    over this cell's own scored span. Neither is dropped.
    """
    df = cell.design
    rows: list[dict] = []
    if df.height == 0 or f"pred__{PRIMARY_MODEL_KEY}" not in df.columns:
        return rows
    d = df.filter(pl.col("oos"))
    pred = d[f"pred__{PRIMARY_MODEL_KEY}"].to_numpy()
    y = d["target_abs_oo"].to_numpy()
    ts = d["slot_end"].to_numpy().astype(np.int64)
    m = np.isfinite(pred) & np.isfinite(y)
    if m.sum() < 30:
        return rows
    pred, y, ts = pred[m], y[m], ts[m]

    for mode, lo, hi in (
        ("calendar", int(DESIGN_START.timestamp() * NS), int(DESIGN_END.timestamp() * NS)),
        ("sample", int(ts.min()), int(ts.max()) + 1),
    ):
        edges = np.linspace(lo, hi, 4)
        signs = []
        for k in range(3):
            sel = (ts >= edges[k]) & (ts < edges[k + 1])
            ic = spearman(pred[sel], y[sel]) if sel.sum() >= 20 else float("nan")
            rows.append(_row(cell, "DESIGN", "STABILITY", f"ic_third{k + 1}_{mode}", ic,
                             model="vlevel_ridge", target="target_abs_oo", n_obs=int(sel.sum()),
                             note=f"{mode} thirds; <20 origins -> NaN (UNPOWERED third)"))
            if np.isfinite(ic):
                signs.append(np.sign(ic))
        if signs:
            rows.append(_row(cell, "DESIGN", "STABILITY", f"n_thirds_positive_{mode}",
                             float(sum(1 for s in signs if s > 0)), n_obs=len(signs),
                             note=f"{len(signs)} of 3 thirds powered"))
    return rows


ARM_FUNCS = {
    "V-PERSIST": arm_persist,
    "V-LEVEL": arm_level,
    "V-REGIME": arm_regime,
    "V-REGIME-HMM": arm_regime_hmm,
    "V-MEASURE": arm_measure,
    "V-CLOCK": arm_clock,
    "V-TAIL": arm_tail,
}


def all_arm_rows(cell: Cell, band: str) -> list[dict]:
    """Run every per-cell arm (V-XS is cross-sectional and runs at portfolio level)."""
    rows: list[dict] = []
    for fn in ARM_FUNCS.values():
        rows += fn(cell, band)
    return rows
