"""Experiment EXP-008 — CF-MR-003/HYP-001: cross-domain mean-reversion availability screen.

Implements the APPROVED analysis plan in ``python/experiments/EXP-008/design.md`` (ANALYSIS-ONLY,
TRAIN-only, 0 counted reads, global holdout sealed). For each (instrument, anchor-series, domain-pair)
stratum it (1) builds a higher-domain anchor and the exec-domain deviation, (2) selects entry timing
where the deviation is characterised mean-reverting at ``<= t-1`` (VR + half-life + Hurst-DFA) and is
extreme (``|z| >= z*``), (3) measures the forward favourable reversion excursion toward the anchor on
**real prices**, and (4) tests Δ-over-a-matched-random control through the frozen ``availability_gate``
(per-cell CI + cross-axis-Holm max-statistic permuted-axis admission over the 15 series×domain axes).

Causality: every decision input is read at index ``i-1`` (the caller acts at bar ``i``'s open); the
favourable excursion is the only forward read and is an outcome, never a decision input. Two
future-destroying leak tripwires (conditioning-label permutation, forward-excursion time-reversal)
must collapse Δ on any admitting cell.

Run (from repo root, after ``uv pip install -e python``)::

    python python/experiments/EXP-008/code/run_experiment.py                # full screen
    python python/experiments/EXP-008/code/run_experiment.py --quick        # 4-instrument smoke

Outputs: ``results/`` (per-cell table, axis admission, tripwires, verdict JSON) and ``plots/`` (P1–P6).
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from numpy.lib.stride_tricks import sliding_window_view
from tqdm.auto import tqdm

from xen import availability_gate as ag
from xen import cross_domain_mr as cdm
from xen import vol_regime as vr
from xen.domain_bars import build_domain_bars
from xen.zigzag import wilder_atr

logger = logging.getLogger("EXP-008")

# --------------------------------------------------------------------------- #
# Constants (design §3–§7; frozen before outcome contact)
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-008")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

SEED = 20260701
H_EXCURSION = 24               # forward excursion horizon (exec bars), design §4
ATR_PERIOD = 14                # exec-bar ATR for excursion normalization
DELTA_STAR = 0.10              # effect floor (ATR), design §7
N_MIN = 100                    # per-cell usable-event floor, design §7
MIN_POWERED_CELLS = 4          # axis eligibility, design §7
MAJORITY = 0.50                # within-axis majority of powered cells, design §7
N_BOOT_CI = 10_000             # per-cell block-bootstrap CI resolution, design §10
POOL_TOTAL = 4_000             # matched-random permutation-pool size (regime-proportioned)
N_TRIPWIRE_PERM = 20           # label-permutation tripwire repetitions
TAU_ATR = ag.TAU_UPPER         # upper-tailmass threshold (1.0 ATR), design §4/§5

ENDPOINTS = (("median", ag.STAT_MEDIAN), ("tailmass", ag.STAT_TAILMASS_UPPER))   # (L), (S)

ALL_INSTRUMENTS = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "USTEC", "US500", "US2000", "JP225", "XAUUSD", "BTCUSD",
)
QUICK_INSTRUMENTS = ("EURUSD", "XAUUSD", "BTCUSD", "USTEC")

# instrument -> S5 class-mate universe (class minus self); empty tuple -> UNPOWERED for S5.
_S5_MATES: dict[str, tuple[str, ...]] = {}
for _cls in cdm.S5_CLASSES.values():
    for _m in _cls:
        _S5_MATES[_m] = tuple(x for x in _cls if x != _m)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class ExecDomain:
    """Exec-domain real-OHLC arrays + causal features for one (instrument, exec-minutes)."""

    ct: np.ndarray             # CloseTime as int64 ns (ascending)
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr_lag: np.ndarray        # ATR(14) shifted 1 bar (known at i-1)
    regime_lag: np.ndarray     # ATR-tercile regime label shifted 1 bar (known at i-1)
    fwd_min_low: np.ndarray    # min Low over [i, i+H-1]  (forward excursion window)
    fwd_max_high: np.ndarray   # max High over [i, i+H-1]
    rev_min_low: np.ndarray    # min Low over [i-H+1, i]  (time-reversal tripwire)
    rev_max_high: np.ndarray


@dataclass
class CellDiag:
    """Per (instrument, series, domain) realized read + power + tripwire diagnostics."""

    axis: str
    instrument: str
    endpoint: str
    n_events: int
    delta: float
    ci_low: float
    mde: float
    powered: bool
    passes_floor: bool         # delta >= DELTA_STAR and ci_low > 0
    delta_labelperm: float     # tripwire-1 mean Δ (should collapse ~0)
    delta_timerev: float       # tripwire-2 Δ (should collapse ~0)


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def canonical_file(symbol: str) -> Path:
    """Resolve the INFR-003 5-year canonical time-bar file for a symbol (design §3)."""
    hits = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol.lower()}_20210602_*.parquet"))
    if not hits:
        raise FileNotFoundError(f"No 5-year canonical file for {symbol}")
    return hits[-1]


def load_train_1m(symbol: str) -> pl.DataFrame:
    """Load a symbol's 1-minute TRAIN slice: first 70% of the first-70% analysis set (design §10).

    The final-30% global holdout is never materialized; the TEST band (last 30% of the analysis set)
    is excluded — this screen touches only TRAIN.
    """
    scan = pl.scan_parquet(canonical_file(symbol)).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total * 0.7)
    train_cutoff = int(analysis_cutoff * 0.7)
    return scan.slice(0, train_cutoff).select(
        "Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"
    ).collect()


# --------------------------------------------------------------------------- #
# Pure computation — forward/backward excursion windows + exec-domain assembly
# --------------------------------------------------------------------------- #
def _window_extremes(arr: np.ndarray, h: int, forward: bool) -> tuple[np.ndarray, np.ndarray]:
    """Rolling min & max of ``arr`` over an ``h``-bar window (forward ``[i,i+h-1]`` or backward)."""
    n = arr.shape[0]
    vmin = np.full(n, np.nan, dtype=np.float64)
    vmax = np.full(n, np.nan, dtype=np.float64)
    if n < h:
        return vmin, vmax
    win = sliding_window_view(arr, h)                              # rows start at 0..n-h
    starts = np.arange(n - h + 1)
    if forward:                                                     # window [i, i+h-1] -> index i
        vmin[starts] = win.min(axis=1)
        vmax[starts] = win.max(axis=1)
    else:                                                           # window [i-h+1, i] -> index i
        ends = starts + h - 1
        vmin[ends] = win.min(axis=1)
        vmax[ends] = win.max(axis=1)
    return vmin, vmax


def build_exec_domain(train_1m: pl.DataFrame, exec_min: int) -> ExecDomain:
    """Build exec-domain real-OHLC arrays + causal features from a 1-minute TRAIN slice."""
    bars = build_domain_bars(train_1m, period_minutes=exec_min).sort("CloseTime")
    o = bars["Open"].to_numpy().astype(np.float64)
    h = bars["High"].to_numpy().astype(np.float64)
    lo = bars["Low"].to_numpy().astype(np.float64)
    c = bars["Close"].to_numpy().astype(np.float64)
    ct = bars["CloseTime"].to_numpy().astype("datetime64[ns]").astype(np.int64)
    atr = wilder_atr(h, lo, c, ATR_PERIOD)
    atr_lag = np.concatenate([[np.nan], atr[:-1]])                 # ATR known at i-1
    regime = vr.regime_labels(h, lo, c)
    regime_lag = np.concatenate([[vr.REGIME_UNDEFINED], regime[:-1]])
    fmin, fmax = _window_extremes(lo, H_EXCURSION, forward=True)   # min Low / (unused) forward
    _, fhi = _window_extremes(h, H_EXCURSION, forward=True)        # max High forward
    rmin, _ = _window_extremes(lo, H_EXCURSION, forward=False)
    _, rhi = _window_extremes(h, H_EXCURSION, forward=False)
    return ExecDomain(ct=ct, open=o, high=h, low=lo, close=c, atr_lag=atr_lag,
                      regime_lag=regime_lag, fwd_min_low=fmin, fwd_max_high=fhi,
                      rev_min_low=rmin, rev_max_high=rhi)


def anchor_arrays(train_1m: pl.DataFrame, anchor_min: int) -> dict[str, np.ndarray]:
    """Anchor-domain arrays consumed by ``cross_domain_mr.anchor_series``."""
    bars = build_domain_bars(train_1m, period_minutes=anchor_min).sort("CloseTime")
    hi = bars["High"].to_numpy().astype(np.float64)
    lo = bars["Low"].to_numpy().astype(np.float64)
    cl = bars["Close"].to_numpy().astype(np.float64)
    ct = bars["CloseTime"].to_numpy().astype("datetime64[ns]").astype(np.int64)
    return {"close": cl, "high": hi, "low": lo, "hlc3": (hi + lo + cl) / 3.0,
            "logclose": np.log(cl), "ct": ct}


def excursion_series(ed: ExecDomain, dev: np.ndarray, reverse: bool = False) -> np.ndarray:
    """Signed favourable excursion toward the anchor per exec bar, ATR units (real prices).

    Fade direction from the decision-time deviation ``dev[i-1]``: ``dev>0`` -> short (favourable =
    ``Open[i] - min Low``), ``dev<0`` -> long (favourable = ``max High - Open[i]``). ``reverse`` swaps
    the forward window for the backward window (time-reversal tripwire). NaN where undefined.
    """
    n = ed.open.shape[0]
    dev_lag = np.concatenate([[np.nan], dev[:-1]])                 # decision-time deviation at bar i
    lows = ed.rev_min_low if reverse else ed.fwd_min_low
    highs = ed.rev_max_high if reverse else ed.fwd_max_high
    theta = np.full(n, np.nan, dtype=np.float64)
    valid = np.isfinite(dev_lag) & np.isfinite(ed.atr_lag) & (ed.atr_lag > 0)
    short = valid & (dev_lag > 0) & np.isfinite(lows)
    long_ = valid & (dev_lag < 0) & np.isfinite(highs)
    theta[short] = (ed.open[short] - lows[short]) / ed.atr_lag[short]
    theta[long_] = (highs[long_] - ed.open[long_]) / ed.atr_lag[long_]
    return theta


def detect_events(ed: ExecDomain, dev: np.ndarray, z: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Entry-event exec-bar indices: extreme (``|z[i-1]|>=z*``) AND MR-screen-pass on ``dev[..i-1]``.

    Only the extreme candidates are screened (an event needs both conditions, so the screen decides
    nothing where ``|z|<z*``) — a causally-identical bound on the expensive VR/HL/Hurst evaluation.
    """
    n = ed.open.shape[0]
    z_lag = np.concatenate([[np.nan], z[:-1]])
    cand = np.flatnonzero(
        (np.arange(n) >= cdm.W_S)
        & np.isfinite(z_lag) & (np.abs(z_lag) >= cdm.Z_STAR)
        & np.isfinite(theta)
    )
    events = [i for i in cand if cdm.mr_screen_pass(dev[i - cdm.W_S:i])]
    return np.asarray(events, dtype=np.int64)


