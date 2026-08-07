"""SPDR-024 episode emission: the table the two blocked questions can be read from.

One row per arm per origin, carrying every column SPDR-021/022/023 could not supply:

* **E1** `regime_state` / `regime_episode_id` - the realised volatility regime, causal at `t-1`.
* **E2** `counterfactual_outcome_bps` - what a REJECTED origin would have returned under the
  fixed arm's own management. Rejected origins carried `0.0` before, which made every selection
  read void.
* **E3** `target_falsifiable_metric` - declared, and emitted as NOT_APPLICABLE while no TARGET
  arm exists in this run rather than silently dropped.
* **E4** `exit_reason` and `entry_ts` - populated, not null.
* **E5** `hold_bars_realised` plus the cap-bind flag.
* **E6** `capital_normalised_return_bps` - the PRIMARY estimand, which unlike per-notional bps
  is not blind to position size.

Nothing here adjudicates: every value is a measurement of what the engine did.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

from xen.adaptive_management.analysis import _attach_results
from xen.adaptive_management.contracts import SIGNAL_DOMAIN_HOURS

NS_PER_HOUR = 3_600_000_000_000

#: States in which an arm created a stop order for the origin. Order creation is NOT admission:
#: design section 2 OBJECT-IDENTITY binds admission to the stop-FILL state, because capital is
#: committed at the fill and every availability/selection measure must condition on the same
#: event the strategy trades on. A rule that changes how long a pending order lives (the
#: `PENDING_EXPIRY` arms) is invisible at order creation and fully visible at the fill.
ORDER_CREATED_STATES = frozenset({"ORDER_CREATED", "FILLED"})

EPISODE_COLUMNS = (
    "experiment_id",
    "universe",
    "signal_domain",
    "symbol",
    "entry_variant",
    "origin_id",
    "episode_id",
    "arm_id",
    "arm_class",
    "policy_id",
    "component",
    "device",
    "setting",
    "comparator_id",
    "state",
    "rejection_class",
    "decision_ts",
    "regime_state",
    "regime_episode_id",
    "order_created",
    "admitted",
    "risk_size",
    "hold_bars",
    "hold_cap_bars",
    "hold_cap_binds",
    "entry_ts",
    "exit_ts",
    "exit_reason",
    "censored",
    "hold_bars_realised",
    "outcome_bps",
    "capital_normalised_return_bps",
    "counterfactual_outcome_bps",
    "counterfactual_capital_normalised_bps",
    "counterfactual_source",
    "target_falsifiable_metric",
    "spread_cost_status",
    "cost_scope",
    "spread_rt_bps",
)


def build_episode_table(run_dir: Path) -> pl.DataFrame:
    """Build the SPDR-024 episode table for one completed TRAIN run."""
    run_dir = Path(run_dir)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    if config.get("band") != "TRAIN":
        raise ValueError("SPDR-024 emission accepts TRAIN runs only")
    if config.get("experiment_id") != "SPDR-024":
        raise ValueError(f"not an SPDR-024 run: {config.get('experiment_id')}")
    universe = str(config["universe"])
    domain = str(config.get("signal_domain", "H1"))
    domain_ns = SIGNAL_DOMAIN_HOURS[domain] * NS_PER_HOUR
    disclosure = config.get("spread_cost_disclosure", {})

    ledger = pl.read_parquet(
        run_dir / "episode_results.parquet",
        columns=["episode_id", "arm_id", "policy_id", "state", "ts_ns", "price", "exit_reason"],
    )
    frames = []
    for name in ("native_parameter_schedule", "policy_schedule"):
        schedule = pl.read_parquet(run_dir / f"{name}.parquet")
        if schedule.is_empty():
            continue
        frames.append(_enrich(schedule, ledger, universe, domain, domain_ns))
    if not frames:
        return pl.DataFrame(schema={name: pl.Utf8 for name in EPISODE_COLUMNS})
    episodes = pl.concat(frames, how="diagonal_relaxed")
    episodes = _attach_counterfactuals(episodes)
    return _finalise(episodes, domain, disclosure)


def _enrich(
    schedule: pl.DataFrame,
    ledger: pl.DataFrame,
    universe: str,
    domain: str,
    domain_ns: int,
) -> pl.DataFrame:
    """Attach engine outcomes and the E4/E5/E6 columns to one schedule table."""
    # _attach_results is the SPDR-021/022/023 arithmetic, reused verbatim so the per-notional
    # denominator and the outcome definition stay byte-identical across experiments.
    frame = _attach_results(schedule, ledger, universe)
    filled = pl.col("_entry_ns").is_not_null()
    closed = pl.col("_exit_ns").is_not_null()
    state = pl.col("state").cast(pl.Utf8)
    created = state.is_in(list(ORDER_CREATED_STATES))
    return frame.with_columns(
        pl.lit(domain).alias("signal_domain"),
        created.alias("order_created"),
        # ADMISSION IS THE FILL (design section 2). Banding on order creation makes every rule
        # that acts on the pending order's lifetime look inert: those arms create exactly the
        # comparator's order set and differ only in which of those orders survive to a fill.
        filled.alias("admitted"),
        # Not every non-admitted origin was REJECTED. Only an origin the rule evaluated and
        # declined answers "does the filter select better trades?"; an origin whose component
        # feature did not exist yet was never evaluated at all, and pooling the two would
        # measure warm-up as if it were selection.
        pl.when(filled)
        .then(pl.lit("ADMITTED"))
        # An order that was created and expired unfilled is an EVALUATED DECLINE at the fill
        # event: the arm committed to the origin, and its own expiry rule is what stopped the
        # commitment becoming capital. This is the population the PENDING_EXPIRY arms act on.
        .when(created)
        .then(pl.lit("EVALUATED_DECLINED_ORDER_EXPIRED"))
        .when(state == "NO_EVENT")
        .then(pl.lit("EVALUATED_DECLINED"))
        .when(state == "NO_FEATURE")
        .then(pl.lit("FEATURE_UNAVAILABLE"))
        .when(state == "BLOCKED_ACTIVE")
        .then(pl.lit("SLOT_OCCUPIED"))
        .otherwise(pl.lit("OTHER_NON_ADMITTED"))
        .alias("rejection_class"),
        # E4: both columns were null on 100% of prior analysis rows while the internals were
        # fully populated. They are the plumbing, not a new measurement.
        pl.when(filled)
        .then(pl.from_epoch(pl.col("_entry_ns"), time_unit="ns").dt.replace_time_zone("UTC"))
        .otherwise(None)
        .alias("entry_ts"),
        pl.when(closed)
        .then(pl.from_epoch(pl.col("_exit_ns"), time_unit="ns").dt.replace_time_zone("UTC"))
        .otherwise(None)
        .alias("exit_ts"),
        pl.col("_exit_reason").alias("exit_reason"),
        (filled & ~closed).alias("censored"),
        # E5: realised duration in signal-domain bars.
        pl.when(filled & closed)
        .then((pl.col("_exit_ns") - pl.col("_entry_ns")) / float(domain_ns))
        .otherwise(None)
        .alias("hold_bars_realised"),
        # E6: the PRIMARY estimand. Per-notional bps is invariant to position size by
        # construction; this is the same move measured against the committed capital base, so
        # halving the position halves the return it contributes.
        pl.when(closed)
        .then(pl.col("outcome_bps") * pl.col("risk_size").fill_null(1.0))
        .otherwise(None)
        .alias("capital_normalised_return_bps"),
        # E3: declared and visible. No TARGET arm exists in this run (OD-11/OD-15), so the
        # metric is emitted as inapplicable rather than omitted.
        pl.lit("NOT_APPLICABLE_NO_TARGET_ARM").alias("target_falsifiable_metric"),
    ).with_columns(
        pl.when(closed).then(pl.col("outcome_bps")).otherwise(None).alias("outcome_bps"),
    )


def _attach_counterfactuals(episodes: pl.DataFrame) -> pl.DataFrame:
    """E2: give every origin the arm did not fill the fixed arm's realised outcome on it.

    The fixed native comparator admits and manages the origin; its realised outcome is exactly
    "what the episode would have returned had the origin been admitted, on the fixed arm's own
    management". A rejected origin therefore carries a real number, never the `0.0` fill that
    made `sign_share_difference` the selected side's own win share minus zero.
    """
    fixed = (
        episodes.filter(pl.col("arm_id") == "FIXED_NATIVE_BREAKOUT")
        .select(
            "symbol",
            "origin_id",
            pl.col("outcome_bps").alias("_cf_outcome_bps"),
            pl.col("capital_normalised_return_bps").alias("_cf_capital_bps"),
            pl.col("admitted").alias("_cf_admitted"),
        )
        .unique(subset=["symbol", "origin_id"], keep="first")
    )
    joined = episodes.join(fixed, on=["symbol", "origin_id"], how="left")
    available = pl.col("_cf_admitted").fill_null(False) & pl.col("_cf_outcome_bps").is_not_null()
    return joined.with_columns(
        pl.when(pl.col("admitted"))
        .then(None)
        .when(available)
        .then(pl.col("_cf_outcome_bps"))
        .otherwise(None)
        .alias("counterfactual_outcome_bps"),
        pl.when(pl.col("admitted"))
        .then(None)
        .when(available)
        .then(pl.col("_cf_capital_bps"))
        .otherwise(None)
        .alias("counterfactual_capital_normalised_bps"),
        pl.when(pl.col("admitted"))
        .then(pl.lit("ADMITTED_NO_COUNTERFACTUAL_REQUIRED"))
        .when(available)
        .then(pl.lit("FIXED_ARM_REALISED_OUTCOME"))
        .otherwise(pl.lit("FIXED_ARM_ALSO_DECLINED"))
        .alias("counterfactual_source"),
    ).drop("_cf_outcome_bps", "_cf_capital_bps", "_cf_admitted")


def _finalise(
    episodes: pl.DataFrame,
    domain: str,
    disclosure: dict[str, Any],
) -> pl.DataFrame:
    """Carry the cost-scope block into the analysis artifact itself (F7) and fix the schema."""
    defaults: dict[str, Any] = {
        "component": None,
        "setting": None,
        "comparator_id": None,
        "hold_cap_bars": None,
        "hold_cap_binds": False,
        "regime_state": "UNKNOWN",
        "regime_episode_id": "UNASSIGNED",
        "arm_class": None,
        "entry_variant": None,
    }
    additions = [
        pl.lit(value).alias(name)
        for name, value in defaults.items()
        if name not in episodes.columns
    ]
    frame = episodes.with_columns(additions) if additions else episodes
    frame = frame.with_columns(
        pl.lit(domain).alias("signal_domain"),
        pl.lit(disclosure.get("spread_cost_status")).alias("spread_cost_status"),
        pl.lit(disclosure.get("cost_scope")).alias("cost_scope"),
        pl.lit(disclosure.get("spread_rt_bps"), dtype=pl.Float64).alias("spread_rt_bps"),
    )
    present = [name for name in EPISODE_COLUMNS if name in frame.columns]
    return frame.select(present).sort(["symbol", "arm_id", "decision_ts"])
