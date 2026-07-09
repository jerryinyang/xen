"""Xen data-layer package.

Core, thesis-agnostic infrastructure for intraday-trading research: deterministic,
streaming-compatible chart-type generators and OHLC resampling built on a
1-minute time-bar base. These primitives are shared by every experiment and are
not specific to any single research thesis.

The ``xen.indicators`` subpackage holds optional, reusable indicator ports that
are not part of the core data layer.
"""

from __future__ import annotations

from xen.bar_aggregator import aggregate_ohlc, coverage_summary
from xen.heiken_ashi_generator import HeikenAshiGenerator, generate_heiken_ashi
from xen.linebreak_generator import LineBreakGenerator, generate_linebreak
from xen.renko_generator import RenkoGenerator, generate_renko
from xen.zigzag import generate_zigzag, wilder_atr

# Note: `xen.signals` is the validation/ingestion side of the cTrader strategy
# branch (design.md v2); it is imported directly where needed (e.g. VAL-002), not
# re-exported here, because Python does not generate strategy signals.

__all__ = [
    "aggregate_ohlc",
    "coverage_summary",
    "HeikenAshiGenerator",
    "generate_heiken_ashi",
    "LineBreakGenerator",
    "generate_linebreak",
    "RenkoGenerator",
    "generate_renko",
    "generate_zigzag",
    "wilder_atr",
]
