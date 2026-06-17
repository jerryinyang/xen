# Audit Report: Experiment EXP-060B — MA(20,50) Substrate Dominance (EXP-060 Gap-Fill)

## Summary

**Verdict: PASS.** 0 Critical, 2 Warning, 3 Info. The `SUBSTRATE_LEAD_FOUND` verdict is trustworthy: all
integrity gates pass, the reused machinery reproduces EXP-060 exactly, and the one new computation (RM3) is
correctly constructed, causally clean, and **non-degenerate** — the headline `M3 beats RM3 in 85/99 cells` is
a real, substantial signal contribution at the median, not a construction artifact. The two Warnings are
interpretive caveats the report must carry to G2 (the lead is narrow and the tradeable-mean edge is confined to
14/99 cells), not correctness failures.

Because this verdict **reverses the EXP-060 expectation and changes G2 routing**, the audit focused on the new
components not covered by the EXP-060 reconciliation: RM3 construction/causality/fairness, the mean bootstrap,
and the M3−RM3 contrast method.

## Code Review

**Diff scope (EXP-060 → EXP-060B):** new `bootstrap_mean_distribution`; `ArmResult` extended with mean
CI/dist + `draw_count`; `_summarize_arm`/`resolve_arm` thread a dedicated `mean_rng`; `matched_random_arm`
generalised over segmentation with explicit RNG-purpose args; new `_ma_context`, `_resolve_nulls`,
`champion_vs_null_contrast`, `ma_control_row`, `skew_rows`, `_skew_attribution`; floor=48/A4 arm and the
factorial decomposition removed (per scope). Median-path code paths unchanged.

- **RM3 construction (`matched_random_arm` via `_resolve_nulls`, lines 596–631, 780–808):** correct and
  symmetric to M3. RM3 receives the MA in-progress state (`ma_state_all` from
  `live_in_progress_state(..., seg.*)`), the MA segmentation `seg` (so the adaptive cap inside the function is
  MA-defined via `adaptive_time_caps_by_epoch(ohlc.epoch[drawn], seg.confirm_epoch, seg.confirm_idx)`), MA
  warmup, the **MA-conditioned** harami exclusion set (`ma_signal_idx = entry_idx[ma.stat.retained_p75]`), and
  `draw_count = m3_m`. It resolves through the **identical** `resolve_arm` path as M3 (champion `V2A-NONE`,
  `benchmark_barriers` from the drawn sub-state, ADV-NONE sentinel, `bench_n` cap). The only difference between
  M3 and RM3 is harami-vs-random entry selection — apples-to-apples. Dedicated RNG purposes
  (`PB_RM3_DRAW/BOOT/BOOT_MEAN = 31000/32000/33000`) leave every EXP-060 stream untouched.
- **Mean bootstrap (`bootstrap_mean_distribution`, lines 441–471):** block construction is byte-identical to
  `xen.expectancy.bootstrap_median_distribution` (`b = max(1, round(m**(1/3)))`, `ceil(m/b)` contiguous
  blocks truncated to `m`); only the statistic differs (`np.mean`). Computed only at `m ≥ POWER_FLOOR (30)`,
  from the dedicated `mean_rng`. `median_ci(mean_dist)` is reused for the percentile CI — correct, as
  `median_ci` is a generic percentile function (5th one-sided / 2.5th / 97.5th).
- **M3−RM3 contrast (`champion_vs_null_contrast`, line 575; `ma_control_row`, line 944):** uses **independent**
  `contrast_ci(variant.dist, null.dist)` on the stored bootstrap distributions — the correct method, since
  matched-random entries are different events with no common subset to pair. `m3_beats_rm3 = median_low_1s > 0`.
- **Causality gate (`_causality_ok`, lines 814–835):** extended to MA — verifies the MA reference segment ends
  ≤ entry epoch (`ma.seg.end_epoch[mk] <= entry_epoch`) in addition to the ZigZag checks. RM3's random entries
  inherit causality structurally: they reuse the same validated `live_in_progress_state` + `_subset_state` over
  `ma_state_all`, and the cap uses only pre-entry confirmed MA crossovers. (See Info-1.)
- **Holdout fence (lines 249–252, 297):** `train_rows = int(int(total*0.7)*0.7)`; `scan_parquet(...).select(cols)
  .slice(0, train_rows).collect()` — file-order prefix, no full sort/collect, domain bars fenced to
  `CloseTime ≤ train_end_ts`. TEST and the final-30% holdout are never read.
- **Standards:** organisation, sectioning, lazy Polars, `tqdm` over instruments, dedicated RNG streams, output
  dirs created only in orchestration — all consistent with EXP-060 and the code conventions.

## Numerical Validation

**Reproduction (reused machinery):** `population_reconciliation.csv` — 99/99 cells: `z3_m/z3_median` ==
EXP-060 A3, `m3_m/m3_median` == EXP-060 maseg, `all_signal_arms_match` and `z3_exit_weights_match` all `true`.
The fork did not perturb the median path (confirms the dedicated-RNG mechanism).

**Integrity flags (`run_metadata.json`):** `determinism_ok: true` (second-pass byte-identical re-run across
the 8 signal arms, both nulls, and the M3−RM3 independent contrast — median + mean), `causality_ok: true`
(0 violations), `invariant_violations: []`, `is_defect: false`.

**Invariants (`_cell_invariants`, lines 838–857), confirmed in outputs:** leg weights sum to 1.0; **ADV-NONE
fires 0 ADV exits** on Z3/Z1/M3/M1/RZ3/RM3 (0 rows with `ew_ADV>0` across all cells); shared 1:1 stop closes
all open legs at the benchmark adv level (Z2/M2); matched-count holds (`rm3_m/m3_m` ratio 0.949–1.000,
median 1.000; the <1.0 cases are low-n 4h cells where the eligible pool is slightly below the draw target —
expected, mirrors EXP-060).

