"""Experiment EXP-046: Phase 012 Entry-Side Gross Screen (7 variants × 37 cells).

Implements the approved analysis plan (analysis-plan.md). For each of the 37
COVERED cells (EXP-044) on the TRAIN stratum only (F01 file-order rows, bound
to the EXP-043 boundary record):

1. aggregate domain bars once per cell, then generate AVWAP bounce events for
   each OAT entry variant (P1 `/ALPHA`, P2 `/MA-DOMAIN`; baseline anchor row);
2. apply the single evaluability convention (H=16 window inside TRAIN), then
   compute direction-signed gross log-bps at H ∈ {4, 8, 16} and the
   regime-cluster bootstrap SE at H=8 (descriptive);
3. apply the mechanical D0 clearance rule against the frozen P4 cost floor
   (CLEAR / NO_CLEAR / BELOW_FLOOR), with per-cell×variant determinism replay;
4. reconcile the baseline row against EXP-043 realized event counts and the
   EXP-045 FH net curve at θ ∈ {4, 8, 16} (full population, forced-clip
   convention) before any non-baseline row is interpreted;
5. report the per-variant mechanical G1 readout (P6 composition threshold).

TRAIN-only; gross-only (the cost floor enters solely as a comparison
constant); 0 TEST reads; the final-30% global holdout is never loaded. G1 is
adjudicated in the Phase 012 checkpoint, not here.

Outputs: ``results/events_summary.csv``, ``results/gross_table.csv``,
``results/clearance_table.csv``, ``results/variant_rollup.csv``,
``results/reconciliation.csv``, ``results/run_metadata.json``, four plots.
"""
from __future__ import annotations

import json
import logging
import math
import sys
import time
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

import variant_screen as vs  # noqa: E402
from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen by scope / analysis plan / D0 — no tuning levers)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-046"
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP043_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-043" / "results"
EXP044_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-044" / "results"
EXP045_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-045" / "results"

DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
MIN_COVERAGE = 0.90
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
EXPECTED_COVERED_CELLS = 37
N_BOOT = 1_000
NS_PER_DAY = 86_400 * 1_000_000_000
RECON_TOL_BPS = 1e-9  # float-precision reconciliation tolerance

# D0 P2 cost model (CONSERVATIVE RT bps, financing bps/day) — frozen, incl.
# the EURUSD 3.0 RT transcription-error correction (identical to EXP-045).
COSTS: dict[str, tuple[float, float]] = {
    "EURUSD": (3.0, 0.6), "USTEC": (5.0, 1.2), "XAUUSD": (6.0, 1.2),
    "BTCUSD": (16.0, 10.0), "GBPUSD": (4.0, 0.8), "USDJPY": (3.6, 0.7),
    "USDCHF": (4.4, 0.7), "USDCAD": (4.4, 0.7), "AUDUSD": (4.0, 0.7),
    "NZDUSD": (5.2, 0.8), "EURJPY": (4.4, 0.8), "GBPJPY": (5.6, 1.0),
    "AUDJPY": (5.2, 0.9), "US500": (3.2, 1.2), "US2000": (6.0, 1.2),
    "DE30": (4.0, 1.2), "JP225": (4.8, 1.2),
}

DE30_DISCLOSURE = (
    "DE30 truncated history: broker history ends 2026-01-16 (~5 months short); "
    "70/30/holdout boundaries derive from its own realized timeline (D0 P8)."
)

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helpers (EXP-043/044/045 loader pattern, unchanged)
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
    """Load exactly the TRAIN 1-minute rows (F01 pattern), bound to EXP-043."""
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


