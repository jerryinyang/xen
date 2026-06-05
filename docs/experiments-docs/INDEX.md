# Experiments Index (Comprehensive)

## Current Checkpoint Status

| Checkpoint | Status | Focus | Documents |
| --- | --- | --- | --- |
| 2026-06-05-003b-incremental-unit-redesign | COMPLETED — REVISED_UNIT_VALIDATED (EXP-017-019 executed and post-governance APPROVED 2026-06-05; retrospective written 2026-06-05) | **Track B follow-up succeeded.** EXP-017 validated the revised incremental-referee logic (7/7 fixture verdicts, 28/28 retained-leg checks, L2 absent). EXP-018 validated the revised portfolio-fitness unit on the construction-accepted dependence grid: FPR controlled in 126/126 accepted cells, finite worst-case MDEs 12/16/32 bps on 5m/1h/4h, and the EXP-015 synchronous/high-overlap/null_R stress corner passes in every domain; 36 infeasible high-rho/low-overlap cells are disclosed as construction-invalid. EXP-019 exercised both assembled-suite paths: EXP-009 dogfood rejects and synthetic positive passes across all domains. The concluded suite is now **{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}**. Phase 004 may open after its mandatory programme-level multiplicity registry precondition is documented. **Not a new programme phase — a revision; Phase 004 remains reserved for signal exploration.** | [design.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/design.md) · [retrospective.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/retrospective.md) |
| 2026-06-04-003-ratification-and-incremental-unit | COMPLETED — PARTIAL_SUCCESS (EXP-012-016 executed and reviewed; amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) applied and Track B re-validated; retrospective written 2026-06-05) | **Framework-conclusion attempt did not reach FULL_FRAMEWORK_CONCLUDED (outcome: PARTIAL_SUCCESS).** Track A succeeded: EXP-012 ratified and adopted the EXP-011 loose point on fresh seeds for 5m/1h/4h. Track B validated the substrate and logic gates (EXP-013/014) but EXP-015 refuted portfolio-fitness calibration because every domain had qualifying dependence cells with no finite MDE. EXP-016 correctly blocked before composition measurement because the incremental unit was not COMPLETE and the dogfood reference book was undefined. **Adversarial review (amendment A1) corrected the incremental inference layer (F04 contiguous-series block length), the EXP-013 redundancy verdict (F01 across-draw distribution + `UNDER_POWERED` class), and EXP-015 diagnosability (F03 per-leg/per-instrument tables); EXP-013→014→015 re-validated 2026-06-04/05 — direction unchanged: Track A SUPPORTED, Track B substrate/logic PASS (EXP-013 PASS with 3 cells now `UNDER_POWERED`; EXP-014 PASS, `effective_n` episode-aware), EXP-015 REFUTED with the failure attributed to the L2 standalone-significance leg driven by BTCUSD.** The concluded suite ships as **two referees only** (frozen strict + ratified-loose); the incremental/fitness unit is carried to a follow-up. **Operator decision recorded 2026-06-05 (retrospective §11): Path B — open a new incremental-unit follow-up checkpoint and fix the L2/BTCUSD calibration failure (and resolve the A1/F02 L4/L5 freeze precondition) before Phase 004**, rather than rescoping Phase 004 to standalone-only. Phase 004 stays blocked until that follow-up delivers a validated+calibrated incremental unit. | [design.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/design.md) · [retrospective.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/retrospective.md) |
| 2026-06-03-002-referee-refinement-and-stringency | COMPLETED (7/7 EXP executed, governance-APPROVED; retrospective written 2026-06-04) | Keystone spine item closed for the scoped realistic candidate (EXP-005); L5 threshold frontier measured (EXP-006); lenient-L5 structural-gain claim refuted because lenient equals the EXP-006 zero-buffer endpoint and drop-L5 (EXP-007); per-instrument MDE heterogeneity found in EURUSD/XAUUSD slower-domain cells (EXP-008); broadened simple-strategy dogfood stayed below every domain MDE (EXP-009); split robustness held on 5m/1h with only 4h falsified — and there the more-OOS protocols detect a lower MDE (EXP-010, corrected 2026-06-04: the original 1h/4h walk-forward MDE inflation was a multi-fold CI artifact); predeclared-loss synthesis recommends tau 0.75/0.25/0.5 on 5m/1h/4h, with adoption deferred to Phase 003 fresh draws (EXP-011). Characterization phase - recommends, does not adopt. | [design.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md) · [retrospective.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/retrospective.md) |
| 2026-06-01-001-thesis-qualification-calibration | COMPLETED | Build the 5-check gate-stack referee + calibration harness; measure per-domain (5m/1h/4h) FPR/TPR/economic-MDE for it and a minimal baseline (EXP-001→004). | [design.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/design.md) · [retrospective.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/retrospective.md) |


## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-06-05-003b-incremental-unit-redesign | COMPLETED — **REVISED_UNIT_VALIDATED** (EXP-017-019 executed, pre+post governance APPROVE; pre-execution amendment B1 applied before any results) | **The framework conclusion is completed — Phase 004 unlocks.** Phase 003b removed the **L2 standalone-significance leg** that A1/F03 diagnosed as the EXP-015/BTCUSD refutation cause, leaving the portfolio-fitness gate `L1 ∧ L3 ∧ L4′ ∧ L5` (strict-L5 binding, L3 its precondition), and resolved the A1/F02 L4′/L5 freeze precondition by operator decision. Predeclared once, measured once (D-no-retune held; B1 changed no predeclared object). **EXP-017** SUPPORTED: 7/7 fixture verdicts, 28/28 retained-leg states, L2 absent 7/7, former-L2-fail fixture now passes. **EXP-018** SUPPORTED (the claim EXP-015 refuted, now holding): 126/126 construction-accepted cells PASS, FPR 0.0–0.004, finite worst-case MDEs 12/16/32 bps on 5m/1h/4h, EXP-015 synchronous/high-overlap/null_R corner PASS across all ρ in every domain; 36 high-ρ/low-overlap cells disclosed as construction-invalid. **EXP-019** SUPPORTED: dogfood rejects across all domains (0 strict/loose/incremental passes); nonredundant synthetic positive passes all three components in every domain. Concluded suite **{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 validated revised incremental/fitness unit}** is frozen — D-adopt (P3) satisfied. **Honest caveat:** the incremental screen is the coarsest (12/16/32 vs strict 1/4/12 and loose 0.5/2/8) — correct portfolio-fitness semantics bought at a higher detection floor; validation is on synthetic dependence draws, not real candidates or fresh regimes (holdout sealed). **Phase 004 unlocks behind its mandatory programme-level multiplicity-registry precondition (P3-§11).** | [retrospective.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/retrospective.md) |
| 2026-06-04-003-ratification-and-incremental-unit | COMPLETED — **PARTIAL_SUCCESS** (EXP-012-016 executed; amendment A1 applied + Track B re-validated 2026-06-04/05) | **Two referees concluded; the fitness check is not.** Track A: EXP-012 ratified the EXP-011 loose point on fresh disjoint seeds (`payload_overlap_count=0`) and **adopted** τ 0.75/0.25/0.5 on 5m/1h/4h — FPR 0/4000, fresh MDEs reproduce Phase 002 to the grid (0.5/2/8 bps), 4h split gate agrees; the meta-Goodhart freeze Phase 002 deferred is now executed. Track B mirrored EXP-001→003: substrate PASS (EXP-013: 108/108 recovery, no phantom; 3 cells honestly `UNDER_POWERED` under A1/F01) and logic PASS (EXP-014: 7/7 verdicts, L3→reference-control, episode-aware `effective_n`), but the keystone **REFUTED** (EXP-015): FPR controlled yet no finite MDE in any domain, attributed by A1/F03 diagnostics to the **L2 standalone-significance leg driven by BTCUSD** (standalone TPR 0.0–0.136 at the 32 bps ceiling). EXP-016 correctly BLOCKED (refuted dependency + undefined dogfood book). Adversarial review (A1: F01 across-draw redundancy verdict, F03 diagnostics, F04 contiguous block length, F02 leg-conservatism freeze precondition) made passing *harder* and did not flip any verdict. Against §9 this is **PARTIAL_SUCCESS** — the suite ships as two referees only; the incremental unit goes to a follow-up. **Operator decision (2026-06-05, §11): Path B — open an incremental-unit follow-up checkpoint and fix the L2/BTCUSD failure (+ A1/F02 L4/L5 freeze precondition) before Phase 004**; Phase 004 stays blocked until that follow-up validates+calibrates the unit. | [retrospective.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/retrospective.md) |
| 2026-06-03-002-referee-refinement-and-stringency | COMPLETED (7/7 EXP executed; §9 a–d met + EXP-009/010 delivered) | **Keystone CLOSED: the strict gate is an honest detection floor, not structurally blind** — EXP-005's realistic near-MDE candidate is detected on every domain (TPR 1.000/0.985/0.947 at 1.0× MDE, FPR=0; all 12 per-instrument rows DETECTED_FLOOR), though detection below the MDE is unreliable (0.5× MDE TPR 0.024/0.371/0.502). The L5 stringency lever is one-dimensional (EXP-006 frontier; lenient L5 ≡ τ=0 ≡ drop-L5, EXP-007 REFUTED) and lower τ buys MDE partly with sub-material passes (5m ≈0.50 at zero-buffer). Pooled map is conservative — per-instrument MDEs only lower (EXP-008: EURUSD/1h, EURUSD+XAUUSD/4h). Untuned simple strategies remain net losers below every MDE (EXP-009). Split-robust on 5m/1h; 4h toward a *lower* MDE under more-OOS protocols (EXP-010, corrected). EXP-011 recommends τ 0.75/0.25/0.5 (1h robust, 5m/4h loss-sensitive); **nothing adopted** — fresh-draw ratification is Phase 003. Framework characterization concluded; finalization (freeze) deferred. | [retrospective.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/retrospective.md) |
| 2026-06-01-001-thesis-qualification-calibration | COMPLETED (4/4 EXP SUPPORTED) | Referee operating characteristics measured (design's success deliverable met): gate-stack FPR=0 at all domains/α vs minimal FPR≈α, bought with 2–8× economic MDE (net 1/4/12 bps on 5m/1h/4h); L5 materiality is the binding, α-invariant leg. H-keystone is **bounded, not closed** — EXP-004 dogfood is a null anchor (untuned Donchian/MA carry ~0 edge below every MDE), so structural blindness is true-negative-confirmed but the gate's detection of a weak *real* edge near the MDE is untested. Next: EXP-005 near-MDE detection anchor. | [retrospective.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/retrospective.md) |



## EXP-001 — Synthetic Substrate Validation

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains via `xen.bar_aggregator.aggregate_ohlc`

### Hypothesis Tests

1. **Hypothesis**: The known-null generators produce no oracle-recoverable edge, and the known-positive generator carries the planted oracle-recoverable net edge, on real analysis-set prices for each of the 5m, 1h, and 4h domains.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% 1-minute analysis slice. No chart-type views.
- **Features**: Close-to-Close next-step real returns; oracle state-following positions; known-null (bar-permutation, random-signal) and known-positive (state-aligned drift) generators; P0 aggregation-integrity checks with negative controls; coverage retention grid.
- **Parameter ranges**: domains {5, 60, 240} min; coverage grid {strict, 0.90, 0.80}; net edge grid `m ∈ {0, 0.5, 1, 2, 4, 8, 12, 16, 24, 32}` bps; 200 null draws/generator, 100 positive draws/edge.
- **Exclusions**: final 30% global holdout, chart-type signals, referee operating-characteristic measurement, Donchian/MA dogfood, parameter tuning, bid/ask spread estimation, data-inferred costs.
- **Constraints**: first-70% analysis slice only; shared `CloseTime` split across domains; fixed seeds; real-price outcome discipline; closed-form injection `delta = m + cost`.

### Results / Observations

- `p0_aggregation_checks.csv`: 56/56 PASS at {5, 240} min (4 instruments), including all 4 negative controls detected per period; 0 oracle OHLC mismatches.
- `run_metadata.json`: `overall_status: PASS`, `p0_pass: true`, `substrate_pass: true`, `inconclusive_cells: 0`, `underpowered_cells: 5`.
- Known-null cells (24): mean gross oracle effect ∈ [−0.087, +0.103] bps, every percentile CI brackets zero (200 draws/cell).
- Known-positive recovery: all non-zero cells recover planted `m` within `max(0.5 bps, 15% of m)`; high-sample domains recover to <0.01 bps (e.g. EURUSD/5m m=32 → 32.0005).
- `underpowered_cells.csv`: 5 per-cell INCONCLUSIVE cells, all 4h — BTCUSD m=1,2; USTEC m=1,2; XAUUSD m=1 — recovered mean but across-draw CI straddles zero; all below the 4h materiality threshold (3.0 bps).
- `analysis_metadata.csv`: post-slice analysis rows reproduce VAL-001 exactly (BTCUSD 1,088,960; EURUSD 872,242; USTEC 830,541; XAUUSD 830,671).
- Coverage retention worsens 5m→4h and improves as `min_coverage` relaxes; 4h/0.90 dropped-window fraction 0.025–0.131.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Every P0 check passes, every known-null is indistinguishable from zero, and every known-positive recovers the planted edge within tolerance; the only shortfalls are five 4h sub-material cells, classified by the predeclared §11/D-prec criteria as under-powered (INCONCLUSIVE), not failures. The substrate gate is PASS, so EXP-002/003 may build on it.

### Hypothesis-Agnostic Observations

- 4h effective sample (~2,700–4,400 returns/instrument) bounds attainable precision; EXP-003's 4h power curve near materiality will carry wide CIs.
- Two structurally different nulls agreeing at ≈0 makes accidental recoverable structure implausible.
- The known-positive "significance" leg measures across-draw recovery precision, not single-series detectability — the latter is EXP-003's measurement.

---

## EXP-002 — Referee Golden-Fixture Correctness

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: EURUSD label only (fixture diagnostics; no market data read)
**Data Views / Feature Categories**: Deterministic in-memory return-space golden fixtures; EXP-001 dependency metadata

### Hypothesis Tests

1. **Hypothesis**: The minimal baseline referee and the 5-check gate-stack referee reproduce predeclared hand-computed verdicts on deterministic golden fixtures, while the gate stack records every leg independently.

### Scope

- **Instruments**: EURUSD label only (referee-logic test, not market behaviour).
- **Data Views / Feature Categories**: five deterministic return-space fixtures (positive oracle, null/negative, one-sided readiness, sub-material, naive-equivalent).
- **Features**: minimal-baseline and gate-stack verdicts; L1–L5 leg states; block-bootstrap CI; cost/materiality application.
- **Parameter ranges**: `alpha = 0.05`; `n_bootstrap = 1000`; EURUSD/5m cost 1.0 bps, materiality 0.5 bps.
- **Exclusions**: FPR/TPR/MDE measurement, real candidates, parameter tuning, chart-type signals, any raw Parquet load, holdout.
- **Constraints**: EXP-001 must record `overall_status == PASS`; fixed deterministic seeds; gate stack must evaluate all five legs without short-circuit.

### Results / Observations

- `golden_fixture_results.csv`: 10/10 verdict checks PASS. positive_oracle (min PASS/gate PASS, +6.0 net), null_negative_edge (REJECT/REJECT, −3.0), readiness_one_sided (PASS/REJECT, +7.0), materiality_too_small (PASS/REJECT, +0.2), naive_equivalent (PASS/REJECT, +1.667). Gate effect = minimal effect − 1.0 bps cost in every row.
- `leg_exposure_matrix.csv`: 25/25 leg-exposure checks PASS; all five legs recorded for every fixture (no short-circuit).
- Leg isolation: L1 via readiness_one_sided (0 down-episodes), L5 via materiality_too_small, L3 via naive_equivalent (`ci_vs_naive_lower = 0`), L3+L5 via null_negative_edge, all-pass via positive_oracle.
- `run_metadata.json`: `overall_status: PASS`. Independent reproduction matched all rows bit-for-bit.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Both referees reproduce every predeclared golden-fixture verdict and the gate stack exposes all five legs without short-circuiting, satisfying the scope's Evidence-FOR criteria; the referee logic is approved for EXP-003.

### Hypothesis-Agnostic Observations

- The `materiality_too_small` minimal row reports a degenerate `effective_n = 0.9` (block-length capped at the limit) because its series is constant to floating-point dust; deterministic, immaterial to the verdict, and impossible on real returns.
- The same data yielding minimal-PASS but gate-REJECT (readiness_one_sided, materiality_too_small) cleanly demonstrates what each extra gate leg buys over the minimal baseline.

---

## EXP-003 — Referee Operating-Characteristic Calibration (Keystone)

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains

### Hypothesis Tests

1. **Hypothesis**: The 5-check gate stack has a measurable empirical economic MDE at FPR ≤ α₀ = 0.05 on each domain, and its operating characteristics can be compared against the minimal baseline referee without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: paired known-null (bar-permutation, random-signal) and known-positive (state-aligned drift) draws; minimal-baseline and gate-stack verdicts with all five legs; block-bootstrap CIs; Wilson-interval FPR/TPR; empirical MDE.
- **Parameter ranges**: α grid {0.10, 0.05, 0.01}; edge grid {0,0.5,1,2,4,8,12,16,24,32} bps; 500 null draws/generator (n=4000/cell pooled over instruments), 500 positive draws/edge (n=2000/cell), 1000 inner bootstrap resamples/verdict.
- **Exclusions**: Donchian/MA dogfood interpretation, referee redesign, loss-function tuning, walk-forward, chart-type candidates, parameter optimization, holdout.
- **Constraints**: EXP-001 and EXP-002 must PASS; first-70% slice only; shared `CloseTime` split across domains; real-price `Close` outcomes; block length on train only; identical (paired) draws to both referees.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `mde_cells: 18`, `mde_status_counts: {PASS: 18}`.
- Gate-stack FPR = 0.0 (0/4000) at every domain and every α (`fpr_summary.csv`); minimal-baseline FPR ≈ α and ≤ α (e.g. 1h: 0.005 / 0.0248 / 0.0493 at α = 0.01 / 0.05 / 0.10).
- Empirical MDE at α = 0.05 (`mde_summary.csv`): gate stack 1.0 (5m) / 4.0 (1h) / 12.0 (4h) bps; minimal baseline 0.5 / 0.5 / 2.0 bps. Gate MDE identical across the α grid; minimal-baseline 4h MDE moves 4.0 → 2.0 → 1.0 across α = 0.01 / 0.05 / 0.10.
- Per-leg null pass rates (α = 0.05, all domains): L1 = L2 = 1.000, L3 = L4 = L5 = 0.000. Near the MDE, L5 is the lagging leg (4h m=2 → L5 = 0.006; 1h m=2 → L5 = 0.371; 4h m=12 → L5 = 0.935; 1h m=4 → L5 = 0.977).
- TPR monotone non-decreasing to 1.0 across the grid (`tpr_summary.csv`); all 18 cells meet FPR half-width ≤ 0.03 and TPR half-width ≤ 0.05.
- Effective N (blocks) reported per cell (e.g. BTCUSD 4h ≈ 1335). An independent end-to-end reproduction of a BTCUSD/4h cell matched `draw_verdicts.csv` bit-for-bit.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Both referees have a usable-precision operating-characteristic map on all three domains; all 18 cells yield a finite MDE at controlled FPR (Evidence-FOR criteria met). The measured keystone result is the per-domain stringency↔sensitivity trade-off: the gate stack drives FPR from ≈ α to 0 at the cost of a 2–8× larger economic MDE.

### Hypothesis-Agnostic Observations

- L5 materiality dominates the gate stack's false negatives and sets its MDE, making the gate MDE α-invariant; the α grid moves only the minimal baseline's MDE.
- Per-domain rates pool four instruments of heterogeneous cost (1–10 bps) and dispersion, so each MDE is a domain aggregate; per-instrument MDEs could be lower (relevant to EXP-004).
- Whether the gate MDE sits above where plausibly-real edges live (structural blindness) is not decided here — it needs the EXP-004 dogfood anchor. The 4h gate MDE (12 bps) exceeds the 4h materiality threshold (3 bps).

---

## EXP-004 — Real Dogfood Consistency Anchor

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Real Donchian-channel breakout (lookback 20) and MA-crossover (fast 20, slow 50) verdicts are consistent with where their measured net effect sizes fall on the calibrated per-domain MDE map from EXP-003.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: fixed Donchian(20) breakout and MA(20,50) crossover positions; minimal-baseline (gross) and 5-check gate-stack (net-of-cost) referee verdicts at α=0.05; block-bootstrap effect CIs; consistency vs the EXP-003 MDE map.
- **Parameter ranges**: α=0.05; 1000 inner block-bootstrap resamples/verdict; Donchian lookback 20; MA fast 20 / slow 50; fixed and untuned.
- **Exclusions**: final 30% global holdout, parameter optimization, strategy improvement, chart-type candidates, stop/target logic, walk-forward, and any revision of referee rules based on dogfood results.
- **Constraints**: EXP-003 MDE artifact must exist (cell inconclusive where MDE missing/imprecise); first-70% slice only; shared 1-minute `CloseTime` train/test boundary across domains; real domain `Close` outcomes with flat scoped costs; look-ahead-safe positions (Donchian prior windows, MA closes at bar `t`), evaluated on `t→t+1` returns.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, α=0.05, 1000 bootstrap resamples, Donchian 20, MA 20/50.
- `dogfood_consistency.csv`: 48/48 cells `consistency_status = PASS`, all `reason = matched_reject`; 0 FAIL, 0 INCONCLUSIVE.
- `dogfood_effects.csv`: all 48 verdicts REJECT (both referees). Gate-stack (net) effects range −12.199 (BTCUSD/4h/MA) to +0.045 (EURUSD/4h/Donchian) bps; minimal-baseline (gross) effects range ≈ [−2.20, +1.32] bps with every CI bracketing or below zero (e.g. XAUUSD/4h/MA +1.317 [−1.445, +4.035]; USTEC/1h/Donchian +0.226 [−0.178, +0.680]).
- EXP-003 α=0.05 MDE map (loaded, audit-verified): gate stack 1.0/4.0/12.0 bps and minimal baseline 0.5/0.5/2.0 bps for 5m/1h/4h; grid uncertainty 0.25/1.0/2.0 (gate) and 0.25/0.25/0.5 (minimal). Every measured effect sits below its domain MDE.
- Effective N: 5m ~49,608–65,144; 1h ~4,155–5,430; 4h ~902–1,335. `block_length = 1` for all 48 cells.
- Cost accounting verified: minimal(gross) − gate(net) effect = cost × active-bar fraction (exact per-instrument cost for always-active MA; in `[0, cost]` for frequently-flat Donchian).
- `analysis_metadata.csv`: per-instrument `analysis_end` precedes each source file's end date, confirming the final 30% holdout was not loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Every cell meets the predeclared Evidence-FOR criterion — a reject with the measured effect below its domain MDE — with no Evidence-AGAINST and no inconclusive cells, so real Donchian/MA verdicts agree with their positions on the EXP-003 calibrated MDE map (48/48 consistent) and no synthetic-vs-real DGP gap is surfaced.

### Hypothesis-Agnostic Observations

- The dogfood set is a **null/lower anchor** for H-keystone: untuned Donchian/MA carry no statistically positive edge even gross of cost, so they locate simple intraday edges at ≈0 beneath every per-domain MDE; this is consistent with the gate stack's rejections (true negatives) but does not, on its own, resolve whether the gate MDE sits above genuinely weak real edges — structural blindness is bounded, not closed.
- The gate stack's systematic negativity is mechanical (cost charged to active bars), not a negative edge; the gross minimal-baseline read is the cleaner edge test and is also non-positive.
- `block_length = 1` across all cells means per-bar Donchian/MA strategy returns showed negligible autocorrelation, so the stationary bootstrap reduced to i.i.d. resampling and effective N equals the raw test-bar count.

---

## EXP-005 — Near-MDE Realistic-Candidate Detection Anchor

**Status**: SUPPORTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: On each scoped domain, the frozen Phase 001 5-check gate stack detects an imperfect realistic candidate whose expected net real-price edge is at least the EXP-003 gate-stack MDE, with pooled-domain TPR >= 0.80 at `FPR <= alpha0 = 0.05`.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: latent state `S_t in {-1,+1}`; imperfect candidate `C_t in {-1,0,+1}` with `p_active=0.80` and `q_match=0.75`; paired null draws (raw returns and bar-permutation); known-positive latent-state drift calibrated so the candidate's expected all-eligible-row net edge equals the target edge; minimal-baseline and gate-stack verdicts; Wilson FPR/TPR summaries; pooled-domain and per-instrument detection rows.
- **Parameter ranges**: alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0=0.05`; EXP-003 gate MDE map at alpha0 = 5m `1.0`, 1h `4.0`, 4h `12.0` bps; edge multipliers `{0.5, 1.0, 1.5, 2.0}`; 500 positive draws per edge/instrument/domain; 500 null draws per null generator/instrument/domain; 1000 bootstrap resamples/verdict.
- **Exclusions**: final 30% global holdout, chart-type signals, real strategy tuning, loss-function tuning, referee redesign, threshold sweeping, lenient-L5 variants, walk-forward validation, stop/target logic, bid/ask spread estimation, and any use of Phase 002 outcomes to alter the candidate construction.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE + finite MDE artifacts required; Phase 002 predeclaration confirmation recorded before measurement; first-70% slice only; shared 1-minute `CloseTime` train/test boundary across domains; real domain `Close` outcomes plus predeclared known-positive drift; frozen `xen.referee_calibration` harness reused unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{exp001_status: PASS, exp003_status: COMPLETE}`, `candidate_sanity.sanity_pass: true`, `domain_status: {5m: DETECTED_FLOOR, 1h: DETECTED_FLOOR, 4h: DETECTED_FLOOR}`.
- Candidate construction sanity passed: overall active rate `0.799997`, active match rate `0.750005`; per-cell active-rate range `0.798518` to `0.800561`; per-cell match-rate range `0.749482` to `0.750623`; positive calibration absolute error range `0.000005` to `0.129769` bps.
- Gate-stack pooled FPR at `alpha0=0.05` is `0/4000` in every domain, Wilson half-width `0.000480`; minimal-baseline diagnostic FPR is `0.02375` (5m), `0.02350` (1h), and `0.02500` (4h).
- Gate-stack pooled TPR at `1.0 x` MDE: 5m `1.0000` (2000/2000, half-width `0.000959`), 1h `0.9850` (1970/2000, half-width `0.005403`), 4h `0.9465` (1893/2000, half-width `0.009890`).
- Gate-stack TPR at `0.5 x` MDE remains below target: 5m `0.024`, 1h `0.371`, 4h `0.502`; at `1.5 x` and `2.0 x` it is effectively saturated in all domains.
- All 12 per-instrument headline rows at `1.0 x` MDE classify `DETECTED_FLOOR` with `under_powered=false`; weakest headline cell is BTCUSD/4h with TPR `0.828` and half-width `0.0330`.
- Audit verdict PASS: result tables internally consistent; independent recomputation of FPR/TPR summaries from 216,000 verdict rows found zero mismatches; no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The frozen gate stack detects the predeclared imperfect realistic candidate at each domain's EXP-003 MDE while controlling FPR. EXP-005 therefore closes the Phase 001 open keystone for this candidate class: the oracle-calibrated MDE map is an honest detection floor here, not evidence of structural blindness.

### Hypothesis-Agnostic Observations

- The strict gate remains conservative: zero pooled null passes for the gate stack, while the minimal baseline sits near nominal but below `alpha0`.
- The exact-MDE pass does not imply reliable detection below the MDE; all three `0.5 x` rows fail the TPR target, especially 5m (`0.024`).
- The pooled-domain pass is not masking an instrument-level headline failure under the approved precision rule, but EXP-008 remains needed because EXP-005 does not estimate per-instrument MDE.
- `block_length = 1` across all verdict rows means the stationary bootstrap reduced to i.i.d. resampling under the frozen estimator; this does not invalidate EXP-005 but preserves the value of EXP-010 split/dependence stress testing.

---

## EXP-006 — L5 Materiality Threshold Sweep

**Status**: SUPPORTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through EXP-003 draw artifacts)
**Data Views / Feature Categories**: EXP-003 draw-level gate-stack verdicts for 5m, 1h, and 4h OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis / exploratory question**: How do the frozen gate stack's FPR and economic MDE vary as the L5 materiality threshold magnitude is swept per domain?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003.
- **Data Views / Feature Categories**: EXP-003 verdict-level artifacts only; no new market-data measurement.
- **Features**: Gate-stack draw pass states, L1-L4 leg states, `ci_lower_bps`, `materiality_bps`, swept `L5_tau = ci_lower_bps > tau_bps`, Wilson FPR/TPR, grid-defined MDE.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; threshold multipliers `{0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00}`; EXP-003 planted-edge grid including `0.0` through `32.0` bps.
- **Exclusions**: Lenient-L5 mechanism from EXP-007, near-MDE realistic candidates, per-instrument MDE de-pooling, loss-function selection, threshold adoption, chart-type signals, and referee redesign.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; result-level post-processing preferred; final 30% global holdout never loaded; L1-L4, costs, materiality constants, sample membership, denominators, and real-price EXP-003 outcomes unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `strict_reference_pass: true`, `gate_draw_rows: 216000`, 7 threshold multipliers.
- `strict_reference_check.csv`: 9/9 domain/alpha rows matched EXP-003 exactly; `draw_mismatch_count = 0` and `mde_match = true` for every row.
- `threshold_draw_verdicts.csv`: 1,512,000 rows (`216,000 x 7`).
- `threshold_fpr_summary.csv`: every domain/alpha/threshold cell has FPR `0/4000`, Wilson half-width `0.000480`.
- `threshold_mde_summary.csv`: 63/63 rows `status = PASS`.
- At `alpha0=0.05`, strict `tau=1.0` MDEs were 5m `1.0`, 1h `4.0`, and 4h `12.0` bps; zero-buffer `tau=0.0` MDEs were 5m `0.5`, 1h `2.0`, and 4h `8.0` bps.
- At `alpha0=0.05`, high-threshold `tau=2.0` MDEs rose to 5m `2.0`, 1h `8.0`, and 4h `16.0` bps.
- TPR at the alpha0 zero-buffer MDE was 5m `1.000` at `0.5` bps, 1h `0.924` at `2.0` bps, and 4h `0.902` at `8.0` bps.
- Audit verdict PASS: no critical or warning issues; independent CSV aggregation verified row counts, denominators, strict-reference equality, and selected FPR/TPR rates.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The exploratory measurement delivered the scoped L5 lever curve with usable precision in every cell. Lower L5 thresholds reduced MDE without increasing pooled FPR on the EXP-003 draw substrate, and the strict `tau=1.0` rows reproduced EXP-003 exactly.

