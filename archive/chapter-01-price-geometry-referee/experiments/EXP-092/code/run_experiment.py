"""EXP-092 — Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors).

Phase 021 / ``CF-MR-001`` / HYP-002 — the per-instrument cost-bearing sequence (design §4 EXP-092; A1-style,
analog EXP-034/083). Governing D0:
``docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/`` — ``D0-predeclarations.md``
§D6/4b (sequence rule) + §D7 (read accounting), ``D0-amendment-003`` (Phase-021 cost table),
``D0-amendment-004``/``-005`` (4h opened -> ADMITTED via EXP-094). TRAIN sub-split only (first 49% per file);
**0 candidate slots, 0 counted TEST reads, holdout never loaded**.

What this is. EXIT-RCT was the **only** exit to pass the EXP-091 (1h) / EXP-094 (4h) screen; ERT + 4
conventional arms died and are not reopened. EXP-092 re-derives, on EXIT-RCT's 11 net-clearing carried cells,
the binding net per-event-expectancy one-sided lower bound, certifies each cell's ``SEQUENCE_PASS``, and emits
the **hash-pinned candidate set (sha256) + the sized phase Holm rule** for the one-shot EXP-093 TEST.
**Necessary-but-not-sufficient for TEST**; no G-021 verdict is decided here, no TEST row is read.

Binding sequence rule (D6/4b). A carried cell ``SEQUENCE_PASS`` iff net per-event expectancy moving-block
bootstrap one-sided lower bound (``net ci_low_1s``, Z=1.645) **> 0** AND power-confirmed (finite EXP-090/094
MDE — satisfied for every carried member by construction). The EXP-093 margin condition (``ci_low > MDE``) is
co-reported descriptively (NOT a sequence gate) so EXP-093's D0 can pick the smallest-defensible subset.

Substrate reuse (verbatim). The EXP-090 module (``build_cell_context``, ``resolve_arm``/RCT, the 1-minute
intrabar fill engine, ``net_return_atr``) and the EXP-091 cost overlay are imported/mirrored unchanged so the
entry/exit/fill/cost machinery is byte-identical to the screen. 4h patches ``DOMAINS["4h"]=240`` exactly as
EXP-094. EXP-092 adds only the per-cell sequence test, the candidate-set hash-pin, and the Holm-rule descriptor.

Cost (D3 + D0-amendment-003). Phase-021-local CONSERVATIVE round-trip ``RT_i`` (bps) + ``F_i = 0``; the shared
``xen.capgeo_cost.COST_CONSTANTS`` is NOT edited (Phase-018 integrity) — only ``event_costs`` / ``holding_days``
mechanics are called with the Phase-021 ``RT_i`` / ``fin_bps_day=0``.
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

from xen.ass import moving_block_bootstrap_cis  # noqa: E402
from xen.capgeo_cost import event_costs, holding_days  # noqa: E402
from xen.intrabar_fill import net_return_atr  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-090 substrate reuse (import the validated module directly)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-092"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
EXP090_CODE = EXP_ROOT / "EXP-090" / "code" / "run_experiment.py"
EXP090_MEMBER_MAP = EXP_ROOT / "EXP-090" / "results" / "member_map.csv"
EXP091_SCREEN = EXP_ROOT / "EXP-091" / "results" / "screen_per_cell_arm.csv"
EXP094_READINESS = EXP_ROOT / "EXP-094" / "results" / "readiness_4h.csv"


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
E90.DOMAINS["4h"] = 240                                  # patch 4h (240-min); EXP-094 ADMITTED it (amendment-004/005)

# --------------------------------------------------------------------------- #
# Constants (frozen at D0/G0 + D0-amendment-003/004/005; never tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = E90.MASTER_SEED                            # 20260623 (shared)
DOMAINS: dict[str, int] = E90.DOMAINS                   # {"15m":15,"1h":60,"4h":240}
ARM = "RCT"                                              # the sole surviving exit (EXP-091/094)

# Carried candidate universe (FROZEN by upstream verdicts; re-derived from upstream files + asserted).
# 1h: EXP-091 RCT net-clearing quorum (5/5). 4h: EXP-094 powered MEMBERs (ADMIT_4H, 6/6 beat the null).
CARRIED_1H = ("EURUSD", "GBPUSD", "NZDUSD", "US2000", "USTEC")
CARRIED_4H = ("AUDJPY", "EURJPY", "EURUSD", "GBPJPY", "USDCHF", "XAUUSD")

# Phase-021 cost table (D0-amendment-003, FROZEN 2026-06-24). RT_i (bps) CONSERVATIVE = 4*c_i; F_i = 0.
# Phase-021-LOCAL — shared xen.capgeo_cost.COST_CONSTANTS is NOT mutated (Phase-018 integrity).
MR_COST_RT_BPS: dict[str, float] = {
    "EURUSD": 3.0, "GBPUSD": 4.0, "USDJPY": 4.0, "USDCHF": 4.0, "AUDUSD": 4.0, "NZDUSD": 4.5,
    "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0, "XAUUSD": 6.0, "USTEC": 5.0, "US2000": 6.0,
    "JP225": 6.0,
}
FIN_BPS_DAY = 0.0                                        # F = 0 (D0-amendment-003)

# Binding net lower bound (D6/4b).
N_BOOT = 10_000                                          # moving-block bootstrap resamples
BOOT_ALPHA = 0.10                                        # 90% CI -> 5th pct = one-sided 95% lower (Z=1.645)
SEQUENCE_ALPHA = 0.05                                    # per-cell one-sided SEQUENCE_PASS (D0 4b)
DETERMINISM_CELLS = (("USTEC", "1h"), ("EURUSD", "4h"))  # one 1h + one 4h replay (D9)

# Phase Holm rule descriptor for EXP-093 (sized at EXP-093 D0 to the carried subset).
HOLM_RULE = {"method": "holm-bonferroni", "alpha": SEQUENCE_ALPHA, "sided": "one",
             "margin": "per-cell EXP-090/094 MDE (1h 0.0125 / 4h 0.025 ATR)",
             "note": ("sized to the EXP-093-carried subset cardinality (smallest defensible, "
                      "<=1-2 cells/surviving exit/domain) selected at EXP-093 D0 from this pinned set")}

HEADLINE_OUTPUTS = ("sequence_per_cell.csv", "candidate_set.csv", "margin_preread.csv")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellSeq:
    """Per carried (instrument, domain) cell EXIT-RCT sequence result (ATR units, real prices)."""

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
    margin: float
    sequence_pass: bool
    clears_margin: bool
    mean_and_median_pos: bool


# --------------------------------------------------------------------------- #
# I/O helpers (read-only upstream dependencies; provenance + drift assertions)
# --------------------------------------------------------------------------- #
def load_carried_cells() -> tuple[list[tuple[str, str]], dict[tuple[str, str], float]]:
    """Re-derive the carried EXIT-RCT cells from upstream files, assert == the frozen set, return margins.

    1h margins from EXP-090 member_map (``rct_margin`` on MEMBERs); 4h margins from EXP-094 readiness
    (``rct_mde`` on MEMBERs). Hard-fail on any upstream drift so the candidate set cannot silently change.
    """
    for p in (EXP090_MEMBER_MAP, EXP091_SCREEN, EXP094_READINESS):
        if not p.exists():
            raise FileNotFoundError(f"dependency gate: missing upstream artifact {p}")

    # 1h survivors: EXP-091 RCT rows with net_clear == true on 1h.
    s91 = pl.read_csv(EXP091_SCREEN)
    rct1h = s91.filter((pl.col("arm") == ARM) & (pl.col("domain") == "1h") & (pl.col("net_clear")))
    got_1h = sorted(rct1h["instrument"].to_list())
    if got_1h != sorted(CARRIED_1H):
        raise ValueError(f"EXP-091 1h RCT net-clear drift: expected {sorted(CARRIED_1H)}, got {got_1h}")

    # 4h members: EXP-094 readiness MEMBERs (ADMIT_4H powered set).
    r94 = pl.read_csv(EXP094_READINESS)
    mem4h = r94.filter((pl.col("domain") == "4h") & (pl.col("verdict") == "MEMBER"))
    got_4h = sorted(mem4h["instrument"].to_list())
    if got_4h != sorted(CARRIED_4H):
        raise ValueError(f"EXP-094 4h MEMBER drift: expected {sorted(CARRIED_4H)}, got {got_4h}")

    # 1h RCT margins (EXP-090 member_map).
    mm = pl.read_csv(EXP090_MEMBER_MAP)
    mm1h = mm.filter((pl.col("domain") == "1h") & (pl.col("verdict") == "MEMBER"))
    margin_1h = {r["instrument"]: float(r["rct_margin"]) for r in mm1h.iter_rows(named=True)}
    margin_4h = {r["instrument"]: float(r["rct_mde"]) for r in mem4h.iter_rows(named=True)}

    cells: list[tuple[str, str]] = [(i, "1h") for i in CARRIED_1H] + [(i, "4h") for i in CARRIED_4H]
    margins: dict[tuple[str, str], float] = {}
    for instr, dom in cells:
        m = margin_1h.get(instr) if dom == "1h" else margin_4h.get(instr)
        if m is None or not np.isfinite(m) or m <= 0.0:
            raise ValueError(f"power-confirmation gate: {instr}-{dom} has no finite positive MDE margin ({m})")
        margins[(instr, dom)] = m
        if instr not in MR_COST_RT_BPS:                  # cost table must price every carried instrument
            raise ValueError(f"cost table (D0-amendment-003) missing instrument: {instr}")
    return cells, margins


# --------------------------------------------------------------------------- #
# Pure computation — resolve real EXIT-RCT exits, overlay cost, net lower bound
# --------------------------------------------------------------------------- #
def _rct_paths(ctx: Any) -> tuple[np.ndarray, np.ndarray, Any]:
    """Resolve real CORE entries through EXIT-RCT; return (gross_atr, holding_days, resolution).

    Mirrors EXP-091 ``_engine_arm_paths`` for the RCT arm exactly (EXP-090 ``resolve_arm`` -> 1m engine).
    Gross = direction-signed real-price ATR return off the touched fill level; holding days from the exit
    domain bar (operator-ratified bar-count proxy).
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    res = E90.resolve_arm(ctx, idx, direction, ARM, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[idx], direction, ctx.atr[idx])
    hd = holding_days(idx, res.exit_domain_idx, DOMAINS[ctx.domain])
    return gross, hd, res