# --------------------------------------------------------------------------- #
# Pure computation — matched-random control + permutation pool (regime-matched, design §5)
# --------------------------------------------------------------------------- #
def _regime_counts(regime_lag: np.ndarray, event_idx: np.ndarray) -> dict[int, int]:
    """Count events per decision-time ATR-tercile regime (drops undefined-regime events)."""
    labels = regime_lag[event_idx]
    return {int(r): int(np.count_nonzero(labels == r))
            for r in vr.REGIME_INDICES if np.count_nonzero(labels == r) > 0}


def matched_random_idx(regime_lag: np.ndarray, counts: dict[int, int], total: int,
                       rng: np.random.Generator) -> np.ndarray:
    """Regime-matched random bar indices totalling ``~total``, proportioned to ``counts`` (design §5)."""
    n_events = sum(counts.values())
    if n_events == 0:
        return np.empty(0, dtype=np.int64)
    out: list[np.ndarray] = []
    for r, n_r in counts.items():
        n_draw = n_r if total == n_events else int(round(total * n_r / n_events))
        out.append(vr.regime_matched_entries(regime_lag, r, n_draw, rng))
    return np.concatenate(out) if out else np.empty(0, dtype=np.int64)


def cell_read(theta: np.ndarray, theta_rev: np.ndarray, ed: ExecDomain, event_idx: np.ndarray,
              extreme_cand: np.ndarray, stat_kind: str, rng: np.random.Generator
              ) -> tuple[ag.CellReadInput, CellDiag] | None:
    """Assemble the gate input + per-cell diagnostics (CI at 10k boot) + both leak tripwires."""
    counts = _regime_counts(ed.regime_lag, event_idx)
    n_events = sum(counts.values())
    if n_events < 2:
        return None
    ev = event_idx[np.isin(ed.regime_lag[event_idx], list(counts))]
    cond = theta[ev]
    ctrl_idx = matched_random_idx(ed.regime_lag, counts, n_events, rng)
    pool_idx = matched_random_idx(ed.regime_lag, counts, POOL_TOTAL, rng)
    ctrl = theta[ctrl_idx][np.isfinite(theta[ctrl_idx])]
    pool = theta[pool_idx][np.isfinite(theta[pool_idx])]
    if ctrl.shape[0] < 2 or pool.shape[0] < 2:
        return None

    delta = ag._stat_1d(cond, stat_kind) - ag._stat_1d(ctrl, stat_kind)
    s_cell = ag.cell_se(cond, ctrl, stat_kind, rng, n_boot=N_BOOT_CI)
    mde = ag.Z_ONE_SIDED * s_cell if np.isfinite(s_cell) else float("nan")
    ci_low = delta - mde if np.isfinite(mde) else float("nan")
    powered = bool(n_events >= N_MIN and np.isfinite(mde) and mde <= DELTA_STAR)
    passes = bool(powered and np.isfinite(ci_low) and delta >= DELTA_STAR and ci_low > 0.0)

    # Tripwire 1 — conditioning-label permutation: pick random n_events among extreme candidates.
    lp = []
    finite_cand = extreme_cand[np.isfinite(theta[extreme_cand])]
    if finite_cand.shape[0] >= n_events:
        for _ in range(N_TRIPWIRE_PERM):
            pseudo = rng.choice(finite_cand, size=n_events, replace=False)
            lp.append(ag._stat_1d(theta[pseudo], stat_kind) - ag._stat_1d(ctrl, stat_kind))
    delta_lp = float(np.mean(lp)) if lp else float("nan")

    # Tripwire 2 — forward-excursion time-reversal: same events, backward window.
    cond_rev = theta_rev[ev][np.isfinite(theta_rev[ev])]
    ctrl_rev = theta_rev[ctrl_idx][np.isfinite(theta_rev[ctrl_idx])]
    delta_rev = (ag._stat_1d(cond_rev, stat_kind) - ag._stat_1d(ctrl_rev, stat_kind)
                 if cond_rev.shape[0] and ctrl_rev.shape[0] else float("nan"))

    cell_id = ed_cell_id(ev.shape[0])
    gate_in = ag.CellReadInput(cell_id=cell_id, cond_values=cond, ctrl_values=ctrl,
                               pool_values=pool, n_cond=int(cond.shape[0]), underpowered=not powered)
    diag = CellDiag(axis="", instrument="", endpoint=stat_kind, n_events=int(n_events),
                    delta=float(delta), ci_low=float(ci_low), mde=float(mde), powered=powered,
                    passes_floor=passes, delta_labelperm=delta_lp, delta_timerev=float(delta_rev))
    return gate_in, diag


