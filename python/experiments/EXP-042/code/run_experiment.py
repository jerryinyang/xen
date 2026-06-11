"""Experiment EXP-042: Track A0 Band-Selection Scan (TRAIN-only, descriptive).

Phase 011 (`2026-06-11-011-per-instrument-foundation`, design §5.2; D0 P3/P7).
Scans the AVWAP entry band multiplier b ∈ {1.0, 1.5, 2.0, 2.5, 3.0} over
17 instruments × {1h, 2h, 4h} on the TRAIN stratum only (first 70% of the
first-70% analysis slice, R1.3 1-minute-row `train_end_ts` boundary), using
the operator-ratified arm-at-adverse-band entry rule
(`xen.avwap.generate_avwap_events(band_multiplier=b, arm_at_adverse_band=True)`).

Per band×cell: event count and mean gross forward return (bps, direction-signed
log return on real domain Close) at H ∈ {4, 8, 16} domain bars. Selection is
the frozen §5.2 rank rule: within-cell rank at H=8 (floor: n ≥ 30 at the H=8
denominator, failing bands imputed worst rank), best median rank across cells,
wider-band tie-break. 0 statistical tests; no cost overlay; no CIs.

Holdout discipline: only the first TRAIN-row count of each 1-minute file is
ever collected (lazy slice before collect); TEST and the final-30% global
holdout are never materialized. TEST row counts used by the power statement
come from boundary arithmetic only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import sys
from dataclasses import dataclass
from pathlib import Path

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
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (all frozen by scope / D0 predeclarations — no tuning levers)
# --------------------------------------------------------------------------- #
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

INSTRUMENTS: tuple[str, ...] = (
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD",
    "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY",
    "US500", "US2000", "DE30", "JP225",
)
DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
BANDS: tuple[float, ...] = (1.0, 1.5, 2.0, 2.5, 3.0)
HORIZONS: tuple[int, ...] = (4, 8, 16)
BINDING_HORIZON = 8          # middle horizon — the only selection input (P3)
EVENT_FLOOR = 30             # min events at the H=8 denominator (P3)
WORST_RANK = float(len(BANDS))
MIN_COVERAGE = 0.90          # P7 — frozen 1h/4h convention extended to 2h
ANALYSIS_FRACTION = 0.7      # first 70% = analysis slice (holdout fence)
TRAIN_FRACTION = 0.7         # first 70% of analysis slice = TRAIN (R1.3)
# Pre-sliced derivative exports that must never match the source-file glob.
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

LOGGER = logging.getLogger("EXP-042")


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TrainSlice:
    """One instrument's TRAIN-only 1-minute slice plus boundary metadata."""

    instrument: str
    source_file: str
    total_rows_1m: int
    analysis_rows_1m: int
    train_rows_1m: int
    test_rows_1m: int
    train_end_ts: str
    frame_1m: pl.DataFrame


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


def load_train_slice(instrument: str) -> TrainSlice:
    """Load exactly the TRAIN 1-minute rows for one instrument (R1.3 boundary).

    Boundary arithmetic on chronologically ordered 1-minute rows:
    ``analysis = floor(0.7 * total)``; ``train = floor(0.7 * analysis)``.
    Only the first ``train`` file-order rows are collected; TEST/holdout rows
    never enter the scan engine (no full-file sort — source chronological
    order was validated by VAL-001 rev. 3 / VAL-003 and is re-asserted on the
    collected TRAIN slice; the total row count comes from Parquet metadata).
    The TEST row count is arithmetic only.
    """
    path = find_source_file(instrument)
    lazy = pl.scan_parquet(path).select(
        "Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"
    )
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(math.floor(ANALYSIS_FRACTION * total))
    train_rows = int(math.floor(TRAIN_FRACTION * analysis_rows))
    test_rows = analysis_rows - train_rows
    frame = lazy.head(train_rows).collect()
    if frame.height != train_rows:
        raise RuntimeError(f"{instrument}: collected {frame.height} != train_rows {train_rows}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(
            f"{instrument}: TRAIN slice not chronologically sorted — source file "
            f"order violates the VAL-validated premise; refusing to proceed."
        )
    train_end_ts = str(frame.get_column("CloseTime").max())
    return TrainSlice(
        instrument=instrument,
        source_file=path.name,
        total_rows_1m=total,
        analysis_rows_1m=analysis_rows,
        train_rows_1m=train_rows,
        test_rows_1m=test_rows,
        train_end_ts=train_end_ts,
        frame_1m=frame,
    )


