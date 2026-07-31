# Checkpoint 018 — Step 3 Adaptive-Management Characterisation

- **Status:** `DESIGN APPROVED 2026-07-30 — IMPLEMENTATION AND EXECUTION NOT YET AUTHORISED`
- **Evidence basis:** `reflection-mid.md`, approved by the operator 2026-07-30
- **Vehicles:** `SPDR-021`, `SPDR-022`, `SPDR-023`
- **Engine:** NautilusTrader, because stops, targets, trails, pending orders and competing exits
  require one native event order
- **Lane:** SPDR characterisation; TRAIN only; 0 counted TEST reads; no holdout contact

## 1. Purpose and interpretation

This is an exploratory map of how already-confirmed volatility information changes both a
strategy's **native geometry** and its external trade management. It is not a three-leg hypothesis
test and it does not issue `SUPPORTED`, `REFUTED`, winner or loser labels.

The three experiments are independent:

| ID | Fixed entry | Variants |
|---|---|---|
| `SPDR-021` | simple candlestick breakout benchmark | fixed plus direct/reverse threshold and expiry |
| `SPDR-022` | continuation after a volatility-band breach (MOMO) | `E-TOUCH/E-CLOSE`; fixed plus direct/reverse `z/H` |
| `SPDR-023` | reversion after a volatility-band breach (MR) | `E-TOUCH/E-CLOSE`; fixed plus direct/reverse `z/H` |

None gates another. All three run regardless of earlier observations. A family-level interpretation
is made only after all three analyses are complete.

Selective strong patterns remain visible and may motivate later work. Robustness, deployability and
locked-rule testing belong to later XENA experiments, not to these screens. Event count, uncertainty
and MDE are reported as context; power labels do not decide which rows are shown or how they are
described.

## 2. Common scope

| Item | Freeze |
|---|---|
| Primary universe | pinned top-25 Bybit USDT linear perps from `cf-voldir-001-universe.json` |
| Replication universe | EURUSD, XAUUSD, USTEC from the INFR-021 cTrader catalog |
| Data roles | crypto is the primary characterisation; cTrader is separate replication, never pooled |
| Clock | H1 decision and management bars; native 1-minute bars resolve orders and competing exits |
| Fence | each universe's TRAIN fence only; cTrader 2024-12-13+ and all global holdouts are forbidden |
| Decision lag | entries and management settings use information confirmed by `t-1` |
| Costs | gross and partial-cost views separate; spread is unavailable and never charged |
| Position overlap | one active order/zone/position per instrument × entry variant × arm; blocked common origins remain recorded |

The cTrader rows use universe-native scale values. No absolute-bps threshold is copied from crypto.

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

## 3. Baselines and direct comparisons

Each experiment first emits its fixed, non-adaptive management baseline:

- unit size;
- no target, protective stop or trailing stop;
- the experiment's fixed time exit;
- for `SPDR-021`, the fixed two-bar pending-order expiry.

Each management device also has a fixed-device comparator. For example, an adaptive target is
compared with a target using the same multiplier of the TRAIN-median scale on the same eligible
episodes. This separates “having a target” from “adapting that target.”

Strategy-native parameters can change which orders or events exist, so they use a **common-origin**
comparison instead of pretending that different trade populations are paired. Every eligible
signal origin or zone origin appears in the fixed, direct and reverse rows. No-order/no-event and
unfilled outcomes remain explicit. Origins that an arm cannot act on because its own order, zone or
position is still active are recorded as `BLOCKED_ACTIVE`, never dropped. Shared trades are
additionally paired by origin.

Every result row therefore names:

`experiment × entry variant × universe × instrument × arm class × volatility component ×
parameter/device × orientation/setting × state`.

It reports both:

1. adaptive minus its fixed comparator on paired episodes or common origins; and
2. adaptive minus the experiment's plain fixed-management baseline.

No pooled number replaces these rows.

## 4. Volatility components

Only objects licensed by the approved evidence inventory are used.

