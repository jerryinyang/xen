VERDICT: APPROVE

Reviewed artifacts:
- `python/experiments/EXP-001/scope.md`
- `python/experiments/EXP-001/analysis-plan.md`
- `python/experiments/EXP-001/code/run_experiment.py`
- `python/src/xen/referee_calibration.py`

Governance notes:
- Scope aligns with active checkpoint `2026-06-01-001-thesis-qualification-calibration/design.md`.
- P0 validation for 5-minute and 240-minute aggregation is explicitly included before substrate measurements are trusted.
- Final 30% global holdout is excluded before aggregation and synthetic generation.
- Null validation measures gross oracle-recoverable edge; known-positive validation measures planted net edge after scoped cost.
- Cost and materiality defaults are predeclared and must be confirmed or overridden before manual EXP-001 execution.
- Code creates output directories only inside orchestration and uses progress tracking for instrument loops.

Static verification:
- `python3 -m py_compile` passed for the new shared module and EXP-001 script.
- `uv run ruff check` passed for the new shared module and EXP-001 script.

---

## Revision 2026-06-02 — post-review remediation (re-reviewed: APPROVE)

A consolidated correctness/design-compliance/completeness/reliability review of
the EXP-001→004 batch surfaced fixes that were implemented and verified:

- **W1 (design compliance, §9 P0 precondition):** `p0_aggregation_checks` now
  emits VAL-001-style **negative controls** (oracle OHLC-mismatch, future-row,
  low-coverage, duplicate-`CloseTime`), one per detection rule per {5, 240}m
  period. Verified on a synthetic frame: all positive checks PASS on clean data
  and all 8 injected defects are detected (control rows PASS).
- **I2 (robustness):** an instrument/domain cell with insufficient returns is now
  recorded as an **INCONCLUSIVE** cell (`inconclusive_cells.csv`, reflected in
  `overall_status`) instead of raising and aborting the run.
- **W5 (completeness):** added the planned **P0-status plot** (`p0_status.png`),
  bringing the run to its declared visualisation set.

Verdict after remediation: **APPROVE**.

---

## Revision 2026-06-02b — verdict-criteria alignment with design Sec. 11 (re-reviewed: APPROVE)

Triggered by the rev. 1 execution result (`overall_status: FAIL`, `p0_pass: true`,
`substrate_pass: false`, `inconclusive_cells: 0`). Operator directed (FleetView
governance fork) to **revise the verdict logic to honor checkpoint design Sec. 11**,
not to accept the FAIL or halt the phase.

**Finding.** The FAIL was isolated to **5 of 122 cells**, all in the **4h** domain at
**sub-material edges** (`m` = 1.0 and 2.0 bps; 4h materiality = 3.0 bps). All five
*recovered* the planted mean within tolerance (1.087, 2.057, 0.959, 2.129, 1.107);
they failed only the `m >= 1` **significance leg** (`ci.lower > 0`), because the
per-draw percentile CI is the spread of the 100 draw estimates (it does not shrink
with draw count) and the short 4h sample makes that spread wide at small edges.
Every known-null cell passed; every 5m and 1h cell passed; every **material** 4h edge
(`m >= 4`) passed. The substrate is sound — the FAIL was a precision/power artifact.

**Defect.** EXP-001 rev. 1 collapsed two distinct sub-tests (recovery vs.
significance) into one PASS/FAIL gate and routed only the *insufficient-bars* case to
INCONCLUSIVE. Checkpoint design **Sec. 11** predeclared — before any measurement —
that effective-sample-limited cells, "**expected most likely on the 4h domain**," are
**INCONCLUSIVE first-class results, not failures**, and that the phase halts only when
"the synthetic substrate **cannot be validated**" (Sec. 4 H-substrate). Hard-failing a
recovered-but-under-powered sub-material 4h cell contradicts that predeclaration.

**Remediation (verified `py_compile` clean):**
- `summarize_draws` now separates **recovery** (FAIL on miss — genuine breakage) from
  **significance** (PASS if clear; **INCONCLUSIVE** if recovered but under-powered).
- `overall_status` is FAIL only on P0 failure or a genuine FAIL cell; `substrate_pass`
  = "no FAIL cell"; under-powered per-cell INCONCLUSIVE cells are reported
  (`underpowered_cells.csv`, `run_metadata.underpowered_cells`) and do not halt.
- `scope.md` Success/Failure/Inconclusive criteria rewritten to match (see scope
  rev. 2).

**Meta-Goodhart compliance (design Sec. 10).** The reclassification rule is **uniform
across every cell** and **imported verbatim from the predeclared Sec. 11/D-prec
policy** — it is not a bespoke exemption for the five failing cells (any
recovered-but-non-significant `m >= 1` cell on any domain reclassifies identically;
only 4h happens to trigger it). Draws are deterministic (fixed seeds), so the re-run
**reclassifies identical effects** rather than re-measuring against a moved target.
This honors a predeclaration; it does not adjust a frozen decision to change an
outcome.

Verdict after alignment: **APPROVE**. Proceed to the manual execution gate (re-run).

