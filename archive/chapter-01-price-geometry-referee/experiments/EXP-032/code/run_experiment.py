"""Experiment EXP-032: One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H*=12, all_legs).

Implements analysis-plan.md / scope.md (Phase 009, registry CF-AVWAP-001/HOLDOUT-B —
the programme's single sanctioned read of the global holdout). Every parameter is
inherited frozen; NO selection of any kind occurs here. Two structurally separated
phases:

**Phase H1 (entry attributes only; no holdout outcome quantity is computed):**

1. Integrity guards (hard gates): (a) hash pins — EXP-037 ``frozen_selection.json``
   content hash and the frozen EXP-027 inference tail (e50873d12a9f68d9);
   (b) analysis-stratum reconciliation — the population regenerated over the FULL
   EURUSD series, restricted to trigger close time <= the holdout boundary, must
   reproduce the EXP-037 EURUSD-4h partition exactly (39 events, 27 TRAIN / 12 TEST
   under the EXP-037 ``boundary_ns``) with identical keys, and identical
   reportability flags vs ``EXP-022/results/lifetime_observations.csv``;
   (c) EXP-037 TEST reproduction anchor — FH(12)/all_legs nets recomputed on the
   EXP-037 TEST stratum (analysis data only) reproduce ``test_verdicts.csv`` EURUSD
   net (+40.558882 bps) to <= 0.01 bps; (d) seal assertion — only the EURUSD
   timebars file is opened (every file/row-range materialized is disclosed), plus
   prefix-equality of the full-series 4h rebuild vs the analysis-only rebuild.
2. Holdout stratum manifest from entry attributes only (triggers, directions,
   regime ids, pyramid flags, control counts) — boundary = CloseTime of 1-minute
   row ``int(total_rows * 0.7) - 1``; HOLDOUT iff trigger close time > boundary,
   ties -> analysis (Phase 009 design / R1.3 convention).
3. Synthetic-null calibration at the holdout cell structure (R1.2 analog):
   cluster layout from holdout ENTRY attributes; dispersion components from the
   already-disclosed full-analysis 39-event FH(12)/all_legs nets; R = 2000
   zero-mean Gaussian cluster replicates scored by the frozen 1000-resample
   bootstrap; binding margin ``m_cell = max(0, Q95 of null ci_low_1s)``.
4. **Freeze-before-outcome barrier:** stratum manifest + margin + inherited frozen
   constants written to ``results/frozen_holdout_manifest.json`` (content-hashed)
   BEFORE any outcome contact. Recovery semantics (EXP-037 R1.6-identical): an
   existing manifest must content-hash-match the recomputed record (hard stop on
   mismatch).

**Phase H2 (one-shot; runs only if the manifest exists and hash-verifies; REFUSES
to run if ``results/holdout_verdict.csv`` exists — no second read under any
circumstance):** per-event ``net_e = fh_bps(12) - 3.0 - 0.6 * elapsed_calendar_days``
on the full-series 4h rebuild (EXP-033/037-identical construction, truncation at the
true series end disclosed), frozen regime-cluster bootstrap (1000 resamples), and the
MECHANICAL binding verdict (family of 1, no Holm): HOLDOUT_CONFIRMED iff
``ci_low_1s > m_cell`` AND ``boot_p <= 0.05``; HOLDOUT_REFUTED iff two-sided
``ci_high < 0``; else HOLDOUT_INCONCLUSIVE. The shot is spent on any outcome.
Non-binding companions in the same pass on the identical events (never promotable):
BTC-exit net (EXP-022 lifetime construction + EXP-034 overlay; point estimate only)
and the gross/cost/financing decomposition of the binding cell. Every mandated
disclosure is persisted (``holdout_events.csv`` per-event table, then
``run_metadata.json``, then ``holdout_verdict.csv`` as the completion marker);
post-verdict rendering and audit read ONLY the persisted artifacts — never holdout
rows again.

**Two-invocation execution (Phase 009 execution addendum):** the freeze and the
irreversible read are separate process invocations — ``--phase h1`` (guards,
manifest, calibration, freeze; no outcome contact) then ``--phase h2`` (re-runs
the deterministic H1 pipeline, hash-matches the frozen manifest cross-process per
R1.6, then spends the shot). The inter-phase verification is mechanical and may
halt only for machinery defects, never for unattractive entry attributes; H2 runs
regardless of how the H1 attributes look. Guard failures before H2 never spend
the shot.

All analysis machinery is REUSED VERBATIM: ``xen.avwap`` generator (frozen EXP-020
parameters), EXP-022 control-selection/lifetime code paths, EXP-037 FH/net
construction, ``xen.financing``, and the frozen EXP-027 inference tail. Zero
baseline: absolute bps vs 0; no percentage-of-baseline metric.

Run (two invocations; verify H1 artifacts between them):
    cd <project-root>
    python python/experiments/EXP-032/code/run_experiment.py --phase h1
    python python/experiments/EXP-032/code/run_experiment.py --phase h2
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.financing import elapsed_calendar_days, verify_financing  # noqa: E402
from xen.referee_calibration import (  # noqa: E402
    DOMAIN_SPECS,
    REQUIRED_TIMEBAR_COLUMNS,
    load_analysis_data,
    seed_for,
    to_canonical_time,
)


def _load_module(name: str, path: Path):
    """Import a module by file path without executing any ``main`` guard."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Frozen prior code paths, reused verbatim (no reimplementation):
#  - EXP-037: FH/net construction, frozen-tail verification, single-cell inference,
#    variance components, BTC-exit overlay (its import also pins the EXP-027 tail).
#  - EXP-022: control selection + lifetime scan (entry-attribute parts run in H1;
#    the lifetime scan itself is an OUTCOME helper and is called only from H2).
EXP037 = _load_module(
    "exp037_run", PROJECT_ROOT / "python" / "experiments" / "EXP-037" / "code"
    / "run_experiment.py")
EXP022 = _load_module(
    "exp022_run", PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "code"
    / "run_experiment.py")
EM = sys.modules["exp027_event_method"]  # registered by the EXP-037 module load

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants (ALL FROZEN, inherited — no selection happens in this experiment)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-032"
REGISTRY_ID = "CF-AVWAP-001/HOLDOUT-B"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
MANIFEST_PATH = RESULTS_DIR / "frozen_holdout_manifest.json"
VERDICT_PATH = RESULTS_DIR / "holdout_verdict.csv"
EVENTS_PATH = RESULTS_DIR / "holdout_events.csv"
ANALYSIS_NETS_PATH = RESULTS_DIR / "analysis_fh_nets.csv"
METADATA_PATH = RESULTS_DIR / "run_metadata.json"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP037_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-037" / "results"

INSTRUMENT = "EURUSD"
DOMAIN = "4h"
ANALYSIS_FRACTION = 0.7

# Frozen EXP-037 selection (verified against the pinned content hash before use).
H_STAR = 12
POLICY = "all_legs"
EXP037_SELECTION_SHA256 = (
    "2bbbf65ba0a3d9d50ad0c988e3845bdae93edc863756c810ff4f53f3770b0fea")
# Frozen EXP-030 CONSERVATIVE cost + D0/EXP-034 financing (EURUSD).
RT_CONS_BPS = 3.0
FINANCING_RATE_BPS_PER_DAY = 0.6
# Frozen EXP-027 inference tail pin (same as EXP-030/033/034/037/038).
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"
# Frozen inference convention.
N_BOOT = 1000
ALPHA = 0.05
# R1.2-analog null calibration (synthetic data only, persisted before the freeze).
N_NULL_CAL = 2000
MARGIN_QUANTILE = 95.0

