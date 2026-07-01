# EXP-012 Audit — CF-MR-003 CONC-1 Track 2, form-2 limit-at-anchor exec-15m

**Class:** price-primary, cTrader in-engine (L-01). **Adjudicated verdict:** **NOT-TRADABLE (POWERED)**,
per stratum, both arms. **Findings:** 0 Critical (verdict-material) blocking · 1 Critical-class control
defect (self-caught, non-verdict-moving after reclassification) · 2 Info. **Audit result: PASS** — the
NOT-TRADABLE verdict is trustworthy; the raw-script `REJECT_LEAK` headline is a **false trip** from a
mis-specified Python leak control and is superseded (`results/verdict_corrected.json`).

---

## 1. Scope compliance — PASS

- 24 cells exactly = EXP-009 admitted exec-15m set (design §2): T2a 14 S3_DETREND single-symbol, T2b 10
  S5_SPREAD basket. No cell added/dropped on any in-experiment read (confirmed vs
  `EXP-009/results/per_cell.parquet`, `any_pass`).
- Price-primary discipline honored: S3/S5 anchor + form-2 limit logic runs in the C# engine
  (`CrossDomainMrLimitModel.cs`); Python (`code/run_experiment.py`) only ingests/validates/adjudicates.
  **No vectorized Python backtest** (would be REJECT) — confirmed: the script reads emitted
  `positions.parquet` columns only and never reconstructs an anchor, z, entry, or fill.
- Frozen 15m referee consumed as-is: `gate_stack_pstar(domain="15m")`, hashes unchanged from EXP-011
  freeze (`referee_pstar 1fd06b28`). No referee module edited (L-12 honored). Verified no `referee_*.py`
  in the working diff.

## 2. Data handling / fences — PASS

- Per-symbol TRAIN fence: every run's `run_metadata.json` `AnalysisEndUtc` = the design's first-49%
  cutoff; `assert_run_within_holdout` asserts max emitted `SourceCloseTime` < fence. No holdout bar
  emitted. Final-30% never touched.
- Open-to-open assembly, ≤t-1 decision inputs, one round-trip cost per entry (L-02), intra-position MTM
  across 15m boundaries (L-09) — `assemble_realized_bps` reads only emitted `Position/RealOpen/
  EntryFillPrice/ExitFillPrice`; next-open shift drops the last bar; NaN/inf guarded.

## 3. Verdict forensics (per-stratum, non-pooled, L-03) — PASS

Re-derived per cell from `results/verdict.json`. **All 24 cells POWERED** (L1=True; reversion episodes
70–390 ≥ min_state_count 25 — T2a 70–94, T2b 145–390). **0/24 admit, 0/24 Holm-admit.**

- **Mechanism of the NOT-TRADABLE:** the edge is null-to-negative at the 15m horizon, not underpowered.
  Nets cluster at ~0: best T2a:GBPUSD +0.04 / T2a:US2000 +0.02 bps/active (both **CI_low < 0**), median
  ≈ −0.05, worst T2a:BTCUSD −0.77, T2b:USTEC −0.54, T2a:USTEC −0.41. Every CI_lower ≤ 0 ⇒ no cell clears
  the frozen 15m referee even before Holm. The driver is the **cost/horizon tradeoff the design
  predicted**: shorter-horizon reversion captures a smaller favourable move against the same
  per-instrument round-trip, so the limit-at-anchor exit does not out-earn the binding-leg cost.
- **No pooled masking:** the headline is not hiding a separating stratum — the per-cell picture is
  uniformly non-admitting; the two sub-families (T2a 0/14, T2b 0/10) agree. Pooling would only reinforce,
  not manufacture, the null.
- **Gate-shape check:** the frozen 15m P*-gate is a location (mean-net) test, which is the correct
  instrument for a "does the strategy earn net bps" question. No tail/bimodal effect is being vetoed —
  the realized-net distributions are centered at/below zero, not positive-with-fat-left-tail. Gate shape
  fits the effect.
