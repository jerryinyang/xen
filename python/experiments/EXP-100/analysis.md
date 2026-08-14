# Data Analysis: EXP-100

## 0. Boundary statement (N1 — binding)

This record issues NO final verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled observed (read directly from an emitted artifact) or inference (a mechanism
reading of observed numbers that is not itself measured). The recommendation in §7 is
non-final and applies only to EXP-100/HYP-000; the operator decides.

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

**N2–N11 reporting discipline.** N2: the measured object is emitted level/raid/TPO state,
not a trade, leg, or P&L episode. N3 and N10: all available counts and their context are
reported; no row is suppressed for sample size. Compact marginals retain every value of every
declared grid layer; a low-information 264-cell listing is not requested. N4: BREAKOUT_BAR is compared directly with
its declared same-stratum LEVEL_CLOSE counterpart. N5: pooled totals are disclosures, not
substitutes for strata. N6/N6b: the only thresholded inferential statement is the
future-destroy *integrity* tripwire (`2.8 × bootstrap_SE`); it is not a value, power, or MDE
gate. N7: falsification probes are explicit in §5. N8: TEST/global holdout observations are
not interpreted. N9: all quantities are gross and zero-cost as disclosed above. N11: no
machine row labels such as `WASH`, `UNPOWERED`, `SUPPORTED`, or `REFUTED` are assigned.
There are no mean-leg/mean-trade returns, P&L, Sharpe, or PSR claims in this record.

## 1. Integrity gate (blocking)

Only integrity findings in this section have blocking authority. Research observations in
§§3–7 do not.

