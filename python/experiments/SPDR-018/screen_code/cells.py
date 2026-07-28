"""Turn a parent's row panel into scored cells carrying the uniform layer.

One scorer, used identically by all four arms, so no arm can quietly acquire a different
uncertainty treatment or a different band rule. The estimand of a cell is whatever its parent's
rows already are; this module adds §4.1, §6.2 and §8 on top and nothing else.

Every cell is emitted on BOTH bases (design §5.3 "gross AND net"):
  * gross basis — ``(p, W, L, W_L, p_be, p_be_net, edge)``. Break-even carries the cost term, so
    ``edge`` is a NET read even though ``W`` and ``L`` are gross sizes. This is the SoT §2 form.
  * net basis   — ``mean / median / trimmed`` of the parent's own partial-net return.
The per-row cost is taken as ``gross - net`` from the parent's own ``xen.evaluation`` overlay:
no accounting primitive is re-implemented here (L-18 / lane rule).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import metrics
from config import BOOT_RESAMPLES, TARGETS


def cost_per_row(df: pd.DataFrame, gross_col: str, net_col: str) -> np.ndarray:
    """The cost the PARENT actually charged, recovered from its own emission."""
    return df[gross_col].to_numpy(dtype=float) - df[net_col].to_numpy(dtype=float)


def _powered(arm: str, rec: dict) -> tuple[bool, float, str]:
    """Is the cell at its PARENT's own declared target precision? (design §9)"""
    t = TARGETS[arm]
    mde = rec.get("net_block_mde_mean_bps", float("nan"))
    n = rec.get("n", 0)
    nd = rec.get("n_dates", 0)
    if arm == "A":
        target = t["mde_ic_ceiling"]
        ok = nd >= t["min_dates"]
        return bool(ok), float(target), t["rule"]
    if arm == "B":
        target = t["mde_ceiling_bps"]
        ok = (np.isfinite(mde) and mde <= target and nd >= t["min_dates"]
              and rec.get("thirds_sign_agree", 0) >= t["thirds_sign_min"])
        return bool(ok), float(target), t["rule"]
    if arm == "C":
        target = t["mde_ceiling_bps"]
        ok = (np.isfinite(mde) and mde <= target and n >= t["min_events"]
              and nd >= t["min_dates"])
        return bool(ok), float(target), t["rule"]
    target = t.get("mde_ceiling_bps", float("nan"))
    ok = n >= t["min_origins"] and nd >= t["min_dates"]
    return bool(ok), float(target), t["rule"]


def thirds_sign_agree(r: np.ndarray, ts: np.ndarray) -> int:
    """How many of three equal calendar thirds carry the overall sign (SPDR-013 §7.1 rule).

    Emitted for every cell so A5's "calendar-thirds vacuity" is a measured number: a third that
    contains no rows at all cannot agree, and that is exactly what 42/45 of SPDR-012's cells hit.
    """
    r = np.asarray(r, dtype=float)
    ts = np.asarray(ts, dtype=np.int64)
    if r.size == 0:
        return 0
    overall = np.sign(np.mean(r))
    if overall == 0:
        return 0
    lo, hi = ts.min(), ts.max()
    if hi == lo:
        return 0
    edges = np.linspace(lo, hi + 1, 4)
    agree = 0
    for i in range(3):
        m = (ts >= edges[i]) & (ts < edges[i + 1])
        if m.sum() == 0:
            continue
        if np.sign(np.mean(r[m])) == overall:
            agree += 1
    return int(agree)


def thirds_populated(r: np.ndarray, ts: np.ndarray) -> int:
    """How many of the three thirds contain ANY rows — the A5 vacuity disclosure."""
    ts = np.asarray(ts, dtype=np.int64)
    if ts.size == 0:
        return 0
    lo, hi = ts.min(), ts.max()
    if hi == lo:
        return 1
    edges = np.linspace(lo, hi + 1, 4)
    return int(sum(1 for i in range(3)
                   if ((ts >= edges[i]) & (ts < edges[i + 1])).sum() > 0))


