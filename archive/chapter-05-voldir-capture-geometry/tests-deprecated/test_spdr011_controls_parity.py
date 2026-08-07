"""A13 parity corpus — the optimised timing match must reproduce the pre-A13 algorithm exactly.

The reference below is a verbatim copy of the pre-A13 `matched_random_timing` pool/selection
logic (full candidate scan). A13 only replaces the scan with an exact-cell bucket index, so
every emitted row — including `beta_distance` floats and the RNG-chosen candidate — must be
bit-identical. Any divergence is an integrity failure, not a tolerance question.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "python/experiments/SPDR-011/code"

EXACT = (
    "symbol",
    "band",
    "direction",
    "utc_slot",
    "vol_tercile",
    "calendar_third",
    "occupancy",
)


def _load(name: str):
    path = CODE_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"spdr011_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controls = _load("controls")


def reference_matched_random_timing(
    live: pl.DataFrame,
    candidates: pl.DataFrame,
    *,
    n_seeds: int,
    seed0: int,
) -> pl.DataFrame:
    """Pre-A13 implementation, preserved verbatim as the parity reference."""
    live_rows = live.sort("event_id").to_dicts()
    candidate_rows = candidates.sort("candidate_id").to_dicts()
    results: list[dict[str, Any]] = []
    for seed in range(seed0, seed0 + n_seeds):
        rng = np.random.default_rng(seed)
        used: set[str] = set()
        for event in live_rows:
            pool = [
                row
                for row in candidate_rows
                if row["candidate_id"] not in used
                and row["trade_day"] != event["trade_day"]
                and all(row[name] == event[name] for name in EXACT)
            ]
            if not pool:
                results.append(
                    {
                        "seed": seed,
                        "event_id": event["event_id"],
                        "candidate_id": None,
                        "matched_trade_day": None,
                        "beta_distance": None,
                        "match_reason": "NO_EXACT_CELL_CANDIDATE",
                        **{name: event[name] for name in EXACT},
                    }
                )
                continue
            distances = np.asarray(
                [abs(float(row["beta60"]) - float(event["beta60"])) for row in pool]
            )
            ordered_indices = sorted(
                range(len(pool)),
                key=lambda index: (distances[index], pool[index]["candidate_id"]),
            )
            nearest_five = ordered_indices[:5]
            chosen = pool[int(rng.choice(nearest_five))]
            used.add(chosen["candidate_id"])
            results.append(
                {
                    "seed": seed,
                    "event_id": event["event_id"],
                    "candidate_id": chosen["candidate_id"],
                    "matched_trade_day": chosen["trade_day"],
                    "beta_distance": abs(
                        float(chosen["beta60"]) - float(event["beta60"])
                    ),
                    "match_reason": None,
                    **{name: event[name] for name in EXACT},
                }
            )
    return pl.DataFrame(results, infer_schema_length=None).sort(["seed", "event_id"])


def _corpus(
    *,
    n_live: int,
    n_candidates: int,
    n_days: int,
    seed: int,
    n_symbols: int = 5,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(seed)
    symbols = np.array(
        ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"][:n_symbols]
    )
    thirds = np.array(["T1", "T2", "T3"])
    slots = np.array([0, 4, 8, 12, 16, 20])
    terciles = np.array(["HIGH", "MID", "LOW"])

    def frame(n: int, id_column: str, prefix: str) -> pl.DataFrame:
        return pl.DataFrame(
            {
                id_column: [f"{prefix}{index:05d}" for index in range(n)],
                "trade_day": [f"d{index % n_days:04d}" for index in range(n)],
                "beta60": rng.normal(1.0, 0.3, n),
                "symbol": symbols[rng.integers(0, len(symbols), n)],
                "band": ["DESIGN"] * n,
                "direction": rng.choice([-1.0, 1.0], n),
                "utc_slot": slots[rng.integers(0, len(slots), n)],
                "vol_tercile": terciles[rng.integers(0, len(terciles), n)],
                "calendar_third": thirds[rng.integers(0, len(thirds), n)],
                "occupancy": [1] * n,
            }
        )

    return frame(n_live, "event_id", "e"), frame(n_candidates, "candidate_id", "c")


PARITY_CASES = [
    pytest.param(40, 900, 60, 11, 3, id="dense-pool"),
    pytest.param(60, 300, 40, 12, 5, id="scarce-pool-exhaustion"),
    pytest.param(30, 120, 12, 13, 5, id="tight-days-forces-no-candidate"),
    pytest.param(25, 2000, 90, 14, 5, id="wide-candidate-scan"),
]


@pytest.mark.parametrize("n_live,n_candidates,n_days,seed,n_symbols", PARITY_CASES)
def test_matched_random_timing_is_bit_identical_to_pre_a13(
    n_live: int, n_candidates: int, n_days: int, seed: int, n_symbols: int
) -> None:
    live, candidates = _corpus(
        n_live=n_live,
        n_candidates=n_candidates,
        n_days=n_days,
        seed=seed,
        n_symbols=n_symbols,
    )
    expected = reference_matched_random_timing(
        live, candidates, n_seeds=6, seed0=41_000
    )
    actual = controls.matched_random_timing(
        live, candidates, n_seeds=6, seed0=41_000
    )
    assert actual.schema == expected.schema
    assert actual.equals(expected)


def test_parity_corpus_exercises_both_match_outcomes() -> None:
    """A parity corpus that never fails to match would not prove the fallback path."""
    live, candidates = _corpus(
        n_live=30, n_candidates=120, n_days=12, seed=13, n_symbols=5
    )
    result = controls.matched_random_timing(
        live, candidates, n_seeds=6, seed0=41_000
    )
    reasons = set(result["match_reason"].unique().to_list())
    assert None in reasons, "corpus never produced a successful match"
    assert "NO_EXACT_CELL_CANDIDATE" in reasons, "corpus never exhausted a cell"


def test_seed_independence_holds_after_a13() -> None:
    """Each seed must be reproducible on its own, exactly as a 1-seed battery call."""
    live, candidates = _corpus(
        n_live=40, n_candidates=900, n_days=60, seed=11, n_symbols=3
    )
    batch = controls.matched_random_timing(
        live, candidates, n_seeds=4, seed0=41_000
    )
    for offset in range(4):
        single = controls.matched_random_timing(
            live, candidates, n_seeds=1, seed0=41_000 + offset
        )
        assert single.equals(batch.filter(pl.col("seed") == 41_000 + offset))