# Reconciliation expectations (guard 1b/1c; any mismatch is a hard stop).
EXPECTED_ANALYSIS_EVENTS = 39          # reportable EURUSD-4h events (EXP-030/037)
EXPECTED_TRAIN_N = 27
EXPECTED_TEST_N = 12
EXP037_TEST_NET_BPS = 40.558882        # test_verdicts.csv EURUSD net (anchor)
RECON_TOL_BPS = 0.01
DETERMINISM_TOL = 1e-12
# Predeclared power expectation (scope) — DISCLOSURE ONLY; a deviation is logged
# and acknowledged but NEVER halts H2 (execution addendum: no attribute-based
# discretion may enter between freeze and read).
EXPECTED_HOLDOUT_RANGE = (15, 18)

MANIFEST_KEYS = ("regime_id", "direction", "event_trigger_idx", "start_idx")

# Seal registry: every Parquet file opened by this run (disclosed in metadata).
FILES_OPENED: list[dict[str, Any]] = []


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
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


def content_hash(record: dict[str, Any]) -> str:
    """EXP-037-identical content hash of a record (excluding the hash field)."""
    payload = {k: v for k, v in record.items() if k != "content_sha256"}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Integrity guards: hash pins (guard 2/3) + financing self-check
# --------------------------------------------------------------------------- #
def verify_exp037_selection() -> dict[str, Any]:
    """Guard 2: pin EXP-037 ``frozen_selection.json`` by content hash; return it.

    H*=12, all_legs, and the 27/12 EURUSD stratum manifest are read ONLY from this
    hash-verified record. Also asserts the frozen constants this script inherits
    match the EXP-037 record and module constants (no silent drift).
    """
    record = load_json(EXP037_RESULTS / "frozen_selection.json")
    got = content_hash(record)
    if got != EXP037_SELECTION_SHA256 or record.get("content_sha256") != got:
        raise ValueError(
            f"FROZEN-SELECTION HASH PIN FAILED: got {got}, "
            f"pinned {EXP037_SELECTION_SHA256}")
    if int(record["h_star"]) != H_STAR or record["pyramid_policy"] != POLICY:
        raise ValueError("frozen_selection.json H*/policy diverge from scope constants")
    if (EXP037.RT_CONS_BPS[INSTRUMENT] != RT_CONS_BPS
            or EXP037.FINANCING_RATE_BPS_PER_DAY[INSTRUMENT]
            != FINANCING_RATE_BPS_PER_DAY):
        raise ValueError("EXP-037 cost/financing constants diverge from scope constants")
    LOGGER.info("Guard 2 PASS: EXP-037 frozen selection hash-pinned (H*=%d, %s)",
                H_STAR, POLICY)
    return record


def exp037_eur_manifest(record: dict[str, Any]) -> tuple[set[tuple], set[tuple], int]:
    """EXP-037 EURUSD stratum manifest as (train_keys, test_keys, boundary_ns)."""
    rows = [m for m in record["stratum_manifest"] if m["instrument"] == INSTRUMENT]
    train = {tuple(int(m[k]) for k in MANIFEST_KEYS)
             for m in rows if m["stratum"] == "TRAIN"}
    test = {tuple(int(m[k]) for k in MANIFEST_KEYS)
            for m in rows if m["stratum"] == "TEST"}
    return train, test, int(record["boundary_ns"][INSTRUMENT])


