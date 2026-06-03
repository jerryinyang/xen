# EXP-007 — Pre-Execution Governance Review

**Experiment:** EXP-007 — Lenient-L5 Referee Variant (Phase 002 lever mechanism)
**Stage:** 4 (pre-execution)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

> **Scope of this verdict.** APPROVE applies to the *artifact quality* of
> `scope.md`, `analysis-plan.md`, and `code/run_experiment.py`. It is **not** a
> statement that the EXP-006 dependency is satisfied. See the manual-gate status
> immediately below.

## Manual execution gate status

```text
MANUAL EXECUTION GATE: BLOCKED — DEPENDENCY NOT MET
BLOCKING DEPENDENCY: EXP-006 (L5 threshold sweep)
REQUIRED EXP-006 ARTIFACTS (all must exist, COMPLETE, strict_reference_pass=true):
  - python/experiments/EXP-006/results/run_metadata.json   (overall_status == COMPLETE, strict_reference_pass == true)
  - python/experiments/EXP-006/results/threshold_mde_summary.csv
  - python/experiments/EXP-006/results/threshold_fpr_summary.csv
  - python/experiments/EXP-006/results/strict_reference_check.csv
  - python/experiments/EXP-006/results/threshold_draw_verdicts.csv
CURRENT STATE (2026-06-03): python/experiments/EXP-006/results/ is absent.
GATE OPENS WHEN: the artifacts above exist and pass; no re-approval of these
  EXP-007 artifacts is required, because EXP-007's own dependency gate
  (require_dependencies) enforces this at runtime and fails loudly otherwise.
```

The EXP-007 code **cannot** be run to a valid result while this gate is BLOCKED:
`require_dependencies()` raises before any measurement if the EXP-006 artifacts are
missing or not COMPLETE. This banner exists so the APPROVE status above is not
misread as "ready to run now" or as evidence that the EXP-006 frontier already
exists. Run EXP-006 to COMPLETE first, then run EXP-007.

*(Added 2026-06-03 in response to adversarial-review finding F01,
`docs/code-reviews/2026-06-03-112954-exp-007-adversarial-review.md`.)*

---

## Operator predeclaration confirmation (design §2 ⚠ gate — D-lenientL5)

D-lenientL5 (`L5_lenient = ci_lower_bps > 0`, with mandatory economically-sub-material
pass-rate reporting against the EXP-006 frontier) was **operator-confirmed on
2026-06-03 before any Phase 002 measurement existed**, recorded in the EXP-005
pre-execution review (`python/experiments/EXP-005/governance/pre-execution-review.md`,
"Operator predeclaration confirmation"). The lenient **definition is carried forward
frozen and unchanged**. `code/run_experiment.py` checks this review for the token
below before producing any measurement.

**PHASE002-PREDECLARATION-CONFIRMED** — D-lenientL5 confirmation recorded (frozen
for the phase); EXP-007 may execute.

## Dated pre-results amendment (frozen-harness clarification — §2 ⚠ compliant)

A pre-results clarification was applied to `scope.md` / `analysis-plan.md` during
this review. It is **derived solely from Phase 001 artifacts** (the frozen
`referee_calibration.gate_stack_row` and the EXP-003 draws), references **no Phase
002 result** (EXP-005/EXP-006 outcomes), is authored **before any EXP-006 or
EXP-007 result exists**, and **does not change the predeclared lenient definition,
the hypothesis H-lenient, or the methodology**. It therefore satisfies the §2 ⚠
amendment discipline (dated, pre-results, predeclared reasoning only).

**What it documents (verified against all 216,000 frozen gate-stack draws, 0
exceptions):**

1. The frozen strict L5 is `ci_lower_bps > materiality_bps` (`:1038`) and L3 is
   `ci_lower_bps > 0 ∧ ci_vs_naive_lower_bps > 0` (`:1037`). Hence the lenient leg
   `ci_lower_bps > 0` is **identically the EXP-006 `τ=0` endpoint**, and — because
   L3 already enforces `ci_lower_bps > 0` — the lenient gate equals dropping L5
   (`L1∧L2∧L3∧L4`). Empirically: `lenient ≡ drop-L5` with 0/216,000 mismatches.
2. **Why the correction was necessary (would otherwise be a Stage-4 REVISE):** the
   pre-correction Evidence-FOR required the lenient MDE to "improve **beyond** the
   EXP-006 frontier." Since the lenient point *is* the τ=0 frontier endpoint, that
   branch is **mathematically unattainable under the frozen harness** — a
   governance REVISE trigger ("criteria that are mathematically unattainable"). The
   design D-lenientL5 "distinct mechanism, not merely a smaller number" framing
   (whose prose mischaracterizes the strict leg as point-estimate-based) does not
   hold against the frozen CI-lower-bound code.
