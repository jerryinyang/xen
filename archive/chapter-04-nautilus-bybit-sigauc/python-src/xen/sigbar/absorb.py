"""Signed absorption events (S9) — SPDR-009 shared module.

Source ``SIGNAL-SIGNED.md`` S9: heavy effort + no result at a structural level,
with measured aggression pointing INTO the level. The screen's primary estimand
is the marginal contrast ``S9 − BASE`` (signed signature over the identical
unsigned climax-hold class).

Object construction imports — never reimplements — the INFR-020 shared
helpers::

    absorb_candidate_predicate
    structural_levels_1m
    assign_candidate_sessions
    available_levels_for_candidates

Integrity (HARD, raise not warn)
--------------------------------
* every frozen INFR-017/018/020 input re-hashed at entry
* DESIGN / CONFIRM only (TEST and holdout unreachable)
* COMPLETE-window candidates only
* levels and outcomes on **1-minute** bars (D6.3)
* causal entry at the NEXT LTF bar open; IB edges only after IB wall-clock
* no per-level Δ; no S1 gate as event qualifier; no A-H1/A-H4 edge-bearing use
* no local accounting primitive

This module is the computation core. The SPDR-009 runner
(``screen_code/absorb_screen.py``) freezes τ / pool cuts, emits report layers,
and must not book P&L.
"""

from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable, Literal

import numpy as np
import polars as pl

from xen.sigbar.baselines import residualise
from xen.sigbar.fences import (
    BASELINES_PARQUET,
    COLUMN_PINS_JSON,
    assert_band,
    assert_frozen_inputs,
    assert_levels_from_1m,
    assert_no_per_level_delta,
    load_bars,
    repo_root,
    sha256_file,
)
from xen.sigbar.ltf import (
    WINDOW_COMPLETE,
    absorb_candidate_predicate,
    aggregate_signed,
    assign_candidate_sessions,
    available_levels_for_candidates,
    design_gap_days,
    prior_htf_session_ranges,
    structural_levels_1m,
)
from xen.sigbar.sessions import (
    CANDIDATE_ANCHORS,
    anchor_table,
    ib_minutes_for_ltf,
    operational_anchor,
)
from xen.sigbar.trap import derange as derange_perm

# --------------------------------------------------------------------------- #
# Frozen pins (AMENDMENT-22 / design §0)
# --------------------------------------------------------------------------- #

REGISTRY_REL = "python/experiments/INFR-018/results/instrument_registry.json"
REGISTRY_PIN_SHA256 = "5c3869845bd514bfa92d236fa4640faa1870fee3facf31efa97bbfe996762485"
KERNEL = "K-UNIFORM"

INFR020_RESULTS = "python/experiments/INFR-020/results"
INFR020_PINS_SHA256 = (
    "5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5"
)
INFR020_ARTIFACT_SHA256: dict[str, str] = {
    "seasonal_baselines_mtf.parquet": (
        "86c81937cbee23f76a62bd4051394f59da3deb2230e7dd958fc573cee38a12c1"
    ),
    "class_thresholds_1m.json": (
        "dee853ad96f11754f410aa8c0a7632b0a782029dee0b770b500a74a9f959e9fc"
    ),
    "class_thresholds_mtf.json": (
        "745fb435eeb9e70fec88d55a32e6dfce38b4c02619824f9cff4d51ca3dcb3ae7"
    ),
    "sessions_mtf.json": (
        "c55cd8806bba048f90e48795fdcab021738d9984a1602ca14f164a0f05b262df"
    ),
    "zone_scale_census.json": (
        "f64e0d22355f8c5f3c5acafff598ae43fa0e84cfac9acc6f9e88fbd458487f1e"
    ),
    "zone_scale_census_d1_ibwidth.json": (
        "76c3d4b58c00361d081de9225e226db2fe2aa86a56f17c18ec23e0e046705f0c"
    ),
    "coverage_report.json": (
        "68dac757a4c96f0989da902805e11265e8108f7555f3d02df6a66f2dafc3a424"
    ),
}

#: Primary holds in LTF bars (design §1 / §3.4).
HOLDS_LTF: tuple[int, ...] = (5, 10)
#: Within-(symbol, pair) refractory = max primary hold.
REFRACTORY_LTF = 10
#: Matched-random donor battery (L-19 floor 25; design uses 30).
N_MATCHED_RANDOM = 30
#: T2 derangement seed battery.
N_DERANGE_SEEDS = 2000
#: Day-block length for clustered bootstrap (covers D4 H=10 = 10 h).
DAY_BLOCK = 5

ZoneMode = Literal["prior_session_range", "ib_width"]
PoolMode = Literal["P", "P_WIDE", "MID_RANGE"]

FIT_METRICS = ("volume", "range", "delta_abs", "delta_ratio")

# Pair → framing. Levels always from 1m; LTF only for detection residuals.
PAIR_SPECS: dict[str, dict[str, Any]] = {
    "D1": {
        "pair_id": "D1",
        "label": "1d/1m",
        "anchor": "A-USOPEN",
        "ltf_minutes": 1,
        "ib_wall_minutes": 15,
        "edge_bearing_anchor": True,  # A-USOPEN is the frozen raced anchor
    },
    "D2": {
        "pair_id": "D2",
        "label": "1h/5m",
        "anchor": "A-H1",
        "ltf_minutes": 5,
        "ib_wall_minutes": 15,
        "edge_bearing_anchor": False,
    },
    "D3": {
        "pair_id": "D3",
        "label": "4h/15m",
        "anchor": "A-H4",
        "ltf_minutes": 15,
        "ib_wall_minutes": 15,
        "edge_bearing_anchor": False,
    },
    "D4": {
        "pair_id": "D4",
        "label": "1d/1h",
        "anchor": "A-USOPEN",
        "ltf_minutes": 60,
        "ib_wall_minutes": 60,  # D4 DEVIATES — disclosed
        "edge_bearing_anchor": True,
    },
}


@dataclass(frozen=True)
class Spdr009FrozenInputs:
    """Verified pins for every SPDR-009 entry point."""

    baselines_1m_sha256: str
    column_pins_sha256: str
    fence_manifest_sha256: str
    registry_pin_sha256: str
    infr020_pins_sha256: str
    infr020_artifacts: dict[str, str]


def _path(root: Path, rel: str) -> Path:
    return root / rel


def assert_spdr009_frozen_inputs(root: Path | None = None) -> Spdr009FrozenInputs:
    """Re-hash every frozen INFR-017/018/020 input; raise on any mismatch.

    Called at every SPDR-009 entry point (design §0 / §7). Extends
    :func:`assert_frozen_inputs` (INFR-017) with the INFR-018 registry pin and
    the full INFR-020 artifact set (AMENDMENT-22).
    """
    root = root or repo_root()
    base = assert_frozen_inputs(root)

    reg_path = _path(root, REGISTRY_REL)
    if not reg_path.exists():
        raise RuntimeError(f"INFR-018 registry missing at {reg_path}")
    reg = json.loads(reg_path.read_text())
    reg_pin = reg.get("pin_sha256")
    if reg_pin != REGISTRY_PIN_SHA256:
        raise RuntimeError(
            f"FROZEN INPUT MISMATCH: registry pin_sha256 {reg_pin} "
            f"!= contracted {REGISTRY_PIN_SHA256}"
        )
    kernel = reg.get("kernel") or reg.get("profile_kernel") or KERNEL
    # Registry may nest kernel under profile settings; only raise if present and wrong.
    if isinstance(reg.get("profile"), dict):
        k = reg["profile"].get("kernel")
        if k is not None and k != KERNEL:
            raise RuntimeError(f"FROZEN INPUT MISMATCH: kernel {k} != {KERNEL}")
    del kernel

    pins_path = _path(root, f"{INFR020_RESULTS}/pins.json")
    if not pins_path.exists():
        raise RuntimeError(f"INFR-020 pins.json missing at {pins_path}")
    pins_sha = sha256_file(pins_path)
    if pins_sha != INFR020_PINS_SHA256:
        raise RuntimeError(
            f"FROZEN INPUT MISMATCH: INFR-020 pins.json {pins_sha} "
            f"!= contracted {INFR020_PINS_SHA256}"
        )
    pins_obj = json.loads(pins_path.read_text())
    art = pins_obj.get("artifacts") or {}
    verified: dict[str, str] = {}
    for name, expect in INFR020_ARTIFACT_SHA256.items():
        p = _path(root, f"{INFR020_RESULTS}/{name}")
        if not p.exists():
            raise RuntimeError(f"INFR-020 artifact missing: {p}")
        got = sha256_file(p)
        if got != expect:
            raise RuntimeError(
                f"FROZEN INPUT MISMATCH: {name} sha256 {got} != contracted {expect}"
            )
        # pins.json must also agree (defense in depth)
        pin_expect = art.get(name)
        if pin_expect is not None and pin_expect != expect:
            raise RuntimeError(
                f"INFR-020 pins.json disagrees with contracted {name}: "
                f"{pin_expect} vs {expect}"
            )
        verified[name] = got

    return Spdr009FrozenInputs(
        baselines_1m_sha256=base.baselines_sha256,
        column_pins_sha256=base.column_pins_sha256,
        fence_manifest_sha256=base.fence_manifest_sha256,
        registry_pin_sha256=reg_pin,
        infr020_pins_sha256=pins_sha,
        infr020_artifacts=verified,
    )


def assert_confirm_freeze_ready(results_dir: Path) -> None:
    """Refuse CONFIRM paths until pool_cuts + INFR-020 pin hashes exist (design §7)."""
    cuts = results_dir / "pool_cuts.json"
    if not cuts.exists():
        raise RuntimeError(
            "CONFIRM-before-freeze refusal: results/pool_cuts.json missing "
            "(design §7 HARD)"
        )
    obj = json.loads(cuts.read_text())
    if not obj.get("tau_by_pair"):
        raise RuntimeError("CONFIRM-before-freeze refusal: pool_cuts lacks tau_by_pair")
    # Re-verify INFR-020 pins are still the contracted set.
    assert_spdr009_frozen_inputs()


