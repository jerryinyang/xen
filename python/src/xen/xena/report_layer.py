"""Reusable report-layer schema + renderer (INFR-016; INFR-022 powering strip).

Every value / quality / significance / selection read in the XENA value chain is a
**report layer**, never a gate. A layer runs for **all authorised candidates**, drops
nothing, and emits — per candidate — exactly:

    observed result          = ###
    ideal range              = ###   (practical real-world expectation, not perfection)
    realistic interpretation = <plain language; no verdict>

The operator reads the layers and authorises which candidates advance. No module in the
value chain returns a value auto-verdict: a :class:`LayerReport` carries **no** ``pass`` /
``blocking_pass`` / ``passed`` field. (Data-VALIDITY attestations — holdout fence, causal
provenance, estimand reconciliation, future-destroy leak survival — are a different layer and
keep their blocking semantics; see INFR-016 design §4a/§4c.)

INFR-022 (powering strip, L-63/N11): ``power_layer`` (MDE-based) is replaced by
``sample_size_layer`` — n_legs, per-leg vol and a design minimum-n **note** only; no MDE,
no ``powered`` boolean, no UNPOWERED label, no hide. ``structural_label`` and every machine
auto-assignment of interpretation labels are **deleted**: STRONG/SUPPORTED/SUGGESTIVE/WASH
(and UNPOWERED/CONTRADICTED) exist only as **operator-supplied tags** (N11) — never machine
fields, never gates. ``psr_layer`` pairs PSR + n beside a mean-trade (bps) read (directive 4).

``interpretation_label`` is a scanning aid ONLY (INFR-016 §8): the design §9-style bands
survive as descriptive labels on a layer, never as gates or drops.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

# Operator-supplied tags only (INFR-022 N11) — NEVER machine-assigned, NEVER gating.
# Machine auto-derivation of structural labels (UNPOWERED / CONTRADICTED) is deleted;
# the operator may optionally tag a layer with plain-language interpretation after reading
# numbers (STRONG/SUPPORTED/SUGGESTIVE/WASH/UNPOWERED/CONTRADICTED).
InterpretationLabel = Literal[
    "STRONG", "SUPPORTED", "SUGGESTIVE", "WASH", "UNPOWERED", "CONTRADICTED",
]
VALID_LABELS: frozenset[str] = frozenset(
    ("STRONG", "SUPPORTED", "SUGGESTIVE", "WASH", "UNPOWERED", "CONTRADICTED"))

# Fields a report layer must NEVER carry — enforced by _forbid_verdict_keys so no value read
# can smuggle an auto-verdict back in.
_FORBIDDEN_KEYS: frozenset[str] = frozenset(
    ("pass", "passed", "blocking_pass", "hard_fail", "hard_fail_leak", "reject",
     "at_or_above_p95", "at_or_above_p99"))


def _forbid_verdict_keys(supporting: dict[str, Any]) -> None:
    bad = sorted(k for k in supporting if k.lower() in _FORBIDDEN_KEYS)
    if bad:
        raise ValueError(
            f"report layer supporting-dict carries auto-verdict key(s) {bad}; report "
            "layers describe, they never decide (INFR-016 §3)")


@dataclass(frozen=True)
class LayerReport:
    """One (layer x candidate) report row. Describes; never decides.

    ``observed``/``ideal_range`` are free-form (a number, a tuple, a short string) so any
    layer can express its native quantity; ``interpretation`` is a plain sentence with no
    verdict. ``supporting`` holds the raw backing numbers and must not contain a verdict key.
    """
    layer: str
    candidate_id: str
    observed: Any
    ideal_range: Any
    interpretation: str
    interpretation_label: str | None = None
    supporting: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.interpretation_label is not None and self.interpretation_label not in VALID_LABELS:
            raise ValueError(
                f"interpretation_label {self.interpretation_label!r} not in {sorted(VALID_LABELS)}")
        _forbid_verdict_keys(self.supporting)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "candidate_id": self.candidate_id,
            "observed": self.observed,
            "ideal_range": self.ideal_range,
            "interpretation": self.interpretation,
            "interpretation_label": self.interpretation_label,
            "supporting": dict(self.supporting),
            # explicit, so any downstream reader sees the invariant, not just its absence:
            "is_gate": False,
        }


def sample_size_layer(candidate_id: str, *, n_legs: int, per_leg_vol_bps: float,
                      design_min_n: int | None = None) -> LayerReport:
    """Sample-size CONTEXT as a REPORT layer (INFR-022 L-63 — replaces ``power_layer``).

    Reports n_legs, per-leg vol, and (optionally) the design's pre-declared minimum-n
    for *primary-inference language* — descriptive only: the row, estimate, interval and
    n all still appear; a small-n row is never hidden, dropped, or labelled UNPOWERED
    (N3/N10). No MDE, no ``powered`` boolean, no detection floor.
    """
    note = (f"design minimum-n {design_min_n} for primary-inference language — descriptive "
            "only, never a hide/drop rule (N3)" if design_min_n is not None else
            "no design minimum-n declared — all rows reported with their counts; "
            "sample-size notes are descriptive only, never a hide/drop rule (N3)")
    interp = (f"{n_legs} legs, per-leg vol {per_leg_vol_bps:.1f} bps — sample-size context; "
              "report alongside the estimate and its uncertainty (operator reads the numbers)")
    return LayerReport(
        layer="sample_size", candidate_id=candidate_id,
        observed=f"n_legs={n_legs}, per-leg vol={per_leg_vol_bps:.1f} bps",
        ideal_range="sufficient event count for the operator's own reading of the estimate",
        interpretation=interp,
        interpretation_label=None,
        supporting={"n_legs": int(n_legs), "per_leg_vol_bps": float(per_leg_vol_bps),
                    "design_min_n": (None if design_min_n is None else int(design_min_n)),
                    "note": note},
    )


def psr_layer(candidate_id: str, *, avg_trade_bps: float, psr: float, n: int) -> LayerReport:
    """PSR pairing layer (INFR-022 §4.2): Probabilistic Sharpe Ratio + n beside the mean
    per-trade (bps) figure, on the SAME trade series and population. Evidence, never a gate;
    NaN psr with n stated when n < 2 or moments non-finite (N3 — the row still appears)."""
    interp = (f"PSR {psr:.3f} over n={n} trades beside avg-trade {avg_trade_bps:.2f} bps "
              "(skew/kurt-adjusted; same series as the mean)" if math.isfinite(psr) else
              f"PSR undefined (n={n}) — reported with its count, not suppressed")
    return LayerReport(
        layer="psr", candidate_id=candidate_id,
        observed=f"avg_trade_bps={avg_trade_bps:.2f}, PSR={psr:.3f}, n={n}",
        ideal_range="PSR beside every mean-trade bps read (same series)",
        interpretation=interp,
        interpretation_label=None,
        supporting={"avg_trade_bps": float(avg_trade_bps), "psr": float(psr), "psr_n": int(n)},
    )

def stage2_bounds_layer(candidate_id: str, *, lcb: float, ucb: float, n_legs: int,
                        net: bool = False) -> LayerReport:
    """Stage-2 lower/upper bound for ONE subset/cell as a REPORT layer.

    Called for **every** certified subset AND per-cell (retires ``one_subset`` top-1 hiding,
    INFR-016 §4b): build one of these per candidate and render them together so nothing is
    hidden. Reports the studentized LCB/UCB; the operator judges — no certify/reject.
    """
    scale = "net" if net else "gross"
    directional = lcb > 0
    interp = (f"{scale} 95% bounds [{lcb:.2f}, {ucb:.2f}] bps over {n_legs} legs — "
              + ("lower band above zero" if directional else
                 "lower band spans zero — edge not resolved above zero"))
    return LayerReport(
        layer=f"stage2_bounds_{scale}", candidate_id=candidate_id,
        observed=f"LCB {lcb:.2f}, UCB {ucb:.2f} bps",
        ideal_range="lower bound (LCB) above zero at the traded scale",
        interpretation=interp,
        interpretation_label=None,
        supporting={"lcb": float(lcb), "ucb": float(ucb), "n_legs": int(n_legs),
                    "scale": scale,
                    "note": "reported for ALL subsets/cells (retires one_subset top-1)"},
    )


def render_layer_table(layer: str, reports: list[LayerReport]) -> str:
    """Render one layer's rows across ALL candidates as an operator-facing markdown table.

    Columns are exactly the §3 framing: ``candidate | observed | ideal | interpretation``
    (+ label). No pass/fail column — there is none to render.
    """
    rows = [r for r in reports if r.layer == layer]
    head = (f"### Layer: {layer}\n\n"
            "| candidate | observed | ideal range | interpretation | label |\n"
            "|---|---|---|---|---|\n")
    if not rows:
        return head + "| _(no authorised candidates)_ | — | — | — | — |\n"
    body = "".join(
        f"| {r.candidate_id} | {r.observed} | {r.ideal_range} | {r.interpretation} | "
        f"{r.interpretation_label or '—'} |\n"
        for r in rows)
    return head + body


def render_all_layers(reports: list[LayerReport]) -> str:
    """Render every layer (in first-seen order) as stacked tables — the full operator read."""
    order: list[str] = []
    for r in reports:
        if r.layer not in order:
            order.append(r.layer)
    return "\n".join(render_layer_table(layer, reports) for layer in order)
