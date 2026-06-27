# Phase 003b Design Amendment B1 — Pre-Execution Review Corrections

**Amendment ID:** 2026-06-05-B1
**Authored:** 2026-06-05
**Phase:** 003b — Incremental-Unit Redesign & Recalibration (Track B follow-up)
**Status:** APPLIED — authored **before any EXP-017/018/019 results exist** (all `results/` dirs empty at authoring), so the predeclaration freeze is preserved by documenting the change before dependent results are read (same posture as Phase 003 amendment A1 §1).
**Trigger:** Adversarial pre-execution review of EXP-017–019 (findings F01–F07) against the active `design.md`, the research-pipeline governance constraints, and the EXP-013/014 substrate.

---

## 1. Scope and posture

This amendment is a **documentation reconciliation + experiment-code robustness/efficiency correction**, not a re-selection of any predeclared object. Explicitly preserved unchanged:

- The **operator-confirmed revised gate** (D-revised-legs: `L1 ∧ L3 ∧ L4′ ∧ L5`, L2 removed) and the **D-l4l5-freeze** L4′/strict-L5 forms.
- Every **threshold**: α grid, α₀, materiality, cost model, D-prec Wilson half-widths, the inherited edge grid, and the P3-D-dependence grid.
- The **D-incr-form estimator**, the **EXP-013 substrate**, and the **D-no-retune** freeze. Nothing here tunes any object toward a desired result; the only verdict-rule change (§4, F02) makes validation **stricter / more conservative**, which cannot manufacture a pass.

Because no governed estimator/CI code path is altered (the only `xen/incremental_referee.py` change is an additive, default-preserving opt-out, §7), **D-reuse does not trigger an EXP-013 re-run.** The pre-execution reviews for EXP-017/018/019 are refreshed with an addendum (§8).

---

## 2. F01 — Binding-leg semantics reconciled (L5-strict is binding; L3 is its precondition)

**Issue.** The design used "binding" for two different legs. D-revised-legs called L3 "the binding test" and H-revised-correct required EXP-017 to confirm "L3 binding," but D-l4l5-freeze (correctly) states "L5 is the binding significance-at-materiality test … L3 functions as the directional/readiness precondition." Under the frozen strict-L5 form, `L5 = (ci_lower > materiality)` with `materiality > 0` **implies** `L3 = (ci_lower > 0)` on the same marginal series, so L3 is logically redundant in the conjunction (the gate is effectively `L1 ∧ L4′ ∧ L5`). EXP-017 therefore cannot exhibit an "L3-binding" state, and EXP-018 leg-attribution can never isolate L3.

**Correction (documentation only — the gate is unchanged and stays operator-confirmed).**

- The §2 D-revised-legs row, the §3 definition (renamed *Incremental-beyond-R test (L3)*), and the §4 H-revised-correct claim are reworded so **L5 is named the operationally binding leg and L3 its directional precondition**, propagating the language the operator already confirmed in D-l4l5-freeze.
- EXP-017 scope/plan/code are reworded to match; EXP-017 already exposes all four retained legs and forbids an impossible L3-fail/L5-pass fixture, which is consistent with the nesting.

**Residual calibration risk (recorded, not fixed — D-no-retune forbids fixing it pre-emptively).** Removing L2 (which EXP-015/A1/F03 showed was the BTCUSD-driven binding leg) helps, but the D-l4l5-freeze simultaneously **tightens L5 from a point estimate to `ci_lower > materiality`**, so the *new* binding leg is a stricter L5. Whether BTCUSD can clear strict-L5 at the dependence corner is exactly what EXP-018 measures. To keep a second refutation diagnosable, EXP-018 already emits `leg_pass_rates.csv` and now `binding_corner_summary.csv` (§4, F03), which together identify the actual binding leg per cell.

---

## 3. F04 / F05 — Fixture nature and provenance stated accurately (EXP-017)

**Issue.** EXP-017 scope/plan called the fixtures "deterministic golden fixtures" with "hand-computed" verdicts, but returns are drawn from a fixed per-fixture seed and retained-leg states emerge from a 1000-resample block bootstrap (seeded, reproducible, but not closed-form). The construction is a copy of EXP-014's builder with new seeds, not a literal reuse of the EXP-014 suite as H-revised-correct states.

**Correction (documentation only).**

- "hand-computed / golden fixtures" → **"seeded-deterministic fixtures with predeclared, hand-reasoned expected leg states, verified against the fixed-seed block bootstrap"** in EXP-017 `scope.md`, `analysis-plan.md`, the code docstring, and the H-revised-correct claim.
- "EXP-014 fixture suite is reused" → **"EXP-014 fixture construction is reused/adapted and extended."** The substantive H-revised-correct requirements are met regardless: `l2_absent_former_standalone_fail` reuses EXP-014's L2-isolating parameters and asserts at run time (`legacy_l2_check`) that the legacy standalone leg would have failed, and `l3_reference_control_fail` is retained and rejects.
- The `l5_strict_materiality_fail` margin is documented: L5=False is robust (CI lower < point ≈ 0.45 < 0.5 materiality); L3=True relies on the planted edge clearing zero, with precedent in EXP-014's analogous fixture. No drift value is changed (changing one would be an unverifiable, freeze-adjacent edit).

