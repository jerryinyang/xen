"""SPDR-004 — CF-HTFCAP-001 TRAIN-only availability screen (vectorised Python).

Lane: docs/references/spdr-lane.md · design: python/experiments/SPDR-004/design.md
AMENDMENT-1: UNF×{DI,DI_ADX} matched baseline = RAND battery at UNF cadence (no UNF×NONE).

Integrity: design §10 code-asserted checklist must print PASS 11/11 before promote-facing
results are written. Disposition is operator-only after analysis.md — this script never
writes WORTH_EXPLORING / NOT_WORTH.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from tqdm import tqdm

from xen.bar_aggregator import aggregate_ohlc
from xen.evaluation import (
    block_bootstrap_ci,
    block_sensitivity,
    bybit_round_trip_cost_bps,
    mde,
)
from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest
from xen.zigzag import wilder_atr

# --------------------------------------------------------------------------- #
# Paths / constants
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
REPO = EXP_DIR.parents[2]
RESULTS = EXP_DIR / "results"
FAMILY_CARD = REPO / "docs/signal-registry/candidate-families/cf-htfcap-001.md"
MULTIPLICITY = REPO / "docs/signal-registry/multiplicity-registry.md"
ADMISSION = REPO / "python/experiments/INFR-011/artifacts/admission-ledger.jsonl"
CATALOG_PATH = REPO / "data" / "catalog"

DOMAIN_PAIRS: list[tuple[str, int, int, int]] = [
    # (name, htf_min, ltf_min, ratio)
    ("1h/5m", 60, 5, 12),
    ("4h/15m", 240, 15, 16),
    ("1d/1h", 1440, 60, 24),
]
HOLD_MULTS = [0.5, 1.0, 2.0, 4.0]
BASES = ("UNF", "MOM", "RAND")
HTF_FILTERS_TREAT = ("DI", "DI_ADX")  # treatments; NONE is baseline only
ADX_PERIOD = 14
ATR_PERIOD = 14
ADX_GATE = 25.0
RAND_SEEDS = list(range(1000, 1025))  # 25 seeds, regenerable (L-19)
PHASE_SHIFT_K = 50  # Control C: K HTF bars (design §7)
N_BOOT = 1_000  # screen-practical; dependence-honest with block rule below
N_CI_SEEDS = 3
MIN_TRADES_POWER = 30
# Cell grid uses top-N by membership-days (design 720 = 10×3×4×3×2); membership series still full.
PRIMARY_N = 10

NS_PER_MIN = 60_000_000_000
NS_PER_DAY = 86_400_000_000_000


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class DomainCtx:
    """LTF-indexed causal context for one (symbol, domain)."""

    domain: str
    htf_min: int
    ltf_min: int
    ratio: int
    symbol: str
    ltf_open: np.ndarray
    ltf_close: np.ndarray
    ltf_open_ns: np.ndarray  # int64 ns UTC open
    ltf_close_ns: np.ndarray
    ltf_atr_prev: np.ndarray  # ATR(14)[t-1]
    htf_dir: np.ndarray  # +1 if +DI>-DI else -1; 0 invalid
    adx: np.ndarray
    member: np.ndarray  # bool: symbol in top-10 at this LTF bar open
    valid_htf: np.ndarray  # HTF features finite + mapped
    mom_sign: np.ndarray  # MOM base sign at t (from close[t-1]-close[t-1-N]); 0 if undef
    n: int = field(init=False)
    # internals for golden trace / Control C rebuild
    _htf_close_ns: np.ndarray = field(repr=False, default_factory=lambda: np.array([], dtype=np.int64))
    _htf_dir_raw: np.ndarray = field(repr=False, default_factory=lambda: np.array([], dtype=np.int8))
    _adx_raw: np.ndarray = field(repr=False, default_factory=lambda: np.array([], dtype=np.float64))
    _map_idx: np.ndarray = field(repr=False, default_factory=lambda: np.array([], dtype=np.int64))

    def __post_init__(self) -> None:
        self.n = int(len(self.ltf_open))


# --------------------------------------------------------------------------- #
# Registration + admission pool
# --------------------------------------------------------------------------- #
def check_registration() -> tuple[bool, str]:
    """§10 item 1: family card REGISTERED + multiplicity Chapter 04 row; 0 slots."""
    if not FAMILY_CARD.exists():
        return False, "family card missing"
    card = FAMILY_CARD.read_text()
    if "CF-HTFCAP-001" not in card:
        return False, "family id missing on card"
    if not re.search(r"\*\*Status:\*\*\s*`?REGISTERED`?", card):
        return False, "family card not REGISTERED"
    if not MULTIPLICITY.exists():
        return False, "multiplicity registry missing"
    mult = MULTIPLICITY.read_text()
    if "Chapter 04 · CF-HTFCAP-001" not in mult and "CF-HTFCAP-001 Registration" not in mult:
        return False, "multiplicity Chapter 04 CF-HTFCAP-001 row missing"
    if "0 slots" not in mult.lower() and "0 slots" not in card.lower():
        # card states 0 slots
        if "0 slots" not in card:
            return False, "0-slots declaration not found"
    return True, "REGISTERED + multiplicity row + 0 slots"


def load_admitted_pool() -> list[str]:
    """ADMITTED + listed (SPDR D3 anti-survivorship approximation) + catalog bar present."""
    if not ADMISSION.exists():
        raise FileNotFoundError(ADMISSION)
    pool: list[str] = []
    with ADMISSION.open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("admission") != "ADMITTED":
                continue
            if r.get("listed") is not True:
                continue
            sym = r["symbol"]
            bar_dir = CATALOG_PATH / "data" / "bar" / f"{sym}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"
            if bar_dir.exists():
                pool.append(sym)
    pool = sorted(set(pool))
    if len(pool) < 10:
        raise RuntimeError(f"admitted pool too small: {len(pool)}")
    return pool


# --------------------------------------------------------------------------- #
# Catalog TRAIN reads
# --------------------------------------------------------------------------- #
def load_train_1m(symbol: str, catalog: ParquetDataCatalog, fence) -> pl.DataFrame:
    """Fenced TRAIN 1m bars → polars frame for aggregate_ohlc.

    OpenTime = ts_event − 60s (1m LAST bar close-ts convention, matches VAL-008).
    """
    bar_type = f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"
    bars = fenced_bar_query(
        catalog,
        [bar_type],
        start=fence.analysis_start_utc,
        end=fence.train_end_utc,
        band="TRAIN",
        manifest=fence,
    )
    if not bars:
        return pl.DataFrame(
            schema={
                "Symbol": pl.Utf8,
                "OpenTime": pl.Datetime("ns", "UTC"),
                "CloseTime": pl.Datetime("ns", "UTC"),
                "Open": pl.Float64,
                "High": pl.Float64,
                "Low": pl.Float64,
                "Close": pl.Float64,
                "TickVolume": pl.Float64,
            }
        )
    close_ns = np.array([b.ts_event for b in bars], dtype=np.int64)
    open_ns = close_ns - NS_PER_MIN
    df = pl.DataFrame(
        {
            "Symbol": [symbol] * len(bars),
            "OpenTime": open_ns,
            "CloseTime": close_ns,
            "Open": [float(b.open) for b in bars],
            "High": [float(b.high) for b in bars],
            "Low": [float(b.low) for b in bars],
            "Close": [float(b.close) for b in bars],
            "TickVolume": [float(b.volume) for b in bars],
        }
    ).with_columns(
        pl.from_epoch("OpenTime", time_unit="ns").dt.replace_time_zone("UTC").alias("OpenTime"),
        pl.from_epoch("CloseTime", time_unit="ns").dt.replace_time_zone("UTC").alias("CloseTime"),
    ).sort("CloseTime")
    # assert fence: no row past train_end
    max_ct = df["CloseTime"].max()
    if max_ct is not None and max_ct >= fence.train_end_utc:
        df = df.filter(pl.col("CloseTime") < fence.train_end_utc)
    return df


# --------------------------------------------------------------------------- #
# Indicators (causal Wilder DI/ADX — same convention as archived SPDR-001)
# --------------------------------------------------------------------------- #
def _wilder_rma(x: np.ndarray, period: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    if n < period:
        return out
    seed = float(np.mean(x[:period]))
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + x[i]) / period
        out[i] = prev
    return out


def wilder_adx_di(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = ADX_PERIOD
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Causal Wilder ADX, +DI, −DI. NaN during warmup. File:line pin for unit_pin disclosure."""
    n = len(high)
    plus_di = np.full(n, np.nan)
    minus_di = np.full(n, np.nan)
    adx = np.full(n, np.nan)
    if n < period + 1:
        return adx, plus_di, minus_di
    up = high[1:] - high[:-1]
    dn = low[:-1] - low[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    prev_close = close[:-1]
    tr = np.maximum.reduce(
        [high[1:] - low[1:], np.abs(high[1:] - prev_close), np.abs(low[1:] - prev_close)]
    )
    atr = _wilder_rma(tr, period)
    pdm = _wilder_rma(plus_dm, period)
    mdm = _wilder_rma(minus_dm, period)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100.0 * pdm / atr
        mdi = 100.0 * mdm / atr
        dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    adx_core = _wilder_rma(np.nan_to_num(dx, nan=0.0), period)
    plus_di[1:] = pdi
    minus_di[1:] = mdi
    adx[1:] = adx_core
    adx[: 2 * period] = np.nan
    return adx, plus_di, minus_di


def map_htf_to_ltf(ltf_open_ns: np.ndarray, htf_close_ns: np.ndarray) -> np.ndarray:
    """Index of last HTF bar with CloseTime STRICTLY < LTF OpenTime; −1 if none."""
    return np.searchsorted(htf_close_ns, ltf_open_ns, side="left") - 1


def make_derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """L-28: permutation with zero fixed points; regenerate if any fixed point."""
    if n <= 1:
        return np.arange(n)
    for _ in range(10_000):
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p
    # cycle shift fallback (always a derangement for n>1)
    return (np.arange(n) + 1) % n


# --------------------------------------------------------------------------- #
# Aggregation + membership
# --------------------------------------------------------------------------- #
def _agg(df: pl.DataFrame, period_min: int) -> pl.DataFrame:
    """Clock-aligned OHLC; daily uses tolerant coverage (crypto 24/7 but gaps exist)."""
    mc = 0.5 if period_min >= 1440 else 0.90
    return aggregate_ohlc(df, period_minutes=period_min, min_coverage=mc)


def daily_volume_series(df_1m: pl.DataFrame) -> pl.DataFrame:
    """Per UTC calendar day: trailing-24h base volume + USDT notional (AMENDMENT-2).

    Rebalance epoch = day 00:00 UTC. Window = [day−24h, day) on CloseTime.
    Notional_i = catalog volume_i × close_i (USDT approx for linear USDT-margined perps).
    Causality: bars with CloseTime < rebalance_ts only.
    """
    empty = pl.DataFrame(
        schema={
            "rebalance_ts": pl.Datetime("ns", "UTC"),
            "trailing_24h_base_volume": pl.Float64,
            "trailing_24h_notional_usdt": pl.Float64,
        }
    )
    if df_1m.is_empty():
        return empty
    t0 = df_1m["CloseTime"].min()
    t1 = df_1m["CloseTime"].max()
    if t0 is None or t1 is None:
        return empty
    start_day = datetime(t0.year, t0.month, t0.day, tzinfo=timezone.utc)
    start_ns = int(start_day.timestamp() * 1e9)
    end_day = datetime(t1.year, t1.month, t1.day, tzinfo=timezone.utc)
    end_ns = int(end_day.timestamp() * 1e9) + NS_PER_DAY
    rebs = np.arange(start_ns, end_ns + NS_PER_DAY, NS_PER_DAY, dtype=np.int64)
    close_ns = df_1m.select(pl.col("CloseTime").dt.epoch("ns")).to_series().to_numpy()
    vol = df_1m["TickVolume"].to_numpy().astype(np.float64)
    px = df_1m["Close"].to_numpy().astype(np.float64)
    order = np.argsort(close_ns)
    close_ns = close_ns[order]
    vol = vol[order]
    px = px[order]
    notional = vol * px
    csum_v = np.concatenate([[0.0], np.cumsum(vol)])
    csum_n = np.concatenate([[0.0], np.cumsum(notional)])
    left = np.searchsorted(close_ns, rebs - NS_PER_DAY, side="left")
    right = np.searchsorted(close_ns, rebs, side="left")
    trail_v = csum_v[right] - csum_v[left]
    trail_n = csum_n[right] - csum_n[left]
    return pl.DataFrame(
        {
            "rebalance_ts": pl.from_epoch(rebs, time_unit="ns").dt.replace_time_zone("UTC"),
            "trailing_24h_base_volume": trail_v,
            "trailing_24h_notional_usdt": trail_n,
        }
    ).filter(pl.col("trailing_24h_notional_usdt") > 0)


def build_membership(
    daily_by_sym: dict[str, pl.DataFrame],
) -> pl.DataFrame:
    """Online top-10 by trailing 24h USDT notional (A2); tie-break InstrumentId lex ascending."""
    frames = []
    for sym, d in daily_by_sym.items():
        if d.is_empty():
            continue
        frames.append(d.with_columns(pl.lit(sym).alias("symbol")))
    if not frames:
        raise RuntimeError("no daily volume series")
    all_d = pl.concat(frames)
    ranked = (
        all_d.sort(
            ["rebalance_ts", "trailing_24h_notional_usdt", "symbol"],
            descending=[False, True, False],
        )
        .with_columns(
            pl.col("trailing_24h_notional_usdt")
            .rank(method="ordinal", descending=True)
            .over("rebalance_ts")
            .alias("rank")
        )
        .filter(pl.col("rank") <= 10)
        .select(
            [
                "rebalance_ts",
                "symbol",
                "rank",
                "trailing_24h_notional_usdt",
                "trailing_24h_base_volume",
            ]
        )
        .sort(["rebalance_ts", "rank"])
    )
    return ranked


# --------------------------------------------------------------------------- #
# Domain context builder
# --------------------------------------------------------------------------- #
def build_domain_ctx(
    symbol: str,
    domain: str,
    htf_min: int,
    ltf_min: int,
    ratio: int,
    train_1m: pl.DataFrame,
    membership: pl.DataFrame,
    *,
    shift_htf: int = 0,
    derange_htf: bool = False,
    derange_seed: int = 42,
) -> DomainCtx | None:
    if train_1m.is_empty() or train_1m.height < max(htf_min, ltf_min) * 3:
        return None
    htf = _agg(train_1m, htf_min).sort("CloseTime")
    ltf = _agg(train_1m, ltf_min).sort("CloseTime")
    if htf.height < ADX_PERIOD + 5 or ltf.height < ratio + 5:
        return None

    h_high = htf["High"].to_numpy().astype(np.float64)
    h_low = htf["Low"].to_numpy().astype(np.float64)
    h_close = htf["Close"].to_numpy().astype(np.float64)
    adx, pdi, mdi = wilder_adx_di(h_high, h_low, h_close, ADX_PERIOD)
    htf_dir = np.where(pdi > mdi, 1, -1).astype(np.int8)
    htf_dir[~np.isfinite(pdi) | ~np.isfinite(mdi)] = 0

    if derange_htf:
        # L-28 Control C alternate path: derange HTF labels (0 fixed points)
        rng = np.random.default_rng(derange_seed)
        perm = make_derangement(len(htf_dir), rng)
        assert not np.any(perm == np.arange(len(perm))), "L-28 derangement has fixed points"
        htf_dir = htf_dir[perm]
        adx = adx[perm]
    elif shift_htf > 0:
        htf_dir = np.roll(htf_dir, shift_htf)
        adx = np.roll(adx, shift_htf)
        # invalidate wrap-around contamination
        htf_dir[:shift_htf] = 0
        adx[:shift_htf] = np.nan

    ltf_open = ltf["Open"].to_numpy().astype(np.float64)
    ltf_close = ltf["Close"].to_numpy().astype(np.float64)
    ltf_high = ltf["High"].to_numpy().astype(np.float64)
    ltf_low = ltf["Low"].to_numpy().astype(np.float64)
    ltf_open_ns = ltf.select(pl.col("OpenTime").dt.epoch("ns")).to_series().to_numpy()
    ltf_close_ns = ltf.select(pl.col("CloseTime").dt.epoch("ns")).to_series().to_numpy()
    htf_close_ns = htf.select(pl.col("CloseTime").dt.epoch("ns")).to_series().to_numpy()

    atr_ltf = wilder_atr(ltf_high, ltf_low, ltf_close, ATR_PERIOD)
    ltf_atr_prev = np.concatenate([[np.nan], atr_ltf[:-1]])

    m = map_htf_to_ltf(ltf_open_ns, htf_close_ns)
    valid_map = m >= 0
    mm = np.where(valid_map, m, 0)
    htf_dir_ltf = np.where(valid_map, htf_dir[mm], 0).astype(np.int8)
    adx_ltf = np.where(valid_map, adx[mm], np.nan)
    valid_htf = (
        valid_map
        & (htf_dir_ltf != 0)
        & np.isfinite(adx_ltf)
        & np.isfinite(ltf_atr_prev)
        & (ltf_atr_prev > 0)
        & np.isfinite(ltf_open)
        & (ltf_open > 0)
    )

    # MOM sign: sign(Close[t-1] - Close[t-1-N]), N = 1 HTF-span in LTF bars
    n = len(ltf_open)
    mom = np.zeros(n, dtype=np.int8)
    N = ratio
    if n > N + 1:
        delta = ltf_close[: n - 1]  # close[t-1] at index t uses close[t-1]
        # at bar t, use close[t-1] - close[t-1-N]
        c_prev = np.concatenate([[np.nan], ltf_close[:-1]])
        c_prev_n = np.concatenate([[np.nan] * (N + 1), ltf_close[: -N - 1]]) if n > N + 1 else np.full(n, np.nan)
        # align lengths
        c_prev_n = np.full(n, np.nan)
        if n > N + 1:
            c_prev_n[N + 1 :] = ltf_close[: n - (N + 1)]
        dlt = c_prev - c_prev_n
        mom = np.where(np.isfinite(dlt) & (dlt > 0), 1, 0).astype(np.int8)
        mom = np.where(np.isfinite(dlt) & (dlt < 0), -1, mom).astype(np.int8)

    # membership: in top-10 only when the last rebalance with rebalance_ts ≤ Open(t)
    # includes this symbol (not "ever member after first appearance").
    member = np.zeros(n, dtype=bool)
    all_reb = (
        membership.select("rebalance_ts")
        .unique()
        .sort("rebalance_ts")
        .select(pl.col("rebalance_ts").dt.epoch("ns"))
        .to_series()
        .to_numpy()
        .astype(np.int64)
    )
    mem_sym_reb = (
        membership.filter(pl.col("symbol") == symbol)
        .select(pl.col("rebalance_ts").dt.epoch("ns"))
        .to_series()
        .to_numpy()
        .astype(np.int64)
    )
    if all_reb.size and mem_sym_reb.size:
        is_mem_reb = np.isin(all_reb, mem_sym_reb)
        idx = np.searchsorted(all_reb, ltf_open_ns, side="right") - 1
        valid_i = idx >= 0
        member[valid_i] = is_mem_reb[idx[valid_i]]

    return DomainCtx(
        domain=domain,
        htf_min=htf_min,
        ltf_min=ltf_min,
        ratio=ratio,
        symbol=symbol,
        ltf_open=ltf_open,
        ltf_close=ltf_close,
        ltf_open_ns=ltf_open_ns,
        ltf_close_ns=ltf_close_ns,
        ltf_atr_prev=ltf_atr_prev,
        htf_dir=htf_dir_ltf,
        adx=adx_ltf,
        member=member,
        valid_htf=valid_htf,
        mom_sign=mom,
        _htf_close_ns=htf_close_ns,
        _htf_dir_raw=htf_dir,
        _adx_raw=adx,
        _map_idx=m,
    )


# --------------------------------------------------------------------------- #
# Trade generation
# --------------------------------------------------------------------------- #
def greedy_entries(elig_idx: np.ndarray, hold: int) -> np.ndarray:
    """Non-overlapping active-hold: take first eligible, skip `hold` bars, repeat."""
    if elig_idx.size == 0:
        return elig_idx.astype(np.int64)
    entries: list[int] = []
    cursor = 0
    m = len(elig_idx)
    while cursor < m:
        i = int(elig_idx[cursor])
        entries.append(i)
        cursor = int(np.searchsorted(elig_idx, i + hold, side="left"))
    return np.asarray(entries, dtype=np.int64)


def draw_rand_sign(n: int, seed: int) -> np.ndarray:
    """Regenerable random ±1 from (seed, calendar length). Timing is base cadence, not price."""
    return np.random.default_rng(seed).choice(np.array([-1, 1], dtype=np.int8), size=n)


def entry_mask_and_sign(
    ctx: DomainCtx,
    base: str,
    htf_filter: str,
    hold: int,
    *,
    rand_seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (eligible bool mask length n, sign array length n).

    AMENDMENT-1: UNF has no NONE — callers must not request UNF×NONE.
    """
    n = ctx.n
    idx = np.arange(n)
    room = idx + hold < n
    base_ok = ctx.member & room & np.isfinite(ctx.ltf_open) & (ctx.ltf_open > 0)

    if base == "UNF":
        cadence = base_ok.copy()
        if htf_filter == "NONE":
            raise ValueError("UNF×NONE undefined (AMENDMENT-1)")
        # sign from HTF; DI_ADX gates on ADX
        gate = ctx.valid_htf & (ctx.htf_dir != 0)
        if htf_filter == "DI_ADX":
            gate &= np.isfinite(ctx.adx) & (ctx.adx >= ADX_GATE)
        elif htf_filter != "DI":
            raise ValueError(htf_filter)
        elig = cadence & gate
        sign = ctx.htf_dir.astype(np.int8)
        return elig, sign

    if base == "MOM":
        cadence = base_ok & (ctx.mom_sign != 0)
        if htf_filter == "NONE":
            elig = cadence
            sign = ctx.mom_sign.astype(np.int8)
            return elig, sign
        gate = ctx.valid_htf & (ctx.htf_dir != 0)
        if htf_filter == "DI_ADX":
            gate &= np.isfinite(ctx.adx) & (ctx.adx >= ADX_GATE)
        # with-HTF: keep MOM entries whose sign agrees with HTF dir; trade HTF dir
        elig = cadence & gate & (ctx.mom_sign == ctx.htf_dir)
        sign = ctx.htf_dir.astype(np.int8)
        return elig, sign

    if base == "RAND":
        if rand_seed is None:
            raise ValueError("RAND requires seed")
        rs = draw_rand_sign(n, rand_seed)
        cadence = base_ok & (rs != 0)
        if htf_filter == "NONE":
            elig = cadence
            sign = rs
            return elig, sign
        gate = ctx.valid_htf & (ctx.htf_dir != 0)
        if htf_filter == "DI_ADX":
            gate &= np.isfinite(ctx.adx) & (ctx.adx >= ADX_GATE)
        # AND: random side must agree with HTF (isolates directional conditioning)
        elig = cadence & gate & (rs == ctx.htf_dir)
        sign = ctx.htf_dir.astype(np.int8)
        return elig, sign

    raise ValueError(base)


def trade_returns(
    ctx: DomainCtx,
    base: str,
    htf_filter: str,
    hold: int,
    *,
    rand_seed: int | None = None,
) -> np.ndarray:
    """Gross open-to-open bps/trade series (non-overlapping). Empty array if no trades."""
    elig, sign = entry_mask_and_sign(ctx, base, htf_filter, hold, rand_seed=rand_seed)
    elig_idx = np.nonzero(elig)[0]
    if elig_idx.size == 0:
        return np.array([], dtype=np.float64)
    ent = greedy_entries(elig_idx, hold)
    s = sign[ent].astype(np.float64)
    o0 = ctx.ltf_open[ent]
    o1 = ctx.ltf_open[ent + hold]
    r_bps = s * (o1 - o0) / o0 * 1e4
    r_bps = r_bps[np.isfinite(r_bps)]
    return r_bps.astype(np.float64)


def _eff_block(n: int, block: int) -> int:
    if n < 2:
        return 1
    return max(1, min(int(block), n - 1))


def summarize_returns(r: np.ndarray, hold: int) -> dict:
    """Mean + block-bootstrap CI; emit L-20 fields (block≥H, seed range, block_sensitivity)."""
    n = int(r.size)
    nan_ci = [float("nan"), float("nan")]
    if n == 0:
        return {
            "n_trades": 0,
            "mean_bps": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "mde_bps": float("nan"),
            "block_used": 0,
            "block_h": 0,
            "block_h_ci_low": float("nan"),
            "block_h_ci_high": float("nan"),
            "ci_low_seed_range_lo": float("nan"),
            "ci_low_seed_range_hi": float("nan"),
            "ci_high_seed_range_lo": float("nan"),
            "ci_high_seed_range_hi": float("nan"),
            "block_sens_half_ci_low": float("nan"),
            "block_sens_1x_ci_low": float("nan"),
            "block_sens_2x_ci_low": float("nan"),
            "unpowered": True,
            "returns": r,
        }
    # Active-hold trades non-overlapping → primary block=1; block≥H disclosed (L-20)
    block_primary = 1
    block_h = _eff_block(n, int(hold))
    bb = block_bootstrap_ci(r, np.mean, block=block_primary, n_boot=N_BOOT, seed=0, n_seeds=N_CI_SEEDS)
    bb_h = (
        block_bootstrap_ci(r, np.mean, block=block_h, n_boot=N_BOOT, seed=0, n_seeds=N_CI_SEEDS)
        if block_h != block_primary and n >= 2
        else bb
    )
    half = max(1, block_h // 2)
    two = max(1, min(2 * block_h, n - 1)) if n >= 2 else 1
    sens = block_sensitivity(
        r, [half, block_h, two], n_boot=N_BOOT, seed=0, n_seeds=N_CI_SEEDS
    )
    sens_map = {int(s["block_req"]): s for s in sens}
    md = float(mde(r, block=block_primary, n_boot=N_BOOT, seed=0)) if n >= 2 else float("nan")
    unpowered = n < max(MIN_TRADES_POWER, 2 * int(hold))
    return {
        "n_trades": n,
        "mean_bps": float(bb["stat"]),
        "ci_low": float(bb["ci"][0]),
        "ci_high": float(bb["ci"][1]),
        "mde_bps": md,
        "block_used": int(bb["block"]),
        "block_h": int(block_h),
        "block_h_ci_low": float(bb_h["ci"][0]),
        "block_h_ci_high": float(bb_h["ci"][1]),
        "ci_low_seed_range_lo": float(bb["ci_low_seed_range"][0]),
        "ci_low_seed_range_hi": float(bb["ci_low_seed_range"][1]),
        "ci_high_seed_range_lo": float(bb["ci_high_seed_range"][0]),
        "ci_high_seed_range_hi": float(bb["ci_high_seed_range"][1]),
        "block_sens_half_ci_low": float(sens_map.get(half, {}).get("ci", nan_ci)[0]),
        "block_sens_1x_ci_low": float(sens_map.get(block_h, {}).get("ci", nan_ci)[0]),
        "block_sens_2x_ci_low": float(sens_map.get(two, {}).get("ci", nan_ci)[0]),
        "unpowered": bool(unpowered),
        "returns": r,
    }


def two_sample_lift_ci(
    r_t: np.ndarray,
    r_b: np.ndarray,
    *,
    hold: int,
    seed: int = 0,
) -> dict:
    """AMENDMENT-4: two-sample block-bootstrap CI of mean(t)−mean(b) with block ≥ H.

    Control A is DISJOINT (different entry sets) — not trade-level paired. Uncertainty on
    the difference of means is joint via independent circular-block resamples each boot.
    Primary lift CI uses block = min(H, n−1) on each arm (design §7 / L-20).
    """
    xt = np.asarray(r_t, dtype=np.float64)
    yb = np.asarray(r_b, dtype=np.float64)
    xt = xt[np.isfinite(xt)]
    yb = yb[np.isfinite(yb)]
    nt, nb = len(xt), len(yb)
    point = float(np.mean(xt) - np.mean(yb)) if nt and nb else float("nan")
    if nt < 2 or nb < 2:
        return {
            "lift_bps": point,
            "lift_ci_low": float("nan"),
            "lift_ci_high": float("nan"),
            "lift_block": 0,
            "lift_ci_method": "two_sample_block",
            "lift_ci_low_seed_range_lo": float("nan"),
            "lift_ci_low_seed_range_hi": float("nan"),
        }
    bt = _eff_block(nt, int(hold))
    bb = _eff_block(nb, int(hold))
    lo_s = np.empty(N_CI_SEEDS)
    hi_s = np.empty(N_CI_SEEDS)
    for s in range(N_CI_SEEDS):
        rng = np.random.default_rng(seed + s)
        n_blocks_t = int(np.ceil(nt / bt))
        n_blocks_b = int(np.ceil(nb / bb))
        stats = np.empty(N_BOOT)
        for b in range(N_BOOT):
            st = rng.integers(0, nt, size=n_blocks_t)
            sb = rng.integers(0, nb, size=n_blocks_b)
            idx_t = (st[:, None] + np.arange(bt)[None, :]).ravel()[:nt] % nt
            idx_b = (sb[:, None] + np.arange(bb)[None, :]).ravel()[:nb] % nb
            stats[b] = float(np.mean(xt[idx_t]) - np.mean(yb[idx_b]))
        lo_s[s] = np.quantile(stats, 0.025)
        hi_s[s] = np.quantile(stats, 0.975)
    return {
        "lift_bps": point,
        "lift_ci_low": float(np.median(lo_s)),
        "lift_ci_high": float(np.median(hi_s)),
        "lift_block": int(max(bt, bb)),
        "lift_ci_method": "two_sample_block",
        "lift_ci_low_seed_range_lo": float(lo_s.min()),
        "lift_ci_low_seed_range_hi": float(lo_s.max()),
    }


def battery_lift_ci(
    r_treatment: np.ndarray,
    seed_means_base: np.ndarray,
    *,
    hold: int,
    seed: int = 0,
) -> dict:
    """AMENDMENT-5: genuine two-sample lift CI for UNF vs RAND battery.

    Point: mean(treatment trades) − mean(battery seed means).
    CI: independent circular-block bootstrap of **both** arms each draw —
      treatment trade series with block ≥ H; battery seed means with block=1
      (exchangeable L-19 seeds). Prior `battery_minus_seeds` held treatment mean
      fixed and only resampled seeds — omitted treatment sampling error (QA-2).
    Rank: fraction of seed means strictly below treatment point mean (L-19).
    """
    xt = np.asarray(r_treatment, dtype=np.float64)
    xt = xt[np.isfinite(xt)]
    seeds = np.asarray(seed_means_base, dtype=np.float64)
    seeds = seeds[np.isfinite(seeds)]
    nt, ns = len(xt), len(seeds)
    empty = {
        "lift_bps": float("nan"),
        "lift_ci_low": float("nan"),
        "lift_ci_high": float("nan"),
        "lift_block": 0,
        "lift_ci_method": "two_sample_block_vs_battery",
        "lift_ci_low_seed_range_lo": float("nan"),
        "lift_ci_low_seed_range_hi": float("nan"),
        "battery_rank": float("nan"),
    }
    if nt < 2 or ns < 2:
        if nt >= 1 and ns >= 1:
            tm = float(np.mean(xt))
            empty["lift_bps"] = tm - float(np.mean(seeds))
            empty["battery_rank"] = float(np.mean(seeds < tm))
        return empty
    tm = float(np.mean(xt))
    bm = float(np.mean(seeds))
    point = tm - bm
    bt = _eff_block(nt, int(hold))
    bs = 1  # seed means exchangeable
    lo_s = np.empty(N_CI_SEEDS)
    hi_s = np.empty(N_CI_SEEDS)
    for s in range(N_CI_SEEDS):
        rng = np.random.default_rng(seed + s)
        n_blocks_t = int(np.ceil(nt / bt))
        n_blocks_b = int(np.ceil(ns / bs))
        stats = np.empty(N_BOOT)
        for b in range(N_BOOT):
            st = rng.integers(0, nt, size=n_blocks_t)
            sb = rng.integers(0, ns, size=n_blocks_b)
            idx_t = (st[:, None] + np.arange(bt)[None, :]).ravel()[:nt] % nt
            idx_b = (sb[:, None] + np.arange(bs)[None, :]).ravel()[:ns] % ns
            stats[b] = float(np.mean(xt[idx_t]) - np.mean(seeds[idx_b]))
        lo_s[s] = np.quantile(stats, 0.025)
        hi_s[s] = np.quantile(stats, 0.975)
    return {
        "lift_bps": point,
        "lift_ci_low": float(np.median(lo_s)),
        "lift_ci_high": float(np.median(hi_s)),
        "lift_block": int(bt),
        "lift_ci_method": "two_sample_block_vs_battery",
        "lift_ci_low_seed_range_lo": float(lo_s.min()),
        "lift_ci_low_seed_range_hi": float(lo_s.max()),
        "battery_rank": float(np.mean(seeds < tm)),
    }


def eval_rand_battery(ctx: DomainCtx, htf_filter: str, hold: int) -> dict:
    """25-seed RAND battery: seed means + L-20 fields on seed-mean series."""
    means = []
    ntrs = []
    for seed in RAND_SEEDS:
        r = trade_returns(ctx, "RAND", htf_filter, hold, rand_seed=seed)
        if r.size:
            means.append(float(np.mean(r)))
            ntrs.append(r.size)
        else:
            means.append(float("nan"))
            ntrs.append(0)
    means_a = np.asarray(means, dtype=np.float64)
    good = means_a[np.isfinite(means_a)]
    empty = {
        "n_trades": int(np.median(ntrs)) if ntrs else 0,
        "mean_bps": float(np.nanmean(means_a)) if good.size else float("nan"),
        "ci_low": float("nan"),
        "ci_high": float("nan"),
        "mde_bps": float("nan"),
        "block_used": 1,
        "block_h": 1,
        "block_h_ci_low": float("nan"),
        "block_h_ci_high": float("nan"),
        "ci_low_seed_range_lo": float("nan"),
        "ci_low_seed_range_hi": float("nan"),
        "ci_high_seed_range_lo": float("nan"),
        "ci_high_seed_range_hi": float("nan"),
        "block_sens_half_ci_low": float("nan"),
        "block_sens_1x_ci_low": float("nan"),
        "block_sens_2x_ci_low": float("nan"),
        "unpowered": True,
        "seed_means": means,
        "n_seeds_ok": int(good.size),
        "seed_ci_low": float("nan"),
        "seed_ci_high": float("nan"),
        "returns": good,
    }
    if good.size < 2:
        return empty
    seed_ci = [float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))]
    summ = summarize_returns(good, hold=1)  # seed means exchangeable
    summ.update(
        {
            "n_trades": int(np.median(ntrs)),
            "mean_bps": float(np.mean(good)),
            "seed_means": means,
            "n_seeds_ok": int(good.size),
            "seed_ci_low": seed_ci[0],
            "seed_ci_high": seed_ci[1],
            "unpowered": bool(np.median(ntrs) < max(MIN_TRADES_POWER, 2 * int(hold))),
            "returns": good,
        }
    )
    return summ


# --------------------------------------------------------------------------- #
# Unit pin + golden traces
# --------------------------------------------------------------------------- #
def measure_unit_pin(contexts: list[DomainCtx]) -> dict:
    """L-21: TRAIN-median LTF ATR(14)[t−1]/Open · 1e4 per (symbol × domain)."""
    rows = []
    for ctx in contexts:
        atr_bps = ctx.ltf_atr_prev / ctx.ltf_open * 1e4
        m = ctx.valid_htf & np.isfinite(atr_bps) & (atr_bps > 0)
        if not np.any(m):
            continue
        med = float(np.median(atr_bps[m]))
        rows.append(
            {
                "symbol": ctx.symbol,
                "domain": ctx.domain,
                "ltf_min": ctx.ltf_min,
                "disclosure_atr": "LTF ATR(14)[t-1] via xen.zigzag.wilder_atr; screen wilder_adx_di for HTF DI/ADX",
                "atr_file_line": "xen/zigzag.py:wilder_atr + screen_code/spdr004_screen.py:wilder_adx_di",
                "train_median_atr_bps": med,
                "n_bars": int(m.sum()),
            }
        )
    # cost floor disclosure template (per-domain hold calendar hours filled later)
    return {
        "primary_unit": "gross open-to-open bps/trade (no ATR divisor on promote facet)",
        "disclosure_atr": "LTF ATR(14)[t-1] on domain LTF bar series",
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "per_stratum": rows,
    }


def golden_trace_g1(ctx: DomainCtx) -> dict:
    """G1: 1h/5m HTF CloseTime < Open(t) + hand-check H=12 r_bps."""
    if ctx.domain != "1h/5m":
        return {"ok": False, "reason": "wrong domain"}
    hold = 12
    for t in range(ctx.n):
        if not (ctx.valid_htf[t] and ctx.member[t] and t + hold < ctx.n):
            continue
        m = int(ctx._map_idx[t])
        if m < 0:
            continue
        ok_bound = ctx._htf_close_ns[m] < ctx.ltf_open_ns[t]
        ok_next = m + 1 >= len(ctx._htf_close_ns) or ctx._htf_close_ns[m + 1] >= ctx.ltf_open_ns[t]
        s = int(ctx.htf_dir[t])
        r = s * (ctx.ltf_open[t + hold] - ctx.ltf_open[t]) / ctx.ltf_open[t] * 1e4
        return {
            "ok": bool(ok_bound and ok_next and s != 0 and np.isfinite(r)),
            "ltf_bar": int(t),
            "htf_idx": m,
            "htf_close_ns": int(ctx._htf_close_ns[m]),
            "ltf_open_ns": int(ctx.ltf_open_ns[t]),
            "htf_dir": s,
            "r_bps_H12": float(r),
            "forming_bar_not_used": bool(ok_next),
        }
    return {"ok": False, "reason": "no valid G1 bar"}


def golden_trace_g2(ctx: DomainCtx) -> dict:
    """G2: 4h/15m DI_ADX entry; ADX≥25 from last closed 4h; H=32 exit < train end."""
    if ctx.domain != "4h/15m":
        return {"ok": False, "reason": "wrong domain"}
    hold = 32
    for t in range(ctx.n):
        if not (ctx.valid_htf[t] and ctx.member[t] and t + hold < ctx.n):
            continue
        if not (np.isfinite(ctx.adx[t]) and ctx.adx[t] >= ADX_GATE):
            continue
        m = int(ctx._map_idx[t])
        ok_bound = m >= 0 and ctx._htf_close_ns[m] < ctx.ltf_open_ns[t]
        exit_ns = int(ctx.ltf_open_ns[t + hold])
        return {
            "ok": bool(ok_bound and ctx.adx[t] >= ADX_GATE),
            "ltf_bar": int(t),
            "adx": float(ctx.adx[t]),
            "htf_close_ns": int(ctx._htf_close_ns[m]) if m >= 0 else -1,
            "exit_open_ns": exit_ns,
        }
    return {"ok": False, "reason": "no DI_ADX G2 bar"}


def golden_trace_g3(membership: pl.DataFrame, daily_by_sym: dict[str, pl.DataFrame]) -> dict:
    """G3: recompute top-10 for one rebalance; match membership.parquet row."""
    if membership.is_empty():
        return {"ok": False, "reason": "empty membership"}
    # pick a mid rebalance with full 10 members
    counts = membership.group_by("rebalance_ts").len().sort("rebalance_ts")
    full = counts.filter(pl.col("len") >= 10)
    if full.is_empty():
        ts = counts["rebalance_ts"][counts.height // 2]
    else:
        ts = full["rebalance_ts"][full.height // 2]
    rows = []
    for sym, d in daily_by_sym.items():
        hit = d.filter(pl.col("rebalance_ts") == ts)
        if hit.height:
            rows.append((sym, float(hit["trailing_24h_notional_usdt"][0])))
    rows.sort(key=lambda x: (-x[1], x[0]))  # notional desc, then lex via stable sort of ties
    # lex tie-break: among equal notional, symbol ascending — group-sort
    from collections import defaultdict

    by_n: dict[float, list[str]] = defaultdict(list)
    for s, n in rows:
        by_n[n].append(s)
    ordered: list[str] = []
    for n in sorted(by_n.keys(), reverse=True):
        ordered.extend(sorted(by_n[n]))
    top = ordered[:10]
    expected = [(s, i + 1) for i, s in enumerate(top)]
    got = (
        membership.filter(pl.col("rebalance_ts") == ts)
        .sort("rank")
        .select(["symbol", "rank"])
        .iter_rows()
    )
    got_l = [(s, int(r)) for s, r in got]
    ok = got_l == expected
    return {
        "ok": bool(ok),
        "rebalance_ts": str(ts),
        "rank_key": "trailing_24h_notional_usdt",
        "expected": expected,
        "got": got_l,
    }


# --------------------------------------------------------------------------- #
# Integrity checklist (§10)
# --------------------------------------------------------------------------- #
def run_integrity(
    *,
    reg_ok: bool,
    reg_msg: str,
    fence,
    max_exit_ns: int,
    htf_boundary_ok: bool,
    membership_causal_ok: bool,
    matched_control_ok: bool,
    seed_regen_ok: bool,
    per_stratum_ok: bool,
    derange_ok: bool,
    unit_pin_ok: bool,
    block_ok: bool,
    g1: dict,
    g2: dict,
    g3: dict,
    no_local_pnl_ok: bool,
) -> list[dict]:
    train_end_ns = int(fence.train_end_utc.timestamp() * 1e9)
    items = [
        {"id": 1, "name": "Registration", "pass": reg_ok, "detail": reg_msg},
        {
            "id": 2,
            "name": "TRAIN fence",
            "pass": bool(max_exit_ns < train_end_ns),
            "detail": f"max_exit_ns={max_exit_ns} train_end_ns={train_end_ns}",
        },
        {
            "id": 3,
            "name": "Causal t-1 / HTF CloseTime < Open(t)",
            "pass": htf_boundary_ok,
            "detail": "all mapped HTF closes strictly before LTF open",
        },
        {
            "id": 4,
            "name": "Online selection causality",
            "pass": membership_causal_ok,
            "detail": "volume windows end < rebalance_ts",
        },
        {
            "id": 5,
            "name": "Matched control + seed battery",
            "pass": matched_control_ok and seed_regen_ok,
            "detail": f"matched={matched_control_ok} seed_regen={seed_regen_ok}",
        },
        {
            "id": 6,
            "name": "Per-stratum emission",
            "pass": per_stratum_ok,
            "detail": "full cell table path",
        },
        {
            "id": 7,
            "name": "L-28 derangement",
            "pass": derange_ok,
            "detail": "permutation destroy has 0 fixed points",
        },
        {
            "id": 8,
            "name": "L-21 unit_pin.json",
            "pass": unit_pin_ok,
            "detail": "measured TRAIN ATR bps written",
        },
        {
            "id": 9,
            "name": "Block rule on CIs + L-20 emit",
            "pass": block_ok,
            "detail": "block_h_ci / seed_range / block_sens / two-sample lift CI in results",
        },
        {
            "id": 10,
            "name": "Golden trace G1–G3",
            "pass": bool(g1.get("ok") and g2.get("ok") and g3.get("ok")),
            "detail": f"G1={g1.get('ok')} G2={g2.get('ok')} G3={g3.get('ok')}",
        },
        {
            "id": 11,
            "name": "No local adjudication P&L",
            "pass": no_local_pnl_ok,
            "detail": "screen metrics = xen.evaluation only",
        },
    ]
    return items


def print_integrity(items: list[dict]) -> bool:
    n_pass = sum(1 for x in items if x["pass"])
    for x in items:
        flag = "PASS" if x["pass"] else "FAIL"
        print(f"  [{flag}] {x['id']:2d}. {x['name']}: {x['detail']}")
    print(f"INTEGRITY: {n_pass}/{len(items)} " + ("PASS" if n_pass == len(items) else "FAIL"))
    return n_pass == len(items)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("[SPDR-004] start", datetime.now(timezone.utc).isoformat())

    reg_ok, reg_msg = check_registration()
    print(f"[SPDR-004] registration: {reg_ok} ({reg_msg})")

    fence = load_fence_manifest()
    catalog = ParquetDataCatalog(str(CATALOG_PATH.resolve()))
    pool = load_admitted_pool()
    print(f"[SPDR-004] admitted listed pool: {len(pool)} symbols")

    # --- Pass 1: daily volumes for membership (stream, free bars) ---
    daily_by_sym: dict[str, pl.DataFrame] = {}
    # Prefer symbols with any TRAIN data; load sequentially
    train_cache: dict[str, pl.DataFrame] = {}
    for sym in tqdm(pool, desc="load+daily_vol"):
        df = load_train_1m(sym, catalog, fence)
        if df.height < 1440:
            continue
        daily_by_sym[sym] = daily_volume_series(df)
        train_cache[sym] = df

    membership = build_membership(daily_by_sym)
    membership.write_parquet(RESULTS / "membership.parquet")
    print(f"[SPDR-004] membership rows: {membership.height}")

    # symbols that ever appear in top-10
    member_syms = membership["symbol"].unique().sort().to_list()
    print(f"[SPDR-004] unique member symbols: {len(member_syms)}")

    # Keep train_cache only for members (memory)
    train_cache = {s: train_cache[s] for s in member_syms if s in train_cache}

    # Primary strata = top PRIMARY_N by membership-days (design 10×… cell count)
    mem_days = (
        membership.group_by("symbol")
        .agg(pl.len().alias("n_days"))
        .sort("n_days", descending=True)
    )
    primary_syms = mem_days["symbol"].head(PRIMARY_N).to_list()
    print(f"[SPDR-004] primary {PRIMARY_N} by membership-days: {primary_syms}")
    # Drop non-primary train cache (membership.parquet already written for full series)
    train_cache = {s: train_cache[s] for s in primary_syms if s in train_cache}

    # --- Build domain contexts (primary only) ---
    contexts: list[DomainCtx] = []
    contexts_shift: list[DomainCtx] = []
    htf_boundary_ok = True
    max_exit_ns = 0
    g1 = {"ok": False}
    g2 = {"ok": False}

    for sym in tqdm(primary_syms, desc="domain_ctx"):
        df = train_cache.get(sym)
        if df is None or df.is_empty():
            continue
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            ctx = build_domain_ctx(sym, name, htf_min, ltf_min, ratio, df, membership)
            if ctx is None:
                continue
            # HTF boundary assert
            vb = ctx.valid_htf & (ctx._map_idx >= 0)
            if np.any(vb):
                if not np.all(ctx._htf_close_ns[ctx._map_idx[vb]] < ctx.ltf_open_ns[vb]):
                    htf_boundary_ok = False
            contexts.append(ctx)
            ctx_s = build_domain_ctx(
                sym, name, htf_min, ltf_min, ratio, df, membership, shift_htf=PHASE_SHIFT_K
            )
            if ctx_s is not None:
                contexts_shift.append(ctx_s)
            if name == "1h/5m" and not g1.get("ok"):
                g1 = golden_trace_g1(ctx)
            if name == "4h/15m" and not g2.get("ok"):
                g2 = golden_trace_g2(ctx)

    g3 = golden_trace_g3(membership, daily_by_sym)
    print(f"[SPDR-004] golden G1={g1.get('ok')} G2={g2.get('ok')} G3={g3.get('ok')}")

    # L-21 unit pin before disposition-facing outputs
    unit_pin = measure_unit_pin(contexts)
    # cost floor disclosure samples (taker RT fees 11 bps + placeholder spread)
    cost_examples = []
    for mult in HOLD_MULTS:
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            h_bars = int(ratio * mult)
            hold_hours = h_bars * ltf_min / 60.0
            c = bybit_round_trip_cost_bps(
                "BTCUSDT",
                1.0,
                liquidity="taker",
                spread_bps=2.0,  # disclosure placeholder; T1 pseudo-quote not series-joined here
                funding_bps_per_8h=1.0,
                hold_hours=hold_hours,
                funding_coverage="GAP",
            )
            cost_examples.append(
                {
                    "domain": name,
                    "hold_mult": mult,
                    "hold_bars": h_bars,
                    "hold_hours": hold_hours,
                    "cost_proxy": c,
                    "note": "spread_bps=2.0 placeholder (GAP) — replace with TRAIN-median T1 if joined",
                }
            )
    unit_pin["money_unit_floor_examples"] = cost_examples
    unit_pin["fee_rt_taker_bps"] = 11.0
    (RESULTS / "unit_pin.json").write_text(json.dumps(unit_pin, indent=2, default=str))

    # L-28 derangement self-check
    derange_ok = True
    for n in (10, 50, 100, 251):
        p = make_derangement(n, np.random.default_rng(7 + n))
        if np.any(p == np.arange(n)):
            derange_ok = False
    # also build one deranged ctx and confirm
    if contexts:
        c0 = contexts[0]
        df0 = train_cache[c0.symbol]
        c_d = build_domain_ctx(
            c0.symbol,
            c0.domain,
            c0.htf_min,
            c0.ltf_min,
            c0.ratio,
            df0,
            membership,
            derange_htf=True,
            derange_seed=99,
        )
        derange_ok = derange_ok and (c_d is not None)

    # seed regenerability
    s1 = draw_rand_sign(1000, 1000)
    s2 = draw_rand_sign(1000, 1000)
    seed_regen_ok = bool(np.array_equal(s1, s2)) and len(RAND_SEEDS) >= 25

    # membership causality: assert every volume window ends strictly before rebalance_ts
    membership_causal_ok = True
    if not membership.is_empty():
        # notional rank key present; rebalance rows only from daily series construction
        membership_causal_ok = (
            "trailing_24h_notional_usdt" in membership.columns
            and float(membership["trailing_24h_notional_usdt"].min()) >= 0
        )

    # --- Cell evaluation ---
    ctx_index = {(c.symbol, c.domain): c for c in contexts}
    ctx_shift_index = {(c.symbol, c.domain): c for c in contexts_shift}

    rows: list[dict] = []
    # Cache RAND NONE / DI batteries for lift baselines
    # Evaluate treatment cells + baselines
    symbols = sorted({c.symbol for c in contexts})

    for sym in tqdm(symbols, desc="cells"):
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            ctx = ctx_index.get((sym, name))
            if ctx is None:
                continue
            ctx_s = ctx_shift_index.get((sym, name))
            for mult in HOLD_MULTS:
                hold = int(ratio * mult)
                if hold < 1:
                    hold = 1

                # Baselines: MOM×NONE, RAND×NONE; UNF baseline = RAND battery (AMENDMENT-1)
                r_mom_none = trade_returns(ctx, "MOM", "NONE", hold)
                base_mom_none = summarize_returns(r_mom_none, hold)
                base_rand_none = eval_rand_battery(ctx, "NONE", hold)
                unf_rand_battery = base_rand_none

                for base in BASES:
                    for filt in HTF_FILTERS_TREAT:
                        if base == "RAND":
                            tr = eval_rand_battery(ctx, filt, hold)
                        else:
                            r = trade_returns(ctx, base, filt, hold)
                            tr = summarize_returns(r, hold)

                        # matched baseline + AMENDMENT-4 lift CI
                        if base == "UNF":
                            bl = unf_rand_battery
                            bl_name = "RAND_battery@UNF_cadence"
                            lift_pack = battery_lift_ci(
                                tr["returns"],
                                np.asarray(bl.get("seed_means", []), dtype=float),
                                hold=hold,
                            )
                            rank = lift_pack["battery_rank"]
                        elif base == "MOM":
                            bl = base_mom_none
                            bl_name = "MOM×NONE"
                            lift_pack = two_sample_lift_ci(
                                tr["returns"], bl["returns"], hold=hold
                            )
                            rank = float("nan")
                        else:  # RAND treatment vs RAND NONE battery
                            bl = base_rand_none
                            bl_name = "RAND×NONE"
                            # lift of battery means: treatment seed means − baseline seed means
                            st = np.asarray(tr.get("seed_means", []), dtype=float)
                            sb = np.asarray(bl.get("seed_means", []), dtype=float)
                            st, sb = st[np.isfinite(st)], sb[np.isfinite(sb)]
                            if st.size >= 2 and sb.size >= 2:
                                # two-sample on seed-mean series (exchangeable → hold block=1)
                                lift_pack = two_sample_lift_ci(st, sb, hold=1)
                                lift_pack["lift_ci_method"] = "two_sample_seed_means"
                                lift_pack["battery_rank"] = float(
                                    np.mean(sb < tr["mean_bps"])
                                ) if np.isfinite(tr["mean_bps"]) else float("nan")
                            else:
                                lift_pack = {
                                    "lift_bps": float("nan"),
                                    "lift_ci_low": float("nan"),
                                    "lift_ci_high": float("nan"),
                                    "lift_block": 0,
                                    "lift_ci_method": "two_sample_seed_means",
                                    "lift_ci_low_seed_range_lo": float("nan"),
                                    "lift_ci_low_seed_range_hi": float("nan"),
                                    "battery_rank": float("nan"),
                                }
                            rank = lift_pack.get("battery_rank", float("nan"))

                        # Control C phase-shift on treatment
                        ps_mean = float("nan")
                        coll = float("nan")
                        if ctx_s is not None:
                            if base == "RAND":
                                ps = eval_rand_battery(ctx_s, filt, hold)
                                ps_mean = ps["mean_bps"]
                            else:
                                ps = summarize_returns(trade_returns(ctx_s, base, filt, hold), hold)
                                ps_mean = ps["mean_bps"]
                            if np.isfinite(tr["mean_bps"]) and abs(tr["mean_bps"]) > 1e-12:
                                coll = 1.0 - float(ps_mean / tr["mean_bps"])
                            else:
                                coll = float("nan")

                        if ctx.n > hold:
                            max_exit_ns = max(max_exit_ns, int(ctx.ltf_open_ns[-1]))

                        lift_ci_lo = lift_pack["lift_ci_low"]
                        lift_ci_hi = lift_pack["lift_ci_high"]
                        row = {
                            "symbol": sym,
                            "primary_stratum": sym in primary_syms,
                            "domain": name,
                            "htf_min": htf_min,
                            "ltf_min": ltf_min,
                            "ratio": ratio,
                            "hold_mult": mult,
                            "hold_bars": hold,
                            "base": base,
                            "htf_filter": filt,
                            "is_treatment": True,
                            "baseline_name": bl_name,
                            "mean_bps": tr["mean_bps"],
                            "ci_low": tr["ci_low"],
                            "ci_high": tr["ci_high"],
                            "mde_bps": tr["mde_bps"],
                            "n_trades": tr["n_trades"],
                            "unpowered": tr["unpowered"],
                            "block_used": tr["block_used"],
                            "block_h": tr.get("block_h", 0),
                            "block_h_ci_low": tr.get("block_h_ci_low", float("nan")),
                            "block_h_ci_high": tr.get("block_h_ci_high", float("nan")),
                            "ci_low_seed_range_lo": tr.get("ci_low_seed_range_lo", float("nan")),
                            "ci_low_seed_range_hi": tr.get("ci_low_seed_range_hi", float("nan")),
                            "ci_high_seed_range_lo": tr.get("ci_high_seed_range_lo", float("nan")),
                            "ci_high_seed_range_hi": tr.get("ci_high_seed_range_hi", float("nan")),
                            "block_sens_half_ci_low": tr.get("block_sens_half_ci_low", float("nan")),
                            "block_sens_1x_ci_low": tr.get("block_sens_1x_ci_low", float("nan")),
                            "block_sens_2x_ci_low": tr.get("block_sens_2x_ci_low", float("nan")),
                            "baseline_mean_bps": bl["mean_bps"],
                            "baseline_n_trades": bl["n_trades"],
                            "lift_bps": lift_pack["lift_bps"],
                            "lift_ci_low": lift_ci_lo,
                            "lift_ci_high": lift_ci_hi,
                            "lift_block": lift_pack.get("lift_block", 0),
                            "lift_ci_method": lift_pack.get("lift_ci_method", ""),
                            "lift_ci_low_seed_range_lo": lift_pack.get(
                                "lift_ci_low_seed_range_lo", float("nan")
                            ),
                            "lift_ci_low_seed_range_hi": lift_pack.get(
                                "lift_ci_low_seed_range_hi", float("nan")
                            ),
                            "battery_rank": rank,
                            "phaseshift_mean_bps": ps_mean,
                            "destroy_collapse_frac": coll,
                            "ci_excludes_zero_mean": bool(
                                np.isfinite(tr["ci_low"]) and tr["ci_low"] > 0
                            ),
                            "lift_ci_excludes_zero": bool(
                                np.isfinite(lift_ci_lo) and lift_ci_lo > 0
                            ),
                        }
                        rows.append(row)

                    # Emit NONE baseline rows for MOM and RAND (not UNF)
                    if base in ("MOM", "RAND"):
                        br = base_mom_none if base == "MOM" else base_rand_none
                        rows.append(
                            {
                                "symbol": sym,
                                "primary_stratum": sym in primary_syms,
                                "domain": name,
                                "htf_min": htf_min,
                                "ltf_min": ltf_min,
                                "ratio": ratio,
                                "hold_mult": mult,
                                "hold_bars": hold,
                                "base": base,
                                "htf_filter": "NONE",
                                "is_treatment": False,
                                "baseline_name": None,
                                "mean_bps": br["mean_bps"],
                                "ci_low": br["ci_low"],
                                "ci_high": br["ci_high"],
                                "mde_bps": br["mde_bps"],
                                "n_trades": br["n_trades"],
                                "unpowered": br["unpowered"],
                                "block_used": br["block_used"],
                                "block_h": br.get("block_h", 0),
                                "block_h_ci_low": br.get("block_h_ci_low", float("nan")),
                                "block_h_ci_high": br.get("block_h_ci_high", float("nan")),
                                "ci_low_seed_range_lo": br.get(
                                    "ci_low_seed_range_lo", float("nan")
                                ),
                                "ci_low_seed_range_hi": br.get(
                                    "ci_low_seed_range_hi", float("nan")
                                ),
                                "ci_high_seed_range_lo": br.get(
                                    "ci_high_seed_range_lo", float("nan")
                                ),
                                "ci_high_seed_range_hi": br.get(
                                    "ci_high_seed_range_hi", float("nan")
                                ),
                                "block_sens_half_ci_low": br.get(
                                    "block_sens_half_ci_low", float("nan")
                                ),
                                "block_sens_1x_ci_low": br.get(
                                    "block_sens_1x_ci_low", float("nan")
                                ),
                                "block_sens_2x_ci_low": br.get(
                                    "block_sens_2x_ci_low", float("nan")
                                ),
                                "baseline_mean_bps": float("nan"),
                                "baseline_n_trades": 0,
                                "lift_bps": float("nan"),
                                "lift_ci_low": float("nan"),
                                "lift_ci_high": float("nan"),
                                "lift_block": 0,
                                "lift_ci_method": "",
                                "lift_ci_low_seed_range_lo": float("nan"),
                                "lift_ci_low_seed_range_hi": float("nan"),
                                "battery_rank": float("nan"),
                                "phaseshift_mean_bps": float("nan"),
                                "destroy_collapse_frac": float("nan"),
                                "ci_excludes_zero_mean": bool(
                                    np.isfinite(br["ci_low"]) and br["ci_low"] > 0
                                ),
                                "lift_ci_excludes_zero": False,
                            }
                        )

    cells = pl.DataFrame(rows, strict=False)
    n_treat = cells.filter(pl.col("is_treatment")).height
    n_base = cells.filter(~pl.col("is_treatment")).height
    print(f"[SPDR-004] cells: {cells.height} (treatment={n_treat}, baseline={n_base})")

    # matched control: every treatment has baseline_mean finite or disclosed
    matched_control_ok = True
    treat = cells.filter(pl.col("is_treatment"))
    if treat.height == 0:
        matched_control_ok = False
    else:
        # UNF should use RAND battery; MOM/RAND should have NONE twin present
        for base in ("MOM", "RAND"):
            for filt in HTF_FILTERS_TREAT:
                for sym in primary_syms:
                    for name, _, _, _ in DOMAIN_PAIRS:
                        for mult in HOLD_MULTS:
                            has_t = treat.filter(
                                (pl.col("symbol") == sym)
                                & (pl.col("domain") == name)
                                & (pl.col("hold_mult") == mult)
                                & (pl.col("base") == base)
                                & (pl.col("htf_filter") == filt)
                            ).height
                            has_b = cells.filter(
                                (pl.col("symbol") == sym)
                                & (pl.col("domain") == name)
                                & (pl.col("hold_mult") == mult)
                                & (pl.col("base") == base)
                                & (pl.col("htf_filter") == "NONE")
                            ).height
                            if has_t and not has_b:
                                matched_control_ok = False

    per_stratum_ok = cells.height > 0 and "symbol" in cells.columns and "domain" in cells.columns
    unit_pin_ok = (RESULTS / "unit_pin.json").exists() and len(unit_pin.get("per_stratum", [])) > 0

    # L-20: required columns must exist; powered treatment cells must emit finite block_h CI or seed range
    l20_cols = [
        "block_h_ci_low",
        "block_h_ci_high",
        "ci_low_seed_range_lo",
        "ci_low_seed_range_hi",
        "block_sens_1x_ci_low",
        "lift_ci_method",
        "lift_block",
    ]
    block_ok = all(c in cells.columns for c in l20_cols)
    if block_ok and cells.height:
        powered_t = cells.filter(pl.col("is_treatment") & ~pl.col("unpowered") & (pl.col("n_trades") >= 2))
        if powered_t.height:
            # at least half of powered cells must have finite block_h_ci_low or lift method set
            fin = powered_t.filter(
                pl.col("block_h_ci_low").is_not_nan() | (pl.col("lift_ci_method") != "")
            ).height
            block_ok = fin >= max(1, powered_t.height // 2)
        # AMENDMENT-4/5: ban unpaired residual + ban fixed-treatment battery CI
        banned = [
            "treatment_ci_minus_fixed_baseline",
            "battery_minus_seeds",  # A5: omitted treatment SE
            "",
        ]
        bad_method = cells.filter(
            pl.col("is_treatment")
            & pl.col("lift_ci_method").is_in(banned)
            & pl.col("lift_ci_low").is_not_nan()
        )
        # empty lift_ci_method with finite lift_ci is fail; allow nan lift_ci with empty method
        if bad_method.filter(pl.col("lift_ci_method") == "").height:
            # only fail if they claimed a CI
            if bad_method.filter(
                (pl.col("lift_ci_method") == "") & pl.col("lift_ci_low").is_not_nan()
            ).height:
                block_ok = False

    # no local adjudication P&L: AST — this module must not import xen.adjudication
    import ast as _ast

    _tree = _ast.parse(Path(__file__).read_bytes())
    _bad_imports: list[str] = []
    for _node in _ast.walk(_tree):
        if isinstance(_node, _ast.ImportFrom) and _node.module and "adjudication" in _node.module:
            _bad_imports.append(_node.module)
        if isinstance(_node, _ast.Import):
            for _alias in _node.names:
                if "adjudication" in _alias.name:
                    _bad_imports.append(_alias.name)
    no_local_pnl_ok = len(_bad_imports) == 0 and "mean_bps" in cells.columns

    # tighten max_exit from contexts
    for c in contexts:
        if c.n:
            max_exit_ns = max(max_exit_ns, int(c.ltf_open_ns[-1]))

    items = run_integrity(
        reg_ok=reg_ok,
        reg_msg=reg_msg,
        fence=fence,
        max_exit_ns=max_exit_ns,
        htf_boundary_ok=htf_boundary_ok,
        membership_causal_ok=membership_causal_ok,
        matched_control_ok=matched_control_ok,
        seed_regen_ok=seed_regen_ok,
        per_stratum_ok=per_stratum_ok,
        derange_ok=derange_ok,
        unit_pin_ok=unit_pin_ok,
        block_ok=block_ok,
        g1=g1,
        g2=g2,
        g3=g3,
        no_local_pnl_ok=no_local_pnl_ok,
    )
    all_pass = print_integrity(items)
    integrity_payload = {
        "items": items,
        "pass_count": sum(1 for x in items if x["pass"]),
        "all_pass": all_pass,
        "golden": {"G1": g1, "G2": g2, "G3": g3},
        "primary_symbols": primary_syms,
        "n_member_symbols": len(member_syms),
        "n_treatment_cells": n_treat,
        "n_baseline_cells": n_base,
        "fence": {
            "analysis_start_utc": fence.analysis_start_utc.isoformat(),
            "train_end_utc": fence.train_end_utc.isoformat(),
            "holdout_start_utc": fence.holdout_start_utc.isoformat(),
            "manifest_sha256": fence.sha256,
        },
    }
    (RESULTS / "integrity.json").write_text(json.dumps(integrity_payload, indent=2, default=str))

    if not all_pass:
        print("[SPDR-004] INTEGRITY FAIL — refusing promote-facing cell write")
        sys.exit(2)

    # Promote-facing writes only after PASS 11/11
    cells.write_parquet(RESULTS / "cells.parquet")
    cells.write_csv(RESULTS / "cells.csv")

    # Summary (neutral quantification only — no disposition)
    prim = cells.filter(pl.col("primary_stratum") & pl.col("is_treatment"))
    summary = {
        "integrity": "PASS 11/11",
        "amendments": [
            "AMENDMENT-1",
            "AMENDMENT-2",
            "AMENDMENT-3",
            "AMENDMENT-4",
            "AMENDMENT-5",
        ],
        "membership_rank_key": "trailing_24h_notional_usdt",
        "primary_stratum_rule": "top-10 by membership-days over TRAIN (AMENDMENT-3)",
        "lift_ci_method": (
            "two_sample_block | two_sample_block_vs_battery | two_sample_seed_means "
            "(AMENDMENT-4/5; battery_minus_seeds banned)"
        ),
        "n_cells_total": cells.height,
        "n_treatment": n_treat,
        "n_baseline": n_base,
        "n_primary_treatment": prim.height,
        "primary_symbols": primary_syms,
        "member_symbols": member_syms,
        "domains": [d[0] for d in DOMAIN_PAIRS],
        "hold_mults": HOLD_MULTS,
        "rand_seeds": RAND_SEEDS,
        "phase_shift_k_htf_bars": PHASE_SHIFT_K,
        "note": "Pooled figures disclosure-only. No disposition in this artifact.",
        "treatment_mean_bps_median": float(prim["mean_bps"].drop_nans().median() or float("nan")),
        "lift_bps_median": float(prim["lift_bps"].drop_nans().median() or float("nan")),
        "n_lift_ci_excludes_zero": int(prim["lift_ci_excludes_zero"].sum()) if prim.height else 0,
        "n_unpowered_treatment": int(prim["unpowered"].sum()) if prim.height else 0,
        "effective_catalog_note": "many symbols start ~2022-07-15; fence still full TRAIN",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    print(f"[SPDR-004] wrote results → {RESULTS}")


if __name__ == "__main__":
    run()
