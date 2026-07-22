"""Regression tests for the INFR-018 instrument-build apparatus.

Each test pins a behaviour whose silent failure would be invisible in the
results — the class of defect INFR-017 shipped twice (an Int8 overflow that
aliased the seasonal grid; a round-trip check that compared written objects
against themselves).
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from xen.sigbar.acceptance import (
    LABEL_ACCEPTANCE,
    LABEL_TRAP,
    LABEL_UNRESOLVED,
    QUALIFY_MINUTES,
    assert_windows_disjoint,
    label_outcomes,
    race_grid,
    separation,
)
from xen.sigbar.classes import (
    LOCATED_CLASSES,
    classify,
    derive_thresholds,
    match_quality,
    residual_matched_control,
)
from xen.sigbar.fences import (
    HOLDOUT_START,
    assert_band,
    assert_no_per_level_delta,
    band_window,
    build_universe,
)
from xen.sigbar.profile import KERNELS, build_profile, poc_and_value_area, price_grid
from xen.sigbar.sessions import (
    CANDIDATE_ANCHORS,
    N_PSEUDO,
    OCCUPIED_MINUTES,
    anchor_table,
    assert_no_fixed_points,
    feasible_offsets,
    pseudo_offsets,
    session_breaks,
)


# ---------------------------------------------------------------------------
# Fences
# ---------------------------------------------------------------------------


def test_assert_band_rejects_holdout_explicitly():
    """A holdout touch must name itself, not hide inside a generic range error."""
    df = pl.DataFrame({"OpenTime": [HOLDOUT_START + dt.timedelta(minutes=1)]})
    with pytest.raises(RuntimeError, match="HOLDOUT VIOLATION"):
        assert_band(df, "DESIGN")


def test_assert_band_rejects_confirm_rows_in_design_path():
    """The CONFIRM bank must be unreachable from a DESIGN-tuning read path."""
    _, design_end = band_window("DESIGN")
    df = pl.DataFrame({"OpenTime": [design_end + dt.timedelta(minutes=1)]})
    with pytest.raises(RuntimeError, match="BAND VIOLATION"):
        assert_band(df, "DESIGN")


def test_assert_band_accepts_in_band():
    start, end = band_window("DESIGN")
    df = pl.DataFrame({"OpenTime": [start + dt.timedelta(days=1), end - dt.timedelta(minutes=1)]})
    assert_band(df, "DESIGN")


def test_per_level_delta_is_barred():
    """The family's hard ban is machine-enforced, not documented."""
    for name in ("Delta", "delta", "BuyVolume", "signed_volume"):
        with pytest.raises(RuntimeError, match="PER-LEVEL DELTA BARRED"):
            assert_no_per_level_delta(pl.Series(name, []))
    assert_no_per_level_delta(pl.Series("Volume", []))  # volume is allowed


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------


def test_universe_selection_is_causal_and_lags_one_day():
    """Turnover measured on day D must rank membership for day D+1, never day D.

    If this shifted the other way the panel would be chosen with same-day
    knowledge — a look-ahead in the universe itself, which no downstream control
    would detect.
    """
    d0 = dt.datetime(2023, 1, 1)
    daily = {
        "AAA": pl.DataFrame({"day": [d0], "turnover_usdt": [100.0], "n_bars": [1440]}),
        "BBB": pl.DataFrame({"day": [d0], "turnover_usdt": [50.0], "n_bars": [1440]}),
    }
    u = build_universe(daily, n=2)
    assert u["day"].unique().to_list() == [d0 + dt.timedelta(days=1)]
    assert u.sort("rank")["symbol"].to_list() == ["AAA", "BBB"]


def test_universe_drops_thin_days():
    """A symbol without a full trailing window is ineligible, not back-filled."""
    d0 = dt.datetime(2023, 1, 1)
    daily = {"AAA": pl.DataFrame({"day": [d0], "turnover_usdt": [100.0], "n_bars": [10]})}
    assert build_universe(daily, n=2).height == 0


def test_universe_tie_break_is_lexicographic():
    d0 = dt.datetime(2023, 1, 1)
    daily = {
        s: pl.DataFrame({"day": [d0], "turnover_usdt": [100.0], "n_bars": [1440]})
        for s in ("ZZZ", "AAA", "MMM")
    }
    u = build_universe(daily, n=2).sort("rank")
    assert u["symbol"].to_list() == ["AAA", "MMM"]


# ---------------------------------------------------------------------------
# Anchors and the destroy control
# ---------------------------------------------------------------------------


def test_equity_open_anchors_track_dst():
    """A fixed UTC offset would mis-anchor roughly half the sample."""
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN")
    tbl = anchor_table(spec, dt.datetime(2023, 1, 1), dt.datetime(2023, 8, 1))
    minutes = {t.hour * 60 + t.minute for t in tbl["anchor_ts"].to_list()}
    assert minutes == {810, 870}, minutes  # 13:30 UTC in EDT, 14:30 UTC in EST


def test_pseudo_anchors_have_zero_fixed_points_for_every_candidate():
    """L-28: a destroy that shares a slot with the real schedule only partly destroys."""
    for i, spec in enumerate(CANDIDATE_ANCHORS):
        shape = spec.sessions_per_day
        offs = pseudo_offsets(spec.anchor_id, shape, N_PSEUDO, 1234 + i)
        assert len(offs) == N_PSEUDO
        assert_no_fixed_points(spec.anchor_id, offs, shape)
        step = 1440 // shape
        for m in offs:
            implied = {(m + k * step) % 1440 for k in range(shape)}
            assert not (implied & set(OCCUPIED_MINUTES[spec.anchor_id]))


def test_pseudo_placement_succeeds_on_the_tight_eight_hourly_shape():
    """The 8-hourly arc is the tight one; rejection sampling failed here."""
    feas = feasible_offsets("A-FUND", 3)
    assert len(feas) >= N_PSEUDO
    for seed in (1, 2, 3, 999, 20180103):
        assert len(pseudo_offsets("A-FUND", 3, N_PSEUDO, seed)) == N_PSEUDO


