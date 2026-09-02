# Data Analysis: EXP-104

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled observed (read directly from an emitted artifact) or inference (a mechanism
reading of observed numbers that is not itself measured). Zero-cost model: every figure is
gross and cost-free (ZERO-COST-DISCLOSURE).

Vehicle: analysis-only re-read of frozen EXP-100 AMENDMENT-14 TRAIN (264 cells). No TEST,
no holdout, no EXP-100 rerun, no family status change. Hypothesis in scope: HYP-004 only.

Per-stratum tables below are taken from the registered live artifact
`python/experiments/EXP-104/results/analysis_results.json` (7260 `value_rows` +
`extra.frequency_census`). Observed means/n were recomputed from raw `raids.parquet` for
**one** cell only (`ctrader-eurusd-15m-breakout_bar-1h-previous_1d`) via
`python/experiments/EXP-104/analysis_code/cross_check_one_cell.py`. Full 264-cell parquet
re-aggregation was not run this pass. 10k bootstrap and 2,000 destroys were **not**
rerun; leak-tripwire numbers are from `extra.control` in the live artifact.

ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable

## 1. Integrity gate (blocking)

Only this section has blocking authority.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells `blocking_pass`) | PASS | `python/experiments/EXP-100/results/estimand_validation.json` and EXP-104 copy: `blocking_pass=true`, `n_cells=264`; 264/264 cell `blocking_pass=true`. sha256 prefix `1593851873c318f3` identical EXP-100..104 |
| Zero-cost (`no_cost_charged`, no directive-gap costs) | PASS | 264/264 `no_cost_charged.ok=true`, `cost_model=NO_COST_CHARGED`, `cost_bps=0.0`, directive `null`. One-cell `run_metadata.json`: `cost_model=NO_COST_CHARGED`, `n_fills=0` |
| Provenance (verdict-bearing columns ≤ t−1) | PASS on checked joins | Live `source.profile_regime_join`: `regime_mismatches=0`, `missing_preceding_marks=0`, `unmatched_raids=0`, `duplicate_profile_keys=0`, `extra_profiles=0`. One-cell raw: `raid_regime` equals preceding `bar_marks.regime` on all 13,580 raids; missing preceding=0. `causal_failures=[]`. See provenance table |
| Leak tripwire collapsed + non-vacuous (bite = `INTEGRITY_Z × bootstrap_SE_raw`, A-15) | PASS (artifact, not recomputed) | `extra.control`: 4356 records, `blocking_pass` all true, `destroyed_survives` all false, `fixed_points=0`, `void_populations=[]`, reasons empty. 1310 `raw_bite=true`; all 1310 have `abs(destroyed_mean) ≤ 2.8 × raw_bootstrap_se`. Bite collapse ratio min/median/max = −0.0240 / −0.00089 / 0.0255. Nested `destroyed_bootstrap_se` disclosed, not used as the non-bite scale (A-15) |
| Singleton destroy groups (A-16) | PASS (disclose-only) | 104 control records carry a size-1 group; 0 records are all-singleton; 0 VOID_NO_MOVABLE_ROWS / VOID_NO_CHANGED_VALUE. Control not voided |
| Holdout untouched | PASS | Fence `2021-06-02T00:01:00Z`–`2023-11-22T00:00:00Z`. One-cell `sweep_ts_ns` max `1700609340e9` < TRAIN_END `1700611200e9`. Live attestation `rows=9840478` inside TRAIN emission. No TEST/holdout path loaded |
| Price-primary (engine emission under fence) | PASS as event study | `data/nautilus_runs/EXP-100/full/`; one-cell `emission_contract_version=nautilus-emission-v1`, Nautilus `1.230.0`, `one_backtest_node=true`. No P&L estimand |
| No experiment-local accounting defs | PASS | `python/experiments/EXP-104/code/` absent. This analysis did not import `analysis_code/analysis.py` |

Live `integrity.blocking_pass=true`, `reasons=[]`.

### Provenance table

