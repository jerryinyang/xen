# Results: Experiment EXP-065

## Summary

On the MA(20,50) substrate, extending the third-barrier holding horizon beyond the benchmark floor-6 adaptive cap — via `/THIRD-TIME` floors {12,24,48} or `/THIRD-EVENT` (next-MA-segment-reversal confirm, 8× backstop) — does **not** improve gross per-event median expectancy for either conditioning object. The native object is **EVIDENCE_AGAINST** (0/4 alternative variants compose at P11 for the combined `median_viable ∧ beats_rm ∧ beats_bench` criterion), and the hybrid object is **INCONCLUSIVE_POWER_LIMITED** (< P11 powered cells). The third barrier is not a leveraged parameter on MA(20,50), replicating the EXP-058 (ZigZag substrate) finding: horizon extension does not improve conditioned harami capture on either substrate.

## Detailed Findings

### Finding 1: Native object — EVIDENCE_AGAINST

- **Observation**: The native conditioned harami population (8360-class, MA-segment `/STRONG-STAT`) is well-powered across all 5 variants: 8–9 cells reach m ≥ 30 (6 instruments, all outside 4h). All 4 alternative variants are `median_viable` and `beats_rm` at P11. However, **none** beats the benchmark (`variant − BENCH` paired median CI_low > 0) at P11.
- **Evidence** (per `composition_readout.json`, native section):

  | Variant | Median-viable cells | Beats-RM cells | Beats-bench cells | Wins cells | Wins composes P11? |
  |---------|--------------------|----------------|-------------------|------------|-------------------|
  | T12     | 8 (6 instr, 8 ∅4h) | 8 (6, 8)       | 0                 | 0          | NO                |
  | T24     | 8 (6, 8)           | 9 (6, 8)       | 0                 | 0          | NO                |
  | T48     | 9 (6, 8)           | 9 (6, 8)       | 3 (2, 2)          | 1 (1, 0)  | NO                |
  | EVENT   | 6 (6, 4)           | 6 (6, 4)       | 3 (3, 2)          | 2 (2, 1)  | NO                |

- **Interpretation**: The 8–9 core cells where the MA-substrate harami expresses a positive median signal (`median_viable` and `beats_rm` are the same cells as EXP-061 M0) are unaffected by horizon extension. The pairwise `variant − benchmark` contrast (same object, same entry, same fav/adv geometry, only the third-barrier window differs) shows CI_low_1s crossing zero in the vast majority of cells — longer holding neither adds nor subtracts from the benchmark median expectancy.

  The `variant_wins` map (see `plots/p11_wins_map.png`) shows isolated wins at EURUSD-4h (T48, EVENT) and GBPUSD-1h + US2000-4h (EVENT), but these are individual cells, not P11-composed. The EURUSD-4h T48 win is `low_n_4h = true` (m < 60 on 4h), further reducing confidence.

- **Consistency**: This replicates EXP-058 on ZigZag (also EVIDENCE_AGAINST for third-barrier geometry), now confirmed on both substrates.

### Finding 2: Hybrid object — INCONCLUSIVE_POWER_LIMITED

- **Observation**: The hybrid conditioned harami population (3202-class, ZigZag `/STRONG-STAT` mask through MA geometry) is power-limited. Only 3–4 cells reach m ≥ 30 across the 5 variants (all < P11 quorum). No variant composes at P11 for any flag (`median_viable`, `beats_rm`, or the combined `variant_wins`).

- **Evidence** (per `composition_readout.json`, hybrid section):

  | Variant | Powered cells | Median-viable (P11?) | Beats-RM (P11?) | Beats-bench (P11?) |
  |---------|--------------|---------------------|-----------------|-------------------|
  | BENCH   | 3 (2 instr, 3 ∅4h) | 3 — NO | 2 — NO | 0 — NO |
  | T12     | 3 (2, 3)           | 3 — NO | 3 — NO | 0 — NO |
  | T24     | 3 (2, 3)           | 3 — NO | 5 (5 instr, 3 ∅4h) — YES (fragile) | 0 — NO |
  | T48     | 4 (3, 4)           | 4 — NO | 3 — NO | 2 — NO |
  | EVENT   | 1 (1, 1)           | 1 — NO | 6 (5, 5) — YES | 0 — NO |

