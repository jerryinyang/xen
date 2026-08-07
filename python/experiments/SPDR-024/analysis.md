# SPDR-024 — analysis of the AMENDMENT-7 TRAIN re-emission

- **Experiment:** `SPDR-024` — SIZE-only volatility adaptive management on a fixed breakout substrate
- **Family / registration:** trade-opportunity-capture geometry (checkpoint `2026-07-25-018`)
- **Band:** TRAIN only. No TEST or holdout path was opened for this record.
- **Cells:** four independent cells — `ctrader|crypto` × `H1|H4` (never pooled across universe or domain)
- **PRIMARY estimand:** capital-normalised episode return (E6); per-notional bps is diagnostic only and barred from sizing claims
- **Devices:** SIZE only (`STATE_HALVE_HIGH` on eight components; continuous `SCALE_NORMALISED` on `RANGE_SCALE` and `SWING_SCALE`). No HOLD/STOP/TARGET/TRAIL/REVERSE arms.
- **Apparatus:** AMENDMENT-7 R1–R5 (detection floor shares the CI’s SE family; no result/power labels; scale vs selection denominators declared)
- **Replaces:** any pre-2026-08-07 `analysis.md` written from the pre-fix emission (purged under defect-doc §13)
- **Canonical tables:** `python/experiments/SPDR-024/results/analysis/{cell}/` — this document summarises; it does not replace the parquets
- **Date of this re-emission analysis:** 2026-08-07

## 0. Boundary of this record

**This record issues no verdict.** It does not say the hypothesis is supported or refuted, does not
name a winner or best arm, does not rank arms for deployment, does not claim anything is tradable,
and does not gate XENA or family status. Where the word “pass” appears it is the name of an integrity
field (`blocking_pass`, `row_accounting.pass`), never a judgement about a measured effect.

Every observation is labelled **observed** (read from an emitted artefact) or **inference**
(a mechanism reading of those numbers). Power / MDE is **context only** under
`adaptive-management-design.md` §1/§9 and AMENDMENT-7: no row is dropped, demoted, or classified
by its floor; `MDE_Z = 2.8` is not a pass mark on realised |estimate|; floors use
`mde = MDE_Z × bootstrap_SE` of the same estimator as that row’s CI (R2).

Scale and selection are **different objects** (R4): scale σ̂ uses `sigma_denominator = paired_delta`;
selection contrasts are in bps with `sigma_denominator = outcome_level_bps`. They do not share a
silent dual-σ̂ ladder.

---

## 1. Cost scope — read before any number

Reproduced from `analysis_summary.json` → `spread_cost_disclosure` (identical form on all four cells):

```text
SPREAD-COST-DISCLOSURE
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: ['fully-net', 'cost-complete', 'tradable', 'deployable']
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: None
```

**Observed.** Spread is not charged (`spread_rt_bps: null`). Scope is partial fees/funding only;
in practice commissions on baseline characterisation are gross with no cost charged
(`cost_basis: GROSS_NO_COST_CHARGED_…` on baseline rows).

**Consequence (inference).** Every effect below is a **gross, cost-free** paired difference or
contrast. Paired adaptive−fixed differences largely cancel common per-trade costs, but not
exactly when arms differ in fill count or hold; no spread is applied on either side.

**Prohibited claims (observed, carried on every summary):** fully-net, cost-complete, tradable, deployable.

---

## 2. Integrity, provenance, and reproduction

### 2.1 HARD inventory (design §13 + implementation additions)

| Cell | `blocking_pass` | HARD count | failed | wall_s (run_cell) | source |
|---|---|---:|---|---:|---|
| ctrader_H1 | `True` | 17 | `[]` | 660.13 | `selfcheck/ctrader_H1/spdr024_selfcheck.json` |
| ctrader_H4 | `True` | 17 | `[]` | 366.68 | `selfcheck/ctrader_H4/spdr024_selfcheck.json` |
| crypto_H1 | `True` | 17 | `[]` | 3026.11 | `selfcheck/crypto_H1/spdr024_selfcheck.json` |
| crypto_H4 | `True` | 17 | `[]` | 1607.72 | `selfcheck/crypto_H4/spdr024_selfcheck.json` |

**Observed.** All four cells report `blocking_pass: true` with **17** HARD checks
reconciled by name. The declared set (identical structure across cells):

`arm_lattice_matches_design`, `causal_t_minus_1_provenance`, `deterministic_rerun`, `e1_regime_label_present`, `e2_counterfactual_present_and_non_zero_fill`, `e4_exit_reason_and_entry_ts_populated`, `e5_hold_duration_and_cap_flag_present`, `e6_capital_normalised_estimand_present`, `estimand_reconciliation`, `future_shift_tripwire_collapse`, `golden_traces_match_design`, `hard_check_count_reconciled_by_name`, `nautilus_order_fill_position_reconciliation`, `no_cost_charged`, `time_derangement_absent`, `train_holdout_fence`, `train_only_band_and_domain`.

### 2.2 Estimand validation and fence

| Cell | estimand `blocking_pass` | n_cells (instruments) | manifest missing | fence ok (all instruments) |
|---|---|---:|---|---|
| ctrader_H1 | `True` | 3 | `[]` | `True` |
| ctrader_H4 | `True` | 3 | `[]` | `True` |
| crypto_H1 | `True` | 25 | `[]` | `True` |
| crypto_H4 | `True` | 25 | `[]` | `True` |

**Observed.** Estimand gate version v2; every symbol expected by the universe config is
present (`missing: []`). Fence attestation `ok: true` on every instrument cell.

**Physicality warning (observed on every `analysis_summary.json`):** occupancy, annualised
return and Sharpe inside estimand validation are computed over the **whole arm lattice**, not
the baseline strategy alone — apparatus figures, not tradable performance.

### 2.2b Magnitude-match control populations (selfcheck)

| Cell | rows | selected | excluded |
|---|---:|---:|---:|
| ctrader_H1 | 19542 | 9772 | 9770 |
| ctrader_H4 | 4786 | 2394 | 2392 |
| crypto_H1 | 96305 | 48158 | 48147 |
| crypto_H4 | 21738 | 10876 | 10862 |

**Observed.** `time_derangement` status is `REMOVED_OD17` (not part of this experiment’s HARD
set). `effect_quality_is_blocking: false` — effect-quality controls are informative only.

### 2.3 Future-shift tripwire (integrity, not a research verdict)

**Observed (from selfcheck controls / tripwire path).** The HARD criterion is design §9 REJECT:
non-vacuous shift and no shifted arm outperforming its causal twin beyond the **integrity bite
scale** (`MDE_Z × bootstrap SE` of the same estimator as the CI). Collapse-into-noise is
informative only and does not block. Full per-arm comparisons sit in selfcheck control artefacts
under `results/selfcheck/{cell}/`.

- **ctrader_H1** control artefact keys present: magnitude_match, time_derangement
- **ctrader_H4** control artefact keys present: magnitude_match, time_derangement
- **crypto_H1** control artefact keys present: magnitude_match, time_derangement
- **crypto_H4** control artefact keys present: magnitude_match, time_derangement

### 2.4 Cap rule

| Cell | cap status | hold_cap_bars |
|---|---|---|
| ctrader_H1 | `NOT_APPLICABLE` | None |
| ctrader_H4 | `NOT_APPLICABLE` | None |
| crypto_H1 | `NOT_APPLICABLE` | None |
| crypto_H4 | `NOT_APPLICABLE` | None |

**Observed / mechanism (inference).** With capture devices excluded, the native breakout has no
exit of its own beyond the one-bar hold; arm B durations collapse to the safety ceiling, so the
declared cap grid cannot bind ≤5%. Cap is NOT_APPLICABLE; comparison arms keep the one-bar hold
(implementation-notes §2).

---

## 3. Apparatus contract (AMENDMENT-7) — how to read floors and channels

From `analysis_summary.json` → `floor_contract` (all cells):

| Field | Value |
|---|---|
| `forbidden_row_floor` | MDE_Z / sqrt(effective_blocks) |
| `mde_z_role` | sample-size planning only; not a pass mark on realised |estimate| |
| `row_floor` | mde = MDE_Z * bootstrap_SE of the same estimator as the CI |
| `scale_sigma_denominator` | paired_delta |
| `selection_sigma_denominator` | outcome_level_bps |

**Observed.** `labels.result_labels_emitted: NONE`. Result-label columns (`band`, `WASH`,
`UNPOWERED`, `resolution_class`, …) are absent from emission frames.

**Historical context only (not a gate):** Step-3 sizing point-estimate range 0.022–0.150 σ̂ may
appear in summaries as family history; AMENDMENT-7 forbids using it as a preflight or resolve bar.

---

## 4. Populations and lenses

Named populations on every estimate row (null where a population does not apply):

| Field | Meaning |
|---|---|
| `eligible_origin_n` | eligible origins for the arm |
| `entry_fill_n` | fills (admission at stop fill) |
| `close_n` | confirmed closes |
| `common_fill_n` | origins filled on both sides of a paired comparison |
| `common_close_n` | common closed pairs in the paired series |
| `effective_trade_blocks` | blocks behind a paired trade-lens interval |
| `effective_origin_blocks` | blocks behind an origin-lens interval |

**Scale channel** = paired adaptive − fixed on **common-closed** trades, PRIMARY capital-normalised
return; sigma-hat-normalised then pooled with symbol-clustered bootstrap (M1).

**Selection channel** = admitted mean − rejected counterfactual mean on the **origin lens**, only
`EVALUATED_DECLINED` / `EVALUATED_DECLINED_ORDER_EXPIRED` (admission at fill).

### 4.1 Row census per cell (analysis_summary)

| Cell | episodes | closed | distinct baseline trades | distinct origins | arms |
|---|---:|---:|---:|---:|---:|
| ctrader_H1 | 762318 | 59168 | 1695 | 20061 | 38 |
| ctrader_H4 | 207290 | 17429 | 491 | 5455 | 38 |
| crypto_H1 | 3882080 | 273650 | 8469 | 102160 | 38 |
| crypto_H4 | 1033372 | 63553 | 2003 | 27194 | 38 |

**Observed.** Sample-size statements must use **distinct trades**, not row counts
(`row_vs_trade_note` on every summary).

---

## 5. Preflight power context (R1 / R5) — descriptive only

Preflight counts are **provisional domain-bar simulated fills** (stop-touch + one-domain-bar hold
matching the FIXED native hold), not silent order counts. Endpoint is the R1 SIZE mechanism
ceiling `√p × |μ|/σ` from baseline-only moments (`p = 0.5` planning gate rate).

