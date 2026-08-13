# Checkpoint 019 — Liquidity Sweeps

- **Opened:** 2026-08-11
- **Status:** `OPEN — EXP-100 HYP-000 UPHELD BY OPERATOR; EXP-101–104 QA IN PROGRESS`
- **Family:** `CF-LIQSWP-001`
- **Source of truth:** `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md`
- **Superpowers design:** `docs/superpowers/specs/2026-08-11-liquidity-sweeps-design.md`

## 1. Governing sources and precedence

1. `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md` — substantive definitions and hypotheses.
2. `docs/references/dataset-reference.md` and `docs/references/architecture.md` — data and engine boundary.
3. `docs/knowledge-base/` — causal, object-identity, TPO/profile, and neutrality lessons.
4. This checkpoint — frozen scope, experiment sequence, estimands, controls, and artifact contract.
5. Individual `python/experiments/EXP-10X/design.md` files — experiment-specific narrowings only.

The source-of-truth value-gap amendment is binding: a tight gap has price span
strictly below 30% of the full VA width/magnitude. In implementation this is
`gap_span < 0.50 * (VAH - VAL)` (AMENDMENT-12). Gap *selection* stays the
emptiest 30% of VA TPO mass.

## 2. Operator amendments

**Revision note:** a previously proposed exclusion of 1W levels was withdrawn during
revision because it was not an operator-approved deviation. Family A therefore retains
the full SoT level catalogue.

**AMENDMENT-2:** use 1H confirmation references for 15m/30m and 1D references
for 1h — **DIRECTION: TIGHTER**.
Running count: **0 looser / 1 tighter / 0 neutral**.

**AMENDMENT-3:** retain 1-minute engine input for granular fill simulation while
reusing the established clock-aligned aggregation convention — **DIRECTION: NEUTRAL**.
Running count: **0 looser / 1 tighter / 1 neutral**.

**AMENDMENT-4:** normalise cross-asset distance and profile measures with causal
same-asset, same-observation-timeframe Wilder ATR(14) — **DIRECTION: NEUTRAL**.
Running count: **0 looser / 1 tighter / 2 neutral**.

**AMENDMENT-5:** add the SoT tight-value-gap condition to `HYP-003` —
**DIRECTION: NEUTRAL**. Running count: **0 looser / 1 tighter / 3 neutral**.

**AMENDMENT-6 (2026-08-12):** close-all-eligible reference settlement —
**DIRECTION: TIGHTER**. On each completed reference event, every eligible
returned unconfirmed raid is settled. The latest eligible expected-side raid
receives `primary_attribution=true` and remains live for the later opposing
endpoint; all earlier eligible expected-side raids close immediately as
`CONFIRMED_NON_PRIMARY`. Every eligible opposing unconfirmed raid fails as
`FAILED_BREAKOUT`. Every primary-attributed confirmed raid completes on the
opposing endpoint. Older open raids are no longer left live until right-censor.
Running count: **0 looser / 2 tighter / 3 neutral**.

**AMENDMENT-7 (2026-08-12):** restrict the family execution universe to cTrader
assets only (`EURUSD`, `XAUUSD`, `USTEC`); exclude the Bybit/crypto catalogue —
**DIRECTION: TIGHTER**. Running count: **0 looser / 3 tighter / 3 neutral**.

**AMENDMENT-8 (2026-08-12):** lock the original SoT raid grain — **DIRECTION:
NEUTRAL**. The SoT tracks excursions and completed raids **bar by bar** on the
cell observation timeframe (15m / 30m / 1h). Confirmation and later endpoint
stay on the confirmation reference (1H for 15m/30m; 1H and 4H for 1h). Downstream
checkpoint/family text and the first apparatus over-specified 1-minute bars as
the raid object; that was an implementation choice, not the SoT. AMENDMENT-8
retires that over-specification. 1-minute input remains for TPO bins,
max-excursion reset, post-confirmation swing extremes, and any later fill
model (AMENDMENT-3). Intra-observation 1m wicks that do not survive the
completed observation OHLC are not raid objects. Running count: **0 looser /
3 tighter / 4 neutral**.

