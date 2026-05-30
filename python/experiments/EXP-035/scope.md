# Experiment: EXP-035 — Market Bias (CEREBR) Deterministic Port and State-Episode Readiness

## Hypothesis

This is a **readiness experiment**, not a return test. It states a falsifiable *port-determinism + count-eligibility* claim, not an edge claim:

> A deterministic Python port of the Market Bias (CEREBR) indicator — `EMA(OHLC, 100)` → Heiken-Ashi-style transform (with the source's `xhaopen[1]` recursion) → `EMA(haopen/haclose/hahigh/halow, 100)` → `osc_bias = 100·(c2 − o2)`, `osc_smooth = EMA(osc_bias, 7)` — in chart-timeframe mode reproduces the published Pine v5 formula deterministically (identical output under shuffle-then-resort and a convergent two-seeding warmup), and its sign-only (bull/bear) and four-way states have adequate independent-episode counts (Gate 2) at `1h`/`4h` on at least two distinct instruments in both train and test segments.

If the port cannot be made deterministic, if the two EMA seedings never converge to an identical state-label sequence within train history, if independent-episode counts are inadequate on `≥ 2` distinct instruments, or if state collapses into one dominant state, Market Bias is recorded as a readiness-gated no-go and no return test (EXP-037) opens for it.

## Question

Does a deterministic Python implementation of Market Bias reproduce the published Pine v5 formula (and, if exported reference values are available, match them bar-for-bar); what is the predeclared two-seeding warmup length `W` per instrument/timeframe; and in chart-timeframe mode do the sign-only (bull vs bear) and four-way (strong/weak bull/bear) states have adequate **independent-episode** counts at `1h`/`4h` per instrument and segment, with what transition counts and persistence?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`, deterministically aggregated to `1h` (60-minute) and `4h` (240-minute) clock-aligned OHLC bars via `python/src/bar_aggregator.aggregate_ohlc`. Market Bias is computed from the aggregated **real** OHLC. No chart-type generator inputs (the HA-style transform inside Market Bias is internal to the indicator port, not the project's `heiken_ashi_generator`). No 1-minute Market Bias.
- **Mode (locked)**: **chart-timeframe mode only** (`design.md` Candidate 2). The indicator timeframe equals the bar timeframe; per the source audit, `indexHighTF` and `indexCurrTF` both collapse to `0` and `f_no_repaint_request` reduces to the identity of its expression, so all `request.security`/multitimeframe/lookahead-offset semantics are no-ops. The port implements only the local EMA/HA recursion on the aggregated bars. **No multitimeframe import is built.**
- **Parameters** (all predeclared, frozen before implementation, never tuned on any result):
  - Market Bias constants from `docs/planning/market-bias.txt`: first smoothing `ha_len = 100`, second smoothing `ha_len2 = 100`, oscillator EMA `osc_len = 7`.
  - State definitions: **sign-only state (primary)** = `bull` if `osc_bias > 0` else `bear` (the `osc_bias == 0` measure-zero tie is assigned to the prior bar's state, predeclared, and its frequency reported). **Four-way state (secondary diagnostic)**: strong-bull (`osc_bias > 0 and osc_bias ≥ osc_smooth`), weak-bull (`osc_bias > 0 and osc_bias < osc_smooth`), strong-bear (`osc_bias < 0 and osc_bias ≤ osc_smooth`), weak-bear (`osc_bias < 0 and osc_bias > osc_smooth`) — matching the Pine `sigcolor` switch.
  - Timeframes: `1h` (`period_minutes = 60`) and `4h` (`period_minutes = 240`). `1d` is out of scope (no daily-session aggregator; and Market Bias is expected to be sample-constrained at `1d` after stacked EMA-100 smoothing — `design.md` §"Data Scope" and Candidate 2).
  - Aggregation coverage settings, both reported: **strict** (`min_coverage = None`) and **tolerant** (`min_coverage = 0.90`), inheriting EXP-034's predeclared coverage characterization. The binding canonical choice is confirmed at the mid-phase reflection; EXP-035 reports episode readiness under both so the reflection can lock one rule across the phase.
  - Warmup `W` (predeclared deterministic rule per `design.md` Candidate 2, amended): compute the four-way state sequence under two EMA seedings — Pine's `ta.ema` convention (SMA of the first `length` values, then recursive EMA) and a cold first-value seed — and set `W` to the smallest bar index beyond which **both seedings produce an identical state-label sequence for all subsequent bars**, floored at `300` same-timeframe bars. Discard the first `W` bars before any readiness metric. If the two seedings never converge to an identical label sequence within available train history, Market Bias **fails readiness** and is not return-tested. No `W` is chosen by inspecting any outcome.
  - Numeric/episode floors (Gate 2): each reported state must have `≥ 100` train rows, `≥ 50` test rows, `≥ 30` train independent episodes, and `≥ 15` test independent episodes. For this long-memory descriptor, **independent episodes are the binding denominator**; an episode is a maximal run of consecutive same-timeframe bars in the same state. Floors are applied to the sign-only states (bull, bear) as primary; four-way episode counts are reported as secondary diagnostics.
  - Reproducibility shuffle seed: `42`.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC. All four are scoped because Gate 2 and the matched-control replication unit require evidence on `≥ 2` distinct instruments, and the long-memory episode constraint must be characterized per instrument.
- **Time range**: Full dataset per instrument with the nested chronological split applied to the **1-minute series before aggregation** (first 70% analysis set via `load_analysis_timebars`; after aggregation, 70/30 train/test). The warmup `W` is discarded **after** the train/test split is defined on the aggregated series but episode/row counts are reported on the post-warmup bars within each segment. The final 30% global holdout is never loaded, inspected, aggregated, or used.
- **Global holdout**: Final 30% of each instrument's chronologically ordered 1-minute dataset is excluded before aggregation or any Market Bias computation. The full dataset is never aggregated and re-split.
- **Look-ahead bias prevention**: Aggregation uses only completed clock-aligned source windows. All EMAs are causal (each value uses only bars at or before its own index; the HA-open recursion uses `xhaopen[1]`/`haclose[1]`, i.e., strictly prior bars). The chart-TF collapse removes the Pine real-time `barstate.isrealtime` offset entirely, so there is no repaint/lookahead path to reproduce. Segment assignment is by the bar's own `CloseTime`, never by bar index.
- **Real-price outcome discipline**: This experiment computes **no** forward return, FE/AE, hit rate, turnover, or P&L. It is readiness-only. Market Bias is derived from EMA-smoothed construction values of the real OHLC, but because **no outcome is computed**, real-price discipline is a no-op here; it is exercised at EXP-037 (return test), where all outcomes will use the aggregated real OHLC, never the smoothed construction values. No HA or Renko construction price is ever used for any outcome.
- **Reference fidelity (predeclared fallback, amendment 4)**: Two port hazards are flagged from the source audit and must be implemented exactly: (a) the HA-open recursion keys off `xhaopen[1]` (the prior bar's `(o+c)/2`), **not** the standard `haopen[1]`; (b) Pine `ta.ema` seeds with the SMA of the first `length` values. **Preferred:** if an exported TradingView reference series for any instrument/timeframe is present under `docs/planning/` before implementation, compare the port bar-for-bar against it and report the max absolute deviation. **Pre-committed fallback:** no exported reference series is currently present (`docs/planning/` contains only `market-bias.txt`); EXP-035 therefore claims only **"deterministic re-implementation of the published Pine formula,"** does **not** claim Pine-equivalence, and any later negative Market Bias return result must carry the unverified-fidelity attribution caveat. A deterministic-but-unverified port is not, by itself, grounds to close the Market Bias branch.
- **Exclusions**:
  - No return, excursion, hit-rate, or P&L metric (blocked by the readiness-before-return gate, `design.md` Gate 1).
  - No matched-control comparison (EMA200 trend-sign control belongs to EXP-037).
  - No multitimeframe / higher-timeframe import; chart-TF only (`design.md` Gate 3 and Candidate 2).
  - No `1d` analysis.
  - No neutral-band definition: Market Bias's neutral/flat baseline is a **return-test** construct (`design.md` §"Locked Primary Edge Metric"); EXP-035 reports the `osc_bias` magnitude distribution so the reflection/EXP-037 scope can later define a flat band, but no neutral state is constructed or gated here.
  - No raw HA direction as a standalone candidate (subsumed by Market Bias; it may appear only as a secondary diagnostic, and is not required for this readiness scope).
  - No parameter variation of `100/100/7`.
  - No tick, bid/ask, spread, commission, or slippage fields.

## Success / Failure Criteria

The aggregate verdict is mechanical once the readiness table is computed. "Success" means *port determinism established and sign-only states count-eligible*, not any edge.

### Per-Instrument-Timeframe-Segment Readiness Checks

For each `(instrument, timeframe, segment)` cell, under the canonical aggregation (inherited from EXP-034; both strict and tolerant reported):

1. **Port determinism**: the SHA-256 digest of the serialized post-warmup `(CloseTime, osc_bias, osc_smooth, sign_state, four_way_state)` table matches between (a) a fresh load + aggregate + port pass and (b) a deterministically shuffled-then-resorted 1-minute load + the same pass. Both train and test digests must match. (`osc_bias`/`osc_smooth` compared at fixed `%.12g` formatting.)
2. **Warmup convergence**: the two-seeding warmup rule converges to an identical four-way state sequence at some `W ≤` (train length), with `W` floored at `300`. Non-convergence within train history fails readiness for that `(instrument, timeframe)`.
3. **Row floor**: each sign-only state (bull, bear) has `≥ 100` post-warmup rows in train and `≥ 50` in test.
4. **Episode floor**: each sign-only state (bull, bear) has `≥ 30` post-warmup independent episodes in train and `≥ 15` in test.
5. **No-collapse**: neither sign-only state holds `> 0.95` of post-warmup bars in either segment (state has not collapsed into one dominant state).

A `(instrument, timeframe)` pair **passes readiness** for Market Bias iff checks 1–5 hold for **both** segments.

### Secondary Diagnostics (reported, non-gating)

- Four-way state row and episode counts per cell (the strong/weak axis is expected to churn; reported to confirm it is a weak/secondary descriptor as `design.md` Candidate 2 anticipates).
- Median and distribution of episode length (bars) per state — persistence.
- Transition counts between states per segment.
- `osc_bias` magnitude distribution (for later neutral-band feasibility; non-gating here).

### Aggregate Verdict (Predeclared)

- **Evidence FOR readiness** (Market Bias advances to the mid-phase reflection as a return-test candidate): checks 1–5 pass on `≥ 2` distinct instruments in both segments at `≥ 1` timeframe under an admissible aggregation.
- **Evidence AGAINST / readiness-gated no-go**: the port cannot be made deterministic (check 1 fails for an unfixable reason), or warmup never converges (check 2), or independent-episode counts are inadequate on `≥ 2` distinct instruments (check 4), or state collapses (check 5), at every timeframe. Market Bias is recorded as a readiness-gated no-go; no EXP-037 opens for it.
- **Inconclusive**: determinism fails for a fixable implementation reason (fix and re-run before verdict), or exactly one instrument passes on an otherwise promising timeframe. Inconclusive relaxes no floor; it triggers a documented gap and a fix-or-close decision.

**Fast stop** (`design.md` Candidate 2): stop before any further work if the port cannot be made deterministic, if independent-episode counts are inadequate on `≥ 2` distinct instruments, or if state collapses into one dominant state.

### Mathematical Attainability

The episode floor is the binding constraint and is exactly what this experiment measures. EXP-007/EXP-009 found HA cuts 15m direction-change count to ~48–49% of time bars; Market Bias adds two stacked EMA-100 smoothings, so it will persist far longer and produce **fewer, longer** episodes. At `1h` (tens of thousands of analysis-set bars per instrument), even strong persistence plausibly yields hundreds of episodes per sign state — comfortably above the `30`/`15` floors. At `4h` (≈¼ the bars) and especially for the four-way strong/weak split, episode counts may be marginal; that risk is precisely what checks 4–5 test. No floor is set above what a moderately persistent two-state null could clear at `1h`, so failure cannot be a moved goalpost.

## Prerequisites and Sequencing

Requires:
- `python/src/market_bias.py` — **one new reusable module** (the single new module permitted by `design.md` complexity budget), implementing the deterministic chart-TF port: causal EMA with Pine SMA-seeding, the HA-style transform with the `xhaopen[1]` recursion, the oscillator, and the sign-only/four-way state labels, plus the two-seeding warmup determination.
- `python/src/bar_aggregator.aggregate_ohlc` with the `min_coverage` parameter added in EXP-034 (reused unchanged).
- `python/src/ict_timebar.load_analysis_timebars`, `train_cutoff_time`, `INSTRUMENTS` (reused unchanged).
- EXP-034's coverage characterization (strict-vs-tolerant). EXP-035 reports under both; the binding canonical rule is confirmed at the mid-phase reflection.

EXP-035 is the second and final Stage A readiness experiment. The mid-phase reflection follows EXP-035 and issues the return-test directive before any EXP-036/037 scope (`design.md` Gate 7).

## Complexity Budget

- **Max statistical test families: 0.** Readiness is exact counts, deterministic digests, exact episode/transition counts, and a deterministic warmup determination. No inferential statistic or bootstrap is needed (`design.md` allows ≤ 3; `0` is chosen deliberately for a determinism/count survey).
- **Max primary visualisations: 4.**
- **Max new reusable modules: 1** — `python/src/market_bias.py`. This is the single new module `design.md` reserves for the Market Bias port. All aggregation/loading reuses existing modules.

## Data Requirements

For each instrument and each timeframe (`60`, `240` minutes), under both aggregation settings:

1. Load the holdout-excluded 1-minute analysis frame via `load_analysis_timebars(DATA_DIR, instrument)`.
2. Aggregate to the target timeframe via `aggregate_ohlc(frame_1m, period_minutes=tf, min_coverage=setting)`.
3. Apply the nested 70/30 chronological train/test split; record the per-cell train cutoff `CloseTime`.
4. Compute Market Bias via `market_bias.compute_market_bias(bars_tf)` (SMA-seeded EMAs; `xhaopen[1]` HA recursion; oscillator; sign-only and four-way states).
5. Determine warmup `W` via `market_bias.convergence_warmup(bars_tf, floor=300)` (two-seeding identical-label convergence). Discard the first `W` bars.
6. Compute post-warmup row counts, independent-episode counts, episode-length persistence, and transition counts per state per segment.
7. Compute determinism digests (canonical vs shuffled-then-resorted).
8. If an exported reference series exists, compute the bar-for-bar max-abs deviation; otherwise record the deterministic-only claim and the pre-committed caveat.
9. Apply the aggregate verdict mechanically.

### Standard Loading Pattern

```python
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

from ict_timebar import INSTRUMENTS, load_analysis_timebars, train_cutoff_time
from bar_aggregator import aggregate_ohlc
from market_bias import compute_market_bias, convergence_warmup

DATA_DIR = PYTHON_ROOT.parent / "data"

for instrument in INSTRUMENTS:
    loaded = load_analysis_timebars(DATA_DIR, instrument)  # first 70% only
    bars_tf = aggregate_ohlc(loaded.frame, period_minutes=60, min_coverage=None)
    mb = compute_market_bias(bars_tf)  # adds osc_bias, osc_smooth, sign_state, four_way_state
```

## Suggested Direction

Report the port-determinism digests and the warmup-convergence `W` per instrument/timeframe **first**, so the readiness counts that follow are known to come from a deterministic, warmed-up series. Then report the sign-only episode-count readiness grid (the binding gate), the four-way episode counts and persistence as secondary diagnostics, and the `osc_bias` magnitude distribution for later neutral-band feasibility. The verdict is mechanical: checks 1–5 on `≥ 2` distinct instruments at `≥ 1` timeframe, or a readiness-gated no-go. State the reference-fidelity status (deterministic-only vs reference-matched) explicitly in every readiness conclusion.
