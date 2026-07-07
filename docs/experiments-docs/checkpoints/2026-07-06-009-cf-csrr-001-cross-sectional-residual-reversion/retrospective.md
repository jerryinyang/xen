# Checkpoint 009 Retrospective — CF-CSRR-001 Disposition (2026-07-07)

**Family disposition: CF-CSRR-001 RETIRED** — operator-signed, 2026-07-07, on tested evidence
(EXP-021 + EXP-022 + EXP-024 all NOT SUPPORTED at availability), not upstream disqualification.
Retirement at **0 slots / 0 counted TEST reads**, holdout sealed. This is the checkpoint design's
pre-declared exit-condition outcome (a): *substrate reverts but no construction separates → RETIRE
at 0 cost.* The model-selection gate was never met, so the validatory tier (EXP-023) and the
pre-declared confirmatory read (HYP-004) were never scoped or spent.

## Phase outcome vs objectives

| Objective (design §Phase objectives) | Outcome |
|---|---|
| 1. Substrate (EXP-021 Currencies) | **MET — reverts.** VR(2)<1 on 28/28 4h cells (median 0.87, HL~1.4), VR<1 on 1D. |
| 2. Component characterisation (EXP-021 primary) | **NOT SUPPORTED.** 0 hedged (mechanism-faithful) cells survive the max-stat multiplicity on any instrument; sole family-wise survivor AUDUSD *unhedged* +9.4 bps = market drift (hedged twin fw_p .68). |
| 3. Indices mirror (EXP-022, VAL-007-gated) | **NOT SUPPORTED.** Substrate reverts (VR(2)<1 on 40/40); 0/74 powered cells clear ci_low>0; max-stat 0/9 instruments fw_p<.05 (best JP225 .33). Addendum A1 powered HK50 → clean null; US-cash NOT-SUPPORTED generalises. |
| — Controlled follow-up (EXP-024, US-bloc USTEC re-test) | **NOT SUPPORTED.** No member clears the hardened CI at the binding all>k/hedged cell; single-worst reproduces EXP-022's USTEC pattern (p_perm 0.009, hardened ci_low −1.15) → effect-at-MDE, USTEC-specific. Lead retired at 0 cost. |
| 4. Construct one model | **NOT REACHED** — the selection gate (a mechanism-faithful construction clearing multiplicity on ≥1 basket) was never met. |
| 5. Validate tradability (EXP-023) | **NOT SCOPED** — no model to validate. |
| 6. Disposition at retrospective | **RETIRED** (this document). |

## Basis for retirement

1. **The mechanism-faithful (hedged) construction never separates on either basket.** The thesis
   is idiosyncratic (consensus-hedged) reversion; on both the Currencies USD-strength basket
   (EXP-021) and the native single-factor equity basket (EXP-022) the hedged cells fail the
   multiplicity-adjusted permuted-axis null at the realized cell count (Currencies 0/7 survive;
   Indices 0/9 instruments fw_p<.05). What positive signal exists is **unhedged market drift**
   (AUDUSD +9.4 bps unhedged, hedged twin dead), not cross-sectional residual reversion.
2. **The single strongest lead is effect-at-MDE, not a hardened edge.** The EXP-022 USTEC lead
   (R_US bloc, session-open anchor) was the best-of-basket disclosed candidate. The pre-registered
   controlled re-test (EXP-024) resolved its open question decisively: powering via all>k *diluted*
   the per-event effect from +4.26 to +1.08 bps (to the MDE), and the exact single-worst form
   reproduced the pattern (p_perm 0.009) but still failed the hardened block-boot CI (ci_low −1.15)
   — at the selection that maximises it. Real, reproducible, USTEC-specific i→i linkage sitting at
   the detection floor; no sibling reproduces it. Not a bloc mechanism, not a tradable edge.
3. **Substrate reverting is necessary, not sufficient.** Both baskets confirm the residual
   mean-reverts (VR<1, short HL). The family dies on the *availability* leg — fading the
   dislocation does not earn an idiosyncratic forward return that clears the honest bar — exactly
   the predeclared "no combination separates from both twins → retire" kill criterion.
