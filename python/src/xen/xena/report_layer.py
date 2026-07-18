"""Reusable report-layer schema + renderer (INFR-016).

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

``interpretation_label`` is a scanning aid ONLY (INFR-016 §8): the design §9-style bands
survive as descriptive labels on a layer, never as gates or drops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Descriptive labels only — never a gate (INFR-016 §8). Auto-derivation is limited to the two
# STRUCTURAL labels (UNPOWERED / CONTRADICTED via structural_label); STRONG/SUPPORTED/SUGGESTIVE/
# WASH remain valid **operator-supplied** tags but are no longer machine-assigned from a
# p-cutpoint (that re-imported the L-32 trap — see structural_label).
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


def structural_label(*, powered: bool, directional_positive: bool) -> str | None:
    """Return ONLY the two labels that are facts about the estimator, not a p-cutpoint.

    ``UNPOWERED`` encodes too-few-seeds (a fact about resolving power); ``CONTRADICTED``
    encodes the wrong sign (a fact about direction). Otherwise **None** — the operator reads
    the observed number + one-sided p + CI directly.

    INFR-016 originally also auto-mapped a one-sided p to STRONG/SUPPORTED/SUGGESTIVE/WASH via
    hardcoded cutpoints (0.05/0.15/0.35). That re-imported the exact L-32 defect in miniature:
    a hardcoded-threshold label reads as a verdict (SOL at p=0.224 → "SUGGESTIVE" would flip to
    "WASH" at p=0.36 on a cutpoint no more justified than the retired P95). The honest read is
    already the number + p + CI; the p-band labels are dropped (INFR-016 follow-up, 2026-07-19).
    """
    if not powered:
        return "UNPOWERED"
    if not directional_positive:
        return "CONTRADICTED"
    return None


def power_layer(candidate_id: str, *, n_legs: int, per_leg_vol_bps: float,
                mde_bps: float, observed_edge_bps: float | None = None) -> LayerReport:
    """Leg-count / power as a REPORT layer — retires the ``n_legs_floor`` in-domain veto.

    Reports n_legs, per-leg vol, and the MDE (minimum detectable edge) so the operator sees
    the resolving power. **Never a floor veto**: a thin-leg candidate is labelled UNPOWERED,
    not dropped (INFR-016 §4b). ``powered`` iff a supplied observed edge exceeds the MDE.
    """
    powered = observed_edge_bps is not None and abs(observed_edge_bps) >= mde_bps
    _interp_unused = None  # noqa: F841 — placeholder anchor (kept minimal)
    interp = (f"{n_legs} legs, per-leg vol {per_leg_vol_bps:.1f} bps, MDE {mde_bps:.1f} bps — "
              + ("enough legs to resolve the observed edge" if powered else
                 "too few legs / too much per-leg vol to resolve an edge this size — underpowered"))
    return LayerReport(
        layer="leg_power", candidate_id=candidate_id,
        observed=f"n_legs={n_legs}, MDE={mde_bps:.1f} bps",
        ideal_range="MDE ≤ the observed edge (enough legs to resolve it)",
        interpretation=interp,
        interpretation_label=None if powered else "UNPOWERED",
        supporting={"n_legs": int(n_legs), "per_leg_vol_bps": float(per_leg_vol_bps),
                    "mde_bps": float(mde_bps),
                    "observed_edge_bps": (None if observed_edge_bps is None
                                          else float(observed_edge_bps)),
                    "powered": bool(powered),
                    "note": "power reported, never a floor veto (retires n_legs_floor)"},
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
