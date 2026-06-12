"""Experiment EXP-044: Phase 011 Track A Per-Cell Event-Level Inference Calibration.

Implements the approved analysis plan (analysis-plan.md). For each of the 50
READY cells certified by EXP-043 (TRAIN stratum only, F01 file-order rows):

1. regenerate the frozen-baseline regime/event scaffolding bit-for-bit and
   assert the realized event count matches EXP-043 (consistency gate);
2. run 500 N1 (placebo-on-real) and 500 N2 (block-permuted) null draws at the
   cell's realized event count and direction mix, plus planted edges
   g in {1,2,4,8,16,32,64,128} bps evaluated from the N1 draws (bootstrap CI
   shifts by g; the sign-permutation p is recomputed per g);
3. score each draw with the frozen single-cell EXP-027 decision rule
   (effect > 0 and CI_low > 0 and p <= alpha; no Holm, no instrument pooling);
4. summarize per-cell FPR / TPR / event-level MDE with Wilson precision and
   classify each cell COVERED / NOT_COVERED / CALIBRATION_UNDERPOWERED;
5. determinism replay: two predeclared cells fully re-run and compared.

No real event outcome is ever computed; no TEST or holdout row is touched.

Outputs: ``results/coverage_map.csv``, ``results/fpr_per_cell.csv``,
``results/tpr_mde_per_cell.csv``, ``results/draw_verdicts.parquet``,
``results/run_metadata.json``, and five plots from the aggregated summaries.
"""
from __future__ import annotations

import json
import logging
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_DIR.parents[2]
SRC_DIR = PROJECT_ROOT / "python" / "src"
CODE_DIR = EXP_DIR / "code"
for extra in (str(SRC_DIR), str(CODE_DIR)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import cell_calibration as cc  # noqa: E402
from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.referee_calibration import estimate_block_length, seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen by scope / analysis plan — no tuning levers)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-044"
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP043_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-043" / "results"

DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
MIN_COVERAGE = 0.90
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

EDGE_GRID: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 128)   # bps, geometric
N_DRAWS = 500
N_BOOT = 1_000
N_PERM = 1_000
BOOT_CHUNK = 2_000
PERM_CHUNK = 500
ALPHAS: tuple[float, ...] = (0.10, 0.05, 0.01)
ALPHA0 = 0.05
TPR_TARGET = 0.80
FPR_HALFWIDTH_MAX = 0.03
TPR_HALFWIDTH_MAX = 0.05
COMPLETION_FLOOR = 0.90
UNDERPOWERED_INCONCLUSIVE_FRACTION = 1.0 / 3.0
DISAGREEMENT_INSTRUMENTS = 3
REPLAY_CELLS: tuple[tuple[str, str], ...] = (("BTCUSD", "1h"), ("JP225", "4h"))

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellSpec:
    """One READY cell with its EXP-043 realized-count targets."""

    instrument: str
    domain: str
    train_events: int
    bull_events: int
    bear_events: int


# --------------------------------------------------------------------------- #
# I/O helpers
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


def load_train_frame(instrument: str, expected: dict[str, Any]) -> pl.DataFrame:
    """Load exactly the TRAIN 1-minute rows (F01/R1.3 pattern), bound to EXP-043.

    ``analysis = floor(0.7 * total)``; ``train = floor(0.7 * analysis)``; only
    the first ``train`` file-order rows are collected. TEST and holdout rows
    never enter the scan engine; chronological order is re-asserted. The source
    file, row counts, and TRAIN-end timestamp are asserted against the EXP-043
    boundary record so EXP-044 runs on the certified substrate bit-for-bit.
    """
    path = find_source_file(instrument)
    if path.name != expected["source_file"]:
        raise RuntimeError(
            f"{instrument}: source file {path.name} != EXP-043 certified "
            f"{expected['source_file']}"
        )
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    if total != int(expected["total_rows_1m"]):
        raise RuntimeError(f"{instrument}: total rows {total} != EXP-043 "
                           f"{expected['total_rows_1m']}")
    train_rows = int(math.floor(TRAIN_FRACTION * math.floor(ANALYSIS_FRACTION * total)))
    if train_rows != int(expected["train_rows_1m"]):
        raise RuntimeError(f"{instrument}: train rows {train_rows} != EXP-043 "
                           f"{expected['train_rows_1m']}")
    frame = (
        pl.scan_parquet(path)
        .select("Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume")
        .head(train_rows)
        .collect()
    )
    if frame.height != train_rows:
        raise RuntimeError(f"{instrument}: collected {frame.height} != train_rows {train_rows}")
    close_time = frame.get_column("CloseTime")
    if not close_time.is_sorted() or close_time.n_unique() != frame.height:
        raise RuntimeError(f"{instrument}: TRAIN slice not strictly chronological")
    if str(close_time.max()) != str(expected["train_end_ts"]):
        raise RuntimeError(f"{instrument}: TRAIN end {close_time.max()} != EXP-043 "
                           f"{expected['train_end_ts']}")
    return frame


