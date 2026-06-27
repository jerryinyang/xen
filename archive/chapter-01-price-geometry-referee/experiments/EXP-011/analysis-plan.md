# Analysis Plan: Experiment EXP-011

## Objective

EXP-011 is the **exploratory synthesis** of Phase 002. Restated question (scope §"Question"): given three loss functions **predeclared in full before any operating point is read**, which per-domain operating point on the frozen gate stack's L5 stringency lever (the EXP-006 threshold `τ`-frontier) does each loss select for 5m / 1h / 4h, and is that selection **robust** across the three? The deliverable is a per-domain **recommended** operating point (headline = primary Loss A), a **cross-loss consistency verdict** (ROBUST / LOSS-SENSITIVE), and a **conditional adoption rule** for Phase 003. EXP-011 recommends; it does not adopt (D-posture). No SUPPORTED/REFUTED verdict — the verdict object is a recommendation.

All computation is **deterministic post-processing of frozen result-level artifacts**. No market data is loaded; no holdout is touched; no new draws are generated; no referee is re-run. The loss form and every coefficient are frozen by `scope.md` and must not be tuned to any observed value.

---

## Methodology

### Step 1: Load and gate frozen inputs (dependency + precision gates)

- **Method**: Lazy/eager Polars reads of the result-level CSV/JSON artifacts listed in `scope.md` §"Data Requirements". Before any value is consumed, assert each dependency's completion token from its `run_metadata.json`: EXP-003 `overall_status == "COMPLETE"`; EXP-006 `overall_status == "COMPLETE"` **and** `strict_reference_pass == true`; EXP-007 `overall_status == "COMPLETE"` **and** `structural_equivalence_pass == true`; EXP-008/009/010/005 `overall_status == "COMPLETE"`. A missing/failed dependency that feeds a domain makes that domain **Inconclusive** (scope §"Success/Failure/Inconclusive"), never silently skipped.
- **Precision gate (carried-forward D-prec)**: a per-`τ` input cell is **reportable** only if its `FPR` Wilson half-width `≤ 0.03` (EXP-006 `threshold_fpr_summary.csv`) and, where a TPR is used, its TPR Wilson half-width `≤ 0.05` (EXP-006 `threshold_tpr_summary.csv`). Cells failing precision are flagged `under_powered=true` and excluded from a forced recommendation; a domain with no reportable operating point is Inconclusive.
- **Why this method**: the upstream experiments already produced Wilson intervals and grid-defined MDEs under the frozen harness; re-deriving them would duplicate frozen work and risk drift. Gating on the published tokens + half-widths is the simplest sufficient guard.
- **Simpler alternative considered**: trusting the summary CSVs without a token/precision gate — rejected: it would let an incomplete or imprecise dependency silently produce a fabricated recommendation, violating the scope's Inconclusive discipline.
- **Assumptions**: the upstream artifacts are the frozen, audited (lightweight-confirmed 2026-06-04) outputs; their `CloseTime`-ordered first-70% provenance is inherited, not re-checked here. No distributional assumption (Wilson intervals are non-parametric).
- **Expected output**: validated in-memory tables — `mde[d,τ]`, `fpr[d,τ]` (+ `fpr_wilson_upper`), `tpr[d,τ,e]` (+ half-width) at α₀=0.05 (α grid retained for context columns only); a `dependency_gate` record; per-cell `reportable` flags.

### Step 2: Build the per-(domain, τ) decision table

- **Method**: Assemble one row per `(domain, τ-multiplier)` at α₀=0.05 over the frozen frontier `τ ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0}`, columns: `mde_bps`, `fpr`, `fpr_wilson_upper`, `materiality_bps(domain)` (5m 0.5 / 1h 1.5 / 4h 3.0), and `sub_rate` (from Steps 3). Mark `τ=1.0` as `strict_reference`, `τ=0.0` as `lenient_endpoint`.
- **Why this method**: the loss read operates on exactly these per-`τ` quantities; a single tidy table makes every loss a pure function of one frame.
- **Simpler alternative considered**: evaluating losses directly off the raw summary CSVs — rejected: a consolidated table makes the predeclared inputs auditable and prevents accidental use of a non-α₀ row.
- **Assumptions**: the `τ`-frontier and α₀ are frozen decision objects (scope); MDE is grid-quantised with the published grid uncertainty.
- **Expected output**: `decision_table.csv` (21 rows: 3 domains × 7 τ) — the spine of the experiment.

