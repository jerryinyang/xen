"""INFR-018 HYP-I4 — instrument validation (source Appendix B Phase 3 + §6.4).

Three exits, all required:

1. **Profile kernel calibrated against a finer reference.** The Bybit public
   trade archive gives trade-level volume-at-price — the truth the §2.1 proxy
   stands in for — so the kernel is calibrated, not frozen blind, and
   ``SKIP-NO-REFERENCE`` is not taken.
2. **§2.3 signed classes cluster at structural edges rather than uniformly**,
   against a seasonal-residual-matched non-event control, with the warning
   prints tested for a distinct *locational* profile.
3. **Baselines and regime bands finalise.** The A5 baselines are already frozen
   at INFR-017; what finalises here is the per-symbol residual threshold values.
   The §2.5 **spread regime bands are recorded UNAVAILABLE** — the stored column
   is pinned unusable and the validated replacement exists on 20 symbol-days
   only (operator decision 2026-07-20).

Usage
-----
    python python/experiments/INFR-018/code/hyp_i4_validation.py
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    SEED_CONTROL_MATCH,
    day_clustered_ci,
    mde_curve,
    out_dir,
    realise_universe,
    residualise_symbol,
    write_json,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.sigbar.classes import (  # noqa: E402
    CLASSES,
    HIGH_PCTL,
    LOCATED_CLASSES,
    LOW_PCTL,
    classify,
    derive_thresholds,
    match_quality,
    residual_matched_control,
    structural_distance,
)
from xen.sigbar.fences import (  # noqa: E402
    assert_band,
    assert_frozen_inputs,
    band_window,
    load_bars,
    repo_root,
)
from xen.sigbar.profile import (  # noqa: E402
    KERNELS,
    build_profile,
    displacement,
    poc_and_value_area,
    price_grid,
    trade_truth_profile,
)
from xen.sigbar.sessions import CANDIDATE_ANCHORS, anchor_table, attach_sessions, session_breaks  # noqa: E402

#: Planted clustering shifts for the exit-2 MDE curve, in the same units as the
#: class contrast the curve is swept on (AMENDMENT-5 framing; not re-audited for
#: a drift-vs-contrast factor on this exit — see design §5.2 if revisited).
CLUSTER_MDE_GRID = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00]

ARCHIVE_URL = "https://public.bybit.com/trading/{symbol}/{symbol}{day}.csv.gz"

#: Calibration reference sample — the SAME 20 symbol-days already audited at
#: INFR-017 A8, re-declared here rather than re-chosen after seeing anything.
CAL_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT")
CAL_DAYS = ("2022-09-14", "2023-01-11", "2023-06-07", "2023-11-01")

#: Two of the four days sit in the CONFIRM band. Disclosed, and permitted:
#: kernel calibration measures reconstruction fidelity of a bar aggregation, not
#: expectancy, and spends no selection budget. The DESIGN-only subset is
#: reported separately so the two scopes are never quoted interchangeably.
DESIGN_CAL_DAYS = ("2022-09-14", "2023-01-11")

CACHE = "python/experiments/INFR-018/data/trade_cache"


def download_day(symbol: str, day: str, timeout: int = 300) -> bytes | None:
    """Fetch (and cache) one gzipped day of raw trades; None if unavailable."""
    cache = repo_root() / CACHE
    cache.mkdir(parents=True, exist_ok=True)
    p = cache / f"{symbol}{day}.csv.gz"
    if p.exists():
        return p.read_bytes()
    try:
        with urllib.request.urlopen(ARCHIVE_URL.format(symbol=symbol, day=day), timeout=timeout) as r:
            b = r.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    p.write_bytes(b)
    return b


def parse_trades(gz_bytes: bytes) -> pl.DataFrame:
    """Raw archive rows as ``timestamp, price, size``, cleaned per INFR-011's rule."""
    df = pl.read_csv(
        io.BytesIO(gzip.decompress(gz_bytes)),
        columns=["timestamp", "size", "price"],
        schema_overrides={"timestamp": pl.Float64, "size": pl.Float64, "price": pl.Float64},
        ignore_errors=True,
    )
    if df.is_empty():
        return df
    return df.filter(
        pl.col("timestamp").is_not_null()
        & pl.col("price").is_not_null()
        & pl.col("size").is_not_null()
        & (pl.col("size") > 0)
        & (pl.col("price") > 0)
    ).sort("timestamp")