| Column | Inputs & timestamps | ≤ t−1? | Evidence |
|---|---|---|---|
| `raid_regime` / `raid_atr` | cached ATR/close before observation update; join `sweep_ts_ns` → preceding `bar_marks` | YES on live join + one cell | live mismatches=0; one-cell mismatches=0 |
| `confirmation_regime` | post-update if same-timestamp observation, else last completed observation | not re-traced bar-by-bar this pass | live `causal_failures=[]`; golden ordering is design text only |
| `endpoint_regime` | state at completed reference event | not re-traced bar-by-bar this pass | same |
| `bar_marks.regime` | post-update observation label; does not overwrite raid label | YES as audit key | one-cell preceding-mark join |
| later-swing outcomes (`swing_*`, `strong_move`) | emitted on completed primary rows | event-time, not a next-bar trade | object identity: event study, no orders |
| frequency exposure | preceding mark regime in `{LOW,MID,HIGH}` | YES | one-cell exposure matches live exposure |

## 2. Question list

1. Per-bar/per-leg totals reconcile? ANSWERED §1 — gate `reconciliation.ok`, note `no leg ledger`; not a P&L object.
2. P&L-bearing object vs estimand? ANSWERED §1/§2.1 — none. Event study on raids. L-16 match: measurement object = raid/swing object.
3. Per-leg gross distribution? UNANSWERED as P&L — no legs. Later-swing outcome distributions: §2.3 (live) + one-cell raw.
4. Episode anatomy? UNANSWERED — no multi-leg trading episodes.
5. Concentration / top winners? ANSWERED as swing tails, not P&L — §2.5. Full 264-cell tail shares not recomputed from parquet.
6. Per-year totals? ANSWERED only for the one raw cell — §2.6. Full 264-cell year split not scanned this pass.
7. Per-stratum headlines? ANSWERED from live `value_rows` / `frequency_census` — §2.3–§2.4. Pooled figures disclosure only.
8. Occupancy? UNANSWERED — no strategy time-in-market. Event study.
9. Annualised return / Sharpe / maxDD vs buy-and-hold? UNANSWERED — no P&L estimand.
10. Exposure risk (open legs, MAE)? UNANSWERED — no legs.
11. Zero-cost verification? ANSWERED §1. Caveat on every money-bearing table.
12. PSR pairing? UNANSWERED / N/A — no mean-trade/leg bps series. `swing_bps` is a swing outcome, not a trade return.
13. Control collapse fraction + vacuity? ANSWERED §1 and §2.7 from live `extra.control` (not recomputed).
14. What would make headlines wrong? ANSWERED §5; one-cell raw executed; full parquet recompute not executed.
15. Sample-size context? ANSWERED — every live row kept; 1980 `EMPTY_ARM_OR_COMPARATOR` disclosed; n_clusters 41–1889 (median 334) on labelled `swing_atr`.
16. Direct comparison vs MID? ANSWERED — all 7260 rows are LOW/HIGH vs MID inside the named stratum.

### 2.1 Object identity and census (live artifact, observed)

| Item | Value | Source |
|---|---|---|
| TRAIN raid rows | 9,840,478 | `source.attestation.rows` |
| Cells | 264; live TF labels **60m** (not `1h`) | `value_rows.stratum.timeframe` |
| Status | COMPLETED 789,326; CONFIRMED_NON_PRIMARY 4,316,600; FAILED_BREAKOUT 4,702,900; RIGHT_CENSORED_EXCURSION 30,520; RIGHT_CENSORED_CONFIRMATION 626; RIGHT_CENSORED_ENDPOINT 506 | `extra.census.status` |
| `raid_regime` | LOW 3,226,992; MID 2,986,976; HIGH 3,552,404; REGIME_WARMUP 73,238; ATR_UNDEFINED 868 | `extra.regime_census` |
| Later-swing denominator | `status=COMPLETED` ∧ `primary_attribution` ∧ `primary_completed` = 789,326 completed (live status). Warmup/undefined never used as contrast arms | design + census |
| Profile join | MATCHED 9,840,478 | `extra.integrity_evidence` |
| Missingness (null swing fields) | `swing_atr`/`swing_price`/`swing_bps`/`strong_move` 9,050,758; `swing_duration_ns` 9,050,646 | `extra.census.missingness` |
| `value_rows` | 7260 = 528 labelled cell-sides × 2 arms × 5 channels + 1980 null-method placeholders | live |
| Labelled nonempty outcome rows | 5280, reason `None`. Placeholder 1980 `EMPTY_ARM_OR_COMPARATOR` with `confirmation_method=None` | live |
| Frequency census | 2178 rows = 726 strata × 3 regimes; 1584 labelled (264×2 sides×3); 594 null-method `EMPTY_EXPOSURE` | live |

