# Family Index — CF-MR-005 (4h Ladder Scale-In Own-Price Mean-Reversion Harvest)

Ladder scale-in on 4h dislocations harvesting short-horizon **own-price** mean reversion, with a
**basket-free trigger**. Registry: `docs/signal-registry/candidate-families/cf-mr-005.md`.
Origin: EXP-014b/014c extend-arm field discovery (spin-out, operator decision D2 2026-07-03) —
see `docs/experiments-docs/families/cf-mr-004/INDEX.md` (EXP-014c card) and
`python/experiments/EXP-014c/{report,audit}.md`.

**Status:** **RETIRED (2026-07-04, operator-signed, checkpoint-006 retrospective).** The
VAL-006 residue does not survive deliberate specification: EXP-018 (first full INFR-001 pass)
returned episode-net WASH in all 4 residue cells, an unfalsified random-timing kill test
(collapse 0.49; NZDUSD random ladder per-leg CI_low > 0 with no signal), and 2022/long-drift
attribution. See `docs/experiments-docs/checkpoints/2026-07-04-006-cf-mr-005-disposition/retrospective.md`.
*(Prior: OPEN — TEST PERSISTENCE RETAINED (EXP-016) — VOIDED by critical-017/VAL-006 (3 TEST
reads SPENT_ON_DEFECT). Prior-prior: CHARACTERISED-NULL / retire-recommended after EXP-015.)*

**Inherited evidence (TRAIN-only disclosure; motivates registration, pre-admits nothing):**
61 cells net ci_low > 0 in EXP-014c (53 never Holm-admitted), exclusively extend/allow arms,
all 11 instruments (10 powered), both z\* triggers, all four exit sets; strongest cells positive every year
2021–2024 (US2000 e3/extend/z15 +10.7/+17.5/+5.3/+9.2 bps/active-bar); per-leg P&L fattens with
ladder depth (US2000 L2 +26.3 bps/leg); 50–85% of edge survives the 60h basket phase-shift
(basket = trigger, not source); NZDUSD survives 3× cost, AUDUSD 2×, US2000 1× only; execution
clean end-to-end.

**First-branch design constraints (binding; full list in the registry file):** mechanism
characterisation before any tradability claim; basket-free trigger; cost realism binding early
(CF-MR-001/002/003 cost-vs-capture precedent; P-02 — no exit-stack rescues); native availability
definition for a multi-add ladder (L-13); left-tail exposure of the scale-in quantified;
attribution controls disclose collapse fractions (EXP-014c W3); frozen referee untuned (L-12).

