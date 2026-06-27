"""EXP-081 — Per-substrate realized return-structure characterization (Phase 018, CF-CAPGEO-001).

HYP-002 characterize step. TRAIN-only, gross, 0 candidate slots, 0 counted TEST reads. For each of
the 184 member substrate-cells (4 frozen substrates x 46 EXP-080-READY instrument x domain cells) this
computes the **frozen D3-input return-structure statistics** EXP-082's mechanical exit-derivation rule
consumes, plus a non-binding ``ASS`` discovery disclosure. No exit/barrier/P&L is applied; every metric
is on real prices.

Per substrate-cell, over each event's per-event **adaptive time cap** (``adaptive_time_caps_by_epoch``,
frozen TIMECAP_*) on real domain OHLC:

- D3 inputs: ``MFE_med`` (Q50), ``MFE_q40`` (Q40), ``TTP_med`` (Q50), ``TTP_q75`` (Q75),
  ``MAE_q90`` (Q90); ``m_anti`` (MAE antimode via Hartigan dip + adaptive-KDE; NaN if unimodal);
  ``tailmass`` + ``q05`` (catastrophe boundary ``median - 3*MAD``).
- ``ASS`` discovery (non-binding): expectancy + median + tail, moving-block bootstrap CIs; D6 Guard (i)
  defers expectancy to the median at effective-n <= 60 on bimodal/asymmetric strata.

Read region: the TRAIN sub-split ``[0, train_cutoff)`` of the analysis set
(``train_cutoff = int(int(total_rows*0.7)*0.7)``). The nested analysis-TEST stratum and the final-30%
global holdout are never sliced. Reuses the VAL-005 validated loader and the EXP-080 frozen substrate
harness unchanged; reconciles per-cell entry counts to EXP-080 restricted to the TRAIN slice.

Run:
    cd python && python experiments/EXP-081/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

from xen.ass import (                    # noqa: E402
    default_block_length,
    moving_block_bootstrap_cis,
    score,
    shape_diagnostic,
)
from xen.capgeo_geometry import (        # noqa: E402
    DIP_ALPHA,
    K_TAIL,
    antimode_mae,
    lifetime_path_geometry,
    tail_stats,
)
from xen.capgeo_substrates import (      # noqa: E402
    ATR_PERIOD,
    SUB_AVWAP,
    SUB_HARAMI_PARTIAL_V2A,
    SUB_HARAMI_V2A_ADVNONE,
    SUB_RANDOM,
    _ma_segment_moves,
    _real_ohlc,
    avwap_entries,
    harami_native_entries,
    random_entries,
)
from xen.domain_bars import build_domain_bars   # noqa: E402
from xen.expectancy import (             # noqa: E402
    adaptive_time_caps_by_epoch,
    live_in_progress_state,
)
from xen.zigzag import wilder_atr        # noqa: E402

LOGGER = logging.getLogger("EXP-081")

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 / EXP-080 reuse
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-081"
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
# Constants (frozen at G0; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_RANDOM = 20260621              # SUB-RANDOM matched-control master seed (D10; == EXP-080)
SEED_ASS = 20260621                # ASS moving-block bootstrap master seed (D10)
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
SUBSTRATE_ORDER = [SUB_AVWAP, SUB_HARAMI_PARTIAL_V2A, SUB_HARAMI_V2A_ADVNONE, SUB_RANDOM]
N_BOOT = 10_000                    # ASS discovery bootstrap resamples (plan Step 7)
EVENT_FLOOR = 30                   # D9: usable-event floor; below -> UNDERPOWERED_DISCLOSED
GUARD_I_N = 60                     # D6 Guard (i): defer expectancy to median at effective-n <= 60
# COVERAGE_EXCLUDED member-set exclusions (EXP-080): no derived candidate, never characterized here.
COVERAGE_EXCLUDED = {("US500", "4h"), ("JP225", "4h")}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellRow:
    """One substrate-cell D3-input + shape + ASS-discovery summary row."""

    instrument: str
    domain: str
    substrate: str
    n_entries: int             # frozen entries on the TRAIN slice (pre-usability)
    n_usable: int              # non-warmup, ATR-defined, non-clipped events (the denominator)
    n_warmup: int
    n_atr_undefined: int
    n_clipped_empty: int
    underpowered: bool         # n_usable < EVENT_FLOOR
    # D3 inputs (ATR units / bars)
    mfe_med: float
    mfe_q40: float
    ttp_med: float
    ttp_q75: float
    mae_q90: float
    m_anti: float
    dip_stat: float
    dip_p: float
    # minority-mass / left-tail read
    tailmass: float
    q05: float
    tail_boundary: float
    mad_zero: bool
    # ASS discovery disclosure (non-binding)
    ass_expectancy: float
    ass_expectancy_lo: float
    ass_expectancy_hi: float
    ass_median: float
    ass_median_lo: float
    ass_median_hi: float
    ass_p_gt0: float
    ass_shape_flag: bool
    ass_guard_i_defer: bool    # effective-n <= 60 AND shape flag -> expectancy deferred to median


# --------------------------------------------------------------------------- #
# Pure computation — per-substrate event direction & adaptive cap
# --------------------------------------------------------------------------- #
def _segment_state(ohlc: dict, entry_idx: np.ndarray) -> tuple[dict, object]:
    """MA-segment move set and the live in-progress state at the given entry indices."""
    seg = _ma_segment_moves(ohlc)
    if entry_idx.shape[0] == 0 or seg["confirm_epoch"].shape[0] == 0:
        return seg, None
    entry_epoch = ohlc["epoch"][entry_idx]
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(
        entry_epoch, entry_close, seg["confirm_epoch"], seg["end_price"],
        seg["end_epoch"], seg["direction"])
    return seg, state


def harami_random_direction(entry_idx: np.ndarray, state) -> np.ndarray:
    """Per-event reversal trade direction ``rd = Direction_k`` (harami / SUB-RANDOM; 0 = warmup).

    The live in-progress MA-segment move at the entry bar (``live_in_progress_state``); invalid
    (no confirmed prior move) -> 0, which the caller excludes as warmup-equivalent.
    """
    m = int(entry_idx.shape[0])
    if m == 0:
        return np.empty(0, dtype=np.int64)
    if state is None:
        return np.zeros(m, dtype=np.int64)
    rd = state.rd.astype(np.int64).copy()
    rd[~state.valid] = 0
    return rd


def _avwap_directions(frame: pl.DataFrame, instrument: str, domain: str, es) -> np.ndarray:
    """AVWAP per-event direction (+1/-1) aligned to the EntrySet trigger order."""
    from xen.avwap import (
        BAND_MULTIPLIER,
        FAST_MA,
        SLOW_MA,
        VOLUME_EXPONENT,
        generate_avwap_events,
    )

    m = int(es.entry_idx.shape[0])
    if m == 0:
        return np.empty(0, dtype=np.int64)
    result = generate_avwap_events(
        frame, instrument=instrument, domain=domain,
        band_multiplier=BAND_MULTIPLIER, volume_exponent=VOLUME_EXPONENT,
        fast_ma=FAST_MA, slow_ma=SLOW_MA)
    ev = result.events
    trig = ev.get_column("trigger_time").dt.epoch("s").to_numpy().astype(np.int64)
    direction = ev.get_column("direction").to_numpy().astype(np.int64)
    order = np.argsort(trig, kind="stable")          # match avwap_entries' stable trigger sort
    return direction[order]


def adaptive_cap(entry_idx: np.ndarray, ohlc: dict, seg: dict) -> tuple[np.ndarray, np.ndarray]:
    """Per-event adaptive time cap (bars) and warmup mask from the cell's MA-segment tempo."""
    if entry_idx.shape[0] == 0 or seg["confirm_epoch"].shape[0] == 0:
        n = int(entry_idx.shape[0])
        return np.zeros(n, dtype=np.int64), np.ones(n, dtype=bool)
    entry_epoch = ohlc["epoch"][entry_idx]
    return adaptive_time_caps_by_epoch(entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])


