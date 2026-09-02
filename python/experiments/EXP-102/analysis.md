# Data Analysis: EXP-102

## 0. Boundary statement (N1 — binding)

This record issues NO final verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled observed (read directly from an emitted artifact) or inference (a mechanism
reading of observed numbers that is not itself measured). The recommendation in §7 is
non-final and applies only to EXP-102 / HYP-002. The operator decides.

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

**Vehicle.** Analysis-only re-read of frozen EXP-100 AMENDMENT-14 TRAIN (264 cells).
No TEST, no holdout, no EXP-100 rerun, no family status change. Bootstrap (10k × 5
seeds) and 2,000-seed destroy were **not** recomputed; those numbers are copied from
`python/experiments/EXP-102/results/analysis_results.json` `extra.control`.
Independent recomputes of means/medians/n: one cell from
`data/nautilus_runs/EXP-100/full/ctrader-eurusd-15m-breakout_bar-1h-previous_1h/raids.parquet`.
Per-stratum 1-vs-0 and 2+-vs-0 tables: registered live `value_rows` (7260 rows),
cross-checked against that one-cell raw recompute (20/20 matched). Experiment-local
`analysis_code/analysis.py` was not imported or called.

**N2–N11.** N2: measured object is an emitted level-linked raid and its later swing;
no trade/leg/P&L. N3/N10: empty arms kept. N4: bands `1` and `2+` vs fixed
`prior_raid_count=0` in the same named stratum; no arm-vs-arm. N5: pooled figures
are disclosure only. N6/N6b: only integrity bite is `INTEGRITY_Z=2.8 × bootstrap_SE_raw`
(AMENDMENT-15). N7: §5. N8: TEST/holdout not read. N9: zero-cost as above. N11: no
machine row labels. PSR is N/A (no trade/leg-bps series; design §6).

## 1. Integrity gate (blocking)

Only this section has blocking authority.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells `blocking_pass`) | **PASS** | `python/experiments/EXP-100/results/estimand_validation.json` and EXP-102 copy: `blocking_pass=true`, `n_cells=264`, 0 cells with `blocking_pass=false`. sha256 prefix `1593851873c318f3` identical for EXP-100..104 copies. Gate **not** re-run. |
| Zero-cost compliance | **PASS** | 264/264 `no_cost_charged.ok=true`; `cost_model=NO_COST_CHARGED`; sample cell `run_metadata.json` same; live `zero_cost_disclosure.cost_model=NO_COST_CHARGED`. |
| Provenance trace (verdict-bearing columns) | **PASS (event-study scope)** | Later-swing fields are post-confirmation outcomes by construction; `prior_raid_count` is earlier completed raids. Live `extra.integrity_evidence.causal_failures=[]`. One-cell: duration alias mismatches 0; `endpoint_ts_ns >= confirmation_ts_ns` on sampled later-swing rows. No `rct[di]` path; `n_fills=0`. |
| Leak tripwire collapsed + non-vacuous (bite = INTEGRITY_Z × bootstrap_SE_raw, A-15) | **PASS (artifact, not recomputed)** | Fixture `results/fixture_integrity.json` `blocking_pass=true`. Live control 4356 records, `blocking_pass` all true, `destroyed_survives` all false, `fixed_points` all 0, `void_populations=[]`. Raw bite 1236; on those, destroyed mean sits inside the raw SE band (A-15). Collapse median ≈ 0. See §1.1. |
| Holdout untouched | **PASS** | No TEST/holdout path opened. Live `after_train_rows=0`, `before_train_rows=0`. TRAIN fence 2021-06-02T00:01:00Z–2023-11-22T00:00:00Z. |
| Price-primary | **PASS** | Source `data/nautilus_runs/EXP-100/full/` (264 dirs). Sample metadata: `emission_contract_version=nautilus-emission-v1`, Nautilus `1.230.0`, `one_backtest_node=true`, `n_fills=0`. |
| No experiment-local accounting defs | **PASS** | No `python/experiments/EXP-102/code/` directory. `check_no_local_accounting` N/A-pass. |
| Raid identity / A-16 singletons | **PASS / disclosed** | Live `duplicate_raid_ids=0` after `source_cell` tagging. One-cell: 110011 unique `raid_id` / 110011 rows; BREAKOUT_BAR vs LEVEL_CLOSE raid_id **sets equal**. A-16: 104 singleton destroy groups disclosed; control not voided. |