# --------------------------------------------------------------------------- #
# Sanctioned full-series EURUSD load (Phase 009 design §5) + seal registry
# --------------------------------------------------------------------------- #
def eurusd_source_path() -> Path:
    """Resolve the EURUSD timebars file and pin it to the EXP-020 lineage source."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    source = expected.filter((pl.col("instrument") == INSTRUMENT)
                             & (pl.col("domain") == DOMAIN))
    if source.height != 1:
        raise ValueError("EXP-020 metadata: expected one EURUSD/4h row")
    path = DATA_DIR / "timebars" / str(source.get_column("source_file").item())
    if not path.exists():
        raise FileNotFoundError(f"missing EXP-020 EURUSD source file: {path}")
    if "eurusd" not in path.name.lower():
        raise ValueError(f"SEAL VIOLATION: resolved non-EURUSD file {path.name}")
    return path


def load_full_eurusd(path: Path) -> tuple[pl.DataFrame, Any, int]:
    """Sanctioned full-series EURUSD 1-minute load (lazy, column-projected).

    Returns ``(full_frame, analysis_data, boundary_ns)``. The analysis prefix is
    loaded through the canonical ``load_analysis_data`` path (the exact
    EXP-020/022/037 lineage loader) and the full frame must reproduce it row-for-row
    on the first 70% (loader-equivalence check). The holdout boundary is the
    CloseTime of 1-minute row ``analysis_rows - 1``; only THIS file's rows past the
    cutoff are ever materialized (seal disclosure in FILES_OPENED).
    """
    scan = pl.scan_parquet(path).select(REQUIRED_TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    full = to_canonical_time(scan.sort("CloseTime").collect())
    if not full.get_column("CloseTime").is_sorted():
        raise ValueError("full EURUSD series is not sorted by CloseTime")
    data = load_analysis_data(path)  # canonical analysis-slice path (same file)
    if data.instrument != INSTRUMENT:
        raise ValueError(f"SEAL VIOLATION: loaded {data.instrument}, not {INSTRUMENT}")
    if total_rows != data.total_rows or data.analysis_rows != int(total_rows
                                                                  * ANALYSIS_FRACTION):
        raise ValueError("row-count mismatch between full scan and analysis loader")
    if not full.slice(0, data.analysis_rows).equals(data.frame):
        raise ValueError("full-series prefix does not reproduce the canonical "
                         "analysis slice (loader equivalence broken)")
    boundary_ns = int(full.get_column("CloseTime").cast(pl.Datetime("ns"))
                      .cast(pl.Int64)[data.analysis_rows - 1])
    FILES_OPENED.append({
        "file": path.name, "purpose": "sanctioned EURUSD full-series read",
        "total_rows": total_rows, "analysis_rows": data.analysis_rows,
        "holdout_rows_materialized": total_rows - data.analysis_rows,
        "rows_materialized": f"0..{total_rows - 1}",
    })
    LOGGER.info("EURUSD full series loaded: %d rows (analysis %d, holdout %d); "
                "boundary=%s", total_rows, data.analysis_rows,
                total_rows - data.analysis_rows, data.analysis_end)
    return full, data, boundary_ns


def rebuild_4h(full: pl.DataFrame, analysis_1m: pl.DataFrame,
               boundary_ns: int) -> tuple[pl.DataFrame, pl.DataFrame,
                                          list[dict[str, Any]]]:
    """EXP-031/033/037-identical 4h rebuilds (full series + analysis-only).

    Only the 4h view is built from the full series (no 5m/1h holdout aggregation —
    seal discipline). Prefix-equality guard: full-series 4h bars with CloseTime <=
    boundary must be identical to the analysis-only rebuild EXP-037 used
    (aggregation is causal/clock-aligned; any drift is a hard stop). The
    analysis-only rebuild is also pinned to the EXP-020 metadata (bar count, max
    CloseTime).
    """
    spec = DOMAIN_SPECS[DOMAIN]
    full_4h = to_canonical_time(aggregate_ohlc(
        full, period_minutes=spec.period_minutes, min_coverage=spec.min_coverage))
    analysis_4h = to_canonical_time(aggregate_ohlc(
        analysis_1m, period_minutes=spec.period_minutes,
        min_coverage=spec.min_coverage))
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    exp = expected.filter((pl.col("instrument") == INSTRUMENT)
                          & (pl.col("domain") == DOMAIN)).to_dicts()[0]
    if (analysis_4h.height != int(exp["domain_bars"])
            or str(analysis_4h.get_column("CloseTime").max())
            != str(exp["domain_max_close_time"])):
        raise ValueError("analysis-only 4h rebuild diverged from EXP-020 metadata")
    close_ns = full_4h.get_column("CloseTime").cast(pl.Datetime("ns")).cast(pl.Int64)
    n_pref = int((close_ns <= boundary_ns).sum())
    if not analysis_4h.slice(0, n_pref).equals(full_4h.slice(0, n_pref)):
        raise ValueError("PREFIX-EQUALITY FAILED: full-series 4h rebuild diverges "
                         "from the analysis-only rebuild on the analysis prefix")
    rows = [
        {"check": "analysis_4h_vs_exp020_metadata", "value": float(analysis_4h.height),
         "expected": float(exp["domain_bars"]), "detail": None, "passed": True},
        {"check": "full_4h_prefix_equality", "value": float(n_pref),
         "expected": float(n_pref),
         "detail": f"analysis-only trailing partial bars past shared prefix: "
                   f"{analysis_4h.height - n_pref}", "passed": True},
    ]
    LOGGER.info("4h rebuild: full=%d bars, analysis=%d bars, shared prefix=%d "
                "(prefix-equality PASS)", full_4h.height, analysis_4h.height, n_pref)
    return full_4h, analysis_4h, rows


def series_arrays(frame_4h: pl.DataFrame) -> dict[str, np.ndarray]:
    """EXP-037-shaped per-cell arrays for ``add_fh_net_columns``/``attach_btc_net``."""
    close = frame_4h.get_column("Close").to_numpy().astype(float)
    return {
        "log_close": np.log(close),
        "close": close,
        "close_time": frame_4h.get_column("CloseTime").to_numpy()
        .astype("datetime64[ns]"),
    }


# --------------------------------------------------------------------------- #
# H1 — population regeneration (ENTRY ATTRIBUTES ONLY; no outcome helpers here)
# --------------------------------------------------------------------------- #
def build_population(events_gen: pl.DataFrame, regimes_gen: pl.DataFrame,
                     n_bars: int, boundary_ns: int) -> tuple[pl.DataFrame, int]:
    """EXP-022-identical event records from entry attributes only.

    Mirrors EXP-022 ``_event_with_controls`` UP TO (and excluding) the lifetime
    scan: target-geometry validity, same-regime control selection (EXP-021 rule,
    reused verbatim), and the reportability flag ``n_controls >= MIN_CONTROLS``.
    No price-difference quantity is computed — this is the H1-safe population.

    Returns the population frame (one row per geometry-valid event) and the
    invalid-target-geometry count (disclosed, EXP-022-identical exclusion).
    """
    regime_lut = EXP022.build_regime_lut(regimes_gen)
    trig = events_gen.get_column("trigger_idx").to_numpy().astype(np.int64)
    is_trigger, near_trigger = EXP022.build_exclusion_masks(n_bars, trig)
    base_cache: dict[int, np.ndarray] = {}
    rows: list[dict[str, Any]] = []
    n_invalid = 0
    for ev in events_gen.iter_rows(named=True):
        rid = int(ev["regime_id"])
        if rid not in regime_lut:
            raise ValueError(f"event regime_id={rid} absent from regime table")
        meta = regime_lut[rid]
        direction = int(ev["direction"])
        t = int(ev["trigger_idx"])
        fav_bps, adv_bps, *_ = EXP022.transfer_targets(
            direction, float(ev["favorable_target_at_trigger"]),
            float(ev["adverse_target_at_trigger"]), float(ev["trigger_close"]),
            float(ev["trigger_close"]))
        if not (fav_bps > 0.0 and adv_bps < 0.0):
            n_invalid += 1
            continue
        if rid not in base_cache:
            base_cache[rid] = EXP022.regime_candidate_base(
                meta["start_idx"], meta["end_idx"], is_trigger, near_trigger)
        controls = EXP022.select_controls(
            base_cache[rid], meta["anchor_idx"], int(ev["anchor_age_bars"]), t, n_bars)
        trigger_ns = int(np.datetime64(ev["trigger_time"], "ns").astype(np.int64))
        rows.append({
            "instrument": INSTRUMENT, "domain": DOMAIN, "regime_id": rid,
            "direction": direction, "is_pyramid_bounce": bool(ev["is_pyramid_bounce"]),
            "start_idx": t, "event_trigger_idx": t,
            "start_close": float(ev["trigger_close"]),
            "favorable_target": float(ev["favorable_target_at_trigger"]),
            "adverse_target": float(ev["adverse_target_at_trigger"]),
            "trigger_ns": trigger_ns,
            "n_controls": len(controls),
            "reportable_event": len(controls) >= EXP022.MIN_CONTROLS,
            "is_holdout": trigger_ns > boundary_ns,  # ties -> analysis (R1.3)
        })
    population = pl.DataFrame(rows)
    LOGGER.info("Population regenerated over full series: %d geometry-valid events "
                "(%d invalid-geometry excluded, EXP-022-identical)",
                population.height, n_invalid)
    return population, n_invalid


def reconcile_analysis_stratum(
    population: pl.DataFrame, train_keys: set[tuple], test_keys: set[tuple],
    exp037_boundary_ns: int,
) -> tuple[list[dict[str, Any]], pl.DataFrame]:
    """Guard 1b: the analysis stratum must reproduce the certified lineage exactly.

    (i) Geometry-valid analysis-stratum events match the EXP-022
    ``lifetime_observations.csv`` EURUSD-4h event keys with identical reportability
    flags; (ii) the reportable subset equals the EXP-037 39-event manifest; (iii)
    the EXP-037 ``boundary_ns`` partitions it 27 TRAIN / 12 TEST with identical
    per-key strata. Any mismatch is a hard stop — the generator lineage is broken
    and the holdout read must not proceed. Returns (check rows, reportable
    analysis-stratum frame).
    """
    analysis = population.filter(~pl.col("is_holdout"))
    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    ref = EXP037.ensure_bool(lifetime, ("reportable_event",)).filter(
        (pl.col("instrument") == INSTRUMENT) & (pl.col("domain") == DOMAIN)
        & (pl.col("role") == "event"))
    ref_flags = {(int(r["regime_id"]), int(r["direction"]), int(r["event_trigger_idx"])):
                 bool(r["reportable_event"]) for r in ref.to_dicts()}
    got_flags = {(int(r["regime_id"]), int(r["direction"]), int(r["event_trigger_idx"])):
                 bool(r["reportable_event"]) for r in analysis.to_dicts()}
    flags_ok = got_flags == ref_flags

    reportable = analysis.filter(pl.col("reportable_event"))
    got_keys = {tuple(int(r[k]) for k in MANIFEST_KEYS) for r in reportable.to_dicts()}
    keys_ok = got_keys == (train_keys | test_keys)

    got_train = {k for k, ns in
                 zip((tuple(int(r[c]) for c in MANIFEST_KEYS)
                      for r in reportable.to_dicts()),
                     reportable.get_column("trigger_ns").to_list())
                 if int(ns) <= exp037_boundary_ns}
    part_ok = (got_train == train_keys
               and (got_keys - got_train) == test_keys)
    rows = [
        {"check": "exp022_event_keys_and_reportability",
         "value": float(len(got_flags)), "expected": float(len(ref_flags)),
         "detail": "keys+flags identical" if flags_ok else "MISMATCH",
         "passed": flags_ok},
        {"check": "exp037_reportable_keys", "value": float(len(got_keys)),
         "expected": float(EXPECTED_ANALYSIS_EVENTS),
         "detail": "39-event manifest reproduced" if keys_ok else "MISMATCH",
         "passed": keys_ok and len(got_keys) == EXPECTED_ANALYSIS_EVENTS},
        {"check": "exp037_train_test_partition", "value": float(len(got_train)),
         "expected": float(EXPECTED_TRAIN_N),
         "detail": f"train={len(got_train)},test={len(got_keys - got_train)}",
         "passed": part_ok},
    ]
    failures = [r["check"] for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"GUARD 1b FAILED (lineage reconciliation): {failures}")
    LOGGER.info("Guard 1b PASS: analysis stratum reproduces EXP-022/EXP-037 lineage "
                "(%d events; 27 TRAIN / 12 TEST)", reportable.height)
    return rows, reportable


def reproduce_exp037_test_anchor(
    reportable_analysis: pl.DataFrame, analysis_arrs: dict[str, np.ndarray],
    test_keys: set[tuple],
) -> tuple[list[dict[str, Any]], pl.DataFrame]:
    """Guard 1c: reproduce the EXP-037 TEST net (+40.558882 bps) to <= 0.01 bps.

    Recomputes FH(12)/all_legs nets through the verbatim EXP-037 estimator
    (``add_fh_net_columns`` on the ANALYSIS-ONLY 4h series — EXP-037's own
    truncation universe) for all 39 disclosed analysis events, and checks the
    event-weighted TEST mean. Returns (check rows, 39-event frame with ``net_12``)
    — the disclosed-data dispersion input for the null calibration and plot 3.
    """
    nets = EXP037.add_fh_net_columns(
        EXP037.apply_policy(reportable_analysis, POLICY),
        {INSTRUMENT: analysis_arrs}, (H_STAR,))
    is_test = pl.Series(
        [tuple(int(r[k]) for k in MANIFEST_KEYS) in test_keys
         for r in nets.to_dicts()])
    test_net = float(nets.filter(is_test).get_column(f"net_{H_STAR}").mean())
    diff = abs(test_net - EXP037_TEST_NET_BPS)
    ok = diff <= RECON_TOL_BPS and int(is_test.sum()) == EXPECTED_TEST_N
    rows = [{"check": "exp037_test_reproduction_anchor", "value": test_net,
             "expected": EXP037_TEST_NET_BPS, "detail": f"abs_diff={diff:.6f}",
             "passed": ok}]
    if not ok:
        raise ValueError(f"GUARD 1c FAILED: TEST anchor {test_net:.6f} vs "
                         f"{EXP037_TEST_NET_BPS} (diff {diff:.6f} > {RECON_TOL_BPS})")
    LOGGER.info("Guard 1c PASS: EXP-037 TEST net reproduced (%.6f bps, "
                "diff %.6f <= %.2f)", test_net, diff, RECON_TOL_BPS)
    return rows, nets


# --------------------------------------------------------------------------- #
# H1 — synthetic-null calibration and binding margin (R1.2 analog)
# --------------------------------------------------------------------------- #
def null_calibration_holdout_cell(
    analysis_nets: pl.DataFrame, holdout: pl.DataFrame,
) -> dict[str, Any]:
    """R1.2-analog calibration of the frozen bootstrap at the holdout structure.

    Cluster layout from the holdout stratum's ENTRY attributes (per-(direction,
    regime_id) sizes under all_legs); zero-mean Gaussian cluster nulls
    (r = a_c + e_i) with method-of-moments components from the full-analysis
    39-event FH(12)/all_legs nets (already-disclosed data); R = N_NULL_CAL
    replicates each scored by the frozen 1000-resample bootstrap. No holdout
    outcome is touched. Returns the calibration record incl. the binding margin
    ``m_cell = max(0, Q95 of null ci_low_1s)``.
    """
    values = analysis_nets.get_column(f"net_{H_STAR}").to_numpy().astype(float)
    clusters = (analysis_nets.get_column("direction").cast(pl.Int64) * 1_000_000
                + analysis_nets.get_column("regime_id").cast(pl.Int64)).to_numpy()
    sigma_b, sigma_w = EXP037.estimate_variance_components(values, clusters)
    layout = (holdout.group_by(["direction", "regime_id"]).agg(pl.len().alias("n"))
              .sort(["direction", "regime_id"]).to_dicts())
    if not layout:
        raise ValueError("holdout stratum is empty — calibration (and the holdout "
                         "read) is undefined")
    dir_labels = np.concatenate([np.full(r["n"], int(r["direction"]), dtype=int)
                                 for r in layout])
    regime_labels = np.concatenate([np.full(r["n"], j, dtype=int)
                                    for j, r in enumerate(layout)])
    inst_labels = np.full(dir_labels.size, INSTRUMENT)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "nullcal", DOMAIN, INSTRUMENT))
    ci_lows = np.empty(N_NULL_CAL)
    boot_ps = np.empty(N_NULL_CAL)
    for k in tqdm(range(N_NULL_CAL), desc="null calibration (holdout cell)",
                  leave=False):
        cluster_fx = rng.normal(0.0, sigma_b, size=len(layout))
        diffs = cluster_fx[regime_labels] + rng.normal(0.0, sigma_w,
                                                       size=dir_labels.size)
        strata = EM.build_strata(diffs, inst_labels, dir_labels, regime_labels,
                                 [INSTRUMENT])
        boot = EM.bootstrap_effect_distribution(
            strata, [INSTRUMENT], rng, EXP037.N_BOOT, EXP037.CHUNK)
        ci_lows[k] = np.percentile(boot, 100.0 * ALPHA)
        boot_ps[k] = (1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT)
    margin = max(0.0, float(np.percentile(ci_lows, MARGIN_QUANTILE)))
    record = {
        "instrument": INSTRUMENT, "domain": DOMAIN, "h_star": H_STAR,
        "policy": POLICY, "n_holdout_events": int(holdout.height),
        "n_holdout_clusters": len(layout),
        "n_dispersion_events": int(analysis_nets.height),
        "sigma_b_bps": sigma_b, "sigma_w_bps": sigma_w,
        "n_null_replicates": N_NULL_CAL,
        "fpr_uncorrected": float(np.mean((boot_ps <= ALPHA) & (ci_lows > 0.0))),
        "margin_bps": margin,
        "fpr_with_margin": float(np.mean((boot_ps <= ALPHA) & (ci_lows > margin))),
    }
    LOGGER.info("Null calibration: FPR(raw)=%.4f -> m_cell=%.3f bps "
                "(FPR with margin=%.4f)", record["fpr_uncorrected"], margin,
                record["fpr_with_margin"])
    return record


# --------------------------------------------------------------------------- #
# H1 — freeze-before-outcome barrier (load-bearing; R1.6 recovery semantics)
# --------------------------------------------------------------------------- #
def freeze_holdout_manifest(
    holdout: pl.DataFrame, calibration: dict[str, Any], boundary_ns: int,
    exp037_boundary_ns: int, recon_rows: list[dict[str, Any]],
    counts: dict[str, int],
) -> dict[str, Any]:
    """Persist the holdout stratum manifest + margin + frozen constants (H1 freeze).

    Written BEFORE any holdout outcome exists; H2 reads population/margin/constants
    ONLY from this file. Recovery semantics (EXP-037 R1.6-identical): if the
    manifest already exists, the recomputed record must content-hash-match exactly
    (hard stop on mismatch — a rerun is never a second predeclaration).
    """
    manifest_rows = [
        {k: int(r[k]) for k in MANIFEST_KEYS}
        | {"trigger_ns": int(r["trigger_ns"]),
           "is_pyramid_bounce": bool(r["is_pyramid_bounce"]),
           "n_controls": int(r["n_controls"])}
        for r in holdout.sort("event_trigger_idx").to_dicts()]
    record = {
        "experiment_id": EXPERIMENT_ID, "registry_id": REGISTRY_ID,
        "frozen_on_emission": True,
        "frozen_constants": {
            "h_star": H_STAR, "pyramid_policy": POLICY,
            "rt_cons_bps": RT_CONS_BPS,
            "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
            "frozen_tail_hash": FROZEN_TAIL_EXPECTED_HASH,
            "exp037_selection_sha256": EXP037_SELECTION_SHA256,
            "n_boot": N_BOOT, "alpha_one_sided": ALPHA,
            "n_null_calibration": N_NULL_CAL,
        },
        "boundary_ns": boundary_ns,
        "exp037_train_test_boundary_ns": exp037_boundary_ns,
        "boundary_convention": "HOLDOUT iff trigger close time > boundary; "
                               "ties -> analysis (R1.3, entry-bar keyed)",
        "counts": counts,
        "holdout_stratum_manifest": manifest_rows,
        "cluster_layout": (holdout.group_by(["direction", "regime_id"])
                           .agg(pl.len().alias("n"))
                           .sort(["direction", "regime_id"]).to_dicts()),
        "calibration": calibration,
        "reconciliation_digest": [
            {"check": r["check"], "passed": bool(r["passed"])} for r in recon_rows],
        "files_opened": FILES_OPENED,
        # Environment record (execution addendum class c): a rerun in a drifted
        # environment is detected here with a named cause — rebuild the recorded
        # environment; NEVER regenerate the manifest.
        "environment": {"python": sys.version.split()[0],
                        "numpy": np.__version__, "polars": pl.__version__},
    }
    record["content_sha256"] = content_hash(record)
    if MANIFEST_PATH.exists():
        existing = load_json(MANIFEST_PATH)
        if existing.get("content_sha256") != record["content_sha256"]:
            diffs = [k for k in record if k != "content_sha256"
                     and json.dumps(existing.get(k), sort_keys=True, default=str)
                     != json.dumps(record.get(k), sort_keys=True, default=str)]
            raise ValueError(
                "FREEZE MISMATCH: existing frozen_holdout_manifest.json does not "
                f"reproduce under rerun — hard stop (R1.6). Differing fields: "
                f"{diffs}. If 'environment' differs, rebuild the recorded "
                "environment (execution addendum class c); do not regenerate.")
        LOGGER.info("FREEZE already on disk and hash-matched — rerun resume (R1.6)")
        return existing
    MANIFEST_PATH.write_text(json.dumps(record, indent=2, default=str))
    LOGGER.info("FREEZE written: %s (n_holdout=%d, m_cell=%.3f bps)",
                MANIFEST_PATH.name, len(manifest_rows),
                calibration["margin_bps"])
    return record


# --------------------------------------------------------------------------- #
# H2 — one-shot holdout outcome + inference (the ONLY holdout outcome contact)
# --------------------------------------------------------------------------- #
def binding_verdict(res: dict[str, Any], margin: float) -> tuple[str, str]:
    """Mechanical verdict + descriptive label (LOCKED, computed by code)."""
    if res["ci_low_1s"] > margin and res["boot_p"] <= ALPHA:
        verdict = "HOLDOUT_CONFIRMED"
    elif res["ci_high"] < 0.0:
        verdict = "HOLDOUT_REFUTED"
    else:
        verdict = "HOLDOUT_INCONCLUSIVE"
    if res["ci_low"] > 0.0:
        label = "EVIDENCE_FOR"
    elif res["ci_high"] < 0.0:
        label = "EVIDENCE_AGAINST"
    else:
        label = "INCONCLUSIVE_SPANS_ZERO"
    return verdict, label


def btc_exit_companion(
    holdout_net: pl.DataFrame, regimes_gen: pl.DataFrame,
    full_arrs: dict[str, np.ndarray],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """NON-BINDING Package-A companion: BTC-exit net on the same holdout events.

    EXP-022 lifetime construction (frozen targets, trend-change boundary at the
    first later opposite regime confirmation, scan to the true series end) plus the
    EXP-034 cost/financing overlay via the verbatim ``attach_btc_net``. Point
    estimate only — computed in the same H2 pass; never promotable.
    """
    tc_map = EXP022.build_trend_change_map(regimes_gen)
    close = full_arrs["close"]
    log_close = full_arrs["log_close"]
    end_idx = close.size - 1
    outcomes, comp_idx, life = [], [], []
    for r in holdout_net.to_dicts():
        out, comp, _bars, bps, _tie = EXP022.scan_lifetime(
            close, log_close, int(r["start_idx"]), int(r["direction"]),
            float(r["favorable_target"]), float(r["adverse_target"]),
            tc_map.get(int(r["regime_id"])), end_idx)
        outcomes.append(out)
        comp_idx.append(comp)
        life.append(bps)
    frame = holdout_net.with_columns([
        pl.Series("btc_outcome", outcomes),
        pl.Series("completion_idx", comp_idx, dtype=pl.Int64),
        pl.Series("lifetime_bps", life, dtype=pl.Float64),
    ])
    completed = frame.filter(pl.col("btc_outcome").is_in(EXP037.COMPLETED_OUTCOMES)
                             & pl.col("lifetime_bps").is_not_null())
    companion: dict[str, Any] = {
        "btc_net_bps": None, "n_btc_completed": int(completed.height),
        "n_btc_unfinished": int(frame.height - completed.height),
    }
    if completed.height:
        with_net = EXP037.attach_btc_net(completed, {INSTRUMENT: full_arrs})
        companion["btc_net_bps"] = float(with_net.get_column("net_btc").mean())
        frame = frame.join(
            with_net.select(list(MANIFEST_KEYS) + ["net_btc"]),
            on=list(MANIFEST_KEYS), how="left")
    else:
        frame = frame.with_columns(pl.lit(None, dtype=pl.Float64).alias("net_btc"))
    return frame, companion


def weekend_spotcheck(holdout_net: pl.DataFrame,
                      full_arrs: dict[str, np.ndarray]) -> dict[str, Any] | None:
    """First weekend-spanning FH hold: entry/exit/days/financing (audit trail)."""
    ct = full_arrs["close_time"]
    n = ct.size
    for r in holdout_net.sort("event_trigger_idx").to_dicts():
        si = int(r["start_idx"])
        exit_idx = min(si + H_STAR, n - 1)
        entry, exit_ = ct[si], ct[exit_idx]
        day_idx = np.arange(entry.astype("datetime64[D]").astype(int),
                            exit_.astype("datetime64[D]").astype(int) + 1)
        if np.any((day_idx + 3) % 7 == 5):  # epoch day 0 = Thursday; Saturday = 5
            days = float(elapsed_calendar_days(entry, exit_))
            return {"event_trigger_idx": si, "entry": str(entry), "exit": str(exit_),
                    "elapsed_calendar_days": days,
                    "financing_bps": FINANCING_RATE_BPS_PER_DAY * days}
    return None


def run_h2(
    population: pl.DataFrame, regimes_gen: pl.DataFrame,
    full_arrs: dict[str, np.ndarray], tail_hash: str,
    disclosure: dict[str, Any],
) -> tuple[dict[str, Any], pl.DataFrame]:
    """Phase H2: the one-shot holdout outcome computation and binding inference.

    Hard gates (LOCKED): refuses to run if ``holdout_verdict.csv`` exists
    (no-second-read, R1.6); refuses unless ``frozen_holdout_manifest.json`` exists,
    parses, and content-hash-verifies; population, margin, and constants are read
    ONLY from the manifest (the population regenerated in THIS process is
    key-matched against it, hard stop on any divergence — under two-invocation
    execution this is a genuine cross-process check). Outcome construction is
    EXP-033/037-identical on the full-series rebuild; inference is the frozen tail
    with a same-seed determinism replay.

    Persistence order (F01): every mandated disclosure is assembled BEFORE any
    write, then written per-event table -> run_metadata.json ->
    holdout_verdict.csv (the verdict file is last so the no-second-read guard
    marks a fully persisted read; a crash before it leaves a deterministic,
    resumable rerun). Returns (verdict row, per-event holdout frame).
    """
    if VERDICT_PATH.exists():
        raise ValueError("NO-SECOND-READ: holdout_verdict.csv already exists — the "
                         "holdout has been read; refusing to recompute (R1.6). "
                         "The shot is spent.")
    if not MANIFEST_PATH.exists():
        raise ValueError("FREEZE-BEFORE-OUTCOME VIOLATION: "
                         "frozen_holdout_manifest.json missing")
    manifest = load_json(MANIFEST_PATH)
    if manifest.get("content_sha256") != content_hash(manifest):
        raise ValueError("FREEZE-BEFORE-OUTCOME VIOLATION: manifest hash check failed")
    fz = manifest["frozen_constants"]
    h_star, margin = int(fz["h_star"]), float(manifest["calibration"]["margin_bps"])
    frozen_keys = {tuple(int(m[k]) for k in MANIFEST_KEYS)
                   for m in manifest["holdout_stratum_manifest"]}
    live = EXP037.apply_policy(
        population.filter(pl.col("is_holdout") & pl.col("reportable_event")),
        str(fz["pyramid_policy"]))
    live_keys = {tuple(int(r[k]) for k in MANIFEST_KEYS) for r in live.to_dicts()}
    if live_keys != frozen_keys:
        raise ValueError("holdout membership diverges from the frozen manifest")

    # --- the one-shot outcome computation (first holdout price contact) ---------
    holdout_net = EXP037.add_fh_net_columns(live, {INSTRUMENT: full_arrs}, (h_star,))
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "holdout", DOMAIN, INSTRUMENT))
    res = EXP037.infer_test_cell(holdout_net, INSTRUMENT, f"net_{h_star}", rng)
    replay = EXP037.infer_test_cell(
        holdout_net, INSTRUMENT, f"net_{h_star}",
        np.random.default_rng(seed_for(EXPERIMENT_ID, "holdout", DOMAIN, INSTRUMENT)))
    drift = max(abs(res[k] - replay[k])
                for k in ("effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p"))
    if drift > DETERMINISM_TOL:
        raise ValueError(f"DETERMINISM REPLAY FAILED: max drift {drift}")
    verdict, label = binding_verdict(res, margin)

    # --- non-binding companions (same pass, same events; never promotable) ------
    holdout_net, companion = btc_exit_companion(holdout_net, regimes_gen, full_arrs)
    # Per-event financing disclosure (same-pass arithmetic on already-computed
    # holding windows; truncation column carried, never silent).
    si = holdout_net.get_column("start_idx").to_numpy().astype(np.int64)
    exit_idx = np.minimum(si + h_star, full_arrs["close_time"].size - 1)
    days = elapsed_calendar_days(full_arrs["close_time"][si],
                                 full_arrs["close_time"][exit_idx])
    holdout_net = holdout_net.with_columns([
        pl.Series("fh_exit_idx", exit_idx),
        pl.Series("financing_days", days),
        pl.Series("financing_bps", FINANCING_RATE_BPS_PER_DAY * days),
    ])
    fh_col = holdout_net.get_column(f"fh_{h_star}")
    # financing = fh - rt - net (the net construction's only other subtrahend).
    fin_mean = float((fh_col - RT_CONS_BPS
                      - holdout_net.get_column(f"net_{h_star}")).mean())
    row = {
        "instrument": INSTRUMENT, "domain": DOMAIN, "h_star": h_star,
        "policy": fz["pyramid_policy"], "n_events": res["n_events"],
        "net_bps": res["effect_bps"], "ci_low": res["ci_low"],
        "ci_high": res["ci_high"], "ci_low_1s": res["ci_low_1s"],
        "boot_p": res["boot_p"], "margin_bps": margin,
        "binding_verdict": verdict, "descriptive_label": label,
        "gross_fh_bps": float(fh_col.mean()), "rt_cost_bps": RT_CONS_BPS,
        "financing_bps_mean": fin_mean,
        "btc_net_bps": companion["btc_net_bps"],
        "n_btc_completed": companion["n_btc_completed"],
        "n_btc_unfinished": companion["n_btc_unfinished"],
        "truncated_share": float(holdout_net.get_column(f"truncated_{h_star}")
                                 .cast(pl.Int8).mean()),
        "companion_note": "btc_net_bps and the decomposition are NON-BINDING "
                          "(Phase 009 design §6); family size 1, no Holm",
        "holdout_spent": True,
        "determinism_replay_max_drift": drift,
    }

    # --- assemble EVERY mandated disclosure before any write (F01) --------------
    spot = weekend_spotcheck(holdout_net, full_arrs)
    per_event = holdout_net.sort("event_trigger_idx").select(
        ["instrument", "domain", "regime_id", "direction", "event_trigger_idx",
         "start_idx", "trigger_ns", "is_pyramid_bounce", "start_close",
         f"fh_{h_star}", f"net_{h_star}", f"truncated_{h_star}", "fh_exit_idx",
         "financing_days", "financing_bps", "btc_outcome", "completion_idx",
         "lifetime_bps", "net_btc"])
    metadata = {
        "experiment_id": EXPERIMENT_ID, "registry_id": REGISTRY_ID,
        "frozen_tail_hash": tail_hash,
        "exp037_selection_sha256": EXP037_SELECTION_SHA256,
        "manifest_content_sha256": manifest["content_sha256"],
        "h_star": h_star, "pyramid_policy": fz["pyramid_policy"],
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "alpha_one_sided": ALPHA, "n_boot": N_BOOT,
        "n_null_calibration": N_NULL_CAL, "margin_bps": margin,
        "binding_rule": "HOLDOUT_CONFIRMED iff ci_low_1s > m_cell AND boot_p <= "
                        "0.05; HOLDOUT_REFUTED iff ci_high < 0; else "
                        "HOLDOUT_INCONCLUSIVE (family of 1, no Holm)",
        "binding_verdict": verdict, "descriptive_label": label,
        "holdout_spent": True,
        "no_second_read": "holdout_verdict.csv now exists; any rerun of H2 "
                          "hard-stops (R1.6). Post-verdict rendering and audit "
                          "read ONLY the persisted artifacts (holdout_events.csv, "
                          "analysis_fh_nets.csv, holdout_verdict.csv) — not a "
                          "second read.",
        "determinism_replay": {"max_drift": drift, "passed": True},
        "weekend_financing_spotcheck": spot,
        "files_opened": FILES_OPENED,
        "seal_note": "only the EURUSD timebars file was opened; BTCUSD/USTEC/"
                     "XAUUSD holdout rows remain sealed",
        **disclosure,
    }
    metadata_json = json.dumps(metadata, indent=2, default=str)  # pre-serialize

    # --- writes: per-event table -> metadata -> verdict (completion marker) -----
    per_event.write_csv(EVENTS_PATH)
    METADATA_PATH.write_text(metadata_json)
    write_rows(VERDICT_PATH, [row])
    LOGGER.info("H2 one-shot verdict: %s (net=%.2f bps, 1s-low=%.2f vs margin=%.2f, "
                "p=%.4f, n=%d)", verdict, row["net_bps"], row["ci_low_1s"],
                margin, row["boot_p"], row["n_events"])
    return row, holdout_net


# --------------------------------------------------------------------------- #
# Plotting (3 / 3 budget; bounded inputs returned by the analysis pass)
# --------------------------------------------------------------------------- #
def plot_binding_verdict(holdout_net: pl.DataFrame, row: dict[str, Any],
                         path: Path) -> None:
    """Plot 1: holdout per-event nets with mean, CIs, margin, and zero line."""
    nets = holdout_net.get_column(f"net_{H_STAR}").to_numpy()
    fig, ax = plt.subplots(figsize=(8, 5))
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "plot_jitter"))
    ax.scatter(rng.uniform(-0.08, 0.08, nets.size), nets, alpha=0.7, color="#34495e",
               label=f"per-event net (n={nets.size})", zorder=3)
    ax.axhspan(row["ci_low"], row["ci_high"], color="#3498db", alpha=0.15,
               label="two-sided 95% CI (descriptive)")
    ax.axhline(row["net_bps"], color="#3498db", lw=1.6,
               label=f"event-weighted mean ({row['net_bps']:.1f} bps)")
    ax.axhline(row["ci_low_1s"], color="#2e7d32", lw=1.4, ls="--",
               label=f"one-sided 95% lower bound ({row['ci_low_1s']:.1f} bps)")
    ax.axhline(row["margin_bps"], color="#c0392b", lw=1.4, ls=":",
               label=f"binding margin m_cell ({row['margin_bps']:.1f} bps)")
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xlim(-0.5, 0.5)
    ax.set_xticks([])
    ax.set_ylabel("Holdout net per-event expectancy (bps)")
    ax.set_title(f"EXP-032 one-shot holdout — FH(12)/all_legs EURUSD-4h\n"
                 f"{row['binding_verdict']} (boot_p={row['boot_p']:.4f})")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fh_vs_btc(row: dict[str, Any], path: Path) -> None:
    """Plot 2: binding FH(12) net vs BTC-exit companion on the same events."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    labels = [f"FH(12) exit (binding)\nn={row['n_events']}",
              f"BTC exit (companion)\nn={row['n_btc_completed']} completed"]
    values = [row["net_bps"],
              row["btc_net_bps"] if row["btc_net_bps"] is not None else np.nan]
    ax.bar([0, 1], values, width=0.5, color=["#3498db", "#e67e22"])
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Holdout net (bps)")
    ax.set_title("EXP-032 exit-mechanism comparison — descriptive, NON-BINDING\n"
                 "(point estimates on the identical holdout events)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_analysis_vs_holdout(analysis_nets: pl.DataFrame,
                             holdout_net: pl.DataFrame, path: Path) -> None:
    """Plot 3: analysis vs holdout per-event net distributions (context only)."""
    a = analysis_nets.get_column(f"net_{H_STAR}").to_numpy()
    h = holdout_net.get_column(f"net_{H_STAR}").to_numpy()
    fig, ax = plt.subplots(figsize=(8, 5))
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "plot_jitter_ah"))
    for x0, vals, color, name in ((0.0, a, "#7f8c8d", "analysis"),
                                  (1.0, h, "#3498db", "holdout")):
        ax.scatter(x0 + rng.uniform(-0.1, 0.1, vals.size), vals, alpha=0.65,
                   color=color, zorder=3)
        ax.hlines(float(vals.mean()), x0 - 0.2, x0 + 0.2, color=color, lw=2.0,
                  label=f"{name} mean ({float(vals.mean()):.1f} bps, n={vals.size})")
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"analysis (n={a.size})", f"holdout (n={h.size})"])
    ax.set_ylabel("Per-event net at FH(12)/all_legs (bps)")
    ax.set_title("EXP-032 analysis-vs-holdout context — no inference drawn")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run_h1(
    frozen_sel: dict[str, Any],
) -> tuple[dict[str, Any], pl.DataFrame, pl.DataFrame, pl.DataFrame,
           dict[str, np.ndarray], dict[str, Any]]:
    """Phase H1: guards, stratum manifest, calibration, and the freeze barrier.

    Structurally outcome-free for holdout rows: the only price-difference
    quantities computed here are the disclosed-data analysis nets (guard 1c /
    dispersion), on the ANALYSIS-ONLY series. Returns (manifest, population,
    analysis-net frame, regimes table, full-series arrays, disclosure dict).
    """
    train_keys, test_keys, exp037_boundary_ns = exp037_eur_manifest(frozen_sel)

    path = eurusd_source_path()
    full, analysis_data, boundary_ns = load_full_eurusd(path)
    full_4h, analysis_4h, prefix_rows = rebuild_4h(full, analysis_data.frame,
                                                   boundary_ns)
    full_arrs = series_arrays(full_4h)
    analysis_arrs = series_arrays(analysis_4h)

    LOGGER.info("Running frozen EXP-020/022 generator over the full 4h series "
                "(%d bars, sequential stateful stream)", full_4h.height)
    gen = generate_avwap_events(full_4h, instrument=INSTRUMENT, domain=DOMAIN)
    population, n_invalid = build_population(gen.events, gen.regimes,
                                             full_4h.height, boundary_ns)

    recon_rows, reportable_analysis = reconcile_analysis_stratum(
        population, train_keys, test_keys, exp037_boundary_ns)
    anchor_rows, analysis_nets = reproduce_exp037_test_anchor(
        reportable_analysis, analysis_arrs, test_keys)
    # Persist the disclosed-data per-event nets (analysis stratum only): the
    # audit/plot input that must never require holdout recomputation (F01).
    analysis_nets.sort("event_trigger_idx").select(
        ["instrument", "domain", "regime_id", "direction", "event_trigger_idx",
         "start_idx", "trigger_ns", "is_pyramid_bounce",
         f"fh_{H_STAR}", f"net_{H_STAR}", f"truncated_{H_STAR}"]
    ).write_csv(ANALYSIS_NETS_PATH)
    seal_rows = [{"check": "seal_only_eurusd_file_opened",
                  "value": float(len({f["file"] for f in FILES_OPENED})),
                  "expected": 1.0,
                  "detail": ";".join(sorted({f["file"] for f in FILES_OPENED})),
                  "passed": len({f["file"] for f in FILES_OPENED}) == 1}]
    if not seal_rows[0]["passed"]:
        raise ValueError("SEAL VIOLATION: more than one data file opened")
    all_recon = prefix_rows + recon_rows + anchor_rows + seal_rows
    write_rows(RESULTS_DIR / "reconciliation.csv", all_recon)

    holdout_all = population.filter(pl.col("is_holdout"))
    holdout = EXP037.apply_policy(holdout_all.filter(pl.col("reportable_event")),
                                  POLICY)
    counts = {
        "analysis_events_geometry_valid": int((~population.get_column("is_holdout"))
                                              .sum()),
        "analysis_events_reportable": int(reportable_analysis.height),
        "holdout_events_pre_reportability": int(holdout_all.height),
        "holdout_events_binding": int(holdout.height),
        "invalid_geometry_excluded": int(n_invalid),
    }
    LOGGER.info("Holdout stratum: %d events pre-reportability -> %d binding "
                "(all_legs)", holdout_all.height, holdout.height)
    write_rows(RESULTS_DIR / "holdout_stratum.csv",
               holdout.sort("event_trigger_idx")
               .select(["instrument", "domain", "regime_id", "direction",
                        "event_trigger_idx", "trigger_ns", "is_pyramid_bounce",
                        "n_controls", "reportable_event"]).to_dicts())

    calibration = null_calibration_holdout_cell(analysis_nets, holdout)
    write_rows(RESULTS_DIR / "null_calibration.csv", [calibration])

    manifest = freeze_holdout_manifest(holdout, calibration, boundary_ns,
                                       exp037_boundary_ns, all_recon, counts)
    disclosure = {"counts": counts, "n_4h_bars_full": int(full_4h.height),
                  "n_4h_bars_analysis": int(analysis_4h.height),
                  "boundary_close_time": str(analysis_data.analysis_end)}
    return manifest, population, analysis_nets, gen.regimes, full_arrs, disclosure


