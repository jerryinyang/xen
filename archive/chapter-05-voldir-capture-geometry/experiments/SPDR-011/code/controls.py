"""SPDR-011 predeclared control and UTC-date inference machinery.

DEVIATIONS: none. These helpers emit measurements only; no value threshold becomes a
machine verdict. Future-path destruction is an integrity report consumed by QA.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import polars as pl

from xen.evaluation import trimmed_mean
from xen.xena.controls import make_derangement


STRATA = ("symbol", "band", "calendar_third")


def stratified_derangement(events: pl.DataFrame, *, seed: int) -> pl.DataFrame:
    """Map every event to another path within symbol/calendar-third, with zero fixed points."""
    required = {"event_id", *STRATA}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"events missing required columns: {missing}")
    if events["event_id"].n_unique() != events.height:
        raise ValueError("event_id must be unique")

    rng = np.random.default_rng(seed)
    records: list[dict[str, str]] = []
    ordered = events.select("event_id", *STRATA).sort([*STRATA, "event_id"])
    for group in ordered.partition_by(list(STRATA), maintain_order=True):
        ids = group["event_id"].to_list()
        if len(ids) < 2:
            raise ValueError(
                "future destroy requires at least two events in every symbol/calendar-third stratum"
            )
        permutation = make_derangement(len(ids), rng)
        if np.any(permutation == np.arange(len(ids))):
            raise AssertionError("derangement contains a fixed point")
        records.extend(
            {"source_event_id": source, "path_event_id": ids[int(target)]}
            for source, target in zip(ids, permutation, strict=True)
        )
    result = pl.DataFrame(records).sort("source_event_id")
    if result.filter(pl.col("source_event_id") == pl.col("path_event_id")).height:
        raise AssertionError("future destroy contains a fixed point")
    return result


def _high_minus_other(labels: np.ndarray, values: np.ndarray) -> float:
    high = values[labels == "HIGH"]
    other = values[labels != "HIGH"]
    if not len(high) or not len(other):
        raise ValueError("sentinel calibration requires HIGH and MID/LOW events")
    return float(np.mean(high) - np.mean(other))


def _deranged_effect(events: pl.DataFrame, sentinel: dict[str, float], seed: int) -> float:
    mapping = stratified_derangement(events, seed=seed)
    labels = events.select("event_id", "vol_tercile").rename(
        {"event_id": "source_event_id"}
    )
    mapped = mapping.join(labels, on="source_event_id", validate="1:1")
    path_values = pl.DataFrame(
        {
            "path_event_id": list(sentinel),
            "sentinel_bps": list(sentinel.values()),
        }
    )
    mapped = mapped.join(path_values, on="path_event_id", validate="1:1")
    return _high_minus_other(
        mapped["vol_tercile"].to_numpy(), mapped["sentinel_bps"].to_numpy()
    )


def calibrate_future_destroy_sentinel(
    events: pl.DataFrame,
    *,
    n_seeds: int = 2000,
    seed0: int = 31_000,
) -> dict[str, Any]:
    """Freeze the synthetic +50-bps tripwire envelope before any real outcome is read."""
    if n_seeds < 2000:
        raise ValueError("future-destroy calibration requires at least 2,000 seeds")
    labels = events["vol_tercile"].to_numpy()
    sentinel_values = np.where(labels == "HIGH", 50.0, 0.0)
    sentinel = dict(zip(events["event_id"].to_list(), sentinel_values, strict=True))
    raw = _high_minus_other(labels, sentinel_values)
    null = np.asarray(
        [_deranged_effect(events, sentinel, seed0 + index) for index in range(n_seeds)],
        dtype=float,
    )
    post_destroy = _deranged_effect(events, sentinel, seed0 + n_seeds)
    envelope = np.quantile(null, [0.005, 0.995])
    return {
        "control_class": "future_destroy",
        "derangement": "within_symbol_calendar_third",
        "n_calibration_seeds": int(n_seeds),
        "seed0": int(seed0),
        "audit_seed": int(seed0 + n_seeds),
        "derangement_zero_fixed_points": True,
        "raw_sentinel_bps": raw,
        "post_destroy_sentinel_bps": float(post_destroy),
        "synthetic_null_envelope_99": [float(envelope[0]), float(envelope[1])],
        "acceptance_rule": (
            "raw sentinel 50 +/- 0.5 bps; audit-seed post-destroy effect inside the "
            "pre-frozen 99% synthetic-null envelope"
        ),
    }


def future_destroy_paths(
    events: pl.DataFrame,
    *,
    seed: int,
    outcome_columns: Sequence[str],
) -> pl.DataFrame:
    """Replace each event's outcomes with another path in its frozen stratum."""
    mapping = stratified_derangement(events, seed=seed)
    missing = sorted(set(outcome_columns) - set(events.columns))
    if missing:
        raise ValueError(f"outcome columns missing: {missing}")
    paths = events.select(
        pl.col("event_id").alias("path_event_id"),
        *[pl.col(name).alias(f"destroyed_{name}") for name in outcome_columns],
    )
    identities = events.drop(list(outcome_columns)).rename({"event_id": "source_event_id"})
    return identities.join(mapping, on="source_event_id", validate="1:1").join(
        paths,
        on="path_event_id",
        validate="m:1",
    )


