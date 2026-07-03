"""
EXP-014b — CF-MR-004/HYP-003 (streamlined S8 rerun) shared analysis library (ANALYSIS-ONLY, L-01/P-09).

amendment-003: S8 only; availability control replaced by the symmetry two-barrier first-passage
(null=0.5, in mr_characterisation.py); single-leg exit = moving-mean form-2 + form-1 (no horizon,
no fix/trail); both-leg variant (short A + long basket, grouped spread); DOMAIN axis {1h,4h}. NEVER
regenerates a signal/anchor/edge/fill — every entry/exit/fill is engine-realized by the native cTrader
run and read from data/strategy_runs/EXP-014b-*/. This module holds the run map, ingestion, the
engine-realized per-bar NET bps assembly (intra-position MTM L-09; RT cost once/entry L-02, per-domain
cost map), the both-leg P&L aggregation, the frozen referee wrappers (referee_pstar.gate_stack_pstar —
never tuned, L-12), and a moving-block bootstrap.
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
DOMAINS = ("1h", "4h")                          # HYP-003 domain axis (separate strata families)
ALPHA = 0.05
N_BOOTSTRAP = 10_000
BLOCK = 4                                       # moving-block length (availability bootstrap)
SEED = 20260702
STRATEGY = "cross_instrument_spread_mr"
DATA_ROOT = ROOT / "data" / "strategy_runs"

FX = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD")
IDX = ("USTEC", "US500", "US2000", "JP225")
S8_CELLS = FX + IDX                             # S8 (basket−median-90): 11 cells

# Single-leg arms: reentry {none,allow,extend}, R only, moving-mean exit. Both-leg = grouped-spread
# variant with two entry mechanisms (limit-cancel-on-partial / market), reentry forced none.
SINGLE_ARMS = ("none", "allow", "extend")
BOTHLEG_ARMS = ("bothleg-limit", "bothleg-market")
ARMS = SINGLE_ARMS + BOTHLEG_ARMS
# The emitted run dirs use the conf shorthand for both-leg arms (EXP-014b-<dom>-s8-<token>-<ztag>);
# analysis keeps the canonical arm names above and maps to the dir token only at the path layer.
ARM_DIR_TOKEN = {"bothleg-limit": "bllim", "bothleg-market": "blmkt"}
# Deviation-magnitude axis (HYP-003): entry band = z*·σ. z20 = 2.0 (faithful default), z15 = 1.5
# (aggressive, less-extreme). Tag ↔ value. PRIMARY = single-leg none at z*=2.0.
ZSTARS = {"z20": 2.0, "z15": 1.5}
PRIMARY_ARM = "none"
PRIMARY_ZTAG = "z20"
Z_TRIGGERS = (2.0, 1.5)          # availability outlier thresholds (band-independent Z; read from one emission)
SERIES = "S8"
CIS_SERIES = "S8_RVINDEX"

PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta",
             "MateCount", "MateExpected", "MateGap", "OpenLegs")
SYSTEMATIC_BREACH_FRAC = 0.05                    # >5% fills outside bar range = systematic (lookahead) → fail
MIN_STATE_AVAIL = 30                             # availability decided-events floor (proportion CI, design §7)


def min_state_for(domain: str) -> int:
    """Frozen per-domain power floor N_min (governs, L-12): 4h=8, 1h=20."""
    return DOMAIN_SPECS[domain].min_state_count


def cost_for(instrument: str, domain: str) -> float:
    """Frozen per-instrument per-domain round-trip cost (bps)."""
    return adaptive_cost_bps_for(instrument, domain)


def run_root(domain: str, arm: str, ztag: str = PRIMARY_ZTAG, shift: bool = False) -> Path:
    """data/strategy_runs root for one (domain, arm, z*-tag) [+ -shift leak-tripwire variant]."""
    token = ARM_DIR_TOKEN.get(arm, arm)   # both-leg arms emit under the conf shorthand (bllim/blmkt)
    name = f"EXP-014b-{domain}-s8-{token}-{ztag}" + ("-shift" if shift else "")
    return DATA_ROOT / name


def newest_run_dir(root: Path, instrument: str, domain: str) -> Path:
    pattern = f"{STRATEGY}_{instrument.lower()}_{domain}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


# --------------------------------------------------------------------------- #
# Ingestion / provenance
# --------------------------------------------------------------------------- #
@dataclass
class Cell:
    domain: str
    arm: str
    ztag: str
    instrument: str
    positions: pl.DataFrame
    cis_trades: pl.DataFrame
    metadata: dict


def load_cell(domain: str, arm: str, instrument: str, ztag: str = PRIMARY_ZTAG,
              shift: bool = False) -> Cell:
    """Load + fence-check one emitted (domain,arm,ztag,instrument) cell; attach cis_trades.parquet."""
    rd = newest_run_dir(run_root(domain, arm, ztag, shift), instrument, domain)
    run = load_emitted_run(rd)
    assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
    cis_path = rd / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    return Cell(domain, arm, ztag, instrument, run.positions, cis, run.metadata)


def validate_provenance(positions: pl.DataFrame, instrument: str) -> dict:
    """Provenance columns present; engine fills within [Low,High] up to a gap/spread tolerance.
    Isolated breaches (bid/ask side vs bid-based OHLC, session-gap open fills of a ≤t-1 resting limit)
    are benign and reported; a >5% systematic breach rate is a non-causal hard fail (L-01 pass)."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    stats: dict = {}
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            stats[leg] = {"n_fills": 0, "n_breach": 0, "max_bps": 0.0, "breach_frac": 0.0}
            continue
        f = fills.with_columns(
            tol=pl.max_horizontal(0.1 * (pl.col("RealHigh") - pl.col("RealLow")), 1e-4 * pl.col(leg)),
            over=pl.max_horizontal(pl.col(leg) - pl.col("RealHigh"), pl.col("RealLow") - pl.col(leg), 0.0))
        breach = f.filter(pl.col("over") > pl.col("tol"))
        max_bps = float((breach.select((pl.col("over") / pl.col(leg) * 1e4).max()).item() or 0.0)
                        ) if breach.height else 0.0
        frac = breach.height / fills.height
        stats[leg] = {"n_fills": fills.height, "n_breach": breach.height,
                      "max_bps": max_bps, "breach_frac": frac}
        if frac > SYSTEMATIC_BREACH_FRAC:
            raise ValueError(f"{instrument}: {breach.height}/{fills.height} {leg} fills outside bar "
                             f"range ({frac:.1%} > {SYSTEMATIC_BREACH_FRAC:.0%}) — systematic non-causal")
    if "MateGap" in df.columns:
        n = df.height
        stats["mate_gap_frac"] = float(df.get_column("MateGap").cast(pl.Int8).sum() / n) if n else 0.0
    return stats


