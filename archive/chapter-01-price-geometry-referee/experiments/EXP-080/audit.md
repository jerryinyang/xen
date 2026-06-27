# Audit Report: Experiment EXP-080 (Phase 018 CF-CAPGEO-001 Substrate/Exit Readiness)

## Summary

- **Verdict**: FAIL (blocking) — two Critical, verdict-material findings; fix + re-execution required before Stage 6.
- **Critical Issues**: 2
- **Warnings**: 1
- **Info Notes**: 3

The implementation is largely clean (holdout-safe, deterministic, causally sound, faithful VAL-005
reuse), but **both verdict-bearing numbers are corrupted or unreliable**:

1. The READY/NOT_READY map (180/192 NOT_READY) is produced by a **mis-denominatored
   dropped-fraction metric** that measures market-session structure, not construction quality —
   the only survivors are the single 24/7 instrument (BTCUSD). **Critical-1.**
2. The `SUBSTRATE_REFUTED` halt is driven **solely** by the null-FPR `n=120` row (wilson_hi 0.0787
   vs gate 0.075), a marginal exceedance at a **bounded probe scale (N_NULL=1000) whose gate
   decision is noise-dominated**, using a floor (`n≥120`) calibrated for a *different* statistic
   (S2). **Critical-2.**

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| run_experiment.py | Correctness (construction metric) | **FAIL** | `construction_integrity` dropped-fraction uses a 24/7 wall-clock denominator (see Critical-1). |
| run_experiment.py | Correctness (null-FPR test) | PASS (impl) / **FAIL (probe scale)** | Bootstrap correctly wired; probe scale makes the binding gate decision unreliable (Critical-2). |
| run_experiment.py | Holdout exclusion | PASS | Only metadata + first-70% via `val005.load_first70`; holdout never materialized. |
| run_experiment.py | Look-ahead / causality | PASS | `entry_invariants` asserts on-close/within-span/causal anchors; 0 invariant failures observed. |
| run_experiment.py | Real-price discipline | PASS | No return/P&L computed; null carrier is the only return series, an explicitly non-tradable centered domain-bar log-return probe. |
| run_experiment.py | Determinism | PASS | nondeterministic_cells=0; two-pass exact equality; seeds recorded in run_metadata.json. |
| run_experiment.py | Loader ordering | PASS | VAL-005 loader sorts by CloseTime before the first-70% slice; no holdout collection. |
| run_experiment.py | Memory/performance | PASS | Per-cell processing; tqdm over 192 cells + null loop; plots from collected summary (no reloads). Holds all 16 analysis frames in `loaded` simultaneously — bounded, acceptable (Info-2). |
| run_experiment.py | Import side effects | PASS | Output dirs created in `main()`; VAL-005 module import is main-guarded/side-effect-free. |
| xen/domain_bars.py | Verbatim VAL-005 promotion | PASS | Byte-identical logic; `regression_check` frame_identical=True (85839 rows, EURUSD-15m). |
| xen/capgeo_substrates.py | Ported detectors / determinism | PASS | AVWAP + EXP-068 harami ports on real OHLC; HA used only for harami detection (no returns); SUB-RANDOM on completed closes only. |

---

## Numerical Validation

### Spot checks

- **Dropped-fraction mechanism (Critical-1).** `construction_integrity`
  (`run_experiment.py:165-168`): `span_minutes=(ep[-1]-ep[0])/60`; `ideal=span_minutes/period+1`;
  `dropped=1-n/ideal`. This is `1 − (realized domain bars)/(windows on a continuous 24/7 clock)`.
  For forex, the weekend share of a 24/7 week is `2/7 = 0.286`; observed forex dropped ≈ 0.30–0.31.
  Empirical confirmation by instrument @15m: **BTCUSD 0.231 (FLAGGED, the only survivor) vs EURUSD
  0.307, GBPUSD 0.304, USDJPY 0.303, XAUUSD 0.338, USTEC 0.327, US500 0.387, JP225 0.441** — a clean
  monotone in market-closed time (24/7 crypto < forex < gold/index < cash-equity index), **not** in
  any construction defect. The **only READY cells are BTCUSD-{15m,1h,4h}** (the single continuously
  traded instrument).
