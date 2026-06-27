# Results: Experiment EXP-054

## Summary

Replacing the worst-case same-bar tie-break with the P15 path-ordered intrabar fill model on the EXP-049 benchmark does not materially change the capture-rate readout. The median `Δr` across 99 cells is ~1.0%, the median tie exposure is ~2.1%, zero cells become VIABLE under P15 on the binding G1 geometry, and zero cells are TIE_BREAK_SENSITIVE. The EXP-049 null (`r ≈ 0.50`, 0/99 VIABLE) is a genuine property of symmetric 1:1 barriers on the unconditioned ZigZag substrate — not an artifact of the pessimistic fill assumption.

## Detailed Findings

### 1. Fill-model effect is small and uniform (G1 binding)

- **Observation**: Median `Δr = r_P15 − r_wc` = 0.0101 (IQR: 0.0051) across all 99 member cells. Every cell shows `Δr ≥ 0` (monotonicity holds by construction). The maximum `Δr` is 0.0374 (US2000-2h). The minimum is 0.0029 (AUDUSD-4h).
- **Evidence**: `composition_readout.json` → `g1_delta_r_median: 0.01005`, `g1_delta_r_iqr: 0.00512`. Per-cell `Δr` is positive and tight in all 99 cells (`fill_compare_map.csv`).
- **Interpretation**: The tie-break choice affects `r` by roughly 1 percentage point on average — a small, bounded effect. The P15 model does not rescue any cell from `BELOW_R` status. The fill-rule was not the cause of the benchmark null.

### 2. Tie exposure is structurally low

- **Observation**: Median same-bar double-touch fraction = 0.0212 (IQR: 0.0112). Only ~2% of resolved events in a typical cell are ties that the P15 model could reassign. The maximum `dt_frac` is 0.0794 (US2000-1h).
- **Evidence**: `composition_readout.json` → `g1_dt_frac_median: 0.02124`, `g1_dt_frac_iqr: 0.01123`.
- **Interpretation**: The fill model's maximum possible effect is structurally bounded by the low frequency of same-bar double-touches. Even if every tie were reassigned from ADV to FAV, the shift in `r` cannot exceed the tie fraction. The observed `dt_frac ≈ 2%` explains why `Δr ≈ 1%` (roughly half of ties reassign, since the P15 path order agrees with the worst-case pick on the other half).

### 3. Viability composition unchanged (P11 not met)

- **Observation**: P15 G1: 0/99 VIABLE, 99/99 BELOW_R. Identical to the worst-case baseline (0/99 VIABLE). P11 composition threshold (≥5 VIABLE cells over ≥3 instruments) is not met.
- **Evidence**: `composition_readout.json` → `g1_p15_composition.n_viable: 0`, `composition_met: false`; `g1_worstcase_composition.n_viable: 0`.
- **Interpretation**: The benchmark does not flip materially under P15. The EXP-049 null stands as a genuine property of the unconditioned, symmetric-barrier, short-horizon benchmark.

### 4. No cell is TIE_BREAK_SENSITIVE

- **Observation**: 0 cells flagged. No cell had a viability-status flip (NOT_VIABLE → VIABLE) and no cell had `Δr ≥ 0.05`.
- **Evidence**: `composition_readout.json` → `n_tie_break_sensitive: 0`, `tie_break_sensitive_cells: []`.
- **Interpretation**: The fill-model effect does not approach the pre-defined TIE_BREAK_SENSITIVE threshold (which is ~5× the median Δr). The effect is well below any materiality concern.

### 5. G2 secondary: isolated VIABLE cell

- **Observation**: G2 (retracement geometry) shows 1 VIABLE cell under P15: USDCAD-2h (`r_P15 = 0.55`, `VIABLE`). This is below the P11 threshold (requires ≥3 instruments).
- **Evidence**: `composition_readout.json` → `g2_p15_composition.n_viable: 1`, `g2_p15_composition.instruments: "USDCAD"`.
- **Interpretation**: An isolated G2 viable cell does not constitute a family-material result. It is consistent with the expected false-positive rate across 99 cells at the 5% significance level (regime-clustered bootstrap CI).

### 6. Median expectancy shift (P14 secondary)

- **Observation**: The P15 fill rule improves median per-event gross ATR-normalised expectancy (G1) relative to the worst-case baseline in most cells. The `e_delta_median` values across cells range from −0.02 to +0.13, with the central mass near +0.03–0.05 ATR.
- **Evidence**: `expectancy_dual_fill.csv` — `e_delta_median` column.
- **Interpretation**: The expectancy shift is directionally positive (as expected — ties can only improve the median by reassigning ADV→FAV) but small in absolute ATR terms. The binding comparison endpoint (`r`) is the correct metric for the method-validation question; the expectancy disclosure confirms the directional consistency.

## Hypothesis Verdict

**HYP-007 — Method-validation hypothesis: SUPPORTED (IMMATERIAL)**

The method-validation hypothesis stated: *Replacing EXP-049's worst-case tie-break with the P15 path-ordered fill model does not materially change the benchmark capture readout.* The data supports this — P15 G1 composition is 0/99 VIABLE, P11 is not met, and no cell is TIE_BREAK_SENSITIVE. The fill-model effect is quantified at ~1% median Δr, bounded by ~2% median tie exposure.

**Deliverable label: FILL_MODEL_CHARACTERISED (IMMATERIAL).** The P15 fill model is adopted as the 014-B fill standard with its effect bounded and documented.

## Limitations

1. **P15 is an approximation.** The path-ordered intrabar fill model (bullish O→L→H→C, bearish O→H→L→C) is a documented approximation of unobserved intrabar motion. For 24/7 instruments (BTCUSD), the session-based microstructure premise has lower fidelity. This does not affect the method-validation conclusion (the experiment quantifies the approximation's effect against the worst-case baseline), but P15's absolute fidelity as a fill model is unvalidated.
2. **Short-horizon cap.** The P4 time cap is unchanged from EXP-049 — ~6 bars in 96/99 cells. Longer horizons may change the tie fraction or P15 effect, but the experiment's purpose is an apples-to-apples re-read of the EXP-049 benchmark, not a new horizon test.
3. **G2 isolated viable cell.** USDCAD-2h is VIABLE under P15 on G2 but represents a single cell out of 99. This is consistent with expected false-positive variation and does not affect the G1 binding conclusion.

## Alternative Explanations

- **The low dt_frac could be a property of the ZigZag substrate.** ZigZag event selection may systematically avoid conditions that produce same-bar double-touches (e.g., large ATR moves that gap through both levels). If so, the fill-model effect would remain small on any symmetric-barrier read of ZigZag-anchored events, even with a more realistic intrabar model. This is consistent with the experiment's conclusion that the benchmark null is a genuine substrate property.

## Recommended Next Steps

No new experiments. EXP-054 fulfils its role as Lead 2 of the 014-B slate. The P15 fill model is adopted for all downstream 014-B experiments (EXP-053, EXP-055–060) with its bounded effect quantified. The routing decision under §8 is for desk adjudication: the benchmark baseline stands as-is (P15 adoption), and no re-baseline is warranted.
