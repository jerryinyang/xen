# Checkpoint 007 Retrospective — CF-VOLHARV-001 Falsification-First Screen (2026-07-05)

**Family disposition: CF-VOLHARV-001 CONTINUES — HYP-002 scoping licensed** (operator decision
2026-07-05). The predeclared kill criterion is NOT met: HYP-001 closed ARTIFACT_CONFIRMED, but
the substrate disclosure shows a genuinely mean-reverting FX block against a near-zero
commission floor — the checkpoint's outcome (b): scope EXP-020 in the next phase.

## Phase outcome vs objectives

| Objective | Outcome |
|---|---|
| Adjudicate the anomaly (EXP-019 / HYP-001) | **COMPLETE — SUPPORTED / ARTIFACT_CONFIRMED** (operator verdict 2026-07-05; `python/experiments/EXP-019/report.md`) |
| Swap-inclusive cost floor | **Partially booked**: FTMO commissions pinned (FX 0.47–1.04 bps RT, XAUUSD 0.28, BTCUSD 13.0, indices 0/spread-only; A5 superseded the swap table per operator directive). **Spreads UNPINNED** — live-only on FTMO's page; operator to supply from the platform; `xen.evaluation` raises until populated. |
| VR/oscillation substrate profile | **BOOKED**: FX MR block real — NZDUSD VR 0.92/0.88/0.80/0.80 at H=6/12/24/48, AUDUSD →0.76, GBPUSD/USDCAD similar; BTC/JPY-crosses/gold/CHF ≈ random walk. |
| HYP-002 scope/retire decision | **SCOPE EXP-020** (this document; next checkpoint) |

## Basis for the HYP-001 verdict (kill test succeeded)

1. The EXP-018 anomaly is a sampling draw: NZDUSD battery ≈ 0 in every hold stratum
   (|mean| < MDE 1.4–5.3 bps); the +31.5 sits above the ENTIRE 25-seed distribution
   (pooled seed means [−11.5, +8.6]).
2. Field-wide: 2/64 strata beyond MDE (≈ chance); direction splits drift-shaped;
   BTCUSD-48/EURUSD-12 WASH; BTCUSD H∈{12,24,48} UNPOWERED (never read as negative).
3. Integrity clean: schedule regeneration byte-exact (price-independence proven), fills
   never early, NZDUSD +1-bar delay twin max pair-diff +0.74 bps. 441 runs, 286,476 legs,
   0 censored, estimand gates blocking_pass throughout.
4. The analytic null (E[gross]=0 for the fixed-hold random object) held exactly as designed —
   gross ≈ 0, so net = −(commission+spread) for the unconditioned object.

## Why the family continues (kill criterion adjudication)

Predeclared criterion (family card): retire if ARTIFACT_CONFIRMED **and** no instrument
where plausible harvest clears 1× swap + double-sided spread. Second leg fails: the MR block
(NZDUSD/AUDUSD/GBPUSD/USDCAD, VR 0.76–0.92 across the hold grid) oscillates measurably while
the commission floor is 0.47–1.04 bps RT. Oscillation exists but is **not harvestable
unconditioned** (HYP-001's whole point) — HYP-002 tests whether a structure with a
rebalancing/crossing channel (volatility pumping / symmetric grid) converts it. The on-paper
viability inequality (implied harvest per crossing vs measured floor) is predeclarable in the
EXP-020 design once spreads are pinned.

## Lessons (carried)

- **L-19 confirmed at scale** ([[single-random-control-fragility]]): a single-seed random
  twin is a noisy yardstick — EXP-018's rt read (+31.5, CI_low +13.7) was a top-of-distribution
  draw of exactly the construction EXP-019 sampled 25×. Kill tests need seed batteries and
  percentile reads, not one twin.
- The analytic-null pattern (design the control object so E[·]=0 by construction) is the
  cheapest possible falsifier when available — prefer it over synthetic path nulls.
- Second consecutive clean INFR-001 pipeline pass (elicitation → QA → gates → operator
  verdict); the smoke-cell integrity-only rule held.

## What is closed / what remains open

- **Closed:** the EXP-018 NZDUSD rt anomaly (permanently — a draw, not a property); the
  fixed-hold unconditioned object as a candidate (E[gross]=0 analytic + empirical).
- **Open:** HYP-002 (EXP-020, next checkpoint) — rebalanced-exposure / grid harvest on the
  MR block, negative controls from the ≈-RW block; HYP-003 (CF-VOLEXP tail) stays DEFERRED.
- **Blocker carried:** per-instrument spread pin (operator, from the FTMO platform) before
  any binding net read in EXP-020.

## Registry actions (sanctioned by this retrospective)

- `candidate-families/cf-volharv-001.md`: HYP-001 evidence row already appended (2026-07-05);
  status stays REGISTERED/ACTIVE; HYP-002 gate lifted → "SCOPING (checkpoint-008)".
- `multiplicity-registry.md`: CF-VOLHARV-001/HYP-001 row → COMPLETE, SUPPORTED/
  ARTIFACT_CONFIRMED; HYP-002 row → SCOPING.
- Checkpoint-008 opened for EXP-020 (design-first; no slots/reads at design).

**Signed:** operator (verdict + continue instruction, 2026-07-05); recorded by the pipeline.