- **Interpretation**: The hybrid object's condition count (~3200 haramis vs ~8360 for native) already limits power at the BENCH geometry (EXP-061 H0 had only 3 powered cells). Third-barrier horizon extension further depletes events through TIMECAP exits, leaving even fewer qualifying events per cell. The `beats_rm` composition for T24 (5 cells, fragile) and EVENT (6 cells) is notable — the matched-random null may be even more power-depleted than the signal variant — but without `median_viable` and `beats_bench` composing, this is not a signal claim. The hybrid third-barrier question simply lacks the event count to be answered on the TRAIN slice.

- **Consistency**: The power limitation is expected and was predeclared in scope/plan: "the hybrid 3202-class object is expected more power-limited than native 8360-class."

### Finding 3: Censoring cost is bounded, and `/THIRD-EVENT` is event-limited

- **Observation**: The censoring fraction (`DATA_CENSORED / built window`) stays low across all variants and objects. Mean TIMECAP fraction increases with horizon but remains modest.

- **Evidence** (from `plots/censoring_timecap_composition.png` and `secondary_map.csv`):

  | Object | BENCH | T12 | T24 | T48 | EVENT |
  |--------|-------|-----|-----|-----|-------|
  | Native censored frac | ~0.000–0.026 | ~0.000–0.026 | ~0.000–0.026 | ~0.000–0.026 | ~0.000–0.026 |
  | Native TIMECAP frac | ~0.12–0.33 | ~0.12–0.33 | ~0.12–0.33 | ~0.12–0.26 | ~0.12–0.34 |

  TIMECAP fraction for the longest variants (T48, EVENT) is not dramatically higher than for BENCH — the benchmark adaptive cap (floor=6) already captures most of the available MA-segment lifetime, and extending the floor only captures a modest additional move share.

  The `/THIRD-EVENT` `event_bound_frac` is **1.0** for every cell and both objects — meaning **every** TIMECAP exit under `/THIRD-EVENT` bounded on an actual follow-through MA rd-confirm, not the 8× backstop. The backstop never binds in this data.

- **Interpretation**: Horizon extension does not create a meaningful censoring penalty on the MA substrate (unlike on ZigZag, where segment lengths are shorter and censoring was a concern). The TIMECAP exits are on genuine MA-segment reversals, not arbitrary backstops. The limiting factor is not censoring but lack of expectancy improvement — the benchmark cap already captures the available move.

### Finding 4: P4 mean diagnostic reveals positive-skewed cells where median is near zero

- **Observation**: Across both objects, `mean_viable` cells consistently outnumber `median_viable` cells. The gap between mean and median (`gap_median_minus_mean` in `per_cell_expectancy.parquet`) is typically negative — the mean is pulled positive relative to the median.
- **Evidence**: Native BENCH: 10 mean-viable cells vs 8 median-viable. Some cells have median near zero but a clearly positive mean (e.g., EURUSD-4h native BENCH: median=2.07, mean=1.07 — both positive; US2000-5m native BENCH: median=0.0, mean=0.24). The tail-share (worst-5%) is stable around 0.24–0.32, indicating the negative tail is not extreme.
- **Interpretation**: The return distribution on the MA substrate is positively skewed at the per-cell level: the typical event returns a small positive amount, but the median (binding endpoint) hovers near zero for many cells. The trimmed mean lags the raw mean slightly but tracks it, suggesting the positive skew is spread rather than single-outlier-driven. This is consistent with EXP-060B/061's finding of a narrow median edge that is real but fragile.

