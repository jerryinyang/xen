"""Experiment EXP-039: /EXIT-X TRAIN-Only Exit Screen (DIAG-006, 0 slots).

Implements scope.md / analysis-plan.md (Phase 010 Track A). Measures, on the
TRAIN stratum only (R1.3 1-minute-row timestamp boundary, ``train_end_ts``),
the per-event NET expectancy (frozen EXP-030 CONSERVATIVE costs + Phase 008
financing) of each registered candidate exit rule on the unchanged AVWAP
bounce-entry substrate (EXP-022 events, all_legs), and applies the predeclared
mechanical qualification rule (Phase 010 design §8.1) against the references
R-BTC (registered band-target/trend-change exit, from the validated EXP-022
CSV) and R-FH(12) (EXP-037 frozen FH exit; 4h only).

Registered candidates (bar-close trigger + bar-close real-Close fill):
E1 HA Harami exhaustion; E2 HA trailing reference; E3 Last-X (X in {3,5,8});
E4 frozen band targets without the trend-change leg; E5 frozen band targets
with the trend-change leg replaced by a hard time-stop (H_ts in {8,12,24}).

Key invariants:
* No TEST or holdout price is ever read: every exit scan is bounded by the
  per-cell TRAIN cutoff index; unresolved-at-boundary events are excluded
  from selection and counted (boundary containment, R1.5 analog).
* All candidate-vs-reference gaps are same-events comparisons (intersection
  population: candidate resolved AND R-BTC contained AND, on 4h, R-FH(12)
  contained).
* The power/fragility statement is persisted BEFORE the qualification flags
  are evaluated; ``qualifying_set.json`` is written exactly once, before any
  plot. This is a diagnostic screen: no binding hypothesis test is run.

Run:
    cd <project-root> && python python/experiments/EXP-039/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import logging
import sys
import time
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

from xen.exit_rules import (  # noqa: E402
    UNRESOLVED,
    first_fire_after,
    fixed_horizon_exit_idx,
    ha_trigger_values,
    harami_fire_indices,
    ha_trailing_fire_indices,
    last_x_fire_indices,
    target_exit_idx,
)
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
from exp027_event_method import domain_effect  # noqa: E402

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-039"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP033_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-033" / "results"

DOMAINS: tuple[str, ...] = ("1h", "4h")                      # 5m retired (Phase 010)
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")
SURVIVING: tuple[str, ...] = ("EURUSD", "USTEC", "XAUUSD")   # BTCUSD break-even excluded

# FROZEN EXP-030 CONSERVATIVE costs + Phase 008 financing (no iteration).
RT_CONS_BPS: dict[str, float] = {"EURUSD": 3.0, "USTEC": 5.0, "XAUUSD": 6.0, "BTCUSD": 16.0}
FINANCING_RATE_BPS_PER_DAY: dict[str, float] = {
    "EURUSD": 0.6, "USTEC": 1.2, "XAUUSD": 1.2, "BTCUSD": 10.0,
}

# Registered candidate grid (frozen at scope freeze) + references.
E3_GRID: tuple[int, ...] = (3, 5, 8)
E5_GRID: tuple[int, ...] = (8, 12, 24)
FH_REF_H = 12                                                 # EXP-037 frozen H*
CANDIDATES: tuple[tuple[str, int | None], ...] = (
    ("E1", None), ("E2", None),
    *[("E3", x) for x in E3_GRID],
    ("E4", None),
    *[("E5", h) for h in E5_GRID],
)
REFERENCES_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "1h": ("R_BTC",), "4h": ("R_BTC", "R_FH"),
}

COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
TRAIN_FRACTION = 0.7

# Reportability floors (EXP-030 pooled convention + EXP-021/027 per-direction
# floor of 8 reused as the per-instrument minimum for the positivity read).
MIN_POOLED_EVENTS = 30
MIN_INSTRUMENT_EVENTS = 8

N_BOOT = 1000
CI_PERCENTILES = (2.5, 97.5)
RECON_TOL_BPS = 0.01
DETERMINISM_TOL = 1e-12
MAX_QUALIFIERS_PER_DOMAIN = 2
MAX_QUALIFIERS_TOTAL = 2

FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"

# EXP-033 reproduction-anchor containment (bar-index rule; anchor ONLY — R1.3).
EXP033_MAX_H = 24


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


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dict rows to CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


def ensure_bool(frame: pl.DataFrame, columns: tuple[str, ...]) -> pl.DataFrame:
    """Cast CSV-loaded ``true``/``false`` columns to Boolean."""
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
    """Assert the imported inference tail matches the pinned EXP-027 hash."""
    used_src = []
    for name in FROZEN_FUNCTIONS:
        used_fn = getattr(EM, name, None)
        if used_fn is None:
            raise ValueError(f"FROZEN_INFERENCE_MODIFIED: function {name} missing")
        used_src.append(inspect.getsource(used_fn))
    h_used = hashlib.sha256("".join(used_src).encode()).hexdigest()[:16]
    if h_used != FROZEN_TAIL_EXPECTED_HASH:
        raise ValueError(
            f"FROZEN_INFERENCE_MODIFIED: got {h_used} != pinned {FROZEN_TAIL_EXPECTED_HASH}")
    LOGGER.info("Frozen inference tail verified (%s)", h_used)
    return h_used


def check_dependencies() -> dict[str, str]:
    """Assert the EXP-020/022/033 artifacts this screen rebuilds against exist."""
    for artifact in (EXP020_RESULTS / "analysis_metadata.csv",
                     EXP022_RESULTS / "lifetime_observations.csv",
                     EXP033_RESULTS / "fh_net_curve.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-020/022/033 artifacts present)")
    return {"EXP-020": "present", "EXP-022": "present", "EXP-033": "present"}


# --------------------------------------------------------------------------- #
# Domain rebuild (full OHLC + HA trigger arrays) + TRAIN boundary
# --------------------------------------------------------------------------- #
def build_cells() -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    """Rebuild first-70% domain bars for the scoped domains; attach HA arrays.

    Returns per-cell arrays (OHLC, log close, CloseTime, HA trigger values,
    binding TRAIN cutoff index from ``train_end_ts``) plus metadata rows for
    the EXP-020 reconciliation.
    """
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    expected_sources = set(expected.get_column("source_file").unique().to_list())
    files = [p for p in list_timebar_files(DATA_DIR) if p.name in expected_sources]
    missing = sorted(expected_sources.difference({p.name for p in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    metadata_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        train_end_ts = np.datetime64(data.train_end_ts, "ns")
        for domain, frame in build_domain_frames(data.frame).items():
            if domain not in DOMAINS:
                continue
            open_ = frame.get_column("Open").to_numpy().astype(float)
            high = frame.get_column("High").to_numpy().astype(float)
            low = frame.get_column("Low").to_numpy().astype(float)
            close = frame.get_column("Close").to_numpy().astype(float)
            ct = frame.get_column("CloseTime").to_numpy().astype("datetime64[ns]")
            ha_open, ha_close = ha_trigger_values(open_, high, low, close)
            # Binding TRAIN cutoff: last domain bar whose CloseTime <= train_end_ts.
            cutoff_idx = int(np.searchsorted(ct, train_end_ts, side="right")) - 1
            if cutoff_idx < 0:
                raise ValueError(f"no TRAIN domain bars for {data.instrument}/{domain}")
            cells[(data.instrument, domain)] = {
                "open": open_, "high": high, "low": low, "close": close,
                "log_close": np.log(close), "close_time": ct,
                "ha_open": ha_open, "ha_close": ha_close,
                "train_cutoff_idx": cutoff_idx,
                "train_end_ts": str(data.train_end_ts),
                "n_bars": frame.height,
            }
            metadata_rows.append({
                "instrument": data.instrument, "domain": domain,
                "source_file": data.source_file,
                "analysis_rows_1m": data.analysis_rows, "domain_bars": frame.height,
                "domain_max_close_time": str(frame.get_column("CloseTime").max()),
            })
    return cells, metadata_rows


def validate_analysis_metadata(metadata_rows: list[dict[str, Any]]) -> None:
    """Hard-fail if rebuilt domain bars diverge from EXP-020 analysis metadata."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    by_cell = {(str(r["instrument"]), str(r["domain"])): r for r in expected.to_dicts()}
    failures = []
    for row in metadata_rows:
        cell = (str(row["instrument"]), str(row["domain"]))
        exp = by_cell.get(cell)
        if exp is None:
            failures.append(f"{cell} missing from EXP-020 metadata")
            continue
        ok = (row["source_file"] == exp["source_file"]
              and int(row["analysis_rows_1m"]) == int(exp["analysis_rows_1m"])
              and int(row["domain_bars"]) == int(exp["domain_bars"])
              and str(row["domain_max_close_time"]) == str(exp["domain_max_close_time"]))
        if not ok:
            failures.append(f"{cell[0]}/{cell[1]}")
    if failures:
        raise ValueError(f"EXP-020 analysis metadata mismatch: {failures}")
    LOGGER.info("Domain rebuild matches EXP-020 metadata for %d cells", len(metadata_rows))


