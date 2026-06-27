"""
EXP-011 loss functions — the three predeclared operating-point loss specifications.

Pure, deterministic selection logic over the frozen EXP-006 tau-frontier. Every
coefficient in this module is PREDECLARED in ``scope.md`` (§"Predeclared loss
function") and frozen for the phase: it is NOT tunable and must not be changed in
response to any observed result. The selection read is mechanical once these
losses are fixed.

Each selector consumes a per-domain sequence of row dicts (one per frontier
multiplier) with keys:
    multiplier, mde_bps, fpr, fpr_wilson_upper, sub_rate, materiality_bps,
    reportable (FPR precision met), c_fn_term (mean 1-TPR over the material-edge
    prior G_d), c_precise (all G_d TPR cells precise).
"""
from __future__ import annotations

from typing import Any, Sequence

# --------------------------------------------------------------------------- #
# Frozen frontier + predeclared loss coefficients (scope.md; NOT tunable)
# --------------------------------------------------------------------------- #
FRONTIER_MULTIPLIERS: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)

# Loss B weights (scope: w_blind = w_fp = w_sub = 1.0 — neutral first-principles prior).
W_BLIND: float = 1.0
W_FP: float = 1.0
W_SUB: float = 1.0

# Loss C coefficients (scope: c_fp = c_fn = 1.0).
C_FP: float = 1.0
C_FN: float = 1.0

# Materiality tie-break cutoff (scope D-lenientL5 caveat): a lower MDE bought with
# more than half sub-material passes is not a genuine sensitivity gain.
SUBMATERIAL_LIMIT: float = 0.50

# Consistency tolerance: agreement within one step on the ordered 7-point frontier.
ONE_GRID_STEP: int = 1

# Float-key snap tolerance for frontier membership.
_SNAP_TOL: float = 1e-9


def _snap(multiplier: float) -> float:
    """Snap a float multiplier to its exact frozen-frontier value."""
    for m in FRONTIER_MULTIPLIERS:
        if abs(m - multiplier) < _SNAP_TOL:
            return m
    raise ValueError(f"multiplier {multiplier!r} is not on the frozen frontier")


def frontier_index(multiplier: float) -> int:
    """Ordered position of a multiplier on the frozen tau-frontier."""
    return FRONTIER_MULTIPLIERS.index(_snap(multiplier))


# --------------------------------------------------------------------------- #
# Loss A — lexicographic, FPR-constrained (PRIMARY; headline recommendation)
# --------------------------------------------------------------------------- #
def select_loss_a(rows: Sequence[dict[str, Any]], alpha0: float) -> dict[str, Any]:
    """Select the primary operating point by the predeclared lexicographic rule.

    (1) keep tau with FPR Wilson upper <= alpha0; (2) minimise MDE; (3) materiality
    tie-break: drop min-MDE survivors with sub_rate > 0.50, then lowest sub_rate;
    (4) conservatism tie-break: largest tau. Degenerate guard: if step 3 empties the
    min-MDE survivors, recommend the lowest-MDE tau whose sub_rate <= 0.50
    (``materiality_limited``).
    """
    survivors = [r for r in rows if r["reportable"] and r["fpr_wilson_upper"] <= alpha0]
    if not survivors:
        return {"selectable": False, "reason": "no_reportable_fpr_survivor"}

    min_mde = min(r["mde_bps"] for r in survivors)
    min_mde_rows = [r for r in survivors if r["mde_bps"] == min_mde]
    acceptable = [r for r in min_mde_rows if r["sub_rate"] <= SUBMATERIAL_LIMIT]
    materiality_limited = False

    if not acceptable:  # degenerate guard (scope): step 3 removed all min-MDE survivors
        materiality_limited = True
        clean = [r for r in survivors if r["sub_rate"] <= SUBMATERIAL_LIMIT]
        if not clean:
            return {"selectable": False, "reason": "all_survivors_submaterial"}
        lowest = min(r["mde_bps"] for r in clean)
        acceptable = [r for r in clean if r["mde_bps"] == lowest]

    best = sorted(acceptable, key=lambda r: (r["sub_rate"], -r["multiplier"]))[0]
    return {
        "selectable": True,
        "multiplier": best["multiplier"],
        "mde_bps": best["mde_bps"],
        "sub_rate": best["sub_rate"],
        "materiality_limited": materiality_limited,
    }


# --------------------------------------------------------------------------- #
# Loss B — weighted scalar (robustness specification)
# --------------------------------------------------------------------------- #
def loss_b_value(row: dict[str, Any], alpha0: float) -> float:
    """L_B = w_blind*max(0,MDE-mat)/mat + w_fp*(FPR/alpha0) + w_sub*sub_rate."""
    mat = row["materiality_bps"]
    blind_band = max(0.0, row["mde_bps"] - mat) / mat
    return W_BLIND * blind_band + W_FP * (row["fpr"] / alpha0) + W_SUB * row["sub_rate"]


def select_loss_b(rows: Sequence[dict[str, Any]], alpha0: float) -> dict[str, Any]:
    """Minimise the predeclared weighted scalar over reportable tau; tie -> largest tau."""
    cand = [r for r in rows if r["reportable"]]
    if not cand:
        return {"selectable": False, "reason": "no_reportable_cell"}
    scored = [(loss_b_value(r, alpha0), r) for r in cand]
    best_val = min(v for v, _ in scored)
    tied = [r for v, r in scored if abs(v - best_val) < 1e-12]
    best = max(tied, key=lambda r: r["multiplier"])
    return {"selectable": True, "multiplier": best["multiplier"], "loss_value": best_val}


# --------------------------------------------------------------------------- #
# Loss C — Bayes risk over the predeclared material-edge prior (robustness spec)
# --------------------------------------------------------------------------- #
def loss_c_value(row: dict[str, Any]) -> float:
    """L_C = c_fp*FPR + c_fn*mean_{e in G_d}(1 - TPR(d,tau,e))."""
    return C_FP * row["fpr"] + C_FN * row["c_fn_term"]


def select_loss_c(rows: Sequence[dict[str, Any]], alpha0: float) -> dict[str, Any]:
    """Minimise the predeclared Bayes risk over reportable, TPR-precise tau.

    A tau is eligible only if its FPR cell is reportable and every material-edge
    prior TPR cell is precise (``c_precise``). ``reduced_precision`` flags that some
    otherwise-reportable tau was dropped for TPR imprecision.
    """
    cand = [r for r in rows if r["reportable"] and r["c_precise"]]
    reduced = any(r["reportable"] and not r["c_precise"] for r in rows)
    if not cand:
        return {"selectable": False, "reason": "no_precise_tpr_cell", "reduced_precision": True}
    scored = [(loss_c_value(r), r) for r in cand]
    best_val = min(v for v, _ in scored)
    tied = [r for v, r in scored if abs(v - best_val) < 1e-12]
    best = max(tied, key=lambda r: r["multiplier"])
    return {
        "selectable": True,
        "multiplier": best["multiplier"],
        "loss_value": best_val,
        "reduced_precision": reduced,
    }


# --------------------------------------------------------------------------- #
# Cross-loss consistency verdict (predeclared meta-rule)
# --------------------------------------------------------------------------- #
def consistency_verdict(mult_a: float, mult_b: float, mult_c: float) -> dict[str, Any]:
    """ROBUST if all three tau* fall within one grid step on the frozen frontier."""
    idx = [frontier_index(m) for m in (mult_a, mult_b, mult_c)]
    spread = max(idx) - min(idx)
    return {
        "verdict": "ROBUST" if spread <= ONE_GRID_STEP else "LOSS_SENSITIVE",
        "index_spread": spread,
    }
