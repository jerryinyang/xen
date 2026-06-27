"""Experiment EXP-037: /EXIT-FH Fixed-Horizon-Exit Capture-Efficiency Variant (4h, one-shot TEST).

Implements analysis-plan.md / scope.md (Phase 008, Tier B2; registered variant
CF-AVWAP-001/EXIT-FH, 1 slot; G1-B2 qualified 4h only; revised R1 2026-06-10,
pre-execution — design §11). Two structurally separated stages:

**TRAIN stage** (all selection; binding TRAIN/TEST boundary = the 1-minute-row
timestamp convention (R1.3): TEST iff trigger close time > ``train_end_ts``, the
CloseTime of the last TRAIN 1-minute analysis row; ties -> TRAIN):

1. Integrity guards 1-3 (hard gates): (a) the FH net curve recomputed under EXP-033's
   containment rule on EXP-033's own TRAIN population (bar-index cutoff — allowed
   ONLY inside this reproduction anchor) reproduces
   ``EXP-033/results/fh_net_curve.csv`` 4h objective values at H in {4,6,8,12} to
   <= 0.01 bps with exact per-instrument counts — proving this script is the EXP-033
   estimator; (b) TRAIN + TEST counts tile the EXP-030 full-analysis 4h cells exactly
   (EURUSD 39 / USTEC 36 / XAUUSD 42), with the timestamp-vs-bar-index membership
   divergence disclosed; (c) frozen EXP-027 inference tail matches the pinned hash
   (e50873d12a9f68d9).
2. Mechanical H* tie-break on the CONTAINED TRAIN subset (R1.5: events whose FH
   window at the grid max H=12 exits at or before the boundary timestamp; spill
   events excluded from selection and counted — the freeze is TEST-price-blind):
   per H in {4,6,8,12} (all_legs) the objective net N(H) plus chronological
   split-half nets N1(H)/N2(H); retain H iff N>0 AND N1>0 AND N2>0;
   H* = argmax_H min(N1,N2), ties to smaller H. Empty retained set =>
   ``B2_NO_ROBUST_HSTAR``: the freeze record is written with ``h_star = null`` and
   the TEST stage NEVER runs (honest no-read outcome; the phase G2 family shrinks
   to EXP-038's single read).
3. Pyramid policy at H* by the EXP-033 one-SE preference rule
   (all_legs -> first_leg_only -> pyramid_legs_only), with the R1.6 pre-freeze
   feasibility filter: a policy is a candidate only if every TEST cell stays
   non-empty under it (entry attributes only — no TEST outcome read).
3b. Pre-TEST synthetic-null calibration (R1.2): per cell, R=2000 zero-mean Gaussian
   cluster-model replicates on the TEST stratum's entry-attribute cluster layout
   (dispersion components from contained-TRAIN nets at H*), each scored by the
   frozen 1000-resample bootstrap -> measured small-n FPR and the binding margin
   ``m_cell = max(0, Q95 of null ci_low_1s)``. Persisted before the freeze.
4. **Freeze-before-TEST (guard 5, the load-bearing control)**: H*, policy, margins,
   and the full per-event stratum manifest are written to
   ``results/frozen_selection.json`` BEFORE any TEST-event return is computed.
   FH/net columns are attached to TRAIN rows only in this stage; TEST rows carry no
   outcome columns until after the freeze. Recovery semantics (R1.6): an existing
   freeze file must content-hash-match the recomputed record (else hard stop); an
   existing ``test_verdicts.csv`` blocks any TEST recomputation (no second read).

**TEST stage** (one-shot): loads H*/policy/margins/membership from the frozen file
(hard assert), computes ``net_e = fh_bps(H*) - RT_cons_i - financing_e`` for TEST
events under the frozen policy, and runs the frozen regime-cluster bootstrap (1000
resamples) per cell. Binding multiplicity is the PHASE-LEVEL Holm family (R1.1:
these 3 raw one-sided p's + EXP-038's 1), adjudicated in the checkpoint's
``G2-gate-review.md`` — this script emits raw p's, a within-route Holm-3
disclosure, and ``route_pass_provisional`` flags (Holm-3 p <= 0.05 AND ci_low_1s >
m_cell); it NEVER emits ``g2_satisfied``. Descriptive labels from the two-sided 95%
CI. A descriptive BTC-exit comparison on the identical TEST events is disclosed
(non-binding).

FH construction is EXP-033-identical: ``10000 * d * ln(close[i+H]/close[i])``,
truncated to the last available analysis bar at the series end (the rebuilt series
covers only the first-70% slice, so the global holdout is never indexed). Financing:
``rate_i * elapsed_calendar_days(entry close, exit close)``, fractional days, via the
shared ``xen.financing`` helper. Zero-baseline: absolute bps vs 0. No cost, financing,
H*, or policy value may be revisited after the TEST read.

Run:
    cd <project-root> && python python/experiments/EXP-037/code/run_experiment.py
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
    elapsed_calendar_days,
    financing_bps_from_days,
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
    domain_effect,
    holm_adjust,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-037"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
FROZEN_SELECTION_PATH = RESULTS_DIR / "frozen_selection.json"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP030_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-030" / "results"
EXP033_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-033" / "results"

DOMAIN = "4h"
# Declared 4h TEST family (BTCUSD excluded by the D0 break-even map).
TEST_INSTRUMENTS: tuple[str, ...] = ("EURUSD", "USTEC", "XAUUSD")

# LOCKED H* candidate set (scope tie-break) and the EXP-033 containment bound used
# only for the guard-1 reproduction population (EXP-033 grid max was 24).
H_CANDIDATES: tuple[int, ...] = (4, 6, 8, 12)
EXP033_CONTAIN_H: int = 24
# R1.5 selection containment: tie-break population = TRAIN events whose FH window at
# the grid max H=12 exits at or before the boundary timestamp (constant across H).
TIEBREAK_CONTAIN_H: int = max(H_CANDIDATES)

TRAIN_FRACTION = 0.7

# R1.2 null calibration (synthetic data only; persisted before the freeze).
N_NULL_CAL = 2000
MARGIN_QUANTILE = 95.0

# EXP-030 full-analysis 4h cell counts (guard 2; drift = hard stop).
EXPECTED_FULL_N: dict[str, int] = {"EURUSD": 39, "USTEC": 36, "XAUUSD": 42}
# EXP-033 contained-TRAIN per-instrument counts (guard 1 population check).
EXP033_CONTAINED_N: dict[str, int] = {"EURUSD": 27, "USTEC": 25, "XAUUSD": 34}

# FROZEN EXP-030 CONSERVATIVE costs + predeclared financing (bps; bps/day).
RT_CONS_BPS: dict[str, float] = {"EURUSD": 3.0, "USTEC": 5.0, "XAUUSD": 6.0}
FINANCING_RATE_BPS_PER_DAY: dict[str, float] = {"EURUSD": 0.6, "USTEC": 1.2, "XAUUSD": 1.2}

# Pyramid-policy menu in the predeclared simplicity-preference order.
POLICIES: tuple[str, ...] = ("all_legs", "first_leg_only", "pyramid_legs_only")
# EXP-033 4h per-instrument reportability floor for policy candidates.
POLICY_MIN_EVENTS = 15

# EXP-028 PRIMARY population construction (identical to EXP-030/033/034).
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
PAIR_KEYS = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx"]
MIN_CONTROLS = EM.MIN_CONTROLS

# Inference convention (frozen method parameters).
N_BOOT = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)

# Tolerances.
RECON_TOL_BPS = 0.01            # guard-1 reproduction vs EXP-033 fh_net_curve
START_CLOSE_RTOL = 1e-9
DETERMINISM_TOL = 1e-12

# Frozen inference functions + pinned hash (same tail and pin as EXP-030/033/034).
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"

# Stratum manifest key columns (event identity inside one (instrument, 4h) cell).
MANIFEST_KEYS = ("instrument", "regime_id", "direction", "event_trigger_idx", "start_idx")


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
        raise FileNotFoundError(f"missing artifact: {path}")
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
# Integrity guards (hash pin, dependencies)
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Guard 3: assert the imported inference tail matches the PINNED EXP-027 hash."""
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
    """Assert G1-B2 qualification (EXP-033 4h eligible) and upstream artifacts exist."""
    b2 = load_json(EXP033_RESULTS / "b2_selection.json")
    sel_4h = b2.get("per_domain", {}).get(DOMAIN, {})
    if not bool(sel_4h.get("b2_eligible")):
        raise ValueError(f"EXP-033 b2_selection: 4h not B2-eligible ({sel_4h.get('reason')!r})")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP030_RESULTS / "net_by_instrument.csv",
                     EXP033_RESULTS / "fh_net_curve.csv",
                     EXP020_RESULTS / "analysis_metadata.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-033 4h B2-eligible; upstream artifacts present)")
    return {"EXP-033": "4h b2_eligible", "EXP-030": "present", "EXP-022": "present"}