# --------------------------------------------------------------------------- #
# Pure computation
# --------------------------------------------------------------------------- #
def forward_return_stats(
    close: np.ndarray,
    trigger_idx: np.ndarray,
    direction: np.ndarray,
) -> dict[int, tuple[int, float]]:
    """Per-horizon (denominator, mean gross bps) for one band×cell event set.

    Forward return = ``10000 * direction * ln(close[t + H] / close[t])`` on real
    domain Close. Events whose full H-bar window spills past the last TRAIN
    domain bar are excluded from that horizon's denominator (no spill past
    ``train_end_ts``). Means are reported only when the denominator is >= 1.
    """
    n_bars = close.size
    out: dict[int, tuple[int, float]] = {}
    log_close = np.log(close)
    for h in HORIZONS:
        qualifying = trigger_idx + h < n_bars
        n_q = int(qualifying.sum())
        if n_q == 0:
            out[h] = (0, float("nan"))
            continue
        t = trigger_idx[qualifying]
        d = direction[qualifying].astype(float)
        rets = 1e4 * d * (log_close[t + h] - log_close[t])
        out[h] = (n_q, float(rets.mean()))
    return out


def rank_bands_within_cell(cell_rows: list[dict]) -> dict[float, float]:
    """Frozen §5.2 within-cell ranking at the binding horizon.

    Bands with denominator < ``EVENT_FLOOR`` are imputed the worst rank (5.0).
    Qualifying bands are ranked by mean gross bps descending (rank 1 = best);
    exact ties receive the average of the tied rank positions.
    """
    qualified = [(r["band"], r["mean_bps_h8"]) for r in cell_rows
                 if r["n_h8"] >= EVENT_FLOOR and not math.isnan(r["mean_bps_h8"])]
    ranks: dict[float, float] = {r["band"]: WORST_RANK for r in cell_rows}
    ordered = sorted(qualified, key=lambda x: -x[1])
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # average of 1-based positions i..j
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = avg_rank
        i = j + 1
    return ranks


