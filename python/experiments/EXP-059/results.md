# Results: Experiment EXP-059

**Title:** Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)

**Phase:** 014-B (Surface read 4, HYP-012)

---

## Summary

All four `/EXIT-PARTIAL` schemes produce higher gross median per-event expectancy than the single-leg benchmark exit, clearing P11 with 25–53 wins across 14–17 instruments. The strongest is **PARTIAL-V2A** (33/66/100% fraction-of-target splits): 53 wins over benchmark (all 17 instruments, 57 viable cells). In contrast, all three structure trailing-stop arms (`/EXIT-TRAIL-STRUCT`) and all four combined arms produce **zero viable cells** — uniformly detrimental within the benchmark adaptive cap (6-bar floor in 96/99 cells). The verdict is **EVIDENCE_FOR**: favourable-side scaled partial exits improve conditioned gross capture on benchmark barrier geometry. The adverse-side structure trailing is not a lever within this horizon; its interaction with longer horizons is deferred to EXP-060.

---

## Detailed Findings

### 1. All four PARTIAL arms clear P11 — partial exits materially improve conditioned expectancy

| Arm | Powered | Viable | Wins (cells) | Wins (instruments) | Wins passes P11 |
|-----|---------|--------|-------------|-------------------|-----------------|
| PARTIAL-V1 | 99 | 40 | 25 | 14 | YES |
| PARTIAL-V2A | 99 | 57 | 53 | 17 | YES |
| PARTIAL-V2B | 99 | 33 | 27 | 14 | YES |
| PARTIAL-V2C | 99 | 56 | 45 | 17 | YES |
| BENCH | 99 | 9 | 0 | 0 | — |

- **Observation:** Every PARTIAL arm beats the single-leg benchmark exit across a broad cross-section of the grid. All pass P11 (≥5 cells, ≥3 instruments). The exit-reason composition plot (`exit_reason_composition.png`) shows that partial-leg favourable triggers capture profit before the benchmark 50% level or the time cap binds — the mechanism hypothesis is confirmed.
- **Evidence:** `composition_readout.json` per-arm win counts; `per_arm_median_forest.png` shows PARTIAL arm medians sit above BENCH in the large majority of cells; `arm_benchmark_contrast_heatmap.png` shows widespread positive contrast.
- **Interpretation:** Scaling out at intermediate favourable levels (`1/3`, `2/3`, `1/2`, `1.0` × `fav_dist`) banks profit before reversal or time-cap expiry, capturing more of the available conditioned move than waiting for a single 50% target. This is consistent with the mean-reverting / cap-bound environment (96/99 cells at 6-bar floor) where partial exits are expected to outperform.

### 2. PARTIAL-V2A (even thirds: 33/66/100% of fav_dist) is the strongest partial-exit scheme

- **53 wins** across 57 viable cells — the broadest adoption of any arm. Wins on all 17 instruments.
- PARTIAL-V2C (33/66% + reversal-event runner) is next at 45 wins (17 instruments).
- PARTIAL-V2B (50/100/150% runner) is weakest among PARTIAL arms at 27 wins (14 instruments) — the 1.5× runner leg rarely fills within the 6-bar cap (`ew_TIMECAP` ≈ 48.5% for BTCUSD-5m V2B per audit spot-check).
- PARTIAL-V1 (first-profitable-close + 50% target + reversal-event) achieves 25 wins (14 instruments) — selective but still P11-clearing.
- **Evidence:** `p11_wins_composition.png` arms × instruments map; `composition_readout.json` per-arm wins; `arm_benchmark_contrast_heatmap.png` density.
- **Interpretation:** Evenly-spaced fractional targets (V2A) provide the most consistent value because they diversify the exit across price-space within the short cap window. The reversal-event runner (V1, V2C) adds selective value above the 1.5× fixed runner (V2B), which is ceilinged by the cap.

### 3. Structure trailing stop is uniformly detrimental within the benchmark horizon

| Arm | Powered | Viable | Wins | P11 |
|-----|---------|--------|------|-----|
| TRAIL-PURE | 99 | 0 | 0 | NO |
| TRAIL-TP-INIT | 99 | 0 | 0 | NO |
| TRAIL-TP-NOINIT | 99 | 0 | 0 | NO |
| COMBINED-V1/V2A/V2B/V2C | 99 each | 0 | 0 | NO |

- **Observation:** All 7 arms with a structure trailing stop produce **zero viable cells** — 100% `CI_SPANS_0` across the entire 99-cell grid. This is not a power problem (all 99 cells powered); it is a genuine measurement within the scoped limitation.
- **Evidence:** `composition_readout.json` TRAIL/COMBINED entries; `return_distribution_by_arm.png` shows TRAIL/COMBINED pooled distribution shifted left of zero; `exit_reason_composition.png` shows the trailing stop binds more often than it lets favourable exits run.
- **Interpretation:** The secondary `atr_mult=0.5` ZigZag retracement fires frequently within the 6-bar cap window, tightening the stop before the position reaches its favourable target. The trailing stop's potential requires *room to run* — a longer horizon than the benchmark cap provides. This is the disclosed clean-OAT measurement: **"trailing does not help within ~6 bars"** (not "trailing never helps"). The horizon × position-management interaction is EXP-060.

