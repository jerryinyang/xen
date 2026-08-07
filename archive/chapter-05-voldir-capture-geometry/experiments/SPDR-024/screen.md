# SPDR-024 screen summary (post AMENDMENT-7 re-screen)

TRAIN-only four-cell re-emission after the detection-floor apparatus fix (AMENDMENT-7).
This is the operational screen record; the full descriptive analysis is in `analysis.md`.

## Boundary

- Band: TRAIN only. No TEST / holdout contact.
- Cost: spread not charged; gross figures; prohibited claims: fully-net, cost-complete, tradable, deployable.
- No research verdict, arm ranking, family action, or XENA gate in this document.

## Cell status

| Cell | wall_s | blocking_pass | HARD | failed | preflight label | n_fills (preflight) |
|---|---:|---|---:|---|---|---:|
| ctrader_H1 | 660.13 | True | 17 | [] | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` | 3846 |
| ctrader_H4 | 366.68 | True | 17 | [] | `DESCRIPTIVE_SIZE_MAGNITUDE_FLOOR_ABOVE_CEILING` | 1061 |
| crypto_H1 | 3026.11 | True | 17 | [] | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` | 17717 |
| crypto_H4 | 1607.72 | True | 17 | [] | `CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING` | 3982 |

## Step inventory (per cell, from performance JSON)

### ctrader_H1

| step | wall_s | returncode |
|---|---:|---:|
| hold_phase | 53.41 | 0 |
| cap_rule | 0.32 | 0 |
| full_grid | 83.75 | 0 |
| future_shift_tripwire | 83.59 | 0 |
| determinism_replay | 186.3 | 0 |
| estimand_gate | 1.52 | 0 |
| selfcheck | 29.57 | 0 |
| analysis | 221.67 | 0 |

### ctrader_H4

| step | wall_s | returncode |
|---|---:|---:|
| hold_phase | 41.02 | 0 |
| cap_rule | 0.28 | 0 |
| full_grid | 51.58 | 0 |
| future_shift_tripwire | 48.91 | 0 |
| determinism_replay | 122.22 | 0 |
| estimand_gate | 0.73 | 0 |
| selfcheck | 9.57 | 0 |
| analysis | 92.37 | 0 |

### crypto_H1

| step | wall_s | returncode |
|---|---:|---:|
| hold_phase | 214.55 | 0 |
| cap_rule | 0.46 | 0 |
| full_grid | 314.58 | 0 |
| future_shift_tripwire | 322.78 | 0 |
| determinism_replay | 840.2 | 0 |
| estimand_gate | 6.34 | 0 |
| selfcheck | 163.61 | 0 |
| analysis | 1163.59 | 0 |

### crypto_H4

| step | wall_s | returncode |
|---|---:|---:|
| hold_phase | 170.93 | 0 |
| cap_rule | 0.27 | 0 |
| full_grid | 198.19 | 0 |
| future_shift_tripwire | 200.7 | 0 |
| determinism_replay | 534.76 | 0 |
| estimand_gate | 2.42 | 0 |
| selfcheck | 41.03 | 0 |
| analysis | 459.42 | 0 |

## Cap rule

All four cells: `NOT_APPLICABLE` (native one-bar hold; duration grid cannot bind ≤5%).

## HARD checks (names)

`arm_lattice_matches_design`, `causal_t_minus_1_provenance`, `deterministic_rerun`, `e1_regime_label_present`, `e2_counterfactual_present_and_non_zero_fill`, `e4_exit_reason_and_entry_ts_populated`, `e5_hold_duration_and_cap_flag_present`, `e6_capital_normalised_estimand_present`, `estimand_reconciliation`, `future_shift_tripwire_collapse`, `golden_traces_match_design`, `hard_check_count_reconciled_by_name`, `nautilus_order_fill_position_reconciliation`, `no_cost_charged`, `time_derangement_absent`, `train_holdout_fence`, `train_only_band_and_domain`

## Artefacts

```
results/{runs,selfcheck,analysis,preflight,performance,logs}/
analysis.md  # full descriptive analysis
```
