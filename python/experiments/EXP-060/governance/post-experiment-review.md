# Post-Experiment Governance Review: EXP-060 — Combined Event System

**Reviewer**: Pipeline agent (automated)
**Date**: 2026-06-17
**Stage**: 8 (Post-execution)
**Predecessor review**: [pre-execution-review.md](pre-execution-review.md) — Stage 4 APPROVE

## Review Scope

This review checks whether EXP-060 was executed faithfully to its approved scope and analysis plan, whether the audit and results document are consistent, and whether the registry disposition is correct. It does not re-run the experiment or re-audit the code.

## Pass/Fail Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| Scope compliance | PASS | 5 arms × 99 cells; champion A3 (V2A × ADV-NONE) binding; 2×2 factorial for decomposition; disclosed A4 sibling (floor=48). All 99 cells reportable. |
| Analysis-plan fidelity | PASS | P14 median endpoint, P15 fills, regime-clustered MBB, two-baseline IUT conjunction (matched-random + MA(20,50)). Composition readout via `composition_readout.json`. |
| Audit verdict | PASS | 0 Critical, 0 Warning, 4 Info. 99/99 EXP-053 reconciliation (diff=0.0), 17/17 determinism replay, 0 causality violations, 0 invariant failures. |
| Results interpretation | PASS | `composition_readout.json` verdict `CHARACTERISED_NOT_VIABLE_ELIGIBLE` is consistent with 0 champion_wins. Key findings documented: substrate property (MA baseline unreachable for ZigZag entries), additive but not synergistic geometric levers. |

## Scope Compliance Check

- **Instruments**: all 17 VAL-003-admitted instruments — COMPLIANT. DE30 truncated-coverage disclosure present.
- **Cells**: 99 member cells (3 COVERAGE_EXCLUDED from EXP-048) — COMPLIANT.
- **Data Views**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for detection only — COMPLIANT.
- **Arms**: A0 BENCH, A1 50PCT-NONE, A2 V2A-1TO1, A3 V2A-NONE (champion, binding), A4 V2A-NONE-T48 (disclosed) — COMPLIANT.
- **Exclusions**: no costs, no `/STRONG-HA` filter, no `/VPTARGET`/`/MAGTARGET`, no combined trailing — COMPLIANT.
- **Slots/TEST reads**: 0 candidate slots, 0 TEST reads — COMPLIANT. Holdouts sealed.
- **Real-price discipline**: HA for detection only, all metrics on real OHLC — COMPLIANT.

## Analysis-Plan Fidelity Check

- **P14 endpoint**: median per-event ATR-normalised gross return — ADOPTED, correct per D0 addendum.
- **P15 fills**: path-ordered intrabar fill model — ADOPTED, correct per EXP-054 ratification.
- **Baselines**: matched-random via same-pipeline with identical events, MA(20,50) segmentation — ADOPTED, correct per P13.
- **Composition readout**: P11 (≥5 cells over ≥3 instruments) for champion_win (viable AND beats both baselines) — ADOPTED, correct.
- **Factorial decomposition**: 2×2 fav×adv with main effects and interaction — ADOPTED, correct per analysis plan §4.

## Consistency Check

- Audit.md PASS → `composition_readout.json` verdict `CHARACTERISED_NOT_VIABLE_ELIGIBLE` → results.md conclusion CHARACTERISED_NOT_VIABLE_ELIGIBLE — CONSISTENT.
- 0 champion_wins → composition_met=false → mechanical CHARACTERISED_NOT_VIABLE — CORRECT per 014-B design §8.
- 69/99 cells viable individually — consistent with conditioned-signal power (EXP-057 ADV-NONE showed similar breadth).
- Factorial additive pattern — consistent with independent lever architecture (EXP-056 and EXP-059 showed separate mechanisms).

## Registry Disposition Check

| Update | Correct? |
|--------|----------|
| `multiplicity-registry.md` HYP-013: CHARACTERISED_NOT_VIABLE_ELIGIBLE | YES |
| `candidate-families/harami.md` HYP-013 row and EXP-060 prose note | YES |
| `python/experiments/INDEX.md` EXP-060 row | YES |
| `docs/experiments-docs/INDEX.md` 014-B checkpoint: EXP-060 COMPLETE + G2 pending | YES |
| Family `cf-ha-harami-001/INDEX.md` EXP-060 card | YES |

## Assessment

EXP-060 was executed faithfully to its approved scope and analysis plan. The audit is clean. The results support the CHARACTERISED_NOT_VIABLE_ELIGIBLE verdict. The registry and indexes are correctly updated. The full 014-B surface is measured. The single G2 desk adjudication is the only remaining 014-B action.

**Verdict: APPROVE — pass to G2 desk adjudication.**

## G2 Context

The following items are sent to the operator desk for the single 014-B G2:

1. **Mechanical readout**: CHARACTERISED_NOT_VIABLE — 0 champion_wins, 0 cells beat MA(20,50) baseline.
2. **Discretionary override path per 014-B design §8**: operator may PROCEED_TO_SCREEN on any cell or combination despite mechanical failure.
3. **Key facts for adjudication**: 69/99 cells viable individually (CI_low>0); 3 beat matched-random; MA(20,50) dominance is a substrate property, not a signal weakness; both geometric levers (V2A, ADV-NONE) independently improve expectancy.
4. **Family disposition options**:
   - **(a) CHARACTERISED_NOT_VIABLE → family CLOSED**: programme routes per Phase 014 closure plan.
   - **(b) PROCEED_TO_SCREEN on ≥1 cell**: register candidate branch, begin EXP-027-analog calibration, requires Phase 015 D0.
   - **(c) SUBSTRATE-METHOD_DEFECT or INCONCLUSIVE**: per design, if operator determines the MA(20,50) baseline is not a fair comparator for ZigZag entries at programme composition scale.