# --------------------------------------------------------------------------- #
# Pure computation — per-substrate-cell summary
# --------------------------------------------------------------------------- #
def _q(x: np.ndarray, q: float) -> float:
    return float(np.quantile(x, q, method="linear")) if x.size else float("nan")


def summarize_cell(
    bars: pl.DataFrame, instrument: str, domain: str,
    substrate: str, es, ass_rng: np.random.Generator,
) -> tuple[CellRow, dict]:
    """Compute the D3 inputs, shape diagnostics, and ASS discovery for one substrate-cell."""
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = es.entry_idx
    n_entries = int(entry_idx.shape[0])

    seg, state = _segment_state(ohlc, entry_idx)
    if substrate == SUB_AVWAP:
        # AVWAP direction is read from the events re-generated on the DOMAIN bars (same input
        # avwap_entries used), never the 1-minute source frame.
        direction = _avwap_directions(bars, instrument, domain, es)
    else:
        direction = harami_random_direction(entry_idx, state)
    cap, warmup = adaptive_cap(entry_idx, ohlc, seg)
    # Direction-undefined events are warmup-equivalent (no regime position) -> excluded.
    dir_ok = direction != 0
    keep = (~warmup) & dir_ok if n_entries else np.empty(0, dtype=bool)
    n_warmup = int(np.count_nonzero(~keep)) if n_entries else 0

    geom_idx = entry_idx[keep] if n_entries else entry_idx
    geom_dir = direction[keep] if n_entries else direction
    geom_cap = cap[keep] if n_entries else cap
    geom_atr = atr[geom_idx] if geom_idx.shape[0] else np.empty(0, dtype=np.float64)
    geo = lifetime_path_geometry(
        ohlc["high"], ohlc["low"], ohlc["close"], geom_atr, geom_idx, geom_dir, geom_cap, n_bars)

    usable = geo.usable
    mfe = geo.mfe[usable]
    mae = geo.mae[usable]
    ttp = geo.ttp[usable].astype(np.float64)
    outcome = geo.outcome[usable]
    n_usable = int(mfe.shape[0])
    underpowered = n_usable < EVENT_FLOOR

    dip_stat, dip_p, m_anti = antimode_mae(mae, dip_alpha=DIP_ALPHA) if n_usable else (
        float("nan"), float("nan"), float("nan"))
    ts = tail_stats(outcome, k_tail=K_TAIL)

    ass = _ass_discovery(outcome, ass_rng)
    row = CellRow(
        instrument=instrument, domain=domain, substrate=substrate,
        n_entries=n_entries, n_usable=n_usable, n_warmup=n_warmup,
        n_atr_undefined=int(geo.n_atr_undefined), n_clipped_empty=int(geo.n_clipped_empty),
        underpowered=bool(underpowered),
        mfe_med=_q(mfe, 0.50), mfe_q40=_q(mfe, 0.40),
        ttp_med=_q(ttp, 0.50), ttp_q75=_q(ttp, 0.75), mae_q90=_q(mae, 0.90),
        m_anti=float(m_anti), dip_stat=float(dip_stat), dip_p=float(dip_p),
        tailmass=ts.tailmass, q05=ts.q05, tail_boundary=ts.boundary, mad_zero=ts.mad_zero,
        ass_expectancy=ass["expectancy"], ass_expectancy_lo=ass["expectancy_lo"],
        ass_expectancy_hi=ass["expectancy_hi"], ass_median=ass["median"],
        ass_median_lo=ass["median_lo"], ass_median_hi=ass["median_hi"],
        ass_p_gt0=ass["p_gt0"], ass_shape_flag=ass["shape_flag"],
        ass_guard_i_defer=ass["guard_i_defer"])
    # Bounded per-event arrays for reproducibility + the representative MAE/outcome plots.
    per_event = {"instrument": instrument, "domain": domain, "substrate": substrate,
                 "mfe": mfe, "mae": mae, "ttp": ttp, "outcome": outcome}
    return row, per_event


