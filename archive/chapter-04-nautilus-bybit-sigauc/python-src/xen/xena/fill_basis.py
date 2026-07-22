"""Print-vs-path fill-basis decomposition (INFR-009 P2; consolidated-03 §4.4).

Mandatory evidence attribution on emitted fills/marks — **not** a synthetic tradable
and **not** a HARD tripwire. Replaces the retired independently-rotated grid-repriced
permutation battery as the limit-entry diagnostic.

Structural identity (fills-derived, always):

    fills_gross  = dir · (ExitFill − EntryFill) / EntryFill · 1e4
    print_bps    = dir · (Open[fill_bar] − EntryFill) / EntryFill · 1e4
    path_bps     = dir · (ExitFill − Open[fill_bar]) / EntryFill · 1e4
    fills_gross  == print_bps + path_bps

Engine ``RealizedBps`` is reported separately. If the engine basis differs (fees,
denominator convention), ``engine_vs_fills`` can be large on live limit fixtures even
when print/path math is correct — watch on XENA-003; do not treat as a binder.

Grid / bar-close entries: print term expected ≈ 0 (observable, not assumed).
Native-limit entries: print can dominate (XENA-003 archetype).

Diagnostic label cutoffs (``grid_like``, ``limit_print_dominance``) are **descriptive
labels only** — not frozen binders, not pass thresholds (consolidated-03: no absolute
scalar smell on the binding path).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream

IDENTITY_TOL_BPS = 1e-6

# Descriptive label cutoffs only — NOT binders, NOT pass thresholds, NOT frozen registry
# values. Do not promote into a hard gate. Revisit as pure documentation if they mislead.
_LABEL_GRID_PRINT_MEAN_MAX = 0.05
_LABEL_GRID_ABS_PRINT_MEAN_MAX = 0.25
_LABEL_LIMIT_GROSS_ABS_MIN = 0.1


def _entry_times_ns(cis: pl.DataFrame) -> np.ndarray:
    et = cis.get_column("EntryTime")
    if et.dtype == pl.Datetime or str(et.dtype).startswith("Datetime"):
        return et.dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    return et.cast(pl.Int64).to_numpy()


def _exit_times_ns(cis: pl.DataFrame) -> np.ndarray:
    xt = cis.get_column("ExitTime")
    if xt.dtype == pl.Datetime or str(xt.dtype).startswith("Datetime"):
        return xt.dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    return xt.cast(pl.Int64).to_numpy()


def decompose_candidate_fills(
    run_dir: str | Path,
    *,
    candidate_id: str = "",
    symbol: str = "",
    segment: tuple[int, int] | None = None,
) -> pl.DataFrame:
    """Per-leg print/path/first-mark decomposition for one emission directory.

    Requires positions.parquet (mark grid) + cis_trades.parquet (fills).

    ``gross_bps`` column = fills-derived (print+path identity basis).
    ``engine_realized_bps`` = engine RealizedBps when present (may differ).
    """
    run = Path(run_dir)
    cis = pl.read_parquet(run / "cis_trades.parquet")
    pos = pl.read_parquet(run / "positions.parquet").sort("SourceCloseTime")

    et = _entry_times_ns(cis)
    xt = _exit_times_ns(cis)
    sel = np.ones(len(et), dtype=bool)
    if segment is not None:
        sel &= (et >= segment[0]) & (et < segment[1])
    if "Censored" in cis.columns:
        sel &= ~np.asarray(cis.get_column("Censored").to_numpy(), dtype=bool)
    cis = cis.filter(pl.Series(sel))
    if cis.height == 0:
        return pl.DataFrame(schema={
            "candidate_id": pl.Utf8, "symbol": pl.Utf8,
            "gross_bps": pl.Float64, "engine_realized_bps": pl.Float64,
            "print_bps": pl.Float64, "path_bps": pl.Float64,
            "first_mark_bps": pl.Float64, "exit_vs_next_open_bps": pl.Float64,
        })

    mt = pos.get_column("SourceCloseTime")
    if mt.dtype == pl.Datetime or str(mt.dtype).startswith("Datetime"):
        mt_ns = mt.dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    else:
        mt_ns = mt.cast(pl.Int64).to_numpy()
    mo = pos.get_column("RealOpen").to_numpy().astype(float)

    et = _entry_times_ns(cis)
    d = cis.get_column("Direction").to_numpy().astype(float)
    if "EntryFillPrice" in cis.columns:
        ep = cis.get_column("EntryFillPrice").to_numpy().astype(float)
        xp = cis.get_column("ExitFillPrice").to_numpy().astype(float)
    else:
        ep = cis.get_column("EntryPrice").to_numpy().astype(float)
        xp = cis.get_column("ExitPrice").to_numpy().astype(float)

    fills_gross = d * (xp - ep) / np.maximum(ep, 1e-12) * 1e4
    if "RealizedBps" in cis.columns:
        engine_rb = cis.get_column("RealizedBps").to_numpy().astype(float)
    else:
        engine_rb = fills_gross.copy()

    i0 = np.searchsorted(mt_ns, et, side="left")
    i0 = np.minimum(i0, len(mt_ns) - 1)
    o_fill = mo[i0]
    o_next = mo[np.minimum(i0 + 1, len(mt_ns) - 1)]

    print_bps = d * (o_fill - ep) / np.maximum(ep, 1e-12) * 1e4
    path_bps = d * (xp - o_fill) / np.maximum(ep, 1e-12) * 1e4
    first_mark_bps = d * (o_next - ep) / np.maximum(ep, 1e-12) * 1e4
    exit_vs_next = d * (xp - o_next) / np.maximum(ep, 1e-12) * 1e4

    return pl.DataFrame({
        "candidate_id": [candidate_id] * len(ep),
        "symbol": [symbol] * len(ep),
        "gross_bps": fills_gross,              # identity basis (print + path)
        "engine_realized_bps": engine_rb,      # may differ from fills basis
        "print_bps": print_bps,
        "path_bps": path_bps,
        "first_mark_bps": first_mark_bps,
        "exit_vs_next_open_bps": exit_vs_next,
    })


def decompose_stream(stream: CandidateStream,
                     *, segment: tuple[int, int] | None = None) -> pl.DataFrame:
    """Decompose from an in-memory CandidateStream (oracle-shaped columns)."""
    trades, marks = stream.trades, stream.marks
    if trades.height == 0 or marks.height < 2:
        return pl.DataFrame()
    et = trades.get_column("EntryTime").to_numpy().astype(np.int64)
    sel = np.ones(len(et), dtype=bool)
    if segment is not None:
        sel &= (et >= segment[0]) & (et < segment[1])
    if "Censored" in trades.columns:
        sel &= ~trades.get_column("Censored").to_numpy().astype(bool)
    tr = trades.filter(pl.Series(sel))
    if tr.height == 0:
        return pl.DataFrame()
    mt = marks.get_column("CloseTime").to_numpy().astype(np.int64)
    mo = marks.get_column("Open").to_numpy().astype(float)
    et = tr.get_column("EntryTime").to_numpy().astype(np.int64)
    d = tr.get_column("Direction").to_numpy().astype(float)
    ep = tr.get_column("EntryPrice").to_numpy().astype(float)
    xp = tr.get_column("ExitPrice").to_numpy().astype(float)
    i0 = np.minimum(np.searchsorted(mt, et, side="left"), len(mt) - 1)
    o_fill = mo[i0]
    o_next = mo[np.minimum(i0 + 1, len(mt) - 1)]
    fills_gross = d * (xp - ep) / np.maximum(ep, 1e-12) * 1e4
    print_bps = d * (o_fill - ep) / np.maximum(ep, 1e-12) * 1e4
    path_bps = d * (xp - o_fill) / np.maximum(ep, 1e-12) * 1e4
    first_mark = d * (o_next - ep) / np.maximum(ep, 1e-12) * 1e4
    return pl.DataFrame({
        "candidate_id": [stream.candidate_id] * len(ep),
        "symbol": [stream.symbol] * len(ep),
        "gross_bps": fills_gross,
        "engine_realized_bps": fills_gross,  # no separate engine column in-stream
        "print_bps": print_bps,
        "path_bps": path_bps,
        "first_mark_bps": first_mark,
        "exit_vs_next_open_bps": d * (xp - o_next) / np.maximum(ep, 1e-12) * 1e4,
    })


def summarize_decomposition(df: pl.DataFrame) -> dict[str, Any]:
    """Aggregate print/path summary + identity + engine-basis watch flag.

    Labels ``grid_like`` / ``limit_print_dominance`` are descriptive only
    (``binding=False``) — never promote to a pass threshold.
    """
    if df is None or df.height == 0:
        return {"n_legs": 0, "empty": True, "binding": False}
    g = df.get_column("gross_bps").to_numpy()  # fills-derived
    p = df.get_column("print_bps").to_numpy()
    pa = df.get_column("path_bps").to_numpy()
    fm = df.get_column("first_mark_bps").to_numpy()
    # Structural identity: print + path == fills-derived gross
    ident = float(np.max(np.abs(g - p - pa)))
    engine_vs_fills = float("nan")
    if "engine_realized_bps" in df.columns:
        eng = df.get_column("engine_realized_bps").to_numpy()
        finite = np.isfinite(eng) & np.isfinite(g)
        if finite.any():
            engine_vs_fills = float(np.max(np.abs(eng[finite] - g[finite])))
    g_mean = float(np.mean(g))
    p_mean = float(np.mean(p))
    abs_print_mean = float(np.mean(np.abs(p)))
    path_mean = float(np.mean(pa))
    return {
        "n_legs": int(df.height),
        "n_candidates": int(df.get_column("candidate_id").n_unique())
        if "candidate_id" in df.columns else 1,
        "identity_max_abs_err_bps": ident,
        "identity_ok": ident <= max(IDENTITY_TOL_BPS, 1e-3),
        "identity_basis": "fills_derived (print + path); not engine RealizedBps",
        "engine_vs_fills_max_abs_bps": engine_vs_fills,
        "engine_vs_fills_note": (
            "Watch on live limit fixtures (e.g. XENA-003): engine RealizedBps may "
            "differ from d·(xp−ep)/ep if fees/denominator differ. Evidence only."
        ),
        "gross_mean_bps": g_mean,
        "gross_median_bps": float(np.median(g)),
        "print_mean_bps": p_mean,
        "print_median_bps": float(np.median(p)),
        "path_mean_bps": path_mean,
        "path_median_bps": float(np.median(pa)),
        "first_mark_mean_bps": float(np.mean(fm)),
        "print_share_of_gross": (float(p_mean / g_mean) if abs(g_mean) > 1e-12
                                 else float("nan")),
        "frac_print_positive": float(np.mean(p > 0)),
        "abs_print_mean_bps": abs_print_mean,
        # Descriptive labels only — not binders (consolidated-03: no frozen-scalar smell)
        "grid_like": bool(
            abs(p_mean) < _LABEL_GRID_PRINT_MEAN_MAX
            and abs_print_mean < _LABEL_GRID_ABS_PRINT_MEAN_MAX
        ),
        "limit_print_dominance": bool(
            abs(g_mean) > _LABEL_LIMIT_GROSS_ABS_MIN
            and abs(p_mean) > abs(path_mean)
        ),
        "label_cutoffs": {
            "role": "descriptive_labels_only",
            "binding": False,
            "grid_print_mean_max": _LABEL_GRID_PRINT_MEAN_MAX,
            "grid_abs_print_mean_max": _LABEL_GRID_ABS_PRINT_MEAN_MAX,
            "limit_gross_abs_min": _LABEL_LIMIT_GROSS_ABS_MIN,
            "note": "Do not promote into a pass threshold or registry pin",
        },
        "binding": False,
    }


def fill_basis_package(
    items: Sequence[tuple[str, str, str | Path]],
    *,
    segment: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Batch decompose a list of (candidate_id, symbol, run_dir) → package summary.

    Used by the shortlist evidence package (INFR-009 §4.3 / §4.4).
    """
    parts: list[pl.DataFrame] = []
    for cid, sym, rd in items:
        df = decompose_candidate_fills(rd, candidate_id=cid, symbol=sym, segment=segment)
        if df.height:
            parts.append(df)
    if not parts:
        return {"n_legs": 0, "empty": True, "per_candidate": {}, "binding": False}
    all_df = pl.concat(parts)
    summary = summarize_decomposition(all_df)
    per: dict[str, Any] = {}
    for cid in all_df.get_column("candidate_id").unique().to_list():
        sub = all_df.filter(pl.col("candidate_id") == cid)
        per[str(cid)] = summarize_decomposition(sub)
    summary["per_candidate"] = per
    summary["binding"] = False
    summary["retired_replacement_for"] = "HARD_permutation_battery"
    return summary


