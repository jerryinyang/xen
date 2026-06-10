# Analysis Plan: Experiment EXP-038 — EURUSD-4h A1-Cell TEST-Stratum Temporal-Stability Subsample Check (one-shot)

## Objective

Evaluate, exactly once, whether the EXP-034 EURUSD-4h A1 strict pass remains
temporally stable on the held-back TEST stratum (last 30% of the analysis set, by
trigger timestamp): the same registered baseline estimand (BTC exit, pyramids
included, frozen CONSERVATIVE 3.0 bps RT + 0.6 bps/day adverse-side financing),
restricted to TEST-stratum events, tested with the frozen EXP-027 regime-cluster
bootstrap. **R1 framing:** this is a dependent-subsample check, not an independent
out-of-sample confirmation (the TEST events contributed to both the D0 cell
selection and the EXP-034 pass). Binding rule (design §8.4 as amended R1.1/R1.2):
one-sided lower bound > the calibrated margin m AND the raw one-sided p survives
the **phase-level Holm family** (this cell + EXP-037's realized cells) — finally
adjudicated in the checkpoint's `G2-gate-review.md`; this run emits a provisional
flag only. Any non-pass leaves the holdout sealed. Everything upstream is reused
from EXP-034 verbatim and re-verified by hard guards.

## Data Wiring (identical to EXP-034, restricted to EURUSD-4h)

- `EXP-022/results/lifetime_observations.csv` — the EXP-028/030/034 PRIMARY event
  population (`role = event`, `reportable_event = true`, completed outcomes,
  `n_controls_finite ≥ MIN_CONTROLS`), filtered to EURUSD-4h. Expected count:
  **exactly 39** (EXP-030/034 reconciliation; drift = hard stop).
- Rebuilt domain series via `xen.referee_calibration` (`load_analysis_data` +
  `build_domain_frames`) — the same loader/fence as EXP-020/022/031/034, validated
  against `EXP-020/results/analysis_metadata.csv`. Supplies `CloseTime[start_idx]`
  (trigger close = stratum-membership key and financing entry) and
  `CloseTime[completion_idx]` (financing exit). Only the EURUSD file is needed, but
  the rebuild-vs-EXP-020-metadata check runs on whatever cells are rebuilt.
- The 1-minute EURUSD analysis slice supplies the **TRAIN/TEST boundary timestamp**
  (see Step 2). The global holdout (final 30% of 1-minute rows) is fenced inside the
  loader and never read.
- Frozen EXP-027 inference tail (`EXP-027/code/event_method.py`), pinned hash
  `e50873d12a9f68d9` — same functions and pin as EXP-030/031/034.
- Frozen constants (no re-derivation): RT_cons EURUSD = 3.0 bps; financing
  EURUSD = 0.6 bps/calendar-day, adverse-side, fractional days via
  `xen.financing.elapsed_calendar_days` (the same helper EXP-034 ran, including its
  self-check); `net_e = lifetime_bps_e − 3.0 − financing_e`.
- EXP-034 reference artifacts for reconciliation: `EXP-034/results/cell_inference.csv`
  (EURUSD-4h row) and `EXP-034/results/run_metadata.json`
  (`a1_strict_pass = true` is a hard dependency gate — without it this experiment has
  no mandate).

## Methodology

### Step 1 — Integrity guards (hard gate; all must pass before any TEST statistic)

Maps 1:1 to the five scope guards.

- **(G-hash) Frozen-tail pin:** imported inference functions hash to
  `e50873d12a9f68d9` (EXP-034 `verify_frozen_inference` verbatim). Hard stop on
  mismatch.
- **(G-count) Population reconciliation:** the rebuilt EURUSD-4h event table has
  exactly 39 rows, and `n_TRAIN + n_TEST = 39` after the partition with zero dropped
  or duplicated events (partition is a total, disjoint labeling).
- **(G-net) Per-event net reproduction:** the full-cell (TRAIN∪TEST) event-weighted
  mean of `net_e` reproduces EXP-034 `cell_inference.csv` `effect_bps` for EURUSD-4h
  to ≤ 0.01 bps — since every EXP-038 event overlaps EXP-034's cell, the cell mean
  matching at this tolerance, on an exactly-reconciled population, certifies the
  per-event net definition. Additionally, re-running the full-cell bootstrap with
  EXP-034's own seed payload (`seed_for("EXP-034", "cell", "4h", "EURUSD")`) must
  reproduce EXP-034 `ci_low/ci_high/ci_low_1s/boot_p` to ≤ 1e-6 — pinning the entire
  estimator construction, not just the point (the EXP-034 F04 pattern).
- **(G-determinism) Same-seed replay:** the TEST-stratum inference re-run with its
  own seed reproduces effect/CI/p to ≤ 1e-12 (EXP-034 `determinism_replay` pattern).
- **(G-partition) Partition persisted before outcome computation:** the TEST member
  list (event keys: instrument, domain, regime_id, direction, event_trigger_idx,
  is_pyramid_bounce, trigger CloseTime, stratum label) is written to
  `results/test_partition.csv` **before** any TEST-stratum net statistic or bootstrap
  is computed; orchestration order in the script enforces this. The R1.2 calibration
  margin is likewise persisted (`results/null_calibration.csv`) before the TEST
  bootstrap.
- **(G-no-second-read, R1.6):** if `results/test_inference.csv` already exists the
  run hard-stops before any TEST inference (the stratum has been read); if
  `results/test_partition.csv` exists from an interrupted run, the recomputed
  partition must match it byte-identically (hard stop on mismatch) — a rerun after
  a post-partition crash is then not a second read.

- **Why this method:** the experiment's only new logic is a partition; proving
  bit-compatibility with EXP-034 isolates that one difference, making the TEST read a
  clean sample restriction of an already-audited estimand.
- **Simpler alternative considered:** trust the EXP-034 code path without
  re-reconciliation — rejected; the guards are cheap and the verdict is
  holdout-gating.
- **Assumptions:** none beyond artifact integrity.
- **Expected output:** `results/reconciliation.csv` (guard rows, all PASS),
  `results/test_partition.csv`.

### Step 2 — Trigger-time TRAIN/TEST partition (the single new computation)

- **Method:** on the EURUSD 1-minute analysis slice (first 70% of the source file,
  sorted by `CloseTime`), compute `train_cutoff = int(analysis_rows × 0.7)` — the
  scope's loading pattern. Define
  `boundary_time = CloseTime of 1-minute analysis row train_cutoff − 1`
  (the last TRAIN bar's close). An event is **TEST iff its trigger close time
  (`CloseTime[start_idx]` on the rebuilt 4h domain series) > boundary_time**, else
  TRAIN. The membership key is the entry-confirmation bar — known at entry, causal,
  no look-ahead; lifetimes may extend past the boundary without affecting membership.
  Predeclared tie rule: a trigger close exactly equal to `boundary_time` is TRAIN
  (strict `>` for TEST).
- **Why this method:** matches the scope's predeclared causal membership rule
  exactly; the 1-minute-row cutoff is the same 70/30 convention used by every prior
  experiment, so the boundary is reproducible from the data alone.
- **Simpler alternative considered:** partition on domain-bar (4h) row index —
  rejected; the project convention defines splits on 1-minute rows, and a bar-index
  rule would violate the timestamp-alignment principle.
- **Assumptions:** strictly increasing `CloseTime` (data-integrity invariant,
  validated in VAL-001).
- **Expected output:** `results/test_partition.csv` (all 39 events with stratum
  labels and trigger timestamps); expected n_TEST ≈ 12 (disclosed, not enforced —
  only the 39 total is enforced).

### Step 2b — Pre-TEST synthetic-null calibration and margin (R1.2; before the TEST read)

- **Method:** calibrate the frozen bootstrap's small-n Type-I behavior at this
  cell's exact structure — no TEST outcome touched:
  1. **Structure** (entry attributes): the TEST stratum's (direction, regime_id)
     cluster sizes.
  2. **Dispersion** (TRAIN stratum only): from demeaned TRAIN-stratum `net_e`,
     method-of-moments components — `σ_w² = pooled within-cluster variance over
     clusters with ≥ 2 events` (fallback: total variance), `σ_b² = max(0,
     var(cluster means) − σ_w² × mean(1/n_c))`.
  3. **Null replicates:** R = 2000 draws of `r_i = a_c + e_i`, `a_c ~ N(0, σ_b²)`,
     `e_i ~ N(0, σ_w²)` (zero true mean) on the TEST cluster layout, each scored by
     the frozen 1000-resample bootstrap, recording `(ci_low_1s, boot_p)`.
  4. **Outputs:** measured null FPR of the uncorrected rule (`boot_p ≤ 0.05 AND
     ci_low_1s > 0`); the binding margin `m = max(0, Q95 of null ci_low_1s)`; FPR
     under the margin rule. Persisted to `results/null_calibration.csv` **before**
     the TEST bootstrap runs.
- **Why this method:** EXP-027's FPR control was measured at domain-level
  populations (4h n≈187 pooled), not ~12-event single cells; percentile bootstraps
  on few clusters undercover, and this single verdict gates holdout admissibility.
  The margin is the smallest mechanical correction restoring ≤ 5% one-sided FPR
  under the matched null without altering the frozen tail.
- **Simpler alternative considered:** caveat-only disclosure — rejected
  (unmeasured Type-I on a holdout-gating verdict is the asymmetric risk).
  TRAIN-residual resampling nulls — rejected for determinism/simplicity at this n.
- **Assumptions:** the Gaussian cluster model with TRAIN-estimated σ_b/σ_w is an
  adequate null for coverage calibration (components disclosed). The TRAIN-stratum
  dispersion read is a scope-amended, mechanical calibration input (no operator
  discretion; cannot alter the estimand or the TEST sample).
- **Expected output:** `results/null_calibration.csv` (structure, σ_b/σ_w,
  fpr_uncorrected, margin_bps, fpr_with_margin).

### Step 3 — One-shot TEST-stratum inference (frozen machinery, absolute estimand)

- **Method:** on the TEST-stratum events only, the frozen regime-cluster bootstrap
  (1000 resamples, chunked; single-instrument specialization: direction strata with
  regime clusters as resampling units — identical to EXP-034 `infer_single_cell`) on
  the event-weighted mean of `net_e`, reporting (a) the **one-sided 95% lower bound**
  (5th bootstrap percentile) — binding against the Step-2b **margin m**; (b) the
  **raw one-sided bootstrap p** `(1 + #{boot ≤ 0}) / (1 + N_BOOT)` — the
  phase-family Holm input (R1.1); (c) the two-sided 95% CI — descriptive label
  only. **Provisional rule (this run): flag iff `ci_low_1s > m AND boot_p ≤
  0.05`.** The **final binding verdict** applies the phase-level Holm family (this
  p + EXP-037's realized p's, ≤ 4 members; with 1000 resamples the p resolution
  0.001 resolves the smallest family level 0.05/4 = 0.0125) in the checkpoint's
  `G2-gate-review.md`. Verdict labels: `A1_CELL_TEST_PASS_PROVISIONAL` on the
  provisional rule; otherwise the descriptive two-sided label —
  `EVIDENCE_AGAINST` (CI_high < 0) or `INCONCLUSIVE_SPANS_ZERO` (CI spans 0),
  recorded as `A1_STRICT_PASS_TEST_CONFIRMATION_FAILED` for phase bookkeeping in
  both non-pass cases.
- **Why this method:** it is the registered estimand's frozen inference, unchanged —
  the whole point of the confirmation is that nothing but the sample changes.
- **Simpler alternative considered:** Wilcoxon signed-rank against 0 — rejected
  (assumes symmetric i.i.d. differences, ignores regime clustering, and would break
  comparability with the EXP-034 pass it confirms).
- **Assumptions:** regime clusters capture within-cell dependence (standing EXP-027
  calibration). **Small-n caveat (predeclared):** with ~12 events the bootstrap rests
  on few regime clusters; disclose `n_events`, `n_bull/n_bear`, and the number of
  distinct regime clusters in TEST alongside the verdict. Per the scope's power
  statement, `INCONCLUSIVE_SPANS_ZERO` is a likely, valid outcome — not failure.
- **Expected output:** `results/test_inference.csv` (one binding row);
  `results/run_metadata.json` with the provisional verdict,
  `g2_adjudication = "PENDING_PHASE_FAMILY_HOLM"` (never a `g2_satisfied` flag),
  frozen hash, constants, and guard outcomes.

### Step 3b — LOCO fragility diagnostic (R1.7; accompanies, never gates)

- **Method:** for each distinct TEST (direction, regime_id) cluster, drop it and
  re-run the frozen bootstrap on the remaining TEST events (deterministic seeds,
  one per drop). Disclose per drop: n remaining, effect, `ci_low_1s`; summary:
  `min ci_low_1s over drops` and `loco_all_above_margin` (does the margin-adjusted
  bound survive every single-cluster removal?). Computed in the same run as part
  of the single predeclared read; cannot alter the verdict.
- **Why this method:** at n≈12 a pass can rest on one or two regime clusters; the
  operator deciding the one-shot holdout package needs a standardized fragility
  measure attached to any pass, not an impression from the strip plot.
- **Expected output:** `results/loco_diagnostic.csv`.

### Step 4 — Transparency disclosures (descriptive, non-binding)

- **Method:** the same frozen inference run descriptively on (a) the full 39-event
  cell (this is exactly the G-net seed-replay from Step 1 — no extra computation) and
  (b) the TRAIN stratum, plus per-stratum descriptive summaries (n, gross mean,
  mean financing, net mean, holding-day quartiles). The TRAIN read is **descriptive
  transparency only** — it selects nothing, tunes nothing, and feeds nothing back
  (scope-amended TRAIN reads: partition, calibration dispersion, and these
  disclosures; this disclosure is the scope-declared comparison visual #2 and
  carries an explicit NON-BINDING label). It additionally evaluates the **R1.7
  nomination precondition**: `train_consistent = (TRAIN-stratum net point > 0)`,
  recorded in `run_metadata.json` — the operator may nominate this package for the
  holdout only if it holds. Standing seed-robustness practice (8 seeds,
  EXP-030/034 pattern) is applied to the TEST CI boundaries and disclosed in the
  same run — no re-read after the verdict.
- **Expected output:** `results/stratum_disclosure.csv`,
  `results/seed_robustness.csv`.

## Visualisations (2 / 2 budget)

1. **TEST-stratum per-event net distribution** — per-event `net_e` dots (jittered
   strip, pyramid legs marked), TEST mean with two-sided 95% CI and the one-sided
   lower bound vs the zero line, binding verdict annotated. Answers: where does the
   one-shot read land relative to zero, and is it driven by one event?
2. **Full-analysis vs TRAIN vs TEST net comparison** — three point-estimates with
   two-sided 95% CIs (full cell, TRAIN, TEST) against zero, n annotated per group,
   TRAIN/full explicitly labeled NON-BINDING. Answers: is the TEST read consistent
   with the in-sample pass it confirms, or did the stratum flip?

## Interpretation Guide (predeclared)

- **`A1_CELL_TEST_PASS_PROVISIONAL`** (`ci_low_1s > m AND boot_p ≤ 0.05`) ⇒
  forwarded to the phase-level Holm adjudication in `G2-gate-review.md`; only a
  surviving Holm-adjusted p ≤ 0.05 yields the final `A1_CELL_TEST_PASS` and makes
  the EXP-032 holdout-release checkpoint admissible for the EURUSD-4h baseline
  package — **subject to the R1.7 nomination precondition** (TRAIN-stratum net
  point > 0). The operator selects one package across any EXP-037/038 G2 passes,
  noting the two routes share nearly the same EURUSD-4h events (a joint pass is not
  independent corroboration). The ~12-event caveat and the LOCO diagnostic must
  accompany the read; the sealed holdout remains the final arbiter.
- **`EVIDENCE_AGAINST`** (two-sided CI_high < 0) ⇒ the in-sample pass inverted on
  the TEST stratum; recorded `A1_STRICT_PASS_TEST_CONFIRMATION_FAILED`; holdout sealed;
  the EURUSD-4h baseline route is closed for this phase.
- **`INCONCLUSIVE_SPANS_ZERO`** ⇒ the predeclared likely outcome at n≈12; recorded
  `A1_STRICT_PASS_TEST_CONFIRMATION_FAILED`; holdout stays sealed; **not** an
  experiment failure — the confirmation could not be made at this sample size.
- Under no outcome is any cost/financing constant revisited, any second TEST read
  taken, the partition redrawn, or any other cell promoted. The TEST verdict is
  final for this phase regardless of how close the bound sits to zero.

## Implementation Safety Constraints (for `experiment-developer`)

- **Reuse, don't rewrite:** import/replicate EXP-034's exact helpers
  (`verify_frozen_inference`, loader path, `build_event_table` filtering,
  `attach_costs_and_financing`, `infer_single_cell`) restricted to EURUSD-4h; the
  only new function is the boundary/partition step. No change to any frozen
  constant, filter, or estimator.
- **Orchestration order is load-bearing:** guards → partition written to disk →
  null calibration written to disk (Step 2b; TRAIN dispersion + TEST entry
  attributes only) → TEST inference. No TEST-stratum net statistic (including
  means in logs) may be computed before `test_partition.csv` AND
  `null_calibration.csv` are written. If `test_inference.csv` exists, hard-stop
  before inference; if a persisted partition exists, the recomputed partition must
  match it exactly (R1.6).
- Absolute bps vs a 0 baseline throughout; no percentage-of-baseline metrics; no
  near-zero denominators. Denominator = TEST event count, fixed by the persisted
  partition; any drift between the persisted partition and the analyzed set is a
  hard stop.
- Timestamp logic only (`CloseTime`); never bar-index alignment across views; the
  boundary comes from the 1-minute analysis slice, membership from the 4h trigger
  close, both as timestamps.
- Lazy Polars loading with the standard first-70% fence; no full-file collection
  before the cutoff; bounded pandas/NumPy conversion only for the 2 plots (≤ 39
  events — trivially bounded).
- Workload is small (one cell, ~5 bootstrap runs of 1000 resamples): `tqdm` only on
  the seed-robustness loop; concise logging; helpers return data, no helper-level
  prints.
- Verdict computation reads only frozen constants and Step-3 outputs; no
  result-aware branching upstream of `test_inference.csv`.
- NaN policy: any null `lifetime_bps`, unresolved timestamp, or NaT is a hard stop
  (inherited EXP-034 behavior), never silently dropped.

## Complexity Check

- Statistical test families: 1 / 1 (frozen regime-cluster bootstrap CI + one-sided
  bootstrap p, one binding cell entering the phase-family Holm; full/TRAIN runs are
  descriptive disclosures of the same family; the Step-2b calibration is
  synthetic-data verification and Step-3b LOCO is a predeclared fragility
  diagnostic of the same family — neither is a new test).
- Visualisations: 2 / 2.
- New code modules: 0 / 0 (one orchestration script reusing the EXP-034 path; the
  trigger-time partition, calibration, and LOCO routines are the only new logic).
