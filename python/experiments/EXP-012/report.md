# Experiment Report: EXP-012 - Fresh-Draw Loose Referee Ratification

## Status: SUPPORTED

**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; fresh synthetic known-null and known-positive draws; no chart-type views

---

## Question

Does the fixed EXP-011 loose referee point, tau 0.75 / 0.25 / 0.5 on 5m / 1h / 4h, earn adoption per domain on fresh seeds?

## Hypothesis

On each domain, the EXP-011-recommended loose operating point reproduces its Phase 002 operating characteristics on fresh synthetic draws: controlled FPR, MDE within one edge-grid step, sub-material pass rate within tolerance, and for 4h, split-protocol agreement.

## Method Summary

The script regenerated known-null and known-positive synthetic draws using fresh seed payloads disjoint from Phase 001/002 inputs. It measured loose and strict referee FPR/TPR/MDE, compared loose operating characteristics against Phase 002, and applied the predeclared per-domain adoption rule.

## Key Findings

### Finding 1: All Domains Adopt the Loose Point

`results/adoption_decisions.csv` reports `ADOPT_LOOSE` for 5m, 1h, and 4h. Every adoption component passed: FPR, MDE, sub-material rate, and the 4h split gate.

### Finding 2: Fresh Characteristics Reproduced Phase 002

At `alpha0 = 0.05`, loose FPR was `0/4000` in every domain. Fresh MDEs matched Phase 002 exactly: 5m `0.5`, 1h `2.0`, and 4h `8.0` bps. Sub-material rates were 5m `0.399139`, 1h `0.027469`, and 4h `0.0`, all within tolerance.

### Finding 3: 4h Split Gate Passed

The 4h loose MDE was `8.0` bps for both the single split and anchored walk-forward K=5, with FPR `0.0` in both protocols.

## Conclusion

**Hypothesis SUPPORTED.**

The fixed loose operating point is ratified on fresh seeds and adopted for all three domains. This freezes the second standalone screen for Phase 003 as tau 0.75/0.25/0.5 on 5m/1h/4h.

## Limitations

- Fresh draws use new synthetic seeds, not new market data.
- The result confirms the fixed EXP-011 point only; it does not reopen tau selection.
- The FPR and MDE adoption conditions had limited discriminating power (adversarial-review F05): fresh FPR was identically `0/4000` and the fresh MDE reproduced Phase 002 exactly, so adoption was effectively decided by the sub-material condition alone (5m 0.399 vs the 0.50 ceiling). Ratification confirms the point on fresh seeds; it does not stress-test it on FPR/MDE. See `results.md` Limitations.

## Implications for Future Research

- Later standalone candidate screens may report both strict and adopted-loose referee outputs.
- The loose point remains a per-candidate qualification screen, not a programme-level multiplicity control.

## Recommended Next Experiments

1. **Phase 004 registry design**: Before real signal exploration, define candidate registry and multiplicity controls.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
