# Pre-Execution Review: EXP-035

**Date:** 2026-06-10
**Experiment:** EXP-035 — TRAIN-Only Conditioning Characterisation (Clinical-Trade Dimensions)

## Governance Checks

### Scope
- Exploratory (characterisation, 0 slots; DIAG-005). Three predeclared dimensions: %completion-to-target (C1), session (C2), trailing volatility regime (C3).
- Hard no-selection rule: G1 qualification flags only; rule-freezing belongs to EXP-036.
- Data views: EXP-022/EXP-020 + rebuilt OHLC (needs High/Low for ATR). TRAIN-only with containment rule (completion_idx ≤ cutoff); TEST and holdout never read.
- G1 gate criteria per design §8.1: materiality (SNR≥1 + candidate net>0), structure (monotonicity/omnibus), stability (split-half), multiplicity (Holm at α_G1=0.10).
- Denominators: per-domain pooled terciles; reportability floors (<30 / <15 events → unreportable); composition-skew flag.
- Zero-baseline: absolute bps differences, not ratios.

### Analysis Plan
- Covariate construction: all three at-trigger (causal). C1 from band geometry with sanitation (share outside [0,1] disclosed). C3 via ATR(14) + trailing 90-day percentile window, calendar-advancing, ≥30 days history required.
- Binning: TRAIN-quantile terciles for C1/C3 (pooled per domain), fixed UTC sessions for C2. Boundaries frozen on emission.
- Inference: joint cluster bootstrap for contrast CI (F06); selection-aware stratified permutation (F05); Holm adjustment.
- F05 acknowledged caveat: event-level label permutation is anti-conservative under clustering; acceptable because §8.1 conjunction's binding leg is the cluster-aware SNR criterion.
- Visualization plan: 5 plots.

### Code
- **Sectioning**: imports → path → constants → I/O → integrity → rebuild → ATR + percentile → event table → band geometry → outcome + covariates → binning → summary → inference (contrast, permutation, stability) → qualification assembly → determinism → plots → orchestration.
- **Holdout exclusion**: standard first-70% via `load_analysis_data`; TRAIN cutoff nested. No holdout or TEST access.
- **Look-ahead**: ATR(14) strictly ≤ trigger timestamp; trailing percentile window advances by calendar time, not bar index. No outcome data past completion_idx.
- **Real-price discipline**: `lifetime_bps` from real OHLC outcomes.
- **Frozen inference**: EXP-027 pinned hash `e50873d12a9f68d9` verified.
- **Progress**: `tqdm` on file rebuild and characterisation loop (12 domain×dimension cells). Helpers return data.
- **Memory**: tidy frame built once, then all tests are pure functions of it. ATR loop is bounded sequential (Wilder smoothing). Trailing percentile uses bounded two-pointer sweep with bisect.
- **Zero-baseline**: absolute bps; bin contrasts are differences; reportability floors guard small-n bins.
- **No deduplication**: no `.unique()` calls.
- **No import-time side effects**: directories created in `main()`.
- **Determinism**: same-seed replay (tolerance 1e-12).
- **F06 joint contrast bootstrap**: implemented as specified — single cluster resample over union regime universe, both bin means formed from same resampled clusters.
- **F05 selection-aware permutation**: re-selects candidate by max rule inside each permutation iteration.
- **F07 stability**: chronological split-half with frozen full-TRAIN tercile boundaries.

### Design Alignment
- A3/DIAG-005 per design §5/A3. TRAIN-only diagnostic (0 slots).
- G1 qualification criteria per design §8.1 (i)-(iv) — all four legs implemented.
- C1/C2/C3 dimensions and binning predeclared, frozen before any TRAIN read.
- F05/F06/F07 amendments reflected in code.

## Verdict

```text
VERDICT: APPROVE
```
