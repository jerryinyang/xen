"""SPDR-009 / xen.sigbar.absorb regression suite.

Covers:
  * frozen-input hash re-verification (INFR-017/018/020)
  * D1 golden traces GT-1…GT-4 (designer-pinned; do not regenerate)
  * GT-5 raise conditions (fence, COMPLETE, D6.3, S1, fixed points, …)
  * arm assignment three-way boundary (GT-4 pattern)
  * fixed-H path-swap + bite units in bps
  * no local accounting in experiment dir
  * shared LTF helpers are imported, not reimplemented
"""

from __future__ import annotations

import inspect
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.estimand_validation import check_no_local_accounting
from xen.sigbar import absorb, ltf
from xen.sigbar.fences import HOLDOUT_START, load_bars, repo_root

ROOT = repo_root()
GT_PATH = ROOT / "python/experiments/SPDR-009/design_derivations/gt_output.json"

# Designer-pinned SOL golden traces (design §8).
GT_KEYS = {
    "GT-1": ("2022-12-28 03:27:00", "S9", "IB_LOW"),
    "GT-2": ("2022-12-29 01:24:00", "S9", "PRIOR_SESSION_LOW"),
    "GT-3": ("2022-12-26 23:34:00", "MIRROR", "PRIOR_VAL"),
    "GT-4": ("2022-11-12 22:08:00", "BASE", "IB_LOW"),
}


def _gt_events() -> dict:
    return json.loads(GT_PATH.read_text())["events"]["SOLUSDT"]


def _find_gt(event_ts: str) -> dict:
    for e in _gt_events():
        if e["event_ts"] == event_ts:
            return e
    raise KeyError(event_ts)


# --------------------------------------------------------------------------- #
# Frozen pins
# --------------------------------------------------------------------------- #


def test_assert_spdr009_frozen_inputs_matches_contracted_hashes():
    fi = absorb.assert_spdr009_frozen_inputs()
    assert fi.baselines_1m_sha256.startswith("1b7244c8")
    assert fi.registry_pin_sha256.startswith("5c386984")
    assert fi.infr020_pins_sha256 == absorb.INFR020_PINS_SHA256
    for name, expect in absorb.INFR020_ARTIFACT_SHA256.items():
        assert fi.infr020_artifacts[name] == expect


def test_seasonal_baselines_mtf_hash_matches_amendment_22():
    from xen.sigbar.fences import sha256_file

    p = ROOT / "python/experiments/INFR-020/results/seasonal_baselines_mtf.parquet"
    assert p.exists()
    assert sha256_file(p) == absorb.INFR020_ARTIFACT_SHA256["seasonal_baselines_mtf.parquet"]


def test_no_local_accounting_in_spdr009_screen_dir():
    check_no_local_accounting(str(ROOT / "python/experiments/SPDR-009/screen_code"))


# --------------------------------------------------------------------------- #
# Shared imports — never reimplement
# --------------------------------------------------------------------------- #


def test_absorb_imports_shared_ltf_helpers_not_redefined():
    src = Path(inspect.getfile(absorb)).read_text()
    for name in (
        "absorb_candidate_predicate",
        "structural_levels_1m",
        "assign_candidate_sessions",
        "available_levels_for_candidates",
    ):
        assert f"def {name}" not in src, f"absorb must not redefine {name}"
        assert name in src
        assert getattr(ltf, name) is not None


# --------------------------------------------------------------------------- #
# Arm assignment unit
# --------------------------------------------------------------------------- #


def test_arm_label_three_way_boundary():
    # GT-4 pattern: huge |Δ| but |signed_score| < dr_hi → BASE
    assert absorb._arm_label(26.0, -1.2096, d_hi=4.85, dr_hi=1.3778) == "BASE"
    assert absorb._arm_label(9.88, 1.50, d_hi=4.85, dr_hi=1.3778) == "S9"
    assert absorb._arm_label(25.5, -1.38, d_hi=4.85, dr_hi=1.3778) == "MIRROR"