---

## 4. F03 — Binding corner reported explicitly; corner axis clarified (EXP-018)

**Issue.** The design requires the synchronous/high-overlap/null_R corner to be "reported explicitly for every domain," but the code only embedded it in the full grid tables. Separately, the design labels the corner by *overlap*, whereas A1/F03 attributes the EXP-015 refutation to the moderate/high shared-latent-state **ρ** cells.

**Correction.** EXP-018 now extracts a dedicated `binding_corner_summary.csv` (and a `binding_corner_status` block in `run_metadata.json`) covering lag=synchronous, overlap=high, reference=null_R across **all three ρ levels**, with an `a1f03_exp015_stress` flag on the moderate/high-ρ cells, plus a console line. This is added reporting only — no new statistical test or plot, so the 4/5/1 budget is unchanged. The design D-dependence note is updated to record the ρ-axis clarification.

---

## 5. F02 — Validation rollup tightened; EXP-019 blocks instead of crashing

**Issue.** EXP-018 set `overall_status = COMPLETE` if *any* domain was SUPPORTED and none REFUTED — weaker than design §9 ("a finite portfolio-fitness MDE map across the grid" per domain). A domain left INCONCLUSIVE (non-finite MDE) could still yield COMPLETE, which then made EXP-019 raise an uncaught `RuntimeError` in `load_suite_manifest` instead of blocking.

**Correction.**

- **EXP-018:** `COMPLETE` now requires **every** in-scope domain to conclude `SUPPORTED*` (finite worst-case MDE, with or without under-powered cells). Any REFUTED domain → `REFUTED`; any INCONCLUSIVE domain → `INCONCLUSIVE`. This is strictly more conservative.
- **EXP-019:** `dependency_manifest()` now verifies a finite per-domain MDE for every in-scope domain and writes clean `BLOCKED` metadata if any is missing/non-finite, rather than crashing downstream.
- The §9 REVISED_UNIT_VALIDATED bullet records this operationalization. Under §9's existing rule, per-*cell* under-power still does not block validation when the binding cells conclude; only a whole-domain failure to produce any finite MDE does.

---

## 6. F06 — Dogfood candidate slate excludes the reference family (EXP-019)

**Issue.** EXP-019 evaluated all six EXP-009 families as candidates C regardless of which family backs the reference book R, diverging from D-dogfood-book ("candidates C are the **remaining** EXP-009 families"); the `DOGFOOD_STRATEGIES` constant was dead code.

**Correction.** The dead constant is removed. EXP-019 reads an optional `reference_family` field from the operator-provided `dogfood_reference_book_manifest.json` and excludes that family from the candidate slate (recorded in `run_metadata.json`). Absent the field, behavior is unchanged (a redundant self-comparison is harmless on the negative path). This does **not** invent the book — the book and family remain operator-provided, still hard-gated by D-dogfood-book.

---

## 7. F07 — Standalone (L2) bootstrap made opt-out for revised-only callers

**Issue.** `incremental_gate_core` ran a second 1000-resample bootstrap on the standalone (L2) series on every call, but the revised gate discards it — ~1.46M wasted bootstraps across EXP-018 (governance §1, "no unnecessary computation").

**Correction.** `incremental_gate_core` gains `compute_standalone: bool = True` (default preserves all existing callers, incl. EXP-014/EXP-017's legacy-L2 diagnostic). `revised_incremental_gate_verdict` defaults it to `False`; EXP-018 passes `False` explicitly. When skipped, `standalone_*` are returned empty/NaN. Because every bootstrap draws from its own explicitly-seeded RNG (inc uses `seed+1`, standalone `seed+2`), **the marginal/L3/L5/L1/L4 outputs are byte-for-byte identical** with or without the flag — this is an efficiency change with no effect on any revised-gate result, so D-reuse is not triggered.

---

## 8. Consequences and re-validation

| Artifact | Touched by | Re-run / re-review |
| --- | --- | --- |
| `xen/incremental_referee.py` | F07 (additive opt-out) | No EXP-013 re-run (no estimator/CI path changed; default behavior preserved). |
| EXP-017 scope/plan/code | F01, F04, F05 (wording; code docstring) | Pre-execution review refreshed (addendum). No logic change. |
| EXP-018 code | F01-diagnostic, F02, F03, F07 | Pre-execution review refreshed (addendum). |
| EXP-019 code | F02, F06, F07 | Pre-execution review refreshed (addendum). |
| `design.md` | F01, F02, F03 wording | This amendment + in-place annotations pointing here. |

**Phase outcome direction unchanged.** B1 does not alter what success means; it makes the validation bar precise and conservative and the experiments robust/diagnosable. EXP-017 → EXP-018 → EXP-019 remain gated as before; D-dogfood-book is still pending operator confirmation before EXP-019.