def verify_h1_artifacts(manifest: dict[str, Any]) -> None:
    """Mechanical inter-phase verification of the H1 artifacts (F03).

    Halts ONLY for defects in machinery: manifest hash failure, malformed or
    non-finite calibration record, or an empty stratum. The predeclared 15-18
    holdout-count expectation is a logged DISCLOSURE — a deviation is acknowledged
    and NEVER halts (no attribute-based discretion between freeze and read; H2
    runs regardless of how the entry attributes look).
    """
    if manifest.get("content_sha256") != content_hash(manifest):
        raise ValueError("H1 VERIFICATION FAILED: manifest hash check failed")
    cal = manifest["calibration"]
    for key in ("sigma_b_bps", "sigma_w_bps", "margin_bps", "fpr_uncorrected",
                "fpr_with_margin"):
        if not np.isfinite(float(cal[key])):
            raise ValueError(f"H1 VERIFICATION FAILED: calibration field {key} "
                             f"is not finite ({cal[key]!r})")
    n_holdout = len(manifest["holdout_stratum_manifest"])
    if n_holdout < 1:
        raise ValueError("H1 VERIFICATION FAILED: empty holdout stratum manifest")
    lo, hi = EXPECTED_HOLDOUT_RANGE
    note = ("within" if lo <= n_holdout <= hi else
            "OUTSIDE (disclosure only — acknowledged, does not halt)")
    LOGGER.info("H1 verification PASS: manifest hash OK, calibration well-formed "
                "(m_cell=%.3f bps), n_holdout=%d — %s the predeclared %d-%d "
                "expectation", float(cal["margin_bps"]), n_holdout, note, lo, hi)