- **Correct definition (precedent).** EXP-048 `run_experiment.py:170`:
  `dropped_fraction = (candidate − retained)/candidate` where `candidate` = clock-grid windows that
  contain ≥1 source bar and `retained` = those passing `min_coverage`. EXP-043 `215-216` computes
  the same via `SourceBars`, and gates the 0.25 FAIL on the **2h domain only** (other domains
  report-only). Under that definition with `min_coverage=0.90`, drops are rare (EXP-043 reported
  0.10–0.26); the frozen `DROP_FAIL=0.25` band was calibrated to it. EXP-080 substituted a different
  denominator, inflating every session instrument past 0.25.
- **Null-FPR rows (Critical-2).** From `null_fpr.json`: n=15 fpr0.110/whi0.131; n=30 0.087/0.106;
  n=60 0.078/0.096 (all `small_n_disclosed`, correctly non-binding post-reconciliation); **n=120
  0.062/0.0787 `operating` → controlled=false (the sole halt trigger)**; n=250 0.046/0.061; n=500
  0.058/0.074; n=2000 0.051/0.066 (all controlled). FPR is monotone-declining in n — the textbook
  percentile-bootstrap small-n under-coverage signature (`ass.moving_block_bootstrap_cis` is a
  5th/95th-percentile bootstrap, `ass.py:534-540`).

### Range / sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| nondeterministic_cells | 0 | YES | Determinism halt leg did not fire. |
| invariant_failure_cells | 0 | YES | ≥3-instrument invariant halt leg did not fire. |
| harami_entry_identity_all_cells | True | YES | Both harami substrates share one detector by construction. |
| regression_check frame_identical | True (85839) | YES | `xen.domain_bars` == VAL-005 build_domain_bars. |
| null-FPR n≥250 wilson_hi | 0.061–0.074 | YES | Controlled at production-relevant n; only n=120 boundary fails. |

---

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

**Readiness map (180 NOT_READY).**

| Stratum | Per-stratum verdict | Agrees with pooled? | Notes |
|---|---|---|---|
| BTCUSD (15m/1h/4h) | READY (dropped 0.23, FLAGGED) | — | Sole 24/7 instrument; the only survivor. |
| All forex (EURUSD…AUDJPY) ×{15m,1h,4h} | NOT_READY via COVERAGE_EXCLUDED | (artifact) | dropped ≈ 0.30 = weekend share; **not** a construction failure. |
| Gold / indices (XAUUSD,USTEC,US500,US2000,JP225) | NOT_READY via COVERAGE_EXCLUDED | (artifact) | dropped 0.33–0.44 = larger session-closed share. |

- Pooled headline: 180/192 NOT_READY. **Is it masking heterogeneity?** No — and that is itself the
  finding: the exclusions are **homogeneously** produced by a single metric artifact (the 24/7
  denominator), cleanly stratified by each instrument's market-open fraction. The per-stratum
  picture does not show genuine per-cell construction failures; it shows the *gate* tracking session
  structure. 0 invariant violations and 0 determinism failures across all 192 cells corroborate that
  construction itself is sound.

**Halt verdict (`SUBSTRATE_REFUTED`).** Re-derived per halt leg: non-determinism leg = not fired
(0 cells); ≥3-instrument same-invariant leg = not fired (0 invariant failures); **null-FPR leg =
fired, solely on the single n=120 row.** The verdict rests on one borderline statistic at one
sample size.

### Mechanism

- **NOT_READY map** is produced entirely by `construction_status == COVERAGE_EXCLUDED`, which is
  produced entirely by `dropped_fraction > 0.25`, which is produced by the 24/7-clock denominator
  counting market-closed time as dropped windows. Driver: the metric, not the data.
- **SUBSTRATE_REFUTED** is produced by exactly one number: the n=120 null-FPR Wilson upper bound
  (0.0787) crossing the 0.075 gate by 0.0037, at a probe scale (N_NULL=1000) whose own noise band
  the code documents as wilson_hi≈0.065 at a true 0.05 rate. The exceedance is ~one noise-unit.

### Gate-shape check

- **Construction gate (0.25 dropped):** wrong instrument for the quantity of interest. It is meant
  to flag aggregation/coverage defects but, as denominatored, measures market-session structure. It
  is structurally blind to the distinction between "poorly constructed" and "trades fewer hours."
  This is "wrong instrument," not "cells genuinely fail construction."