def ed_cell_id(n: int) -> str:
    """Opaque per-cell id (event count) — the axis/instrument labels are set by the caller."""
    return f"n{n}"


# --------------------------------------------------------------------------- #
# Orchestration — per-instrument feature build, per-axis screening
# --------------------------------------------------------------------------- #
def build_baskets(train: dict[str, pl.DataFrame], exec_min: int, instruments: tuple[str, ...]
                  ) -> dict[str, np.ndarray | None]:
    """Exec-aligned S5 basket log-price per instrument (equal-wt class-mates, timestamp-aligned).

    Each mate is TRAIN-sliced on its **own** timeline before alignment (design §10), then joined by
    exec ``CloseTime`` (never bar index). Lone-class instruments -> ``None`` (UNPOWERED S5).
    """
    log_by_inst: dict[str, pl.DataFrame] = {}
    for sym in instruments:
        bars = build_domain_bars(train[sym], period_minutes=exec_min).sort("CloseTime")
        log_by_inst[sym] = bars.select(
            "CloseTime", pl.col("Close").log().alias(f"lp_{sym}"))
    out: dict[str, np.ndarray | None] = {}
    for sym in instruments:
        mates = [m for m in _S5_MATES.get(sym, ()) if m in log_by_inst]
        base = log_by_inst[sym].select("CloseTime")
        if not mates:
            out[sym] = None
            continue
        joined = base
        for m in mates:
            joined = joined.join(log_by_inst[m], on="CloseTime", how="left")
        mat = joined.select([f"lp_{m}" for m in mates]).to_numpy()
        basket = np.nanmean(mat, axis=1)                          # drop-to-available mates
        basket[np.all(~np.isfinite(mat), axis=1)] = np.nan        # no mate -> UNPOWERED bar
        out[sym] = basket
    return out