## Table of contents
- [EXP-018 — HYP-003, deliberate ladder harvest disposition probe — COMPLETE, NOT SUPPORTED → family RETIRED](#exp-018--cf-mr-005hyp-003-deliberate-ladder-harvest-disposition-probe-price-primary)
- EXP-016 — TEST-001, one-shot TEST persistence read — COMPLETE, PERFORMANCE_RETAINED **(VOIDED — critical-017/VAL-006; reads SPENT_ON_DEFECT)** (L-16/L-17 filed)
- [EXP-015 — HYP-001, mechanism characterisation — COMPLETE, NO_MECHANISM_EVIDENCE](#exp-015--cf-mr-005hyp-001-mechanism-characterisation-analysis-only)

---

## EXP-018 — CF-MR-005/HYP-003: deliberate ladder harvest disposition probe (price-primary)

**Completed 2026-07-04 · operator verdict NOT SUPPORTED · first full INFR-001 pipeline pass
(QA subagent APPROVE; estimand gate PASS ×14 roots) ·
[report](../../../../python/experiments/EXP-018/report.md) ·
[design+A1](../../../../python/experiments/EXP-018/design.md) ·
[analysis](../../../../python/experiments/EXP-018/analysis.md) ·
[qa-review](../../../../python/experiments/EXP-018/qa-review.md)**

- **Hypothesis Tests:** Does the VAL-006 residue (US2000 ladder cluster; US500 both-leg
  cluster), specified deliberately (harvest exit set = moving-anchor TP + ⌈3·HL⌉ cap-48
  time-stop, no SL/form-1; braked contrast; both-leg joint form-1 + group time-stop) and
  emitted under the post-critical-017 accounting contract, show dislocation-conditioned,
  exposure-honest, regime-robust positive **episode** economics on TRAIN — and not in the
  NZDUSD negative-control cell?
- **Scope:** 5 live cells (US2000 A/extend, A/allow, B/extend; US500 blmkt-A; NZDUSD A/extend
  neg-control), 4h, S8 trigger frozen (residue-faithful, A1); 18 engine runs = live + seeded
  random-timing destroy twins (matched cadence/dir/holds, matched-hold market exits — L-08)
  + entry-delay +1 tripwire twins + 60h shift disclosure twins; TRAIN 49% fences; episode net
  via `xen.adjudication.build_episodes` at frozen costs; block-5 bootstrap; no referee reads;
  0 slots, 0 counted reads.
- **Results / Observations:** Episode primary **WASH in all 4 residue cells** — US2000
  A/extend +381.9 bps/ep CI [−122, +809] (MDE 504, powered vs residue ~575); A/allow +82.5
  [−151, +228]; B/extend +85.2 [−570, +644]; **US500 both-leg −2.5 [−26, +24] (MDE 24,
  well-powered zero)**. NZDUSD control −273.6 [−694, +52] ✓. **Random-timing destroy:** US2000
  collapse 0.49 (diff CI [−516, +866]); A/allow control beats live (1.96); **NZDUSD rt per-leg
  +31.5 CI [+13.7, +49.9] — CI_low > 0 from pure random timing** while live loses −20.6/leg.
  Real per-leg positive retained honestly: US2000 A/extend +36.8 CI [+9.2, +64], survives 2×
  cost; exposure-honest on avg (24.8%/yr vs 2.8% matched B&H) but NOT on peak (2.9%/yr ≈ B&H;
  peak 43 legs; maxDD 61% of net). 2022 sole CI-positive year; longs +72.7 vs shorts +7.2/leg;
  top-5 episodes = 82% of net; braked arm dies (SL 588 vs TP 579). Delay tripwire graceful
  (0.42–1.13, no sign flip); shift disclosure incoherent (0.53/1.03/2.72).
- **Hypothesis-Specific Conclusion:** **NOT SUPPORTED (operator, 2026-07-04; analyst
  concurring).** The residue's per-leg-CI-positive form is reproducible by an unconditioned
  ladder; what P&L exists is 2022 long-drift carry on deep-add inventory, not a
  dislocation-conditioned harvest. **Family RETIRED at checkpoint-006 retrospective
  (operator-signed).**
- **Hypothesis-Agnostic Observations:** (1) KB lesson-candidate — per-leg CI_low>0 on a ladder
  object is not conditioning evidence; demand an episode-level cadence-matched random-timing
  control (NZDUSD proof-by-example). (2) Matched-hold destroy exits (never re-import the
  anchor into the null) made the read possible — L-08 corollary. (3) rt template placement
  matches cadence at leg level, not episode level (fewer, merged control episodes) — improve
  in any successor. (4) NZDUSD unconditioned matched-hold ladders profit significantly on a
  B&H-negative instrument — an unregistered two-sided vol/rebound question, not MR.

---

## EXP-015 — CF-MR-005/HYP-001: mechanism characterisation (analysis-only)

**Completed 2026-07-03 · audit PASS (0 open Critical; 2 Critical fixed + full re-run) ·
[report](../../../../python/experiments/EXP-015/report.md) ·
[design](../../../../python/experiments/EXP-015/design.md) ·
[audit](../../../../python/experiments/EXP-015/audit.md)**

- **Hypothesis Tests:** Does own price at 4h, conditioned on a basket-free dislocation
  (`z = (logP − Median₉₀)/σ₂₀₀`, ≤ t−1), revert toward the frozen anchor beyond a
  vol-tercile × |ret|-decile matched control, per cell, monotonically in depth (bins
  [1.5,2)…[3,∞), horizons 6–48 bars) — and is the EXP-014b/c extend-arm P&L attributable to
  that depth-graded reversion vs drift / short-vol / tail episodes?
- **Scope:** 11 cells (FX 7 + IDX 4), 4h only; EXP-013 first-49% TRAIN fence verbatim;
  analysis-only (Part A = EXP-014b/c emissions read-only, 87/88 loaded + provenance
  re-asserted; Part B = timebar measurement, no strategy P&L in Python); paired
  fraction-of-dislocation-recovered estimand (L-13/L-15 #3), moving-block bootstrap (12, 10k),
  L-07 block-permuted-returns tripwire (200 replicates, collapse fractions disclosed); frozen
  seeds 20260703/20260704; 0 slots, 0 counted reads.
- **Results / Observations:** **0/11 MECHANISM_SUPPORTED.** Powered bin-1 (n 32–62, 10 cells):
  ΔR₂₄ straddles 0 in 9/10; **US2000 significantly negative** (−0.295 [−0.443, −0.007]).
  Depth-slope CIs straddle 0 in 11/11; **bins 2–4 never reach the 30-event floor** (max n=28).
  Event-mass mismatch: ~30–60 de-clustered own-price episodes/cell vs ~750 engine extend legs.
  Tripwire: 41/44 inside the permuted null band; 3 exceedances all unpowered — no surviving
  edge. Part A: ≥2-leg legs carry ~68% (34–83%) of net P&L; episode left tail heavy (EURUSD
  e0/z15 q05 ≈ −2,356 bps/episode); deepest-decile episode P&L share unstable (−1.6…+3.3);
  bin-4 non-recovery (never 50% in 48 bars) 40–85%, recurring annually; L0 shift-collapse
  fractions heterogeneous (med 0.33, range −125…+10; disclosed per L-15); cost not binding
  (M5: EURUSD 2.93→2.47 bps at 1→3×).
- **Hypothesis-Specific Conclusion:** **NO_MECHANISM_EVIDENCE.** The engine "ladder harvest"
  is not own-price dislocation-conditional mean reversion: the entry cadence was supplied by
  the S8 basket construction, and where powered, dislocated bars recover no better than
  matched controls. HYP-002 tradability not admissible; **family retire recommended**
  (operator-gated; design §1 retire predeclaration met on the powered strata, §5 routes the
  straddle outcome to the operator).
- **Hypothesis-Agnostic Observations:** (1) A trailing-drift split whose window equals the
  anchor window is structurally degenerate (with-drift n≈0) — decouple windows in any
  successor design (audit W2). (2) Emission gap: `EXP-014c-4h-s8-e2-extend-z15` lacks US500.
  (3) The scale-in field P&L is anatomically exposure/tail-flavored: multi-leg-dependent,
  heavy-left-tail, deepest-episode-funded in several cells.

---

## EXP-016 — CF-MR-005/TEST-001: one-shot TEST persistence read (price-primary)

**Completed 2026-07-03 · operator-directed · 3 counted TEST reads (pre-entered) ·
[report](../../../../python/experiments/EXP-016/report.md) ·
[design](../../../../python/experiments/EXP-016/design.md)**

- **Hypothesis Tests.** Does the TRAIN-passing variant (e3/extend/z15, prespecified — the only
  config where all 3 cells Holm-admitted in EXP-014c) retain net edge in the untouched TEST
  band (rows 49%→70%, ≈2024-09→2025-05/06) on US2000/AUDUSD/NZDUSD-4h?
- **Scope.** Same C# model byte-identical; conf fences extended to the 70% cutoff (49% fences
  verified = EXP-013 verbatim); 6 native runs (3 raw + 3 shift twins, twins = collapse-fraction
  disclosure per L-15); frozen §4 criteria + ledger entries BEFORE result contact; one-shot.
- **Results / Observations.** TRAIN legs reproduce EXP-014c exactly (3.98/4.00/10.90). **TEST
  net exceeds TRAIN in all 3 cells:** US2000 +11.83 (ci_low +5.33, boot_p 0.0001, 20 epi, 262
  trades), NZDUSD +4.68 (ci_low +0.59, p 0.0064, Holm ✓), AUDUSD +5.50 (p 0.066, 5 epi, n.s.).
  Frozen referee: UNPOWERED on all 3 — leg forensics isolate **L1_readiness as the sole failing
  leg** (effective_n 333 vs full-sample floor; +8 bps bite plant fails the same leg ⇒ gate
  provably blind on a ~1,110-bar band). Shift collapse: 0.94 / 1.06 / 0.56.
- **Hypothesis-Specific Conclusion.** **PERFORMANCE_RETAINED (numerically 3/3; formal referee
  inapplicable — L-17).** Per the operator's pre-committed fork, the evaluation harness — not
  the strategy — is the suspect: EXP-015's per-event estimand could not see the multi-leg P&L
  object (L-16). Family OPEN; retire withdrawn; mechanism question open.
- **Hypothesis-Agnostic Observations.** (1) **L-17**: the frozen referee cannot adjudicate
  short bands at any edge size — run the bite plant first; if it fails on sample-size legs the
  gate is inapplicable, not negative. (2) **L-16**: characterisation estimands must match the
  P&L-bearing object (L-13 extended upstream). (3) One 9-month window; tail population
  untested; final TEST read per stratum must wait for a predeclared short-band instrument.
