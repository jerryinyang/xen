"""SPDR-024 emission requirements E1-E6, the hold-cap rule and the report ladder.

Everything in this module is declared by `python/experiments/SPDR-024/design.md` and by the
binding operator register in `next-experiment-shape.md` section 0. Nothing here selects a value
from an outcome: the regime label comes from volatility at `<= t-1` (E1 / V-C RULES), the hold
cap comes from the arm-B duration distribution only (section 7 CAP-RULE), and the variance
treatments are frozen before results exist (D12).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from xen.adaptive_management.contracts import (
    HOLD_CAP_BIND_FRACTION,
    HOLD_CAP_GRID,
    SAFETY_CEILING_BARS,
    SAFETY_CEILING_FLAG_FRACTION,
    UNCAPPED_ARM_ID,
)

#: E1 regime label source. `level_now` is the volatility level state of the signal-domain bar,
#: already lagged to `t-1` by `features.build_feature_panel`.
#:
#: DISCLOSURE, because it affects one read: this is also the gate of the `LEVEL_NOW` arm. For
#: that arm alone, "stratify by regime" and "stratify by the arm's own gate" are the same cut,
#: so its regime-conditional read is definitionally aligned rather than independently
#: informative. Every other component is gated on a different quantity.
REGIME_COLUMN = "level_now"
REGIME_LABEL_SHARED_WITH_ARM = "ADP_LEVEL_NOW_SIZE_STATE_HALVE_HIGH"
#: V-C RULES: a regime episode shorter than this many domain bars merges into its predecessor.
MIN_REGIME_EPISODE_BARS = 4


# --------------------------------------------------------------------------- #
# E1 - realised regime label per origin and per episode
# --------------------------------------------------------------------------- #


def regime_panel(features: pl.DataFrame) -> pl.DataFrame:
    """Per symbol and signal-domain bar: the causal regime label and its episode id.

    An episode is one contiguous run of the regime state (V-C RULES). Runs shorter than
    `MIN_REGIME_EPISODE_BARS` merge into the preceding episode, which is applied mechanically
    here and never tuned after estimates exist.
    """
    if features.is_empty():
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "ts": pl.Datetime("ns", "UTC"),
                "regime_state": pl.Utf8,
                "regime_episode_id": pl.Utf8,
            }
        )
    frames: list[pl.DataFrame] = []
    for symbol, group in features.sort(["symbol", "ts"]).group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        states = group[REGIME_COLUMN].cast(pl.Utf8).fill_null("UNKNOWN").to_list()
        # Raw contiguous runs first, then the merge. Deciding at the transition would attach a
        # short run to the run that FOLLOWS it, where the rule says it joins the one before.
        runs: list[int] = []
        for position, state in enumerate(states):
            if position and state == states[position - 1]:
                runs[-1] += 1
            else:
                runs.append(1)
        episode_index: list[int] = []
        current = -1
        for length in runs:
            # A run below the declared minimum is not its own block; it merges into the
            # preceding episode. The first run has no predecessor, so it starts one.
            if length >= MIN_REGIME_EPISODE_BARS or current < 0:
                current += 1
            episode_index.extend([current] * length)
        frames.append(
            group.select(
                pl.col("symbol").cast(pl.Utf8),
                pl.col("ts").cast(pl.Datetime("ns", "UTC")),
                pl.col(REGIME_COLUMN).cast(pl.Utf8).fill_null("UNKNOWN").alias("regime_state"),
                pl.Series(
                    "regime_episode_id",
                    [f"{name}-R{index:06d}" for index in episode_index],
                    dtype=pl.Utf8,
                ),
            )
        )
    return pl.concat(frames)


def regime_episode_summary(panel: pl.DataFrame) -> pl.DataFrame:
    """Episode count, state and length distribution, as V-C requires to be reported."""
    if panel.is_empty():
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "regime_episode_id": pl.Utf8,
                "regime_state": pl.Utf8,
                "start_ts": pl.Datetime("ns", "UTC"),
                "end_ts": pl.Datetime("ns", "UTC"),
                "length_bars": pl.Int64,
            }
        )
    return (
        panel.group_by(["symbol", "regime_episode_id"])
        .agg(
            pl.col("regime_state").first(),
            pl.col("ts").min().alias("start_ts"),
            pl.col("ts").max().alias("end_ts"),
            pl.len().cast(pl.Int64).alias("length_bars"),
        )
        .sort(["symbol", "start_ts"])
    )


def attach_regime_labels(
    frame: pl.DataFrame,
    panel: pl.DataFrame,
    *,
    ts_column: str = "decision_ts",
) -> pl.DataFrame:
    """Attach the E1 regime label to any frame keyed by symbol and a domain-bar timestamp."""
    if frame.is_empty() or panel.is_empty() or ts_column not in frame.columns:
        return frame
    joined = frame.join(
        panel.rename({"ts": ts_column}),
        on=["symbol", ts_column],
        how="left",
    )
    return joined.with_columns(
        pl.col("regime_state").fill_null("UNKNOWN"),
        pl.col("regime_episode_id").fill_null("UNASSIGNED"),
    )


# --------------------------------------------------------------------------- #
# Hold horizon - design section 7 (H1/H2) and the section 7 safety ceiling
# --------------------------------------------------------------------------- #


def hold_duration_distribution(
    durations_bars: np.ndarray,
    *,
    ceiling_bars: int = SAFETY_CEILING_BARS,
) -> dict[str, Any]:
    """Describe arm B's realised closed-position durations, in signal-domain bars."""
    values = np.asarray(durations_bars, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "closed_positions": 0,
            "ceiling_bars": ceiling_bars,
            "ceiling_bind_rate": None,
            "percentiles": {},
        }
    return {
        "closed_positions": int(values.size),
        "ceiling_bars": ceiling_bars,
        "ceiling_bind_rate": float(np.mean(values >= ceiling_bars)),
        "percentiles": {
            str(q): float(np.percentile(values, q)) for q in (50, 75, 90, 95, 99, 100)
        },
        "mean_bars": float(values.mean()),
    }


