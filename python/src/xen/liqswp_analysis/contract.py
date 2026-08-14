"""Result and integrity contracts shared by EXP-101 through EXP-104."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


ZERO_COST_DISCLOSURE = {
    "heading": "ZERO-COST-DISCLOSURE",
    "cost_model": "NO_COST_CHARGED",
    "spread": "not modeled",
    "commissions": "not modeled",
    "swaps/funding": "not modeled",
    "implication": (
        "every figure in this document is gross and cost-free; no spread, commission, "
        "or swap enters any calculation. Realised results would differ (likely worse) "
        "under any real cost schedule."
    ),
    "prohibited_claims": "fully-net, cost-complete, tradable, deployable",
    "lifting": (
        "only an explicit operator directive may introduce a cost model for a scoped "
        "experiment; the directive is recorded in that experiment's design.md."
    ),
}


@dataclass(frozen=True)
class IntegrityStatus:
    """Hard data-validity result; never an economic verdict."""

    blocking_pass: bool
    reasons: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return {
            "blocking_pass": bool(self.blocking_pass),
            "reasons": list(self.reasons),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class AnalysisResult:
    """Complete neutral result with fail-closed value-row suppression."""

    experiment: str
    source: Mapping[str, Any]
    population: Mapping[str, Any]
    integrity: IntegrityStatus
    value_rows: tuple[Mapping[str, Any], ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""
        return {
            "experiment": self.experiment,
            "source": dict(self.source),
            "population": dict(self.population),
            "integrity": self.integrity.to_dict(),
            "value_rows": [dict(row) for row in self.value_rows]
            if self.integrity.blocking_pass
            else [],
            "extra": dict(self.extra),
            "zero_cost_disclosure": dict(ZERO_COST_DISCLOSURE),
        }
