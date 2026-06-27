"""Experiment EXP-080: Phase 018 CF-CAPGEO-001 Substrate/Exit Readiness.

Implements the analysis plan (analysis-plan.md): a determinism + look-ahead-invariant +
coverage readiness map over 192 substrate-cells (4 frozen substrates x 16 instruments x
{15m,1h,4h}), the D7 [15,8000] bracket, ONE statistical test (the moving-block null-FPR
machinery sanity), and four bounded plots. NO exit/return/capture/expectancy/P&L is computed.

Reuse discipline (analysis-plan Step 0 binding note):
  * file resolution + holdout-safe loading reuse the VAL-005-validated
    ``discover_infr003_files`` / ``load_first70`` (the simplified latest-glob would
    mis-select the retained pre-INFR-003 dataset, since the 2021-start 5-year files do not
    sort after the 2023-start old files);
  * production domain construction uses ``xen.domain_bars.build_domain_bars`` (promoted
    verbatim from VAL-005), reconciled to the VAL-005 original on a shared cell BEFORE any
    substrate read;
  * the frozen entry substrates are ``xen.capgeo_substrates`` (AVWAP final + EXP-068 native
    conditioned-harami port + fixed-seed matched-random).

Manual execution gate: run this script yourself; it reads only metadata + the first-70%
analysis slice and never materializes the final-30% holdout.

Run:  python python/experiments/EXP-080/code/run_experiment.py
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
import seaborn as sns  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.ass import default_block_length, moving_block_bootstrap_cis  # noqa: E402
from xen.capgeo_substrates import (  # noqa: E402
    HARAMI_SUBSTRATES,
    MA_SLOW,
    SUB_AVWAP,
    SUB_HARAMI_PARTIAL_V2A,
    SUB_HARAMI_V2A_ADVNONE,
    SUB_RANDOM,
    avwap_entries,
    harami_native_entries,
    random_entries,
)
from xen.domain_bars import build_domain_bars
from xen.avwap import SLOW_MA as AVWAP_SLOW_MA  # noqa: E402

LOGGER = logging.getLogger("EXP-080")

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 reuse (validated resolver/loader; regression anchor)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-080"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_VAL005_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-005" / "code" / "run_experiment.py"


def _load_val005():
    """Import the VAL-005 module (import-safe: constants/functions only, main guarded)."""
    spec = importlib.util.spec_from_file_location("val005_capgeo", _VAL005_CODE)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Could not load VAL-005 from {_VAL005_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Constants (frozen at G0; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_RANDOM = 20260621              # SUB-RANDOM matched-control master seed (D10)
SEED_NULL = 20260621               # null-FPR machinery-probe master seed
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
SUBSTRATE_ORDER = [SUB_AVWAP, SUB_HARAMI_PARTIAL_V2A, SUB_HARAMI_V2A_ADVNONE, SUB_RANDOM]

# D7 ASS-discovery sample-size bracket (Phase-017 validated synthetic span; frozen).
BRACKET_LO, BRACKET_HI = 15, 8000

# Construction-integrity dropped-window bands (frozen; EXP-043/048/VAL-005).
DROP_FLAG, DROP_FAIL = 0.10, 0.25

# Null-FPR machinery sanity (Step 6) — run at the VALIDATED m_cell machinery scale.
# Carrier = block-permuted, mean-centered domain-bar returns (non-tradable machinery probe).
# Tested at event-count scale spanning the [15,8000] bracket (the inference sample size),
# not the domain-bar count: the downstream WF bootstrap operates on per-entry returns whose
# counts the bracket bounds, and FPR control is n-sensitive at the small-n end (Phase-017
# EXP-077/078). The large-n end (>=2000) was validated in Phase 017 and is re-anchored at 2000.
NULL_NS = (15, 30, 60, 120, 250, 500, 2000)
# Scale raised to the D0 §D9 / EXP-027/070 validated m_cell machinery scale per the Stage-5
# governance ruling (2026-06-21): the original bounded probe (N_NULL=1000, N_BOOT=2000) left the
# binding n=120 Wilson-hi gate decision noise-dominated. N_BOOT=10_000 is the validated inner scale
# (D0 §D9 S1: "recomputed per realized structure in EXP-083 at N_BOOT = 10_000"). N_NULL=5000 outer
# replicates resolve the Wilson-hi gate at the operating floor (D0 §D9 S1 calibrated FPR 0.050 at
# Wilson-hi 0.058 ~ >=3000 replicates). The 0.075 gate and the n>=120 floor are UNCHANGED — this
# matches the probe to the scale its criterion was calibrated against (not a goalpost change).
N_NULL = 5000                      # null replicates per n (validated-machinery scale)
NULL_NBOOT = 10000                 # inner bootstrap resamples (D0 §D9 validated m_cell scale)
NULL_ALPHA = 0.10                  # 90% CI -> one-sided 5% lower-bound FPR target
FPR_TARGET, FPR_WILSON_HI = 0.05, 0.075
CARRIER_INSTRUMENT, CARRIER_DOMAIN = "EURUSD", "15m"   # null-carrier source cell
# Operating floor for the BINDING null-FPR halt. The small-n (n < 120) percentile-bootstrap
# FPR inflation is a KNOWN, DISCLOSED property (Phase-017 EXP-077/078; D0 D6 Guard (i):
# "defer to median at effective n<=60"; the D9 bite-check froze the operating floor at n>=120).
# Halting on it would contradict the ratified G0 carry-forward guards, so n < 120 rows are
# recorded as DISCLOSURE (regime="small_n_disclosed") and only n >= 120 rows are halt-binding.
# (Clarifies the analysis-plan's literal "at any tested n" per the binding D0 guards; flagged
# for Stage-4 governance.)
FPR_OPERATING_FLOOR_N = 120


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass
class CellRecord:
    """One substrate-cell readiness record."""

    instrument: str
    domain: str
    substrate: str
    n_bars: int
    dropped_fraction: float
    construction_status: str
    entry_count: int
    entry_rate_per_1k: float
    bracket_flag: str
    invariants_pass: bool
    first_violation: str
    determinism_pass: bool
    readiness_status: str
    detail: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Pure computation — construction integrity
# --------------------------------------------------------------------------- #
def _candidate_window_count(source: pl.DataFrame, period_minutes: int, source_max_ep: int) -> int:
    """Count fence-eligible, data-bearing period-grid windows in the 1-minute source.

    A *candidate* window is a clock-grid bucket (same bucketing rule as
    ``aggregate_ohlc``: ``(CloseTime.epoch('s') - 1) // period_seconds``) that contains
    >=1 source bar AND whose right-label ``(bucket + 1) * period_seconds`` does not exceed
    the last source bar (the holdout fence). Windows dropped by the fence are excluded so
    holdout-hygiene is not counted as a coverage drop. This is the denominator the validated
    EXP-043/048 / ``coverage_summary`` dropped-fraction definition uses.
    """
    if source.height == 0:
        return 0
    period_seconds = period_minutes * 60
    buckets = source.select(
        ((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds).alias("_b")
    ).unique()
    return int(buckets.filter(((pl.col("_b") + 1) * period_seconds) <= source_max_ep).height)


def construction_integrity(
    source: pl.DataFrame, bars: pl.DataFrame, period_minutes: int,
) -> dict:
    """Per (instrument x domain) construction-integrity record (deterministic checks).

    The dropped-window fraction is the VALIDATED coverage-based definition
    (EXP-048 ``(candidate - retained)/candidate``; EXP-043 / ``xen.bar_aggregator``):
    of the fence-eligible, data-bearing period-grid windows (``candidate``), the fraction
    NOT emitted as domain bars (``retained = bars.height``) because they fell below
    ``build_domain_bars``' ``min_coverage`` threshold. It measures coverage/construction
    quality, NOT market-session structure: a continuous-clock denominator would count
    weekend/session-closed time as "dropped" and spuriously exclude every session
    instrument (audit EXP-080 Critical-1).
    """
    n = int(bars.height)
    source_max_ep = (
        int(source.select(pl.col("CloseTime").dt.epoch("s").max()).item())
        if source.height else 0
    )
    candidate = _candidate_window_count(source, period_minutes, source_max_ep)
    if n == 0:
        # No bars emitted: all candidate windows (if any) dropped. 0/0 -> 0.0 (finite).
        dropped = 1.0 if candidate > 0 else 0.0
        return {"n_bars": 0, "dropped_fraction": float(dropped), "ohlc_ok": True,
                "sorted_ok": True, "fence_ok": True, "status": "COVERAGE_EXCLUDED"}
    o = bars.get_column("Open").to_numpy()
    h = bars.get_column("High").to_numpy()
    low = bars.get_column("Low").to_numpy()
    c = bars.get_column("Close").to_numpy()
    ep = bars.get_column("CloseTime").dt.epoch("s").to_numpy()
    ohlc_ok = bool(np.all(h >= np.maximum(o, c)) and np.all(low <= np.minimum(o, c)))
    sorted_ok = bool(np.all(np.diff(ep) > 0))
    fence_ok = bool(ep[-1] <= source_max_ep)
    # Coverage-based dropped fraction: fence-eligible data-bearing windows not retained.
    dropped = 0.0 if candidate == 0 else max(0.0, (candidate - n) / candidate)
    if not (ohlc_ok and sorted_ok and fence_ok) or dropped > DROP_FAIL:
        status = "COVERAGE_EXCLUDED"
    else:
        status = "FLAGGED" if dropped >= DROP_FLAG else "CLEAN"
    return {"n_bars": n, "dropped_fraction": float(dropped), "ohlc_ok": ohlc_ok,
            "sorted_ok": sorted_ok, "fence_ok": fence_ok, "status": status}


# --------------------------------------------------------------------------- #
# Pure computation — entry-detector invariant battery (look-ahead/causality)
# --------------------------------------------------------------------------- #
def entry_invariants(es, bar_epoch: np.ndarray) -> tuple[bool, str]:
    """Assert per-substrate entry invariants. Returns (all_pass, first_violation)."""
    n = es.entry_idx.shape[0]
    if n == 0:
        return True, ""                       # empty set: vacuously clean (sparse disclosure)
    idx, ep = es.entry_idx, es.entry_epoch
    checks: list[tuple[str, bool]] = [
        ("idx_in_range", bool(np.all((idx >= 0) & (idx < bar_epoch.shape[0])))),
        ("on_close", bool(np.all(bar_epoch[np.clip(idx, 0, bar_epoch.shape[0] - 1)] == ep))),
        ("within_span", bool(np.all(ep <= es.analysis_end_epoch))),
        ("monotone", bool(np.all(np.diff(ep) >= 0))),
        ("no_negative_epoch", bool(np.all(ep > 0))),
    ]
    if es.substrate == SUB_AVWAP:
        d = es.detail
        checks.append(("avwap_anchor_causal", bool(np.all(d["anchor_epoch"] <= ep))))
        checks.append(("avwap_armed_causal", bool(np.all(d["armed_epoch"] <= ep))))
    elif es.substrate in HARAMI_SUBSTRATES:
        conf = es.detail["in_progress_confirm_epoch"]
        ok = bool(np.all((conf < 0) | (conf <= ep)))   # in-progress move confirmed <= entry
        checks.append(("harami_in_progress_causal", ok))
    for name, ok in checks:
        if not ok:
            return False, name
    return True, ""


def bracket_flag(count: int) -> str:
    """D7 [15,8000] ASS-discovery bracket classification."""
    if count < BRACKET_LO:
        return "OUT_LOW"
    if count > BRACKET_HI:
        return "OUT_HIGH"
    return "IN_BRACKET"


def entries_equal(a, b) -> bool:
    """Exact entry-set equality (determinism / harami-identity)."""
    return (a.entry_idx.shape == b.entry_idx.shape
            and bool(np.array_equal(a.entry_idx, b.entry_idx))
            and bool(np.array_equal(a.entry_epoch, b.entry_epoch)))


# --------------------------------------------------------------------------- #
# Pure computation — moving-block null-FPR sanity (Step 6, the one statistical test)
# --------------------------------------------------------------------------- #
def _draw_null_series(pool: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Length-n moving-block draw from a long mean-centered carrier (preserves dependence)."""
    b = int(min(max(1, default_block_length(n)), pool.shape[0]))
    n_starts = pool.shape[0] - b + 1
    n_blocks = int(np.ceil(n / b))
    starts = rng.integers(0, n_starts, size=n_blocks)
    idx = (starts[:, None] + np.arange(b)[None, :]).reshape(-1)[:n]
    return pool[idx]


def null_fpr(pool: np.ndarray, rng: np.random.Generator) -> list[dict]:
    """Moving-block bootstrap CI_low>0 FPR over null replicates, per event-count n.

    ``regime`` splits the operating floor (n >= FPR_OPERATING_FLOOR_N, halt-binding) from the
    disclosed small-n inflation (n < floor; Phase-017 known property, not halt-binding).
    ``controlled`` is the raw Wilson-hi <= 0.075 check at every n (transparency); the halt uses
    only the operating-regime rows (see main()).
    """
    rows: list[dict] = []
    for n in tqdm(NULL_NS, desc="null-FPR sanity", leave=False):
        regime = "operating" if n >= FPR_OPERATING_FLOOR_N else "small_n_disclosed"
        if pool.shape[0] < max(8, n):
            rows.append({"n": n, "fpr": float("nan"), "wilson_hi": float("nan"),
                         "n_null": 0, "controlled": False, "regime": regime,
                         "note": "carrier too short"})
            continue
        fp = 0
        for _ in range(N_NULL):
            series = _draw_null_series(pool, n, rng)
            ci = moving_block_bootstrap_cis(series, rng, n_boot=NULL_NBOOT, alpha=NULL_ALPHA)
            fp += int(ci.expectancy_lo > 0.0)
        fpr = fp / N_NULL
        whi = _wilson_upper(fp, N_NULL)
        rows.append({"n": n, "fpr": float(fpr), "wilson_hi": float(whi),
                     "n_null": N_NULL, "controlled": bool(whi <= FPR_WILSON_HI),
                     "regime": regime, "note": ""})
    return rows


def _wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    """Wilson 95% upper bound for a binomial rate."""
    if n == 0:
        return 1.0
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre + margin) / denom)