- **Power is real, not assumed:** F-2 planted-positive injection PASSES 24/24 (a known +8 bps/active
  edge is detected at each cell's N) ⇒ the vehicle *can* see a real edge at this episode count, so the
  null is genuine. This is the definitive-close condition EXP-010 lacked (it was UNPOWERED).

## 4. Vehicle fidelity (F-1, design §6) — PASS (remedies EXP-010 gate-debt)

Per-cell in-engine z vs the reference z rebuilt from emitted `Dev`: **z_corr = 1.00 on all 24**;
**|z|≥2 Jaccard 0.97–0.99**. This clears the tightened tolerance (z_corr ≥ 0.90 ∧ Jaccard ≥ 0.70) with
large margin and discharges EXP-010's F-1 debt (its T1 vehicle was 0.67 / 0.30). 0 cells VEHICLE_UNFIT.
The S3 single-symbol path (no basket carry-forward) and the disciplined basket resolution are faithful.

## 5. Causal-provenance & leak pass (L-01) — PASS on the valid control; **defect in the redundant one**

- **Provenance trace.** Verdict-bearing columns all trace ≤ t-1: `Anchor/Dev/Z/Vr/Hl/Beta` are the
  engine's rested (t-1) decision series; `EntryFillPrice/ExitFillPrice` validated inside `[RealLow,
  RealHigh]` of the emitting bar (`validate_provenance`); the exit limit is `a[t-1]` fixed at entry (no
  `rct[di]` self-close-as-own-limit). Cost is the frozen per-instrument 15m round-trip. No acausal read.
- **VALID future-destroy (the design's §7 tripwire): CLEAN.** The live phase-shifted-basket shuffle run
  (`EXP-012-t2b-shuffle`, `--BasketPhaseShiftHours=2000`) re-adjudicated → **0 survivors among live
  admits, `tripwire_pass=True`**. (Vacuous-on-null risk is moot here: there is nothing to destroy because
  the live edge is null, AND the planted-positive power check separately proves detectability.)
- **CONTROL DEFECT (self-caught) — F-2 Python permutation-destroy is mean-invariant.** `f2_plant_destroy`
  computes the "future-destroy" as `planted[perm]` — a permutation of the realized-bps array. The referee
  scores the **mean**, and a permutation is **mean-invariant**; the plant is a constant +8 bps on active
  bars (a mean shift), so the permuted series keeps the lifted mean and cannot collapse (23/24
  `destroyed_pass=True`). This is not a leak in the strategy — it is a **provably ill-posed control**:
  *no* guaranteed-positive additive plant can be collapsed by a mean-preserving permutation. The
  raw-script outcome logic escalated this to `REJECT_LEAK`, which is a **false positive**.
  - **Materiality:** the defect is Critical-*class* (it moved the raw headline), but **after
    reclassification it moves no true verdict-bearing number**: the valid future-destroy (live shuffle)
    is clean, F-1 fit, and all 24 nets are ≤0 at CI. The corrected verdict NOT-TRADABLE (POWERED) is
    unaffected. Per operator direction (verdict is NOT-TRADABLE under either reading), **no re-run** —
    the mean-invariant permutation is demoted to a labeled non-gating diagnostic
    (`verdict_corrected.json`: `f2_permutation_destroy = INVALID_MEAN_INVARIANT_DIAGNOSTIC_NOT_A_GATE`).
    Follow-up (new scope, not this one): if a Python-side non-vacuous leak control is wanted for a
    *mean* referee, it must break alignment causally (permute positions and re-assemble realized), not
    permute the P&L — a permutation of P&L can never test a mean. Filed for the design ledger.

## 6. Code standards — PASS (Info)

- **Info-1:** `code/run_experiment.py` follows the section layout (constants → I/O → pure checks →
  computation → plotting → orchestration → main); typed, docstringed, deterministic (seed 20260701),
  handles empty/NaN/short series. Bootstrap n=10_000 per cell ×3 adjudications (live + plant + destroy) —
  bounded, acceptable runtime (~2.5 min).
- **Info-2:** the `f2_plant_destroy` docstring claims "future-destroy … MUST collapse," which §5 shows is
  unsatisfiable for a mean stat. Doc is now contradicted by the reclassification; left in place with the
  `verdict_corrected.json` note rather than retro-editing the shipped artifact.

---

## Verdict

**AUDIT PASS.** The binding result — **NOT-TRADABLE (POWERED), 24/24 cells, both arms, per stratum** — is
trustworthy: fences intact, provenance causal, vehicle faithful (F-1 clean, fixes EXP-010 debt), power
real (plant detected 24/24), and the **valid** future-destroy (live phase-shift shuffle) clean. The
`REJECT_LEAK` headline is a **false trip** from a mean-invariant Python permutation control and is
superseded. No verdict-material finding survives; no re-execution required. Registry disposition:
CF-MR-003 CONC-1 Track 2 CLOSED NOT-TRADABLE (powered), 0 counted reads (TRAIN disclosure), holdout
sealed.
