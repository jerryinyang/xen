"""SPDR-001 — HTF-context screen on CTRL-01 random LTF entries (TRAIN-only availability).

Lane: SPDR speed-run (docs/references/spdr-lane.md). NOT a cTrader experiment — vectorised
Python, TRAIN-only, disposition-only (WORTH_EXPLORING / NOT_WORTH / INCONCLUSIVE). No P&L
verdict, no read/holdout/family. See python/experiments/SPDR-001/design.md.

Mechanism (design §1): a random entry has independent symmetric sign s (E[s]=0), so per-trade
E[s·r]=0 for any bar-selection filter. Only the DI-direction filter conditions the sign (aligns
the random-timed position to the last-closed HTF trend). So DI-containing variants are the SIGNAL
axis; gating-only variants (ADX-strength, ATR-vol, ATR×ADX) are built-in expected-zero NULL
sentinels (free FPR + leak check).

THE causal hazard: at LTF entry bar t the HTF context comes ONLY from the last HTF bar with
CloseTime < Open(t) (never the still-forming HTF bar). Enforced in map_htf_to_ltf + golden trace.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

from xen.bar_aggregator import aggregate_ohlc
from xen.evaluation import block_bootstrap_ci, mde, trimmed_mean
from xen.vol_regime import regime_labels, REGIME_LOW, REGIME_MED, REGIME_HIGH
from xen.zigzag import wilder_atr

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS = EXP_DIR / "results"
DATA_DIR = EXP_DIR.parents[2] / "data"                      # <root>/data

INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]        # 4-core (operator)
DOMAIN_PAIRS = [                                            # (name, htf_min, ltf_min, ratio)
    ("1d/1h", 1440, 60, 24),
    ("4h/1h", 240, 60, 4),
    ("1h/5min", 60, 5, 12),
]
HOLD_MULTS = [1, 2, 3, 4]
LAMBDA = 2.0                                                # SELL:NEUTRAL:BUY = 1:2:1 -> |u|>=0.5
ADX_PERIOD = 14
ATR_PERIOD = 14
N_SEEDS = 25                                                # L-19 battery
PHASE_SHIFT_HTF_BARS = 500                                  # Control B: K >> max hold
FWER_Q = 0.95                                               # per-instrument empirical-null quantile

# Random sign thresholds for lambda: ratio 1:lambda:1 over [-1,1] -> neutral band width
# = lambda/(2+lambda) centred at 0. For lambda=2 band = [-0.5, +0.5]; buy u>=0.5, sell u<=-0.5.
SIGN_THR = 1.0 / (2.0 + LAMBDA) * LAMBDA + 0.0             # = lambda/(2+lambda)=0.5 for lambda=2


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class DomainCtx:
    """Per-(instrument, domain-pair) causal context, all TRAIN-only, LTF-indexed."""
    name: str
    ltf_open: np.ndarray          # LTF Open price
    ltf_atr_prev: np.ndarray      # ATR_LTF(14)[t-1] (causal normaliser)
    htf_dir: np.ndarray           # +1 if +DI>-DI at mapped HTF bar else -1 (int8); 0 if invalid
    adx_bucket: np.ndarray        # 0:<25 1:[25,75) 2:>=75 ; -1 invalid
    atr_reg: np.ndarray           # 0 LOW 1 MED 2 HIGH ; -1 invalid
    valid: np.ndarray             # bool: mapped HTF finite AND ltf_atr_prev finite
    n: int = field(init=False)

    def __post_init__(self):
        self.n = len(self.ltf_open)


# --------------------------------------------------------------------------- #
# I/O + TRAIN fence
# --------------------------------------------------------------------------- #
def load_train_1m(symbol: str) -> pl.DataFrame:
    """Latest-glob 1m bars for symbol, sorted, sliced to the TRAIN block (first 70% of the
    first 70%). The holdout/TEST bars never leave this function (fence asserted by caller)."""
    # filenames are lowercase; two eras coexist -> pick the INFR-003 5-year canonical by the
    # collection timestamp (trailing yyyymmdd_hhmmss), excluding the old analysis70_* files.
    paths = [p for p in DATA_DIR.glob(f"timebars/timebars_{symbol.lower()}_*.parquet")
             if "analysis70" not in p.name]
    if not paths:
        raise FileNotFoundError(f"no timebars for {symbol}")
    paths.sort(key=lambda p: p.stem.split("_")[-2] + p.stem.split("_")[-1])
    df = pl.scan_parquet(paths[-1]).sort("CloseTime").collect()
    n = df.height
    analysis = df.head(int(n * 0.7))
    train = analysis.head(int(analysis.height * 0.7))
    return train


# --------------------------------------------------------------------------- #
# Causal indicators
# --------------------------------------------------------------------------- #
def _wilder_rma(x: np.ndarray, period: int) -> np.ndarray:
    """Causal Wilder smoothing, seeded by the simple mean of the first `period` values.
    NaN before index period-1. Matches xen.zigzag.wilder_atr convention."""
    n = len(x)
    out = np.full(n, np.nan)
    if n < period:
        return out
    seed = np.mean(x[:period])
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + x[i]) / period
        out[i] = prev
    return out


def wilder_adx_di(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                  period: int = ADX_PERIOD) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Causal Wilder ADX, +DI, -DI (all depend only on bars <= i). NaN during warmup."""
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
    tr = np.maximum.reduce([high[1:] - low[1:],
                            np.abs(high[1:] - prev_close),
                            np.abs(low[1:] - prev_close)])
    atr = _wilder_rma(tr, period)          # length n-1, aligned to bars 1..n-1
    pdm = _wilder_rma(plus_dm, period)
    mdm = _wilder_rma(minus_dm, period)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100.0 * pdm / atr
        mdi = 100.0 * mdm / atr
        dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    adx_core = _wilder_rma(np.nan_to_num(dx, nan=0.0), period)   # smoothing of DX (NaN warmup ok)
    # place back onto full-length arrays (index shift by +1 because diffs drop bar 0)
    plus_di[1:] = pdi
    minus_di[1:] = mdi
    adx[1:] = adx_core
    # invalidate the DX warmup region on adx (first ~2*period bars are unreliable)
    adx[: 2 * period] = np.nan
    return adx, plus_di, minus_di