**Blocking conclusion (observed):** integrity may be read. Destroy/bootstrap numbers below
are from the registered live artifact, not recomputed.

### 1.1 Leak tripwire (registered live `extra.control`; not recomputed)

`COUNT_CROSSWISE_FUTURE_DESTROY`, 2,000 derangements, joint resampling
(`independent_arms=false` on all 5280 finite value rows). INTEGRITY_Z=2.8.
AMENDMENT-15: when raw bites, require `|m_destroy| <= 2.8 × bootstrap_SE_raw`.
AMENDMENT-16: n<2 groups stay fixed and are disclosed.

| Item | Observed |
|---|---|
| Control records | 4356 (3168 finite raw; 1188 EMPTY_ARM_OR_COMPARATOR) |
| `blocking_pass` | 4356 true / 0 false |
| `destroyed_survives` | 0 true |
| `fixed_points` | 0 on every record |
| `population_match` | true on extra.control |
| VOID reasons | none; `void_populations=[]` |
| Raw bite true | 1236 |
| Collapse ratio (finite, n=3162) | min −9.82, p05 −0.060, **median −0.00135**, p95 0.067, max 17.93 |
| \|collapse\| < 0.5 | 3115 / 3162 |
| \|collapse\| > 1 | 25 / 3162 (small-raw-denominator ratios; disclosed, not a row veto) |
| A-15 bite: destroy inside raw SE band | 1228 inside / 0 outside among bite rows with stored summary SE; artifact `raw_bite=1236` uses per-seed SE (8-row SE-summary difference, not a fail) |
| A-16 singleton groups | 104 groups of size 1 in 104 records; example `EURUSD/30m/BREAKOUT_BAR/1H/LOW/PREVIOUS_1H:1-vs-0:swing_duration_ns` group_sizes `[1, 2863]`, moved 2863, reasons `[]`, `blocking_pass=true` |
| Example bite (live, not recomputed) | `EURUSD/15m/BREAKOUT_BAR/1H/HIGH/PREVIOUS_1H:1-vs-0:strong_move`: raw −0.1955, SE 0.0240, m_destroy −0.00065, collapse 0.0033, moved 2967, fp 0. Bite band 2.8×SE ≈ 0.067; \|m_destroy\| inside. |

**Fixture (registered, not recomputed).** Plants +0.50 ATR, +3.6e12 ns, +0.25 strong_move
on band `1` vs `0`. Destroyed means ≈ 0; collapse ≈ −0.0037 / −0.0035 / −0.0031.
Band `2+` EMPTY on the 200+200 fixture (expected). `blocking_pass=true`.

### Provenance table

| Column | Inputs & timestamps | ≤ t−1 / causal? | Evidence |
|---|---|---|---|
| `prior_raid_count` | completed raids on same `level_id` before this raid | observed: live `level_count_sequence_failures=0`, `invalid_prior_raid_count_rows=0` | `analysis_results.json` extra.integrity_evidence |
| `status` / `primary_attribution` / `primary_completed` | confirmation vs expected-side HTF event | observed: later-swing population uses COMPLETED ∧ both flags true | design §3; one-cell later n=5852 equals COMPLETED in that cell |
| `swing_*` / `strong_move` | confirmation → opposing endpoint | future of the raid **by estimand**; leak control destroys this block | design §5; live destroy non-survival |
| `swing_duration_ns` / `duration_ns` | asserted alias | observed: live duration alias mismatches 0; one-cell 0 | integrity evidence + one-cell |
| `raid_id` | per `source_cell` | observed: `duplicate_raid_ids=0`; methods share ids | live + one-cell set equality |

## 2. Question list

