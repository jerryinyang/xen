"""EXP-089 — CF-MR-001 Mean-Reversion Entry Availability Screen (Phase 020, AMENDED).

TRAIN-only, gross, 0 candidate slots, 0 counted TEST reads, holdout never touched.
An RSI-2 mean-reversion (fade) entry availability screen with a strategy-agnostic ATR
volatility-regime partition. The endpoint is the entry-signed favourable excursion
(``MFE_med`` in ATR units) measured over a **causal MR-tempo cap** (D0-amendment-001:
the cell's own RSI-2 reversion tempo, not a trend-length window). The binding
admit/exonerate is **G-020**, not this experiment — EXP-089 emits the realized gate
statistics (provisional disposition captioned NON-BINDING pending G-020).

D0-amendment-001 vs the voided first run: (1) the trend-length MA-segment adaptive cap
→ a causal MR-tempo cap (``xen.mean_reversion.reversion_episodes`` / ``mr_tempo_caps``);
(2) the three ``/VOLREGIME`` sub-screens use a **regime-matched** random control (same
rule, same regime → entry-ATR cancels) — leg-2 / beats-CORE / regime-membership null
**retired**; (3) all 6 sub-screens are single-test leg-1 through
``xen.availability_gate.run_sub_screen`` + ``combine_axis`` (joint max, no Holm).

Read region: TRAIN sub-split ``[0, int(int(total_rows*0.7)*0.7))``; the analysis-TEST
stratum and the final-30% global holdout are never sliced.

Run:
    cd python && python experiments/EXP-089/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

from xen.availability_gate import (      # noqa: E402
    STAT_MEDIAN,
    CellReadInput,
    SubScreenResult,
    combine_axis,
    run_sub_screen,
)
from xen.capgeo_geometry import lifetime_path_geometry   # noqa: E402
from xen.capgeo_substrates import ATR_PERIOD, _real_ohlc, random_entries   # noqa: E402
from xen.domain_bars import build_domain_bars   # noqa: E402
from xen.mean_reversion import (         # noqa: E402
    CORE,
    CORE_FILTER,
    CORE_TREND,
    MR_CAP_FLOOR,
    MR_CAP_MAX,
    MR_EPISODE_WINDOW,
    MR_K_MULT,
    MR_MIN_EPISODES,
    RSI_MID,
    VARIANT_SUB_SCREENS,
    mean_reversion_entries,
    mr_tempo_caps,
    reversion_episodes,
)
from xen.vol_regime import (             # noqa: E402
    REGIME_INDICES,
    REGIME_SUB_SCREENS,
    regime_labels,
    regime_matched_entries,
)
from xen.zigzag import wilder_atr        # noqa: E402

LOGGER = logging.getLogger("EXP-089")

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 / EXP-080 reuse
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-089"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_VAL005_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-005" / "code" / "run_experiment.py"
_EXP080_READY_MAP = PROJECT_ROOT / "python/experiments/EXP-080/results/ready_map.csv"
_BITE_REPORT = (PROJECT_ROOT / "docs/experiments-docs/checkpoints"
                / "2026-06-23-020-mean-reversion-entry-availability"
                / "bite-check" / "bite_check_report.json")


def _load_val005():
    """Import the VAL-005 module (import-safe: constants/functions only, main guarded)."""
    spec = importlib.util.spec_from_file_location("val005_capgeo", _VAL005_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load VAL-005 from {_VAL005_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Constants (frozen at G0 / D0 / D0-amendment-001; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_MASTER = 20260623             # Phase 020 master seed (D1)
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
SUB_SCREEN_ORDER = [CORE, *REGIME_SUB_SCREENS, CORE_TREND, CORE_FILTER]   # D2b/scope SUB order
SUBSCREEN_ID = {name: i for i, name in enumerate(SUB_SCREEN_ORDER)}
REGIME_BY_SUB = {REGIME_SUB_SCREENS[g]: g for g in REGIME_INDICES}
EVENT_FLOOR = 15                   # D7 coverage floor (no upper bound for this dense family)
POOL_RAW_MULT = 8                  # leg-1 random pool raw draw = mult x conditioned raw entries
POOL_RAW_MIN = 3000
POOL_RAW_CAP = 30000
D2A_NULL_BAND = (17, 29)           # Phase-020 D2a coin-flip band Binom(46,0.5) (reporting only)
COVERAGE_EXCLUDED = {("US500", "4h"), ("JP225", "4h")}
N_PERM = 5000                      # production permutations
N_PERM_STABILITY = 1000            # MC-stability cross-check scale

# Seed-stream tags (distinct sub-streams off the master seed; determinism-stable).
_CTRL_TAG, _POOL_TAG, _POOLDIR_TAG, _GATE_TAG = 11, 12, 13, 21


def _rng(*key: int) -> np.random.Generator:
    """Deterministic generator off the master seed for a given integer key."""
    return np.random.default_rng([SEED_MASTER, *key])


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class CellBuild:
    """Per-cell gate-ready inputs (one CellReadInput per sub-screen) + disclosures."""

    cell_id: str
    instrument: str
    domain: str
    cri: dict                      # sub-screen name -> CellReadInput
    cap_stats: dict                # sub-screen name -> cap-distribution disclosure
    n_raw: dict                    # sub-screen name -> raw signal entry count
    recon_ok: bool                 # count/direction/regime-membership match across all sub-screens


# --------------------------------------------------------------------------- #
# Pure computation — signed favourable excursion over the MR-tempo cap (real OHLC)
# --------------------------------------------------------------------------- #
def _event_mfe(ohlc: dict, atr: np.ndarray, episodes: tuple, entry_idx: np.ndarray,
               direction: np.ndarray, n_bars: int
               ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Entry-signed favourable ``MFE`` (ATR units) over each event's causal MR-tempo cap.

    Caps come from the cell's RSI-2 reversion tempo (``mr_tempo_caps``); warmup events
    are excluded. ``lifetime_path_geometry`` with the entry ``direction`` returns the
    favourable excursion in the entry-signed direction. Returns ``(mfe, surviving idx,
    surviving direction, raw cap, raw warmup mask)`` — the raw cap/warmup are over the
    input ``entry_idx`` (for the cap disclosure).
    """
    close_idx, durations = episodes
    cap, warmup = mr_tempo_caps(entry_idx, close_idx, durations)
    empty = np.empty(0, np.float64), np.empty(0, np.int64), np.empty(0, np.int64)
    if entry_idx.shape[0] == 0 or not np.any(~warmup):
        return (*empty, cap, warmup)
    keep = ~warmup
    gidx = entry_idx[keep].astype(np.int64)
    gdir = direction[keep].astype(np.int64)
    geo = lifetime_path_geometry(ohlc["high"], ohlc["low"], ohlc["close"], atr[gidx], gidx,
                                 gdir, cap[keep], n_bars)
    u = geo.usable
    return geo.mfe[u], gidx[u].astype(np.int64), gdir[u].astype(np.int64), cap, warmup


