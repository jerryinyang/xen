# CF-CSRR-001 — Origin Document (Variant Provenance & Component Decomposition)

**Family:** CF-CSRR-001 — Cross-Sectional Consensus-Residual Reversion (basket).
**Created:** 2026-07-06. **Status at creation:** REGISTERED (family card:
`docs/signal-registry/candidate-families/cf-csrr-001.md`).
**Purpose of this file:** preserve, *faithfully and without editorialisation*, the source
text of each registered variant, then map the variants onto a shared **component axis**
decomposition. The characterisation experiments screen those components individually and
select ONE model from the observations. Registration provenance:
`.ignore/temp/new-family/{r1-dlc.md, r2-ksd.md, r3-mlg.md, r4-tpg.md, verdict.md}`.

**Reading contract:** everything under a "SOURCE (verbatim)" heading is copied from the
suggestion documents unchanged (only fenced for clarity). Everything under "Decomposition"
or "Editorial" is this programme's analysis and is clearly separated so the source is never
corrupted or biased in transcription. Where a source idea used a rolling estimator or a
passive-limit entry that the MR-arc lessons flag, the flag lives in Editorial, not in the
transcription.

---

## The 5 registered variants

| ID | Name | Source | Rank (verdict.md) |
|---|---|---|---|
| V1 | Median-Basket Deviation, single-worst-only | `r1-dlc.md` §"Strategy 2" | Rank 1 (strongest suggested variant) |
| V2 | Consensus Residual Basket | `r4-tpg.md` §2 | Rank 1 |
| V3 | Implied Fair-Price Level | `r4-tpg.md` closing observation ("A fourth observation…") | Rank 1 |
| V4 | Cross-Sectional Z-Spread with Price Inversion | `r2-ksd.md` "Idea #1" | Rank 1 |
| V5 | Consensus-Residual, Active-Entry / Passive-Exit (remodel) | this programme (verdict.md + design turn) | — |

> The rank-1 cluster in `verdict.md` = {r1-dlc S2, r4-tpg S2, r4-tpg obs, r2-ksd I1}. Those
> are the **4 suggested variants**; V5 is the programme remodel. All 5 are registered so each
> component can be characterised individually before one model is constructed/selected.

---

## V1 — Median-Basket Deviation, single-worst-only

**SOURCE (verbatim, `r1-dlc.md`, "Strategy 2"):**

> **Universe:** all 10 indices.
>
> **Spread:** anchor each index to its own prior daily close (or Monday open for a weekly
> variant). Compute each index's log move from anchor:
>
> r_i(t) = ln(P_i(t) / anchor_i)
>
> Then the basket "mean" is the **cross-sectional median**: m(t) = median(r_1…r_10). Each
> instrument's spread is s_i = r_i − m.
>
> The median is the unconventional-but-robust piece: it replaces the whole
> cointegration/beta/covariance apparatus with a single rank statistic. It's non-parametric,
> can't be dragged by one crashing index, and asks nothing of the data except that 10 quotes
> exist — perfectly happy with sparse, hourly, or gappy bars.
>
> **Unique feature — position management:** trade only the *single* largest |s_i| when it
> exceeds threshold k, hedged 1:1 notional against the index currently *sitting at* the median
> (or the two flanking it, half notional each). Not the whole basket. This means: at most one
> position at a time, two or three legs, no netting logic, no correlated stack of ten fades,
> and the hedge leg is by definition the "most representative" index at that moment rather than
> a fixed benchmark. k can be a fixed coarse value (e.g., 40–80 bps for daily anchors) or, in
> the same spirit as Strategy 1, the trailing median of the daily max-|s_i| — one parameter
> either way.
>
> **Invertibility:** m moves slowly relative to any single index (it takes 5 indices moving to
> shift it), so the entry price for candidate i is effectively static over short horizons:
>
> P_i* = anchor_i × e^(m(t) ± k)
>
> Precompute it, rest a limit there, refresh when m ticks (i.e., when the middle-ranked
> instruments move enough to change the median). Exit price is anchor_i × e^(m) — also a
> resting limit. This is unusually clean: most basket strategies can't quote a firm price
> because the "fair value" is a moving regression output.
>
> **Rationale:** a single global equity risk factor dominates daily co-movement across these
> 10 indices. When nine indices moved −0.3% to +0.2% and one moved +1.4%, the deviation is far
> more likely to be local flow, an FX translation quirk, or thin-session drift than genuine
> country-specific repricing — and the median tells you what "the world" did without needing to
> model it. Fading only the *most* extreme deviator concentrates capital where the noise/signal
> odds are best and where the passive fill premium is largest.
>
> **Assumptions:** (1) deviations from the global factor are transient absent country-specific
> news — the failure mode is a real local shock (BOJ surprise on JP225, China policy on HK50).
> Mitigation: skip the trade if the deviator's move happened in one bar/gap rather than a grind
> (a one-line filter, no parameter), plus a time stop of 1–2 sessions. (2) The 10 series are
> comparable at the same timestamp — with near-24h CFD quotes this mostly holds, but the median
> is cleanest during overlapping liquid hours; a weekly-anchor variant sidesteps the timezone
> issue entirely at the cost of frequency.