def direction_derangement(events: pl.DataFrame, *, seed: int) -> pl.DataFrame:
    """Reassign directions through a zero-fixed event mapping within frozen strata."""
    required = {"event_id", "direction", *STRATA}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"events missing required columns: {missing}")
    mapping = stratified_derangement(events, seed=seed).rename(
        {"path_event_id": "direction_event_id"}
    )
    directions = events.select(
        pl.col("event_id").alias("direction_event_id"),
        pl.col("direction").alias("deranged_direction"),
    )
    return mapping.join(directions, on="direction_event_id", validate="m:1")


def matched_random_timing(
    live: pl.DataFrame,
    candidates: pl.DataFrame,
    *,
    n_seeds: int = 2000,
    seed0: int = 41_000,
) -> pl.DataFrame:
    """Match non-breakout boundaries by exact exposure cell, then nearest beta.

    A live event may never retain its own UTC date. Candidate reuse is forbidden within a
    seed; different seeds are independent report draws. Candidate construction (including
    exclusion of all signal episode windows) is an upstream causal obligation.
    """
    exact = (
        "symbol",
        "band",
        "direction",
        "utc_slot",
        "vol_tercile",
        "calendar_third",
        "occupancy",
    )
    live_required = {"event_id", "trade_day", "beta60", *exact}
    candidate_required = {"candidate_id", "trade_day", "beta60", *exact}
    live_missing = sorted(live_required - set(live.columns))
    candidate_missing = sorted(candidate_required - set(candidates.columns))
    if live_missing or candidate_missing:
        raise ValueError(
            f"matched timing columns missing: live={live_missing}, candidates={candidate_missing}"
        )
    if n_seeds < 1:
        raise ValueError("n_seeds must be positive")

    live_rows = live.sort("event_id").to_dicts()
    candidate_rows = candidates.sort("candidate_id").to_dicts()
    # A13: bucket candidates by their exact-match cell once instead of rescanning every
    # candidate for every live event of every seed. Buckets are filled in candidate_id
    # order, so each pool is the same list, in the same order, that the full scan built.
    # Every `exact` field is a non-null string, integer or +/-1 direction, so tuple-key
    # equality is the same relation as the per-field comparison it replaces.
    cells: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in candidate_rows:
        cells.setdefault(tuple(row[name] for name in exact), []).append(row)
    results: list[dict[str, Any]] = []
    for seed in range(seed0, seed0 + n_seeds):
        rng = np.random.default_rng(seed)
        used: set[str] = set()
        for event in live_rows:
            pool = [
                row
                for row in cells.get(tuple(event[name] for name in exact), ())
                if row["candidate_id"] not in used
                and row["trade_day"] != event["trade_day"]
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
                        **{name: event[name] for name in exact},
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
                    **{name: event[name] for name in exact},
                }
            )
    return pl.DataFrame(results, infer_schema_length=None).sort(["seed", "event_id"])