ATR-undefined: 868 raid rows (`profile_undefined_reason` / `raid_regime`). Excluded from `swing_atr` and `strong_move` channels in the live adapter; countable elsewhere. Warmup/undefined observation exposure summed over 264 unique cells (one side, live census): REGIME_WARMUP 66,264 marks; ATR_UNDEFINED 3,696 marks. Reported separately, not as arms.

### 2.2 One-cell raw cross-check (observed)

Cell `data/nautilus_runs/EXP-100/full/ctrader-eurusd-15m-breakout_bar-1h-previous_1d/`.
Script `analysis_code/cross_check_one_cell.py` → `cross_check_one_cell.json`.

| Check | Raw | Live | Match? |
|---|---|---|---|
| Raid rows (TRAIN fence) | 13,580 | (cell subset of 9,840,478) | cell complete |
| `swing_duration_ns == duration_ns` | 0 mismatches | live `duration_alias_mismatches=0` | YES |
| `raid_regime` vs preceding mark | 0 mismatches; 0 missing preceding | join zeros | YES |
| Later-swing n by side×regime | LOW/LOW 283, LOW/MID 349, LOW/HIGH 588; HIGH-side 237/308/456; warmup 4 | `value_rows` n | YES |
| Outcome means + n, 5 channels × 2 sides × 2 arms | 20/20 | `value_rows.observed` | YES |

Frequency on the same cell (design identity `rate = 1000 × starts / exposure`):

| Side | Regime | Raw exposure | Live exposure | Raw starts (all raids) | Live `starts` | Raw per-side rate | Raw pooled-side rate | Live `rate_per_1000` |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LOW | LOW | 19971 | 19971 | 1907 | 283 | 95.49 | 167.94 | 167.94 |
| LOW | MID | 18294 | 18294 | 2316 | 349 | 126.60 | 226.63 | 226.63 |
| LOW | HIGH | 19676 | 19676 | 3478 | 588 | 176.76 | 307.23 | 307.23 |
| HIGH | LOW | 19971 | 19971 | 1447 | 238 | 72.46 | 167.94 | 167.94 |

Observed: live **exposure** matches preceding-mark counts. Live **starts** match later-swing n (283), not all-raid starts (1907). Live **rate** matches pooled-across-sides all-raid starts / exposure (167.94), not `1000 × row.starts / row.exposure`. Same rate is duplicated on both sides. Inference: the registered frequency table does not obey the design row identity; CIs are not independent per side.

### 2.3 Later-swing contrasts vs MID (live `value_rows`, labelled 528 strata)

ZERO-COST-DISCLOSURE applies to `swing_price` / `swing_bps` (gross, not tradable).

Primary channels. Interval class uses live L=5 95% interval. Not a row verdict.

| Channel | Arm | n rows | point + | point − | CI above 0 | CI overlaps 0 | CI below 0 |
|---|---|---:|---:|---:|---:|---:|---:|
| `swing_atr` | LOW | 528 | 526 | 2 | 400 | 128 | 0 |
| `swing_atr` | HIGH | 528 | 12 | 516 | 0 | 94 | 434 |
| `swing_duration_ns` | LOW | 528 | 94 | 434 | 16 | 360 | 152 |
| `swing_duration_ns` | HIGH | 528 | 438 | 90 | 296 | 222 | 10 |
| `strong_move` | LOW | 528 | 482 | 46 | 266 | 262 | 0 |
| `strong_move` | HIGH | 528 | 14 | 514 | 0 | 180 | 348 |
| `swing_price` | LOW | 528 | 272 | 256 | 28 | 414 | 86 |
| `swing_price` | HIGH | 528 | 318 | 210 | 36 | 476 | 16 |
| `swing_bps` | LOW | 528 | 282 | 246 | 30 | 422 | 76 |
| `swing_bps` | HIGH | 528 | 322 | 206 | 38 | 472 | 18 |

`swing_atr` n (sum of labelled rows, MID counted once per stratum): LOW 252,928; MID 238,200; HIGH 292,110. n_clusters min/median/max 41 / 334 / 1889.