**Spot checks (M3 vs RM3 non-degeneracy — the decisive question):**
- RM3 median across cells: min 0.268 / median 0.380 / max 0.530 — i.e. RM3 reproduces the **~0.38 geometry
  drift-capture baseline** (the same number the ZigZag random/champion produced in EXP-060). RM3 is a live,
  plausible control, **not** degenerate.
- M3 median across cells: min 0.075 / median 1.158 / max 1.821 — the harami+strong signal lifts the median
  ~0.78 ATR above the RM3 baseline. The M3−RM3 median contrast CI_low among median-viable cells: median 0.551,
  range −0.199…0.993 (only 4/89 ≤ 0). The 85-cell result is real and substantial.
- **Mean (the skew):** RM3 mean median −0.054; **M3 mean median −0.065** — both ≈0/negative at the typical
  cell. M3's mean is higher than RM3's where measured (e.g. GBPUSD-1h M3 0.595 vs RM3 0.173; GBPUSD-4h 1.084 vs
  −0.225), but it clears zero with one-sided confidence in only 14/99 cells. The capped-up (V2A) / uncapped-down
  (ADV-NONE) skew afflicts M3 exactly as predicted.

## Assumption Validation

- **Moving-block bootstrap** (median + mean): appropriate for time-ordered returns; block length tied to
  per-cell `m`. The **mean** CI is tail-sensitive and therefore wide — this is the intended measurement of the
  skew, not a defect; it is correctly the binding constraint on `mean_viable` (14/99).
- **Independent contrast** for signal-vs-matched-random: correct (different event sets). Less powerful than a
  paired design, but pairing is inapplicable here.
- **Power:** `m < 30` → not powered for either statistic; no ratios on empty denominators. RM3 pools are large
  on liquid cells (MA qualifies ~3–4× more events than ZigZag).

## Results Plausibility

The result is internally coherent and mechanistically sensible: (1) RM3 ≈ 0.38 = the geometry baseline;
(2) M3 ≈ 1.16 median = signal lifts the median on MA (unlike ZigZag, where the same signal did not beat its
random control in EXP-060 — 3/99); (3) M3 mean ≈ 0 = the no-stop left tail caps tradeable expectancy. All
three are consistent with the capped-up/uncapped-down thesis and with the substrate genuinely mattering for
whether the harami expresses an edge. Values are within expected ATR-normalised ranges.

## Scope Compliance

Matches scope/plan: 10 predeclared objects (8 signal arms + RZ3 + RM3), median binding / mean disclosed (P14),
no floor=48 arm, no factorial, 99-cell TRAIN grid, gross, real-price metrics (MA on real close; HA only for
detection). Complexity within budget (4 methods; 5 plots present; 0 new `xen/` modules — local helpers only).
Verdict fork implemented per plan §6.

## Issues

### Critical
None.

### Warning

- **W1 — The lead is narrow and concentrated (interpretation caveat, not a defect).** `m3_lead_cell` composes
  P11 only via **14 cells / 9 instruments**, and **8 of 14 are 4h** (n = 108–194) — the lowest-count, highest-
  noise domain (the same domain that produced EXP-060's 3 spurious random-beaters). The high-count lead cells
  have mean CI_low barely above zero (GBPUSD-5m 0.037, AUDUSD-30m 0.053, GBPJPY-30m 0.088). The verdict is
  mechanically correct (14/9 clears ≥5/≥3), but its robustness leans on small-n cells; the report and G2 must
  not read `SUBSTRATE_LEAD_FOUND` as a broad, stable edge. Recommend the results write-up disclose the lead-cell
  domain distribution and a sensitivity note (e.g. how the P11 tally changes if 4h cells are set aside).
- **W2 — Median dominance overstates tradeable expectancy (the central G2 caveat).** 89 cells are median-viable
  but only **14 are mean-viable**; M3's gross mean is ≈0/negative at the typical cell (mean median −0.065),
  i.e. the same left-skew as the ZigZag champion. `SUBSTRATE_LEAD_FOUND` is true at the binding **median**, but
  the *average* M3 trade makes ≈0 gross across most of the grid, before costs. The report must foreground that
  the "lead" is a median phenomenon and that the mean-positive subset is exactly the 14 lead cells.

### Info

- **I1 — RM3 causality is structural, not separately gated.** `_causality_ok` validates the harami-entry MA
  state, not the RM3 random-entry state explicitly. RM3 causality holds transitively (same `live_in_progress_state`
  over `ma_state_all` + `_subset_state` indexing; cap from pre-entry confirmed crossovers). No action needed;
  noted for completeness.
- **I2 — Plan/code discrepancy (code is correct).** analysis-plan §2 (Method 3) labels the M3−RM3 contrast as a
  *paired* `paired_median_contrast_ci`; the code correctly uses **independent** `contrast_ci` (matched-random
  are different events — no common subset to pair). The plan text is the error; the implementation is right.
  The documenter should correct the plan note in the report.
- **I3 — Matched-random does not isolate signal sub-components.** M3 (harami + /STRONG-STAT p75) vs RM3 (random
  in-MA-regime, non-conditioned) attributes the lift to the **combined** signal, not separately to the harami
  pattern, the strong-magnitude conditioning, or their interaction with MA direction. This mirrors EXP-060's
  matched-random convention and is acceptable for the binding "does the signal add value on MA?" question; an
  attribution split would be a new scoped experiment (relevant only if G2 routes to a SUBSTRATE follow-up).

## Re-Audit Requirements

None. PASS as-is. The two Warnings are interpretive disclosures for `results.md`/`report.md`, not code fixes.