- **Null-FPR gate (wilson_hi ≤ 0.075 at n≥120):** the `n≥120` operating floor was calibrated in
  D0 §D9 for the **S2 separability minority-mass false-flag** statistic (ff 0.040, wilson_hi 0.048
  at n=120), *not* for this moving-block mean-CI percentile-bootstrap FPR. The S1/m_cell machinery
  the EXP-080 probe actually approximates was validated at **N_BOOT=10_000** (D0 §D9: "recomputed
  per realized structure in EXP-083 at N_BOOT=10_000"; FPR 0.050, wilson_hi 0.058). EXP-080 ran a
  **bounded probe** (N_NULL=1000, N_BOOT=2000) explicitly below that scale. Applying a gate
  calibrated for one statistic/scale to a different statistic at a noise-dominated scale is a
  calibration-transfer mismatch — the binding decision is not reliably resolved.

---

## Scope Compliance

- Analysis plan followed: **YES on structure**, with two correctness deviations (Critical-1 metric
  definition; Critical-2 probe scale unpinned and below validated scale).
- Complexity budget: 1/1 test, 4/4 plots, 2/2 modules. Within budget.
- Holdout exclusion verified: **YES** (metadata + first-70% only; regression_check confirms domain
  construction parity; fence applied).
- Entry-count / D7-bracket / harami-identity outputs are computed **independently of readiness
  status** and are therefore **not** corrupted by Critical-1 (they remain valid for re-use), though
  they will be re-emitted on the rerun.

---

## Issues

### Critical

1. **Dropped-fraction metric mis-denominatored against a continuous 24/7 clock (verdict-material).**
   - File: `python/experiments/EXP-080/code/run_experiment.py:165-168` (`construction_integrity`).
   - Description: `ideal = span_minutes/period_minutes + 1`; `dropped = 1 − n/ideal` measures the
     fraction of a continuous 24/7 clock with no domain bar, i.e. market-closed time (weekends,
     sessions), not windows dropped by the coverage filter. Confirmed empirically: BTCUSD (24/7) is
     the only cell under 0.25; all session instruments land at their market-closed fraction
     (~0.30 forex → 0.44 JP225).
   - Impact: flips 45/48 instrument×domain cells (180/192 substrate-cells) to spurious
     `COVERAGE_EXCLUDED → NOT_READY`, corrupting the READINESS_DELIVERED map and the EXP-081
     membership set. The frozen `DROP_FAIL=0.25` band was calibrated against the EXP-043/048
     coverage-based definition, not this one.
   - Fix: compute dropped-fraction the validated way — `(candidate − retained)/candidate` over
     clock-grid windows that contain source data (EXP-048 `run_experiment.py:170`), or equivalently
     via `xen.bar_aggregator.coverage_summary` / `SourceBars` (EXP-043 `215-216`). Reuse the
     validated definition; do not derive coverage from wall-clock span. Re-run.

2. **Null-FPR `SUBSTRATE_REFUTED` halt rests on a noise-dominated boundary decision at an
   unvalidated probe scale, with a floor calibrated for a different statistic (verdict-material).**
   - File: `python/experiments/EXP-080/code/run_experiment.py:104-120, 236-262` (`NULL_NS`, `N_NULL`,
     `NULL_NBOOT`, `null_fpr`); gate at `:552-558`.
   - Description: the sole halt trigger is n=120 (wilson_hi 0.0787 > 0.075). The probe ran at
     N_NULL=1000 / N_BOOT=2000 — explicitly "NOT the production 10_000" (code comment `:98-109`).
     At N_NULL=1000 the gate decision is within the probe's own sampling noise (point FPR 0.062;
     n=250/500/2000 all controlled with declining FPR). The `n≥120` floor was calibrated in D0 §D9
     for the S2 minority-mass false-flag, not this moving-block mean-CI percentile FPR; the m_cell
     machinery this probe approximates was validated at N_BOOT=10_000.
   - Impact: independently sets `SUBSTRATE_REFUTED`; will **reproduce deterministically** on the
     Critical-1 rerun (carrier EURUSD-15m is unaffected by the dropped-fraction fix; SEED_NULL is
     fixed), so fixing Critical-1 alone leaves the experiment SUBSTRATE_REFUTED on this leg.
   - Disposition (governance, not a unilateral re-tune): this is **not** a code-correctness bug and
     must **not** be resolved by raising N_NULL until the gate flips (goalpost-moving, prohibited).
     The probe scale and the criterion-transfer must be **ratified by governance** before the rerun:
     either (a) run the null-FPR machinery sanity at the **validated m_cell scale (N_BOOT=10_000)**
     the criterion references in D0 §D9 — matching the probe to the scale the gate was calibrated
     against (not goalpost-moving; the 0.075 gate is unchanged), so the n=120 decision is
     statistically resolved; or (b) governance affirms the bounded-probe halt as a genuine
     refutation and Phase 018 halts. Route to the pipeline governance gate, not silently to the
     developer.

