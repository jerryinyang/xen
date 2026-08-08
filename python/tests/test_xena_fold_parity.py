"""INFR-007 golden parity gate — the Rust fold kernel (`xena_fold`) must be BITWISE
identical to the Python oracle backend (proposal `xena-infr-update.md` §safety-protocol).

Two layers, both blocking:

1. Synthetic adversarial cases (always run): censored legs, same-timestamp
   exit/entry/mark collisions, single-bar trades, empty/singleton subsets, capacity
   rejection cascades, segment-end censoring, costs on/off, weights, money_per_unit.
   Python and Rust backends are run side by side and compared bitwise.

2. Pinned real corpus (runs when `data/strategy_runs/XENA-001` and the pinned hash file
   are present): (subset, segment) cases derived from the XENA-001 universe; the Rust
   backend must reproduce the sha256 digests pinned from the Python backend at
   `tests/data/xena_fold_parity_hashes.json`. Any future Rust/toolchain upgrade must
   re-prove itself against these pinned hashes (regenerate ONLY via
   `gen_xena_fold_parity_corpus.py` after an operator-approved change).

Equality is bitwise — sha256 over raw array bytes, never `allclose`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.xena.oracle import CandidateStream, OracleConfig, OracleResult, evaluate

xena_fold = pytest.importorskip("xena_fold")

ROOT = Path(__file__).resolve().parents[2]
UNIVERSE = ROOT / "data" / "strategy_runs" / "XENA-001"
HASHES = Path(__file__).parent / "data" / "xena_fold_parity_hashes.json"

NS_MIN = 60_000_000_000  # one minute in ns


# --------------------------------------------------------------------------- #
# digest + comparison helpers
# --------------------------------------------------------------------------- #
def result_digest(res: OracleResult) -> str:
    """sha256 over the raw bytes of every verdict-bearing output (bitwise, no allclose)."""
    h = hashlib.sha256()
    h.update(res.equity_times.tobytes())
    h.update(res.equity.tobytes())
    h.update(np.float64(res.F_point).tobytes())
    h.update(np.int64(res.n_admitted).tobytes())
    h.update(np.int64(res.n_rejected).tobytes())
    for df in (res.ledger, res.rejected):
        for name, dtype in df.schema.items():
            col = df.get_column(name)
            if dtype == pl.Utf8:
                h.update("\x00".join(col.to_list()).encode())
            else:
                h.update(np.ascontiguousarray(col.to_numpy()).tobytes())
    return h.hexdigest()


def assert_bitwise_equal(a: OracleResult, b: OracleResult) -> None:
    assert a.equity_times.tobytes() == b.equity_times.tobytes()
    assert a.equity.tobytes() == b.equity.tobytes()
    assert np.float64(a.F_point).tobytes() == np.float64(b.F_point).tobytes()
    assert a.ledger.equals(b.ledger)
    assert a.rejected.equals(b.rejected)
    assert result_digest(a) == result_digest(b)


def both(subset, streams, config, segment=None) -> tuple[OracleResult, OracleResult]:
    rp = evaluate(subset, streams, replace(config, backend="python"), segment=segment)
    rr = evaluate(subset, streams, replace(config, backend="rust"), segment=segment)
    return rp, rr


# --------------------------------------------------------------------------- #
# synthetic adversarial universe
# --------------------------------------------------------------------------- #
def _marks(t0: int, n: int, opens: list[float]) -> pl.DataFrame:
    return pl.DataFrame({"CloseTime": [t0 + i * NS_MIN for i in range(n)],
                         "Open": opens[:n]})


def _trades(rows: list[tuple]) -> pl.DataFrame:
    return pl.DataFrame(
        {"EntryTime": [r[0] for r in rows], "ExitTime": [r[1] for r in rows],
         "Direction": [float(r[2]) for r in rows], "EntryPrice": [r[3] for r in rows],
         "ExitPrice": [r[4] for r in rows], "StopDistance": [r[5] for r in rows],
         "Censored": [bool(r[6]) for r in rows]},
        schema={"EntryTime": pl.Int64, "ExitTime": pl.Int64, "Direction": pl.Float64,
                "EntryPrice": pl.Float64, "ExitPrice": pl.Float64,
                "StopDistance": pl.Float64, "Censored": pl.Boolean})


@pytest.fixture()
def synth_streams() -> list[CandidateStream]:
    t0 = 1_600_000_000_000_000_000
    m = t0  # alias
    opens_a = [100.0, 101.5, 99.75, 102.25, 101.0, 103.5, 102.0, 104.25, 103.0, 105.0]
    opens_b = [50.0, 50.25, 49.5, 51.0, 50.75, 52.25, 51.5, 53.0, 52.25, 54.0]
    # A: normal + single-bar (exit before next bar close) + censored tail
    a_trades = _trades([
        (m + 1 * NS_MIN, m + 4 * NS_MIN, 1, 100.7, 102.1, 0.9, False),
        (m + 2 * NS_MIN, m + 2 * NS_MIN + 10_000_000_000, -1, 101.3, 101.1, 0.5, False),
        (m + 6 * NS_MIN, m + 20 * NS_MIN, 1, 102.4, 0.0, 1.3, True),   # censored leg
    ])
    # B: same-timestamp collisions — B entry at A's exit time and at A's mark times
    b_trades = _trades([
        (m + 4 * NS_MIN, m + 7 * NS_MIN, -1, 50.6, 51.4, 0.7, False),  # entry == A exit t
        (m + 5 * NS_MIN, m + 8 * NS_MIN, 1, 52.1, 52.9, 0.4, False),
        (m + 8 * NS_MIN, m + 9 * NS_MIN, 1, 52.4, 53.8, 0.6, False),
    ])
    # C: dense entries to force capacity rejections under a tight cap
    c_trades = _trades([
        (m + k * NS_MIN, m + (k + 2) * NS_MIN, (1 if k % 2 else -1),
         100.0 + 0.1 * k, 100.5 + 0.1 * k, 0.3, False) for k in range(1, 8)
    ])
    return [
        CandidateStream("A", "SYNA", a_trades, _marks(t0, 10, opens_a), 4.0),
        CandidateStream("B", "SYNB", b_trades, _marks(t0, 10, opens_b), 2.5,
                        money_per_unit=2.5),
        CandidateStream("C", "SYNA", c_trades, _marks(t0, 10, opens_a), 6.0),
    ]


BASE = OracleConfig()
DIRECTIVE = {"reason": "INFR-007 parity corpus (pinned costed cases)",
             "scope": "parity-corpus"}


def test_full_subset_zero_cost_default(synth_streams):
    """INFR-022: default oracle config is zero-cost — the costed pin is inert."""
    rp, rr = both({"A", "B", "C"}, synth_streams, BASE)
    assert rp.n_admitted > 0
    assert (rp.ledger.get_column("CostMoney") == 0.0).all()
    assert_bitwise_equal(rp, rr)


def test_full_subset_directive_costed(synth_streams):
    """Directive-backed costed configs still exercise the cost branch bit-identically."""
    cfg = replace(BASE, charge_costs=True, operator_cost_directive=DIRECTIVE)
    rp, rr = both({"A", "B", "C"}, synth_streams, cfg)
    assert rp.n_admitted > 0
    assert (rp.ledger.get_column("CostMoney") > 0).any()
    assert_bitwise_equal(rp, rr)


def test_rejection_cascade(synth_streams):
    cfg = replace(BASE, r_max=0.011, risk_per_position=0.005)
    rp, rr = both({"A", "B", "C"}, synth_streams, cfg)
    assert rp.n_rejected > 0, "case must exercise the rejection branch"
    assert_bitwise_equal(rp, rr)


def test_cost_free_with_weights(synth_streams):
    cfg = replace(BASE, charge_costs=False, weights={"A": 0.5, "C": 2.0})
    rp, rr = both({"A", "B", "C"}, synth_streams, cfg)
    assert_bitwise_equal(rp, rr)


def test_empty_and_singleton_subsets(synth_streams):
    for subset in (set(), {"A"}, {"B"}, {"C"}):
        rp, rr = both(subset, synth_streams, BASE)
        assert_bitwise_equal(rp, rr)


def test_segment_end_censoring(synth_streams):
    t0 = 1_600_000_000_000_000_000
    # segment ends mid-universe: open positions censored at the last in-segment open
    seg = (t0, t0 + 5 * NS_MIN + 1)
    rp, rr = both({"A", "B", "C"}, synth_streams, BASE, segment=seg)
    assert bool(rp.ledger.get_column("Censored").any()), "case must censor a leg"
    assert_bitwise_equal(rp, rr)


def test_segment_excluding_all(synth_streams):
    t0 = 1_600_000_000_000_000_000
    seg = (t0 - 100 * NS_MIN, t0 - 50 * NS_MIN)
    rp, rr = both({"A", "B"}, synth_streams, BASE, segment=seg)
    assert rp.n_admitted == 0
    assert_bitwise_equal(rp, rr)


# --------------------------------------------------------------------------- #
# pinned real corpus (XENA-001)
# --------------------------------------------------------------------------- #
def _load_xena001_streams() -> list[CandidateStream]:
    import sys
    code_dir = ROOT / "python" / "experiments" / "XENA-001" / "code"
    sys.path.insert(0, str(code_dir))
    try:
        from run_search import load_streams
        return load_streams()
    finally:
        sys.path.remove(str(code_dir))


def corpus_cases(ids: list[str], results_dir: Path) -> list[dict]:
    """Deterministic corpus spec: seeded random subsets over segment variants, plus the
    12 real restart best-subsets. Shared by the generator and the test."""
    start = int(np.datetime64("2021-06-02T00:01", "ns").astype(np.int64))
    end = int(np.datetime64("2023-03-08T00:00", "ns").astype(np.int64))
    third = (end - start) // 3
    segments = [(start, end), (start, start + third),
                (start + third, start + 2 * third), (start + 2 * third, end)]
    cases: list[dict] = []
    rng = np.random.default_rng(20260712)
    for i in range(488):
        seg = segments[i % len(segments)]
        size = int(rng.integers(1, 91))
        subset = sorted(str(c) for c in rng.choice(ids, size=size, replace=False))
        cases.append({"case": f"rand-{i:03d}", "subset": subset, "segment": list(seg),
                      "charge_costs": bool(i % 5 == 0)})
    for rid in range(12):
        f = results_dir / f"search_restart_{rid:02d}.json"
        if f.exists():
            best = json.loads(f.read_text())["best_subset"]
            cases.append({"case": f"best-r{rid:02d}", "subset": sorted(best),
                          "segment": [start, end], "charge_costs": False})
    return cases


@pytest.mark.skipif(not UNIVERSE.exists(), reason="XENA-001 universe data not present")
@pytest.mark.skipif(not HASHES.exists(), reason="pinned parity hashes not generated")
def test_pinned_corpus_rust_backend():
    pinned = json.loads(HASHES.read_text())
    streams = _load_xena001_streams()
    ids = sorted(s.candidate_id for s in streams)
    cases = corpus_cases(ids, ROOT / "python" / "experiments" / "XENA-001" / "results")
    assert len(cases) == len(pinned["cases"]), "corpus spec drifted from pinned file"
    mismatches = []
    for case, exp in zip(cases, pinned["cases"]):
        assert case["case"] == exp["case"]
        cfg = OracleConfig(charge_costs=case["charge_costs"], backend="rust",
                           operator_cost_directive=DIRECTIVE
                           if case["charge_costs"] else None)
        res = evaluate(set(case["subset"]), streams, cfg,
                       segment=tuple(case["segment"]))
        if result_digest(res) != exp["digest"]:
            mismatches.append(case["case"])
    assert not mismatches, f"bitwise parity broken on {len(mismatches)} cases: {mismatches[:10]}"
