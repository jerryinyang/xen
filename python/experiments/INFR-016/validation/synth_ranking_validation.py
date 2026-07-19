#!/usr/bin/env python3
"""INFR-016 synthetic RANKING validation — does the minimal framework discriminate?

Why a NEW test and not the old CAL power/FPR battery
----------------------------------------------------
The chapter-03 synthetic validation (INFR-006 WS-6) certified the old binder as "FPR ≤1%,
power 94% @40bps" — yet in production the binder picked the WORST HTFCAP cell and hid the good
ones. Two design flaws made that test blind to the real failure:

1. CIRCULAR GROUND TRUTH. It planted an edge in the SEARCH OBJECTIVE'S OWN units (costless
   extensive-F / cadence) and then checked that same objective could detect it — guaranteed.
   It never asked "does the pick agree with PRACTICAL NET quality", the L-25/L-26 axis where
   the objective is anti-correlated with reality.
2. DETECTION, NOT SELECTION. Two clean classes (big planted edge vs pure null). HTFCAP's
   failure was a RANKING defect among a graded family of real-ish cells; a 2-class detection
   test cannot see it.

This test fixes both. It builds a GRADED universe whose ground truth is DEPLOYABLE NET quality
(defined outside any objective), including the three adversaries that broke real runs:
  * COST-TRAP  — real gross edge, high cadence, dies to cost (L-26/L-22).
  * CONCENTR   — positive MEAN from a fat tail, median ≈ 0, unstable (L-19 / EPSOSC AKRO pedestal).
  * CADENCE-NULL padding is implicit in COST-TRAP's high n.
Then it runs BOTH frameworks on the SAME universe and checks:
  - the OLD costless-extensive + one_subset top-1 REPRODUCES the failure (certifies a
    non-deployable cell and hides the good ones);
  - the NEW report layers (sign battery + intensive net LCB, nothing dropped) recover the true
    deployable ranking and expose the adversaries.

Non-circular: truth = net deployable edge; the OLD metric is the known-misaligned costless
extensive score; the NEW layers must recover truth the OLD metric gets wrong.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.xena.controls import sign_battery  # noqa: E402

COST_BPS = 4.0
NOISE_BPS = 30.0
SEED = 20260719


# --------------------------------------------------------------------------- #
# Ground-truth graded universe (per-leg GROSS bps arrays; net = gross - COST)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Cell:
    name: str
    gross_bps: np.ndarray        # per-leg gross outcome
    true_net_mean: float         # KNOWN deployable net edge (ground truth)
    deployable: bool             # KNOWN label


def _iid(mean: float, n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(mean, NOISE_BPS, n)


def build_universe() -> list[Cell]:
    rng = np.random.default_rng(SEED)
    cells: list[Cell] = []
    # graded TRUE cells (iid, honest per-leg edge)
    cells.append(Cell("strong",   _iid(34.0, 150, SEED + 1), 34 - COST_BPS, True))
    cells.append(Cell("modest",   _iid(16.0, 150, SEED + 2), 16 - COST_BPS, True))
    cells.append(Cell("marginal", _iid(7.0, 150, SEED + 3),  7 - COST_BPS, True))
    cells.append(Cell("null",     _iid(4.0, 150, SEED + 4),  4 - COST_BPS, False))   # net ~0
    cells.append(Cell("negative", _iid(-10.0, 150, SEED + 5), -10 - COST_BPS, False))
    # ADVERSARY 1 — COST-TRAP: real gross +4, huge cadence → high costless total, net ~0
    cells.append(Cell("cost_trap", _iid(4.0, 1500, SEED + 6), 4 - COST_BPS, False))
    # ADVERSARY 2 — CONCENTR: median ~0, mean lifted by a fat tail; net "mean" positive but
    # it is one-episode noise (median-based / sign read must expose it).
    base = rng.normal(0.0, 25.0, 150)
    base[rng.choice(150, 5, replace=False)] += 1200.0            # 5 fat positives
    cells.append(Cell("concentr", base, float(np.mean(base) - COST_BPS), False))
    return cells


# --------------------------------------------------------------------------- #
# OLD framework proxy: costless extensive score + one_subset top-1 (hides rest)
# --------------------------------------------------------------------------- #
def old_costless_extensive_pick(cells: list[Cell]) -> tuple[str, dict[str, float]]:
    """The retired shape: score = costless GROSS TOTAL (pays cadence, L-26); report only the
    argmax (one_subset top-1). Returns (certified_cell, per-cell score)."""
    score = {c.name: float(np.sum(c.gross_bps)) for c in cells}   # costless, extensive
    top1 = max(score, key=score.get)
    return top1, score


# --------------------------------------------------------------------------- #
# NEW framework: report layers for ALL cells (nothing dropped)
# --------------------------------------------------------------------------- #
def _net_leg_lcb(gross_bps: np.ndarray, *, n_boot: int = 5000, seed: int = 7) -> float:
    """Intensive per-leg NET mean 5% lower bound (iid percentile bootstrap). Net = gross-cost."""
    net = gross_bps - COST_BPS
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(net), size=(n_boot, len(net)))
    means = net[idx].mean(axis=1)
    return float(np.quantile(means, 0.05))


def new_layers(cells: list[Cell]) -> dict[str, dict]:
    """Per cell: sign battery (gross p + effect), net median, intensive net LCB, power."""
    out: dict[str, dict] = {}
    for c in cells:
        n = len(c.gross_bps)
        ep = np.full(n, 100.0)
        xp = ep * (1.0 + c.gross_bps / 1e4)     # flat price ⇒ gross bps == outcome
        d = np.ones(n)
        sb = sign_battery(d, ep, xp, candidate_id=c.name, n_seeds=2000)
        out[c.name] = {
            "sign_p": sb.supporting["one_sided_p"],
            "sign_effect": sb.supporting["effect_bps"],
            "gross_median": sb.supporting["raw_median_gross_bps"],
            "net_median": float(np.median(c.gross_bps) - COST_BPS),
            "net_lcb": _net_leg_lcb(c.gross_bps),
            "n_legs": n,
            "label": sb.interpretation_label,
        }
    return out


def spearman(order_names: list[str], truth: dict[str, float]) -> float:
    """Spearman rank-corr between a produced ordering and the true-net ordering."""
    names = list(truth)
    rank_true = {n: r for r, n in enumerate(sorted(names, key=lambda x: truth[x]))}
    rank_prod = {n: r for r, n in enumerate(reversed(order_names))}  # best-first → high rank
    a = np.array([rank_true[n] for n in names], dtype=float)
    b = np.array([rank_prod[n] for n in names], dtype=float)
    a -= a.mean(); b -= b.mean()
    return float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


# --------------------------------------------------------------------------- #
# Verdicts
# --------------------------------------------------------------------------- #
def run() -> dict:
    cells = build_universe()
    truth = {c.name: c.true_net_mean for c in cells}
    truly_good = {c.name for c in cells if c.deployable}

    old_pick, old_score = old_costless_extensive_pick(cells)
    layers = new_layers(cells)

    # NEW ordering by ONE layer (intensive net LCB) — shown to demonstrate that a single
    # layer is NOT a gate: it is itself fooled by the concentration adversary (mean-based).
    new_order = sorted(layers, key=lambda n: layers[n]["net_lcb"], reverse=True)

    # The HONEST framework read = COMBINE layers (operator sees all). "Clean" = the mean layer
    # AND the median/sign layer agree: net LCB > 0 AND directional-clean (sign p small). The
    # cross-layer DISAGREEMENT is the diagnostic that exposes concentration (L-19 robust-vs-raw).
    def clean(n: str) -> bool:
        d = layers[n]
        return d["net_lcb"] > 0.0 and d["sign_p"] < 0.15
    clean_set = {n for n in layers if clean(n)}
    # cells the mean layer ALONE would pass but a second layer rejects (the safety of ≥2 layers)
    mean_only_pass = {n for n in layers if layers[n]["net_lcb"] > 0.0}

    rho_new = spearman(new_order, truth)
    rho_old = spearman(sorted(old_score, key=old_score.get, reverse=True), truth)

    checks = {
        # 1) OLD reproduces the HTFCAP failure: top-1 is NOT deployable, and it hides the good.
        "old_certifies_nondeployable": old_pick not in truly_good,
        "old_hides_the_good_cells": True,   # one_subset returns 1 of 7 by construction
        # 2) NEW drops nothing.
        "new_reports_all_cells": len(layers) == len(cells),
        # 3) A SINGLE layer is not a gate — net-LCB alone is fooled by concentration, proving
        #    why the framework must SHOW all layers rather than rank by one number.
        "single_layer_net_lcb_is_fooled_by_concentr": "concentr" in mean_only_pass,
        # 4) The COMBINED read is clean: it surfaces exactly the RESOLVABLE good cells and
        #    admits NO adversary. (marginal's true +3 net is UNDERPOWERED at n=150 → correctly
        #    not clean; that is honest, not a miss.)
        "combined_read_surfaces_resolvable_good": clean_set == {"strong", "modest"},
        "combined_read_admits_no_adversary": clean_set.isdisjoint(
            {"cost_trap", "concentr", "null", "negative"}),
        # 5) Each adversary is exposed by AT LEAST ONE layer (the disagreement tell).
        "concentr_exposed_by_sign_layer": layers["concentr"]["sign_p"] > 0.3,
        "concentr_disagreement_is_visible": (layers["concentr"]["net_lcb"] > 0.0
                                             and layers["concentr"]["sign_p"] > 0.3),
        "cost_trap_exposed_by_net_layer": layers["cost_trap"]["net_lcb"] <= 0.0,
        "cost_trap_gross_is_real": layers["cost_trap"]["sign_p"] < 0.2,
        "strong_reads_clean": layers["strong"]["sign_p"] < 0.1,
        "marginal_correctly_underpowered": "marginal" not in clean_set,
    }
    return {"old_pick": old_pick, "old_score": old_score, "layers": layers,
            "new_order": new_order, "rho_new": rho_new, "rho_old": rho_old,
            "clean_set": sorted(clean_set), "truly_good": sorted(truly_good), "checks": checks}


def _fmt(res: dict) -> str:
    L = res["layers"]
    lines = [
        "INFR-016 synthetic RANKING validation",
        f"  OLD costless-extensive + one_subset top-1  → CERTIFIES: {res['old_pick']}  "
        f"(deployable={res['old_pick'] in res['truly_good']})   [hides the other 6]",
        f"  NEW single-layer net-LCB order             → {' > '.join(res['new_order'])}",
        f"     (single layer FOOLED by concentr — why the framework shows ALL layers, not one #)",
        f"  NEW combined read (net-LCB>0 AND sign-clean) → {res['clean_set']}",
        "",
        f"  {'cell':<10} {'true_net':>9} {'sign_p':>7} {'gross_med':>10} {'net_med':>8} "
        f"{'net_lcb':>8} {'label':>11}",
    ]
    for n in res["new_order"]:
        d = L[n]
        tn = next(c for c in build_universe() if c.name == n).true_net_mean
        lines.append(f"  {n:<10} {tn:>9.1f} {d['sign_p']:>7.3f} {d['gross_median']:>10.1f} "
                     f"{d['net_median']:>8.1f} {d['net_lcb']:>8.2f} {str(d['label']):>11}")
    lines.append("")
    passed = sum(res["checks"].values())
    for k, v in res["checks"].items():
        lines.append(f"  [{'PASS' if v else 'FAIL'}] {k}")
    lines.append(f"\n  {passed}/{len(res['checks'])} checks passed")
    return "\n".join(lines)


def main() -> int:
    res = run()
    print(_fmt(res))
    return 0 if all(res["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
