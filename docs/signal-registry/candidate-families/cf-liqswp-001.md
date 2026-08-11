# CF-LIQSWP-001 — Liquidity Sweeps

- **Status:** `REGISTERED` — 2026-08-11, checkpoint-019
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

- Bybit: top 10 admitted USDT linear perpetuals by 30-day `sum(close*volume)`
  at the TRAIN boundary. Pin: `cf-liqswp-001-universe.json`.
- cTrader: `EURUSD.CTrader`, `XAUUSD.CTrader`, and `USTEC.CTrader`, kept
  separate from Bybit and from one another.
- Observation timeframes: 15m, 30m, 1h.
- Engine input: 1m bars. Base-bar parity uses `xen.bar_aggregator`.
- All distances are emitted in raw price, bps, and ATR units. The ATR unit is
  causal Wilder ATR(14) on the observation timeframe, using only completed bars.

### Level catalogue

1. Previous completed 1H, 4H, 1D, and 1W highs and lows.
2. Previous completed Asia, Europe, and America session highs and lows using
   the approved local IANA/DST-aware windows.
3. Causal rolling highest-high and lowest-low over 16, 32, 64, 128, and 256
   completed observation bars.

All four timeframe levels are included. Each level keeps a stable source identity and remains
tracked until its direction-opposing event. Coincident prices are not merged.

### Raid state

- High excursion: a 1m high strictly above the level.
- Low excursion: a 1m low strictly below the level.
- Return: a later inclusive touch back to the level.
- A same-bar cross-and-return is retained as `AMBIGUOUS_INTRABAR` and excluded
  from the primary completed-raid estimand.
- Every completed raid is retained. Previous raids on the same level are linked
  and counted; they are not collapsed.
- If multiple levels are raided before confirmation, the most recent resolvable
  raid receives primary attribution. Same-bar ties remain explicitly tied while
  all levels retain their excursion state.

### Confirmation and outcome

For 15m/30m observations, confirmation events use 1H levels. For 1h
observations, they use 1D levels. The two confirmation definitions are separate:

- `BREAKOUT_BAR`: the completed higher-timeframe bar closes beyond the previous
  completed higher-timeframe bar’s high or low.
- `LEVEL_CLOSE`: the completed higher-timeframe bar closes beyond the selected
  configured higher-degree level. Every level configuration is reported
  separately; overlapping configurations are not silently pooled.

The expected-side event confirms a sweep. An excursion-side event confirms a
breakout and retains the raid as a failed sweep. The later swing ends at the
first opposing confirmation event after sweep confirmation. No arbitrary
timeout is imposed; unresolved paths are right-censored at the TRAIN boundary.

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
tight_gap = gap_span < 0.30 * VA_width
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
- No pooled Bybit/cTrader verdict.

## Implementation path

Shared streaming detector and TPO profile state are implemented once and reused
by the five experiment configurations. Every price-primary run uses Nautilus;
Python validates emitted state and computes the registered estimands only.

## Real-price and holdout discipline

Signals and event states use confirmed data through `t-1` at the decision bar
open. One-minute fill simulation remains engine-native. The global Bybit and
cTrader fences are asserted before data access, and holdout data is never
loaded.
