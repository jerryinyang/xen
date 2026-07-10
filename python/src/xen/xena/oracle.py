"""XENA backtest oracle — full chronological shared-capital portfolio simulation (INFR-006 WS-2).

The single sanctioned evaluator of F(S) for the XENA framework (`xena-model.md` §3). Composes
engine-emitted candidate trade streams into one shared account; the only interaction channel
between candidates is capacity-constrained trade admission. It never generates, times, or
prices a trade — all signal logic lives in cTrader (price-primary carve-out, INFR-006 design
§3): a candidate's entry/exit timestamps and fill prices are identical in every subset; only
sizes, admissions, and the account path differ.

Accounting contract (extends `xen.adjudication`, L-18):
* Position P&L accrues per bar via open-to-open marks anchored at the position's own fills —
  the same telescoping construction as ``assemble_multileg_bps``: per position,
  ``sum(increments) == direction * (exit_fill - entry_fill) * size * money_per_unit`` exactly.
* Round-trip cost is charged once, on the entry event (L-02); spread + commission both binding
  (L-22), injected via ``cost_bps`` per candidate (from the FTMO table upstream).
* Reconciliation invariant: ``final_equity - initial_equity == sum(ledger NetMoney)`` (marked
  to last mark for censored positions) — checked on every evaluation; failure raises.

Risk model (`problem-statement.md` §3):
* ``FM(t)`` (free margin) := marked-to-market equity at t. v1 models no leverage margin;
  logged implementation detail, revisable under spec §12.
* New trade risk ``R_i = r · FM(t) · w_i``; units = ``R_i / (stop_distance · money_per_unit)``.
* Global cap: admit only if ``open_risk + R_i <= R_max · FM(t)``; otherwise the signal is
  REJECTED and logged as a first-class event (the non-additivity channel).
* INTERPRETATION NOTE (review F07): `problem-statement.md` §3 writes the cap as
  ``R_current + R_i ≤ R_max`` without fixing R_max's scale; this oracle reads it as a
  FRACTION of FM(t) (cap loosens as equity grows, tightens in drawdown), consistent with
  the r·FM(t) sizing convention. A fixed monetary cap would produce different admission
  dynamics; changing this reading is a calibration-invalidating regime change.

Determinism: ``evaluate(bitmask, streams, config, segment, seed)`` is a pure function —
bit-identical output for identical inputs. Event ordering is total: (time, phase, candidate,
trade_seq) with phase increment < exit < entry, so marks and exits at time t update equity
before an entry at t is sized. ``seed`` is threaded for future stochastic fill models; v1 has
none.

v1 unit limitation: ``money_per_unit`` converts one unit's 1.0 price move into account
currency. Default 1.0 is correct for USD-quoted instruments on a USD account (indices,
XXXUSD); non-USD-quote symbols must pass an explicit factor.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import polars as pl

REQUIRED_TRADE_COLS = ("EntryTime", "ExitTime", "Direction", "EntryPrice", "ExitPrice",
                       "StopDistance", "Censored")
REQUIRED_MARK_COLS = ("CloseTime", "Open")

RECONCILE_TOL_MONEY = 1e-6  # relative to initial equity

# event phases — total order within a timestamp
_PH_MARK, _PH_EXIT, _PH_ENTRY = 0, 1, 2


# --------------------------------------------------------------------------- #
# Input contracts
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CandidateStream:
    """One engine-emitted candidate: its trade-intent ledger + per-bar real-open marks.

    ``trades``: EntryTime, ExitTime, Direction (+1/-1), EntryPrice, ExitPrice, StopDistance
    (price units, >0), Censored (bool; ExitPrice ignored, marked to last mark).
    ``marks``: CloseTime (bar close), Open (the bar's real open) — the candidate symbol's
    price grid used for intra-position mark-to-market (L-09).
    ``cost_bps``: round-trip cost in bps of entry notional (spread + commission, L-22).
    ``money_per_unit``: account-currency value of a 1.0 price move on 1 unit.
    """
    candidate_id: str
    symbol: str
    trades: pl.DataFrame
    marks: pl.DataFrame
    cost_bps: float
    money_per_unit: float = 1.0

    def __post_init__(self) -> None:
        missing = [c for c in REQUIRED_TRADE_COLS if c not in self.trades.columns]
        if missing:
            raise ValueError(f"{self.candidate_id}: trades missing {missing}")
        missing = [c for c in REQUIRED_MARK_COLS if c not in self.marks.columns]
        if missing:
            raise ValueError(f"{self.candidate_id}: marks missing {missing}")


@dataclass(frozen=True)
class OracleConfig:
    """Risk-model parameters (problem-statement §3). All frozen during a XENA run."""
    initial_equity: float = 100_000.0
    risk_per_position: float = 0.005     # r: fraction of FM(t) per new trade
    r_max: float = 0.05                  # global open-risk cap, fraction of FM(t)
    weights: dict[str, float] | None = None   # w_i per candidate_id; None = equal 1.0
    # Operator amendment 2026-07-10 (gross-selection): SELECTION stages (search +
    # certification) run cost-free (charge_costs=False) — commissions/spread are excluded
    # from the portfolio-selection process. The FINAL GATE forces charge_costs=True
    # regardless of what it is handed (L-22: costs are a binding verdict leg). Ledger
    # CostMoney is 0.0 when uncharged.
    charge_costs: bool = True


@dataclass(frozen=True)
class OracleResult:
    """Everything a XENA evaluation may consume downstream. ``F_point`` is the base
    objective's point value; the bootstrap layer wraps this result, never the oracle."""
    equity_times: np.ndarray        # event timestamps (ns int64), monotone
    equity: np.ndarray              # marked-to-market equity after each event
    ledger: pl.DataFrame            # every admitted position (incl. censored)
    rejected: pl.DataFrame          # every capacity-rejected signal (first-class events)
    F_point: float
    n_admitted: int
    n_rejected: int


def default_objective(equity_times: np.ndarray, equity: np.ndarray,
                      initial_equity: float) -> float:
    """Placeholder base objective: total log-wealth. The real F is pre-registered at the
    WS-6 freeze (INFR-006 Q5); everything downstream sees only a scalar."""
    final = equity[-1] if len(equity) else initial_equity
    if final <= 0:
        return float("-inf")
    return float(math.log(final / initial_equity))


# --------------------------------------------------------------------------- #
# Internal: per-trade mark schedule
# --------------------------------------------------------------------------- #
def _trade_mark_schedule(times: np.ndarray, opens: np.ndarray, entry_t: int, exit_t: int,
                         entry_px: float, exit_px: float, censored: bool,
                         ) -> tuple[np.ndarray, np.ndarray]:
    """(mark_times, unit_pnl_increments) for one long-unit position; telescopes exactly to
    ``exit_mark - entry_px``. Marks: entry fill → bar opens strictly inside the span → exit
    fill (or last available open when censored). Mark timestamps are the bar CloseTimes at
    which each open becomes known plus the exit time; every increment is timestamped at or
    after the information that prices it exists (causal)."""
    i0 = int(np.searchsorted(times, entry_t, side="left"))
    if censored:
        i1 = len(times) - 1
        exit_mark = opens[i1]
        exit_time = times[i1]
    else:
        i1 = int(np.searchsorted(times, exit_t, side="left"))
        i1 = min(i1, len(times) - 1)
        exit_mark = exit_px
        exit_time = exit_t
    # interior bar opens: bars i0+1 .. i1 (their opens become known at those bars)
    interior = opens[i0 + 1:i1 + 1]
    interior_t = times[i0 + 1:i1 + 1]
    marks = np.concatenate(([entry_px], interior, [exit_mark]))
    mts = np.concatenate((interior_t, [exit_time]))
    # drop any interior mark timestamped after the exit (short trades inside one bar)
    keep = mts <= exit_time
    # rebuild: increments between consecutive kept marks
    kept_marks = np.concatenate(([entry_px], marks[1:][keep]))
    kept_t = mts[keep]
    if len(kept_t) == 0:  # exit before the next bar: single increment at exit time
        kept_marks = np.array([entry_px, exit_mark])
        kept_t = np.array([exit_time])
    inc = np.diff(kept_marks)
    return kept_t, inc


# --------------------------------------------------------------------------- #
# The oracle
# --------------------------------------------------------------------------- #
def evaluate(bitmask: dict[str, bool] | set[str], streams: list[CandidateStream],
             config: OracleConfig, *, segment: tuple[int, int] | None = None,
             seed: int = 0,
             objective: Callable[[np.ndarray, np.ndarray, float], float] = default_objective,
             ) -> OracleResult:
    """F(S) via the full chronological shared-capital simulation. Pure + deterministic.

    ``bitmask``: included candidate_ids (set, or dict id→bool).
    ``segment``: optional (start_ns, end_ns) — only trades with EntryTime inside are
    considered, AND every position is **censored at the segment end**: the mark grid is
    truncated to ``< end_ns`` and a position whose exit falls at/after the boundary is
    marked to the last in-segment open (the ``Censored`` mechanism). No P&L event ever
    lands outside the segment, so folds built from disjoint segments are disjoint in P&L
    regardless of holding horizon (review finding 1).
    ``seed``: threaded for future stochastic elements; unused in v1.
    """
    del seed  # v1: no stochastic elements; parameter kept for interface stability
    included_ids = ({k for k, v in bitmask.items() if v} if isinstance(bitmask, dict)
                    else set(bitmask))
    streams_by_id = {s.candidate_id: s for s in streams}
    unknown = included_ids - set(streams_by_id)
    if unknown:
        raise ValueError(f"bitmask includes unknown candidates {sorted(unknown)}")
    weights = config.weights or {}

    # ---- build the entry-event heap (deterministic total order) ----
    heap: list[tuple[int, int, str, int, tuple]] = []
    for cid in sorted(included_ids):
        s = streams_by_id[cid]
        tr = s.trades.sort("EntryTime")
        et = tr.get_column("EntryTime").cast(pl.Int64).to_numpy()
        xt = tr.get_column("ExitTime").cast(pl.Int64).to_numpy()
        d = tr.get_column("Direction").to_numpy().astype(float)
        ep = tr.get_column("EntryPrice").to_numpy().astype(float)
        xp = tr.get_column("ExitPrice").to_numpy().astype(float)
        sd = tr.get_column("StopDistance").to_numpy().astype(float)
        cz = tr.get_column("Censored").to_numpy().astype(bool)
        if (sd <= 0).any():
            raise ValueError(f"{cid}: non-positive StopDistance")
        mk = s.marks.sort("CloseTime")
        mtimes = mk.get_column("CloseTime").cast(pl.Int64).to_numpy()
        mopens = mk.get_column("Open").to_numpy().astype(float)
        if segment is not None:
            in_seg = mtimes < segment[1]
            mtimes, mopens = mtimes[in_seg], mopens[in_seg]
        for k in range(tr.height):
            if segment is not None and not (segment[0] <= et[k] < segment[1]):
                continue
            # segment-end censoring: an exit at/after the boundary is marked to the last
            # in-segment open, exactly like a fence-censored leg (finding 1)
            censored_k = bool(cz[k]) or (segment is not None and int(xt[k]) >= segment[1])
            if len(mtimes) == 0 or et[k] > mtimes[-1]:
                continue  # no in-segment mark can price this entry
            heap.append((int(et[k]), _PH_ENTRY, cid, k,
                         (d[k], ep[k], xp[k], sd[k], censored_k, mtimes, mopens,
                          int(xt[k]))))
    heapq.heapify(heap)

    equity = config.initial_equity
    open_risk = 0.0
    eq_t: list[int] = [0 if not heap else heap[0][0]]
    eq_v: list[float] = [equity]
    ledger_rows: list[dict] = []
    rejected_rows: list[dict] = []
    open_risk_by_key: dict[tuple[str, int], float] = {}
    total_cost = 0.0
    seq = 0  # global tiebreak for pushed mark/exit events

    while heap:
        t, phase, cid, k, payload = heapq.heappop(heap)
        if phase == _PH_MARK:
            money_inc, = payload
            equity += money_inc
            eq_t.append(t)
            eq_v.append(equity)
        elif phase == _PH_EXIT:
            open_risk -= open_risk_by_key.pop((cid, k))
        else:  # _PH_ENTRY — size against current marked equity
            d, ep, xp, sd, cz, mtimes, mopens, xt_k = payload
            s = streams_by_id[cid]
            w = float(weights.get(cid, 1.0))
            fm = equity
            r_i = config.risk_per_position * fm * w
            if open_risk + r_i > config.r_max * fm + 1e-12:
                rejected_rows.append({"Time": t, "CandidateId": cid, "TradeSeq": k,
                                      "RiskRequested": r_i, "OpenRisk": open_risk,
                                      "RiskCap": config.r_max * fm})
                continue
            units = r_i / (sd * s.money_per_unit)
            cost = (s.cost_bps / 1e4 * units * ep * s.money_per_unit
                    if config.charge_costs else 0.0)
            equity -= cost
            total_cost += cost
            eq_t.append(t)
            eq_v.append(equity)
            open_risk += r_i
            open_risk_by_key[(cid, k)] = r_i
            mark_t, unit_inc = _trade_mark_schedule(mtimes, mopens, t, xt_k, ep, xp, cz)
            gross = 0.0
            for mt, inc in zip(mark_t, unit_inc):
                money = d * inc * units * s.money_per_unit
                gross += money
                seq += 1
                heapq.heappush(heap, (int(mt), _PH_MARK, cid, seq, (money,)))
            exit_time = int(mark_t[-1])
            seq += 1
            heapq.heappush(heap, (exit_time, _PH_EXIT, cid, k, ()))
            ledger_rows.append({"CandidateId": cid, "TradeSeq": k, "EntryTime": t,
                                "ExitTime": exit_time, "Direction": d, "Units": units,
                                "EntryPrice": ep, "Risk": r_i, "GrossMoney": gross,
                                "CostMoney": cost, "NetMoney": gross - cost,
                                "Censored": cz})

    ledger = pl.DataFrame(ledger_rows) if ledger_rows else pl.DataFrame(
        schema={"CandidateId": pl.Utf8, "TradeSeq": pl.Int64, "EntryTime": pl.Int64,
                "ExitTime": pl.Int64, "Direction": pl.Float64, "Units": pl.Float64,
                "EntryPrice": pl.Float64, "Risk": pl.Float64, "GrossMoney": pl.Float64,
                "CostMoney": pl.Float64, "NetMoney": pl.Float64, "Censored": pl.Boolean})
    rejected = pl.DataFrame(rejected_rows) if rejected_rows else pl.DataFrame(
        schema={"Time": pl.Int64, "CandidateId": pl.Utf8, "TradeSeq": pl.Int64,
                "RiskRequested": pl.Float64, "OpenRisk": pl.Float64, "RiskCap": pl.Float64})

    # ---- reconciliation invariant (L-18): equity delta == ledger net ----
    ledger_net = float(ledger.get_column("NetMoney").sum() or 0.0) if ledger.height else 0.0
    diff = abs((equity - config.initial_equity) - ledger_net)
    if diff > RECONCILE_TOL_MONEY * config.initial_equity:
        raise AssertionError(
            f"oracle reconciliation failed: equity delta {equity - config.initial_equity:.6f} "
            f"vs ledger net {ledger_net:.6f} (diff {diff:.6f})")

    times = np.asarray(eq_t, dtype=np.int64)
    eqv = np.asarray(eq_v, dtype=float)
    return OracleResult(times, eqv, ledger, rejected,
                        objective(times, eqv, config.initial_equity),
                        ledger.height, rejected.height)
