# SPDR-021 — analysis

- **Experiment:** `SPDR-021` — Volatility-adaptive management on a fixed breakout benchmark
- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN only. No TEST or holdout artifact was opened at any point in producing this record.
- **Run stamp:** `20260803T140238Z` (amended rerun; two universes, six cells total across cTrader and crypto)
- **Entry substrate:** a single entry variant, `BREAKOUT`. `E-TOUCH` and `E-CLOSE` do not exist in this experiment and are not reported anywhere below.
- **Date:** 2026-08-04

## 0. Boundary of this record

**This record issues no verdict.** It does not say the hypothesis is supported or refuted, does not
name a winner or a best arm, does not rank arms, does not claim anything is tradable or deployable,
and does not gate `SPDR-022`, `SPDR-023`, the family, or XENA. It reports what the emitted data
says, what it does not say, and the mechanism behind each pattern. Where the word "pass" appears it
is the literal name of an integrity field in an artifact (`blocking_pass`, `row_accounting.pass`),
never a judgement about a measured value.

Every observation below is labelled as either **observed** (a number read directly out of an
emitted artifact) or **inference** (a mechanism reading that explains observed numbers but is not
itself measured).

---

## 1. Cost scope — read this before any number

Reproduced verbatim from the run's own disclosure (`config.json`, `run_summary.json`, both
universes, identical):

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

**Observed.** Spread is not charged at all (`spread_rt_bps: null`). The declared scope is fees and
funding only. Therefore every cost-bearing figure in every artifact understates cost and every
net-of-cost reading derived from them is overstated.

**Observed, and stronger than the declared scope.** In this run the fee/funding component is also
zero, and no cost value survives into the analysis tables:

| Cost evidence | cTrader | crypto |
| --- | --- | --- |
| `positions.parquet` `commissions` — distinct values | `0.00 USD` on all 158,547 positions | `0.00000000 USDT` on all 771,135 positions |
| `per_stratum_estimates.parquet` `partial_cost_mean_bps` non-null | 0 of 903 rows | 0 of 7,547 rows |
| `native_parameter_shared_trades.parquet` `partial_cost_bps` non-null | 0 of 72,477 rows | 0 of 346,894 rows |

**Consequence (inference).** Every estimate in this record should be read as a **gross,
cost-free** difference. It is not a partially-netted figure. Two riders:

- Because the native and device estimands are *paired adaptive-minus-fixed differences*, a per-trade
  cost that both sides pay at the same rate and frequency would largely cancel. It would **not**
  cancel exactly, because arms differ in fill counts and in holding duration (§5, §6) — arms that
  trade more or hold longer would carry more cost than their comparator.
- Any figure below that looks like a captured move (for example the TARGET `realised_capture_bps`
  readings in §6.1) is a gross move with no spread crossed on either entry or exit.

**Known recording defect (observed).** The mirrored disclosure columns on
`per_stratum_estimates.parquet` — `spread_cost_status`, `spread_rt_bps`, `cost_scope` — are null on
all 903 cTrader rows and all 7,547 crypto rows. The disclosure itself is intact in `config.json`
and `run_summary.json` (quoted above); the analysis reads those keys at the top level of the config
while the run nests them under `spread_cost_disclosure`. No estimate is affected. The limitation is
restated here in place of the missing columns.

---

## 2. Integrity, provenance, and reproduction

**Observed.** Both universes report `integrity_selfcheck.json` `blocking_pass: true` with 14 of 14
hard checks `true`, identically in cTrader and crypto:

`causality`, `deterministic_replay`, `entry_parity`, `fence`, `future_shift_changed_mapping`,
`golden_traces`, `management_lattice`, `management_lifecycle`, `native_lattice`,
`no_native_management_cross`, `order_fill_position_reconciliation`, `provenance`, `row_accounting`,
`unique_result_keys`.

| Item | cTrader | crypto |
| --- | --- | --- |
| `estimand_validation.json` `blocking_pass` | `true` over 3 cells | `true` over 25 cells |
| Fence status / last bar | `PINNED`, `2023-11-22 00:00:00` | `PINNED`, `2023-12-18 00:00:00` |
| Fence manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| `row_accounting.json` | `pass: true`; native 1,303,965, management 1,604,880, origins 20,061 | `pass: true`; native 6,640,400, management 8,172,800, origins 102,160 |
| Per-cell reconciliation (`abs_diff_bps` vs `tol_bps` 1.0) | `ok: true` in 3/3 cells (EURUSD `1.46e-11`) | `ok: true` in 25/25 cells |
| Analysis reproduction (`reproduction-hashes.json`) | 13/13 artifacts SHA-256 equal | 13/13 artifacts SHA-256 equal, `all_equal: true` |

**Observed anomaly, non-blocking.** `run_summary.json` carries
`"hard_integrity": "NOT_YET_RUN_TASK_8"` in both universes, while `integrity_selfcheck.json` in the
same directory carries the completed 14-check block with `blocking_pass: true`. The summary field
is a stale placeholder written before the self-check step; the self-check artifact is the one with
the evidence. Flagged so no reader treats the summary string as the integrity state.

**Physicality — how to read it (inference).** `estimand_validation.json` reports occupancy near
1.0 in every cell (EURUSD 0.9997, USTEC 0.9808, XAUUSD 0.9990; crypto 0.933–0.9996), very large
annualised returns (145.9%–468.1% cTrader; up to 39,292.9% on 1000RATSUSDT) and sanity flags on
every cell. These figures are **not** a strategy's performance. They are computed over the
**union of every arm's legs** in a 65-native-arm × 84-management-arm characterisation lattice —
51,204 legs on EURUSD alone over 2.47 years — so occupancy ≈ 1 means *some arm* was in a position
almost always, and the return figure sums many overlapping hypothetical arms with no cost charged
(§1). Read them as a description of the lattice's coverage, not of any tradable object. Two crypto
cells additionally exceed the Sharpe sanity threshold on that same aggregated basis
(1000RATSUSDT 4.00 over 0.070 years, BIGTIMEUSDT 3.90 over 0.182 years) — both are very short
histories and both recur in the concentration findings of §5.3.

---

## 3. Populations and the two lenses — definitions used throughout

Copied from `analysis_summary.json` `count_definitions` (identical in both universes):

| Field | Meaning as emitted |
| --- | --- |
| `eligible_origin_n` | eligible scheduled origins — **includes origins with zero exposure because the arm was occupied** |
| `entry_fill_n` | actual filled entries |
| `close_n` | actual confirmed closes |
| `common_fill_n` | origins filled on **both** comparison sides |
| `common_close_n` | origins closed on **both** comparison sides |
| `effective_origin_blocks` | resampled origin/date blocks behind an origin-level interval |
| `effective_trade_blocks` | resampled paired-trade/date blocks behind a trade-level interval |

The two native lenses answer different questions and are **never merged anywhere in this record**:

- **`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`** — per eligible origin, counting zero-exposure origins.
  Denominator is `eligible_origin_n`; uncertainty uses `effective_origin_blocks`. This lens
  measures *what the whole opportunity schedule produced*, including opportunities an arm could not
  take because it was occupied.
