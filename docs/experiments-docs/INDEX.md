# Experiments Index (Comprehensive)

## Current Infrastructure Tasks

| Task | Status | Focus | Document |
| --- | --- | --- | --- |
| **INFR-001 — cTrader Branch & Strategy-Host Integration** (2026-06-06) | **COMPLETE — all VAL-class gates PASS (2026-06-06)** via VAL-002; closed under design.md v2 (§0 execution-model correction). | **Task A COMPLETE — it was the sole focus; the hard block is now lifted.** All four acceptance gates pass (design §6): (1) **transcription** — 108/108 C# ports vs Python references PASS; (2) **end-to-end integration** — all 12 cells (4 instruments × 3 domains) of real `Mode=StrategyHost` cTrader runs reproduce EXP-004/009 (24/24 REJECT, gate-stack `below_MDE`, `matched_reject`) through the unchanged frozen suite via the `xen.signals` ingestion harness; (3) **holdout fence** respected in every cell (in-robot self-guard + harness re-assertion); (4) **reproducibility** behavioral — 5m reproduces the console oracle to full float precision, 1h/4h differ ≤1.83 bps on cTrader's own feed (all far below MDE), per-run config recorded. The frozen qualification suite `{strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}` was carried in untouched. **Phase 004 / AVWAP signal exploration may now open**, behind its mandatory programme-level multiplicity-registry precondition (P3-§11, a Task-B artifact). Governed by VAL-class validation, not per-hypothesis governance. | [design.md](checkpoints/2026-06-06-INFR-001-ctrader-branch-integration/design.md) · [retrospective.md](checkpoints/2026-06-06-INFR-001-ctrader-branch-integration/retrospective.md) |

## Current Checkpoint Status

| Checkpoint | Status | Focus | Documents |
| --- | --- | --- | --- |
| 2026-06-09-007-avwap-tradability-and-isolation | ACTIVE — design opened 2026-06-09; follows Phase 006 (EVAL_SUPPORTED). No result yet. | **Answers tradability and decomposes the edge, before any holdout release.** Phase 006's per-event edge is gross of costs and undecomposed; EXP-023's per-bar REFUTED (incl. negative net after trend-change exits + cost) was not overturned. Two experiments, **dependency LOCKED**: **EXP-030** cost-bearing tradability under a predeclared event-level cost model (NOT the per-bar suite, NOT a flat subtraction) — the hard gate for holdout release; **EXP-031** edge isolation (entry-timing vs exit-rule) — runs **regardless** of EXP-030 (mechanism info is valuable even if the candidate fails on costs); neither blocks the other. Holdout release (EXP-032) DEFERRED + gated on EXP-030 EVIDENCE_FOR. HYP-001 recorded as open and **explicitly NOT confirmed** by EXP-028/029 (conditioned-on-event; trigger ≠ barrier), with a confound-free testable framing noted. Holdout sealed; no tuning. | [design.md](checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md) |
| 2026-06-08-006-avwap-evaluation-correction | **COMPLETED 2026-06-09 — EVAL_SUPPORTED (cTrader-confirmed)**; supersedes Phase 005. Amended 2026-06-09: EXP-028 omission recorded and EXP-029 appended. All three experiments complete (EXP-027 METHOD_VALID, EXP-028 EVAL_SUPPORTED, EXP-029 CONSISTENT/cTrader-confirmed); phase objective fully satisfied; retrospective written 2026-06-09. | **Fixes the evaluation vehicle Phases 004/005 mis-applied, then re-screens the faithful strategy.** Operator review found EXP-023/024/025 screened/diagnosed a ~6%-active event signal through a per-bar continuous-position referee calibrated only for ≥80%-active series (EXP-005). The strategy position rule was ~faithful; the **yardstick** was wrong. Three experiments: **EXP-027** defines + calibrates an event-level evaluation method (METHOD_VALID); **EXP-028** re-screens the faithful AVWAP strategy under it (Python-only; EVAL_SUPPORTED); **EXP-029** closed the cTrader per-bar streaming omission — the corrected C# strategy run on cTrader reproduced EXP-028 PRIMARY excess on all 3 domains (parity **CONSISTENT**; all 5 binding gates pass), upgrading EXP-028 to **cTrader-confirmed**. HYP-001 (line S/R) recorded as open, not in scope. Holdout sealed; no tuning. Root cause: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. Omission (now closed): `checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md`. | [design.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/design.md) · [retrospective.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/retrospective.md) · [EXP-028-omission.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md) |
| 2026-06-08-005-avwap-exit-and-branch-exploration | **HALTED 2026-06-08** (was ACTIVE) — superseded by Phase 006 before Stage B/C. Stage A diagnostics (EXP-024 MIXED_OR_INCONCLUSIVE, EXP-025 INCONCLUSIVE) inherited an evaluation-framing defect; EXP-026 `/EXIT` shelved; Stage C deferred. See [retrospective.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/retrospective.md) and the framing-divergence review. | **Continues `CF-AVWAP-001` after Batch 004-A closed BASELINE_BRANCH_REFUTED.** Three dependent stages. **(A) Diagnosis** (Python-only, no suite, no multiplicity slot): EXP-024 edge-dissipation decomposition completed with diagnostic `MIXED_OR_INCONCLUSIVE` — primary 5m resolves fork (b) entry/position dilution (+0.370 bps best bounded hold < 0.5 bps floor), 1h/4h unresolved due wide CIs, and no domain supports fork (a); EXP-025 direct AVWAP-line S/R test remains pending (gap #4 — never tested directly; EXP-021/022 tested continuation and completion, not reaction-at-line). **(B) EXIT screen**: EXP-026 `CF-AVWAP-001/EXIT` is **not automatically justified by EXP-024 alone**; mixed/inconclusive output requires explicit operator/governance handling before any `/EXIT` screen. **(C) Branch exploration**: `/LB` `/MB` `/ATR` detectors (gaps #2) and new `/ANCHOR` running-extreme-vs-significant-pivot (gap #1). `/ALPHA` `/BAND` parameter sensitivity deferred out of phase. Knife-edge guardrail: exit/detector rules come from structure, predeclared, measured once — no sweep, no post-result reselection. Holdout sealed. | [design.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md) |
| 2026-06-07-004-avwap-signal-exploration | COMPLETED — Batch 004-A baseline chain complete: EXP-020 SUPPORTED_FULL; EXP-021 SUPPORTED; EXP-022 SUPPORTED; **EXP-023 REFUTED**. | **First real signal-exploration phase; baseline branch screened to a clean negative.** The mandatory programme-level multiplicity/file-drawer registry is documented in `docs/signal-registry/multiplicity-registry.md`, and Batch 004-A registers only `CF-AVWAP-001` (Anchored VWAP on regime pivots). EXP-020 validated the first-branch substrate across all three domains; EXP-021 confirmed fixed-horizon bounce reaction (all 3 domains EVIDENCE_FOR, +3.8/+9.1/+37.6 bps); EXP-022 confirmed the band-target/trend-change lifetime method (rate diffs +23.9/+21.9/+26.4 pp, Holm p=0.0003). EXP-023 then screened the cTrader strategy-host AVWAP baseline through the **frozen suite** on emitted real prices: 12/12 cells admitted, C# transcription smoke PASS, but **0/12 strict, 0/12 ratified-loose, 0/12 revised-incremental passes → REFUTED** (effects ≪ frozen floors; high favorable-target rate 0.60–0.80 but ~0/negative net expectancy from trend-change exits + cost). This is a **baseline-branch negative, not COMPONENT_REFUTED** of CF-AVWAP-001 (design §8). Next AVWAP work requires new scoped experiments on registered non-baseline branches (LB/MB/ATR/ALPHA/BAND/EXIT), with no in-place baseline tuning. | [design.md](checkpoints/2026-06-07-004-avwap-signal-exploration/design.md) · [retrospective.md](checkpoints/2026-06-07-004-avwap-signal-exploration/retrospective.md) |
| 2026-06-05-003b-incremental-unit-redesign | COMPLETED — REVISED_UNIT_VALIDATED (EXP-017-019 executed and post-governance APPROVED 2026-06-05; retrospective written 2026-06-05) | **Track B follow-up succeeded.** EXP-017 validated the revised incremental-referee logic (7/7 fixture verdicts, 28/28 retained-leg checks, L2 absent). EXP-018 validated the revised portfolio-fitness unit on the construction-accepted dependence grid: FPR controlled in 126/126 accepted cells, finite worst-case MDEs 12/16/32 bps on 5m/1h/4h, and the EXP-015 synchronous/high-overlap/null_R stress corner passes in every domain; 36 infeasible high-rho/low-overlap cells are disclosed as construction-invalid. EXP-019 exercised both assembled-suite paths: EXP-009 dogfood rejects and synthetic positive passes across all domains. The concluded suite is now **{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}**. Phase 004 may open after its mandatory programme-level multiplicity registry precondition is documented. **Not a new programme phase — a revision; Phase 004 remains reserved for signal exploration.** | [design.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/design.md) · [retrospective.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/retrospective.md) |
| 2026-06-04-003-ratification-and-incremental-unit | COMPLETED — PARTIAL_SUCCESS (EXP-012-016 executed and reviewed; amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) applied and Track B re-validated; retrospective written 2026-06-05) | **Framework-conclusion attempt did not reach FULL_FRAMEWORK_CONCLUDED (outcome: PARTIAL_SUCCESS).** Track A succeeded: EXP-012 ratified and adopted the EXP-011 loose point on fresh seeds for 5m/1h/4h. Track B validated the substrate and logic gates (EXP-013/014) but EXP-015 refuted portfolio-fitness calibration because every domain had qualifying dependence cells with no finite MDE. EXP-016 correctly blocked before composition measurement because the incremental unit was not COMPLETE and the dogfood reference book was undefined. **Adversarial review (amendment A1) corrected the incremental inference layer (F04 contiguous-series block length), the EXP-013 redundancy verdict (F01 across-draw distribution + `UNDER_POWERED` class), and EXP-015 diagnosability (F03 per-leg/per-instrument tables); EXP-013→014→015 re-validated 2026-06-04/05 — direction unchanged: Track A SUPPORTED, Track B substrate/logic PASS (EXP-013 PASS with 3 cells now `UNDER_POWERED`; EXP-014 PASS, `effective_n` episode-aware), EXP-015 REFUTED with the failure attributed to the L2 standalone-significance leg driven by BTCUSD.** The concluded suite ships as **two referees only** (frozen strict + ratified-loose); the incremental/fitness unit is carried to a follow-up. **Operator decision recorded 2026-06-05 (retrospective §11): Path B — open a new incremental-unit follow-up checkpoint and fix the L2/BTCUSD calibration failure (and resolve the A1/F02 L4/L5 freeze precondition) before Phase 004**, rather than rescoping Phase 004 to standalone-only. Phase 004 stays blocked until that follow-up delivers a validated+calibrated incremental unit. | [design.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/design.md) · [retrospective.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/retrospective.md) |
| 2026-06-03-002-referee-refinement-and-stringency | COMPLETED (7/7 EXP executed, governance-APPROVED; retrospective written 2026-06-04) | Keystone spine item closed for the scoped realistic candidate (EXP-005); L5 threshold frontier measured (EXP-006); lenient-L5 structural-gain claim refuted because lenient equals the EXP-006 zero-buffer endpoint and drop-L5 (EXP-007); per-instrument MDE heterogeneity found in EURUSD/XAUUSD slower-domain cells (EXP-008); broadened simple-strategy dogfood stayed below every domain MDE (EXP-009); split robustness held on 5m/1h with only 4h falsified — and there the more-OOS protocols detect a lower MDE (EXP-010, corrected 2026-06-04: the original 1h/4h walk-forward MDE inflation was a multi-fold CI artifact); predeclared-loss synthesis recommends tau 0.75/0.25/0.5 on 5m/1h/4h, with adoption deferred to Phase 003 fresh draws (EXP-011). Characterization phase - recommends, does not adopt. | [design.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md) · [retrospective.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/retrospective.md) |
| 2026-06-01-001-thesis-qualification-calibration | COMPLETED | Build the 5-check gate-stack referee + calibration harness; measure per-domain (5m/1h/4h) FPR/TPR/economic-MDE for it and a minimal baseline (EXP-001→004). | [design.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/design.md) · [retrospective.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/retrospective.md) |


## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-06-08-006-avwap-evaluation-correction | COMPLETED — **EVAL_SUPPORTED (cTrader-confirmed)** (EXP-027/028/029 executed, all post-governance APPROVE; retrospective written 2026-06-09) | **The correction phase repaired the evaluation vehicle Phases 004/005 mis-applied, then re-screened the faithful strategy positive — confirmed on the production code path.** EXP-027 METHOD_VALID: a predeclared event-level method (per-event matched-control expectancy reusing the EXP-021/022 bootstrap/permutation/Holm machinery, recalibrated for the sparse regime on synthetic substrates only) shows controlled FPR (≤0.05 across the {3,6,12}% activity bracket) and finite MDE (1/4/32 bps on 5m/1h/4h) — the EXP-021/022 inference transfers to ~6%-active signals. EXP-028 EVAL_SUPPORTED: the unchanged faithful strategy is PRIMARY EVIDENCE_FOR on all three domains (+5.78/+23.38/+69.02 bps, Holm p=0.003) — the EXP-023 negative was a framing/dilution artifact, not absence of signal. EXP-029 CONSISTENT: the corrected, pyramid-inclusive C# `AvwapBounceModel` run bar-by-bar on cTrader reproduces EXP-028's PRIMARY excess on all three domains (\|Δeffect\|=0.007/0.054/0.000 bps; all five binding gates pass — entry signal ≥99.8% of EXP-020 triggers, pyramid counts ±0.5%, executed completion match rate 1.000), upgrading EXP-028 to cTrader-confirmed and extending VAL-002 pipeline parity to the AVWAP baseline. **Process lesson** (`EXP-028-omission.md`): a "faithful re-screen" must state its execution path (cTrader per-bar vs Python re-analysis) explicitly in scope; Stage 4 governance must check it against the lineage the faithfulness clause assumes. Open: HYP-001 (line S/R) untested; costs not deducted; holdout sealed. Does **not** overturn EXP-023's per-bar REFUTED (non-substitutable yardsticks). | [retrospective.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/retrospective.md) |
| 2026-06-08-005-avwap-exit-and-branch-exploration | **HALTED 2026-06-08** — `HALTED_FRAMING_INVALID` (before Stage B/C; superseded by Phase 006) | **Halted because Stage A diagnosed the signal *within* the wrong evaluation vehicle instead of questioning the vehicle.** EXP-023/024/025 screened/diagnosed a ~6%-active event signal through a per-bar continuous-position referee calibrated only for ≥80%-active series (EXP-005); EXP-023's negative is dominated by ~16× denominator dilution, EXP-024's fork-(b) leg is a per-bar-floor category mismatch, and EXP-025's metric is confounded by the trigger definition (HYP-001 still untested). EXP-021/022 per-event evidence is **not** invalidated. Retained findings: edge is relative-not-absolute; trend-change exits cut losers. Dispositions: EXP-023 SUPERSEDED, EXP-024 RETAINED (fork discounted), EXP-025 INCONCLUSIVE (non-informative for HYP-001); EXP-026 `/EXIT` SHELVED; Stage C deferred. Redirect → Phase 006 (fix evaluation vehicle, then re-screen). Review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. | [retrospective.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/retrospective.md) |
| 2026-06-07-004-avwap-signal-exploration | COMPLETED — **BASELINE_BRANCH_REFUTED** (EXP-020-023 executed; EXP-023 post-governance APPROVE; retrospective written 2026-06-08) | **The first real signal-exploration cycle reached its terminal screen and closed negative for the registered baseline branch.** EXP-020 SUPPORTED_FULL: the AVWAP state machine is deterministic and look-ahead safe, 12/12 cells reportable, 0 invariant failures. EXP-021 SUPPORTED: fixed-horizon bounce reaction positive on all domains (+3.8/+9.1/+37.6 bps, Holm p=0.0003). EXP-022 SUPPORTED: band-target/trend-change lifetime completion advantage positive on all domains (+23.9/+21.9/+26.4 pp, Holm p=0.0003). EXP-023 REFUTED: 12/12 cTrader cells admitted, same-feed Donchian reference aligned, holdout fence and C# smoke PASS, but 0/12 strict, 0/12 ratified-loose, and 0/12 revised-incremental passes; effects far below frozen floors. **Synthesis:** conditional AVWAP event evidence is real in this analysis set, but the untuned baseline position/exit overlay does not qualify as a cost-bearing tradable strategy. This is a baseline-branch negative, not a retirement of `CF-AVWAP-001`; follow-up requires new registered scopes such as EXIT, LB, MB, ATR, ALPHA, or BAND. | [retrospective.md](checkpoints/2026-06-07-004-avwap-signal-exploration/retrospective.md) |
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

