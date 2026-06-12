# Results: Experiment EXP-044

## Summary

The per-cell calibration delivered its coverage map in full: all 50 READY
cells classified, determinism replay PASS, audit PASS. Experiment verdict
per the predeclared rules: **CALIBRATION_DELIVERED** (Evidence FOR). The
frozen EXP-027 event-level inference, applied standalone per cell with no
pooling and no Holm, is **COVERED in 37 of 50 cells** (74%) and
**NOT_COVERED in 13**, with zero CALIBRATION_UNDERPOWERED cells (100% draw
completion; max FPR Wilson half-width 0.0225 vs threshold 0.03). The
METHOD_NOT_TRANSFERABLE triggers did not fire: two-null disagreement occurred
in only 2 instruments (AUDUSD, USDCAD; trigger requires ≥3) and no domain
showed wide FPR excess. G1 leg (ii) is therefore adjudicable from
`coverage_map.csv`: the 37 COVERED cells may proceed to Track B; the 13
NOT_COVERED cells are excluded with record.

## Detailed Findings

### 1. Error control holds in most cells; failures are mostly marginal N1 excess

- **Observation**: per-cell FPR at α₀ = 0.05 averages 0.041 under N1
  (placebo-on-real) and 0.031 under N2 (block-permuted), n = 500 reportable
  draws per point everywhere. Twelve cells fail on an FPR point estimate
  above α₀; eleven of those are marginal (0.052–0.062) — for every marginal
  cell the Wilson 95% interval **includes α₀** (e.g. AUDUSD-1h
  [0.036, 0.075]), so sampling variability alone could explain each
  individual excess — and exactly one is **material**: USDCAD-2h, N1
  FPR = 0.070 with Wilson interval [0.051, 0.096] entirely above α₀. The
  exclusion criterion is the predeclared point-estimate rule at adequate
  precision, a deliberate conservative design choice; G1 should read the
  11 marginal cells as borderline failures, not clear excesses.
- **Evidence**: `fpr_per_cell.csv`; `plots/fpr_per_cell_heatmap.png`.
- **Interpretation**: the per-cell application of the frozen machinery is not
  systematically broken — there is no domain-wide or instrument-family
  pathology — but at single-cell resolution a marginal-excess tail exists,
  concentrated under N1. Under the predeclared Revision-1 rule these cells
  are honestly NOT_COVERED; the rule is strict by design and the
  marginal/material grading is preserved in the `reason` column.

### 2. The MDE-vs-count curve behaves as power theory predicts

- **Observation**: among COVERED cells, median per-cell MDE is 16 bps at 1h
  (151–266 events; range 8–32), 32 bps at 2h (86–143 events; range 16–128),
  and 64 bps at 4h (32–86 events; range 32–128). The only cell with no
  finite MDE on the {1,…,128} bps grid is BTCUSD-4h (68 events, TPR at
  128 bps = 0.64); BTCUSD-2h needs the full 128 bps. TPR curves are
  monotone within Monte-Carlo noise.
- **Evidence**: `tpr_mde_per_cell.csv`; `plots/mde_per_cell_heatmap.png`,
  `plots/mde_vs_event_count.png`.
- **Interpretation**: per-cell inference degrades smoothly, not abruptly, as
  counts fall from ~270 to ~32 — there is no cliff below which the machinery
  stops functioning, but thin 4h cells can only certify large effects
  (32–128 bps). BTCUSD's outsized MDEs at every domain reflect its return
  volatility, not a method defect. This table is the Track B/D power
  context: a Track B candidate in a 4h cell must plausibly carry ≥32–128 bps
  per-event excess to be detectable there.

### 3. The new grid territory is usable

- **Observation**: the 13 new-universe instruments contribute 31 COVERED /
  7 NOT_COVERED cells; the first-ever 2h domain has 12 of 16 cells COVERED
  with realistic MDEs (16–64 bps for everything except BTCUSD). Among the
  previously calibrated universe, AUDUSD-1h, BTCUSD-1h, and USTEC-1h are
  marginal-excess NOT_COVERED despite large counts — confirming that
  EXP-027's pooled-domain FPR control did not automatically transfer to
  every single cell, which is precisely why this experiment was required.
- **Evidence**: `coverage_map.csv`; `plots/coverage_verdict_summary.png`.

### 4. Substrate-level validity holds, but N1 > N2 is a systematic offset, not noise

- **Observation**: the predeclared METHOD_NOT_TRANSFERABLE triggers did not
  fire — Wilson-interval disagreement in only 2 instruments (AUDUSD,
  USDCAD; trigger requires ≥3) and no domain-wide excess. However, the
  per-cell pattern is systematic: N1 FPR exceeds N2 FPR in 35 of 50 cells
  (13 below, 2 ties; one-sided sign-test p ≈ 0.001), medians 0.041 vs
  0.030, and 11 of the 12 FPR-based NOT_COVERED cells fail on N1 only
  (USDJPY-4h, N2 = 0.054, is the lone N2-only failure). The Wilson
  non-overlap trigger was designed for gross per-instrument disagreement
  and is structurally insensitive to a consistent ~0.01 offset at n = 500
  (half-widths ≈ 0.02), so "trigger not fired" must not be read as "the
  two nulls agree."
