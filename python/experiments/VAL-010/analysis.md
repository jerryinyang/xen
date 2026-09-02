# Data Analysis: VAL-010

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Observations are
**observed** (`anatomy_summary.json` from TRAIN completed primaries) or **inference**.
§7 applies only to VAL-010’s anatomy question. No TEST, holdout, costs, P&L, or family action.

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

**Grid rule.** Physical grid collapses only BB/LC. Contrast `n_strata=264` is
**132 physical settings × 2 sides**, not 264 independent source cells.

**Channel rule.** A pattern in `strong_move` / `swing_atr` is not confirmed by duration
unless duration moves with the same sign and coverage.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation | **PASS** | VAL-009 copy of EXP-100 gate, `blocking_pass=true` |
| Zero-cost | **PASS** | inherited gate |
| Population | **PASS** | COMPLETED ∧ primary ∧ primary_completed ∧ not ATR_UNDEFINED ∧ finite ATR |
| TRAIN fence | **PASS** | `sweep_ts_ns` in `OUTCOME_COLUMNS`; `<= TRAIN_END_NS` |
| Holdout | **PASS** | EXP-100 full only |
| Local accounting | **PASS** | analyst script only |

## 2. Question list

1. Integrity? **ANSWERED** §1.
2. P&L / PSR? **UNANSWERED — N/A**.
3. Where does the strong-move inequality sit (excursion vs later swing vs surplus vs path)? **ANSWERED** §3–4.
4. Do repeat bands 1 and 2+ differ from band 0 on all three outcome channels? **ANSWERED** §3–4.
5. Does duration agree with ATR / strong-move? **ANSWERED** §4.
6. Is BB/LC treated as replication? **ANSWERED** (no; physical unique on `physical_cell, raid_id`).
7. Falsification probes? **ANSWERED** §5.

## 3. Evidence FOR a descriptive anatomy (not a mechanism)

Physical completed primaries, n=394,607 (raw parity n=789,214 = 2×):

| Channel | Pooled physical |
|---|---|
| mean max excursion | 1.603 ATR |
| mean later swing | 3.685 ATR |
| mean surplus (`swing − excursion`) | 2.082 ATR |
| strong-move rate | 0.831 |
| median duration | 5.0 h |
| retrace | DEFINED 364,176; AMBIGUOUS_SAME_BAR 26,744; NO_POST_CONFIRMATION_MFE 3,687 |

Physical-stratum contrasts (132 settings × 2 sides = 264 strata):

| Contrast | Channel | mean Δ | strata − / 0 / + |
|---|---|---|---|
| 1 vs 0 | strong_move_rate | −0.240 | 255 / 3 / 6 |
| 1 vs 0 | swing_atr | −1.111 | 237 / 0 / 27 |
| 1 vs 0 | duration_hours | +0.463 | 130 / 0 / 134 |
| 2+ vs 0 | strong_move_rate | −0.117 | 242 / 0 / 22 |
| 2+ vs 0 | swing_atr | −1.460 | 250 / 0 / 14 |
| 2+ vs 0 | duration_hours | +0.721 | 117 / 0 / 147 |

By configuration, band **0** has small excursion and large surplus; band **1** often has
excursion ≥ swing (negative surplus on PREVIOUS_1D/1W/AMERICA/ASIA/EUROPE and ROLLING_14/22).
**Inference:** the lower strong-move rate on later raids sits in a **larger initial excursion
and a smaller (sometimes negative) surplus**, not in a shorter swing.

## 4. Evidence AGAINST treating this as confirmation of EXP-102/104 “support”

- **Duration does not agree.** 1 vs 0 duration is 130 negative / 134 positive; median Δ is
  +0.027 h. A 5 h median is essentially unchanged across bands. Duration cannot carry the
  strong-move story.
- Pooled strong-move 0.831 hides the band-1 drop (config examples: PREVIOUS_1D 0.835 → 0.608;
  ROLLING_7 0.968 → 0.745).
- Band 2+ is **not** a monotone continuation of band 1: strong-move partially recovers while
  swing_atr stays lower than band 0.
- `pre_mfe_retrace` is **outcome anatomy**. It is not an entry filter. DEFINED is common
  (92.3%); that does not validate a path-based rule.
- No cost, fill, or tradability object exists.

## 5. What would make the headline numbers wrong (N7)

| Headline | Probe | Result |
|---|---|---|
| Surplus = swing − excursion | unit inequality on a 2-row frame | test `mean_surplus_atr == 0.5` |
| Repeat bands 0/1/2+ | omit a band | test keeps all three |
| Duration vs strong-move | one-channel “support” label | contrast helper emits three channels; duration split |
| 264 strata = 264 source cells | count keys | keys are `physical_cell, side, config`; physical_cell already collapsed BB/LC |

## 6. Anomalies & open questions

- Why band 1 surplus goes negative on session/clock configs more than on short rolling windows.
- Whether excursion inflation on repeat 1 is the same physical level being re-raided (VAL-009
  exact count) or a different level population. This file cannot separate those.

## 7. Recommended verdict (characterisation only — NOT final, NOT family)

- Recommendation: the anatomy question is **answered as a description**. Repeat-band
  differences in `strong_move` line up with excursion/surplus, **not** with duration.
  EXP-102/104 language that said “supported” on strong-move/ATR should not treat duration
  (or frequency, VAL-011) as a second confirming channel.
- Driven by: 255/264 strata with lower strong-move on band 1; duration sign split 130/134.
- Would change if: duration contrasts concentrated on the same side as strong-move.
- Hand-off: operator decides how to annotate EXP-102/104. No family action.