# --------------------------------------------------------------------------- #
# Event substrate (EXP-022 validated CSV) + per-event reconciliation
# --------------------------------------------------------------------------- #
def load_train_events(cells: dict[tuple[str, str], dict[str, Any]]) -> pl.DataFrame:
    """Load reportable completed bounce EVENTS for scoped domains; TRAIN only.

    TRAIN membership is binding by trigger timestamp: ``start_idx <=
    train_cutoff_idx`` (the last domain bar at or before ``train_end_ts``).
    Verifies ``start_close`` against the rebuilt close array per event.
    """
    lt = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    lt = ensure_bool(lt, ("reportable_event", "is_pyramid_bounce"))
    events = lt.filter(
        (pl.col("role") == "event") & pl.col("reportable_event")
        & pl.col("outcome").is_in(COMPLETED_OUTCOMES)
        & pl.col("lifetime_bps").is_not_null()
        & pl.col("domain").is_in(DOMAINS)
    )
    rows = events.to_dicts()
    keep, bad_close = [], 0
    for r in rows:
        cell = cells[(str(r["instrument"]), str(r["domain"]))]
        t = int(r["start_idx"])
        if t > cell["train_cutoff_idx"]:
            continue                                   # TEST-stratum event: never read
        if abs(cell["close"][t] - float(r["start_close"])) > 1e-9 * float(r["start_close"]):
            bad_close += 1
        keep.append(r)
    if bad_close:
        raise ValueError(f"start_close mismatch vs rebuilt bars in {bad_close} TRAIN events")
    out = pl.DataFrame(keep)
    LOGGER.info("TRAIN events: %s",
                {d: out.filter(pl.col('domain') == d).height for d in DOMAINS})
    return out


def reconcile_btc_lifetimes(
    events: pl.DataFrame, cells: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Per-event R-BTC reconciliation: rebuilt lifetime_bps == EXP-022 CSV.

    ``10000 * direction * (log_close[completion_idx] - log_close[start_idx])``
    must reproduce the validated CSV value for every TRAIN event (<= RECON_TOL).
    """
    worst = 0.0
    for r in events.to_dicts():
        cell = cells[(str(r["instrument"]), str(r["domain"]))]
        lc = cell["log_close"]
        rebuilt = 10_000.0 * int(r["direction"]) * (lc[int(r["completion_idx"])]
                                                    - lc[int(r["start_idx"])])
        worst = max(worst, abs(rebuilt - float(r["lifetime_bps"])))
    if worst > RECON_TOL_BPS:
        raise ValueError(f"R-BTC RECONCILIATION FAILED: max |diff| {worst:.4f} bps")
    LOGGER.info("R-BTC per-event reconciliation PASS (max |diff| %.6f bps)", worst)
    return {"check": "r_btc_lifetimes", "max_abs_diff_bps": worst, "passed": True}


def reconcile_fh_vs_exp033(
    events: pl.DataFrame, cells: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reproduce EXP-033's 4h per-instrument FH(12) all_legs net (anchor only).

    Uses EXP-033's own containment rule (bar-index cutoff floor(0.7*n_bars);
    ``start_idx + 24 <= cutoff`` AND ``completion_idx <= cutoff``) — admissible
    only inside this reproduction anchor (R1.3). Tolerance: RECON_TOL_BPS
    against ``fh_net_curve.csv`` per-instrument rows at horizon 12.
    """
    curve = pl.read_csv(EXP033_RESULTS / "fh_net_curve.csv")
    ref = {str(r["set"]): float(r["net_bps"]) for r in curve.to_dicts()
           if str(r["domain"]) == "4h" and int(r["horizon"]) == FH_REF_H
           and str(r["set"]) in INSTRUMENTS and r["net_bps"] is not None}
    rows = []
    for inst in sorted(ref):
        cell = cells[(inst, "4h")]
        cut033 = int(np.floor(TRAIN_FRACTION * cell["n_bars"]))
        sub = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == "4h"))
        nets = []
        for r in sub.to_dicts():
            t = int(r["start_idx"])
            if t + EXP033_MAX_H > cut033 or int(r["completion_idx"]) > cut033:
                continue
            j = t + FH_REF_H
            lc, ct = cell["log_close"], cell["close_time"]
            fh = 10_000.0 * int(r["direction"]) * (lc[j] - lc[t])
            days = float(elapsed_calendar_days(ct[t : t + 1], ct[j : j + 1])[0])
            nets.append(fh - RT_CONS_BPS[inst]
                        - float(financing_bps_from_days(
                            np.array([FINANCING_RATE_BPS_PER_DAY[inst]]),
                            np.array([days]))[0]))
        rebuilt = float(np.mean(nets)) if nets else float("nan")
        diff = abs(rebuilt - ref[inst])
        rows.append({"check": "r_fh12_vs_exp033", "instrument": inst, "n_events": len(nets),
                     "rebuilt_net_bps": rebuilt, "exp033_net_bps": ref[inst],
                     "abs_diff_bps": diff, "passed": bool(diff <= RECON_TOL_BPS)})
    failures = [r["instrument"] for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"R-FH(12) RECONCILIATION FAILED vs EXP-033: {failures}")
    LOGGER.info("R-FH(12) reconciliation PASS vs EXP-033 (4h, %d instruments)", len(rows))
    return rows


