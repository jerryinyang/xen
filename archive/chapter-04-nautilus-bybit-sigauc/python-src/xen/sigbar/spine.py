"""CF-SIGAUC-001 statistical spine (S1 + S2) — SPDR-007 shared computation.

The single new module the SPDR-007 design (§9) permits. It builds the S1
confirmed-break event population from the FROZEN INFR-018 pin, measures each
event's session-horizon excursion and its target-before-invalidation race, fits
and verifies the S2 Protection quantile, and supplies the matched-unconditional
control, the side-derangement control, and the future-destroy outcome-path-swap
tripwire.

Every entry — real, control, or tripwire — is routed through ONE evaluator
(:func:`evaluate_entries`) so the exit rule (TP before STOP, pessimistic same-bar,
session-end timeout) is bit-identically matched across arms (L-24 F04). Nothing
here books P&L: the metrics are real-price excursions in IB-width units and a
win-rate, the availability toolbox the SPDR lane permits — not an accounting
primitive (`check_no_local_accounting` stays trivially satisfied).

All prices are REAL bar prices; the entry is the OPEN of the bar at
``qualify_end`` (decision on confirmed data ≤ t−1); the outcome window is the
bars STRICTLY AFTER that entry bar up to ``session_end``. Causal by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from xen.sigbar.acceptance import Discriminator, evaluate_discriminator, find_pokes
from xen.sigbar.sessions import AnchorSpec, CANDIDATE_ANCHORS, anchor_table, attach_sessions, session_breaks

# --------------------------------------------------------------------------- #
# Frozen parameters — inherited from the INFR-018 pin, never re-selected here.
# --------------------------------------------------------------------------- #
ANCHOR_ID = "A-USOPEN"
IB_MINUTES = 15
#: A6 = D4, tau=0.50, w=30 min, price-only; poke depth delta=0 (INFR-018 registry).
A6_DISCRIMINATOR = Discriminator("D4-t50-w30", "D4", False, {"tau": 0.50, "w": 30})
POKE_DELTA = 0.0

#: S2 resolution rule (design §3.2): TP1 = Protection Level; STOP = TP1/2 (1:2 R).
STOP_FRACTION = 0.5
#: p ≈ 0.65–0.70 (source S2); the Protection Level is the (1−p) quantile of MFE.
P_VALUES = (0.65, 0.70)

#: Matched-control replicates per event (design §4.2; ≥ L-19 floor of 25).
N_CONTROL = 30
#: Control entries may not land within this many minutes of the event they control.
CONTROL_EXCLUSION_MIN = 30
#: Regime percentile window (design §4.1): trailing 60 sessions, min 30 priors.
REGIME_WINDOW = 60
REGIME_MIN_PRIORS = 30
N_TERCILES = 3

#: Calendar-day block for the clustered bootstrap (source §6b; matches INFR-018).
DAY_BLOCK = 5

# Deterministic seeds — every randomised draw fixes one (streaming-safe).
SEED_CONTROL = 20180701
SEED_SIDE_DERANGE = 20180703
SEED_PATH_SWAP = 20180705

_ANCHOR_SPEC: AnchorSpec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == ANCHOR_ID)


# --------------------------------------------------------------------------- #
# Guards (design §7 HARD — raise, never warn)
# --------------------------------------------------------------------------- #
def anchor_spec() -> AnchorSpec:
    """The frozen A-USOPEN anchor spec (DST-correct, from the shared registry)."""
    return _ANCHOR_SPEC


def protection_level(mfe_norm: np.ndarray, p: float) -> float:
    """The Protection Level = the ``(1−p)`` quantile of normalised favourable excursion.

    A target reached with probability ``p`` is the ``(1−p)`` quantile of MFE
    (source S2 MECHANISM). ``p ≈ 0.65–0.70 → q ≈ 0.30–0.35``. The reversed
    reading (``p`` quantile) roughly doubles TP1 and falsifies S1 for the wrong
    reason, so a request for a quantile above 0.5 RAISES (design §3.3 / GT-4d).
    """
    q = 1.0 - p
    if q > 0.5:
        raise ValueError(
            f"protection_level: q={q:.3f} > 0.5 is the reversed-quantile trap "
            f"(p={p} implies the {q:.2f} quantile of MFE, not {p}); refused (design §3.3)"
        )
    a = np.asarray(mfe_norm, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan")
    return float(np.quantile(a, q))


def assert_entry_after_qualify(events: pl.DataFrame) -> None:
    """Raise unless every event's entry is the bar at ``qualify_end`` (design §2)."""
    if events.height == 0:
        return
    bad = events.filter(pl.col("entry_ts") != pl.col("qualify_end")).height
    if bad:
        raise RuntimeError(
            f"ENTRY SEAM: {bad} events have entry_ts != qualify_end — the entry must be the "
            "open of the bar at qualify_end (design §2/§3.2)"
        )