### Hypothesis-Agnostic Observations

- L5 threshold magnitude is a practical stringency lever, but EXP-006 does not adopt an operating point.
- The zero-buffer endpoint is the key input to EXP-007 and EXP-011.
- FPR staying zero likely reflects other gate legs remaining restrictive on the scoped null generators; fresh-draw adoption remains a later-phase decision.
- Results are pooled by domain, so EXP-008 remains necessary for instrument-level heterogeneity.

---

## EXP-007 — Lenient-L5 Referee Variant

**Status**: REFUTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through EXP-003/EXP-006 draw artifacts)
**Data Views / Feature Categories**: EXP-003 gate-stack draw verdicts plus EXP-006 threshold frontier artifacts for 5m, 1h, and 4h OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The predeclared lenient L5 variant lowers the gate stack's economic MDE relative to the frozen strict gate while holding `FPR <= alpha0 = 0.05`, beyond what is achieved by the EXP-006 threshold-magnitude frontier.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003 and EXP-006.
- **Data Views / Feature Categories**: EXP-003 draw-level verdict artifacts and EXP-006 threshold-frontier artifacts; no new market-data measurement.
- **Features**: `L5_lenient = ci_lower_bps > 0.0`, unchanged L1-L4, strict and lenient pass states, verdict-level equality against EXP-006 `tau=0`, Wilson FPR/TPR, grid-defined MDE, and economically sub-material pass rates.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; EXP-003 planted-edge grid; EXP-006 threshold frontier for comparison.
- **Exclusions**: Adoption/freezing of the lenient variant, loss-function selection, changing L1-L4, changing costs/materiality constants, adding thresholds after reading EXP-006, chart-type signals, and referee redesign.
- **Constraints**: EXP-001 PASS, EXP-003 COMPLETE, and EXP-006 COMPLETE with `strict_reference_pass = true`; final 30% global holdout never loaded; real-price EXP-003 outcomes reused unchanged; sub-material denominator is lenient positive passes per domain/alpha/edge.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `structural_equivalence_pass: true`, headline alpha0 verdict `EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN` for 5m, 1h, and 4h.
- `lenient_draw_verdicts.csv`: 216,000 rows.
- `structural_equivalence_check.csv`: 9/9 rows have `lenient_vs_dropl5_mismatch = 0`, `lenient_vs_exp006_tau0_mismatch = 0`, `lenient_vs_exp006_tau0_unmatched = 0`, `draws_match_dropl5 = true`, `draws_match_exp006_tau0 = true`, and `lenient_eq_tau0_mde = true`.
- `lenient_fpr_summary.csv`: lenient FPR `0/4000` in every domain/alpha row, Wilson half-width `0.000480`.
- At `alpha0=0.05`, lenient MDEs were 5m `0.5`, 1h `2.0`, and 4h `8.0` bps versus strict `1.0`, `4.0`, and `12.0` bps. These lenient MDEs equal the EXP-006 zero-buffer and best acceptable frontier MDEs.
- At the alpha0 lenient MDE, TPR was 5m `1.000` (`2000/2000`), 1h `0.924` (`1848/2000`), and 4h `0.902` (`1804/2000`).
- At the alpha0 lenient MDE, economically sub-material pass rates were 5m `0.4965`, 1h `0.054654`, and 4h `0.0`.
- `lenient_vs_frontier.csv`: all 9 domain/alpha rows have `improves_beyond_frontier = false` and `verdict = EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN`.
- Audit verdict PASS: no critical or warning issues; independent CSV aggregation verified row counts, denominators, structural-equivalence counts, and selected FPR/TPR/sub-material rates.

