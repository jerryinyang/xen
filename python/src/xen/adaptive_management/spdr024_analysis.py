"""SPDR-024 estimates: the scale channel, the selection channel and the report ladder.

Three things make this different from the SPDR-021/022/023 analyser, and each is forced by the
binding specification rather than imported from it:

* the PRIMARY estimand is the capital-normalised episode return (E6). Per-notional bps is
  retained as a diagnostic and is **barred from every sizing claim, in either direction**;
* uncertainty is computed three ways and all three are always reported (D12). The most
  conservative governs every band label; no treatment may be picked after seeing the estimates;
* the selection channel is read against the rejected origins' emitted counterfactuals (E2),
  never on the trade lens, where an admission rule's paired delta is zero by identity (F2).

Aggregation is the standing ordering: un-nest -> sigma-hat-normalise -> pool, with a
symbol-clustered interval (M1). Per-symbol reads are a diagnostic, never the estimand.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import numpy as np
import polars as pl

#: D12 variance treatments. Frozen here, before any estimate exists.
TREATMENTS = ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")
#: V-B block width in signal-domain bars, carried from the Step-3 form for comparability.
TIME_BLOCK_BARS = 24
#: Design section 10: MDE_sigma = 2.8 / sqrt(n).
MDE_Z = 2.8
#: The RANGE of sizing effects Step-3 observed, in sigma-hat units. Reported in
#: `analysis_summary.json` as the reference a reader compares each cell's MDE against. It is
#: reference context only: nothing in this module compares an MDE with it, because that
#: comparison produced the power labels the contract forbids.
STEP3_OBSERVED_EFFECT_SIGMA_MAX = 0.150
STEP3_OBSERVED_EFFECT_SIGMA_MIN = 0.022
BOOTSTRAP_DRAWS = 2_000
BOOTSTRAP_SEED = 20260806
#: Rejection classes whose origins carry a real E2 counterfactual. Both are genuine declines at
#: the fill event: the rule either never created the order, or created one its own expiry rule
#: killed before it filled.
DECLINED_CLASSES = ("EVALUATED_DECLINED", "EVALUATED_DECLINED_ORDER_EXPIRED")


#: Gate-permutation control draws. The control answers the only question the raw paired
#: difference cannot: is the gate applied to WORSE trades, or merely applied?
GATE_PERMUTATION_DRAWS = 2_000
#: Regime strata the scale channel is reported on (E1 / OD-18).
REGIME_STRATA = ("ALL", "HIGH", "LOW")


@dataclass(frozen=True)
class SymbolSeries:
    """One symbol's paired difference series with its three block partitions.

    `weights` and `baseline` carry the two factors the difference is built from, because the
    paired difference for a SIZE arm is exactly `(risk_size - 1) x baseline_outcome`. Keeping
    them lets the estimator separate the part that is arithmetic from the part that is a
    measurement (see `decompose`).
    """

    symbol: str
    values: np.ndarray
    blocks: dict[str, np.ndarray]
    weights: np.ndarray | None = None
    baseline: np.ndarray | None = None

    @property
    def n(self) -> int:
        return int(self.values.size)

    @property
    def sigma(self) -> float:
        return float(np.std(self.values, ddof=1)) if self.values.size > 1 else float("nan")


# --------------------------------------------------------------------------- #
# Series construction
# --------------------------------------------------------------------------- #


def _block_ids(frame: pl.DataFrame, domain_hours: int) -> dict[str, np.ndarray]:
    """The three declared block partitions for one symbol's paired series."""
    n = frame.height
    entry_ns = frame["entry_ts"].cast(pl.Datetime("ns", "UTC")).dt.epoch("ns").to_numpy()
    block_ns = TIME_BLOCK_BARS * domain_hours * 3_600_000_000_000
    return {
        # V-A: the trade count is the sample size; every trade is its own block.
        "V_A_UNCHUNKED": np.arange(n, dtype=np.int64),
        # V-B: fixed-length clock blocks, the Step-3 form.
        "V_B_TIME_BLOCK": (entry_ns // block_ns).astype(np.int64),
        # V-C: one contiguous regime episode per block (E1); merged short episodes already
        # carry their predecessor's id, so contiguity holds by construction.
        "V_C_REGIME_EPISODE": pl.Series(frame["regime_episode_id"]).cast(pl.Categorical)
        .to_physical()
        .to_numpy()
        .astype(np.int64),
    }


def paired_series(
    episodes: pl.DataFrame,
    arm_id: str,
    comparator_id: str,
    value_column: str,
    *,
    domain_hours: int,
    regime: str = "ALL",
) -> list[SymbolSeries]:
    """Common-closed paired differences for one arm, one per symbol.

    An episode enters only when BOTH sides closed inside the fence: a censored position is
    never silently closed and never enters a paired read. `regime` restricts the pairs to one
    realised volatility state (E1), which is what makes the regime question answerable.
    """
    arm = episodes.filter(pl.col("arm_id") == arm_id).select(
        "symbol",
        "origin_id",
        "entry_ts",
        "regime_episode_id",
        "regime_state",
        "risk_size",
        pl.col(value_column).alias("_arm_value"),
    )
    comparator = episodes.filter(pl.col("arm_id") == comparator_id).select(
        "symbol",
        "origin_id",
        pl.col(value_column).alias("_comparator_value"),
        pl.col("outcome_bps").alias("_baseline_outcome_bps"),
    )
    paired = (
        arm.join(comparator, on=["symbol", "origin_id"], how="inner")
        .filter(pl.col("_arm_value").is_not_null() & pl.col("_comparator_value").is_not_null())
        .with_columns((pl.col("_arm_value") - pl.col("_comparator_value")).alias("_delta"))
        .sort(["symbol", "entry_ts"])
    )
    if regime != "ALL":
        paired = paired.filter(pl.col("regime_state") == regime)
    series: list[SymbolSeries] = []
    for symbol, group in paired.group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        series.append(
            SymbolSeries(
                symbol=str(name),
                values=group["_delta"].to_numpy().astype(float),
                blocks=_block_ids(group, domain_hours),
                weights=group["risk_size"].fill_null(1.0).to_numpy().astype(float),
                baseline=group["_baseline_outcome_bps"].to_numpy().astype(float),
            )
        )
    return series


# --------------------------------------------------------------------------- #
# Separating the arithmetic from the measurement
# --------------------------------------------------------------------------- #


def decompose(series: list[SymbolSeries]) -> dict[str, Any]:
    """Split a SIZE arm's paired difference into its exposure and selectivity parts.

    For a SIZE arm the paired difference is exactly `(s - 1) * r`, where `s` is the arm's own
    risk size and `r` the baseline episode's return. Its mean therefore decomposes as

        E[(s-1)r] = (E[s] - 1) * E[r]        <- EXPOSURE: pure arithmetic. Reducing exposure on
                                                a population with a positive mean must lower the
                                                total, and on a negative-mean population must
                                                raise it. It carries no information about the
                                                component.
                  + Cov(s, r)                <- SELECTIVITY: the only part that can answer
                                                "does this component cut the WORSE trades?"

    Reporting the undecomposed difference makes the same component look helpful wherever the
    baseline loses money and harmful wherever it earns - which is a statement about the
    baseline, not about volatility.
    """
    weights = np.concatenate([s.weights for s in series if s.weights is not None])
    baseline = np.concatenate([s.baseline for s in series if s.baseline is not None])
    values = np.concatenate([s.values for s in series]) if series else np.array([])
    if weights.size == 0 or baseline.size == 0 or values.size == 0:
        return {
            "gate_rate": float("nan"),
            "mean_risk_size": float("nan"),
            "baseline_mean_bps": float("nan"),
            "exposure_term_bps": float("nan"),
            "selectivity_term_bps": float("nan"),
            "exposure_share_of_effect": float("nan"),
        }
    total = float(np.mean(values))
    exposure = float((np.mean(weights) - 1.0) * np.mean(baseline))
    selectivity = total - exposure
    magnitude = abs(exposure) + abs(selectivity)
    return {
        "gate_rate": float(np.mean(weights != 1.0)),
        "mean_risk_size": float(np.mean(weights)),
        "baseline_mean_bps": float(np.mean(baseline)),
        "net_effect_bps": total,
        "exposure_term_bps": exposure,
        "selectivity_term_bps": selectivity,
        # ABSOLUTE-magnitude share: |exposure| / (|exposure| + |selectivity|). It answers "how
        # much of the movement is arithmetic", and it is NOT a share of the net effect - the
        # two terms can oppose, so exposure alone can exceed the net. The signed ratio below
        # says which case a row is in.
        "exposure_share_of_movement": (
            float(abs(exposure) / magnitude) if magnitude > 0 else float("nan")
        ),
        "exposure_over_net_effect": (
            float(exposure / total) if total != 0 and np.isfinite(total) else float("nan")
        ),
        "terms_oppose": bool(
            np.isfinite(exposure) and np.isfinite(selectivity) and exposure * selectivity < 0
        ),
    }


def gate_permutation_control(
    series: list[SymbolSeries],
    treatment: str,
    *,
    n_draws: int = GATE_PERMUTATION_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Is the gate applied to WORSE trades, or merely applied? (design section 8 non-vacuity)

    The control permutes each symbol's `risk_size` vector against its own outcomes. That keeps
    the gate rate and the exact multiplier distribution - so the EXPOSURE term is preserved
    identically - while destroying any association between the gate and the outcome, which is
    the SELECTIVITY term. It can move the statistic (it is not mean-preserving on the paired
    difference), and it can come out either way: a component that gates the worse trades lands
    in the tail, one that gates arbitrarily lands mid-distribution.
    """
    usable = [s for s in series if s.weights is not None and s.baseline is not None and s.n > 1]
    # A permutation can only destroy an association that exists to be destroyed. Where the gate
    # takes one value on every row of a stratum there is nothing to permute, so the control is
    # structurally vacuous and must say so rather than return p = 1.0 as though it had run.
    varying = [item for item in usable if np.unique(item.weights).size > 1]
    if usable and not varying:
        return {
            "control": "GATE_PERMUTATION",
            "applicable": False,
            "not_applicable_reason": (
                "the gate is constant on every row of this stratum, so permuting it changes "
                "nothing; the control cannot move the statistic it exists to destroy"
            ),
            "observed_sigma": float("nan"),
            "null_mean_sigma": float("nan"),
            "component_specific_sigma": float("nan"),
            "percentile_in_null": float("nan"),
            "two_sided_p": float("nan"),
            "draws": 0,
        }
    if not usable:
        return {
            "control": "GATE_PERMUTATION",
            "applicable": False,
            "not_applicable_reason": "no usable paired series in this stratum",
            "observed_sigma": float("nan"),
            "null_mean_sigma": float("nan"),
            "component_specific_sigma": float("nan"),
            "percentile_in_null": float("nan"),
            "two_sided_p": float("nan"),
            "draws": 0,
        }

    def _pooled(deltas: list[np.ndarray]) -> float:
        parts = []
        for delta in deltas:
            sigma = float(np.std(delta, ddof=1)) if delta.size > 1 else float("nan")
            if np.isfinite(sigma) and sigma > 0:
                parts.append(delta / sigma)
        return float(np.mean(np.concatenate(parts))) if parts else float("nan")

    observed = _pooled([s.values for s in usable])
    rng = np.random.default_rng(seed)
    draws = np.full(n_draws, np.nan)
    for index in range(n_draws):
        permuted = []
        for item in usable:
            shuffled = rng.permutation(item.weights)
            permuted.append((shuffled - 1.0) * item.baseline)
        draws[index] = _pooled(permuted)
    finite = draws[np.isfinite(draws)]
    if not finite.size or not np.isfinite(observed):
        percentile = two_sided = float("nan")
        null_mean = float("nan")
    else:
        null_mean = float(np.mean(finite))
        percentile = float(np.mean(finite <= observed))
        two_sided = float(
            2.0 * min(np.mean(finite <= observed), np.mean(finite >= observed))
        )
    if finite.size:
        null_low, null_high = (
            float(np.percentile(finite, 2.5)),
            float(np.percentile(finite, 97.5)),
        )
    else:
        null_low = null_high = float("nan")
    return {
        "control": "GATE_PERMUTATION",
        "applicable": True,
        "observed_sigma": observed,
        "null_mean_sigma": null_mean,
        "component_specific_sigma": (
            observed - null_mean if np.isfinite(observed) and np.isfinite(null_mean)
            else float("nan")
        ),
        # The null's own 95% envelope. Carrying it turns the component-specific part into an
        # effect WITH an interval, which is what the section 11 band rule takes - instead of a
        # p-value compared against a fixed cut, the class of value gate this programme retired.
        "null_q2_5_sigma": null_low,
        "null_q97_5_sigma": null_high,
        "component_specific_ci_low_sigma": (
            observed - null_high if np.isfinite(observed) and np.isfinite(null_high)
            else float("nan")
        ),
        "component_specific_ci_high_sigma": (
            observed - null_low if np.isfinite(observed) and np.isfinite(null_low)
            else float("nan")
        ),
        "percentile_in_null": percentile,
        "two_sided_p": min(two_sided, 1.0) if np.isfinite(two_sided) else float("nan"),
        "draws": int(finite.size),
        "treatment_of_reference": treatment,
        "preserves": "gate rate and multiplier distribution (exposure term identical)",
        "destroys": "gate-to-outcome association (the selectivity term)",
    }


# --------------------------------------------------------------------------- #
# Uncertainty
# --------------------------------------------------------------------------- #


def _block_index(blocks: np.ndarray) -> list[np.ndarray]:
    order = np.argsort(blocks, kind="stable")
    sorted_blocks = blocks[order]
    boundaries = np.flatnonzero(np.diff(sorted_blocks)) + 1
    return np.split(order, boundaries) if order.size else []


def clustered_interval(
    series: list[SymbolSeries],
    treatment: str,
    *,
    n_boot: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Pooled sigma-hat-normalised effect with a symbol-clustered block-bootstrap interval.

    Symbols are the cluster unit because cross-symbol contemporaneous correlation is not a
    time-series dependence and is never addressed by any time-blocking treatment (design
    section 10). Blocks inside a drawn symbol follow the treatment.
    """
    usable = [item for item in series if item.n > 1 and np.isfinite(item.sigma) and item.sigma > 0]
    if not usable:
        return _empty_interval(treatment, series)
    normalised = {item.symbol: item.values / item.sigma for item in usable}
    partitions = {item.symbol: _block_index(item.blocks[treatment]) for item in usable}
    pooled = np.concatenate([normalised[item.symbol] for item in usable])
    estimate = float(np.mean(pooled))
    effective_blocks = int(sum(len(partitions[item.symbol]) for item in usable))

    rng = np.random.default_rng(seed)
    symbols = [item.symbol for item in usable]
    draws = np.empty(n_boot, dtype=float)
    # One draw plan per replicate is reused across every symbol's identical arithmetic; the
    # populations differ by symbol, so nothing is shared across genuinely different samples.
    for index in range(n_boot):
        chosen = rng.integers(0, len(symbols), size=len(symbols))
        parts: list[np.ndarray] = []
        for position in chosen:
            symbol = symbols[position]
            blocks = partitions[symbol]
            picks = rng.integers(0, len(blocks), size=len(blocks))
            parts.append(np.concatenate([normalised[symbol][blocks[pick]] for pick in picks]))
        sample = np.concatenate(parts)
        draws[index] = float(np.mean(sample)) if sample.size else np.nan
    finite = draws[np.isfinite(draws)]
    ci_low, ci_high = (
        (float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5)))
        if finite.size
        else (float("nan"), float("nan"))
    )
    return {
        "treatment": treatment,
        "estimate_sigma": estimate,
        "ci_low_sigma": ci_low,
        "ci_high_sigma": ci_high,
        "effective_blocks": effective_blocks,
        "mde_sigma": MDE_Z / np.sqrt(effective_blocks) if effective_blocks else float("nan"),
        "n_trades": int(sum(item.n for item in usable)),
        "n_symbols": len(usable),
    }