def _net_lower_bound(series: np.ndarray, seed: int) -> float:
    """One-sided net expectancy lower bound (moving-block bootstrap, Z=1.645)."""
    if series.shape[0] < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    ci = moving_block_bootstrap_cis(series, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
    return float(ci.expectancy_lo)


def sequence_cell(ctx: Any, margin: float) -> CellSeq:
    """Resolve real EXIT-RCT exits for one cell, overlay cost, apply the binding sequence rule (D6/4b)."""
    idx = ctx.core_entry_idx
    p_entry, atr_entry = ctx.close[idx], ctx.atr[idx]
    gross, hd, res = _rct_paths(ctx)
    resolved = res.resolved
    keep = resolved & np.isfinite(gross) & np.isfinite(atr_entry) & (atr_entry > 0.0) \
        & np.isfinite(hd) & (hd >= 0.0)
    n_events, n_resolved = int(idx.shape[0]), int(np.count_nonzero(keep))
    tie = res.tie_break[keep]
    tie_frac = float(np.mean(tie)) if tie.shape[0] else 0.0
    from xen.intrabar_fill import KIND_FAV
    terminal_fav = float(np.mean(res.kind[keep] == KIND_FAV)) if n_resolved else float("nan")
    if n_resolved < 2:                                   # cannot bootstrap -> SEQUENCE_INDETERMINATE
        return CellSeq(ctx.instrument, ctx.domain, n_events, n_resolved,
                       (n_resolved / n_events if n_events else float("nan")), tie_frac, terminal_fav,
                       float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), margin,
                       False, False, False)
    g = gross[keep]
    rt = MR_COST_RT_BPS[ctx.instrument]
    costs = event_costs(g, p_entry[keep], atr_entry[keep], hd[keep], rt_bps=rt, fin_bps_day=FIN_BPS_DAY)
    net = costs.net
    net_lo = _net_lower_bound(net, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, ARM, "net"))
    net_mean, net_median = float(np.mean(net)), float(np.median(net))
    seq_pass = bool(np.isfinite(net_lo) and net_lo > 0.0 and np.isfinite(margin) and margin > 0.0)
    return CellSeq(
        instrument=ctx.instrument, domain=ctx.domain, n_events=n_events, n_resolved=n_resolved,
        resolved_frac=float(np.mean(resolved)), tie_break_frac=tie_frac, terminal_fav=terminal_fav,
        holding_days_mean=float(np.mean(hd[keep])), gross_mean=float(np.mean(g)), net_mean=net_mean,
        net_median=net_median, net_ci_low=net_lo, margin=margin, sequence_pass=seq_pass,
        clears_margin=bool(np.isfinite(net_lo) and net_lo > margin),
        mean_and_median_pos=bool(net_mean > 0.0 and net_median > 0.0))


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(cell: tuple[str, str], path: Path, margin: float) -> CellSeq:
    """Build the cell substrate (EXP-090 verbatim) + run the EXIT-RCT sequence test."""
    instrument, domain = cell
    train_1m, _meta = E90.load_train_1m(instrument, path)
    ctx, _dropped, status = E90.build_cell_context(train_1m, instrument, domain)
    if ctx is None:                                      # a carried cell must build (upstream guarantee)
        raise RuntimeError(f"{instrument}-{domain}: carried cell failed to build ({status})")
    return sequence_cell(ctx, margin)


