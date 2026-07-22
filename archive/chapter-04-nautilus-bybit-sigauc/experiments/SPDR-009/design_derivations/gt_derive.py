"""Designer-side golden-trace derivation for SPDR-009 (S9 signed absorption).

Independent of the future ``xen.sigbar.absorb`` implementation by construction:
every quantity below is recomputed here from the frozen primitives
(``fences.load_bars``, ``baselines.residualise``, ``sessions``, ``profile``) and
the pinned INFR-018 registry. QA diffs the implementation against this output;
the developer must not regenerate it.

Run:  python python/experiments/SPDR-009/design_derivations/gt_derive.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from xen.sigbar.baselines import residualise  # noqa: E402
from xen.sigbar.fences import assert_frozen_inputs, load_bars, repo_root  # noqa: E402
from xen.sigbar.profile import build_profile, poc_and_value_area  # noqa: E402
from xen.sigbar.sessions import anchor_table, attach_sessions, session_breaks  # noqa: E402
from xen.sigbar.spine import IB_MINUTES, anchor_spec  # noqa: E402

REGISTRY = "python/experiments/INFR-018/results/instrument_registry.json"
BASELINES = "python/experiments/INFR-017/results/seasonal_baselines.parquet"
KERNEL = "K-UNIFORM"
VA_SHARE = 0.685
HOLDS = (5, 10)
#: Contact zone: |Close - level| <= TAU * ib_width. Source §2.1 requires profile
#: levels to be ZONES with a stated tolerance, never precision levels.
TAU = 0.25
METRICS = ("volume", "range", "delta_abs", "delta_ratio")


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #
def bar_metrics(bars: pl.DataFrame) -> pl.DataFrame:
    return bars.with_columns(
        pl.col("Volume").alias("volume"),
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Delta").abs().alias("delta_abs"),
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("Delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )


def resid(bars: pl.DataFrame, symbol: str) -> pl.DataFrame:
    bl = (
        pl.scan_parquet(repo_root() / BASELINES)
        .filter(pl.col("symbol") == symbol)
        .collect()
    )
    if bl.height == 0:
        raise RuntimeError(f"no frozen A5 baseline for {symbol}")
    out = bar_metrics(bars)
    for m in METRICS:
        out = residualise(out, bl, m, time_col="OpenTime")
    return out


def levels_for(bars: pl.DataFrame, sess: pl.DataFrame) -> pl.DataFrame:
    """IB edges (this session, fixed at anchor+L) + prior-session extremes/POC/VA."""
    ordered = sess.sort("anchor_ts")
    out = [
        ordered.select(
            "anchor_ts",
            pl.col("ib_high").alias("level_price"),
            pl.lit("IB_HIGH").alias("level_kind"),
        ),
        ordered.select(
            "anchor_ts",
            pl.col("ib_low").alias("level_price"),
            pl.lit("IB_LOW").alias("level_kind"),
        ),
    ]
    rows: list[dict] = []
    for a, e in zip(ordered["anchor_ts"].to_list(), ordered["session_end"].to_list()):
        win = bars.filter((pl.col("OpenTime") >= a) & (pl.col("OpenTime") < e))
        if win.height == 0:
            continue
        rec = {
            "src_anchor": a,
            "prior_high": float(win["High"].max()),
            "prior_low": float(win["Low"].min()),
        }
        try:
            edges, prof = build_profile(win, KERNEL)
            poc, val, vah = poc_and_value_area(edges, prof, share=VA_SHARE)
            rec.update({"prior_poc": poc, "prior_val": val, "prior_vah": vah})
        except (ValueError, ZeroDivisionError):
            rec.update({"prior_poc": None, "prior_val": None, "prior_vah": None})
        rows.append(rec)
    if rows:
        prior = pl.DataFrame(rows).sort("src_anchor")
        prior = prior.with_columns(
            pl.col("src_anchor").shift(-1).alias("anchor_ts")
        ).drop_nulls("anchor_ts")
        for col, kind in (
            ("prior_high", "PRIOR_SESSION_HIGH"),
            ("prior_low", "PRIOR_SESSION_LOW"),
            ("prior_poc", "PRIOR_POC"),
            ("prior_val", "PRIOR_VAL"),
            ("prior_vah", "PRIOR_VAH"),
        ):
            out.append(
                prior.select(
                    "anchor_ts",
                    pl.col(col).alias("level_price"),
                    pl.lit(kind).alias("level_kind"),
                )
            )
    return pl.concat(out, how="vertical").drop_nulls("level_price")


# --------------------------------------------------------------------------- #
# S9 event construction (design §3)
# --------------------------------------------------------------------------- #
def events_for(symbol: str, th: dict) -> list[dict]:
    bars = load_bars(symbol, "DESIGN")
    spec = anchor_spec()
    anchors = anchor_table(spec, bars["OpenTime"].min(), bars["OpenTime"].max())
    sess = session_breaks(bars, anchors, IB_MINUTES)
    lv = levels_for(bars, sess)
    r = resid(bars, symbol)
    j = attach_sessions(r, anchors, IB_MINUTES).join(
        sess.select("anchor_ts", "ib_high", "ib_low", "ib_width"), on="anchor_ts", how="left"
    )
    # Hold is measured on the RAW contiguous 1-minute series, never on the
    # session-attached frame: indexing the latter would step across session
    # gaps and silently lengthen the hold.
    raw = bars.sort("OpenTime")
    raw_idx = {t: i for i, t in enumerate(raw["OpenTime"].to_list())}
    raw_open = raw["Open"].to_list()
    raw_ts = raw["OpenTime"].to_list()

    v_hi = th["volume"]["high"]
    r_lo = th["range"]["low"]
    d_hi = th["delta_abs"]["high"]
    dr_abs_hi = th["delta_ratio"]["abs_high"]

    # unsigned climax-hold base: heavy volume, bottom-decile range
    base = j.with_columns(
        (
            (pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= r_lo)
        ).fill_null(False).alias("is_base"),
        pl.col("Close").shift(1).alias("prev_close"),
    )

    lv_by_anchor: dict = {}
    for row in lv.iter_rows(named=True):
        lv_by_anchor.setdefault(row["anchor_ts"], []).append(
            (row["level_kind"], row["level_price"])
        )

    cand = base.filter(pl.col("is_base")).drop_nulls("prev_close")

    out: list[dict] = []
    for e in cand.iter_rows(named=True):
        ibw = e["ib_width"]
        if ibw is None or ibw <= 0:
            continue
        for kind, price in lv_by_anchor.get(e["anchor_ts"], []):
            if price is None or abs(e["Close"] - price) > TAU * ibw:
                continue
            if kind.startswith("IB") and e["mins_since"] < IB_MINUTES:
                continue  # IB edge not yet fixed — causality
            # "Δ sign points INTO the level" (source S9): into = the direction
            # from price TO the level. Close is the reference; prev_close only
            # breaks an exact tie. Both are known at the event bar's close and
            # the entry is the NEXT bar's open, so this is ≤ t−1.
            into = 1 if e["Close"] < price else (-1 if e["Close"] > price else 0)
            if into == 0:
                into = (
                    1 if e["prev_close"] < price else (-1 if e["prev_close"] > price else 0)
                )
            if into == 0:
                continue
            dr = e["delta_ratio_resid"]
            da = e["delta_abs_resid"]
            if dr is None or da is None:
                continue
            signed = into * dr
            if da >= d_hi and signed >= dr_abs_hi:
                arm = "S9"
            elif da >= d_hi and signed <= -dr_abs_hi:
                arm = "MIRROR"
            else:
                arm = "BASE"
            marker = arm == "S9"
            i = raw_idx[e["OpenTime"]]
            entry_i = i + 1
            if entry_i + max(HOLDS) >= len(raw_open):
                continue
            # entry_ts is defined by the CLOCK (event_ts + 1min), not by position:
            # across a data gap the next row is not the next minute (QA-1 R13).
            if (raw_ts[entry_i] - e["OpenTime"]).total_seconds() != 60:
                continue
            # contiguity: the whole hold must be unbroken 1-minute bars
            span = (raw_ts[entry_i + max(HOLDS)] - raw_ts[entry_i]).total_seconds() / 60
            if span != max(HOLDS):
                continue
            entry = raw_open[entry_i]
            side = -into
            rets = {
                f"ret_bps_H{h}": side * 1e4 * (raw_open[entry_i + h] - entry) / entry
                for h in HOLDS
            }
            out.append(
                {
                    "symbol": symbol,
                    "event_ts": str(e["OpenTime"]),
                    "anchor_ts": str(e["anchor_ts"]),
                    "level_kind": kind,
                    "level_price": price,
                    "OHLC": [e["Open"], e["High"], e["Low"], e["Close"]],
                    "prev_close": e["prev_close"],
                    "into_side": into,
                    "volume_resid": e["volume_resid"],
                    "range_resid": e["range_resid"],
                    "delta_abs_resid": da,
                    "delta_ratio_resid": dr,
                    "signed_score": signed,
                    "arm": arm,
                    "S9_marker": marker,
                    "entry_ts": str(raw_ts[entry_i]),
                    "entry_open": entry,
                    "rev_side": "SHORT" if side < 0 else "LONG",
                    "ib_width": e["ib_width"],
                    **rets,
                }
            )
    return out


def main() -> None:
    fi = assert_frozen_inputs()
    reg = json.loads((repo_root() / REGISTRY).read_text())
    th_all = reg["class_thresholds"]["per_symbol_values"]
    print(f"frozen baselines sha256 = {fi.baselines_sha256[:8]}…")
    print(f"registry class_thresholds symbols = {len(th_all)}")

    # Only the PINNED golden traces are written to disk. QA run 1 (I-15) found
    # that dumping every pool event's forward return would make any later
    # amendment to tau / the pool legs / the arm cuts outcome-informed by
    # construction. The census that justifies the event definition lives in
    # diag_census.py, which computes no outcome at all.
    payload: dict = {
        "frozen": {"baselines": fi.baselines_sha256},
        "scope": "PINNED GOLDEN TRACES ONLY — not a result set (QA-1 I-15)",
        "events": {},
    }
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        if sym not in th_all:
            print(f"{sym}: no pinned class thresholds — skipped")
            continue
        ev = events_for(sym, th_all[sym])
        marked = [e for e in ev if e["arm"] == "S9"]
        mirror = [e for e in ev if e["arm"] == "MIRROR"]
        unmarked = [e for e in ev if e["arm"] == "BASE"]
        by_kind: dict[str, int] = {}
        for e in ev:
            by_kind[e["level_kind"]] = by_kind.get(e["level_kind"], 0) + 1
        print(
            f"\n=== {sym}: pool P n={len(ev)} | S9 n={len(marked)} "
            f"| MIRROR n={len(mirror)} | BASE n={len(unmarked)} | by level {by_kind}"
        )
        picks = marked[:2] + mirror[:1] + unmarked[:1]
        prior = [e for e in ev if e["level_kind"].startswith("PRIOR")]
        if prior:
            picks.append(prior[0])
        # de-duplicate: the PRIOR pick can already be one of the arm picks (QA-2 R-9)
        seen: set = set()
        picks = [
            e
            for e in picks
            if not (key := (e["event_ts"], e["level_kind"])) in seen and not seen.add(key)
        ]
        payload["events"][sym] = picks
        for e in picks:
            print(json.dumps(e, indent=1, default=str))

    (Path(__file__).parent / "gt_output.json").write_text(
        json.dumps(payload, indent=1, default=str)
    )


if __name__ == "__main__":
    main()