# --------------------------------------------------------------------------- #
# Exit evaluation (pure computation)
# --------------------------------------------------------------------------- #
def precompute_fire_indices(
    cells: dict[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], dict[tuple[str, int | None, int], np.ndarray]]:
    """Per cell: sorted fire-index arrays for the event-independent rules."""
    out: dict[tuple[str, str], dict[tuple[str, int | None, int], np.ndarray]] = {}
    for cell_key, cell in tqdm(cells.items(), desc="precompute fire indices"):
        fires: dict[tuple[str, int | None, int], np.ndarray] = {}
        fires[("E1", None, 0)] = harami_fire_indices(cell["ha_open"], cell["ha_close"])
        for d in (1, -1):
            fires[("E2", None, d)] = ha_trailing_fire_indices(
                cell["close"], cell["ha_open"], cell["ha_close"], d)
            for x in E3_GRID:
                fires[("E3", x, d)] = last_x_fire_indices(
                    cell["close"], cell["high"], cell["low"], d, x)
        out[cell_key] = fires
    return out


def resolve_exit(
    exit_id: str, param: int | None, row: dict[str, Any],
    cell: dict[str, Any], fires: dict[tuple[str, int | None, int], np.ndarray],
) -> int:
    """Exit bar index for one event under one rule; UNRESOLVED if not by cutoff."""
    t = int(row["start_idx"])
    d = int(row["direction"])
    cut = cell["train_cutoff_idx"]
    if exit_id == "E1":
        return first_fire_after(fires[("E1", None, 0)], t, cut)
    if exit_id == "E2":
        return first_fire_after(fires[("E2", None, d)], t, cut)
    if exit_id == "E3":
        return first_fire_after(fires[("E3", param, d)], t, cut)
    if exit_id == "E4":
        return target_exit_idx(cell["close"], t, d, float(row["favorable_target"]),
                               float(row["adverse_target"]), cut)
    if exit_id == "E5":
        return target_exit_idx(cell["close"], t, d, float(row["favorable_target"]),
                               float(row["adverse_target"]), cut, h_cap=int(param))
    if exit_id == "R_BTC":
        j = int(row["completion_idx"])
        return j if j <= cut else UNRESOLVED
    if exit_id == "R_FH":
        return fixed_horizon_exit_idx(t, FH_REF_H, cut)
    raise ValueError(f"unknown exit_id {exit_id!r}")


def evaluate_exits(
    events: pl.DataFrame, cells: dict[tuple[str, str], dict[str, Any]],
    fires_by_cell: dict[tuple[str, str], dict[tuple[str, int | None, int], np.ndarray]],
) -> pl.DataFrame:
    """Per-event exit, holding time, and net for every evaluation (long table)."""
    evaluations: list[tuple[str, int | None]] = list(CANDIDATES) + [("R_BTC", None),
                                                                    ("R_FH", None)]
    event_dicts = events.to_dicts()
    out_rows: list[dict[str, Any]] = []
    for (exit_id, param) in tqdm(evaluations, desc="evaluate exits"):
        for r in event_dicts:
            inst, dom = str(r["instrument"]), str(r["domain"])
            if exit_id == "R_FH" and dom != "4h":
                continue
            cell = cells[(inst, dom)]
            j = resolve_exit(exit_id, param, r, cell, fires_by_cell[(inst, dom)])
            t = int(r["start_idx"])
            d = int(r["direction"])
            resolved = j != UNRESOLVED
            if resolved:
                lc, ct = cell["log_close"], cell["close_time"]
                lifetime = 10_000.0 * d * (lc[j] - lc[t])
                days = float(elapsed_calendar_days(ct[t : t + 1], ct[j : j + 1])[0])
                net = lifetime - RT_CONS_BPS[inst] - float(
                    financing_bps_from_days(
                        np.array([FINANCING_RATE_BPS_PER_DAY[inst]]),
                        np.array([days]))[0])
            else:
                lifetime, days, net = float("nan"), float("nan"), float("nan")
            out_rows.append({
                "instrument": inst, "domain": dom, "exit_id": exit_id,
                "param": -1 if param is None else int(param),
                "regime_id": int(r["regime_id"]), "direction": d,
                "is_pyramid_bounce": bool(r["is_pyramid_bounce"]),
                "start_idx": t, "exit_idx": j, "resolved": resolved,
                "trigger_ns": int(cell["close_time"][t].astype(np.int64)),
                "holding_bars": (j - t) if resolved else -1,
                "holding_days": days, "lifetime_bps": lifetime, "net_bps": net,
            })
    return pl.DataFrame(out_rows)