3. **What the correction did:** kept H-lenient falsifiable (structural-gain branch
   retained but explicitly flagged not-attainable-under-frozen-harness), made the
   attainable **Evidence-AGAINST** the expected resolution (lenient = τ=0 = drop-L5
   → a magnitude change, not a distinct mechanism), and made the experiment's real,
   attainable deliverable the **measurement** of lenient operating characteristics,
   the **economically sub-material pass-rate** accounting (not produced by EXP-006,
   required by D-lenientL5), and the **numerical structural-equivalence confirmation**.

> Operator note: this reframing of a predeclared success criterion is surfaced for
> review. It changes no frozen definition and is fully reversible; EXP-007 is gated
> behind its own manual execution step, so it can be overridden before it runs.

## Correctness verification performed (pre-execution, not the experiment run)

- Frozen L5 / L3 confirmed in `referee_calibration.py`; `lenient ≡ drop-L5 ≡ τ=0`
  proven on all 216,000 draws (0 mismatches); 137,039 lenient passes vs 114,665
  strict.
- Idioms validated on the real artifact (`json_decode` subset, group-by Wilson).
- Pure helper branch coverage exercised on synthetic inputs: `_lenient_verdict`
  (all six branches), `_mde_equal` (NaN/None edges), `submaterial_accounting`
  (zero-pass → `NaN`, never 0), `compute_variant_mde` statuses.
- `py_compile` + `ruff` clean; module import creates no directories.

---

## Artifact review against governance constraints

### Scope (`scope.md`)

| Check | Result |
| --- | --- |
| Single falsifiable hypothesis | PASS — H-lenient: does lenient L5 lower MDE at FPR ≤ α₀ beyond the EXP-006 frontier; expected (and predeclared) resolution FALSIFIED. |
| Concrete success/failure/inconclusive criteria | PASS (post-correction) — Evidence-AGAINST and the measurement deliverable are attainable and measurable; the unattainable structural-gain branch is transparently flagged, not hidden. |
| Boundaries (views, params, exclusions) | PASS — α grid, edge grid, sub-material definition/denominator, EXP-006 dependency, and exclusions (adoption, loss selection, L1–L4 changes, new thresholds) explicit. |
| Complexity budget | PASS — 4 tests / 4 plots / 0 modules; the structural-equivalence confirmation is a deterministic consistency check, not a 5th statistical test. |
| Holdout exclusion | PASS — post-processing of EXP-003/EXP-006 artifacts; standard loader is a documented unused fallback. |
| Real-price outcome rule | PASS — reused EXP-003 effect/CI are net-of-cost real-`Close`; sub-material uses `effect_bps < materiality_bps(domain)`; no synthetic chart prices. |

### Analysis plan (`analysis-plan.md`)

| Check | Result |
| --- | --- |
| Method justification | PASS — each step documents method, rationale, simpler-alternative, assumptions, expected output. |
| Assumptions valid for time-ordered data | PASS — non-parametric Wilson; denominators inherited from EXP-003; lenient==τ0==dropL5 equivalence is exact under the frozen harness. |
| Cross-view alignment | PASS (N/A) — no new market-data view. |
| Visualisations purposeful | PASS — 4 plots map to sub-questions (MDE comparison, FPR comparison, strict-vs-lenient TPR, sub-material heatmap). |
| Interpretation guide pre-defined | PASS — expected falsification-by-construction predeclared; structural-equivalence mismatch flagged as a reconstruction defect to investigate. |
| Budget compliance | PASS — 4/4/0. |

### Code (`code/run_experiment.py`)

