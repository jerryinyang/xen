"""EXP-050 -- Phase 014-A Harami-in-Context: Position-in-Move vs Baselines.

`CF-HA-HARAMI-001` / HYP-003. TRAIN-only, gross, descriptive; 0 candidate slots,
0 TEST reads. For each EXP-048-READY cell (instrument x domain) this script, on
the TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by the F01 file-order prefix
   convention (no full-file sort/collect; TEST and the final-30% global holdout
   are never read);
2. aggregates the domain (5m strict; 15m/30m/1h/2h/4h at min_coverage=0.90) and
   fences every domain bar to `CloseTime <= train_end_ts`;
3. generates Heiken Ashi candles and detects HA haramis (`xen.ha_harami`,
   frozen) -- one event per `HA0Time`; the real signal price `P_sig` is the real
   domain `Close` at `HA0Time` (== `RealClose`; no HA price enters any metric);
4. runs the frozen Wilder-ATR ZigZag substrate (`xen.zigzag`, real bars) and
   assigns each domain bar -- hence each harami -- to its containing confirmed
   move under pivot tiling, computing the price-excursion position-in-move
   (`xen.move_position`);
5. measures the per-cell final-third rate `FT = P(pos >= 0.67)` against the exact
   direction-matched random-timing baseline `FT_rand` (binding) and the MA(20,50)
   alternative-segmentation baseline (disclosed), with a regime-clustered
   moving-block bootstrap CI on the gap `Delta = FT - FT_rand`;
6. runs a determinism replay (second full pass, identical seeds) and the
   detector/assignment/causality-fence invariant batteries, and applies the P9
   materiality (`Delta >= 0.10` & n_assigned >= 30) and P11 composition rules as
   a mechanical readout (not a gate decision).

Outputs (results/): per_cell_context.parquet, final_third_rate_map.csv,
secondary_disclosure.csv, composition_readout.json, run_metadata.json. Plots
(plots/): FT heatmap, Delta gap heatmap, pooled position distribution, assigned
-count heatmap. Real prices throughout; no HA price enters any metric.
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
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.move_position import (  # noqa: E402
    ASSIGNED,
    AFTER_LAST,
    BEFORE_FIRST,
    DEGENERATE,
    POSITION_THRESHOLD,
    assign_to_moves,
    direction_matched_rate,
    duration_fraction,
)
from xen.referee_calibration import ma_crossover_positions  # noqa: E402
from xen.zigzag import generate_zigzag  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 frozen; conventions from EXP-048 / EXP-049)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-050"
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
MA_FAST, MA_SLOW = 20, 50  # P13.2 alternative segmentation
MEMBER_STATUSES = ("READY", "READY_FLAGGED")
POS_THRESHOLD = POSITION_THRESHOLD   # P9 near-exhaustion (0.67)
MATERIALITY_DELTA = 0.10             # P9 cluster-materiality gap (10 pp)
POWER_FLOOR = 30                     # P11 reportability floor (assigned haramis)
HIST_BINS = 20                       # position distribution bins
HIST_LO, HIST_HI = -0.5, 1.5         # position distribution range
N_BOOT = 10_000           # MBB resamples
BOOT_BATCH = 2_000        # MBB vectorized batch size
BASE_SEED = 20260615      # frozen bootstrap seed (no tuning)
TOTAL_CELLS = len(INSTRUMENTS) * len(DOMAINS)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts/rates "
    "derive from its own realized timeline and are not span-comparable (VAL-003)."
)
# Per-cell status -> integer code (for heatmap masking).
CSTATUS_CODES: dict[str, int] = {
    "CLUSTERED": 0, "NOT_CLUSTERED": 1, "NOT_REPORTABLE_BY_POWER": 2, "EXCLUDED": 3,
}
INVARIANT_NAMES: list[str] = ["inv_detector", "inv_assignment", "inv_fence"]
# Per-cell diagnostic decomposition of the aggregate `inv_assignment` battery
# (reported alongside it for triage; not themselves CONTEXT_REFUTED gates).
INVARIANT_DIAGNOSTIC_FIELDS: list[str] = ["inv_unmatched", "inv_bad_pos", "inv_partition"]
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
            f"EXP-048 readiness map not found at {READINESS_MAP}; EXP-050 is gated "
            "on EXP-048 READINESS_DELIVERED + audit PASS."
        )
    rows = pl.read_csv(READINESS_MAP).select("instrument", "domain", "status").to_dicts()
    return {(r["instrument"], r["domain"]): r["status"] for r in rows}


# --------------------------------------------------------------------------- #
# Pure computation -- segmentation builders
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def build_ma_regimes(bars: pl.DataFrame) -> pl.DataFrame:
    """MA(fast, slow)-crossover regimes as a move segmentation (disclosed P13.2).

    A regime = a maximal contiguous run of constant non-zero MA-crossover
    position. ``StartPrice``/``EndPrice`` = real ``Close`` at the run's first/last
    bar; ``Direction`` = the run's sign. Flat (position 0) bars carry no regime.
    """
    empty = pl.DataFrame(
        schema={"StartTime": bars.schema["CloseTime"], "EndTime": bars.schema["CloseTime"],
                "StartPrice": pl.Float64, "EndPrice": pl.Float64, "Direction": pl.Int32}
    )
    if bars.height < 2:
        return empty
    close = bars.get_column("Close").to_numpy().astype(np.float64)
    times = bars.get_column("CloseTime")
    pos = ma_crossover_positions(close, fast=MA_FAST, slow=MA_SLOW)  # length n-1
    m = int(pos.shape[0])
    if m == 0:
        return empty
    change = np.empty(m, dtype=bool)
    change[0] = True
    if m > 1:
        change[1:] = pos[1:] != pos[:-1]
    starts = np.flatnonzero(change)
    ends = np.append(starts[1:] - 1, m - 1)
    keep = pos[starts] != 0.0
    s, e = starts[keep], ends[keep]
    if s.shape[0] == 0:
        return empty
    return pl.DataFrame({
        "StartTime": times.gather(s), "EndTime": times.gather(e),
        "StartPrice": close[s], "EndPrice": close[e],
        "Direction": pos[s].astype(np.int32),
    })


# --------------------------------------------------------------------------- #
# Pure computation -- bootstrap, assignment, per-cell core
# --------------------------------------------------------------------------- #
def _cell_rng(cell_index: int) -> np.random.Generator:
    """Deterministic, independent per-cell RNG (SeedSequence spawn by index)."""
    # SeedSequence(BASE_SEED).spawn(TOTAL_CELLS) is deterministic, so re-deriving
    # the same child by global cell index reproduces identical draws across passes.
    child = np.random.SeedSequence(BASE_SEED).spawn(TOTAL_CELLS)[cell_index]
    return np.random.default_rng(child)


def mbb_ci_delta(
    indicator: np.ndarray, ft_rand: float, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float, float, int]:
    """Regime-clustered moving-block bootstrap CI on ``Delta = FT - FT_rand``.

    Resamples the ``HA0Time``-ordered final-third indicator sequence (FT_rand held
    fixed). Block length ``b = max(1, round(n**(1/3)))``; ``ceil(n/b)`` contiguous
    blocks per resample (truncated to length ``n``). Returns
    ``(ci_low_1s, ci_lo_2s, ci_hi_2s, block_len)`` -- ``ci_low_1s`` is the 5th
    percentile (one-sided 95% lower bound).
    """
    n = int(indicator.shape[0])
    b = max(1, int(round(n ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(n / b))
    max_start = max(0, n - b)
    ind = indicator.astype(np.int32)
    offsets = np.arange(b, dtype=np.int64)
    deltas: list[np.ndarray] = []
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :n]
        ft_star = ind[idx].mean(axis=1)
        deltas.append(ft_star - ft_rand)
        done += k
    all_d = np.concatenate(deltas)
    return (float(np.percentile(all_d, 5.0)), float(np.percentile(all_d, 2.5)),
            float(np.percentile(all_d, 97.5)), b)


def _assign_bars(bars: pl.DataFrame, moves: pl.DataFrame, left_strict: bool) -> pl.DataFrame:
    """Assign every domain bar to its containing move (price-excursion pos)."""
    events = bars.with_row_index("bar_idx").select(
        pl.col("bar_idx"),
        pl.col("CloseTime").alias("EventTime"),
        pl.col("Close").alias("EventPrice"),
    )
    return assign_to_moves(events, moves, left_strict=left_strict, threshold=POS_THRESHOLD)


def _harami_view(haramis: pl.DataFrame, assigned_bars: pl.DataFrame) -> pl.DataFrame:
    """Look up each harami's containing-move position via its own domain bar.

    `HA0Time` is the latest HA candle's `CloseTime`, which equals a domain bar
    `CloseTime` (HA is 1:1 with real bars), so a harami's position is exactly its
    own bar's position -- apples-to-apples with the in-move random baseline.
    """
    bar_view = assigned_bars.select(
        pl.col("EventTime").alias("HA0Time"), "bar_idx", "pos", "move_dir",
        "move_start_time", "move_end_time", "exclusion",
    )
    return haramis.select("HA0Time", "ReducedOK").join(bar_view, on="HA0Time", how="left")


def _seg_stats(
    assigned_bars: pl.DataFrame, harami_view: pl.DataFrame, close_epoch: np.ndarray,
    want_duration: bool,
) -> dict[str, Any]:
    """Final-third stats for one segmentation (ZigZag or MA): FT, FT_rand, splits."""
    pop = assigned_bars.filter(pl.col("exclusion") == ASSIGNED)
    pop_pos = pop.get_column("pos").to_numpy().astype(np.float64)
    pop_dir = pop.get_column("move_dir").to_numpy().astype(np.int64)

    ha = harami_view.filter(pl.col("exclusion") == ASSIGNED).sort("HA0Time")
    n_assigned = int(ha.height)
    har_pos = ha.get_column("pos").to_numpy().astype(np.float64)
    har_dir = ha.get_column("move_dir").to_numpy().astype(np.int64)
    ind = (har_pos >= POS_THRESHOLD).astype(np.int32)

    ft = float(ind.mean()) if n_assigned else None
    ft_rand = (
        float(direction_matched_rate(pop_pos, pop_dir, har_dir, threshold=POS_THRESHOLD))
        if n_assigned else None
    )
    delta = (ft - ft_rand) if (ft is not None and ft_rand is not None) else None

    out: dict[str, Any] = {
        "pop": pop, "ha": ha, "n_assigned": n_assigned, "ind": ind,
        "har_dir": har_dir, "har_pos": har_pos, "pop_pos": pop_pos, "pop_dir": pop_dir,
        "FT": ft, "FT_rand": ft_rand, "delta": delta,
        "n_assigned_up": int((har_dir == 1).sum()), "n_assigned_down": int((har_dir == -1).sum()),
        "w_up": (float((har_dir == 1).mean()) if n_assigned else None),
        "w_down": (float((har_dir == -1).mean()) if n_assigned else None),
        "q_up": _q(pop_pos, pop_dir, 1), "q_down": _q(pop_pos, pop_dir, -1),
    }
    if want_duration and n_assigned:
        out["dur"] = _duration_stats(pop, ha, close_epoch, har_dir)
    else:
        out["dur"] = {"FT_dur": None, "FT_dur_rand": None, "delta_dur": None}
    return out


def _q(pop_pos: np.ndarray, pop_dir: np.ndarray, direction: int) -> float | None:
    """In-move-bar final-third rate for one direction (None if no such bars)."""
    mask = pop_dir == direction
    return float(np.mean(pop_pos[mask] >= POS_THRESHOLD)) if mask.any() else None


def _duration_stats(
    pop: pl.DataFrame, ha: pl.DataFrame, close_epoch: np.ndarray, har_dir: np.ndarray,
) -> dict[str, Any]:
    """Disclosed duration-fraction final-third rate + direction-matched baseline."""
    har_dur = duration_fraction(
        ha.get_column("bar_idx").to_numpy().astype(np.int64),
        _t2idx(ha.get_column("move_start_time"), close_epoch),
        _t2idx(ha.get_column("move_end_time"), close_epoch),
    )
    pop_dur = duration_fraction(
        pop.get_column("bar_idx").to_numpy().astype(np.int64),
        _t2idx(pop.get_column("move_start_time"), close_epoch),
        _t2idx(pop.get_column("move_end_time"), close_epoch),
    )
    valid = ~np.isnan(har_dur)
    ft_dur = float(np.mean(har_dur[valid] >= POS_THRESHOLD)) if valid.any() else None
    ft_dur_rand = float(direction_matched_rate(
        np.where(np.isnan(pop_dur), -1.0, pop_dur),
        pop.get_column("move_dir").to_numpy().astype(np.int64), har_dir,
        threshold=POS_THRESHOLD))
    delta_dur = (ft_dur - ft_dur_rand) if ft_dur is not None else None
    return {"FT_dur": ft_dur, "FT_dur_rand": ft_dur_rand, "delta_dur": delta_dur}


def _t2idx(time_col: pl.Series, close_epoch: np.ndarray) -> np.ndarray:
    """Map a Datetime column to domain-bar indices (exact match by epoch second)."""
    target = time_col.dt.epoch("s").to_numpy()
    return np.searchsorted(close_epoch, target)


def compute_core(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Build the domain, segmentations, harami positions, baselines, and CI.

    Pure given identical inputs/seeds. Returns a flat dict of per-cell measured
    fields plus the bounded plot inputs (position histograms).
    """
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = int(bars.height)
    close_epoch = bars.get_column("CloseTime").dt.epoch("s").to_numpy() if n_bars else np.empty(0)

    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    ha_candles = generate_heiken_ashi(bars)
    haramis = detect_ha_harami(ha_candles)
    n_haramis_total = int(haramis.height)

    zz_bars = _assign_bars(bars, moves, left_strict=True)
    zz_har = _harami_view(haramis, zz_bars)
    zz = _seg_stats(zz_bars, zz_har, close_epoch, want_duration=True)

    ma_regimes = build_ma_regimes(bars)
    ma_bars = _assign_bars(bars, ma_regimes, left_strict=False)
    ma_har = _harami_view(haramis, ma_bars)
    ma = _seg_stats(ma_bars, ma_har, close_epoch, want_duration=False)

    # ZigZag harami exclusion partition (denominator discipline).
    excl = zz_har.get_column("exclusion")
    n_warmup = int((excl == BEFORE_FIRST).sum())
    n_formingtail = int((excl == AFTER_LAST).sum())
    n_degenerate = int((excl == DEGENERATE).sum())
    n_unmatched = int(excl.is_null().sum())
    n_assigned = zz["n_assigned"]

    # MA harami exclusion (flat = before/after a regime).
    ma_excl = ma_har.get_column("exclusion")
    n_ma_flat = int((ma_excl == BEFORE_FIRST).sum() + (ma_excl == AFTER_LAST).sum())
    n_ma_degenerate = int((ma_excl == DEGENERATE).sum())

    # Bootstrap CI on the binding gap (reportable cells only).
    ci_low_1s = ci_lo_2s = ci_hi_2s = None
    block_len = max(1, int(round(n_assigned ** (1.0 / 3.0)))) if n_assigned else None
    if n_assigned >= POWER_FLOOR:
        ci_low_1s, ci_lo_2s, ci_hi_2s, block_len = mbb_ci_delta(
            zz["ind"], zz["FT_rand"], _cell_rng(cell_index))

    # Position distribution summary + bounded histogram plot inputs.
    pos_median = float(np.median(zz["har_pos"])) if n_assigned else None
    pos_iqr = (float(np.percentile(zz["har_pos"], 75) - np.percentile(zz["har_pos"], 25))
               if n_assigned else None)
    har_hist = _hist(zz["har_pos"])
    pop_hist = _hist(zz["pop_pos"])

    invariants = _invariants(
        haramis, moves, zz["pop"], n_assigned, zz_har, n_haramis_total,
        n_warmup, n_formingtail, n_degenerate, n_unmatched, train_end_epoch)

    delta_ma = (zz["FT"] - ma["FT"]) if (zz["FT"] is not None and ma["FT"] is not None) else None
    return {
        "n_bars": n_bars, "n_moves": int(moves.height), "n_haramis_total": n_haramis_total,
        "n_assigned": n_assigned, "n_assigned_up": zz["n_assigned_up"],
        "n_assigned_down": zz["n_assigned_down"],
        "n_warmup_excl": n_warmup, "n_formingtail_excl": n_formingtail,
        "n_degenerate_excl": n_degenerate, "n_unmatched_excl": n_unmatched,
        "FT": zz["FT"], "FT_rand": zz["FT_rand"], "delta": zz["delta"],
        "ci_low_1s": ci_low_1s, "ci_lo_2s": ci_lo_2s, "ci_hi_2s": ci_hi_2s,
        "block_len": block_len, "q_up": zz["q_up"], "q_down": zz["q_down"],
        "w_up": zz["w_up"], "w_down": zz["w_down"],
        "pos_median": pos_median, "pos_iqr": pos_iqr,
        "FT_dur": zz["dur"]["FT_dur"], "FT_dur_rand": zz["dur"]["FT_dur_rand"],
        "delta_dur": zz["dur"]["delta_dur"],
        "n_ma_assigned": ma["n_assigned"], "FT_MA": ma["FT"], "FT_MA_rand": ma["FT_rand"],
        "delta_ma_vs_rand": ma["delta"], "delta_ma": delta_ma,
        "n_ma_flat_excl": n_ma_flat, "n_ma_degenerate_excl": n_ma_degenerate,
        "har_hist": har_hist, "pop_hist": pop_hist,
        **invariants,
    }