def _empty_interval(treatment: str, series: list[SymbolSeries]) -> dict[str, Any]:
    return {
        "treatment": treatment,
        "estimate_sigma": float("nan"),
        "ci_low_sigma": float("nan"),
        "ci_high_sigma": float("nan"),
        "effective_blocks": 0,
        "mde_sigma": float("nan"),
        "n_trades": int(sum(item.n for item in series)),
        "n_symbols": len(series),
    }


# --------------------------------------------------------------------------- #
# NO RESULT LABELS ANYWHERE IN THIS MODULE.
#
# The binding contract (`adaptive-management-design.md` section 1 and section 9) requires every
# row to be described by ESTIMATE, UNCERTAINTY, POPULATION COUNT, EFFECTIVE COUNT and MDE, and
# nothing else: "Emit event count, effective count, CI and MDE for every row. These are
# informative diagnostics, not verdict labels or pruning rules", and "power labels do not decide
# which rows are shown or how they are described."
#
# An earlier build of this module emitted `band` / `governing_band` / `component_specific_band`,
# and a later correction added `resolution_class` on top. Both are withdrawn. A band computed
# from the floor decides how a row is described BY ITS POWER, which is the one thing the
# contract forbids; refining the taxonomy made the violation more systematic, not less. The
# reader compares the estimate with its own MDE and its own interval, which are all present on
# every row.
# --------------------------------------------------------------------------- #