| Component | Frozen object | Management use | Native-parameter use |
|---|---|---|---|
| `RANGE_SCALE` | causal H1 EWMA Parkinson range, converted per universe to forecast next open-to-open absolute move | target, stop, trail distance; inverse-volatility sizing | breakout threshold/expiry; breach `z/H` |
| `SWING_SCALE` | SPDR-013 causal ZigZag 2.0×ATR(14) next-swing magnitude forecast | target and stop distance | breakout threshold/expiry; breach `z/H` |
| `LEVEL_NOW` | slow rolling-median volatility level, `LOW/HIGH` | full reporting section; target, stop, trail, hold and size schedules | breakout threshold/expiry; breach `z/H` |
| `LEVEL_FORECAST` | R-MARKOV probability of the H1 level state at `k=4` and `k=12`; `HIGH` when the causal probability is at least 0.50 | the same devices, with each horizon reported separately | breakout threshold/expiry; breach `z/H` |
| `SHOCK` | top-decile absolute H1 return, active for two bars | short response window; distance, hold and size schedules | breakout threshold/expiry; breach `z/H` |
| `SWING_GT_CUR` | frozen SPDR-018 `logit_ridge` `T-GT-CUR` classifier | opportunity section; target distance and holding period | breakout threshold/expiry; breach `z/H` |
| `TAIL_RISK` | expanding causal probability of exceeding the instrument's own next-move P90; high above the unconditional 0.10 rate | target/stop reach context and size restraint | breakout threshold/expiry; breach `z/H` |

`TAIL_RISK` is executable as a prior-only expanding empirical probability conditioned on the
current `LEVEL_NOW` state. The P90 threshold is frozen on the calibration band. At decision `t`,
only next-move outcomes completed before `t` enter the matching-state numerator and denominator;
before that state has a completed observation, the probability is `0.10`. `HIGH` means the
probability is strictly above `0.10`. No fitted outcome model or same-bar outcome is permitted.

`LEVEL_NOW` is always a reporting section, including `LOW` and `HIGH`; it is never used to hide
the less favourable state. Filtered reads report the selected and non-selected populations.
`LEVEL_FORECAST k=1`, calendar/session effects, D1 close-to-close volatility, HAR, `R-HMM-RV`,
new direction models and the unpowerable ordered-last-k event are excluded.

## 5. Strategy-native parameter arms

These arms are equal in standing to the external management arms. Every parameter is tested in
both directions; “direct” and “reverse” are identifiers, not favourable labels.

For continuous `RANGE_SCALE` and `SWING_SCALE`, define
`q = clip(event_scale / calibration_median_scale, 0.5, 2.0)`. For the other components, `HIGH`
means the frozen high/active/true state in §4 and `LOW` means its complement.
Where the continuous components drive the categorical expiry or `H` schedule, `q >= 1.0` is
`HIGH` and `q < 1.0` is `LOW`. The equality rule is frozen and applies in both orientations.

### SPDR-021

| Parameter | Fixed | Direct arm | Reverse arm |
|---|---:|---|---|
| Breakout delta threshold | `0.50 ATR(20)` | higher continuous scale or categorical `HIGH/active` makes entry easier: `clip(0.50/q, 0.25, 1.00)` or `HIGH=0.375`, `LOW=0.750` | the same state makes entry stricter: `clip(0.50×q, 0.25, 1.00)` or `HIGH=0.750`, `LOW=0.375` |
| Pending-order expiry | 2 H1 bars | `LONG_ON_HIGH`: `HIGH=4`, `LOW=1` | `SHORT_ON_HIGH`: `HIGH=1`, `LOW=4` |

### SPDR-022 and SPDR-023

| Parameter | Fixed | Direct arm | Reverse arm |
|---|---:|---|---|
| Band multiplier `z` | `1.50` | higher continuous scale or categorical `HIGH/active` gives an earlier/narrower event: `clip(1.50/q, 1.00, 2.00)` or `HIGH=1.00`, `LOW=2.00` | the same state demands a wider/more selective event: `clip(1.50×q, 1.00, 2.00)` or `HIGH=2.00`, `LOW=1.00` |
| Band lifetime `H` | 12 H1 bars | `LONG_ON_HIGH`: `HIGH=24`, `LOW=4` | `SHORT_ON_HIGH`: `HIGH=4`, `LOW=24` |

