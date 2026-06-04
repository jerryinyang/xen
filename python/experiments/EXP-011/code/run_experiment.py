"""
Experiment EXP-011: Predeclared-Loss Operating-Point Synthesis & Recommendation.

Phase 002 synthesis (exploratory; recommends, does not adopt). Reads frozen
result-level artifacts from EXP-003/005/006/007/008/009/010 and, under three loss
functions PREDECLARED in scope.md, selects a recommended per-domain operating point
on the frozen EXP-006 L5 threshold tau-frontier, reports a cross-loss consistency
verdict, and records the predeclared conditional adoption rule for Phase 003.

Pure deterministic result-level post-processing: no market data is loaded, no
global holdout is touched, no new draws are generated, and no referee is re-run.
The only non-trivial computation is a bounded, projected, draw-keyed join used to
reconstruct the sub-material pass rate for tau>0 (EXP-007 definition), guarded by an
exact reproduction check against EXP-007's published tau=0 values.

Implements analysis-plan.md Steps 1-6. Do not run inside the pipeline (manual
execution gate).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from xen.referee_calibration import MATERIALITY_BPS as XEN_MATERIALITY_BPS
from xen.referee_calibration import write_json

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loss_functions import (  # noqa: E402  (local helper; needs script dir on path)
    FRONTIER_MULTIPLIERS,
    SUBMATERIAL_LIMIT,
    consistency_verdict,
    loss_b_value,
    loss_c_value,
    select_loss_a,
    select_loss_b,
    select_loss_c,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants — paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-011"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"


def _results(exp: str) -> Path:
    return EXPERIMENTS_DIR / exp / "results"


EXP003_META = _results("EXP-003") / "run_metadata.json"
EXP003_DRAWS = _results("EXP-003") / "draw_verdicts.csv"
EXP005_META = _results("EXP-005") / "run_metadata.json"
EXP006_META = _results("EXP-006") / "run_metadata.json"
EXP006_MDE = _results("EXP-006") / "threshold_mde_summary.csv"
EXP006_FPR = _results("EXP-006") / "threshold_fpr_summary.csv"
EXP006_TPR = _results("EXP-006") / "threshold_tpr_summary.csv"
EXP006_DRAWS = _results("EXP-006") / "threshold_draw_verdicts.csv"
EXP007_META = _results("EXP-007") / "run_metadata.json"
EXP007_SUBMAT = _results("EXP-007") / "submaterial_pass_rates.csv"
EXP007_FRONTIER = _results("EXP-007") / "lenient_vs_frontier.csv"
EXP008_META = _results("EXP-008") / "run_metadata.json"
EXP008_POOL = _results("EXP-008") / "mde_pool_comparison.csv"
EXP008_PI_MDE = _results("EXP-008") / "per_instrument_mde_summary.csv"
EXP009_META = _results("EXP-009") / "run_metadata.json"
EXP009_DIST = _results("EXP-009") / "effect_distribution_summary.csv"
EXP010_META = _results("EXP-010") / "run_metadata.json"
EXP010_PROTO = _results("EXP-010") / "protocol_comparison.csv"
EXP010_PROTO_MDE = _results("EXP-010") / "protocol_mde_summary.csv"

# --------------------------------------------------------------------------- #
# Constants — frozen Phase 001/002 invariants & predeclared selection knobs
# (every value here is predeclared by scope.md; none is tunable against results)
# --------------------------------------------------------------------------- #
ALPHA0 = 0.05
DOMAINS = ("5m", "1h", "4h")
REFEREE = "gate_stack"
FPR_HALF_WIDTH_TARGET = 0.03  # D-prec
TPR_HALF_WIDTH_TARGET = 0.05  # D-prec
MATERIAL_BAND_MULT = 4.0  # Loss C prior band [mat, 4*mat] (scope)
REPRO_TOL = 1e-9  # sub-material tau=0 reproduction tolerance vs EXP-007

# Materiality buffers — sourced from the frozen harness, asserted at runtime.
MATERIALITY_BPS: dict[str, float] = {d: float(XEN_MATERIALITY_BPS[d]) for d in DOMAINS}
_EXPECTED_MATERIALITY = {"5m": 0.5, "1h": 1.5, "4h": 3.0}

# Loss C material-edge prior G_d: EXP-006 planted-edge grid points within [mat, 4*mat].
# Derived from the frozen edge grid {0,0.5,1,2,4,8,12,16,24,32}; pinned here and
# asserted against the band so the prior support is auditable.
GD_EDGES: dict[str, tuple[float, ...]] = {
    "5m": (0.5, 1.0, 2.0),
    "1h": (2.0, 4.0),
    "4h": (4.0, 8.0, 12.0),
}

DRAW_KEY_COLS = ["instrument", "domain", "scenario", "generator", "edge_bps", "draw", "alpha"]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> dict[str, Any]:
    """Read a JSON metadata file."""
    return json.loads(path.read_text())


def _read_summary(path: Path) -> pl.DataFrame:
    """Eagerly read a small result-level summary CSV."""
    return pl.read_csv(path)


def _key(*parts: Any) -> tuple:
    """Build a float-safe lookup key (round floats to avoid IEEE mismatch)."""
    return tuple(round(p, 4) if isinstance(p, float) else p for p in parts)


# --------------------------------------------------------------------------- #
# Step 1 — dependency + precision gating
# --------------------------------------------------------------------------- #
def gate_dependencies() -> dict[str, str]:
    """Assert upstream completion tokens; core deps hard-fail, context deps soft.

    EXP-003/006/007 feed every domain and the reproduction gate -> hard failure if
    missing/incomplete. EXP-005/008/009/010 are overlay/context only -> recorded,
    not fatal (a missing context artifact degrades the adoption overlay, never the
    headline recommendation).
    """
    m3, m6, m7 = _load_json(EXP003_META), _load_json(EXP006_META), _load_json(EXP007_META)
    if m3.get("overall_status") != "COMPLETE":
        raise RuntimeError("EXP-003 not COMPLETE; cannot evaluate the lever.")
    if m6.get("overall_status") != "COMPLETE" or not m6.get("strict_reference_pass"):
        raise RuntimeError("EXP-006 not COMPLETE / strict_reference_pass false.")
    if m7.get("overall_status") != "COMPLETE" or not m7.get("structural_equivalence_pass"):
        raise RuntimeError("EXP-007 not COMPLETE / structural_equivalence_pass false.")

    tokens = {
        "EXP-003": m3.get("overall_status"),
        "EXP-006": m6.get("overall_status"),
        "EXP-007": m7.get("overall_status"),
    }
    for exp, meta in (("EXP-005", EXP005_META), ("EXP-008", EXP008_META),
                      ("EXP-009", EXP009_META), ("EXP-010", EXP010_META)):
        try:
            tokens[exp] = _load_json(meta).get("overall_status", "MISSING")
        except FileNotFoundError:
            tokens[exp] = "MISSING"
            logger.warning("%s metadata missing; its overlay will be omitted.", exp)
    return tokens


# --------------------------------------------------------------------------- #
# Step 2 — decision table
# --------------------------------------------------------------------------- #
def _materiality_expr() -> pl.Expr:
    """Polars expression mapping the domain column to its frozen materiality buffer."""
    expr = pl.when(pl.col("domain") == "5m").then(pl.lit(MATERIALITY_BPS["5m"]))
    expr = expr.when(pl.col("domain") == "1h").then(pl.lit(MATERIALITY_BPS["1h"]))
    expr = expr.when(pl.col("domain") == "4h").then(pl.lit(MATERIALITY_BPS["4h"]))
    return expr.otherwise(None).alias("materiality_bps")


def build_decision_table(mde: pl.DataFrame, fpr: pl.DataFrame) -> pl.DataFrame:
    """Assemble one row per (domain, tau-multiplier) at alpha0 (sub_rate added later)."""
    mde_s = mde.filter((pl.col("referee") == REFEREE) & (pl.col("alpha") == ALPHA0)).select(
        ["domain", "multiplier", "mde_bps", "fpr", "fpr_wilson_half_width", "mde_grid_uncertainty_bps"]
    )
    fpr_s = fpr.filter((pl.col("referee") == REFEREE) & (pl.col("alpha") == ALPHA0)).select(
        ["domain", "multiplier", pl.col("wilson_upper").alias("fpr_wilson_upper")]
    )
    table = mde_s.join(fpr_s, on=["domain", "multiplier"], how="inner").with_columns(
        _materiality_expr(),
        (pl.col("fpr_wilson_half_width") <= FPR_HALF_WIDTH_TARGET).alias("reportable"),
        (pl.col("multiplier") == 1.0).alias("strict_reference"),
        (pl.col("multiplier") == 0.0).alias("lenient_endpoint"),
    )
    return table.sort(["domain", "multiplier"])


# --------------------------------------------------------------------------- #
# Step 3 — sub-material reconstruction (bounded, projected, draw-keyed join)
# --------------------------------------------------------------------------- #
def reconstruct_submaterial() -> pl.DataFrame:
    """Reconstruct sub(d, tau, e) for all multipliers via a bounded projected join.

    sub = fraction of positive-scenario gate passes (``passed_tau``) whose net point
    estimate ``effect_bps`` < materiality_bps(domain). ``passed_tau`` (EXP-006, full
    gate at swept tau) is joined to ``effect_bps`` (EXP-003, tau-invariant net point
    estimate) on the shared draw keys. Memory is bounded by column projection plus a
    scenario/alpha filter before collect; the cross product is never materialised.
    """
    left = (
        pl.scan_csv(EXP006_DRAWS)
        .select(["instrument", "domain", "scenario", "generator", "edge_bps",
                 "draw", "alpha", "multiplier", "passed_tau"])
        .filter((pl.col("scenario") == "positive") & (pl.col("alpha") == ALPHA0))
        .collect()
    )
    right = (
        pl.scan_csv(EXP003_DRAWS)
        .select(["instrument", "domain", "scenario", "generator", "edge_bps",
                 "draw", "alpha", "referee", "effect_bps"])
        .filter((pl.col("referee") == REFEREE) & (pl.col("scenario") == "positive")
                & (pl.col("alpha") == ALPHA0))
        .drop("referee")
        .collect()
    )
    joined = left.join(right, on=DRAW_KEY_COLS, how="inner")

    # Key-alignment guards: every EXP-006 row must match (fan-out is many-tau-to-one
    # on the tau-invariant effect), and every EXP-003 positive draw must appear.
    if joined.height != left.height:
        raise RuntimeError(
            f"sub-material join dropped EXP-006 rows: {left.height - joined.height} unmatched."
        )
    unmatched_right = right.join(
        left.select(DRAW_KEY_COLS).unique(), on=DRAW_KEY_COLS, how="anti"
    )
    if unmatched_right.height != 0:
        raise RuntimeError(
            f"{unmatched_right.height} EXP-003 positive draws absent from the EXP-006 sweep."
        )

    agg = (
        joined.with_columns((pl.col("effect_bps") < _materiality_expr()).alias("sub_flag"))
        .group_by(["domain", "multiplier", "edge_bps"])
        .agg(
            pl.col("passed_tau").sum().alias("pass_count"),
            (pl.col("passed_tau") & pl.col("sub_flag")).sum().alias("submaterial_count"),
        )
        .with_columns(
            pl.when(pl.col("pass_count") > 0)
            .then(pl.col("submaterial_count") / pl.col("pass_count"))
            .otherwise(0.0)  # finite zero-baseline: no passes -> no sub-material passes
            .alias("sub_rate")
        )
        .sort(["domain", "multiplier", "edge_bps"])
    )
    return agg


def check_submaterial_reproduction(recon: pl.DataFrame, exp007: pl.DataFrame) -> bool:
    """Hard gate: reconstructed sub(d, tau=0, e) must equal EXP-007 within tolerance."""
    ours = recon.filter(pl.col("multiplier") == 0.0).select(["domain", "edge_bps", "sub_rate"])
    theirs = exp007.filter(pl.col("alpha") == ALPHA0).select(
        ["domain", "edge_bps", pl.col("submaterial_rate").alias("exp007_rate")]
    )
    merged = ours.join(theirs, on=["domain", "edge_bps"], how="inner")
    if merged.height != theirs.height or merged.height != ours.height:
        raise RuntimeError(
            f"sub-material tau=0 edge sets differ (ours={ours.height}, "
            f"EXP-007={theirs.height}, matched={merged.height})."
        )
    max_abs = merged.select((pl.col("sub_rate") - pl.col("exp007_rate")).abs().max()).item()
    if max_abs is None or max_abs > REPRO_TOL:
        raise RuntimeError(f"sub-material tau=0 reproduction mismatch: max |diff| = {max_abs}.")
    return True


# --------------------------------------------------------------------------- #
# Step 3/4 prep — attach sub_rate at each tau's operating MDE edge; TPR terms
# --------------------------------------------------------------------------- #
def attach_sub_rate(decision: pl.DataFrame, recon: pl.DataFrame, exp007: pl.DataFrame) -> pl.DataFrame:
    """Attach sub_rate at edge == MDE(d, tau): tau=0 from EXP-007, tau>0 from recon."""
    recon_map = {
        _key(r["domain"], r["multiplier"], r["edge_bps"]): r["sub_rate"]
        for r in recon.iter_rows(named=True)
    }
    e7 = exp007.filter(pl.col("alpha") == ALPHA0)
    exp007_map = {
        _key(r["domain"], r["edge_bps"]): r["submaterial_rate"] for r in e7.iter_rows(named=True)
    }
    sub_values: list[float] = []
    for r in decision.iter_rows(named=True):
        mde, mult, dom = r["mde_bps"], r["multiplier"], r["domain"]
        if mult == 0.0:
            sub_values.append(float(exp007_map[_key(dom, mde)]))
        else:
            sub_values.append(float(recon_map[_key(dom, mult, mde)]))
    return decision.with_columns(pl.Series("sub_rate", sub_values))


def build_tpr_terms(tpr: pl.DataFrame) -> dict[tuple, dict[str, float]]:
    """Per (domain, multiplier): mean (1-TPR) over G_d and a precision flag.

    Returns a map keyed (domain, multiplier) -> {c_fn_term, c_precise}.
    """
    t = tpr.filter((pl.col("referee") == REFEREE) & (pl.col("alpha") == ALPHA0))
    tpr_map = {
        _key(r["domain"], r["multiplier"], r["edge_bps"]): (r["tpr"], r["wilson_half_width"])
        for r in t.iter_rows(named=True)
    }
    out: dict[tuple, dict[str, float]] = {}
    for dom in DOMAINS:
        for mult in FRONTIER_MULTIPLIERS:
            one_minus_tpr, precise = [], True
            for edge in GD_EDGES[dom]:
                tpr_val, hw = tpr_map[_key(dom, mult, edge)]
                one_minus_tpr.append(1.0 - tpr_val)
                precise = precise and (hw <= TPR_HALF_WIDTH_TARGET)
            out[_key(dom, mult)] = {
                "c_fn_term": float(np.mean(one_minus_tpr)),
                "c_precise": bool(precise),
            }
    return out


def assemble_rows(decision: pl.DataFrame, tpr_terms: dict[tuple, dict[str, float]]
                  ) -> dict[str, list[dict[str, Any]]]:
    """Group decision rows by domain into the dicts consumed by loss_functions."""
    rows_by_domain: dict[str, list[dict[str, Any]]] = {d: [] for d in DOMAINS}
    for r in decision.iter_rows(named=True):
        dom, mult = r["domain"], r["multiplier"]
        terms = tpr_terms[_key(dom, mult)]
        rows_by_domain[dom].append({
            "multiplier": mult,
            "mde_bps": r["mde_bps"],
            "fpr": r["fpr"],
            "fpr_wilson_upper": r["fpr_wilson_upper"],
            "sub_rate": r["sub_rate"],
            "materiality_bps": r["materiality_bps"],
            "reportable": r["reportable"],
            "c_fn_term": terms["c_fn_term"],
            "c_precise": terms["c_precise"],
        })
    for dom in DOMAINS:
        rows_by_domain[dom].sort(key=lambda x: x["multiplier"])
    return rows_by_domain


# --------------------------------------------------------------------------- #
# Step 4/5 — evaluate losses, consistency verdict, recommendation
# --------------------------------------------------------------------------- #
def _driver_term(rows: list[dict[str, Any]], multipliers: list[float]) -> str:
    """Name the normalised cost term with the largest spread across selected tau."""
    by_mult = {r["multiplier"]: r for r in rows}
    terms: dict[str, list[float]] = {"blind_band": [], "fpr": [], "sub_material": []}
    for m in set(multipliers):
        r = by_mult[m]
        mat = r["materiality_bps"]
        terms["blind_band"].append(max(0.0, r["mde_bps"] - mat) / mat)
        terms["fpr"].append(r["fpr"] / ALPHA0)
        terms["sub_material"].append(r["sub_rate"])
    spreads = {k: (max(v) - min(v)) for k, v in terms.items()}
    return max(spreads, key=lambda k: spreads[k])


def evaluate_domain(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the three predeclared losses and the consistency verdict for one domain."""
    a = select_loss_a(rows, ALPHA0)
    b = select_loss_b(rows, ALPHA0)
    c = select_loss_c(rows, ALPHA0)

    if not a["selectable"]:
        return {"status": "INCONCLUSIVE", "reason": a.get("reason"),
                "loss_a": a, "loss_b": b, "loss_c": c}

    taus = {"A": a["multiplier"], "B": b.get("multiplier"), "C": c.get("multiplier")}
    if b["selectable"] and c["selectable"]:
        cons = consistency_verdict(taus["A"], taus["B"], taus["C"])
        verdict = cons["verdict"]
        spread = cons["index_spread"]
        driver = _driver_term(rows, [taus["A"], taus["B"], taus["C"]]) \
            if verdict == "LOSS_SENSITIVE" else None
    else:
        verdict, spread, driver = "INCOMPLETE", None, None  # a robustness spec under-powered

    return {
        "status": "RECOMMENDED",
        "tau_star_headline": a["multiplier"],
        "mde_bps": a["mde_bps"],
        "sub_rate": a["sub_rate"],
        "materiality_limited": a["materiality_limited"],
        "tau_star_A": taus["A"],
        "tau_star_B": taus["B"],
        "tau_star_C": taus["C"],
        "consistency_verdict": verdict,
        "index_spread": spread,
        "driver_term": driver,
        "loss_c_reduced_precision": c.get("reduced_precision", False),
        "loss_a": a, "loss_b": b, "loss_c": c,
    }


