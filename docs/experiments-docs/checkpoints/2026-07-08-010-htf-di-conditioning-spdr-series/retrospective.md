# Checkpoint 010/011 Retrospective — CF-HTFDI-001 Disposition (2026-07-09)

**Family disposition: CF-HTFDI-001 RETIRED** — operator-signed, 2026-07-09, on tested evidence
(EXP-025 HYP-A graduation NOT SUPPORTED — magnitude, not existence; powered negative). Retirement
at **0 slots / 0 counted TEST reads**, holdout sealed. The T1 TRAIN tier was terminal: 0/440
SEL-NEIGHBOR qualifiers, so the T2 exit tier and the counted TEST reads were never scoped or spent.

## Phase outcome vs objectives

| Objective | Outcome |
|---|---|
| 1. SPDR screen series (SPDR-001/002/003, CTRL-01/02/03) | **WORTH_EXPLORING (corrected)** — HTF ±DI conditions LTF forward-return sign as continuation on USTEC 1h/5min only; high-vol ATR amplifies; XAU fade thread withdrawn at the same-day correction (under-blocked CIs + mislabelled estimand). |
| 2. Family registration (CF-HTFDI-001, single thread) | **DONE 2026-07-08** — HYP-A continuation, USTEC anchor stratum; control apparatus (25-seed battery, ref-arm, null sentinel) graduated on the control side. |
| 3. HYP-A graduation (EXP-025, 22 symbols, 1h/5min, full pipeline) | **NOT SUPPORTED (magnitude, not existence)** — 0/440 SEL-NEIGHBOR qualifiers (rule 1 own-F0 CI_low>0 fails every cell), MDE ≤5.2 bps, 2.43M TRAIN trades, 0 UNPOWERED. |
| 4. T2 exit-method tier | **NOT SCOPED** — no T1 survivors; analyst recommendation against an exit rescue (a capping/trailing exit cannot manufacture a 10× magnitude gap). |
| 5. Counted TEST confirmation | **NOT SPENT** — 0 reads. |
| 6. Disposition at retrospective | **RETIRED** (this document). |

## Basis for retirement

1. **The channel is real but an order of magnitude below the bar.** The conditioning effect
   replicates end-to-end — screen → engine random-entry reference arm (dir_gap 0.42 vs screen 0.50
   ATR_5m at h48) → 25-seed diagnostic battery (US500 cells ≥2 seed-SD; genuine direction-timing
   gap +1.9–6.2 bps on traded slots). But the true effect is ≈4 bps/trade at h48 (0.2–1 bps at
   short holds), and the tradable residue after one-sided capture + single-position throttle
   dilution is ~1–3 bps/trade: below round-trip commission on FX (200/200 cells ≤ 0 net) and ~1/10
   of the noise-robust SEL-NEIGHBOR selection bar on indices.
2. **The registration target never existed.** The design's "30–60 bps/trade" band was a 4.1×
   units artifact — the graduation design asserted a 1h-ATR divisor where the SPDR screen
   normalised by the 5min LTF ATR(14)[t−1]. Reconciled quantitatively (USTEC TRAIN-median 1h ATR
   33.9 bps vs 5min ATR 8.19 bps). The family was registered against a fictitious magnitude.
3. **What survives is drift, not DI.** 99% of the 200 index cells have the stronger side aligned
   with the instrument's realized drift side; no DI dose-response (low-margin halves ≥ high-margin
   halves); the 3/440 full-TRAIN CI-clear cells (vs ≈11 expected by chance) all fail F0 and flip
   sign by year. h48-friendliness is mechanical drift capture growing with H, not a 1h-DI horizon
   story.
4. **Powered, apparatus-exonerated negative.** MDE 0.18–5.23 bps per cell against both the design
   target and the corrected ~4 bps true effect; engine provenance hard-assert + golden trace
   clean; null sentinel healthy (1/22 CI-clear vs binomial threshold 3); all 440 + 75 battery
   estimand gates `blocking_pass`. Two external reviews (2026-07-09) confirmed the causal chain.
5. **Integrity clean throughout.** TRAIN-only selection (WF-EXPANDING folds inside first
   70%×70%), 0 counted TEST reads, holdout sealed, leak tripwires clean, no local accounting.

Family arc for the record: origin `mtf.md` idea → SPDR-001/002/003 speed-run screens (TRAIN-only,
0 engine runs) → same-day correction (block=H re-derivation; fade thread withdrawn; single USTEC
continuation thread) → CF-HTFDI-001 REGISTERED 2026-07-08 → EXP-025 full-pipeline graduation →
NOT SUPPORTED 2026-07-09 → RETIRED at this retrospective. Total family cost: one full-pipeline
experiment, 0 slots, 0 counted reads.

## Lessons (codified pre-retrospective; binding)

- **L-21 — screen→graduation unit pin + money-unit floor.** The failure seam was the unit
  conversion at the graduation boundary; `docs/references/spdr-lane.md` now requires the screen's
  normaliser pinned in money units and a money-unit floor gate before any WORTH_EXPLORING
  graduates.
- **L-22 — spread as a binding SUPPORTED tier** (commission-only netting is not a tradability
  claim).
- **L-23 — amendment-direction ledger.** All seven 2026-07-08 pre-measurement amendments loosened
  toward ADMIT; direction must be tracked.
- **L-24 — eligibility/null future-design rules** (regime-stability eligibility, battery-under-exit
  null, derived tripwire thresholds, MDE-consistent read floor, shrinkage-aware power math).
- **SPDR lane verdict:** the lane worked as designed as an integrity fence (TRAIN-only, causal,
  0 reads) but under-specified magnitude honesty; L-21's unit pin is the repair, already binding.

## What is closed / what remains open

- **Closed:** CF-HTFDI-001 (this family). The HTF-DI continuation conditioning thesis at 1h/5min
  is measured, real, and untradable at its true magnitude. Re-opening requires a construction that
  plausibly changes the *magnitude* (not the exit), on a genuinely new mechanism claim — a NEW
  family with its own D0, not a re-read of this screen.
- **Open, unregistered (logged, NOT booked):** the tail-managed naive base observation (both
  informative bases median-positive / tail-killed; `mean_excl_worst5` positive 46/48 strata) —
  an orthogonal risk-overlay direction, own-D0 family if pursued. EURUSD 1d/1h power-up stratum
  dies with the family (it carried no CI-clear evidence).
- **Infra flag (standing):** DE40/STOXX50 missing from `xen.evaluation.FTMO_COSTS` under those
  keys — fix before any future experiment nets those symbols.

## Registry actions (sanctioned by this retrospective)

- `candidate-families/cf-htfdi-001.md` status → **RETIRED (2026-07-09, operator-signed,
  checkpoint-010/011 retrospective)**.
- `multiplicity-registry.md`: CF-HTFDI-001 batch header → **RETIRED**; HYP-A row already
  COMPLETED NOT SUPPORTED; T2/TEST tiers NOT SCOPED (0 reads, 0 slots).
- `docs/experiments-docs/INDEX.md`: Phase-011 header → CLOSED — RETIRED; family-status table row
  updated.
- `families/cf-htfdi-001/INDEX.md`: status line → RETIRED (this retrospective).

**Signed:** operator (retire decision, 2026-07-09); recorded by research-pipeline orchestrator.