- **`COMMON_CLOSE_TRADE`** — actual fills and closes where **both** sides have real `_entry_ns` and
  `_exit_ns` under the 2026-08-03 amendment. Denominator is `common_close_n`; uncertainty uses
  `effective_trade_blocks`. This lens measures *what happened inside trades both arms actually took*.

Block length is 24 bars in both universes (`analysis_summary.json` `block_bars: 24`); the
interpretation field on both universes is `DESCRIPTIVE_ONLY`.

**Power is context, never a gate.** No row anywhere below is dropped, trimmed, top-N pruned or
labelled because of its count or its MDE. Small-count rows are reported next to their counts.

---

## 4. Where the complete tables live

Selective tables in this document are summaries. **Nothing here replaces the full tables.** Every
row of every table below is present in the canonical artifacts, which are the record:

```
python/experiments/SPDR-021/results/analysis/ctrader/   (13 artifacts)
python/experiments/SPDR-021/results/analysis/crypto/    (13 artifacts)
python/experiments/SPDR-021/results/analysis/reproduction-hashes.json
```

| Artifact | cTrader rows | crypto rows | Complete content |
| --- | ---: | ---: | --- |
| `per_stratum_estimates.parquet` | 903 | 7,547 | every native and management estimate, both lenses, all states, all counts, MDE |
| `native_parameter_origins.parquet` | 729 | 6,011 | origin-lens rows: 65 arms × symbols × 4 states |
| `native_parameter_shared_trades.parquet` | 72,477 | 346,894 | one row per common-filled origin per adaptive arm, with both sides' fill/exit fields |
| `native_parameter_selected_excluded.parquet` | 1,303,965 | 6,640,400 | **every** scheduled origin-arm row, labelled `SELECTED` / `EXCLUDED` |
| `device_target/stop/trail/hold/size.parquet` | 528 / 480 / 270 / 360 / 264 | 4,400 / 4,000 / 2,250 / 3,000 / 2,200 | per-device metric rows, adaptive and fixed comparator side by side |
| `state_sections.parquet` | 1,101 | 9,111 | per-arm episode-state sections with row counts |
| `selection_checks.parquet` | 195 | 1,625 | per-arm selected/excluded diagnostics |
| `controls.parquet` | 962 | 8,002 | `TIME_DERANGEMENT`, `MAGNITUDE_MATCH`, and the two fixed comparator pointer rows |

Row counts reconcile to the run: `native_parameter_selected_excluded.parquet` equals
`row_accounting.json` `native_rows` exactly in both universes (1,303,965 and 6,640,400). No row is
hidden.

---

## 5. Native parameters — breakout threshold and pending expiry

### 5.0 The fixed benchmark (`FIXED_NATIVE_BREAKOUT`), per symbol — full table

Lens `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`, state `ALL`. Estimate is 0 by construction (the arm
compared to itself).

**cTrader — all 3 rows:**

| Symbol | `eligible_origin_n` | `signal_count` | `entry_fill_n` = `close_n` | `fill_rate` | `exposure_per_origin` (bps) | `effective_origin_blocks` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EURUSD | 6,882 | 2,057 | 626 | 0.090962 | +0.067549 | 722 |
| XAUUSD | 6,590 | 1,871 | 570 | 0.086495 | +0.229767 | 691 |
| USTEC | 6,589 | 1,810 | 502 | 0.076188 | −0.001287 | 702 |

**crypto — all 25 rows:**

| Symbol | `eligible_origin_n` | `signal_count` | `entry_fill_n` | `close_n` | `fill_rate` | `exposure_per_origin` (bps) | `effective_origin_blocks` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1000BONKUSDT | 3,093 | 763 | 270 | 270 | 0.087294 | +2.282770 | 346 |
| 1000LUNCUSDT | 4,675 | 1,170 | 340 | 340 | 0.072727 | +0.370316 | 465 |
| 1000PEPEUSDT | 2,377 | 537 | 184 | 184 | 0.077408 | +1.182309 | 230 |
| 1000RATSUSDT | 277 | 75 | 28 | 28 | 0.101083 | +16.669470 | 26 |
| ADAUSDT | 5,435 | 1,495 | 463 | 463 | 0.085189 | +0.395085 | 522 |
| AVAXUSDT | 5,390 | 1,460 | 484 | 484 | 0.089796 | −0.410663 | 521 |
| BIGTIMEUSDT | 721 | 195 | 58 | 58 | 0.080444 | +1.731660 | 67 |
| BLURUSDT | 3,364 | 936 | 279 | 279 | 0.082937 | +0.468003 | 306 |
| BNBUSDT | 5,130 | 1,400 | 444 | 444 | 0.086550 | +0.008426 | 522 |
| BTCUSDT | 6,009 | 1,234 | 406 | 406 | 0.067565 | +0.175802 | 521 |
| DOGEUSDT | 5,451 | 1,359 | 465 | 465 | 0.085305 | +0.091452 | 521 |
| DYDXUSDT | 4,920 | 1,362 | 423 | 423 | 0.085976 | −0.896817 | 521 |
| ETHUSDT | 6,057 | 1,314 | 420 | 420 | 0.069341 | +0.240602 | 521 |
| GALAUSDT | 5,519 | 1,493 | 441 | 441 | 0.079906 | +0.746407 | 521 |
| INJUSDT | 5,246 | 1,582 | 470 | 469 | 0.089592 | −0.084827 | 488 |
| LINKUSDT | 5,677 | 1,609 | 530 | 530 | 0.093359 | +0.091521 | 521 |
| MATICUSDT | 9,814 | 2,815 | 850 | 850 | 0.086611 | +0.247742 | 902 |
| OPUSDT | 5,687 | 1,564 | 527 | 527 | 0.092667 | +0.689851 | 521 |
| ORDIUSDT | 2,359 | 590 | 180 | 180 | 0.076304 | +2.285187 | 210 |
| PYTHUSDT | 306 | 96 | 25 | 25 | 0.081699 | +0.664705 | 27 |
| SEIUSDT | 1,398 | 412 | 112 | 112 | 0.080114 | +1.097745 | 124 |
| SOLUSDT | 5,518 | 1,402 | 438 | 438 | 0.079377 | +1.170343 | 522 |
| TIAUSDT | 487 | 144 | 46 | 46 | 0.094456 | −1.283301 | 45 |
| WLDUSDT | 1,575 | 440 | 149 | 149 | 0.094603 | +0.227477 | 148 |
| XRPUSDT | 5,675 | 1,402 | 438 | 438 | 0.077181 | +0.469564 | 521 |

**Observed.** The fixed breakout converts roughly 7–10% of eligible origins into a fill in both
universes (cTrader 0.0762–0.0910; crypto 0.0676–0.1011). One crypto cell (INJUSDT) has
`close_n` one below `entry_fill_n` — a single censored open position at the fence.

**Observed.** Censoring at the run level is small and disclosed per cell in
`estimand_validation.json` `n_censored_legs`: 48–52 legs per cTrader cell out of 51,204–55,217
legs; 8–114 per crypto cell. Censored legs are retained in the artifacts, not dropped.

### 5.1 Lens 1 — `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`, all 8 components × all arm forms

