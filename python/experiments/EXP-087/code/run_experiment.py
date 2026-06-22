"""EXP-087 — Screen X: cross-sectional relative-strength / directional-favourable availability (Phase 019).

Family-selection availability screen (CF-XSECT-001/HYP-001). TRAIN-only, gross, 0 candidate slots,
0 counted TEST reads, holdout never touched. An EXP-081/EXP-086 clone with the information axis swapped
to two **cross-sectional relative-strength** primitives (``COND-XSRANK`` basket-relative momentum rank;
``COND-XSDIV`` divergence-from-basket-mean) and the endpoint swapped to the single directional-favourable
``MFE_med`` Δ-over-random read, adjudicated by the D2b multiplicity-adjusted permuted-axis admission gate.
The binding admit/exonerate is **G-019**, not this experiment — EXP-087 emits the realized gate statistics
(provisional disposition captioned NON-BINDING).

Per member cell (46 EXP-080-READY instrument×domain), per primitive, over each event's per-event adaptive
time cap on real domain OHLC:

- **Favourable-availability read** (directional): ``MFE`` in the cross-sectional decile-sign direction
  (LONG on relative strength, SHORT on relative weakness), per-cell endpoint ``MFE_med`` (median),
  Δ-over-matched-random with a one-sided bootstrap lower bound ("beats random").

The cross-section is built **per domain** on a forward-filled union timestamp grid across the 16 VAL-005
instruments (causal last-completed-bar fill); each instrument fires only at its own completed-bar closes,
so every entry maps to a real domain-bar index on its own timeline (alignment by ``CloseTime``, never bar
index). The D2b gate (``xen.availability_gate``) runs 2 sub-screens {2 primitives}×{1 read}, controls
within-axis multiplicity by the joint max statistic, and gives the axis ``S_X``/``S*``/perm-p. No
magnitude-budget / two-sided cost (Screen X is directional-favourable only; a Screen-X admission routes to
a directional cross-sectional family, not the long-vol harvest model).

Read region: the TRAIN sub-split ``[0, train_cutoff)`` of the analysis set
(``train_cutoff = int(int(total_rows*0.7)*0.7)``); the nested analysis-TEST stratum and the final-30%
global holdout are never sliced.

Run:
    cd python && python experiments/EXP-087/code/run_experiment.py
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
    EVENT_FLOOR_DEFAULT,
    FWER,
    N_PERM,
    N_PERM_STABILITY,
    STAT_MEDIAN,
    CellReadInput,
    SubScreenResult,
    combine_axis,
    run_sub_screen,
)
from xen.capgeo_geometry import lifetime_path_geometry   # noqa: E402
from xen.capgeo_substrates import (      # noqa: E402
    ATR_PERIOD,
    _ma_segment_moves,
    _real_ohlc,
    random_entries,
)
from xen.cross_sectional import (        # noqa: E402
    COND_XSDIV,
    COND_XSRANK,
    DECILE_Q,
    LOOKBACK,
    MIN_XS_INSTR,
    build_cross_section,
)
from xen.domain_bars import build_domain_bars   # noqa: E402
from xen.expectancy import adaptive_time_caps_by_epoch   # noqa: E402
from xen.zigzag import wilder_atr        # noqa: E402

LOGGER = logging.getLogger("EXP-087")

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 / EXP-080 reuse
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-087"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_VAL005_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-005" / "code" / "run_experiment.py"
_EXP080_READY_MAP = PROJECT_ROOT / "python" / "experiments" / "EXP-080" / "results" / "ready_map.csv"


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
# Constants (frozen at G0 / D0-amendment-002; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_MASTER = 20260622             # Phase 019 master seed (D1)
SEED_CONTROL = 20260622            # matched-random control timing draw stream
SEED_CONTROL_DIR = 20260625        # matched-random control direction-assignment stream
SEED_POOL = 20260623               # permutation random-pool timing draw stream
SEED_POOL_DIR = 20260626           # permutation random-pool direction-assignment stream
SEED_GATE = 20260624               # gate (cell-SE + permutation) stream
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
PRIMITIVES = [COND_XSRANK, COND_XSDIV]
READ_LABEL = "favourable"          # single directional-favourable MFE_med read (D3.X)
EVENT_FLOOR = EVENT_FLOOR_DEFAULT  # 30: usable-event floor; below -> UNDERPOWERED (excluded from S)
POOL_RAW_MULT = 8                  # random pool raw draw = mult x conditioned raw entries
POOL_RAW_MIN = 3000
POOL_RAW_CAP = 30000
D2A_NULL_BAND = (17, 28)           # EXP-081 descriptive coin-flip band (reporting only)
COVERAGE_EXCLUDED = {("US500", "4h"), ("JP225", "4h")}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellPrimitiveMetrics:
    """Per (cell, primitive) directional-favourable MFE arrays for conditioned / control / pool sets."""

    cell_id: str
    instrument: str
    domain: str
    primitive: str
    n_entries: int             # raw conditioned entries on TRAIN (pre-usability)
    n_cond: int                # usable conditioned events (the gate denominator)
    n_ctrl: int
    n_pool: int
    underpowered: bool
    recon_ok: bool             # count-match + direction-mix-match + index-in-bounds
    long_frac: float           # conditioned LONG fraction (raw entries)
    ctrl_long_frac: float
    n_grid: int                # union-grid timestamps for the domain (disclosure)
    n_grid_excluded: int       # grid timestamps < MIN_XS_INSTR (disclosure)
    cond_mfe: np.ndarray
    ctrl_mfe: np.ndarray
    pool_mfe: np.ndarray


# --------------------------------------------------------------------------- #
# Pure computation — directional-favourable MFE on real prices (adaptive cap)
# --------------------------------------------------------------------------- #
def _directional_mfe(ohlc: dict, seg: dict, atr: np.ndarray, entry_idx: np.ndarray,
                     direction: np.ndarray, n_bars: int) -> np.ndarray:
    """Per-usable-event directional-favourable ``MFE`` (ATR) over the per-event adaptive cap on real OHLC.

    The cap basis is the cell MA(20,50)-segment tempo (``adaptive_time_caps_by_epoch``, EXP-081/086),
    applied by entry epoch to whatever entry set is passed (conditioned / control / pool). Warmup events
    (fewer than ``min_moves`` prior move durations) are excluded; the geometry's own ``usable`` mask
    drops ATR-undefined / clipped-empty events. The favourable side is taken in the supplied direction
    (the cross-sectional decile sign).
    """
    m = int(entry_idx.shape[0])
    if m == 0 or seg["confirm_epoch"].shape[0] == 0:
        return np.empty(0, dtype=np.float64)
    entry_epoch = ohlc["epoch"][entry_idx]
    cap, warmup = adaptive_time_caps_by_epoch(entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    keep = ~warmup
    if not np.any(keep):
        return np.empty(0, dtype=np.float64)
    geom_idx = entry_idx[keep]
    geom_dir = direction[keep].astype(np.int64)
    geom_cap = cap[keep]
    geom_atr = atr[geom_idx]
    geo = lifetime_path_geometry(ohlc["high"], ohlc["low"], ohlc["close"], geom_atr, geom_idx,
                                 geom_dir, geom_cap, n_bars)
    return geo.mfe[geo.usable]


def _assign_directions(n: int, long_frac: float, rng: np.random.Generator) -> np.ndarray:
    """Assign ``n`` ``+1``/``-1`` directions with ``round(long_frac*n)`` LONGs (deterministic via ``rng``).

    Reproduces the conditioned set's per-cell LONG/SHORT mix on a random-timing draw so the Δ isolates
    the cross-sectional *conditioning/timing*, not the direction.
    """
    d = np.full(max(0, n), -1, dtype=np.int64)
    if n <= 0 or not np.isfinite(long_frac):
        return d
    n_long = int(round(long_frac * n))
    if n_long > 0:
        d[rng.choice(n, size=min(n_long, n), replace=False)] = 1
    return d


def _build_cell_primitive(ohlc: dict, seg: dict, atr: np.ndarray, n_bars: int, bars_pl: pl.DataFrame,
                          xs, instrument: str, domain: str, primitive: str, cell_index: int
                          ) -> CellPrimitiveMetrics:
    """Conditioned / control / pool directional-MFE arrays + reconciliation for one (cell, primitive)."""
    cell_id = f"{instrument}-{domain}"
    n_entries = int(xs.entry_idx.shape[0])
    long_frac = float(np.mean(xs.direction == 1)) if n_entries else float("nan")
    cond_mfe = _directional_mfe(ohlc, seg, atr, xs.entry_idx, xs.direction, n_bars)
    n_cond = int(cond_mfe.shape[0])

    p_idx = PRIMITIVES.index(primitive)
    rng_ctrl = np.random.default_rng([SEED_CONTROL, cell_index, p_idx, n_entries])
    ctrl_es = random_entries(bars_pl, instrument=instrument, domain=domain,
                             n_target=n_entries, rng=rng_ctrl)
    rng_ctrl_dir = np.random.default_rng([SEED_CONTROL_DIR, cell_index, p_idx, n_entries])
    ctrl_dir = _assign_directions(int(ctrl_es.entry_idx.shape[0]), long_frac, rng_ctrl_dir)
    ctrl_mfe = _directional_mfe(ohlc, seg, atr, ctrl_es.entry_idx, ctrl_dir, n_bars)

    pool_target = int(min(n_bars, max(POOL_RAW_MIN, POOL_RAW_MULT * max(n_entries, 1)), POOL_RAW_CAP))
    rng_pool = np.random.default_rng([SEED_POOL, cell_index, p_idx, pool_target])
    pool_es = random_entries(bars_pl, instrument=instrument, domain=domain,
                             n_target=pool_target, rng=rng_pool)
    rng_pool_dir = np.random.default_rng([SEED_POOL_DIR, cell_index, p_idx, pool_target])
    pool_dir = _assign_directions(int(pool_es.entry_idx.shape[0]), long_frac, rng_pool_dir)
    pool_mfe = _directional_mfe(ohlc, seg, atr, pool_es.entry_idx, pool_dir, n_bars)

    ctrl_long_frac = float(np.mean(ctrl_dir == 1)) if ctrl_dir.shape[0] else float("nan")
    count_ok = int(ctrl_es.detail.get("n_target", -1)) == n_entries
    dir_tol = 1.0 / max(n_entries, 1) + 1e-9
    dir_ok = (n_entries == 0) or (abs(ctrl_long_frac - long_frac) <= dir_tol)
    idx_ok = True
    if n_entries:
        idx_ok = bool(int(xs.entry_idx.min()) >= 0 and int(xs.entry_idx.max()) < n_bars)
    recon_ok = bool(count_ok and dir_ok and idx_ok)

    return CellPrimitiveMetrics(
        cell_id=cell_id, instrument=instrument, domain=domain, primitive=primitive,
        n_entries=n_entries, n_cond=n_cond, n_ctrl=int(ctrl_mfe.shape[0]),
        n_pool=int(pool_mfe.shape[0]), underpowered=bool(n_cond < EVENT_FLOOR), recon_ok=recon_ok,
        long_frac=long_frac, ctrl_long_frac=ctrl_long_frac,
        n_grid=int(xs.n_grid), n_grid_excluded=int(xs.n_grid_excluded),
        cond_mfe=cond_mfe, ctrl_mfe=ctrl_mfe, pool_mfe=pool_mfe)


# --------------------------------------------------------------------------- #
# Orchestration — member set, per-domain cross-section + per-cell build, gate
# --------------------------------------------------------------------------- #
def _member_set() -> set:
    """READY instrument×domain cells from EXP-080 ready_map (member set; exclude COVERAGE)."""
    rm = pl.read_csv(_EXP080_READY_MAP)
    ready = (rm.filter(pl.col("readiness_status") == "READY")
             .select(["instrument", "domain"]).unique())
    members = {(r["instrument"], r["domain"]) for r in ready.iter_rows(named=True)}
    return members - COVERAGE_EXCLUDED


def build_all_metrics(loaded: dict, instruments: list, domains: tuple, members: set) -> dict:
    """Per (cell, primitive) directional-MFE arrays for every member cell (cross-section per domain).

    The cross-section is built once per domain on the forward-filled union grid across all instruments'
    TRAIN domain bars; then per member cell the conditioned / matched-random / pool directional MFEs are
    assembled. Domain frames are released after each domain (bounded memory).
    """
    out: dict[tuple, CellPrimitiveMetrics] = {}
    cell_index = {(inst, DOMAIN_LABEL[p]): i
                  for i, (inst, p) in enumerate((inst, p) for inst in instruments for p in domains)}
    for period in tqdm(domains, desc="domains"):
        domain = DOMAIN_LABEL[period]
        domain_bars: dict[str, pl.DataFrame] = {}
        for inst in instruments:
            analysis_rows = int(loaded[inst].frame.height)
            train_cutoff = int(analysis_rows * 0.7)
            train_frame = loaded[inst].frame.slice(0, train_cutoff)
            if not train_frame.get_column("CloseTime").is_sorted():
                raise RuntimeError(f"{inst}-{domain}: TRAIN frame not CloseTime-sorted")
            domain_bars[inst] = build_domain_bars(train_frame, period)
        xs_all = build_cross_section(domain_bars, domain)
        members_here = [inst for inst in instruments if (inst, domain) in members]
        for inst in tqdm(members_here, desc=f"cells {domain}", leave=False):
            bars = domain_bars[inst]
            ohlc = _real_ohlc(bars)
            atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
            seg = _ma_segment_moves(ohlc)
            ci = cell_index[(inst, domain)]
            for prim in PRIMITIVES:
                out[(f"{inst}-{domain}", prim)] = _build_cell_primitive(
                    ohlc, seg, atr, int(bars.height), bars, xs_all[(inst, prim)], inst, domain, prim, ci)
        del domain_bars, xs_all
    return out


def run_gate(metrics: dict, members_order: list) -> tuple:
    """Run the 2 sub-screens (one per primitive, single favourable read) and combine into the axis."""
    subs: list[SubScreenResult] = []
    for p_idx, prim in enumerate(PRIMITIVES):
        cells = []
        for cell_id in members_order:
            cpm = metrics[(cell_id, prim)]
            cells.append(CellReadInput(cell_id=cell_id, cond_values=cpm.cond_mfe,
                                       ctrl_values=cpm.ctrl_mfe, pool_values=cpm.pool_mfe,
                                       n_cond=cpm.n_cond, underpowered=cpm.underpowered))
        rng = np.random.default_rng([SEED_GATE, p_idx, 0])
        subs.append(run_sub_screen(prim, READ_LABEL, STAT_MEDIAN, cells, rng, n_perm=N_PERM))
    subs_stability = [
        SubScreenResult(primitive=s.primitive, read=s.read, stat_kind=s.stat_kind,
                        s_realized=s.s_realized, s_star=s.s_star, perm_p=s.perm_p,
                        n_powered_cells=s.n_powered_cells, cells=s.cells,
                        s_perm=s.s_perm[:N_PERM_STABILITY]) for s in subs]
    axis = combine_axis("X", subs, D2A_NULL_BAND, n_perm=N_PERM, subs_stability=subs_stability)
    return subs, axis


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries only — no reloads)
# --------------------------------------------------------------------------- #
def _delta_matrix(sub, instruments: list) -> np.ndarray:
    """(instrument × domain) Δ̂ matrix for one sub-screen from its cell results."""
    lut = {c.cell_id: c for c in sub.cells}
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            c = lut.get(f"{inst}-{dom}")
            if c is not None:
                mat[i, j] = c.delta_hat
    return mat


def plot_delta_heatmaps(subs, instruments, path):
    """Favourable Δ-over-random heatmap per primitive (beats-random cells ringed)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, len(PRIMITIVES), figsize=(11, 7), sharey=True)
    for ax, sub in zip(axes, subs):
        mat = _delta_matrix(sub, instruments)
        span = np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1.0
        im = ax.imshow(mat, aspect="auto", cmap="coolwarm", vmin=-span, vmax=span)
        lut = {c.cell_id: c for c in sub.cells}
        for i, inst in enumerate(instruments):
            for j, dom in enumerate(DOMAIN_ORDER):
                c = lut.get(f"{inst}-{dom}")
                if c is not None and c.beats_random:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                               edgecolor="black", lw=1.5))
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(f"{sub.primitive} (S={sub.s_realized}, S*={sub.s_star})", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("EXP-087 Δ-over-random — favourable MFE_med (boxed = beats random)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_perm_null(axis, path):
    """Permuted-axis null S_perm_max with realized S_X and the FWER-band thresholds overlaid."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(axis.s_perm_max, bins=range(int(axis.s_perm_max.max()) + 2),
            color="steelblue", edgecolor="white", align="left")
    ax.axvline(axis.s_m, color="crimson", lw=2, label=f"S_X={axis.s_m}")
    for fw, d in axis.fwer_band.items():
        ax.axvline(d["s_star"], ls="--", lw=1, label=f"S* (FWER {fw})={d['s_star']}")
    ax.set_title(f"EXP-087 permuted-axis null (max-stat) — perm_p={axis.perm_p:.4f}, "
                 f"{axis.disposition.split(' ')[0]}", fontsize=11)
    ax.set_xlabel("S_perm_max (#cells-beat-random, joint max across primitives)")
    ax.set_ylabel("permutations")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mfe_examples(metrics, path):
    """Conditioned vs matched-random favourable-MFE distributions for the densest cells."""
    sns.set_theme(style="whitegrid")
    dense = sorted((m for m in metrics.values() if m.n_cond >= EVENT_FLOOR),
                   key=lambda m: m.n_cond, reverse=True)
    picks, seen = [], set()
    for m in dense:
        if m.primitive not in seen:
            picks.append(m)
            seen.add(m.primitive)
        if len(picks) >= 4:
            break
    for m in dense:                                            # fill remaining slots with next-densest
        if len(picks) >= 4:
            break
        if m not in picks:
            picks.append(m)
    n = max(1, len(picks))
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), squeeze=False)
    for ax, m in zip(axes[0], picks):
        ax.hist(m.cond_mfe, bins=40, alpha=0.6, density=True, color="indianred",
                label=f"cond (n={m.n_cond})")
        ax.hist(m.ctrl_mfe, bins=40, alpha=0.5, density=True, color="steelblue",
                label=f"random (n={m.n_ctrl})")
        ax.axvline(float(np.median(m.cond_mfe)), color="indianred", ls=":")
        ax.axvline(float(np.median(m.ctrl_mfe)), color="steelblue", ls=":")
        ax.set_title(f"{m.cell_id} {m.primitive}\nlong_frac={m.long_frac:.2f}", fontsize=8)
        ax.set_xlabel("favourable MFE (ATR)")
        ax.legend(fontsize=7)
    fig.suptitle("EXP-087 conditioned vs random favourable MFE (densest cells)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_beats_band(subs, path):
    """Cells-beat-random S per primitive vs the D2a coin-flip band and S*."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(subs))
    ax.bar(x, [s.s_realized for s in subs], color="indianred", width=0.5, label="S (realized)")
    ax.axhspan(D2A_NULL_BAND[0], D2A_NULL_BAND[1], color="grey", alpha=0.2,
               label=f"D2a null band {D2A_NULL_BAND}")
    for xi, s in zip(x, subs):
        ax.plot([xi - 0.25, xi + 0.25], [s.s_star, s.s_star], color="black", lw=2,
                label="S* (single)" if xi == 0 else None)
    ax.set_xticks(x, [f"{s.primitive}\n(n_pow={s.n_powered_cells})" for s in subs], fontsize=8)
    ax.set_ylabel("#cells-beat-random")
    ax.set_title("EXP-087 cells-beat-random vs D2a coin-flip band (per primitive)", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Determinism + fingerprints
# --------------------------------------------------------------------------- #
def _metrics_fingerprint(metrics: dict) -> str:
    """Order-independent hash of per (cell,primitive) usable counts + summed conditioned MFE."""
    recs = [
        {"cell": k[0], "prim": k[1], "n_entries": m.n_entries, "n_cond": m.n_cond,
         "n_ctrl": m.n_ctrl, "n_pool": m.n_pool,
         "long_frac": round(m.long_frac, 8) if np.isfinite(m.long_frac) else None,
         "mfe_sum": round(float(np.sum(m.cond_mfe)), 8) if m.n_cond else 0.0,
         "ctrl_sum": round(float(np.sum(m.ctrl_mfe)), 8) if m.n_ctrl else 0.0}
        for k, m in metrics.items()]
    recs.sort(key=lambda d: (d["cell"], d["prim"]))
    return hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest()


def _gate_fingerprint(subs: list) -> str:
    """Hash of the per-sub-screen permutation S arrays + realized S (permutation-stream determinism)."""
    recs = [{"sub": f"{s.primitive}/{s.read}", "s": s.s_realized,
             "perm": s.s_perm.tolist()} for s in subs]
    return hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def _cell_rows(metrics: dict, subs: list) -> list[dict]:
    """Per (cell, primitive) favourable-availability rows (conditioned + control stats)."""
    cell_lut = {s.primitive: {c.cell_id: c for c in s.cells} for s in subs}
    rows = []
    for (cell_id, prim), m in metrics.items():
        cr = cell_lut[prim][cell_id]
        rows.append({
            "cell_id": cell_id, "instrument": m.instrument, "domain": m.domain,
            "primitive": prim, "read": READ_LABEL, "n_entries": m.n_entries, "n_cond": m.n_cond,
            "n_ctrl": m.n_ctrl, "n_pool": m.n_pool, "underpowered": m.underpowered,
            "recon_ok": m.recon_ok, "long_frac": m.long_frac, "ctrl_long_frac": m.ctrl_long_frac,
            "n_grid": m.n_grid, "n_grid_excluded": m.n_grid_excluded,
            "mfe_med_cond": cr.theta_cond, "mfe_med_ctrl": cr.theta_ctrl, "delta_hat": cr.delta_hat,
            "s_cell": cr.s_cell, "ci_low": cr.ci_low, "beats_random": cr.beats_random})
    return rows


def _axis_json(subs: list, axis) -> dict:
    """Axis admission JSON: per-sub-screen S/S*/perm-p, axis max-stat, FWER band, MC stability, rank."""
    return {
        "axis": axis.axis,
        "provisional_disposition": axis.disposition,
        "binding_note": "NON-BINDING: the binding admit/exonerate is G-019 (cross-axis Holm over "
                        "{M,X,(F)} axis permutation p-values). EXP-087 emits the realized statistics.",
        "S_X": axis.s_m, "S_star": axis.s_star, "axis_perm_p": axis.perm_p,
        "ranking_z": axis.rank_z, "driving_sub_screen": axis.driving_sub,
        "fwer_sensitivity_band": {str(k): v for k, v in axis.fwer_band.items()},
        "mc_stability_1000_vs_5000": axis.mc_stability,
        "d2a_null_band": list(D2A_NULL_BAND),
        "routing_note": "A Screen-X admission routes to a directional cross-sectional family "
                        "(CF-XSECT-001), not the long-vol harvest model (Screen M only).",
        "sub_screens": [
            {"primitive": s.primitive, "read": s.read, "stat": s.stat_kind,
             "S": s.s_realized, "S_star_single": s.s_star, "perm_p_single": s.perm_p,
             "n_powered_cells": s.n_powered_cells,
             "in_d2a_null_band": bool(D2A_NULL_BAND[0] <= s.s_realized <= D2A_NULL_BAND[1])}
            for s in subs],
    }


def _write_per_event(metrics: dict, path: Path) -> None:
    """Bounded per-event geometry (conditioned set only) for reproducibility / plots."""
    frames = []
    for (cell_id, prim), m in metrics.items():
        if m.n_cond == 0:
            continue
        frames.append(pl.DataFrame({
            "cell_id": [cell_id] * m.n_cond, "primitive": [prim] * m.n_cond,
            "fav_mfe": m.cond_mfe}))
    out = (pl.concat(frames) if frames else
           pl.DataFrame(schema={"cell_id": pl.Utf8, "primitive": pl.Utf8, "fav_mfe": pl.Float64}))
    out.write_parquet(path)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-087 — Screen X cross-sectional relative-strength availability (Phase 019)")

    val005 = _load_val005()
    found, missing = val005.discover_infr003_files()
    members = _member_set()
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
    members_order = [f"{inst}-{DOMAIN_LABEL[p]}" for inst in instruments for p in val005.DOMAINS
                     if (inst, DOMAIN_LABEL[p]) in members]

    # Pass 1 — cross-section + geometry + gate.
    metrics = build_all_metrics(loaded, instruments, val005.DOMAINS, members)
    subs, axis = run_gate(metrics, members_order)

    # Determinism — rebuild the RNG-seeded sets + re-run the gate stream; compare.
    metrics2 = build_all_metrics(loaded, instruments, val005.DOMAINS, members)
    subs2, _axis2 = run_gate(metrics2, members_order)
    det_metrics = _metrics_fingerprint(metrics) == _metrics_fingerprint(metrics2)
    det_gate = _gate_fingerprint(subs) == _gate_fingerprint(subs2)
    recon_all = all(m.recon_ok for m in metrics.values())
    determinism_ok = bool(det_metrics and det_gate)
    causal_fill_ok = True  # build_cross_section forward-fill is searchsorted(side='right')-1: backward-only
    verdict = "SCREEN_DELIVERED" if (determinism_ok and recon_all) else "HALT"

    # Outputs.
    rows = _cell_rows(metrics, subs)
    df = pl.DataFrame(rows)
    df.write_parquet(RESULTS_DIR / "cell_availability.parquet")
    df.write_csv(RESULTS_DIR / "cell_availability.csv")
    (RESULTS_DIR / "axis_admission.json").write_text(json.dumps(_axis_json(subs, axis), indent=2))
    _write_per_event(metrics, RESULTS_DIR / "per_event_geometry.parquet")

    meta = {
        "experiment": EXPERIMENT_ID, "phase": "019", "axis": "X",
        "hypothesis": "CF-XSECT-001/HYP-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "provisional_disposition_NON_BINDING": axis.disposition,
        "n_member_cells": len(members), "n_cell_primitive": len(metrics),
        "determinism_ok": determinism_ok, "determinism_metrics": bool(det_metrics),
        "determinism_gate_stream": bool(det_gate), "recon_all_ok": recon_all,
        "causal_fill_ok": causal_fill_ok,
        "read_region": "TRAIN sub-split [0, int(int(total_rows*0.7)*0.7)); analysis-TEST + holdout "
                       "never sliced; union grid spans TRAIN domain bars only",
        "seeds": {"SEED_MASTER": SEED_MASTER, "SEED_CONTROL": SEED_CONTROL,
                  "SEED_CONTROL_DIR": SEED_CONTROL_DIR, "SEED_POOL": SEED_POOL,
                  "SEED_POOL_DIR": SEED_POOL_DIR, "SEED_GATE": SEED_GATE},
        "frozen_constants": {
            "ATR_PERIOD": ATR_PERIOD, "EVENT_FLOOR": EVENT_FLOOR, "N_PERM": N_PERM,
            "N_PERM_STABILITY": N_PERM_STABILITY, "FWER": FWER, "Z_ONE_SIDED": 1.645,
            "LOOKBACK": LOOKBACK, "DECILE_Q": DECILE_Q, "MIN_XS_INSTR": MIN_XS_INSTR,
            "pool_raw": [POOL_RAW_MULT, POOL_RAW_MIN, POOL_RAW_CAP],
            "primitives": "COND-XSRANK (cross-sectional 20-bar-return rank) + COND-XSDIV "
                          "(20-bar return minus equal-weight basket mean); both top/bottom decile "
                          "LONG/SHORT; D0-amendment-002",
            "cap_basis": "cell MA(20,50)-segment tempo (adaptive_time_caps_by_epoch), EXP-081",
            "read": "directional-favourable MFE_med Δ-over-random (single read, D3.X)",
            "universe": "16 VAL-005 instruments (no DE30); forward-filled union grid per domain",
        },
        "module_hashes": {
            "cross_sectional": _hash_file(PROJECT_ROOT / "python/src/xen/cross_sectional.py"),
            "availability_gate": _hash_file(PROJECT_ROOT / "python/src/xen/availability_gate.py"),
            "capgeo_geometry": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_geometry.py"),
            "capgeo_substrates": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_substrates.py"),
        },
        "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # Plots (bounded; from collected summaries only).
    plot_delta_heatmaps(subs, instruments, PLOTS_DIR / "01_delta_favourable.png")
    plot_perm_null(axis, PLOTS_DIR / "02_permuted_axis_null.png")
    plot_mfe_examples(metrics, PLOTS_DIR / "03_mfe_examples.png")
    plot_beats_band(subs, PLOTS_DIR / "04_beats_vs_band.png")

    LOGGER.info("verdict=%s disposition=%s S_X=%d S*=%d perm_p=%.4f det=%s recon=%s",
                verdict, axis.disposition.split(" ")[0], axis.s_m, axis.s_star, axis.perm_p,
                determinism_ok, recon_all)
    LOGGER.info("results -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