def _cap_stats(cap: np.ndarray, warmup: np.ndarray) -> dict:
    """Per-set cap-distribution disclosure (median/mean cap, warmup/floor/cap-max share)."""
    n = int(cap.shape[0])
    n_warm = int(np.count_nonzero(warmup))
    eff = cap[~warmup]
    if eff.shape[0] == 0:
        return {"n_raw": n, "pct_warmup": (n_warm / n if n else 0.0),
                "cap_median": float("nan"), "cap_mean": float("nan"),
                "pct_floor": 0.0, "pct_capmax": 0.0}
    return {"n_raw": n, "pct_warmup": (n_warm / n if n else 0.0),
            "cap_median": float(np.median(eff)), "cap_mean": float(np.mean(eff)),
            "pct_floor": float(np.mean(eff == MR_CAP_FLOOR)),
            "pct_capmax": float(np.mean(eff == MR_CAP_MAX))}


def _matched_control_mfe(ohlc: dict, atr: np.ndarray, episodes: tuple, n_bars: int,
                         ctrl_idx: np.ndarray, dirs_raw: np.ndarray,
                         rng: np.random.Generator) -> np.ndarray:
    """Usable signed-favourable MFE of a count+direction-matched control on given bars.

    ``ctrl_idx`` are the (already drawn) random control bar indices; the signal's
    direction multiset is shuffled and assigned (matched direction, randomized
    direction-time pairing). Same MR-tempo cap rule as the signal (horizon parity).
    """
    if dirs_raw.shape[0] == 0 or ctrl_idx.shape[0] == 0:
        return np.empty(0, np.float64)
    d = dirs_raw.copy()
    rng.shuffle(d)
    mfe, _, _, _, _ = _event_mfe(ohlc, atr, episodes, ctrl_idx, d[:ctrl_idx.shape[0]], n_bars)
    return mfe