- **Direction and diagnosis**: N1 > N2 is the opposite direction of the
  block-length artifact the plan's caveat 4 anticipated (N2 > N1).
  Estimated block length is 1 in every cell, making N2 an i.i.d.-resampled
  comparator in practice — so the gap is read as real-return dependence
  that N2 destroys and N1 retains. A read-only diagnostic over the 50
  cells supports this: per-cell N1 FPR is uncorrelated with event count
  (Spearman ρ = 0.06; BTCUSD-1h at 273 events fails), while the N1−N2 gap
  correlates positively with regime count (ρ ≈ 0.40, ρ = 0.35 with event
  count) and negatively with events per regime (ρ ≈ −0.32). The FPR
  failures also spread across all domains (1h 3, 2h 4, 4h 5) rather than
  concentrating in thin 4h cells — the failure mode the scope's honest
  prior expected (MDE failure in thin cells) produced only BTCUSD-4h.
  Together this points at within-regime dependence of real returns under
  the per-cell statistic, not event sparsity or noisy control means, as
  the driver of the marginal N1 excess. This is a descriptive diagnosis
  from existing outputs, not a calibrated attribution.
- **Binding consequence (for G1 adjudication 2 of 2)**: the predeclared
  per-cell rule already requires FPR ≤ α₀ under **both** nulls, so the
  stricter N1 is binding by construction and the 12 FPR-based exclusions
  stand. Re-basing coverage on N2 alone would be post-hoc metric
  reselection, which the scope explicitly excludes. The pooled-domain
  two-null agreement EXP-027 found did not replicate at per-cell scale;
  the coverage map absorbs this honestly via the conservative rule.
- **Evidence**: `run_metadata.json` `substrate_check`;
  `fpr_per_cell.csv` (per-cell N1/N2 pairs); `coverage_map.csv`
  (reason and domain spread); audit Info 4.

## Hypothesis Verdict

**SUPPORTED (CALIBRATION_DELIVERED)** — with the per-cell qualification the
hypothesis itself anticipated. The EXP-027 machinery exhibits controlled FPR
and finite MDE at realized TRAIN counts in 37/50 cells; the 13 exceptions
(12 FPR-excess, mostly marginal; 1 no-finite-MDE) are recorded exclusions,
not a substrate failure. G1 leg (ii) is satisfied for the COVERED set.

## Limitations

- **Horizon-transfer assumption** (plan caveat 1): calibration is at
  H_cal = 8 bars only. If Track D selects exits far from H≈8 — especially in
  thin 4h cells — the predeclared targeted second-horizon FPR check is
  required before the binding TEST read.
- **Secondary α = 0.01 is anti-conservative** (mean FPR 0.0225 across
  cells): consistent with independent sign flips under within-regime
  dependence. Only the primary α₀ = 0.05 operating point is classified and
  consumed by G3; do not reuse the α = 0.01 columns as if calibrated.
- **N2's dependence stress is weak in practice** (block length 1
  everywhere); the two-null agreement is therefore less informative about
  serial-dependence robustness than the design intended.
- **MDE values recorded for NOT_COVERED cells are power context only**
  (audit Info 1); the verdict column alone governs Track B admission.
- The grid endpoint binds for four cells at MDE = 128 bps; their true MDE
  may be higher, and BTCUSD-4h's is somewhere above 128 bps. Per scope, the
  grid is not extended post hoc.

## Alternative Explanations

- The 11 marginal NOT_COVERED cells are individually compatible with
  Monte-Carlo noise around a true FPR of 0.05 (at 500 draws, a true-0.05
  cell shows a point estimate > 0.05 roughly 40% of the time, and ~12/100
  cell×generator points landing in 0.052–0.07 is unremarkable). The
  predeclared rule deliberately resolves this ambiguity conservatively
  (exclude on point excess); the alternative reading — that most marginal
  cells are actually fine — would require more draws, which is an operator
  precision-only decision, not a defect.
- The small-cluster bootstrap artifact (plan caveat 3) does not explain the
  failures: every cell has ≥17 regimes per direction, and the NOT_COVERED
  set includes high-regime-count 1h cells.

## Recommended Next Steps

1. Close G1 adjudication 2 of 2 in
   `checkpoints/2026-06-11-011-per-instrument-foundation/G1-gate-review.md`
   against `coverage_map.csv` (37-cell Track B grid).
2. New scope (conditional, predeclared): targeted second-horizon FPR check
   on any Track D-selected cells whose trained exits sit far from H≈8.
3. New scope (operator option): precision-only re-run (more draws, no object
   change) on the 11 marginal NOT_COVERED cells if the reduced grid proves
   costly to Track B — this is the predeclared draw-count lever, not
   re-picking the method.
4. New scope (diagnostic, optional): per-cell attribution of the systematic
   N1 > N2 FPR offset — test whether within-regime real-return dependence
   (e.g. via a regime-block-permuted third null preserving within-regime
   structure) explains the marginal N1 excess. Informational for Track D /
   G3 power planning; does not reopen the coverage map.
5. EXP-029-analog C#/Python parity remains a separate registered Track A
   item.
