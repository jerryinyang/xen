"""INFR-014 structural tests — factories, L-26 refuse, seeds, next-open, registry schema."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from xen.xena.calibration_bybit import (
    BITE_SELECT_MIN,
    BITE_SURVIVAL_MAX,
    CONFIRM_SEEDS,
    DESIGN_SEEDS,
    IntegrityError,
    assert_seed_disjoint,
    assert_stage1_net_binding,
    bybit_cost_bps_for_hold,
    factory_fingerprint,
    make_episode_null_universe,
    make_filter_null_universe,
    next_open_sanity_artifact,
    verify_bybit_registry,
    write_bybit_registry,
)
from xen.xena.calibration_p3b import LOW
from xen.xena.fill_basis import next_open_discriminating_control, reprice_entries_to_next_open
from xen.xena.calibration_pc import c_layout


def test_factories_differ():
    assert factory_fingerprint(make_filter_null_universe) != factory_fingerprint(
        make_episode_null_universe
    )


def test_filter_universe_has_base_and_filt():
    streams = make_filter_null_universe(91000, LOW, n_candidates=64)
    ids = [s.candidate_id for s in streams]
    assert any(i.startswith("base") for i in ids)
    assert any(i.startswith("filt") for i in ids)
    assert len(streams) == 64
    # costs must be positive Bybit RT (not flat silent 0)
    assert all(s.cost_bps > 0 for s in streams)


def test_episode_universe_episode_shaped():
    streams = make_episode_null_universe(91000, LOW, n_candidates=16)
    assert len(streams) == 16
    # variable holds
    holds = []
    for s in streams:
        et = s.trades.get_column("EntryTime").to_numpy()
        xt = s.trades.get_column("ExitTime").to_numpy()
        holds.extend(((xt - et) / 1e9 / 3600.0).tolist())
    assert len(set(np.round(holds, 2))) > 1  # not fixed-H only


def test_hard_refuse_costless_stage1():
    with pytest.raises(IntegrityError):
        assert_stage1_net_binding(charge_costs=False, score_kind="g_net")
    with pytest.raises(IntegrityError):
        assert_stage1_net_binding(charge_costs=True, score_kind="g_gross")
    assert_stage1_net_binding(charge_costs=True, score_kind="g_net")


def test_seed_disjoint():
    assert_seed_disjoint()
    assert DESIGN_SEEDS["low"] == 91000
    assert CONFIRM_SEEDS["high"] == 94000


def test_bybit_cost_positive_gap():
    c = bybit_cost_bps_for_hold("BTCUSDT", hold_hours=8.0)
    # fee RT 11.0 + spread 5.0 + funding 1.0 = 17.0 at 8h hold
    assert c >= 16.0


def test_next_open_control_runs():
    art = next_open_sanity_artifact(seed=7)
    assert art["control"] == "next_open_discriminating"
    assert art["lesson"] == "L-27"
    assert art["n_legs"] > 0


def test_reprice_preserves_exit():
    streams = make_filter_null_universe(11, LOW, n_candidates=4)
    s = streams[0]
    tr2 = reprice_entries_to_next_open(s.trades, s.marks)
    np.testing.assert_array_equal(
        s.trades.get_column("ExitPrice").to_numpy(),
        tr2.get_column("ExitPrice").to_numpy(),
    )


def test_registry_schema_and_verify(tmp_path: Path):
    # minimal synthetic certifiable class results
    design_ok = {
        "design_ok": True,
        "frozen_procedure": {
            "binder": "two_stage_sample_split",
            "stage1_score_kind": "g_net",
            "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "embargo_frac": 0.20,
            "n_boot": 200,
            "block_legs": 1,
            "alpha": 0.05,
            "design_bite_ok": True,
        },
    }
    confirm = {
        "outcome": {
            "verdict": "DUAL_CERTIFY",
            "recommend": "route_both",
            "terminal": False,
        },
        "per_cadence": {
            "low": {"certified": True, "e2e_alpha": 0.03, "no_search_cov": 0.02},
            "high": {"certified": True, "e2e_alpha": 0.04, "no_search_cov": 0.02},
        },
        "procedure": design_ok["frozen_procedure"],
    }
    path = tmp_path / "bybit_pc_frozen_registry.json"
    art = write_bybit_registry(
        {
            "CLS-FILTER": {"design": design_ok, "confirm": confirm},
            "CLS-EPISODE": {
                "design": design_ok,
                "confirm": {
                    "outcome": {
                        "verdict": "TERMINAL",
                        "recommend": "TERMINAL_cannot_certify",
                        "terminal": True,
                    },
                    "per_cadence": {},
                    "procedure": design_ok["frozen_procedure"],
                },
            },
        },
        out_path=path,
        selection_rule_default_hash="abc",
        next_open_artifact={"n_legs": 1},
    )
    assert "sha256" in art
    reg = verify_bybit_registry(path)
    assert reg["schema"].startswith("xena.infr014")
    assert reg["pin_usage"]["limit_print_sole_certify_forbidden"] is True
    assert reg["limit_entry_cells"] is False
    # tamper → fail
    blob = json.loads(path.read_text())
    blob["registry"]["limit_entry_cells"] = True
    path.write_text(json.dumps(blob))
    with pytest.raises(IntegrityError):
        verify_bybit_registry(path)


def test_bite_thresholds_match_design():
    assert BITE_SELECT_MIN == 0.5
    assert BITE_SURVIVAL_MAX == 0.125


def test_c_layout_embargo_frac_inherited():
    lay = c_layout(6000, 20, embargo_frac=0.20)
    span = 6000 * 60 * 1_000_000_000
    assert lay.gate[0] - lay.ranking[1] == int(0.20 * span)


def test_no_search_coverage_respects_caller_seed_bases():
    """QA Issue 9: coverage must not re-pin DESIGN seeds when confirm bases are set."""
    from xen.xena.calibration_bybit import (
        CONFIRM_SEEDS,
        DESIGN_SEEDS,
        no_search_coverage,
        _set_seeds,
    )
    from xen.xena.calibration_p3b import ScaleSpec

    scale = ScaleSpec("toy", n_null=4, n_cand=8, budget=20, n_restarts=1,
                      n_power=1, n_coverage=4)
    _set_seeds(CONFIRM_SEEDS["low"], CONFIRM_SEEDS["high"])
    cov = no_search_coverage(
        "CLS-FILTER", LOW, scale=scale, n_universes=4, alpha=0.05,
    )
    assert cov["seed_bases"] == dict(CONFIRM_SEEDS)
    seeds = [r["seed"] for r in cov["rows"]]
    # low cadence uses SEED_BASE_LOW = confirm low
    assert all(s >= CONFIRM_SEEDS["low"] for s in seeds)
    assert all(s < DESIGN_SEEDS["high"] or s >= CONFIRM_SEEDS["low"] for s in seeds)
    # must not be design-bank bases
    assert cov["seed_bases"]["low"] != DESIGN_SEEDS["low"]
    assert min(seeds) >= CONFIRM_SEEDS["low"]


def test_verify_void_priors_required():
    """QA Issue 12: void_priors must list VOID chapter pins."""
    design_ok = {
        "design_ok": True,
        "frozen_procedure": {
            "binder": "two_stage_sample_split",
            "stage1_score_kind": "g_net",
            "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "embargo_frac": 0.20,
            "n_boot": 200,
            "block_legs": 1,
            "alpha": 0.05,
            "design_bite_ok": True,
        },
    }
    confirm = {
        "outcome": {
            "verdict": "DUAL_CERTIFY",
            "recommend": "route_both",
            "terminal": False,
        },
        "per_cadence": {
            "low": {"certified": True, "e2e_alpha": 0.03, "no_search_cov": 0.02},
            "high": {"certified": True, "e2e_alpha": 0.04, "no_search_cov": 0.02},
        },
        "procedure": design_ok["frozen_procedure"],
    }
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "reg.json"
        write_bybit_registry(
            {
                "CLS-FILTER": {"design": design_ok, "confirm": confirm},
                "CLS-EPISODE": {
                    "design": design_ok,
                    "confirm": {
                        "outcome": {
                            "verdict": "TERMINAL",
                            "recommend": "TERMINAL_cannot_certify",
                            "terminal": True,
                        },
                        "per_cadence": {},
                        "procedure": design_ok["frozen_procedure"],
                    },
                },
            },
            out_path=path,
        )
        reg = verify_bybit_registry(path)
        assert "db87dc1a" in " ".join(reg["void_priors"])
        # strip a void prior → verify fails
        art = json.loads(path.read_text())
        art["registry"]["void_priors"] = []
        blob = json.dumps(art["registry"], sort_keys=True).encode()
        import hashlib
        art["sha256"] = hashlib.sha256(blob).hexdigest()
        path.write_text(json.dumps(art))
        with pytest.raises(IntegrityError, match="void_priors"):
            verify_bybit_registry(path)