### Step 3: Sub-material pass-rate `sub(d, τ)` at each τ's operating MDE edge

The sub-material rate is the **economically binding** term (scope §"Suggested Direction"). Definition is **identical to EXP-007**: `sub(d, τ)` = among **positive-scenario** draws at the operating edge `e* = MDE(d, τ)` that **pass the gate at τ**, the fraction whose **net point estimate `effect_bps < materiality_bps(d)`**.

- **τ = 0 (direct read)**: take `sub(d, 0)` from EXP-007 `submaterial_pass_rates.csv` (row `edge_bps == MDE(d,0)`), cross-checked against `lenient_vs_frontier.csv` `submaterial_rate_at_lenient_mde`. (Published: 5m 0.4965, 1h 0.0547, 4h 0.0 at α₀.)
- **τ > 0 (bounded deterministic reconstruction)**:
  1. From EXP-006 `threshold_draw_verdicts.csv` (1.512 M rows) lazily project only `[instrument, domain, scenario, generator, edge_bps, draw, alpha, multiplier, passed_tau]`, filter `scenario == "positive"` and `alpha == 0.05`. (`passed_tau` is the **full gate-stack** pass with L5 swept to τ — confirmed: the frozen FPR/TPR/MDE summaries aggregate exactly this column.)
  2. From EXP-003 `draw_verdicts.csv` (432 k rows, 136 MB) lazily project only `[instrument, domain, scenario, generator, edge_bps, draw, alpha, referee, effect_bps]`, filter `referee == "gate_stack"`, `scenario == "positive"`, `alpha == 0.05`. `effect_bps` is the **net (cost-applied) point estimate** and is **τ-invariant** (the L5 threshold does not change the estimate), so it joins across all multipliers.
  3. **Inner-join** on `[instrument, domain, scenario, generator, edge_bps, draw, alpha]`; assert **zero unmatched positive rows on either side** (key-alignment guard — a mismatch means reconstruction drift and must error, not silently drop).
  4. For each `(domain, multiplier, edge_bps)`: `sub = mean(effect_bps < materiality_bps(domain))` over rows with `passed_tau == true`; if the passed-count is 0, `sub` is defined as `0.0` with a `sub_pass_count == 0` flag (no sub-material passes possible — finite zero-baseline handling, never NaN).
  5. Look up `sub(d, τ)` at `edge_bps == MDE(d, τ)` for each frontier τ.
- **Mandatory reproduction cross-check**: the reconstructed `sub(d, τ=0, e)` over all positive edges **must equal** EXP-007 `submaterial_pass_rates.csv` (exact within float tolerance `1e-9`). A mismatch is a hard error (it would prove the τ>0 reconstruction uses a different method than the published τ=0). This guards the whole reconstruction with the one row we can check against an independent experiment.
- **Why this method**: it reuses the only two frozen files that jointly carry the pass state per τ and the net point estimate, under the exact EXP-007 definition; the τ=0 reproduction gate makes the reconstruction self-validating.
- **Simpler alternative considered**: (a) using EXP-006's `ci_lower_bps` as the sub-material criterion — **rejected**, sub-material is a **point-estimate** test (`effect_bps`), not a CI-bound test; `ci_lower_bps ≠ effect_bps`. (b) Materialising all 1.5 M × 432 k rows — rejected; the projected, scenario/α-filtered streaming join keeps memory bounded (positive-scenario, α₀ slice only; ~8 columns each).
- **Assumptions**: draw keys are aligned 1:1 between EXP-003 and EXP-006 (asserted in step 3); `effect_bps` is τ-invariant (true by construction — L5 threshold changes only the pass decision, not the estimate).
- **Expected output**: `sub_material_by_tau.csv` (`domain, multiplier, edge_bps=MDE, sub_rate, sub_pass_count`); a `submaterial_repro_check` boolean (must be true).

### Step 4: Evaluate the three predeclared losses → `τ*_A`, `τ*_B`, `τ*_C` per domain

Implement **exactly** the three losses frozen in `scope.md` §"Predeclared loss function"; no new loss, no coefficient tuning.

