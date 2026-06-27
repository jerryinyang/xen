# Pre-Execution Review: EXP-034

**Date:** 2026-06-10
**Experiment:** EXP-034 — Per-Instrument Cost-Bearing Tradability Screen (with Financing)

## Governance Checks

### Scope
- Single hypothesis: positive net per-event expectancy on EURUSD-4h under frozen costs + financing, fixed-sequence FWER=0.05.
- Declared cell family from D0 §1.1, testing order from D0 §1.2; power statement predeclared.
- Data views: EXP-022/EXP-020 + rebuilt OHLC; full analysis set (same population as EXP-028/030).
- Holdout excluded; no TRAIN/TEST sub-splitting. Financing rates operator-amendable only until scope freeze.
- Denominators: per-cell event counts must reconcile exactly with EXP-030 (EURUSD-4h 39, USTEC-4h 36, XAUUSD-1h 207).
- Zero-baseline: absolute bps vs 0; no percentage metrics.
- F01 clarification: binding rule is one-sided 95% lower bound (5th pctile) > 0 AND boot_p ≤ 0.05.
- F02 note: A1 strict pass is necessary-but-not-sufficient for G2 (requires TEST confirmation).

### Analysis Plan
- Method: deterministic overlay on EXP-030; reconciliation guards (counts exact, no-financing net ≤ 0.01 bps, CI-seed reproduction ≤ 1e-6 bps) hard-fail before any verdict.
- Single new computation: per-event financing duration via shared `xen.financing` helper; verified by self-check.
- Fixed-sequence walk at one-sided α=0.05; descriptive labels for unreached cells.
- Seed-robustness disclosure (8 seeds) + determinism replay.
- Visualization plan: 3 plots.

### Code
- **Sectioning**: imports → path → constants → I/O → integrity → rebuild → event table → cost overlay → reconciliation → inference → sequence walk → disclosures → determinism → plots → orchestration.
- **Holdout exclusion**: standard first-70% via `load_analysis_data`. No holdout access.
- **Look-ahead**: outcome `lifetime_bps` is precomputed from event lifetime; no post-completion data used. Financing uses trigger→completion timestamps.
- **Real-price discipline**: `lifetime_bps` derived from real OHLC returns.
- **Frozen inference**: EXP-027 pinned hash `e50873d12a9f68d9` verified; F04 CI reconciliation uses EXP-030's seed payload to reproduce EXP-030 CIs.
- **Progress**: `tqdm` on file rebuild and per-cell inference loop (12 cells). Helpers return data.
- **Memory**: vectorized cost/financing overlay (NumPy). No row-by-row Python loops.
- **Zero-baseline**: absolute bps; metrics against 0 only.
- **No deduplication**: no `.unique()` calls.
- **No import-time side effects**: directories created in `main()`.
- **Determinism**: same-seed replay (tolerance 1e-12); seed robustness across 8 seeds.

### Design Alignment
- A1 per design §5/A1. Verdict-grade screen of HYP-004 baseline + frozen cost layer (0 candidate slots).
- D0 §1.1/§1.2 declared family and fixed-sequence procedure correctly implemented.
- F01 one-sided test, F02 G2-note, F04 CI reconciliation all reflected.
- Financing rates and RT costs match D0 and design predeclarations.
- `g2_admissible: false` with correct §8.4 amendment note in metadata.

## Verdict

```text
VERDICT: APPROVE
```