Scope: state `ALL`; 64 adaptive arm forms per symbol = 8 components × {threshold DIRECT, threshold
REVERSE, expiry DIRECT, expiry REVERSE, and the four orientation pairs DIRECT_DIRECT,
DIRECT_REVERSE, REVERSE_DIRECT, REVERSE_REVERSE on the bounded threshold+expiry combination}.
That is **192 arm-cells on cTrader** (3 symbols) and **1,600 on crypto** (25 symbols). Every one is
in `per_stratum_estimates.parquet` and `native_parameter_origins.parquet`; the per-component
summary below is a view of them, not a substitute.

Whole-lens shape (observed):

| | cTrader (192 cells) | crypto (1,600 cells) |
| --- | --- | --- |
| median \|estimate\| | 0.035069 bps/origin | 0.310153 bps/origin |
| max \|estimate\| | 0.247677 bps/origin | 16.669470 bps/origin |
| median MDE | 0.125697 bps | 0.883311 bps |
| cells with `ci_low > 0` | 2 (1.0%) | 53 (3.3%) |
| cells with `ci_high < 0` | 11 (5.7%) | 57 (3.6%) |
| cells with \|estimate\| > MDE | 8 (4.2%) | 72 (4.5%) |
| `eligible_origin_n` per cell | 6,589–6,882 | 277–9,814 |
| `effective_origin_blocks` per cell | 691–722 | 26–902 |

**Observed.** The typical adaptive-minus-fixed change per eligible origin is a fraction of a basis
point on cTrader and a fraction of a basis point on all large-sample crypto instruments. In both
universes the count of intervals excluding zero on the positive side and on the negative side is
close to symmetric and close to what 95% intervals produce on 192 and 1,600 draws with no effect
(cTrader 2 up / 11 down; crypto 53 up / 57 down). This is a description of the distribution, not a
significance test on the family.

**Component-level view, cTrader, all 64 arm forms** (each row pools the 3 symbols; per-symbol values
are in the artifacts). Median estimate in bps per eligible origin; a parenthesised `n+` / `n−`
counts intervals excluding zero on that side out of the 3 symbol-cells.

| Component | THRESH DIRECT | THRESH REVERSE | EXPIRY DIRECT | EXPIRY REVERSE | D_D | D_R | R_D | R_R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LEVEL_FORECAST_K12 | −0.0224 (1−) | −0.0115 | −0.0168 (1−) | −0.0055 (1−) | −0.0579 (1−) | −0.0202 | −0.0335 | −0.0076 |
| LEVEL_FORECAST_K4 | −0.0352 (1−) | +0.0023 | +0.0020 (1−) | −0.0257 | −0.0365 (1−) | −0.0579 (1−) | +0.0033 | −0.0300 |
| LEVEL_NOW | −0.0301 | +0.0109 | +0.0184 | −0.0134 | −0.0396 | −0.0179 | +0.0365 | −0.0279 |
| RANGE_SCALE | +0.0551 | −0.0085 | −0.0216 | −0.0011 | +0.0153 | +0.0399 | +0.0069 (1−) | −0.0341 |
| SHOCK | −0.0640 | +0.0701 (1+) | −0.0205 | +0.0032 | −0.0569 | −0.0076 | +0.0163 | +0.0237 |
| SWING_GT_CUR | −0.0289 | +0.0522 | −0.0292 | −0.0156 | −0.0655 | −0.0164 | +0.0262 | +0.0328 |
| SWING_SCALE | +0.0542 | −0.0277 | −0.0353 (1−) | +0.0306 | +0.0050 | +0.0446 (1+) | −0.0129 (1−) | −0.0226 |
| TAIL_RISK | +0.0267 | −0.0280 | −0.0189 | −0.0032 | +0.0076 | +0.0239 | −0.0507 | −0.0647 |

Median MDE across these cells is 0.1257 bps, so the great majority of these medians sit inside the
interval width. Full per-symbol estimate / `ci_low` / `ci_high` / `mde` / counts:
`results/analysis/ctrader/per_stratum_estimates.parquet` (filter `arm_class` in
`NATIVE`,`NATIVE_COMBINATION`, `state == 'ALL'`).

**Crypto, all 1,600 arm-cells:** the same 64 arm forms across 25 symbols, complete in
`results/analysis/crypto/per_stratum_estimates.parquet`. Whole-lens shape is in the table above;
concentration is in §5.3.

### 5.2 Lens 2 — `COMMON_CLOSE_TRADE` for native parameters is structurally empty of difference

**Observed, and this is the single most consequential structural fact in the native half of the
experiment.** On every common-filled origin, in both universes, the adaptive arm's recorded trade
is *identical* to the fixed arm's:

| Check on `native_parameter_shared_trades.parquet` | cTrader | crypto |
| --- | --- | --- |
| rows (common-filled origin × adaptive arm) | 72,477 | 346,894 |
| rows with real `_entry_ns` and `_exit_ns` | 72,477 / 72,477 | 346,894 / 346,894 |
| `_entry_ns == fixed_entry_ns` | 72,477 | same pattern |
| `_exit_ns == fixed_exit_ns` | 72,477 | same pattern |
| `paired_outcome_delta_bps` — distinct values | one value: `0.0` | one value: `0.0` |
| distinct `_entry_price` per origin across all arms that share it | 1, on all 1,698 shared origins | — |
| distinct `threshold_atr` per origin across those same arms | up to 7 (range 0.25–1.00) | — |

A worked row from the artifact — one origin, ten different adaptive arms, three different
thresholds, one identical trade:

| `native_arm_id` | `threshold_atr` | `stop_price` | `_entry_price` | `_entry_ns` | `outcome_bps` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_DIRECT` | 0.368997 | 1.05554 | 1.05554 | 1677459780000000000 | 3.78953 |
| `NAT_BREAKOUT_SWING_SCALE_BREAKOUT_THRESHOLD_DIRECT` | 0.326212 | 1.05554 | 1.05554 | 1677459780000000000 | 3.78953 |
| `NAT_BREAKOUT_RANGE_SCALE_PENDING_EXPIRY_DIRECT` | 0.500000 | 1.05554 | 1.05554 | 1677459780000000000 | 3.78953 |
| … 7 further arms, same three columns | 0.326–0.500 | 1.05554 | 1.05554 | same | 3.78953 |

Also observed: the origins appearing in this table number exactly 626 / 570 / 502 on
EURUSD / XAUUSD / USTEC — i.e. exactly the fixed arm's fill counts from §5.0. Every adaptive arm's
common-fill set is a subset of the fixed arm's fills.

**Mechanism (inference, and it is confirmed by the design's own golden trace).** The breakout
threshold in SPDR-021 is an **admission rule on impulse size, not a price offset**. Design golden
trace 1 states it explicitly: with `ATR20=2` and an impulse of exactly 1.0 ATR, the direct
threshold 0.25 and the fixed threshold 0.50 both create the long stop and the reverse threshold
1.00 does not, "because the rule is strict `>`" — and in all admitting cases the buy stop is the
same price, 102. The pending expiry likewise governs only how long the pending order survives; a
fill that occurs inside both expiry windows is the same fill. So on any origin where **both**
sides admit an order, the two orders are the same order and the trade cannot differ.

**Consequence (inference).** For SPDR-021's native parameters, the `COMMON_CLOSE_TRADE` lens
cannot carry information by construction, and everything the native arms do lives in the
occupancy-inclusive origin lens of §5.1 — specifically in *which origins get an order at all*
(`signal_count` and `fill_count` vary widely across arms: cTrader adaptive `fill_count` 253–865
against the fixed 502–626; crypto 0–1,145). This is a property of this experiment's parameter
semantics. It is stated as a limit on what the second lens can answer here, not as a defect in the
data: the table is complete, correct, and reproduces exactly.

**Open question.** Whether the trade-lens degeneracy is entirely the strict-`>` admission semantics
(the golden-trace reading) or whether the shared-trades table additionally mirrors the fixed side's
`stop_price` into the adaptive row cannot be separated from these artifacts alone, because the
table carries only one `stop_price` column per row. The two readings agree on every observable
here. Resolving it needs the per-arm order ledger, not a new run.

### 5.3 Concentration in the native lens

**Observed — cTrader.** All 13 arm-cells whose interval excludes zero, in full:

| Symbol | Component | Parameter | Orientation | Estimate | CI | MDE | `eligible_origin_n` | blocks |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| XAUUSD | LEVEL_FORECAST_K12 | THRESH+EXPIRY | DIRECT_DIRECT | −0.184876 | [−0.360659, −0.030675] | 0.175782 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K4 | THRESH+EXPIRY | DIRECT_DIRECT | −0.180292 | [−0.357268, −0.031051] | 0.176976 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K4 | PENDING_EXPIRY | DIRECT | −0.177430 | [−0.345674, −0.042886] | 0.168244 | 6,590 | 691 |
| XAUUSD | RANGE_SCALE | THRESH+EXPIRY | REVERSE_DIRECT | −0.167820 | [−0.333726, −0.038722] | 0.165905 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K12 | PENDING_EXPIRY | DIRECT | −0.164902 | [−0.329842, −0.022936] | 0.164941 | 6,590 | 691 |
| XAUUSD | SWING_SCALE | THRESH+EXPIRY | REVERSE_DIRECT | −0.164256 | [−0.326571, −0.037181] | 0.162315 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K12 | BREAKOUT_THRESHOLD | DIRECT | −0.157301 | [−0.332822, −0.009656] | 0.175521 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K4 | THRESH+EXPIRY | DIRECT_REVERSE | −0.153434 | [−0.321557, −0.001417] | 0.168123 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K4 | BREAKOUT_THRESHOLD | DIRECT | −0.148960 | [−0.313854, −0.008046] | 0.164894 | 6,590 | 691 |
| XAUUSD | LEVEL_FORECAST_K12 | PENDING_EXPIRY | REVERSE | −0.144804 | [−0.315456, −0.008988] | 0.170652 | 6,590 | 691 |
| XAUUSD | SWING_SCALE | PENDING_EXPIRY | DIRECT | −0.085140 | [−0.160475, −0.014511] | 0.075335 | 6,590 | 691 |
| USTEC | SHOCK | BREAKOUT_THRESHOLD | REVERSE | +0.151336 | [+0.025084, +0.285032] | 0.126253 | 6,589 | 702 |
| USTEC | SWING_SCALE | THRESH+EXPIRY | DIRECT_REVERSE | +0.247677 | [+0.034278, +0.465687] | 0.213399 | 6,589 | 702 |

11 of 13 sit on **one instrument** (XAUUSD) and all 11 are negative; EURUSD contributes none. The
XAUUSD cluster is dominated by the two LEVEL_FORECAST components and by DIRECT-side orientations.
Interpretation of the sign here is bounded: XAUUSD also has the largest fixed
`exposure_per_origin` of the three (+0.229767 bps), so a negative adaptive-minus-fixed change on
XAUUSD is a reduction relative to the largest benchmark, and the effect size (≈0.15–0.18 bps per
origin) is the same order as the cell's own MDE (0.16–0.18).

**Observed — crypto.** 110 of 1,600 arm-cells have an interval excluding zero, and they are heavily
concentrated by instrument:

| Symbol | cells | Symbol | cells | Symbol | cells |
| --- | ---: | --- | ---: | --- | ---: |
| 1000RATSUSDT | 18 | AVAXUSDT | 7 | 1000PEPEUSDT | 2 |
| ORDIUSDT | 14 | SOLUSDT | 6 | BNBUSDT | 2 |
| OPUSDT | 13 | DOGEUSDT | 5 | BTCUSDT | 1 |
| DYDXUSDT | 12 | ETHUSDT | 4 | LINKUSDT | 1 |
| TIAUSDT | 9 | MATICUSDT | 4 | 1000LUNCUSDT | 1 |
| 1000BONKUSDT | 3 | INJUSDT | 3 | PYTHUSDT | 1 |
| XRPUSDT | 2 | BIGTIMEUSDT | 2 | 5 symbols with none | 0 |

By component the 110 spread almost evenly (SWING_SCALE 19, RANGE_SCALE 18, LEVEL_FORECAST_K12 16,
TAIL_RISK 16, LEVEL_FORECAST_K4 13, LEVEL_NOW 10, SWING_GT_CUR 9, SHOCK 9); by orientation likewise
(REVERSE 33, DIRECT 31, DIRECT_REVERSE 15, REVERSE_DIRECT 12, REVERSE_REVERSE 11, DIRECT_DIRECT 8).
No component or orientation family stands apart from the others.

**Observed — a degenerate sub-population, fully explained.** 32 of the 1,600 crypto arm-cells have
`fill_count == 0`: all 8 SWING_SCALE arm forms on each of 1000RATSUSDT, PYTHUSDT, TIAUSDT and
BIGTIMEUSDT. On 1000RATSUSDT all eight report the **identical** estimate −16.669470 with the
identical interval [−37.061395, −0.021409] and MDE 20.391924 on 277 eligible origins / 26 effective
blocks. **Mechanism (inference):** those are exactly the four shortest crypto histories (0.070,
0.073, 0.129 and 0.182 years), the SWING_SCALE component never accumulates enough swing history to
emit a feature there, so no order is ever created, and the arm's estimate collapses to minus the
fixed benchmark's `exposure_per_origin` — which for 1000RATSUSDT is precisely +16.669470 bps
(§5.0). These are "the arm did not trade", not "the arm traded worse". They are retained and
reported, not removed. A further 19 cells have `fill_count` between 1 and 9.

Excluding those four short-history instruments, the largest remaining crypto magnitudes are on
ORDIUSDT (2,359 origins) and DYDXUSDT (4,920 origins) at roughly 1–2.8 bps per origin against MDEs
of the same order. DYDXUSDT is also the one crypto cell whose aggregated ledger total is negative
(−308,323.7 bps, §2), and its 12 interval-excluding cells are all on the positive side — i.e.
adaptive arms differ most from the fixed benchmark on the instrument where the fixed benchmark did
worst. Whether that is a genuine conditional or a regression-to-the-mean artifact of a single
instrument is **unresolved** from these data.

### 5.4 Selected and excluded origins — retained in full

**Observed.** `native_parameter_selected_excluded.parquet` retains every scheduled origin-arm row:

| | cTrader | crypto |
| --- | ---: | ---: |
| total rows | 1,303,965 | 6,640,400 |
| `SELECTED` (state `ORDER_CREATED`) | 326,294 | 1,490,840 |
| `EXCLUDED` — of which state `NO_EVENT` | 839,559 | 4,379,536 |
| `EXCLUDED` — of which state `NO_FEATURE` | 138,112 | 770,024 |
| `SELECTED` `outcome_bps` mean / median / sd | 0.35879 / 0.0 / 14.654 | — |
| `EXCLUDED` `outcome_bps` mean / sd | 0.0 / 0.0 | 0.0 / 0.0 |

**Observed limitation of the selection check.** Because every `EXCLUDED` row carries
`outcome_bps == 0` by construction (no order existed, so there is no outcome), the emitted
`excluded_mean_median_gap` is exactly `0.0` on all 195 cTrader and all 1,625 crypto rows of
`selection_checks.parquet`, and `payoff_scale_ratio` is null on all of them. The check therefore
**cannot** detect outcome-based selection — there is no excluded-but-traded population to compare
against. The one diagnostic that does vary is `sign_share_difference` (cTrader 0.1222–0.1788;
crypto 0.0877–0.3750), which describes how much the long/short mix shifts between an arm's admitted
and non-admitted origins. Crypto `selected_n` ranges 0–3,623 (the zero is the SWING_SCALE
short-history case of §5.3); `excluded_n` ranges 183–8,361.

### 5.5 Episode-state sections — retained in full

**Observed.** `state_sections.parquet` keeps every state for all 145 arms:

| State | cTrader rows | crypto rows | arms |
| --- | ---: | ---: | ---: |
| `NO_EVENT` | 1,924,156 | 10,057,294 | 145 |
| `NO_FEATURE` | 224,090 | 1,242,894 | 77 |
| `ORDER_CREATED` | 760,599 | 3,513,012 | 145 |

`NO_EVENT` and `NO_FEATURE` rows carry `mean_outcome_bps == 0.0` exactly, everywhere. The
row-weighted `ORDER_CREATED` mean is +0.305856 bps (cTrader, per-arm range −3.447985 to +4.356417)
and +1.640368 bps (crypto, per-arm range −610.725219 to +145.357226). The extreme crypto per-arm
values sit on the short-history cells of §5.3. `NO_FEATURE` exists for 77 of 145 arms — the
components that can be undefined early in a history; the fixed arm and the pure-expiry arms have no
`NO_FEATURE` section.

---

## 6. External management devices — individual devices, before any combination

All device estimates use the `COMMON_CLOSE_TRADE` lens against a **declared fixed device**
comparator, never against another adaptive arm. Full tables:
`results/analysis/{ctrader,crypto}/device_{target,stop,trail,hold,size}.parquet`.
Rows in state `NO_EVENT` (roughly half of each device table, with `common_close_n == 0`) are
retained in the artifacts and excluded only from the tallies below, which are state
`ORDER_CREATED`.

Tally convention: `n` = adaptive rows (fixed-comparator self-rows excluded), `ci+` / `ci−` = rows
whose interval excludes zero on each side, medians across those rows.

### 6.1 TARGET

| Metric | Universe | n | ci+ | ci− | median est | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `realised_capture_bps` | cTrader | 57 | 36 | 9 | +0.853885 | 0.651523 | 91 |
| | crypto | 475 | 249 | 59 | +7.749607 | 9.480638 | 42 |
| `missed_excess_bps` | cTrader | 57 | 8 | 22 | −0.390085 | 0.749616 | 91 |
| | crypto | 475 | 45 | 116 | −4.609993 | 13.398677 | 42 |
| `time_to_target` | cTrader | 57 | 22 | 9 | +1.062817 | 15.278492 | 91 |
| | crypto | 475 | 124 | 74 | +0.398684 | 13.041881 | 42 |
| `reach_rate` | cTrader | 57 | 0 | 6 | 0.000000 | 0.000000 | 91 |
| | crypto | 475 | 0 | 48 | 0.000000 | 0.000000 | 42 |

**Observed.** `reach_rate` is **exactly 1.000000** for every pure TARGET arm and every fixed TARGET
comparator, in both universes. It falls below 1 only on the device-combination arms (§6.6).

**Mechanism (inference).** A pure TARGET arm has no competing exit — no stop, no trail, no time
cap. It closes only when the target is reached, so within the closed population the reach rate is 1
by construction, and `common_close_n` counts only origins where **both** the adaptive and the fixed
target were reached. Conditional on both being reached, a farther adaptive target necessarily
captures more. The positive `realised_capture_bps` tallies are therefore largely a
distance-to-magnitude identity on a subset selected for success, not a probability-weighted
improvement. Reading these as captured edge would double-count the selection.

**Observed, supporting that reading.** The extreme values sit on the smallest counts. cTrader
`ADP_SWING_SCALE_TARGET_M0.75` reports +30.001640 bps [+29.069033, +30.934248] on
`common_close_n = 2` / `effective_trade_blocks = 2`; `ADP_SWING_SCALE_TARGET_M1.00` reports
+41.189624 with a zero-width interval on `common_close_n = 1`. Crypto TARGET reaches +4,831.4 bps
in one cell of the M1.50 group whose median `common_close_n` is 17.5. These rows are retained and
reported exactly as emitted; their counts are the caveat.

**Observed, contrary to a pure-artifact reading.** The state-conditioned setting
`STATE_LOW_075_HIGH_150`, which has much larger paired populations (cTrader median
`common_close_n` 160, crypto 61), still shows a consistent positive lean: cTrader 10 of 18 cells
with `ci_low > 0` against 1 negative, median +0.500652 bps against a median MDE of 0.287480; crypto
76 of 144 positive against 5 negative, median +5.025226 bps against MDE 4.663330. Same direction on
both universes, at populations where the two-sample artifact is weaker.

### 6.2 STOP

| Metric | Universe | n | ci+ | ci− | median est | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `loss_severity_bps` | cTrader | 51 | 0 | 23 | −1.297248 | 0.593150 | 83 |
| | crypto | 425 | 13 | 208 | −9.929195 | 9.346159 | 46 |
| `adverse_excursion_bps` | cTrader | 51 | 21 | 6 | +0.914124 | 1.001742 | 83 |
| | crypto | 425 | 177 | 54 | +8.053013 | 15.162157 | 46 |
| `recovery_after_stop_bps` | cTrader | 51 | 3 | 1 | −1.237086 | 3.714725 | 83 |
| | crypto | 425 | 30 | 18 | −3.758283 | 26.846282 | 46 |
| `stop_rate` | cTrader | 51 | 7 | 0 | 0.000000 | 0.014133 | 83 |
| | crypto | 425 | 54 | 0 | 0.000000 | 0.012346 | 46 |

**Observed.** The fixed comparators' own `stop_rate` is 0.982558 / 0.984228 / 0.996795 for
M0.75 / M1.00 / M1.50 on cTrader; adaptive pure-STOP arms sit at 1.000000. The residual comes from
the `FAILSAFE` exit: `exit_reason` strings on pure STOP arms read e.g.
`STOP=0.985714|FAILSAFE=0.014286`.

**Mechanism (inference).** A pure STOP arm has no target and no time cap, so it exits only on the
stop (or the deterministic reduce-only fail-safe mandated by the amendment). Its closed population
is therefore all losses, and a wider adaptive stop mechanically produces a larger loss per closed
trade and a larger adverse excursion. This is the exact mirror of the TARGET pattern in §6.1 and
has the same status: a distance-to-magnitude identity on a subset selected by the exit itself.

**Observed.** Paired populations for pure STOP arms are the smallest in the experiment — crypto
median `common_close_n` of 14 (M1.00) and 8 (M1.50), minimum 1; cTrader minima of 8, 9 and 4 in the
three multiplier groups. **Mechanism (inference):** an arm with no time cap holds the single
position slot until its stop is hit, so it declines most subsequent origins; requiring *both* sides
to fill and close on the same origin then leaves very few paired trades. This is the occupancy cost
of price-only arms, and it is why the origin-level lens exists.

**Observed.** The state-conditioned `STATE_LOW_075_HIGH_150` STOP arms, with larger populations
(cTrader median 142, crypto 78), still lean negative: cTrader 6 of 10 cells `ci_high < 0` with
median −0.517661 against MDE 0.457899; crypto 61 negative against 8 positive, median −3.340784
against MDE 4.329047.

### 6.3 TRAIL

| Metric | Universe | n | ci+ | ci− | median est | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `peak_giveback_bps` | cTrader | 36 | 24 | 2 | +0.895130 | 0.623904 | 120.5 |
| | crypto | 300 | 158 | 6 | +9.480820 | 10.178634 | 48 |
| `favourable_excursion_captured` | cTrader | 36 | 3 | 9 | −0.005515 | 0.040176 | 120.5 |
| | crypto | 300 | 5 | 52 | −0.016991 | 0.071053 | 48 |
| `loss_tail_bps` | cTrader | 36 | 2 | 3 | −0.062817 | 0.224599 | 120.5 |
| | crypto | 300 | 3 | 41 | 0.000000 | 7.371249 | 48 |

**Observed.** The fixed TRAIL comparators capture 0.384307 / 0.437277 / 0.432810 of the favourable
excursion (M0.75 / M1.00 / M1.50, cTrader). Adaptive trails give back **more** peak (24 of 36
cTrader cells and 158 of 300 crypto cells with `ci_low > 0`) while capturing a **slightly smaller**
fraction of the favourable excursion (9 of 36 and 52 of 300 with `ci_high < 0`). The two universes
agree in direction on both metrics.

**Mechanism (inference).** A volatility-scaled trail is on average a wider trail; a wider trail
tolerates more retracement before exiting, which raises giveback, and the extra room does not
convert into a larger captured fraction of the same excursion. `loss_tail_bps` moves little in
cTrader and negative in a minority of crypto cells — the wider trail does not systematically
lengthen the loss tail.

### 6.4 HOLD

| Metric | Universe | n | ci+ | ci− | median est | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `opportunity_duration` (bars) | cTrader | 36 | 27 | 9 | +1.407683 | 0.287213 | 379 |
| | crypto | 300 | 208 | 72 | +1.490074 | 0.433457 | 204.5 |
| `decay_bps` | cTrader | 36 | 31 | 3 | +7.551681 | 2.478637 | 379 |
| | crypto | 300 | 244 | 23 | +53.974476 | 22.529353 | 204.5 |
| `outcome_by_time_bps` | cTrader | 36 | 0 | 10 | −2.127551 | 3.072122 | 379 |
| | crypto | 300 | 5 | 55 | −3.158469 | 28.349272 | 204.5 |
| `holding_efficiency` | cTrader | 36 | 0 | 11 | −3.851834 | 2.186610 | 379 |
| | crypto | 300 | 9 | 84 | −0.913772 | 1.269253 | 204.5 |

**Observed, split by setting (cTrader).** The two HOLD settings move in opposite directions and the
data separates them cleanly:

- `STATE_LOW_4_HIGH_12` (hold longer in the identified state): duration +1.497981 bars with all
  12 of 12 intervals excluding zero on the positive side (MDE 0.287213); decay +10.729973 bps,
  12 of 12 positive; `outcome_by_time_bps` −1.974882 bps, 2 of 12 negative, MDE 3.407212.
- `STATE_SHOCK_2` (hold shorter on shock): duration −0.954586 bars, 3 of 3 intervals negative;
  decay −8.169423 bps, 3 of 3 negative; `outcome_by_time_bps` −0.437001, none excluding zero.

**Observed, crypto.** The same shape, larger: `STATE_LOW_4_HIGH_12` duration +1.490074 bars with
208 of 300 positive; decay +53.974476 bps with 244 positive; `outcome_by_time_bps` median
−3.158469 with 55 of 300 negative against 5 positive; `holding_efficiency` 84 negative against 9
positive. `common_close_n` here is the largest of the price-only devices (median 204.5 crypto,
379 cTrader) because a time-capped arm releases the position slot and is available for the next
origin.

**Mechanism (inference).** Holding longer buys more elapsed time, and the emitted data says the
extra time is spent giving back rather than accruing: duration up, decay up, outcome-per-unit-time
down, holding efficiency down. Holding shorter on shock does the mirror. Both directions are
consistent across the two universes and across the two settings, and both are measured on the
largest paired populations in the device half of the experiment.

### 6.5 SIZE

| Metric | Universe | n | ci+ | ci− | median est | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `risk_dispersion` | cTrader | 30 | 0 | **30** | −4.307154 | 1.760564 | 570 |
| | crypto | 250 | 6 | **204** | −25.481287 | 17.196871 | 420 |
| `tail_loss_bps` | cTrader | 30 | 0 | 22 | −6.000903 | 4.560281 | 570 |
| | crypto | 250 | 0 | 95 | −38.274656 | 63.376482 | 420 |
| `drawdown_bps` | cTrader | 30 | 7 | 0 | +44.303124 | 100.520174 | 570 |
| | crypto | 250 | 43 | 0 | +233.007735 | 637.492640 | 420 |
| `concentration` | cTrader | 30 | 7 | 1 | +0.000880 | 0.003015 | 570 |
| | crypto | 250 | 15 | 11 | +0.002646 | 0.008132 | 420 |

**Observed, and it is the most uniform result in the experiment.** Every one of the 30 cTrader SIZE
cells has `ci_high < 0` on `risk_dispersion` — 30 of 30, across all four settings
(`SCALE_NORMALISED`, `STATE_HALVE_HIGH`, `STATE_LOW_075_HIGH_150_ON_RANGE_SCALE`,
`STATE_LOW_075_HIGH_150_ON_SHOCK`). Crypto reproduces it at 204 of 250 negative against 6 positive.
`tail_loss_bps` moves the same way (22 of 30; 95 of 250, with zero cells on the other side).
`drawdown_bps` improves in sign but its MDE (100.5 cTrader, 637.5 crypto) exceeds the median
estimate, so most of those cells do not separate from zero.

**Observed.** The paired outcome estimate for **every** SIZE arm in `per_stratum_estimates.parquet`
is exactly `0.000000` with `ci_low = ci_high = mde = 0.000000` — all 30 cTrader and all 250 crypto
rows, all four settings.

**Mechanism (inference).** `outcome_bps` is a per-unit return, so scaling risk cannot change it:
the SIZE device is invisible to the outcome estimand by construction and its entire information
content sits in the dispersion / tail / drawdown / concentration metrics of `device_size.parquet`.
The exact zeros are the expected reading, not a missing measurement. Under the 2026-08-03 amendment
SIZE closes on the fixed one-H1-bar strategy hold, which is why it has the largest paired
populations of any device (cTrader 570 of the fixed arm's 502–626 fills; crypto median 420).

### 6.6 Device combinations — reported after the individual devices

| Arm | Universe | cells | median outcome est | ci+ | ci− | median MDE | median `common_close_n` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `TARGET+STOP` M1.00 | cTrader | 3 | −6.446757 | 0 | 3 | 1.300692 | 194 |
| | crypto | 24 | −52.844554 | 0 | 24 | 15.920045 | 70.5 |
| `TARGET+STOP+HOLD` M1.00 | cTrader | 3 | −6.495819 | 0 | 3 | 1.320034 | 194 |
| | crypto | 24 | −53.127285 | 0 | 24 | 15.920045 | 70.5 |
| `TRAIL+HOLD` M1.00 | cTrader | 3 | −4.288286 | 0 | 3 | 2.181267 | 250 |
| | crypto | 24 | −66.716554 | 0 | 21 | 40.083175 | 70.5 |

**Observed.** These are the only arms where the exit is genuinely contested. `reach_rate` for
`TARGET+STOP` is 0.512262 against the fixed pure-target comparator's 1.000000 (all 6 cTrader cells
`ci_high < 0`), and `stop_rate` is 0.479564 against the pure-target comparator's 0.000000 (all 6
cells `ci_low > 0`). `exit_reason` strings confirm the split directly, e.g.
`STOP=0.498413|TARGET=0.484127|FAILSAFE=0.011111|HOLD=0.006349`.

**Mechanism (inference).** The negative combination estimates are, in the first instance, the
comparator's construction rather than a claim about combining devices: a `TARGET+STOP` arm is being
differenced against `FIXED_TARGET_M1.00`, whose closed population is target-hits only. Adding a stop
removes roughly half of those from the target branch and books them as losses instead, so the
difference must be negative. This is the same conditioning identity as §6.1/§6.2 seen from the
other side. It is **not** evidence that combination is worse than the individual devices — the two
populations are not the same population. `TARGET+STOP` and `TARGET+STOP+HOLD` are near-identical in
every cell (cTrader −6.446757 vs −6.495819), which is consistent with the 1-bar hold rarely binding
once a target and stop are both present.

**Observed, unresolved.** `MANAGEMENT_COMPONENT_COMBINATION` arms (a component's state applied on
top of another component's state) show the largest positive TARGET and TRAIL readings in crypto
(`TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE`: 52 of 81 cells with `ci_low > 0`, median
+25.010825 bps, median `common_close_n` 36; `TRAIL | ..._ON_RANGE_SCALE`: 20 of 59 positive, median
+26.029810, median `common_close_n` 33) while the equivalent cTrader groups are smaller and mixed
(TARGET 9 of 10 positive, median +2.232157; TRAIL 6 of 7 positive, median +5.257890). The paired
populations for these arms are among the smallest in the device tables and the same
conditional-success selection of §6.1 applies. Left as an open observation.

---

## 7. Controls

Two controls were executed, and two comparator pointer rows are recorded. All are **informative and
gate nothing**, per the design and the amendment.

| Control | Population | Comparator | cTrader rows | crypto rows |
| --- | --- | --- | ---: | ---: |
| `TIME_DERANGEMENT` | `ELIGIBLE_ORIGIN_TIME_DERANGED` | `FIXED_NATIVE_BREAKOUT` | 192 | 1,600 |
| `MAGNITUDE_MATCH` | `ELIGIBLE_ORIGIN_MAGNITUDE_STRATUM` | `FIXED_NATIVE_BREAKOUT` | 768 | 6,400 |
| `FIXED_NATIVE_PARAMETER` | `ELIGIBLE_ORIGIN` | `DECLARED_FIXED_NATIVE` | 1, estimate null, `undefined_reason: REPORTED_IN_NATIVE_PARAMETER_ORIGINS` | 1 |
| `FIXED_DEVICE` | `COMMON_CLOSE_TRADE` | `DECLARED_FIXED_DEVICE` | 1, estimate null, `undefined_reason: REPORTED_IN_DEVICE_TABLES` | 1 |

### 7.1 Fixed comparators

**Observed.** The two fixed comparator rows in `controls.parquet` carry no estimate by design: they
are pointers stating that the fixed-native-parameter comparison lives in
`native_parameter_origins.parquet` (§5.0/§5.1 — every adaptive estimate is already a difference
against `FIXED_NATIVE_BREAKOUT`) and the fixed-device comparison lives in the device tables (§6 —
every device row carries `comparator_observed` beside `observed`, and `comparator_id` names the
declared fixed device). Both comparators are therefore fully reported; they are just reported in
their own tables rather than duplicated in `controls.parquet`. All comparator values quoted in §5
and §6 come from those tables.

### 7.2 TIME_DERANGEMENT — executed, and non-diagnostic for the point estimate

**Observed.** The engine-side derangement is real: `controls.json` records 44,703 deranged rows
(cTrader) and 231,146 (crypto), seed 240730, `zero_fixed_points: true` in both — no origin kept its
own time slot.

**Observed.** Nevertheless, joining all 192 cTrader and all 1,600 crypto `TIME_DERANGEMENT` rows to
their corresponding raw native arm rows:

| Quantity | cTrader | crypto |
| --- | --- | --- |
| control `estimate` identical to raw `estimate` | **192 of 192** (max abs diff 5.55e-17) | **1,600 of 1,600** (max abs diff 3.55e-15) |
| control `ci_low` identical to raw | 0 of 192 (max abs diff 0.028375) | — |
| control `ci_high` identical to raw | 0 of 192 (max abs diff 0.023119) | — |
| control `mde` identical to raw | 0 of 192 (max abs diff 0.028375) | — |

Example (EURUSD, `NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_DIRECT`): control estimate 0.028730
vs raw 0.028730; control CI [−0.019795, +0.078116] vs raw [−0.018085, +0.075757].

**Mechanism (inference).** The estimand on this lens is a **mean over eligible origins**, and a
permutation of time labels leaves the set of per-origin outcomes unchanged — so the mean is
permutation-invariant. The derangement can only alter the block structure used to resample the
interval, which is exactly what the data shows: point estimates identical to machine precision,
intervals and MDEs slightly different. The collapse fraction (control effect divided by raw effect)
is **1.000 in all 1,792 cells**.

**Consequence (stated plainly).** This control cannot discriminate for or against a time-alignment
artifact in these estimates, because a mean statistic is invariant to the permutation applied. It
is reported as executed and as non-diagnostic for the point estimate; it does contribute a
dependence-structure sensitivity read on the intervals. This is a limitation of the control's form
against this estimand, not a data defect, and it is not an integrity finding — the separate
future-shift tripwire (`future_shift_changed_mapping`) is `true` in both universes.

### 7.3 MAGNITUDE_MATCH — executed and diagnostic

**Observed.** `controls.json` records 19,542 magnitude-matched rows on cTrader (9,772 selected,
9,770 excluded) and 96,305 on crypto (48,158 / 48,147). The analysis emits four impulse-magnitude
strata per arm-cell:

| `magnitude_bin` | Universe | rows | median est | ci+ | ci− | median `count` | median `effective_count` |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | cTrader | 192 | −0.039253 | 34 | 9 | 1,607 | 214 |
| 1 | cTrader | 192 | +0.052880 | 14 | 0 | 1,607 | 280 |
| 2 | cTrader | 192 | +0.079294 | 25 | 5 | 1,607 | 280 |
| 3 | cTrader | 192 | +0.070733 | 11 | 1 | 1,606 | 263 |
| 0 | crypto | 1,600 | −0.010676 | 59 | 112 | 1,240 | 184 |
| 1 | crypto | 1,600 | −0.012184 | 64 | 87 | 1,240 | 200 |
| 2 | crypto | 1,600 | −0.130814 | 23 | 29 | 1,240 | 192 |
| 3 | crypto | 1,600 | +0.000000 | 47 | 56 | 1,239 | 164 |

Per-symbol, cTrader (256 rows each): EURUSD median +0.011631 (13 positive / 7 negative),
USTEC +0.083196 (25 / 3), XAUUSD +0.077569 (46 / 5).

**Observed, and the two universes disagree.** Within matched impulse magnitude, cTrader leans
positive in the three upper bins (73 positive against 6 negative across bins 1–3) while crypto is
close to balanced with a slight negative lean (193 positive against 284 negative across all four
bins). A pattern present in one universe and absent — indeed mildly reversed — in the other is
reported as **inconsistent across universes**, with no attempt to reconcile it here.

**Mechanism note (inference).** This control conditions on impulse magnitude, which is precisely
what the volatility components rescale. It therefore does bite on the question "is the adaptive
change just a re-selection toward larger impulses?" — unlike the time derangement, its stratum
means are not invariant to the manipulation.

---

## 8. Observations, stated symmetrically

### Consistent across both universes

1. **SIZE reduces risk dispersion with no outcome change.** 30 of 30 cTrader cells and 204 of 250
   crypto cells with `ci_high < 0` on `risk_dispersion`; tail loss moves the same way with zero
   cells on the opposite side in either universe; the paired outcome estimate is exactly zero
   everywhere (§6.5). The mechanism is transparent and the populations are the largest in the
   device half (`common_close_n` 570 / 420).
2. **Holding longer costs elapsed value.** Duration up, decay up, outcome-per-time down, efficiency
   down; the shock-shortening setting shows the mirror. Both universes, both settings, on the
   largest price-device populations (§6.4).
3. **Wider trails give back more peak without capturing more of the excursion** (§6.3).
4. **The native per-origin effect is small and near-symmetric.** Median |estimate| 0.035 bps
   (cTrader) and 0.310 bps (crypto) per eligible origin, against median MDEs of 0.126 and 0.883;
   interval-excluding cells split 2 up / 11 down and 53 up / 57 down (§5.1).

### Contrary, concentrated, or inconsistent

5. **The cTrader native signal is one instrument.** 11 of 13 interval-excluding cells are XAUUSD
   and all 11 are negative; EURUSD contributes none (§5.3).
6. **The largest crypto native magnitudes are non-trades.** 32 cells with `fill_count == 0`, all
   SWING_SCALE on the four shortest histories; on 1000RATSUSDT all eight report the identical
   −16.669470, which is exactly minus the fixed benchmark's `exposure_per_origin` (§5.3).
7. **The magnitude-matched control leans positive on cTrader and mildly negative on crypto** —
   the two universes do not agree (§7.3).
8. **TARGET and STOP device readings are dominated by an exit-conditioning identity.** `reach_rate`
   is exactly 1.0 for pure targets and `stop_rate` about 1.0 for pure stops, so the closed
   populations are selected by the exit being measured; the largest magnitudes sit on
   `common_close_n` of 1–2 (§6.1, §6.2).
9. **Device-combination arms are differenced against a single-device comparator**, so their negative
   estimates follow from the comparator's construction and are not a comparison between combining
   and not combining (§6.6).

### Unresolved

10. **Whether the native trade lens is degenerate purely by parameter semantics** (the strict-`>`
    admission reading, which the design's golden trace 1 corroborates) **or additionally by a mirrored
    `stop_price` column** cannot be separated from these artifacts (§5.2).
11. **Whether DYDXUSDT's 12 positive cells are a conditional or a single-instrument artifact** —
    it is the one crypto cell whose aggregated ledger total is negative (§5.3).
12. **Whether the component-combination TARGET/TRAIL positives in crypto survive a population that
    is not selected by the exit** (§6.6).
13. **What any of this looks like under real cost.** No spread is charged and every recorded
    commission is zero (§1). Devices differ in trade count and duration, so cost would not cancel
    evenly across the arms compared here.
14. **The time-derangement control cannot speak to the point estimates** in its current form
    (§7.2), so no control in this run bears on time-alignment for the origin-lens means; the
    engine-side future-shift tripwire is the only attestation that does.

---

## 9. Caveats a reader must carry

1. Cost is absent, not partial: zero commission on all 158,547 cTrader and all 771,135 crypto
   positions, zero cost columns populated, spread never charged. All figures are gross.
2. The mirrored spread/cost columns on `per_stratum_estimates.parquet` are null in all six cells;
   the disclosure lives in `config.json` / `run_summary.json` and is reproduced in §1.
3. `run_summary.json` `hard_integrity` reads `NOT_YET_RUN_TASK_8` in both universes; the completed
   14-check block is in `integrity_selfcheck.json` (§2).
4. `estimand_validation.json` physicality figures describe the aggregated multi-arm lattice, not a
   strategy; every cell carries sanity flags for that reason (§2).
5. The two lenses are not interchangeable and are not merged anywhere here; for the native
   parameters the trade lens carries no difference at all (§5.2).
6. `selection_checks.parquet` cannot detect outcome-based selection because excluded origins have
   no outcome (§5.4).
7. `TIME_DERANGEMENT` is non-diagnostic for the point estimate by construction (§7.2).
8. Prose tables in §5 and §6 are summaries. The complete row-level record is the 26 parquet files
   listed in §4, and it reproduces bit-for-bit (`reproduction-hashes.json`, `all_equal: true`,
   13/13 artifacts per universe).

## 10. Hand-off

This record issues no verdict, no ranking, and no disposition. The interpretation across
SPDR-021, SPDR-022 and SPDR-023 belongs to the operator. Probes that could be run against the
existing emission, without a new run: the per-arm order ledger to settle §8.10; a per-instrument
recomputation of §6.1/§6.2 restricted to arms sharing an exit structure, to separate the
conditioning identity from any residual difference; and a cost-sensitivity sweep applying a
per-trade charge to each arm at its own trade count and duration, to see which of §8.1–§8.3
survives an assumed spread.

Analysis probes written for this record: `python/experiments/SPDR-021/analysis_code/probe_read.py`
(read-only; writes nothing; lint-clean under `ruff check`).