| Cell | n_fills | planning floor (most conservative) | mechanism ceiling | descriptive label |
|---|---:|---:|---:|---|
| ctrader_H1 | 3846 | 0.0681 | 0.1553 | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` |
| ctrader_H4 | 1061 | 0.1346 | 0.1254 | `DESCRIPTIVE_SIZE_MAGNITUDE_FLOOR_ABOVE_CEILING` |
| crypto_H1 | 17717 | 0.0334 | 0.1360 | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` |
| crypto_H4 | 3982 | 0.0684 | 0.1206 | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` |

**Observed.** `ctrader_H4` is the only cell whose **planning** floor sits above the mechanism
ceiling under the preflight treatments; the other three are at or below. All four cells still
ran (breadth retained; magnitude claims for DESCRIPTIVE cells are not supported by preflight).

**Inference.** Domain-bar fill simulation is optimistic vs minute-path engine fills (~0.67 vs
~0.30 fill rates on cTrader H1 in the prior cycle). Labels use the R1 endpoint regardless;
post-run power context uses bootstrap floors on the real emission.

---

## 6. Baseline characterisation (arm A / OD-3)

**Observed** from `baseline_characterisation.parquet`, POOLED `FIXED_SIZE_UNIT` and
`UNCAPPED_HOLD_SAFETY_CEILING`:

### ctrader_H1

| arm | fills | closed | gross_mean_bps | gross_sigma_bps | win_share | hold_median | regime_share_high |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_SIZE_UNIT | 1695 | 1695 | 1.0988 | 27.0408 | 0.5145 | 1.0 | 0.4832 |
| UNCAPPED_HOLD_SAFETY_CEILING | 383 | 382 | 10.9588 | 203.4885 | 0.5183 | 120.0 | 0.4450 |

### ctrader_H4

| arm | fills | closed | gross_mean_bps | gross_sigma_bps | win_share | hold_median | regime_share_high |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_SIZE_UNIT | 491 | 491 | -2.4798 | 42.2124 | 0.4379 | 1.0 | 0.5886 |
| UNCAPPED_HOLD_SAFETY_CEILING | 108 | 107 | 10.0407 | 387.1996 | 0.5234 | 120.0 | 0.5701 |

### crypto_H1

| arm | fills | closed | gross_mean_bps | gross_sigma_bps | win_share | hold_median | regime_share_high |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_SIZE_UNIT | 8470 | 8469 | 5.2058 | 152.3315 | 0.4605 | 1.0 | 0.5478 |
| UNCAPPED_HOLD_SAFETY_CEILING | 1592 | 1574 | 35.2108 | 2390.7599 | 0.5089 | 120.0 | 0.5356 |

### crypto_H4

| arm | fills | closed | gross_mean_bps | gross_sigma_bps | win_share | hold_median | regime_share_high |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_SIZE_UNIT | 2003 | 2003 | -8.8018 | 272.1917 | 0.4314 | 1.0 | 0.5337 |
| UNCAPPED_HOLD_SAFETY_CEILING | 405 | 383 | 12.7019 | 4368.6914 | 0.5405 | 120.0 | 0.4282 |

**Inference.** FIXED_SIZE_UNIT hold_median = 1 bar is the native one-bar exit. UNCAPPED hold
reaches the 120-bar safety ceiling by construction when no other exit exists.

---

## 7. Scale channel — PRIMARY capital-normalised SIZE effects

All tables in this section are **POOLED**, **regime = ALL**, **PRIMARY lens**, **governing
treatment** under R2 (highest coherent floor / bootstrap SE). Units: sigma-hat of the paired
difference (`sigma_denominator = paired_delta`). Diagnostic per-notional lens is omitted from
sizing claims (exact_zero_delta_share ≈ 1 on that lens by construction for pure SIZE).

### 7.1 Cell-level CI tallies (governing rows)

| Cell | n arms | median est σ̂ | median mde σ̂ | median |est|/SE | ci+ | ci− | cross0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ctrader_H1 | 10 | -0.0561 | 0.1006 | 1.5841 | 0 | 1 | 9 |
| ctrader_H4 | 10 | 0.0461 | 0.1648 | 0.8351 | 0 | 0 | 10 |
| crypto_H1 | 10 | -0.0195 | 0.0461 | 1.7982 | 0 | 4 | 6 |
| crypto_H4 | 10 | 0.0350 | 0.0821 | 1.1447 | 2 | 0 | 8 |

**Observed.** No cell has a majority of governing intervals excluding zero on the positive side.
crypto_H1 has the most one-sided negative intervals (4/10 ci−). cTrader H4 is entirely cross-zero
at the governing treatment.

### 7.2 Full governing arm table (all cells)

#### ctrader_H1

| component | setting | est σ̂ | CI low | CI high | mde σ̂ | SE | n_trades | blocks | treatment | gate_rate | exposure_term_bps | selectivity_term_bps | control p |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | -0.0329 | -0.0970 | 0.0451 | 0.1029 | 0.0368 | 1695 | 1695 | V_A_UNCHUNKED | 0.2973 | -0.1634 | 0.0848 | 0.9320 |
| LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | -0.0226 | -0.0868 | 0.0496 | 0.0982 | 0.0351 | 1695 | 1695 | V_A_UNCHUNKED | 0.2773 | -0.1523 | 0.1042 | 0.6620 |
| LEVEL_NOW | STATE_HALVE_HIGH | -0.0479 | -0.1272 | 0.0441 | 0.1205 | 0.0430 | 1695 | 1695 | V_A_UNCHUNKED | 0.4832 | -0.2655 | -0.1033 | 0.6300 |
| RANGE_SCALE | SCALE_NORMALISED | -0.0584 | -0.1281 | 0.0204 | 0.1060 | 0.0379 | 1695 | 1695 | V_A_UNCHUNKED | 1.0000 | -0.2038 | -0.1499 | 0.0210 |
| RANGE_SCALE | STATE_HALVE_HIGH | -0.0594 | -0.1291 | 0.0230 | 0.1099 | 0.0392 | 1695 | 1695 | V_A_UNCHUNKED | 0.7540 | -0.4142 | -0.0701 | 0.1940 |
| SHOCK | STATE_HALVE_HIGH | -0.0692 | -0.1338 | 0.0042 | 0.0961 | 0.0343 | 1695 | 1107 | V_C_REGIME_EPISODE | 0.3723 | -0.2045 | -0.1776 | 0.0530 |
| SWING_GT_CUR | STATE_HALVE_HIGH | -0.0538 | -0.1041 | -0.0032 | 0.0738 | 0.0264 | 1695 | 1107 | V_C_REGIME_EPISODE | 0.4926 | -0.2707 | -0.0938 | 0.4220 |
| SWING_SCALE | SCALE_NORMALISED | -0.0492 | -0.1042 | 0.0044 | 0.0791 | 0.0282 | 1695 | 1107 | V_C_REGIME_EPISODE | 0.9723 | -0.1978 | -0.1303 | 0.2720 |
| SWING_SCALE | STATE_HALVE_HIGH | -0.0610 | -0.1228 | 0.0089 | 0.0958 | 0.0342 | 1695 | 1695 | V_A_UNCHUNKED | 0.8047 | -0.4421 | -0.0776 | 0.2040 |
| TAIL_RISK | STATE_HALVE_HIGH | -0.0619 | -0.1329 | 0.0169 | 0.1068 | 0.0381 | 1695 | 1695 | V_A_UNCHUNKED | 0.7192 | -0.3951 | -0.1343 | 0.1170 |

#### ctrader_H4

| component | setting | est σ̂ | CI low | CI high | mde σ̂ | SE | n_trades | blocks | treatment | gate_rate | exposure_term_bps | selectivity_term_bps | control p |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | 0.0635 | -0.0618 | 0.1888 | 0.1815 | 0.0648 | 491 | 359 | V_B_TIME_BLOCK | 0.3442 | 0.4268 | 0.3851 | 0.3370 |
| LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | 0.0493 | -0.0755 | 0.1645 | 0.1673 | 0.0598 | 491 | 292 | V_C_REGIME_EPISODE | 0.3646 | 0.4520 | 0.2437 | 0.5610 |
| LEVEL_NOW | STATE_HALVE_HIGH | 0.0491 | -0.0419 | 0.1513 | 0.1376 | 0.0491 | 491 | 359 | V_B_TIME_BLOCK | 0.5886 | 0.7298 | 0.2047 | 0.6680 |
| RANGE_SCALE | SCALE_NORMALISED | 0.0148 | -0.0904 | 0.1348 | 0.1622 | 0.0579 | 491 | 491 | V_A_UNCHUNKED | 1.0000 | 0.4480 | 0.1503 | 0.6880 |
| RANGE_SCALE | STATE_HALVE_HIGH | 0.0525 | -0.0433 | 0.1560 | 0.1450 | 0.0518 | 491 | 359 | V_B_TIME_BLOCK | 0.7576 | 0.9394 | 0.2689 | 0.6410 |
| SHOCK | STATE_HALVE_HIGH | 0.0871 | -0.0178 | 0.1972 | 0.1528 | 0.0546 | 491 | 359 | V_B_TIME_BLOCK | 0.3747 | 0.4647 | 0.8176 | 0.1270 |
| SWING_GT_CUR | STATE_HALVE_HIGH | 0.0333 | -0.0741 | 0.1598 | 0.1699 | 0.0607 | 491 | 359 | V_B_TIME_BLOCK | 0.4277 | 0.5303 | 0.2565 | 0.9330 |
| SWING_SCALE | SCALE_NORMALISED | -0.0483 | -0.1647 | 0.0888 | 0.1813 | 0.0648 | 491 | 359 | V_B_TIME_BLOCK | 0.8513 | 0.3149 | -0.4076 | 0.0510 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0211 | -0.0981 | 0.1529 | 0.1739 | 0.0621 | 491 | 359 | V_B_TIME_BLOCK | 0.8106 | 1.0051 | -0.1443 | 0.2350 |
| TAIL_RISK | STATE_HALVE_HIGH | 0.0431 | -0.0572 | 0.1456 | 0.1429 | 0.0510 | 491 | 359 | V_B_TIME_BLOCK | 0.7393 | 0.9167 | 0.0633 | 0.9480 |

#### crypto_H1

| component | setting | est σ̂ | CI low | CI high | mde σ̂ | SE | n_trades | blocks | treatment | gate_rate | exposure_term_bps | selectivity_term_bps | control p |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | -0.0458 | -0.0803 | -0.0158 | 0.0448 | 0.0160 | 8441 | 8441 | V_A_UNCHUNKED | 0.3316 | -0.8630 | -0.9569 | 0.0000 |
| LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | -0.0490 | -0.0781 | -0.0198 | 0.0416 | 0.0149 | 8469 | 5058 | V_C_REGIME_EPISODE | 0.3399 | -0.8849 | -1.0507 | 0.0000 |
| LEVEL_NOW | STATE_HALVE_HIGH | -0.0337 | -0.0657 | -0.0020 | 0.0452 | 0.0161 | 8469 | 5058 | V_C_REGIME_EPISODE | 0.5478 | -1.4258 | -0.8466 | 0.0620 |
| RANGE_SCALE | SCALE_NORMALISED | 0.0179 | -0.0171 | 0.0531 | 0.0505 | 0.0180 | 8469 | 8469 | V_A_UNCHUNKED | 1.0000 | 1.1872 | -1.1950 | 0.4090 |
| RANGE_SCALE | STATE_HALVE_HIGH | -0.0015 | -0.0363 | 0.0329 | 0.0488 | 0.0174 | 8469 | 5058 | V_C_REGIME_EPISODE | 0.3852 | -1.0026 | -0.3213 | 0.0730 |
| SHOCK | STATE_HALVE_HIGH | -0.0132 | -0.0470 | 0.0189 | 0.0477 | 0.0170 | 8469 | 5058 | V_C_REGIME_EPISODE | 0.2575 | -0.6703 | -0.4678 | 0.9630 |
| SWING_GT_CUR | STATE_HALVE_HIGH | -0.0438 | -0.0732 | -0.0152 | 0.0417 | 0.0149 | 8469 | 8469 | V_A_UNCHUNKED | 0.5434 | -1.4144 | -0.8672 | 0.0010 |
| SWING_SCALE | SCALE_NORMALISED | 0.0341 | -0.0009 | 0.0671 | 0.0478 | 0.0171 | 8312 | 8312 | V_A_UNCHUNKED | 0.9294 | 1.0805 | 0.4256 | 0.0350 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0083 | -0.0248 | 0.0399 | 0.0470 | 0.0168 | 8469 | 8469 | V_A_UNCHUNKED | 0.3566 | -0.9282 | 0.3912 | 0.0060 |
| TAIL_RISK | STATE_HALVE_HIGH | -0.0258 | -0.0584 | 0.0058 | 0.0450 | 0.0161 | 8469 | 5058 | V_C_REGIME_EPISODE | 0.4962 | -1.2915 | -0.5939 | 0.3310 |

#### crypto_H4

| component | setting | est σ̂ | CI low | CI high | mde σ̂ | SE | n_trades | blocks | treatment | gate_rate | exposure_term_bps | selectivity_term_bps | control p |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | 0.0112 | -0.0465 | 0.0740 | 0.0864 | 0.0309 | 1978 | 1978 | V_A_UNCHUNKED | 0.2966 | 1.3051 | -0.0771 | 0.2680 |
| LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | 0.0214 | -0.0315 | 0.0823 | 0.0824 | 0.0294 | 1990 | 1380 | V_B_TIME_BLOCK | 0.3240 | 1.4259 | -0.6221 | 0.4530 |
| LEVEL_NOW | STATE_HALVE_HIGH | 0.0503 | -0.0014 | 0.1035 | 0.0757 | 0.0271 | 2003 | 2003 | V_A_UNCHUNKED | 0.5337 | 2.3487 | 1.2353 | 0.6560 |
| RANGE_SCALE | SCALE_NORMALISED | 0.0284 | -0.0363 | 0.0973 | 0.0948 | 0.0339 | 2003 | 1388 | V_B_TIME_BLOCK | 1.0000 | -1.4558 | 4.3426 | 0.0510 |
| RANGE_SCALE | STATE_HALVE_HIGH | 0.0618 | 0.0065 | 0.1179 | 0.0819 | 0.0293 | 2003 | 2003 | V_A_UNCHUNKED | 0.4249 | 1.8698 | 2.6995 | 0.2360 |
| SHOCK | STATE_HALVE_HIGH | 0.0416 | -0.0147 | 0.0995 | 0.0804 | 0.0287 | 2003 | 1388 | V_B_TIME_BLOCK | 0.2866 | 1.2612 | 0.3742 | 0.6630 |
| SWING_GT_CUR | STATE_HALVE_HIGH | 0.0104 | -0.0416 | 0.0623 | 0.0744 | 0.0266 | 1963 | 1963 | V_A_UNCHUNKED | 0.4678 | 2.0587 | -2.0795 | 0.0710 |
| SWING_SCALE | SCALE_NORMALISED | 0.0042 | -0.0688 | 0.0789 | 0.1059 | 0.0378 | 1677 | 1166 | V_B_TIME_BLOCK | 0.6820 | -0.8973 | 2.6170 | 0.3000 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0648 | -0.0019 | 0.1280 | 0.0951 | 0.0340 | 2003 | 2003 | V_A_UNCHUNKED | 0.5047 | 2.2213 | 2.8527 | 0.2290 |
| TAIL_RISK | STATE_HALVE_HIGH | 0.0585 | 0.0052 | 0.1152 | 0.0794 | 0.0284 | 2003 | 2003 | V_A_UNCHUNKED | 0.5347 | 2.3531 | 2.0907 | 0.4360 |

**Reading (observed).** For SIZE, the paired difference decomposes into exposure
`(E[size]−1)×E[outcome]` and selectivity. Where `exposure_term` dominates and gate-permutation
`control_two_sided_p` is large, the raw paired estimate is largely arithmetic exposure, not a
demonstrated quality of the gate (implementation-notes / design controls).

### 7.3 Continuous vs discrete SIZE (OD-14 coverage)

**Observed** (`od14_coverage`): continuous `SCALE_NORMALISED` and discrete `STATE_HALVE_HIGH`
head-to-head only on `RANGE_SCALE` and `SWING_SCALE`. Other six components are discrete only.

**ctrader_H1**

| component | setting | est σ̂ | CI | exposure_bps | selectivity_bps |
|---|---|---:|---|---:|---:|
| RANGE_SCALE | SCALE_NORMALISED | -0.0584 | [-0.1281, 0.0204] | -0.2038 | -0.1499 |
| RANGE_SCALE | STATE_HALVE_HIGH | -0.0594 | [-0.1291, 0.0230] | -0.4142 | -0.0701 |
| SWING_SCALE | SCALE_NORMALISED | -0.0492 | [-0.1042, 0.0044] | -0.1978 | -0.1303 |
| SWING_SCALE | STATE_HALVE_HIGH | -0.0610 | [-0.1228, 0.0089] | -0.4421 | -0.0776 |

**ctrader_H4**

| component | setting | est σ̂ | CI | exposure_bps | selectivity_bps |
|---|---|---:|---|---:|---:|
| RANGE_SCALE | SCALE_NORMALISED | 0.0148 | [-0.0904, 0.1348] | 0.4480 | 0.1503 |
| RANGE_SCALE | STATE_HALVE_HIGH | 0.0525 | [-0.0433, 0.1560] | 0.9394 | 0.2689 |
| SWING_SCALE | SCALE_NORMALISED | -0.0483 | [-0.1647, 0.0888] | 0.3149 | -0.4076 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0211 | [-0.0981, 0.1529] | 1.0051 | -0.1443 |

**crypto_H1**

| component | setting | est σ̂ | CI | exposure_bps | selectivity_bps |
|---|---|---:|---|---:|---:|
| RANGE_SCALE | SCALE_NORMALISED | 0.0179 | [-0.0171, 0.0531] | 1.1872 | -1.1950 |
| RANGE_SCALE | STATE_HALVE_HIGH | -0.0015 | [-0.0363, 0.0329] | -1.0026 | -0.3213 |
| SWING_SCALE | SCALE_NORMALISED | 0.0341 | [-0.0009, 0.0671] | 1.0805 | 0.4256 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0083 | [-0.0248, 0.0399] | -0.9282 | 0.3912 |

**crypto_H4**

| component | setting | est σ̂ | CI | exposure_bps | selectivity_bps |
|---|---|---:|---|---:|---:|
| RANGE_SCALE | SCALE_NORMALISED | 0.0284 | [-0.0363, 0.0973] | -1.4558 | 4.3426 |
| RANGE_SCALE | STATE_HALVE_HIGH | 0.0618 | [0.0065, 0.1179] | 1.8698 | 2.6995 |
| SWING_SCALE | SCALE_NORMALISED | 0.0042 | [-0.0688, 0.0789] | -0.8973 | 2.6170 |
| SWING_SCALE | STATE_HALVE_HIGH | 0.0648 | [-0.0019, 0.1280] | 2.2213 | 2.8527 |

### 7.4 Variance treatments (agreement / divergence)

For each cell, compare the three treatments on POOLED PRIMARY regime=ALL for a single
illustrative arm (`ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH` if present, else first arm):

**ctrader_H1** — arm `ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH`

| treatment | est σ̂ | CI low | CI high | mde σ̂ | blocks | governs? |
|---|---:|---:|---:|---:|---:|---|
| V_A_UNCHUNKED | -0.0619 | -0.1329 | 0.0169 | 0.1068 | 1695 | True |
| V_B_TIME_BLOCK | -0.0619 | -0.1289 | 0.0144 | 0.1044 | 1212 | False |
| V_C_REGIME_EPISODE | -0.0619 | -0.1329 | 0.0170 | 0.1048 | 1107 | False |

**ctrader_H4** — arm `ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH`

| treatment | est σ̂ | CI low | CI high | mde σ̂ | blocks | governs? |
|---|---:|---:|---:|---:|---:|---|
| V_A_UNCHUNKED | 0.0431 | -0.0505 | 0.1408 | 0.1381 | 491 | False |
| V_B_TIME_BLOCK | 0.0431 | -0.0572 | 0.1456 | 0.1429 | 359 | True |
| V_C_REGIME_EPISODE | 0.0431 | -0.0595 | 0.1410 | 0.1371 | 292 | False |

**crypto_H1** — arm `ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH`

| treatment | est σ̂ | CI low | CI high | mde σ̂ | blocks | governs? |
|---|---:|---:|---:|---:|---:|---|
| V_A_UNCHUNKED | -0.0258 | -0.0577 | 0.0044 | 0.0450 | 8469 | False |
| V_B_TIME_BLOCK | -0.0258 | -0.0563 | 0.0032 | 0.0428 | 5796 | False |
| V_C_REGIME_EPISODE | -0.0258 | -0.0584 | 0.0058 | 0.0450 | 5058 | True |

**crypto_H4** — arm `ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH`

| treatment | est σ̂ | CI low | CI high | mde σ̂ | blocks | governs? |
|---|---:|---:|---:|---:|---:|---|
| V_A_UNCHUNKED | 0.0585 | 0.0052 | 0.1152 | 0.0794 | 2003 | True |
| V_B_TIME_BLOCK | 0.0585 | 0.0064 | 0.1112 | 0.0750 | 1388 | False |
| V_C_REGIME_EPISODE | 0.0585 | 0.0042 | 0.1116 | 0.0768 | 1203 | False |

**Inference.** Divergence across V-A/V-B/V-C is a dependence diagnostic (design §10.1), not a
menu of favourable intervals. The governing row is the highest R2 floor.

### 7.5 Regime strata (HIGH / LOW) — scale, governing, POOLED

**ctrader_H1** — median estimate by regime across arms:
- HIGH: n=10, median est=-0.0706, ci+/ci−/cross0 = 0/2/8
- LOW: n=10, median est=-0.0275, ci+/ci−/cross0 = 0/0/9

**ctrader_H4** — median estimate by regime across arms:
- HIGH: n=10, median est=0.0653, ci+/ci−/cross0 = 0/0/10
- LOW: n=10, median est=-0.0122, ci+/ci−/cross0 = 0/0/9

**crypto_H1** — median estimate by regime across arms:
- HIGH: n=10, median est=-0.0296, ci+/ci−/cross0 = 1/4/5
- LOW: n=10, median est=0.0165, ci+/ci−/cross0 = 0/0/9

**crypto_H4** — median estimate by regime across arms:
- HIGH: n=10, median est=0.0456, ci+/ci−/cross0 = 0/0/10
- LOW: n=10, median est=0.0205, ci+/ci−/cross0 = 0/0/9

---

## 8. Selection channel — admitted vs declined counterfactuals

Units: **bps** on the origin lens. `sigma_denominator = outcome_level_bps` when a σ̂ form is
shown. Floors `mde_bps = MDE_Z × bootstrap_SE` of the contrast.

### 8.1 Cell-level summary (POOLED)

| Cell | n contrasts | median contrast_bps | median |contrast|/SE | ci+ | ci− | cross0 | empty rejected |
|---|---:|---:|---:|---:|---:|---:|---:|
| ctrader_H1 | 24 | -0.71 | 0.53 | 0 | 0 | 24 | 0 |
| ctrader_H4 | 24 | 1.32 | 0.45 | 0 | 0 | 24 | 0 |
| crypto_H1 | 24 | 4.29 | 0.87 | 0 | 0 | 24 | 0 |
| crypto_H4 | 24 | -11.42 | 0.50 | 0 | 0 | 24 | 0 |

### 8.2 Governing selection table (POOLED)

#### ctrader_H1

| component | contrast_bps | CI low | CI high | mde_bps | n_adm | n_rej | matched_bps | collapse_frac |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | -2.30 | -6.65 | 0.54 | 5.35 | 889 | 398 | -1.83 | 0.205 |
| LEVEL_FORECAST_K4 | -2.33 | -6.97 | 0.44 | 5.43 | 909 | 380 | -1.03 | 0.559 |
| LEVEL_NOW | -0.64 | -5.32 | 2.39 | 5.66 | 1592 | 586 | 0.14 | 1.214 |
| RANGE_SCALE | 0.17 | -3.42 | 3.17 | 4.55 | 2213 | 315 | 0.31 | -0.849 |
| SHOCK | -0.96 | -3.60 | 1.40 | 3.66 | 1165 | 782 | -0.96 | -0.025 |
| SWING_GT_CUR | -0.71 | -3.89 | 2.77 | 4.86 | 1608 | 563 | -0.70 | 0.019 |
| SWING_SCALE | -0.99 | -4.71 | 2.09 | 4.78 | 2187 | 266 | -1.11 | -0.127 |
| TAIL_RISK | -0.04 | -5.61 | 2.89 | 6.02 | 1964 | 409 | 0.16 | 2.891 |
| LEVEL_FORECAST_K12 | -1.91 | -6.73 | 1.17 | 5.61 | 841 | 300 | -1.73 | 0.098 |
| LEVEL_FORECAST_K12 | -0.30 | -6.13 | 3.96 | 7.30 | 1023 | 148 | 0.74 | 3.500 |
| LEVEL_FORECAST_K4 | -2.30 | -6.68 | 1.22 | 5.47 | 884 | 273 | 0.26 | 1.111 |
| LEVEL_FORECAST_K4 | -1.47 | -7.13 | 2.46 | 6.91 | 1014 | 148 | -0.00 | 0.999 |
| LEVEL_NOW | -0.72 | -5.54 | 3.08 | 6.09 | 1502 | 426 | 3.70 | 6.168 |
| LEVEL_NOW | 0.29 | -3.55 | 3.21 | 4.88 | 1721 | 235 | 0.90 | -2.116 |
| RANGE_SCALE | 1.14 | -4.65 | 6.22 | 7.45 | 2057 | 133 | 1.61 | -0.333 |
| RANGE_SCALE | -1.21 | -6.93 | 1.89 | 6.22 | 1810 | 187 | -1.14 | 0.011 |
| SHOCK | -0.71 | -3.92 | 1.74 | 4.13 | 1116 | 659 | -0.71 | -0.019 |
| SHOCK | 0.55 | -3.04 | 4.08 | 5.30 | 1644 | 268 | 0.56 | -0.018 |
| SWING_GT_CUR | -0.53 | -5.19 | 3.04 | 5.90 | 1555 | 396 | -0.51 | 0.030 |
| SWING_GT_CUR | 1.41 | -2.44 | 6.48 | 6.37 | 1644 | 250 | 1.44 | -0.024 |
| SWING_SCALE | 2.70 | -5.01 | 10.31 | 10.81 | 2030 | 74 | 2.72 | -0.004 |
| SWING_SCALE | -1.89 | -7.02 | 1.75 | 6.43 | 1777 | 179 | -2.05 | -0.086 |
| TAIL_RISK | 1.23 | -2.64 | 3.99 | 4.53 | 1798 | 248 | 4.04 | -2.081 |
| TAIL_RISK | -1.09 | -6.29 | 1.80 | 5.91 | 1808 | 193 | -1.09 | 0.113 |

#### ctrader_H4

| component | contrast_bps | CI low | CI high | mde_bps | n_adm | n_rej | matched_bps | collapse_frac |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | -3.02 | -20.87 | 10.27 | 22.65 | 308 | 89 | -5.16 | -0.706 |
| LEVEL_FORECAST_K4 | -0.37 | -18.17 | 13.74 | 23.00 | 318 | 83 | -4.63 | -11.556 |
| LEVEL_NOW | -1.30 | -15.39 | 8.90 | 17.57 | 502 | 135 | -6.93 | -4.337 |
| RANGE_SCALE | 5.19 | -7.28 | 16.93 | 17.72 | 685 | 73 | 3.05 | -0.237 |
| SHOCK | 0.82 | -9.76 | 8.70 | 13.73 | 371 | 207 | 0.14 | -1.385 |
| SWING_GT_CUR | -1.48 | -11.43 | 7.03 | 13.42 | 435 | 140 | -1.53 | -0.029 |
| SWING_SCALE | 3.22 | -7.99 | 17.04 | 17.68 | 586 | 64 | 1.85 | 0.424 |
| TAIL_RISK | -2.92 | -16.49 | 8.04 | 17.89 | 604 | 106 | -7.15 | -0.446 |
| LEVEL_FORECAST_K12 | -0.58 | -20.24 | 13.84 | 23.29 | 278 | 59 | -5.09 | -7.819 |
| LEVEL_FORECAST_K12 | 1.27 | -13.68 | 15.44 | 19.68 | 319 | 36 | -1.33 | 2.042 |
| LEVEL_FORECAST_K4 | 1.37 | -18.45 | 16.69 | 24.49 | 288 | 54 | -20.33 | 15.887 |
| LEVEL_FORECAST_K4 | 3.95 | -11.05 | 17.66 | 20.50 | 320 | 35 | 2.54 | 0.355 |
| LEVEL_NOW | -2.14 | -18.66 | 9.78 | 20.12 | 456 | 92 | -18.23 | -7.508 |
| LEVEL_NOW | 4.91 | -7.69 | 16.06 | 16.76 | 521 | 55 | 0.72 | 0.854 |
| RANGE_SCALE | 16.01 | -2.68 | 44.08 | 33.17 | 611 | 32 | 11.01 | 0.007 |
| RANGE_SCALE | 3.34 | -9.38 | 15.00 | 17.90 | 566 | 48 | 3.84 | -0.201 |
| SHOCK | -1.54 | -12.69 | 8.13 | 14.72 | 329 | 176 | -2.54 | -0.034 |
| SHOCK | 5.74 | -4.18 | 15.15 | 13.74 | 500 | 68 | 5.92 | 0.014 |
| SWING_GT_CUR | -2.35 | -13.20 | 7.04 | 14.72 | 393 | 100 | -2.36 | -0.005 |
| SWING_GT_CUR | 6.68 | -5.06 | 16.05 | 14.93 | 457 | 59 | 6.66 | 0.003 |
| SWING_SCALE | 13.51 | -5.87 | 60.21 | 47.64 | 524 | 25 | 12.00 | 0.112 |
| SWING_SCALE | 4.32 | -11.49 | 15.73 | 18.90 | 476 | 44 | 3.75 | 0.132 |
| TAIL_RISK | -1.11 | -14.44 | 13.25 | 19.08 | 528 | 65 | -3.03 | 0.369 |
| TAIL_RISK | 4.61 | -10.35 | 17.00 | 20.07 | 564 | 48 | 3.12 | 0.325 |

#### crypto_H1

| component | contrast_bps | CI low | CI high | mde_bps | n_adm | n_rej | matched_bps | collapse_frac |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | 3.07 | -7.91 | 12.78 | 15.01 | 4782 | 1894 | 0.30 | 0.903 |
| LEVEL_FORECAST_K4 | 3.94 | -6.58 | 14.05 | 14.52 | 4957 | 1800 | -2.82 | 1.716 |
| LEVEL_NOW | 2.43 | -6.10 | 10.84 | 11.98 | 8082 | 2925 | -3.23 | 2.331 |
| RANGE_SCALE | 2.68 | -6.31 | 11.66 | 12.76 | 7219 | 3385 | 1.17 | 0.400 |
| SHOCK | 2.41 | -7.57 | 12.02 | 13.36 | 4958 | 4431 | 1.40 | 0.396 |
| SWING_GT_CUR | 3.67 | -4.05 | 10.89 | 11.06 | 8135 | 2600 | 3.37 | 0.082 |
| SWING_SCALE | -0.02 | -9.09 | 8.55 | 12.57 | 6414 | 3080 | -0.02 | 0.002 |
| TAIL_RISK | 3.93 | -5.47 | 13.82 | 13.18 | 7791 | 3159 | -1.38 | 1.497 |
| LEVEL_FORECAST_K12 | 2.46 | -9.32 | 13.97 | 16.75 | 4473 | 1494 | 2.50 | -0.019 |
| LEVEL_FORECAST_K12 | 6.11 | -8.79 | 19.81 | 20.09 | 5240 | 688 | 0.27 | 0.956 |
| LEVEL_FORECAST_K4 | 4.65 | -5.10 | 15.70 | 14.65 | 4656 | 1388 | 10.01 | -1.153 |
| LEVEL_FORECAST_K4 | 5.93 | -9.82 | 19.80 | 20.81 | 5279 | 657 | -8.45 | 2.425 |
| LEVEL_NOW | 3.63 | -4.29 | 11.40 | 11.18 | 7582 | 2263 | 14.80 | -3.079 |
| LEVEL_NOW | 5.94 | -6.25 | 18.29 | 17.78 | 8533 | 1105 | -3.69 | 1.620 |
| RANGE_SCALE | 1.94 | -6.19 | 11.13 | 12.51 | 7187 | 2556 | 2.14 | 0.154 |
| RANGE_SCALE | 6.53 | -4.54 | 18.09 | 16.58 | 8150 | 1350 | 4.32 | 0.134 |
| SHOCK | 5.18 | -3.98 | 15.46 | 13.74 | 4995 | 3809 | 4.43 | 0.127 |
| SHOCK | 5.56 | -4.99 | 15.45 | 14.40 | 7805 | 1520 | 4.99 | 0.108 |
| SWING_GT_CUR | 5.07 | -3.54 | 12.78 | 11.69 | 7684 | 1886 | 4.83 | 0.047 |
| SWING_GT_CUR | 6.42 | -5.39 | 19.74 | 18.36 | 8132 | 1052 | 6.53 | -0.018 |
| SWING_SCALE | -0.66 | -10.52 | 10.99 | 15.11 | 6609 | 2154 | -0.69 | -0.047 |
| SWING_SCALE | 5.80 | -6.21 | 16.69 | 16.00 | 7436 | 1357 | 5.90 | -0.016 |
| TAIL_RISK | 4.84 | -3.47 | 13.28 | 12.05 | 7417 | 2446 | 5.06 | -0.044 |
| TAIL_RISK | 5.90 | -6.67 | 19.69 | 18.55 | 8463 | 1205 | -2.87 | 1.740 |

#### crypto_H4

| component | contrast_bps | CI low | CI high | mde_bps | n_adm | n_rej | matched_bps | collapse_frac |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEVEL_FORECAST_K12 | -22.55 | -60.62 | 15.57 | 53.89 | 1065 | 430 | -30.05 | -0.333 |
| LEVEL_FORECAST_K4 | -5.56 | -42.59 | 35.72 | 56.15 | 1141 | 412 | -9.38 | -0.687 |
| LEVEL_NOW | -4.64 | -33.06 | 24.20 | 41.08 | 1943 | 671 | -14.01 | -2.020 |
| RANGE_SCALE | -14.07 | -47.94 | 17.10 | 48.25 | 1849 | 711 | -18.22 | 0.010 |
| SHOCK | -15.60 | -49.66 | 17.80 | 47.55 | 1255 | 982 | -11.17 | 0.138 |
| SWING_GT_CUR | -6.00 | -43.26 | 32.12 | 54.05 | 1752 | 484 | -5.63 | 0.061 |
| SWING_SCALE | -20.19 | -62.67 | 22.92 | 58.26 | 1331 | 463 | -19.79 | 0.020 |
| TAIL_RISK | -6.04 | -36.87 | 22.14 | 42.16 | 1977 | 702 | -12.22 | -1.494 |
| LEVEL_FORECAST_K12 | -3.99 | -39.42 | 31.88 | 53.02 | 981 | 341 | -6.71 | -0.681 |
| LEVEL_FORECAST_K12 | -32.66 | -99.31 | 22.70 | 87.48 | 1132 | 179 | -40.43 | -0.238 |
| LEVEL_FORECAST_K4 | 4.60 | -29.34 | 40.82 | 50.27 | 1059 | 308 | -31.56 | 7.867 |
| LEVEL_FORECAST_K4 | -16.01 | -70.82 | 41.15 | 77.93 | 1157 | 167 | -18.23 | -0.139 |
| LEVEL_NOW | 4.05 | -24.15 | 34.23 | 42.57 | 1800 | 511 | -25.92 | 7.398 |
| LEVEL_NOW | -11.41 | -53.54 | 32.39 | 64.13 | 1977 | 260 | -19.81 | -0.736 |
| RANGE_SCALE | 6.64 | -26.91 | 44.97 | 49.90 | 1833 | 480 | 5.10 | 0.092 |
| RANGE_SCALE | -31.31 | -83.85 | 11.92 | 66.89 | 1980 | 311 | -38.31 | -0.002 |
| SHOCK | 7.96 | -22.38 | 38.19 | 43.66 | 1241 | 834 | 12.72 | -0.152 |
| SHOCK | -27.54 | -80.66 | 15.93 | 68.42 | 1847 | 352 | -27.31 | -0.014 |
| SWING_GT_CUR | 0.49 | -35.16 | 38.56 | 52.87 | 1628 | 333 | 2.97 | -5.041 |
| SWING_GT_CUR | -11.43 | -66.80 | 39.19 | 76.18 | 1594 | 217 | -11.27 | 0.014 |
| SWING_SCALE | -28.08 | -64.76 | 10.95 | 53.94 | 1314 | 313 | -27.26 | 0.029 |
| SWING_SCALE | -13.41 | -59.03 | 30.71 | 66.14 | 1382 | 205 | -13.41 | 0.000 |
| TAIL_RISK | 6.35 | -23.28 | 40.77 | 46.79 | 1870 | 516 | 5.48 | 0.405 |
| TAIL_RISK | -16.83 | -62.07 | 23.23 | 60.70 | 2023 | 283 | -28.99 | -0.496 |

**Inference.** Admission rules here are volatility gates, so unmatched admitted−declined is
partly a HIGH-vs-LOW comparison. The regime-matched contrast is the control-relevant figure for
selection quality (design §8). Collapse fraction is arithmetic (unmatched≠0), not MDE-gated.

---

## 9. Concentration and pool-filter ladder

**Observed** from `pool_filter_ladder.parquet` (disclosure ladder, not a pruning rule):

### ctrader_H1

Rows: 336; columns include: channel, arm_id, lens, regime, ladder_step, dropped_symbols, n_symbols, unweighted_mean_of_symbol_means_raw, worst_symbol, best_symbol, value_column, class…
- channel `SCALE`: 240 ladder rows
- channel `SELECTION`: 96 ladder rows

### ctrader_H4

Rows: 336; columns include: channel, arm_id, lens, regime, ladder_step, dropped_symbols, n_symbols, unweighted_mean_of_symbol_means_raw, worst_symbol, best_symbol, value_column, class…
- channel `SELECTION`: 96 ladder rows
- channel `SCALE`: 240 ladder rows

### crypto_H1

Rows: 336; columns include: channel, arm_id, lens, regime, ladder_step, dropped_symbols, n_symbols, unweighted_mean_of_symbol_means_raw, worst_symbol, best_symbol, value_column, class…
- channel `SELECTION`: 96 ladder rows
- channel `SCALE`: 240 ladder rows

### crypto_H4

Rows: 336; columns include: channel, arm_id, lens, regime, ladder_step, dropped_symbols, n_symbols, unweighted_mean_of_symbol_means_raw, worst_symbol, best_symbol, value_column, class…
- channel `SELECTION`: 96 ladder rows
- channel `SCALE`: 240 ladder rows

Full per-step tables remain in the parquet; POOLED is disclosure-only unless homogeneity is shown
(design §11).

---

## 10. Dependence premise (paired difference)

### ctrader_H1
- **observed (summary):** premise = `design section 10 assumes no detectable serial dependence in the trade series`
- **observed:** verdict = `NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS`
- **observed:** paired_difference symbols outside noise band: `['EURUSD', 'USTEC', 'XAUUSD']`
- **observed:** consequence if not supported: V-A's unchunked treatment would overstate resolution; V-B and V-C remain, and the most conservative still governs every band
- **observed:** detailed dependence artefact keys: ['baseline_series', 'paired_difference_series', 'reading']

### ctrader_H4
- **observed (summary):** premise = `design section 10 assumes no detectable serial dependence in the trade series`
- **observed:** verdict = `NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS`
- **observed:** paired_difference symbols outside noise band: `['EURUSD', 'USTEC', 'XAUUSD']`
- **observed:** consequence if not supported: V-A's unchunked treatment would overstate resolution; V-B and V-C remain, and the most conservative still governs every band
- **observed:** detailed dependence artefact keys: ['baseline_series', 'paired_difference_series', 'reading']

### crypto_H1
- **observed (summary):** premise = `design section 10 assumes no detectable serial dependence in the trade series`
- **observed:** verdict = `NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS`
- **observed:** paired_difference symbols outside noise band: `['1000BONKUSDT', '1000LUNCUSDT', '1000PEPEUSDT', 'ADAUSDT', 'AVAXUSDT', 'BIGTIMEUSDT', 'BLURUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DYDXUSDT', 'ETHUSDT', 'GALAUSDT', 'INJUSDT', 'LINKUSDT', 'MATICUSDT', 'OPUSDT', 'ORDIUSDT', 'SEIUSDT', 'SOLUSDT', 'TIAUSDT', 'WLDUSDT', 'XRPUSDT']`
- **observed:** consequence if not supported: V-A's unchunked treatment would overstate resolution; V-B and V-C remain, and the most conservative still governs every band
- **observed:** detailed dependence artefact keys: ['baseline_series', 'paired_difference_series', 'reading']

### crypto_H4
- **observed (summary):** premise = `design section 10 assumes no detectable serial dependence in the trade series`
- **observed:** verdict = `NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS`
- **observed:** paired_difference symbols outside noise band: `['1000BONKUSDT', '1000LUNCUSDT', '1000PEPEUSDT', 'ADAUSDT', 'AVAXUSDT', 'BLURUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DYDXUSDT', 'ETHUSDT', 'GALAUSDT', 'INJUSDT', 'LINKUSDT', 'MATICUSDT', 'OPUSDT', 'ORDIUSDT', 'SOLUSDT', 'XRPUSDT']`
- **observed:** consequence if not supported: V-A's unchunked treatment would overstate resolution; V-B and V-C remain, and the most conservative still governs every band
- **observed:** detailed dependence artefact keys: ['baseline_series', 'paired_difference_series', 'reading']

**Inference.** Where the unchunked (V-A) premise is not supported, V-B/V-C and the most
conservative governing treatment remain the protective read (design §10.1).

---

## 11. Observations, stated symmetrically

### 11.1 Consistent patterns (observed across cells)

- Integrity clears everywhere: `blocking_pass=true`, HARD count 17, golden traces pass.
- Scale effects are small in σ̂ units relative to bootstrap floors on many rows; intervals often
  cross zero at the governing treatment.
- SIZE exposure terms are first-class and often large relative to selectivity; gate-permutation
  p-values frequently fail to reject the null that the gate is exchangeable with a random gate.
- Selection contrasts are reported in **bps** on a different denominator than scale σ̂ — they
  must not be ranked against scale using a shared numeric ladder (R4).
- Continuous vs discrete SIZE is only defined on two components (RANGE_SCALE, SWING_SCALE).

### 11.2 Contrary, concentrated, or cell-specific (observed)

- **crypto_H1** scale: more ci− governing rows than other cells (4/10) — direction of the
  point estimates tends negative under SIZE halving when gross expectancy is positive (A4 arithmetic).
- **crypto_H4** selection: median contrast largely negative in bps vs positive median on crypto_H1
  — domains disagree on the selection lens; not pooled.
- **ctrader_H4** preflight DESCRIPTIVE for SIZE magnitude (planning floor above mechanism ceiling);
  post-run scale intervals are all cross-zero at governing treatment.
- Dependence premise not supported on all symbols in cTrader (paired-difference ACF outside band).

### 11.3 Unresolved / what the apparatus does not settle (inference)

- Whether vol-responsive SIZE improves capital-normalised outcomes after cost is **not** answered
  (no spread charged; no verdict).
- Whether selection quality is real after regime matching is arm- and cell-specific; many matched
  contrasts sit near zero relative to their own bootstrap SE.
- H4 vs H1 is a separate population each time; no cross-domain pooling is licensed.
- Whether vol-state alone filters the **baseline** (as distinct from SIZE-by-regime in §7.5) is
  addressed descriptively in the operator probe §15 — not a predeclared primary estimand.

---

## 12. What would make the headline numbers wrong

1. **Reading scale and selection on one σ̂ ladder** — forbidden under R4; denominators differ.
2. **Treating MDE_Z as a resolve bar** or reintroducing WASH/UNPOWERED language — withdrawn (A6/A7).
3. **Using preflight order counts or Step-3 0.022–0.150 as gates** — R1/R5; historical context only.
4. **Quoting estimand_validation occupancy/Sharpe as strategy performance** — lattice-wide apparatus
   figure (`estimand_validation_physicality_scope` warning on every summary).
5. **Ignoring exposure vs selectivity** — raw paired SIZE differences can look like “edge” when
   they are mostly (E[size]−1)×baseline mean.
6. **Charging no spread then claiming tradability** — prohibited.
7. **Rewalking the purged pre-fix emission** — deleted; only this re-emission is current.

---

## 13. Where the complete tables live

```text
python/experiments/SPDR-024/results/
  analysis/{ctrader_H1,ctrader_H4,crypto_H1,crypto_H4}/
    baseline_characterisation.parquet
    scale_channel_estimates.parquet
    selection_channel_estimates.parquet
    pool_filter_ladder.parquet
    paired_difference_dependence.json
    analysis_summary.json
    episodes.parquet
  analysis/probes/   # §15 baseline vol-state filter probe CSVs
  preflight/{cell}.json
  selfcheck/{cell}/
  performance/{cell}.json
  estimand_validation_{cell}.json
