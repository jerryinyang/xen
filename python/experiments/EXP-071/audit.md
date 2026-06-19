# EXP-071 — Audit (Stage 5)

**Auditor verdict: PASS** (0 Critical / 1 Warning / 3 Info)
**Date:** 2026-06-19
**Scope:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `frozen_selection.json`,
`results/` (per_cell_results.csv, portfolio_results.csv, composition_verdict.json,
test_read_manifest.csv, run_metadata.json), and the five plots.

The experiment is the harami family's **first counted TEST contact** (HYP-024). The audit
focuses on (a) the integrity gates that make a TEST read admissible, (b) byte-faithful reuse
of the EXP-070-calibrated EXP-068 machinery, and (c) independent recomputation of the binding
verdict.

---

## 1. Integrity gates — all verified

| Gate | Requirement | Finding |
| --- | --- | --- |
| **Holdout fence** | final 30% never loaded | `load_test_1m` lazy-scans `[0, train_cutoff)` ∪ `[train_cutoff, analysis_cutoff)`; `analysis_cutoff = int(total*0.7)`; holdout `[analysis_cutoff, total)` never materialized; forward barrier scans clip at the analysis edge → `DATA_CENSORED`. **PASS.** |
| **Freeze-before-TEST (D0 P8)** | `frozen_selection.json` written + SHA-256-pinned before any TEST row | `load_test_1m` hard-raises if the freeze file is absent; orchestration writes/loads the freeze (Step 1c) before the first `resolve_test_cell`. Freeze `frozen_utc=21:46:26` precedes run `21:51:52`. SHA-256 `ca16bcd…` recorded in `run_metadata.json`. **PASS.** |
| **TEST-family identity (D0 P5)** | EXP-068 g015 PARTIAL-V2A set ex-EURUSD == 6 P5 cells | `assert_dependency_gates` enforces set equality and aborts otherwise; freeze records the 6 cells byte-identically. **PASS.** |
| **Null-A binding gate (D0-amendment-004)** | every P5 cell `fpr_conj_nullA ≤ 0.05`, non-degenerate CI | enforced in `assert_dependency_gates`; the stale both-nulls `verdict` column is read for provenance only (note carried in metadata + freeze). All 6 FPRs ∈ [0.014, 0.035]. **PASS.** |
| **P12 reconciliation (D0 P1)** | EXP-068 BENCH+PARTIAL-V2A / EXP-061 M0 / EXP-066 PARTIAL-V2A reproduced on TRAIN at 1e-9 | `p12_reconcile` re-runs the frozen `compute_cell` per cell; `p12_max_abs_diff = 0.0` across all 6 cells (tol 1e-9). **PASS.** |
| **Determinism (D0 P7 Leg 3)** | full second pass byte-identical | `determinism_replay` re-resolves all 6 cells; `determinism_pass = true`, 0 mismatches; per-cell fingerprint includes the retained `pv_returns` rounded to 12 dp. **PASS.** |
| **Real-price discipline** | outcomes on RealOHLC; HA detection only | `resolve_test_cell` uses `exp068.real_ohlc(combined)`; HA candles enter only `harami_entry_indices`. No metric reads `HAOpen/High/Low/Close`. **PASS.** |
| **No TRAIN events in TEST inference** | TRAIN bars for state only | `cond = retained_p75 & (entry_epoch > train_end)` restricts the binding population to TEST-window entries; matched-random pool restricted via `warmup_test = warmup_all | (epoch ≤ train_end)`. Combined domain bars asserted strictly increasing across the TRAIN/TEST seam. **PASS.** |
| **Frozen inference reuse** | `signal_arm`/`matched_random_arm`/`_summarize_arm`/bootstrap/`_winsorized_mean` unchanged in semantics | all imported from `exp068` (module has no import-time side effects, thread pins set before polars/numpy import); only the 5 new local pieces (loader, freeze writer, Holm classifier, portfolio aggregator, manifest) are added. **PASS.** |

## 2. Independent recomputation of the binding verdict

Re-derived from the published per-cell p-values, independent of the experiment code:

- **Holm median leg** (k=6, α=0.05): sorted p = {GBPUSD-5m 0.0022 ≤ 0.00833 ✓; GBPJPY-30m
  0.0182 > 0.0100 ✗ → step-down halts}. Only **GBPUSD-5m** clears. Matches `median_holm_clear`.