# --------------------------------------------------------------------------- #
# Step 6 — read-only context overlays (never inputs to tau* selection)
# --------------------------------------------------------------------------- #
def build_overlays(tokens: dict[str, str]) -> dict[str, Any]:
    """Per-instrument (EXP-008), split (EXP-010), non-blindness (EXP-005),
    effect-location (EXP-009) overlays — descriptive caveats only."""
    overlays: dict[str, Any] = {}

    if tokens.get("EXP-008") == "COMPLETE":
        pool = _read_summary(EXP008_POOL).filter(
            (pl.col("referee") == REFEREE) & (pl.col("alpha") == ALPHA0)
        )
        overlays["per_instrument_material"] = {
            dom: pool.filter((pl.col("domain") == dom) & pl.col("material"))["instrument"].to_list()
            for dom in DOMAINS
        }

    if tokens.get("EXP-010") == "COMPLETE":
        proto = _read_summary(EXP010_PROTO).filter(pl.col("alpha") == ALPHA0)
        overlays["walk_forward_material"] = {
            dom: bool(proto.filter(
                (pl.col("domain") == dom) & (pl.col("protocol") == "walk_forward")
            )["material"].to_list()[0]) if proto.filter(
                (pl.col("domain") == dom) & (pl.col("protocol") == "walk_forward")
            ).height else None
            for dom in DOMAINS
        }

    if tokens.get("EXP-005") == "COMPLETE":
        overlays["domain_status_exp005"] = _load_json(EXP005_META).get("domain_status", {})

    if tokens.get("EXP-009") == "COMPLETE":
        dist = _read_summary(EXP009_DIST).filter(
            (pl.col("group_kind") == "domain") & (pl.col("family") == "ALL")
            & (pl.col("referee") == REFEREE)
        )
        overlays["exp009_n_at_or_above_mde"] = {
            r["domain"]: int(r["n_at_or_above_mde"]) for r in dist.iter_rows(named=True)
        }
    return overlays