# --------------------------------------------------------------------------- #
# Event population — every A6-ACCEPTED poke under the frozen rule.
# --------------------------------------------------------------------------- #
def build_events(joined: pl.DataFrame, sessions: pl.DataFrame) -> pl.DataFrame:
    """Return one row per S1 confirmed break (A6-accepted poke) with entry state.

    The event population is exactly ``says_accept == True`` under the frozen
    discriminator (design §3.1) — NOT the resolved-and-accept subset. The entry
    is the open of the bar at ``qualify_end``; events whose entry bar is missing
    (a data gap on that exact minute) are dropped and their count returned.

    Parameters
    ----------
    joined :
        ``attach_sessions`` output for one symbol (carries ``anchor_ts``,
        ``mins_since``, ``ib_minutes``); residual columns optional (unused for
        the price-only D4).
    sessions :
        ``session_breaks`` output for the same symbol.

    Returns
    -------
    polars.DataFrame
        ``anchor_ts, poke_ts, poke_side, qualify_end, entry_ts, entry, side,
        ib_high, ib_low, ib_width, session_end, entry_phase, day`` plus a
        single-row attr-like ``_n_missing_entry`` is NOT attached (see
        :func:`build_events_with_diag`).
    """
    return build_events_with_diag(joined, sessions)[0]


def build_events_with_diag(joined: pl.DataFrame, sessions: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """:func:`build_events` plus a diagnostics dict (poke/accept/missing counts)."""
    pokes = find_pokes(joined, sessions, POKE_DELTA)
    diag = {"n_pokes": int(pokes.height)}
    if pokes.height == 0:
        return _empty_events(), {**diag, "n_accepts": 0, "n_missing_entry": 0}

    ev = evaluate_discriminator(joined, pokes, A6_DISCRIMINATOR)
    accepted = pokes.join(ev.filter(pl.col("says_accept")), on="anchor_ts", how="inner")
    diag["n_accepts"] = int(accepted.height)
    if accepted.height == 0:
        return _empty_events(), {**diag, "n_missing_entry": 0}

    # Entry = the open of the bar at qualify_end. join, not asof: the entry must
    # be that exact minute or the event is not evaluable (a gap there).
    entry_bar = joined.select(
        pl.col("OpenTime").alias("entry_ts"), pl.col("Open").alias("entry")
    )
    events = accepted.with_columns(pl.col("qualify_end").alias("entry_ts")).join(
        entry_bar, on="entry_ts", how="left"
    )
    n_missing = int(events.filter(pl.col("entry").is_null()).height)
    events = events.drop_nulls("entry")

    events = events.with_columns(
        pl.col("poke_side").alias("side"),
        ((pl.col("entry_ts") - pl.col("anchor_ts")).dt.total_minutes()).alias("entry_phase"),
        pl.col("entry_ts").dt.truncate("1d").alias("day"),
        (1e4 * pl.col("ib_width") / ((pl.col("ib_high") + pl.col("ib_low")) / 2.0)).alias("ib_width_bps"),
    ).select(
        "anchor_ts", "poke_ts", "poke_side", "qualify_end", "entry_ts", "entry", "side",
        "ib_high", "ib_low", "ib_width", "ib_width_bps", "session_end", "entry_phase", "day",
    )
    assert_entry_after_qualify(events)
    return events, {**diag, "n_missing_entry": n_missing}


def _empty_events() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "anchor_ts": pl.Datetime, "poke_ts": pl.Datetime, "poke_side": pl.Int64,
            "qualify_end": pl.Datetime, "entry_ts": pl.Datetime, "entry": pl.Float64,
            "side": pl.Int64, "ib_high": pl.Float64, "ib_low": pl.Float64,
            "ib_width": pl.Float64, "ib_width_bps": pl.Float64, "session_end": pl.Datetime,
            "entry_phase": pl.Int64, "day": pl.Datetime,
        }
    )


# --------------------------------------------------------------------------- #
# The single entry evaluator — real, control, and tripwire all route here.
# --------------------------------------------------------------------------- #
@dataclass
class _SymbolBars:
    """One symbol's bar arrays for fast first-passage evaluation."""

    ts: np.ndarray      # OpenTime, int64 ns, sorted ascending
    open_: np.ndarray
    high: np.ndarray
    low: np.ndarray