def parse_args() -> argparse.Namespace:
    """CLI: the freeze and the irreversible read are separate invocations (F03)."""
    parser = argparse.ArgumentParser(description=(
        "EXP-032 one-shot holdout confirmation. Run '--phase h1' first (guards, "
        "stratum manifest, calibration, freeze; no holdout outcome contact), "
        "verify the H1 artifacts, then run '--phase h2' (the irreversible read). "
        "H2 WILL run regardless of how the H1 entry attributes look — the "
        "inter-phase check may halt only for machinery defects."))
    parser.add_argument("--phase", choices=("h1", "h2"), required=True)
    return parser.parse_args()


def main() -> None:
    """Run EXP-032: guards -> H1 freeze (invocation 1) -> one-shot H2 (invocation 2)."""
    phase = parse_args().phase
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s [phase %s]: one-shot holdout confirmation of Package B "
                "(EURUSD-4h, FH H*=%d, %s) ===", EXPERIMENT_ID, phase.upper(),
                H_STAR, POLICY)

    # Hard gates before anything else is emitted (guards 2/3 + financing check).
    tail_hash = EXP037.verify_frozen_inference()
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    frozen_sel = verify_exp037_selection()

    # ---- Phase H1 (entry attributes only; freeze-before-outcome) --------------
    # In the H2 invocation this re-runs deterministically: guards re-verify and
    # the recomputed manifest must hash-match the frozen one (R1.6) — a genuine
    # cross-process barrier between freeze and read.
    manifest, population, _analysis_nets, regimes_gen, full_arrs, disclosure = \
        run_h1(frozen_sel)
    verify_h1_artifacts(manifest)
    if phase == "h1":
        LOGGER.info("H1 complete: manifest frozen at %s. Inspect results/, then "
                    "run '--phase h2' to spend the shot (H2 runs regardless of "
                    "entry attributes; only machinery defects may halt).",
                    MANIFEST_PATH.name)
        return

    # ---- Phase H2 (one-shot; reads population/margin ONLY from the manifest) --
    row, _holdout_net = run_h2(population, regimes_gen, full_arrs, tail_hash,
                               disclosure)

    # ---- plots (3 / 3) — rendered from the PERSISTED artifacts only ------------
    # (predeclared: post-verdict rendering reads disk artifacts, not holdout rows;
    # this is not a second read).
    per_event = pl.read_csv(EVENTS_PATH)
    analysis_persisted = pl.read_csv(ANALYSIS_NETS_PATH)
    plot_binding_verdict(per_event, row, PLOTS_DIR / "holdout_verdict.png")
    plot_fh_vs_btc(row, PLOTS_DIR / "fh_vs_btc_exit.png")
    plot_analysis_vs_holdout(analysis_persisted, per_event,
                             PLOTS_DIR / "analysis_vs_holdout.png")

    # ---- console summary --------------------------------------------------------
    LOGGER.info("--- BINDING VERDICT: %s ---", row["binding_verdict"])
    LOGGER.info("EURUSD-4h holdout: n=%d net=%.2f bps CI=[%.2f, %.2f] 1s-low=%.2f "
                "(margin=%.2f) p=%.4f | gross=%.2f rt=%.2f fin=%.2f | "
                "btc companion=%s (n=%d) | truncated share=%.3f",
                row["n_events"], row["net_bps"], row["ci_low"], row["ci_high"],
                row["ci_low_1s"], row["margin_bps"], row["boot_p"],
                row["gross_fh_bps"], row["rt_cost_bps"], row["financing_bps_mean"],
                f"{row['btc_net_bps']:.2f}" if row["btc_net_bps"] is not None
                else "n/a", row["n_btc_completed"], row["truncated_share"])
    LOGGER.info("The holdout shot is SPENT. Results in %s, plots in %s",
                RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