### Hypothesis-Specific Conclusion

**REFUTED**

Lenient L5 controlled FPR and lowered strict MDE, but it did not lower MDE beyond the EXP-006 threshold frontier. It exactly matched EXP-006 `tau=0` and drop-L5 at the verdict and MDE levels, so H-lenient's structural-gain claim is refuted by the predeclared Evidence-AGAINST criterion.

### Hypothesis-Agnostic Observations

- The useful object for synthesis is the EXP-006 zero-buffer endpoint plus EXP-007's sub-material accounting, not a distinct lenient-L5 mechanism.
- The 5m sub-material rate at the lenient MDE (`0.4965`) is just below the `0.50` cutoff, so 5m zero-buffer sensitivity should be treated cautiously in EXP-011.
- Because L3 already requires `ci_lower_bps > 0`, removing L5's materiality buffer makes L5 redundant under the frozen harness.
- No Phase 002 result adopts or freezes a new referee; Phase 003 fresh-draw ratification remains required for any operating-point change.

---

## EXP-008 - Per-Instrument MDE De-Pooling

**Status**: SUPPORTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-003 gate-stack draw verdicts for 5m, 1h, and 4h OHLC domains, de-pooled by instrument; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Per-instrument gate-stack economic MDEs differ materially from the Phase 001 four-instrument pooled domain MDEs, where material means `|per_instrument_MDE - pooled_MDE| >= max(0.5 bps, 20% of pooled_MDE)` at `alpha0 = 0.05`.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: EXP-003 verdict-level artifacts only; no new market-data measurement.
- **Features**: Gate-stack draw pass states, per-instrument Wilson FPR/TPR, grid-defined per-instrument MDE, pooled-vs-instrument material-difference flag.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; EXP-003 edge grid; TPR target `0.80`; frozen material margin `max(0.5 bps, 20% of pooled_MDE)`.
- **Exclusions**: Fresh draw generation, new market-data measurement, chart-type signals, referee redesign, strategy candidates, split-protocol comparison, loss-function selection, and operating-point adoption.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; final 30% global holdout never loaded; EXP-003 sample membership, denominators, costs, materiality, and real-price outcomes reused unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `gate_draw_rows: 216000`, `hpool_rollup: {hpool_verdict: SUPPORTED, reportable_cells_alpha0: 12, material_cells_alpha0: 3}`.
- `per_instrument_mde_summary.csv`: 36/36 instrument/domain/alpha rows `status = PASS`.
- At `alpha0=0.05`, gate FPR was `0/1000` in every instrument/domain cell, Wilson half-width `0.001913`; TPR rows used `n=500`, max Wilson half-width `0.043182`.
- Material alpha0 differences:
  - EURUSD/1h: per-instrument MDE `2.0` bps vs pooled `4.0` bps; delta `-2.0`; margin `0.8`.
  - EURUSD/4h: per-instrument MDE `8.0` bps vs pooled `12.0` bps; delta `-4.0`; margin `2.4`.
  - XAUUSD/4h: per-instrument MDE `8.0` bps vs pooled `12.0` bps; delta `-4.0`; margin `2.4`.
- All 5m per-instrument MDEs equaled the pooled 5m MDE of `1.0` bps.
- Audit verdict PASS: independent regrouping from EXP-003 draw verdicts found 0 FPR mismatches and 0 TPR mismatches.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The predeclared Evidence-FOR criterion is met because at least one reportable per-instrument cell differs materially from the pooled MDE. The pooled EXP-003 MDE map masks lower per-instrument MDEs in EURUSD/1h and EURUSD/XAUUSD 4h.

### Hypothesis-Agnostic Observations