def load_ready_cells() -> tuple[list[CellSpec], dict[str, dict[str, Any]]]:
    """Dependency gate on EXP-043: READY grid, count targets, boundary record.

    Cross-checks ``readiness_map.csv`` against ``power_statement.csv`` (same
    READY set, exactly 50 cells, JP225-2h recorded NOT_READY) and returns the
    per-instrument boundary record for source-identity binding.
    """
    metadata = json.loads((EXP043_RESULTS / "run_metadata.json").read_text())
    if metadata.get("verdict") != "READINESS_DELIVERED" or metadata.get("substrate_alert"):
        raise RuntimeError(
            "EXP-043 dependency gate failed: verdict="
            f"{metadata.get('verdict')} substrate_alert={metadata.get('substrate_alert')}"
        )
    boundaries: dict[str, dict[str, Any]] = metadata["boundaries"]
    power = pl.read_csv(EXP043_RESULTS / "power_statement.csv")
    readiness = pl.read_csv(EXP043_RESULTS / "readiness_map.csv")
    ready_power = {(r["instrument"], r["domain"])
                   for r in power.filter(pl.col("verdict") == "READY").to_dicts()}
    ready_map = {(r["instrument"], r["domain"])
                 for r in readiness.filter(pl.col("verdict") == "READY").to_dicts()}
    if ready_power != ready_map:
        raise RuntimeError("EXP-043 readiness_map and power_statement READY sets differ")
    if len(ready_power) != 50 or ("JP225", "2h") in ready_power:
        raise RuntimeError(
            f"unexpected READY grid: {len(ready_power)} cells "
            f"(expected 50, JP225-2h excluded)"
        )
    ready = power.filter(pl.col("verdict") == "READY").sort(["instrument", "domain"])
    cells = [
        CellSpec(r["instrument"], r["domain"], int(r["train_events"]),
                 int(r["bull_events"]), int(r["bear_events"]))
        for r in ready.to_dicts()
    ]
    missing = {c.instrument for c in cells} - set(boundaries)
    if missing:
        raise RuntimeError(f"EXP-043 boundary record missing instruments: {sorted(missing)}")
    return cells, boundaries


