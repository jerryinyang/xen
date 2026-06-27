# Analysis Plan: Experiment EXP-034 — Per-Instrument Cost-Bearing Tradability Screen (with Financing)

## Objective

Determine, with FWER ≤ 0.05, whether any D0-declared instrument×domain cell —
EURUSD-4h (primary), USTEC-4h, XAUUSD-1h, in fixed-sequence order — retains
positive **net** per-event expectancy on the full first-70% analysis set under the
frozen EXP-030 CONSERVATIVE cost model **plus** the predeclared financing layer.
This is the strict-gate (G2) vehicle for any holdout-release discussion. A pass on
EURUSD-4h is the live question; the power statement in scope predeclares USTEC-4h
as likely unresolvable and XAUUSD-1h as likely failing.

## Data Wiring

- `EXP-022/results/lifetime_observations.csv`, `role = event`,
  `reportable_event = true` — the exact EXP-028/030 PRIMARY event population
  (pyramids included). Cell populations must reconcile **exactly**: EURUSD-4h 39,
  USTEC-4h 36, XAUUSD-1h 207 (and all 12 cells against EXP-030
  `net_by_instrument.csv` `n_events`).
- `EXP-020/results/avwap_events.csv` — trigger timestamps (1:1 join on
  instrument/domain/regime_id/trigger index/pyramid flag; zero unmatched rows,
  hard assert).
- Rebuilt domain series (EXP-031-identical) — completion timestamps at
  `completion_idx`. Open-ended lifetimes (no completion inside the analysis set)
  are handled exactly as EXP-030 handled them; the no-financing reconciliation
  guard (Step 1) enforces equivalence, making the handling self-verifying.
- Frozen `event_method.py` inference tail, pinned hash `e50873d12a9f68d9`.
- Frozen constants: RT_cons = {EURUSD 3.0, USTEC 5.0, XAUUSD 6.0, BTCUSD 16.0} bps;
  financing rates = {EURUSD 0.6, USTEC 1.2, XAUUSD 1.2, BTCUSD 10.0} bps/calendar
  day, adverse-side.

## Methodology

### Step 1 — Reconciliation guards (hard gate before any verdict computation)