---

## EXP-020 — AVWAP Event-Substrate Readiness

**Status**: SUPPORTED_FULL
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; registered CF-AVWAP-001 first-branch AVWAP state machine; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The Phase 004 Batch 004-A AVWAP definition can be implemented as a deterministic, look-ahead-safe event substrate with usable bounce-event coverage on at least one predeclared domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice. No chart-type views.
- **Features**: Sequential state machine: MA(20,50) regime detector, viable-pivot anchor selection, anchored VWAP (typical price weighted by TickVolume^0.75), MAD band (multiplier 1.0), arm/trigger bounce logic, invariant checks, deterministic replay, event-coverage readiness classification.
- **Parameter ranges**: fast MA 20, slow MA 50; TickVolume exponent 0.75; band multiplier 1.0; domains 5m/1h/4h; readiness thresholds: ≥30 total events, ≥8 per direction, ≥3 reportable instruments per domain.
- **Exclusions**: Market-edge claims, frozen-suite screening, cTrader strategy-host runs, alternative regime detectors, volume/band sweeps, exits/stops/targets, chart-type signals, parameter changes after results.
- **Constraints**: First-70% slice only; CloseTime ordering; sequential look-ahead-safe state machine; no returns, P&L, or excursion computation; zero-weight TickVolume skipped without division-by-zero; zero denominators reported as null.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED_FULL`, `ready_domain_count: 3`, `ready_domains: [5m, 1h, 4h]`, `invariants_ok: true`, `determinism_pass: true`, `holdout_violation_count: 0`, `total_events: 20911`.
- `domain_readiness.csv`: all three domains ready (4/4 reportable instruments each).
- `event_coverage.csv`: all 12 cells reportable. 5m: 4,327–5,978 events per instrument (density ~260–276 per 10k bars). 1h: 287–421 events (density ~207–242). 4h: 61–109 events (density ~199–246).
- `direction_balance.csv`: bull fractions 0.46–0.56 across all 12 cells; widest gap EURUSD/4h (39 bull, 31 bear).
- `invariant_checks.csv`: 192/192 checks PASS with 0 violations (16 checks × 12 cells).
- `determinism_check.csv`: 12/12 cells match event hashes and regime hashes between main and replay pass.
- `analysis_metadata.csv`: each instrument at exactly 70.00% analysis rows (BTCUSD 1,088,960/1,555,658; EURUSD 872,242/1,246,061; USTEC 830,541/1,186,488; XAUUSD 830,671/1,186,674).
- Audit: PASS, 0 critical, 0 warnings, 1 info note (EURUSD/4h moderate direction imbalance — both directions still reportable).

### Hypothesis-Specific Conclusion

**SUPPORTED_FULL**

All Evidence-FOR criteria are met: all invariant checks pass for every instrument/domain (0 violations across 192 checks), deterministic replay produces identical event tables and summary hashes (12/12 cells match), and all three domains are ready (4/4 reportable instruments). EXP-021 and EXP-022 may scope reaction and lifetime-move studies on any subset of the ready domains.

### Hypothesis-Agnostic Observations

- Event density is consistent across instruments and domains, with 5m providing the highest absolute counts.
- Direction balance is reasonable across all 12 cells; no domain or instrument shows degenerate single-direction coverage.
- The AVWAP state machine's re-arm sequencing is validated by the `rearm_monotonic` invariant (0 violations), confirming that the scope's arm/trigger/re-arm discipline is correctly implemented.
- The moderate EURUSD/4h direction gap (0.557 bull fraction) is a descriptive note for EXP-021 scoping, not a correctness issue.

---

## EXP-021 — AVWAP Bounce Reaction Study

**Status**: SUPPORTED
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 AVWAP bounce event substrate (CF-AVWAP-001 first branch)

### Hypothesis Tests

1. **Hypothesis**: AVWAP bounce events from the supported CF-AVWAP-001 first branch show better fixed-horizon direction-signed real-price reaction than matched non-event controls on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 events and regime summary. No chart-type views.
- **Features**: Same-regime matched controls (up to 5, min 3, by nearest anchor age/timestamp, 6-bar exclusion window around triggers), direction-signed log returns at 1/3/6 completed bars, instrument-averaged equal-weight domain effect estimator, regime-cluster bootstrap CI (10k resamples), stratified paired sign-permutation p-value (10k flips), Holm adjustment across 3 domains.
- **Parameter ranges**: primary horizon 3; secondary 1 and 6; MAX_CONTROLS=5; MIN_CONTROLS=3; EXCLUSION_BARS=6; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; alpha=0.05; N_BOOT=10,000; N_PERM=10,000.
- **Exclusions**: cTrader strategy-host screening or frozen-suite candidate qualification (EXP-023); lifetime target/trend-change outcomes (EXP-022); full strategy backtests, exits, stops, pyramiding, risk management, or position sizing; alternative AVWAP branches; parameter tuning or horizon selection after reading outcomes; percentage improvement against a zero baseline.
- **Constraints**: EXP-020 must be SUPPORTED_FULL with ready domains {5m, 1h, 4h}, 0 invariant violations, and deterministic replay match; first-70% slice only; CloseTime ordering; real domain Close outcomes; same-regime matching makes regime_id exact dependence clusters.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED`, dependency gate PASSED (EXP-020 SUPPORTED_FULL).
- `domain_reaction_tests.csv`:
  - 5m: effect +3.8 bps, CI [+3.5, +4.1], n=16,249, Holm p=0.0003, EVIDENCE_FOR.
  - 1h: effect +9.1 bps, CI [+5.1, +13.3], n=1,207, Holm p=0.0003, EVIDENCE_FOR.
  - 4h: effect +37.6 bps, CI [+22.3, +52.7], n=246, Holm p=0.0003, EVIDENCE_FOR.
- All three domains EVIDENCE_FOR. No secondary horizon is negative in any domain (all 1-bar and 6-bar effects positive).
- All 24 instrument×direction cells have positive mean paired differences at the primary horizon.
- `control_match_diagnostics.csv`: all 4 instruments reaction-reportable in all 3 domains. Mean controls per reportable event 4.5–5.0. Non-reportable events primarily `insufficient_same_regime_controls`.
- Audit verdict PASS: 0 critical, 0 warnings, 1 info note (4h effect partly driven by extreme BTCUSD control means).
- Cash in the analysis set only; holdout never loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All four Evidence-FOR criteria are met: (1) EXP-020 dependency gate passes; (2) all three domains are reaction-reportable with ≥4 reportable instruments each; (3) all three domains have primary effect > 0 bps, 95% CI lower bound > 0 bps, and Holm-adjusted p ≤ 0.05; (4) no domain has both secondary horizons negative. The fixed-horizon bounce reaction operationalization of CF-AVWAP-001/HYP-002 is supported.

### Hypothesis-Agnostic Observations

- The effect scales with domain (5m < 1h < 4h), consistent with larger per-bar moves at longer horizons.
- BTCUSD contributes the largest per-instrument effects, especially at 4h where same-regime controls have extreme negative means (−75 to −94 bps over 3 bars), inflating the paired contrast. The equal-weight domain estimator mitigates single-instrument dominance.
- The same-regime control restriction is binding (costing 8–14 events per 4h direction cell) but all domains still reach full reportability.
- Secondary horizons (1-bar, 6-bar) are positive and monotonic, ruling out a one-bar fluke or reversal artifact.

## EXP-022 — AVWAP Original Lifetime Move Study

**Status**: SUPPORTED
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 AVWAP event substrate (CF-AVWAP-001 first branch); band-target/trend-change lifetime method

### Hypothesis Tests