def random_top2_cluster_matches(
    events: pl.DataFrame,
    *,
    symbols: Sequence[str],
    realised_pairs: pl.DataFrame,
    n_seeds: int = 2000,
    seed0: int = 51_000,
) -> pl.DataFrame:
    """Match realised TOP2 to date-level two-symbol clusters by occupancy then signed beta."""
    required = {"trade_day", "symbol", "top2", "direction", "beta60"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"events missing required columns: {missing}")
    if len(symbols) != 5 or len(set(symbols)) != 5:
        raise ValueError("L4 requires the frozen five-symbol eligible cross-section")
    if n_seeds < 1:
        raise ValueError("n_seeds must be positive")
    pair_required = {"trade_day", "symbol_1", "symbol_2"}
    pair_missing = sorted(pair_required - set(realised_pairs.columns))
    if pair_missing:
        raise ValueError(f"realised TOP2 pairs missing columns: {pair_missing}")
    realised_pair_map = {
        row["trade_day"]: frozenset((row["symbol_1"], row["symbol_2"]))
        for row in realised_pairs.iter_rows(named=True)
    }

    dates = events["trade_day"].unique().sort().to_list()
    aggregate = {
        (row["trade_day"], row["symbol"]): row
        for row in (
            events.group_by("trade_day", "symbol")
            .agg(
                pl.len().alias("episode_count"),
                (pl.col("direction") * pl.col("beta60"))
                .sum()
                .alias("signed_beta_exposure"),
            )
            .iter_rows(named=True)
        )
    }
    realised = {
        row["trade_day"]: row
        for row in (
            events.filter(pl.col("top2"))
            .group_by("trade_day")
            .agg(
                pl.len().alias("episode_count"),
                (pl.col("direction") * pl.col("beta60"))
                .sum()
                .alias("signed_beta_exposure"),
            )
            .iter_rows(named=True)
        )
    }
    from itertools import combinations

    candidates: dict[Any, list[dict[str, Any]]] = {}
    for trade_day in dates:
        target = realised.get(
            trade_day,
            {"episode_count": 0, "signed_beta_exposure": 0.0},
        )
        pairs = []
        for first, second in combinations(sorted(symbols), 2):
            if frozenset((first, second)) == realised_pair_map.get(trade_day):
                continue
            rows = [aggregate.get((trade_day, symbol)) for symbol in (first, second)]
            count = sum(int(row["episode_count"]) if row else 0 for row in rows)
            exposure = sum(float(row["signed_beta_exposure"]) if row else 0.0 for row in rows)
            if count == int(target["episode_count"]):
                pairs.append(
                    {
                        "symbols": [first, second],
                        "episode_count": count,
                        "signed_beta_exposure": exposure,
                        "beta_distance": abs(exposure - float(target["signed_beta_exposure"])),
                    }
                )
        if pairs:
            minimum = min(pair["beta_distance"] for pair in pairs)
            pairs = [pair for pair in pairs if pair["beta_distance"] == minimum]
        candidates[trade_day] = pairs

    results: list[dict[str, Any]] = []
    for seed in range(seed0, seed0 + n_seeds):
        rng = np.random.default_rng(seed)
        for trade_day in dates:
            pool = candidates[trade_day]
            target = realised.get(
                trade_day,
                {"episode_count": 0, "signed_beta_exposure": 0.0},
            )
            if not pool:
                results.append(
                    {
                        "seed": seed,
                        "trade_day": trade_day,
                        "symbol_1": None,
                        "symbol_2": None,
                        "realised_top2_episode_count": int(target["episode_count"]),
                        "matched_episode_count": None,
                        "beta_distance": None,
                        "match_reason": "NO_EXACT_OCCUPANCY_PAIR",
                    }
                )
                continue
            chosen = pool[int(rng.integers(0, len(pool)))]
            results.append(
                {
                    "seed": seed,
                    "trade_day": trade_day,
                    "symbol_1": chosen["symbols"][0],
                    "symbol_2": chosen["symbols"][1],
                    "realised_top2_episode_count": int(target["episode_count"]),
                    "matched_episode_count": int(chosen["episode_count"]),
                    "beta_distance": float(chosen["beta_distance"]),
                    "match_reason": None,
                }
            )
    return pl.DataFrame(results, infer_schema_length=None).sort(["seed", "trade_day"])


def _partial_residue(
    source: pl.DataFrame,
    mapping: pl.DataFrame,
    *,
    assigned_direction_col: str | None = None,
) -> float:
    paths = source.select(
        pl.col("event_id").alias("path_event_id"),
        (pl.col("gross_signed_4h_bps") * pl.col("direction")).alias("raw_path_bps"),
    )
    joined = mapping.join(paths, on="path_event_id", validate="m:1")
    direction = (
        pl.col(assigned_direction_col)
        if assigned_direction_col is not None
        else pl.col("direction")
    )
    joined = joined.with_columns(
        (direction * pl.col("raw_path_bps") - pl.col("total_bps") - 2.0).alias("residue")
    )
    high = joined.filter(pl.col("vol_tercile") == "HIGH")["residue"]
    other = joined.filter(pl.col("vol_tercile") != "HIGH")["residue"]
    if high.is_empty() or other.is_empty():
        return float("nan")
    return float(high.mean() - other.mean())


