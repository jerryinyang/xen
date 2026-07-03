"""
EXP-014 — INDEPENDENT MR characterisation (analysis-only; booked BEFORE net-verdict contact, §7).

Answers "how mean-reverting is each series, on its own terms" from the SAME single cTrader emission
as the tradability run (design §7 / amendment §5) — NOT a separate strategy run, NOT a vectorized
edge module (L-01). Two reads, per series/stratum, on the PRIMARY (none/R) emission:

  (A) Full 6-stage screen on the emitted spread (Dev) series — robust detrend, lag-1 autocorr,
      variance ratio VR(q=4), ADF, KPSS, AR(1)/OU half-life. ALL INFORMATIVE, none gating (L-12).
  (B) Native reversion-completion estimands (L-13: reach-anchor / fraction-recovered /
      time-to-anchor ÷ fitted half-life) over each event's own horizon H_i=min(48,3·HL), against a
      DISLOCATION-MATCHED matched-random control (same |z| bin, screen-free) — separates reversion
      completion from static-TP price-hit (fixes finding C). Δ CI via block-bootstrap (L-07).

Writes results/mr_characterisation.json + plots/mr_characterisation.png. VR/HL reuse the frozen
xen.cross_domain_mr helpers; ADF/KPSS are from-scratch (statsmodels absent) and informative only.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns

import lib
from xen.cross_domain_mr import variance_ratio, half_life                     # noqa: E402
from xen.reversion_targets import (anchor_price_level, dislocation_bin,        # noqa: E402
                                   event_horizon, event_target_metrics)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-014-mr")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-014" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-014" / "plots"
Z_TRIGGER = 2.0            # |z| dislocation threshold (the strategy's entry extreme; provenance)
H_CAP = 48
H_MULT = 3.0


@dataclass
class MrCell:
    series: str
    instrument: str
    n_bars: int
    # (A) 6-stage screen (informative)
    autocorr1: float
    vr_med: float
    adf_t: float
    kpss_lm: float
    hl_med: float
    detrend_std: float
    # (B) native reversion-completion vs dislocation-matched control
    n_events: int
    hit_cond: float
    hit_ctrl: float
    hit_delta: float
    hit_ci_low: float
    frac_cond: float
    frac_ctrl: float
    frac_delta: float
    frac_ci_low: float
    ttime_med_hl: float


# --------------------------------------------------------------------------- #
# (A) 6-stage screen helpers — VR/HL reuse xen; ADF/KPSS from scratch (informative).
# --------------------------------------------------------------------------- #
def lag1_autocorr(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if x.size < 3:
        return float("nan")
    x = x - x.mean()
    denom = float(np.dot(x, x))
    return float(np.dot(x[:-1], x[1:]) / denom) if denom > 0 else float("nan")


def adf_tstat(y: np.ndarray, n_lags: int = 1) -> float:
    """Augmented Dickey-Fuller t-stat on the lagged-level coefficient (constant, `n_lags` diffs).
    From scratch (statsmodels absent). Informative only — more negative ⇒ more stationary
    (≈ −2.86 at 5%). Never gates (L-12); Hurst-DFA deliberately excluded (L-13)."""
    y = y[np.isfinite(y)]
    n = y.size
    if n < 20 + n_lags:
        return float("nan")
    dy = np.diff(y)
    rows = n - 1 - n_lags
    if rows < 10:
        return float("nan")
    ylag = y[n_lags:n - 1]
    cols = [ylag, np.ones(rows)]
    for k in range(1, n_lags + 1):
        cols.append(dy[n_lags - k:n - 1 - k])
    X = np.column_stack(cols)
    yv = dy[n_lags:]
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    resid = yv - X @ beta
    dof = rows - X.shape[1]
    if dof <= 0:
        return float("nan")
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = float(np.sqrt(sigma2 * xtx_inv[0, 0]))
    return float(beta[0] / se) if se > 0 else float("nan")


def kpss_lm(y: np.ndarray) -> float:
    """KPSS level-stationarity LM statistic (Bartlett long-run variance). From scratch, informative
    (≈ 0.463 at 5%; larger ⇒ reject stationarity). Complements ADF (reversed null)."""
    y = y[np.isfinite(y)]
    n = y.size
    if n < 20:
        return float("nan")
    e = y - y.mean()
    s = np.cumsum(e)
    bw = int(np.floor(4.0 * (n / 100.0) ** 0.25))
    gamma0 = float(e @ e) / n
    lrv = gamma0
    for lag in range(1, bw + 1):
        w = 1.0 - lag / (bw + 1.0)
        cov = float(e[lag:] @ e[:-lag]) / n
        lrv += 2.0 * w * cov
    if lrv <= 0:
        return float("nan")
    return float(np.sum(s ** 2) / (n ** 2 * lrv))


def robust_detrend_std(dev: np.ndarray, w: int = 90) -> float:
    """Rolling-median detrend residual std (stage 1) — informative dispersion after detrending."""
    dev = dev[np.isfinite(dev)]
    if dev.size < w:
        return float(np.std(dev)) if dev.size > 1 else float("nan")
    med = np.array([np.median(dev[max(0, i - w + 1):i + 1]) for i in range(dev.size)])
    return float(np.std(dev - med))


def six_stage_screen(dev: np.ndarray) -> dict:
    dev = dev[np.isfinite(dev)]
    vr = variance_ratio(dev, q=4) if dev.size >= 8 else float("nan")
    hl = half_life(dev) if dev.size >= 3 else float("nan")
    return {"autocorr1": lag1_autocorr(dev), "vr_med": float(vr), "adf_t": adf_tstat(dev),
            "kpss_lm": kpss_lm(dev), "hl_med": float(hl), "detrend_std": robust_detrend_std(dev)}


# --------------------------------------------------------------------------- #
# (B) Native reversion-completion vs dislocation-matched matched-random control.
# --------------------------------------------------------------------------- #
def reversion_completion(positions: pl.DataFrame, series_cis: str) -> dict:
    """Reach-anchor / fraction-recovered / time-to-anchor(÷HL) on |z|≥2 dislocations vs a
    dislocation-matched (same |z| bin, screen-free) random-bar control. Real intrabar OHLC only."""
    d = positions.sort("SourceCloseTime").filter(~pl.col("Warmup"))
    if d.height < 30:
        return {"n_events": 0}
    op = d.get_column("RealOpen").to_numpy().astype(float)
    lo = d.get_column("RealLow").to_numpy().astype(float)
    hi = d.get_column("RealHigh").to_numpy().astype(float)
    dev = d.get_column("Dev").to_numpy().astype(float)
    anchor = d.get_column("Anchor").to_numpy().astype(float)
    z = d.get_column("Z").to_numpy().astype(float)
    hl = d.get_column("Hl").to_numpy().astype(float)
    n = op.shape[0]

    # Decision-time (≤ t-1) lagged inputs; anchor PRICE level (emitted Anchor, else recovered).
    a_lag = np.full(n, np.nan)
    a_lag[1:] = anchor[:-1]
    if not np.isfinite(a_lag).any():
        a_lag = anchor_price_level(series_cis, op, np.roll(dev, 1))
    dev_lag = np.roll(dev, 1); dev_lag[0] = np.nan
    z_lag = np.roll(z, 1); z_lag[0] = np.nan
    hl_lag = np.roll(hl, 1); hl_lag[0] = np.nan
    horizon = event_horizon(hl_lag, H_MULT, H_CAP)

    absz = np.abs(z_lag)
    valid = np.isfinite(absz) & np.isfinite(a_lag) & (horizon > 0)
    cond_idx = np.flatnonzero(valid & (absz >= Z_TRIGGER))
    if cond_idx.size < lib.MIN_STATE:
        return {"n_events": int(cond_idx.size)}

    cond = event_target_metrics(cond_idx, op, lo, hi, a_lag, dev_lag, hl_lag, horizon)

    # Dislocation-matched control: for each conditioned event, a screen-free random bar in the same
    # |z| bin (varies only whether the extreme is a real spread dislocation vs matched-random timing).
    rng = np.random.default_rng(lib.SEED)
    pool_by_bin: dict[int, list[int]] = {}
    for i in np.flatnonzero(valid):
        b = dislocation_bin(float(absz[i]))
        pool_by_bin.setdefault(b, []).append(int(i))
    ctrl_idx = []
    for i in cond["idx"]:
        b = dislocation_bin(float(absz[i]))
        pool = pool_by_bin.get(b, [])
        if pool:
            ctrl_idx.append(int(rng.choice(pool)))
    ctrl_idx = np.asarray(ctrl_idx, dtype=np.int64)
    ctrl = event_target_metrics(ctrl_idx, op, lo, hi, a_lag, dev_lag, hl_lag, horizon)

    hit_d, hit_lo, _ = lib.two_sample_diff_ci(cond["hit"], ctrl["hit"])
    frac_d, frac_lo, _ = lib.two_sample_diff_ci(cond["frac"], ctrl["frac"])
    tt = cond["ttime"][np.isfinite(cond["ttime"])]
    return {
        "n_events": int(cond["idx"].size),
        "hit_cond": float(np.mean(cond["hit"])) if cond["hit"].size else float("nan"),
        "hit_ctrl": float(np.mean(ctrl["hit"])) if ctrl["hit"].size else float("nan"),
        "hit_delta": hit_d, "hit_ci_low": hit_lo,
        "frac_cond": float(np.mean(cond["frac"])) if cond["frac"].size else float("nan"),
        "frac_ctrl": float(np.mean(ctrl["frac"])) if ctrl["frac"].size else float("nan"),
        "frac_delta": frac_d, "frac_ci_low": frac_lo,
        "ttime_med_hl": float(np.median(tt)) if tt.size else float("nan"),
    }


def characterise_cell(series: str, instrument: str) -> MrCell:
    cell = lib.load_cell(series, instrument=instrument, arm=lib.PRIMARY_ARM)
    pos = cell.positions.sort("SourceCloseTime").filter(~pl.col("Warmup"))
    dev = pos.get_column("Dev").to_numpy().astype(float)
    scr = six_stage_screen(dev)
    rev = reversion_completion(cell.positions, lib.SERIES[series]["cis"])
    return MrCell(series=series, instrument=instrument, n_bars=cell.positions.height,
                  autocorr1=scr["autocorr1"], vr_med=scr["vr_med"], adf_t=scr["adf_t"],
                  kpss_lm=scr["kpss_lm"], hl_med=scr["hl_med"], detrend_std=scr["detrend_std"],
                  n_events=int(rev.get("n_events", 0)),
                  hit_cond=rev.get("hit_cond", float("nan")), hit_ctrl=rev.get("hit_ctrl", float("nan")),
                  hit_delta=rev.get("hit_delta", float("nan")), hit_ci_low=rev.get("hit_ci_low", float("nan")),
                  frac_cond=rev.get("frac_cond", float("nan")), frac_ctrl=rev.get("frac_ctrl", float("nan")),
                  frac_delta=rev.get("frac_delta", float("nan")), frac_ci_low=rev.get("frac_ci_low", float("nan")),
                  ttime_med_hl=rev.get("ttime_med_hl", float("nan")))


def plot_characterisation(cells: list[MrCell], save) -> None:
    if not cells:
        return
    sns.set_theme(style="whitegrid")
    labels = [f"{c.series}:{c.instrument}" for c in cells]
    x = np.arange(len(cells))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(16, 5))
    ax.bar(x, [c.vr_med for c in cells], color=["#2c7" if (c.vr_med == c.vr_med and c.vr_med < 1) else "#c55" for c in cells])
    ax.axhline(1.0, color="red", ls="--", lw=1, label="VR=1 (random walk)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("median VR(q=4)"); ax.set_title("EXP-014 MR screen: variance ratio (<1 = reverting)")
    ax.legend()
    ax2.bar(x - 0.2, [c.hit_delta for c in cells], 0.4, label="Δ reach-anchor (cond−ctrl)", color="#59b")
    ax2.bar(x + 0.2, [c.frac_delta for c in cells], 0.4, label="Δ fraction-recovered", color="#e8a")
    ax2.axhline(0.0, color="red", ls="--", lw=1)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, rotation=90, fontsize=6)
    ax2.set_ylabel("Δ vs dislocation-matched control")
    ax2.set_title("EXP-014 native reversion-completion (>0 = beats matched-random)")
    ax2.legend(); fig.tight_layout()
    fig.savefig(save / "mr_characterisation.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-014 MR characterisation — 6-stage screen + native reversion estimands (PRIMARY none/R).")
    cells: list[MrCell] = []
    for series, cfg in lib.SERIES.items():
        for inst in cfg["cells"]:
            try:
                c = characterise_cell(series, inst)
            except FileNotFoundError as exc:
                logger.warning("skip %s:%s — %s", series, inst, exc)
                continue
            cells.append(c)
            logger.info("[%s] %s: VR=%.2f HL=%.0f ac1=%.2f ADF=%.2f KPSS=%.2f | events=%d "
                        "hitΔ=%.3f(ci%.3f) fracΔ=%.3f(ci%.3f) tt=%.2fHL", series, inst, c.vr_med,
                        c.hl_med, c.autocorr1, c.adf_t, c.kpss_lm, c.n_events, c.hit_delta,
                        c.hit_ci_low, c.frac_delta, c.frac_ci_low, c.ttime_med_hl)
    out = {"experiment": "EXP-014", "family": "CF-MR-004", "read": "mr_characterisation_before_verdict",
           "domain": lib.DOMAIN, "z_trigger": Z_TRIGGER, "cells": [asdict(c) for c in cells]}
    (RESULTS / "mr_characterisation.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    plot_characterisation(cells, PLOTS)
    logger.info("MR characterisation written (%d cells) -> results/mr_characterisation.json", len(cells))


if __name__ == "__main__":
    main()
