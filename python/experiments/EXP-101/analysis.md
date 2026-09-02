# Data Analysis: EXP-101

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled **observed** (read from an emitted artifact or recomputed from `raids.parquet`)
or **inference** (a mechanism reading that is not itself measured). The recommendation in
§7 is non-final and applies only to EXP-101 / HYP-001. No TEST, holdout, EXP-100 rerun, or
family-status change.

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

**N2–N11.** N2: object is a level-linked raid and later confirmed swing; no trade/fill/P&L.
N3/N10: no row dropped for n. N4: each arm vs its fixed same-stratum comparator only
(Family A `PREVIOUS_1H`, Family B `PREVIOUS_ASIA`, Family C `ROLLING_7`). N5: pooled figures
are disclosure. N6/N6b: only thresholded inferential statement is the future-destroy
integrity bite `INTEGRITY_Z=2.8 × bootstrap_SE_raw` (AMENDMENT-15). N7: §5. N8: no TEST/
holdout interpretation. N9: zero-cost as above. N11: no machine row labels. PSR is N/A
(no mean-trade/leg bps series).

Destroy / 10k-bootstrap numbers are **copied from**
`python/experiments/EXP-101/results/analysis_results.json` extra.control / value_rows;
they were **not recomputed**. Independent recomputes: means, medians, counts on two raw
cell-groups via `python/experiments/EXP-101/analysis_code/interrogate.py`.

## 1. Integrity gate (blocking)

Only this section has blocking authority.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells `blocking_pass`) | **PASS** | `python/experiments/EXP-100/results/estimand_validation.json`: `blocking_pass=true`, `n_cells=264`, 0 cell `blocking_pass=false`. EXP-101..104 copies sha256 prefix `1593851873c318f3` (byte-identical to EXP-100). |
| Zero-cost (`no_cost_charged`) | **PASS** | 264/264 `no_cost_charged.ok=true`; `cost_model=NO_COST_CHARGED`, `cost_bps=0.0`, directive `null`; 264/264 `run_metadata.json` `cost_model=NO_COST_CHARGED`; `n_fills` sum 0. |
| Provenance (verdict-bearing columns ≤ t-1) | **PASS for timestamps on sampled cells; engine internals not re-derived** | See provenance table. Two cell-groups: 0 chronology inversions on completed-primary rows; all inspected timestamps inside TRAIN `2021-06-02T00:01Z`–`2023-11-22T00:00Z`. No orders/fills. L-01 `rct[di]` N/A (no trade path). |
| Leak tripwire collapsed + non-vacuous (A-15 bite = `INTEGRITY_Z × bootstrap_SE_raw`) | **PASS (registered live artifact, not recomputed)** | `extra.control`: 1584 records, `blocking_pass` all true, `destroyed_survives` all false, `fixed_points=0`, `void_populations=[]`. Raw bite 260/1584; among those, 0 fail `abs(m_destroy) > 2.8 × SE_raw`. Collapse \|mean_destroyed/raw\| on bite: min 5.73e-6, median 0.00176, max 0.0159. Nested destroyed SE / raw SE ≈ 0.011–0.026 (A-15: compare destroyed mean to **raw** SE). Fixture `results/fixture_integrity.json` `blocking_pass=true` (24/24 planted contrasts bite raw and do not survive). |
| A-16 singleton destroy groups | **disclosed, not voiding** | 64 control records have a size-1 group (all `swing_duration_ns`); example EURUSD 30m BREAKOUT_BAR 1H LOW `PREVIOUS_4H`: `group_sizes=[20829,1]`, `moved_rows=20829`, `fixed_points=0`, `reasons=[]`, `blocking_pass=true`. Control does not void (`VOID_NO_MOVABLE_ROWS` / `VOID_NO_CHANGED_VALUE` absent). |
| Holdout untouched | **PASS** | Live `source.root` = `data/nautilus_runs/EXP-100/full` only. Sampled cell-groups: 0 timestamps after TRAIN end on creation/excursion/confirmation/endpoint/censor. No TEST/holdout path loaded. |
| Price-primary (engine emission under fence) | **PASS as event-study emission** | 264 cells, Nautilus `1.230.0`, `emission_contract_version=nautilus-emission-v1`, `one_backtest_node=true`, `n_fills=0`. Not a trading strategy. |
| No experiment-local accounting defs | **PASS** | No `python/experiments/EXP-101/code/`. Analyst scripts under `analysis_code/` only; `analysis.py` was not imported. |