# --------------------------------------------------------------------------- #
# Precompute (real TRAIN scaffolding; consistency gate vs EXP-043)
# --------------------------------------------------------------------------- #
def build_precompute(
    spec: CellSpec, frame_1m: pl.DataFrame
) -> tuple[cc.CellPrecompute, dict[str, Any]]:
    """Regenerate the frozen-baseline scaffolding for one cell and precompute.

    Hard-fails if the regenerated event count differs from the EXP-043 realized
    count (consistency gate). Real trigger bars are recorded only as exclusions
    and their forward outcomes are NaN-masked, so no real event outcome can be
    gathered, even accidentally. Returns the precompute plus per-cell
    diagnostics (regimes per direction, block length).
    """
    minutes = DOMAINS[spec.domain]
    bars = aggregate_ohlc(frame_1m, period_minutes=minutes, min_coverage=MIN_COVERAGE)
    result = generate_avwap_events(
        bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume"),
        instrument=spec.instrument, domain=spec.domain,
    )
    if result.events.height != spec.train_events:
        raise RuntimeError(
            f"{spec.instrument}-{spec.domain}: regenerated event count "
            f"{result.events.height} != EXP-043 realized {spec.train_events}"
        )
    n = bars.height
    log_close = np.log(bars.get_column("Close").to_numpy())
    bar_log_returns = np.diff(log_close)

    real_trigger = np.zeros(n, dtype=bool)
    if result.events.height:
        real_trigger[result.events.get_column("trigger_idx").to_numpy()] = True

    regimes = result.regimes
    regime_start = regimes.get_column("regime_start_idx").to_numpy()
    regime_end = regimes.get_column("regime_end_idx").to_numpy()
    regime_dir = regimes.get_column("direction").to_numpy()
    pools = tuple(
        cc.regime_interior_pool(int(s), int(e), n, real_trigger)
        for s, e in zip(regime_start, regime_end)
    )

    # Exact placement allocation: each direction's realized count target is
    # distributed across that direction's regime pools by largest remainder
    # (deterministic), so every draw places exactly the realized counts unless
    # the pools themselves are too small (recorded per draw).
    regime_alloc = np.zeros(len(pools), dtype=np.int64)
    for d, target in ((1, spec.bull_events), (-1, spec.bear_events)):
        idx = [i for i, rd in enumerate(regime_dir) if int(rd) == d]
        sizes = np.array([pools[i].size for i in idx], dtype=np.int64)
        for i, a in zip(idx, cc.allocate_pool_targets(sizes, target)):
            regime_alloc[i] = a

    # Anti-overfitting fence, made literal: real trigger bars' forward outcomes
    # are NaN — pools already exclude them, and any accidental gather would
    # propagate loudly into the paired diffs instead of leaking silently.
    dlog_real = cc.forward_logdiff_from_close(log_close, cc.H_CAL)
    dlog_real[real_trigger] = np.nan

    diag = {
        "n_regimes_bull": int((regime_dir == 1).sum()),
        "n_regimes_bear": int((regime_dir == -1).sum()),
        "block_length": int(estimate_block_length(bar_log_returns)),
        "alloc_bull": int(regime_alloc[regime_dir == 1].sum()),
        "alloc_bear": int(regime_alloc[regime_dir == -1].sum()),
    }
    pre = cc.CellPrecompute(
        instrument=spec.instrument,
        domain=spec.domain,
        n=n,
        log_close=log_close,
        bar_log_returns=bar_log_returns,
        block_length=diag["block_length"],
        regime_id=regimes.get_column("regime_id").to_numpy(),
        regime_dir=regime_dir,
        regime_pool=pools,
        real_trigger=real_trigger,
        dlog_real=dlog_real,
        regime_alloc=regime_alloc,
        n_target_bull=spec.bull_events,
        n_target_bear=spec.bear_events,
    )
    return pre, diag


