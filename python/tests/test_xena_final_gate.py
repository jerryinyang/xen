"""Tests for xen.xena.final_gate + xen.xena.calibration (INFR-006 Appendix A + WS-6)."""
from __future__ import annotations

import json

import pytest

from xen.xena.calibration import (SegmentLayout, calibration_battery,
                                  dogfood_universe, freeze_registry,
                                  insensitivity_sweep, planted_recovery_stats,
                                  planted_universe, verify_frozen_registry)
from xen.xena.final_gate import (GATE_LEDGER_NAME, GateBudgetExhausted,
                                 GateRetryRefused, run_final_gate)
from xen.xena.oracle import OracleConfig
from xen.xena.search import SearchParams

from tests.test_xena_search import CFG, make_stream

NS = 1_000_000_000
FAST = SearchParams(L=30, n_boot=80, block_bars=64, init_size=3)
SPAN = (0, 4000 * 60 * NS)
LAYOUT = SegmentLayout.from_span(*SPAN)          # 50/30/20 search/ranking/gate
GATE_SEG = LAYOUT.gate


def gate_kwargs(tmp_path, **over):
    kw = dict(gate_segment=GATE_SEG, pass_threshold=0.0, search_F_claim=0.05,
              universe_root=tmp_path, universe_id="XENA-T", evaluation_count=123,
              params=FAST)
    kw.update(over)
    return kw


# --------------------------------------------------------------------------- #
# Final gate
# --------------------------------------------------------------------------- #
def test_final_gate_pass_and_artifact(tmp_path):
    streams = [make_stream(f"win{i}", +40.0, seed=i) for i in range(3)]
    art = run_final_gate({s.candidate_id for s in streams}, streams, CFG,
                         **gate_kwargs(tmp_path))
    assert art["passed"]
    g = art["gross"]
    assert g["F_boot"]["p25"] <= g["F_boot"]["median"] <= g["F_boot"]["p75"]
    assert len(g["decay_windows"]) == 4
    assert "decay_rank_corr" in g
    assert art["binding_block"] == "gross"
    # informational net block present, costed, and its own full protocol
    n = art["net_informational"]
    assert n["costs_charged"] is True and g["costs_charged"] is False
    assert "dd_feasibility" in n and "F_boot" in n
    assert art["evaluation_count"] == 123
    assert (tmp_path / GATE_LEDGER_NAME).exists()
    assert (tmp_path / "xena_final_gate_1.json").exists()
    # deterministic oracle, n_seeds default 1 → zero seed spread
    assert art["gross"]["seed_replication"]["spread"] == 0.0


def test_final_gate_fail_still_spends_slot(tmp_path):
    streams = [make_stream(f"lose{i}", -40.0, seed=i) for i in range(3)]
    art = run_final_gate({s.candidate_id for s in streams}, streams, CFG,
                         **gate_kwargs(tmp_path))
    assert not art["passed"]
    ledger = json.loads((tmp_path / GATE_LEDGER_NAME).read_text())
    assert len(ledger) == 1 and ledger[0]["passed"] is False


def test_gate_budget_cap_2(tmp_path):
    streams = [make_stream("a", +40.0, seed=1), make_stream("b", +40.0, seed=2)]
    run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    run_final_gate({"b"}, streams, CFG, **gate_kwargs(tmp_path))
    with pytest.raises(GateBudgetExhausted):
        run_final_gate({"a", "b"}, streams, CFG, **gate_kwargs(tmp_path))
    # a different universe id still has budget
    art = run_final_gate({"a"}, streams, CFG,
                         **gate_kwargs(tmp_path, universe_id="XENA-U"))
    assert art["universe_id"] == "XENA-U"


def test_same_failed_subset_retry_refused_without_attestation(tmp_path):
    """Q2 second-slot semantics: no free retry of an identical failed subset."""
    streams = [make_stream("a", -40.0, seed=1)]
    art = run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    assert not art["passed"]
    with pytest.raises(GateRetryRefused):
        run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    # with an operator-signed attestation the second slot is usable and recorded
    art2 = run_final_gate({"a"}, streams, CFG,
                          **gate_kwargs(tmp_path,
                                        new_data_attestation="TEST band extended "
                                        "2026-08-01, operator JI"))
    assert art2["new_data_attestation"].startswith("TEST band extended")
    ledger = json.loads((tmp_path / GATE_LEDGER_NAME).read_text())
    assert ledger[1]["new_data_attestation"] is not None