**Live integrity:** `python/experiments/EXP-101/results/analysis_results.json` `integrity.blocking_pass=true`, `reasons=[]`, `value_rows=2640`.

### Provenance table

| Column | Inputs & timestamps | ≤ t-1 / causal fence? | Evidence |
|---|---|---|---|
| `config` / `source_configuration` | cell identity, frozen at emission | yes (label, not outcome) | `run_metadata.json` `run_config.cell.level_config`; raids `config` |
| `status`, `primary_attribution`, `primary_completed` | confirmation/endpoint vs TRAIN end | sampled completed-primary: `level_creation ≤ first_excursion ≤ confirmation ≤ endpoint`; 0 inversions | two cell-groups, `interrogate.py` |
| `swing_atr`, `strong_move` | post-confirmation path; ATR-undefined excluded from interpretation | outcome after confirmation; 112 ATR_UNDEFINED in method-not-null census excluded from these channels | design §1/§3; census `atr_undefined` |
| `swing_duration_ns` / `duration_ns` | confirmation→opposing reference or TRAIN censor | alias equal on sampled files (0 mismatch, 0 xor-null) | two cell-groups |
| `swing_price`, `swing_bps` | source-field summaries, not tripwire estimands | same completed-primary population | design §3 |

## 2. Question list

1. Gate completeness / zero-cost? **ANSWERED** §1.
2. Object identity (raid+later swing, not a trade)? **ANSWERED** §2.1.
3. Per-leg P&L / episode anatomy / occupancy / Sharpe / buy-and-hold / exposure? **UNANSWERED — N/A** (event study, `n_fills=0`, no P&L estimand).
4. PSR pairing on a mean-trade bps series? **UNANSWERED — N/A** (design §6; `swing_bps` is a source summary, not a trade).
5. Census: all rows, statuses, empty arms? **ANSWERED** §2.1.
6. Duration alias `swing_duration_ns == duration_ns`? **ANSWERED** on two cell-groups (0 mismatch).
7. ATR_UNDEFINED exclusion? **ANSWERED** §2.1.
8. Direct comparator (N4) per family? **ANSWERED** §2.2–2.3.
9. Per-stratum structure vs pooled mask? **ANSWERED** §2.2 (BB/LC identity disclosed).
10. Mean vs median; tails/concentration of swing outcomes? **ANSWERED** §2.4.
11. Year split? **ANSWERED on two cell-groups only** §2.5; full 264-cell year split **UNANSWERED** (timestamps exist; full parquet census not rerun).
12. Leak tripwire collapse fraction, A-15 raw-SE bite, A-16 singletons, VOID reasons? **ANSWERED** §1 from live `extra.control` (not recomputed).
13. Independent recompute of observed means/n vs live `raw_estimate` / n? **ANSWERED** §2.6 (160 live rows, 0 mismatches). Full 264-cell raw recompute **UNANSWERED** (orchestrator: do not wait on full scan).
14. What would make headlines wrong? **ANSWERED** §5.

### 2.1 Identity, census, empty arms

**Observed object.** Completed-primary raids:
`status==COMPLETED AND primary_attribution==true AND primary_completed==true`.
264 cells; live attestation `rows=9,840,478` matches config-sum in `extra.census.config`.

**Status (live census, all rows):**

| status | n |
|---:|---:|
| FAILED_BREAKOUT | 4,702,900 |
| CONFIRMED_NON_PRIMARY | 4,316,600 |
| COMPLETED | 789,326 |
| RIGHT_CENSORED_EXCURSION | 30,520 |
| RIGHT_CENSORED_CONFIRMATION | 626 |
| RIGHT_CENSORED_ENDPOINT | 506 |