def _ass_discovery(outcome: np.ndarray, rng: np.random.Generator) -> dict:
    """Non-binding ASS expectancy/median/tail + CIs with D6 Guard (i)."""
    n = int(outcome.shape[0])
    nan = float("nan")
    if n < 4:                                        # ASS / shape need >= 4 points
        return {"expectancy": nan, "expectancy_lo": nan, "expectancy_hi": nan,
                "median": nan, "median_lo": nan, "median_hi": nan, "p_gt0": nan,
                "shape_flag": False, "guard_i_defer": False}
    sc = score(outcome, shrink=False, thresholds=(0.0,))
    ci = moving_block_bootstrap_cis(
        outcome, rng, n_boot=N_BOOT, block=default_block_length(n))
    shp = shape_diagnostic(outcome)
    guard_i = bool((n <= GUARD_I_N) and shp.flag)    # defer expectancy to median
    return {"expectancy": float(sc.expectancy_direct),
            "expectancy_lo": float(ci.expectancy_lo), "expectancy_hi": float(ci.expectancy_hi),
            "median": float(sc.median), "median_lo": float(ci.median_lo),
            "median_hi": float(ci.median_hi), "p_gt0": float(sc.p_gt.get(0.0, nan)),
            "shape_flag": bool(shp.flag), "guard_i_defer": guard_i}


