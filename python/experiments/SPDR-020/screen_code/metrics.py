"""log R metrics, day-block bootstrap envelope, sensitivity ladder (design §5, §8).

H1: SPDR-018 §6.2 blocks {1,3,7}. H4: {4,12,28} co-report. Deadband 5 bps.
Bootstrap speed path bit-identical to xen.evaluation.block_bootstrap_ci — asserted.
"""
from __future__ import annotations

import numpy as np

from xen.evaluation import block_bootstrap_ci

from config import (
    BOOT_BLOCKS_DAYS_H1,
    BOOT_BLOCKS_DAYS_H4,
    BOOT_CI_ALPHA,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    COST_FLOOR_BPS,
    DAY_NS,
    DEADBAND_BPS,
    EFFECTIVE_COVERAGE_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    IID_MDE_CONST,
    LADDER_PLANT_N,
    LADDER_RUNGS,
    NS,
    ZVOL_COVERED_N,
)


def day_index(
    ts_ns: np.ndarray,
    *,
    calendar_start_ns: int | None = None,
    calendar_end_ns: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Map timestamps to a complete consecutive UTC-day calendar.

    Days without episodes remain zero rows in sufficient-statistic arrays. This
    prevents a multi-day block from becoming a block of non-consecutive event days.
    """
    days = np.asarray(ts_ns, dtype=np.int64) // DAY_NS
    if days.size == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
    first = (
        int(calendar_start_ns) // DAY_NS
        if calendar_start_ns is not None
        else int(days.min())
    )
    last_exclusive = (
        int(calendar_end_ns + DAY_NS - 1) // DAY_NS
        if calendar_end_ns is not None
        else int(days.max()) + 1
    )
    if last_exclusive <= first:
        raise ValueError("calendar_end_ns must be after calendar_start_ns")
    if np.any(days < first) or np.any(days >= last_exclusive):
        raise ValueError("timestamps fall outside the declared calendar")
    starts = np.arange(first, last_exclusive, dtype=np.int64) * DAY_NS
    return (days - first).astype(np.int64), starts


_SUFF_COLS = ("n", "sum", "n_pos", "sum_pos", "n_neg", "sum_neg", "n_zero", "sumsq")


def day_sufficient(r: np.ndarray, day_idx: np.ndarray, n_days: int, *, deadband: float = DEADBAND_BPS) -> np.ndarray:
    """Day sufficient stats with 5 bps deadband (FLAT excluded from p)."""
    r = np.asarray(r, dtype=float)
    pos = r > deadband
    neg = r < -deadband
    zero = np.abs(r) <= deadband  # FLAT
    out = np.zeros((n_days, len(_SUFF_COLS)), dtype=float)
    out[:, 0] = np.bincount(day_idx, minlength=n_days)
    out[:, 1] = np.bincount(day_idx, weights=r, minlength=n_days)
    out[:, 2] = np.bincount(day_idx, weights=pos.astype(float), minlength=n_days)
    out[:, 3] = np.bincount(day_idx, weights=np.where(pos, r, 0.0), minlength=n_days)
    out[:, 4] = np.bincount(day_idx, weights=neg.astype(float), minlength=n_days)
    out[:, 5] = np.bincount(day_idx, weights=np.where(neg, r, 0.0), minlength=n_days)
    out[:, 6] = np.bincount(day_idx, weights=zero.astype(float), minlength=n_days)
    out[:, 7] = np.bincount(day_idx, weights=r * r, minlength=n_days)
    return out


def _agg(s: np.ndarray) -> dict:
    n = s[:, 0].sum()
    tot = s[:, 1].sum()
    n_pos = s[:, 2].sum()
    sum_pos = s[:, 3].sum()
    n_neg = s[:, 4].sum()
    sum_neg = s[:, 5].sum()
    n_zero = s[:, 6].sum()
    signed = n_pos + n_neg
    nan = float("nan")
    return {
        "n": float(n),
        "mean": tot / n if n else nan,
        "p": n_pos / signed if signed else nan,
        "W": sum_pos / n_pos if n_pos else nan,
        "L": -sum_neg / n_neg if n_neg else nan,
        "n_pos": float(n_pos),
        "n_neg": float(n_neg),
        "p_flat": n_zero / n if n else nan,
    }


def log_R_from_pWL(p: float, W: float, L: float) -> float:
    if not all(np.isfinite([p, W, L])) or p <= 0 or p >= 1 or L <= 0 or W <= 0:
        return float("nan")
    return float(np.log(W / L) - np.log((1.0 - p) / p))


def _resample_day_blocks(n_days: int, block: int, n_boot: int, seed: int) -> np.ndarray:
    eff = max(1, min(int(block), n_days - 1))
    n_blocks = int(np.ceil(n_days / eff))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n_days, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n_days]
    return idx % n_days


def _logR_boot_stats(suff: np.ndarray, block: int, n_boot: int, seed: int) -> np.ndarray:
    n_days = suff.shape[0]
    idx = _resample_day_blocks(n_days, block, n_boot, seed)
    tot = suff[idx].sum(axis=1)
    n_pos, sum_pos = tot[:, 2], tot[:, 3]
    n_neg, sum_neg = tot[:, 4], tot[:, 5]
    signed = n_pos + n_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(signed > 0, n_pos / signed, np.nan)
        W = np.where(n_pos > 0, sum_pos / n_pos, np.nan)
        L = np.where(n_neg > 0, -sum_neg / n_neg, np.nan)
        logR = np.where(
            (p > 0) & (p < 1) & (W > 0) & (L > 0),
            np.log(W / L) - np.log((1.0 - p) / p),
            np.nan,
        )
    return logR


def _logR_from_totals(tot: np.ndarray) -> np.ndarray:
    n_pos, sum_pos = tot[:, 2], tot[:, 3]
    n_neg, sum_neg = tot[:, 4], tot[:, 5]
    signed = n_pos + n_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(signed > 0, n_pos / signed, np.nan)
        W = np.where(n_pos > 0, sum_pos / n_pos, np.nan)
        L = np.where(n_neg > 0, -sum_neg / n_neg, np.nan)
        return np.where(
            (p > 0) & (p < 1) & (W > 0) & (L > 0),
            np.log(W / L) - np.log((1.0 - p) / p),
            np.nan,
        )


def _calendar_sufficient(
    returns: np.ndarray,
    timestamps: np.ndarray,
    *,
    calendar_start_ns: int,
    calendar_end_ns: int,
) -> np.ndarray:
    idx, starts = day_index(
        timestamps,
        calendar_start_ns=calendar_start_ns,
        calendar_end_ns=calendar_end_ns,
    )
    return day_sufficient(returns, idx, len(starts))


def _paired_bootstrap_values(
    sufficients: tuple[np.ndarray, ...],
    *,
    n_boot: int,
    clock: str,
    formula,
) -> tuple[np.ndarray, str]:
    n_days = sufficients[0].shape[0]
    if any(s.shape[0] != n_days for s in sufficients):
        raise ValueError("paired sufficient arrays must share one calendar")
    values: list[np.ndarray] = []
    signature_parts: list[str] = []
    for block in block_days_for_clock(clock):
        for seed in BOOT_SEEDS:
            idx = _resample_day_blocks(n_days, block, n_boot, seed)
            signature_parts.append(f"{block}:{seed}:{hash(idx.tobytes())}")
            stats = [
                _logR_from_totals(s[idx].sum(axis=1))
                for s in sufficients
            ]
            values.append(formula(*stats))
    return np.concatenate(values), "|".join(signature_parts)


def _plant_totals_via_wl(totals: np.ndarray, delta: float) -> np.ndarray:
    """Increase W/L by exp(delta), preserving p and all signed counts."""
    planted = totals.copy()
    planted[:, 3] *= np.exp(delta)
    return planted


def _plant_totals_via_p(totals: np.ndarray, delta: float) -> np.ndarray:
    """Increase logit(p) by delta, preserving W and L within each replicate."""
    planted = totals.copy()
    n_pos, n_neg = totals[:, 2], totals[:, 4]
    signed = n_pos + n_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        p0 = np.where(signed > 0, n_pos / signed, np.nan)
        p1 = 1.0 / (1.0 + ((1.0 - p0) / p0) * np.exp(-delta))
        W = np.where(n_pos > 0, totals[:, 3] / n_pos, np.nan)
        L = np.where(n_neg > 0, -totals[:, 5] / n_neg, np.nan)
    planted[:, 2] = signed * p1
    planted[:, 4] = signed * (1.0 - p1)
    planted[:, 3] = planted[:, 2] * W
    planted[:, 5] = -planted[:, 4] * L
    return planted


def _paired_effect_replicate_ladder(
    sufficients: tuple[np.ndarray, ...],
    *,
    n_boot: int,
    clock: str,
    formula,
) -> tuple[np.ndarray, str, dict]:
    """Paired base and two-operator plants using identical calendar resamples."""
    n_days = sufficients[0].shape[0]
    if any(s.shape[0] != n_days for s in sufficients):
        raise ValueError("paired sufficient arrays must share one calendar")
    base_parts: list[np.ndarray] = []
    planted_wl: dict[str, list[np.ndarray]] = {
        str(delta): [] for delta in LADDER_RUNGS
    }
    planted_p: dict[str, list[np.ndarray]] = {
        str(delta): [] for delta in LADDER_RUNGS
    }
    signature_parts = []
    count_rows = []
    for block in block_days_for_clock(clock):
        for seed in BOOT_SEEDS:
            indices = _resample_day_blocks(n_days, block, n_boot, seed)
            signature_parts.append(f"{block}:{seed}:{hash(indices.tobytes())}")
            totals = [s[indices].sum(axis=1) for s in sufficients]
            base = formula(*[_logR_from_totals(item) for item in totals])
            base_parts.append(base)
            count_row = {
                "block_days": int(block),
                "seed": int(seed),
                "requested": int(n_boot),
                "realised_base": int(np.isfinite(base).sum()),
                "realised_via_WL": {},
                "realised_via_p": {},
            }
            for delta in LADDER_RUNGS:
                rung = str(delta)
                wl_totals = list(totals)
                wl_totals[0] = _plant_totals_via_wl(totals[0], delta)
                wl_values = formula(*[
                    _logR_from_totals(item) for item in wl_totals
                ])
                planted_wl[rung].append(wl_values)
                count_row["realised_via_WL"][rung] = int(
                    np.isfinite(wl_values).sum()
                )

                p_totals = list(totals)
                p_totals[0] = _plant_totals_via_p(totals[0], delta)
                p_values = formula(*[
                    _logR_from_totals(item) for item in p_totals
                ])
                planted_p[rung].append(p_values)
                count_row["realised_via_p"][rung] = int(
                    np.isfinite(p_values).sum()
                )
            count_rows.append(count_row)
    base_values = np.concatenate(base_parts)
    finite_base = base_values[np.isfinite(base_values)]
    reference = (
        float(np.quantile(finite_base, 1 - BOOT_CI_ALPHA / 2))
        if finite_base.size else float("nan")
    )

    def rates(parts: dict[str, list[np.ndarray]]) -> dict[str, float]:
        return {
            rung: (
                float(np.nanmean(np.concatenate(values) > reference))
                if np.isfinite(reference) else float("nan")
            )
            for rung, values in parts.items()
        }

    ladder = {
        "via_WL": rates(planted_wl),
        "via_p": rates(planted_p),
        "operator_definitions": {
            "via_WL": "multiply changed-arm positive payoff sums by exp(delta), fixed p",
            "via_p": "shift changed-arm logit(p) by delta, fixed W and L",
        },
        "requested_replicates_per_seed": int(n_boot),
        "realised_replicates_per_seed": count_rows,
        "all_replicate_counts_match": bool(all(
            row["realised_base"] == n_boot
            and all(value == n_boot for value in row["realised_via_WL"].values())
            and all(value == n_boot for value in row["realised_via_p"].values())
            for row in count_rows
        )),
        "detection_reference": "upper_95pct_unplanted_paired_effect",
    }
    return base_values, "|".join(signature_parts), ladder


def paired_delta_metrics(
    changed_r: np.ndarray,
    changed_ts: np.ndarray,
    baseline_r: np.ndarray,
    baseline_ts: np.ndarray,
    *,
    n_boot: int = BOOT_RESAMPLES,
    clock: str = "H1",
    calendar_start_ns: int | None = None,
    calendar_end_ns: int | None = None,
) -> dict:
    """Paired calendar-block bootstrap of changed minus baseline log R."""
    all_ts = np.concatenate(
        [np.asarray(changed_ts, dtype=np.int64), np.asarray(baseline_ts, dtype=np.int64)]
    )
    if all_ts.size == 0:
        raise ValueError("paired bootstrap needs timestamps")
    start = (
        int(calendar_start_ns // DAY_NS * DAY_NS)
        if calendar_start_ns is not None
        else int(all_ts.min() // DAY_NS * DAY_NS)
    )
    end = (
        int((calendar_end_ns + DAY_NS - 1) // DAY_NS * DAY_NS)
        if calendar_end_ns is not None
        else int((all_ts.max() // DAY_NS + 1) * DAY_NS)
    )
    changed = _calendar_sufficient(
        np.asarray(changed_r, dtype=float),
        np.asarray(changed_ts, dtype=np.int64),
        calendar_start_ns=start,
        calendar_end_ns=end,
    )
    baseline = _calendar_sufficient(
        np.asarray(baseline_r, dtype=float),
        np.asarray(baseline_ts, dtype=np.int64),
        calendar_start_ns=start,
        calendar_end_ns=end,
    )
    values, signature, ladder = _paired_effect_replicate_ladder(
        (changed, baseline),
        n_boot=n_boot,
        clock=clock,
        formula=lambda a, b: a - b,
    )
    finite = values[np.isfinite(values)]
    point = log_R_from_pWL(**{
        k: _agg(changed)[k] for k in ("p", "W", "L")
    }) - log_R_from_pWL(**{
        k: _agg(baseline)[k] for k in ("p", "W", "L")
    })
    if finite.size:
        lo = float(np.quantile(finite, BOOT_CI_ALPHA / 2))
        hi = float(np.quantile(finite, 1 - BOOT_CI_ALPHA / 2))
    else:
        lo = hi = float("nan")
    return {
        "delta_log_R": float(point),
        "ci_low": lo,
        "ci_high": hi,
        "ci_width": hi - lo,
        "block_mde": float(point - lo),
        "paired": True,
        "calendar_days": int(changed.shape[0]),
        "n_boot_replicates": int(finite.size),
        "requested_replicates_per_seed": int(n_boot),
        "resample_signature_a": signature,
        "resample_signature_b": signature,
        "ladder": ladder,
    }


def paired_interaction_metrics(
    joint_r: np.ndarray,
    shock_r: np.ndarray,
    level_r: np.ndarray,
    baseline_r: np.ndarray,
    timestamps: np.ndarray | tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    *,
    n_boot: int = BOOT_RESAMPLES,
    clock: str = "H1",
    calendar_start_ns: int | None = None,
    calendar_end_ns: int | None = None,
) -> dict:
    """Paired bootstrap for joint − shock − level + baseline interaction."""
    if isinstance(timestamps, tuple):
        timestamp_arms = tuple(np.asarray(ts, dtype=np.int64) for ts in timestamps)
    else:
        shared = np.asarray(timestamps, dtype=np.int64)
        timestamp_arms = (shared, shared, shared, shared)
    all_ts = np.concatenate(timestamp_arms)
    start = (
        int(calendar_start_ns // DAY_NS * DAY_NS)
        if calendar_start_ns is not None
        else int(all_ts.min() // DAY_NS * DAY_NS)
    )
    end = (
        int((calendar_end_ns + DAY_NS - 1) // DAY_NS * DAY_NS)
        if calendar_end_ns is not None
        else int((all_ts.max() // DAY_NS + 1) * DAY_NS)
    )
    suff = tuple(
        _calendar_sufficient(
            np.asarray(r, dtype=float),
            arm_ts,
            calendar_start_ns=start,
            calendar_end_ns=end,
        )
        for r, arm_ts in zip(
            (joint_r, shock_r, level_r, baseline_r),
            timestamp_arms,
        )
    )
    values, signature, ladder = _paired_effect_replicate_ladder(
        suff,
        n_boot=n_boot,
        clock=clock,
        formula=lambda joint, shock, level, baseline: (
            joint - shock - level + baseline
        ),
    )
    finite = values[np.isfinite(values)]
    points = [
        log_R_from_pWL(**{k: _agg(s)[k] for k in ("p", "W", "L")})
        for s in suff
    ]
    point = points[0] - points[1] - points[2] + points[3]
    lo = float(np.quantile(finite, BOOT_CI_ALPHA / 2))
    hi = float(np.quantile(finite, 1 - BOOT_CI_ALPHA / 2))
    return {
        "delta_log_R": float(point),
        "ci_low": lo,
        "ci_high": hi,
        "ci_width": hi - lo,
        "block_mde": float(point - lo),
        "paired": True,
        "interaction_formula": "joint-shock-level+baseline",
        "n_boot_replicates": int(finite.size),
        "requested_replicates_per_seed": int(n_boot),
        "resample_signature": signature,
        "ladder": ladder,
    }


def replicate_sensitivity_ladder(
    returns: np.ndarray,
    timestamps: np.ndarray,
    *,
    n_boot: int = LADDER_PLANT_N,
    clock: str = "H1",
    rungs: tuple[float, ...] = LADDER_RUNGS,
    calendar_start_ns: int | None = None,
    calendar_end_ns: int | None = None,
) -> dict:
    """Detection curves from planted effects on each bootstrap replicate."""
    ts = np.asarray(timestamps, dtype=np.int64)
    idx, starts = day_index(
        ts,
        calendar_start_ns=calendar_start_ns,
        calendar_end_ns=calendar_end_ns,
    )
    suff = day_sufficient(np.asarray(returns, dtype=float), idx, len(starts))
    base_values: list[np.ndarray] = []
    planted_wl: dict[str, list[np.ndarray]] = {str(d): [] for d in rungs}
    planted_p: dict[str, list[np.ndarray]] = {str(d): [] for d in rungs}
    for block in block_days_for_clock(clock):
        for seed in BOOT_SEEDS:
            sample_idx = _resample_day_blocks(len(starts), block, n_boot, seed)
            totals = suff[sample_idx].sum(axis=1)
            base = _logR_from_totals(totals)
            base_values.append(base)
            for delta in rungs:
                wl_totals = totals.copy()
                wl_totals[:, 3] *= np.exp(delta)
                planted_wl[str(delta)].append(_logR_from_totals(wl_totals))

                p_totals = totals.copy()
                n_signed = p_totals[:, 2] + p_totals[:, 4]
                with np.errstate(divide="ignore", invalid="ignore"):
                    p0 = p_totals[:, 2] / n_signed
                    odds = ((1 - p0) / p0) * np.exp(-delta)
                    p1 = 1 / (1 + odds)
                p_totals[:, 2] = n_signed * p1
                p_totals[:, 4] = n_signed * (1 - p1)
                planted_p[str(delta)].append(_logR_from_totals(p_totals))
    base_all = np.concatenate(base_values)
    threshold = float(np.nanquantile(base_all, 1 - BOOT_CI_ALPHA / 2))

    def rates(values: dict[str, list[np.ndarray]]) -> dict[str, float]:
        return {
            rung: float(np.nanmean(np.concatenate(parts) > threshold))
            for rung, parts in values.items()
        }

    return {
        "via_WL": rates(planted_wl),
        "via_p": rates(planted_p),
        "n_boot_replicates": int(np.isfinite(base_all).sum()),
        "requested_replicates_per_seed": int(n_boot),
        "detection_reference": "upper_95pct_unplanted_bootstrap",
    }


def block_days_for_clock(clock: str) -> tuple[int, ...]:
    if clock == "H4":
        return BOOT_BLOCKS_DAYS_H4
    return BOOT_BLOCKS_DAYS_H1


def envelope_ci_logR(
    suff: np.ndarray,
    *,
    n_boot: int = BOOT_RESAMPLES,
    clock: str = "H1",
) -> dict:
    n_days = suff.shape[0]
    point_a = _agg(suff)
    point = log_R_from_pWL(point_a["p"], point_a["W"], point_a["L"])
    blocks = block_days_for_clock(clock)
    if n_days < 2:
        return {
            "stat": float(point), "ci_low": float("nan"), "ci_high": float("nan"),
            "n_days": int(n_days), "per_block": [], "per_seed": [], "degenerate": True,
            "blocks_days": list(blocks),
        }
    lows, highs = [], []
    per_block, per_seed = [], []
    for bl in blocks:
        eff = max(1, min(int(bl), n_days - 1))
        seed_lo, seed_hi = [], []
        for seed in BOOT_SEEDS:
            stats = _logR_boot_stats(suff, bl, n_boot, seed)
            v = stats[np.isfinite(stats)]
            if v.size == 0:
                continue
            lo = float(np.quantile(v, BOOT_CI_ALPHA / 2))
            hi = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
            seed_lo.append(lo)
            seed_hi.append(hi)
            per_seed.append({
                "block_days": int(bl), "seed": int(seed),
                "ci_low": lo, "ci_high": hi,
            })
        if seed_lo:
            lows += seed_lo
            highs += seed_hi
            per_block.append({
                "block_days": int(bl), "effective_block": eff,
                "ci": [float(np.median(seed_lo)), float(np.median(seed_hi))],
            })
    return {
        "stat": float(point),
        "ci_low": float(min(lows)) if lows else float("nan"),
        "ci_high": float(max(highs)) if highs else float("nan"),
        "n_days": int(n_days),
        "per_block": per_block,
        "per_seed": per_seed,
        "degenerate": False,
        "blocks_days": list(blocks),
        "envelope_rule": f"min/max over blocks {list(blocks)} days x 5 seeds",
    }


def assert_canonical_equivalence(
    suff: np.ndarray, *, block: int = 3, n_boot: int = 500, tol: float = 1e-9
) -> dict:
    def stat(s: np.ndarray) -> float:
        a = _agg(np.atleast_2d(s))
        return log_R_from_pWL(a["p"], a["W"], a["L"])

    canon = block_bootstrap_ci(
        suff, stat, block=block, n_boot=n_boot, alpha=BOOT_CI_ALPHA,
        seed=BOOT_SEEDS[0], n_seeds=1,
    )
    fast = _logR_boot_stats(suff, block, n_boot, BOOT_SEEDS[0])
    v = fast[np.isfinite(fast)]
    lo = float(np.quantile(v, BOOT_CI_ALPHA / 2))
    hi = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
    d_lo = abs(lo - canon["ci"][0])
    d_hi = abs(hi - canon["ci"][1])
    return {
        "statistic": "log_R", "block": block, "n_boot": n_boot,
        "canonical_ci": [float(canon["ci"][0]), float(canon["ci"][1])],
        "vectorised_ci": [lo, hi], "abs_diff": [d_lo, d_hi], "tol": tol,
        "equivalent": bool(d_lo <= tol and d_hi <= tol),
    }


def block_mde(ci: dict) -> float:
    if not np.isfinite(ci.get("stat", np.nan)) or not np.isfinite(ci.get("ci_low", np.nan)):
        return float("nan")
    return float(ci["stat"] - ci["ci_low"])


def iid_mde_companion(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    n = r.size
    if n < 2:
        return float("nan")
    return float(IID_MDE_CONST * np.std(r, ddof=1) / np.sqrt(n))


def cell_metrics(
    r: np.ndarray,
    ts_ns: np.ndarray,
    *,
    n_boot: int = BOOT_RESAMPLES,
    cost_bps: float = COST_FLOOR_BPS,
    clock: str = "H1",
    calendar_start_ns: int | None = None,
    calendar_end_ns: int | None = None,
) -> dict:
    r = np.asarray(r, dtype=float)
    ok = np.isfinite(r)
    r = r[ok]
    ts = np.asarray(ts_ns, dtype=np.int64)[ok]
    out: dict = {"n": int(r.size), "cost_bps_DISCLOSURE_ONLY": float(cost_bps), "clock": clock}
    if r.size == 0:
        out.update({
            "empty": True, "log_R": float("nan"), "ci_low": float("nan"),
            "ci_high": float("nan"), "ci_width": float("nan"), "block_mde": float("nan"),
            "mde50": float("nan"), "mde80": float("nan"), "mde95": float("nan"),
        })
        return out

    day_idx, day_starts = day_index(
        ts,
        calendar_start_ns=calendar_start_ns,
        calendar_end_ns=calendar_end_ns,
    )
    n_days = int(day_starts.size)
    suff = day_sufficient(r, day_idx, n_days)
    base = _agg(suff)
    out.update(base)
    out["n_dates"] = n_days

    p, W, L = base["p"], base["W"], base["L"]
    denom = W + L if np.isfinite(W) and np.isfinite(L) else float("nan")
    out["W_L"] = float(W / L) if (np.isfinite(L) and L > 0) else float("nan")
    out["p_be"] = float(L / denom) if (np.isfinite(denom) and denom > 0) else float("nan")
    out["p_be_net"] = (
        float((L + cost_bps) / denom) if (np.isfinite(denom) and denom > 0) else float("nan")
    )
    out["p_be_net_flag"] = "DISCLOSURE_ONLY"
    out["log_R"] = log_R_from_pWL(p, W, L)

    # identity on non-flat rows (deadband)
    signed = np.abs(r) > DEADBAND_BPS
    signed_mean = float(r[signed].mean()) if signed.any() else float("nan")
    recon = (p * W - (1.0 - p) * L) if all(np.isfinite([p, W, L])) else float("nan")
    out["identity_residual_bps"] = (
        abs(recon - signed_mean) if np.isfinite(recon) and np.isfinite(signed_mean) else float("nan")
    )
    out["identity_tol_bps"] = IDENTITY_RECONSTRUCTION_TOL_BPS
    out["mean_signed_rows"] = signed_mean

    ci = envelope_ci_logR(suff, n_boot=n_boot, clock=clock)
    out["ci_low"] = ci["ci_low"]
    out["ci_high"] = ci["ci_high"]
    out["ci_width"] = (
        float(ci["ci_high"] - ci["ci_low"])
        if np.isfinite(ci["ci_low"]) and np.isfinite(ci["ci_high"]) else float("nan")
    )
    out["block_mde"] = block_mde(ci)
    out["iid_mde_log__COMPANION_ONLY"] = (
        iid_mde_companion(r) / max((1 - p) * L, 1e-12)
        if all(np.isfinite([p, L])) else float("nan")
    )
    out["mde_source_for_bands"] = "block"
    out["blocks_days"] = ci.get("blocks_days")
    out["n_days"] = n_days

    mde = out["block_mde"]
    out["realised_c"] = float(mde * np.sqrt(r.size)) if np.isfinite(mde) and r.size else float("nan")
    out["effective_n"] = float(r.size)

    if np.isfinite(out["ci_low"]) and out["ci_low"] > 0:
        out["band_label"] = "ABOVE_THE_MIRROR"
    elif np.isfinite(out["ci_high"]) and out["ci_high"] < 0:
        out["band_label"] = "BELOW_THE_MIRROR"
    else:
        out["band_label"] = "COVERS_THE_MIRROR"

    half = out["block_mde"]
    rates_wl, rates_p, req_n = {}, {}, {}
    if np.isfinite(half):
        se = half / 1.96
        planted = replicate_sensitivity_ladder(
            r,
            ts,
            n_boot=n_boot,
            clock=clock,
            calendar_start_ns=calendar_start_ns,
            calendar_end_ns=calendar_end_ns,
        )
        for delta in LADDER_RUNGS:
            rates_wl[str(delta)] = planted["via_WL"][str(delta)]
            rates_p[str(delta)] = planted["via_p"][str(delta)]
            req_n[str(delta)] = (
                float(np.ceil(r.size * (half / delta) ** 2))
                if delta > 0 and r.size else float("nan")
            )
        out["mde50"] = float((0.0 + 1.96) * se)
        out["mde80"] = float((0.841621 + 1.96) * se)
        out["mde95"] = float((1.644854 + 1.96) * se)
    else:
        out["mde50"] = out["mde80"] = out["mde95"] = float("nan")
    out["ladder"] = {
        "ladder_rungs": list(LADDER_RUNGS),
        "detect_rate_via_WL": rates_wl,
        "detect_rate_via_p": rates_p,
        "required_n_via_WL": req_n,
        "plant_bootstrap_replicates": (
            planted["n_boot_replicates"] if np.isfinite(half) else 0
        ),
        "plant_bootstrap_replicates_per_seed": (
            planted["requested_replicates_per_seed"] if np.isfinite(half) else 0
        ),
    }
    for k, v in rates_wl.items():
        out[f"detect_wl_{k}"] = v
    for k, v in rates_p.items():
        out[f"detect_p_{k}"] = v
    out["kappa"] = float("nan")
    return out


def span_stats(entry_ts: np.ndarray, exit_ts: np.ndarray, h_hours: float) -> dict:
    e = np.asarray(entry_ts, dtype=np.int64)
    x = np.asarray(exit_ts, dtype=np.int64)
    if e.size == 0:
        return {"span_exact_frac": float("nan"), "span_p50": float("nan"), "span_p90": float("nan")}
    span_h = (x - e) / (3600 * NS)
    exact = np.isclose(span_h, h_hours, rtol=0, atol=h_hours * 0.05 + 1e-9)
    return {
        "span_exact_frac": float(exact.mean()),
        "span_p50": float(np.median(span_h)),
        "span_p90": float(np.percentile(span_h, 90)),
    }


def effective_coverage(ts_ns: np.ndarray, symbols: np.ndarray) -> dict:
    ts = np.asarray(ts_ns, dtype=np.int64)
    syms = np.asarray(symbols)
    if ts.size == 0:
        return {
            "n": 0, "n_symbols": 0, "effective_frac_of_nominal": float("nan"),
            "zvol_covered_n_asserted": ZVOL_COVERED_N,
        }
    nominal_days = float((ts.max() - ts.min()) / DAY_NS)
    multi = ts >= EFFECTIVE_COVERAGE_START_NS
    eff_days = float((ts[multi].max() - ts[multi].min()) / DAY_NS) if multi.any() else 0.0
    return {
        "n": int(ts.size),
        "n_symbols": int(len(np.unique(syms))),
        "nominal_days": nominal_days,
        "effective_multi_symbol_days": eff_days,
        "effective_frac_of_nominal": (eff_days / nominal_days) if nominal_days > 0 else float("nan"),
        "zvol_covered_n_asserted": ZVOL_COVERED_N,
    }


def delta_logR(cell_a: dict, cell_b: dict) -> dict:
    la = cell_a.get("log_R", float("nan"))
    lb = cell_b.get("log_R", float("nan"))
    d = la - lb if np.isfinite(la) and np.isfinite(lb) else float("nan")
    wa = cell_a.get("ci_width", float("nan"))
    wb = cell_b.get("ci_width", float("nan"))
    half = 0.5 * (wa + wb) if np.isfinite(wa) and np.isfinite(wb) else float("nan")
    return {
        "delta_log_R": d,
        "ci_low": d - half if np.isfinite(d) and np.isfinite(half) else float("nan"),
        "ci_high": d + half if np.isfinite(d) and np.isfinite(half) else float("nan"),
        "ci_width": 2 * half if np.isfinite(half) else float("nan"),
        "block_mde": half if np.isfinite(half) else float("nan"),
    }