- 5m shows no visible per-instrument heterogeneity at the EXP-003 grid resolution.
- The material differences are in the lower-MDE direction, making the pooled map conservative for those cells rather than overly permissive.
- EXP-008 sharpens the map for EXP-011 but does not adopt per-instrument thresholds.

---

## EXP-009 - Broadened Untuned Strategy Effect-Size Distribution

**Status**: MEASUREMENT COMPLETE (exploratory)
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; six fixed untuned simple strategy families; no chart-type views

### Hypothesis Tests

1. **Hypothesis / exploratory question**: Where do the net and gross effect sizes of a broadened set of untuned, fixed-parameter simple strategies sit relative to each domain's EXP-003 MDE?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: Donchian(20), MA(20/50), RSI(14), Bollinger(20, 2.0), MACD(12,26,9), ROC(20) positions; frozen minimal-baseline and gate-stack referee effects; MDE location classification; domain/family distribution summaries.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; 1000 bootstrap resamples; fixed strategy parameters as named.
- **Exclusions**: Strategy tuning, ensembling, stops/targets, chart-type signals, per-instrument MDE estimation, split-protocol variation, loss-function selection, referee redesign, and any per-strategy qualification verdict.
- **Constraints**: EXP-003 COMPLETE and EXP-004 PASS required; first-70% analysis slice only; shared `CloseTime` split; `t -> t+1` real `Close` returns; all warmup/NaN positions flat, not dropped.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{exp003_status: COMPLETE, exp004_status: PASS}`.
- `strategy_verdicts.csv`: 432 rows = 6 strategies x 4 instruments x 3 domains x 2 referees x 3 alphas.
- `strategy_effects.csv`: 144 alpha0 effect rows; 72 gate-stack rows.
- Gate-stack MDE location: 72/72 cells `below_MDE`; 0 `near_MDE`; 0 `at_or_above_MDE`.
- Domain gate-stack net-effect summaries:
  - 5m median `-1.018395` bps, IQR `[-3.007847, -0.406185]`, range `[-9.987340, -0.069953]`.
  - 1h median `-0.998325` bps, IQR `[-2.878832, -0.383782]`, range `[-10.949345, -0.080834]`.
  - 4h median `-0.952547` bps, IQR `[-2.318087, -0.098853]`, range `[-13.029254, +0.045022]`.
- Largest positive gate-stack point estimate: EURUSD/4h Donchian(20) `+0.045022` bps, CI `[-0.390681, +0.514643]`, below 4h gate MDE `12.0` bps.
- Effective N ranged from `902` to `65144`; `block_length = 1` for all 72 gate cells.
- Audit verdict PASS: no critical or warning issues; output dimensions, ranges, causal indicator construction, and real-price discipline verified.

### Hypothesis-Specific Conclusion

**MEASUREMENT COMPLETE (exploratory)**

EXP-009 is exploratory, but its scoped deliverable was produced. The broadened fixed simple-strategy distribution sits below every domain MDE, strengthening the EXP-004 lower anchor rather than surfacing a near-MDE real candidate. The cells are mostly **net-negative** after cost (medians ~ -1 bps), so this is a lower anchor of net losers, not small positive edges sitting just under the floor.

### Hypothesis-Agnostic Observations

- Simple untuned standalone strategies remain a lower anchor (mostly net-negative after cost) after broadening from 2 to 6 strategy definitions.
- Cost-applied net effects are frequently negative, especially active BTCUSD trend/momentum cells.
- The result does not refute tuned, ensemble, or incremental-information candidates; those require new predeclared scopes.

---

## EXP-010 - Split-Protocol Robustness of the Referee

**Status**: PARTIALLY REFUTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain)
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; regenerated known-null and known-positive referee-calibration draws; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Alternative within-analysis-set split protocols - anchored walk-forward and purged/embargoed CV - do not materially change the frozen referee's pooled-by-domain gate-stack FPR and economic MDE versus the mandated single chronological split.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: Single chronological split, anchored walk-forward K=5, purged/embargoed CV K=5, regenerated known-null and known-positive draws, frozen minimal-baseline and gate-stack verdicts, Wilson FPR/TPR, grid MDE, reference-reproduction check.
- **Parameter ranges**: Alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; EXP-003 edge grid; 250 null draws per null generator; 250 positive draws per edge; 1000 bootstrap resamples; walk-forward K=5; purged CV K=5; purge 1 bar; embargo `max(1, block_length)`.
- **Exclusions**: Protocol adoption, per-instrument de-pooling, broadened strategy set, near-MDE candidate, L5 threshold/lenient variants, referee redesign, chart-type signals, and holdout use.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; all protocols operate only within the first-70% analysis set; fold boundaries mapped from shared 1-minute `CloseTime`; referee costs/materiality/legs/bootstrap frozen.

### Results / Observations

> **Corrected 2026-06-04 (adversarial review F01).** The original multi-fold wrapper combined folds by concatenating per-fold bootstrap-mean distributions, giving multi-fold protocols a per-fold-sized CI on a pooled-OOS estimate and spuriously inflating walk-forward MDE on 1h/4h. The wrapper now uses a test-size-weighted, per-resample average of per-fold bootstrap means (stratified pooled-OOS bootstrap); single-fold is bit-identical to the frozen referee. The numbers below are the corrected re-run.

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `reference_reproduction_pass: true`, `hsplit_verdict_by_domain: {5m: SUPPORTED, 1h: SUPPORTED, 4h: FALSIFIED}`.
- `protocol_draw_verdicts.csv`: 594,000 rows, matching the scoped draw/protocol/referee/alpha budget.
- `reference_reproduction_check.csv`: 9/9 domain/alpha rows have `fpr_consistent = true` and `mde_consistent = true`.
- At `alpha0=0.05`, gate FPR was `0/2000` for every domain/protocol, Wilson half-width `0.000959`.
- At `alpha0=0.05`, gate MDEs:
  - 5m: single `1.0`, walk-forward `1.0`, purged CV `1.0` bps.
  - 1h: single `4.0`, walk-forward `4.0`, purged CV `4.0` bps.
  - 4h: single `12.0`, walk-forward `8.0`, purged CV `8.0` bps.
- `protocol_comparison.csv`: 5m and 1h non-material for both alternatives; 4h walk-forward and purged CV both material with delta `-4.0` vs margin `2.4` (lower MDE — more OOS rows).
- Matched-draw CI widths now decrease with `effective_n` (single 2.57 @1056 > walk-forward 1.74 @1760 > purged-CV 1.24 @3515), confirming the artifact is fixed. Re-audit verdict PASS.

### Hypothesis-Specific Conclusion

**PARTIALLY REFUTED**

H-split is SUPPORTED on 5m and 1h and FALSIFIED only on 4h. Unlike the original run, the falsification is a single domain and points the other way: the more-OOS alternative protocols (walk-forward ~0.5n, purged CV ~all n) detect a one-grid-step smaller edge than the conservative single split (~0.3n OOS) at the data-poorest domain. This is an OOS-sample-size effect (adversarial-review F02), not a referee-logic change, and FPR stays controlled.

### Hypothesis-Agnostic Observations

- Walk-forward and purged CV agree at 4h, so the effect tracks OOS sample size, not a specific protocol; a common-OOS-window ablation would isolate it (out of predeclared scope).
- The single-split reference reproduction (bit-identical to the frozen referee) makes the protocol deltas interpretable; a multi-fold-specific check (CI scales with pooled-OOS size) is now a standing audit requirement.
- EXP-010 supplies corrected robustness context for EXP-011: 5m/1h split-robust, 4h split-sensitive in the more-sensitive direction.

---

## EXP-011 - Predeclared-Loss Operating-Point Synthesis & Recommendation

**Status**: RECOMMENDATION DELIVERED (exploratory)
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through upstream calibration artifacts)
**Data Views / Feature Categories**: Result-level artifacts from EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, and EXP-010; no market-data or chart-type views loaded

### Hypothesis Tests

1. **Hypothesis / exploratory question**: Given three loss functions predeclared in full, which L5 threshold multiplier on the frozen EXP-006 tau-frontier should Phase 002 recommend per domain, and is that recommendation robust across Loss A/B/C?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain for headline recommendation.
- **Data Views / Feature Categories**: Frozen result-level artifacts only; no raw market data, no chart-type views, no new draws, and no referee rerun.
- **Features**: EXP-006 tau-frontier MDE/FPR/TPR; EXP-003 draw-level effect estimates for sub-material reconstruction; EXP-007 tau=0 sub-material check; EXP-008 per-instrument overlay; EXP-009 real-effect location overlay; EXP-010 split overlay; EXP-005 non-blindness context.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; primary `alpha0=0.05`; tau frontier `{0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0}` times materiality; materiality buffers 0.5/1.5/3.0 bps; Loss A/B/C fixed as in `scope.md`.
- **Exclusions**: Adoption/freezing of a new referee, loss reweighting, new thresholds, per-instrument headline recommendations, walk-forward re-selection, chart-type signals, and incremental-information candidate design.
- **Constraints**: EXP-003/005/006/007/008/009/010 dependency tokens complete; final 30% global holdout never loaded; result tables inherit real-price `Close` outcome discipline from upstream calibration experiments; EXP-011 recommendation is a Phase 002 recommendation only.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `submaterial_repro_check: true`, `inconclusive_domains: []`, and all dependency tokens `COMPLETE`.
- `decision_table.csv`: 21 rows = 3 domains x 7 tau multipliers; every row reportable with FPR Wilson upper `0.000959478516832434`.
- `sub_material_by_tau.csv`: 210 rows; audit confirmed the decision-table `sub_rate` values match the reconstructed operating-MDE rows.
- `recommendation.csv`:
  - 5m: headline tau `0.75`, MDE `0.5` bps, sub-material rate `0.39759036144578314`, Loss A/B `0.75`, Loss C `0.25`, `LOSS_SENSITIVE`, driver `sub_material`.
  - 1h: headline tau `0.25`, MDE `2.0` bps, sub-material rate `0.026223776223776224`, Loss A/B `0.25`, Loss C `0.0`, `ROBUST`.
  - 4h: headline tau `0.5`, MDE `8.0` bps, sub-material rate `0.0`, Loss A/B `0.5`, Loss C `0.0`, `LOSS_SENSITIVE`, driver `blind_band`.
- `adoption_rule.json` (re-run, data-derived caveats): EXP-005 detection `DETECTED_FLOOR` for all domains; EXP-009 `n_at_or_above_mde = 0` for every domain; per-instrument material overlays on EURUSD (1h) and EURUSD/XAUUSD (4h); walk-forward materiality false on 5m and 1h and true on 4h (corrected EXP-010). `run_metadata.method_notes` records the Loss C zero-FPR degeneracy and the Loss A MDE-before-sub-material trade; `scoped_overlays_complete = true`.
- Re-audit verdict PASS: independent loss recomputation matched all saved Loss A/B/C selections; deps hard-gated; sub-material tau=0 reproduction PASS.

### Hypothesis-Specific Conclusion

**RECOMMENDATION DELIVERED (exploratory)**

EXP-011 has no pass/fail hypothesis, but its scoped deliverable is complete. The primary predeclared loss recommends tau `0.75` (5m), `0.25` (1h), and `0.5` (4h); 1h is cross-loss robust, while 5m and 4h are loss-sensitive. No operating point is adopted in Phase 002.

### Hypothesis-Agnostic Observations

- The strict gate is already an honest detection floor on the EXP-005 scoped realistic candidate, so sub-strict tau recommendations are sensitivity-headroom choices, not corrections for demonstrated blindness.
- EXP-009 found no scoped untuned strategy effect at or above any domain MDE, so the recommendation affects calibration sensitivity more than a currently observed real candidate.
- Under the corrected EXP-010, only **4h** requires stricter Phase 003 ratification for split sensitivity (1h is now split-robust); the 4h shift is toward a lower MDE under more-OOS protocols.
- Loss C is a weak corroborator on the zero-FPR substrate (monotone toward the lenient endpoint), and Loss A can recommend a tau* with a non-trivial sub-material rate (5m) — read tau* with its sub_rate.
- Per-instrument overlays suggest pooled recommendations may mask lower achievable sensitivity in EURUSD/1h and EURUSD/XAUUSD 4h.

---

## EXP-012 - Fresh-Draw Loose Referee Ratification

**Status**: SUPPORTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; fresh synthetic known-null and known-positive draws; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: On each domain, the EXP-011-recommended loose operating point reproduces its Phase 002 operating characteristics on fresh synthetic draws: gate FPR <= alpha0 at D-prec precision, MDE within one edge-grid step of Phase 002, sub-material pass rate within tolerance and below the 0.50 ceiling, and for 4h, split-protocol agreement.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: fresh known-null and known-positive draws, fixed EXP-011 tau point, loose and strict referee verdicts, FPR/TPR/MDE summaries, sub-material pass-rate reconstruction, 4h single-vs-anchored-walk-forward split gate.
- **Parameter ranges**: tau multipliers 5m `0.75`, 1h `0.25`, 4h `0.5`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; 500 null draws per generator, 500 positive draws per edge; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: tau re-selection, threshold tuning, real candidate signals, chart-type candidates, bid/ask spread inference, and global holdout use.
- **Constraints**: EXP-001 PASS and EXP-003/EXP-010/EXP-011 COMPLETE required; first-70% slice only; real domain `Close` returns; fresh seed payloads disjoint from Phase 001/002 inputs.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{EXP-001: PASS, EXP-003: COMPLETE, EXP-010: COMPLETE, EXP-011: COMPLETE}`.
- Fresh seed check: `payload_overlap_count = 0`; 6 benign 32-bit integer collisions versus about 7.1 expected by chance.
- `adoption_decisions.csv`: all domains `ADOPT_LOOSE`.
- At `alpha0=0.05`, loose FPR = `0/4000` in 5m, 1h, and 4h; Wilson half-width `0.000479739`.
- Fresh loose MDEs exactly match Phase 002: 5m `0.5`, 1h `2.0`, 4h `8.0` bps.
- Sub-material rates: 5m `0.3991389913899139` vs Phase 002 `0.39759036144578314`; 1h `0.027469316189362946` vs `0.026223776223776224`; 4h `0.0` vs `0.0`.
- 4h split gate: single and anchored walk-forward loose MDE both `8.0` bps, FPR both `0.0`, `protocols_agree = true`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All three domains satisfy the frozen adoption rule. Phase 003 adopts the EXP-011 loose referee point for 5m/1h/4h rather than falling back to strict.

