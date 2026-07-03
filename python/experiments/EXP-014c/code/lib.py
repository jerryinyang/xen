"""
EXP-014c — CF-MR-004/HYP-004 (lean bracket exit-set) shared analysis library (ANALYSIS-ONLY, L-01/P-09).

amendment-004: 4h only, single-leg, S8 only. EXIT axis E0/E1/E2/E3; E0 (moving-mean baseline) is the
REUSED EXP-014b 4h emission set (read-only); E1-E3 are the EXP-014c native runs. Reentry
{none,allow,extend} + z* {2.0,1.5} retained as characterisation axes. NEVER regenerates a
signal/anchor/edge/fill — every entry/exit/fill is engine-realized and read from
data/strategy_runs/EXP-014{b,c}-*/. Carries the audited post-C1/C2 EXP-014b machinery: engine-realized
per-bar NET bps assembly (intra-position MTM L-09; RT cost once/entry L-02, frozen per-domain cost
map), frozen referee wrappers (referee_pstar.gate_stack_pstar — never tuned, L-12), Holm, bootstrap.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.referee_adaptive import adaptive_cost_bps_for, adaptive_row          # noqa: E402
from xen.referee_calibration import DOMAIN_SPECS                              # noqa: E402
from xen.referee_pstar import gate_stack_pstar                               # noqa: E402
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen) + run map
# --------------------------------------------------------------------------- #
DOMAIN = "4h"                                   # HYP-004: 4h only (1h retired — 014b leak)
ALPHA = 0.05
N_BOOTSTRAP = 10_000
SEED = 20260703
STRATEGY = "cross_instrument_spread_mr"
DATA_ROOT = ROOT / "data" / "strategy_runs"

FX = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD")
IDX = ("USTEC", "US500", "US2000", "JP225")
S8_CELLS = FX + IDX

EXITS = ("e0", "e1", "e2", "e3")                # moving | frozen_tp | frozen_tp_sl | bracket
ARMS = ("none", "allow", "extend")
ZSTARS = {"z20": 2.0, "z15": 1.5}
PRIMARY = ("e3", "none", "z20")                  # binding family
PRIMARY_CELLS = ("JP225", "EURUSD")              # prespecified primaries (014b collapse-verified)
F2_PLANT_BPS = 8.0
EXIT_REASONS = ("tp_anchor", "sl_outward", "time_stop", "form1_reversion",
                "form2_favorable_limit", "open_at_end")

PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta",
             "MateCount", "MateExpected", "MateGap", "OpenLegs")
SYSTEMATIC_BREACH_FRAC = 0.05


def min_state() -> int:
    """Frozen 4h power floor (governs, L-12)."""
    return DOMAIN_SPECS[DOMAIN].min_state_count


def cost_for(instrument: str) -> float:
    """Frozen per-instrument 4h round-trip cost (bps)."""
    return adaptive_cost_bps_for(instrument, DOMAIN)


def run_root(etag: str, arm: str, ztag: str, shift: bool = False) -> Path:
    """data/strategy_runs root for one (exit, arm, z*) family. E0 = the reused EXP-014b 4h
    emission (read-only); E1-E3 = the EXP-014c runs; -shift = the PRIMARY leak-tripwire twin."""
    if etag == "e0":
        if shift:
            return DATA_ROOT / f"EXP-014b-4h-s8-{arm}-{ztag}-shift"   # exists for none/extend z20+z15
        return DATA_ROOT / f"EXP-014b-4h-s8-{arm}-{ztag}"
    name = f"EXP-014c-4h-s8-{etag}-{arm}-{ztag}" + ("-shift" if shift else "")
    return DATA_ROOT / name


def newest_run_dir(root: Path, instrument: str) -> Path:
    pattern = f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


@dataclass
class Cell:
    etag: str
    arm: str
    ztag: str
    instrument: str
    positions: pl.DataFrame
    cis_trades: pl.DataFrame
    metadata: dict


def load_cell(etag: str, arm: str, instrument: str, ztag: str, shift: bool = False) -> Cell:
    """Load + fence-check one emitted (exit,arm,ztag,instrument) cell; attach cis_trades.parquet."""
    rd = newest_run_dir(run_root(etag, arm, ztag, shift), instrument)
    run = load_emitted_run(rd)
    assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
    cis_path = rd / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    return Cell(etag, arm, ztag, instrument, run.positions, cis, run.metadata)


def validate_provenance(positions: pl.DataFrame, instrument: str) -> dict:
    """Provenance columns present; engine fills within [Low,High] up to a gap/spread tolerance.
    A >5% systematic breach rate is a non-causal hard fail (L-01 pass). Wired into the pipeline
    (EXP-014b audit I2)."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    stats: dict = {}
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            stats[leg] = {"n_fills": 0, "n_breach": 0, "breach_frac": 0.0}
            continue
        f = fills.with_columns(
            tol=pl.max_horizontal(0.1 * (pl.col("RealHigh") - pl.col("RealLow")), 1e-4 * pl.col(leg)),
            over=pl.max_horizontal(pl.col(leg) - pl.col("RealHigh"), pl.col("RealLow") - pl.col(leg), 0.0))
        breach = f.filter(pl.col("over") > pl.col("tol"))
        frac = breach.height / fills.height
        stats[leg] = {"n_fills": fills.height, "n_breach": breach.height, "breach_frac": frac}
        if frac > SYSTEMATIC_BREACH_FRAC:
            raise ValueError(f"{instrument}: {breach.height}/{fills.height} {leg} fills outside bar "
                             f"range ({frac:.1%} > {SYSTEMATIC_BREACH_FRAC:.0%}) — systematic non-causal")
    return stats