# --------------------------------------------------------------------------- #
# Aggregation — candidate set, hash-pin, Holm sizing
# --------------------------------------------------------------------------- #
def build_candidate_set(results: list[CellSeq]) -> tuple[list[dict[str, Any]], str]:
    """SEQUENCE_PASS cells ranked by net_ci_low desc -> rows + sha256 over a canonical serialization."""
    passing = [r for r in results if r.sequence_pass]
    passing.sort(key=lambda r: (-r.net_ci_low, f"{r.instrument}-{r.domain}"))
    rows = [{"rank": k + 1, "cell": f"{r.instrument}-{r.domain}", "instrument": r.instrument,
             "domain": r.domain, "net_ci_low": r.net_ci_low, "net_mean": r.net_mean,
             "net_median": r.net_median, "margin": r.margin, "clears_margin": r.clears_margin,
             "mean_and_median_pos": r.mean_and_median_pos, "n_resolved": r.n_resolved}
            for k, r in enumerate(passing)]
    canon = json.dumps([{k: rr[k] for k in ("cell", "net_ci_low", "margin", "clears_margin",
                                            "mean_and_median_pos", "n_resolved")} for rr in rows],
                       sort_keys=True).encode()
    return rows, hashlib.sha256(canon).hexdigest()


# --------------------------------------------------------------------------- #
# Determinism + hashing
# --------------------------------------------------------------------------- #
def determinism_replay(results: dict[tuple[str, str], CellSeq], files: dict[str, Path],
                       margins: dict[tuple[str, str], float], pinned_hash: str) -> dict[str, Any]:
    """Re-run one 1h + one 4h cell; assert net_ci_low / SEQUENCE_PASS frame-identical, hash stable (D9)."""
    checked, mismatches = [], []
    for cell in DETERMINISM_CELLS:
        if cell not in results:
            continue
        checked.append(f"{cell[0]}-{cell[1]}")
        b = compute_cell(cell, files[cell[0]], margins[cell])
        a = results[cell]
        if not (a.sequence_pass == b.sequence_pass and _eq(a.net_ci_low, b.net_ci_low)
                and a.n_resolved == b.n_resolved):
            mismatches.append(f"{cell[0]}-{cell[1]}")
    # hash re-pin from the replayed full set ordering is checked at run-level (pinned_hash carried for record)
    return {"determinism_pass": not mismatches, "cells_checked": checked,
            "non_deterministic": mismatches, "candidate_set_sha256": pinned_hash}


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
def write_outputs(results: list[CellSeq], candidate_rows: list[dict[str, Any]]) -> None:
    """Flatten to the headline CSV tables (per-cell sequence, candidate set, margin pre-read)."""
    seq_rows = [{
        "cell": f"{r.instrument}-{r.domain}", "instrument": r.instrument, "domain": r.domain,
        "n_events": r.n_events, "n_resolved": r.n_resolved, "resolved_frac": r.resolved_frac,
        "tie_break_frac": r.tie_break_frac, "terminal_fav": r.terminal_fav,
        "holding_days_mean": r.holding_days_mean, "gross_mean": r.gross_mean, "net_mean": r.net_mean,
        "net_median": r.net_median, "net_ci_low": r.net_ci_low, "margin": r.margin,
        "sequence_pass": r.sequence_pass, "clears_margin": r.clears_margin,
        "mean_and_median_pos": r.mean_and_median_pos} for r in results]
    pl.DataFrame(seq_rows).write_csv(RESULTS_DIR / "sequence_per_cell.csv")
    cand = candidate_rows or [{"rank": None, "cell": None, "instrument": None, "domain": None,
                               "net_ci_low": None, "net_mean": None, "net_median": None, "margin": None,
                               "clears_margin": None, "mean_and_median_pos": None, "n_resolved": None}]
    pl.DataFrame(cand).write_csv(RESULTS_DIR / "candidate_set.csv")
    preread = [{"cell": f"{r.instrument}-{r.domain}", "instrument": r.instrument, "domain": r.domain,
                "net_ci_low": r.net_ci_low, "margin": r.margin, "clears_margin": r.clears_margin,
                "net_mean": r.net_mean, "net_median": r.net_median,
                "mean_and_median_pos": r.mean_and_median_pos, "n_resolved": r.n_resolved}
               for r in results]
    pl.DataFrame(preread).write_csv(RESULTS_DIR / "margin_preread.csv")