- **Loss A (PRIMARY — lexicographic / FPR-constrained)**, per domain over the frontier:
  1. keep τ with `fpr_wilson_upper ≤ α₀ = 0.05`;
  2. among survivors, minimise `mde_bps`;
  3. **materiality tie-break** — drop min-MDE survivors with `sub_rate > 0.50`; among the rest pick the **lowest `sub_rate`**;
  4. **conservatism tie-break** — if still tied, pick the **largest τ**.
  - Degenerate guard (scope): if step 3 removes *all* min-MDE survivors, recommend the **lowest-MDE τ with `sub_rate ≤ 0.50`** and label the row `materiality_limited = true`.
- **Loss B (weighted scalar)**, per domain `argmin_τ`:
  `L_B = 1.0·max(0, mde − mat)/mat + 1.0·(fpr/α₀) + 1.0·sub_rate` (weights `w_blind=w_fp=w_sub=1.0`, frozen).
- **Loss C (Bayes risk over predeclared material-edge prior)**, per domain `argmin_τ`:
  `L_C = 1.0·fpr + 1.0·mean_{e ∈ Gd}(1 − tpr[d,τ,e])`, where `Gd` = the **EXP-006 planted-edge grid points within `[mat, 4·mat]`**, discrete-uniform: **5m → {0.5, 1.0, 2.0}; 1h → {2.0, 4.0}; 4h → {4.0, 8.0, 12.0}** (grid `{0,0.5,1,2,4,8,12,16,24,32}` ∩ band, closed interval). `Gd` is the predeclared reference prior, **not** the EXP-009 distribution.
  - Precision note: every `tpr[d,τ,e]` used must pass the half-width gate (Step 1); if a required `Gd` edge fails precision for a domain, Loss C for that domain is flagged `reduced_precision` and, if that prevents a unique argmin, the domain's Loss-C cell is Inconclusive (does not block A/B).
- **Tie handling in B/C**: exact-tie argmin resolved by **largest τ** (same conservatism convention as A) so all three losses share one tie rule.
- **Why this method**: each loss is a pure, total function of `decision_table` (+ `tpr` for C); the read is mechanical and reproducible, exactly as the scope mandates ("the recommendation read is mechanical once these losses are fixed").
- **Simpler alternative considered**: a single loss — rejected by the operator's robustness requirement; three predeclared losses with a consensus rule turn the "which loss" degree of freedom into an honest robustness check (scope §"Predeclaration integrity").
- **Assumptions**: none distributional. Loss C's expectation is a finite discrete-uniform average (no integration assumption).
- **Expected output**: `loss_evaluation.csv` (`domain, loss {A,B,C}, tau_star, mde_at_tau_star, sub_at_tau_star, loss_value, flags`).

### Step 5: Cross-loss consistency verdict + headline recommendation

- **Method**: per domain, compare `{τ*_A, τ*_B, τ*_C}` on the ordered frontier index. **ROBUST** if all equal **or** all within **one grid step** (|index difference| ≤ 1 pairwise across all three); else **LOSS-SENSITIVE**. Headline recommendation = **`τ*_A`** in every case. For LOSS-SENSITIVE domains, record the full `{τ*_A, τ*_B, τ*_C}` range and a one-line attribution of which cost term (blind-band, FPR, or sub-material) drove the disagreement (read from which term dominates `L_B`/the `L_C` expectation at the differing τ).
- **Why this method**: a one-grid-step tolerance matches the MDE grid quantisation (a difference within the grid resolution is not a meaningful disagreement); it is the predeclared scope rule.
- **Simpler alternative considered**: exact-equality only — rejected: it would call trivial one-step quantisation differences "disagreement", overstating sensitivity.
- **Assumptions**: the frontier is an ordered 7-point grid (frozen).
- **Expected output**: `recommendation.csv` (`domain, tau_star_headline, mde, sub_rate, consistency_verdict, tau_star_A/B/C, driver_term, under_powered`).

### Step 6: Conditional adoption rule + context overlays (no re-selection)

