# SPDR-012 — compliance trace (design § / RAW § → implementation)

Every binding clause of `python/experiments/SPDR-012/design.md` and every Step-A clause of
`.ignore/what-next/alts/vol-direction-structural-programme-raw.md` mapped to the code or
artifact that implements it. Paths are relative to `python/experiments/SPDR-012/`.

**Deviations: ONE — DEV-1**, operator-signed 2026-07-23 and recorded as **AMENDMENT-T1** in
`design.md` §5: the future-destroy tripwire is demoted from a HARD gate to a report layer.
A second amendment, **AMENDMENT-T2** (DIRECTION: NEUTRAL), records that the §6.4 PASS/STOP
recommendation is not computed and all three candidate bases are reported instead. Both are
machine-readable in `screen_code/config.py:DEVIATIONS` and `results/integrity_selfcheck.json`.

**Nine ambiguity resolutions (IN-1…IN-9)** are recorded in
`screen_code/config.py:INTERPRETATION_NOTES` and mirrored into
`results/integrity_selfcheck.json`. Eight weaken no clause — each is either forced by
causality or emits **both** readings; IN-8 is the note attached to DEV-1 and does change what
a clause tests, which is why it also carries a deviation entry.

This trace was revised after fresh-context QA run 1 (`qa-review.md`, verdict REVISE). Findings
F-3 and F-5…F-13 are fixed in code; F-1/F-2 became DEV-1/AMENDMENT-T1; F-4 became
AMENDMENT-T2.

---

## 1. Scope fence (design §0)

| Clause | Implemented |
|---|---|
| Vehicle = vectorised Python on fenced catalog, no Nautilus, no estimand gate | `screen_code/catalog_io.py:63` `load_minute_bars` (parquet + fence assert); no `xen.adjudication` import anywhere in `screen_code/` |
| DESIGN band `[2021-06-29T06:53Z, 2023-03-01Z)` | `screen_code/config.py:41-42`; split at `screen_code/pipeline.py:59` `_split_bands` |
| CONFIRM band `[2023-03-01Z, 2023-12-18Z)`, verification read only | `screen_code/config.py:43-44`; frozen-model scoring `screen_code/pipeline.py:190-198`, `pipeline.py:236-244` |
| TEST `≥2023-12-18` never | `screen_code/config.py:45`; asserted `run_screen.py` check `7.1b` |
| Holdout `≥2025-01-08` never | `catalog_fence.assert_within_fence` refuses; asserted `run_screen.py` check `7.2` |
| Symbols = top 25 by 30d USD volume, family pin | `screen_code/universe.py:56` `recompute_universe` + `universe.py:87` `assert_pin` (aborts on mismatch) |
| Clocks H1/H4/D1 all primary, full arm suite each | `screen_code/config.py:58-66`; task grid `run_screen.py:main` (`25 × 3 = 75` cells) |
| Warm-up ≥ max(60 D1, 60 H4, 120 H1) complete bars | `screen_code/config.py:60-68` + `screen_code/features.py:145-156` (60 calendar days **and** the per-clock bar count) |
| Complexity 8 arms × 3 clocks, no post-outcome arm invention | `screen_code/arms.py:ARM_FUNCS` (7 per-cell arms) + `screen_code/cross_section.py` (V-XS); arm list frozen before the run |
| SPREAD-COST-DISCLOSURE emitted wherever bps appear | `screen_code/config.py:131` → `results/integrity_selfcheck.json.spread_cost_disclosure`; repeated in `screen.md` and `analysis.md` |
| Battery / derangement applies | `screen_code/controls.py` (200-seed circular shift, 2000-seed derangement) |
| Future-destroy tripwire in characterisation form | `screen_code/controls.py` `future_destroy_layer` — **report layer, not a gate**, per AMENDMENT-T1; summarised non-gating in `results/integrity_selfcheck.json.report_layers` |

## 2. Frozen definitions (design §3)