def assert_not_edge_bearing_operational(anchor_id: str, *, as_edge: bool) -> None:
    """A-H1/A-H4 may not be consumed as edge-bearing (design §7 HARD)."""
    if as_edge and anchor_id in ("A-H1", "A-H4"):
        raise RuntimeError(
            f"A-H NON-EDGE: refusing to treat operational anchor {anchor_id} "
            "as edge-bearing (INFR-020 / design §7)"
        )


def refuse_s1_as_qualifier() -> None:
    """Any code path that would use S1 acceptance as an event qualifier raises.

    The binding refusal is this raise; callers that would consult
    ``acceptance.evaluate_discriminator`` for event qualification must call this
    first (design §7 / Addendum §2.7).
    """
    raise RuntimeError(
        "S1-GATE REFUSAL: acceptance.evaluate_discriminator may not qualify "
        "absorption events (Addendum §2.7 / design §7)"
    )


def assert_no_ltf_outcome_path(source_bar_minutes: int, *, context: str = "") -> None:
    """D6.3: outcome and level paths must consume 1-minute bars only."""
    if source_bar_minutes != 1:
        raise RuntimeError(
            f"D6.3 OUTCOME PATH: {context or 'path'} used bar_minutes="
            f"{source_bar_minutes}; 1-minute bars required"
        )


# --------------------------------------------------------------------------- #
# Pair / session helpers
# --------------------------------------------------------------------------- #


def _anchor_spec(anchor_id: str):
    if anchor_id == "A-USOPEN":
        return next(a for a in CANDIDATE_ANCHORS if a.anchor_id == "A-USOPEN")
    return operational_anchor(anchor_id)


def ib_minutes_for_pair(pair_id: str) -> int:
    """IB wall-clock minutes for a pair (D4 = 60; others max(15, ltf))."""
    spec = PAIR_SPECS[pair_id]
    ltf = int(spec["ltf_minutes"])
    wall = int(spec["ib_wall_minutes"])
    if pair_id == "D4":
        return 60
    if pair_id == "D1":
        return 15
    return ib_minutes_for_ltf(ltf, wall_clock_minutes=wall)


def load_thresholds(
    pair_id: str,
    symbol: str,
    *,
    root: Path | None = None,
) -> dict[str, dict[str, float]]:
    """Per-(symbol, timeframe) class cuts from the frozen INFR-020 pins.

    D1 → ``class_thresholds_1m.json`` (all 194). D2–D4 → ``class_thresholds_mtf.json``.
    """
    root = root or repo_root()
    ltf = int(PAIR_SPECS[pair_id]["ltf_minutes"])
    if ltf == 1:
        path = _path(root, f"{INFR020_RESULTS}/class_thresholds_1m.json")
        obj = json.loads(path.read_text())
        block = (obj.get("per_symbol") or {}).get(symbol)
    else:
        path = _path(root, f"{INFR020_RESULTS}/class_thresholds_mtf.json")
        obj = json.loads(path.read_text())
        block = (obj.get("per_symbol_tf") or {}).get(symbol, {}).get(f"{ltf}m")
    if not block:
        raise RuntimeError(f"no threshold block for {symbol} pair {pair_id}")
    return block


