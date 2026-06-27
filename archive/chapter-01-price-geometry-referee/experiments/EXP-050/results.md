# Results: Experiment EXP-050

Phase 014-A Harami-in-Context: Position-in-Move of HA Harami Signals vs Predeclared Baselines (ATR-ZigZag, 99 Cells). TRAIN-only, gross, descriptive. 0 candidate slots, 0 TEST reads.

## Summary

The raw unfiltered HA harami signal is **systematically front-loaded** in ZigZag moves. Across all 99 cells, harami positions fall reliably in the first half of moves (median pos ≈ 0.45–0.52), well below the "near-exhaustion" threshold of 0.67. The per-cell final-third rate FT (≈ 0.21–0.31) is substantially lower than the direction-matched random-timing baseline FT_rand (≈ 0.33–0.43), producing uniformly negative deltas of −0.12 to −0.18. **0/99 cells are CLUSTERED** by the P9 materiality rule. The P11 composition rule is not met. The experiment verdict is CONTEXT_CHARACTERISATION_DELIVERED — the per-cell characterization is complete and clean regardless of the negative clustering outcome.

## Detailed Findings

### Finding 1: Haramis are front-loaded, not exhaustion-clustered

- **Observation**: Every cell has delta < 0. The weakest (least negative) is US2000-2h at Δ = −0.116; the strongest is NZDUSD-4h at Δ = −0.176. No cell approaches the +0.10 materiality threshold, or even Δ > 0.
- **Evidence**: `final_third_rate_map.csv` (99 member cells, all reportable). FT range [0.210, 0.312], FT_rand range [0.334, 0.432]. Harami median position 0.43–0.52 (first half of moves).
- **Interpretation**: Raw harami signals fire early in ZigZag moves, not near exhaustion. This is uniform across all 17 instruments and 6 domains — not a power issue (median n_assigned ≈ 2,500, min 393). The harami-in-context thesis requires selection to reverse this front-loading.

### Finding 2: The front-loading is a ZigZag segmentation phenomenon

- **Observation**: Under the MA(20,50) alternative segmentation, delta_ma_vs_rand clusters around zero (range [−0.041, +0.010]; 3/99 cells barely positive). Haramis are essentially uniformly distributed within MA regimes.
- **Evidence**: `secondary_disclosure.csv`. delta_ma_vs_rand is −0.01 to −0.04 for most cells, versus delta of −0.12 to −0.18 under ZigZag.
- **Interpretation**: Haramis are not systematically early or late in a directional regime — they fire uniformly across MA-defined moves. The ZigZag-specific front-loading arises because ZigZag confirms a move's start at a pivot extreme and the harami (a small consolidation pattern) tends to appear soon after that extreme, before the move has traveled most of its price range.

### Finding 3: Duration-based position confirms the pattern

- **Observation**: delta_dur is also uniformly negative [−0.16, −0.10]. The front-loading is not a price-excursion artifact.
- **Evidence**: `secondary_disclosure.csv`.
- **Interpretation**: Even on bar-count time within the move, haramis appear earlier than random timing. The pattern is robust to the position metric.

### Finding 4: No power or construction issues

- **Observation**: All 99 member cells are reportable (n_assigned ≥ 30), all pass the invariant battery, all are deterministic. Exclusion rates are negligible (warmup ≤ 1.5%, forming-tail ≤ 0.5%, degenerate = 0%).
- **Evidence**: `per_cell_context.parquet` invariants all 0, determinism_ok all True. `secondary_disclosure.csv` exclusion fractions.
- **Interpretation**: The negative result cannot be attributed to underpowered cells, construction defects, or data quality issues. It is a genuine property of the raw HA harami signal on this ZigZag substrate.

### Finding 5: Composition not met at any threshold

- **Observation**: 0 CLUSTERED cells at Δ ≥ 0.10. Even at relaxed thresholds (Δ ≥ 0.05, Δ ≥ 0.15) and relaxed composition rules (4 cells/2 instruments, 3 cells/2 instruments), no combination qualifies.
- **Evidence**: `composition_readout.json` — all support tiers and sensitivity checks return 0 cells / composition_met = false.
- **Interpretation**: This is not a borderline miss — the signal is decisively not near exhaustion by any reasonable threshold.

## Hypothesis Verdict

**CONTEXT_CHARACTERISATION_DELIVERED** — per-cell measurements produced successfully. The substantive readout for HYP-003 is: the raw HA harami signal does not cluster near exhaustion on the ZigZag substrate. Harami timing is systematically front-loaded relative to random in-move timing. This is a valid, clean negative finding.

## Limitations

- **Look-ahead carve-out**: Position-in-move uses the terminal pivot, not knowable at signal time. The metric describes completed moves in hindsight. This is appropriate for characterization but does not directly translate to a live trading rule.
- **No filter applied**: The raw signal pools all haramis (no `/BARCFG`, no strong-move filter, no confirmation). EXP-050 is a baseline — it does not test whether a selected subset can cluster near exhaustion.
- **ZigZag-specific front-loading**: The MA (P13.2) secondary shows uniform distribution, meaning the front-loading is a property of the ZigZag segmentation rather than harami timing against trend direction per se. Whether this matters depends on which segmentation 014-B uses.

## Alternative Explanations

- **Harami as early-move phenomenon**: A harami is a small real body inside a larger prior body. In a fresh ZigZag move, the first pullback/consolidation naturally takes this form. The signal may be detecting "pause after pivot" rather than "exhaustion before reversal."
- **ZigZag asymmetry**: ZigZag pivots at trend-change points; the harami detector fires at the first HA consolidation after that pivot. By construction, this is early in the move's price range. The MA regime segmentation, which starts a regime when the crossover occurs (not at an extreme), does not have this property — hence the uniform MA distribution.

## Recommended Next Steps

1. **EXP-051** (HYP-004, already scoped): Test whether `/STRONG-STAT` and `/STRONG-HA` filters shift the position distribution rightward. If strong-move filters select haramis that cluster nearer exhaustion, the raw front-loading is survivable.
2. **EXP-052** (HYP-005, already scoped): Test signal + confirmation combinations directly.
3. **014-B design implication**: The raw signal's anti-exhaustion bias means any combined event definition must rely on the capture barrier system (EXP-049/014-B) to manage outcome — not on the harami's position-in-move as a timing filter.