**AMENDMENT-9 (2026-08-13):** retire 1h→1D confirmation. 15m/30m stay on 1H.
1h cells keep **both** 1H (same-TF settle) and 4H (the 15m→1H analog). Matrix
becomes **288 cells** (144 fifteen/thirty-minute + 144 one-hour; later cut to
264 by AMENDMENT-11). Run order is all 15m, then all 30m, then all 1h. The 13
finished EURUSD 1h→1D emissions are the old object and are deleted. **DIRECTION: LOOSER** versus AMENDMENT-2's 1D
confirm clock (more frequent settle events); 4H arm is the tighter of the two
1h arms. Running count: **1 looser / 3 tighter / 4 neutral**.

**AMENDMENT-10 (2026-08-13):** previous 1D/1W levels are completed **trading**
sessions, not contiguous 1,440 / 10,080-minute bars — **DIRECTION: NEUTRAL**
(restores the SoT named-session object; does not change 15m/1H/4H bar grain).
A trading day is `America/New_York` 17:00 → next 17:00, Monday–Friday, with
historical DST. Sunday after 17:00 NY belongs to Monday. Friday after 17:00 NY
is weekend. Observed minutes only; no synthetic fills. A trading week is that
Mon–Fri book, emitted at Friday 17:00 NY. Last unfinished TRAIN bucket is
right-censored. Rationale: the AMENDMENT-9 contiguous-minute rule produced 0
1D/1W levels on sessioned cTrader minutes; UTC calendar days would mint ~128
Sunday stubs and flip the book at 00:00 UTC (mid-Asia). StreamingOHLC for
15m/30m/1H/4H is unchanged. Running count: **1 looser / 3 tighter / 5 neutral**.

**AMENDMENT-11 (2026-08-13):** replace rolling windows 16/32/64/128/256 with
**7 / 14 / 22 / 252** — **DIRECTION: NEUTRAL** (operator: trading-native counts).
Matrix becomes **264 cells** (11 configs × same confirm grid). Old rolling
emissions are the old object and are deleted. Running count: **1 looser / 3
tighter / 6 neutral**.

**AMENDMENT-12 (2026-08-13):** a gap is tight when `gap_span < 0.50 * VA_width`
— **DIRECTION: NEUTRAL** (operator). Gap *selection* stays the lowest-density
bins reaching at least **30%** of VA TPO count. Running count: **1 looser / 3
tighter / 7 neutral**.

**AMENDMENT-13 (2026-08-13):** a raid starts when a completed observation bar
goes strictly beyond the level. Same-bar return does **not** close it and is
not `AMBIGUOUS_INTRABAR`. The raid stays live until the later confirmation or
fail event, or TRAIN right-censor. Return to the level is still recorded when
it happens; it is not a second-bar requirement for raid identity. A 1-minute
wick that does not survive the observation OHLC is still not a raid
(AMENDMENT-8 grain unchanged). Old two-bar / same-bar-close emissions are the
old object and are deleted. **DIRECTION: LOOSER**. Running count: **2 looser /
3 tighter / 7 neutral**.

## 3. Mechanism

```text
MECHANISM: A liquidity level is a causal, persistent price object. A raid is an
observation-bar excursion strictly beyond that level (AMENDMENT-8 grain;
AMENDMENT-13 lifetime). Same-bar return does not close the raid. After a raid,
the first expected-side higher-timeframe confirmation marks a sweep; an
excursion-side confirmation marks a breakout and failed sweep. The experiment
measures the later opposing swing, its ATR-normalised magnitude and duration,
and whether it exceeds the initial excursion. Level degree, prior raid count,
online TPO value-gap structure, and causal volatility regime are descriptive
conditioning variables. No live prediction or cost-complete trading claim is
made.
DERIVED: estimand=per-stratum event-conditioned outcome distributions and direct
contrasts; null=future-destroyed post-raid alignment plus fixed direct baselines;
horizon=until first opposing confirmation or TRAIN right-censor; test=neutral
per-stratum evidence for and against the predeclared contrasts.
```

## 4. Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the measured object is the same
    causal level/raid/sweep state that the engine emits; no proxy entry event is used.
  measured conditioning event == traded entry event: N/A — this is an event-study
    characterisation, not a deployment strategy; any fill simulation is a separate
    engine artifact and cannot change the state estimand.
  effect-splitting windows non-overlapping: YES — each raid owns its own excursion,
    confirmation, and later-swing intervals; shared level dependence is handled by
    level-clustered uncertainty rather than duplicated independent claims.