def eval_key(exit_id: str, param: int | None) -> str:
    """Stable label for an (exit, param) evaluation, e.g. ``E3(5)``."""
    return exit_id if param is None else f"{exit_id}({param})"


# --------------------------------------------------------------------------- #
# Populations, pooled statistics, descriptive bootstrap
# --------------------------------------------------------------------------- #
def intersection_population(
    long: pl.DataFrame, exit_id: str, param: int | None, domain: str,
) -> pl.DataFrame:
    """Candidate rows on the same-events intersection with the domain references.

    Intersection = candidate resolved AND every applicable reference resolved,
    joined on the event identity (instrument, start_idx).
    """
    key_cols = ["instrument", "start_idx"]
    cand = long.filter((pl.col("exit_id") == exit_id)
                       & (pl.col("param") == (-1 if param is None else param))
                       & (pl.col("domain") == domain) & pl.col("resolved"))
    for ref in REFERENCES_BY_DOMAIN[domain]:
        ref_ok = long.filter((pl.col("exit_id") == ref) & (pl.col("domain") == domain)
                             & pl.col("resolved")).select(key_cols)
        cand = cand.join(ref_ok, on=key_cols, how="semi")
    return cand


def reference_nets_on(
    long: pl.DataFrame, pop: pl.DataFrame, domain: str,
) -> dict[str, pl.DataFrame]:
    """Reference rows restricted to a candidate's intersection population."""
    key_cols = ["instrument", "start_idx"]
    keys = pop.select(key_cols)
    return {ref: long.filter((pl.col("exit_id") == ref) & (pl.col("domain") == domain))
                .join(keys, on=key_cols, how="semi")
            for ref in REFERENCES_BY_DOMAIN[domain]}


def pooled_net(frame: pl.DataFrame) -> float:
    """Event-weighted pooled net over the surviving instruments (binding pooling)."""
    sub = frame.filter(pl.col("instrument").is_in(SURVIVING))
    return float(sub.get_column("net_bps").mean()) if sub.height else float("nan")


def equal_weight_net(frame: pl.DataFrame) -> float:
    """Frozen-style equal-weight-across-instruments net (cross-check column)."""
    sub = frame.filter(pl.col("instrument").is_in(SURVIVING))
    insts = [i for i in SURVIVING
             if sub.filter(pl.col("instrument") == i).height > 0]
    if not insts:
        return float("nan")
    return float(domain_effect(sub.get_column("net_bps").to_numpy().astype(float),
                               sub.get_column("instrument").to_numpy(), insts))


def cluster_bootstrap_stats(
    frame: pl.DataFrame, seed: int, ref_frame: pl.DataFrame | None = None,
) -> dict[str, float]:
    """Descriptive event-weighted cluster bootstrap (SE + percentile CI).

    Resamples ``regime_id`` clusters with replacement within (instrument,
    direction) strata over the surviving instruments, recomputing the
    event-weighted pooled net — and, when ``ref_frame`` is given (same events,
    same cluster structure), the pooled reference gap with paired resamples.
    Descriptive only; no p-values.
    """
    sub = frame.filter(pl.col("instrument").is_in(SURVIVING))
    if sub.height == 0:
        return {"se": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "gap_se": float("nan")}
    nets = sub.get_column("net_bps").to_numpy().astype(float)
    if ref_frame is not None:
        ref = ref_frame.filter(pl.col("instrument").is_in(SURVIVING)).sort(
            ["instrument", "start_idx"])
        sub = sub.sort(["instrument", "start_idx"])
        nets = sub.get_column("net_bps").to_numpy().astype(float)
        ref_nets = ref.get_column("net_bps").to_numpy().astype(float)
        if ref.height != sub.height:
            raise ValueError("reference frame is not the same-events population")
    strata_keys = (sub.get_column("instrument").to_numpy().astype(str)
                   + "|" + sub.get_column("direction").to_numpy().astype(str))
    clusters = sub.get_column("regime_id").to_numpy().astype(np.int64)
    rng = np.random.default_rng(seed)
    stratum_clusters: dict[str, np.ndarray] = {}
    members: dict[tuple[str, int], np.ndarray] = {}
    for s in np.unique(strata_keys):
        mask = strata_keys == s
        cs = np.unique(clusters[mask])
        stratum_clusters[s] = cs
        for c in cs:
            members[(s, int(c))] = np.flatnonzero(mask & (clusters == c))
    boots, gap_boots = [], []
    for _ in range(N_BOOT):
        idx_parts = []
        for s, cs in stratum_clusters.items():
            draw = rng.choice(cs, size=cs.size, replace=True)
            idx_parts.extend(members[(s, int(c))] for c in draw)
        idx = np.concatenate(idx_parts)
        boots.append(float(nets[idx].mean()))
        if ref_frame is not None:
            gap_boots.append(float(nets[idx].mean() - ref_nets[idx].mean()))
    boots_arr = np.asarray(boots)
    out = {"se": float(np.std(boots_arr)),
           "ci_low": float(np.percentile(boots_arr, CI_PERCENTILES[0])),
           "ci_high": float(np.percentile(boots_arr, CI_PERCENTILES[1])),
           "gap_se": float("nan")}
    if gap_boots:
        out["gap_se"] = float(np.std(np.asarray(gap_boots)))
    return out


def split_half_nets(pop: pl.DataFrame, refs: dict[str, pl.DataFrame],
                    better_ref: str, own: pl.DataFrame) -> dict[str, float]:
    """Chronological split-half statistics (criterion populations pinned).

    Intersection population: pooled net and better-reference gap per half
    (same-events; feeds the §8.1(iii) gap-sign leg and grid selection).
    Own-contained population: pooled net per half (feeds the §8.1(iii)
    net>0 leg, per the pinned criterion populations — design §11 amendment).
    """
    sub = pop.filter(pl.col("instrument").is_in(SURVIVING))
    med = float(sub.get_column("trigger_ns").median()) if sub.height else float("nan")
    out: dict[str, float] = {"split_median_ns": med}
    for name, cond in (("h1", pl.col("trigger_ns") <= med),
                       ("h2", pl.col("trigger_ns") > med)):
        half = sub.filter(cond)
        keys = half.select(["instrument", "start_idx"])
        ref_half = refs[better_ref].join(keys, on=["instrument", "start_idx"], how="semi")
        out[f"{name}_net_bps"] = pooled_net(half)
        out[f"{name}_gap_bps"] = pooled_net(half) - pooled_net(ref_half)
        out[f"{name}_n"] = half.height
    own_sub = own.filter(pl.col("instrument").is_in(SURVIVING))
    own_med = (float(own_sub.get_column("trigger_ns").median())
               if own_sub.height else float("nan"))
    for name, cond in (("h1", pl.col("trigger_ns") <= own_med),
                       ("h2", pl.col("trigger_ns") > own_med)):
        half = own_sub.filter(cond)
        out[f"{name}_own_net_bps"] = pooled_net(half)
        out[f"{name}_own_n"] = half.height
    return out


