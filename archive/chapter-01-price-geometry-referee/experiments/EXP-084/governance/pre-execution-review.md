# EXP-084 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-084 — AVWAP-4h Portfolio Confirmation Read of the Net-Surviving Capture Geometry
(CF-CAPGEO-001 Phase 018 / HYP-004b)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Reference:** `research-pipeline/references/governance-constraints.md`; checkpoint
`2026-06-20-018-capgeo-exit-geometry` (`D0-amendment-003`, D0-predeclarations §D4/§D5); signal registry
(`multiplicity-registry.md`, `test-read-ledger.md`, `candidate-families/cf-capgeo-001.md`).
**Date:** 2026-06-22

---

## Checks that PASS

| Constraint | Finding |
|---|---|
| **Holdout sealed** | `val005.load_first70` slices `analysis_rows = int(total*0.7)` and never materializes the final 30%. The WF series is `li.frame` (the analysis set); the frozen schedule tests [50%,100%] of *that* series = [35%,70%] of the file. No code path builds, slices, or folds the holdout. `holdout_untouched: true` asserted. ✓ |
| **Temporal alignment** | Pooling is by event close-time (`_pool` → `np.lexsort((iv, ct))`, primary close-time, deterministic tie-break on instrument order). No bar-index alignment across instruments. ✓ |
| **Real-price discipline** | Net returns are ATR-unit, built from `rx._real_ohlc(bars)`; no HA/Renko synthetic prices anywhere. ✓ |
| **Per-stratum doctrine** | The binding verdict is the explicit **portfolio** unit (`binding=true, unit="portfolio"`); per-stratum (3) and per-arm (11) reads are emitted `binding=false` disclosure. This is the operator-ratified portfolio-aggregate design, not a collapsed cross-stratum `.all()` — consistent with the EXP-076 C1 precedent. ✓ |
| **Registry / ledger precondition** | `CF-CAPGEO-001` is `REGISTERED`/SCREENING; the EXP-084 row in `multiplicity-registry.md` is `OPENED — portfolio read` (D0-amendment-003), no new countable item. `test-read-ledger.md`: the 3 strata (NZDUSD/USDCAD/USTEC-4h) are 0/2 and the read is entered as a **disclosure** (portfolio-aggregate rule) — caps preserved. Scope states the 0/2 tally. ✓ |
| **Provenance / hash-pin** | EXP-083 valid-set sha `fa4035f3…` asserted; EXP-085 cost constants carried verbatim; basket+rule hash-pinned before any OOS fold (D4.1); 6 frozen-module hashes + `wf` recorded. ✓ |
| **Frozen constants justified** | `S2_FLOOR=120`, `K_tail=3.0`, `τ_tail=0.06`, `δ=0.40`, WF schedule (0.50/0.10/5/30) are frozen D4/D5 constants; `m_margin` is null-calibrated (data-derived), not a magic threshold. ✓ |
| **Complexity budget** | 3 method families / 4 plots / 0 new modules (reuses `xen.wf`, `xen.capgeo_screen`, `xen.capgeo_cost`). Within budget. ✓ |
| **Code conventions** | Imports→path→constants→helpers→pure compute→plotting→orchestration→`main()`; `matplotlib.use("Agg")` and no dir creation at import (mkdir in `main`); `tqdm` over the basket; plotting from the bounded payload; determinism via fixed seeds + two-pass fingerprint. Module call signatures verified against source. ✓ |

---

## Finding requiring revision

### C1 (verdict-material) — an *unadjudicable* S2 is collapsed into a binding `NOT_CONFIRM`

**Location:** `code/run_experiment.py` — `run_once` lines 462/470–471 and `verdict_logic` lines 277–287.

```python
s2_ok_floor = n_train >= S2_FLOOR            # 120
...
s2_pass = bool(s2_raw and s2_ok_floor)       # floor-not-met  ->  s2_pass = False
...
verdict = verdict_logic(..., s1_pass, s2_pass, n_oos, subfloor_all)
```