### Hypothesis-Agnostic Observations

- The fresh-draw ratification addresses synthetic seed-selection Goodhart risk, not fresh market-regime risk.
- 5m still carries a material sub-material pass rate (~0.40), but it stayed within the predeclared adoption rule and below the 0.50 ceiling.
- Later candidate screens can report strict plus adopted-loose outputs, but programme-level multiplicity remains outside this suite.

---

## EXP-013 - Incremental Substrate Validation

**Status**: SUPPORTED — re-validated 2026-06-04 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F01 across-draw redundancy verdict + `UNDER_POWERED` class; F04 contiguous-series block length). Remains PASS with three high-cost cells reclassified `UNDER_POWERED`. Numbers below reflect the rerun.
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; seeded R/C incremental known-truth substrate

### Hypothesis Tests

1. **Hypothesis**: The incremental substrate recovers a planted marginal edge within `max(0.5 bps, 15% of m)` and reads no phantom positive incremental edge for the redundancy null where R and C share structure but C adds no marginal edge.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice.
- **Features**: seeded blockwise latent state, R-only/C-change/overlap/inactive masks, model-free marginal net P&L, positive planted marginal edge, redundancy null, bootstrap intervals, denominator and cost accounting.
- **Parameter ranges**: episode lengths 5m `24`, 1h `8`, 4h `4`; 100 positive draws per edge; 100 redundancy draws; inherited edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: incremental MDE calibration, golden fixtures, real candidate signals, chart-type candidates, linear residualization as qualifying evidence, and global holdout use.
- **Constraints**: EXP-001 PASS and Track B predeclaration token required; first-70% slice only; real domain `Close` returns; denominator is rows where C changes the combined book relative to R-alone.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `measurements_produced: true`, `recovery_fail: false`, `phantom_edge: false`, `powered_null_cells: 9`, `insufficient_return_cells: 0`, `redundancy_verdict_basis: across_draw_distribution`.
- `positive_recovery.csv`: 108/108 cells PASS. Maximum absolute recovery error `0.39608151988927` bps, below tolerance.
- `redundancy_null.csv`: 8 `PASS`, 3 `UNDER_POWERED` (BTCUSD/1h, BTCUSD/4h, USTEC/4h), 1 `NULL_COST_DOMINATED` (XAUUSD/4h); 0 `PHANTOM_EDGE`.
- Verdict basis is the across-draw distribution (F01): the most positive across-draw mean across all 12 cells is `-0.041182` bps, so no cell has even a positive point estimate; the 3 `UNDER_POWERED` cells have across-draw CI half-width ≥ materiality.
- `substrate_integrity.csv`: C-change denominator fraction range `0.24983388704318937` to `0.2504520795660036`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The Track B incremental substrate is validated. It recovers planted marginal edge and does not manufacture positive incremental evidence from shared R-C structure.

### Hypothesis-Agnostic Observations

- The redundancy-null cells read negative (cost drag) under the confirmed incremental cost model, not as phantom positives; one cell (XAUUSD/4h) is adequately-powered cost-dominated, and three (BTCUSD/1h, BTCUSD/4h, USTEC/4h) are under-powered (CI too wide to bound a phantom) and disclosed rather than passed.
- The substrate gate passes, but later calibration still needs to prove finite MDE under dependence stress.

---

## EXP-014 - Incremental Referee Golden-Fixture Correctness

**Status**: SUPPORTED — re-validated 2026-06-04 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F04 contiguous-series block length): 7/7 verdicts and 35/35 leg states reproduced unchanged; `effective_n` now episode-aware (`276.9` on `all_pass`); EXP-013 dependency re-confirmed PASS.
**Date**: 2026-06-04
**Instruments**: Fixture labels only; no market data read
**Data Views / Feature Categories**: Deterministic in-memory return-space and R/C position fixtures

### Hypothesis Tests

1. **Hypothesis**: The incremental referee reproduces predeclared hand-computed verdicts on deterministic golden fixtures, exposes all gate legs without short-circuiting, and correctly generalizes L3 from naive control to reference control.

### Scope

- **Instruments**: Fixture labels only.
- **Data Views / Feature Categories**: deterministic fixture arrays; no Parquet market-data load.
- **Features**: seven fixture verdicts, L1-L5 expected states, no-short-circuit leg exposure, L3 reference-control isolation.
- **Parameter ranges**: primary `alpha0=0.05`; 1000 bootstrap resamples; fixtures `all_pass_incremental`, L1-L5 fail fixtures, and `redundant_shared_structure`.
- **Exclusions**: MDE calibration, dependence-grid measurement, real candidate signals, chart-type candidates, and global holdout use.
- **Constraints**: EXP-013 PASS and Track B predeclaration token required.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `verdicts_reproduced: true`, `leg_states_reproduced: true`, `all_legs_exposed_no_short_circuit: true`.
- `fixture_results.csv`: 7/7 fixture verdicts match expected.
- `leg_exposure_matrix.csv`: 35/35 L1-L5 checks PASS; all legs exposed for every fixture.
- `l3_reference_control_fail` rejects despite standalone-looking edge, isolating the incremental-beyond-R requirement.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The incremental referee logic is correct under the confirmed leg mapping and may be used for EXP-015 calibration.

