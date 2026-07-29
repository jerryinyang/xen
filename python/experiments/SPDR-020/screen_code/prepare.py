"""Per-symbol series preparation: H1/H4 packs, M1 stream, parent gates, s_symbol pin."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_minute_bars
from config import (
    BANDS,
    CLOCKS,
    CONFIRM_END,
    DESIGN_START,
    NS,
    PARENT_015_CODE,
    PARENT_015_RESULTS,
    TRAIN_END_NS,
    ZVOL_SCALE_PATH,
    ZVOL_WARMUP_BARS,
)
from indicators import (
    abs_oo_bps,
    atr_zigzag,
    ewma_park,
    expanding_percentile,
    expanding_std,
    parkinson,
    rolling_median_split,
    wilder_atr,
    zz_mag_forecast_series,
)


@dataclass
class SeriesPack:
    """Precomputed per-symbol clock series (SPDR-014 shape + gates + M1)."""

    symbol: str
    clock: str
    slot_start: np.ndarray
    slot_end: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr: np.ndarray
    atr_lag: np.ndarray
    park: np.ndarray
    ewma_park: np.ndarray
    sigma_zvol: np.ndarray
    sigma_zmag: np.ndarray
    abs_oo: np.ndarray
    uncond_sigma: np.ndarray
    vol_pct: np.ndarray
    mag_pct: np.ndarray
    slow_regime: np.ndarray
    shock_flag: np.ndarray
    r: np.ndarray
    s_symbol: float
    design_lo: int
    design_hi: int
    confirm_hi: int
    # M1 for L4 exits
    m1: dict[str, np.ndarray] = field(repr=False, default_factory=dict)
    # SPDR-015 gates held forward to this clock (at breach bar)
    s_hmm_rv: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_rmarkov_k4: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_rmarkov_k12: np.ndarray = field(default_factory=lambda: np.empty(0))
    tgtcur_fires: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_stay: np.ndarray = field(default_factory=lambda: np.empty(0))
    n_prior_trans: np.ndarray = field(default_factory=lambda: np.empty(0))
    s_hat_uncond: float = float("nan")  # TRAIN-median sigma_zvol
    source_train_medians: dict[str, float] = field(default_factory=dict)


def _band_index_bounds(slot_start: np.ndarray, start: datetime, end: datetime) -> tuple[int, int]:
    lo_ns = int(start.timestamp() * NS)
    hi_ns = int(end.timestamp() * NS)
    lo = int(np.searchsorted(slot_start, lo_ns, side="left"))
    hi = int(np.searchsorted(slot_start, hi_ns, side="left"))
    return lo, hi


def load_s_symbol_pin() -> dict[str, float]:
    """s_symbol from SPDR-014/results/zvol_scale.json — never re-fit."""
    raw = json.loads(Path(ZVOL_SCALE_PATH).read_text())
    out: dict[str, float] = {}
    for k, v in raw.items():
        if v is None:
            out[k] = float("nan")
        else:
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = float("nan")
    return out


def resolve_frozen_s_symbol(value: float | None) -> float:
    """Return the parent pin verbatim; missing coverage remains missing."""
    if value is None or not np.isfinite(value):
        return float("nan")
    return float(value)


def zvol_source_is_available(s_symbol: float | None) -> bool:
    return bool(s_symbol is not None and np.isfinite(s_symbol))


def _hold_forward(src_end: np.ndarray, src_val: np.ndarray, dst_end: np.ndarray) -> np.ndarray:
    out = np.full(dst_end.size, np.nan)
    if src_end.size == 0:
        return out
    j = 0
    last = np.nan
    n_src = src_end.size
    for i, t in enumerate(dst_end):
        while j < n_src and src_end[j] <= t:
            if np.isfinite(src_val[j]):
                last = float(src_val[j])
            j += 1
        out[i] = last
    return out


def _m1_arrays(minutes: pl.DataFrame) -> dict[str, np.ndarray]:
    if minutes.height == 0:
        return {
            "ts": np.empty(0, dtype=np.int64),
            "open": np.empty(0), "high": np.empty(0),
            "low": np.empty(0), "close": np.empty(0),
        }
    return {
        "ts": minutes["ts_event"].to_numpy().astype(np.int64),
        "open": minutes["open"].to_numpy().astype(float),
        "high": minutes["high"].to_numpy().astype(float),
        "low": minutes["low"].to_numpy().astype(float),
        "close": minutes["close"].to_numpy().astype(float),
    }


def prepare_symbol(
    symbol: str,
    clock: str,
    *,
    manifest=None,
    s_symbol: float | None = None,
    minutes: pl.DataFrame | None = None,
) -> SeriesPack | None:
    if minutes is None:
        minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)
    if minutes.height == 0:
        return None
    bars = aggregate_clock(minutes, clock).filter(pl.col("complete"))
    if bars.height < CLOCKS[clock]["warmup_bars"] + 30:
        return None

    slot_start = bars["slot_start"].to_numpy().astype(np.int64)
    slot_end = bars["slot_end"].to_numpy().astype(np.int64)
    open_ = bars["open"].to_numpy().astype(float)
    high = bars["high"].to_numpy().astype(float)
    low = bars["low"].to_numpy().astype(float)
    close = bars["close"].to_numpy().astype(float)

    park = parkinson(high, low)
    ewma = ewma_park(park)
    abs_oo = abs_oo_bps(open_)
    atr = wilder_atr(high, low, close)
    atr_lag = np.concatenate([[np.nan], atr[:-1]])

    design_lo_raw, design_hi = _band_index_bounds(slot_start, *BANDS["DESIGN"])
    _, confirm_hi = _band_index_bounds(slot_start, *BANDS["CONFIRM"])

    design_mask = np.zeros(open_.size, dtype=bool)
    design_mask[design_lo_raw:design_hi] = True
    warm_idx = np.where(design_mask & np.isfinite(ewma))[0]
    if warm_idx.size < ZVOL_WARMUP_BARS:
        design_lo = int(warm_idx[0]) + 1 if warm_idx.size else design_lo_raw
    else:
        design_lo = int(warm_idx[ZVOL_WARMUP_BARS - 1]) + 1

    s_symbol = resolve_frozen_s_symbol(s_symbol)
    sigma_zvol = np.where(np.isfinite(ewma), s_symbol * ewma, np.nan)

    atr_start = int(np.argmax(np.isfinite(atr))) if np.isfinite(atr).any() else 0
    swings = atr_zigzag(close, atr, atr_start)
    sigma_zmag = zz_mag_forecast_series(close.size, swings)

    uncond = expanding_std(abs_oo, min_n=20)
    vol_pct = expanding_percentile(ewma)
    mag_pct = expanding_percentile(np.where(np.isfinite(sigma_zmag), sigma_zmag, np.nan))
    slow = rolling_median_split(ewma, window=20)

    r = np.full(close.size, np.nan)
    r[1:] = np.log(close[1:] / close[:-1])
    abs_r = np.abs(r)
    shock = np.zeros(close.size, dtype=float)
    hist: list[float] = []
    for i in range(close.size):
        if not np.isfinite(abs_r[i]):
            shock[i] = 0.0
            continue
        hist.append(float(abs_r[i]))
        thr = float(np.quantile(hist, 0.9)) if len(hist) >= 20 else float("inf")
        shock[i] = 1.0 if abs_r[i] >= thr else 0.0

    train_mask = (slot_end < TRAIN_END_NS) & np.isfinite(sigma_zvol)
    s_hat_uncond = (
        float(np.median(sigma_zvol[train_mask])) if train_mask.any() else float("nan")
    )
    train_time = slot_end < TRAIN_END_NS
    zmag_mask = train_time & np.isfinite(sigma_zmag)
    zmag_median = (
        float(np.median(sigma_zmag[zmag_mask])) if zmag_mask.any() else float("nan")
    )
    source_train_medians = {
        "Z-VOL": s_hat_uncond,
        "Z-MAG": zmag_median,
        "Z-MAG-SENS": zmag_median / 2.0 if np.isfinite(zmag_median) else float("nan"),
    }

    return SeriesPack(
        symbol=symbol, clock=clock,
        slot_start=slot_start, slot_end=slot_end,
        open=open_, high=high, low=low, close=close,
        atr=atr, atr_lag=atr_lag,
        park=park, ewma_park=ewma,
        sigma_zvol=sigma_zvol, sigma_zmag=sigma_zmag,
        abs_oo=abs_oo, uncond_sigma=uncond,
        vol_pct=vol_pct, mag_pct=mag_pct,
        slow_regime=slow, shock_flag=shock, r=r,
        s_symbol=float(s_symbol) if np.isfinite(s_symbol) else float("nan"),
        design_lo=design_lo, design_hi=design_hi, confirm_hi=confirm_hi,
        m1=_m1_arrays(minutes),
        s_hat_uncond=s_hat_uncond,
        source_train_medians=source_train_medians,
    )


# --------------------------------------------------------------------------- gates (SPDR-015)
def _load_015_transitions():
    import importlib
    import sys

    code_dir = str(PARENT_015_CODE)
    for key in list(sys.modules):
        if key in ("config", "features", "transitions", "controls", "hmm", "universe"):
            mod = sys.modules[key]
            f = getattr(mod, "__file__", "") or ""
            if any(x in f for x in ("SPDR-015", "SPDR-019", "SPDR-018", "SPDR-014", "SPDR-020")):
                del sys.modules[key]
    sys.path.insert(0, code_dir)
    try:
        for name in ("config", "features", "transitions"):
            if name in sys.modules:
                f = getattr(sys.modules[name], "__file__", "") or ""
                if PARENT_015_CODE.as_posix() not in Path(f).as_posix():
                    del sys.modules[name]
        return importlib.import_module("transitions")
    finally:
        if code_dir in sys.path:
            sys.path.remove(code_dir)
        for key in list(sys.modules):
            mod = sys.modules[key]
            f = getattr(mod, "__file__", "") or ""
            if f and Path(f).parent == PARENT_015_CODE:
                sys.modules.pop(key)
                sys.modules[f"_SPDR_015__{key}"] = mod


def _p_stay_series(state_i: np.ndarray, src_end: np.ndarray, dst_end: np.ndarray):
    n_src = state_i.size
    p_stay_src = np.full(n_src, np.nan)
    n_prior = np.zeros(n_src, dtype=float)
    # expanding same-state transition rate
    same = 0
    total = 0
    for i in range(1, n_src):
        a, b = state_i[i - 1], state_i[i]
        if a < 0 or b < 0:
            p_stay_src[i] = p_stay_src[i - 1] if i else np.nan
            n_prior[i] = total
            continue
        total += 1
        if a == b:
            same += 1
        p_stay_src[i] = same / total if total else np.nan
        n_prior[i] = total
    return _hold_forward(src_end, p_stay_src, dst_end), _hold_forward(src_end, n_prior, dst_end)


def attach_gates(pack: SeriesPack, *, trans_mod=None) -> dict:
    """Hold SPDR-015 gates forward onto the pack's clock (breach-bar conditioning)."""
    path = PARENT_015_RESULTS / "regime_states.parquet"
    n = pack.close.size
    empty = {
        "s_hmm_rv": np.full(n, np.nan),
        "p_rmarkov_k4": np.full(n, np.nan),
        "p_rmarkov_k12": np.full(n, np.nan),
        "tgtcur_fires": np.full(n, np.nan),
        "p_stay": np.full(n, np.nan),
        "n_prior_trans": np.zeros(n),
    }
    if not path.exists():
        for k, v in empty.items():
            setattr(pack, k, v)
        return {"symbol": pack.symbol, "status": "NO_REGIME_FILE"}

    rs = pl.read_parquet(path).filter(
        (pl.col("symbol") == pack.symbol) & (pl.col("clock") == "H1")
    ).sort("slot_end")
    if rs.height == 0:
        for k, v in empty.items():
            setattr(pack, k, v)
        return {"symbol": pack.symbol, "status": "NO_REGIME_ROWS"}

    src_end = rs["slot_end"].to_numpy().astype(np.int64)
    s_hmm = rs["s_hmm_rv"].to_numpy().astype(float)
    pack.s_hmm_rv = _hold_forward(src_end, s_hmm, pack.slot_end)

    if trans_mod is None:
        trans_mod = _load_015_transitions()
    cols = {
        "s_markov": rs["s_markov"].to_numpy().astype(float),
        "dur_markov": rs["dur_markov"].to_numpy().astype(float),
        "rv20": rs["rv20"].to_numpy().astype(float),
        "park_ewma": rs["park_ewma"].to_numpy().astype(float),
        "lvl_pct": rs["lvl_pct"].to_numpy().astype(float),
        "n_high_4_markov": rs["n_high_4_markov"].to_numpy().astype(float),
        "n_high_12_markov": rs["n_high_12_markov"].to_numpy().astype(float),
        "s_shock": rs["s_shock"].to_numpy().astype(float),
    }
    state_i = np.where(np.isfinite(cols["s_markov"]), cols["s_markov"].astype(np.int64), -1)
    X = trans_mod._feature_matrix_for_model(cols, "R-MARKOV")
    is_origin = rs["is_origin"].to_numpy().astype(bool)
    probs4 = trans_mod.walk_forward_probs(state_i, X, src_end, is_origin, 4)
    probs12 = trans_mod.walk_forward_probs(state_i, X, src_end, is_origin, 12)
    pack.p_rmarkov_k4 = _hold_forward(src_end, probs4["logistic_ridge"], pack.slot_end)
    pack.p_rmarkov_k12 = _hold_forward(src_end, probs12["logistic_ridge"], pack.slot_end)
    pack.p_stay, pack.n_prior_trans = _p_stay_series(state_i, src_end, pack.slot_end)

    zz_path = PARENT_015_RESULTS / "zz_ordinal.parquet"
    tgtcur = np.full(n, np.nan)
    if zz_path.exists():
        zz = pl.read_parquet(zz_path).filter(
            (pl.col("symbol") == pack.symbol) & (pl.col("clock") == "H1")
        )
        cur = zz.filter((pl.col("target") == "T-GT-CUR") & (pl.col("model") == "logit_ridge"))
        if cur.height:
            c_end = cur["confirm_slot_end"].to_numpy().astype(np.int64)
            c_fire = (cur["p"].to_numpy().astype(float) >= 0.5).astype(float)
            tgtcur = _hold_forward(c_end, c_fire, pack.slot_end)
    pack.tgtcur_fires = tgtcur
    return {"symbol": pack.symbol, "status": "OK", "n_regime": int(rs.height)}


