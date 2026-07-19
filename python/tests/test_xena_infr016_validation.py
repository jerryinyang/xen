"""INFR-016 framework validation as regression guards (synthetic ranking + real replay)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_VAL = Path(__file__).resolve().parents[1] / "experiments" / "INFR-016" / "validation"
sys.path.insert(0, str(_VAL))

import htfcap_replay  # noqa: E402
import synth_ranking_validation as srv  # noqa: E402


def test_synthetic_ranking_discriminates():
    """Old costless-extensive+top-1 reproduces the HTFCAP failure; the minimal layers recover
    the true deployable ranking and expose the adversaries (single layer alone is fooled)."""
    res = srv.run()
    failed = [k for k, v in res["checks"].items() if not v]
    assert not failed, f"synthetic validation failed checks: {failed}"


@pytest.mark.skipif(not htfcap_replay.RUNS.exists(),
                    reason="no XENA-HTFCAP-001 emissions on this machine")
def test_htfcap_known_answer_replay():
    """Report layers over the REAL HTFCAP emissions reproduce the redo: BTC adx25 H32/H64
    sign-clean, SOL v1.5 suggestive (p≈0.22), a non-empty clean set the binder had hidden."""
    res = htfcap_replay.run()
    failed = [k for k, v in res["checks"].items() if not v]
    assert not failed, f"HTFCAP replay failed checks: {failed}"