def conversion_control_batteries(
    artifact: pl.DataFrame,
    *,
    n_seeds: int = 2000,
    seed0: int = 31_000,
) -> dict[str, Any]:
    """Run frozen direction and future-path batteries after the estimand gate."""
    if n_seeds < 1:
        raise ValueError("n_seeds must be positive")
    required = {
        "event_id",
        "symbol",
        "band",
        "calendar_third",
        "direction",
        "vol_tercile",
        "gross_signed_4h_bps",
        "total_bps",
        "4h_available",
    }
    missing = sorted(required - set(artifact.columns))
    if missing:
        raise ValueError(f"artifact missing control columns: {missing}")
    source = artifact.filter(pl.col("4h_available")).select(sorted(required - {"4h_available"}))
    identity = source.select(
        pl.col("event_id").alias("source_event_id"),
        pl.col("event_id").alias("path_event_id"),
        "direction",
        "vol_tercile",
        "total_bps",
    )
    raw = _partial_residue(source, identity)
    direction_effects: list[float] = []
    future_effects: list[float] = []
    changed_fractions: list[float] = []
    for seed in range(seed0, seed0 + n_seeds):
        direction_map = direction_derangement(source, seed=seed)
        direction_rows = (
            source.select(
                pl.col("event_id").alias("source_event_id"),
                pl.col("event_id").alias("path_event_id"),
                "direction",
                "vol_tercile",
                "total_bps",
            )
            .join(direction_map, on="source_event_id", validate="1:1")
        )
        direction_effects.append(
            _partial_residue(
                source,
                direction_rows,
                assigned_direction_col="deranged_direction",
            )
        )
        changed_fractions.append(
            float(
                direction_rows.select(
                    (pl.col("direction") != pl.col("deranged_direction")).mean()
                ).item()
            )
        )
        future_map = stratified_derangement(source, seed=seed)
        future_rows = source.select(
            pl.col("event_id").alias("source_event_id"),
            "direction",
            "vol_tercile",
            "total_bps",
        ).join(future_map, on="source_event_id", validate="1:1")
        future_effects.append(_partial_residue(source, future_rows))

    def summary(values: list[float]) -> dict[str, Any]:
        array = np.asarray(values, dtype=float)
        return {
            "mean_bps": float(np.nanmean(array)),
            "median_bps": float(np.nanmedian(array)),
            "p05_p95_bps": [
                float(np.nanquantile(array, 0.05)),
                float(np.nanquantile(array, 0.95)),
            ],
            "one_sided_p": float(np.nanmean(array >= raw)),
            "seed_effect_bps": values,
        }

    return {
        "seed_range": [int(seed0), int(seed0 + n_seeds - 1)],
        "n_seeds": int(n_seeds),
        "raw_high_minus_other_residue_bps": raw,
        "retained_rows": source.height,
        "retained_fraction": source.height / artifact.height if artifact.height else 0.0,
        "direction_derangement": {
            **summary(direction_effects),
            "assigned_sign_changed_fraction": {
                "min": float(np.min(changed_fractions)),
                "median": float(np.median(changed_fractions)),
                "max": float(np.max(changed_fractions)),
            },
        },
        "future_path_derangement": summary(future_effects),
    }


