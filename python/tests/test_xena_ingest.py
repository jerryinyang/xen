"""Tests for xen.xena.ingest (INFR-006 WS-1) — toy 3-candidate universe through the
blocking candidate gate, plus every gate failure mode."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.xena.ingest import (GATE_ARTIFACT_NAME, gate_candidate, gate_universe,
                             load_candidate, load_universe, xena_money_per_unit)
from xen.xena.oracle import OracleConfig, evaluate

T0 = datetime(2024, 1, 1)
ANALYSIS_END = "2025-01-01T00:00:00"


def write_run(run_dir: Path, *, n_bars: int = 200, n_trades: int = 5,
              price0: float = 100.0, drift: float = 0.01,
              analysis_end: str | None = ANALYSIS_END,
              stop: float = 1.0, corrupt_realized: bool = False,
              fence_breach: bool = False) -> None:
    """Synthesize a minimal standard emission (positions + cis_trades + metadata)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    times = [T0 + timedelta(minutes=15 * i) for i in range(n_bars)]
    opens = price0 + drift * np.arange(n_bars)
    pl.DataFrame({"SourceCloseTime": times, "RealOpen": opens}).with_columns(
        pl.col("SourceCloseTime").dt.cast_time_unit("ns")).write_parquet(
        run_dir / "positions.parquet")

    rows = []
    for k in range(n_trades):
        ei = 10 + 30 * k
        xi = ei + 20
        if fence_breach and k == n_trades - 1:
            entry_t = datetime(2025, 6, 1)
            exit_t = datetime(2025, 6, 2)
        else:
            entry_t, exit_t = times[ei], times[xi]
        ep, xp, d = float(opens[ei]), float(opens[xi]) + 0.5, 1.0
        rb = d * (xp - ep) / ep * 1e4
        if corrupt_realized and k == 0:
            rb += 50.0
        rows.append({"EntryTime": entry_t, "ExitTime": exit_t, "Direction": 1,
                     "EntryFillPrice": ep, "ExitFillPrice": xp, "RealizedBps": rb,
                     "Censored": 0, "SlPrice": ep - stop})
    pl.DataFrame(rows).with_columns(pl.col("EntryTime").dt.cast_time_unit("ns"),
                                    pl.col("ExitTime").dt.cast_time_unit("ns")
                                    ).write_parquet(run_dir / "cis_trades.parquet")
    meta = {} if analysis_end is None else {"AnalysisEndUtc": analysis_end}
    (run_dir / "run_metadata.json").write_text(json.dumps(meta), encoding="utf-8")


def write_universe(root: Path, n: int = 3) -> Path:
    cands = []
    for i in range(n):
        write_run(root / f"c{i}", drift=0.01 * (i + 1))
        cands.append({"candidate_id": f"c{i}", "run_dir": f"c{i}", "symbol": "TEST",
                      "cost_bps": 1.0})
    mpath = root / "universe_manifest.json"
    mpath.write_text(json.dumps({"universe_id": "XENA-TOY", "candidates": cands}),
                     encoding="utf-8")
    return mpath


# --------------------------------------------------------------------------- #
def test_load_candidate_maps_contract(tmp_path):
    write_run(tmp_path / "r")
    s = load_candidate(tmp_path / "r", candidate_id="a", symbol="TEST", cost_bps=1.0)
    assert s.trades.height == 5
    assert (s.trades.get_column("StopDistance") == 1.0).all()
    assert s.marks.height == 200


def test_gate_passes_clean_run(tmp_path):
    write_run(tmp_path / "r")
    rep = gate_candidate(tmp_path / "r", candidate_id="a", symbol="TEST", cost_bps=1.0)
    assert rep["blocking_pass"], rep["checks"]
    assert all(c["pass"] for c in rep["checks"].values())


@pytest.mark.parametrize("kw,failing_check", [
    ({"fence_breach": True}, "fence"),
    ({"analysis_end": None}, "fence"),
    ({"stop": 0.0}, "stop_contract"),
    ({"corrupt_realized": True}, "fill_consistency"),
])
def test_gate_failure_modes(tmp_path, kw, failing_check):
    write_run(tmp_path / "r", **kw)
    rep = gate_candidate(tmp_path / "r", candidate_id="a", symbol="TEST", cost_bps=1.0)
    assert not rep["blocking_pass"]
    assert not rep["checks"][failing_check]["pass"]


def test_gate_missing_slprice_is_schema_fail(tmp_path):
    write_run(tmp_path / "r")
    cis = pl.read_parquet(tmp_path / "r" / "cis_trades.parquet").drop("SlPrice")
    cis.write_parquet(tmp_path / "r" / "cis_trades.parquet")
    rep = gate_candidate(tmp_path / "r", candidate_id="a", symbol="TEST", cost_bps=1.0)
    assert not rep["blocking_pass"]
    assert not rep["checks"]["schema"]["pass"]


# --------------------------------------------------------------------------- #
def test_universe_gate_and_load_toy_3(tmp_path):
    mpath = write_universe(tmp_path, 3)
    art = gate_universe(mpath)
    assert art["blocking_pass"] and art["n_pass"] == 3
    assert (tmp_path / GATE_ARTIFACT_NAME).exists()
    uni = load_universe(mpath)
    assert uni.universe_id == "XENA-TOY" and len(uni.streams) == 3
    # end-to-end: oracle evaluates the full toy universe
    res = evaluate({s.candidate_id for s in uni.streams}, uni.streams, OracleConfig())
    assert res.n_admitted == 15


def test_load_refuses_without_gate(tmp_path):
    mpath = write_universe(tmp_path, 2)
    with pytest.raises(RuntimeError, match="run gate_universe first"):
        load_universe(mpath)


def test_load_refuses_failing_gate(tmp_path):
    mpath = write_universe(tmp_path, 2)
    write_run(tmp_path / "c1", fence_breach=True)  # corrupt one candidate
    art = gate_universe(mpath)
    assert not art["blocking_pass"]
    with pytest.raises(RuntimeError, match="FAILING"):
        load_universe(mpath)


def test_money_per_unit_conventions():
    assert xena_money_per_unit("EURUSD") == 1.0
    assert xena_money_per_unit("USTEC") == 1.0
    assert xena_money_per_unit("XAUUSD") == 1.0
    # USD-base / cross / non-USD-quoted CFD: rate mandatory
    assert xena_money_per_unit("USDJPY", quote_usd_rate=1 / 155.0) == pytest.approx(1 / 155.0)
    assert xena_money_per_unit("EURJPY", quote_usd_rate=1 / 155.0) == pytest.approx(1 / 155.0)
    assert xena_money_per_unit("JP225", quote_usd_rate=1 / 155.0) == pytest.approx(1 / 155.0)
    for sym in ("USDJPY", "JP225", "EU50", "UK100"):
        with pytest.raises(ValueError, match="quote_usd_rate"):
            xena_money_per_unit(sym)


def test_load_refuses_stale_gate(tmp_path):
    mpath = write_universe(tmp_path, 2)
    gate_universe(mpath)
    # add a candidate after gating → stale artifact
    manifest = json.loads(mpath.read_text())
    write_run(tmp_path / "c9")
    manifest["candidates"].append({"candidate_id": "c9", "run_dir": "c9",
                                   "symbol": "TEST", "cost_bps": 1.0})
    mpath.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="stale"):
        load_universe(mpath)
