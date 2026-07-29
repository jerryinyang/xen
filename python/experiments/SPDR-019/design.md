# SPDR-019 — Design: naive signed breakout + opportunity-modulated capture geometry

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D6`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **SoT (substance precedence):** `.ignore/what-next/alts/opportunity.md` §6.1 / §6.3 — this design
  narrows, never thins
- **Binding reflection inputs:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid-volatility-model.md`
  §2 (evidence inventory + classes), §5.2 (the five layers), §5.4 (the residual target),
  §5.4a (cost exclusion), §5.9 (the layer protocol)
- **Governing amendments:** **AMENDMENT-C5** (gross-only measurement), **AMENDMENT-C6** (layer
  protocol), plus standing **C1** (cTrader replication-only), **C2** (claim refusals — unchanged)
- **Lane:** SPDR TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** DESIGN — **execution unauthorised**

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  NOTE (AMENDMENT-C5): cost enters NO estimand, threshold or comparison in this design.
    p_be_net and the cost floor are emitted per cell as a DISCLOSED REFERENCE only.
```

---

## §1 What this experiment is

> **Falsifiable question.** On a fixed, non-predictive, signed breakout entry, does any layer of the
> opportunity model — scale, volatility state, swing gate, or capture parameters — move the payoff
> residual `log R = log(W/L) − log((1−p)/p)` reliably above zero, relative to the unmodulated
> baseline?

`log R > 0` is exactly `p > p_be`, which is exactly `E[gross] > 0`. It is an identity, not an
approximation, and it contains no cost term — which is why AMENDMENT-C5 costs nothing in rigour.

**This is a capture-geometry experiment, not a direction experiment.** The entry is fixed and is not
the research subject. No entry parameter is tuned to improve `p`; direction is **measured, not
targeted** (SoT §1.2). A zero baseline residual is a **predeclared, acceptable, and expected**
outcome — SPDR-018 measured five exit geometries spanning a 5.3× powered `W/L` range, all on the
zero line.

```
MECHANISM: A three-bar pivot-plus-momentum breakout commits capital when price trades through the
  extreme of the momentum bar. Its P&L-bearing object is a single signed EPISODE (one entry, one
  exit, no scaling). The regularity under test is NOT that this entry predicts direction - SPDR-013
  established that unconditional/trend direction has no exploitable edge, and this design assumes
  p sits at its own break-even. The regularity under test is that FORECASTABLE MOVE SCALE, which
  SPDR-012/013/015 established at rank IC ~0.33 (H1/H4) and which rescales the entire magnitude
  distribution (top/bottom decile 3.71x, P90 ratio matching the mean ratio to two decimals), can be
  used to place the exit boundaries of that episode so that the realised payoff sits OFF the
  driftless mirror W/L = (1-p)/p. Event cadence: pivot events; the realised signal rate is
  MEASURED and EMITTED per delta level, never assumed. The falsifier is log R indistinguishable
  from zero under every layer at a stated MDE.
DERIVED:
  estimand = per-EPISODE signed gross return in bps, decomposed per cell into
             (p, W, L, W_L, p_be, log R); log R is the primary read. Episode-level because the
             traded object is an episode, not a bar (L-16/L-18).
  null     = the DRIFTLESS MIRROR log R = 0, derived from the mechanism's own identity
             (E[gross]=0 forces W/L=(1-p)/p). NOT "zero P&L" - 32.5% of SPDR-018's powered cells
             clear gross break-even, so a zero-P&L null would re-discover that and call it an
             effect. Plus a side-derangement and an entry-timing derangement (SS7).
  horizon  = the Active Hold Period, swept over the measured regime run-length scale
             (E[run] 18.9-23.1 H1 bars, MAE ~12); no horizon outside that scale is introduced.
  test     = block-bootstrap CI on log R under SPDR-018 SS6.2's OWN rule, inherited verbatim and
             quoted in full in SS8.1: per-calendar-day sufficient statistics; day-block sweep
             {1, 3, 7} days; minimum block 1 day = 24 H1 bars >= every horizon; min/max envelope
             over blocks x seeds; 5-seed battery; xen.evaluation.block_bootstrap_ci; effective
             block capped < n. Dependence-matched block MDE (M-1) stated in LOG UNITS per cell
             before the run; realised EFFECTIVE sample size and realised c emitted per cell
             alongside n.
```

**Why this is not a reused stack.** The estimand is the identity residual of *this* episode object;
the null is that object's own arithmetic zero line; the horizon is set by the *measured* regime
run-length of the conditioning variable. None of the three would transfer to a different mechanism:
a mean-reversion or carry candidate has a different P&L object, a different zero line (carry is not
driftless), and no regime-run horizon. What is deliberately inherited is the `(p, W, L)` layer,
because that is the checkpoint's organising identity.

---

## §2 The entry — fixed, frozen, not the research subject

Verbatim from SoT §6.1. Index `[0]` = the decision bar (most recent **confirmed** bar), `[1]`,
`[2]` its predecessors. All state is `≤ t−1` relative to the order being live.

```
LONG:  low[1]  <  min(low[0],  low[2])   AND  ( (close[0] - close[1]) / ATR20) >  deltaThreshold
SHORT: high[1] >  max(high[0], high[2])  AND  (-(close[0] - close[1]) / ATR20) >  deltaThreshold

ENTRY:  LONG  = buy  stop at high[0];   SHORT = sell stop at low[0]
        order expires unfilled after `inactiveHold` HOURS
EXIT:   close after `activeHold` HOURS (Layer-4 variants replace this; L0 does not)

`activeHold` and `inactiveHold` are stated in HOURS on BOTH clocks (SS4.2). On H1 an hour is one
bar; on M15 it is four. The time exit fires at the open of the first decision-clock bar at or
after the elapsed hours.
```

`ATR20` = **Wilder ATR(20) on the decision clock, evaluated at `[0]`, causal `≤ t−1`.** Single
definition, shared by every arm (see the CONVERSION-PIN, §7).

**`deltaThreshold` is FROZEN as a swept axis, not calibrated** (QA finding). It takes exactly three
values — **`δ ∈ {0.25, 0.5, 1.0}`** — and **all three are reported side by side**. There is no
calibration step, no selection of a "best" δ, and no tuning against any outcome: δ selects how
extreme the momentum bar must be, which is an entry property, and tuning it would be researching
direction (SoT §1.2). The realised **signal rate at each δ is emitted** so the population is
visible. `δ = 0.5` is the golden-trace anchor and carries no privileged status.

**Fill rule (declared; resolved causally, not approximated).** Stop-order fills are resolved on the
**1-minute bar stream** (`data/catalog/`, T1 lane), never on the decision clock's OHLC:

| Case | Fill |
|---|---|
| An M1 bar within the pending window trades through the stop price | Fill **at the stop price** |
| An M1 bar **opens** beyond the stop price (gap) | Fill **at that M1 open** — the adverse case, never improved |
| No M1 bar reaches the stop before `inactiveHold` elapses | **Expire unfilled**; the signal is recorded as an unfilled event, not dropped |

Unfilled signals are emitted and counted. **Fill rate is a reported quantity per cell**, because a
capture variant that changes the fill rate changes the population and would otherwise silently
re-select it.

**Exit fill rule (declared; the L4 devices need it and the entry rule does not cover them).** All
exits are resolved on the same **M1 stream**, causally:

| Exit | Fill |
|---|---|
| **Profit target** | first M1 bar trading through the target → fill **at the target price**; if an M1 bar **opens beyond** it, fill at that open |
| **Trailing stop** | the trail ratchets **once per M1 bar, on that bar's close**, and never intra-bar; it triggers on the first M1 bar trading through the trail level, filling **at the trail level** (or at the open if gapped through) |
| **Time exit** | at the **open of the first decision-clock bar at or after `activeHold`** — an open-to-open exit, matching the entry convention |
| **Precedence within one M1 bar** | if target and trail/stop are both reachable in the same M1 bar, the **adverse one fills** (trail/stop). Never assume the favourable ordering |
| **Precedence with the time exit** | a target or trail triggering **at or before** the time-exit bar's open takes precedence |

The adverse-precedence rule is deliberate: intrabar ordering is unknowable at M1 resolution, so the
screen takes the pessimistic branch every time rather than manufacturing a favourable path.

**No slippage model, no queue model, no partial fills.** This is a screen; SoT §6.1 is explicit that
booked P&L requires a native execution vehicle. Nothing here is a tradability claim.

---

## §3 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES. Both are the signed EPISODE: fill at the stop price
    (or gap open) -> exit at the variant's exit rule. p, W, L are computed over episodes, never
    over bars, and never over an aggregate of bars belonging to one episode (L-16/L-18, B-8).
  measured conditioning event == traded entry event: YES. Every layer conditions on state known at
    the DECISION BAR CLOSE `[0]`, which is the bar whose extreme becomes the stop price - the exact
    state at which capital is committed. No layer conditions on the fill bar, the pivot bar `[1]`
    alone, or on any post-decision quantity (B-4).
  effect-splitting windows non-overlapping: YES. One episode occupies [fill_ts, exit_ts). A symbol
    holds at most ONE open episode at a time; a signal arriving while an episode is open is
    recorded as SUPPRESSED and counted, never silently dropped. Overlapping-window dependence
    between consecutive episodes is handled by block bootstrap under SPDR-018's inherited block
    rule (min 1 day = 24 H1 bars, envelope over blocks x seeds, 5-seed battery; SS1, SS8.1; B-9,
    spdr-lane dependence rule).
```

**Flat legs.** `r == 0` episodes are excluded from `p` and counted as `p_flat` (SPDR-018 §6 item 7).
Immaterial at scale, but reported, and their existence is disclosed in every cell.

---

## §4 The layer protocol (AMENDMENT-C6 — BINDING)

### 4.1 Phase (a) — sequential characterisation, run in full

Every stage emits the full `(p, W, L, W_L, p_be, log R)` decomposition with block CIs, its own MDE
in log units, its evidence class, its fill rate, and its episode count. **No stage is skipped
because an earlier one read flat.**

| Stage | What runs | Variants | Read |
|---|---|---|---|
| **L0** | The entry with a **fixed** capture policy: `activeHold` = **1 hour**, `inactiveHold` = **2 hours** (§4.2 — hours on both clocks), no target, no stop, no selection | 1 | The baseline `(p, W, L, log R)` and κ. **Mandatory first** — the entry carries a momentum prior, so without it every later change is misattributed |
| **L1** | **Scale alone, on the FIXED entry.** ŝ = H1 Parkinson-EWMA forecast, used ONLY to select among the signals the frozen `deltaThreshold` already produced — `δ` stays at its swept value, no new signal is created, and every retained episode keeps L0's own signal bar, stop price, fill and exit. The L1 population is a strict SUBSET of the L0 population (asserted, §12) | 4 (ŝ-decile cuts d≥5, d≥7, d≥9, and the ŝ-continuous rank reported as a dose-response — decile definition pinned in §4.1b) | Δ`log R` vs L0; the full decomposition |
| **L2** | **State alone**, three cells, not one: **(i)** shock axis (HMM HIGH/LOW label), **(ii)** level axis (R-MARKOV k=4 and k=12 state), **(iii)** both jointly | 5 (see §4.1a) | Δ`log R` per axis **and the interaction term**. Their near-independence (51–62% agreement, V9/V10) is a pre-registered prediction under test |
| **L3** | **Swing gate alone.** `T-GT-CUR` fires / does not fire; parameters left at L0 values | 3 (fires / does not fire / T-GT-MED5 co-report) | Δ`log R`; **plus the mandatory L-51 three-number selection check** on **every selected subset**, per the §15 anchor — the term "powered subset" no longer denotes a population (§9) |
| **L4** | **Capture devices, one at a time.** Each device runs **twice**: unmodulated (a fixed multiple of the **TRAIN-median ŝ per symbol** — the SAME estimator as the modulated arm, §4.2) and modulated (the same multiple × ŝ(t,h)) | see 4.2 | Δ`log R` per device; the unmodulated run is the comparator that separates the device from the information |
| **L5** | The small combination the L1–L4 reads justify | ≤ 4 | Term-level decomposition **alongside** any blended score. **L5 is evidence-selected and shares a sample with the reads that chose it — it does not and cannot substitute for phase (b)** |

### 4.1a The 33 predeclared variant identities, and the parent rows they read

Every phase-(a) variant is named here, because a variant the design does not name is a variant
the developer invents. The identities are pinned in
`results/expected_resolution_prior.json` (`declared_axes.variant_id`) and expanded per
`(clock, δ, scope)` in `results/expected_resolution.json`.

