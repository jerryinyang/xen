# EXP-090 — Audit

**Verdict: PASS (final run), after two HALT-class confounds were found, reproduced, fixed, and the experiment fully re-run.** All fixes are recorded in [`D0-amendment-002.md`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-002.md). No ratified parameter-table value was changed.

## Audit trail (three runs)

### Run 1 — HALT: 1-minute fill engine (two defects)

The first run reported `READINESS_CALIBRATION_DELIVERED` with **all 32 cells COVERAGE_EXCLUDED** — which the audit identified as a **mis-reported process-level HALT**, not a clean map. Root cause (reproduced):

1. **Window over-assignment** — `xen.intrabar_fill.minute_bounds_for_domain` mapped each domain bar to the 1-minute bars since the *previous kept* domain close (`(dce[k-1], dce[k]]`). Because `build_domain_bars` drops coverage/fence windows and markets have session gaps, `dce` is non-contiguous, so a bar absorbed 1-minute bars from dropped/gap windows whose prices fall outside its own `[Low,High]`. Reproduced: 817 / 60,026 EURUSD-15m bars had mapped 1m ranges exceeding the domain `[Low,High]`; up to ~22% of windows dropped on JP225.
2. **Limit/stop gap-throughs** — even with the window fixed, ~2.5% of favourable fills recorded the *level* when price gapped past it within the touching 1-minute bar (level outside that bar's `[Low,High]`).

Both violate the D2.5 "fill price = a real touched level ∈ `[Low,High]`" invariant. Two further orchestration defects were noted and fixed: the verdict logic did not implement the predeclared HALT (only checked non-determinism), and `_classify_member` filed a readiness-invariant breach as benign `COVERAGE_EXCLUDED` rather than `NOT_READY`/HALT.

**Fixes (Amendment 002, Fix 1):** anchor each bar's 1-minute window to its own `(close − period, close]` (matching `aggregate_ohlc`'s bucketing exactly); gap-through fills fill at the touching 1-minute bar's **open** (a real marketable price in `[Low,High]`). Added `minute_open` to the engine. Added a `NOT_READY` verdict and a `HALT_READINESS_INVARIANT` experiment verdict so a systematic engine failure can never again be reported as a clean map. Post-fix: fill-validity TRUE on all 32 cells × 5 arms.

### Run 2 — DELIVERED (12 members), but Null B found methodologically broken

Run 2 (engine fixed) delivered 12 members but `null_fpr_sanity` showed `controlled_alpha0: false` with Null B (block-rotated 1m path) FPR up to **0.248**. Investigation (reproduced):

- Block-rotating the 1-minute **price path** matches each entry to **wrong-era prices**, so the ATR-normalised return `dir·(fill − entry)/ATR_entry` mixes a fill from one price regime with an entry/ATR from another, **inflating per-event return variance 30–145×** (BTCUSD-1h RCT std 0.29→9.25 ATR; EURUSD-1h ERT 0.46→67.4 ATR). The recentred mean is exactly 0 (verified ≈1e-16 — *no injected expectancy*), but the heavy-tailed cross-regime distribution destabilises the binding **mean** lower bound, miscalibrating Null B's FPR.
- `scope.md` originally specified Null B as **block-permuted real returns** (EXP-001/027/044 form); the analysis-plan substituted block-rotated *path* (EXP-070 form). EXP-070 tolerated path-rotation only because its binding statistic was the **median** (outlier-robust); EXP-090's binding statistic is the **mean**.
- Consequence: the both-nulls-binding gate wrongly excluded 14 cells that pass the faithful null A with a finite MDE and only trip the broken Null B.

**Fix (Amendment 002, Fix 2):** Null B reverts to the circular moving-block resample of the resolved **real return series** (`_block_permute_returns`, EXP-044 form) — preserving real magnitude, breaking long-range serial dependence, no cross-regime explosion. Post-fix: Null B std matches the real null (0.29→0.32, 0.46→0.47), centred mean 0.

### Run 3 — final, PASS

20 MEMBER / 12 COVERAGE_EXCLUDED, determinism PASS, holdout untouched, 0 reads, 0 slots. Integrity verified:

- **Fill substrate:** fill-validity / timestamp-alignment / determinism all TRUE on every cell × arm; resolution 0.991–1.000.
- **FPR control:** every MEMBER's carried arm ≤ 0.050 under both nulls (0 violations); native-arm FPR symmetric across nulls/domains (median 0.048–0.051, max 0.063–0.070) — controlled to sampling noise. The pooled `controlled_alpha0: false` boolean trips only on expected noise-level exceedances (one Null A/B point ~0.07–0.08), not a machinery defect; no member rests on an over-firing arm.
- **Coverage:** all 32 cells `IN_FLOOR`; all dropped-fractions ≤ 0.217 < 0.25.
- **Determinism:** EURUSD-15m, AUDJPY-1h byte-identical replay; headline outputs SHA-256 pinned in `run_metadata.json`.

## Non-confound deviation (recorded, non-binding)

The **disclosed median lower-bound leg** (D5, "co-reported, never gates") was **dropped** for performance — `np.median` was ~86% of bootstrap cost (424 ms → 61 ms/call). The binding **mean** lower bound is **bit-identical** to the shared `xen.ass` estimator (verified across seeds; the median computation consumed no randomness). Recorded in `run_metadata.json` (`median_leg`). This is an output reduction of a non-binding diagnostic, not a methodology change; runtime fell from ~8 h to ~67 min.

## Anti-overfitting fence (verified)

`real_fade_outcomes_resolved: false` — the real CORE fade entries' exits were never resolved or read; the calibration used only matched-random-entry exit-resolved returns (random placement, not the signal). Planted drift touched outcomes only, never placement/matching. Holdout untouched; counted reads 0.