def load_covered_cells() -> tuple[list[tuple[str, str, int]], dict[str, dict[str, Any]]]:
    """Dependency gates: EXP-044 COVERED grid + EXP-043 counts and boundaries."""
    meta44 = json.loads((EXP044_RESULTS / "run_metadata.json").read_text())
    if meta44.get("verdict") != "CALIBRATION_DELIVERED":
        raise RuntimeError(f"EXP-044 gate failed: verdict={meta44.get('verdict')}")
    coverage = pl.read_csv(EXP044_RESULTS / "coverage_map.csv")
    covered = coverage.filter(pl.col("verdict") == "COVERED").sort(["instrument", "domain"])
    if covered.height != EXPECTED_COVERED_CELLS:
        raise RuntimeError(f"COVERED cells {covered.height} != {EXPECTED_COVERED_CELLS}")
    meta43 = json.loads((EXP043_RESULTS / "run_metadata.json").read_text())
    boundaries: dict[str, dict[str, Any]] = meta43["boundaries"]
    power = pl.read_csv(EXP043_RESULTS / "power_statement.csv")
    counts = {(r["instrument"], r["domain"]): int(r["train_events"])
              for r in power.to_dicts()}
    cells = []
    for r in covered.to_dicts():
        key = (r["instrument"], r["domain"])
        if key not in counts:
            raise RuntimeError(f"{key}: missing from EXP-043 power_statement")
        cells.append((r["instrument"], r["domain"], counts[key]))
    missing = {c[0] for c in cells} - set(boundaries)
    if missing:
        raise RuntimeError(f"EXP-043 boundary record missing instruments: {sorted(missing)}")
    return cells, boundaries


def load_exp045_fh_curve() -> dict[tuple[str, str, int], float]:
    """EXP-045 FH net means at θ ∈ {4, 8, 16} (baseline reconciliation anchor)."""
    meta45 = json.loads((EXP045_RESULTS / "run_metadata.json").read_text())
    if meta45.get("verdict") != "TRAINING_DELIVERED":
        raise RuntimeError(f"EXP-045 gate failed: verdict={meta45.get('verdict')}")
    curves = pl.read_csv(EXP045_RESULTS / "score_curves.csv")
    fh = curves.filter(
        (pl.col("family") == "FH") & pl.col("theta").is_in([float(h) for h in vs.HORIZONS])
    )
    return {(r["instrument"], r["domain"], int(r["theta"])): float(r["net_mean_bps"])
            for r in fh.to_dicts()}