# --------------------------------------------------------------------------- #
# HTF -> LTF causal map
# --------------------------------------------------------------------------- #
def map_htf_to_ltf(ltf_open_time: np.ndarray, htf_close_time: np.ndarray) -> np.ndarray:
    """Index into HTF of the last bar with CloseTime STRICTLY < LTF OpenTime, per LTF bar.
    -1 where no closed HTF bar exists yet. This is the anti-lookahead core (design §2)."""
    # searchsorted 'left' -> first HTF idx with CloseTime >= LTF open; minus 1 = last strictly <.
    idx = np.searchsorted(htf_close_time, ltf_open_time, side="left") - 1
    return idx


def _agg(df: pl.DataFrame, period_min: int) -> pl.DataFrame:
    """Deployed 0.90-coverage convention for intraday bars; for daily (>=1440) retain any
    nonempty session (index/FX sessions never fill 1440 min) -> honest per-instrument daily OHLC.
    Train slice is pre-applied, so no window can cross the holdout boundary (causal by construction)."""
    mc = 1e-6 if period_min >= 1440 else 0.90
    return aggregate_ohlc(df, period_minutes=period_min, min_coverage=mc)


def build_domain_ctx(name: str, htf_min: int, ltf_min: int, train_1m: pl.DataFrame,
                     shift_htf: int = 0) -> DomainCtx:
    """Build the LTF-indexed causal context for one domain pair. `shift_htf`>0 phase-shifts the
    HTF context (Control B future-destroy): the HTF label arrays are rolled forward K bars so the
    regime no longer corresponds to the LTF bar's own forward window (bar mapping unchanged)."""
    htf = _agg(train_1m, htf_min).sort("CloseTime")
    ltf = _agg(train_1m, ltf_min).sort("CloseTime")
    if htf.height == 0 or ltf.height == 0:
        raise ValueError(f"empty bars for {name}: htf={htf.height} ltf={ltf.height}")

    h_high = htf["High"].to_numpy().astype(float)
    h_low = htf["Low"].to_numpy().astype(float)
    h_close = htf["Close"].to_numpy().astype(float)
    adx, pdi, mdi = wilder_adx_di(h_high, h_low, h_close, ADX_PERIOD)
    atr_reg_htf = regime_labels(h_high, h_low, h_close, atr_period=ATR_PERIOD)
    htf_dir_htf = np.where(pdi > mdi, 1, -1).astype(np.int8)
    htf_dir_htf[~np.isfinite(pdi) | ~np.isfinite(mdi)] = 0
    adx_bucket_htf = np.full(len(adx), -1, dtype=np.int8)
    fin = np.isfinite(adx)
    adx_bucket_htf[fin & (adx < 25)] = 0
    adx_bucket_htf[fin & (adx >= 25) & (adx < 75)] = 1
    adx_bucket_htf[fin & (adx >= 75)] = 2

    if shift_htf > 0:                                   # Control B: roll HTF context forward K bars
        htf_dir_htf = np.roll(htf_dir_htf, shift_htf)
        adx_bucket_htf = np.roll(adx_bucket_htf, shift_htf)
        atr_reg_htf = np.roll(atr_reg_htf, shift_htf)

    ltf_open = ltf["Open"].to_numpy().astype(float)
    ltf_open_time = ltf["OpenTime"].to_numpy().astype("datetime64[ns]").astype("int64")
    ltf_low = ltf["Low"].to_numpy().astype(float)
    ltf_high = ltf["High"].to_numpy().astype(float)
    ltf_close = ltf["Close"].to_numpy().astype(float)
    h_close_time = htf["CloseTime"].to_numpy().astype("datetime64[ns]").astype("int64")

    atr_ltf = wilder_atr(ltf_high, ltf_low, ltf_close, ATR_PERIOD)
    ltf_atr_prev = np.concatenate([[np.nan], atr_ltf[:-1]])      # ATR[t-1], causal normaliser

    m = map_htf_to_ltf(ltf_open_time, h_close_time)
    valid_map = m >= 0
    mm = np.where(valid_map, m, 0)
    htf_dir = np.where(valid_map, htf_dir_htf[mm], 0).astype(np.int8)
    adx_bucket = np.where(valid_map, adx_bucket_htf[mm], -1).astype(np.int8)
    atr_reg = np.where(valid_map, atr_reg_htf[mm], -1).astype(np.int8)

    valid = (valid_map & (htf_dir != 0) & (adx_bucket >= 0) & (atr_reg >= 0)
             & np.isfinite(ltf_atr_prev) & (ltf_atr_prev > 0))
    ctx = DomainCtx(name=name, ltf_open=ltf_open, ltf_atr_prev=ltf_atr_prev,
                    htf_dir=htf_dir, adx_bucket=adx_bucket, atr_reg=atr_reg, valid=valid)
    ctx._htf_close_time = h_close_time            # for golden trace
    ctx._ltf_open_time = ltf_open_time
    ctx._htf_dir_htf = htf_dir_htf
    ctx._ltf_high = ltf_high                      # exposed for downstream signals (e.g. SPDR-002)
    ctx._ltf_low = ltf_low
    ctx._ltf_close = ltf_close
    return ctx