| Integrity check | Observed result | Artifact evidence |
|---|---|---|
| Family and cell estimand gates | **PASS** | `results/estimand_validation.json`: `blocking_pass: true`, `n_cells: 264`; 264/264 cell `blocking_pass: true` |
| Schema / catalogue / expected family | **PASS** | 264/264 schema, catalogue, and cell manifests `ok`; family expected EURUSD/XAUUSD/USTEC, emitted all three, `missing: []` |
| Fence | **PASS** | 264/264 `fence.ok: true`, `status: PINNED`, `within_fence: true`, `analysis_end_utc: 2024-12-13T00:00:00Z`; expected and actual manifest hash both `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| TRAIN / global holdout tripwire | **PASS** | `probe_integrity.json.past_train`: 63,304 exact-TRAIN-end stamps, all split equally between `censor_ts_ns` and `endpoint_ts_ns`; `after_train_end: 0`, `holdout: 0`. `scan_summary.json`: `raid_ts_holdout`, `mark_holdout`, and `mark_past_train_cells` all 0 |
| Zero-cost integrity | **PASS** | 264/264 `no_cost_charged.ok: true`; `NO_COST_CHARGED`, no non-zero columns or rows, `cost_bps: 0.0`, directive `null` |
| State reconciliation | **PASS for the emitted object** | 264/264 `reconciliation.ok: true`, note `no leg ledger`; this attests the non-trading state object and does not attest P&L |
| Identity, joins, chronology, statuses | **PASS** | `scan_summary.json.integrity_fail_sums`: duplicate raid/level IDs, missing/extra profiles, chronology/grid failures, active residuals, retired statuses, invalid AMENDMENT-14 fields, fills, and ambiguous retired closures are all 0 |
| Future-destroy integrity control | **PASS for its declared finite-primary population** | `amendment_summary.json.control`: 264/264 cell summaries pass. Each cell uses 462–6,580 aligned finite primary raid pairs (115–5,269 level clusters). Alignment-collapse fractions are 0.02695–0.32993; destroyed-alignment survival fractions are 0.67007–0.97305; 0 block-fragile cells. Definitions are in §2.2. |
| Golden lifecycle fixture | **PASS after fixture correction** | `probe_integrity.json.golden.checks` and `.same_bar_return_golden.checks`: all lifecycle/cardinality/attribution booleans are true. The old fixture allowed valid re-piercing, then incorrectly required one terminal row per level. |
| ATR-undefined initial maximum excursion | **FAIL (scoped implementation defect)** | `atr_undefined_prevalence.json`: 868 ATR-undefined raids took the no-profile path; 780 (89.862%) emit a smaller max than the side-aware high/low of their completed initial observation. `probe_integrity.json` supplies the targeted trace. |
| Price-primary / no trading path | **Artifact-consistent** | `scan_summary.json`: Nautilus version `1.230.0`, `n_fills: 0`; no P&L or fill estimand is analysed. The supplied artifacts do not independently attest every implementation provenance line |

**Blocking conclusion (observed):** the supplied family gate still reports `blocking_pass: true`,
but the independent golden follow-up found a scoped state-measurement defect. Interpretation stops
for `max_price`, `max_excursion`, and derived excursion fields on the 868 ATR-undefined raids; 780
are numerically understated and 88 have zero observed initial-bar impact. Count, identity,
chronology, status, finite-primary control, and grid-marginal reads below do not use the defective
value path. This is not evidence of economic value.

## 2. Question list and answers

The list below was frozen before the post-gate interrogation. Answers use only the supplied
artifacts.

1. **Gate completeness?** ANSWERED — 264/264 cells pass schema, fence, catalogue, manifest,
   reconciliation, and zero-cost checks (§1).
2. **Object identity?** ANSWERED — this is a level/raid/TPO state object. The gate explicitly
   says `no leg ledger`, and `scan_summary.json` reports `n_fills: 0`; therefore trade P&L is
   outside the object.
3. **Non-trading metrics?** ANSWERED — per-leg returns, PSR, P&L episode anatomy, trading
   occupancy/exposure, return, Sharpe, drawdown, and fill quality are **not applicable**, not
   zero. State occupancy is described only through level/raid/profile counts.
4. **Declared family?** ANSWERED — EURUSD, XAUUSD, USTEC; 15m/30m/60m; BREAKOUT_BAR and
   LEVEL_CLOSE; 1H for 15m/30m and 1H+4H for 60m; eleven declared configs; 264 cells. Cell
   counts are 66/66/132 by timeframe, with no 1D confirmation cells.
5. **All rows and per-stratum counts?** ANSWERED with informative marginals — all 264 cells
   are retained and none has zero raids, levels, 1D anchors, or 1W anchors. `coverage_marginals.json`
   retains every venue, instrument, timeframe, confirmation method, confirmation reference, and
   level-configuration value with cells, levels, raids, lifecycle, and pre-MFE counts (§2.1).
   Pooled totals are 9,840,478 raids, 6,329,824 levels, 789,832 primary confirmations, and
   789,326 completed primary raids. No 264-row listing is needed to disclose layer concentration.
6. **Identity/profile/status integrity?** ANSWERED — duplicate raid/level IDs, missing/extra
   profiles, active residuals, and retired status hits are all 0. Defined TPO profiles total
   9,794,210; undefined profiles total 46,268: 45,400 `GAP_UNDEFINED` and 868
   `ATR_UNDEFINED`.
7. **Causal timestamps and fences?** ANSWERED — chronology and minute-grid failure sums are 0;
   only 31,652 censor and 31,652 endpoint stamps equal TRAIN end; none is later or in holdout.
8. **Independent and golden reproduction?** ANSWERED with a scoped failure — three sampled
   finite-ATR EURUSD-15m raids reproduce emitted max excursion exactly from observation marks.
   Corrected lifecycle fixtures are uniformly green and show CONFIRMED_NON_PRIMARY and primary
   COMPLETED paths. The targeted ATR-undefined trace fails maximum-excursion identity: 0.8 emitted
   versus the completed observation's 1.2. Family-wide reconstruction finds 780/868 exposed rows
   with the same direction of mismatch (§6.1).
9. **AMENDMENT-3 grain?** ANSWERED — 14,583,052 source minutes are not themselves completed
   observations, consistent with real 1m input feeding coarser observations; invalid
   observation-source count is 0. The artifact does not expose a standalone synthetic-bar
   count, so absence of synthetic closure bars is supported indirectly, not independently.
10. **AMENDMENT-4 ATR fields?** ANSWERED with scope — reported identity failures are 0 on
    their finite-ATR populations. The ATR-undefined probe does not fabricate a normalized value,
    but does under-record the raw initial-observation maximum excursion (§1); that path is stopped.
11. **AMENDMENT-6 attribution?** ANSWERED — maximum primary per confirmation/side is 1;
    invalid primary status, completed non-primary, and unlinked non-primary failures are 0.
    Corrected golden settlement examples have T2 primary COMPLETED and earlier T1
    CONFIRMED_NON_PRIMARY; the old cross-raid harness caveat is resolved.
12. **AMENDMENT-7 universe?** ANSWERED — only the three declared cTrader symbols appear; no
    Bybit instrument is present.
13. **AMENDMENT-8 observation-bar starts?** ANSWERED — invalid observation-source count is 0;
    golden `t1_wick_did_not_add_raid: true` shows a non-surviving 1m wick did not start a raid.
14. **AMENDMENT-9 grid?** ANSWERED — exact 66/66/132 grid described in answer 4.
15. **AMENDMENT-10 clock?** ANSWERED — across the 48 daily/weekly cells, 1D anchors span
    640–644 and 1W anchors equal 129; weekend-dated Saturday/Sunday anchors and zero-level
    cells are 0. The 6,000 Sunday creation rows in each daily/weekly summary are compatible
    with NY-session creation and are not weekend anchor keys.
16. **AMENDMENT-11 windows?** ANSWERED — only rolling 7/14/22/252 appear alongside the seven
    declared previous-period/session configurations; observed and expected lists match.
17. **AMENDMENT-12 TPO rules?** ANSWERED — conservation, VA-mass-short, and tight-rule failure
    counts are 0. Defined profiles are 9,794,210; tight profiles 1,439,234 (14.695%, per-cell
    9.186%–18.137%). VA mass has p1 0.70 and median 0.7273; selected-bin range is 1–1,927.
    Gap span/VA is below 0.5 for 14.695% and at least 1 for 53.515%.
18. **AMENDMENT-13 same-bar return?** ANSWERED — 7,669,654 of 9,809,958 returned raids return
    on the same observation bar; per-cell fraction 75.182%–79.916% (median 78.031%). Retired
    ambiguous closure and same-bar-closed-ambiguous counts are 0. Golden confirms the raid is
    live immediately after same-bar pierce/return and later reaches COMPLETED.
19. **AMENDMENT-14 retrace?** ANSWERED — 728,936 DEFINED, 53,496 AMBIGUOUS_SAME_BAR, and 7,400
    NO_POST_CONFIRMATION_MFE. Invalid status/price, missing primary, unexpected non-primary,
    side-bound, and no-MFE-price failure counts are all 0. Ambiguity is explicitly represented,
    not silently folded into a numeric retrace.
20. **Duration definitions?** ANSWERED — excursion-duration, swing-duration, unconfirmed
    non-null swing-duration, and frozen duration-alias failure counts are all 0.
21. **Future-destroy validity?** ANSWERED — all 264 cells changed and pass the integrity bite;
    no fixed points/count/ID/status mismatches are reported. The control changes aligned future
    fields while preserving IDs/statuses and outcome marginals.
22. **Collapse fractions?** ANSWERED — across 264 cell-level summaries, alignment-collapse
    fraction `(raw alignment fraction − destroyed alignment fraction) / raw alignment fraction`
    ranges 0.02695–0.32993 (median 0.19697). Destroyed-alignment survival fraction
    `destroyed alignment fraction / raw alignment fraction` ranges 0.67007–0.97305. Each raw
    or destroyed alignment fraction uses the cell's 462–6,580 aligned finite primary raid pairs
    as denominator (789,646 pooled pairs); the numerator is pairs where emitted `strong_move`
    agrees with the corresponding raw or destroyed swing/max-excursion comparison. CI-low is
    0.01845–0.27397; seed-band global bounds are 0.01768–0.27669; 0 cells are block-fragile.
    All ATR-undefined rows are excluded because `max_excursion_atr` is null; the excluded primary
    subset is 112 rows, 84 materially affected (§6.1). These are integrity-control statistics only.
23. **Direct method comparison?** ANSWERED — 132/132 same-stratum pairs have equal IDs and
    statuses and 0 count differences. This total overlap is evidence of equivalence for the
    emitted state object, not a ranking or economic comparison.
24. **Calendar concentration?** ANSWERED descriptively — raids/primary/completed are
    2,197,572/171,060/171,060 in 2021; 4,025,596/327,522/327,522 in 2022; and
    3,617,310/291,250/290,744 in 2023. State production is present in every year but is not
    uniform; 2022 has the largest mass. The artifacts provide no exposure-normalized yearly
    rate, so stability per unit time is UNANSWERED.
25. **Headline falsification?** ANSWERED in §5; all declared probes ran, with limitations
    stated rather than converted to passes.
26. **Physical meaning of no orders/fills?** ANSWERED — EXP-100 characterizes a state machine
    that creates many overlapping levels and raids and settles them causally. It does not show
    that any state can be entered, filled, monetized, or survive costs.

### 2.1 Declared-grid count marginals

The compact source artifact is `results/analysis/coverage_marginals.json`. `Primary confirmed`
counts non-null `confirmation_ts_ns`; in this emission it equals `primary_attributed`. Pre-MFE
`D / A / N` means `DEFINED / AMBIGUOUS_SAME_BAR / NO_POST_CONFIRMATION_MFE`. The artifact also
retains returned, failed, confirmed-non-primary, and all three right-censor counts.

**Venue**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| ctrader | 264 | 6,329,824 | 9,840,478 | 789,832 / 789,832 | 789,326 | 728,936 / 53,496 / 7,400 |

**Instrument**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 88 | 2,114,528 | 3,315,732 | 260,738 / 260,738 | 260,428 | 242,296 / 15,758 / 2,684 |
| USTEC | 88 | 2,133,056 | 3,250,370 | 274,206 / 274,206 | 274,114 | 250,778 / 20,228 / 3,200 |
| XAUUSD | 88 | 2,082,240 | 3,274,376 | 254,888 / 254,888 | 254,784 | 235,862 / 17,510 / 1,516 |

**Timeframe**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 66 | 2,994,184 | 4,631,206 | 252,434 / 252,434 | 252,306 | 231,864 / 18,022 / 2,548 |
| 30m | 66 | 1,579,144 | 2,333,912 | 242,758 / 242,758 | 242,632 | 222,948 / 17,362 / 2,448 |
| 60m | 132 | 1,756,496 | 2,875,360 | 294,640 / 294,640 | 294,388 | 274,124 / 18,112 / 2,404 |

**Confirmation method**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| breakout_bar | 132 | 3,164,912 | 4,920,239 | 394,916 / 394,916 | 394,663 | 364,468 / 26,748 / 3,700 |
| level_close | 132 | 3,164,912 | 4,920,239 | 394,916 / 394,916 | 394,663 | 364,468 / 26,748 / 3,700 |

**Confirmation reference**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 198 | 5,451,576 | 8,164,150 | 714,312 / 714,312 | 713,934 | 656,020 / 51,100 / 7,192 |
| 4h | 66 | 878,248 | 1,676,328 | 75,520 / 75,520 | 75,392 | 72,916 / 2,396 / 208 |

**Level configuration**

| Value | Cells | Levels | Raids | Primary confirmed / attributed | Completed | Pre-MFE D / A / N |
|---|---:|---:|---:|---:|---:|---:|
| PREVIOUS_1D | 24 | 30,784 | 248,292 | 49,558 / 49,558 | 49,520 | 45,964 / 3,178 / 416 |
| PREVIOUS_1H | 24 | 650,496 | 1,935,994 | 113,546 / 113,546 | 113,486 | 104,718 / 7,734 / 1,094 |
| PREVIOUS_1W | 24 | 6,192 | 90,616 | 21,100 / 21,100 | 21,082 | 19,430 / 1,412 / 258 |
| PREVIOUS_4H | 24 | 145,152 | 723,758 | 90,312 / 90,312 | 90,264 | 83,338 / 6,184 / 790 |
| PREVIOUS_AMERICA | 24 | 30,800 | 289,434 | 55,000 / 55,000 | 54,962 | 51,038 / 3,448 / 514 |
| PREVIOUS_ASIA | 24 | 30,784 | 328,066 | 58,004 / 58,004 | 57,986 | 53,588 / 3,934 / 482 |
| PREVIOUS_EUROPE | 24 | 30,768 | 303,722 | 57,352 / 57,352 | 57,330 | 53,032 / 3,832 / 488 |
| ROLLING_14 | 24 | 1,354,080 | 1,740,190 | 104,420 / 104,420 | 104,352 | 96,262 / 7,150 / 1,008 |
| ROLLING_22 | 24 | 1,353,696 | 1,372,976 | 93,612 / 93,612 | 93,544 | 86,248 / 6,462 / 902 |
| ROLLING_252 | 24 | 1,342,656 | 373,824 | 32,678 / 32,678 | 32,618 | 29,998 / 2,338 / 342 |
| ROLLING_7 | 24 | 1,354,416 | 2,433,606 | 114,250 / 114,250 | 114,182 | 105,320 / 7,824 / 1,106 |

### 2.2 Future-destroy populations and fractions

The 264-cell artifact is a summary population: one row per declared cell. Within each row, the
analysis population is `aligned_finite_primary_raid_pairs`: raw/destroyed rows joined by `raid_id`,
with non-null primary confirmation and finite raw/destroyed swing plus finite max excursion.
There are 462–6,580 such pairs and 115–5,269 level clusters per cell. The six detailed probe cells
are examples, not a second denominator: they contain 4,931–9,988 total emitted raid rows, of which
495–1,074 are primary-confirmed and all 495–1,074 are aligned finite primary pairs.

For each cell, `raw_alignment_fraction = raw_alignment_numerator_n / aligned_pair_denominator_n`
and the destroyed equivalent uses the same denominator. Collapse and survival are defined in Q22.

## 3. Evidence FOR the hypothesis

1. **The unaffected integrity checks are clean across the declared grid (observed).** Family and
   264/264 published gates pass for manifest, catalogue, fence, zero-cost, identity, chronology,
   holdout, and reconciliation. The scoped ATR-undefined defect in §1 prevents extending this
   evidence to every emitted value field.
2. **The intended state object is populated broadly (observed).** All 264 cells contain raids,
   levels, daily anchors, and weekly anchors. The family emits 9,840,478 raids and 6,329,824
   levels across three instruments, three timeframes, two methods, valid confirmation grids,
   and all eleven configurations; calendar-year production is non-zero in 2021–2023.
3. **Identity and lifecycle rules reconcile (observed).** There are no duplicate IDs, orphan
   profiles, active end-state objects, unknown/retired states, chronology failures, or
   confirmation-without-return events. Status totals reconcile to raid total: 4,702,900
   FAILED_BREAKOUT, 4,316,600 CONFIRMED_NON_PRIMARY, 789,326 COMPLETED, plus 30,520/626/506
   excursion/confirmation/endpoint right-censors.
4. **Most amendment mechanics agree across aggregate and trace evidence (observed).** The audits
   report zero failures for finite-ATR identities, primary attribution, TPO conservation/tightness,
   retrace bounds/statuses, and duration aliases. Corrected golden rows exhibit non-primary,
   primary-completed, and same-bar-live paths; three sampled finite-ATR raw-mark reconstructions
   match. This evidence explicitly excludes the ATR-undefined maximum-excursion defect (§1).
5. **The leak control is non-vacuous and clears its predeclared integrity bite (observed).** All
   264 cells change future fields and pass; collapse fractions are 0.02695–0.32993 with positive
   CI-low bounds and no block-fragile cells. This supports aligned future-path provenance; it
   does not measure market edge.
6. **Method comparison is exact rather than selectively favorable (observed).** All 132 direct
   BREAKOUT_BAR/LEVEL_CLOSE counterparts have identical IDs/statuses/counts. This supports
   stable measurement under the two declared method labels, while also showing they provide no
   differentiating evidence here.

## 4. Evidence AGAINST the hypothesis

1. **ATR-undefined maximum excursion is under-recorded (observed).** With no profile generation,
   the processor retains the first beyond-minute extreme and does not advance to a later extreme
   inside the same completed observation. Exact emission-only reconstruction identifies 868
   exposed raids and 780 materially changed values (89.862%); 88 have zero observed impact.
   Affected maximum-excursion fields are not interpreted (§6.1).
2. **The old aggregate golden cardinality failures were fixture defects (observed).** A same-bar
   return legitimately resets the level for a later re-pierce; subsequent synthetic observations
   then created additional T1/T2 rows, while the harness incorrectly required one row per level.
   Isolated lifecycle traces now make every cardinality/attribution boolean true without changing
   strategy code.
3. **Marginals show concentration without dropping grid values (observed).** Raid mass ranges from
   90,616 for PREVIOUS_1W to 2,433,606 for ROLLING_7 and from 2,333,912 at 30m to 4,631,206 at 15m.
   These are descriptive counts, not exposure-normalized rates.
4. **Same-bar returns dominate (observed).** 7,669,654 returns occur on the sweep bar, with a
   narrow 75.182%–79.916% cell range. This is explicitly valid under AMENDMENT-13, yet it means
   evidence about longer-lived return paths is a minority of return events.
5. **Not every profile/retrace is numeric (observed).** There are 46,268 undefined TPO profiles;
   53,496 retraces are AMBIGUOUS_SAME_BAR and 7,400 have no post-confirmation MFE. These are
   explicit states rather than integrity failures, but downstream hypotheses must not silently
   treat them as measured numeric values.
6. **Calendar mass is uneven (observed).** 2022 contributes 4.03M raids versus 2.20M in 2021
   and 3.62M in 2023. Without an exposure-normalized denominator, the artifacts cannot establish
   rate stability across years.
7. **There is no economic observation (observed).** No orders, fills, leg ledger, costs, returns,
   P&L, or PSR exist. Thus the evidence cannot support profitability, tradability, or deployment,
   even if the state-object hypothesis is accepted.

## 5. What would make the headline numbers wrong (N7)

- **Stale/wrong family root:** compare manifest identity, emitted instruments, pinned fence, and
  hash → executed; expected/emitted family matches, and expected/actual hash is identical.
- **Incomplete grid:** enumerate symbols, timeframes, methods, refs, and configs and check zero
  cells → executed; 264 cells and 66/66/132 timeframe grid match, with no zero raid/level cells.
- **Pooled masking:** inspect every value of every declared grid layer → executed through
  `coverage_marginals.json`; no value is dropped, and count concentration is visible without a
  264-row cell dump.
- **Duplicate/orphan inflation:** check raid/level duplicates and missing/extra profiles → executed;
  all failure sums are 0.
- **Wrong clock or holdout leak:** check weekend anchor keys and every boundary class → executed;
  no weekend-dated anchors, post-TRAIN stamps, or holdout timestamps; exact TRAIN-end stamps are
  only endpoint/censor pairs.
- **Invalid TPO reconstruction:** test conservation, minimum VA mass, selection/tight rule, and
  profile joins → executed; all failure sums are 0, with undefined profiles disclosed.
- **Vacuous future-destroy control:** require changed future fields, zero fixed points, preserved
  IDs/status/counts, positive collapse, and block robustness → executed; all 264 pass. The
  `2.8 × bootstrap_SE` bite remains integrity-only (N6b), never a value/MDE claim.
- **Malformed AMENDMENT-14 bounds:** check eligible status, finite price, primary-only assignment,
  side-aware bounds, and no-MFE handling → executed; all failure sums are 0 and ambiguous/no-MFE
  counts are disclosed separately.
- **Trace false positive:** isolate raid identity from valid re-piercing and separately vary the
  first/later source extremes → executed. Lifecycle booleans turn uniformly true after the fixture
  correction, while the ATR-undefined maximum-excursion mismatch remains reproducible.

## 6. Anomalies & open questions

1. The fixture/cardinality question is resolved: valid re-piercing caused the old false/null
   aggregate checks. The corrected lifecycle checks are all true.
2. The layer-count question is resolved by `coverage_marginals.json`, which retains all declared
   values and relevant count/status fields.
3. The control denominator question is resolved in §2.2 and in renamed artifact fields. The
   ATR-undefined maximum-excursion defect is quantified in §6.1; only still-later post-observation
   maxima are not identifiable from the frozen emissions.
4. The 46,268 undefined TPO profiles split into 45,400 `GAP_UNDEFINED` and 868
   `ATR_UNDEFINED`; only the latter can take the defective no-generation path.
5. Year totals are not normalized by eligible bars/anchors, so state-frequency stationarity is
   not established.
6. The 53,496 AMBIGUOUS_SAME_BAR retraces are correctly separated, but the artifacts do not show
   how their fraction varies by stratum.
7. No strategy, emission, or verdict change is proposed here. Any economic, fill, cost, P&L,
   or PSR question requires a different trading experiment and cannot be answered from EXP-100.

### 6.1 ATR-undefined defect prevalence and decision impact

Source: `analysis_code/atr_undefined_prevalence.py` →
`results/analysis/atr_undefined_prevalence.json`. No rerun, catalogue read, strategy import, or
strategy change was used.

**Identification.** Exposure is the exact intersection of raid
`profile_undefined_reason=ATR_UNDEFINED` and matching TPO `UNDEFINED/ATR_UNDEFINED`. Joining
`sweep_ts_ns` to the emitted completed observation mark reconstructs the side-aware initial
maximum from `RealHigh/RealLow`. Because `first_excursion_ts_ns` is the first source minute
beyond the level, a larger completed-observation extreme proves a later source minute exceeded
it. The full source-minute path, exact minute attaining that maximum, and any maximum after the
initial observation were not emitted and are not reconstructible.

| Population | Explicit denominator | ATR-undefined exposure | Materially changed |
|---|---:|---:|---:|
| All raids | 9,840,478 | 868 (0.008821%) | 780 (0.007926%) |
| All profile-undefined raids | 46,268 | 868 (1.8760%) | 780 (1.6858%) |
| ATR-undefined raids | 868 | 868 (100%) | 780 (89.8618%) |
| Primary-attributed raids | 789,832 | 112 (0.014180%) | 84 (0.010635%) |
| Completed raids | 789,326 | 112 (0.014189%) | 84 (0.010642%) |
| Future-destroy aligned finite-primary pairs | 789,646 | 0 (0%) | 0 (0%) |

The remaining 88/868 exposed rows (10.1382%) have zero initial-observation understatement.
Both confirmation methods duplicate the same state objects exactly: 434 exposed / 390 changed
after method deduplication, versus 868 / 780 emitted cell rows.

**Understatement distribution.** Relative understatement = missing excursion / reconstructed
initial-observation excursion. “Materially changed” means the side-aware reconstructed max price
exceeds emitted `max_price` by more than `1e-12 × (1 + |reconstructed max price|)`; this is
numerical materiality, not an economic threshold.

| Population | n | Absolute mean / median / p95 / max (raw price units) | Relative mean / median / p95 / max |
|---|---:|---:|---:|
| All ATR-undefined, zeros included | 868 | 4.6982 / 0.6100 / 24.1000 / 37.1000 | 59.13% / 63.75% / 96.77% / 99.57% |
| Materially changed only | 780 | 5.2283 / 0.8800 / 24.1000 / 37.1000 | 65.80% / 71.43% / 96.81% / 99.57% |

Pooled absolute magnitudes mix instrument units; use the instrument rows below. Relative values
are comparable across layers. The compact JSON retains absolute and relative q0/q25/q50/q75/
q90/q95/q99/q100 for every layer value, including zero-exposure configs.

| Layer | Value | Exposed | Changed (% exposed) | Changed absolute median / p95 | Changed relative median / p95 |
|---|---|---:|---:|---:|---:|
| Instrument | EURUSD | 216 | 202 (93.52%) | 0.00055 / 0.00164 | 66.87% / 96.81% |
| Instrument | XAUUSD | 342 | 320 (93.57%) | 0.83 / 5.71 | 64.25% / 95.73% |
| Instrument | USTEC | 310 | 258 (83.23%) | 11.20 / 37.10 | 73.51% / 97.01% |
| Timeframe | 15m | 30 | 28 (93.33%) | 0.58 / 0.63 | 43.61% / 95.45% |
| Timeframe | 30m | 198 | 170 (85.86%) | 0.30 / 10.30 | 60.59% / 95.56% |
| Timeframe | 60m | 640 | 582 (90.94%) | 1.66 / 24.10 | 72.89% / 97.01% |
| Reference | 1h | 536 | 478 (89.18%) | 0.63 / 21.10 | 64.37% / 96.77% |
| Reference | 4h | 332 | 302 (90.96%) | 2.04 / 24.10 | 73.36% / 97.06% |
| Method | BREAKOUT_BAR | 434 | 390 (89.86%) | 0.88 / 24.10 | 71.43% / 96.81% |
| Method | LEVEL_CLOSE | 434 | 390 (89.86%) | 0.88 / 24.10 | 71.43% / 96.81% |

Only five configs have exposure: PREVIOUS_1H 602/534 changed, PREVIOUS_4H 40/40,
PREVIOUS_ASIA 48/44, ROLLING_7 174/158, and ROLLING_14 4/4. The other six declared configs
have zero ATR-undefined rows; full denominators and distributions are in the JSON.

**Decision impact.** Coverage/lifecycle/status/attribution totals include these objects but do
not use the biased values. The raw-bps identity check includes them only by re-deriving bps from
the same biased `max_excursion`; finite-ATR and `strong_move` checks exclude them. The
future-destroy control also excludes every exposed row because `max_excursion_atr` is null,
including 112 primary rows (84 changed completed rows), so its published result does not change.
The exact-state hypothesis is still not clean for maximum excursion: low prevalence among all
raids does not offset 780/868 changed values on the exposed path. Unaffected count, chronology,
lifecycle, and finite-primary control findings remain numerically unchanged.

## 7. Interpretation boundary — no verdict assigned

This follow-up assigns no final or replacement verdict. It resolves the old fixture/cardinality
contradiction, supplies complete declared-layer marginals, and names every future-destroy
population and fraction. It also finds a real, scoped implementation defect in ATR-undefined
maximum-excursion tracking. Accordingly, this analysis stops interpretation of the affected
maximum-excursion value path rather than changing strategy code or relabelling the frozen run.

**Final verdict is the operator's.** No tradability, P&L, Sharpe, or PSR conclusion follows.