def score_signed_cell(df: pd.DataFrame, *, arm: str, item: str, key: dict,
                      gross_col: str, net_col: str, ts_col: str, symbol_col: str = "symbol",
                      exit_ts_col: str | None = None, h: int | None = None,
                      clock_minutes: int | None = None,
                      levers_exhausted: bool = False, full: bool = False,
                      n_boot: int = BOOT_RESAMPLES,
                      sigma_bps: float | None = None) -> dict:
    """One fully-decorated cell record. ``key`` identifies the cell; nothing is dropped."""
    n_rows = len(df)
    rec: dict = {"arm": arm, "residue_item": item, **key, "n_rows_raw": int(n_rows)}
    if n_rows == 0:
        rec.update({"n": 0, "empty": True, "band_label_mean": "UNPOWERED",
                    "band_label_edge": "UNPOWERED",
                    "note": "cell retained with n=0 — no post-outcome universe edit (design §9)"})
        return rec

    ts = df[ts_col].to_numpy(dtype=np.int64)
    gross = df[gross_col].to_numpy(dtype=float)
    net = df[net_col].to_numpy(dtype=float)
    cost = cost_per_row(df, gross_col, net_col)
    cost_mean = float(np.nanmean(cost)) if np.isfinite(cost).any() else 0.0

    g = metrics.signed_cell(gross, ts, cost_bps=cost_mean, full=full, n_boot=n_boot)
    n_ = metrics.signed_cell(net, ts, cost_bps=0.0, full=full, n_boot=n_boot)
    if g.get("empty") or n_.get("empty"):
        # every value in the cell is non-finite. The cell is RETAINED with its count disclosed —
        # a post-outcome universe edit is forbidden (design §9).
        rec.update({"n": 0, "n_dates": 0, "empty": True,
                    "band_label_mean": "UNPOWERED", "band_label_edge": "UNPOWERED",
                    "note": "all rows non-finite; cell retained, never silently dropped"})
        return rec

    for src, prefix in ((g, "gross_"), (n_, "net_")):
        for k, v in src.items():
            if k == "_ci_detail":
                continue
            rec[prefix + k] = v
    rec["n"] = int(g.get("n", 0))
    rec["n_dates"] = int(g.get("n_dates", 0))
    rec["cost_bps_mean"] = cost_mean
    rec["cost_bps_median"] = float(np.nanmedian(cost)) if np.isfinite(cost).any() else 0.0

    # the SoT §2 quantities live on the gross basis with the cost in the break-even
    for k in ("p", "W", "L", "W_L", "p_be", "p_be_net", "edge", "p_flat",
              "edge_ci_low", "edge_ci_high", "p_ci_low", "p_ci_high",
              "W_ci_low", "W_ci_high", "L_ci_low", "L_ci_high",
              "W_L_ci_low", "W_L_ci_high", "block_mde_p", "block_mde_edge"):
        rec[k] = g.get(k)
    rec["identity_residual_bps"] = g.get("identity_residual_bps")
    rec["identity_reconstruction"] = g.get("identity_reconstruction")

    rec["thirds_sign_agree"] = thirds_sign_agree(net, ts)
    rec["thirds_populated"] = thirds_populated(net, ts)
    rec["n_symbols"] = int(df[symbol_col].nunique()) if symbol_col in df.columns else 1

    # M-4 effective coverage
    cov = metrics.effective_coverage(
        ts, df[symbol_col].to_numpy() if symbol_col in df.columns else np.array(["_"] * n_rows))
    rec.update({f"coverage_{k}": v for k, v in cov.items() if k != "n"})

    # M-2 span disclosure
    if exit_ts_col is not None and h is not None and clock_minutes is not None:
        sp = metrics.span_stats(ts, df[exit_ts_col].to_numpy(dtype=np.int64), h, clock_minutes)
        rec.update({f"span_{k}": v for k, v in sp.items() if k != "n"})
    else:
        rec["span_status"] = "N/A — this cell has no fixed index-offset horizon"

    # sigma-normalised companions (pooling aid only; bps stays primary — P-15 / L-21)
    if sigma_bps and np.isfinite(sigma_bps) and sigma_bps > 0:
        rec["sigma_bps_used"] = float(sigma_bps)
        rec["net_mean_in_sigma_units__POOLING_AID_ONLY"] = (
            float(rec["net_mean"] / sigma_bps) if np.isfinite(rec.get("net_mean", np.nan))
            else float("nan"))
        rec["sigma_unit_caveat"] = ("never a headline, never compared to the cost floor "
                                    "(P-15 / L-21 / design §4.3)")

    powered, target, rule = _powered(arm, rec)
    rec["target_mde"] = target
    rec["target_rule"] = rule
    rec["at_parent_target_precision"] = bool(powered)
    rec["band_label_mean"] = metrics.band_mean(
        {k[4:]: v for k, v in rec.items() if k.startswith("net_")},
        levers_exhausted=levers_exhausted)
    rec["band_label_edge"] = metrics.band_edge(rec, levers_exhausted=levers_exhausted)
    rec["mde_source_for_bands"] = "block"
    rec["levers_exhausted"] = bool(levers_exhausted)
    return rec


