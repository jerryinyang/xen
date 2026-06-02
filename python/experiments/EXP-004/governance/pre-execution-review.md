VERDICT: APPROVE

Reviewed artifacts:
- `python/experiments/EXP-004/scope.md`
- `python/experiments/EXP-004/analysis-plan.md`
- `python/experiments/EXP-004/code/run_experiment.py`
- `python/src/xen/referee_calibration.py`

Governance notes:
- Scope matches active checkpoint EXP-004 dogfood consistency anchor.
- EXP-003 MDE output is enforced before manual execution.
- Donchian(20) and MA(20,50) parameters are fixed and not tuned.
- Donchian uses prior high/low windows; MA uses data available at bar close; outcomes use next-bar real Close-to-Close returns.
- Final 30% global holdout is excluded before domain construction.
- Missing or non-finite MDE cells are classified as inconclusive rather than forced to a verdict.

Static verification:
- `python3 -m py_compile` passed for the new shared module and EXP-004 script.
- `uv run ruff check` passed for the new shared module and EXP-004 script.

---

## Revision 2026-06-02 — post-review remediation (re-reviewed: APPROVE)

Fixes from the consolidated review:

- **W2 (look-ahead/design, §9):** dogfood candidates now use the shared
  1-minute boundary timestamp (`domain_split_index`) for the train/test cut,
  consistent with EXP-003, rather than a per-domain row fraction.
- **W5/completeness:** added the planned **candidate verdict-matrix plot**
  (`candidate_verdict_matrix.png`), bringing EXP-004 to 3/3 visualisations.
- Inherits the shared-module changes (vectorized bootstrap, gross minimal
  baseline). The dependency gate remains correct: EXP-004 requires the EXP-003
  **MDE artifact to exist** (not a PASS status), so an underpowered/permissive
  EXP-003 cell still produces interpretable consistency results.

Verdict after remediation: **APPROVE**.