Outcome denominator = 789,326 COMPLETED. Method-not-null census also carries 506 endpoint-censored primaries (not in outcome). Failed / non-primary / excursion- and confirmation-censored rows have `confirmation_method=null` in this emission; they form 18 incomplete strata (`symbol × timeframe × side` with method/ref null) → **720** `EMPTY_ARM_OR_COMPARATOR` value_rows (18×8×5). Those empty arms are non-completed raids, not missing completed configs.

**Among 48 fully named strata (method+ref set): 0 empty completed arms.** Primary-channel `arm_n` min 174 (`ROLLING_252`) / 206 (`PREVIOUS_1W`); comparators min 519.

**ATR_UNDEFINED:** 868 census-tagged rows overall; **112** in method-not-null (primary) census — EURUSD 36, USTEC 28, XAUUSD 48 — concentrated on `PREVIOUS_1H` (58), `ROLLING_7` (26), `PREVIOUS_ASIA` (16), `PREVIOUS_4H` (12). These 112 are excluded from `swing_atr` / `strong_move` interpretation (binding EXP-100 decision). Count sits in census; live value_rows do not print a per-row excluded field.

**Config mass (all raids, disclosure):** `ROLLING_7` 2,433,606; `PREVIOUS_1H` 1,935,994; `ROLLING_14` 1,740,190; `ROLLING_22` 1,372,976; `PREVIOUS_4H` 723,758; `ROLLING_252` 373,824; `PREVIOUS_ASIA` 328,066; `PREVIOUS_EUROPE` 303,722; `PREVIOUS_AMERICA` 289,434; `PREVIOUS_1D` 248,292; `PREVIOUS_1W` 90,616.

**Completed-primary n summed over 48 strata (swing_atr channel = finite ATR):**

| arm | arm_n sum | comparator | cmp_n sum |
|---|---:|---|---:|
| PREVIOUS_4H | 90,252 | PREVIOUS_1H | 113,428 |
| PREVIOUS_1D | 49,520 | PREVIOUS_1H | 113,428 |
| PREVIOUS_1W | 21,082 | PREVIOUS_1H | 113,428 |
| PREVIOUS_EUROPE | 57,330 | PREVIOUS_ASIA | 57,970 |
| PREVIOUS_AMERICA | 54,962 | PREVIOUS_ASIA | 57,970 |
| ROLLING_14 | 104,352 | ROLLING_7 | 114,156 |
| ROLLING_22 | 93,544 | ROLLING_7 | 114,156 |
| ROLLING_252 | 32,618 | ROLLING_7 | 114,156 |

**BB vs LC identity (observed).** All 576 primary (symbol,tf,ref,side,arm,channel) pairs have identical `estimate` and `arm_n` for `BREAKOUT_BAR` vs `LEVEL_CLOSE`. Registered N=48 strata is two copies of 24 physical grids. Tables below count registered strata; they are **not** 48 independent replications.

Fills/orders: 0 (metadata 264/264 + sample `fills.parquet`).

### 2.2 Per-stratum contrast counts (registered live intervals)

48 named strata × 8 contrasts × 3 primary channels = **1152** rows; 0 empty. Interval = registered 5-seed × 10k cluster bootstrap, default L=5, independent arms. Phrase: **bootstrap 95% CI excludes zero** where `excl0`. Destroy numbers not used as value thresholds.

| Family | Channel | n | CI excl. 0 | + | − | overlap 0 | median estimate |
|---|---|---:|---:|---:|---:|---:|---:|
| A (vs 1H) | swing_atr | 144 | 20 | 0 | 20 | 124 | −0.105 ATR |
| A | swing_duration_ns | 144 | 12 | 12 | 0 | 132 | +1.79e12 ns (~0.50 h) |
| A | strong_move | 144 | **144** | 0 | **144** | 0 | −0.155 |
| B (vs ASIA) | swing_atr | 96 | 6 | 0 | 6 | 90 | −0.080 ATR |
| B | swing_duration_ns | 96 | 2 | 0 | 2 | 94 | −1.36e12 ns |
| B | strong_move | 96 | 2 | 0 | 2 | 94 | −0.0048 |
| C (vs 7) | swing_atr | 144 | 12 | 0 | 12 | 132 | −0.080 ATR |
| C | swing_duration_ns | 144 | 2 | 2 | 0 | 142 | +4.64e11 ns |
| C | strong_move | 144 | **132** | 0 | **132** | 12 | −0.059 |

