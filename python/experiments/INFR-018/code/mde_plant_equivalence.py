"""Prove the MDE plant in use is the plant design §3.4 specifies (QA I-13).

§3.4 asks for the bite/MDE curve to be traced by *injecting* a synthetic effect
into the sessions — "widen post-break drift in the break direction by
s·IB_width" — while ``common.mde_curve`` sweeps ``s`` on the finished day-level
contrast series. QA flagged the gap three runs running, and it matters now
because the headline read on the HYP-I2 table is that the winner's contrast sits
below its own floor.

The two are the same plant, and this script demonstrates it in two legs rather
than asserting it:

  LEG 1 (session level, one symbol).  A session contributes an asymmetry only if
    it breaks: ``asym = MFE/IB_width − MAE/IB_width``, and both excursions are
    null when ``break_ts`` is null. Widening post-break drift by ``s·IB_width``
    adds ``s·IB_width`` to MFE and nothing to MAE, so every contributing session's
    ``asym`` rises by exactly ``s``.

  LEG 2 (pooled, the winner cell).  Adding a constant ``s`` to every real-arm
    session raises each day's real-arm median by exactly ``s`` and leaves the
    control arm untouched, so the paired day-contrast series is exactly
    ``contrast + s``.

What is NOT equivalent, and is a deliberate choice rather than an oversight:
``mde_curve`` re-centres the series before adding ``s``
(``values − median(values) + s``). That asks *what effect size could a sample
with this noise structure detect*, which is the MDE. Sweeping ``values + s``
would ask what happens when ``s`` is piled on top of whatever effect the data
already contains, which is not a detectability floor. The re-centring is
recorded in design §3.4 rather than left implicit.

Usage
-----
    python python/experiments/INFR-018/code/mde_plant_equivalence.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    SEED_PSEUDO_DAILY,
    SEED_PSEUDO_FUND,
    paired_day_contrast,
    realise_universe,
    write_json,
)
from hyp_i2_anchor_race import (  # noqa: E402
    MDE_GRID,
    RACE_COLUMNS,
    _anchors_for,
    _restrict_to_members,
    run_jobs,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.sigbar.fences import assert_frozen_inputs, load_bars, repo_root  # noqa: E402
from xen.sigbar.sessions import (  # noqa: E402
    CANDIDATE_ANCHORS,
    N_PSEUDO,
    assert_no_fixed_points,
    attach_sessions,
    pseudo_offsets,
    pseudo_spec,
    session_breaks,
)

BAND = "DESIGN"
TOL = 1e-9


def leg1_session_level(symbol: str, anchor_id: str, ib_minutes: int) -> dict:
    """Drift the post-break PATH by s·IB_width and re-invoke ``session_breaks``.

    The plant moves OHLC on bars strictly after ``break_ts`` (break detection
    cannot change — the drift is post-break), then MFE/MAE/asym are whatever
    ``session_breaks`` computes. Re-implementing those formulas here would still
    "confirm" if the library moved (QA I-65). Adding the drift to ``mfe``
    directly is arithmetic on an identity and proves nothing (QA run 6, I-48).
    """
    root = repo_root()
    bars = load_bars(symbol, BAND, root=root).select(RACE_COLUMNS)
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == anchor_id)
    anchors = _anchors_for(spec, BAND)
    sess = session_breaks(bars, anchors, ib_minutes)
    broken = sess.filter(pl.col("asym").is_not_null())
    # Map each bar to its session's break so the plant is strictly post-break.
    break_map = broken.select("anchor_ts", "break_ts", "break_side", "ib_width")
    rows = []
    for s in MDE_GRID:
        # Bars with no break stay untouched; bars strictly after break_ts shift
        # by s·W·side. Then re-invoke session_breaks so MFE/MAE come from the
        # library, not a re-implementation (I-65).
        attached = attach_sessions(bars, anchors, ib_minutes)
        joined = attached.join(
            break_map, on="anchor_ts", how="left"
        ).with_columns(
            pl.when(
                pl.col("break_ts").is_not_null()
                & (pl.col("OpenTime") > pl.col("break_ts"))
            )
            .then(s * pl.col("ib_width") * pl.col("break_side"))
            .otherwise(0.0)
            .alias("_drift")
        ).with_columns(
            (pl.col("Open") + pl.col("_drift")).alias("Open"),
            (pl.col("High") + pl.col("_drift")).alias("High"),
            (pl.col("Low") + pl.col("_drift")).alias("Low"),
            (pl.col("Close") + pl.col("_drift")).alias("Close"),
        )
        planted_sess = session_breaks(
            joined.select(RACE_COLUMNS), anchors, ib_minutes
        ).filter(pl.col("asym").is_not_null())
        # Align on anchor_ts so the delta is per-session, not row-order.
        paired = broken.select("anchor_ts", "asym").join(
            planted_sess.select("anchor_ts", pl.col("asym").alias("asym_planted")),
            on="anchor_ts",
            how="inner",
        )
        delta = (paired["asym_planted"] - paired["asym"]).to_numpy()
        rows.append({
            "s_drift": s,
            "mean_asym_shift": float(np.mean(delta)),
            "max_abs_deviation_from_2s": float(np.max(np.abs(delta - 2 * s))),
            "max_abs_deviation_from_1s": float(np.max(np.abs(delta - s))),
            "n_sessions": int(broken.height),
        })
    return {
        "symbol": symbol,
        "anchor_id": anchor_id,
        "ib_minutes": ib_minutes,
        "n_sessions_with_asym": int(broken.height),
        "n_sessions_total": int(sess.height),
        "claim": "a post-break drift of s·IB_width raises MFE by s·IB_width AND lowers MAE by "
                 "s·IB_width, so asym rises by 2s — NOT s",
        "sweep": rows,
        "max_abs_deviation_from_2s": max(r["max_abs_deviation_from_2s"] for r in rows),
    }


def leg2_pooled(anchor_id: str, ib_minutes: int, workers: int) -> dict:
    """Show the pooled day-contrast series under the plant is exactly contrast + s."""
    membership, _ = realise_universe(BAND)
    symbols = sorted(membership["symbol"].unique().to_list())
    controls_by_anchor = {}
    for i, spec in enumerate(CANDIDATE_ANCHORS):
        shape = spec.sessions_per_day
        seed = (SEED_PSEUDO_FUND if shape == 3 else SEED_PSEUDO_DAILY) + i
        offs = pseudo_offsets(spec.anchor_id, shape, N_PSEUDO, seed)
        assert_no_fixed_points(spec.anchor_id, offs, shape)
        controls_by_anchor[spec.anchor_id] = {
            "seed": seed, "offsets": offs,
            "specs": [pseudo_spec(shape, o, j) for j, o in enumerate(offs)],
        }
    acc = run_jobs(
        symbols, [(anchor_id, ib_minutes, 0, True)], BAND, membership, controls_by_anchor,
        workers=workers, desc="plant-equivalence cell",
    )
    slot = acc[(anchor_id, ib_minutes, 0)]
    real = pl.concat(slot["real"])
    ctrl = pl.concat(slot["ctrl"])
    base, days = paired_day_contrast(real, ctrl, "asym")
    rows = []
    for s in MDE_GRID:
        planted = real.with_columns((pl.col("asym") + s).alias("asym"))
        vals, d2 = paired_day_contrast(planted, ctrl, "asym")
        same_days = len(d2) == len(days) and bool(np.all(d2 == days))
        rows.append({
            "s": s,
            "same_day_set": same_days,
            "max_abs_deviation_from_base_plus_s": float(np.max(np.abs(vals - (base + s)))),
        })
    return {
        "anchor_id": anchor_id,
        "ib_minutes": ib_minutes,
        "n_days": int(len(base)),
        "claim": "adding s to every real-arm session shifts the paired day-contrast series "
                 "by exactly s",
        "sweep": rows,
        "max_abs_deviation": max(r["max_abs_deviation_from_base_plus_s"] for r in rows),
    }


def main() -> int:
    import argparse
    import os

    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    args = ap.parse_args()

    frozen = assert_frozen_inputs()
    race = __import__("json").loads(
        (repo_root() / "python/experiments/INFR-018/results/hyp_i2_anchor_race_DESIGN.json")
        .read_text()
    )
    top = race["ranked"][0]

    leg1 = leg1_session_level("BTCUSDT", top["anchor_id"], top["ib_minutes"])
    leg2 = leg2_pooled(top["anchor_id"], top["ib_minutes"], args.workers)
    ok = leg1["max_abs_deviation_from_2s"] < TOL and leg2["max_abs_deviation"] < TOL

    write_json(
        "mde_plant_equivalence.json",
        {
            "purpose": "pin the units of the MDE plant: what a drift plant of size s does to "
                       "the contrast the curve is swept in (QA I-13 / I-48)",
            "cell": {"anchor_id": top["anchor_id"], "ib_minutes": top["ib_minutes"]},
            "frozen_inputs": {"baselines_sha256": frozen.baselines_sha256},
            "tolerance": TOL,
            "leg1_session_level": leg1,
            "leg2_pooled_day_contrast": leg2,
            "measured_relation": "a post-break drift of s·IB_width shifts the paired day "
                                 "contrast by 2s",
            "units_of_the_published_mde": "CONTRAST units — the same units as E. The curve is "
                                          "swept directly on the contrast, so `mde` and "
                                          "`below_own_mde` compare like with like. The "
                                          "equivalent drift plant is HALF the published floor.",
            "relation_holds": ok,
            "recentring": "mde_curve sweeps values − median(values) + u. The re-centring is a "
                          "deliberate choice: it makes the curve a DETECTABILITY floor at the "
                          "realised n rather than a sweep piled on top of the effect already "
                          "in the data.",
            "supersedes": "the 2026-07-21 version of this artifact, whose leg 1 added the plant "
                          "to the mfe column and then verified asym had moved — arithmetic on "
                          "an identity, and wrong by a factor of 2 (QA run 6, I-48)",
            "scope": "validity attestation — not a value read, not evidence of anything working",
        },
    )
    print(f"leg1 (drift → 2s) max deviation {leg1['max_abs_deviation_from_2s']:.3e}")
    print(f"       vs the 1s claim         {min(r['max_abs_deviation_from_1s'] for r in leg1['sweep']):.3e}")
    print(f"leg2 (asym +u → contrast +u)   {leg2['max_abs_deviation']:.3e}")
    print("RELATION CONFIRMED: drift s ⇒ contrast 2s" if ok else "RELATION NOT CONFIRMED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