`swing_atr` interval class by symbol (both arms, 352 rows each):

| Symbol | CI above 0 | CI overlaps 0 | CI below 0 |
|---|---:|---:|---:|
| EURUSD | 142 | 56 | 154 |
| XAUUSD | 106 | 128 | 118 |
| USTEC | 152 | 38 | 162 |

`swing_atr` by timeframe: 15m 84 / 48 / 132; 30m 112 / 24 / 128; 60m 204 / 150 / 174 (above / overlap / below).

Mean vs median sign on `swing_atr`: same 1018 / 1056, opposite 38. On `swing_duration_ns`: same 542, opposite 514 (median often 0 contrast).

Seed-low-range straddle among `swing_atr` rows whose L=5 CI excludes 0: 12 / 834. L2/L5/L10 interval-class change: 64 / 1056.

Example (observed, not a ranking): EURUSD 15m BREAKOUT_BAR 1H PREVIOUS_1D side=LOW.

| Channel | Arm | arm_n / MID n | arm mean | MID mean | contrast | L=5 interval | median contrast |
|---|---|---|---:|---:|---:|---|---:|
| `swing_atr` | LOW | 283 / 349 | 6.036 | 5.101 | +0.935 | [0.0015, 1.838] | +0.932 |
| `swing_atr` | HIGH | 588 / 349 | 3.382 | 5.101 | −1.719 | [−2.371, −1.100] | −0.978 |
| `swing_duration_ns` (hours = ns/3.6e12) | LOW | 283 / 349 | 5.46 h | 7.56 h | −2.11 h | excludes 0 | 0 h |
| `swing_duration_ns` | HIGH | 588 / 349 | 10.56 h | 7.56 h | +2.99 h | excludes 0 | +1.00 h |
| `strong_move` | LOW | 283 / 349 | 0.866 | 0.819 | +0.046 | overlaps 0 | 0 |
| `strong_move` | HIGH | 588 / 349 | 0.707 | 0.819 | −0.112 | [−0.156, −0.067] | 0 |
| `swing_bps` | LOW | 283 / 349 | 29.46 | 33.50 | −4.03 | overlaps 0 | −5.20 |

Pooled across strata is disclosure only and is not used as a finding (L-03).

### 2.4 Raid frequency (live census; descriptive; not under future-destroy)

Design rate is per `asset × TF × method × ref × config × side`. Live labelled rows: 1584, `empty_exposure_reason=None` on all labelled rows. Null-method placeholders: 594 `EMPTY_EXPOSURE` with **non-null** `rate_per_1000` (kept, not dropped).

Because one-cell rates are identical across sides, interval counts are also reported on **264 unique cells** (side=LOW slice of `uncertainty`, default L=96/48/24 for 15m/30m/60m). Destroy does not cover this read.

| Contrast | Unique cells | CI above 0 | CI overlaps 0 | CI below 0 |
|---|---:|---:|---:|---:|
| LOW−MID rate / 1000 marks | 264 | 44 | 98 | 122 |
| HIGH−MID rate / 1000 marks | 264 | 180 | 68 | 16 |

Labelled mean `rate_per_1000` (live, 528 side-rows, same numbers both sides): LOW 1381.8, MID 1390.7, HIGH 1507.6. Starts on side=LOW slice: LOW 125,752; MID 121,942; HIGH 152,612 — these starts track later-swing n, not all-raid starts (one-cell).

### 2.5 Concentration / tails

Not P&L. One-cell later-swing `swing_atr` means already right-skewed (LOW mean 6.04 vs median 4.58; HIGH mean 3.38 vs median 2.67). Full-emission top-1%/top-5% share of ATR-sum was not recomputed this pass. `strong_move` is common in the example (MID 0.82, LOW 0.87, HIGH 0.71), so the HIGH contrast is a drop in an already high base rate, not a rare-event tail.

### 2.6 Year split

Timestamps exist (`sweep_ts_ns`). Full 264-cell year split not scanned. One-cell later-swing counts:

| Year | LOW | MID | HIGH | WARMUP |
|---|---:|---:|---:|---:|
| 2021 | 112 | 143 | 194 | 4 |
| 2022 | 205 | 270 | 442 | 0 |
| 2023 | 203 | 244 | 408 | 0 |