def _pool_mfe(ohlc: dict, atr: np.ndarray, episodes: tuple, n_bars: int, pool_idx: np.ndarray,
              p_long: float, rng_dir: np.random.Generator) -> np.ndarray:
    """Usable signed-fav MFE of the permutation random pool (direction-proportioned)."""
    if pool_idx.shape[0] == 0:
        return np.empty(0, np.float64)
    d = np.where(rng_dir.random(pool_idx.shape[0]) < p_long, 1, -1).astype(np.int64)
    mfe, _, _, _, _ = _event_mfe(ohlc, atr, episodes, pool_idx, d, n_bars)
    return mfe


def _pool_target(n_sig: int, n_avail: int) -> int:
    """Random-pool raw draw size, bounded by the available candidate-bar count."""
    return int(min(n_avail, max(POOL_RAW_MIN, POOL_RAW_MULT * max(n_sig, 1)), POOL_RAW_CAP))


# --------------------------------------------------------------------------- #
# Orchestration — per-cell build (geometry + matched controls + regime partition)
# --------------------------------------------------------------------------- #
def _build_variant(ohlc, atr, episodes, bars, n_bars, inst, domain, cell_id, es, ci) -> dict:
    """All-bars CellReadInput + cap stats for one variant sub-screen (CORE / TREND / FILTER)."""
    ss = es.sub_screen
    n_raw = int(es.entry_idx.shape[0])
    n_long = int(np.count_nonzero(es.direction == 1))
    p_long = n_long / max(n_raw, 1)
    sid = SUBSCREEN_ID[ss]
    cond_mfe, _, _, cap_raw, warm_raw = _event_mfe(ohlc, atr, episodes, es.entry_idx,
                                                   es.direction, n_bars)
    ctrl_idx = random_entries(bars, instrument=inst, domain=domain, n_target=n_raw,
                              rng=_rng(_CTRL_TAG, ci, sid, n_raw)).entry_idx
    ctrl_mfe = _matched_control_mfe(ohlc, atr, episodes, n_bars, ctrl_idx, es.direction,
                                    _rng(_CTRL_TAG, ci, sid, n_raw + 1))
    pool_idx = random_entries(bars, instrument=inst, domain=domain,
                              n_target=_pool_target(n_raw, n_bars),
                              rng=_rng(_POOL_TAG, ci, sid, n_raw)).entry_idx
    pool_mfe = _pool_mfe(ohlc, atr, episodes, n_bars, pool_idx, p_long,
                         _rng(_POOLDIR_TAG, ci, sid, n_raw))
    n_cond = int(cond_mfe.shape[0])
    cri = CellReadInput(cell_id=cell_id, cond_values=cond_mfe, ctrl_values=ctrl_mfe,
                        pool_values=pool_mfe, n_cond=n_cond, underpowered=bool(n_cond < EVENT_FLOOR))
    return {"cri": cri, "cap_stats": _cap_stats(cap_raw, warm_raw), "n_raw": n_raw,
            "recon_ok": bool(ctrl_idx.shape[0] == min(n_raw, n_bars))}


