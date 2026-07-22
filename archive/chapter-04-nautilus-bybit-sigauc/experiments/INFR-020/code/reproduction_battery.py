"""INFR-020 reproduction battery A1–A11 (design §4).

Run (DESIGN-band sample by default)::

    python/.venv/bin/python python/experiments/INFR-020/code/reproduction_battery.py
    python/.venv/bin/python python/experiments/INFR-020/code/reproduction_battery.py --full

Exits 0 only when every executed assert passes. Writes
``results/reproduction_battery.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.sigbar.baselines import (  # noqa: E402
    BASELINE_METRICS,
    FULL_GRID_CELLS,
    fit_seasonal_baseline,
    full_grid_cells,
    residualise,
)
from xen.sigbar.classes import derive_thresholds  # noqa: E402
from xen.sigbar.fences import (  # noqa: E402
    BASELINES_SHA256,
    assert_design_only_fit,
    assert_frozen_inputs,
    assert_levels_from_1m,
    assert_no_forward_provenance,
    assert_windows_complete,
    check_no_outcome_columns,
    load_bars,
    repo_root,
)
from xen.sigbar.ltf import (  # noqa: E402
    WINDOW_COMPLETE,
    absorb_candidate_predicate,
    aggregate_signed,
    assert_associativity,
    assert_bar_causality,
    assert_split_additive,
    assign_candidate_sessions,
    available_levels_for_candidates,
    design_gap_days,
    structural_levels_1m,
)
from xen.sigbar.sessions import (  # noqa: E402
    CANDIDATE_ANCHORS,
    OPERATIONAL_ANCHORS,
    anchor_table,
    ib_minutes_for_ltf,
    session_breaks,
)

RESULTS = Path(__file__).resolve().parents[1] / "results"
REGISTRY = ROOT / "experiments" / "INFR-018" / "results" / "instrument_registry.json"
BASELINES_PATH = ROOT / "experiments" / "INFR-017" / "results" / "seasonal_baselines.parquet"

# DESIGN-band sample for speed; --full uses all 194 fitted symbols for A1.
SAMPLE_SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "LTCUSDT",
    "CRVUSDT",
)

VT_WINDOW = datetime(2022, 7, 15, 13, 0, 0)
# Designer-derived VT-1..VT-3 (design §6 / agg_trace.json).
VT_EXPECTED: dict[int, dict[str, float]] = {
    5: {
        "Open": 20975.0,
        "High": 20999.0,
        "Low": 20970.0,
        "Close": 20970.5,
        "Volume": 718.345,
        "BuyVolume": 443.107,
        "SellVolume": 275.238,
        "Delta": 167.869,
    },
    15: {
        "Open": 20975.0,
        "High": 21094.5,
        "Low": 20945.0,
        "Close": 20947.5,
        "Volume": 4653.376,
        "BuyVolume": 2550.228,
        "SellVolume": 2103.148,
        "Delta": 447.080,
    },
    60: {
        "Open": 20975.0,
        "High": 21094.5,
        "Low": 20790.5,
        "Close": 20855.5,
        "Volume": 13447.757,
        "BuyVolume": 6786.452,
        "SellVolume": 6661.305,
        "Delta": 125.147,
    },
}


def _bar_metrics(bars: pl.DataFrame) -> pl.DataFrame:
    out = bars.with_columns(
        pl.col("Volume").alias("volume"),
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Delta").abs().alias("delta_abs"),
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("Delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )
    if "SpreadBps" in out.columns:
        out = out.with_columns(pl.col("SpreadBps").alias("spread"))
    return out


def _load_design_with_spread(symbol: str) -> pl.DataFrame:
    """DESIGN bars via fenced load, plus optional SpreadBps from staging for A1."""
    bars = load_bars(symbol, "DESIGN")
    path = repo_root() / "python/experiments/INFR-011/data/staging/bars" / f"{symbol}.parquet"
    # load_bars drops SpreadBps; re-attach if present for spread baseline A1.
    schema_names = pl.scan_parquet(path).collect_schema().names()
    if "SpreadBps" in schema_names and bars.height:
        sp = (
            pl.scan_parquet(path)
            .filter(
                (pl.col("OpenTime") >= bars["OpenTime"].min())
                & (pl.col("OpenTime") <= bars["OpenTime"].max())
            )
            .select(["OpenTime", "SpreadBps"])
            .collect()
        )
        bars = bars.join(sp, on="OpenTime", how="left")
    return _bar_metrics(bars)


def _value_equal(a: pl.DataFrame, b: pl.DataFrame, cols: list[str], *, tol: float = 0.0) -> list[str]:
    """Return list of mismatch descriptions (empty = match).

    Float columns are compared after casting both sides to Float32 — the frozen
    pin stores ``loc``/``scale`` as f32, so f64 refit noise is not a real
    generalisation drift.
    """
    errs: list[str] = []
    if a.height != b.height:
        return [f"height {a.height} != {b.height}"]
    joined = a.join(b, on=["mod", "dow"], how="inner", suffix="_pin")
    if joined.height != a.height:
        errs.append(f"key join lost rows: {joined.height} vs {a.height}")
    for c in cols:
        if c in ("sparse",):
            mism = joined.filter(pl.col(c) != pl.col(f"{c}_pin")).height
            if mism:
                errs.append(f"{c}: {mism} mismatches")
            continue
        if c == "n":
            mism = joined.filter(pl.col(c) != pl.col(f"{c}_pin")).height
            if mism:
                errs.append(f"{c}: {mism} mismatches")
            continue
        # float loc/scale — pin is f32; cast both for value-identity
        left = joined[c].cast(pl.Float32)
        right = joined[f"{c}_pin"].cast(pl.Float32)
        either_null = left.is_null() ^ right.is_null()
        if either_null.any():
            errs.append(f"{c}: null-pattern mismatch ({int(either_null.sum())} rows)")
            continue
        diff = (left - right).abs().fill_null(0.0)
        max_d = float(diff.max()) if diff.len() else 0.0
        if max_d > tol:
            errs.append(f"{c}: max abs diff {max_d} (after f32 cast)")
    return errs


def a1_a1b(symbols: list[str]) -> dict[str, Any]:
    """A1 value-identity + A1b generalised path (bar_minutes=1)."""
    frozen = pl.scan_parquet(BASELINES_PATH)
    # Prove A1b: call site always passes bar_minutes explicitly through the
    # generalised signature (no legacy branch).
    assert "bar_minutes" in fit_seasonal_baseline.__code__.co_varnames
    per_sym: dict[str, Any] = {}
    all_ok = True
    for sym in symbols:
        bars = _load_design_with_spread(sym)
        assert_design_only_fit(bars, context=f"A1:{sym}")
        pin = frozen.filter(pl.col("symbol") == sym).collect()
        if pin.height == 0:
            per_sym[sym] = {"ok": False, "error": "not in frozen baselines"}
            all_ok = False
            continue
        sym_ok = True
        metric_errs: dict[str, list[str]] = {}
        for metric in BASELINE_METRICS:
            if metric == "spread" and "spread" not in bars.columns:
                continue
            if metric not in bars.columns:
                continue
            fitted = fit_seasonal_baseline(bars, metric, bar_minutes=1)
            if fitted.height != FULL_GRID_CELLS:
                metric_errs[metric] = [f"grid height {fitted.height}"]
                sym_ok = False
                continue
            pin_m = pin.filter(pl.col("metric") == metric).select(
                ["mod", "dow", "loc", "scale", "n", "sparse"]
            )
            # Align dtypes for join
            fitted_c = fitted.select(["mod", "dow", "loc", "scale", "n", "sparse"]).with_columns(
                pl.col("mod").cast(pl.Int32),
                pl.col("dow").cast(pl.Int32),
            )
            pin_m = pin_m.with_columns(
                pl.col("mod").cast(pl.Int32),
                pl.col("dow").cast(pl.Int32),
            )
            errs = _value_equal(fitted_c, pin_m, ["loc", "scale", "n", "sparse"])
            if errs:
                metric_errs[metric] = errs
                sym_ok = False
        per_sym[sym] = {"ok": sym_ok, "metric_errors": metric_errs}
        all_ok = all_ok and sym_ok
    # Positive tests at each bar_minutes (A1b / QA T3)
    grid_ok = True
    grid_notes: dict[str, int] = {}
    for bm in (1, 5, 15, 60):
        n = full_grid_cells(bm)
        grid_notes[f"{bm}m"] = n
        sample = _load_design_with_spread("BTCUSDT")
        # For bm>1 use COMPLETE coarse bars
        if bm == 1:
            fit_df = sample
        else:
            gaps = design_gap_days(sample)
            fit_df = aggregate_signed(sample, bm, gap_days=gaps, complete_only=True)
            fit_df = _bar_metrics(fit_df)
        cells = fit_seasonal_baseline(fit_df, "volume", bar_minutes=bm)
        if cells.height != n:
            grid_ok = False
    return {
        "name": "A1/A1b",
        "ok": all_ok and grid_ok,
        "symbols": per_sym,
        "grid_cells": grid_notes,
        "grid_ok": grid_ok,
        "via_generalised_path": True,
    }


def a2(*, full: bool = False) -> dict[str, Any]:
    """A2: derive_thresholds on 1m reproduces the registry blocks on overlap.

    ``full=True`` traverses **all** pinned blocks (design A2); the sample path
    remains for fast local iteration only (QA-6 I-3).
    """
    reg = json.loads(REGISTRY.read_text())
    pinned = reg["class_thresholds"]["per_symbol_values"]
    if full:
        overlap = sorted(pinned.keys())
    else:
        overlap = [s for s in SAMPLE_SYMBOLS if s in pinned] or list(pinned.keys())[:5]
    metrics = ("volume", "range", "delta_abs", "delta_ratio")
    frozen = pl.scan_parquet(BASELINES_PATH)
    errs: dict[str, Any] = {}
    ok = True
    for sym in overlap:
        bars = _load_design_with_spread(sym)
        bl = frozen.filter(pl.col("symbol") == sym).collect()
        resid = bars
        for m in metrics:
            resid = residualise(resid, bl, m, bar_minutes=1)
        th = derive_thresholds(resid, metrics)
        pin = pinned[sym]
        for m in metrics:
            if m not in th or m not in pin:
                continue
            for k in ("high", "low", "n"):
                if abs(float(th[m][k]) - float(pin[m][k])) > 1e-6 * max(1.0, abs(float(pin[m][k]))):
                    # quantile float noise: allow slightly looser
                    if abs(float(th[m][k]) - float(pin[m][k])) > 1e-4:
                        errs.setdefault(sym, {}).setdefault(m, {})[k] = {
                            "got": th[m][k],
                            "pin": pin[m][k],
                        }
                        ok = False
            if "abs_high" in pin[m]:
                if abs(float(th[m]["abs_high"]) - float(pin[m]["abs_high"])) > 1e-4:
                    errs.setdefault(sym, {}).setdefault(m, {})["abs_high"] = {
                        "got": th[m]["abs_high"],
                        "pin": pin[m]["abs_high"],
                    }
                    ok = False
    # Estimator identity, tested rather than tautologically asserted (QA-6 I-7a):
    # a lookalike estimator (percentile shifted by one rank) must NOT reproduce
    # the pinned block, and the real one must.
    same_estimator = False
    if overlap:
        probe = overlap[0]
        bars = _load_design_with_spread(probe)
        bl = frozen.filter(pl.col("symbol") == probe).collect()
        resid = bars
        for m in metrics:
            resid = residualise(resid, bl, m, bar_minutes=1)
        real = derive_thresholds(resid, ("volume",))["volume"]["high"]
        lookalike = float(
            resid.select(pl.col("volume_resid").quantile(0.89)).item()
        )
        pin_v = float(pinned[probe]["volume"]["high"])
        same_estimator = (
            abs(real - pin_v) <= 1e-4 and abs(lookalike - pin_v) > 1e-4
        )
    return {
        "name": "A2",
        "ok": ok and same_estimator,
        "mode": "full" if full else "sample",
        "n_pinned_blocks": len(pinned),
        "n_checked": len(overlap),
        "checked_symbols": overlap if not full else f"all {len(overlap)}",
        "errors": errs,
        "estimator_discriminates_lookalike": same_estimator,
    }


def a3() -> dict[str, Any]:
    """A3: A-USOPEN L=15 session_breaks path unchanged; IB helper returns 15 at 1m."""
    bars = load_bars("BTCUSDT", "DESIGN")
    usopen = next(a for a in CANDIDATE_ANCHORS if a.anchor_id == "A-USOPEN")
    start, end = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = anchor_table(usopen, start, end)
    # Byte-stable path: same call as INFR-018
    ib = ib_minutes_for_ltf(1, wall_clock_minutes=15)
    if ib != 15:
        return {"name": "A3", "ok": False, "error": f"ib_minutes_for_ltf(1)={ib}"}
    breaks = session_breaks(bars, anchors, 15)
    # Golden IB: BTCUSDT session 2022-07-15 13:30Z — 20833.0 / 21020.5 / 187.5
    target = datetime(2022, 7, 15, 13, 30)
    row = breaks.filter(pl.col("anchor_ts") == target)
    golden_ok = False
    golden: dict[str, Any] = {}
    if row.height == 1:
        golden = {
            "ib_high": float(row["ib_high"][0]),
            "ib_low": float(row["ib_low"][0]),
            "ib_width": float(row["ib_width"][0]),
        }
        golden_ok = (
            abs(golden["ib_high"] - 21020.5) < 1e-9
            and abs(golden["ib_low"] - 20833.0) < 1e-9
            and abs(golden["ib_width"] - 187.5) < 1e-9
        )
    # Operational anchors present, no race machinery required
    h1 = next(a for a in OPERATIONAL_ANCHORS if a.anchor_id == "A-H1")
    h4 = next(a for a in OPERATIONAL_ANCHORS if a.anchor_id == "A-H4")
    return {
        "name": "A3",
        "ok": golden_ok and h1.sessions_per_day == 24 and h4.sessions_per_day == 6,
        "golden_ib": golden,
        "golden_ok": golden_ok,
        "n_sessions": breaks.height,
        "ib_helper_1m": ib,
    }


def a4_a5_vt() -> dict[str, Any]:
    """A4/A5/VT-1..3 on BTCUSDT 2022-07-15 13:00Z; A5 associativity; A5b note."""
    bars = load_bars("BTCUSDT", "DESIGN")
    gaps = design_gap_days(bars)
    vt: dict[str, Any] = {}
    ok = True
    for p, exp in VT_EXPECTED.items():
        agg = aggregate_signed(bars, p, gap_days=gaps, complete_only=False)
        assert_split_additive(agg)
        assert_bar_causality(agg, bars, p)  # full frame (vectorised, QA-6 I-2b)
        row = agg.filter(pl.col("OpenTime") == VT_WINDOW)
        if row.height != 1:
            vt[f"{p}m"] = {"ok": False, "error": "window missing"}
            ok = False
            continue
        r = row.to_dicts()[0]
        mismatches = {
            k: {"got": float(r[k]), "exp": v}
            for k, v in exp.items()
            if abs(float(r[k]) - v) > 1e-3  # staging float rounding
        }
        # tighter on OHLC
        for k in ("Open", "High", "Low", "Close"):
            if abs(float(r[k]) - exp[k]) > 1e-9:
                mismatches[k] = {"got": float(r[k]), "exp": exp[k]}
        split_gap = abs(float(r["BuyVolume"]) + float(r["SellVolume"]) - float(r["Volume"]))
        row_ok = not mismatches and r["SourceBars"] == p and split_gap < 1e-6
        vt[f"{p}m"] = {
            "ok": row_ok,
            "SourceBars": int(r["SourceBars"]),
            "window_class": r["window_class"],
            "split_gap": split_gap,
            "mismatches": mismatches,
        }
        ok = ok and row_ok

    # A5 associativity
    try:
        assert_associativity(bars, via=5, target=15, gap_days=gaps)
        assoc_ok = True
        assoc_err = None
    except Exception as e:  # noqa: BLE001 — battery records failure
        assoc_ok = False
        assoc_err = str(e)
        ok = False

    # A5b: the two window conventions (OpenTime group_by_dynamic vs the legacy
    # CloseTime-epoch bucketing) are *measured* against each other on the
    # overlapping windows, not merely characterised in prose (QA-6 I-7b).
    from xen.bar_aggregator import aggregate_ohlc

    legacy_in = bars.with_columns(
        pl.lit("BTCUSDT").alias("Symbol"),
        (pl.col("OpenTime") + pl.duration(minutes=1)).alias("CloseTime"),
    ).sort("CloseTime")
    legacy = aggregate_ohlc(legacy_in, 5)
    new5 = aggregate_signed(bars, 5, gap_days=gaps, complete_only=False)
    j = new5.join(
        legacy.select(
            pl.col("OpenTime"),
            pl.col("Open").alias("o2"),
            pl.col("High").alias("h2"),
            pl.col("Low").alias("l2"),
            pl.col("Close").alias("c2"),
        ),
        on="OpenTime",
        how="inner",
    )
    a5b_max = {
        a: float(j.select((pl.col(a) - pl.col(b)).abs().max()).item() or 0.0)
        for a, b in (("Open", "o2"), ("High", "h2"), ("Low", "l2"), ("Close", "c2"))
    }
    a5b_ok = bool(j.height) and max(a5b_max.values()) <= 1e-9
    if not a5b_ok:
        ok = False
    a5b = {
        "ok": a5b_ok,
        "n_joined_windows": j.height,
        "max_abs_diff": a5b_max,
        "ltf_convention": "group_by_dynamic(OpenTime, every=Nm, closed=left, label=left)",
        "legacy_convention": "bucket = (CloseTime.epoch_s - 1) // (N*60)",
    }
    return {
        "name": "A4/A5/VT",
        "ok": ok and assoc_ok,
        "vt": vt,
        "associativity_ok": assoc_ok,
        "associativity_error": assoc_err,
        "a5b": a5b,
    }


def a7_a8_a9_a10(symbols: list[str] | None = None) -> dict[str, Any]:
    """A7 outcome ban, A8 window integrity, A9 candidates, A10 null-scale cells."""
    symbols = list(symbols or SAMPLE_SYMBOLS[:3])
    # A7 schema
    try:
        check_no_outcome_columns(["OpenTime", "Volume", "volume_resid"], context="clean")
        a7_schema_ok = True
    except RuntimeError:
        a7_schema_ok = False
    planted_raised = False
    try:
        check_no_outcome_columns(["OpenTime", "fwd_return"], context="plant")
    except RuntimeError:
        planted_raised = True

    a8_ok = True
    a9_ok = True
    a10: dict[str, Any] = {}
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        gaps = design_gap_days(bars)
        for p in (5, 15, 60):
            agg = aggregate_signed(bars, p, gap_days=gaps, complete_only=False)
            # every bar carries classification
            need = {"window_class", "n_missing", "traded_fraction", "SourceBars"}
            if not need.issubset(agg.columns):
                a8_ok = False
            complete = agg.filter(pl.col("window_class") == WINDOW_COMPLETE)
            try:
                assert_windows_complete(complete, context=f"{sym}/{p}m")
                assert_no_forward_provenance(complete, period_minutes=p)
            except RuntimeError:
                a8_ok = False
            # non-complete must NOT pass assert_windows_complete
            partial = agg.filter(pl.col("window_class") != WINDOW_COMPLETE)
            if partial.height:
                try:
                    assert_windows_complete(partial, context="should_fail")
                    a8_ok = False  # failed to raise
                except RuntimeError:
                    pass
            # A10: null-scale cells after fit on COMPLETE only
            if complete.height:
                mdf = _bar_metrics(complete)
                cells = fit_seasonal_baseline(mdf, "range", bar_minutes=p)
                null_scale = int(cells.filter(pl.col("scale").is_null()).height)
                a10[f"{sym}/{p}m/range"] = {
                    "null_scale_cells": null_scale,
                    "total_cells": cells.height,
                }
            # A9: candidates from COMPLETE only, traded_fraction == 1
            if complete.height > 100:
                mdf = _bar_metrics(complete)
                # fit + residualise for volume/range
                for metric in ("volume", "range"):
                    bl = fit_seasonal_baseline(mdf, metric, bar_minutes=p)
                    mdf = residualise(mdf, bl, metric, bar_minutes=p)
                th = derive_thresholds(mdf, ("volume", "range"))
                cands = absorb_candidate_predicate(mdf, th)
                if cands.height and "traded_fraction" in cands.columns:
                    if float(cands["traded_fraction"].min()) < 1.0:
                        a9_ok = False

    # VT-4(i): provenance is traced from real frames, not a declared constant
    # (QA-6 I-2d). A level frame built on 1m must pass; the same level frame
    # stamped as 5m, and a 5-minute source series, must both raise.
    levels_ok = True
    bars_btc = load_bars("BTCUSDT", "DESIGN")
    gaps_btc = design_gap_days(bars_btc)
    usopen = next(a for a in CANDIDATE_ANCHORS if a.anchor_id == "A-USOPEN")
    anch = anchor_table(usopen, bars_btc["OpenTime"].min(), bars_btc["OpenTime"].max())
    lv = structural_levels_1m(bars_btc, anch.head(30), 15, include_profile=False)
    try:
        assert_levels_from_1m(lv, source_bars=bars_btc, context="A-levels")
    except RuntimeError:
        levels_ok = False
    # planted: level frame claiming an aggregated source
    try:
        assert_levels_from_1m(
            lv.with_columns(pl.lit(5).cast(pl.Int32).alias("level_source_bar_minutes"))
        )
        levels_ok = False
    except RuntimeError:
        pass
    # planted: an actually-5-minute source series
    agg5 = aggregate_signed(bars_btc, 5, gap_days=gaps_btc, complete_only=True)
    try:
        assert_levels_from_1m(source_bars=agg5, context="planted-5m")
        levels_ok = False
    except RuntimeError:
        pass
    # planted: structural_levels_1m itself must refuse an aggregated source
    try:
        structural_levels_1m(agg5, anch.head(30), 15, include_profile=False)
        levels_ok = False
    except RuntimeError:
        pass

    return {
        "name": "A7-A10",
        "ok": a7_schema_ok and planted_raised and a8_ok and a9_ok and levels_ok,
        "a7_schema_ok": a7_schema_ok,
        "a7_planted_raises": planted_raised,
        "a8_ok": a8_ok,
        "a9_ok": a9_ok,
        "a10_null_scale": a10,
        "levels_from_1m_ok": levels_ok,
    }


def accounting_check() -> dict[str, Any]:
    rep = check_no_local_accounting(Path(__file__).resolve().parent)
    return {"name": "check_no_local_accounting", "ok": rep["ok"], "detail": rep}


def a11_d4_prior_level_provenance() -> dict[str, Any]:
    """QA-9 R9-1: a D4 straddling bar cannot consume levels it helped form."""
    event_open = datetime(2022, 10, 10, 13, 0)
    bars = load_bars("GMXUSDT", "DESIGN")
    agg = aggregate_signed(
        bars,
        60,
        gap_days=design_gap_days(bars),
        complete_only=True,
    )
    cand = agg.filter(pl.col("OpenTime") == event_open)
    usopen = next(a for a in CANDIDATE_ANCHORS if a.anchor_id == "A-USOPEN")
    anchors = anchor_table(usopen, bars["OpenTime"].min(), bars["OpenTime"].max())
    cand_sessions = assign_candidate_sessions(cand, anchors, ltf_minutes=60)
    levels = structural_levels_1m(
        bars,
        anchors,
        60,
        only_anchors=set(cand_sessions["anchor_ts"].to_list()),
        include_profile=True,
    )
    pairs = available_levels_for_candidates(cand_sessions, levels)

    prior = pairs.filter(pl.col("level_kind").str.starts_with("PRIOR_"))
    profile = prior.filter(pl.col("level_kind").is_in(["PRIOR_POC", "PRIOR_VAH", "PRIOR_VAL"]))
    high = prior.filter(pl.col("level_kind") == "PRIOR_SESSION_HIGH")
    low = prior.filter(pl.col("level_kind") == "PRIOR_SESSION_LOW")
    all_stamped = levels.height == 7 and levels["formed_ts"].null_count() == 0
    profile_excluded = profile.height == 3 and profile["excluded_self_made"].all()
    high_excluded = high.height == 1 and bool(high["excluded_self_made"].item())
    low_available = low.height == 1 and bool(low["level_available"].item())

    # Missing provenance must fail closed; treating null/missing as "old" is
    # the exact class of defect this regression exists to prevent.
    missing_raises = False
    try:
        available_levels_for_candidates(cand_sessions, levels.drop("formed_ts"))
    except RuntimeError:
        missing_raises = True

    return {
        "name": "A11_D4_prior_level_provenance",
        "ok": bool(
            cand_sessions.height == 1
            and cand_sessions["straddles_anchor"].item()
            and all_stamped
            and profile_excluded
            and high_excluded
            and low_available
            and missing_raises
        ),
        "symbol": "GMXUSDT",
        "event_open": str(event_open),
        "anchor_ts": str(cand_sessions["anchor_ts"].item()),
        "all_seven_levels_stamped": all_stamped,
        "profile_levels_excluded": profile_excluded,
        "prior_high_excluded": high_excluded,
        "prior_low_available": low_available,
        "missing_formed_ts_raises": missing_raises,
    }


def run_battery(*, full: bool = False, out_dir: Path | None = None) -> dict[str, Any]:
    """Run A1–A11. ``out_dir`` overrides the artifact directory so a sample run
    cannot overwrite the pinned ``results/reproduction_battery.json`` (QA-7 I7-5a)."""
    results_dir = Path(out_dir) if out_dir else RESULTS
    root = repo_root()
    results_dir.mkdir(parents=True, exist_ok=True)
    frozen = assert_frozen_inputs(root)
    if frozen.baselines_sha256 != BASELINES_SHA256:
        raise RuntimeError("frozen baseline hash mismatch at battery entry")

    if full:
        symbols = sorted(
            pl.scan_parquet(BASELINES_PATH).select("symbol").unique().collect()["symbol"].to_list()
        )
    else:
        symbols = list(SAMPLE_SYMBOLS)

    results: list[dict[str, Any]] = []
    results.append(a1_a1b(symbols if full else list(SAMPLE_SYMBOLS)))
    results.append(a2(full=full))
    results.append(a3())
    results.append(a4_a5_vt())
    results.append(a7_a8_a9_a10(list(SAMPLE_SYMBOLS[:3])))
    results.append(a11_d4_prior_level_provenance())
    results.append(accounting_check())

    report = {
        "item": "INFR-020",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "full" if full else "sample",
        "symbols": symbols if full else list(SAMPLE_SYMBOLS),
        "frozen_baselines_sha256": frozen.baselines_sha256,
        "results": results,
        "all_ok": all(r.get("ok") for r in results),
    }
    out_path = results_dir / "reproduction_battery.json"
    # Same key check the runner applies to every other artifact (QA-7 I7-7).
    keys: set[str] = set()

    def _walk(o: Any) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                keys.add(str(k))
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)

    _walk(report)
    check_no_outcome_columns(keys, context="artifact:reproduction_battery")
    out_path.write_text(json.dumps(report, indent=2, default=str))
    report["path"] = str(out_path)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--full",
        action="store_true",
        help="run the full A1–A11 battery over all 194 fitted instruments (slow)",
    )
    ap.add_argument("--out-dir", default=None, help="artifact directory (default results/)")
    args = ap.parse_args()
    report = run_battery(full=args.full, out_dir=Path(args.out_dir) if args.out_dir else None)
    print(json.dumps({k: report[k] for k in ("mode", "all_ok", "path")}, indent=2))
    for r in report["results"]:
        status = "PASS" if r.get("ok") else "FAIL"
        print(f"  [{status}] {r.get('name')}")
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