def run_axis(axis: str, cells_in: list[ag.CellReadInput], diags: list[CellDiag],
             rng: np.random.Generator) -> dict:
    """Frozen-gate axis admission (max-statistic permuted null over the two endpoints) + majority read."""
    subs = []
    for (name, kind) in ENDPOINTS:
        endpoint_cells = [c for c, d in zip(cells_in, diags) if d.endpoint == kind]
        subs.append(ag.run_sub_screen(name, name, kind, endpoint_cells, rng))
    max_powered = max((s.n_powered_cells for s in subs), default=0)
    combined = ag.combine_axis(axis, subs, null_band=(0, 1)) if max_powered else None

    read = {}
    for (name, kind) in ENDPOINTS:
        dk = [d for d in diags if d.endpoint == kind]
        powered = [d for d in dk if d.powered]
        n_pass = sum(d.passes_floor for d in powered)
        read[name] = {
            "n_powered": len(powered),
            "n_pass_floor": int(n_pass),
            "majority": bool(powered and n_pass / len(powered) >= MAJORITY),
            "eligible": bool(len(powered) >= MIN_POWERED_CELLS),
        }
    return {
        "axis": axis,
        "perm_p": float(combined.perm_p) if combined else float("nan"),
        "s_m": int(combined.s_m) if combined else 0,
        "s_star": int(combined.s_star) if combined else 0,
        "disposition": combined.disposition if combined else "UNPOWERED (no powered cell)",
        "endpoint_read": read,
    }