# --------------------------------------------------------------------------- #
# Pure computation (per cell × variant)
# --------------------------------------------------------------------------- #
def screen_cell_variant(
    bars: pl.DataFrame,
    instrument: str,
    domain: str,
    variant: vs.Variant,
) -> tuple[dict, dict, list[dict]]:
    """Generate events (twice, determinism), score gross vs floor for one
    cell×variant. Returns (events_summary row, clearance row, gross rows)."""
    domain_cols = bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume")
    kwargs = dict(volume_exponent=variant.alpha, fast_ma=variant.fast_ma,
                  slow_ma=variant.slow_ma)
    result = generate_avwap_events(domain_cols, instrument=instrument,
                                   domain=domain, **kwargs)
    replay = generate_avwap_events(domain_cols, instrument=instrument,
                                   domain=domain, **kwargs)
    # Full-frame equality (every column, incl. trigger_idx/regime_id used by
    # scoring), not just the persisted fingerprint digest.
    determinism_pass = (
        result.events.equals(replay.events)
        and result.regimes.equals(replay.regimes)
    )
    ev = result.events
    n_events = ev.height
    close = bars.get_column("Close").to_numpy().astype(float)

    gross_means: dict[int, float] = {}
    se_binding = float("nan")
    n_evaluable = 0
    n_regimes_evaluable = 0
    if n_events > 0:
        trigger_idx = ev.get_column("trigger_idx").to_numpy()
        direction = ev.get_column("direction").to_numpy()
        regime = ev.get_column("regime_id").to_numpy()
        keep = vs.evaluable_mask(trigger_idx, bars.height)
        n_evaluable = int(keep.sum())
        n_regimes_evaluable = int(np.unique(regime[keep]).size) if n_evaluable else 0
        if n_evaluable > 0:
            gross = vs.gross_at_horizons(close, trigger_idx[keep], direction[keep])
            gross_means = {h: float(g.mean()) for h, g in gross.items()}
            rng = np.random.default_rng(
                seed_for(EXPERIMENT_ID, variant.name, instrument, domain, "se")
            )
            se_binding = vs.cluster_bootstrap_se(
                gross[vs.H_BINDING], direction[keep], regime[keep], rng, N_BOOT
            )

    rt_bps, financing = COSTS[instrument]
    floor = vs.cost_floor_bps(rt_bps, financing, domain)
    verdict, margin = vs.clearance_verdict(
        n_evaluable, gross_means, se_binding, floor, determinism_pass
    )

    disclosure = DE30_DISCLOSURE if instrument == "DE30" else ""
    summary = {
        "variant": variant.name, "instrument": instrument, "domain": domain,
        "disclosure": disclosure, "n_events": n_events,
        "n_evaluable": n_evaluable,
        "n_regimes_evaluable": n_regimes_evaluable,
        "determinism_pass": determinism_pass,
        "events_digest": vs.events_digest(ev) if n_events else "",
    }
    clearance = {
        "variant": variant.name, "axis": variant.axis,
        "instrument": instrument, "domain": domain, "disclosure": disclosure,
        "n_evaluable": n_evaluable, "floor_bps": floor,
        "gross_h8_bps": gross_means.get(vs.H_BINDING),
        "se_h8_bps": se_binding if math.isfinite(se_binding) else None,
        "margin_bps": margin if math.isfinite(margin) else None,
        "verdict": verdict,
    }
    gross_rows = [
        {"variant": variant.name, "instrument": instrument, "domain": domain,
         "disclosure": disclosure, "horizon": h,
         "gross_mean_bps": gross_means.get(h), "n_evaluable": n_evaluable}
        for h in vs.HORIZONS
    ]
    return summary, clearance, gross_rows


def reconcile_baseline(
    bars: pl.DataFrame,
    instrument: str,
    domain: str,
    expected_events: int,
    fh_anchor: dict[tuple[str, str, int], float],
) -> list[dict]:
    """Baseline integrity anchor (blocking): EXP-043 event count + EXP-045 FH
    net curve at θ ∈ {4, 8, 16} under EXP-045's exact conventions (full event
    population, forced exits clipped to the last TRAIN bar, exact fractional
    calendar-day financing)."""
    result = generate_avwap_events(
        bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume"),
        instrument=instrument, domain=domain,
    )
    rows = [{
        "instrument": instrument, "domain": domain, "check": "event_count_exp043",
        "ours": float(result.events.height), "anchor": float(expected_events),
        "abs_diff": float(abs(result.events.height - expected_events)),
        "pass": result.events.height == expected_events,
    }]
    ev = result.events
    close = bars.get_column("Close").to_numpy().astype(float)
    time_ns = bars.get_column("CloseTime").cast(pl.Int64).to_numpy()
    trigger_idx = ev.get_column("trigger_idx").to_numpy()
    direction = ev.get_column("direction").to_numpy()
    last = bars.height - 1
    rt_bps, financing = COSTS[instrument]
    log_close = np.log(close)
    for h in vs.HORIZONS:
        exit_idx = np.minimum(trigger_idx + h, last)
        gross = direction * (log_close[exit_idx] - log_close[trigger_idx]) * 10_000.0
        days = (time_ns[exit_idx] - time_ns[trigger_idx]) / NS_PER_DAY
        net_mean = float((gross - rt_bps - financing * days).mean())
        anchor = fh_anchor.get((instrument, domain, h))
        ok = anchor is not None and abs(net_mean - anchor) <= RECON_TOL_BPS
        rows.append({
            "instrument": instrument, "domain": domain,
            "check": f"fh_net_exp045_h{h}", "ours": net_mean,
            "anchor": anchor, "abs_diff": (abs(net_mean - anchor)
                                           if anchor is not None else None),
            "pass": bool(ok),
        })
    # Internal cross-check of the binding gross/evaluable path (the exact
    # population and code path the clearance rule reads): the screen-side
    # `vs.evaluable_mask` + `vs.gross_at_horizons` means must match an
    # independently indexed recomputation on the same baseline events.
    keep = vs.evaluable_mask(trigger_idx, bars.height)
    if keep.any():
        screen_gross = vs.gross_at_horizons(close, trigger_idx[keep], direction[keep])
        for h in vs.HORIZONS:
            ref = float((direction[keep] * (
                log_close[trigger_idx[keep] + h] - log_close[trigger_idx[keep]]
            ) * 10_000.0).mean())
            ours = float(screen_gross[h].mean())
            rows.append({
                "instrument": instrument, "domain": domain,
                "check": f"gross_evaluable_xcheck_h{h}", "ours": ours,
                "anchor": ref, "abs_diff": abs(ours - ref),
                "pass": abs(ours - ref) <= RECON_TOL_BPS,
            })
    return rows