# --------------------------------------------------------------------------- #
# unsigned / measurement-object cells (arm A, arm D)
#
# These objects carry NO signed return, so the (p, W, L) decomposition does not apply to them
# (design §4.1 applies it to "every cell carrying a signed return"). Arms A and D are measurement
# objects with no P&L claim (design §3), so they get the uncertainty layer and the band labels
# and nothing else. Their statistics are all decomposable into per-day sufficient statistics, so
# the same day-block envelope bootstrap drives their MDE too (M-1).
# --------------------------------------------------------------------------- #
def _envelope_from_suff(suff: np.ndarray, stat, n_boot: int) -> dict:
    """Envelope CI for an arbitrary statistic of summed per-day sufficient statistics."""
    from config import BOOT_BLOCKS_DAYS, BOOT_CI_ALPHA, BOOT_SEEDS
    from metrics import _resample_day_blocks

    n_days = suff.shape[0]
    point = float(stat(suff.sum(axis=0)))
    if n_days < 2:
        return {"stat": point, "ci_low": float("nan"), "ci_high": float("nan"),
                "n_days": int(n_days), "degenerate": True}
    lows, highs = [], []
    for bl in BOOT_BLOCKS_DAYS:
        for si in range(len(BOOT_SEEDS)):
            idx = _resample_day_blocks(n_days, bl, n_boot, BOOT_SEEDS[0] + si)
            tot = suff[idx].sum(axis=1)
            with np.errstate(divide="ignore", invalid="ignore"):
                vals = stat(tot.T)
            vals = np.asarray(vals, dtype=float)
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                continue
            lows.append(float(np.quantile(vals, BOOT_CI_ALPHA / 2)))
            highs.append(float(np.quantile(vals, 1 - BOOT_CI_ALPHA / 2)))
    return {"stat": point,
            "ci_low": float(min(lows)) if lows else float("nan"),
            "ci_high": float(max(highs)) if highs else float("nan"),
            "n_days": int(n_days), "degenerate": False,
            "envelope_rule": "min/max over blocks {1,3,7} days x 5 seeds"}


def score_gap_cell(value: np.ndarray, is_high: np.ndarray, ts: np.ndarray, *, arm: str,
                   item: str, key: dict, levers_exhausted: bool = False,
                   n_boot: int = BOOT_RESAMPLES) -> dict:
    """HIGH-minus-LOW separation of an unsigned magnitude (arm A: V-REGIME / V-TAIL / HMM)."""
    v = np.asarray(value, dtype=float)
    hi = np.asarray(is_high, dtype=bool)
    t = np.asarray(ts, dtype=np.int64)
    ok = np.isfinite(v)
    v, hi, t = v[ok], hi[ok], t[ok]
    rec = {"arm": arm, "residue_item": item, **key, "n": int(v.size)}
    if v.size == 0:
        rec.update({"empty": True, "band_label_gap": "UNPOWERED",
                    "note": "cell retained with n=0 — never silently dropped"})
        return rec
    day_idx, day_starts = metrics.day_index(t)
    nd = day_starts.size
    suff = np.zeros((nd, 4))
    suff[:, 0] = np.bincount(day_idx, weights=hi.astype(float), minlength=nd)
    suff[:, 1] = np.bincount(day_idx, weights=np.where(hi, v, 0.0), minlength=nd)
    suff[:, 2] = np.bincount(day_idx, weights=(~hi).astype(float), minlength=nd)
    suff[:, 3] = np.bincount(day_idx, weights=np.where(~hi, v, 0.0), minlength=nd)

    def gap(tot):
        nh, sh, nl, sl = tot[0], tot[1], tot[2], tot[3]
        return np.where((nh > 0) & (nl > 0), sh / np.where(nh > 0, nh, np.nan)
                        - sl / np.where(nl > 0, nl, np.nan), np.nan)

    ci = _envelope_from_suff(suff, gap, n_boot)
    rec.update({
        "gap_bps": ci["stat"], "gap_ci_low": ci["ci_low"], "gap_ci_high": ci["ci_high"],
        "block_mde_gap_bps": (ci["stat"] - ci["ci_low"]
                              if np.isfinite(ci["ci_low"]) else float("nan")),
        "iid_mde_bps__COMPANION_ONLY": metrics.iid_mde_companion(v),
        "mean_high": float(v[hi].mean()) if hi.any() else float("nan"),
        "mean_low": float(v[~hi].mean()) if (~hi).any() else float("nan"),
        "n_high": int(hi.sum()), "n_low": int((~hi).sum()), "n_dates": int(nd),
        "thirds_sign_agree": thirds_sign_agree(np.where(hi, v, -v), t),
        "thirds_populated": thirds_populated(v, t),
        "mde_source_for_bands": "block", "levers_exhausted": bool(levers_exhausted),
    })
    rec.update({f"coverage_{k}": val for k, val in
                metrics.effective_coverage(t, key.get("_symbols", np.array(["_"] * v.size))).items()
                if k != "n"})
    t_a = TARGETS["A"]
    rec["target_mde"] = t_a["gap_mde_ceiling_bps"]
    rec["target_rule"] = t_a["rule"]
    rec["at_parent_target_precision"] = bool(nd >= t_a["min_dates"])
    rec["band_label_gap"] = metrics._label(
        ci["stat"], ci["ci_low"], ci["ci_high"], rec["block_mde_gap_bps"],
        t_a["gap_mde_ceiling_bps"], 15.0, -15.0, levers_exhausted=levers_exhausted)
    return rec