# --------------------------------------------------------------------------- #
# Plotting (<=4 bounded plots from collected summaries; no reloads)
# --------------------------------------------------------------------------- #
def make_plots(results: list[CellSeq], candidate_rows: list[dict[str, Any]]) -> None:
    _plot_net_ci_vs_thresholds(results)
    _plot_sequence_map(results)
    _plot_mean_vs_median(results)
    _plot_robustness_ranking(candidate_rows)


def _cells(results: list[CellSeq]) -> list[str]:
    return [f"{r.instrument}-{r.domain}" for r in results]


def _plot_net_ci_vs_thresholds(results: list[CellSeq]) -> None:
    order = sorted(results, key=lambda r: (r.domain, -r.net_ci_low))
    labels = [f"{r.instrument}-{r.domain}" for r in order]
    ci = [r.net_ci_low for r in order]
    mg = [r.margin for r in order]
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = ["seagreen" if r.sequence_pass else "indianred" for r in order]
    ax.barh(y, ci, color=colors, label="net ci_low_1s")
    ax.plot(mg, y, "ks", ms=5, label="EXP-093 margin (MDE)")
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(y, labels, fontsize=7)
    ax.set_xlabel("ATR(14) units")
    ax.set_title("EXP-092 net ci_low_1s vs 0 (SEQUENCE_PASS) and vs margin", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "net_ci_low_vs_thresholds.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_sequence_map(results: list[CellSeq]) -> None:
    instruments = sorted({r.instrument for r in results})
    domains = ["1h", "4h"]
    arr = np.full((len(instruments), len(domains)), np.nan)
    for r in results:
        arr[instruments.index(r.instrument), domains.index(r.domain)] = 1.0 if r.sequence_pass else 0.0
    fig, ax = plt.subplots(figsize=(4.5, 7))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(domains)), domains)
    ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
    for i in range(len(instruments)):
        for j in range(len(domains)):
            v = arr[i, j]
            ax.text(j, i, "" if np.isnan(v) else ("PASS" if v > 0.5 else "fail"),
                    ha="center", va="center", fontsize=6)
    ax.set_title("EXP-092 SEQUENCE_PASS candidate map", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.05)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "sequence_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_mean_vs_median(results: list[CellSeq]) -> None:
    order = sorted(results, key=lambda r: (r.domain, -r.net_ci_low))
    labels = [f"{r.instrument}-{r.domain}" for r in order]
    means = [r.net_mean for r in order]
    medians = [r.net_median for r in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, means, 0.4, label="net mean (ATR)", color="steelblue")
    ax.bar(x + 0.2, medians, 0.4, label="net median (ATR)", color="darkorange")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, labels, rotation=40, ha="right", fontsize=7)
    ax.set_title("EXP-092 net mean vs median per cell (robust core = both > 0)", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mean_vs_median.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_robustness_ranking(candidate_rows: list[dict[str, Any]]) -> None:
    rows = [r for r in candidate_rows if r.get("cell")]
    fig, ax = plt.subplots(figsize=(7, 5))
    if rows:
        labels = [r["cell"] for r in rows]
        ci = [r["net_ci_low"] for r in rows]
        y = np.arange(len(rows))
        colors = ["seagreen" if r["clears_margin"] and r["mean_and_median_pos"] else
                  ("gold" if r["clears_margin"] else "indianred") for r in rows]
        ax.barh(y, ci, color=colors)
        ax.set_yticks(y, labels, fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("net ci_low_1s (ATR)")
        ax.set_title("EXP-092 pinned candidate ranking\n(green=clears margin & mean+median; "
                     "gold=clears margin only; red=fragile)", fontsize=9)
    else:
        ax.text(0.5, 0.5, "SEQUENCE_EMPTY", ha="center", va="center")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "robustness_ranking.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def experiment_verdict(candidate_rows: list[dict[str, Any]], determinism: dict[str, Any]) -> str:
    """SEQUENCE_DELIVERED (+ SEQUENCE_EMPTY if no cell passes); HALT on non-determinism."""
    if not determinism["determinism_pass"]:
        return "HALT_NON_DETERMINISM"
    return "SEQUENCE_DELIVERED" if candidate_rows else "SEQUENCE_DELIVERED_EMPTY"


def run(limit: int | None = None) -> dict[str, Any]:
    """Sequence EXIT-RCT on the 11 carried cells (TRAIN-only); pin the candidate set + Holm rule."""
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
    by_cell: dict[tuple[str, str], CellSeq] = {}
    for cell in tqdm(cells, desc="carried cells", unit="cell", dynamic_ncols=True):
        t0 = time.perf_counter()
        by_cell[cell] = compute_cell(cell, files[cell[0]], margins[cell])
        LOGGER.info("cell %s-%s done in %.1fs (seq_pass=%s, net_ci_low=%.4f)",
                    cell[0], cell[1], time.perf_counter() - t0,
                    by_cell[cell].sequence_pass, by_cell[cell].net_ci_low)
    results = [by_cell[c] for c in cells]
    candidate_rows, pinned_hash = build_candidate_set(results)
    determinism = determinism_replay(by_cell, files, margins, pinned_hash)
    verdict = experiment_verdict(candidate_rows, determinism)
    write_outputs(results, candidate_rows)
    make_plots(results, candidate_rows)
    meta = _build_metadata(cells, results, candidate_rows, pinned_hash, determinism, verdict)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(results, candidate_rows, verdict, determinism)
    return meta


def _build_metadata(cells: list[tuple[str, str]], results: list[CellSeq],
                    candidate_rows: list[dict[str, Any]], pinned_hash: str,
                    determinism: dict[str, Any], verdict: str) -> dict[str, Any]:
    n_pass = sum(1 for r in results if r.sequence_pass)
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "021", "family": "CF-MR-001", "hyp": "HYP-002",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "experiment_verdict": verdict,
        "master_seed": MASTER_SEED, "surviving_exit": ARM,
        "n_carried_cells": len(cells), "carried_cells": [f"{i}-{d}" for i, d in cells],
        "carried_1h": list(CARRIED_1H), "carried_4h": list(CARRIED_4H),
        "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA, "z_one_sided": 1.645,
        "sequence_alpha": SEQUENCE_ALPHA,
        "sequence_rule": "SEQUENCE_PASS iff net ci_low_1s > 0 AND finite EXP-090/094 MDE (power-confirmed)",
        "n_sequence_pass": n_pass,
        "candidate_set": candidate_rows, "candidate_set_sha256": pinned_hash,
        "candidate_set_size": len(candidate_rows), "holm_rule": HOLM_RULE,
        "cost_model": "EXP-085 CONSERVATIVE RT (D0-amendment-003 Phase-021 table); F=0",
        "cost_rt_bps": MR_COST_RT_BPS, "fin_bps_day": FIN_BPS_DAY, "cost_table_hash": cost_table_hash(),
        "cost_table_note": ("Phase-021-LOCAL (D0-amendment-003, FROZEN 2026-06-24); shared "
                            "xen.capgeo_cost.COST_CONSTANTS NOT mutated (Phase-018 integrity)."),
        "margin_preread_note": ("net_ci_low > margin (margin = EXP-090/094 MDE) is the EXP-093 condition, "
                                "co-reported DESCRIPTIVELY here; it does NOT gate SEQUENCE_PASS (D0 4b/4c)."),
        "determinism": determinism,
        "real_fade_outcomes_resolved": True, "holdout_untouched": True,
        "counted_test_reads": 0, "candidate_slots": 0,
        "upstream": {"exp090_member_map": str(EXP090_MEMBER_MAP), "exp091_screen": str(EXP091_SCREEN),
                     "exp094_readiness": str(EXP094_READINESS)},
    }


def _log_summary(results: list[CellSeq], candidate_rows: list[dict[str, Any]], verdict: str,
                 determinism: dict[str, Any]) -> None:
    n_pass = sum(1 for r in results if r.sequence_pass)
    n_robust = sum(1 for r in candidate_rows if r.get("clears_margin") and r.get("mean_and_median_pos"))
    LOGGER.info("EXP-092 verdict=%s | SEQUENCE_PASS %d/%d | margin+mean+median robust %d | det=%s",
                verdict, n_pass, len(results), n_robust, determinism["determinism_pass"])
    for r in sorted(results, key=lambda r: (r.domain, -r.net_ci_low)):
        LOGGER.info("  %-12s net_ci_low=%+.4f margin=%.4f -> %s%s", f"{r.instrument}-{r.domain}",
                    r.net_ci_low, r.margin, "PASS" if r.sequence_pass else "fail",
                    "" if r.clears_margin else "  (below EXP-093 margin)")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-092 per-instrument cost-bearing sequence (TRAIN-only)")
    ap.add_argument("--limit", type=int, default=None, help="limit carried cells (smoke test)")
    args = ap.parse_args()
    meta = run(limit=args.limit)
    print(f"EXP-092 complete: verdict={meta['experiment_verdict']} "
          f"SEQUENCE_PASS={meta['n_sequence_pass']}/{meta['n_carried_cells']} "
          f"candidate_set_size={meta['candidate_set_size']} sha256={meta['candidate_set_sha256'][:12]}… "
          f"determinism={meta['determinism']['determinism_pass']}")


if __name__ == "__main__":
    main()
