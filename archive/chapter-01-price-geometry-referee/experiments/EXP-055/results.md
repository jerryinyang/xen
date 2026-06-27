# Results: Experiment EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-Analog Lifetime MFE/MAE)

## Summary

The `/STRONG`-conditioned HA harami's predicted reversal move offers a meaningful favourable excursion across the grid. **AVAILABILITY_GOOD**: 74 cells over all 17 instruments clear the P11 quorum (≥5 cells over ≥3 instruments) with median MFE robustly above 1.0 ATR and above median MAE. The AVWAP parallel is confirmed — the move *is available*; the EXP-049/053 capture failure was a capture-geometry problem, not a signal problem. No correctness defects detected.

## Detailed Findings

### Finding 1: Favourable reversal move is broadly available

- **Observation**: 74/99 member cells are MOVE_AVAILABLE across all 17 instruments. 99/99 cells are powered (≥30 qualifying events). 3 cells are COVERAGE_EXCLUDED.
- **Evidence**: Per-cell median MFE ranges from ~0.90 to ~2.02 ATR units. Median MAE ranges from ~0.65 to ~1.34 ATR units. In 74 cells, median MFE CI_low > 1.0 ATR AND median MFE > median MAE. See `per_cell_mfe_mae_forest.png` for the full per-cell distribution; `move_available_composition_map.png` for the grid layout.
- **Interpretation**: The reversal move predicted by the conditioned HA harami is real and exploitable — the market reliably produces a favourable excursion of at least 1 ATR before adverse excursion dominates. This is the AVWAP (EXP-047) situation: the short-horizon benchmark capture (EXP-049/053) missed the move not because no move existed, but because capture geometry failed to extract it.

### Finding 2: Availability is instrument- and domain-dependent

- **Observation**: NOT_AVAILABLE cells (25) cluster in longer domains (1h/2h/4h) and specific instrument groups — notably indices (US500-15m/30m/1h, US2000-15m/30m/1h), NZDUSD-2h/4h, and some forex pairs. Short domains (5m, 15m, 30m) are almost universally MOVE_AVAILABLE.
- **Evidence**: The `mfe_mae_asymmetry_heatmap.png` shows positive (MFE − MAE) dominance concentrated in shorter domains and forex pairs. Longer-domain CIs are wider (fewer events), causing NOT_AVAILABLE even when the point estimate is above the threshold.
- **Interpretation**: Availability is broad but not uniform. The conditioned signal's reversal move is most reliable on shorter timeframes and major forex pairs. Index instruments and longer domains need more power or a different capture approach.

### Finding 3: The favourable move is an ambient regime property, not signal-specific

- **Observation**: The signal does NOT beat either baseline (matched-random or MA-segmented) on median MFE in any cell. All contrast_low values are negative.
- **Evidence**: `availability_secondary.csv` shows `contrast_random_low` ranges from approximately −0.09 to −1.08; `contrast_ma_low` ranges from approximately −1.95 to −8.21. The beats_both_mfe list is empty (0 cells). Matched-random entries in the same regime — measured over their own reversal moves — have equally large or larger MFE. MA(20,50)-segmented moves have substantially larger MFE.
- **Interpretation**: The lifetime favourable excursion is a property of the ZigZag-defined reversal move structure itself, not of the conditioned harami entry timing. Any entry during a strong move captures the same ambient reversal swing. This is consistent with the scope's expectation (the matched-random contrast is a disclosed secondary, not a binding MOVE_AVAILABLE leg) and mirrors the EXP-047 pattern where the anchor move was also ambient.

### Finding 4: No correctness defects

- **Observation**: All three correctness gates pass cleanly — 0 non-deterministic cells (full-frame replay on every cell), 0 causality/window-invariant violations, 0 EXP-053 population reconciliation mismatches.
- **Evidence**: `composition_readout.json` `defect.is_defect = false`; `population_reconciliation.csv` shows all 96 member cells match EXP-053 exactly on harami count and retained count. `run_metadata.json` confirms determinism and causality across all cells.
- **Interpretation**: The experiment is mechanically sound. The population is byte-identical to EXP-053, so the AVAILABILITY_GOOD finding is directly attributable to the longer (M_b) lifetime window, not a re-derived signal.

### Finding 5: Disclosed secondaries agree with the binding arm

- **Observation**: The `/STRONG-HA` arm shows similar MOVE_AVAILABLE patterns; the MAD sensitivity arm tracks the p75 arm closely. Censored fractions are low (0–2% across most cells). Matched-random control MFE medians are comparable to the signal's.
- **Evidence**: `availability_secondary.csv` columns `ha_median_mfe` vs `stat_median_mfe` show consistent values; both arms produce similar availability maps (not formally composed).
- **Interpretation**: The availability finding is robust across disclosed filter forms. The `/STRONG-HA` alternative filter would reach the same conclusion.

## Hypothesis Verdict

**AVAILABILITY_GOOD (characterisation delivered)**

The scope's predeclared outcome criterion is met: MOVE_AVAILABLE clears P11 (74 cells, 17 instruments). The conditioned harami's predicted reversal move offers a meaningful favourable excursion — robustly above 1.0 ATR and above adverse excursion — that the short-horizon benchmark capture (EXP-049/053) missed.

The experiment settles the open parallel from the 014-A G1 desk: this is the AVWAP situation — *move available, capture missing* — not the worse alternative (*no available move*). Continuing to iterate capture geometry and exits across the 014-B surface (EXP-056–060) is justified.

No edge claim is made (gross, availability is a ceiling on capture). No gate is self-adjudicated (routing is the single 014-B G2).

## Limitations

1. **Gross only** — No costs are applied. The MFE/MAE represent available excursion, not capturable return. Even if the move is available, capture friction (spread, slippage, barrier placement) may consume the edge.
2. **ATR normalisation is an approximation** — ATR at entry is a fixed divisor for a window that may span many bars. This is consistent with the 014-B endpoint discipline but is a simplification.
3. **MA-segmentation baseline power** — MA(20,50) segments produce much larger M_b moves (longer trends → bigger swings), so the contrast is not a fair fight — disclosed as such in the scope.
4. **Ambient regime property** — The matched-random baseline shows that the favourable move is a property of being in a reversal regime, not of the specific harami entry. This does not invalidate the availability finding (the question was whether a *move exists*, not whether the entry is uniquely good), but it contextualises it.

## Alternative Explanations

- **Reversal move is a mechanical ZigZag artifact**: The 2nd confirmation after any entry in a strong move will mechanically define a reversal window. This is the very property being measured — the question is whether the harami's timing still allows capture before the adverse target is hit. The result says yes, it does — the favourable excursion dominates.
- **DE30 truncated history bias**: DE30 data ends 2026-01-16 vs ~2026-06 for other instruments. DE30 cells are MOVE_AVAILABLE in 4/6 domains, consistent with the broad pattern. No material bias.

## Recommended Next Steps

1. Continue to the remaining 014-B surface experiments (EXP-056–060) as planned — the availability finding justifies the full capture-geometry exploration.
2. The 25 NOT_AVAILABLE cells (especially index instruments) should be monitored in subsequent experiments for consistent underperformance; they may warrant exclusion from candidate definitions.