# --------------------------------------------------------------------------- #
# Orchestration helpers — entry generation (mirrors EXP-080 plumbing) + reconciliation
# --------------------------------------------------------------------------- #
def make_entrysets(bars: pl.DataFrame, instrument: str, domain: str, cell_index: int) -> dict:
    """Four substrate entry sets for one cell on the TRAIN slice (EXP-080 plumbing/seed)."""
    avwap = avwap_entries(bars, instrument=instrument, domain=domain)
    harami = harami_native_entries(bars, instrument=instrument, domain=domain)
    harami_count = int(harami.entry_idx.shape[0])
    rnd = random_entries(bars, instrument=instrument, domain=domain, n_target=harami_count,
                         rng=np.random.default_rng([SEED_RANDOM, cell_index, harami_count]))
    return {SUB_AVWAP: avwap, SUB_HARAMI_PARTIAL_V2A: harami,
            SUB_HARAMI_V2A_ADVNONE: harami, SUB_RANDOM: rnd}


def entrysets_equal(a: dict, b: dict) -> bool:
    """Frame-identical entry indices across all substrates (determinism check)."""
    for sub in SUBSTRATE_ORDER:
        if not np.array_equal(a[sub].entry_idx, b[sub].entry_idx):
            return False
    return True


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries only — no reloads)
# --------------------------------------------------------------------------- #
def _pivot(df: pl.DataFrame, value: str, substrate: str, instruments: list[str]) -> np.ndarray:
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    sub = df.filter(pl.col("substrate") == substrate)
    lut = {(r["instrument"], r["domain"]): r[value] for r in sub.iter_rows(named=True)}
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            v = lut.get((inst, dom))
            if v is not None:
                mat[i, j] = v
    return mat