def _hist(values: np.ndarray) -> list[int]:
    """Fixed-bin position histogram counts (bounded plot input)."""
    if values.size == 0:
        return [0] * HIST_BINS
    counts, _ = np.histogram(values, bins=HIST_BINS, range=(HIST_LO, HIST_HI))
    return [int(c) for c in counts]


def _invariants(
    haramis: pl.DataFrame, moves: pl.DataFrame, pop: pl.DataFrame, n_assigned: int,
    zz_har: pl.DataFrame, n_haramis_total: int, n_warmup: int, n_formingtail: int,
    n_degenerate: int, n_unmatched: int, train_end_epoch: int,
) -> dict[str, int]:
    """Detector / assignment / causality-fence invariant counts (all must be 0)."""
    inv_detector = int((~haramis.get_column("ReducedOK")).sum()) if n_haramis_total else 0

    partition_ok = (n_assigned + n_warmup + n_formingtail + n_degenerate + n_unmatched
                    == n_haramis_total)
    bad_pos = int(zz_har.filter(
        (pl.col("exclusion") == ASSIGNED) & ~pl.col("pos").is_finite()).height)
    inv_partition = 0 if partition_ok else 1
    inv_assignment = n_unmatched + bad_pos + inv_partition

    fence = 0
    if n_haramis_total:
        fence += int((haramis.get_column("HA0Time").dt.epoch("s") > train_end_epoch).sum())
    if moves.height:
        fence += int((moves.get_column("ConfirmTime").dt.epoch("s") > train_end_epoch).sum())
    if pop.height:
        fence += int((pop.get_column("EventTime").dt.epoch("s") > train_end_epoch).sum())
    return {"inv_detector": inv_detector, "inv_assignment": int(inv_assignment),
            "inv_unmatched": int(n_unmatched), "inv_bad_pos": int(bad_pos),
            "inv_partition": int(inv_partition), "inv_fence": int(fence)}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def cell_status(rec: dict[str, Any]) -> str:
    """Mechanical P9 per-cell status (binding random baseline)."""
    if not rec["member"]:
        return "EXCLUDED"
    if (rec["n_assigned"] or 0) < POWER_FLOOR:
        return "NOT_REPORTABLE_BY_POWER"
    if rec["delta"] is not None and rec["delta"] >= MATERIALITY_DELTA:
        return "CLUSTERED"
    return "NOT_CLUSTERED"


