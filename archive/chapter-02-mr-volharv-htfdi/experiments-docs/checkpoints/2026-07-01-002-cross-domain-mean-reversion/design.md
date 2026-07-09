# Phase 002 — Cross-Domain Mean-Reversion Availability (Chapter 02)

**Status:** G0 RATIFIED (2026-07-01). **Chapter:** 02 (cTrader-primary era). **Prior phase:** 001 CLOSED
(referee renew + CF-MR-002 exoneration). **Slots/reads:** 0 candidate slots, 0 counted TEST reads; global
holdout sealed.
**Family:** CF-MR-003 — `docs/signal-registry/candidate-families/cf-mr-003.md` (REGISTERED 2026-07-01).
**Origin:** operator dump `.ignore/dumps/` (cross-domain MR + MR screening framework), concretized via
`/research-pipeline` 2026-07-01.

## Context — where the programme is

Phase 001 closed at the **terminal branch** (retrospective §6): every *opened* price-derived entry axis —
directional, magnitude, relational, MR-fade (CF-MR-002 EXONERATED net-neg 34/34) — screened/closed;
declared frontier = non-price data acquisition. Opening a further **price-derived** family is a deliberate,
operator-ratified probe against a LOW honest prior, admitted **only** because it carries a distinguishing
information source (cross-domain deviation + MR-screen-as-selector) and is gated availability-first at
**zero cost** (0 slots, 0 reads, analysis-only). See CF-MR-003 §"why this is not a re-parameterization".

## Objective

**O1 — Availability screen (methodological, cheap).** Establish whether conditioning entry on a
**cross-domain deviation series characterised mean-reverting at `≤ t-1`** yields a reversion excursion
beyond a **matched-random** control on TRAIN. This is the EXP-081-clone selection gate applied *first*,
before any strategy machinery. Two outcomes only at this rung: **admit-to-explore** or **exonerate**;
no tradability/deployability claim is in scope.

## Ratified forks (operator, 2026-07-01)

| # | Fork | Decision |
|---|------|----------|
| **Governance** | Open a price-derived family vs terminal-branch redirect | **Open CF-MR-003, screen-first.** New information source (MR-screen-as-selector + cross-domain anchor); honest prior LOW; 0 cost. |
| **`/SERIES` anchor** | What is the traded quantity | **Cross-domain deviation**, expanded to a **5-series axis** (operator, 2026-07-01) for a fair full-space test since this rung gates the family: S1 CENTER (median), S2 RANGE (Donchian midline), S3 DETREND (OLS-trendline residual), S4 OU (Ornstein equilibrium, multi-dim HLC3), S5 SPREAD (rolling-β asset-class basket, cross-instrument). Full defs EXP-008 §4. |
| **Domain-pair axis** | Which anchor:exec pairs | **3 pairs (operator, 2026-07-01):** 4h/1h, 4h/15m, 1D/1h (ratios 4:1/16:1/24:1). |
| **First scope** | Screen vs full strategy | **Availability screen only.** Analysis-only, TRAIN, Δ-over-matched-random. Defer `/DIRECTION /REENTRY /TARGET /EXIT`. Building the strategy first = "measure availability last" (methodology-canon), forbidden. |
| **Multiplicity / budget** | 240-cell control | 16 inst × 5 series × 3 pairs ≤ 240 cells → **cross-axis Holm over 15 series×domain axes** (max-stat permuted-axis admission, `availability_gate` G-019). Complexity budget **operator-approved** 2026-07-01. |

## Sequencing (gates)

1. **G0 (this checkpoint):** ratify scope; register CF-MR-003; 0 reads/slots. *(done 2026-07-01)*
2. **EXP-008 (CF-MR-003/HYP-001):** availability screen — analysis-only, TRAIN-only, matched-random control,
   per-stratum, 0 slots/reads, holdout sealed. Design via `experiment-quant-analyst`; inline pre-exec GATE.
3. **Adjudicate:** admit-to-explore → a *new* dated D0 concretizes strategy machinery (still 0 counted reads
   until a tradability read is separately gated). Exonerate → record; family retained; terminal branch stands.

## Hard guards (binding)

- Availability measured **first** (methodology-canon); no strategy machinery, no cost/net claim, no in-engine
  run in EXP-008.
- Matched-random control = within-instrument, matched count + regime (EXP-081/EXP-047 pattern); edge =
  Δ-over-random, not raw excursion.
- **Per-stratum** binding verdicts; pooled = disclosure-only (L-03).
- All screen computation `≤ t-1` (no forming-bar OHLC); real-price excursion outcomes only.
- Renewed referee stays FROZEN; CF-MR-003 **never** tunes it (L-12). Global holdout sealed (not in Phase-002
  scope). No counted TEST read in Phase 002 without a separate operator gate.
- No scope expansion after this G0 — a tradability question is a new experiment under a new D0.

## Success criteria (O1)

- **Admit-to-explore:** MR-screen-conditioned reversion excursion exceeds matched-random with per-stratum
  bootstrap CI excluding zero on a predeclared majority of strata, at a predeclared minimum effect size.
- **Exonerate:** no excursion advantage over matched-random after the predeclared read (mixed/CI-overlap/
  below-effect-floor), consistent with the terminal-branch prior.
- **Inconclusive:** direction mixed / CIs overlap zero / available event count below the predeclared minimum.

*(Concrete effect-size floor, majority threshold, MDE, block-bootstrap null, and the exact screen leg set +
thresholds are predeclared in EXP-008 `design.md` and frozen before outcome contact.)*