# --------------------------------------------------------------------------- #
# Plotting (inputs: bounded summary rows only)
# --------------------------------------------------------------------------- #
def _margin_heatmap(clearance: list[dict], axis: str, path: Path) -> None:
    """Margin heatmap (variants of one axis × 37 cells); CLEAR cells outlined."""
    rows = [c for c in clearance if c["axis"] in (axis, "baseline")]
    variants = [v.name for v in vs.VARIANTS if v.axis in (axis, "baseline")]
    cells = sorted({(c["instrument"], c["domain"]) for c in rows})
    grid = np.full((len(cells), len(variants)), np.nan)
    verdicts = {}
    for c in rows:
        i = cells.index((c["instrument"], c["domain"]))
        j = variants.index(c["variant"])
        if c["margin_bps"] is not None:
            grid[i, j] = c["margin_bps"]
        verdicts[(i, j)] = c["verdict"]
    fig, ax = plt.subplots(figsize=(1.6 * len(variants) + 3, 0.28 * len(cells) + 2))
    vmax = np.nanmax(np.abs(grid)) if np.isfinite(grid).any() else 1.0
    im = ax.imshow(grid, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax)
    for (i, j), verdict in verdicts.items():
        if verdict == "CLEAR":
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       edgecolor="black", lw=1.6))
        elif verdict == "BELOW_FLOOR":
            ax.text(j, i, "BF", ha="center", va="center", fontsize=5, alpha=0.6)
    ax.set_xticks(range(len(variants)), variants, rotation=30, fontsize=7)
    ax.set_yticks(range(len(cells)), [f"{i}-{d}" for i, d in cells], fontsize=5.5)
    fig.colorbar(im, ax=ax, label="margin = gross(H=8) − floor − 1×SE (bps)")
    ax.set_title(f"EXP-046 clearance margins — /{axis.upper()} axis "
                 "(black outline = CLEAR, BF = below event floor)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_horizon_robustness(gross_rows: list[dict], clearance: list[dict],
                            path: Path) -> None:
    """gross(H=4) vs gross(H=16) for cells passing the H=8 margin leg."""
    margin_pass = {(c["variant"], c["instrument"], c["domain"])
                   for c in clearance
                   if c["margin_bps"] is not None and c["margin_bps"] >= 0.0}
    by_key: dict[tuple, dict[int, float]] = {}
    for g in gross_rows:
        key = (g["variant"], g["instrument"], g["domain"])
        if key in margin_pass and g["gross_mean_bps"] is not None:
            by_key.setdefault(key, {})[g["horizon"]] = g["gross_mean_bps"]
    fig, ax = plt.subplots(figsize=(7, 6))
    for (variant, inst, dom), gm in by_key.items():
        if 4 in gm and 16 in gm:
            ax.scatter(gm[4], gm[16], s=18, alpha=0.8)
            ax.annotate(f"{variant}:{inst}-{dom}", (gm[4], gm[16]), fontsize=5)
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("gross(H=4) (bps)")
    ax.set_ylabel("gross(H=16) (bps)")
    ax.set_title("EXP-046 sign robustness for margin-passing cells\n"
                 "(clearance requires the upper-right quadrant)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_event_counts(summaries: list[dict], path: Path) -> None:
    """Evaluable-event map (variants × cells) with the 30-event floor marked."""
    variants = [v.name for v in vs.VARIANTS]
    cells = sorted({(s["instrument"], s["domain"]) for s in summaries})
    grid = np.zeros((len(cells), len(variants)))
    for s in summaries:
        grid[cells.index((s["instrument"], s["domain"])),
             variants.index(s["variant"])] = s["n_evaluable"]
    fig, ax = plt.subplots(figsize=(1.4 * len(variants) + 3, 0.28 * len(cells) + 2))
    im = ax.imshow(grid, aspect="auto", cmap="viridis")
    for i in range(len(cells)):
        for j in range(len(variants)):
            if grid[i, j] < vs.EVENT_FLOOR:
                ax.text(j, i, int(grid[i, j]), ha="center", va="center",
                        fontsize=5, color="red")
    ax.set_xticks(range(len(variants)), variants, rotation=30, fontsize=7)
    ax.set_yticks(range(len(cells)), [f"{i}-{d}" for i, d in cells], fontsize=5.5)
    fig.colorbar(im, ax=ax, label="evaluable TRAIN events")
    ax.set_title(f"EXP-046 evaluable events (red = below the {vs.EVENT_FLOOR}-event floor)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the 7-variant × 37-cell entry-side gross screen (TRAIN-only)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    cells, boundaries = load_covered_cells()
    fh_anchor = load_exp045_fh_curve()
    LOGGER.info("dependency gates PASS: %d COVERED cells; EXP-045 FH anchor loaded",
                len(cells))

    summaries: list[dict] = []
    clearance: list[dict] = []
    gross_rows: list[dict] = []
    recon_rows: list[dict] = []

    by_instrument: dict[str, list[tuple[str, str, int]]] = {}
    for spec in cells:
        by_instrument.setdefault(spec[0], []).append(spec)

    total_units = len(cells) * len(vs.VARIANTS)
    with tqdm(total=total_units, desc=f"{EXPERIMENT_ID} gross screen") as progress:
        for instrument, specs in by_instrument.items():
            frame_1m = load_train_frame(instrument, boundaries[instrument])
            for inst, domain, expected_events in specs:
                bars = aggregate_ohlc(frame_1m, period_minutes=DOMAINS[domain],
                                      min_coverage=MIN_COVERAGE)
                recon_rows.extend(
                    reconcile_baseline(bars, inst, domain, expected_events, fh_anchor)
                )
                for variant in vs.VARIANTS:
                    progress.set_postfix_str(f"{inst}-{domain} {variant.name}")
                    summary, clear_row, g_rows = screen_cell_variant(
                        bars, inst, domain, variant
                    )
                    summaries.append(summary)
                    clearance.append(clear_row)
                    gross_rows.extend(g_rows)
                    progress.update(1)
                del bars
            del frame_1m

    reconciliation_pass = all(r["pass"] for r in recon_rows)
    determinism_all = all(s["determinism_pass"] for s in summaries)
    integrity_pass = reconciliation_pass and determinism_all
    rollup = vs.variant_rollup(clearance)
    # A failed-integrity grid is not interpretable: suppress the G1 readout
    # entirely (analysis-plan interpretation guide — fix and rerun).
    viable = [r for r in rollup if r["composition_met"]] if integrity_pass else []
    g1_readout = (
        ("ENTRY_GROSS_VIABLE" if viable else "ENTRY_GROSS_FLAT")
        if integrity_pass else "INCONCLUSIVE_INTEGRITY_FAIL"
    )
    verdict = "SCREEN_DELIVERED" if integrity_pass else "INTEGRITY_FAIL"

    pl.DataFrame(summaries).write_csv(RESULTS_DIR / "events_summary.csv")
    pl.DataFrame(gross_rows).write_csv(RESULTS_DIR / "gross_table.csv")
    pl.DataFrame(clearance).write_csv(RESULTS_DIR / "clearance_table.csv")
    pl.DataFrame(rollup).write_csv(RESULTS_DIR / "variant_rollup.csv")
    pl.DataFrame(recon_rows).write_csv(RESULTS_DIR / "reconciliation.csv")

    metadata = {
        "experiment": EXPERIMENT_ID,
        "verdict": verdict,
        "g1_mechanical_readout": g1_readout,
        "g1_note": "G1 is adjudicated in the Phase 012 checkpoint "
                   "G1-gate-review.md; this readout is the mechanical count.",
        "reconciliation_pass": reconciliation_pass,
        "determinism_all_pass": determinism_all,
        "variants_meeting_composition": [r["variant"] for r in viable],
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "method": {
            "variants": [v.name for v in vs.VARIANTS],
            "horizons": list(vs.HORIZONS),
            "binding_horizon": vs.H_BINDING,
            "margin_rule": "gross(H=8) >= floor + 1*SE AND gross(4) > 0 "
                           "AND gross(16) > 0 (D0 P5)",
            "floor_rule": "RT + financing * (8*hours/24) (D0 P4)",
            "event_floor": vs.EVENT_FLOOR,
            "composition_threshold": f">= {vs.G1_MIN_CELLS} cells over "
                                     f">= {vs.G1_MIN_INSTRUMENTS} instruments (D0 P6)",
            "evaluability": "trigger + H_MAX(16) within TRAIN (one population "
                            "per cell x variant across horizons)",
            "n_bootstrap": N_BOOT,
            "cost_model": "D0/Phase-011 P2 CONSERVATIVE (comparison floor only; "
                          "no net columns anywhere)",
            "floor_disclosure": "days(8,d) is a frozen calendar-day "
                                "approximation (P4); it understates wall-clock "
                                "financing for holds spanning weekends/closures "
                                "(largest for 4h index cells) — any clearing "
                                "index cell carries this caveat at G1.",
            "se_disclosure": "regime-cluster SE preserves within-regime "
                             "dependence only; overlap correlation between "
                             "short adjacent regimes (< H=8 bars) is not "
                             "captured — n_regimes_evaluable per cell is "
                             "reported in events_summary.csv for this reading.",
        },
        "dependency": {
            "exp044_covered_cells": len(cells),
            "exp045_anchor": "FH net at theta in {4,8,16}, full population, "
                             "forced-clip convention",
        },
        "disclosures": {"DE30": DE30_DISCLOSURE},
        "holdout_fence": "F01 TRAIN rows only (first 70% of first 70%, file "
                         "order); TEST and global holdout never loaded",
        "test_reads": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    _margin_heatmap(clearance, "alpha", PLOTS_DIR / "margin_heatmap_alpha.png")
    _margin_heatmap(clearance, "ma", PLOTS_DIR / "margin_heatmap_ma.png")
    plot_horizon_robustness(gross_rows, clearance,
                            PLOTS_DIR / "horizon_robustness.png")
    plot_event_counts(summaries, PLOTS_DIR / "event_count_map.png")

    LOGGER.info("verdict: %s; mechanical G1 readout: %s; variants meeting "
                "composition: %s; reconciliation_pass=%s; determinism=%s",
                verdict, g1_readout,
                [r["variant"] for r in viable] or "none",
                reconciliation_pass, determinism_all)
    LOGGER.info("outputs written under %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
