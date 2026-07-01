"""
Experiment EXP-010 — CF-MR-003 CONC-1 Track 1: form-2 limit-at-anchor MR-fade tradability screen.

PRICE-PRIMARY / analysis-only Python (L-01): this script NEVER regenerates a signal, anchor, edge,
or fill. The S5_SPREAD exec-grid-β anchor, the VR∧HL selector, the |z|≥2 extreme, the live-limit
entry, and the form-2 limit / horizon-market exits are all computed IN-ENGINE by
`StrategyHost/CrossDomainMrLimitModel.cs` and emitted to `data/strategy_runs/EXP-010/`. Here we only
(1) ingest + validate the emissions (holdout fence, causal-provenance columns), (2) ASSEMBLE the
per-bar realized NET bps series from the engine-emitted fills (entry limit, exit limit/market) with
intra-position mark-to-market (L-09), (3) adjudicate each cell under the FROZEN referee
(`referee_pstar.gate_stack_pstar` §10.3a q*=0.75 + E6 P*-gate) with per-instrument 1h cost (L-02),
(4) apply phase-Holm over the 5 distinct cells (L-03), and (5) confirm the T1 leak tripwire (the
phase-shifted-basket run in `data/strategy_runs/EXP-010-shuffle/`) collapses the edge.

Realized-bps assembly is NOT an edge module: it reads only emitted columns (Position, RealOpen,
EntryFillPrice, ExitFillPrice) — the same sanctioned pattern as
`xen.signals.ingestion.returns_and_positions_realized` (EXP-006), extended to a TWO-limit-leg
strategy (entry fill + exit fill). No `rct`-style favourable-index recompute exists (P-09 clean).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import polars as pl

from xen.referee_adaptive import ROUND_TRIP_COST_BPS_17
from xen.referee_pstar import gate_stack_pstar
from xen.referee_adaptive import adaptive_row
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout

# --------------------------------------------------------------------------- #
# Constants (frozen; member set = 5 distinct S5 exec-1h admitted cells — design §3)
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-010")

ROOT = Path(__file__).resolve().parents[4]
RUNS_LIVE = ROOT / "data" / "strategy_runs" / "EXP-010"
RUNS_SHUFFLE = ROOT / "data" / "strategy_runs" / "EXP-010-shuffle"
RESULTS = Path(__file__).resolve().parents[1] / "results"

CELLS = ("AUDUSD", "GBPUSD", "NZDUSD", "US2000", "US500")
DOMAIN = "1h"
ALPHA = 0.05
N_BOOTSTRAP = 10_000
SEED = 20260701
STRATEGY = "cross_domain_mr_limit"

# Provenance columns the T2 causal trace + assembly require (design §7).
PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta")


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class CellVerdict:
    instrument: str
    n_bars: int
    n_entries: int
    n_episodes: int
    realized_mean_bps: float
    ci_low: float
    l1: bool
    l3: str
    admit: bool
    holm_admit: bool
    powered: bool


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def newest_run_dir(root: Path, instrument: str) -> Path:
    """Newest emitted run dir for a cell (`{strategy}_{symbol}_{domain}_{stamp}`)."""
    pattern = f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


# --------------------------------------------------------------------------- #
# Pure checks — causal-provenance validation (design §7 T2; assembly-side mirror of the audit)
# --------------------------------------------------------------------------- #
def validate_provenance(positions: pl.DataFrame, instrument: str) -> None:
    """Assert the emitted decision/fill columns are present and internally causal.

    Checks (raise on violation): all PROV_COLS present; fills lie within the emitting bar's real
    range (a limit that filled must be inside [Low, High]); post-warmup decision provenance is finite
    on active bars. This is the assembly-side sanity mirror; the binding T2 timestamp trace is the
    auditor's job.
    """
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            continue
        bad = fills.filter(
            (pl.col(leg) < pl.col("RealLow") - 1e-9) | (pl.col(leg) > pl.col("RealHigh") + 1e-9))
        if bad.height:
            raise ValueError(
                f"{instrument}: {bad.height} {leg} fills outside the emitting bar's [Low, High] "
                "(non-causal / mispriced fill)")


# --------------------------------------------------------------------------- #
# Pure computation — realized NET bps assembly from engine-emitted fills (L-09 MTM, L-02 cost)
# --------------------------------------------------------------------------- #
def assemble_realized_bps(
    positions: pl.DataFrame, *, cost_bps: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-bar (open-to-open) realized NET bps with exact entry+exit limit fills + intra-position MTM.

    Reads ONLY engine-emitted columns. For bar t (dropping the last, no next open):
      * held bar   -> pos[t] * log(Open[t+1]/Open[t]) * 1e4                       (MTM)
      * entry bar  -> pos[t] * log(Open[t+1]/EntryFillPrice[t]) * 1e4            (open from the fill)
      * exit  bar  -> pos[t] * log(ExitFillPrice[t]/Open[t]) * 1e4              (close at the fill)
      * entry==exit-> pos[t] * log(ExitFillPrice[t]/EntryFillPrice[t]) * 1e4     (round-trip in one bar)
    Round-trip `cost_bps` (L-02 binding) is charged once per entry (amortized B-convention, matching
    the frozen gate). Returns `(returns, positions_aligned, realized_bps)`, all length n-1.

    Causal-provenance: realized_bps[t] reads pos[t], Open[t], Open[t+1], and the fills placed before
    bar t opened (rested from t-1). No future bar is read.
    """
    df = positions.sort("SourceCloseTime")
    pos = df.get_column("Position").to_numpy().astype(float)
    op = df.get_column("RealOpen").to_numpy().astype(float)
    entry = df.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_ = df.get_column("ExitFillPrice").to_numpy().astype(float)
    n = len(pos)
    if n < 3:
        raise ValueError("too few emitted bars to assemble a realized series")

    next_open = op[1:]
    op = op[:-1]
    pos = pos[:-1]
    entry = entry[:-1]
    exit_ = exit_[:-1]
    has_entry = ~np.isnan(entry)
    has_exit = ~np.isnan(exit_)

    with np.errstate(divide="ignore", invalid="ignore"):
        open_price = np.where(has_entry, entry, op)                 # position opens at the entry fill
        close_price = np.where(has_exit, exit_, next_open)          # closes at the exit fill, else next open
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.where(pos != 0.0, gross, 0.0)
    gross = np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0)

    realized_bps = gross - cost_bps * has_entry.astype(float)       # one RT cost per entry
    market_returns = np.log(next_open / op)                        # open-to-open market ret (naive leg)
    market_returns = np.nan_to_num(market_returns, nan=0.0, posinf=0.0, neginf=0.0)
    return market_returns, pos, realized_bps