def matched_timing_battery(
    live: pl.DataFrame,
    candidates: pl.DataFrame,
    *,
    n_seeds: int = 2000,
    seed0: int = 41_000,
) -> dict[str, Any]:
    """Run the frozen timing match and report HIGH-minus-other matched residue."""
    live_complete = live.filter(pl.col("4h_available")).with_columns(
        pl.lit(1).alias("occupancy")
    )
    candidate_complete = candidates.filter(pl.col("4h_available"))
    raw_high = live_complete.filter(pl.col("vol_tercile") == "HIGH")["partial_net_2bps"]
    raw_other = live_complete.filter(pl.col("vol_tercile") != "HIGH")["partial_net_2bps"]
    raw = float(raw_high.mean() - raw_other.mean())
    effects: list[float] = []
    matched_fractions: list[float] = []
    candidate_values = candidate_complete.select(
        "candidate_id",
        pl.col("partial_net_2bps").alias("matched_residue"),
    )
    for seed in range(seed0, seed0 + n_seeds):
        mapping = matched_random_timing(
            live_complete,
            candidate_complete,
            n_seeds=1,
            seed0=seed,
        ).join(candidate_values, on="candidate_id", how="left", validate="m:1")
        available = mapping.filter(pl.col("matched_residue").is_not_null())
        matched_fractions.append(
            available.height / live_complete.height if live_complete.height else 0.0
        )
        high = available.filter(pl.col("vol_tercile") == "HIGH")["matched_residue"]
        other = available.filter(pl.col("vol_tercile") != "HIGH")["matched_residue"]
        effects.append(
            float(high.mean() - other.mean())
            if not high.is_empty() and not other.is_empty()
            else float("nan")
        )
    array = np.asarray(effects, dtype=float)
    return {
        "seed_range": [int(seed0), int(seed0 + n_seeds - 1)],
        "n_seeds": int(n_seeds),
        "raw_high_minus_other_residue_bps": raw,
        "matched_effect_bps": effects,
        "matched_mean_bps": float(np.nanmean(array)),
        "matched_p05_p95_bps": [
            float(np.nanquantile(array, 0.05)),
            float(np.nanquantile(array, 0.95)),
        ],
        "raw_minus_matched_bps": float(raw - np.nanmean(array)),
        "matched_fraction": {
            "min": float(np.min(matched_fractions)),
            "median": float(np.median(matched_fractions)),
            "max": float(np.max(matched_fractions)),
        },
    }


def l3_date_block_ci(
    artifact: pl.DataFrame,
    *,
    n_boot: int = 10_000,
    seeds: Sequence[int] = (101, 211, 307, 401, 503),
) -> dict[str, Any]:
    """Five-seed 95% UTC-date bootstrap CI for HIGH-minus-MID/LOW L3 residue."""
    complete = artifact.filter(
        pl.col("4h_available") & pl.col("partial_net_2bps").is_not_null()
    )
    dates = complete["trade_day"].unique().sort().to_list()
    if not dates:
        raise ValueError("L3 date-block CI has no complete UTC dates")
    per_date = (
        complete.group_by("trade_day")
        .agg(
            pl.col("partial_net_2bps")
            .filter(pl.col("vol_tercile") == "HIGH")
            .sum()
            .alias("high_sum"),
            (pl.col("vol_tercile") == "HIGH").sum().alias("high_n"),
            pl.col("partial_net_2bps")
            .filter(pl.col("vol_tercile") != "HIGH")
            .sum()
            .alias("other_sum"),
            (pl.col("vol_tercile") != "HIGH").sum().alias("other_n"),
        )
        .sort("trade_day")
    )
    hs = per_date["high_sum"].to_numpy().astype(float)
    hn = per_date["high_n"].to_numpy().astype(float)
    os = per_date["other_sum"].to_numpy().astype(float)
    on = per_date["other_n"].to_numpy().astype(float)
    lowers: list[float] = []
    uppers: list[float] = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        draws = []
        for _ in range(n_boot):
            indices = rng.integers(0, len(dates), size=len(dates))
            high_n = hn[indices].sum()
            other_n = on[indices].sum()
            if high_n and other_n:
                draws.append(hs[indices].sum() / high_n - os[indices].sum() / other_n)
        if not draws:
            raise ValueError("L3 date bootstrap produced no two-arm resamples")
        lowers.append(float(np.quantile(draws, 0.025)))
        uppers.append(float(np.quantile(draws, 0.975)))
    return {
        "independent_unit": "UTC_DATE",
        "block_days": 1,
        "n_dates": len(dates),
        "n_boot_per_seed": int(n_boot),
        "seeds": [int(seed) for seed in seeds],
        "ci95_lower_by_seed": lowers,
        "ci95_upper_by_seed": uppers,
        "seed_bound_ci95": [min(lowers), max(uppers)],
    }