# --------------------------------------------------------------------------- #
# Domain rebuild (4h Close + CloseTime) + holdout-safe metadata guard
# --------------------------------------------------------------------------- #
def expected_timebar_sources() -> set[str]:
    """Canonical source Parquet filenames recorded by EXP-020 metadata."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    return set(expected.get_column("source_file").unique().to_list())


def build_cell_series() -> dict[str, dict[str, np.ndarray]]:
    """Rebuild first-70% 4h domain bars for the declared instruments.

    Same loader/fence as EXP-020/031/033/034 (``xen.referee_calibration``), so 4h bar
    indices align with ``start_idx``/``completion_idx`` by construction. Hard-fails if
    the rebuild diverges from EXP-020 analysis metadata (bar counts, max CloseTime).
    """
    expected_sources = expected_timebar_sources()
    files = [path for path in list_timebar_files(DATA_DIR) if path.name in expected_sources]
    missing = sorted(expected_sources.difference({path.name for path in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    expected_by_cell = {(str(r["instrument"]), str(r["domain"])): r for r in expected.to_dicts()}
    series: dict[str, dict[str, np.ndarray]] = {}
    for path in tqdm(files, desc="rebuild 4h domain bars"):
        data = load_analysis_data(path)
        if data.instrument not in TEST_INSTRUMENTS:
            continue
        frame = build_domain_frames(data.frame)[DOMAIN]
        exp = expected_by_cell.get((data.instrument, DOMAIN))
        if exp is None:
            raise ValueError(f"{data.instrument}/{DOMAIN} missing from EXP-020 metadata")
        if (int(frame.height) != int(exp["domain_bars"])
                or str(frame.get_column("CloseTime").max()) != str(exp["domain_max_close_time"])
                or int(data.analysis_rows) != int(exp["analysis_rows_1m"])):
            raise ValueError(f"domain rebuild diverged from EXP-020 metadata for "
                             f"{data.instrument}/{DOMAIN}")
        series[data.instrument] = {
            "log_close": np.log(frame.get_column("Close").to_numpy().astype(float)),
            "close": frame.get_column("Close").to_numpy().astype(float),
            "close_time": frame.get_column("CloseTime").to_numpy().astype("datetime64[ns]"),
            # R1.3 binding boundary: CloseTime of the last TRAIN 1-minute analysis
            # row (the shared loader's train_end_ts; same convention as EXP-038).
            "boundary_ns": np.datetime64(data.train_end_ts, "ns").astype(np.int64),
        }
    absent = sorted(set(TEST_INSTRUMENTS).difference(series))
    if absent:
        raise ValueError(f"missing rebuilt 4h series for instruments: {absent}")
    LOGGER.info("4h domain rebuild matches EXP-020 metadata for %d instruments", len(series))
    return series


def train_cutoffs(series: dict[str, dict[str, np.ndarray]]) -> dict[str, int]:
    """Per-instrument 4h bar-index cutoff: floor(TRAIN_FRACTION * n_4h_bars).

    EXP-033's convention — used ONLY inside the guard-1 reproduction anchor and the
    R1.3 divergence disclosure. The binding partition uses ``boundary_ns`` (R1.3).
    """
    return {inst: int(np.floor(TRAIN_FRACTION * arrs["log_close"].size))
            for inst, arrs in series.items()}


def attach_trigger_ns(frame: pl.DataFrame,
                      series: dict[str, dict[str, np.ndarray]]) -> pl.DataFrame:
    """Attach the entry-confirmation (trigger) close time as int64 ns (entry attribute).

    Pure entry-attribute lookup (``CloseTime[start_idx]`` on the rebuilt 4h series);
    no outcome column is touched, so this may run before the freeze for all rows.
    """
    si = frame.get_column("start_idx").to_numpy().astype(np.int64)
    inst = frame.get_column("instrument").to_numpy()
    trigger_ns = np.full(frame.height, np.int64(0))
    for i, arrs in series.items():
        rows = np.flatnonzero(inst == i)
        if rows.size == 0:
            continue
        b = si[rows]
        if (b < 0).any() or (b >= arrs["close_time"].size).any():
            raise ValueError(f"start_idx out of analysis-slice range for {i}/{DOMAIN}")
        trigger_ns[rows] = arrs["close_time"][b].astype(np.int64)
    return frame.with_columns(pl.Series("trigger_ns", trigger_ns))


# --------------------------------------------------------------------------- #
# Population (EXP-030 PRIMARY, 4h declared cells) + stratum partition
# --------------------------------------------------------------------------- #
def load_population(lifetime: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """(events, controls): the EXP-028/030 PRIMARY 4h rows for the declared instruments.

    Events: ``role=event AND reportable_event`` with >= MIN_CONTROLS completed matched
    controls (EXP-034 ``build_event_table`` semantics, restricted to the scope cells).
    Controls are returned separately for the guard-1 containment reproduction.
    """
    lt = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lt.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES)
                   & pl.col("lifetime_bps").is_not_null()
                   & (pl.col("domain") == DOMAIN)
                   & pl.col("instrument").is_in(TEST_INSTRUMENTS))
    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_n = controls.group_by(PAIR_KEYS).agg(pl.len().alias("n_controls_finite"))
    events = events.join(ctrl_n, on=PAIR_KEYS, how="inner").filter(
        pl.col("n_controls_finite") >= MIN_CONTROLS)
    keep = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx",
            "is_pyramid_bounce", "start_idx", "completion_idx", "start_close",
            "lifetime_bps"]
    LOGGER.info("4h PRIMARY event population: %d rows", events.height)
    return events.select(keep), controls


def partition_strata(
    events: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
    cutoffs: dict[str, int],
) -> tuple[pl.DataFrame, pl.DataFrame, list[dict[str, Any]]]:
    """Guard 2: trigger-keyed TRAIN/TEST partition tiling the EXP-030 cells exactly.

    R1.3 binding convention: an event is TEST iff its trigger close time (int64 ns,
    entry attribute) exceeds the instrument's 1-minute ``train_end_ts`` boundary;
    ties -> TRAIN. Per-cell TRAIN + TEST must equal the EXP-030 full-analysis count
    (hard stop). The membership divergence vs the EXP-033 bar-index cutoff is
    disclosed per cell (transparency only; never alters membership).
    """
    bound = pl.DataFrame({"instrument": list(series),
                          "boundary_ns": [int(arrs["boundary_ns"]) for arrs in series.values()]})
    cut = pl.DataFrame({"instrument": list(cutoffs), "train_cutoff_idx": list(cutoffs.values())})
    joined = events.join(bound, on="instrument", how="left").join(cut, on="instrument", how="left")
    if joined.filter(pl.col("boundary_ns").is_null()).height:
        raise ValueError("missing TRAIN/TEST boundary timestamp for some instruments")
    joined = joined.with_columns([
        (pl.col("trigger_ns") <= pl.col("boundary_ns")).alias("is_train"),
        (pl.col("start_idx") < pl.col("train_cutoff_idx")).alias("is_train_baridx"),
    ])
    rows: list[dict[str, Any]] = []
    for inst in TEST_INSTRUMENTS:
        sub = joined.filter(pl.col("instrument") == inst)
        n_train = sub.filter(pl.col("is_train")).height
        n_test = sub.filter(~pl.col("is_train")).height
        expected = EXPECTED_FULL_N[inst]
        ok = (n_train + n_test) == expected
        rows.append({"check": "population_partition", "instrument": inst, "horizon": None,
                     "rebuilt": float(n_train + n_test), "expected": float(expected),
                     "abs_diff": float(abs(n_train + n_test - expected)),
                     "detail": f"train={n_train},test={n_test}", "passed": ok})
        if not ok:
            raise ValueError(f"GUARD 2 FAILED: {inst}/4h TRAIN+TEST = {n_train + n_test} "
                             f"!= EXP-030 count {expected}")
        divergent = sub.filter(pl.col("is_train") != pl.col("is_train_baridx")).height
        rows.append({"check": "boundary_convention_divergence", "instrument": inst,
                     "horizon": None, "rebuilt": float(divergent), "expected": None,
                     "abs_diff": None,
                     "detail": "events whose membership differs between the binding "
                               "1m-timestamp boundary and the EXP-033 bar-index cutoff "
                               "(disclosure only)", "passed": True})
    dup = joined.group_by(list(MANIFEST_KEYS)).agg(pl.len().alias("k")).filter(pl.col("k") > 1)
    if dup.height:
        raise ValueError(f"GUARD 2 FAILED: {dup.height} duplicated event keys in partition")
    LOGGER.info("Guard 2 PASS: TRAIN/TEST tiles EXP-030 4h cells (%s)",
                {r["instrument"]: r["detail"] for r in rows
                 if r["check"] == "population_partition"})
    drop_cols = ["is_train", "is_train_baridx", "train_cutoff_idx"]
    train = joined.filter(pl.col("is_train")).drop(drop_cols)
    test = joined.filter(~pl.col("is_train")).drop(drop_cols)
    return train, test, rows


# --------------------------------------------------------------------------- #
# Pure computation: FH outcomes, nets, objective aggregation
# --------------------------------------------------------------------------- #
def add_fh_net_columns(
    frame: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
    horizons: tuple[int, ...],
) -> pl.DataFrame:
    """Attach ``fh_<H>``, ``net_<H>``, and ``truncated_<H>`` outcome columns.

    EXP-033-identical FH construction with the predeclared series-end truncation:
    ``exit_idx = min(start_idx + H, n - 1)`` on the rebuilt first-70% 4h series (the
    holdout is never indexed). ``net_H = fh_H - RT_cons_i - rate_i * days_H`` via the
    shared ``xen.financing`` helper. Also asserts ``start_close`` reproduces the
    rebuilt base bar (index->timestamp alignment integrity). Trigger timestamps are
    attached separately by ``attach_trigger_ns`` (entry attribute, pre-freeze safe).
    """
    si = frame.get_column("start_idx").to_numpy().astype(np.int64)
    d = frame.get_column("direction").to_numpy().astype(float)
    sc = frame.get_column("start_close").to_numpy().astype(float)
    inst = frame.get_column("instrument").to_numpy()
    rt = np.array([RT_CONS_BPS[i] for i in inst], dtype=float)
    rate = np.array([FINANCING_RATE_BPS_PER_DAY[i] for i in inst], dtype=float)
    n_rows = frame.height
    fh = {h: np.full(n_rows, np.nan) for h in horizons}
    days = {h: np.full(n_rows, np.nan) for h in horizons}
    trunc = {h: np.zeros(n_rows, dtype=bool) for h in horizons}
    base_bad = 0
    for i, arrs in series.items():
        rows = np.flatnonzero(inst == i)
        if rows.size == 0:
            continue
        lc, ct = arrs["log_close"], arrs["close_time"]
        b = si[rows]
        if (b < 0).any() or (b >= lc.size).any():
            raise ValueError(f"start_idx out of analysis-slice range for {i}/{DOMAIN}")
        tol = START_CLOSE_RTOL * sc[rows]
        base_bad += int(np.sum(np.abs(np.exp(lc[b]) - sc[rows]) > tol))
        for h in horizons:
            tgt = np.minimum(b + h, lc.size - 1)
            trunc[h][rows] = (b + h) > (lc.size - 1)
            fh[h][rows] = 10_000.0 * d[rows] * (lc[tgt] - lc[b])
            days[h][rows] = elapsed_calendar_days(ct[b], ct[tgt])
    if base_bad:
        raise ValueError(f"start_close mismatch vs rebuilt base bar in {base_bad} rows")
    cols: list[pl.Series] = []
    for h in horizons:
        cols.append(pl.Series(f"fh_{h}", fh[h]))
        cols.append(pl.Series(f"net_{h}", fh[h] - rt - financing_bps_from_days(rate, days[h])))
        cols.append(pl.Series(f"truncated_{h}", trunc[h]))
    return frame.with_columns(cols)


def apply_policy(events: pl.DataFrame, policy: str) -> pl.DataFrame:
    """Filter the event frame to a pyramid-policy subset."""
    if policy == "all_legs":
        return events
    if policy == "first_leg_only":
        return events.filter(~pl.col("is_pyramid_bounce"))
    if policy == "pyramid_legs_only":
        return events.filter(pl.col("is_pyramid_bounce"))
    raise ValueError(f"unknown policy {policy!r}")


def objective_net(events: pl.DataFrame, value_col: str) -> float:
    """Equal-weight mean over the declared instruments of per-instrument event means.

    The frozen ``domain_effect`` aggregation (EXP-033-identical). Hard-fails if any
    declared instrument has zero rows — the objective is undefined in that case.
    """
    counts = {i: events.filter(pl.col("instrument") == i).height for i in TEST_INSTRUMENTS}
    empty = [i for i, n in counts.items() if n == 0]
    if empty:
        raise ValueError(f"objective undefined: no events for {empty}")
    return domain_effect(events.get_column(value_col).to_numpy().astype(float),
                         events.get_column("instrument").to_numpy(), list(TEST_INSTRUMENTS))


def bootstrap_net(events: pl.DataFrame, value_col: str, insts: list[str],
                  seed: int) -> np.ndarray:
    """Frozen regime-cluster bootstrap distribution of the equal-weight net."""
    sub = events.filter(pl.col("instrument").is_in(insts))
    diffs = sub.get_column(value_col).to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    return bootstrap_effect_distribution(strata, insts, np.random.default_rng(seed),
                                         N_BOOT, CHUNK)


# --------------------------------------------------------------------------- #
# Guard 1: EXP-033 reproduction anchor (containment population, same code path)
# --------------------------------------------------------------------------- #
def reproduce_exp033_curve(
    events: pl.DataFrame, controls: pl.DataFrame,
    series: dict[str, dict[str, np.ndarray]], cutoffs: dict[str, int],
) -> list[dict[str, Any]]:
    """Recompute the FH net curve on EXP-033's contained TRAIN population; compare.

    Containment (EXP-033/F08): ``start_idx + 24 <= cutoff AND completion_idx <= cutoff``
    for events AND controls; events additionally need >= MIN_CONTROLS contained matched
    controls (EXP-033 ``build_train_legs`` semantics). The 4h objective net at every
    H in {4,6,8,12} (all_legs) must reproduce ``EXP-033/results/fh_net_curve.csv`` to
    <= RECON_TOL_BPS with exact per-instrument counts. Hard gate.
    """
    cut = pl.DataFrame({"instrument": list(cutoffs), "cutoff": list(cutoffs.values())})

    def contained(frame: pl.DataFrame) -> pl.DataFrame:
        joined = frame.join(cut, on="instrument", how="left")
        return joined.filter(
            ((pl.col("start_idx") + EXP033_CONTAIN_H) <= pl.col("cutoff"))
            & (pl.col("completion_idx") <= pl.col("cutoff"))).drop("cutoff")

    ev_c = contained(events)
    ctrl_c = contained(controls)
    ctrl_n = ctrl_c.group_by(PAIR_KEYS).agg(pl.len().alias("n_contained_controls"))
    ev_c = ev_c.join(ctrl_n, on=PAIR_KEYS, how="inner").filter(
        pl.col("n_contained_controls") >= MIN_CONTROLS)
    ev_c = add_fh_net_columns(ev_c, series, H_CANDIDATES)
    for h in H_CANDIDATES:
        if ev_c.filter(pl.col(f"truncated_{h}")).height:
            raise ValueError(f"guard-1 invariant violated: truncated fh_{h} in containment set")

    ref = pl.read_csv(EXP033_RESULTS / "fh_net_curve.csv")
    ref = ref.filter((pl.col("domain") == DOMAIN) & (pl.col("policy") == "all_legs"))
    ref_obj = {int(r["horizon"]): float(r["net_bps"])
               for r in ref.filter(pl.col("set") == "objective").to_dicts()}
    rows: list[dict[str, Any]] = []
    for inst in TEST_INSTRUMENTS:
        n_inst = ev_c.filter(pl.col("instrument") == inst).height
        ok = n_inst == EXP033_CONTAINED_N[inst]
        rows.append({"check": "exp033_contained_n", "instrument": inst, "horizon": None,
                     "rebuilt": float(n_inst), "expected": float(EXP033_CONTAINED_N[inst]),
                     "abs_diff": float(abs(n_inst - EXP033_CONTAINED_N[inst])),
                     "detail": None, "passed": ok})
    for h in H_CANDIDATES:
        net = objective_net(ev_c, f"net_{h}")
        diff = abs(net - ref_obj[h])
        rows.append({"check": "exp033_objective_net", "instrument": "objective",
                     "horizon": h, "rebuilt": net, "expected": ref_obj[h],
                     "abs_diff": diff, "detail": None,
                     "passed": bool(diff <= RECON_TOL_BPS)})
    failures = [f"{r['check']}/{r['instrument']}/H={r['horizon']}"
                for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"GUARD 1 FAILED (EXP-033 reproduction): {failures}")
    LOGGER.info("Guard 1 PASS: EXP-033 FH curve reproduced at H in %s (<= %.2f bps)",
                H_CANDIDATES, RECON_TOL_BPS)
    return rows


# --------------------------------------------------------------------------- #
# TRAIN stage: containment, mechanical H* tie-break + pyramid policy (selection only)
# --------------------------------------------------------------------------- #
def contained_train_subset(
    train: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
) -> tuple[pl.DataFrame, dict[str, int]]:
    """R1.5 selection population: TRAIN events whose FH(12) exit stays inside TRAIN.

    Contained iff ``close_time[min(start_idx + TIEBREAK_CONTAIN_H, n - 1)] <=
    boundary`` — fixed at the grid max so the selection population is constant
    across candidate H and no TEST-window price can enter the freeze. Returns the
    contained frame and the per-instrument excluded (spill) counts; spill events
    keep their binding TRAIN membership — only selection is blind to them.
    """
    si = train.get_column("start_idx").to_numpy().astype(np.int64)
    inst = train.get_column("instrument").to_numpy()
    contained = np.zeros(train.height, dtype=bool)
    for i, arrs in series.items():
        rows = np.flatnonzero(inst == i)
        if rows.size == 0:
            continue
        ct = arrs["close_time"].astype(np.int64)
        exit_idx = np.minimum(si[rows] + TIEBREAK_CONTAIN_H, ct.size - 1)
        contained[rows] = ct[exit_idx] <= int(arrs["boundary_ns"])
    out = train.filter(pl.Series(contained))
    spill = {i: int(np.sum((inst == i) & ~contained)) for i in TEST_INSTRUMENTS}
    LOGGER.info("R1.5 containment: %d/%d TRAIN events retained for selection "
                "(spill excluded: %s)", out.height, train.height, spill)
    return out, spill


def train_tiebreak(
    train_net: pl.DataFrame, spill: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The predeclared {4,6,8,12} tie-break on the contained TRAIN selection set.

    Per H: contained-TRAIN objective net N(H) and chronological split-half nets
    N1/N2 (halves at the pooled median contained-TRAIN trigger timestamp, EXP-033's
    construction). Retain H iff N>0 AND N1>0 AND N2>0; H* = argmax_H min(N1, N2),
    ties to smaller H. Returns (table rows, selection record). Point estimates
    only — no inference. ``objective_net`` hard-fails (pre-freeze, recoverable) if
    any instrument is empty in a half (R1.6 feasibility).
    """
    med = float(train_net.get_column("trigger_ns").median())
    h1 = train_net.filter(pl.col("trigger_ns") <= med)
    h2 = train_net.filter(pl.col("trigger_ns") > med)
    rows: list[dict[str, Any]] = []
    retained: dict[int, float] = {}
    for h in H_CANDIDATES:
        n_full = objective_net(train_net, f"net_{h}")
        n_h1 = objective_net(h1, f"net_{h}")
        n_h2 = objective_net(h2, f"net_{h}")
        keep = bool(n_full > 0.0 and n_h1 > 0.0 and n_h2 > 0.0)
        if keep:
            retained[h] = min(n_h1, n_h2)
        rows.append({
            "horizon": h, "policy": "all_legs",
            "n_full_bps": n_full, "n_half1_bps": n_h1, "n_half2_bps": n_h2,
            "worst_half_bps": min(n_h1, n_h2), "retained": keep,
            "reportable": None, "se": None,
            "n_spill_excluded": sum(spill.values()),
            "n_events": train_net.height,
            **{f"n_{i}": train_net.filter(pl.col("instrument") == i).height
               for i in TEST_INSTRUMENTS},
        })
    if retained:
        best = max(retained.values())
        h_star = min(h for h, v in retained.items() if v == best)
        selection: dict[str, Any] = {
            "status": "H_STAR_SELECTED", "h_star": h_star,
            "worst_half_at_h_star_bps": retained[h_star],
            "retained_h": sorted(retained), "split_median_ns": med,
        }
    else:
        selection = {"status": "B2_NO_ROBUST_HSTAR", "h_star": None,
                     "retained_h": [], "split_median_ns": med}
    LOGGER.info("TRAIN tie-break: retained=%s -> %s (H*=%s)",
                sorted(retained), selection["status"], selection.get("h_star"))
    return rows, selection


