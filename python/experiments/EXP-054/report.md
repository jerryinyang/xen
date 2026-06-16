# Experiment Report: EXP-054 — Intrabar Fill-Model Correction (Benchmark Capture Re-Read vs EXP-049 Worst-Case Tie-Break)

## Status: FILL_MODEL_CHARACTERISED (IMMATERIAL)

**Date:** 2026-06-16
**Instruments:** BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 cells)
**Data Views / Feature Categories:** 5m/15m/30m/1h/2h/4h real domain OHLC; ATR-ZigZag substrate; benchmark 3-barrier geometry (50% favourable, 1:1 adverse, adaptive time-cap); P15 path-ordered intrabar fills vs EXP-049 worst-case tie-break

---

## Question

Does replacing the EXP-049 worst-case same-bar tie-break with the P15 path-ordered intrabar fill model materially change the benchmark capture-rate readout — and if so, does the P15 readout meet P11 viability?

## Hypothesis

Replacing EXP-049's worst-case tie-break with the P15 path-ordered intrabar fill model (bullish O→L→H→C, bearish O→H→L→C) does not materially change the benchmark capture readout — the r~0.50 null across 99 cells is a genuine property of symmetric 1:1 barriers on the unconditioned ZigZag substrate, not a fill-rule artifact.

## Method Summary

Re-read the EXP-049 benchmark across all 99 member cells, resolving every event under **both** the worst-case tie-break and P15 path-ordered fill in a single pass. Per-cell first-hit capture ratio `r`, same-bar double-touch fraction `dt_frac`, and Δr = r_P15 − r_wc are computed for G1 (binding) and G2 (disclosed). Regime-clustered moving-block bootstrap CI (10,000 resamples) applied to `r` under P15 for viability classification. Four mechanical correctness gates: (1) EXP-049 worst-case reconciliation (exact match to stored r and counts), (2) determinism (two-pass frame-identical), (3) monotonicity (Δr ≥ 0, r_P15 ≥ r_wc, FAV_P15 ≥ FAV_wc), (4) tie-reassignment subset bound (reassigned ⊆ tie set). Materiality criterion: P11 composition (≥5 VIABLE cells over ≥3 instruments) or ≥1 TIE_BREAK_SENSITIVE cell (viability flip or Δr ≥ 0.05).

## Key Findings

### Finding 1: Fill-model effect is small and uniform (median Δr ≈ 1%)

The median Δr across all 99 G1 cells is 0.0101 (IQR 0.0051). Every cell shows Δr ≥ 0 by construction. The maximum Δr is 0.0374 (US2000-2h). The fill rule changes capture rates by roughly 1 percentage point on average — a small, bounded effect.

![Per-cell Δr heatmap](plots/delta_r_heatmap.png)

### Finding 2: Same-bar double-touch exposure is structurally low (median ~2%)

Only ~2% of resolved events in a typical cell are same-bar double-touches that the P15 model could reassign (median dt_frac = 0.0212, IQR 0.0112). The maximum dt_frac is 0.0794 (US2000-1h). The fill model's maximum possible effect is structurally bounded by the low tie frequency.

![Double-touch fraction heatmap](plots/dt_frac_heatmap.png)

### Finding 3: Viability composition unchanged — P11 not met under P15

0/99 G1 cells are VIABLE under P15 — identical to the worst-case baseline. P11 composition threshold (≥5 VIABLE cells over ≥3 instruments) is not met. The EXP-049 null stands as a genuine property of the unconditioned, symmetric-barrier, short-horizon benchmark.

### Finding 4: Zero cells are TIE_BREAK_SENSITIVE

No cell had a viability-status flip (NOT_VIABLE → VIABLE) and no cell had Δr ≥ 0.05. The fill-model effect does not approach the pre-declared materiality threshold.

![Paired EXP-049 vs P15 r scatter](plots/r_paired_scatter.png)

### Finding 5: G2 secondary shows isolated VIABLE cell (USDCAD-2h)

Under G2 (retracement geometry), 1 cell (USDCAD-2h) is VIABLE under P15 (r=0.55). This is below the P11 3-instrument threshold and consistent with expected false-positive variation at 5% across 99 cells.

### Finding 6: Median expectancy shift is directionally positive but small

The P15 rule improves median per-event gross ATR-normalised expectancy (G1) relative to worst-case. E_delta_median values range from −0.02 to +0.13 ATR, central mass near +0.03–0.05. Directionally consistent with reassigning ADV→FAV on ties.

![Viability status heatmap with TIE_BREAK_SENSITIVE](plots/viability_status_heatmap.png)

## Conclusion

**FILL_MODEL_CHARACTERISED (IMMATERIAL).** The P15 path-ordered fill model replaces the EXP-049 worst-case tie-break without materially changing any outcome read. 0/99 G1 cells become VIABLE, P11 is not met, 0 cells are TIE_BREAK_SENSITIVE. The median Δr ≈ 1% is bounded by ~2% median tie exposure. The EXP-049 r≈0.50 null is a genuine property of symmetric 1:1 barriers on the unconditioned ZigZag substrate, not a fill-rule artifact.

## Registry Disposition

**Updates applied:**
- `docs/signal-registry/multiplicity-registry.md`: `CF-HA-HARAMI-001/HYP-007 — EXP-054` advanced from PLANNED to FILL_MODEL_CHARACTERISED (IMMATERIAL). 0 candidate slots, 0 TEST reads consumed.
- `docs/signal-registry/candidate-families/harami.md`: HYP-007 row updated with FILL_MODEL_CHARACTERISED (IMMATERIAL).
- No `test-read-ledger.md` entry required (TRAIN-only, 0 TEST reads).

## Limitations

1. **P15 is an approximation.** The path-ordered intrabar fill model (bullish O→L→H→C, bearish O→H→L→C) is a documented approximation of unobserved intrabar motion. For 24/7 instruments (BTCUSD), the session-based microstructure premise has lower fidelity. This does not affect the method-validation conclusion (the experiment quantifies the approximation's effect against the worst-case baseline), but P15's absolute fidelity as a fill model is unvalidated.
2. **Short-horizon cap.** The P4 time cap is unchanged from EXP-049 — ~6 bars in 96/99 cells. Longer horizons may change the tie fraction or P15 effect, but the experiment's purpose is an apples-to-apples re-read of the EXP-049 benchmark, not a new horizon test.
3. **G2 isolated viable cell.** USDCAD-2h is VIABLE under P15 on G2 but represents a single cell out of 99. Consistent with expected false-positive variation; does not affect the G1 binding conclusion.

## Implications for Future Research

- The P15 fill model is adopted as the 014-B fill standard with its ~1% effect bounded and documented. No benchmark re-baseline is warranted.
- Remaining 014-B experiments (EXP-055–060) use P15 fills with confidence that the fill rule does not distort outcomes.
- The EXP-049 unconditional null is confirmed as a genuine substrate property — not a fill-rule defect. This reinforces that the family's edge must come from conditioning (EXP-053) and alternative barrier geometries (EXP-056–058), not from correcting a pessimistic fill assumption.

## Recommended Next Experiments

1. **EXP-055:** Long-horizon availability diagnostic.
2. **EXP-056–058:** Alternative barrier geometries.
3. **EXP-059:** Position-management exits.
4. **EXP-060:** Combined event system.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