| Arm | swing_atr excl0 (+/−) | duration excl0 (+/−) | strong_move excl0 (+/−) |
|---|---|---|---|
| PREVIOUS_4H | 0/48 (0/0) | 0/48 | **48/48 (0/48)** |
| PREVIOUS_1D | 0/48 | 4/48 (4/0) | **48/48 (0/48)** |
| PREVIOUS_1W | 20/48 (0/20) | 8/48 (8/0) | **48/48 (0/48)** |
| PREVIOUS_EUROPE | 6/48 (0/6) | 0/48 | 0/48 |
| PREVIOUS_AMERICA | 0/48 | 2/48 (0/2) | 2/48 (0/2) |
| ROLLING_14 | 0/48 | 0/48 | 38/48 (0/38) |
| ROLLING_22 | 0/48 | 0/48 | **48/48 (0/48)** |
| ROLLING_252 | 12/48 (0/12) | 2/48 (2/0) | 46/48 (0/46) |

**By instrument (registered 128 contrasts/channel/symbol):** strong_move excl0 EURUSD 90, XAUUSD 92, USTEC 96 (all negative). swing_atr excl0 EURUSD 6, XAUUSD 10, USTEC 22 (all negative). Duration excl0 almost all XAUUSD (14) plus 2 USTEC.

**Block / seed hygiene (excl0 primary rows):** `sign(ci_low)` changes across L=2/5/10 on **2/332** rows — both USTEC 60m 1H LOW `PREVIOUS_1W` duration, BB and LC copies; L=2 overlaps 0, L=5/10 exclude 0. Seed-low straddles 0 on 2 duration rows (USTEC 15m 1H LOW `PREVIOUS_1W`, BB/LC copies) whose **median** interval still overlaps 0.

**Integrity bite vs value CI.** Raw bite (2.8×SE) is 256 strong_move + 4 swing_atr (2× PREVIOUS_1W atr copies + 2× ROLLING_252 atr copies); 0 duration. Value CIs exclude 0 more often than the integrity bite (as expected: ~2 vs 2.8). All 260 bite rows collapse (median |collapse| 0.00176).

### 2.3 Example named stratum (EURUSD 15m BREAKOUT_BAR 1H LOW)

Raw means match live (this cell-group, 80 rows, 0 mismatch). ZERO-COST-DISCLOSURE on all rows.

| Arm vs cmp | Channel | arm_n/cmp_n | means | estimate | bootstrap 95% CI | excl0 |
|---|---|---:|---|---:|---|---|
| 4H vs 1H | swing_atr | 2304/2885 | 4.431 / 4.413 | +0.018 | [−0.290, +0.326] | no |
| 4H vs 1H | duration_ns | 2304/2885 | 2.931e13 / 2.902e13 | +0.080 h | overlaps 0 | no |
| 4H vs 1H | strong_move | 2304/2885 | 0.849 / 0.902 | **−0.0533** | [−0.0723, −0.0346] | **yes** |
| 1D vs 1H | swing_atr | 1224/2885 | 4.497 / 4.413 | +0.084 | [−0.303, +0.499] | no |
| 1D vs 1H | strong_move | 1224/2885 | 0.777 / 0.902 | **−0.125** | [−0.155, −0.095] | **yes** |
| 1W vs 1H | swing_atr | 524/2885 | 4.327 / 4.413 | −0.086 | [−0.520, +0.408] | no |
| 1W vs 1H | strong_move | 524/2885 | 0.744 / 0.902 | **−0.158** | [−0.207, −0.107] | **yes** |
| EUROPE vs ASIA | swing_atr | 1520/1402 | 4.322 / 4.367 | −0.045 | [−0.418, +0.325] | no |
| EUROPE vs ASIA | strong_move | 1520/1402 | 0.785 / 0.785 | +0.0003 | [−0.036, +0.036] | no |
| AMERICA vs ASIA | swing_atr | 1380/1402 | 4.614 / 4.367 | +0.247 | [−0.150, +0.648] | no |
| AMERICA vs ASIA | strong_move | 1380/1402 | 0.786 / 0.785 | +0.0009 | [−0.033, +0.035] | no |
| 14 vs 7 | swing_atr | 3009/3105 | 4.314 / 4.300 | +0.014 | [−0.279, +0.308] | no |
| 14 vs 7 | strong_move | 3009/3105 | 0.930 / 0.942 | **−0.0128** | [−0.0252, −0.0004] | **yes** |
| 22 vs 7 | strong_move | 2903/3105 | 0.913 / 0.942 | **−0.0298** | [−0.0430, −0.0165] | **yes** |
| 252 vs 7 | swing_atr | 1172/3105 | 4.170 / 4.300 | −0.130 | [−0.511, +0.278] | no |
| 252 vs 7 | strong_move | 1172/3105 | 0.840 / 0.942 | **−0.103** | [−0.131, −0.074] | **yes** |