```

## 5. Frozen scope

### 5.1 Universes

**cTrader only (AMENDMENT-7):** `EURUSD.CTrader`, `XAUUSD.CTrader`,
`USTEC.CTrader`; each is an independent stratum.

Pin: `docs/signal-registry/candidate-families/cf-liqswp-001-universe.json`.
Fence: INFR-021 (`train_start=2021-06-02T00:01:00Z`,
`train_end=2023-11-22T00:00:00Z`, manifest SHA
`4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0`).

**Bybit/crypto:** excluded from this family until a later operator amendment.
No TEST or holdout data is loaded.

### 5.2 Time and levels

- Observation timeframes: 15m, 30m, 1h. Raid start, return, and beyond are
  decided on these bars (AMENDMENT-8). Same-bar return does not close a raid
  (AMENDMENT-13).
- Engine input: 1m real OHLCV bars. Streaming higher-timeframe state is
  produced online; `xen.bar_aggregator` is the deterministic parity reference.
  1m remains the TPO / max-excursion / swing-extreme / fill-path grain.
- Family A: previous completed 1H, 4H, 1D, and 1W highs and lows.
- Family B: previous completed Asia, Europe, and America session highs and lows.
- Family C: causal rolling 7, 14, 22, and 252-bar highs and lows of the
  current observation timeframe (AMENDMENT-11).
- Family A 1D/1W clocks: completed NY 17:00 trading day / Mon–Fri trading week
  (AMENDMENT-10). 1H/4H remain contiguous completed StreamingOHLC windows.
- Levels are identified by source family, configuration, side, and anchor
  period/session. Coincident prices remain distinct objects.

Sessions use the approved IANA local-time windows: Asia/Tokyo 09:00–18:00,
Europe/London 08:00–17:00, and America/New_York 08:00–17:00, converted to UTC
with historical DST rules.

### 5.3 Causal ATR unit

The primary scale is causal Wilder ATR(14) on the observation timeframe,
calculated from completed bars only and read at the next bar open. All price
distances are emitted as raw price, bps, and ATR units. The value-gap bin width
is frozen at `0.10 × ATR_unit` when the active profile begins. A non-finite or
non-positive ATR produces an explicit `ATR_UNDEFINED` state.

## 6. Online state machine

For every active level and timestamp, the engine emits the level identity,
side, source/configuration, active/expired state, price relation, excursion
magnitude and duration, return state, prior raid count, confirmation state,
breakout/failure state, and later-swing outcome fields where available.

High levels are raided above and expect a downward move. Low levels are raided
below and expect an upward move. A completed observation bar that goes strictly
beyond the level starts a live raid (AMENDMENT-13). Inclusive return is still
recorded on that bar or a later bar; it is not required to *open* the raid and
does not terminate it. Confirmation or fail on the reference clock settles the
raid. A 1-minute wick that does not survive the observation OHLC is not a raid.

If multiple levels/raids are eligible before confirmation, primary attribution
goes to the most recent resolvable raid (AMENDMENT-6). Same-bar ordering is not
fabricated. All eligible earlier returned raids settle on that same reference
event as `CONFIRMED_NON_PRIMARY` (expected-side) or `FAILED_BREAKOUT`
(opposing-side); they do not remain live until right-censor. Excursion maxima
are retained on each raid record through settlement.

## 7. Confirmation and endpoint rules

For 15m/30m observations the confirmation reference is 1H. For 1h it is both
1H and 4H as separate strata (AMENDMENT-9). 1D confirmation is retired. Each
method is a separate estimand:

1. `BREAKOUT_BAR`: a completed reference bar closes beyond the previous
   reference bar’s high/low.
2. `LEVEL_CLOSE`: a completed reference bar closes beyond the selected
   configured higher-degree level. Each level family/configuration is retained
   as its own stratum; any overlap with the previous-bar extreme is disclosed,
   not silently pooled.

The expected-side event confirms eligible returned raids. Only the latest
primary remains live for the later swing; earlier eligible raids close as
`CONFIRMED_NON_PRIMARY` with profiles finalized at that confirmation close.
The excursion-side event fails every eligible returned unconfirmed raid as
`FAILED_BREAKOUT`. The later swing ends at the first opposing reference event
after primary sweep confirmation; every primary-attributed live raid completes
there. No arbitrary timeout is used. Missing endpoints are right-censored at
the relevant TRAIN boundary.

## 8. TPO value-gap algorithm

The profile is built for each completed raid once its expected-side confirmation
event is known, but the state is maintained online throughout the active path.
The profile interval begins at the 1m bar that establishes the current maximum
excursion and ends at the completed close of the same-direction confirmation
event. If a new maximum occurs, the active profile is reset at that bar and
continues forward; historical bars are never retrospectively replayed.

Each closed 1m bar contributes one TPO count to every fixed price bin intersecting
its inclusive low-high range. Bins use width `0.10 × ATR_unit`; the integer bin
grid is stable for the profile. The profile retains TPO counts, interval bounds,
number of contributing 1m brackets, and conservation checks.

The POC is the lowest-price maximum-count bin. The VA expands contiguously from
the POC until cumulative TPO count is at least 70% of total TPO count, annexing
the upper neighbour first on equal counts. Inside the VA, select the lowest-
density bins until their TPO count is at least 30% of VA TPO count. Retain both
the exact selected-bin mask and its conservative outer span.

```text
VA_width       = VAH - VAL
gap_span       = gap_high - gap_low
tight_gap      = gap_span < 0.50 * VA_width
gap_span_atr   = gap_span / ATR_unit
gap_span_va    = gap_span / VA_width
```

`tight_gap` is a deterministic label for analysis, not an automatic quality or
value verdict. If `VA_width <= 0`, no selected bins exist, or the minimum bin
span cannot satisfy the strict 50% tightness comparison, emit an explicit profile reason.
Gap *selection* uses 30% of VA TPO mass; tightness uses 50% of VA width (AMENDMENT-12).

## 9. Hypotheses and experiments

| ID | Experiment | Primary estimand |
|---|---|---|
| `HYP-000` | `EXP-100` | State-machine coverage, causal availability, parity, and reconciliation of level/raid/confirmation objects. |
| `HYP-001` | `EXP-101` | Outcome distributions by level family/configuration and ATR-normalised significance strata. |
| `HYP-002` | `EXP-102` | Outcome distributions by previous completed raid count on the same level. |
| `HYP-003` | `EXP-103` | Defined-profile, tight-gap, and non-tight-gap outcomes; primary contrast is tight versus non-tight among defined profiles, with all-profile baseline retained. |
| `HYP-004` | `EXP-104` | Raid frequency, excursion/swing magnitude, duration, and outcome quality by causal volatility regime. |
| `HYP-005` | deferred | Breakout-only significance; operator-gated and excluded from this initial batch. |

Primary outcome fields are `swing_atr`, `swing_duration`,
`strong_move = swing_atr > max_excursion_atr`, breakout/failure state, and
right-censor status. Continuous values remain primary; binary labels are
secondary descriptions.

## 10. Controls and validity proofs

```text
CONTROL FUTURE_DESTROY:
  question answered: does the observed post-raid outcome relationship require
    the real future path rather than merely the event-count distribution?
  population: same emitted raid objects with post-confirmation outcome blocks
    deranged within asset × observation timeframe × configuration; disjoint in
    alignment from the real outcome series.
  bite: changes the future swing and strong-move statistic while preserving the
    event population and marginal block distribution.
  non-vacuity: perturbs swing_atr, swing_duration, and strong_move labels.
  expected outcome if H true: the event-to-outcome contrast collapses toward the
    same-stratum baseline; if H false: similar contrast remains.
  disclosure: report destroy/raw contrast ratio and fixed-point count.
  destroy form: DERANGEMENT — zero fixed points, per L-28.