def governing_treatment(intervals: list[dict[str, Any]]) -> dict[str, Any]:
    """The most conservative of the three governs every band label (D12).

    Conservative means the highest detection floor: the treatment that credits the sample with
    the fewest independent blocks and therefore demands the largest effect. Selecting on
    interval width alone can import the SMALLEST floor with the widest interval, which is not
    the conservative choice the directive asks for; width breaks a tie.
    """
    scored = [item for item in intervals if np.isfinite(item["mde_sigma"])]
    if not scored:
        return intervals[0]
    return max(
        scored,
        key=lambda item: (
            item["mde_sigma"],
            (item["ci_high_sigma"] - item["ci_low_sigma"])
            if np.isfinite(item["ci_high_sigma"] - item["ci_low_sigma"])
            else -np.inf,
        ),
    )


# --------------------------------------------------------------------------- #
# The two channels
# --------------------------------------------------------------------------- #


def _arm_populations(
    episodes: pl.DataFrame,
    arm_id: str,
    comparator_id: str,
) -> dict[str, Any]:
    """The separately-named populations behind one arm's paired comparison.

    Each is counted from the ledger it actually describes. `common_fill_n` is the origins filled
    on BOTH sides; `common_close_n` is per-stratum and comes from the paired series itself, so it
    is not computed here.
    """
    arm = episodes.filter(pl.col("arm_id") == arm_id)
    comparator = episodes.filter(pl.col("arm_id") == comparator_id)
    arm_filled = set(arm.filter(pl.col("admitted")).select("symbol", "origin_id").rows())
    comparator_filled = set(
        comparator.filter(pl.col("admitted")).select("symbol", "origin_id").rows()
    )

    def _for(frame: pl.DataFrame, filled: set) -> dict[str, Any]:
        return {
            "eligible_origin_n": frame.height,
            "entry_fill_n": int(frame["admitted"].sum()),
            "close_n": int(frame["exit_ts"].is_not_null().sum()),
            "common_fill_n": len(filled & comparator_filled),
        }

    per_symbol: dict[str, Any] = {}
    for symbol, group in arm.group_by("symbol", maintain_order=True):
        name = str(symbol[0] if isinstance(symbol, tuple) else symbol)
        per_symbol[name] = _for(
            group, {row for row in arm_filled if row[0] == name}
        )
    return {**_for(arm, arm_filled), "per_symbol": per_symbol}


def scale_channel_estimates(
    episodes: pl.DataFrame,
    *,
    domain_hours: int,
    n_boot: int = BOOTSTRAP_DRAWS,
) -> pl.DataFrame:
    """Every SIZE arm against FIXED_SIZE_UNIT, on the PRIMARY estimand and its diagnostic."""
    arms = (
        episodes.filter(
            (pl.col("device") == "SIZE") & (pl.col("arm_id") != "FIXED_SIZE_UNIT")
        )
        .select("arm_id", "component", "setting")
        .unique()
        .sort("arm_id")
    )
    rows: list[dict[str, Any]] = []
    for arm in arms.iter_rows(named=True):
        populations = _arm_populations(episodes, arm["arm_id"], "FIXED_SIZE_UNIT")
        for lens, column in (
            ("PRIMARY_capital_normalised", "capital_normalised_return_bps"),
            ("DIAGNOSTIC_per_notional_bps", "outcome_bps"),
        ):
            for regime in REGIME_STRATA:
                series = paired_series(
                    episodes,
                    arm["arm_id"],
                    "FIXED_SIZE_UNIT",
                    column,
                    domain_hours=domain_hours,
                    regime=regime,
                )
                rows.extend(
                    _estimate_rows(
                        series,
                        populations=populations,
                        identity={
                            "channel": "SCALE",
                            "arm_id": arm["arm_id"],
                            "component": arm["component"],
                            "setting": arm["setting"],
                            "comparator_id": "FIXED_SIZE_UNIT",
                            "lens": lens,
                            "estimand": column,
                            "regime": regime,
                        },
                        n_boot=n_boot,
                        # The decomposition and its control are properties of the SIZE
                        # mechanism, so they are computed on the PRIMARY lens only; on the
                        # per-notional lens the difference is identically zero.
                        with_control=(lens == "PRIMARY_capital_normalised"),
                    )
                )
    # infer_schema_length=None scans every row before choosing dtypes. Several columns are
    # legitimately null on a long run of leading rows - a suppressed collapse fraction, a
    # control that did not apply - and the default 100-row window then types the column Null
    # and fails on the first float. Cell size decides whether that happens, so the default
    # makes the analyser succeed or fail depending on how many symbols a universe has.
    return pl.from_dicts(rows, infer_schema_length=None) if rows else pl.DataFrame()


def _estimate_rows(
    series: list[SymbolSeries],
    identity: dict[str, Any],
    *,
    populations: dict[str, Any],
    n_boot: int,
    with_control: bool = False,
) -> list[dict[str, Any]]:
    """One row per variance treatment, then the per-symbol ladder. No row carries a label.

    Every row is described by estimate, uncertainty, population count, effective count and MDE,
    which is the whole of what the contract permits. `governs` marks which of the three declared
    variance treatments credits the fewest independent blocks (D12); it describes a treatment,
    not a result.
    """
    intervals = [
        clustered_interval(series, treatment, n_boot=n_boot) for treatment in TREATMENTS
    ]
    governing = governing_treatment(intervals)
    parts = decompose(series) if with_control else {}
    control = (
        gate_permutation_control(series, governing["treatment"])
        if with_control
        else {}
    )
    rows: list[dict[str, Any]] = []
    for interval in intervals:
        rows.append(
            {
                **identity,
                "scope": "POOLED",
                "symbol": None,
                **interval,
                **_scale_populations(populations, interval),
                **parts,
                **{f"control_{key}": value for key, value in control.items()},
                "governs": interval["treatment"] == governing["treatment"],
                "mean_delta_raw": _pooled_raw_mean(series),
                **_breakeven_from_series(series),
                # Share of paired rows whose difference is exactly zero. On the per-notional
                # lens of a SIZE arm this is 1.0 because basis points cannot register a size
                # change; on the primary lens a 1.0 means the arm never gated in this stratum.
                # Emitted as the measured share so the reader distinguishes the two, rather
                # than as a label asserting which one it is.
                "exact_zero_delta_share": _zero_delta_share(series),
            }
        )
    for item in series:
        raw = float(np.mean(item.values)) if item.n else float("nan")
        rows.append(
            {
                **identity,
                **({} if not with_control else decompose([item])),
                "scope": "PER_SYMBOL",
                "symbol": item.symbol,
                "treatment": "V_A_UNCHUNKED",
                "estimate_sigma": raw / item.sigma if item.sigma else float("nan"),
                "ci_low_sigma": None,
                "ci_high_sigma": None,
                "effective_blocks": item.n,
                "mde_sigma": MDE_Z / np.sqrt(item.n) if item.n else float("nan"),
                "n_trades": item.n,
                "n_symbols": 1,
                **_scale_populations(
                    populations.get("per_symbol", {}).get(item.symbol, {}),
                    {"effective_blocks": item.n, "n_trades": item.n},
                ),
                "governs": False,
                "mean_delta_raw": raw,
                **breakeven_spread(raw * item.n, item.n),
                "exact_zero_delta_share": _zero_delta_share([item]),
            }
        )
    return rows