Inference (one cell only): pattern is not a single-year spike; 2022 has the most completed primaries, matching the TRAIN mass.

### 2.7 Future-destroy (live artifact only)

Source: `analysis_results.json extra.control`. 2,000 derangements **not** rerun.

| Item | Observed |
|---|---|
| Records | 4356 (3 outcome channels × 2 arms × strata incl. placeholders) |
| `fixed_points` | 0 |
| `population_match` | true |
| `blocking_pass` | 4356/4356 true |
| `destroyed_survives` | 0 |
| `raw_bite` | 1310 true / 3046 false |
| Bite channels | `swing_atr` 622, `strong_move` 392, `swing_duration_ns` 296 |
| Bite collapse ratio | near 0 (min −0.024, median −0.00089, max 0.0255) |
| A-15 | 1310/1310 `abs(m_destroy) ≤ 2.8 × raw_bootstrap_se`; nested destroyed SE disclosed smaller (example HIGH `swing_atr` se_raw 0.324 vs se_dest 0.0055) |
| A-16 | 104 singleton groups disclosed; control not voided |
| VOID reasons | none |
| Empty-arm notes | 1188 `EMPTY_ARM_OR_COMPARATOR - no estimate possible` |
| Example group | EURUSD 15m … PREVIOUS_1D: `group_sizes=[1224]`, `moved_rows=1224` (one movable group) |

Example HIGH `swing_atr` (raw bites): raw −1.719, destroyed mean +0.0073, collapse −0.0043, survives false.

Frequency is **not** claimed validated by this destroy.

## 3. Evidence FOR the hypothesis

Hypothesis (HYP-004): LOW/HIGH causal volatility regimes differ from MID in later-swing outcomes **and** raid frequency.

1. **`swing_atr` vs MID is directionally structured, not noise.** Observed: LOW−MID point contrast positive in 526/528 labelled strata; L=5 interval above 0 in 400/528. HIGH−MID point negative in 516/528; interval below 0 in 434/528. Same sign on means and medians in 1018/1056. One-cell raw reproduced the live means (LOW +0.935 ATR, HIGH −1.719 ATR). n is large (arms 253k / 238k / 292k).
2. **`strong_move` moves with the same LOW-up / HIGH-down pattern.** HIGH−MID interval below 0 in 348/528; LOW−MID above 0 in 266/528 (262 overlap). Example HIGH −0.112 [−0.156, −0.067].
3. **Raid frequency HIGH vs MID differs on most unique cells.** 180/264 unique-cell default-L intervals above 0 for HIGH−MID; only 16 below 0. Live mean rate/1000 marks HIGH 1508 vs MID 1391. Descriptive only; not destroy-covered.
4. **Integrity control does not explain the raw outcome contrasts as an unmoved labeling artifact.** When the raw contrast bites, destroyed means sit near 0 (collapse |ratio| ≤ 0.0255; 0 survivals). A-15 raw-SE bite band holds on all 1310 biting records (artifact).
5. **Causal label join is clean on the checked paths.** 0 regime mismatches on 9.84M attested rows and on the raw cell. Warmup/undefined held out of arms.

## 4. Evidence AGAINST the hypothesis

1. **The hypothesis is a conjunction; frequency is the weaker and internally inconsistent half.** Live `starts` ≠ all-raid starts; live `rate_per_1000` ≠ `1000 × starts / exposure`; rates/CIs duplicate across sides (one-cell). Per-side design estimand is not what the rate column reports. LOW−MID frequency intervals overlap 0 in 98/264 unique cells and go the other way in 44/264.
2. **`swing_duration_ns` does not carry the same story.** 582/1056 intervals overlap 0. Mean vs median sign disagrees in 514/1056. Example: LOW mean duration shorter than MID (CI excludes 0) but median contrast 0.
3. **Price/bps secondary outcomes are mostly overlap.** `swing_price` 890/1056 overlap 0; `swing_bps` 894/1056 overlap 0. ZERO-COST; not a trade return.
4. **Heterogeneity (L-03).** XAUUSD `swing_atr` intervals overlap 0 in 128/352 vs USTEC 38/352. 60m has 150/528 `swing_atr` overlaps vs 24/264 on 30m. A pooled “regimes differ” sentence would mask XAUUSD/60m.
5. **LOW and HIGH differ from MID in opposite directions.** That still matches the word “differ”, but it contradicts a single “high vol → larger later swing” mechanism. Inference, not a measured mechanism.
6. **Some excluding CIs are fragile.** 12 `swing_atr` excluding-0 rows have `seed_low_range` straddling 0; 64/1056 change interval class across L=2/5/10.
7. **Empty / warmup mass is real.** 73,238 warmup raids; 868 ATR_UNDEFINED; 1980 empty outcome placeholders; 594 EMPTY_EXPOSURE frequency rows with filled rates. Not arms, but they are part of the emission.
8. **No economic object.** Occupancy, Sharpe, buy-and-hold, PSR, P&L: N/A. Even a clean event-study difference is not a tradable edge (ZERO-COST-DISCLOSURE).