| Clause | Implemented |
|---|---|
| `open_ts = ts_event − 1m`; slots = `open_ts.truncate(clock)` | `screen_code/catalog_io.py:161-166` |
| Complete iff last print == `slot_end` **and** coverage ≥ H1 48 / H4 192 / D1 1000 | `screen_code/catalog_io.py:181-187`, floors `config.py:59-63` |
| Incomplete bars counted, excluded from forecasts | `aggregate_clock` retains them with `complete=False`; `build_features` filters (`features.py:70`); counts in `results/cell_diagnostics.json` |
| `r_i = log(C_i/C_{i-1})`, `rv_cc = r²` | `screen_code/features.py:88-90` |
| `rv20` = sqrt(mean of 20 squared returns) | `features.py:92`, window `config.py:77` |
| `parkinson`, `gk` (0 on invalid OHLC) | `features.py:95-105` |
| `abs_oo` = `1e4·|O_{i+1}/O_i − 1|` bps | `features.py:113-114` (`oo_move`) |
| `rv_next` = rv20 at end of bar i+1 | `features.py:117-118` |
| Lag rule: features ≤ i; targets use bar i+1 only | `features.py` module docstring + `run_screen.py` check `7.4` |
| Origin timestamp = `slot_end_i`; drop terminal bar | `features.py:150-156` (`is_origin` requires a finite target) |

## 3. Arms (design §4, all mandatory — AMENDMENT-A2)

| Arm | Implemented | Primary metric emitted |
|---|---|---|
| **V-PERSIST** | `arms.py:93` | `autocorr_abs_r_lag{1,2,3,5}`, `autocorr_rv20_lag{1,2,3,5}`, `ar1_slope_abs_r`, `half_life_abs_r_bars`, `ic_lag1_rv20_vs_target` (+CI, band), HAR ridge+OLS `oos_ic`/`oos_r2_vs_uncond` |
| **V-LEVEL** | `arms.py:180`, models `pipeline.py:154-176` | EWMA(λ=0.94), OLS, ridge(α=1.0) × targets {next `abs_oo`, next `rv20`}: `oos_ic` (+CI, **band cell**), `oos_mae`, `dmae_vs_uncond`, `oos_r2_vs_uncond` |
| **V-REGIME** | `features.py:184` `add_regime_states` + `arms.py:240` | `gap_high_low_bps` (+CI, band), means/medians per state, `p_high_given_high`, `p_low_given_low`, `state_frac_high`, `ic_state_vs_target` |
| **V-REGIME-HMM** | `hmm.py` (Baum-Welch + causal forward filter), driven at `pipeline.py:218`; metrics `arms.py:247` | same gap metrics + `agreement_with_markov`, `hmm_sigma_high/low`, `hmm_p_stay_high/low` |
| **V-MEASURE** | `arms.py:277` | pairwise `rankcorr_*`, `ic_{rv20,parkinson,gk,ewma_vol}_vs_target` (+CI, band), single-measure ridge `oos_ic`/`oos_mae` per target |
| **V-CLOCK** | dummies `pipeline.py:91`, models `pipeline.py:166-176`, metrics `arms.py:310` | `oos_r2_vlevel_only`, `oos_r2_vlevel_plus_{session,dow,session+dow}`, `incr_r2_*`, `mean_resid_session_*`, `mean_resid_dow_*` |
| **V-XS** | `cross_section.py` | `mean_abs_oo_tercile_{0,1,2}`, `xs_gap_top_minus_bottom_bps` (+CI, band), `xs_ic_rank_vs_target`; POOLED row explicitly disclosure-only |
| **V-TAIL** | `arms.py:368` | `p90/p95_abs_oo_{high,low}_bps`, `exceed_p{90,95}_{high,low}`, `exceed_diff_p{90,95}` (+CI) |

Multiplicity: `8 arms × 3 clocks × 25 symbols` disclosed in `screen.md`; every cell is emitted
to `results/metrics_by_cell.parquet` (nothing hidden behind a pooled count, L-03).

### Universe pin (design §0.1 / AMENDMENT-U1)

`screen_code/universe.py` recomputes `sum(close×volume)` on fenced 1m bars over
`[2023-11-18, 2023-12-18)` across **all 903 readable catalog symbols** and asserts set equality
against **both** pin files (`docs/signal-registry/candidate-families/cf-voldir-001-universe.json`
and `results/universe_top25.json`). Result: exact match, recorded in
`results/universe_recomputed.json`. A mismatch raises `UniversePinMismatch` and aborts.