**Decomposition:** anchor = prior-close/own-anchor log move; consensus = **cross-sectional
median**; selection = **single-worst |s_i|**; hedge = **median index 1:1** (or two flanking
half-half); threshold = fixed-bps *or* trailing-median of daily max|s_i|; entry/exit =
**passive limit** at `anchor_i·e^(m±k)`; guards = one-bar-gap skip filter + 1–2 session time
stop.

---

## V2 — Consensus Residual Basket

**SOURCE (verbatim, `r4-tpg.md`, §2 "Consensus Residual Basket"):**

> This one is my favorite. Instead of comparing US500 against US100 alone, measure how much one
> index disagrees with **everyone else**.
>
> For US500, the residual is
>
> R = P_500 − (w_1·P_US30 + w_2·P_GER40 + w_3·P_UK100 + w_4·P_JP225) / (Σ w)
>
> Weights can simply be equal — no optimization required. The basket becomes a "market
> consensus," and you are betting on one market temporarily disagreeing with the crowd.
>
> **Novel twist:** Don't compute consensus from prices; compute it from **normalized daily
> moves**. For example, suppose today US30 is +0.8%, GER40 +0.7%, UK100 +0.6%, and JP225
> +0.75%, giving a consensus of roughly +0.71%. If US500 only moved +0.2%, the residual is
> about −0.5% — trade the convergence.
>
> **Why this is different:** Most basket spreads are weighted sums. This is closer to
> "cross-market voting": each index gets one vote, and no regression is involved.
>
> **Why it may work:** Global equity markets share common drivers — macro news, rates, risk
> appetite. Yet one market frequently opens late, overreacts, or underreacts before catching up
> to the rest.
>
> **Assumptions:** Global information propagates imperfectly, and regional markets temporarily
> lag.
>
> **Noise robustness:** Very robust. One noisy index hardly changes the consensus, and no
> covariance estimation is needed.
>
> **Invertibility:** Yes. The consensus level can be translated into an implied target level
> for the missing index, so you can derive an expected US500 price from the basket price and
> place resting limits accordingly.

**Decomposition:** anchor = own prior close (normalized daily move); consensus =
**equal-weight mean of normalized moves** ("one vote each"); selection = per-index residual
(multi); hedge = vs basket; threshold = residual magnitude; entry/exit = **passive resting
limit** at implied level. Distinguishing component from V1: **mean (equal-weight) consensus**
vs V1's **median** consensus; residual on **normalized moves** rather than log level.

---

## V3 — Implied Fair-Price Level