### Hypothesis-Agnostic Observations

- This experiment validates logic wiring only; it does not measure operating characteristics.
- The fixture suite should remain a regression target if the incremental unit is revised.

---

## EXP-015 - Incremental Referee Portfolio-Fitness Calibration

**Status**: REFUTED — re-validated 2026-06-05 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F03 per-leg + per-instrument diagnostics; F04 no-op for the per-row grid). Outcome stands REFUTED; the failure is now attributed to the L2 standalone-significance leg driven by BTCUSD. Numbers below reflect the rerun.
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; incremental R/C dependence-grid known-truth draws

### Hypothesis Tests

1. **Hypothesis**: The incremental referee has a finite portfolio-fitness MDE at FPR <= `alpha0` on each domain, and redundancy-null FPR remains controlled under the checkpoint's R-C dependence grid.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice.
- **Features**: redundancy-null FPR, positive TPR/MDE, rho/overlap/lag/reference-strength dependence grid, construction diagnostics, denominator summaries, worst-case domain MDE rule.
- **Parameter ranges**: rho labels `{independent, moderate, high}`; overlap `{low, medium, high}`; lag `{synchronous, c_lags_r_1, c_leads_r_1}`; reference strength `{null_R, R_at_strict_mde}`; alpha grid `{0.10, 0.05, 0.01}`; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: real candidate signals, chart-type candidates, re-tuning estimator or leg mapping, standalone referee ratification, suite integration, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-014 PASS, and EXP-003 strict MDE map required; first-70% slice only; real domain `Close` returns; construction-invalid cells reported explicitly.

### Results / Observations

- `run_metadata.json`: `overall_status: REFUTED`, dependencies `{EXP-013: PASS, EXP-014: PASS, EXP-003: FOUND}`.
- `domain_mde_summary.csv`:
  - 5m: finite MDE cells `41`, failing cells `1`, construction-invalid/underpowered cells `12`, status `REFUTED`.
  - 1h: finite MDE cells `40`, failing cells `2`, construction-invalid/underpowered cells `12`, status `REFUTED`.
  - 4h: finite MDE cells `40`, failing cells `2`, construction-invalid/underpowered cells `12`, status `REFUTED`.
- Failing cells are all synchronous high-overlap `null_R` contexts: high rho/high overlap on 5m; moderate and high rho/high overlap on 1h and 4h.
- Accepted-cell FPR is controlled: max FPR `0.0` on 5m and `0.01` on 1h/4h; no cell exceeds `alpha0 = 0.05`.
- `construction_diagnostics.csv`: 12 construction-invalid cells per domain, all high-rho low/medium-overlap combinations marked `target_rho_infeasible_for_overlap`.
- F03 attribution (`leg_pass_rates.csv`, `tpr_by_instrument.csv`): in every failing cell the verdict pass rate equals the L2 standalone-significance pass rate (5m/high `0.75`, 1h/mod `0.784`, 1h/high `0.716`, 4h/mod `0.63`, 4h/high `0.382`) with L1/L4/L5 at `1.0` and L3 ≥ `0.97`; BTCUSD's standalone TPR is `0.0`–`0.136` at the 32 bps ceiling versus the other instruments at/near `1.0`, holding the pooled rate below the `0.80` power floor.
- Worst finite PASS-cell MDEs are 5m `32.0`, 1h `24.0`, 4h `32.0` bps, but these are not adoptable because failing cells exist.
- Audit verdict PASS: results are valid for interpretation; no critical or warning issues.

### Hypothesis-Specific Conclusion

**REFUTED**

The incremental referee controls FPR in accepted cells but fails the finite-MDE requirement in every domain. The Track B portfolio-fitness unit is not validated and cannot be frozen for Phase 004 use.

### Hypothesis-Agnostic Observations

- The refutation is sensitivity-driven, not false-positive-driven, and is localized to the L2 leg / BTCUSD by the F03 diagnostics — not a substrate or logic defect.
- EXP-013 and EXP-014 still stand: the substrate and logic are valid, but this calibrated operating point fails under dependence stress.
- Phase 003 cannot reach FULL_FRAMEWORK_CONCLUDED without a new incremental-unit follow-up or an explicit standalone-only rescope.

---

## EXP-016 - Assembled Suite Composition Anchor

**Status**: BLOCKED
**Date**: 2026-06-04
**Instruments**: Not measured
**Data Views / Feature Categories**: Blocker manifest only; no suite-composition measurement produced

### Hypothesis Tests

1. **Exploratory question**: Does the assembled strict, ratified-loose, and incremental suite wire both reject and pass paths end to end on the EXP-009 dogfood negative path and a synthetic positive suite-level fixture?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for the planned dogfood path; not measured in the blocked run.
- **Data Views / Feature Categories**: planned 5m/1h/4h dogfood domains and synthetic positive fixture; blocked run emits only dependency and blocker manifests.
- **Features**: suite dependency manifest, dogfood reference-book precondition, positive fixture precondition, blocker report.
- **Parameter ranges**: not measured.
- **Exclusions**: inventing the dogfood reference book, changing EXP-012 adoption decisions, changing EXP-015 calibration, real signal exploration, chart-type candidates, and global holdout use.
- **Constraints**: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-015 COMPLETE, and `inputs/dogfood_reference_book.csv` required before measurement.

### Results / Observations

- `run_metadata.json`: `overall_status: BLOCKED`, `measurements_produced: false`.
- `dependency_manifest.csv`: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-015 metadata `REFUTED`, upstream result files found, dogfood reference book MISSING.
- `blocker_report.csv`: two blockers:
  - EXP-015 `overall_status='REFUTED'`, required `COMPLETE`.
  - missing `python/experiments/EXP-016/inputs/dogfood_reference_book.csv`.
- No suite manifest, expected-output matrix, positive fixture, standalone verdicts, incremental verdicts, or composition summary was produced.
- Audit verdict PASS for blocked-state handling.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE / BLOCKED**

The composition question is unanswered. EXP-016 correctly stopped before measurement because the suite was not assembleable under the approved scope.

### Hypothesis-Agnostic Observations

- The blocked result confirms governance discipline: the script does not invent an undefined dogfood reference book and does not proceed after EXP-015 refutes the incremental unit.
- Phase 003 cannot be reported as full-framework concluded from the current EXP-016 artifact set.

---

## EXP-017 - Revised Incremental Referee Golden-Fixture Correctness

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: Fixture labels only; no market data read
**Data Views / Feature Categories**: Seeded-deterministic in-memory return-space and R/C position fixtures

### Hypothesis Tests

1. **Hypothesis**: The revised incremental referee, with L2 removed and retained legs L1, L3, L4', and strict L5, reproduces predeclared fixture verdicts, exposes every retained leg without short-circuiting, omits L2 from gate output, and verifies the former standalone-L2 failure fixture now passes under the revised formula.

### Scope

- **Instruments**: Fixture labels only; not a market-behavior experiment.
- **Data Views / Feature Categories**: Deterministic return-space and R/C position fixtures; no market Parquet load.
- **Features**: seven fixture verdicts, retained-leg states for L1/L3/L4'/L5, L2-absence checks, legacy-L2 diagnostic, mismatch report.
- **Parameter ranges**: `alpha = 0.05`, 1000 bootstrap resamples, revised gate `L1 and L3 and L4_prime and strict_L5; L2 absent`.
- **Exclusions**: Operating-characteristic calibration, MDE measurement, real candidate signals, chart-type candidates, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-014 PASS, and active Phase 003b design confirmations required; fixtures are seeded-deterministic rather than closed-form analytic.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `verdicts_reproduced: true`, `retained_leg_states_reproduced: true`, `all_retained_legs_exposed_no_short_circuit: true`, `l2_absent_from_revised_gate_output: true`.
- `fixture_results.csv`: 7/7 fixture verdicts PASS; `mismatch_details.csv` is empty.
- `leg_exposure_matrix.csv`: 28/28 retained-leg checks PASS, all retained legs exposed.
- `l2_absence_check.csv`: 7/7 PASS; emitted revised-gate legs contain L1, L3, L4', L5, and supporting numeric fields only.
- `l2_absent_former_standalone_fail`: legacy L2 diagnostic fails (`legacy_l2_pass_diagnostic = false`, `legacy_l2_ci_lower_bps = -3.3855586505512987`) while revised verdict PASS.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

EXP-017 validates the revised incremental-referee logic gate. It confirms L2 removal, retained-leg exposure, and expected fixture behavior, so EXP-018 may use EXP-017 as a PASS dependency.

### Hypothesis-Agnostic Observations

- This is a logic correctness gate only; it does not measure false-positive risk, power, or MDE.
- The fixture suite should remain the regression test for any future change to `revised_incremental_gate_row()`.

---

## EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; seeded R/C dependence-grid known-truth draws

### Hypothesis Tests