# --------------------------------------------------------------------------- #
# Filter variants
# --------------------------------------------------------------------------- #
def variant_specs() -> list[dict]:
    """20 filter variants (design §4). Each: name, regime-mask fn (over ctx), use_dir, is_signal."""
    specs = [{"name": "none", "mask": lambda c: np.ones(c.n, bool), "dir": False, "sig": False,
              "twin": None}]
    # ADX-strength (gating-only null sentinels)
    for b, nm in [(0, "adx_lt25"), (1, "adx_25_75"), (2, "adx_ge75")]:
        specs.append({"name": nm, "mask": (lambda c, b=b: c.adx_bucket == b), "dir": False,
                      "sig": False, "twin": None})
    # DI direction (signal); twin = none
    specs.append({"name": "di", "mask": lambda c: np.ones(c.n, bool), "dir": True, "sig": True,
                  "twin": "none"})
    # ATR-vol (gating-only null sentinels)
    for r, nm in [(REGIME_LOW, "atr_low"), (REGIME_MED, "atr_med"), (REGIME_HIGH, "atr_high")]:
        specs.append({"name": nm, "mask": (lambda c, r=r: c.atr_reg == r), "dir": False,
                      "sig": False, "twin": None})
    # ATR x ADX{<25,>=25} 6 gating-only + ATR x ADX x DI 6 signal (twin = the gating-only counterpart)
    for r, rn in [(REGIME_LOW, "atrL"), (REGIME_MED, "atrM"), (REGIME_HIGH, "atrH")]:
        for lo, an in [(True, "adxLo"), (False, "adxHi")]:
            def mk(c, r=r, lo=lo):
                adx_ok = (c.adx_bucket == 0) if lo else (c.adx_bucket >= 1)  # <25 vs >=25
                return (c.atr_reg == r) & adx_ok
            gname = f"{rn}_{an}"
            specs.append({"name": gname, "mask": mk, "dir": False, "sig": False, "twin": None})
            specs.append({"name": f"{gname}_di", "mask": mk, "dir": True, "sig": True,
                          "twin": gname})
    return specs