1. Gate completeness / zero-cost / no local accounting? **ANSWERED** §1.
2. Object identity (raid vs trade)? **ANSWERED** §2.1 — event study; P&L N/A.
3. Per-leg gross / occupancy / Sharpe / buy-and-hold / exposure / PSR? **UNANSWERED (N/A)** — no trade, leg, episode, or capital estimand (design §2–§6).
4. Do later-swing outcomes differ for band `1` vs `0`? **ANSWERED** §3–§4.
5. Do they differ for band `2+` vs `0`? **ANSWERED** §3–§4.
6. Per-stratum structure / which layers drive or contradict? **ANSWERED** §2.3.
7. Empty arms? **ANSWERED** §2.2.
8. Concentration / tails of swing outcomes? **ANSWERED with scope** §2.4 (one-cell + contrast-estimate distribution; full 9.84M-row quantile scan not run).
9. Year split? **UNANSWERED** — timestamps exist (`endpoint_ts_ns`); full 264-cell year walk skipped by steering. Live `after_train_rows=0`.
10. ATR-undefined exclusion? **ANSWERED** §2.2.
11. Direct comparator only (N4)? **ANSWERED** — arms vs `0` only; `independent_arms=false`.
12. Destroy collapse / A-15 / A-16 / vacuity? **ANSWERED** §1.1 (artifact).
13. One-cell raw vs live means? **ANSWERED** §2.5 — 20/20 match.
14. Identity BREAKOUT_BAR vs LEVEL_CLOSE share `raid_id`? **ANSWERED** §1 / §2.5.
15. What would make headlines wrong? **ANSWERED** §5.

### 2.1 Object identity

HYP-002 estimand is later-swing **outcomes** (`swing_atr`, `swing_duration_ns`, unpaired
`strong_move` proportion) by prior-raid **count band**, comparator `0`.
`pnl_object=none`. Sample cell `n_fills=0`, `n_orders=0`, `n_positions=0`.

Later-swing population (design §3): `status==COMPLETED` ∧ `primary_attribution` ∧
`primary_completed`. Census COMPLETED = 789326. Outcome missingness 9,050,758
(`swing_atr`/`strong_move`/`swing_price`/`swing_bps`) of 9,840,478 rows — the
non-completed mass. Duration missingness 9,050,646 (112-row difference vs other
outcomes; disclosed).

### 2.2 Census, empty arms, ATR-undefined (observed)

Population labels (live, matches task): `0: 1,124,116` / `1: 1,016,744` / `2+: 7,699,618`;
rows `9,840,478`. Exact `prior_raid_count` keys: 250 (0..249).

| Status | n |
|---|---:|
| COMPLETED | 789326 |
| CONFIRMED_NON_PRIMARY | 4316600 |
| FAILED_BREAKOUT | 4702900 |
| RIGHT_CENSORED_EXCURSION | 30520 |
| RIGHT_CENSORED_CONFIRMATION | 626 |
| RIGHT_CENSORED_ENDPOINT | 506 |

Value rows: 7260 = 5 channels × 2 arms × 726 strata. Finite estimates 5280
(528 named method/reference strata × 2 arms × 5 channels). EMPTY_ARM_OR_COMPARATOR
1980 = 198 strata × 2 × 5. Those 198 are `confirmation_method=null` ×
3 symbols × 3 tf × 11 configs × 2 sides — unconfirmed rows, not later-swing.
**No finite later-swing stratum is empty on band 0, 1, or 2+** in the live value table.

ATR-undefined: excluded from `swing_atr` and `strong_move` (design / operator).
One-cell later-swing ATR-undefined = 0. Full ATR-undefined count not re-scanned;
EXP-100 record had 868 profile ATR-undefined raids in the emission.

### 2.3 Per-stratum CI class counts (live L=5 joint cluster bootstrap; not recomputed)

528 strata per arm×channel. Interval = median 95% percentile bounds across seeds 0–4.
Phrase: **bootstrap 95% CI excludes zero** where stated — not a hypothesis test.

**Band 1 vs 0**

| Channel | CI > 0 | CI < 0 | overlap 0 | arm_n median | cmp_n median | contrast p05 / median / p95 |
|---|---:|---:|---:|---:|---:|---|
| swing_atr | 4 | 266 | 258 | 82 | 59 | −3.28 / −0.895 / +0.280 |
| swing_duration_ns | 34 | 18 | 476 | 82 | 59 | −2.16e13 / +1.44e11 / +3.68e13 |
| strong_move | 0 | 438 | 90 | 82 | 59 | −0.429 / −0.245 / −0.029 |
| swing_bps (source summary) | 4 | 204 | 320 | 82 | 59 | −58.4 / −11.7 / +13.1 |
| swing_price (source summary) | 4 | 200 | 324 | 82 | 59 | — |