### Finding 5: Full structural validation passed

- **Reconciliation**: 99/99 cells — native BENCH reproduces EXP-061 M0, hybrid BENCH reproduces EXP-061 H0, to full floating-point precision.
- **Determinism**: 17 cells replayed byte-identically (one per instrument), 0 failures.
- **Causality**: all 99 cells pass.
- **Invariants**: all 7 per-object invariant gates pass for all cells (exit weights, matched-count, BENCH cap identity, cap monotonicity, event bounds, warmup identity, fav_dist positivity).
- No defect was found. The numerical pipeline is trustworthy.

## Hypothesis Verdict

**REFUTED (native) — The hypothesis is rejected for the native conditioning object on MA(20,50). No alternative third-barrier geometry improves median expectancy over the benchmark floor-6 adaptive cap at P11.**

The hybrid object is **INCONCLUSIVE** due to power constraints — the question cannot be answered on the TRAIN slice with the 3202-class population.

The phase-level reading is **EVIDENCE_AGAINST (native stronger)**, consistent with the full surface protocol: the third barrier is not a leverage parameter on MA(20,50), matching the EXP-058 result on ZigZag.

## Limitations

- **TRAIN-only**: Results are confined to the first 49% of the data (file-order chronological prefix). The TEST slice and the global 30% holdout remain sealed. Generalisation beyond the TRAIN window is not tested.
- **Power-limited hybrid**: The hybrid object (3202-class, third-barrier pipeline) lacks the event count to distinguish signal from noise on the TRAIN slice. A null result for the hybrid question is not informative — the experiment cannot determine whether horizon extension would help the hybrid object with more data.
- **MA(20,50) fixed**: Only one MA period pair is tested. Longer/shorter MA pairs might produce different segment-duration profiles and thus different third-barrier behaviour.
- **Gross returns only**: No costs, slippage, or spread are modelled. The narrow positive median expectancy in the 8 core cells would likely be eroded by transaction costs (though the third-barrier question is answered in the negative regardless).
- **P15 fill approximation**: The P15 fill model is a documented approximation of unobserved intrabar motion (EXP-054 bounds the error). The third-barrier windows are long enough that P15 fills are a small fraction of the total return, mitigating this concern.

## Alternative Explanations

- **The benchmark cap is already optimal**: The floor-6 MA adaptive cap may already capture the full available MA-segment move. MA segments on the TRAIN slice have a natural duration distribution that the benchmark cap (k=1.5, floor=6) already spans; longer windows add TIMECAP exits at later bars where prices have reverted toward the entry level, adding no expectancy gain.
- **Signal attribution is the binding constraint**: The `beats_rm` signal-attribution gate is harder for longer-horizon variants because the matched-random control also benefits from a longer drift window (the MA substrate provides favourable directional drift per segment). The variant — RM contrast measures harami-specific edge above drift, and longer windows may dilute the harami-specific contribution.
- **Substrate convergence**: The MA(20,50) third-barrier result replicates the ZigZag (EXP-058) result exactly — no variant composes at P11. The third barrier may be a generally powerless lever for 3-barrier capture frameworks on any substrate.

## Recommended Next Steps

1. **Proceed with Phase 015 surface S3 (position-management exits, EXP-066) as scheduled** — the third-barrier lever is now characterised as EVIDENCE_AGAINST on both substrates. The family stays OPEN (P9); S3 runs regardless.
2. **No third-barrier follow-up on MA**: Unlike EXP-060B (which found a real MA-substrate lead and triggered a follow-up phase), EXP-065 found a clear negative on the expressing (native) object. The third-barrier lever on MA is closed for Phase 015.
3. **Document for G-015 input**: The native object's third-barrier result feeds EXP-068 (native combined champion) — the winning variants' metrics accompany the benchmark BENCH as a documented non-contributor. The hybrid object's power-limited result feeds EXP-067 (hybrid combined champion) with the same documentation.
