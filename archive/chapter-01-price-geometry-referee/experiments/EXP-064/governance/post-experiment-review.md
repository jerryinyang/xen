# EXP-064 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-064 — MA(20,50)-Substrate Favourable-Target Geometry (Conditioned HA Harami;
`/VPTARGET`, `/MAGTARGET` vs Benchmark 50%; **Dual Conditioning Object: Hybrid and Native**), Phase 015 Surface S1.
**Family / item:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-017`.
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`.
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`,
`docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`,
`docs/experiments-docs/INDEX.md` (live-status update only),
`docs/signal-registry/multiplicity-registry.md`,
`docs/signal-registry/candidate-families/harami.md`.

---

## Audit Review

| Check | Finding |
| --- | --- |
| Audit verdict | **PASS** — 0 Critical, 0 Warning, 3 Info. ✓ |
| Info 1 (rm_m < draw_count) | By-design scope behaviour; conservative bias toward EVIDENCE_AGAINST; verdict robust (max beats_rm = 8 cells, well below P11 quorum of 5/3/3). Not a defect. ✓ |
| Info 2 (matched-count invariant checks draw target) | Correctly documented; pool never depleted (k = draw_count in all 99 cells); no impact on verdict. ✓ |
| Info 3 (per-event VP loop) | Causally required sequential scan; compute dominated by bootstrap; bounded per cell. ✓ |
| Critical / Warning items | None. ✓ |

## Results Review

| Check | Finding |
| --- | --- |
| Verdict consistent with data | EVIDENCE_AGAINST on both objects is directly supported by the per-variant tally: 0 variant_wins composing for any of the 7 alternative variants on either object. Maximum hybrid wins = 3 (VP-FAR), maximum native = 0 — both well below P11 quorum. ✓ |
| VP attribution mechanism | Interpretation correctly identifies that VP targets improve returns but via substrate geometry (RM also benefits), not harami-signal-specific return. Mechanistic explanation is consistent with the data (beats_rm = 2–4/14 viable cells for VP-FAR native). ✓ |
| MAG attribution result | MAG-0.5×20 beats_RM at P11 (8 cells/7 instr/7 non-4h) correctly identified as the sole variant with signal-specific beats_RM. The complementary failure on beats_bench (3 cells only) is correctly explained by shorter-target geometry. ✓ |
| P4 mean diagnostic | Disclosed as non-binding co-primary. Trimmed-mean negative for VP-FAR (−0.029 native, −0.060 hybrid) is correctly interpreted as evidence of thin right-tail optimism rather than stable central tendency. ✓ |
| EXP-056 consistency noted | Correct — 0/8 on ZigZag (EXP-056) + 0/8 on MA (EXP-064) cited without overstating the cross-substrate comparison. ✓ |
| Limitations stated | 5 pre-declared limitations covered: TRAIN-only, TickVolume proxy, LOOKBACK=1, OAT design, hybrid power gap. ✓ |
| No goalpost movement | All interpretation is grounded in predeclared criteria from scope.md and analysis-plan.md. No post-result criteria introduced. ✓ |

## Report Review

| Check | Finding |
| --- | --- |
| Research question and hypothesis stated | ✓ |
| Scope boundaries and exclusions | ✓ |
| Method summary with reference to analysis-plan.md | ✓ |
| Key quantitative results with sample sizes | ✓ — per-variant variant tables (viable, beats_RM, beats_bench, wins) and P4 table. |
| Audit caveats incorporated | ✓ — 3 Info notes acknowledged in audit section; none affect verdict. |
| Conclusion uses approved result category (EVIDENCE_AGAINST) | ✓ |
| Links to code, results, plots, audit, governance | ✓ — full Artifacts table including post-experiment-review. |
| Follow-up recommendations as separate future experiments | ✓ — EXP-065/066/067/068 listed as next. |

## Index Update Review

| Artifact | Check | Finding |
| --- | --- | --- |
| `python/experiments/INDEX.md` | EXP-064 row added with correct status (EVIDENCE_AGAINST), one-line finding, and date 2026-06-18. | ✓ |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | EXP-064 added to ToC; full 5-field card appended; results table and hypothesis-agnostic observations included. | ✓ |
| `docs/experiments-docs/INDEX.md` | Live status updated: Family Indexes EXP range advanced to EXP-048–064 (Phase 014–015); Phase 015 checkpoint status updated to note EXP-064 COMPLETE 2026-06-18. No per-experiment card added to the master. | ✓ |

## Signal-Registry Disposition Review

| Check | Finding |
| --- | --- |
| Disposition recorded in report.md | ✓ — explicit `Registry Disposition` section. |
| HYP-017 outcome in multiplicity-registry.md | ✓ — status updated from PLANNED to CHARACTERISED; result recorded (EVIDENCE_AGAINST both objects); 0 slots, 0 TEST reads confirmed. |
| Candidate-family status in candidate-families/harami.md | ✓ — EXP-064 result added under HYP-017 entry; family status remains REGISTERED / OPEN (no premature closure). |
| Family closure | Correctly NOT applied — P9 (no-early-closure rule) in effect; G-015 adjudicates after the full slate (EXP-065–068 remaining). ✓ |
| TEST-read ledger | No entry required — 0 TEST reads. ✓ |
| Candidate slot | Not consumed — characterisation only; registration deferred to G-015 PROCEED. ✓ |
| Refuted/inconclusive item retention | HYP-017 retained in the ledger (never deleted or renamed). ✓ |

## Core Constraint Verification

| Constraint | Finding |
| --- | --- |
| OOS holdout exclusion | Confirmed in audit — `load_train_1m` reads only F01 TRAIN prefix; TEST and final-30% holdout never read. ✓ |
| Causality / look-ahead safety | Confirmed in audit — VP reference = prior **completed** MA segment; MAG reference = trailing confirmed segments; causality gate asserts all VP span ends ≤ entry. `causality_ok = True` all 99 cells. ✓ |
| Real-price discipline | Detection on HA candles only; all metrics (returns, VP construction, ATR normalisation, bootstrap) on real OHLC. ✓ |
| Dual-object amendment compliance | Both objects reported individually; OBJECTS = ("nat","hyb"); composition_readout has separate native/hybrid blocks; no pooled statistic. Reconciliation roles corrected (native↔EXP-061 M0; hybrid↔EXP-061 H0). ✓ |
| No new countable item introduced | Variants `/VPTARGET` and `/MAGTARGET` were already registered in the Phase 014-B batch; reuse on MA substrate recorded in multiplicity-registry Phase 015 batch. ✓ |
| Determinism | determinism_ok = True; 17/17 instrument first-usable cells replayed byte-identical. ✓ |
| Scope completeness | All 8 binding variants × 2 objects computed; 5/5 plots produced; 99/99 member cells powered; 0 defects. ✓ |

---

```text
VERDICT: APPROVE
```

All post-experiment checks pass: the audit is PASS with no critical or warning items; the interpretation is correctly grounded in predeclared criteria and does not move goalposts; the report is complete with quantitative evidence, audit caveats, and registry disposition; all index updates are applied correctly (no per-experiment card in the master, detailed card in the family index, live status updated); the signal-registry disposition is correctly recorded (HYP-017 measured-negative, family stays OPEN, 0 slots, 0 TEST reads, no deletion). The dual-object amendment is correctly implemented throughout. EXP-064 (Phase 015 S1) is closed; the remaining Phase 015 surface reads are EXP-065 (S2 third-barrier) and EXP-066 (S3 exits).
