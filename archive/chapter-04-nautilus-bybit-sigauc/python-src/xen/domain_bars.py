"""Holdout-fenced domain-bar construction for CF-CAPGEO-001 (Phase 018).

Promoted **verbatim** from the VAL-005-validated path
(``python/experiments/VAL-005/code/run_experiment.py::build_domain_bars``,
operator decision 2026-06-21, VAL-005 G1 finding) so Phase-018 experiments share
one canonical construction. EXP-080 regression-checks this promotion against the
VAL-005 original on >=1 shared cell before any substrate read.

The rule: aggregate the analysis-slice 1-minute bars at the deployed coverage
(``min_coverage=0.90``), then apply the **analysis-boundary fence** — drop any
resample window whose right-labelled ``CloseTime`` exceeds the last available
source bar. Under the coverage-tolerant mode a trailing partial window is
retained with a nominal grid-boundary label that can sit up to one window past
the data, crossing into holdout-minute timestamps; the OHLC is fully causal
(analysis bars only) but the label is not fence-clean, so the canonical deployed
construction drops it.
"""

from __future__ import annotations

import polars as pl

from xen.bar_aggregator import aggregate_ohlc

# Deployed coverage for CF-CAPGEO-001 domain construction (VAL-005 MIN_COVERAGE).
MIN_COVERAGE: float = 0.90


def build_domain_bars(
    source: pl.DataFrame,
    period_minutes: int,
    min_coverage: float = MIN_COVERAGE,
) -> pl.DataFrame:
    """Holdout-fenced deployed domain construction for CF-CAPGEO-001.

    Aggregates the analysis-slice 1-minute bars at the deployed coverage, then
    applies the analysis-boundary fence: drop any resample window whose
    right-labelled ``CloseTime`` exceeds the last available source bar.

    Parameters
    ----------
    source : pl.DataFrame
        1-minute bars of one instrument's analysis slice, sorted by ``CloseTime``
        (non-decreasing). Must carry the ``aggregate_ohlc`` required columns.
    period_minutes : int
        Domain period in minutes (15, 60, or 240 for Phase 018).
    min_coverage : float, default ``MIN_COVERAGE`` (0.90)
        Coverage-tolerant window-retention fraction passed to ``aggregate_ohlc``.

    Returns
    -------
    pl.DataFrame
        Holdout-fenced domain bars (windows labelled past the source max dropped).
    """
    agg = aggregate_ohlc(source, period_minutes=period_minutes, min_coverage=min_coverage)
    source_max = source.select(pl.max("CloseTime")).item()
    return agg.filter(pl.col("CloseTime") <= source_max)
