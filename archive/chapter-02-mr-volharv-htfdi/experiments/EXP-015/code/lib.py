"""
EXP-015 — CF-MR-005/HYP-001 shared library (ANALYSIS-ONLY, L-01/P-09).

Part A reads existing EXP-014b/c 4h engine emissions READ-ONLY (anatomy only; no admissibility
claim). Part B is an availability-style measurement on 1m-derived 4h timebars: basket-free
own-price dislocation events + conditional forward-return profiles. NO strategy P&L is
simulated anywhere in Python.

Causal-provenance contract (Part B):
  - Trigger/state at action bar t reads ONLY confirmed bars <= t-1:
    S_{t-1} = logClose_{t-1} - Median_90(logClose)_{t-1}; sigma_{t-1} = rolling std of S over
    WZ=200 bars ending t-1; z_{t-1} = S_{t-1}/sigma_{t-1}. Event fires at the OPEN of bar t.
  - The anchor a = exp(Median_90(logClose)_{t-1}) is FROZEN at event time.
  - Recovery R_h = dir * (logOpen_{t+h} - logOpen_t) / |S_{t-1}| is open-to-open from the
    action bar's open; the forming bar's own OHLC is never read at decision time.
  - Matching features (vol tercile / |return| decile) are computed on closed-bar returns and
    read at t-1.

Fence: EXP-013 first-49% per-symbol cutoffs, verbatim (tools/ctrader-cli/experiments/
EXP-013.conf ANALYSIS_END). 1m bars with CloseTime >= fence are dropped BEFORE aggregation;
max CloseTime asserted < fence per cell. Final-30% holdout never loaded (fence ~= 49%).

Frozen seeds: bootstrap 20260703, permutation 20260704. Block length 12 bars.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.bar_aggregator import aggregate_ohlc                                   # noqa: E402
from xen.referee_adaptive import adaptive_cost_bps_for                          # noqa: E402
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout   # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen per design.md)
# --------------------------------------------------------------------------- #
DOMAIN = "4h"
PERIOD_MINUTES = 240
FX = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD")
IDX = ("USTEC", "US500", "US2000", "JP225")
CELLS = FX + IDX

# EXP-013 first-49% TRAIN cutoffs, verbatim (EXP-013.conf ANALYSIS_END).
FENCE_UTC: dict[str, str] = {
    "EURUSD": "2024-08-25T22:19:00Z",
    "GBPUSD": "2024-09-08T22:09:00Z",
    "USDJPY": "2024-09-06T12:28:00Z",
    "USDCHF": "2024-09-09T00:05:00Z",
    "USDCAD": "2024-09-06T16:23:00Z",
    "AUDUSD": "2024-09-06T14:40:00Z",
    "NZDUSD": "2024-09-06T05:42:00Z",
    "USTEC": "2024-08-26T01:06:00Z",
    "US500": "2024-09-17T17:26:00Z",
    "US2000": "2024-09-10T09:33:00Z",
    "JP225": "2024-09-23T04:40:00Z",
}

MEDIAN_W = 90            # anchor window (4h bars) — mirrors S8 construction minus the basket
SIGMA_W = 200            # WZ: rolling std of S
Z_ENTRY = 1.5            # bin-1 lower edge (z* in {1.5, 2.0} => bins 2-4 give the z*=2.0 read)
Z_EXIT = 1.0             # episode ends when |z| < Z_EXIT (de-clustering)
DEPTH_BINS = ((1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, np.inf))
HORIZONS = (6, 12, 24, 48)
H_BIND = 24              # binding horizon for M2/M3/tripwire reads
VOL_W = 20               # closed-bar return vol window for matching
DRIFT_W = 90             # trailing-return window for the M3b drift split
N_CONTROLS = 20          # matched controls per event (frozen-seed sample)
MIN_EVENTS = 30          # powered floor per (cell, bin)
BLOCK = 12               # moving-block length (bars) — bootstrap + permutation
N_BOOTSTRAP = 10_000
N_PERM = 200
SEED_BOOT = 20260703
SEED_PERM = 20260704
ALPHA = 0.05

# Part A (read-only emissions)
STRATEGY = "cross_instrument_spread_mr"
DATA_ROOT = ROOT / "data" / "strategy_runs"
EXITS = ("e0", "e1", "e2", "e3")
ZTAGS = ("z15", "z20")
LADDER_LEVELS = (0, 1, 2)
COST_MULTS = (1.0, 2.0, 3.0)
PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "OpenLegs")
SYSTEMATIC_BREACH_FRAC = 0.05


def cost_for(instrument: str) -> float:
    """Frozen per-instrument 4h round-trip cost (bps) — referee cost table, read-only."""
    return adaptive_cost_bps_for(instrument, DOMAIN)


def fence_naive_utc(symbol: str) -> datetime:
    """Fence timestamp as tz-naive UTC (parquet datetimes are naive UTC)."""
    return datetime.fromisoformat(FENCE_UTC[symbol].replace("Z", "+00:00")).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Part B — data loading (fenced) + feature construction
# --------------------------------------------------------------------------- #
def load_4h_bars(symbol: str) -> pl.DataFrame:
    """Load the 5y-era 1m file for `symbol`, fence at the EXP-013 cutoff, aggregate to 4h.

    The 5y era is pinned by prefix (`timebars_<sym>_20210602_*`) — the plain latest-glob
    would select the old 2023-era file. Strict aggregation (min_coverage=None) drops
    partial windows, so no boundary fence is needed beyond the 1m filter.
    """
    pattern = f"timebars/timebars_{symbol.lower()}_20210602_*.parquet"
    hits = sorted((ROOT / "data").glob(pattern))
    if not hits:
        raise FileNotFoundError(f"{symbol}: no 5y-era timebars file ({pattern})")
    fence = fence_naive_utc(symbol)
    bars_1m = (
        pl.scan_parquet(hits[-1])
        .select("Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close")
        .sort("CloseTime")
        .filter(pl.col("CloseTime") < fence)
        .collect()
    )
    if bars_1m.is_empty():
        raise ValueError(f"{symbol}: no 1m bars before fence {fence}")
    max_ct = bars_1m.get_column("CloseTime").max()
    if max_ct >= fence:
        raise ValueError(f"{symbol}: fence breach — max CloseTime {max_ct} >= {fence}")
    return aggregate_ohlc(bars_1m, period_minutes=PERIOD_MINUTES, min_coverage=None)


@dataclass
class CellSeries:
    """Per-cell 4h arrays. All state columns are raw (unlagged); event logic applies [t-1]."""
    symbol: str
    close_time: np.ndarray     # datetime64[ns]
    open_: np.ndarray
    log_close: np.ndarray
    s: np.ndarray              # S_t = logClose_t - Median_90(logClose)_t
    sigma: np.ndarray          # rolling std of S over SIGMA_W
    z: np.ndarray              # S/sigma
    vol: np.ndarray            # rolling std of closed-bar log returns over VOL_W
    abs_ret: np.ndarray        # |1-bar closed log return|
    drift: np.ndarray          # trailing DRIFT_W-bar log-close return (sign = drift direction)
    year: np.ndarray


def build_series(symbol: str, bars_4h: pl.DataFrame) -> CellSeries:
    """Compute anchor/dislocation/matching features on the fenced 4h frame.

    Every rolling window is full-window (nulls during warmup); values at index i use bars
    <= i only (closed-bar states — the event layer applies the additional [t-1] lag).
    """
    df = bars_4h.sort("CloseTime").with_columns(logc=pl.col("Close").log())
    df = df.with_columns(
        med90=pl.col("logc").rolling_median(window_size=MEDIAN_W),
        ret=pl.col("logc").diff(),
    )
    df = df.with_columns(s=pl.col("logc") - pl.col("med90"))
    df = df.with_columns(
        sigma=pl.col("s").rolling_std(window_size=SIGMA_W),
        vol=pl.col("ret").rolling_std(window_size=VOL_W),
        abs_ret=pl.col("ret").abs(),
        drift=pl.col("logc") - pl.col("logc").shift(DRIFT_W),
    )
    df = df.with_columns(z=pl.col("s") / pl.col("sigma"))
    return CellSeries(
        symbol=symbol,
        close_time=df.get_column("CloseTime").to_numpy(),
        open_=df.get_column("Open").to_numpy().astype(float),
        log_close=df.get_column("logc").to_numpy().astype(float),
        s=df.get_column("s").to_numpy().astype(float),
        sigma=df.get_column("sigma").to_numpy().astype(float),
        z=df.get_column("z").to_numpy().astype(float),
        vol=df.get_column("vol").to_numpy().astype(float),
        abs_ret=df.get_column("abs_ret").to_numpy().astype(float),
        drift=df.get_column("drift").to_numpy().astype(float),
        year=df.get_column("CloseTime").dt.year().to_numpy().astype(int),
    )


# --------------------------------------------------------------------------- #
# Part B — event extraction (sequential, de-clustered) + recovery measurement
# --------------------------------------------------------------------------- #
def depth_bin(abs_z: float) -> int:
    """0-based depth bin for |z| >= Z_ENTRY; -1 below entry."""
    for b, (lo, hi) in enumerate(DEPTH_BINS):
        if lo <= abs_z < hi:
            return b
    return -1


def extract_events(series: CellSeries) -> pl.DataFrame:
    """De-clustered dislocation events, one per (episode, depth bin) entry.

    Sequential/stateful by design: an episode starts when |z_{t-1}| >= Z_ENTRY and ends when
    |z_{t-1}| < Z_EXIT (or the dislocation sign flips). Within an episode each depth bin
    emits at most one event, the first bar t whose |z_{t-1}| reaches that bin (a jump
    through several bins emits all newly reached bins — the ladder adds every crossed rung).
    Event fields are all [t-1] states; t is the action-bar index (decision at its open).
    """
    z, s, drift = series.z, series.s, series.drift
    n = len(z)
    rows: list[tuple] = []
    in_epi, epi_sign, bins_hit = False, 0, set()
    for t in range(1, n):
        zl = z[t - 1]
        if not np.isfinite(zl):
            in_epi, bins_hit = False, set()
            continue
        sign = 1 if zl > 0 else -1
        if abs(zl) < Z_EXIT or (in_epi and sign != epi_sign):
            in_epi, bins_hit = False, set()
        if abs(zl) < Z_ENTRY:
            continue
        if not in_epi:
            in_epi, epi_sign, bins_hit = True, sign, set()
        top = depth_bin(abs(zl))
        for b in range(top + 1):
            if b not in bins_hit:
                bins_hit.add(b)
                rows.append((t, b, abs(s[t - 1]), -sign, float(drift[t - 1])))
    return pl.DataFrame(
        rows, orient="row",
        schema={"t": pl.Int64, "bin": pl.Int64, "abs_s": pl.Float64,
                "dir": pl.Int64, "drift": pl.Float64},
    )


def recovery(series: CellSeries, t: np.ndarray, direction: np.ndarray, abs_s: np.ndarray,
             h: int) -> np.ndarray:
    """R_h = dir*(logOpen_{t+h} - logOpen_t)/|S_{t-1}| ; NaN when t+h is beyond the fence."""
    log_open = np.log(series.open_)
    n = len(log_open)
    out = np.full(len(t), np.nan)
    ok = (t + h) < n
    with np.errstate(divide="ignore", invalid="ignore"):
        out[ok] = direction[ok] * (log_open[t[ok] + h] - log_open[t[ok]]) / abs_s[ok]
    return out


def running_max_recovery(series: CellSeries, t: int, direction: int, abs_s: float,
                         h_max: int) -> float:
    """Max fraction recovered over opens t+1..t+h_max (M4 bin-4 non-recovery census).

    NaN (censored) when the full h_max window is not available before the fence — a partial
    window cannot certify "never recovered within h_max".
    """
    log_open = np.log(series.open_)
    end = t + h_max
    if end > len(log_open) - 1:
        return float("nan")
    path = direction * (log_open[t + 1: end + 1] - log_open[t]) / abs_s
    return float(np.max(path))


# --------------------------------------------------------------------------- #
# Part B — matched control (vol tercile x |return| decile, frozen seed)
# --------------------------------------------------------------------------- #
def build_strata(series: CellSeries, h_max: int) -> tuple[np.ndarray, np.ndarray]:
    """(stratum_id, valid_pool) per bar t, from [t-1] matching features.

    Stratum = vol tercile (3) x |return| decile (10), quantiles over valid bars of the cell.
    Pool bars need finite features, |S_{t-1}| > 0, and h_max headroom before the fence. The
    pool is NOT conditioned on dislocation (design M1: matched-random, not z-filtered).
    """
    n = len(series.z)
    vol_l = np.concatenate(([np.nan], series.vol[:-1]))
    ret_l = np.concatenate(([np.nan], series.abs_ret[:-1]))
    s_l = np.concatenate(([np.nan], series.s[:-1]))
    valid = (np.isfinite(vol_l) & np.isfinite(ret_l) & np.isfinite(s_l)
             & np.isfinite(np.concatenate(([np.nan], series.z[:-1])))
             & (np.abs(s_l) > 0) & (np.arange(n) + h_max < n))
    stratum = np.full(n, -1, dtype=int)
    if valid.sum() < 60:
        return stratum, valid
    v_edges = np.nanquantile(vol_l[valid], [1 / 3, 2 / 3])
    r_edges = np.nanquantile(ret_l[valid], np.arange(1, 10) / 10)
    v_bin = np.digitize(vol_l, v_edges)
    r_bin = np.digitize(ret_l, r_edges)
    stratum[valid] = v_bin[valid] * 10 + r_bin[valid]
    return stratum, valid


def match_controls(events: pl.DataFrame, series: CellSeries, stratum: np.ndarray,
                   valid: np.ndarray, rng: np.random.Generator) -> dict[int, np.ndarray]:
    """Per event t: N_CONTROLS bar indices sampled (frozen rng) from the event's stratum,
    excluding the event bars themselves. Returns {event_t: control_indices}."""
    event_ts = set(events.get_column("t").to_list())
    pool_mask = valid.copy()
    for t in event_ts:
        pool_mask[t] = False
    out: dict[int, np.ndarray] = {}
    pools: dict[int, np.ndarray] = {}
    for t in sorted(event_ts):
        st = stratum[t] if valid[t] else -1
        if st < 0:  # event bar lacks matching features/headroom — control via full pool
            pool = np.flatnonzero(pool_mask)
        else:
            if st not in pools:
                pools[st] = np.flatnonzero(pool_mask & (stratum == st))
            pool = pools[st]
        if len(pool) == 0:
            out[t] = np.empty(0, dtype=int)
            continue
        out[t] = rng.choice(pool, size=min(N_CONTROLS, len(pool)),
                            replace=len(pool) < N_CONTROLS)
    return out


def control_recovery(series: CellSeries, ctrl_idx: np.ndarray, h: int) -> np.ndarray:
    """Control R_h at control bars' OWN dislocation (dir toward own anchor, own |S_{t-1}|)."""
    if len(ctrl_idx) == 0:
        return np.empty(0)
    s_l = series.s[ctrl_idx - 1]
    direction = np.where(s_l > 0, -1, 1)
    return recovery(series, ctrl_idx, direction, np.abs(s_l), h)


