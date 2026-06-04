# Experiment Report: EXP-010 - Split-Protocol Robustness of the Referee

## Status: PARTIALLY REFUTED

**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain)
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; regenerated known-null and known-positive referee-calibration draws; no chart-type views

---

## Question

Do alternative within-analysis-set split protocols materially change the frozen referee's pooled-by-domain operating characteristics versus the mandated single chronological split?

## Hypothesis

H-split: anchored walk-forward and purged/embargoed CV do not materially change gate-stack FPR or economic MDE versus the single chronological split, under the frozen criterion.

## Method Summary

EXP-010 regenerated EXP-003-style null and positive draws with a reduced draw budget held constant across protocols. It evaluated the frozen referees under single split, anchored walk-forward, and purged/embargoed CV. Fold boundaries were mapped from shared 1-minute `CloseTime` coordinates into each domain, and the amended multi-fold wrapper evaluated the referee per fold with disjoint fold train/test sets before combining one verdict per draw.

## Key Findings

### Finding 1: The Single-Split Reference Reproduced EXP-003

The single-split arm passed every reference check: FPR intervals overlap EXP-003 and MDEs match within grid uncertainty across all 9 domain/alpha rows. This validates the regenerated substrate and wrapper for protocol comparison.

### Finding 2: FPR Was Stable

At `alpha0=0.05`, gate-stack FPR was `0/2000` for every domain/protocol, with Wilson half-width `0.000959`.

![FPR by protocol](plots/fpr_by_protocol.png)

### Finding 3: Walk-Forward Materially Raised MDE on 1h and 4h

Anchored walk-forward changed MDE materially on slower domains:

- 1h: single `4.0` bps -> walk-forward `8.0` bps; margin `0.8` bps.
- 4h: single `12.0` bps -> walk-forward `24.0` bps; margin `2.4` bps.

Purged CV matched the single split on all domains, and 5m stayed at `1.0` bps under every protocol.

![MDE by protocol](plots/mde_by_protocol.png)

## Conclusion

**Hypothesis PARTIALLY REFUTED.**

H-split is supported on 5m, but falsified on 1h and 4h because anchored walk-forward materially increases the gate-stack economic MDE while FPR remains controlled. The split protocol itself can move measured sensitivity on slower domains. EXP-010 does not recommend a split change; it supplies robustness context for EXP-011.

## Limitations

- Draw counts are reduced versus EXP-003 for tri-protocol tractability, though all alpha0 reportability targets pass.
- The multi-fold wrapper is experiment-local and guarded by the single-split reproduction check.
- The result applies to the frozen synthetic calibration substrate, not real strategy candidates.

## Implications for Future Research

- EXP-011 should treat 1h/4h walk-forward MDE sensitivity as a robustness penalty or context item.
- Purged CV matching single split suggests the issue is specific to anchored walk-forward, not any alternative split protocol.

## Recommended Next Experiments

1. **EXP-011**: Incorporate split-protocol robustness into the predeclared loss-function synthesis.
2. **Phase 003 decision phase**: If a split-policy change is proposed, ratify it separately on fresh draws.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Raw Results | [results/](results/) |
| Plots | [plots/](plots/) |