```

```text
TRIPWIRE: future-destroyed post-confirmation outcome blocks
  must collapse the aligned event/outcome contrast;
  vacuity check: swing magnitude, duration, and strong-move fields are directly
    changed while event labels and their marginal counts remain fixed;
  if permutation-based: derangement=YES (zero fixed points; L-28);
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

The future-destroy tripwire is the only blocking control. Its integrity bite is
`INTEGRITY_Z × bootstrap_SE`, with `INTEGRITY_Z = 2.8`; it is not a research
effect threshold. Other controls and all value/quality reads are informative.

Uncertainty is clustered by `level_id` within asset, venue, observation
timeframe, confirmation method, and level configuration. Repeated raids on one
level therefore do not masquerade as independent levels.

## 11. Required emissions

At minimum, each raid record must carry:

- source level identity and configuration;
- observation timeframe, venue, instrument, confirmation method/reference;
- level price, side, ATR unit and ATR lag/source timestamp;
- excursion start, maximum excursion price/time, magnitude, duration;
- return timestamp and prior raid count;
- sweep/breakout confirmation state and endpoint/censor state;
- reversal/swing magnitude and duration in raw price, bps, and ATR;
- TPO profile status, profile interval, bin width, TPO bracket count, VAH/VAL,
  VA TPO count, selected gap-bin mask, gap span, gap span in ATR, gap/VA ratio,
  tight-gap label, and explicit undefined reason where applicable;
