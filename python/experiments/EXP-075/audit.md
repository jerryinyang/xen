# Audit Report: Experiment EXP-075

TRAIN-design of an exhaustion-cap entry filter on the 99-cell MA-native N-PARTIAL-V2A harami
(CF-HA-HARAMI-001 / HYP-028).

## Summary

- **Verdict**: CONDITIONAL PASS (code correct, fences intact, verdict numerically faithful; one
  process Warning — the executed run narrowly predated the F4 disclosure-column instrumentation —
  plus two Info notes).
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 2

The implementation is numerically faithful to the analysis plan: the TRAIN/TEST/holdout fence
holds, the baseline `r_e` reconciles to EXP-074 to 1e-9 (the hard-fail assert did not trip), the
exhaustion cap is a causal entry-only boolean subset, the matched-random null is re-drawn at the
retained count, the run is deterministic by construction, and the routing verdict
(`FILTER_INEFFECTIVE`) is correctly computed under the pinned, pre-registered thresholds. The
result is a clean negative: the exhaustion cap is **not a lever** — neither the deployable uniform
rule (M-GLOBAL) nor the per-cell overfit ceiling (M-PERCELL) materially improves any band-core
domain.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Cap = `cond ∧ (feat ≤ U)`; `metric_on_subset` bootstraps retained `r_e`; matched-random re-drawn at retained `n`. Feature/`r_e` alignment hard-checked (`np.allclose(res.r_full[qual][order], res.r_e)`, line 244). |
| `code/run_experiment.py` | Holdout/TEST fence | PASS | `load_train_1m` slices `[0, int(int(total·0.7)·0.7))` only; TEST + holdout never sliced/collected; forward resolution clips at the TRAIN edge. |
| `code/run_experiment.py` | Reconciliation | PASS | `pass_a` asserts uncapped `r_e == EXP-074 events_<cell>.parquet` at 1e-9 (hard-fail); run completed → all cells matched. |
| `code/run_experiment.py` | Causality | PASS | Cap only removes entries; never reaches forward; never alters a retained event's resolution. `msofar_atr`/`ss_excess` use the entry bar's own close vs the pivot confirmed at `ConfirmTime ≤ t_i` and trailing ATR/p75. |
| `code/run_experiment.py` | Determinism | PASS (by construction) | Integer-list seeds `[BASE_SEED, ci, sel, form, thr, purpose]`; matched-random `_null_key` is collision-free across `sel/form/thr` for `ci ≤ 98`. No `hash()` on labels. Not re-run (≈28 min); same posture as the EXP-074 audit. |
| `code/run_experiment.py` | Pinned-denominator / no membership drift | PASS | `powered` = baseline q05 tail ≥ 30, fixed pre-cap; the cap never moves its own denominator. No dedup on the event set. |
| `code/run_experiment.py` | Routing logic | PASS | `route()` maps the per-domain vector to the four-tier verdict exactly per the pinned bars (see Numerical Validation). |
| `code/run_experiment.py` | Organization / import side effects | PASS | imports → path → constants → types → I/O → pure compute → plotting → orchestration → `main`; dirs in `run()`; `Agg`. |
| `code/run_experiment.py` | Memory/performance | PASS | Resolutions discarded per cell; pass B re-resolves only band-core+5m (68 cells); plots reuse in-memory tables. |
| `code/run_experiment.py` | Progress / logging | PASS | `tqdm` on both passes; concise summary print. |

## Numerical Validation

### Run integrity

- **Cells**: 99 resolved; **67 powered** (5m=17, 15m=17, 30m=17, 1h=16; 2h/4h=0) — **identical to
  EXP-074**, confirming the same TRAIN resolution and powered-cell definition. Pass B covered the
  68 band-core+5m cells (4 domains × 17 instruments). ✓
- **Reconciliation**: the `pass_a` hard-fail (`baseline r_e reconciliation FAILED vs EXP-074`) did
  not raise, so every cell's uncapped `r_e` matched EXP-074 to 1e-9. ✓
- **Locked thresholds**: F1 `U = 20.61` ATR (p95), F2 `U' = 5.86` (p95). Both locked at p95 because
  **no percentile improved any band-core domain** (`u_sensitivity` F1/F2 = 0 at p85/p90/p95), so the
  pre-registered tie-break (toward least restrictive) correctly selected the highest percentile. ✓

### Routing verdict (re-derived against the pinned bars)

Per-domain F1 vector (binding):

| Domain | n_pow | base share | M-GLOBAL share | Δ (uplift) | M-PERCELL share | percell uplift | premium | hurt |
|---|---|---|---|---|---|---|---|---|
| 15m | 17 | 0.059 | 0.059 | 0.000 | 0.000 | −0.059 | −0.059 | no |
| 30m | 17 | 0.059 | 0.059 | 0.000 | 0.176 | **+0.118** | +0.118 | no |
| 1h | 16 | 0.188 | 0.188 | 0.000 | 0.188 | 0.000 | 0.000 | no |

- **M-GLOBAL adds 0 improved cells in every domain** (Δ = 0.000 everywhere, incl. 5m) — the
  deployable uniform cap changes no cell's improved status at the locked U.
- **M-PERCELL** (overfit ceiling) reaches its max uplift at 30m = **+0.118 < 0.15** (`UPLIFT_BAR`).
- `route()`: `powered_domains` = 3 ≥ 2 (not INCONCLUSIVE_POWER); `improved` (M-GLOBAL) = 0 < 2 (not
  FILTER_PROMISING); `percell_uplift` list = ∅ (no domain ≥ 0.15) ⇒ **`FILTER_INEFFECTIVE`**. ✓
  Correctly computed and consistent with `route()`'s definition.

