# Results: Experiment EXP-051

Phase 014-A · HYP-004 · `CF-HA-HARAMI-001/STRONG-STAT` & `/STRONG-HA` · Strong-Move Filter Characterisation (ATR-ZigZag, 99 Cells, TRAIN-only).

## Summary

Both `/STRONG-STAT` (p75) and `/STRONG-HA` (primary same-direction) **carve a materially different move population** from the ATR-ZigZag confirmed-move substrate. Every one of the 99 member cells satisfies P10 (`ρ ≥ 1.5` and `f ∈ [0.10, 0.50]`), and both filters clear P11 with 99 material cells across all 17 instruments. The result is uniform across all 6 domains (5m–4h), with narrow IQRs on both ρ and f. The disclosed alternative forms (median+1×MAD, any-direction sensitivity) agree exactly — **0 flips** in materiality status. The experiment verdict is `STRONG_FILTER_CHARACTERISATION_DELIVERED` (determinism PASS, invariants all 0, audit PASS). The materiality readout is a mechanical output; G1 checkpoint adjudication is desk work.

## Detailed Findings

### Finding 1: `/STRONG-STAT` (p75) — 99/99 MATERIAL, full cross-cell consistency

- **Observation**: Every cell meets both P10 legs. ρ ranges from 1.72 (minimum) to 2.19 (maximum), with median 1.92 and IQR [1.86, 1.97]. The retained fraction f ranges from 0.25 to 0.32, with median 0.27 (slightly above the theoretical 0.25 due to ties and the `≥` threshold). **0 cells fail the ρ leg; 0 cells fail the f leg.**
- **Evidence**: `p10_map.csv`, `composition_readout.json` (stat_p75 block). All 99 cells reportable (n_defined range 331–31,431). Cross-domain: 5m=17, 15m=17, 30m=17, 1h=17, 2h=16, 4h=15 material cells. Bootstrap CIs all finite (0 NaN dropped per cell).
- **Interpretation**: The trailing-window p75 reliably selects the top quartile of confirmed-move magnitudes. The median retained move is ~1.9× the unfiltered median — a material size differential that is consistent with a heavy-tailed magnitude distribution where the top 25% of moves are substantially larger than the median. The tight IQR (0.06 on ρ, 0.01 on f) indicates the filter behaves similarly across instruments and domains.

### Finding 2: `/STRONG-HA` (primary same-direction) — 99/99 MATERIAL, slightly more selective

- **Observation**: ρ ranges from 1.62 to 2.08, median 1.80, IQR [1.76, 1.86]. Retained fraction f ranges from 0.15 to 0.24, median 0.20 — more selective than `/STRONG-STAT` (f ≈ 0.27). **0 cells fail either leg.**
- **Evidence**: `p10_map.csv`, `composition_readout.json` (ha_primary block). Same cross-domain pattern: 5m=17, 15m=17, 30m=17, 1h=17, 2h=16, 4h=15. Bootstrap CIs all finite. HA warmup excludes 0 moves (all past the earliest possible HA run completion).
- **Interpretation**: The HA impulse-run detector (3 consecutive qualifying bars within a move span) retains a smaller fraction of moves (~20%) than p75 (~27%), with a slightly lower median-magnitude ratio (~1.80 vs ~1.92). Both legs of P10 are satisfied in every cell. The direction-match constraint (primary) does not prevent materiality — all cells pass under same-direction mapping.

### Finding 3: Disclosed alternative forms agree — zero flips