| Stage | `variant_id` | Count |
|---|---|---|
| L0 | `L0_BASELINE` | 1 |
| L1 | `L1_SHAT_DECILE_GE5` · `L1_SHAT_DECILE_GE7` · `L1_SHAT_DECILE_GE9` · `L1_SHAT_RANK_CONTINUOUS` | 4 |
| L2 | `L2_SHOCK_HMM` · `L2_LEVEL_RMARKOV_K4` · `L2_LEVEL_RMARKOV_K12` · `L2_JOINT_HMM_HIGH_AND_K12_HIGH` · `L2_INTERACTION_HMM_X_K12` | 5 |
| L3 | `L3_TGTCUR_FIRES` · `L3_TGTCUR_DOES_NOT_FIRE` · `L3_TGTMED5_CO_REPORT` | 3 |
| L4 | `L4_TARGET_A{1,2,3}_{UNMOD,MOD}` (6) · `L4_TRAIL_B{1,2}_{UNMOD,MOD}` (4) · `L4_HOLD_{1,4,12,20}H_{UNMOD,MOD}` (8) · `L4_SIZE_{UNMOD,MOD}` (2) | 20 |

**The joint L2 cell is `HMM HIGH AND R-MARKOV-k12 HIGH`** — the high/high interaction at the
stronger registered horizon (k=12, ΔBrier −0.1085 against k=4's −0.0199, V15). The
`L2_INTERACTION_HMM_X_K12` row carries the interaction term itself
(`Δlog R(joint) − Δlog R(shock) − Δlog R(k12)`), which is the quantity prediction 4 is about.

**L5 has no predeclared identity and is not in the 33.** Its ≤ 4 combinations are
evidence-selected from the L1–L4 reads, so naming them now would either be a guess or a
pre-commitment the protocol forbids. **Before L5 runs, a dated, hash-pinned addendum generated
by the same function must declare the exact L5 combinations and their expected-resolution rows.**
Placeholders (`L5_SLOT_1`, or any equivalent) are refused: an artifact row that names nothing is
not a predeclaration.

**The parent rows every gate reads (frozen; the developer chooses none of them).** These layers
consume forecasts already emitted by registered parents. The model, the field and the firing rule
are fixed here because each choice changes episode membership and therefore every count:

Each gate names its SOURCE ARTIFACT AND COLUMN, because "the R-MARKOV forecast" is not a field
and a developer cannot read it (QA run 6):

```
HMM shock label  : SPDR-015/results/regime_states.parquet, column `s_hmm_rv`, rows for the
                   symbol at clock H1.  HIGH = 1, LOW = 0, and s_hmm_rv < 0 means NO STATE -
                   such an event is INELIGIBLE for the L2 shock rows and is excluded from them
                   with a count and reason, never coerced to LOW.
                   Availability timestamp = `slot_end`.

T-GT-CUR         : SPDR-015/results/zz_ordinal.parquet, rows `target == 'T-GT-CUR'` and
                   `model == 'logit_ridge'`.  FIRES when the emitted `p` >= 0.5.
                   Availability timestamp = `confirm_slot_end` (the swing's confirmation).

T-GT-MED5        : same artifact, rows `target == 'T-GT-MED5'` and `model == 'ridge_cont'`.
                   FIRES when the emitted `pred_cont` > the emitted `threshold` ON THE SAME ROW.
                   That `threshold` IS the parent's causal five-swing median (`_median_last_k(
                   mags, 5, k)`, swings closed at or before k, predicting k+1) - it is read from
                   the artifact, never recomputed here, so there is no second definition to drift.

R-MARKOV k=4/k=12: THE PARENT PERSISTED NO PER-BAR PROBABILITY. `transition_metrics.parquet`
                   holds skill summaries only; the walk-forward `logistic_ridge` probability
                   lives inside SPDR-015/screen_code/transitions.py and was never emitted. Two
                   honest routes existed and the second is taken:
                     (a) using the emitted state `s_markov` directly - REFUSED: that is the k=1
                         gate, which V15 measured inert and SS3 of the reflection refuses;
                     (b) REGENERATE the k=4 and k=12 probabilities by calling the PARENT'S OWN
                         FROZEN function `walk_forward_probs(state, X, slot_end, is_origin, k)`
                         from SPDR-015/screen_code/transitions.py, on the feature matrix that
                         function itself defines, built ONLY from columns the parent emitted in
                         regime_states.parquet: `s_markov`, `dur_markov`, `rv20`, `park_ewma`,
                         `lvl_pct`, `n_high_4_markov`, `n_high_12_markov`, `s_shock`.
                         `n_high_{4,12}_markov` are BACKWARD-looking counts over the last k bars
                         (`_n_high_last_k`), verified causal.
                   HIGH when the regenerated p >= 0.5. The parent's code is imported, not
                   reimplemented - a second implementation is a second object (L-13).
                   PARENT PARITY, HARD (SS12): the regenerated probabilities must reproduce
                   SPDR-015's own emitted `delta_brier_vs_pers` at k=4 and k=12, per symbol,
                   to |d| <= 1e-9, written to results/parent_gate_parity.json. If parity fails,
                   the gate is not the parent's gate and the emission is invalid.
                   PARITY-EXEMPT SYMBOLS: the parent emitted a NULL metric wherever a symbol had
                   fewer than 40 usable origins (transitions.py returns all-NaN there), which on
                   H1 / R-MARKOV / logistic_ridge is 8 of 25 symbols - 1000PEPEUSDT, 1000RATSUSDT,
                   BIGTIMEUSDT, ORDIUSDT, PYTHUSDT, SEIUSDT, TIAUSDT, WLDUSDT (the same warm-up
                   gap that costs SPDR-020 its 8 Z-VOL symbols). There is nothing to reproduce, so
                   those symbols are declared PARITY-EXEMPT BY NAME in parent_gate_parity.json and
                   the HARD check runs on the 17 with a finite parent metric. `|NaN - NaN| <= 1e-9`
                   is false, so without this clause a correct screen fails its own check.
                   CONSEQUENCE, DISCLOSED not hidden: the 4 L2 level/joint/interaction variants
                   run on 17 of 25 symbols. Per-variant symbol coverage is emitted in
                   metrics_by_cell, and M-4 effective coverage is applied to those pooled figures.

ALIGNMENT        : every label is generated on H1 and HELD FORWARD to each H1/M15 decision close
                   from its own availability timestamp above. NO backfill, no interpolation, no
                   fill across the TRAIN fence. An event with no available label yet is excluded
                   from that layer's rows with a count and reason.
FORBIDDEN AS A GATE INPUT: the realised outcome label `y` (present in both parent artifacts and
                   trivially joinable - which is exactly why it is named), the realised swing
                   magnitude `mag_k1`, `next_abs_oo`, `run_len_*`, and any quantity dated at or
                   after the decision bar close [0]. Asserted by name in SS12.
```

`p >= 0.5` here is not an adequacy threshold and is not tuned: it is the decision boundary of the
parent's own binary forecast, i.e. the label the parent itself emits. No cell is admitted,
excluded or ranked by it.

### 4.1b How every decile is defined (QA run 6)

A decile is not a quantity until its reference population and its estimation window are stated,
and both choices change which episodes enter L1:

```
POPULATION : PER SYMBOL, always. A POOLED decile on a panel whose per-symbol sigma-hat runs from
             ~13 to ~129 bps is a SYMBOL SELECTOR wearing a scale label - the high deciles would
             fill with the loudest symbols and L1 would measure cross-sectional selection, not
             scale. L-50/P-21 forbid a threshold that crosses a universe boundary, and this is the
             same rule applied inside the universe.
WINDOW     : EXPANDING and CAUSAL. The decile edges at decision bar [0] are the empirical
             quantiles of that symbol's own s_hat over every H1 bar STRICTLY BEFORE [0], after
             the 60-bar warm-up. Full-TRAIN quantiles are refused: they are a look-ahead, and
             they are the kind that survives a fence check because no future BAR is read - only
             a future DISTRIBUTION.
WARM-UP    : a symbol needs at least 250 prior H1 s_hat values before any L1 decile row is
             emitted for it; below that the event is INELIGIBLE for L1 rows only, counted with a
             reason, and still present in every other layer.
CONTINUOUS : `L1_SHAT_RANK_CONTINUOUS` uses the same per-symbol expanding empirical rank in
             [0,1], not a z-score - the forecast rescales a distribution rather than shifting a
             mean (V5), so a rank is the right summary and needs no distributional assumption.
M-3 DECILES: the magnitude-matched comparator's |decision-bar move| deciles use the SAME rule -
             per symbol, expanding, causal. A comparator matched on pooled deciles would be
             matched on the wrong thing.
```

Asserted in §12: no decile edge is computed from data at or after the decision bar close, and no
decile edge is shared across symbols.

### 4.2 The L4 device grid (SoT §6.3, all four devices)

| Device | Unmodulated | Modulated | What it moves |
|---|---|---|---|
| **Dynamic profit target** | `a × ŝ_uncond`, `a ∈ {1, 2, 3}` | `a × ŝ(h)` | `W` up, `p` down |
| **Trailing stop** | `b × ŝ_uncond`, `b ∈ {1, 2}` | `b × ŝ(h)` | `W` and `L` jointly, path-dependently |
| **Holding period** | `activeHold ∈ {1, 4, 12, 20}` **HOURS** — on H1 that is 1/4/12/20 bars, on M15 it is 4/16/48/80 bars | `activeHold` scaled to the state's `E[run]` by the exact equation below, also in hours | the horizon over which `W`, `L`, `p` are realised |
| **Position sizing** | fixed notional `N0` (1 unit of account per episode) | `N0 × (ŝ_uncond / ŝ(t,h))`, clipped to `[0.25, 4]` — i.e. the constant `c` is pinned to `N0 × ŝ_uncond` per symbol, so the modulated arm is **anchored at the same scale** as its comparator. Its realised mean weight is **not** identical (Jensen, plus the clip): the **mean and sd of the realised weight are emitted per symbol** rather than assumed | **variance and comparability ONLY.** Reported on dispersion, never on the mean (SoT §4.4). A sizing cell may not carry a `log R` claim |

**Comparator units are identical by construction** (QA run 2). An earlier draft set the unmodulated
arm in `ATR20` (price units, decision clock) against the modulated arm in `ŝ` (bps, H1) — two
different units *and* two different estimators, since Wilder ATR ≈ mean range while Parkinson σ ≈
0.6 × range, giving the arms systematically different widths (~1.5–1.7×) before any information
effect. That is the EXP-025 seam (L-21) and it would have corrupted the one comparison the L4 stage
exists to make.

```
UNMODULATED arm: a * s_hat_uncond  =  the SAME Parkinson-EWMA estimator, in bps, but its
                 TRAIN-median CONSTANT per symbol - i.e. the boundary does not respond to the
                 forecast. Same unit, same estimator, same clock as the modulated arm.
MODULATED arm:   a * s_hat(t, h)   =  the same object evaluated conditionally at t.
=> the ONLY difference between the arms is whether the width RESPONDS to the forecast, which is
   precisely the "does volatility information help" question. No level shift, no unit seam.
ATR20 is retained ONLY as the deltaThreshold normaliser (SoT SS6.1 defines the entry that way);
it never sets an exit boundary.
HORIZON SCALING: s_hat(t,h) = s_hat_H1(t) * sqrt(h_hours), with h expressed in HOURS on both
   clocks. On M15 a 4-bar hold is h=1 hour, NOT h=4 - stated because the bar-vs-hour ambiguity is
   a 2x inflation and is exactly the EXP-025 failure.
E[run] is measured in H1 bars; on M15 it is converted to hours first, never applied as a bar count.

MODULATED HOLD - the exact equation (without it, MOD and UNMOD are the same hold and the pair
measures nothing):
    E_run(t) = clip( p_stay(t) / (1 - p_stay(t)), 1, 48 )        expected remaining run, HOURS
    h_mod(t) = clip( h * E_run(t) / 20, 1, 20 )                  the modulated hold, HOURS
  - h is the paired UNMODULATED hold from {1, 4, 12, 20}; the divisor 20 is that grid's own top
    value, so h_mod == h exactly when E_run sits at the measured 19-23h E[run] scale. The device
    therefore LENGTHENS the hold in sticky states and SHORTENS it in unsticky ones, around the
    same anchor its comparator uses. No rounding: an hour-valued hold resolves at the first
    decision-clock open at or after it, per SS2.
  - p_stay(t) is the R-MARKOV same-state transition rate estimated on at least 30 PRIOR
    transitions sharing the current origin state, with BOTH endpoints strictly before t. Below 30
    the event is INELIGIBLE for the MOD-hold row and is excluded from it, with the count and the
    reason emitted; it stays in every other row. The latest eligible H1 value is held forward, no
    backfill.
  - The clips are structural, not tuned: [1, 48] bounds the odds ratio at one hour and two days,
    and [1, 20] keeps h_mod inside the same declared grid its comparator lives in. E[run] is used
    as a SCALE here, never as a timer (V14, evidence class [D]).
```

**Hold values are stated in HOURS on both clocks**, because the scale that bounds them is a calendar
quantity: the **measured** regime run-length `E[run]` 18.9–23.1 H1 bars ≈ **19–23 hours**, MAE ~12
(evidence class `[D]`, so it sets a *scale*, never a timer). The grid `{1, 4, 12, 20}` hours spans
that scale from well inside it to its lower edge, identically on M15 and H1. Nothing outside the
scale is swept.

*(An earlier draft stated the grid in **periods**. On M15 that made the whole sweep 0.25–5 hours —
entirely below the 19–23 hour scale the same paragraph claimed bounded it — and the longest M15 hold
a quarter of the shortest H1 hold in the same grid. The conversion clause existed for the modulated
arm only; it now governs both arms and the unmodulated grid itself.)*

### 4.3 Phase (b) — the full cross

> **Phase (a) determines WHETHER phase (b) runs. It does NOT determine WHAT is in it.**

**TRIGGER — pre-declared here, before phase (a) runs (registered AMENDMENT-C6; reflection
§5.9.1).** The condition is stated on the phase-(a) reads themselves:

```
Phase (b) MAY run only if, in the phase-(a) emission on the primary read, AT LEAST ONE of:
  (i)  some layer/device cell has  Delta log R vs L0  with ci_low > 0, or
  (ii) some layer/device cell has  absolute log R     with ci_low > 0   (H1 only - on M15 the
       absolute read is an ENTRY statement, SS8.1, so it cannot trigger (b)).
Otherwise phase (b) DOES NOT RUN, and that is the pre-declared outcome.
```

This uses the §9 CI-relative band vocabulary and introduces **no magnitude** — there is no effect
size to pick, and none is picked. It is a **stopping rule on a phase**, not a value gate on a
cell: nothing is admitted, excluded, labelled or ranked by it, no cell is dropped, and every
phase-(a) cell is reported in full either way (INFR-016 intact).

The condition is **necessary, not sufficient**: phase (b) additionally requires its own operator
execution authority and its own design amendment. The operator may decline a fired trigger. What
the operator may **not** do is decide after seeing (a) what "promising" meant — that is the
optional-stopping hole C6 exists to close, and it is now closed.

*(An earlier draft — AMENDMENT-7, now superseded — replaced this condition with post-(a) operator
judgement and carried a standing execution blocker because a design cannot amend a registered
family amendment by disclosing that it disagrees with it. The condition is restored, so the
blocker is discharged rather than escalated.)*

**The SCOPE is pre-declared too, and is what prevents the overfitting.** Phase (a) may inform
*whether* phase (b) runs; it may never shrink what phase (b) contains.

**Scope, fixed and independent of the (a) outcome:** the complete {L1, L2, L3} × {target, trail,
hold, sizing} cross on the same episode population. **Individually-flat layers stay in the grid on
equal footing** — a layer can be flat alone and productive in combination, and pruning makes that
permanently undiscoverable. **Estimand:** the **interaction**,
`Δlog R(combined) − Σ Δlog R(individual)`, not the combined main effect.

**Resolution statement for the (b) grid — what replaces C6's `NOT_RESOLVABLE` booking.** Registered
AMENDMENT-C6 requires that *"a grid that cannot resolve the interaction is booked `NOT_RESOLVABLE`
rather than run and explained"*. AMENDMENT-C7 — later, and specific to these two designs — forbids
emitting that flag anywhere. **C7 supersedes the flag; it does not supersede the obligation.** The
obligation is discharged without the flag as follows:

```
The phase-(b) design amendment MUST state, per cell and BEFORE (b) runs:
  - the expected n, computed from phase (a)'s REALISED per-cell n (not predicted afresh), and
  - the expected mde50 for the INTERACTION estimand, from the c basis artifact, and
  - the fraction of the (b) grid whose expected mde50 sits above EACH of the six registered
    ladder rungs {0.02, 0.03, 0.05, 0.075, 0.10, 0.15} - the whole six-number distribution.
That distribution is REPORTED, not adjudicated. It is what C6 wanted booked; the operator judges
whether the grid is worth running, and records the decision. No rung is privileged - an earlier
draft summarised only the 0.10 rung, which handed one arbitrary rung a canonical role the
programme retired. No cell is labelled, and no grid is auto-refused.
```

Phase (b) requires **its own operator execution authority** and a design amendment recording the
final cell count, the per-cell MDE and the resolution statement above. It is not authorised by this
document.

---

## §5 Estimand and the primary read

```
Per episode:  r = signed gross return in bps, from the ENTRY FILL price to the EXIT FILL price,
              both defined in SS2. (The time exit is open-to-open; target and trail exits fill at
              their own trigger prices. 'Open-to-open' describes the TIME exit only - it is not a
              blanket statement about every exit, and an earlier draft's wording implied it was.)
Per cell:     p     = P(r > 0)                    W = E[ r | r>0]     L = E[-r | r<0]
              W_L   = W/L                         p_be = L/(W+L)
              log R = log(W_L) - log((1-p)/p)     <-- THE PRIMARY READ
              identity assertion: |p*W - (1-p)*L - mean(r)| < 0.01 bps, EVERY cell
DISCLOSED REFERENCE ONLY (never a threshold, never a comparison, AMENDMENT-C5):
              cost, p_be_net = (L+cost)/(W+L), net mean, and the distance to the cost floor
```

**The mirror is exact, not fitted.** `log R = 0` ⟺ `W/L = (1−p)/p` ⟺ `p = p_be` ⟺ `E[gross] = 0`.
**The fitted-slope form (0.9408) is refused as a target**: its residual is centred at zero by
construction and no policy can beat it on average (reflection §A / audit A1).

κ = `median(r / mfe)` is reported as a **non-tradable, ceiling-relative diagnostic**. It multiplies
nothing (SoT §2.1).

---

## §6 Controls

```
CONTROL MIRROR-NULL (primary):
  question answered: is this cell's payoff distinguishable from the arithmetic zero line its own
    rate forces?
  population: the cell's own episodes. NOT disjoint by construction - and it does not need to be,
    because this is a POINT null (log R = 0), not a two-population comparison. The disjointness
    requirement (B-1) applies to matched-control designs; stated here explicitly so QA does not
    read its absence as an omission.
  bite/MDE: block-bootstrap CI on log R under SPDR-018's inherited block rule (SS8.1). Per-cell
    MDE in log units is emitted BEFORE the read (see SS8), with the effective sample size, the
    realised c and the control's own sensitivity ladder. No adequacy cutoff is applied; the reader
    judges resolution from the ladder.
  non-vacuity: log R is a function of p, W and L jointly; the null perturbs none of them - it is
    an analytic reference value, so vacuity does not arise. What could refute it: any cell whose
    CI excludes 0.
  expected outcome if H true: log R CI-low > 0 on some cell. If H false: CI covers 0 (the
    SPDR-018 result, where the centre sat at -0.0301).
  disclosure: the distance in log units and the implied bps, both reported. COLLAPSE FRACTION
    (B-2): N/A by construction and stated so rather than omitted - this is a POINT null, so
    there is no control effect to divide by the raw effect. Recorded as `collapse_fraction:
    null, reason: POINT_NULL` so the field is never silently absent.

EXIT-MATCHING, BINDING ON BOTH DERANGEMENTS (L-24.2 / F04, QA run 6): every deranged seed is
  RE-RESOLVED on the M1 stream UNDER THE SAME EXIT RULE as the live arm it referees. Negating r
  is exact only where the exit is time-based; on a target or trailing-stop arm the SIDE decides
  WHICH BARRIER IS HIT AND WHEN, so a sign flip would referee a path the deranged position never
  took. Concretely: the deranged side/timing is applied first, then the entry fill, the barrier
  levels and the exit are resolved again from M1 exactly as SS2 specifies, and r is computed from
  the re-resolved fills. The cheap negation shortcut is PERMITTED ONLY on the time-exit arms
  (L0, the hold devices) and is asserted per arm in SS12. Where a device's null cannot be
  exit-matched at all, that device's control is demoted to DISCLOSURE and labelled as such.

CONTROL SIDE-DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: does the entry's SIDE carry information, or would random sides produce the
    same payoff geometry?
  population: the same episodes with sides deranged; DISJOINT in labelling from the live series -
    every episode's side differs from its own (zero fixed points).
  bite/MDE: >= 2000 seeds; plant curve co-designed - inject +5/+10/+20/+40 bps of true side
    information, stated ALSO in sigma-hat units (0.068 / 0.137 / 0.274 / 0.548 sigma at the
    measured pooled sigma-hat = 73.00 bps) and RE-DERIVED per universe at run, never carried as an
    absolute bps bar across a universe boundary (L-50 / P-21). Report the detection rate at each
    rung. The control is reported UNUSABLE for any effect below its own plant-curve resolution.
  non-vacuity: deranging the side flips the sign of r, which moves the MEAN, p, W and L - the
    exact sufficient statistics of log R. It is not mean-preserving (B-6 satisfied).
  expected outcome if H true: live log R above the null distribution. If H false: inside it.
  disclosure: percentile + the null's own mean, sd and quantiles (P-24), never a bare percentile,
    AND the COLLAPSE FRACTION (B-2) = deranged log R / live log R, emitted with the percentile.
    Disclosure only: it is not a threshold and appears in no HARD list (M-5 - this object sits
    at a near-zero mean, where a collapse ratio is unstable by construction).
  destroy form: DERANGEMENT (zero fixed points, asserted and counted; L-28).

CONTROL ENTRY-TIMING DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: is the payoff geometry a property of the SIGNAL's timing, or of the ambient
    return distribution at matched holding length?
  population: episodes whose entry timestamps are deranged within symbol, holding length and side
    preserved. Disjoint in timing from the live series (zero fixed points).
  bite/MDE: >= 2000 seeds; same plant curve.
  non-vacuity: re-timing changes which returns are realised -> moves p, W, L (B-6 satisfied).
  expected outcome if H true: live log R above the deranged null. If H false: inside it.
  disclosure: percentile + null mean/sd/quantiles, AND the COLLAPSE FRACTION (B-2) = deranged
    log R / live log R. Disclosure only, never a threshold (M-5, near-zero mean).
  destroy form: DERANGEMENT (L-28).

CONTROL MAGNITUDE-MATCHED COMPARATOR (M-3 - MANDATORY for L1 and L3):
  question answered: for any layer defined on move SIZE, is the effect "the volatility state" or
    merely "this was a big bar"? SPDR-018 measured mag_high at percentile 0.46 against exactly
    this comparator - the distinction is real and it has bitten before.
  population: episodes NOT selected by the layer, matched on realised |decision-bar move| decile.
    DISJOINT from the selected population by construction; disjointness asserted per decile.
  bite/MDE: plant curve per decile; the comparator is reported UNUSABLE where its own plant curve
    is blind.
  non-vacuity: it substitutes a different episode population at matched magnitude - p, W, L all
    move.
  expected outcome if H true: selected log R above matched. If H false: equal.
  disclosure: MANDATORY per P-24 - the comparator's OWN mean, its null quantiles, AND its plant
    curve are emitted with every percentile. A percentile alone is uninterpretable and is refused.
    COLLAPSE FRACTION (B-2) = matched-comparator log R / selected log R, emitted per decile.
    Disclosure only, never a threshold (M-5).
```

### 6.1 Leak tripwire (HARD — blocking)

```
Both tripwires are STRUCTURAL: they pass or fail on counts and identities that are decided by the
construction, never on the size of a payoff difference. Payoff deltas ARE emitted with their CIs,
and they are INFORMATIVE ONLY - a magnitude pass rule would turn a validity check into an effect
gate (L-24.3). Every named field below is written to results/integrity_selfcheck.json.

TRIPWIRE-1 (causal misalignment):
  form: rebuild every layer's conditioning state from bar `[+1]` (one bar into the future) instead
    of `[0]`, and re-run the identical pipeline. Both state streams are materialised before the
    comparison.
  emitted statistics: `shift_is_exact_one_row` (bool), `changed_state_rows`,
    `changed_selection_episodes`, `legal_episode_count`, `leaky_episode_count`, and the paired
    deltas in p, W, L and log R with CIs.
  HARD PASS, fixed before the run - ALL THREE:
    `shift_is_exact_one_row == true`       the leaky stream is the legal stream shifted by exactly
                                           one decision-clock row, with no other difference
    AND `changed_state_rows > 0`           the illegal input actually differs somewhere
    AND `changed_selection_episodes > 0`   that difference actually reaches episode selection or
                                           exit placement
  Expected direction (reported, never asserted as a pass condition): the leaky twin's log R is
    higher. A design that required a direction or a magnitude here would be gating on an effect.
  vacuity check: the leaky state changes which episodes are selected and how their exits are
    placed -> it moves p, W and L, the sufficient statistics of log R. Non-vacuous.
  if permutation-based: N/A (not a permutation - a deliberate index shift).
  A missing, empty or zero-count field is a FAILURE, never a vacuous pass (P-23/L-52).

TRIPWIRE-2 (fill-rule look-ahead) - COVERS ENTRIES AND EXITS (QA run 1 required fix):
  form: two deterministic twins, both re-resolving ALL fills - entry stops AND the L4 exits
    (target, trail, time):
      (a) DECISION-CLOCK twin: resolve fills on the decision-clock bar's OHLC instead of the M1
          stream;
      (b) FAVOURABLE-PRECEDENCE twin: keep M1 resolution but let the TARGET win inside an M1 bar
          where both target and trail/stop are reachable (SS2 mandates the ADVERSE branch).
  emitted statistics: `clock_vs_m1_differing_fill_ids` and its count;
    `both_reachable_bar_ids` and its count; `favourable_precedence_differing_fill_ids` and its
    count; per differing id, the two fill prices; plus paired payoff deltas with CIs.
  HARD PASS, fixed before the run - ALL FOUR:
    `count(clock_vs_m1_differing_fill_ids) > 0`
    AND `count(both_reachable_bar_ids) > 0`, where `both_reachable_bar_ids` counts only M1 bars
        in which the target and the trail/stop levels are DISTINCT prices; bars where the two
        levels coincide cannot differ under either precedence and are counted separately as
        `price_identical_bars`, never as a failure
    AND `count(favourable_precedence_differing_fill_ids) == count(both_reachable_bar_ids)`
    AND for EVERY id in `favourable_precedence_differing_fill_ids`, the favourable twin's fill
        price is mechanically no worse for the position than the emitted arm's
        (LONG: favourable exit price >= emitted; SHORT: <=), asserted per id.
  The third clause is what proves the adverse rule is actually implemented, and it is a price
  comparison per episode - not an aggregate effect. The differing-id LISTS, not just the counts,
  are emitted so QA can re-derive them from the catalog.
  vacuity check: fill prices enter r directly -> they move p, W and L. Non-vacuous.
  A missing, empty or zero-count field is a FAILURE, never a vacuous pass (P-23/L-52).
```

---

## §7 Unit pin (L-21 / P-15)

```
CONVERSION-PIN:
  divisor object 1: Wilder ATR(20) on the decision clock, evaluated at bar [0], causal <= t-1.
                    This is the `deltaThreshold` normaliser AND NOTHING ELSE. Verbatim from
                    SoT 6.1. It NEVER sets an exit boundary and never appears in any L4 arm:
                    the UNMODULATED L4 devices are bound to `s_hat_uncond` (divisor object 2,
                    per-symbol TRAIN median), the same estimator as the modulated arm. Pairing a
                    Wilder-ATR arm against a Parkinson arm is two estimators at a ~1.5-1.7x level
                    shift (Wilder ATR ~ mean true range, Parkinson sigma ~ 0.6 x range) - the
                    EXP-025 seam (L-21) that the L4 comparison exists to avoid. SS12 asserts it.
  divisor object 2: s_hat = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1,
                    in bps, horizon-scaled s_hat*sqrt(h). IDENTICAL object to SPDR-014's Z-VOL
                    width and SPDR-018's unit pin - reused, not redefined.
  measured value:   TRAIN-median of BOTH objects, per symbol and pooled, COMPUTED AT RUN ->
                    results/unit_pin.json. Never recalled, never asserted. Covers all 25 symbols
                    or states the gap explicitly.
  resulting effect: every effect reported in BOTH bps and sigma units, side by side, on every cell.
  cost floor:       13.1-16.1 bps partial (fees + discrete funding + allowance); spread NOT
                    charged, so the true floor is strictly higher. Emitted as a DISCLOSED
                    REFERENCE only - no read in this design is compared against it (AMENDMENT-C5).
                    A sigma-unit effect is NEVER compared to the floor (P-15).
```

**bps is primary everywhere.** σ̂-normalisation buys pooling power; it never becomes a headline in
its own units.

---

## §8 Resolution statement — sensitivity across a range, not a single bar

**No resolution figure is typed into this document.** Every one is computed by
`xen.resolution_basis` from SPDR-018's emitted cells and pinned to `results/resolution_basis.json`.
This section states the METHOD and the artifact; the numbers live in the artifact.

```
DEFINITION (xen.resolution_basis):
    mde_log = block_mde_bps / ((1-p)*L)          MDE in log-residual units
    c       = mde_log * sqrt(n)                  dimensionless -> ports across arms, clocks,
                                                 universes (L-50)
    required n at target D = (c/D)^2             mde50 at size n = c/sqrt(n)
c RISES with n, which is the block-dependence penalty. That is measured, not assumed.

HORIZON: the derivation expects block_mde_bps and (1-p)*L to rise with h and cancel, leaving c
  horizon-invariant. THE ARTIFACT REFUTES THAT AS A CATEGORICAL CLAIM AT THE TARGET SCALE and the
  design carries the measurement, not the expectation: in the 15,000+ band the arm-C horizon
  medians are h=4: 11.855, h=12: 8.363, h=24: 11.744 - a 1.42x spread on 6 / 14 / 6 cells. So no
  "c is flat" statement is made anywhere, the basis artifact emits `horizon_summaries` per band,
  and any expected mde50 read off a band median inherits that band's horizon spread as
  uncertainty. An earlier draft asserted flatness and was wrong exactly where it mattered.

WHY THIS IS A FUNCTION AND NOT PROSE: three successive drafts of this section typed three different
constants, each pairing a numerator and a denominator drawn from DIFFERENT populations - k=370 on a
precision-selected subset; k=948 full-population; and a horizon-split k paired with a
powered-subset (1-p)*L = 48.5, which overstated required n ~6.9x. Every one of those was arithmetic
in prose, where nothing could check it. Resolution figures are now emitted, versioned and diffable.

POPULATION - ONE, DECLARED AND ENFORCED (QA run 5):
  The basis is computed on SPDR-018 ARM C ONLY - the signed parent arm - and the artifact pins the
  filter (`input_filter`), the row accounting and the exclusions by reason. Measured:
  24,098 source rows -> 18,988 matched by `arm == 'C'` -> 18,479 retained, 509 excluded, all 509
  for a missing required value and none for any other reason. An earlier artifact was computed on
  ALL arms while the design quoted the arm-C thinness figures; two populations cannot both be the
  pinned basis, and the row accounting now makes the population unambiguous and every drop
  visible.

BASIS PROVENANCE AND ITS LIMIT (recorded because reusing c across CI rules is unsound):
  c was measured on SPDR-018 arm-C cells whose CIs used SPDR-018 SS6.2's rule, quoted WORD FOR
  WORD in SS8.1 and pinned as `source_ci_rule` in the artifact. This design adopts that rule
  UNCHANGED, so c transports correctly. Reusing c under a weaker rule would understate this
  design's own uncertainty - the failure direction that matters.

THINNESS IS DISCLOSED, NOT FLATTERED (the artifact carries `cells` AND `distinct_n` per band):
  the 15,000+ band holds 26 rows but only 8 DISTINCT sample sizes across 3 bases. WHICH band this
  design's strata land in is NOT predicted - no n is forecast anywhere (SS8.1), so the band is
  assigned from the realised n when it exists. Its interquartile spread is therefore NOISE, not a defensible range, and
  NO "range across bases" claim is made from it. An earlier draft treated it as a range, picked anchors of c = 7.5 and 9 that were measured on
  neither band, asserted that "0.03 is out of reach at EVERY basis", and then rebutted itself with
  a c = 5.4 anchor and a predicted "50k-60k episodes for the primary stratum". All of it is
  WITHDRAWN: c = 5.4 appears nowhere in the arm-C artifact (its smallest band median is 5.634),
  and this design forecasts NO episode count for any stratum (SS8.1). The crossing point is read
  off the artifact's own `required_n_by_band` grid when a realised n exists, not predicted here.
```

**The direct check, computed the same way.** Arm-C pooled cells with `n ≥ 10,000` realise
0.053–0.107 log units (41 cells); the three largest sample sizes (`n` = 20,977 / 20,572 / 20,279)
realise 0.0727–0.0945 across their nine cells, with the per-horizon spans overlapping
(h=4: 0.078–0.094, h=12: 0.076–0.082, h=24: 0.073–0.090) — close together at this `n`, which is
a measurement at this scale and not a flatness claim. **0 of the 18,479 retained arm-C cells reach
0.03**, other than three degenerate `n = 2`, `p = 0` cells which carry no information.

**The available population, read from the artifact — not from date arithmetic.**
`SPDR-018/results/unit_pin.json` records the actual TRAIN bar count:

```
pooled H1 bars, 25 symbols, full TRAIN = 229,646     <-- NOT 25 x 21,648 = 541,200
  only MATICUSDT (21,582) spans the window; median symbol = 12,444; smallest = 555
  catalog history cap: the panel is one symbol deep before 2022-07-14 (M-4)
```

*(An earlier draft assumed ~541k bars from the TRAIN date range. That was wrong by 2.35× and the
correct figure was in the file this section already cited. Corrected here against the artifact.)*

**Two power levers are applied, both for power alone** (operator directive 2026-07-28):

| Lever | Effect on `n` | Cost |
|---|---|---|
| **Full TRAIN is the primary read**; DESIGN/CONFIRM scored as verification | **~2×** | The band split becomes a stability check rather than the primary object. SPDR-018's own power lever 2 |
| **M15 added as a capture clock**, with the scale forecast ŝ still computed on **H1** | **~4×** | Multiplicity: two clocks reported separately, never pooled. Legitimate because the capture question is about exit geometry, not intraday forecast skill — V4's "no within-day skill" constrains the *forecast*, which stays on H1 |

```
RESOLUTION (replaces the pass/fail POWER block; operator mandate 2026-07-28):
  Every cell emits a SENSITIVITY LADDER instead of a powered/unpowered verdict. For a fixed
  ladder of candidate effect sizes, the cell reports the fraction of block-bootstrap replicates
  in which a PLANTED effect of that size would have been detected at its own realised n:

      ladder = { 0.02, 0.03, 0.05, 0.075, 0.10, 0.15 }  log units

  PLANT OPERATOR (must be stated, or the ladder is ambiguous - QA run 2):
    PRIMARY: plant delta on the residual by scaling W/L by exp(delta) with p HELD FIXED. This is
      the operator a capture policy actually acts through - exits move payoff asymmetry.
    CO-REPORT: the same delta planted through p at fixed W/L. Detection rates differ between the
      two, and BOTH are emitted per rung. Neither is privileged; the pair shows how
      operator-dependent the cell's resolution is.

  CURVE SUMMARY, replacing a single bar (three points, none canonical):
      mde50 / mde80 / mde95 = the effect size detectable in 50% / 80% / 95% of replicates,
      interpolated from the ladder.
    These are DESCRIPTIVE re-parameterisations of the same curve. They restore separability -
    cells can be counted, sorted and compared - WITHOUT any rung or rate being the admission
    bar. No cell is admitted, excluded, labelled or ranked by them.
    (QA run 2 proposed a `finest_rung_detected` field; that requires picking a privileged
    detection rate, which would reintroduce exactly the cutoff this mandate removed. Reporting
    three points of the curve achieves the same separability with no privileged value.)

  Emitted per cell:  realised n | block MDE | CI width | detection rate at each rung, per plant
                     operator | mde50/mde80/mde95 | the n required at each rung.
  No cell is flagged powered, unpowered or NOT_RESOLVABLE. A cell with coarse resolution reports
  coarse resolution, in numbers, and is still reported in full.
  MDE is always the dependence-matched BLOCK form (M-1), built under the SPDR-018 block rule
  inherited verbatim in SS8.1; the iid form is companion-only and may never be presented as the
  cell's resolution.

  B-5 ENFORCEMENT (QA runs 2 and 3 - the label was categorical and therefore countable; these
  restore that property without a threshold, and are HARD schema checks, not conventions):
    1. No `log R` value ships in ANY artifact without `ci_low`, `ci_high`, `ci_width` and
       `block_mde` present on the SAME ROW. Asserted over metrics_by_cell, layer_deltas and the
       resolution ladder alike.
    2. Any AGGREGATE statement over cells ("N of M covered the mirror") must carry the
       resolution distribution of those cells - median mde50 and the count below each rung.
       An aggregate without it is a negative-by-omission, which B-5 forbids as squarely as a
       dropped label does.
    3. The expected-resolution table (below) is PREDECLARED per stratum, at the granularity the
       design reports. Predeclaration was the real content of the retired POWER block and is
       orthogonal to the label; it is retained.
    4. PREDECLARED vs REALISED on the same row (QA runs 3 and 5). Each stratum's predeclared
       expected n and expected mde50 ship alongside its realised n and realised mde50 in
       resolution_ladder.parquet, with the signed difference where a prior exists.
       THE OPERATIVE B-5 PROTECTION IS CLAUSES 1-3: same-row realised CI/MDE, the aggregate
       resolution distribution, and the ban on negative-by-omission. Clause 4 is a CALIBRATION
       AUDIT of the forecast, not the protection itself, and inference never consumes it: all
       interpretation and every aggregate use the REALISED CI / MDE / resolution curve only.
       Nothing is admitted, excluded, labelled or ranked by the comparison. `analysis.md` must
       report the full signed discrepancy distribution rather than a summary of it.
```

**What this changes and what it does not.** The conversion `Δlog R ≈ Δmean / ((1−p)·L)` and the
`n`-scaling below are **derivations** and stand unchanged — they are how resolution is computed. What
is removed is the single canonical bar that used to turn them into a verdict.

### 8.1 M15 — the evidence both ways, and what it forces (QA run 2)

SPDR-013 measured M15 on both axes and they point in opposite directions. An earlier draft cited
neither; both are binding here.

| | Finding | Source |
|---|---|---|
| **For M15** | the next-swing **magnitude** forecast is **better on M15 than H1, on all 25 symbols** (OOS IC 0.34–0.46, ridge ≥ AR1) | SPDR-013 `analysis.md` §7 |
| **Against M15** | **direction** on M15 reads **worse than shuffled** — side-derangement percentile **0.20–0.28** against 0.48–0.57 on H1, with a +20 bps bite plant detected; gross −2 to −3 bps | SPDR-013 `analysis.md`, DIRECTION-DERANGEMENT |

M15 is therefore the **better clock for the quantity this design uses it for** (scale) and the
**worse clock for the quantity this design does not target** (direction).

**What it forces.** If the M15 `L0` baseline sits below the mirror — which the direction evidence
makes likely — then under §9's CI-relative bands **every M15 cell would read "below the mirror",
and that would be a statement about the ENTRY, not about capture geometry.** So:

```
On M15 the PRIMARY read is  Delta log R  =  log R(layer) - log R(L0),  not absolute log R.
  - The layer protocol already emits this (results/layer_deltas.parquet); it is now the headline.
  - Absolute log R is still emitted and still banded, but on M15 it is labelled an ENTRY
    statement and may not be reported as a capture-geometry result.
  - The L0 baseline's own position relative to the mirror is reported explicitly, with its CI and
    resolution, so the reader sees what the deltas are measured from.
  - On H1 both absolute and delta reads are reported; H1 is where the absolute read is
    interpretable.
```

**Block dependence caps the M15 gain, and the block rule is the parent's own so it cannot be
understated.**

```
BLOCK RULE (binding, both clocks, code-asserted) - INHERITED VERBATIM FROM SPDR-018 SS6.2, which
is the emission SS8's c basis was measured on. It is not a new rule and contains no invented
constant. All five clauses are binding; quoting a subset is how an implementer ends up choosing
their own sweep and calling it compliance (QA run 5):
    1. aggregate to PER-CALENDAR-DAY SUFFICIENT STATISTICS;
    2. resample day-blocks of {1, 3, 7} DAYS - the full sweep, not "a sweep";
    3. minimum block = 1 day = 24 H1 bars, >= every horizon in scope;
    4. envelope = MIN/MAX over blocks x seeds (CONSERVATIVE), 5-SEED battery;
    5. call `xen.evaluation.block_bootstrap_ci`, with the EFFECTIVE BLOCK CAPPED < n
       (INFR-004 / L-20);
    6. THE REPORTED MDE IS THE BLOCK MDE (SoT SS9 M-1); the iid 2.8sigma/sqrt(n) form is emitted
       ONLY as a labelled companion column and may not drive a band label.
  THIS SIX-CLAUSE LIST IS THE CANONICAL LITERAL. `source_ci_rule` in
  results/resolution_basis.json quotes SPDR-018 SS6.2's own text and nothing else, so the rule
  this design runs under and the rule c was measured under are the same text; SS12 checks it
  CLAUSE BY CLAUSE against this list rather than by string equality, because a string comparison
  fails on whitespace and passes on a paraphrase.
  ADDITIONALLY REQUIRED BY THIS DESIGN (an emission requirement, NOT part of the inherited rule
  and deliberately not folded into the pinned string): the PER-SEED bound spreads and the
  PER-BLOCK-LENGTH sensitivity are emitted per cell, not just the final envelope. A single
  collapsed envelope hides exactly the fragility INFR-004 added the sweep and battery to expose.
  - A DAY is a calendar unit, so the rule is identical on M15 and H1 by construction. This is what
    closes the M15 problem: a block stated in BARS would span 3 hours at h=12 on M15 against 12
    hours on H1, while the clustering the L2 state axes and s_hat condition on is calendar
    persistent at the 19-23 hour E[run] scale. Under-blocking UNDERSTATES variance, narrows CIs and
    manufactures `ci_low > 0` - the design's only positive band - on the clock carrying the primary
    read. That is the Phase-010 shape (block=5 on H=48 windows understated uncertainty 2-3x).
  - The block SWEEP and the SEED BATTERY are not optional trimmings: INFR-004 / L-20 added them
    after single-seed, single-block CIs proved fragile at small n. An earlier draft of this design
    replaced the parent's rule with a SINGLE block length of `max(hold hours, 20 hours)`, dropped
    the sweep and the battery, called the change a TIGHTENING, and asserted that c had been
    measured under it. All three were wrong: 20 hours is looser than 24 at short horizons, a single
    block length is looser than a min/max envelope, and the parent used the rule above. Withdrawn.
  - It follows that c transports into this design correctly, because the CI construction is now the
    same one c was measured under.
  - Realised EFFECTIVE sample size is emitted per cell alongside n.
```

Consequently the "~4×" in the lever table is an upper bound on `n`, **not** on precision, and the
realised gain is whatever the emitted effective sample size says it is.

```
EXPECTED RESOLUTION, PER STRATUM - PREDECLARED BY GENERATION, AND IT ALREADY EXISTS.
  Predeclaration is required (design-requirements SS6, B-5). It is COMPUTED and PINNED rather than
  hand-written, and - the point QA run 5 made - it is GENERATED AND COMMITTED NOW, before any
  implementation or outcome access. Naming a future path is not a predeclaration.

    results/resolution_basis.json          the arm-C c bands: cells, distinct_n,
                                           horizon_summaries, row accounting, source_ci_rule
    results/expected_resolution_prior.json the declared axes and the parent priors that exist
    -> results/expected_resolution.json     the expansion. COMMITTED, DATED 2026-07-29T00:00:00Z,
                                           SHA-256-pinned on its inputs.

  GENERATOR (deterministic, tested, re-runnable by QA):
      python -c "from xen.resolution_basis import write_expected_resolution as w; w(
        'experiments/SPDR-019/results/expected_resolution_prior.json',
        'experiments/SPDR-019/results/resolution_basis.json',
        'experiments/SPDR-019/results/expected_resolution.json',
        generated_at_utc='2026-07-29T00:00:00Z', source_hashes=<pins>)"

  SCHEMA - one row per declared stratum, grain `(clock, delta, variant_id, scope)`:
      clock in {M15, H1} x delta in {0.25, 0.5, 1.0} x the 33 variant_ids of SS4.1a
      x scope in {POOLED, each of the 25 pinned universe symbols}
      = 2 x 3 x 33 x 26 = 5,148 rows, none omitted, none a placeholder.
      Each row carries: prior_status, expected_n, n_band, c_median, expected_mde50.

  WHAT IT SAYS, and why that is the honest answer: EVERY row is
  `prior_status = UNKNOWN_NO_PARENT_MEASURED_POPULATION` with `expected_n` and `expected_mde50`
  NULL. No parent ever ran this entry - SPDR-018 measured the parents' own exit geometries on
  different entry objects, and no emission in the programme carries a signal, fill or episode
  count for the SoT SS6.1 breakout at any (clock, delta). An invented number here would be worse
  than a null, and the withdrawn "~13-16k on H1 / ~50-60k on M15" figures were exactly that: a
  date-range-shaped guess (M-4). The c basis is pinned alongside, so the moment a realised n is
  measured it converts to a resolution without re-deriving anything by hand.
  `COMPUTED AT RUN` appears in no RESOLUTION artifact (the unit pin's measured medians are a
  different thing - they are measured from data at run, not forecast): an explicit typed null
  with a stated reason is a
  declaration; a promise to fill a field in later is not.
  The <=4 L5 combinations are excluded by construction and require their own dated, hash-pinned
  addendum from the same generator before L5 runs (SS4.1a).

  BAND AXIS AND THE JOIN KEY (QA run 6): the predeclaration is stated at the FULL-TRAIN grain,
  which is the primary read (SS10). The DESIGN and CONFIRM verification rows are the same strata
  scored on a sub-band, so they carry `band` as a fourth reporting column and JOIN to the
  predeclaration on `(clock, delta, variant_id, scope)` alone, inheriting that stratum's row.
  This is exact here BECAUSE every predeclared value is null: a band-specific expected n would
  otherwise need its own row rather than an inherited one, and this clause would be wrong.

  UNIVERSE PIN, stated because two files exist: the predeclaration's 25 symbols are hash-pinned
  from `SPDR-014/results/universe_recomputed.json`, while SS10 names the family pin
  `cf-voldir-001-universe.json` as the run-time authority. SS12 asserts SET EQUALITY between them
  before the run; if they ever differ, the predeclaration is regenerated and re-reviewed rather
  than reconciled by hand.

  OUTCOME FENCE: the generator's only inputs are the declared axes, the pinned universe file and
  the SPDR-018 arm-C basis. It reads no episode, no return and no outcome of this experiment,
  and it cannot: nothing of this experiment exists yet.

  STATED PLAINLY: a covering CI must read as "we could not see an effect this small here", never as
  "there is no effect" (B-5).

  RESOLUTION IS MEASURED, NOT FORECAST (HARD): every cell emits its OWN realised c alongside its
  realised n and mde50, and the predeclared expected n / expected mde50 ship on the SAME ROW with
  the signed `(realised - expected)` difference where a prior exists. ALL INFERENCE AND EVERY
  AGGREGATE USE THE REALISED CI / MDE / RESOLUTION CURVE ONLY. The predeclared-vs-realised pair is
  a CALIBRATION AUDIT: its full signed discrepancy distribution is reported, and it admits,
  excludes, labels and ranks nothing. It also means the NEXT design reads a measured c off this
  run instead of re-deriving one by hand.
```

**Consequence, stated plainly:** the primary reads live on **M15, full TRAIN, pooled across
symbols**, because that is where resolution is finest. H1 is the co-report and the clock-effect
check; per-symbol is heterogeneity disclosure. None of these is an admissibility rule — every cell
is reported with its own resolution attached, and the reader weighs them.

---

## §9 Interpretation bands — CI-relative, with no adequacy label (operator mandate 2026-07-28)

**Precision-first.** No cell carries a `powered` / `unpowered` / `NOT_RESOLVABLE` flag. Every cell
reports its **effect, its block-bootstrap CI, its CI width, its block MDE, and its resolution curve**
(§8), and the reader judges adequacy. Powering is left to later verification, not asserted here.

```
BANDS (per cell, on log R - defined by the CI's relation to the mirror, NOT by any magnitude):
  ABOVE THE MIRROR:  ci_low  > 0     the residual is resolvably positive on this cell's own data
  COVERS THE MIRROR: ci spans 0      report the point estimate, the CI WIDTH and the MDE together,
                     so a wide-CI cell and a genuinely-null cell are visibly different. This is
                     NEVER a refutation and NEVER a negative.
  BELOW THE MIRROR:  ci_high < 0     the residual is resolvably negative - itself a finding
                     (SPDR-018's centre sat at -0.0301)
No magnitude threshold appears in any band. An earlier draft used +-0.03 and a 0.07 adequacy
cutoff; both were anchored on sd(log R)=0.0729 and median log R=-0.0301, which are DISPERSION and
LOCATION of the observed residual - neither is a statement about what effect size matters. Removed
by operator mandate.

POOLED: the lane default is that a pooled figure is DISCLOSURE-ONLY (spdr-lane L-03). This design
  proposes pooled-across-symbol as the PRIMARY read, because that is where resolution is finest
  (SS8), and it may hold that status only conditionally:
    - every pooled figure is reported WITH a homogeneity statistic (I^2 across symbols) and the
      per-symbol spread behind it;
    - if the emitted homogeneity statistic does NOT support pooling, the pooled line REVERTS to
      the lane default and is reported as disclosure-only, with the per-symbol table as the read.
    - The OPERATOR judges that on the emitted value. No cutoff is written here and nothing is
      machine-dropped (INFR-016) - what is pre-declared is the CONSEQUENCE, so the lane default is
      the fallback rather than something this design discards a priori.
  Per-symbol figures are disclosure in either case.
EVIDENCE CLASS: rows still carry [S] scored / [D] disclosure per reflection SS2.0 - these describe
  WHAT KIND of read a row is, not whether it is adequate. The [P]/[U] adequacy classes are
  RETIRED for this experiment; adequacy is read off the MDE and resolution curve.
```

**No band is a gate, and no band is an adequacy claim.** Every value/quality read is a report layer;
the operator authorises what advances (INFR-016). Nothing is machine-dropped between layers.

**The B-5 protection: strengthened on emission, and conditional on §8 on inference.** B-5 exists so a
thin cell is never read as a negative. A boolean `UNPOWERED` flag delivered that with an invented
cutoff; **binding every effect to its own MDE and CI width on the same row (a HARD schema check,
§12) delivers it without one**, and the §13 refusal on aggregates lacking the resolution
distribution closes the negative-by-aggregation route a boolean left open. On the **emission** axis
the protection is genuinely stronger.

**Stated honestly, and corrected (QA run 5).** An earlier draft claimed the predeclared table *is*
the B-5 protection. It is not, and the claimed symmetry was overstated. The two forecast errors are
not equivalent in consequence: an **optimistic** forecast can help a covering CI be misread as
evidence of no effect — the actual B-5 harm — while a **pessimistic** forecast wastes resolved
evidence, which is bad evidence handling but an abstention, not a false negative. Nothing acts on
the comparison, so it makes miscalibration visible after the fact; it cannot stop a reader using a
wrong forecast.

**So the protection is on the emission side and it is unconditional:** every effect carries its own
realised CI, CI width and block MDE on the same row (a HARD schema check, §12); every aggregate
carries the resolution distribution of the cells behind it; and **all inference uses the realised
curve only**. The predeclared table is a calibration audit, reported in full as a signed
discrepancy distribution and consumed by nothing.

---

## §10 Scope

| Item | Freeze |
|---|---|
| Primary catalog | Bybit USDT linear perps, `data/catalog/`, INFR-011 fence |
| Fill resolution | **M1 (T1 lane) bars**, causal, no intrabar look-ahead |
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality |
| Clocks | **M15 primary** (power), **H1 co-report** (the clock-effect check). The scale forecast ŝ stays on **H1**. No D1. Clocks reported separately, **never pooled**. See §8.1 — on M15 the primary read is **Δ`log R` vs L0**, not absolute `log R` |
| TRAIN fence | `analysis_start 2021-06-29T06:53Z` → `train_end 2023-12-18T00:00Z`; asserted in code |
| Primary band | **Full TRAIN** (power lever 2). DESIGN `[2021-06-29, 2023-03-01)` / CONFIRM `[2023-03-01, 2023-12-18)` both scored as **verification**, `n`-weighted |
| Global holdout | `2025-01-08T00:00Z` — **never queried** |
| cTrader | **Not in phase (a).** Replication is a separate leg under AMENDMENT-C1 if the operator authorises it; never pooled into `n` |
| Complexity | 1 entry module, 1 layer module, 4 device modules, 1 metrics layer, 1 control module; ≤ 8 plots |
| `deltaThreshold` | **frozen**: `{0.25, 0.5, 1.0}`, all reported, none selected (§2) |
| Cell count | phase (a), **per `(clock, δ)` combination: ≤ 40 cells** — L0 1 + L1 4 + L2 5 + L3 3 + L4 **20** = **33 predeclared and named (§4.1a)**, + L5 ≤ 4 evidence-selected and declared by addendum before L5 runs = **≤ 37**. L4's 20 is §4.2's grid counted out: target 3+3, trail 2+2, hold 4+4, sizing 1+1. **Across the declared sweep: 33 × 2 clocks × 3 δ = 198 fixed cells, ≤ 222 once L5 lands, ≤ 240 with headroom** on full TRAIN, + the two verification bands. **Per-symbol expansion, disclosed rather than hidden:** every cell is also reported per symbol, so the emitted disclosure grid is `198 × (1 pooled + 25 symbols) = 5,148` rows — the exact row count of `expected_resolution.json`. Per-symbol rows are heterogeneity disclosure, not independent discoveries. **Disclosed, not rationed** (multiplicity disclosure, `spdr-lane.md` L-03). *(An earlier draft stated "≤ 60" against a stage sum of 61, quoted L4 as ~44 against §4.2's 20, multiplied the cap by the sweep, and omitted the per-symbol axis entirely.)* |

---

## §11 Golden traces (QA derives the numbers — the developer must not)

Deterministic selection rules, so QA computes expected values independently from the catalog.

```
G1 (entry + fill, the L0 baseline):
  BTCUSDT, H1, DESIGN. The FIRST bar satisfying the LONG condition at deltaThreshold = 0.5.
  QA computes: the three bar OHLCs, the pivot test, the ATR20 value at [0], the momentum ratio,
  the stop price (= high[0]), the first M1 bar that trades through it, the fill price, the exit
  timestamp at activeHold = 1 HOUR (one H1 bar here; four M15 bars on the other clock), the exit
  price, and r in bps.

G2 (expiry path):
  ETHUSDT, H1, DESIGN. The first SHORT signal whose stop is NOT reached within
  inactiveHold = 2 HOURS (two H1 bars here; eight M15 bars on the other clock).
  QA confirms: the order expires, the signal is EMITTED as unfilled, and it contributes to the
  fill-rate denominator but to no (p, W, L) term.

G3 (suppression, the B-9 guard):
  Any symbol, H1, DESIGN. The first signal arriving while an episode is already open.
  QA confirms: it is recorded SUPPRESSED and counted, and does NOT open a second episode.

G4 (the identity, and the primary read):
  The L0 pooled H1 CONFIRM cell. QA computes p, W, L from the emitted episode rows and asserts
  |p*W - (1-p)*L - mean| < 0.01 bps, then recomputes log R = log(W/L) - log((1-p)/p) from those
  same three numbers and asserts it equals the emitted log R exactly.

G5 (the mirror null is the exact one):
  The same cell. QA asserts that the emitted null reference is 0 for log R defined with SLOPE 1,
  and that NO fitted-slope residual appears anywhere in the emission. This trace exists solely to
  make audit item A1 non-repeatable.

G7 (exit fill precedence - the three clauses most likely to invert in code):
  Any symbol, M15, full TRAIN. The first episode in which BOTH a profit target and a trailing
  stop are reachable inside the SAME M1 bar. QA computes: which fills under the design's ADVERSE
  precedence rule, the fill price, and r in bps - and separately confirms (a) the trail ratcheted
  on M1 CLOSES only, never intra-bar, and (b) a time-exit episode fills at the OPEN of the first
  decision-clock bar at or after activeHold.

G6 (leak discrimination):
  The G1 rows under TRIPWIRE-1's leaky twin. QA confirms SS6.1's three structural conditions -
  `shift_is_exact_one_row`, `changed_state_rows > 0`, `changed_selection_episodes > 0` - and that
  the legal variant is the one that entered the research emission. No magnitude is asserted: the
  payoff delta is reported and carries no pass rule.
```

---

## §12 Integrity checklist (code-asserted; SPDR stage-2 self-check)

| Check | Assertion |
|---|---|
| **Check count** | the self-check asserts the **expected NUMBER** of HARD checks and reconciles them **by name** against this table (P-23 / L-52) |
| TRAIN fence | `max(exit_ts) < 2023-12-18T00:00Z`; zero rows at or after it |
| Holdout | zero queries `>= 2025-01-08` |
| Causality | every layer's state index `<= [0]`; ATR20 and ŝ exclude the decision bar's own forward information; TRIPWIRE-1 |
| Fill causality | every fill's M1 timestamp `>` its decision-bar close; TRIPWIRE-2 |
| Universe pin | top-25 recompute == pin file, set equality |
| **Identity reconstruction** | `\|p·W − (1−p)·L − mean\| < 0.01 bps` on **every** cell |
| **`log R` definition** | asserted equal to `log(W/L) − log((1−p)/p)` with **slope 1**; a fitted-slope residual appearing anywhere is a **hard failure** |
| **Cost isolation** | no cost term enters any estimand, threshold, band or comparison; `p_be_net` present and flagged `DISCLOSURE_ONLY` (AMENDMENT-C5) |
| **MDE column** | the reported resolution column is the **block** MDE in log units; the iid column is labelled companion-only (M-1) |
| **Block rule (inherited)** | block bootstrap uses SPDR-018 §6.2's rule verbatim, **checked clause by clause against §8.1's canonical six-clause list** (never by string equality): per-calendar-day sufficient statistics; day-blocks of **`{1,3,7}`**; minimum 1 day = 24 H1 bars ≥ every horizon; **min/max envelope over blocks × 5 seeds**; `xen.evaluation.block_bootstrap_ci` with **effective block `< n`** (§8.1). A single-block-length CI, a different or partial sweep, a missing seed battery, a missing daily aggregation, a missing small-`n` cap, or a block computed in bars is a **hard failure**. **Per-seed bound spreads and per-block-length sensitivity are emitted per cell**, not just the envelope; realised effective sample size and realised `c` emitted per cell alongside `n`. `source_ci_rule` in `results/resolution_basis.json` is asserted to be SPDR-018 §6.2's own text — this design's extra emission requirements are deliberately not part of that string |
| **Decile causality** | every ŝ decile edge, every ŝ continuous rank and every M-3 magnitude decile is computed **per symbol** on an **expanding** window using only bars strictly before the decision close, after the declared warm-up; a pooled or full-TRAIN decile edge anywhere is a **hard failure** (§4.1b) |
| **Exit-matched nulls** | each derangement seed is re-resolved on M1 **under the live arm's own exit rule**; the sign-negation shortcut is asserted present **only** on time-exit arms (L-24.2/F04, §6) |
| **Parent-gate parity** | the regenerated R-MARKOV k=4/k=12 probabilities reproduce SPDR-015's emitted `delta_brier_vs_pers` per symbol to `|Δ| ≤ 1e-9`, written to `results/parent_gate_parity.json`. A parity failure means the gate is not the parent's gate — **hard failure** (§4.1a) |
| **Universe file equality** | `SPDR-014/results/universe_recomputed.json` (the predeclaration's pin) and `cf-voldir-001-universe.json` (§10's run-time pin) are asserted to hold the **same 25 symbols** |
| **L1 fixed-entry subset** | every L1 episode key `(symbol, signal_ts, side, δ)` is asserted present in the L0 population at the same `δ`, with identical stop price, fill ts/price and signal bar. An L1 episode absent from L0 means ŝ moved the entry itself, which is a **hard failure**. **Authority: reflection §5.9's single-fixed-entry rule**, which binds over §5.5's suggestion that `deltaThreshold` be *calibrated* on ŝ deciles — that reading would re-parameterise the entry, and the departure is booked in AMENDMENT-18 rather than smuggled |
| **L4 comparator identity** | for **every** L4 device pair, the unmodulated and modulated arms are asserted to share **estimator (Parkinson-EWMA ŝ), unit (bps), clock (H1 forecast), horizon scaling (`√h`, `h` in hours) and multiplier**, differing **only** in constant-per-symbol-TRAIN-median ŝ vs conditional ŝ(t,h). An ATR-derived exit boundary anywhere in an L4 arm is a **hard failure** — Wilder ATR(20) may appear only as the `deltaThreshold` normaliser (§7) |
| **Predeclaration present** | `results/expected_resolution.json` exists, is dated, carries the SHA-256 of every input, expands **all 5,148** declared strata (§8.1 schema) with **no** placeholder status and **no** `COMPUTED AT RUN` string, and its `input_sha256.basis` equals the sha256 of the committed `results/resolution_basis.json`. Regenerating it after implementation begins is a design change requiring fresh QA |
| **Basis population** | `results/resolution_basis.json` declares exactly one population (`input_filter: arm == 'C'`) and its row accounting reconciles: `filter_matched − retained == excluded == Σ excluded_by_reason` |
| **Parent-gate provenance** | each layer's gate reads exactly the model/field/rule pinned in §4.1a (`s_hmm_rv`; `logistic_ridge`; `logit_ridge`; `ridge_cont` vs the causal five-swing median), labels are held forward from H1 with **no backfill**, and the outcome label `y` and realised swing magnitude appear in **no** gate input — a **hard failure** if they do |
| **MOD-hold eligibility** | the modulated-hold arm uses §4.2's exact `E_run`/`h_mod` equation; events with fewer than 30 prior same-origin R-MARKOV transitions are **excluded from that row only**, with count and reason emitted. A MOD row whose holds are identical to its UNMOD twin on every episode is a **hard failure** (the pair would measure nothing) |
| **L-51 selection check** | the three-number check (payoff-scale ratio, sign-share differential, mean-vs-median gap in the excluded set) runs on **every selected subset the design or analysis reports separately** — L1's `d≥5/d≥7/d≥9` cuts, L2's state cells, L3's gate, L5's combination, and cells above vs below median `mde50` — each against its own complement, and is emitted to `results/selection_check.json`. Binding per `chapter-06-governance.md` §1b |
| **M-4 effective coverage** | any pooled bar or episode count used in a resolution statement is the **measured** `unit_pin.json` / emitted value, never a date-range product; effective-vs-nominal multi-symbol coverage emitted |
| **Predeclared vs realised resolution** | each stratum's **predeclared** expected `n` and expected `mde50` (§8.1) ship on the **same row** as its **realised** `n` and `mde50` in `resolution_ladder.parquet`. Nothing is admitted, excluded, labelled or ranked by the comparison (B-5 enforcement clause 4, QA run 3) |
| **`log R` never unaccompanied** | HARD schema check: no `log R` ships in **any** artifact without `ci_low`, `ci_high`, `ci_width` and `block_mde` on the **same row** — asserted over `metrics_by_cell`, `layer_deltas` and the resolution ladder alike (B-5 enforcement, QA run 2) |
| **Ladder plant operator** | both plant operators (via `W/L` at fixed `p`; via `p` at fixed `W/L`) computed and emitted per rung; neither omitted |
| **No adequacy flag** | asserted that **no** `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` column is emitted anywhere, and that no single canonical MDE threshold appears in code (operator mandate 2026-07-28) |
| **Ladder emitted** | the sensitivity ladder is present on **every** cell, with its detection rates and required-`n` values |
| **Span disclosure** | exact-span subset and span distribution per horizon cell (M-2) |
| Episode exclusivity | at most one open episode per symbol; suppression count emitted |
| Fill rate | emitted per cell; unfilled and suppressed signals counted, never dropped |
| Derangements | fixed-point count == 0, measured and reported (L-28) |
| Determinism | runs **unconditionally** whenever `--jobs > 1`, independent of `--resume`; parallel bit-identical to sequential (P-23) |
| Golden traces | G1–G7 pass |
| No local accounting | screen metrics are availability/residual bps, not booked P&L; no `xen.adjudication` mimicry |
| Code hash | sha256 of `screen_code/` pinned into `results/integrity_selfcheck.json` |

```
HARD (block execution / invalidate emission):
  check-count reconciliation, TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, causality,
  fill causality, universe pin, identity reconstruction, log R definition, cost isolation,
  derangement fixed-point count, golden traces, determinism, BLOCK RULE (all six clauses),
  L4 COMPARATOR IDENTITY, PARENT-GATE PROVENANCE, PARENT-GATE PARITY, DECILE CAUSALITY,
  EXIT-MATCHED NULLS, L1 FIXED-ENTRY SUBSET, MOD-HOLD ELIGIBILITY, PREDECLARATION PRESENT,
  BASIS POPULATION, UNIVERSE FILE EQUALITY, L-51 SELECTION CHECK,
  `log R` never unaccompanied, PREDECLARED vs REALISED resolution.
  EXPECTED HARD-CHECK COUNT: 28, reconciled BY NAME by the check-count assertion (P-23 / L-52).
  (The last four are HARD on PRESENCE and FORM - they assert that the check ran and that the
  columns exist. None of them adjudicates a value; no cell is admitted or excluded by any of
  them. L-51 is HARD because governance SS1b makes it mandatory, and a selection check that is
  silently skipped is indistinguishable from one that passed.)
INFORMATIVE (operator judges, no auto-verdict):
  every effect size, control percentile, collapse fraction, band label, dose-response shape,
  fill rate, kappa, cost overlay, heterogeneity statistic.
```

Every check depends on an **emitted artifact** — missing or empty is a **failure**, never a vacuous
pass (P-23). No required check lives in a manual post-step (L-52).

---

## §13 What this design refuses

- **Any cost term in any estimand, threshold or comparison** (AMENDMENT-C5). Cost is disclosure.
- **Any expectancy, tradability, deployability or cost-complete claim** (AMENDMENT-C2, unchanged).
- **The fitted-slope residual as a target** — it is centred at zero by construction (audit A1).
- **Scoring any capture variant against zero P&L** rather than against the mirror.
- **Any rule, band or gate phrased against `p > 0.5`** — the reference is `p_be` (SoT §2.2).
- **Researching direction prediction**: no new entry model, no trend filter, no tuning of any entry
  parameter to improve `p`. **`deltaThreshold` is frozen at `{0.25, 0.5, 1.0}`, all three reported
  side by side and none selected (§2)** — there is no calibration step of any kind. The realised
  signal rate and fill rate at each level are emitted, so the population behind each δ is visible.
- **Combining layers before characterising them individually** (AMENDMENT-C6).
- **Pruning phase (b) to phase (a)'s winners** — the scope is fixed and includes flat layers.
- **Reading a coarse-resolution cell as a negative** (B-5), or reading a CI that covers the mirror as a refutation.
- **Any aggregate statement over cells** ("N of M covered the mirror") **without the resolution distribution of those cells** — median `mde50` and the count below each rung. An aggregate without it is a negative-by-omission, which B-5 forbids exactly as it forbids a dropped label (QA run 2).
- **Emitting any `powered` / `unpowered` / `NOT_RESOLVABLE` flag, or any single canonical adequacy threshold** — retired by operator mandate 2026-07-28; resolution is reported as a ladder and adequacy is the reader's judgement.
- **A per-symbol `log R` conclusion carried without its resolution ladder** — per-symbol cells resolve coarsely (§8) and are heterogeneity disclosure.
- **Any ATR-derived exit boundary.** Wilder ATR(20) normalises `deltaThreshold` and nothing else (§7).
- **A placeholder predeclaration row** — an L5 slot, a `COMPUTED AT RUN` string, or any named-but-empty stratum (§8.1).
- **A blended score without its term-level decomposition** (SoT §7).
- **A sizing cell reported as improving expectancy** (SoT §4.4).
- Any family status change; any XENA; any TEST or holdout contact.

---

## §14 Amendment ledger

```
AMENDMENT-1: full TRAIN becomes the primary read; DESIGN/CONFIRM scored as verification.
  - DIRECTION: LOOSER (more n per cell; the band split stops halving the primary read)
  - Operator directive 2026-07-28, for POWER. SPDR-018's own power lever 2.
AMENDMENT-2: add M15 as the primary capture clock; H1 becomes co-report. The scale forecast
  s_hat REMAINS on H1.
  - DIRECTION: LOOSER (~4x the bars)
  - Operator directive 2026-07-28, for POWER. V4's no-within-day-skill result constrains the
    FORECAST clock, which is unchanged; the trade clock is a separate object.
AMENDMENT-3: freeze deltaThreshold as a swept axis {0.25, 0.5, 1.0}, all reported, none selected.
  - DIRECTION: TIGHTER (removes an unpinned parameter that swung power ~7x)
  - QA finding, run 1.
AMENDMENT-4: specify exit fill resolution for target / trail / time, with ADVERSE precedence
  inside an M1 bar; correct the SS5 open-to-open wording to apply to the time exit only.
  - DIRECTION: TIGHTER (pessimistic branch taken every time; a specification gap closed)
  - QA finding, run 1.
AMENDMENT-5: correct the SS8 population figure to the artifact value (229,646 pooled H1 bars,
  not the ~541k implied by the TRAIN date range) and the signal rate to a measured quantity.
  - DIRECTION: NEUTRAL (a factual correction; it makes the power statement harsher, not looser)
  - QA finding, run 1.

AMENDMENT-7: replace the pre-declared NUMERIC phase-(b) trigger with operator judgement on the
  full phase-(a) report; only the SCOPE stays pre-declared.
  - DIRECTION: LOOSER
  - Operator directive 2026-07-28. **SUPERSEDED BY AMENDMENT-17 (QA run 5 remediation).** The
    departure from registered AMENDMENT-C6 and reflection SS5.9.1 is withdrawn rather than
    disclosed, the pre-declared condition is restored in SS4.3, and the EXECUTION BLOCKER this row
    carried is DISCHARGED. Nothing in the design now departs from the registered layer protocol.
AMENDMENT-6: retire the powered/unpowered adequacy label and the +-0.03 / 0.07 magnitude
  thresholds; report a SENSITIVITY LADDER per cell and define bands by the CI's relation to the
  mirror instead.
  - DIRECTION: NEUTRAL (nothing is admitted or excluded either way; a boolean is replaced by the
    numbers behind it, and every effect is now bound to its own MDE and CI width on the same row)
  - Operator mandate 2026-07-28. The retired thresholds were anchored on sd(log R)=0.0729 and
    median log R=-0.0301 - the DISPERSION and LOCATION of the observed residual, neither of which
    is a statement about what effect size matters. Powering is left to later verification.

AMENDMENT-8: correct the required-n scaling constant from the powered-subset basis (k=370) to
  the full-population, horizon-split basis (k = 569 / 955 / 1384); add the per-stratum predeclared
  resolution table; unify the L4 comparator units on s_hat (the unmodulated arm now uses the
  TRAIN-median of the SAME estimator, removing the ATR-vs-Parkinson level shift and the
  bar-vs-hour horizon ambiguity); extend TRIPWIRE-2 to exits and add G7.
  - DIRECTION: TIGHTER (the requirement rises ~6.6x at h=12; a comparator seam and a fill-rule
    verification gap are closed)
  - QA runs 1 and 2. The old k was the P-22 selection bias inside a power derivation; the old
    comparator was the EXP-025 unit seam (L-21).
AMENDMENT-9: on M15 the primary read becomes Delta log R vs L0, with absolute log R retained but
  labelled an ENTRY statement.
  - DIRECTION: NEUTRAL (a reporting-object change; nothing is admitted or excluded)
  - QA run 2. SPDR-013 measures M15 direction WORSE than shuffled (derangement 0.20-0.28 vs
    0.48-0.57 on H1), so an absolute band on M15 would report an entry defect as a capture result.
    M15 is retained because the same source measures the MAGNITUDE forecast better on M15 than H1
    on all 25 symbols - which is the quantity this design uses it for.

AMENDMENT-10: state every hold in HOURS on both clocks (`activeHold` / `inactiveHold` grid
  {1, 4, 12, 20} hours; L0 at 1 hour / 2 hours). Against the checkpoint's frozen h in
  {4, 12, 24} bars this grid ADDS 1 hour and DROPS 24 hours; 20 is INSIDE the frozen range, not
  beyond it. The authority for the scale is reflection SS5.5's measured E[run] bound
  (18.9-23.1 H1 bars). (An earlier version of this row said 20 was "beyond" {4,12,24}, which is
  arithmetically false and is corrected here.)
  - DIRECTION: LOOSER (the hold axis adds a shorter horizon than the frozen grid's minimum)
  - QA runs 2 and 3. An earlier draft swept the same numbers as *periods*, which on M15 put the
    entire hold axis at 0.25-5 hours, below the very scale the design cited as its bound.
AMENDMENT-11: state the block-bootstrap block in CALENDAR TIME, matched across clocks
  (block >= max(hold hours, 20 hours)); emit the realised effective sample size per cell.
  - DIRECTION: TIGHTER (a bar-stated block on M15 understates dependence, narrows CIs and
    manufactures `ci_low > 0` on the primary clock - the Phase-010 shape)
  - QA runs 2 and 3. **SUPERSEDED BY AMENDMENT-15**: the diagnosis held, the remedy did not -
    `max(hold hours, 20 hours)` is a single block length and is LOOSER than the parent's rule at
    short horizons. The `max(...)` form is not a live rule anywhere in this design.
AMENDMENT-12: replace SS8's required-n arithmetic with the dimensionless constant
  c = mde_log * sqrt(n), stratified by n band, and report the basis range with an invariance
  statement per P-25; predeclare expected resolution per LAYER CELL, not per clock; bind the
  predeclared and realised resolution to the same emitted row.
  - DIRECTION: NEUTRAL (a correction and a finer predeclaration; nothing is admitted or excluded)
  - QA run 3. The previous form paired a full-population numerator with a powered-subset
    denominator ((1-p)*L = 48.5), overstating the achieved MDE 2.62x and required n ~6.9x - the
    same P-25/L-53 defect AMENDMENT-8 was written to remove, left in the denominator.
AMENDMENT-14: replace SS8's hand-computed resolution tables with generation by
  `xen.resolution_basis`, pinned to results/resolution_basis.json -> results/expected_resolution.json;
  emit realised c per cell; disclose band thinness (cells AND distinct_n); withdraw the picked
  anchors c = 7.5 / 9 and the false "0.03 out of reach at EVERY basis" claim.
  - DIRECTION: NEUTRAL (a correction; nothing is admitted or excluded, and the design now makes no
    invariance claim it has not computed)
  - QA run 4. Three drafts typed three different constants; the numbers are now emitted, not typed.
AMENDMENT-15: adopt SPDR-018's block rule VERBATIM (blocks in days, min 1 day = 24 H1 bars, min/max
  envelope over a block sweep, 5-seed battery) in place of the invented `max(hold hours, 20 hours)`
  single-block rule introduced by AMENDMENT-11.
  - DIRECTION: TIGHTER (restores the INFR-004/L-20 sweep and seed battery; the withdrawn rule was
    LOOSER than the parent's at short horizons and was mislabelled a tightening)
  - QA run 4. AMENDMENT-11 is superseded; its M15-vs-bars diagnosis was right, its remedy was not.
AMENDMENT-16: derive both tripwires' expected separation on TRAIN with a CI (L-24.3) instead of
  "must materially change" / "must differ"; unify the SS4.1 L4 comparator wording onto s_hat.
  - DIRECTION: TIGHTER (a HARD check with no pass rule was unauditable; the SS4.1 row still said
    "a fixed ATR multiple" against SS4.2's s_hat, leaving the EXP-025 unit seam half-closed)
  - QA run 4.
AMENDMENT-13: correct the phase-(a) cell count (L4 is 20 cells, not ~44; 37 per (clock, delta);
  <= 240 across the declared sweep); re-anchor the L-51 selection check to every SELECTED subset
  and make it HARD; add the M-4 effective-coverage and calendar-block assertions to SS12; make the
  pooled-primary read revert to the lane default if homogeneity does not support it; record the
  reflection SS5.9 L4 narrowing (modulation by s_hat only, not by each volatility layer).
  - DIRECTION: TIGHTER (four checks added or promoted; a lane default restored as the fallback)
  - QA runs 2 and 3.

AMENDMENT-17: QA run-5 remediation, in one row because the items are one repair of the same
  document: (a) RESTORE the pre-declared phase-(b) trigger of registered AMENDMENT-C6 /
  reflection SS5.9.1, superseding AMENDMENT-7 and discharging its execution blocker; (b) replace
  both tripwires' "must materially change" / "must differ" with the STRUCTURAL inequalities and
  named emitted fields of SS6.1; (c) quote SPDR-018 SS6.2's block rule word for word in SS8.1 and
  SS12 - {1,3,7}-day sweep, per-calendar-day sufficient statistics, block_bootstrap_ci, effective
  block < n - and require per-seed and per-block emissions; (d) recompute the basis on ARM C ONLY
  with row accounting and per-horizon summaries, and WITHDRAW the "c is FLAT across horizons"
  claim, which the target band refutes (11.855 / 8.363 / 11.744); (e) GENERATE AND COMMIT
  results/expected_resolution.json - all 5,148 declared strata, explicit unknowns, hash-pinned -
  removing every `COMPUTED AT RUN` placeholder; (f) bind ATR20 to `deltaThreshold` only and assert
  L4 comparator identity; (g) name the 33 variant identities, the parent model/field/firing rules
  and the exact modulated-hold equation; (h) state that inference uses REALISED resolution only
  and demote predeclared-vs-realised to a calibration audit; (i) report phase-(b) resolution at
  ALL SIX ladder rungs, not only 0.10; (j) add collapse-fraction, span and per-symbol-expansion
  disclosures and the resolution artifacts to SS15.
  - DIRECTION: TIGHTER (one loosening withdrawn; six checks added or made executable; a
    population and a horizon claim corrected against the artifact; nothing is admitted or excluded)
  - QA run 5. It also pins L1 as a SELECTION on the frozen entry (a strict subset of L0's
    episodes) rather than an s_hat-conditioned `deltaThreshold`, which would have changed which
    signals exist and broken reflection SS5.9's single-fixed-entry requirement - the same defect
    QA found in SPDR-020's L1.

AMENDMENT-18: QA run-6 remediation, booked as one row because it is one repair pass:
  (a) name every layer gate's SOURCE ARTIFACT AND COLUMN, and regenerate the R-MARKOV k=4/k=12
  probabilities via SPDR-015's own frozen `walk_forward_probs` - the parent persisted skill
  summaries only - with a HARD parity check and a named PARITY-EXEMPT list for the 8 symbols whose
  parent metric is null; (b) pin every decile as PER-SYMBOL, EXPANDING and CAUSAL (SS4.1b);
  (c) require every derangement seed to be RE-RESOLVED under the live arm's own exit rule, with
  sign-negation allowed only on time-exit arms (L-24.2/F04); (d) withdraw the residual n forecast
  ("50k-60k") and the c = 5.4 anchor, neither of which exists in the arm-C artifact; (e) check the
  block rule CLAUSE BY CLAUSE against SS8.1's canonical six-clause list and trim the pinned
  `source_ci_rule` to SPDR-018 SS6.2's own text; (f) exclude price-identical bars from TRIPWIRE-2's
  equality; (g) restate G6 structurally; (h) pin the sizing normalisation; (i) state the
  DESIGN/CONFIRM join key; (j) assert universe-file set equality.
  - DIRECTION: TIGHTER (four checks added, two forecasts withdrawn, no cell admitted or excluded)
  - QA run 6.
  - THREE DEPARTURES FROM THE BINDING REFLECTION, BOOKED HERE RATHER THAN LEFT IMPLICIT. All three
    are narrowings and all three follow SS5.9, which binds over the looser readings elsewhere in
    the same document:
      1. SS5.5 offers the ŝ-decile as the CALIBRATION AXIS for `deltaThreshold`. Taken literally
         that re-parameterises the entry and creates signals the frozen entry never produced, so
         L1 is implemented as a SELECTION on the fixed entry instead (SS4.1, SS4.1b).
      2. SS5.9's L1 row says ŝ is used "only to set parameter magnitudes". This design's L1 sets
         no magnitude at all - the magnitudes are L4's - so L1 is a pure selection layer and the
         ŝ-scaled magnitudes are tested in L4's modulated arms, where their comparator lives.
      3. SS5.9 says the L4 UNMODULATED arm is "a fixed multiple of ATR". This design uses the
         per-symbol TRAIN-median of the SAME Parkinson-EWMA ŝ instead, because an ATR arm against
         a Parkinson arm is a ~1.5-1.7x estimator seam (L-21 / EXP-025) that would swamp the
         information effect the pair exists to measure.
    Each keeps the reflection's INTENT - one fixed entry, layers characterised alone, a comparator
    that isolates the information - and none widens scope.

running count (all rows as labelled, including superseded): 4 looser / 9 tighter / 5 neutral
ACTIVE rows after supersessions (AMENDMENT-7 by -17, AMENDMENT-11 by -15): 3 looser / 8 tighter /
5 neutral.
L-23 STREAK NOTE (clause 3 applies to the conservative direction too): AMENDMENTS 12-18 are seven
consecutive TIGHTER rows. Flagged for the operator at the execution gate: a design that only ever
tightens after review is one whose first draft was systematically under-specified, which is what
this ledger records.
NOTE per L-23: LOOSER now stands at 3 (AMENDMENT-1 full TRAIN, -2 M15, -10 hold grid) and is
FLAGGED for the operator at the execution gate, as L-23 requires.
EXPECTED FALSE-QUALIFIER COUNT UNDER THE FINAL SET (L-23, mandatory): **N/A - ZERO machine
qualifiers.** Under AMENDMENT-C7 this design emits no `powered` / `unpowered` / `at_target` /
`NOT_RESOLVABLE` field and applies no canonical adequacy threshold, so there is no qualification
rule for a global null to trip and the expected count of falsely qualified cells is exactly zero
by construction. What IS disclosed instead, because a reader will still count CI-based bands: at
the 95% CI used here, the nominal rate of cells reading `ci_low > 0` under a true global null is
2.5%, i.e. **4.95 of the 198 fixed cells** and **128.7 of the 5,148 per-symbol disclosure rows**
(`0.025 × rows`, emitted per reporting tier in the basis artifact's terms). That is DISCLOSURE:
no cell is qualified, dropped or ranked by it.
Assessment, item by item:
  - AMENDMENT-1 (full TRAIN): defensible. SPDR-018's own power lever 2; acts purely on population
    size; both bands still scored as verification.
  - AMENDMENT-2 (M15 primary): defensible ONLY WITH AMENDMENT-15 (which superseded AMENDMENT-11).
    Under a bar-stated block M15 bought apparent precision the calendar dependence does not
    support; under SPDR-018's calendar day-block rule the lever acts on population size alone, as
    claimed.
  - AMENDMENT-7 (phase-(b) trigger): WITHDRAWN by AMENDMENT-17. It was never defensible on this
    document's own authority - a design cannot amend a registered family amendment by disclosing
    that it disagrees with it - so the pre-declared condition is restored instead. It no longer
    counts as a live loosening and its execution blocker is discharged.
  - AMENDMENT-10 (hold horizon): defensible. Reflection SS5.5's measured E[run] bound authorises
    the scale; the alternative was a hold axis that did not reach the scale it claimed.
No loosening touches an integrity check, fence, causality rule or claim boundary - verified against
SS10, SS12 and SS13. The eight active tightenings close real specification gaps.
```

Checkpoint/family amendments in force: **U1** (top-25 universe, NEUTRAL), **S1** (per-symbol
sufficiency, NEUTRAL), **C1** (cTrader replication-only, NEUTRAL), **C2** (claim refusals, TIGHTER),
**C5** (gross-only measurement, **NARROWING** — transcribed from the family ledger's own label at
`cf-voldir-001.md`; TIGHTER in L-23's three-way vocabulary), **C6** (layer protocol, TIGHTER — **no
departure remains**: AMENDMENT-17 restored the pre-declared phase-(b) trigger C6 requires), **C7** (retire the canonical power threshold, NEUTRAL — the
authority for §8, §9 and AMENDMENT-6; omitted from this list in an earlier draft).

---

## §15 Artifacts

| Path | Content |
|---|---|
| `python/src/xen/resolution_basis.py` | shared, tested basis + deterministic expected-resolution generator (also used by SPDR-020) |
| `screen_code/` | entry module, layer module, 4 device modules, metrics layer, control module |
| `results/resolution_basis.json` | arm-C `c` bands: `cells`, `distinct_n`, `horizon_summaries`, `input_filter`, `row_counts` incl. exclusions by reason, the complete `source_ci_rule`, generator + source SHA-256 |
| `results/expected_resolution_prior.json` | the declared axes (2 clocks × 3 δ × 33 `variant_id` × 26 scopes), the L5-addendum rule, and the parent priors that exist (none) |
| `results/expected_resolution.json` | the committed, dated predeclaration: all 5,148 strata, every one explicitly `UNKNOWN_NO_PARENT_MEASURED_POPULATION` with null `expected_n` / `expected_mde50`, input SHA-256 pins. No placeholders |
| `results/episodes.parquet` | every episode: signal ts, decision state, stop price, fill ts/price, exit ts/price/reason, `r` bps, layer tags |
| `results/signals.parquet` | every signal incl. **unfilled** and **suppressed**, with reason |
| `results/metrics_by_cell.parquet` | per cell: `variant_id`, `clock`, `delta`, `scope`, `p`,`W`,`L`,`W_L`,`p_be`,**`log R`**, block + iid MDE in log units, CIs, CI width, ladder detection rates, band label (CI-relative), evidence class, fill rate, `p_flat`, κ, `n`, homogeneity, **`span_exact_frac`** and **`span_p50` / `span_p90`** (the M-2 exact-span subset and span distribution per horizon cell), **`collapse_fraction`** per control, cost overlay flagged `DISCLOSURE_ONLY` |
| `results/layer_deltas.parquet` | Δ`log R` per stage vs L0, with the L2 interaction term |
| `results/controls.json` | all four controls: percentiles, **null means and quantiles**, **plant curves** (P-24), derangement fixed-point counts |
| `results/selection_check.json` | the L-51 three-number check. **Anchor redefined post-C7**: with no powered/unpowered split there is no precision-selected subset, so the check is run on **every subset the design or analysis reports separately** (each selection layer's kept-vs-excluded episodes, and cells above vs below median `mde50`) — payoff-scale ratio, sign-share differential, mean-vs-median gap in the excluded set (P-22) |
| `results/unit_pin.json` | measured ATR20 and σ̂ medians (computed, not asserted) |
| `results/resolution_ladder.parquet` | per cell: realised `n`, **realised effective sample size**, block MDE, CI width, detection rate at each rung **per plant operator**, `mde50`/`mde80`/`mde95`, the `n` required at each rung, and — on the **same row** — the stratum's **predeclared expected `n` and expected `mde50`** from §8.1. **No adequacy flag** |
| `results/golden_traces.json` | G1–G7 |
| `results/integrity_selfcheck.json` | check-count reconciliation, fences, causality, pin, identity, `log R` definition, cost isolation, code sha256 |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
