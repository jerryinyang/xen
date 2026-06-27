"""Experiment EXP-035: TRAIN-Only Conditioning Characterisation (Clinical-Trade Dimensions).

Implements analysis-plan.md / scope.md (Phase 008, Tier A3; DIAG-005, 0 slots).
Characterises, on TRAIN only, whether the faithful strategy's per-event ABSOLUTE NET
expectancy (frozen CONSERVATIVE costs + predeclared financing) varies materially and
stably across three predeclared dimensions, and emits the design-§8.1 G1 qualification
flag per domain x dimension. HARD NO-SELECTION RULE: no stratum, rule, or threshold is
chosen here — flags only; rule-freezing belongs to the EXP-036 Tier-B scope.

Dimensions (frozen before any TRAIN read):
  C1  %completion-to-target at confirmation:
        c1 = 1 - direction-signed remaining favorable distance / band_spread_at_trigger
      (every term an at-trigger column of EXP-020 ``avwap_events.csv``; causal).
      TRAIN-quantile terciles pooled per domain; boundaries frozen on emission.
  C2  Session of trigger_time (UTC): Asia [00,08) / London [08,16) / NY [16,24). Fixed.
  C3  Trailing volatility regime: ATR(14, domain bars, strictly <= trigger timestamp)
      as percentile rank within a trailing 90-calendar-day window; >= 30 days history
      required (else excluded from C3 only, disclosed). TRAIN-quantile terciles.

Per-event outcome: ``net_e = lifetime_bps - RT_cons_i - financing_e`` (identical
construction to EXP-034; outcome reads nothing past ``completion_idx``).

G1 qualification per domain x dimension (design §8.1; conjunction — all of):
  (i)   Material: top-vs-bottom contrast >= its own 95% bootstrap CI half-width
        (SNR >= 1) AND top/candidate-bin net point > 0;
  (ii)  Structured: weak monotone bin ordering (C1/C3) or omnibus permutation
        heterogeneity (C2, alpha_G1);
  (iii) Stable: chronological TRAIN split-half — same top/candidate bin in both halves
        AND contrast > 0 in both halves (frozen full-TRAIN tercile boundaries reused);
  (iv)  Multiplicity: permutation p survives Holm across the 3 dimensions within the
        domain at alpha_G1 = 0.10.
Floors: a bin with < 30 events (5m/1h) or < 15 (4h) is unreportable; any unreportable
bin makes the domain x dimension G1-INELIGIBLE (reported descriptively).

Predeclared caveat (plan Step 4): event-level label permutation under within-cluster
correlation is anti-conservative; acceptable because §8.1 is a conjunction whose
binding materiality leg is the cluster-aware SNR criterion. Permutation strata are
(instrument, direction) — the frozen machinery's strata; regime clusters remain the
bootstrap resampling unit. F05 (2026-06-10): the permutation statistic RE-SELECTS
the candidate bin by the same max rule inside every permutation (|high-low| for
ordered dims; max candidate-vs-rest for sessions), so candidate selection is part
of the null distribution, not held fixed. F06 (2026-06-10): the contrast CI comes
from a single JOINT cluster resample over the union regime universe of both bins,
capturing cross-bin covariance where a regime spans bins.

TRAIN containment: an event is included iff ``completion_idx <= train_cutoff_idx``
(the BTC lifetime completes inside TRAIN). TEST and the global holdout are never read.

Run:
    cd <project-root> && python python/experiments/EXP-035/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]

from xen.financing import (  # noqa: E402
    NS_PER_DAY,
    elapsed_calendar_days,
    financing_bps,
    verify_financing,
)
from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)

# Frozen EXP-027 inference tail — imported directly from the canonical file.
EXP027_METHOD = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "code" / "event_method.py"


def _load_module(name: str, path: Path):
    """Import a module by file path without executing any ``main`` guard."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EM = _load_module("exp027_event_method", EXP027_METHOD)
from exp027_event_method import (  # noqa: E402
    bootstrap_effect_distribution,
    build_strata,
    holm_adjust,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-035"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")
DIMENSIONS: tuple[str, ...] = ("c1_completion", "c2_session", "c3_vol")
ORDERED_DIMENSIONS: tuple[str, ...] = ("c1_completion", "c3_vol")

TRAIN_FRACTION = 0.7

# FROZEN EXP-030 CONSERVATIVE costs + predeclared financing (bps; bps/day).
RT_CONS_BPS: dict[str, float] = {"EURUSD": 3.0, "USTEC": 5.0, "XAUUSD": 6.0, "BTCUSD": 16.0}
FINANCING_RATE_BPS_PER_DAY: dict[str, float] = {
    "EURUSD": 0.6, "USTEC": 1.2, "XAUUSD": 1.2, "BTCUSD": 10.0,
}

# G1 gate constants (design §8.1; frozen).
ALPHA_G1 = 0.10
SNR_FLOOR = 1.0

# C3 covariate constants (scope; frozen).
ATR_PERIOD = 14
VOL_WINDOW_DAYS = 90
VOL_MIN_HISTORY_DAYS = 30

# Session bins (UTC hour of trigger CloseTime).
SESSIONS: tuple[str, ...] = ("asia", "london", "ny")

# Reportability floors per domain (any unreportable bin -> G1-ineligible).
BIN_FLOOR: dict[str, int] = {"5m": 30, "1h": 30, "4h": 15}
# Composition-skew disclosure: one instrument > this share of a bin.
SKEW_SHARE = 0.5

# EXP-028 PRIMARY population construction (identical to EXP-030/034).
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
JOIN_KEYS = ("instrument", "domain", "regime_id", "direction", "event_trigger_idx")
MIN_CONTROLS = EM.MIN_CONTROLS

# Inference convention.
N_BOOT = 1000
N_PERM = 1000
CHUNK = 200
CI_PERCENTILES = (2.5, 97.5)

