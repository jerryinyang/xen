# Data Analysis: EXP-103

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled **observed** (read from an emitted artifact or recomputed from parquet) or
**inference** (a mechanism reading that is not itself measured). The recommendation in §7
is non-final and applies only to EXP-103 / HYP-003; the operator decides. No TEST or
holdout path was loaded. No 10,000-draw bootstrap and no 2,000-seed destroy were rerun.

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

Vehicle: analysis-only re-read of frozen EXP-100 AMENDMENT-14 TRAIN (264 cells).
Scripts: `python/experiments/EXP-103/analysis_code/interrogate.py` (does not import
`analysis.py`). Per-stratum tight vs non-tight tables: registered
`python/experiments/EXP-103/results/analysis_results.json` (`value_rows` = 3630).
Raw cross-check: one emission cell recomputed from `raids.parquet` + left-joined
`tpo_profiles.parquet`. Destroy / outer-bootstrap numbers: registered
`extra.control` only.

Comparator (binding): non-tight **DEFINED** profiles in the same
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`.
All-defined is disclosure only. Outcome population (design §3): `status==COMPLETED` AND
`primary_attribution` AND `primary_completed` AND joined `profile_status==DEFINED`.

## 1. Integrity gate (blocking)

Only this section has blocking authority.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells `blocking_pass`) | **PASS** | `python/experiments/EXP-103/results/estimand_validation.json`: `blocking_pass=true`, `n_cells=264`, 0/264 cell `blocking_pass` false. SHA256 prefix `1593851873c318f3` = byte-identical EXP-100 copy. |
| Zero-cost (`no_cost_charged`) | **PASS** | 264/264 `no_cost_charged.ok=true`; `cost_model=NO_COST_CHARGED`; `n_non_zero_rows=0`; `cost_bps=0`; directive null. One-cell `run_metadata.json`: `cost_model=NO_COST_CHARGED`, `n_fills=0`. |
| Provenance (gap label ≤ confirmation; later swing after) | **PASS on the recomputed cell** | EURUSD 15m BREAKOUT_BAR 1H PREVIOUS_1D: 2225/2225 outcome rows have `profile_end_ts_ns == confirmation_ts_ns`; 0 rows with `endpoint_ts_ns < confirmation_ts_ns`. Full 264-cell timestamp walk not rerun. |
| Leak tripwire collapsed + non-vacuous (bite = `INTEGRITY_Z × bootstrap_SE_raw`, A-15) | **PASS (registered artifact, not recomputed)** | `extra.control.records` n=2178; `destroyed_survives=false` on 2178; `raw_bite=true` on 404. When the stored flag bites, destroyed mean sits inside `2.8 ×` the disclosed raw SE (400/400). Collapse \|ratio\| on biters: min 3.5e-5, median 0.00539, max 0.0338 (none >0.5). Fixed points = 0. VOID reasons empty. See §1.1. |
| Holdout untouched | **PASS for this analysis + one-cell stamps** | No TEST/holdout path loaded. One-cell `confirmation/endpoint/censor/first_excursion_ts_ns` hits after TRAIN end 2023-11-22T00:00:00Z: 0. Gate fence 264/264 `PINNED`, manifest SHA256 `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0`. |
| Price-primary / event-study object | **PASS as event study** | No P&L estimand. One-cell `n_fills=0`. Emission root `data/nautilus_runs/EXP-100/full/`. Live `source.mode=live`, `rows=9840478`. |
| No experiment-local accounting defs | **PASS** | `python/experiments/EXP-103/code/` does not exist (analysis-only). `interrogate.py` does not define P&L primitives. |
| Raid/profile join | **PASS (live + one cell)** | Live `profile_join`: raid_rows=9840478, profile_rows=9840478, unmatched=0, extra=0, duplicate keys=0. One cell: 13580/13580, unmatched=0. |
| ATR-undefined rows joined, not voided | **PASS (live census)** | `profile_census.undefined_reasons.ATR_UNDEFINED=868` remain in the census; live `void_populations=[]`; unmatched raids=0. |
| Golden T1/T2/T3 (independent replay) | **PASS** | T1: poc=100, va_count=114, val=100, vah=105, gap_span=2, gap_span_va=0.40, tight=true. T2: poc=105, va_count=75, val=101, vah=106, gap_span=3, gap_span_va=0.60, tight=false. T3: gap_span_va=0.50 ⇒ tight=false (strict `<`). Fixture `blocking_pass=true`, 400 rows. |
| `duration_ns == swing_duration_ns` | **PASS on one cell** | 0 mismatches, 0 xor-null. |

### Provenance table (one-cell observed)

| Column | Inputs & timestamps | ≤ confirmation / after-confirm? | Evidence |
|---|---|---|---|
| `tight_gap` / gap geometry | TPO profile on `[profile_start_ts_ns, profile_end_ts_ns]` | Profile ends at confirmation | 2225/2225 `profile_end_ts_ns == confirmation_ts_ns` |
| `swing_*`, `strong_move` | Later opposing swing after confirmation | After confirmation | 0 outcome rows with `endpoint_ts_ns < confirmation_ts_ns` |
| ATR-undefined exclusion | `undefined_reason` / `profile_undefined_reason` | Join retained | This cell: 0 ATR_UNDEFINED; live census 868 rows kept |

### 1.1 Leak tripwire (registered `extra.control` — not recomputed)

A-15: if `|D_raw| > 2.8 × SE_raw[s]` on any seed, require `|m_destroy| ≤ 2.8 × SE_raw[s]` (raw SE, not nested destroyed SE).

| Item | Observed |
|---|---|
| Records | 2178 = 726 strata × {swing_atr, swing_duration_ns, strong_move} |
| Empty-arm notes | 594 `EMPTY_ARM_OR_COMPARATOR - no estimate possible` |
| Movable records | 1584; `destroyed_draws` ∈ {0, 2000} |
| `blocking_pass` | true on 2178 |
| `population_match` | true on 2178 |
| `fixed_points` | 0 (derangement) |
| A-16 singleton groups (`n<2`) | **0** (disclose-only). `n_groups=1584`, min group size **174** |
| VOID reasons | none |
| `raw_bite` | 404 true / 1774 false (250 atr, 106 strong_move, 48 duration) |
| `destroyed_survives` | **0** |
| Biter \|collapse_ratio\| | median 0.00539, max 0.0338 |
| Nested `bootstrap_se_mean_destroyed` | disclosed per seed in the artifact; A-15 compares destroyed mean to **raw** SE |

Four records have stored `raw_bite=true` while `|D_raw| / disclosed_median_SE ≈ 2.788 < 2.8`. Nested seeds show at least one seed still bites. Destroyed means remain far inside the raw bite band. Not a survival.

**Inference:** the registered control is non-vacuous for these mean/proportion contrasts (outcomes move; labels fixed). Collapse near 0 on biting strata means the raw contrast required aligned future outcomes, not gap labels alone.

## 2. Question list

1. Gate completeness? **ANSWERED** §1.
2. Object identity (L-16)? **ANSWERED** §2.1.
3. Per-leg gross distribution / where the money comes from? **UNANSWERED** — no trade/leg/P&L object. Swing-outcome distributions: §2.2–§2.4.
4. Episode anatomy? **UNANSWERED** — no multi-leg episodes.
5. Concentration / tails of swing outcomes? **ANSWERED (one-cell probe)** §2.5; full 9.8M-row tail census not rerun.
6. Per-year totals? **ANSWERED (3-cell probe)** §2.6; full 264-cell year table not rerun. Timestamps exist.
7. Per-stratum structure? **ANSWERED** §2.3–§2.4.
8. Occupancy? **UNANSWERED** — event study, not a time-in-market strategy.
9. Annualised return / Sharpe / maxDD vs buy-and-hold? **UNANSWERED** — no capital path.
10. Exposure / MAE / underwater? **UNANSWERED** — no book.
11. Zero-cost verification? **ANSWERED** §1. Caveat on every money-adjacent table.
12. PSR pairing? **UNANSWERED / N/A** — no mean-trade bps series. `swing_bps` is a price excursion, not a trade return (design §7).
13. Control collapse fraction? **ANSWERED** §1.1 (registered).
14. What would make headlines wrong? **ANSWERED** §5.
15. Sample-size context (N3)? **ANSWERED** — every nonempty stratum kept; empty arms disclosed.
16. Direct comparison (N4)? **ANSWERED** — tight minus non-tight DEFINED, same stratum. All-defined is not used as comparator.

### 2.1 Object identity (observed)

| Claim | Observed |
|---|---|
| Measurement object | Joined raid + same-key TPO profile |
| Trading object | None (no orders/fills/P&L) |
| Match? | YES for the event study as designed; N/A as a trading estimand |
| One-cell fills | 0 |
| Gate reconciliation note | `no leg ledger` |

### 2.2 Census (live `extra.census` / `profile_census`; observed)

| Item | n |
|---:|---:|
| Raid rows (= profile rows) | 9,840,478 |
| DEFINED profiles | 9,794,210 |
| UNDEFINED | 46,268 |
| ATR_UNDEFINED | 868 |
| GAP_UNDEFINED | 45,400 |
| tight (all rows) | 1,439,234 |
| non-tight (all rows) | 8,354,976 |
| COMPLETED | 789,326 |
| CONFIRMED_NON_PRIMARY | 4,316,600 |
| FAILED_BREAKOUT | 4,702,900 |
| RIGHT_CENSORED_EXCURSION | 30,520 |
| RIGHT_CENSORED_CONFIRMATION | 626 |
| RIGHT_CENSORED_ENDPOINT | 506 |

Outcome-population counts from nonempty `value_rows` (sum of `arm_n`+`comparator_n`, each channel): **46,528 tight + 742,516 non-tight = 789,044**.

Count gaps (observed, not repaired):

| Quantity | n | vs 789,044 |
|---|---:|---:|
| Census COMPLETED | 789,326 | +282 |
| Census COMPLETED tight + non-tight (`by_stratum_arm`) | 46,528 + 742,798 = 789,326 | non-tight +282 vs contrast n |
| Live `all_defined_baseline.*.n` | 789,550 | +506 (= RIGHT_CENSORED_ENDPOINT) |

**Inference:** the all-defined disclosure n equals the contrast denominator plus 506 censored-endpoint rows, which design §3 says must not enter the later-swing denominator. Treat 789,550 as disclosure with that contamination risk; do not use it as a comparator.

### 2.3 Cartesian grid, empty arms, method duplication (observed)

| Item | n |
|---|---:|
| `value_rows` | 3630 = 726 strata × 5 channels |
| Nonempty strata (both arms present) | 528 |
| `EMPTY_ARM_OR_COMPARATOR` strata | 198 |
| Empty pattern | 66 per timeframe × {15m,30m,60m}; `confirmation_method=None`, `confirmation_reference=None` (non-completed census pulled into the grid) |

Tight-arm n (nonempty, swing_atr): min **7**, median **61**, max **311**. `arm_n<10`: 8 strata; `<30`: 106; `<100`: 358. Comparator n: min 165, median 1272.5, max 3138. No row dropped for n.

**BREAKOUT_BAR vs LEVEL_CLOSE:** all 264 nonempty pairs have **identical** `(estimate, arm_n, comparator_n)` on swing_atr, duration, and strong_move. One-cell raw check: BB and LC cells both have 13,580 raids and identical outcome means; `tpo_profiles.parquet` SHA16 matches (`5344a8df4e90e7d4`); `raids.parquet` SHA16 differs; `event_log_sha256` matches. **Inference:** confirmation-method is not an independent HYP-003 replication. Effective distinct nonempty strata ≈ 264, not 528. Tables below still list the declared 528 because N3 forbids dropping rows.

### 2.4 Per-stratum contrasts (registered observed means + registered CIs)

CIs and SEs are from the live artifact (5×10,000 cluster bootstrap, L=5 default). They were **not** recomputed. Means/n on the EURUSD 15m BB PREVIOUS_1D cell **were** recomputed from parquet and matched 10/10 channels × sides.

ZERO-COST-DISCLOSURE applies to `swing_bps` / `swing_price` (price units, not P&L).

Headline sign / interval counts (528 nonempty strata):

| Channel | neg | pos | CI below 0 | CI above 0 | CI overlaps 0 | empty |
|---|---:|---:|---:|---:|---:|---:|
| swing_atr (primary) | 504 | 24 | 344 | 0 | 184 | 198 |
| swing_duration_ns (primary) | 332 | 196 | 90 | 2 | 436 | 198 |
| strong_move (unpaired proportion) | 146 | 382 | 20 | 158 | 350 | 198 |
| swing_bps (secondary) | 502 | 26 | 336 | 0 | 192 | 198 |
| swing_price (secondary) | 502 | 26 | 336 | 0 | 192 | 198 |

Median contrast signs (secondary): swing_atr 504 neg / 24 pos (same as means); duration 206 neg / 130 pos / 192 zero.

Disclosure-only size-weighted means (not a finding): tight swing_atr 2.846 vs non-tight 3.738, contrast **−0.891 ATR** (n=46528 / 742516). Duration −0.73 hours (tight 10.29 h vs 11.02 h).

#### swing_atr by layer (nonempty; registered CI)

| Layer | value | n strata | pos | neg | CI below 0 | overlap 0 | tight n | non-tight n |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| symbol | EURUSD | 176 | 2 | 174 | 130 | 46 | 15546 | 244798 |
| symbol | USTEC | 176 | 4 | 172 | 118 | 58 | 15856 | 258110 |
| symbol | XAUUSD | 176 | 18 | 158 | 96 | 80 | 15126 | 239608 |
| tf | 15m | 132 | 0 | 132 | 110 | 22 | 17394 | 234846 |
| tf | 30m | 132 | 2 | 130 | 76 | 56 | 11658 | 230930 |
| tf | 60m | 264 | 22 | 242 | 158 | 106 | 17476 | 276740 |
| method | BREAKOUT_BAR | 264 | 12 | 252 | 172 | 92 | 23264 | 371258 |
| method | LEVEL_CLOSE | 264 | 12 | 252 | 172 | 92 | 23264 | 371258 |
| ref | 1H | 396 | 10 | 386 | 272 | 124 | 41836 | 671910 |
| ref | 4H | 132 | 14 | 118 | 72 | 60 | 4692 | 70606 |
| side | HIGH | 264 | 12 | 252 | 186 | 78 | 23284 | 362526 |
| side | LOW | 264 | 12 | 252 | 158 | 106 | 23244 | 379990 |

Config layer (swing_atr): every config is majority negative. CI-below-0 ranges from 22/48 (PREVIOUS_1D, PREVIOUS_AMERICA) to 42/48 (PREVIOUS_1H, ROLLING_7).

Duration: 436/528 intervals overlap 0. strong_move: 158/528 intervals above 0 (tight higher strong_move rate), 350 overlap, 20 below.

One-cell raw vs live (EURUSD 15m BB 1H PREVIOUS_1D) — observed match:

| Side | channel | tight n | non-tight n | contrast | registered 95% CI | match |
|---|---|---:|---:|---:|---|---|
| LOW | swing_atr | 59 | 1165 | −1.825 | [−2.383, −1.244] | yes |
| LOW | duration_ns | 59 | 1165 | −6.075e12 | overlaps 0 | yes |
| LOW | strong_move | 59 | 1165 | +0.038 | overlaps 0 | yes |
| LOW | swing_bps | 59 | 1165 | −12.87 | [−16.86, −8.66] | yes |
| HIGH | swing_atr | 54 | 947 | −0.969 | [−1.740, −0.141] | yes |
| HIGH | duration_ns | 54 | 947 | +1.710e13 | overlaps 0 | yes |
| HIGH | strong_move | 54 | 947 | +0.109 | [+0.029, +0.178] | yes |

Largest |swing_atr| registered contrasts (each number appears twice: BB and LC):

| Stratum | tight n | non-tight n | tight mean | non-tight mean | contrast | CI |
|---|---:|---:|---:|---:|---:|---|
| USTEC 15m PREVIOUS_1W LOW | 26 | 513 | 1.725 | 5.124 | −3.400 | [−4.292, −2.708] |
| USTEC 15m PREVIOUS_1D LOW | 50 | 1214 | 2.526 | 4.809 | −2.283 | [−3.154, −1.306] |
| USTEC 15m ROLLING_7 HIGH | 268 | 2867 | 3.057 | 5.331 | −2.273 | [−2.810, −1.703] |

CI hygiene (registered, swing_atr): 6/344 CI-below-0 strata have at least one of 5 seeds overlapping 0 (seed-fragile; 3 unique after BB/LC clone). Block-length L=2/5/10: 18/528 sign(`ci_low`) changes (9 unique clones). Default L=5 used in the headline table.

### 2.5 Concentration / tails (one-cell probe only)

EURUSD 15m BB PREVIOUS_1D completed-primary DEFINED:

| Arm | n | mean ATR | median | q95 | q99 | top-1 share of sum | top-5 share | mean without top 5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| tight | 113 | 3.328 | 2.681 | 8.47 | 12.36 | 4.82% | 15.97% | 2.926 |
| non-tight | 2112 | 4.734 | 3.427 | 13.70 | 21.95 | 0.42% | 1.67% | 4.666 |

**Inference:** the tight arm is small-n and more tail-heavy as a *share of its own sum*. Removing the top 5 tight swings still leaves mean 2.93 < non-tight 4.67. Not a single-outlier story on this cell. Full-grid tail census **UNANSWERED**.

### 2.6 Year split (3-cell probe; confirmation_ts_ns)

swing_atr tight−non-tight, same outcome filter. All nine year-cells are negative. Tight n per year is small (18–51).

| Cell | 2021 | 2022 | 2023 |
|---|---|---|---|
| EURUSD 15m BB PREVIOUS_1D | −1.815 (25/426) | −0.533 (48/867) | −2.128 (40/819) |
| XAUUSD 15m BB PREVIOUS_1D | −2.776 (22/449) | −1.027 (44/923) | −0.907 (42/799) |
| USTEC 15m BB PREVIOUS_1D | −1.301 (18/524) | −1.126 (51/1033) | −2.872 (40/853) |

Full 264-cell year table **UNANSWERED**.

### 2.7 Profile integrity (computable subset)

Live `integrity_evidence.profiles.reasons=[]`; `va_rows_checked=9794210`; `gap_rows_checked=0` (live table has masks, not per-bin counts; design §5). One-cell defined 13567: conservation fail 0, bin-width fail 0, tight-boundary fail 0, VA-mass threshold fail 0, va_width fail 0.

## 3. Evidence FOR the hypothesis

Hypothesis: tight DEFINED TPO gaps have **different** later-swing outcomes than non-tight DEFINED gaps in the same stratum.

1. **swing_atr location shift, same direction in almost every declared slice (observed).** 504/528 nonempty strata have tight mean ATR < non-tight mean. 344/528 registered bootstrap 95% CIs lie entirely below 0; **0** lie entirely above 0. All three symbols, all three timeframes, both sides, both refs, all 11 configs are majority-negative. 15m: 132/132 negative point estimates, 110 CI below 0.
2. **Secondary price units agree (observed, zero-cost).** swing_bps and swing_price: 502/528 negative; 336 CIs below 0; 0 above 0.
3. **Medians agree with means on ATR (observed).** 504 negative median contrasts — not a mean-only tail artifact at the sign level.
4. **Raw cell recomputation matches the registered means (observed).** 10/10 channel×side estimates on EURUSD 15m BB PREVIOUS_1D, including LOW ATR −1.825 with CI [−2.383, −1.244].
5. **Year probe does not isolate the ATR gap to one calendar year (observed, 3 cells).** Nine year-blocks all negative.
6. **Registered future-destroy collapses biting ATR contrasts (observed from artifact).** 250 ATR records bite; 0 survive; biter |collapse| median 0.005. **Inference:** the ATR contrast is carried by aligned future outcomes, not by shuffling-invariant labels.
7. **strong_move differs in the opposite direction (observed).** 382/528 positive point estimates; 158 CIs above 0 vs 20 below. Tight raids are more often flagged `strong_move` even while mean ATR is smaller — a second distributional difference, not a copy of the ATR sign.

## 4. Evidence AGAINST the hypothesis

1. **The second primary channel does not separate (observed).** swing_duration_ns: 436/528 CIs overlap 0; only 90 below and 2 above. Point signs mix (332 neg / 196 pos). Design §3 names duration co-primary with ATR. A “later-swing outcome” that is only a shorter ATR path, not a different duration, is a narrower claim than HYP-003 as written.
2. **184/528 ATR intervals still overlap 0 (observed).** Majority-negative point estimates are not the same as interval-separated strata. XAUUSD overlap 80/176; 60m overlap 106/264; PREVIOUS_1D overlap 26/48. Small tight n (median 61; 106 strata `arm_n<30`) widens intervals — reported as width, not hidden.
3. **Confirmation-method duplication (observed).** 264/264 BB/LC pairs are numerically identical on the HYP-003 contrasts. Counting 528 strata double-counts one contrast. This inflates “how many strata agree.”
4. **Tight is the rare arm (observed).** 46,528 vs 742,516. A label that selects ~6% of completed-primary DEFINED raids can differ because it selects a different excursion-to-confirm geometry (smaller VA / shorter path), not because a later swing *responds* to a tight gap. **Inference / confounding.**
5. **24 ATR strata have the opposite sign (observed).** 18 of them are XAUUSD. Heterogeneity exists; pooled −0.891 ATR is disclosure only.
6. **strong_move vs ATR disagreement (observed).** If “different” is supposed to be one mechanism (concentrated gap → continued displacement), a *smaller* mean ATR plus a *higher* strong_move rate is an internally mixed pattern. 350/528 strong_move CIs overlap 0.
7. **CI fragility on a minority of ATR reads (registered).** 6 seed-overlap cases among CI-below-0; 18 L=2/5/10 sign changes. Not the bulk, but those rows are not robust to the predeclared sensitivity knobs.
8. **All-defined n does not match the outcome population (observed).** 789,550 vs 789,044. Using all-defined as if it were the outcome census would be wrong (and the design already forbids it as comparator).
9. **No trading object (observed).** Different swing *descriptions* are not an edge. Occupancy, Sharpe, buy-and-hold, PSR: N/A.

## 5. What would make the headline numbers wrong (N7)

| Headline | Falsifying probe | Run? |
|---|---|---|
| Tight mean ATR < non-tight | Recompute means from left-joined `raids.parquet` | **Yes, one cell, 10/10 match.** Full 264-cell mean recompute not rerun (steered to JSON + one cell). |
| 344 ATR CIs below 0 | Rerun 5×10k cluster bootstrap | **Not rerun** (contract). Seed/L-sensitivity read from artifact instead. |
| Destroy collapse | Rerun 2,000 derangements | **Not rerun.** Numbers labelled registered. |
| Join dropped ATR-undefined / failed rows | Left join + unmatched counts | Live unmatched=0; ATR_UNDEFINED=868 still in census; one-cell unmatched=0. |
| `duration_ns` alias broken | Row-wise equality | One-cell 0 mismatches. |
| Wrong comparator (all-defined or other adaptive arm) | Check `comparator=false` on all 3630 rows | Observed: arm=true, comparator=false on all value_rows. |
| TRAIN/holdout bleed | Timestamp > 2023-11-22 | One-cell 0; no holdout files opened. |
| BB and LC as independent corroboration | Hash/mean compare | **They are not independent** (§2.3). |
| Tight difference is one year / one tail | Year probe; drop top-5 | 3-cell years all negative; one-cell mean survives drop-top-5. Full grid not run. |

## 6. Anomalies & open questions

- **BB/LC clone.** Profiles and event-log hashes match on the sampled pair; raid bytes differ; HYP-003 estimates are identical on all 264 pairs. Operator probe: is confirmation-method a no-op for TPO gap labels and later swings in this emission?
- **all_defined n = contrast n + 506 RCE.** Likely includes `RIGHT_CENSORED_ENDPOINT`. Probe: rebuild the disclosure baseline under design §3 only.
- **COMPLETED 789,326 vs contrast 789,044 (+282).** Probe: which 282 completed rows lack a usable tight/non-tight outcome (undefined profile vs null swing)?
- **Full-grid year and tail tables** not rebuilt from 9.8M rows in this pass.
- **Gap mass ≥30%** not recomputable on live masks (`gap_rows_checked=0`).
- **ATR-undefined max-excursion defect** from EXP-100 remains scoped to 868 rows; those rows are excluded from ATR/`strong_move` interpretation and were not voided from the join.
- Suggested probes that do **not** need a new emission: (a) drop LC clones and re-read 264 unique strata; (b) split ATR contrast by `va_width` / `gap_span_atr` bins to test scale confounding; (c) rebuild all-defined under §3; (d) year table from `confirmation_ts_ns` on the existing parquets.

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: INCONCLUSIVE**
- **Driven by:**
  1. Mean ATR later-swings are smaller on tight DEFINED gaps than on same-stratum non-tight DEFINED gaps in 504/528 strata, with 344 registered CIs entirely below 0, and the registered destroy collapses that contrast (median |collapse| ≈ 0.005).
  2. The other primary channel — swing duration — mostly does not separate (436/528 CIs overlap 0), so the declared later-swing *pair* does not jointly move.
  3. BREAKOUT_BAR and LEVEL_CLOSE are duplicate HYP-003 contrasts (264/264), so stratum counts overstate independent agreement; tight n is ~6% of the outcome population (confounding / selection remains open).
- **Would change if:** a full-parquet recompute of the 264 unique (non-cloned) strata still showed ATR CIs below 0 *and* duration separated in the same direction; or a `va_width`-matched comparison erased the ATR gap (that would push toward no remaining difference). A trading/P&L read would not change this event-study recommendation.
- **Hand-off:** final verdict is the operator’s. Runnable on the existing emission: drop LC clones; `va_width`-matched ATR contrast; year table; rebuild all-defined under §3. Do not treat this as a family or tradability decision.

No row in §§1–6 is tagged SUPPORTED / WASH / CONTRADICTED. Those words appear only in this operator-facing recommendation.
