# INFR-017 — Report: Signed-Bar Tier Built, Audited, and Pinned

**Item:** INFR-017 · **Executed:** 2026-07-20 (re-run after QA run 1 REVISE) · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §3
**Stage:** I (instrument building) — outputs are parameters and validated instruments, **never evidence that anything works**.
**Band:** TRAIN only. No TEST contact. Global holdout never queried. 0 counted reads, 0 slots.

---

## 1. One-line outcome

**The kill-gate passed and the signed tier is real** — the stored taker split reproduces from raw Bybit trades *exactly* — but the **stored spread column is not a spread**, and the family's breadth is **296 instruments, not 894**.

## 2. Kill-gate — HYP-I1

> *Does the stored taker split reproduce from raw trades?*

**PASS.** `results/a8_provenance_audit.json`

Gate hardened after QA run 1: it now requires coverage of **all** declared symbol-days (`FAIL_INCOMPLETE_COVERAGE` otherwise — previously 1-of-20 with 19 failed downloads would have returned PASS), and any bar-count or key-set disagreement is a FAIL rather than a note (previously the inner join excluded unmatched bars from the deviation statistics, so a dropped-minute defect could pass silently). Neither bit in this run.

| Measure | Result |
|---|---|
| Symbol-days audited | **20 / 20** declared (5 symbols × 4 days), 0 unavailable |
| `Volume` worst relative deviation | **0.0** |
| `BuyVolume` worst relative deviation | **0.0** |
| `SellVolume` worst relative deviation | **0.0** |
| `NTrades` mismatches | **0** |
| Frozen tolerance | 1e-9 |

Not merely within tolerance — **bit-exact**. The audit recomputed the bars from the raw archive schema without importing `stream_pipeline.py`, so this is provenance, not reproduction (L-01: numeric reproduction is structurally blind to provenance).

**Sign convention tested inside the audit, and it is load-bearing.** The archive's `side` column is the **taker/aggressor** side, not the maker side. Cross-tabulating `side` against `tickDirection` across all 20 symbol-days: `side=Buy` is dominated by `PlusTick` and `side=Sell` by `MinusTick`, **unanimously on every symbol-day, median odds 26.2:1**. Had `side` named the maker, **Δ would carry the wrong sign throughout the family** and every absorption and divergence read would invert. Emitted to `a8_provenance_audit.json` under `aggressor_side_convention` — cite the artifact, not prose. (QA run 1 Issue 8: this claim was previously asserted in a shared docstring from an ad-hoc check the audit never performed; W1 now computes it.)

**Consequence:** the family's founding premise — *per-bar delta is a measurement, not an estimate* — is verified. CF-SIGAUC-001 is not parked.

## 3. The spread column is not a spread (W2)

The most consequential finding. `results/column_pins.json`

**What it actually is** (`INFR-011/scripts/stream_pipeline.py::day_to_bars`):
```
SpreadAbs = MeanBuy − MeanSell        # difference of mean PRINT prices over a whole minute
SpreadBps = 1e4 · SpreadAbs / midpoint
```
A difference of minute-mean prices is dominated by **intra-minute drift**, not by the bid–ask gap. Measured on the TRAIN band:

| Symbol | n minutes | **negative** | median (bps) | nulls |
|---|---|---|---|---|
| BTCUSDT | 750,081 | **32.4%** | 0.147 | 158 |
| ETHUSDT | 745,563 | **39.9%** | 0.077 | 4,543 |
| SOLUSDT | 744,336 | **24.9%** | 0.910 | 6,951 |
| DOGEUSDT | 662,099 | 11.5% | 1.513 | 69,125 |
| XRPUSDT | 733,587 | 7.3% | 1.983 | 15,465 |

A spread is non-negative by construction. A quantity negative in ~40% of minutes on ETH is measuring drift.

**Two compounding gaps:**
1. `docs/references/dataset-reference.md` describes this column as having a *"tick-size floor, conservative bias"*. **No tick floor exists in the producing code.** Doc and artifact disagree.
2. `xen.evaluation.t1_round_trip_spread_bps` returns `stress * spread_bps` **unfloored**, so a negative value propagates into `bybit_round_trip_cost_bps` as a **negative cost — a subsidy.**

**Resolution (pinned).** The stored column is marked **UNUSABLE as a cost input**. A replacement estimator was built and validated on the same audit sample:

> **Flip-pair effective spread** — median `|Δprice|` across adjacent *side-flipping* trade pairs, per minute. Consecutive trades on opposite aggressor sides cross the quoted spread; same-side runs walk the book and are excluded. The per-minute median is robust to the drift that destroys any mean-price differencing.

