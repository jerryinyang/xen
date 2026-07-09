"""
EXP-014b — CF-MR-003/HYP-003 availability read (analysis-only; booked BEFORE net-verdict contact).

amendment-003 REPLACES the degenerate dislocation-matched control (it drew from the |z|≥2 signal
population itself → signal-vs-signal → vacuous; see .ignore/temp/dumps/finding-availability-control-
degenerate.md) with the **symmetry two-barrier first-passage** control:

  Hold the outlier FIXED. From the event open `o`, with dislocation `D = |o − anchor_lag|` and fade
  side `s = sign(dev_lag)`, race two symmetric barriers over the event horizon H = min(cap, ⌈3·HL⌉):
    - INWARD  = the anchor (distance D toward the mean),
    - OUTWARD = o + s·D  (distance D away from the mean).
  First-passage over real intrabar Low/High; earlier bar wins. Per (cell,domain):
    p_inward = inward_first / (inward_first + outward_first)   over DECIDED events.
  NULL = 0.5 (a driftless symmetric-barrier first-passage is 50/50 — gambler's-ruin symmetry).
  Availability ⇔ ci_low(p_inward) > 0.5. Sliced by trend (counter-/with-/neutral) and vol tercile.
  Disclosure: time-reversal (backward window ⇒ p_inward ≈ 0.5) + peer-feed phase-shift collapse.

Runs on the PRIMARY none single-leg emission per domain. Also emits the descriptive 6-stage screen
(VR/HL/ADF/KPSS/autocorr — informative only, L-12). NEVER regenerates a signal/fill (L-01).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns

import lib
from xen.cross_domain_mr import variance_ratio, half_life                     # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-014b-mr")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-014b" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-014b" / "plots"
H_CAP = 48
H_MULT = 3.0
# amendment-003: trend-strength band is PER-CELL data-driven (top tercile of |trend_z|), not a fixed
# threshold. The inherited fixed |trend_z|≥1.0 was miscalibrated to the emitted scale (|trend_z| caps
# <1 because σ_close(200) is trend-inflated) → counter/with-trend slices were structurally empty. The
# tercile matches how vol_regime is bucketed and adapts to each instrument/domain's own scale.
TREND_STRONG_Q = 2.0 / 3.0   # "strong trend" = |trend_z| in its top tercile (per cell)
SLICES = ("all", "counter_trend", "with_trend", "trend_neutral", "vol_low", "vol_mid", "vol_high")


# --------------------------------------------------------------------------- #
# (A) descriptive 6-stage screen (informative only) — VR/HL reuse xen; ADF/KPSS from scratch.
# --------------------------------------------------------------------------- #
def lag1_autocorr(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if x.size < 3:
        return float("nan")
    x = x - x.mean()
    denom = float(np.dot(x, x))
    return float(np.dot(x[:-1], x[1:]) / denom) if denom > 0 else float("nan")


def adf_tstat(y: np.ndarray, n_lags: int = 1) -> float:
    """ADF t-stat on the lagged-level coefficient (constant, `n_lags` diffs). From scratch,
    informative only (≈ −2.86 at 5%); never gates (L-12)."""
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
    """KPSS level-stationarity LM (Bartlett long-run var). From scratch, informative (≈0.463 at 5%)."""
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


def six_stage_screen(dev: np.ndarray) -> dict:
    dev = dev[np.isfinite(dev)]
    vr = variance_ratio(dev, q=4) if dev.size >= 8 else float("nan")
    hl = half_life(dev) if dev.size >= 3 else float("nan")
    return {"autocorr1": lag1_autocorr(dev), "vr_med": float(vr), "adf_t": adf_tstat(dev),
            "kpss_lm": kpss_lm(dev), "hl_med": float(hl)}


# --------------------------------------------------------------------------- #
# (B) symmetry two-barrier first-passage.
# --------------------------------------------------------------------------- #
def _first_true(mask: np.ndarray) -> int:
    hits = np.flatnonzero(mask)
    return int(hits[0]) if hits.size else -1


def two_barrier_outcome(o: float, anchor: float, seg_low: np.ndarray, seg_high: np.ndarray,
                        s: float) -> int:
    """First-passage race of the inward (anchor) vs outward (o+s·D) barrier over one event window.
    Returns 1=inward first, 0=outward first, -1=ambiguous (same bar), -2=censored (neither in H)."""
    D = abs(o - anchor)
    if not (D > 0.0) or seg_low.size == 0:
        return -2
    if s > 0.0:                                   # short: price above anchor
        ti = _first_true(seg_low <= anchor)       # inward: fall to the anchor
        to = _first_true(seg_high >= o + D)        # outward: rise a further D
    else:                                         # long: price below anchor
        ti = _first_true(seg_high >= anchor)       # inward: rise to the anchor
        to = _first_true(seg_low <= o - D)         # outward: fall a further D
    if ti < 0 and to < 0:
        return -2
    if to < 0:
        return 1
    if ti < 0:
        return 0
    if ti < to:
        return 1
    if to < ti:
        return 0
    return -1


@dataclass
class SliceStat:
    p_inward: float = float("nan")
    ci_low: float = float("nan")
    ci_high: float = float("nan")
    n_decided: int = 0


@dataclass
class MrCell:
    domain: str
    instrument: str
    z_trigger: float          # |z| outlier threshold this availability read used (2.0 | 1.5)
    n_bars: int
    n_events: int
    n_ambiguous: int
    n_censored: int
    # descriptive 6-stage
    autocorr1: float
    vr_med: float
    adf_t: float
    kpss_lm: float
    hl_med: float
    # symmetry read per slice + disclosure
    slices: dict = field(default_factory=dict)          # slice -> SliceStat
    p_inward_reverse: float = float("nan")              # time-reversal disclosure (should ≈0.5)
    ci_low_reverse: float = float("nan")
    p_inward_shift: float = float("nan")                # peer-feed phase-shift (should collapse ≈0.5)
    ci_low_shift: float = float("nan")


def _event_arrays(positions: pl.DataFrame):
    """Lagged (≤ t-1) decision inputs + real intrabar OHLC for the outlier events."""
    d = positions.sort("SourceCloseTime").filter(~pl.col("Warmup"))
    n = d.height
    if n < 30:
        return None
    op = d.get_column("RealOpen").to_numpy().astype(float)
    lo = d.get_column("RealLow").to_numpy().astype(float)
    hi = d.get_column("RealHigh").to_numpy().astype(float)
    anchor = d.get_column("Anchor").to_numpy().astype(float)
    dev = d.get_column("Dev").to_numpy().astype(float)
    z = d.get_column("Z").to_numpy().astype(float)
    hl = d.get_column("Hl").to_numpy().astype(float)
    trend_dir = (d.get_column("TrendDir").to_numpy().astype(float)
                 if "TrendDir" in d.columns else np.zeros(n))
    trend_z = (d.get_column("TrendZ").to_numpy().astype(float)
               if "TrendZ" in d.columns else np.zeros(n))
    vol = (d.get_column("VolRegime").to_numpy().astype(float)
           if "VolRegime" in d.columns else np.full(n, -1.0))
    lag = lambda a: np.concatenate([[np.nan], a[:-1]])   # [i-1] decision-time value
    return dict(op=op, lo=lo, hi=hi, a_lag=lag(anchor), dev_lag=lag(dev), z_lag=lag(z),
                hl_lag=lag(hl), trend_dir_lag=lag(trend_dir), trend_z_lag=lag(trend_z),
                vol_lag=lag(vol), n=n)


def symmetry_read(positions: pl.DataFrame, seed: int, z_trigger: float) -> dict | None:
    """Per-event two-barrier outcomes + per-slice p_inward CI (null 0.5) + time-reversal disclosure.
    z_trigger = the |z| outlier threshold (the traded deviation magnitude: 2.0 or 1.5). Z is
    band-independent, so both thresholds read from the same PRIMARY none emission."""
    a = _event_arrays(positions)
    if a is None:
        return None
    n = a["n"]
    horizon = np.where(np.isfinite(a["hl_lag"]) & (a["hl_lag"] > 0),
                       np.minimum(H_CAP, np.ceil(H_MULT * a["hl_lag"])), 0).astype(int)
    absz = np.abs(a["z_lag"])
    valid = np.isfinite(absz) & np.isfinite(a["a_lag"]) & (horizon > 0) & (absz >= z_trigger)
    idx = np.flatnonzero(valid)
    if idx.size < lib.MIN_STATE_AVAIL:
        return {"n_events": int(idx.size), "underpowered": True}

    fwd, rev, meta = [], [], []
    n_amb = n_cens = 0
    for i in idx:
        o = a["op"][i]; anchor = a["a_lag"][i]; s = np.sign(a["dev_lag"][i]); H = int(horizon[i])
        of = two_barrier_outcome(o, anchor, a["lo"][i:i + H], a["hi"][i:i + H], s)
        if of == -1:
            n_amb += 1
        elif of == -2:
            n_cens += 1
        else:
            fwd.append(of)
            meta.append((float(a["trend_dir_lag"][i]), float(a["trend_z_lag"][i]),
                         float(a["vol_lag"][i]), float(s)))
        lo0 = max(0, i - H + 1)                       # time-reversal: reversed pre-window
        rb = two_barrier_outcome(o, anchor, a["lo"][lo0:i + 1][::-1], a["hi"][lo0:i + 1][::-1], s)
        if rb in (0, 1):
            rev.append(rb)

    fwd = np.asarray(fwd, dtype=float)
    meta = np.asarray(meta, dtype=float) if meta else np.empty((0, 4))
    # Per-cell "strong trend" threshold = top-tercile |trend_z| over the decided events (data-driven,
    # amendment-003). Degenerate (all |trend_z| equal / <2 events) → no strong events → slices empty.
    strong_thr = (float(np.nanquantile(np.abs(meta[:, 1]), TREND_STRONG_Q))
                  if meta.shape[0] >= 2 else float("inf"))
    slices: dict[str, SliceStat] = {}
    for sl in SLICES:
        mask = _slice_mask(sl, meta, strong_thr)
        p, lo_, hi_, nd = lib.proportion_ci_vs_half(fwd[mask], seed=seed)
        slices[sl] = SliceStat(p, lo_, hi_, nd)
    pr, lor, _, _ = lib.proportion_ci_vs_half(np.asarray(rev, dtype=float), seed=seed)
    return {"n_events": int(idx.size), "n_ambiguous": n_amb, "n_censored": n_cens,
            "slices": {k: asdict(v) for k, v in slices.items()},
            "p_inward_reverse": pr, "ci_low_reverse": lor}


def _slice_mask(sl: str, meta: np.ndarray, strong_thr: float) -> np.ndarray:
    """Boolean mask over decided events for a named slice. meta cols = [trend_dir, trend_z, vol, s].
    `strong_thr` = per-cell top-tercile |trend_z| cutoff (amendment-003; strong = |trend_z| ≥ cutoff)."""
    if meta.shape[0] == 0:
        return np.zeros(0, dtype=bool)
    trend_dir, trend_z, vol, s = meta[:, 0], meta[:, 1], meta[:, 2], meta[:, 3]
    strong = np.abs(trend_z) >= strong_thr
    if sl == "all":
        return np.ones(meta.shape[0], dtype=bool)
    if sl == "counter_trend":                         # excursion against the trend (dip in uptrend)
        return strong & (s * trend_dir < 0)
    if sl == "with_trend":                            # extension with the trend (fade fights it)
        return strong & (s * trend_dir > 0)
    if sl == "trend_neutral":
        return ~strong | (trend_dir == 0)
    if sl == "vol_low":
        return vol == 0
    if sl == "vol_mid":
        return vol == 1
    if sl == "vol_high":
        return vol == 2
    return np.zeros(meta.shape[0], dtype=bool)


def characterise_cell(domain: str, instrument: str, z_trigger: float,
                      cell: lib.Cell, shift_cell: lib.Cell | None) -> MrCell | None:
    """Availability read for one (cell, domain, z_trigger). `cell` = the PRIMARY none z20 emission
    (Z band-independent → both z_triggers read from it); `shift_cell` = its phase-shift twin or None."""
    pos = cell.positions.sort("SourceCloseTime").filter(~pl.col("Warmup"))
    dev = pos.get_column("Dev").to_numpy().astype(float)
    scr = six_stage_screen(dev)
    sym = symmetry_read(cell.positions, lib.SEED, z_trigger)
    if sym is None:
        return None
    mc = MrCell(domain=domain, instrument=instrument, z_trigger=z_trigger, n_bars=cell.positions.height,
                n_events=int(sym.get("n_events", 0)), n_ambiguous=int(sym.get("n_ambiguous", 0)),
                n_censored=int(sym.get("n_censored", 0)), autocorr1=scr["autocorr1"],
                vr_med=scr["vr_med"], adf_t=scr["adf_t"], kpss_lm=scr["kpss_lm"], hl_med=scr["hl_med"],
                slices=sym.get("slices", {}), p_inward_reverse=sym.get("p_inward_reverse", float("nan")),
                ci_low_reverse=sym.get("ci_low_reverse", float("nan")))
    # Peer-feed phase-shift collapse (if the -shift twin was emitted): availability must →≈0.5.
    if shift_cell is not None:
        s2 = symmetry_read(shift_cell.positions, lib.SEED, z_trigger)
        if s2 and "slices" in s2:
            mc.p_inward_shift = s2["slices"]["all"]["p_inward"]
            mc.ci_low_shift = s2["slices"]["all"]["ci_low"]
    return mc


# --------------------------------------------------------------------------- #
# Plot + orchestration.
# --------------------------------------------------------------------------- #
def plot_symmetry(cells: list[MrCell], save) -> None:
    if not cells:
        return
    sns.set_theme(style="whitegrid")
    labels = [f"{c.domain}:{c.instrument}" for c in cells]
    x = np.arange(len(cells))
    fig, ax = plt.subplots(figsize=(15, 5))
    p = [c.slices.get("all", {}).get("p_inward", float("nan")) for c in cells]
    lo = [c.slices.get("all", {}).get("ci_low", float("nan")) for c in cells]
    ax.errorbar(x, p, yerr=[np.subtract(p, lo), np.zeros(len(p))], fmt="o", ms=4, capsize=2,
                color="#59b", label="p_inward (ci_low bar)")
    ax.axhline(0.5, color="red", ls="--", lw=1, label="null 0.5 (coin flip)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("p_inward (>0.5 ci_low = reverts beyond chance)")
    ax.set_title("EXP-014b symmetry two-barrier availability: p_inward per cell×domain (all events)")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "mr_characterisation.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-014b MR availability — symmetry two-barrier (null 0.5) + 6-stage screen; S8, {1h,4h}.")
    cells: list[MrCell] = []
    for domain in lib.DOMAINS:
        for inst in lib.S8_CELLS:
            try:                                    # availability reads the PRIMARY none z20 emission
                cell = lib.load_cell(domain, lib.PRIMARY_ARM, inst, ztag=lib.PRIMARY_ZTAG)
            except FileNotFoundError as exc:
                logger.warning("skip %s:%s — %s", domain, inst, exc)
                continue
            try:
                shift_cell = lib.load_cell(domain, lib.PRIMARY_ARM, inst,
                                           ztag=lib.PRIMARY_ZTAG, shift=True)
            except FileNotFoundError:
                shift_cell = None
            for z_trigger in lib.Z_TRIGGERS:        # report availability at each traded magnitude
                c = characterise_cell(domain, inst, z_trigger, cell, shift_cell)
                if c is None:
                    logger.info("[%s] %s z%.1f: <30 events — unpowered for availability", domain, inst, z_trigger)
                    continue
                cells.append(c)
                allsl = c.slices.get("all", {})
                ct = c.slices.get("counter_trend", {})
                logger.info("[%s] %s z%.1f: ev=%d(amb%d cens%d) VR=%.2f HL=%.0f | p_in(all)=%.3f(ci%.3f n%d) "
                            "counter=%.3f(ci%.3f n%d) rev=%.3f shift=%.3f", domain, inst, z_trigger,
                            c.n_events, c.n_ambiguous, c.n_censored, c.vr_med, c.hl_med,
                            allsl.get("p_inward", float("nan")), allsl.get("ci_low", float("nan")),
                            allsl.get("n_decided", 0), ct.get("p_inward", float("nan")),
                            ct.get("ci_low", float("nan")), ct.get("n_decided", 0),
                            c.p_inward_reverse, c.p_inward_shift)
    out = {"experiment": "EXP-014b", "family": "CF-MR-004", "hypothesis": "HYP-003",
           "read": "symmetry_two_barrier_before_verdict", "null": 0.5, "z_triggers": list(lib.Z_TRIGGERS),
           "min_state_avail": lib.MIN_STATE_AVAIL, "cells": [asdict(c) for c in cells]}
    (RESULTS / "mr_characterisation.json").write_text(json.dumps(out, indent=2, default=str),
                                                      encoding="utf-8")
    plot_symmetry(cells, PLOTS)
    logger.info("MR availability written (%d cells) -> results/mr_characterisation.json", len(cells))


if __name__ == "__main__":
    main()