# ---------------------------------------------------------------------------
# Session construction — the golden traces
# ---------------------------------------------------------------------------


def _synthetic_day(base: float = 100.0) -> pl.DataFrame:
    """One flat-IB day whose break and excursion are hand-computable."""
    t0 = dt.datetime(2022, 8, 1)
    rows = []
    for i in range(1440):
        if i < 65:                      # IB (first 60) then 5 quiet bars still inside it
            o = c = base
            h, l = base + 1, base - 1
        elif i == 65:                   # the break bar: closes above the IB high
            o, h, l, c = base, base + 3, base, base + 2
        elif i == 70:                   # the excursion extreme
            o, h, l, c = base + 2, base + 10, base + 1, base + 9
        else:
            o = h = l = c = base + 2
            h, l = base + 2.5, base + 1.5
        rows.append(
            {"OpenTime": t0 + dt.timedelta(minutes=i), "Open": o, "High": h, "Low": l,
             "Close": c, "Volume": 10.0, "NTrades": 5, "BuyVolume": 6.0, "SellVolume": 4.0,
             "Delta": 2.0, "Turnover": 1000.0}
        )
    return pl.DataFrame(rows)


def test_session_break_takes_the_first_close_beyond_and_excludes_its_own_bar():
    bars = _synthetic_day()
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == "A-UTC0")
    anchors = anchor_table(spec, dt.datetime(2022, 8, 1), dt.datetime(2022, 8, 3))
    out = session_breaks(bars, anchors, 60)
    row = out.filter(pl.col("anchor_ts") == dt.datetime(2022, 8, 1)).to_dicts()[0]
    assert row["ib_high"] == 101.0 and row["ib_low"] == 99.0 and row["ib_width"] == 2.0
    assert row["break_ts"] == dt.datetime(2022, 8, 1, 1, 5)
    assert row["break_side"] == 1 and row["break_close"] == 102.0
    # The break bar's own high (103) must NOT count toward the excursion; the
    # post-break extreme is 110.
    assert row["mfe"] == pytest.approx(8.0)
    assert row["mfe_norm"] == pytest.approx(4.0)


def test_ib_shift_tripwire_changes_the_boundary():
    """The future-destroy must move the sufficient statistic, not just a label."""
    bars = pl.concat([_synthetic_day(100.0), _synthetic_day(200.0).with_columns(
        pl.col("OpenTime") + pl.duration(days=1))], how="vertical")
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == "A-UTC0")
    anchors = anchor_table(spec, dt.datetime(2022, 8, 1), dt.datetime(2022, 8, 4))
    plain = session_breaks(bars, anchors, 60)
    shifted = session_breaks(bars, anchors, 60, ib_shift=1)
    d0 = dt.datetime(2022, 8, 1)
    assert plain.filter(pl.col("anchor_ts") == d0)["ib_high"].item() == 101.0
    # day 0 now carries day 1's boundary — information that did not exist yet
    assert shifted.filter(pl.col("anchor_ts") == d0)["ib_high"].item() == 201.0


# ---------------------------------------------------------------------------
# A6
# ---------------------------------------------------------------------------


def test_race_grid_is_frozen_and_balanced():
    grid = race_grid()
    ids = [d.disc_id for d in grid]
    assert len(ids) == len(set(ids)), "duplicate discriminator id"
    assert sum(1 for d in grid if d.flow_augmented) == sum(1 for d in grid if not d.flow_augmented)
    assert {d.family for d in grid} == {"D1", "D2", "D3", "D4"}


def test_window_overlap_raises():
    """The single check that stops a discriminator seeing its own outcome."""
    t = dt.datetime(2023, 1, 1)
    bad = pl.DataFrame({"qualify_end": [t], "outcome_start": [t - dt.timedelta(minutes=1)]})
    with pytest.raises(RuntimeError, match="WINDOW OVERLAP"):
        assert_windows_disjoint(bad)
    ok = pl.DataFrame({"qualify_end": [t], "outcome_start": [t + dt.timedelta(minutes=1)]})
    assert_windows_disjoint(ok)


def test_window_equality_is_valid_adjacent_disjoint():
    """Half-open windows: outcome_start == qualify_end is the correct join, not an overlap (I-1)."""
    t = dt.datetime(2023, 1, 1)
    adjacent = pl.DataFrame({"qualify_end": [t], "outcome_start": [t]})
    assert_windows_disjoint(adjacent)  # must not raise


def test_separation_is_invariant_to_call_rate():
    """A rule that simply calls 'accept' at the base rate must score S = 0."""
    n = 400
    labels = ["ACCEPTANCE" if i % 2 else "TRAP" for i in range(n)]
    ev = pl.DataFrame({"label": labels, "says_accept": [i % 4 < 2 for i in range(n)]})
    s = separation(ev)
    assert abs(s["S"]) < 1e-12
    perfect = pl.DataFrame({"label": labels, "says_accept": [l == "ACCEPTANCE" for l in labels]})
    assert separation(perfect)["S"] == pytest.approx(1.0)