def score_mean_cell(value: np.ndarray, ts: np.ndarray, *, arm: str, item: str, key: dict,
                    target_mde: float, supported: float, contradicted: float,
                    label_field: str = "band_label", levers_exhausted: bool = False,
                    n_boot: int = BOOT_RESAMPLES) -> dict:
    """A plain mean of an unsigned quantity with the day-block envelope CI and MDE (M-1).

    Used for arm D's forecast-skill objects (hit rate, Brier, delta-Brier vs persistence,
    run-length MAE, stickiness) — measurement objects with no P&L claim, so no (p, W, L).
    """
    v = np.asarray(value, dtype=float)
    t = np.asarray(ts, dtype=np.int64)
    ok = np.isfinite(v)
    v, t = v[ok], t[ok]
    rec = {"arm": arm, "residue_item": item, **key, "n": int(v.size)}
    if v.size == 0:
        rec.update({"empty": True, label_field: "UNPOWERED",
                    "note": "cell retained with n=0 — never silently dropped"})
        return rec
    day_idx, day_starts = metrics.day_index(t)
    nd = day_starts.size
    suff = np.zeros((nd, 2))
    suff[:, 0] = np.bincount(day_idx, weights=v, minlength=nd)
    suff[:, 1] = np.bincount(day_idx, minlength=nd)
    ci = _envelope_from_suff(
        suff, lambda tot: np.where(tot[1] > 0, tot[0] / np.where(tot[1] > 0, tot[1], np.nan),
                                   np.nan), n_boot)
    rec.update({
        "value": ci["stat"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
        "block_mde": (ci["stat"] - ci["ci_low"]
                      if np.isfinite(ci["ci_low"]) else float("nan")),
        "iid_mde__COMPANION_ONLY": metrics.iid_mde_companion(v),
        "median": float(np.median(v)), "n_dates": int(nd),
        "mde_source_for_bands": "block", "target_mde": float(target_mde),
        "thirds_populated": thirds_populated(v, t),
        "levers_exhausted": bool(levers_exhausted),
    })
    rec[label_field] = metrics._label(ci["stat"], ci["ci_low"], ci["ci_high"], rec["block_mde"],
                                      target_mde, supported, contradicted,
                                      levers_exhausted=levers_exhausted)
    return rec


def score_ic_cell(x: np.ndarray, y: np.ndarray, ts: np.ndarray, *, arm: str, item: str,
                  key: dict, levers_exhausted: bool = False,
                  n_boot: int = BOOT_RESAMPLES) -> dict:
    """Rank IC of a forecast against its target (arm A: V-LEVEL / V-PERSIST / V-MEASURE / V-XS).

    Ranks are taken ONCE on the whole cell, then the bootstrap correlates the fixed ranks — the
    standard fast Spearman bootstrap. The MDE is the day-block envelope half-width (M-1); the
    parent's own analytic ``1.5/sqrt(n_dates)`` rule is carried as its published target, not as
    the uncertainty.
    """
    from scipy.stats import rankdata

    xr = np.asarray(x, dtype=float)
    yr = np.asarray(y, dtype=float)
    t = np.asarray(ts, dtype=np.int64)
    ok = np.isfinite(xr) & np.isfinite(yr)
    xr, yr, t = xr[ok], yr[ok], t[ok]
    rec = {"arm": arm, "residue_item": item, **key, "n": int(xr.size)}
    if xr.size < 3:
        rec.update({"empty": xr.size == 0, "band_label_ic": "UNPOWERED",
                    "note": "cell retained — never silently dropped"})
        return rec
    a, b = rankdata(xr), rankdata(yr)
    day_idx, day_starts = metrics.day_index(t)
    nd = day_starts.size
    suff = np.zeros((nd, 6))
    for j, w in enumerate((np.ones_like(a), a, b, a * b, a * a, b * b)):
        suff[:, j] = np.bincount(day_idx, weights=w, minlength=nd)

    def corr(tot):
        n, sa, sb, sab, saa, sbb = (tot[i] for i in range(6))
        cov = sab - sa * sb / n
        va = saa - sa * sa / n
        vb = sbb - sb * sb / n
        den = np.sqrt(np.where(va > 0, va, np.nan) * np.where(vb > 0, vb, np.nan))
        return cov / den

    ci = _envelope_from_suff(suff, corr, n_boot)
    t_a = TARGETS["A"]
    analytic = (t_a["mde_ic_const"] / np.sqrt(nd)) if nd > 0 else float("nan")
    rec.update({
        "rank_ic": ci["stat"], "ic_ci_low": ci["ci_low"], "ic_ci_high": ci["ci_high"],
        "block_mde_ic": (ci["stat"] - ci["ci_low"]
                         if np.isfinite(ci["ci_low"]) else float("nan")),
        "parent_analytic_mde_ic__COMPANION_ONLY": float(analytic),
        "n_dates": int(nd), "mde_source_for_bands": "block",
        "target_mde": t_a["mde_ic_ceiling"], "target_rule": t_a["rule"],
        "at_parent_target_precision": bool(nd >= t_a["min_dates"]),
        "n_dates_short_of_225": int(max(0, t_a["min_dates"] - nd)),
        "thirds_populated": thirds_populated(xr, t),
        "levers_exhausted": bool(levers_exhausted),
    })
    rec["band_label_ic"] = metrics._label(
        ci["stat"], ci["ci_low"], ci["ci_high"], rec["block_mde_ic"],
        t_a["mde_ic_ceiling"], 0.10, -0.05, levers_exhausted=levers_exhausted)
    return rec


def score_r2_cell(y: np.ndarray, pred: np.ndarray, base: np.ndarray, ts: np.ndarray, *,
                  arm: str, item: str, key: dict, levers_exhausted: bool = False,
                  n_boot: int = BOOT_RESAMPLES) -> dict:
    """Incremental OOS R^2 of a model over its own base (arm A: V-CLOCK at D1).

    A4's open question is whether the D1 penalty was overfitting (7 dummies on ~100 daily
    observations) rather than evidence against calendar structure — so the incremental R^2 is
    reported WITH its day-block CI and its realised n, not as a bare negative number.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(pred, dtype=float)
    b = np.asarray(base, dtype=float)
    t = np.asarray(ts, dtype=np.int64)
    ok = np.isfinite(y) & np.isfinite(p) & np.isfinite(b)
    y, p, b, t = y[ok], p[ok], b[ok], t[ok]
    rec = {"arm": arm, "residue_item": item, **key, "n": int(y.size)}
    if y.size < 3:
        rec.update({"empty": y.size == 0, "band_label_r2": "UNPOWERED"})
        return rec
    day_idx, day_starts = metrics.day_index(t)
    nd = day_starts.size
    suff = np.zeros((nd, 3))
    suff[:, 0] = np.bincount(day_idx, weights=(y - p) ** 2, minlength=nd)
    suff[:, 1] = np.bincount(day_idx, weights=(y - b) ** 2, minlength=nd)
    suff[:, 2] = np.bincount(day_idx, minlength=nd)

    def dr2(tot):
        sse_m, sse_b = tot[0], tot[1]
        return np.where(sse_b > 0, 1.0 - sse_m / np.where(sse_b > 0, sse_b, np.nan), np.nan)

    ci = _envelope_from_suff(suff, dr2, n_boot)
    rec.update({
        "incremental_r2": ci["stat"], "r2_ci_low": ci["ci_low"], "r2_ci_high": ci["ci_high"],
        "block_mde_r2": (ci["stat"] - ci["ci_low"]
                         if np.isfinite(ci["ci_low"]) else float("nan")),
        "n_dates": int(nd), "n_obs_per_date": float(y.size / nd) if nd else float("nan"),
        "mde_source_for_bands": "block", "levers_exhausted": bool(levers_exhausted),
        "target_rule": TARGETS["A"]["rule"],
        "at_parent_target_precision": bool(nd >= TARGETS["A"]["min_dates"]),
    })
    rec["band_label_r2"] = metrics._label(ci["stat"], ci["ci_low"], ci["ci_high"],
                                          rec["block_mde_r2"], 0.01, 0.0, 0.0,
                                          levers_exhausted=levers_exhausted)
    return rec


def to_frame(records: list[dict]) -> pd.DataFrame:
    """Records -> a flat table. Never drops a column; never drops a cell."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    return df.reindex(sorted(df.columns), axis=1)