# --------------------------------------------------------------------------- #
# Per-cell calibration (pure computation over the precompute)
# --------------------------------------------------------------------------- #
def _evaluate_draw(
    pre: cc.CellPrecompute, generator: str, draw: int, dlog: np.ndarray,
    edges: tuple[int, ...],
) -> list[dict[str, Any]]:
    """One draw: placement -> controls -> per-edge effect/CI/p rows.

    The bootstrap runs once at g=0; a planted edge shifts the effect and the
    percentile CI by exactly +g, while the sign-permutation p is recomputed on
    the shifted differences (sign flips of shifted data are not a shift).
    """
    place_rng = np.random.default_rng(
        seed_for(EXPERIMENT_ID, pre.instrument, pre.domain, generator, "place", draw)
    )
    ev = cc.simulate_cell_draw(pre, dlog, place_rng)
    base = {
        "instrument": pre.instrument, "domain": pre.domain,
        "generator": generator, "draw": draw,
        "n_events": ev.n_events, "n_bull": ev.n_bull, "n_bear": ev.n_bear,
        "n_placed_bull": ev.n_placed_bull, "n_placed_bear": ev.n_placed_bear,
        "placement_exact": (ev.n_placed_bull == pre.n_target_bull
                            and ev.n_placed_bear == pre.n_target_bear),
        "reportable": ev.reportable,
    }
    if not ev.reportable:
        return [base | {"g_bps": float(g), "effect_bps": float("nan"),
                        "ci_low": float("nan"), "ci_high": float("nan"),
                        "p_value": float("nan")}
                for g in (0,) + edges]
    effect0 = float(ev.paired_diff.mean())
    boot_rng = np.random.default_rng(
        seed_for(EXPERIMENT_ID, pre.instrument, pre.domain, generator, "boot", draw)
    )
    dist = cc.bootstrap_cell_distribution(cc.build_cell_strata(ev), boot_rng, N_BOOT, BOOT_CHUNK)
    finite = dist[np.isfinite(dist)]
    ci0_low, ci0_high = (
        (float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5)))
        if finite.size else (float("nan"), float("nan"))
    )
    rows = []
    for g in (0,) + edges:
        perm_rng = np.random.default_rng(
            seed_for(EXPERIMENT_ID, pre.instrument, pre.domain, generator, "perm", draw, g)
        )
        p = cc.permutation_p_cell(ev.paired_diff + g, effect0 + g, perm_rng, N_PERM, PERM_CHUNK)
        rows.append(base | {"g_bps": float(g), "effect_bps": effect0 + g,
                            "ci_low": ci0_low + g, "ci_high": ci0_high + g,
                            "p_value": p})
    return rows


def run_cell(pre: cc.CellPrecompute) -> list[dict[str, Any]]:
    """All draws for one cell: N1 (nulls + planted edges) and N2 (null only)."""
    rows: list[dict[str, Any]] = []
    for draw in range(N_DRAWS):
        rows.extend(_evaluate_draw(pre, "N1", draw, pre.dlog_real, EDGE_GRID))
    for draw in range(N_DRAWS):
        block_rng = np.random.default_rng(
            seed_for(EXPERIMENT_ID, pre.instrument, pre.domain, "N2", "block", draw)
        )
        permuted = cc.block_permute_returns(pre.bar_log_returns, pre.block_length, block_rng)
        dlog2 = cc.forward_logdiff_from_returns(permuted, cc.H_CAL, pre.n)
        dlog2[pre.real_trigger] = np.nan  # same fence mask as the real path
        rows.extend(_evaluate_draw(pre, "N2", draw, dlog2, ()))
    return rows


# --------------------------------------------------------------------------- #
# Summaries — FPR / TPR / MDE / coverage (pure over the draw rows)
# --------------------------------------------------------------------------- #
def _for_flag(frame: pl.DataFrame, alpha: float) -> pl.Series:
    return (
        (frame["effect_bps"] > 0) & (frame["ci_low"] > 0) & (frame["p_value"] <= alpha)
    )


def summarize_rates(draws: pl.DataFrame) -> tuple[list[dict], list[dict]]:
    """Per-cell FPR rows (by generator/alpha) and TPR rows (by edge/alpha)."""
    fpr_rows, tpr_rows = [], []
    for (inst, dom), cell in draws.group_by(["instrument", "domain"], maintain_order=True):
        for generator in ("N1", "N2"):
            null = cell.filter((pl.col("generator") == generator) & (pl.col("g_bps") == 0.0))
            rep = null.filter(pl.col("reportable"))
            completion = rep.height / null.height if null.height else float("nan")
            for alpha in ALPHAS:
                k = int(_for_flag(rep, alpha).sum())
                low, high, half = cc.wilson_interval(k, rep.height)
                fpr_rows.append({
                    "instrument": inst, "domain": dom, "generator": generator,
                    "alpha": alpha, "n_reportable_draws": rep.height,
                    "n_draws": null.height, "completion_rate": completion,
                    "fpr": k / rep.height if rep.height else float("nan"),
                    "wilson_low": low, "wilson_high": high, "wilson_halfwidth": half,
                })
        planted = cell.filter((pl.col("generator") == "N1") & (pl.col("g_bps") > 0.0)
                              & pl.col("reportable"))
        for g in EDGE_GRID:
            sub = planted.filter(pl.col("g_bps") == float(g))
            for alpha in ALPHAS:
                k = int(_for_flag(sub, alpha).sum())
                low, high, half = cc.wilson_interval(k, sub.height)
                tpr_rows.append({
                    "instrument": inst, "domain": dom, "g_bps": float(g),
                    "alpha": alpha, "n_reportable_draws": sub.height,
                    "tpr": k / sub.height if sub.height else float("nan"),
                    "wilson_low": low, "wilson_high": high, "wilson_halfwidth": half,
                })
    return fpr_rows, tpr_rows