def test_separation_excludes_unresolved_but_reports_its_rate():
    ev = pl.DataFrame({
        "label": ["ACCEPTANCE", "TRAP", "UNRESOLVED", "UNRESOLVED"],
        "says_accept": [True, False, True, False],
    })
    s = separation(ev)
    assert s["n"] == 2
    assert s["unresolved_rate"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Profile kernels
# ---------------------------------------------------------------------------


def test_all_kernels_conserve_volume():
    """A kernel that loses or invents volume would silently distort every profile."""
    bars = _synthetic_day()
    edges = price_grid(float(bars["Low"].min()), float(bars["High"].max()))
    for k in KERNELS:
        _, prof = build_profile(bars, k, edges=edges)
        assert prof.sum() == pytest.approx(float(bars["Volume"].sum()), rel=1e-9)


def test_profiles_share_an_explicit_grid():
    """Two profiles compared on grids derived from their own ranges are not comparable."""
    bars = _synthetic_day()
    sub = bars.head(60)
    edges = price_grid(float(bars["Low"].min()), float(bars["High"].max()))
    e1, p1 = build_profile(bars, "K-UNIFORM", edges=edges)
    e2, p2 = build_profile(sub, "K-UNIFORM", edges=edges)
    assert np.array_equal(e1, e2) and len(p1) == len(p2)


def test_value_area_covers_the_requested_share():
    edges = price_grid(0.0, 10.0, 100)
    prof = np.zeros(100)
    prof[48:52] = 25.0
    poc, val, vah = poc_and_value_area(edges, prof, share=0.685)
    assert val <= poc <= vah
    lo_i = int(np.searchsorted(edges, val) - 1)
    hi_i = int(np.searchsorted(edges, vah) - 1)
    assert prof[lo_i:hi_i + 1].sum() >= 0.685 * prof.sum() - 1e-9


# ---------------------------------------------------------------------------
# §2.3 classes
# ---------------------------------------------------------------------------


def _resid_frame(**over) -> pl.DataFrame:
    base = {
        "OpenTime": [dt.datetime(2022, 8, 1)], "Open": [100.0], "High": [101.0],
        "Low": [99.0], "Close": [100.5], "Delta": [5.0],
        "volume_resid": [0.0], "range_resid": [0.0],
        "delta_abs_resid": [0.0], "delta_ratio_resid": [0.0],
    }
    base.update({k: [v] for k, v in over.items()})
    return pl.DataFrame(base)


_TH = {m: {"high": 1.0, "low": -1.0, "n": 100, "high_pctl": 0.9, "low_pctl": 0.1}
       for m in ("volume", "range", "delta_abs", "delta_ratio")}


def test_absorption_requires_effort_without_result():
    hit = classify(_resid_frame(volume_resid=2.0, range_resid=-2.0, delta_abs_resid=2.0), _TH)
    assert hit["sig_class"][0] == "ABSORPTION"
    # same heavy effort but a WIDE range is not absorption
    miss = classify(_resid_frame(volume_resid=2.0, range_resid=2.0, delta_abs_resid=2.0), _TH)
    assert miss["sig_class"][0] != "ABSORPTION"


def test_warning_print_is_a_drive_whose_delta_opposes_its_close():
    drive = classify(
        _resid_frame(volume_resid=2.0, range_resid=2.0, Close=100.95, Delta=5.0), _TH
    )
    warn = classify(
        _resid_frame(volume_resid=2.0, range_resid=2.0, Close=100.95, Delta=-5.0), _TH
    )
    assert drive["sig_class"][0] == "DRIVE"
    assert warn["sig_class"][0] == "DRIVE_WARNING_PRINT"


def test_vacuum_run_is_distance_on_thin_interest():
    v = classify(_resid_frame(volume_resid=-2.0, range_resid=2.0), _TH)
    assert v["sig_class"][0] == "VACUUM_RUN"


def test_dry_up_is_not_a_located_class():
    """Source §2.3 defines dry-up by a trend across bars, not by a location."""
    assert "DRY_UP" not in LOCATED_CLASSES


def test_thresholds_are_derived_from_the_data_not_asserted():
    resid = pl.DataFrame({"volume_resid": list(np.linspace(-3, 3, 1001))})
    th = derive_thresholds(resid, ("volume",))
    assert th["volume"]["high"] == pytest.approx(np.quantile(np.linspace(-3, 3, 1001), 0.9))
    assert th["volume"]["high_pctl"] == 0.9


def test_classify_refuses_without_derived_thresholds():
    with pytest.raises(RuntimeError, match="missing derived thresholds"):
        classify(_resid_frame(), {"volume": _TH["volume"]})


def test_qualify_window_is_shared_across_candidates():
    """One shared window is what keeps the race from being a horizon comparison."""
    assert QUALIFY_MINUTES == 30


# ---------------------------------------------------------------------------
# QA run 1 seams that the original 26 tests missed
# ---------------------------------------------------------------------------


def test_build_profile_rejects_signed_weight_column():
    """I-16: the ban must check the real weight column, not a literal Series('Volume')."""
    bars = _synthetic_day().with_columns(pl.col("Delta").alias("signed_volume"))
    edges = price_grid(float(bars["Low"].min()), float(bars["High"].max()))
    with pytest.raises(RuntimeError, match="PER-LEVEL DELTA BARRED"):
        build_profile(bars, "K-UNIFORM", edges=edges, weight_col="signed_volume")
    with pytest.raises(RuntimeError, match="PER-LEVEL DELTA BARRED"):
        build_profile(bars, "K-UNIFORM", edges=edges, weight_col="Delta")


def test_residual_matched_control_balances_regime_means():
    """I-3: control bins must come from a COMMON distribution, not each arm's own ranks."""
    rng = np.random.default_rng(0)
    n = 400
    # High-activity events sit in the upper residual tail; pool is the full range.
    pool_v = rng.normal(0.0, 1.0, n)
    pool_r = rng.normal(0.0, 1.0, n)
    event_idx = np.where((pool_v > 1.0) & (pool_r > 0.5))[0][:40]
    rows = []
    for i in range(n):
        rows.append({
            "OpenTime": dt.datetime(2022, 8, 1) + dt.timedelta(minutes=i),
            "volume_resid": float(pool_v[i]),
            "range_resid": float(pool_r[i]),
            "sig_class": "ABSORPTION" if i in set(event_idx.tolist()) else None,
        })
    all_bars = pl.DataFrame(rows)
    events = all_bars.filter(pl.col("sig_class").is_not_null())
    ctrl = residual_matched_control(all_bars, events, seed=42, n_per_event=1)
    assert ctrl.height > 0
    mq = match_quality(events, ctrl)
    # Matched means must be closer than the unmatched full-pool gap would be.
    pool_non = all_bars.filter(pl.col("sig_class").is_null())
    unmatched_gap = abs(
        float(events["volume_resid"].mean()) - float(pool_non["volume_resid"].mean())
    )
    assert mq["volume_resid_abs_gap"] < unmatched_gap * 0.5
    assert mq["volume_resid_abs_gap"] < 0.5
    assert mq["range_resid_abs_gap"] < 0.5


def test_label_outcomes_requires_both_acceptance_clauses():
    """I-15: ACCEPTANCE needs further run BEFORE re-entry (source S3/S4; design §4.3)."""
    t0 = dt.datetime(2022, 8, 1, 1, 0)
    # Session: IB [99, 101], width 2. Up-poke extreme 102. Outcome starts at t0.
    # Path: runs to 104 (1 IB further) at t+1, then re-enters below 101 at t+2.
    bars = pl.DataFrame({
        "OpenTime": [t0 + dt.timedelta(minutes=i) for i in range(5)],
        "Open": [102.0, 103.0, 104.0, 100.5, 100.0],
        "High": [102.5, 104.5, 104.5, 101.0, 100.5],
        "Low": [101.5, 102.5, 100.0, 99.5, 99.0],  # t+2 Low re-enters (≤101)
        "Close": [102.0, 104.0, 100.5, 100.0, 100.0],
        "Volume": [10.0] * 5,
    })
    pokes = pl.DataFrame({
        "anchor_ts": [dt.datetime(2022, 8, 1)],
        "outcome_start": [t0],
        "session_end": [t0 + dt.timedelta(minutes=5)],
        "poke_side": [1],
        "poke_extreme": [102.0],
        "ib_high": [101.0],
        "ib_low": [99.0],
        "ib_width": [2.0],
    }).with_columns(pl.col("anchor_ts").cast(pl.Datetime("us")))
    bars = bars.with_columns(pl.lit(dt.datetime(2022, 8, 1)).alias("anchor_ts"))
    lab = label_outcomes(bars, pokes)
    assert lab["label"][0] == LABEL_ACCEPTANCE
    assert lab["accept_ok"][0] is True

    # Same run AFTER re-entry first → not ACCEPTANCE under both clauses.
    bars_late = pl.DataFrame({
        "OpenTime": [t0 + dt.timedelta(minutes=i) for i in range(5)],
        "Open": [102.0, 100.5, 100.0, 103.0, 105.0],
        "High": [102.5, 101.0, 100.5, 104.0, 106.0],
        "Low": [101.5, 99.5, 99.0, 102.0, 104.0],  # re-entry at t+1 before accept level
        "Close": [102.0, 100.0, 100.0, 104.0, 105.0],
        "Volume": [10.0] * 5,
        "anchor_ts": [dt.datetime(2022, 8, 1)] * 5,
    })
    lab2 = label_outcomes(bars_late, pokes)
    assert lab2["accept_ok"][0] is False


def test_label_outcomes_trap_invalidated_by_second_poke():
    """I-15 TRAP clause: opposite edge before exceeding poke extreme; second poke invalidates."""
    t0 = dt.datetime(2022, 8, 1, 1, 0)
    # Up-poke extreme 102. Path first goes beyond 102, then to opposite edge.
    bars = pl.DataFrame({
        "OpenTime": [t0 + dt.timedelta(minutes=i) for i in range(4)],
        "Open": [102.0, 103.0, 102.0, 100.0],
        "High": [102.5, 103.5, 102.5, 100.5],  # t+1 exceeds poke extreme
        "Low": [101.5, 102.0, 99.5, 98.5],       # later touches opposite (ib_low=99)
        "Close": [102.0, 103.0, 100.0, 99.0],
        "Volume": [10.0] * 4,
        "anchor_ts": [dt.datetime(2022, 8, 1)] * 4,
    })
    pokes = pl.DataFrame({
        "anchor_ts": [dt.datetime(2022, 8, 1)],
        "outcome_start": [t0],
        "session_end": [t0 + dt.timedelta(minutes=4)],
        "poke_side": [1],
        "poke_extreme": [102.0],
        "ib_high": [101.0],
        "ib_low": [99.0],
        "ib_width": [2.0],
    })
    lab = label_outcomes(bars, pokes)
    assert lab["trap_ok"][0] is False  # beyond-poke before opposite edge
    # Clean trap: opposite edge first, never beyond poke extreme.
    bars_trap = pl.DataFrame({
        "OpenTime": [t0 + dt.timedelta(minutes=i) for i in range(4)],
        "Open": [101.5, 100.5, 99.5, 99.0],
        "High": [101.8, 101.0, 100.0, 99.5],
        "Low": [100.5, 99.5, 98.5, 98.0],  # opposite edge at t+2
        "Close": [101.0, 100.0, 99.0, 98.5],
        "Volume": [10.0] * 4,
        "anchor_ts": [dt.datetime(2022, 8, 1)] * 4,
    })
    lab_t = label_outcomes(bars_trap, pokes)
    assert lab_t["label"][0] == LABEL_TRAP
    assert lab_t["trap_ok"][0] is True


def test_dry_up_detects_multi_bar_effort_drain():
    """I-20: DRY_UP is a trend across bars (same direction, falling V and |Δ| residuals)."""
    t0 = dt.datetime(2022, 8, 1)
    # Three same-direction up bars with falling volume_resid and faster-falling |Δ|.
    rows = []
    for i, (vr, dr) in enumerate([(2.0, 2.0), (1.0, 0.5), (0.0, -1.0), (-0.5, -1.5)]):
        rows.append({
            "OpenTime": t0 + dt.timedelta(minutes=i),
            "Open": 100.0 + i * 0.1,
            "High": 100.5 + i * 0.1,
            "Low": 99.9 + i * 0.1,
            "Close": 100.4 + i * 0.1,  # up bar
            "Delta": 1.0,
            "volume_resid": vr,
            "range_resid": 0.0,
            "delta_abs_resid": dr,
            "delta_ratio_resid": 0.0,
            "anchor_ts": t0,
        })
    bars = pl.DataFrame(rows)
    out = classify(bars, _TH)
    # DRY_UP needs DRYUP_BARS=3 same-dir bars with two successive declines → index 2+
    assert "DRY_UP" in out["sig_class"].to_list()
    assert "DRY_UP" not in LOCATED_CLASSES


def _load_freeze_mod():
    import importlib.util
    from pathlib import Path

    fp = (
        Path(__file__).resolve().parents[1]
        / "experiments/INFR-018/code/freeze_and_pin.py"
    )
    spec = importlib.util.spec_from_file_location("infr018_freeze", fp)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _i2_tw(**over):
    """Minimal HYP-I2 tripwire dict with a bite-proving leak plant."""
    base = {
        "class": "future_destroy",
        "adjudication_kind": "i2_survival",
        "contrast_raw": 0.10,
        "contrast_shifted": -4.0,
        "collapse_fraction": -40.0,
        "day_contrast_correlation": 0.06,
        "survives": False,
        "positive_control": {
            "kind": "i2_leak_plant",
            "contrast_raw": -2.0,
            "contrast_shifted": -1.9,
            "collapse_fraction": 0.95,
            "day_contrast_correlation": 0.2,
            "survives": True,  # same-sign material → re-derives as survives
        },
    }
    pc_over = over.pop("positive_control", "__keep__")
    base.update(over)
    if pc_over == "__keep__":
        pass
    elif pc_over is None:
        base.pop("positive_control", None)
    else:
        base["positive_control"] = pc_over
    return base


def test_adjudicate_i2_survival_same_sign_and_day_corr():
    """I-34: shared adjudicator — opposite-sign null vs same-sign leak."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments/INFR-018/code"))
    from common import adjudicate_i2_survival

    # Destroy null: large opposite-sign, low day_corr → does not survive.
    null = adjudicate_i2_survival(
        contrast_raw=0.1, contrast_shifted=-4.0, collapse_fraction=-40.0,
        day_contrast_correlation=0.06,
    )
    assert null["survives"] is False
    assert null["same_sign_material"] is False

    # Leaky construction: same-sign material cf → survives.
    leak = adjudicate_i2_survival(
        contrast_raw=-2.0, contrast_shifted=-1.9, collapse_fraction=0.95,
        day_contrast_correlation=0.1,
    )
    assert leak["survives"] is True
    assert leak["same_sign_material"] is True

    # High day_corr alone → survives.
    corr = adjudicate_i2_survival(
        contrast_raw=0.1, contrast_shifted=-0.01, collapse_fraction=-0.1,
        day_contrast_correlation=0.8,
    )
    assert corr["survives"] is True

    with pytest.raises(ValueError, match="day_contrast_correlation"):
        adjudicate_i2_survival(
            contrast_raw=0.1, contrast_shifted=-4.0, collapse_fraction=-40.0,
            day_contrast_correlation=None,
        )


def test_tripwire_blocks_freeze_on_survival_not_opposite_null():
    """I-5/I-29/I-34/I-36: freeze re-derives survival; production name string has bite."""
    mod = _load_freeze_mod()
    # Production call site name (QA run 4, I-36) — not the short label alone.
    NAME = "HYP-I2 future_shift"

    # Opposite-sign null + bite plant → accepted under the LIVE name.
    ok_null = mod._assert_tripwire(_i2_tw(), NAME)
    assert ok_null["survives_rederived"]["survives"] is False

    # Same-sign material on the REAL arm → hard block (re-derived True).
    with pytest.raises(RuntimeError, match="EDGE SURVIVED"):
        mod._assert_tripwire(
            _i2_tw(
                contrast_raw=0.2,
                contrast_shifted=0.18,
                collapse_fraction=0.9,
                day_contrast_correlation=0.1,
                survives=True,
            ),
            NAME,
        )
    # Lying flag alone is also refused (disagrees with re-derived).
    with pytest.raises(RuntimeError, match="disagrees"):
        mod._assert_tripwire(
            _i2_tw(
                contrast_raw=0.2,
                contrast_shifted=0.18,
                collapse_fraction=0.9,
                day_contrast_correlation=0.1,
                survives=False,
            ),
            NAME,
        )

    # Null day_corr → refuse (soft path closed).
    with pytest.raises(RuntimeError, match="re-derived|day_contrast"):
        mod._assert_tripwire(
            _i2_tw(day_contrast_correlation=None, survives=False),
            NAME,
        )

    # Missing positive control → refuse under production name (I-36).
    with pytest.raises(RuntimeError, match="positive_control"):
        tw = _i2_tw()
        del tw["positive_control"]
        mod._assert_tripwire(tw, NAME)

    # Pre–I-34 full-race shape (no plant, opposite-sign null fields only) → refuse.
    with pytest.raises(RuntimeError, match="positive_control"):
        mod._assert_tripwire(
            {
                "class": "future_destroy",
                "contrast_raw": 0.1,
                "contrast_shifted": -4.17,
                "collapse_fraction": -41.7,
                "day_contrast_correlation": 0.06,
                "survives": False,
            },
            NAME,
        )

    # Leak plant that does NOT survive → gate insensitive.
    with pytest.raises(RuntimeError, match="POSITIVE CONTROL"):
        mod._assert_tripwire(
            _i2_tw(
                positive_control={
                    "kind": "i2_leak_plant",
                    "contrast_raw": 0.1,
                    "contrast_shifted": -4.0,
                    "collapse_fraction": -40.0,
                    "day_contrast_correlation": 0.05,
                    "survives": False,
                }
            ),
            NAME,
        )

    # Emitter flag disagrees with re-derived → refuse.
    with pytest.raises(RuntimeError, match="disagrees"):
        mod._assert_tripwire(_i2_tw(survives=True), NAME)

    # I-59: opposite-sign large |cf| is NOT survival (AMENDMENT-4 trap on I3).
    # Missing probe still refuses; the main arm does not.
    with pytest.raises(RuntimeError, match="positive_control leak plant is REQUIRED"):
        mod._assert_tripwire(
            {"collapse_fraction": -6.10, "S_raw": 0.4, "S_swapped": -2.44,
             "class": "future_destroy"},
            "HYP-I3 outcome_path_swap",
        )
    # Same-sign material |cf| > 0.25 IS survival → hard block.
    with pytest.raises(RuntimeError, match="DID NOT COLLAPSE"):
        mod._assert_tripwire(
            {"collapse_fraction": 0.9, "S_raw": 0.4, "S_swapped": 0.36,
             "class": "future_destroy",
             "positive_control": {
                 "kind": "i3_leak_plant", "S_raw": 0.4, "S_swapped": 0.36,
                 "collapse_fraction": 0.9,
             }},
            "HYP-I3 outcome_path_swap",
        )
    # S_raw/S_swapped mandatory for the sign clause.
    with pytest.raises(RuntimeError, match="S_raw|sign clause|re-derived"):
        mod._assert_tripwire(
            {"collapse_fraction": 0.05, "class": "future_destroy"},
            "HYP-I3 outcome_path_swap",
        )

    def _i3_probe(cf):
        return {
            "kind": "i3_leak_plant",
            "purpose": "a discriminator that CAN see outcome bars",
            "required_outcome": "SURVIVES",
            "read_past_qualify": True,
            "S_raw": 0.4,
            "S_swapped": 0.4 * cf,
            "collapse_fraction": cf,
        }

    def _i3_tw(cf=0.05, probe_cf=0.9, **over):
        body = {
            "collapse_fraction": cf,
            "S_raw": 0.4,
            "S_swapped": 0.4 * cf,
            "class": "future_destroy",
            "positive_control": _i3_probe(probe_cf),
        }
        body.update(over)
        return body

    # AMENDMENT-6: the leaky probe reads the SAME spliced bars the labels came
    # from, so it must SURVIVE. Requiring it to collapse certified a toothless
    # gate (QA run 6, I-45).
    ok = mod._assert_tripwire(_i3_tw(), "HYP-I3 outcome_path_swap")
    assert ok["collapse_fraction"] == 0.05
    assert ok["survives_rederived"]["survives"] is False
    assert ok["positive_control"]["survives_rederived"]["survives"] is True
    # A probe that COLLAPSED means the destroy never reached the rule's inputs.
    with pytest.raises(RuntimeError, match="POSITIVE CONTROL did not survive"):
        mod._assert_tripwire(_i3_tw(probe_cf=0.02), "HYP-I3 outcome_path_swap")
    # Opposite-sign persistence is not survival: the probe's separation flipped
    # sign, so it is not still reading the path its labels came from.
    with pytest.raises(RuntimeError, match="POSITIVE CONTROL did not survive"):
        mod._assert_tripwire(_i3_tw(probe_cf=-0.9), "HYP-I3 outcome_path_swap")
    # A probe whose collapse fraction could not be computed is not a free pass.
    with pytest.raises(RuntimeError, match="POSITIVE CONTROL did not survive"):
        mod._assert_tripwire(
            _i3_tw(positive_control={"collapse_fraction": None}),
            "HYP-I3 outcome_path_swap",
        )
    # The emitter's own survives flag is not trusted over the re-derivation.
    with pytest.raises(RuntimeError, match="disagrees with the re-derived"):
        mod._assert_tripwire(
            _i3_tw(positive_control={**_i3_probe(0.9), "survives": False}),
            "HYP-I3 outcome_path_swap",
        )
    # The probe requirement is NOT keyed on the caller's name string (I-53).
    with pytest.raises(RuntimeError, match="positive_control leak plant is REQUIRED"):
        mod._assert_tripwire(
            {"collapse_fraction": 0.05, "S_raw": 0.4, "S_swapped": 0.02,
             "class": "future_destroy"},
            "future_shift",
        )
    with pytest.raises(RuntimeError, match="no tripwire"):
        mod._assert_tripwire(None, NAME)

    # I-63: I2 positive control carries survives_rederived on the returned dict.
    i2_ok = mod._assert_tripwire(_i2_tw(), "HYP-I2 future_shift")
    assert "survives_rederived" in i2_ok["positive_control"]
    assert i2_ok["positive_control"]["survives_rederived"]["survives"] is True


# ---------------------------------------------------------------------------
# HYP-I3 path-swap tripwire — the destroy must reach the bars the rule READS
# ---------------------------------------------------------------------------


def _i3_swap_fixture(
    n_sessions: int = 12,
    symbol: str = "AAA",
    scale: float = 1.0,
    *,
    session_len: int = 240,
    day_offset: int = 0,
    through_attach_sessions: bool = True,
):
    """One symbol, several sessions.

    Built through ``attach_sessions`` by default so the bar frame carries the
    production ``session_end`` column (QA I-56 / I-58). ``n_sessions`` is 12 so
    horizon buckets hold more than one event; singletons are skipped by the
    destroy (I-57) and would leave nothing to splice at n=2.
    """
    from xen.sigbar.sessions import attach_sessions

    rows, pokes, anchors = [], [], []
    for k in range(n_sessions):
        # Vary horizon slightly so value-rank buckets are non-degenerate when two
        # symbols are pooled (I-58: ordinal rank made the same-symbol test mute).
        length = session_len + (k % 5) * 12
        anchor = dt.datetime(2022, 8, 1) + dt.timedelta(days=k + day_offset)
        session_end = anchor + dt.timedelta(minutes=length)
        anchors.append({"anchor_ts": anchor, "session_end": session_end})
        base = (100.0 + 10.0 * k) * scale
        for i in range(length):
            t = anchor + dt.timedelta(minutes=i)
            px = base + (0.0 if i < length // 2 else 1.0 + k)
            rows.append({
                "OpenTime": t, "Open": px, "High": px + 0.5,
                "Low": px - 0.5, "Close": px, "Volume": 10.0, "NTrades": 5,
                "BuyVolume": 6.0, "SellVolume": 4.0, "Delta": 2.0, "Turnover": 1000.0,
            })
        outcome_start = anchor + dt.timedelta(minutes=length // 2)
        pokes.append({
            "anchor_ts": anchor, "symbol": symbol,
            "poke_ts": anchor + dt.timedelta(minutes=max(length // 4, 1)),
            "poke_side": 1, "poke_extreme": base + 1.0,
            "qualify_end": anchor + dt.timedelta(minutes=max(length // 4, 1) + QUALIFY_MINUTES),
            "outcome_start": outcome_start,
            "session_end": session_end,
            "ib_high": base + 0.5, "ib_low": base - 0.5, "ib_width": 1.0,
        })
    raw = pl.DataFrame(rows)
    if through_attach_sessions:
        bars = attach_sessions(raw, pl.DataFrame(anchors), ib_minutes=max(session_len // 8, 15))
        assert "session_end" in bars.columns, "production schema must carry session_end"
    else:
        bars = raw
    return {symbol: bars}, pl.DataFrame(pokes)


def _import_i3():
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "experiments/INFR-018/code"))
    from hyp_i3_a6_race import swap_outcome_paths

    return swap_outcome_paths


def test_path_swap_replaces_the_bars_the_discriminator_reads():
    """AMENDMENT-6 / QA I-45.

    The destroy used to recompute labels from a donor path while every rule was
    still evaluated on the target's REAL bars. A rule that peeks at outcome bars
    then decorrelates from the donor-derived labels exactly like an honest one,
    so every rule collapsed and no leak could ever survive. This pins the fix:
    the outcome window the rule reads must actually change, and the qualifying
    window must not.
    """
    swap_outcome_paths = _import_i3()
    bars_by_symbol, pokes = _i3_swap_fixture()
    labels, spliced, stats = swap_outcome_paths(
        bars_by_symbol, pokes, np.random.default_rng(0)
    )
    assert stats["status"] == "OK"
    assert "AAA" in spliced, "the spliced bars must be returned, not discarded"
    # Self-donors (singletons) are excluded from the destroy population (I-57).
    assert stats["n_events_spliced"] == stats["n_permutable_rows"]
    assert stats["n_events_spliced"] + stats["n_self_donor_skipped"] == pokes.height
    assert stats["n_cross_symbol_donors"] == 0
    # OpenTime uniqueness after the splice (I-61).
    assert spliced["AAA"].select("OpenTime").n_unique() == spliced["AAA"].height

    orig, new = bars_by_symbol["AAA"], spliced["AAA"]
    n_changed = 0
    for row in pokes.to_dicts():
        win = (pl.col("OpenTime") >= row["outcome_start"]) & (
            pl.col("OpenTime") < row["session_end"]
        )
        before = (pl.col("OpenTime") >= row["anchor_ts"]) & (
            pl.col("OpenTime") < row["outcome_start"]
        )
        # Qualifying window untouched — honest rule makes identical calls.
        assert orig.filter(before)["Close"].to_list() == new.filter(before)["Close"].to_list()
        if orig.filter(win)["Close"].to_list() != new.filter(win)["Close"].to_list():
            n_changed += 1

    assert n_changed == stats["n_permutable_rows"] > 0
    assert stats["fixed_point_rate_within_permutable"] == 0.0
    assert "same-symbol" in stats["block_definition"]


def test_path_swap_donors_are_same_symbol():
    """A donor from another instrument sits at a foreign price level, so the
    labels would be decided by scale accident rather than by an unrelated future
    (QA run 6, I-45). Fixture uses SHARED horizon values across symbols so a
    mutation that drops symbol from the block key WOULD mix donors (I-58).
    """
    swap_outcome_paths = _import_i3()
    # Interleave day offsets so equal-horizon ranks sit next to each other across
    # symbols when the block key is broken — the mutation I-58 showed surviving.
    aaa_bars, aaa_pokes = _i3_swap_fixture(day_offset=0)
    zzz_bars, zzz_pokes = _i3_swap_fixture(symbol="ZZZ", scale=1000.0, day_offset=0)
    bars_by_symbol = {**aaa_bars, **zzz_bars}
    pokes = pl.concat([aaa_pokes, zzz_pokes])

    _labels, spliced, stats = swap_outcome_paths(
        bars_by_symbol, pokes, np.random.default_rng(0)
    )
    assert stats["n_symbols_spliced"] == 2
    assert stats["n_cross_symbol_donors"] == 0
    # AAA's spliced bars must stay on AAA's price scale — a ZZZ donor would be
    # three orders of magnitude away and would decide every label by scale alone.
    assert spliced["AAA"]["Close"].max() < 10_000.0
    assert spliced["ZZZ"]["Close"].min() > 10_000.0


def test_path_swap_session_end_collision_does_not_drop_events():
    """I-56: bars carry session_end from attach_sessions; after a path swap the
    donor's session_end must not empty the outcome window for later targets.
    """
    swap_outcome_paths = _import_i3()
    bars_by_symbol, pokes = _i3_swap_fixture(n_sessions=12)
    labels, spliced, stats = swap_outcome_paths(
        bars_by_symbol, pokes, np.random.default_rng(1)
    )
    assert stats["status"] == "OK"
    # Every permutable event must produce a label; calendar-ordered drop was the bug.
    assert stats["n_events_spliced"] == stats["n_permutable_rows"]
    assert labels.height == stats["n_events_spliced"]
    assert stats.get("n_no_donor_path", 0) == 0


def test_path_swap_skips_singleton_self_donors():
    """I-57: a block of size 1 is a self-donor; it is not counted as spliced."""
    swap_outcome_paths = _import_i3()
    bars_one, pokes_one = _i3_swap_fixture(n_sessions=1)
    _labels, _spliced, stats = swap_outcome_paths(
        bars_one, pokes_one, np.random.default_rng(0)
    )
    # n < 2 → destroy cannot run; n=1 is the pure singleton case.
    assert stats["status"] in ("TOO_FEW_EVENTS", "NO_DONOR_PATHS", "OK")
    if stats["status"] == "OK":
        assert stats["n_self_donor_skipped"] >= 1
        assert stats["n_events_spliced"] == 0


def _i3_accept_trap_fixture(n_sessions: int = 16, symbol: str = "AAA"):
    """Sessions with alternating ACCEPTANCE / TRAP outcome paths.

    Flat signature fixtures leave every D4 call identical, so the leaky probe
    cannot demonstrate survival (S is null). Half the sessions run beyond the
    accept level; half crash through the opposite IB edge.
    """
    from xen.sigbar.sessions import attach_sessions

    rows, pokes, anchors = [], [], []
    for k in range(n_sessions):
        length = 240 + (k % 5) * 12
        anchor = dt.datetime(2022, 8, 1) + dt.timedelta(days=k)
        session_end = anchor + dt.timedelta(minutes=length)
        anchors.append({"anchor_ts": anchor, "session_end": session_end})
        base = 100.0 + 10.0 * k
        mid = length // 2
        for i in range(length):
            t = anchor + dt.timedelta(minutes=i)
            if i < mid:
                px = base
            elif k % 2 == 0:
                px = base + 3.0 + (i - mid) * 0.05
            else:
                px = base - 2.0 - (i - mid) * 0.05
            rows.append({
                "OpenTime": t, "Open": px, "High": px + 0.5, "Low": px - 0.5,
                "Close": px, "Volume": 10.0, "NTrades": 5, "BuyVolume": 6.0,
                "SellVolume": 4.0, "Delta": 2.0, "Turnover": 1000.0,
            })
        poke_ts = anchor + dt.timedelta(minutes=max(length // 4, 1))
        pokes.append({
            "anchor_ts": anchor, "symbol": symbol,
            "poke_ts": poke_ts, "poke_side": 1, "poke_extreme": base + 1.0,
            "qualify_end": poke_ts + dt.timedelta(minutes=QUALIFY_MINUTES),
            "outcome_start": anchor + dt.timedelta(minutes=mid),
            "session_end": session_end,
            "ib_high": base + 0.5, "ib_low": base - 0.5, "ib_width": 1.0,
        })
    bars = attach_sessions(pl.DataFrame(rows), pl.DataFrame(anchors), ib_minutes=30)
    return {symbol: bars}, pl.DataFrame(pokes)


def test_path_swap_leaky_survives_honest_collapses():
    """I-58 / AMENDMENT-6 second half: on the SPLICED bars a leaky rule keeps
    separation and an honest rule loses it. This is the half of the I-45 fix
    that mutation-testing found untested.
    """
    from xen.sigbar.acceptance import Discriminator, evaluate_discriminator, separation

    swap_outcome_paths = _import_i3()
    bars_by_symbol, pokes = _i3_accept_trap_fixture(n_sessions=16)
    labels_swapped, spliced, stats = swap_outcome_paths(
        bars_by_symbol, pokes, np.random.default_rng(2)
    )
    assert stats["n_events_spliced"] >= 4

    real_labs = []
    for sym, bars in bars_by_symbol.items():
        pk = pokes.filter(pl.col("symbol") == sym)
        lab = label_outcomes(bars, pk).with_columns(pl.lit(sym).alias("symbol"))
        real_labs.append(lab)
    real_labels = pl.concat(real_labs)
    keys = labels_swapped.select("anchor_ts", "symbol")
    real_on = (
        pokes.join(real_labels, on=["anchor_ts", "symbol"], how="inner")
        .join(keys, on=["anchor_ts", "symbol"], how="semi")
    )
    swapped_on = pokes.join(labels_swapped, on=["anchor_ts", "symbol"], how="inner")

    honest = Discriminator("HONEST", "D1", False, {"n": 2})
    leaky = Discriminator("LEAK", "D4", False, {"tau": 0.5, "w": 240})

    def _sep(disc, events, bars_map, *, leak=False):
        calls = []
        for sym, bars in bars_map.items():
            ev = events.filter(pl.col("symbol") == sym)
            if ev.height == 0:
                continue
            c = evaluate_discriminator(bars, ev, disc, read_past_qualify=leak)
            calls.append(c.with_columns(pl.lit(sym).alias("symbol")))
        if not calls:
            return None
        j = events.join(pl.concat(calls), on=["anchor_ts", "symbol"], how="inner").with_columns(
            pl.col("says_accept").fill_null(False)
        )
        return separation(j).get("S")

    s_l_raw = _sep(leaky, real_on, bars_by_symbol, leak=True)
    s_l_sw = _sep(leaky, swapped_on, spliced, leak=True)
    s_h_raw = _sep(honest, real_on, bars_by_symbol, leak=False)
    s_h_sw = _sep(honest, swapped_on, spliced, leak=False)

    # Structural pin: the leaky probe (read_past_qualify on spliced bars) must
    # keep same-sign material separation — that is what makes the gate have bite.
    assert s_l_raw is not None and s_l_sw is not None
    assert s_l_raw * s_l_sw > 0
    assert abs(s_l_sw / s_l_raw) > 0.25
    # Honest on spliced bars must not keep a large same-sign fraction of a
    # non-null raw S. If raw S is null/zero the destroy has nothing to collapse.
    if s_h_raw not in (None, 0) and s_h_sw is not None:
        cf_h = s_h_sw / s_h_raw
        assert not (s_h_raw * s_h_sw > 0 and abs(cf_h) > 0.25)
