"""INFR-022 Task 4 — PSR end-to-end smoke (§4.4).

Three layers, one contract: wherever a mean trade / mean leg return in bps is reported,
`psr` + `psr_n` sit beside it, computed from the SAME per-trade series and population
(never another population's n). Covers:

1. unit tests on `xen.evaluation.psr` / `psr_row`;
2. XENA report-layer pairing on `gross_mean_bps` (`report_layer.psr_layer`);
3. a synthetic multi-row analysis artifact with mean + `psr` + `psr_n` aligned per row.
"""
from __future__ import annotations

import numpy as np
import pytest

from xen.evaluation import psr, psr_row
from xen.xena.report_layer import psr_layer


def _series(mean_bps: float, n: int, noise_bps: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(mean_bps, noise_bps, n)


def test_unit_psr_and_row() -> None:
    x = _series(3.0, 120, 10.0, seed=7)
    out = psr(x)
    assert out["n"] == 120
    assert 0.0 <= out["psr"] <= 1.0
    assert out["sr_hat"] == pytest.approx(float(np.mean(x) / np.std(x)), abs=1e-12)
    row = psr_row(x)
    assert row == {"psr": out["psr"], "psr_n": 120}


def test_xena_report_layer_pairs_gross_mean_bps() -> None:
    """Economics-disclosure style: gross_mean_bps row gains a psr_layer on the same series."""
    x = _series(2.4, 200, 12.0, seed=11)
    out = psr(x)
    rep = psr_layer("C1-USTEC-1H5M-H05X-V00", avg_trade_bps=float(np.mean(x)),
                    psr=out["psr"], n=out["n"])
    assert rep.layer == "psr"
    assert rep.supporting["psr_n"] == out["n"]
    assert rep.supporting["avg_trade_bps"] == pytest.approx(float(np.mean(x)))
    assert rep.to_dict()["is_gate"] is False


def test_synthetic_multi_row_artifact_aligned() -> None:
    """Multi-stratum analysis artifact: every row carries mean + psr + psr_n from the SAME
    series; psr_n matches the series length that produced the mean."""
    strata = [
        ("crypto-low", 2.1, 250, 9.0, 1),
        ("crypto-high", -1.4, 60, 11.0, 2),
        ("ctrader", 0.6, 14, 7.0, 3),      # small n — still reported with its count
    ]
    artifact = []
    for name, mean_bps, n, noise_bps, seed in strata:
        x = _series(mean_bps, n, noise_bps, seed)
        row = {"stratum": name, "avg_trade_bps": float(np.mean(x))}
        row.update(psr_row(x))             # psr + psr_n on the same vector
        artifact.append(row)

    for row, (name, mean_bps, n, _noise, _seed) in zip(artifact, strata, strict=True):
        assert row["psr_n"] == n == len(_series(mean_bps, n, 1.0, 0))  # same n as the mean
        assert np.isfinite(row["psr"]) or n < 2
        if n >= 2:
            assert 0.0 <= row["psr"] <= 1.0
    # co-presence: every mean row carries the pair
    assert all({"avg_trade_bps", "psr", "psr_n"} <= set(r) for r in artifact)
    # the small-n row (n=14) is present with its psr, not suppressed
    assert artifact[2]["psr_n"] == 14