**Band 2+ vs 0**

| Channel | CI > 0 | CI < 0 | overlap 0 | arm_n median | cmp_n median | contrast p05 / median / p95 |
|---|---:|---:|---:|---:|---:|---|
| swing_atr | 2 | 354 | 172 | 1171 | 59 | −3.87 / −1.23 / +0.0017 |
| swing_duration_ns | 62 | 16 | 450 | 1171 | 59 | −1.70e13 / +9.20e11 / +3.48e13 |
| strong_move | 0 | 402 | 126 | 1171 | 59 | −0.245 / −0.130 / +0.068 |
| swing_bps (source summary) | 2 | 318 | 208 | 1171 | 59 | −67.3 / −16.3 / +3.16 |
| swing_price (source summary) | 2 | 316 | 210 | 1171 | 59 | — |

n_clusters (swing_atr rows): 1-vs-0 min 10 / med 128 / max 2130; 2+-vs-0 min 47 / med 392 / max 2573.

**Layer split — strong_move CI < 0 (no CI > 0 anywhere)**

| Arm | Layer | Counts (CI<0 / overlap / CI>0) |
|---|---|---|
| 1 | EURUSD / USTEC / XAUUSD | 164/12/0 ; 130/46/0 ; 144/32/0 |
| 1 | 15m / 30m / 60m | 112/20/0 ; 116/16/0 ; 210/54/0 |
| 1 | BREAKOUT_BAR = LEVEL_CLOSE | 219/45/0 each |
| 2+ | EURUSD / USTEC / XAUUSD | 158/18/0 ; 116/60/0 ; 128/48/0 |
| 2+ | BREAKOUT_BAR = LEVEL_CLOSE | 201/63/0 each |

**Layer split — swing_atr CI < 0**

| Arm | Layer | CI<0 / overlap / CI>0 |
|---|---|---|
| 1 | EURUSD / USTEC / XAUUSD | 86/90/0 ; 84/90/2 ; 96/78/2 |
| 1 | HIGH / LOW | 104/160/0 ; 162/98/4 |
| 2+ | EURUSD / USTEC / XAUUSD | 112/64/0 ; 116/58/2 ; 126/50/0 |
| 2+ | HIGH / LOW | 160/104/0 ; 194/68/2 |
| 1 and 2+ | BREAKOUT_BAR vs LEVEL_CLOSE | identical CI-class counts |

Methods match because they share raid identity (one-cell set equality; live
`duplicate_raid_ids=0`).

**Duration** is mostly overlap at every layer (476/528 and 450/528).

Block-length sensitivity vs L=5 sign-class: swing_atr L2 48 / L10 32 of 1056;
duration 28 / 42; strong_move 18 / 26. Seed-low-range straddle among CI-excludes-zero:
ATR 0/626, duration 4/130, strong_move 0/840.

Mean vs median contrast sign: ATR 1-vs-0 agree 484 / flip 44; 2+ agree 498 / flip 30.
strong_move almost no median contrast (boolean/step).

### 2.4 Tails / concentration (scoped)

Full-emission swing-outcome quantiles **not** recomputed (scan skipped).

One-cell later-swing `swing_atr` (n=5852, ATR-undefined 0): mean 4.63, std 4.46,
min −0.014, q25 1.91, median 3.24, q75 5.71, max 41.56. Duration hours
(`swing_duration_ns / 3.6e12`): mean ≈ 8.2 h, median 4 h, min 1 h.

Contrast-estimate distribution (§2.3) is the cross-stratum tail of **differences**,
not of raw swings. 2+ vs 0 ATR p95 ≈ 0: almost no stratum has a large positive
mean-ATR contrast.

### 2.5 One-cell raw recompute vs live

Cell `ctrader-eurusd-15m-breakout_bar-1h-previous_1h`: 110011 raids, unique raid_id
110011, later-swing 5852 = band 0:400 / 1:511 / 2+:4941. Partner LEVEL_CLOSE
raid_id set **equal**. Duration alias mismatches 0.

Independent means (COMPLETED ∧ primary flags; ATR-undefined dropped on ATR/strong_move;
finite values) vs live `observed.arm_mean` / `comparator_mean` / `arm_n` / `estimate`:
**20/20 match** (2 sides × 5 channels × 2 arms).

