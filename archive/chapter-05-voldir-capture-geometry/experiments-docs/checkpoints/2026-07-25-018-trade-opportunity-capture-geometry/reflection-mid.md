# Checkpoint 018 — Mid-checkpoint Reflection: the confirmed evidence base

- **Assembled:** 2026-07-26 · **Consolidated 2026-07-30**
- **What this document is:** the single inventory of what checkpoint-018 has confirmed through
  `SPDR-018B`, each observation carried with its own evidence class, universe, horizon, effect size
  and source, and each mapped to the adaptive-management decision it is licensed to inform.
- **What this document is NOT:** it selects **no next experiment**, names **no replacement
  identifier**, prescribes **no test grid or protocol**, and adopts **no universal outcome measure**
  across management devices. It takes no end-state, no family action and no gating verdict.
- **Status:** **EVIDENCE INVENTORY APPROVED BY OPERATOR 2026-07-30.** This document remains evidence
  only; the separately approved replacement design is `adaptive-management-design.md`.
- **History note (2026-07-30).** This file consolidates two mid-checkpoint documents into one. The
  second document's evidence inventory is retained above; its prescription — a scale-free payoff
  residual as the common target across every device, plus a bundled layer-by-layer test protocol —
  was the contamination point and is **withdrawn**, together with the sequencing authorisation the
  former §9 signed. Two capture designs built on that prescription were removed from the programme
  the same day and their identifiers permanently voided; recovery is via Git history only.
- **Family:** `CF-VOLDIR-001` — `REGISTERED`, unchanged. Transitions are retrospective-only.
- **Authority:** checkpoint-018 `design.md` §5 Step 2; SoT `.ignore/what-next/alts/opportunity.md`;
  chapter-06 governance.
- **Binding sources (final, not re-run here):** SPDR-012, SPDR-013, SPDR-015 (checkpoint-017);
  `SPDR-018` (crypto, 25 Bybit perps) + `SPDR-018B` (cTrader replication), with addenda P02/P03 and
  P04; checkpoint-017 `retrospective.md`; `corrections-log.md` (independent adversarial audit
  2026-07-26, **RELIABLE WITH CORRECTIONS**; both verdicts survive).
- **Inventory audit (2026-07-30):** high-consequence counts, baseline statistics, mirror
  relationship, powered exit coverage and breach-type medians were re-derived from the surviving
  cell-level emissions by `SPDR-018/analysis_code/a07_reflection_inventory_audit.py`. Source
  documents were then checked claim by claim. Corrections from that audit are incorporated here.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY  (cTrader: BORROWED from Bybit AND RESCALED = DOUBLY SYNTHETIC)
  implication: every money figure understates true cost; reported net is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  SPREAD: NEVER CHARGED, PROGRAMME-WIDE (2026-07-23, evaluation-framework.md SSChapter-04) -
    a standing exclusion with a travelling caveat, not a pending pin
