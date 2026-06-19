"""EXP-071 — One-Shot TEST Confirmation of the Full G-015 Passing Cell Set.

``CF-HA-HARAMI-001`` / HYP-024 — Phase 016 **first counted TEST contact** in the harami
family's history (mirrors EXP-037/038 in the AVWAP pipeline). Governing checkpoint:
``docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/`` —
``design.md`` §5/§7/§8; ``D0-predeclarations.md`` P1-P15; ``D0-amendment-003`` (binding
full-conjunction FPR object); ``D0-amendment-004`` (**Null-A is the sole binding FPR null;
Null-B demoted to advisory**). EXP-070 returned ``CALIBRATION_DELIVERED`` (all 6 P5 cells
PASS under the amended Null-A-only rule).

The EXP-068 ``N-PARTIAL-V2A`` / ``N-V2A×ADV-NONE`` / ``N-BENCH`` / ``RM-native`` inference
machinery is **reused unchanged in semantics** (imported from EXP-068's ``run_experiment``
module — that module has no import-time side effects). This experiment applies it to the
**TEST stratum** (next 21% of each instrument's chronologically ordered 1-minute file, after
the first-49% TRAIN slice) of the predeclared 6-cell binding family:

    GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h   (ex-EURUSD)

Only five new pieces are local to this experiment (scope §Complexity Budget; analysis-plan
§Reused-vs-New):

  (a) TEST-slice loader with TRAIN state carry-in (:func:`load_test_1m`,
      :func:`resolve_test_cell`) — TRAIN bars warm MA / ``/STRONG-STAT`` / ATR / segment
      state; only TEST-window haramis enter the binding inference.
  (b) Freeze-file writer (:func:`ensure_freeze_file` / :func:`_write_freeze_file`) — atomic
      (``.tmp`` + ``os.replace``) and SHA-256-pinned; written **before any TEST row is
      loaded** (D0 P8); reused unchanged on a re-run so the commitment is preserved.
  (c) Holm-adjusted composition classifier (:func:`holm_reject`,
      :func:`classify_cells`) — per-cell conjunction -> experiment verdict (D0 P9).
  (d) Equal-weight portfolio aggregator (:func:`portfolio_composite`) — pooled per-event
      ``N-PARTIAL-V2A`` composite CI (D0 P10 disclosure; non-binding).
  (e) TEST-read manifest emitter (:func:`build_test_read_manifest`) — input for the
      same-commit ``test-read-ledger.md`` update (D0 P6).

Binding gate (D0 P9): a cell **clears** iff median CI_low > 0 (Holm-adjusted across the
powered binding family at α = 0.05) ∧ raw-mean CI_low > 0 (unadjusted) ∧ ``beats-RM``
contrast CI_low > 0 (Holm-adjusted) ∧ ``N-PARTIAL-V2A`` median point estimate > the
per-cell EXP-070 calibrated margin. ``TEST_CONFIRMED`` iff ≥ 3 cells clear, over ≥ 2
instruments, of which ≥ 2 clearing cells are non-4h.

Discipline (binding, carried): detection on HA candles; **every outcome metric on real
prices** (``RealOpen/High/Low/Close``); HA prices never enter any metric; the global
final-30% holdout is **never loaded**; gross only (no costs — EXP-072 scope). The binding
FPR null is **Null-A only** (D0-amendment-004); the stale ``verdict`` column of EXP-070's
``calibration_map.csv`` (written under the superseded both-nulls rule, not regenerated) is
**not** used to gate — the gate keys on ``fpr_conj_nullA ≤ 0.05``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pin per-process native thread pools to 1 BEFORE importing polars/numpy (mirrors EXP-068).
for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
EXPERIMENTS_ROOT = EXPERIMENT_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
FREEZE_FILE = EXPERIMENT_DIR / "frozen_selection.json"

EXP068_CODE = EXPERIMENTS_ROOT / "EXP-068" / "code"
EXP068_RESULTS = EXPERIMENTS_ROOT / "EXP-068" / "results"
EXP070_RESULTS = EXPERIMENTS_ROOT / "EXP-070" / "results"

# Import the frozen EXP-068 inference machinery by module (no import-time side effects:
# its orchestration is guarded by ``if __name__ == "__main__"``). Reused unchanged in
# semantics per analysis-plan §Reused-vs-New.
if str(EXP068_CODE) not in sys.path:
    sys.path.insert(0, str(EXP068_CODE))
import run_experiment as exp068  # noqa: E402

from xen.expectancy import (  # noqa: E402
    bootstrap_median_distribution,
    median_ci,
)

# --------------------------------------------------------------------------- #
# Constants (D0-frozen; none tuned)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-071"
BASE_SEED = exp068.BASE_SEED            # 20260616 — frozen master seed (EXP-068 convention)
N_BOOT = exp068.N_BOOT                  # 10_000
BOOT_BATCH = exp068.BOOT_BATCH
POWER_FLOOR = exp068.POWER_FLOOR        # 30 qualifying TEST events per cell
TRIM_FRAC = exp068.TRIM_FRAC            # 0.10 — winsorized-mean trim
RECON_TOL = exp068.RECON_TOL           # 1e-9 — P12 reproduction tolerance
ALPHA = 0.05                            # D0 P9 family-wise level (Holm)
ANALYSIS_FRACTION = exp068.ANALYSIS_FRACTION  # 0.7
TRAIN_FRACTION = exp068.TRAIN_FRACTION        # 0.7 (of the analysis set)
BINDING_OBJECT = "nat"                  # native conditioning object (D0 P1)
BINDING_ARM = "PARTIAL-V2A"             # N-PARTIAL-V2A (D0 P2 lead arm)
DISCLOSED_ARM = "V2A-ADVNONE"           # N-V2A×ADV-NONE (D0 P2 disclosed-secondary)
BENCH_ARM = "BENCH"                     # N-BENCH (signal-check anchor)
TEST_ARMS: tuple[str, ...] = (BINDING_ARM, DISCLOSED_ARM, BENCH_ARM)
COMPOSITE_SEED = [BASE_SEED, 999, "composite"]  # D0 P10 portfolio seed (predeclared label)
# Integer RNG seeds under the predeclared [BASE_SEED, 999, "composite"] block (numpy
# SeedSequence requires int-only entries): purpose 0 = composite median, 1 = composite mean.
COMPOSITE_RNG_MEDIAN = [BASE_SEED, 999, 0]
COMPOSITE_RNG_MEAN = [BASE_SEED, 999, 1]

# Predeclared TEST family (D0 P5; ex-EURUSD; frozen at G0; all PASS under D0-amendment-004).
# (instrument, domain, is_4h)
BINDING_CELLS: tuple[tuple[str, str, bool], ...] = (
    ("GBPUSD", "5m", False),
    ("GBPUSD", "1h", False),
    ("NZDUSD", "1h", False),
    ("NZDUSD", "2h", False),
    ("GBPJPY", "30m", False),
    ("US2000", "4h", True),
)
EXPECTED_FAMILY: set[str] = {f"{i}-{d}" for i, d, _ in BINDING_CELLS}
# Composition threshold (D0 P9), recorded verbatim into the freeze file.
COMPOSITION_THRESHOLD = ("≥ 3 cells clear the full conjunction (median CI_low>0 Holm-adj ∧ "
                         "raw-mean CI_low>0 ∧ beats-RM CI_low>0 Holm-adj ∧ median > "
                         "calibrated margin), spanning ≥ 2 instruments, of which ≥ 2 "
                         "clearing cells are non-4h.")
MARGIN_VERDICT_NOTE = ("EXP-070 calibration_map.csv 'verdict' column reflects the superseded "
                       "both-nulls rule (D0-amendment-003) and was NOT regenerated; the "
                       "binding FPR gate keys on fpr_conj_nullA ≤ 0.05 per D0-amendment-004.")

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellInference:
    """Per-cell TEST inference outputs for the three exit arms + RM-native null."""

    instrument: str
    domain: str
    is_4h: bool
    m: int                              # qualifying N-PARTIAL-V2A TEST events
    below_floor: bool
    # binding arm (N-PARTIAL-V2A)
    pv_median: float | None
    pv_ci_low_1s: float | None
    pv_ci_lo_2s: float | None
    pv_ci_hi_2s: float | None
    pv_mean: float | None
    pv_mean_ci_low_1s: float | None
    pv_winsorm: float | None
    p_median: float | None              # one-sided bootstrap p-value P(median* ≤ 0)
    p_beats_rm: float | None            # one-sided bootstrap p-value P(contrast* ≤ 0)
    beats_rm_low_1s: float | None
    beats_rm_lo_2s: float | None
    beats_rm_hi_2s: float | None
    rm_m: int
    rm_median: float | None
    # disclosed arms
    advnone_m: int
    advnone_median: float | None
    advnone_mean: float | None
    advnone_winsorm: float | None
    bench_m: int
    bench_median: float | None
    bench_mean: float | None
    # carried EXP-070 context (disclosed)
    calibrated_margin: float
    temporal_flag: str
    nullA_fpr: float
    nullB_fpr_advisory: float
    # per-event returns retained for the portfolio composite (binding arm only)
    pv_returns: np.ndarray


# --------------------------------------------------------------------------- #
# I/O helpers — EXP-070 / EXP-068 dependency loading (no TEST rows here)
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    """SHA-256 of a file's bytes (provenance pin)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_calibration_map() -> dict[str, dict[str, Any]]:
    """Load EXP-070 per-cell calibrated margins, Null-A/Null-B FPR, temporal flags.

    The binding FPR gate keys on ``fpr_conj_nullA`` (D0-amendment-004); the stale
    ``verdict`` column is read for provenance only.
    """
    path = EXP070_RESULTS / "calibration_map.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing EXP-070 calibration map: {path}")
    df = pl.read_parquet(path) if path.suffix == ".parquet" else pl.read_csv(path)
    out: dict[str, dict[str, Any]] = {}
    for row in df.iter_rows(named=True):
        out[str(row["cell"])] = {
            "verdict_stale": row.get("verdict"),
            "fpr_conj_nullA": float(row["fpr_conj_nullA"]),
            "fpr_conj_nullB": float(row["fpr_conj_nullB"]),
            "calibrated_margin_atr": float(row["calibrated_margin_atr"]),
            "temporal_flag": str(row.get("temporal_flag")),
            "degenerate_ci": bool(row.get("degenerate_ci")),
            "mde_atr": row.get("mde_atr"),
        }
    return out


