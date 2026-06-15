"""EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami).

`CF-HA-HARAMI-001` / HYP-001. TRAIN-only, gross, 0 candidate slots, 0 TEST
reads. For each of the 102 cells (17 instruments x {5m, 15m, 30m, 1h, 2h, 4h})
this script, on the TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by the F01 file-order prefix
   convention (no full-file sort/collect; TEST and the final-30% global holdout
   are never read);
2. aggregates the domain (5m strict; 15m/30m/1h/2h/4h at min_coverage=0.90),
   fences every domain bar to `CloseTime <= train_end_ts`, and applies the
   frozen dropped-window-fraction gate (<0.10 clean / 0.10-0.25 flagged /
   >0.25 COVERAGE_EXCLUDED);
3. computes two independent primitives — the streaming Wilder-ATR ZigZag
   substrate (`xen.zigzag`, real bars) and the HA harami detector
   (`xen.ha_harami`, HA candles from `xen.heiken_ashi_generator`);
4. runs the full ZigZag and HA-harami invariant batteries (keyed by invariant
   name), a determinism replay (second full pass, exact frame equality), and
   the descriptive move/event-rate and /BARCFG coverage measurements with the
   predeclared denominators and zero-baseline handling;
5. adjudicates per-cell READY and the mechanical SUBSTRATE_REFUTED rule.

Outputs (results/): per_cell_checks.parquet, readiness_map.csv,
move_event_rates.csv, barcfg_coverage.csv, run_metadata.json. Plots (plots/):
readiness heatmap, ZigZag move-rate heatmap, harami event-rate heatmap, /BARCFG
coverage composition by domain. No statistical test; no outcome/return metric.
"""
from __future__ import annotations