```

---

## 0. The 20-second version

**We know a great deal about how big the next move will be, and essentially nothing usable about
which way it goes.** That asymmetry is measured on two asset classes, not asserted.

**The aggregate mean sits near gross break-even; the typical cell does not.** Across 25 crypto
perps and, independently, three cTrader instruments, the mean is close to the gross zero line, but
the crypto median and trimmed mean are about **12–14 bps below it**. **Not one powered cell out of
1,728 clears even the disclosed partial-cost floor.** In the mean decomposition, cost accounts for
**91–96% of the disclosed gap**; this does not erase the negative cell tail.

**Payoff asymmetry is not a free lever.** `W/L` is ~97% the arithmetic mirror of the win rate: push
one, the other moves back by almost exactly the offsetting amount, and the average trade does not
improve. This replicated on the second asset class more tightly than on the first.

**Two questions remain genuinely open, and neither is a "no".** Shock-conditioned momentum (C2) and
the ordered volatility-flip conditioner (C3) are **unpowered / unpowerable, not refuted**.

**What follows is an inventory, not a plan.** Section 4 states plainly that no next experiment and
no universal outcome measure is selected here.

---

## 1. Rules for reading this inventory (binding)

1. **Units before magnitudes (L-21, L-50, P-21).** σ̂ is **73.00 bps** pooled TRAIN on crypto and
   **13.03 bps** on cTrader — a 5.6× difference. **No bps threshold in this document crosses a
   universe boundary.** State targets in σ̂ or ATR units, or re-derive per universe.
2. **Powered means powered against a block MDE (M-1)**, never an iid `2.8σ/√n` form.
3. **Powered-subset magnitudes need the three-number selection check first (L-51, P-22):**
   payoff-scale ratio powered÷excluded, sign-share differential, mean-vs-median gap in the excluded
   set. Worked failure: ten `trail` cells at +7…+23 bps drawn from 116 excluded cells averaging
   **−27.6 bps**.
4. **A magnitude-matched (M-3) percentile is uninterpretable** without the comparator's own mean,
   its null quantiles and its plant curve (P-24).
5. **cTrader is replication credibility, never power.** Its `n` is never pooled; its power counts
   are not comparable to crypto's (different precision base).
6. **Unpowered is not negative (B-5).** Section 3 items are power statements only.
7. **Medians are the headline** on every P&L-adjacent quantity (fat-tailed family); where mean and
   median disagree, both are given.

### 1.1 Evidence classes

Every row below carries exactly one class, and the class limits what may be built on it.

| Class | Meaning | What it licenses |
|---|---|---|
| **[P] powered confirmation** | The cell clears its own block MDE (M-1) at parent target precision | Parameterisation, thresholds, pre-registered predictions |
| **[S] informative but not powered** | Scored and SUPPORTED, but no bps target rule attaches | Design inputs and ordering claims; **not** a magnitude threshold |
| **[D] descriptive only** | Disclosure layer — emitted for context, never adjudicated | Interpretation and sanity checks. **Never a parameter source** |
| **[U] unresolved** | Measured, below target precision, or terminally unpowerable | Direction-of-travel only. **Never a claim, never a threshold** (B-5) |

---

## 2. Confirmed observations, by the management decision they can inform

### 2.0 Summary map

| Confirmed information | Permitted adaptive-management use |
|---|---|
| forecast next-move scale and distribution | set candidate target and stop distances; stratify opportunity size |
| slow volatility level / state persistence | define the time scale over which management settings may remain valid |
| fast shock state and decay | define short-lived entry / management response windows |
| next-swing-bigger-than-current classification | select or stratify opportunities; **never** assume directional edge |
| tail-exceedance probability | risk limits, target / stop reach probabilities, size restraint |
| direction findings | measure as context; **do not** treat volatility scale as directional information |
| `p`, `W`, `L`, cost-floor findings | describe the baseline economic object; prevent edge-manufacturing claims |

**No fitted score, layer stack, capture policy or test grid belongs in this inventory.**

### 2.1 Forecast next-move scale and distribution
*Licensed use: set candidate target and stop distances; stratify opportunity size.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **V1** | Range-based volatility level forecasts next-move size | **[P]** | crypto 25 perps; H1 and H4 | rank IC **0.338 (H1)** / **0.301 (H4)**; re-measured per-symbol median **0.3262**, **165/165 cells CI-excluding-zero** (68.9% of those also meet parent target precision — not the same label); pooled H1 0.421–0.434. cTrader **IC +0.228**, replicates smaller | SPDR-012 V-LEVEL; SPDR-018 A-IC |
| **V2** | The fitted V-LEVEL forms tie — EWMA is enough | **[S]** | crypto; H1/H4 | ridge / HAR / EWMA are indistinguishable on the intraday V-LEVEL task; HAR is weakest and collapses at D1 | SPDR-012 V-LEVEL |
| **V3** | Range measures beat close-to-close | **[S]** | crypto; D1 and intraday | **+0.09…+0.13 IC at D1**; mechanism is window-length staleness, not overnight or coverage | SPDR-012 V-MEASURE / §6 |
| **V4** | The usable clock is day-scale, never hour-to-hour | **[P]** | crypto; H1 vs H4 vs D1 | fit-free IC H1 **0.305** > H4 0.255 > D1 0.173; H1−D1 **+0.148 [+0.109, +0.183]**, positive 20/20 symbols. **Within-day IC +0.024 (H1), −0.116 (H4)** | SPDR-012 §5.1 / §5.3 |
| **V5** | The forecast rescales the **entire** distribution, not just its middle | **[S]** | crypto; H1 CONFIRM | decile 10 / decile 1 mean **3.71**, monotone 9/9 steps; tail rate (next > own P90) **0.017 → 0.304 = 18×**; top-vs-bottom quintile mean 2.86 / median 2.93 / P90 2.92 — agree to two decimals | SPDR-012 §3.3 |
| **V6** | The effect is homogeneous across the universe | **[P]** | crypto; H1/H4 (not D1) | CONFIRM H1 **I² = 0.00**, cross-symbol sd 0.022 vs median SE 0.024. **D1 I² = 0.79** | SPDR-012 §3.4 |
| **V7** | Next-swing magnitude is forecastable (continuous) | **[P]** | crypto; ZigZag 2.0×ATR(14) events | OOS rank IC **0.34–0.46, all 25 symbols** | SPDR-013 §7 |

**What this licenses.** Scale is the primary input for **how far** to place a target or stop and for
**stratifying** opportunity size. Because the whole distribution rescales (V5), any quantile-defined
distance may legitimately be expressed as a multiple of the forecast. One parameterisation may be
shared across the universe on H1/H4, **not** on D1 (V6). Refresh day-scale (V4).

### 2.2 Slow volatility level and state persistence
*Licensed use: define the time scale over which management settings may remain valid.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **V8** | `V-REGIME` (rolling-median split of rv20) is a slow **level** classifier | **[S]** | crypto; H1/H4/D1 | flags ~48% of bars; mean run length **18.6 / 16.3 / 13.2 bars**; `P(HIGH\|HIGH)` **0.946 / 0.939 / 0.931**; `rv20` alone reproduces it at AUC 0.807 | SPDR-012 §3.5 |
| **V11** | HMM HIGH−LOW next-move size gap — the 017 76/83-unpowered blocker, now powered | **[P]** | crypto; D1/H4/H1 | pooled TRAIN **D1 +180.4 [119.7, 252.1]**, **H4 +67.5 [54.7, 80.6]**, **H1 +48.0 [41.7, 54.7]**; second variant set gives D1 +100.1 / H4 +34.3 / H1 +18.1 → **honest H1 range +18…+48 bps**; per-symbol H1 median **+24.7**, 97.3% CI-excluding-zero. cTrader **+6.88 bps**, replicates in sign at a smaller absolute magnitude | SPDR-018 **A1** |
| **V12** | Level-arm gaps are flat in **relative** terms across clocks | **[S]** | crypto; all bands × clocks | V-REGIME gap ÷ own mean \|move\| = **0.216–0.282** everywhere; HMM relative gap 0.65–0.90 (H1) | SPDR-012 §5.2 / §3.5 |
| **V13** | Daily level-regimes are ~94% persistent | **[S]** | crypto; D1 | `p_stay` median **0.9486** CONFIRM / 0.9376 DESIGN / 0.9365 TRAIN, range 0.866–1.000, 22/25 SUPPORTED (60 SUPPORTED / 14 UNPOWERED / 1 NOT_RESOLVABLE across cells). cTrader **0.9517** | SPDR-018 **D7** |
| **V14** | Regime run-length is predictable only weakly, and the error is quantified | **[D]** | crypto; H1/H4 | H1 median MAE **11.95–12.00 bars** against a predicted `E[run]` of **18.9–23.1**; H4 10.9–11.3 vs 17.8–21.1. **Typical error ≈ half the quantity predicted** | SPDR-018 **D2** (262/300 cells DISCLOSURE, 38 UNPOWERED) |
| **V15** | Multi-bar volatility-state transitions beat persistence; single-bar does not | **[P]** | crypto; H1 | ΔBrier vs persistence: k=1 **0.0000 / −0.00049 (inert)**; k=4 **−0.0199**; k=12 **−0.1085**, 57–59% CI-excluding-zero. cTrader independently reproduces only the k=1 inert read; its −0.0256 result belongs to a different verification slice and is not a like-for-like magnitude | SPDR-015 arm 2a (16/16 coins); SPDR-018 **D5**; SPDR-018B **D5/D8** |
| **V16** | `R-HMM-RV` as a forecaster is real but weak | **[P]** | crypto; H1 | ΔBrier k=1 −0.00135, k=4 −0.00595, k=12 −0.0317; 36–47% CI-excl-0 — **~one third of R-MARKOV at matched k** | SPDR-018 **D6** |

**What this licenses.** The slow level state sets **how long a management setting can be expected to
remain valid** — runs of 13–19 bars on H1, ~94% daily persistence. `E[run]` is a **scale**, never a
timer: the typical prediction error is about half the predicted quantity (V14). Multi-bar transition
gating (k=4/12) is the supported state read; **k=1 is refused as inert**.

### 2.3 Fast shock state and decay
*Licensed use: define short-lived entry / management response windows.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **V9** | `V-REGIME-HMM` is a single-bar **shock detector**, not a regime model | **[S]** | crypto; H1 | flags 5–13% of bars; run length **~2 bars**; `\|r_t\|` alone reproduces it at **AUC 0.95–0.98**; the two arms agree only 51–62% ≈ independence | SPDR-012 §3.5 |
| **V10** | Shock carries almost all the joint size information; the slow level adds ~14%, and only when no shock just fired | **[S]** | crypto; H1 CONFIRM | 2×2 on next \|move\| bps: HMM-HIGH 95.0 / 94.9 regardless of the level arm; within HMM-LOW the level arm adds **+6.3 on 45.5 (+14%)** | SPDR-012 §3.5 |
| **V23** | `mag_high` is "the decision bar was large", not "the volatility state" | **[D]** | crypto; cTrader | M-3 magnitude-matched: live −11.607 vs comparator −10.704, **percentile 0.46**, gap 0.90 bps. cTrader live −3.402 vs −2.068, pct 0.2735 | SPDR-018 §5 |

**What this licenses.** Shock is a **separate, near-orthogonal fast axis** with a ~2-bar life — the
natural scale for a short-lived response window (e.g. how long a pending order stays live). Condition
on shock **first**, level second (V10). Never treat shock as a regime. **Any conditioner defined on
`|r_t|` requires a magnitude-matched comparator (V23, M-3 mandatory).**

### 2.4 Next-swing-bigger-than-current classification
*Licensed use: select or stratify opportunities. **Never** assume directional edge.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **V17** | `T-GT-CUR` — "is the next swing bigger than the current one" | **[P]** | crypto; 1,800 never-before-scored CONFIRM cells, n = 5,698 | hit **0.6465 [0.6247, 0.6678]** (`ar1_threshold`), **0.6999 [0.6831, 0.7176]** (`logit_ridge`), **0.6781 [0.6589, 0.6978]** (`ridge_cont`) vs base **0.4674**. **All three CIs sit 16–23 points above base and do not approach it.** The most robust positive object in either run | SPDR-018 **D8**; SPDR-015 2b (21/21 coins × 3 models, +0.21 over base) |
| **V18** | `T-GT-MED5` is the strongest ordinal target | **[P]** | crypto | `ridge_cont` **+0.107** CONFIRM / +0.102 TRAIN / +0.096 DESIGN; hit **0.585 vs base 0.483**, 21/26 SUPPORTED on CONFIRM | SPDR-018 **D4** |
| **V19** | `T-GT-MED10` resolves with a smaller, real lift (017 called it INCONCLUSIVE) | **[P]** | crypto | `ridge_cont` **+0.063** / `logit_ridge` +0.058 / `ar1_threshold` +0.048 | SPDR-018 **D3** |

**What this licenses.** A **selection / stratification** gate: take or rank the opportunity when the
next swing is forecast larger. It is a **size** statement, not a direction statement, and carries
**no signed term** — it may never be read as a directional edge.

### 2.5 Tail-exceedance probability
*Licensed use: risk limits, target / stop reach probabilities, size restraint.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **V20a** | Tail exceedance lifts with the vol state | **[P]** | crypto; H1 | median **+0.056 (p90)** / **+0.031 (p95)**, **90.9%** of per-symbol cells CI-excluding-zero; extreme-move rate ~1.8× in the high-vol state | SPDR-018 **A2**; SPDR-012 V-TAIL |
| **V20b** | The cTrader tail read is unresolved | **[U]** | cTrader | **+0.0095**, 8.3% CI-excluding-zero, all 72 WASH. This neither replicates nor refutes V20a and supplies no portable magnitude | SPDR-018B **A2** |

**What this licenses.** A **probability** input to risk limits and to the chance a given target or
stop distance is reached. Not an expectancy input.

### 2.6 Direction findings
*Licensed use: measure as context. **Do not** treat volatility scale as directional information.*

| # | Observation | Class | Universe / horizon | Effect size | Source |
|---|---|---|---|---|---|
| **DIR-1** | Unconditional / trend direction is dead on net | **[P]** | crypto | SPDR-013: **0 of 2,940 SUPPORTED**; availability ambient (`sig_over_rand` 0.95–1.03) | SPDR-013 |
| **DIR-2** | The sides carry real directional information, and it points **against** the registered direction | **[P]** | crypto; cTrader | arm-C side-derangement live **−12.221 bps at percentile 0.0065** (cTrader −2.632 at 0.023, ~1/5 the magnitude on a 1/5.6-σ universe) | SPDR-018 §5; SPDR-018B R8 |
| **DIR-3** | The powered counter-outcome: the negative tail is strongly enriched, but flipping it does not route | **[P]** | crypto | **130 of 1,413** powered cells have a gross-mean CI excluding zero — **129 negative, 1 positive** (expectation ~35 per tail under a null: positive tail **depleted**, negative tail **enriched ~3.7×**). Median −4.12, max \|effect\| 12.93 bps. Flipped: **0 of 129** clear even the partial cost floor; best flipped net **−0.65 bps**. cTrader has **no enriched tail** (12 neg / 2 pos of 315 ≈ nominal) | SPDR-018 report §3; SPDR-018B |
| **DIR-4** | Mean-reversion lean, corroborating | **[D]** | crypto | C8 `p_momo` ≈ **0.468–0.470** | SPDR-018 **C8** |

**What this licenses.** Direction is **measured, not targeted**. Volatility scale is not a directional
signal and may not be substituted for one. **DIR-3 is a positive quantification and must not be filed
as a null** — nor may it be routed, since it does not clear its cost floor when flipped.

### 2.7 `p`, `W`, `L` and the cost floor — the baseline economic object
*Licensed use: describe the baseline; prevent edge-manufacturing claims.*

**Crypto is the powered estimate; cTrader is credibility only** (AMENDMENT-C1 / S1). Power counts are
not comparable between them (L-50). Medians are the headline, with the cross-cell mean alongside.

| Term | **Crypto** (25 perps, 1,413 powered) median \| mean | **cTrader** (3 instruments, 315 powered) median \| mean |
|---|---|---|
| `p` | 0.3887 \| 0.3781 | 0.4868 \| **0.4300** |
| `p_be` (gross) | 0.4025 \| 0.3859 | 0.4855 \| 0.4330 |
| **gap `p − p_be`** | **−0.0138 \| −0.0078** | **+0.0013 \| −0.0030** ← *changes sign* |
| `W` / `L` | 128.65 / 75.55 \| 128.81 / **84.69** bps | 24.66 / 20.99 \| 23.90 / 19.02 bps |
| `W/L` | 1.4844 \| **1.7548** | 1.0597 \| **1.4372** |
| `p_be_net` | 0.4992 \| 0.4641 | 0.5334 \| 0.4987 |
| **`edge = p − p_be_net`** | **−0.0728 \| −0.0860** | **−0.0544 \| −0.0687** |
| gross mean | −1.178 bps (**0.016σ**) | −0.080 bps (**0.006σ**) |
| net mean | −15.157 bps | −2.500 bps (doubly synthetic) |
| clears gross break-even | 459 / 1,413 = **32.5%** | 129 / 315 = **41.0%** |
| **clears net break-even** | **0 / 1,413** | **0 / 315** |
| gap decomposition | rate +0.0067 / cost +0.0650 → **cost 90.7%** | rate +0.0023 / cost +0.0529 → **cost 95.8%** |
| σ̂ (pooled TRAIN) | 73.00 bps | 13.03 bps |
| mirror fit `log(W/L)` on `log((1−p)/p)` | R² **0.9667**, slope 0.9408 | R² **0.9746**, slope 0.9656 |
| cells indistinguishable from the mirror | 82.8% | 93.0% |
| best powered cell | **+8.50** bps gross (best with a CI excluding zero **+8.24**, cost 13.62 → **net −5.38**) | **+1.389 bps** gross vs a 2.43 bps charge |
| edge negative in **every** symbol | yes — all 21 named (−0.020 to −0.160) | yes — all 3 (−0.054 to −0.106) |

> **Reading note — two traps.**
>
> **1. Do not subtract the rows.** `edge = p − p_be_net` holds **exactly per cell** (max deviation
> 0.0), but **neither the median nor the mean operator is additive across cells.** Crypto: median `p`
> − median `p_be_net` gives −0.1105 against a true median `edge` of **−0.0728**. cTrader: −0.0466
> versus a true −0.0544. Always read `edge` from its own column.
>
> **2. One conclusion is median-dependent.** cTrader's gap to gross break-even is **+0.0013 on
> medians and −0.0030 on means** — it changes sign. Both are inside noise (gross mean 0.006σ), so
> **"`p` sits *at* its own gross break-even" is robust on both bases and is the claim to make;
> "`p` sits *above*" is NOT robust and must not be claimed.** Crypto's gap is negative on both bases,
> and cTrader-is-tighter holds on both.
>
> **Where mean and median diverge most:** crypto `L` (75.55 vs 84.69) and both universes' `W/L` —
> the right-skew in loss size and payoff asymmetry (L-51; thread P2).

**Arm split (crypto) — two different objects, never pooled into one story:**

| Arm | `p` | `W` | `L` | `W/L` | `p_be_net` | edge | gross | cost share of the gap |
|---|---|---|---|---|---|---|---|---|
| **B** (SPDR-013 residue) | 0.336 | 107.6 | 53.9 | **1.880** | 0.434 | −0.096 | −1.75 | 88.4% |
| **C** (SPDR-014 residue) | 0.467 | 142.1 | 124.5 | **1.136** | 0.526 | −0.057 | **+0.08** | **98.8%** |

**Arm C's rate sits 0.0007 from its own gross break-even.** There is no rate deficit to fix on arm C;
there is only a cost floor.

**The identity is verified, not assumed.** Against the mean over non-flat signed legs,
`p·W − (1−p)·L = mean` reconstructs to **1.46e-11 bps** on crypto's 24,098 cells and **8.53e-14
bps** on cTrader's, against a 0.01 bps tolerance. `p_be`, `p_be_net` and `edge` re-derive to **max
difference 0.0**. Axis-B of design §3, listed **NEVER MEASURED** at checkpoint open, is discharged.
The emitted all-leg mean also includes flat legs, producing a gap of up to **0.585 bps** on powered
crypto cells and about **0.042 bps at cTrader's p99**. Flat legs must still be charged their cost.

**The three point statistics disagree on crypto, and only one has CIs:**

| Statistic | crypto powered (gross) | cTrader powered (gross) |
|---|---|---|
| mean | **−1.18** | −0.080 |
| median | **−14.43** | −0.560 |
| 10% trimmed mean | **−11.67** | −0.573 |

The mean is the correct object for the identity. But **"the cells sit essentially at gross
break-even" is the most favourable of the three by 13 bps on crypto**. Where median/trimmed CIs have
been recovered (451 arm-B cells, addendum P02/P03) they **reject zero — median 449/451, trimmed
451/451, all negative — where the mean does not (46/451)**. The near-break-even framing is the
weakest reading of the evidence, not the strongest.

**How volatility enters this identity — the part that constrains any capture design:**

| # | Observation | Class | Universe | Effect size | Source |
|---|---|---|---|---|---|
| **V21** | Selection scales **both** sides of the identity | **[P]** | crypto (174 powered cells); cTrader R7 | across magnitude strata the rate is pinned in **0.4147–0.4795** while `W` runs **109.5 → 235.4 bps** and `L` runs **94.7 → 171.1**; `W/L` moves only **1.10 → 1.40** | SPDR-018 **C5** |
| **V22** | Conditioning on a volatility event does the same thing — the terms offset | **[D]** | crypto; cTrader | ambient-base arm B: rate **+0.0423**, `W` **+130.2**, `L` **+87.6**, IQR +202.3 bps, but `W/L` **−0.174**. Arm C: rate +0.0255, `W` −33.7, `W/L` −0.124, Δmean −0.318 bps. cTrader `W` +6.67, `L` +7.74, `W/L` −0.028, Δmean −0.053 | SPDR-018 §5 |
| **V24** | Most powered cells statistically cover the zero-mean payoff mirror | **[P]** | crypto; cTrader | The mirror `W/L = (1−p)/p` is a mathematical consequence of zero gross mean, not an empirical model. Residual `log(W/L) − log((1−p)/p)` has median **−0.0301**, mean −0.0356, sd 0.0729, positive in **32.5%** of cells; **82.8%** of powered cells are statistically indistinguishable from the mirror. *Descriptively*, a fitted regression reaches R² **0.9667** (cTrader **0.9746**, 93.0% indistinguishable) — **not an opportunity budget** | SPDR-018 Class B; SPDR-018B R3 |
| **V25a** | Observed powered parent geometries move `W/L` substantially without improving the mean | **[P]** | crypto; cTrader | Across 1,413 powered crypto cells from arm-B exits and arm-C breach types, `W/L` spans **0.998 → 5.25 = 5.3×** with the mean near zero (`p` 0.154 → 0.503). Only `combined` (478/1,022) and `signalflip` (401/1,022) supply powered arm-B cells. cTrader's all-powered span is **5.0×** | SPDR-018 Class B; SPDR-018B R3 |
| **V25b** | The full five-device span is descriptive, not established | **[U]** | crypto; cTrader | The headline **0.150 → 10.05 = 67×** includes `stop`-only, `trail`-only and `time`, **each with 0 of 1,022 crypto cells at target precision**. cTrader's corresponding descriptive span is 36.4× | SPDR-018 B1/B2; SPDR-018B |
| **V26** | Longer holds at low thresholds push the identity toward the symmetric coin flip | **[P]** | crypto (14 powered, monotone) | z=1.0/h=4 **+1.15 bps** (`p` 0.4761, `W/L` 1.116); z=1.0/h=12 **+2.86** (`p` 0.4999, `W/L` 1.025); z=1.5/h=12 −1.43; z=2.0/h=4 −0.52. Higher z pushes `p` down and `W/L` up; **they move against each other and the mean stays within ±3 bps of zero** | SPDR-018 **C6** |
| **V27** | Touch and horizon exits are positive while close exits are negative; all are sub-cost | **[P]** | crypto; cTrader | Crypto: **E-TOUCH +0.6…+1.5**, **E-HORIZON −0.03…+0.69**, **E-CLOSE −1.2…−3.0**. cTrader medians: **+0.124 / +0.158 / −0.491**. The sign grouping replicates; the exact TOUCH > HORIZON order does **not** | SPDR-018 **C4**; SPDR-018B R13 |
| **V28** | Absolute-bps thresholds are not portable across universes with different σ̂ | **[P]** | crypto vs cTrader | σ̂ **73.00** vs **13.03** bps. The same 10 bps precision bar means **0.137σ̂** vs **0.767σ̂**; the corrected cTrader screen therefore uses a universe-native threshold. Side-derangement also measures −12.221 vs −2.632 bps, but that one comparison does not prove that every effect scales exactly with σ̂ | SPDR-018B L-50 / P-21; SPDR-018 §5; SPDR-018B R8 |

**The cost floor these magnitudes are measured against:**

| Item | Value |
|---|---|
| Charged cost (crypto) | **13.1–16.1 bps**, pooled 13.540 — fees + discrete funding + allowance |
| Charged cost (cTrader) | ~2.43–2.54 bps — **doubly synthetic** (borrowed from Bybit and rescaled) |
| Spread | **NEVER CHARGED, programme-wide (2026-07-23).** Not a pending pin. Every net figure is overstated by an unquantified amount, and the caveat travels with it |
| Deflator sensitivity (cTrader) | defensible range **0.185–0.703** (factor 3.8, ±2× on every net figure); the 0/315 conclusion clears the defensible floor by **4%** (P-25 / L-53) |

Against this floor: the largest measured volatility effect *usable for selection* — the regime size
gap at +18…+48 bps on H1 — is comfortably above the cost floor **as a magnitude**. The largest
measured *signed* effect is not: the best powered cell with a CI excluding zero is **+8.24 bps gross
→ net −5.38**.

**What this licenses.** A description of the baseline economic object, and a **refusal**: no design
may claim that selection, exits, holds or sizing manufacture expectancy out of a joint `(p, W, L)`
sitting at break-even. Any proposal that claims otherwise must **name the mechanism** that puts
`R = p·W/((1−p)·L)` above 1. The powered parent geometries span 5.3× in `W/L` without doing so;
the full five-exit-device, 67× grid is descriptive and mostly unresolved.

### 2.8 Settled weak or dead directions — do not re-spend

| Object | Why |
|---|---|
| **Calendar / session features** | SPDR-018 A4: D1 cells run at exactly **1.000 observation per date** against 6–9 dummies; median incremental R² D1 **−0.032…−0.050**, H1 −0.0004…−0.003, session-only on D1 exactly **0.000** in all 48 cells. *(cTrader's +0.0291 is over-fitting on 3 instruments in a TRAIN-only lane — N4, not a market statement)* |
| **k=1 next-bar volatility forecasting as a gate** | V15 — inert |
| **`R-HMM-RV` as a forecaster** | V16 — real but weak, ~1/3 of R-MARKOV; do not promote it over the stronger read |
| **`R-SHOCK` as a regime** | named comparator only |
| **Close-to-close RV at D1; HAR** | V3, V2 |
| **Cross-sectional rank as a primary lever** | weakest SPDR-012 axis |
| **Unconditional / trend direction on net** | DIR-1 |
| **Path-noise forecasting; the DERIVED error-dynamics layer; model-predicted-price mispricing zones** | SPDR-017: model IC ≈ 0, three destroys indistinguishable |

---

## 3. Limitations and unresolved questions

### 3.1 Not available — power statements, never negatives (B-5)

| Item | State |
|---|---|
| **C2 — shock-conditioned MOMO** | Crypto survivor: M-3 live **+22.6 bps** vs a magnitude-matched comparator at percentile **0.95**, one-sided p = 0.05, **n = 505**, +37.1 bps above magnitude-matched bars. Grid **UNPOWERED** (65 of 1,020 at target; powered C2 cells sit at gross −0.32 bps). cTrader: **NOT REPLICATED AND NOT REFUTED**, citable only as *"does not transport cleanly"*. The operator skipped P1, so C2 is **not settled under the current evidence scope**; it books at the retrospective as terminal `NOT_RESOLVABLE`, **never a refutation** |
| **C3 — ordered `last_k` volatility flip** | **Terminally unpowerable in its registered form** (addendum P04): all 1,946 unresolved cells are already pooled + σ̂-normalised on full TRAIN — every design §5 lever is spent — median realised `n` 140 events at block MDE 90.2 bps against a 10 bps target, median **81× short**. At the conditioner's own event rate (**3 events per 10,000 bars**) the median cell needs **201 years** of 25-symbol history; 88.3% need >20y, 64.5% >100y. **Unpowerable, NOT refuted.** Powered C3 cells sit at gross **+0.34 bps** — the only positive item-level gross median in arm C, far below any cost floor. The only route to powering it is changing the event definition, which is **a different object and a new registration** |
| **B1 / B2 / B3** | `stop`/`trail`-only (0 of 2,044), `time` (0 of 1,022), and the positive-mean cells (**830, not the design's 125** — a premise defect in a frozen design). Their value is descriptive `W/L`-movability evidence (V25b), not as expectancy cells |
| **A3 per-symbol DESIGN** | 99–102 dates against 225 required — a property of catalog length, not of the effect. Pooled DESIGN resolves it (327–330 dates) |
| **P7 — Asia magnitude × shock interaction** | magnitude-matched **no-shock** momentum ≈ **+9.98 bps in Asia vs −1.17 in EU** on 162–184 rows. **Unregistered lead — must be registered before it is screened** |

**Why the cTrader read cannot close C2** (four reasons, descending force): (1) the comparator is not a
neutral yardstick — its own mean runs +0.97 (EU) → +3.46 (US) → **+12.05 bps (Asia)**, and the Asia
null lies entirely above zero (q5 +2.09), so a zero-effect arm reads percentile 0.000 against it;
(2) the effect vanishes where liquidity is deepest — ASIA −13.57 (n 184) / US −1.99 (n 853) /
**EU +0.62, pct 0.443 (n 557)**; (3) **corrected 2026-07-26** — the like-for-like cell (n=290) **was**
powered for an effect of crypto's magnitude (plant curve {+5: 0.285, +10: 0.755, **+20: 1.000,
+40: 1.000**}) and measured **−9.383 bps at pct 0.043**, the opposite sign, which **strengthens "not
replicated" and removes one support for "not refuted"**; (4) the comparator level is
construction-dependent — an independent rebuild reproduces every *live* value exactly but shifts the
comparator 2.3–3.4 bps and flips the `P-MR` read (0.067 → 0.826).

### 3.2 Open threads on the evidence base itself

| # | Thread | State |
|---|---|---|
| **P1** | Re-run M-3 on `shock_flag` at `n` in the thousands | **SKIPPED BY OPERATOR 2026-07-26** (no 018C). Consequence: C2 remains unsettled under the current evidence scope |
| **P2** | Median / trimmed-mean CIs | **PARTLY DONE** — 451 powered arm-B `per_symbol` cells (addendum P02/P03). Changes wording, not the verdict: the negative read gets **stronger**. **Still open: arm C (534 cells) and the `trail`/`stop` populations** |
| **P3** | CI fragility sweep | **CLOSED only for the recovered stratum.** Across 451 powered crypto arm-B per-symbol cells, seed spans **~4.8% of CI width** (p95 0.067) and block spans 0.43–0.65 bps against 2–18 bps effects. Arm C, pooled cells, stop/trail populations and cTrader were **not directly swept**, so no universal stability claim is made |
| **P4** | Is C3's required `n` reachable? | **ANSWERED 2026-07-26** — see C3 above |
| **P5** | Per-symbol spread pin | **NOT A THREAD — retired 2026-07-23.** Spread is never charged programme-wide; the T1 lane holds no quote data and a fixed proxy is refused in code. Carried as a permanent caveat and a claim refusal (AMENDMENT-C2), not as pending work |
| **P6** | 018B determinism + a Bybit-holdout assertion on its §5 guard reads | **SKIPPED by directive 2026-07-28**, recorded as an **open gap**. No violation is evidenced; the exposure is absence of evidence. Any future citation of 018B's §5 guard reads must carry this caveat |
| **P7** | Asia magnitude × shock | Unregistered lead — **register before screening** |
| **P8** | C9 / D3 / D4 on cTrader; arm-C parent parity on the remaining 2,323 crypto cells; why the 018B power flag is not regenerable (317 vs 315) | Completeness, not decision-relevant |

### 3.3 The honest caveat that keeps §2.7 falsifiable

SPDR-018/018B measured `W/L` under the **parents' own outcome geometries**, not under a designed
management policy. The 5.3× powered span combines arm-B exit modes with arm-C breach types; of the
five arm-B exit modes, only two are powered. The full 67× arm-B span is descriptive. These results
**cannot rule out** that some geometry outside this grid sits off the mirror. What they do is
**raise the bar**: the mechanism must be named, not searched for.

### 3.4 What is NOT run, and may never be read as a null

C9 (`DA-STRADDLE`), D3 and D4 were **not run on cTrader**. Seven inherited HARD checks do not exist on
018B (determinism among them). These are absences, not results.

---

## 4. What this document does not decide

**No next experiment is selected here.** No replacement identifier is named, no entry object is
chosen, no grid is declared, and no evaluation method is adopted.

**No universal outcome measure is selected here.** In particular, **no single score — including any
scale-free payoff ratio — is imposed across all management devices.** A device's outcome measure must
match that device's actual job, and that choice belongs to a later design, not to this inventory.

The observations above license **selection, stratification, parameter scaling, timing scale and risk
limits**. They do not license an edge claim, and they do not by themselves say which management
question is worth asking next. **That is the operator's call, and it is open.**

---

## 5. Governance state

| Item | Value |
|---|---|
| Counted TEST reads consumed by SPDR-018 + SPDR-018B | **0** (lifetime cap untouched) |
| Multiplicity slots consumed | **0** (AMENDMENT-C3 disclosed-not-rationed; AMENDMENT-C4 records the tail counts — both are `docs/signal-registry/multiplicity-registry.md` amendments, not family-contract amendments) |
| Holdout contact | **none** — Bybit 2025-01-08 and cTrader 2024-12-13 never queried. One recorded gap: no HARD assertion that 018B's §5 cross-universe guard reads stayed inside the Bybit TRAIN fence (P6); no violation is evidenced |
| Family status | `CF-VOLDIR-001` **REGISTERED**, unchanged. Transitions are retrospective-only |
| Capture axis | **Unregistered.** The two registrations opened 2026-07-25 were withdrawn and permanently voided 2026-07-30 for design defects. One completed run and one incomplete run were removed from the active evidence base; no SPDR-018/018B result is retracted |
| XENA | `XENA-VOLDIR-001` **RESERVED**; not discussable until a cost-surviving base graduates under separate authority |
| Spread | **NEVER CHARGED, programme-wide (2026-07-23).** Standing exclusion + travelling caveat; every net figure is overstated by an unquantified amount. Not an open item |
| New knowledge-base entries | **L-50, L-51, L-52, L-53**; dead ends **P-21…P-25** |
| Outstanding engineering | `SPDR-018B/screen_code/add_missing_controls.py` is still a manual post-step any re-run silently undoes (L-52) |

---

**No family action, end-state decision, gating verdict, tradability, deployability, cost-complete,
graduation or XENA claim is made or implied by this document. The mid-checkpoint reflection does not
close the checkpoint on a null rate (design §5 Step 2), and it selects no next experiment.**