All seven components receive every applicable native arm. The bounded native combinations are:

- `SPDR-021`: threshold + pending expiry;
- `SPDR-022/023`: `z + H`.

For each component, the combination includes all four predeclared orientation pairs
(`direct/direct`, `direct/reverse`, `reverse/direct`, `reverse/reverse`). This is the entire native
combination grid. Native parameters are **not crossed with external targets, stops, trails, holds or
sizing** in these experiments.

`LEVEL_FORECAST k=4` and `k=12` are separate executable component IDs, giving eight executable IDs
from seven component families. Before universe/instrument/state expansion, the native grid contains
64 adaptive configurations in SPDR-021 and 64 per breach variant (128 each) in SPDR-022 and
SPDR-023, plus their fixed comparator rows. This breadth is disclosed, never winner-pruned.

Reports name the actual behaviour (`easier/stricter`, `longer/shorter`, `narrower/wider`) rather
than labelling one arm intuitive and the other counter-intuitive. Both receive equal standing:
high volatility can reasonably mean either more opportunity or more noise/risk, and the experiment
is intended to show which interpretation fits which strategy and state.

Native-arm outcomes are origin count, signal/event rate, fill rate, time to signal/event/fill,
selected and excluded path distributions, per-trade outcomes, and exposure-correct per-origin
outcomes with no-trade origins retained. Directional accuracy remains measured, never optimised.

The common origin clock is fixed before any native parameter is applied: every warm H1 decision bar
is a zone origin for breach strategies, and every warm H1 bar satisfying the parameter-free
candlestick-shape predicate is a breakout origin. Each arm separately records whether that origin
created an event/order, expired, filled, or was blocked by its own active state.

## 6. Device arms

The distance ladder is `m ∈ {0.75, 1.00, 1.50}`. For a scale component:

`adaptive distance = m × causal event scale`.

Its fixed-device comparator is:

`fixed distance = m × TRAIN-median causal scale within the same universe and eligible population`.

The multiplier ladder is fully reported; no multiplier is declared the winner.

| Device | Adaptive rule | Device-native measures |
|---|---|---|
| Target | profit limit at the frozen distance | reach rate, realised capture, missed favourable excess, time to target |
| Protective stop | stop at the frozen adverse distance | adverse excursion, stop rate, loss severity, recovery after stop as a diagnostic |
| Trailing stop | native trailing stop with the frozen distance, activated after `1.0 ×` that distance in favourable excursion | peak giveback, favourable excursion captured, loss-tail change |
| Holding period | fixed caps `{2,4,12}` bars; state arms use 2 bars for `SHOCK`, and 4/12 for low/high expected opportunity | outcome by time, decay, holding efficiency, opportunity duration |
| Position size | fixed one-risk-unit comparator; `clip(median_scale/event_scale, 0.5, 2.0)` for scale normalisation; high `TAIL_RISK` or active `SHOCK` halves that result | dispersion of risk, drawdown, tail loss and concentration; never mean expectancy |

State-conditioned distance arms use `0.75 ×` the fixed distance in the lower state and `1.50 ×` in
the higher state. Both states and the unconditioned fixed distance are emitted. Forecast-state arms
use the frozen out-of-sample class probability; no threshold is tuned after outcomes are seen.
For `LEVEL_NOW` and each `LEVEL_FORECAST` horizon, the size arm is one risk unit in `LOW` and
one-half risk unit in `HIGH`. This is a restraint arm, not an expectancy claim.

Fixed distances and other frozen reference values are estimated on the first chronological 20% of
TRAIN after warm-up, then held constant over the remaining TRAIN characterisation band. Expanding
models may update only from observations already complete at the decision time.

## 7. Individual reads and bounded combinations