def screen(instruments: tuple[str, ...], n_perm_note: str) -> dict:
    """Full screen: build features, assemble cells, run the 15 series×domain axes + cross-axis Holm."""
    rng = np.random.default_rng(SEED)
    logger.info("Loading TRAIN slices for %d instruments", len(instruments))
    train = {sym: load_train_1m(sym) for sym in tqdm(instruments, desc="load 1m TRAIN")}

    exec_mins = sorted({e for (_, e) in cdm.DOMAIN_PAIRS.values()})
    baskets = {e: build_baskets(train, e, instruments) for e in exec_mins}

    per_cell: list[CellDiag] = []
    axis_inputs: dict[str, tuple[list[ag.CellReadInput], list[CellDiag]]] = {}

    for series in tqdm(cdm.SERIES, desc="series"):
        for pair, (a_min, e_min) in cdm.DOMAIN_PAIRS.items():
            axis = f"{series}|{pair}"
            axis_inputs[axis] = ([], [])
            for sym in instruments:
                ed = build_exec_domain(train[sym], e_min)
                anc = anchor_arrays(train[sym], a_min)
                basket = baskets[e_min][sym] if series == "S5_SPREAD" else None
                asr = cdm.anchor_series(series, ed.close, ed.ct, anc, basket)
                if not np.any(np.isfinite(asr.dev)):
                    continue
                theta = excursion_series(ed, asr.dev, reverse=False)
                theta_rev = excursion_series(ed, asr.dev, reverse=True)
                events = detect_events(ed, asr.dev, asr.z, theta)
                if events.shape[0] < 2:
                    continue
                z_lag = np.concatenate([[np.nan], asr.z[:-1]])
                extreme = np.flatnonzero(np.isfinite(z_lag) & (np.abs(z_lag) >= cdm.Z_STAR))
                for (name, kind) in ENDPOINTS:
                    res = cell_read(theta, theta_rev, ed, events, extreme, kind, rng)
                    if res is None:
                        continue
                    gate_in, diag = res
                    diag.axis, diag.instrument = axis, sym
                    axis_inputs[axis][0].append(gate_in)
                    axis_inputs[axis][1].append(diag)
                    per_cell.append(diag)

    axis_results = [run_axis(ax, ci, dg, rng) for ax, (ci, dg) in axis_inputs.items()]
    # Cross-axis Holm over the axis permuted-p values (design §5).
    pvals = [a["perm_p"] if np.isfinite(a["perm_p"]) else 1.0 for a in axis_results]
    holm = ag.holm_adjust(pvals)
    for a, hp in zip(axis_results, holm):
        a["holm_p"] = float(hp)
        a["holm_admit"] = bool(hp <= ag.FWER)

    verdict = adjudicate(axis_results, per_cell)
    return {"axis_results": axis_results, "verdict": verdict,
            "per_cell": [asdict(d) for d in per_cell], "n_perm_note": n_perm_note}