# ---------------------------------------------------------------------------
# Exit 1 — kernel calibration
# ---------------------------------------------------------------------------


def infer_tick(trades: pl.DataFrame) -> float | None:
    """Smallest positive price increment observed — the instrument's tick.

    Returns ``None`` when no positive increment appears, so a
    ``SPEC_INCOMPLETE`` instrument yields a null tick figure rather than a
    displacement silently computed against a guessed tick size.
    """
    p = np.unique(trades["price"].to_numpy())
    if p.size < 2:
        return None
    d = np.diff(p)
    d = d[d > 0]
    return float(d.min()) if d.size else None


def calibrate_kernels(anchor_spec, ib_minutes: int) -> dict:
    """Compare each candidate kernel's profile against trade-level truth.

    The calibration window is one anchored session per symbol-day, so the object
    calibrated is the object the framework actually builds profiles on.

    **The winner is chosen on the DESIGN bank alone.** QA run 1 (I-6) found the
    winner selected on the DESIGN+CONFIRM pool while the DESIGN-only table was
    computed and then ignored. The design permits CONFIRM days here because
    reconstruction fidelity is not an expectancy read and *spends no selection
    budget* — but selecting the winner on them spends exactly that, and leaves
    HYP-I4 with no untouched band to confirm in, which is the whole point of the
    checkpoint's D3 adaptation. The CONFIRM days now serve only as the
    TRAIN-INTERNAL confirmation that the DESIGN choice reproduces.
    """
    rows: list[dict] = []
    unavailable: list[dict] = []
    for sym in CAL_SYMBOLS:
        for day in CAL_DAYS:
            gz = download_day(sym, day)
            if gz is None:
                unavailable.append({"symbol": sym, "day": day, "reason": "archive fetch failed"})
                continue
            trades = parse_trades(gz)
            if trades.is_empty():
                unavailable.append({"symbol": sym, "day": day, "reason": "no usable trades"})
                continue
            d0 = datetime.fromisoformat(day)
            band = "DESIGN" if day in DESIGN_CAL_DAYS else "CONFIRM"

            # The archive is the one read path that fetches from outside the
            # fenced staging tree, so its timestamps are asserted rather than
            # trusted to the CAL_DAYS literal (QA run 1, I-19).
            ts = pl.from_epoch(trades["timestamp"].cast(pl.Int64), time_unit="s")
            assert_band(pl.DataFrame({"OpenTime": ts}), band)
            if ts.min() < d0 or ts.max() >= d0 + timedelta(days=1):
                raise RuntimeError(
                    f"trade archive for {sym} {day} spans [{ts.min()}, {ts.max()}], outside the "
                    "declared calibration day"
                )

            bars = load_bars(sym, band).filter(
                (pl.col("OpenTime") >= d0) & (pl.col("OpenTime") < d0 + timedelta(days=1))
            )
            if bars.height == 0:
                unavailable.append({"symbol": sym, "day": day, "reason": "no stored bars in band"})
                continue

            lo, hi = float(bars["Low"].min()), float(bars["High"].max())
            edges = price_grid(lo, hi)
            # Truth restricted to the same price span so proxy and truth share a grid.
            t = trades.filter((pl.col("price") >= lo) & (pl.col("price") <= hi))
            truth = trade_truth_profile(t, edges)

            # The divisor is the SESSION IB width of the frozen anchor on this
            # day — the object design §5.1 names — not the day's full range.
            anchors = anchor_table(anchor_spec, d0 - timedelta(days=1), d0 + timedelta(days=2))
            sess = session_breaks(bars, anchors, ib_minutes)
            ib_width = float(sess["ib_width"].drop_nulls().median()) if sess.height else float("nan")
            tick = infer_tick(t)

            for kernel in KERNELS:
                _, prof = build_profile(bars, kernel, edges=edges)
                d = displacement(edges, prof, truth, ib_width=ib_width, tick=tick)
                rows.append({"symbol": sym, "day": day, "band": band, "kernel": kernel,
                             "n_trades": t.height, "n_bars": bars.height, **d})

    if not rows:
        return {
            "calibration": "SKIP-NO-REFERENCE",
            "reason": "no reference sample could be obtained (archive unreachable)",
            "unavailable": unavailable,
        }

    tbl = pl.DataFrame(rows)

    def _summary(frame: pl.DataFrame) -> pl.DataFrame:
        return (
            frame.group_by("kernel")
            .agg(
                pl.col("poc_disp_norm_ib_width").median().alias("median_poc_disp_norm_ib_width"),
                pl.col("poc_disp_ticks").median().alias("median_poc_disp_ticks"),
                pl.col("tv_distance").median().alias("median_tv_distance"),
                pl.col("val_disp_norm_ib_width").median().alias("median_val_disp_norm_ib_width"),
                pl.col("vah_disp_norm_ib_width").median().alias("median_vah_disp_norm_ib_width"),
                pl.len().alias("n_windows"),
            )
            .sort(["median_poc_disp_norm_ib_width", "median_tv_distance"])
        )

    design_only = _summary(tbl.filter(pl.col("band") == "DESIGN"))
    confirm_only = _summary(tbl.filter(pl.col("band") == "CONFIRM"))
    if design_only.height == 0:
        return {
            "calibration": "SKIP-NO-REFERENCE",
            "reason": "no DESIGN-bank reference window could be obtained; a winner selected on "
                      "CONFIRM alone would spend selection budget on the confirmation band",
            "unavailable": unavailable,
        }
    winner = design_only["kernel"][0]
    return {
        "calibration": "PERFORMED",
        "reference": {
            "source": "Bybit public trade archive (trade-level volume-at-price)",
            "symbols": list(CAL_SYMBOLS),
            "days": list(CAL_DAYS),
            "design_bank_days": list(DESIGN_CAL_DAYS),
            "scope_note": "the winner is selected on the DESIGN days ONLY. The CONFIRM days are "
                          "reported as a TRAIN-INTERNAL reproduction check and spend no "
                          "selection budget. The two scopes are never quoted interchangeably.",
        },
        "per_window": rows,
        "summary_design_only": design_only.to_dicts(),
        "summary_confirm_train_internal": confirm_only.to_dicts(),
        "winner": winner,
        "winner_selected_on": "DESIGN",
        "confirm_reproduces_winner": (
            bool(confirm_only["kernel"][0] == winner) if confirm_only.height else None
        ),
        "unavailable": unavailable,
    }


