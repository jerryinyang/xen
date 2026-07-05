# Phase 005 — CF-MR-005 Ladder-Harvest Mechanism Characterisation (Chapter 02)

**Status:** G0 RATIFIED (2026-07-03, operator decisions D2/D3). **Chapter:** 02
(cTrader-primary era). **Prior phase:** 004 CLOSED (CF-MR-004 RETIRED 2026-07-03;
[retrospective](../2026-07-01-004-cross-domain-mr-renewal/retrospective.md)).
**Family:** CF-MR-005 — `docs/signal-registry/candidate-families/cf-mr-005.md` (REGISTERED
2026-07-03). **Origin:** EXP-014c extend-arm field discovery; operator decision record
`.ignore/temp/d1/exp-014c-findings-and-decisions.md` (D1–D6, binding).

## Context — where the programme is

Phase 004 retired CF-MR-004 on a credible negative (entry-seam mismatch; exits exonerated) but
surfaced a robust unclaimed phenomenon: **61 EXP-014c cells with net ci_low > 0 (53 never
Holm-admitted), exclusively extend/allow arms, both z\*, all four exit sets, year-stable
2021–2024, 50–85% surviving the 60h basket phase-shift** — a 4h ladder scale-in harvesting
short-horizon **own-price** mean reversion (the basket supplied a trigger, not the harvest).
Inadmissible as CF-MR-004 evidence (attribution); registered as its own family (D2).

**Honest prior: MODERATE for the mechanism, LOW for eventual tradability.** The field evidence is
engine-realized and cross-instrument, but CF-MR-001/002/003 all died on cost-vs-capture, US2000
fails at 2× cost, and the scale-in carries an unmeasured left tail (the martingale-flavored
component is short a tail the 5y window may not contain).

## Objective

**O1 — Mechanism characterisation (TRAIN, analysis-only).** Under a **basket-free** own-price
dislocation trigger, does 4h price revert toward a frozen ≤t-1 anchor beyond a
dislocation-matched control, per instrument, **monotonically in depth**, over the ladder-relevant
horizon — and is the engine-observed extend-arm P&L attributable to that depth-graded reversion
rather than to drift, short-vol exposure, or a few tail episodes? → **EXP-015**
(`python/experiments/EXP-015/design.md`, CF-MR-005/HYP-001).

Outcomes (frozen in EXP-015 §5): MECHANISM_SUPPORTED → HYP-002 tradability D0 (price-primary,
separate scope); EXPOSURE_ARTIFACT → family retires; TAIL_FUNDED → HYP-002 only with a
predeclared tail budget; UNPOWERED/INCONCLUSIVE → operator routing.

## Ratified constraints (operator D2/D3 + registry first-branch, binding)

| # | Constraint | Source |
|---|---|---|
| 1 | Basket-free trigger (own-price only; S8 spread is CF-MR-004 property) | D2; `cf-mr-005.md` #1 |
| 2 | Mechanism before any tradability claim; no exit design anywhere (P-02) | D2; `cf-mr-005.md` #2/#4 |
| 3 | Analysis-only phase — no new emissions, no vectorized strategy backtest (L-01); P&L anatomy exclusively from existing EXP-014b/c engine fills, read-only | EXP-015 classification |
| 4 | Attribution controls disclose collapse fractions, never binary-only (**L-15**) | D5; `lessons-and-amendments.md` L-15 |
| 5 | Phase-shift-control semantics study **deferred** behind this characterisation | D3 |
| 6 | Ladder-native availability object (fraction-of-dislocation recovered), not the two-barrier race (L-13) | `cf-mr-005.md` #5 |
| 7 | Cost realism disclosed early ({1,2,3}× stress), binding at HYP-002 | `cf-mr-005.md` #3 |
| 8 | Left-tail exposure quantified (episode-level, top-k sensitivity, bin-4 non-recovery census) | D2; `cf-mr-005.md` #2 |

## Sequencing (gates)

1. **G0 (this checkpoint):** ratified via operator D2/D3 + CF-MR-005 registration; 0 slots, 0 reads.
2. **EXP-015 Stage 1:** design complete, inline pre-exec **GATE: APPROVE** (2026-07-03).
3. **Stages 2–5:** implement → execute (local, analysis-only — no credentialed runs) → audit
   (uncapped; provenance re-assertion on every emission read) → report + registry/index updates.
4. **Phase close:** retrospective; routing per EXP-015 §5 outcome. HYP-002 (tradability,
   price-primary, native cTrader ladder) requires its **own D0 and phase** — never opened inside
   this one.

## Hard guards (binding)

- Final-30% holdout sealed; fence = EXP-013 first-49% TRAIN cutoffs verbatim (assert per cell).
- 0 candidate slots, 0 counted TEST reads (TRAIN-only characterisation).
- Frozen referee untuned and not the binding instrument (L-12); interpretation criteria frozen in
  EXP-015 §5 before results.
- All event logic ≤ t-1, open-to-open, action-bar open; block-permute leak tripwire (L-07) with
  collapse fractions (L-15); no signal-derived-target null (L-08); per-stratum verdicts (L-03).
- Emissions read-only; per-cell EXP-014c statuses stand (D4).

## Success criteria (O1)

Phase succeeds if EXP-015 delivers a **decisive per-cell characterisation** under the frozen
criteria — supported, artifact, tail-funded, or powered-inconclusive — with every read
per-stratum, controls collapse-fraction-disclosed, and the HYP-002 go/no-go derivable mechanically
from EXP-015 §5. A clean EXPOSURE_ARTIFACT retire is a success, not a failure.