# --------------------------------------------------------------------------- #
# Adjudication — frozen referee (no referee module edited; L-12)
# --------------------------------------------------------------------------- #
def adjudicate(instrument: str, positions: pl.DataFrame) -> tuple[CellVerdict, dict, float]:
    """Route one cell's emitted realized series through the frozen P*-gate + adaptive row.

    Returns `(verdict, row, p_boot)`. `p_boot` is a one-sided bootstrap p for net>0, read from the
    referee's OWN frozen neutral-mean bootstrap distribution (`core["neutral_means"]`) — no referee
    edit — for the phase-Holm multiplicity control (L-03).
    """
    cost_bps = ROUND_TRIP_COST_BPS_17[instrument][DOMAIN]
    returns, pos, realized_bps = assemble_realized_bps(positions, cost_bps=cost_bps)
    core = gate_stack_pstar(
        returns, pos, realized_bps,
        domain=DOMAIN, cost_bps=cost_bps, n_bootstrap=N_BOOTSTRAP, seed=SEED)
    row = adaptive_row(core, alpha=ALPHA)
    legs = json.loads(row["leg_results"])
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    p_boot = float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")
    n_entries = int(np.sum(~np.isnan(
        positions.sort("SourceCloseTime").get_column("EntryFillPrice").to_numpy().astype(float))))
    verdict = CellVerdict(
        instrument=instrument,
        n_bars=positions.height,
        n_entries=n_entries,
        n_episodes=int(core.get("n_episodes", 0)),
        realized_mean_bps=float(np.mean(realized_bps[realized_bps != 0.0])
                                if np.any(realized_bps != 0.0) else 0.0),
        ci_low=float(row["ci_lower_bps"]),
        l1=bool(core["l1"]),
        l3=str(legs.get("L3_outcome", "NA")),
        admit=bool(row["passed"]),
        holm_admit=False,     # set by holm() below
        powered=bool(core["l1"] and core.get("n_episodes", 0) > 0),
    )
    return verdict, row, p_boot


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm–Bonferroni over the distinct cells (L-03). Cells without a finite p abstain (False)."""
    items = [(k, v) for k, v in pvals.items() if np.isfinite(v)]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen(root: Path, label: str) -> tuple[list[CellVerdict], dict]:
    """Ingest + validate + adjudicate the 5 cells under `root` (live or shuffle)."""
    verdicts: list[CellVerdict] = []
    rows: dict[str, dict] = {}
    pvals: dict[str, float] = {}
    for inst in CELLS:
        run = load_emitted_run(newest_run_dir(root, inst))
        assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
        validate_provenance(run.positions, inst)
        v, row, p_boot = adjudicate(inst, run.positions)
        verdicts.append(v)
        rows[inst] = row
        pvals[inst] = p_boot
        logger.info("[%s] %s: entries=%d episodes=%d realized_mean=%.2fbps ci_low=%.2f L1=%s L3=%s p=%.4f",
                    label, inst, v.n_entries, v.n_episodes, v.realized_mean_bps, v.ci_low, v.l1, v.l3, p_boot)
    holm_map = holm(pvals)
    for v in verdicts:
        v.holm_admit = bool(holm_map.get(v.instrument, False) and v.admit)
    return verdicts, {"rows": rows, "pvals": pvals, "holm": holm_map}


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-010 CONC-1 T1 — 5 distinct S5 exec-1h cells; frozen referee domain=1h.")

    live, live_detail = screen(RUNS_LIVE, "LIVE")
    n_powered = sum(v.powered for v in live)
    n_admit = sum(v.holm_admit for v in live)

    tripwire_ok = None
    shuffle: list[CellVerdict] = []
    if RUNS_SHUFFLE.exists() and any(RUNS_SHUFFLE.iterdir()):
        shuffle, _ = screen(RUNS_SHUFFLE, "SHUFFLE")
        # Tripwire passes iff the phase-shifted edge collapses on the LIVE-admitting cells.
        admit_insts = {v.instrument for v in live if v.holm_admit}
        surviving = [v.instrument for v in shuffle if v.instrument in admit_insts and v.admit]
        tripwire_ok = (len(surviving) == 0)
        logger.info("Leak tripwire: surviving-under-shuffle=%s -> %s",
                    surviving, "PASS" if tripwire_ok else "FAIL (leak -> REJECT)")
    else:
        logger.warning("Shuffle runs not present yet — run EXP-010-shuffle before booking a verdict.")

    # Predeclared interpretation (design §8): TRADABLE-ON-TRAIN iff >=50% of powered cells Holm-ADMIT
    # AND the tripwire collapses the edge.
    if tripwire_ok is False:
        outcome = "REJECT_LEAK"
    elif n_powered == 0:
        outcome = "UNPOWERED"
    elif n_admit / max(n_powered, 1) >= 0.5 and tripwire_ok:
        outcome = "TRADABLE_ON_TRAIN"
    elif tripwire_ok is None:
        outcome = "PENDING_TRIPWIRE"
    else:
        outcome = "NOT_TRADABLE"

    result = {
        "experiment": "EXP-010",
        "arm": "T1_S5_exec1h",
        "cells": [asdict(v) for v in live],
        "n_powered": n_powered,
        "n_holm_admit": n_admit,
        "tripwire_pass": tripwire_ok,
        "shuffle_cells": [asdict(v) for v in shuffle],
        "outcome": outcome,
        "holm": live_detail["holm"],
        "pvals": live_detail["pvals"],
    }
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("VERDICT: %s | powered=%d admit=%d tripwire=%s -> results/verdict.json",
                outcome, n_powered, n_admit, tripwire_ok)


if __name__ == "__main__":
    main()