Duration CIs on this stratum all overlap 0. Median `strong_move` contrast is 0 (boolean medians both 1) — mean-rate contrast is the relevant strong_move read.

### 2.4 Tails / concentration (disclosure)

EURUSD 15m BREAKOUT_BAR 1H **cell-group** completed-primary `swing_atr` (n=41,876, ATR-defined): mean 4.59, median 3.23, std 4.46, q01 0.17, q05 0.65, q95 13.2, q99 22.7; top 1% share of sum 6.05%; top 5% 20.8%. Duration hours: mean 8.30, median 4.0, q99 64. strong_move rate 0.879.

**Inference:** means sit above medians (right tail). Removing the top 1% would still leave most of the ATR mass; this is not a one-trade P&L edge story.

Family A duration: mean-median sign agreement only 46/144 (median contrast often 0). ATR mean-median sign disagreement exists but is secondary to CI overlap.

### 2.5 Year split (two cell-groups only)

EURUSD 15m BREAKOUT_BAR 1H completed-primary confirmation years: 2021 n=8,888; 2022 n=17,196; 2023 n=15,792. **Observed** strong_move arm−comparator diffs, pooled across sides in this group (disclosure, no CI):

| Year | 4H | 1D | 1W | EUR | AM | 14 | 22 | 252 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | −0.061 | −0.134 | −0.094 | +0.030 | +0.021 | −0.008 | −0.026 | −0.115 |
| 2022 | −0.058 | −0.150 | −0.212 | +0.008 | −0.013 | −0.018 | −0.032 | −0.097 |
| 2023 | −0.067 | −0.115 | −0.157 | −0.006 | +0.020 | −0.012 | −0.029 | −0.094 |

Family A/C strong_move diffs stay negative in every year in this group. Family B flips sign. Mean `swing_atr` diffs in the same group **flip sign by year** (e.g. PREVIOUS_1D 2022 −0.30 vs 2023 +0.45). Full-grid year table not computed.

### 2.6 Live vs raw cross-check

| Cell-group | files | raids | completed-primary | live rows checked | mismatches | chrono fail | duration alias fail | holdout after TRAIN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD 15m BB 1H all 11 configs | 11 | 782,068 | 41,876 | 80 | **0** | 0 | 0 | 0 |
| XAUUSD 60m LC 4H all 11 configs | 11 | — | 12,540 | 80 | **0** | 0 | 0 | 0 |

`arm_n`, `comparator_n`, `arm_mean`, `comparator_mean`, `estimate` matched to 1e-9. Remaining 992 primary live rows not independently recomputed from parquet.

## 3. Evidence FOR the hypothesis

Hypothesis: higher-degree / longer-window level configs have **different** later-swing outcomes than lower-degree ones, vs fixed comparators, per stratum.