def test_mid_range_score_allows_mirror_arm():
    """MID_RANGE uses raw delta_ratio_resid so MIRROR is reachable (QA-6 I-1)."""
    # signed_score = raw dr (no into projection)
    assert absorb._arm_label(10.0, -1.5, d_hi=4.85, dr_hi=1.3778) == "MIRROR"
    assert absorb._arm_label(10.0, 1.5, d_hi=4.85, dr_hi=1.3778) == "S9"


def test_into_side_tie_break_uses_prior_close():
    assert absorb._into_side(10.0, 10.0, 9.5) == 1
    assert absorb._into_side(10.0, 10.0, 10.5) == -1
    assert absorb._into_side(10.0, 10.0, 10.0) == 0


# --------------------------------------------------------------------------- #
# Golden traces (D1, ib_width zone — designer-pinned)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def sol_d1_events_ib():
    """Build D1 SOL events under the original ib_width τ=0.25 zone (GT continuity)."""
    absorb.assert_spdr009_frozen_inputs()
    ev = absorb.build_contact_events(
        "SOLUSDT",
        "DESIGN",
        "D1",
        tau=0.25,
        zone_mode="ib_width",
        pool_mode="P",
        nearest_only=False,  # keep multi-level so GT level_kind can match
    )
    if ev.height == 0:
        pytest.skip("no SOL D1 events under ib_width τ=0.25")
    bars = load_bars("SOLUSDT", "DESIGN")
    scored = absorb.evaluate_outcomes_1m(bars, ev)
    return scored


def _match_row(scored: pl.DataFrame, event_ts: str, level_kind: str) -> dict | None:
    ts = datetime.fromisoformat(event_ts)
    hit = scored.filter(
        (pl.col("event_ts") == ts) & (pl.col("level_kind") == level_kind)
    )
    if hit.height == 0:
        # try without level filter
        hit = scored.filter(pl.col("event_ts") == ts)
    if hit.height == 0:
        return None
    return hit.row(0, named=True)


@pytest.mark.parametrize("gt_id,event_ts,arm,level_kind", [
    ("GT-1", "2022-12-28 03:27:00", "S9", "IB_LOW"),
    ("GT-2", "2022-12-29 01:24:00", "S9", "PRIOR_SESSION_LOW"),
    ("GT-3", "2022-12-26 23:34:00", "MIRROR", "PRIOR_VAL"),
    ("GT-4", "2022-11-12 22:08:00", "BASE", "IB_LOW"),
])
def test_golden_trace_arm_and_returns(sol_d1_events_ib, gt_id, event_ts, arm, level_kind):
    pinned = _find_gt(event_ts)
    row = _match_row(sol_d1_events_ib, event_ts, level_kind)
    assert row is not None, f"{gt_id}: event not found at {event_ts} / {level_kind}"
    assert row["arm"] == arm == pinned["arm"], f"{gt_id} arm mismatch"
    assert int(row["into_side"]) == int(pinned["into_side"])
    assert abs(float(row["signed_score"]) - float(pinned["signed_score"])) < 1e-4
    # returns within tight tolerance of designer-pinned values
    assert abs(float(row["ret_bps_H5"]) - float(pinned["ret_bps_H5"])) < 1e-3
    assert abs(float(row["ret_bps_H10"]) - float(pinned["ret_bps_H10"])) < 1e-3
    # entry is next 1m open
    assert row["entry_ts"] == datetime.fromisoformat(pinned["entry_ts"])


# --------------------------------------------------------------------------- #
# GT-5 raise conditions
# --------------------------------------------------------------------------- #


def test_gt5a_band_raises_on_test_or_holdout_path():
    with pytest.raises((RuntimeError, ValueError)):
        load_bars("SOLUSDT", "TEST")


def test_gt5b_confirm_before_freeze_raises(tmp_path):
    with pytest.raises(RuntimeError, match="CONFIRM-before-freeze|pool_cuts"):
        absorb.assert_confirm_freeze_ready(tmp_path)