**SOURCE (verbatim, `r4-tpg.md`, closing observation "A fourth observation that combines all
three"):**

> A surprisingly underexplored idea is to define **equilibrium as a price level rather than a
> spread value**. For example:
>
> P_US500* = (P_US30 + 0.8·P_US100 + 0.6·P_GER40) / c
>
> You then trade the **actual implied fair price** of the US500 rather than an abstract spread,
> and the spread is simply
>
> P_US500 − P_US500*.
>
> This makes the strategy naturally invertible into concrete index levels, so you can place
> passive limit entries and exits at predetermined prices instead of reacting with market
> orders when an indicator crosses a threshold. That structure is particularly attractive for
> index CFDs or futures, because it supports proactive order placement while remaining
> conceptually simple and only mildly parametric.

**Decomposition:** anchor = none (absolute level); consensus = **weighted implied fair-price
level** (fixed linear combination of peers, non-equal weights); selection = single target
index; hedge = implicit in the combo; threshold = level deviation; entry/exit = **passive
limit** at the implied level. Distinguishing component: **weighted (non-equal, price-level)
consensus** vs V1 median / V2 equal-weight-of-moves. This is the parametric end of the anchor
axis (weights `0.8, 0.6, c` are free), and therefore the most multiplicity-exposed.

---

## V4 — Cross-Sectional Z-Spread with Price Inversion

**SOURCE (verbatim, `r2-ksd.md`, "Idea #1"):**

> At every time step t, look across all 10 indices:
>
> 1. **Compute instantaneous returns:** r_{i,t} = P_{i,t}/P_{i,t-1} − 1
> 2. **Compute cross-sectional statistics:** r̄_t = (1/N)·Σ r_{i,t} (basket mean return);
>    σ_t = std(r_{i,t}) (cross-sectional dispersion)
> 3. **Define the "spread" for each index i:** s_{i,t} = (r_{i,t} − r̄_t) / σ_t
>    This is simply the cross-sectional z-score—how many dispersion-units index i is from the
>    basket centroid at time t.
> 4. **Entry signal:** When |s_{i,t}| > k_entry (e.g., 1.5–2.0), index i has strayed far from
>    the pack → fade it (short the outperformer, long the underperformer).
> 5. **Exit signal:** When s_{i,t} crosses zero (reverts to the basket mean).
>
> **The Price-Inversion Feature.** Because the spread is defined in return space with a simple
> linear construction, it inverts cleanly:
>
> Entry price precalculation: P_{i,target} = P_{i,t} × (1 + r̄_t ± k_entry·σ_t)
> Exit price precalculation: P_{i,exit} = P_{i,t} × (1 + r̄_t)
>
> In practice: calculate these prices at the close of each bar; place resting limit orders at
> the entry prices for all N indices; cancel/reprice on each new bar if unfilled; attach a
> take-profit limit at the exit price.
>
> **Why It Might Work.** This exploits the *cross-sectional* rather than *temporal* dimension.
> Major global equity indices are driven by overlapping macro factors (global growth
> expectations, risk appetite, USD liquidity). When one index decouples sharply from the
> centroid in a single period, that decoupling is often idiosyncratic noise or local liquidity
> shock rather than a genuine regime change—it tends to get "pulled back" toward the pack within
> a few periods.
>
> **Assumptions:** The basket exhibits sufficient cross-sectional co-movement (high average
> pairwise correlation) so that deviations are mean-reverting, not structural. One-period
> returns are approximately symmetric, so the z-score is meaningful without distributional
> fitting. The cross-sectional mean r̄_t is a reasonable proxy for the "fair" return of any
> given index over the next period.
>
> **Parameters (Minimal):** k_entry (entry threshold in σ units, 1.5–2.5); rebalance frequency
> (daily or session-level). No lookback window, no rolling estimation, no distributional
> assumptions.

**Decomposition:** anchor = one-bar prior price (instantaneous return); consensus =
**cross-sectional mean return r̄**; normalization = **÷ cross-sectional dispersion σ_t**
(z-score) — the distinguishing component; selection = all |s|>k (multi); hedge = long/short
within basket; threshold = **fixed σ-multiple k_entry**; entry/exit = **passive resting limit**
at inverted price. Distinguishing component vs V1/V2: **cross-sectional-σ normalization** of
the residual (dispersion-scaled), and a one-bar (not session/close) anchor.

---

## V5 — Consensus-Residual, Active-Entry / Passive-Exit (programme remodel)

**EDITORIAL — this is the programme's own variant, built mechanism-first from the MR-arc
lessons. Not from a suggestion document.** Full rationale in `.ignore/temp/new-family/`
verdict.md and the design turn that produced it. Verbatim design intent:

The core insight that separates V5 from V1–V4 is that **all four suggested variants place the
entry as a passive limit at the deviation price** — which the MR arc proved is *adverse
selection*: a resting limit at the extreme fills preferentially when the divergence keeps going
against you (the exact seam that retired CF-MR-003/004). V5 splits execution:

- **Entry = ACTIVE, on the confirmed event we measure.** At each confirmed bar close
  (decision ≤ t-1), find the single index with max|s_i|; if ≥ k, enter at the next bar open,
  market, direction = −sign(s_i). The entry event equals the event the reversion was measured
  on — no passive-limit adverse selection.
- **Exit = PASSIVE, at the rolling consensus.** Rest a TP limit at consensus parity
  `P_i,target = anchor_i·e^(m(t))`, **re-pegged each bar as m updates** (rolling anchor —
  reversion comes *to* you = favourable fill). This quarantines passive fills to the side where
  selection is positive.
- **Stop = TIME only, no price stop.** A price stop is an adverse-selection magnet (hit on the
  overshoot, then price reverts without you); r3-mlg S2 rediscovered this independently. Exit
  at market after T bars; a catastrophic guard (≈3× entry residual) bounds the tail, disclosed
  not primary.
- **Structure = single-worst, one position, median-index 1:1 hedge, NO hard cap.**
  Single-position-per-episode makes cap-lock (the CF-MR-005 killer) structurally impossible.
- **Anchor = return-from-rollover; consensus = cross-sectional median** (robust, no rolling z).
- **Mandatory control battery:** (1) random-timing twin at the P&L object (L-18/19), (2)
  random-index twin (extremeness vs timing), (3) momentum-signed inverted twin (drift-carry
  check, the USDCAD lesson).

**Decomposition:** anchor = return-from-rollover median; consensus = **cross-sectional
median**; selection = **single-worst**; hedge = **median-index 1:1**; threshold = trailing
median of daily max|s_i|; **entry = active confirmed-breach**; **exit = passive
rolling-consensus limit + time-stop, no price stop**; controls = three-twin battery.
Distinguishing component: **the execution split (active entry / passive exit) + time-only
stop** — the axis on which V1–V4 are all identical (passive-limit both sides) and V5 differs.

---

## Shared component-axis decomposition (what the characterisation screens)

Each variant is a point in a 7-axis component space. Characterisation isolates each axis so a
single model is *constructed from observation*, not chosen by narrative.

| Axis | Component | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|---|
| **A. Consensus estimator** | how "fair value" is formed | median | equal-wt mean of moves | weighted implied level | cross-sec mean | median |
| **B. Residual normalization** | raw vs dispersion-scaled | raw / range | raw (moves) | raw (level) | **÷ σ_t (z)** | raw |
| **C. Selection** | how many positions | single-worst | multi | single | multi | single-worst |
| **D. Hedge** | reference leg | median index | basket | implicit combo | within-basket L/S | median index 1:1 |
| **E. Entry execution** | fill discipline | passive limit | passive limit | passive limit | passive limit | **active confirmed-breach** |
| **F. Exit / stop** | target + stop type | passive limit + time stop | passive limit | passive limit | passive limit (s→0) | **passive rolling-consensus + time-only** |
| **G. Threshold** | trigger scale | fixed-bps / trailing-median | residual mag | level dev | fixed σ-mult | trailing-median |

**Load-bearing axes (per MR-arc lessons):**
- **E (entry execution)** — passive-limit entry = adverse selection (CF-MR-003/004). Only V5
  departs. This is the axis most likely to decide net viability; it is a *tradability* axis, so
  it is characterised at the validatory tier, not the execution-agnostic exploratory screen.
- **A/B (consensus + normalization)** — decides whether the residual is even mean-reverting;
  the substrate question. Screened first, execution-agnostic.
- **F (stop type)** — time-only vs price stop; price stop is an adverse-selection magnet.

**Currencies-basket construction note (operator decision 2026-07-06):** the consensus-residual
premise (one dominant common factor) does not map cleanly onto a mixed USD-quoted / JPY-cross
FX basket. For the Currencies arm the consensus is built on a **USD-strength alignment** (legs
signed to a common USD factor) rather than a naive median of heterogeneous quotes. This is
itself a registered component to validate — see family card §Currencies consensus.

---

## What this document is NOT

- Not a design. Per-experiment `design.md` files are quant-designer stage-1 deliverables,
  mechanism-first, one hypothesis each.
- Not a verdict. No component is preferred here; the characterisation screens decide.
- Not a re-open of any retired family (P-01/P-02): distinctness argued in the family card.