# process-local cache (spawn workers each get one load)
_TRANS_MOD = None
_S_PIN_CACHE: dict[str, float] | None = None
_FENCE_MANIFEST = None


def load_symbol_bundle(symbol: str, *, s_pin: dict[str, float] | None = None) -> dict | None:
    """Work-unit input: both clocks + shared M1 + gates."""
    global _TRANS_MOD, _S_PIN_CACHE, _FENCE_MANIFEST
    from xen.nautilus.catalog_fence import load_fence_manifest

    if _FENCE_MANIFEST is None:
        _FENCE_MANIFEST = load_fence_manifest()
    manifest = _FENCE_MANIFEST
    minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)
    if minutes.height == 0:
        return None
    if s_pin is None:
        if _S_PIN_CACHE is None:
            _S_PIN_CACHE = load_s_symbol_pin()
        s_pin = _S_PIN_CACHE
    s_sym = s_pin.get(symbol, float("nan"))
    packs: dict[str, SeriesPack] = {}
    if _TRANS_MOD is None:
        try:
            _TRANS_MOD = _load_015_transitions()
        except Exception:
            _TRANS_MOD = False  # type: ignore
    trans = _TRANS_MOD if _TRANS_MOD is not False else None
    gate_info: dict = {}
    for clock in CLOCKS:
        pack = prepare_symbol(symbol, clock, manifest=manifest, s_symbol=s_sym, minutes=minutes)
        if pack is None:
            continue
        gate_info = attach_gates(pack, trans_mod=trans)
        packs[clock] = pack
    if not packs:
        return None
    return {
        "symbol": symbol,
        "packs": packs,
        "s_symbol": float(s_sym) if np.isfinite(s_sym) else float("nan"),
        "s_hat_uncond": packs.get("H1", next(iter(packs.values()))).s_hat_uncond,
        "gate_info": gate_info if packs else {},
    }