def reprice_entries_to_next_open(
    trades: pl.DataFrame,
    marks: pl.DataFrame,
) -> pl.DataFrame:
    """Re-price entry fills to the next bar open; hold times / exits / sizing fixed (L-27).

    Parameters
    ----------
    trades :
        Columns EntryTime, ExitTime, Direction, EntryPrice, ExitPrice (+ optional).
    marks :
        Columns CloseTime (ns int) and Open.

    Returns
    -------
    pl.DataFrame
        Copy of trades with EntryPrice replaced by next-open; adds ``live_entry_price``
        and ``next_open_entry_price`` for audit.
    """
    if trades.height == 0 or marks.height < 2:
        return trades
    mt = marks.get_column("CloseTime").to_numpy().astype(np.int64)
    mo = marks.get_column("Open").to_numpy().astype(float)
    et = trades.get_column("EntryTime").to_numpy().astype(np.int64)
    ep = trades.get_column("EntryPrice").to_numpy().astype(float)
    i0 = np.minimum(np.searchsorted(mt, et, side="left"), len(mt) - 1)
    i1 = np.minimum(i0 + 1, len(mt) - 1)
    next_open = mo[i1]
    return trades.with_columns(
        pl.Series("live_entry_price", ep),
        pl.Series("next_open_entry_price", next_open),
        pl.Series("EntryPrice", next_open),
    )