1. **Hypothesis**: Under the registered band-target/trend-change lifetime definition, AVWAP bounce events from the supported CF-AVWAP-001 first branch produce more favorable completed-move outcomes than matched non-event lifetime analogs on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 events and regime summary with frozen favorable/adverse targets at trigger. No chart-type views.
- **Features**: Same-regime matched controls (up to 5, min 3, by nearest anchor age/timestamp, 6-bar exclusion window around triggers), frozen event target distance transfer to control close (log bps), lifetime completion scan (favorable target, adverse target, trend-change, unfinished), instrument-averaged equal-weight domain rate-difference estimator (pp), regime-cluster bootstrap CI (10k resamples), stratified paired permutation p-value (10k flips), Holm adjustment across 3 domains, volatility-context ratio diagnostic (20-bar MAD of typical-price log returns).
- **Parameter ranges**: MAX_CONTROLS=5; MIN_CONTROLS=3; EXCLUSION_BARS=6; MIN_TARGET_COMPLETED=30; DOMAIN_MIN_INSTRUMENTS=3; LOCALVOL_WINDOW=20; VOL_CONTEXT_BOUNDS=[0.5, 2.0]; alpha=0.05; N_BOOT=10,000; N_PERM=10,000.
- **Exclusions**: Fixed-horizon reaction testing (EXP-021); cTrader strategy-host screening or frozen-suite candidate qualification (EXP-023); full strategy backtests, optimized exits, stops, pyramiding, risk management, or position sizing; alternative AVWAP branches; parameter tuning after reading lifetime outcomes; percentage improvement against a zero baseline.
- **Constraints**: EXP-020 must be SUPPORTED_FULL with ready domains {5m, 1h, 4h}, 0 invariant violations, and deterministic replay match; first-70% slice only; CloseTime ordering; real domain Close outcomes; trend-change is nearest later opposite MA(20,50) regime confirmation; same-regime matching makes regime_id exact dependence clusters; targets frozen at trigger time.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED`, dependency gate PASSED (EXP-020 SUPPORTED_FULL), all 4/4 instruments reportable in all 3 domains.
- `domain_lifetime_tests.csv`:
  - 5m: rate diff +23.9 pp, 95% CI [22.7, 25.1], expectancy diff +6.5 bps, median vol ratio 0.986, Holm p=0.0003, EVIDENCE_FOR.
  - 1h: rate diff +21.9 pp, 95% CI [17.2, 26.6], expectancy diff +27.0 bps, median vol ratio 1.024, Holm p=0.0003, EVIDENCE_FOR.
  - 4h: rate diff +26.4 pp, 95% CI [17.7, 35.3], expectancy diff +79.6 bps, median vol ratio 0.987, Holm p=0.0003, EVIDENCE_FOR.
- All three domains EVIDENCE_FOR. All domains have positive expectancy point estimates.
- Event favorable rates: 67–69% across domains. Control favorable rates: 42–45%.
- All median volatility-context ratios within [0.5, 2.0]; unfinished event fraction 0.0 for all domains.
- `lifetime_observations.csv`: 85,816 rows (events + controls across all cells).
- `control_lifetime_diagnostics.csv`: 24 instrument×direction rows. Insufficient same-regime controls: range 2–373 (5m dominates, as expected).
- Integrity counters: 4,604 invalid_target_events (geometrically impossible targets, excluded correctly), 0 tie_completions, 0 events_no_future_bars.
- Audit verdict PASS: 0 critical, 0 warnings, 2 info notes.
- Cash in the analysis set only; holdout never loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All predeclared Evidence-FOR criteria are met: (1) EXP-020 dependency gate passes; (2) all three domains are lifetime-reportable with ≥3 of 4 reportable instruments each; (3) all three domains have rate diff > 0 pp, 95% CI lower bound > 0 pp, and Holm-adjusted p ≤ 0.05; (4) all domains have positive expectancy point estimates; (5) no domain is volatility-context-confounded or censored. The original band-target/trend-change lifetime operationalization of CF-AVWAP-001/HYP-003 is supported on all three domains.

### Hypothesis-Agnostic Observations

- The favorable rate advantage is large (22–26 pp) and nearly identical across domains, suggesting the lifetime method captures a genuine event property rather than a domain-specific artifact.
- Expectancy scales with domain width (6.5 → 27.0 → 79.6 bps for 5m/1h/4h), reflecting larger per-move returns on wider targets.
- The volatility-context diagnostic (all medians within 0.986–1.024) confirms that matched controls face comparable target difficulty, ruling out a volatility-mismatch confound.
- The ~4,600 excluded invalid-target events carry useful information: they represent cases where the AVWAP target at trigger time is already beyond the adverse direction, which happens when the A/VWAP band is very narrow or price is very close to the band — this is structural to the first branch's MAD-band construction.

---

## EXP-023 — AVWAP Baseline Candidate Screen

> **SUPERSEDED (framing-corrected) 2026-06-08.** The REFUTED verdict below is valid
> **only as a per-bar continuous-position screen**, not as a tradability test of the
> original selective event vehicle: a ~6%-active signal was scored against a per-bar
> MDE floor calibrated for ≥80%-active series (EXP-005), so the result is dominated
> by ~16× denominator dilution, not absence of signal. Record retained; conclusion
> corrected. Re-screened faithfully under an event-level method in **EXP-028**
> (Phase 006). Review:
> `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.

**Status**: REFUTED → SUPERSEDED (framing-corrected)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: cTrader `Mode=StrategyHost` AVWAP-baseline runs (CF-AVWAP-001/HYP-004 first branch) and aligned Donchian(20) reference on 5m/1h/4h domains, evaluated on emitted real OHLC (`RealClose`); first-70% analysis slice only; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The registered CF-AVWAP-001 baseline signal can qualify under at least one component of the frozen Phase 004 suite — standalone strict, standalone ratified-loose/fallback, or revised portfolio-fitness against the existing D-dogfood-book Donchian(20) reference — while reporting the original AVWAP strategy metric book, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4 × 3 domains = 12 cells).
- **Data Views / Feature Categories**: cTrader strategy-host AVWAP-baseline and Donchian(20) outputs (positions/events/trade blotter/metadata); fixed first-70% source-Parquet smoke output only to validate the C# AVWAP port against the `xen.avwap` Python reference. No chart-type views.
- **Features**: standalone strict gate stack and EXP-012 ratified-loose/strict-fallback referee at α₀=0.05; EXP-018 revised portfolio-fitness unit (`clip(R+C,−1,+1)−R` marginal estimator) vs Donchian(20); original metric book on real `RealClose` (bounce prevalence, executed-entry/non-executed-pyramid counts, favorable/adverse/trend-change/unfinished completions, expectancy, robust mean/MAD and mean/std risk levels, raw-return comparison); same-feed reference identity, holdout-fence, and C#/Python transcription checks.
- **Parameter ranges**: regime MA(20,50) on domain `RealClose`; AVWAP source `(RealHigh+RealLow+RealClose)/3`; weight `TickVolume**0.75`; MAD band ×1.0; frozen suite settings loaded from artifacts — strict MDE 1/4/12, ratified-loose τ 0.375/0.375/1.5 with MDE 0.5/2/8, revised-incremental MDE 12/16/32 bps (5m/1h/4h); α₀=0.05; n_bootstrap=1000.
- **Exclusions**: alternative AVWAP branches/detectors/weights/bands; parameter or domain/instrument tuning after reading outcomes; chart-type variants; unregistered exit overlays, stops, targets, trailing exits, sizing, pyramiding, portfolio weighting, risk management; changes to strict/loose/incremental referee logic or the D-dogfood-book reference; execution-realism claims; the final 30% global holdout.
- **Constraints**: EXP-020 SUPPORTED_FULL (ready {5m,1h,4h}, 0 invariant/holdout violations, deterministic replay), EXP-021/022 SUPPORTED, VAL-002 PASS, EXP-012/018/019 frozen-suite identity — all verified value-based from artifacts; cTrader emits no row at/after `AnalysisEndUtc`; Python ingests/validates only and never regenerates the candidate signal for screening; real `RealClose` return basis; `SourceCloseTime` temporal alignment; zero denominators null/non-reportable.

### Results / Observations