import json
import logging
import sys
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

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.zigzag import generate_zigzag  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 frozen; readiness conventions from EXP-043)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-048"
INSTRUMENTS: list[str] = [
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500",
    "US2000", "DE30", "JP225",
]
# domain name -> (period_minutes, min_coverage). 5m strict; rest at 0.90.
DOMAINS: dict[str, tuple[int, float | None]] = {
    "5m": (5, None), "15m": (15, 0.90), "30m": (30, 0.90),
    "1h": (60, 0.90), "2h": (120, 0.90), "4h": (240, 0.90),
}
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
ATR_PERIOD = 14            # P1: Wilder ATR period
ATR_MULT = 1.0             # P1: ATR_MULT
DROP_CLEAN = 0.10          # < clean
DROP_GATE = 0.25           # > -> COVERAGE_EXCLUDED (gated domains only)
REPORTING_FLOOR = 30       # descriptive event-count floor (not a READY criterion)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16 (~5 months short "
    "of the rest); counts/rates derive from its own realized timeline and are "
    "not span-comparable to full-history instruments (VAL-003 disclosure)."
)
BARCFG_LABELS: dict[tuple[int, int], str] = {
    (1, 1): "UP_UP", (1, -1): "UP_DN", (-1, 1): "DN_UP", (-1, -1): "DN_DN",
}
# Readiness status -> integer code (for the heatmap).
STATUS_CODES: dict[str, int] = {
    "READY": 0, "READY_FLAGGED": 1, "CONSTRUCTED_EMPTY": 2,
    "COVERAGE_EXCLUDED": 3, "NOT_READY_CONSTRUCTION": 4,
    "NOT_READY_INVARIANT": 5, "NOT_READY_DETERMINISM": 6,
}
STATUS_COLORS: list[str] = [
    "#1a9850", "#a6d96a", "#cccccc", "#fee08b",
    "#f46d43", "#d73027", "#7b3294",
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
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix.

    Reads only Parquet metadata (row count) and the first ``train_rows``
    file-order rows; never sorts/collects the full file, never reads TEST or
    the final-30% global holdout. Asserts the collected slice is chronological.
    """
    path = find_source_file(instrument)
    total_rows = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    train = (
        pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()
    )
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    train_end_epoch = int(train.get_column("CloseTime").dt.epoch("s")[-1])
    meta = {
        "source_file": path.name,
        "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows,
        "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": train_end_epoch,
    }
    return train, meta


# --------------------------------------------------------------------------- #
# Pure computation — construction, primitives, invariants, rates
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> tuple[pl.DataFrame, float]:
    """Aggregate one domain, fence to train_end, return (bars, dropped_fraction).

    Dropped fraction = (candidate windows - retained) / candidate windows on
    the TRAIN slice; a degenerate cell with zero candidate windows reports 1.0
    only if some candidates exist, else 0.0 (guarded against 0/0).
    """
    period_s = period_minutes * 60
    candidate = int(
        train_1m.select(
            ((pl.col("CloseTime").dt.epoch("s") - 1) // period_s).n_unique()
        ).item()
    )
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    bars = bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)
    retained = bars.height
    dropped_fraction = 0.0 if candidate == 0 else (candidate - retained) / candidate
    return bars, float(dropped_fraction)


def check_construction(bars: pl.DataFrame, period_minutes: int) -> dict[str, int]:
    """Count construction-integrity violations on a domain frame."""
    period_s = period_minutes * 60
    ct = bars.get_column("CloseTime").dt.epoch("s")
    return {
        "ohlc_high": int(bars.filter(
            pl.col("High") < pl.max_horizontal("Open", "Close")).height),
        "ohlc_low": int(bars.filter(
            pl.col("Low") > pl.min_horizontal("Open", "Close")).height),
        "closetime_monotonic": int((ct.diff().drop_nulls() <= 0).sum()),
        "grid_alignment": int((ct % period_s != 0).sum()),
    }


def zigzag_invariants(
    moves: pl.DataFrame, train_end_epoch: int
) -> dict[str, int]:
    """Count ZigZag invariant violations, keyed by invariant name."""
    if moves.is_empty():
        return {k: 0 for k in (
            "zz_alternation", "zz_confirm_after_pivot", "zz_confirm_within_train",
            "zz_threshold_breach", "zz_confirm_monotonic", "zz_null")}
    direction = moves.get_column("Direction")
    confirm = moves.get_column("ConfirmTime").dt.epoch("s")
    end = moves.get_column("EndTime").dt.epoch("s")
    up = moves.filter(pl.col("Direction") == 1)
    dn = moves.filter(pl.col("Direction") == -1)
    breach = (
        int(up.filter(pl.col("ConfirmClose") >= pl.col("ThresholdAtConfirm")).height)
        + int(dn.filter(pl.col("ConfirmClose") <= pl.col("ThresholdAtConfirm")).height)
    )
    required = ["StartTime", "EndTime", "ConfirmTime", "Direction", "StartPrice",
                "EndPrice", "ConfirmClose", "ATRAtConfirm", "ThresholdAtConfirm"]
    nulls = int(moves.select(
        pl.any_horizontal(pl.col(required).is_null())).to_series().sum())
    return {
        "zz_alternation": int((direction.diff().drop_nulls() == 0).sum()),
        "zz_confirm_after_pivot": int((confirm <= end).sum()),
        "zz_confirm_within_train": int((confirm > train_end_epoch).sum()),
        "zz_threshold_breach": breach,
        "zz_confirm_monotonic": int((confirm.diff().drop_nulls() <= 0).sum()),
        "zz_null": nulls,
    }


def harami_invariants(
    events: pl.DataFrame, train_end_epoch: int
) -> dict[str, int]:
    """Count HA-harami invariant violations, keyed by invariant name."""
    if events.is_empty():
        return {k: 0 for k in (
            "ha_predicate_agreement", "ha_adjacent", "ha_within_train",
            "ha_monotonic", "ha_body_containment", "ha_null")}
    ha1 = events.get_column("HA1Time").dt.epoch("s")
    ha0 = events.get_column("HA0Time").dt.epoch("s")
    required = ["HA1Time", "HA0Time", "HA1Direction", "HA0Direction",
                "PrevBodyMin", "PrevBodyMax", "BodyMin", "BodyMax", "HAClose0"]
    nulls = int(events.select(
        pl.any_horizontal(pl.col(required).is_null())).to_series().sum())
    containment = int(events.filter(
        ~((pl.col("PrevBodyMax") > pl.col("BodyMax"))
          & (pl.col("PrevBodyMin") < pl.col("BodyMin")))).height)
    return {
        "ha_predicate_agreement": int((~events.get_column("ReducedOK")).sum()),
        "ha_adjacent": int((ha1 >= ha0).sum()),
        "ha_within_train": int((ha0 > train_end_epoch).sum()),
        "ha_monotonic": int((ha0.diff().drop_nulls() <= 0).sum()),
        "ha_body_containment": containment,
        "ha_null": nulls,
    }


def barcfg_counts(events: pl.DataFrame) -> dict[str, int]:
    """Count harami events per /BARCFG configuration."""
    counts = {label: 0 for label in BARCFG_LABELS.values()}
    if events.is_empty():
        return counts
    grouped = (
        events.group_by("HA1Direction", "HA0Direction").len().to_dicts()
    )
    for row in grouped:
        key = (int(row["HA1Direction"]), int(row["HA0Direction"]))
        if key in BARCFG_LABELS:
            counts[BARCFG_LABELS[key]] = int(row["len"])
    return counts


def primitives_pass(bars: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Run both primitives once and return (zigzag_moves, harami_events)."""
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    ha = generate_heiken_ashi(bars)
    events = detect_ha_harami(ha)
    return moves, events


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def process_cell(
    instrument: str, domain: str, train_1m: pl.DataFrame, train_end_epoch: int,
) -> dict[str, Any]:
    """Process one instrument x domain cell; return its full check record."""
    period_minutes, min_coverage = DOMAINS[domain]
    bars, dropped = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = bars.height
    gated = min_coverage is not None

    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain,
        "train_domain_bars": n_bars, "dropped_fraction": dropped,
    }

    if n_bars < ATR_PERIOD:                       # empty-construction guard
        rec.update(_empty_cell_record())
        return rec

    construction = check_construction(bars, period_minutes)
    construction_clean = sum(construction.values()) == 0
    # Dropped-fraction classification applies to coverage-mode domains only
    # (15m/30m/1h/2h/4h); 5m strict carries no dropped-fraction gate (scope §1).
    coverage_excluded = gated and dropped > DROP_GATE
    flagged = gated and (DROP_CLEAN <= dropped <= DROP_GATE)

    # Determinism replay: re-aggregate the domain and re-run both primitives, then
    # compare the domain bars, move table, and event table frame-identical (scope §4).
    moves, events = primitives_pass(bars)
    bars2, _ = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    moves2, events2 = primitives_pass(bars2)
    determinism_ok = (
        bars.equals(bars2) and moves.equals(moves2) and events.equals(events2)
    )

    zz_inv = zigzag_invariants(moves, train_end_epoch)
    ha_inv = harami_invariants(events, train_end_epoch)
    invariants_clean = sum(zz_inv.values()) + sum(ha_inv.values()) == 0

    n_moves, n_harami = moves.height, events.height
    cfg = barcfg_counts(events)

    rec.update({
        "n_moves": n_moves, "n_harami": n_harami,
        "move_rate_per_1000": n_moves / n_bars * 1000.0,
        "harami_rate_per_1000": n_harami / n_bars * 1000.0,
        "below_move_floor": n_moves < REPORTING_FLOOR,
        "below_harami_floor": n_harami < REPORTING_FLOOR,
        "construction_clean": construction_clean,
        "coverage_excluded": coverage_excluded,
        "flagged_disclosure": flagged,
        "determinism_ok": determinism_ok,
        "invariants_clean": invariants_clean,
        **{f"cfg_{label}": cfg[label] for label in BARCFG_LABELS.values()},
        **construction, **zz_inv, **ha_inv,
    })
    rec["status"] = adjudicate(rec)
    rec["status_code"] = STATUS_CODES[rec["status"]]
    return rec