ADOPTION_RULE_TEMPLATE = (
    "Adopt tau* for domain {domain} only if, on FRESH Phase 003 synthetic draws, all hold: "
    "(i) FPR(d, tau*) Wilson upper <= alpha0=0.05; (ii) sub(d, tau*) <= 0.50 at the operating "
    "MDE; (iii) an EXP-005-style realistic candidate carrying an edge >= MDE(d, tau*) is detected "
    "with TPR >= 0.80. If any condition fails on fresh draws, retain the frozen strict reference "
    "tau=1.0 for that domain. Caveats: 1h/4h MDE roughly doubles under walk-forward (EXP-010) so "
    "the recommendation is conditional on the single chronological split; the strict gate is "
    "already an honest detection floor on all domains (EXP-005 DETECTED_FLOOR), so any sub-tau=1.0 "
    "recommendation is a sensitivity-headroom choice, not a blindness remedy."
)


def build_adoption_rule(results: dict[str, dict[str, Any]], overlays: dict[str, Any]) -> dict[str, Any]:
    """Attach the predeclared conditional adoption rule + overlay flags per domain."""
    rule: dict[str, Any] = {}
    for dom in DOMAINS:
        res = results[dom]
        rule[dom] = {
            "recommended_tau_multiplier": res.get("tau_star_headline"),
            "status": res["status"],
            "conditional_adoption_rule": ADOPTION_RULE_TEMPLATE.format(domain=dom),
            "per_instrument_material": overlays.get("per_instrument_material", {}).get(dom),
            "walk_forward_material": overlays.get("walk_forward_material", {}).get(dom),
            "exp005_detection": overlays.get("domain_status_exp005", {}).get(dom),
            "exp009_n_at_or_above_mde": overlays.get("exp009_n_at_or_above_mde", {}).get(dom),
        }
    return rule