- `run_metadata.json`: `overall_status: REFUTED`, `admitted_cells: 12/12`, `blockers: []`, `smoke_status: [PASS, PASS, PASS]`, `pass_tally: {strict:0, loose:0, incremental:0, suite_pass:0, reportable:12}`.
- `dependency_manifest.csv`: 34/34 PASS. `csharp_avwap_smoke_checks.csv`: 5m/1h/4h PASS, 0 field mismatch, `max_abs_price_diff=0.0`, event counts 5978/421/109 identical (C# vs `xen.avwap`).
- `run_manifest.csv`: all 12 `admitted=true`, `same_feed_ok=true`, `feed_max_abs_diff=0.0`, `n_time_mismatch=0`. `holdout_fence_checks.csv`: candidate and reference max `SourceCloseTime` < `AnalysisEndUtc` in every cell.
- `standalone_suite_verdicts.csv`: 0/12 strict, 0/12 effective-loose. Net effects −1.41 (BTCUSD/4h) to +0.21 bps (EURUSD/4h) vs strict MDE 1/4/12; every `ci_lower` below loose τ (max −0.127, EURUSD/1h).
- `portfolio_fitness_verdicts.csv`: 0/12 `positive_incremental`; all 12 reportable, `n_reference_unaligned=0`, denominators 155–15,951; incremental edges −11.90 (USTEC/4h) to +6.05 bps (XAUUSD/4h), all ≪ floors 12/16/32; small positive 4h points EURUSD/4h +4.39 (ci_lower +0.31) and XAUUSD/4h +6.05 (ci_lower −3.62) below floor.
- `strategy_metric_book.csv`: `successful_bounce_rate` 0.605–0.800; `model_net_bps` ~0-to-negative (BTCUSD/5m −0.740, BTCUSD/4h −1.362; EURUSD/4h +0.081); `lifetime_expectancy_bps` mostly negative (BTCUSD/4h −30.3; EURUSD/4h +8.0); `model_robust_ratio` null in all cells (MAD=0; strategy flat ~92.6% of bars, BTCUSD/5m); model mean/std negative vs small positive raw mean/std.
- `event_trade_diagnostics.csv`: long+short entries reconcile to metric-book `n_entries` per cell (audit cross-check).
- Audit verdict PASS: 0 critical, 0 warnings, 6 info; independent recomputation of BTCUSD/5m metric-book risk metrics matched bit-exact.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**REFUTED**

The predeclared Evidence-AGAINST criteria are met in full: all dependency and run-admission checks passed, all 12 instrument/domain cells are reportable against an aligned same-feed Donchian(20) reference, no suite component (strict, ratified-loose/fallback, or revised portfolio-fitness) passes any cell, and both standalone and incremental effects lie below their frozen domain detection floors in every cell. The baseline CF-AVWAP-001/HYP-004 signal does not qualify under the frozen Phase 004 suite on the first-70% analysis set. This is an admissible negative (not BLOCKED/INCONCLUSIVE) and a baseline-branch result, not a COMPONENT_REFUTED retirement of CF-AVWAP-001 (checkpoint `design.md` §8).

### Hypothesis-Agnostic Observations

- Conditional-event evidence (EXP-021 reaction, EXP-022 lifetime) did not carry through to a tradable, always-on, cost-bearing position judged by a stringent frozen referee — a documented gap between conditional event behavior and continuously-held strategy P&L.
- A 60–80% favorable-target rate co-exists with ~0/negative net expectancy because `successful_bounce_rate` excludes trend-change exits while net expectancy and lifetime returns include them; trend-change exits plus per-active-bar cost erode the edge.
- The robust mean/MAD risk level is structurally undefined for a strategy flat ~93% of the time (MAD=0) — handled per the scope zero-baseline rule as a null, with the mean/std diagnostic used for the model-vs-raw comparison.

---

## EXP-024 — AVWAP Event-Edge Dissipation Decomposition

> **RETAINED, fork leg discounted (2026-06-08).** The fork-(b) leg compared a
> cumulative per-event hold return against a per-bar floor — a category mismatch
> that makes fork (b) near-foreordained and low-information. **Retained findings
> stand:** the edge is relative-not-absolute (raw hold ~0 vs +3.8 bps EXP-021
> control-excess on 5m), and trend-change exits cut losers not winners
> (−2.79/−8.76/−17.59 bps). See the framing-divergence review.

**Status**: MIXED_OR_INCONCLUSIVE (RETAINED; fork leg discounted)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-020 AVWAP bounce events (CF-AVWAP-001 first branch), EXP-021 fixed-horizon reaction observations, EXP-022 lifetime observations, and 5m/1h/4h real OHLC domain bars rebuilt from the first-70% analysis slice; diagnostic only, no frozen suite

### Hypothesis Tests

1. **Diagnostic fork question**: Between EXP-021's positive fixed-horizon bounce reaction and EXP-023's ~0-to-negative always-on strategy expectancy, is the edge lost to fork (a) a fixable holding/exit problem, or fork (b) entry/position dilution that makes the always-on/bounded-hold overlay the wrong vehicle?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars rebuilt from first-70% 1-minute analysis slices; EXP-020 `avwap_events.csv`; EXP-021 `reaction_observations.csv` for matched cross-check; EXP-022 event-role `lifetime_observations.csv` for completed lifetime reference.
- **Features**: direction-signed real-close gross returns over fixed bounded-hold horizons; completed common-set lifetime returns; bounded-vs-lifetime paired contrasts; regime-cluster bootstrap CIs; Holm adjustment across the horizon grid; trend-change return distribution; holding/exposure descriptors; secondary cost attribution.
- **Parameter ranges**: horizon grid `{1,2,3,4,5,6,8,10,12,16,20,24}` completed domain bars; loose floors 0.5/2/8 bps for 5m/1h/4h; margin `max(0.5 bps, 0.25 x floor)`; primary domain 5m; `N_BOOT=10,000`; `DOMAIN_MIN_COMPLETED=100`.
- **Exclusions**: frozen qualification suite; cTrader candidate screen; parameter/exit/detector tuning; global holdout; ALPHA/BAND sensitivity; EXP-025 direct line-S/R question.
- **Constraints**: first-70% analysis slice only; real domain Close returns; no synthetic prices; no percentage improvement over zero baseline; common completed-event denominators for bounded-vs-lifetime contrasts; EXP-020/021/022 substrate consistency required.

### Results / Observations

- `run_metadata.json`: `overall_status=COMPLETE`, `domain_verdicts={5m:FORK_B_DILUTION, 1h:INCONCLUSIVE_UNRESOLVED, 4h:INCONCLUSIVE_UNRESOLVED}`, `phase_verdict=MIXED_OR_INCONCLUSIVE`, `exp021_matched_crosscheck_max_abs_diff_bps=0.0`, event join row counts preserved, duplicate join rows 0.
- `domain_reconstruction_check.csv`: 12/12 EXP-020 metadata checks pass.
- `event_join_diagnostics.csv`: joined event rows 5m 19,242 / 1h 1,360 / 4h 309; completed common-set rows 5m 15,037 / 1h 1,033 / 4h 235; row counts preserved and duplicate join keys 0.
- `exp021_crosscheck.csv`: exact matched-event return reproduction for EXP-021 horizons `{1,3,6}`; matched event counts 5m 16,249, 1h 1,207, 4h 246/246/244; max row and mean absolute difference 0.0 bps.
- `fork_verdict.csv`:
  - 5m: `h*=16`, `g*=+0.370` bps, floor 0.5, CI `[-0.396,+1.164]`, `g_life=+0.058`, `delta=+0.312`, `n=15,037`, verdict `FORK_B_DILUTION`.
  - 1h: `h*=24`, `g*=+4.248` bps, floor 2.0, CI `[-10.190,+18.417]`, `delta=+6.197`, `n=1,033`, verdict `INCONCLUSIVE_UNRESOLVED`.
  - 4h: `h*=8`, `g*=+8.137` bps, floor 8.0, CI `[-22.769,+39.747]`, `delta=+16.840`, `n=233`, verdict `INCONCLUSIVE_UNRESOLVED`.
- `trend_change_returns.csv`: trend-change lifetime means 5m -2.79 bps (`[-3.32,-2.32]`), 1h -8.76 (`[-15.03,-3.24]`), 4h -17.59 (`[-40.38,+3.68]`); negative fractions 65.8%, 56.9%, 54.0%.
- `holding_exposure.csv`: event prevalence 2.68% / 2.26% / 2.21% of domain bars (5m/1h/4h); reconstructed active-bar fractions 6.17% / 5.73% / 5.67%; pyramid bounces 9,679/19,242 (5m), 636/1,360 (1h), 146/309 (4h).
- `cost_attribution.csv`: 5m `g*` gross +0.370 bps becomes -4.651 net; 1h +4.248 becomes -0.597; 4h +8.137 becomes +2.793 after mean round-trip costs.
- Audit verdict PASS: 0 critical, 2 warnings (1h/4h precision; mixed/inconclusive Stage-B handling), 3 info notes.

### Hypothesis-Specific Conclusion

**MIXED_OR_INCONCLUSIVE**

The primary 5m domain resolves to fork (b): bounded-hold gross returns do not reach the loosest suite floor, even before cost. The 1h and 4h domains remain inconclusive because above-floor point estimates have wide CIs that fail the floor-clearance rule. No domain supports fork (a), so EXP-026 `/EXIT` is not automatically justified by EXP-024 alone; any `/EXIT` continuation requires explicit mixed/inconclusive governance handling.

### Hypothesis-Agnostic Observations

- EXP-021's matched event-vs-control reaction and EXP-024's all/completed-event bounded-hold return are different estimands; the corrected cross-check proves the return formula matches on identical rows while showing that the positive matched-control component signal dilutes in the all-event vehicle.
- Trend-change exits are negative on average, which weakens the simple "holding too long gives back winners" explanation for EXP-023's failure.
- Sparse exposure (about 5.7-6.2% active bars) and many pyramid bounces contextualize why conditional event evidence can fail to become a cost-bearing always-on strategy.

---

## EXP-025 — AVWAP Line Support/Resistance Direct Test

> **INCONCLUSIVE — non-informative for HYP-001 (2026-06-08).** The event-bar
> line-rejection metric is structurally confounded: bounce triggers cross AVWAP
> intrabar by definition, inflating adverse penetration and biasing the metric
> negative before any data. It did **not** test HYP-001 (line as S/R), which
> remains untested. Carries zero weight in synthesis. See the framing-divergence
> review.

**Status**: INCONCLUSIVE (non-informative for HYP-001)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% 1-minute analysis slices via EXP-020 conventions; EXP-020 avwap_events.csv event definitions; same-regime non-event controls with line-proximity matching.

### Hypothesis Tests

1. **Hypothesis**: AVWAP bounce trigger bars from the supported CF-AVWAP-001 first branch show a larger event-bar AVWAP line-rejection score than matched same-regime non-event control bars on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% 1-minute analysis slices; EXP-020 AVWAP event and regime tables; causal per-bar AVWAP replay for control matching.
- **Features**: Event-bar line-rejection score (close_rebound_bps - adverse_penetration_bps) with bullish/bearish direction formulas; matched same-regime line-proximate non-event controls (up to 5, min 3); regime-cluster bootstrap CI; stratified paired sign permutation test; Holm adjustment.
- **Parameter ranges**: Domains {5m, 1h, 4h}; max 5 controls, min 3; line-proximity rule abs(close_to_avwap_bps) <= max(1.0, band_spread_bps); 6-bar exclusion around triggers; 10,000 bootstrap/permutation resamples.
- **Exclusions**: frozen-suite candidate qualification, cTrader strategy-host generation, EXP-021 fixed-horizon return continuation, EXP-022 lifetime outcomes, EXP-024 bounded-hold decomposition, threshold sweeps, percentage improvement against zero baseline, final 30% global holdout.
- **Constraints**: dependency gate (EXP-020 SUPPORTED_FULL + EXP-024 documented); domain OHLC rebuilt from exact EXP-020 source files with metadata validation; causal AVWAP replay; event-bar h=0 only; no future returns; event-weighted cell means, equal-weight instrument domain estimator.

### Results / Observations

| Domain | Effect (bps) | CI Low | CI High | n | Holm p | Decision | Balance |
|--------|-------------|--------|---------|---|--------|----------|---------|
| 5m | -4.41 | -4.85 | -4.00 | 10,432 | 1.0 | EVIDENCE_AGAINST | OK (1.99 bps) |
| 1h | -16.94 | -22.12 | -11.77 | 763 | 1.0 | EVIDENCE_AGAINST | Broken (6.58 bps) |
| 4h | -6.77 | -34.13 | +22.80 | 120 | 1.0 | INCONCLUSIVE_SPANS_ZERO | Broken (27.57 bps) |

- All 24 reportable instrument/domain/direction cells show events with lower (more negative) line-rejection scores than matched controls.
- 0 events lost to invalid AVWAP or score; all non-reportable events due to <3 line-proximate controls.
- Domain reconstruction PASS (all 12 cells match EXP-020 metadata exactly).
- Audit: CONDITIONAL PASS (0 critical, 2 warnings: BTCUSD 5m proximity imbalance masked by domain pooling, 4h bootstrap degenerate clusters).

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

No domain meets Evidence FOR (all effects are negative). Evidence AGAINST does not apply because the 4h domain CI spans zero. The 5m domain is the cleanest read (unbroken balance, n=10,432, tight CIs) and shows clear EVIDENCE_AGAINST, but the predeclared criteria require all reportable domains to have CI upper bound ≤ 0 for Evidence AGAINST. The negative effect is structurally consistent: bounce triggers cross AVWAP by definition, so adverse intrabar penetration is inherent to the metric design.

### Hypothesis-Agnostic Observations

- The scoped metric likely conflates the trigger definition with the line-rejection signal: a bounce trigger cannot occur without adverse penetration (the intrabar crossover), so the line-rejection score systematically penalizes events versus non-crossing controls.
- EXP-025 does not invalidate EXP-021/022 positive component evidence (bounce continuation, lifetime outcomes), which test different constructs (regime-gated continuation and completion rather than bar-level line reaction).
- Phase 005 Stage A now completes with all three diagnostics resolved: EXP-023 REFUTED, EXP-024 MIXED_OR_INCONCLUSIVE, EXP-025 INCONCLUSIVE. No diagnostic provides a clean Stage A positive that automatically justifies Stage B.

---

## EXP-027 — Event-Level Evaluation Method: Definition and Sparse-Regime Calibration

**Status**: METHOD_VALID
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 regime intervals as matched-control scaffolding; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: A predeclared event-level evaluation method — with per-event matched-control expectancy as the binding decision statistic (reusing the EXP-021/022 regime-cluster bootstrap + stratified paired sign-permutation + Holm inference and Evidence-FOR rule), and an exposure-aware equity-curve-vs-buy-hold companion — exhibits controlled false-positive error (empirical FPR ≤ α₀ = 0.05 under known-null sparse event processes) and recovery (a finite empirical event-level MDE at TPR ≥ 0.80 while FPR ≤ α₀) across the 5m / 1h / 4h domains, within a sparse activity envelope bracketing the real AVWAP signal ({~3%, ~6%, ~12%} active).

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from first-70% analysis slice. No chart-type views.
- **Features**: Per-event direction-signed log bps matched-control excess; regime-cluster bootstrap CI (1,000 resamples); stratified paired sign-permutation p-value (1,000 flips); Holm adjustment across 3 domains; Evidence-FOR rule (effect > 0 AND CI low > 0 AND Holm p ≤ α); exposure-aware equity-curve vs matched-control baseline companion; two null generators (placebo-on-real, block-permuted-returns); planted-edge additive drift.
- **Parameter ranges**: Activity grid {0.03, 0.06, 0.12}; primary p_trig=0.06; edge grid {0, 1, 2, 4, 8, 16, 32, 64} bps; α grid {0.10, 0.05, 0.01}, primary α₀=0.05; primary horizon H=3 with secondary H=1, 6; MAX_CONTROLS=5, MIN_CONTROLS=3, EXCLUSION_BARS=6; n_draws=500/cell; n_bootstrap=1,000; n_permutation=1,000; TPR target=0.80; FPR half-width max=0.03; TPR half-width max=0.05.
- **Exclusions**: Real AVWAP bounce-event outcomes (anti-overfitting fence — only synthetic signals used); frozen per-bar suite as evaluator; equity-curve companion as a pass-gate; any metric/parameter reselection against Phase 006 outcomes; HYP-001, exit overlays, detector/anchor branches, ALPHA/BAND/XTF/MA-DOMAIN sensitivity; activity outside {3%, 12%} (out-of-envelope); percentage improvement against zero baseline.
- **Constraints**: EXP-020 SUPPORTED_FULL dependency gate; first-70% analysis slice only (final 30% global holdout never loaded); real domain Close outcomes; same-regime control matching; look-ahead-safe placement/matching (timestamp, regime direction, anchor age only); fixed seeds via `seed_for(...)`; deterministic generation with replay check; vectorized control matching equivalence-guarded against EXP-021 reference.

### Results / Observations

- `run_metadata.json`: `overall_status: METHOD_VALID`, `fpr_controlled_primary: true`, `bracket_fpr_ok: true`, `recovered_domains: [5m, 1h, 4h]`, `all_domains_recovered: true`, `determinism_pass: true`, `companion_null_sane: true`, `control_matching_equivalence_pass: true`.

- **FPR summary** (fpr_summary.csv, 54 per-domain cells + 18 family-wise rows):
  - At α₀=0.05, primary p_trig=0.06: 5m placebo 0.016 [0.008, 0.031], 5m block 0.030 [0.018, 0.049]; 1h placebo 0.018 [0.009, 0.034], 1h block 0.034 [0.021, 0.054]; 4h placebo 0.030 [0.018, 0.049], 4h block 0.034 [0.021, 0.054].
  - Max per-domain FPR at any α/p_trig/null: 0.042 (1h, placebo, p_trig=0.03, α=0.10); at α₀=0.05: max 0.038.
  - Family-wise any-domain FPR at α₀=0.05: 0.064 (placebo, p_trig=0.06), 0.094 (block, p_trig=0.06).
  - All 54 cells precision-ok (max Wilson half-width 0.018, well below 0.03 ceiling).
  - No systematic FPR increase at higher activity; 5m/placebo/0.12 gives FPR=0.000.

- **TPR / MDE summary** (tpr_summary.csv, mde_summary.csv):
  - 5m MDE = 1.0 bps (TPR=1.000 [0.992, 1.000], TPR at g=0 = 0.016).
  - 1h MDE = 4.0 bps (TPR=0.818 [0.782, 0.849], TPR at g=2 = 0.302).
  - 4h MDE = 32.0 bps (TPR=0.998 [0.989, 1.000], TPR at g=16 = 0.738).
  - All 9 mde_summary rows recovered=true; all 72 tpr_summary rows precision-ok (max TPR Wilson half-width 0.041, below 0.05 ceiling).
  - TPR at α=0.01: 5m MDE=1.0, 1h MDE=8.0, 4h MDE=32.0 bps.

- **Equity companion** (equity_companion_summary.csv, 24 rows):
  - Null advantage rates: 5m 0.358, 1h 0.522, 4h 0.442 (near chance; no systematic false advantage).
  - Null mean equity advantage negative in all domains: 5m −533 bps, 1h −38 bps, 4h −179 bps.
  - Under planted edge: advantage rate and mean equity advantage monotonically increasing with g; rate reaches 1.000 at g=1 (5m), g=8 (1h), g=32 (4h).
  - Sortino-style risk-adjusted ratio tracks the same monotonic pattern.

- **Determinism**: Byte-identical FPR/TPR on a fixed (5m, p_trig=0.06, placebo_on_real) replay cell.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**METHOD_VALID**

All predeclared Evidence-FOR criteria from scope.md are met: (1) FPR ≤ α₀ = 0.05 in every domain at the primary p_trig=0.06 under both null generators (max per-domain FPR = 0.034 at α₀=0.05; all Wilson upper bounds ≤ 0.054); (2) FPR does not materially exceed α₀ across the {0.03, 0.06, 0.12} bracket (max bracket FPR = 0.038 at α₀=0.05); (3) a finite event-level MDE exists in every domain at p_trig=0.06 (5m: 1 bps, 1h: 4 bps, 4h: 32 bps); (4) determinism replay passes; (5) the equity-curve companion shows no systematic false advantage under null and monotonic edge detection under planted drift. The event-level method is a fit-for-purpose yardstick for the sparse (~6% active) regime. EXP-028 may proceed under this method.

### Hypothesis-Agnostic Observations

- The MDE gradient across domains (5m=1 < 1h=4 < 4h=32 bps) is consistent with the event-count gradient (~20,800 / ~1,750 / ~400 events/draw) — event count, not signal quality, is the binding constraint on power.
- The 5m MDE of 1 bps is driven by very high event count (~20,800/draw), not signal strength; the 1h and 4h MDEs (4 and 32 bps) are more informative for EXP-028 planning because they better approximate the real event count.
- The 4h MDE jump from TPR=0.738 at g=16 to TPR=0.998 at g=32 bps means the true MDE lies between 16 and 32 bps — a finer grid ({16, 20, 24, 28, 32}) would improve resolution.
- The FPR being well below α₀ in many cells (e.g. 0.000 at 5m/0.12 placebo_on_real) reflects conservatism from the Holm adjustment and three-condition Evidence-FOR rule — desirable for a screening yardstick (errs on the side of not declaring false edges), at the cost of slightly reduced power.
- The two null generators agree within tolerance across all cells, making accidental structure in the placebo-on-real generator an implausible explanation for the FPR control.
- The method is calibrated only on synthetic substrates; real-signal performance is unknown until EXP-028 (anti-overfitting fence — by design).

---

## EXP-028 — Faithful Selective AVWAP Strategy Re-Screen

**Status**: EVAL_SUPPORTED
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: Real 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domain bars from first-70% analysis slice; EXP-020 AVWAP bounce events; EXP-022 lifetime completion outcomes; no chart-type views.

### Hypothesis Tests

1. **Hypothesis**: Under the frozen EXP-027 event-level evaluation method, the faithful selective AVWAP strategy — unchanged from the EXP-023 baseline — shows positive event-level edge (per-event matched-control expectancy > 0) on at least one domain (5m, 1h, or 4h), using only the first-70% analysis set and predeclared inference.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: Real 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 AVWAP events; EXP-022 lifetime observations; EXP-021 reaction observations for secondary-stability inputs.
- **Features**: PRIMARY (binding): symmetric own-exit matched-control lifetime excess reusing EXP-022 observations (event and control both completed under band-target/trend-change exit). SECONDARY (non-binding): endogenous-exit vs fixed-window control, gated by predeclared placebo-null calibration. Exposure-matched equity companion. Frozen EXP-027 inference tail: regime-cluster bootstrap CI, stratified paired sign-permutation, Holm across 3 domains.
- **Parameter ranges**: Alpha₀=0.05; N_BOOT=1000; N_PERM=1000; N_PLACEBO_DRAWS=100; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; fixed seeds with determinism replay.
- **Exclusions**: The frozen per-bar qualification suite as evaluation vehicle; asymmetric construction as binding gate; sweep/tuning/metric reselection; exit/detector/anchor branches; HYP-001; percentage improvement against zero baseline; costs/stops/sizing.
- **Constraints**: EXP-020 SUPPORTED_FULL and EXP-027 METHOD_VALID dependency gate; first-70% slice only; CloseTime ordering; real domain Close returns; pyramid bounces included as closer-to-original and absorbed by regime-cluster bootstrap; frozen inference tail hash-guarded against EXP-027 source drift.

### Results / Observations

- `overall_verdict`: EVAL_SUPPORTED. Binding gate PRIMARY symmetric own-exit lifetime excess.
- PRIMARY per-domain:
  - 5m: effect +5.78 bps, CI [5.39, 6.13], Holm p=0.003, n=12,795, EVIDENCE_FOR.
  - 1h: effect +23.38 bps, CI [17.40, 29.32], Holm p=0.003, n=924, EVIDENCE_FOR.
  - 4h: effect +69.02 bps, CI [46.84, 90.52], Holm p=0.003, n=187, EVIDENCE_FOR.
- SECONDARY: 1h calibrated (FPR=0.03), EVIDENCE_FOR; 5m/4h NOT_CALIBRATED as expected.
- Equity companion: all domains advantage_rate=1.0, positive Sortino differences.
- Fixed-horizon secondary-stability: all h1/h6 excesses positive (no secondary horizon instability).
- Audit PASS: 0 critical, 0 warnings, 3 info.
- Pyramid split: 6,785 pyramid / 7,121 non-pyramid (5m/1h/4h combined).
- Dependency gate PASS (EXP-020 SUPPORTED_FULL, EXP-027 METHOD_VALID).
- Frozen inference hash PASS, alignment 12/12 cells, reconciliation 0 bad.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**EVAL_SUPPORTED**

All predeclared Evidence-FOR criteria are met: (1) dependency gate passes; (2) at least one domain (all three) is PRIMARY Evidence-FOR at α₀=0.05 with effect > 0, CI_low > 0, and Holm p ≤ 0.05; (3) secondary-horizon stable (no domain has both h1 and h6 negative). The faithful selective AVWAP strategy shows positive event-level edge on all three domains under the fit-for-purpose, in-envelope EXP-027 method. The EXP-023 negative was a framing/dilution artifact caused by applying a per-bar floor to a ~6%-active event strategy.

> **Caveat (cTrader parity) — RESOLVED 2026-06-09 by EXP-029.** This EVAL_SUPPORTED originally rested on a Python re-analysis of the canonical EXP-020 event substrate, with the faithful strategy not yet executed through its cTrader C# per-bar streaming path. **EXP-029 closed this:** the corrected `AvwapBounceModel.cs` (pyramids opened as independent positions, executed completion serialized) was run on cTrader per-bar streaming and reproduced this PRIMARY excess on all 3 domains (parity CONSISTENT; all 5 binding gates pass, incl. exit-parity match_rate=1.0). EXP-028 is therefore **cTrader-confirmed**. See `checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md` and the EXP-029 entry below.

### Hypothesis-Agnostic Observations

- The effect increases monotonically 5m < 1h < 4h (+5.78 / +23.38 / +69.02 bps), matching the EXP-021/022 domain gradient and reflecting larger absolute moves over longer holds.
- The binding PRIMARY gate uses the symmetric construction that EXP-027 actually calibrated; the asymmetric secondary gate is correctly non-binding where uncalibrated (5m FPR=1.0, 4h FPR=0.26).
- Pyramid bounces (~50% of events) do not drive the result — the regime-cluster bootstrap absorbs within-regime dependence — but including them is faithful to the original concept.
- This is the first fairly-evaluated positive result for CF-AVWAP-001 under a correct yardstick; the next stage is operator review (FAMILY_REVIEW or robustness/protocol testing).
- HYP-001 (AVWAP line S/R) remains untested and open.

---

## EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

**Status**: CONSISTENT (parity confirmed — EXP-028 upgraded to cTrader-confirmed)
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: cTrader `Mode=StrategyHost` per-bar streaming output (`positions.parquet`, `avwap_events.parquet`) from the corrected C# `AvwapBounceModel`, on real 5m (strict), 1h and 4h (`min_coverage=0.90`) domain bars resampled in-engine from the 1-minute cTrader feed, first-70% analysis slice; no chart-type views.

### Hypothesis Tests

1. **Hypothesis**: The corrected C# AVWAP strategy (pyramid bounces opened as independent positions; executed completion serialized) running on cTrader via per-bar streaming produces event-level results consistent with the Python-only EXP-028 re-analysis — per-domain PRIMARY verdicts and effect directions agree and effects fall inside the predeclared parity tolerances — confirming the Python re-analysis faithfully represents the cTrader execution path. Same estimand (symmetric own-exit matched-control excess) and same frozen EXP-027 inference (hash `ea261b9ee0a8aca3`) as EXP-028; first-70% analysis set only.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: cTrader-emitted corrected-model runs (12 cells); PRIMARY estimand rebuilt on the cTrader `RealClose` feed; matched controls rebuilt in Python via imported EXP-021/022 helpers (analysis construct — never a Python signal oracle); regime/anchor/frozen-targets/pyramid tag taken from the C# emission.
- **Features**: PRIMARY (binding): per-event symmetric own-exit matched-control lifetime excess (`event_lifetime_bps − mean(control_lifetime_bps)`, direction-signed log bps on cTrader `RealClose`). Five predeclared binding parity gates: verdict-match, magnitude-equivalence (F02), count ±10% incl. pyramid split (F04), exit-parity grading of the C# completion code (F01), 5m signal-layer reconciliation vs the EXP-020 substrate (F03). Non-binding: fixed-horizon {1,3,6} secondary-stability (cTrader-feed analog, F07); exposure-matched equity companion.
- **Parameter ranges**: α₀=0.05; N_BOOT=1000; N_PERM=1000; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; effect-equiv margin max(2 bps, 25%·|ref|), divergence margin max(2 bps, 50%·|ref|); count tol ±10%/±20%; exit-parity ≥99%; signal-match ≥98% / target rel-diff ≤1e-3; fixed seeds; per-instrument `AnalysisEndUtc` fence (BTCUSD 2025-06-17T22:38Z, EURUSD 2025-05-09T16:55Z, USTEC 2025-05-12T04:54Z, XAUUSD 2025-05-12T03:35Z).
- **Exclusions**: Any change to the frozen EXP-027 inference; strategy parameter tuning / band sweep / exit redesign / sizing / costs; detector/anchor branches (`/LB`,`/MB`,`/ATR`,`/ANCHOR`), `/ALPHA`,`/BAND`, cross-timeframe variants; HYP-001; the frozen per-bar qualification suite as the vehicle (this is an event-level parity check, not a per-bar re-screen); percentage improvement against a zero baseline.
- **Constraints**: EXP-027 METHOD_VALID and EXP-028 results present (dependency gate); frozen-inference hash hard-asserted `== ea261b9ee0a8aca3 ==` EXP-028's; estimand evaluated on the same cTrader feed the C# executed on; holdout fence in-robot (`AssertCanEmit`) + Python re-assertion; cross-feed alignment by `SourceCloseTime`, never bar index; real-price `RealClose` returns only.

### Results / Observations

- `overall_parity_disposition`: **CONSISTENT**; per-domain bands 5m/1h/4h all CONSISTENT; no INCONSISTENT domain.
- PRIMARY per-domain (EXP-029 cTrader vs EXP-028 Python):
  - 5m: +5.79 bps CI [5.37, 6.18] vs +5.78 [5.39, 6.13]; |Δ|=0.007; Holm p=0.003; n=12,784 vs 12,795; both EVIDENCE_FOR.
  - 1h: +23.33 bps CI [17.46, 28.91] vs +23.38 [17.40, 29.32]; |Δ|=0.054; Holm p=0.003; n=927 vs 924; both EVIDENCE_FOR.
  - 4h: +69.02 bps CI [49.32, 90.38] vs +69.02 [46.84, 90.52]; |Δ|=0.000 (bit-identical point estimate, differing CIs); Holm p=0.003; n=187 vs 187; both EVIDENCE_FOR.
- Binding gates (all domains): verdict-match ✔; magnitude-equivalent ✔ (no magnitude-divergent); count ±10% ✔ (total/bull/bear/pyramid within ±0.5%); exit-parity ✔ (`match_rate`=1.0 on 15,027/1,038/236 events; max bps discrepancy 1.8e-11/1.4e-13/0.0); 5m signal-layer ✔ (per-instrument EXP-020 trigger match 0.9990/0.9978/0.9998/1.0, all ≥0.98; matched-target median rel-diff 0.0).
- Pyramid split: 6,254/445/84 (EXP-029) vs 6,258/443/84 (EXP-028).
- Integrity: `frozen_inference_hash`=`ea261b9ee0a8aca3` (== EXP-028, hard-asserted); `control_matching_equivalence_pass`=true; `reconciliation_bad`=0; holdout fence respected (per-cell max `SourceCloseTime` < `AnalysisEndUtc`).
- Equity companion (non-gating): advantage 5m +20,115 / 1h +5,819 / 4h +3,755 bps; advantage_rate 1.0; positive Sortino differences.
- Audit PASS: 0 critical, 0 warnings, 4 info.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**CONSISTENT (parity confirmed).**

All five binding gates hold on all three domains (≥2/3 required) and the 5m signal-layer passes with no INCONSISTENT domain, so under the predeclared disposition rule EXP-028's Python-only EVAL_SUPPORTED is **upgraded to cTrader-confirmed**. The corrected C# strategy executed on cTrader per-bar streaming reproduces EXP-028's per-event excess, verdicts, counts, and pyramid split, with the entry signal (F03), pyramid handling (F04), and executed completion code (F01) all independently graded. The Phase 006 objective is fully satisfied and the EXP-028 omission is closed.

### Hypothesis-Agnostic Observations

- Exit-parity match_rate=1.0 with non-zero residuals (~1e-11/1e-13) shows the C# completion code and the Python `scan_lifetime` are genuinely independent implementations that agree to float precision — a real cross-implementation grade, not a tautology.
- The 4h PRIMARY point estimate is bit-identical to EXP-028 while 5m/1h differ slightly; audit-verified as cTrader 4h feed coinciding with the local feed for the fenced window (separate code paths, differing CIs), consistent with VAL-002's ≤1.83 bps drift being an upper bound, not a guaranteed difference.
- Secondary-horizon {1,3,6} numbers intentionally differ from EXP-028 (F07): computed from the cTrader feed and feeding only the non-binding stability guard; the PRIMARY excess is the sole parity object.
- This is event-level parity, not per-bar-suite tradability: EXP-023's per-bar REFUTED is not overturned, all effects are gross (no costs), and the holdout remains sealed. HYP-001 remains untested and open.
- Process lesson recorded: a "faithful re-screen" must state its execution path (cTrader per-bar vs Python re-analysis) explicitly in scope, and Stage 4 governance must check it against the lineage the faithfulness clause assumes.

