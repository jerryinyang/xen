# Validation of Adversarial Review — EXP-008 / EXP-009 / EXP-010

**Date:** 2026-06-03
**Validates:** `docs/code-reviews/2026-06-03-194448-exp-008-010-adversarial-review.md`
**Reviewer status verified against:** pre-execution artifacts only (none of EXP-008/009/010
has `results/`, `audit.md`, or `report.md` yet; this is a pre-execution adjudication).
**Verification basis:** read every cited `scope.md`, `analysis-plan.md`, code file, the frozen
`xen.referee_calibration` harness, the active Phase-002 `design.md`, the upstream EXP-003/EXP-004
artifacts, and the prior Stage-4 governance verdicts; ran `py_compile`, `ruff`, and targeted
pure-function checks (no experiment orchestration run, no holdout touched).

## Verdict summary

| ID | Reviewer severity | My verdict | My severity | Fix efficacy | Status |
| --- | --- | --- | --- | --- | --- |
| F01 | Major | **VALID** | **Major** (agree — structurally inverts the worst failure mode) | Effective | Fixed |
| F02 | Major | **VALID** | Major as a design defect; **modest practical magnitude** on this substrate | Effective (option A) | Fixed |
| F03 | Major | **VALID** | **Major** (plan-specified rule dropped; biases the headline read) | Effective | Fixed |
| F04 | Major | **VALID** | Moderate→Major (promised safety property missing) | Effective | Fixed |
| F05 | Major | **VALID** | Moderate (frozen-predeclaration + hard-constraint violation; within-domain impact limited) | Effective (option a: timestamp-align) | Fixed |
| F06 | Minor | **VALID** | **Minor** (agree) | Effective | Fixed |

**All six findings are valid.** No claim was rejected. My only divergence from the reviewer is on
*magnitude* for F02 and F05 (real defects, but their numeric effect on the headline verdict is
smaller than "can invert it" for this `block_length=1` substrate). I fixed all six regardless,
because all are pre-execution and cheaply correctable before the experiments run.

---

## F01 — EXP-010 suppresses FPR-only material failures when MDE is not reportable — VALID, Major

**Claim.** The frozen material-difference criterion (`scope.md:15-23`) is an **OR** of three
sub-conditions (MDE margin breached, FPR Wilson interval disjoint, FPR Wilson lower > α₀). The
implementation gated the final `material` flag on `reportable`, which requires the protocol's MDE
row `status == "PASS"` (`run_experiment.py:460-480`).

**Verification.** Confirmed, and it is worse than a generic suppression: `summarize_mde` sets
`status = "FPR_UNCONTROLLED"` precisely when `fpr > alpha` (`run_experiment.py:319-320`). So
whenever a protocol's FPR is uncontrolled — the single most important falsification signal for
H-split — its MDE status is *guaranteed* not `PASS`, hence `reportable=False`, hence
`material=False`. The worst failure mode was **structurally unreportable**. A synthetic
`compare_protocols` call with a purged-CV arm at FPR≈0.20 and MDE status `FPR_UNCONTROLLED`
returned `material=False`, domain verdict `SUPPORTED` (pre-fix).

**Severity.** Major — agree fully. This can invert the headline per-domain verdict.

**Fix implemented.** Decoupled FPR materiality from MDE reportability. FPR materiality
(`fpr_disjoint` or `fpr_uncontrolled`) is now gated only on **FPR precision** (D-prec: both single
and protocol FPR Wilson half-width ≤ 0.03), independent of MDE estimability; MDE materiality keeps
its own `mde_reportable` flag. `material = mde_material OR fpr_material`. The domain verdict is
`FALSIFIED` if any alternative protocol is material, `SUPPORTED` if at least one comparison was
assessable with usable precision and none material, else `INCONCLUSIVE`. Post-fix check: the same
FPR-uncontrolled purged-CV case now yields `material=True`, verdict `FALSIFIED`.

---

## F02 — EXP-010 pooled multi-fold train and OOS sets overlap — VALID

**Claim.** `_pooled_indices()` de-duplicated the union of every fold's train indices and every
fold's test indices, then fed those overlapping unions to block-length estimation, L1/L4, and the
OOS bootstrap (`split_protocols.py:112-119, 237-257`). The plan's own safety constraint requires
train/test disjointness (`analysis-plan.md:180-185`).

