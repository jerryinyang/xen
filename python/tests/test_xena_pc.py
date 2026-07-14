"""INFR-009 P-C exit (c) unit tests — layout embargo, deplant exactness, gate logic.

Fast structural tests only (no full search). The heavy e2e/bite is exercised by the
design/confirm bank runs; here we lock the novel primitives.
"""
from __future__ import annotations

import numpy as np

from xen.xena.calibration_p3b import LOW, make_null_universe
from xen.xena.calibration_pc import (BITE_EDGE_BPS, EMBARGO_FRAC, _failure_label,
                                     _outcome, c_layout, deplant_stage2)

NS = 1_000_000_000
_PLANT = ("plant", "HCPLANT")


def test_c_layout_distant_embargo():
    n_bars, H = 6000, 20
    lay = c_layout(n_bars, H, embargo_frac=EMBARGO_FRAC)
    span = n_bars * 60 * NS
    purge = int(EMBARGO_FRAC * span)
    # embargo gap sits between stage-1 (ranking end) and stage-2 (gate start)
    assert lay.purge_ns == purge
    assert lay.gate[0] - lay.ranking[1] == purge
    # ordered, disjoint, contiguous stage-1 bands; gate ends at span
    assert lay.search[0] == 0 and lay.search[1] == lay.ranking[0]
    assert lay.ranking[1] < lay.gate[0] < lay.gate[1] == span
    # embargo ≫ H (adjacent-purge that leaked in P3d was 1·H)
    embargo_bars = purge / (60 * NS)
    assert embargo_bars >= 40 * H  # 1200 bars = 60·H at 0.20


def test_deplant_stage2_exact_inverse_on_plant():
    streams = make_null_universe(4242, LOW, n_candidates=8, edge_bps=BITE_EDGE_BPS)
    stage2_start = c_layout(LOW.n_bars, LOW.hold_bars).gate[0]
    plant = next(s for s in streams if s.candidate_id.startswith(_PLANT))

    et = plant.trades.get_column("EntryTime").to_numpy().astype(np.int64)
    d = plant.trades.get_column("Direction").to_numpy().astype(float)
    xp_pre = plant.trades.get_column("ExitPrice").to_numpy().astype(float)
    in_s2 = et >= stage2_start
    assert in_s2.any() and (~in_s2).any()  # plant spans both stages

    out = deplant_stage2(streams, edge_bps=BITE_EDGE_BPS, stage2_start_ns=stage2_start)
    plant_out = next(s for s in out if s.candidate_id == plant.candidate_id)
    xp_post = plant_out.trades.get_column("ExitPrice").to_numpy().astype(float)

    # stage-1 trades untouched; stage-2 trades = exact unplanted raw exit
    np.testing.assert_allclose(xp_post[~in_s2], xp_pre[~in_s2], rtol=0, atol=0)
    expected_raw = xp_pre[in_s2] / (1.0 + d[in_s2] * BITE_EDGE_BPS / 1e4)
    np.testing.assert_allclose(xp_post[in_s2], expected_raw, rtol=1e-12, atol=1e-12)


def test_deplant_leaves_null_candidates_untouched():
    streams = make_null_universe(4242, LOW, n_candidates=8, edge_bps=BITE_EDGE_BPS)
    stage2_start = c_layout(LOW.n_bars, LOW.hold_bars).gate[0]
    out = deplant_stage2(streams, edge_bps=BITE_EDGE_BPS, stage2_start_ns=stage2_start)
    for s0, s1 in zip(streams, out):
        if s0.candidate_id.startswith(_PLANT):
            continue
        np.testing.assert_array_equal(
            s0.trades.get_column("ExitPrice").to_numpy(),
            s1.trades.get_column("ExitPrice").to_numpy())


def test_outcome_table_per_cadence():
    assert _outcome(True, True)["verdict"] == "DUAL_CERTIFY"
    assert _outcome(False, True)["verdict"] == "HIGH_ONLY_CERTIFY"
    assert _outcome(True, False)["verdict"] == "LOW_ONLY_CERTIFY"
    both_none = _outcome(False, False)
    assert both_none["verdict"] == "TERMINAL" and both_none["terminal"] is True
    # single-cadence pass never recommends full route-restore
    assert _outcome(False, True)["recommend"] == "P4_high_only"


def test_failure_label_coverage_vs_selection():
    # coverage-limited: e2e ≈ no-search (inflation ~0)
    assert _failure_label(0.055, 0.06) == "coverage_limited"
    # selection-unsafe: e2e materially above no-search
    assert _failure_label(0.05, 0.09) == "selection_unsafe"