def test_passed_subset_may_regate_without_attestation(tmp_path):
    """Only FAILED rows block a re-gate; a passed subset re-run is not retry-shopping."""
    streams = [make_stream("a", +40.0, seed=1)]
    art = run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    assert art["passed"]
    art2 = run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    assert art2["passed"]


def test_gate_dual_blocks_gross_binding_net_informational(tmp_path):
    """A-4: binding verdict from the gross block; net block informational, costed,
    strictly below gross on a costed stream."""
    from xen.xena.oracle import CandidateStream
    base = make_stream("a", +40.0, seed=1)
    costed = CandidateStream("a", "TEST", base.trades, base.marks, cost_bps=8.0)
    art = run_final_gate({"a"}, [costed], OracleConfig(charge_costs=False),
                         **gate_kwargs(tmp_path))
    assert art["binding_block"] == "gross"
    assert art["gross"]["costs_charged"] is False
    assert art["net_informational"]["costs_charged"] is True
    assert art["net_informational"]["F_point"] < art["gross"]["F_point"]
    # passed reflects the GROSS block regardless of net
    assert art["passed"] == (art["gross"]["F_boot"]["p25"] >= 0.0
                             and art["gross"]["dd_feasibility"]["feasible"])


def test_dd_feasibility_binding_leg(tmp_path):
    """A path breaching the total-DD limit fails the gate even with P25 above threshold."""
    from xen.xena.final_gate import dd_feasibility
    import numpy as np
    # direct unit check: 15% loss vs initial breaches the 10% total limit
    t = np.arange(5, dtype=np.int64) * 3600 * NS
    eq = np.array([100_000.0, 99_000.0, 85_000.0, 101_000.0, 102_000.0])
    dd = dd_feasibility(t, eq, initial_equity=100_000.0)
    assert not dd["feasible"] and dd["worst_total_dd"] == pytest.approx(0.15)
    # clean path is feasible
    dd2 = dd_feasibility(t, np.linspace(100_000, 104_000, 5), initial_equity=100_000.0)
    assert dd2["feasible"]


def test_gate_artifact_carries_dd(tmp_path):
    streams = [make_stream("a", +40.0, seed=1)]
    art = run_final_gate({"a"}, streams, CFG, **gate_kwargs(tmp_path))
    assert art["gross"]["dd_feasibility"]["feasible"] is True
    assert art["net_informational"]["dd_feasibility"] is not None
    assert art["passed"]


def test_search_stage_gap_reported(tmp_path):
    streams = [make_stream("a", +40.0, seed=1)]
    art = run_final_gate({"a"}, streams, CFG,
                         **gate_kwargs(tmp_path, search_F_claim=10.0))
    gap = art["search_stage_gap_p25claim_minus_gate_median"]
    assert gap == pytest.approx(10.0 - art["gross"]["F_boot"]["median"])


# --------------------------------------------------------------------------- #
# Calibration batteries (small smoke scale; full scale is the WS-6 run)
# --------------------------------------------------------------------------- #
BATTERY_KW = dict(config=CFG, n_restarts=2, budget=120, plateau_threshold=0.4,
                  f_floor=0.0, n_folds=3, params=FAST, layout=LAYOUT,
                  purge_ns=60 * 60 * NS)


def test_dogfood_negative_battery_low_fpr(tmp_path):
    bat = calibration_battery(
        universes=3,
        make_universe=lambda s: dogfood_universe(n_candidates=6, seed=s),
        gate_pass_threshold=0.0, gate_workdir=tmp_path,
        **BATTERY_KW)
    assert bat["n_universes"] == 3
    assert bat["certification_rate"] <= 1 / 3   # null universes must (almost) never certify
    # gate pass rate is measured through the real gate path (None only if never certified)
    assert bat["gate_pass_rate"] is not None
    assert bat["gate_pass_rate"] <= bat["certification_rate"]