| Check | Result |
| --- | --- |
| Plan compliance | PASS — implements the four plan steps + equivalence confirmation; emits the named artifacts; no out-of-scope analyses. |
| Predeclaration gate | PASS — `require_predeclaration_confirmation()` requires the token in this review before any measurement (mirrors EXP-005). |
| Dependency gate | PASS — requires EXP-001 PASS, EXP-003 COMPLETE, and EXP-006 COMPLETE with `strict_reference_pass=true`, failing loudly otherwise. |
| Holdout exclusion | PASS — only `pl.scan_csv` of EXP-003 draws + small EXP-006 CSV reads; no timebars/holdout path. |
| Look-ahead prevention | PASS (N/A) — pure post-processing of `t→t+1` EXP-003 draws. |
| Real-price discipline | PASS — net-of-cost real-`Close` effects/CIs; sub-material on `effect_bps`. |
| Frozen-harness reuse | PASS — imports `wilson_interval` / `materiality_bps_for` / `write_json` only; `referee_calibration` unchanged → no re-validation. |
| Determinism | PASS — pure deterministic transforms; no RNG. |
| Type hints / docstrings | PASS — public functions typed and documented. |
| NaN / edge handling | PASS — zero-lenient-pass → `NaN` sub-material (not 0); `_mde_equal` handles NaN/None; no-MDE / FPR-uncontrolled statuses explicit; verdict treats NaN sub-rate as non-blocking. |
| Separation of concerns | PASS — gates / load / summaries / MDE / equivalence / sub-material / frontier / plotting / orchestration / `main()` sectioned VAL-001 style. |
| No magic numbers | PASS — α0, targets, sub-material limit 0.50, τ0 multiplier named; edge grid derived from data. |
| Import side effects | PASS — verified none. |
| Progress / logging | PASS — concise INFO summary; no qualifying multi-minute Python loop (vectorized collect + group-by), so `tqdm` correctly not used. |
| Plot memory | PASS — plots consume bounded summary frames (≤ ~54 MDE/FPR cells, ≤ 27 sub-material cells); no millions-row pandas conversion. |
| Safe optimization / vectorization | PASS — variant verdicts are vectorized boolean expressions preserving sample membership, denominators, and recorded effect/CI. |
| Duplicate-source denominators | N/A — referee draws, not chart-type events. |

---

## Info notes (non-blocking)

- The headline H-lenient verdict is expected to resolve `EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN`
  (lenient = τ=0 = drop-L5) — a legitimate predeclared finding that closes the
  lever-mechanism characterization, not a run failure. Per-domain verdicts and the
  sub-material accounting are the substantive outputs.
- EXP-007 overlaps the EXP-006 τ=0 endpoint by construction; its non-redundant
  content is the sub-material pass-rate accounting (required by D-lenientL5) and
  the auditable structural-equivalence confirmation.
- `overall_status` is `COMPLETE` / `INCONCLUSIVE` (a measurement run); the
  structural-equivalence pass (`lenient == drop-L5`) is a hard correctness gate
  expected to hold (0/216,000 mismatches pre-verified).

---

## Conclusion

Scope, analysis-plan, and code satisfy all governance constraints with no Critical
or Warning issues. The one defect found at review — an unattainable structural-gain
success criterion inherited from the design's mechanism framing — was corrected via
a dated, predeclaration-safe, frozen-harness amendment that changes no frozen
definition. Operator predeclaration of D-lenientL5 is recorded. **APPROVE** (artifact
quality) — the manual execution gate is **BLOCKED** until EXP-006 completes (see the
Manual execution gate status banner above).

## Post-review remediation (2026-06-03, adversarial-review F01–F05)

The independent adversarial review
(`docs/code-reviews/2026-06-03-112954-exp-007-adversarial-review.md`) raised five
findings against the EXP-006/EXP-007 package. All five were validated and an
effective fix was applied to each (no frozen definition changed; reasoning derived
solely from Phase 001 artifacts):

- **F01** — manual-gate status made explicit (BLOCKED banner above); the APPROVE
  verdict is scoped to artifact quality only.
- **F02** — `code/run_experiment.py` now writes `lenient_draw_verdicts.csv`
  (per-draw strict / lenient / drop-L5 flags + keys + effect/CI/materiality + L1–L4)
  before summary aggregation. The Plan-compliance "emits the named artifacts" check
  now holds for all planned outputs.
- **F03** — the lenient ↔ EXP-006 `τ=0` equivalence is now confirmed **verdict-level**
  (per-draw join against EXP-006 `threshold_draw_verdicts.csv`, mismatch + unmatched
  counts folded into `structural_equivalence_pass`); the MDE-summary equality is
  retained only as a secondary check. `threshold_draw_verdicts.csv` is added to the
  required EXP-006 dependency set.
- **F04** — a dated erratum was added to the active checkpoint `design.md`
  reconciling the stale D-lenientL5 "distinct mechanism" framing with the
  frozen-harness clarification.
- **F05** — `submaterial_accounting()` now builds the full positive
  (domain, alpha, edge) grid and emits zero-lenient-pass cells with
  `lenient_pass_count = 0` and `submaterial_rate = NaN` (never dropped, never 0).

These changes touch only pre-execution artifacts; no results existed and none were
altered. Full validation rationale:
`docs/code-reviews/2026-06-03-exp-006-007-review-validation.md`.