| Symbol | flip-pair negative | flip-pair median (bps) | 1 tick (bps) |
|---|---|---|---|
| BTCUSDT | **0.0%** | 0.244 | 0.043 |
| ETHUSDT | **0.0%** | 0.305 | 0.058 |
| SOLUSDT | **0.0%** | 0.727 | 0.376 |
| DOGEUSDT | **0.0%** | 1.470 | 1.477 |
| XRPUSDT | **0.0%** | 1.929 | 1.965 |

Zero negatives on every symbol. On wide-tick instruments (DOGE, XRP) it lands **exactly at the tick floor** — the correct answer. On fine-tick instruments it sits above the tick, because adjacent flips also span real price movement. **It is therefore a conservative upper bound on the effective spread, not the quoted spread** — the right direction of error for a cost floor, and it must be labelled as such wherever used.

**Scope limit, stated honestly.** The flip-pair estimator needs raw trades. Bulk trades are not retained, so it is currently validated on 20 symbol-days only. Computing it across the universe is a **separate data operation** (INFR-011 scale), not inside INFR-017's budget. Until then, SPDR-007's money floor uses `taker RT 11.0 bps + max(tick, flip-pair estimate) + funding` on the instruments where it is measured, and a **tick-size floor** elsewhere.

> **Blast-radius flag — raised, not resolved.** `SpreadBps` and `t1_round_trip_spread_bps` are shared programme cost machinery, not family-local. Whether any prior chapter-04 cost read was affected is **not an INFR-017 question** and was not investigated. Flagged for the operator and the checkpoint-014 retrospective.

## 4. Stream dependence (W3) — resolves permissively

Source §0.3/§2.5 treats the spread regime layer as separable from the bar-flow stream. Both are computed from the same aggressor split here, so the dependence was measured rather than assumed:

| Symbol | corr(Δ/V, stored spread) | 95% CI | corr(Δ/V, flip-pair) |
|---|---|---|---|
| BTCUSDT | −0.031 | [−0.057, −0.006] | −0.005 |
| ETHUSDT | −0.028 | [−0.053, −0.002] | +0.007 |
| SOLUSDT | −0.019 | [−0.045, +0.007] | +0.012 |
| DOGEUSDT | +0.006 | [−0.022, +0.033] | −0.002 |
| XRPUSDT | −0.048 | [−0.074, −0.022] | +0.007 |

All `|corr| ≤ 0.048`, far below the pre-declared 0.20 reporting threshold. **Shared source does not produce shared signal.** The §2.5 spread regime layer may be treated as separable from Δ reads. Constraint lifted; recorded in the pin.

## 5. Remaining work items

| ID | Outcome |
|---|---|
| **W4** `NTrades` | Usable. Median average trade size: BTC 0.146, ETH 1.43, SOL 29.3, DOGE 5,225, XRP 1,334 (base units). Admitted as a z-scored participation multiplier **only**, seasonally normalised (order-splitting drift). Never a standalone signal. |
| **W5** signed lane | **Round-trip exact against the staging source.** 1,440 bars × 3 symbols, joined on timestamp: **0 mismatches** across all ten compared fields (OHLC, `Volume→volume`, `BuyVolume→buy_volume`, `SellVolume→sell_volume`, `NTrades→n_trades`, `Delta→delta`, and `SpreadBps→spread_feature` with its status), **0 split-invariant violations**. QA run 1 (Issue 4) found the original check compared written objects against themselves — proving only that Nautilus serialisation is lossless, which INFR-013 already established; a swapped Buy/Sell mapping would have passed. It now compares against staging, which is what the exit condition requires. Separate catalog root (`data/catalog_sigbar/`); spread status read **from the pin** (`config_hash = e3b9fd9b…`), not hard-coded. |
| **W6** A5 baselines | **194 instruments fitted**, 5 metrics each, on the **full 1440×7 = 10,080-cell grid** (verified: `mod` spans 0–1439, 1,440 distinct values), median + 1.4826·MAD, DESIGN-bank only, uncovered cells materialised with the day-of-week fallback. `\|Δ\|` and `Δ/V` fitted **separately** per A5. Artifact sha256 `1b7244c87aaafe29…`. **The first fit was invalid** — §7a. |
| **W7** admission | 904 staged / 894 ADMITTED / **10 staged-not-admitted**, each listed with its reason. The signed lane inherits ADMITTED status. Delta fully explained. |

## 6. The breadth finding — material for SPDR-008

The source's stated comparative advantage is breadth (§6.12: *"validate across the full cross-section FIRST"*), and checkpoint-014 §6 set SPDR-008's universe to "full ADMITTED cross-section". Measured:

Emitted to `results/admission_reconciliation.json` under `band_coverage` — these numbers drive a recommended checkpoint change, so they are computed and stored, not asserted in prose (QA run 2, Issue 3).

| Population | Count |
|---|---|
| ADMITTED instruments | 894 |
| …with **any** bars before TRAIN end (2023-12-18) | **296** |
| …with **any** bars before DESIGN-bank end (2023-03-01) | **197** |
| Baselines actually fitted | 194 (3 lost to corrupt staging parquets, §7d) |

The 4-year trailing history cap plus late listings mean **two thirds of the admitted universe has no readable TRAIN data at all**. This is not fatal — 296 instruments is still an order of magnitude more breadth than any prior family in this programme (which ran 10–20) — but the checkpoint's "full ADMITTED cross-section" phrasing overstates it.

**Recommended checkpoint amendment (operator's call, NEUTRAL direction):** restate the SPDR-008 universe as *"all admitted instruments with readable TRAIN data — measured 296"*, and INFR-018/SPDR-007's n=20 as drawn from the 197 with DESIGN-bank coverage.

## 7. Defects found and fixed (QA run 1 → REVISE → re-run)

QA run 1 returned **REVISE** with two blocking defects. Recorded here rather than quietly corrected.

### 7a. The seasonal grid was silently aliased — the first baseline artifact was invalid

`xen.sigbar.baselines` computed minute-of-day as `hour * 60 + minute`. Polars returns `dt.hour()` and `dt.minute()` as **Int8**, so `hour * 60` overflows for every hour >= 3 and the sum wraps: `05:00 -> 44`, `23:59 -> -97`, `12:30 -> -18`. The grid collapsed from 1,440 minutes to **256 aliased buckets** (range -128…127), each pooling roughly five unrelated times of day.

- **Why it was invisible:** no exception, self-consistent keys (`residualise` used the same broken expression), plausible-looking artifact. It would have surfaced only as uninterpretable Stage II results.
- **What it destroyed:** exactly the confound A5 exists to remove. A "high volume" residual would have compared 00:44 against 05:00 against 10:16.
- **Fix:** explicit `Int32` casts; an `assert_seasonal_keys_valid` range guard at the point of use; the full 10,080-cell grid materialised so uncovered cells are explicit rows carrying the fallback rather than missing rows that left-join to null; and a **regression test** (`python/tests/test_sigbar_baselines.py`, 5 cases) pinning the key to the identity on minute index and asserting the exact timestamps that wrapped.
- **The first artifact and its sha `78dd7988…` are discarded, not re-pinned.** Current: `1b7244c8…`.

### 7b. The design's own headline numbers crossed the sealed holdout — **CLEARED by the operator 2026-07-20**

Two holdout touches occurred: one caught in-flight, one caught by QA.

**(i) Caught during execution.** `spread_pin.py::_tick_bps_reference` scanned the full staging parquet with no band filter. Fixed to bound the read to the sampled TRAIN days; the corrected tick references changed materially (BTC 0.0157 -> 0.0429 bps).

**(ii) Caught by QA — the design text, not the code.** design.md §3(b) originally reported BTC `n = 2,103,839` and 39.6% negative. That is the **entire staging file**, spanning 2022-07-15 -> 2026-07-14, including **796,320 bars at or after `holdout_start_utc`**. The figures came from an ad-hoc exploratory scan run before the item's read paths existed. The code was fenced; the table was not.

- **What was read:** the univariate distribution of one data-quality column — count, sign fraction, quantiles. No price path, no forward return, no P&L, no signal.
- **Effect on conclusions:** none directional. On TRAIN the column is still negative in 32.4% of BTC minutes, so W2 exists for the same reason — but the specific numbers did not reproduce and are replaced throughout (design §3(b), checkpoint-014 §3, `data_types.py`).
- **Read budget:** spends no sanctioned shot (not an edge read, not a TEST read).
- **Status: ADJUDICATED — CLEARED (operator, 2026-07-20).** The disclosure stands permanently in design.md §3(b); the holdout remains SEALED for all evidential purposes and no sanctioned read was consumed.

**Fence state after the fix:** QA independently verified every code read path is bounded and assert rather than warn, and that the CONFIRM bank is untouched (max fitted bar `2023-02-28 23:59:00`).

### 7c. Three further QA findings, fixed

- **The W2 pin recorded no decision.** The UNUSABLE call was hard-coded in `signed_bar_lane.py` while `column_pins.json` — the artifact meant to freeze it — stated nothing. Exactly the drift a pin exists to prevent. The pin now carries a `W2_decision` block (chosen option, reason, why each rejected option lost, downstream constraint) plus a self-`pin_sha256`; the ingest **reads the status from the pin** and stamps its hash into every record as `config_hash`.
- **The kill-gate admitted partial passes** — see §2.
- **A shared data contract asserted an unperformed verification** — see §2.

### 7d. Known limitations carried forward

- Three staging parquets are corrupt and could not be fitted (`KAVAUSDT`, `KLAYUSDT`, `KNCUSDT`) — belongs back with INFR-011.
- The A8 `0.0` deviation is stronger than "matches to rounding", but it means the audit and the pipeline perform the same float summation over the same rows. Independence is genuine at the level of *code path* (no import — L-01 satisfied), not of *algorithm*: the audit deliberately copies INFR-011's documented cleaning rule, so a defect in that rule would reproduce. Bounded by `NTrades` matching exactly and bar counts agreeing on all 20 days.
- The W3 Fisher-z CI assumes independent observations on autocorrelated minute data — disclosure only, not dependence-honest.
- `cell_coverage` now separates **empty** cells from **thin-but-populated** cells; previously one `sparse` rate conflated them, and 73 of 194 symbols were affected (one reported 100% sparse while 62% of its grid was simply empty).
- The pin distinguishes its two scopes explicitly: `stored_column_full_train` is the whole TRAIN band; every candidate-estimator figure is the 4 pre-declared sample days. They differ by 1–2 points per symbol and must not be quoted interchangeably.

### 7e. QA runs 2 and 3 — both blocking defects confirmed fixed, bookkeeping corrected

QA run 2 re-derived the fixes from the data rather than accepting the claims: it re-ran the old grid expression to confirm the regression test genuinely catches the bug, verified the emitted parquet has 10,080 cells spanning minutes 0–1439, confirmed the corrected TRAIN figures reproduce from the result file, and found no new fence violation across every data read path. Verdict **REVISE** on bookkeeping only:

1. **Report §8 handed INFR-018 the discarded baseline hash** (`78dd7988…` instead of `1b7244c8…`) — the next item would have failed its check or loaded the broken file. **Corrected.**
2. **The family registry still carried the holdout-derived null counts** (168 / 4,652 / 7,066). Every other location had been corrected; this one is the record downstream items read. **Corrected to 158 / 4,543 / 6,951.**
3. **The breadth numbers were prose-only.** Now emitted to `admission_reconciliation.json`.
4. **The pin mislabelled sample-day figures as TRAIN-band.** Scope labels added to both blocks.

Plus the three minor notes above (spread fields absent from the round-trip, null-blind mismatch counter, conflated sparse rate) — all fixed.

**QA run 3** confirmed items 1–3 and all minors, and caught one that had survived two rounds: the frozen `W2_decision` block quoted the **4-sample-day** negative rates under a "TRAIN band" label, while the design and report published the full-TRAIN figures. A warning note had been added at the top of the pin, but the misleading sentence itself was left standing — inside the artifact INFR-018 reads as the decision of record. Now corrected to quote the full-TRAIN rates (BTC 32.374%, ETH 39.939%, SOL 24.937%, DOGE 11.506%, XRP 7.282%) with both scopes carried explicitly under `evidence_scopes`. Conclusion unchanged — the column is unusable on either scope.

`pin_sha256` is now **`e3b9fd9b…`** (it changed twice as the pin's content was corrected); the lane's `config_hash` tracks it, so no record carries a hash that no longer exists. The baselines sha `1b7244c8…` has been stable across every rerun — the fit is deterministic.

## 8. What INFR-018 may now treat as frozen

**May rely on:**
- `Δ = BuyVolume − SellVolume` as exact per-bar taker aggression, sign convention verified.
- The A5 seasonal baselines (`seasonal_baselines.parquet`, sha256 **`1b7244c87aaafe29…`** — NOT the discarded `78dd7988…`, see §7a) for every threshold — "high volume", "large |Δ|", "wide range" are residuals against these, never raw numbers.
- The `SignedBar` contract and `data/catalog_sigbar/` as the engine-readable path.
- Spread and bar-flow as **separable** streams (W3).

**May NOT rely on:**
- `SpreadBps` as a spread or a cost input — **UNUSABLE**, pinned.
- Universe breadth beyond the **296** TRAIN-readable instruments (197 in the DESIGN bank).
- Any flip-pair spread number outside the 20 audited symbol-days without recomputing it.
- The CONFIRM bank for anything — untouched by this item, and it stays untouched until each INFR-018 kill-gate confirms there.

## 9. Verdict

**HYP-I1 PASS. INFR-017 complete.** The measuring instruments exist, are audited, and are pinned. One column was found broken and is pinned as such rather than quietly used. The family proceeds to INFR-018 (anchor race, acceptance-discriminator race, proxy validation).

Nothing in this item is evidence that any signal works — by construction (Stage I).
