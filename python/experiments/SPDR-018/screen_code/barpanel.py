"""Fenced bar frames, loaded through the ARM'S OWN PARENT's catalog module.

Each arm reads bars with the aggregation its parent registered (``load_minute_bars`` +
``aggregate_clock`` from that parent's ``catalog_io``), so no arm silently re-aggregates its
object on a different clock definition. Nothing here is a new object — it exists to supply the
decision-bar magnitude ``|r_t|`` that M-3 needs, and the raw series the golden traces are
recomputed from.
"""
from __future__ import annotations

import threading

import numpy as np

import parents
from config import CONFIRM_END, DESIGN_START, HOLDOUT_START_NS, NS, TRAIN_END_NS

_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str, str], dict] = {}

#: which parent's clock table defines each clock
CLOCK_OWNER = {"M15": "SPDR-013", "H1": "SPDR-014", "H4": "SPDR-014", "D1": "SPDR-012"}


def _fence_assert(ts: np.ndarray) -> None:
    """HARD: TRAIN-only, and the global holdout is never even approached."""
    if ts.size == 0:
        return
    hi = int(ts.max())
    if hi >= TRAIN_END_NS:
        raise AssertionError(f"bar panel crossed the TRAIN fence: {hi} >= {TRAIN_END_NS}")
    if hi >= HOLDOUT_START_NS:
        raise AssertionError("bar panel touched the global holdout")


def bars(symbol: str, clock: str, *, parent: str | None = None, manifest=None) -> dict:
    """TRAIN-fenced bars for ``symbol`` on ``clock``, plus the causal decision-bar magnitude.

    Returned arrays (all aligned, index ``t`` = one clock bar):
      ``slot_start`` ``slot_end`` ``open`` ``high`` ``low`` ``close`` ``complete``
      ``r_oo_bps``   open-to-open return INTO bar t: ``(open[t]/open[t-1] - 1) * 1e4``
      ``abs_r_bps``  ``|r_oo_bps|`` — the decision-bar magnitude M-3 matches on. Known at the
                     open of bar ``t``, so a rule reading it decides no earlier than ``t``.
    """
    owner = parent or CLOCK_OWNER[clock]
    key = (symbol, clock, owner)
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]

    cat = parents.load(owner)["catalog_io"]
    minutes = cat.load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN",
                                   manifest=manifest)
    if minutes.height == 0:
        out = {"symbol": symbol, "clock": clock, "n": 0, "empty": True}
    else:
        agg = cat.aggregate_clock(minutes, clock)
        o = agg["open"].to_numpy()
        r = np.full(o.size, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            r[1:] = (o[1:] / o[:-1] - 1.0) * 1e4
        ts = agg["slot_end"].to_numpy().astype(np.int64)
        _fence_assert(ts)
        out = {
            "symbol": symbol, "clock": clock, "n": int(agg.height), "empty": False,
            "slot_start": agg["slot_start"].to_numpy().astype(np.int64),
            "slot_end": ts,
            "open": o,
            "high": agg["high"].to_numpy(),
            "low": agg["low"].to_numpy(),
            "close": agg["close"].to_numpy(),
            "complete": agg["complete"].to_numpy(),
            "r_oo_bps": r,
            "abs_r_bps": np.abs(r),
            "clock_minutes": int(parents.const(owner, "CLOCKS")[clock]["minutes"]),
            "aggregation_owner": owner,
        }
    with _LOCK:
        _CACHE[key] = out
    return out


def forward_oo_bps(panel: dict, idx: np.ndarray, h: int, side: np.ndarray | int = 1
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Signed open-to-open return over ``h`` bars from entry at ``open[idx+1]``.

    Entry strictly after the decision bar ``idx`` (TRIPWIRE-1), exit at the declared offset.
    Returns ``(r_bps, entry_ts_ns, exit_ts_ns)`` with NaN where the exit runs past the fence.
    """
    o = panel["open"]
    ts = panel["slot_start"]
    n = o.size
    i = np.asarray(idx, dtype=np.int64)
    e = i + 1
    x = e + h
    ok = (e >= 0) & (x < n)
    r = np.full(i.size, np.nan)
    ent = np.full(i.size, -1, dtype=np.int64)
    exi = np.full(i.size, -1, dtype=np.int64)
    if ok.any():
        s = np.asarray(side, dtype=float) if np.ndim(side) else float(side)
        s_ok = s[ok] if np.ndim(s) else s
        r[ok] = s_ok * (o[x[ok]] / o[e[ok]] - 1.0) * 1e4
        ent[ok] = ts[e[ok]]
        exi[ok] = ts[x[ok]]
    return r, ent, exi


def clock_minutes(clock: str) -> int:
    owner = CLOCK_OWNER[clock]
    return int(parents.const(owner, "CLOCKS")[clock]["minutes"])


def day_of(ts_ns: np.ndarray) -> np.ndarray:
    return np.asarray(ts_ns, dtype=np.int64) // (86_400 * NS)