def process_member_cell(
    instrument: str, domain: str, status_048: str, train_1m: pl.DataFrame,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Process one EXP-048-READY cell: context core + determinism replay."""
    period_minutes, min_coverage = DOMAINS[domain]
    core1 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    core2 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    determinism_ok = core1 == core2

    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": True, "determinism_ok": determinism_ok, **core1,
    }
    total = rec["n_haramis_total"] or 0
    rec["warmup_frac"] = (rec["n_warmup_excl"] / total) if total else None
    rec["formingtail_frac"] = (rec["n_formingtail_excl"] / total) if total else None
    rec["degenerate_frac"] = (rec["n_degenerate_excl"] / total) if total else None
    rec["reportable"] = (rec["n_assigned"] or 0) >= POWER_FLOOR
    rec["clustered_binding"] = bool(
        rec["reportable"] and rec["delta"] is not None and rec["delta"] >= MATERIALITY_DELTA)
    rec["status"] = cell_status(rec)
    rec["status_code"] = CSTATUS_CODES[rec["status"]]
    return rec


def excluded_cell(instrument: str, domain: str, status_048: str) -> dict[str, Any]:
    """Record for a non-member (not EXP-048-READY) cell -- unmeasured."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": False, "determinism_ok": None, "n_bars": None, "n_moves": None,
        "n_haramis_total": None, "n_assigned": None, "FT": None, "FT_rand": None,
        "delta": None, "ci_low_1s": None, "reportable": False, "clustered_binding": False,
        "status": "EXCLUDED", "status_code": CSTATUS_CODES["EXCLUDED"],
        "har_hist": [0] * HIST_BINS, "pop_hist": [0] * HIST_BINS,
    }
    for name in INVARIANT_NAMES + INVARIANT_DIAGNOSTIC_FIELDS:
        rec[name] = None
    return rec