DETERMINISM_TOL = 1e-12
START_CLOSE_RTOL = 1e-9

FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")


def ensure_output_dirs() -> None:
    """Create ``results/`` and ``plots/`` (orchestration-time only)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    """Read a JSON metadata file (raises if absent)."""
    if not path.exists():
        raise FileNotFoundError(f"missing run metadata: {path}")
    return json.loads(path.read_text())


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dict rows to CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


def ensure_bool(frame: pl.DataFrame, columns: tuple[str, ...]) -> pl.DataFrame:
    """Cast CSV-loaded ``true``/``false`` columns to Boolean (Polars may infer Utf8)."""
    exprs = []
    for col in columns:
        if col not in frame.columns:
            continue
        if frame.schema[col] == pl.Utf8:
            exprs.append((pl.col(col).str.to_lowercase() == "true").alias(col))
        else:
            exprs.append(pl.col(col).cast(pl.Boolean))
    return frame.with_columns(exprs) if exprs else frame


# --------------------------------------------------------------------------- #
# Integrity guards
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the imported inference tail matches the PINNED EXP-027 source hash."""
    used_src = []
    for name in FROZEN_FUNCTIONS:
        used_fn = getattr(EM, name, None)
        if used_fn is None:
            raise ValueError(f"FROZEN_INFERENCE_MODIFIED: function {name} missing")
        used_src.append(inspect.getsource(used_fn))
    h_used = hashlib.sha256("".join(used_src).encode()).hexdigest()[:16]
    if h_used != FROZEN_TAIL_EXPECTED_HASH:
        raise ValueError(
            f"FROZEN_INFERENCE_MODIFIED: inference tail diverges from the pinned "
            f"EXP-027/028 source (got {h_used} != pinned {FROZEN_TAIL_EXPECTED_HASH})."
        )
    LOGGER.info("Frozen inference tail verified against pinned EXP-027 hash (%s)", h_used)
    return h_used


def check_dependencies() -> dict[str, str]:
    """Assert EXP-028 EVAL_SUPPORTED and required upstream artifacts exist."""
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    v028 = str(exp028.get("overall_verdict", ""))
    if v028 != "EVAL_SUPPORTED":
        raise ValueError(f"EXP-028 overall_verdict must be EVAL_SUPPORTED, got {v028!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP020_RESULTS / "avwap_events.csv",
                     EXP020_RESULTS / "analysis_metadata.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-028=%s)", v028)
    return {"EXP-028": v028, "EXP-022": "present", "EXP-020": "present"}


# --------------------------------------------------------------------------- #
# Domain rebuild (OHLC + CloseTime) + metadata guard
# --------------------------------------------------------------------------- #
def expected_timebar_sources() -> set[str]:
    """Canonical source Parquet filenames recorded by EXP-020 metadata."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    return set(expected.get_column("source_file").unique().to_list())


def build_cell_series() -> tuple[dict[tuple[str, str], dict[str, np.ndarray]], list[dict[str, Any]]]:
    """Rebuild first-70% domain bars; return per-cell OHLC + CloseTime arrays.

    High/Low are needed here (unlike EXP-033/034) for the ATR(14) covariate.
    """
    expected_sources = expected_timebar_sources()
    files = [path for path in list_timebar_files(DATA_DIR) if path.name in expected_sources]
    missing = sorted(expected_sources.difference({path.name for path in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    series: dict[tuple[str, str], dict[str, np.ndarray]] = {}
    metadata_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            series[(data.instrument, domain)] = {
                "close": frame.get_column("Close").to_numpy().astype(float),
                "high": frame.get_column("High").to_numpy().astype(float),
                "low": frame.get_column("Low").to_numpy().astype(float),
                "close_time_ns":
                    frame.get_column("CloseTime").to_numpy().astype("datetime64[ns]")
                    .astype(np.int64),
            }
            metadata_rows.append({
                "instrument": data.instrument, "domain": domain,
                "source_file": data.source_file,
                "analysis_rows_1m": data.analysis_rows,
                "domain_bars": frame.height,
                "domain_max_close_time": str(frame.get_column("CloseTime").max()),
            })
    return series, metadata_rows


def validate_analysis_metadata(metadata_rows: list[dict[str, Any]]) -> None:
    """Hard-fail if the reconstructed domain bars diverge from EXP-020 analysis metadata."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    expected_by_cell = {(str(r["instrument"]), str(r["domain"])): r for r in expected.to_dicts()}
    failures = []
    for row in metadata_rows:
        cell = (str(row["instrument"]), str(row["domain"]))
        exp = expected_by_cell.get(cell)
        if exp is None:
            failures.append(f"{cell[0]}/{cell[1]} (missing)")
            continue
        ok = (row["source_file"] == exp["source_file"]
              and int(row["analysis_rows_1m"]) == int(exp["analysis_rows_1m"])
              and int(row["domain_bars"]) == int(exp["domain_bars"])
              and str(row["domain_max_close_time"]) == str(exp["domain_max_close_time"]))
        if not ok:
            failures.append(f"{cell[0]}/{cell[1]}")
    if failures:
        raise ValueError(f"EXP-020 analysis metadata mismatch (domain rebuild diverged): {failures}")
    LOGGER.info("Domain rebuild matches EXP-020 metadata for %d cells", len(metadata_rows))


