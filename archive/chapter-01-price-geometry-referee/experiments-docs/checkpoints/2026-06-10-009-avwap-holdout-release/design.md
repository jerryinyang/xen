# Phase 009 — AVWAP Holdout Release (EXP-032, Package B)

**Status:** COMPLETED 2026-06-10 — EXP-032 executed (HOLDOUT_INCONCLUSIVE, shot
SPENT); see [retrospective.md](retrospective.md). Design opened 2026-06-10.
**Authorization:** Phase 008 G2 SATISFIED → CLINICAL_TRADABLE
(`../2026-06-10-008-avwap-clinical-tradability/G2-gate-review.md`); operator
selected **Package B** (recorded 2026-06-10 in the same artifact). Design §8.4 (as
amended R1.1/R1.2) and §10 of Phase 008 require the holdout release to run behind
strict G2, in its **own checkpoint**, with one fully predeclared package.
**Scope freeze:** every parameter in §4–§6 is frozen at EXP-032 Stage-1 scope
approval. After the freeze, **no amendment of any kind is admissible** — the
holdout read is one-shot and irreversible; a flawed predeclaration is spent, not
fixed.

## 1. Objective

Answer exactly one question with the programme's single sanctioned read of the
global holdout:

> Does the Package-B candidate — the faithful selective AVWAP bounce strategy on
> **EURUSD-4h** with the TRAIN-frozen fixed-horizon exit at **H\* = 12** domain
> bars and **all_legs** pyramid policy, under the frozen CONSERVATIVE cost model
> (RT 3.0 bps) plus predeclared financing (0.6 bps/day, adverse-side, fractional
> calendar days) — retain positive **net** per-event expectancy on the
> **holdout stratum** (final 30% of the full dataset, never previously read)?

This is the first and only time the global holdout is unsealed, and only to the
minimal extent §5 defines.

## 2. Evidential basis (why this package, why now)

- **G2 (strict) satisfied 2026-06-10:** EURUSD-4h passed the binding phase-level
  Holm-4 family on both routes — EXP-037 (FH H\*=12 exit: net +40.56 bps on TEST,
  ci_low_1s 21.94 > margin 8.42, adj_p ≈ 0.004) and EXP-038 (BTC-exit baseline:
  +24.27 bps, ci_low_1s 15.43 > 3.78, adj_p ≈ 0.004).
- **Package B over A (operator rationale):** larger TEST effect and a mechanism
  understood across three experiments (EXP-031 isolated the BTC-exit long-horizon
  drag; EXP-033 measured the TRAIN FH(H) recovery curve; EXP-037 confirmed it
  one-shot on TEST). Package A is **not** released; the two packages share events,
  so the selection is exclusive and final.
- **Lineage of the estimand:** event population and triggers EXP-020/022 →
  faithful strategy EXP-028 (cTrader-confirmed via EXP-029, BTC exit) → frozen
  costs EXP-030 → financing D0/EXP-034 → FH exit machinery EXP-033 → frozen
  H\*=12/all_legs EXP-037 (`frozen_selection.json`, content-hash
  `2bbbf65b…770b0fea`). EXP-032 changes **nothing** in this chain; it only moves
  the evaluation stratum.

## 3. The single-shot rules (binding)

1. **One read.** The holdout outcome inference runs exactly once. A
   no-second-read guard (EXP-037 R1.6 semantics) refuses to recompute inference if
   a verdict artifact exists; a halted run resumes only by exact freeze-record
   hash reproduction.
2. **One estimand.** Only the §4 estimand may be computed from holdout rows. No
   secondary analyses, no other instruments, no other domains, no other exits
   (except the §6 predeclared non-binding companion, computed in the same single
   pass on the same events).
3. **No iteration.** No cost, financing, horizon, policy, population, or
   inference parameter may change after scope freeze — regardless of outcome.
4. **Outcome is final.** CONFIRMED, REFUTED, or INCONCLUSIVE — the shot is spent
   in all three cases. There is no second holdout read for `CF-AVWAP-001`
   Package B, and INCONCLUSIVE does not refund the shot.
5. **Mechanical adjudication.** The verdict rule (§6) is computed by code from
   predeclared constants; no operator judgment enters the verdict.

## 4. Package B estimand (FROZEN — inherited verbatim from EXP-037)

- **Instrument/domain:** EURUSD, 4h (EXP-031-identical domain rebuild from
  1-minute bars). No other instrument or domain.
- **Events:** the deterministic AVWAP bounce event generator (EXP-020/022
  parameters, unchanged) run as a sequential stateful stream over the **full**
  EURUSD 1-minute series. Events with trigger close time ≤ the holdout boundary
  must reproduce the known analysis-set population exactly (reconciliation
  guard); events with trigger close time **> boundary** form the holdout stratum.
  Pyramids included per `all_legs`.
