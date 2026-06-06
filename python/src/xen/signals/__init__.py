"""Ingestion/validation side of the INFR-001 cTrader strategy branch (design.md v2).

The cTrader cAlgo is the sole signal generator. Python does **not** generate or
re-implement strategy signals; it ingests the emitted strategy-host run and routes
positions (on emitted real-price returns) through the frozen referee suite.
"""

from __future__ import annotations

from xen.signals.ingestion import (
    POSITION_COLUMNS,
    EmittedRun,
    assert_before_analysis_end,
    assert_run_within_holdout,
    load_emitted_run,
    returns_and_positions,
    screen_emitted_positions,
    screen_emitted_run,
)

__all__ = [
    "POSITION_COLUMNS",
    "EmittedRun",
    "assert_before_analysis_end",
    "assert_run_within_holdout",
    "load_emitted_run",
    "returns_and_positions",
    "screen_emitted_positions",
    "screen_emitted_run",
]
