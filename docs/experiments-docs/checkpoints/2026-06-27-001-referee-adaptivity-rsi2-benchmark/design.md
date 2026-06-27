# Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark (Chapter 02 opener)

**Status:** DRAFT — G0 PENDING (2026-06-27). **Chapter:** 02 (cTrader-primary era).
**Slots/reads:** 0 candidate slots, 0 counted TEST reads at G0; global holdout sealed.

This is the first Chapter-02 phase. It does double duty: (1) the **referee renew** — fix the
gating-system rigidity uncovered in Chapter 01 (KB **L-12**); (2) the **architecture benchmark** —
push the finalised, causally-correct RSI-2 fade (**CF-MR-002**) end-to-end through the new
cTrader-primary lean pipeline to measure the rollover's correctness *and* speed/efficiency.

## Objectives

1. **O1 — Referee adaptivity (methodological).** Replace rigid fixed-threshold conjunctive gating
   with a power-aware, candidate-matched scheme that **keeps the earned FPR control** but stops
   over-rejecting and mis-scaling. Validate on nulls + synthetics; freeze before any live read.
2. **O2 — Causal RSI-2 (CF-MR-002).** Re-run the RSI-2 fade with the `rct[di-1]` causal exit, in
   the cTrader engine (look-ahead impossible by construction), under the new bar-open / open-to-open
   convention. Establish whether the bare fade has any net edge once causal — the honest prior is it
   does **not** (L-01: causalized, net-negative even gross).
3. **O3 — Architecture benchmark.** Record wall-clock + token cost + artifact count for the full
   lean pipeline run, vs the Chapter-01 8-stage baseline, as the rollover's efficiency proof.

## O1 — the weakness (from L-12) and the investigation

The frozen 5-check stack is an **AND of fixed-threshold legs**. Three documented failure modes:

| Mode | Chapter-01 evidence | Direction to investigate (predeclare at D0) |
|---|---|---|
| Conjunctive fragility (FPR→0 bought with 2–8× MDE; modest/tail/sparse true edges vetoed) | EXP-003 keystone trade-off; CF-VOLEXP tail-only below band; L-11 | Replace hard AND with a **calibrated composite** no single blind leg can veto; predeclared FPR target |
| Structurally-impossible legs (no finite MDE in a regime ⇒ auto-fail, not a test) | EXP-015 standalone-L2 dropped; CF-MR-001 `COVERAGE_EXCLUDED` cells | **Power-aware gating**: apply a leg only where finite MDE exists; report *unpowered*, never *fail* |
| Fixed thresholds mis-scaled to the candidate | L-04 (16× dilution false REFUTE); EXP-008 per-instrument MDE < pooled; fixed-Sharpe=1.0 bite + SUB-RANDOM null both swapped mid-CF-MR-001 | **Candidate-matched thresholds**: MDE-curve co-designed with the band per vehicle/shape/instrument (generalize L-08) |

**Hard governance (binding).** The referee is FROZEN. The redesign is a *predeclared* experiment:
its FPR is re-calibrated on the **dogfood-negative + synthetic-positive** (EXP-019 protocol) and the
new gate is **frozen before** it adjudicates any live candidate. The new gate must **not** be tuned
on CF-MR-002 (that is the exact selection bias L-12 warns against). Old frozen suite is retained and
reported in parallel until the new one is ratified on fresh draws.

## O2 — CF-MR-002 (causal RSI-2 fade), the benchmark vehicle

- **New family, not a reopen.** CF-MR-001 is CLOSED/REFUTED and not reopenable by re-parameterization;
  its closure note authorises a *new* family under its own D0 only **after** the `rct[di-1]` causal
  fix. CF-MR-002 is that family. See `docs/signal-registry/candidate-families/cf-mr-002.md`.
- **Entry:** RSI(2) fade, frozen 10/90 extremes (inherited definition, no re-tuning).
- **Exit:** reversion-completion target rested **only** from `rct[di-1]` (the causal limit). Engine =
  cTrader StrategyHost; Python is analysis-only on emitted `data/strategy_runs/`.
- **Execution convention:** decide at bar **open** on confirmed bars (`≤ t-1`); returns **open-to-open**;
  binding-leg slippage charged. Ships a future-destroying control (must collapse any edge).
- **Honest prior:** availability (gross MFE, no RCT limit) was real (EXP-089/G-020); net capturability
  is what was refuted. Expectation = causal bare fade is **not** net-tradable. A surprise either way is
  read on its own terms.

## O3 — architecture benchmark metrics

Record for the CF-MR-002 run: pipeline wall-clock per stage; approximate token cost; artifact count
(target 4: `design.md`, `code/`, `audit.md`, `report.md`); number of operator stops; and whether the
causal-provenance audit + leak tripwire fire correctly. Compare against the Chapter-01 8-stage norm.

## Sequencing (gates)

1. **G0 (this checkpoint):** ratify scope; register CF-MR-002; predeclare the O1 redesign criteria +
   FPR target + the synthetic-positive/dogfood-negative calibration set. 0 reads/slots.
2. **D-referee:** build + FPR-recalibrate the adaptive gate on nulls/synthetics; **freeze** (hash-pin).
3. **D-benchmark:** run CF-MR-002 causal in-engine through the lean pipeline; adjudicate on BOTH the
   frozen old suite and the newly-frozen adaptive gate (parallel disclosure).
4. **Critical decisions (operator-gated):** any counted TEST read; any deployability claim;
   credentialed/cost-bearing cTrader runs; anything holdout-adjacent. The global holdout is **not** in
   scope for Phase 001.

## Out of scope / deferred

Holdout release; CF-MR-002 deployment economics; the CF-MR-001 deferred levers (vol-regime,
contrarian, 25/75, 15m, cross-cuts). Each needs its own dated D0 + slot decision.

## Success criteria

- O1: an adaptive gate with FPR ≤ the frozen suite's on the dogfood-negative, finite power on the
  synthetic-positive, frozen before any live read — or a documented decision that the frozen suite is
  not improvable without losing FPR control.
- O2: a causal, leak-tripwire-passing CF-MR-002 verdict (net edge: yes/no/inconclusive) with the
  global holdout untouched.
- O3: a recorded efficiency delta (time/tokens/artifacts/stops) vs the Chapter-01 baseline.