4. **Integrity clean throughout.** Leak tripwire collapses (ρ→0) on all three experiments; holdout
   sealed (first-49% load, final-30% never touched); causal ≤t-1 provenance + open-to-open;
   no local accounting (canonical `xen.evaluation` only); 0 slots, 0 counted TEST reads.

Family arc for the record: checkpoint-009 opened on the cross-sectional / relative-value cell of
the availability 2×2 (the open frontier after own-price directional reversion closed with
CF-MR-002..005) → EXP-021 Currencies NOT SUPPORTED (drift, not hedged reversion) → EXP-022 Indices
NOT SUPPORTED (0/9 fw_p, US-cash generalised via Addendum A1) → EXP-024 controlled USTEC re-test
NOT SUPPORTED (effect-at-MDE). No model selected; EXP-023/HYP-004 never scoped.

## Lessons (carried; KB lesson-candidate flagged)

- **Lesson-candidate (KB intake):** a substrate that reverts (VR<1) is not a signal — the
  availability leg (does fading the dislocation earn a hedged forward return that clears the honest
  CI) is the binding test, and it failed on both baskets. Do not read a VR<1 substrate as a
  candidate edge. Extends the L-11 wash discipline to cross-sectional residuals.
- **Controlled-thesis-shopping worked as designed.** The EXP-022 USTEC lead was pursued only as a
  pre-registered, frozen-construction, in-sample-honest re-test with the binding bar = the CI it
  previously failed. It resolved the underpowered-vs-effect-at-MDE question cleanly and retired the
  lead at 0 cost — the intended function of the registration guard (KB `controlled_thesis_shopping_allowed`).
- **Cost model corrected this checkpoint (2026-07-07, out-of-band):** `round_trip_cost_bps`
  flat_USD/percent/currency-aware-notional fixes + the netted-turnover requirement (see KB
  `evaluation-framework.md` § Trading-cost model). Not verdict-material here (availability tiers
  apply no cost), but it is now the standing cost basis for any future tradability tier.

## What is closed / what remains open

- **Closed:** CF-CSRR-001 (this family). The cross-sectional consensus-residual **reversion**
  thesis has now failed availability on both registered baskets and on the controlled USTEC
  re-test. With CF-MR-002..005 (own-price directional reversion) and CF-XSECT-001 (directional
  relative-strength) already retired, the availability 2×2's reversion cells are exhausted in the
  tested form-space.
- **Open, unregistered (disclosed leads, NOT booked):** AUDUSD / USDCAD (FX, EXP-021) and the
  USTEC R_US/session-open form (retired as effect-at-MDE, EXP-024). Pursuing any of these requires
  a fresh family registration with a genuinely new mechanism/target — not a re-open of CF-CSRR-001.
  A within-basket structure that clears the honest CI on unseen data would be a NEW family.

## Registry actions (sanctioned by this retrospective)

- `candidate-families/cf-csrr-001.md` status → **RETIRED (2026-07-07, operator-signed,
  checkpoint-009)**; HYP-001 row corrected to COMPLETED — NOT SUPPORTED (was stale REGISTERED);
  HYP-003/EXP-023 and HYP-004 marked NOT SCOPED / never spent (no reads, no slots).
- `multiplicity-registry.md`: CF-CSRR-001 Registration status → **RETIRED**; HYP-001/002/002b rows
  already SCREENED/COMPLETED NOT SUPPORTED; HYP-003/004 → NOT SCOPED (0 reads, 0 slots).
- `docs/experiments-docs/INDEX.md`: Phase-009 header → CLOSED — RETIRED; family-status table row
  updated.
- `families/cf-csrr-001/INDEX.md`: status line → RETIRED (checkpoint-009 retrospective).

**Signed:** operator (verdict + closure instruction, 2026-07-07); recorded by research-pipeline
orchestrator.