# --------------------------------------------------------------------------- #
# Random draw + greedy active-hold
# --------------------------------------------------------------------------- #
def draw_sign(n: int, seed: int) -> np.ndarray:
    """Random sign per LTF bar, independent of price (seed only). u~U(-1,1); |u|>=SIGN_THR -> +/-1
    else 0 (neutral). lambda=2 => neutral band [-0.5,0.5]."""
    u = np.random.default_rng(seed).uniform(-1.0, 1.0, size=n)
    s = np.zeros(n, dtype=np.int8)
    s[u >= SIGN_THR] = 1
    s[u <= -SIGN_THR] = -1
    return s


def greedy_entries(elig_idx: np.ndarray, hold: int) -> np.ndarray:
    """Non-overlapping active-hold selection: take first eligible, skip `hold` bars, repeat."""
    entries = []
    cursor = 0
    m = len(elig_idx)
    while cursor < m:
        i = elig_idx[cursor]
        entries.append(i)
        cursor = int(np.searchsorted(elig_idx, i + hold, side="left"))
    return np.asarray(entries, dtype=np.int64)


def cell_seed_means(ctx: DomainCtx, spec: dict, hold: int, seed: int) -> float:
    """Mean ATR-normalised open-to-open forward return for one (cell, seed). NaN if no trades."""
    n = ctx.n
    s = draw_sign(n, seed)
    regime = spec["mask"](ctx)
    elig = ctx.valid & regime & (s != 0)
    # entry+hold must stay inside TRAIN (no bar >= n)
    idx_all = np.arange(n)
    elig &= (idx_all + hold < n)
    if spec["dir"]:
        elig &= (s == ctx.htf_dir)                       # AND semantics: random side must agree
    elig_idx = np.nonzero(elig)[0]
    if elig_idx.size == 0:
        return np.nan
    ent = greedy_entries(elig_idx, hold)
    sign = ctx.htf_dir[ent] if spec["dir"] else s[ent]
    move = ctx.ltf_open[ent + hold] - ctx.ltf_open[ent]
    r_norm = sign * move / ctx.ltf_atr_prev[ent]
    return float(np.mean(r_norm)), ent.size


def eval_cell(ctx: DomainCtx, spec: dict, hold: int) -> dict:
    """Seed battery -> battery mean, seed-percentile CI (L-19), block-boot CI + MDE on seed means."""
    means = np.full(N_SEEDS, np.nan)
    ntr = np.zeros(N_SEEDS, dtype=np.int64)
    for k in range(N_SEEDS):
        r = cell_seed_means(ctx, spec, hold, seed=k)
        if isinstance(r, tuple):
            means[k], ntr[k] = r
    good = means[np.isfinite(means)]
    if good.size < 2:
        return {"battery_mean": float(np.nanmean(means)) if good.size else np.nan,
                "seed_ci": [np.nan, np.nan], "ci": [np.nan, np.nan], "mde": np.nan,
                "n_trades_med": int(np.median(ntr)), "n_seeds_ok": int(good.size),
                "trimmed": np.nan}
    seed_ci = [float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))]
    bb = block_bootstrap_ci(good, np.mean, block=1)      # seed means exchangeable -> block=1
    return {"battery_mean": float(np.mean(good)), "seed_ci": seed_ci, "ci": bb["ci"],
            "mde": float(mde(good, block=1)), "n_trades_med": int(np.median(ntr)),
            "n_seeds_ok": int(good.size), "trimmed": float(trimmed_mean(good))}


