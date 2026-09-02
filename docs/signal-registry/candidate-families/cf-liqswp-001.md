# CF-LIQSWP-001 — Liquidity Sweeps

- **Status:** `REGISTERED` — 2026-08-11, checkpoint-019; amended 2026-08-13 (AMENDMENT-6/7/8/9/10/11/12/13/14); family status unchanged
- **Chapter:** 06
- **Source of truth:** `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md`
- **Checkpoint:** `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/design.md`
- **Route:** `EXP-100` apparatus → `EXP-101` significance → `EXP-102` repeated raids → `EXP-103` value gap → `EXP-104` volatility regime
- **Execution:** Nautilus `BacktestNode`, 1-minute primary bars, TRAIN only

## Thesis

Liquidity levels can be represented as causal, persistent objects. A completed
raid may be followed by a strong move in the opposite direction. The checkpoint
measures whether level degree, repeated interaction, a tight TPO value gap, and
volatility regime describe different outcome distributions. It does not predict
the raid live and does not make a cost-complete trading or deployment claim.

## Frozen definitions

### Universes and timeframes

- **cTrader only (AMENDMENT-7):** `EURUSD.CTrader`, `XAUUSD.CTrader`, and
  `USTEC.CTrader`, kept separate from one another. Pin:
  `cf-liqswp-001-universe.json`.
- **Bybit/crypto:** excluded until a later operator amendment.
- Observation timeframes: 15m, 30m, 1h. Raid start, return, and beyond are
  decided on these bars (SoT bar-by-bar grain; AMENDMENT-8). Same-bar return
  does not close a raid (AMENDMENT-13).
- Engine input: 1m bars. Base-bar parity uses `xen.bar_aggregator`. 1m remains
  the TPO / max-excursion / swing-extreme / fill-path grain (AMENDMENT-3).
- All distances are emitted in raw price, bps, and ATR units. The ATR unit is
  causal Wilder ATR(14) on the observation timeframe, using only completed bars.

### Level catalogue

1. Previous completed 1H, 4H, 1D, and 1W highs and lows.
2. Previous completed Asia, Europe, and America session highs and lows using
   the approved local IANA/DST-aware windows.
3. Causal rolling highest-high and lowest-low over 7, 14, 22, and 252
   completed observation bars (AMENDMENT-11).

Previous 1D/1W levels are the last completed New York 17:00 trading day and the
last completed Monday–Friday trading week (AMENDMENT-10). They are not
contiguous 1,440/10,080-minute bars.

All four timeframe levels are included. Each level keeps a stable source identity.
Coincident prices are not merged. Raid lifetime follows AMENDMENT-6 (below).

### Raid state

- High excursion / raid start: a completed observation-bar high strictly above the level.
- Low excursion / raid start: a completed observation-bar low strictly below the level.
- Return: an inclusive observation-bar touch back to the level, same bar or later.
  Recorded; does not open or close the raid (AMENDMENT-13).
- Same-bar pierce-and-return stays live until confirmation/fail or TRAIN censor.
  `AMBIGUOUS_INTRABAR` is retired.
- A 1-minute wick that does not survive the observation OHLC is not a raid
  (AMENDMENT-8; original SoT grain).
- Every completed raid is retained. Previous raids on the same level are linked
  and counted; they are not collapsed.
- If multiple levels/raids are eligible before confirmation, the most recent
  resolvable raid receives primary attribution (AMENDMENT-6). Same-bar ties
  remain explicitly tied. Each raid retains its own excursion state through
  settlement.

### Confirmation and outcome

For 15m/30m observations, confirmation events use 1H. For 1h observations,
both 1H and 4H are kept as separate strata (AMENDMENT-9). 1D confirmation is
retired. The two confirmation definitions are separate:

- `BREAKOUT_BAR`: the completed higher-timeframe bar closes beyond the previous
  completed higher-timeframe bar’s high or low.
- `LEVEL_CLOSE`: the completed higher-timeframe bar closes beyond the selected
  configured higher-degree level. Every level configuration is reported
  separately; overlapping configurations are not silently pooled.

**AMENDMENT-6 (close-all-eligible):** on each completed reference event, every
eligible returned unconfirmed raid is settled. Expected-side: latest raid stays
primary and live for the later swing; earlier eligible raids close immediately
as `CONFIRMED_NON_PRIMARY` with profiles finalized at that close. Opposing-side:
every eligible returned unconfirmed raid fails as `FAILED_BREAKOUT`. Every
primary-attributed confirmed raid completes on the first opposing reference
event after confirmation. No arbitrary timeout; unresolved paths are
right-censored at the TRAIN boundary.

AMENDMENT-14 adds `pre_mfe_retrace={price,status}` for the side-aware maximum
pre-terminal-MFE retracement after confirmation. `AMBIGUOUS_SAME_BAR` and
`NO_POST_CONFIRMATION_MFE` remain explicit states; the field changes no population,
control, or HYP-000 false qualifier.

### TPO value gap

