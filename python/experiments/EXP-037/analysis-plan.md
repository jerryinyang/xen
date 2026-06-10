# Analysis Plan: Experiment EXP-037 — `/EXIT-FH` Fixed-Horizon-Exit Capture-Efficiency Variant (4h, one-shot TEST)

## Objective

On the 4h domain only (G1-B2 qualification: EXP-033 TRAIN grid max +45.79 bps > 0),
freeze a single fixed-horizon exit H\* and pyramid policy from TRAIN by the scope's
mechanical tie-break (computed on the spill-contained TRAIN subset, R1.5), then
evaluate the FH(H\*) variant's **net** per-event expectancy (absolute estimand,
frozen CONSERVATIVE costs + financing) **exactly once** on the TEST stratum, per
instrument (EURUSD-4h, USTEC-4h, XAUUSD-4h). Binding inference (design §8.4 as
amended R1.1/R1.2): raw one-sided bootstrap p per cell entering the **phase-level
Holm family** (these 3 cells + EXP-038's cell; adjudicated in the checkpoint's
`G2-gate-review.md`), and a one-sided 95% lower bound that must clear the
**calibrated margin m_cell** from the pre-TEST synthetic-null calibration. This
run emits raw p's and `route_pass_provisional` flags only — never `g2_satisfied`.
Possible outcomes per scope: provisional pass cells, EVIDENCE_AGAINST,
INCONCLUSIVE_SPANS_ZERO, or `B2_NO_ROBUST_HSTAR` (no TEST read at all).

## Data Wiring

Identical substrate to EXP-033/EXP-034 (their plans incorporated by reference):

- `EXP-022/results/lifetime_observations.csv`, `role = event`,
  `reportable_event = true` — the EXP-028/030 PRIMARY population, pyramids included.
  4h cells only; BTCUSD excluded (D0 §3). Full-analysis cell counts must reconcile
  exactly to EXP-030: EURUSD-4h 39, USTEC-4h 36, XAUUSD-4h 42.
- `EXP-020/results/avwap_events.csv` — trigger timestamps (1:1 join, zero unmatched
  rows, hard assert).
- Rebuilt 4h domain Close series via `xen.bar_aggregator` (EXP-031/033-identical
  parameters; bar counts must reproduce `EXP-020/results/analysis_metadata.csv`).
  The rebuilt series covers only the first-70% analysis slice, so FH truncation at
  series end can never read the global holdout.
- Frozen `event_method.py` inference tail, pinned hash `e50873d12a9f68d9` (hard
  assert — guard 3).
- Frozen constants: RT_cons = {EURUSD 3.0, USTEC 5.0, XAUUSD 6.0} bps; financing
  rates = {EURUSD 0.6, USTEC 1.2, XAUUSD 1.2} bps per calendar day, adverse-side,
  fractional days from rebuilt-series timestamps.

**FH outcome (EXP-033-identical construction):**
`fh_bps(e, H) = 10000 × d × ln(close[entry_idx + H] / close[entry_idx])`, truncated
to the last available analysis bar when `entry_idx + H` exceeds the rebuilt series
(predeclared). `net_e(H) = fh_bps(e, H) − RT_cons_i − rate_i ×
elapsed_calendar_days(trigger_close_time, fh_exit_close_time)`. Financing helper is
the EXP-034 pure function, reused verbatim.

### Stratum partition (binding population; guard 2; R1.3 unified convention)