```

Screen summary: `python/experiments/SPDR-024/screen.md`

Defect record + operator decision §13:
`docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/mde-floor-defect-spdr024.md`

Claude pre-run review:
`docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md`

---


---

## Appendix A — Per-symbol scale snapshots (governing, PRIMARY, regime=ALL)

Selected components for readability; full POOLED and PER_SYMBOL tables are in
`scale_channel_estimates.parquet`.

### ctrader_H1

| component | symbol | est σ̂ | mde σ̂ | n_trades | SE |
|---|---|---:|---:|---:|---:|
| LEVEL_NOW | EURUSD | -0.0517 | 0.1129 | 624 | 0.0403 |
| LEVEL_NOW | USTEC | 0.0339 | 0.1244 | 501 | 0.0444 |
| LEVEL_NOW | XAUUSD | -0.1157 | 0.1167 | 570 | 0.0417 |
| RANGE_SCALE | EURUSD | -0.0747 | 0.1080 | 624 | 0.0386 |
| RANGE_SCALE | USTEC | 0.0169 | 0.1257 | 501 | 0.0449 |
| RANGE_SCALE | XAUUSD | -0.1096 | 0.1180 | 570 | 0.0421 |
| TAIL_RISK | EURUSD | -0.0691 | 0.1080 | 624 | 0.0386 |
| TAIL_RISK | USTEC | 0.0081 | 0.1265 | 501 | 0.0452 |
| TAIL_RISK | XAUUSD | -0.1157 | 0.1167 | 570 | 0.0417 |

### ctrader_H4

| component | symbol | est σ̂ | mde σ̂ | n_trades | SE |
|---|---|---:|---:|---:|---:|
| LEVEL_NOW | EURUSD | 0.0249 | 0.2159 | 166 | 0.0771 |
| LEVEL_NOW | USTEC | 0.0921 | 0.2275 | 148 | 0.0813 |
| LEVEL_NOW | XAUUSD | 0.0358 | 0.2091 | 177 | 0.0747 |
| RANGE_SCALE | EURUSD | 0.0144 | 0.2178 | 166 | 0.0778 |
| RANGE_SCALE | USTEC | 0.1130 | 0.2307 | 148 | 0.0824 |
| RANGE_SCALE | XAUUSD | 0.0376 | 0.2089 | 177 | 0.0746 |
| TAIL_RISK | EURUSD | -0.0029 | 0.2172 | 166 | 0.0776 |
| TAIL_RISK | USTEC | 0.0883 | 0.2294 | 148 | 0.0819 |
| TAIL_RISK | XAUUSD | 0.0485 | 0.2093 | 177 | 0.0748 |

### crypto_H1

| component | symbol | est σ̂ | mde σ̂ | n_trades | SE |
|---|---|---:|---:|---:|---:|
| LEVEL_NOW | 1000BONKUSDT | -0.0793 | 0.1727 | 270 | 0.0617 |
| LEVEL_NOW | 1000LUNCUSDT | -0.0530 | 0.1518 | 340 | 0.0542 |
| LEVEL_NOW | 1000PEPEUSDT | -0.0811 | 0.2043 | 184 | 0.0730 |
| LEVEL_NOW | 1000RATSUSDT | -0.2162 | 0.5084 | 28 | 0.1816 |
| LEVEL_NOW | ADAUSDT | -0.0386 | 0.1268 | 463 | 0.0453 |
| LEVEL_NOW | AVAXUSDT | 0.0045 | 0.1287 | 484 | 0.0460 |
| LEVEL_NOW | BIGTIMEUSDT | 0.0619 | 0.3655 | 58 | 0.1305 |
| LEVEL_NOW | BLURUSDT | -0.0474 | 0.1661 | 279 | 0.0593 |
| LEVEL_NOW | BNBUSDT | -0.0057 | 0.1315 | 444 | 0.0470 |
| LEVEL_NOW | BTCUSDT | -0.0838 | 0.1366 | 406 | 0.0488 |
| LEVEL_NOW | DOGEUSDT | -0.0241 | 0.1293 | 465 | 0.0462 |
| LEVEL_NOW | DYDXUSDT | 0.1124 | 0.1316 | 423 | 0.0470 |
| LEVEL_NOW | ETHUSDT | -0.0314 | 0.1364 | 419 | 0.0487 |
| LEVEL_NOW | GALAUSDT | -0.0519 | 0.1287 | 441 | 0.0460 |
| LEVEL_NOW | INJUSDT | 0.0350 | 0.1289 | 469 | 0.0460 |
| LEVEL_NOW | LINKUSDT | 0.0216 | 0.1198 | 531 | 0.0428 |
| LEVEL_NOW | MATICUSDT | -0.0403 | 0.0960 | 850 | 0.0343 |
| LEVEL_NOW | OPUSDT | -0.0951 | 0.1208 | 527 | 0.0431 |
| LEVEL_NOW | ORDIUSDT | -0.1017 | 0.2073 | 180 | 0.0740 |
| LEVEL_NOW | PYTHUSDT | -0.0440 | 0.5537 | 25 | 0.1978 |
| LEVEL_NOW | SEIUSDT | -0.0420 | 0.2618 | 112 | 0.0935 |
| LEVEL_NOW | SOLUSDT | -0.1072 | 0.1319 | 438 | 0.0471 |
| LEVEL_NOW | TIAUSDT | -0.1862 | 0.4042 | 46 | 0.1444 |
| LEVEL_NOW | WLDUSDT | -0.0631 | 0.2277 | 149 | 0.0813 |
| LEVEL_NOW | XRPUSDT | -0.0418 | 0.1324 | 438 | 0.0473 |
| RANGE_SCALE | 1000BONKUSDT | -0.1165 | 0.1716 | 270 | 0.0613 |
| RANGE_SCALE | 1000LUNCUSDT | -0.0146 | 0.1475 | 340 | 0.0527 |
| RANGE_SCALE | 1000PEPEUSDT | -0.0961 | 0.2084 | 184 | 0.0744 |
| RANGE_SCALE | 1000RATSUSDT | -0.2893 | 0.5150 | 28 | 0.1839 |
| RANGE_SCALE | ADAUSDT | 0.0125 | 0.1299 | 463 | 0.0464 |
| RANGE_SCALE | AVAXUSDT | 0.0558 | 0.1270 | 484 | 0.0454 |
| RANGE_SCALE | BIGTIMEUSDT | -0.0606 | 0.3739 | 58 | 0.1335 |
| RANGE_SCALE | BLURUSDT | 0.0056 | 0.1672 | 279 | 0.0597 |
| RANGE_SCALE | BNBUSDT | 0.0058 | 0.1312 | 444 | 0.0469 |
| RANGE_SCALE | BTCUSDT | 0.0557 | 0.1398 | 406 | 0.0499 |
| RANGE_SCALE | DOGEUSDT | 0.0101 | 0.1299 | 465 | 0.0464 |
| RANGE_SCALE | DYDXUSDT | 0.0959 | 0.1359 | 423 | 0.0485 |
| RANGE_SCALE | ETHUSDT | 0.0946 | 0.1420 | 419 | 0.0507 |
| RANGE_SCALE | GALAUSDT | -0.0681 | 0.1321 | 441 | 0.0472 |
| RANGE_SCALE | INJUSDT | 0.0331 | 0.1316 | 469 | 0.0470 |
| RANGE_SCALE | LINKUSDT | 0.0667 | 0.1208 | 531 | 0.0431 |
| RANGE_SCALE | MATICUSDT | 0.0099 | 0.0967 | 850 | 0.0345 |
| RANGE_SCALE | OPUSDT | -0.0658 | 0.1220 | 527 | 0.0436 |
| RANGE_SCALE | ORDIUSDT | -0.1112 | 0.2072 | 180 | 0.0740 |
| RANGE_SCALE | PYTHUSDT | 0.1226 | 0.5416 | 25 | 0.1934 |
| RANGE_SCALE | SEIUSDT | -0.0552 | 0.2643 | 112 | 0.0944 |
| RANGE_SCALE | SOLUSDT | -0.0942 | 0.1321 | 438 | 0.0472 |
| RANGE_SCALE | TIAUSDT | -0.0011 | 0.4089 | 46 | 0.1460 |
| RANGE_SCALE | WLDUSDT | -0.0760 | 0.2273 | 149 | 0.0812 |
| RANGE_SCALE | XRPUSDT | -0.0238 | 0.1319 | 438 | 0.0471 |
| TAIL_RISK | 1000BONKUSDT | -0.0634 | 0.1758 | 270 | 0.0628 |
| TAIL_RISK | 1000LUNCUSDT | -0.0372 | 0.1485 | 340 | 0.0531 |
| TAIL_RISK | 1000PEPEUSDT | -0.1399 | 0.2030 | 184 | 0.0725 |
| TAIL_RISK | 1000RATSUSDT | -0.3212 | 0.5186 | 28 | 0.1852 |
| TAIL_RISK | ADAUSDT | -0.0391 | 0.1272 | 463 | 0.0454 |
| TAIL_RISK | AVAXUSDT | 0.0096 | 0.1275 | 484 | 0.0455 |
| TAIL_RISK | BIGTIMEUSDT | 0.0619 | 0.3655 | 58 | 0.1305 |
| TAIL_RISK | BLURUSDT | -0.0356 | 0.1701 | 279 | 0.0607 |
| TAIL_RISK | BNBUSDT | -0.0063 | 0.1318 | 444 | 0.0471 |
| TAIL_RISK | BTCUSDT | -0.0723 | 0.1357 | 406 | 0.0485 |
| TAIL_RISK | DOGEUSDT | -0.0241 | 0.1293 | 465 | 0.0462 |
| TAIL_RISK | DYDXUSDT | 0.1217 | 0.1328 | 423 | 0.0474 |
| TAIL_RISK | ETHUSDT | 0.0410 | 0.1398 | 419 | 0.0499 |
| TAIL_RISK | GALAUSDT | -0.0421 | 0.1302 | 441 | 0.0465 |
| TAIL_RISK | INJUSDT | 0.0299 | 0.1290 | 469 | 0.0461 |
| TAIL_RISK | LINKUSDT | 0.0223 | 0.1197 | 531 | 0.0428 |
| TAIL_RISK | MATICUSDT | -0.0324 | 0.0954 | 850 | 0.0341 |
| TAIL_RISK | OPUSDT | -0.0699 | 0.1227 | 527 | 0.0438 |
| TAIL_RISK | ORDIUSDT | -0.0668 | 0.2138 | 180 | 0.0764 |
| TAIL_RISK | PYTHUSDT | -0.1831 | 0.5494 | 25 | 0.1962 |
| TAIL_RISK | SEIUSDT | -0.0454 | 0.2616 | 112 | 0.0934 |
| TAIL_RISK | SOLUSDT | -0.0988 | 0.1316 | 438 | 0.0470 |
| TAIL_RISK | TIAUSDT | -0.1862 | 0.4042 | 46 | 0.1444 |
| TAIL_RISK | WLDUSDT | -0.0802 | 0.2257 | 149 | 0.0806 |
| TAIL_RISK | XRPUSDT | -0.0377 | 0.1320 | 438 | 0.0471 |

### crypto_H4

| component | symbol | est σ̂ | mde σ̂ | n_trades | SE |
|---|---|---:|---:|---:|---:|
| LEVEL_NOW | 1000BONKUSDT | -0.0179 | 0.3575 | 65 | 0.1277 |
| LEVEL_NOW | 1000LUNCUSDT | 0.1512 | 0.3142 | 79 | 0.1122 |
| LEVEL_NOW | 1000PEPEUSDT | -0.0082 | 0.3732 | 52 | 0.1333 |
| LEVEL_NOW | 1000RATSUSDT | 0.6140 | 1.1097 | 5 | 0.3963 |
| LEVEL_NOW | ADAUSDT | 0.0422 | 0.2533 | 115 | 0.0905 |
| LEVEL_NOW | AVAXUSDT | -0.0334 | 0.2534 | 123 | 0.0905 |
| LEVEL_NOW | BIGTIMEUSDT | 0.0775 | 0.7206 | 15 | 0.2574 |
| LEVEL_NOW | BLURUSDT | 0.0600 | 0.3493 | 67 | 0.1248 |
| LEVEL_NOW | BNBUSDT | 0.0548 | 0.2447 | 123 | 0.0874 |
| LEVEL_NOW | BTCUSDT | 0.1029 | 0.2947 | 87 | 0.1053 |
| LEVEL_NOW | DOGEUSDT | 0.0515 | 0.2738 | 100 | 0.0978 |
| LEVEL_NOW | DYDXUSDT | 0.0207 | 0.2586 | 120 | 0.0924 |
| LEVEL_NOW | ETHUSDT | 0.0975 | 0.3020 | 85 | 0.1079 |
| LEVEL_NOW | GALAUSDT | 0.1515 | 0.2580 | 114 | 0.0921 |
| LEVEL_NOW | INJUSDT | -0.0327 | 0.2594 | 117 | 0.0926 |
| LEVEL_NOW | LINKUSDT | -0.0299 | 0.2612 | 114 | 0.0933 |
| LEVEL_NOW | MATICUSDT | 0.0734 | 0.1985 | 190 | 0.0709 |
| LEVEL_NOW | OPUSDT | 0.0853 | 0.2629 | 118 | 0.0939 |
| LEVEL_NOW | ORDIUSDT | -0.2055 | 0.4266 | 44 | 0.1523 |
| LEVEL_NOW | PYTHUSDT | 0.0570 | 0.9760 | 7 | 0.3486 |
| LEVEL_NOW | SEIUSDT | 0.0101 | 0.5147 | 29 | 0.1838 |
| LEVEL_NOW | SOLUSDT | 0.0692 | 0.2839 | 96 | 0.1014 |
| LEVEL_NOW | TIAUSDT | -0.2200 | 0.7648 | 13 | 0.2731 |
| LEVEL_NOW | WLDUSDT | 0.1976 | 0.5155 | 29 | 0.1841 |
| LEVEL_NOW | XRPUSDT | 0.1514 | 0.2785 | 96 | 0.0995 |
| RANGE_SCALE | 1000BONKUSDT | -0.1525 | 0.3550 | 65 | 0.1268 |
| RANGE_SCALE | 1000LUNCUSDT | 0.1313 | 0.3107 | 79 | 0.1110 |
| RANGE_SCALE | 1000PEPEUSDT | -0.1304 | 0.3745 | 52 | 0.1338 |
| RANGE_SCALE | 1000RATSUSDT | 0.6140 | 1.1097 | 5 | 0.3963 |
| RANGE_SCALE | ADAUSDT | -0.0398 | 0.2539 | 115 | 0.0907 |
| RANGE_SCALE | AVAXUSDT | 0.0946 | 0.2463 | 123 | 0.0880 |
| RANGE_SCALE | BIGTIMEUSDT | 0.3342 | 0.7053 | 15 | 0.2519 |
| RANGE_SCALE | BLURUSDT | -0.1146 | 0.3439 | 67 | 0.1228 |
| RANGE_SCALE | BNBUSDT | 0.0182 | 0.2445 | 123 | 0.0873 |
| RANGE_SCALE | BTCUSDT | 0.1931 | 0.2964 | 87 | 0.1058 |
| RANGE_SCALE | DOGEUSDT | 0.0617 | 0.2765 | 100 | 0.0988 |
| RANGE_SCALE | DYDXUSDT | 0.0471 | 0.2559 | 120 | 0.0914 |
| RANGE_SCALE | ETHUSDT | 0.2244 | 0.3004 | 85 | 0.1073 |
| RANGE_SCALE | GALAUSDT | 0.1680 | 0.2645 | 114 | 0.0945 |
| RANGE_SCALE | INJUSDT | 0.0251 | 0.2591 | 117 | 0.0925 |
| RANGE_SCALE | LINKUSDT | 0.1472 | 0.2612 | 114 | 0.0933 |
| RANGE_SCALE | MATICUSDT | 0.0420 | 0.2035 | 190 | 0.0727 |
| RANGE_SCALE | OPUSDT | 0.0562 | 0.2636 | 118 | 0.0942 |
| RANGE_SCALE | ORDIUSDT | -0.1065 | 0.4235 | 44 | 0.1513 |
| RANGE_SCALE | PYTHUSDT | 0.4491 | 0.9848 | 7 | 0.3517 |
| RANGE_SCALE | SEIUSDT | 0.0171 | 0.5154 | 29 | 0.1841 |
| RANGE_SCALE | SOLUSDT | 0.0275 | 0.2865 | 96 | 0.1023 |
| RANGE_SCALE | TIAUSDT | 0.1205 | 0.7513 | 13 | 0.2683 |
| RANGE_SCALE | WLDUSDT | 0.1317 | 0.5143 | 29 | 0.1837 |
| RANGE_SCALE | XRPUSDT | 0.1280 | 0.2784 | 96 | 0.0994 |
| TAIL_RISK | 1000BONKUSDT | -0.0222 | 0.3580 | 65 | 0.1279 |
| TAIL_RISK | 1000LUNCUSDT | 0.2430 | 0.3168 | 79 | 0.1131 |
| TAIL_RISK | 1000PEPEUSDT | -0.0996 | 0.3711 | 52 | 0.1325 |
| TAIL_RISK | 1000RATSUSDT | 0.3394 | 1.1361 | 5 | 0.4057 |
| TAIL_RISK | ADAUSDT | 0.0422 | 0.2533 | 115 | 0.0905 |
| TAIL_RISK | AVAXUSDT | -0.0297 | 0.2528 | 123 | 0.0903 |
| TAIL_RISK | BIGTIMEUSDT | 0.0727 | 0.7207 | 15 | 0.2574 |
| TAIL_RISK | BLURUSDT | -0.0764 | 0.3466 | 67 | 0.1238 |
| TAIL_RISK | BNBUSDT | 0.0584 | 0.2448 | 123 | 0.0874 |
| TAIL_RISK | BTCUSDT | 0.1104 | 0.2932 | 87 | 0.1047 |
| TAIL_RISK | DOGEUSDT | 0.0513 | 0.2737 | 100 | 0.0977 |
| TAIL_RISK | DYDXUSDT | -0.0072 | 0.2611 | 120 | 0.0933 |
| TAIL_RISK | ETHUSDT | 0.1050 | 0.3030 | 85 | 0.1082 |
| TAIL_RISK | GALAUSDT | 0.1562 | 0.2576 | 114 | 0.0920 |
| TAIL_RISK | INJUSDT | -0.0210 | 0.2585 | 117 | 0.0923 |
| TAIL_RISK | LINKUSDT | -0.0197 | 0.2610 | 114 | 0.0932 |
| TAIL_RISK | MATICUSDT | 0.0854 | 0.1988 | 190 | 0.0710 |
| TAIL_RISK | OPUSDT | 0.1091 | 0.2610 | 118 | 0.0932 |
| TAIL_RISK | ORDIUSDT | -0.0289 | 0.4255 | 44 | 0.1520 |
| TAIL_RISK | PYTHUSDT | 0.3780 | 0.9726 | 7 | 0.3473 |
| TAIL_RISK | SEIUSDT | 0.0101 | 0.5147 | 29 | 0.1838 |
| TAIL_RISK | SOLUSDT | 0.1096 | 0.2843 | 96 | 0.1015 |
| TAIL_RISK | TIAUSDT | 0.2774 | 0.7336 | 13 | 0.2620 |
| TAIL_RISK | WLDUSDT | 0.2018 | 0.5156 | 29 | 0.1842 |
| TAIL_RISK | XRPUSDT | 0.1233 | 0.2759 | 96 | 0.0985 |

## Appendix B — Question index

| # | Question | Section |
|---|---|---|
| Q1 | Did integrity / estimand / fence clear on all cells? | §2 |
| Q2 | What cost is charged? | §1 |
| Q3 | What are the populations and lenses? | §4 |
| Q4 | What does preflight say about SIZE magnitude capacity? | §5 |
| Q5 | What is the FIXED baseline level? | §6 |
| Q6 | What does each SIZE arm do on the PRIMARY paired scale? | §7 |
| Q7 | Continuous vs discrete SIZE where both exist? | §7.3 |
| Q8 | Do variance treatments agree? | §7.4 |
| Q9 | Does the effect differ by HIGH/LOW regime? | §7.5 |
| Q10 | Does selection (admitted vs declined) look real after regime match? | §8 |
| Q11 | Is the pooled figure concentrated in a few symbols? | §9, App A |
| Q12 | Is the unchunked dependence premise supported? | §10 |
| Q13 | What would make the numbers wrong? | §12 |
| Q14 | Can decision-time vol-state (HIGH/LOW) act as a filter on the baseline alone? | §15 |

## 14. Hand-off

This experiment characterises SIZE adaptive management on the breakout substrate under TRAIN-only,
gross, no-spread conditions across four cells. It produces the map; the operator interprets economic
content and any next research action. No family action, no XENA gate, no TEST read was taken here.

An operator-directed post-hoc probe (§15) re-slices the **unmodified baseline** by the emitted
vol-state label (mean bps and per-trade Sharpe). That probe is descriptive only and is not a
predeclared primary estimand of the SIZE lattice.

---

## 15. Operator probe — vol-state conditioning as a baseline filter

**Scope.** Post-hoc descriptive probe (operator request after the AMENDMENT-7 re-emission analysis).
**Not** part of the predeclared SIZE arm lattice; **not** a research verdict or deploy claim.

**Question.** On the plain breakout (`FIXED_SIZE_UNIT` only), does decision-time volatility state
(HIGH vs LOW) act as a useful **selectivity stratum** — i.e. would keeping only HIGH (or only LOW)
fills improve mean gross bps and/or risk-adjusted quality relative to the other state / to ALL?

**Artefacts.**

```text
python/experiments/SPDR-024/analysis_code/probe_baseline_regime_filter.py
python/experiments/SPDR-024/results/analysis/probes/
  baseline_regime_origin_rates.csv
  baseline_regime_performance_pooled.csv
  baseline_regime_performance_persymbol.csv
  baseline_regime_filter_contrasts.csv