def adjudicate(axis_results: list[dict], per_cell: list[CellDiag]) -> dict:
    """Predeclared §7 verdict: ADMIT-TO-EXPLORE / EXONERATE / INCONCLUSIVE (leak-gated)."""
    admitting = []
    for a in axis_results:
        if not a["holm_admit"]:
            continue
        for name, rd in a["endpoint_read"].items():
            if rd["eligible"] and rd["majority"]:
                # leak gate on this axis's passing powered cells
                axis_cells = [d for d in per_cell
                              if d.axis == a["axis"] and d.powered and d.passes_floor
                              and d.endpoint == dict(ENDPOINTS)[name]]
                lp_ok = all(abs(d.delta_labelperm) < DELTA_STAR for d in axis_cells if
                            np.isfinite(d.delta_labelperm))
                tr_ok = all(d.delta_timerev < DELTA_STAR for d in axis_cells if
                            np.isfinite(d.delta_timerev))
                admitting.append({"axis": a["axis"], "endpoint": name,
                                  "leak_clean": bool(lp_ok and tr_ok),
                                  "long_tail_flag": name == "tailmass"})
    clean = [x for x in admitting if x["leak_clean"]]
    n_eligible = sum(any(rd["eligible"] for rd in a["endpoint_read"].values()) for a in axis_results)
    if clean:
        outcome = "ADMIT-TO-EXPLORE"
    elif n_eligible < 0.5 * len(axis_results):
        outcome = "INCONCLUSIVE"
    else:
        outcome = "EXONERATE"
    return {"outcome": outcome, "admitting_axes": admitting, "n_eligible_axes": int(n_eligible),
            "n_axes": len(axis_results)}