Individual component × device rows are produced before combinations:

| Component | Target | Stop | Trail | Hold | Size |
|---|:---:|:---:|:---:|:---:|:---:|
| `RANGE_SCALE` | ✓ | ✓ | ✓ | — | ✓ |
| `SWING_SCALE` | ✓ | ✓ | — | — | — |
| `LEVEL_NOW` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `LEVEL_FORECAST` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `SHOCK` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `SWING_GT_CUR` | ✓ | — | — | ✓ | — |
| `TAIL_RISK` | ✓ | ✓ | — | — | ✓ |

Only these component combinations are added:

- `RANGE_SCALE + LEVEL_NOW`;
- `RANGE_SCALE + LEVEL_FORECAST`, with `k=4` and `k=12` separate;
- `SHOCK + LEVEL_NOW`;
- `RANGE_SCALE + SWING_GT_CUR`.

The combination order is binding: the first component supplies the primary numeric schedule and
the second component supplies its declared state/opportunity adjustment. Combinations do not
silently import a third component.

- `RANGE_SCALE + LEVEL_NOW` and `RANGE_SCALE + LEVEL_FORECAST`: range supplies the event-scale
  distance and inverse-range size base; the level state multiplies distance by `0.75` in `LOW` and
  `1.50` in `HIGH`, uses the declared 4/12-bar low/high hold where a hold is present, and multiplies
  size by `1.0` in `LOW` and `0.5` in `HIGH`.
- `SHOCK + LEVEL_NOW`: level supplies the `0.75/1.50` fixed-distance adjustment. An active shock
  overrides the hold to 2 bars and multiplies size by `0.5`; otherwise the level supplies the
  4/12-bar low/high hold and `1.0/0.5` low/high size multiplier. No additional distance or size
  component is implied.
- `RANGE_SCALE + SWING_GT_CUR`: range supplies target distance; `FALSE` multiplies it by `0.75`
  and uses a 4-bar hold where a hold is present, while `TRUE` multiplies it by `1.50` and uses a
  12-bar hold. No signed or directional term is introduced.

Apply only the rules for devices present in the declared row. A combination row must carry both
component IDs and their roles explicitly; losing either input is an integrity failure.

Only these multi-device combinations are added:

- target + protective stop;
- trailing stop + time cap;
- target + protective stop + time cap.

Multi-device combinations use `RANGE_SCALE` as the distance input and the declared state component
only where named above. Position sizing remains a separate risk-normalisation read over the same
trade paths and is not crossed with the exit combinations. No exhaustive power set is allowed.

## 8. Entry freezes

### SPDR-021 — breakout benchmark

On completed H1 bars:

```text
LONG:  low[1] < min(low[0], low[2])
       and (close[0] - close[1]) / ATR(20)[0] > 0.50
SHORT: high[1] > max(high[0], high[2])
       and -(close[0] - close[1]) / ATR(20)[0] > 0.50
```

Place a stop order at `high[0]` for long or `low[0]` for short on the next actionable bar. The
fixed baseline expires an unfilled order after two H1 bars and exits a filled position after one H1
bar. Only the predeclared native arms in §5 may vary the threshold or expiry; no value is tuned from
outcomes.

### SPDR-022 and SPDR-023 — breach entries

Both inherit the causal SPDR-014 `Z-VOL` band, narrowed to H1, EWMA Parkinson width, `z=1.5` and
`H=12`. `E-TOUCH` is the first high/low touch; `E-CLOSE` is the first close outside the band. Entry
is the next real open. Only the predeclared native arms in §5 may vary `z` or `H`.

`SPDR-022` trades with the breach side. `SPDR-023` trades against it. Their plain baseline exits
after four H1 bars with no other management. `E-TOUCH` and `E-CLOSE` remain separate throughout;
event rate and band selectivity are reported on every row.

## 9. Measures shared only where they genuinely apply

For every trade-bearing row, report trade count, gross and partial-cost mean/median/trimmed outcome,
`p`, `W`, `L`, `W/L`, `p_be_net`, edge, MFE, MAE and exit-reason shares. These are context and
identity checks, not a universal ranking score.