def _scale_populations(
    populations: dict[str, Any],
    interval: dict[str, Any],
) -> dict[str, Any]:
    """The separately-named populations the contract requires on every row.

    A count may never be filled in from a different population: where one does not apply to this
    channel it is null. The scale channel is a paired trade-lens read, so its origin-block count
    is null and its trade-block count carries the resampled blocks.
    """
    return {
        "eligible_origin_n": populations.get("eligible_origin_n"),
        "entry_fill_n": populations.get("entry_fill_n"),
        "close_n": populations.get("close_n"),
        "common_fill_n": populations.get("common_fill_n"),
        "common_close_n": interval.get("n_trades"),
        "effective_origin_blocks": None,
        "effective_trade_blocks": interval.get("effective_blocks"),
    }


def _zero_delta_share(series: list[SymbolSeries]) -> float:
    values = np.concatenate([item.values for item in series]) if series else np.array([])
    return float(np.mean(values == 0.0)) if values.size else float("nan")


def _pooled_raw_mean(series: list[SymbolSeries]) -> float:
    values = np.concatenate([item.values for item in series]) if series else np.array([])
    return float(np.mean(values)) if values.size else float("nan")


def breakeven_spread(total_effect_bps: float, round_trips: int) -> dict[str, Any]:
    """M7: |effect| / round-trips, at THAT arm's own turnover. Cost is never charged.

    Cost does not cancel in a paired difference when the two arms differ in trade count, so the
    divisor is this arm's own round-trip count rather than a shared one. Each closed episode is
    one round trip (entry fill + exit fill).
    """
    if not np.isfinite(total_effect_bps) or round_trips <= 0:
        return {
            "breakeven_spread_rt_bps": float("nan"),
            "round_trips": int(max(round_trips, 0)),
            "breakeven_spread_class": "NON_EMITTED_SCENARIO",
            "breakeven_spread_basis": "|total effect| / this arm's own round trips",
        }
    return {
        "breakeven_spread_rt_bps": abs(total_effect_bps) / round_trips,
        "round_trips": int(round_trips),
        "breakeven_spread_class": "NON_EMITTED_SCENARIO",
        "breakeven_spread_basis": "|total effect| / this arm's own round trips",
    }


def _breakeven_from_series(series: list[SymbolSeries]) -> dict[str, Any]:
    mean = _pooled_raw_mean(series)
    round_trips = int(sum(item.n for item in series))
    return breakeven_spread(mean * round_trips, round_trips)