def select_pyramid_policy(
    train_net: pl.DataFrame, h_star: int, test_events: pl.DataFrame,
) -> tuple[list[dict[str, Any]], str]:
    """EXP-033 one-SE preference rule over the policy menu at the tie-break H*.

    A policy is a candidate iff (a) every declared instrument keeps >=
    POLICY_MIN_EVENTS contained-TRAIN events under it (EXP-033's 4h reportability
    floor) AND (b) every TEST cell stays non-empty under it — checked from entry
    attributes only (``is_pyramid_bounce``; no TEST outcome is read; R1.6
    pre-freeze feasibility). The selected policy is the first in preference order
    within one bootstrap SE of the best candidate.
    """
    policy_res: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        sub = apply_policy(train_net, policy)
        counts = {i: sub.filter(pl.col("instrument") == i).height for i in TEST_INSTRUMENTS}
        test_counts = {i: apply_policy(test_events, policy)
                       .filter(pl.col("instrument") == i).height
                       for i in TEST_INSTRUMENTS}
        test_feasible = all(n > 0 for n in test_counts.values())
        reportable = all(n >= POLICY_MIN_EVENTS for n in counts.values()) and test_feasible
        res: dict[str, Any] = {"reportable": reportable, "counts": counts,
                               "test_counts": test_counts}
        if reportable:
            boot = bootstrap_net(sub, f"net_{h_star}", list(TEST_INSTRUMENTS),
                                 seed_for(EXPERIMENT_ID, "policy", DOMAIN, policy))
            res["net_bps"] = objective_net(sub, f"net_{h_star}")
            res["se"] = float(np.std(boot))
        policy_res[policy] = res
        rows.append({"horizon": h_star, "policy": policy, "reportable": reportable,
                     "n_full_bps": res.get("net_bps"), "se": res.get("se"),
                     "n_half1_bps": None, "n_half2_bps": None, "worst_half_bps": None,
                     "retained": None, "n_spill_excluded": None,
                     "n_events": sub.height,
                     **{f"n_{i}": counts[i] for i in TEST_INSTRUMENTS}})
    candidates = {p: r for p, r in policy_res.items() if r["reportable"]}
    if not candidates:
        raise ValueError("no pyramid policy satisfies the TRAIN floor "
                         f"({POLICY_MIN_EVENTS} events/instrument) and the R1.6 "
                         "TEST-cell non-emptiness feasibility")
    best = max(candidates, key=lambda p: candidates[p]["net_bps"])
    threshold = candidates[best]["net_bps"] - candidates[best]["se"]
    chosen = next(p for p in POLICIES
                  if p in candidates and candidates[p]["net_bps"] >= threshold)
    LOGGER.info("Pyramid policy at H*=%d: %s (best=%s, one-SE threshold=%.2f bps)",
                h_star, chosen, best, threshold)
    return rows, chosen