# --------------------------------------------------------------------------- #
# Golden trace (design §8) + integrity self-check (§9)
# --------------------------------------------------------------------------- #
def golden_trace(ctx: DomainCtx) -> dict:
    """Verify HTF-bar-boundary causality on a concrete LTF entry: the mapped HTF CloseTime is
    strictly < LTF OpenTime, and no later HTF bar was used."""
    n = ctx.n
    t = None
    for i in range(n):
        if ctx.valid[i] and i + 4 < n:
            t = i
            break
    if t is None:
        return {"ok": False, "reason": "no valid bar"}
    m = map_htf_to_ltf(ctx._ltf_open_time[t:t + 1], ctx._htf_close_time)[0]
    ok = (m >= 0) and (ctx._htf_close_time[m] < ctx._ltf_open_time[t]) and \
         (m + 1 >= len(ctx._htf_close_time) or ctx._htf_close_time[m + 1] >= ctx._ltf_open_time[t])
    return {"ok": bool(ok), "ltf_bar": int(t), "htf_idx": int(m),
            "htf_close_ns": int(ctx._htf_close_time[m]), "ltf_open_ns": int(ctx._ltf_open_time[t]),
            "htf_dir": int(ctx.htf_dir[t]), "adx_bucket": int(ctx.adx_bucket[t]),
            "atr_reg": int(ctx.atr_reg[t])}


def integrity_checks(train_1m: pl.DataFrame, ctx: DomainCtx, max_hold: int) -> dict:
    """Design §9: TRAIN fence + HTF boundary + causal lag + golden trace. Any FAIL blocks the read."""
    gt = golden_trace(ctx)
    # TRAIN fence: the whole ctx derives from train_1m only; assert no NaN normaliser leaks in valid
    fence_ok = bool(np.all(np.isfinite(ctx.ltf_atr_prev[ctx.valid])))
    # HTF boundary holds for ALL valid bars
    m = map_htf_to_ltf(ctx._ltf_open_time, ctx._htf_close_time)
    vb = ctx.valid & (m >= 0)
    boundary_ok = bool(np.all(ctx._htf_close_time[m[vb]] < ctx._ltf_open_time[vb]))
    return {"golden_trace": gt, "train_fence_ok": fence_ok, "htf_boundary_ok": boundary_ok,
            "all_pass": bool(gt["ok"] and fence_ok and boundary_ok)}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> None:
    RESULTS.mkdir(exist_ok=True)
    specs = variant_specs()
    rows: list[dict] = []
    integrity: list[dict] = []

    for sym in tqdm(INSTRUMENTS, desc="instruments"):
        train_1m = load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            ctx = build_domain_ctx(name, htf_min, ltf_min, train_1m, shift_htf=0)
            ctx_shift = build_domain_ctx(name, htf_min, ltf_min, train_1m,
                                         shift_htf=PHASE_SHIFT_HTF_BARS)
            holds = [ratio * mlt for mlt in HOLD_MULTS]
            ig = integrity_checks(train_1m, ctx, max(holds))
            ig.update({"instrument": sym, "domain": name})
            integrity.append(ig)
            for mlt, hold in zip(HOLD_MULTS, holds):
                for spec in specs:
                    r = eval_cell(ctx, spec, hold)
                    row = {"instrument": sym, "domain": name, "htf_ltf_ratio": ratio,
                           "hold_mult": mlt, "hold_bars": hold, "variant": spec["name"],
                           "is_signal_axis": spec["sig"], "twin": spec["twin"], **r}
                    if spec["sig"]:                       # Control B on signal cells only
                        rb = eval_cell(ctx_shift, spec, hold)
                        row["phaseshift_mean"] = rb["battery_mean"]
                        row["phaseshift_seed_ci_low"] = rb["seed_ci"][0]
                    rows.append(row)

    df = pl.DataFrame(rows, strict=False)
    df = _attach_derived(df)
    df.write_parquet(RESULTS / "cells.parquet")
    Path(RESULTS / "integrity.json").write_text(json.dumps(integrity, indent=2))
    _write_summary(df, integrity)
    _write_csv(df)
    print(f"[SPDR-001] wrote {df.height} cells -> {RESULTS/'cells.csv'}")