- **Method**: attach to each domain's recommendation the predeclared **conditional adoption rule** verbatim from `scope.md` (re-confirm on fresh Phase 003 draws: FPR Wilson upper ≤ α₀; `sub ≤ 0.50` at the operating MDE; EXP-005-style TPR ≥ 0.80 at the operating MDE — else retain strict `τ=1.0`). Then compute, as **read-only overlays** (never inputs to τ* selection):
  - **Per-instrument masking (EXP-008)**: for each domain, compare the pooled MDE at `τ*` against the per-instrument MDEs (`per_instrument_mde_summary.csv`, `mde_pool_comparison.csv`); flag domains where ≥1 instrument's MDE is `material` (|Δ|≥max(0.5, 0.2·pooled)) — i.e. the pooled recommendation may not transfer per-instrument. (Known at α₀: EURUSD/1h, EURUSD/4h, XAUUSD/4h are lower per-instrument.)
  - **Split-sensitivity (EXP-010)**: from `protocol_comparison.csv`, flag domains where walk-forward materially raises the MDE (1h, 4h) → the recommendation is conditional on the single chronological split.
  - **Non-blindness (EXP-005)**: read `domain_status` (all `DETECTED_FLOOR`) → annotate that any sub-`τ=1.0` recommendation is a sensitivity-headroom choice, not a blindness remedy.
  - **Effect-location reality check (EXP-009)**: from `effect_distribution_summary.csv` / `effect_vs_mde.csv`, report that observed untuned net effects sit below every domain MDE (so the operating-point choice currently affects no real detection) — context only.
- **Why this method**: the scope confines EXP-008/009/010/005 to overlays/caveats; this step records them without letting them re-open the τ* decision (no per-instrument or walk-forward re-selection — explicit scope exclusions).
- **Simpler alternative considered**: omitting overlays — rejected: the conditional adoption rule is a required deliverable and is meaningless without the split/instrument caveats that condition it.
- **Assumptions**: overlays are descriptive; no new inference.
- **Expected output**: `adoption_rule.json` (per-domain rule text + overlay flags); fields feeding Plot 4 and `run_metadata.json` rollup (`recommendation_by_domain`, `consistency_by_domain`, `inconclusive_domains`).

---

## Visualisations

1. **Loss-vs-τ curves, small multiples per domain** — for each domain, three lines `L_A`-rank / `L_B` / `L_C` over the 7-point τ-frontier with each loss's `τ*` marked. Shows *why* each loss lands where it does. (Loss A has no continuous scalar; plot its rank/selection markers alongside B/C scalars on a twin axis or as marker overlays.)
2. **MDE-vs-τ frontier per domain** — step plot of `MDE(d,τ)` over τ, with the materiality buffer as a horizontal reference line, sub-material rate shaded/annotated per τ, and the headline `τ*` marked. Shows the sensitivity↔sub-material trade-off the recommendation balances.
3. **Cross-loss consistency matrix** — 3 domains × 3 losses heatmap/table of selected `τ*`, cells coloured by per-domain ROBUST/LOSS-SENSITIVE verdict. The at-a-glance robustness result.
4. **Adoption / robustness overlay** — per domain, the pooled MDE at `τ*` against (a) per-instrument MDEs (EXP-008) and (b) walk-forward MDE (EXP-010), with the materiality buffer line. Shows where the single-split pooled recommendation is instrument- or split-sensitive (the adoption caveats).

All plot inputs are the small aggregated tables from Steps 2–6 (≤ a few dozen rows each); no raw draw frame is converted to pandas for plotting (the bounded join output is aggregated first).

---

## Interpretation Guide (predeclared before results exist)

- If, for a domain, the three losses select the **same τ or within one grid step** → **ROBUST**; report `τ*_A` as the recommended operating point with confidence that it is not an artifact of the loss specification.
- If the three losses **diverge by more than one grid step** → **LOSS-SENSITIVE**; report `τ*_A` as the headline but explicitly flag sensitivity, give the `{τ*_A,τ*_B,τ*_C}` range, and name the driving cost term; the conditional adoption rule must carry the sensitivity into Phase 003.
- If, among the lowest-MDE τ for a domain, **all have `sub_rate > 0.50`** (expected most likely at 5m, where the τ=0 endpoint sub ≈ 0.4965 sits just under the cutoff) → the recommendation is **materiality-limited**: the lever's extra sensitivity is mostly sub-material there, so the recommended τ is the most-stringent τ achieving the min MDE, and the write-up states the sensitivity gain over strict `τ=1.0` is largely economically negligible.
- If a domain's required inputs **fail the precision gate** or the losses cannot produce a unique `τ*_A` → **Inconclusive** for that domain ("no recommendation for domain d"); not forced to a value.
- If the **per-instrument overlay** shows ≥1 material instrument deviation (EURUSD/XAUUSD at 1h/4h) → annotate that the pooled recommendation may understate achievable sensitivity for the tighter-MDE instruments; this conditions, but does not change, the pooled headline.
- If the **walk-forward overlay** shows a material MDE increase (1h/4h) → the recommendation is explicitly conditional on the mandated single split and must be re-confirmed under walk-forward before any Phase 003 adoption.
- Because EXP-005 is `DETECTED_FLOOR` on all domains, **any** recommendation below `τ=1.0` is interpreted as a sensitivity-headroom recommendation, never as correcting demonstrated blindness.

