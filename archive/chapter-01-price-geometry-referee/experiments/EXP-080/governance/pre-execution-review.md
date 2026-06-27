# EXP-080 — Stage 4 Pre-Execution Governance Review

**Experiment:** EXP-080 — Phase 018 CF-CAPGEO-001 Substrate/Exit Readiness (HYP-001)
**Reviewed:** 2026-06-21
**Artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/domain_bars.py`, `python/src/xen/capgeo_substrates.py`
**Governing constants:** D0 `D0-predeclarations.md` (G0 PASS 2026-06-21), VAL-005 PASS,
multiplicity-registry Phase 018 batch, test-read-ledger INFR-003 active ledger.

---

## VERDICT

```text
VERDICT: APPROVE
```

**(Resolved after revision cycle 1 of 2 — see "Revision cycle 1" below.)**

### Initial verdict (revision cycle 1 issued): REVISE

```text
VERDICT: REVISE
FAILING_ARTIFACT: python/experiments/EXP-080/analysis-plan.md (and scope.md success/failure criteria)
REQUIRED_SKILL: experiment-quant-analyst
ISSUES:
- Predeclaration↔implementation inconsistency on the BINDING null-FPR halt criterion.
  The code binds SUBSTRATE_REFUTED's null-FPR leg to the ratified D9 operating floor
  (n>=120 halt-binding; n<120 recorded as regime="small_n_disclosed"), which is correct
  and consistent with binding D0 (§D9 floor n>=120; §D6 Guard (i)). But the predeclared
  artifacts still literally encode the unqualified criterion and must be reconciled to the
  ratified floor BEFORE execution, so the predeclared verdict matches what runs:
    * analysis-plan.md Step 6 (line 152-153): "CONTROLLED iff Wilson-hi <= 0.075 at every tested n"
    * analysis-plan.md Step 8 (line 173): "null-FPR Wilson-hi > 0.075 at any tested n"
    * analysis-plan.md Interpretation Guide (lines 208-209): "UNCONTROLLED at any n => SUBSTRATE_REFUTED halt"
    * scope.md Success/Failure (line 178-179): "moving-block null-FPR uncontrolled (Wilson-hi > 0.075)"
  Remediation: amend these to state the halt binds ONLY on the operating regime (n>=120),
  with n<120 recorded as disclosure per D0 §D9 (floor n>=120) + §D6 Guard (i) and the
  Phase-017 EXP-077/078 small-n percentile-bootstrap inflation finding. NO code change is
  required (the code is already correct); this is a surgical predeclaration alignment to
  remove a post-hoc-threshold appearance and a self-contradicting Stage-8 verdict criterion.