def _build_regime(ohlc, atr, episodes, n_bars, inst, domain, cell_id, core_es, reg_bar,
                  ci) -> dict:
    """Regime-matched CellReadInputs + cap stats for the three /VOLREGIME sub-screens."""
    core_mfe, surv_idx, surv_dir, _, _ = _event_mfe(ohlc, atr, episodes, core_es.entry_idx,
                                                    core_es.direction, n_bars)
    surv_reg = reg_bar[surv_idx]
    raw_reg = reg_bar[core_es.entry_idx]
    out = {}
    recon_ok = True
    for g in REGIME_INDICES:
        ss = REGIME_SUB_SCREENS[g]
        sid = SUBSCREEN_ID[ss]
        cond_mfe = core_mfe[surv_reg == g]
        dirs_raw_g = core_es.direction[raw_reg == g]
        n_raw_g = int(dirs_raw_g.shape[0])
        n_long_g = int(np.count_nonzero(dirs_raw_g == 1))
        p_long = n_long_g / max(n_raw_g, 1)
        n_cand = int(np.count_nonzero(reg_bar == g))
        ctrl_idx = regime_matched_entries(reg_bar, g, n_raw_g, _rng(_CTRL_TAG, ci, sid, n_raw_g))
        ctrl_mfe = _matched_control_mfe(ohlc, atr, episodes, n_bars, ctrl_idx, dirs_raw_g,
                                        _rng(_CTRL_TAG, ci, sid, n_raw_g + 1))
        pool_idx = regime_matched_entries(reg_bar, g, _pool_target(n_raw_g, n_cand),
                                          _rng(_POOL_TAG, ci, sid, n_raw_g))
        pool_mfe = _pool_mfe(ohlc, atr, episodes, n_bars, pool_idx, p_long,
                             _rng(_POOLDIR_TAG, ci, sid, n_raw_g))
        # regime-membership integrity: every drawn control / pool bar carries regime g
        match_ok = (bool(np.all(reg_bar[ctrl_idx] == g)) and bool(np.all(reg_bar[pool_idx] == g))
                    and ctrl_idx.shape[0] == min(n_raw_g, n_cand))
        recon_ok = recon_ok and match_ok
        # cap stats over the regime-g raw CORE entries
        reg_entry_idx = core_es.entry_idx[raw_reg == g]
        cap_g, warm_g = mr_tempo_caps(reg_entry_idx, episodes[0], episodes[1])
        n_cond = int(cond_mfe.shape[0])
        out[ss] = {
            "cri": CellReadInput(cell_id=cell_id, cond_values=cond_mfe, ctrl_values=ctrl_mfe,
                                 pool_values=pool_mfe, n_cond=n_cond,
                                 underpowered=bool(n_cond < EVENT_FLOOR)),
            "cap_stats": _cap_stats(cap_g, warm_g), "n_raw": n_raw_g, "recon_ok": match_ok}
    out["_recon_ok"] = recon_ok
    return out


def build_all_cells(loaded: dict, full_grid: list, members: set) -> dict:
    """Per-cell gate-ready inputs for every member cell (the geometry pass; RNG-seeded draws)."""
    out: dict[str, CellBuild] = {}
    for ci, (inst, period) in enumerate(tqdm(full_grid, desc="build cells")):
        domain = DOMAIN_LABEL[period]
        if (inst, domain) not in members:
            continue
        li = loaded[inst]
        train_cutoff = int(int(li.frame.height) * 0.7)
        train_frame = li.frame.slice(0, train_cutoff)
        if not train_frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"{inst}-{domain}: TRAIN frame not CloseTime-sorted")
        bars = build_domain_bars(train_frame, period)
        n_bars = int(bars.height)
        cell_id = f"{inst}-{domain}"
        ohlc = _real_ohlc(bars)
        atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
        reg_bar = regime_labels(ohlc["high"], ohlc["low"], ohlc["close"])
        entries = mean_reversion_entries(ohlc["close"], instrument=inst, domain=domain,
                                         n_bars=n_bars)
        # Causal RSI-2 reversion tempo (shared cell clock for the MR-tempo cap).
        episodes = reversion_episodes(_rsi2_series(ohlc["close"]))
        cri, cap_stats, n_raw = {}, {}, {}
        recon = True
        for ss in VARIANT_SUB_SCREENS:
            b = _build_variant(ohlc, atr, episodes, bars, n_bars, inst, domain, cell_id,
                               entries[ss], ci)
            cri[ss], cap_stats[ss], n_raw[ss] = b["cri"], b["cap_stats"], b["n_raw"]
            recon = recon and b["recon_ok"]
        rb = _build_regime(ohlc, atr, episodes, n_bars, inst, domain, cell_id, entries[CORE],
                           reg_bar, ci)
        for ss in REGIME_SUB_SCREENS:
            cri[ss], cap_stats[ss], n_raw[ss] = rb[ss]["cri"], rb[ss]["cap_stats"], rb[ss]["n_raw"]
        recon = recon and rb["_recon_ok"]
        out[cell_id] = CellBuild(cell_id=cell_id, instrument=inst, domain=domain, cri=cri,
                                 cap_stats=cap_stats, n_raw=n_raw, recon_ok=recon)
    return out