def classify_cells(
    cells: list[CellSpec], fpr_rows: list[dict], tpr_rows: list[dict],
    diags: dict[tuple[str, str], dict],
) -> list[dict]:
    """Per-cell coverage verdict at alpha0 per the predeclared plan rules.

    Any FPR point estimate above alpha0 at adequate precision is NOT_COVERED
    (the Wilson-lower-bound case is flagged 'material'); the underpowered class
    is reserved for genuine precision/completion shortfalls.
    """
    out = []
    for spec in cells:
        fpr = {r["generator"]: r for r in fpr_rows
               if r["instrument"] == spec.instrument and r["domain"] == spec.domain
               and r["alpha"] == ALPHA0}
        tpr = sorted(
            (r for r in tpr_rows
             if r["instrument"] == spec.instrument and r["domain"] == spec.domain
             and r["alpha"] == ALPHA0),
            key=lambda r: r["g_bps"],
        )
        completion_ok = all(r["completion_rate"] >= COMPLETION_FLOOR for r in fpr.values())
        fpr_precise = all(r["wilson_halfwidth"] <= FPR_HALFWIDTH_MAX for r in fpr.values())
        tpr_usable = [r for r in tpr if r["wilson_halfwidth"] <= TPR_HALFWIDTH_MAX
                      or r["tpr"] >= TPR_TARGET]
        fpr_controlled = all(r["fpr"] <= ALPHA0 for r in fpr.values())
        fpr_material_excess = any(r["wilson_low"] > ALPHA0 for r in fpr.values())
        mde = next((r["g_bps"] for r in tpr_usable if r["tpr"] >= TPR_TARGET), None)

        if not completion_ok or not fpr_precise:
            verdict, reason = "CALIBRATION_UNDERPOWERED", "completion_or_precision_floor_unmet"
        elif fpr_material_excess:
            verdict, reason = "NOT_COVERED", "fpr_materially_above_alpha0"
        elif not fpr_controlled:
            verdict, reason = "NOT_COVERED", "fpr_point_above_alpha0_adequate_precision"
        elif mde is not None:
            verdict, reason = "COVERED", ""
        else:
            verdict, reason = "NOT_COVERED", "no_finite_mde_on_grid"
        diag = diags.get((spec.instrument, spec.domain), {})
        out.append({
            "instrument": spec.instrument, "domain": spec.domain,
            "train_events": spec.train_events, "verdict": verdict, "reason": reason,
            "fpr_n1": fpr.get("N1", {}).get("fpr"), "fpr_n2": fpr.get("N2", {}).get("fpr"),
            "mde_bps": mde if mde is not None else None,
            "n_regimes_bull": diag.get("n_regimes_bull"),
            "n_regimes_bear": diag.get("n_regimes_bear"),
            "block_length": diag.get("block_length"),
            "alloc_bull": diag.get("alloc_bull"),
            "alloc_bear": diag.get("alloc_bear"),
        })
    return out


def substrate_check(coverage: list[dict], fpr_rows: list[dict]) -> dict[str, Any]:
    """METHOD_NOT_TRANSFERABLE triggers: two-null disagreement / domain-wide excess."""
    disagree_instruments: set[str] = set()
    for row in coverage:
        pair = [r for r in fpr_rows
                if r["instrument"] == row["instrument"] and r["domain"] == row["domain"]
                and r["alpha"] == ALPHA0 and r["wilson_halfwidth"] <= FPR_HALFWIDTH_MAX]
        if len(pair) == 2:
            a, b = pair
            if a["wilson_low"] > b["wilson_high"] or b["wilson_low"] > a["wilson_high"]:
                disagree_instruments.add(row["instrument"])
    domain_wide = []
    for domain in DOMAINS:
        rows = [r for r in fpr_rows if r["domain"] == domain and r["alpha"] == ALPHA0
                and r["wilson_halfwidth"] <= FPR_HALFWIDTH_MAX]
        if rows and all(r["wilson_low"] > ALPHA0 for r in rows):
            domain_wide.append(domain)
    return {
        "two_null_disagreement_instruments": sorted(disagree_instruments),
        "domain_wide_fpr_excess": domain_wide,
        "triggered": len(disagree_instruments) >= DISAGREEMENT_INSTRUMENTS or bool(domain_wide),
    }


