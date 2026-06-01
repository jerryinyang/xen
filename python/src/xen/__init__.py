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

__all__ = [
    "aggregate_ohlc",
    "coverage_summary",
    "HeikenAshiGenerator",
    "generate_heiken_ashi",
    "LineBreakGenerator",
    "generate_linebreak",
    "RenkoGenerator",
    "generate_renko",
]