def next_open_discriminating_control(
    streams: Sequence[CandidateStream],
    *,
    segment: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """L-27 next-open discriminating control (INFR-014 WP6).

    Compare live fills-derived gross edge vs the same legs re-priced to the next bar
    open (exits/holds/sizing fixed). Large live−next_open gap indicates passive-print
    (limit) edge rather than predictive timing.

    Required apparatus even when all CAL cells are market (proves tooling for future
    limit-entry universes; SPDR-005 §2.3 forward note).
    """
    live_parts: list[pl.DataFrame] = []
    next_parts: list[pl.DataFrame] = []
    for s in streams:
        live = decompose_stream(s, segment=segment)
        if live.height == 0:
            continue
        live_parts.append(live)
        tr = s.trades
        if segment is not None:
            et = tr.get_column("EntryTime").to_numpy().astype(np.int64)
            sel = (et >= segment[0]) & (et < segment[1])
            tr = tr.filter(pl.Series(sel))
        if tr.height == 0:
            continue
        tr_next = reprice_entries_to_next_open(tr, s.marks)
        # recompute fills gross on re-priced entries (exits fixed)
        d = tr_next.get_column("Direction").to_numpy().astype(float)
        ep = tr_next.get_column("EntryPrice").to_numpy().astype(float)
        xp = tr_next.get_column("ExitPrice").to_numpy().astype(float)
        g = d * (xp - ep) / np.maximum(ep, 1e-12) * 1e4
        next_parts.append(pl.DataFrame({
            "candidate_id": [s.candidate_id] * len(g),
            "symbol": [s.symbol] * len(g),
            "gross_bps": g,
        }))
    if not live_parts:
        return {
            "n_legs": 0,
            "empty": True,
            "binding": False,
            "control": "next_open_discriminating",
            "lesson": "L-27",
            "note": "no legs in segment",
        }
    live_df = pl.concat(live_parts)
    live_mean = float(live_df.get_column("gross_bps").mean())
    if next_parts:
        next_df = pl.concat(next_parts)
        next_mean = float(next_df.get_column("gross_bps").mean())
        n_next = int(next_df.height)
    else:
        next_mean = float("nan")
        n_next = 0
    gap = live_mean - next_mean if np.isfinite(next_mean) else float("nan")
    return {
        "n_legs": int(live_df.height),
        "n_legs_next_open": n_next,
        "empty": False,
        "binding": False,
        "control": "next_open_discriminating",
        "lesson": "L-27",
        "live_gross_mean_bps": live_mean,
        "next_open_gross_mean_bps": next_mean,
        "live_minus_next_open_bps": float(gap) if np.isfinite(gap) else float("nan"),
        "discrimination_note": (
            "gap≈0 expected for market-on-open / market-on-confirmed entries; "
            "large positive live−next_open gap flags limit-print dominance"
        ),
        "pin_usage": "limit_print_sole_certify_forbidden when gap dominates",
    }