```

**Method (observed).**

- Population: `FIXED_SIZE_UNIT` origins and closed fills; TRAIN emission already on disk.
- Label: `regime_state` ∈ {HIGH, LOW, UNKNOWN}.
- Origin lens: order rate and fill rate by regime.
- Fill lens: mean `outcome_bps` and **trade Sharpe** =
  `mean(outcome_bps) / std(outcome_bps)` (per-trade, not annualised; gross; no risk-free).
- Uncertainty: block bootstrap, block length ≈ √n, 2000 draws; CI tag `ci+` / `ci-` / `cross0`.
- Contrast: HIGH − LOW on mean and on Sharpe; also only-HIGH vs ALL.
- Per-symbol map; POOLED is disclosure-only unless symbols agree.

**Relation to §7.5.** Section 7.5 stratifies **SIZE (adaptive − fixed)** by HIGH/LOW.
This section stratifies the **baseline alone** by HIGH/LOW — a different object.

### 15.1 Label level (origin vs fill) — E1

| Design (E1) | Observed on this emission |
|---|---|
| Regime per **origin** | Yes — every origin row carries `regime_state` and `regime_episode_id`, including non-fills |
| Regime per **episode** | Yes on admitted fills — same fields on the closed row |
| Separate fill-time re-label | **No** second column; label is attached at **`decision_ts`** (join to feature panel), not at `entry_ts` |

**Observed.** Same `origin_id` never disagrees on `regime_state` across the 38 arms. Non-admitted
origins have regime present and `entry_ts` / `outcome_bps` null. Fills inherit the origin’s
decision-time label.

**Source of the binary cut (observed, implementation).** `REGIME_COLUMN = level_now`, itself
`HIGH` if `rv20 ≥` rolling median of `rv20` else `LOW` (features panel). Same object as the
`LEVEL_NOW` arm’s gate — so for that arm alone, “stratify by regime” and “stratify by own gate”
coincide (disclosed in `spdr024.py`).

**Episode table vs continuous vol.** Analysis episode frames store the **label only**. Continuous
`rv20` / `lvl_pct` live on run `features.parquet` (offline re-bin possible; not used in this probe).

### 15.2 Origin-level activity by regime (POOLED)

| Cell | Fill rate HIGH | Fill rate LOW | ALL | n fills HIGH / LOW |
|---|---:|---:|---:|---:|
| ctrader_H1 | 0.0846 | 0.0844 | 0.0845 | 819 / 870 |
| ctrader_H4 | 0.1109 | 0.0678 | 0.0900 | 289 / 188 |
| crypto_H1 | 0.0975 | 0.0696 | 0.0829 | 4639 / 3752 |
| crypto_H4 | 0.0880 | 0.0600 | 0.0737 | 1069 / 865 |

**Observed.** On crypto and cTrader H4, HIGH origins order and fill more often than LOW.
cTrader H1 fill rates are essentially equal. **Inference.** HIGH is a busier state on most cells —
more opportunities, not automatically better quality.

### 15.3 Fill-level baseline performance — mean bps and trade Sharpe (POOLED)

Size = 1 on `FIXED_SIZE_UNIT`, so mean bps equals capital-normalised mean on this arm.

| Cell | Regime | n | Mean bps | Mean CI | Trade Sharpe | Sharpe CI | σ (bps) | Win share |
|---|---|---:|---:|---|---:|---|---:|---:|
| ctrader_H1 | ALL | 1695 | +1.10 | cross0* | +0.041 | ci+ | 27.0 | 0.515 |
| ctrader_H1 | HIGH | 819 | +1.53 | cross0 | +0.053 | cross0 | 28.7 | 0.501 |
| ctrader_H1 | LOW | 870 | +0.73 | cross0 | +0.028 | cross0 | 25.5 | 0.528 |
| ctrader_H4 | ALL | 491 | −2.48 | cross0 | −0.059 | cross0 | 42.2 | 0.438 |
| ctrader_H4 | HIGH | 289 | −3.18 | cross0 | −0.073 | cross0 | 43.4 | 0.426 |
| ctrader_H4 | LOW | 188 | −1.91 | cross0 | −0.048 | cross0 | 39.7 | 0.447 |
| crypto_H1 | ALL | 8469 | +5.21 | ci+ | +0.034 | ci+ | 152.3 | 0.461 |
| crypto_H1 | HIGH | 4639 | +8.30 | ci+ | +0.050 | ci+ | 165.5 | 0.468 |
| crypto_H1 | LOW | 3751 | +2.39 | cross0 | +0.019 | cross0 | 124.8 | 0.453 |
| crypto_H4 | ALL | 2003 | −8.80 | cross0 | −0.032 | cross0 | 272.2 | 0.431 |
| crypto_H4 | HIGH | 1069 | −13.43 | cross0 | −0.046 | cross0 | 291.4 | 0.416 |
| crypto_H4 | LOW | 865 | −2.06 | cross0 | −0.009 | cross0 | 239.5 | 0.452 |

\*Bootstrap CI for cTrader H1 ALL mean sits on the edge of zero across seeds; level Sharpe for ALL
is ci+. UNKNOWN strata are small and omitted from the filter contrast.

**Observed.** Win share barely moves by regime. Medians often sit near zero or negative while means
are positive (fat right tail). HIGH strata typically show **higher mean and higher σ** than LOW.

### 15.4 Filter contrast — HIGH minus LOW (selectivity test)

| Cell | Δ mean (bps) | Mean CI | Δ Sharpe | Sharpe CI | HIGH / LOW Sharpe | Retention if only HIGH |
|---|---:|---|---:|---|---:|---:|
| ctrader_H1 | +0.80 | cross0 | +0.025 | cross0 | 0.053 / 0.028 | 0.48 |
| ctrader_H4 | −1.27 | cross0 | −0.025 | cross0 | −0.073 / −0.048 | 0.59 |
| crypto_H1 | +5.91 | cross0 | +0.031 | cross0 | 0.050 / 0.019 | 0.55 |
| crypto_H4 | −11.37 | cross0 | −0.038 | cross0 | −0.046 / −0.009 | 0.53 |

**only-HIGH vs ALL (POOLED, point estimates):**

| Cell | Δ mean (bps) | Δ Sharpe |
|---|---:|---:|
| ctrader_H1 | +0.43 | +0.013 |
| ctrader_H4 | −0.70 | −0.015 |
| crypto_H1 | +3.09 | +0.016 |
| crypto_H4 | −4.63 | −0.014 |

**Observed.** No cell’s HIGH − LOW contrast excludes zero on **mean or Sharpe**. Domain directions
disagree: H1 cells point mildly toward HIGH on mean/Sharpe; H4 cells point toward LOW (HIGH more
negative). **Inference.** Decision-time vol-state is **not** a stable cross-domain filter on this
baseline under TRAIN gross conditions.

### 15.5 Per-symbol concentration

| Cell | Symbols (n≥5 both sides) | HIGH better on mean (point) | HIGH better on Sharpe (point) | Mean CI clear of 0 | Sharpe CI clear of 0 |
|---|---:|---:|---:|---:|---:|
| ctrader_H1 | 3 | 2/3 | 2/3 | 1/3 | 0/3 |
| ctrader_H4 | 3 | 0/3 | 0/3 | 0/3 | 0/3 |
| crypto_H1 | 25 | 17/25 | 16/25 | 1/25 | 3/25 |
| crypto_H4 | 22 | 9/22 | 10/22 | 1/22 | 1/22 |

**cTrader H1 (observed).** EURUSD ~flat; USTEC HIGH worse on point; **XAUUSD** mean HIGH − LOW
≈ +5.0 bps (mean CI ci+); Sharpe HIGH − LOW ≈ +0.15 still **cross0** (HIGH also noisier).

**crypto_H1 (observed).** Pooled direction is majority-shared (~68% of symbols) but almost all
symbol-level HIGH − LOW intervals cross zero. Local sharps: OPUSDT mean and Sharpe ci+ for HIGH
better; BTCUSDT Sharpe ci+; BIGTIME among the worst (Sharpe ci− for HIGH).

**crypto_H4 / ctrader_H4.** Agree with pooled “HIGH not better”; almost no clear CIs.

**Sign agreement with pooled HIGH − LOW:**

| Cell | Mean sign agree | Sharpe sign agree |
|---|---|---|
| ctrader_H1 | 2/3 | 2/3 |
| ctrader_H4 | 3/3 | 3/3 |
| crypto_H1 | 17/25 | 16/25 |
| crypto_H4 | 13/22 | 12/22 |

### 15.6 Symmetric observations and limits

**Consistent patterns (observed).**

- Integrity of the parent emission is unchanged; this probe reuses closed baseline fills only.
- Regime labels are decision-time origin labels, present on fills by inheritance.
- HIGH often busier (higher fill rate) on crypto and cTrader H4.
- HIGH − LOW never clears zero on mean **or** Sharpe at cell POOLED level.
- Sharpe gains are smaller than raw mean gains where HIGH σ exceeds LOW σ.
- Domains disagree (H1 vs H4); symbols often disagree or fail to clear noise.

**Contrary / cell-specific (observed).**

- crypto_H1 HIGH **level** mean and level Sharpe both ci+ vs zero; the **contrast** HIGH − LOW
  still crosses zero.
- XAUUSD H1 mean contrast ci+; Sharpe contrast does not.
- H4: HIGH looks worse than LOW on point estimates (mean and Sharpe).

**What this probe does not settle (inference).**

- Costed / net selectivity (spread still uncharged).
- Occupancy-inclusive origin expectancy treating non-fills as zero (fill-level only here).
- Ternary LOW/MID/HIGH cuts (episode table is binary; continuous `rv20`/`lvl_pct` are on
  features only — left for a separate offline probe if wanted).
- Whether adaptive SIZE should condition on vol-state (that is §7.5 / scale channel, not this cut).

**Reading guardrails.** Gross only; probe-grade block bootstrap (not the full V-A/V-B/V-C governing
ladder of §7); no tradable/deployable claim; no family action.

### 15.7 One-line map for the operator

Relative to taking all baseline fills, **decision-time HIGH vs LOW is not a clean multi-cell
selectivity filter** on this breakout: residual H1 (especially crypto) point estimates favor HIGH
on mean and Sharpe but fail the HIGH − LOW interval test; H4 points the other way; concentration
and cost remain open.

