"""INFR-020 Stage-I multi-timeframe apparatus runner (design §7 execution order).

Strict order:
  frozen hashes → A1/A1b/A2/A3 → W2a classify → W2b agg → W1 baselines 5m/15m/1h
  → W3 thresholds → W4 sessions → A7–A10 → W5 census stubs → coverage → pins.json

Default is a DESIGN-band liquid sample for speed; ``--full`` walks all 194.
Does **not** emit a competing 1m baseline (INFR-017 remains the sole 1m pin).

Usage::

    python/.venv/bin/python python/experiments/INFR-020/code/run_apparatus.py
    python/.venv/bin/python python/experiments/INFR-020/code/run_apparatus.py --full
    python/.venv/bin/python python/experiments/INFR-020/code/run_apparatus.py --skip-battery
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.sigbar.baselines import fit_seasonal_baseline, residualise  # noqa: E402
from xen.sigbar.classes import derive_thresholds  # noqa: E402
from xen.sigbar.fences import (  # noqa: E402
    assert_design_only_fit,
    assert_frozen_inputs,
    assert_levels_from_1m,
    assert_no_forward_provenance,
    check_no_outcome_columns,
    load_bars,
    repo_root,
    sha256_file,
)
from xen.sigbar.fences import band_window  # noqa: E402
from xen.sigbar.ltf import (  # noqa: E402
    WINDOW_COMPLETE,
    absorb_candidate_predicate,
    aggregate_signed,
    assert_bar_causality,
    assert_split_additive,
    assert_windows_complete,
    assign_candidate_sessions,
    available_levels_for_candidates,
    design_gap_days,
    gap_excision_spans,
    prior_htf_session_ranges,
    session_ib_from_1m,
    structural_levels_1m,
)
from xen.sigbar.sessions import (  # noqa: E402
    CANDIDATE_ANCHORS,
    OPERATIONAL_ANCHORS,
    anchor_table,
    ib_minutes_for_ltf,
    operational_anchor,
)

from reproduction_battery import SAMPLE_SYMBOLS, run_battery  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
BASELINES_PATH = ROOT / "experiments" / "INFR-017" / "results" / "seasonal_baselines.parquet"
LTF_PERIODS = (5, 15, 60)
FIT_METRICS = ("volume", "range", "delta_abs", "delta_ratio")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bar_metrics(bars: pl.DataFrame) -> pl.DataFrame:
    return bars.with_columns(
        pl.col("Volume").alias("volume"),
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Delta").abs().alias("delta_abs"),
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("Delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )


def _symbols(full: bool) -> list[str]:
    if full:
        return sorted(
            pl.scan_parquet(BASELINES_PATH).select("symbol").unique().collect()["symbol"].to_list()
        )
    return list(SAMPLE_SYMBOLS)


def _ledger_error_days() -> dict[str, int]:
    """``unresolved_error_days`` per symbol from the INFR-011 admission ledger."""
    out: dict[str, int] = {}
    path = repo_root() / "python/experiments/INFR-011/artifacts/admission-ledger.jsonl"
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            sym = rec.get("symbol")
            if sym:
                out[sym] = int(rec.get("unresolved_error_days") or 0)
    return out


def w2_aggregate_and_classify(symbols: list[str]) -> dict[str, Any]:
    """W2a classify + W2b aggregation; emit gap excision + class counts."""
    gap_report: dict[str, Any] = {}
    class_counts: dict[str, Any] = {}
    ledger = _ledger_error_days()
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        assert_design_only_fit(bars, context=f"W2:{sym}")
        gaps = design_gap_days(bars)
        led = ledger.get(sym)
        gap_report[sym] = {
            "n_gap_days": len(gaps),
            "spans": gap_excision_spans(gaps),
            "gap_days": sorted(str(d) for d in gaps),
            # Ledger reconciliation (design §2 W2a; QA-6 I-9c). The ledger is a
            # whole-archive object and carries no gap timestamps, so it can
            # neither confirm nor produce the in-band day-holes — both
            # directions of disagreement are named rather than netted out.
            "ledger_unresolved_error_days": led,
            "ledger_miss": bool(len(gaps) > 0 and (led or 0) == 0),
            "ledger_only": bool(len(gaps) == 0 and (led or 0) > 0),
        }
        class_counts[sym] = {}
        for p in LTF_PERIODS:
            agg = aggregate_signed(bars, p, gap_days=gaps, complete_only=False)
            check_no_outcome_columns(agg, context=f"{sym}/{p}m")
            # HARD integrity asserts on the production path (QA-6 I-2)
            assert_split_additive(agg)
            assert_bar_causality(agg, bars, p)
            assert_no_forward_provenance(agg, period_minutes=p)
            vc = (
                agg.group_by("window_class")
                .len()
                .to_dicts()
                if agg.height
                else []
            )
            class_counts[sym][f"{p}m"] = {
                "n_windows": agg.height,
                "by_class": {r["window_class"]: r["len"] for r in vc},
                "n_complete": int(
                    agg.filter(pl.col("window_class") == WINDOW_COMPLETE).height
                )
                if agg.height
                else 0,
            }
    return {"gap_excision": gap_report, "class_counts": class_counts}


def w1_baselines(symbols: list[str]) -> pl.DataFrame:
    """Fit 5m/15m/1h seasonal baselines on COMPLETE windows only. No 1m emit."""
    frames: list[pl.DataFrame] = []
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        gaps = design_gap_days(bars)
        for p in LTF_PERIODS:
            complete = aggregate_signed(bars, p, gap_days=gaps, complete_only=True)
            if complete.height == 0:
                continue
            assert_windows_complete(complete, context=f"W1:{sym}/{p}m")
            assert_no_forward_provenance(complete, period_minutes=p)
            mdf = _bar_metrics(complete)
            assert_design_only_fit(mdf, context=f"W1:{sym}/{p}m")
            for metric in FIT_METRICS:
                cells = fit_seasonal_baseline(mdf, metric, bar_minutes=p)
                frames.append(
                    cells.with_columns(
                        pl.lit(sym).alias("symbol"),
                        pl.lit(p).alias("bar_minutes"),
                    )
                )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical")


def w3_thresholds(symbols: list[str], baselines: pl.DataFrame) -> dict[str, Any]:
    """Per (symbol, timeframe) class thresholds via unmodified derive_thresholds."""
    out: dict[str, Any] = {"percentile_levels": {"high": 0.9, "low": 0.1}, "per_symbol_tf": {}}
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        gaps = design_gap_days(bars)
        out["per_symbol_tf"][sym] = {}
        for p in LTF_PERIODS:
            complete = aggregate_signed(bars, p, gap_days=gaps, complete_only=True)
            if complete.height == 0:
                continue
            assert_windows_complete(complete, context=f"W3:{sym}/{p}m")
            mdf = _bar_metrics(complete)
            bl = baselines.filter(
                (pl.col("symbol") == sym) & (pl.col("bar_minutes") == p)
            )
            if bl.height == 0:
                continue
            resid = mdf
            for metric in FIT_METRICS:
                resid = residualise(resid, bl, metric, bar_minutes=p)
            th = derive_thresholds(resid, FIT_METRICS)
            out["per_symbol_tf"][sym][f"{p}m"] = th
    return out


def w3b_thresholds_1m(symbols: list[str]) -> dict[str, Any]:
    """1-minute class thresholds for the whole universe, emitted and pinned.

    D1's candidate population is a 1-minute one, so SPDR-009 cannot rebuild it
    from the 5/15/60m artifact. The 137 instruments in the INFR-018 registry
    have a pinned block; the other 57 had none, which left D1 irreproducible
    (QA-6 I-5). Residuals are taken against the frozen INFR-017 1m baseline —
    no competing 1m baseline is fitted.

    Where a symbol overlaps the frozen registry, the derived block must
    reproduce it value-identically; a mismatch raises.
    """
    reg_path = ROOT / "experiments" / "INFR-018" / "results" / "instrument_registry.json"
    pinned = json.loads(reg_path.read_text())["class_thresholds"]["per_symbol_values"]
    frozen = pl.scan_parquet(BASELINES_PATH)
    out: dict[str, Any] = {
        "bar_minutes": 1,
        "band": "DESIGN",
        "baseline_source": "INFR-017 frozen 1m pin (no re-fit)",
        "percentile_levels": {"high": 0.9, "low": 0.1},
        "registry_overlap_checked": [],
        "per_symbol": {},
    }
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        if bars.height == 0:
            continue
        assert_design_only_fit(bars, context=f"W3b:{sym}")
        bl = frozen.filter(pl.col("symbol") == sym).collect()
        if bl.height == 0:
            out["per_symbol"][sym] = {"note": "no frozen 1m baseline for symbol"}
            continue
        mdf = _bar_metrics(bars)
        for metric in FIT_METRICS:
            mdf = residualise(mdf, bl, metric, bar_minutes=1)
        th = derive_thresholds(mdf, FIT_METRICS)
        out["per_symbol"][sym] = th
        if sym in pinned:
            for m in FIT_METRICS:
                if m not in th or m not in pinned[sym]:
                    continue
                for k in ("high", "low", "n"):
                    if k not in pinned[sym][m] or k not in th[m]:
                        continue
                    got, pin_v = float(th[m][k]), float(pinned[sym][m][k])
                    if abs(got - pin_v) > 1e-4:
                        raise RuntimeError(
                            f"W3b 1m threshold drift {sym}/{m}/{k}: {got} vs pinned {pin_v}"
                        )
            out["registry_overlap_checked"].append(sym)
    out["n_symbols"] = len(out["per_symbol"])
    out["n_registry_overlap"] = len(out["registry_overlap_checked"])
    return out


def w4_sessions(symbols: list[str]) -> dict[str, Any]:
    """Operational A-H1/A-H4 anchor tables + IB rule disclosure (no excursion outcomes)."""
    ib_rule = {
        "wall_clock_minutes": 15,
        "by_ltf": {
            "1m": ib_minutes_for_ltf(1),
            "5m": ib_minutes_for_ltf(5),
            "15m": ib_minutes_for_ltf(15),
            "60m": ib_minutes_for_ltf(60),
        },
        "note": (
            "IB share-of-session varies 1%→25% across D1–D2; not cross-pair comparable. "
            "D4 IB is 60 min (min one LTF bar)."
        ),
        "edge_bearing": False,
        "race_run": False,
    }
    anchors_out: dict[str, Any] = {}
    # Materialise one day of anchor stamps as a schema pin (not full history).
    day0 = datetime(2022, 7, 15)
    day1 = datetime(2022, 7, 16)
    for spec in OPERATIONAL_ANCHORS:
        tbl = anchor_table(spec, day0, day1)
        anchors_out[spec.anchor_id] = {
            "sessions_per_day": spec.sessions_per_day,
            "minutes_of_day": list(spec.minutes_of_day or ()),
            "sample_day_anchors": [str(t) for t in tbl["anchor_ts"].to_list()],
        }
    check_no_outcome_columns(
        ["anchor_ts", "session_end", "ib_high", "ib_low", "ib_width"],
        context="W4 schema",
    )
    return {
        "ib_rule": ib_rule,
        "operational_anchors": anchors_out,
        "symbols_framed": symbols,
    }


# Pair → (HTF anchor id, LTF bar minutes, HTF session length minutes for framing)
# D1/D4 use frozen A-USOPEN; D2 A-H1; D3 A-H4. Levels always from 1m bars.
_PAIR_SPEC: dict[str, dict[str, Any]] = {
    "D1_1d/1m": {"anchor": "A-USOPEN", "ltf": 1, "ib_wall": 15},
    "D2_1h/5m": {"anchor": "A-H1", "ltf": 5, "ib_wall": 15},
    "D3_4h/15m": {"anchor": "A-H4", "ltf": 15, "ib_wall": 15},
    "D4_1d/1h": {"anchor": "A-USOPEN", "ltf": 60, "ib_wall": 60},  # D4 IB DEVIATES
}

_CENSUS_COUNT_KEYS = {
    "n_candidates",
    "n_candidates_pre_ib",
    "n_ib_edge_unavailable",
    "n_ib_edge_self_made_excluded",
    "n_prior_level_self_made_excluded",
    "n_self_made_level_excluded",
    "n_candidates_no_levels",
    "n_candidates_straddling_anchor",
    "n_candidates_measured",
    "n_candidates_unanchored",
}


def _anchor_spec(anchor_id: str):
    if anchor_id == "A-USOPEN":
        return next(a for a in CANDIDATE_ANCHORS if a.anchor_id == "A-USOPEN")
    return operational_anchor(anchor_id)


def _quantile_dict(vals: list[float]) -> dict[str, float | None]:
    if not vals:
        return {"n": 0, "p10": None, "p25": None, "p50": None, "p75": None, "p90": None}
    s = pl.Series(vals)
    return {
        "n": len(vals),
        "p10": float(s.quantile(0.10)),
        "p25": float(s.quantile(0.25)),
        "p50": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
    }


def _unmeasurable_census_entry(
    n_complete: int,
    range_price: list[float],
    range_bps: list[float],
    note: str,
    **extra: Any,
) -> dict[str, Any]:
    """Emit an unmeasurable W5 cell with the complete count schema."""
    return {
        "measurable": False,
        "n_complete": n_complete,
        "n_candidates": 0,
        "n_candidates_pre_ib": 0,
        "n_ib_edge_unavailable": 0,
        "n_ib_edge_self_made_excluded": 0,
        "n_prior_level_self_made_excluded": 0,
        "n_self_made_level_excluded": 0,
        "n_candidates_no_levels": 0,
        "n_candidates_straddling_anchor": 0,
        "n_candidates_measured": 0,
        "n_candidates_unanchored": 0,
        "prior_session_range_price": _quantile_dict(range_price),
        "prior_session_range_bps": _quantile_dict(range_bps),
        "note": note,
        **extra,
    }


def _assert_census_schema(
    census: dict[str, Any],
    d1_ibwidth: dict[str, Any],
    symbols: list[str],
) -> None:
    """Refuse incomplete/misleading W5 census schemas before artifact writes."""
    errors: list[str] = []
    pairs = census.get("pairs") or {}
    d1_symbols = d1_ibwidth.get("symbols") or {}
    for sym in symbols:
        sym_pairs = pairs.get(sym) or {}
        for pair_name in _PAIR_SPEC:
            entry = sym_pairs.get(pair_name)
            if not isinstance(entry, dict):
                errors.append(f"{sym}/{pair_name}: missing cell")
                continue
            missing = sorted(_CENSUS_COUNT_KEYS - set(entry))
            if missing:
                errors.append(f"{sym}/{pair_name}: missing count keys {missing}")
                continue
            if entry.get("measurable") is False and any(
                int(entry[k]) != 0 for k in _CENSUS_COUNT_KEYS
            ):
                errors.append(f"{sym}/{pair_name}: unmeasurable cell has non-zero counts")
            if int(entry["n_candidates"]) != (
                int(entry["n_candidates_measured"])
                + int(entry["n_candidates_no_levels"])
                + int(entry["n_candidates_unanchored"])
            ):
                errors.append(f"{sym}/{pair_name}: candidate identity failed")

        d1 = d1_symbols.get(sym)
        if not isinstance(d1, dict):
            errors.append(f"{sym}/D1-sensitivity: missing cell")
            continue
        missing = sorted(_CENSUS_COUNT_KEYS - set(d1))
        if missing:
            errors.append(f"{sym}/D1-sensitivity: missing count keys {missing}")
        if "measurable" not in d1:
            errors.append(f"{sym}/D1-sensitivity: missing measurable flag")
        if d1.get("measurable") is False and any(
            int(d1.get(k, 0)) != 0 for k in _CENSUS_COUNT_KEYS
        ):
            errors.append(f"{sym}/D1-sensitivity: unmeasurable cell has non-zero counts")
        if int(d1.get("n_candidates", 0)) != (
            int(d1.get("n_candidates_measured", 0))
            + int(d1.get("n_candidates_no_levels", 0))
            + int(d1.get("n_candidates_unanchored", 0))
        ):
            errors.append(f"{sym}/D1-sensitivity: candidate identity failed")

    if errors:
        raise RuntimeError(f"W5 census schema failed ({len(errors)}): {errors[:8]}")


def w5_zone_scale_census(
    symbols: list[str],
    thresholds: dict[str, Any],
    baselines: pl.DataFrame,
    thresholds_1m: dict[str, Any],
) -> dict[str, Any]:
    """W5 contact-zone scale census — DESIGN only, count-only (design §2 W5).

    Per (symbol, pair):
      - prior-HTF-session range distribution (price + bps of session mid)
      - candidate counts via shared ``absorb_candidate_predicate`` (COMPLETE only)
      - distance from each candidate close to nearest structural level, as a
        fraction of prior-session range (primary scale) — quantiles only
      - D1 sensitivity: same distances as a fraction of ``0.25 × ib_width``

    Levels and prior-session range are built from **1-minute** bars only (D6.3).
    No forward return, excursion, or outcome column is computed.

    **Level availability.** A level enters a candidate's set only once it is
    knowable and only when none of the candidate's own source minutes formed it.
    This applies to current-session IB edges and to prior-session levels when an
    LTF bar straddles the session anchor (QA-9 R9-1).
    """
    start, end = band_window("DESIGN")
    census: dict[str, Any] = {
        "band": "DESIGN",
        "level_source_bar_minutes": 1,
        "primary_scale": "prior_htf_session_range",
        "pairs": {},
    }
    d1_ibwidth: dict[str, Any] = {
        "band": "DESIGN",
        "scale": "0.25 * ib_width",
        "level_source_bar_minutes": 1,
        "symbols": {},
    }

    for i_sym, sym in enumerate(symbols):
        if (i_sym + 1) % 10 == 0 or i_sym == 0:
            print(f"  W5 {i_sym + 1}/{len(symbols)} {sym}", flush=True)
        bars = load_bars(sym, "DESIGN")
        if bars.height == 0:
            continue
        assert_design_only_fit(bars, context=f"W5:{sym}")
        gaps = design_gap_days(bars)
        census["pairs"][sym] = {}

        for pair_name, spec in _PAIR_SPEC.items():
            ltf = int(spec["ltf"])
            ib_mins = ib_minutes_for_ltf(ltf) if ltf > 1 else 15
            if pair_name == "D4_1d/1h":
                ib_mins = 60  # D4 deviation: min whole bar = 60 min
            elif pair_name == "D1_1d/1m":
                ib_mins = 15

            a_spec = _anchor_spec(spec["anchor"])
            anchors = anchor_table(a_spec, start, end)
            ranges = prior_htf_session_ranges(bars, anchors)
            ib = session_ib_from_1m(bars, anchors, ib_mins)
            n_ib_degenerate = (
                int(ib.filter(pl.col("ib_degenerate")).height) if ib.height else 0
            )
            if ib.height:
                ib = ib.filter(~pl.col("ib_degenerate"))

            # Prior-session range distribution (price + bps of mid) — all sessions
            range_price: list[float] = []
            range_bps: list[float] = []
            n_prior_missing = 0
            if ranges.height:
                for row in ranges.iter_rows(named=True):
                    pr_raw = row["prior_session_range"]
                    if pr_raw is None:
                        # calendar-adjacent predecessor traded nothing (I-6/I-9a)
                        n_prior_missing += 1
                        continue
                    pr = float(pr_raw)
                    mid = 0.5 * (
                        float(row["prior_session_high"]) + float(row["prior_session_low"])
                    )
                    if pr > 0 and mid > 0:
                        range_price.append(pr)
                        range_bps.append(1e4 * pr / mid)

            # Candidates first (COMPLETE LTF); then levels only for their sessions
            if ltf == 1:
                complete = bars.with_columns(
                    pl.lit(WINDOW_COMPLETE).alias("window_class"),
                    pl.lit(1.0).alias("traded_fraction"),
                    pl.lit(1).alias("SourceBars"),
                )
                mdf = _bar_metrics(complete)
                # Governing 1m pin (INFR-017) — do not re-fit competing baselines
                bl_1m = (
                    pl.scan_parquet(BASELINES_PATH)
                    .filter(pl.col("symbol") == sym)
                    .collect()
                )
                th_block = thresholds_1m.get("per_symbol", {}).get(sym) or {}
                if bl_1m.height == 0 or "volume" not in th_block:
                    census["pairs"][sym][pair_name] = _unmeasurable_census_entry(
                        complete.height,
                        range_price,
                        range_bps,
                        "no frozen 1m baseline or no pinned 1m threshold block",
                    )
                    continue
                for metric in FIT_METRICS:
                    mdf = residualise(mdf, bl_1m, metric, bar_minutes=1)
            else:
                th_block = (
                    thresholds.get("per_symbol_tf", {}).get(sym, {}).get(f"{ltf}m") or {}
                )
                complete = aggregate_signed(bars, ltf, gap_days=gaps, complete_only=True)
                if complete.height:
                    assert_windows_complete(complete, context=f"W5:{sym}/{pair_name}")
                    assert_no_forward_provenance(complete, period_minutes=ltf)
                if complete.height == 0 or not th_block:
                    census["pairs"][sym][pair_name] = _unmeasurable_census_entry(
                        complete.height if complete is not None else 0,
                        range_price,
                        range_bps,
                        "no complete bars or thresholds",
                    )
                    continue
                mdf = _bar_metrics(complete)
                bl_sym = baselines.filter(
                    (pl.col("symbol") == sym) & (pl.col("bar_minutes") == ltf)
                )
                if bl_sym.height == 0:
                    # A run-local baseline must never silently stand in for a
                    # pinned one — that substitution is how the contaminated
                    # 5-symbol run produced a plausible 194-symbol census
                    # (QA-7 I7-4). Declare the cell unmeasurable instead.
                    census["pairs"][sym][pair_name] = _unmeasurable_census_entry(
                        complete.height,
                        range_price,
                        range_bps,
                        f"no pinned {ltf}m baseline block for symbol (no run-local refit)",
                    )
                    continue
                for metric in FIT_METRICS:
                    mdf = residualise(mdf, bl_sym, metric, bar_minutes=ltf)

            if not th_block:
                census["pairs"][sym][pair_name] = _unmeasurable_census_entry(
                    complete.height,
                    range_price,
                    range_bps,
                    "no thresholds",
                )
                continue
            # Some thin names lack a usable range residual scale (null MAD → no
            # range cut). Absorption needs both volume.high and range.low.
            if (
                "volume" not in th_block
                or "range" not in th_block
                or "high" not in th_block.get("volume", {})
                or "low" not in th_block.get("range", {})
            ):
                # Not a measured zero — the absorption predicate needs both a
                # volume.high and a range.low cut, and this symbol has no usable
                # range residual scale (null MAD). QA-6 I-9f.
                census["pairs"][sym][pair_name] = _unmeasurable_census_entry(
                    complete.height,
                    range_price,
                    range_bps,
                    "incomplete thresholds (missing volume/range cuts)",
                    threshold_keys=list(th_block.keys()),
                )
                continue

            cands = absorb_candidate_predicate(mdf, th_block)
            dist_over_range: list[float] = []
            dist_over_ib025: list[float] = []
            levels = pl.DataFrame()
            n_pre_ib = 0
            n_ib_edge_unavailable = 0
            n_ib_self_made = 0
            n_prior_self_made = 0
            n_any_self_made = 0
            n_measured = 0
            n_no_levels = 0
            n_unanchored = 0
            n_straddling = 0
            if cands.height:
                # Conditioning happens at the candidate's CLOSE, so the session
                # it belongs to is the one holding its LAST source minute, and a
                # level is available if it is knowable at that close (QA-7 I7-1).
                # D4 does not nest — A-USOPEN anchors at 13:30 while D4 bars open
                # on the hour — so an OpenTime-based test asks the question 30
                # minutes early and refuses events whose IB has long completed.
                cand_joined = assign_candidate_sessions(cands, anchors, ltf_minutes=ltf)
                if cand_joined.height == 0:
                    cand_joined = cands.clear()
                n_unanchored = cands.height - cand_joined.height
                n_straddling = (
                    int(cand_joined.filter(pl.col("straddles_anchor")).height)
                    if cand_joined.height
                    else 0
                )
                only = set(cand_joined["anchor_ts"].unique().to_list())
                # Profile only sessions that host candidates (full seven-kind set)
                levels = structural_levels_1m(
                    bars, anchors, ib_mins, only_anchors=only, include_profile=True
                )
                # Provenance traced from the emitted frame + its source series,
                # not from a declared constant (QA-6 I-2).
                assert_levels_from_1m(
                    levels if levels.height else None,
                    source_bars=bars,
                    context=f"W5:{sym}/{pair_name}",
                )
                range_by_anchor: dict[Any, float] = {}
                ib_by_anchor: dict[Any, float] = {}
                if levels.height:
                    for row in levels.select(
                        "anchor_ts",
                        *(
                            c
                            for c in ("prior_session_range", "ib_width")
                            if c in levels.columns
                        ),
                    ).unique().iter_rows(named=True):
                        a = row["anchor_ts"]
                        if row.get("prior_session_range") is not None:
                            range_by_anchor[a] = float(row["prior_session_range"])
                        if row.get("ib_width") is not None:
                            ib_by_anchor[a] = float(row["ib_width"])
                # fill scale maps from ranges/ib tables when level join missed
                if ranges.height:
                    for row in ranges.filter(
                        pl.col("anchor_ts").is_in(list(only))
                    ).iter_rows(named=True):
                        if row["prior_session_range"] is None:
                            continue
                        range_by_anchor.setdefault(
                            row["anchor_ts"], float(row["prior_session_range"])
                        )
                if ib.height:
                    for row in ib.filter(
                        pl.col("anchor_ts").is_in(list(only))
                    ).iter_rows(named=True):
                        ib_by_anchor.setdefault(row["anchor_ts"], float(row["ib_width"]))

                # One shared availability rule (xen.sigbar.ltf), the same object
                # SPDR-009 imports — no retyped copy here (QA-8 I8-2). The bar
                # survives; only levels it cannot know are dropped from its set.
                pairs_lv = available_levels_for_candidates(cand_joined, levels)
                if pairs_lv.height:
                    per_cand = pairs_lv.group_by("OpenTime").agg(
                        pl.col("anchor_ts").first(),
                        pl.col("mins_since_close").first(),
                        pl.col("level_distance").filter(pl.col("level_available")).min().alias("d"),
                        # disclosure: would the nearest level over the FULL set
                        # have been an IB edge this bar cannot yet use?
                        pl.col("is_ib_edge")
                        .sort_by("level_distance")
                        .first()
                        .alias("nearest_all_is_ib"),
                        pl.col("level_available").any().alias("any_available"),
                        pl.col("excluded_self_made").any().alias("any_self_made"),
                        (pl.col("excluded_self_made") & pl.col("is_ib_edge"))
                        .any()
                        .alias("ib_self_made"),
                        (pl.col("excluded_self_made") & ~pl.col("is_ib_edge"))
                        .any()
                        .alias("prior_self_made"),
                    )
                    for row in per_cand.iter_rows(named=True):
                        a = row["anchor_ts"]
                        pre_ib = int(row["mins_since_close"]) < ib_mins
                        if pre_ib:
                            n_pre_ib += 1
                        if row["any_self_made"]:
                            n_any_self_made += 1
                        if row["ib_self_made"]:
                            n_ib_self_made += 1
                        if row["prior_self_made"]:
                            n_prior_self_made += 1
                        if row["d"] is None or not row["any_available"]:
                            n_no_levels += 1
                            continue
                        if pre_ib and row["nearest_all_is_ib"]:
                            n_ib_edge_unavailable += 1
                        d = float(row["d"])
                        n_measured += 1
                        pr = range_by_anchor.get(a)
                        if pr and pr > 0:
                            dist_over_range.append(d / pr)
                        ibw = ib_by_anchor.get(a)
                        if ibw and ibw > 0:
                            dist_over_ib025.append(d / (0.25 * ibw))
                    n_no_levels += cand_joined.height - per_cand.height
                else:
                    n_no_levels += cand_joined.height

            if cands.height != n_measured + n_no_levels + n_unanchored:
                raise RuntimeError(
                    f"W5 candidate count identity failed for {sym}/{pair_name}: "
                    f"{cands.height} != {n_measured} + {n_no_levels} + {n_unanchored}"
                )

            entry = {
                "measurable": True,
                "anchor": spec["anchor"],
                "ltf_minutes": ltf,
                "ib_minutes": ib_mins,
                "n_complete": complete.height,
                "n_candidates": cands.height,
                "n_candidates_pre_ib": n_pre_ib,
                "n_ib_edge_unavailable": n_ib_edge_unavailable,
                "n_ib_edge_self_made_excluded": n_ib_self_made,
                "n_prior_level_self_made_excluded": n_prior_self_made,
                "n_self_made_level_excluded": n_any_self_made,
                "n_candidates_no_levels": n_no_levels,
                "n_candidates_straddling_anchor": n_straddling,
                "n_candidates_measured": n_measured,
                # identity: candidates == measured + no_levels + unanchored
                "n_candidates_unanchored": n_unanchored,
                "min_traded_fraction": (
                    float(cands["traded_fraction"].min())
                    if cands.height and "traded_fraction" in cands.columns
                    else None
                ),
                "prior_session_range_price": _quantile_dict(range_price),
                "prior_session_range_bps": _quantile_dict(range_bps),
                "dist_over_prior_session_range": _quantile_dict(dist_over_range),
                "n_sessions_with_range": len(range_price),
                "n_sessions_prior_missing": n_prior_missing,
                "n_sessions_ib_degenerate": n_ib_degenerate,
                "n_level_rows": levels.height if isinstance(levels, pl.DataFrame) else 0,
            }
            census["pairs"][sym][pair_name] = entry

            if pair_name == "D1_1d/1m":
                d1_ibwidth["symbols"][sym] = {
                    "measurable": True,
                    "n_candidates": cands.height,
                    "n_candidates_pre_ib": n_pre_ib,
                    "n_ib_edge_unavailable": n_ib_edge_unavailable,
                    "n_ib_edge_self_made_excluded": n_ib_self_made,
                    "n_prior_level_self_made_excluded": n_prior_self_made,
                    "n_self_made_level_excluded": n_any_self_made,
                    "n_candidates_no_levels": n_no_levels,
                    "n_candidates_straddling_anchor": n_straddling,
                    "n_candidates_measured": n_measured,
                    "n_candidates_unanchored": n_unanchored,
                    "dist_over_0.25_ib_width": _quantile_dict(dist_over_ib025),
                    "ib_width_price": _quantile_dict(
                        [float(x) for x in ib["ib_width"].to_list()] if ib.height else []
                    ),
                    "level_source_bar_minutes": 1,
                }

        if sym not in d1_ibwidth["symbols"]:
            primary_d1 = census.get("pairs", {}).get(sym, {}).get("D1_1d/1m", {})
            d1_ibwidth["symbols"][sym] = {
                "measurable": False,
                "note": primary_d1.get("note", "D1 sensitivity unavailable"),
                "n_candidates": 0,
                "n_candidates_pre_ib": 0,
                "n_ib_edge_unavailable": 0,
                "n_ib_edge_self_made_excluded": 0,
                "n_prior_level_self_made_excluded": 0,
                "n_self_made_level_excluded": 0,
                "n_candidates_no_levels": 0,
                "n_candidates_straddling_anchor": 0,
                "n_candidates_measured": 0,
                "n_candidates_unanchored": 0,
                "dist_over_0.25_ib_width": _quantile_dict([]),
                "ib_width_price": _quantile_dict([]),
                "level_source_bar_minutes": 1,
            }

    _assert_census_schema(census, d1_ibwidth, symbols)
    return {"zone_scale_census": census, "zone_scale_census_d1_ibwidth": d1_ibwidth}

def coverage_report(symbols: list[str], class_counts: dict[str, Any]) -> dict[str, Any]:
    """Retention / sparse / activity disclosure (informative, not gating)."""
    rows: list[dict[str, Any]] = []
    for sym in symbols:
        bars = load_bars(sym, "DESIGN")
        gaps = design_gap_days(bars)
        row: dict[str, Any] = {
            "symbol": sym,
            "n_1m": bars.height,
            "gap_days": len(gaps),
            "periods": {},
        }
        for p in LTF_PERIODS:
            agg = aggregate_signed(bars, p, gap_days=gaps, complete_only=False)
            n = agg.height
            n_c = int(agg.filter(pl.col("window_class") == WINDOW_COMPLETE).height) if n else 0
            partial = agg.filter(pl.col("window_class") != WINDOW_COMPLETE)
            complete = agg.filter(pl.col("window_class") == WINDOW_COMPLETE)
            med_c = float(complete["Volume"].median()) if complete.height else None
            med_p = float(partial["Volume"].median()) if partial.height else None
            ratio = (med_c / med_p) if (med_c and med_p and med_p > 0) else None
            # sparse rate on COMPLETE fit
            sparse_rate = None
            null_scale_range = None
            null_scale_volume = None
            if complete.height:
                mdf = _bar_metrics(complete)
                cells = fit_seasonal_baseline(mdf, "volume", bar_minutes=p)
                sparse_rate = float(cells["sparse"].mean())
                null_scale_volume = int(cells.filter(pl.col("scale").is_null()).height)
                rc = fit_seasonal_baseline(mdf, "range", bar_minutes=p)
                null_scale_range = int(rc.filter(pl.col("scale").is_null()).height)
            row["periods"][f"{p}m"] = {
                "n_windows": n,
                "n_complete": n_c,
                "retention": round(n_c / n, 4) if n else 0.0,
                "vol_ratio_complete_vs_partial": round(ratio, 2) if ratio is not None else None,
                "sparse_rate_volume": sparse_rate,
                "null_scale_range_cells": null_scale_range,
                "null_scale_volume_cells": null_scale_volume,
                "by_class": class_counts.get(sym, {}).get(f"{p}m", {}).get("by_class"),
            }
        # A10 on the 1m/D1 path too — this is where the one unmeasurable symbol
        # arose, and it was previously unreported (QA-6 I-9b). Read off the
        # frozen INFR-017 pin; no competing 1m fit.
        pin_1m = (
            pl.scan_parquet(BASELINES_PATH)
            .filter(pl.col("symbol") == sym)
            .select(["metric", "scale", "sparse"])
            .collect()
        )
        one_min: dict[str, Any] = {"in_frozen_pin": bool(pin_1m.height)}
        for metric in ("volume", "range"):
            m = pin_1m.filter(pl.col("metric") == metric)
            one_min[f"null_scale_{metric}_cells"] = (
                int(m.filter(pl.col("scale").is_null()).height) if m.height else None
            )
        one_min["sparse_rate_volume"] = (
            float(pin_1m.filter(pl.col("metric") == "volume")["sparse"].mean())
            if pin_1m.filter(pl.col("metric") == "volume").height
            else None
        )
        row["one_minute"] = one_min
        rows.append(row)
    return {
        "band": "DESIGN",
        "n_symbols": len(symbols),
        "retention_floor_predeclared": 0.50,
        "instruments": rows,
    }


def _json_keys(obj: Any, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(str(k))
            _json_keys(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _json_keys(v, out)


def emit_json(path: Path, obj: Any, *, context: str) -> str:
    """Write a JSON artifact after checking its own key vocabulary (QA-6 I-2c)."""
    keys: set[str] = set()
    _json_keys(obj, keys)
    check_no_outcome_columns(keys, context=f"artifact:{context}")
    path.write_text(json.dumps(obj, indent=2, default=str))
    return sha256_file(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full", action="store_true", help="all 194 A5 instruments")
    ap.add_argument("--skip-battery", action="store_true", help="skip A1–A11 preflight")
    ap.add_argument(
        "--from-w5",
        action="store_true",
        help="reuse on-disk W1–W4 artifacts; re-run W5 + coverage + pins only",
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help=(
            "artifact directory (default results/). Sample runs must use a "
            "separate directory: a 5-symbol run writing into results/ silently "
            "replaces the full-universe W1/W3 artifacts a later --from-w5 reuses."
        ),
    )
    args = ap.parse_args()

    global RESULTS
    if args.out_dir:
        RESULTS = Path(args.out_dir)
        if not RESULTS.is_absolute():
            RESULTS = Path(__file__).resolve().parents[1] / args.out_dir

    root = repo_root()
    RESULTS.mkdir(parents=True, exist_ok=True)

    # --- frozen inputs ---
    frozen = assert_frozen_inputs(root)
    pins: dict[str, Any] = {
        "item": "INFR-020",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_inputs": {
            "baselines_sha256": frozen.baselines_sha256,
            "column_pins_sha256": frozen.column_pins_sha256,
            "fence_manifest_sha256": frozen.fence_manifest_sha256,
        },
        "artifacts": {},
    }

    # --- battery first (design §7) ---
    if not args.skip_battery:
        battery = run_battery(full=bool(args.full), out_dir=RESULTS)
        if not battery["all_ok"]:
            print("BATTERY FAILED — refusing to emit downstream artifacts", file=sys.stderr)
            return 1
        pins["artifacts"]["reproduction_battery.json"] = sha256_file(
            RESULTS / "reproduction_battery.json"
        )

    symbols = _symbols(args.full)
    print(f"universe: {len(symbols)} symbols ({'full' if args.full else 'sample'})")

    bl_path = RESULTS / "seasonal_baselines_mtf.parquet"
    th_path = RESULTS / "class_thresholds_mtf.json"
    gap_path = RESULTS / "gap_excision_report.json"
    sess_path = RESULTS / "sessions_mtf.json"

    th1m_path = RESULTS / "class_thresholds_1m.json"

    # W2a/W2b always runs: it is where the production-path integrity asserts
    # live (split additivity, bar causality, forward provenance) and it feeds
    # both the gap report and coverage's class counts.
    print("W2 classify + aggregate (hard asserts on the emitting path) …")
    w2 = w2_aggregate_and_classify(symbols)
    pins["artifacts"]["gap_excision_report.json"] = emit_json(
        gap_path, w2["gap_excision"], context="gap_excision_report"
    )

    if args.from_w5:
        print("resuming from W5 — loading W1–W4 artifacts from disk")
        if not bl_path.exists() or not th_path.exists():
            raise RuntimeError("--from-w5 requires seasonal_baselines_mtf.parquet and class_thresholds_mtf.json")
        bl = pl.read_parquet(bl_path)
        th = json.loads(th_path.read_text())
        # Reused artifacts must actually cover this run's universe (QA-7 I7-5b):
        # a sample-scale W1/W3 silently reused by a full run is the contamination
        # path that produced a 5-symbol census labelled 194.
        bl_syms = set(bl["symbol"].unique().to_list()) if bl.height else set()
        th_syms = set((th.get("per_symbol_tf") or {}).keys())
        for name, have in (("seasonal_baselines_mtf", bl_syms), ("class_thresholds_mtf", th_syms)):
            missing = sorted(set(symbols) - have)
            if missing:
                raise RuntimeError(
                    f"--from-w5: on-disk {name} covers {len(have)} symbols and is missing "
                    f"{len(missing)} of this run's universe (first: {missing[:5]}) — "
                    "re-run the full pipeline instead of reusing a narrower artifact"
                )
        check_no_outcome_columns(bl, context="artifact:seasonal_baselines_mtf")
        pins["artifacts"]["seasonal_baselines_mtf.parquet"] = sha256_file(bl_path)
        pins["artifacts"]["class_thresholds_mtf.json"] = sha256_file(th_path)
        if sess_path.exists():
            pins["artifacts"]["sessions_mtf.json"] = sha256_file(sess_path)
        else:
            pins["artifacts"]["sessions_mtf.json"] = emit_json(
                sess_path, w4_sessions(symbols), context="sessions_mtf"
            )
    else:
        # --- W1 ---
        print("W1 baselines 5m/15m/1h …")
        bl = w1_baselines(symbols)
        if bl.height:
            check_no_outcome_columns(bl, context="artifact:seasonal_baselines_mtf")
            bl.write_parquet(bl_path)
            pins["artifacts"]["seasonal_baselines_mtf.parquet"] = sha256_file(bl_path)
            if "bar_minutes" in bl.columns and (bl["bar_minutes"] == 1).any():
                raise RuntimeError("W1 must not emit a 1-minute baseline (INFR-017 is sole 1m pin)")
        else:
            bl_path.write_bytes(b"")
            pins["artifacts"]["seasonal_baselines_mtf.parquet"] = _sha256_bytes(b"")

        # --- W3 ---
        print("W3 thresholds …")
        th = w3_thresholds(symbols, bl)
        pins["artifacts"]["class_thresholds_mtf.json"] = emit_json(
            th_path, th, context="class_thresholds_mtf"
        )

        # --- W4 ---
        print("W4 sessions …")
        pins["artifacts"]["sessions_mtf.json"] = emit_json(
            sess_path, w4_sessions(symbols), context="sessions_mtf"
        )

    # --- W3b: 1m thresholds for the whole universe (D1 reproducibility) ---
    print("W3b 1m thresholds (universe) …")
    th_1m = w3b_thresholds_1m(symbols)
    pins["artifacts"]["class_thresholds_1m.json"] = emit_json(
        th1m_path, th_1m, context="class_thresholds_1m"
    )

    # --- W5 full zone-scale census (count-only) ---
    print("W5 zone-scale census (prior-session range + candidate distances) …")
    w5 = w5_zone_scale_census(symbols, th, bl, th_1m)
    pins["artifacts"]["zone_scale_census.json"] = emit_json(
        RESULTS / "zone_scale_census.json",
        w5["zone_scale_census"],
        context="zone_scale_census",
    )
    pins["artifacts"]["zone_scale_census_d1_ibwidth.json"] = emit_json(
        RESULTS / "zone_scale_census_d1_ibwidth.json",
        w5["zone_scale_census_d1_ibwidth"],
        context="zone_scale_census_d1_ibwidth",
    )

    # --- coverage ---
    print("coverage report …")
    cov = coverage_report(symbols, w2["class_counts"])
    pins["artifacts"]["coverage_report.json"] = emit_json(
        RESULTS / "coverage_report.json", cov, context="coverage_report"
    )
    # --- accounting fence ---
    acct = check_no_local_accounting(Path(__file__).resolve().parent)
    if not acct["ok"]:
        raise RuntimeError(f"local accounting defs found: {acct}")

    # --- battery coverage of these pins (QA-6 I-3) ---
    bat_path = RESULTS / "reproduction_battery.json"
    if not bat_path.exists():
        raise RuntimeError(
            "no reproduction_battery.json on disk — pins may not be handed to a "
            "consumer without the battery that covers them"
        )
    bat = json.loads(bat_path.read_text())
    pins["artifacts"]["reproduction_battery.json"] = sha256_file(bat_path)
    pins["battery"] = {
        "mode": bat.get("mode"),
        "all_ok": bat.get("all_ok"),
        "generated_utc": bat.get("generated_utc"),
        "n_symbols": len(bat.get("symbols") or []),
    }
    if args.full and (bat.get("mode") != "full" or not bat.get("all_ok")):
        raise RuntimeError(
            f"full-universe pins require a passing full battery; got mode="
            f"{bat.get('mode')!r} all_ok={bat.get('all_ok')!r}"
        )

    # Stamp at write time, not run start, so the pin cannot read as predating
    # its own contents; record what the battery actually covers (QA-7 I7-9).
    pins["generated_utc"] = datetime.now(timezone.utc).isoformat()
    pins["battery"]["covers_modules"] = [
        "xen.sigbar.ltf",
        "xen.sigbar.fences",
        "xen.sigbar.baselines",
        "xen.sigbar.sessions",
        "xen.sigbar.classes",
        "xen.sigbar.profile",
    ]
    pins["battery"]["covers_runner"] = False
    pins_path = RESULTS / "pins.json"
    emit_json(pins_path, pins, context="pins")
    print(json.dumps({"ok": True, "pins": str(pins_path), "n_symbols": len(symbols)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
