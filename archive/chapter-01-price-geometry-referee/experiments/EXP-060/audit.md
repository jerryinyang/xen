# Audit Report: EXP-060

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | 5-arm 2×2 factorial + BENCH + disclosed horizon sibling; A0 reproduces EXP-053; invariants cover single-leg match, degenerate V2A, shared stop, ADV-NONE, A4 cap dominance. |
| `code/run_experiment.py` | Edge cases | PASS | Empty cell path (`_empty_arm`); `<30` power floor; finite-ATR gate; np.errstate guard; 0-signal pool handled. |
| `code/run_experiment.py` | Type safety | PASS | Typed `ArmSpec`, `ArmResult`, `InProgressState` dataclasses; typed public functions. |
| `code/run_experiment.py` | NaN handling | PASS | `np.isfinite` gates on `atr_entry` and `m_sofar`; bootstrap CI explicitly returns `None` on underpowered; `isnan`-free metric paths. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 file-order-prefix: `slice(0, int(int(total*0.7)*0.7))`; full file never sorted/collected; domain bars fenced to `CloseTime ≤ train_end_epoch_s`; forward scans clipped → `DATA_CENSORED`. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy `scan_parquet` sorts by file order (pre-sorted at source); `is_sorted` assertion on `CloseTime` after load. |
| `code/run_experiment.py` | Memory/performance | PASS | Column projection (8 cols); per-instrument load + process; `tqdm` outer loop; per-cell `del cell`. |
| `code/run_experiment.py` | Safe optimization | PASS | Process-pool parallelism: per-cell RNG seeded by `(BASE_SEED, cell_index, purpose)` → order-independent; results merged in fixed `INSTRUMENTS` order; thread pools pinned to 1. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over instruments; per-worker `tqdm` within `as_completed`. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER`-based; concise per-run summary; helper functions return data not prints. |
| `code/run_experiment.py` | Organization / import side effects | PASS | Imports → constants → types → I/O → computation → invariants → flattening → composition → replay → plotting → orchestration; dirs created in `run()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | 5 plots from collected per-cell summaries + factorial records; no reloads. |
| `code/run_experiment.py` | Docstrings | PASS | Module, class, and public function docstrings; inline comments for arm specification, RNG streams, invariants. |

## Numerical Validation

### Spot Checks — GBPUSD-4h champion A3 (V2A-NONE)

From `champion_map.csv`:
- `m` = 67 qualifying events (≥ 30 power floor ✓)
- `median` = 0.9289616833465384 ATR units ≈ 0.93 ATR
- `ci_low_1s` = 0.6305091289301974 > 0 → **viable** (= `true` ✓)
- `contrast_random_low` = 0.1130106772968067 > 0 → beats matched-random ✓
- `contrast_ma_low` = -1.1980013598769215 < 0 → fails MA(20,50) baseline
- `champion_win` = `false` (requires both beats_random AND beats_ma) ✓

Cross-check: `composition_readout.json` shows 0 champion wins, 69 viable cells — the MA(20,50) baseline is structurally dominant (EXP-055 established that MA segments capture larger swings). The champion median of 0.93 ATR is plausible against the EXP-053 benchmark median of 0.77 ATR for this cell — the ADV-NONE and V2A add ~0.16 ATR.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| A3 champion `m` (qualifying events) | ≥ 0 | [56, 3754] | YES |
| A3 champion `median` (ATR units) | real | [−0.125, 0.929] | YES |
| A3 champion `ci_low_1s` | real | [−0.498, 0.631] | YES |
| `contrast_random_low` | real (delta) | [−0.627, 0.170] | YES |
| `contrast_ma_low` | real (delta) | [−2.404, −0.569] | YES — all negative |
| `beats_random` | {true, false} | 3 true / 96 false | YES |
| `beats_ma` | {true, false} | 0 true / 99 false | YES — MA baseline dominates systematically |
| `champion_win` | {true, false} | 0 true / 99 false | YES |
| Invariant violations | 0 | 0 | YES |
| Causality violations | 0 | 0 | YES |
| Determinism failures | 0 | 0 | YES |
| EXP-053 mismatches | 0 | 0 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| EXP-053 reconciliation | 99/99 consistent | YES | BENCH arm reproduces EXP-053 per-cell `stat_m`, `stat_median`, and `stat_r_firsthit` to 1e-9 for all 99 cells. |
| Determinism replay | 17/17 PASS | YES | First usable cell per instrument replayed byte-identically across all arms + baselines + interaction. |
| A3 champion wins | 0 cells, 0 instruments | YES | `contrast_ma_low` < 0 in 100/100 champion cells. MA(20,50) baseline captures structurally larger excursion swings (longer trends by construction). EXP-055 already disclosed this pattern. |
| A3 viable cells | 69/99 across 17 instruments | YES | Consistent with EXP-053's EVIDENCE_FOR finding. The V2A+ADV-NONE combination preserves the conditioned signal's positive median. |
| Factorial: champion_vs_bench | A3 - A0 | Plausible | The paired contrast measures the combined V2A+ADV-NONE improvement over the BENCH. Negative on MA-baseline contrast because MA segmentation captures larger trends — this is the disclosed "ambient regime property" from EXP-055. |
| Exit-reason composition | A0–A3 | Plausible | ADV-NONE arms (A1, A3, A4) have zero adverse exit weight; V2A arms (A2, A3, A4) split exits across fractional legs; benchmark cap (A0–A3) shows higher time-cap fraction than A4. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap (MBB) | Stationarity within block | PARTIAL | Acknowledged in scope; a known caveat for time-ordered financial data. Block length = `round(m^(1/3))` — short enough to mitigate within-block structure. The contrast with the independent MA(20,50) baseline provides an alternative reference. |
| Two-baseline IUT conjunction | Conservative (size ≤ α) | YES | The conjunction of two independent CI_low>0 conditions is strictly more conservative than either alone (Bonferroni-boundable). 0/99 champion_wins confirms the conjunction is binding. |
| P15 path-ordered fill model | Represents intrabar execution | PARTIAL | Documented approximation; EXP-054 measured the fill-model effect as Δr median 0.010 (IMMATERIAL). The median endpoint (P14) is robust to the tie-break choice. |
| Full-file ordering | Chronological by `CloseTime` | YES | Source files have strictly increasing `CloseTime` (cAlgo invariant); `is_sorted` assertion after load. |
| F01 file-order prefix | Identical to EXP-053–059 | YES | 99/99 population reconciliation PASS: counts, medians, and first-hit r all match EXP-053. |