def estimate_variance_components(values: np.ndarray, clusters: np.ndarray) -> tuple[float, float]:
    """Method-of-moments (sigma_b, sigma_w) from demeaned TRAIN nets and cluster labels.

    sigma_w^2 = pooled within-cluster variance over clusters with >= 2 events
    (fallback: total variance if none); sigma_b^2 = max(0, var(cluster means) -
    sigma_w^2 * mean(1/n_c)). Predeclared in analysis-plan Step 3b.
    """
    demeaned = values - values.mean()
    uniq = np.unique(clusters)
    sizes = np.array([np.sum(clusters == u) for u in uniq], dtype=float)
    means = np.array([demeaned[clusters == u].mean() for u in uniq])
    multi = sizes >= 2
    if multi.any():
        ss = sum(float(np.sum((demeaned[clusters == u] - demeaned[clusters == u].mean()) ** 2))
                 for u in uniq[multi])
        dof = float(np.sum(sizes[multi] - 1))
        var_w = ss / dof if dof > 0 else float(np.var(demeaned, ddof=1))
    else:
        var_w = float(np.var(demeaned, ddof=1))
    var_means = float(np.var(means, ddof=1)) if uniq.size >= 2 else 0.0
    var_b = max(0.0, var_means - var_w * float(np.mean(1.0 / sizes)))
    return float(np.sqrt(var_b)), float(np.sqrt(var_w))