### 4. Combined arms (partial fav + trail adverse) destroy partial-exit advantage

- All 4 COMBINED arms: 0 viable, 0 wins — compared to 25–53 wins for standalone PARTIAL arms.
- Replacing the fixed 1:1 stop with the structure trailing stop on partial-leg arms causes the trail to bind before the partial legs can realise their favourable exits.
- **Evidence:** `arm_benchmark_contrast_heatmap.png` shows uniformly negative contrast for COMBINED arms; `exit_reason_composition.png` shows the trailing stop dominates the exit-reason fraction.
- **Interpretation:** Within the benchmark ~6-bar window, the trailing adverse is strictly harmful on partial-leg positions. The 1:1 fixed stop is the superior adverse-side treatment at this horizon.

### 5. BENCH reproduces EXP-053 exactly

- All 99 cells: `m_match=true`, `median_match=true`, `r_match=true` — byte-identical per-cell median expectancy, qualifying count, and first-hit `r`.
- 0 defects, 0 invariant violations, 0 causality violations across all 12 arms.
- Determinism verified on all 17 instruments (byte-identical replay).
- **Evidence:** `composition_readout.json` defect block; `run_metadata.json` reconciliation tables.
- **Interpretation:** The experiment infrastructure and conditioned population are sound. The EVIDENCE_FOR reading is built on a verified foundation.

---

## Hypothesis Verdict

**EVIDENCE_FOR** — At least one position-management exit scheme (`/EXIT-PARTIAL`) clears P11 on its own median expectancy and beats the benchmark on the paired contrast within the quorum.

**Condition:** The EVIDENCE_FOR label applies to the `/EXIT-PARTIAL` branch (favourable-side scaled exits). The `/EXIT-TRAIL-STRUCT` branch (adverse-side structure trailing) does not improve capture within the benchmark horizon — a measured-negative characterization that is a valid input to G2.

---

## Limitations

1. **Benchmark cap bounds the runner/reversal legs.** The P4 adaptive cap collapsed to the 6-bar floor in 96/99 cells, limiting the reversal-event legs (V1, V2C), the V2B 1.5× runner, and all TRAIL arms to ~6 bars. The measurement is clean-OAT (does position-management help *within the benchmark horizon*?), but the horizon × position-management interaction is deferred to EXP-060. A flat result on TRAIL arms should not be misread as "trailing never helps."

2. **`ATR_MULT_TRAIL = 0.5` is frozen.** The trailing structure sensitivity to the ZigZag ATR multiplier is not tested here; a coarser trail might behave differently.

3. **Gross only; no costs.** Partial exits incur more trades (3 fills per event vs 1), which would increase cost drag at a future tradability screen. The gross median advantage must be large enough to absorb this.

4. **Moving-block bootstrap caveats.** Approximate within-cell stationarity is assumed; block lengths (4–15 per cell) absorb short-range dependence. No stronger statistical claim is made.

5. **P15 fill approximation.** Intrabar motion is modelled by the P15 path order; 1-minute base bars are not replayed. EXP-054 bounds this error.

6. **DE30 truncated broker history** (2026-01-16). Its counts derive from its own realised timeline and are not span-comparable with other instruments.

---

## Alternative Explanations

1. **Partial exits may capture mean reversion, not sustained trend.** In a 6-bar cap window, the conditioned move may peak early and reverse. Partial exits bank at intermediate levels; the benchmark single exit waits for 50% and often reverts before filling. The result may be largely driven by the cap window being too short for the single exit to express its design. EXP-060 (combined with better third barriers) will disambiguate.

2. **The trailing ZigZag may be too tight at 0.5×ATR.** A `atr_mult=0.5` secondary ZigZag retracement in a short window fires on noise-level pullbacks. A coarser threshold (e.g., `atr_mult=1.0`) or a different trailing construction (e.g., volatility-based) might behave differently. This is a registered but untested sensitivity.

3. **The 3-leg equal-weight structure is arbitrary.** The leg count and equal weighting are a fixed governance constant. A different weighting (e.g., 50/30/20 or increasing size on runner legs) could produce a different readout. The predeclared sweep covers three fraction grids for the "3 equal legs" design point.

---

## Recommended Next Steps

1. **EXP-060 (combined event system):** Pair the best partial-exit scheme (V2A) with the best EXP-058 third barrier (`/THIRD-TIME` or `/THIRD-EVENT`) to test whether a longer horizon allows the partial-exit advantage to compound and whether the trailing stop becomes viable with more room to run.

2. **`ATR_MULT_TRAIL` sensitivity sweep (registered `/THIRD-TIME`-analog grid):** Test the trail at coarser ZigZag multipliers (e.g., 0.75, 1.0, 1.5) within the same benchmark cap, or within the EXP-060 longer horizon, to see if the trailing stop becomes beneficial at any tightness.

3. **Cost-aware partial-exit analysis:** Estimate commission/slippage drag from 3-leg partial exits vs single-leg benchmark to quantify the net advantage available at tradability.