def _heatmap_panels(df, value, instruments, title, path, cmap="viridis"):
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)
    for ax, sub in zip(axes, SUBSTRATE_ORDER):
        mat = _pivot(df, value, sub, instruments)
        im = ax.imshow(mat, aspect="auto", cmap=cmap)
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(sub.replace("SUB-", ""), fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mfe_med(df, instruments, path):
    """Plot 1 — per-substrate MFE_med heatmap (favourable capture geometry)."""
    _heatmap_panels(df, "mfe_med", instruments, "EXP-081 MFE_med (ATR) by substrate", path)


def plot_ttp(df, instruments, path):
    """Plot 2 — per-substrate TTP_med capture-time heatmap (EXP-082 H_cap input)."""
    _heatmap_panels(df, "ttp_med", instruments,
                    "EXP-081 TTP_med (bars to peak MFE) by substrate", path, cmap="magma")


def plot_tailmass(df, instruments, path):
    """Plot 4 — per-substrate tailmass heatmap (minority-mass read incl. SUB-RANDOM)."""
    _heatmap_panels(df, "tailmass", instruments,
                    "EXP-081 tailmass (fraction below median-3*MAD) by substrate", path,
                    cmap="rocket_r")


def plot_mae_representative(per_events, df, path):
    """Plot 3 — MAE distributions for representative dense cells with catastrophe boundary."""
    sns.set_theme(style="whitegrid")
    # one densest real-substrate cell per domain (by n_usable)
    real = df.filter(pl.col("substrate") != SUB_RANDOM)
    picks = []
    for dom in DOMAIN_ORDER:
        sub = real.filter((pl.col("domain") == dom) & (pl.col("n_usable") >= EVENT_FLOOR))
        if sub.height:
            top = sub.sort("n_usable", descending=True).row(0, named=True)
            picks.append((top["instrument"], top["domain"], top["substrate"]))
    fig, axes = plt.subplots(1, max(1, len(picks)), figsize=(5 * max(1, len(picks)), 4),
                             squeeze=False)
    key = {(p["instrument"], p["domain"], p["substrate"]): p for p in per_events}
    for ax, (inst, dom, sub) in zip(axes[0], picks):
        pe = key.get((inst, dom, sub))
        row = df.filter((pl.col("instrument") == inst) & (pl.col("domain") == dom)
                        & (pl.col("substrate") == sub)).row(0, named=True)
        if pe is not None and pe["mae"].size:
            ax.hist(pe["mae"], bins=40, color="indianred", edgecolor="white")
        if np.isfinite(row["m_anti"]):
            ax.axvline(row["m_anti"], color="black", ls="--", label="m_anti")
        ax.set_title(f"{inst}-{dom} {sub.replace('SUB-','')}\nMAE (ATR), dip_p={row['dip_p']:.3f}",
                     fontsize=9)
        ax.set_xlabel("MAE (ATR)")
        ax.legend(fontsize=7)
    fig.suptitle("EXP-081 representative MAE distributions (dip antimode overlay)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_outcome_bimodal(per_events, df, path):
    """Plot 5 — realized-outcome distributions for cells flagged dip_p<0.05 (bimodal shape)."""
    sns.set_theme(style="whitegrid")
    flagged = df.filter((pl.col("dip_p") < DIP_ALPHA) & (pl.col("n_usable") >= EVENT_FLOOR)
                        & (pl.col("substrate") != SUB_RANDOM)).sort("tailmass", descending=True)
    picks = [(r["instrument"], r["domain"], r["substrate"]) for r in flagged.head(6).iter_rows(
        named=True)]
    key = {(p["instrument"], p["domain"], p["substrate"]): p for p in per_events}
    n = max(1, len(picks))
    ncol = min(3, n)
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(5 * ncol, 3.5 * nrow), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, (inst, dom, sub) in zip(axes.flat, picks):
        ax.axis("on")
        pe = key.get((inst, dom, sub))
        if pe is not None and pe["outcome"].size:
            ax.hist(pe["outcome"], bins=40, color="steelblue", edgecolor="white")
            ax.axvline(0.0, color="grey", ls=":")
        ax.set_title(f"{inst}-{dom} {sub.replace('SUB-','')}", fontsize=9)
        ax.set_xlabel("realized outcome (ATR)")
    fig.suptitle("EXP-081 realized-outcome distributions — dip-flagged (bimodal) cells", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _member_set() -> set:
    """READY instrument x domain cells from EXP-080 ready_map (member set; exclude COVERAGE)."""
    rm = pl.read_csv(_EXP080_READY_MAP)
    ready = (rm.filter(pl.col("readiness_status") == "READY")
             .select(["instrument", "domain"]).unique())
    members = {(r["instrument"], r["domain"]) for r in ready.iter_rows(named=True)}
    return members - COVERAGE_EXCLUDED


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process_cell(frame: pl.DataFrame, instrument: str, period: int, cell_index: int) -> tuple:
    """All four substrate summaries for one (instrument x domain) cell + determinism check."""
    domain = DOMAIN_LABEL[period]
    bars = build_domain_bars(frame, period)
    es1 = make_entrysets(bars, instrument, domain, cell_index)
    es2 = make_entrysets(bars, instrument, domain, cell_index)
    det_entries_ok = entrysets_equal(es1, es2)

    rows: list[CellRow] = []
    per_events: list[dict] = []
    for sub in SUBSTRATE_ORDER:
        rng = np.random.default_rng([SEED_ASS, cell_index, SUBSTRATE_ORDER.index(sub)])
        row, pe = summarize_cell(bars, instrument, domain, sub, es1[sub], rng)
        rows.append(row)
        per_events.append(pe)
    entry_counts = {sub: int(es1[sub].entry_idx.shape[0]) for sub in SUBSTRATE_ORDER}
    return rows, per_events, det_entries_ok, entry_counts


def _summary_fingerprint(rows: list[CellRow]) -> str:
    """Order-independent hash of the numeric summary (determinism comparator)."""
    recs = sorted(({k: (round(v, 10) if isinstance(v, float) and np.isfinite(v) else v)
                    for k, v in asdict(r).items()} for r in rows),
                  key=lambda d: (d["instrument"], d["domain"], d["substrate"]))
    return hashlib.sha256(json.dumps(recs, sort_keys=True, default=str).encode()).hexdigest()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-081 — per-substrate realized return-structure characterization")

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
        raise RuntimeError("no instruments loaded; cannot characterize")

    # cell_index mirrors EXP-080 exactly: enumerate the full 48-cell grid in loader order so the
    # SUB-RANDOM draw key [SEED_RANDOM, cell_index, n_target] reproduces EXP-080's headline draw.
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]

    all_rows: list[CellRow] = []
    all_per_events: list[dict] = []
    nondet_cells: list[str] = []
    train_cutoffs: dict[str, int] = {}
    for ci, (inst, period) in enumerate(tqdm(full_grid, desc="characterize cells")):
        domain = DOMAIN_LABEL[period]
        if (inst, domain) not in members:
            continue
        li = loaded[inst]
        # TRAIN sub-split of the already-holdout-safe first-70% analysis frame.
        analysis_rows = int(li.frame.height)
        train_cutoff = int(analysis_rows * 0.7)
        train_frame = li.frame.slice(0, train_cutoff)
        if not train_frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"{inst}-{domain}: TRAIN frame not CloseTime-sorted")
        train_cutoffs[inst] = train_cutoff

        rows, per_events, det_ok, _counts = process_cell(train_frame, inst, period, ci)
        if not det_ok:
            nondet_cells.append(f"{inst}-{domain}")
        # determinism of the numeric summary (second full pass)
        rows2, _pe2, _d2, _c2 = process_cell(train_frame, inst, period, ci)
        if _summary_fingerprint(rows) != _summary_fingerprint(rows2):
            nondet_cells.append(f"{inst}-{domain}:summary")
        all_rows.extend(rows)
        all_per_events.extend(per_events)

    df = pl.DataFrame([asdict(r) for r in all_rows])

    # Harami entry-identity disclosure (shared detector -> identical geometry by construction).
    harami_identical = bool(
        df.filter(pl.col("substrate") == SUB_HARAMI_PARTIAL_V2A).sort(["instrument", "domain"])
        .select(["n_entries", "n_usable", "mfe_med", "mae_q90", "tailmass"]).equals(
            df.filter(pl.col("substrate") == SUB_HARAMI_V2A_ADVNONE).sort(["instrument", "domain"])
            .select(["n_entries", "n_usable", "mfe_med", "mae_q90", "tailmass"])))

    n_cells = df.height
    n_underpowered = int(df.filter(pl.col("underpowered")).height)
    nondet = sorted(set(nondet_cells))
    verdict = "CHARACTERISATION_DELIVERED" if not nondet else "HALT_NONDETERMINISM"

    # Persist results.
    df.write_parquet(RESULTS_DIR / "substrate_cell_summary.parquet")
    df.write_csv(RESULTS_DIR / "substrate_cell_summary.csv")
    _write_per_event_parquet(all_per_events, RESULTS_DIR / "per_event_geometry.parquet")
    _write_ass_json(df, RESULTS_DIR / "ass_discovery.json")

    meta = {
        "experiment": EXPERIMENT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "n_substrate_cells": int(n_cells),
        "n_member_instrument_domain_cells": len(members),
        "n_underpowered_cells": n_underpowered,
        "nondeterministic_cells": nondet,
        "harami_entry_identity_geometry": harami_identical,
        "read_region": "TRAIN sub-split [0, int(analysis_rows*0.7)); analysis-TEST + holdout "
                       "never sliced",
        "train_cutoffs": train_cutoffs,
        "seeds": {"SEED_RANDOM": SEED_RANDOM, "SEED_ASS": SEED_ASS},
        "frozen_constants": {
            "ATR_PERIOD": ATR_PERIOD, "K_TAIL": K_TAIL, "DIP_ALPHA": DIP_ALPHA,
            "EVENT_FLOOR": EVENT_FLOOR, "GUARD_I_N": GUARD_I_N, "N_BOOT": N_BOOT,
            "timecap": "xen.expectancy frozen TIMECAP_* (K=1.5, WINDOW=20, FLOOR=6, MIN_MOVES=5)",
            "cap_basis": "cell MA(20,50)-segment move-duration tempo (adaptive_time_caps_by_epoch) "
                         "applied to all 4 substrates by entry epoch",
            "quantile_method": "numpy linear",
        },
        "module_hashes": {
            "capgeo_geometry": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_geometry.py"),
            "capgeo_substrates": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_substrates.py"),
            "domain_bars": _hash_file(PROJECT_ROOT / "python/src/xen/domain_bars.py"),
            "ass": _hash_file(PROJECT_ROOT / "python/src/xen/ass.py"),
            "expectancy": _hash_file(PROJECT_ROOT / "python/src/xen/expectancy.py"),
        },
        "exp080_reconciliation": _reconcile_exp080(df),
        "holdout_untouched": True,
        "counted_test_reads": 0,
        "candidate_slots": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # Plots (bounded; from collected summaries only).
    plot_mfe_med(df, instruments, PLOTS_DIR / "01_mfe_med_heatmap.png")
    plot_ttp(df, instruments, PLOTS_DIR / "02_ttp_capture_time.png")
    plot_mae_representative(all_per_events, df, PLOTS_DIR / "03_mae_representative.png")
    plot_tailmass(df, instruments, PLOTS_DIR / "04_tailmass_heatmap.png")
    plot_outcome_bimodal(all_per_events, df, PLOTS_DIR / "05_outcome_bimodal.png")

    LOGGER.info("verdict=%s cells=%d underpowered=%d nondet=%s harami_identical=%s",
                verdict, n_cells, n_underpowered, nondet or "none", harami_identical)
    LOGGER.info("results -> %s", RESULTS_DIR)


def _reconcile_exp080(df: pl.DataFrame) -> dict:
    """Disclosure: TRAIN-slice entry counts vs EXP-080 full-slice counts (TRAIN <= full)."""
    rm = pl.read_csv(_EXP080_READY_MAP).select(
        ["instrument", "domain", "substrate", "entry_count"]).rename(
        {"entry_count": "exp080_full_count"})
    j = df.select(["instrument", "domain", "substrate", "n_entries"]).join(
        rm, on=["instrument", "domain", "substrate"], how="left")
    le = j.filter(pl.col("n_entries") <= pl.col("exp080_full_count"))
    return {"train_le_full_all": bool(le.height == j.height),
            "n_compared": int(j.height),
            "n_train_le_full": int(le.height)}


def _write_per_event_parquet(per_events: list[dict], path: Path) -> None:
    """Bounded per-event geometry (long format) for reproducibility and the plots."""
    frames = []
    for pe in per_events:
        n = pe["mfe"].shape[0]
        if n == 0:
            continue
        frames.append(pl.DataFrame({
            "instrument": [pe["instrument"]] * n, "domain": [pe["domain"]] * n,
            "substrate": [pe["substrate"]] * n,
            "mfe": pe["mfe"], "mae": pe["mae"], "ttp": pe["ttp"], "outcome": pe["outcome"]}))
    out = pl.concat(frames) if frames else pl.DataFrame(
        schema={"instrument": pl.Utf8, "domain": pl.Utf8, "substrate": pl.Utf8,
                "mfe": pl.Float64, "mae": pl.Float64, "ttp": pl.Float64, "outcome": pl.Float64})
    out.write_parquet(path)


def _write_ass_json(df: pl.DataFrame, path: Path) -> None:
    """ASS discovery disclosure (non-binding) per substrate-cell."""
    cols = ["instrument", "domain", "substrate", "n_usable", "underpowered",
            "ass_expectancy", "ass_expectancy_lo", "ass_expectancy_hi",
            "ass_median", "ass_median_lo", "ass_median_hi", "ass_p_gt0",
            "ass_shape_flag", "ass_guard_i_defer"]
    payload = {
        "note": "ASS is a NON-BINDING discovery overlay (G-017 DISCOVERY_ONLY). No decision rests "
                "on these numbers. D6 Guard (i): expectancy deferred to median where "
                "ass_guard_i_defer is true (effective-n <= 60 AND shape flag).",
        "n_boot": N_BOOT, "seed": SEED_ASS,
        "rows": df.select(cols).to_dicts()}
    path.write_text(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