# --------------------------------------------------------------------------- #
# Verdict, composition, readout
# --------------------------------------------------------------------------- #
def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """CONTEXT_REFUTED iff non-determinism on any cell, or a battery (1-3)
    invariant on >= 3 instruments. Otherwise CONTEXT_CHARACTERISATION_DELIVERED."""
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
        "verdict": "CONTEXT_REFUTED" if refuted else "CONTEXT_CHARACTERISATION_DELIVERED",
        "non_deterministic_cells": non_det,
        "systematic_invariant_failures": systematic,
    }


def composition_readout(records: list[dict[str, Any]]) -> dict[str, Any]:
    """P11 composition on the binding random baseline + disclosed support tiers."""
    members = [r for r in records if r["member"]]
    clustered = [r for r in members if r["status"] == "CLUSTERED"]
    binding = _compose(clustered)

    strong = [r for r in clustered
              if r.get("ci_low_1s") is not None and r["ci_low_1s"] > MATERIALITY_DELTA]
    reliably_positive = [r for r in members if r.get("reportable")
                         and r.get("delta") is not None and r["delta"] > 0
                         and r.get("ci_low_1s") is not None and r["ci_low_1s"] > 0]
    ma_robust = [r for r in clustered if r.get("delta_ma_vs_rand") is not None
                 and r["delta_ma_vs_rand"] >= MATERIALITY_DELTA]

    reportable = [r for r in members if r.get("reportable")]
    sens = {
        "delta_ge_0.05": _compose([r for r in reportable
                                   if r.get("delta") is not None and r["delta"] >= 0.05]),
        "delta_ge_0.15": _compose([r for r in reportable
                                   if r.get("delta") is not None and r["delta"] >= 0.15]),
        "relaxed_4cells_2instruments": _relaxed(clustered, 4, 2),
        "relaxed_3cells_2instruments": _relaxed(clustered, 3, 2),
    }
    return {
        "binding_random_baseline": binding,
        "support_tier_ci_low_gt_0.10": _compose(strong),
        "support_tier_reliably_positive": _compose(reliably_positive),
        "ma_robustness_composition": _compose(ma_robust),
        "sensitivity_non_binding": sens,
        "rule": ("CLUSTERED iff delta = FT - FT_rand >= 0.10 AND n_assigned >= 30 "
                 "(binding random baseline); composition_met iff >=5 CLUSTERED cells "
                 "over >=3 instruments (P9/P11). CI tiers and MA-robustness disclosed."),
    }