| Side | Channel | Arm | arm_n / cmp_n | raw contrast | live 95% CI (L=5) |
|---|---|---|---:|---:|---|
| HIGH | swing_atr | 1 | 266/204 | −0.505 | [−1.46, +0.42] overlap |
| HIGH | swing_atr | 2+ | 2497/204 | −1.099 | [−1.88, −0.38] CI excludes 0 |
| HIGH | strong_move | 1 | 266/204 | −0.195 | [−0.244, −0.150] CI excludes 0 |
| HIGH | strong_move | 2+ | 2497/204 | −0.0685 | [−0.079, −0.058] CI excludes 0 |
| HIGH | duration_ns | 1 | 266/204 | +2.53e12 (≈0.70 h) | overlap 0 |
| LOW | swing_atr | 1 | 245/196 | −1.351 | [−2.22, −0.52] CI excludes 0 |
| LOW | swing_atr | 2+ | 2444/196 | −1.919 | [−2.64, −1.24] CI excludes 0 |
| LOW | strong_move | 1 | 245/196 | −0.179 | [−0.228, −0.130] CI excludes 0 |
| LOW | strong_move | 2+ | 2444/196 | −0.0915 | [−0.107, −0.075] CI excludes 0 |

ZERO-COST-DISCLOSURE applies to these outcome tables (no P&L estimand).

## 3. Evidence FOR the hypothesis

Hypothesis: later-swing outcomes **differ** by prior-raid count vs count-zero.

1. **strong_move proportion, 1 vs 0 (observed).** 438/528 strata: bootstrap 95% CI
   below 0; **0** above; 90 overlap. Median contrast −0.245. Every symbol, timeframe,
   method, and side shows the same sign class (CI>0 = 0). Same-series PSR: N/A.
2. **strong_move, 2+ vs 0 (observed).** 402/528 CI below 0; 0 above; 126 overlap.
   Median contrast −0.130. Methods identical.
3. **swing_atr mean, 2+ vs 0 (observed).** 354/528 CI below 0; 2 above (thin weekly
   USTEC 60m LOW PREVIOUS_1W, n_cmp=17); 172 overlap. Median contrast −1.23 ATR.
   Comparator n median 59 vs arm 1171 — the negative contrast is not a tiny-arm fluke
   on the 2+ side.
4. **Destroy collapse (artifact, inference about alignment).** Median collapse −0.00135;
   biting example collapse 0.0033. Destroyed_survives=0. Inference: the count-band
   contrast is carried by **aligned future outcome blocks**, not by the count label
   alone (control is non-vacuous for these means/proportions).
5. **One-cell raw identity (observed).** Independent parquet means match live estimates
   exactly on 20 contrasts; raid_id unique per cell; methods share raid_ids.

## 4. Evidence AGAINST the hypothesis

1. **Duration is a primary estimator and mostly does not differ (observed).**
   1-vs-0: 476/528 overlap 0 (34 CI>0, 18 CI<0). 2+-vs-0: 450/528 overlap.
   Median contrasts near 0 relative to scale (~1e11–1e12 ns vs hour = 3.6e12).
   If “outcomes differ” is required on **both** mean ATR and mean duration, duration
   does not carry it.
2. **swing_atr 1 vs 0 is split, not unanimous (observed).** 266 CI<0, 258 overlap, 4 CI>0.
   About half the strata are compatible with no mean-ATR difference at this interval.
   Count-zero n is thin (median 59; min n_clusters 10). Overlap here is often
   “cannot see”, not a precise zero.
3. **Opposite-sign ATR strata exist (observed, small n).** All 6 CI>0 ATR rows are
   PREVIOUS_1W LOW, 60m, methods paired:
   - USTEC 1H, 1-vs-0 n=20/17, est +1.31, CI [0.42, 2.29]
   - USTEC 1H, 2+-vs-0 n=516/17, est +0.98, CI [0.33, 1.63]
   - XAUUSD 4H, 1-vs-0 n=5/5, est +2.06, CI [0.32, 3.95]
   Heterogeneity, not a second mechanism proof.
4. **Mean/median flips (observed).** ATR 1-vs-0 44/528 sign disagreements between
   mean contrast and median contrast — tails can move the mean.