- **Holm beats-RM leg**: sorted p = {GBPUSD-5m 0.0065 ≤ 0.00833 ✓; GBPJPY-30m 0.0491 > 0.0100 ✗}.
  Only **GBPUSD-5m** clears. Matches `beats_rm_holm_clear`.
- **Per-cell conjunction (median∧raw-mean∧beats-RM∧margin):** GBPUSD-5m fails on raw-mean
  (`pv_mean_ci_low_1s = −0.086 ≤ 0`); GBPJPY-30m passes raw-mean but fails both Holm legs;
  all others fail ≥2 legs. **0/6 cells clear.** Matches `clears_composition` (all false).
- **Experiment verdict:** `n_median_ci_low_neg = 4` (GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, US2000-4h
  have one-sided CI_low ≤ 0) > 6/2, and 0 cells clear → **TEST_NOT_CONFIRMED**. Reproduced exactly.

The classifier follows the predeclared D0 P9 mechanical rule (majority median CI_low ≤ 0 →
systematic negative → NOT_CONFIRMED). No discretion applied. **Verdict correct.**

## 3. Findings

### WARNING-1 — "equal-weight" portfolio composite is event-pooled and GBPUSD-5m-dominated
`portfolio_composite` pools **per-event** returns (`m_total = 5264 = Σ cell events`), so
GBPUSD-5m (3843 events, 73% of the pool) drives the composite. The positive composite median
CI (`composite_median_ci_low_1s = 0.496`) is therefore essentially the GBPUSD-5m signal, **not**
a cell-balanced family read. This matches the scope §Portfolio Disclosure wording ("pooling
per-event returns equally across cells") and the docstring ("each event weight 1"), but the
`analysis-plan` Step 5 parenthetical ("equally weighted by cell … regardless of cell event
count") describes a different (cell-equal) scheme that was **not** implemented. The two scope
texts are internally inconsistent; the code matches the binding scope text, not the plan
parenthetical. **Non-binding** (the verdict is per-cell only), so this does not change the
result — but the composite must **not** be read as family-level confirmation. Required action:
the interpretation (`results.md`) and report must disclose that the composite is event-pooled
and single-cell-dominated. No code change required.

### INFO-1 — verdict is mechanically NOT_CONFIRMED but part of the negative is power-limited
NZDUSD-1h (median CI_low −0.056, essentially at zero) and US2000-4h (n=75, single 4h cell, wide
CI) contribute to the majority-negative count but are closer to power-limited than to strongly
negative. The predeclared rule (majority median CI_low ≤ 0) correctly yields NOT_CONFIRMED; this
nuance is interpretive context, not a verdict defect. Disclose in `results.md`.

### INFO-2 — RM-native draw count differs slightly from signal count in one cell
US2000-4h: `rm_m = 72` vs binding `m = 75` (matched-random pool exhausted 3 fewer eligible
draws). This is frozen `matched_random_arm` behavior (pool-limited draw), reused unchanged;
immaterial to the contrast direction (beats-RM fails by a wide Holm margin). No action.

### INFO-3 — GBPUSD-5m is the lone yellow-flag cell
GBPUSD-5m satisfies median+ ∧ beats-RM+ ∧ winsorm+ (`pv_winsorm = 0.163`) but raw-mean−
(`pv_mean = 0.090`, CI_low −0.086) → `yellow_flag = true`. This is exactly the PARTIAL_RECOVERY
tail-drag signature flagged at D0 P4. It is the natural seed for the TRAIN-only diagnostic
follow-up (EXP-074 / HYP-027, already registered). Correctly flagged; disclose.

## 4. Code-standards spot check
Organization (imports → path setup → constants → types → I/O → pure computation → plotting →
orchestration → `main`) clean; thread pins before polars/numpy import; output dirs created only
in `run()`; `tqdm` on all outer loops (P12, TEST cells, determinism); plots built from collected
summaries with no heavy reloads; lazy Polars scans with column projection; no silent dedup; NaN
handled via explicit `None`/below-floor records. Conforms to project conventions.

## 5. Audit conclusion
All binding integrity gates pass; the inference machinery is byte-faithful to its certified
TRAIN state (P12 = 0.0); determinism PASS; the verdict reproduces independently. **VERDICT: PASS.**
The single WARNING (event-pooled composite labelling) is a documentation-disclosure requirement,
not a correctness defect, and is routed to Stage 6/7.