This experiment **recommends**; it does not adopt. No fresh-draw ratification is performed here (Phase 003).

---

## Implementation Safety Constraints (for experiment-developer)

- **No market data, no holdout, no new draws.** Pure result-level post-processing. The first-70% loader pattern is included in the scope only as the mandatory safety pattern *if* raw bars were ever touched — they must not be. No code path globs `data/timebars` for analysis.
- **Bounded memory on the only heavy step (Step 3 join)**: use `pl.scan_csv(...).select(<projection>).filter(scenario=="positive", alpha==0.05)` on both draw files *before* `collect()`; inner-join on the 7 keys; never materialise the cross product. Assert zero unmatched positive rows.
- **Determinism**: every output is a deterministic function of frozen inputs; no randomness, no seeds needed. Re-running must reproduce all CSVs byte-stably (sort outputs by `domain, multiplier[, edge_bps]` before write).
- **Finite zero-baseline handling**: `sub_rate` with zero passing draws is `0.0` with an explicit `sub_pass_count` flag — never NaN, never a divide-by-zero. Loss C's `(1 − tpr)` is bounded in [0,1] by construction.
- **Frozen constants, no magic numbers**: `MATERIALITY_BPS = {5m:0.5, 1h:1.5, 4h:3.0}` and α₀=0.05 imported from / asserted against `xen.referee_calibration`; loss coefficients (`w_*`, `c_*`, `0.50` sub cutoff, `4·mat` band, one-grid-step tolerance) declared as named constants in a clearly-sectioned constants block, each annotated as predeclared by scope (not tunable).
- **Reproduction gate is a hard error**, not a warning: if `sub(d, τ=0)` reconstruction ≠ EXP-007 published values (tol 1e-9), or any dependency token/precision gate fails for a domain feeding a recommendation, raise/flag explicitly per the scope's Inconclusive discipline.
- **Sectioning (VAL-001 style)**: imports → path setup → constants → I/O loaders → pure loss/aggregation functions → plotting → orchestration → `main()`. No directory creation, file writes, data loads, or plotting at import time. Helper functions return data; orchestration prints concise progress. Use `tqdm` only if any loop is long (the join is a single vectorised op; per-domain loops over 3 domains × 7 τ are trivial and need no progress bar).
- **Vectorisation discipline**: the sub-material aggregation is a Polars group-by (causally safe — no temporal reordering, denominators preserved as positive-pass counts). Keep the loss-selection logic explicit per domain (only 21 rows); do not over-vectorise the lexicographic rule at the cost of readability.
- **Alignment**: all joins are by **draw key**, never by row position; timestamp/bar-index alignment is not applicable (no market data), but the draw-key join must be on the full composite key, never positional.

---

## Complexity Check

- **Statistical operations**: 2 / 2 — (1) precision-gate classification via the frozen Wilson half-widths; (2) sub-material proportion estimation (the reconstructed pass-rate). The three loss evaluations and the consistency verdict are deterministic arithmetic, not statistical tests.
- **Visualisations**: 4 / 4 — loss-vs-τ; MDE-vs-τ frontier; consistency matrix; adoption/robustness overlay.
- **New modules**: 1 / 1 — one small `loss_functions.py` (pure functions for Losses A/B/C, the sub-material reconstruction, and the consistency verdict), keeping `run_experiment.py` as orchestration. Inline is acceptable if the developer prefers 0 modules; must not exceed 1.

## Data-View / Alignment Considerations

- All inputs are **result-level tables** from frozen experiments; the only "view" is the draw-keyed verdict space. Cross-file combination (Step 3) is by **composite draw key**, never bar index or row order.
- Observation-count note: EXP-006 carries 7 multipliers per EXP-003 draw, so `threshold_draw_verdicts` ≈ 3.5× the EXP-003 positive-draw count per domain after the α/scenario filter; the join is many-(τ)-to-one on `effect_bps`, which is the intended τ-invariant fan-out (assert the per-key multiplicity equals the number of frontier multipliers present).
- Real-price discipline: not directly exercised (no returns computed here), but every reused `effect_bps`/MDE/TPR originates from EXP-003's real domain `Close` outcomes; no synthetic price enters at any point.