def _symbol_bars(bars: pl.DataFrame) -> _SymbolBars:
    b = bars.sort("OpenTime")
    return _SymbolBars(
        ts=b["OpenTime"].to_numpy().astype("datetime64[ns]").astype("int64"),
        open_=b["Open"].to_numpy().astype(float),
        high=b["High"].to_numpy().astype(float),
        low=b["Low"].to_numpy().astype(float),
    )


def evaluate_entries(
    bars: pl.DataFrame,
    entries: pl.DataFrame,
    *,
    tp1_ibw: dict[int, float] | float | None = None,
    high_override: np.ndarray | None = None,
    low_override: np.ndarray | None = None,
) -> pl.DataFrame:
    """Excursion + TP-before-STOP race for a set of entries in one symbol's bars.

    The ONE evaluator every arm uses (design §9). For each entry it takes the
    bars strictly after ``entry_ts`` up to ``session_end`` and computes, on REAL
    prices: ``mfe``/``mae`` (side-relative maxima), their IB-width-normalised
    forms, ``asym``, ``remaining_horizon`` (minutes), and — when ``tp1_ibw`` is
    supplied — the race outcome ``TP`` / ``STOP`` / ``TIMEOUT``.

    Race rule (design §3.2): TP distance = ``tp1_ibw · ib_width`` (favourable),
    STOP distance = ``STOP_FRACTION · tp1_ibw · ib_width`` (adverse), first
    passage; if a single bar spans both levels the outcome is ``STOP``
    (pessimistic — sub-minute order is unavailable, source A2).

    Parameters
    ----------
    entries :
        ``entry_ts, session_end, entry, side, ib_width`` (+ ``anchor_ts`` id and
        any carry-through columns, preserved on output).
    tp1_ibw :
        Protection Level in IB-width units. A scalar applies to all entries; a
        ``{side: value}`` dict applies per side; ``None`` skips the race.
    high_override, low_override :
        Replacement High/Low arrays (same length/order as the symbol's bars) —
        the outcome-path-swap tripwire supplies a spliced path here. Entry prices
        in ``entries`` are unchanged; only the outcome bars move.
    """
    sb = _symbol_bars(bars)
    high = sb.high if high_override is None else np.asarray(high_override, dtype=float)
    low = sb.low if low_override is None else np.asarray(low_override, dtype=float)
    if len(high) != len(sb.ts) or len(low) != len(sb.ts):
        raise ValueError("override arrays must match the symbol's bar count")

    e = entries.sort("entry_ts")
    e_ts = e["entry_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    e_end = e["session_end"].to_numpy().astype("datetime64[ns]").astype("int64")
    e_entry = e["entry"].to_numpy().astype(float)
    e_side = e["side"].to_numpy().astype(int)
    e_ibw = e["ib_width"].to_numpy().astype(float)

    def _tp(side: int) -> float:
        if tp1_ibw is None:
            return float("nan")
        return float(tp1_ibw[side]) if isinstance(tp1_ibw, dict) else float(tp1_ibw)

    n = len(e_ts)
    mfe = np.full(n, np.nan)
    mae = np.full(n, np.nan)
    rem = np.full(n, np.nan)
    outcome = np.empty(n, dtype=object)
    n_post = np.zeros(n, dtype=int)

    # First bar strictly after entry_ts; first bar at/after session_end.
    i0 = np.searchsorted(sb.ts, e_ts, side="right")
    i1 = np.searchsorted(sb.ts, e_end, side="left")

    for k in range(n):
        a, b = i0[k], i1[k]
        n_post[k] = max(0, b - a)
        rem[k] = (e_end[k] - e_ts[k]) / 6e10  # ns → minutes
        if b <= a:
            outcome[k] = "NO_WINDOW"
            continue
        hi = high[a:b]
        lo = low[a:b]
        side = e_side[k]
        entry = e_entry[k]
        if side == 1:
            mfe[k] = float(hi.max()) - entry
            mae[k] = entry - float(lo.min())
        else:
            mfe[k] = entry - float(lo.min())
            mae[k] = float(hi.max()) - entry
        if tp1_ibw is None:
            outcome[k] = ""
            continue
        tp_d = _tp(side) * e_ibw[k]
        stop_d = STOP_FRACTION * _tp(side) * e_ibw[k]
        if side == 1:
            tp_hit = hi >= entry + tp_d
            stop_hit = lo <= entry - stop_d
        else:
            tp_hit = lo <= entry - tp_d
            stop_hit = hi >= entry + stop_d
        first_tp = int(np.argmax(tp_hit)) if tp_hit.any() else len(hi)
        first_stop = int(np.argmax(stop_hit)) if stop_hit.any() else len(hi)
        if first_stop == len(hi) and first_tp == len(hi):
            outcome[k] = "TIMEOUT"
        elif first_stop <= first_tp:          # same-bar → STOP (pessimistic)
            outcome[k] = "STOP"
        else:
            outcome[k] = "TP"

    out = e.with_columns(
        pl.Series("mfe", mfe), pl.Series("mae", mae),
        pl.Series("remaining_horizon", rem), pl.Series("n_post", n_post),
        pl.Series("outcome", outcome),
    ).with_columns(
        pl.when(pl.col("ib_width") > 0).then(pl.col("mfe") / pl.col("ib_width")).otherwise(None).alias("mfe_norm"),
        pl.when(pl.col("ib_width") > 0).then(pl.col("mae") / pl.col("ib_width")).otherwise(None).alias("mae_norm"),
    ).with_columns(
        (pl.col("mfe_norm") - pl.col("mae_norm")).alias("asym"),
    )
    return out


# --------------------------------------------------------------------------- #
# Regime percentile (trailing, causal ≤ t−1) and coherence score.
# --------------------------------------------------------------------------- #
def regime_percentile(events: pl.DataFrame, sessions: pl.DataFrame) -> pl.DataFrame:
    """Attach ``ib_width_pctl`` = trailing-SESSION rank of this session's IB-width bps.

    The rank is against the symbol's own **sessions** (source §4.1 / S2
    DEPENDS-ON: "trailing ~60 sessions"), NOT the sparse accepted-break events —
    ranking against events would use a different, signal-conditioned reference.
    Causal: only STRICTLY PRIOR sessions (≤ t−1), a window of up to
    :data:`REGIME_WINDOW` with a minimum of :data:`REGIME_MIN_PRIORS` priors;
    a session with fewer priors gets a null percentile (excluded + counted).
    Also attaches ``ib_width_pctl_acausal`` (full-session-sample rank) as the §7
    disclosure probe — never used for conditioning.
    """
    empties = (pl.lit(None, dtype=pl.Float64).alias("ib_width_pctl"),
               pl.lit(None, dtype=pl.Float64).alias("ib_width_pctl_acausal"))
    if events.height == 0:
        return events.with_columns(*empties)
    s = sessions.filter(pl.col("ib_width") > 0).sort("anchor_ts").with_columns(
        (1e4 * pl.col("ib_width") / ((pl.col("ib_high") + pl.col("ib_low")) / 2.0)).alias("sw_bps")
    )
    s_ts = s["anchor_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    s_w = s["sw_bps"].to_numpy().astype(float)
    ns = len(s_w)
    order = s_w.argsort().argsort()
    acaus_by_ts = {int(t): order[i] / max(ns - 1, 1) for i, t in enumerate(s_ts)}

    e = events.sort("anchor_ts")
    e_ts = e["anchor_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    caus = np.full(len(e_ts), np.nan)
    acaus = np.full(len(e_ts), np.nan)
    for k, t in enumerate(e_ts):
        idx = int(np.searchsorted(s_ts, t, side="left"))  # sessions strictly before this anchor
        lo = max(0, idx - REGIME_WINDOW)
        prior = s_w[lo:idx]
        if len(prior) >= REGIME_MIN_PRIORS:
            caus[k] = float((prior < s_w[idx if idx < ns else ns - 1]).mean())
        acaus[k] = acaus_by_ts.get(int(t), np.nan)
    return e.with_columns(pl.Series("ib_width_pctl", caus), pl.Series("ib_width_pctl_acausal", acaus))


def attach_coherence(events: pl.DataFrame, joined_resid: pl.DataFrame) -> pl.DataFrame:
    """Attach ``coh`` = mean ``delta_ratio_resid`` over the qualifying window × side.

    Reads the FROZEN A5 residual (never a raw Δ number; card ban 2). The
    qualifying window is ``[poke_ts, qualify_end)`` — strictly pre-entry, so the
    score is causal. Positive ``coh`` = aggression leaned in the poke's direction
    versus the seasonal norm.
    """
    if events.height == 0:
        return events.with_columns(pl.lit(None, dtype=pl.Float64).alias("coh"))
    q = (
        joined_resid.join(
            events.select("anchor_ts", "poke_ts", "qualify_end", "poke_side"),
            on="anchor_ts", how="inner",
        )
        .filter((pl.col("OpenTime") >= pl.col("poke_ts")) & (pl.col("OpenTime") < pl.col("qualify_end")))
        .group_by("anchor_ts")
        .agg((pl.col("delta_ratio_resid").mean() * pl.col("poke_side").first()).alias("coh"))
    )
    return events.join(q, on="anchor_ts", how="left")


def tercile_edges(values: np.ndarray) -> tuple[float, float]:
    """The 1/3 and 2/3 cut points of a value array (frozen on DESIGN, applied to CONFIRM)."""
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if a.size < N_TERCILES:
        return float("nan"), float("nan")
    return float(np.quantile(a, 1 / 3)), float(np.quantile(a, 2 / 3))


def apply_terciles(values: pl.Expr, lo: float, hi: float) -> pl.Expr:
    """Map a value column to tercile labels 0/1/2 given frozen cut points."""
    return (
        pl.when(values <= lo).then(0).when(values <= hi).then(1).otherwise(2)
    )


# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #
def matched_unconditional(
    bars: pl.DataFrame,
    events: pl.DataFrame,
    sessions: pl.DataFrame,
    tp1_ibw: dict[int, float] | float,
    *,
    n_control: int = N_CONTROL,
    seed: int = SEED_CONTROL,
) -> pl.DataFrame:
    """Cross-session phase-matched unconditional control, evaluated identically to the real arm.

    DEVIATION FROM DESIGN §4.2 (developer, recorded — see module DEVIATIONS): the
    design's within-session phase-matched control is INFEASIBLE by construction.
    The real event enters at ``entry_phase`` ≈ 45–55 min into the session, which is
    precisely the ``[poke − 30, qualify_end + 30]`` exclusion band, so a
    within-session draw matched to that phase always lands inside the exclusion and
    is forced to a later (mid-session) minute — reintroducing the exact horizon
    confound QA I-2 identified (measured: control remaining-horizon 723 min vs the
    real events' 1391). Phase-matching therefore requires OTHER sessions.

    For each real event (side ``d``, phase ``φ`` = entry_phase), ``n_control``
    DONOR sessions are drawn (seeded) from the symbol's own session pool,
    excluding the event's own session, each entered at ``anchor(donor) + φ`` on
    side ``d`` and normalised by the DONOR session's own IB width. This is:
      - phase-matched → remaining horizon matches the real event by construction;
      - side-matched;
      - disjoint (donor ≠ event session);
      - unconditional on acceptance (donors are not filtered by the A6 call),
    so the contrast isolates the acceptance conditioning, not window length, and
    answers the source §6.3 / card §5 P-01 question ("is it the event or the
    session's own directional drift at that phase?").
    """
    if events.height == 0 or sessions.height == 0:
        return evaluate_entries(bars, _empty_control(), tp1_ibw=None)
    rng = np.random.default_rng(seed)

    sess = sessions.filter(pl.col("ib_width") > 0).sort("anchor_ts")
    s_anchor = sess["anchor_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    s_end = sess["session_end"].to_numpy().astype("datetime64[ns]").astype("int64")
    s_ibw = sess["ib_width"].to_numpy().astype(float)
    ns = len(s_anchor)
    s_len_min = (s_end - s_anchor) // 60_000_000_000
    # Donor session's own trailing-60 regime percentile, so the control arm carries
    # a matched ib_width_pctl for the R3 contrast (else R3 falls back to the raw
    # signal ρ the I-3 normaliser-mechanic guard forbids).
    s_wbps = 1e4 * s_ibw / (((sess["ib_high"] + sess["ib_low"]) / 2.0).to_numpy().astype(float))
    s_pctl = np.full(ns, np.nan)
    for i in range(ns):
        lo = max(0, i - REGIME_WINDOW)
        prior = s_wbps[lo:i]
        if len(prior) >= REGIME_MIN_PRIORS:
            s_pctl[i] = float((prior < s_wbps[i]).mean())

    ev = events.select("anchor_ts", "side", "entry_phase").to_dicts()
    ev_anchor_ns = {int(np.datetime64(r["anchor_ts"], "ns").astype("int64")) for r in ev}

    rows = []
    for r in ev:
        phase = int(r["entry_phase"])
        side = int(r["side"])
        # donors: sessions long enough for this phase, excluding the event's own
        elig = [i for i in range(ns) if s_len_min[i] > phase + 1 and int(s_anchor[i]) not in ev_anchor_ns]
        if not elig:
            continue
        pick = rng.choice(elig, size=min(n_control, len(elig)),
                          replace=len(elig) < n_control)
        for i in pick:
            ctrl_ts = int(s_anchor[i]) + phase * 60_000_000_000
            rows.append({
                "anchor_ts": r["anchor_ts"], "entry_ts_ns": ctrl_ts,
                "session_end_ns": int(s_end[i]), "side": side, "ib_width": float(s_ibw[i]),
                "ib_width_pctl": (None if not np.isfinite(s_pctl[i]) else float(s_pctl[i])),
            })
    if not rows:
        return evaluate_entries(bars, _empty_control(), tp1_ibw=None)

    ctrl = pl.DataFrame(rows).with_columns(
        pl.from_epoch(pl.col("entry_ts_ns"), time_unit="ns").cast(bars["OpenTime"].dtype).alias("entry_ts"),
        pl.from_epoch(pl.col("session_end_ns"), time_unit="ns").cast(bars["OpenTime"].dtype).alias("session_end"),
    ).drop("entry_ts_ns", "session_end_ns")
    # Entry price = OPEN of the bar at the donor's phase minute; drop draws with no bar there.
    entry_bar = bars.select(pl.col("OpenTime").alias("entry_ts"), pl.col("Open").alias("entry"))
    ctrl = ctrl.join(entry_bar, on="entry_ts", how="left").drop_nulls("entry")
    # A UNIQUE row id — control rows collide on entry_ts (different events can pick the
    # same donor session at the same phase), so any downstream attach must key on _rid,
    # never on entry_ts, or a many-to-many join explodes.
    ctrl = ctrl.with_columns(
        pl.col("entry_ts").dt.truncate("1d").alias("day"),
        pl.int_range(pl.len(), dtype=pl.Int64).alias("_rid"),
    )
    # tp1_ibw is accepted for API symmetry; the race is added per-p downstream by the
    # runner (excursion is tp1-independent), so evaluate excursion only here.
    del tp1_ibw
    out = evaluate_entries(bars, ctrl, tp1_ibw=None)
    # D-1 / GT-4(e): donor entry must not land inside the event's own session window
    # (cross-session disjoint — replaces the within-session CONTROL_EXCLUSION_MIN path).
    assert_control_cross_session_disjoint(events, out)
    return out


def assert_control_cross_session_disjoint(events: pl.DataFrame, control: pl.DataFrame) -> None:
    """Raise if any control entry lands inside its event's session (D-1 integrity / GT-4e).

    ``CONTROL_EXCLUSION_MIN`` named the old within-session exclusion; under D-1 the
    hard rule is stronger: donor session ≠ event session, so the control entry
    cannot fall in ``[event.anchor_ts, event.session_end)``.
    """
    if control.height == 0 or events.height == 0:
        return
    keys = ["anchor_ts"]
    if "symbol" in events.columns and "symbol" in control.columns:
        keys = ["symbol", "anchor_ts"]
    ev = events.select(*keys, "session_end").unique(subset=keys)
    j = control.select(*keys, "entry_ts").join(ev, on=keys, how="inner")
    bad = j.filter(
        (pl.col("entry_ts") >= pl.col("anchor_ts"))
        & (pl.col("entry_ts") < pl.col("session_end"))
    )
    if bad.height:
        raise RuntimeError(
            f"CONTROL DISJOINT FAIL: {bad.height} control entries land inside their event "
            f"session window (D-1 / design §4.2 / GT-4e; CONTROL_EXCLUSION_MIN={CONTROL_EXCLUSION_MIN})"
        )


def _empty_control() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "anchor_ts": pl.Datetime, "entry_ts": pl.Datetime, "session_end": pl.Datetime,
            "side": pl.Int64, "ib_width": pl.Float64, "ib_width_pctl": pl.Float64,
            "entry": pl.Float64, "day": pl.Datetime, "_rid": pl.Int64,
        }
    )


def derange_within_day(events: pl.DataFrame, col: str, *, seed: int = SEED_SIDE_DERANGE) -> tuple[pl.DataFrame, dict]:
    """Derange ``col`` within calendar-day blocks; zero fixed points, asserted (L-28).

    A day block with one event, or an all-one-value block, cannot be deranged to
    zero fixed points — those events are DROPPED and COUNTED (design §4.2 / QA
    I-5). Returns the derangeable subset with ``col`` replaced and a coverage
    dict; the caller reports the deranged fraction beside the collapse fraction.
    """
    if events.height == 0:
        return events, {"n_input": 0, "n_deranged": 0, "n_dropped_singleton": 0, "fixed_point_rate": 0.0}
    rng = np.random.default_rng(seed)
    keep_parts: list[pl.DataFrame] = []
    n_dropped = 0
    n_dropped_infeasible = 0
    for _, block in events.group_by("day", maintain_order=True):
        vals = block[col].to_numpy()
        m = len(vals)
        if m < 2 or len(np.unique(vals)) < 2:
            n_dropped += m
            continue
        # A value-derangement exists iff no value occupies more than half the block
        # (three '+1's among four cannot all be sent to the single '−1'). Such a
        # block is dropped and counted (design §4.2 singleton/coverage rule, I-5).
        _, counts = np.unique(vals, return_counts=True)
        if int(counts.max()) * 2 > m:
            n_dropped_infeasible += m
            continue
        perm = _derangement(m, vals, rng)
        keep_parts.append(block.with_columns(pl.Series(col, vals[perm])))
    if not keep_parts:
        return events.head(0), {
            "n_input": int(events.height), "n_deranged": 0,
            "n_dropped_singleton": n_dropped, "n_dropped_infeasible": n_dropped_infeasible,
            "fixed_point_rate": 0.0,
        }
    out = pl.concat(keep_parts)
    return out, {
        "n_input": int(events.height), "n_deranged": int(out.height),
        "n_dropped_singleton": n_dropped, "n_dropped_infeasible": n_dropped_infeasible,
        "fixed_point_rate": 0.0,
    }


def _derangement(m: int, vals: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """A permutation index with zero VALUE fixed points (vals[perm[i]] != vals[i])."""
    for _ in range(200):
        perm = rng.permutation(m)
        if not np.any(vals[perm] == vals):
            return perm
    # Deterministic fallback: rotate, then repair any residual value-fixed points.
    perm = np.roll(np.arange(m), 1)
    for i in range(m):
        if vals[perm[i]] == vals[i]:
            for j in range(m):
                if vals[perm[j]] != vals[i] and vals[perm[i]] != vals[j]:
                    perm[i], perm[j] = perm[j], perm[i]
                    break
    if np.any(vals[perm] == vals):
        raise RuntimeError("could not construct a zero-fixed-point derangement")
    return perm


# --------------------------------------------------------------------------- #
# Outcome-path-swap tripwire (future-destroy, HARD) + positive control plant.
# --------------------------------------------------------------------------- #
def outcome_path_swap(
    bars: pl.DataFrame,
    events: pl.DataFrame,
    tp1_ibw: dict[int, float] | float,
    *,
    seed: int = SEED_PATH_SWAP,
) -> tuple[pl.DataFrame, dict]:
    """Replace each event's OUTCOME path with a deranged donor's, re-based to entry.

    Everything at or before the entry bar is untouched, so every conditioning
    quantity is identical while the outcome is unrelated to it (design §4.3). The
    donor's outcome-window High/Low are re-timed onto the target window and
    re-based so the donor's entry-price maps to the target's entry (destroy the
    OUTCOME's relation to the conditioning, not the price scale). Donors are a
    within-symbol derangement matched on remaining-session length bucket; events
    with no usable donor are dropped and counted.

    Returns ``(evaluated_swapped_events, coverage)``.
    """
    if events.height < 2:
        return evaluate_entries(bars, events.head(0), tp1_ibw=tp1_ibw), {
            "n_input": int(events.height), "n_spliced": 0, "n_no_donor": int(events.height),
            "spliced_fraction": 0.0,
        }
    sb = _symbol_bars(bars)
    rng = np.random.default_rng(seed)

    e = events.sort("entry_ts")
    e_ts = e["entry_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    e_end = e["session_end"].to_numpy().astype("datetime64[ns]").astype("int64")
    e_entry = e["entry"].to_numpy().astype(float)
    i0 = np.searchsorted(sb.ts, e_ts, side="right")
    i1 = np.searchsorted(sb.ts, e_end, side="left")
    lengths = i1 - i0
    n = len(e_ts)

    # Donor derangement bucketed by remaining-length decile so a spliced window
    # is long enough for the target (short donor → truncated, dropped).
    buckets = np.clip((lengths / max(lengths.max(), 1) * 10).astype(int), 0, 9)
    donor = _bucketed_derangement(buckets, rng)

    high = sb.high.copy()
    low = sb.low.copy()
    keep = np.zeros(n, dtype=bool)
    n_no_donor = 0
    for k in range(n):
        d = donor[k]
        if d < 0 or lengths[d] < lengths[k] or lengths[k] <= 0:
            n_no_donor += 1
            continue
        # Donor outcome path, re-based so donor entry-price → target entry-price.
        d_hi = sb.high[i0[d]:i0[d] + lengths[k]].copy()
        d_lo = sb.low[i0[d]:i0[d] + lengths[k]].copy()
        offset = e_entry[k] - e_entry[d]
        high[i0[k]:i1[k]] = d_hi + offset
        low[i0[k]:i1[k]] = d_lo + offset
        keep[k] = True

    # Carry each kept event's DONOR anchor so a genuine bite test can correlate the
    # swapped excursion against the donor's OWN real excursion (a real positive
    # control, not a tautology): if the swap installed the donor's outcome path,
    # swapped asym tracks donor asym; if it reached nothing, they are independent.
    e_anchor_ns = e["anchor_ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    donor_anchor_ns = np.where(keep, e_anchor_ns[np.where(keep, donor, 0)], 0).astype("int64")
    e = e.with_columns(pl.Series("donor_anchor_ns", donor_anchor_ns))
    kept = e.filter(pl.Series(keep)).with_columns(
        pl.from_epoch(pl.col("donor_anchor_ns"), time_unit="ns").cast(e["anchor_ts"].dtype).alias("donor_anchor_ts")
    ).drop("donor_anchor_ns")
    # Excursion always; race at each Protection level when a mapping is supplied.
    # A bare float/side-dict keeps the legacy single `outcome` column.
    if isinstance(tp1_ibw, dict) and tp1_ibw and all(
        isinstance(k, str) and k.startswith("p") for k in tp1_ibw
    ):
        res = evaluate_entries(bars, kept, tp1_ibw=None, high_override=high, low_override=low)
        for name, q in tp1_ibw.items():
            r = evaluate_entries(
                bars, kept.select(
                    [c for c in ("anchor_ts", "entry_ts", "session_end", "entry", "side",
                                 "ib_width", "day") if c in kept.columns]
                ),
                tp1_ibw=q, high_override=high, low_override=low,
            )
            res = res.join(
                r.select("entry_ts", pl.col("outcome").alias(f"outcome_{name}")),
                on="entry_ts", how="left",
            )
    else:
        res = evaluate_entries(bars, kept, tp1_ibw=tp1_ibw, high_override=high, low_override=low)
    return res, {
        "n_input": n, "n_spliced": int(keep.sum()), "n_no_donor": int(n_no_donor),
        "spliced_fraction": float(keep.mean()),
    }


def _bucketed_derangement(buckets: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Index array pairing each row with another of the same length-bucket, no fixed points."""
    n = len(buckets)
    donor = np.full(n, -1, dtype=int)
    for b in np.unique(buckets):
        idx = np.where(buckets == b)[0]
        if len(idx) < 2:
            continue
        for _ in range(200):
            perm = rng.permutation(idx)
            if not np.any(perm == idx):
                donor[idx] = perm
                break
        else:
            donor[idx] = np.roll(idx, 1)
    return donor


def path_swap_bite(swapped_with_donor: pl.DataFrame) -> dict:
    """Pooled positive-control bite test for the outcome-path-swap tripwire.

    A genuine (non-tautological) bite test: correlate each swapped event's
    PRICE-level favourable excursion ``mfe`` against the DONOR's OWN real ``mfe``.
    The swap installs the donor's re-based price path, so ``swapped_mfe`` is the
    donor's raw price excursion over the (possibly truncated) window — if the swap
    reached the outcome bars the reads consume, the two are strongly correlated;
    if it reached nothing, ``swapped_mfe`` would be the TARGET's excursion,
    independent of the donor (design §4.3 / INFR-018 AMENDMENT-6). Price MFE, not
    the IB-width-normalised asym, because the donor and target divisors differ and
    would attenuate an otherwise clean signal. Pooled across all symbols so low-n
    symbols cannot fail a per-symbol split.

    Parameters
    ----------
    swapped_with_donor :
        Pooled swapped events carrying ``mfe`` (swapped, price) and ``donor_mfe``
        (the donor session's real price MFE).

    Returns
    -------
    dict
        ``{corr, n, bite}`` — ``bite`` True when the correlation clears 0.5.
    """
    d = swapped_with_donor.drop_nulls(["mfe", "donor_mfe"])
    if d.height < 30:
        return {"corr": None, "n": int(d.height), "bite": False, "reason": "n<30"}
    corr = float(pl.DataFrame({"a": d["mfe"], "b": d["donor_mfe"]}).select(pl.corr("a", "b")).item())
    return {"corr": corr, "n": int(d.height), "bite": bool(np.isfinite(corr) and corr > 0.5),
            "note": "corr(swapped price MFE, donor real price MFE); >0.5 proves the swap "
                    "installed the donor outcome into the bars the reads consume"}