## 4. Controls + tripwire (design §5)

| Control | Implemented | Pins honoured |
|---|---|---|
| `TIME-SHUFFLE-PREDICTORS` | `controls.py:144` | destroy form CIRCULAR_SHIFT by `U{1..n-1}`, targets fixed, seeds **101–300** (200), collapse fraction + envelope emitted |
| `TARGET-LABEL-DERANGEMENT` | `controls.py:166` | DERANGEMENT inside symbol × calendar-month blocks, **zero fixed points asserted** (`controls.py:90-96`, L-28), seeds **31000–32999** (2000-seed upgrade taken — wall clock under the design's 30-min ceiling), one-sided p + collapse fraction |
| `UNCONDITIONAL-MEAN-BASELINE` | `models.py:69` (expanding fit-window mean) → `arms.py:166-176` | ΔMAE with date-block CI + ΔR² per model/target |
| Bite / MDE plant (+0.25 rank corr) | `controls.py:100` `plant_feature` (Gaussian-copula inverse), checked at `controls.py:204` | plant must be destroyed by **both** destroy forms; achieved plant IC reported |
| `TARGET-FUTURE-DESTROY` — **report layer, not a gate** (AMENDMENT-T1) | `controls.py:future_destroy_layer` → `results/controls.json.*.TARGET-FUTURE-DESTROY_REPORT_LAYER`; summarised non-gating in `results/integrity_selfcheck.json.report_layers` | `observed / ideal / interpretation`, no `pass` field. Reference bars are expressed in units of the destroyed null's own dispersion (z ≤ 3 / z ≥ 3), so no bespoke IC constant is asserted (QA F-3). Both destroy forms reported. |

## 5. Units, inference, bands, power (design §6)

| Clause | Implemented |
|---|---|
| UNIT-PIN — target already in bps, no ATR divisor | `config.py:142` `UNIT_PIN`; emitted in the self-check |
| Per-symbol before pooled; pooled disclosure-only | every metric row is keyed `(symbol, clock, band)`; only V-XS emits a `POOLED` row, labelled disclosure-only (`cross_section.py:104`) |
| Date-block bootstrap, blocks 1/3/7, seeds 101/211/307/401/503, 10k resamples | `config.py:98-100`; engine `stats_core.py:block_bootstrap`; the full 15-cell grid is emitted per bootstrapped metric to `results/ci_grid.json` (QA F-6 — it was computed and discarded in the first run) |
| OOS protocol — expanding window, initial fit 40%, monthly re-fit | `models.py:69` `walk_forward_predict`; `pipeline.py:82` `_initial_fit_index` (see IN-1) |
| Chronological DESIGN thirds | `arms.py:406` `stability_rows` — **both** calendar and sample thirds (see IN-2) |
| Interpretation bands (labels, never gates) | `stats_core.py` `band_ic` / `band_gap` — literal design thresholds, unmodified; disclosure companions `band_ic_detected` / `band_gap_detected` emitted in the separate `band_label_detected` column (see IN-9) |
| CI envelope vs SE conservatism | `ci_low`/`ci_high` are the min/max over the 15 (block × seed) cells — a conservative **envelope** of 95% CIs, not itself a 95% interval; `se` is now the **max** SD over the same grid (was the median) so the MDE test matches the envelope, with `se_median` emitted alongside (QA F-11) |
| MDE(IC) ≈ 1.5/√n_eff, n_eff ≈ unique dates | `stats_core.py:267` `mde_ic`; gap MDE = 2.8·SE (`mde_from_se`) |
| UNPOWERED labelled, never folded into a negative | band functions return `UNPOWERED`; thin cells still emit their numbers |

## 6. Integrity checklist (design §7) and golden traces (design §8)

| Clause | Artifact |
|---|---|
| §7.1 every query TRAIN; max target ts < `train_end_utc` | `results/integrity_selfcheck.json` check `7.1` (+ `7.1b` for the TEST boundary) |
| §7.2 no row ≥ `holdout_start_utc` | check `7.2` |
| §7.3 CONFIRM not in estimation coefficients | check `7.3` — every model's `final_fit_end_ts` ≤ DESIGN end |
| §7.4 features ≤ origin; targets next bar only | check `7.4` — `target_slot_start ≥ slot_end` on every emitted origin |
| §7.3b DESIGN target **exit** price is inside DESIGN | check `7.3b` (added by AMENDMENT-T1; QA F-7) |
| §7.5 derangements have 0 fixed points | check `7.5` — **measured** count across the whole seed battery, expected exactly 0 (QA F-10; assertions are stripped under `python -O`) |
| §7.6 write `results/integrity_selfcheck.json` with all asserts PASS | the file itself |
| §8 G1 BTCUSDT H4 rv20 by hand (rel 1e-9) | `results/golden_traces.json.G1` (21 closes + 20 log returns listed) |
| §8 G2 ETHUSDT H1 origin feature vector, no target leakage | `results/golden_traces.json.G2` |
| §8 G3 SOLUSDT time-shuffle seed 101 moves the IC | `results/golden_traces.json.G3` |

## 7. Interpretation notes (ambiguity resolutions — no clause weakened)

| ID | Clause | Resolution |
|---|---|---|
| IN-1 | §6.2 "first 40% DESIGN for initial fit" | Calendar reading is empty for every symbol (catalog carries a trailing 4-year cap; earliest 1m bar is 2022-07-15 except MATICUSDT). Initial fit = first 40% of each cell's own scored DESIGN origins. |
| IN-2 | §6.2 chronological DESIGN thirds | **Both** emitted: literal calendar thirds and equal-elapsed sample thirds. |
| IN-3 | §5 time-shuffle | Circular shift applied to the OOS prediction series against fixed targets — identical to shifting the feature rows with the model frozen. |
| IN-4 | §6.2/§6.3 which CI assigns the band | Worst case over the 3 blocks × 5 seeds (min CI low, max CI high); full grid emitted. |
| IN-5 | §3.3 "next bar" when the next complete bar is not adjacent | Literal text implemented; `next_contiguous` / `target_contiguous` flags and the contiguous fraction disclosed per cell. **Measured (QA F-8, the earlier "≈1.00" was wrong):** DESIGN median 0.949, min 0.636; CONFIRM median 0.979, min 0.598 — so 5–36% of targets span a longer-than-clock horizon on the thinnest cells. A `target_contiguous_frac` row and an `oos_ic_contiguous_subset` row are now emitted per primary cell so the confound is directly checkable; QA measured the contiguous-subset IC (median 0.237) against all rows (median 0.245) and it does not inflate the headline. |
| IN-6 | §4 V-REGIME-HMM "on r or rv20" | Fitted to the clock log-return series with state-specific (μ, σ²); HIGH = larger σ. |
| **IN-7** | §3.2 vs §3.3 target indexing | §3.2 writes `abs_oo_i = 1e4·\|O_{i+1}/O_i − 1\|`, but `O_{i+1}` is the traded price **at** the origin instant `slot_end_i`, so that quantity is already known at origin i. §3.3 ("Target = next bar's `abs_oo`") and §7.4 ("targets use next bar only") force the causal reading: the target for origin i is the move realised over bar i+1, entered at `O_{i+1}`. Implemented as `target_abs_oo_i = oo_move_{i+1}`; the origin-known variant `oo_move` is still emitted per row for disclosure. |
| **IN-8** → **DEV-1 / AMENDMENT-T1** | §5 tripwire "must collapse" | Two independent defects: the pinned block-restricted destroy cannot be adjudicated for collapse (it leaves the between-month component intact, so its null median rises with the true relationship — 0.109 against a live 0.259, failing 33/90 cells including the strongest), and **no** outcome-side destroy can detect look-ahead (`E[Spearman(pred, deranged y)] = 0` for any fixed predictor, so a re-specified unrestricted version passes 90/90 and carries no information). **Operator decision 2026-07-23:** demote to a **report layer** with no `pass` field rather than keep a hard gate. Both destroy forms still run at 2000 seeds. The no-leak claim rests on the §7 construction asserts and the independent QA re-derivation of the walk-forward path. |
| **IN-9** | §6.3 UNPOWERED clause | The clause fires on the *prospective* MDE (>0.10), which the realised DESIGN sample cannot clear (~100 unique dates after the history cap). The literal label is what counts and is emitted as `band_label`; a disclosure companion `band_label_detected` (UNPOWERED only when the observed effect is below its own detection floor) sits beside it so the operator sees both. No cell is dropped or re-labelled. |

## 8. RAW brief Step-A coverage (`vol-direction-structural-programme-raw.md`)

| RAW clause | Where |
|---|---|
| §3 Step A "evaluate/quantify how reliably volatility can be predicted or modelled" | the whole screen; headline objects `oos_ic`, `dmae_vs_uncond`, `gap_high_low_bps` |
| §3 Step A "standardise definitions (raw level vs regime; horizon; instrument class; lag/causality)" | design §3 frozen definitions → `features.py`; horizons = H1/H4/D1; instrument class = top-25 Bybit USDT perps; causality asserted §7 |
| §3 Step A "quantify reliability with predeclared metrics (not a single 'looks clustered' narrative)" | 8 arms, every metric predeclared in design §4/§6 before execution |
| §3 Step A "stop the programme branch if volatility is not reliable enough" | design §6.4 PASS/STOP recommendation computed in `analysis.md`; operator decides |
| §3 Step A "no direction model, no combination, no tradability claim" | no direction arm, no combination arm, no P&L object anywhere in `screen_code/` |
| §5.1 axis — persistence / clustering | V-PERSIST |
| §5.1 axis — level forecasting (OLS/ridge on lagged RV, HAR-RV, EWMA/RiskMetrics) | V-LEVEL + V-PERSIST HAR |
| §5.1 axis — regime models (2–3 state Markov; HMM on returns or RV) | V-REGIME (2-state Markov on rv20) + V-REGIME-HMM (2-state Gaussian HMM) |
| §5.1 axis — realised vs range-style (realised range, Parkinson, Garman–Klass, close-to-close) | V-MEASURE |
| §5.1 axis — calendar / clock effects (UTC session, day-of-week) | V-CLOCK |
| §5.1 axis — cross-sectional rank | V-XS |
| §5.1 axis — distributional / tail | V-TAIL |
| §5.1 metric — OOS R² / rank-IC / MAE on next-horizon RV or \|move\| | `oos_r2_vs_uncond`, `oos_ic`, `oos_mae` on both targets |
| §5.1 metric — regime hit-rate only secondary; primary = state-conditional magnitude separation with CIs | `gap_high_low_bps` + CI is the regime headline; persistence probabilities are secondary rows |
| §5.1 metric — stability across time thirds and symbols | `STABILITY` rows + per-symbol reporting throughout |
| §5.1 metric — collapse under time-shuffle / label-shuffle controls | `results/controls.json` |
| §5.1 metric — minimum useful horizon where predictability clears noise | H1/H4/D1 compared cell by cell in `screen.md`/`analysis.md` |
| §4 universe = current top 25 by 30-day USD volume, TRAIN-only, not re-ranked after outcomes | `universe.py` recompute + pin assert; ranking window frozen in `config.py:51-52` |
| §6 refusals — no breakout direction device, no win-rate, no combination, no indicator zoo, no TEST/holdout, partial-cost caveat | none present; caveat emitted with every bps figure |

## 9. Deliverables (design §9)

| Artifact | Path |
|---|---|
| Screen code | `screen_code/` (13 modules) |
| Per-origin forecasts + features | `results/vol_reliability.parquet` |
| Per-cell metrics | `results/metrics_by_cell.parquet` |
| Control envelopes | `results/controls.json` |
| Integrity self-check | `results/integrity_selfcheck.json` |
| Universe recompute + pin check | `results/universe_recomputed.json` |
| Golden traces | `results/golden_traces.json` |
| Cell diagnostics + model log | `results/cell_diagnostics.json` |
| Cross-sectional panel | `results/xs_panel.parquet` |
| Block × seed CI grid | `results/ci_grid.json` |
| Fresh-context QA review | `qa-review.md` |
| Neutral screen summary | `screen.md` |
| Full-facet analysis + PASS/STOP recommendation | `analysis.md` |