Per (instrument, 4h): the binding boundary is the **CloseTime of the last TRAIN
1-minute analysis row** (`train_rows = int(analysis_rows × 0.7)`; the shared
loader's `train_end_ts` — the project convention, identical to EXP-038). An event
is **TEST iff its entry-confirmation (trigger) close time > boundary**; ties →
TRAIN. This is causal (known at entry) and exhaustive: TRAIN ∪ TEST = the
full-analysis cell with no drops or duplicates (hard reconciliation against the
EXP-030 counts above). A TEST event's FH window may truncate at the analysis end —
predeclared in scope. The per-cell membership divergence between this timestamp
boundary and the EXP-033 bar-index cutoff (`floor(0.7 × n_domain_bars)`) is
disclosed in `reconciliation.csv` (transparency only).

The EXP-033 bar-index cutoff survives **only** inside guard 1's reproduction
anchor, which runs on EXP-033's own contained population (F08 rule) to prove
code-path equivalence before the binding trigger-keyed numbers are computed.

### Selection population (R1.5 — spill containment)

All TRAIN selection reads (tie-break, policy, calibration dispersion) use the
**contained TRAIN subset**: TRAIN events whose FH window at the grid maximum
H = 12 exits at or before the boundary timestamp (`close_time[min(start_idx + 12,
n − 1)] ≤ boundary`). The containment horizon is fixed at 12 across all candidate
H so the selection population is constant (the EXP-033/F08 pattern). Excluded
spill events are counted and disclosed (`n_spill_excluded`); they remain in the
binding TRAIN/TEST membership — only the selection objective is blind to them.
This makes the freeze strictly TEST-price-blind.

## Methodology

### Step 1 — Integrity guards 1–3 (hard gate before any selection output)

- **Method**:
  (a) **Guard 1 — EXP-033 reproduction anchor:** recompute the FH net curve at
  H ∈ {4, 6, 8, 12}, all_legs, under EXP-033's containment rule on its TRAIN
  population; the 4h objective values must reproduce
  `EXP-033/results/fh_net_curve.csv` (6.150307 / 20.948089 / 31.299833 / 39.105283
  bps) to ≤ 0.01 bps, and per-instrument n must match (27/25/34). Same code path,
  same population ⇒ near-exact; any drift is a hard stop.
  (b) **Guard 2 — population reconciliation:** per-cell TRAIN + TEST counts sum to
  the EXP-030 full-analysis counts (39/36/42), zero dropped/duplicated event keys.
  (c) **Guard 3 — frozen-tail hash pin** == `e50873d12a9f68d9`.
- **Why this method**: the one-shot TEST read is only meaningful if the estimator is
  provably the one EXP-033 ran and the stratum partition provably tiles the audited
  EXP-030 population. This mirrors EXP-033's own Step-1(c) relaxed-rule anchor.
- **Simpler alternative considered**: trust shared code — rejected; the
  trigger-keyed partition is new logic adjacent to the population definition.
- **Assumptions**: none beyond artifact integrity.
- **Expected output**: `results/reconciliation.csv` (PASS/FAIL per anchor; all PASS
  required to proceed).

### Step 2 — TRAIN tie-break table and H\* selection (mechanical, predeclared)

- **Method**: on the **contained TRAIN subset** (R1.5 above), for each
  H ∈ {4, 6, 8, 12} under pyramid policy all_legs, compute the domain objective net
  (EXP-033-identical aggregation: per-instrument event-weighted mean of `net_e(H)`,
  equal-weight across EURUSD/USTEC/XAUUSD) three ways: full `N(H)` and
  chronological split-half `N₁(H)`, `N₂(H)` (halves split at the pooled median
  contained-TRAIN trigger timestamp, EXP-033's split construction). Pre-freeze
  feasibility: every instrument must be non-empty in both halves (hard stop —
  recoverable, since it precedes the freeze).
  - **Stability filter**: retain H iff `N(H) > 0 ∧ N₁(H) > 0 ∧ N₂(H) > 0`.
  - **Selection**: `H* = argmax_H min(N₁(H), N₂(H))` over retained H; ties to the
    smaller H.
  - **Empty-set rule**: if nothing is retained, emit `B2_NO_ROBUST_HSTAR`, write the
    frozen-selection record with `h_star = null`, and **skip Steps 3–5 entirely** —
    no TEST quantity is ever computed. The Tier-B slot is consumed; G2 routing falls
    to EXP-038.
  The full {4,6,8,12} × {N, N₁, N₂} table is disclosed regardless of the pick.
  The `s_entry(H)` attribution map is never consulted.
- **Why this method**: the max-min worst-half criterion directly targets the
  EXP-033 `h_star_stable = false` fragility — it selects for the H whose worst
  chronological half is best, rather than a noise-dominated argmax. Point estimates
  only; no new test family (the predeclared filter and argmax are selection rules,
  not inference).
- **Simpler alternative considered**: keep EXP-033's H\*=8 directly — rejected by
  scope; the disclosed instability is exactly why the operator predeclared a
  robustness tie-break. Plain argmax of N(H) — rejected; reproduces the fragility.
- **Assumptions**: none; deterministic arithmetic on TRAIN events.
- **Expected output**: `results/train_tiebreak.csv` (H × {N, N₁, N₂, retained,
  boundary_spill, per-instrument n}).

### Step 3 — Pyramid policy at H\* (TRAIN-frozen, one-SE rule; R1.6 feasibility)

- **Method**: recompute contained-TRAIN objective net at the chosen H\* under each
  policy ∈ {all_legs, first_leg_only, pyramid_legs_only}. A policy is a candidate
  only if (a) every declared instrument keeps ≥ POLICY_MIN_EVENTS contained-TRAIN
  events (EXP-033 floor) AND (b) **every TEST cell stays non-empty under it**,
  checked from entry attributes only (`is_pyramid_bounce` of TEST events — no TEST
  outcome read; R1.6 pre-freeze feasibility). Bootstrap SE of the best candidate's
  net from the frozen regime-cluster bootstrap (1000 resamples, seed payload
  namespaced "EXP-037"). Select the first candidate in the preference order
  all_legs → first_leg_only → pyramid_legs_only whose net is within one SE of the
  best (EXP-033's one-SE rule, recomputed at the tie-break H\*).
- **Why this method**: scope-mandated; identical to the EXP-033 policy mechanism so
  the freeze is comparable to the disclosed `policy_stable = true` record.
- **Simpler alternative considered**: carry EXP-033's all_legs unconditionally —
  rejected; the scope requires recomputation at the tie-break H\*, which may differ
  from 8.
- **Assumptions**: regime clusters capture within-domain dependence (standing
  EXP-027 calibration).
- **Expected output**: policy nets + SE in `results/train_tiebreak.csv` (policy
  rows); selected policy in the frozen-selection record.

### Step 3b — Pre-TEST synthetic-null calibration and margin (R1.2; before the freeze)

- **Method**: per declared cell, calibrate the frozen bootstrap's small-n Type-I
  behavior on synthetic nulls matched to the cell's TEST structure — **no TEST
  outcome is touched**:
  1. **Structure** (entry attributes only): the TEST stratum's (direction,
     regime_id) cluster sizes under the frozen policy.
  2. **Dispersion** (TRAIN only): from the cell's contained-TRAIN `net_e(H*)`
     values under the frozen policy, demeaned; method-of-moments components —
     `σ_w² = pooled within-cluster variance over clusters with ≥ 2 events`
     (fallback: total variance if none), `σ_b² = max(0, var(cluster means) −
     σ_w² × mean(1/n_c))`.
  3. **Null replicates**: R = 2000; each draws `r_i = a_c + e_i`,
     `a_c ~ N(0, σ_b²)`, `e_i ~ N(0, σ_w²)` (zero true mean) on the TEST cluster
     layout, then runs the frozen 1000-resample regime-cluster bootstrap and
     records `(ci_low_1s, boot_p)`.
  4. **Outputs**: measured null FPR of the uncorrected dual rule
     (`boot_p ≤ 0.05 AND ci_low_1s > 0`); the binding margin
     `m_cell = max(0, Q95 of null ci_low_1s)`; the FPR under the margin rule.
- **Why this method**: percentile bootstraps on few clusters undercover;
  EXP-027's FPR validation was at n≈187 pooled, not ~12-event cells. The margin is
  the smallest mechanical correction that restores ≤ 5% one-sided FPR under the
  matched null without touching the frozen inference tail. Gaussian cluster nulls
  are the standard calibration vehicle here — the question is the bootstrap's
  small-sample coverage geometry, not the return distribution's tails, and TRAIN
  supplies the dependence scale via σ_b/σ_w.
- **Simpler alternative considered**: skip calibration and caveat the verdict —
  rejected; this verdict gates holdout admissibility, so an unmeasured Type-I rate
  is the asymmetric risk. Resampling TRAIN residuals instead of Gaussian draws —
  considered; rejected for determinism/simplicity (12-event cells leave too few
  distinct residuals to vary across 2000 replicates).
- **Assumptions**: the Gaussian cluster model with TRAIN-estimated components is an
  adequate null for coverage calibration (disclosed; components persisted).
- **Expected output**: `results/null_calibration.csv` (per cell: structure,
  σ_b/σ_w, fpr_uncorrected, margin_bps, fpr_with_margin), written **before** the
  freeze; margins embedded in `frozen_selection.json`.

### Step 4 — Freeze-before-TEST assertion (guard 5; the load-bearing control)

- **Method**: write `results/frozen_selection.json` — experiment ID, H\*, policy,
  per-cell calibration margins, per-event stratum manifest (event keys +
  TRAIN/TEST labels), per-cell TRAIN/TEST counts, boundary timestamps, and a
  content hash — **before any TEST outcome is computed**. The TEST stage is a
  separate orchestration function that (a) hard-asserts the file exists and
  parses, (b) reads H\*/policy/margins/membership only from it, and (c) recomputes
  nothing selection-related. Code review point: no TEST-row `net_e` evaluation is
  reachable upstream of this assertion.
- **Recovery semantics (R1.6)**: if `frozen_selection.json` already exists at
  freeze time, the recomputed record must content-hash-match it exactly (hard stop
  on mismatch) — a rerun after a post-freeze crash is therefore not a second
  selection. If `test_verdicts.csv` already exists, the TEST stage refuses to run
  (no second read under any circumstance).
- **Why this method**: this disk barrier is what makes the TEST read one-shot and
  honest; it converts the scope's procedural promise into a checkable artifact.
- **Expected output**: `results/frozen_selection.json` (frozen on emission).

### Step 5 — One-shot TEST inference (frozen machinery; guards 4 applied at the end)

- **Method**: per cell (EURUSD-4h, USTEC-4h, XAUUSD-4h), on the cell's TEST events
  under the frozen H\*/policy: event-weighted mean of `net_e(H*)`; frozen
  regime-cluster bootstrap (1000 resamples; regime clusters resampled within
  direction strata — the single-instrument specialization, EXP-034-identical)
  reporting (a) the **one-sided 95% lower bound** (5th bootstrap percentile — the
  binding bound per the F01 clarification), (b) the two-sided 95% CI (descriptive
  labels only), (c) the **raw one-sided bootstrap p** (share of resamples ≤ 0).
  - **Multiplicity (R1.1)**: the binding family is the **phase-level Holm family**
    (these 3 raw p's + EXP-038's raw p), adjudicated mechanically in the
    checkpoint's `G2-gate-review.md` after both experiments complete. This run
    additionally reports a within-route Holm-3 adjustment as the
    **provisional** flag input — clearly labeled, never final (Holm-3 levels are
    laxer than the phase family's). With 1000 resamples the p resolution (0.001)
    comfortably resolves the smallest phase-family Holm level (0.05/4 = 0.0125).
  - **Provisional route rule**: a cell is `route_pass_provisional` iff its
    within-route Holm-3 one-sided p ≤ 0.05 **and** its one-sided 95% lower bound >
    **m_cell** (the frozen calibration margin, R1.2). Final `EXIT_FH_TEST_PASS`
    status exists only in `G2-gate-review.md`.
  - **Descriptive labels** (non-binding, two-sided CI): EVIDENCE_FOR (CI_low > 0),
    EVIDENCE_AGAINST (CI_high < 0), INCONCLUSIVE_SPANS_ZERO.
  - **Guard 4 — determinism**: same-seed full replay must produce byte-identical
    CSV/JSON outputs; replay flag in `results/run_metadata.json`.
- **Why this method**: distribution-free, dependence-aware, identical to the frozen
  Phase 007/008 machinery — TEST cells are directly comparable to the EXP-030/034
  record. Sign-permutation remains invalid for an absolute (non-paired) mean.
- **Simpler alternative considered**: Wilcoxon signed-rank vs 0 — rejected (assumes
  symmetric i.i.d. differences, ignores regime clustering). Pooled-domain single
  test — rejected; the scope declares per-instrument cells with Holm.
- **Assumptions**: regime-cluster exchangeability within direction strata (standing
  EXP-027 calibration); small-n caveat per the scope's power statement (~12/11/13
  TEST events per cell) — INCONCLUSIVE everywhere is the predeclared honest
  expectation, not failure.
- **Expected output**: `results/test_verdicts.csv` (per cell: n, mean net, one-sided
  lower bound, two-sided CI, raw one-sided p, within-route Holm p, margin,
  `route_pass_provisional` flag, descriptive label); `results/run_metadata.json`
  (replay flag, guard statuses, `g2_adjudication = "PENDING_PHASE_FAMILY_HOLM"` —
  never a `g2_satisfied` flag).

### Step 6 — Descriptive companion: FH(H\*) vs BTC exit on TEST (non-binding)

- **Method**: on the identical TEST events per cell, compute the BTC-exit net
  (`lifetime_bps − RT_cons_i − financing(trigger → completion)`, the EXP-034
  construction) and report it alongside the FH(H\*) net — point estimates only,
  clearly labeled non-binding. No additional test family.
- **Why this method**: this is the capture-efficiency question made visible — did
  the FH exit recover the −27 bps BTC drag on the same out-of-stratum events? It
  contextualizes the verdict without expanding the test budget.
- **Expected output**: comparison columns in `results/test_verdicts.csv`; plot 3.

## Visualisations (3 / 3 budget)

1. **TRAIN tie-break picture**: N(H), N₁(H), N₂(H) vs H ∈ {4,6,8,12} with the
   retained set shaded and H\* marked (plus policy nets at H\* as an inset/panel) —
   shows exactly what the mechanical rule saw.
2. **TEST verdict picture**: per-cell TEST net with two-sided 95% CI and the
   one-sided lower bound marked against the zero line, Holm pass/fail flags
   annotated.
3. **FH(H\*) vs BTC-exit per-cell comparison on TEST** (paired bars, point
   estimates, n labels) — the capture-efficiency read; labeled non-binding.

## Interpretation Guide (predeclared)

- **Supports the hypothesis** iff ≥ 1 cell is finally `EXIT_FH_TEST_PASS` in
  `G2-gate-review.md` (phase-family Holm one-sided p ≤ 0.05 AND one-sided 95%
  lower bound > m_cell) → strict G2 satisfied; the EXP-032 holdout-release
  checkpoint becomes admissible (operator selects one package). This experiment's
  own outputs are provisional until that adjudication. The small-n caveat
  accompanies any pass.
- **Contradicts** iff all three tested cells have two-sided CI_high < 0 on TEST.
- **Inconclusive** iff TEST CIs span zero — the predeclared power-limited
  expectation; routes Phase 008 toward CHARACTERISED_NOT_CONFIRMED via B2 while
  EXP-038 carries the independent A1-cell route. A null here does not refute the
  capture-efficiency mechanism.
- **`B2_NO_ROBUST_HSTAR`** if Step 2's filter empties: no TEST read, slot consumed,
  honest fragility outcome; G2 must route through EXP-038.
- Step 6's comparison is context only — under no outcome does it alter a verdict,
  promote a cell, or justify re-selection. No cost/financing constant is revisited
  under any outcome.

## Implementation Safety Constraints (for `experiment-developer`)

- All quantities in absolute bps against a 0 baseline; no percentage-of-baseline
  metrics; no ratios with near-zero denominators.
- Denominators fixed by guard 2 reconciliation; any count drift is a hard stop.
- Timestamp ordering by `CloseTime` / trigger timestamps; never bar-index alignment
  across views. Binding stratum membership from the trigger close **timestamp** vs
  the 1-minute `train_end_ts` boundary (causal; R1.3); the bar-index cutoff is
  allowed only inside guard 1's EXP-033 reproduction anchor.
- **Stage separation is structural**: TRAIN selection (Steps 1–3b) and TEST
  evaluation (Step 5) are separate functions; the TEST function's only selection
  input is `frozen_selection.json` (Step 4 barrier). No TEST-event `net_e` may be
  computed before the freeze file is written. The TEST stage refuses to run when
  `test_verdicts.csv` already exists; an existing freeze file must hash-match the
  recomputed record (R1.6).
- Calibration (Step 3b) reads TRAIN outcomes and TEST **entry attributes** only;
  seeds namespaced ("EXP-037", "nullcal", ...); R = 2000 replicates with `tqdm`.
- FH returns vectorized as shifted-Close lookups computed once for all four H;
  no per-event Python loops over large frames; the cell loop uses `tqdm`.
- Financing helper reused verbatim from EXP-034 (pure function, fractional calendar
  days including weekends); spot-check one weekend-spanning 4h hold.
- Lazy Polars loading with the standard first-70% pattern; the rebuilt 4h series is
  built once and reused for TRAIN, TEST, and plots; bounded pandas conversion only
  for the 3 plots.
- Bootstrap: one shared resample-index set per stage (TRAIN policy SE; TEST cells),
  seeds namespaced "EXP-037"; 1000 resamples (frozen method parameter).
- No directory creation, data loads, or plotting at import time; helpers return
  data; concise orchestration-level logging only.
- Truncation events (FH window past series end) and boundary-spill counts are
  disclosed columns, never silent.

## Complexity Check

- Statistical test families: 1 / 1 (frozen regime-cluster bootstrap CI + one-sided
  bootstrap p, applied per TEST cell; phase-family Holm adjudicated at G2. Step 2/3
  selections are predeclared mechanical rules on point estimates, not tests; the
  Step 3b null calibration is synthetic-data verification of the same frozen
  family, not a new family).
- Visualisations: 3 / 3.
- New modules: 1 / 1 (orchestration script; `event_method.py` and the EXP-034
  financing helper imported/reused unchanged).