- **Observation**: **0 cells flip** materiality status between p75 and median+1×MAD; **0 cells flip** between primary and sensitivity HA mappings.
- **Evidence**: `composition_readout.json` cross_form_agreement: `stat_p75_vs_mad_flips = 0`, `ha_primary_vs_sensitivity_flips = 0`. The MAD-form ρ median is 1.80 (lower than p75's 1.92) but still above 1.50 in all cells, with f ≈ 0.32 (still within [0.10, 0.50]). The sensitivity-form ρ median is 1.79 (vs primary 1.80) — nearly identical.
- **Interpretation**: The materiality conclusion is robust within each filter family. The threshold choice (p75 vs median+1×MAD) shifts ρ and f but does not push any cell below the P10 bar. Dropping the direction-match constraint barely changes the retained set (ha_sensitivity f ≈ 0.202 vs ha_primary f ≈ 0.201).

### Finding 4: Cross-domain and cross-instrument consistency

- **Observation**: All 6 domains are fully represented in the material set for both binding filters. The 2h and 4h domains have 16 and 15 cells respectively (vs 17 for shorter domains), reflecting the 3 COVERAGE_EXCLUDED cells (JP225-2h, JP225-4h, US500-4h) that are not member cells. The truncated-DE30 instrument (broker history ends 2026-01-16) shows ρ/f values within the cross-cell range.
- **Evidence**: `composition_readout.json` material_per_domain blocks. Per-cell ρ/f in `p10_map.csv`.
- **Interpretation**: The strong-move filter behaviour is consistent across instrument types (crypto, FX majors, FX crosses, equity indices) and time domains. No instrument or domain is an outlier; the filters carve a materially larger move population regardless of the instrument's volatility regime or data span.

### Finding 5: Diagnostic integrity — invariants, determinism, power

- **Observation**: All invariant counts are 0 (filter well-formedness, magnitude validity, HA self-consistency, causality fence). Determinism: PASS (0 non-deterministic cells). All 99 member cells are reportable (n_defined ≥ 30). Degenerate moves: 0–1 per cell (vanishingly rare). STAT warmup (NO_DECISION): exactly 5 moves per cell (the warmup floor); HA warmup: 0 moves per cell. Bootstrap CIs all finite.
- **Evidence**: `run_metadata.json` determinism result, `excluded_fractions.csv`, `per_cell_strong_move.parquet` invariants.
- **Interpretation**: The characterisation is construction-valid on every cell. There are no power issues (minimum n_defined = 331, far above the 30 floor), no causality violations, and no determinism failures. The negative findings (null reads) in EXP-049 and EXP-050 cannot be attributed to substrate or data quality — this experiment demonstrates the ZigZag move population can be cleanly characterised at scale.

### Finding 6: Harami overlap (disclosed secondary)

- **Observation**: Overlap_A (fraction of retained moves containing ≥1 harami) ranges from 65–87% (`/STRONG-STAT`) and 74–91% (`/STRONG-HA`). Overlap_B (fraction of assigned haramis on a retained move) ranges 24–46% across both filters.
- **Evidence**: `harami_overlap.csv`.
- **Interpretation**: Most retained strong moves contain at least one harami (overlap_A), but most haramis occur on non-retained moves (overlap_B < 50%). This is consistent with the retained fraction being ~20–27% of all defined moves — the harami detector is not strongly specific to strong moves. These numbers inform 014-B combined-event registration: a combined "harami at strong move" event would need to resolve the low overlap_B by conditioning harami detection on the strong-move filter context.

## Hypothesis Verdict

**STRONG_FILTER_CHARACTERISATION_DELIVERED** — the per-cell ρ/f/materiality maps for both binding filter forms, the disclosed alternatives, overlap, excluded-fraction tables, and the P10/P11 composition readout are produced with determinism PASS and no invariant breach. The **substantive readout** is:

- `/STRONG-STAT` (p75): **P11 pass** (99 material cells, 17 instruments). The filter carves a materially larger, selective move population (ρ ≥ 1.5, f ∈ [0.10, 0.50]) across the full 99-cell grid.
- `/STRONG-HA` (primary): **P11 pass** (99 material cells, 17 instruments). The filter also carves a materially larger, selective move population, with a different retained fraction (~20% vs ~27%) and slightly lower ρ (~1.80 vs ~1.92).
- **Both filters are effective at selecting materially larger moves** by the predeclared P10 bar. The composition readout supports both for 014-B combined-event registration.

The experiment does not self-adjudicate G1. The materiality outcome is a mechanical readout; checkpoint desk work determines the 014-A G1 routing.

## Limitations

- **Completed-move magnitude allowance (predeclared)**: `mag_M = |EndPrice_M − StartPrice_M|` uses the terminal pivot, which is future information relative to mid-move bars. This is a descriptive characterisation of completed moves, not a live trading signal. Filter *thresholds* are causal (trailing prior context only); only the magnitude measurement uses the future pivot. This is the same allowance EXP-050 declared and is appropriate for population characterisation.
- **Gross characterisation, no costs**: All measurements are gross. No costs, slippage, or capture geometry are applied. The materiality verdict describes the move population, not net tradability.
- **TRAIN-only**: These results describe the first 49% of each instrument's file-order data. Behaviour on the TEST stratum or the global holdout is not assessed.
- **Benchmark defaults**: The trailing window (20 bars), warmup floor (5), run length (X=3), and p75/MAD thresholds are D0-frozen. Other parameter choices would yield different ρ/f values. Sensitivity to these is a 014-B question.
- **DE30 truncated history**: DE30 broker history ends 2026-01-16 (train_end_ts = 2024-06-28, vs ~2024-08 to 2024-10 for other instruments). DE30 ρ/f values are within the cross-cell range and do not distort composition tallies.
- **Harami overlap is descriptive only**: The overlap fractions describe the co-occurrence of haramis with strong moves. They do not imply a causal or predictive relationship and are not a binding claim.

## Alternative Explanations

- **p75 mechanical selectivity**: The trailing-window p75 typically retains ~25% of moves (modulo ties), which by construction falls inside the [0.10, 0.50] band. The ρ ≥ 1.5 result reflects the heavy right tail of move magnitudes — the median of the top quartile is naturally ~1.9× the full median. The uniform materiality across all 99 cells may partly reflect this mechanical property rather than a special feature of ATR-ZigZag segmentation.
- **HA impulse runs as large-move proxy**: The `/STRONG-HA` detector selects moves containing 3 consecutive strong HA bars. These tend to occur during sustained directional impulses, which naturally have larger price excursions. The lower ρ (~1.80 vs ~1.92) may reflect that HA impulse bars can occur mid-move without the move being in the very top magnitude quartile.
- **No threshold tuning needed**: The result is so consistent (99/99 MATERIAL for both filters) that the P10/P11 bar is crossed easily. This could mean the bar is not discriminating enough (ρ ≥ 1.5 and f ∈ [0.10, 0.50] may be a low threshold on this substrate), or that both filters genuinely carve distinct sub-populations. The point criterion is D0-frozen and no tuning is permitted or needed.

## Recommended Next Steps

1. **G1 desk adjudication (design §10)** — Combine the EXP-051 strong-move filter characterisation with EXP-049 (capture readout), EXP-050 (position-in-move characterisation), and EXP-048 (readiness) for the 014-A phase verdict. The strong-move filters are supported as materially different move selectors per P11; the 014-A gate decision on combined-event registration proceeds to checkpoint desk work.
2. **014-B combined-event registration** — Both `/STRONG-STAT` and `/STRONG-HA` are viable candidates for conditioning harami detection on strong-move context. Key design inputs from this experiment:
   - The filters select ~20–27% of confirmed moves (non-overlapping subsets); the combined "harami at strong move" event density will be overlap_A × f × harami_rate.
   - Overlap_B (24–46%) is a baseline: most haramis occur outside strong moves. A combined-event definition must handle this asymmetry — either by filtering harami detection to strong-move windows or by using the strong-move condition as a post-hoc selector on captured haramis.
   - The narrow cross-cell IQR on ρ and f suggests uniform filter behaviour across instruments/domains, so 014-B parameterisation can be simpler (global defaults, not per-cell tuned).
3. **Alternative strong-move definitions** — The p75 and HA-impulse forms are two specific implementations. Other variants (static magnitude thresholds, volatility-regime-adaptive windows, different run lengths for HA) are scoped as 014-B sensitivity work if the combined-event registration proceeds.
4. **EXP-052 (HYP-005, already scoped)** — Test signal + confirmation combinations directly, building on the strong-move substrate characterised here.