- causal volatility-regime labels at raid, excursion, confirmation, and endpoint.

The engine also emits the bar-level state needed to verify that no level or raid
was silently discarded.

## 12. Interpretation and sample-size rules

```text
BANDS (operator-only, never machine-assigned):
  HIGHER: direct contrast and interval are read as higher in the observed data.
  OVERLAP: interval overlap or small contrast is reported as overlap, not refutation.
  LOWER: direct contrast and interval are read as lower in the observed data.
POOLED: disclosure-only unless asset and venue homogeneity is demonstrated.

SAMPLE-SIZE:
  expected events per stratum: measured by preflight; no numerical expectation is
    used as a gate.
  minimum_n_for_primary_inference: none; every realised row is retained with its count.
  declared_fixed_comparator: all completed raids in the same named stratum, plus
    the future-destroy control where applicable.
  channels:
    - name: continuous outcome contrasts
      sigma_denominator: outcome_level
    - name: paired event labels
      sigma_denominator: paired_delta
  strata predeclared thin: every cTrader asset × timeframe × level config × confirmation
    method cell; thin rows remain visible and are not called absent.
```

## 13. Golden trace

```text
GOLDEN-TRACE:
  T1: 15m high level L-H1=100.00 is active. A completed 15m bar prints
      high=101.20, low=100.80, close=101.00: excursion_above=true,
      max_excursion=1.20, returned=false. A later completed 15m bar touches
      100.00: completed_raid=true, prior_raid_count=0. A 1m wick through 101.20
      that is not the 15m high does not start a raid (AMENDMENT-8). Same-bar
      return on that 15m bar does not close the raid (AMENDMENT-13).
  T2: before the expected-side reference event, a second active high level is
      raided on a later observation bar. On confirmation the second receives
      primary attribution and stays live for the swing; the first eligible
      returned raid settles as CONFIRMED_NON_PRIMARY with its max excursion
      retained (AMENDMENT-6).
  T3: the 1H reference bar closes below its expected-side reference low. The
      confirmation timestamp is the completed 1H close, not a 15m or 1m stamp.
      The sweep is confirmed; the TPO profile (1m bins) ends at that close, and
      later opposing reference confirmation closes the swing.
```

QA must independently hand-check the trace against the emission. The developer
must not derive the expected trace from implementation output.

## 14. Integrity versus informative results

```text
HARD (block): future-destroy tripwire integrity, holdout exclusion, causal
  provenance, emission completeness, estimand reconciliation, deterministic
  replay, no-local-accounting, and zero-cost compliance.
INFORMATIVE (operator judges): all observed frequencies, magnitudes, intervals,
  PSR, gap/tightness contrasts, volatility contrasts, and cross-venue replication.
```

## 15. Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission,
    or swap enters any calculation. Realised results would differ (likely worse) under any
    real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped
    experiment; the directive is recorded in that experiment's design.md.
```

## 16. Execution sequence

1. Fresh-context QA reviews the checkpoint and five experiment designs
   (including AMENDMENT-6/7/8/9/10/11/12).
2. Operator execution approval is required after QA approval.
3. Run cTrader-only matrix (264 cells), beginning with the EURUSD 30-day
   preflight cell under the INFR-021 fence.
4. Run the estimand-validation gate before analysis.
5. Analyse each experiment separately; no automatic family verdict.
6. Operator reviews evidence and decides whether any deferred breakout branch
   or Bybit re-admission is opened.
