"""Signed failed-break / trap events (S3 Δ+) — SPDR-008 shared module.

Source ``SIGNAL-SIGNED.md`` S3: *"A poke ≥ δ beyond a boundary (IB edge, VA edge,
prior extreme) fails A6 within N bars and closes back inside … trapped aggressors'
forced unwind fuels the move back across the range."* The data-tier's new,
falsifiable content is that the trapped inventory is **measured**: trap load is
signed by the aggressor split (``poke_side × Σ delta_ratio_resid`` — the A5 Δ/V
signed-direction residual), positive only when measured flow AGREED with the poke
(a genuine trap) and negative under absorption. The falsifiable claim SPDR-008
screens is that reversal excursion is MONOTONE in that measured load.

Three boundary types, tested **independently** (SPDR-008 design §4.1):

- ``IB``    — the anchored opening-range edge (current session; frozen apparatus).
- ``PVA``   — the prior session's proxy value-area edge (VAH/VAL, K-UNIFORM).
- ``PRIOR`` — the prior session's real extreme (High/Low).

Frozen-apparatus reuse (design §3.1 / QA-1 Issue 2): the ``IB`` boundary reuses
:func:`xen.sigbar.acceptance.find_pokes` / :func:`evaluate_discriminator` /
:func:`label_outcomes` UNMODIFIED; :func:`assert_ib_matches_frozen` proves this
module's level-generalised A6 reproduces the frozen ``evaluate_discriminator`` on
the IB level byte-identically before any PVA/PRIOR read is trusted. ``PVA``/``PRIOR``
use :func:`find_pokes_at_level` + :func:`d4_reject_at_level`. ``acceptance.py`` and
``profile.py`` are never modified.

No per-level Δ (card ban 2): trap load reads the per-BAR ``delta_ratio_resid`` only;
:func:`xen.sigbar.fences.assert_no_per_level_delta` guards the profile path in
``profile.py``. No local accounting primitive — reversal excursion is an
availability magnitude, never a booked P&L.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import polars as pl

from xen.sigbar import acceptance, profile, sessions

#: Frozen A6 = D4-t50-w30 (INFR-018 instrument_registry.json a6_rule); the poke
#: search reuses the frozen post-IB window and δ=0.
A6_TAU = 0.50
A6_W = 30
QUALIFY = acceptance.QUALIFY_MINUTES  # 30
BOUNDARY_TYPES = ("IB", "PVA", "PRIOR")

#: The frozen D4-t50-w30 discriminator, reused unmodified for the IB boundary.
_D4_FROZEN = acceptance.Discriminator("D4-t50-w30", "D4", False, {"tau": A6_TAU, "w": A6_W})


# --------------------------------------------------------------------------- #
# Derangement (L-28: zero fixed points)
# --------------------------------------------------------------------------- #
def derange(n: int, rng: np.random.Generator) -> np.ndarray:
    """A permutation of ``range(n)`` with zero fixed points (L-28).

    Raises for ``n < 2`` — a single element cannot be deranged; the caller drops
    and counts such blocks (design §4.2 singleton/coverage rule).
    """
    if n < 2:
        raise ValueError(f"cannot derange n={n} (need >= 2; caller drops+counts)")
    while True:
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p


# --------------------------------------------------------------------------- #
# Boundary levels (all known <= t-1)
# --------------------------------------------------------------------------- #
def boundary_levels(joined: pl.DataFrame, sess: pl.DataFrame) -> pl.DataFrame:
    """Per ``anchor_ts``: the IB / PVA / PRIOR up+down levels.

    ``IB`` from the current session's ``session_breaks``; ``PVA`` (prior value-area
    edges, K-UNIFORM proxy profile) and ``PRIOR`` (prior real extreme) from the
    PRIOR anchored session — fully closed before the current session opens, so
    every level is available at the current session's open (causal).

    Returns one row per anchor_ts that has a covered prior session, with columns
    ``anchor_ts, prior_anchor, ib_high, ib_low, pva_high, pva_low, prior_high,
    prior_low`` (PVA/PRIOR are null where the prior session is too thin to profile).
    """
    anc = sess.select("anchor_ts", "ib_high", "ib_low", "ib_width").sort("anchor_ts")
    ib_lookup = {r["anchor_ts"]: (r["ib_high"], r["ib_low"], r["ib_width"])
                 for r in anc.iter_rows(named=True)}
    order = list(anc["anchor_ts"])
    rows: list[dict] = []
    prev = None
    for a in order:
        if prev is not None:
            pb = joined.filter(pl.col("anchor_ts") == prev)
            ib_h, ib_l, ib_w = ib_lookup[a]
            row = {
                "anchor_ts": a, "prior_anchor": prev,
                "ib_high": ib_h, "ib_low": ib_l, "ib_width": ib_w,
                "prior_high": float(pb["High"].max()) if pb.height else None,
                "prior_low": float(pb["Low"].min()) if pb.height else None,
                "pva_high": None, "pva_low": None,
            }
            if pb.height >= 30:
                edges, prof = profile.build_profile(pb, "K-UNIFORM")
                _, val, vah = profile.poc_and_value_area(edges, prof)
                row["pva_low"], row["pva_high"] = val, vah
            rows.append(row)
        prev = a
    return pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={"anchor_ts": anc.schema["anchor_ts"], "prior_anchor": anc.schema["anchor_ts"],
                "ib_high": pl.Float64, "ib_low": pl.Float64, "ib_width": pl.Float64,
                "pva_high": pl.Float64, "pva_low": pl.Float64,
                "prior_high": pl.Float64, "prior_low": pl.Float64}
    )


# --------------------------------------------------------------------------- #
# Level-generalised poke + A6 reject (PVA/PRIOR; IB via frozen — asserted equal)
# --------------------------------------------------------------------------- #
def find_pokes_at_level(joined: pl.DataFrame, levels: pl.DataFrame,
                        up_col: str, dn_col: str) -> pl.DataFrame:
    """First poke (δ=0) beyond an arbitrary up/down level, per session.

    Mirrors :func:`xen.sigbar.acceptance.find_pokes` exactly in form (extremum
    touch, first-in-session, ``[anchor+L, session_end)`` search, qualify window
    ``[poke_ts, poke_ts+30)``, drop pokes whose window runs past session end) but
    reads the level from ``levels`` columns instead of ``ib_high``/``ib_low``.

    Returns ``anchor_ts, poke_ts, poke_side, poke_extreme, level_up, level_dn,
    session_end, qualify_end, ib_width`` (ib_width carried for the normaliser).
    ``levels`` must carry ``ib_width`` (the frozen L-21 divisor, same for all types).
    """
    lv = levels.select("anchor_ts", "ib_width", pl.col(up_col).alias("level_up"),
                        pl.col(dn_col).alias("level_dn"))
    sess_end = joined.group_by("anchor_ts").agg(pl.col("session_end").first())
    j = (
        joined.join(lv, on="anchor_ts", how="inner")
        .filter(pl.col("level_up").is_not_null() & pl.col("level_dn").is_not_null()
                & (pl.col("level_up") > pl.col("level_dn")))
        .filter(pl.col("mins_since") >= pl.col("ib_minutes"))
        .with_columns(
            pl.when(pl.col("High") > pl.col("level_up")).then(pl.lit(1))
            .when(pl.col("Low") < pl.col("level_dn")).then(pl.lit(-1))
            .otherwise(pl.lit(0)).alias("poke_side")
        )
        .filter(pl.col("poke_side") != 0)
    )
    first = (
        j.sort("OpenTime").group_by("anchor_ts").agg(
            pl.col("OpenTime").first().alias("poke_ts"),
            pl.col("poke_side").first().alias("poke_side"),
            pl.when(pl.col("poke_side").first() == 1).then(pl.col("High").first())
            .otherwise(pl.col("Low").first()).alias("poke_first_extreme"),
            pl.col("level_up").first().alias("level_up"),
            pl.col("level_dn").first().alias("level_dn"),
            pl.col("ib_width").first().alias("ib_width"),
        )
        .join(sess_end, on="anchor_ts", how="left")
        .with_columns((pl.col("poke_ts") + pl.duration(minutes=QUALIFY)).alias("qualify_end"))
        .filter(pl.col("qualify_end") < pl.col("session_end"))
    )
    return first


def d4_reject_at_level(joined: pl.DataFrame, pokes: pl.DataFrame) -> pl.DataFrame:
    """D4-t50-w30 acceptance at an arbitrary level → ``says_accept`` per poke.

    Re-implements the frozen ``evaluate_discriminator(D4-t50-w30)`` close-count
    form (fraction of closes beyond the poked level within ``[poke_ts, poke_ts+w)``
    ``>= tau``) against ``level_up``/``level_dn`` instead of the IB edge.
    :func:`assert_ib_matches_frozen` proves this reproduces the frozen function on
    the IB level.
    """
    pk = pokes.select("anchor_ts", "poke_ts", "poke_side", "level_up", "level_dn")
    collide = [c for c in pk.columns if c != "anchor_ts" and c in joined.columns]
    base = joined.drop(collide) if collide else joined
    q = (
        base.join(pk, on="anchor_ts", how="inner")
        .filter((pl.col("OpenTime") >= pl.col("poke_ts"))
                & (pl.col("OpenTime") < pl.col("poke_ts") + pl.duration(minutes=A6_W)))
        .with_columns(
            pl.when(pl.col("poke_side") == 1).then(pl.col("Close") > pl.col("level_up"))
            .otherwise(pl.col("Close") < pl.col("level_dn")).alias("close_beyond")
        )
        .group_by("anchor_ts").agg(pl.col("close_beyond").mean().alias("frac"))
        .with_columns((pl.col("frac") >= A6_TAU).alias("says_accept"))
    )
    return q.select("anchor_ts", "says_accept", "frac")


def assert_ib_matches_frozen(joined: pl.DataFrame, sess: pl.DataFrame) -> None:
    """Prove the level-generalised A6 reproduces the frozen path on the IB level.

    Runs the frozen ``find_pokes`` + ``evaluate_discriminator(D4-t50-w30)`` and this
    module's ``find_pokes_at_level`` + ``d4_reject_at_level`` on ``ib_high``/``ib_low``,
    and raises unless the ``says_accept`` calls agree on every shared poke (design
    §3.1). A mismatch means the PVA/PRIOR generalisation diverged from the frozen
    rule and every downstream read is unattributable.
    """
    frozen_pokes = acceptance.find_pokes(joined, sess, 0.0)
    if frozen_pokes.height == 0:
        return
    frozen = acceptance.evaluate_discriminator(joined, frozen_pokes, _D4_FROZEN)
    lv = sess.select("anchor_ts", "ib_high", "ib_low", "ib_width")
    gen_pokes = find_pokes_at_level(joined, lv, "ib_high", "ib_low")
    gen = d4_reject_at_level(joined, gen_pokes).select("anchor_ts", "says_accept")
    m = (
        frozen.rename({"says_accept": "frozen_accept"})
        .join(gen.rename({"says_accept": "gen_accept"}), on="anchor_ts", how="inner")
    )
    # The frozen find_pokes and the generalised one select the same first poke per
    # session (same extremum-touch rule), so the shared set is the full frozen set.
    if m.height != frozen.height:
        raise RuntimeError(
            f"IB regression: generalised pokes cover {m.height}/{frozen.height} frozen sessions"
        )
    bad = m.filter(pl.col("frozen_accept") != pl.col("gen_accept")).height
    if bad:
        raise RuntimeError(
            f"IB regression: {bad} A6 calls differ between frozen and generalised D4-t50-w30"
        )


# --------------------------------------------------------------------------- #
# Confirmed traps + reversal excursion + measured-flow trap load
# --------------------------------------------------------------------------- #
def find_traps(joined: pl.DataFrame, pokes: pl.DataFrame, rejects: pl.DataFrame) -> pl.DataFrame:
    """Confirmed traps: A6-REJECTED pokes that reclaim, with reversal + trap load.

    Parameters
    ----------
    joined :
        Bars for one symbol with ``anchor_ts, mins_since, session_end`` attached
        AND ``delta_ratio_resid`` (the signed A5 residual; null-safe).
    pokes :
        Output of :func:`find_pokes_at_level` (or, for IB, the frozen ``find_pokes``
        with ``level_up/level_dn`` set to ib_high/ib_low).
    rejects :
        ``anchor_ts, says_accept`` — the A6 call. Only ``says_accept == False`` are traps.

    Returns one row per confirmed trap with the design §3.2 quantities.
    """
    reject_set = set(rejects.filter(~pl.col("says_accept"))["anchor_ts"].to_list())
    out: list[dict] = []
    for r in pokes.iter_rows(named=True):
        if r["anchor_ts"] not in reject_set:
            continue
        side = r["poke_side"]
        level = r["level_up"] if side == 1 else r["level_dn"]
        opp = r["level_dn"] if side == 1 else r["level_up"]
        poke_ts, qend, send = r["poke_ts"], r["qualify_end"], r["session_end"]
        win = joined.filter((pl.col("anchor_ts") == r["anchor_ts"])
                            & (pl.col("OpenTime") >= poke_ts) & (pl.col("OpenTime") < qend)).sort("OpenTime")
        if win.height == 0:
            continue
        # reclaim: first bar closing back on the inside of the poked level
        inside = (win["Close"] <= level) if side == 1 else (win["Close"] >= level)
        recl = win.filter(inside)
        if recl.height == 0:
            continue  # no reclaim → not a trap
        reclaim_ts = recl["OpenTime"][0]
        poke_bars = win.filter(pl.col("OpenTime") <= reclaim_ts)
        poke_extreme = (float(poke_bars["High"].max()) if side == 1
                        else float(poke_bars["Low"].min()))
        # trap load — SIGNED BY MEASURED FLOW (poke_side × Σ delta_ratio_resid)
        rr = poke_bars["delta_ratio_resid"]
        trap_load = None if rr.null_count() == rr.len() else side * float(rr.fill_null(0.0).sum())
        # entry at the bar after the reclaim close
        entry_bar = joined.filter((pl.col("anchor_ts") == r["anchor_ts"])
                                  & (pl.col("OpenTime") == reclaim_ts + timedelta(minutes=1)))
        if entry_bar.height == 0:
            continue
        entry = float(entry_bar["Open"][0])
        ibw = r["ib_width"]
        if not (ibw > 0) or not (entry > 0):
            continue  # degenerate session — no valid normaliser
        rev_side = -side
        out_bars = joined.filter((pl.col("anchor_ts") == r["anchor_ts"])
                                 & (pl.col("OpenTime") > reclaim_ts) & (pl.col("OpenTime") < send)).sort("OpenTime")
        if out_bars.height == 0:
            continue
        hi_p, lo_p = float(out_bars["High"].max()), float(out_bars["Low"].min())
        if rev_side == 1:
            mfe, mae = hi_p - entry, entry - lo_p
        else:
            mfe, mae = entry - lo_p, hi_p - entry
        ibw = r["ib_width"]
        race = _race_outcome(out_bars, rev_side, opp, poke_extreme)
        entry_ts = reclaim_ts + timedelta(minutes=1)
        out.append({
            "anchor_ts": r["anchor_ts"], "poke_ts": poke_ts, "reclaim_ts": reclaim_ts,
            "entry_ts": entry_ts, "session_end": send,
            "poke_side": side, "rev_side": rev_side, "side": rev_side,  # side == rev_side for reuse
            "level": level, "opposite_edge": opp, "poke_extreme": poke_extreme, "entry": entry,
            "ib_width": ibw, "mfe_rev_norm": mfe / ibw, "mae_rev_norm": mae / ibw,
            "mfe_rev_bps": 1e4 * mfe / entry, "trap_load": trap_load,
            "race": race, "n_post": out_bars.height,
        })
    return pl.DataFrame(out) if out else _empty_traps()


def _race_outcome(out_bars: pl.DataFrame, rev_side: int, opp: float, poke_extreme: float) -> str:
    """Opposite-edge-before-poke-extreme, pessimistic same-bar → STOP (design §3.2)."""
    hi = out_bars["High"].to_numpy()
    lo = out_bars["Low"].to_numpy()
    for i in range(len(hi)):
        if rev_side == 1:  # long: TP = opp above? no — opp is the far edge; long targets up
            hit_tp = hi[i] >= opp
            hit_stop = lo[i] <= poke_extreme
        else:  # short: TP = opp below; stop = poke_extreme above
            hit_tp = lo[i] <= opp
            hit_stop = hi[i] >= poke_extreme
        if hit_tp and hit_stop:
            return "STOP"  # pessimistic same-bar
        if hit_stop:
            return "STOP"
        if hit_tp:
            return "TP"
    return "TIMEOUT"


def _empty_traps() -> pl.DataFrame:
    return pl.DataFrame(schema={
        "anchor_ts": pl.Datetime, "poke_ts": pl.Datetime, "reclaim_ts": pl.Datetime,
        "entry_ts": pl.Datetime, "session_end": pl.Datetime,
        "poke_side": pl.Int64, "rev_side": pl.Int64, "side": pl.Int64,
        "level": pl.Float64, "opposite_edge": pl.Float64,
        "poke_extreme": pl.Float64, "entry": pl.Float64, "ib_width": pl.Float64,
        "mfe_rev_norm": pl.Float64, "mae_rev_norm": pl.Float64, "mfe_rev_bps": pl.Float64,
        "trap_load": pl.Float64, "race": pl.Utf8, "n_post": pl.Int64,
    })


# --------------------------------------------------------------------------- #
# Per-boundary trap-load tercile cuts (DESIGN-frozen, applied to CONFIRM)
# --------------------------------------------------------------------------- #
def tercile_cuts(trap_loads: np.ndarray) -> tuple[float, float]:
    """The 33rd/67th percentile cut points of trap_load (LOW/MID/HIGH)."""
    v = trap_loads[~np.isnan(trap_loads)]
    if v.size < 3:
        return float("nan"), float("nan")
    return float(np.percentile(v, 100 / 3)), float(np.percentile(v, 200 / 3))


def assign_tier(trap_load: float, lo_cut: float, hi_cut: float) -> str:
    if trap_load is None or np.isnan(trap_load) or np.isnan(lo_cut):
        return "NA"
    if trap_load <= lo_cut:
        return "LOW"
    if trap_load >= hi_cut:
        return "HIGH"
    return "MID"