def test_gt5c_frozen_hash_mismatch_raises(monkeypatch, tmp_path):
    # Point INFR-020 pins path at a tampered file via monkeypatch of sha256_file path
    # Simpler: corrupt expectation by calling with wrong registry constant.
    bad = absorb.REGISTRY_PIN_SHA256
    monkeypatch.setattr(absorb, "REGISTRY_PIN_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="FROZEN INPUT MISMATCH"):
        absorb.assert_spdr009_frozen_inputs()
    monkeypatch.setattr(absorb, "REGISTRY_PIN_SHA256", bad)


def test_gt5d_per_level_delta_raises():
    with pytest.raises(RuntimeError, match="PER-LEVEL DELTA"):
        from xen.sigbar.fences import assert_no_per_level_delta

        assert_no_per_level_delta(pl.Series("delta_at_level", [1.0]))


def test_gt5g_derangement_fixed_point_raises():
    # n=1 cannot be deranged
    from xen.sigbar.trap import derange

    with pytest.raises(ValueError):
        derange(1, np.random.default_rng(0))


def test_gt5h_s1_gate_refusal():
    with pytest.raises(RuntimeError, match="S1-GATE"):
        absorb.refuse_s1_as_qualifier()


def test_gt5j_ltf_outcome_path_raises():
    with pytest.raises(RuntimeError, match="D6.3"):
        absorb.assert_no_ltf_outcome_path(5, context="planted")


def test_gt5k_ah_edge_bearing_raises():
    with pytest.raises(RuntimeError, match="A-H NON-EDGE"):
        absorb.assert_not_edge_bearing_operational("A-H1", as_edge=True)


def test_gt5l_non_complete_candidate_raises():
    # plant a non-COMPLETE frame into absorb_candidate_predicate with require_complete
    bars = pl.DataFrame(
        {
            "OpenTime": [datetime(2022, 1, 1, 0, 0)],
            "volume_resid": [10.0],
            "range_resid": [-2.0],
            "window_class": ["NO_TRADE_PARTIAL"],
            "traded_fraction": [0.5],
        }
    )
    th = {"volume": {"high": 1.0}, "range": {"low": -1.0}}
    # predicate filters COMPLETE only — returns empty, does not raise by itself
    out = ltf.absorb_candidate_predicate(bars, th, require_complete=True)
    assert out.height == 0
    # build path that finds non-COMPLETE after complete_only=False would raise at fence
    with pytest.raises(RuntimeError, match="traded_fraction|COMPLETE|CANDIDATE"):
        bad = bars.with_columns(pl.lit("COMPLETE").alias("window_class"))
        ltf.absorb_candidate_predicate(bad, th, require_complete=True)


def test_gt5e_ib_edge_before_complete_is_unavailable():
    """GT-5(e): IB edges are not available before IB wall-clock completes."""
    from xen.sigbar.ltf import available_levels_for_candidates

    anchor = datetime(2022, 1, 2, 13, 30)
    cand = pl.DataFrame(
        {
            "OpenTime": [anchor + __import__("datetime").timedelta(minutes=5)],
            "Close": [100.0],
            "anchor_ts": [anchor],
            "mins_since_close": [6],  # < 15
        }
    )
    levels = pl.DataFrame(
        {
            "anchor_ts": [anchor],
            "level_price": [101.0],
            "level_kind": ["IB_HIGH"],
            "available_mins_since": [15],
            "formed_ts": [anchor + __import__("datetime").timedelta(minutes=2)],
        }
    )
    pairs = available_levels_for_candidates(cand, levels)
    assert pairs.height == 1
    assert not pairs["level_available"].item()
    assert pairs["excluded_not_yet_formed"].item()


def test_gt5f_prior_levels_formed_before_consumer_session():
    """GT-5(f): PRIOR_* levels carry formed_ts from the prior closed session."""
    from xen.sigbar.ltf import structural_levels_1m, assign_candidate_sessions
    import datetime as dt

    prev = dt.datetime(2022, 1, 1, 13, 30)
    cur = dt.datetime(2022, 1, 2, 13, 30)
    nxt = dt.datetime(2022, 1, 3, 13, 30)
    anchors = pl.DataFrame(
        {"anchor_ts": [prev, cur], "session_end": [cur, nxt]}
    )
    # prior session bars only
    bars = pl.DataFrame(
        {
            "OpenTime": [prev + dt.timedelta(minutes=i) for i in range(60)],
            "Open": [100.0] * 60,
            "High": [101.0 + (i == 10) for i in range(60)],
            "Low": [99.0 - (i == 20) for i in range(60)],
            "Close": [100.0] * 60,
            "Volume": [1.0] * 60,
            "BuyVolume": [0.6] * 60,
            "SellVolume": [0.4] * 60,
            "NTrades": [1] * 60,
        }
    )
    levels = structural_levels_1m(
        bars, anchors, 15, only_anchors={cur}, include_profile=False
    )
    prior = levels.filter(pl.col("level_kind").str.starts_with("PRIOR_"))
    assert prior.height >= 2
    assert prior["formed_ts"].null_count() == 0
    assert (prior["formed_ts"] < cur).all()


def test_gt5i_matched_random_own_session_raises():
    """GT-5(i): donor entry inside the event's own HTF session must raise.

    The event's declared session window is widened to 30 days so that donor
    anchors (daily) provably fall inside it — the raise path is exercised, not
    merely reachable in principle.
    """
    import datetime as dt

    bars = load_bars("SOLUSDT", "DESIGN")
    ts = bars["OpenTime"].to_list()
    entry = ts[50_000]
    event = ts[49_999]
    anchor = entry - dt.timedelta(minutes=100)
    events = pl.DataFrame(
        {
            "symbol": ["SOLUSDT"],
            "pair_id": ["D1"],
            "band": ["DESIGN"],
            "event_ts": [event],
            "entry_ts": [entry],
            "anchor_ts": [anchor],
            "session_end": [anchor + dt.timedelta(days=30)],
            "side": [1],
            "into_side": [-1],
            "ltf_minutes": [1],
            "arm": ["S9"],
            "signed_score": [1.5],
            "level_kind": ["IB_LOW"],
            "level_price": [1.0],
            "zone_scale": [1.0],
            "zone_mode": ["ib_width"],
            "tau": [0.25],
        }
    )
    from xen.sigbar.sessions import anchor_table
    from xen.sigbar.spine import anchor_spec

    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = anchor_table(anchor_spec(), lo, hi)
    with pytest.raises(RuntimeError, match="MATCHED_RANDOM DISJOINT FAIL"):
        absorb.matched_random_timing(bars, events, anchors, n_donors=30, seed=1)


def test_matched_random_cross_session_donors_do_not_raise():
    """Companion to GT-5(i): a normal one-day session yields only outside donors."""
    import datetime as dt

    bars = load_bars("SOLUSDT", "DESIGN")
    ts = bars["OpenTime"].to_list()
    entry = ts[50_000]
    anchor = entry - dt.timedelta(minutes=100)
    events = pl.DataFrame(
        {
            "symbol": ["SOLUSDT"],
            "pair_id": ["D1"],
            "band": ["DESIGN"],
            "event_ts": [ts[49_999]],
            "entry_ts": [entry],
            "anchor_ts": [anchor],
            "session_end": [anchor + dt.timedelta(days=1)],
            "side": [1],
            "into_side": [-1],
            "ltf_minutes": [1],
            "arm": ["S9"],
            "signed_score": [1.5],
            "level_kind": ["IB_LOW"],
            "level_price": [1.0],
            "zone_scale": [1.0],
            "zone_mode": ["ib_width"],
            "tau": [0.25],
        }
    )
    from xen.sigbar.sessions import anchor_table
    from xen.sigbar.spine import anchor_spec

    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = anchor_table(anchor_spec(), lo, hi)
    out = absorb.matched_random_timing(bars, events, anchors, n_donors=10, seed=3)
    # The control must actually resolve donors — an empty T4 arm silently voids
    # soil leg (ii) of the §4 conjunction (QA-10 I-1).
    assert out.height > 0, "matched-random control produced no usable donors"
    assert "ret_bps_H10" in out.columns
    assert out["ret_bps_H10"].drop_nulls().len() == out.height
    assert (out["src_event_ts"] == events["event_ts"][0]).all()
    inside = out.filter(
        (pl.col("entry_ts") >= anchor)
        & (pl.col("entry_ts") < anchor + dt.timedelta(days=1))
    )
    assert inside.height == 0


def test_session_remainder_column_emitted_when_session_end_present():
    bars = load_bars("SOLUSDT", "DESIGN")
    ts = bars["OpenTime"].to_list()
    event, entry = ts[10_000], ts[10_001]
    sess_end = ts[10_001 + 120]  # ~2h later on contiguous span
    # find a real later timestamp ~2h if contiguous
    events = pl.DataFrame(
        {
            "symbol": ["SOLUSDT"],
            "pair_id": ["D1"],
            "band": ["DESIGN"],
            "event_ts": [event],
            "entry_ts": [entry],
            "anchor_ts": [event],
            "session_end": [entry + __import__("datetime").timedelta(hours=2)],
            "side": [1],
            "into_side": [-1],
            "ltf_minutes": [1],
            "arm": ["S9"],
            "signed_score": [1.0],
            "level_kind": ["IB_LOW"],
            "level_price": [1.0],
            "zone_scale": [1.0],
            "zone_mode": ["prior_session_range"],
            "tau": [0.25],
        }
    )
    out = absorb.evaluate_outcomes_1m(bars, events, holds=(5, 10))
    assert out.height == 1
    assert "ret_bps_session" in out.columns
    # may or may not clear contiguity; column must exist
    assert "session_remainder_ok" in out.columns


def test_session_remainder_survives_late_first_non_null():
    """QA-9 I-1: >100 events with no remainder followed by one with a remainder.

    The session columns stay None until an event clears the contiguity guard, so
    a short schema-inference window typed them Null and then failed on the first
    real float. Sample membership must not depend on batch ordering.
    """
    import datetime as dt

    bars = load_bars("SOLUSDT", "DESIGN")
    ts = bars["OpenTime"].to_list()
    rows = []
    for i in range(120):
        e, en = ts[10_000 + 2 * i], ts[10_001 + 2 * i]
        rows.append(
            {
                "symbol": "SOLUSDT", "pair_id": "D1", "band": "DESIGN",
                "event_ts": e, "entry_ts": en, "anchor_ts": e,
                "session_end": en,  # no remainder
                "side": 1, "into_side": -1, "ltf_minutes": 1, "arm": "BASE",
                "signed_score": 0.1, "level_kind": "IB_LOW", "level_price": 1.0,
                "zone_scale": 1.0, "zone_mode": "ib_width", "tau": 0.25,
            }
        )
    e, en = ts[40_000], ts[40_001]
    rows.append(
        {
            "symbol": "SOLUSDT", "pair_id": "D1", "band": "DESIGN",
            "event_ts": e, "entry_ts": en, "anchor_ts": e,
            "session_end": en + dt.timedelta(hours=2),  # real remainder
            "side": 1, "into_side": -1, "ltf_minutes": 1, "arm": "S9",
            "signed_score": 1.5, "level_kind": "IB_LOW", "level_price": 1.0,
            "zone_scale": 1.0, "zone_mode": "ib_width", "tau": 0.25,
        }
    )
    out = absorb.evaluate_outcomes_1m(
        bars, pl.DataFrame(rows, infer_schema_length=None), holds=(5, 10)
    )
    assert out.height == 121
    assert out["session_remainder_ok"].sum() == 1
    assert out["ret_bps_session"].drop_nulls().len() == 1


def test_bare_level_matches_per_event_not_global_sample():
    """T5 draws are matched to pool events (level_kind × side × phase), not a global cap."""
    absorb.assert_spdr009_frozen_inputs()
    pool = absorb.build_contact_events(
        "SOLUSDT", "DESIGN", "D1", tau=0.25, zone_mode="ib_width", pool_mode="P"
    )
    if pool.height < 3:
        pytest.skip("thin pool")
    pool = absorb.apply_refractory(pool).head(5)
    bare = absorb.bare_level_touch_events(
        "SOLUSDT",
        "DESIGN",
        "D1",
        events=pool,
        tau=0.25,
        zone_mode="ib_width",
        n_per_event=5,
    )
    if bare.height == 0:
        pytest.skip("no bare donors for sample")
    assert "src_event_ts" in bare.columns
    # each source event contributes at most n_per_event rows
    counts = bare.group_by("src_event_ts").len()
    assert int(counts["len"].max()) <= 5


# --------------------------------------------------------------------------- #
# Path swap + derangement
# --------------------------------------------------------------------------- #


def _synth_arm(n: int, mean: float, label: str, seed: int, days: int = 60) -> pl.DataFrame:
    import datetime as dt

    rng = np.random.default_rng(seed)
    base = dt.datetime(2022, 6, 1)
    return pl.DataFrame(
        {
            "day": [base + dt.timedelta(days=int(i % days)) for i in range(n)],
            "ret_bps_H10": rng.normal(mean, 20.0, n),
            "arm": [label] * n,
            "symbol": ["SYNTH"] * n,
        }
    )


def test_mde_strictly_positive_when_raw_edge_already_material():
    """QA-12 I-1: an uncentred sweep returns MDE=0 once the raw edge is material.

    MDE must measure the arm's RESOLUTION, not the observed effect — otherwise
    §5's `effect >= its own MDE` is circular and CF* would plant 0 bps, i.e.
    calibrate on the observed (possibly leaking) edge.
    """
    treat = _synth_arm(400, 40.0, "S9", seed=0)
    base = _synth_arm(1200, 0.0, "BASE", seed=1)
    raw = absorb.contrast_day_clustered(treat, base, ret_col="ret_bps_H10")
    assert raw["excludes_zero"], "fixture must have an already-material raw edge"
    m = absorb.plant_mde_curve(treat, base, ret_col="ret_bps_H10")
    assert m["mde_bps"] is not None and m["mde_bps"] > 0
    assert m["centred_on_observed"] is True
    assert m["observed_contrast"] == pytest.approx(raw["contrast"], abs=1e-6)


def test_cf_star_refuses_zero_or_absent_mde():
    """QA-12 I-1: a zero/absent plant would calibrate CF* on the observed edge."""
    ev = pl.concat(
        [_synth_arm(50, 10.0, "S9", seed=2), _synth_arm(200, 0.0, "BASE", seed=3)]
    )
    for bad in (0.0, None, -1.0):
        cf = absorb.calibrate_cf_star({}, ev, mde_bps=bad, n_seeds=1)
        assert cf["cf_star"] is None
        assert cf["status"] == "UNDERIVABLE"
    # and it never substitutes the inherited prior
    assert cf.get("prior_cf") == 0.25
    assert cf.get("cf_star") != 0.25


def test_label_band_all_branches_reachable():
    """QA-12 I-2: SUPPORTED must stay reachable — it is soil leg (i)."""
    assert absorb.label_band(37.6, [30.0, 43.8], 2.0) == "SUPPORTED"
    assert absorb.label_band(37.6, [30.0, 43.8], 0.0) == "SUPPORTED"
    assert absorb.label_band(2.0, [1.0, 3.0], 10.0) == "SUGGESTIVE"
    assert absorb.label_band(-9.0, [-15.0, -3.0], 5.0) == "CONTRADICTED"
    assert absorb.label_band(1.0, [-4.0, 6.0], 10.0) == "WASH"
    assert absorb.label_band(None, None, None) == "UNPOWERED"
    assert absorb.label_band(5.0, None, 2.0) == "UNPOWERED"
    assert absorb.label_band(5.0, [-1.0, 11.0], None) == "UNPOWERED"


def test_label_band_mde_missing_preserves_interval_sign():
    """QA-14: MDE absence must not hide a measured negative interval."""
    assert absorb.label_band(-6.0, [-9.0, -3.0], None) == "CONTRADICTED"
    assert absorb.label_band(6.0, [3.0, 9.0], None) == "SUGGESTIVE"
    assert absorb.label_band(6.0, [-3.0, 9.0], None) == "UNPOWERED"
    assert absorb.label_band(6.0, [None, None], 5.0) == "UNPOWERED"
    assert absorb.label_band(6.0, [9.0, 3.0], 5.0) == "UNPOWERED"


def test_mde_constant_shift_optimization_matches_grid_sweep(monkeypatch):
    """The one-bootstrap MDE is identical to an explicit constant-plant sweep."""
    treat = _synth_arm(80, 2.0, "S9", seed=20, days=20)
    base = _synth_arm(160, 0.0, "BASE", seed=21, days=20)
    grid = np.array([0.0, 2.0, 4.0, 6.0, 8.0])

    real_contrast = absorb.contrast_day_clustered
    observed = real_contrast(treat, base, ret_col="ret_bps_H10")
    centred = treat.with_columns(
        (pl.col("ret_bps_H10") - observed["contrast"]).alias("ret_bps_H10")
    )
    expected = None
    for plant in grid:
        planted = centred.with_columns(
            (pl.col("ret_bps_H10") + float(plant)).alias("ret_bps_H10")
        )
        row = real_contrast(planted, base, ret_col="ret_bps_H10")
        if row.get("ci") and row["ci"][0] > 0:
            expected = float(plant)
            break

    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_contrast(*args, **kwargs)

    monkeypatch.setattr(absorb, "contrast_day_clustered", counted)
    actual = absorb.plant_mde_curve(
        treat, base, ret_col="ret_bps_H10", grid=grid
    )
    assert actual["mde_bps"] == expected
    assert calls == 2  # observed contrast + one centred bootstrap


def test_t2_monotone_plant_publishes_real_resolution():
    """QA-15: T2 MDE must come from a known plant, not null quantiles."""
    rng = np.random.default_rng(3)
    n = 120
    ev = pl.DataFrame(
        {
            "signed_score": np.linspace(-2.0, 2.0, n),
            "ret_bps_H10": rng.normal(0.0, 8.0, n),
        }
    )
    result = absorb.signed_score_plant_mde_curve(
        ev,
        ret_col="ret_bps_H10",
        n_seeds=40,
        grid=np.arange(0.0, 10.1, 1.0),
    )
    assert result["mde_rho"] is not None and result["mde_rho"] > 0
    assert result["mde_plant_bps_per_score_sd"] > 0
    assert abs(result["centred_rho"]) < 0.01
    assert result["zero_fixed_points_asserted"] is True
    chosen = result["curve"][-1]
    assert chosen["planted_rho"] > chosen["critical_rho_p95"]
    assert chosen["one_sided_p"] <= 0.05
    assert "deranged_rho_ci" in chosen


def test_label_band_imprecise_cell_is_not_a_null():
    """QA-13: |effect| >= MDE with a zero-spanning CI had NO defined band.

    It must not read as WASH (the powered-null cell) — a large point estimate
    cannot support "nothing is there" (B-5) — nor as UNPOWERED, which asserts
    MDE > |effect|. AMENDMENT-30 gives it its own band with non-contributing
    closure semantics.
    """
    assert absorb.label_band(12.0, [-4.0, 20.0], 1.0) == "IMPRECISE"
    assert absorb.label_band(-12.0, [-20.0, 4.0], 1.0) == "IMPRECISE"
    # boundary: exactly at the MDE is IMPRECISE, just below it is WASH
    assert absorb.label_band(10.0, [-5.0, 25.0], 10.0) == "IMPRECISE"
    assert absorb.label_band(9.99, [-5.0, 25.0], 10.0) == "WASH"
    # the decision table is exhaustive — no input yields an undefined label
    valid = {"UNPOWERED", "CONTRADICTED", "SUPPORTED", "SUGGESTIVE", "WASH", "IMPRECISE"}
    for eff in (-20.0, -1.0, 0.0, 1.0, 20.0):
        for ci in ([-30.0, -5.0], [-5.0, 5.0], [5.0, 30.0], None):
            for mde in (None, 0.0, 2.0, 50.0):
                assert absorb.label_band(eff, ci, mde) in valid


def test_derange_scores_global_zero_fixed_points():
    ev = pl.DataFrame(
        {
            "signed_score": np.linspace(-2, 2, 40),
            "symbol": ["SOLUSDT"] * 40,
        }
    )
    out, cov = absorb.derange_scores_global(ev, seed=7)
    assert cov["fixed_point_rate"] == 0.0
    assert out.height == 40
    # index derangement: not identical permutation of positions for unique values
    assert not np.array_equal(
        out["signed_score"].to_numpy(), ev["signed_score"].to_numpy()
    )


def test_path_swap_fixed_h_preserves_entry_and_changes_outcome():
    bars = load_bars("SOLUSDT", "DESIGN")
    # synthetic two events with real entry timestamps on the bar grid
    ts = bars["OpenTime"].to_list()
    # pick two well-separated minutes mid-sample; entry = event + 1m
    ev0, en0 = ts[10_000], ts[10_001]
    ev1, en1 = ts[20_000], ts[20_001]
    events = pl.DataFrame(
        {
            "symbol": ["SOLUSDT", "SOLUSDT"],
            "pair_id": ["D1", "D1"],
            "band": ["DESIGN", "DESIGN"],
            "event_ts": [ev0, ev1],
            "entry_ts": [en0, en1],
            "anchor_ts": [ev0, ev1],
            "session_end": [en0, en1],
            "side": [1, -1],
            "into_side": [-1, 1],
            "ltf_minutes": [1, 1],
            "arm": ["S9", "BASE"],
            "signed_score": [1.5, 0.1],
            "level_kind": ["IB_LOW", "IB_HIGH"],
            "level_price": [1.0, 2.0],
            "zone_scale": [1.0, 1.0],
            "zone_mode": ["ib_width", "ib_width"],
            "tau": [0.25, 0.25],
        }
    )
    raw = absorb.evaluate_outcomes_1m(bars, events, holds=(10,))
    assert raw.height == 2
    sw, cov = absorb.outcome_path_swap_fixed_h(bars, raw, hold_ltf=10, seed=1)
    assert cov["n_input"] == raw.height
    assert sw.height >= 1
    bite = absorb.path_swap_bite_bps(sw)
    assert "corr" in bite
    # bite uses bps of entry, not IB-normalised
    assert "mfe_bps" in sw.columns
    assert "donor_mfe_bps" in sw.columns


# --------------------------------------------------------------------------- #
# Usable universe + cost floor
# --------------------------------------------------------------------------- #


def test_usable_universe_option_a_floors():
    d1 = absorb.usable_universe("D1")
    d2 = absorb.usable_universe("D2")
    d4 = absorb.usable_universe("D4")
    assert d1["n_usable"] == 194
    assert d2["n_usable"] == 72
    assert d4["n_usable"] == 31


def test_cost_floor_audited_symbols_near_design_table():
    # design §6.1 D1 H=10: SOL ≈ 11.748
    fl = absorb.cost_floor_bps("SOLUSDT", hold_hours=10 / 60)
    assert fl["total_bps"] == pytest.approx(11.748, abs=0.05)
    assert fl["fee_rt_bps"] == pytest.approx(11.0, abs=0.01)
    assert fl["spread_label"] == "MAX_TICK_FLIP_UPPER_BOUND"


def test_hold_hours_per_pair():
    assert absorb.hold_hours_for_pair("D1", 10) == pytest.approx(10 / 60)
    assert absorb.hold_hours_for_pair("D2", 10) == pytest.approx(50 / 60)
    assert absorb.hold_hours_for_pair("D3", 10) == pytest.approx(2.5)
    assert absorb.hold_hours_for_pair("D4", 10) == pytest.approx(10.0)


# --------------------------------------------------------------------------- #
# Refractory + window hygiene
# --------------------------------------------------------------------------- #


def test_refractory_prevents_overlap_within_symbol_pair():
    base = datetime(2022, 1, 1, 12, 0)
    rows = []
    for i in range(5):
        rows.append(
            {
                "symbol": "SOLUSDT",
                "pair_id": "D1",
                "event_ts": base.replace(minute=i),
                "ltf_minutes": 1,
            }
        )
    ev = pl.DataFrame(rows)
    out = absorb.apply_refractory(ev, refractory_ltf=10)
    # first kept; next needs ≥10 min gap → only first survives in this dense block
    assert out.height == 1


def test_holdout_constant_is_sealed():
    assert HOLDOUT_START == datetime(2025, 1, 8)