# --------------------------------------------------------------------------- #
# Engine-realized per-bar NET bps (intra-position MTM, L-09; RT cost once/entry, L-02).
# Reads ONLY emitted columns (P-09 clean). Position = dir active during the bar.
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


def _both_leg_group_nets(cis: pl.DataFrame, *, instrument: str, cost_lookup) -> list[tuple] | None:
    """Per grouped-spread-position net bps + its exit-settlement time, ordered by SpreadPositionId.

    Returns a list of ``(SpreadPositionId, exit_SourceCloseTime, net_bps)`` over COMPLETED groups
    (Censored==0), or None if the emission lacks the both-leg grouping columns. ``net_bps`` uses the
    pinned SPREAD weighting (audit C2 fix; matches the notional sizing A=1, each mate=1/n and the
    emitted per-bar MtmBps): ``net = A_net + mean(mate_nets)`` with each leg's
    ``RealizedBps − cost_lookup(LegSymbol)`` (RT cost once per leg, L-02; the 1/n mate weight
    applies to cost too since mate cost bps act on 1/n of the A notional). A partial_abort group
    with no filled mates settles as the A leg alone. All legs of a group share one exit
    ``SourceCloseTime`` (emitted at the joint close bar) — used as the settlement key.
    Analysis-only: reads engine-realized columns; never recomputes a fill (L-01/P-09)."""
    if cis.height == 0 or "SpreadPositionId" not in cis.columns or "LegSymbol" not in cis.columns:
        return None
    comp = cis.filter((pl.col("Censored") == 0) & (pl.col("SpreadPositionId") > 0)) \
        if "Censored" in cis.columns else cis.filter(pl.col("SpreadPositionId") > 0)
    if comp.height == 0:
        return []
    rows = comp.select("SpreadPositionId", "LegSymbol", "RealizedBps", "SourceCloseTime").to_dicts()
    by_pos: dict = {}
    for r in rows:
        net = float(r["RealizedBps"] or 0.0) - float(cost_lookup(str(r["LegSymbol"])))
        g = by_pos.setdefault(r["SpreadPositionId"], {"t": r["SourceCloseTime"], "a": [], "m": []})
        (g["a"] if str(r["LegSymbol"]) == instrument else g["m"]).append(net)
    out = []
    for pid, g in sorted(by_pos.items()):
        a_net = float(np.sum(g["a"]))                      # the single A leg (sum tolerates dupes)
        m_net = float(np.mean(g["m"])) if g["m"] else 0.0  # equal-weight mate basket (1/n each)
        out.append((pid, g["t"], a_net + m_net))
    return out


