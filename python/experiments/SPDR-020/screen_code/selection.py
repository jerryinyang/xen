"""L-51 three-number selection check (design §12). HARD on presence/form only."""
from __future__ import annotations

import numpy as np
import pandas as pd

CELL_COLUMNS = (
    "symbol", "clock", "source", "z", "H", "event_type", "h", "policy", "band",
)
IDENTITY_COLUMNS = ("event_key", "entry_ts")


def _three_numbers(selected: np.ndarray, complement: np.ndarray) -> dict:
    """Payoff-scale ratio, sign-share differential, excluded-set mean−median gap."""
    sel = selected[np.isfinite(selected)]
    comp = complement[np.isfinite(complement)]
    if sel.size == 0 or comp.size == 0:
        return {
            "payoff_scale_ratio": float("nan"),
            "sign_share_differential": float("nan"),
            "excluded_mean_minus_median": float("nan"),
            "n_selected": int(sel.size),
            "n_complement": int(comp.size),
        }
    scale_sel = float(np.median(np.abs(sel))) if sel.size else float("nan")
    scale_comp = float(np.median(np.abs(comp))) if comp.size else float("nan")
    ratio = scale_sel / scale_comp if scale_comp and np.isfinite(scale_comp) and scale_comp > 0 else float("nan")
    p_sel = float((sel > 0).mean())
    p_comp = float((comp > 0).mean())
    return {
        "payoff_scale_ratio": ratio,
        "sign_share_differential": p_sel - p_comp,
        "excluded_mean_minus_median": float(comp.mean() - np.median(comp)),
        "n_selected": int(sel.size),
        "n_complement": int(comp.size),
    }


def run_selection_checks(episodes: pd.DataFrame, metrics_df: pd.DataFrame) -> dict:
    """Emit L-51 rows for every selected subset the design reports separately."""
    rows = []
    if episodes.empty:
        return {"rows": [], "schema_ok": False, "note": "empty episodes"}

    required_columns = {*CELL_COLUMNS, "variant_id", "r_bps"}
    missing_columns = sorted(required_columns - set(episodes.columns))
    if missing_columns:
        return {
            "rows": [],
            "schema_ok": False,
            "note": f"missing exact-cell columns: {missing_columns}",
        }
    base = episodes[episodes["variant_id"] == "L0_BASELINE"]

    identity_columns = (
        ["event_key"] if "event_key" in episodes.columns
        else ["entry_ts"] if "entry_ts" in episodes.columns
        else []
    )
    if not identity_columns:
        return {
            "rows": [],
            "schema_ok": False,
            "note": "missing event identity column",
        }

    failures = []
    for vid, ckey in (
        ("L2_SHOCK_HMM", "L0_not_HMM_HIGH"),
        ("L2_LEVEL_RMARKOV_K4", "L0_not_k4_HIGH"),
        ("L2_LEVEL_RMARKOV_K12", "L0_not_k12_HIGH"),
        ("L2_JOINT_HMM_HIGH_AND_K12_HIGH", "L0_not_joint"),
        ("L3_TGTCUR_FIRES", "L0_tgtcur_off"),
    ):
        sel_eps = episodes[episodes["variant_id"] == vid]
        if sel_eps.empty:
            failures.append({"subset": vid, "reason": "required_subset_missing"})
            rows.append({
                "subset": vid,
                "complement_key": ckey,
                "cell": None,
                "disjoint": False,
                "exhaustive": False,
                "exact_cell_valid": False,
                **_three_numbers(np.array([]), np.array([])),
            })
            continue
        for cell_key, selected_cell in sel_eps.groupby(list(CELL_COLUMNS), sort=True):
            cell = dict(zip(CELL_COLUMNS, cell_key, strict=True))
            base_mask = pd.Series(True, index=base.index)
            for column, value in cell.items():
                if pd.isna(value):
                    base_mask &= base[column].isna()
                else:
                    base_mask &= base[column] == value
            base_cell = base[base_mask]
            selected_ids = set(map(
                tuple,
                selected_cell[identity_columns].itertuples(index=False, name=None),
            ))
            base_ids = base_cell[identity_columns].apply(tuple, axis=1)
            selected_base = base_cell[base_ids.isin(selected_ids)]
            complement = base_cell[~base_ids.isin(selected_ids)]
            valid = not base_cell.empty and not selected_base.empty and not complement.empty
            if not valid:
                failures.append({"subset": vid, "cell": cell})
            rows.append({
                "subset": vid,
                "complement_key": ckey,
                "cell": cell,
                "disjoint": bool(
                    set(selected_base.index).isdisjoint(complement.index)
                ),
                "exhaustive": (
                    len(selected_base) + len(complement) == len(base_cell)
                ),
                "exact_cell_valid": valid,
                **_three_numbers(
                    selected_base["r_bps"].to_numpy(dtype=float),
                    complement["r_bps"].to_numpy(dtype=float),
                ),
            })

    # Each event type against the other event types in its matching parent cell.
    event_parent_columns = [c for c in CELL_COLUMNS if c != "event_type"]
    for parent_key, parent in base.groupby(event_parent_columns, sort=True):
        parent_cell = dict(zip(event_parent_columns, parent_key, strict=True))
        event_types = sorted(parent["event_type"].dropna().unique())
        for event_type in event_types:
            selected_event = parent[parent["event_type"] == event_type]
            complement = parent[parent["event_type"] != event_type]
            valid = not selected_event.empty and not complement.empty
            if not valid:
                failures.append({
                    "subset": f"event_{event_type}",
                    "cell": parent_cell,
                    "reason": "empty_event_complement",
                })
            rows.append({
                "subset": f"event_{event_type}",
                "complement_key": f"not_{event_type}",
                "cell": {**parent_cell, "event_type": event_type},
                "disjoint": True,
                "exhaustive": len(selected_event) + len(complement) == len(parent),
                "exact_cell_valid": valid,
                **_three_numbers(
                    selected_event["r_bps"].to_numpy(dtype=float),
                    complement["r_bps"].to_numpy(dtype=float),
                ),
            })

    # above vs below median mde50 (from metrics)
    if not metrics_df.empty and "mde50" in metrics_df.columns and "log_R" in metrics_df.columns:
        m = metrics_df[metrics_df["mde50"].notna()].copy()
        if len(m):
            med = float(m["mde50"].median())
            hi = m[m["mde50"] >= med]
            lo = m[m["mde50"] < med]
            # use mean as proxy payoff column
            col = "mean" if "mean" in m.columns else "log_R"
            stats = _three_numbers(
                hi[col].to_numpy(dtype=float) if col in hi.columns else np.array([]),
                lo[col].to_numpy(dtype=float) if col in lo.columns else np.array([]),
            )
            rows.append({
                "subset": "above_median_mde50",
                "complement_key": "below_median_mde50",
                **stats,
            })
        else:
            failures.append({
                "subset": "above_median_mde50",
                "reason": "no_finite_mde50_cells",
            })
    else:
        failures.append({
            "subset": "above_median_mde50",
            "reason": "required_metrics_population_missing",
        })

    required = {
        "subset", "complement_key", "payoff_scale_ratio",
        "sign_share_differential", "excluded_mean_minus_median",
    }
    schema_ok = (
        len(rows) > 0
        and not failures
        and all(required.issubset(r.keys()) for r in rows)
    )
    return {
        "rows": rows,
        "schema_ok": schema_ok,
        "n_rows": len(rows),
        "invalid_exact_cells": failures,
        "note": "Each selected set is compared within its exact disjoint L0 cell.",
    }