## Results Plausibility

- **Champion verdict CHARACTERISED_NOT_VIABLE_ELIGIBLE** is internally consistent: 69/99 cells are individually VIABLE (median CI_low > 0) and composition is met (17/17 instruments), but the two-baseline IUT conjunction fails for all cells — MA(20,50) consistently dominates.
- **MA-baseline dominance** was pre-disclosed: EXP-055 found 0/99 cells beat MA(20,50) on median MFE. The "ambient regime property" means MA-segmented trends capture larger swings than ZigZag-identified moves at any single entry point.
- **Three cells beat matched-random** (GBPUSD-4h, USDCHF-4h, US2000-4h) — plausible given the EVIDENCE_FOR from EXP-053; all are longer-domain cells where the signal is strongest.
- **0 defects** across all invariant, causality, determinism, and reconciliation gates — the code and data handling are clean.
- **Exit-reason composition** shows the expected pattern: A1/A3/A4 have zero ADV weight; A0/A2 have ~0.18 ADV weight; A2/A3/A4 show weighted FAV leg distribution; A4 shows higher TIMECAP fraction (longer horizon censors more events).

## Scope Compliance

| Check | Verdict |
|-------|---------|
| Implementation matches plan | YES — exactly 5 arms (A0–A4), 2×2 factorial, champion A3 binding, A4 disclosed-only; P11 composition readout; all predeclared invariants. |
| Instruments match scope | YES — all 17 VAL-003 instruments; 3 COVERAGE_EXCLUDED cells (US500-4h, JP225-2h/4h). |
| Parameters match scope | YES — ATR 14/1.0, P2 50%, P3 1:1, P4 adaptive cap floor=6, P5 LOOKBACK=1, P7 p75/20, P15 path-ordered. |
| No undocumented analyses | YES — factorial and baselines are explicitly in scope. |
| Complexity budget | Stat tests: 4 (3 arm medians + factorial + interaction + baselines) / 4 budget. Plots: 5 / 5 budget. New modules: 0 / ≤1 budget. |
| Holdout exclusion verified | YES — TRAIN-only F01 prefix; final 30% global holdout + nested TEST never read. |
| Real-price outcome discipline | YES — HA prices used only in harami/impulse detection; all metrics on real OHLC. |

## Issues

### Critical

None.

### Warning

None.

### Info

1. **MA(20,50) baseline dominates all champion cells**
   - File: `results/composition_readout.json`, `results/champion_map.csv`
   - `contrast_ma_low` < 0 for all 99 champion cells (range −0.569 to −2.404). This is a systematic, pre-discovered substrate property (EXP-055: "0 cells beat MA(20,50) on median MFE"). The two-baseline IUT conjunction is the binding constraint; there is no path to CHAMPION_WIN for any cell on this substrate and MA baseline parameterization.

2. **DE30 truncated history**
   - File: `code/run_experiment.py` line 152–154
   - DE30 broker m1 data ends 2026-01-16. DE30 does not appear among 0 champion_wins (immaterial). DE30 per-cell counts are consistent with the shorter timeline (5m: 2521 conditioned vs 3117 BTCUSD-5m — proportional to its ~82% row count).

3. **ADV-NONE cost caveat**
   - File: `results/run_metadata.json`
   - ADV-NONE leaves the adverse unbounded within the cap. The median endpoint (P14) is robust to extreme left-tail outliers, but the mean may diverge. Costs are out of 014-B scope — this is a design limitation for a future tradability screen, not an audit finding.

4. **Fill-model approximation**
   - File: `results/run_metadata.json`
   - P15 path-ordered fill model is a documented approximation of unobserved intrabar motion. EXP-054 measured the effect as IMMATERIAL (Δr median 0.010) for symmetric 1:1 barriers on this substrate.

## Re-Audit Requirements

None — full PASS.