def _rsi2_series(close: np.ndarray) -> np.ndarray:
    """Causal Wilder RSI(2) on real domain close (for the reversion-episode tempo)."""
    from xen.mean_reversion import RSI_FAST_PERIOD, wilder_rsi
    return wilder_rsi(close, RSI_FAST_PERIOD)


def _truncate_sub(s: SubScreenResult) -> SubScreenResult:
    """Sub-screen with the permutation stream truncated to the MC-stability scale."""
    return SubScreenResult(primitive=s.primitive, read=s.read, stat_kind=s.stat_kind,
                           s_realized=s.s_realized, s_star=s.s_star, perm_p=s.perm_p,
                           n_powered_cells=s.n_powered_cells, cells=s.cells,
                           s_perm=s.s_perm[:N_PERM_STABILITY])


def run_gate(builds: dict, members_order: list) -> tuple[list, object]:
    """Run all 6 single-test sub-screens through run_sub_screen and the joint-max combine."""
    ordered = []
    for ss in SUB_SCREEN_ORDER:
        cells = [builds[cid].cri[ss] for cid in members_order]
        ordered.append(run_sub_screen(ss, "mfe_med", STAT_MEDIAN, cells,
                                      _rng(_GATE_TAG, SUBSCREEN_ID[ss]), n_perm=N_PERM))
    subs_stability = [_truncate_sub(s) for s in ordered]
    axis = combine_axis("CF-MR-001", ordered, D2A_NULL_BAND, n_perm=N_PERM,
                        subs_stability=subs_stability)
    return ordered, axis


def _z_rank(s: SubScreenResult) -> float:
    """Sub-screen-level permutation z-score ``(S − mean(S_perm)) / sd(S_perm)`` (D5 ranking)."""
    sd = float(np.std(s.s_perm, ddof=1))
    return (s.s_realized - float(np.mean(s.s_perm))) / sd if sd > 0 else float("nan")


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries only — no reloads)
# --------------------------------------------------------------------------- #
def _delta_matrix(sub: SubScreenResult, instruments: list) -> np.ndarray:
    """(instrument × domain) matrix of per-cell ``delta_hat`` from a sub-screen's results."""
    lut = {c.cell_id: c for c in sub.cells}
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            c = lut.get(f"{inst}-{dom}")
            if c is not None:
                mat[i, j] = c.delta_hat
    return mat


def _box_beats(ax, sub: SubScreenResult, instruments: list) -> None:
    """Ring the cells whose leg-1 beats-random passes."""
    lut = {c.cell_id: c for c in sub.cells}
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            c = lut.get(f"{inst}-{dom}")
            if c is not None and c.beats_random:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                           edgecolor="black", lw=1.5))