def null_calibration(
    train_net: pl.DataFrame, test_events: pl.DataFrame, h_star: int, policy: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """R1.2: synthetic-null calibration of the frozen bootstrap at the TEST structure.

    Per declared cell — using TEST **entry attributes** only (direction, regime
    cluster sizes under the frozen policy) and contained-TRAIN dispersion at H* —
    draw ``N_NULL_CAL`` zero-mean Gaussian cluster-model replicates
    (r = a_c + e_i), score each with the frozen 1000-resample bootstrap, and
    report the measured FPR of the uncorrected dual rule plus the binding margin
    ``m_cell = max(0, Q95 of null ci_low_1s)``. No TEST outcome is touched.
    """
    rows: list[dict[str, Any]] = []
    margins: dict[str, float] = {}
    train_pol = apply_policy(train_net, policy)
    test_pol = apply_policy(test_events, policy)
    for inst in TEST_INSTRUMENTS:
        tr = train_pol.filter(pl.col("instrument") == inst)
        te = test_pol.filter(pl.col("instrument") == inst)
        if tr.height < 2 or te.height == 0:
            raise ValueError(f"null calibration infeasible for {inst}/{DOMAIN} "
                             f"(train n={tr.height}, test n={te.height})")
        tr_clusters = (tr.get_column("direction").cast(pl.Int64) * 1_000_000
                       + tr.get_column("regime_id").cast(pl.Int64)).to_numpy()
        sigma_b, sigma_w = estimate_variance_components(
            tr.get_column(f"net_{h_star}").to_numpy().astype(float), tr_clusters)
        # TEST cluster layout from entry attributes: (direction, regime_id) sizes.
        layout = (te.group_by(["direction", "regime_id"]).agg(pl.len().alias("n"))
                  .sort(["direction", "regime_id"]).to_dicts())
        dir_labels = np.concatenate([np.full(r["n"], int(r["direction"]), dtype=int)
                                     for r in layout])
        regime_labels = np.concatenate([np.full(r["n"], j, dtype=int)
                                        for j, r in enumerate(layout)])
        inst_labels = np.full(dir_labels.size, inst)
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "nullcal", DOMAIN, inst))
        ci_lows = np.empty(N_NULL_CAL)
        boot_ps = np.empty(N_NULL_CAL)
        for k in tqdm(range(N_NULL_CAL), desc=f"null calibration {inst}", leave=False):
            cluster_fx = rng.normal(0.0, sigma_b, size=len(layout))
            diffs = cluster_fx[regime_labels] + rng.normal(0.0, sigma_w,
                                                           size=dir_labels.size)
            strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [inst])
            boot = bootstrap_effect_distribution(strata, [inst], rng, N_BOOT, CHUNK)
            ci_lows[k] = np.percentile(boot, 100.0 * ALPHA)
            boot_ps[k] = (1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT)
        margin = max(0.0, float(np.percentile(ci_lows, MARGIN_QUANTILE)))
        fpr_raw = float(np.mean((boot_ps <= ALPHA) & (ci_lows > 0.0)))
        fpr_margin = float(np.mean((boot_ps <= ALPHA) & (ci_lows > margin)))
        margins[inst] = margin
        rows.append({
            "instrument": inst, "domain": DOMAIN, "h_star": h_star, "policy": policy,
            "n_test_events": te.height, "n_test_clusters": len(layout),
            "n_train_events": tr.height, "sigma_b_bps": sigma_b, "sigma_w_bps": sigma_w,
            "n_null_replicates": N_NULL_CAL, "fpr_uncorrected": fpr_raw,
            "margin_bps": margin, "fpr_with_margin": fpr_margin,
        })
        LOGGER.info("Null calibration %s: FPR(raw)=%.4f -> margin=%.3f bps "
                    "(FPR with margin=%.4f)", inst, fpr_raw, margin, fpr_margin)
    return rows, margins