# --------------------------------------------------------------------------- #
# Plotting (P1–P6, design §9) — bounded inputs from the screen pass
# --------------------------------------------------------------------------- #
def _cell_frame(per_cell: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(per_cell) if per_cell else pl.DataFrame(
        schema={"axis": pl.Utf8, "instrument": pl.Utf8, "endpoint": pl.Utf8})


def plot_delta_heatmaps(df: pl.DataFrame, path: Path) -> None:
    """P1 — per-series Δ heatmaps over domain×instrument (median endpoint, small multiples)."""
    sns.set_theme(style="white")
    sub = df.filter(pl.col("endpoint") == ag.STAT_MEDIAN)
    fig, axes = plt.subplots(1, len(cdm.SERIES), figsize=(4 * len(cdm.SERIES), 5), squeeze=False)
    for k, series in enumerate(cdm.SERIES):
        ax = axes[0][k]
        s = sub.filter(pl.col("axis").str.starts_with(series))
        if s.height:
            piv = s.with_columns(pl.col("axis").str.split("|").list.get(1).alias("pair")) \
                   .pivot(values="delta", index="instrument", on="pair", aggregate_function="first")
            data = piv.drop("instrument").to_pandas()
            sns.heatmap(data, ax=ax, cmap="RdBu_r", center=0, vmin=-0.5, vmax=0.5,
                        yticklabels=piv["instrument"].to_list(), cbar=k == len(cdm.SERIES) - 1)
        ax.set_title(series, fontsize=10)
    fig.suptitle("P1 — Δ(cond−ctrl) median excursion (ATR) by series×domain×instrument")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_axis_admission(axis_results: list[dict], path: Path) -> None:
    """P2 — cross-axis admission: S_M vs S* (max-stat null) per axis."""
    sns.set_theme(style="whitegrid")
    labels = [a["axis"] for a in axis_results]
    fig, ax = plt.subplots(figsize=(10, 8))
    y = np.arange(len(labels))
    ax.barh(y, [a["s_m"] for a in axis_results], color="steelblue", label="S_M (realized)")
    ax.plot([a["s_star"] for a in axis_results], y, "rx", label="S* (max-stat null)")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("cells beating random")
    ax.set_title("P2 — per-axis max-statistic admission")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_shape_tailmass(df: pl.DataFrame, path: Path) -> None:
    """P3 — tailmass-endpoint Δ map (shape / long-tail read)."""
    sns.set_theme(style="white")
    sub = df.filter(pl.col("endpoint") == ag.STAT_TAILMASS_UPPER)
    fig, ax = plt.subplots(figsize=(9, 7))
    if sub.height:
        piv = sub.pivot(values="delta", index="instrument", on="axis", aggregate_function="first")
        data = piv.drop("instrument").to_pandas()
        sns.heatmap(data, ax=ax, cmap="RdBu_r", center=0, yticklabels=piv["instrument"].to_list(),
                    cbar_kws={"label": "Δ tailmass (#{θ≥1 ATR}/n)"})
        ax.set_xticklabels(ax.get_xticklabels(), fontsize=6, rotation=90)
    ax.set_title("P3 — Δ upper-tailmass by axis×instrument")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leak_tripwires(df: pl.DataFrame, path: Path) -> None:
    """P4 — leak-tripwire before/after: real Δ vs label-perm Δ vs time-reversal Δ (powered cells)."""
    sns.set_theme(style="whitegrid")
    sub = df.filter(pl.col("powered"))
    fig, ax = plt.subplots(figsize=(8, 6))
    if sub.height:
        ax.scatter(sub["delta"], sub["delta_labelperm"], s=12, alpha=0.6, label="label-perm")
        ax.scatter(sub["delta"], sub["delta_timerev"], s=12, alpha=0.6, marker="^",
                   label="time-reversal")
        lim = float(max(0.6, sub["delta"].abs().max() or 0.6))
        ax.plot([-lim, lim], [0, 0], "k--", lw=0.8)
        ax.axvline(DELTA_STAR, color="red", ls=":", lw=0.8, label="Δ*")
    ax.set_xlabel("real Δ (ATR)")
    ax.set_ylabel("tripwire Δ (ATR)")
    ax.set_title("P4 — leak tripwires must collapse to ~0")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_power_map(df: pl.DataFrame, path: Path) -> None:
    """P5 — MDE + powered/UNPOWERED map (median endpoint)."""
    sns.set_theme(style="white")
    sub = df.filter(pl.col("endpoint") == ag.STAT_MEDIAN)
    fig, ax = plt.subplots(figsize=(9, 7))
    if sub.height:
        piv = sub.pivot(values="mde", index="instrument", on="axis", aggregate_function="first")
        data = piv.drop("instrument").to_pandas()
        sns.heatmap(data, ax=ax, cmap="viridis_r", vmin=0, vmax=0.5,
                    yticklabels=piv["instrument"].to_list(), cbar_kws={"label": "MDE (ATR)"})
        ax.set_xticklabels(ax.get_xticklabels(), fontsize=6, rotation=90)
    ax.set_title(f"P5 — per-cell MDE (Δ*={DELTA_STAR}); blank/high = UNPOWERED")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_counts(df: pl.DataFrame, path: Path) -> None:
    """P6 — per-cell event counts vs N_min (availability distribution / powered fraction proxy)."""
    sns.set_theme(style="whitegrid")
    sub = df.filter(pl.col("endpoint") == ag.STAT_MEDIAN)
    fig, ax = plt.subplots(figsize=(9, 6))
    if sub.height:
        for series in cdm.SERIES:
            s = sub.filter(pl.col("axis").str.starts_with(series))
            if s.height:
                ax.scatter([series] * s.height, s["n_events"], s=14, alpha=0.5)
        ax.axhline(N_MIN, color="red", ls=":", label=f"N_min={N_MIN}")
    ax.set_yscale("symlog")
    ax.set_ylabel("events per cell")
    ax.set_title("P6 — conditioned-event availability by series")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-008 cross-domain MR availability screen")
    parser.add_argument("--quick", action="store_true", help="4-instrument smoke subset")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    instruments = QUICK_INSTRUMENTS if args.quick else ALL_INSTRUMENTS
    out = screen(instruments, n_perm_note=f"N_PERM={ag.N_PERM}, B_SE={ag.B_SE}, CI_boot={N_BOOT_CI}")

    df = _cell_frame(out["per_cell"])
    df.write_parquet(RESULTS_DIR / "per_cell.parquet")
    (RESULTS_DIR / "axis_results.json").write_text(json.dumps(out["axis_results"], indent=2))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(
        {"verdict": out["verdict"], "n_perm_note": out["n_perm_note"],
         "instruments": list(instruments), "quick": args.quick}, indent=2))

    plot_delta_heatmaps(df, PLOTS_DIR / "P1_delta_heatmaps.png")
    plot_axis_admission(out["axis_results"], PLOTS_DIR / "P2_axis_admission.png")
    plot_shape_tailmass(df, PLOTS_DIR / "P3_tailmass.png")
    plot_leak_tripwires(df, PLOTS_DIR / "P4_leak_tripwires.png")
    plot_power_map(df, PLOTS_DIR / "P5_power_map.png")
    plot_event_counts(df, PLOTS_DIR / "P6_event_counts.png")

    v = out["verdict"]
    logger.info("VERDICT: %s | admitting=%d | eligible axes=%d/%d",
                v["outcome"], len(v["admitting_axes"]), v["n_eligible_axes"], v["n_axes"])
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