The headline for each device remains its device-native measures in §6. Any “best” table must state
which measure it is best on and must link back to the full row table.

State and selection rows also carry the three-number selection check:

- payoff-scale ratio between selected and excluded episodes;
- sign-share difference;
- mean-minus-median gap in the excluded episodes.

## 10. Uncertainty, controls and integrity

- Management-device estimates use paired episode differences. Native-parameter estimates use the
  full common-origin population, plus paired shared-trade diagnostics.
- Confidence intervals use calendar-block resampling with block length at least the longest active
  management or native-event horizon (at least 24 H1 bars) and cluster instruments within each
  resample.
- Emit event count, effective count, CI and MDE for every row. These are informative diagnostics,
  not verdict labels or pruning rules.
- Magnitude-defined arms (`SHOCK`, scale and tail strata) carry magnitude-matched comparators.
- A time-derangement control breaks component-to-episode alignment with zero fixed points.
- A one-bar future-shift tripwire must visibly change the component mapping; it is a leak check, not
  an economic null.
- Nautilus order/fill records are the accounting source. Competing exits use the engine's event
  ordering; no local OHLC “which hit first” reconstruction may adjudicate P&L.
- Re-running with identical inputs must reproduce orders, fills, trade rows and summary rows.
- Crypto and cTrader are emitted and analysed separately.

```text
CONTROL FIXED_DEVICE:
  question answered: what changed because the volatility input adapted this device?
  population: the identical eligible entry episodes under the same device with its value frozen
  bite/MDE: paired block MDE emitted for every row
  non-vacuity: changes the device parameter while preserving entry, side and eligible episode
  expected outcome: direct adaptive-minus-fixed device measure
  disclosure: both device-vs-device and adaptive-vs-plain-baseline estimates

CONTROL FIXED_NATIVE_PARAMETER:
  question answered: what changed because volatility adapted an intrinsic strategy parameter?
  population: every identical eligible signal/zone origin under the fixed parameter
  bite/MDE: common-origin block MDE emitted for event/fill/exposure and outcome measures
  non-vacuity: changes threshold/expiry/z/H while preserving origin, component and strategy side rule
  expected outcome: direct and reverse arm minus fixed parameter, with no-event/no-fill explicit
  disclosure: common-origin estimate, shared-trade paired diagnostic, selected and excluded paths

CONTROL TIME_DERANGEMENT:
  question answered: does event-time alignment of the volatility component matter?
  population: the same episode set with component timestamps deranged; zero fixed points
  bite/MDE: alignment collapse and paired block MDE emitted
  non-vacuity: changes component-to-path assignment and therefore adaptive device values
  expected outcome: aligned-minus-deranged direct estimate
  disclosure: collapse fraction is descriptive only
  destroy form: DERANGEMENT

CONTROL MAGNITUDE_MATCH:
  question answered: does a shock, tail or scale-defined state add information beyond move size?
  population: non-selected episodes matched within instrument, clock and causal magnitude bin
  bite/MDE: paired/weighted block MDE emitted
  non-vacuity: preserves magnitude distribution while changing the named state
  expected outcome: state-minus-matched-state direct estimate
  disclosure: selected and excluded populations plus the three-number selection check
```

```text
INTERPRETATION:
  no SUPPORTED/WASH/CONTRADICTED verdict bands apply to SPDR-021/022/023
  all rows are described by estimate, uncertainty, event count and MDE
  pooled summaries are disclosure-only
```

## 11. Claim boundary and hand-off

These experiments may say how much a volatility component changed a device, for which strategy,
entry variant, state and universe. They may identify concentrated or apparently strong patterns.
They may not call a component universally effective or ineffective, claim tradability, change the
family status, open XENA, or suppress contrary rows.

After all three analyses, the operator makes the checkpoint-level interpretation. Any robustness
or deployment candidate then receives a new locked XENA design, separate data authority and normal
governance.
