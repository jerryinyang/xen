Used `research-pipeline` references: shared pipeline config, dataset reference,
architecture reference, experiment indexes, the active checkpoint design
`docs/experiments-docs/checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md`,
the EXP-007 scope/analysis-plan/code/pre-execution governance package, and
dependency context from EXP-003, EXP-005, and EXP-006.

Content type: empirical experiment design plus result-post-processing code.
Active lenses: statistical validity, reproducibility/auditability, governance
predeclaration integrity, and dependency sequencing.

Review scope note: EXP-007 currently has `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, and `governance/pre-execution-review.md`. It has no
`results/`, `audit.md`, `results.md`, or `report.md` artifacts in this workspace,
so this is a pre-execution adversarial review. I did not run
`python/experiments/EXP-007/code/run_experiment.py`. Read-only checks confirmed
that the script compiles and that EXP-003 supports the documented
`lenient == drop-L5` equivalence on 216,000 gate-stack rows.

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "EXP-007 is approved even though its hard EXP-006 dependency is absent",
    "evidence": "EXP-007 scope requires a valid EXP-006 threshold frontier and strict-reference reproduction before interpretation (`python/experiments/EXP-007/scope.md:34`, `:63-65`), and the code fails if `python/experiments/EXP-006/results/run_metadata.json` or the threshold summaries are missing (`python/experiments/EXP-007/code/run_experiment.py:145-154`). In the current workspace, `python/experiments/EXP-006/results/` is missing, while EXP-007 governance still records `VERDICT: APPROVE` and says to proceed to the manual gate with the caveat that EXP-006 must complete first (`python/experiments/EXP-007/governance/pre-execution-review.md:9-11`, `:149`).",
    "impact": "The EXP-007 package is not runnable or interpretable from the current artifact state. A manual runner following the approval status can start EXP-007 out of sequence and immediately fail, or worse, treat the approval as evidence that the EXP-006 frontier dependency has already been satisfied.",
    "fix": "Do not advance EXP-007 to a runnable manual gate until EXP-006 has produced `run_metadata.json`, `threshold_mde_summary.csv`, `threshold_fpr_summary.csv`, and `strict_reference_check.csv` with `overall_status == COMPLETE` and `strict_reference_pass == true`. Alternatively, revise the governance verdict/status to an explicit dependency-blocked state and re-approve after EXP-006 completion."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Planned draw-level lenient verdict artifact is not written",
    "evidence": "The analysis plan Step 2 names `lenient_draw_verdicts.csv` as the expected output of lenient variant reconstruction (`python/experiments/EXP-007/analysis-plan.md:17-23`). The orchestration writes only summary/frontier/equivalence files (`python/experiments/EXP-007/code/run_experiment.py:712-717`) and never writes the reconstructed draw-level frame from `load_gate_draws()`.",
    "impact": "The main reconstruction step becomes less auditable. Reviewers cannot inspect the per-draw strict, lenient, and drop-L5 pass flags without rerunning local reconstruction logic from EXP-003, which weakens reproducibility and makes denominator or sample-membership drift harder to catch.",
    "fix": "Write `RESULTS_DIR / \"lenient_draw_verdicts.csv\"` with the draw keys, strict `passed`, `passed_lenient`, `passed_drop_l5`, `effect_bps`, `ci_lower_bps`, materiality, and the unchanged L1-L4 fields before summary aggregation. Keep it deterministic and row-count checked against the EXP-003 gate-stack subset."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "EXP-006 tau=0 equivalence is summary-level, not verdict-level",
    "evidence": "The plan requires numerical confirmation that lenient verdicts equal the EXP-006 `tau=0` rows and the L5-removed gate on the shared draws (`python/experiments/EXP-007/analysis-plan.md:33-39`, `:50-51`). The code checks `lenient == drop-L5` per EXP-003 draw, but compares EXP-006 `tau=0` only by MDE summary from `threshold_mde_summary.csv` (`python/experiments/EXP-007/code/run_experiment.py:377-413`, especially `:390-409`). No EXP-006 draw-level threshold artifact is required or compared.",
    "impact": "A defect in EXP-006 tau=0 reconstruction, sample membership, or per-draw pass flags could be missed if the final MDE happens to match. This undercuts the experiment's stated structural-equivalence deliverable, which is supposed to be an auditable verdict-level equality on shared draws.",
    "fix": "Require EXP-006's `threshold_draw_verdicts.csv` or reconstruct the EXP-006 tau=0 pass flag inside EXP-007 from the same draw keys, then compare row counts, keys, and pass flags against `passed_lenient`. Keep the MDE equality check as a secondary summary check."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Active checkpoint design still conflicts with EXP-007's corrected mechanism framing",
    "evidence": "The active design says D-lenientL5 is a structurally distinct mechanism and describes the strict leg as a point-estimate/materiality-buffer requirement (`docs/experiments-docs/checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md:36`, `:60`). EXP-007 scope says that framing does not hold under the frozen harness: lenient L5 is the EXP-006 tau=0 endpoint, equivalent to dropping L5 because L3 already requires `ci_lower_bps > 0` (`python/experiments/EXP-007/scope.md:15-20`, `:44-48`).",
    "impact": "The experiment-level correction is sensible, but the checkpoint-level source of truth remains stale. Downstream synthesis, especially EXP-011, could still describe the lenient variant as a mechanism gain instead of the zero-buffer threshold endpoint plus sub-material accounting.",
    "fix": "Add a dated erratum or amendment to the active checkpoint design that records the frozen-harness clarification and points to EXP-007's corrected interpretation. Future synthesis should cite the amended design rather than the original D-lenientL5 prose."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Zero-pass sub-material cells are documented but cannot be emitted",
    "evidence": "The analysis plan says that if a domain/alpha/edge has zero lenient passes, its sub-material rate is reported as `NaN`, not coerced to zero (`python/experiments/EXP-007/analysis-plan.md:82-87`). The implementation filters to `passed_lenient` before grouping (`python/experiments/EXP-007/code/run_experiment.py:437-448`), so zero-pass cells are omitted rather than emitted with `lenient_pass_count = 0` and `submaterial_rate = NaN`.",
    "impact": "For the current EXP-003 artifact, a read-only spot check found no zero-pass lenient positive cells across 90 domain/alpha/edge cells, so this is not expected to change the current headline. It remains a reproducibility defect for edge grids or reruns where zero-pass cells exist: missing rows can be mistaken for missing data rather than valid zero-denominator cells.",
    "fix": "Build the sub-material table from the full positive domain/alpha/edge grid, left-join lenient-pass counts, fill missing counts with zero, and explicitly emit `NaN` for the sub-material rate when `lenient_pass_count == 0`."
  }
]
```

Summary: EXP-007's core mathematical reframing is well supported by the frozen
harness, and the implementation avoids market-data and holdout access. The main
risks are not look-ahead or price-discipline issues; they are dependency
sequencing and auditability. Before relying on EXP-007, complete EXP-006, add the
missing draw-level reconstruction/equivalence artifacts, and reconcile the active
checkpoint design with the corrected frozen-harness interpretation.