def freeze_selection(
    selection: dict[str, Any], policy: str | None, margins: dict[str, float] | None,
    train: pl.DataFrame, test: pl.DataFrame, cutoffs: dict[str, int],
    boundaries: dict[str, int],
) -> dict[str, Any]:
    """Guard 5: persist H*, policy, margins, and the stratum manifest BEFORE any TEST read.

    The returned record is written to ``frozen_selection.json``; the TEST stage reads
    selection state exclusively from that file. The manifest lists every event key
    with its stratum so the one-shot TEST membership is fixed on disk. R1.6 recovery:
    if a freeze file already exists, the recomputed record must content-hash-match
    it exactly (a rerun after a post-freeze crash is not a second selection);
    mismatch is a hard stop.
    """
    manifest = []
    for stratum, frame in (("TRAIN", train), ("TEST", test)):
        for r in frame.select(list(MANIFEST_KEYS)).to_dicts():
            manifest.append({**{k: r[k] for k in MANIFEST_KEYS}, "stratum": stratum})
    record = {
        "experiment_id": EXPERIMENT_ID, "frozen_on_emission": True,
        "status": selection["status"], "h_star": selection.get("h_star"),
        "pyramid_policy": policy, "h_candidates": list(H_CANDIDATES),
        "calibration_margins_bps": margins,
        "train_cutoffs_baridx_disclosure": cutoffs,
        "boundary_ns": boundaries,
        "counts": {i: {"train": train.filter(pl.col("instrument") == i).height,
                       "test": test.filter(pl.col("instrument") == i).height}
                   for i in TEST_INSTRUMENTS},
        "split_median_ns": selection.get("split_median_ns"),
        "stratum_manifest": manifest,
    }
    payload = json.dumps(record, sort_keys=True, default=str)
    record["content_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    if FROZEN_SELECTION_PATH.exists():
        existing = load_json(FROZEN_SELECTION_PATH)
        if existing.get("content_sha256") != record["content_sha256"]:
            raise ValueError("FREEZE MISMATCH: existing frozen_selection.json does not "
                             "reproduce under rerun — hard stop (R1.6)")
        LOGGER.info("FREEZE already on disk and hash-matched — rerun resume (R1.6)")
        return existing
    FROZEN_SELECTION_PATH.write_text(json.dumps(record, indent=2, default=str))
    LOGGER.info("FREEZE written: %s (status=%s, H*=%s, policy=%s, margins=%s)",
                FROZEN_SELECTION_PATH.name, record["status"], record["h_star"],
                policy, margins)
    return record


# --------------------------------------------------------------------------- #
# TEST stage (one-shot; reads selection state ONLY from the frozen file)
# --------------------------------------------------------------------------- #
def infer_test_cell(sub: pl.DataFrame, inst: str, value_col: str,
                    rng: np.random.Generator) -> dict[str, Any]:
    """Frozen-tail single-cell inference on the TEST net (EXP-034 specialization).

    One-sided 95% lower bound = 5th bootstrap percentile (binding, F01); two-sided
    95% CI descriptive; one-sided bootstrap p = (1 + #{boot <= 0}) / (1 + N_BOOT).
    """
    diffs = sub.get_column(value_col).to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    effect = domain_effect(diffs, inst_labels, [inst])
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [inst])
    boot = bootstrap_effect_distribution(strata, [inst], rng, N_BOOT, CHUNK)
    return {
        "n_events": sub.height, "effect_bps": effect,
        "ci_low": float(np.percentile(boot, CI_PERCENTILES[0])),
        "ci_high": float(np.percentile(boot, CI_PERCENTILES[1])),
        "ci_low_1s": float(np.percentile(boot, 100.0 * ALPHA)),
        "boot_p": float((1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT)),
    }


def run_test_stage(
    test_events: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
) -> list[dict[str, Any]]:
    """One-shot TEST evaluation at the frozen H*/policy/margins.

    Hard-asserts the freeze file exists and reads H*, policy, margins, and
    membership from it (no recomputation of any selection quantity). FH/net columns
    for TEST rows are computed HERE, strictly after the freeze. Emits raw one-sided
    p's (phase-family inputs, R1.1), a within-route Holm-3 disclosure, and
    ``route_pass_provisional`` flags (Holm-3 p <= 0.05 AND ci_low_1s > m_cell);
    never a final G2 verdict. Refuses to run if a verdict artifact already exists
    (R1.6 no-second-read guard). Also attaches the descriptive BTC-exit net on the
    identical events (non-binding comparison).
    """
    if (RESULTS_DIR / "test_verdicts.csv").exists():
        raise ValueError("NO-SECOND-READ: test_verdicts.csv already exists — the TEST "
                         "stratum has been read; refusing to recompute (R1.6)")
    if not FROZEN_SELECTION_PATH.exists():
        raise ValueError("FREEZE-BEFORE-TEST VIOLATION: frozen_selection.json missing")
    frozen = load_json(FROZEN_SELECTION_PATH)
    h_star = frozen.get("h_star")
    policy = frozen.get("pyramid_policy")
    margins = frozen.get("calibration_margins_bps")
    if h_star is None or policy is None or margins is None:
        raise ValueError("TEST stage invoked without a frozen H*/policy/margins")
    h_star = int(h_star)
    frozen_test_keys = {tuple(m[k] for k in MANIFEST_KEYS)
                       for m in frozen["stratum_manifest"] if m["stratum"] == "TEST"}
    live_keys = {tuple(r[k] for k in MANIFEST_KEYS)
                 for r in test_events.select(list(MANIFEST_KEYS)).to_dicts()}
    if frozen_test_keys != live_keys:
        raise ValueError("TEST membership diverges from the frozen stratum manifest")

    test_net = add_fh_net_columns(test_events, series, (h_star,))
    test_net = attach_btc_net(test_net, series)
    test_net = apply_policy(test_net, policy)

    cell_p: dict[str, float] = {}
    cells: dict[str, dict[str, Any]] = {}
    for inst in tqdm(TEST_INSTRUMENTS, desc="TEST cells"):
        sub = test_net.filter(pl.col("instrument") == inst)
        if sub.height == 0:
            raise ValueError(f"TEST cell {inst}/4h empty under frozen policy {policy!r}")
        res = infer_test_cell(sub, inst, f"net_{h_star}",
                              np.random.default_rng(seed_for(EXPERIMENT_ID, "test",
                                                             DOMAIN, inst)))
        res["btc_net_bps"] = float(sub.get_column("net_btc").mean())
        res["mean_truncated"] = float(sub.get_column(f"truncated_{h_star}").cast(pl.Int8).mean())
        cells[inst] = res
        cell_p[inst] = res["boot_p"]
    holm = holm_adjust(cell_p)

    rows: list[dict[str, Any]] = []
    for inst in TEST_INSTRUMENTS:
        res = cells[inst]
        margin = float(margins[inst])
        provisional = bool(holm[inst] <= ALPHA and res["ci_low_1s"] > margin)
        if res["ci_low"] > 0.0:
            descriptive = "EVIDENCE_FOR"
        elif res["ci_high"] < 0.0:
            descriptive = "EVIDENCE_AGAINST"
        else:
            descriptive = "INCONCLUSIVE_SPANS_ZERO"
        rows.append({
            "instrument": inst, "domain": DOMAIN, "h_star": h_star, "policy": policy,
            "n_events": res["n_events"], "net_bps": res["effect_bps"],
            "ci_low": res["ci_low"], "ci_high": res["ci_high"],
            "ci_low_1s": res["ci_low_1s"], "boot_p": res["boot_p"],
            "holm_p_route": holm[inst], "margin_bps": margin,
            "route_pass_provisional": provisional,
            "binding_note": "raw boot_p enters the phase-level Holm family (R1.1); "
                            "final EXIT_FH_TEST_PASS only in G2-gate-review.md",
            "descriptive_label": descriptive,
            "btc_net_bps": res["btc_net_bps"],
            "fh_minus_btc_bps": res["effect_bps"] - res["btc_net_bps"],
            "truncated_share": res["mean_truncated"],
        })
    return rows