def select_band(median_ranks: dict[float, float]) -> float:
    """Best median rank across cells; ties go to the wider band (frozen rule)."""
    best = min(median_ranks.values())
    tied = [b for b, m in median_ranks.items() if m == best]
    return max(tied)


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs returned from the analysis pass; no reloads)
# --------------------------------------------------------------------------- #
def plot_rank_heatmap(rank_df: pl.DataFrame, path: Path) -> None:
    """51-cell × 5-band rank heatmap at H=8, floor-imputed cells annotated."""
    cells = sorted(set(zip(rank_df["instrument"], rank_df["domain"])))
    matrix = np.full((len(cells), len(BANDS)), np.nan)
    floored = np.zeros_like(matrix, dtype=bool)
    index = {c: i for i, c in enumerate(cells)}
    for row in rank_df.to_dicts():
        i = index[(row["instrument"], row["domain"])]
        j = BANDS.index(row["band"])
        matrix[i, j] = row["rank_h8"]
        floored[i, j] = bool(row["floor_imputed"])
    fig, ax = plt.subplots(figsize=(7, 14))
    im = ax.imshow(matrix, aspect="auto", cmap="viridis_r", vmin=1, vmax=WORST_RANK)
    ax.set_xticks(range(len(BANDS)), [str(b) for b in BANDS])
    ax.set_yticks(range(len(cells)), [f"{i}-{d}" for i, d in cells], fontsize=6)
    for i in range(len(cells)):
        for j in range(len(BANDS)):
            if floored[i, j]:
                ax.text(j, i, "F", ha="center", va="center", color="red", fontsize=5)
    ax.set_xlabel("band multiplier")
    ax.set_title("EXP-042 within-cell band rank at H=8 (F = event-count floor imputed)")
    fig.colorbar(im, ax=ax, label="rank (1 = best)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_event_counts(scan_df: pl.DataFrame, path: Path) -> None:
    """Event count vs band, per domain, one line per instrument (log y)."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(15, 5), sharey=True)
    for ax, domain in zip(axes, DOMAINS):
        sub = scan_df.filter(pl.col("domain") == domain)
        for inst in INSTRUMENTS:
            rows = sub.filter(pl.col("instrument") == inst).sort("band")
            ax.plot(rows["band"], rows["n_events"].to_numpy() + 1, lw=0.8, label=inst)
        ax.axhline(EVENT_FLOOR, color="red", ls="--", lw=0.8)
        ax.set_yscale("log")
        ax.set_title(domain)
        ax.set_xlabel("band multiplier")
    axes[0].set_ylabel("TRAIN events + 1 (log)")
    axes[-1].legend(fontsize=5, ncol=2)
    fig.suptitle("EXP-042 TRAIN event count vs band (red dashes = floor 30)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_gross_by_band(scan_df: pl.DataFrame, path: Path) -> None:
    """Per-domain median (across instruments) of cell mean gross bps vs band."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(15, 5))
    for ax, domain in zip(axes, DOMAINS):
        sub = scan_df.filter(pl.col("domain") == domain)
        for h in HORIZONS:
            med = (sub.filter(pl.col(f"n_h{h}") >= 1)
                   .group_by("band").agg(pl.col(f"mean_bps_h{h}").median())
                   .sort("band"))
            ax.plot(med["band"], med[f"mean_bps_h{h}"], marker="o", label=f"H={h}")
        ax.axhline(0.0, color="grey", lw=0.6)
        ax.set_title(domain)
        ax.set_xlabel("band multiplier")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("median across instruments of cell mean gross bps")
    fig.suptitle("EXP-042 gross forward return vs band (context only — not a selection input)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def scan_instrument(ts: TrainSlice) -> list[dict]:
    """All domain×band measurements for one instrument's TRAIN slice."""
    rows: list[dict] = []
    for domain, minutes in DOMAINS.items():
        bars = aggregate_ohlc(ts.frame_1m, period_minutes=minutes, min_coverage=MIN_COVERAGE)
        close = bars.get_column("Close").to_numpy().astype(float)
        for band in BANDS:
            result = generate_avwap_events(
                bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume"),
                instrument=ts.instrument, domain=domain,
                band_multiplier=band, arm_at_adverse_band=True,
            )
            ev = result.events
            row: dict = {
                "instrument": ts.instrument, "domain": domain, "band": band,
                "n_domain_bars": bars.height, "n_events": ev.height,
            }
            if ev.height:
                stats = forward_return_stats(
                    close,
                    ev.get_column("trigger_idx").to_numpy(),
                    ev.get_column("direction").to_numpy(),
                )
            else:
                stats = {h: (0, float("nan")) for h in HORIZONS}
            for h in HORIZONS:
                row[f"n_h{h}"], row[f"mean_bps_h{h}"] = stats[h]
            rows.append(row)
    return rows


def build_rank_outputs(scan_df: pl.DataFrame) -> tuple[pl.DataFrame, dict[float, float], float]:
    """Apply the frozen selection rule; return rank table, medians, selected band."""
    rank_rows: list[dict] = []
    for inst in INSTRUMENTS:
        for domain in DOMAINS:
            cell = scan_df.filter(
                (pl.col("instrument") == inst) & (pl.col("domain") == domain)
            ).to_dicts()
            if not cell:
                continue
            ranks = rank_bands_within_cell(cell)
            for r in cell:
                rank_rows.append({
                    "instrument": inst, "domain": domain, "band": r["band"],
                    "n_h8": r["n_h8"], "mean_bps_h8": r["mean_bps_h8"],
                    "floor_imputed": r["n_h8"] < EVENT_FLOOR,
                    "rank_h8": ranks[r["band"]],
                })
    rank_df = pl.DataFrame(rank_rows)
    median_ranks = {
        b: float(rank_df.filter(pl.col("band") == b).get_column("rank_h8").median())
        for b in BANDS
    }
    return rank_df, median_ranks, select_band(median_ranks)


def build_power_statement(
    scan_df: pl.DataFrame, slices: dict[str, TrainSlice], selected: float
) -> pl.DataFrame:
    """Selected band's per-cell TRAIN event rates + projected TEST counts.

    Projection = TRAIN events × (TEST 1m rows / TRAIN 1m rows); row counts come
    from boundary arithmetic only — no TEST bar content is read.
    """
    rows = []
    for r in scan_df.filter(pl.col("band") == selected).to_dicts():
        ts = slices[r["instrument"]]
        ratio = ts.test_rows_1m / ts.train_rows_1m if ts.train_rows_1m else float("nan")
        rows.append({
            "instrument": r["instrument"], "domain": r["domain"], "band": selected,
            "train_events": r["n_events"], "train_domain_bars": r["n_domain_bars"],
            "events_per_1k_bars": (1000.0 * r["n_events"] / r["n_domain_bars"]
                                   if r["n_domain_bars"] else float("nan")),
            "test_over_train_1m_ratio": ratio,
            "projected_test_events": r["n_events"] * ratio,
            "meets_floor_h8": r["n_h8"] >= EVENT_FLOOR,
        })
    return pl.DataFrame(rows)


def main() -> None:
    """Run the A0 band-selection scan end to end (TRAIN-only)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    scan_rows: list[dict] = []
    slices: dict[str, TrainSlice] = {}
    boundaries: dict[str, dict] = {}
    for inst in tqdm(INSTRUMENTS, desc="A0 band scan (instruments)"):
        ts = load_train_slice(inst)
        slices[inst] = ts
        boundaries[inst] = {
            "source_file": ts.source_file, "total_rows_1m": ts.total_rows_1m,
            "analysis_rows_1m": ts.analysis_rows_1m, "train_rows_1m": ts.train_rows_1m,
            "test_rows_1m_count_only": ts.test_rows_1m, "train_end_ts": ts.train_end_ts,
        }
        scan_rows.extend(scan_instrument(ts))
        slices[inst] = TrainSlice(  # drop the 1m frame; keep boundary metadata only
            instrument=ts.instrument, source_file=ts.source_file,
            total_rows_1m=ts.total_rows_1m, analysis_rows_1m=ts.analysis_rows_1m,
            train_rows_1m=ts.train_rows_1m, test_rows_1m=ts.test_rows_1m,
            train_end_ts=ts.train_end_ts, frame_1m=pl.DataFrame(),
        )

    scan_df = pl.DataFrame(scan_rows).sort(["instrument", "domain", "band"])
    rank_df, median_ranks, selected = build_rank_outputs(scan_df)
    power_df = build_power_statement(scan_df, slices, selected)

    floored_frac_by_band = {
        b: float(rank_df.filter(pl.col("band") == b).get_column("floor_imputed").mean())
        for b in BANDS
    }
    degenerate_floor = all(floored_frac_by_band[b] > 0.5 for b in BANDS if b >= 1.5)

    scan_path = RESULTS_DIR / "band_scan.parquet"
    scan_df.write_parquet(scan_path)
    rank_df.write_csv(RESULTS_DIR / "rank_table.csv")
    power_df.write_csv(RESULTS_DIR / "power_statement.csv")

    # F03: a floor-dominated scan must not silently freeze the band — the
    # selection is reported but the freeze is withheld for operator adjudication.
    verdict = ("BAND_SELECTED_DEGENERATE_FLOOR_PENDING_ADJUDICATION"
               if degenerate_floor else "BAND_SELECTED")

    metadata = {
        "experiment": "EXP-042",
        "verdict": verdict,
        "selected_band": selected,
        "median_ranks": {str(b): median_ranks[b] for b in BANDS},
        "floor_imputed_fraction_by_band": {str(b): floored_frac_by_band[b] for b in BANDS},
        "degenerate_floor_disclosure": degenerate_floor,
        "entry_rule": "arm_at_adverse_band (operator-ratified 2026-06-11); trigger = AVWAP recross",
        "bands": list(BANDS), "horizons": list(HORIZONS),
        "binding_horizon": BINDING_HORIZON, "event_floor": EVENT_FLOOR,
        "min_coverage": MIN_COVERAGE, "domains": DOMAINS,
        "analysis_fraction": ANALYSIS_FRACTION, "train_fraction": TRAIN_FRACTION,
        "boundaries": boundaries,
        "band_scan_sha256": hashlib.sha256(scan_path.read_bytes()).hexdigest(),
        "de30_disclosure": "DE30 coverage truncated (history ends 2026-01-16); "
                           "boundaries derive from its own realized timeline (D0 P8).",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    plot_rank_heatmap(rank_df, PLOTS_DIR / "rank_heatmap.png")
    plot_event_counts(scan_df, PLOTS_DIR / "event_count_vs_band.png")
    plot_gross_by_band(scan_df, PLOTS_DIR / "gross_bps_vs_band.png")

    LOGGER.info("selected band: %s", selected)
    LOGGER.info("median ranks: %s", {b: round(median_ranks[b], 2) for b in BANDS})
    LOGGER.info("floor-imputed fraction by band: %s",
                {b: round(floored_frac_by_band[b], 2) for b in BANDS})
    if degenerate_floor:
        LOGGER.warning("DEGENERATE_FLOOR: >50%% of cells floor-imputed at every band "
                       ">= 1.5 — band freeze WITHHELD pending operator adjudication.")
    LOGGER.info("outputs written under %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