### Warning

1. **Null carrier includes weekend/session-gap jump returns.**
   - File: `run_experiment.py:454-457` (carrier = centered EURUSD-15m domain-bar log-returns).
   - Description: consecutive domain bars across a weekend produce large jump returns (heavy tails).
   - Materiality: assessed and shown **not** to be the FPR-inflation driver — heavy tails widen the
     bootstrap mean distribution, pushing `CI_low` more negative and *suppressing* `CI_low>0`
     false positives. It is therefore a disclosure/quality note, not the mechanism behind Critical-2,
     and cannot by itself move the verdict toward refute. Worth cleaning (e.g. intra-session returns
     only) when Critical-2 is addressed, but not independently blocking.

### Info

1. **Construction gate applied to all three domains vs EXP-043 precedent (2h-only).** EXP-043 gated
   the 0.25 FAIL on the newly-constructed 2h domain only; the scope here applies it to 15m/1h/4h.
   This is a scope choice, not a bug, but compounds Critical-1's blast radius.
2. **All 16 analysis frames held in memory simultaneously** (`loaded` dict, `:494-501`). Bounded and
   consistent with VAL-005; noted for awareness.
3. **`plt.cm.get_cmap` deprecation** (`:299, 336`) — cosmetic; not result-bearing.

---

## Materiality & Re-Audit Requirements

- **Critical-1** moves the readiness-map deliverable (READY/NOT_READY for 180 cells) and the EXP-081
  membership set → blocking. Fix the dropped-fraction definition (validated coverage-based) and
  re-run.
- **Critical-2** moves the experiment verdict (`SUBSTRATE_REFUTED` vs `READINESS_DELIVERED`) →
  blocking. Requires a **governance ruling** on the null-FPR probe scale / criterion transfer before
  the rerun (do not re-tune to flip). Note its deterministic reproduction means the verdict will not
  change on a Critical-1-only rerun.
- **Confirmed non-issues (cannot move a verdict-bearing number):** holdout exclusion (metadata +
  first-70% only; regression parity), look-ahead/causality (0 invariant failures; causal asserts),
  real-price discipline (no P&L; non-tradable probe), determinism (0 nondeterministic cells; fixed
  seeds), VAL-005 reuse (resolver selection correct; build_domain_bars verbatim; regression
  frame_identical). Entry-count/D7-bracket/harami-identity outputs are readiness-independent and
  uncorrupted.
- **Re-audit on rerun:** confirm (i) dropped-fraction now matches the EXP-048/`coverage_summary`
  definition and the READY map reflects genuine construction quality (expect the great majority of
  session cells READY at `min_coverage=0.90`); (ii) the governance-ratified null-FPR probe disposition
  is implemented exactly as ruled; (iii) entry counts and harami identity reconcile to this run
  (they should be unchanged).

**Routing:** Critical-1 → `experiment-developer` (mechanical fix + rerun). Critical-2 → pipeline
governance gate for a probe-scale/criterion-transfer ruling **before** the rerun.

---

# Re-Audit (post-fix rerun) — 2026-06-22

Both Critical findings were fixed (`experiment-developer`) and the experiment re-run after the
Stage-5 governance ruling on Critical-2 (re-scale to the validated machinery). **Re-audit verdict:
PASS** — both Criticals resolved, the new verdict is sound, no new findings.

## Critical resolution

| Finding | Fix | Confirmed resolved |
|---|---|---|
| **Critical-1** (dropped-fraction denominator) | `construction_integrity` now uses the validated coverage-based `(candidate − retained)/candidate` over fence-eligible, data-bearing period-grid windows (`_candidate_window_count`). | **YES.** New @15m drops: BTCUSD 0.013, EURUSD 0.025, GBPUSD 0.021, XAUUSD 0.020, USTEC 0.002, US500 0.091, JP225 0.161 — coverage-stratified, no longer session-stratified. Only 2/48 cells exceed 0.25 (US500-4h 0.251, JP225-4h 0.281). BTCUSD is no longer the sole survivor. |
| **Critical-2** (null-FPR probe scale) | `N_NULL` 1000→5000, `NULL_NBOOT` 2000→10000 (validated m_cell scale); gate 0.075 and floor n≥120 unchanged. | **YES.** Operating regime (n≥120) all controlled: n=120 wilson_hi **0.0642** (was 0.0787), n=250 0.0680, n=500 0.0657, n=2000 0.0555. The prior n=120 halt was a probe-scale artifact, now resolved. Small-n (n<120) still uncontrolled (0.081–0.091) but correctly `small_n_disclosed` / non-binding. |