1. **Family A strong_move (observed).** 144/144 registered strata: bootstrap 95% CI excludes 0, all negative vs `PREVIOUS_1H`. Rates fall as window lengthens (example EURUSD 15m BB 1H LOW: 1H 0.902 → 4H 0.849 → 1D 0.777 → 1W 0.744). `arm_n` 206–3241. BB/LC copies identical, so 72 unique grids, still 72/72. Independent-arm resampling.

2. **Family C strong_move (observed).** 132/144 CI exclude 0, all negative vs `ROLLING_7`. `ROLLING_22` 48/48; `ROLLING_252` 46/48; `ROLLING_14` 38/48. The 12 overlaps are small negative diffs on 4H-reference / `ROLLING_14` (and two `ROLLING_252` EURUSD 4H HIGH copies), intervals still mostly one-sided negative.

3. **Not a label-only artifact (integrity, observed from live control).** On 260 raw-bite rows, destroyed mean collapse fraction median 0.00176, max 0.016; 0 survival vs A-15 raw-SE band; 0 VOID. Fixture plants behave as declared. **Inference:** configuration–outcome association uses the aligned post-confirmation block.

4. **Year stability of the strong_move sign in the EURUSD 15m BB group (observed, disclosure).** Family A and C diffs negative in 2021, 2022, and 2023.

5. **Some ATR/duration separations, same direction story (observed, minority).** `PREVIOUS_1W` mean `swing_atr` CI excludes 0 in 20/48 strata, all negative (HIGH-side EURUSD/USTEC; XAUUSD 30m/60m both sides). `ROLLING_252` atr 12/48, all negative, all USTEC. Family A duration 12/48 exclude 0, all **positive** (longer swings). Consistent with “different,” not with a single larger-excursion story.

## 4. Evidence AGAINST the hypothesis

1. **Family B does not separate (observed).** vs `PREVIOUS_ASIA`: strong_move 2/96 exclude 0 (USTEC 15m 1H LOW `PREVIOUS_AMERICA` BB+LC copies, est −0.040); atr 6/96; duration 2/96. Median strong_move estimate −0.0048. Session “degree” is not a longer window; this family is in the design and is mostly noise.

2. **Primary mean `swing_atr` mostly overlaps 0 (observed).** 346/384 overlap; 38 exclude 0, all negative, concentrated in `PREVIOUS_1W` and USTEC `ROLLING_252`. `PREVIOUS_4H`, `PREVIOUS_1D`, `ROLLING_14`, `ROLLING_22`, `PREVIOUS_AMERICA`: **0/48** atr CIs exclude 0. Example stratum atr +0.018 with CI width ~0.62. **Inference:** mean ATR magnitude is not a general higher-degree shift.

3. **Primary mean duration mostly overlaps 0 (observed).** 368/384 overlap. Median duration contrast often 0. Two excl0 duration rows are block-fragile (L=2 overlaps 0). **Inference:** duration is not a clean separator.

4. **Channel conflict if one wanted “bigger later swings” (inference from observed signs).** Where duration CIs exclude 0 they are positive; where atr CIs exclude 0 they are negative; strong_move (later swing > initial excursion) is lower on longer windows. That is a **composition** change (fewer “strong” moves, not larger mean ATR).

5. **ATR year instability (observed, one cell-group).** Mean atr diffs flip sign across 2021–2023 while strong_move does not. A pooled atr headline would mix regimes.

6. **BB/LC duplication (observed).** Counting 144/144 without noting identical copies overstates independent stratum coverage (24 unique grids × 2 methods).

7. **Right tail / mean≠median (observed).** ATR mean 4.59 vs median 3.23 in the EURUSD 15m group; strong_move median contrast 0 because both arms have median True. Mean-rate is required; a median-only read would hide the strong_move result.

8. **Smaller n on the longest windows (observed, context not a veto).** `PREVIOUS_1W` arm_n sum 21,082 vs comparator 113,428; `ROLLING_252` 32,618 vs 114,156; min cell n 174–206. Those CIs that exclude 0 are still reported with n (N3); several 1W atr exclusions are the ones that separate.

## 5. What would make the headline numbers wrong (N7)