def attach_btc_net(
    frame: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
) -> pl.DataFrame:
    """Descriptive BTC-exit net on the same events (EXP-034 construction; non-binding).

    ``net_btc = lifetime_bps - RT_cons_i - rate_i * days(trigger close, completion
    close)`` with timestamps from the rebuilt 4h series.
    """
    si = frame.get_column("start_idx").to_numpy().astype(np.int64)
    ci = frame.get_column("completion_idx").to_numpy().astype(np.int64)
    inst = frame.get_column("instrument").to_numpy()
    n = frame.height
    entry_dt = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    exit_dt = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    for i, arrs in series.items():
        rows = np.flatnonzero(inst == i)
        if rows.size == 0:
            continue
        ct = arrs["close_time"]
        if (ci[rows] < 0).any() or (ci[rows] >= ct.size).any():
            raise ValueError(f"completion_idx out of analysis-slice range for {i}/{DOMAIN}")
        entry_dt[rows] = ct[si[rows]]
        exit_dt[rows] = ct[ci[rows]]
    if np.isnat(entry_dt).any() or np.isnat(exit_dt).any():
        raise ValueError("unresolved BTC holding timestamps")
    rt = np.array([RT_CONS_BPS[i] for i in inst], dtype=float)
    rate = np.array([FINANCING_RATE_BPS_PER_DAY[i] for i in inst], dtype=float)
    days = elapsed_calendar_days(entry_dt, exit_dt)
    lifetime = frame.get_column("lifetime_bps").to_numpy().astype(float)
    return frame.with_columns(
        pl.Series("net_btc", lifetime - rt - financing_bps_from_days(rate, days)))


# --------------------------------------------------------------------------- #
# Determinism replay (guard 4)
# --------------------------------------------------------------------------- #
def determinism_replay(
    test_rows: list[dict[str, Any]] | None,
    test_events: pl.DataFrame, series: dict[str, dict[str, np.ndarray]],
    tiebreak_rows: list[dict[str, Any]], train_net: pl.DataFrame,
    spill: dict[str, int],
) -> dict[str, Any]:
    """Same-seed replay: primary TEST cell when TEST ran, else the tie-break table."""
    if test_rows:
        ref = next(r for r in test_rows if r["instrument"] == TEST_INSTRUMENTS[0])
        h_star, policy = int(ref["h_star"]), str(ref["policy"])
        sub = apply_policy(
            attach_btc_net(add_fh_net_columns(test_events, series, (h_star,)), series),
            policy).filter(pl.col("instrument") == TEST_INSTRUMENTS[0])
        replay = infer_test_cell(sub, TEST_INSTRUMENTS[0], f"net_{h_star}",
                                 np.random.default_rng(seed_for(EXPERIMENT_ID, "test",
                                                                DOMAIN, TEST_INSTRUMENTS[0])))
        drift = max(abs(replay[k] - ref[{"effect_bps": "net_bps"}.get(k, k)])
                    for k in ("effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p"))
        cell = f"TEST/{TEST_INSTRUMENTS[0]}"
    else:
        replay_rows, _ = train_tiebreak(train_net, spill)
        drift = max(abs(float(a[k]) - float(b[k]))
                    for a, b in zip(replay_rows,
                                    [r for r in tiebreak_rows if r["retained"] is not None])
                    for k in ("n_full_bps", "n_half1_bps", "n_half2_bps"))
        cell = "TRAIN/tiebreak"
    return {"cell": cell, "max_drift": drift, "passed": bool(drift <= DETERMINISM_TOL)}