# ---------------------------------------------------------------------------
# Exit 2 — class clustering
# ---------------------------------------------------------------------------


def prior_session_levels(
    bars: pl.DataFrame, sess: pl.DataFrame, kernel: str
) -> pl.DataFrame:
    """Structural levels for each session, all knowable at or before its open.

    Three families, per design §5.2 — QA run 1 (I-11) found only one and a half
    of them built, which left the exit-1 kernel entirely unconsumed by exit 2 and
    made a null result unreadable ("classes do not cluster at IB edges" is not
    "classes do not cluster at structure"):

    1. this session's IB edges;
    2. the prior session's true HIGH and LOW — the session extreme, which is a
       different object from the prior IB (the first 15-60 minutes only);
    3. the prior session's POC and value-area edges, built with the **frozen
       kernel** — the object exit 1 calibrates that kernel expressly to produce.

    Each level carries ``level_created_ts``, the timestamp of the bar that
    established it, so a class event can be excluded from a level it created.
    """
    out: list[pl.DataFrame] = []
    ordered = sess.sort("anchor_ts")

    # (1) this session's IB edges, with the bars that set them
    out.append(ordered.select(
        "anchor_ts",
        pl.col("ib_high").alias("level_price"),
        pl.lit("IB_HIGH").alias("level_kind"),
        pl.col("ib_high_ts").alias("level_created_ts"),
    ))
    out.append(ordered.select(
        "anchor_ts",
        pl.col("ib_low").alias("level_price"),
        pl.lit("IB_LOW").alias("level_kind"),
        pl.col("ib_low_ts").alias("level_created_ts"),
    ))

    # (2)+(3) prior-session objects, computed per session then shifted forward
    rows: list[dict] = []
    anchors = ordered["anchor_ts"].to_list()
    ends = ordered["session_end"].to_list()
    for a, e in zip(anchors, ends):
        win = bars.filter((pl.col("OpenTime") >= a) & (pl.col("OpenTime") < e))
        if win.height == 0:
            continue
        hi_ts = win.sort("High", descending=True)["OpenTime"][0]
        lo_ts = win.sort("Low")["OpenTime"][0]
        rec = {
            "src_anchor": a,
            "prior_high": float(win["High"].max()),
            "prior_high_ts": hi_ts,
            "prior_low": float(win["Low"].min()),
            "prior_low_ts": lo_ts,
        }
        try:
            edges, prof = build_profile(win, kernel)
            poc, val, vah = poc_and_value_area(edges, prof)
            rec.update({"prior_poc": poc, "prior_val": val, "prior_vah": vah})
        except (ValueError, ZeroDivisionError):
            rec.update({"prior_poc": None, "prior_val": None, "prior_vah": None})
        rows.append(rec)

    if rows:
        prior = pl.DataFrame(rows).sort("src_anchor")
        # shift forward: session N's levels are available to session N+1
        prior = prior.with_columns(pl.col("src_anchor").shift(-1).alias("anchor_ts")).drop_nulls(
            "anchor_ts"
        )
        for col, kind, ts_col in (
            ("prior_high", "PRIOR_SESSION_HIGH", "prior_high_ts"),
            ("prior_low", "PRIOR_SESSION_LOW", "prior_low_ts"),
            ("prior_poc", "PRIOR_POC", None),
            ("prior_val", "PRIOR_VAL", None),
            ("prior_vah", "PRIOR_VAH", None),
        ):
            if col not in prior.columns:
                continue
            out.append(prior.select(
                "anchor_ts",
                pl.col(col).alias("level_price"),
                pl.lit(kind).alias("level_kind"),
                (pl.col(ts_col) if ts_col else pl.lit(None, dtype=pl.Datetime)).alias(
                    "level_created_ts"
                ),
            ))

    return pl.concat(out, how="vertical").drop_nulls("level_price")


