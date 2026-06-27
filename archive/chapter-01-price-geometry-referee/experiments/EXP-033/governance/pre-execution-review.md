# Pre-Execution Review: EXP-033

**Date:** 2026-06-10
**Experiment:** EXP-033 — TRAIN-Only Horizon Sweep (Attribution Crossover + FH(H) Net Curve)

## Governance Checks

### Scope
- Two predeclared exploratory questions (attribution map + FH net curve / B2 selections); diagnostic only, 0 slots — conforms to design §5/A2.
- Data views: EXP-022/EXP-020 + rebuilt OHLC via `xen.bar_aggregator`; parameters locked (H grid, costs, financing).
- TRAIN-only with F08 containment rule (start_idx + MAX_H ≤ cutoff AND completion_idx ≤ cutoff); holdout excluded, TEST never read.
- Mechanical selection rules (one-SE H\*, simplicity-preference pyramid policy); F07 split-half stability disclosure, non-binding.
- Denominators defined: per-instrument event-weighted means → equal-weight cross-instrument; unreportable cells (<30 / <15 events) disclosed.
- Zero-baseline: absolute bps, no ratios. Complexity budget: 2 test families / 4 plots / 1 new module.

### Analysis Plan
- Reconciliation anchors against EXP-031 (H∈{1,6} leg effects ≤ 0.01 bps) before any sweep output; same PAIR_KEYS as EXP-031 confirmed.
- Shared bootstrap resample indices across H per domain for curve coherence.
- Interpretation guide predeclared; implementation safety constraints listed.

### Code
- **Sectioning**: VAL-001-style sections (imports → path → constants → I/O → integrity → rebuild → population → FH cols → containment → reconciliation → legs → inference → crossover → net curve → selections → stability → determinism → plots → orchestration).
- **Holdout exclusion**: standard first-70% analysis-set load via `load_analysis_data`; TRAIN cutoff is nested 70% of domain bars. No holdout path.
- **Look-ahead**: FH returns are forward-looking by design (the experiment measures H-bar outcomes); all covariates known at trigger time. No future-data use post-completion.
- **Real-price discipline**: all returns from real `Close`; no synthetic prices.
- **Frozen inference**: EXP-027 pinned hash `e50873d12a9f68d9` verified at runtime; same PAIR_KEYS as EXP-031.
- **Progress**: `tqdm` on file rebuild, attribution sweep, FH net curve. Helpers return data, no helper-level printing.
- **Memory**: vectorized FH computation via shifted-lookup (NumPy); no row-by-row Python loops over event frames.
- **Zero-baseline**: absolute bps; s_entry ill-defined guard (`|X_full| > SE`); unreportable cells skipped with disclosure.
- **No deduplication**: no `.unique()` calls.
- **No import-time side effects**: directories created in `main()`.
- **Determinism**: same-seed replay with identity tolerance 1e-12.

### Design Alignment
- A2/DIAG-004 per design §5/A2. TRAIN-only diagnostic (0 slots).
- Financing values match D0 memo and design predeclarations.
- F07 split-half disclosure and F08 containment rule amendments reflected in scope and code.

## Verdict

```text
VERDICT: APPROVE
```