**Verification.** Confirmed. Walk-forward pooled train `[0, e_{k-1})` overlaps pooled OOS
`[warmup, n)`; purged CV pools to OOS `[0, n)` and in-sample `≈[0, n)` (every OOS row is a train row
in another fold). The overlap is real and protocol-dependent. **Notably, the Stage-4 governance
review already documented this as an accepted approximation** ("Info #1"), reasoning that the
headline FPR/MDE come from the strictly-OOS bootstrap and `block_length = 1` makes the bootstrap
i.i.d. The adversarial reviewer correctly re-raises it as a partition-cleanliness defect.

**Severity.** This is an **aggregation-artifact / partition-cleanliness** defect, **not temporal
leakage** (governance is right that no future data enters the scored bootstrap). For *this*
substrate the practical magnitude is modest: L3/L5 bind the gate (not L4), and `block_length=1`
makes the block-length contamination inert. So I regard "can invert the headline" as overstated
here — but the defect is genuine, it violates the plan's own disjointness rule, and a clean fix
also future-proofs the wrapper if `block_length > 1` ever occurs. I treat it as a Major *design*
defect with smaller *numeric* impact.

**Why the reviewer's option B is infeasible, and which fix is effective.** A "single disjoint
pooled partition" (option B) cannot work for purged CV: the test folds tile `[0, n)`, so the
disjoint in-sample complement is **empty** — there is no held-out in-sample, and it would also
degenerate walk-forward into a single 50/50 split, erasing the protocol's expanding-window
character. The methodologically correct fix is the reviewer's **option A**: evaluate the frozen
referee **per fold** (train⊥test within each fold by construction, with the purge/embargo gap) and
combine.

**Fix implemented.** `evaluate_partition_referees` now estimates each fold's block length on that
fold's own (disjoint) train, runs the neutral/vs-naive/minimal bootstraps on that fold's own test,
and combines: the effect and `effective_n` use the pooled OOS returns (each row once); the CI is
taken over the concatenation of per-fold bootstrap-mean distributions; L1 episodes are summed per
fold; L4 uses the size-weighted train mean over all fold trains and the pooled-OOS mean; reported
block length is the per-fold max. No row ever informs the block length or train mean of a fold in
which it is scored OOS. **For the single contiguous fold this reduces bit-for-bit to the frozen
`evaluate_referees`** — verified: 0 verdict mismatches and max numeric diff `0.00e+00` across both
referees and the α grid, so the reference-reproduction anchor is preserved exactly. This is a
change to a predeclared aggregation rule; because no EXP-010 result exists yet, it is recorded as a
dated amendment in `scope.md` / `analysis-plan.md` (§2 ⚠ discipline).

---

## F03 — EXP-009 MDE-location labels ignore the CI rule in the approved plan — VALID, Major

**Claim.** The plan defines `below_MDE` CI-aware (effect's CI upper bound < domain MDE;
`analysis-plan.md:91-94`, Interpretation Guide line 131). `classify_location()` took only
`effect, mde, grid_unc` and classified on the point estimate (`run_experiment.py:185-202`);
`ci_upper_below_mde` was a side field not used in the summary (`:263-275, :303-305`).

**Verification.** Confirmed. A strategy with point estimate below the MDE but a CI upper bound
crossing it was counted `below_MDE`, overstating "the untuned set sits safely below the MDE."

**Severity.** Major — agree. The classification feeds the headline descriptive read and the
`effect_distribution_summary.csv` counts; the plan explicitly specified CI-awareness and the code
dropped it.

**Fix implemented.** `classify_location` now takes `ci_upper`. Precedence: `at_or_above_MDE` if
`effect ≥ mde`; `near_MDE` if within grid uncertainty; `below_MDE` only if `ci_upper < mde`
(confidently below); otherwise `near_MDE` (point below but CI crosses — the explicit
uncertainty band). The call site threads `verdict["ci_upper_bps"]`, so the CI-aware label flows
into the distribution summary and plots. Verified on the four representative cases.

---

## F04 — EXP-009 dependency gate does not enforce required upstream validity — VALID

**Claim.** Scope requires EXP-003 `COMPLETE` with finite gate-stack MDE rows **and** EXP-004
SUPPORTED (`scope.md:63-66`); the plan promised the MDE is "asserted finite ... fails loudly"
(`analysis-plan.md:15-23`). The code only checked EXP-004 file existence and never asserted finite
MDE rows (`run_experiment.py:112-156`).

