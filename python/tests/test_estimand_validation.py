"""Tests for the estimand validation gate (INFR-001 WS-2)."""
from __future__ import annotations

from pathlib import Path

import pytest

from xen.estimand_validation import check_no_local_accounting, validate_run

_US2000 = (Path(__file__).resolve().parents[2] / "data" / "strategy_runs" /
           "EXP-014c-4h-s8-e3-extend-z15" /
           "cross_instrument_spread_mr_us2000_4h_20260703_055334")


def test_banned_local_accounting_defs_detected(tmp_path: Path) -> None:
    code = tmp_path / "code"
    code.mkdir()
    (code / "lib.py").write_text(
        "def assemble_realized_bps(df, *, cost_bps):\n    return None\n")
    (code / "ok.py").write_text(
        "from xen.adjudication import assemble_multileg_bps\n")
    report = check_no_local_accounting(code)
    assert not report["ok"]
    assert len(report["banned_defs_found"]) == 1
    assert "lib.py" in report["banned_defs_found"][0]


def test_clean_experiment_code_passes(tmp_path: Path) -> None:
    code = tmp_path / "code"
    code.mkdir()
    (code / "run.py").write_text("from xen.adjudication import reconcile\n")
    assert check_no_local_accounting(code)["ok"]


@pytest.mark.skipif(not _US2000.exists(), reason="US2000 emission not present")
def test_real_run_blocking_pass_and_true_physicality() -> None:
    report = validate_run(_US2000, cost_bps=8.0)
    assert report["blocking_pass"]
    assert report["reconciliation"]["ok"]
    phys = report["physicality"]
    # the corrected estimand: modest return, tiny Sharpe — nothing like the corrupt
    # 110%/yr / Sharpe 6.5 the legacy per-bar series reported (critical-017)
    assert phys["annualised_return"] < 0.10
    assert phys["per_bar_sharpe_annualised"] < 1.0
    assert 0.6 < phys["occupancy"] < 0.8
