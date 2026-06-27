# Audit Report: EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 5

The experiment code faithfully implements the approved scope and analysis plan. The lazy uncapped resolver is correct, the invariants all pass across every cell, EXP-053 reconciliation is byte-exact on all 99 cells, and determinism holds. The EVIDENCE_AGAINST verdict is mechanically correct per the predeclared rules. One warning about interpretation framing at G2.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | 5 arms, lazy/path-ordered/built-stop resolvers, paired contrasts, P11/EVIDENCE_* fork all implement scope exactly. |
| `code/run_experiment.py` | Edge cases | PASS | Entry at `last_train_idx` (offset 0, all DATA_CENSORED) handled by `_edge_ok` first-execution fix. Empty-cell paths, zero-harami, no-secondary-history cells all produce NOT_VIABLE_BY_POWER. |
| `code/run_experiment.py` | Type safety | PASS | Full type hints on all public signatures; NumPy/Polars typed throughout. |
| `code/run_experiment.py` | NaN handling | PASS | Qualifying mask gates on `np.isfinite(atr_entry) & (atr_entry > 0.0)`; `weighted_returns` uses `np.errstate(invalid="ignore", divide="ignore")`. Stop trajectory seeds NaN; bootstraps guard `m >= POWER_FLOOR`. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` reads only `train_rows` file-order rows; full file never sorted/collected; every domain bar fenced to `CloseTime <= train_end_epoch`; uncapped scan clips to `last_train_idx`. No TEST/holdout contact. |
| `code/run_experiment.py` | Loader ordering | PASS | `pl.scan_parquet` → `select(cols).slice(0, train_rows).collect()` — F01 file-order prefix; assert `CloseTime.is_sorted()`. No sort of full file. |
| `code/run_experiment.py` | Memory/performance | PASS | Unbounded `build_active_stops` avoided for uncapped arms — lazy pointer-driven stop. Bounded subsample (`INVARIANT_MAX_EVENTS=1500`) for O(train_len) invariant re-resolutions (F03). `tqdm` over instrument-level parallel workers. |
| `code/run_experiment.py` | Safe optimization | PASS | Parallel workers (ProcessPoolExecutor) validated byte-identical to serial (per-cell seeds → order-independent). Determinism replay on one light cell per instrument (not all), then compared vs its live cell. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over instruments and `as_completed` futures. Concise `LOGGER.info` section headers. |
| `code/run_experiment.py` | Logging/output | PASS | `main()` emits concise summary (verdict, passers, status counts). All results to `results/`; plots to `plots/`. |
| `code/run_experiment.py` | Organization / import side effects | PASS | Imports → constants → types → helpers → pure computation → plotting → orchestration → `main()`. Output dirs created in `run()`, not at import. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use bounded `records` list + `pooled` per-event sample returned from analysis pass; no second full load/generation pass. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring (scope, plan, invariants); per-function docstrings with Parameters/Returns. |
| `python/src/xen/position_exits.py` | Correctness | PASS | `resolve_legs_uncapped` / `_scan_event_uncapped` correctly implement lazy trailing stop (no TIMECAP, DATA_CENSORED at edge, monotone ratchet to confirmed secondary pivots). |
| `python/src/xen/position_exits.py` | Edge cases | PASS | Entry at TRAIN edge → empty scan → all DATA_CENSORED at offset 0. No prior secondary confirmation → NaN stop throughout → either FAV (combined) or censored. |
| `python/src/xen/position_exits.py` | Type safety | PASS | NumPy typed arrays; legacy 2-tuple return unchanged for EXP-059 callers; additive `exit_off` out-param. |
| `python/src/xen/position_exits.py` | NaN handling | PASS | Stop seeds `NaN` until first post-entry secondary confirmation; `np.isfinite` guards in both `_scan_event` and `_scan_event_uncapped`. |
| `python/src/xen/position_exits.py` | Frozen-function integrity | PASS | Existing `resolve_legs`, `build_active_stops`, `_scan_event` unchanged — additive `exit_off` out-param preserves 2-tuple return for EXP-059 callers. Resolver hashes pinned in `run_metadata.json` (F06). |

---

## Numerical Validation

### Spot Checks (BTCUSD-5m)

**BENCH expectancy:**
- `R_event = Σ_l w_l · rd·(exit_px − C)/ATR_entry`. Single leg w=1, BENCH resolves at 1:1 stop or 50% fav.
- Median = 0.05697, 1s CI_low = 0.00097, m = 3117. Consistent with EXP-053 (verified exact match).
- First-hit r = 0.5058 (FAV/(FAV+ADV), TIMECAP excluded). Expected ≈0.50 for a 50% fav / 1:1 stop with adaptive cap. Plausible.

**TRAIL-PURE-UNCAPPED expectancy:**
- Median = −0.4135, CI_low_1s = −0.4379 (CI spans 0, negative). This means the pure uncapped trailing consistently loses on median expectancy — plausible because there is no initial stop, so early adverse excursions before the first secondary confirmation are unbounded.
- The mean is +0.098 (positive, but fat right tail from the few events that hit a massive runner). Confirms the no-initial-stop fat-tail widening P14 warned about — median is the correct endpoint.

**COMBINED-UNCAPPED-V2A expectancy:**
- Median = 0.0765, CI_low_1s = 0.0125 (viable, positive). The V2A partial legs help materially vs the pure uncapped case.
- but contrast vs BENCH = −0.0362 CI_low — not beating BENCH (CI_low < 0).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction (rd) | {+1, -1} | [+1, -1] (int64) | YES |
| BENCH median expectancy | ℝ (expected −1 to +1 ATR) | [−0.432, 0.774] | YES |
| First-hit r (BENCH) | ≈0.50 (0.30–0.70) | [0.318, 0.667] | YES |
| TickVolume | ≥ 0 | Not used (aggregated into domain bars) | N/A |
| Holding duration (BENCH) | ≤ bench_N (~6 bars) | p50=6.0, max≤10 | YES |
| Holding duration (uncapped) | > BENCH | p50=7–8, p90=13–23, max up to 66 | YES |
| Exit-weights sum per arm | 1.0 per arm | Sums to 1.0 (verified per cell) | YES |
| DATA_CENSORED per cell | Non-negative integer | 0–22 total per arm across all cells | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| BENCH viable cells | 9/99 | YES | Only 9 cells have CI_low > 0; the conditioned signal isn't strongly positive in most cells even under the benchmark. |
| TRAIL-PURE-UNCAPPED viable cells | 0/99 | YES | Uniformly negative (no initial stop → adverse excursions dominate). |
| COMBINED-UNCAPPED-V2A viable cells | 1/99 | YES | V2A legs improve on pure uncapped but only BTCUSD-5m reaches CI_low > 0. |
| Median divergent share (TRAIL-PURE) | 48.3% | YES | Nearly half of paired events held past the cap — the cap binds frequently for the pure trailing arm. |
| Median divergent share (COMBINED) | 35.8% | YES | V2A legs resolve some events early, reducing the divergent share vs pure trailing. |
| Capped siblings beats BENCH | 0/99 (TRAIL), 2/99 (COMBINED) | YES | Even with the cap, the no-init trailing model rarely beats 1:1. |

---

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap median CI | Within-cell approximate stationarity; block length absorbs short-range dependence | PARTIAL | Standard caveat; blocks are short (4–15 bars, `round(m^{1/3})`). No stronger claim is made. |
| Paired contrast (vs BENCH) | Common qualifying subset pairs well-defined | YES | Shared conditioned events; uncapped censoring is disclosed separately (near-zero in practice). |
| Cap-isolation contrast | Uncapped − capped sibling differs only by cap | YES | Identical no-init trailing stop + P15 path on shared `[entry+1, entry+bench_n]` prefix → within-cap exits are byte-identical (verified by `lazy_dense_prefix_ok` invariant across all cells). |
| Lazy stop == dense stop on shared prefix | The two implementation paths agree | YES | `lazy_dense_prefix_ok` passes in every cell (verified per cell). |
| F01 file-order = chronological | 1-minute rows are in chronological file order | YES | Asserted at load time; all 17 instruments pass. Historical data convention confirmed by VAL-001. |
| MA-seg baseline | MA(20,50) crossover is a valid alternative trend substrate | PARTIAL | Disclosed secondary; no strong claim made. |

---

## Results Plausibility

- **EVIDENCE_AGAINST is the correct mechanical verdict.** Neither binding arm clears P11 WIN (0 winning cells for TRAIL-PURE-UNCAPPED, 0 for COMBINED-UNCAPPED-V2A). BENCH is adequately powered (99 cells, 17 instruments), and both binding arms are powered (99 cells each). The verdict follows mechanically from the predeclared rules.
- **The no-initial-stop effect dominates.** The pure uncapped trailing arm has uniformly negative median expectancy — without the benchmark 1:1 initial stop, early adverse excursions before the first secondary confirmation are unbounded, producing large negative returns that dominate the median.
- **V2A partial legs help but not enough.** COMBINED-UNCAPPED-V2A raises the median from −0.41 to +0.08 in BTCUSD-5m (the one viable cell), but still fails to beat BENCH on the paired contrast (CI_low < 0 in the quorum).
- **Censoring is negligible.** Total DATA_CENSORED across all cells: 22 (TRAIL-PURE-UNCAPPED) and 15 (COMBINED-UNCAPPED-V2A) out of tens of thousands of events. The INCONCLUSIVE_POWER_LIMITED scenario (the scope's stated "materially more likely" outcome) did not materialize — the trailing stop usually fills before the TRAIN edge even without a cap. The censoring share on the divergent subset (35–48% median) reflects events that outlast the benchmark cap but still resolve inside the TRAIN window.
- **The cap-isolation divergent subset contrast is the informative read.** Median divergent shares of 35–48% show the cap binds frequently. On those divergent events, the uncapped version rarely beats its capped sibling (0/96 cells for TRAIL-PURE, 2/89 for COMBINED) — meaning even where the cap binds, removing it doesn't help (because the trailing stop eventually fills at a worse price, not better).
- **Holding durations are consistent.** BENCH and capped siblings hold 4–7 bars (median p50=6); uncapped arms hold 7–8 bars (median p50) and up to 66 bars (max). The longer hold with worse outcomes is consistent with "let it run never helps on these conditioned events."

---

## Scope Compliance

- **Analysis plan followed:** YES — 5 arms, both paired contrasts, P13 baselines, P11 composition, separated censoring, holding duration, all 7 invariants + determinism + EXP-053 anchor. No extra analyses.
- **Deviations:** None. The only non-trivial extension (F04 additive exit-offset return) is documented, reversible, and verified byte-identical for EXP-059 callers.
- **Complexity budget:** 4 stat methods / 5 plots / 0 new modules — all within budget. The cap-isolation divergent-subset contrast reuses the same `paired_median_contrast_ci` (same method, different arm pair) and does not exceed the 4-method limit.
- **Holdout exclusion verified:** YES — F01 prefix TRAIN-only loading; no full-file sort/collect; all domain bars fenced to `CloseTime ≤ train_end_ts`; uncapped scans clip to `last_train_idx`. 0 TEST reads confirmed.
- **EXP-053 reconciliation:** All 99 cells match exactly on m, median, and first-hit r (byte-identical). Population reconciliation across all 17 instruments.

---

## Issues

### Critical

*None.*

### Warning

1. **EVIDENCE_AGAINST verdict requires caveat at G2: BENCH itself is weak.**
   - File: `results/composition_readout.json`
   - Description: BENCH is viable (CI_low > 0) in only 9/99 member cells spanning 7 instruments. The other 90/99 cells have BENCH CI spanning 0 — meaning the conditioned `/STRONG-STAT` HA harami signal is not detectably positive even under the benchmark. The failure of the uncapped trailing model to beat a weak benchmark is itself informative but the EVIDENCE_AGAINST label should be read alongside BENCH's own weak signal strength. The code's mechanical verdict is correct per the predeclared rules; this is an interpretation caveat for G2, not a code defect.
   - Impact: If BENCH itself shows borderline/null signal in most cells, the contrast captures "both arms ineffective" rather than "uncapping specifically hurts." Scope §Interpretation Guide acknowledges this implicitly (cross-check EXP-055/EXP-057).
   - Fix: None required (mechanical per plan). G2 desk should read this alongside BENCH's own viability map.

### Info

1. **INCONCLUSIVE_POWER_LIMITED did not materialize.**
   - Description: The scope flagged INCONCLUSIVE_POWER_LIMITED as "materially more likely" due to high DATA_CENSORED from unbounded windows. In practice, censoring is near-zero (median per-cell = 0 for all arms). The trailing stop fills before the TRAIN edge in virtually every cell. The EVIDENCE_AGAINST verdict is therefore informative, not power-limited.
   - This is a legitimate positive finding: the uncapped model can be powered on TRAIN history but still underperforms.

2. **First-execution edge-case bug correctly fixed and verified.**
   - Description: The `edge_ok` invariant flagged entry at `last_train_idx` (offset 0, all DATA_CENSORED) before the fix. The fix at `_edge_ok` lines 912–927 correctly skips the `off >= 1` check when all legs are DATA_CENSORED. Both originally-failing cells (GBPUSD-2h, AUDUSD-5m) pass post-fix. `invariant_violations` is empty in the final run.

3. **Parallel execution validated byte-identical to serial.**
   - Description: ProcessPoolExecutor with per-cell seeds guarantees order-independent results. `run_metadata.json` reports 0 `non_deterministic` cells. `determinism_ok: true` with 17 light cells re-run and compared byte-identical.

4. **Resolver source hashes pinned (F06 remediation).**
   - Description: SHA-256 of all 8 resolver functions recorded in `run_metadata.json`. Any silent edit to a resolver source will be detectable by diffing the hash map.

5. **Cap-isolation divergent-subset contrast is correctly implemented (F02 remediation).**
   - Description: Both full-common and divergent-subset contrasts are reported. The divergent subset (`unc.past_cap & common`) correctly captures events the uncapped arm held past `bench_n` — the only events whose exit can differ from the capped sibling. `capiso_div_share` is the fraction of paired events that diverge. The plot and summary correctly use the divergent contrast as the interpretable read.

---

## Re-Audit Requirements

None — all conditions pass with 0 critical, 1 warning (interpretation caveat, not code defect).