5. **Mass is in 2+ (observed).** Census 2+ = 7.70M / 9.84M raids; later-swing arm_n
   median 1171 vs 82 vs 59. A “repeat-raid” story is mostly the 2+ bag vs a small
   first-raid comparator, not a balanced three-arm experiment.
6. **No economic object (observed).** Occupancy, Sharpe, buy-and-hold, P&L, PSR:
   N/A. Zero-cost. Difference in swing outcomes is not a tradable edge in this file.
7. **Year stability unknown.** Full timestamp year split not run.

## 5. What would make the headline numbers wrong (N7)

| Headline | Probe | Run? |
|---|---|---|
| Live arm means / n | Recompute from `raids.parquet` later-swing filter | **Yes, one cell, 20/20 match.** Full 264-cell mean recompute **not** run (steering). |
| CI excludes 0 | Seed-low-range straddle; L=2/10 sign-class | **Read from live artifact** (not recomputed). strong_move/ATR seed-low straddle 0 among excl-0; duration 4/130. Block flips 18–48/1056. |
| Destroy collapse ≈ 0 | Recompute 2,000 derangements | **Not run.** Copied from live `extra.control`. Fixture plants collapse ≈ 0. |
| Duplicate raid_ids inflate n | Per-cell uniqueness; method pairing | Live `duplicate_raid_ids=0`; one-cell unique; method sets equal. |
| ATR-undefined leaking into ATR/strong_move | Exclude `profile_undefined_reason=ATR_UNDEFINED` | Applied on one-cell; live adapter contract same. Full exclusion census not re-scanned. |
| Wrong population (non-primary as endpoint) | Filter COMPLETED ∧ primary flags | One-cell later n = COMPLETED count in that cell. |
| Duration alias | `duration_ns == swing_duration_ns` | Live 0; one-cell 0. |
| Pooled masking | Per-stratum CI classes | **Done** §2.3. Methods identical; USTEC/XAU weekly LOW are the ATR+ exceptions. |
| Holdout / after TRAIN | timestamp > TRAIN_END | Live after_train_rows=0; TEST not opened. |

## 6. Anomalies & open questions

- 198 null-method EMPTY strata: expected unconfirmed-row partition, not later-swing holes.
- 8-row gap between artifact `raw_bite=1236` and summary-SE recomputed bite 1228: per-seed
  SE vs stored summary SE. Not treated as a fail.
- 25 collapse ratios with \|ratio\|>1: small raw denominators. Disclosed.
- 104 singleton destroy groups (A-16): rare partial-nullness rows; control not voided.
- BREAKOUT_BAR and LEVEL_CLOSE are duplicate state objects for this estimand (same
  raid_ids, identical CI-class counts). They are not two independent tests.
- Full-population swing quantiles, year split, and 264-cell mean-vs-live audit remain
  unrun. Suggested probes on the **existing** emission: (a) year of `endpoint_ts_ns` ×
  band × channel; (b) drop PREVIOUS_1W and re-tabulate ATR CI classes; (c) median-only
  contrast table for ATR.

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- Recommendation: **SUPPORTED**
- Driven by:
  1. strong_move 1-vs-0: 438/528 strata bootstrap 95% CI below 0, **zero** above;
  2. swing_atr 2+-vs-0: 354/528 CI below 0 vs 2 above, median contrast −1.23 ATR;
  3. registered future-destroy collapse near 0 with `destroyed_survives=0` (validity:
     the difference sits in aligned later-swing outcomes, not in the count label).
- Would change if: a full raw recompute showed live `arm_mean`/`n` mismatches; if
  duration were required to differ as a joint primary and the operator treats overlap
  as a veto; if dropping thin PREVIOUS_1W / pooling methods as one object flipped the
  strong_move CI-class majority (unlikely given 0 CI>0).
- Hand-off: final verdict is the operator's. Runnable on this emission without rerun:
  year split; 264-cell mean audit; PREVIOUS_1W sensitivity. Do not treat this as
  family status, tradability, or a TEST/holdout result.

Operator line: **recommended SUPPORTED** — later swings after repeat raids are
usually *smaller in ATR and less often a strong move* than first raids; duration
does not clearly change; this is not a trading result.