The profile is built online from 1m bars between the maximum-excursion-setting
bar and the completed close of the same-direction confirmation event. Each
1m bar contributes one TPO count to every fixed price bin intersecting its
inclusive low-high range. Bin width is `0.10 × ATR_unit`, with ATR_unit frozen
causally when the active profile begins.

The VA grows from the lowest-price maximum-TPO bin to at least 70% of total TPO
count; upper-bin-first ties apply. The value gap is the lowest-density set of VA
bins reaching at least 30% of VA TPO count. The exact selected-bin mask and its
outer span are emitted.

```text
VA_width = VAH - VAL
gap_span = gap_high - gap_low
tight_gap = gap_span < 0.50 * VA_width
```

`tight_gap` is an event label, not a machine verdict. Zero/undefined ATR,
degenerate profiles, and bin-resolution limits receive explicit reason codes.

## Hypotheses and experiments

| Hypothesis | EXP-ID | Primary question |
|---|---|---|
| `CF-LIQSWP-001/HYP-000` | `EXP-100` | Does the streaming object record levels, raids, confirmation, breakouts, and later outcomes causally and reproducibly? |
| `CF-LIQSWP-001/HYP-001` | `EXP-101` | Do higher-degree level strata have different later swing magnitude, duration, or strong-move frequency? |
| `CF-LIQSWP-001/HYP-002` | `EXP-102` | Does prior raid count change later swing outcomes? |
| `CF-LIQSWP-001/HYP-003` | `EXP-103` | Are sweeps with a tight value gap associated with different later outcomes than other defined profiles? |
| `CF-LIQSWP-001/HYP-004` | `EXP-104` | Does causal volatility regime describe raid frequency, magnitude, duration, and outcome quality? |
| `CF-LIQSWP-001/HYP-005` | deferred | Are breakout-causing levels uniquely significant? Operator-gated and not in the initial batch. |

## Exclusions

- No live sweep prediction claim.
- No absolute-distance “strong move” threshold; continuous ATR outcomes and
  `swing_atr > max_excursion_atr` are used.
- No cost, spread, funding, commission, tradability, or deployability claim.
- No TEST or holdout reads.
- No pooled cross-asset verdict. Bybit is out of scope (AMENDMENT-7).

## Implementation path

Shared streaming detector and TPO profile state are implemented once and reused
by the five experiment configurations. Every price-primary run uses Nautilus;
Python validates emitted state and computes the registered estimands only.

## Real-price and holdout discipline

Signals and event states use confirmed data through `t-1` at the decision bar
open. One-minute fill simulation remains engine-native. The cTrader INFR-021
fence is asserted before data access (AMENDMENT-7). Holdout data is never
loaded.

## Evidence record

| Experiment | Evidence disposition | Read accounting |
|---|---|---|
| `EXP-100` / `HYP-000` AMENDMENT-14 | **COMPLETED — operator-approved with scoped exclusion.** Retain the current 264-cell TRAIN run. Exclude every ATR-undefined excursion and derived value: 780/9,840,478 emitted rows affected (0.007926%); 390 unique affected objects after method deduplication; 84 affected primary/completed rows; median affected understatement 71.43%. Coverage, chronology, lifecycle, status, attribution, and the finite-population future-destroy result are retained. Analyst assigned no replacement verdict; operator verdict is recorded separately in the report. | 0 counted TEST reads; 0 holdout reads; 0 candidate slots |
| `EXP-101` / `HYP-001` | **INCONCLUSIVE (2026-09-02).** Strong-move rate falls vs short baselines on previous-period and rolling families; session family and declared ATR/duration means do not jointly move. Operator: not a general higher-degree leftover mechanism. | 0 counted TEST reads; 0 holdout reads; 0 candidate slots |
| `EXP-102` / `HYP-002` | **COMPLETED — descriptive ATR/strong-move only (2026-09-02).** Later completed raids usually leave a smaller leftover and a lower strong-move rate than first raids. Duration does not confirm. Operator narrowed the analyst SUPPORTED tag. | 0 counted TEST reads; 0 holdout reads; 0 candidate slots |
| `EXP-103` / `HYP-003` | **INCONCLUSIVE (2026-09-02).** Tight DEFINED leftovers often smaller in ATR; duration does not separate; tight arm ~6% of the outcome population; BB/LC duplicates. | 0 counted TEST reads; 0 holdout reads; 0 candidate slots |
| `EXP-104` / `HYP-004` | **COMPLETED — descriptive ATR/strong-move only (2026-09-02).** LOW leftovers larger vs MID, HIGH smaller. Duration goes the other way on HIGH; start-rate is highest in HIGH while leftover ATR is weaker. Operator narrowed the analyst SUPPORTED tag. | 0 counted TEST reads; 0 holdout reads; 0 candidate slots |

Binding operator verdict: “retain the current run; ATR-undefined excursion values are
limited/invalid and must be excluded from all interpretations; make no implementation changes;
perform no reruns/emissions.”

This is an evidence row only. The family status remains `REGISTERED`; no checkpoint family
decision exists. Family promotion, closure, or retirement is reserved for an operator-signed
checkpoint retrospective.