When the pooled WF initial-train count `n_train < S2_FLOOR`, the code sets `s2_pass = False` and feeds that
into the G-018 conjunction. With a decisive positive WF expectancy (`exp_lo > m`, power adequate, CI not
spanning zero), `verdict_logic` then returns **`NOT_CONFIRM`** — i.e. it reports a *binding S2 failure* for a
leg that was never adjudicated.

This contradicts the predeclared design on two counts:

1. **Plan/amendment directive.** `analysis-plan.md` Step 3 (l.76) and Risk 3 (l.210–211), and
   `D0-amendment-003` §1.1/§5, require that if the floor is not met **"S2 reverts to deferred + disclosed …
   the key advance is lost → flag, do not fake it."** Emitting a binding `NOT_CONFIRM` premised on the S2 leg
   *is* faking the adjudication outcome (a non-pass reported as a pass/fail decision).
2. **Scope's own verdict definitions.** `scope.md` defines `NOT_CONFIRM` as "fails ≥1 binding leg **with
   adequate power**." An unadjudicable S2 (n below its operating floor) has, by definition, *inadequate*
   power — so the floor-fail case fits **none** of the three pre-registered outcomes (`CONFIRM` /
   `NOT_CONFIRM` / `INCONCLUSIVE_SPANS_ZERO`, the last keyed to the expectancy CI, not S2). The code silently
   defaults this unhandled state to `NOT_CONFIRM`.

**Why this is live, not a remote corner case.** EXP-085 reports per-cell TRAIN-sub-split (first-49%-of-file)
n=44–78 for the three basket cells → pooled ≈ 168 on that region. The S2 region here is the WF
initial-train [0, 50%] of the **full** analysis set (first 70% of file); scaling ≈ 168 × (70/49) ≈ 240 full,
× 0.50 ≈ **~120 — at the floor.** The plan itself expects only ≈140–165. The verdict can therefore plausibly
hinge on this branch.

**Required fix (route to `experiment-developer`).** When `s2_floor_ok` is False, do **not** emit a binding
`NOT_CONFIRM` premised on S2. Preferred minimal fix that stays inside the pre-registration: treat
S2-floor-not-met as a **process-level HALT** (surface to the operator — the scope already reserves a HALT
category for "the key advance is lost"), rather than auto-emitting a verdict on an unadjudicable leg. Keep
`s2_floor_ok` and the S2 diagnostics in the outputs. *Alternative* (requires a scope/plan amendment, operator
ratification): add a distinct pre-registered `INCONCLUSIVE_S2_DEFERRED` outcome and branch the verdict to it.
Either way the non-confirmation must not be reported as a binding S2 *failure*.

---

## Info (non-blocking — do not require a revision cycle, but fold into the C1 fix if touching the file)

- **I1.** `one_sided_lo` is imported (l.49–54) but unused in EXP-084 — remove the dead import.
- **I2.** `run_once` binds `rng = np.random.default_rng([SEED_BOOT_084, 1])` (l.447) but every downstream
  computation re-seeds its own generator; the top-level `rng` appears unused. Harmless for determinism (all
  paths are independently seeded), but remove or use it to avoid reader confusion.

---

### Resolution — REVISE cycle 1 (experiment-developer, 2026-06-22)

C1 fixed: `run_once` now raises a **process-level HALT** when `n_train < S2_FLOOR` (immediately after the floor
check, before any WF aggregate or binding verdict), routing the unadjudicable-S2 case to the operator —
"deferred+disclosed", never a binding `NOT_CONFIRM`. The fix stays inside the three pre-registered outcomes
(no unratified verdict label). I1/I2 cleared (unused `one_sided_lo` import and unused `run_once` `rng`
removed). Byte-compiles clean. Frozen constants, seeds, cost model, reconciliation tolerances, WF schedule,
holdout-exclusion path, two-pass determinism, and output schema all unchanged. Re-review confirms all
constraints satisfied.

```text
VERDICT: APPROVE
```