def plot_delta_map(subs: list, instruments: list, path: Path) -> None:
    """Per-cell Δ̂_rand heatmap across the 6 sub-screens (beats-random cells ringed)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(2, 3, figsize=(13, 11), sharey=True)
    for ax, sub in zip(axes.ravel(), subs):
        mat = _delta_matrix(sub, instruments)
        vmax = np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1.0
        im = ax.imshow(mat, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
        _box_beats(ax, sub, instruments)
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=6)
        ax.set_title(f"{sub.primitive} (S={sub.s_realized}, S*={sub.s_star})", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("EXP-089 Δ-over-random (signed MFE_med, MR-tempo cap) — boxed = beats-random "
                 "(regimes: regime-matched control)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_regime_split(subs_by_name: dict, instruments: list, path: Path) -> None:
    """Leg-1 Δ̂_rand of the three regime sub-screens vs the regime-matched control (boxed = beats)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 3, figsize=(13, 7), sharey=True)
    for ax, name in zip(axes, REGIME_SUB_SCREENS):
        sub = subs_by_name[name]
        mat = _delta_matrix(sub, instruments)
        vmax = np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1.0
        im = ax.imshow(mat, aspect="auto", cmap="PuOr", vmin=-vmax, vmax=vmax)
        _box_beats(ax, sub, instruments)
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=6)
        ax.set_title(f"{name} (S={sub.s_realized})", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("EXP-089 regime split — Δ̂_rand vs regime-matched control (boxed = beats-random)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_s_vs_sstar(subs: list, axis, path: Path) -> None:
    """Per-sub-screen realized S with each sub-screen S* and the joint S* (argmax highlighted)."""
    sns.set_theme(style="whitegrid")
    names = [s.primitive for s in subs]
    s_vals = [s.s_realized for s in subs]
    s_star_single = [s.s_star for s in subs]
    drive = axis.driving_sub.split("/")[0]
    colors = ["crimson" if n == drive else "steelblue" for n in names]
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(names))
    ax.bar(x, s_vals, color=colors, alpha=0.85, label="S realized")
    ax.scatter(x, s_star_single, marker="_", s=400, color="black", label="S* (single sub-screen)")
    ax.axhline(axis.s_star, ls="--", color="darkorange", lw=1.5, label=f"joint S*={axis.s_star}")
    ax.set_xticks(x, names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("S = #cells beats-random (powered)")
    ax.set_title(f"EXP-089 per-sub-screen S vs S* — S_fam={axis.s_m}, perm_p={axis.perm_p:.4f}",
                 fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_perm_null(axis, path: Path) -> None:
    """Joint permuted-axis null S_perm_max with realized S_fam and the FWER-band thresholds."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(axis.s_perm_max, bins=range(int(axis.s_perm_max.max()) + 2),
            color="steelblue", edgecolor="white", align="left")
    ax.axvline(axis.s_m, color="crimson", lw=2, label=f"S_fam={axis.s_m}")
    for fw, d in axis.fwer_band.items():
        ax.axvline(d["s_star"], ls="--", lw=1, label=f"S* (FWER {fw})={d['s_star']}")
    ax.set_title(f"EXP-089 joint permuted-axis null — perm_p={axis.perm_p:.4f}, "
                 f"{axis.disposition.split(' ')[0]}", fontsize=11)
    ax.set_xlabel("S_perm_max (joint max across 6 sub-screens)")
    ax.set_ylabel("permutations")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Determinism + fingerprints
# --------------------------------------------------------------------------- #
def _cells_fingerprint(builds: dict) -> str:
    """Order-independent hash of per (cell, sub-screen) usable counts + summed metric values."""
    recs = []
    for cid, b in builds.items():
        rec = {"cell": cid}
        for ss, cri in b.cri.items():
            n = int(cri.n_cond)
            rec[f"{ss}_n"] = n
            rec[f"{ss}_sum"] = round(float(np.sum(cri.cond_values)), 8) if n else 0.0
        recs.append(rec)
    recs.sort(key=lambda d: d["cell"])
    return hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest()


def _gate_fingerprint(subs: list) -> str:
    """Hash of per-sub-screen permutation S arrays + realized S (perm-stream determinism)."""
    recs = [{"sub": s.primitive, "s": s.s_realized, "perm": s.s_perm.tolist()} for s in subs]
    return hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "MISSING"


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def _cell_rows(builds: dict, subs: list) -> list[dict]:
    """Per (cell, sub-screen) availability rows (leg-1 only; cap-distribution disclosure)."""
    rows = []
    for sub in subs:
        for c in sub.cells:
            b = builds[c.cell_id]
            cs = b.cap_stats[sub.primitive]
            rows.append({
                "cell_id": c.cell_id, "instrument": b.instrument, "domain": b.domain,
                "sub_screen": sub.primitive, "n_cond": c.n_cond, "n_raw": b.n_raw[sub.primitive],
                "underpowered": c.underpowered, "theta_signal": c.theta_cond,
                "theta_random": c.theta_ctrl, "delta_rand": c.delta_hat, "s_rand": c.s_cell,
                "ci_low_rand": c.ci_low, "beats_random": c.beats_random,
                "cap_median": cs["cap_median"], "cap_mean": cs["cap_mean"],
                "pct_warmup": cs["pct_warmup"], "pct_cap_floor": cs["pct_floor"],
                "pct_cap_max": cs["pct_capmax"],
            })
    return rows


def _family_json(subs: list, axis) -> dict:
    """Family admission JSON: per-sub-screen S/S*/perm-p/z; family stats; FWER band; disposition."""
    token = axis.disposition.split(" ")[0]
    z_by_sub = {s.primitive: _z_rank(s) for s in subs}
    argmax_lever = max((s for s in subs if s.s_realized == axis.s_m),
                       key=lambda s: (z_by_sub[s.primitive] if np.isfinite(z_by_sub[s.primitive])
                                      else -np.inf)).primitive
    return {
        "family": "CF-MR-001",
        "provisional_disposition": f"{token} (NON-BINDING — pending G-020; "
                                   "no cross-axis Holm, single family)",
        "binding_note": "NON-BINDING: the binding admit/exonerate is G-020 (D5 mechanical rule). "
                        "EXP-089 (amended) emits the realized statistics. ADMITTED iff S_fam>S* "
                        "AND axis_perm_p<=0.05 (FWER 0.05).",
        "S_fam": axis.s_m, "S_star": axis.s_star, "axis_perm_p": axis.perm_p,
        "ranking_z": axis.rank_z, "driving_sub_screen": axis.driving_sub,
        "argmax_lever_by_z": argmax_lever,
        "fwer_sensitivity_band": {str(k): v for k, v in axis.fwer_band.items()},
        "mc_stability_1000_vs_5000": axis.mc_stability,
        "d2a_coinflip_band": list(D2A_NULL_BAND),
        "sub_screens": [
            {"sub_screen": s.primitive, "S": s.s_realized, "S_star_single": s.s_star,
             "perm_p_single": s.perm_p, "z_rank": z_by_sub[s.primitive],
             "n_powered_cells": s.n_powered_cells,
             "in_d2a_coinflip_band": bool(D2A_NULL_BAND[0] <= s.s_realized <= D2A_NULL_BAND[1])}
            for s in subs],
    }


def _write_per_event(subs_by_name: dict, builds: dict, path: Path) -> None:
    """Bounded per-event regime signed-MFE (signal + regime-matched control) for reproducibility."""
    frames = []
    for g, name in zip(REGIME_INDICES, REGIME_SUB_SCREENS):
        for cid, b in builds.items():
            cri = b.cri[name]
            if cri.cond_values.shape[0]:
                frames.append(pl.DataFrame({"cell_id": [cid] * cri.cond_values.shape[0],
                                            "regime": name, "kind": "signal",
                                            "signed_mfe": cri.cond_values}))
            if cri.ctrl_values.shape[0]:
                frames.append(pl.DataFrame({"cell_id": [cid] * cri.ctrl_values.shape[0],
                                            "regime": name, "kind": "control",
                                            "signed_mfe": cri.ctrl_values}))
    out = (pl.concat(frames) if frames else
           pl.DataFrame(schema={"cell_id": pl.Utf8, "regime": pl.Utf8, "kind": pl.Utf8,
                                "signed_mfe": pl.Float64}))
    out.write_parquet(path)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-089 (AMENDED) — CF-MR-001 mean-reversion entry availability screen (Phase 020)")

    val005 = _load_val005()
    found, missing = val005.discover_infr003_files()
    rm = pl.read_csv(_EXP080_READY_MAP)
    ready = (rm.filter(pl.col("readiness_status") == "READY")
             .select(["instrument", "domain"]).unique())
    ready_set = {(r["instrument"], r["domain"]) for r in ready.iter_rows(named=True)}
    members = ready_set - COVERAGE_EXCLUDED
    LOGGER.info("EXP-080 member set: %d instrument x domain cells", len(members))

    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    loaded: dict[str, object] = {}
    for inst in instruments:
        li, _seal, status = val005.load_first70(found[inst])
        if li is None:
            missing[inst] = f"load failed: {status}"
            continue
        loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    if not instruments:
        raise RuntimeError("no instruments loaded; cannot screen")
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    members_order = [f"{inst}-{DOMAIN_LABEL[p]}" for inst, p in full_grid
                     if (inst, DOMAIN_LABEL[p]) in members]

    # Pass 1 — geometry + gate.
    builds = build_all_cells(loaded, full_grid, members)
    subs, axis = run_gate(builds, members_order)

    # Determinism — re-build the RNG-seeded sets + re-run the gate stream; compare.
    builds2 = build_all_cells(loaded, full_grid, members)
    subs2, _axis2 = run_gate(builds2, members_order)
    det_cells = _cells_fingerprint(builds) == _cells_fingerprint(builds2)
    det_gate = _gate_fingerprint(subs) == _gate_fingerprint(subs2)
    recon_all = all(b.recon_ok for b in builds.values())
    determinism_ok = bool(det_cells and det_gate)
    verdict = "SCREEN_DELIVERED" if (determinism_ok and recon_all) else "HALT"

    # Outputs.
    subs_by_name = {s.primitive: s for s in subs}
    df = pl.DataFrame(_cell_rows(builds, subs))
    df.write_parquet(RESULTS_DIR / "cell_availability.parquet")
    df.write_csv(RESULTS_DIR / "cell_availability.csv")
    (RESULTS_DIR / "family_admission.json").write_text(json.dumps(_family_json(subs, axis), indent=2))
    _write_per_event(subs_by_name, builds, RESULTS_DIR / "per_event_geometry.parquet")

    meta = {
        "experiment": EXPERIMENT_ID, "phase": "020", "family": "CF-MR-001",
        "hypothesis": "CF-MR-001/HYP-001", "amendment": "D0-amendment-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict, "provisional_disposition_NON_BINDING": axis.disposition,
        "n_member_cells": len(members), "n_cells_built": len(builds),
        "determinism_ok": determinism_ok, "determinism_cells": bool(det_cells),
        "determinism_gate_stream": bool(det_gate), "recon_all_ok": recon_all,
        "regime_match_recon_ok": recon_all,
        "read_region": "TRAIN sub-split [0, int(int(total_rows*0.7)*0.7)); analysis-TEST + holdout "
                       "never sliced",
        "seeds": {"SEED_MASTER": SEED_MASTER, "CTRL_TAG": _CTRL_TAG, "POOL_TAG": _POOL_TAG,
                  "POOLDIR_TAG": _POOLDIR_TAG, "GATE_TAG": _GATE_TAG},
        "frozen_constants": {
            "ATR_PERIOD": ATR_PERIOD, "RSI": "2 (10/90), filter 5 (50-cross), EMA 20",
            "regime": "ATR(14) causal rolling-50 percentile, cuts 33/66 LOW/MED/HIGH",
            "mr_tempo_cap": {"K_MULT": MR_K_MULT, "EPISODE_WINDOW": MR_EPISODE_WINDOW,
                             "MIN_EPISODES": MR_MIN_EPISODES, "CAP_FLOOR": MR_CAP_FLOOR,
                             "CAP_MAX": MR_CAP_MAX, "episode_close_rsi": RSI_MID},
            "EVENT_FLOOR": EVENT_FLOOR, "N_PERM": N_PERM, "N_PERM_STABILITY": N_PERM_STABILITY,
            "FWER": 0.05, "Z_ONE_SIDED": 1.645, "pool_raw": [POOL_RAW_MULT, POOL_RAW_MIN,
                                                             POOL_RAW_CAP],
            "sub_screen_order": SUB_SCREEN_ORDER, "cross_axis_holm": "NONE (single family)",
            "cap_basis": "causal RSI-2 reversion-episode tempo (D0-amendment-001; replaces "
                         "MA-segment trend cap)",
            "control": "regime-matched (same-regime bars) for /VOLREGIME; all-bars for "
                       "CORE/variants; leg-2 retired",
            "endpoint": "entry-signed favourable MFE_med (ATR units); leg-1 vs matched control "
                        "(single-test all 6 sub-screens)",
        },
        "bite_report_sha256": _hash_file(_BITE_REPORT),
        "bite_expected_single_test_sha256":
            "f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65",
        "module_hashes": {
            "availability_gate": _hash_file(PROJECT_ROOT / "python/src/xen/availability_gate.py"),
            "mean_reversion": _hash_file(PROJECT_ROOT / "python/src/xen/mean_reversion.py"),
            "vol_regime": _hash_file(PROJECT_ROOT / "python/src/xen/vol_regime.py"),
            "capgeo_geometry": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_geometry.py"),
        },
        "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # Plots (bounded; from collected summaries only).
    plot_delta_map(subs, instruments, PLOTS_DIR / "01_delta_signed_mfe_map.png")
    plot_regime_split(subs_by_name, instruments, PLOTS_DIR / "02_regime_split_delta_rand.png")
    plot_s_vs_sstar(subs, axis, PLOTS_DIR / "03_s_vs_sstar.png")
    plot_perm_null(axis, PLOTS_DIR / "04_joint_permuted_axis_null.png")

    LOGGER.info("verdict=%s disposition=%s S_fam=%d S*=%d perm_p=%.4f det=%s recon=%s",
                verdict, axis.disposition.split(" ")[0], axis.s_m, axis.s_star, axis.perm_p,
                determinism_ok, recon_all)
    LOGGER.info("results -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