## New headline

`verdict=READINESS_DELIVERED`; 184 READY / 8 NOT_READY of 192; nondeterministic_cells=0;
invariant_failure_cells=0; halt_invariant_ge3_instruments=False; null_fpr_uncontrolled_operating=False;
harami_entry_identity_all_cells=True; regression_check frame_identical=True (85839 rows); all 192
substrate-cells IN_BRACKET [15,8000].

## Verdict Forensics (new verdict)

### Per-stratum re-derivation & masking check

- **184 READY** span all 16 instruments × {15m,1h,4h} except the two excluded 4h index cells.
- **8 NOT_READY = 2 unique cells × 4 substrates**: **US500-4h** (drop 0.251) and **JP225-4h**
  (drop 0.281), both `COVERAGE_EXCLUDED` via dropped>0.25, with `invariants_pass=true`,
  `determinism_pass=true`, no invariant violation. These are **genuine 4h coverage-sparsity
  exclusions** for cash-equity indices (session + holiday structure thins 4h grid windows below the
  0.90 coverage threshold), consistent with the EXP-043 precedent (JP225-2h NOT_READY at 0.2566;
  index 2h cells flagged). Not a metric artifact.
- Pooled `READINESS_DELIVERED` is **not masking heterogeneity**: the two exclusions are surfaced
  per-cell (4 substrates each) and correctly stratified to the one domain (4h) and instrument class
  (cash-equity index) where coverage is genuinely thin; READY holds uniformly elsewhere. The
  per-substrate picture agrees (the two harami substrates and SUB-RANDOM share the same cell
  classification; AVWAP too).

### Mechanism

- **READY** is produced by: coverage-based construction integrity PASS (drop ≤ 0.25, fence held) ∧
  0 invariant violations ∧ determinism PASS — exactly the predeclared lenient readiness rule.
- **NOT_READY** (US500-4h, JP225-4h) is produced solely by the coverage drop exceeding the frozen
  0.25 band at the 4h domain; no causal/determinism defect.
- **READINESS_DELIVERED** (not SUBSTRATE_REFUTED): all three halt legs clear — non-determinism 0,
  ≥3-instrument same-invariant 0, null-FPR operating-regime all controlled.

### Gate-shape check

- The 0.25 construction gate now measures the correct quantity (coverage), so it is the right
  instrument for this check. US500-4h at **0.251** is marginally over the frozen 0.25 band — a
  borderline exclusion worth noting for the interpreter (Stage 6), but the band is predeclared and
  must not be retro-edited; recorded as disclosure.
- The null-FPR gate (wilson_hi ≤ 0.075 at n≥120) is now resolved at the validated scale; the small-n
  rows correctly fall outside the binding regime per D0 §D9 / §D6 Guard (i).

## Confirmations (unchanged-good)

Holdout exclusion (metadata + first-70% only; regression frame_identical), look-ahead/causality
(0 invariant failures; causal asserts), real-price discipline (no P&L; non-tradable centered-return
probe only), determinism (0 nondeterministic cells; fixed seeds; second pass exact), VAL-005 reuse
(resolver + verbatim build_domain_bars + regression check) — all still PASS. D7 bracket: 192/192
IN_BRACKET (AVWAP 78–2641; harami/random 284–7657). Harami entry-population identity holds in all
cells (shared detector by construction). Complexity budget unchanged (1 test, 4 plots, 2 modules).

## Re-Audit verdict

**PASS — no Critical, no Warning, no blocking finding.** Both prior Criticals are resolved and the
`READINESS_DELIVERED` verdict is mechanistically sound and not masking heterogeneity. Cleared to
Stage 6 (interpretation). Disclosures for the interpreter: (i) US500-4h coverage drop is borderline
(0.251 vs 0.25); (ii) JP225-4h and US500-4h excluded from EXP-081 with record; (iii) small-n
(n<120) null-FPR inflation persists as the disclosed Phase-017 property (non-binding).