# --------------------------------------------------------------------------- #
# Plotting (3)
# --------------------------------------------------------------------------- #
def plot_train_tiebreak(tiebreak_rows: list[dict[str, Any]],
                        selection: dict[str, Any], policy: str | None,
                        path: Path) -> None:
    """TRAIN {4,6,8,12} net table (full + halves) with retained set and H*/policy."""
    curve = [r for r in tiebreak_rows if r["retained"] is not None]
    pol = [r for r in tiebreak_rows if r["retained"] is None]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    hs = [r["horizon"] for r in curve]
    for key, label, style in (("n_full_bps", "N(H) full TRAIN", "o-"),
                              ("n_half1_bps", "N1(H) half 1", "s--"),
                              ("n_half2_bps", "N2(H) half 2", "^--")):
        axes[0].plot(hs, [r[key] for r in curve], style, label=label)
    for r in curve:
        if r["retained"]:
            axes[0].axvspan(r["horizon"] - 0.15, r["horizon"] + 0.15, color="#2e7d32",
                            alpha=0.12)
    if selection.get("h_star") is not None:
        axes[0].axvline(selection["h_star"], color="#2e7d32", ls="--", lw=1.2,
                        label=f"H*={selection['h_star']}")
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set_xticks(hs)
    axes[0].set_xlabel("H (4h domain bars)")
    axes[0].set_ylabel("Objective net (bps)")
    axes[0].set_title(f"TRAIN tie-break — {selection['status']}")
    axes[0].legend(fontsize=8)
    if pol:
        xs = np.arange(len(pol))
        for k, r in enumerate(pol):
            color = "#2e7d32" if r["policy"] == policy else (
                "#7f8c8d" if r["reportable"] else "#c0392b")
            if r["n_full_bps"] is not None:
                axes[1].bar(k, r["n_full_bps"], yerr=r["se"] or 0.0, capsize=4, color=color)
        axes[1].set_xticks(xs)
        axes[1].set_xticklabels([r["policy"] for r in pol], fontsize=8)
        axes[1].axhline(0, color="black", lw=0.8)
        axes[1].set_ylabel("Net at H* (bps)")
        axes[1].set_title(f"Pyramid policy at H* (chosen: {policy})")
    else:
        axes[1].text(0.5, 0.5, "No policy step (B2_NO_ROBUST_HSTAR)",
                     ha="center", va="center")
        axes[1].axis("off")
    fig.suptitle("EXP-037 TRAIN selection (frozen before TEST)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_no_test(path: Path, message: str) -> None:
    """Placeholder figure for the B2_NO_ROBUST_HSTAR no-read outcome."""
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_test_verdicts(test_rows: list[dict[str, Any]], path: Path) -> None:
    """Per-cell TEST net with two-sided CI, one-sided lower bound, margin, and flags."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for k, r in enumerate(test_rows):
        color = "#2e7d32" if r["route_pass_provisional"] else (
            "#c0392b" if r["descriptive_label"] == "EVIDENCE_AGAINST" else "#7f8c8d")
        ax.errorbar(k, r["net_bps"],
                    yerr=[[r["net_bps"] - r["ci_low"]], [r["ci_high"] - r["net_bps"]]],
                    fmt="o", capsize=5, color=color, markersize=8)
        ax.plot(k, r["ci_low_1s"], marker="_", color=color, markersize=16)
        ax.plot(k, r["margin_bps"], marker="_", color="#c0392b", markersize=10)
        flag = ("PROVISIONAL PASS" if r["route_pass_provisional"]
                else r["descriptive_label"])
        ax.annotate(f"raw p={r['boot_p']:.3f}\nroute holm p={r['holm_p_route']:.3f}"
                    f"\n{flag}", (k, r["ci_high"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(test_rows)))
    ax.set_xticklabels([f"{r['instrument']}-4h\n(n={r['n_events']})" for r in test_rows])
    ax.set_ylabel("TEST net per-event expectancy (bps)")
    ax.set_title(f"EXP-037 one-shot TEST — FH(H*={test_rows[0]['h_star']}), "
                 f"policy={test_rows[0]['policy']}\n"
                 "flags PROVISIONAL — binding G2 = phase-family Holm in G2-gate-review.md")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fh_vs_btc(test_rows: list[dict[str, Any]], path: Path) -> None:
    """FH(H*) vs BTC-exit net per TEST cell (point estimates; NON-BINDING)."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(test_rows))
    width = 0.35
    ax.bar(x - width / 2, [r["net_bps"] for r in test_rows], width,
           label="FH(H*) exit", color="#3498db")
    ax.bar(x + width / 2, [r["btc_net_bps"] for r in test_rows], width,
           label="BTC exit (same events)", color="#e67e22")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['instrument']}-4h\n(n={r['n_events']})" for r in test_rows])
    ax.set_ylabel("TEST net (bps)")
    ax.set_title("EXP-037 capture-efficiency comparison — descriptive, NON-BINDING")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run EXP-037 end to end: guards -> TRAIN selection -> freeze -> one-shot TEST."""
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s: /EXIT-FH fixed-horizon-exit variant (4h one-shot TEST) ===",
                EXPERIMENT_ID)

    frozen_hash = verify_frozen_inference()
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    deps = check_dependencies()

    series = build_cell_series()
    cutoffs = train_cutoffs(series)
    boundaries = {i: int(arrs["boundary_ns"]) for i, arrs in series.items()}

    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    events, controls = load_population(lifetime)
    events = attach_trigger_ns(events, series)

    # Guards 1-2 (hard gates before any selection output).
    recon_rows = reproduce_exp033_curve(events, controls, series, cutoffs)
    train, test, partition_rows = partition_strata(events, series, cutoffs)

    # ---- TRAIN stage: outcome columns attached to TRAIN rows ONLY -------------
    # R1.5: all selection reads use the contained subset (spill excluded, disclosed).
    train_contained, spill = contained_train_subset(train, series)
    train_net = add_fh_net_columns(train_contained, series, H_CANDIDATES)
    tiebreak_rows, selection = train_tiebreak(train_net, spill)
    policy: str | None = None
    margins: dict[str, float] | None = None
    calibration_rows: list[dict[str, Any]] = []
    if selection["h_star"] is not None:
        policy_rows, policy = select_pyramid_policy(train_net, int(selection["h_star"]),
                                                    test)
        tiebreak_rows = tiebreak_rows + policy_rows
        # R1.2: null calibration persisted BEFORE the freeze (synthetic data only).
        calibration_rows, margins = null_calibration(train_net, test,
                                                     int(selection["h_star"]), policy)
        write_rows(RESULTS_DIR / "null_calibration.csv", calibration_rows)

    # ---- Guard 5: freeze BEFORE any TEST quantity exists ----------------------
    frozen = freeze_selection(selection, policy, margins, train, test, cutoffs,
                              boundaries)

    # ---- TEST stage (one-shot) or the predeclared no-read path ----------------
    test_rows: list[dict[str, Any]] | None = None
    if frozen["h_star"] is not None:
        test_rows = run_test_stage(test, series)

    replay = determinism_replay(test_rows, test, series, tiebreak_rows, train_net, spill)
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # ---- persist results -------------------------------------------------------
    write_rows(RESULTS_DIR / "reconciliation.csv",
               recon_rows + partition_rows)
    write_rows(RESULTS_DIR / "train_tiebreak.csv", tiebreak_rows)
    n_pass = 0
    if test_rows:
        write_rows(RESULTS_DIR / "test_verdicts.csv", test_rows)
        n_pass = sum(1 for r in test_rows if r["route_pass_provisional"])
        outcome = ("ROUTE_PASS_PROVISIONAL_PENDING_PHASE_HOLM" if n_pass
                   else "TEST_COMPLETE_NO_PASS")
    else:
        outcome = "B2_NO_ROBUST_HSTAR"
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "frozen_tail_hash": frozen_hash,
        "dependencies": deps,
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "h_candidates": list(H_CANDIDATES),
        "h_star": frozen["h_star"],
        "pyramid_policy": frozen["pyramid_policy"],
        "selection_status": frozen["status"],
        "boundary_convention": "TEST iff trigger close > 1m train_end_ts; ties->TRAIN "
                               "(design R1.3)",
        "boundary_ns": boundaries,
        "n_spill_excluded_from_selection": spill,
        "calibration_margins_bps": margins,
        "alpha_one_sided": ALPHA, "n_boot": N_BOOT,
        "n_null_calibration": N_NULL_CAL,
        "binding_rule": ("phase-level Holm family over all realized binding one-sided "
                         "TEST p's (<=4: 3 EXP-037 cells + 1 EXP-038 cell) at alpha=0.05 "
                         "AND ci_low_1s > m_cell (R1.1/R1.2); adjudicated in "
                         "G2-gate-review.md — flags here are PROVISIONAL"),
        "freeze_content_sha256": frozen["content_sha256"],
        "determinism_replay": replay,
        "n_route_pass_provisional": n_pass,
        "g2_adjudication": "PENDING_PHASE_FAMILY_HOLM (G2-gate-review.md)",
        "test_verdicts_provisional": (
            {r["instrument"]: ("ROUTE_PASS_PROVISIONAL" if r["route_pass_provisional"]
                               else r["descriptive_label"])
             for r in test_rows} if test_rows else None),
        "overall_outcome": outcome,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # ---- plots -------------------------------------------------------------------
    plot_train_tiebreak(tiebreak_rows, selection, policy,
                        PLOTS_DIR / "train_tiebreak.png")
    if test_rows:
        plot_test_verdicts(test_rows, PLOTS_DIR / "test_verdicts.png")
        plot_fh_vs_btc(test_rows, PLOTS_DIR / "fh_vs_btc_exit.png")
    else:
        msg = "B2_NO_ROBUST_HSTAR — no TEST read (stability filter empty)"
        plot_no_test(PLOTS_DIR / "test_verdicts.png", msg)
        plot_no_test(PLOTS_DIR / "fh_vs_btc_exit.png", msg)

    # ---- console summary -----------------------------------------------------------
    LOGGER.info("--- outcome: %s ---", outcome)
    if test_rows:
        for r in test_rows:
            LOGGER.info("%s-4h: net=%.2f bps 1s-low=%.2f (margin=%.2f) CI=[%.2f, %.2f] "
                        "raw_p=%.4f route_holm_p=%.4f btc=%.2f -> %s",
                        r["instrument"], r["net_bps"], r["ci_low_1s"], r["margin_bps"],
                        r["ci_low"], r["ci_high"], r["boot_p"], r["holm_p_route"],
                        r["btc_net_bps"],
                        "ROUTE_PASS_PROVISIONAL" if r["route_pass_provisional"]
                        else r["descriptive_label"])
    LOGGER.info("G2 adjudication: %s. Results in %s, plots in %s",
                metadata["g2_adjudication"], RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