# --------------------------------------------------------------------------- #
# Plotting (4; built from the collected per-cell summary — no reloads)
# --------------------------------------------------------------------------- #
_STATUS_CODE = {"READY": 0, "CONSTRUCTED_EMPTY": 1, "COVERAGE_EXCLUDED": 2, "NOT_READY": 3}
_BRACKET_CODE = {"IN_BRACKET": 0, "OUT_LOW": 1, "OUT_HIGH": 2}


def _pivot(df: pl.DataFrame, value: str, substrate: str, instruments: list[str]) -> np.ndarray:
    """Instrument x domain matrix of `value` for one substrate (NaN where absent)."""
    sub = df.filter(pl.col("substrate") == substrate)
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    lut = {(r["instrument"], r["domain"]): r[value] for r in sub.iter_rows(named=True)}
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(DOMAIN_ORDER):
            if (inst, dom) in lut:
                mat[i, j] = lut[(inst, dom)]
    return mat


def plot_ready_heatmap(df: pl.DataFrame, instruments: list[str], path: Path) -> None:
    """Plot 1: READY-status small-multiple (4 panels, one per substrate)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)
    cmap = plt.cm.get_cmap("RdYlGn_r", 4)
    for ax, sub in zip(axes, SUBSTRATE_ORDER):
        codes = _pivot(df.with_columns(
            pl.col("readiness_status").replace_strict(_STATUS_CODE, default=3).alias("code")),
            "code", sub, instruments)
        ax.imshow(codes, aspect="auto", cmap=cmap, vmin=0, vmax=3)
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(sub.replace("SUB-", ""), fontsize=9)
    fig.suptitle("EXP-080 substrate-cell readiness "
                 "(green=READY, ... , red=NOT_READY)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_rate_heatmap(df: pl.DataFrame, instruments: list[str], path: Path) -> None:
    """Plot 2: entry-rate (entries / 1,000 domain bars) heatmap by substrate."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)
    for ax, sub in zip(axes, SUBSTRATE_ORDER):
        mat = _pivot(df, "entry_rate_per_1k", sub, instruments)
        im = ax.imshow(mat, aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(sub.replace("SUB-", ""), fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("EXP-080 entry rate (events / 1,000 domain bars)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bracket_map(df: pl.DataFrame, instruments: list[str], path: Path) -> None:
    """Plot 3: D7 [15,8000] bracket map (IN_BRACKET / OUT_LOW / OUT_HIGH) by substrate."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 4, figsize=(16, 7), sharey=True)
    cmap = plt.cm.get_cmap("coolwarm", 3)
    for ax, sub in zip(axes, SUBSTRATE_ORDER):
        codes = _pivot(df.with_columns(
            pl.col("bracket_flag").replace_strict(_BRACKET_CODE, default=1).alias("bcode")),
            "bcode", sub, instruments)
        ax.imshow(codes, aspect="auto", cmap=cmap, vmin=0, vmax=2)
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
        ax.set_title(sub.replace("SUB-", ""), fontsize=9)
    fig.suptitle("EXP-080 D7 bracket (blue=IN, red=OUT_LOW, far=OUT_HIGH)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_count_distribution(df: pl.DataFrame, path: Path) -> None:
    """Plot 4: entry-count distribution (log-x) vs the [15,8000] bracket band."""
    sns.set_theme(style="whitegrid")
    counts = df.filter(pl.col("entry_count") > 0).get_column("entry_count").to_numpy()
    fig, ax = plt.subplots(figsize=(9, 5))
    if counts.size:
        bins = np.logspace(0, np.log10(max(counts.max(), BRACKET_HI) + 1), 40)
        ax.hist(counts, bins=bins, color="steelblue", edgecolor="white")
        ax.set_xscale("log")
    ax.axvspan(BRACKET_LO, BRACKET_HI, color="green", alpha=0.12, label="[15, 8000] bracket")
    ax.axvline(BRACKET_LO, color="green", ls="--")
    ax.axvline(BRACKET_HI, color="green", ls="--")
    ax.set_title(f"EXP-080 entry-count distribution vs D7 bracket (n cells = {counts.size})")
    ax.set_xlabel("entry count (log scale)")
    ax.set_ylabel("substrate-cells")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration helpers
# --------------------------------------------------------------------------- #
def _warmup(substrate: str) -> int:
    """Per-substrate minimum domain-bar count below which no entry state can form."""
    if substrate == SUB_AVWAP:
        return AVWAP_SLOW_MA
    if substrate in HARAMI_SUBSTRATES:
        return MA_SLOW
    return 1


def _make_entrysets(bars: pl.DataFrame, instrument: str, domain: str, cell_index: int) -> dict:
    """Generate all four substrate entry sets for one cell (one deterministic pass)."""
    avwap = avwap_entries(bars, instrument=instrument, domain=domain)
    harami = harami_native_entries(bars, instrument=instrument, domain=domain)
    targets = sorted({int(avwap.entry_idx.shape[0]), int(harami.entry_idx.shape[0])})
    rng = np.random.default_rng([SEED_RANDOM, cell_index])
    rnd_by_target = {
        t: random_entries(bars, instrument=instrument, domain=domain, n_target=t,
                          rng=np.random.default_rng([SEED_RANDOM, cell_index, t]))
        for t in targets}
    harami_count = int(harami.entry_idx.shape[0])
    rnd_headline = rnd_by_target.get(harami_count, random_entries(
        bars, instrument=instrument, domain=domain, n_target=harami_count,
        rng=np.random.default_rng([SEED_RANDOM, cell_index, harami_count])))
    del rng
    return {SUB_AVWAP: avwap, SUB_HARAMI_PARTIAL_V2A: harami,
            SUB_HARAMI_V2A_ADVNONE: harami, SUB_RANDOM: rnd_headline,
            "_rnd_by_target": rnd_by_target}


def _classify(substrate: str, constr: dict, inv_pass: bool, det_pass: bool, n_bars: int) -> str:
    """Per-cell readiness classification."""
    if n_bars < _warmup(substrate):
        return "CONSTRUCTED_EMPTY"
    if constr["status"] == "COVERAGE_EXCLUDED":
        return "NOT_READY"
    if inv_pass and det_pass:
        return "READY"
    return "NOT_READY"


def process_cell(
    frame: pl.DataFrame, instrument: str, period: int, cell_index: int,
) -> tuple[list[CellRecord], dict]:
    """Full readiness pass for one (instrument x domain) cell, all 4 substrates."""
    domain = DOMAIN_LABEL[period]
    bars = build_domain_bars(frame, period)
    bars2 = build_domain_bars(frame, period)            # determinism: domain bars
    bar_epoch = bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64) \
        if bars.height else np.empty(0, np.int64)
    constr = construction_integrity(frame, bars, period)
    bars_det_ok = bars.equals(bars2)

    es1 = _make_entrysets(bars, instrument, domain, cell_index)
    es2 = _make_entrysets(bars, instrument, domain, cell_index)   # determinism: entries

    records: list[CellRecord] = []
    for sub in SUBSTRATE_ORDER:
        es = es1[sub]
        cnt = int(es.entry_idx.shape[0])
        inv_pass, viol = entry_invariants(es, bar_epoch)
        det_pass = bool(bars_det_ok and entries_equal(es, es2[sub]))
        status = _classify(sub, constr, inv_pass, det_pass, constr["n_bars"])
        rate = (1000.0 * cnt / constr["n_bars"]) if constr["n_bars"] else 0.0
        detail = {"matched_targets": sorted(es1["_rnd_by_target"].keys())} \
            if sub == SUB_RANDOM else {}
        records.append(CellRecord(
            instrument=instrument, domain=domain, substrate=sub, n_bars=constr["n_bars"],
            dropped_fraction=round(constr["dropped_fraction"], 6),
            construction_status=constr["status"], entry_count=cnt,
            entry_rate_per_1k=round(rate, 4), bracket_flag=bracket_flag(cnt),
            invariants_pass=inv_pass, first_violation=viol, determinism_pass=det_pass,
            readiness_status=status, detail=detail))

    # Step 7 — harami entry-population identity (shared detector -> identical by construction)
    harami_identical = entries_equal(es1[SUB_HARAMI_PARTIAL_V2A], es1[SUB_HARAMI_V2A_ADVNONE])
    # null carrier: centered domain-bar log returns of the designated carrier cell (Step 6).
    # Captured once here (no re-derivation later) — a non-tradable machinery probe, not an edge.
    carrier = None
    if instrument == CARRIER_INSTRUMENT and domain == CARRIER_DOMAIN and bars.height > 2:
        rets = np.diff(np.log(bars.get_column("Close").to_numpy().astype(np.float64)))
        rets = rets[np.isfinite(rets)]
        carrier = rets - rets.mean()
    cell_meta = {"instrument": instrument, "domain": domain,
                 "harami_identical": bool(harami_identical),
                 "harami_count": int(es1[SUB_HARAMI_PARTIAL_V2A].entry_idx.shape[0]),
                 "avwap_count": int(es1[SUB_AVWAP].entry_idx.shape[0]),
                 "carrier": carrier}
    return records, cell_meta


# --------------------------------------------------------------------------- #
# Regression check — xen.domain_bars vs VAL-005 original (before substrate reads)
# --------------------------------------------------------------------------- #
def regression_check(val005, frame: pl.DataFrame, period: int) -> dict:
    """Reconcile xen.domain_bars.build_domain_bars to VAL-005 on one shared cell."""
    ours = build_domain_bars(frame, period)
    theirs = val005.build_domain_bars(frame, period)
    ok = ours.equals(theirs)
    return {"period_minutes": period, "rows_ours": int(ours.height),
            "rows_val005": int(theirs.height), "frame_identical": bool(ok)}


# --------------------------------------------------------------------------- #
# main()
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-080 — Phase 018 substrate/exit readiness")

    val005 = _load_val005()
    found, missing = val005.discover_infr003_files()
    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    LOGGER.info("Resolved %d/%d INFR-003 files (missing: %s)",
                len(instruments), len(val005.TARGET_SYMBOLS), sorted(missing) or "none")

    # Load all analysis slices (holdout-safe; reused validated loader).
    loaded: dict[str, object] = {}
    for inst in instruments:
        li, _seal, status = val005.load_first70(found[inst])
        if li is None:
            missing[inst] = f"load failed: {status}"
            continue
        loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    if not instruments:
        raise RuntimeError("no instruments loaded; cannot run readiness")

    # Step 0 — regression check BEFORE any substrate read (first loaded instrument, 15m).
    reg = regression_check(val005, loaded[instruments[0]].frame, val005.DOMAINS[0])
    LOGGER.info("Domain-bar regression vs VAL-005 (%s, %dm): identical=%s (%d rows)",
                instruments[0], reg["period_minutes"], reg["frame_identical"], reg["rows_ours"])
    if not reg["frame_identical"]:
        raise RuntimeError("REGRESSION FAIL: xen.domain_bars diverges from VAL-005")

    # Per-cell readiness passes (192 substrate-cells = 48 instrument x domain cells x 4).
    records: list[CellRecord] = []
    cell_metas: list[dict] = []
    carrier_returns: np.ndarray | None = None
    cells = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    for ci, (inst, period) in enumerate(tqdm(cells, desc="readiness cells")):
        recs, meta = process_cell(loaded[inst].frame, inst, period, ci)
        records.extend(recs)
        carrier = meta.pop("carrier")                 # keep carrier out of the serialized meta
        if carrier is not None:
            carrier_returns = carrier                 # designated carrier cell's centered returns
        cell_metas.append(meta)
    if carrier_returns is None:                        # carrier cell absent: use first dense cell
        for inst, period in cells:
            cb = build_domain_bars(loaded[inst].frame, period)
            if cb.height > 2:
                r = np.diff(np.log(cb.get_column("Close").to_numpy().astype(np.float64)))
                r = r[np.isfinite(r)]
                carrier_returns = r - r.mean()
                break

    # Step 6 — moving-block null-FPR sanity.
    LOGGER.info("Null-FPR machinery sanity over n=%s (carrier len=%d)",
                NULL_NS, 0 if carrier_returns is None else carrier_returns.shape[0])
    fpr_rows = null_fpr(carrier_returns, np.random.default_rng(SEED_NULL)) \
        if carrier_returns is not None else []

    # Aggregate -> verdict (Step 8).
    df = pl.DataFrame([{k: v for k, v in asdict(r).items() if k != "detail"} for r in records])
    status_counts = df.get_column("readiness_status").value_counts().to_dicts()
    nondet = df.filter(~pl.col("determinism_pass")).height
    inv_fail = df.filter(~pl.col("invariants_pass"))
    # >=3-instrument same-violation-per-substrate halt trigger
    halt_inv = False
    if inv_fail.height:
        grp = (inv_fail.group_by(["substrate", "first_violation"])
               .agg(pl.col("instrument").n_unique().alias("n_inst")))
        halt_inv = bool(grp.filter(pl.col("n_inst") >= 3).height)
    # Halt only on OPERATING-regime (n >= floor) FPR failure; small-n inflation is disclosed
    # (Phase-017 D6 Guard (i) + D9 operating floor), not a machinery defect.
    null_uncontrolled = any(
        r["regime"] == "operating" and r["n_null"] > 0 and not r["controlled"]
        for r in fpr_rows)
    small_n_disclosed = any(
        r["regime"] == "small_n_disclosed" and r["n_null"] > 0 and not r["controlled"]
        for r in fpr_rows)
    refuted = bool(nondet > 0 or halt_inv or null_uncontrolled)
    verdict = "SUBSTRATE_REFUTED" if refuted else "READINESS_DELIVERED"
    harami_all_identical = all(m["harami_identical"] for m in cell_metas)

    # Persist results.
    df.write_csv(RESULTS_DIR / "ready_map.csv")
    df.select(["instrument", "domain", "substrate", "entry_count", "entry_rate_per_1k",
               "n_bars", "bracket_flag"]).write_csv(RESULTS_DIR / "entry_counts_bracket.csv")
    df.write_parquet(RESULTS_DIR / "substrate_cell_summary.parquet")
    (RESULTS_DIR / "null_fpr.json").write_text(json.dumps(
        {"params": {"n_values": list(NULL_NS), "n_null": N_NULL, "n_boot": NULL_NBOOT,
                    "alpha": NULL_ALPHA, "fpr_target": FPR_TARGET,
                    "wilson_hi_gate": FPR_WILSON_HI,
                    "operating_floor_n": FPR_OPERATING_FLOOR_N,
                    "halt_binds_on": "operating regime (n >= operating_floor_n) only; "
                    "small-n inflation disclosed per Phase-017 D6 Guard (i) + D9 floor",
                    "carrier": f"{CARRIER_INSTRUMENT}-{CARRIER_DOMAIN} centered domain-bar "
                    "log-returns (non-tradable machinery probe)"},
         "rows": fpr_rows}, indent=2))

    meta = {
        "experiment": EXPERIMENT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "status_counts": status_counts,
        "nondeterministic_cells": int(nondet),
        "invariant_failure_cells": int(inv_fail.height),
        "halt_invariant_ge3_instruments": halt_inv,
        "null_fpr_uncontrolled_operating": null_uncontrolled,
        "null_fpr_small_n_inflation_disclosed": small_n_disclosed,
        "null_fpr_operating_floor_n": FPR_OPERATING_FLOOR_N,
        "harami_entry_identity_all_cells": harami_all_identical,
        "harami_entry_identity_basis": "shared detector by construction (both harami substrates "
        "carry the one MA-native /STRONG-STAT-conditioned HA-harami entry; they differ only by "
        "exit, not applied in EXP-080) -> entry-level counted-read accounting coincides",
        "n_substrate_cells": df.height,
        "instruments": instruments,
        "missing_instruments": missing,
        "domains": [DOMAIN_LABEL[p] for p in val005.DOMAINS],
        "regression_check": reg,
        "seeds": {"SEED_RANDOM": SEED_RANDOM, "SEED_NULL": SEED_NULL},
        "frozen_constants": {"bracket": [BRACKET_LO, BRACKET_HI],
                             "drop_bands": [DROP_FLAG, DROP_FAIL],
                             "ma_slow": MA_SLOW, "avwap_slow_ma": AVWAP_SLOW_MA},
        "source_files": {s: found[s].name for s in instruments},
        "polars_version": pl.__version__, "numpy_version": np.__version__,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2))

    # Plots (from the collected summary — no reloads).
    plot_ready_heatmap(df, instruments, PLOTS_DIR / "01_ready_status_heatmap.png")
    plot_rate_heatmap(df, instruments, PLOTS_DIR / "02_entry_rate_heatmap.png")
    plot_bracket_map(df, instruments, PLOTS_DIR / "03_d7_bracket_map.png")
    plot_count_distribution(df, PLOTS_DIR / "04_entry_count_distribution.png")

    LOGGER.info("VERDICT: %s | cells=%d | status=%s", verdict, df.height, status_counts)
    LOGGER.info("null-FPR controlled at all n: %s | harami entry-identity all cells: %s",
                not null_uncontrolled, harami_all_identical)
    LOGGER.info("Wrote results/ and plots/ under %s", EXPERIMENT_DIR)


if __name__ == "__main__":
    main()
