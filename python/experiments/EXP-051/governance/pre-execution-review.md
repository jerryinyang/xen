# EXP-051 Pre-Execution Governance Review

**Stage 4 (consolidated pre-execution governance).** Artifacts reviewed:
`scope.md`, `analysis-plan.md`, `code/run_experiment.py`, new module
`python/src/xen/strong_move.py`. Reviewed against `governance-constraints.md`,
`_pipeline-config.md` (programme principles, OOS rules), and the active checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture/design.md` + `D0-predeclarations.md`.

---

## Phase alignment (design.md §6, registry HYP-004)

- EXP-051 = **HYP-004**: "do `/STRONG-STAT` and `/STRONG-HA` identify materially
  different move populations, cross-cell consistent? Mechanical 'materially
  different' threshold **[D0]**." Scope/plan/code match exactly. ✓
- Characterization: **0 candidate slots, 0 TEST reads, gross, TRAIN-only**, 99 cells
  (EXP-048 READY ∪ READY_FLAGGED; 3 COVERAGE_EXCLUDED dropped). ✓
- Registry variants `CF-HA-HARAMI-001/STRONG-STAT`, `/STRONG-HA` are registered
  (Phase 014 batch); no slot consumed by characterization. ✓
- 014-A selects/freezes no parameter or branch; experiment emits the P10/P11 readout
  and does **not** self-adjudicate G1. ✓

## Core constraints

| Constraint | Verdict | Evidence |
| --- | --- | --- |
| Simplicity / justified complexity | PASS | P10 is a deterministic point criterion; the single inferential method (MBB bootstrap CI on ρ) is explicitly **non-binding** disclosed support. Simpler-alternative (iid bootstrap, rank test) documented and rejected with reason. |
| No academic-finance pitfalls | PASS | Non-parametric throughout (medians, percentiles, MAD, block bootstrap). No normality/stationarity/iid assumptions; block bootstrap explicitly honours serial dependence. |
| Single hypothesis / scoping | PASS | One question (materially-different move populations). Two filters + two HA mappings + two STAT forms are **predeclared OAT** with a single *binding* form each (p75; same-direction) and the rest **disclosed**; "no post-result selection" stated (P7). Not compound testing. |
| Concrete criteria | PASS | `ρ ≥ 1.5 ∧ f ∈ [0.10,0.50] ∧ n_defined ≥ 30` (P10); `≥5 cells/≥3 instruments` (P11). Mathematically attainable (smoke: ρ=1.77, f=0.27). |
| Complexity budget | PASS | 1 statistical test (MBB CI), 4 plots, 1 new module — counted in code: `mbb_ci_rho`, four `plot_*` calls in `make_plots`, `strong_move.py`. Frozen modules reused unedited. |
| OOS holdout | PASS | F01 prefix `train_rows=int(int(total*0.7)*0.7)`, `scan_parquet(...).slice(0, train_rows)`; full file never sorted/collected; TEST + final-30% never read; every emitted timestamp fenced `≤ train_end_ts` (`inv_fence`). |
| Look-ahead prevention | PASS | Filter *decisions* causal: `/STRONG-STAT` trailing window strictly prior (`mags[max(0,i-window):i]`); `/STRONG-HA` qualify uses `body.shift(1).rolling_median` + own bar. ZigZag generator frozen/sequential. Completed-move *magnitude* uses the terminal pivot — declared **non-tradable descriptive completed-move allowance** (same carve-out governance approved in EXP-050); no signal/capture/P&L consumes it. |
| Real-price / synthetic discipline | PASS | Magnitudes = real `EndPrice/StartPrice`; HA candles used for `/STRONG-HA` run detection and harami detection **only**; overlap signal price = real `RealClose`. No HA price enters any metric (explicit in scope, plan, code, and `run_metadata`). |
| Timestamp alignment | PASS | All alignment by `CloseTime`/epoch; run→move and harami→move by timestamp interval (`searchsorted` / `assign_to_moves` forward as-of), never bar index. |
| Zero-baseline / NaN | PASS | `n_retained=0 ⇒ ρ=null, f=0` (not material, never 0/0); `n_defined<30 ⇒ NOT_REPORTABLE_BY_POWER`; bootstrap zero-retained resamples → `ρ*=NaN` dropped with disclosed count; ρ denominator is the strictly-positive unfiltered median (not a zero baseline; no percentage-over-zero). |
| Safe optimization / vectorization | PASS | ZigZag state machine untouched; `/STRONG-STAT` variable-window quantile kept a bounded sequential loop; `/STRONG-HA` run scan vectorised via cumsum (causally equivalent: window all-qualify + `|Σdir|==run_len`); run→move searchsorted on a completed segmentation. No sample-membership/denominator/ordering change. |
| Determinism | PASS | Two-pass `core1==core2` per cell (incl. bootstrap CI); fixed `BASE_SEED` with per-(cell,binding-form) `SeedSequence` spawn; type-7 quantile, raw MAD, B/L pinned. Smoke confirmed determinism True with CI present. |

## Code-specific (governance §Code) — PASS

Plan-compliant; holdout-excluded; look-ahead-safe; real-price; timestamp-aligned;
typed public functions with docstrings; explicit NaN/empty/zero-division handling;
analysis / plotting / orchestration separated; thresholds are documented D0 constants
(no magic numbers); lazy Polars with column projection; VAL-001-style sectioning; **no
import-time side effects** (dirs created only in `run()`; verified); concise logging +
`tqdm` outer loop; plots built from the bounded per-cell summary (no reload); frozen
generators called unedited and deterministically. `py_compile` OK, no >100-char lines,
`ruff` clean. Module + synthetic end-to-end smoke pass (no real-data / holdout contact):
determinism True, all four invariants 0, binding-only CI/overlap, correct long-frame
expansion.

## Analysis-plan (governance §Analysis Plan) — PASS

Each method has "why this method" + "simpler alternative considered" + assumptions;
cross-view alignment by timestamp specified; 4 purposeful plots; pre-registered
interpretation guide incl. the `ρ`-leg vs `f`-leg failure decomposition and the
"delivery, not materiality" verdict rule; budget compliant.

## Notes (Info only — no action required)

- The `/STRONG-STAT` trailing window includes any (vanishingly rare) degenerate
  zero-magnitude prior confirmed moves, faithful to "trailing confirmed moves";
  degenerate moves are excluded from the population and disclosed.
- `/STRONG-STAT` and `/STRONG-HA` carry slightly different per-cell denominators
  (different warmup); each `n_defined` is reported separately — correct discipline,
  disclosed in scope/plan/metadata.

---

## Disposition of pre-execution audit findings (2026-06-15)

A pre-execution code-review (auditor) raised F01–F07. Disposition:

- **F01 (Critical — "no results produced"):** Not a defect — it is the expected
  pipeline state. EXP-051 sits at the manual execution gate; the pipeline cannot
  execute experiment code (hard constraint). The operator runs it; Stage 5 (audit of
  *results*) follows. No action in code.
- **F02 (Major — exact float equality):** Premise rejected on inspection of
  `heiken_ashi_generator.py:49-50` — `ha_low = min(real_low, ha_open, ha_close)` and
  `ha_high = max(...)` return an operand **verbatim** (no arithmetic, no rounding), so
  `HALow == HAOpen` is exact when there is no lower wick. A `1e-10` tolerance would be
  an unjustified magic number and could admit genuine micro-wicks. **Kept exact
  equality**; addressed the "blind monitor" sub-concern by adding a *non-tautological*
  HA generator-consistency invariant (`HALow/HAHigh` reproduce `min/max` of the real
  components) to `inv_ha_selfconsistent`.
- **F03 (Major — doc inconsistency):** **Fixed** `analysis-plan.md` §"Defined-decision
  set" to reference the 8th HA bar / `ha_run_warmup_end_time` run-completion boundary,
  consistent with the scope and code.
- **F04 (Minor — bootstrap envelope):** Bounded by a pre-execution microbench: worst
  plausible cell (pessimistic n=74k) ≈ 53 s for both binding forms × 2 determinism
  passes; real cells ≤ ~30k moves (~24 s). Total bootstrap stays single-digit minutes.
  `B=10000` retained per the approved plan; communicated as a schedule note. No change.
- **F05 (Minor — hard-fail vs sort):** Fix rejected — sorting the F01 prefix would
  change TRAIN-prefix membership and corrupt the holdout boundary (the established
  EXP-043/048/050 convention). The loud hard-fail is intentional; **added a clarifying
  comment** documenting the deliberate divergence from the generic sort-before-slice loader.
- **F06 (Minor — `retained ⊆ defined` not independently checked):** **Added**, correctly
  conditioned: STAT `retained ⊆ stat_defined` (provably 0) folded into
  `inv_filter_wellformed`; HA `retained(non-degenerate) ⊆ ha_defined` (provably 0) folded
  into `inv_ha_selfconsistent`. The naive unconditioned check would false-positive on
  legitimate degenerate-span runs; the intentional `& defined` masking is now commented.
- **F07 (Minor — array-length validation):** **Added** a length-consistency guard at the
  top of `_form_stats` (verified it raises on mismatch).

All code/doc changes re-verified: `py_compile` OK, `ruff` clean, ≤100-char lines,
synthetic smoke determinism True with all four invariants 0 and the new length-guard firing.
None alter the approved methodology, denominators, temporal semantics, or budget.

VERDICT: APPROVE (unchanged; pre-execution audit findings dispositioned above)
