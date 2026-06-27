"""EXP-086 — Screen M: single-series magnitude / non-directional availability (Phase 019).

Family-selection availability screen (CF-VOLEXP-001/HYP-001). TRAIN-only, gross, 0 candidate slots,
0 counted TEST reads, holdout never touched. An EXP-081 clone with the information axis swapped to two
single-series **compression primitives** (raw HA harami inside-bar; real-OHLC NR7) and the endpoint
swapped to the SPLIT magnitude reads, adjudicated by the D2b multiplicity-adjusted permuted-axis
admission gate. The binding admit/exonerate is **G-019**, not this experiment — EXP-086 emits the
realized gate statistics (provisional disposition captioned NON-BINDING).

Per member cell (46 EXP-080-READY instrument×domain), per primitive, over each event's per-event
adaptive time cap on real domain OHLC:

- **Typical-range read** (direction-agnostic): ``range_sym = max(MFE, MAE)``, median Δ-over-random.
- **Tail read** (regime-signed): ``tailmass`` of the signed realized outcome, Δ-over-random;
  ``q05``/dip companions; ``msofar_atr`` rank-biserial (descriptive, NON-BINDING).

The two reads are kept strictly separate (no pooled |move|). The D2b gate (``xen.availability_gate``)
runs 4 sub-screens {2 primitives}×{2 reads}, controls within-axis multiplicity by the max statistic,
and gives the axis ``S_M``/``S*``/perm-p. A two-sided magnitude-budget (``xen.capgeo_cost``, frozen
EXP-085 table) qualifies any magnitude admission.

Read region: the TRAIN sub-split ``[0, train_cutoff)`` of the analysis set
(``train_cutoff = int(int(total_rows*0.7)*0.7)``); the nested analysis-TEST stratum and the final-30%
global holdout are never sliced.

Run:
    cd python && python experiments/EXP-086/code/run_experiment.py
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
from scipy import stats                  # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

from xen.availability_gate import (      # noqa: E402
    EVENT_FLOOR_DEFAULT,
    FWER,
    N_PERM,
    N_PERM_STABILITY,
    STAT_MEDIAN,
    STAT_TAILMASS,
    CellReadInput,
    SubScreenResult,
    combine_axis,
    run_sub_screen,
)
from xen.capgeo_cost import COST_CONSTANTS                       # noqa: E402
from xen.capgeo_geometry import lifetime_path_geometry, tail_stats   # noqa: E402
from xen.capgeo_substrates import (      # noqa: E402
    ATR_PERIOD,
    _ma_segment_moves,
    _real_ohlc,
    random_entries,
)
from xen.compression_primitives import (  # noqa: E402
    COND_HARAMI,
    COND_NR7,
    harami_raw_entries,
    nr7_entries,
)
from xen.domain_bars import build_domain_bars   # noqa: E402
from xen.expectancy import adaptive_time_caps_by_epoch, live_in_progress_state   # noqa: E402
from xen.zigzag import wilder_atr        # noqa: E402

LOGGER = logging.getLogger("EXP-086")

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 / EXP-080 reuse
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-086"
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
# Constants (frozen at G0 / D0-amendment-001; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_MASTER = 20260622             # Phase 019 master seed (D1)
SEED_CONTROL = 20260622            # matched-random control draw stream
SEED_POOL = 20260623               # permutation random-pool draw stream
SEED_GATE = 20260624               # gate (cell-SE + permutation) stream
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
PRIMITIVES = [COND_HARAMI, COND_NR7]
READS = [("typical-range", STAT_MEDIAN), ("tail", STAT_TAILMASS)]
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
    """Per (cell, primitive) per-event metric arrays for the conditioned / control / pool sets."""

    cell_id: str
    instrument: str
    domain: str
    primitive: str
    n_entries: int             # raw conditioned entries on TRAIN (pre-usability)
    n_cond: int                # usable conditioned events (the gate denominator)
    n_ctrl: int
    n_pool: int
    underpowered: bool
    recon_ok: bool             # control raw draw n_target == conditioned raw entries
    cond_range: np.ndarray
    cond_outcome: np.ndarray
    ctrl_range: np.ndarray
    ctrl_outcome: np.ndarray
    pool_range: np.ndarray
    pool_outcome: np.ndarray
    # budget + descriptive inputs (conditioned set)
    px_per_atr_med: float
    holding_bars_med: float
    rb_msofar: float           # msofar_atr rank-biserial vs the q05 tail (within-cond; NON-BINDING)
    dip_p: float
    mad_zero: bool


# --------------------------------------------------------------------------- #
# Pure computation — per-event geometry assembly (real prices; EXP-081 mapping)
# --------------------------------------------------------------------------- #
def _event_metrics(ohlc: dict, seg: dict, atr: np.ndarray, entry_idx: np.ndarray,
                   n_bars: int) -> dict:
    """Per-usable-event (range_sym, signed_outcome, msofar_atr, p_entry, atr_entry, cap) on real OHLC.

    Direction-agnostic range from a ``d=+1`` path-geometry call (MFE=up-excursion, MAE=down-excursion);
    the signed outcome multiplies the raw close-to-close by the regime MA-segment direction ``rd``
    (EXP-081 mapping). Keeps only non-warmup, regime-directed (``rd != 0``), ATR-defined, non-clipped
    events.
    """
    m = int(entry_idx.shape[0])
    empty = {k: np.empty(0, dtype=np.float64) for k in
             ("range_sym", "signed_outcome", "msofar_atr", "p_entry", "atr_entry")}
    empty["cap"] = np.empty(0, dtype=np.int64)
    if m == 0 or seg["confirm_epoch"].shape[0] == 0:
        return empty
    entry_epoch = ohlc["epoch"][entry_idx]
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    rd = state.rd.astype(np.int64).copy()
    rd[~state.valid] = 0
    cap, warmup = adaptive_time_caps_by_epoch(entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    keep = (~warmup) & (rd != 0)
    if not np.any(keep):
        return empty
    geom_idx = entry_idx[keep]
    geom_rd = rd[keep]
    geom_cap = cap[keep]
    geom_atr = atr[geom_idx]
    geom_msofar = state.m_sofar[keep]
    geo = lifetime_path_geometry(ohlc["high"], ohlc["low"], ohlc["close"], geom_atr, geom_idx,
                                 np.ones(geom_idx.shape[0], dtype=np.int64), geom_cap, n_bars)
    u = geo.usable
    return {
        "range_sym": np.maximum(geo.mfe[u], geo.mae[u]),
        "signed_outcome": geom_rd[u] * geo.outcome[u],
        "msofar_atr": geom_msofar[u] / geom_atr[u],
        "p_entry": ohlc["close"][geom_idx[u]],
        "atr_entry": geom_atr[u],
        "cap": geom_cap[u],
    }


def _rank_biserial_tail(msofar: np.ndarray, outcome: np.ndarray) -> float:
    """Rank-biserial of msofar_atr vs the q05-tail indicator (within-cond; NON-BINDING, EXP-074)."""
    n = int(outcome.shape[0])
    if n < 4:
        return float("nan")
    thr = float(np.quantile(outcome, 0.05, method="linear"))
    in_tail = outcome < thr
    n1, n0 = int(np.count_nonzero(in_tail)), int(np.count_nonzero(~in_tail))
    if n1 == 0 or n0 == 0:
        return float("nan")
    try:
        u, _ = stats.mannwhitneyu(msofar[in_tail], msofar[~in_tail], alternative="two-sided")
    except ValueError:                                           # pragma: no cover - degenerate
        return float("nan")
    return float(2.0 * u / (n1 * n0) - 1.0)


def _build_cell_primitive(ohlc: dict, seg: dict, atr: np.ndarray, bars_height: int,
                          es, instrument: str, domain: str, primitive: str, cell_index: int
                          ) -> CellPrimitiveMetrics:
    """All conditioned/control/pool metric arrays + budget/descriptive inputs for one (cell, primitive)."""
    cell_id = f"{instrument}-{domain}"
    n_entries = int(es.entry_idx.shape[0])
    cond = _event_metrics(ohlc, seg, atr, es.entry_idx, bars_height)
    n_cond = int(cond["range_sym"].shape[0])

    p_idx = PRIMITIVES.index(primitive)
    bars_pl = _BARS_CACHE[cell_id]                               # reuse the built domain frame
    rng_ctrl = np.random.default_rng([SEED_CONTROL, cell_index, p_idx, n_entries])
    ctrl_es = random_entries(bars_pl, instrument=instrument, domain=domain,
                             n_target=n_entries, rng=rng_ctrl)
    ctrl = _event_metrics(ohlc, seg, atr, ctrl_es.entry_idx, bars_height)

    pool_target = int(min(bars_height, max(POOL_RAW_MIN, POOL_RAW_MULT * max(n_entries, 1)),
                          POOL_RAW_CAP))
    rng_pool = np.random.default_rng([SEED_POOL, cell_index, p_idx, pool_target])
    pool_es = random_entries(bars_pl, instrument=instrument, domain=domain,
                             n_target=pool_target, rng=rng_pool)
    pool = _event_metrics(ohlc, seg, atr, pool_es.entry_idx, bars_height)

    px_per_atr = cond["p_entry"] / cond["atr_entry"] if n_cond else np.empty(0)
    ts = tail_stats(cond["signed_outcome"])
    return CellPrimitiveMetrics(
        cell_id=cell_id, instrument=instrument, domain=domain, primitive=primitive,
        n_entries=n_entries, n_cond=n_cond, n_ctrl=int(ctrl["range_sym"].shape[0]),
        n_pool=int(pool["range_sym"].shape[0]),
        underpowered=bool(n_cond < EVENT_FLOOR),
        recon_ok=bool(int(ctrl_es.detail.get("n_target", -1)) == n_entries),
        cond_range=cond["range_sym"], cond_outcome=cond["signed_outcome"],
        ctrl_range=ctrl["range_sym"], ctrl_outcome=ctrl["signed_outcome"],
        pool_range=pool["range_sym"], pool_outcome=pool["signed_outcome"],
        px_per_atr_med=float(np.median(px_per_atr)) if n_cond else float("nan"),
        holding_bars_med=float(np.median(cond["cap"])) if n_cond else float("nan"),
        rb_msofar=_rank_biserial_tail(cond["msofar_atr"], cond["signed_outcome"]),
        dip_p=_dip_p(cond["signed_outcome"]), mad_zero=bool(ts.mad_zero))


def _dip_p(x: np.ndarray) -> float:
    """Hartigan dip-test p-value of a sample (NON-BINDING tail-bimodality companion)."""
    import diptest
    if x.shape[0] < 4:
        return float("nan")
    return float(diptest.diptest(np.asarray(x, dtype=np.float64))[1])


# --------------------------------------------------------------------------- #
# Pure computation — magnitude-budget two-sided cost (frozen EXP-085 table)
# --------------------------------------------------------------------------- #
def _magnitude_budget(cpm: CellPrimitiveMetrics, read: str) -> dict:
    """Per-cell two-sided magnitude budget: net = harvestable_range − (2·txn + financing) ATR.

    Cost constants exist only for the 4 EXP-085 Phase-018 instruments; other instruments report
    ``COST_UNAVAILABLE`` (a full 16-instrument cost table is a future-family concern — never tuned
    here). Harvestable range = ``R_med`` (typical-range) or ``|q05|`` (tail; long-vol harvest).
    """
    if cpm.instrument not in COST_CONSTANTS or cpm.n_cond == 0:
        return {"cost_available": False, "harvestable_atr": float("nan"),
                "cost2_atr": float("nan"), "net_atr": float("nan")}
    rt_bps, fin_bps_day = COST_CONSTANTS[cpm.instrument]
    domain_minutes = {v: k for k, v in DOMAIN_LABEL.items()}[cpm.domain]
    holding_days = cpm.holding_bars_med * float(domain_minutes) / 1440.0
    cost_txn = (rt_bps / 1e4) * cpm.px_per_atr_med
    cost_fin = (fin_bps_day / 1e4) * holding_days * cpm.px_per_atr_med
    cost2 = 2.0 * cost_txn + cost_fin
    if read == "typical-range":
        harvest = float(np.median(cpm.cond_range))
    else:
        harvest = abs(float(np.quantile(cpm.cond_outcome, 0.05, method="linear")))
    return {"cost_available": True, "harvestable_atr": harvest,
            "cost2_atr": float(cost2), "net_atr": float(harvest - cost2)}


# --------------------------------------------------------------------------- #
# Orchestration — member set, per-cell build, gate
# --------------------------------------------------------------------------- #
_BARS_CACHE: dict[str, pl.DataFrame] = {}


def _member_set() -> set:
    """READY instrument×domain cells from EXP-080 ready_map (member set; exclude COVERAGE)."""
    rm = pl.read_csv(_EXP080_READY_MAP)
    ready = (rm.filter(pl.col("readiness_status") == "READY")
             .select(["instrument", "domain"]).unique())
    members = {(r["instrument"], r["domain"]) for r in ready.iter_rows(named=True)}
    return members - COVERAGE_EXCLUDED


def build_all_metrics(loaded: dict, full_grid: list, members: set) -> dict:
    """Per (cell, primitive) metric arrays for every member cell (the geometry pass; RNG-seeded draws)."""
    out: dict[tuple, CellPrimitiveMetrics] = {}
    _BARS_CACHE.clear()
    for ci, (inst, period) in enumerate(tqdm(full_grid, desc="build metrics")):
        domain = DOMAIN_LABEL[period]
        if (inst, domain) not in members:
            continue
        li = loaded[inst]
        analysis_rows = int(li.frame.height)
        train_cutoff = int(analysis_rows * 0.7)
        train_frame = li.frame.slice(0, train_cutoff)
        if not train_frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"{inst}-{domain}: TRAIN frame not CloseTime-sorted")
        bars = build_domain_bars(train_frame, period)
        cell_id = f"{inst}-{domain}"
        _BARS_CACHE[cell_id] = bars
        ohlc = _real_ohlc(bars)
        atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
        seg = _ma_segment_moves(ohlc)
        for prim in PRIMITIVES:
            es = (harami_raw_entries(bars, instrument=inst, domain=domain) if prim == COND_HARAMI
                  else nr7_entries(bars, instrument=inst, domain=domain))
            out[(cell_id, prim)] = _build_cell_primitive(
                ohlc, seg, atr, int(bars.height), es, inst, domain, prim, ci)
    return out


def run_gate(metrics: dict, members_order: list) -> tuple:
    """Run the 4 sub-screens and combine into the axis max-statistic admission result."""
    subs: list[SubScreenResult] = []
    for p_idx, prim in enumerate(PRIMITIVES):
        for r_idx, (read, stat_kind) in enumerate(READS):
            cells = []
            for cell_id in members_order:
                cpm = metrics[(cell_id, prim)]
                cond_v = cpm.cond_range if read == "typical-range" else cpm.cond_outcome
                ctrl_v = cpm.ctrl_range if read == "typical-range" else cpm.ctrl_outcome
                pool_v = cpm.pool_range if read == "typical-range" else cpm.pool_outcome
                cells.append(CellReadInput(cell_id=cell_id, cond_values=cond_v, ctrl_values=ctrl_v,
                                           pool_values=pool_v, n_cond=cpm.n_cond,
                                           underpowered=cpm.underpowered))
            rng = np.random.default_rng([SEED_GATE, p_idx, r_idx])
            subs.append(run_sub_screen(prim, read, stat_kind, cells, rng, n_perm=N_PERM))
    subs_stability = [
        SubScreenResult(primitive=s.primitive, read=s.read, stat_kind=s.stat_kind,
                        s_realized=s.s_realized, s_star=s.s_star, perm_p=s.perm_p,
                        n_powered_cells=s.n_powered_cells, cells=s.cells,
                        s_perm=s.s_perm[:N_PERM_STABILITY]) for s in subs]
    axis = combine_axis("M", subs, D2A_NULL_BAND, n_perm=N_PERM, subs_stability=subs_stability)
    return subs, axis


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries only — no reloads)
# --------------------------------------------------------------------------- #
def _delta_matrix(metrics: dict, subs: list, prim: str, read: str, instruments: list) -> np.ndarray:
    """(instrument × domain) Δ̂ matrix for one (primitive, read) from the sub-screen cell results."""
    sub = next(s for s in subs if s.primitive == prim and s.read == read)
    lut = {c.cell_id: c for c in sub.cells}
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            c = lut.get(f"{inst}-{dom}")
            if c is not None:
                mat[i, j] = c.delta_hat
    return mat


def plot_delta_heatmaps(metrics, subs, instruments, read, path):
    """Δ-over-random heatmap per primitive for one read (beats-random cells ringed)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, len(PRIMITIVES), figsize=(11, 7), sharey=True)
    for ax, prim in zip(axes, PRIMITIVES):
        mat = _delta_matrix(metrics, subs, prim, read, instruments)
        im = ax.imshow(mat, aspect="auto", cmap="coolwarm",
                       vmin=-np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else -1,
                       vmax=np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1)
        sub = next(s for s in subs if s.primitive == prim and s.read == read)
        lut = {c.cell_id: c for c in sub.cells}
        for i, inst in enumerate(instruments):
            for j, dom in enumerate(DOMAIN_ORDER):
                c = lut.get(f"{inst}-{dom}")
                if c is not None and c.beats_random:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                               edgecolor="black", lw=1.5))
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(f"{prim} (S={sub.s_realized}, S*={sub.s_star})", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(f"EXP-086 Δ-over-random — {read} read (boxed = beats random)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_perm_null(axis, path):
    """Permuted-axis null S_perm_max with realized S_M and the FWER-band thresholds overlaid."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(axis.s_perm_max, bins=range(int(axis.s_perm_max.max()) + 2),
            color="steelblue", edgecolor="white", align="left")
    ax.axvline(axis.s_m, color="crimson", lw=2, label=f"S_M={axis.s_m}")
    for fw, d in axis.fwer_band.items():
        ax.axvline(d["s_star"], ls="--", lw=1,
                   label=f"S* (FWER {fw})={d['s_star']}")
    ax.set_title(f"EXP-086 permuted-axis null (max-stat) — perm_p={axis.perm_p:.4f}, "
                 f"{axis.disposition.split(' ')[0]}", fontsize=11)
    ax.set_xlabel("S_perm_max (#cells-beat-random, joint max across sub-screens)")
    ax.set_ylabel("permutations")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_outcome_examples(metrics, subs, path):
    """Conditioned vs matched-random signed-outcome distributions for the densest cells."""
    sns.set_theme(style="whitegrid")
    dense = sorted(metrics.values(), key=lambda m: m.n_cond, reverse=True)
    picks = []
    seen = set()
    for m in dense:
        key = (m.primitive,)
        if key not in seen and m.n_cond >= EVENT_FLOOR:
            picks.append(m)
            seen.add(key)
        if len(picks) >= 4:
            break
    n = max(1, len(picks))
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), squeeze=False)
    for ax, m in zip(axes[0], picks):
        ax.hist(m.cond_outcome, bins=40, alpha=0.6, density=True, color="indianred",
                label=f"cond (n={m.n_cond})")
        ax.hist(m.ctrl_outcome, bins=40, alpha=0.5, density=True, color="steelblue",
                label=f"random (n={m.n_ctrl})")
        ax.axvline(0.0, color="grey", ls=":")
        ax.set_title(f"{m.cell_id} {m.primitive}\nrb_msofar={m.rb_msofar:.2f} dip_p={m.dip_p:.3f}",
                     fontsize=8)
        ax.set_xlabel("signed outcome (ATR)")
        ax.legend(fontsize=7)
    fig.suptitle("EXP-086 conditioned vs random signed-outcome (densest cells)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_budget(budget_rows, path):
    """Magnitude-budget harvestable-range vs two-sided cost (cells with cost constants)."""
    sns.set_theme(style="whitegrid")
    rows = [r for r in budget_rows if r["cost_available"]]
    fig, ax = plt.subplots(figsize=(8, 5))
    if rows:
        harv = np.array([r["harvestable_atr"] for r in rows])
        cost = np.array([r["cost2_atr"] for r in rows])
        net = harv - cost
        colors = np.where(net > 0, "seagreen", "indianred")
        ax.scatter(cost, harv, c=colors, s=30, alpha=0.8)
        lim = max(harv.max(), cost.max()) * 1.05
        ax.plot([0, lim], [0, lim], ls="--", color="grey", label="break-even")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
    ax.set_title("EXP-086 magnitude-budget (green = net>0; EXP-085 4-instrument cost table)",
                 fontsize=10)
    ax.set_xlabel("two-sided cost (ATR)")
    ax.set_ylabel("harvestable range (ATR)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Determinism + fingerprints
# --------------------------------------------------------------------------- #
def _metrics_fingerprint(metrics: dict) -> str:
    """Order-independent hash of the per (cell,primitive) usable counts + summed metric values."""
    recs = [
        {"cell": k[0], "prim": k[1], "n_entries": m.n_entries, "n_cond": m.n_cond,
         "n_ctrl": m.n_ctrl, "n_pool": m.n_pool,
         "range_sum": round(float(np.sum(m.cond_range)), 8) if m.n_cond else 0.0,
         "out_sum": round(float(np.sum(m.cond_outcome)), 8) if m.n_cond else 0.0}
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
    """Per (cell, primitive, read) availability rows (both reads, conditioned + control stats)."""
    rows = []
    cell_lut = {(s.primitive, s.read): {c.cell_id: c for c in s.cells} for s in subs}
    for (cell_id, prim), m in metrics.items():
        budgets = {read: _magnitude_budget(m, read) for read, _ in READS}
        for read, _stat in READS:
            cr = cell_lut[(prim, read)][cell_id]
            b = budgets[read]
            rows.append({
                "cell_id": cell_id, "instrument": m.instrument, "domain": m.domain,
                "primitive": prim, "read": read, "n_entries": m.n_entries, "n_cond": m.n_cond,
                "n_ctrl": m.n_ctrl, "n_pool": m.n_pool, "underpowered": m.underpowered,
                "recon_ok": m.recon_ok, "theta_cond": cr.theta_cond, "theta_ctrl": cr.theta_ctrl,
                "delta_hat": cr.delta_hat, "s_cell": cr.s_cell, "ci_low": cr.ci_low,
                "beats_random": cr.beats_random, "rb_msofar": m.rb_msofar, "dip_p": m.dip_p,
                "mad_zero": m.mad_zero, "cost_available": b["cost_available"],
                "harvestable_atr": b["harvestable_atr"], "cost2_atr": b["cost2_atr"],
                "net_atr": b["net_atr"]})
    return rows


def _axis_json(subs: list, axis) -> dict:
    """Axis admission JSON: per-sub-screen S/S*/perm-p, axis max-stat, FWER band, MC stability, rank."""
    return {
        "axis": axis.axis,
        "provisional_disposition": axis.disposition,
        "binding_note": "NON-BINDING: the binding admit/exonerate is G-019 (cross-axis Holm over "
                        "{M,X,(F)} axis permutation p-values). EXP-086 emits the realized statistics.",
        "S_M": axis.s_m, "S_star": axis.s_star, "axis_perm_p": axis.perm_p,
        "ranking_z": axis.rank_z, "driving_sub_screen": axis.driving_sub,
        "fwer_sensitivity_band": {str(k): v for k, v in axis.fwer_band.items()},
        "mc_stability_1000_vs_5000": axis.mc_stability,
        "d2a_null_band": list(D2A_NULL_BAND),
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
            "range_sym": m.cond_range, "signed_outcome": m.cond_outcome}))
    out = (pl.concat(frames) if frames else
           pl.DataFrame(schema={"cell_id": pl.Utf8, "primitive": pl.Utf8,
                                "range_sym": pl.Float64, "signed_outcome": pl.Float64}))
    out.write_parquet(path)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-086 — Screen M single-series magnitude availability (Phase 019)")

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
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    members_order = [f"{inst}-{DOMAIN_LABEL[p]}" for inst, p in full_grid
                     if (inst, DOMAIN_LABEL[p]) in members]

    # Pass 1 — geometry + gate.
    metrics = build_all_metrics(loaded, full_grid, members)
    subs, axis = run_gate(metrics, members_order)

    # Determinism — re-draw the RNG-seeded random sets + re-run the gate stream; compare.
    metrics2 = build_all_metrics(loaded, full_grid, members)
    subs2, _axis2 = run_gate(metrics2, members_order)
    det_metrics = _metrics_fingerprint(metrics) == _metrics_fingerprint(metrics2)
    det_gate = _gate_fingerprint(subs) == _gate_fingerprint(subs2)
    recon_all = all(m.recon_ok for m in metrics.values())
    determinism_ok = bool(det_metrics and det_gate)
    verdict = "SCREEN_DELIVERED" if (determinism_ok and recon_all) else "HALT"

    # Outputs.
    rows = _cell_rows(metrics, subs)
    df = pl.DataFrame(rows)
    df.write_parquet(RESULTS_DIR / "cell_availability.parquet")
    df.write_csv(RESULTS_DIR / "cell_availability.csv")
    (RESULTS_DIR / "axis_admission.json").write_text(json.dumps(_axis_json(subs, axis), indent=2))
    _write_per_event(metrics, RESULTS_DIR / "per_event_geometry.parquet")

    meta = {
        "experiment": EXPERIMENT_ID, "phase": "019", "axis": "M",
        "hypothesis": "CF-VOLEXP-001/HYP-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "provisional_disposition_NON_BINDING": axis.disposition,
        "n_member_cells": len(members), "n_cell_primitive": len(metrics),
        "determinism_ok": determinism_ok, "determinism_metrics": bool(det_metrics),
        "determinism_gate_stream": bool(det_gate), "recon_all_ok": recon_all,
        "read_region": "TRAIN sub-split [0, int(int(total_rows*0.7)*0.7)); analysis-TEST + holdout "
                       "never sliced",
        "seeds": {"SEED_MASTER": SEED_MASTER, "SEED_CONTROL": SEED_CONTROL,
                  "SEED_POOL": SEED_POOL, "SEED_GATE": SEED_GATE},
        "frozen_constants": {
            "ATR_PERIOD": ATR_PERIOD, "EVENT_FLOOR": EVENT_FLOOR, "N_PERM": N_PERM,
            "N_PERM_STABILITY": N_PERM_STABILITY, "FWER": FWER, "Z_ONE_SIDED": 1.645,
            "NR_LOOKBACK": 7, "K_TAIL": 3.0, "pool_raw": [POOL_RAW_MULT, POOL_RAW_MIN, POOL_RAW_CAP],
            "primitives": "COND-HARAMI (raw detect_ha_harami) + COND-NR7 (real-OHLC NR7); "
                          "D0-amendment-001",
            "cap_basis": "cell MA(20,50)-segment tempo (adaptive_time_caps_by_epoch), EXP-081",
        },
        "module_hashes": {
            "availability_gate": _hash_file(PROJECT_ROOT / "python/src/xen/availability_gate.py"),
            "compression_primitives": _hash_file(
                PROJECT_ROOT / "python/src/xen/compression_primitives.py"),
            "capgeo_geometry": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_geometry.py"),
            "capgeo_cost": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_cost.py"),
        },
        "cost_model_note": "Magnitude-budget uses the frozen EXP-085 4-instrument CONSERVATIVE table "
                           "(AUDUSD/NZDUSD/USDCAD/USTEC); other instruments report COST_UNAVAILABLE "
                           "(a 16-instrument cost table is a future-family concern, never tuned here).",
        "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # Plots (bounded; from collected summaries only).
    plot_delta_heatmaps(metrics, subs, instruments, "typical-range",
                        PLOTS_DIR / "01_delta_typical_range.png")
    plot_delta_heatmaps(metrics, subs, instruments, "tail", PLOTS_DIR / "02_delta_tail.png")
    plot_perm_null(axis, PLOTS_DIR / "03_permuted_axis_null.png")
    plot_outcome_examples(metrics, subs, PLOTS_DIR / "04_outcome_examples.png")
    plot_budget([_magnitude_budget(m, "typical-range") for m in metrics.values()],
                PLOTS_DIR / "05_magnitude_budget.png")

    LOGGER.info("verdict=%s disposition=%s S_M=%d S*=%d perm_p=%.4f det=%s recon=%s",
                verdict, axis.disposition.split(" ")[0], axis.s_m, axis.s_star, axis.perm_p,
                determinism_ok, recon_all)
    LOGGER.info("results -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