**Verification.** Confirmed. EXP-004 status was recorded but not enforced; `load_mde_map` set
missing MDEs to `nan`, which `classify_location` silently turned into `no_mde`. The scope
predeclares missing/non-finite MDE as **Evidence AGAINST**, so a silent `no_mde` path with
`overall_status = COMPLETE` contradicts the predeclaration. On the current artifacts the gate would
pass anyway (EXP-004 `overall_status = "PASS"`, EXP-003 gate-stack α₀ MDE = 1/4/12 bps finite), so
the bug is a missing safety property rather than a present miscalculation.

**Severity.** Moderate→Major — a promised fail-loud guarantee was absent.

**Fix implemented.** `require_dependencies` now raises unless EXP-004 `overall_status == "PASS"`
(the accepted success status in the EXP-004 metadata, i.e. the H-dogfood SUPPORTED anchor).
`load_mde_map` now asserts a finite gate-stack α₀ MDE row exists for every required domain
(5m/1h/4h) and raises an explicit dependency-failure (Evidence AGAINST) otherwise.

---

## F05 — EXP-010 split-boundary spec conflicts with timestamp discipline — VALID

**Claim.** Design §7 (`design.md:109`) and the EXP-010 scope (`scope.md:42-45`) require shared split
boundaries as canonical `CloseTime` timestamps, never per-timeframe row fractions. The code used
per-domain row fractions: `int(n * warmup_fraction)` and `np.linspace(0, n, k+1)`
(`split_protocols.py:66-68, 85`).

**Verification.** Confirmed. The single-split arm was timestamp-mapped (`domain_split_index`), but
walk-forward and purged-CV fold boundaries were per-timeframe row fractions of each domain's `n`, so
the 5m/1h/4h alternative folds spanned different wall-clock windows — a frozen-predeclaration and
hard-constraint violation ("never use bar indices for temporal alignment across data views").

**Severity.** Moderate. It violates a frozen predeclaration and a programme hard constraint, but
because H-split compares protocol-vs-single *within* each domain, the cross-domain misalignment's
effect on the per-domain verdict is limited. I fixed it properly rather than amending the rule away,
consistent with the timestamp-over-bar-count principle.

**Fix implemented.** Fold boundaries are now computed as fractions of the **canonical 1-minute
analysis base** (the same reference from which the mandated 70/30 boundary is derived), converted to
timestamps, and mapped into each domain by counting domain return rows at or before each boundary
timestamp (identical mechanism to `domain_split_index`). Verified: a shared boundary timestamp maps
to proportional row indices across a fine and a 5×-coarse domain, and CV tiling is exactly `[0, n)`.

---

## F06 — EXP-010 does not implement the planned bounded/streamed output — VALID, Minor

**Claim.** Scope/plan require `protocol_draw_verdicts.csv` bounded/streamed and forbid accumulating
all verdict rows in memory (`scope.md:168-175`, `analysis-plan.md:192-195`). The code appended every
worker result into one list and wrote it at the end (`run_experiment.py:243-255, 702-703`).

**Verification.** Confirmed. The full list (~5.9×10⁵ rows at the fixed budget — manageable but
against the plan) was held in memory and the summaries consumed it.

**Severity.** Minor — agree.

**Fix implemented.** Verdict rows are streamed to `protocol_draw_verdicts.csv` via an ordered
`imap` + `csv.DictWriter` (deterministic row order, fixed schema), and folded into bounded FPR/TPR
pass-count cells (≈540 cells) as they are produced. The FPR/TPR/MDE summaries, reference-reproduction
check, and material comparison are all derived from those bounded accumulators, so the full verdict
list is never materialized. Verified end-to-end on a small synthetic set: streamed row count,
header schema, and accumulator counts reconcile with the streamed CSV.

---

## EXP-008

No finding was raised against EXP-008, and I concur: its scope/plan/code are a holdout-safe,
result-level reprocessing of frozen EXP-003 artifacts with the H-pool margin frozen pre-results, no
new modules, and Wilson/grid-MDE estimators reused unchanged. Nothing in the validation of
EXP-009/010 surfaced a contradicting issue in EXP-008.

---

## Disposition

All six fixes are implemented in
`python/experiments/EXP-009/code/run_experiment.py` and
`python/experiments/EXP-010/code/{run_experiment.py,split_protocols.py}`. `py_compile` and `ruff`
pass; targeted pure-function checks pass (notably bit-for-bit K=1 equivalence for the F02 fix). All
three experiments remain **pre-execution** (no results existed), so these are predeclaration-stage
corrections; the F02 aggregation change is recorded as a dated amendment. The experiments should now
proceed through the manual execution gate and Stage-5 audit.