def adjudicate_future_destroy(
    *,
    raw_effect_bps: float,
    date_block_ci_lower_by_seed: Sequence[float],
    destroyed_effect_bps: Sequence[float],
) -> dict[str, Any]:
    """Apply A6's effect-aware real future-path integrity rule."""
    lowers = np.asarray(date_block_ci_lower_by_seed, dtype=float)
    destroyed = np.asarray(destroyed_effect_bps, dtype=float)
    if lowers.size != 5 or not np.isfinite(lowers).all():
        raise ValueError("future destroy requires five finite date-block CI lower bounds")
    if destroyed.size != 2000 or not np.isfinite(destroyed).all():
        raise ValueError("future destroy requires exactly 2,000 finite deranged effects")
    raw = float(raw_effect_bps)
    applicable = bool(raw >= 15.0 and np.min(lowers) > 0.0)
    percentile_99 = float(np.quantile(destroyed, 0.99))
    empirical_p = float(np.mean(destroyed >= raw))
    destroyed_median = float(np.median(destroyed))
    percentile_ok = raw > percentile_99 and empirical_p <= 0.01
    collapse_ok = abs(destroyed_median) <= 0.25 * abs(raw)
    status = (
        "NOT_APPLICABLE"
        if not applicable
        else "VALID"
        if percentile_ok and collapse_ok
        else "INVALID"
    )
    return {
        "integrity_status": status,
        "applicability": (
            "RAW_L3_SUPPORTED" if applicable else "RAW_L3_NOT_SUPPORTED"
        ),
        "raw_effect_bps": raw,
        "date_block_ci_lower_by_seed": lowers.tolist(),
        "destroyed_99th_percentile_bps": percentile_99,
        "empirical_one_sided_p": empirical_p,
        "destroyed_median_bps": destroyed_median,
        "destroyed_to_raw_abs_ratio": (
            abs(destroyed_median) / abs(raw) if raw else None
        ),
        "rule": (
            "if raw>=15 and all five CI lowers>0: raw>p99, p<=0.01, "
            "abs(destroyed median)<=25% abs(raw)"
        ),
    }


def _statistic(name: str) -> Callable[[np.ndarray], float]:
    return {
        "mean": lambda values: float(np.mean(values)),
        "median": lambda values: float(np.median(values)),
        "trimmed_mean_20pct": lambda values: float(trimmed_mean(values, trim=0.2)),
    }[name]


def _sample_date_blocks(
    date_rows: list[np.ndarray],
    *,
    rng: np.random.Generator,
    block_days: int,
) -> np.ndarray:
    n_dates = len(date_rows)
    sampled: list[np.ndarray] = []
    while len(sampled) < n_dates:
        start = int(rng.integers(0, n_dates))
        for offset in range(block_days):
            sampled.append(date_rows[(start + offset) % n_dates])
            if len(sampled) == n_dates:
                break
    return np.concatenate(sampled)


def date_block_inference(
    frame: pl.DataFrame,
    *,
    value_col: str,
    date_col: str = "trade_date",
    n_boot: int = 10_000,
    seeds: Sequence[int] = (101, 211, 307, 401, 503),
    block_days: int = 1,
) -> dict[str, Any]:
    """Bootstrap whole UTC-date clusters and report seed-bound intervals."""
    if n_boot < 1 or block_days < 1 or not seeds:
        raise ValueError("n_boot, block_days and seeds must be positive")
    clean = frame.select(date_col, value_col).drop_nulls().sort(date_col)
    groups = clean.partition_by(date_col, maintain_order=True)
    if not groups:
        raise ValueError("no non-null observations")
    date_rows = [group[value_col].to_numpy().astype(float) for group in groups]
    statistics: dict[str, Any] = {}
    for name in ("mean", "median", "trimmed_mean_20pct"):
        stat = _statistic(name)
        per_seed = []
        for seed in seeds:
            rng = np.random.default_rng(seed)
            draws = np.asarray(
                [stat(_sample_date_blocks(date_rows, rng=rng, block_days=block_days))
                 for _ in range(n_boot)]
            )
            per_seed.append(
                {
                    "seed": int(seed),
                    "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
                }
            )
        statistics[name] = {
            "observed": stat(clean[value_col].to_numpy().astype(float)),
            "per_seed": per_seed,
            "seed_bound_ci95": [
                min(item["ci95"][0] for item in per_seed),
                max(item["ci95"][1] for item in per_seed),
            ],
        }
    return {
        "independent_unit": "UTC_DATE",
        "n_dates": len(groups),
        "n_rows": clean.height,
        "n_boot_per_seed": int(n_boot),
        "seeds": [int(seed) for seed in seeds],
        "block_days": int(block_days),
        "statistics": statistics,
    }
