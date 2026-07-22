# INFR-014 design-clause → code map (QA input)

| Design clause | Code location |
|---|---|
| WP0 universe_selection API §9.1 | `python/src/xen/nautilus/universe_selection.py` |
| Causality ≤t−1 / ε=1ns | `rank_from_volume_panel`, `_asof_cutoff_ns` |
| HOLDOUT refuse | `select_membership` band check + `FenceViolation` |
| rule_hash | `rule_hash(SelectionRule)` |
| WP1 CAL form §5.4 | `python/src/xen/xena/calibration_bybit.py` |
| CLS-FILTER factory §4.1 | `make_filter_null_universe` |
| CLS-EPISODE factory §4.1 | `make_episode_null_universe` |
| Factories must differ | module-level `assert factory_fingerprint(...)` |
| L-26 hard refuse costless stage-1 | `assert_stage1_net_binding` + `run_two_stage` |
| stage-1 g_net + charge_costs | `run_restart(..., score_kind="g_net")`, `OracleConfig(charge_costs=True)` |
| stage-2 α̂ = gross LCB | `eval_lcb_legs(..., net=False)` → `gross_pass` |
| stage-2 net deployability field | `eval_lcb_legs(..., net=True)` → `net_pass` |
| COST-STACK | `bybit_cost_bps_for_hold` → `bybit_round_trip_cost_bps` |
| GAP spread=5.0 | `GAP_SPREAD_BPS`, `results/cost_pins.json` |
| Seeds 91k/92k design, 93k/94k confirm | `DESIGN_SEEDS`, `CONFIRM_SEEDS` |
| Bite plant §4.1 / §5 | `bite_check`, thresholds 0.5 / 0.125 |
| Bite FAIL = TERMINAL | `run_design` early return, no confirm |
| No optional stopping | `confirm_gate` fixed `n_null`; no peek-and-extend |
| Gate point α̂ ≤0.05 ∧ cov | `confirm_gate` certified = alpha_ok ∧ coverage_ok |
| Wilson disclosure-only | recorded in `alpha_wilson_95`, not gate |
| WP4 registry §4.2 | `write_bybit_registry`, `verify_bybit_registry` |
| pin_usage.limit_print_sole_certify_forbidden | registry JSON field |
| partial-writes:false / ≥1 certifiable | `write_bybit_registry` IntegrityError if zero |
| ch03 pin never binding | `VOID_PRIORS`; no load of `db87dc1a` |
| WP5 S1 smoke §8 | `experiments/INFR-014/code/run_s1_smoke.py` |
| L-30 dispose_on_completion=False | `BacktestRunConfig(dispose_on_completion=False)` |
| L-29 fill-ts anchor | `_fill_ts_anchor_check` |
| WP6 next-open L-27 | `xen.xena.fill_basis.next_open_discriminating_control` |
| L-28 derangement | design control; CAL null banks are synthetic path nulls (no index permutation in α̂ path) |
| search score_kind plumbing | `xen.xena.search.run_restart(score_kind=...)` |
| certify fold score_kind | `xen.xena.certify.rank_on_folds` / `certify_and_rank` |

**Deviations:** none silent. Registry tool path uses real module `fill_basis` (design §7.3 forbids parallel `fills_basis` package; §4.2 schema string had a typo).

### Post-QA Issues 9–13 (2026-07-17)

| Issue | Location |
|---|---|
| 9 confirm cov seeds | `no_search_coverage` — no DESIGN re-pin; `confirm_gate` asserts `seed_bases == CONFIRM_SEEDS` |
| 10 S1 A-vs-B + ADMITTED + estimand | `code/run_s1_smoke.py` rewrite |
| 11 cal_summary | `code/run_cal.py` always writes summary before exit |
| 12 void_priors verify | `verify_bybit_registry` requires VOID prefixes |
| 13 procedure alpha | `confirm_gate` / `e2e_alpha` / `no_search_coverage` take `alpha=` from procedure |