1. **Hypothesis**: The revised incremental referee has a finite portfolio-fitness MDE at FPR <= `alpha0` on each domain across the construction-accepted unchanged P3-D-dependence grid, and redundancy-null FPR remains controlled at the synchronous/high-overlap/null_R corner where EXP-015 failed.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type candidates.
- **Features**: redundancy-null FPR, positive-edge TPR/MDE, retained-leg pass rates, per-instrument TPR, denominator summaries, construction diagnostics, explicit binding-corner summary.
- **Parameter ranges**: rho `{independent, moderate, high}`; overlap `{low, medium, high}`; lag `{synchronous, c_lags_r_1, c_leads_r_1}`; reference strength `{null_R, R_at_strict_mde}`; alpha grid `{0.10, 0.05, 0.01}`; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps; 125 draws per instrument/cell.
- **Exclusions**: Real candidate signals, chart-type candidates, retuning the revised gate, changing strict or ratified-loose referees, suite integration, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-017 PASS, and EXP-003 strict MDE map required; headline domain MDE is worst-case finite accepted-cell MDE.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`; domain statuses all `SUPPORTED_WITH_UNDERPOWERED_CELLS`; domain MDEs 5m `12.0`, 1h `16.0`, 4h `32.0` bps.
- `construction_diagnostics.csv`: 810,000 construction rows; 630,000 accepted and 180,000 invalid. Invalid reason is `target_rho_infeasible_for_overlap`.
- `fpr_summary.csv`: 126 accepted cells PASS, 36 construction-invalid cells; accepted-cell FPR range `0.0` to `0.004`, max FPR Wilson half-width `0.006684203250090802`.
- `cell_mde_summary.csv`: 126 PASS cells, 36 CONSTRUCTION_INVALID cells; 0 FPR or no-finite-MDE failures.
- `domain_mde_summary.csv`: each domain has 42 finite MDE cells, 0 failing cells, 12 construction-invalid/underpowered cells, total 54 cells.
- `binding_corner_summary.csv`: all nine synchronous/high-overlap/null_R corner rows PASS. Moderate/high-rho stress MDEs are 5m `1.0`, 1h `8.0`, and 4h `24.0` bps.
- Audit recomputation: FPR and TPR counts from `draw_verdicts.csv` match summary files with 0 mismatches; domain MDE recomputation matches `domain_mde_summary.csv`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The revised incremental / portfolio-fitness unit validates on every construction-accepted dependence-grid cell. FPR is controlled, finite MDEs exist in all domains, and the explicit EXP-015 stress corner now passes.

### Hypothesis-Agnostic Observations

- The validated revised-unit MDE map is materially conservative: 12/16/32 bps on 5m/1h/4h.
- The 36 disclosed non-PASS cells are construction-infeasible high-rho/low-overlap contexts, not failed inference cells.
- The EXP-015 refutation was repaired by removing standalone L2; the revised unit now tests portfolio fitness, not standalone C significance.

---

## EXP-019 - Assembled Suite Composition Anchor

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for dogfood path; EURUSD fixture label for synthetic positive path
**Data Views / Feature Categories**: 5m, 1h, and 4h OHLC domains for dogfood path; deterministic synthetic positive fixture for pass path

### Hypothesis Tests

1. **Exploratory integration claim**: Conditional on EXP-018 validation and the confirmed dogfood reference book, the assembled suite of frozen strict referee, EXP-012 ratified-loose referee, and EXP-018 revised incremental unit composes end to end on both the EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for real dogfood path; EURUSD fixture label for synthetic positive path.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice for dogfood; in-memory synthetic arrays for positive fixture.
- **Features**: strict and loose/fallback standalone verdicts, revised incremental verdicts, dogfood reference-book manifest, suite manifest, expected-output matrix, positive fixture manifest, composition summary.
- **Parameter ranges**: strict MDEs 1/4/12 bps; EXP-012 effective loose MDEs 0.5/2/8 bps; EXP-018 revised incremental MDEs 12/16/32 bps on 5m/1h/4h; dogfood reference book `donchian_20`; candidates `ma_20_50`, `rsi_14`, `bollinger_20_2`, `macd_12_26_9`, `roc_20`.
- **Exclusions**: New real signal exploration, chart-type candidates, suite retuning, changing upstream adoption decisions, programme-level multiplicity control, and global holdout use.
- **Constraints**: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-018 COMPLETE with finite domain MDEs, and predeclared dogfood reference book required before measurement.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`; all six domain/path statuses expected.
- `dependency_manifest.csv`: EXP-009, EXP-012, and EXP-018 metadata COMPLETE; strict MDE map, dogfood artifacts, adoption decisions, EXP-018 domain MDE summary, dogfood reference book, and dogfood reference manifest FOUND.
- `suite_manifest.csv`: strict MDEs 1/4/12 bps, ratified-loose effective MDEs 0.5/2/8 bps, revised incremental MDEs 12/16/32 bps on 5m/1h/4h.
- `suite_composition_summary.csv`: dogfood negative path has 0 strict passes, 0 loose/fallback passes, 0 incremental passes in every domain; status `REJECT_PATH_EXERCISED` for 5m/1h/4h.
- `suite_composition_summary.csv`: synthetic positive path has 1 strict pass, 1 loose/fallback pass, 1 incremental pass in every domain; status `PASS_PATH_EXERCISED` for 5m/1h/4h.
- `positive_fixture_manifest.csv`: 3/3 rows `nonredundancy_ok = true`, active overlap fraction `0.0`, signed R-C rho near zero.
- Audit verdict PASS: no critical or warning issues. Audit notes a stale earlier `blocker_report.csv`, superseded by current completed metadata and manifests.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The assembled suite composes end to end. The dogfood negative path rejects across all domains, and the synthetic positive path passes strict, ratified-loose, and revised incremental components across all domains.

### Hypothesis-Agnostic Observations

- EXP-019 is an integration anchor, not Phase 004 signal exploration.
- The concluded suite can now be recorded as `{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental / fitness unit}`.
- Phase 004 remains gated on documenting the programme-level multiplicity registry before real candidate screening begins.

---

## VAL-001 - Data Architecture Temporal Integrity Validation

**Status**: SUPPORTED (rev. 3)
**Date**: 2026-06-01
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break level 3; Renko ATR period 14; Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: The available Xen data architecture preserves temporal alignment across scoped time-bar, timeframe, and chart-type views — with no future-timestamp or cross-view misalignment in any emitted row, and no structural look-ahead in prefix-stability probes positioned at the head, middle, and tail of the analysis slice — when every derived view is generated only from the first 70% of each chronologically ordered base dataset.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: Base 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break, Renko, and Heiken Ashi generated from each scoped source timeframe.
- **Features**: Required time-bar schema, OHLC integrity, `CloseTime`, `SourceCloseTime`, `SourceCount`, Heiken Ashi real OHLC preservation, prefix stability, deterministic regeneration, and negative-control detection.
- **Parameter ranges**: Line Break `level=3`; Renko `atr_period=14`; timeframe periods `1`, `15`, and `60` minutes.
- **Exclusions**: Final 30% global holdout, tick data, bid/ask spread, trading costs, strategy backtests, return forecasting, parameter tuning, randomized tests, and persisted generated chart-type datasets.
- **Constraints**: All validation uses the first 70% chronological analysis slice only. Time bars align by `CloseTime`; Line Break and Renko align by `SourceCloseTime`; Heiken Ashi aligns by `CloseTime`. No P&L or return metrics are in scope.

### Results / Observations

- `validation_checks.csv`: 416 PASS, 0 FAIL, 0 INCONCLUSIVE (rev. 3).
- Real-instrument checks: BTCUSD 98/98 PASS; EURUSD 98/98 PASS; USTEC 98/98 PASS; XAUUSD 98/98 PASS.
- Synthetic control checks: 24/24 PASS, including 23/23 detected negative controls (one per data-integrity and alignment check) plus 1 golden fixture.
- Prefix-stability look-ahead probes: 60 checks (head/middle/tail for 1-minute views, `full` for 15m/60m), 0 diverged cuts; determinism: 36/36 PASS.
- Analysis rows after first-70% slicing (unchanged from rev. 2): BTCUSD 1,088,960; EURUSD 872,242; USTEC 830,541; XAUUSD 830,671.
- Resample oracle comparisons: 0 rows only in production, 0 rows only in oracle, and 0 OHLC mismatches for every 15-minute and 60-minute instrument comparison.
- Heiken Ashi density: 1.0 for every instrument/timeframe combination.
- Line Break event-density range: 0.195149 to 0.275556 event rows per source row.
- Renko event-density range: 0.222171 to 0.298266 event rows per source row.
- Renko duplicate-source denominator context: 107,824 duplicate `SourceCloseTime` groups and 128,556 extra same-source rows across all scoped outputs.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The current data layer passed the temporal-integrity readiness gate. The conclusion is supported because every scoped positive check passed and every injected negative control was detected, satisfying the predefined success criteria.

### Hypothesis-Agnostic Observations

- Renko same-source duplicate rows are common enough to require explicit denominator reporting in future chart-type experiments.
- Future downstream strategy or signal experiments can rely on timestamp alignment as validated here, but they must still evaluate returns and P&L on real time-matched prices.
- Changes to data-loading conventions, chart generators, or `aggregate_ohlc()` should trigger a new VAL rerun before dependent research uses the changed layer.
- rev. 3 hardened the suite's detection power: every base-integrity, resample, sparse-chart, Heiken Ashi, schema, look-ahead, and determinism check now has a matching negative control, and look-ahead is probed at the head/middle/tail of each slice. Byte-identical reproduction of rev. 2 generator outputs confirms deterministic generation; future VAL reruns should keep this control-per-check standard.
- The Line Break and Renko generators were manually verified against `architecture.md`; note Xen Renko intentionally differs from classic TradingView Renko (SMA-of-TR ATR, 1-brick symmetric reversal, first-close anchor).