def both_leg_realized_bps(cis: pl.DataFrame, *, instrument: str, cost_lookup) -> np.ndarray | None:
    """Per grouped-spread-position realized net bps (equal-weight over N+1 legs). Thin wrapper over
    :func:`_both_leg_group_nets`; None if the grouping columns are absent, else the per-group array."""
    groups = _both_leg_group_nets(cis, instrument=instrument, cost_lookup=cost_lookup)
    return None if groups is None else np.asarray([net for _, _, net in groups], dtype=float)


def both_leg_realized_series(positions: pl.DataFrame, cis: pl.DataFrame, *, instrument: str,
                             cost_lookup) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Faithful single-leg→grouped-spread mirror feeding the FROZEN pstar referee (L-12).

    Builds a per-bar ``(returns, pos, realized_bps, exit_mask)`` aligned to the positions frame so
    :func:`pstar_core` / ``gate_stack_pstar`` consumes both-leg EXACTLY as single-leg: identical
    70/30 time split, identical contiguous-``pos`` episode counting (each spread-group hold is one
    episode → ``min_state`` counts groups automatically), identical per-bar market-return naive
    control leg. The ONLY change vs single-leg is the SIGNAL leg — realized net is the grouped-spread
    engine-realized P&L (Σ N+1 legs, RT cost once per leg, equal-weight; see
    :func:`_both_leg_group_nets`) SETTLED lump-sum on each group's exit bar (matched by
    ``SourceCloseTime``). Held bars carry 0 realized (engine-realized settlement — no invented marks);
    a group's per-episode sum the referee's sub-pop leg sees equals its total net. This is the exact
    seam ``gate_stack_pstar`` was designed for (signal-leg source swap, no threshold/knob change).

    Output shape mirrors :func:`assemble_realized_bps` (length ``N-1``; last bar dropped for the
    open-to-open next step). ``exit_mask`` marks each group's settlement bar (for per-episode bite
    plants). Provenance (L-01/P-09): reads ONLY emitted engine-realized columns — positions.Position
    (per-bar group sign) + RealOpen (A open, naive leg) + cis_trades.{SpreadPositionId, LegSymbol,
    RealizedBps, Censored, SourceCloseTime}; never recomputes a fill; every value ≤ fence."""
    df = positions.sort("SourceCloseTime")
    op = df.get_column("RealOpen").to_numpy().astype(float)
    pos = df.get_column("Position").to_numpy().astype(float)
    st = df.get_column("SourceCloseTime").to_list()
    if len(pos) < 3:
        raise ValueError("too few emitted bars to assemble a both-leg realized series")
    market_returns = np.nan_to_num(np.log(op[1:] / op[:-1]), nan=0.0, posinf=0.0, neginf=0.0)
    pos = pos[:-1]
    realized = np.zeros(len(pos), dtype=float)
    exit_mask = np.zeros(len(pos), dtype=bool)
    groups = _both_leg_group_nets(cis, instrument=instrument, cost_lookup=cost_lookup) or []
    idx_of = {t: i for i, t in enumerate(st[:-1])}          # settlement bar within the referee window
    for _pid, exit_t, net in groups:
        i = idx_of.get(exit_t)
        if i is not None:                                   # exit bar inside the fenced window
            realized[i] += net
            exit_mask[i] = True
    return market_returns, pos, realized, exit_mask


def pstar_core(returns: np.ndarray, pos: np.ndarray, realized_bps: np.ndarray,
               cost_bps: float, domain: str) -> dict:
    """Frozen per-domain P*-gate core (referee_pstar.gate_stack_pstar) — never tuned (L-12)."""
    return gate_stack_pstar(returns, pos, realized_bps, domain=domain, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=SEED)


def boot_p(core: dict) -> float:
    """One-sided bootstrap p from the referee's neutral-mean distribution (for Holm)."""
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    return float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")


