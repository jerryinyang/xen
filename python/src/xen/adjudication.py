"""Canonical multi-leg-correct P&L estimands for emitted strategy runs (INFR-001 WS-1).

Replaces the experiment-local ``assemble_realized_bps`` lineage (EXP-010..017), whose
fill-substitution into a +/-1 ``Position`` path counted profit per leg but marked risk for a
single unit — inflating/sign-flipping multi-leg (allow/extend) per-bar series (critical-017,
C-1). This module derives everything from the per-leg ledger (``cis_trades``), which is the
engine's own realized truth.

Accounting contract
-------------------
* A leg's gross P&L is the engine's ``RealizedBps`` = ``Direction * (ExitFillPrice -
  EntryFillPrice) / EntryFillPrice * 1e4`` (linear return on real fills).
* The per-bar series distributes each leg's P&L across the bars it is open, using
  open-to-open marks anchored at the leg's own entry fill:
  ``inc_i = Direction * (M_end(i) - M_start(i)) / EntryFillPrice * 1e4`` with
  ``M_start(entry bar) = EntryFillPrice``, ``M_start(i) = RealOpen[i]`` otherwise,
  ``M_end(i) = RealOpen[i+1]`` for interior bars and ``ExitFillPrice`` on the exit bar.
  The increments telescope, so per leg: ``sum(inc) == RealizedBps`` exactly, and per cell:
  ``sum(per-bar gross) == sum(leg RealizedBps)`` — the mandatory reconciliation invariant.
* Zero-cost model (INFR-022): the ``cost_bps`` parameter is kept for API stability and is
  pinned to 0 by every live caller; ``net_bps == gross_bps`` on live paths. Non-zero cost
  pins are refused by callers under the zero-cost compliance contract (``assert_zero_cost``),
  unless an explicit operator cost directive is recorded in the design.
* A censored leg (open at the emission fence) is marked to the last bar's ``RealOpen`` and
  flagged; its marked-to-open P&L is reported separately from realized.

Causal provenance contract
--------------------------
All inputs are engine emissions (real fills, confirmed bars <= the run's ``AnalysisEndUtc``
fence). Leg-to-bar attribution maps each intrabar m1 fill timestamp to the first emitted bar
whose ``SourceCloseTime`` >= the fill time — the bar the fill occurred in, matching the
engine's own ``cis_trades.SourceCloseTime`` attribution. Nothing here reads data after a
bar's close; nothing regenerates a signal, entry, or fill.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

REQUIRED_POSITION_COLS = ("SourceCloseTime", "RealOpen")
REQUIRED_LEG_COLS = ("EntryTime", "ExitTime", "Direction", "EntryFillPrice",
                     "ExitFillPrice", "RealizedBps", "Censored")

# |sum(per-bar gross) - sum(leg RealizedBps)| tolerance, bps. The construction telescopes,
# so anything beyond float noise means a broken input, not rounding.
RECONCILE_TOL_BPS = 1.0


@dataclass(frozen=True)
class MultiLegSeries:
    """Exposure-correct per-bar P&L for one emitted cell.

    Arrays are aligned to ``times`` (the emission's bar ``SourceCloseTime``, sorted).
    ``gross_bps``/``net_bps`` sum contributions of every *completed* leg open in each bar
    (``net = gross - cost_bps`` per completed leg on its entry bar); ``open_legs`` is
    recomputed from leg spans including fence-open legs (cross-check against the emitted
    ``OpenLegs`` column, not a copy of it). ``censored_mtm_bps`` is the marked-to-open
    P&L of fence-open legs, reported separately and excluded from both series.
    """
    times: np.ndarray
    gross_bps: np.ndarray
    net_bps: np.ndarray
    open_legs: np.ndarray
    n_legs: int
    n_censored: int
    censored_mtm_bps: float
    n_aborted: int = 0  # legs with no exit fill and non-finite RealizedBps (e.g.
    #                     partial_abort) — excluded from all series, disclosed here


@dataclass(frozen=True)
class ReconcileReport:
    per_bar_gross_total: float
    per_leg_realized_total: float
    abs_diff_bps: float
    tol_bps: float
    ok: bool


def _require(df: pl.DataFrame, cols: tuple[str, ...], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns {missing}")


def _leg_bar_spans(times: np.ndarray, legs: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Map each leg's fill timestamps to bar indices (first bar closing at/after the fill)."""
    entry_i = np.searchsorted(times, legs.get_column("EntryTime").to_numpy(), side="left")
    exit_t = legs.get_column("ExitTime").to_numpy()
    censored = legs.get_column("Censored").to_numpy().astype(bool)
    exit_i = np.searchsorted(times, exit_t, side="left")
    exit_i = np.where(censored, len(times) - 1, exit_i)
    if (entry_i >= len(times)).any():
        raise ValueError("leg EntryTime beyond the emitted bar range")
    exit_i = np.minimum(exit_i, len(times) - 1)
    if (exit_i < entry_i).any():
        raise ValueError("leg exits before it enters — corrupted leg ledger")
    return entry_i, exit_i


# Columns that would carry an engine-charged cost. Zero-cost model (INFR-022): any
# non-zero value in these columns means costs entered the emission — a blocking failure.
_COST_COLUMN_FRAGMENTS = ("commission", "fee", "funding", "swap", "spread")


def check_no_cost_charged(*frames: pl.DataFrame) -> dict:
    """Blocking zero-cost check: no non-zero commission/cost column in the emission frames.

    Scans every column whose lowercased name contains a cost fragment
    (commission/fee/funding/swap/spread). A non-zero value in any such column means the
    emission carried an engine-side cost — the zero-cost model (INFR-022 §3.2) forbids it
    on the live path. Pass the RAW emission frames (the Nautilus ``positions_ledger`` /
    ``fills`` carry a ``commissions`` column that the adjudication shim drops during
    normalisation) plus the normalised positions/cis frames. Returns
    ``{"ok": bool, "non_zero_columns": [...], "n_non_zero_rows": n}``; ``ok`` is True
    when no such column exists or all values are zero.
    """
    hits: dict[str, int] = {}
    for df in frames:
        for col in df.columns:
            low = col.lower()
            if not any(frag in low for frag in _COST_COLUMN_FRAGMENTS):
                continue
            try:
                s = df.get_column(col)
                if s.dtype == pl.Utf8:
                    continue
                arr = s.to_numpy()
                num = np.asarray(arr, dtype=float)
                nz = int(np.count_nonzero(num[np.isfinite(num)] != 0.0))
            except (TypeError, ValueError):
                continue
            if nz:
                hits[col] = hits.get(col, 0) + nz
    return {"ok": not hits, "non_zero_columns": sorted(hits), "n_non_zero_rows": sum(hits.values())}


def per_leg_net(cis_trades: pl.DataFrame, *, cost_bps: float) -> pl.DataFrame:
    """Per-leg ledger with ``NetBps = RealizedBps - cost_bps`` (cost once per leg).

    Zero-cost model (INFR-022): live callers pass ``cost_bps=0`` so ``NetBps == RealizedBps``.
    """
    _require(cis_trades, REQUIRED_LEG_COLS, "cis_trades")
    return cis_trades.with_columns((pl.col("RealizedBps") - cost_bps).alias("NetBps"))


def assemble_multileg_bps(positions: pl.DataFrame, cis_trades: pl.DataFrame, *,
                          cost_bps: float, own_symbol: str | None = None) -> MultiLegSeries:
    """Exposure-correct per-bar gross/net series from the per-leg ledger.

    Correct for any leg multiplicity (single-leg arms are the one-leg special case).
    Every open leg contributes its own marked increment each bar; cost is charged on each
    leg's entry bar. See the module accounting contract for the mark construction and the
    telescoping reconciliation guarantee.

    ``own_symbol``: for mixed-symbol ledgers (both-leg arms carry mate-symbol legs), a
    censored leg can only be marked to open against its OWN symbol's price path. Pass the
    cell's symbol to restrict ``censored_mtm_bps`` to own-symbol legs; foreign-symbol
    censored legs still count in ``n_censored`` but contribute no marked MTM (marking a
    EURUSD leg to a USDJPY open is meaningless). Completed legs are unaffected — their
    P&L telescopes to their own fills regardless of interior marks.
    """
    _require(positions, REQUIRED_POSITION_COLS, "positions")
    _require(cis_trades, REQUIRED_LEG_COLS, "cis_trades")
    df = positions.sort("SourceCloseTime")
    times = df.get_column("SourceCloseTime").to_numpy()
    opens = df.get_column("RealOpen").to_numpy().astype(float)
    n = len(times)
    if n < 2:
        raise ValueError("too few emitted bars to assemble a per-bar series")

    gross = np.zeros(n)
    net = np.zeros(n)
    open_legs = np.zeros(n, dtype=np.int64)
    censored_mtm = 0.0
    n_censored = 0

    if cis_trades.height == 0:
        return MultiLegSeries(times, gross, net, open_legs, 0, 0, 0.0)

    # aborted legs (no exit fill, non-finite realized P&L, not censored — e.g. the engine's
    # partial_abort on a both-leg entry) are excluded from every series and disclosed
    aborted_mask = (pl.col("RealizedBps").is_finite().not_()
                    & (pl.col("Censored").cast(pl.Boolean).not_()))
    n_aborted = cis_trades.filter(aborted_mask).height
    legs = cis_trades.filter(aborted_mask.not_())
    if legs.height == 0:
        return MultiLegSeries(times, gross, net, open_legs, 0, 0, 0.0, n_aborted)
    entry_i, exit_i = _leg_bar_spans(times, legs)
    direction = legs.get_column("Direction").to_numpy().astype(float)
    entry_px = legs.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_px = legs.get_column("ExitFillPrice").to_numpy().astype(float)
    censored = legs.get_column("Censored").to_numpy().astype(bool)
    if own_symbol is not None and "LegSymbol" in legs.columns:
        markable = (legs.get_column("LegSymbol") == own_symbol).to_numpy()
    else:
        markable = np.ones(legs.height, dtype=bool)

    for k in range(legs.height):
        b_e, b_x = int(entry_i[k]), int(exit_i[k])
        # marks at bar boundaries: entry fill -> RealOpen[b_e+1 .. b_x] -> exit fill
        marks = np.empty(b_x - b_e + 2)
        marks[0] = entry_px[k]
        if b_x > b_e:
            marks[1:-1] = opens[b_e + 1:b_x + 1]
        if censored[k]:
            last = opens[min(b_x + 1, n - 1)]
            marks[-1] = last
            n_censored += 1
            if markable[k]:
                censored_mtm += direction[k] * (last - entry_px[k]) / entry_px[k] * 1e4
        else:
            marks[-1] = exit_px[k]
        inc = direction[k] * np.diff(marks) / entry_px[k] * 1e4
        open_legs[b_e:b_x + 1] += 1
        if not censored[k]:
            gross[b_e:b_x + 1] += inc
            net[b_e:b_x + 1] += inc
            net[b_e] -= cost_bps

    return MultiLegSeries(times, gross, net, open_legs, legs.height, n_censored,
                          float(censored_mtm), n_aborted)


def reconcile(series: MultiLegSeries, cis_trades: pl.DataFrame, *,
              tol_bps: float = RECONCILE_TOL_BPS) -> ReconcileReport:
    """The mandatory pre-verdict invariant: per-bar gross must sum to per-leg realized P&L.

    Completed legs only (censored legs are excluded from ``gross_bps`` by construction).
    Failure means the series is not measuring the strategy's P&L — no verdict, no TEST read,
    no control run may consume it (critical-017 / A-4).
    """
    _require(cis_trades, REQUIRED_LEG_COLS, "cis_trades")
    leg_total = float(cis_trades.filter(pl.col("Censored").cast(pl.Boolean).not_()
                                        & pl.col("RealizedBps").is_finite())
                      .get_column("RealizedBps").sum() or 0.0)
    bar_total = float(series.gross_bps.sum())
    diff = abs(bar_total - leg_total)
    return ReconcileReport(bar_total, leg_total, diff, tol_bps, bool(diff <= tol_bps))


def build_episodes(positions: pl.DataFrame, cis_trades: pl.DataFrame, *,
                   cost_bps: float) -> pl.DataFrame:
    """Episode table: the strategy's P&L-bearing object for multi-leg arms (L-16).

    An episode is a maximal contiguous span of bars with at least one leg open (recomputed
    from leg spans, not the emitted ``OpenLegs`` column). Per episode: net = sum of member
    legs' ``NetBps`` (legs belong to the episode their entry bar falls in); exposure stats
    from the recomputed concurrent-leg count; MAE/underwater from the exposure-correct
    per-bar net series within the span.
    """
    series = assemble_multileg_bps(positions, cis_trades, cost_bps=cost_bps)
    times, net, open_legs = series.times, series.net_bps, series.open_legs
    if cis_trades.height == 0:
        return pl.DataFrame()
    live = cis_trades.filter(pl.col("RealizedBps").is_finite()
                             | pl.col("Censored").cast(pl.Boolean))
    if live.height == 0:
        return pl.DataFrame()
    legs = per_leg_net(live, cost_bps=cost_bps)
    entry_i, _ = _leg_bar_spans(times, legs)
    leg_net = legs.get_column("NetBps").to_numpy()
    leg_censored = legs.get_column("Censored").to_numpy().astype(bool)

    rows = []
    n = len(times)
    i = 0
    while i < n:
        if open_legs[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and open_legs[j + 1] > 0:
            j += 1
        member = (entry_i >= i) & (entry_i <= j)
        span = net[i:j + 1]
        cum = np.cumsum(span)
        uw = int(np.argmax(cum > 0.0)) if np.any(cum > 0.0) else int(j - i + 1)
        rows.append({
            "start_time": times[i], "end_time": times[j],
            "n_bars": int(j - i + 1), "n_legs": int(member.sum()),
            "max_open_legs": int(open_legs[i:j + 1].max()),
            "net_bps": float(leg_net[member & ~leg_censored].sum()),
            "mae_bps": float(min(cum.min(), 0.0)), "underwater_bars": uw,
            "censored": bool(j == n - 1 or (member & leg_censored).any()),
        })
        i = j + 1
    return pl.DataFrame(rows)