# --------------------------------------------------------------------------- #
# Plotting (inputs are the small Step 2-6 tables only)
# --------------------------------------------------------------------------- #
def plot_loss_curves(rows_by_domain: dict[str, list[dict[str, Any]]],
                     results: dict[str, dict[str, Any]], path: Path) -> None:
    """Plot 1 — L_B and L_C vs tau per domain with each loss's tau* marked."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=True)
    for ax, dom in zip(axes, DOMAINS):
        rows = rows_by_domain[dom]
        mults = [r["multiplier"] for r in rows]
        lb = [loss_b_value(r, ALPHA0) for r in rows]
        lc = [loss_c_value(r) for r in rows]
        ax.plot(mults, lb, "o-", label="Loss B (scalar)", color="tab:blue")
        ax.plot(mults, lc, "s-", label="Loss C (Bayes risk)", color="tab:green")
        res = results[dom]
        colors = {"tau_star_A": "tab:red", "tau_star_B": "tab:blue", "tau_star_C": "tab:green"}
        for key, col in colors.items():
            tau = res.get(key)
            if tau is not None:
                ax.axvline(tau, color=col, ls="--", alpha=0.6,
                           label=f"{key.split('_')[-1]}*={tau:g}")
        ax.set_title(f"{dom} (verdict: {res.get('consistency_verdict', 'NA')})")
        ax.set_xlabel("L5 threshold multiplier tau")
        ax.set_ylabel("loss value")
        ax.legend(fontsize=7)
    fig.suptitle("EXP-011 Plot 1 — Loss vs tau-frontier per domain", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_frontier(rows_by_domain: dict[str, list[dict[str, Any]]],
                      results: dict[str, dict[str, Any]], path: Path) -> None:
    """Plot 2 — MDE-vs-tau step per domain + materiality line + sub-material shading + tau*."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, dom in zip(axes, DOMAINS):
        rows = rows_by_domain[dom]
        mults = np.array([r["multiplier"] for r in rows])
        mde = np.array([r["mde_bps"] for r in rows])
        sub = np.array([r["sub_rate"] for r in rows])
        ax.step(mults, mde, where="mid", color="tab:gray", zorder=1)
        sc = ax.scatter(mults, mde, c=sub, cmap="OrRd", vmin=0.0, vmax=1.0,
                        s=90, edgecolor="black", zorder=2)
        ax.axhline(MATERIALITY_BPS[dom], color="tab:blue", ls=":",
                   label=f"materiality = {MATERIALITY_BPS[dom]:g} bps")
        tau = results[dom].get("tau_star_headline")
        if tau is not None:
            ax.scatter([tau], [results[dom]["mde_bps"]], marker="*", s=320,
                       color="tab:red", edgecolor="black", zorder=3, label=f"tau* = {tau:g}")
        ax.set_title(dom)
        ax.set_xlabel("L5 threshold multiplier tau")
        ax.set_ylabel("economic MDE (bps)")
        ax.legend(fontsize=7)
        fig.colorbar(sc, ax=ax, label="sub-material rate")
    fig.suptitle("EXP-011 Plot 2 — MDE vs tau (sub-material shaded), headline tau* starred",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_consistency_matrix(results: dict[str, dict[str, Any]], path: Path) -> None:
    """Plot 3 — domain x loss selected tau*, cells coloured by per-domain verdict."""
    losses = ["tau_star_A", "tau_star_B", "tau_star_C"]
    color_by_verdict = {"ROBUST": 0.0, "LOSS_SENSITIVE": 1.0, "INCOMPLETE": 0.5, "NA": 0.5}
    grid = np.zeros((len(DOMAINS), len(losses)))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, dom in enumerate(DOMAINS):
        verdict = results[dom].get("consistency_verdict", "NA")
        grid[i, :] = color_by_verdict.get(verdict, 0.5)
        for j, key in enumerate(losses):
            tau = results[dom].get(key)
            label = f"{tau:g}" if tau is not None else "—"
            ax.text(j, i, label, ha="center", va="center", fontsize=12, fontweight="bold")
    ax.imshow(grid, cmap="RdYlGn_r", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(losses)))
    ax.set_xticklabels(["Loss A\n(primary)", "Loss B", "Loss C"])
    ax.set_yticks(range(len(DOMAINS)))
    ax.set_yticklabels([f"{d}\n({results[d].get('consistency_verdict','NA')})" for d in DOMAINS])
    ax.set_title("EXP-011 Plot 3 — Selected tau* by loss (green=ROBUST, red=LOSS_SENSITIVE)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_adoption_overlay(results: dict[str, dict[str, Any]], path: Path,
                          tokens: dict[str, str]) -> None:
    """Plot 4 — recommended pooled MDE at tau* vs per-instrument (EXP-008) and
    walk-forward (EXP-010) strict-gate MDEs + materiality line (adoption caveats)."""
    pi = (_read_summary(EXP008_PI_MDE).filter(
        (pl.col("referee") == REFEREE) & (pl.col("alpha") == ALPHA0))
        if tokens.get("EXP-008") == "COMPLETE" else None)
    wf = (_read_summary(EXP010_PROTO_MDE).filter(
        (pl.col("protocol") == "walk_forward") & (pl.col("referee") == REFEREE)
        & (pl.col("alpha") == ALPHA0))
        if tokens.get("EXP-010") == "COMPLETE" else None)

    fig, ax = plt.subplots(figsize=(9, 5))
    for x, dom in enumerate(DOMAINS):
        rec_mde = results[dom].get("mde_bps")
        if rec_mde is not None:
            ax.scatter([x], [rec_mde], marker="*", s=320, color="tab:red",
                       edgecolor="black", zorder=4,
                       label="recommended MDE at tau*" if x == 0 else None)
        if pi is not None:
            vals = pi.filter(pl.col("domain") == dom)["mde_bps"].to_list()
            ax.scatter([x] * len(vals), vals, marker="o", color="tab:purple", alpha=0.7,
                       zorder=3, label="per-instrument MDE (strict, EXP-008)" if x == 0 else None)
        if wf is not None:
            wv = wf.filter(pl.col("domain") == dom)["mde_bps"].to_list()
            if wv:
                ax.scatter([x] * len(wv), wv, marker="D", color="tab:orange", zorder=3,
                           label="walk-forward MDE (strict, EXP-010)" if x == 0 else None)
        ax.hlines(MATERIALITY_BPS[dom], x - 0.3, x + 0.3, color="tab:blue", ls=":",
                  label="materiality" if x == 0 else None)
    ax.set_xticks(range(len(DOMAINS)))
    ax.set_xticklabels(DOMAINS)
    ax.set_yscale("log")
    ax.set_ylabel("economic MDE (bps, log scale)")
    ax.set_title("EXP-011 Plot 4 — Adoption/robustness overlay (instrument & split caveats)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _write_csvs(decision: pl.DataFrame, recon: pl.DataFrame,
                results: dict[str, dict[str, Any]]) -> None:
    """Write the deterministic, sorted result tables."""
    decision.sort(["domain", "multiplier"]).write_csv(RESULTS_DIR / "decision_table.csv")
    recon.sort(["domain", "multiplier", "edge_bps"]).write_csv(
        RESULTS_DIR / "sub_material_by_tau.csv"
    )
    loss_rows = []
    rec_rows = []
    for dom in DOMAINS:
        res = results[dom]
        for loss in ("A", "B", "C"):
            sel = res.get(f"loss_{loss.lower()}", {})
            loss_rows.append({
                "domain": dom, "loss": loss, "selectable": sel.get("selectable"),
                "tau_star": sel.get("multiplier"), "loss_value": sel.get("loss_value"),
                "mde_bps": sel.get("mde_bps"), "sub_rate": sel.get("sub_rate"),
                "reason": sel.get("reason"),
            })
        rec_rows.append({
            "domain": dom, "status": res["status"],
            "tau_star_headline": res.get("tau_star_headline"),
            "mde_bps": res.get("mde_bps"), "sub_rate": res.get("sub_rate"),
            "materiality_limited": res.get("materiality_limited"),
            "tau_star_A": res.get("tau_star_A"), "tau_star_B": res.get("tau_star_B"),
            "tau_star_C": res.get("tau_star_C"),
            "consistency_verdict": res.get("consistency_verdict"),
            "index_spread": res.get("index_spread"), "driver_term": res.get("driver_term"),
        })
    pl.DataFrame(loss_rows).sort(["domain", "loss"]).write_csv(RESULTS_DIR / "loss_evaluation.csv")
    pl.DataFrame(rec_rows).sort("domain").write_csv(RESULTS_DIR / "recommendation.csv")


