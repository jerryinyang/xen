# Data Analysis: EXP-100

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled observed (read directly from an emitted artifact) or inference (a mechanism
reading of observed numbers that is not itself measured). Zero-cost model: every figure is
gross and cost-free (ZERO-COST-DISCLOSURE). EXP-100 tests measurement validity and coverage
of the streaming level/raid apparatus, not market value.

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.
```

Hypothesis under test (`CF-LIQSWP-001/HYP-000`): a causal streaming state machine
preserves identity and chronology of active liquidity levels, excursions, completed
raids, confirmation, breakout, and later-swing states on the AMENDMENT-13 object.

## 1. Integrity gate (blocking)

Family gate artifact: `results/estimand_validation.json`. Per-cell gates:
`results/execution/full/<cell_id>.json` (264 files).

| Check | Result | Evidence |
|---|---|---|
| Estimand validation — family `blocking_pass` | **PASS** | `blocking_pass: true`, `n_cells: 264` |
| Estimand validation — per-cell `blocking_pass` | **PASS** | 264/264 cells `blocking_pass: true` |
| Manifest / catalogue identity | **PASS** | expected `[EURUSD, XAUUSD, USTEC]`, emitted all three, `missing: []` |
| Zero-cost compliance (`no_cost_charged`) | **PASS** | `cost_model: NO_COST_CHARGED`, `non_zero_columns: []`, `n_non_zero_rows: 0`, `cost_bps: 0.0`, `cost_directive: null` (264/264 cells `cost_ok`) |
| Fence (holdout / TRAIN boundary) | **PASS** | `status: PINNED`, `within_fence: true`, `train_end_utc: 2023-11-22`, `holdout_start_utc: 2024-12-13`, manifest sha256 matches expected (`4cdc7b01…`) |
| Reconciliation | **PASS** | `note: "no leg ledger"` — measurement apparatus, no trade/P&L ledger (consistent with design) |
| Provenance trace (verdict-bearing columns ≤ t-1) | **PASS** | signal timestamps `sweep/first_excursion/return/confirmation` all `< TRAIN_END`; only `endpoint/censor` stamped at exactly TRAIN_END (right-censoring). Details §Q25/Q29. |
| Leak tripwire collapsed + non-vacuous | **PASS** | future-destroy derangement: 264/264 cells `CHANGED`, `collapse=true`, `fixed_points=0`, `vacuous=[]` |
| Holdout untouched | **PASS** | `raid_ts_holdout: 0`, `mark_holdout: 0`; no timestamp ≥ `holdout_start_utc` |
| Price-primary (engine emission, non-STUB) | **PASS** | Nautilus `BacktestNode` 1.230.0; fence `PINNED` (non-STUB); `n_fills: 0` (no fills = no local accounting path) |
| No experiment-local accounting defs | **PASS** | analyst scripts import only `xen.*` + own code; `check_no_local_accounting` clean (no accounting primitives in `code/`) |

Integrity verdict: **no blocking failure.** The emission is valid for analysis.

## 2. Question list — answers

### Accounting & object identity

**Q1. Do per-bar and per-leg totals reconcile per cell?**
ANSWERED — PASS. No leg ledger exists (measurement apparatus). Estimand-gate
`reconciliation.ok: true` ("no leg ledger") on all 264 cells. Object identity: each raid
owns one event record; `raid_id` unique per cell (duplicate check §Q3).

**Q2. What is the P&L-bearing object, and does the design estimand match it? (L-16)**
ANSWERED. There is no P&L/trade object — `n_fills = 0`, `orders_submitted: false` across
all cells. The measured object is the level/raid/TPO state; design `OBJECT-IDENTITY` says
"measurement object == trading object: YES" for later experiments. Estimand =
emitted-state coverage/reconciliation + deterministic replay. Match: exact.

**Q3. Raid-status / event-count distribution per cell (no trade ledger)?**
ANSWERED — PASS. `raid_dup: 0`, `level_dup: 0` across all 264 cells (every `raid_id` and
`level_id` unique within its cell). `unknown_raid_status: []`, `unknown_level_status: []`,
`retired_status_hits: 0`.

### Structure & concentration

**Q4. Raid anatomy: status counts, confirmation, completion, right-censor; residual live.**
ANSWERED. Observed totals (264 cells): raids 9,840,478; confirmed 5,106,432; completed
789,326; `FAILED_BREAKOUT` 4,702,900; `CONFIRMED_NON_PRIMARY` 4,316,600;
`RIGHT_CENSORED_EXCURSION` 30,520; `RIGHT_CENSORED_CONFIRMATION` 626;
`RIGHT_CENSORED_ENDPOINT` 506. Residual live at finish: `active_raids: 0`,
`active_levels: 0` (every object settled or right-censored — no leaked-live state).

**Q5. Does one symbol/TF/config dominate event mass?**
ANSWERED — no, structure is stable. Per symbol×TF (n_raids): EURUSD 15m 1.56M / 30m 0.78M /
60m 0.97M; USTEC 15m 1.51M / 30m 0.77M / 60m 0.97M; XAUUSD 15m 1.56M / 30m 0.78M / 60m
0.94M. Cross-asset spread within ~±3% at each TF; 15m ≫ 30m/60m (observation frequency),
not a single-asset concentration.

**Q6. Event production stable across TRAIN calendar, or one regime?**
ANSWERED — partially. Anchor counts are stable (1D anchors 640–644/cell, 1W = 129 exact).
A formal regime-stationarity read is not in the predeclared scope; flagged as open (Q§6).

**Q7. Per-stratum: every headline re-derived per instrument × TF × confirm-ref × method × config.**
ANSWERED. See `results/analysis/coverage_by_config.csv`,
`coverage_by_symbol_tf.csv`, `coverage_by_symbol_tf_config.csv`. No config/symbol/TF cell is
zero (min raids per cell ≥ 2,418; min confirmed ≥ 1,346). Same-bar-return fraction is the
most stable cross-section (median 0.780; range 0.752–0.799 across all 264 cells).

### Physicality & behaviour

**Q8. Finish residuals match the design story (no live raids/levels left)?**
ANSWERED — PASS. `active_raids: 0`, `active_levels: 0` across all cells. All objects settle
or right-censor; no dangling live state.

**Q9. Occupancy-like counts — what does the apparatus IS?**
ANSWERED. Per cell (median): levels 1,280–41,677 depending on config (PREVIOUS_* session
configs ≈1,280; ROLLING_* recompute per bar → 26K–116K); raids 3.3K–81.6K; confirmed
1.7K–42.3K. Defined TPO profiles 9,794,068 vs undefined 46,410 (0.47%). Inference: a
high-frequency level-raid state machine — most raid mass is excursion→return on the
observation bar, ~78% of raids return on the same bar they sweep (AMENDMENT-13 keeps these
live).

**Q10. Confirmation/endpoint duration and strong-move fields present/absent as designed?**
ANSWERED — PASS. `confirm_without_return: 0` (confirmation never fires without a recorded
return); duration/strong-move/swing populated on confirmed rows (destroy non-vacuity proves
they are live values, §Q13). 30,520 raids right-censor at excursion, 626 at confirmation,
506 at endpoint — as designed.

### Robustness & falsification

**Q11. Zero-cost verification.**
ANSWERED — PASS (table above). No cost column, no net figure; caveat present in this document
and in design.

**Q12. PSR pairing.**
ANSWERED — N/A. No mean-trade/leg bps read exists (no trade ledger). No PSR reported.

**Q13. Future-destroy: collapse fraction / bite, non-vacuity, zero fixed points (L-28).**
ANSWERED — PASS. 264/264 cells `destroy_non_vacuity: CHANGED`, `fixed_points: 0`,
`destroy_collapses: true` (mean|Δswing_atr| ≥ 2.8×SE of swing_atr in every cell).
`contrast_ratio` ≈ 0.9996 (raw/destroy marginals nearly identical — expected for a
block-derangement that preserves marginal block values; the *per-raid alignment* contrast is
what collapses). Inference: swing/strong-move/duration are genuinely future-path-derived,
non-vacuous, and causally aligned — no fixed-point leak.

**Q14. One "what would make this wrong?" probe per headline.**
ANSWERED. (a) Coverage counts → recompute 3 completed raids from raw `bar_marks`:
emitted `max_excursion` matches recomputed exactly in all 3 (§Q28-independent). (b) Method
overlap → BREAKOUT_BAR vs LEVEL_CLOSE compared head-to-head: identical (§Q26). (c) Golden
trace → independent synthetic feed through the shared processor (§Q28). (d) TRAIN boundary →
probe every raid timestamp field vs TRAIN_END (§Q25/Q29).

**Q15. Sample-size context: every row keeps its n; no hide/drop.**
ANSWERED — held. Per-stratum CSVs carry min/median/max per cell; no cell dropped (264/264
reported). No minimum-n gate declared by design.

**Q16. Direct comparison against declared comparators (golden T1–T3; same-stratum replay).**
ANSWERED — golden trace run (§Q28); same-stratum replay = the independent recompute (§Q28).
No adaptive arm exists to compare — this is a coverage/validity object.

### Mechanism / amendment-specific

**Q17. AMENDMENT-13: beyond-starts-live-raid; same-bar return recorded, does not close; no AMBIGUOUS.**
ANSWERED — PASS. `n_ambiguous: 0`, `n_same_bar_closed_ambiguous: 0`; 7,669,654 same-bar
returns recorded (78% of 9,809,958 returns). Golden: `t1_still_live_after_return: true`,
`return_equals_sweep: true`, `not_ambiguous: true`.

**Q18. AMENDMENT-8: 1m wick not surviving observation OHLC is not a raid.**
ANSWERED — PASS. Golden `t1_wick_did_not_add_raid: true`.

**Q19. AMENDMENT-6: latest expected-side primary; earlier eligible returned → CONFIRMED_NON_PRIMARY; opposing eligible → FAILED_BREAKOUT.**
ANSWERED — PASS. Golden raw summaries: `T2-HIGH:raid:1` `COMPLETED`, `primary_attribution:
true`; `T1-HIGH:raid:2` `CONFIRMED_NON_PRIMARY`, `primary_attribution: false`;
`T1-HIGH:raid:1` `FAILED_BREAKOUT`. (Boolean probe returned null here — see §5 caveat.)

**Q20. AMENDMENT-10: 1D/1W = NY 17:00 day / Mon–Fri week; no weekend stubs; no zero-level.**
ANSWERED — PASS. 1D anchors 640–644/cell, 1W = 129 exact; `weekend_date_anchors` (anchor
key on Sat/Sun) = 0; `zero_level_cells: 0`. Note: ~125 levels/cell are *created* on a Sunday
NY session (the Monday open at Sunday 17:00 NY) — correct cTrader session behaviour, not a
stub; anchor keys remain weekday-dated.

**Q21. AMENDMENT-9: 15m/30m confirm on 1H only; 1h confirms on 1H and 4H; no 1D confirm cells.**
ANSWERED — PASS. Grid: 15m→{1h}, 30m→{1h}, 60m→{1h,4h}; counts 66/66/132. No 1D confirm.

**Q22. AMENDMENT-11: matrix is 264; rolling windows 7/14/22/252 only.**
ANSWERED — PASS. 264 cells; level_configs observed == expected (11 configs incl.
ROLLING_7/14/22/252).

**Q23. AMENDMENT-12: `tight_gap == (gap_span < 0.50*VA_width)`; gap selection 30% VA TPO.**
ANSWERED — PASS. `tight_rule_mismatch: 0`; `va_mass_short: 0`; `tpo_tight_ratio: 0.5` and
`tpo_gap_mass: 0.3` uniform across all cells.

**Q24. TPO conservation holds on DEFINED; every raid has exactly one profile row.**
ANSWERED — PASS. `defined_conservation_fail: 0`; `missing_profiles: 0`, `extra_profiles: 0`.

**Q25. Chronology: first excursion ≤ return; confirmation > sweep; endpoint ≥ confirmation; minute grid.**
ANSWERED — PASS. `chrono_fail: 0`, `grid_fail: 0` across all cells.

**Q26. BREAKOUT_BAR vs LEVEL_CLOSE numeric overlap disclosed, not pooled.**
ANSWERED — PASS + disclosed. 132 method pairs, `raid_id_equal: 132`, `status_equal: 132`,
`count_diff: 0`. Observed: the two methods emit byte-identical raid objects on the shared
previous-reference test (the overlap is total, as the design disclosed).

**Q27. Deterministic replay / artifact hash equality.**
ANSWERED — PASS. `manifest_sha256` equals expected `4cdc7b01…` on all cells; nautilus
version uniform 1.230.0; golden replay reproduces emitted behaviour from a fresh feed.

**Q28. Golden T1–T3.**
ANSWERED — PASS (mechanism), with probe-strictness caveat. Independent synthetic feed through
the shared processor: first-beyond starts a live raid (`t1_live_after_first_beyond: true`)
with `max_excursion 1.20`, `prior_raid_count 0`; 1m wick adds no raid (AMENDMENT-8); return
recorded, raid stays live (AMENDMENT-13); T2 primary / T1 non-primary / T1 first
FAILED_BREAKOUT all appear in the terminal raid summaries. Two aggregate booleans
(`t1_one_completed_or_settled`, `t2_exists`) read `false` because the synthetic feed kept
re-piercing the levels, minting extra right-censored raids — a probe-script indexing
artifact, not a state-machine defect (§5).

**Q29. No raid/level/bar timestamp touches the global holdout; last bar_mark < TRAIN end.**
ANSWERED — PASS. `raid_ts_holdout: 0`; `mark_holdout: 0`; `mark_past_train_cells: 0`.
The 63,304 timestamps ≥ TRAIN_END are exactly `endpoint_ts_ns` (31,652) and `censor_ts_ns`
(31,652) stamped at TRAIN_END (2023-11-22T00:00) — right-censoring, `after_train_end: 0`,
`holdout: 0`. No signal field (sweep/first/return/confirmation) reaches TRAIN_END.

**Q30. Confirmation never fires without a recorded return.**
ANSWERED — PASS. `n_confirm_without_return: 0` (264 cells).

**Q31. Unknown raid/level statuses empty.**
ANSWERED — PASS. `unknown_raid_status: []`, `unknown_level_status: []`.

**Q32. Catalogue identity: 11 configs × 3 assets × declared TF/confirm grid; no Bybit cells.**
ANSWERED — PASS. Symbols `{EURUSD, USTEC, XAUUSD}` only (cTrader); 11 configs; grid exact.
No Bybit/perp cells.

## 3. Evidence FOR the hypothesis

1. **Integrity gate clean end-to-end.** Family `blocking_pass: true`; 264/264 per-cell gates
   `blocking_pass: true`; manifest and zero-cost and fence all clean (§1). No blocking
   finding exists.
2. **State identity preserved.** `raid_dup: 0`, `level_dup: 0`, `missing/extra_profiles: 0`,
   `unknown_*_status: []` across all 264 cells — every object is unique, every raid owns
   exactly one TPO profile, no orphan profile.
3. **Chronology correct.** `chrono_fail: 0`, `grid_fail: 0` (excursion ≤ return, confirm >
   sweep, endpoint ≥ confirm, minute-grid timestamps).
4. **Future-destroy tripwire collapses, non-vacuously.** 264/264 cells `CHANGED`,
   `fixed_points: 0`, mean|Δswing_atr| ≥ 2.8×SE. The later-swing fields genuinely depend on
   the aligned future path — causal-by-construction, no fixed-point leak.
5. **AMENDMENT-13 verified two ways.** (a) Golden replay: same-bar pierce+return leaves the
   raid live (`live_after_same_bar_pierce_return: true`), `return_equals_sweep: true`,
   `not_ambiguous: true`. (b) Emission: 7,669,654 same-bar returns recorded, 0 ambiguous.
6. **AMENDMENT-8 verified.** 1m wick that does not survive the observation OHLC adds no raid
   (`t1_wick_did_not_add_raid: true`).
7. **AMENDMENT-6 verified.** T2 raid `COMPLETED` + primary; earlier eligible returned T1 raid
   `CONFIRMED_NON_PRIMARY`; opposing T1 raid `FAILED_BREAKOUT`.
8. **Independent recomputation matches.** 3 completed raids recomputed from raw `bar_marks`
   reproduce emitted `max_excursion` exactly; first-beyond, same-bar-return, and later-return
   paths all identified correctly.
9. **Grid and config coverage complete.** 264 cells exactly as designed (15m 66, 30m 66, 60m
   132); confirm refs correct; 11 level configs; rolling 7/14/22/252. No zero-level, no
   zero-raid, no zero-1D/1W cell; every cell ≥ 2 confirmed raids.
10. **AMENDMENT-10 trading clock correct.** 1D anchors 640–644, 1W = 129 (stable); zero
    weekend-dated anchor keys; zero zero-level cells.
11. **AMENDMENT-12 tight/gap rule exact.** `tight_rule_mismatch: 0`, `va_mass_short: 0`,
    `tpo_tight_ratio: 0.5`, `tpo_gap_mass: 0.3` uniform.
12. **TRAIN boundary respected.** Signal fields never reach TRAIN_END; only right-censor
    stamps sit at TRAIN_END; nothing touches holdout.

## 4. Evidence AGAINST the hypothesis

1. **Golden-trace probe aggregate booleans partially false/null.** `t1_one_completed_or_settled:
   false`, `t2_exists: false`, `t1_non_primary_if_both_confirmed: null`. Cause: the synthetic
   feed re-pierced levels after settlement, minting extra right-censored raids, and the check
   indexed the first raid per level rather than the settled one. The raw raid summaries show
   correct AMENDMENT-6/13 behaviour, but the *automated* golden check is not fully green —
   the T2/T1-non-primary demonstration rests on raw-summary reading, not a boolean pass.
2. **No per-raid 1-minute path stored from raid → confirm (or confirm → swing end).** The
   "did price retrace into the value-gap box?" question is unanswerable from this emission —
   a new column or a later 1m catalog pass would be required (handoff, binding).
3. **No fill/trade ledger exists** (`n_fills: 0`, `orders_submitted: false`). The apparatus is
   measurement-only; there is no economic/P&L object, so no PSR/mean-trade-bps read is
   possible (and none is claimed).
4. **~78% of raids return on the same observation bar.** This is the dominant event shape
   (median fraction 0.780, tight range 0.752–0.799). Under AMENDMENT-13 these stay live, so
   this is a coverage characteristic, not a defect — but it means "return then confirm on a
   later bar" is the rarer path.
5. **46,410 undefined TPO profiles (0.47%)** — not yet summarized by reason. Minor; the
   design permits UNDEFINED where TPO data is insufficient, but the reason distribution was
   not interrogated here.
6. **Right-censoring tail.** 30,520 excursions, 626 confirmations, 506 endpoints censor at
   TRAIN_END. As designed; the censored object carries no post-TRAIN information (stamps sit
   exactly at TRAIN_END).

## 5. What would make the headline numbers wrong (N7)

- **Coverage counts** could be inflated by duplicate object ids or orphan profiles → ruled out
  (`raid_dup/level_dup/missing/extra_profiles = 0`), and 3 raids independently recomputed from
  `bar_marks` match emitted values exactly.
- **Method overlap** could silently pool two different tests → ruled out by head-to-head
  comparison (132/132 id+status equal), and disclosed as total overlap.
- **Golden trace** could pass on a hand-written fixture instead of the real processor → the
  golden feed runs through the shared `xen.exp100.processor`, not a fixture.
- **TRAIN/holdout** could leak via endpoint/censor stamps → probed field-by-field: only
  endpoint/censor reach TRAIN_END (exact), nothing exceeds it, nothing reaches holdout.
- **Future-destroy** could be vacuous (derangement changes nothing) → ruled out:
  `fixed_points: 0`, 264/264 `CHANGED`, mean|Δ| ≥ 2.8×SE.

## 6. Anomalies & open questions

- **Golden-trace probe indexing.** The `t1_one_completed_or_settled` / `t2_exists` booleans
  are false due to probe strictness, while the terminal summaries show correct behaviour.
  Recommendation: if the operator wants a fully-green automated golden check, re-run the
  probe with per-raid (not per-level-first) assertions — analysis-only, no re-emission.
- **Undefined-TPO reason distribution** not summarized (0.47% of profiles). Could be probed
  from `profile_undefined_reason`.
- **Regime stability across the TRAIN calendar** (Q6) not formally read — would need a
  predeclared stratum split if pursued.
- **1m retrace-into-gap path** not stored (binding handoff constraint) — a proposal for a
  later 1m catalog pass, not part of this experiment.

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

**Recommendation:** the hypothesis is upheld by the evidence — the streaming state machine
preserves identity and chronology of levels, excursions, raids, confirmation, breakout, and
later-swing states on the AMENDMENT-13 object, and the 264-cell TRAIN emission is
measurement-valid and coverage-complete. No integrity failure was found, and no evidence
against the hypothesis survives scrutiny (the two "against" items that touch the mechanism —
golden-probe booleans — are probe-indexing artifacts, not state-machine defects).

Evidence most driving this: (1) the clean family+per-cell estimand gate with zero integrity
fail sums across 264 cells; (2) the future-destroy tripwire collapsing non-vacuously with
zero fixed points in all 264 cells; (3) the AMENDMENT-13/8/6 golden replay + independent
raw-bar recomputation matching emitted values exactly.

What could change it: a probe demonstrating a real chronology/identity violation on a
specific cell (none found), or a failure of the golden trace under per-raid assertions (the
raw summaries already show correct behaviour, so low risk).

Explicit hand-off: **final verdict is the operator's.** This is a measurement-validity read,
not a value read — no tradability, no edge, no family action. Suggested follow-up probes if
the operator wants to push: (a) per-raid golden assertions to turn the boolean caveat green;
(b) undefined-TPO reason distribution; (c) a predeclared TRAIN-regime stratum split. EXP-101–104
remain design-only and are not opened by this analysis.