# --------------------------------------------------------------------------- #
# Engine-realized per-bar NET bps (intra-position MTM, L-09; RT cost once/entry, L-02).
# --------------------------------------------------------------------------- #
def assemble_realized_bps(positions: pl.DataFrame, *, cost_bps: float
                          ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = positions.sort("SourceCloseTime")
    pos = df.get_column("Position").to_numpy().astype(float)
    op = df.get_column("RealOpen").to_numpy().astype(float)
    entry = df.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_ = df.get_column("ExitFillPrice").to_numpy().astype(float)
    if len(pos) < 3:
        raise ValueError("too few emitted bars to assemble a realized series")
    next_open = op[1:]
    op, pos, entry, exit_ = op[:-1], pos[:-1], entry[:-1], exit_[:-1]
    has_entry = ~np.isnan(entry)
    has_exit = ~np.isnan(exit_)
    with np.errstate(divide="ignore", invalid="ignore"):
        open_price = np.where(has_entry, entry, op)          # entry bar → entry fill else bar open
        close_price = np.where(has_exit, exit_, next_open)   # exit bar → exit fill else next open
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.where(pos != 0.0, gross, 0.0)
    gross = np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0)
    realized_bps = gross - cost_bps * has_entry.astype(float)
    market_returns = np.nan_to_num(np.log(next_open / op), nan=0.0, posinf=0.0, neginf=0.0)
    return market_returns, pos, realized_bps


def pstar_core(returns: np.ndarray, pos: np.ndarray, realized_bps: np.ndarray,
               cost_bps: float) -> dict:
    """Frozen 4h P*-gate core (referee_pstar.gate_stack_pstar) — never tuned (L-12)."""
    return gate_stack_pstar(returns, pos, realized_bps, domain=DOMAIN, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=SEED)


def referee_row(core: dict) -> dict:
    return adaptive_row(core, alpha=ALPHA)


def boot_p(core: dict) -> float:
    """One-sided bootstrap p from the referee's neutral-mean distribution (for Holm)."""
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    return float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm step-down over cross-cell p-values within one (exit,arm,z*) family (L-03/L-08)."""
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if m - i > 0 and p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out


def binom_ci(k: int, n: int, alpha: float = ALPHA, n_boot: int = N_BOOTSTRAP,
             seed: int = SEED) -> tuple[float, float, float]:
    """(p, lo, hi) bootstrap CI for a binomial share (M3 consistency read)."""
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    draws = rng.binomial(n, k / n, size=n_boot) / n
    return (k / n, float(np.quantile(draws, alpha / 2)), float(np.quantile(draws, 1 - alpha / 2)))
