"""Controls: mirror null (primary), side-derangement, timing, ambient, tripwires (design §6)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from config import (
    CONTROL_PRIMARY,
    DEADBAND_BPS,
    DERANGE_SEEDS,
    PLANT_CURVE_BPS,
    TIMING_SEEDS,
    DESIGN_START_NS,
    TRAIN_END_NS,
)
from metrics import cell_metrics, log_R_from_pWL, paired_delta_metrics

CONTROL_CELL_COLUMNS = (
    "symbol", "clock", "source", "z", "H", "event_type", "h", "policy", "band",
    "variant_id",
)

ACCOUNTABLE_CONTROL_STATUSES = frozenset({
    "USABLE", "UNUSABLE_THIN", "UNUSABLE_VACUOUS", "MISSING",
})


def control_cell_key(cell: dict) -> tuple:
    """Exact control-cell identity used for manifest reconciliation."""
    return tuple(cell.get(column) for column in CONTROL_CELL_COLUMNS)


def hold_bars_for_variant(variant_id: str) -> int | None:
    """Return the hold length for an L4_HOLD_* device, else None."""
    text = str(variant_id)
    if not text.startswith("L4_HOLD_"):
        return None
    body = text[len("L4_HOLD_"):]
    try:
        return int(body.split("_", 1)[0])
    except ValueError:
        return None


def expand_required_control_cells(
    episodes: pd.DataFrame,
    *,
    l4_variants: tuple[str, ...] | list[str],
) -> list[dict]:
    """Required control populations for the primary object and every L4 device.

    Permanent rule (design §6.1 L-24.2 + hold h-free grid):
    1. PRIMARY + residual-bound L4 (target/trail/size) inherit the primary residual `h`;
    2. HOLD devices are h-free: required `h` is the device's own hold length (4/12/24),
       never the residual primary horizon;
    3. every L4 cell that already exists in the emission is required too.
    Absence is labelled MISSING — never silently omitted from the manifest.
    """
    if episodes.empty:
        return []
    base_columns = [
        column for column in CONTROL_CELL_COLUMNS
        if column != "variant_id" and column in episodes.columns
    ]
    required_identity = ("symbol", "clock", "source", "event_type", "policy")
    if any(column not in episodes.columns for column in required_identity):
        return []
    primary = episodes.copy()
    for column, value in (
        ("clock", CONTROL_PRIMARY["clock"]),
        ("source", CONTROL_PRIMARY["source"]),
        ("event_type", CONTROL_PRIMARY["event_type"]),
        ("policy", CONTROL_PRIMARY["policy"]),
    ):
        primary = primary[primary[column] == value]
    if "z" in primary.columns:
        primary = primary[np.isclose(primary["z"].astype(float), CONTROL_PRIMARY["z"])]
    if "H" in primary.columns:
        primary = primary[primary["H"] == CONTROL_PRIMARY["H"]]
    # Residual-bound primary cells (L0 and non-hold L4) use the control primary h.
    residual_primary = primary
    if "h" in residual_primary.columns:
        residual_primary = residual_primary[
            residual_primary["h"] == CONTROL_PRIMARY["h"]
        ]
    required: list[dict] = []
    seen: set[tuple] = set()

    def _add(cell: dict) -> None:
        key = control_cell_key(cell)
        if key in seen:
            return
        seen.add(key)
        required.append(cell)

    hold_variants = [
        str(v) for v in l4_variants
        if str(v).startswith("L4_HOLD_") and hold_bars_for_variant(str(v)) is not None
    ]
    residual_l4_variants = [
        str(v) for v in l4_variants
        if str(v).startswith("L4_") and not str(v).startswith("L4_HOLD_")
    ]

    if not residual_primary.empty and base_columns:
        for cell_key, _ in residual_primary.groupby(base_columns, sort=True):
            if not isinstance(cell_key, tuple):
                cell_key = (cell_key,)
            base = dict(zip(base_columns, cell_key, strict=True))
            _add({**base, "variant_id": CONTROL_PRIMARY["variant_id"]})
            for variant_id in residual_l4_variants:
                _add({**base, "variant_id": variant_id})

    # HOLD devices: one cell per h-free base, with h = hold_bars (not residual h).
    hold_base_columns = [c for c in base_columns if c != "h"]
    hold_base_source = primary if not primary.empty else residual_primary
    if hold_variants and not hold_base_source.empty and hold_base_columns:
        for cell_key, _ in hold_base_source.groupby(hold_base_columns, sort=True):
            if not isinstance(cell_key, tuple):
                cell_key = (cell_key,)
            base = dict(zip(hold_base_columns, cell_key, strict=True))
            for variant_id in hold_variants:
                hold_h = hold_bars_for_variant(variant_id)
                if hold_h is None:
                    continue
                cell = {**base, "variant_id": variant_id}
                if "h" in CONTROL_CELL_COLUMNS:
                    cell["h"] = hold_h
                _add(cell)

    # Observed L4 populations outside the primary base still require controls.
    l4 = episodes[episodes["variant_id"].astype(str).str.startswith("L4_")]
    l4_columns = [c for c in CONTROL_CELL_COLUMNS if c in l4.columns]
    if not l4.empty and l4_columns:
        for cell_key, _ in l4.groupby(l4_columns, sort=True):
            if not isinstance(cell_key, tuple):
                cell_key = (cell_key,)
            _add(dict(zip(l4_columns, cell_key, strict=True)))
    return required


@dataclass(frozen=True)
class TripwireRun:
    conditioning: np.ndarray
    event_keys: set[tuple]
    returns: np.ndarray
    timestamps: np.ndarray


def derangement_permutation(size: int, *, seed: int) -> np.ndarray:
    """Return a seeded permutation with no row-identity fixed points."""
    if size < 2:
        raise ValueError("derangement needs at least two rows")
    rng = np.random.default_rng(seed)
    order = rng.permutation(size)
    shift = int(rng.integers(1, size))
    permutation = np.empty(size, dtype=np.int64)
    permutation[order] = np.roll(order, shift)
    if np.any(permutation == np.arange(size)):
        raise AssertionError("failed to construct row-identity derangement")
    return permutation


def derange_indices(values: np.ndarray, *, seed: int) -> np.ndarray:
    """Reassign values through a zero-row-fixed-point permutation."""
    values = np.asarray(values)
    return values[derangement_permutation(values.size, seed=seed)]


def derange_binary_sides(sides: np.ndarray) -> np.ndarray:
    sides = np.asarray(sides)
    if not np.all(np.isin(sides, (-1, 1))):
        raise ValueError("side derangement requires binary ±1 sides")
    return -sides


def _summary(r: np.ndarray) -> dict:
    r = np.asarray(r, dtype=float)
    pos = r > DEADBAND_BPS
    neg = r < -DEADBAND_BPS
    n = int(pos.sum() + neg.sum())
    p = float(pos.sum() / n) if n else float("nan")
    W = float(r[pos].mean()) if pos.any() else float("nan")
    L = float(-r[neg].mean()) if neg.any() else float("nan")
    return {
        "p": p,
        "W": W,
        "L": L,
        "W_L": W / L if np.isfinite(W) and np.isfinite(L) and L > 0 else float("nan"),
        "log_R": log_R_from_pWL(p, W, L),
        "mean": float(np.mean(r)) if r.size else float("nan"),
        "n": int(r.size),
    }


def _null_distribution_payload(
    null_returns: list[np.ndarray],
    *,
    live_log_r: float,
) -> dict:
    log_values = np.asarray(
        [_summary(values)["log_R"] for values in null_returns],
        dtype=float,
    )
    finite = log_values[np.isfinite(log_values)]
    all_returns = (
        np.concatenate(null_returns) if null_returns else np.empty(0, dtype=float)
    )
    sigma = (
        float(np.std(all_returns, ddof=1))
        if all_returns.size > 1
        else float("nan")
    )
    q95 = float(np.quantile(finite, 0.95)) if finite.size else float("nan")
    plant_curve = {}
    for bps in PLANT_CURVE_BPS:
        planted = np.asarray(
            [_summary(values + bps)["log_R"] for values in null_returns],
            dtype=float,
        )
        plant_curve[str(bps)] = {
            "detection_rate": (
                float(np.nanmean(planted > q95))
                if np.isfinite(q95)
                else float("nan")
            ),
            "sigma_units": bps / sigma if np.isfinite(sigma) and sigma > 0 else float("nan"),
        }
    return {
        "live_log_R": live_log_r,
        "null_mean": float(np.mean(finite)) if finite.size else float("nan"),
        "null_sd": float(np.std(finite, ddof=1)) if finite.size > 1 else float("nan"),
        "null_q05": float(np.quantile(finite, 0.05)) if finite.size else float("nan"),
        "null_q95": q95,
        "percentile": (
            float(np.mean(finite < live_log_r))
            if finite.size and np.isfinite(live_log_r)
            else float("nan")
        ),
        "plant_curve_bps": plant_curve,
        "sigma_bps_run_derived": sigma,
    }


def _paired_component_deltas(legal: TripwireRun, leaky: TripwireRun, *, n_boot: int) -> dict:
    a = _summary(leaky.returns)
    b = _summary(legal.returns)
    log_delta = paired_delta_metrics(
        leaky.returns,
        leaky.timestamps,
        legal.returns,
        legal.timestamps,
        n_boot=n_boot,
    )
    return {
        key: {
            "delta": float(a[key] - b[key])
            if np.isfinite(a[key]) and np.isfinite(b[key])
            else float("nan"),
            "ci_low": (
                log_delta["ci_low"] if key == "log_R" else float("nan")
            ),
            "ci_high": (
                log_delta["ci_high"] if key == "log_R" else float("nan")
            ),
        }
        for key in ("p", "W", "L", "log_R")
    }


def evaluate_tripwire_1(
    legal: TripwireRun,
    leaky: TripwireRun,
    *,
    n_boot: int = 200,
) -> dict:
    """Evaluate evidence from two independently rebuilt end-to-end runs."""
    n = min(legal.conditioning.size, leaky.conditioning.size)
    comparable = (
        np.isfinite(legal.conditioning[:n])
        & np.isfinite(leaky.conditioning[:n])
    )
    changed = int(np.sum(
        comparable
        & (legal.conditioning[:n] != leaky.conditioning[:n])
    ))
    symdiff = sorted(legal.event_keys ^ leaky.event_keys)
    return {
        "hard_pass": bool(changed > 0 and len(symdiff) > 0),
        "changed_conditioning_rows": changed,
        "event_key_symmetric_difference_count": len(symdiff),
        "event_key_symmetric_difference": [list(x) for x in symdiff],
        "paired_deltas": _paired_component_deltas(legal, leaky, n_boot=n_boot),
        "evidence_source": "independent_legal_and_t_plus_1_pipeline_runs",
    }


def evaluate_tripwire_2(
    event_index_pairs: list[dict],
    *,
    live_returns: np.ndarray,
    leaky_returns: np.ndarray,
    timestamps: np.ndarray,
    n_boot: int = 200,
    live_p_event: float | None = None,
    leaky_p_event: float | None = None,
    future_touch_zones: int | None = None,
) -> dict:
    valid = [
        p for p in event_index_pairs
        if p.get("leaky_event_idx") == p.get("anchor_idx")
        and p.get("leaky_event_idx") < p.get("legal_event_idx")
    ]
    legal = TripwireRun(
        np.empty(0),
        set(),
        np.asarray(live_returns, dtype=float),
        np.asarray(timestamps, dtype=np.int64),
    )
    leaky = TripwireRun(
        np.empty(0),
        set(),
        np.asarray(leaky_returns, dtype=float),
        np.asarray(timestamps, dtype=np.int64),
    )
    deltas = _paired_component_deltas(legal, leaky, n_boot=n_boot)
    deltas["p_event"] = {
        "delta": (
            float(leaky_p_event - live_p_event)
            if live_p_event is not None and leaky_p_event is not None
            else float("nan")
        ),
        "ci_low": float("nan"),
        "ci_high": float("nan"),
    }
    future_count = (
        int(future_touch_zones)
        if future_touch_zones is not None
        else len(event_index_pairs)
    )
    return {
        "hard_pass": bool(
            future_count > 0
            and event_index_pairs
            and len(valid) == len(event_index_pairs)
        ),
        "future_touch_zones": future_count,
        "early_entry_count": len(valid),
        "event_index_pairs": event_index_pairs,
        "paired_deltas": deltas,
        "all_early_have_leaky_at_anchor_before_legal": len(valid) == len(event_index_pairs),
    }


def entry_timing_control(
    episodes: pd.DataFrame,
    *,
    rerun: Callable[[pd.DataFrame, str], np.ndarray],
    exit_rule: str,
    seeds: tuple[int, ...],
) -> dict:
    """Derange entry timestamps and rerun the exact live fill/exit rule."""
    nulls = []
    null_returns = []
    changed = 0
    fixed = 0
    assignment_signatures = []
    for seed in seeds:
        frame = episodes.copy()
        original = frame["entry_idx"].to_numpy().copy()
        source_rows = np.arange(len(frame))
        permutation = derangement_permutation(len(frame), seed=seed)
        frame["entry_idx"] = original[permutation]
        frame["_control_source_row"] = source_rows[permutation]
        assignment_signatures.append(tuple(permutation.tolist()))
        changed += int(np.sum(frame["entry_idx"].to_numpy() != original))
        fixed += int(np.sum(permutation == source_rows))
        values = rerun(frame, exit_rule)
        null_returns.append(values)
        nulls.append(_summary(values))
    live_values = rerun(episodes.copy(), exit_rule)
    distribution = _null_distribution_payload(
        null_returns,
        live_log_r=_summary(live_values)["log_R"],
    )
    return {
        "control": "ENTRY_TIMING_DERANGEMENT",
        "exit_rule": exit_rule,
        "exit_matched": True,
        "reran_fills_and_exits": True,
        "n_seeds": len(seeds),
        "fixed_point_count": fixed,
        "changed_entry_count": changed,
        "unique_assignment_count": len(set(assignment_signatures)),
        "null_sufficient_statistics": nulls,
        **distribution,
    }


def side_label_control(
    episodes: pd.DataFrame,
    *,
    rerun: Callable[[pd.DataFrame, str], np.ndarray],
    exit_rule: str,
    seeds: tuple[int, ...],
) -> dict:
    """Derange side labels and rerun the signed return estimand."""
    nulls = []
    null_returns = []
    changed = 0
    fixed = 0
    assignment_signatures = []
    for seed in seeds:
        frame = episodes.copy()
        original = frame["side"].to_numpy()
        if not np.all(np.isin(original, (-1, 1))):
            raise ValueError("side derangement requires binary ±1 sides")
        permutation = derangement_permutation(len(frame), seed=seed)
        frame["side"] = original[permutation]
        frame["_control_source_row"] = permutation
        assignment_signatures.append(tuple(permutation.tolist()))
        changed += int(np.sum(frame["side"].to_numpy() != original))
        fixed += int(np.sum(permutation == np.arange(len(frame))))
        values = rerun(frame, exit_rule)
        null_returns.append(values)
        nulls.append(_summary(values))
    live_values = rerun(episodes.copy(), exit_rule)
    distribution = _null_distribution_payload(
        null_returns,
        live_log_r=_summary(live_values)["log_R"],
    )
    return {
        "control": "SIDE_DERANGEMENT",
        "exit_rule": exit_rule,
        "exit_matched": True,
        "reran_signed_estimand": True,
        "n_seeds": len(seeds),
        "fixed_point_count": fixed,
        "changed_side_count": changed,
        "fixed_point_definition": "source_row_identity",
        "unique_assignment_count": len(set(assignment_signatures)),
        "null_sufficient_statistics": nulls,
        **distribution,
    }


def ambient_base_control(episodes: pd.DataFrame) -> dict:
    event = episodes[episodes["is_breach"].astype(bool)]
    ambient = episodes[~episodes["is_breach"].astype(bool)]
    event_keys = set(event["event_key"])
    ambient_keys = set(ambient["event_key"])
    return {
        "control": "AMBIENT_BASE",
        "disjoint": event_keys.isdisjoint(ambient_keys),
        "n_event": len(event),
        "n_control": len(ambient),
        "event": _summary(event["r_bps"].to_numpy(dtype=float)),
        "comparator": _summary(ambient["r_bps"].to_numpy(dtype=float)),
    }


def magnitude_matched_control(
    episodes: pd.DataFrame,
    *,
    seeds: tuple[int, ...] = DERANGE_SEEDS,
) -> dict:
    rows = []
    disjoint = True
    for decile, group in episodes.groupby("move_decile", sort=True):
        selected = group[group["selected"].astype(bool)]
        comparator = group[~group["selected"].astype(bool)]
        sel_keys = set(selected["event_key"])
        comp_keys = set(comparator["event_key"])
        disjoint = disjoint and sel_keys.isdisjoint(comp_keys)
        rows.append({
            "move_decile": int(decile),
            "n_selected": len(selected),
            "n_comparator": len(comparator),
            "selected": _summary(selected["r_bps"].to_numpy(dtype=float)),
            "comparator": _summary(comparator["r_bps"].to_numpy(dtype=float)),
            **_magnitude_null(group, seeds=seeds),
        })
    return {
        "control": "MAGNITUDE_MATCHED",
        "disjoint_per_decile": disjoint,
        "deciles": rows,
    }


def _magnitude_null(group: pd.DataFrame, *, seeds: tuple[int, ...]) -> dict:
    values = group["r_bps"].to_numpy(dtype=float)
    n_selected = int(group["selected"].astype(bool).sum())
    null_returns = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        null_returns.append(values[rng.permutation(len(values))[:n_selected]])
    live = group.loc[group["selected"].astype(bool), "r_bps"].to_numpy(dtype=float)
    return _null_distribution_payload(
        null_returns,
        live_log_r=_summary(live)["log_R"],
    )


def chronological_thirds_control(episodes: pd.DataFrame) -> dict:
    """Report the primary-cell result independently in chronological thirds."""
    boundaries = np.linspace(DESIGN_START_NS, TRAIN_END_NS, 4, dtype=np.int64)
    full = _summary(episodes["r_bps"].to_numpy(dtype=float))
    full_sign = int(np.sign(full["log_R"])) if np.isfinite(full["log_R"]) else 0
    rows = []
    for third in range(3):
        lo = int(boundaries[third])
        hi = int(boundaries[third + 1])
        mask = (episodes["entry_ts"] >= lo) & (episodes["entry_ts"] < hi)
        summary = _summary(episodes.loc[mask, "r_bps"].to_numpy(dtype=float))
        third_sign = (
            int(np.sign(summary["log_R"]))
            if np.isfinite(summary["log_R"]) else 0
        )
        rows.append({
            "third": third + 1,
            "interval_start_ns": lo,
            "interval_end_ns": hi,
            "agrees_with_full_sign": bool(
                full_sign != 0 and third_sign == full_sign
            ),
            **summary,
        })
    return {
        "control": "CHRONOLOGICAL_THIRDS",
        "interval_start_ns": DESIGN_START_NS,
        "interval_end_ns": TRAIN_END_NS,
        "split_rule": "equal_full_TRAIN_timestamp_intervals",
        "full_log_R_sign": full_sign,
        "sign_agreement": bool(
            full_sign != 0 and all(row["agrees_with_full_sign"] for row in rows)
        ),
        "thirds": rows,
    }


def _control_quality(result: dict, *, changed_field: str) -> dict:
    plant_curve = result.get("plant_curve_bps", {})
    finite_plants = sum(
        1
        for row in plant_curve.values()
        if np.isfinite(row.get("detection_rate", float("nan")))
    )
    unique = int(result.get("unique_assignment_count", 0))
    changed = int(result.get(changed_field, 0))
    null_sd = float(result.get("null_sd", float("nan")))
    usable = bool(
        int(result.get("n_seeds", 0)) > 1
        and unique > 1
        and changed > 0
        and np.isfinite(null_sd)
        and null_sd > 0
        and finite_plants == len(plant_curve)
        and finite_plants > 0
    )
    return {
        "usable": usable,
        "unique_assignment_count": unique,
        "changed_input_count": changed,
        "null_sd": null_sd,
        "finite_plant_rungs": finite_plants,
        "total_plant_rungs": len(plant_curve),
    }


def _audited_control_cell(
    arm: pd.DataFrame,
    *,
    cell: dict,
    exit_rule: str,
    rerun: Callable[[pd.DataFrame, str], np.ndarray],
    seeds: tuple[int, ...],
) -> dict:
    if len(arm) < 2:
        return {
            "cell": cell,
            "population_n": int(len(arm)),
            "status": "UNUSABLE_THIN",
            "usable": False,
            "reason": "derangement_requires_at_least_two_rows",
            "plant_resolution": {
                "timing": None,
                "side": None,
                "reason": "not_estimable_on_thin_population",
            },
        }
    timing = entry_timing_control(
        arm, rerun=rerun, exit_rule=exit_rule, seeds=seeds,
    )
    side = side_label_control(
        arm, rerun=rerun, exit_rule=exit_rule, seeds=seeds,
    )
    timing_quality = _control_quality(
        timing, changed_field="changed_entry_count",
    )
    side_quality = _control_quality(side, changed_field="changed_side_count")
    usable = timing_quality["usable"] and side_quality["usable"]
    return {
        "cell": cell,
        "population_n": int(len(arm)),
        "status": "USABLE" if usable else "UNUSABLE_VACUOUS",
        "usable": usable,
        "timing": timing,
        "side": side,
        "plant_resolution": {
            "timing": timing_quality,
            "side": side_quality,
        },
    }


def _logR(r: np.ndarray) -> float:
    r = r[np.isfinite(r)]
    if r.size == 0:
        return float("nan")
    pos = r > DEADBAND_BPS
    neg = r < -DEADBAND_BPS
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    p = n_pos / (n_pos + n_neg)
    W = float(r[pos].mean())
    L = float(-r[neg].mean())
    return log_R_from_pWL(p, W, L)


def side_derangement(r: np.ndarray, ts: np.ndarray, *, n_seeds: int = 2000) -> dict:
    """Flip every side (negate r); zero fixed points. ≥2000 seeds via sign RNG on ties only.

    Live sides are fully flipped (destroy form DERANGEMENT). Plant curve co-reported.
    """
    r = np.asarray(r, dtype=float)
    live = _logR(r)
    # full flip is deterministic; seed battery randomizes which subset of flips if needed
    # design: every episode's side differs — pure negate has zero fixed points
    null_r = -r
    null_logR = _logR(null_r)
    # seed battery: random re-label half? No — derange means all sides flipped is one derangement;
    # additional seeds: random signs with zero fixed points (forced flip)
    null_vals = []
    for i, seed in enumerate(DERANGE_SEEDS[:n_seeds]):
        rng = np.random.default_rng(seed)
        # random signs forced different from live
        live_sign = np.sign(r)
        live_sign = np.where(live_sign == 0, 1.0, live_sign)
        # forced opposite
        forced = -live_sign
        # optional: reshuffle magnitudes across episodes preserving forced sign
        idx = rng.permutation(r.size)
        null_vals.append(_logR(np.abs(r[idx]) * forced))
    null_vals = np.array(null_vals, dtype=float)
    null_vals = null_vals[np.isfinite(null_vals)]
    pct = float((null_vals < live).mean()) if null_vals.size and np.isfinite(live) else float("nan")
    plant = {}
    for bps in PLANT_CURVE_BPS:
        planted = live + (bps / 100.0)  # rough residual plant for disclosure
        plant[str(bps)] = {
            "detection_rate": float((null_vals < planted).mean()) if null_vals.size else float("nan"),
        }
    return {
        "control": "SIDE_DERANGEMENT",
        "live_log_R": live,
        "null_mean": float(null_vals.mean()) if null_vals.size else float("nan"),
        "null_sd": float(null_vals.std(ddof=1)) if null_vals.size > 1 else float("nan"),
        "null_q05": float(np.quantile(null_vals, 0.05)) if null_vals.size else float("nan"),
        "null_q95": float(np.quantile(null_vals, 0.95)) if null_vals.size else float("nan"),
        "percentile": pct,
        "fixed_point_count": 0,  # forced opposite signs
        "fixed_point_asserted_zero": True,
        "n_seeds": int(null_vals.size),
        "plant_curve_bps": plant,
        "pure_negate_log_R": null_logR,
        "collapse_fraction_DISCLOSURE_ONLY": (
            float(abs(live - null_logR) / max(abs(live), 1e-12))
            if np.isfinite(live) and np.isfinite(null_logR) else float("nan")
        ),
    }


def entry_timing_derangement(r: np.ndarray, ts: np.ndarray, *, n_seeds: int = 2000) -> dict:
    r = np.asarray(r, dtype=float)
    ts = np.asarray(ts, dtype=np.int64)
    live = _logR(r)
    null_vals = []
    for seed in TIMING_SEEDS[:n_seeds]:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(r.size)
        # derange: zero fixed points
        if r.size > 1 and np.any(idx == np.arange(r.size)):
            # force derangement via cycle
            idx = np.roll(np.arange(r.size), 1)
        null_vals.append(_logR(r[idx]))
    null_vals = np.array([v for v in null_vals if np.isfinite(v)], dtype=float)
    pct = float((null_vals < live).mean()) if null_vals.size and np.isfinite(live) else float("nan")
    return {
        "control": "ENTRY_TIMING_DERANGEMENT",
        "live_log_R": live,
        "null_mean": float(null_vals.mean()) if null_vals.size else float("nan"),
        "null_sd": float(null_vals.std(ddof=1)) if null_vals.size > 1 else float("nan"),
        "null_q05": float(np.quantile(null_vals, 0.05)) if null_vals.size else float("nan"),
        "null_q95": float(np.quantile(null_vals, 0.95)) if null_vals.size else float("nan"),
        "percentile": pct,
        "fixed_point_count": 0,
        "n_seeds": int(null_vals.size),
        "collapse_fraction_DISCLOSURE_ONLY": float("nan"),
    }


def _arm_for_cell(episodes: pd.DataFrame, cell: dict) -> pd.DataFrame:
    arm = episodes
    for column in CONTROL_CELL_COLUMNS:
        value = cell.get(column)
        if column not in arm.columns:
            return arm.iloc[0:0]
        if isinstance(value, float):
            arm = arm[np.isclose(arm[column].astype(float), float(value))]
        else:
            arm = arm[arm[column] == value]
    return arm


def run_primary_controls(
    episodes: pd.DataFrame,
    *,
    n_boot: int = 500,
    rerun: Callable[[pd.DataFrame, str], np.ndarray] | None = None,
    ambient_candidates: pd.DataFrame | None = None,
    magnitude_candidates: pd.DataFrame | None = None,
    seeds: tuple[int, ...] = TIMING_SEEDS,
    required_cells: list[dict] | None = None,
    l4_variants: tuple[str, ...] | list[str] | None = None,
) -> dict:
    """Controls on the primary L0 cell (design CONTROL_PRIMARY)."""
    if episodes.empty:
        return {"status": "EMPTY"}
    if "suppressed" in episodes.columns:
        episodes = episodes[~episodes["suppressed"].fillna(False).astype(bool)].copy()
    cp = CONTROL_PRIMARY
    m = episodes.copy()
    for col, val in (
        ("variant_id", cp["variant_id"]),
        ("clock", cp["clock"]),
        ("source", cp["source"]),
        ("event_type", cp["event_type"]),
        ("policy", cp["policy"]),
    ):
        if col in m.columns:
            m = m[m[col] == val]
    if "z" in m.columns:
        m = m[np.isclose(m["z"].astype(float), cp["z"])]
    if "h" in m.columns:
        m = m[m["h"] == cp["h"]]
    if "H" in m.columns:
        m = m[m["H"] == cp["H"]]
    if m.empty or rerun is None or ambient_candidates is None or magnitude_candidates is None:
        return {
            "status": "INCOMPLETE",
            "all_mandatory_controls_present": False,
            "missing": [
                name
                for name, value in (
                    ("primary_cell", not m.empty),
                    ("rerun", rerun is not None),
                    ("ambient_candidates", ambient_candidates is not None),
                    ("magnitude_candidates", magnitude_candidates is not None),
                )
                if not value
            ],
        }

    mirror_population = (
        m[m["band"] == "CONFIRM"] if "band" in m.columns else m
    )
    r = mirror_population["r_bps"].to_numpy(dtype=float)
    ts = mirror_population["entry_ts"].to_numpy(dtype=np.int64)
    live = cell_metrics(r, ts, n_boot=n_boot, clock="H1")

    if required_cells is None:
        if l4_variants is None:
            l4_variants = sorted({
                str(v) for v in episodes["variant_id"].astype(str)
                if str(v).startswith("L4_")
            })
        required_cells = expand_required_control_cells(
            episodes, l4_variants=tuple(l4_variants),
        )

    required_by_family: dict[str, list[dict]] = {
        "PRIMARY": [],
        "L4_EXIT_MATCHED": [],
    }
    for cell in required_cells:
        family = (
            "L4_EXIT_MATCHED"
            if str(cell.get("variant_id", "")).startswith("L4_")
            else "PRIMARY"
        )
        required_by_family[family].append(dict(cell))

    primary_cells = []
    for cell in required_by_family["PRIMARY"]:
        arm = _arm_for_cell(episodes, cell)
        if arm.empty:
            primary_cells.append({
                "cell": cell,
                "population_n": 0,
                "status": "MISSING",
                "usable": False,
                "plant_resolution": {
                    "timing": None,
                    "side": None,
                    "reason": "required_primary_cell_absent_from_emission",
                },
            })
            continue
        primary_cells.append(
            _audited_control_cell(
                arm,
                cell=cell,
                exit_rule="L0_BASELINE",
                rerun=rerun,
                seeds=seeds,
            )
        )
    timing = {
        "control": "ENTRY_TIMING_DERANGEMENT",
        "cells": [
            row["timing"] | {"cell": row["cell"]}
            for row in primary_cells if row.get("timing")
        ],
        "fixed_point_count": sum(
            row["timing"]["fixed_point_count"]
            for row in primary_cells if row.get("timing")
        ),
    }
    side = {
        "control": "SIDE_DERANGEMENT",
        "cells": [
            row["side"] | {"cell": row["cell"]}
            for row in primary_cells if row.get("side")
        ],
        "fixed_point_count": sum(
            row["side"]["fixed_point_count"]
            for row in primary_cells if row.get("side")
        ),
    }
    ambient = ambient_base_control(ambient_candidates)
    magnitude = magnitude_matched_control(magnitude_candidates, seeds=seeds)
    chronological_group_columns = [
        column for column in CONTROL_CELL_COLUMNS
        if column != "band" and column in episodes.columns
    ]
    chronological_cells = []
    chronological_population = pd.concat(
        [m, episodes[episodes["variant_id"].astype(str).str.startswith("L4_")]],
        ignore_index=True,
    )
    if chronological_group_columns and not chronological_population.empty:
        for cell_key, arm in chronological_population.groupby(
            chronological_group_columns, sort=True,
        ):
            if not isinstance(cell_key, tuple):
                cell_key = (cell_key,)
            cell = dict(zip(chronological_group_columns, cell_key, strict=True))
            chronological_cells.append(
                chronological_thirds_control(arm) | {"cell": cell}
            )
    chronological = {
        "control": "CHRONOLOGICAL_THIRDS",
        "cells": chronological_cells,
        "cell_count": len(chronological_cells),
        "full_train_interval": [DESIGN_START_NS, TRAIN_END_NS],
        "split_rule": "equal_full_TRAIN_timestamp_intervals",
    }
    exit_matched = []
    missing_cell_columns = set(CONTROL_CELL_COLUMNS) - set(episodes.columns)
    if missing_cell_columns and required_by_family["L4_EXIT_MATCHED"]:
        raise ValueError(
            f"L4 controls missing exact-cell columns: {sorted(missing_cell_columns)}"
        )
    for cell in required_by_family["L4_EXIT_MATCHED"]:
        variant_id = str(cell["variant_id"])
        arm = _arm_for_cell(episodes, cell)
        if arm.empty:
            exit_matched.append({
                "cell": cell,
                "variant_id": variant_id,
                "population_n": 0,
                "status": "MISSING",
                "usable": False,
                "plant_resolution": {
                    "timing": None,
                    "side": None,
                    "reason": "required_l4_cell_absent_from_emission",
                },
            })
            continue
        audited = _audited_control_cell(
            arm,
            cell=cell,
            exit_rule=variant_id,
            rerun=rerun,
            seeds=seeds,
        )
        audited["variant_id"] = variant_id
        exit_matched.append(audited)
    control_manifest = [
        {
            "family": "PRIMARY",
            "cell": row["cell"],
            "population_n": row["population_n"],
            "status": row["status"],
            "usable": row["usable"],
            "plant_resolution": row["plant_resolution"],
        }
        for row in primary_cells
    ] + [
        {
            "family": "L4_EXIT_MATCHED",
            "cell": row["cell"],
            "population_n": row["population_n"],
            "status": row["status"],
            "usable": row["usable"],
            "plant_resolution": row["plant_resolution"],
        }
        for row in exit_matched
    ]
    required_control_keys = {
        (
            "PRIMARY" if not str(cell.get("variant_id", "")).startswith("L4_")
            else "L4_EXIT_MATCHED",
            *control_cell_key(cell),
        )
        for cell in required_cells
    }
    emitted_control_keys = {
        (
            row["family"],
            *control_cell_key(row["cell"]),
        )
        for row in control_manifest
    }
    missing_control_keys = sorted(
        required_control_keys - emitted_control_keys,
        key=str,
    )
    extra_control_keys = sorted(
        emitted_control_keys - required_control_keys,
        key=str,
    )
    missing_labelled = [
        row for row in control_manifest if row["status"] == "MISSING"
    ]
    control_manifest_complete = bool(
        control_manifest
        and not missing_control_keys
        and not extra_control_keys
    )
    all_controls_usable = bool(
        control_manifest_complete
        and all(row["usable"] for row in control_manifest)
        and not missing_labelled
    )
    all_controls_accounted_for = bool(
        control_manifest_complete
        and all(
            row["status"] in ACCOUNTABLE_CONTROL_STATUSES
            and row.get("plant_resolution") is not None
            for row in control_manifest
        )
    )
    return {
        "primary_cell": cp,
        "mirror_null": {
            "control": "MIRROR_NULL",
            "log_R": live.get("log_R"),
            "ci_low": live.get("ci_low"),
            "ci_high": live.get("ci_high"),
            "null_reference": 0.0,
            "slope": 1.0,
            "n": live.get("n"),
            "cell": {
                **cp,
                "band": "CONFIRM",
                "scope": "POOLED",
            },
        },
        "side_derangement": side,
        "entry_timing_derangement": timing,
        "ambient_base": ambient,
        "magnitude_matched": magnitude,
        "chronological_thirds": chronological,
        "exit_matched_controls": exit_matched,
        "control_manifest": control_manifest,
        "required_control_cell_count": len(required_control_keys),
        "emitted_control_cell_count": len(emitted_control_keys),
        "missing_control_cells": [list(key) for key in missing_control_keys],
        "extra_control_cells": [list(key) for key in extra_control_keys],
        "missing_labelled_cells": [
            {"family": row["family"], "cell": row["cell"]}
            for row in missing_labelled
        ],
        "control_manifest_complete": control_manifest_complete,
        "all_control_cells_usable": all_controls_usable,
        "all_mandatory_controls_present": all_controls_accounted_for,
        "fixed_point_total": int(side.get("fixed_point_count", 0))
        + int(timing.get("fixed_point_count", 0)),
    }


def tripwire_1_structural(pack_state_legal: np.ndarray, pack_state_leaky: np.ndarray) -> dict:
    """TRIPWIRE-1: rebuild conditioning from t+1. HARD PASS on row + key diffs."""
    legal = np.asarray(pack_state_legal, dtype=float)
    leaky = np.asarray(pack_state_leaky, dtype=float)
    n = min(legal.size, leaky.size)
    if n == 0:
        return {"hard_pass": False, "changed_conditioning_rows": 0, "event_key_symmetric_difference_count": 0}
    legal, leaky = legal[:n], leaky[:n]
    both = np.isfinite(legal) & np.isfinite(leaky)
    changed = int(np.sum(both & (legal != leaky)))
    # event-key proxy: selection mask differs
    sel_l = (legal == 1).astype(int)
    sel_k = (leaky == 1).astype(int)
    symdiff = int(np.sum(sel_l != sel_k))
    return {
        "hard_pass": bool(changed > 0 and symdiff > 0),
        "changed_conditioning_rows": changed,
        "event_key_symmetric_difference_count": symdiff,
    }


def tripwire_2_structural(
    *,
    future_touch_zones: int,
    early_entry_count: int,
    all_early_have_leaky_lt_legal: bool,
) -> dict:
    """TRIPWIRE-2: look-ahead breach detector. HARD PASS on structural counts."""
    return {
        "hard_pass": bool(
            future_touch_zones > 0
            and early_entry_count > 0
            and all_early_have_leaky_lt_legal
        ),
        "future_touch_zones": int(future_touch_zones),
        "early_entry_count": int(early_entry_count),
        "all_early_have_leaky_lt_legal": bool(all_early_have_leaky_lt_legal),
    }