def _empty_cell_record() -> dict[str, Any]:
    """Record fields for a CONSTRUCTED_EMPTY cell (TRAIN bars < ATR warmup).

    All detail keys are present (0/clean) so the per-cell record schema is
    uniform across every status; nothing is checked because there is no move,
    event, or trend state to check. ``CONSTRUCTED_EMPTY`` trumps coverage
    exclusion, so the coverage diagnostics stay ``False`` to remain consistent
    with the adjudicated status.
    """
    base: dict[str, Any] = {
        "n_moves": 0, "n_harami": 0,
        "move_rate_per_1000": 0.0, "harami_rate_per_1000": 0.0,
        "below_move_floor": True, "below_harami_floor": True,
        "construction_clean": True,
        "coverage_excluded": False,
        "flagged_disclosure": False,
        "determinism_ok": True, "invariants_clean": True,
        "ohlc_high": 0, "ohlc_low": 0, "closetime_monotonic": 0, "grid_alignment": 0,
        "status": "CONSTRUCTED_EMPTY", "status_code": STATUS_CODES["CONSTRUCTED_EMPTY"],
    }
    for label in BARCFG_LABELS.values():
        base[f"cfg_{label}"] = None                 # non-reportable: 0 harami
    for name in INVARIANT_NAMES:
        base[name] = 0
    return base


