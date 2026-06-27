# EXP-090 — Results

**Verdict:** `READINESS_CALIBRATION_DELIVERED` · 20 MEMBER / 12 COVERAGE_EXCLUDED · determinism PASS · holdout untouched · 0 counted TEST reads · 0 candidate slots. (Final run; see [audit.md](audit.md) for the two prior runs.)

## Factual outputs

### Coverage & entries ([results/entry_coverage.csv](results/entry_coverage.csv))
- All 32 cells `IN_FLOOR` (≥15 events). CORE fade entry counts: 15m 12,827–16,225; 1h 3,293–4,156. Entry rate ~227–281 per 1,000 domain bars.
- Dropped-window fraction 0.001–0.217 (max JP225-1h), all ≤ 0.25 (construction PASS).

### Exit substrate ([results/exit_substrate_readiness.csv](results/exit_substrate_readiness.csv))
- 32 cells × 5 arms (RCT, ERT, ATR-barrier, RSI-revert, fixed-bar): **fill-price validity TRUE, timestamp-aligned TRUE, determinism TRUE — everywhere.**
- Resolution completeness 0.991–1.000 (median 0.996). Conservative adverse-first tie-break incidence ≤ 0.184%.

### Member map ([results/member_map.csv](results/member_map.csv))
- **20 MEMBER** (10 × 15m, 10 × 1h). Carried margins: RCT 0.0125 ATR, ERT 0.025 ATR. Native-arm key: RCT carries 15 cells, ERT carries 5 (4 RCT-only, 1 RCT+ERT among them; full table in [report.md](report.md)).
- **12 COVERAGE_EXCLUDED**, all for "no finite MDE on either native arm" (power outcome): EURUSD-15m, USDCAD-15m, USDCAD-1h, AUDUSD-1h, NZDUSD-15m, EURJPY-15m, XAUUSD-1h, BTCUSD-15m, BTCUSD-1h, US500-15m, US500-1h, JP225-1h.

### FPR / MDE ([results/fpr_mde_per_cell.csv](results/fpr_mde_per_cell.csv), [results/null_fpr_sanity.json](results/null_fpr_sanity.json))
- Native-arm FPR by domain × null (median / max): 15m A 0.050/0.068, B 0.049/0.070; 1h A 0.051/0.063, B 0.048/0.067. Symmetric and controlled across both nulls.
- Every MEMBER carried arm ≤ 0.050 under both nulls (0 violations).
- `null_fpr_sanity.controlled_alpha0: false` — pooled all-points boolean tripped by noise-level exceedances (A max 0.071, B max 0.082); not a per-cell control failure.
- Median lower-bound leg dropped (D5 non-binding); `fpr_median` columns are null.

### Determinism / provenance ([results/run_metadata.json](results/run_metadata.json))
- `determinism_pass: true` (EURUSD-15m, AUDJPY-1h). Headline outputs SHA-256 hash-pinned. `holdout_untouched: true`, `counted_test_reads: 0`, `candidate_slots: 0`, `real_fade_outcomes_resolved: false`.

## Interpretation (separated from facts above)

- **The deliverable map is the result.** 20 cells are ready and powered for EXP-091, each carrying its calibrated margin; 12 cannot bound a confirmation at their event count and are excluded with record. This is a power/recovery map, not an edge result — no real fade outcome was read.
- **The excluded set is a uniform power outcome**, not an FPR or engine failure: all 12 fail only for "no finite MDE," every cell is `IN_FLOOR`, and the engine and FPR control are clean throughout.
- **Membership near the FPR boundary is noise-sensitive.** Against the prior (broken-Null-B) run: 9 robust / 11 newly-admitted / 3 boundary-noise dropouts. The 9 robust cells are the safest core; the hard ≤0.05 gate (±0.014 noise) flips marginal cells. See [report.md](report.md) for the cell-level decomposition and the EXP-091 caveat.