def class_clustering(
    anchor_spec, ib_minutes: int, membership: pl.DataFrame, band: str, kernel: str
) -> dict:
    """Do §2.3 class events sit nearer structural levels than matched non-events?"""
    root = repo_root()
    start, end = band_window(band)
    anchors = anchor_table(anchor_spec, start, end)
    symbols = sorted(membership["symbol"].unique().to_list())

    thresholds: dict[str, dict] = {}
    counts: dict[str, int] = {}
    match_rows: dict[str, list[dict]] = {}
    excluded_self_levels = 0
    per_class_rows: dict[str, list[pl.DataFrame]] = {
        c: [] for c in CLASSES
    }

    for sym in tqdm(symbols, desc="classes"):
        raw = load_bars(sym, band, root=root)
        if raw.height == 0:
            continue
        try:
            res = residualise_symbol(raw, sym)
        except RuntimeError:
            continue
        th = derive_thresholds(res, ("volume", "range", "delta_abs", "delta_ratio"))
        if len(th) < 4:
            continue
        thresholds[sym] = th
        sess = session_breaks(res, anchors, ib_minutes)
        if sess.height == 0:
            continue
        attached = attach_sessions(res, anchors, ib_minutes)
        tagged = classify(attached, th)
        member_days = membership.filter(pl.col("symbol") == sym).select("day").unique()
        tagged = tagged.with_columns(pl.col("anchor_ts").dt.truncate("1d").alias("day")).join(
            member_days, on="day", how="semi"
        )

        levels = prior_session_levels(attached, sess, kernel)
        scaled = tagged.join(sess.select("anchor_ts", "ib_width"), on="anchor_ts", how="inner")

        for cls in per_class_rows:
            ev = scaled.filter(pl.col("sig_class") == cls)
            if ev.height == 0:
                continue
            counts[cls] = counts.get(cls, 0) + ev.height
            if cls not in LOCATED_CLASSES:
                # Counted, but not clustering-tested: its mechanism makes no
                # locational prediction, so a clustering claim would test
                # something §2.3 does not assert.
                continue
            ctrl = residual_matched_control(scaled, ev, seed=SEED_CONTROL_MATCH)
            if ctrl.height == 0:
                continue
            match_rows.setdefault(cls, []).append(match_quality(ev, ctrl))
            d_ev = structural_distance(ev, levels).with_columns(pl.lit("EVENT").alias("arm"))
            d_ct = structural_distance(ctrl, levels).with_columns(pl.lit("CONTROL").alias("arm"))
            excluded_self_levels += int(
                ev.height + ctrl.height - (d_ev.height + d_ct.height)
            )
            for frame in (d_ev, d_ct):
                if frame.height:
                    per_class_rows[cls].append(
                        frame.with_columns(
                            pl.lit(sym).alias("symbol"),
                            pl.col("anchor_ts").dt.truncate("1d").alias("day"),
                        )
                    )

    out: dict = {
        "thresholds_per_symbol": thresholds,
        "percentile_levels": {"high": HIGH_PCTL, "low": LOW_PCTL},
        "event_counts": counts,
        "classes_detected": list(CLASSES),
        "classes_clustering_tested": list(LOCATED_CLASSES),
        "non_located_note": "DRY_UP, DRIVE and DRIVE_WARNING_PRINT are DETECTED AND COUNTED but "
                            "not clustering-tested: §2.3 gives them no locational prediction. "
                            "A zero count therefore means 'none occurred', never 'never looked "
                            "for'.",
        "self_created_levels_excluded": excluded_self_levels,
        "level_families": ["IB_HIGH", "IB_LOW", "PRIOR_SESSION_HIGH", "PRIOR_SESSION_LOW",
                           "PRIOR_POC", "PRIOR_VAL", "PRIOR_VAH"],
        "per_class": {},
    }
    for cls, frames in per_class_rows.items():
        if cls not in LOCATED_CLASSES:
            out["per_class"][cls] = {
                "n_event": counts.get(cls, 0),
                "status": "DETECTED_NOT_CLUSTERING_TESTED",
                "reason": "no locational prediction in §2.3",
            }
            continue
        if not frames:
            out["per_class"][cls] = {"n": 0, "status": "NO_EVENTS"}
            continue
        allf = pl.concat(frames, how="vertical")
        ev = allf.filter(pl.col("arm") == "EVENT")
        ct = allf.filter(pl.col("arm") == "CONTROL")
        if ev.height == 0 or ct.height == 0:
            out["per_class"][cls] = {"n_event": ev.height, "n_control": ct.height,
                                     "status": "NO_CONTRAST"}
            continue
        e = ev.group_by("day").agg(pl.col("d_norm").median().alias("e")).sort("day")
        c = ct.group_by("day").agg(pl.col("d_norm").median().alias("c")).sort("day")
        j = e.join(c, on="day", how="inner")
        contrast = (j["e"] - j["c"]).to_numpy()
        ci = day_clustered_ci(contrast)
        # The plant curve is published for every class BEFORE its real contrast
        # is read, so an UNPOWERED class is distinguishable from a null one.
        power = mde_curve(-contrast, CLUSTER_MDE_GRID) if len(contrast) else {"mde": None}
        mde = power.get("mde")
        obs = float(np.median(contrast)) if len(contrast) else None
        # UNPOWERED first (B-5 / I-32): |obs| < MDE is "not measurable", not WASH.
        if obs is None:
            band_label = "NO_CONTRAST"
        elif mde is None or abs(obs) < mde:
            band_label = "UNPOWERED"
        elif obs < 0 and ci["ci"][1] is not None and ci["ci"][1] < 0:
            band_label = "CLUSTERS"
        elif ci["ci"][0] is not None and ci["ci"][0] > 0:
            band_label = "ANTI_CLUSTERS"
        else:
            band_label = "WASH"
        out["per_class"][cls] = {
            "n_event": ev.height,
            "n_control": ct.height,
            "n_days_paired": len(contrast),
            "contrast_median": obs,
            "contrast_ci": ci,
            "power": power,
            "interpretation_band": band_label,
            "band_note": "LABEL, NOT A GATE (L-32). UNPOWERED is never read as a negative (B-5).",
            "match_quality": match_rows.get(cls, []),
            "nearest_level_kinds": (
                ev.group_by("nearest_kind").agg(pl.len().alias("n")).sort("n", descending=True)
                .to_dicts()
            ),
            "reads": "NEGATIVE contrast = events sit NEARER structure than matched non-events",
            "located_class": True,
            "CALIBRATION_ONLY": {
                "note": "NOT_AN_EDGE_CLAIM — absolute arm distances, for audit of the contrast only",
                "median_d_norm_event": float(ev["d_norm"].median() or float("nan")),
                "median_d_norm_control": float(ct["d_norm"].median() or float("nan")),
            },
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", default="DESIGN", choices=["DESIGN", "CONFIRM"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    frozen = assert_frozen_inputs()
    freeze = out_dir() / "anchor_freeze.json"
    a6 = out_dir() / "a6_freeze.json"
    for p, why in ((freeze, "HYP-I2 anchor"), (a6, "HYP-I3 A6 rule")):
        if not p.exists():
            raise RuntimeError(
                f"HYP-I4 requires the frozen {why} ({p.name}). Source Appendix B: a result "
                "obtained out of sequence is unattributable and re-runs."
            )
    fa = json.loads(freeze.read_text())
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == fa["anchor_id"])
    ib_minutes = int(fa["ib_minutes"])

    membership, recon = realise_universe(args.band, limit=args.limit)
    universe_scale = {
        "limit": args.limit,
        "n_symbols_selected": int(recon.get("n_distinct_symbols_selected") or 0),
        "n_days": int(recon.get("n_days") or 0),
    }

    kernel = calibrate_kernels(spec, ib_minutes)
    if kernel.get("calibration") != "PERFORMED":
        raise RuntimeError(
            "HYP-I4 exit 1 could not calibrate the kernel against a finer reference "
            f"({kernel.get('reason')}). A silent uncalibrated freeze is banned (checkpoint-014 "
            "§4 HYP-I4.1): either restore archive access, or record SKIP-NO-REFERENCE as an "
            "operator-signed decision in the design before re-running."
        )
    clustering = class_clustering(spec, ib_minutes, membership, args.band, kernel["winner"])

    write_json(
        f"hyp_i4_validation_{args.band}.json",
        {
            "hypothesis": "HYP-I4",
            "phase": "source Appendix B Phase 3 + §6.4 — validate the instruments",
            "band": args.band,
            "inherited": {"anchor_id": fa["anchor_id"], "ib_minutes": ib_minutes,
                          "a6_rule": json.loads(a6.read_text()).get("disc_id")},
            "frozen_inputs": {
                "baselines_sha256": frozen.baselines_sha256,
                "column_pins_sha256": frozen.column_pins_sha256,
            },
            "universe_scale": universe_scale,
            "exit_1_kernel": kernel,
            "exit_2_class_clustering": clustering,
            "exit_3_bands": {
                "a5_baselines": {
                    "status": "FROZEN AT INFR-017 — consumed, not refitted",
                    "sha256": frozen.baselines_sha256,
                    "finalised_here": "per-symbol residual threshold VALUES at the declared "
                                      "percentile levels (see exit_2_class_clustering.thresholds_per_symbol)",
                },
                "delta_truth_window": {
                    "status": "NOT REQUIRED",
                    "reason": "delta IS truth at bar scale (source §6.4); it needs no reference window",
                },
                "spread_regime_bands": {
                    "status": "UNAVAILABLE — NO USABLE INPUT",
                    "reason": "the stored SpreadBps column is pinned UNUSABLE (INFR-017 W2: "
                              "negative in 32.374% of BTC and 39.939% of ETH TRAIN minutes; a "
                              "spread is non-negative by construction). The validated flip-pair "
                              "replacement exists on 20 symbol-days only and a universe-wide "
                              "recompute is an INFR-011-scale data operation, out of this item's "
                              "budget.",
                    "operator_decision": "2026-07-20 — record as unavailable and move on",
                    "binding_downstream_consequence": "the source's §2.5 spread regime/veto layer "
                                                      "(stress-regime conditioning, precision-location "
                                                      "demotion, re-normalisation marking) is NOT "
                                                      "available to Stage II; every later read that "
                                                      "would have used it must state its absence.",
                },
            },
            "scope": "STAGE I — validated instruments, never evidence that anything works",
        },
    )
    print(f"wrote {out_dir() / f'hyp_i4_validation_{args.band}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