## 5. What would make the headline numbers wrong (N7)

| Headline | Probe | Run? |
|---|---|---|
| Live `swing_atr` means / n | Recompute from `raids.parquet` later-swing filter, ATR_UNDEFINED dropped | YES, one cell, 20/20 match. Not run on 264 cells |
| Live frequency `rate=1000×starts/exposure` | Recompute preceding-mark exposure + all-raid starts per side | YES, one cell: **identity fails** on starts and rate |
| Intervals exclude 0 | Do not rerun 10k bootstrap; read seed ranges + L=2/10 | YES on live fields; 12 seed-straddle, 64 block-class changes |
| Destroy collapse | Do not rerun 2,000 derangements; read `collapse_ratio`, A-15, A-16 | YES from artifact |
| Wrong population (include failed/censored) | Compare later-swing n vs all raids | YES, one cell: later 2,225 vs 13,580 raids |
| Year artifact | Split `sweep_ts_ns` | YES one cell only; all three TRAIN years present |
| Side-pooled masking | Compare sides | YES: live frequency rates identical across sides |
| Holdout leakage | Timestamp vs TRAIN_END; no TEST paths | YES one cell + no TEST load |

## 6. Anomalies & open questions

- Live frequency census: `EMPTY_EXPOSURE` rows still carry numeric rates/contrasts (594 null-method rows). Design asked null rate/contrast on empty exposure.
- Live frequency `starts` track later-swing counts on the checked cell; rates track pooled all-raid starts. Two different start definitions in one table.
- Confirmation_method `None` strata appear in `value_rows` and frequency (198 placeholders × channels). Kept, not dropped.
- `strong_move` medians are 0/1 with median contrast often 0 even when the mean contrast’s interval excludes 0 (proportion, not a median-friendly channel).
- Full 264-cell year split, tail shares, and independent duration-alias scan across all cells: not done this pass.
- Suggested probes on the existing emission (no new run): (a) rebuild frequency with design identity per side using all `raid_id` starts; (b) stream later-swing means for all 264 cells to confirm the other 263; (c) year×regime `swing_atr` table.

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- Recommendation: **SUPPORTED** (descriptive HYP-004 only; not tradable; not family).
- Driven by:
  1. LOW later-swings are larger in ATR units than MID in 400/528 strata (interval above 0); HIGH later-swings are smaller in 434/528 (interval below 0); one-cell raw matched live means.
  2. HIGH-regime raid rate exceeds MID on 180/264 unique cells (live default-L interval above 0), LOW rate is below MID more often than above (122 vs 44), so frequency also differs — with the construction caveat in §2.2/§4.1.
  3. Future-destroy, when it bites, collapses those outcome contrasts (artifact collapse |ratio| ≤ 0.026, 0 survivals, A-15/A-16 clean).
- Would change if: a design-faithful per-side frequency rebuild put HIGH−MID and LOW−MID intervals mostly on 0; or a 264-cell raw recompute showed live `swing_atr` means do not match parquet outside the checked cell; or duration/price were treated as co-primary and their overlap-0 majority were required for support.
- Hand-off: final verdict is the operator's. Named probes: rebuild frequency from preceding marks + all raid starts; stream all-cell later-swing means; year×regime ATR table. No TEST/holdout. No family action.

Operator one-liner: **recommended SUPPORTED** — later ATR swings and raid rates differ by causal vol regime (LOW ≠ MID ≠ HIGH), but this is an event study, not a trade, and the live frequency table does not follow its own starts/exposure formula.
