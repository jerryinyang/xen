"""EXP-093 — One-Shot TEST Confirmation of the RSI-2 Fade (EXIT-RCT; 11 carried cells).

Phase 021 / ``CF-MR-001`` / HYP-002 — the phase's single binding tradability read (analog
EXP-037/038/032). Governing D0:
``docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/`` — ``D0-predeclarations.md``
§D6/4c (TEST PASS rule) + §D7 (counted-read accounting), ``D0-amendment-003`` (Phase-021 cost table),
``D0-amendment-004``/``-005`` (4h ADMITTED via EXP-094), ``D0-amendment-006`` (carried set = all 11
EXP-092 SEQUENCE_PASS cells; Holm-11). Reads the **analysis-TEST stratum** of the 11 carried strata;
**11 counted TEST reads, 0 candidate slots, final-30% global holdout never loaded**.

What this is. EXIT-RCT was the only exit to survive the EXP-091/094 screen and the EXP-092 sequence pinned
11 SEQUENCE_PASS cells (sha256 ``f6427e83…``). EXP-093 resolves the **real** EXIT-RCT exits on the
analysis-TEST stratum of all 11 carried cells, overlays the frozen cost, and applies the binding rule:

    Cell CONFIRMS iff  Holm-adj p <= 0.05  AND  net ci_low_1s > margin   (margin = EXP-090/094 MDE)
    Holm family = the 11 carried cells (one-sided, alpha=0.05; D0-amendment-006).

Substrate reuse (verbatim). The EXP-090 module (``build_cell_context``, ``resolve_arm``/RCT, the 1-minute
intrabar fill engine, ``net_return_atr``) and the EXP-092 cost overlay are imported/mirrored unchanged. The
**only** delta vs EXP-092 is the data slice: instead of the TRAIN sub-split, EXP-093 loads the full
**analysis set** ``[0, int(total*0.7))`` (the TRAIN region serving only as causal indicator warmup) and takes
the binding estimand from the CORE fade entries whose **domain CloseTime falls in the analysis-TEST stratum**
``[ts_lo, analysis_edge]`` (``ts_lo = CloseTime[int(int(total*0.7)*0.7)]``). The 1-minute fill walk clips at
the analysis edge by timestamp (``train_edge_epoch`` = the last analysis 1m bar) — **the final-30% holdout 1m
bars are never loaded**. EXP-093 adds only the analysis-TEST loader, the per-cell one-sided bootstrap p, the
Holm-11 procedure, and the adjudication.

Cost (D3 + D0-amendment-003). Phase-021-local CONSERVATIVE round-trip ``RT_i`` (bps) + ``F_i = 0``; the shared
``xen.capgeo_cost.COST_CONSTANTS`` is NOT edited (Phase-018 integrity).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.ass import BOOT_BATCH, default_block_length  # noqa: E402
from xen.capgeo_cost import event_costs, holding_days  # noqa: E402
from xen.intrabar_fill import KIND_FAV, net_return_atr  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-090 substrate reuse (import the validated module directly)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-093"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
EXP090_CODE = EXP_ROOT / "EXP-090" / "code" / "run_experiment.py"
EXP090_MEMBER_MAP = EXP_ROOT / "EXP-090" / "results" / "member_map.csv"
EXP091_SCREEN = EXP_ROOT / "EXP-091" / "results" / "screen_per_cell_arm.csv"
EXP094_READINESS = EXP_ROOT / "EXP-094" / "results" / "readiness_4h.csv"
EXP092_META = EXP_ROOT / "EXP-092" / "results" / "run_metadata.json"
EXP092_CANDIDATE = EXP_ROOT / "EXP-092" / "results" / "candidate_set.csv"


def _load_exp090() -> Any:
    """Import the validated EXP-090 module (import-safe: ``main`` guarded; reuses its substrate)."""
    if not EXP090_CODE.exists():
        raise FileNotFoundError(f"EXP-090 module missing: {EXP090_CODE}")
    spec = importlib.util.spec_from_file_location("exp090_mr_readiness", EXP090_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load EXP-090 from {EXP090_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


E90 = _load_exp090()
E90.DOMAINS["4h"] = 240                                  # patch 4h (240-min); EXP-094 ADMITTED it (amd-004/005)

# --------------------------------------------------------------------------- #
# Constants (frozen at D0/G0 + D0-amendment-003/004/005/006; never tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = E90.MASTER_SEED                            # 20260623 (shared)
DOMAINS: dict[str, int] = E90.DOMAINS                   # {"15m":15,"1h":60,"4h":240}
ARM = "RCT"                                              # the sole surviving exit (EXP-091/094)

# Carried candidate universe = the full EXP-092 SEQUENCE_PASS set, all 11 cells (D0-amendment-006,
# operator-ratified 2026-06-24). Hash-pinned f6427e83…; re-derived + asserted against upstream below.
CARRIED_1H = ("EURUSD", "GBPUSD", "NZDUSD", "US2000", "USTEC")
CARRIED_4H = ("AUDJPY", "EURJPY", "EURUSD", "GBPJPY", "USDCHF", "XAUUSD")
PINNED_CANDIDATE_SHA256_PREFIX = "f6427e83"              # EXP-092 candidate_set_sha256 provenance pin

# Phase-021 cost table (D0-amendment-003, FROZEN 2026-06-24). RT_i (bps) CONSERVATIVE = 4*c_i; F_i = 0.
# Phase-021-LOCAL — shared xen.capgeo_cost.COST_CONSTANTS is NOT mutated (Phase-018 integrity).
MR_COST_RT_BPS: dict[str, float] = {
    "EURUSD": 3.0, "GBPUSD": 4.0, "USDJPY": 4.0, "USDCHF": 4.0, "AUDUSD": 4.0, "NZDUSD": 4.5,
    "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0, "XAUUSD": 6.0, "USTEC": 5.0, "US2000": 6.0,
    "JP225": 6.0,
}
FIN_BPS_DAY = 0.0                                        # F = 0 (D0-amendment-003)

# Binding inference (D6/4c). Bit-identical block scheme to xen.ass.moving_block_bootstrap_cis (mean leg).
N_BOOT = 10_000                                          # moving-block bootstrap resamples
BOOT_ALPHA = 0.10                                        # 90% CI -> 5th pct = one-sided 95% lower (Z=1.645)
HOLM_ALPHA = 0.05                                        # phase Holm one-sided alpha (D6/4c)
DETERMINISM_CELLS = (("USTEC", "1h"), ("EURUSD", "4h"))  # one 1h + one 4h replay (D9)

HEADLINE_OUTPUTS = ("test_adjudication.csv", "test_per_cell.csv", "train_vs_test.csv")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellTest:
    """Per carried (instrument, domain) cell EXIT-RCT TEST-stratum result (ATR units, real prices)."""

    instrument: str
    domain: str
    n_events: int
    n_resolved: int
    resolved_frac: float
    tie_break_frac: float
    terminal_fav: float
    holding_days_mean: float
    gross_mean: float
    net_mean: float
    net_median: float
    net_ci_low: float
    boot_p: float
    margin: float
    mae_q05: float


# --------------------------------------------------------------------------- #
# I/O helpers (analysis-TEST slice; the final-30% global holdout is never loaded)
# --------------------------------------------------------------------------- #
def load_analysis_1m(instrument: str, path: Path) -> tuple[pl.DataFrame, int, dict[str, Any]]:
    """Load the **analysis set** ``[0, int(total*0.7))`` and the analysis-TEST start epoch ``ts_lo``.

    The full first-70% analysis set is loaded so RSI(2)/ATR(14)/EMA(10) have causal warmup and the 1m
    fill walk can extend to the analysis edge; the TRAIN region ``[0, train_cutoff)`` serves only as
    warmup (no TRAIN entry enters the binding estimand). The **final-30% global holdout
    ``[analysis_cutoff, total)`` is never sliced or materialized**. ``ts_lo`` =
    ``CloseTime[int(int(total*0.7)*0.7)]`` (the analysis-TEST stratum's left edge, 1-minute-row
    timestamp boundary R1.3). Returns (analysis 1m frame, ts_lo_epoch, source-identity record).
    """
    scan = pl.scan_parquet(path).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total_rows * 0.7)
    train_cutoff = int(analysis_cutoff * 0.7)
    # ts_lo from the analysis frame itself (row train_cutoff); holdout rows are never read.
    frame = scan.slice(0, analysis_cutoff).collect()
    if frame.height != analysis_cutoff:                           # 0 holdout rows read (assert)
        raise RuntimeError(f"{instrument}: analysis slice {frame.height} != {analysis_cutoff}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: analysis slice not sorted by CloseTime")
    ts_lo_epoch = int(frame.get_column("CloseTime").dt.epoch("s").to_numpy()[train_cutoff])
    meta = {"source_file": path.name, "total_rows": total_rows, "analysis_rows": analysis_cutoff,
            "train_rows": train_cutoff, "test_rows": analysis_cutoff - train_cutoff,
            "ts_lo": str(frame.get_column("CloseTime").to_numpy()[train_cutoff]),
            "analysis_end": str(frame.get_column("CloseTime").max())}
    return frame, ts_lo_epoch, meta


def load_carried_cells() -> tuple[list[tuple[str, str]], dict[tuple[str, str], float]]:
    """Re-derive the 11 carried EXIT-RCT cells from upstream, assert == the pinned set, return margins.

    1h survivors from EXP-091 (RCT net_clear), 4h members from EXP-094 (ADMIT_4H MEMBERs); margins from
    EXP-090 member_map (1h ``rct_margin``) + EXP-094 readiness (4h ``rct_mde``). Provenance: assert the
    EXP-092 candidate set hashes to ``f6427e83…`` and its 11 cells == the carried set (hard-fail on any
    drift so the carried set cannot silently change).
    """
    for p in (EXP090_MEMBER_MAP, EXP091_SCREEN, EXP094_READINESS, EXP092_META, EXP092_CANDIDATE):
        if not p.exists():
            raise FileNotFoundError(f"dependency gate: missing upstream artifact {p}")

    s91 = pl.read_csv(EXP091_SCREEN)
    rct1h = s91.filter((pl.col("arm") == ARM) & (pl.col("domain") == "1h") & (pl.col("net_clear")))
    got_1h = sorted(rct1h["instrument"].to_list())
    if got_1h != sorted(CARRIED_1H):
        raise ValueError(f"EXP-091 1h RCT net-clear drift: expected {sorted(CARRIED_1H)}, got {got_1h}")

    r94 = pl.read_csv(EXP094_READINESS)
    mem4h = r94.filter((pl.col("domain") == "4h") & (pl.col("verdict") == "MEMBER"))
    got_4h = sorted(mem4h["instrument"].to_list())
    if got_4h != sorted(CARRIED_4H):
        raise ValueError(f"EXP-094 4h MEMBER drift: expected {sorted(CARRIED_4H)}, got {got_4h}")

    # Provenance pin: EXP-092 candidate set hash + membership == the carried 11 (D0-amendment-006).
    e92_meta = json.loads(EXP092_META.read_text())
    pinned = str(e92_meta.get("candidate_set_sha256", ""))
    if not pinned.startswith(PINNED_CANDIDATE_SHA256_PREFIX):
        raise ValueError(f"EXP-092 candidate hash drift: {pinned[:12]} != {PINNED_CANDIDATE_SHA256_PREFIX}…")
    pinned_cells = sorted(pl.read_csv(EXP092_CANDIDATE)["cell"].to_list())
    cells: list[tuple[str, str]] = [(i, "1h") for i in CARRIED_1H] + [(i, "4h") for i in CARRIED_4H]
    if sorted(f"{i}-{d}" for i, d in cells) != pinned_cells:
        raise ValueError(f"carried set != pinned EXP-092 set: {pinned_cells}")

    mm = pl.read_csv(EXP090_MEMBER_MAP)
    mm1h = mm.filter((pl.col("domain") == "1h") & (pl.col("verdict") == "MEMBER"))
    margin_1h = {r["instrument"]: float(r["rct_margin"]) for r in mm1h.iter_rows(named=True)}
    margin_4h = {r["instrument"]: float(r["rct_mde"]) for r in mem4h.iter_rows(named=True)}
    margins: dict[tuple[str, str], float] = {}
    for instr, dom in cells:
        m = margin_1h.get(instr) if dom == "1h" else margin_4h.get(instr)
        if m is None or not np.isfinite(m) or m <= 0.0:
            raise ValueError(f"power-confirmation gate: {instr}-{dom} has no finite positive MDE ({m})")
        margins[(instr, dom)] = m
        if instr not in MR_COST_RT_BPS:                  # cost table must price every carried instrument
            raise ValueError(f"cost table (D0-amendment-003) missing instrument: {instr}")
    return cells, margins


# --------------------------------------------------------------------------- #
# Pure computation — binding inference (block bootstrap lower bound + one-sided p)
# --------------------------------------------------------------------------- #
def _mblock_lower_and_p(x: np.ndarray, rng: np.random.Generator, *, n_boot: int, alpha: float,
                        block: int | None = None, batch: int = BOOT_BATCH) -> tuple[float, float]:
    """Moving-block bootstrap one-sided mean lower bound **and** one-sided p (same resample stream).

    Bit-for-bit reproduces ``xen.ass.moving_block_bootstrap_cis(...).expectancy_lo`` for the mean leg
    (identical block scheme / ``rng.integers`` call shape / batching / percentile; the shared
    estimator's median leg consumes no randomness, so the mean lower bound is identical). From the same
    gathered resample means it also returns ``boot_p = (1 + #{mean <= 0}) / (1 + n_boot)`` — the
    EXP-032/037/038 one-sided bootstrap p for ``H0: net expectancy <= 0``.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        raise ValueError(f"_mblock_lower_and_p needs >= 2 points, got {n}")
    b = int(block) if block is not None else default_block_length(n)
    b = int(min(max(1, b), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    exp_boot = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]
        exp_boot[done:done + bs] = x[idx].mean(axis=1)
        done += bs
    ci_low = float(np.percentile(exp_boot, 100.0 * alpha / 2.0))
    boot_p = float((1 + int(np.count_nonzero(exp_boot <= 0.0))) / (1 + n_boot))
    return ci_low, boot_p


# --------------------------------------------------------------------------- #
# Pure computation — resolve real EXIT-RCT exits on the analysis-TEST stratum
# --------------------------------------------------------------------------- #
def _test_entries(ctx: Any, ts_lo_epoch: int) -> tuple[np.ndarray, np.ndarray]:
    """CORE fade entries whose domain-bar CloseTime is in the analysis-TEST stratum (>= ts_lo).

    Entry selection is by timestamp (domain ``CloseTime`` epoch), never by bar index; the TRAIN region
    (domain close < ts_lo) is warmup only. The upper edge is the analysis edge — no domain bar exists
    beyond it (holdout never loaded).
    """
    idx = ctx.core_entry_idx
    in_test = ctx.domain_close_epoch[idx] >= ts_lo_epoch
    return idx[in_test], ctx.core_direction[in_test]


def test_cell(ctx: Any, ts_lo_epoch: int, margin: float) -> CellTest:
    """Resolve real EXIT-RCT exits on the TEST stratum, overlay cost, compute net lower bound + boot_p.

    Mirrors EXP-092 ``sequence_cell`` exactly (same engine, same ``keep`` mask, same cost overlay) on
    the TEST-stratum entry subset; adds the one-sided bootstrap p for the Holm leg.
    """
    test_idx, test_dir = _test_entries(ctx, ts_lo_epoch)
    n_events = int(test_idx.shape[0])
    if n_events == 0:
        return _indeterminate_cell(ctx, n_events, 0, margin)
    res = E90.resolve_arm(ctx, test_idx, test_dir, ARM, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[test_idx], test_dir, ctx.atr[test_idx])
    hd = holding_days(test_idx, res.exit_domain_idx, DOMAINS[ctx.domain])
    p_entry, atr_entry = ctx.close[test_idx], ctx.atr[test_idx]
    keep = res.resolved & np.isfinite(gross) & np.isfinite(atr_entry) & (atr_entry > 0.0) \
        & np.isfinite(hd) & (hd >= 0.0)
    n_resolved = int(np.count_nonzero(keep))
    tie = res.tie_break[keep]
    tie_frac = float(np.mean(tie)) if tie.shape[0] else 0.0
    terminal_fav = float(np.mean(res.kind[keep] == KIND_FAV)) if n_resolved else float("nan")
    if n_resolved < 2:                                   # cannot bootstrap -> INDETERMINATE
        return _indeterminate_cell(ctx, n_events, n_resolved, margin, tie_frac, terminal_fav,
                                   float(np.mean(res.resolved)))
    g = gross[keep]
    costs = event_costs(g, p_entry[keep], atr_entry[keep], hd[keep],
                        rt_bps=MR_COST_RT_BPS[ctx.instrument], fin_bps_day=FIN_BPS_DAY)
    net = costs.net
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, ARM, "net"))
    net_lo, boot_p = _mblock_lower_and_p(net, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
    mae_q05 = float(np.percentile(g, 5.0))               # adverse-tail shape read (gross, ATR)
    return CellTest(
        instrument=ctx.instrument, domain=ctx.domain, n_events=n_events, n_resolved=n_resolved,
        resolved_frac=float(np.mean(res.resolved)), tie_break_frac=tie_frac, terminal_fav=terminal_fav,
        holding_days_mean=float(np.mean(hd[keep])), gross_mean=float(np.mean(g)),
        net_mean=float(np.mean(net)), net_median=float(np.median(net)), net_ci_low=net_lo,
        boot_p=boot_p, margin=margin, mae_q05=mae_q05)


def _indeterminate_cell(ctx: Any, n_events: int, n_resolved: int, margin: float,
                        tie_frac: float = float("nan"), terminal_fav: float = float("nan"),
                        resolved_frac: float = float("nan")) -> CellTest:
    """A cell with < 2 resolved TEST events: reported as INDETERMINATE (no forced number)."""
    nan = float("nan")
    return CellTest(ctx.instrument, ctx.domain, n_events, n_resolved, resolved_frac, tie_frac,
                    terminal_fav, nan, nan, nan, nan, nan, nan, margin, nan)


# --------------------------------------------------------------------------- #
# Pure computation — Holm-11 over one-sided p, then the per-cell adjudication (D6/4c)
# --------------------------------------------------------------------------- #
def holm_adjust(pvals: dict[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    """Holm-Bonferroni step-down adjusted one-sided p-values over the carried family.

    NaN p (INDETERMINATE cells) carried as NaN (cannot enter the ordered family); the family size is
    the count of finite p-values (the carried cells that produced a bound).
    """
    items = [(k, p) for k, p in pvals.items() if np.isfinite(p)]
    m = len(items)
    items.sort(key=lambda kp: kp[1])
    adj: dict[tuple[str, str], float] = {k: float("nan") for k in pvals}
    running = 0.0
    for rank, (k, p) in enumerate(items):
        val = (m - rank) * p
        running = max(running, val)                      # enforce monotonic non-decreasing step-down
        adj[k] = float(min(1.0, running))
    return adj


def adjudicate(cell: CellTest, holm_adj_p: float) -> str:
    """Frozen D6/4c per-cell verdict: CONFIRM / FAIL / INCONCLUSIVE / INDETERMINATE."""
    if cell.n_resolved < 2 or not np.isfinite(cell.net_ci_low):
        return "INDETERMINATE"
    holm_sig = np.isfinite(holm_adj_p) and holm_adj_p <= HOLM_ALPHA
    clears_margin = cell.net_ci_low > cell.margin
    if holm_sig and clears_margin:
        return "CONFIRM"
    if cell.net_ci_low <= 0.0:                           # bound spans zero -> power-limited
        return "INCONCLUSIVE"
    return "FAIL"                                         # significant-but-immaterial, or not Holm-sig


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(cell: tuple[str, str], path: Path, margin: float) -> CellTest:
    """Build the cell substrate over the analysis set (EXP-090 verbatim) + run the TEST-stratum read."""
    instrument, domain = cell
    analysis_1m, ts_lo_epoch, _meta = load_analysis_1m(instrument, path)
    ctx, _dropped, status = E90.build_cell_context(analysis_1m, instrument, domain)
    if ctx is None:                                      # a carried cell must build (upstream guarantee)
        raise RuntimeError(f"{instrument}-{domain}: carried cell failed to build ({status})")
    return test_cell(ctx, ts_lo_epoch, margin)


# --------------------------------------------------------------------------- #
# Determinism + hashing
# --------------------------------------------------------------------------- #
def determinism_replay(results: dict[tuple[str, str], CellTest], files: dict[str, Path],
                       margins: dict[tuple[str, str], float]) -> dict[str, Any]:
    """Re-run one 1h + one 4h cell; assert net_ci_low / boot_p / n_resolved frame-identical (D9)."""
    checked, mismatches = [], []
    for cell in DETERMINISM_CELLS:
        if cell not in results:
            continue
        checked.append(f"{cell[0]}-{cell[1]}")
        b = compute_cell(cell, files[cell[0]], margins[cell])
        a = results[cell]
        if not (_eq(a.net_ci_low, b.net_ci_low) and _eq(a.boot_p, b.boot_p)
                and a.n_resolved == b.n_resolved):
            mismatches.append(f"{cell[0]}-{cell[1]}")
    return {"determinism_pass": not mismatches, "cells_checked": checked,
            "non_deterministic": mismatches}


def _eq(a: float, b: float) -> bool:
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    out: dict[str, str] = {}
    for name in HEADLINE_OUTPUTS:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def cost_table_hash() -> str:
    """Provenance hash of the Phase-021 cost table (D0-amendment-003)."""
    payload = json.dumps({"RT": MR_COST_RT_BPS, "F": FIN_BPS_DAY}, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def load_train_reference() -> dict[str, dict[str, float]]:
    """EXP-092 TRAIN net_ci_low / net_mean per cell (for the TRAIN->TEST shrinkage companion)."""
    df = pl.read_csv(EXP092_CANDIDATE)
    return {r["cell"]: {"train_net_ci_low": float(r["net_ci_low"]), "train_net_mean": float(r["net_mean"])}
            for r in df.iter_rows(named=True)}


def write_outputs(results: list[CellTest], adj: dict[tuple[str, str], float],
                  verdicts: dict[tuple[str, str], str], train_ref: dict[str, dict[str, float]]) -> None:
    """Write the three headline tables: per-cell TEST, the adjudication, and TRAIN->TEST shrinkage."""
    per_cell = [{
        "cell": f"{r.instrument}-{r.domain}", "instrument": r.instrument, "domain": r.domain,
        "n_events": r.n_events, "n_resolved": r.n_resolved, "resolved_frac": r.resolved_frac,
        "tie_break_frac": r.tie_break_frac, "terminal_fav": r.terminal_fav,
        "holding_days_mean": r.holding_days_mean, "gross_mean": r.gross_mean, "net_mean": r.net_mean,
        "net_median": r.net_median, "net_ci_low": r.net_ci_low, "boot_p": r.boot_p,
        "mae_q05": r.mae_q05, "margin": r.margin} for r in results]
    pl.DataFrame(per_cell).write_csv(RESULTS_DIR / "test_per_cell.csv")

    adj_rows = []
    for r in results:
        k = (r.instrument, r.domain)
        ap = adj[k]
        adj_rows.append({
            "cell": f"{r.instrument}-{r.domain}", "instrument": r.instrument, "domain": r.domain,
            "n_resolved": r.n_resolved, "net_mean": r.net_mean, "net_median": r.net_median,
            "net_ci_low": r.net_ci_low, "margin": r.margin, "boot_p": r.boot_p, "holm_adj_p": ap,
            "holm_sig": bool(np.isfinite(ap) and ap <= HOLM_ALPHA),
            "clears_margin": bool(np.isfinite(r.net_ci_low) and r.net_ci_low > r.margin),
            "verdict": verdicts[k]})
    pl.DataFrame(adj_rows).write_csv(RESULTS_DIR / "test_adjudication.csv")

    shrink = []
    for r in results:
        ref = train_ref.get(f"{r.instrument}-{r.domain}", {})
        t_ci = ref.get("train_net_ci_low", float("nan"))
        t_mean = ref.get("train_net_mean", float("nan"))
        shrink.append({
            "cell": f"{r.instrument}-{r.domain}", "domain": r.domain,
            "train_net_ci_low": t_ci, "test_net_ci_low": r.net_ci_low,
            "delta_net_ci_low": r.net_ci_low - t_ci if np.isfinite(r.net_ci_low) else float("nan"),
            "train_net_mean": t_mean, "test_net_mean": r.net_mean,
            "delta_net_mean": r.net_mean - t_mean if np.isfinite(r.net_mean) else float("nan")})
    pl.DataFrame(shrink).write_csv(RESULTS_DIR / "train_vs_test.csv")


# --------------------------------------------------------------------------- #
# Plotting (4 bounded plots from collected summaries; no reloads)
# --------------------------------------------------------------------------- #
def make_plots(results: list[CellTest], adj: dict[tuple[str, str], float],
               verdicts: dict[tuple[str, str], str], train_ref: dict[str, dict[str, float]]) -> None:
    _plot_test_ci_vs_thresholds(results, verdicts)
    _plot_confirm_map(results, verdicts)
    _plot_train_vs_test(results, train_ref)
    _plot_boot_inputs(results)


def _ordered(results: list[CellTest]) -> list[CellTest]:
    return sorted(results, key=lambda r: (r.domain, -(r.net_ci_low if np.isfinite(r.net_ci_low) else -9)))


def _plot_test_ci_vs_thresholds(results: list[CellTest], verdicts: dict[tuple[str, str], str]) -> None:
    order = _ordered(results)
    labels = [f"{r.instrument}-{r.domain}" for r in order]
    ci = [r.net_ci_low for r in order]
    mg = [r.margin for r in order]
    y = np.arange(len(order))
    color = {"CONFIRM": "seagreen", "FAIL": "indianred", "INCONCLUSIVE": "gold",
             "INDETERMINATE": "gray"}
    colors = [color.get(verdicts[(r.instrument, r.domain)], "gray") for r in order]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(y, ci, color=colors)
    ax.plot(mg, y, "ks", ms=5, label="EXP-090/094 margin (MDE)")
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(y, labels, fontsize=7)
    ax.set_xlabel("net ci_low_1s (ATR units)")
    ax.set_title("EXP-093 TEST net ci_low_1s vs 0 and vs margin\n"
                 "(green=CONFIRM red=FAIL gold=INCONCLUSIVE)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "test_net_ci_low_vs_thresholds.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_confirm_map(results: list[CellTest], verdicts: dict[tuple[str, str], str]) -> None:
    instruments = sorted({r.instrument for r in results})
    domains = ["1h", "4h"]
    code = {"CONFIRM": 3, "FAIL": 1, "INCONCLUSIVE": 2, "INDETERMINATE": 0}
    arr = np.full((len(instruments), len(domains)), np.nan)
    for r in results:
        arr[instruments.index(r.instrument), domains.index(r.domain)] = \
            code.get(verdicts[(r.instrument, r.domain)], np.nan)
    fig, ax = plt.subplots(figsize=(4.5, 7))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlGn", vmin=0, vmax=3)
    ax.set_xticks(range(len(domains)), domains)
    ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
    for i in range(len(instruments)):
        for j in range(len(domains)):
            v = arr[i, j]
            if not np.isnan(v):
                ax.text(j, i, verdicts[(instruments[i], domains[j])][:4], ha="center", va="center",
                        fontsize=6)
    ax.set_title("EXP-093 per-stratum TEST verdict", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.05)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "confirm_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_train_vs_test(results: list[CellTest], train_ref: dict[str, dict[str, float]]) -> None:
    order = _ordered(results)
    labels = [f"{r.instrument}-{r.domain}" for r in order]
    train_ci = [train_ref.get(f"{r.instrument}-{r.domain}", {}).get("train_net_ci_low", np.nan)
                for r in order]
    test_ci = [r.net_ci_low for r in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, train_ci, 0.4, label="TRAIN net ci_low (EXP-092)", color="steelblue")
    ax.bar(x + 0.2, test_ci, 0.4, label="TEST net ci_low (EXP-093)", color="darkorange")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, labels, rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("net ci_low_1s (ATR)")
    ax.set_title("EXP-093 TRAIN vs TEST net ci_low (selection-overlap / shrinkage honesty)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "train_vs_test_ci_low.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_boot_inputs(results: list[CellTest]) -> None:
    order = _ordered(results)
    labels = [f"{r.instrument}-{r.domain}" for r in order]
    means = [r.net_mean for r in order]
    medians = [r.net_median for r in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, means, 0.4, label="net mean (ATR)", color="steelblue")
    ax.bar(x + 0.2, medians, 0.4, label="net median (ATR)", color="darkorange")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, labels, rotation=40, ha="right", fontsize=7)
    ax.set_title("EXP-093 TEST net mean vs median per cell (binding gate = mean; median = shape)",
                 fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "test_mean_vs_median.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def experiment_verdict(verdicts: dict[tuple[str, str], str], determinism: dict[str, Any]) -> str:
    """G-021 routing readout (the adjudicated G-021 verdict is written separately at the gate review)."""
    if not determinism["determinism_pass"]:
        return "HALT_NON_DETERMINISM"
    vals = set(verdicts.values())
    if "CONFIRM" in vals:
        return "TEST_CONFIRMED"                           # >= 1 cell CONFIRMS -> routes G-021 TRADABLE
    if vals <= {"FAIL", "INDETERMINATE"}:
        return "TEST_NOT_CONFIRMED"                       # every powered cell FAILS -> NOT_TRADABLE
    return "TEST_INCONCLUSIVE"                            # some cell power-limited / spans zero


def run(limit: int | None = None) -> dict[str, Any]:
    """One-shot TEST confirmation of EXIT-RCT on the 11 carried cells (analysis-TEST stratum)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cells, margins = load_carried_cells()
    if limit:
        cells = cells[:limit]
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    for instr, _dom in cells:
        if instr not in files:
            raise FileNotFoundError(f"no INFR-003 file for {instr}")
    by_cell: dict[tuple[str, str], CellTest] = {}
    for cell in tqdm(cells, desc="carried cells (TEST)", unit="cell", dynamic_ncols=True):
        t0 = time.perf_counter()
        by_cell[cell] = compute_cell(cell, files[cell[0]], margins[cell])
        LOGGER.info("cell %s-%s done in %.1fs (n_resolved=%d, net_ci_low=%.4f, boot_p=%.4f)",
                    cell[0], cell[1], time.perf_counter() - t0, by_cell[cell].n_resolved,
                    by_cell[cell].net_ci_low, by_cell[cell].boot_p)
    results = [by_cell[c] for c in cells]
    pvals = {c: by_cell[c].boot_p for c in cells}
    adj = holm_adjust(pvals)
    verdicts = {c: adjudicate(by_cell[c], adj[c]) for c in cells}
    determinism = determinism_replay(by_cell, files, margins)
    verdict = experiment_verdict(verdicts, determinism)
    train_ref = load_train_reference()
    write_outputs(results, adj, verdicts, train_ref)
    make_plots(results, adj, verdicts, train_ref)
    meta = _build_metadata(cells, results, adj, verdicts, determinism, verdict)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(results, adj, verdicts, verdict, determinism)
    return meta


def _build_metadata(cells: list[tuple[str, str]], results: list[CellTest],
                    adj: dict[tuple[str, str], float], verdicts: dict[tuple[str, str], str],
                    determinism: dict[str, Any], verdict: str) -> dict[str, Any]:
    n_confirm = sum(1 for v in verdicts.values() if v == "CONFIRM")
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "021", "family": "CF-MR-001", "hyp": "HYP-002",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "experiment_verdict": verdict,
        "master_seed": MASTER_SEED, "surviving_exit": ARM,
        "carried_set_decision": "D0-amendment-006 (all 11 EXP-092 SEQUENCE_PASS cells; Holm-11)",
        "n_carried_cells": len(cells), "carried_cells": [f"{i}-{d}" for i, d in cells],
        "n_confirm": n_confirm,
        "verdict_counts": {v: sum(1 for x in verdicts.values() if x == v)
                           for v in sorted(set(verdicts.values()))},
        "holm": {"method": "holm-bonferroni", "alpha": HOLM_ALPHA, "sided": "one",
                 "family_size": int(sum(1 for r in results if np.isfinite(r.boot_p))),
                 "margin": "per-cell EXP-090/094 MDE (1h 0.0125 / 4h 0.025 ATR)"},
        "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA, "z_one_sided": 1.645,
        "test_rule": ("CONFIRM iff Holm-adj p <= 0.05 AND net ci_low_1s > margin; "
                      "else FAIL / INCONCLUSIVE_SPANS_ZERO (D6/4c)"),
        "cost_model": "EXP-085 CONSERVATIVE RT (D0-amendment-003 Phase-021 table); F=0",
        "cost_rt_bps": MR_COST_RT_BPS, "fin_bps_day": FIN_BPS_DAY, "cost_table_hash": cost_table_hash(),
        "determinism": determinism,
        "real_fade_outcomes_resolved": True,
        "stratum": "analysis-TEST (last 30% of the first-70% analysis set; holdout never loaded)",
        "holdout_untouched": True, "counted_test_reads": len(cells), "candidate_slots": 0,
        "ledger_note": ("each carried (instrument, domain) stratum spends 1 counted TEST read (0->1); "
                        "cap 2/stratum; recorded in test-read-ledger.md in the same change as the result"),
        "upstream": {"exp090_member_map": str(EXP090_MEMBER_MAP), "exp091_screen": str(EXP091_SCREEN),
                     "exp094_readiness": str(EXP094_READINESS), "exp092_candidate": str(EXP092_CANDIDATE)},
    }


def _log_summary(results: list[CellTest], adj: dict[tuple[str, str], float],
                 verdicts: dict[tuple[str, str], str], verdict: str,
                 determinism: dict[str, Any]) -> None:
    n_confirm = sum(1 for v in verdicts.values() if v == "CONFIRM")
    LOGGER.info("EXP-093 verdict=%s | CONFIRM %d/%d | det=%s | holdout_untouched=True counted_reads=%d",
                verdict, n_confirm, len(results), determinism["determinism_pass"], len(results))
    for r in _ordered(results):
        k = (r.instrument, r.domain)
        LOGGER.info("  %-12s n=%5d net_ci_low=%+.4f margin=%.4f holm_p=%.4f -> %s",
                    f"{r.instrument}-{r.domain}", r.n_resolved, r.net_ci_low, r.margin,
                    adj[k], verdicts[k])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-093 one-shot TEST confirmation (analysis-TEST stratum)")
    ap.add_argument("--limit", type=int, default=None, help="limit carried cells (smoke test)")
    args = ap.parse_args()
    meta = run(limit=args.limit)
    print(f"EXP-093 complete: verdict={meta['experiment_verdict']} "
          f"CONFIRM={meta['n_confirm']}/{meta['n_carried_cells']} "
          f"counts={meta['verdict_counts']} determinism={meta['determinism']['determinism_pass']} "
          f"holdout_untouched={meta['holdout_untouched']} counted_test_reads={meta['counted_test_reads']}")


if __name__ == "__main__":
    main()