**Bar-sensitivity (disclosed, decision-neutral):** the verdict turns on `UPLIFT_BAR = 0.15`. 30m's
M-PERCELL uplift +0.118 falls short; were the bar 0.10 the label would flip to **FILTER_OVERFIT**
(M-PERCELL gains exist but M-GLOBAL improves 0 domains). **Both tiers route identically** — do not
spend the holdout; route toward closing CAND-001 — so the *disposition* is robust to the bar even
though the *tier name* is not. The 0.15 is a pinned, pre-registered, analogy-borrowed bar (EXP-074
material bar ↔ AUC 0.575), not a calibrated value; this is correctly disclosed in `results.md`.

### Mechanism check (confirms the EXP-074 bimodality reading)

Spot-checked `cell_metrics.csv`: the M-GLOBAL cap **lowers** the mean in cells where high-exhaustion
entries are median-positive winners (e.g. USTEC-1h base_mean +0.167 → global_mean_F1 −0.089 at
retention 0.899; BTCUSD-30m +0.126 → wait, −0.154). High `m_sofar/atr` entries are **bimodal** —
the cap removes catastrophic q05 losers *and* large winners together, netting ≈0 or negative. This
is direct empirical confirmation of EXP-074's tail-shape/bimodality finding and is the mechanistic
reason the cap cannot be a lever. ✓

### Undefined-feature share (F4 disclosure — computed independently)

Recomputed from EXP-074's `events_<cell>.parquet` (which carry `msofar_atr` and `ss_excess_ratio`
over the full qual population): **`undef_share ≡ 0.0` for both F1 and F2 across all 68 band-core+5m
cells** (mean and max 0.0 per domain). The `cond` gate (`retained_p75` ∧ TRAIN) only admits events
with a valid state and defined strong-stat, so the cap features are always defined on the qual set.
**Consequence:** retention reflects the exhaustion cap alone — the F4 retention-attribution caveat
is empirically void for this experiment. ✓

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap (mean/median legs) | Local serial dependence among clustered events | OK | Frozen EXP-068 block bootstrap, `b=round(n^{1/3})`, N_BOOT=10k; descriptive CI. |
| Matched-random re-draw at retained count | Capped signal vs count-matched regime random | OK | `matched_random_arm` re-drawn at retained `n` per (cell, form, thr); keeps the beats-RM contrast apples-to-apples (analysis-plan Step 2). |
| Pooled-quantile global U | A deployable rule is one rule | OK | `U_global` from the band-core pool; 5m evaluated under it (disclosed), excluded from the pool that sets it. |
| Joint four-leg `improved` criterion | The economically correct instrument for exhaustion bimodality | OK | Requires raw-mean ∧ median ∧ beats-RM CI_low>0 ∧ retention ≥0.70 simultaneously (analysis-plan Step 3). |

## Scope Compliance

- Analysis plan followed: YES (per band-core domain binding; 5m + band-pooled disclosed-only;
  F1 lead / F2 normalizer-robustness; M-GLOBAL deployable / M-PERCELL diagnostic-only; pinned bars).
- TRAIN-only, 0 counted TEST reads, holdout untouched: YES.
- No candidate slot consumed; locked filter explicitly non-confirmatory (`deployable=false`): YES.
- Complexity budget: 3 stat families + bootstrap (≤3 ✓); 6 plots (=6 ✓); 1 module (=1 ✓).
- No parameter tuned beyond `U` (selected by the pre-registered mechanical rule): YES.

## Issues

### Warning

1. **The executed run narrowly predated the F4 disclosure-column instrumentation, so
   `cell_metrics.csv` lacks `undef_share_F1/F2`.**
   - File: `code/run_experiment.py` line 497 (`undef_share_{form}`); the edit is present in the
     source (mtime 11:15:38) but the run process (results written 11:43:17, ≈28 min runtime) began
     within seconds of the save and imported the pre-edit source.
   - Impact: **none on the verdict or any metric** — the F4 change only *records* a column; it
     touches no resolution, mask, seed, denominator, or statistic. The disclosure was reconstructed
     independently from EXP-074 parquets (`undef_share ≡ 0.0` everywhere; see Numerical Validation)
     and is carried into `results.md`.
   - Fix (no re-run required for correctness): the next EXP-075 execution will emit the columns
     natively. The interpretation already states the empirically-zero undefined share, so the
     analysis-plan's retention-attribution disclosure requirement is satisfied.

### Info

1. **Matplotlib "categorical units" warning from `plot_u_sensitivity`.** The U-sensitivity plot
   passes the percentile x-axis as strings (`"85"/"90"/"95"`); matplotlib warns they are parseable
   as numbers. Cosmetic only — the plot renders correctly. Optional: cast to int or label explicitly.

2. **Run cost.** ≈28 min wall (pass A 15:24 over 99 cells, pass B 12:57 over 68), dominated by the
   ~5,500 block-bootstraps incl. matched-random re-draws. Inherent to the per-threshold matched-null
   design; bounded and `tqdm`-tracked. No action.

## Re-Audit Requirements

No code re-run required — results are numerically trustworthy and the verdict is robust. The single
Warning is a process timing note with zero verdict impact; the mandated `undef_share` disclosure was
reconstructed (≡ 0.0) and the next run emits it natively. Recommended (non-blocking): silence the
`plot_u_sensitivity` categorical-units warning on any future re-run.