def hold_cap_from_durations(
    durations_bars: np.ndarray,
    *,
    grid: tuple[int, ...] = HOLD_CAP_GRID,
    bind_fraction: float = HOLD_CAP_BIND_FRACTION,
    ceiling_bars: int = SAFETY_CEILING_BARS,
) -> dict[str, Any]:
    """Apply the design section 7 CAP-RULE mechanically to a duration distribution.

    The rule: the smallest grid value that binds at most `bind_fraction` of arm B's closed
    positions. Duration basis only - reading the cap off outcomes would be selection on the
    estimand. When no grid value satisfies the rule the result is NOT_APPLICABLE: the rule is
    reported as it fell out, never relaxed to produce a number.
    """
    values = np.asarray(durations_bars, dtype=float)
    values = values[np.isfinite(values)]
    bind_rates = {
        int(candidate): (float(np.mean(values > candidate)) if values.size else None)
        for candidate in grid
    }
    chosen: int | None = None
    if values.size:
        for candidate in sorted(grid):
            if bind_rates[int(candidate)] <= bind_fraction:
                chosen = int(candidate)
                break
    distribution = hold_duration_distribution(values, ceiling_bars=ceiling_bars)
    ceiling_rate = distribution["ceiling_bind_rate"]
    return {
        "rule": (
            "smallest declared grid value binding <= "
            f"{bind_fraction:.0%} of arm B closed positions; duration basis only"
        ),
        "grid": list(grid),
        "bind_rate_by_candidate": bind_rates,
        "hold_cap_bars": chosen,
        "status": "SELECTED" if chosen is not None else "NOT_APPLICABLE",
        "realised_bind_rate": bind_rates.get(chosen) if chosen is not None else None,
        "duration_distribution": distribution,
        "safety_ceiling_bars": ceiling_bars,
        "safety_ceiling_bind_rate": ceiling_rate,
        "safety_ceiling_flagged": (
            bool(ceiling_rate is not None and ceiling_rate > SAFETY_CEILING_FLAG_FRACTION)
        ),
        "uncapped_arm_id": UNCAPPED_ARM_ID,
    }