# --------------------------------------------------------------------------- #
# Screen statistics, grid selection, qualification
# --------------------------------------------------------------------------- #
def screen_statistics(long: pl.DataFrame) -> list[dict[str, Any]]:
    """Full per-(domain, evaluation) statistics table (incl. references)."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        evals = list(CANDIDATES) + [(r, None) for r in REFERENCES_BY_DOMAIN[domain]]
        for exit_id, param in tqdm(evals, desc=f"screen stats {domain}"):
            pop = intersection_population(long, exit_id, param, domain)
            refs = reference_nets_on(long, pop, domain)
            ref_nets = {ref: pooled_net(f) for ref, f in refs.items()}
            better_ref = max(ref_nets, key=lambda k: ref_nets[k])
            sub = pop.filter(pl.col("instrument").is_in(SURVIVING))
            seed = seed_for(EXPERIMENT_ID, "boot", domain, exit_id, param or 0)
            boot = cluster_bootstrap_stats(pop, seed, refs[better_ref]
                                           if exit_id not in refs else None)
            own = long.filter((pl.col("exit_id") == exit_id)
                              & (pl.col("param") == (-1 if param is None else param))
                              & (pl.col("domain") == domain))
            own_resolved = own.filter(pl.col("resolved"))
            halves = split_half_nets(pop, refs, better_ref, own_resolved)
            inst_cols: dict[str, Any] = {}
            for inst in INSTRUMENTS:
                isub = pop.filter(pl.col("instrument") == inst)
                inst_cols[f"net_{inst}"] = (float(isub.get_column("net_bps").mean())
                                            if isub.height else None)
                inst_cols[f"n_{inst}"] = isub.height
                osub = own_resolved.filter(pl.col("instrument") == inst)
                inst_cols[f"own_net_{inst}"] = (float(osub.get_column("net_bps").mean())
                                                if osub.height else None)
                inst_cols[f"own_n_{inst}"] = osub.height
            # EURUSD-share disclosure (design §11/3): additive decomposition of
            # the event-weighted intersection pooled net, plus ex-EURUSD pooled.
            pooled = pooled_net(pop)
            eur = sub.filter(pl.col("instrument") == "EURUSD")
            ex_eur = sub.filter(pl.col("instrument") != "EURUSD")
            eur_share = (
                (eur.height / sub.height) * float(eur.get_column("net_bps").mean())
                / pooled
                if sub.height and eur.height and np.isfinite(pooled) and pooled != 0.0
                else None)
            pooled_ex_eur = (float(ex_eur.get_column("net_bps").mean())
                             if ex_eur.height else None)
            rows.append({
                "domain": domain, "exit_id": exit_id,
                "param": -1 if param is None else int(param),
                "eval": eval_key(exit_id, param), "is_reference": exit_id in ref_nets,
                "n_own_resolved": own.filter(pl.col("resolved")).height,
                "n_unresolved": own.filter(~pl.col("resolved")).height,
                "n_intersection": sub.height,
                "pooled_net_bps": pooled,
                "own_pooled_net_bps": pooled_net(own_resolved),
                "eurusd_net_contribution_share": eur_share,
                "pooled_net_ex_eurusd_bps": pooled_ex_eur,
                "equal_weight_net_bps": equal_weight_net(pop),
                "se": boot["se"], "ci_low": boot["ci_low"], "ci_high": boot["ci_high"],
                "better_ref": better_ref, "better_ref_net_bps": ref_nets[better_ref],
                "gap_bps": pooled_net(pop) - ref_nets[better_ref],
                "gap_se": boot["gap_se"],
                "mean_holding_bars": (float(sub.get_column("holding_bars").mean())
                                      if sub.height else None),
                **{f"ref_net_{k}": v for k, v in ref_nets.items()},
                **halves, **inst_cols,
            })
    return rows


def select_grid_points(stats: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    """Per (domain, gridded exit): max-min worst-half net, smaller-param tie."""
    selected: dict[tuple[str, str], int] = {}
    for domain in DOMAINS:
        for exit_id in ("E3", "E5"):
            grid = [r for r in stats
                    if r["domain"] == domain and r["exit_id"] == exit_id]
            if not grid:
                continue
            def worst_half(r: dict[str, Any]) -> float:
                vals = [r.get("h1_net_bps"), r.get("h2_net_bps")]
                vals = [v for v in vals if v is not None and np.isfinite(v)]
                return min(vals) if vals else float("-inf")
            best = sorted(grid, key=lambda r: (-worst_half(r), r["param"]))[0]
            selected[(domain, exit_id)] = int(best["param"])
    return selected


def write_power_statement(stats: list[dict[str, Any]],
                          selected: dict[tuple[str, str], int]) -> list[dict[str, Any]]:
    """Persist the fragility statement BEFORE qualification flags are computed."""
    rows = []
    for r in stats:
        if r["is_reference"]:
            continue
        if r["exit_id"] in ("E3", "E5") and r["param"] != selected.get(
                (r["domain"], r["exit_id"])):
            continue
        gap_fragile = (not np.isfinite(r["gap_bps"]) or not np.isfinite(r["gap_se"])
                       or abs(r["gap_bps"]) < r["gap_se"])
        rows.append({
            "domain": r["domain"], "eval": r["eval"],
            "n_intersection": r["n_intersection"],
            "pooled_se_bps": r["se"], "gap_bps": r["gap_bps"], "gap_se_bps": r["gap_se"],
            "min_stable_gap_bps": r["gap_se"], "gap_fragile": gap_fragile,
            "below_pooled_floor": r["n_intersection"] < MIN_POOLED_EVENTS,
        })
    write_rows(RESULTS_DIR / "power_statement.csv", rows)
    LOGGER.info("Power/fragility statement persisted (%d rows) before qualification",
                len(rows))
    return rows


def qualify(stats: list[dict[str, Any]],
            selected: dict[tuple[str, str], int]) -> list[dict[str, Any]]:
    """Design §8.1 mechanical qualification (criterion populations pinned).

    (i) per-instrument positivity and the net>0 leg of (iii) read the
    candidate's OWN boundary-contained population; (ii) and the gap-sign leg
    of (iii) read the intersection population (design §11 amendment).
    Ranking and caps are applied separately in ``rank_and_cap``.
    """
    qual_rows: list[dict[str, Any]] = []
    for r in stats:
        if r["is_reference"]:
            continue
        if r["exit_id"] in ("E3", "E5") and r["param"] != selected.get(
                (r["domain"], r["exit_id"])):
            continue
        floor_ok = (r["n_intersection"] >= MIN_POOLED_EVENTS
                    and all(r[f"own_n_{i}"] >= MIN_INSTRUMENT_EVENTS
                            for i in SURVIVING))
        pos_ok = all(r[f"own_net_{i}"] is not None and r[f"own_net_{i}"] > 0.0
                     for i in SURVIVING)
        beat_ok = np.isfinite(r["gap_bps"]) and r["gap_bps"] > 0.0
        h1n, h2n = r.get("h1_own_net_bps"), r.get("h2_own_net_bps")
        h1g, h2g = r.get("h1_gap_bps"), r.get("h2_gap_bps")
        stable_ok = (h1n is not None and h2n is not None and h1n > 0.0 and h2n > 0.0
                     and h1g is not None and h2g is not None
                     and np.sign(h1g) == np.sign(h2g) == np.sign(r["gap_bps"]))
        h1i, h2i = r.get("h1_net_bps"), r.get("h2_net_bps")
        worst_half = min(v for v in (h1i, h2i) if v is not None) \
            if (h1i is not None and h2i is not None) else float("-inf")
        n_params = {"E1": 0, "E2": 0, "E3": 1, "E4": 0, "E5": 1}[r["exit_id"]]
        qual_rows.append({
            "domain": r["domain"], "eval": r["eval"], "exit_id": r["exit_id"],
            "param": r["param"], "floor_ok": floor_ok,
            "per_instrument_positive": pos_ok, "beats_better_ref": beat_ok,
            "split_half_stable": stable_ok,
            "qualifies": bool(floor_ok and pos_ok and beat_ok and stable_ok),
            "worst_half_net_bps": worst_half, "n_params": n_params,
            "mean_holding_bars": r["mean_holding_bars"],
            "eurusd_net_contribution_share": r["eurusd_net_contribution_share"],
            "pooled_net_ex_eurusd_bps": r["pooled_net_ex_eurusd_bps"],
        })
    return qual_rows


def rank_and_cap(
    long: pl.DataFrame, qual_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Rank qualifiers on the within-domain qualifier-intersection population.

    Per the design §11 amendment: the ranking that decides what consumes the
    EXP-041 slot is recomputed on the events contained under EVERY qualifying
    candidate of the domain and the applicable references (same-events
    comparison). Per-candidate-population numbers are disclosed alongside;
    any rank reversal between the two computations is flagged and escalates
    to operator adjudication before the EXP-041 freeze.

    Returns (chosen qualifiers after caps, ranking disclosure rows,
    rank_reversal flag). Also sets ``selected_for_tier_b`` on ``qual_rows``.
    """
    key_cols = ["instrument", "start_idx"]
    ranking_rows: list[dict[str, Any]] = []
    chosen: list[dict[str, Any]] = []
    reversal_any = False

    def _order_key(field: str):
        return lambda q: (-q[field] if np.isfinite(q[field]) else np.inf,
                          q["n_params"], q["mean_holding_bars"] or 0.0)

    for domain in DOMAINS:
        dq = [q for q in qual_rows if q["domain"] == domain and q["qualifies"]]
        if not dq:
            continue
        keys: pl.DataFrame | None = None
        evals = ([(q["exit_id"], q["param"]) for q in dq]
                 + [(ref, -1) for ref in REFERENCES_BY_DOMAIN[domain]])
        for exit_id, param in evals:
            res = long.filter((pl.col("exit_id") == exit_id)
                              & (pl.col("param") == param)
                              & (pl.col("domain") == domain)
                              & pl.col("resolved")).select(key_cols).unique()
            keys = res if keys is None else keys.join(res, on=key_cols, how="semi")
        assert keys is not None
        for q in dq:
            rows = long.filter((pl.col("exit_id") == q["exit_id"])
                               & (pl.col("param") == q["param"])
                               & (pl.col("domain") == domain)
                               ).join(keys, on=key_cols, how="semi")
            sub = rows.filter(pl.col("instrument").is_in(SURVIVING))
            if sub.height:
                med = float(sub.get_column("trigger_ns").median())
                h1 = sub.filter(pl.col("trigger_ns") <= med)
                h2 = sub.filter(pl.col("trigger_ns") > med)
                halves = [float(h.get_column("net_bps").mean())
                          for h in (h1, h2) if h.height]
                q["shared_worst_half_net_bps"] = (min(halves) if halves
                                                  else float("-inf"))
            else:
                q["shared_worst_half_net_bps"] = float("-inf")
            q["shared_n"] = sub.height
        per_cand = sorted(dq, key=_order_key("worst_half_net_bps"))
        shared = sorted(dq, key=_order_key("shared_worst_half_net_bps"))
        reversal = [q["eval"] for q in per_cand] != [q["eval"] for q in shared]
        reversal_any = reversal_any or reversal
        for rank, q in enumerate(shared, start=1):
            ranking_rows.append({
                "domain": domain, "eval": q["eval"],
                "shared_rank": rank,
                "per_candidate_rank": per_cand.index(q) + 1,
                "shared_worst_half_net_bps": q["shared_worst_half_net_bps"],
                "per_candidate_worst_half_net_bps": q["worst_half_net_bps"],
                "shared_n": q["shared_n"],
                "domain_rank_reversal": reversal,
            })
        chosen.extend(shared[:MAX_QUALIFIERS_PER_DOMAIN])
    # Global cap: cross-domain comparison uses each qualifier's within-domain
    # intersection statistic (design §11 amendment).
    chosen.sort(key=lambda q: (-q["shared_worst_half_net_bps"]
                               if np.isfinite(q["shared_worst_half_net_bps"])
                               else np.inf, q["n_params"]))
    chosen = chosen[:MAX_QUALIFIERS_TOTAL]
    chosen_keys = {(q["domain"], q["eval"]) for q in chosen}
    for q in qual_rows:
        q["selected_for_tier_b"] = (q["domain"], q["eval"]) in chosen_keys
    if reversal_any:
        LOGGER.warning("RANK REVERSAL between per-candidate and shared-population "
                       "rankings — operator adjudication required before the "
                       "EXP-041 freeze (qualifying set marked provisional)")
    return chosen, ranking_rows, reversal_any


