# Actionable confirmation extraction — SPDR-021 / 022 / 023 adaptive-management screens

Band: **TRAIN only**. Cost scope: **partial (fees/funding only), spread NOT charged**.
This document contains no experiment verdict, no family disposition, no XENA gate, no deployability claim.

---

## 0. Setup

### 0.1 Experiments, runs, cost scope

| Cell | Experiment | Universe | Run stamp | Integrity | Estimand validation |
|---|---|---|---|---|---|
| 1 | SPDR-021 (breakout) | cTrader (3 symbols) | `SPDR-021-ctrader-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |
| 2 | SPDR-021 | crypto (25 symbols) | `SPDR-021-crypto-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |
| 3 | SPDR-022 (MOMO breach) | cTrader | `SPDR-022-ctrader-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |
| 4 | SPDR-022 | crypto | `SPDR-022-crypto-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |
| 5 | SPDR-023 (MR breach) | cTrader | `SPDR-023-ctrader-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |
| 6 | SPDR-023 | crypto | `SPDR-023-crypto-train-20260803T140238Z` | `blocking_pass: true` | `blocking_pass: true` |

No missing cells. No integrity failures — extraction proceeds on all six.

**Cost scope (one line):** every run declares `cost_scope: PARTIAL_FEES_FUNDING_ONLY`, `spread_cost_status: UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps: null`. Every bps number below is **effectively gross**. Prohibited claims per the run's own disclosure: fully-net, cost-complete, tradable, deployable.
Provenance: `data/nautilus_runs/<run>/run_summary.json` → `spread_cost_disclosure`; identical block in `config.json`.

### 0.2 Cell grid and independence structure (Pre-test H)

Grid = experiment × universe, 6 cells (table above).

**Independence, mandatory statement.** SPDR-022 and SPDR-023 share band, origins, symbols, period and differ only in **entry direction**. They are near-siblings, not independent replicates. This extraction goes further than the caveat and **measures** the sibling relation (see ledger `X-01`): on `E_CLOSE` the two experiments' fixed baselines are **exact negatives of each other, symbol by symbol, to machine precision**. Any claim resting on 022+023 alone counts as **one substrate**.

Weighting: cTrader carries 3 symbols, crypto 25. A crypto cell and a cTrader cell are not equal weight; both are reported separately throughout, never pooled.

Substrate count for A1 shape = **2 of 3** at best (021 breakout; 022/023 breach-band as one).

### 0.3 Chance-rate calibration (quoted, as required)

- **Sign-only agreement is not evidence.** Under a coin flip, P(≥4 of 6 cells agreeing in sign) = 22/64 = **34.4%**. Scanning ~50 metric families under sign-only would produce ~17 spurious "global" findings. Direction agreement alone counts **zero** cells in this document.
- **Per-cell null rate, measured in these very runs** — native origin lens, non-fixed arms, `state = ALL`:

| Cell | rows | CI excludes 0 | rate | `\|est\|>MDE` | rate |
|---|---|---|---|---|---|
| 021 ctrader | 192 | 13 | 6.77% | 8 | 4.17% |
| 021 crypto | 1,600 | 110 | 6.88% | 72 | 4.50% |
| 022 ctrader | 384 | 17 | 4.43% | 17 | 4.43% |
| 022 crypto | 3,200 | 135 | 4.22% | 122 | 3.81% |
| 023 ctrader | 384 | 10 | 2.60% | 9 | 2.34% |
| 023 crypto | 3,200 | 115 | 3.59% | 92 | 2.88% |

Median ≈ **4.3%** — interval coverage, nothing more. **~4.5% is the per-cell null rate used throughout.** Under it, 4-of-6 *qualifying* cells is a ~1e-5 event.

- **Warning that changes how the device tables must be read.** The device tables do **not** sit at the null rate: 43–55% of finite `ORDER_CREATED` rows have CI excluding zero (021 ctr 55.2%, 021 cry 43.2%, 022 ctr 52.6%, 022 cry 46.7%, 023 ctr 52.5%, 023 cry 44.1%). That elevation is **almost entirely forced metrics** — see section 1. Splitting by metric separates them cleanly: `decay_bps` 89.6–100%, `risk_dispersion` 84.0–100%, `opportunity_duration` 94.0–100% against `outcome_by_time_bps` 19.2–34.3%, `drawdown_bps` 13.4–25.0%, `recovery_after_stop_bps` 8.2–20.9%. Reading the device tables un-split converts machine execution into "findings"; Pre-test F is the whole difference.

### 0.4 Fixed comparator levels (needed by B-pre-1)

`per_stratum_estimates.parquet`, `arm_class = FIXED_NATIVE`, finite `gross_mean_bps`:

| Cell | variant | median gross bps | median `win_share` | median `breakeven_win_share_net` | trades |
|---|---|---|---|---|---|
| 021 ctrader | BREAKOUT | **+0.743** | 0.5120 | 0.4591 | 3,396 |
| 021 crypto | BREAKOUT | **+5.092** | 0.4617 | 0.4452 | 16,938 |
| 022 ctrader | E_CLOSE | **−0.312** | 0.4908 | 0.4920 | 15,074 |
| 022 ctrader | E_TOUCH | **−0.411** | 0.5000 | 0.5083 | 16,992 |
| 022 crypto | E_TOUCH | **−2.118** | 0.4727 | 0.4874 | 86,154 |
| 022 crypto | E_CLOSE | **−2.578** | 0.4645 | 0.4886 | 76,422 |
| 023 ctrader | E_TOUCH | **+0.385** | 0.4968 | 0.4928 | 16,992 |
| 023 ctrader | E_CLOSE | **+0.312** | 0.5068 | 0.5080 | 15,074 |
| 023 crypto | E_TOUCH | **+2.373** | 0.5197 | 0.5101 | 86,154 |

**SPDR-022's baseline is a losing baseline before any spread is charged** (`win_share` at or below `breakeven_win_share_net` on all four rows). Any ECONOMIC SUPPORT item measured against it is capped at PARK by B-pre-1 and may only be phrased as "less bad than a losing baseline". SPDR-021's baseline is marginally above its own break-even, still gross.

---

## 1. Machine checks (FORCED metrics — attestation, not findings)

Population for every row: `state = ORDER_CREATED`, `arm_class != FIXED_MANAGEMENT`, finite estimate/CI/MDE. Hit rate = share of rows whose CI excludes zero. Range across the 6 cells.

| Metric | Device | Expected direction (by construction) | Hit rate range (6 cells) | median est/MDE range | Fired? |
|---|---|---|---|---|---|
| `decay_bps` | HOLD | longer hold ⇒ more decay | 89.6% – 100% | 2.40 – 4.78 | yes, 6/6 |
| `opportunity_duration` | HOLD | 12-bar arm occupies longer than 4-bar | 94.0% – 100% | 0.80 – 0.97 (of rows > MDE) | yes, 6/6 |
| `risk_dispersion` | SIZE | halving/normalising risk ⇒ less dispersion | 84.0% – 100% | 1.48 – 6.03 | yes, 6/6 |
| `adverse_excursion_bps` | STOP | wider stop ⇒ reached later / deeper | 41.9% – 73.9% | 0.55 – 1.31 | yes, 6/6 |
| `peak_giveback_bps` | TRAIL | wider trail ⇒ more giveback | 48.5% – 73.3% | 0.69 – 1.71 | yes, 6/6 |
| `time_to_target` | TARGET | farther target ⇒ later | 42.5% – 58.0% | 0.01 – 0.29 | partially |
| `realised_capture_bps` | TARGET | farther target ⇒ more captured when reached | 49.8% – 84.9% | 0.35 – 1.32 | yes, 6/6 |
| `tail_loss_bps` | SIZE | halving risk in HIGH ⇒ smaller tail | 38.0% – 96.7% | — | yes |
| `reach_rate` (pure TARGET) | TARGET | degenerate: 1.000 both sides | Δ exactly 0 on 100% of rows, 6/6 | 0 | degenerate |
| `stop_rate` (pure STOP) | STOP | degenerate on 022/023 | Δ exactly 0 on 98.5–100%, 4 cells | 0 | degenerate |

None of the above is a finding. They attest the rig executed the declared rules. `reach_rate` / `stop_rate` degeneracy re-enters the ledger as `X-08` (apparatus), and `decay_bps` / `risk_dispersion` / `peak_giveback_bps` / `adverse_excursion_bps` re-enter only as the reference half of the Pre-test G pairs `X-03` … `X-06`.

**Pre-test G paired contrasts, on identical rows** (the pair join is by `symbol × entry_variant × arm_id × arm_class × component × setting × comparator_id × state`, keeping only rows where **both** metrics are finite):

| Cell | Device | FORCED metric | hit/n | rate | est/MDE | FREE metric | hit/n | rate | est/MDE | blocks |
|---|---|---|---|---|---|---|---|---|---|---|
| 021 ctr | HOLD | decay_bps | 34/36 | 94.4% | 3.05 | outcome_by_time_bps | 10/36 | 27.8% | 0.69 | 319 |
| 021 cry | HOLD | decay_bps | 267/298 | 89.6% | 2.40 | outcome_by_time_bps | 60/298 | 20.1% | 0.11 | 174 |
| 022 ctr | HOLD | decay_bps | 70/70 | 100% | 4.78 | outcome_by_time_bps | 22/70 | 31.4% | 0.18 | 475 |
| 022 cry | HOLD | decay_bps | 557/596 | 93.5% | 2.83 | outcome_by_time_bps | 115/596 | 19.3% | 0.03 | 203 |
| 023 ctr | HOLD | decay_bps | 68/68 | 100% | 4.11 | outcome_by_time_bps | 22/68 | 32.4% | 0.04 | 479 |
| 023 cry | HOLD | decay_bps | 548/600 | 91.3% | 2.90 | outcome_by_time_bps | 115/600 | 19.2% | 0.15 | 202 |
| 021 ctr | SIZE | risk_dispersion | 30/30 | 100% | 2.45 | drawdown_bps | 7/30 | 23.3% | 0.44 | 405 |
| 021 cry | SIZE | risk_dispersion | 210/250 | 84.0% | 1.48 | drawdown_bps | 43/250 | 17.2% | 0.37 | 287 |
| 022 ctr | SIZE | risk_dispersion | 58/60 | 96.7% | 6.03 | drawdown_bps | 14/60 | 23.3% | 0.73 | 650 |
| 022 cry | SIZE | risk_dispersion | 428/500 | 85.6% | 2.00 | drawdown_bps | 110/500 | 22.0% | 0.50 | 521 |
| 023 ctr | SIZE | risk_dispersion | 58/60 | 96.7% | 5.73 | drawdown_bps | 15/60 | 25.0% | 0.67 | 654 |
| 023 cry | SIZE | risk_dispersion | 429/500 | 85.8% | 2.04 | drawdown_bps | 67/500 | 13.4% | 0.36 | 521 |
| 021 ctr | TRAIL | peak_giveback_bps | 22/30 | 73.3% | 1.71 | favourable_excursion_captured | 8/30 | 26.7% | 0.19 | 151 |
| 021 cry | TRAIL | peak_giveback_bps | 151/261 | 57.9% | 0.86 | favourable_excursion_captured | 45/261 | 17.2% | 0.24 | 42 |
| 022 ctr | TRAIL | peak_giveback_bps | 28/51 | 54.9% | 0.96 | favourable_excursion_captured | 15/51 | 29.4% | 0.18 | 13 |
| 022 cry | TRAIL | peak_giveback_bps | 225/434 | 51.8% | 0.84 | favourable_excursion_captured | 101/434 | 23.3% | 0.00 | 13 |
| 023 ctr | TRAIL | peak_giveback_bps | 26/43 | 60.5% | 1.39 | favourable_excursion_captured | 14/43 | 32.6% | 0.20 | 29 |
| 023 cry | TRAIL | peak_giveback_bps | 224/462 | 48.5% | 0.69 | favourable_excursion_captured | 110/462 | 23.8% | 0.07 | 15 |
| 021 ctr | STOP | adverse_excursion_bps | 17/23 | 73.9% | 1.31 | recovery_after_stop_bps | 4/23 | 17.4% | 0.33 | 101 |
| 021 cry | STOP | adverse_excursion_bps | 141/292 | 48.3% | 0.75 | recovery_after_stop_bps | 46/292 | 15.8% | 0.13 | 44 |
| 022 ctr | STOP | adverse_excursion_bps | 24/41 | 58.5% | 1.09 | recovery_after_stop_bps | 0/41 | 0.0% | 0.02 | 26 |
| 022 cry | STOP | adverse_excursion_bps | 206/492 | 41.9% | 0.55 | recovery_after_stop_bps | 51/492 | 10.4% | 0.06 | 16 |
| 023 ctr | STOP | adverse_excursion_bps | 26/50 | 52.0% | 0.95 | recovery_after_stop_bps | 8/50 | 16.0% | 0.13 | 16 |
| 023 cry | STOP | adverse_excursion_bps | 233/492 | 47.4% | 0.82 | recovery_after_stop_bps | 77/492 | 15.7% | 0.01 | 14 |

TARGET is deliberately absent from the paired table: **both** of its emitted outcome metrics (`realised_capture_bps`, `missed_excess_bps`) are functions of target distance, and its rate metric is degenerate. TARGET has **no FREE metric emitted** — that is itself an apparatus fact (`X-08`).

---

## 2. Actionable confirmation ledger

Sorted per the required key: FREE before FORCED-paired, then consistency shape, then `min(effect/MDE)` across qualifying cells (weakest cell), then `min(effective_count)`, then A2-MECHANISM before A2-SEARCHED.

---

### [X-01] SPDR-022 and SPDR-023 are the same trades with the sign flipped — the native geometry effect is a direction artifact

- **Claim:** *refuted* — "the MOMO-breach and MR-breach screens are two substrates, and the native band geometry (`z`, `H`) produces an effect on each."
- **Polarity:** REFUTE
- **Kind:** STRUCTURAL
- **Forcedness:** FREE (the estimates are per-origin outcome estimates; nothing in the arm definitions forces them to be exact negatives)
- **Consistency path:** A1 GLOBAL over the 022/023 block (shape: **4/6 cells, 1/2 available substrates in that block, 2/2 universes, both entry variants**; per-cell qualifying rule (c) structural on E_CLOSE, (b) on E_TOUCH)
- **Hit rate & denominator:**
  - Fixed baseline, `E_CLOSE`: `gross_mean_bps(022) + gross_mean_bps(023) = 0.0` **exactly** on **25/25 crypto symbols** and **3/3 cTrader symbols** (largest residual 1.78e-15).
  - Origin-lens estimates, joined on `symbol × entry_variant × arm_id × component × parameter × orientation × state=ALL`: Pearson **r = −0.9893** (crypto, n = 3,200), **r = −0.9467** (cTrader, n = 384). Opposite sign on **3,032/3,200 (94.8%)** crypto and **353/384 (91.9%)** cTrader rows.
  - Cancellation magnitude: median `|est_022 + est_023|` = **5.33e-15** (crypto) vs median `|est_022|` = 0.617 — i.e. **complete** cancellation. cTrader: 0.0034 vs 0.061 — 94% cancellation.
- **Effect:** metric = per-origin occupancy-inclusive outcome estimate and fixed-arm gross bps; the 023 value is the negation of the 022 value; comparator = the paired experiment.
- **Weakest qualifying cell:** cTrader E_TOUCH, where the mirror is 91.9% rather than exact — the residual is the touch-fill asymmetry (a limit touch fills on one side and not the mirrored side), not an independent effect.
- **Significance standard:** structural / identity (exact zero across the full population on E_CLOSE), supported by near-universal directional on E_TOUCH.
- **Evidence snapshot:** crypto E_CLOSE per-symbol sums: 1000BONK 1.78e-15, 1000LUNC −8.88e-16, 1000PEPE −1.78e-15, ADA 0.0, AVAX 0.0 (…25/25). cTrader USTEC E_CLOSE exactly 0.0.
- **Provenance:**
  `python/experiments/SPDR-02{2,3}/results/analysis/{ctrader,crypto}/per_stratum_estimates.parquet` | `gross_mean_bps` | `arm_class == 'FIXED_NATIVE' and gross_mean_bps.is_finite()` | 6/50 rows per cell.
  `…/native_parameter_origins.parquet` | `estimate` | `arm_class != 'FIXED_NATIVE' and state == 'ALL'` | 384 / 3,200 rows per universe.
- **Conditioning required?:** none.
- **Failure modes checked:** concentration (mirror holds symbol-by-symbol, not just pooled); small-n (25 crypto symbols, 3,200 arm rows); lens mismatch (holds on origin lens AND on the fixed baseline); leak (no single symbol drives it).
- **Actionability:** **METHOD** + **KILL-AS-ALPHA**
- **Implication:** running the long and the short version of the same band is not a replication — it is the same trade twice with the sign flipped, so "022 supports it and 023 supports it" can never be true at once, and neither can carry the other.
- **Next use:** never count 022 and 023 as two cells for robustness. Any future direction-pair design must either share one comparator or predeclare that only the *asymmetry* between the two sides is estimable.

---

### [X-02] Admission-rule geometry never changes the value of a shared trade — it acts only on selection

**Scope note, stated first:** this item covers the **admission-rule** parameters — SPDR-021's `BREAKOUT_THRESHOLD` and `PENDING_EXPIRY`, and SPDR-022/023's `BAND_H`. It **does not** cover `BAND_Z`, which is a price-offset parameter and does move shared-trade outcomes on ~24% of pairs. Do not generalise the identity to `BAND_Z`.

- **Claim:** *refuted* — "changing a native **admission rule** (breakout threshold, pending expiry, band `H`) improves the outcome of the trades it and the fixed arm both take."
- **Polarity:** REFUTE
- **Kind:** STRUCTURAL
- **Forcedness:** FREE (nothing in a threshold/expiry/`H` change forces a shared trade to have an identical outcome — it is an empirical identity of how these arms interact with the fill mechanics)
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, all entry variants**; per-cell qualifying rule (c) structural — exact zero across the full population in every cell)
- **Hit rate & denominator:**
  - SPDR-021, **all three parameters**, paired trade delta exactly 0 on **100.0%** of rows: cTrader 72,477/72,477 (`BREAKOUT_THRESHOLD` 19,003; `PENDING_EXPIRY` 20,724; combination 32,750); crypto 346,894/346,894 (89,460 / 102,996 / 154,438).
  - SPDR-022/023, `BAND_H`: exactly 0 on **100.0%** of rows — 152,538 (022 ctr), 769,378 (022 cry), 152,193 (023 ctr), 768,999 (023 cry).
  - `BAND_Z` and `BAND_Z+BAND_H` are the only arms with any non-zero pairs, and even there **73.6–76.6%** of pairs are exactly zero.
- **Effect:** metric = `paired_outcome_delta_bps`; median delta = **0.0000** on every parameter in every cell; comparator = `FIXED_NATIVE_BREAKOUT` / `FIXED_NATIVE_BAND_E_{TOUCH,CLOSE}`.
- **Weakest qualifying cell:** none — the identity is exact in all six.
- **Significance standard:** structural / identity.
- **Evidence snapshot:** SPDR-021 crypto, 346,894 shared-trade rows, mean delta 0.0, median 0.0, zero-share 1.000.
- **Provenance:** `python/experiments/SPDR-02{1,2,3}/results/analysis/{ctrader,crypto}/native_parameter_shared_trades.parquet` | `paired_outcome_delta_bps` | `paired_outcome_delta_bps.is_not_null()`, grouped by `parameter` | 72,477 / 346,894 / 377,857 / 1,743,705 / 377,333 / 1,742,747 rows.
- **Conditioning required?:** none.
- **Failure modes checked:** small-n (millions of rows); lens mismatch (this *is* the trade lens; the origin lens is reported separately and disagrees, which is the point); zero-fill (rows with null delta excluded, share reported).
- **Actionability:** **METHOD** + **KILL-AS-ALPHA**
- **Implication:** these entry-geometry knobs decide *which* trades happen, never *how well* the shared ones do — so the trade lens is structurally blind to them and cannot be used to compare them.
- **Next use:** for any selection-style parameter, read the origin/occupancy lens only, and state up front that the trade lens will return zero. A design that budgets power for a trade-lens read of `H` is spending it on a guaranteed null.

---

### [X-03] Vol-gated hold length moves elapsed-time metrics exactly as coded and leaves trade value where it was

- **Claim:** *refuted* — "changing exit timing by volatility state changes the trade's value."
- **Polarity:** REFUTE
- **Kind:** ECONOMIC (paired against a MECHANICAL reference — Pre-test G, one item)
- **Forcedness:** FREE (`outcome_by_time_bps`), paired with FORCED-as-reference (`decay_bps`)
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, both entry variants**; per-cell qualifying rule (b) — median `|estimate|` far below median MDE with the claim explicitly "no resolved change")
- **Hit rate & denominator:** on identical rows, `decay_bps` resolves **34/36, 267/298, 70/70, 557/596, 68/68, 548/600** (89.6–100%) at est/MDE 2.40–4.78, while `outcome_by_time_bps` resolves **10/36, 60/298, 22/70, 115/596, 22/68, 115/600** (19.2–32.4%) at est/MDE **0.03–0.69**.
- **Restricted to the actual volatility rule** (`setting = STATE_LOW_4_HIGH_12`, i.e. hold 4 bars in LOW and 12 in HIGH): median est/MDE = **0.60, 0.06, 0.04, 0.08, 0.05, 0.07** across the six cells, resolving 4/27, 15/225, 12/54, 27/450, 14/54, 26/450, with signs **mixed** (e.g. 022 crypto 12 positive / 15 negative; 023 crypto 13/13).
- **Effect:** metric = `outcome_by_time_bps`; median delta = **+0.065 to +1.76 bps** on the state-gated rule; comparator = `FIXED_HOLD_B4`.
- **Weakest qualifying cell:** 022 cTrader, est/MDE = **0.04**, `effective_trade_blocks` median **478**.
- **Significance standard:** interval standard, null clause — "there is a resolved change in value" is refuted.
- **Evidence snapshot:** 021 cTrader `STATE_LOW_4_HIGH_12`: median est −2.030 vs median MDE 3.360, 4/27 resolving, all negative. 022 crypto: median est +1.043 vs MDE 13.591, 27/450 resolving, 12 positive / 15 negative.
- **Provenance:** `…/device_hold.parquet` | `estimate, ci_low, ci_high, mde` | `arm_class != 'FIXED_MANAGEMENT' and state == 'ORDER_CREATED' and metric_name in {'decay_bps','outcome_by_time_bps'}`, inner-joined on the 8-key row identity | 36 / 298 / 70 / 596 / 68 / 600 paired rows.
- **ECONOMIC — B-pre-1 baseline:** 021 +0.743 / +5.092 bps gross; 022 **−0.31 to −2.58 bps gross, `win_share` at or below `breakeven_win_share_net`**; 023 the exact mirror. This item is a REFUTE, so B-pre-1's PARK cap does not bind, but the baseline sign is quoted as required.
- **ECONOMIC — B-pre-2 break-even spread:** the gated arm and `FIXED_HOLD_B4` both close once per paired origin, so `round-trips per unit of effect = 1` on each side and spread **cancels in the difference**. `breakeven_spread_rt_bps = |0.065…1.76| / 1 = 0.07 – 1.76 bps` if charged one-sided. Statement: *even the point estimate is fully consumed at a round-trip spread of under 2 bps.* Label: **NON-EMITTED SCENARIO** (`spread_rt_bps` is null in the run).
- **Conditioning required?:** none — the claim is refuted both ungated and under the state gate.
- **Failure modes checked:** concentration, small-n (`effective_trade_blocks` median 174–479, all ≥30), zero-fill, unfair comparator (same-device comparator `FIXED_HOLD_B4`), lens mismatch, cost.
- **Actionability:** **KILL-AS-ALPHA**
- **Implication:** holding longer in calm markets and shorter in rough ones changes how long you sit in the trade — reliably, by construction — and does not change what the trade is worth.
- **Next use:** stop treating hold-length rules as an expectancy lever. If they are kept at all, justify them on exposure/capacity grounds and measure that, not P&L.

---

### [X-04] Vol-gated stop distance does not carry the loss-severity effect — the fixed distance does

- **Claim:** *refuted* — "gating stop distance by volatility state is what controls loss severity."
- **Polarity:** REFUTE
- **Kind:** RISK
- **Forcedness:** FREE-in-form, but read as a **gated-vs-ungated shrinkage contrast**, which is the diagnostic
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, both entry variants**; per-cell qualifying rule (a) on the ungated arm, (b) on the gated arm — the contrast is the finding)
- **Hit rate & denominator:** median `|est|/MDE` on `loss_severity_bps`, ungated fixed-distance settings (`M0.75 / M1.00 / M1.50`) vs the volatility rule (`STATE_LOW_075_HIGH_150`):

| Cell | ungated est/MDE | gated est/MDE | shrink factor |
|---|---|---|---|
| 021 ctrader | 13.37 / 11.57 / 2.02 | **1.20** | ~10× |
| 021 crypto | 1.56 / 1.18 / 1.97 | **0.84** | ~2× |
| 022 ctrader | 1.88 / 1.83 / 1.35 | **0.10** | ~18× |
| 022 crypto | 2.49 / 1.89 / 1.44 | **0.28** | ~7× |
| 023 ctrader | 2.13 / 0.77 / 1.05 | **0.96** | ~1.3× |
| 023 crypto | 3.07 / 2.20 / 1.61 | **0.26** | ~9× |

- **Effect:** metric = `loss_severity_bps`; gated median delta = **−0.065 to −3.60 bps**, against ungated medians of **−2.8 to −120.6 bps**; comparator = `FIXED_STOP_M1.00`.
- **Weakest qualifying cell:** 022 cTrader gated, est/MDE **0.10**, `effective_trade_blocks` median 29.
- **Significance standard:** magnitude (ratio to MDE stated per cell), with the sign stable on the ungated half.
- **Evidence snapshot:** 022 crypto gated: 65/250 resolving, 28 positive / 37 negative — sign not even stable. Ungated `M0.75`: 48/65 resolving, 48 negative.
- **Provenance:** `…/device_stop.parquet` | `estimate, mde, ci_low, ci_high` | `arm_class != 'FIXED_MANAGEMENT' and state == 'ORDER_CREATED' and metric_name == 'loss_severity_bps'`, split by `setting` | 27–583 rows per cell.
- **Conditioning required?:** the finding *is* the conditioning result — gating the device **shrinks** its effect 1.3–18× relative to the ungated form on the same device and universe. Per the standing habit, that is evidence **against** the conditional, not for it.
- **Failure modes checked:** unfair comparator (both halves share `FIXED_STOP_M1.00`), small-n (`effective_trade_blocks` medians 6–103; the 021 cTrader ungated cells sit at 34–59, above floor; the crypto `M1.50` cells sit at 3–8 and are **not** used to carry the claim, only the gated/ungated ratio), concentration, cost.
- **Actionability:** **KILL-AS-ALPHA** (as a volatility conditional) / **KEEP** (as ordinary risk tech: a tighter stop gives a smaller loss, which is not news)
- **Implication:** how far away the stop sits controls how much you lose; deciding that distance from a volatility state adds nothing on top.
- **Next use:** if stop distance is kept adaptive, the burden is to beat a *fixed* distance on the same population — this emission shows the gate itself buys nothing.

---

### [X-05] A vol-scaled trail does not capture more of the favourable move

- **Claim:** *refuted* — "scaling the trail by volatility captures a larger share of the favourable excursion."
- **Polarity:** REFUTE
- **Kind:** ECONOMIC (paired with the MECHANICAL reference `peak_giveback_bps` — Pre-test G, one item)
- **Forcedness:** FREE (`favourable_excursion_captured`), paired with FORCED-as-reference (`peak_giveback_bps`)
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, both entry variants**; per-cell qualifying rule (b))
- **Hit rate & denominator:** on identical rows, `peak_giveback_bps` resolves 48.5–73.3% at est/MDE 0.69–1.71; `favourable_excursion_captured` resolves **8/30, 45/261, 15/51, 101/434, 14/43, 110/462** (17.2–32.6%) at est/MDE **0.00–0.24**. Sign share across all finite rows: 30.7%, 33.3%, 36.7%, 48.6%, 39.1%, 42.4% positive — i.e. **a coin flip, drifting slightly negative**.
- **Restricted to the volatility rule** (`STATE_LOW_075_HIGH_150`): median est **−0.003 to −0.018** against median MDE 0.027–0.052, est/MDE **0.07–0.47**, 3–32 resolving of 12–200.
- **Effect:** metric = `favourable_excursion_captured` (a share, 0–1); median delta = **−0.018 to +0.000**; comparator = `FIXED_TRAIL_M1.00`.
- **Weakest qualifying cell:** 022 crypto, est/MDE **0.00**, `effective_trade_blocks` median **13** — below the 30 floor. **Stated exception:** the crypto trail cells run thin (`effective_trade_blocks` 13–15). The claim is carried by the cTrader cells (151, 13, 29) and 021 crypto (42); 022/023 crypto corroborate direction but do not meet the floor.
- **Significance standard:** interval standard, null clause.
- **Evidence snapshot:** 021 crypto `STATE_LOW_075_HIGH_150`: 14/96 resolving, **all 14 negative**, median est −0.018 vs MDE 0.052.
- **Provenance:** `…/device_trail.parquet` | `estimate, ci_low, ci_high, mde` | `arm_class != 'FIXED_MANAGEMENT' and state == 'ORDER_CREATED' and metric_name in {'peak_giveback_bps','favourable_excursion_captured'}`, row-identity join | 30 / 261 / 51 / 434 / 43 / 462 paired rows.
- **ECONOMIC — B-pre-1 baseline:** as §0.4; 022's baseline is a losing one.
- **ECONOMIC — B-pre-2 break-even spread:** the metric is a capture *share*, not bps; converting at the arm's own median realised capture, a −0.018 share shift on a ~7 bps capture is ~0.13 bps. `breakeven_spread_rt_bps ≈ 0.13`. Statement: *the effect is fully consumed at a round-trip spread of ~0.13 bps.* Label: **NON-EMITTED SCENARIO**.
- **Conditioning required?:** none — refuted ungated and gated.
- **Failure modes checked:** small-n (**flagged above, exception stated**), unfair comparator (shared `FIXED_TRAIL_*`), concentration, cost, lens mismatch.
- **Actionability:** **KILL-AS-ALPHA**
- **Implication:** a volatility-scaled trailing stop gives back more when it is wider — exactly as coded — but does not bank a larger share of the move.
- **Next use:** if a trail is retained, evaluate it against the *fixed* trail on capture share with `effective_trade_blocks ≥ 30` per cell; the current crypto trail cells cannot resolve it either way.

---

### [X-06] Nothing recoverable after a vol-adapted stop

- **Claim:** *refuted* — "adapting the stop to volatility changes how much price would have recovered after the stop (i.e. reduces avoidable stop-outs)."
- **Polarity:** REFUTE
- **Kind:** RISK
- **Forcedness:** FREE (`recovery_after_stop_bps`), paired with FORCED-as-reference (`adverse_excursion_bps`)
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, both entry variants**; per-cell qualifying rule (b))
- **Hit rate & denominator:** on identical rows, `adverse_excursion_bps` resolves 41.9–73.9%; `recovery_after_stop_bps` resolves **4/23, 46/292, 0/41, 51/492, 8/50, 77/492** — i.e. **0.0%–17.4%**, spanning the ~4.5% null rate. Sign share across all finite rows: 39.1%, 38.5%, 55.6%, 40.9%, 38.0%, 46.4% positive — a coin flip in all six cells.
- **Effect:** metric = `recovery_after_stop_bps`; median delta = **−3.59 to +0.04 bps**; median est/MDE = **0.01 – 0.33**; comparator = `FIXED_STOP_M1.00`.
- **Weakest qualifying cell:** 023 crypto, est/MDE **0.01**, `effective_trade_blocks` median 14 — below floor; carried by 021 cTrader (101) and 021 crypto (44). **Exception stated.**
- **Significance standard:** interval standard, null clause; 022 cTrader is a clean **0/41**.
- **Provenance:** `…/device_stop.parquet` | `estimate, ci_low, ci_high, mde` | as X-04 with `metric_name == 'recovery_after_stop_bps'` | 23 / 292 / 41 / 492 / 50 / 492 rows.
- **Conditioning required?:** none.
- **Failure modes checked:** small-n (exception stated), unfair comparator, concentration, cost.
- **Actionability:** **KILL-AS-ALPHA**
- **Implication:** the "my stop was too tight and the trade would have come back" story is not in this data — moving the stop with volatility does not change what happens after it fires.
- **Next use:** drop `recovery_after_stop_bps` as a justification metric for adaptive stops; it has never once resolved coherently here.

---

### [X-07] Vol-aware sizing reduces drawdown depth — direction is near-certain, size is under the floor

- **Claim:** *supported* — "sizing down in identified high-volatility states reduces drawdown depth." **Not** a claim about expectancy.
- **Polarity:** SUPPORT
- **Kind:** RISK
- **Forcedness:** FREE — the prompt's own worked example lists `drawdown_bps` as free ("smaller size need not reduce drawdown"; drawdown is path-dependent and could easily have gone the other way under `SCALE_NORMALISED`, and in one cell it does)
- **Consistency path:** **A2-MECHANISM** — stratum: *rows where the sizing rule actually binds on an identified state* (`setting ∈ {STATE_HALVE_HIGH, STATE_LOW_075_HIGH_150_ON_RANGE_SCALE, STATE_LOW_075_HIGH_150_ON_SHOCK}`), read against `FIXED_SIZE_UNIT`. Nameable a priori: SIZE acts on position scale, so it can only be read where the state gate changes the scale. **No multiplicity penalty.**
- **Hit rate & denominator:**
  - Of all CI-resolving rows in the stratum, the share on the drawdown-**reducing** side: 5/5, 41/41, 10/10, 108/108, 11/11, 61/61 — **236 of 236 resolving rows across 6/6 cells, zero on the other side.**
  - Denominator: 27 / 225 / 54 / 450 / 54 / 450 stratum-cells; resolution rate 13–24%.
  - Sign share across *all* finite rows (not just resolving): 93.3%, 78.8%, 95.0%, 82.6%, 95.0%, 78.3%.
- **A2 detail:** `strata_scanned = 5` (the five `setting` values of the SIZE device); `expected_FP = 5 × 0.045 = 0.23`; `sibling_check`: applying the same stratum definition to the SIZE device's *other* free metric, `concentration`, gives 50.0–80.0% positive-share — it does **not** light up the same way, so the stratum is not a generic artifact. **Leave-stratum-out parent:** removing the state-gated settings leaves `SCALE_NORMALISED` alone, where the direction **collapses** (023 crypto: 3 positive / 3 negative, median est −347). Parent collapses ⇒ report the stratum as the finding and **explicitly retract** any "vol-aware sizing reduces drawdown" claim stated at the device level — it is the *state-gated* form only.
- **Effect:** metric = `drawdown_bps` (baseline is negative, e.g. `FIXED_SIZE_UNIT` = −242.5 bps on EURUSD; a **positive** delta means a **shallower** drawdown); median delta = **+24.5 to +3,607 bps** depending on cell and rule; comparator = `FIXED_SIZE_UNIT`.
- **Weakest qualifying cell:** 021 cTrader `STATE_LOW_075_HIGH_150_ON_RANGE_SCALE`, est/MDE **0.20**, `effective_trade_blocks` **405**. Even the strongest cells sit at est/MDE **0.83–0.97** — **below 1 in every cell**.
- **Significance standard:** **near-universal directional** (Gate B standard 4), applied to the CI **side** of resolving rows rather than to the point estimate. Explicitly *not* the magnitude standard: median `|est|` is below median MDE everywhere. Under the measured null (≈4.5% resolution, symmetric sign) the probability of 236/236 resolving rows landing on one side is negligible; the probability that the *median row* clears MDE is what fails.
- **Evidence snapshot:** 022 crypto `STATE_LOW_075_HIGH_150_ON_SHOCK`: 25/50 resolving, 25 positive / 0 negative, median est +3,607 vs MDE 4,013 (est/MDE 0.90). 021 cTrader `SCALE_NORMALISED`: 2/3 resolving, both positive, est/MDE 0.83.
- **Provenance:** `…/device_size.parquet` | `estimate, ci_low, ci_high, mde, effective_trade_blocks` | `arm_class != 'FIXED_MANAGEMENT' and state == 'ORDER_CREATED' and metric_name == 'drawdown_bps'`, split by `setting` | 30 / 250 / 60 / 500 / 60 / 500 rows per cell.
- **Conditioning required?:** **yes** — the state gate must be on. Under continuous `SCALE_NORMALISED` the direction does not hold.
- **Failure modes checked:** concentration (holds in both universes and all symbol groups), small-n (`effective_trade_blocks` 287–654, comfortably above the 30 floor — the strongest-populated item in this ledger), zero-fill, unfair comparator (single shared comparator `FIXED_SIZE_UNIT`), leak (leave-stratum-out run and reported: parent collapses), cost (no bps edge claimed).
- **Actionability:** **PARK** — real, mechanism-consistent, but the median effect sits below the detectable floor and the item says nothing about expectancy.
- **Implication:** cutting position size when the volatility state flags high does make the worst stretches shallower — reliably in direction, but by an amount this run cannot size.
- **Next use:** if drawdown control is a design goal, this is the one lever with a consistent sign; a follow-up must be powered for **magnitude** (target `est/MDE > 1`, which needs roughly 1.2–8× the current effective blocks) and must compare state-gated against continuous scaling head to head.

---

### [X-08] Absorbing devices make their own rate metric unreadable, and TARGET emits no free metric at all

- **Claim:** *refuted* — "the emitted device rate metrics (`reach_rate`, `stop_rate`) can be used to compare a pure absorbing device against its fixed comparator."
- **Polarity:** REFUTE
- **Kind:** APPARATUS / STRUCTURAL
- **Forcedness:** FORCED-degenerate (re-entering as a first-class apparatus fact, per Gate B standard 3)
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes**; per-cell qualifying rule (c))
- **Hit rate & denominator:** `reach_rate` Δ **exactly 0.0000** on **47/47, 375/375, 58/58, 639/639, 60/60, 602/602** pure-TARGET arm rows — **100% in all six cells**, with `observed = comparator_observed = 1.000`. `stop_rate` Δ exactly 0 on **54/54, 530/538, 52/52, 576/583** in the four 022/023 cells (98.5–100%) and 15/27, 186/339 (≈55%) in the two 021 cells, where a competing target exit exists.
- **Effect:** metric = `reach_rate` / `stop_rate`; Δ = 0.0000 by construction — when the target is the only exit, every closed trade reached its target on both sides.
- **Significance standard:** structural / degeneracy across the full population.
- **Provenance:** `…/device_target.parquet`, `…/device_stop.parquet` | `estimate, observed, comparator_observed` | `metric_name in {'reach_rate','stop_rate'} and state == 'ORDER_CREATED' and arm_class in {'MANAGEMENT','MANAGEMENT_COMPONENT_COMBINATION'}` | 47–702 rows per cell.
- **Companion apparatus fact:** the TARGET device emits **no FREE metric**. `reach_rate` is degenerate; `time_to_target`, `realised_capture_bps` and `missed_excess_bps` are all monotone functions of target distance. TARGET therefore cannot enter a Pre-test G pair at all in this emission.
- **Actionability:** **METHOD**
- **Implication:** when a device is the only way out of the trade, "how often it fires" is always 100% on both sides — the number carries no information, and the target device has no outcome metric that could have come out either way.
- **Next use:** read absorbing-device rate metrics **only** where a competing exit exists (SPDR-021's target+stop arms). Any future adaptive-management emission must add at least one target metric that is not a function of target distance — otherwise TARGET is unfalsifiable by construction.

---

### [X-09] `TIME_DERANGEMENT` is exactly the real estimate — the control is vacuous here

- **Claim:** *refuted* — "the time-derangement control provides a null reference for the native origin-lens estimates."
- **Polarity:** REFUTE
- **Kind:** APPARATUS
- **Forcedness:** FREE
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes**; per-cell qualifying rule (c))
- **Hit rate & denominator:** joined to its paired real estimate on `symbol × entry_variant × arm_id × component`, the control value is **identical to the real value on 100.0% of rows** in every cell — 192 / 1,600 / 384 / 3,200 / 384 / 3,200 rows, median `|control − real|` = **3.5e-18 to 1.1e-16**.
- **Effect:** the derangement is **permutation-invariant** against an origin-lens mean; it cannot collapse anything.
- **Significance standard:** structural / identity.
- **Provenance:** `…/controls.parquet` | `estimate` | `control == 'TIME_DERANGEMENT'`, joined to `…/native_parameter_origins.parquet` | `estimate` | `state == 'ALL'`.
- **Contrast:** `MAGNITUDE_MATCH` is *not* vacuous, but is only weakly diagnostic — CI-exclusion rate 4.2%, 4.8%, 7.1%, 7.5%, 8.0%, 12.9% across the six cells, i.e. at or barely above the ~4.5% null rate.
- **Actionability:** **METHOD**
- **Implication:** shuffling the timing and re-measuring gives back the exact same number, so this control has never tested anything on this estimand — it is not a passing control, it is an absent one.
- **Next use:** replace it. A causal-alignment break (as ratified for the fold kernel) is required; a permutation against a mean statistic is provably invariant and must not be re-emitted as a control.

---

### [X-10] The pooled cTrader native number is one symbol

- **Claim:** *refuted* — "the pooled cTrader native origin-lens estimate describes the cTrader substrate."
- **Polarity:** REFUTE
- **Kind:** APPARATUS (concentration / leak)
- **Forcedness:** FREE
- **Consistency path:** **A2-MECHANISM** — stratum: *cTrader native origin-lens rows, split by symbol*. Nameable a priori (3 symbols, wildly different vol scales, no pooling weight applied).
- **Hit rate & denominator:** SPDR-021 cTrader: **11 of 13** interval-excluding rows are XAUUSD, **all 11 negative** (the other 2 are USTEC, both positive), out of 192 rows. SPDR-022 cTrader: 8/17 XAUUSD (all negative), 7 USTEC (all positive), 2 EURUSD. SPDR-023 cTrader: 6/10 XAUUSD (all positive).
- **A2 detail:** `strata_scanned = 3` (three symbols); `expected_FP = 3 × 0.045 = 0.14`; `sibling_check` = yes, the same concentration appears in the sibling experiment with the sign flipped, which is X-01 not an independent effect. **Leave-stratum-out parent:** SPDR-021 cTrader pooled mean **−0.00851 → +0.01910** with XAUUSD removed — **the sign flips**; removing USTEC instead gives −0.03855. Parent **collapses**. The pooled number is retracted as a substrate-level statement.
- **Significance standard:** structural (leave-one-out sign reversal).
- **Provenance:** `python/experiments/SPDR-021/results/analysis/ctrader/native_parameter_origins.parquet` | `estimate, ci_low, ci_high, symbol` | `arm_class != 'FIXED_NATIVE' and state == 'ALL'` | 192 rows, 13 resolving.
- **Failure modes checked:** this item *is* the leak check for the other native items; X-01 and X-02 are unaffected because both are exact identities that hold symbol by symbol.
- **Actionability:** **METHOD**
- **Implication:** three instruments is not a substrate — one of them decides the pooled sign, and dropping it flips the answer.
- **Next use:** never report a pooled cTrader native figure without the leave-one-symbol-out table beside it. Do not treat XAUUSD's behaviour as an independent conditional either — it is the pooled number, not a stratum within it.

---

### [X-11] Capping hold time on top of a level exit destroys value

- **Claim:** *refuted* — "adding a bar-count hold cap on top of a target or trail exit is value-neutral."
- **Polarity:** REFUTE
- **Kind:** ECONOMIC
- **Forcedness:** FREE
- **Consistency path:** A1 GLOBAL (shape: **6/6 cells, 2/2 substrates, 2/2 universes, both entry variants**; per-cell qualifying rule (a) — majority of rows resolve on the same side)
- **Hit rate & denominator:** device-combination arms `DC_TRAIL_HOLD` and `DC_TARGET_STOP_HOLD` (`setting = M1.00` in `device_hold`), measured on `outcome_by_time_bps` against `FIXED_TRAIL_M1.00` / `FIXED_TARGET_M1.00`: resolving **6/6, 44/48, 10/10, 89/100, 10/10, 86/100** — and of those, negative on **6/6, 44/44, 10/10, 89/89, 9/10, 85/86**.
- **Effect:** metric = `outcome_by_time_bps`; median delta = **−4.41, −60.05, −7.93, −58.36, −5.84, −51.87 bps**; median est/MDE = **2.50, 2.40, 2.82, 2.11, 2.14, 2.15**.
- **Weakest qualifying cell:** 022 crypto, est/MDE **2.11**, `effective_trade_blocks` median **26** — **below the 30 floor**, as is 023 crypto (28). **Exception stated:** the two crypto breach cells do not meet the effective-count floor; the claim is carried by 021 cTrader (170), 021 crypto (56) and 022/023 cTrader (45, 45), with the crypto breach cells corroborating direction only.
- **Significance standard:** interval standard — majority resolve, same side, median `|est|` ≈ 2.1–2.8× MDE.
- **Evidence snapshot:** 021 cTrader per-symbol: EURUSD `DC_TRAIL_HOLD` −4.29 (MDE 2.10, n=81), `DC_TARGET_STOP_HOLD` −3.65 (MDE 0.84, n=83); XAUUSD −4.54 / −6.50; USTEC −4.02 / −7.38. All six negative, all resolving.
- **Provenance:** `…/device_hold.parquet` | `estimate, ci_low, ci_high, mde, comparator_observed` | `setting == 'M1.00' and metric_name == 'outcome_by_time_bps' and state == 'ORDER_CREATED'` | 6 / 48 / 10 / 100 / 10 / 100 rows.
- **ECONOMIC — B-pre-1 baseline:** comparator's own level `comparator_observed` = +3.02 to +9.52 bps on 021 cTrader; the fixed native baseline is +0.74 / +5.09 bps (021) and **negative** (−0.31 to −2.58 bps) on 022. On 022 the combination makes a losing baseline lose more.
- **ECONOMIC — B-pre-2 break-even spread:** both arms close once per paired origin (paired on common closes, 1:1 turnover), so spread cancels in the difference; the loss is **not** a cost artifact. Charged one-sided, `breakeven_spread_rt_bps = 4.4 – 60.1`. Statement: *this effect would require a round-trip spread of 4.4–60 bps to be explained away by cost, which is far above any plausible spread on these instruments.* Label: **NON-EMITTED SCENARIO**.
- **Conditioning required?:** none.
- **Failure modes checked:** **unfair comparator — flagged.** A device *combination* is being differenced against a *single-device* comparator, so part of the gap is "two devices vs one", not "the hold cap specifically". The closed population is paired on common closes (`common_close_n` 81–367 on 021 cTrader), so it is not selected by the exit being measured. Also checked: small-n (**exception stated above** — 022/023 crypto at 26/28 are below the 30 floor; the other four cells run 45–170), concentration (all three cTrader symbols and both combination arms agree), cost (see above).
- **Actionability:** **PARK** (real and consistent, but the comparator is not like-for-like; needs a `TRAIL + HOLD` vs `TRAIL` comparison holding device count fixed)
- **Implication:** forcing trades out on a bar count when a target or trail was already going to close them costs several basis points a trade, everywhere we looked.
- **Next use:** before any combination arm is designed again, define a comparator with the same number of devices. Then re-ask whether the hold cap specifically, or just "more devices", carries the loss.

---

## 3. Regime / conditioning map

Only Gate A+B survivors. `—` = not separable on this emission.

| Effect | LOW | HIGH | SHOCK | continuous (`SCALE_NORMALISED` / `M*`) | symbol | entry variant |
|---|---|---|---|---|---|---|
| X-02 native geometry → trade value (null) | — | — | — | zero on all forms | uniform (exact) | uniform (exact) |
| X-03 hold length → trade value (null) | null | null | null (`STATE_SHOCK_2` est/MDE 0.01–0.20) | **resolves negative** only when compared against a *level* exit (see X-11) | uniform | uniform |
| X-04 stop distance → loss severity | gated est/MDE 0.10–1.20 | same | gated-on-SHOCK est/MDE 0.43–1.61 | **ungated est/MDE 1.05–13.37** | uniform | uniform |
| X-05 trail → capture share (null) | null | null | null | null | uniform | uniform |
| X-06 recovery after stop (null) | — | — | — | null | uniform | uniform |
| **X-07 sizing → drawdown depth** | binds only via the gate | **direction holds, 236/236 resolving rows** | **strongest cells: est/MDE 0.80–0.97** | **collapses** (023 crypto 3 pos / 3 neg) | holds both universes | holds both |
| X-10 pooled cTrader native | — | — | — | — | **XAUUSD decides the sign** | — |

**Mandatory statement on realised regime.** This emission **gates arms** by volatility state; it does **not stratify outcomes** by realised volatility state. The only `state` values carried into the analysis artifacts are episode-lifecycle labels — `ORDER_CREATED`, `NO_EVENT`, `NO_FEATURE`, and on 022/023 additionally `CENSORED`, `EVENT_UNDECIDED`, `INCOMPLETE` (`state_sections.parquet`, `per_stratum_estimates.parquet`, `native_parameter_origins.parquet`). There is no `vol_state` / `regime` column anywhere in the six cells' artifacts.

Consequence: **"does the edge live in high-volatility regimes?" is unanswerable on this emission** and does not belong in the ledger. The only regime information available is *which arm was active*, which confounds the rule with the state. A future run must emit a **realised** regime label per origin and per trade, assigned from information available at decision time, so outcomes can be cut by regime independently of the arm that was running.

---

## 4. Explicitly dropped

| Slice | Reason |
|---|---|
| `missed_excess_bps` (TARGET, all cells) | `FORCED` — monotone in target distance |
| `realised_capture_bps` (TARGET, all cells) | `FORCED` — monotone in target distance; 49.8–84.9% hit rate is the rig, not a finding |
| `time_to_target` (TARGET) | `FORCED` |
| `decay_bps`, `opportunity_duration` (HOLD) | `FORCED` — reported in §1 and as X-03's reference half |
| `risk_dispersion`, `tail_loss_bps` (SIZE) | `FORCED` under `STATE_HALVE_HIGH` |
| `adverse_excursion_bps` (STOP), `peak_giveback_bps` (TRAIL) | `FORCED` — reference halves of X-06 / X-05 |
| `concentration` (SIZE) | `BELOW_MDE` — est/MDE 0.00–1.26, sign share 50–80%, no stratum survives; positive-share is stable in 022/023 but those are one substrate (X-01) |
| `loss_tail_bps` (TRAIL) | `BELOW_MDE` — 14.7–35.3% resolving, mixed sign in every cell |
| `holding_efficiency` (HOLD) | `NOT_EMITTED` in practice — finite on 2/90, 97/750, 15/321, 150/2535, 18/321, 156/2535 rows (2–20%) vs 50% for `outcome_by_time_bps` on the same table |
| `payoff_scale_ratio` (selection checks) | `NOT_EMITTED` — **0 finite values of 9,100 rows** across all six cells |
| `spread_cost_status`, `cost_scope`, `spread_rt_bps`, `partial_cost_mean_bps` (per-stratum) | `NOT_EMITTED` — all null / 0 finite on 903–19,961 rows per cell; the disclosure exists only in `run_summary.json` and `config.json` and is **not carried into the analysis artifacts** |
| `TIME_DERANGEMENT` control | `NON_DIAGNOSTIC_CONTROL` — see X-09; named once, not re-derived |
| `MAGNITUDE_MATCH` control | `NON_DIAGNOSTIC_CONTROL` (weak) — 4.2–12.9% CI-exclusion, at/near the 4.5% null rate; no bin ordering survives |
| Native `BAND_Z` / `BAND_Z+BAND_H` trade-lens means | `LEAK` — top 1% of `\|Δ\|` pairs carry **15.4%, 29.4%, 17.7%, 45.6%** of the summed delta, all reinforcing the bulk sign; combined with X-01 the mean is a direction artifact concentrated in a few pairs |
| Per-symbol native conditionals on cTrader | `LEAK` — see X-10; leave-one-out flips the pooled sign |
| Crypto TRAIL and STOP device cells | `SMALL_N` where `effective_trade_blocks` medians run 13–16; used only for direction corroboration in X-05 / X-06, never to carry a claim |
| `NO_EVENT` / `NO_FEATURE` / `CENSORED` / `INCOMPLETE` state rows | `SMALL_N` — `common_close_n = 0`, all estimates NaN by construction; excluded from every rate above |
| Component-level ranking (RANGE_SCALE vs SWING_SCALE vs LEVEL_* vs SHOCK vs TAIL_RISK) | `NO_STRATUM` — scanned across all five device families and both lenses; no component reaches the qualifying rule in ≥4 cells on any FREE metric |

---

## 5. Probe log

All probes read-only; no canonical artifact was modified. Scripts under `python/experiments/SPDR-021/analysis_code/`. No seeds used (no resampling performed — all CIs/MDEs were read as emitted).

| Script | What it computes | Artifacts read | Filters | Rows |
|---|---|---|---|---|
| `xtract_p1_rates.py` | per-cell interval-exclusion and `\|est\|>MDE` rates; same split by metric; native origin- and trade-lens rates | `device_{target,stop,trail,hold,size}.parquet`, `native_parameter_origins.parquet`, `per_stratum_estimates.parquet` (6 cells) | finite `estimate/ci_low/ci_high`; `arm_class != FIXED_*`; `state == 'ORDER_CREATED'` (devices) / `'ALL'` (native) | 658–10,708 device; 192–3,200 native |
| `xtract_p2_native.py` | share of shared-trade paired deltas exactly zero, by parameter; top-1% concentration of summed delta and its sign; origin-lens hit rate by parameter | `native_parameter_shared_trades.parquet`, `native_parameter_origins.parquet` | `paired_outcome_delta_bps.is_not_null()`; `\|Δ\| > 1e-12` for concentration | 72,477–1,743,705 |
| `xtract_p3_mirror.py` | SPDR-022 vs SPDR-023 Pearson r and opposite-sign share on the origin lens and the aggregated trade lens; median `\|est_022 + est_023\|` | both experiments' `native_parameter_origins.parquet`, `native_parameter_shared_trades.parquet` | join on `symbol, entry_variant, arm_id, component, parameter, orientation, state='ALL'` | 384 (ctr), 3,200 (cry) joined |
| `xtract_p4_devices.py` | Pre-test G forced/free contrasts on identical rows | all five `device_*.parquet`, 6 cells | inner join of the FORCED and FREE key sets on the 8-key row identity; `state == 'ORDER_CREATED'`; `arm_class != 'FIXED_MANAGEMENT'` | 23–673 paired rows per family/cell |
| `xtract_p5_signs.py` | CI-side split (pos/neg) of resolving rows for nine FREE metrics; fixed-native baseline dump | `device_*.parquet`, `per_stratum_estimates.parquet` | as above; baselines `arm_class == 'FIXED_NATIVE'` | 23–739 per metric/cell |
| `xtract_p6_setting.py` | FREE metrics split by `setting` (gated vs ungated vs continuous) | `device_{size,hold,stop,trail}.parquet` | as above, grouped by `setting` | 3–450 per setting/cell |
| `xtract_p7_misc.py` | all-row sign shares; control diagnosticity; `TIME_DERANGEMENT` vs paired real estimate; leave-one-symbol-out pooled native means; per-variant baselines | `device_*.parquet`, `controls.parquet`, `native_parameter_origins.parquet`, `per_stratum_estimates.parquet` | controls joined on `symbol, entry_variant, arm_id, component` | 192–12,800 |
| `xtract_p8_struct.py` | absorbing-device Δ-exactly-zero counts; `payoff_scale_ratio` / `holding_efficiency` population; per-stratum cost-column population | `device_{target,stop}.parquet`, `selection_checks.parquet`, `device_hold.parquet`, `per_stratum_estimates.parquet` | `arm_class in {MANAGEMENT, MANAGEMENT_COMPONENT_COMBINATION}` for degeneracy | 27–702 / 195–3,250 / 903–19,961 |
| inline (bash) | integrity + estimand `blocking_pass` per run; spread disclosure; `state_sections` state vocabulary; per-symbol 022/023 baseline mirror | `data/nautilus_runs/<run>/{integrity_selfcheck,estimand_validation,run_summary,config}.json`, `state_sections.parquet` | — | 6 runs |

Reproduction hashes for the analysis stage: `python/experiments/SPDR-02{1,2,3}/results/analysis/reproduction-hashes.json`.

---

## 6. Operator handoff

**What's solid enough to carry forward (KEEP / METHOD):**
1. The two breach screens are the same trades with the sign flipped — their fixed baselines cancel to zero exactly, symbol by symbol. Treat them as **one** substrate, never two. (X-01)
2. Native **admission rules** (threshold, expiry, band `H`) change *which* trades happen, never *what the shared ones are worth* — exactly zero on ~2.3 million paired trade rows. Read them on the origin lens only. The price-offset parameter `BAND_Z` is the exception and does move outcomes. (X-02)
3. The time-derangement control returns the identical number to the real estimate on 100% of rows in all six cells. It has never tested anything; replace it before the next run. (X-09)
4. Three cTrader instruments is not a substrate: dropping XAUUSD flips the pooled native sign. (X-10)

**Strongest refutes of an alpha hope (KILL-AS-ALPHA):**
5. Volatility-gated **hold length** moves elapsed time exactly as coded and moves trade value not at all — 6/6 cells, effect 0.03–0.60× the detection floor. (X-03)
6. Volatility-gated **stop distance** does not carry the loss-severity effect — gating **shrinks** it 1.3–18× versus the plain fixed distance. (X-04)
7. Volatility-scaled **trail** gives back more when wider, and banks no larger share of the move. (X-05) Nothing recovers after a vol-adapted stop either. (X-06)

**Worth a dedicated follow-up (PARK):**
8. **Sizing down in flagged high-volatility states makes drawdowns shallower** — 236 of 236 resolving rows on one side across 6/6 cells, on the best-populated device in the study. But the median effect is below the detection floor everywhere (est/MDE 0.20–0.97), and it collapses under continuous scaling. This is the one lever with a consistent sign, and it needs a magnitude-powered rerun, not another direction check. (X-07)
9. Hold caps stacked on level exits cost 4–60 bps a trade in all six cells — but the comparator is a single-device arm, so redo it with device count held fixed. (X-11)

**What I deliberately did not claim:** no experiment verdict, no family disposition, no deployability; no net or cost-complete statement (spread is uncharged in every cell); no regime conclusion — this emission gates arms by volatility but never labels realised regime, so the regime question is unanswerable here; no TEST/holdout was opened; no component ranking, because none reached the qualifying rule in ≥4 cells.