def test_planted_battery_recovers_edge(tmp_path):
    bat = calibration_battery(
        universes=2,
        make_universe=lambda s: planted_universe(n_planted=3, n_null=4,
                                                 edge_bps=40.0, seed=s),
        gate_pass_threshold=0.0, gate_workdir=tmp_path,
        **BATTERY_KW)
    assert bat["certification_rate"] > 0        # a strong planted edge must certify
    rec = planted_recovery_stats(bat)
    assert rec["planted_fraction_mean"] >= 0.6  # winners dominated by planted candidates


def test_universe_regenerable_from_seed():
    a = dogfood_universe(n_candidates=2, seed=7)
    b = dogfood_universe(n_candidates=2, seed=7)
    for s1, s2 in zip(a, b):
        assert s1.trades.equals(s2.trades) and s1.marks.equals(s2.marks)


# --------------------------------------------------------------------------- #
# v2 path generators (realistic-null battery)
# --------------------------------------------------------------------------- #
def test_path_universe_regenerable_and_shared_path():
    from xen.xena.calibration import path_universe
    a = path_universe(n_planted=1, n_null=2, edge_bps=30.0, seed=5)
    b = path_universe(n_planted=1, n_null=2, edge_bps=30.0, seed=5)
    for s1, s2 in zip(a, b):
        assert s1.trades.equals(s2.trades) and s1.marks.equals(s2.marks)
    # all candidates in one universe share ONE price path (correlated-noise null)
    assert a[0].marks.equals(a[1].marks) and a[1].marks.equals(a[2].marks)
    # path is not flat and stops scale with vol (not all equal)
    import numpy as np
    opens = a[0].marks.get_column("Open").to_numpy()
    assert np.std(opens) > 0
    sd = a[0].trades.get_column("StopDistance").to_numpy()
    assert (sd > 0).all()


def test_path_null_is_zero_expectation():
    """Coin-flip direction ⇒ E[gross]=0 by construction; check across a seed battery."""
    import numpy as np
    from xen.xena.calibration import path_universe
    means = []
    for seed in range(1, 30):
        u = path_universe(n_planted=0, n_null=1, edge_bps=0.0, seed=seed)
        tr = u[0].trades
        d = tr.get_column("Direction").to_numpy()
        ep = tr.get_column("EntryPrice").to_numpy()
        xp = tr.get_column("ExitPrice").to_numpy()
        means.append(float(np.mean(d * (xp - ep) / ep * 1e4)))
    m = np.array(means)
    # battery mean within 2 SE of zero
    assert abs(m.mean()) < 2 * m.std() / np.sqrt(len(m))


def test_path_planted_edge_is_exact_shift():
    import numpy as np
    from xen.xena.calibration import path_universe, regime_gbm_path
    u = path_universe(n_planted=1, n_null=0, edge_bps=25.0, seed=9)
    tr = u[0].trades
    opens = u[0].marks.get_column("Open").to_numpy()
    t = u[0].marks.get_column("CloseTime").to_numpy()
    d = tr.get_column("Direction").to_numpy()
    xp = tr.get_column("ExitPrice").to_numpy()
    xt = tr.get_column("ExitTime").to_numpy()
    idx = np.searchsorted(t, xt)
    raw = opens[idx]
    # exit fill = raw path price shifted favourably by exactly 25 bps
    assert np.allclose(xp, raw * (1.0 + d * 25.0 / 1e4))


def test_costs_charged_in_null_universe():
    """Design item 4: nulls carry realistic round-trip costs (net edge < 0)."""
    u = dogfood_universe(n_candidates=1, seed=3)
    assert u[0].cost_bps > 0


def test_layout_bands_disjoint():
    lay = SegmentLayout.from_span(0, 1000)
    assert lay.search[1] == lay.ranking[0] and lay.ranking[1] == lay.gate[0]
    assert lay.search[0] < lay.search[1] < lay.ranking[1] < lay.gate[1]