# --------------------------------------------------------------------------- #
# Determinism replay
# --------------------------------------------------------------------------- #
def determinism_replay(long: pl.DataFrame, stats: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-run one cell's bootstrap with the same seed; assert exact identity."""
    target = next(r for r in stats if r["domain"] == "4h" and r["eval"] == "E4")
    pop = intersection_population(long, "E4", None, "4h")
    seed = seed_for(EXPERIMENT_ID, "boot", "4h", "E4", 0)
    replay = cluster_bootstrap_stats(pop, seed)
    drift = max(abs(replay["se"] - target["se"]),
                abs(replay["ci_low"] - target["ci_low"]),
                abs(replay["ci_high"] - target["ci_high"]))
    return {"cell": "4h/E4", "max_drift": drift,
            "passed": bool(drift <= DETERMINISM_TOL)}


# --------------------------------------------------------------------------- #
# Plotting (5)
# --------------------------------------------------------------------------- #
def _candidate_rows(stats: list[dict[str, Any]], domain: str,
                    selected: dict[tuple[str, str], int]) -> list[dict[str, Any]]:
    """Candidate stats at selected grid points for one domain."""
    out = []
    for r in stats:
        if r["domain"] != domain or r["is_reference"]:
            continue
        if r["exit_id"] in ("E3", "E5") and r["param"] != selected.get(
                (domain, r["exit_id"])):
            continue
        out.append(r)
    return out


def plot_net_forest(stats: list[dict[str, Any]], selected: dict[tuple[str, str], int],
                    path: Path) -> None:
    """Pooled net per exit with descriptive CIs; references as vertical lines."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6.5 * len(DOMAINS), 4.8))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        rows = _candidate_rows(stats, domain, selected)
        ys = np.arange(len(rows))
        for k, r in enumerate(rows):
            ax.errorbar(r["pooled_net_bps"], k,
                        xerr=[[r["pooled_net_bps"] - r["ci_low"]],
                              [r["ci_high"] - r["pooled_net_bps"]]],
                        fmt="o", color="#3498db", capsize=3)
        for ref in REFERENCES_BY_DOMAIN[domain]:
            ref_row = next(r for r in stats
                           if r["domain"] == domain and r["exit_id"] == ref)
            ax.axvline(ref_row["pooled_net_bps"], ls="--", lw=1.0,
                       color="#e67e22" if ref == "R_BTC" else "#2e7d32",
                       label=f"{ref} ({ref_row['pooled_net_bps']:.1f})")
        ax.axvline(0, color="black", lw=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels([r["eval"] for r in rows], fontsize=8)
        ax.set_xlabel("Pooled net per-event expectancy (bps)")
        ax.set_title(f"{domain} (surviving instruments, intersection populations)")
        ax.legend(fontsize=8)
    fig.suptitle("EXP-039 exit screen — TRAIN net by exit (descriptive CIs)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_gap_stability(stats: list[dict[str, Any]], selected: dict[tuple[str, str], int],
                       path: Path) -> None:
    """Full-TRAIN reference gap vs the two split-half gaps per candidate."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6.5 * len(DOMAINS), 4.5))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        rows = _candidate_rows(stats, domain, selected)
        x = np.arange(len(rows))
        ax.bar(x - 0.25, [r["gap_bps"] for r in rows], 0.22, label="full TRAIN",
               color="#3498db")
        ax.bar(x, [r.get("h1_gap_bps") or np.nan for r in rows], 0.22, label="half 1",
               color="#85c1e9")
        ax.bar(x + 0.25, [r.get("h2_gap_bps") or np.nan for r in rows], 0.22,
               label="half 2", color="#aed6f1")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([r["eval"] for r in rows], fontsize=8, rotation=45)
        ax.set_ylabel("Gap vs better reference (bps)")
        ax.set_title(domain)
        ax.legend(fontsize=8)
    fig.suptitle("EXP-039 reference-gap split-half stability", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_holding_times(long: pl.DataFrame, path: Path) -> None:
    """Holding-time distributions per exit vs references (resolved events)."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6.5 * len(DOMAINS), 4.5))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        sub = long.filter((pl.col("domain") == domain) & pl.col("resolved")
                          & pl.col("instrument").is_in(SURVIVING))
        labels, data = [], []
        for exit_id, param in list(CANDIDATES) + [(r, None)
                                                  for r in REFERENCES_BY_DOMAIN[domain]]:
            rows = sub.filter((pl.col("exit_id") == exit_id)
                              & (pl.col("param") == (-1 if param is None else param)))
            if rows.height:
                labels.append(eval_key(exit_id, param))
                data.append(rows.get_column("holding_bars").to_numpy())
        ax.boxplot(data, tick_labels=labels, showfliers=False)
        ax.set_ylabel("Holding time (domain bars)")
        ax.set_title(domain)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    fig.suptitle("EXP-039 holding-time distributions", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_containment(stats: list[dict[str, Any]], selected: dict[tuple[str, str], int],
                     path: Path) -> None:
    """Own-resolved vs intersection counts and boundary exclusions per cell."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6.5 * len(DOMAINS), 4.2))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        rows = _candidate_rows(stats, domain, selected)
        x = np.arange(len(rows))
        ax.bar(x - 0.2, [r["n_own_resolved"] for r in rows], 0.18, label="own resolved",
               color="#3498db")
        ax.bar(x, [r["n_intersection"] for r in rows], 0.18, label="intersection",
               color="#2e7d32")
        ax.bar(x + 0.2, [r["n_unresolved"] for r in rows], 0.18,
               label="unresolved (excluded)", color="#c0392b")
        ax.set_xticks(x)
        ax.set_xticklabels([r["eval"] for r in rows], fontsize=8, rotation=45)
        ax.set_ylabel("Events")
        ax.set_title(domain)
        ax.legend(fontsize=8)
    fig.suptitle("EXP-039 containment / population accounting", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_grid_curves(stats: list[dict[str, Any]], path: Path) -> None:
    """E3 X-grid and E5 H_ts-grid net curves (full TRAIN + halves)."""
    fig, axes = plt.subplots(len(DOMAINS), 2, figsize=(11, 4.2 * len(DOMAINS)),
                             squeeze=False)
    for row_i, domain in enumerate(DOMAINS):
        for col_i, (exit_id, grid) in enumerate((("E3", E3_GRID), ("E5", E5_GRID))):
            ax = axes[row_i][col_i]
            rows = sorted([r for r in stats
                           if r["domain"] == domain and r["exit_id"] == exit_id],
                          key=lambda r: r["param"])
            xs = [r["param"] for r in rows]
            ax.plot(xs, [r["pooled_net_bps"] for r in rows], "o-", label="full TRAIN",
                    color="#3498db")
            ax.plot(xs, [r.get("h1_net_bps") for r in rows], "s--", label="half 1",
                    color="#85c1e9")
            ax.plot(xs, [r.get("h2_net_bps") for r in rows], "^--", label="half 2",
                    color="#aed6f1")
            ax.axhline(0, color="black", lw=0.8)
            ax.set_xticks(list(grid))
            ax.set_xlabel("X" if exit_id == "E3" else "H_ts")
            ax.set_ylabel("Pooled net (bps)")
            ax.set_title(f"{domain} {exit_id}")
            ax.legend(fontsize=8)
    fig.suptitle("EXP-039 grid-selection transparency", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-039 TRAIN-only exit screen end to end."""
    configure_logging()
    ensure_output_dirs()
    t0 = time.time()
    LOGGER.info("=== %s: /EXIT-X TRAIN-only exit screen ===", EXPERIMENT_ID)

    frozen_hash = verify_frozen_inference()
    verify_financing()
    deps = check_dependencies()

    cells, metadata_rows = build_cells()
    validate_analysis_metadata(metadata_rows)
    events = load_train_events(cells)
    recon = [reconcile_btc_lifetimes(events, cells)]
    recon += reconcile_fh_vs_exp033(events, cells)

    fires = precompute_fire_indices(cells)
    long = evaluate_exits(events, cells, fires)
    stats = screen_statistics(long)
    selected = select_grid_points(stats)
    write_power_statement(stats, selected)          # ordering: BEFORE qualification
    qual_rows = qualify(stats, selected)
    chosen, ranking_rows, rank_reversal = rank_and_cap(long, qual_rows)

    replay = determinism_replay(long, stats)
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # ---- persist results (qualifying_set.json once, before plots) -------------
    write_rows(RESULTS_DIR / "reconciliation.csv", recon)
    long.write_csv(RESULTS_DIR / "per_event_exits.csv")
    write_rows(RESULTS_DIR / "screen_statistics.csv", stats)
    write_rows(RESULTS_DIR / "grid_selection.csv",
               [{"domain": d, "exit_id": e, "selected_param": p}
                for (d, e), p in selected.items()])
    write_rows(RESULTS_DIR / "qualification_table.csv", qual_rows)
    write_rows(RESULTS_DIR / "ranking_table.csv", ranking_rows)
    screen_outcome = "QUALIFIED" if chosen else "FLAT"
    qualifying_set = {
        "experiment_id": EXPERIMENT_ID, "frozen_on_emission": True,
        "screen_outcome": screen_outcome,
        "rank_reversal": rank_reversal,
        "provisional_pending_operator_adjudication": rank_reversal,
        "qualifiers": [{
            "domain": q["domain"], "exit_id": q["exit_id"], "param": q["param"],
            "eval": q["eval"], "worst_half_net_bps": q["worst_half_net_bps"],
            "shared_worst_half_net_bps": q["shared_worst_half_net_bps"],
            "instrument_family": list(SURVIVING),
        } for q in chosen],
        "references": {d: list(REFERENCES_BY_DOMAIN[d]) for d in DOMAINS},
        "fh_ref_h": FH_REF_H, "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
    }
    payload = json.dumps(qualifying_set, indent=2, default=str)
    qualifying_set["content_sha256"] = hashlib.sha256(payload.encode()).hexdigest()[:16]
    (RESULTS_DIR / "qualifying_set.json").write_text(
        json.dumps(qualifying_set, indent=2, default=str))

    metadata = {
        "experiment_id": EXPERIMENT_ID, "frozen_tail_hash": frozen_hash,
        "dependencies": deps, "domains": list(DOMAINS),
        "surviving_instruments": list(SURVIVING),
        "train_boundary_convention": "1-minute-row timestamp (train_end_ts, R1.3)",
        "train_cutoffs": {f"{i}/{d}": cells[(i, d)]["train_cutoff_idx"]
                          for (i, d) in cells},
        "train_end_ts": {f"{i}/{d}": cells[(i, d)]["train_end_ts"] for (i, d) in cells},
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "n_boot": N_BOOT, "floors": {"pooled": MIN_POOLED_EVENTS,
                                     "per_instrument": MIN_INSTRUMENT_EVENTS},
        "grid_selection": {f"{d}/{e}": p for (d, e), p in selected.items()},
        "screen_outcome": screen_outcome,
        "n_qualifiers": len(chosen),
        "rank_reversal": rank_reversal,
        "determinism_replay": replay,
        "runtime_seconds": round(time.time() - t0, 1),
        "overall_status": "MEASUREMENT_COMPLETE",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2,
                                                              default=str))

    # ---- plots ---------------------------------------------------------------
    plot_net_forest(stats, selected, PLOTS_DIR / "net_by_exit_forest.png")
    plot_gap_stability(stats, selected, PLOTS_DIR / "reference_gap_stability.png")
    plot_holding_times(long, PLOTS_DIR / "holding_time_dist.png")
    plot_containment(stats, selected, PLOTS_DIR / "containment_accounting.png")
    plot_grid_curves(stats, PLOTS_DIR / "grid_curves.png")

    # ---- console summary -----------------------------------------------------
    LOGGER.info("Screen outcome: %s (%d qualifier(s))", screen_outcome, len(chosen))
    for q in chosen:
        LOGGER.info("  -> %s on %s (worst-half net %.2f bps)", q["eval"], q["domain"],
                    q["worst_half_net_bps"])
    LOGGER.info("Results in %s, plots in %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