def main() -> None:
    """Run the EXP-011 predeclared-loss operating-point synthesis."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("=== EXP-011: Predeclared-Loss Operating-Point Synthesis ===")

    # Frozen-constant guard: materiality buffers must match the harness + scope.
    for dom in DOMAINS:
        if MATERIALITY_BPS[dom] != _EXPECTED_MATERIALITY[dom]:
            raise RuntimeError(f"materiality drift for {dom}: {MATERIALITY_BPS[dom]}")
        band = (MATERIALITY_BPS[dom], MATERIAL_BAND_MULT * MATERIALITY_BPS[dom])
        for e in GD_EDGES[dom]:
            if not band[0] <= e <= band[1]:
                raise RuntimeError(f"G_d edge {e} outside material band {band} for {dom}.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    tokens = gate_dependencies()
    logger.info("Dependency tokens: %s", tokens)

    mde = _read_summary(EXP006_MDE)
    fpr = _read_summary(EXP006_FPR)
    tpr = _read_summary(EXP006_TPR)
    exp007 = _read_summary(EXP007_SUBMAT)

    decision = build_decision_table(mde, fpr)
    recon = reconstruct_submaterial()
    repro_ok = check_submaterial_reproduction(recon, exp007)
    logger.info("Sub-material tau=0 reproduction vs EXP-007: %s", "PASS" if repro_ok else "FAIL")

    decision = attach_sub_rate(decision, recon, exp007)
    tpr_terms = build_tpr_terms(tpr)
    rows_by_domain = assemble_rows(decision, tpr_terms)

    results = {dom: evaluate_domain(rows_by_domain[dom]) for dom in DOMAINS}
    overlays = build_overlays(tokens)
    adoption_rule = build_adoption_rule(results, overlays)

    _write_csvs(decision, recon, results)
    write_json(RESULTS_DIR / "adoption_rule.json", adoption_rule)

    inconclusive = [d for d in DOMAINS if results[d]["status"] != "RECOMMENDED"]
    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "overall_status": "COMPLETE",
        "measurements_produced": True,
        "alpha0": ALPHA0,
        "frontier_multipliers": list(FRONTIER_MULTIPLIERS),
        "materiality_bps": MATERIALITY_BPS,
        "submaterial_limit": SUBMATERIAL_LIMIT,
        "gd_edges": {d: list(GD_EDGES[d]) for d in DOMAINS},
        "submaterial_repro_check": repro_ok,
        "dependency_tokens": tokens,
        "recommendation_by_domain": {
            d: results[d].get("tau_star_headline") for d in DOMAINS
        },
        "mde_by_domain": {d: results[d].get("mde_bps") for d in DOMAINS},
        "consistency_by_domain": {d: results[d].get("consistency_verdict") for d in DOMAINS},
        "materiality_limited_by_domain": {
            d: results[d].get("materiality_limited") for d in DOMAINS
        },
        "inconclusive_domains": inconclusive,
    })

    plot_loss_curves(rows_by_domain, results, PLOTS_DIR / "loss_vs_tau.png")
    plot_mde_frontier(rows_by_domain, results, PLOTS_DIR / "mde_vs_tau_frontier.png")
    plot_consistency_matrix(results, PLOTS_DIR / "consistency_matrix.png")
    plot_adoption_overlay(results, PLOTS_DIR / "adoption_overlay.png", tokens)

    logger.info("Recommendation by domain (headline tau* multiplier):")
    for dom in DOMAINS:
        res = results[dom]
        logger.info(
            "  %-3s status=%s tau*=%s MDE=%s sub=%.4f verdict=%s%s",
            dom, res["status"], res.get("tau_star_headline"), res.get("mde_bps"),
            res.get("sub_rate") if res.get("sub_rate") is not None else float("nan"),
            res.get("consistency_verdict"),
            " [materiality-limited]" if res.get("materiality_limited") else "",
        )
    logger.info("Outputs written to %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