def assert_dependency_gates(calib: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Hard-fail dependency gates (D0 P5/P7; analysis-plan Step 1). No TEST rows loaded.

    Verifies: (1) the EXP-068 g015 PARTIAL-V2A passing set ex-EURUSD equals the 6 P5 cells;
    (2) every P5 cell PASSes the amended Null-A binding gate (``fpr_conj_nullA ≤ 0.05``)
    with a non-degenerate CI. Returns provenance for the freeze file.
    """
    g015_path = EXP068_RESULTS / "g015_verdict.json"
    if not g015_path.exists():
        raise FileNotFoundError(f"missing EXP-068 g015 verdict: {g015_path}")
    g015 = json.loads(g015_path.read_text())
    g015_cells = g015["native_per_arm"]["PARTIAL-V2A"]["g015_passes"]["cells"]
    ex_eurusd = {c for c in g015_cells if not c.startswith("EURUSD-")}
    if ex_eurusd != EXPECTED_FAMILY:
        raise RuntimeError(
            f"EXP-068 g015 PARTIAL-V2A set ex-EURUSD {sorted(ex_eurusd)} != declared P5 "
            f"family {sorted(EXPECTED_FAMILY)} (D0 P5 freeze violated)")
    for cell in EXPECTED_FAMILY:
        if cell not in calib:
            raise RuntimeError(f"{cell}: absent from EXP-070 calibration_map.csv")
        c = calib[cell]
        if c["fpr_conj_nullA"] > 0.05:
            raise RuntimeError(
                f"{cell}: Null-A conjunction FPR {c['fpr_conj_nullA']:.3f} > 0.05 — not PASS "
                "under D0-amendment-004; cell would be FPR-excluded (freeze must record)")
        if c["degenerate_ci"]:
            raise RuntimeError(f"{cell}: degenerate CI in EXP-070 calibration (METHOD_DEFECT)")
    return {
        "g015_source": str(g015_path),
        "g015_partial_v2a_cells": g015_cells,
        "calibration_map_sha256": _sha256_file(EXP070_RESULTS / "calibration_map.csv"),
        "temporal_stability_sha256": _sha256_file(EXP070_RESULTS / "temporal_stability.csv"),
        "binding_fpr_null": "Null-A only (D0-amendment-004)",
    }


# --------------------------------------------------------------------------- #
# Pure computation — P12 reconciliation (TRAIN-only; before the freeze file)
# --------------------------------------------------------------------------- #
def _ref_cell(parquet: pl.DataFrame, instrument: str, domain: str,
              arm: str) -> dict[str, Any]:
    """Pull the EXP-068 native per-cell anchor row for one (instrument, domain, arm)."""
    sub = parquet.filter(
        (pl.col("instrument") == instrument) & (pl.col("domain") == domain)
        & (pl.col("object") == "nat") & (pl.col("arm") == arm)
        & (pl.col("member") == True))  # noqa: E712
    if sub.height != 1:
        raise RuntimeError(f"EXP-068 anchor for nat {arm} {instrument}-{domain}: "
                           f"expected 1 row, found {sub.height}")
    return sub.to_dicts()[0]


def p12_reconcile(
    cell_index: dict[tuple[str, str], int],
    anchor061: dict[tuple[str, str], dict[str, Any]],
    anchor066: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reproduce EXP-068 BENCH+PARTIAL-V2A / EXP-061 M0 / EXP-066 PARTIAL-V2A on TRAIN at 1e-9.

    Re-runs the frozen EXP-068 ``compute_cell`` (TRAIN slice, identical cell_index + seeds)
    for each binding cell and asserts byte-faithful reproduction of EXP-068's stored
    per-cell anchors (and the EXP-061/EXP-066 anchors EXP-068 itself reconciled). Hard-fail
    on any mismatch — the freeze-faithfulness proof required before any TEST contact (D0 P1).
    """
    parquet = pl.read_parquet(EXP068_RESULTS / "per_cell_expectancy.parquet")
    rows: list[dict[str, Any]] = []
    for instrument, domain, _ in tqdm(BINDING_CELLS, desc="P12 reconcile (TRAIN)"):
        train_1m, meta = exp068.load_train_1m(instrument)
        ci = cell_index[(instrument, domain)]
        cell = exp068.compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        if cell.get("empty"):
            raise RuntimeError(f"{instrument}-{domain}: empty TRAIN cell — cannot reconcile")
        sig = cell["arms"]["nat"]["signals"]
        max_diff = 0.0
        for arm in (BENCH_ARM, BINDING_ARM):
            ref = _ref_cell(parquet, instrument, domain, arm)
            got = sig[arm]
            if got.m != int(ref["m"]):
                raise RuntimeError(f"{instrument}-{domain} nat {arm}: m {got.m} != "
                                   f"EXP-068 {ref['m']} (P12 mismatch)")
            for field in ("median", "ci_low_1s", "mean", "mean_ci_low_1s"):
                d = abs(float(getattr(got, field)) - float(ref[field]))
                max_diff = max(max_diff, d)
                if d > RECON_TOL:
                    raise RuntimeError(f"{instrument}-{domain} nat {arm}.{field}: |Δ|={d:.2e} "
                                       f"> {RECON_TOL:.0e} (P12 mismatch)")
        # EXP-061 M0 (native BENCH) + EXP-066 native PARTIAL-V2A anchors.
        a061 = anchor061.get((instrument, domain), {}).get("M0")
        a066 = anchor066.get((instrument, domain))
        if a061 is None or a066 is None:
            raise RuntimeError(f"{instrument}-{domain}: missing EXP-061/EXP-066 anchor")
        d061 = abs(float(sig[BENCH_ARM].median) - float(a061["median"]))
        d066 = abs(float(sig[BINDING_ARM].median) - float(a066["median"]))
        if d061 > RECON_TOL or d066 > RECON_TOL:
            raise RuntimeError(f"{instrument}-{domain}: EXP-061/066 anchor mismatch "
                               f"(M0 |Δ|={d061:.2e}, PARTIAL |Δ|={d066:.2e})")
        max_diff = max(max_diff, d061, d066)
        rows.append({"cell": f"{instrument}-{domain}", "checked": True,
                     "max_abs_diff": max_diff,
                     "bench_m": sig[BENCH_ARM].m, "partial_m": sig[BINDING_ARM].m})
        del train_1m, cell
    return rows


# --------------------------------------------------------------------------- #
# I/O helpers — TEST-slice loader with TRAIN state carry-in (P8 gates this)
# --------------------------------------------------------------------------- #
def load_test_1m(instrument: str) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Return (train_1m, test_1m) slices for one instrument; the holdout is never loaded.

    TRAIN = first 49% (state carry-in only); TEST = next 21% (the binding stratum); the
    final 30% global holdout (``[analysis_cutoff, total)``) is excluded at the lazy-scan
    slice and never materialized.

    Enforces the D0 P8 contract: refuses to load any TEST row unless the hash-pinned
    freeze file already exists on disk.
    """
    if not FREEZE_FILE.exists():
        raise RuntimeError("D0 P8 violation: freeze file absent — no TEST row may be loaded")
    path = exp068.find_source_file(instrument)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    scan = pl.scan_parquet(path).select(cols).sort("CloseTime")
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_cutoff = int(total * ANALYSIS_FRACTION)
    train_cutoff = int(analysis_cutoff * TRAIN_FRACTION)
    # holdout = [analysis_cutoff, total) — NEVER LOADED.
    train_1m = scan.slice(0, train_cutoff).collect()
    test_1m = scan.slice(train_cutoff, analysis_cutoff - train_cutoff).collect()
    if not train_1m.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    if not test_1m.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TEST slice not chronological by CloseTime")
    if test_1m.is_empty():
        raise RuntimeError(f"{instrument}: empty TEST 1-minute slice")
    meta = {
        "source_file": path.name, "total_rows_1m": total,
        "analysis_cutoff_1m": analysis_cutoff, "train_cutoff_1m": train_cutoff,
        "test_rows_1m": int(test_1m.height),
        "train_end_epoch_s": int(train_1m.get_column("CloseTime").dt.epoch("s")[-1]),
        "analysis_end_epoch_s": int(test_1m.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train_1m, test_1m, meta


def build_test_domain(
    test_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, analysis_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate TEST 1-minute rows to domain bars, fenced strictly to the TEST window.

    Clock-aligned aggregation (``xen.bar_aggregator``); any window straddling the
    TRAIN/TEST 1-minute boundary is naturally dropped by the coverage rule on each side.
    """
    bars = exp068.aggregate_ohlc(test_1m, period_minutes=period_minutes,
                                 min_coverage=min_coverage)
    return bars.filter((pl.col("CloseTime").dt.epoch("s") > train_end_epoch)
                       & (pl.col("CloseTime").dt.epoch("s") <= analysis_end_epoch))


# --------------------------------------------------------------------------- #
# Pure computation — per-cell TEST inference (TRAIN state carry-in)
# --------------------------------------------------------------------------- #
def _pvalue_le_zero(dist: np.ndarray) -> float | None:
    """One-sided bootstrap p-value P(stat* ≤ 0); None on an empty distribution."""
    if dist.shape[0] == 0:
        return None
    return float(np.mean(dist <= 0.0))


def resolve_test_cell(
    instrument: str, domain: str, is_4h: bool, calib_cell: dict[str, Any],
    cell_index: int,
) -> CellInference:
    """Resolve all three arms + RM-native null on the TEST stratum of one cell.

    Domain bars are built over the analysis set as TRAIN bars (frozen ``build_domain``)
    concatenated with TEST bars (``build_test_domain``) so MA(20,50) / ``/STRONG-STAT`` /
    ATR / segment state is warmed by TRAIN; only haramis whose entry domain-bar closes in
    the TEST window (``epoch > train_end_epoch``) enter the binding population. The
    matched-random pool is restricted to TEST-window bars by marking TRAIN bars ineligible
    in the ``warmup`` mask passed to the frozen :func:`matched_random_arm` (no modification
    to certified code). Forward scans clip at the analysis-set edge -> ``DATA_CENSORED``;
    no holdout row is ever reachable.
    """
    train_1m, test_1m, meta = load_test_1m(instrument)
    train_end = meta["train_end_epoch_s"]
    analysis_end = meta["analysis_end_epoch_s"]
    period, coverage = exp068.DOMAINS[domain]
    train_bars = exp068.build_domain(train_1m, period, coverage, train_end)
    test_bars = build_test_domain(test_1m, period, coverage, train_end, analysis_end)
    combined = pl.concat([train_bars, test_bars]).sort("CloseTime")

    ohlc = exp068.real_ohlc(combined)
    if not bool(np.all(np.diff(ohlc["epoch"]) > 0)):
        raise RuntimeError(f"{instrument}-{domain}: combined domain bars not strictly "
                           "increasing in CloseTime (TRAIN/TEST seam violation)")
    atr = exp068.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], exp068.ATR_PERIOD)
    entry_idx = exp068.harami_entry_indices(combined, ohlc["epoch"])
    margin = calib_cell["calibrated_margin_atr"]
    flag = calib_cell["temporal_flag"]
    fpr_a, fpr_b = calib_cell["fpr_conj_nullA"], calib_cell["fpr_conj_nullB"]
    if entry_idx.shape[0] == 0:
        return _below_floor_cell(instrument, domain, is_4h, margin, flag, fpr_a, fpr_b)

    entry_epoch = ohlc["epoch"][entry_idx]
    ma = exp068._ma_context(ohlc, atr, entry_idx, entry_epoch)
    if ma.get("empty"):
        return _below_floor_cell(instrument, domain, is_4h, margin, flag, fpr_a, fpr_b)

    # TEST-window restriction: events whose entry domain-bar closes after the TRAIN edge.
    test_entry = entry_epoch > train_end
    cond = ma["stat"]["retained_p75"] & test_entry
    last_idx = int(ohlc["close"].shape[0]) - 1
    seg = ma["seg"]
    state_all = exp068.live_in_progress_state(
        ohlc["epoch"], ohlc["close"], seg["confirm_epoch"], seg["end_price"],
        seg["end_epoch"], seg["direction"])
    _, warmup_all = exp068.adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    # Restrict the matched-random pool to TEST-window bars (TRAIN bars marked ineligible).
    warmup_test = warmup_all | (ohlc["epoch"] <= train_end)
    signal_idx = entry_idx[cond]

    sig: dict[str, Any] = {}
    null: dict[str, Any] = {}
    for aid in TEST_ARMS:
        arm = exp068.ARM_BY_ID[aid]
        sig[aid] = exp068.signal_arm(BINDING_OBJECT, arm, ohlc, ma, cond, entry_idx,
                                     last_idx, cell_index)
        null[aid] = exp068.matched_random_arm(
            BINDING_OBJECT, arm, ohlc, state_all, seg, warmup_test, ma["atr"],
            signal_idx, sig[aid].m, cell_index, last_idx)
    pv, adv, bench = sig[BINDING_ARM], sig[DISCLOSED_ARM], sig[BENCH_ARM]
    pv_null = null[BINDING_ARM]
    below = pv.m < POWER_FLOOR

    contrast_dist = (pv.dist - pv_null.dist) if (pv.dist.shape[0] and pv_null.dist.shape[0]
                                                 ) else np.empty(0, dtype=np.float64)
    beats_low, beats_lo, beats_hi = (median_ci(contrast_dist) if contrast_dist.shape[0]
                                     else (None, None, None))
    return CellInference(
        instrument=instrument, domain=domain, is_4h=is_4h, m=pv.m, below_floor=below,
        pv_median=pv.median, pv_ci_low_1s=pv.ci_low_1s, pv_ci_lo_2s=pv.ci_lo_2s,
        pv_ci_hi_2s=pv.ci_hi_2s, pv_mean=pv.mean, pv_mean_ci_low_1s=pv.mean_ci_low_1s,
        pv_winsorm=(exp068._winsorized_mean(pv.r_e) if pv.m > 0 else None),
        p_median=_pvalue_le_zero(pv.dist), p_beats_rm=_pvalue_le_zero(contrast_dist),
        beats_rm_low_1s=beats_low, beats_rm_lo_2s=beats_lo, beats_rm_hi_2s=beats_hi,
        rm_m=pv_null.m, rm_median=pv_null.median,
        advnone_m=adv.m, advnone_median=adv.median, advnone_mean=adv.mean,
        advnone_winsorm=(exp068._winsorized_mean(adv.r_e) if adv.m > 0 else None),
        bench_m=bench.m, bench_median=bench.median, bench_mean=bench.mean,
        calibrated_margin=margin, temporal_flag=flag, nullA_fpr=fpr_a,
        nullB_fpr_advisory=fpr_b,
        pv_returns=(pv.r_e.copy() if not below else np.empty(0, dtype=np.float64)))