```

### Revision cycle 1 — resolution (experiment-quant-analyst, 2026-06-21): RESOLVED → APPROVE

The predeclared null-FPR halt criterion was reconciled to the ratified D0 §D9 operating
floor in both documents (no code change; the code was already correct and ratified):

- `analysis-plan.md` Step 6 expected output, Step 8 halt triggers, and the Interpretation
  Guide null-FPR clause now bind CONTROLLED/halt only on the operating regime `n ≥ 120`,
  with `n < 120` recorded as `small_n_disclosed` (citing D0 §D9, §D6 Guard (i), EXP-077/078).
- `scope.md` Per-Cell Checks Step 5 and the Evidence-AGAINST (SUBSTRATE_REFUTED) criterion
  now carry the same `n ≥ 120` operating-regime qualifier and the small-`n` disclosure.

Verified by grep: all four halt-criterion mentions across both docs now carry the operating
floor; no unqualified "any/every tested n" halt wording remains. The predeclared artifacts,
the code, and binding D0 are now mutually consistent. **No experiment code was changed.**

---

## Flagged decisions — adjudication

### Decision 1 — File resolution/loading reuse (VAL-005 resolver, not the scope's latest-glob): **RATIFIED**

Confirmed a genuine bug is avoided, not a scope change:

- Base filenames are `timebars_<symbol>_<start>_<collected>.parquet`; the `start_token`
  precedes the `collected_token` lexically. The 5-year INFR-003 files start **2021**; the
  retained pre-INFR-003 files start **2023**. A naive `sorted(glob)[-1]` orders by the full
  name (start first) and would select the **2023-start old dataset** — the wrong file.
- VAL-005's `discover_infr003_files` selects by `max(collected_token)` with the
  `INFR003_MIN_COLLECTED` floor (`run_experiment.py:224-257`) — the validated path that
  picks the 2026-06-21-collected 5-year file.
- `xen.domain_bars.build_domain_bars` is byte-verbatim to VAL-005's G1-validated function;
  `regression_check` reconciles `ours.equals(theirs)` on a shared cell and **raises before
  any substrate read** (`run_experiment.py:469-510`).
- `load_first70` reads only metadata + the first-70% prefix and never collects the holdout
  (`VAL-005 run_experiment.py:263-310`).

This is a faithful improvement consistent with the analysis-plan Step 0 binding note (which
explicitly permits importing or promoting the validated VAL-005 logic). **Ratified.**

### Decision 2 — Null-FPR halt bound to the operating regime (n>=120): **SUBSTANCE RATIFIED; predeclaration must be reconciled (REVISE above)**

- **Substance is correct.** D0 §D9 (RATIFIED, G0 PASS 2026-06-21) froze the operating floor
  at **n>=120**; §D6 Guard (i) defers to the median at effective-n<=60; Phase-017
  EXP-077/078 documented small-n percentile-bootstrap FPR inflation as a known, disclosed
  property. Binding the halt to "any tested n" would spuriously self-refute the experiment on
  this disclosed small-n inflation, contradicting binding D0 constants. The code's
  `regime="operating"` (n>=120, halt-binding) vs `"small_n_disclosed"` (n<120, recorded but
  not halt-binding) at `run_experiment.py:120,246,550-558` is the correct reading and is
  documented in-code and in `null_fpr.json` / `run_metadata.json`. The chosen test points
  `NULL_NS=(15,30,60,120,250,500,2000)` split cleanly at the floor (n=60 sits in the disclosed
  band, consistent with §D6 Guard (i)). **The interpretation is ratified.**
- **Why REVISE nonetheless.** The binding verdict criterion is a *predeclared* object. The
  scope and analysis-plan still literally encode the unqualified "at any/every tested n"
  halt, which the code (correctly) does not implement. Predeclaration integrity (file-drawer
  control; "no post-hoc thresholds") requires the predeclared documents to state the actual
  binding criterion before execution; otherwise Stage 8 would adjudicate against a criterion
  the run contradicts. The fix is a documentation reconciliation only, anchored to the
  already-ratified D0 §D9 floor — no code or re-run implication (we are pre-execution).

---

## Standard governance checks (all PASS unless noted)

| Constraint | Finding |
|---|---|
| **Registry precondition** | `CF-CAPGEO-001` REGISTERED; Phase 018 batch registers the 4 substrates as predeclared countable items; G0 PASS. EXP-080 = 0 slots / 0 counted reads (readiness/disclosure). All 48 new-dataset strata at 0/2, open. **PASS.** |
| **OOS holdout** | Only Parquet metadata + first-70% prefix loaded (`load_first70`); `build_domain_bars` fence drops any window labelled past `source_max`; null carrier built from analysis bars only. Holdout never materialized. **PASS.** |
| **Look-ahead / causality** | Entry-invariant battery asserts on-close, within-span, monotone, and detector-specific causal epochs (AVWAP anchor/armed <= entry; harami in-progress confirm <= entry) (`run_experiment.py:180-204`). Ported detectors keep streaming semantics; SUB-RANDOM lands on completed closes only. Alignment by `CloseTime` epoch, never bar index. **PASS.** |
| **Real-price / synthetic discipline** | AVWAP + all MA/STRONG-STAT gating on real domain OHLC; harami detection on HA candles is permitted because **no return/capture/MFE/MAE/expectancy/P&L is computed anywhere** in EXP-080. The single statistical test's carrier is an explicitly non-tradable, mean-centered, block-permuted domain-bar log-return machinery probe — not a substrate outcome. **PASS.** |
| **Per-stratum verdict (no masking)** | Code emits a `CellRecord` per substrate-cell (192 rows); READY/NOT_READY/COVERAGE_EXCLUDED/CONSTRUCTED_EMPTY is per cell. SUBSTRATE_REFUTED is a disjunction of predeclared *systematic* triggers (non-determinism on any cell; same invariant on >=3 instruments; operating-regime FPR), not a pooled statistic collapsing heterogeneity. Readiness experiment, 0 counted reads, no strategy estimand. **PASS.** |
| **Determinism** | Two full passes; exact frame/array equality (`entries_equal`); domain-bar `bars.equals(bars2)`; seeds (`SEED_RANDOM`, `SEED_NULL`) recorded in `run_metadata.json`. **PASS.** |
| **Method choice (no academic-finance pitfalls)** | Non-parametric moving-block bootstrap (preserves serial dependence) for the null-FPR sanity; i.i.d./normal alternatives explicitly rejected in the plan. **PASS.** |
| **Gate-threshold calibration** | D7 bracket [15,8000], drop bands 0.10/0.25, and the n>=120 floor / Wilson-hi 0.075 gate are all D0/D9-frozen and calibrated (bite-check GREEN), not magic constants. **PASS.** |
| **Complexity budget** | 1 statistical test, 4 plots, 2 new modules (`capgeo_substrates`, `domain_bars` — the latter a verbatim promotion). Within budget. **PASS.** |
| **Code conventions** | Imports→path setup→constants→dataclasses→pure computation→plotting→orchestration→`main()`; output dirs created in `main()` only; lazy scans; `tqdm` over the 192 cells and the null-FPR loop; plots built from the collected summary (no reloads); bounded per-cell memory. VAL-005 module import is side-effect-free (main-guarded) and used only for the regression-anchored resolver/loader, per the plan's allowance. **PASS** (minor: `plt.cm.get_cmap` is deprecated in newer matplotlib — Info only, non-blocking). |

---

## Routing

Route `analysis-plan.md` (and the `scope.md` Success/Failure criteria) to
**experiment-quant-analyst** to reconcile the predeclared null-FPR halt criterion with the
ratified D9 operating floor (n>=120 binding; n<120 disclosed per §D6 Guard (i) +
EXP-077/078). On return, re-review for Stage-4 APPROVE; no other artifact requires change.