def bar_metrics(bars: pl.DataFrame) -> pl.DataFrame:
    """Raw effort/result metrics required by the A5 residual path."""
    return bars.with_columns(
        pl.col("Volume").alias("volume"),
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Delta").abs().alias("delta_abs"),
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("Delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )


def residualise_pair(
    bars: pl.DataFrame,
    symbol: str,
    pair_id: str,
    *,
    root: Path | None = None,
) -> pl.DataFrame:
    """Attach volume/range/|Δ|/(Δ/V) residuals for one pair's LTF series."""
    root = root or repo_root()
    ltf = int(PAIR_SPECS[pair_id]["ltf_minutes"])
    out = bar_metrics(bars)
    if ltf == 1:
        bl = (
            pl.scan_parquet(_path(root, BASELINES_PARQUET))
            .filter(pl.col("symbol") == symbol)
            .collect()
        )
    else:
        bl = (
            pl.scan_parquet(
                _path(root, f"{INFR020_RESULTS}/seasonal_baselines_mtf.parquet")
            )
            .filter((pl.col("symbol") == symbol) & (pl.col("bar_minutes") == ltf))
            .collect()
        )
    if bl.height == 0:
        raise RuntimeError(f"no baseline for {symbol} pair {pair_id} (ltf={ltf}m)")
    for m in FIT_METRICS:
        out = residualise(out, bl, m, time_col="OpenTime", bar_minutes=ltf)
    return out


def ltf_complete_bars(
    bars_1m: pl.DataFrame,
    pair_id: str,
) -> pl.DataFrame:
    """COMPLETE-window LTF series for detection; 1m is stamped COMPLETE."""
    ltf = int(PAIR_SPECS[pair_id]["ltf_minutes"])
    if ltf == 1:
        return bars_1m.with_columns(
            pl.lit(WINDOW_COMPLETE).alias("window_class"),
            pl.lit(1.0).alias("traded_fraction"),
            pl.lit(1).alias("SourceBars"),
        )
    gaps = design_gap_days(bars_1m)
    return aggregate_signed(bars_1m, ltf, gap_days=gaps, complete_only=True)


# --------------------------------------------------------------------------- #
# Pool + arms
# --------------------------------------------------------------------------- #


def _into_side(close: float, level: float, prev_close: float | None) -> int:
    """Direction from price TO the level; tie → prior close; still 0 → drop."""
    if close < level:
        return 1
    if close > level:
        return -1
    if prev_close is None:
        return 0
    if prev_close < level:
        return 1
    if prev_close > level:
        return -1
    return 0


def _arm_label(
    delta_abs_resid: float,
    signed_score: float,
    d_hi: float,
    dr_hi: float,
) -> str:
    """Three-way arm assignment (design §3.3). Disjoint + exhaustive in pool P."""
    if delta_abs_resid >= d_hi and signed_score >= dr_hi:
        return "S9"
    if delta_abs_resid >= d_hi and signed_score <= -dr_hi:
        return "MIRROR"
    return "BASE"


def _zone_scale_value(
    row: dict,
    *,
    zone_mode: ZoneMode,
) -> float | None:
    if zone_mode == "ib_width":
        w = row.get("ib_width")
        return float(w) if w is not None and w > 0 else None
    pr = row.get("prior_session_range")
    return float(pr) if pr is not None and pr > 0 else None


def build_contact_events(
    symbol: str,
    band: str,
    pair_id: str,
    *,
    tau: float,
    zone_mode: ZoneMode = "prior_session_range",
    pool_mode: PoolMode = "P",
    range_resid_cut_key: str = "low",
    range_resid_p25: float | None = None,
    bars_1m: pl.DataFrame | None = None,
    root: Path | None = None,
    nearest_only: bool = True,
) -> pl.DataFrame:
    """Locate climax-hold-at-level events for one (symbol, pair, band).

    Parameters
    ----------
    tau :
        Contact tolerance multiplier on the zone scale (count-frozen by the
        runner before any outcome read).
    zone_mode :
        ``prior_session_range`` (D6 primary) or ``ib_width`` (D1 sensitivity /
        golden-trace continuity).
    pool_mode :
        ``P`` uses p10 range residual; ``P_WIDE`` uses p25 if present in the
        threshold block under ``range.p25`` / caller-supplied override via
        ``range_resid_cut_key``; ``MID_RANGE`` keeps climax-hold bars with NO
        level within ``1.0 × prior_session_range``.
    nearest_only :
        If True, keep one event per LTF bar (nearest available level) for the
        pooled read (design §3.2).

    Returns
    -------
    Event frame (no outcomes). Columns include arm label, signed_score, side,
    entry_ts, and level provenance. Empty if nothing qualifies.
    """
    root = root or repo_root()
    if pair_id not in PAIR_SPECS:
        raise KeyError(f"unknown pair {pair_id}")
    if band not in ("DESIGN", "CONFIRM"):
        raise RuntimeError(f"band {band!r} unreachable (DESIGN/CONFIRM only)")

    spec = PAIR_SPECS[pair_id]
    # D2/D3 anchors are operational-only; never mark them edge-bearing here.
    assert_not_edge_bearing_operational(spec["anchor"], as_edge=False)

    # The runner builds three pools from the same immutable source frame. Let it
    # pass that frame through so a symbol's parquet is not reloaded for every
    # pool; the event construction itself is unchanged.
    bars_1m = bars_1m if bars_1m is not None else load_bars(symbol, band, root=root)
    if bars_1m.height == 0:
        return _empty_events()
    assert_band(bars_1m, band)
    assert_no_ltf_outcome_path(1, context=f"levels:{symbol}/{pair_id}")

    ltf = int(spec["ltf_minutes"])
    ib_mins = ib_minutes_for_pair(pair_id)
    a_spec = _anchor_spec(spec["anchor"])
    lo, hi = bars_1m["OpenTime"].min(), bars_1m["OpenTime"].max()
    anchors = anchor_table(a_spec, lo, hi)

    complete = ltf_complete_bars(bars_1m, pair_id)
    if complete.height == 0:
        return _empty_events()
    if "window_class" in complete.columns:
        bad = complete.filter(pl.col("window_class") != WINDOW_COMPLETE)
        if bad.height:
            raise RuntimeError(
                f"COMPLETE-window fence: {bad.height} non-COMPLETE rows in "
                f"{symbol}/{pair_id} candidate series"
            )

    mdf = residualise_pair(complete, symbol, pair_id, root=root)
    th = load_thresholds(pair_id, symbol, root=root)
    # P_WIDE: no-result leg at per-(symbol,tf) p25 range residual + tighter τ
    # (design §3.2). p25 is not in the frozen p10 class pin — derive it from
    # the residual series on this band (count-only; no outcomes) or accept an
    # explicit override from pool_cuts via range_resid_p25.
    th_use: dict[str, Any] = {
        k: (dict(v) if isinstance(v, dict) else v) for k, v in th.items()
    }
    if pool_mode == "P_WIDE":
        r = dict(th_use.get("range") or {})
        p25 = range_resid_p25 if range_resid_p25 is not None else r.get("p25")
        if p25 is None and "range_resid" in mdf.columns:
            # count-only derivation on this band's COMPLETE residuals
            vals = mdf["range_resid"].drop_nulls()
            if vals.len() >= 20:
                p25 = float(vals.quantile(0.25))
        if p25 is None and range_resid_cut_key != "low" and range_resid_cut_key in r:
            p25 = r[range_resid_cut_key]
        if p25 is None:
            raise RuntimeError(
                f"P_WIDE requires a p25 range residual cut for {symbol}/{pair_id}; "
                "could not derive from residual series"
            )
        r["low"] = float(p25)
        r["p25"] = float(p25)
        r["wide_cut_source"] = "p25_range_resid"
        th_use["range"] = r

    cands = absorb_candidate_predicate(mdf, th_use, require_complete=True)
    if cands.height == 0:
        return _empty_events()

    # prev close for into_side tie-break (prior LTF bar)
    mdf_prev = mdf.select(
        "OpenTime",
        pl.col("Close").shift(1).alias("prev_close"),
        "delta_abs_resid",
        "delta_ratio_resid",
        "volume_resid",
        "range_resid",
        "Open",
        "High",
        "Low",
        "Close",
    )
    cands = cands.join(
        mdf_prev.select("OpenTime", "prev_close"),
        on="OpenTime",
        how="left",
    )

    cand_sess = assign_candidate_sessions(cands, anchors, ltf_minutes=ltf)
    if cand_sess.height == 0:
        return _empty_events()

    only = set(cand_sess["anchor_ts"].unique().to_list())
    levels = structural_levels_1m(
        bars_1m, anchors, ib_mins, only_anchors=only, include_profile=True
    )
    assert_levels_from_1m(
        levels if levels.height else None,
        source_bars=bars_1m,
        context=f"absorb:{symbol}/{pair_id}",
    )
    # Card ban 2 — refuse if a signed weight ever reaches the profile path here.
    assert_no_per_level_delta(pl.Series("Volume", [0.0]))

    ranges = prior_htf_session_ranges(bars_1m, anchors)
    range_map: dict[Any, float] = {}
    if ranges.height:
        for row in ranges.iter_rows(named=True):
            if row["prior_session_range"] is not None:
                range_map[row["anchor_ts"]] = float(row["prior_session_range"])

    pairs_lv = available_levels_for_candidates(cand_sess, levels)
    if pairs_lv.height == 0 and pool_mode != "MID_RANGE":
        return _empty_events()

    d_hi = float(th["delta_abs"]["high"])
    dr_hi = float(th["delta_ratio"]["abs_high"])

    if "session_end" not in cand_sess.columns:
        cand_sess = cand_sess.join(
            anchors.select("anchor_ts", "session_end"), on="anchor_ts", how="left"
        )

    # Residual / OHLC lookup keyed by OpenTime (single source for contact rows).
    feat = mdf_prev.join(
        cand_sess.select("OpenTime", "anchor_ts", "mins_since_close", "session_end"),
        on="OpenTime",
        how="inner",
    )
    feat_by_ts = {r["OpenTime"]: r for r in feat.iter_rows(named=True)}

    ib_map: dict[Any, float] = {}
    if levels.height and "ib_width" in levels.columns:
        for row in levels.select("anchor_ts", "ib_width").unique().iter_rows(named=True):
            if row["ib_width"] is not None and float(row["ib_width"]) > 0:
                ib_map[row["anchor_ts"]] = float(row["ib_width"])

    rows: list[dict] = []
    if pool_mode == "MID_RANGE":
        # Climax-hold bars with no available level within 1.0 × prior range.
        min_dist: dict[Any, float] = {}
        if pairs_lv.height:
            avail0 = pairs_lv.filter(pl.col("level_available"))
            if avail0.height:
                for r in (
                    avail0.group_by("OpenTime")
                    .agg(pl.col("level_distance").min().alias("d"))
                    .iter_rows(named=True)
                ):
                    min_dist[r["OpenTime"]] = float(r["d"])
        for e in feat.iter_rows(named=True):
            pr = range_map.get(e["anchor_ts"])
            if pr is None or pr <= 0:
                continue
            md = min_dist.get(e["OpenTime"])
            if md is not None and md <= 1.0 * pr:
                continue
            da = e.get("delta_abs_resid")
            dr = e.get("delta_ratio_resid")
            if da is None or dr is None:
                continue
            # No structural level → no into_side projection. Continuous score is
            # the raw Δ/V residual so both S9 (+dr_hi) and MIRROR (−dr_hi) can
            # fire (QA-6 I-1). Side fades measured aggression for the path read.
            signed = float(dr)
            arm = _arm_label(float(da), signed, d_hi, dr_hi)
            into = 1 if signed >= 0 else -1  # disclosure only; not a level direction
            side = -into  # fade the measured aggression
            entry_ts = e["OpenTime"] + timedelta(minutes=ltf)
            rows.append(
                {
                    "symbol": symbol,
                    "pair_id": pair_id,
                    "band": band,
                    "pool": pool_mode,
                    "event_ts": e["OpenTime"],
                    "entry_ts": entry_ts,
                    "anchor_ts": e["anchor_ts"],
                    "session_end": e.get("session_end"),
                    "level_kind": "MID_RANGE",
                    "level_price": None,
                    "level_distance": md,
                    "zone_scale": pr,
                    "tau": tau,
                    "zone_mode": zone_mode,
                    "into_side": into,
                    "side": side,
                    "volume_resid": e.get("volume_resid"),
                    "range_resid": e.get("range_resid"),
                    "delta_abs_resid": float(da),
                    "delta_ratio_resid": float(dr),
                    "signed_score": signed,
                    "arm": arm,
                    "ltf_minutes": ltf,
                    "mins_since_close": e.get("mins_since_close"),
                }
            )
    else:
        avail = pairs_lv.filter(pl.col("level_available"))
        if avail.height == 0:
            return _empty_events()
        for e in avail.iter_rows(named=True):
            feat_row = feat_by_ts.get(e["OpenTime"])
            if feat_row is None:
                continue
            if zone_mode == "ib_width":
                scale = ib_map.get(e["anchor_ts"])
            else:
                scale = range_map.get(e["anchor_ts"])
            if scale is None or scale <= 0:
                continue
            dist = float(e["level_distance"])
            if dist > tau * float(scale):
                continue
            if str(e["level_kind"]).startswith("IB_") and e.get("mins_since_close") is not None:
                if int(e["mins_since_close"]) < ib_mins:
                    raise RuntimeError(
                        f"IB-EDGE BEFORE COMPLETE: {symbol} {e['OpenTime']} "
                        f"mins_since_close={e['mins_since_close']} < ib={ib_mins}"
                    )
            into = _into_side(
                float(e["Close"]),
                float(e["level_price"]),
                feat_row.get("prev_close"),
            )
            if into == 0:
                continue
            da = feat_row.get("delta_abs_resid")
            dr = feat_row.get("delta_ratio_resid")
            if da is None or dr is None:
                continue
            signed = into * float(dr)
            arm = _arm_label(float(da), signed, d_hi, dr_hi)
            entry_ts = e["OpenTime"] + timedelta(minutes=ltf)
            rows.append(
                {
                    "symbol": symbol,
                    "pair_id": pair_id,
                    "band": band,
                    "pool": pool_mode,
                    "event_ts": e["OpenTime"],
                    "entry_ts": entry_ts,
                    "anchor_ts": e["anchor_ts"],
                    "session_end": feat_row.get("session_end"),
                    "level_kind": e["level_kind"],
                    "level_price": float(e["level_price"]),
                    "level_distance": dist,
                    "zone_scale": float(scale),
                    "tau": tau,
                    "zone_mode": zone_mode,
                    "into_side": into,
                    "side": -into,
                    "volume_resid": feat_row.get("volume_resid"),
                    "range_resid": feat_row.get("range_resid"),
                    "delta_abs_resid": float(da),
                    "delta_ratio_resid": float(dr),
                    "signed_score": signed,
                    "arm": arm,
                    "ltf_minutes": ltf,
                    "mins_since_close": e.get("mins_since_close"),
                    "formed_ts": e.get("formed_ts"),
                }
            )

    if not rows:
        return _empty_events()
    ev = pl.DataFrame(rows, infer_schema_length=None)
    if nearest_only and pool_mode != "MID_RANGE":
        ev = (
            ev.sort(["event_ts", "level_distance"])
            .unique(subset=["event_ts"], keep="first")
        )
    # Consecutive qualifiers at the same level → first bar only (design §3.2).
    if pool_mode != "MID_RANGE" and "level_kind" in ev.columns:
        ev = (
            ev.sort("event_ts")
            .with_columns(
                (
                    (pl.col("level_kind") == pl.col("level_kind").shift(1))
                    & (pl.col("symbol") == pl.col("symbol").shift(1))
                    & (pl.col("pair_id") == pl.col("pair_id").shift(1))
                    & (
                        (pl.col("event_ts") - pl.col("event_ts").shift(1))
                        .dt.total_minutes()
                        == pl.col("ltf_minutes")
                    )
                )
                .fill_null(False)
                .alias("_consec_same_level")
            )
            .filter(~pl.col("_consec_same_level"))
            .drop("_consec_same_level")
        )
    return ev.sort("event_ts")


def apply_refractory(events: pl.DataFrame, *, refractory_ltf: int = REFRACTORY_LTF) -> pl.DataFrame:
    """Within-(symbol, pair) refractory so primary outcome windows do not overlap."""
    if events.height == 0:
        return events
    keep: list[int] = []
    last_by: dict[tuple, Any] = {}
    for i, r in enumerate(events.sort("event_ts").iter_rows(named=True)):
        key = (r["symbol"], r["pair_id"])
        ltf = int(r["ltf_minutes"])
        et = r["event_ts"]
        prev = last_by.get(key)
        if prev is not None:
            gap_min = (et - prev).total_seconds() / 60.0
            if gap_min < refractory_ltf * ltf:
                continue
        last_by[key] = et
        keep.append(i)
    if not keep:
        return events.head(0)
    ordered = events.sort("event_ts")
    return ordered.with_row_index("_i").filter(pl.col("_i").is_in(keep)).drop("_i")


# --------------------------------------------------------------------------- #
# 1-minute path outcomes (D6.3)
# --------------------------------------------------------------------------- #


def evaluate_outcomes_1m(
    bars_1m: pl.DataFrame,
    events: pl.DataFrame,
    holds: Iterable[int] = HOLDS_LTF,
    *,
    include_session_remainder: bool = True,
) -> pl.DataFrame:
    """Open-to-open side-signed returns + MFE/MAE on the 1-minute path.

    Entry = OPEN of the bar at ``entry_ts`` (next LTF open). Hold H is in LTF
    bars → wall-clock minutes = H × ltf_minutes, stepped on **1-minute opens**.
    Contiguity required over the whole primary span; else the event is dropped
    and the caller counts it.

    When ``include_session_remainder`` and ``session_end`` is present, also emit
    ``ret_bps_session`` / MFE/MAE to the last 1-minute open strictly before
    session end (design §3.4 secondary — DISCLOSURE only; may overlap).
    """
    assert_no_ltf_outcome_path(1, context="evaluate_outcomes_1m")
    if events.height == 0 or bars_1m.height == 0:
        return events.head(0)

    raw = bars_1m.sort("OpenTime")
    ts = raw["OpenTime"].to_list()
    op = raw["Open"].to_numpy().astype(float)
    hi = raw["High"].to_numpy().astype(float)
    lo = raw["Low"].to_numpy().astype(float)
    idx = {t: i for i, t in enumerate(ts)}
    holds = tuple(holds)
    max_h = max(holds) if holds else 0

    out_rows: list[dict] = []
    n_dropped_gap = 0
    for e in events.iter_rows(named=True):
        entry_ts = e["entry_ts"]
        if entry_ts not in idx:
            n_dropped_gap += 1
            continue
        i0 = idx[entry_ts]
        ltf = int(e["ltf_minutes"])
        # event bar must be contiguous into entry (clock definition)
        event_ts = e["event_ts"]
        if event_ts in idx:
            if (entry_ts - event_ts).total_seconds() != ltf * 60:
                n_dropped_gap += 1
                continue
        need = max_h * ltf
        if need > 0:
            if i0 + need >= len(ts):
                n_dropped_gap += 1
                continue
            # contiguity over full primary outcome span
            span = (ts[i0 + need] - ts[i0]).total_seconds() / 60.0
            if span != need:
                n_dropped_gap += 1
                continue
        entry = float(op[i0])
        if entry <= 0:
            n_dropped_gap += 1
            continue
        side = int(e["side"])
        rec = dict(e)
        rec["entry"] = entry
        rec["day"] = entry_ts.replace(hour=0, minute=0, second=0, microsecond=0)
        rec["n_dropped_gap_flag"] = 0

        def _path_stats(i1: int) -> tuple[float, float, float]:
            ret = side * 1e4 * (float(op[i1]) - entry) / entry
            if i1 > i0:
                path_hi = hi[i0 + 1 : i1 + 1]
                path_lo = lo[i0 + 1 : i1 + 1]
            else:
                path_hi = hi[i0:i0]
                path_lo = lo[i0:i0]
            if len(path_hi) == 0:
                return ret, 0.0, 0.0
            if side > 0:
                mfe = 1e4 * (float(path_hi.max()) - entry) / entry
                mae = 1e4 * (float(path_lo.min()) - entry) / entry
            else:
                mfe = 1e4 * (entry - float(path_lo.min())) / entry
                mae = 1e4 * (entry - float(path_hi.max())) / entry
            return ret, float(mfe), float(mae)

        for h in holds:
            i1 = i0 + h * ltf
            ret, mfe, mae = _path_stats(i1)
            rec[f"ret_bps_H{h}"] = ret
            rec[f"mfe_bps_H{h}"] = mfe
            rec[f"mae_bps_H{h}"] = mae
            zs = e.get("zone_scale")
            if (
                zs is not None
                and float(zs) > 0
                and e.get("zone_mode") == "prior_session_range"
            ):
                rec[f"ret_norm_H{h}"] = ret / (1e4 * float(zs) / entry)
            else:
                rec[f"ret_norm_H{h}"] = None

        # Secondary: HTF session remainder (disclosure; may overlap primary)
        rec["ret_bps_session"] = None
        rec["mfe_bps_session"] = None
        rec["mae_bps_session"] = None
        rec["session_remainder_ok"] = False
        if include_session_remainder and e.get("session_end") is not None:
            sess_end = e["session_end"]
            # last 1m open strictly before session_end, after entry
            i_end = bisect.bisect_left(ts, sess_end) - 1
            if i_end > i0 and i_end < len(ts):
                span_s = (ts[i_end] - ts[i0]).total_seconds() / 60.0
                if span_s == float(i_end - i0):
                    ret_s, mfe_s, mae_s = _path_stats(i_end)
                    rec["ret_bps_session"] = ret_s
                    rec["mfe_bps_session"] = mfe_s
                    rec["mae_bps_session"] = mae_s
                    rec["session_remainder_ok"] = True
                    rec["session_exit_ts"] = ts[i_end]
        out_rows.append(rec)

    if not out_rows:
        return events.head(0)
    # infer_schema_length=None: the session-remainder columns are None until an
    # event clears the contiguity guard, so a short inference window can type them
    # Null and then fail on the first real value (QA-9 I-1).
    out = pl.DataFrame(out_rows, infer_schema_length=None)
    out = out.with_columns(pl.lit(n_dropped_gap).alias("_batch_dropped_gap"))
    return out


# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #


def derange_scores_global(
    events: pl.DataFrame,
    col: str = "signed_score",
    *,
    seed: int,
) -> tuple[pl.DataFrame, dict]:
    """Global zero-fixed-point derangement of ``col`` (design §4.2; L-28).

    Not day-blocked — sparse cadence makes within-day derangement near-vacuous
    (AMENDMENT-2). Raises if a fixed point remains.
    """
    if events.height < 2:
        return events.head(0), {
            "n_input": int(events.height),
            "n_deranged": 0,
            "fixed_point_rate": 0.0,
        }
    rng = np.random.default_rng(seed)
    vals = events[col].to_numpy().astype(float)
    n = len(vals)
    perm = derange_perm(n, rng)
    deranged = vals[perm]
    if np.any(deranged == vals):
        # value-fixed points possible even with index derangement; repair
        for _ in range(200):
            perm = derange_perm(n, rng)
            deranged = vals[perm]
            if not np.any(deranged == vals):
                break
        else:
            # if many ties, fall back to index derangement and assert index FP=0
            if np.any(perm == np.arange(n)):
                raise RuntimeError("derangement has fixed points (L-28)")
    if np.any(perm == np.arange(n)):
        raise RuntimeError("derangement has index fixed points (L-28)")
    out = events.with_columns(pl.Series(col, deranged))
    return out, {
        "n_input": n,
        "n_deranged": n,
        "fixed_point_rate": 0.0,
        "seed": seed,
    }


def derange_scores_within_symbol(
    events: pl.DataFrame,
    col: str = "signed_score",
    *,
    seed: int,
) -> tuple[pl.DataFrame, dict]:
    """Within-symbol score derangement (mitigation on the global null)."""
    if events.height == 0:
        return events, {"n_input": 0, "n_deranged": 0, "n_dropped": 0}
    rng = np.random.default_rng(seed)
    parts: list[pl.DataFrame] = []
    n_dropped = 0
    for _, block in events.group_by("symbol", maintain_order=True):
        if block.height < 2:
            n_dropped += block.height
            continue
        vals = block[col].to_numpy().astype(float)
        n = len(vals)
        perm = derange_perm(n, rng)
        if np.any(perm == np.arange(n)):
            raise RuntimeError("within-symbol derangement fixed point (L-28)")
        parts.append(block.with_columns(pl.Series(col, vals[perm])))
    if not parts:
        return events.head(0), {
            "n_input": int(events.height),
            "n_deranged": 0,
            "n_dropped": n_dropped,
        }
    out = pl.concat(parts)
    return out, {
        "n_input": int(events.height),
        "n_deranged": int(out.height),
        "n_dropped": n_dropped,
        "seed": seed,
    }


def matched_random_timing(
    bars_1m: pl.DataFrame,
    events: pl.DataFrame,
    anchors: pl.DataFrame,
    *,
    n_donors: int = N_MATCHED_RANDOM,
    seed: int = 20260721,
    holds: Iterable[int] = HOLDS_LTF,
) -> pl.DataFrame:
    """Cross-session phase-matched unconditional control (design §4.2).

    For each event (side d, phase φ = mins_since_anchor at entry), draw donors
    from other sessions of the same symbol; enter at anchor(donor)+φ on side d;
    resolve at the same H on the 1-minute path. Raises if a donor lands in the
    event's own HTF session.
    """
    if events.height == 0:
        return events.head(0)
    rng = np.random.default_rng(seed)
    a_list = anchors.sort("anchor_ts")
    a_ts = a_list["anchor_ts"].to_list()
    a_end = a_list["session_end"].to_list()
    n_a = len(a_ts)
    sess_len = [
        int((a_end[i] - a_ts[i]).total_seconds() // 60) for i in range(n_a)
    ]

    rows: list[dict] = []
    for e in events.iter_rows(named=True):
        phase = int((e["entry_ts"] - e["anchor_ts"]).total_seconds() // 60)
        side = int(e["side"])
        own = e["anchor_ts"]
        elig = [
            i
            for i in range(n_a)
            if a_ts[i] != own and sess_len[i] > phase + 1
        ]
        if not elig:
            continue
        pick = rng.choice(elig, size=min(n_donors, len(elig)), replace=False)
        for i in pick:
            entry_ts = a_ts[i] + timedelta(minutes=phase)
            # HARD: donor must not land in event's own session
            if e["anchor_ts"] <= entry_ts < e["session_end"]:
                raise RuntimeError(
                    "MATCHED_RANDOM DISJOINT FAIL: donor entry inside event session "
                    f"(design §4.2 / GT-5i) entry={entry_ts} event_anchor={e['anchor_ts']}"
                )
            # The donor's own detection bar, NOT the source event's: the outcome
            # builder checks event→entry contiguity, so stamping the source
            # event_ts here drops every donor row (QA-10 I-1). Source linkage is
            # kept on src_event_ts.
            rows.append(
                {
                    "symbol": e["symbol"],
                    "pair_id": e["pair_id"],
                    "band": e["band"],
                    "pool": "MATCHED_RANDOM",
                    "event_ts": entry_ts - timedelta(minutes=int(e["ltf_minutes"])),
                    "entry_ts": entry_ts,
                    "anchor_ts": a_ts[i],
                    "session_end": a_end[i],
                    "level_kind": e.get("level_kind"),
                    "level_price": e.get("level_price"),
                    "into_side": e["into_side"],
                    "side": side,
                    "signed_score": e.get("signed_score"),
                    "arm": "MATCHED_RANDOM",
                    "ltf_minutes": e["ltf_minutes"],
                    "zone_scale": e.get("zone_scale"),
                    "zone_mode": e.get("zone_mode"),
                    "tau": e.get("tau"),
                    "src_event_ts": e["event_ts"],
                    "src_event_anchor": e["anchor_ts"],
                }
            )
    if not rows:
        return events.head(0)
    ctrl = pl.DataFrame(rows, infer_schema_length=None)
    return evaluate_outcomes_1m(bars_1m, ctrl, holds=holds)


def outcome_path_swap_fixed_h(
    bars_1m: pl.DataFrame,
    events: pl.DataFrame,
    *,
    hold_ltf: int = 10,
    seed: int = 20260722,
) -> tuple[pl.DataFrame, dict]:
    """Fixed-H future-destroy path swap (design §4.3 — NOT spine.outcome_path_swap).

    Donors bucketed by hold length (wall-clock minutes = hold_ltf × ltf).
    Everything at or before entry is identical; the forward path is a deranged
    donor's, re-based to the target's entry price. Zero fixed points, asserted.
    """
    assert_no_ltf_outcome_path(1, context="outcome_path_swap_fixed_h")
    if events.height < 2:
        return events.head(0), {
            "n_input": int(events.height),
            "n_spliced": 0,
            "n_no_donor": int(events.height),
            "spliced_fraction": 0.0,
        }

    raw = bars_1m.sort("OpenTime")
    ts = raw["OpenTime"].to_list()
    op = raw["Open"].to_numpy().astype(float)
    hi = raw["High"].to_numpy().astype(float)
    lo = raw["Low"].to_numpy().astype(float)
    idx = {t: i for i, t in enumerate(ts)}
    rng = np.random.default_rng(seed)

    # Build hold-length buckets
    meta: list[dict] = []
    for e in events.iter_rows(named=True):
        et = e["entry_ts"]
        if et not in idx:
            meta.append({**e, "_i0": -1, "_len": 0})
            continue
        i0 = idx[et]
        ltf = int(e["ltf_minutes"])
        length = hold_ltf * ltf
        meta.append({**e, "_i0": i0, "_len": length, "_entry": float(op[i0]) if i0 >= 0 else None})

    lengths = np.array([m["_len"] for m in meta], dtype=int)
    n = len(meta)
    # bucket by exact length (fixed-H → usually one bucket)
    buckets = lengths.copy()
    donor = np.full(n, -1, dtype=int)
    for b in np.unique(buckets):
        ix = np.where((buckets == b) & (b > 0))[0]
        if len(ix) < 2:
            continue
        for _ in range(200):
            perm = rng.permutation(ix)
            if not np.any(perm == ix):
                donor[ix] = perm
                break
        else:
            donor[ix] = np.roll(ix, 1)
            if np.any(donor[ix] == ix):
                raise RuntimeError("path-swap derangement fixed point (L-28)")

    out_rows: list[dict] = []
    n_no_donor = 0
    for k, m in enumerate(meta):
        d = int(donor[k])
        if d < 0 or m["_i0"] < 0 or meta[d]["_i0"] < 0:
            n_no_donor += 1
            continue
        length = m["_len"]
        i0_t, i0_d = m["_i0"], meta[d]["_i0"]
        if i0_t + length >= len(ts) or i0_d + length >= len(ts):
            n_no_donor += 1
            continue
        # contiguity both windows
        if (ts[i0_t + length] - ts[i0_t]).total_seconds() / 60.0 != length:
            n_no_donor += 1
            continue
        if (ts[i0_d + length] - ts[i0_d]).total_seconds() / 60.0 != length:
            n_no_donor += 1
            continue
        entry_t = float(m["_entry"])
        entry_d = float(meta[d]["_entry"])
        offset = entry_t - entry_d
        side = int(m["side"])
        # re-based donor path on target's timeline
        d_op = op[i0_d : i0_d + length + 1] + offset
        d_hi = hi[i0_d + 1 : i0_d + length + 1] + offset
        d_lo = lo[i0_d + 1 : i0_d + length + 1] + offset
        ret = side * 1e4 * (float(d_op[length]) - entry_t) / entry_t
        if side > 0:
            mfe = 1e4 * (float(d_hi.max()) - entry_t) / entry_t if len(d_hi) else 0.0
            mae = 1e4 * (float(d_lo.min()) - entry_t) / entry_t if len(d_lo) else 0.0
            donor_mfe = 1e4 * (
                float(hi[i0_d + 1 : i0_d + length + 1].max()) - entry_d
            ) / entry_d if length > 0 else 0.0
        else:
            mfe = 1e4 * (entry_t - float(d_lo.min())) / entry_t if len(d_lo) else 0.0
            mae = 1e4 * (entry_t - float(d_hi.max())) / entry_t if len(d_hi) else 0.0
            donor_mfe = 1e4 * (
                entry_d - float(lo[i0_d + 1 : i0_d + length + 1].min())
            ) / entry_d if length > 0 else 0.0
        rec = {k2: v for k2, v in m.items() if not str(k2).startswith("_")}
        rec[f"ret_bps_H{hold_ltf}"] = ret
        rec[f"mfe_bps_H{hold_ltf}"] = float(mfe)
        rec[f"mae_bps_H{hold_ltf}"] = float(mae)
        rec["mfe_bps"] = float(mfe)  # bite unit
        rec["donor_mfe_bps"] = float(donor_mfe)
        rec["donor_event_ts"] = meta[d]["event_ts"]
        rec["entry"] = entry_t
        out_rows.append(rec)

    cov = {
        "n_input": n,
        "n_spliced": len(out_rows),
        "n_no_donor": n_no_donor,
        "spliced_fraction": float(len(out_rows) / n) if n else 0.0,
        "hold_ltf": hold_ltf,
        "seed": seed,
    }
    if not out_rows:
        return events.head(0), cov
    return pl.DataFrame(out_rows, infer_schema_length=None), cov


def _corr_finite(a: np.ndarray, b: np.ndarray) -> tuple[float | None, int]:
    """Pearson corr with an explicit finite guard (Addendum §2.5)."""
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    n = int(len(a))
    if n < 5 or a.std() == 0 or b.std() == 0:
        return None, n
    return float(np.corrcoef(a, b)[0, 1]), n


def path_swap_bite_bps(swapped: pl.DataFrame) -> dict:
    """Positive-control bite: corr(swapped_mfe_bps, donor_mfe_bps) > 0.5 (design §4.3).

    Computed **per symbol**, then pooled. ``mfe_bps`` divides the donor's
    excursion by the TARGET's entry price while ``donor_mfe_bps`` divides it by
    the DONOR's — within a symbol those divisors are comparable, but the D1
    cross-section spans seven orders of magnitude in price (0.00067 → 20551), so
    a single pooled correlation measures divisor dispersion rather than whether
    the swap reached the reads. That is exactly the divisor mismatch
    AMENDMENT-15 / QA-2 R-4 forbids. The pooled figure is still reported; the
    0.5 floor is applied to the per-symbol median (post-measurement
    AMENDMENT-27).
    """
    if swapped.height == 0 or "mfe_bps" not in swapped.columns:
        return {"n": 0, "corr": None, "bite_ok": False, "reason": "no swapped rows"}
    a_all = swapped["mfe_bps"].to_numpy().astype(float)
    b_all = swapped["donor_mfe_bps"].to_numpy().astype(float)
    pooled_corr, n = _corr_finite(a_all, b_all)

    per_symbol: dict[str, float] = {}
    if "symbol" in swapped.columns:
        for sym, block in swapped.group_by("symbol", maintain_order=True):
            key = sym[0] if isinstance(sym, tuple) else sym
            c, n_s = _corr_finite(
                block["mfe_bps"].to_numpy().astype(float),
                block["donor_mfe_bps"].to_numpy().astype(float),
            )
            if c is not None:
                per_symbol[str(key)] = c
    vals = np.array(list(per_symbol.values())) if per_symbol else np.array([])
    median = float(np.median(vals)) if vals.size else None
    return {
        "n": n,
        "corr": pooled_corr,
        "corr_pooled_note": (
            "pooled across a 7-orders-of-magnitude price cross-section — "
            "divisor-dispersion artifact; not the adjudicating figure"
        ),
        "per_symbol_median_corr": median,
        "per_symbol_min_corr": float(vals.min()) if vals.size else None,
        "n_symbols": int(vals.size),
        "frac_symbols_above_floor": (
            float(np.mean(vals > 0.5)) if vals.size else None
        ),
        "bite_ok": bool(median is not None and median > 0.5),
        "floor": 0.5,
        "applied_to": "per_symbol_median_corr",
    }


def spearman_finite(x: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    """Spearman ρ with explicit finite-value guard (Addendum §2.5). Returns (ρ, n_kept)."""
    from scipy.stats import spearmanr

    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 5:
        return float("nan"), n
    rho = float(spearmanr(x[ok], y[ok]).correlation)
    return rho, n


def signed_score_plant_mde_curve(
    events: pl.DataFrame,
    *,
    ret_col: str,
    n_seeds: int = 200,
    grid: np.ndarray | None = None,
    seed: int = 20260723,
) -> dict:
    """Resolution of T2's Spearman read under a known monotone return plant.

    The observed monotone component is removed first, then ``u`` bps per one
    standard deviation of ``signed_score`` is added to the real return noise.
    At every grid point the score is globally deranged with zero index fixed
    points. The first plant whose observed rho clears the one-sided 5% null is
    the published MDE; its units are both plant bps/score-SD and rho.
    """
    from scipy.stats import rankdata

    if grid is None:
        grid = np.arange(0.0, 30.01, 0.5)
    if (
        events.height < 8
        or "signed_score" not in events.columns
        or ret_col not in events.columns
        or n_seeds < 1
    ):
        return {
            "mde_rho": None,
            "mde_plant_bps_per_score_sd": None,
            "UNPOWERED": True,
            "n": int(events.height),
        }

    x_all = events["signed_score"].to_numpy().astype(float)
    y_all = events[ret_col].to_numpy().astype(float)
    ok = np.isfinite(x_all) & np.isfinite(y_all)
    x, y = x_all[ok], y_all[ok]
    n = int(len(x))
    sx = float(np.std(x))
    if n < 8 or not np.isfinite(sx) or sx <= 0:
        return {
            "mde_rho": None,
            "mde_plant_bps_per_score_sd": None,
            "UNPOWERED": True,
            "n": n,
            "reason": "insufficient finite score variation",
        }
    z = (x - float(np.mean(x))) / sx

    # Centre the observed Spearman component, mirroring the contrast centring
    # used by plant_mde_curve. A deterministic bisection finds the smallest
    # absolute residual rho without altering the real return noise distribution.
    def _rho_at(beta: float) -> float:
        return spearman_finite(x, y - beta * z)[0]

    rho0 = _rho_at(0.0)
    beta = 0.0
    if np.isfinite(rho0) and rho0 != 0.0:
        step = max(float(np.std(y)), 1e-6)
        lo, hi = (0.0, step) if rho0 > 0 else (-step, 0.0)
        edge = hi if rho0 > 0 else lo
        for _ in range(24):
            r_edge = _rho_at(edge)
            if np.isfinite(r_edge) and np.sign(r_edge) != np.sign(rho0):
                break
            step *= 2.0
            edge = step if rho0 > 0 else -step
        if rho0 > 0:
            hi = edge
        else:
            lo = edge
        candidates = [(abs(rho0), 0.0)]
        for _ in range(40):
            mid = (lo + hi) / 2.0
            r_mid = _rho_at(mid)
            if not np.isfinite(r_mid):
                break
            candidates.append((abs(r_mid), mid))
            if np.sign(r_mid) == np.sign(rho0):
                if rho0 > 0:
                    lo = mid
                else:
                    hi = mid
            elif rho0 > 0:
                hi = mid
            else:
                lo = mid
        beta = min(candidates, key=lambda item: item[0])[1]
    y_centred = y - beta * z
    centred_rho = spearman_finite(x, y_centred)[0]

    def _std_ranks(values: np.ndarray) -> np.ndarray:
        ranks = rankdata(values, method="average").astype(float)
        sd = float(np.std(ranks))
        if sd <= 0 or not np.isfinite(sd):
            return np.full(len(ranks), np.nan)
        return (ranks - float(np.mean(ranks))) / sd

    x_rank = _std_ranks(x)
    rng = np.random.default_rng(seed)
    deranged_ranks = np.empty((n_seeds, n), dtype=np.float32)
    for i in range(n_seeds):
        perm = derange_perm(n, rng)
        if np.any(perm == np.arange(n)):
            raise RuntimeError("T2 plant derangement has fixed points (L-28)")
        deranged_ranks[i] = x_rank[perm]

    curve: list[dict] = []
    mde_rho: float | None = None
    mde_plant: float | None = None
    for u in grid:
        planted = y_centred + float(u) * z
        y_rank = _std_ranks(planted)
        if not np.all(np.isfinite(y_rank)):
            continue
        rho = float(np.mean(x_rank * y_rank))
        null = (deranged_ranks @ y_rank) / float(n)
        p_one = float(np.mean(null >= rho))
        critical = float(np.quantile(null, 0.95))
        row = {
            "plant_bps_per_score_sd": float(u),
            "planted_rho": rho,
            "deranged_rho_mean": float(np.mean(null)),
            "deranged_rho_ci": [
                float(np.quantile(null, 0.025)),
                float(np.quantile(null, 0.975)),
            ],
            "critical_rho_p95": critical,
            "one_sided_p": p_one,
        }
        curve.append(row)
        if float(u) > 0 and rho > critical and p_one <= 0.05:
            mde_rho = rho
            mde_plant = float(u)
            break

    return {
        "mde_rho": mde_rho,
        "mde_plant_bps_per_score_sd": mde_plant,
        "UNPOWERED": mde_rho is None,
        "n": n,
        "n_seeds": int(n_seeds),
        "centred_on_observed": True,
        "centering_bps_per_score_sd": float(beta),
        "observed_rho": float(rho0),
        "centred_rho": float(centred_rho),
        "zero_fixed_points_asserted": True,
        "curve": curve,
        "grid_max": float(grid[-1]),
    }


def contrast_day_clustered(
    treat: pl.DataFrame,
    base: pl.DataFrame,
    *,
    ret_col: str,
    block: int = DAY_BLOCK,
) -> dict:
    """Day-clustered block-bootstrap CI on the per-day arm contrast (bps).

    Resampling unit = calendar day (design §6.4). On days with both arms, the
    unit is ``mean(treat|day) − mean(base|day)``; on treat-only days the global
    base mean is the fallback (disclosed).
    """
    from xen.evaluation import block_bootstrap_ci

    if treat.height == 0 or base.height == 0:
        return {"n_treat": treat.height, "n_base": base.height, "UNPOWERED": True}
    if ret_col not in treat.columns or ret_col not in base.columns:
        return {"error": f"missing {ret_col}", "UNPOWERED": True}

    def _day_means(df: pl.DataFrame) -> dict:
        g = df.group_by("day").agg(pl.col(ret_col).mean().alias("m"))
        return {r["day"]: r["m"] for r in g.iter_rows(named=True)}

    mt, mb = _day_means(treat), _day_means(base)
    base_mean = float(base[ret_col].mean())
    if not mt:
        return {"n_treat": treat.height, "n_base": base.height, "UNPOWERED": True}
    shared = sorted(set(mt) & set(mb))
    if len(shared) >= 3:
        day_contrast = np.array([mt[d] - mb[d] for d in shared])
        paired = True
    else:
        day_contrast = np.array([mt[d] - base_mean for d in mt])
        paired = False
    if len(day_contrast) < 3:
        return {
            "n_treat": treat.height,
            "n_base": base.height,
            "n_days": len(day_contrast),
            "n_shared_days": len(shared),
            "contrast": float(treat[ret_col].mean() - base_mean),
            "paired_days": paired,
            "UNPOWERED": True,
        }
    r = block_bootstrap_ci(day_contrast, np.mean, block=block)
    return {
        "n_treat": treat.height,
        "n_base": base.height,
        "n_days": len(day_contrast),
        "n_shared_days": len(shared),
        "paired_days": paired,
        "contrast": float(r["stat"]),
        "ci": list(r["ci"]),
        "excludes_zero": bool(r["ci"][0] > 0 or r["ci"][1] < 0),
        "treat_mean": float(treat[ret_col].mean()),
        "base_mean": base_mean,
        "UNPOWERED": False,
    }


def plant_mde_curve(
    treat: pl.DataFrame,
    base: pl.DataFrame,
    *,
    ret_col: str,
    grid: np.ndarray | None = None,
    block: int = DAY_BLOCK,
) -> dict:
    """Smallest additive plant u whose day-clustered CI excludes 0 — the arm's RESOLUTION.

    The treat arm is first CENTRED on the base arm (its observed contrast is
    subtracted), so the answer measures what this arm at this realised n can
    resolve, independently of what was observed. Without centring the sweep
    returns 0.0 whenever the raw contrast is already materially positive, which
    breaks both consumers (QA-12): §5's ``effect ≥ its own MDE`` test becomes
    circular, and ``calibrate_cf_star`` would plant 0 bps and therefore
    calibrate CF* on the OBSERVED, possibly-leaking edge — the AMENDMENT-13
    defect, in the one regime where CF* is ever applied. Centred, u=0 can never
    qualify, so the result is strictly positive or ``None``.

    Published before the real read (design §4.2 / §6.3). Units = bps contrast.
    """
    if grid is None:
        grid = np.arange(0.0, 30.01, 0.5)
    if treat.height == 0 or base.height == 0 or ret_col not in treat.columns:
        return {"mde_bps": None, "UNPOWERED": True, "grid": list(map(float, grid))}
    obs = contrast_day_clustered(treat, base, ret_col=ret_col, block=block)
    obs_c = obs.get("contrast")
    if obs_c is None:
        return {
            "mde_bps": None,
            "n_treat": int(treat.height),
            "n_base": int(base.height),
            "UNPOWERED": True,
            "note": "observed contrast unresolvable — cannot centre the arm",
        }
    # Centre once. A constant plant translates every day contrast, every
    # bootstrap resample, and therefore both CI bounds by exactly ``u``. One
    # bootstrap is mathematically identical to rerunning the same fixed-seed
    # bootstrap for every grid point, while avoiding 61 repeated 50k-resample
    # calculations per curve.
    centred = treat.with_columns((pl.col(ret_col) - float(obs_c)).alias(ret_col))
    resolution = contrast_day_clustered(centred, base, ret_col=ret_col, block=block)
    ci = resolution.get("ci")
    if ci is not None and len(ci) >= 2 and np.isfinite(ci[0]):
        for u in grid:
            if float(ci[0]) + float(u) > 0:
                return {
                    "mde_bps": float(u),
                    "n_treat": int(treat.height),
                    "n_base": int(base.height),
                    "UNPOWERED": False,
                    "centred_on_observed": True,
                    "observed_contrast": float(obs_c),
                    "centred_ci": list(ci),
                    "grid_max": float(grid[-1]),
                }
    return {
        "mde_bps": None,
        "n_treat": int(treat.height),
        "n_base": int(base.height),
        "UNPOWERED": True,
        "centred_on_observed": True,
        "observed_contrast": float(obs_c),
        "note": "no plant in grid produced CI>0",
        "grid_max": float(grid[-1]),
    }


def label_band(effect: float | None, ci: list | None, mde: float | None) -> str:
    """§5 interpretation labels — report only, never a gate.

    A measured interval wholly below zero is CONTRADICTED even when no MDE is
    available: that band has no MDE term. Positive intervals without an MDE are
    SUGGESTIVE; zero-spanning intervals need an MDE to distinguish WASH from
    IMPRECISE and are therefore UNPOWERED when it is absent.
    """
    if effect is None or (isinstance(effect, float) and not np.isfinite(effect)):
        return "UNPOWERED"
    # An MDE of exactly 0 is a VALID resolution statement ("this arm resolves any
    # positive effect"), so §5's `effect ≥ its own MDE` still applies and
    # SUPPORTED stays reachable. Only a non-finite or negative MDE is unusable.
    # `calibrate_cf_star` refuses the same 0 as a plant size — the two consumers
    # disagreed before QA-12 and now agree on what 0 means.
    if mde is not None and (not np.isfinite(mde) or mde < 0):
        mde = None
    if ci is None or len(ci) < 2:
        return "UNPOWERED"
    lo, hi = ci[0], ci[1]
    if lo is None or hi is None:
        return "UNPOWERED"
    try:
        lo_f, hi_f = float(lo), float(hi)
    except (TypeError, ValueError):
        return "UNPOWERED"
    if not np.isfinite(lo_f) or not np.isfinite(hi_f) or lo_f > hi_f:
        return "UNPOWERED"
    if hi_f < 0:
        return "CONTRADICTED"
    if lo_f > 0:
        if mde is None:
            return "SUGGESTIVE"
        return "SUPPORTED" if abs(float(effect)) >= float(mde) else "SUGGESTIVE"
    if mde is None:
        return "UNPOWERED"
    # CI spans zero. Below the arm's resolution ⇒ within noise (the powered null
    # cell). At or above it ⇒ IMPRECISE: a point estimate larger than what the
    # arm resolves, whose interval still spans zero — inconclusive, never a null
    # (design §5 / AMENDMENT-30). The MDE plants a CONSTANT shift and so carries
    # no dispersion; a real, day-concentrated effect can beat it and still not
    # exclude zero.
    return "WASH" if abs(float(effect)) < float(mde) else "IMPRECISE"


def _swap_pooled(
    bars_by: dict[str, pl.DataFrame],
    events: pl.DataFrame,
    *,
    hold_ltf: int,
    seed: int,
) -> pl.DataFrame:
    """Fixed-H path swap run per symbol (donors must share a price series), pooled."""
    parts: list[pl.DataFrame] = []
    for sym, block in events.group_by("symbol", maintain_order=True):
        key = sym[0] if isinstance(sym, tuple) else sym
        bars = bars_by.get(str(key))
        if bars is None or block.height < 2:
            continue
        try:
            sw, _ = outcome_path_swap_fixed_h(
                bars, block, hold_ltf=hold_ltf, seed=seed
            )
        except Exception:
            continue
        if sw.height:
            parts.append(sw)
    if not parts:
        return events.head(0)
    return pl.concat(parts, how="diagonal_relaxed")


def calibrate_cf_star(
    bars_by: dict[str, pl.DataFrame],
    events: pl.DataFrame,
    *,
    ret_col: str = "ret_bps_H10",
    hold_ltf: int = 10,
    mde_bps: float,
    plant_multiples: tuple[float, ...] = (1.0, 2.0, 3.0),
    n_seeds: int = 200,
    seed0: int = 20260722,
) -> dict:
    """Derive CF* on a planted causal edge (design §4.3 AMENDMENT-13).

    Plant ``k × MDE`` on the S9 arm, run fixed-H path-swap over ``n_seeds``,
    take the upper 95th percentile of |collapse_fraction|. Emit all three
    plant sizes; apply the 1× value.

    Calibrated on the **pooled** arm across symbols — the arm the tripwire is
    actually applied to. A single-symbol arm cannot produce a material planted
    contrast, so every seed was discarded and the inherited 0.25 prior was used
    instead, which is precisely what AMENDMENT-4 forbids (QA-12 finding).
    ``mde_bps`` must come from the SAME arm, else a 1× plant is not material by
    construction. When the arm cannot support a material plant at any size,
    CF* is reported ``UNDERIVABLE`` — it is never silently defaulted to 0.25.
    """
    if "arm" not in events.columns or ret_col not in events.columns:
        return {
            "cf_star": None,
            "status": "UNDERIVABLE",
            "reason": f"events lack 'arm' or {ret_col!r}",
            "prior_cf": 0.25,
            "prior_is_never_a_fallback": True,
        }
    s9 = events.filter(pl.col("arm") == "S9")
    base = events.filter(pl.col("arm") == "BASE")
    out: dict[str, Any] = {
        "ret_col": ret_col,
        "hold_ltf": hold_ltf,
        "mde_bps": mde_bps,
        "n_seeds": n_seeds,
        "n_S9": int(s9.height),
        "n_BASE": int(base.height),
        "n_symbols": int(events["symbol"].n_unique()) if "symbol" in events.columns else 0,
        "by_multiple": {},
        "prior_cf": 0.25,
        "prior_is_never_a_fallback": True,
    }
    if s9.height < 2 or base.height < 1 or ret_col not in events.columns:
        out.update({"cf_star": None, "status": "UNDERIVABLE", "reason": "thin arms"})
        return out
    if not mde_bps or float(mde_bps) <= 0:
        # A zero/absent plant would calibrate CF* on the OBSERVED edge rather
        # than a known causal one (AMENDMENT-13). Never proceed on it.
        out.update(
            {
                "cf_star": None,
                "status": "UNDERIVABLE",
                "reason": (
                    "no strictly positive MDE at realised n — the arm cannot "
                    "support a known causal plant, so CF* has no valid regime"
                ),
                "mde_bps_seen": mde_bps,
            }
        )
        return out

    for k in plant_multiples:
        plant = float(k) * float(mde_bps)
        # The planted raw contrast is deterministic — compute it once, not per seed.
        s9p = s9.with_columns((pl.col(ret_col) + plant).alias(ret_col))
        raw = contrast_day_clustered(s9p, base, ret_col=ret_col)
        if not raw.get("excludes_zero"):
            out["by_multiple"][str(k)] = {
                "plant_bps": plant,
                "n_usable_seeds": 0,
                "cf_star": None,
                "reason": "planted raw contrast not material at this arm",
            }
            continue
        raw_c = float(raw["contrast"])
        if raw_c == 0:
            out["by_multiple"][str(k)] = {
                "plant_bps": plant, "n_usable_seeds": 0, "cf_star": None,
                "reason": "zero raw contrast",
            }
            continue
        pool = pl.concat([s9p, base.select(s9p.columns)], how="diagonal_relaxed")
        collapse = []
        for s in range(n_seeds):
            sw = _swap_pooled(bars_by, pool, hold_ltf=hold_ltf, seed=seed0 + s)
            if sw.height == 0 or ret_col not in sw.columns:
                continue
            sw_s9 = sw.filter(pl.col("arm") == "S9")
            sw_base = sw.filter(pl.col("arm") == "BASE")
            if sw_s9.height == 0 or sw_base.height == 0:
                continue
            dest = contrast_day_clustered(sw_s9, sw_base, ret_col=ret_col)
            if dest.get("contrast") is None:
                continue
            collapse.append(float(dest["contrast"]) / raw_c)
        arr = np.abs(np.array(collapse)) if collapse else np.array([])
        out["by_multiple"][str(k)] = {
            "plant_bps": plant,
            "raw_contrast": raw_c,
            "n_usable_seeds": len(collapse),
            "cf_star": float(np.quantile(arr, 0.95)) if arr.size else None,
        }
    one = out["by_multiple"].get("1.0") or out["by_multiple"].get("1") or {}
    out["cf_star"] = one.get("cf_star")
    out["applied_multiple"] = 1.0
    out["status"] = "DERIVED" if out["cf_star"] is not None else "UNDERIVABLE"
    if out["status"] == "UNDERIVABLE":
        out.setdefault("reason", "no usable calibration seed at the 1x plant")
    # Stability across plant sizes (QA-3 R20).
    sizes = [v.get("cf_star") for v in out["by_multiple"].values() if v.get("cf_star") is not None]
    out["cf_star_spread_across_plants"] = (
        float(max(sizes) - min(sizes)) if len(sizes) > 1 else None
    )
    return out


#: Phase-band width (minutes) for bare-level matching (same phase band as event).
BARE_PHASE_BAND_MIN = 30


def bare_level_touch_events(
    symbol: str,
    band: str,
    pair_id: str,
    *,
    events: pl.DataFrame,
    tau: float,
    zone_mode: ZoneMode = "prior_session_range",
    n_per_event: int = 30,
    seed: int = 20260721,
    phase_band_min: int = BARE_PHASE_BAND_MIN,
    bars_1m: pl.DataFrame | None = None,
    root: Path | None = None,
) -> pl.DataFrame:
    """Location-only control: zone contact WITHOUT climax-hold signature (T5).

    For each pool-P event, draw up to ``n_per_event`` bare-touch donors matched on
    **same symbol, same level_kind, same side, same phase band** (mins_since_close
    within ±phase_band_min), DISJOINT from pool P by the effort/no-result legs
    (design §4.2). Seeded; outcomes on the 1-minute path.
    """
    root = root or repo_root()
    if events.height == 0:
        return _empty_events()
    # Restrict to this symbol's events
    if "symbol" in events.columns:
        target_ev = events.filter(pl.col("symbol") == symbol)
    else:
        target_ev = events
    if target_ev.height == 0:
        return _empty_events()

    bars_1m = bars_1m if bars_1m is not None else load_bars(symbol, band, root=root)
    if bars_1m.height == 0:
        return _empty_events()
    ltf = int(PAIR_SPECS[pair_id]["ltf_minutes"])
    ib_mins = ib_minutes_for_pair(pair_id)
    a_spec = _anchor_spec(PAIR_SPECS[pair_id]["anchor"])
    lo, hi = bars_1m["OpenTime"].min(), bars_1m["OpenTime"].max()
    anchors = anchor_table(a_spec, lo, hi)
    complete = ltf_complete_bars(bars_1m, pair_id)
    if complete.height == 0:
        return _empty_events()
    mdf = residualise_pair(complete, symbol, pair_id, root=root)
    th = load_thresholds(pair_id, symbol, root=root)
    v_hi = float(th["volume"]["high"])
    r_lo = float(th["range"]["low"])
    # DISJOINT from pool P: not both effort and no-result
    non = mdf.filter(
        ~((pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= r_lo))
    )
    if non.height == 0:
        return _empty_events()
    if "window_class" in non.columns:
        non = non.filter(pl.col("window_class") == WINDOW_COMPLETE)
    non = non.with_columns(pl.col("Close").shift(1).alias("prev_close"))
    cand_sess = assign_candidate_sessions(non, anchors, ltf_minutes=ltf)
    if cand_sess.height == 0:
        return _empty_events()
    if "session_end" not in cand_sess.columns:
        cand_sess = cand_sess.join(
            anchors.select("anchor_ts", "session_end"), on="anchor_ts", how="left"
        )
    only = set(cand_sess["anchor_ts"].unique().to_list())
    levels = structural_levels_1m(
        bars_1m, anchors, ib_mins, only_anchors=only, include_profile=True
    )
    pairs_lv = available_levels_for_candidates(cand_sess, levels)
    if pairs_lv.height == 0:
        return _empty_events()
    ranges = prior_htf_session_ranges(bars_1m, anchors)
    range_map = {
        r["anchor_ts"]: float(r["prior_session_range"])
        for r in ranges.iter_rows(named=True)
        if r["prior_session_range"] is not None
    }
    ib_map: dict[Any, float] = {}
    if levels.height and "ib_width" in levels.columns:
        for r in levels.select("anchor_ts", "ib_width").unique().iter_rows(named=True):
            if r["ib_width"] is not None:
                ib_map[r["anchor_ts"]] = float(r["ib_width"])

    # Build donor pool keyed for matching
    donors: list[dict] = []
    avail = pairs_lv.filter(pl.col("level_available"))
    # join session_end / mins_since_close if missing on avail
    if "mins_since_close" not in avail.columns or "session_end" not in avail.columns:
        avail = avail.join(
            cand_sess.select(
                "OpenTime", "anchor_ts", "mins_since_close", "session_end"
            ).unique(subset=["OpenTime", "anchor_ts"]),
            on=["OpenTime", "anchor_ts"],
            how="left",
        )
    event_times = set(target_ev["event_ts"].to_list()) if "event_ts" in target_ev.columns else set()
    for e in avail.iter_rows(named=True):
        if e["OpenTime"] in event_times:
            continue  # never reuse a pool-P bar
        scale = (
            ib_map.get(e["anchor_ts"])
            if zone_mode == "ib_width"
            else range_map.get(e["anchor_ts"])
        )
        if scale is None or scale <= 0:
            continue
        if float(e["level_distance"]) > tau * scale:
            continue
        into = _into_side(float(e["Close"]), float(e["level_price"]), None)
        if into == 0:
            continue
        phase = e.get("mins_since_close")
        if phase is None:
            continue
        donors.append(
            {
                "event_ts": e["OpenTime"],
                "entry_ts": e["OpenTime"] + timedelta(minutes=ltf),
                "anchor_ts": e["anchor_ts"],
                "session_end": e.get("session_end"),
                "level_kind": e["level_kind"],
                "level_price": float(e["level_price"]),
                "level_distance": float(e["level_distance"]),
                "zone_scale": float(scale),
                "into_side": into,
                "side": -into,
                "mins_since_close": int(phase),
            }
        )
    if not donors:
        return _empty_events()

    # Index donors by (level_kind, side)
    by_key: dict[tuple, list[dict]] = {}
    for d in donors:
        by_key.setdefault((d["level_kind"], d["side"]), []).append(d)

    rng = np.random.default_rng(seed)
    picked: list[dict] = []
    for ev in target_ev.iter_rows(named=True):
        kind = ev.get("level_kind")
        side = int(ev["side"])
        phase = ev.get("mins_since_close")
        if phase is None and ev.get("entry_ts") is not None and ev.get("anchor_ts") is not None:
            phase = int((ev["entry_ts"] - ev["anchor_ts"]).total_seconds() // 60)
        if kind is None or phase is None:
            continue
        pool = by_key.get((kind, side), [])
        if not pool:
            continue
        # same phase band; exclude event's own session
        own_anchor = ev.get("anchor_ts")
        elig = [
            d
            for d in pool
            if abs(int(d["mins_since_close"]) - int(phase)) <= phase_band_min
            and d["anchor_ts"] != own_anchor
        ]
        if not elig:
            continue
        n_draw = min(n_per_event, len(elig))
        choose = rng.choice(len(elig), size=n_draw, replace=False)
        for j in choose:
            d = elig[int(j)]
            picked.append(
                {
                    "symbol": symbol,
                    "pair_id": pair_id,
                    "band": band,
                    "pool": "BARE_TOUCH",
                    "event_ts": d["event_ts"],
                    "entry_ts": d["entry_ts"],
                    "anchor_ts": d["anchor_ts"],
                    "session_end": d["session_end"],
                    "level_kind": d["level_kind"],
                    "level_price": d["level_price"],
                    "level_distance": d["level_distance"],
                    "zone_scale": d["zone_scale"],
                    "tau": tau,
                    "zone_mode": zone_mode,
                    "into_side": d["into_side"],
                    "side": d["side"],
                    "arm": "BARE_TOUCH",
                    "ltf_minutes": ltf,
                    "mins_since_close": d["mins_since_close"],
                    "signed_score": None,
                    "src_event_ts": ev.get("event_ts"),
                }
            )
    if not picked:
        return _empty_events()
    bare = pl.DataFrame(picked, infer_schema_length=None)
    return evaluate_outcomes_1m(bars_1m, bare)


# --------------------------------------------------------------------------- #
# Universe from coverage_report
# --------------------------------------------------------------------------- #


def usable_universe(
    pair_id: str,
    *,
    retention_floor: float = 0.50,
    root: Path | None = None,
) -> dict[str, Any]:
    """Option-A usable universe from the frozen coverage report."""
    root = root or repo_root()
    cov = json.loads(
        _path(root, f"{INFR020_RESULTS}/coverage_report.json").read_text()
    )
    ltf = int(PAIR_SPECS[pair_id]["ltf_minutes"])
    kept: list[str] = []
    limited: list[str] = []
    for inst in cov["instruments"]:
        sym = inst["symbol"]
        if ltf == 1:
            # D1: all instruments with a 1m pin (in_frozen_pin)
            if inst.get("one_minute", {}).get("in_frozen_pin", True):
                kept.append(sym)
            else:
                limited.append(sym)
            continue
        per = (inst.get("periods") or {}).get(f"{ltf}m") or {}
        ret = per.get("retention")
        if ret is not None and float(ret) >= retention_floor:
            kept.append(sym)
        else:
            limited.append(sym)
    return {
        "pair_id": pair_id,
        "ltf_minutes": ltf,
        "retention_floor": retention_floor,
        "n_usable": len(kept),
        "n_liquidity_limited": len(limited),
        "usable": sorted(kept),
        "liquidity_limited": sorted(limited),
    }


def cost_floor_bps(
    symbol: str,
    *,
    hold_hours: float,
    root: Path | None = None,
) -> dict[str, Any]:
    """Per-symbol floor from the INFR-017 column pin (design §6.1)."""
    from xen.evaluation import bybit_round_trip_cost_bps

    root = root or repo_root()
    pins = json.loads(_path(root, COLUMN_PINS_JSON).read_text())
    per = (pins.get("per_symbol") or {}).get(symbol) or {}
    tick = per.get("one_tick_bps")
    flip = None
    sample = per.get("sample") or {}
    c_flip = sample.get("candidate_C_flip_pair") or {}
    if isinstance(c_flip, dict) and c_flip.get("median") is not None:
        flip = float(c_flip["median"])
    if tick is not None:
        tick = float(tick)
    if tick is None and flip is None:
        spread = 0.0
        spread_label = "NO_SPREAD_PIN"
    elif tick is None:
        spread = float(flip)
        spread_label = "FLIP_PAIR_ONLY"
    elif flip is None:
        spread = float(tick)
        spread_label = "SPREAD_TICK_FLOOR_ONLY"
    else:
        spread = max(float(tick), float(flip))
        # Pin labels flip-pair as a conservative UPPER bound on the audited set.
        spread_label = "MAX_TICK_FLIP_UPPER_BOUND"
    floor = bybit_round_trip_cost_bps(
        symbol, 1.0, liquidity="taker", spread_bps=spread, hold_hours=hold_hours
    )
    return {
        "symbol": symbol,
        "hold_hours": hold_hours,
        "one_tick_bps": tick,
        "flip_pair_bps": flip,
        "spread_used_bps": spread,
        "spread_label": spread_label,
        "validated_on_sample_only": bool(flip is not None),
        **floor,
    }


# --------------------------------------------------------------------------- #
# Schema helpers
# --------------------------------------------------------------------------- #


def _empty_events() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "symbol": pl.Utf8,
            "pair_id": pl.Utf8,
            "band": pl.Utf8,
            "pool": pl.Utf8,
            "event_ts": pl.Datetime("us"),
            "entry_ts": pl.Datetime("us"),
            "anchor_ts": pl.Datetime("us"),
            "session_end": pl.Datetime("us"),
            "level_kind": pl.Utf8,
            "level_price": pl.Float64,
            "level_distance": pl.Float64,
            "zone_scale": pl.Float64,
            "tau": pl.Float64,
            "zone_mode": pl.Utf8,
            "into_side": pl.Int64,
            "side": pl.Int64,
            "volume_resid": pl.Float64,
            "range_resid": pl.Float64,
            "delta_abs_resid": pl.Float64,
            "delta_ratio_resid": pl.Float64,
            "signed_score": pl.Float64,
            "arm": pl.Utf8,
            "ltf_minutes": pl.Int64,
            "mins_since_close": pl.Int64,
        }
    )


def hold_hours_for_pair(pair_id: str, hold_ltf: int) -> float:
    """Wall-clock hours for a primary hold."""
    return hold_ltf * int(PAIR_SPECS[pair_id]["ltf_minutes"]) / 60.0
