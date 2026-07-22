"""Xen data-layer package.

Core, thesis-agnostic infrastructure retained for the active research chapter.
"""

from __future__ import annotations

from xen.bar_aggregator import aggregate_ohlc, coverage_summary

__all__ = [
    "aggregate_ohlc",
    "coverage_summary",
]