def adjudicate(rec: dict[str, Any]) -> str:
    """Mechanical per-cell READY adjudication."""
    if rec["coverage_excluded"]:
        return "COVERAGE_EXCLUDED"
    if not rec["construction_clean"]:
        return "NOT_READY_CONSTRUCTION"
    if not rec["invariants_clean"]:
        return "NOT_READY_INVARIANT"
    if not rec["determinism_ok"]:
        return "NOT_READY_DETERMINISM"
    return "READY_FLAGGED" if rec["flagged_disclosure"] else "READY"


# --------------------------------------------------------------------------- #
# Verdict
# --------------------------------------------------------------------------- #
INVARIANT_NAMES: list[str] = [
    "zz_alternation", "zz_confirm_after_pivot", "zz_confirm_within_train",
    "zz_threshold_breach", "zz_confirm_monotonic", "zz_null",
    "ha_predicate_agreement", "ha_adjacent", "ha_within_train",
    "ha_monotonic", "ha_body_containment", "ha_null",
]


def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the SUBSTRATE_REFUTED rule: any non-determinism, or the same named
    invariant violated on >= 3 instruments."""
    non_det = [f"{r['instrument']}-{r['domain']}" for r in records
               if not r.get("determinism_ok", True)]
    systematic: dict[str, int] = {}
    for name in INVARIANT_NAMES:
        instruments = {r["instrument"] for r in records if r.get(name, 0)}
        if len(instruments) >= 3:
            systematic[name] = len(instruments)
    refuted = bool(non_det) or bool(systematic)
    return {
        "verdict": "SUBSTRATE_REFUTED" if refuted else "READINESS_DELIVERED",
        "non_deterministic_cells": non_det,
        "systematic_invariant_failures": systematic,
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded; built from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _pivot(df: pl.DataFrame, value: str) -> tuple[np.ndarray, list[str]]:
    """Build an instrument x domain matrix (row=instrument order) for heatmaps."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r[value] for r in df.to_dicts()}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            val = lookup.get((inst, dom))
            if val is not None:
                matrix[i, j] = float(val)
    return matrix, domains