def referee_row(returns: np.ndarray, pos: np.ndarray, realized_bps: np.ndarray,
                cost_bps: float, domain: str) -> dict:
    return adaptive_row(pstar_core(returns, pos, realized_bps, cost_bps, domain), alpha=ALPHA)


# --------------------------------------------------------------------------- #
# Bootstrap helpers.
#   - block_bootstrap_mean_ci / two_sample_diff_ci: moving-block on per-event outcomes (L-07).
#   - proportion_ci_vs_half: bootstrap CI for the symmetry two-barrier p_inward vs the 0.5 null.
# --------------------------------------------------------------------------- #
def block_bootstrap_mean_ci(x: np.ndarray, *, block: int = BLOCK, n: int = N_BOOTSTRAP,
                            seed: int = SEED, alpha: float = ALPHA) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) via a moving-block bootstrap over per-event outcomes."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    if x.size < block or block <= 1:
        return (float(np.mean(x)), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(x.size / block))
    starts_max = x.size - block + 1
    means = np.empty(n, dtype=float)
    for b in range(n):
        starts = rng.integers(0, starts_max, size=n_blocks)
        sample = np.concatenate([x[s:s + block] for s in starts])[:x.size]
        means[b] = sample.mean()
    lo = float(np.quantile(means, alpha / 2.0))
    hi = float(np.quantile(means, 1.0 - alpha / 2.0))
    return (float(np.mean(x)), lo, hi)


def proportion_ci_vs_half(outcomes: np.ndarray, *, n: int = N_BOOTSTRAP, seed: int = SEED,
                          alpha: float = ALPHA) -> tuple[float, float, float, int]:
    """Symmetry-control statistic. `outcomes` = per-DECIDED-event indicators (1=inward first,
    0=outward first). Returns (p_inward, ci_low, ci_high, n_decided) via an iid bootstrap over
    events (each event is one independent first-passage race). Availability ⇔ ci_low > 0.5."""
    x = np.asarray(outcomes, dtype=float)
    x = x[np.isfinite(x)]
    n_dec = int(x.size)
    if n_dec == 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    rng = np.random.default_rng(seed)
    props = np.empty(n, dtype=float)
    for b in range(n):
        props[b] = x[rng.integers(0, n_dec, size=n_dec)].mean()
    lo = float(np.quantile(props, alpha / 2.0))
    hi = float(np.quantile(props, 1.0 - alpha / 2.0))
    return (float(x.mean()), lo, hi, n_dec)


def two_sample_diff_ci(cond: np.ndarray, ctrl: np.ndarray, *, block: int = BLOCK,
                       n: int = N_BOOTSTRAP, seed: int = SEED, alpha: float = ALPHA
                       ) -> tuple[float, float, float]:
    """Δ = mean(cond) − mean(ctrl) with a bootstrap CI (moving-block on cond, iid on ctrl)."""
    cond = np.asarray(cond, dtype=float); cond = cond[np.isfinite(cond)]
    ctrl = np.asarray(ctrl, dtype=float); ctrl = ctrl[np.isfinite(ctrl)]
    if cond.size == 0 or ctrl.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    diffs = np.empty(n, dtype=float)
    eff_block = block if cond.size >= block else 1
    n_blocks = int(np.ceil(cond.size / eff_block))
    starts_max = max(1, cond.size - eff_block + 1)
    for b in range(n):
        starts = rng.integers(0, starts_max, size=n_blocks)
        cs = np.concatenate([cond[s:s + eff_block] for s in starts])[:cond.size]
        ks = ctrl[rng.integers(0, ctrl.size, size=ctrl.size)]
        diffs[b] = cs.mean() - ks.mean()
    delta = float(cond.mean() - ctrl.mean())
    return (delta, float(np.quantile(diffs, alpha / 2.0)), float(np.quantile(diffs, 1.0 - alpha / 2.0)))


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm step-down over cross-cell p-values within one (domain,arm) family (L-03/L-08)."""
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if m - i > 0 and p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out