- **Stratum boundary (one convention, R1.3-consistent):** boundary = CloseTime of
  the last analysis 1-minute row (`analysis_rows = int(total_rows × 0.7)`, the
  shared loader's analysis cutoff). An event is HOLDOUT iff its
  entry-confirmation (trigger) close time > boundary; ties → analysis. Membership
  is keyed on the causal entry bar; the FH window may extend toward series end.
- **Outcome per event:** real-OHLC return from entry-confirmation close to the
  close H\*=12 domain bars later (last available bar if truncated at series end —
  EXP-033-identical rule; truncated share disclosed), minus RT 3.0 bps, minus
  financing 0.6 bps/day × elapsed fractional calendar days (trigger → FH exit).
- **Per-cell estimand:** event-weighted mean of `net_e` over holdout-stratum
  events. Baseline is exactly 0 bps net; no percentage-of-baseline metric.

## 5. Holdout access protocol (minimal unsealing)

- **Unsealed:** EURUSD 1-minute rows after the analysis cutoff — and only for:
  (a) streaming event generation continuity, (b) the 4h rebuild, (c) the §4
  outcome computation. Loading is lazy and column-projected.
- **Stays sealed:** BTCUSD, USTEC, XAUUSD holdout rows (never loaded); EURUSD
  holdout for any purpose beyond §4/§6 (no 5m/1h aggregation, no per-bar suite
  runs, no conditioning, no plots of holdout price paths beyond the predeclared
  event-level figures).
- **Two-phase execution with freeze-before-outcome (load-bearing guard):**
  - **Phase H1 (entry attributes only):** generate events over the full series;
    persist the holdout stratum manifest (triggers, directions, regime ids,
    pyramid flags), event counts, the analysis-stratum reconciliation result, the
    §6 calibration margin, and the inherited frozen constants to
    `frozen_holdout_manifest.json` (content-hashed). **No FH return, net, or any
    outcome quantity is computed in H1.**
  - **Phase H2 (one-shot outcome):** runs only if the manifest exists and
    verifies; computes outcomes and inference once; writes the verdict artifact.
- This phase ends the global-holdout reserve for EURUSD. All future EURUSD
  experiments must treat the holdout as contaminated-by-disclosure for any
  EURUSD-4h event-level claim; the programme-level seal remains for the other
  three instruments.

## 6. Inference, calibration, and verdict (FROZEN)

- **Inference:** frozen EXP-027 regime-cluster bootstrap (1000 resamples) +
  one-sided bootstrap p, pinned tail hash `e50873d12a9f68d9` (same tail as
  EXP-034/037/038). Family size = 1 (this is the phase's only binding read);
  no Holm correction applies or is needed.
- **Small-n margin (R1.2 analog, computed in Phase H1):** synthetic-null
  calibration of the frozen bootstrap at the matched holdout cell structure —
  cluster sizes and direction labels from the holdout stratum's **entry
  attributes**; null returns from the zero-mean Gaussian cluster model
  (r = a_c + e_i) with between/within variance components estimated by method of
  moments from the **full-analysis** EURUSD-4h FH(H\*=12)/all_legs nets (TRAIN
  and TEST strata are both already-disclosed data); R = 2000 null replicates,
  each scored by the frozen 1000-resample bootstrap. Binding margin
  `m_cell = max(0, Q95 of null ci_low_1s)`, persisted in the H1 manifest before
  any outcome contact.
- **Binding verdict rule (single cell):**
  - **HOLDOUT_CONFIRMED** iff one-sided 95% lower bound `ci_low_1s > m_cell`
    AND one-sided bootstrap p ≤ 0.05.
  - **HOLDOUT_REFUTED** iff two-sided 95% CI upper bound < 0.
  - **HOLDOUT_INCONCLUSIVE** otherwise.
- **Non-binding companion (predeclared, same pass, never promotable):** BTC-exit
  net on the same holdout events (Package-A estimand, descriptive only — mirrors
  EXP-037's `btc_net_bps` disclosure) and the gross/cost/financing decomposition
  of the binding cell. Neither can ground, upgrade, or substitute for the
  binding verdict, nor nominate any future holdout read.

## 7. Honest power statement

The analysis set (70%) holds 39 EURUSD-4h events; the holdout (30%) is expected
to hold roughly 15–18, subject to regime composition. At the EXP-037 TEST scale
(n = 12 → margin 8.42 bps), a true effect near the TEST point estimate
(+40 bps) would likely confirm, but a true effect near the EXP-038 baseline
scale (+24 bps) with holdout-regime dispersion could land INCONCLUSIVE.
INCONCLUSIVE is an expected, honest outcome and still spends the shot — this is
accepted in advance by the operator's Package-B selection.

## 8. Outcomes and consequences

| Outcome | Consequence |
| --- | --- |
| HOLDOUT_CONFIRMED | First net-positive, holdout-confirmed AVWAP candidate. Programme synthesis update; cTrader per-bar parity check of the **FH exit** variant (EXP-029 covered only the BTC exit) becomes the next required step before any live consideration — on analysis-set data only. |
| HOLDOUT_REFUTED | Package B refuted out-of-sample. Holdout spent. Return to characterisation; Tier C (Stage-C branches, HYP-001) per Phase 008 design §9. No re-release. |
| HOLDOUT_INCONCLUSIVE | Holdout spent without confirmation. Same routing as REFUTED for resource purposes; the TEST-stratum evidence stands but is never upgradable. |

## 9. Non-goals

- Any holdout read beyond §4/§6 (other instruments, domains, exits, strata,
  conditioning, per-bar suite screening).
- Any parameter iteration after scope freeze (costs, financing, H\*, policy,
  population, inference, margin machinery).
- Any second holdout read, for any package, regardless of outcome.
- cTrader parity execution inside this phase (follow-up, analysis-set only).
- HYP-001 and Tier-C work (separate, after this phase closes).

## 10. Experiments

| ID | Title | Slot | Status |
| --- | --- | --- | --- |
| EXP-032 | One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs) | holdout shot (1-of-1, programme-level) | Stage 1 scoped 2026-06-10 |

Registry: `CF-AVWAP-001/HOLDOUT-B` (multiplicity-registry.md). The Stage-4
pre-execution governance review for EXP-032 is the final gate before the manual
execution handoff; given irreversibility, REVISE findings must be resolved
before any code run, including Phase H1.