# --------------------------------------------------------------------------- #
# Insensitivity sweep + freeze
# --------------------------------------------------------------------------- #
def test_insensitivity_sweep_smoke():
    streams = [make_stream(f"w{i}", +40.0, seed=i) for i in range(4)]
    out = insensitivity_sweep(streams, CFG, budget=40, layout=LAYOUT, base=FAST,
                              L_values=(30, 60), block_values=(32, 64),
                              move_prob_variants=(
                                  {"add": 0.25, "drop": 0.25, "swap": 0.45, "2swap": 0.05},),
                              n_seeds=2)
    assert set(out) == {"L", "block_bars", "move_probs"}
    assert set(out["L"]) == {"30", "60"}


def test_freeze_and_verify_registry(tmp_path):
    path = tmp_path / "frozen.json"
    freeze_registry(params=FAST, plateau_threshold=0.5, f_floor=0.01,
                    gate_pass_threshold=0.0, layout=LAYOUT,
                    battery_summary={"certification_rate": 0.0},
                    out_path=path, operator_signoff="JI 2026-07-10")
    reg = verify_frozen_registry(path)
    assert reg["plateau_threshold"] == 0.5
    # tamper → verification fails
    art = json.loads(path.read_text())
    art["registry"]["plateau_threshold"] = 0.99
    path.write_text(json.dumps(art))
    with pytest.raises(RuntimeError, match="hash mismatch"):
        verify_frozen_registry(path)


# --------------------------------------------------------------------------- #
# Registry enforcement (review F01) + failed-subset similarity report (F03)
# --------------------------------------------------------------------------- #
def _frozen(tmp_path, gate_thr=0.0):
    path = tmp_path / "frozen.json"
    freeze_registry(params=FAST, plateau_threshold=0.5, f_floor=0.01,
                    gate_pass_threshold=gate_thr, layout=LAYOUT,
                    battery_summary={}, out_path=path, operator_signoff="JI")
    return path


def test_gate_registry_binding(tmp_path):
    streams = [make_stream(f"w{i}", +40.0, seed=i) for i in range(3)]
    reg = _frozen(tmp_path)
    # threshold drift from the pin refuses without operator attestation
    with pytest.raises(ValueError, match="threshold-shopping"):
        run_final_gate({"w0"}, streams, CFG,
                       **gate_kwargs(tmp_path, pass_threshold=-1.0, registry_path=reg))
    # params drift refuses too
    with pytest.raises(ValueError, match="search_params"):
        run_final_gate({"w0"}, streams, CFG,
                       **gate_kwargs(tmp_path, registry_path=reg,
                                     params=SearchParams(L=99, n_boot=80,
                                                         block_bars=64, init_size=3)))
    # matching pin runs and records the sha in artifact + ledger
    art = run_final_gate({"w0"}, streams, CFG,
                         **gate_kwargs(tmp_path, registry_path=reg))
    assert art["registry_sha256"] == json.loads(reg.read_text())["sha256"]
    ledger = json.loads((tmp_path / GATE_LEDGER_NAME).read_text())
    assert ledger[-1]["registry_sha256"] == art["registry_sha256"]
    # operator attestation overrides a drifted threshold (recorded verbatim)
    art2 = run_final_gate({"w0", "w1"}, streams, CFG,
                          **gate_kwargs(tmp_path, pass_threshold=-1.0, registry_path=reg,
                                        threshold_override_attestation="JI: recalib"))
    assert art2["threshold_override_attestation"] == "JI: recalib"


def test_gate_reports_similarity_to_prior_failed(tmp_path):
    streams = ([make_stream(f"l{i}", -40.0, seed=i) for i in range(2)]
               + [make_stream("w0", +40.0, seed=9)])
    art1 = run_final_gate({"l0", "l1"}, streams, CFG,
                          **gate_kwargs(tmp_path, pass_threshold=10.0))
    assert not art1["passed"] and art1["max_jaccard_vs_prior_failed"] is None
    # overlapping (but not identical) subset: reported, NOT refused (operator F03)
    art2 = run_final_gate({"l0", "w0"}, streams, CFG, **gate_kwargs(tmp_path))
    assert art2["max_jaccard_vs_prior_failed"] == pytest.approx(1 / 3)