def _origin_blocks(frame: pl.DataFrame, treatment: str, domain_hours: int) -> np.ndarray:
    """Block ids for an origin-level population, on the same three declared partitions."""
    if treatment == "V_A_UNCHUNKED":
        return np.arange(frame.height, dtype=np.int64)
    if treatment == "V_C_REGIME_EPISODE":
        return (
            pl.Series(frame["regime_episode_id"]).cast(pl.Categorical).to_physical().to_numpy()
            .astype(np.int64)
        )
    block_ns = TIME_BLOCK_BARS * domain_hours * 3_600_000_000_000
    epochs = frame["decision_ts"].cast(pl.Datetime("ns", "UTC")).dt.epoch("ns").to_numpy()
    return (epochs // block_ns).astype(np.int64)


def _contrast_interval(
    admitted: pl.DataFrame,
    rejected: pl.DataFrame,
    treatment: str,
    *,
    domain_hours: int,
    n_boot: int,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Symbol-clustered block bootstrap of admitted-minus-rejected, in bps.

    The two populations are disjoint by construction (no origin is in both), so each side is
    resampled on its own blocks inside the drawn symbol.
    """
    left = admitted["outcome_bps"].to_numpy().astype(float)
    right = rejected["counterfactual_outcome_bps"].to_numpy().astype(float)
    if left.size < 2 or right.size < 2:
        return {
            "treatment": treatment,
            "ci_low_bps": float("nan"),
            "ci_high_bps": float("nan"),
            "effective_blocks_admitted": 0,
            "effective_blocks_rejected": 0,
        }
    symbols = sorted(
        set(admitted["symbol"].to_list()) & set(rejected["symbol"].to_list())
    )
    if not symbols:
        return {
            "treatment": treatment,
            "ci_low_bps": float("nan"),
            "ci_high_bps": float("nan"),
            "effective_blocks_admitted": 0,
            "effective_blocks_rejected": 0,
        }
    packs: dict[str, tuple] = {}
    for symbol in symbols:
        side_a = admitted.filter(pl.col("symbol") == symbol)
        side_b = rejected.filter(pl.col("symbol") == symbol)
        if side_a.height < 1 or side_b.height < 1:
            continue
        packs[symbol] = (
            side_a["outcome_bps"].to_numpy().astype(float),
            _block_index(_origin_blocks(side_a, treatment, domain_hours)),
            side_b["counterfactual_outcome_bps"].to_numpy().astype(float),
            _block_index(_origin_blocks(side_b, treatment, domain_hours)),
        )
    if not packs:
        return {
            "treatment": treatment,
            "ci_low_bps": float("nan"),
            "ci_high_bps": float("nan"),
            "effective_blocks_admitted": 0,
            "effective_blocks_rejected": 0,
        }
    names = list(packs)
    rng = np.random.default_rng(seed)
    draws = np.full(n_boot, np.nan)
    for index in range(n_boot):
        chosen = rng.integers(0, len(names), size=len(names))
        left_parts: list[np.ndarray] = []
        right_parts: list[np.ndarray] = []
        for position in chosen:
            values_a, blocks_a, values_b, blocks_b = packs[names[position]]
            picks_a = rng.integers(0, len(blocks_a), size=len(blocks_a))
            picks_b = rng.integers(0, len(blocks_b), size=len(blocks_b))
            left_parts.append(np.concatenate([values_a[blocks_a[p]] for p in picks_a]))
            right_parts.append(np.concatenate([values_b[blocks_b[p]] for p in picks_b]))
        sample_a = np.concatenate(left_parts)
        sample_b = np.concatenate(right_parts)
        if sample_a.size and sample_b.size:
            draws[index] = float(np.mean(sample_a) - np.mean(sample_b))
    finite = draws[np.isfinite(draws)]
    return {
        "treatment": treatment,
        "ci_low_bps": float(np.percentile(finite, 2.5)) if finite.size else float("nan"),
        "ci_high_bps": float(np.percentile(finite, 97.5)) if finite.size else float("nan"),
        "effective_blocks_admitted": int(
            sum(len(packs[name][1]) for name in names)
        ),
        "effective_blocks_rejected": int(sum(len(packs[name][3]) for name in names)),
    }


def selection_channel_estimates(
    episodes: pl.DataFrame,
    *,
    fixed_arm_id: str = "FIXED_NATIVE_BREAKOUT",
    domain_hours: int = 1,
    n_boot: int = 1_000,
) -> pl.DataFrame:
    """Admitted-minus-rejected on the origin lens, against the E2 counterfactuals.

    The rejected set is DISJOINT from the admitted set by construction, and it can show the
    higher mean - which is exactly the outcome that would refute the filter (control
    COUNTERFACTUAL-REJECT, B-1).
    """
    arms = (
        episodes.filter(
            (pl.col("arm_class").is_in(["NATIVE", "NATIVE_COMBINATION"]))
            & (pl.col("arm_id") != fixed_arm_id)
        )
        .select("arm_id", "component")
        .unique()
        .sort("arm_id")
    )
    rows: list[dict[str, Any]] = []
    for arm in arms.iter_rows(named=True):
        frame = episodes.filter(pl.col("arm_id") == arm["arm_id"])
        for scope, group in _by_symbol_and_pooled(frame):
            admitted_frame = group.filter(
                pl.col("admitted") & pl.col("outcome_bps").is_not_null()
            )
            admitted = admitted_frame["outcome_bps"].to_numpy()
            # Only origins the rule EVALUATED AND DECLINED belong in the rejected set. An
            # origin whose component feature did not exist yet was never evaluated, so pooling
            # it here would measure the warm-up period as if it were selection. A decline is
            # judged at the FILL: an order the arm created and its own expiry rule killed
            # before it filled is a decline, and it is the only one a PENDING_EXPIRY arm makes.
            declined = group.filter(
                pl.col("rejection_class").is_in(list(DECLINED_CLASSES))
                & pl.col("counterfactual_outcome_bps").is_not_null()
            )
            rejected = declined["counterfactual_outcome_bps"].to_numpy()
            excluded = {
                str(row["rejection_class"]): int(row["n"])
                for row in group.filter(~pl.col("admitted"))
                .group_by("rejection_class")
                .agg(pl.len().alias("n"))
                .iter_rows(named=True)
                if str(row["rejection_class"]) not in DECLINED_CLASSES
            }
            # The band rule needs an interval, and D12 is not qualified by channel: all three
            # treatments are computed here too, and the most conservative governs.
            intervals = [
                _contrast_interval(
                    admitted_frame,
                    declined,
                    treatment,
                    domain_hours=domain_hours,
                    n_boot=n_boot,
                )
                for treatment in TREATMENTS
            ]
            # Same conservatism rule as the scale channel: fewest independent blocks wins,
            # width breaks the tie. A channel-specific rule would let the same run label two
            # effects by two standards.
            scored = [
                item
                for item in intervals
                if np.isfinite(item["ci_high_bps"] - item["ci_low_bps"])
            ]
            governing = (
                min(
                    scored,
                    key=lambda item: (
                        item["effective_blocks_admitted"] + item["effective_blocks_rejected"],
                        -(item["ci_high_bps"] - item["ci_low_bps"]),
                    ),
                )
                if scored
                else intervals[0]
            )
            # Design section 3's aggregation ordering applies to this channel too: pooling raw
            # bps across symbols lets the widest-dispersion symbol dominate. Per-symbol sigma
            # spans a factor of three here, so the normalised contrast is the estimand and the
            # raw bps is the disclosure.
            sigma = _pooled_sigma(admitted_frame, declined)
            contrast_bps = _mean(admitted) - _mean(rejected)
            # D12 governs this channel's FLOOR as well as its interval: the block counts come
            # from the same governing treatment the interval came from.
            mde_bps = _two_sample_mde(
                admitted,
                rejected,
                n_left=governing.get("effective_blocks_admitted"),
                n_right=governing.get("effective_blocks_rejected"),
            )
            # CONTROL MAGNITUDE-MATCH (design section 8): every admission rule here IS a
            # volatility gate, so admitted and declined populations differ by regime BY
            # CONSTRUCTION. The matched contrast asks the question inside each state, where
            # that difference cannot do the work.
            matched = _regime_matched_contrast(admitted_frame, declined)
            rows.append(
                {
                    "channel": "SELECTION",
                    "arm_id": arm["arm_id"],
                    "component": arm["component"],
                    "comparator_id": fixed_arm_id,
                    "lens": "ORIGIN_LENS_FILL_CONDITIONAL_BOTH_SIDES",
                    "contrast_sigma": (
                        contrast_bps / sigma if np.isfinite(sigma) and sigma > 0
                        else float("nan")
                    ),
                    "pooled_sigma_bps": sigma,
                    **matched,
                    **breakeven_spread(
                        contrast_bps * int(admitted.size), int(admitted.size)
                    ),
                    "estimand": "admitted_mean_minus_rejected_counterfactual_mean_bps",
                    "scope": scope[0],
                    "symbol": scope[1],
                    "governing_treatment": governing["treatment"],
                    "ci_low_bps": governing["ci_low_bps"],
                    "ci_high_bps": governing["ci_high_bps"],
                    "intervals_by_treatment": json.dumps(
                        {item["treatment"]: [item["ci_low_bps"], item["ci_high_bps"]]
                         for item in intervals},
                        sort_keys=True,
                    ),
                    "n_admitted": int(admitted.size),
                    "n_rejected": int(rejected.size),
                    # A property of the rule's own semantics, not of the sample: a rule that
                    # never declines an origin carrying a counterfactual has no population that
                    # could answer "does it select better trades?", and more data does not
                    # create one.
                    "rejected_population_empty": bool(rejected.size == 0),
                    "rejected_population": "EVALUATED_DECLINED_ONLY",
                    "excluded_non_admitted_by_class": json.dumps(excluded, sort_keys=True),
                    "admitted_mean_bps": _mean(admitted),
                    "rejected_counterfactual_mean_bps": _mean(rejected),
                    "contrast_bps": _mean(admitted) - _mean(rejected),
                    "admitted_positive_share": _positive_share(admitted),
                    "rejected_positive_share": _positive_share(rejected),
                    "mde_bps": mde_bps,
                    "mde_bps_unblocked": _two_sample_mde(admitted, rejected),
                    "contrast_over_mde": (
                        float(abs(contrast_bps) / mde_bps)
                        if np.isfinite(mde_bps) and mde_bps > 0 else float("nan")
                    ),
                    # The MDE expressed on the same sigma-hat scale as the contrast, so the
                    # reader can compare the two directly without converting units. Context,
                    # not a classification.
                    "mde_sigma": (
                        mde_bps / sigma
                        if np.isfinite(sigma) and sigma > 0 else float("nan")
                    ),
                    # The separately-named populations. This is an origin-lens read, so the
                    # trade-block count does not apply and is null rather than borrowed.
                    "eligible_origin_n": group.height,
                    "entry_fill_n": int(group["admitted"].sum()),
                    "close_n": int(group["exit_ts"].is_not_null().sum()),
                    "common_fill_n": None,
                    "common_close_n": None,
                    "effective_origin_blocks": (
                        governing.get("effective_blocks_admitted", 0)
                        + governing.get("effective_blocks_rejected", 0)
                    ),
                    "effective_trade_blocks": None,
                }
            )
    # infer_schema_length=None scans every row before choosing dtypes. Several columns are
    # legitimately null on a long run of leading rows - a suppressed collapse fraction, a
    # control that did not apply - and the default 100-row window then types the column Null
    # and fails on the first float. Cell size decides whether that happens, so the default
    # makes the analyser succeed or fail depending on how many symbols a universe has.
    return pl.from_dicts(rows, infer_schema_length=None) if rows else pl.DataFrame()


def _pooled_sigma(admitted: pl.DataFrame, declined: pl.DataFrame) -> float:
    """Dispersion of the pooled outcome scale, for the sigma-hat-normalised contrast."""
    values = np.concatenate(
        [
            admitted["outcome_bps"].drop_nulls().to_numpy().astype(float),
            declined["counterfactual_outcome_bps"].drop_nulls().to_numpy().astype(float),
        ]
    )
    return float(np.std(values, ddof=1)) if values.size > 1 else float("nan")


def _regime_matched_contrast(
    admitted: pl.DataFrame,
    declined: pl.DataFrame,
) -> dict[str, Any]:
    """CONTROL MAGNITUDE-MATCH, on the coarsest quantity the emission supports: the regime.

    Admission rules here are volatility gates, so an unmatched admitted-minus-declined contrast
    is partly a HIGH-versus-LOW comparison. This recomputes the contrast INSIDE each realised
    regime and reports the collapse fraction against the unmatched figure, together with each
    stratum's own comparator mean and count - a percentile without its comparator's mean is
    uninterpretable (P-24).
    """
    strata: dict[str, Any] = {}
    weighted_total = 0.0
    weight_total = 0
    # Rows the matched figure actually covers. A stratum too thin to estimate is dropped, and
    # comparing a matched figure over the surviving strata against an unmatched figure over the
    # WHOLE population would put a coverage difference into the collapse fraction and read it
    # as regime confounding. The unmatched baseline is therefore recomputed on the same rows.
    covered_admitted: list[np.ndarray] = []
    covered_declined: list[np.ndarray] = []
    for state in ("HIGH", "LOW"):
        left = admitted.filter(pl.col("regime_state") == state)["outcome_bps"].drop_nulls()
        right = declined.filter(pl.col("regime_state") == state)[
            "counterfactual_outcome_bps"
        ].drop_nulls()
        if left.len() < 2 or right.len() < 2:
            strata[state] = {"n_admitted": left.len(), "n_declined": right.len(),
                             "contrast_bps": None}
            continue
        left_values = left.to_numpy().astype(float)
        right_values = right.to_numpy().astype(float)
        contrast = float(np.mean(left_values) - np.mean(right_values))
        strata[state] = {
            "n_admitted": int(left.len()),
            "n_declined": int(right.len()),
            "admitted_mean_bps": float(np.mean(left_values)),
            "declined_mean_bps": float(np.mean(right_values)),
            "contrast_bps": contrast,
            "mde_bps": _two_sample_mde(left_values, right_values),
        }
        weighted_total += contrast * (left.len() + right.len())
        weight_total += left.len() + right.len()
        covered_admitted.append(left_values)
        covered_declined.append(right_values)
    matched = weighted_total / weight_total if weight_total else float("nan")
    all_admitted = admitted["outcome_bps"].drop_nulls().to_numpy().astype(float)
    all_declined = declined["counterfactual_outcome_bps"].drop_nulls().to_numpy().astype(float)
    matched_admitted = (
        np.concatenate(covered_admitted) if covered_admitted else np.array([], dtype=float)
    )
    matched_declined = (
        np.concatenate(covered_declined) if covered_declined else np.array([], dtype=float)
    )
    # Like for like: the unmatched comparator is the contrast on exactly the rows the matched
    # figure covers.
    unmatched = _mean(matched_admitted) - _mean(matched_declined)
    coverage = (
        float((matched_admitted.size + matched_declined.size)
              / (all_admitted.size + all_declined.size))
        if (all_admitted.size + all_declined.size) else float("nan")
    )
    # A collapse fraction is only meaningful when there is something to collapse. Dividing one
    # noise draw by another produces spectacular ratios that mean nothing, so it is emitted
    # ONLY where the unmatched contrast clears its own detection floor.
    unmatched_mde = _two_sample_mde(matched_admitted, matched_declined)
    resolves = bool(
        np.isfinite(unmatched) and np.isfinite(unmatched_mde) and abs(unmatched) >= unmatched_mde
    )
    # Suppressed values are NULL, never NaN. A NaN is non-null on every row and reads as
    # "populated" to any check that tests null-ness - the exact shape of the defect this
    # apparatus was corrected for elsewhere.
    collapse = (
        float(1.0 - matched / unmatched)
        if resolves and unmatched != 0 and np.isfinite(matched)
        else None
    )
    return {
        "control": "MAGNITUDE_MATCH_REGIME_STRATIFIED",
        "unmatched_contrast_bps": unmatched,
        "whole_population_contrast_bps": _mean(all_admitted) - _mean(all_declined),
        "matched_coverage_share": coverage,
        "unmatched_contrast_mde_bps": unmatched_mde,
        "unmatched_contrast_resolves": resolves,
        "regime_matched_contrast_bps": matched,
        "regime_match_collapse_fraction": collapse,
        "collapse_fraction_suppressed_reason": (
            None if resolves else "unmatched contrast is inside its own noise floor"
        ),
        "regime_strata": json.dumps(strata, sort_keys=True, default=str),
        "regime_imbalance_note": (
            "an admission rule that is itself a volatility gate splits the two populations by "
            "regime by construction; the matched figure is the one a selection claim rests on"
        ),
    }


def _by_symbol_and_pooled(frame: pl.DataFrame):
    for symbol, group in frame.group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        yield ("PER_SYMBOL", str(name)), group
    yield ("POOLED", None), frame


def _mean(values: np.ndarray) -> float:
    return float(np.mean(values)) if values.size else float("nan")


def _positive_share(values: np.ndarray) -> float:
    return float(np.mean(values > 0)) if values.size else float("nan")


def _two_sample_mde(
    left: np.ndarray,
    right: np.ndarray,
    *,
    n_left: int | None = None,
    n_right: int | None = None,
) -> float:
    """Two-sample MDE at the realised split, in bps. The bite check the design co-designs.

    `n_left`/`n_right` override the raw row counts with the governing treatment's INDEPENDENT
    block counts. The interval on this contrast comes from a block bootstrap, so taking the
    floor from unblocked row counts would band one effect by two standards - a floor that
    credits every row as independent against an interval that does not.
    """
    if left.size < 2 or right.size < 2:
        return float("nan")
    size_left = int(n_left) if n_left else int(left.size)
    size_right = int(n_right) if n_right else int(right.size)
    if size_left < 1 or size_right < 1:
        return float("nan")
    pooled = np.concatenate([left, right])
    sigma = float(np.std(pooled, ddof=1))
    return MDE_Z * sigma * np.sqrt(1.0 / size_left + 1.0 / size_right)


# `_selection_band` is withdrawn. It classified a contrast by comparing it with its own floor,
# which is the power label the contract forbids. `contrast_bps`, `mde_bps`, `mde_sigma`,
# `contrast_over_mde`, both interval bounds, `n_admitted`, `n_rejected` and
# `effective_origin_blocks` are all on the row; the reader does the comparison.
#
# One factual column survives from it, because it is a statement about the POPULATION rather
# than about the result: `rejected_population_empty` records that a rule declined no origin
# carrying a counterfactual, which is a property of the arm's semantics and no amount of data
# changes it.


# --------------------------------------------------------------------------- #
# Arm A - baseline characterisation (design section 6A / OD-3)
# --------------------------------------------------------------------------- #


def baseline_characterisation(
    episodes: pl.DataFrame,
    *,
    baseline_arm_id: str = "FIXED_SIZE_UNIT",
    uncapped_arm_id: str = "UNCAPPED_HOLD_SAFETY_CEILING",
) -> pl.DataFrame:
    """OD-3: characterise the baseline alone, first, per symbol and pooled.

    Design section 6A makes this first-class, not a preamble: the arm's own level, reported
    before any component is compared against it. Everything here is a description of what the
    fixed strategy did - no comparison, no band, no claim.

    `win_share` is reported beside `breakeven_win_share` - the win share the arm's own realised
    average win and loss would need in order to break even at zero cost. Since no cost is
    charged anywhere in this run (D9), that is a gross break-even and the true one is worse.
    """
    rows: list[dict[str, Any]] = []
    for arm_id in (baseline_arm_id, uncapped_arm_id):
        arm = episodes.filter(pl.col("arm_id") == arm_id)
        if arm.is_empty():
            continue
        for scope, group in _by_symbol_and_pooled(arm):
            closed = group.filter(pl.col("exit_ts").is_not_null())
            outcomes = closed["outcome_bps"].drop_nulls().to_numpy().astype(float)
            wins = outcomes[outcomes > 0]
            losses = outcomes[outcomes < 0]
            mean_win = float(np.mean(wins)) if wins.size else float("nan")
            mean_loss = float(abs(np.mean(losses))) if losses.size else float("nan")
            holds = closed["hold_bars_realised"].drop_nulls().to_numpy().astype(float)
            win_share = float(np.mean(outcomes > 0)) if outcomes.size else float("nan")
            rows.append(
                {
                    "arm_id": arm_id,
                    "scope": scope[0],
                    "symbol": scope[1],
                    "origins": group.height,
                    "orders_created": int(group["order_created"].sum())
                    if "order_created" in group.columns else None,
                    "fills": int(group["admitted"].sum()),
                    "closed": closed.height,
                    "censored": int(group["censored"].sum()),
                    # Exposure per origin: the share of eligible origins that became capital.
                    "fill_rate_per_origin": (
                        float(group["admitted"].sum() / group.height) if group.height else None
                    ),
                    "fill_rate_per_order": (
                        float(group["admitted"].sum() / group["order_created"].sum())
                        if "order_created" in group.columns and group["order_created"].sum()
                        else None
                    ),
                    "gross_mean_bps": _mean(outcomes),
                    "gross_median_bps": (
                        float(np.median(outcomes)) if outcomes.size else float("nan")
                    ),
                    "gross_sigma_bps": (
                        float(np.std(outcomes, ddof=1)) if outcomes.size > 1 else float("nan")
                    ),
                    "win_share": win_share,
                    "mean_win_bps": mean_win,
                    "mean_loss_bps": mean_loss,
                    # p* = L / (W + L): the win share this arm's own payoff shape needs to break
                    # even. Gross, because no cost is charged (D9).
                    "breakeven_win_share": (
                        float(mean_loss / (mean_win + mean_loss))
                        if np.isfinite(mean_win) and np.isfinite(mean_loss)
                        and (mean_win + mean_loss) > 0
                        else float("nan")
                    ),
                    "win_share_minus_breakeven": (
                        float(win_share - mean_loss / (mean_win + mean_loss))
                        if np.isfinite(win_share) and np.isfinite(mean_win)
                        and np.isfinite(mean_loss) and (mean_win + mean_loss) > 0
                        else float("nan")
                    ),
                    "exit_composition": json.dumps(
                        {
                            str(row["exit_reason"]): int(row["n"])
                            for row in closed.group_by("exit_reason")
                            .agg(pl.len().alias("n"))
                            .sort("n", descending=True)
                            .iter_rows(named=True)
                        },
                        sort_keys=True,
                    ),
                    "hold_bars_median": (
                        float(np.median(holds)) if holds.size else float("nan")
                    ),
                    "hold_bars_p90": (
                        float(np.percentile(holds, 90)) if holds.size else float("nan")
                    ),
                    "hold_bars_max": float(np.max(holds)) if holds.size else float("nan"),
                    "regime_share_high": (
                        float(np.mean(closed["regime_state"].to_numpy() == "HIGH"))
                        if closed.height else float("nan")
                    ),
                    "class": "BASELINE_CHARACTERISATION_NO_COMPARISON_NO_BAND",
                    "cost_basis": "GROSS_NO_COST_CHARGED_SPREAD_UNAVAILABLE",
                }
            )
    # infer_schema_length=None scans every row before choosing dtypes. Several columns are
    # legitimately null on a long run of leading rows - a suppressed collapse fraction, a
    # control that did not apply - and the default 100-row window then types the column Null
    # and fails on the first float. Cell size decides whether that happens, so the default
    # makes the analyser succeed or fail depending on how many symbols a universe has.
    return pl.from_dicts(rows, infer_schema_length=None) if rows else pl.DataFrame()


# --------------------------------------------------------------------------- #
# Leak tripwire (design section 9) - HARD, and retained after OD-17
# --------------------------------------------------------------------------- #


def tripwire_collapse(
    causal: pl.DataFrame,
    shifted: pl.DataFrame,
    *,
    domain_hours: int,
    n_boot: int = 500,
) -> dict[str, Any]:
    """Compare the causal arm set with its future-shifted twin.

    The shift is not a permutation, so there is no fixed-point concern; its non-vacuity is
    checked directly on the two sufficient statistics of the primary estimand - WHICH origins
    each arm admits, and WHAT capital it commits. A shifted arm that outperforms its causal
    twin beyond that cell's own detection floor is an acausal leak, and the emission is
    invalid: that is a data fault, never a finding about edge.
    """
    causal_admitted = set(
        causal.filter(pl.col("admitted")).select("arm_id", "symbol", "origin_id").rows()
    )
    shifted_admitted = set(
        shifted.filter(pl.col("admitted")).select("arm_id", "symbol", "origin_id").rows()
    )
    admission_changed = len(causal_admitted ^ shifted_admitted)
    causal_capital = causal.select("arm_id", "symbol", "origin_id", "risk_size").rows()
    shifted_capital = shifted.select("arm_id", "symbol", "origin_id", "risk_size").rows()
    capital_changed = len(set(causal_capital) ^ set(shifted_capital))

    arms = sorted(
        set(
            causal.filter(
                (pl.col("device") == "SIZE") & (pl.col("arm_id") != "FIXED_SIZE_UNIT")
            )["arm_id"].to_list()
        )
    )
    comparisons: list[dict[str, Any]] = []
    for arm_id in arms:
        pair = {}
        for label, frame in (("causal", causal), ("shifted", shifted)):
            series = paired_series(
                frame,
                arm_id,
                "FIXED_SIZE_UNIT",
                "capital_normalised_return_bps",
                domain_hours=domain_hours,
            )
            interval = clustered_interval(series, "V_A_UNCHUNKED", n_boot=n_boot)
            pair[label] = interval
        causal_effect = abs(pair["causal"]["estimate_sigma"])
        shifted_effect = abs(pair["shifted"]["estimate_sigma"])
        mde = pair["causal"]["mde_sigma"]
        survives = bool(
            np.isfinite(shifted_effect)
            and np.isfinite(causal_effect)
            and np.isfinite(mde)
            and shifted_effect - causal_effect > mde
        )
        # The tripwire is named for a COLLAPSE, and only an arm that has an edge can collapse.
        # Where the causal effect is already inside the cell's own floor there is nothing to
        # destroy, and "did not survive" is not evidence of causality - it is the tripwire
        # having no bite on that arm. Recorded per arm so the pass cannot be read as more than
        # it is.
        edge_present = bool(
            np.isfinite(causal_effect) and np.isfinite(mde) and causal_effect >= mde
        )
        comparisons.append(
            {
                "arm_id": arm_id,
                "channel": "SCALE",
                "causal_effect_sigma": pair["causal"]["estimate_sigma"],
                "shifted_effect_sigma": pair["shifted"]["estimate_sigma"],
                "mde_sigma": mde,
                "collapse_fraction": (
                    float(1.0 - shifted_effect / causal_effect)
                    if causal_effect > 0 and np.isfinite(shifted_effect)
                    else None
                ),
                "causal_edge_present": edge_present,
                # Where an edge exists the design requires it to collapse INTO the noise floor,
                # not merely to shrink: collapse fraction ~ 1.0.
                "collapsed_into_noise": bool(
                    edge_present and np.isfinite(shifted_effect) and shifted_effect < mde
                ),
                "shifted_edge_survives": survives,
            }
        )
    # The selection channel is half the arm set and was previously never leak-tested. Its
    # statistic is the admitted-minus-declined contrast, so the shift is checked on that too.
    selection_arms = sorted(
        set(
            causal.filter(
                (pl.col("arm_class").is_in(["NATIVE", "NATIVE_COMBINATION"]))
                & (pl.col("arm_id") != "FIXED_NATIVE_BREAKOUT")
            )["arm_id"].to_list()
        )
    )
    for arm_id in selection_arms:
        pair = {}
        for label, frame in (("causal", causal), ("shifted", shifted)):
            rows = frame.filter(pl.col("arm_id") == arm_id)
            left = rows.filter(pl.col("admitted") & pl.col("outcome_bps").is_not_null())[
                "outcome_bps"
            ].to_numpy()
            right = rows.filter(
                (pl.col("rejection_class") == "EVALUATED_DECLINED")
                & pl.col("counterfactual_outcome_bps").is_not_null()
            )["counterfactual_outcome_bps"].to_numpy()
            pair[label] = {
                "contrast": _mean(left) - _mean(right) if left.size and right.size else np.nan,
                "mde": _two_sample_mde(left, right),
                "n_declined": int(right.size),
            }
        causal_effect = abs(pair["causal"]["contrast"])
        shifted_effect = abs(pair["shifted"]["contrast"])
        mde = pair["causal"]["mde"]
        applicable = pair["causal"]["n_declined"] > 0 and pair["shifted"]["n_declined"] > 0
        survives = bool(
            applicable
            and np.isfinite(shifted_effect)
            and np.isfinite(causal_effect)
            and np.isfinite(mde)
            and shifted_effect - causal_effect > mde
        )
        edge_present = bool(
            applicable
            and np.isfinite(causal_effect)
            and np.isfinite(mde)
            and causal_effect >= mde
        )
        comparisons.append(
            {
                "arm_id": arm_id,
                "channel": "SELECTION",
                "causal_effect_bps": pair["causal"]["contrast"],
                "shifted_effect_bps": pair["shifted"]["contrast"],
                "mde_bps": mde,
                "applicable": applicable,
                "causal_edge_present": edge_present,
                "collapsed_into_noise": bool(
                    edge_present and np.isfinite(shifted_effect) and shifted_effect < mde
                ),
                "shifted_edge_survives": survives,
            }
        )

    surviving = [item for item in comparisons if item["shifted_edge_survives"]]
    non_vacuous = bool(admission_changed > 0 or capital_changed > 0)
    with_edge = [item for item in comparisons if item.get("causal_edge_present")]
    failed_to_collapse = [
        item["arm_id"] for item in with_edge if not item.get("collapsed_into_noise")
    ]
    return {
        "arms_compared": len(comparisons),
        "scale_arms_compared": len(arms),
        "selection_arms_compared": len(selection_arms),
        "known_limit": (
            "the statistic is scale-invariant in the delta series, so a strictly proportional "
            "leak would not trip it; it detects a leak that changes WHICH origins are admitted "
            "or the RELATIVE size committed, which is the leak this apparatus can produce"
        ),
        "admission_rows_changed": admission_changed,
        "committed_capital_rows_changed": capital_changed,
        "non_vacuous": non_vacuous,
        "surviving_arms": [item["arm_id"] for item in surviving],
        # How much of the arm set the tripwire could actually bite on. An arm whose causal
        # effect is already inside the cell's floor has no edge to destroy, so its "did not
        # survive" carries no causal information.
        "arms_with_a_causal_edge": len(with_edge),
        # INFORMATIVE, not a gate. See the HARD criterion below for why.
        "arms_with_an_edge_that_did_not_collapse_into_noise": failed_to_collapse,
        "informative": bool(with_edge),
        "bite_note": (
            "no arm in this cell carries a causal effect above its own detection floor, so the "
            "tripwire had nothing to collapse; the pass records the absence of a surviving "
            "shifted edge, NOT a demonstrated collapse"
            if not with_edge
            else "the tripwire had at least one arm with an edge to destroy"
        ),
        "non_collapse_note": (
            "a SIZE arm's paired difference is dominated by the exposure term "
            "(E[size] - 1) x E[outcome], and a one-bar availability shift barely changes the "
            "GATE RATE, so the exposure term is nearly invariant to the shift. An arm whose "
            "effect is mostly exposure arithmetic therefore need not collapse, and requiring it "
            "to would fail a valid emission. This is the scale-invariance limit recorded above, "
            "seen from the other side."
        ),
        "comparisons": comparisons,
        # HARD criterion, taken from design section 9's REJECT clause: the shift must be
        # non-vacuous, and no shifted arm may outperform its causal twin beyond that cell's own
        # floor. Section 9 states "expected collapse fraction ~ 1.0" as an EXPECTATION; its
        # REJECT condition is "a SURVIVING edge under the shift".
        #
        # An earlier version of this function ALSO required every arm that had an edge to
        # collapse INTO the noise floor, and blocked when one did not. That is overreach, and it
        # produced a false HARD failure on crypto H4 `ADP_SWING_SCALE_SIZE_STATE_HALVE_HIGH`:
        # causal effect 0.0648 sigma-hat against a floor of 0.0626 - clearing it by 3.5% - with a
        # shifted twin of 0.0656, which is statistically the same number rather than an
        # outperforming one. A HARD failure declares the EMISSION INVALID and sends the operator
        # to fix the data; that verdict would have been wrong. Collapse behaviour is reported per
        # arm and in the two fields above, and gates nothing.
        "pass": bool(non_vacuous and not surviving),
        "class": "future_destroy HARD VALIDITY",
        "failure_meaning": "an acausal leak: fix the data, never read it as 'no edge'",
    }


# --------------------------------------------------------------------------- #
# Report ladder (design section 6E) - a concentration diagnostic, not a strategy branch
# --------------------------------------------------------------------------- #


def pool_filter_ladder(
    estimates: pl.DataFrame,
    *,
    value_column: str = "mean_delta_raw",
) -> pl.DataFrame:
    """(i) every symbol, (ii) pooled, (iii) pooled with each drop - all three always shown.

    Nothing is tuned at entry and no trade is selected on its own outcome: the drops are
    applied to the REPORT, per symbol, in the same shape as the SPDR-021 leave-one-out that
    flipped a pooled sign.

    The ladder's pooled figure is the **unweighted mean of per-symbol means in raw units**, and
    is deliberately named as such: it is NOT the sigma-hat-normalised pooled estimate that the
    estimate tables carry under the word POOLED. Two different quantities under one word is how
    a concentration diagnostic gets quoted as an effect size.
    """
    if estimates.is_empty() or value_column not in estimates.columns:
        return pl.DataFrame()
    per_symbol = estimates.filter(pl.col("scope") == "PER_SYMBOL")
    rows: list[dict[str, Any]] = []
    group_keys = [
        name for name in ("channel", "arm_id", "lens", "regime") if name in per_symbol.columns
    ]
    for key, group in per_symbol.group_by(group_keys, maintain_order=True):
        values = group.select("symbol", pl.col(value_column).alias("mean_delta_raw")).drop_nulls()
        if values.height < 2:
            continue
        ordered = values.sort("mean_delta_raw")
        worst = ordered["symbol"][0]
        best = ordered["symbol"][-1]
        for label, dropped in (
            ("POOLED_ALL_SYMBOLS", set()),
            ("POOLED_DROP_WORST", {worst}),
            ("POOLED_DROP_BEST", {best}),
            ("POOLED_DROP_BOTH", {worst, best}),
        ):
            kept = values.filter(~pl.col("symbol").is_in(list(dropped)))
            rows.append(
                {
                    **dict(zip(group_keys, key, strict=True)),
                    "ladder_step": label,
                    "dropped_symbols": ",".join(sorted(dropped)) or None,
                    "n_symbols": kept.height,
                    "unweighted_mean_of_symbol_means_raw": (
                        float(kept["mean_delta_raw"].mean()) if kept.height else float("nan")
                    ),
                    "worst_symbol": worst,
                    "best_symbol": best,
                    "value_column": value_column,
                    "class": "CONCENTRATION_DIAGNOSTIC_NOT_A_CLAIM",
                    "not_the_headline_pooled_estimate": (
                        "raw units, unweighted across symbols; the estimate tables' POOLED is "
                        "sigma-hat-normalised and is a different quantity"
                    ),
                }
            )
    # infer_schema_length=None scans every row before choosing dtypes. Several columns are
    # legitimately null on a long run of leading rows - a suppressed collapse fraction, a
    # control that did not apply - and the default 100-row window then types the column Null
    # and fails on the first float. Cell size decides whether that happens, so the default
    # makes the analyser succeed or fail depending on how many symbols a universe has.
    return pl.from_dicts(rows, infer_schema_length=None) if rows else pl.DataFrame()