- **Method**: (a) per-cell event counts == EXP-030, exact, all 12 cells; (b) the
  **no-financing** per-cell net (`lifetime_bps − RT_cons_i`, event-weighted mean)
  reproduces EXP-030 `net_by_instrument.csv` `net_cons_bps` to ≤ 0.01 bps, all 12
  cells; (c) frozen-tail hash pin; (d) **CI reconciliation (F04, 2026-06-10)**:
  for the declared cells, the no-financing bootstrap run with EXP-030's own seed
  payload (`seed_for("EXP-030", "perinst", domain, inst)`) must reproduce EXP-030
  `net_cons_ci_low/high` to ≤ 1e-6 bps — pinning the verdict-bearing CI estimator
  (and the power statement's borrowed half-widths) to the EXP-030 construction,
  not just the point.
- **Why this method**: the experiment's only new computation is financing; proving
  everything upstream is bit-compatible with EXP-030 isolates the new layer and
  inherits EXP-030's audit.
- **Simpler alternative considered**: reconcile declared cells only — rejected;
  the all-12 disclosure table is also a deliverable and must sit on verified
  numbers.
- **Assumptions**: none beyond artifact integrity.
- **Expected output**: `results/reconciliation.csv`, PASS required to proceed.

### Step 2 — Financing layer (the single new computation)

- **Method**: per event,
  `financing_e = rate_i × elapsed_calendar_days(trigger_time, completion_time)`,
  fractional days from rebuilt-series timestamps (weekends/closures included —
  accurate and conservative versus bar-count approximation; triple-swap averaged
  into the daily rate). `net_e = lifetime_bps_e − RT_cons_i − financing_e`.
- **Why this method**: deterministic, per-event, duration-faithful; matches the
  design's predeclaration exactly.
- **Simpler alternative considered**: flat per-domain financing constant (rate ×
  median hold) — rejected; duration varies widely within 4h cells and a constant
  would understate the cost of exactly the long-duration events financing exists
  to penalize.
- **Assumptions**: the adverse-side daily rate bounds the realized swap regardless
  of position direction (conservative by construction).
- **Expected output**: per-event net arrays; `results/financing_disclosure.csv`
  (per cell: median/IQR holding days, mean financing bps, financing share of total
  cost) — descriptive context for interpretation.

### Step 3 — Per-cell inference (frozen machinery, absolute estimand)

- **Method**: per declared cell, the frozen regime-cluster bootstrap (1000
  resamples; regime clusters resampled within direction strata — the single-
  instrument specialization of the frozen (instrument, direction) strata) on the
  event-weighted mean of `net_e`, reporting (a) the **one-sided 95% lower bound**
  (5th bootstrap percentile) — the BINDING bound at the declared one-sided
  α = 0.05 (F01 clarification, 2026-06-10: the two-sided 95% CI's 2.5th percentile
  would be an undeclared one-sided 0.025 test, halving the level D0 §1.2's
  test-choice argument assumed); (b) the two-sided 95% CI — descriptive, for
  EXP-030 comparability; and (c) the **one-sided bootstrap p** (share of resamples
  with mean ≤ 0) — the EXP-030 absolute-estimand substitution; sign-permutation
  remains invalid for an absolute (non-paired) mean.
- **Why this method**: distribution-free, dependence-aware, and identical to the
  Phase 007 precedent, so cells are comparable to the EXP-030 record.
- **Simpler alternative considered**: Wilcoxon signed-rank against 0 — rejected;
  assumes symmetric i.i.d. differences and ignores regime clustering. t-test —
  catalog "methods to avoid".
- **Assumptions**: regime clusters capture the within-cell dependence (standing
  EXP-027 calibration); no normality/stationarity assumed.
- **Expected output**: per-cell effect, CI, raw one-sided p, n — for the 3
  declared cells (binding) and all 12 cells (descriptive, clearly labeled
  non-binding).

### Step 4 — Fixed-sequence verdict walk (D0 §1.2, LOCKED)

- **Method**: test EURUSD-4h at one-sided α = 0.05 (PASS iff bootstrap p ≤ 0.05
  AND one-sided 95% lower bound > 0 — the dual requirement at the declared level);
  only on PASS proceed to USTEC-4h; only then XAUUSD-1h. Stop at first failure;
  unreached cells are `NOT_TESTED_SEQUENCE`. Labels: `SEQUENCE_PASS_ALPHA05`
  (reached + dual pass); otherwise the descriptive two-sided-CI label —
  `EVIDENCE_AGAINST` (CI_high < 0), `EVIDENCE_FOR` (CI_low > 0),
  `INCONCLUSIVE_SPANS_ZERO`. Additionally emit the lenient G1 continuation flag
  per declared cell (point > 0 AND CI not entirely below 0).
- **Why this method**: fixed-sequence controls FWER at exactly α with maximal
  power on the a-priori-ordered primary — the D0-recorded rationale.
- **Simpler alternative considered**: Holm-3 — rejected in D0 §1.2 (recorded
  pre-measurement): it taxes the primary cell's α by 3× for no error-rate benefit
  given the disclosure-derived ordering.
- **Assumptions**: the ordering was fixed before measurement (D0, 2026-06-10) —
  the validity condition of fixed-sequence testing.
- **Expected output**: `results/sequence_verdicts.csv`; `results/run_metadata.json`
  carries `a1_strict_pass` and `g2_admissible: false` with the §8.4-amendment note
  (F02, 2026-06-10): an A1 strict pass is necessary-but-not-sufficient for holdout
  release — A1 selects its family from EXP-030 disclosures and tests on the same
  analysis data, so the pass routes the cell into a one-shot Tier-B TEST-stratum
  confirmation, and only that TEST result satisfies G2.

### Step 5 — Determinism and seed robustness

- **Method**: same-seed full replay (byte-identical outputs) + 8-seed bootstrap
  re-run disclosing CI-boundary stability for the declared cells (the EXP-030
  Revision-1 disclosure pattern, kept as standing practice).
- **Expected output**: replay flag + `results/seed_robustness.csv`.

## Visualisations (3 / 3 budget)

1. **Declared-cell net with 95% CI vs the zero line**, sequence order annotated —
   the verdict picture.
2. **Financing-impact waterfall per declared cell** (gross → −RT → −financing →
   net) — shows what the new layer did.
3. **All-12-cell descriptive map** (net point + CI, declared cells highlighted) —
   the disclosure context; explicitly labeled non-binding.

## Interpretation Guide (predeclared)

- EURUSD-4h SEQUENCE_PASS_ALPHA05 ⇒ A1 strict pass: the cell earns a one-shot
  Tier-B TEST-stratum confirmation; G2 (and EXP-032 admissibility) is decided by
  that confirmation, not by this in-sample pass (design §8.4 as amended
  2026-06-10). The n=39 caveat must accompany any such read — the cell is small,
  and the holdout shot remains the only true out-of-sample arbiter.
- EURUSD-4h INCONCLUSIVE_SPANS_ZERO with point > 0 ⇒ G1-lenient continuation: the
  cell stays alive for Tier-B composition, but G2 is not met from A1; emphasis
  shifts to the Tier-B variants.
- EURUSD-4h EVIDENCE_AGAINST ⇒ financing erased the headroom; with the other two
  cells predeclared as long shots, A1 effectively closes the per-instrument lever
  and the phase outcome leans on B1/B2.
- USTEC-4h/XAUUSD-1h outcomes are read strictly within their predeclared power
  expectations; an INCONCLUSIVE there is confirmation of the power statement, not
  new information.
- Under no outcome is any non-declared cell promoted, and under no outcome is any
  cost or financing constant revisited.

## Implementation Safety Constraints (for `experiment-developer`)

- All quantities in absolute bps against a 0 baseline; no percentage-of-baseline
  metrics; no ratios with near-zero denominators.
- Denominators: per-cell event counts are fixed by the Step-1 reconciliation; any
  count drift is a hard stop, not a warning.
- Timestamp joins by `CloseTime`-derived event timestamps; never bar-index
  alignment across views.
- The financing helper is a pure function (timestamps in, bps out) shared verbatim
  with EXP-033/035 implementations; unit-test it on a handful of hand-computed
  durations including a weekend-spanning 4h hold.
- Lazy Polars loading with the standard first-70% pattern; no full-data collection
  before the analysis cutoff; bounded pandas conversion only for the 3 plots.
- `tqdm` over the 12-cell loop; concise logging; helpers return data.
- Verdict computation reads only frozen constants and Step-3 outputs; no
  result-aware branching anywhere upstream of `sequence_verdicts.csv`.

## Complexity Check

- Statistical test families: 1 / 1 (regime-cluster bootstrap CI + one-sided
  bootstrap p, applied per cell in sequence).
- Visualisations: 3 / 3.
- New modules: 1 / 1 (orchestration script + shared financing helper).