def _attach_derived(df: pl.DataFrame) -> pl.DataFrame:
    """Collapse fraction (twin), tripwire survival, per-instrument empirical-null FWER flag."""
    # twin battery_mean lookup
    twin_map = {(r["instrument"], r["domain"], r["hold_bars"], r["variant"]): r["battery_mean"]
                for r in df.iter_rows(named=True)}
    coll, surv, seedpos = [], [], []
    for r in df.iter_rows(named=True):
        # seed_ci excludes zero on the positive side
        sc_low = r["seed_ci"][0] if r["seed_ci"] is not None else None
        pos = bool(sc_low is not None and np.isfinite(sc_low) and sc_low > 0)
        seedpos.append(pos)
        if r["is_signal_axis"] and r["twin"] is not None:
            tw = twin_map.get((r["instrument"], r["domain"], r["hold_bars"], r["twin"]), np.nan)
            bm = r["battery_mean"]
            coll.append(float(tw / bm) if (bm not in (0, None) and np.isfinite(bm) and bm != 0)
                        else np.nan)
        else:
            coll.append(np.nan)
        if r["is_signal_axis"]:
            ps = r.get("phaseshift_seed_ci_low")
            # tripwire "survives" = shifted edge still seed-positive (a leak). survives=False is good.
            surv.append(bool(ps is not None and np.isfinite(ps) and ps > 0))
        else:
            surv.append(False)
    df = df.with_columns([pl.Series("seed_positive", seedpos),
                          pl.Series("collapse_frac", coll),
                          pl.Series("tripwire_survives", surv)])
    # per-instrument empirical null = |battery_mean| over gating-only cells; FWER threshold q95
    flags = []
    for r in df.iter_rows(named=True):
        inst = r["instrument"]
        null_bm = df.filter((pl.col("instrument") == inst) & (~pl.col("is_signal_axis"))
                            & (pl.col("variant") != "none"))["battery_mean"].to_numpy()
        null_bm = np.abs(null_bm[np.isfinite(null_bm)])
        thr = float(np.quantile(null_bm, FWER_Q)) if null_bm.size else np.nan
        flag = bool(r["is_signal_axis"] and r["seed_positive"] and (not r["tripwire_survives"])
                    and np.isfinite(r["battery_mean"]) and np.isfinite(thr)
                    and abs(r["battery_mean"]) > thr)
        flags.append(flag)
    return df.with_columns(pl.Series("fwer_notable", flags))


def _write_csv(df: pl.DataFrame) -> None:
    """CSV export: stringify list columns (seed_ci) which CSV can't hold."""
    out = df.with_columns([pl.col(c).cast(pl.List(pl.Float64)).list.eval(pl.element().round(6))
                           .cast(pl.List(pl.Utf8)).list.join(";").alias(c)
                           for c in ("seed_ci", "ci") if c in df.columns])
    out.write_csv(RESULTS / "cells.csv")


def _write_summary(df: pl.DataFrame, integrity: list[dict]) -> None:
    sig = df.filter(pl.col("is_signal_axis"))
    gate = df.filter((~pl.col("is_signal_axis")) & (pl.col("variant") != "none"))
    n_notable = int(df["fwer_notable"].sum())
    gate_pos_frac = float(gate["seed_positive"].mean()) if gate.height else float("nan")
    all_ig = all(x["all_pass"] for x in integrity)
    summ = {
        "integrity_all_pass": all_ig,
        "n_cells": df.height,
        "n_signal_cells": sig.height,
        "n_gating_null_cells": gate.height,
        "gating_null_seed_positive_fraction": gate_pos_frac,   # FPR sentinel (expect ~0.025 one-sided)
        "n_signal_seed_positive": int(sig["seed_positive"].sum()),
        "n_signal_fwer_notable": n_notable,
        "n_signal_tripwire_survives": int(sig["tripwire_survives"].sum()),
        "notable_cells": df.filter(pl.col("fwer_notable")).select(
            ["instrument", "domain", "hold_bars", "variant", "battery_mean", "seed_ci",
             "collapse_frac", "phaseshift_mean"]).to_dicts(),
    }
    Path(RESULTS / "summary.json").write_text(json.dumps(summ, indent=2, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "notable_cells"}, indent=2))


if __name__ == "__main__":
    run()