def plot_status_heatmap(df: pl.DataFrame, save_path: Path) -> None:
    """Heatmap of per-cell readiness status (the SUBSTRATE_REFUTED visual)."""
    matrix, domains = _pivot(df, "status_code")
    cmap = ListedColormap(STATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(STATUS_COLORS) + 0.5), cmap.N)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(domains)), domains)
    ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS)
    ax.set_title(f"{EXPERIMENT_ID}: per-cell readiness status (102 cells)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=STATUS_COLORS[c])
               for c in STATUS_CODES.values()]
    ax.legend(handles, list(STATUS_CODES.keys()), bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_rate_heatmap(df: pl.DataFrame, value: str, title: str, save_path: Path) -> None:
    """Heatmap of a per-cell rate (moves or harami per 1,000 bars)."""
    matrix, domains = _pivot(df, value)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", annot=True, fmt=".0f",
                xticklabels=domains, yticklabels=INSTRUMENTS,
                cbar_kws={"label": title}, annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: {title}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_barcfg_composition(df: pl.DataFrame, save_path: Path) -> None:
    """Stacked /BARCFG composition by domain (event-pooled, harami-bearing cells).

    Events are pooled within each domain (sum config_k over cells / sum total
    harami over cells) so that event-sparse cells do not over-weight noisy
    fractions; the per-domain pooled event count is annotated so sparse domains
    are visually distinguishable from dense ones.
    """
    labels = list(BARCFG_LABELS.values())
    domains = list(DOMAINS.keys())
    fracs = np.zeros((len(domains), len(labels)))
    pooled_n: list[int] = []
    for j, dom in enumerate(domains):
        cells = df.filter((pl.col("domain") == dom) & (pl.col("n_harami") > 0))
        total = int(cells.get_column("n_harami").sum()) if not cells.is_empty() else 0
        pooled_n.append(total)
        if total == 0:
            continue
        sums = np.array([int(cells.get_column(f"cfg_{lab}").sum()) for lab in labels])
        fracs[j] = sums / total
    fig, ax = plt.subplots(figsize=(8, 5))
    bottom = np.zeros(len(domains))
    for k, lab in enumerate(labels):
        ax.bar(domains, fracs[:, k], bottom=bottom, label=lab)
        bottom += fracs[:, k]
    for j, total in enumerate(pooled_n):
        ax.text(j, 1.01, f"n={total:,}", ha="center", va="bottom", fontsize=7)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("pooled event fraction (harami-bearing cells)")
    ax.set_title(f"{EXPERIMENT_ID}: /BARCFG coverage composition by domain")
    ax.legend(title="(HA_1, HA_0)", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Run all 102 cells and write artifacts. Returns run metadata."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    for instrument in tqdm(INSTRUMENTS, desc="instruments"):
        train_1m, meta = load_train_1m(instrument)
        instrument_meta[instrument] = meta
        for domain in DOMAINS:
            records.append(process_cell(
                instrument, domain, train_1m, meta["train_end_epoch_s"]))
        del train_1m

    df = pl.DataFrame(records)
    verdict = compute_verdict(records)
    write_outputs(df, verdict, instrument_meta)
    make_plots(df)
    return _summarize(df, verdict)


def write_outputs(
    df: pl.DataFrame, verdict: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist per-cell parquet, the three CSV tables, and run_metadata.json."""
    df.write_parquet(RESULTS_DIR / "per_cell_checks.parquet")
    df.select(
        "instrument", "domain", "status", "train_domain_bars",
        "dropped_fraction", "construction_clean", "invariants_clean",
        "determinism_ok", "coverage_excluded", "flagged_disclosure",
    ).write_csv(RESULTS_DIR / "readiness_map.csv")
    df.select(
        "instrument", "domain", "train_domain_bars", "n_moves",
        "move_rate_per_1000", "n_harami", "harami_rate_per_1000",
        "below_move_floor", "below_harami_floor",
    ).write_csv(RESULTS_DIR / "move_event_rates.csv")
    cfg_cols = [f"cfg_{lab}" for lab in BARCFG_LABELS.values()]
    df.select("instrument", "domain", "n_harami", *cfg_cols).write_csv(
        RESULTS_DIR / "barcfg_coverage.csv")

    status_counts = {s: int((df.get_column("status") == s).sum())
                     for s in STATUS_CODES}
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-A", "hypothesis": "HYP-001", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "params": {"atr_period": ATR_PERIOD, "atr_mult": ATR_MULT,
                   "atr_estimator": "Wilder", "analysis_fraction": ANALYSIS_FRACTION,
                   "train_fraction": TRAIN_FRACTION},
        "domains": {k: {"period_minutes": v[0], "min_coverage": v[1]}
                    for k, v in DOMAINS.items()},
        "dropped_fraction_thresholds": {"clean_below": DROP_CLEAN, "exclude_above": DROP_GATE},
        "reporting_floor": REPORTING_FLOOR,
        "denominators": {
            "move_rate": "confirmed moves / 1000 TRAIN domain bars",
            "harami_rate": "harami events / 1000 HA candles (= TRAIN domain bars)",
            "barcfg_coverage": "config events / total harami events; null when 0 harami",
        },
        "n_cells": df.height,
        "status_counts": status_counts,
        "verdict": verdict,
        "de30_disclosure": DE30_DISCLOSURE,
        "instrument_meta": instrument_meta,
        "holdout_fence": (
            "Only Parquet metadata + first train_rows file-order rows read per "
            "instrument; full file never sorted/collected; every emitted domain "
            "bar/move/event fenced to CloseTime <= train_end_ts; TEST and final-30% "
            "holdout never read."
        ),
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def make_plots(df: pl.DataFrame) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    plot_status_heatmap(df, PLOTS_DIR / "readiness_status_heatmap.png")
    plot_rate_heatmap(df, "move_rate_per_1000",
                      "ZigZag moves per 1,000 domain bars",
                      PLOTS_DIR / "zigzag_move_rate_heatmap.png")
    plot_rate_heatmap(df, "harami_rate_per_1000",
                      "HA harami events per 1,000 candles",
                      PLOTS_DIR / "harami_event_rate_heatmap.png")
    plot_barcfg_composition(df, PLOTS_DIR / "barcfg_composition_by_domain.png")


def _summarize(df: pl.DataFrame, verdict: dict[str, Any]) -> dict[str, Any]:
    """Build the concise stdout summary."""
    return {
        "verdict": verdict["verdict"],
        "status_counts": {s: int((df.get_column("status") == s).sum())
                          for s in STATUS_CODES},
        "non_deterministic_cells": verdict["non_deterministic_cells"],
        "systematic_invariant_failures": verdict["systematic_invariant_failures"],
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("status counts: %s", json.dumps(summary["status_counts"]))
    if summary["non_deterministic_cells"]:
        LOGGER.info("NON-DETERMINISTIC: %s", summary["non_deterministic_cells"])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