| Headline | Falsification probe | Run? |
|---|---|---|
| Live means/n | Recompute from `raids.parquet` with design outcome filter + ATR-undefined keep-nulls | **Yes**, 2 cell-groups, 160 rows, 0 mismatch. Full 264-cell recompute not run. |
| `swing_duration_ns` | Assert equality with `duration_ns` | **Yes** on those files, 0 mismatch. |
| Empty-arm story | Confirm method-null rows are non-completed | **Yes** (census split; parquet status×method_null). |
| CI excludes 0 | Seed-low range; L=2/5/10 `sign(ci_low)` | **Yes** from live seeds/sensitivities: 2 duration rows seed-straddle; 2 duration rows block-fragile. Strong_move excl0 rows not seed-straddle / not block-fragile. |
| Difference is a count/label artifact | Collapse fraction on CONFIG_CROSSWISE_FUTURE_DESTROY | **Read, not rerun**: bite rows collapse to ~0. |
| A-15 wrong SE | Compare `abs(m_destroy)` to `2.8×SE_raw` vs nested SE | **Read**: 0 fail vs raw SE; nested SE is ~50–90× smaller (would be a false survival test — A-15). |
| A-16 void | Singleton groups void control | **No**: 64 disclosed, `blocking_pass` true, VOID empty. |
| ATR_UNDEFINED silently in means | Exclusion on `profile_undefined_reason==ATR_UNDEFINED` only (null reason kept) | **Yes** in cross-check; 112 primary-census exclusions. Using `!=` would drop null-reason rows (bug, caught). |
| Year artifact | Split confirmation year | **Partial**: one group, strong_move sign stable A/C; atr not. |
| BB/LC as independent strata | Compare estimates | **Yes**: 576/576 primary pairs identical. |
| Holdout leak | Timestamps after 2023-11-22 | **Yes** on two groups: 0. |
| P&L / tradable reading | Any fill/cost path | **N/A / blocked by zero-cost + n_fills=0**. |

## 6. Anomalies & open questions

- `confirmation_method` / `confirmation_reference` are null on failed, non-primary, and most censored rows; only completed (and 506 endpoint-censored) primaries carry method/ref. 720 EMPTY value_rows follow from that encoding, not from missing cells.
- BREAKOUT_BAR and LEVEL_CLOSE are numerically the same later-swing contrasts in this emission (EXP-100 state-object overlap). Treat as one physical grid.
- Integrity bite fires almost only on `strong_move` (256) plus 4 atr rows — not on duration.
- Full 264-cell raw mean recompute and full year×stratum table not produced.
- Occupancy / Sharpe / buy-and-hold / PSR / P&L: N/A.
- Suggested probes on the **existing** emission: (i) strong_move vs initial-excursion distribution (is the rate drop a smaller later swing or a larger first raid?); (ii) drop BB or LC to unduplicate; (iii) year×stratum CIs if a later analysis spends that compute; (iv) do not treat Family B as a longer-window test.

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- Recommendation: **INCONCLUSIVE**
- Driven by:
  1. Family A and C **strong_move** rates are lower than their short baselines in essentially every named stratum (CIs exclude 0; destroy collapses).
  2. Family B (sessions vs ASIA) does **not** show that difference.
  3. Declared primary **means** (`swing_atr`, `swing_duration_ns`) mostly overlap 0; where they do not, ATR is smaller and duration sometimes longer — not one “bigger later swing” mechanism.
- Would change if: the operator takes “different” to mean strong_move-only on previous-period and rolling families (then a SUPPORT reading of that narrower claim); or if a full year×stratum / unduplicated-method pass wiped the strong_move CIs (then toward NOT SUPPORTED).
- Hand-off: final verdict is the operator's. Runnable on the existing emission: unduplicate BB/LC; year×stratum strong_move; excursion-vs-swing decomposition. No family disposition in this record.

Scripts: `python/experiments/EXP-101/analysis_code/interrogate.py` → `analysis_code/interrogation_summary.json`, `analysis_code/live_stratum_summary.json`. Artifacts: `results/analysis_results.json`, `results/estimand_validation.json` (copy of EXP-100), `results/fixture_integrity.json`, `data/nautilus_runs/EXP-100/full/*/raids.parquet`.
