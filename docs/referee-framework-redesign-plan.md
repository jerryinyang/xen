# Referee Framework Redesign — Consolidated Plan (D0 input)

**Purpose.** Filter + consolidate three independent assessments of
`docs/referee-framework-design-manual.md` — the manual author's own
(`docs/referee-framework-assessment.md`), independent auditor 1, and independent auditor 2 — and
**cross-validate every load-bearing claim against the authoritative code**
(`python/src/xen/referee_calibration.py`, `incremental_referee.py`), not against the manual's prose.
The output is a structured plan that the Chapter-02 Phase-001 checkpoint's **D0 predeclarations**
(`docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/`) build on,
for the framework-update branch (O1 referee renew / KB **L-12**).

**Method note.** Auditors offered both *speculations* ("verify against code: is block length on raw
returns or P&L?") and *observations*. The consolidation below resolves the speculations by reading
the code, so D0 inherits verified facts, not unexamined claims. Several headline concerns dissolve on
contact with the code; the single highest-leverage one is confirmed.

---

## 1. Cross-validated findings ledger (claim → code → verdict)

Code line references are authoritative (manual §0: "where manual and code disagree, code wins").

| # | Claim (source) | Code check | Verdict |
|---|---|---|---|
| **F1** | Block length may run on **raw returns** → ACF≈0 → bootstrap silently degenerates to i.i.d. → understated CIs (auditor 2 verify #1) | `referee_calibration.py:964,972` — block length is estimated on `strategy[:cut]`, the **P&L series**, not raw returns; minimal baseline `:816` same; incremental `_contiguous_block_length` on `net_full` | **REFUTED** — for the *block-length input only*. Code does it right. **Does not** dismiss the deeper verdict-statistic concern → see **F10**. |
| **F2** | L3 "vs-naive" might be **two separate CIs** (weak) rather than a CI on the **difference series** (auditor 2 verify #2) | `:975` `diff_vs_naive = test_values − naive[...]`; `:1037` `ci_naive` is the CI on that difference series; L3 = `ci_neutral.lower>0 ∧ ci_naive.lower>0` | **REFUTED.** Code uses the stronger difference-series form. Not a defect. |
| **F3** | **Component A charges cost per-holding-bar; Component B amortizes per-episode** — internally inconsistent cost footing (auditor 2 [High], verify #3) | A: `strategy_return_bps:538` `gross − cost_bps*active` charges full round-trip on **every non-zero bar**. B: `per_bar_incremental_cost:131` = `cost_bps/episode_length` | **CONFIRMED.** Real, verified asymmetry. **Highest-leverage finding.** A overcharges turnover for any persistent-direction (low-turnover) signal. |
| **F4** | `L2_integrity` ships as a hard-coded `True` no-op inside a go/no-go gate (auditor 1 #5, auditor 2 [High]) | `gate_stack_core:1003` `"l2": True` | **CONFIRMED.** The "5-check" stack has only 4 live legs. |
| **F5** | The "5-check" gate is effectively **~3 binding checks** (auditor 2 [Med]) | L5 (`:1038` neutral CI-lower > materiality > 0) ⟹ test-net mean > 0 ⟹ L4's test-side (`:1004`) is auto-satisfied; L4 reduces to a **train-sign** check; L2=True. Binding DoF = **L1, L3, L5** | **CONFIRMED.** Power/FPR reasoning must be attributed to L1/L3/L5, not five legs. |
| **F6** | The MDE is measured against **constant additive drift**, which real alpha (state-dependent / tail / nonlinear) does not resemble (auditor 1 #2) | `plant_positive_edge:508` `returns + states*delta_return` (constant per-state drift); substrate `:339` identical | **CONFIRMED.** Directly scopes the Q2 synthetic-positive battery — the renew must plant non-constant shapes. |
| **F7** | The naive control is **one fixed strawman** (prior-return sign); beating it ≠ broad superiority (auditor 1 #3; author obs b) | `naive_momentum_positions:541` is the sole control | **CONFIRMED.** |
| **F8** | **Component-selection is a post-hoc DoF** — "binding component depends on scope," chosen after seeing results, is the selection the freeze forbids (auditor 2 [Med]) | Manual §1; no code binds a component pre-hoc | **CONFIRMED (protocol gap).** Predeclare the binding component per candidate. |
| **F9** | The cost asymmetry **compounds** Mode-1 fragility and the pooled-domain veto, worst on **BTCUSD** (10 bps round-trip charged per holding bar) (auditor 2 r2) | F3 + `ROUND_TRIP_COST_BPS:60` BTCUSD=10.0 all domains | **CONFIRMED.** Part of what the assessment blamed on the AND / equal-weight pooling (author obs d) is actually A over-charging turnover. |
| **F10** | **The binding verdict statistic is the MEAN of a sparse per-trade / per-active-bar net-P&L series** (`gate_stack_row:1059` CI on `neutral_mean`; B on the `m≠0` denominator). Per-trade P&L is **fragile, sparse, unstable**; a per-bar **return-series risk-adjusted metric** (Sharpe + co-binding Calmar/tail) on the net equity curve is more robust and rounded. (operator-raised; absent from all 3 assessments) | `strategy_return_bps:511` → mean-of-series is the only location stat; **Phase 022 precedent verified**: EXP-095/096 (`archive/.../checkpoints/2026-06-24-022-portfolio-noise-holdout/`) moved portfolio adjudication from pooled per-trade expectancy → **time-aligned equity-curve Sharpe LB + co-binding Calmar LB** (MBB, MTM per L-09); `D0-amendment-001` F3: "Sharpe **alone** is a weak economic descriptor for a sparse, clustered MR strategy" (high Sharpe = scrutiny flag) | **CONFIRMED (architectural).** The referee's location-mean statistic should be complemented (≥ dual-reported), and tested for replacement, by a return-series risk-adjusted + tail stack. **Reinforces Q7** (per-bar open-to-open is the natural equity-curve input) and **partly subsumes F3** (cost = per-bar drag on the curve, not a per-trade-mean charge). |

### Unverifiable by reading (stand as plausible; resolve with a run)
- **4h readiness floor near bootstrap breakdown** — `effective_n≥25`, `≥8 episodes/direction` (`DOMAIN_SPECS:50`). FPR≈0 at 4h may be wide-CI blindness, not discrimination (auditor 2 [Med]). Needs an empirical CI-width check.
- **Percentile-bootstrap undercoverage on fat-tailed P&L** — `percentile_ci`/`ci_from_means` are one-sided percentile bounds; BCa/studentized would cover better (auditor 1, auditor 2 [Low]). Coverage-quality margin, not a live bug.
- **FPR≈0 precision** — "≈0" over a finite calibration set (B was 126/126) bounds true FPR only to low-single-digit % at 95%. `wilson_interval` already exists — report the count + Wilson upper bound, drop "≈0" (auditor 1 #6, auditor 2 [Med]).

---

## 2. Affirmed — do not touch (all three converge)

- **Split discipline** (`load_analysis_data`, `domain_split_index`, `resolve_split_index`): wall-clock `train_end_ts` fixed on the 1-min base, inherited across resampled domains; train-estimated block length; test-only inference. Causal/streaming-safe. **Keep.**
- **Component B marginal estimator** (`marginal_net_series`): `m = clip(R+C,±1) − R` on real returns, denominator `m≠0`, model-free w.r.t. R–C dependence. **The strongest part of the whole suite** (both auditors). Keep.
- **F04 contiguous block length** (`_contiguous_block_length` on zero-padded `net_full`): a real bug correctly fixed; gap-extraction would destroy within-episode autocorrelation. **Keep.**
- **One bootstrap distribution reused across the α grid** — guarantees nested/monotone α decisions. **Keep.**
- **Negative anchors** (untuned Donchian/MA, broadened simples at net ≈ −1 bps): meaningful "gate isn't trivially passable" control. **Keep.**
- **EXP-015 → revised drop of standalone-L2** in Component B: correct lesson (no finite MDE under a synchronous null). **Keep** the revised unit.

---

## 3. The central reconciliation — rigidity is *both* the bug and the asset

The one **genuine live disagreement** across the three docs (surfaced in both auditors' round-3
replies, reconciled in neither source):

- **L-12 / assessment author:** the fixed-threshold conjunction's rigidity is the **keystone bug**
  (Modes 1–3): hard vetoes, no-finite-MDE auto-fails, mis-scaled thresholds.
- **Auditor 2:** the rigidity is the **institutional asset** — the suite's *rejections* are
  trustworthy **precisely because** thresholds never see the candidate. Candidate-matched thresholds
  (§10.2) **spend** that guarantee.

**Synthesis adopted (both round-3 replies independently land here):** split the gate by what each
leg earns.

> **Hard validity floor / soft economics.** Keep rigidity where it earns trust — **readiness L1 +
> coverage** (cannot be faked, keep at FPR≈0, candidate-blind). Relax / adapt rigidity only on the
> **economic legs** (L3 / L5), and only where Modes 1–2 **demonstrably** cost a true positive.

This makes candidate-adaptivity surgical, not global: the FPR guarantee on the validity floor stays
candidate-blind (so rejections stay credible), while power is bought back on exactly the leg/cell
combinations where the chapter's evidence shows true positives were vetoed.

---

## 4. The falsifiable success criterion (gives Q8 its operational definition)

All of §10.3's composite-form options collapse to **one testable question** (auditor 2's reframe):

> Does any redesign **dominate** the frozen conjunction on the **DET curve** — strictly lower
> economic MDE at equal-or-better dogfood-negative FPR?

- **If yes** → adopt the dominating operating point; freeze it before any live read.
- **If no composite dominates** → the conjunction is already on the efficient frontier, and "the
  frozen suite is not improvable without losing FPR control" (Q8) is **proven, not asserted** — itself
  a valid, falsifiable Phase-001 outcome.

This replaces the vague "improve or at least preserve FPR" success bar with a DET-dominance test.

---

## 5. Prioritized redesign levers (re-ranked by cross-validated evidence)

Re-ranked from assessment §10 using the code findings. **The cost-control arm is promoted to first**
because it is the cheapest experiment and isolates how much of Mode 1 is structural vs. accounting.

| Rank | Lever | Fixes | Evidence basis | Risk |
|---|---|---|---|---|
| **0 (do first)** | **Amortize A's cost like B** (control arm): re-run A with `cost/episode_length` turnover cost vs the current per-holding-bar charge | F3/F9 — Mode-1 contribution from cost accounting, not gate shape | **Code-confirmed** asymmetry; cheap; freeze-clean (no candidate involved) | Low. May recover persistent/modest cases *without touching gate shape*. |
| **1 (tie)** | **Return-series evaluation unit** (F10, operator-raised) — replace/complement the location-mean P&L statistic with a per-bar **net equity-curve** assessed by a **risk-adjusted + tail stack** (Sharpe LB **co-bound** with Calmar/tail, since Sharpe-alone is weak for sparse clustered MR — Phase 022 D0-amend-001 F3). **Minimum: enforce dual reporting** (per-trade AND return-series); test whether the return-series stat **dominates** mean-P&L on the DET curve | F10 sparsity/instability; **Mode 3** (sparse-vehicle dilution, L-04) | **Phase 022 precedent verified** (EXP-095/096 return-series Sharpe+Calmar LB with MTM). Natural input once Q7 re-baselines to per-bar open-to-open; partly subsumes F3 | **Scope import:** brings the Phase-022 *deployment-stage* return-series lesson (assessment §11 **sense 2**) **upstream** into the referee (**sense 1**) — a deliberate widening of the renew. High-Sharpe scrutiny flag + MTM discipline (L-09) must carry over. |
| **1 (tie)** | **Power-aware leg gating** — leg → `UNPOWERED` (excluded, not failed) where it has **no finite MDE in the cell** | Mode 2 | Generalizes EXP-015→017; both auditors rate it high | **Hidden DoF:** finite-MDE must be computed on **calibration/planted** data, **never** the candidate's realized returns, else it becomes outcome-dependent leg selection (auditor 2 #1). Bake into the predeclared rule. |
| **2** | **Validity-then-economics sequencing** (§10.3a): L1+coverage gate *admissibility*; a **single binding economic statistic** (incremental net CI-lower) decides edge; other legs become reported diagnostics | Mode 1 | **Both auditors' top composite pick**; cleanest classical architecture; preserves a hard validity floor (§3 synthesis) | Concentrates FPR onto one CI — where the percentile-undercoverage margin (§1 unverifiable) starts to matter. Verify CI coverage. |
| **3** | **Candidate-matched thresholds** (§10.2): MDE-curve co-designed with the candidate per vehicle/shape/instrument; per-instrument MDE where powered (< pooled, EXP-008) | Mode 3 | Generalizes EXP-095 band, L-08; deepest demonstrated mis-scaling | **Spends the freeze guarantee** (both auditors). Mitigation: a **frozen, deterministic, performance-independent** derivation rule, predeclared (Q5). Apply only on economic legs (§3). |
| **4** | **Activity-rate-aware vehicle routing** (§10.4): classify active-fraction → per-bar vs event-level | L-04 | Both note it; **but** only routes to two validated endpoints — the **6–80%-active middle has no validated vehicle** (auditor 2 [Low]). Either calibrate one or scope it out. | Coverage gap, not a defect. |
| **5 (candidate, not settled)** | **ASS / WF adaptive backbone** (`xen.ass`, `xen.wf`) — KDE + hier. empirical-Bayes shrinkage + bootstrap CI; expectancy/median/tail | shape-blindness; **also fixes the 4h breakdown** (small-n guard defers to median at eff-n≤60, and 4h eff-n≈25 sits inside it — auditor 2) | VALIDATED_WITH_GUARDS (EXP-076/077), not fully ratified | Empirical-Bayes shrinkage **is a pooling mechanism** → latent **L-03** tension; confirm per-stratum estimate still emitted, shrinkage bounded. Higher validation burden. |
| **last** | **Calibrated soft-vote** (§10.3b): weighted score over legs, threshold set to dogfood FPR | Mode 1 | **Both auditors rank it last** | New free DoF (weights/cutoff/normalization); fits to one negative's shape. **De-prioritize.** |

Also adopt (independent of the composite): **per-stratum verdict by construction** (§10.6, fixes
L-03); **reconcile spec↔code** on the leg names (author obs a — `evaluation-framework.md` vs the
implemented L2=True / folded-L3); **implement or delete L2** (F4); **report decision margin /
distance-from-boundary** alongside pass/fail (auditor 1 r3 — quantify knife-edge vs plateau).

---

## 6. The missing analysis both docs lack — threshold/gate robustness

Auditor 1 (round 3) and auditor 2 (round 3) agree the assessment covers **rigidity** (the *shape*)
exhaustively but **statistical robustness** (the *machinery's* stability) barely. Add to the renew:

- **Threshold-perturbation sweep.** For each threshold (materiality, `min_effective_n`,
  `min_state_count`, coverage, CI cutoff), recompute Δverdicts under ±5/10/20% perturbation; report
  "% of decisions invariant." Distinguishes a stable plateau from a knife-edge.
- **Bootstrap sensitivity** — alternative block-length estimators / bootstrap variants.
- **4h CI-width audit** — is FPR≈0 at 4h discrimination or wide-CI blindness?
- **Recent-regime disclosure** — inference lands on total-percentile [49%,70%]; the [70%,100%] holdout
  is never loaded, so a signal decaying in the recent regime still passes. Not fixable in Phase 001
  (holdout sealed) — **one disclosure sentence** in interpretation.

---

## 7. Recommended D0 predeclarations (answers to assessment §12)

Q2 is sequenced **before** Q1 (auditor 2: you can't pick the FPR/power frontier without first fixing
which edge shapes you're trying to recover). **Forks Q1/Q4/Q6/Q7 are operator-ratified (2026-06-27)** —
values below are binding D0 inputs.

| Q | Ratified decision / recommendation | Status |
|---|---|---|
| **Q2 synthetic battery** (do first) | Predeclare edge **shapes** the redesign must gain power on — and per **F6** make them **non-constant**: dense, **tail-only**, **sparse/event**, **state-dependent**, sub-MDE→super-MDE, on the cells the frozen gate failed. Plant via an extended generator (not only `plant_positive_edge`'s constant drift). | Recommend |
| **Q3 dogfood draws** | Reuse the EXP-019 dogfood construction **+** draw fresh additional nulls; report FPR with a stated **Wilson half-width** (`wilson_interval` exists) and a draw count — never "≈0". | Recommend |
| **Q1 FPR frontier** | **Surgical small budget.** Validity floor (L1+coverage) stays **hard at FPR≈0 and candidate-blind**; a small FPR (≤ α) is spent **only** on the economic legs (L3/L5) where Modes 1–2 demonstrably cost true positives. | **RATIFIED** |
| **Q4 composite form** | Primary = **§10.3(a) validity-then-economics**; also evaluate **(c) single-statistic** as a reported variant, **selected by §4 DET-dominance** (one predeclared criterion controls the 2-way multiplicity). **(b) soft-vote dropped.** | **RATIFIED** |
| **Q5 threshold-derivation rule** | If candidate-matched thresholds are adopted: the rule must be **frozen, deterministic, performance-independent**, computed on **calibration/planted** data only (never candidate realized returns). Default: per-instrument MDE where powered, else band-co-designed MDE-curve. | Recommend |
| **Q6 scope universe** | **Full 17-instrument universe (VAL-003), domains 1h/4h only** (5m dropped). **Consequence (binding):** the frozen `ROUND_TRIP_COST_BPS` map defines only 4 instruments (`referee_calibration.py:57-62`) — recalibration **must extend a frozen, predeclared per-instrument round-trip cost** to all 17 **before E2**, set candidate-blind (a cost knob set after seeing results re-opens the freeze). Per-instrument MDE (EXP-008: < pooled) becomes the powered default across a much wider cost range. | **RATIFIED** |
| **Q7 return convention** | **Re-baseline to open-to-open `≤ t-1`** (Chapter-02 standing convention). The frozen close-to-close (`next_log_returns_from_bars:469`) is Chapter-01 legacy and `OnClose` is not live-actable. Full recalibration runs on the new return basis; the retained old suite keeps close-to-close for parallel disclosure. | **RATIFIED** |
| **Q8 "not improvable"** | The **§4 DET-dominance** test: if no redesign strictly lowers MDE at equal-or-better FPR, the frozen suite is on the efficient frontier and "not improvable without losing FPR control" is proven. | Recommend (resolved) |

| **Q9 metric unit** (F10, new) | **Enforce dual reporting** — every verdict carries **both** the per-trade/per-active-bar net-P&L stat **and** a per-bar return-series risk-adjusted stat (**Sharpe LB co-bound with Calmar/tail**, MTM per L-09, high-Sharpe scrutiny flag). Test via §4 DET whether the return-series stat should **bind**. Materiality (L5) gets a parallel return-series floor (calibrated like Phase 022's m\*). | **RATIFIED (operator-raised)** |

Plus predeclare: **binding component per candidate** (fixes F8 post-hoc selection); **per-stratum
verdict representation**; the **cost-control arm** (lever 0) as the first sub-experiment; the
**return-series evaluation unit** (Q9/F10) co-developed with the metric (note: this widens the renew
to import the Phase-022 deployment-stage lesson upstream into the referee — assessment §11 sense 2 → sense 1).

**Q6 cross-checks pulled in by the 17-instrument / 1h-4h-only choice:**
- **Per-instrument MDE is now load-bearing** — 17 instruments span a far wider cost range (forex 1.0 →
  BTCUSD 10.0+), so the pooled MDE map (L-04 dilution; author obs d) is even less defensible; lever 3
  (candidate-matched, per-instrument-where-powered) is effectively mandatory, not optional.
- **F3/F9 cost asymmetry bites harder at scale** — A's per-holding-bar overcharge compounds across more
  high-cost instruments; the E1 cost-control arm is more, not less, important.
- **4h thinness (§1 unverifiable) multiplies** — 4h readiness (eff_n≈25) across 17 instruments puts many
  4h cells near the bootstrap-breakdown floor; the E4 4h CI-width audit must run **per-instrument**.
- **Per-stratum non-pooling (L-03) is unavoidable** — 17×2 domain cells; a pooled verdict would mask far
  more heterogeneity. Bake per-stratum output in (§10.6).

---

## 8. Structured experiment plan — D-referee branch

Sequencing under the checkpoint gates (G0 → D-referee → D-benchmark). The new gate is **frozen
(hash-pinned) before** it adjudicates CF-MR-002; it must **never** be tuned on CF-MR-002 (the exact
L-12 selection bias).

```
G0 (operator-gated): ratify this plan's predeclarations → checkpoint design.md D0.
                     Forks Q1/Q4/Q6/Q7 ratified (§7). 0 reads / 0 slots.
   │
   ├─ E0  Freeze the 17-instrument per-instrument cost map (Q6 consequence) + re-baseline
   │      returns to open-to-open ≤t-1 (Q7). Candidate-blind, set BEFORE E1. Prereq for all below.
   │
   ├─ E1  Cost-control arm (lever 0).  Re-run frozen A with B-style amortized cost on the
   │      dogfood-negative + synthetic-positive. Measure how much Mode-1 power loss is
   │      accounting (F3/F9) vs gate shape. Freeze-clean: no live candidate. → DET point.
   │
   ├─ E2  Synthetic-positive battery (Q2) + fresh dogfood draws (Q3).  Build the non-constant
   │      edge-shape generator (F6); fix shapes BEFORE the FPR frontier. Wilson-bounded FPR.
   │      17 instruments × {1h,4h} cells, per-stratum.
   │
   ├─ E3  Adaptive gate build.  Return-series evaluation unit (Q9/F10: per-bar equity-curve
   │      Sharpe LB + co-binding Calmar/tail, dual-reported with per-trade) + power-aware leg
   │      gating (lever 1, calibration-data MDE only) + validity-then-economics composite
   │      (lever 2) + candidate-matched economic-leg thresholds (lever 3, frozen rule).
   │      Per-stratum output. Implement/remove L2 (F4). Reconcile spec↔code leg names.
   │
   ├─ E4  Robustness pass (§6).  Threshold-perturbation Δverdicts; 4h CI-width audit; bootstrap
   │      sensitivity; recent-regime disclosure.
   │
   ├─ E5  Adjudicate on the DET curve (§4).  Does any redesign dominate the conjunction?
   │      Adopt the dominating point OR record the proven "not improvable" null. FREEZE + hash-pin.
   │
   └─ D-benchmark  Run CF-MR-002 causal in-engine; report on BOTH the frozen old suite AND the
                   newly-frozen adaptive gate (parallel disclosure). Holdout untouched.
```

**Pipeline routing.** E1–E5 are **analysis-only** (Python on emitted/synthetic substrates;
`build_rc_substrate`, `plant_positive_edge`, the frozen primitives) → run directly under the lean
pipeline. CF-MR-002 (D-benchmark) is **price-primary** → cTrader StrategyHost, operator-gated
credentialed run. Every price-primary leg ships a future-destroying control (L-01).

**Hard guards carried in.** Referee FROZEN until E5 freeze; new gate not tuned on CF-MR-002; global
holdout sealed (not in Phase-001 scope); per-stratum binding verdicts (pooled = disclosure-only);
no scope expansion after G0.

---

## 9. Operator decisions — ratified (2026-06-27)

The 4 forks not derivable from code or the assessments are now decided:

- **Q1 FPR frontier** → surgical small budget (hard validity floor, soft economics).
- **Q4 composite form** → validity-then-economics primary + single-statistic variant, select by DET.
- **Q6 scope universe** → full 17-instrument, 1h/4h only (5m dropped). Pulls in the **E0** cost-map
  freeze + the four §7 cross-checks.
- **Q7 return convention** → re-baseline open-to-open `≤ t-1`.
- **Q9 metric unit (F10, operator-raised)** → enforce dual reporting (per-trade + per-bar
  return-series Sharpe LB co-bound with Calmar/tail, MTM); DET-test whether the return-series stat
  binds. Widens the renew to import the Phase-022 return-series lesson upstream (assessment §11 sense
  2 → sense 1).

Everything else in §7 proceeds on its evidence-based recommendation unless overridden at G0. This plan
is the consolidation feeding the checkpoint `design.md` D0 predeclarations; ratifying those (and
registering CF-MR-002) remains the operator-gated G0 step.
