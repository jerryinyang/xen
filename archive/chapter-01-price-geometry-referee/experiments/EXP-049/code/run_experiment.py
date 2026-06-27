"""EXP-049 — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate.

`CF-HA-HARAMI-001` / HYP-002. TRAIN-only, gross, exit-agnostic; 0 candidate
slots, 0 TEST reads. For each EXP-048-READY cell (instrument x domain) this
script, on the TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by the F01 file-order prefix
   convention (no full-file sort/collect; TEST and the final-30% global holdout
   are never read);
2. aggregates the domain (5m strict; 15m/30m/1h/2h/4h at min_coverage=0.90) and
   fences every domain bar to `CloseTime <= train_end_ts`;
3. runs the frozen Wilder-ATR ZigZag substrate (`xen.zigzag`, real bars) and, at
   each confirmed trend-change, builds the Phase 014 benchmark 3-barrier system
   (both favourable geometries G1/G2; P3 1:1 adverse; P4 adaptive time cap; P5
   LOOKBACK=1) and resolves favourable-before-adverse on real OHLC, conservative
   tie-break (`xen.capture_barriers`);
4. estimates the per-cell capture rate `r = FAV/(FAV+ADV)` with the
   regime-clustered moving-block bootstrap CI, and applies the P12 viability and
   P11 composition rules as a mechanical readout (not a gate decision);
5. runs a determinism replay (second full pass, identical seeds) and the
   barrier-construction causality/fence invariant batteries, and adjudicates the
   mechanical BARRIER_REFUTED rule.

Outputs (results/): per_cell_capture.parquet, capture_rate_map.csv (G1),
capture_rate_secondary.csv (G2), censoring_disclosure.csv,
composition_readout.json, run_metadata.json. Plots (plots/): G1 capture-rate
heatmap, viability-status heatmap, resolved-count heatmap, unresolved-fraction
heatmap. Real prices throughout; no HA price enters any metric.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from matplotlib.colors import BoundaryNorm, ListedColormap
from tqdm.auto import tqdm

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
READINESS_MAP = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-048" / "results" / "readiness_map.csv"
)

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    GeometryResult,
    build_barriers,
    confirm_indices,
    resolve_first_touch,
    summarize_geometry,
    time_caps,
    viable_status,
)
from xen.zigzag import generate_zigzag  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 frozen; conventions from EXP-048)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-049"
INSTRUMENTS: list[str] = [
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500",
    "US2000", "DE30", "JP225",
]
DOMAINS: dict[str, tuple[int, float | None]] = {
    "5m": (5, None), "15m": (15, 0.90), "30m": (30, 0.90),
    "1h": (60, 0.90), "2h": (120, 0.90), "4h": (240, 0.90),
}
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
ATR_PERIOD = 14            # P1: Wilder ATR period
ATR_MULT = 1.0             # P1: ATR_MULT
MEMBER_STATUSES = ("READY", "READY_FLAGGED")
BASE_SEED = 20260614       # frozen bootstrap seed (no tuning)
GEOM_G1, GEOM_G2 = 1, 2
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts/rates "
    "derive from its own realized timeline and are not span-comparable (VAL-003)."
)
# Viability status -> integer code (for the heatmap; EXCLUDED for non-members).
VSTATUS_CODES: dict[str, int] = {
    "VIABLE": 0, "BELOW_R": 1, "CI_SPANS_050": 2,
    "NOT_VIABLE_BY_POWER": 3, "EXCLUDED": 4,
}
VSTATUS_COLORS: list[str] = ["#1a9850", "#fee08b", "#f46d43", "#cccccc", "#7b3294"]
INVARIANT_NAMES: list[str] = [
    "inv_causality", "inv_nevent_floor", "inv_nan_barrier",
    "inv_window_fence", "inv_g1_favdist",
]
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helpers (F01 TRAIN-only loader; never sorts/collects the full file)
# --------------------------------------------------------------------------- #
def find_source_file(instrument: str) -> Path:
    """Return the newest full (non-derivative) 1-minute Parquet for one symbol."""
    matches = sorted(
        p for p in DATA_DIR.glob(f"timebars_{instrument.lower()}_*.parquet")
        if not any(marker in p.name for marker in EXCLUDED_FILE_MARKERS)
    )
    if not matches:
        raise FileNotFoundError(f"no 1-minute source file for {instrument} under {DATA_DIR}")
    return matches[-1]


def load_train_1m(instrument: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix."""
    path = find_source_file(instrument)
    total_rows = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    train = pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    meta = {
        "source_file": path.name, "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows, "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": int(train.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train, meta


def load_membership() -> dict[tuple[str, str], str]:
    """Map (instrument, domain) -> EXP-048 readiness status."""
    if not READINESS_MAP.exists():
        raise FileNotFoundError(
            f"EXP-048 readiness map not found at {READINESS_MAP}; EXP-049 is gated "
            "on EXP-048 READINESS_DELIVERED + audit PASS."
        )
    rows = pl.read_csv(READINESS_MAP).select("instrument", "domain", "status").to_dicts()
    return {(r["instrument"], r["domain"]): r["status"] for r in rows}


# --------------------------------------------------------------------------- #
# Pure computation — per-cell capture core
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def compute_core(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Build the domain, ZigZag moves, both-geometry barriers, and capture stats.

    Returns a dict carrying the domain frame, both ``GeometryResult`` objects, the
    invariant counts, and the median time cap. Pure given identical inputs/seeds.
    """
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = bars.height
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    if moves.height == 0:
        return {"bars": bars, "n_bars": n_bars, "n_moves": 0,
                "g1": _empty_geometry(), "g2": _empty_geometry(),
                "invariants": {k: 0 for k in INVARIANT_NAMES},
                "m0_excluded": 0, "warmup_excluded": 0,
                "g2_degenerate_excluded": 0, "n_event_median": None}

    confirm_idx = confirm_indices(moves, bars)
    confirm_close = moves.get_column("ConfirmClose").to_numpy().astype(np.float64)
    high = bars.get_column("High").to_numpy().astype(np.float64)
    low = bars.get_column("Low").to_numpy().astype(np.float64)
    n_event, warmup = time_caps(confirm_idx)
    bar = build_barriers(moves, confirm_close)

    g1_defined = (~warmup) & (~bar["m0"])
    g2_defined = g1_defined & (~bar["g2_degenerate"])
    cls_g1 = resolve_first_touch(high, low, confirm_idx, bar["g1_fav"],
                                 bar["g1_adv"], bar["rd"], n_event, g1_defined, n_bars)
    cls_g2 = resolve_first_touch(high, low, confirm_idx, bar["g2_fav"],
                                 bar["g2_adv"], bar["rd"], n_event, g2_defined, n_bars)
    g1 = summarize_geometry(cls_g1, g1_defined, _cell_rng(cell_index, GEOM_G1))
    g2 = summarize_geometry(cls_g2, g2_defined, _cell_rng(cell_index, GEOM_G2))

    invariants = _invariants(confirm_idx, n_event, warmup, bar, g1_defined,
                             bars, train_end_epoch, n_bars)
    median_cap = (float(np.median(n_event[~warmup])) if (~warmup).any() else None)
    return {"bars": bars, "n_bars": n_bars, "n_moves": int(moves.height),
            "g1": g1, "g2": g2, "invariants": invariants,
            "m0_excluded": int(bar["m0"].sum()),
            "warmup_excluded": int(warmup.sum()),
            "g2_degenerate_excluded": int((g1_defined & bar["g2_degenerate"]).sum()),
            "n_event_median": median_cap}


def _cell_rng(cell_index: int, geom_id: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-geometry RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, geom_id])


def _invariants(
    confirm_idx: np.ndarray, n_event: np.ndarray, warmup: np.ndarray,
    bar: dict[str, np.ndarray], g1_defined: np.ndarray, bars: pl.DataFrame,
    train_end_epoch: int, n_bars: int,
) -> dict[str, int]:
    """Barrier-construction causality / fence invariant counts (all must be 0)."""
    diffs = np.diff(confirm_idx)
    fence = int((bars.get_column("CloseTime").dt.epoch("s") > train_end_epoch).sum())
    # scope §181: "no barrier field NaN/null" — blanket over BOTH geometries'
    # constructed targets, not G1 alone (g2_fav/g2_adv share c/m/e with g1).
    nan_barrier = (
        np.isnan(bar["g1_fav"][g1_defined]).sum()
        + np.isnan(bar["g1_adv"][g1_defined]).sum()
        + np.isnan(bar["g2_fav"][g1_defined]).sum()
        + np.isnan(bar["g2_adv"][g1_defined]).sum()
    )
    # scope §182: warmup events carry NO barrier (n_event == 0), never capped;
    # non-warmup events must clear the floor (N_event >= 6).
    nevent_bad = (n_event[~warmup] < 6).sum() + (n_event[warmup] != 0).sum()
    return {
        "inv_causality": int((diffs <= 0).sum()),
        "inv_nevent_floor": int(nevent_bad),
        "inv_nan_barrier": int(nan_barrier),
        "inv_window_fence": fence,
        "inv_g1_favdist": int((bar["m"][g1_defined] <= 0.0).sum()),
    }


def _empty_geometry() -> GeometryResult:
    """A zero-event GeometryResult (cells with no confirmed move)."""
    return GeometryResult(
        classes=np.empty(0, dtype=np.int64), defined=0, fav=0, adv=0, timecap=0,
        data_censored=0, resolved=0, r=None, ci_low_1s=None, ci_lo_2s=None,
        ci_hi_2s=None, boot_degenerate_frac=0.0, block_len=1)


def cores_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Frame-identical determinism comparison of two compute_core passes."""
    if not a["bars"].equals(b["bars"]):
        return False
    for key in ("g1", "g2"):
        ga, gb = a[key], b[key]
        if not np.array_equal(ga.classes, gb.classes):
            return False
        # scope §187-188: "frame-identical" — compare the full inference tuple
        # (both CI bounds, the bootstrap degeneracy fraction, and block length),
        # not just the P12-binding (r, ci_low_1s, resolved).
        if (ga.r, ga.ci_low_1s, ga.ci_lo_2s, ga.ci_hi_2s, ga.resolved,
                ga.boot_degenerate_frac, ga.block_len) != (
                gb.r, gb.ci_low_1s, gb.ci_lo_2s, gb.ci_hi_2s, gb.resolved,
                gb.boot_degenerate_frac, gb.block_len):
            return False
    return a["invariants"] == b["invariants"] and a["n_moves"] == b["n_moves"]


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def process_member_cell(
    instrument: str, domain: str, status_048: str, train_1m: pl.DataFrame,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Process one EXP-048-READY cell: capture core + determinism replay."""
    period_minutes, min_coverage = DOMAINS[domain]
    core1 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    core2 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    determinism_ok = cores_equal(core1, core2)

    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": True, "n_bars": core1["n_bars"], "n_moves": core1["n_moves"],
        "m0_excluded": core1["m0_excluded"], "warmup_excluded": core1["warmup_excluded"],
        "g2_degenerate_excluded": core1["g2_degenerate_excluded"],
        "n_event_median": core1["n_event_median"],
        "determinism_ok": determinism_ok, **core1["invariants"],
    }
    rec.update(_geometry_fields(core1["g1"], "g1"))
    rec.update(_geometry_fields(core1["g2"], "g2"))
    rec["g1_status_code"] = VSTATUS_CODES[rec["g1_viable_status"]]
    # scope §115-116: disclose G2 degeneracy as count AND fraction per cell.
    # Denominator = the G2 candidate pool (g1_defined events) = surviving
    # g2_defined + excluded degenerate; None when the pool is empty.
    g2_candidates = rec["g2_defined"] + rec["g2_degenerate_excluded"]
    rec["g2_degenerate_frac"] = (
        rec["g2_degenerate_excluded"] / g2_candidates if g2_candidates else None)
    return rec


def _geometry_fields(g: GeometryResult, prefix: str) -> dict[str, Any]:
    """Flatten one GeometryResult into per-cell record columns (+ secondaries)."""
    defined = g.defined
    fav_all = (g.fav / defined) if defined else None
    timecap_frac = (g.timecap / defined) if defined else None
    datatrunc_frac = (g.data_censored / defined) if defined else None
    return {
        f"{prefix}_defined": defined, f"{prefix}_fav": g.fav, f"{prefix}_adv": g.adv,
        f"{prefix}_timecap": g.timecap, f"{prefix}_datacensored": g.data_censored,
        f"{prefix}_resolved": g.resolved, f"{prefix}_r": g.r,
        f"{prefix}_ci_low_1s": g.ci_low_1s, f"{prefix}_ci_lo_2s": g.ci_lo_2s,
        f"{prefix}_ci_hi_2s": g.ci_hi_2s,
        f"{prefix}_boot_degenerate_frac": g.boot_degenerate_frac,
        f"{prefix}_block_len": g.block_len,
        f"{prefix}_fav_all": fav_all, f"{prefix}_timecap_frac": timecap_frac,
        f"{prefix}_datatrunc_frac": datatrunc_frac,
        f"{prefix}_viable_status": viable_status(g),
    }


def excluded_cell(instrument: str, domain: str, status_048: str) -> dict[str, Any]:
    """Record for a non-member (not EXP-048-READY) cell — unmeasured."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": False, "n_bars": None, "n_moves": None, "m0_excluded": None,
        "warmup_excluded": None, "g2_degenerate_excluded": None,
        "g2_degenerate_frac": None,
        "n_event_median": None, "determinism_ok": None,
        "g1_viable_status": "EXCLUDED", "g1_status_code": VSTATUS_CODES["EXCLUDED"],
        "g2_viable_status": "EXCLUDED",
    }
    for name in INVARIANT_NAMES:
        rec[name] = None
    return rec


# --------------------------------------------------------------------------- #
# Verdict, composition, readout
# --------------------------------------------------------------------------- #
def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Mechanical BARRIER_REFUTED rule: non-determinism on any cell, or a
    causality/fence invariant on >= 3 instruments."""
    members = [r for r in records if r["member"]]
    non_det = [f"{r['instrument']}-{r['domain']}" for r in members
               if not r.get("determinism_ok", True)]
    systematic: dict[str, int] = {}
    for name in INVARIANT_NAMES:
        instruments = {r["instrument"] for r in members if (r.get(name) or 0) > 0}
        if len(instruments) >= 3:
            systematic[name] = len(instruments)
    refuted = bool(non_det) or bool(systematic)
    return {
        "verdict": "BARRIER_REFUTED" if refuted else "CAPTURE_READINESS_DELIVERED",
        "non_deterministic_cells": non_det,
        "systematic_invariant_failures": systematic,
    }


def composition_readout(records: list[dict[str, Any]]) -> dict[str, Any]:
    """P11 composition readout for both geometries + non-binding sensitivity."""
    members = [r for r in records if r["member"]]
    g2 = _compose(members, "g2_viable_status")
    # Machine-readable disclosure: G2 operates on a systematically censored
    # subset (entry already at/through the move midpoint -> fav_distance<=0 ->
    # degenerate). A consumer reading composition_met in isolation must not
    # conflate "G2 non-viable because flat" with "G2 non-viable because half the
    # events are excluded by construction" (scope §113-117; results.md finding 3).
    g2["disclosure"] = (
        "G2 events are a systematically censored subset of the G1-defined pool: "
        "~52-60% of G1-defined events are excluded as degenerate "
        "(fav_distance<=0; entry already at/through the move midpoint) before "
        "resolution, so per-cell g2_defined is materially smaller than g1_defined "
        "and inherently lower-powered. composition_met=false here may reflect this "
        "structural censoring rather than a genuinely flat metric. Per-cell "
        "exclusion is disclosed in capture_rate_secondary.csv "
        "(g2_degenerate_frac, g2_degenerate_excluded)."
    )
    return {
        "g1_primary": _compose(members, "g1_viable_status"),
        "g2_secondary": g2,
        "sensitivity_non_binding": {
            "g1_relaxed_4cells_2instruments": _relaxed(members, "g1_viable_status", 4, 2),
            "g1_relaxed_3cells_2instruments": _relaxed(members, "g1_viable_status", 3, 2),
            "g1_r_threshold_0_52": _compose_r052(members),
        },
        "rule": "VIABLE iff r>=0.55 AND boot CI_low(1s)>0.50 AND resolved>=30; "
                "composition_met iff >=5 VIABLE cells over >=3 instruments (P11/P12).",
    }


def _compose(members: list[dict[str, Any]], status_key: str) -> dict[str, Any]:
    viable = [r for r in members if r[status_key] == "VIABLE"]
    instruments = sorted({r["instrument"] for r in viable})
    return {
        "n_viable": len(viable), "n_instruments": len(instruments),
        "instruments": ";".join(instruments),
        "viable_cells": [f"{r['instrument']}-{r['domain']}" for r in viable],
        "composition_met": len(viable) >= 5 and len(instruments) >= 3,
    }


def _relaxed(members: list[dict[str, Any]], status_key: str, c: int, i: int) -> bool:
    viable = [r for r in members if r[status_key] == "VIABLE"]
    return len(viable) >= c and len({r["instrument"] for r in viable}) >= i


def _compose_r052(members: list[dict[str, Any]]) -> dict[str, Any]:
    sel = [r for r in members if (r["g1_resolved"] or 0) >= 30
           and r["g1_r"] is not None and r["g1_r"] >= 0.52
           and r["g1_ci_low_1s"] is not None and r["g1_ci_low_1s"] > 0.50]
    instruments = sorted({r["instrument"] for r in sel})
    return {"n_cells": len(sel), "n_instruments": len(instruments),
            "composition_met": len(sel) >= 5 and len(instruments) >= 3}


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _matrix(records: list[dict[str, Any]], value: str) -> np.ndarray:
    """instrument x domain matrix (NaN where missing/None) for heatmaps."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r.get(value) for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            val = lookup.get((inst, dom))
            if val is not None:
                matrix[i, j] = float(val)
    return matrix


def plot_rate_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """G1 capture-rate r heatmap; NOT_VIABLE_BY_POWER / EXCLUDED cells are NaN."""
    matrix = _matrix(records, "g1_r")
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="RdYlGn", center=0.50, vmin=0.0, vmax=1.0,
                annot=True, fmt=".2f", xticklabels=list(DOMAINS.keys()),
                yticklabels=INSTRUMENTS, cbar_kws={"label": "r = P(fav before adv | resolved)"},
                annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: G1 capture rate (null r=0.50)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_status_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell P12 viability-status heatmap (G1)."""
    matrix = _matrix(records, "g1_status_code")
    cmap = ListedColormap(VSTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(VSTATUS_COLORS) + 0.5), cmap.N)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(DOMAINS)), list(DOMAINS.keys()))
    ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS)
    ax.set_title(f"{EXPERIMENT_ID}: G1 viability status")
    handles = [plt.Rectangle((0, 0), 1, 1, color=VSTATUS_COLORS[c])
               for c in VSTATUS_CODES.values()]
    ax.legend(handles, list(VSTATUS_CODES.keys()), bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_count_heatmap(
    records: list[dict[str, Any]], value: str, title: str, save_path: Path,
) -> None:
    """Generic per-cell count/fraction heatmap (resolved count; unresolved frac)."""
    matrix = _matrix(records, value)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", annot=True, fmt=".2g",
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": title}, annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: {title}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]]) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    enriched = [dict(r, g1_unresolved_frac=_unresolved_frac(r)) for r in records]
    plot_rate_heatmap(records, PLOTS_DIR / "g1_capture_rate_heatmap.png")
    plot_status_heatmap(records, PLOTS_DIR / "g1_viability_status_heatmap.png")
    plot_count_heatmap(records, "g1_resolved", "resolved events (G1)",
                       PLOTS_DIR / "g1_resolved_count_heatmap.png")
    plot_count_heatmap(enriched, "g1_unresolved_frac",
                       "unresolved fraction (timecap + data-trunc, G1)",
                       PLOTS_DIR / "g1_unresolved_fraction_heatmap.png")


def _unresolved_frac(rec: dict[str, Any]) -> float | None:
    tc, dt = rec.get("g1_timecap_frac"), rec.get("g1_datatrunc_frac")
    if tc is None or dt is None:
        return None
    return tc + dt


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns run metadata summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    membership = load_membership()
    cell_index = {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}

    records: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    for instrument in tqdm(INSTRUMENTS, desc="instruments"):
        members = [d for d in DOMAINS
                   if membership.get((instrument, d)) in MEMBER_STATUSES]
        if not members:
            for domain in DOMAINS:
                records.append(excluded_cell(
                    instrument, domain, membership.get((instrument, domain), "UNKNOWN")))
            continue
        train_1m, meta = load_train_1m(instrument)
        instrument_meta[instrument] = meta
        for domain in DOMAINS:
            status_048 = membership.get((instrument, domain), "UNKNOWN")
            if status_048 in MEMBER_STATUSES:
                records.append(process_member_cell(
                    instrument, domain, status_048, train_1m,
                    meta["train_end_epoch_s"], cell_index[(instrument, domain)]))
            else:
                records.append(excluded_cell(instrument, domain, status_048))
        del train_1m

    verdict = compute_verdict(records)
    readout = composition_readout(records)
    write_outputs(records, verdict, readout, instrument_meta)
    make_plots(records)
    return _summarize(records, verdict, readout)


def write_outputs(
    records: list[dict[str, Any]], verdict: dict[str, Any],
    readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the three CSVs, and the two JSON files."""
    df = pl.DataFrame(records, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_capture.parquet")

    g1_cols = ["instrument", "domain", "member", "exp048_status", "n_moves",
               "g1_defined", "g1_resolved", "g1_fav", "g1_adv", "g1_r",
               "g1_ci_low_1s", "g1_ci_lo_2s", "g1_ci_hi_2s", "g1_block_len",
               "g1_boot_degenerate_frac", "g1_viable_status"]
    df.select([c for c in g1_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "capture_rate_map.csv")

    g2_cols = ["instrument", "domain", "member", "g2_defined",
               "g2_degenerate_excluded", "g2_degenerate_frac", "g2_resolved",
               "g2_fav", "g2_adv", "g2_r", "g2_ci_low_1s", "g2_ci_lo_2s",
               "g2_ci_hi_2s", "g2_viable_status"]
    df.select([c for c in g2_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "capture_rate_secondary.csv")

    cens_cols = ["instrument", "domain", "g1_defined", "g1_timecap",
                 "g1_datacensored", "g1_timecap_frac", "g1_datatrunc_frac",
                 "g1_fav_all", "warmup_excluded", "m0_excluded",
                 "g2_degenerate_excluded", "n_event_median"]
    df.select([c for c in cens_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "censoring_disclosure.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-A", "hypothesis": "HYP-002", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "barrier_anchor": "ZigZag trend-change confirmation (substrate capture ceiling)",
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "atr_estimator": "Wilder",
            "favourable_fraction": 0.50, "adverse": "1:1 R:R (P3)",
            "third_barrier": "N=max(6,round(1.5*median(trailing-20 confirmed-move durations)))",
            "lookback": 1, "tie_break": "same-bar double-touch -> ADVERSE",
            "n_boot": 10000, "base_seed": BASE_SEED,
            "geometries": {"G1_primary": "distance-based (0.5*M)",
                           "G2_secondary": "retracement-level (move midpoint)"},
        },
        "membership": {
            "source": "EXP-048 readiness_map.csv (READY + READY_FLAGGED)",
            "n_member_cells": sum(1 for r in records if r["member"]),
            "n_excluded_cells": sum(1 for r in records if not r["member"]),
        },
        "preconditions": {
            "gate": "EXP-049 execution gate is blocked until EXP-048 reaches "
                    "READINESS_DELIVERED + audit PASS (scope §17-23; pre-execution "
                    "review info-note 1).",
            "exp048_readiness_verdict": "READINESS_DELIVERED",
            "exp048_audit_verdict": "PASS",
            "exp048_post_experiment_review": "APPROVE",
            "satisfied": True,
            "evidence": "EXP-048/audit.md, "
                        "EXP-048/governance/post-experiment-review.md",
        },
        "denominators": {
            "primary_r": "FAV / (FAV + ADV) over resolved; resolved<30 -> NOT_VIABLE_BY_POWER",
            "fav_all": "FAV / defined (built barriers)",
            "censoring": "TIMECAP/defined and DATA_CENSORED/defined",
        },
        "verdict": verdict, "composition_readout": readout,
        "de30_disclosure": DE30_DISCLOSURE, "instrument_meta": instrument_meta,
        "holdout_fence": (
            "Only Parquet metadata + first train_rows file-order rows read per "
            "instrument; full file never sorted/collected; every domain bar fenced "
            "to CloseTime <= train_end_ts; forward resolution windows clipped to the "
            "TRAIN edge; TEST and final-30% holdout never read."
        ),
        "note": "Routing (PROCEED_TO_SCREEN vs CHARACTERISED_NOT_VIABLE) is the §10 "
                "G1 desk adjudication on this readout, not self-declared here.",
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(
    records: list[dict[str, Any]], verdict: dict[str, Any], readout: dict[str, Any],
) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        status_counts[r["g1_viable_status"]] = status_counts.get(r["g1_viable_status"], 0) + 1
    return {"verdict": verdict["verdict"], "g1_status_counts": status_counts,
            "g1_composition_met": readout["g1_primary"]["composition_met"],
            "g1_n_viable": readout["g1_primary"]["n_viable"],
            "g1_n_instruments": readout["g1_primary"]["n_instruments"],
            "non_deterministic_cells": verdict["non_deterministic_cells"],
            "systematic_invariant_failures": verdict["systematic_invariant_failures"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("G1 viability status counts: %s", json.dumps(summary["g1_status_counts"]))
    LOGGER.info("G1 composition: %s VIABLE cells over %s instruments (met=%s)",
                summary["g1_n_viable"], summary["g1_n_instruments"],
                summary["g1_composition_met"])
    if summary["non_deterministic_cells"]:
        LOGGER.info("NON-DETERMINISTIC: %s", summary["non_deterministic_cells"])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