# --------------------------------------------------------------------------- #
# Plotting (inputs: aggregated summary rows only — no reloads)
# --------------------------------------------------------------------------- #
def _cell_matrix(rows: list[dict], instruments: list[str], value: str) -> np.ndarray:
    matrix = np.full((len(instruments), len(DOMAINS)), np.nan)
    domains = list(DOMAINS)
    for r in rows:
        if r.get(value) is not None:
            matrix[instruments.index(r["instrument"]), domains.index(r["domain"])] = r[value]
    return matrix


def plot_fpr_heatmap(fpr_rows: list[dict], instruments: list[str], path: Path) -> None:
    """17x3 per-cell FPR heatmap, one panel per null generator (alpha0)."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 9), sharey=True)
    for ax, generator in zip(axes, ("N1", "N2")):
        rows = [r | {"v": r["fpr"]} for r in fpr_rows
                if r["generator"] == generator and r["alpha"] == ALPHA0]
        matrix = _cell_matrix(rows, instruments, "v")
        im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=0.0, vmax=2 * ALPHA0)
        ax.set_xticks(range(len(DOMAINS)), list(DOMAINS))
        ax.set_title(f"{generator} FPR (alpha0={ALPHA0})")
        for i in range(len(instruments)):
            for j in range(len(DOMAINS)):
                if np.isfinite(matrix[i, j]):
                    ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=6)
    axes[0].set_yticks(range(len(instruments)), instruments, fontsize=7)
    fig.colorbar(im, ax=axes, label="FPR")
    fig.suptitle("EXP-044 per-cell FPR by null generator")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_heatmap(coverage: list[dict], instruments: list[str], path: Path) -> None:
    """17x3 per-cell MDE heatmap; non-covered/underpowered cells annotated."""
    matrix = _cell_matrix(coverage, instruments, "mde_bps")
    fig, ax = plt.subplots(figsize=(6.5, 10))
    with np.errstate(divide="ignore"):
        im = ax.imshow(np.log2(matrix), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(DOMAINS)), list(DOMAINS))
    ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
    domains = list(DOMAINS)
    for r in coverage:
        i, j = instruments.index(r["instrument"]), domains.index(r["domain"])
        label = f"{int(r['mde_bps'])}" if r["mde_bps"] is not None else r["verdict"][:9]
        ax.text(j, i, label, ha="center", va="center", color="white", fontsize=6)
    ax.set_title("EXP-044 per-cell event-level MDE (bps, log2 shading)")
    fig.colorbar(im, ax=ax, label="log2(MDE bps)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_mde_vs_count(coverage: list[dict], path: Path) -> None:
    """Per-cell MDE vs realized TRAIN event count (log-log), by domain."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    markers = {"1h": "o", "2h": "s", "4h": "^"}
    for domain in DOMAINS:
        sub = [r for r in coverage if r["domain"] == domain and r["mde_bps"] is not None]
        if sub:
            ax.scatter([r["train_events"] for r in sub], [r["mde_bps"] for r in sub],
                       marker=markers[domain], alpha=0.8, label=domain)
            for r in sub:
                ax.annotate(r["instrument"], (r["train_events"], r["mde_bps"]),
                            fontsize=4.5, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("realized TRAIN event count")
    ax.set_ylabel("per-cell event-level MDE (bps)")
    ax.set_title("EXP-044 MDE vs realized event count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_precision(fpr_rows: list[dict], coverage: list[dict], path: Path) -> None:
    """Wilson half-widths and completion rates across cells (alpha0)."""
    rows = [r for r in fpr_rows if r["alpha"] == ALPHA0]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist([r["wilson_halfwidth"] for r in rows if np.isfinite(r["wilson_halfwidth"])],
                 bins=24, color="steelblue")
    axes[0].axvline(FPR_HALFWIDTH_MAX, color="red", linestyle="--",
                    label=f"threshold {FPR_HALFWIDTH_MAX}")
    axes[0].set_xlabel("FPR Wilson half-width")
    axes[0].legend()
    axes[1].hist([r["completion_rate"] for r in rows if np.isfinite(r["completion_rate"])],
                 bins=24, color="darkorange")
    axes[1].axvline(COMPLETION_FLOOR, color="red", linestyle="--",
                    label=f"floor {COMPLETION_FLOOR}")
    axes[1].set_xlabel("draw completion rate")
    axes[1].legend()
    n_under = sum(1 for r in coverage if r["verdict"] == "CALIBRATION_UNDERPOWERED")
    fig.suptitle(f"EXP-044 calibration precision diagnostic ({n_under} underpowered cells)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_verdict_summary(coverage: list[dict], verdict: str, path: Path) -> None:
    """Coverage-verdict counts and the experiment headline."""
    counts: dict[str, int] = {}
    for r in coverage:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(list(counts), list(counts.values()),
           color=["seagreen" if k == "COVERED" else "indianred" if k == "NOT_COVERED"
                  else "goldenrod" for k in counts])
    for i, (k, v) in enumerate(counts.items()):
        ax.text(i, v, str(v), ha="center", va="bottom")
    ax.set_title(f"EXP-044 coverage verdicts — experiment: {verdict}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_all_cells(
    cells: list[CellSpec], boundaries: dict[str, dict[str, Any]], desc: str
) -> tuple[pl.DataFrame, dict[tuple[str, str], dict]]:
    """Build precomputes instrument-by-instrument and run every cell's draws."""
    rows: list[dict[str, Any]] = []
    diags: dict[tuple[str, str], dict] = {}
    by_instrument: dict[str, list[CellSpec]] = {}
    for spec in cells:
        by_instrument.setdefault(spec.instrument, []).append(spec)
    with tqdm(total=len(cells), desc=desc) as progress:
        for instrument, specs in by_instrument.items():
            frame_1m = load_train_frame(instrument, boundaries[instrument])
            for spec in specs:
                pre, diag = build_precompute(spec, frame_1m)
                diags[(spec.instrument, spec.domain)] = diag
                progress.set_postfix_str(f"{spec.instrument}-{spec.domain}")
                rows.extend(run_cell(pre))
                progress.update(1)
            del frame_1m
    return pl.DataFrame(rows), diags


def determinism_replay(
    cells: list[CellSpec], boundaries: dict[str, dict[str, Any]], draws: pl.DataFrame
) -> bool:
    """Fully re-run the two predeclared replay cells and compare frame-identically."""
    replay_specs = [c for c in cells if (c.instrument, c.domain) in REPLAY_CELLS]
    replay, _ = run_all_cells(replay_specs, boundaries,
                              "EXP-044 determinism replay (2 cells)")
    sort_keys = ["instrument", "domain", "generator", "draw", "g_bps"]
    for spec in replay_specs:
        mask = (pl.col("instrument") == spec.instrument) & (pl.col("domain") == spec.domain)
        if not draws.filter(mask).sort(sort_keys).equals(replay.filter(mask).sort(sort_keys)):
            LOGGER.warning("determinism replay MISMATCH on %s-%s",
                           spec.instrument, spec.domain)
            return False
    return True


def main() -> None:
    """Run the 50-cell per-cell inference calibration end to end (TRAIN-only)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    cc.verify_control_matching()
    cells, boundaries = load_ready_cells()
    instruments = sorted({c.instrument for c in cells})
    LOGGER.info("dependency gate PASS: %d READY cells across %d instruments "
                "(source identity bound to EXP-043 boundaries)",
                len(cells), len(instruments))

    draws, diags = run_all_cells(cells, boundaries,
                                 f"EXP-044 calibration ({len(cells)} cells)")
    draws.write_parquet(RESULTS_DIR / "draw_verdicts.parquet")

    fpr_rows, tpr_rows = summarize_rates(draws)
    coverage = classify_cells(cells, fpr_rows, tpr_rows, diags)
    substrate = substrate_check(coverage, fpr_rows)
    determinism_pass = determinism_replay(cells, boundaries, draws)
    placement_exact_rate = float(draws.get_column("placement_exact").mean())

    n_under = sum(1 for r in coverage if r["verdict"] == "CALIBRATION_UNDERPOWERED")
    if substrate["triggered"]:
        verdict = "METHOD_NOT_TRANSFERABLE"
    elif n_under > UNDERPOWERED_INCONCLUSIVE_FRACTION * len(coverage) or not determinism_pass:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "CALIBRATION_DELIVERED"

    pl.DataFrame(fpr_rows).write_csv(RESULTS_DIR / "fpr_per_cell.csv")
    pl.DataFrame(tpr_rows).write_csv(RESULTS_DIR / "tpr_mde_per_cell.csv")
    pl.DataFrame(coverage).write_csv(RESULTS_DIR / "coverage_map.csv")

    counts: dict[str, int] = {}
    for r in coverage:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    metadata = {
        "experiment": EXPERIMENT_ID,
        "verdict": verdict,
        "determinism_pass": determinism_pass,
        "coverage_counts": counts,
        "substrate_check": substrate,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "placement_exact_rate": placement_exact_rate,
        "method": {
            "h_cal_bars": cc.H_CAL, "edge_grid_bps": list(EDGE_GRID),
            "n_draws": N_DRAWS, "n_bootstrap": N_BOOT, "n_permutation": N_PERM,
            "alphas": list(ALPHAS), "alpha0": ALPHA0, "tpr_target": TPR_TARGET,
            "min_reportable_events": cc.MIN_REPORTABLE_EVENTS,
            "min_direction_events": cc.MIN_DIRECTION_EVENTS,
            "controls": {"min": cc.MIN_CONTROLS, "max": cc.MAX_CONTROLS,
                         "exclusion_bars": cc.EXCLUSION_BARS},
            "pyramid": {"frac": cc.PYRAMID_FRAC, "span": cc.PYRAMID_SPAN},
            "completion_floor": COMPLETION_FLOOR,
            "precision": {"fpr_halfwidth_max": FPR_HALFWIDTH_MAX,
                          "tpr_halfwidth_max": TPR_HALFWIDTH_MAX},
            "decision_rule": "FOR iff effect>0 and ci95_low>0 and p<=alpha; "
                             "single cell, no Holm, no instrument pooling",
        },
        "dependency": {"exp043_verdict": "READINESS_DELIVERED",
                       "ready_cells": len(cells), "instruments": instruments},
        "replay_cells": [f"{i}-{d}" for i, d in REPLAY_CELLS],
        "holdout_fence": "F01 TRAIN rows only (first 70% of first 70%, file order); "
                         "TEST and global holdout never loaded",
        "anti_overfitting_fence": "real trigger locations used only as exclusions; "
                                  "real event outcomes never computed or read",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    plot_fpr_heatmap(fpr_rows, instruments, PLOTS_DIR / "fpr_per_cell_heatmap.png")
    plot_mde_heatmap(coverage, instruments, PLOTS_DIR / "mde_per_cell_heatmap.png")
    plot_mde_vs_count(coverage, PLOTS_DIR / "mde_vs_event_count.png")
    plot_precision(fpr_rows, coverage, PLOTS_DIR / "calibration_precision.png")
    plot_verdict_summary(coverage, verdict, PLOTS_DIR / "coverage_verdict_summary.png")

    LOGGER.info("verdict: %s; coverage counts: %s; determinism_pass=%s",
                verdict, counts, determinism_pass)
    for r in coverage:
        if r["verdict"] != "COVERED":
            LOGGER.info("%s %s-%s: %s", r["verdict"], r["instrument"], r["domain"], r["reason"])
    LOGGER.info("outputs written under %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
