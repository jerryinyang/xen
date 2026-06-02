VERDICT: APPROVE

Reviewed artifacts:
- `python/experiments/EXP-002/scope.md`
- `python/experiments/EXP-002/analysis-plan.md`
- `python/experiments/EXP-002/code/run_experiment.py`
- `python/src/xen/referee_calibration.py`

Governance notes:
- Scope matches active checkpoint EXP-002: golden-fixture correctness for the minimal baseline and 5-check gate-stack referees.
- EXP-001 pass metadata is enforced before manual execution.
- No raw market data is loaded, so the global holdout remains untouched.
- Gate-stack leg output is checked for all L1-L5 legs without short-circuiting.
- Fixture parameters are fixed and do not tune against results.

Static verification:
- `python3 -m py_compile` passed for the new shared module and EXP-002 script.
- `uv run ruff check` passed for the new shared module and EXP-002 script.

---

## Revision 2026-06-02 — post-review remediation (re-reviewed: APPROVE)

The consolidated review found a **blocking golden-fixture defect** that the
original syntax/lint-only check missed. It was fixed and verified by execution:

- **C1 (correctness, blocking):** the `naive_equivalent` fixture used a 2-bar
  whipsaw pattern `[+,+,-,-]` on which naive momentum is **unprofitable**
  (net ≈ −1.0 bps/bar). The minimal referee would therefore REJECT it while the
  fixture predeclared `expected_minimal="PASS"` → the fixture would report FAIL,
  forcing EXP-002 `overall_status=FAIL` and **halting the phase at the EXP-002→
  003 dependency gate**. The pattern is now a trending run-length-3 series
  `[+,+,+,-,-,-]` (gross +2.67 bps/bar): the candidate clears the gross minimal
  test and fails only gate **L3** (it ties its own naive control), which is the
  fixture's intended purpose. The predeclared verdicts were already correct and
  are unchanged.
- **W3 (design compliance, §6.1):** per operator decision, the minimal baseline
  now tests the **gross** edge (no cost gate); cost enters only via gate-stack
  leg L5.

Verification: all 5 fixtures × 2 referees (10 verdict rows) and every required
gate-leg check PASS when run through the actual referees.

Verdict after remediation: **APPROVE**.

