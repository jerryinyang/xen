"""EXP-074 — TRAIN-only substrate-wide loser-tail characterization of the 99-cell MA-native
N-PARTIAL-V2A harami.

Implements the analysis plan in ``python/experiments/EXP-074/analysis-plan.md`` for
CF-HA-HARAMI-001 / HYP-027. Diagnostic, TRAIN-only, **0 candidate slots, 0 counted TEST
reads** (D0-amendment-005 + D0-amendment-006). The next-21% TEST stratum and the final-30%
holdout are never sliced; forward resolution of TRAIN entries clips at the TRAIN edge
(boundary entries censor).

Pipeline:
  (1) Resolve N-PARTIAL-V2A events on the TRAIN window of every cell in the full 99-cell
      MA-substrate matrix (the EXP-068 grid), reusing the frozen EXP-068 machinery unchanged
      in semantics (the only departure from EXP-071 is the entry mask flipped to TRAIN:
      ``entry_epoch <= train_end``).
  (2) Extract the 14 causal entry-time features per qualifying event, aligned to the arm's
      ``r_e`` via the certified ``qual`` mask + stable entry-order argsort.
  (3) Build three tail-target framings (T-A extreme+sign, T-B mean-below-median, T-C
      continuous) and rank every feature by its separation of each framing (rank-biserial /
      Spearman / phi / Kruskal-Wallis + Cramér's V), with moving-block bootstrap CIs on the
      lead and above-bar features, per cell.
  (4) Aggregate **per domain** (BINDING — pooling masks domain structure) into a dual-metric
      four-tier verdict per domain: INCONCLUSIVE_POWER (< MIN_POWERED_PER_DOMAIN powered cells),
      SEPARATOR_FOUND (>=1 uniform lever: a feature candidate in >= SUBSTRATE_SHARE_MIN of the
      domain's powered cells with a material within-domain median CI), SEPARABLE_NO_UNIFORM_LEVER
      (per-cell any-feature separability rate >= DOMAIN_SEPARABLE_RATE but no uniform lever), or
      NO_SEPARATOR. The pooled substrate verdict is retained as a DISCLOSED-ONLY secondary line.
      GBPUSD-5m is reported as a named continuity cell (not the binding object).

This script does NOT select a filter, tune any parameter, or read TEST/holdout.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup — import the frozen EXP-068 machinery by module (no side effects;
# its orchestration is guarded by ``if __name__ == "__main__"``).
# --------------------------------------------------------------------------- #
EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_ROOT = EXPERIMENT_DIR.parent
EXP068_CODE = EXPERIMENTS_ROOT / "EXP-068" / "code"
if str(EXP068_CODE) not in sys.path:
    sys.path.insert(0, str(EXP068_CODE))
import run_experiment as exp068  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen; reused from EXP-068 — none tuned)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-074"
BASE_SEED = exp068.BASE_SEED                  # 20260616
N_BOOT = exp068.N_BOOT                        # 10_000
BOOT_BATCH = exp068.BOOT_BATCH
POWER_FLOOR = exp068.POWER_FLOOR              # 30 — tail-cell floor (analysis-plan §Power)
ANALYSIS_FRACTION = exp068.ANALYSIS_FRACTION  # 0.7
TRAIN_FRACTION = exp068.TRAIN_FRACTION        # 0.7 (of the analysis set)
MA_FAST, MA_SLOW = exp068.MA_FAST, exp068.MA_SLOW
ATR_PERIOD = exp068.ATR_PERIOD
BINDING_OBJECT = "nat"
BINDING_ARM = "PARTIAL-V2A"
STAT_WINDOW, STAT_MIN_WINDOW, STAT_Q = 20, 5, 0.75   # live_strong_stat defaults

# Feature-definition constants (declared; not tuned, not selected).
ATR_PCTILE_WINDOW = 500   # trailing bars for the ATR percentile-rank feature (f8)
MATERIAL_BAR = 0.15       # |effect| material-separation bar (analysis-plan §Material bar)
SUBSTRATE_SHARE_MIN = 0.50  # single-feature breadth: share of cells a feature must separate
MIN_POWERED_CELLS = 30      # pooled-substrate INCONCLUSIVE_POWER floor (disclosed-only)
MIN_POWERED_PER_DOMAIN = 5  # per-domain INCONCLUSIVE_POWER floor (binding domain verdict)
DOMAIN_SEPARABLE_RATE = 0.50  # per-cell any-feature separability rate for SEPARABLE_NO_UNIFORM_LEVER
# UTC session buckets by hour (feature f13; descriptive, not tuned).
SESSION_BY_HOUR = {**{h: "Asia" for h in (22, 23, 0, 1, 2, 3, 4, 5, 6)},
                   **{h: "London" for h in (7, 8, 9, 10, 11)},
                   **{h: "Overlap" for h in (12, 13, 14, 15)},
                   **{h: "NY" for h in (16, 17, 18, 19, 20, 21)}}

# Cells (instrument, domain, is_4h): the full 99-cell MA-substrate matrix — derived from the
# frozen EXP-068 grid (17 instruments x 6 domains minus the 3 structurally-excluded cells).
# No cell is hand-picked or pre-excluded by prior outcome (D0-amendment-006).
CELLS: tuple[tuple[str, str, bool], ...] = tuple(
    (inst, dom, dom == "4h")
    for inst in exp068.INSTRUMENTS
    for dom in exp068.DOMAINS
    if (inst, dom) not in exp068.EXCLUDED_CELLS
)
# GBPUSD-5m: named continuity cell for comparison with EXP-071/074-prior; NOT the binding
# object — the verdict is substrate-wide (scope §Success/Failure).
CONTINUITY_CELL = "GBPUSD-5m"

# Continuous features (rank-biserial vs binary, Spearman vs T-C). Order fixes f-index.
CONT_FEATURES = ("msofar_atr", "ss_excess_ratio", "ss_excess_diff", "disp_mad_med",
                 "favdist_atr", "move_age_bars", "move_count_k", "atr_pctile",
                 "harami_compression", "harami_body_atr", "entry_range_atr",
                 "ma_sep_atr", "ma_slope_atr")
# Binary features (phi/tail-rate-diff vs binary; rank-biserial vs T-C).
BIN_FEATURES = ("polarity_agree_ha0", "polarity_agree_ha1", "rd_long")
# Multi-level categorical (Kruskal-Wallis + Cramér's V; never linear/circular).
CAT_FEATURES = ("session", "day_of_week")
# Lead features always bootstrapped (H1 magnitude bound, H2 polarity).
LEAD_FEATURES = ("msofar_atr", "polarity_agree_ha0")

RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellEvents:
    """Per-event TRAIN N-PARTIAL-V2A returns + causal feature matrix for one cell."""

    cell: str
    instrument: str
    domain: str
    is_4h: bool
    r_e: np.ndarray                       # qualifying returns, entry order
    features: dict[str, np.ndarray]       # feature -> array aligned to r_e (object for cat)
    coverage: dict[str, int]              # feature -> finite/defined count
    n_events: int
    censored: int


# --------------------------------------------------------------------------- #
# I/O helpers (TRAIN-only loader — no freeze gate, no TEST/holdout slice)
# --------------------------------------------------------------------------- #
def load_train_1m(instrument: str) -> tuple[pl.DataFrame, int]:
    """Return (train_1m, train_end_epoch_s) for one instrument; TRAIN slice only.

    TRAIN = first 49% (0.7 x 0.7) of the chronological file. The next-21% TEST stratum
    ``[train_cutoff, analysis_cutoff)`` and the final-30% holdout ``[analysis_cutoff, total)``
    are never sliced or materialized.
    """
    path = exp068.find_source_file(instrument)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    scan = pl.scan_parquet(path).select(cols).sort("CloseTime")
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_cutoff = int(total * ANALYSIS_FRACTION)
    train_cutoff = int(analysis_cutoff * TRAIN_FRACTION)
    train_1m = scan.slice(0, train_cutoff).collect()   # TEST + holdout never sliced here
    if train_1m.is_empty():
        raise RuntimeError(f"{instrument}: empty TRAIN slice")
    if not train_1m.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    train_end = int(train_1m.get_column("CloseTime").dt.epoch("s")[-1])
    return train_1m, train_end


# --------------------------------------------------------------------------- #
# Pure computation — causal entry-feature extraction
# --------------------------------------------------------------------------- #
def strong_stat_detail(
    k_inclusive: np.ndarray, m_sofar: np.ndarray, magnitudes: np.ndarray,
    window: int = STAT_WINDOW, min_window: int = STAT_MIN_WINDOW, q: float = STAT_Q,
) -> dict[str, np.ndarray]:
    """Per-entry trailing-window p75 threshold, median, MAD (mirrors live_strong_stat).

    Returns ``defined`` (bool), ``thr`` (p75), ``med``, ``mad`` — all causal (trailing
    confirmed moves with ConfirmTime <= entry, inclusive of the binding move ``k``).
    """
    n = int(k_inclusive.shape[0])
    defined = np.zeros(n, dtype=bool)
    thr = np.full(n, np.nan)
    med = np.full(n, np.nan)
    mad = np.full(n, np.nan)
    for i in range(n):
        kk = int(k_inclusive[i])
        if kk < 0:
            continue
        lo = max(0, kk - window + 1)
        w = magnitudes[lo:kk + 1]
        if w.shape[0] < min_window:
            continue
        defined[i] = True
        thr[i] = float(np.quantile(w, q, method="linear"))
        m = float(np.median(w))
        med[i] = m
        mad[i] = float(np.median(np.abs(w - m)))
    return {"defined": defined, "thr": thr, "med": med, "mad": mad}


def harami_directions(combined: pl.DataFrame, bar_epoch: np.ndarray,
                      entry_idx: np.ndarray) -> dict[str, np.ndarray]:
    """Re-detect HA haramis on the same domain bars and align directions/bodies to entry_idx.

    Reproduces ``exp068.harami_entry_indices`` exactly so the mapped grid indices equal the
    resolve path's ``entry_idx`` (asserted); returns the per-event HA polarity and body fields.
    """
    ha = exp068.generate_heiken_ashi(combined)
    haramis = exp068.detect_ha_harami(ha)
    if haramis.height == 0:
        empty = np.empty(0)
        return {"grid_idx": np.empty(0, dtype=np.int64), "ha0_dir": empty, "ha1_dir": empty,
                "inner_body": empty, "prior_body": empty}
    he = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    grid_idx = exp068._map_to_grid(bar_epoch, he, "harami HA0Time")
    if not np.array_equal(grid_idx, entry_idx):
        raise RuntimeError("harami re-detection grid indices diverge from resolve entry_idx")
    body_max = haramis.get_column("BodyMax").to_numpy().astype(np.float64)
    body_min = haramis.get_column("BodyMin").to_numpy().astype(np.float64)
    prev_max = haramis.get_column("PrevBodyMax").to_numpy().astype(np.float64)
    prev_min = haramis.get_column("PrevBodyMin").to_numpy().astype(np.float64)
    return {"grid_idx": grid_idx,
            "ha0_dir": haramis.get_column("HA0Direction").to_numpy().astype(np.float64),
            "ha1_dir": haramis.get_column("HA1Direction").to_numpy().astype(np.float64),
            "inner_body": body_max - body_min, "prior_body": prev_max - prev_min}


def trailing_pctile(values: np.ndarray, idx: np.ndarray, window: int) -> np.ndarray:
    """Causal trailing percentile-rank of values[idx] within the prior ``window`` bars.

    pct = fraction of finite values in (idx-window, idx] that are <= values[idx]. NaN when
    fewer than ``min_window`` (= STAT_MIN_WINDOW) finite trailing samples exist.
    """
    out = np.full(idx.shape[0], np.nan)
    for j, gi in enumerate(idx):
        lo = max(0, int(gi) - window + 1)
        w = values[lo:int(gi) + 1]
        w = w[np.isfinite(w)]
        if w.shape[0] < STAT_MIN_WINDOW or not np.isfinite(values[int(gi)]):
            continue
        out[j] = float(np.mean(w <= values[int(gi)]))
    return out


def session_labels(epoch: np.ndarray) -> np.ndarray:
    """UTC session bucket per entry epoch (object array; circular hour handled by bucketing)."""
    hours = ((epoch // 3600) % 24).astype(int)
    return np.array([SESSION_BY_HOUR[int(h)] for h in hours], dtype=object)


def day_of_week_labels(epoch: np.ndarray) -> np.ndarray:
    """UTC day-of-week per entry epoch (object array of Mon..Sun)."""
    names = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    dt = epoch.astype("datetime64[s]")
    dow = ((dt.astype("datetime64[D]").astype(np.int64) + 3) % 7)  # 1970-01-01 = Thu
    return np.array([names[int(d)] for d in dow], dtype=object)


def resolve_cell_events(instrument: str, domain: str, is_4h: bool,
                        cell_index: int) -> CellEvents:
    """Resolve TRAIN N-PARTIAL-V2A events + the 14 causal features for one cell.

    Mirrors EXP-071's resolution exactly except the entry mask is TRAIN
    (``entry_epoch <= train_end``) and the domain bars are built over the TRAIN 1-minute
    slice only (forward scans clip at the TRAIN edge -> boundary entries censor; no TEST row).
    """
    train_1m, train_end = load_train_1m(instrument)
    period, coverage = exp068.DOMAINS[domain]
    combined = exp068.build_domain(train_1m, period, coverage, train_end).sort("CloseTime")
    ohlc = exp068.real_ohlc(combined)
    if not bool(np.all(np.diff(ohlc["epoch"]) > 0)):
        raise RuntimeError(f"{instrument}-{domain}: TRAIN domain bars not strictly increasing")
    atr = exp068.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = exp068.harami_entry_indices(combined, ohlc["epoch"])
    cell = f"{instrument}-{domain}"
    if entry_idx.shape[0] == 0:
        return CellEvents(cell, instrument, domain, is_4h, np.empty(0), {}, {}, 0, 0)

    entry_epoch = ohlc["epoch"][entry_idx]
    ma = exp068._ma_context(ohlc, atr, entry_idx, entry_epoch)
    if ma.get("empty"):
        return CellEvents(cell, instrument, domain, is_4h, np.empty(0), {}, {}, 0, 0)

    # TRAIN-window mask (complement of EXP-071's TEST mask) ^ /STRONG-STAT gate.
    train_entry = entry_epoch <= train_end
    cond = ma["stat"]["retained_p75"] & train_entry
    last_idx = int(ohlc["close"].shape[0]) - 1

    arm = exp068.ARM_BY_ID[BINDING_ARM]
    res = exp068.signal_arm(BINDING_OBJECT, arm, ohlc, ma, cond, entry_idx, last_idx, cell_index)
    if res.m == 0:
        return CellEvents(cell, instrument, domain, is_4h, np.empty(0), {}, {}, 0,
                          int(res.data_censored))

    # ---- Align features to r_e via the certified qual mask + stable entry-order argsort ----
    qual = res.qual
    order = np.argsort(entry_idx[qual], kind="stable")
    if not np.allclose(res.r_full[qual][order], res.r_e, equal_nan=True):
        raise RuntimeError(f"{cell}: feature/r_e alignment check failed")

    def align(arr: np.ndarray) -> np.ndarray:
        return arr[qual][order]

    state = ma["state"]
    atr_entry = ma["atr_entry"]
    m_sofar = state.m_sofar
    seg = ma["seg"]
    ss = strong_stat_detail(state.k, m_sofar, seg["magnitude"])
    hd = harami_directions(combined, ohlc["epoch"], entry_idx)
    rd = state.rd.astype(np.float64)

    # MA(20,50) separation + slope at entry (ATR-normalised).
    diff = exp068._sma(ohlc["close"], MA_FAST) - exp068._sma(ohlc["close"], MA_SLOW)
    diff_entry = diff[entry_idx]
    prev = np.where(entry_idx >= 1, entry_idx - 1, entry_idx)
    diff_slope = diff_entry - diff[prev]

    with np.errstate(divide="ignore", invalid="ignore"):
        confirm_idx_k = np.where(state.k >= 0, seg["confirm_idx"][state.k], -1)
        feats_full: dict[str, np.ndarray] = {
            "msofar_atr": m_sofar / atr_entry,
            "ss_excess_ratio": m_sofar / ss["thr"],
            "ss_excess_diff": m_sofar - ss["thr"],
            "disp_mad_med": ss["mad"] / ss["med"],
            "favdist_atr": ma["fav_dist"] / atr_entry,
            "move_age_bars": (entry_idx - confirm_idx_k).astype(np.float64),
            "move_count_k": state.k.astype(np.float64),
            "atr_pctile": trailing_pctile(atr, entry_idx, ATR_PCTILE_WINDOW),
            "harami_compression": hd["inner_body"] / hd["prior_body"],
            "harami_body_atr": hd["inner_body"] / atr_entry,
            "entry_range_atr": (ohlc["high"][entry_idx] - ohlc["low"][entry_idx]) / atr_entry,
            "ma_sep_atr": diff_entry / atr_entry,
            "ma_slope_atr": diff_slope / atr_entry,
            "polarity_agree_ha0": (hd["ha0_dir"] == rd).astype(np.float64),
            "polarity_agree_ha1": (hd["ha1_dir"] == rd).astype(np.float64),
            "rd_long": (rd > 0).astype(np.float64),
        }
    # invalidate magnitude/maturity features where state/strong-stat undefined
    bad_state = ~state.valid
    for key in ("msofar_atr", "ss_excess_ratio", "ss_excess_diff", "favdist_atr",
                "move_age_bars", "move_count_k", "ma_sep_atr", "ma_slope_atr"):
        feats_full[key][bad_state] = np.nan
    for key in ("ss_excess_ratio", "ss_excess_diff", "disp_mad_med"):
        feats_full[key][~ss["defined"]] = np.nan

    sess_full = session_labels(entry_epoch)
    dow_full = day_of_week_labels(entry_epoch)

    features: dict[str, np.ndarray] = {k: align(v) for k, v in feats_full.items()}
    features["session"] = align(sess_full)
    features["day_of_week"] = align(dow_full)

    coverage = {k: int(np.isfinite(v).sum()) for k, v in features.items()
                if v.dtype != object}
    return CellEvents(cell, instrument, domain, is_4h, res.r_e, features, coverage,
                      int(res.m), int(res.data_censored))


# --------------------------------------------------------------------------- #
# Pure computation — separation / association metrics
# --------------------------------------------------------------------------- #
def _clean_pair(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Finite-paired subset of two equal-length arrays."""
    m = np.isfinite(x) & np.isfinite(y)
    return x[m], y[m]


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks (1..n) with tie-averaging — scipy.stats.rankdata('average') equivalent."""
    a = np.asarray(a, dtype=np.float64)
    n = a.shape[0]
    sorter = np.argsort(a, kind="mergesort")
    inv = np.empty(n, dtype=np.int64)
    inv[sorter] = np.arange(n)
    sa = a[sorter]
    obs = np.r_[True, sa[1:] != sa[:-1]]
    dense = np.cumsum(obs)[inv]
    counts = np.r_[np.flatnonzero(obs), n]
    return 0.5 * (counts[dense] + counts[dense - 1] + 1)


def rank_biserial(feature: np.ndarray, tail: np.ndarray) -> tuple[float, float, int, int]:
    """Rank-biserial r = 2*AUC-1 for feature in tail-group vs rest (Mann-Whitney U effect size).

    Positive r => tail (loser) events have systematically HIGHER feature values.
    Returns (r, auc, n_tail, n_rest); NaN when a group is empty or degenerate.
    """
    f = feature.astype(np.float64)
    ok = np.isfinite(f)
    f, t = f[ok], np.asarray(tail)[ok]
    g1 = f[t == 1]
    g0 = f[t == 0]
    n1, n0 = int(g1.shape[0]), int(g0.shape[0])
    if n1 == 0 or n0 == 0:
        return float("nan"), float("nan"), n1, n0
    ranks = _rankdata(f)
    r1 = float(ranks[t == 1].sum())
    u1 = r1 - n1 * (n1 + 1) / 2.0          # Mann-Whitney U for group 1
    auc = float(u1 / (n1 * n0))
    return 2.0 * auc - 1.0, auc, n1, n0


def spearman_loss(feature: np.ndarray, r_e: np.ndarray) -> float:
    """Loss-association = -Spearman(feature, r_e): positive => higher feature, more loss."""
    f, r = _clean_pair(feature.astype(np.float64), r_e)
    if f.shape[0] < 3 or np.all(f == f[0]) or np.all(r == r[0]):
        return float("nan")
    rho = float(np.corrcoef(_rankdata(f), _rankdata(r))[0, 1])
    return -rho if np.isfinite(rho) else float("nan")


def phi_binary(feature: np.ndarray, tail: np.ndarray) -> tuple[float, float]:
    """Phi (MCC) of a binary feature vs binary tail + tail-rate difference (feat=1 minus feat=0).

    Positive => feature==1 associated with MORE tail membership (more loss).
    """
    f = feature.astype(np.float64)
    ok = np.isfinite(f)
    f, t = f[ok], tail[ok]
    if np.all(f == f[0]) or np.all(t == t[0]):
        return float("nan"), float("nan")
    phi = float(np.corrcoef(f, t)[0, 1])
    r1 = float(t[f == 1].mean()) if (f == 1).any() else float("nan")
    r0 = float(t[f == 0].mean()) if (f == 0).any() else float("nan")
    return phi, r1 - r0


def cramers_v(labels: np.ndarray, tail: np.ndarray) -> float:
    """Cramér's V of a categorical feature vs binary tail (unsigned association)."""
    cats = [c for c in np.unique(labels)]
    if len(cats) < 2:
        return float("nan")
    table = np.array([[int(((labels == c) & (tail == t)).sum()) for t in (0, 1)] for c in cats],
                     dtype=np.float64)
    n = table.sum()
    if n == 0 or (table.sum(axis=0) == 0).any() or (table.sum(axis=1) == 0).any():
        return float("nan")
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / n
    chi2 = float(((table - expected) ** 2 / expected).sum())
    k = min(table.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 else float("nan")


def kruskal_epsilon_sq(labels: np.ndarray, r_e: np.ndarray) -> float:
    """Epsilon-squared effect size from the Kruskal-Wallis H across categorical groups vs r_e.

    H = 12/(N(N+1)) * sum(R_g^2/n_g) - 3(N+1) over pooled average ranks; eps^2 = (H-k+1)/(N-k).
    """
    fin = np.isfinite(r_e)
    lab, r = np.asarray(labels)[fin], r_e[fin]
    cats = [c for c in np.unique(lab)]
    sizes = [int((lab == c).sum()) for c in cats]
    cats = [c for c, s in zip(cats, sizes) if s > 0]
    n = int(r.shape[0])
    k = len(cats)
    if k < 2 or n <= k or np.all(r == r[0]):
        return float("nan")
    ranks = _rankdata(r)
    s = sum((ranks[lab == c].sum()) ** 2 / (lab == c).sum() for c in cats)
    h = 12.0 / (n * (n + 1)) * s - 3.0 * (n + 1)
    return float((h - k + 1) / (n - k))


# --------------------------------------------------------------------------- #
# Pure computation — moving-block bootstrap on an effect estimate
# --------------------------------------------------------------------------- #
def block_bootstrap_ci(effect_fn, arrays: tuple[np.ndarray, ...], n: int, seed: list[int],
                       n_boot: int = N_BOOT) -> dict[str, float]:
    """Moving-block bootstrap CI on an effect over the chronological event sequence.

    ``arrays`` are equal-length per-event arrays (feature, target, ...) resampled jointly in
    contiguous blocks of length b = round(n**(1/3)). Returns 1s/2s percentile bounds.
    """
    if n < POWER_FLOOR:
        return {"ci_low_1s": float("nan"), "ci_hi_1s": float("nan"),
                "ci_low_2s": float("nan"), "ci_hi_2s": float("nan"), "block_len": 0}
    b = max(1, int(round(n ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(n / b))
    starts_pool = np.arange(0, n - b + 1) if n - b + 1 > 0 else np.array([0])
    rng = np.random.default_rng(seed)
    est = np.empty(n_boot, dtype=np.float64)
    for it in range(n_boot):
        starts = rng.choice(starts_pool, size=n_blocks, replace=True)
        idx = np.concatenate([np.arange(s, s + b) for s in starts])[:n]
        est[it] = effect_fn(*(a[idx] for a in arrays))
    est = est[np.isfinite(est)]
    if est.shape[0] == 0:
        return {"ci_low_1s": float("nan"), "ci_hi_1s": float("nan"),
                "ci_low_2s": float("nan"), "ci_hi_2s": float("nan"), "block_len": b}
    return {"ci_low_1s": float(np.percentile(est, 16)),
            "ci_hi_1s": float(np.percentile(est, 84)),
            "ci_low_2s": float(np.percentile(est, 2.5)),
            "ci_hi_2s": float(np.percentile(est, 97.5)), "block_len": b}


# --------------------------------------------------------------------------- #
# Orchestration — per-cell ranking + verdict
# --------------------------------------------------------------------------- #
BINARY_FRAMINGS = ("TA_q05", "TA_neg", "TB_median")


def build_targets(r_e: np.ndarray) -> dict[str, np.ndarray]:
    """Three tail-target framings (binary T-A/T-B; T-C is r_e itself)."""
    q05 = float(np.quantile(r_e, 0.05, method="linear"))
    med = float(np.median(r_e))
    return {"TA_q05": (r_e < q05).astype(int), "TA_neg": (r_e < 0).astype(int),
            "TB_median": (r_e < med).astype(int)}


def rank_cell(ev: CellEvents) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compute the feature x framing separation table and the cell verdict."""
    rows: list[dict[str, Any]] = []
    if ev.n_events == 0:
        return rows, {"cell": ev.cell, "verdict": "INCONCLUSIVE_POWER", "reason": "no events",
                      "n_events": 0}
    targets = build_targets(ev.r_e)
    n_q05 = int(targets["TA_q05"].sum())

    def add(feature: str, framing: str, metric: str, effect: float, loss_sign: float,
            extra: dict[str, Any] | None = None) -> None:
        row = {"cell": ev.cell, "feature": feature, "framing": framing, "metric": metric,
               "effect": effect, "abs_effect": abs(effect) if np.isfinite(effect) else float("nan"),
               "loss_direction": loss_sign, "n_events": ev.n_events, "n_tail_q05": n_q05}
        if extra:
            row.update(extra)
        rows.append(row)

    # continuous features
    for f in CONT_FEATURES:
        x = ev.features[f]
        for fr in BINARY_FRAMINGS:
            r, auc, n1, n0 = rank_biserial(x, targets[fr])
            add(f, fr, "rank_biserial", r, np.sign(r) if np.isfinite(r) else float("nan"),
                {"auc": auc, "n_tail": n1, "n_rest": n0})
        sl = spearman_loss(x, ev.r_e)
        add(f, "TC", "spearman_loss", sl, np.sign(sl) if np.isfinite(sl) else float("nan"))
    # binary features
    for f in BIN_FEATURES:
        x = ev.features[f]
        for fr in BINARY_FRAMINGS:
            phi, dr = phi_binary(x, targets[fr])
            add(f, fr, "phi", phi, np.sign(phi) if np.isfinite(phi) else float("nan"),
                {"tail_rate_diff": dr})
        rb, _, _, _ = rank_biserial(ev.r_e * -1.0, x.astype(int))  # loss-association of feat==1
        add(f, "TC", "rank_biserial_loss", rb, np.sign(rb) if np.isfinite(rb) else float("nan"))
    # multi-level categorical (unsigned)
    for f in CAT_FEATURES:
        labels = ev.features[f]
        for fr in BINARY_FRAMINGS:
            v = cramers_v(labels, targets[fr])
            add(f, fr, "cramers_v", v, float("nan"))
        eps = kruskal_epsilon_sq(labels, ev.r_e)
        add(f, "TC", "kruskal_eps_sq", eps, float("nan"))

    verdict = adjudicate(ev, rows, n_q05)
    return rows, verdict


def adjudicate(ev: CellEvents, rows: list[dict[str, Any]], n_q05: int) -> dict[str, Any]:
    """Map the ranking table to SEPARATOR_FOUND / NO_SEPARATOR / INCONCLUSIVE_POWER."""
    if n_q05 < POWER_FLOOR:
        return {"cell": ev.cell, "verdict": "INCONCLUSIVE_POWER",
                "reason": f"q05 tail cell {n_q05} < {POWER_FLOOR}", "n_events": ev.n_events,
                "n_tail_q05": n_q05}
    # directional features only (continuous + binary); require all-framing sign consistency.
    framings = ("TA_q05", "TA_neg", "TB_median", "TC")
    candidates: list[dict[str, Any]] = []
    directional = list(CONT_FEATURES) + list(BIN_FEATURES)
    for f in directional:
        fr_rows = {r["framing"]: r for r in rows if r["feature"] == f}
        signs = [fr_rows[fr]["loss_direction"] for fr in framings if fr in fr_rows]
        effects = {fr: fr_rows[fr]["abs_effect"] for fr in framings if fr in fr_rows}
        consistent = all(np.isfinite(s) for s in signs) and len({s for s in signs}) == 1
        prim = effects.get("TA_q05", float("nan"))
        candidates.append({"feature": f, "consistent": bool(consistent),
                           "primary_abs_effect": prim,
                           "max_abs_effect": float(np.nanmax(list(effects.values()))
                                                   if effects else float("nan"))})
    found = [c for c in candidates
             if c["consistent"] and np.isfinite(c["primary_abs_effect"])
             and c["primary_abs_effect"] >= MATERIAL_BAR]
    verdict = {"cell": ev.cell, "n_events": ev.n_events, "n_tail_q05": n_q05,
               "material_bar": MATERIAL_BAR, "candidates": candidates,
               "separators": [c["feature"] for c in found]}
    verdict["verdict"] = "SEPARATOR_FOUND" if found else "NO_SEPARATOR"
    return verdict


def bootstrap_leads(ev: CellEvents, rows: list[dict[str, Any]],
                    cell_index: int) -> list[dict[str, Any]]:
    """Block-bootstrap CI for lead features + any feature reaching the material bar on TA_q05."""
    if ev.n_events < POWER_FLOOR:
        return []
    targets = build_targets(ev.r_e)
    to_boot = set(LEAD_FEATURES)
    for r in rows:
        if (r["framing"] == "TA_q05" and r["feature"] in CONT_FEATURES + BIN_FEATURES
                and np.isfinite(r["abs_effect"]) and r["abs_effect"] >= MATERIAL_BAR):
            to_boot.add(r["feature"])
    out: list[dict[str, Any]] = []
    for fi, f in enumerate(sorted(to_boot)):
        x = ev.features[f]
        if f in CONT_FEATURES:
            eff = lambda xf, tt: rank_biserial(xf, tt)[0]  # noqa: E731
        else:
            eff = lambda xf, tt: phi_binary(xf, tt)[0]      # noqa: E731
        ci = block_bootstrap_ci(eff, (x.astype(np.float64), targets["TA_q05"]),
                                 ev.n_events, [BASE_SEED, cell_index, fi, 0])
        point = (rank_biserial(x, targets["TA_q05"])[0] if f in CONT_FEATURES
                 else phi_binary(x, targets["TA_q05"])[0])
        out.append({"cell": ev.cell, "feature": f, "framing": "TA_q05", "point": point, **ci})
    return out


# --------------------------------------------------------------------------- #
# Pure computation — substrate-wide aggregation (the binding verdict object)
# --------------------------------------------------------------------------- #
DIRECTIONAL_FEATURES = tuple(CONT_FEATURES) + tuple(BIN_FEATURES)


def _ci_material_side(point: float, ci_low_1s: float, ci_hi_1s: float) -> bool:
    """True if the 1σ CI lies on the material side of MATERIAL_BAR with a consistent sign."""
    if not (np.isfinite(point) and np.isfinite(ci_low_1s) and np.isfinite(ci_hi_1s)):
        return False
    return ci_low_1s >= MATERIAL_BAR if point >= 0 else ci_hi_1s <= -MATERIAL_BAR


def _cross_cell_median_ci(effects: np.ndarray, seed_idx: int) -> dict[str, float]:
    """Bootstrap CI on the cross-cell median of a feature's signed per-cell TA_q05 effect.

    Resamples powered cells with replacement (cell-level bootstrap; cheap, no per-event draw).
    """
    e = effects[np.isfinite(effects)]
    n = int(e.shape[0])
    if n == 0:
        return {"median": float("nan"), "med_ci_low_1s": float("nan"),
                "med_ci_hi_1s": float("nan"), "n_cells_eff": 0}
    rng = np.random.default_rng([BASE_SEED, 7770, seed_idx])
    boot = np.median(e[rng.integers(0, n, size=(N_BOOT, n))], axis=1)
    return {"median": float(np.median(e)), "med_ci_low_1s": float(np.percentile(boot, 16)),
            "med_ci_hi_1s": float(np.percentile(boot, 84)), "n_cells_eff": n}


_FRAMINGS = ("TA_q05", "TA_neg", "TB_median", "TC")


def _is_cell_candidate(rows_lookup: dict, boot_lookup: dict, cell: str, f: str) -> bool:
    """Cell-level candidate separator gate: cross-framing consistency ∧ point≥bar ∧ 1σ CI material."""
    fr = rows_lookup.get((cell, f), {})
    ta = fr.get("TA_q05")
    if ta is None:
        return False
    signs = [fr[k]["loss_direction"] for k in _FRAMINGS if k in fr]
    consistent = (all(np.isfinite(s) for s in signs)
                  and len({s for s in signs}) == 1 and len(signs) == len(_FRAMINGS))
    point_ok = np.isfinite(ta["abs_effect"]) and ta["abs_effect"] >= MATERIAL_BAR
    b = boot_lookup.get((cell, f))
    ci_ok = b is not None and _ci_material_side(b["point"], b["ci_low_1s"], b["ci_hi_1s"])
    return bool(consistent and point_ok and ci_ok)


def _feature_breadth(cells: list[str], f: str, fi: int, rows_lookup: dict,
                     boot_lookup: dict) -> dict[str, Any]:
    """Per-feature single-lever breadth over a cell set: candidate share + signed-effect median CI."""
    cand = [c for c in cells if _is_cell_candidate(rows_lookup, boot_lookup, c, f)]
    signed = [float(rows_lookup[(c, f)]["TA_q05"]["effect"]) for c in cells
              if (c, f) in rows_lookup and "TA_q05" in rows_lookup[(c, f)]
              and np.isfinite(rows_lookup[(c, f)]["TA_q05"]["effect"])]
    med = _cross_cell_median_ci(np.asarray(signed, dtype=np.float64), fi)
    share = len(cand) / len(cells) if cells else float("nan")
    is_lever = (np.isfinite(share) and share >= SUBSTRATE_SHARE_MIN
                and _ci_material_side(med["median"], med["med_ci_low_1s"], med["med_ci_hi_1s"]))
    return {"feature": f, "n_cells": len(cells), "n_candidate_cells": len(cand),
            "share": share, "median_effect": med["median"], "med_ci_low_1s": med["med_ci_low_1s"],
            "med_ci_hi_1s": med["med_ci_hi_1s"], "n_cells_eff": med["n_cells_eff"],
            "is_uniform_lever": bool(is_lever), "candidate_cells": cand}


def _powered_cells(verdicts: dict[str, Any]) -> list[str]:
    return [c for c, v in verdicts.items()
            if v.get("verdict") != "INCONCLUSIVE_POWER" and int(v.get("n_tail_q05", 0)) >= POWER_FLOOR]


def domain_aggregate(all_rows: list[dict[str, Any]], all_boot: list[dict[str, Any]],
                     verdicts: dict[str, Any]) -> dict[str, Any]:
    """Per-domain dual-metric verdict (the binding object — pooling masks domain structure).

    Each domain reports BOTH (a) the per-cell **any-feature separability rate** (fraction of the
    domain's powered cells with a per-cell SEPARATOR_FOUND) and (b) the per-feature **single-lever
    breadth** (candidate share + within-domain median CI per feature). Four-tier verdict:
      INCONCLUSIVE_POWER  — < MIN_POWERED_PER_DOMAIN powered cells in the domain;
      SEPARATOR_FOUND     — ≥1 feature is a uniform lever (breadth ≥ SUBSTRATE_SHARE_MIN ∧ median CI);
      SEPARABLE_NO_UNIFORM_LEVER — any-feature rate ≥ DOMAIN_SEPARABLE_RATE but no uniform lever
                            (tail separable, but via heterogeneous cell-specific features);
      NO_SEPARATOR        — neither.
    """
    boot_lookup = {(r["cell"], r["feature"]): r for r in all_boot}
    rows_lookup: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for r in all_rows:
        rows_lookup.setdefault((r["cell"], r["feature"]), {})[r["framing"]] = r
    powered = set(_powered_cells(verdicts))

    out: dict[str, Any] = {}
    for dom in exp068.DOMAINS:
        dom_cells = sorted(c for c in powered if c.rsplit("-", 1)[1] == dom)
        all_dom = [c for c in verdicts if c.rsplit("-", 1)[1] == dom]
        if len(dom_cells) < MIN_POWERED_PER_DOMAIN:
            out[dom] = {"verdict": "INCONCLUSIVE_POWER", "n_cells": len(all_dom),
                        "n_powered": len(dom_cells), "min_powered": MIN_POWERED_PER_DOMAIN,
                        "sep_rate": float("nan"), "uniform_levers": [], "per_feature": []}
            continue
        n_sep = sum(verdicts[c].get("verdict") == "SEPARATOR_FOUND" for c in dom_cells)
        sep_rate = n_sep / len(dom_cells)
        per_feature = [_feature_breadth(dom_cells, f, fi, rows_lookup, boot_lookup)
                       for fi, f in enumerate(DIRECTIONAL_FEATURES)]
        levers = [d["feature"] for d in per_feature if d["is_uniform_lever"]]
        if levers:
            verdict = "SEPARATOR_FOUND"
        elif sep_rate >= DOMAIN_SEPARABLE_RATE:
            verdict = "SEPARABLE_NO_UNIFORM_LEVER"
        else:
            verdict = "NO_SEPARATOR"
        out[dom] = {"verdict": verdict, "n_cells": len(all_dom), "n_powered": len(dom_cells),
                    "sep_rate": sep_rate, "n_cells_sep": n_sep, "uniform_levers": levers,
                    "domain_separable_rate": DOMAIN_SEPARABLE_RATE,
                    "share_min": SUBSTRATE_SHARE_MIN, "per_feature": per_feature}
    return out


def substrate_aggregate(all_rows: list[dict[str, Any]], all_boot: list[dict[str, Any]],
                        verdicts: dict[str, Any]) -> dict[str, Any]:
    """Pooled substrate aggregation — DISCLOSED ONLY (pools across domains; not binding).

    Retained as a secondary line; the binding read is ``domain_aggregate`` because pooling 5m
    noise + underpowered 2h/4h against the 15m–1h sweet spot masks domain structure.
    """
    boot_lookup = {(r["cell"], r["feature"]): r for r in all_boot}
    rows_lookup: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for r in all_rows:
        rows_lookup.setdefault((r["cell"], r["feature"]), {})[r["framing"]] = r
    powered = _powered_cells(verdicts)
    per_feature = [_feature_breadth(powered, f, fi, rows_lookup, boot_lookup)
                   for fi, f in enumerate(DIRECTIONAL_FEATURES)]
    separators = [d["feature"] for d in per_feature if d["is_uniform_lever"]]
    if len(powered) < MIN_POWERED_CELLS:
        verdict = "INCONCLUSIVE_POWER"
    else:
        verdict = "SEPARATOR_FOUND" if separators else "NO_SEPARATOR"
    return {"verdict": verdict, "disclosed_only": True, "n_powered_cells": len(powered),
            "min_powered_cells": MIN_POWERED_CELLS, "substrate_share_min": SUBSTRATE_SHARE_MIN,
            "material_bar": MATERIAL_BAR, "separators": separators,
            "lead_features": list(LEAD_FEATURES), "per_feature": per_feature,
            "powered_cells": powered}


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded; reuse the computed tables — no data reload)
# --------------------------------------------------------------------------- #
def _save(fig: plt.Figure, name: str) -> None:
    fig.savefig(PLOTS_DIR / name, dpi=110, bbox_inches="tight")
    plt.close(fig)


def plot_cross_cell(rank_df: pl.DataFrame, substrate: dict[str, Any]) -> None:
    """Plot 1: cross-cell distribution of each lead feature's TA_q05 effect over powered cells."""
    powered = set(substrate.get("powered_cells", []))
    leads = list(LEAD_FEATURES)
    data, labels = [], []
    for f in leads:
        sub = rank_df.filter((pl.col("feature") == f) & (pl.col("framing") == "TA_q05")
                             & pl.col("cell").is_in(list(powered)))
        eff = [e for e in sub.get_column("effect").to_list() if e is not None and np.isfinite(e)]
        if eff:
            data.append(eff)
            labels.append(f)
    if not data:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(data, showfliers=True, tick_labels=labels, vert=True)
    ax.axhline(MATERIAL_BAR, color="#d73027", ls="--", lw=1)
    ax.axhline(-MATERIAL_BAR, color="#d73027", ls="--", lw=1)
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_ylabel("TA_q05 effect per cell")
    ax.set_title(f"Lead-feature separation across {len(powered)} powered cells")
    plt.xticks(rotation=20, ha="right")
    _save(fig, "01_cross_cell_leads.png")


def plot_domain_breadth(domain_agg: dict[str, Any]) -> None:
    """Plot 2: per-domain single-lever breadth heatmap (feature × domain) + verdict / sep-rate band."""
    doms = [d for d in exp068.DOMAINS if domain_agg.get(d, {}).get("per_feature")]
    feats = list(DIRECTIONAL_FEATURES)
    mat = np.full((len(feats), len(doms)), np.nan)
    for j, dom in enumerate(doms):
        share = {d["feature"]: d["share"] for d in domain_agg[dom]["per_feature"]}
        for i, f in enumerate(feats):
            mat[i, j] = share.get(f, np.nan)
    fig, ax = plt.subplots(figsize=(max(4, 1.2 * len(doms)), max(3, 0.4 * len(feats))))
    im = ax.imshow(mat, cmap="YlGnBu", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(doms)),
                  [f"{d}\n{domain_agg[d]['verdict'].split('_')[0]}\n"
                   f"rate={domain_agg[d]['sep_rate']:.0%}" for d in doms], fontsize=8)
    ax.set_yticks(range(len(feats)), feats, fontsize=8)
    ax.set_title(f"Single-lever breadth by feature × domain "
                 f"(share floor {SUBSTRATE_SHARE_MIN:.0%})")
    fig.colorbar(im, ax=ax, shrink=0.7, label="candidate-cell share")
    _save(fig, "02_domain_breadth.png")


def plot_h1(events: dict[str, CellEvents]) -> None:
    """Plot 3: H1 — r_e by m_sofar/atr quintile (GBPUSD-5m continuity cell)."""
    ev = events.get(CONTINUITY_CELL)
    if ev is None or ev.n_events == 0:
        return
    x, r = _clean_pair(ev.features["msofar_atr"], ev.r_e)
    if x.shape[0] < 10:
        return
    q = np.quantile(x, np.linspace(0, 1, 6))
    bins = np.clip(np.digitize(x, q[1:-1]), 0, 4)
    data = [r[bins == b] for b in range(5)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(data, showfliers=False, tick_labels=[f"Q{b+1}" for b in range(5)])
    ax.axhline(0, color="#d73027", lw=1)
    ax.set_xlabel("m_sofar/ATR quintile (low→high)")
    ax.set_ylabel("r_e (ATR units)")
    ax.set_title(f"H1: {CONTINUITY_CELL} return by exhaustion-magnitude quintile")
    _save(fig, "03_h1_msofar_atr.png")


def plot_h2(events: dict[str, CellEvents]) -> None:
    """Plot 4: H2 — tail-rate by harami-polarity agreement (GBPUSD-5m continuity cell)."""
    ev = events.get(CONTINUITY_CELL)
    if ev is None or ev.n_events == 0:
        return
    targets = build_targets(ev.r_e)
    agree = ev.features["polarity_agree_ha0"]
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["disagree", "agree"]
    for j, fr in enumerate(("TA_q05", "TA_neg")):
        rates = [float(targets[fr][agree == g].mean()) if (agree == g).any() else np.nan
                 for g in (0, 1)]
        ax.bar(np.arange(2) + j * 0.35, rates, width=0.33, label=fr)
    ax.set_xticks(np.arange(2) + 0.18, labels)
    ax.set_ylabel("tail rate")
    ax.set_title(f"H2: {CONTINUITY_CELL} loss-tail rate by polarity agreement")
    ax.legend()
    _save(fig, "04_h2_polarity.png")


def plot_session_magnitude(events: dict[str, CellEvents]) -> None:
    """Plot 5: tail-rate heatmap over session x m_sofar/atr tercile (GBPUSD-5m continuity cell)."""
    ev = events.get(CONTINUITY_CELL)
    if ev is None or ev.n_events == 0:
        return
    targets = build_targets(ev.r_e)["TA_q05"]
    sess = ev.features["session"]
    x = ev.features["msofar_atr"]
    ok = np.isfinite(x)
    terc = np.full(x.shape[0], -1)
    if ok.sum() >= 3:
        q = np.quantile(x[ok], [1 / 3, 2 / 3])
        terc[ok] = np.digitize(x[ok], q)
    order = ["Asia", "London", "Overlap", "NY"]
    mat = np.full((len(order), 3), np.nan)
    for i, s in enumerate(order):
        for t in range(3):
            mask = (sess == s) & (terc == t)
            if mask.any():
                mat[i, t] = float(targets[mask].mean())
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(mat, cmap="OrRd", aspect="auto")
    ax.set_xticks(range(3), ["mag-low", "mag-mid", "mag-high"])
    ax.set_yticks(range(len(order)), order)
    ax.set_title(f"{CONTINUITY_CELL} q05 tail-rate: session x magnitude")
    fig.colorbar(im, ax=ax, shrink=0.7)
    _save(fig, "05_session_magnitude.png")


def plot_continuity_ranking(rank_df: pl.DataFrame) -> None:
    """Plot 6: GBPUSD-5m continuity-cell feature-separation ranking (TA_q05) + material line."""
    sub = rank_df.filter((pl.col("cell") == CONTINUITY_CELL) & (pl.col("framing") == "TA_q05"))
    sub = sub.sort("abs_effect", descending=False, nulls_last=False)
    if sub.height == 0:
        return
    feats = sub.get_column("feature").to_list()
    eff = sub.get_column("effect").to_list()
    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(feats))))
    ax.barh(feats, eff, color="#762a83")
    ax.axvline(MATERIAL_BAR, color="#d73027", ls="--", lw=1)
    ax.axvline(-MATERIAL_BAR, color="#d73027", ls="--", lw=1)
    ax.set_xlabel("signed effect (rank-biserial / phi / V), TA_q05")
    ax.set_title(f"{CONTINUITY_CELL} (continuity cell) loss-tail separation (TA_q05)")
    _save(fig, "06_continuity_ranking.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Resolve all cells, rank features, bootstrap leads, write outputs, return summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    events: dict[str, CellEvents] = {}
    all_rows: list[dict[str, Any]] = []
    all_boot: list[dict[str, Any]] = []
    verdicts: dict[str, Any] = {}
    coverage_rows: list[dict[str, Any]] = []

    for ci, (inst, dom, is4) in enumerate(tqdm(CELLS, desc="cells")):
        ev = resolve_cell_events(inst, dom, is4, ci)
        events[ev.cell] = ev
        if ev.n_events > 0:
            pl.DataFrame({"r_e": ev.r_e,
                          **{k: v for k, v in ev.features.items() if v.dtype != object},
                          **{k: v.astype(str) for k, v in ev.features.items()
                             if v.dtype == object}}
                         ).write_parquet(RESULTS_DIR / f"events_{ev.cell}.parquet")
        coverage_rows.append({"cell": ev.cell, "n_events": ev.n_events,
                              "censored": ev.censored, **ev.coverage})
        rows, verdict = rank_cell(ev)
        all_rows.extend(rows)
        verdicts[ev.cell] = verdict
        all_boot.extend(bootstrap_leads(ev, rows, ci))
        tqdm.write(f"{ev.cell}: n={ev.n_events} censored={ev.censored} "
                   f"verdict={verdict['verdict']}")

    rank_df = pl.DataFrame(all_rows) if all_rows else pl.DataFrame()
    boot_df = pl.DataFrame(all_boot) if all_boot else pl.DataFrame()
    if rank_df.height:
        rank_df.write_csv(RESULTS_DIR / "feature_separation.csv")
    if boot_df.height:
        boot_df.write_csv(RESULTS_DIR / "bootstrap_ci.csv")
    pl.DataFrame(coverage_rows).write_csv(RESULTS_DIR / "coverage.csv")
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(verdicts, indent=2, default=str))

    # ---- Per-domain aggregation (BINDING) + pooled substrate (disclosed-only) ----
    domain_agg = domain_aggregate(all_rows, all_boot, verdicts)
    substrate = substrate_aggregate(all_rows, all_boot, verdicts)
    (RESULTS_DIR / "domain_verdict.json").write_text(json.dumps(domain_agg, indent=2, default=str))
    (RESULTS_DIR / "substrate_verdict.json").write_text(
        json.dumps(substrate, indent=2, default=str))
    if rank_df.height:
        share_rows = [{"domain": dom, **{k: v for k, v in d.items() if k != "candidate_cells"}}
                      for dom, da in domain_agg.items() for d in da.get("per_feature", [])]
        if share_rows:
            pl.DataFrame(share_rows).write_csv(RESULTS_DIR / "domain_feature_share.csv")
        pl.DataFrame([{k: v for k, v in d.items() if k != "candidate_cells"}
                      for d in substrate["per_feature"]]
                     ).write_csv(RESULTS_DIR / "substrate_feature_share.csv")

    domain_verdicts = {d: a["verdict"] for d, a in domain_agg.items()}
    metadata = {
        "experiment_id": EXPERIMENT_ID, "hypothesis": "HYP-027", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN only [0, train_cutoff); TEST not re-read; holdout sealed",
        "binding_object": "per-domain (5m/15m/30m/1h/2h/4h), dual-metric",
        "continuity_cell": CONTINUITY_CELL, "material_bar": MATERIAL_BAR,
        "substrate_share_min": SUBSTRATE_SHARE_MIN, "domain_separable_rate": DOMAIN_SEPARABLE_RATE,
        "min_powered_per_domain": MIN_POWERED_PER_DOMAIN,
        "n_boot": N_BOOT, "base_seed": BASE_SEED, "atr_pctile_window": ATR_PCTILE_WINDOW,
        "n_cells": len(CELLS), "domain_verdicts": domain_verdicts,
        "domain_sep_rate": {d: a.get("sep_rate") for d, a in domain_agg.items()},
        "domain_uniform_levers": {d: a.get("uniform_levers", []) for d, a in domain_agg.items()},
        "pooled_substrate_verdict_disclosed": substrate["verdict"],
        "pooled_n_powered_cells": substrate["n_powered_cells"],
        "continuity_verdict": verdicts.get(CONTINUITY_CELL, {}).get("verdict"),
        "fence": "load_train_1m slices [0, train_cutoff) only; forward scans clip at TRAIN edge",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # plots (reuse computed tables; substrate/domain first, then continuity-cell diagnostics)
    if rank_df.height:
        plot_cross_cell(rank_df, substrate)
        plot_domain_breadth(domain_agg)
        plot_continuity_ranking(rank_df)
    plot_h1(events)
    plot_h2(events)
    plot_session_magnitude(events)
    return metadata


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOGGER.info("EXP-074: TRAIN-only substrate-wide loser-tail characterization "
                "(CF-HA-HARAMI-001/HYP-027, 99 cells)")
    summary = run()
    print("\n=== EXP-074 complete ===")
    print("per-domain verdict (binding):")
    for dom in exp068.DOMAINS:
        if dom in summary["domain_verdicts"]:
            rate = summary["domain_sep_rate"].get(dom)
            rate_s = f"{rate:.0%}" if isinstance(rate, float) and rate == rate else "n/a"
            print(f"  {dom:4} {summary['domain_verdicts'][dom]:26} sep_rate={rate_s} "
                  f"levers={summary['domain_uniform_levers'].get(dom, [])}")
    print(f"pooled substrate (disclosed-only): {summary['pooled_substrate_verdict_disclosed']} "
          f"(powered {summary['pooled_n_powered_cells']}/{summary['n_cells']})")
    print(f"continuity {CONTINUITY_CELL} verdict: {summary['continuity_verdict']}")
    print(f"artifacts -> {RESULTS_DIR}")


if __name__ == "__main__":
    main()