# --------------------------------------------------------------------------- #
# Part B — paired estimator + moving-block bootstrap + permutation null
# --------------------------------------------------------------------------- #
def paired_deltas(series: CellSeries, ev: pl.DataFrame,
                  controls: dict[int, np.ndarray], h: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-event paired difference d_e = R_h(event) - median(R_h(matched controls)) (L-15 #3).

    Returns (d, t) for events where both legs are finite; ΔR_h = median(d).
    """
    t_arr = ev.get_column("t").to_numpy()
    dir_arr = ev.get_column("dir").to_numpy()
    s_arr = ev.get_column("abs_s").to_numpy()
    r_ev = recovery(series, t_arr, dir_arr, s_arr, h)
    d, ts = [], []
    for i, t in enumerate(t_arr):
        if not np.isfinite(r_ev[i]):
            continue
        rc = control_recovery(series, controls.get(int(t), np.empty(0, dtype=int)), h)
        rc = rc[np.isfinite(rc)]
        if len(rc) == 0:
            continue
        d.append(r_ev[i] - float(np.median(rc)))
        ts.append(int(t))
    return np.asarray(d), np.asarray(ts, dtype=int)


def block_boot_ci(d: np.ndarray, ts: np.ndarray, n_boot: int, seed: int,
                  stat=np.median) -> tuple[float, float, float]:
    """(stat, lo, hi): moving-block bootstrap over events grouped in BLOCK-bar time blocks."""
    if len(d) == 0:
        return (float("nan"), float("nan"), float("nan"))
    blocks = ts // BLOCK
    uniq = np.unique(blocks)
    groups = [d[blocks == b] for b in uniq]
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot)
    m = len(groups)
    for k in range(n_boot):
        pick = rng.integers(0, m, size=m)
        stats[k] = stat(np.concatenate([groups[j] for j in pick]))
    return (float(stat(d)), float(np.quantile(stats, ALPHA / 2)),
            float(np.quantile(stats, 1 - ALPHA / 2)))


def bin_slope(medians: dict[int, float]) -> float:
    """OLS slope of median ΔR over available depth-bin indices (M2 trend read)."""
    xs = np.array(sorted(b for b, v in medians.items() if np.isfinite(v)), dtype=float)
    if len(xs) < 2:
        return float("nan")
    ys = np.array([medians[int(b)] for b in xs])
    return float(np.polyfit(xs, ys, 1)[0])


def permuted_series(series: CellSeries, rng: np.random.Generator) -> CellSeries:
    """Rebuild the cell's path from block-permuted open-to-open returns (L-07 tripwire).

    r_i = logOpen_{i+1} - logOpen_i permuted in BLOCK-length blocks; opens rebuilt from the
    same origin; Close'_i := Open'_{i+1} (last close = last open) so anchor/z/matching
    features recompute on the permuted path via the same code path.
    """
    log_open = np.log(series.open_)
    r = np.diff(log_open)
    n_r = len(r)
    n_blocks = int(np.ceil(n_r / BLOCK))
    order = rng.permutation(n_blocks)
    idx = np.concatenate([np.arange(b * BLOCK, min((b + 1) * BLOCK, n_r)) for b in order])
    lo_new = np.concatenate(([log_open[0]], log_open[0] + np.cumsum(r[idx])))
    open_new = np.exp(lo_new)
    close_new = np.concatenate((open_new[1:], open_new[-1:]))
    df = pl.DataFrame({
        "CloseTime": series.close_time, "Open": open_new,
        "High": np.maximum(open_new, close_new), "Low": np.minimum(open_new, close_new),
        "Close": close_new, "Symbol": [series.symbol] * len(open_new),
    })
    return build_series(series.symbol, df)


def pipeline_delta_r(series: CellSeries, rng: np.random.Generator,
                     h: int = H_BIND) -> dict[int, float]:
    """Full M1 pipeline -> point ΔR_h per depth bin (used per permutation replicate)."""
    ev = extract_events(series)
    if ev.is_empty():
        return {}
    stratum, valid = build_strata(series, h_max=max(HORIZONS))
    controls = match_controls(ev, series, stratum, valid, rng)
    out: dict[int, float] = {}
    for b in range(len(DEPTH_BINS)):
        sub = ev.filter(pl.col("bin") == b)
        if sub.is_empty():
            continue
        d, _ = paired_deltas(series, sub, controls, h)
        if len(d):
            out[b] = float(np.median(d))
    return out


# --------------------------------------------------------------------------- #
# Part A — read-only emission loaders (adapted from the audited EXP-014c lib)
# --------------------------------------------------------------------------- #
def run_root(etag: str, arm: str, ztag: str, shift: bool = False) -> Path:
    """Emission root for one (exit, arm, z*) family. e0 = EXP-014b 4h runs; e1-e3 = EXP-014c."""
    if etag == "e0":
        return DATA_ROOT / (f"EXP-014b-4h-s8-{arm}-{ztag}" + ("-shift" if shift else ""))
    return DATA_ROOT / (f"EXP-014c-4h-s8-{etag}-{arm}-{ztag}" + ("-shift" if shift else ""))


def newest_run_dir(root: Path, instrument: str) -> Path:
    hits = sorted(root.glob(f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root}")
    return hits[-1]


@dataclass
class EmittedCell:
    etag: str
    arm: str
    ztag: str
    instrument: str
    positions: pl.DataFrame
    cis_trades: pl.DataFrame
    metadata: dict


def load_cell(etag: str, arm: str, instrument: str, ztag: str, shift: bool = False) -> EmittedCell:
    """Load + fence-check one emitted cell (read-only); re-assert provenance (design §4.2)."""
    rd = newest_run_dir(run_root(etag, arm, ztag, shift), instrument)
    run = load_emitted_run(rd)
    assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
    validate_provenance(run.positions, instrument)
    cis_path = rd / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    return EmittedCell(etag, arm, ztag, instrument, run.positions, cis, run.metadata)


def validate_provenance(positions: pl.DataFrame, instrument: str) -> dict:
    """EXP-014c audit provenance check: fills within [Low,High] up to gap/spread tolerance;
    >5% systematic breach is a non-causal hard fail (L-01 pass)."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    stats: dict = {}
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            stats[leg] = {"n_fills": 0, "breach_frac": 0.0}
            continue
        f = fills.with_columns(
            tol=pl.max_horizontal(0.1 * (pl.col("RealHigh") - pl.col("RealLow")),
                                  1e-4 * pl.col(leg)),
            over=pl.max_horizontal(pl.col(leg) - pl.col("RealHigh"),
                                   pl.col("RealLow") - pl.col(leg), 0.0))
        frac = f.filter(pl.col("over") > pl.col("tol")).height / fills.height
        stats[leg] = {"n_fills": fills.height, "breach_frac": frac}
        if frac > SYSTEMATIC_BREACH_FRAC:
            raise ValueError(f"{instrument}: {frac:.1%} {leg} fills outside bar range — "
                             "systematic non-causal")
    return stats


def assemble_realized_bps(positions: pl.DataFrame, *, cost_bps: float
                          ) -> tuple[np.ndarray, np.ndarray]:
    """Engine-realized per-bar NET bps (intra-position MTM L-09; RT cost once/entry L-02).

    Provenance: realized_bps[t] reads pos[t], RealOpen[t]/RealOpen[t+1] and the engine's own
    Entry/ExitFillPrice at t — never a future bar. Returns (realized_bps, open_legs) aligned
    (last bar dropped — no next open).
    """
    df = positions.sort("SourceCloseTime")
    pos = df.get_column("Position").to_numpy().astype(float)
    op = df.get_column("RealOpen").to_numpy().astype(float)
    entry = df.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_ = df.get_column("ExitFillPrice").to_numpy().astype(float)
    legs = df.get_column("OpenLegs").to_numpy().astype(float)
    if len(pos) < 3:
        raise ValueError("too few emitted bars")
    next_open = op[1:]
    op, pos, entry, exit_, legs = op[:-1], pos[:-1], entry[:-1], exit_[:-1], legs[:-1]
    has_entry = ~np.isnan(entry)
    has_exit = ~np.isnan(exit_)
    with np.errstate(divide="ignore", invalid="ignore"):
        open_price = np.where(has_entry, entry, op)
        close_price = np.where(has_exit, exit_, next_open)
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.nan_to_num(np.where(pos != 0.0, gross, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
    return gross - cost_bps * has_entry.astype(float), legs


def episodes_from_legs(cis: pl.DataFrame) -> list[dict]:
    """Group completed legs into ladder-occupancy episodes by [EntryTime, ExitTime] overlap.

    Sequential by EntryTime: a leg joins the open episode while its EntryTime <= the episode's
    running max ExitTime. Censored legs are excluded (counted by the caller).
    """
    comp = cis.filter(pl.col("Censored") == 0).sort("EntryTime")
    if comp.height == 0:
        return []
    episodes: list[dict] = []
    cur: dict | None = None
    for r in comp.iter_rows(named=True):
        if cur is not None and r["EntryTime"] <= cur["max_exit"]:
            cur["legs"].append(r)
            cur["max_exit"] = max(cur["max_exit"], r["ExitTime"])
        else:
            if cur is not None:
                episodes.append(cur)
            cur = {"legs": [r], "max_exit": r["ExitTime"]}
    if cur is not None:
        episodes.append(cur)
    out = []
    for e in episodes:
        legs = e["legs"]
        out.append({
            "start": min(x["EntryTime"] for x in legs),
            "end": e["max_exit"],
            "n_legs": len(legs),
            "pnl_bps": float(sum(x["RealizedBps"] for x in legs)),
            "max_abs_entry_z": float(max(abs(x["EntryZ"]) for x in legs)),
            "sum_mae_bps": float(sum(min(x["MaeBps"], 0.0) for x in legs)),
            "max_bars_held": int(max(x["BarsHeld"] for x in legs)),
            "year": int(min(x["EntryTime"] for x in legs).year),
        })
    return out
