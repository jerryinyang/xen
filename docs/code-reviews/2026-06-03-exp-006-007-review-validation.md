# Validation of the EXP-006 / EXP-007 Adversarial Review

**Date:** 2026-06-03
**Reviewer artifact validated:** `docs/code-reviews/2026-06-03-112954-exp-007-adversarial-review.md`
**Scope:** Independent verification of the five adversarial-review findings (F01–F05)
against the actual EXP-006 / EXP-007 artifacts, a verdict on validity + severity, an
assessment of each recommended fix's efficacy, and implementation of an effective fix
for every valid finding.
**State at validation:** EXP-006 and EXP-007 each have `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, and a Stage-4 `pre-execution-review.md`. Neither has a
`results/` directory, an `audit.md`, a `results.md`, or a `report.md`. This is a
**pre-execution** package; no experiment was run and no results were altered. Per the
pipeline hard constraint, experiment code was **not** executed; verification used
read-only inspection, `py_compile`, `ruff`, and synthetic-input checks of the pure
transforms only.

---

## Verdict summary

| ID | Auditor severity | Validation verdict | Adjusted severity | Fix efficacy | Action |
| --- | --- | --- | --- | --- | --- |
| F01 | Major | **VALID** | **Minor** (downgraded) | Effective (lightweight variant applied) | Fixed |
| F02 | Major | **VALID** | **Moderate** | Effective | Fixed |
| F03 | Major | **VALID** | **Moderate–Major** | Effective, and *more* feasible than the auditor assumed | Fixed (option 1) |
| F04 | Major | **VALID** | **Minor–Moderate** | Effective | Fixed |
| F05 | Minor | **VALID** | **Minor** (concur) | Effective | Fixed |

All five findings are factually valid. Three severity ratings are downgraded with
reasons below; none is dismissed. An effective fix was implemented for each.

---

## F01 — EXP-007 approved while its hard EXP-006 dependency is absent

**Claim.** EXP-007's Stage-4 review records `VERDICT: APPROVE` even though
`python/experiments/EXP-006/results/` does not exist, and EXP-007 both requires that
frontier (`scope.md`) and fails without it (`code/run_experiment.py:145-154`).

**Validation: VALID (facts confirmed).** EXP-006 `results/` is genuinely absent.
EXP-007 `require_dependencies()` raises `FileNotFoundError` / `RuntimeError` if the
EXP-006 metadata/artifacts are missing or not `COMPLETE` with
`strict_reference_pass == true`. The review's verdict line is `APPROVE`.

**Severity: downgraded Major → Minor.** The auditor's "worse" scenario — a runner
treating APPROVE as evidence the dependency is satisfied — is a *misreading* risk, not
a correctness risk. The runtime gate makes an out-of-sequence run **fail loudly and
immediately**; it cannot produce a wrong or holdout-touching result. The approval text
already carried "(EXP-006 must complete first)". The residual issue is purely that the
manual-gate **status** was not explicit enough to prevent confusion — a governance
hygiene defect, not a result-integrity defect.

**Fix efficacy: effective (lightweight variant).** The auditor's first option ("do not
advance to a runnable manual gate until EXP-006 completes") and second option
("explicit dependency-blocked state, re-approve after") are both sound. The second is
the proportionate one because the artifacts themselves are genuinely sound and the
runtime gate already enforces sequencing. Re-approval is unnecessary precisely because
`require_dependencies()` re-checks at run time.

**Implemented.** `python/experiments/EXP-007/governance/pre-execution-review.md` now
carries a prominent **"MANUAL EXECUTION GATE: BLOCKED — DEPENDENCY NOT MET"** banner
listing the exact required EXP-006 artifacts and the open-condition, plus a scope note
clarifying that APPROVE applies to artifact quality only.

---

## F02 — Planned `lenient_draw_verdicts.csv` is never written

**Claim.** `analysis-plan.md` Step 2 names `lenient_draw_verdicts.csv` as an expected
output, but the orchestration writes only summary/frontier/equivalence files and never
persists the reconstructed draw-level frame.

**Validation: VALID.** Confirmed: `main()` (pre-fix) wrote `lenient_fpr_summary.csv`,
`lenient_tpr_summary.csv`, `lenient_mde_summary.csv`, `structural_equivalence_check.csv`,
`submaterial_pass_rates.csv`, `lenient_vs_frontier.csv`, and `run_metadata.json` — but
**not** `lenient_draw_verdicts.csv`. The frame exists (`load_gate_draws()` produces
`passed`, `passed_lenient`, `passed_drop_l5`, the unchanged effect/CI/legs) but was
discarded. This is a real plan-vs-code mismatch and an auditability gap; the Stage-4
review's "emits the named artifacts" check was therefore inaccurate.

**Severity: Moderate.** Purely additive; the per-draw audit trail is partially
recoverable from the equivalence check and from EXP-006's own draw artifact, so it is
not a correctness defect — but the predeclared artifact was simply missing.

**Fix efficacy: effective.** Exactly as recommended.

**Implemented.** `main()` now writes `RESULTS_DIR / "lenient_draw_verdicts.csv"` with the
draw keys, strict `passed`, `passed_lenient`, `passed_drop_l5`, `effect_bps`,
`ci_lower_bps`, `materiality_bps`, and the unchanged `L1_readiness…L4_stability`, before
summary aggregation. It is deterministic and its row count equals the EXP-003 gate-stack
subset (recorded as `gate_draw_rows`).

---

## F03 — EXP-006 `τ=0` equivalence is summary-level, not verdict-level

**Claim.** The plan promises numerical confirmation that lenient verdicts equal the
EXP-006 `τ=0` rows on the shared draws, but the code compares EXP-006 `τ=0` only by MDE
summary (`threshold_mde_summary.csv`); no EXP-006 draw-level artifact is required or
compared, so a defect in EXP-006's `τ=0` reconstruction could be missed if the final MDE
coincides.

**Validation: VALID.** Confirmed. Pre-fix `structural_equivalence_check()` did
verdict-level checking for the **internal** drop-L5 leg (`passed_lenient !=
passed_drop_l5` per draw) but compared EXP-006 `τ=0` only at the **MDE-summary** scalar
(`lenient_mde_bps` vs `threshold_mde_summary.csv` `mde_bps`). Both `scope.md` (success
criteria) and `analysis-plan.md` Step 4 explicitly promise verdict-level equality
"…equal the EXP-006 `τ=0` rows … **on the shared draws**", so the code under-delivered
against its own predeclared deliverable.

**Severity: Moderate–Major.** The experiment's named structural-equivalence deliverable
is supposed to be auditable verdict-level equality; a summary-only check is genuinely
weaker and could mask sample-membership or per-draw pass-flag drift between the two
independent reconstructions.

**Fix efficacy: effective — and more feasible than the auditor assumed.** The auditor
offered "require EXP-006's `threshold_draw_verdicts.csv` **or** reconstruct the `τ=0`
flag inside EXP-007." Important: **EXP-006 already writes `threshold_draw_verdicts.csv`**
(`EXP-006/code/run_experiment.py:514-517`) with per-draw `passed_tau` at every
multiplier, including `τ=0`. So option 1 is fully feasible against a real artifact — and
it is the *correct* choice: reconstructing `τ=0` inside EXP-007 would be tautological
(it equals `passed_lenient` by construction and would never catch an EXP-006 defect).
Only reading EXP-006's *actual* output cross-checks the two reconstructions.

**Implemented.** New `exp006_tau0_verdict_mismatch()` scans EXP-006
`threshold_draw_verdicts.csv` at `multiplier == 0`, joins it to the EXP-007 draws on the
shared draw keys `(instrument, domain, scenario, generator, edge_bps, draw, alpha)`, and
counts per-`(domain, alpha)` pass-flag mismatches **and** unmatched draws. Both are
folded into `structural_equivalence_pass`; the MDE-summary equality is retained as a
secondary check. `threshold_draw_verdicts.csv` is added to EXP-007's required EXP-006
dependency set. A synthetic-input check confirmed the join detects both a flag mismatch
and an unmatched draw.

---

## F04 — Active checkpoint design still conflicts with EXP-007's corrected framing

**Claim.** The active `design.md` (D-lenientL5, `:36`; H-lenient, `:60`) still calls the
lenient variant a "structurally distinct mechanism" and describes the strict leg as a
point-estimate/materiality-buffer test, whereas EXP-007's scope shows that framing does
not hold under the frozen harness (lenient L5 = EXP-006 `τ=0` = drop-L5). Downstream
synthesis (esp. EXP-011) could repeat the stale framing.

**Validation: VALID.** Confirmed: `design.md:36` reads "a **mechanism** change, not
merely a smaller number… structurally distinct from EXP-006's threshold-magnitude
sweep" and describes the strict leg via "the point estimate exceed *cost + per-domain
materiality buffer*"; the frozen code is CI-lower-bound-based. The experiment-level
correction lives only in EXP-007's scope, leaving the checkpoint source-of-truth stale.

**Severity: Minor–Moderate.** Documentation / source-of-truth staleness, not a code or
result defect, but it does create a real risk of EXP-011 mis-describing the lever.

**Fix efficacy: effective and predeclaration-safe.** A dated erratum that records the
clarification (derived solely from Phase 001 artifacts, citing no Phase 002 result,
authored pre-results) and leaves the predeclared lenient definition and H-lenient
untouched satisfies the §2 ⚠ amendment discipline.

**Implemented.** A "⚠ Erratum 2026-06-03" block was added to the checkpoint `design.md`
immediately after the §2 ⚠ operator-confirmation paragraph. It records both equivalences
(verified 0/216,000), states the strict leg is CI-lower-bound (not point-estimate),
keeps the lenient definition and H-lenient unchanged (structural-gain branch expected
FALSIFIED), and imposes a downstream obligation on EXP-011 to cite the erratum rather
than the original D-lenientL5 prose. The original frozen text is left intact (the
predeclaration record is preserved; the amendment is additive).

---

## F05 — Zero-pass sub-material cells are documented but cannot be emitted

**Claim.** The plan says a domain/alpha/edge with zero lenient passes reports its
sub-material rate as `NaN` (not coerced to 0), but the implementation filters to
`passed_lenient` before grouping, so zero-pass cells are omitted entirely.

**Validation: VALID.** Confirmed: pre-fix `submaterial_accounting()` filtered to
`(scenario == "positive") & passed_lenient` *before* `group_by`, so a cell with no
lenient passes produced no row at all — a missing row, not a `lenient_pass_count = 0` /
`submaterial_rate = NaN` row.

**Severity: Minor (concur with auditor).** No current-headline impact: the auditor's
read-only spot check (and the structure of the EXP-003 substrate) imply no zero-pass
lenient-positive cell exists in the current 90-cell grid. It is a reproducibility defect
for edge grids / reruns where zero-pass cells can occur, where a missing row could be
misread as missing data rather than a valid zero-denominator cell.

**Fix efficacy: effective.** Exactly as recommended.

**Implemented.** `submaterial_accounting()` now builds the full positive
`(domain, alpha, edge_bps)` grid from the positive draws, left-joins the lenient-pass and
sub-material counts, fills missing counts with 0, and emits `submaterial_rate = NaN` when
`lenient_pass_count == 0`. A synthetic-input check confirmed a zero-pass cell is emitted
with count 0 and a `NaN` rate, and that downstream consumers (`build_lenient_vs_frontier`,
the heatmap, `_lenient_verdict`) already treat a `NaN` rate as non-blocking.

---

## Files changed

- `python/experiments/EXP-007/code/run_experiment.py` — F02 (`lenient_draw_verdicts.csv`),
  F03 (verdict-level `τ=0` cross-check + new required dependency + `DRAW_KEY_COLS` /
  `EXP006_DRAW_VERDICTS` constants), F05 (full-grid sub-material accounting).
- `python/experiments/EXP-007/scope.md` — F03 (added `threshold_draw_verdicts.csv` to
  Data Requirements; documented the verdict-level cross-check and the persisted
  draw-level artifact).
- `python/experiments/EXP-007/analysis-plan.md` — F03 (Step 4 now specifies verdict-level
  `τ=0` equivalence with MDE-summary equality as secondary).
- `python/experiments/EXP-007/governance/pre-execution-review.md` — F01 (BLOCKED
  manual-gate banner; APPROVE scoped to artifact quality) + a post-review remediation
  addendum for F02–F05.
- `docs/experiments-docs/checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md`
  — F04 (dated erratum).

## Verification performed

- `py_compile` clean on the edited `EXP-007/code/run_experiment.py` (and unchanged
  `EXP-006`), `ruff check` clean.
- Synthetic-input checks of the two rewritten pure transforms: F05 emits the zero-pass
  cell with count 0 / `NaN` rate; F03 join detects both a pass-flag mismatch and an
  unmatched draw.
- No experiment code was executed; no `results/` exist or were created; the global
  holdout was never loaded or referenced.

## Residual notes

- EXP-007 remains correctly **dependency-blocked** on EXP-006 (F01 banner). The fixes do
  not unblock it; they make the gate explicit and harden the post-EXP-006 run.
- The F03 cross-check adds a read of EXP-006's ~1.5M-row `threshold_draw_verdicts.csv`,
  filtered (lazily) to the `τ=0` slice (~216k rows) and joined to the equally-sized
  EXP-007 draw set — bounded and consistent with EXP-006 already writing that file.
- Complexity budget unaffected: the verdict-level equivalence is a deterministic
  consistency check, not a 5th statistical test (consistent with the Stage-4 review's own
  categorization).