# --------------------------------------------------------------------------- #
# Covariates: ATR percentile (C3) — causal, calendar-window
# --------------------------------------------------------------------------- #
def atr_series(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Wilder ATR(ATR_PERIOD) per bar (standard true range; NaN until seeded).

    Sequential by definition (Wilder smoothing is a recurrence); the loop is bounded
    by the domain bar count and runs once per cell.
    """
    n = close.size
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev_close = close[:-1]
    tr[1:] = np.maximum.reduce([
        high[1:] - low[1:],
        np.abs(high[1:] - prev_close),
        np.abs(low[1:] - prev_close),
    ])
    atr = np.full(n, np.nan)
    if n <= ATR_PERIOD:
        return atr
    atr[ATR_PERIOD] = tr[1 : ATR_PERIOD + 1].mean()
    for i in range(ATR_PERIOD + 1, n):
        atr[i] = (atr[i - 1] * (ATR_PERIOD - 1) + tr[i]) / ATR_PERIOD
    return atr


def trailing_percentile(values: np.ndarray, times_ns: np.ndarray,
                        window_days: int, min_history_days: int) -> np.ndarray:
    """Percentile rank of values[i] within the trailing calendar window (strictly causal).

    Window = bars j with ``times[j] in (times[i] - window_days, times[i]]`` and finite
    values[j]; the current bar is included (its value is known at its own CloseTime).
    NaN where the available history span is < min_history_days or the window holds < 2
    finite values. Two-pointer sweep (O(n) amortized window maintenance with a sorted
    rank query per bar, bounded by the window size).
    """
    n = values.size
    out = np.full(n, np.nan)
    window_ns = window_days * NS_PER_DAY
    min_hist_ns = min_history_days * NS_PER_DAY
    left = 0
    import bisect
    window_sorted: list[float] = []
    window_queue: list[tuple[int, float]] = []  # (bar index, value) in arrival order
    for i in range(n):
        v = values[i]
        if np.isfinite(v):
            bisect.insort(window_sorted, v)
            window_queue.append((i, v))
        lo_bound = times_ns[i] - window_ns
        while window_queue and times_ns[window_queue[0][0]] <= lo_bound:
            _idx, old = window_queue.pop(0)
            pos = bisect.bisect_left(window_sorted, old)
            window_sorted.pop(pos)
        if not np.isfinite(v):
            continue
        first_finite_ns = times_ns[window_queue[0][0]]
        if times_ns[i] - first_finite_ns < min_hist_ns:
            continue
        m = len(window_sorted)
        if m < 2:
            continue
        rank = bisect.bisect_left(window_sorted, v)
        out[i] = rank / (m - 1)
    return out


# --------------------------------------------------------------------------- #
# Tidy frame construction (events + covariates + net outcome)
# --------------------------------------------------------------------------- #
def build_event_table(lifetime: pl.DataFrame) -> pl.DataFrame:
    """EXP-028/030 PRIMARY event set, retaining indices for joins and financing."""
    lifetime = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lifetime.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES)
                         & pl.col("lifetime_bps").is_not_null())
    keys = list(JOIN_KEYS)
    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_n = controls.group_by(keys).agg(pl.len().alias("n_controls_finite"))
    merged = events.join(ctrl_n, on=keys, how="inner").filter(
        pl.col("n_controls_finite") >= MIN_CONTROLS)
    return merged.select(
        "instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
        "start_idx", "completion_idx", "start_close", "lifetime_bps",
    )


def join_band_geometry(events: pl.DataFrame) -> pl.DataFrame:
    """1:1 join to EXP-020 ``avwap_events.csv`` for at-trigger band geometry + trigger time.

    Join key: (instrument, domain, regime_id, trigger_idx == start_idx, pyramid flag).
    Zero unmatched events is a hard assert (unmatched = data defect, not a filter).
    """
    av = pl.read_csv(EXP020_RESULTS / "avwap_events.csv", try_parse_dates=True)
    av = ensure_bool(av, ("is_pyramid_bounce",))
    av = av.select(
        "instrument", "domain", "regime_id", "is_pyramid_bounce",
        pl.col("trigger_idx").alias("start_idx"),
        "trigger_time", "trigger_close", "band_spread_at_trigger",
        "favorable_target_at_trigger",
    )
    n_before = events.height
    joined = events.join(
        av, on=["instrument", "domain", "regime_id", "start_idx", "is_pyramid_bounce"],
        how="inner")
    if joined.height != n_before:
        raise ValueError(
            f"band-geometry join not 1:1: {n_before} events -> {joined.height} rows "
            "(unmatched or duplicated EXP-020 event rows)")
    return joined


def attach_outcome_and_covariates(
    events: pl.DataFrame, series: dict[tuple[str, str], dict[str, np.ndarray]],
    cutoffs: dict[tuple[str, str], int],
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Attach net outcome, C1/C2/C3 covariates, and apply TRAIN containment.

    Returns the tidy TRAIN frame and per-domain accounting (containment + C3 history
    exclusions). All covariates are strictly at-or-before the trigger timestamp.
    """
    si = events.get_column("start_idx").to_numpy().astype(np.int64)
    ci = events.get_column("completion_idx").to_numpy().astype(np.int64)
    sc = events.get_column("start_close").to_numpy().astype(float)
    inst = events.get_column("instrument").to_numpy()
    dom = events.get_column("domain").to_numpy()
    n = events.height
    entry_ns = np.full(n, np.int64(0))
    exit_ns = np.full(n, np.int64(0))
    atr_pct = np.full(n, np.nan)
    in_train = np.zeros(n, dtype=bool)
    base_bad = 0
    for (i, dm), arrs in tqdm(series.items(), desc="covariates", total=len(series)):
        rows = np.flatnonzero((inst == i) & (dom == dm))
        if rows.size == 0:
            continue
        close, high, low = arrs["close"], arrs["high"], arrs["low"]
        ct = arrs["close_time_ns"]
        s, c = si[rows], ci[rows]
        if (s < 0).any() or (s >= close.size).any() or (c < 0).any() or (c >= close.size).any():
            raise ValueError(f"index out of analysis-slice range for {i}/{dm}")
        tol = START_CLOSE_RTOL * sc[rows]
        base_bad += int(np.sum(np.abs(close[s] - sc[rows]) > tol))
        entry_ns[rows] = ct[s]
        exit_ns[rows] = ct[c]
        atr = atr_series(high, low, close)
        pct = trailing_percentile(atr, ct, VOL_WINDOW_DAYS, VOL_MIN_HISTORY_DAYS)
        atr_pct[rows] = pct[s]
        in_train[rows] = c <= cutoffs[(i, dm)]
    if base_bad:
        raise ValueError(f"start_close mismatch vs rebuilt base bar in {base_bad} rows")

    # Shared live path (F03): durations and financing via xen.financing helpers.
    entry_dt = entry_ns.astype("datetime64[ns]")
    exit_dt = exit_ns.astype("datetime64[ns]")
    rates = np.array([FINANCING_RATE_BPS_PER_DAY[i] for i in inst], dtype=float)
    rt = np.array([RT_CONS_BPS[i] for i in inst], dtype=float)
    holding_days = elapsed_calendar_days(entry_dt, exit_dt)
    lifetime_bps = events.get_column("lifetime_bps").to_numpy().astype(float)
    net = lifetime_bps - rt - financing_bps(rates, entry_dt, exit_dt)
    trigger_ns = entry_ns

    # C1 from band geometry (direction-signed remaining favorable distance).
    d = events.get_column("direction").to_numpy().astype(float)
    fav = events.get_column("favorable_target_at_trigger").to_numpy().astype(float)
    tc = events.get_column("trigger_close").to_numpy().astype(float)
    spread = events.get_column("band_spread_at_trigger").to_numpy().astype(float)
    if np.any(spread <= 0):
        raise ValueError("non-positive band_spread_at_trigger (C1 denominator)")
    c1 = 1.0 - d * (fav - tc) / spread

    # C2 from trigger CloseTime UTC hour.
    hour = ((trigger_ns // (3600 * 1_000_000_000)) % 24).astype(int)
    c2 = np.where(hour < 8, "asia", np.where(hour < 16, "london", "ny"))

    out = events.with_columns([
        pl.Series("net", net), pl.Series("holding_days", holding_days),
        pl.Series("c1", c1), pl.Series("c2", c2), pl.Series("c3", atr_pct),
        pl.Series("trigger_ns", trigger_ns), pl.Series("in_train", in_train),
    ])
    accounting = []
    for domain in DOMAINS:
        sub = out.filter(pl.col("domain") == domain)
        train = sub.filter(pl.col("in_train"))
        accounting.append({
            "domain": domain, "n_events_analysis": sub.height,
            "n_events_train": train.height,
            "excluded_containment": sub.height - train.height,
            "c3_missing_history": int(train.filter(~pl.col("c3").is_finite()).height),
        })
    return out.filter(pl.col("in_train")).drop("in_train"), accounting


# --------------------------------------------------------------------------- #
# Binning (frozen TRAIN terciles + fixed sessions) and floors
# --------------------------------------------------------------------------- #
def assign_bins(train: pl.DataFrame) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Assign per-domain bins for all three dimensions; record tercile boundaries.

    C1/C3: TRAIN-quantile terciles pooled per domain (boundaries frozen on emission).
    C2: fixed sessions. Returns (frame with bin columns, boundary rows).
    """
    boundary_rows: list[dict[str, Any]] = []
    frames = []
    for domain in DOMAINS:
        sub = train.filter(pl.col("domain") == domain)
        exprs = []
        for dim, col in (("c1_completion", "c1"), ("c3_vol", "c3")):
            vals = sub.get_column(col).to_numpy().astype(float)
            finite = vals[np.isfinite(vals)]
            if finite.size < 3:
                exprs.append(pl.lit(None, dtype=pl.Utf8).alias(f"bin_{dim}"))
                continue
            q1, q2 = np.quantile(finite, [1 / 3, 2 / 3])
            boundary_rows.append({"domain": domain, "dimension": dim,
                                  "q33": float(q1), "q67": float(q2),
                                  "n_finite": int(finite.size)})
            exprs.append(
                pl.when(~pl.col(col).is_finite()).then(pl.lit(None, dtype=pl.Utf8))
                .when(pl.col(col) <= q1).then(pl.lit("low"))
                .when(pl.col(col) <= q2).then(pl.lit("mid"))
                .otherwise(pl.lit("high")).alias(f"bin_{dim}"))
        exprs.append(pl.col("c2").alias("bin_c2_session"))
        frames.append(sub.with_columns(exprs))
    return pl.concat(frames, how="vertical"), boundary_rows


def covariate_summary(train: pl.DataFrame) -> list[dict[str, Any]]:
    """Predeclared covariate disclosures per domain (plan Step 1; F06).

    Includes the C1 distribution and its share outside [0, 1] (C1 is mechanically
    coupled to remaining-move size — this table is the auditability record for
    that coupling), C3 finite-history coverage, and session counts.
    """
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        sub = train.filter(pl.col("domain") == domain)
        c1 = sub.get_column("c1").to_numpy().astype(float)
        c3 = sub.get_column("c3").to_numpy().astype(float)
        c2 = sub.get_column("c2").to_numpy()
        n = c1.size
        if n == 0:
            rows.append({"domain": domain, "n_events": 0})
            continue
        rows.append({
            "domain": domain, "n_events": n,
            "c1_mean": float(np.mean(c1)), "c1_p5": float(np.percentile(c1, 5)),
            "c1_median": float(np.median(c1)), "c1_p95": float(np.percentile(c1, 95)),
            "c1_share_below_0": float(np.mean(c1 < 0.0)),
            "c1_share_above_1": float(np.mean(c1 > 1.0)),
            "c3_finite_share": float(np.mean(np.isfinite(c3))),
            "n_asia": int(np.sum(c2 == "asia")),
            "n_london": int(np.sum(c2 == "london")),
            "n_ny": int(np.sum(c2 == "ny")),
        })
    return rows


def bin_labels(dim: str) -> list[str]:
    """Ordered bin labels for a dimension."""
    return ["low", "mid", "high"] if dim in ORDERED_DIMENSIONS else list(SESSIONS)


def bin_stats(train: pl.DataFrame, domain: str, dim: str) -> list[dict[str, Any]]:
    """Per-bin n, mean net, instrument composition + floor/skew flags."""
    sub = train.filter((pl.col("domain") == domain) & pl.col(f"bin_{dim}").is_not_null())
    rows = []
    floor = BIN_FLOOR[domain]
    for b in bin_labels(dim):
        binned = sub.filter(pl.col(f"bin_{dim}") == b)
        n = binned.height
        comp = (binned.group_by("instrument").agg(pl.len().alias("n"))
                .sort("n", descending=True))
        top_share = (comp["n"][0] / n) if n else 0.0
        rows.append({
            "domain": domain, "dimension": dim, "bin": b, "n_events": n,
            "mean_net_bps": float(binned.get_column("net").mean()) if n else None,
            "reportable": n >= floor,
            "top_instrument": comp["instrument"][0] if n else None,
            "top_instrument_share": float(top_share),
            "composition_skewed": bool(top_share > SKEW_SHARE),
        })
    return rows


# --------------------------------------------------------------------------- #
# Inference: cluster-bootstrap contrast, permutation p, split-half stability
# --------------------------------------------------------------------------- #
def _mean_net(diffs: np.ndarray) -> float:
    """Pooled event-weighted mean (the bin statistic; instruments pooled per plan)."""
    return float(diffs.mean()) if diffs.size else float("nan")


def _joint_contrast_bootstrap(sub_a: pl.DataFrame, sub_b: pl.DataFrame,
                              rng: np.random.Generator) -> np.ndarray:
    """Joint regime-cluster bootstrap distribution of mean_net(a) - mean_net(b).

    F06: regime clusters are resampled ONCE per replicate within each (instrument,
    direction) stratum over the UNION regime universe of the two bins, and both
    pooled bin means are formed from the same resampled clusters — capturing the
    cross-bin covariance that arises when a regime spans both bins (two independent
    bin bootstraps would mis-scale the contrast CI, the SNR denominator).
    """
    def _arrays(s: pl.DataFrame) -> tuple[np.ndarray, ...]:
        return (s.get_column("net").to_numpy().astype(float),
                s.get_column("instrument").to_numpy(),
                s.get_column("direction").to_numpy().astype(int),
                s.get_column("regime_id").to_numpy().astype(int))

    na, ia, da, ra = _arrays(sub_a)
    nb, ib, db, rb = _arrays(sub_b)
    num_a, den_a = np.zeros(N_BOOT), np.zeros(N_BOOT)
    num_b, den_b = np.zeros(N_BOOT), np.zeros(N_BOOT)
    strata_keys = sorted({(str(i), int(d)) for i, d in zip(ia, da)}
                         | {(str(i), int(d)) for i, d in zip(ib, db)})
    for inst, d in strata_keys:
        ma = (ia == inst) & (da == d)
        mb = (ib == inst) & (db == d)
        regs = np.unique(np.concatenate([ra[ma], rb[mb]])) if (ma.any() or mb.any()) \
            else np.empty(0, dtype=int)
        r = regs.size
        if r == 0:
            continue
        sum_a = np.zeros(r)
        cnt_a = np.zeros(r)
        if ma.any():
            inv = np.searchsorted(regs, ra[ma])
            sum_a = np.bincount(inv, weights=na[ma], minlength=r)
            cnt_a = np.bincount(inv, minlength=r).astype(float)
        sum_b = np.zeros(r)
        cnt_b = np.zeros(r)
        if mb.any():
            inv = np.searchsorted(regs, rb[mb])
            sum_b = np.bincount(inv, weights=nb[mb], minlength=r)
            cnt_b = np.bincount(inv, minlength=r).astype(float)
        for start in range(0, N_BOOT, CHUNK):
            size = min(CHUNK, N_BOOT - start)
            sel = rng.integers(0, r, size=(size, r))
            num_a[start:start + size] += sum_a[sel].sum(axis=1)
            den_a[start:start + size] += cnt_a[sel].sum(axis=1)
            num_b[start:start + size] += sum_b[sel].sum(axis=1)
            den_b[start:start + size] += cnt_b[sel].sum(axis=1)
    mean_a = np.divide(num_a, den_a, out=np.full(N_BOOT, np.nan), where=den_a > 0)
    mean_b = np.divide(num_b, den_b, out=np.full(N_BOOT, np.nan), where=den_b > 0)
    return mean_a - mean_b


def contrast_inference(train: pl.DataFrame, domain: str, dim: str,
                       stats_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Materiality contrast + permutation p for one domain x dimension.

    Ordered dims: Delta = top - bottom tercile pooled mean, one-sided permutation on
    Delta. Session: candidate = max-net bin, contrast = candidate vs rest, omnibus =
    max pairwise |difference| permutation. Labels permuted within (instrument,
    direction) strata. Bootstrap CI on the contrast from independent cluster
    bootstraps of the two bin means (difference of independent cluster resamples —
    bins partition distinct events, sharing no regime rows across bins only when a
    regime spans bins; the stratified label permutation is the primary null device
    and the CI is the materiality yardstick).
    """
    sub = train.filter((pl.col("domain") == domain) & pl.col(f"bin_{dim}").is_not_null())
    by_bin = {r["bin"]: r for r in stats_rows}
    labels = bin_labels(dim)
    means = {b: by_bin[b]["mean_net_bps"] for b in labels}
    if any(means[b] is None for b in labels):
        return {"eligible": False, "reason": "empty bin"}
    if dim in ORDERED_DIMENSIONS:
        top_bin, bottom_bin = "high", "low"
        # Predeclared direction: contrast is |top - bottom| with the candidate being
        # the better-net end; monotonicity is weak ordering in either direction.
        if means["high"] >= means["low"]:
            candidate, anti = "high", "low"
        else:
            candidate, anti = "low", "high"
        delta = means[candidate] - means[anti]
        mono = (means["low"] <= means["mid"] <= means["high"]
                or means["low"] >= means["mid"] >= means["high"])
    else:
        candidate = max(labels, key=lambda b: means[b])
        anti = None
        rest = sub.filter(pl.col(f"bin_{dim}") != candidate)
        delta = means[candidate] - float(rest.get_column("net").mean())
        mono = True  # structure leg for sessions is the omnibus test, set below
    # Joint cluster-bootstrap CI on the contrast (F06: one resample, both bins).
    rng_j = np.random.default_rng(seed_for(EXPERIMENT_ID, "boot", domain, dim, "joint"))
    sub_cand = sub.filter(pl.col(f"bin_{dim}") == candidate)
    sub_anti = (sub.filter(pl.col(f"bin_{dim}") == anti) if dim in ORDERED_DIMENSIONS
                else sub.filter(pl.col(f"bin_{dim}") != candidate))
    boot_delta = _joint_contrast_bootstrap(sub_cand, sub_anti, rng_j)
    ci_low = float(np.nanpercentile(boot_delta, CI_PERCENTILES[0]))
    ci_high = float(np.nanpercentile(boot_delta, CI_PERCENTILES[1]))
    half_width = (ci_high - ci_low) / 2.0
    snr = abs(delta) / half_width if half_width > 0 else float("inf")

    # Stratified label permutation (F05: selection-aware statistic).
    perm_p, omnibus_p = _permutation_tests(sub, dim, domain)
    if dim not in ORDERED_DIMENSIONS:
        mono = bool(omnibus_p <= ALPHA_G1)

    return {
        "eligible": True, "candidate_bin": candidate,
        "delta_bps": float(delta), "delta_ci_low": ci_low, "delta_ci_high": ci_high,
        "ci_half_width": half_width, "snr": float(snr),
        "candidate_mean_net_bps": means[candidate],
        "material": bool(snr >= SNR_FLOOR and means[candidate] > 0),
        "structured": bool(mono), "perm_p": perm_p, "omnibus_p": omnibus_p,
    }


def _permutation_tests(sub: pl.DataFrame, dim: str, domain: str) -> tuple[float, float | None]:
    """Selection-aware contrast permutation p (+ omnibus p for sessions).

    Bin labels are permuted within (instrument, direction) strata. F05: because the
    observed candidate bin is data-selected (the better-net tercile end for ordered
    dims; the argmax session), the permutation statistic RE-SELECTS by the same max
    rule inside every permutation — ordered dims: ``|mean(high) - mean(low)|``;
    sessions: ``max_b(mean_b - mean_rest_b)``. Holding the observed candidate fixed
    under the null would be anti-conservative (~2x for ordered dims, more for
    sessions). The omnibus session statistic (max - min of bin means) was already
    selection-aware.
    """
    net = sub.get_column("net").to_numpy().astype(float)
    bins = sub.get_column(f"bin_{dim}").to_numpy()
    inst = sub.get_column("instrument").to_numpy()
    direction = sub.get_column("direction").to_numpy().astype(int)
    strata_ids = np.unique(np.char.add(inst.astype(str), direction.astype(str)),
                           return_inverse=True)[1]
    labels = bin_labels(dim)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "perm", domain, dim))

    def contrast_stat(b: np.ndarray) -> float:
        if dim in ORDERED_DIMENSIONS:
            hi_mask = b == "high"
            lo_mask = b == "low"
            if not hi_mask.any() or not lo_mask.any():
                return float("nan")
            return float(abs(net[hi_mask].mean() - net[lo_mask].mean()))
        best = -np.inf
        for lb in labels:
            m = b == lb
            if not m.any() or m.all():
                continue
            best = max(best, float(net[m].mean() - net[~m].mean()))
        return best if np.isfinite(best) else float("nan")

    def omnibus_stat(b: np.ndarray) -> float:
        ms = [net[b == lb].mean() for lb in labels if (b == lb).any()]
        if len(ms) < 2:
            return float("nan")
        return float(max(ms) - min(ms))

    obs_contrast = contrast_stat(bins)
    obs_omnibus = omnibus_stat(bins)
    ge_contrast = 0
    ge_omnibus = 0
    perm = bins.copy()
    for _k in range(N_PERM):
        for s in np.unique(strata_ids):
            mask = strata_ids == s
            perm[mask] = rng.permutation(perm[mask])
        cs = contrast_stat(perm)
        if np.isfinite(cs) and cs >= obs_contrast:
            ge_contrast += 1
        os_ = omnibus_stat(perm)
        if np.isfinite(os_) and os_ >= obs_omnibus:
            ge_omnibus += 1
    perm_p = (1 + ge_contrast) / (1 + N_PERM)
    omnibus_p = (1 + ge_omnibus) / (1 + N_PERM) if dim not in ORDERED_DIMENSIONS else None
    return perm_p, omnibus_p


def split_half_stability(train: pl.DataFrame, domain: str, dim: str,
                         candidate: str) -> dict[str, Any]:
    """Chronological split-half check with frozen full-TRAIN bins (plan Step 5)."""
    sub = train.filter((pl.col("domain") == domain) & pl.col(f"bin_{dim}").is_not_null())
    med = float(sub.get_column("trigger_ns").median())
    halves = {"h1": sub.filter(pl.col("trigger_ns") <= med),
              "h2": sub.filter(pl.col("trigger_ns") > med)}
    labels = bin_labels(dim)
    out: dict[str, Any] = {}
    stable_bin, stable_delta = True, True
    for name, half in halves.items():
        means = {}
        for b in labels:
            cell = half.filter(pl.col(f"bin_{dim}") == b)
            means[b] = float(cell.get_column("net").mean()) if cell.height else float("nan")
        finite = {b: m for b, m in means.items() if np.isfinite(m)}
        if not finite:
            return {"stable": False, "reason": f"{name} empty"}
        top = max(finite, key=lambda b: finite[b])
        if dim in ORDERED_DIMENSIONS:
            anti = "low" if candidate == "high" else "high"
            delta = means.get(candidate, np.nan) - means.get(anti, np.nan)
        else:
            rest = half.filter(pl.col(f"bin_{dim}") != candidate)
            delta = (means.get(candidate, np.nan)
                     - (float(rest.get_column("net").mean()) if rest.height else np.nan))
        out[f"{name}_top_bin"] = top
        out[f"{name}_delta_bps"] = float(delta) if np.isfinite(delta) else None
        stable_bin = stable_bin and (top == candidate)
        stable_delta = stable_delta and bool(np.isfinite(delta) and delta > 0)
    out["stable"] = bool(stable_bin and stable_delta)
    return out


# --------------------------------------------------------------------------- #
# G1 qualification assembly (reads emitted sub-criteria only)
# --------------------------------------------------------------------------- #
def assemble_qualification(
    char_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Holm across the 3 dimensions per domain; assemble the conjunction flag."""
    out: list[dict[str, Any]] = []
    for domain in DOMAINS:
        dom_rows = [r for r in char_rows if r["domain"] == domain]
        pvals = {r["dimension"]: r["perm_p"] for r in dom_rows
                 if r.get("floor_eligible") and r.get("eligible")}
        adjusted = holm_adjust(pvals) if pvals else {}
        for r in dom_rows:
            holm_p = adjusted.get(r["dimension"])
            multiplicity = bool(holm_p is not None and holm_p <= ALPHA_G1)
            qualified = bool(
                r.get("floor_eligible") and r.get("eligible")
                and r.get("material") and r.get("structured")
                and r.get("stable") and multiplicity)
            out.append({
                "domain": domain, "dimension": r["dimension"],
                "floor_eligible": r.get("floor_eligible"),
                "candidate_bin": r.get("candidate_bin"),
                "delta_bps": r.get("delta_bps"), "snr": r.get("snr"),
                "candidate_mean_net_bps": r.get("candidate_mean_net_bps"),
                "material_i": r.get("material"), "structured_ii": r.get("structured"),
                "stable_iii": r.get("stable"), "perm_p": r.get("perm_p"),
                "holm_p": holm_p, "multiplicity_iv": multiplicity,
                "qualified": qualified,
            })
    return out


# --------------------------------------------------------------------------- #
# Determinism replay
# --------------------------------------------------------------------------- #
def determinism_replay(train: pl.DataFrame, char_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-run one domain x dimension contrast with original seeds; assert identity."""
    ref = next((r for r in char_rows
                if r["domain"] == "5m" and r["dimension"] == "c1_completion"
                and r.get("eligible")), None)
    if ref is None:
        return {"cell": "5m/c1_completion", "max_drift": None, "passed": True,
                "note": "reference cell ineligible; replay skipped"}
    stats = [r for r in ref["_stats_rows"]] if "_stats_rows" in ref else None
    replay = contrast_inference(train, "5m", "c1_completion",
                                stats or bin_stats(train, "5m", "c1_completion"))
    drift = max(abs(replay["delta_bps"] - ref["delta_bps"]),
                abs(replay["delta_ci_low"] - ref["delta_ci_low"]),
                abs(replay["perm_p"] - ref["perm_p"]))
    return {"cell": "5m/c1_completion", "max_drift": drift,
            "passed": bool(drift <= DETERMINISM_TOL)}


# --------------------------------------------------------------------------- #
# Plotting (5)
# --------------------------------------------------------------------------- #
def _plot_dimension(stats_all: list[dict[str, Any]], dim: str, title: str,
                    path: Path) -> None:
    """Bin mean net with floors flagged, per domain, for one dimension."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(5 * len(DOMAINS), 4.2))
    labels = bin_labels(dim)
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        rows = [r for r in stats_all if r["domain"] == domain and r["dimension"] == dim]
        by_bin = {r["bin"]: r for r in rows}
        xs = np.arange(len(labels))
        for k, b in enumerate(labels):
            r = by_bin.get(b)
            if r is None or r["mean_net_bps"] is None:
                continue
            color = "#3498db" if r["reportable"] else "#c0392b"
            hatch = "//" if r["composition_skewed"] else None
            ax.bar(k, r["mean_net_bps"], color=color, hatch=hatch, width=0.6)
            ax.annotate(f"n={r['n_events']}", (k, r["mean_net_bps"]),
                        textcoords="offset points", xytext=(0, 4), ha="center", fontsize=7)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels)
        ax.set_title(domain)
        ax.set_ylabel("Mean net (bps)")
    fig.suptitle(title + " (red = below floor; hatched = composition-skewed)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_stability(qual_rows: list[dict[str, Any]], char_rows: list[dict[str, Any]],
                   path: Path) -> None:
    """Split-half Delta per domain x dimension (instability visible at a glance)."""
    fig, ax = plt.subplots(figsize=(10, 5))
    xs, h1s, h2s, ticklabels = [], [], [], []
    k = 0
    for r in char_rows:
        if not r.get("eligible"):
            continue
        xs.append(k)
        h1s.append(r.get("h1_delta_bps"))
        h2s.append(r.get("h2_delta_bps"))
        ticklabels.append(f"{r['domain']}\n{r['dimension'].split('_')[0]}")
        k += 1
    xs_arr = np.array(xs, dtype=float)
    ax.bar(xs_arr - 0.18, [v if v is not None else np.nan for v in h1s], 0.36,
           label="TRAIN half 1", color="#3498db")
    ax.bar(xs_arr + 0.18, [v if v is not None else np.nan for v in h2s], 0.36,
           label="TRAIN half 2", color="#e67e22")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(xs)
    ax.set_xticklabels(ticklabels, fontsize=7)
    ax.set_ylabel("Contrast Delta (bps)")
    ax.set_title("EXP-035 split-half stability (same-sign positive Delta required)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_qualification_matrix(qual_rows: list[dict[str, Any]], path: Path) -> None:
    """Domain x dimension grid coloring each §8.1 sub-criterion and the final flag."""
    criteria = ("floor_eligible", "material_i", "structured_ii", "stable_iii",
                "multiplicity_iv", "qualified")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    n_rows = len(DOMAINS) * len(DIMENSIONS)
    grid = np.full((n_rows, len(criteria)), np.nan)
    ylabels = []
    r_idx = 0
    for domain in DOMAINS:
        for dim in DIMENSIONS:
            row = next((r for r in qual_rows
                        if r["domain"] == domain and r["dimension"] == dim), None)
            ylabels.append(f"{domain} / {dim}")
            if row is not None:
                for c_idx, c in enumerate(criteria):
                    v = row.get(c)
                    grid[r_idx, c_idx] = 1.0 if v else 0.0 if v is not None else np.nan
            r_idx += 1
    im = ax.imshow(grid, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(criteria)))
    ax.set_xticklabels(criteria, fontsize=7, rotation=20)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(ylabels, fontsize=7)
    ax.set_title("EXP-035 G1 qualification matrix (green = pass)")
    fig.colorbar(im, shrink=0.6)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-035 conditioning characterisation end to end."""
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s: TRAIN-only conditioning characterisation ===", EXPERIMENT_ID)

    frozen_hash = verify_frozen_inference()
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    deps = check_dependencies()

    series, metadata_rows = build_cell_series()
    validate_analysis_metadata(metadata_rows)
    cutoffs = {cell: int(np.floor(TRAIN_FRACTION * arrs["close"].size))
               for cell, arrs in series.items()}

    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    events = build_event_table(lifetime)
    events = join_band_geometry(events)
    train, accounting = attach_outcome_and_covariates(events, series, cutoffs)
    LOGGER.info("TRAIN population: %s",
                {d: train.filter(pl.col('domain') == d).height for d in DOMAINS})

    train, boundary_rows = assign_bins(train)

    stats_all: list[dict[str, Any]] = []
    char_rows: list[dict[str, Any]] = []
    cells = [(d, dim) for d in DOMAINS for dim in DIMENSIONS]
    for domain, dim in tqdm(cells, desc="characterisation"):
        stats_rows = bin_stats(train, domain, dim)
        stats_all.extend(stats_rows)
        floor_eligible = all(r["reportable"] for r in stats_rows)
        rec: dict[str, Any] = {"domain": domain, "dimension": dim,
                               "floor_eligible": floor_eligible}
        inf = contrast_inference(train, domain, dim, stats_rows)
        rec.update(inf)
        if inf.get("eligible"):
            rec.update(split_half_stability(train, domain, dim, inf["candidate_bin"]))
        char_rows.append(rec)

    qual_rows = assemble_qualification(char_rows)
    replay = determinism_replay(train, char_rows)
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # ---- persist results -----------------------------------------------------
    write_rows(RESULTS_DIR / "population_accounting.csv", accounting)
    write_rows(RESULTS_DIR / "covariate_summary.csv", covariate_summary(train))
    write_rows(RESULTS_DIR / "tercile_boundaries.csv", boundary_rows)
    write_rows(RESULTS_DIR / "characterisation.csv", [
        {k: v for k, v in r.items() if not k.startswith("_")} for r in char_rows])
    write_rows(RESULTS_DIR / "bin_stats.csv", stats_all)
    write_rows(RESULTS_DIR / "g1_qualification.csv", qual_rows)
    metadata = {
        "experiment_id": EXPERIMENT_ID, "frozen_tail_hash": frozen_hash,
        "dependencies": deps, "train_fraction": TRAIN_FRACTION,
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "alpha_g1": ALPHA_G1, "snr_floor": SNR_FLOOR,
        "atr_period": ATR_PERIOD, "vol_window_days": VOL_WINDOW_DAYS,
        "n_boot": N_BOOT, "n_perm": N_PERM,
        "determinism_replay": replay,
        "qualified": {f"{r['domain']}/{r['dimension']}": bool(r["qualified"])
                      for r in qual_rows},
        "n_qualified": int(sum(1 for r in qual_rows if r["qualified"])),
        "overall_status": "CHARACTERISATION_DELIVERED",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # ---- plots (5) -------------------------------------------------------------
    _plot_dimension(stats_all, "c1_completion",
                    "EXP-035 C1 — %completion-to-target terciles", PLOTS_DIR / "c1_bins.png")
    _plot_dimension(stats_all, "c2_session",
                    "EXP-035 C2 — session bins (UTC)", PLOTS_DIR / "c2_bins.png")
    _plot_dimension(stats_all, "c3_vol",
                    "EXP-035 C3 — trailing-vol percentile terciles", PLOTS_DIR / "c3_bins.png")
    plot_stability(qual_rows, char_rows, PLOTS_DIR / "split_half_stability.png")
    plot_qualification_matrix(qual_rows, PLOTS_DIR / "qualification_matrix.png")

    # ---- console summary -------------------------------------------------------
    for r in qual_rows:
        if r["qualified"]:
            LOGGER.info("QUALIFIED: %s / %s (candidate=%s, Delta=%.2f bps, holm_p=%.4f)",
                        r["domain"], r["dimension"], r["candidate_bin"],
                        r["delta_bps"], r["holm_p"])
    LOGGER.info("Qualified dimensions: %d / %d cells", metadata["n_qualified"], len(qual_rows))
    LOGGER.info("Results in %s, plots in %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