def _compose(cells: list[dict[str, Any]]) -> dict[str, Any]:
    instruments = sorted({r["instrument"] for r in cells})
    return {
        "n_cells": len(cells), "n_instruments": len(instruments),
        "instruments": ";".join(instruments),
        "cells": [f"{r['instrument']}-{r['domain']}" for r in cells],
        "composition_met": len(cells) >= 5 and len(instruments) >= 3,
    }


def _relaxed(cells: list[dict[str, Any]], c: int, i: int) -> bool:
    return len(cells) >= c and len({r["instrument"] for r in cells}) >= i


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _matrix(records: list[dict[str, Any]], value: str, mask_unreportable: bool) -> np.ndarray:
    """instrument x domain matrix (NaN where missing / not reportable)."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = lookup.get((inst, dom))
            if rec is None or not rec.get("member"):
                continue
            if mask_unreportable and not rec.get("reportable"):
                continue
            val = rec.get(value)
            if val is not None:
                matrix[i, j] = float(val)
    return matrix


def _clustered_mask(records: list[dict[str, Any]]) -> np.ndarray:
    domains = list(DOMAINS.keys())
    mask = np.zeros((len(INSTRUMENTS), len(domains)), dtype=bool)
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = lookup.get((inst, dom))
            if rec is not None and rec.get("status") == "CLUSTERED":
                mask[i, j] = True
    return mask


def plot_ft_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Observed final-third-rate FT heatmap; non-reportable / excluded greyed."""
    matrix = _matrix(records, "FT", mask_unreportable=True)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="magma", vmin=0.0, vmax=1.0, annot=True, fmt=".2f",
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "FT = P(pos >= 0.67)"}, annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: observed final-third rate FT")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delta_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Gap Delta = FT - FT_rand heatmap; CLUSTERED cells (Delta>=0.10) marked '*'."""
    matrix = _matrix(records, "delta", mask_unreportable=True)
    clustered = _clustered_mask(records)
    vmax = float(np.nanmax(np.abs(matrix))) if np.isfinite(matrix).any() else 0.1
    vmax = max(vmax, MATERIALITY_DELTA)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="RdBu_r", center=0.0, vmin=-vmax, vmax=vmax,
                annot=True, fmt=".2f", xticklabels=list(DOMAINS.keys()),
                yticklabels=INSTRUMENTS, cbar_kws={"label": "Delta = FT - FT_rand"},
                annot_kws={"size": 6})
    for i, j in zip(*np.where(clustered)):
        ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor="black", lw=2))
    ax.set_title(f"{EXPERIMENT_ID}: gap Delta vs random baseline (boxed = CLUSTERED, "
                 f">= {MATERIALITY_DELTA:.2f})")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_position_distribution(records: list[dict[str, Any]], save_path: Path) -> None:
    """Pooled position distribution: haramis vs in-move random baseline.

    Equal-weight per reportable cell (each cell's histogram normalized to a
    density before pooling) so large cells do not dominate. Built from the emitted
    fixed-bin counts -- no data reload.
    """
    reportable = [r for r in records if r.get("reportable")]
    edges = np.linspace(HIST_LO, HIST_HI, HIST_BINS + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    har = _pool_hist(reportable, "har_hist")
    pop = _pool_hist(reportable, "pop_hist")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.step(centers, har, where="mid", label="haramis", color="#d73027", lw=2)
    ax.step(centers, pop, where="mid", label="in-move random baseline",
            color="#4575b4", lw=2)
    ax.axvline(POS_THRESHOLD, color="black", ls="--", lw=1, label=f"pos = {POS_THRESHOLD}")
    ax.set_xlabel("position-in-move (price excursion)")
    ax.set_ylabel("mean per-cell density")
    ax.set_title(f"{EXPERIMENT_ID}: pooled position-in-move "
                 f"(equal-weight over {len(reportable)} reportable cells)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _pool_hist(cells: list[dict[str, Any]], key: str) -> np.ndarray:
    """Mean of per-cell normalized histograms (equal weight per cell)."""
    if not cells:
        return np.zeros(HIST_BINS)
    acc = np.zeros(HIST_BINS)
    used = 0
    for r in cells:
        counts = np.asarray(r.get(key) or [0] * HIST_BINS, dtype=np.float64)
        total = counts.sum()
        if total > 0:
            acc += counts / total
            used += 1
    return acc / used if used else acc


def plot_count_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Assigned-harami-count heatmap (reads the 30-event reportability floor)."""
    matrix = _matrix(records, "n_assigned", mask_unreportable=False)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", annot=True, fmt=".0f",
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "n_assigned haramis"}, annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: assigned-harami count (floor = {POWER_FLOOR})")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]]) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    plot_ft_heatmap(records, PLOTS_DIR / "final_third_rate_heatmap.png")
    plot_delta_heatmap(records, PLOTS_DIR / "delta_gap_heatmap.png")
    plot_position_distribution(records, PLOTS_DIR / "position_distribution.png")
    plot_count_heatmap(records, PLOTS_DIR / "assigned_count_heatmap.png")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_outputs(
    records: list[dict[str, Any]], verdict: dict[str, Any],
    readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the two CSVs, and the two JSON files."""
    scalar = [{k: v for k, v in r.items() if k not in ("har_hist", "pop_hist")}
              for r in records]
    pl.DataFrame(records, strict=False).write_parquet(RESULTS_DIR / "per_cell_context.parquet")
    df = pl.DataFrame(scalar, strict=False)

    ft_cols = ["instrument", "domain", "member", "exp048_status", "n_haramis_total",
               "n_assigned", "n_assigned_up", "n_assigned_down", "FT", "FT_rand",
               "delta", "ci_low_1s", "ci_lo_2s", "ci_hi_2s", "block_len",
               "q_up", "q_down", "w_up", "w_down", "reportable", "clustered_binding",
               "status", "determinism_ok"]
    df.select([c for c in ft_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "final_third_rate_map.csv")

    sec_cols = ["instrument", "domain", "FT_MA", "FT_MA_rand", "delta_ma_vs_rand",
                "delta_ma", "n_ma_assigned", "n_ma_flat_excl", "n_ma_degenerate_excl",
                "FT_dur", "FT_dur_rand", "delta_dur", "pos_median", "pos_iqr",
                "n_warmup_excl", "n_formingtail_excl", "n_degenerate_excl",
                "warmup_frac", "formingtail_frac", "degenerate_frac"]
    df.select([c for c in sec_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "secondary_disclosure.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-A", "hypothesis": "HYP-003", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "metric": ("position-in-move (price excursion) pos=(P_sig-StartPrice)/"
                   "(EndPrice-StartPrice); P_sig=real Close at HA0Time; non-tradable "
                   "descriptive (uses confirmed terminal pivot); no P&L/signal uses pos"),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "atr_estimator": "Wilder",
            "pos_threshold": POS_THRESHOLD, "materiality_delta": MATERIALITY_DELTA,
            "power_floor": POWER_FLOOR, "ma_fast": MA_FAST, "ma_slow": MA_SLOW,
            "n_boot": N_BOOT, "base_seed": BASE_SEED,
            "hist_bins": HIST_BINS, "hist_range": [HIST_LO, HIST_HI],
            "baselines": {"binding": "random matched-count timestamps (exact "
                                     "direction-matched in-move rate, R->inf limit)",
                          "disclosed": "MA(20,50)-crossover alternative segmentation"},
            "ft_rand_form": "exact closed-form FT_rand = sum_d w_d * q_d (no MC draw)",
            "ci_form": "regime-clustered moving-block bootstrap on Delta (FT_rand fixed)",
        },
        "membership": {
            "source": "EXP-048 readiness_map.csv (READY + READY_FLAGGED)",
            "n_member_cells": sum(1 for r in records if r["member"]),
            "n_excluded_cells": sum(1 for r in records if not r["member"]),
        },
        "denominators": {
            "FT": "(# assigned haramis with pos>=0.67) / n_assigned (assigned only); "
                  "n_assigned<30 -> NOT_REPORTABLE_BY_POWER (never 0/0)",
            "exclusions": "warmup/forming-tail/degenerate partition n_haramis_total",
        },
        "verdict": verdict, "composition_readout": readout,
        "de30_disclosure": DE30_DISCLOSURE, "instrument_meta": instrument_meta,
        "holdout_fence": (
            "Only Parquet metadata + first train_rows file-order rows read per "
            "instrument; full file never sorted/collected; every domain bar, harami "
            "HA0Time, and move ConfirmTime fenced to CloseTime <= train_end_ts; TEST "
            "and final-30% holdout never read."
        ),
        "note": ("P9/P11 readout is mechanical; the 014-A G1 desk adjudication on this "
                 "readout is checkpoint work, not self-declared here."),
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(
    records: list[dict[str, Any]], verdict: dict[str, Any], readout: dict[str, Any],
) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    binding = readout["binding_random_baseline"]
    return {"verdict": verdict["verdict"], "status_counts": status_counts,
            "composition_met": binding["composition_met"],
            "n_clustered": binding["n_cells"], "n_instruments": binding["n_instruments"],
            "non_deterministic_cells": verdict["non_deterministic_cells"],
            "systematic_invariant_failures": verdict["systematic_invariant_failures"]}


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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("status counts: %s", json.dumps(summary["status_counts"]))
    LOGGER.info("composition (binding random baseline): %s CLUSTERED cells over %s "
                "instruments (met=%s)", summary["n_clustered"], summary["n_instruments"],
                summary["composition_met"])
    if summary["non_deterministic_cells"]:
        LOGGER.info("NON-DETERMINISTIC: %s", summary["non_deterministic_cells"])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
