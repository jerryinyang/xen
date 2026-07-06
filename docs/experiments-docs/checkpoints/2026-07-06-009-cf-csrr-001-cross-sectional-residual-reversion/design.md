# Checkpoint 009 — CF-CSRR-001 Cross-Sectional Consensus-Residual Reversion (2026-07-06)

**Phase container** for the first CF-CSRR-001 experiment set. Predecessor: checkpoint-008
(CF-VOLHARV-001 structure harvest — RETIRED; vol-harvest arc closed). Family card:
`docs/signal-registry/candidate-families/cf-csrr-001.md`. Origin (faithful variant provenance +
7-axis component decomposition): `docs/experiments-docs/families/cf-csrr-001/origin.md`.
Registration batch: `multiplicity-registry.md` → "Chapter 02 · CF-CSRR-001 Registration".

## Why this family, why this shape

The MR arc's post-mortem (`.ignore/temp/new-family/verdict.md`) established two things. (1) The
open frontier of the availability 2×2 is the **cross-sectional / relative-value** cell —
single-series directional price-geometry is dead twice over, and every own-price directional
reversion family (CF-MR-002..005) died at the cost/capture wall or the entry seam. (2) The
recurring killer was **passive-limit entry = adverse selection** (CF-MR-003/004 retired exactly
there). CF-CSRR-001 moves to a cross-sectional consensus-residual entry and, for tradability,
adopts an **active-entry / passive-exit** execution split that quarantines passive fills to the
favourable (reversion-arrives) side.

Five variants are registered — four suggested (r1-dlc S2, r4-tpg §2, r4-tpg closing obs, r2-ksd
I1) and one programme remodel (V5). They are not competing strategies to horse-race; they are
**one point each in a shared 7-axis component space** (A consensus estimator · B normalization ·
C selection · D hedge · E entry execution · F exit/stop · G threshold). The phase **characterises
each axis individually** and **constructs one model** from the observations — it does not pick a
variant by narrative.

Substrate is unproven here: MR is established on FX majors (own-price VR), but cross-sectional
*residual* reversion on either basket is untested. So the phase opens **availability-screen-first,
execution-agnostic**, and can retire the family cheaply if the residual does not revert.

## Phase objectives

1. **Substrate (EXP-021, disclosure):** is the aligned consensus-residual mean-reverting on the
   Currencies basket at 4h (VR<1 / residual autocorr<0)? A flat residual retires the arm.
2. **Component characterisation (EXP-021, primary):** across axes A×B×C×D, which construction
   maximises signal-conditional residual-reversion Δ over a matched **random-index + random-timing**
   twin, under a multiplicity-adjusted permuted-axis null at the realized cell count?
3. **Indices mirror (EXP-022, VAL-007-gated):** repeat (1)+(2) on the native single-factor equity
   basket once INFR-005/VAL-007 admits all 10 index symbols.
4. **Construct one model** from (2)+(3): the selected (A,B,C,D,G) construction + the V5 execution
   split — recorded and hash-pinned before any tradability read.
5. **Validate tradability (EXP-023):** the selected model, price-primary in cTrader with V5
   execution, **net of honest round-trip cost**, vs the three-twin battery + TRAIN block-bootstrap /
   both-halves robustness.
6. **Decide disposition at the retrospective:** retire, iterate a component, or authorise the
   pre-declared confirmatory TEST read (HYP-004) — operator-signed.

## Currencies consensus (binding, operator 2026-07-06)

The consensus-residual premise assumes one dominant common factor. The Currencies basket mixes
USD-quoted majors and JPY crosses (opposing USD exposure); a naive quote-median is factor-
incoherent. EXP-021 builds the consensus on a **USD-strength alignment** (legs signed to a common
USD factor; JPY crosses decomposed to USD legs where possible). If the aligned residual is not
mean-reverting, the Currencies arm dies in EXP-021. A naive-median contrast is disclosure-only.

## Exploratory / validatory / confirmatory staging (operator 2026-07-06)

| Tier | Experiments | Reads | Gate |
|---|---|---|---|
| **Exploratory** | EXP-021 (Currencies), EXP-022 (Indices, VAL-007-gated) | 0, TRAIN-only | availability + component characterisation → select one model |
| **Validatory** | EXP-023 (selected model tradability) | 0, TRAIN-only | net-of-cost + three-twin battery + robustness |
| **Confirmatory** | HYP-004 (pre-declared, **not scoped this checkpoint**) | 0 now; ≤1 counted read later | authorised only if EXP-023 clears the family-card gate; hash-pin first |

## Planned work

| Item | What | Gate |
|---|---|---|
| EXP-021 | HYP-001 Currencies availability + A×B×C×D component screen (USD-strength consensus; random-index + random-timing twins; permuted-axis null); substrate VR/autocorr disclosure | quant-designer design.md → QA (fresh context) → operator execution gate → estimand gate → data-analyst → operator verdict |
| EXP-022 | HYP-002 Indices mirror of EXP-021 | **BLOCKED until VAL-007 PASS** (Indices basket 10/10); then same pipeline |
| model select | Construct one (A,B,C,D,G)+V5 model from EXP-021/022 observations; record + hash-pin | operator-signed at/after EXP-021/022 verdicts |
| EXP-023 | HYP-003 tradability of the selected model: cTrader price-primary, V5 execution (active entry / passive rolling-consensus exit / time-only stop / single-worst + median-index 1:1 hedge / no cap), honest round-trip cost, three-twin battery, block-bootstrap + both-halves | quant-designer → QA → operator execution gate → estimand gate → data-analyst → operator verdict |
| HYP-004 | Confirmatory TEST read | **design-gated on EXP-023 clearing the gate; not scoped now** |

## Constraints in force

- TRAIN only (first-70% analysis slice → TRAIN); TEST band never emitted; holdout sealed; 0 slots,
  0 counted reads at exploratory + validatory by construction.
- **Indices arm hard-blocked on VAL-007** — a 10-index consensus requires all 10 admitted; no
  Indices read on a 4/10 basket.
- Integrity gates hard (holdout, estimand reconciliation, causal-fill ≤ t-1, provenance,
  twin-schedule price-independence); every quality read informative — operator judges (INFR-001).
- Per-stratum adjudication; pooled figures disclosure-only (L-03); UNPOWERED never read as negative.
- **Passive-limit entry is banned as the tradability vehicle** (adverse selection, CF-MR-003/004) —
  V1–V4's passive-limit entry is characterised execution-agnostically only; EXP-023 uses V5.
- Momentum-signed inverted twin mandatory on any positive (drift-carry check, USDCAD lesson).
- Family status changes ONLY at this checkpoint's retrospective, operator-signed. Experiments append
  evidence/disposition rows only — never a status transition.
- Predeclared kill criteria + confirmatory gate: family card.

## Exit condition

Retrospective written when EXP-021 (and EXP-022 if VAL-007 admits in time) have operator verdicts,
a single model is selected + hash-pinned, and EXP-023 has an operator verdict — then the disposition
(retire / iterate a component / authorise HYP-004) is operator-signed. Possible outcomes: (a) residual
not MR or no combination beats both twins → RETIRE at 0 cost; (b) availability but net capture <
honest round-trip → NOT-TRADABLE, retire (the cost wall); (c) net survival + twin battery cleared →
authorise the pre-declared confirmatory read.

## Resume pointer

First missing artifact drives resume: no EXP-021 `design.md` → quant-designer (stage 1). Currencies
arm is unblocked now; Indices arm waits on VAL-007. Each per-EXP `design.md` is a separate
quant-designer deliverable, mechanism-first, one hypothesis each — not written at registration.