def _below_floor_cell(instrument: str, domain: str, is_4h: bool, margin: float, flag: str,
                      fpr_a: float, fpr_b: float) -> CellInference:
    """Construct a below-floor / no-event placeholder cell (excluded from composition)."""
    return CellInference(
        instrument=instrument, domain=domain, is_4h=is_4h, m=0, below_floor=True,
        pv_median=None, pv_ci_low_1s=None, pv_ci_lo_2s=None, pv_ci_hi_2s=None,
        pv_mean=None, pv_mean_ci_low_1s=None, pv_winsorm=None, p_median=None,
        p_beats_rm=None, beats_rm_low_1s=None, beats_rm_lo_2s=None, beats_rm_hi_2s=None,
        rm_m=0, rm_median=None, advnone_m=0, advnone_median=None, advnone_mean=None,
        advnone_winsorm=None, bench_m=0, bench_median=None, bench_mean=None,
        calibrated_margin=margin, temporal_flag=flag, nullA_fpr=fpr_a,
        nullB_fpr_advisory=fpr_b, pv_returns=np.empty(0, dtype=np.float64))


# --------------------------------------------------------------------------- #
# Pure computation — Holm adjustment + composition classification (D0 P9)
# --------------------------------------------------------------------------- #
def holm_reject(pvalues: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm-Bonferroni step-down rejections of one-sided H0 (stat ≤ 0) over a family.

    Family = the cells with a defined p-value (powered cells). A cell is rejected
    (i.e. clears the leg, CI_low > 0 after adjustment) iff its sorted p-value and all
    preceding ones are ≤ ``alpha / (k - rank + 1)``. Returns one bool per input cell.
    """
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    k = len(items)
    out: dict[str, bool] = {}
    failed = False
    for i, (cell, p) in enumerate(items):
        thr = alpha / (k - i)            # k - (i+1) + 1
        if failed or p > thr:
            out[cell] = False
            failed = True
        else:
            out[cell] = True
    return out


def classify_cells(cells: list[CellInference]) -> dict[str, Any]:
    """Per-cell conjunction flags + experiment-level verdict (D0 P9).

    Holm adjustment (median + beats-RM legs) is applied across the powered binding cells.
    Raw-mean leg is unadjusted (per-cell co-primary, D0 P4). Below-floor cells are excluded
    with explicit disposition.
    """
    powered = [c for c in cells if not c.below_floor and c.p_median is not None]
    p_med = {c.instrument + "-" + c.domain: c.p_median for c in powered}
    p_rm = {c.instrument + "-" + c.domain: (c.p_beats_rm if c.p_beats_rm is not None else 1.0)
            for c in powered}
    holm_med = holm_reject(p_med)
    holm_rm = holm_reject(p_rm)

    records: list[dict[str, Any]] = []
    clearing: list[CellInference] = []
    n_median_neg = 0
    for c in cells:
        key = f"{c.instrument}-{c.domain}"
        if c.below_floor:
            records.append({**_cell_record(c), "disposition": "below_floor",
                            "median_holm_clear": False, "beats_rm_holm_clear": False,
                            "raw_mean_clear": False, "margin_clear": False,
                            "clears_composition": False, "yellow_flag": False,
                            "mean_recoverable": _mean_recoverable(c)})
            continue
        med_clear = bool(holm_med.get(key, False))
        rm_clear = bool(holm_rm.get(key, False))
        raw_clear = bool(c.pv_mean_ci_low_1s is not None and c.pv_mean_ci_low_1s > 0.0)
        margin_clear = bool(c.pv_median is not None and c.pv_median > c.calibrated_margin)
        clears = med_clear and rm_clear and raw_clear and margin_clear
        winsorm_pos = bool(c.pv_winsorm is not None and c.pv_winsorm > 0.0)
        yellow = bool(med_clear and rm_clear and winsorm_pos and not raw_clear)
        if c.pv_ci_low_1s is not None and c.pv_ci_low_1s <= 0.0:
            n_median_neg += 1
        if clears:
            clearing.append(c)
        records.append({**_cell_record(c), "disposition": "powered",
                        "median_holm_clear": med_clear, "beats_rm_holm_clear": rm_clear,
                        "raw_mean_clear": raw_clear, "margin_clear": margin_clear,
                        "clears_composition": clears, "yellow_flag": yellow,
                        "mean_recoverable": _mean_recoverable(c)})

    n_clear = len(clearing)
    instruments = sorted({c.instrument for c in clearing})
    non_4h_clear = [c for c in clearing if not c.is_4h]
    confirmed = (n_clear >= 3 and len(instruments) >= 2 and len(non_4h_clear) >= 2)
    n_powered = len(powered)
    if confirmed:
        verdict = "TEST_CONFIRMED"
    elif n_powered > 0 and n_median_neg > n_powered / 2.0:
        verdict = "TEST_NOT_CONFIRMED"
    else:
        verdict = "TEST_INCONCLUSIVE"
    return {
        "verdict": verdict,
        "n_clearing": n_clear, "n_instruments": len(instruments),
        "n_non_4h_clearing": len(non_4h_clear), "n_powered": n_powered,
        "n_below_floor": sum(1 for c in cells if c.below_floor),
        "n_median_ci_low_neg": n_median_neg,
        "clearing_cells": [f"{c.instrument}-{c.domain}" for c in clearing],
        "clearing_instruments": instruments,
        "holm_family_size": n_powered,
        "per_cell": records,
    }


def _mean_recoverable(c: CellInference) -> bool:
    """N-V2A×ADV-NONE MEAN_RECOVERABLE flag: winsorm > 0 ∧ raw mean point < 0 (D0 P11)."""
    return bool(c.advnone_m >= POWER_FLOOR and c.advnone_winsorm is not None
                and c.advnone_winsorm > 0.0 and c.advnone_mean is not None
                and c.advnone_mean < 0.0)


def _cell_record(c: CellInference) -> dict[str, Any]:
    """Flatten a CellInference to a CSV-ready dict (no per-event arrays)."""
    return {
        "cell": f"{c.instrument}-{c.domain}", "instrument": c.instrument, "domain": c.domain,
        "is_4h": c.is_4h, "m_test_events": c.m, "below_floor": c.below_floor,
        "pv_median": c.pv_median, "pv_ci_low_1s": c.pv_ci_low_1s,
        "pv_ci_lo_2s": c.pv_ci_lo_2s, "pv_ci_hi_2s": c.pv_ci_hi_2s,
        "pv_mean": c.pv_mean, "pv_mean_ci_low_1s": c.pv_mean_ci_low_1s,
        "pv_winsorm": c.pv_winsorm, "p_median": c.p_median, "p_beats_rm": c.p_beats_rm,
        "beats_rm_low_1s": c.beats_rm_low_1s, "beats_rm_lo_2s": c.beats_rm_lo_2s,
        "beats_rm_hi_2s": c.beats_rm_hi_2s, "rm_m": c.rm_m, "rm_median": c.rm_median,
        "advnone_m": c.advnone_m, "advnone_median": c.advnone_median,
        "advnone_mean": c.advnone_mean, "advnone_winsorm": c.advnone_winsorm,
        "bench_m": c.bench_m, "bench_median": c.bench_median, "bench_mean": c.bench_mean,
        "calibrated_margin_atr": c.calibrated_margin, "temporal_flag": c.temporal_flag,
        "nullA_fpr": c.nullA_fpr, "nullB_fpr_advisory": c.nullB_fpr_advisory,
    }


# --------------------------------------------------------------------------- #
# Pure computation — equal-weight portfolio composite (D0 P10; non-binding)
# --------------------------------------------------------------------------- #
def portfolio_composite(cells: list[CellInference]) -> dict[str, Any]:
    """Pooled per-event N-PARTIAL-V2A composite CI across powered binding cells.

    Per-event returns from every powered binding cell are pooled (each event weight 1; no
    cell up/down-weighted by a portfolio weight — the equal-weight disclosure of D0 P10).
    Median + raw mean get a moving-block bootstrap CI (block ``b = round(m_total^(1/3))``,
    ``N_BOOT`` resamples, the predeclared composite seed); winsorized mean is a point
    estimate. Returns the composite stats and the retained median bootstrap distribution
    for plotting. This is a disclosure, not a gate.
    """
    contributing = [c for c in cells if not c.below_floor and c.pv_returns.shape[0] > 0]
    if not contributing:
        return {"contributing_cells": [], "m_total": 0, "composite_median": None,
                "median_dist": np.empty(0, dtype=np.float64)}
    pooled = np.concatenate([c.pv_returns for c in contributing])
    rng_med = np.random.default_rng(COMPOSITE_RNG_MEDIAN)
    rng_mean = np.random.default_rng(COMPOSITE_RNG_MEAN)
    med_dist, block_len = bootstrap_median_distribution(pooled, rng_med, n_boot=N_BOOT,
                                                         batch=BOOT_BATCH)
    mean_dist, _ = exp068.bootstrap_stat_distribution(pooled, rng_mean, "mean",
                                                      n_boot=N_BOOT, batch=BOOT_BATCH)
    med_low, med_lo, med_hi = median_ci(med_dist)
    mean_low, mean_lo, mean_hi = median_ci(mean_dist)
    return {
        "contributing_cells": [f"{c.instrument}-{c.domain}" for c in contributing],
        "m_total": int(pooled.shape[0]), "block_len": int(block_len),
        "composite_median": float(np.median(pooled)),
        "composite_median_ci_low_1s": med_low, "composite_median_ci_lo_2s": med_lo,
        "composite_median_ci_hi_2s": med_hi,
        "composite_mean": float(np.mean(pooled)),
        "composite_mean_ci_low_1s": mean_low, "composite_mean_ci_lo_2s": mean_lo,
        "composite_mean_ci_hi_2s": mean_hi,
        "composite_winsorm": exp068._winsorized_mean(pooled),
        "composite_seed": str(COMPOSITE_SEED),
        "median_dist": med_dist,
    }


# --------------------------------------------------------------------------- #
# Pure computation — TEST-read manifest (D0 P6 ledger input)
# --------------------------------------------------------------------------- #
def build_test_read_manifest(cells: list[CellInference]) -> list[dict[str, Any]]:
    """One row per binding stratum: counted_reads_consumed = 1 (powered) / 0 (below-floor)."""
    return [{"instrument": c.instrument, "domain": c.domain,
             "stratum": f"{c.instrument}-{c.domain}",
             "counted_reads_consumed": (0 if c.below_floor else 1),
             "disposition": ("below_floor (excluded from composition)" if c.below_floor
                             else "binding stratum-specific inference")}
            for c in cells]


# --------------------------------------------------------------------------- #
# Freeze-file writer (D0 P8 — atomic + SHA-256, BEFORE any TEST row is loaded)
# --------------------------------------------------------------------------- #
def ensure_freeze_file(calib: dict[str, dict[str, Any]],
                       provenance: dict[str, Any]) -> tuple[str, bool]:
    """Reuse the existing pre-TEST freeze commitment, or write it (D0 P8).

    The freeze file is the irrevocable pre-TEST commitment: it must be written **once,
    before any TEST row is loaded**. If a hash-pinned freeze file already exists (e.g. a
    bug-fix re-run after the original pre-TEST freeze), it is **reused unchanged** — the
    original commitment is preserved, not rewritten — after verifying its declared family
    still matches the code's declared family. Returns ``(sha256, reused)``.
    """
    if FREEZE_FILE.exists():
        existing = json.loads(FREEZE_FILE.read_text())
        cells = {c["cell"] for c in existing.get("test_family", [])}
        if cells != EXPECTED_FAMILY:
            raise RuntimeError(
                f"existing freeze file family {sorted(cells)} != declared family "
                f"{sorted(EXPECTED_FAMILY)} — remove the file to re-freeze (D0 P8/P15)")
        if "frozen_selection_sha256" not in existing:
            raise RuntimeError("existing freeze file is not hash-pinned — remove to re-freeze")
        return str(existing["frozen_selection_sha256"]), True
    return _write_freeze_file(calib, provenance), False


def _write_freeze_file(calib: dict[str, dict[str, Any]], provenance: dict[str, Any]) -> str:
    """Write ``frozen_selection.json`` atomically and append its SHA-256 (D0 P8).

    Records the predeclared TEST family, EXP-070 Null-A/Null-B FPR + calibrated margins +
    temporal flags per cell, the composition threshold verbatim, the inference-method
    parameters (seed / N_BOOT / block rule), and the composite seed. Written via a ``.tmp``
    sibling + ``os.replace`` to prevent partial-write corruption. Returns the content hash.
    """
    family = []
    for instrument, domain, is_4h in BINDING_CELLS:
        c = calib[f"{instrument}-{domain}"]
        family.append({
            "cell": f"{instrument}-{domain}", "instrument": instrument, "domain": domain,
            "is_4h": is_4h, "fpr_conj_nullA": c["fpr_conj_nullA"],
            "fpr_conj_nullB_advisory": c["fpr_conj_nullB"],
            "calibrated_margin_atr": c["calibrated_margin_atr"],
            "temporal_flag": c["temporal_flag"],
            "amended_verdict": "PASS (Null-A ≤ 0.05; D0-amendment-004)",
            "stale_both_nulls_verdict": c["verdict_stale"],
        })
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "D0 P8 freeze-before-TEST — written before any TEST row is loaded",
        "checkpoint": "2026-06-18-016-harami-candidate-screening",
        "binding_object": BINDING_OBJECT, "binding_arm": BINDING_ARM,
        "test_family": family,
        "fpr_exclusions": [],  # none — all 6 P5 cells PASS under D0-amendment-004
        "binding_fpr_null": "Null-A only (D0-amendment-004; Null-B advisory)",
        "verdict_column_note": MARGIN_VERDICT_NOTE,
        "composition_threshold": COMPOSITION_THRESHOLD,
        "inference_method": {
            "base_seed": BASE_SEED, "n_boot": N_BOOT,
            "block_length_rule": "b = round(m**(1/3))",
            "rng_convention": ("EXP-068 arm_pb purpose-block convention "
                               "(default_rng([BASE_SEED, cell_index, purpose])); reused "
                               "unchanged from the EXP-070-calibrated machinery"),
            "winsorize_trim_frac": TRIM_FRAC, "power_floor": POWER_FLOOR, "alpha": ALPHA,
        },
        "composite_seed": {"predeclared_label": str(COMPOSITE_SEED),
                           "median_rng_seed": COMPOSITE_RNG_MEDIAN,
                           "mean_rng_seed": COMPOSITE_RNG_MEAN},
        "provenance": provenance,
        "excluded_eurusd_cells": ["EURUSD-15m", "EURUSD-1h", "EURUSD-4h"],
    }
    body = json.dumps(payload, indent=2, sort_keys=True, default=str)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    final = {**payload, "frozen_selection_sha256": digest}
    tmp = FREEZE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(final, indent=2, default=str))
    os.replace(tmp, FREEZE_FILE)
    return digest


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries + the composite dist)
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def plot_median_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell N-PARTIAL-V2A median + CI vs calibrated margin (headline composition read)."""
    fig, ax = plt.subplots(figsize=(11, 6))
    cells = [r for r in records if r["pv_median"] is not None]
    if not cells:
        _placeholder(ax, "no powered cells")
    else:
        y = np.arange(len(cells))
        med = np.array([r["pv_median"] for r in cells], dtype=float)
        lo = np.array([r["pv_ci_lo_2s"] if r["pv_ci_lo_2s"] is not None else r["pv_median"]
                       for r in cells], dtype=float)
        hi = np.array([r["pv_ci_hi_2s"] if r["pv_ci_hi_2s"] is not None else r["pv_median"]
                       for r in cells], dtype=float)
        xerr = np.vstack([np.clip(med - lo, 0.0, None), np.clip(hi - med, 0.0, None)])
        colours = ["#1a9850" if r["clears_composition"] else "#d73027" for r in cells]
        ax.errorbar(med, y, xerr=xerr, fmt="none", ecolor="#888888", elinewidth=1.0,
                    capsize=2, zorder=1)
        ax.scatter(med, y, c=colours, s=55, zorder=3, label="N-PARTIAL-V2A median")
        adv = [r["advnone_median"] for r in cells]
        ax.scatter(adv, y, facecolors="none", edgecolors="#ff7f0e", s=45, zorder=2,
                   label="N-V2A×ADV-NONE median")
        for i, r in enumerate(cells):
            ax.plot([r["calibrated_margin_atr"]] * 2, [i - 0.35, i + 0.35], color="k",
                    lw=1.4, ls="--", zorder=4)
        ax.axvline(0.0, color="k", lw=0.8)
        ax.set_yticks(y, [f"{r['cell']} [{r['temporal_flag'][:4]}]" for r in cells],
                      fontsize=8)
        ax.set_xlabel("per-event median expectancy (ATR units)")
        ax.set_title(f"{EXPERIMENT_ID}: TEST median vs calibrated margin "
                     "(green=clears; dashed=margin)")
        ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_composition_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Cell × conjunction-leg pass/fail heatmap (green/red/grey + yellow-flag marker)."""
    legs = ["median_holm_clear", "raw_mean_clear", "beats_rm_holm_clear", "margin_clear"]
    leg_labels = ["median CI_low>0\n(Holm)", "raw-mean\nCI_low>0", "beats-RM CI_low>0\n(Holm)",
                  "median > margin"]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    if not records:
        _placeholder(ax, "no cells")
    else:
        matrix = np.zeros((len(records), len(legs)))
        for ri, r in enumerate(records):
            for ci, leg in enumerate(legs):
                matrix[ri, ci] = (np.nan if r["below_floor"] else (1.0 if r[leg] else 0.0))
        ax.imshow(matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")
        for ri, r in enumerate(records):
            if r["below_floor"]:
                ax.text(len(legs) / 2.0 - 0.5, ri, "below-floor", ha="center", va="center",
                        fontsize=8, color="k")
            if r.get("yellow_flag"):
                ax.text(0, ri, "▲", ha="center", va="center", fontsize=10, color="#b8860b")
        ax.set_xticks(range(len(legs)), leg_labels, fontsize=7)
        ax.set_yticks(range(len(records)), [r["cell"] for r in records], fontsize=8)
        ax.set_title(f"{EXPERIMENT_ID}: composition conjunction legs (▲ = yellow-flag)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_beats_rm(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell beats-RM-native contrast point estimate + CI with a zero reference."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    cells = [r for r in records if r["beats_rm_low_1s"] is not None]
    if not cells:
        _placeholder(ax, "no powered cells with a beats-RM contrast")
    else:
        y = np.arange(len(cells))
        point = np.array([0.5 * (r["beats_rm_lo_2s"] + r["beats_rm_hi_2s"]) for r in cells])
        lo = np.array([r["beats_rm_lo_2s"] for r in cells], dtype=float)
        hi = np.array([r["beats_rm_hi_2s"] for r in cells], dtype=float)
        xerr = np.vstack([np.clip(point - lo, 0.0, None), np.clip(hi - point, 0.0, None)])
        colours = ["#1a9850" if r["beats_rm_holm_clear"] else "#d73027" for r in cells]
        ax.errorbar(point, y, xerr=xerr, fmt="o", ecolor="#888888", elinewidth=1.0,
                    capsize=2, mfc="none", mec="none")
        ax.scatter(point, y, c=colours, s=55, zorder=3)
        ax.axvline(0.0, color="k", lw=0.9, ls="--")
        ax.set_yticks(y, [r["cell"] for r in cells], fontsize=8)
        ax.set_xlabel("N-PARTIAL-V2A − RM-native median contrast (ATR units)")
        ax.set_title(f"{EXPERIMENT_ID}: beats-RM-native contrast per cell "
                     "(green=Holm-clears)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_portfolio_composite(portfolio: dict[str, Any], save_path: Path) -> None:
    """Pooled composite N-PARTIAL-V2A bootstrap median distribution + 95% CI + zero line."""
    fig, ax = plt.subplots(figsize=(9, 5))
    dist = portfolio.get("median_dist", np.empty(0))
    if dist.shape[0] == 0:
        _placeholder(ax, "no contributing cells for the portfolio composite")
    else:
        ax.hist(dist, bins=60, color="#4575b4", alpha=0.8)
        for key, style, label in (("composite_median_ci_lo_2s", "--", "95% CI"),
                                   ("composite_median_ci_hi_2s", "--", None)):
            ax.axvline(portfolio[key], color="k", lw=1.0, ls=style, label=label)
        ax.axvline(portfolio["composite_median"], color="#d73027", lw=1.5,
                   label="point estimate")
        ax.axvline(0.0, color="k", lw=1.2)
        ax.set_xlabel("composite median expectancy (ATR units)")
        ax.set_ylabel("bootstrap resample count")
        ax.set_title(f"{EXPERIMENT_ID}: equal-weight portfolio composite "
                     f"(m={portfolio['m_total']}, {len(portfolio['contributing_cells'])} cells)")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_winsorm_diagnostic(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell winsorized vs raw mean for both arms (MEAN_RECOVERABLE / yellow-flag)."""
    fig, ax = plt.subplots(figsize=(11, 6))
    cells = [r for r in records if not r["below_floor"]]
    if not cells:
        _placeholder(ax, "no powered cells")
    else:
        y = np.arange(len(cells))
        ax.scatter([r["pv_winsorm"] for r in cells], y, c="#1f77b4", s=50,
                   label="N-PARTIAL-V2A winsorm")
        ax.scatter([r["pv_mean"] for r in cells], y, marker="x", c="#1f77b4", s=45,
                   label="N-PARTIAL-V2A raw mean")
        ax.scatter([r["advnone_winsorm"] for r in cells], y, facecolors="none",
                   edgecolors="#ff7f0e", s=55, label="N-V2A×ADV-NONE winsorm")
        ax.scatter([r["advnone_mean"] for r in cells], y, marker="+", c="#ff7f0e", s=55,
                   label="N-V2A×ADV-NONE raw mean")
        for i, r in enumerate(cells):
            tags = []
            if r.get("yellow_flag"):
                tags.append("YF")
            if r.get("mean_recoverable"):
                tags.append("MR")
            if tags:
                ax.text(0.02, i, " ".join(tags), transform=ax.get_yaxis_transform(),
                        fontsize=7, color="#b8860b", va="center")
        ax.axvline(0.0, color="k", lw=0.9, ls="--")
        ax.set_yticks(y, [r["cell"] for r in cells], fontsize=8)
        ax.set_xlabel("expectancy (ATR units)")
        ax.set_title(f"{EXPERIMENT_ID}: winsorized vs raw mean per arm "
                     "(YF=yellow-flag; MR=mean-recoverable)")
        ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(classification: dict[str, Any], portfolio: dict[str, Any]) -> None:
    """Render the five bounded plots from collected summaries (no data reloads)."""
    records = classification["per_cell"]
    plot_median_forest(records, PLOTS_DIR / "median_forest_vs_margin.png")
    plot_composition_heatmap(records, PLOTS_DIR / "composition_heatmap.png")
    plot_beats_rm(records, PLOTS_DIR / "beats_rm_contrast.png")
    plot_portfolio_composite(portfolio, PLOTS_DIR / "portfolio_composite.png")
    plot_winsorm_diagnostic(records, PLOTS_DIR / "winsorm_diagnostic.png")


# --------------------------------------------------------------------------- #
# Determinism replay (D0 P7 Leg 3)
# --------------------------------------------------------------------------- #
def _cell_fingerprint(c: CellInference) -> tuple[Any, ...]:
    """Order-stable fingerprint of a cell's binding statistics for byte comparison."""
    return (c.m, c.pv_median, c.pv_ci_low_1s, c.pv_mean, c.pv_mean_ci_low_1s,
            c.pv_winsorm, c.p_median, c.p_beats_rm, c.beats_rm_low_1s, c.rm_m,
            tuple(np.round(c.pv_returns, 12).tolist()))


def determinism_replay(cell_index: dict[tuple[str, str], int],
                       calib: dict[str, dict[str, Any]],
                       first_pass: list[CellInference]) -> dict[str, Any]:
    """Re-resolve all six cells and assert byte-identical binding statistics (P7 Leg 3)."""
    spot = {"US2000-4h", "GBPUSD-1h"}
    mismatches: list[str] = []
    for c in tqdm(first_pass, desc="determinism replay"):
        key = (c.instrument, c.domain)
        again = resolve_test_cell(c.instrument, c.domain, c.is_4h,
                                  calib[f"{c.instrument}-{c.domain}"], cell_index[key])
        if _cell_fingerprint(again) != _cell_fingerprint(c):
            mismatches.append(f"{c.instrument}-{c.domain}")
    spot_checked = sorted(spot & {f"{c.instrument}-{c.domain}" for c in first_pass})
    return {"determinism_pass": not mismatches, "mismatches": mismatches,
            "spot_check_cells": spot_checked, "n_cells_replayed": len(first_pass)}


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    frame = pl.DataFrame(records, strict=False) if records else pl.DataFrame({"empty": []})
    frame.write_csv(path)


def write_outputs(
    classification: dict[str, Any], portfolio: dict[str, Any],
    manifest: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    freeze_hash: str, provenance: dict[str, Any], determinism: dict[str, Any],
    instrument_meta: dict[str, Any],
) -> None:
    """Persist per-cell results, portfolio, verdict, manifest, and run metadata."""
    _write_csv(classification["per_cell"], RESULTS_DIR / "per_cell_results.csv")
    # contributing_cells is a list -> join to a scalar string (CSV has no nested columns).
    portfolio_row = {k: v for k, v in portfolio.items() if k != "median_dist"}
    portfolio_row["contributing_cells"] = "; ".join(portfolio_row.get("contributing_cells") or [])
    _write_csv([portfolio_row], RESULTS_DIR / "portfolio_results.csv")
    _write_csv(manifest, RESULTS_DIR / "test_read_manifest.csv")
    verdict_doc = {k: v for k, v in classification.items() if k != "per_cell"}
    verdict_doc["per_cell_flags"] = [
        {"cell": r["cell"], "disposition": r["disposition"],
         "median_holm_clear": r["median_holm_clear"], "raw_mean_clear": r["raw_mean_clear"],
         "beats_rm_holm_clear": r["beats_rm_holm_clear"], "margin_clear": r["margin_clear"],
         "clears_composition": r["clears_composition"], "yellow_flag": r["yellow_flag"],
         "mean_recoverable": r["mean_recoverable"]}
        for r in classification["per_cell"]]
    (RESULTS_DIR / "composition_verdict.json").write_text(
        json.dumps(verdict_doc, indent=2, default=str))

    per_cell_sha = _sha256_file(RESULTS_DIR / "per_cell_results.csv")
    portfolio_sha = _sha256_file(RESULTS_DIR / "portfolio_results.csv")
    meta = {
        "experiment_id": EXPERIMENT_ID, "hypothesis": "HYP-024",
        "family": "CF-HA-HARAMI-001", "candidate": "CAND-001",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": "2026-06-18-016-harami-candidate-screening",
        "stratum": "TEST (next 21% per file); TRAIN state carry-in; final-30% holdout sealed",
        "posture": "gross only (no costs — EXP-072 scope; D0 P12)",
        "verdict": classification["verdict"],
        "composition_threshold": COMPOSITION_THRESHOLD,
        "binding_fpr_null": "Null-A only (D0-amendment-004)",
        "verdict_column_note": MARGIN_VERDICT_NOTE,
        "freeze_file": str(FREEZE_FILE), "freeze_file_sha256": freeze_hash,
        "p12_reconciliation": recon_rows,
        "p12_max_abs_diff": (max((r["max_abs_diff"] for r in recon_rows), default=0.0)),
        "p12_tolerance": RECON_TOL,
        "dependency_provenance": provenance,
        "determinism": determinism,
        "per_cell_results_sha256": per_cell_sha, "portfolio_results_sha256": portfolio_sha,
        "inference_params": {"base_seed": BASE_SEED, "n_boot": N_BOOT,
                             "block_length_rule": "b = round(m**(1/3))",
                             "power_floor": POWER_FLOOR, "trim_frac": TRIM_FRAC,
                             "alpha": ALPHA, "composite_seed": str(COMPOSITE_SEED)},
        "reuse_note": ("signal_arm / matched_random_arm / contrast / _summarize_arm / "
                       "bootstrap_median_distribution / median_ci / _winsorized_mean reused "
                       "unchanged in semantics from EXP-068 (the EXP-070-calibrated "
                       "machinery); matched-random TEST pool restricted to the TEST window "
                       "via the warmup mask only."),
        "holdout_fence": ("load_test_1m slices [0, analysis_cutoff) only; the final-30% "
                          "holdout is never materialized; forward scans clip at the "
                          "analysis-set edge -> DATA_CENSORED."),
        "registry": ("CF-HA-HARAMI-001/HYP-024 (EXP-071); first counted TEST reads under "
                     "CAND-001; per-stratum counted reads in test_read_manifest.csv; "
                     "portfolio composite is a disclosure against all 6 member strata "
                     "(D0 P10), not a counted read."),
        "instrument_meta": instrument_meta,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Full EXP-071 pipeline. Strict ordering: gates -> P12 -> FREEZE -> TEST inference."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cell_index = exp068._cell_index_map()

    # Step 1a — dependency gates (NO TEST rows).
    LOGGER.info("%s: dependency gates (EXP-070 calibration, EXP-068 g015)", EXPERIMENT_ID)
    calib = load_calibration_map()
    provenance = assert_dependency_gates(calib)

    # Step 1b — P12 reconciliation on TRAIN (NO TEST rows).
    anchor061 = exp068.load_exp061_bench()
    anchor066 = exp068.load_exp066_partial()
    if not anchor061 or not anchor066:
        raise RuntimeError("missing EXP-061/EXP-066 reconciliation anchors (P12 gate)")
    recon_rows = p12_reconcile(cell_index, anchor061, anchor066)

    # Step 1c — FREEZE FILE (D0 P8): written once before any TEST row is loaded; reused
    # (not rewritten) on a bug-fix re-run so the original pre-TEST commitment is preserved.
    freeze_hash, reused = ensure_freeze_file(calib, provenance)
    if not FREEZE_FILE.exists():
        raise RuntimeError("freeze file was not written — TEST contact forbidden (P8)")
    LOGGER.info("freeze file %s + hash-pinned (%s…); TEST contact authorised",
                "reused" if reused else "written", freeze_hash[:12])

    # Step 2-3 — TEST inference (TEST rows loaded only now, after the freeze).
    cells: list[CellInference] = []
    instrument_meta: dict[str, Any] = {}
    for instrument, domain, is_4h in tqdm(BINDING_CELLS, desc="TEST cells"):
        ci = cell_index[(instrument, domain)]
        cell = resolve_test_cell(instrument, domain, is_4h, calib[f"{instrument}-{domain}"], ci)
        cells.append(cell)
        if instrument not in instrument_meta:
            _, _, meta = load_test_1m(instrument)
            instrument_meta[instrument] = meta

    # Step 4-6 — composition, portfolio, manifest.
    classification = classify_cells(cells)
    portfolio = portfolio_composite(cells)
    manifest = build_test_read_manifest(cells)

    # Step 7 — determinism replay (second full pass; byte-identical assertion).
    determinism = determinism_replay(cell_index, calib, cells)
    if not determinism["determinism_pass"]:
        LOGGER.error("DETERMINISM FAILURE: %s", determinism["mismatches"])

    write_outputs(classification, portfolio, manifest, recon_rows, freeze_hash,
                  provenance, determinism, instrument_meta)
    make_plots(classification, portfolio)
    return {"verdict": classification["verdict"], "n_clearing": classification["n_clearing"],
            "clearing_cells": classification["clearing_cells"],
            "n_below_floor": classification["n_below_floor"],
            "composite_median_ci_low_1s": portfolio.get("composite_median_ci_low_1s"),
            "determinism_pass": determinism["determinism_pass"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    argparse.ArgumentParser(description=f"{EXPERIMENT_ID} one-shot TEST confirmation").parse_args()
    LOGGER.info("%s: one-shot TEST confirmation of the 6-cell harami binding family",
                EXPERIMENT_ID)
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("VERDICT: %s", summary["verdict"])
    LOGGER.info("clearing cells (%s): %s", summary["n_clearing"], summary["clearing_cells"])
    LOGGER.info("below-floor cells: %s", summary["n_below_floor"])
    LOGGER.info("portfolio composite median CI_low(1s): %s",
                summary["composite_median_ci_low_1s"])
    LOGGER.info("determinism: %s", "PASS" if summary["determinism_pass"] else "FAIL")
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
