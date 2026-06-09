# Experiment: EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

## Hypothesis

The corrected C# AVWAP strategy running on cTrader via per-bar streaming
(`Mode=StrategyHost`, pyramid bounces included) produces event-level results
consistent with the Python-only EXP-028 event-level re-analysis — the per-domain
event-level verdicts and effect directions agree, and CIs overlap — confirming
that the Python re-analysis faithfully represents the cTrader execution path.

## Question

EXP-028 evaluated the faithful AVWAP strategy under the EXP-027 event-level method
using **Python re-analysis** of upstream synthetic-event artifacts (EXP-020 events,
EXP-022 lifetime observations). It found `EVAL_SUPPORTED` with all 3 domains
`EVIDENCE_FOR`. But EXP-028 never ran the actual C# strategy on cTrader — the
per-bar streaming path validated in VAL-002 was bypassed.

Does the C# strategy, running bar-by-bar inside cTrader's engine with the corrected
pyramid handling, reproduce EXP-028's event-level findings? Or do discrepancies
between the C# per-bar execution and the Python re-analysis change the verdict?

## Rationale

This experiment closes the omission documented in
`docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md`:
EXP-028 was supposed to reuse and correct EXP-023's C# code and run directly on
cTrader, but was implemented as a pure Python re-analysis. Without this step, the
`EVAL_SUPPORTED` verdict lacks cTrader-side confirmation.

## Strategy Definition

The strategy is `CF-AVWAP-001/HYP-004-R` (the EXP-028 re-screen slot; same baseline
as EXP-023/028), with one correction to the C# implementation:

| Component | Specification |
|-----------|--------------|
| Regime detector | MA crossover, fast 20 / slow 50, on domain `Close` |
| AVWAP source | Typical price `(High + Low + Close) / 3` |
| AVWAP weight | `TickVolume ** 0.75` |
| Band spread | Median absolute deviation from anchored typical-price path |
| Band multiplier | 1.0 |
| Bounce definition | EXP-020: arm on close below AVWAP (bullish)/above AVWAP (bearish); trigger on close crossing back |
| Exit rule | EXP-022 band-target/trend-change completion rule |
| Pyramid handling | **CORRECTED from EXP-023**: each pyramid bounce becomes a tradable position, matching the EXP-028 scope definition and the original `anchored-vwap.md` concept. `AvwapBounceModel.cs` already *emits* pyramid bounce events (tagged `bounce_pyramid` / `isPyramid`) but *suppresses the position* (`pyramid_skipped`, single concurrent position). The correction is on the **position/completion side**: open and independently track a position for each pyramid bounce, with `is_pyramid_bounce` exposed on the table EXP-029 consumes for per-event returns. |

**Cost**: None (event-level edge test, matching EXP-028).

## Scope Boundaries

- **Data Views**:
  - cTrader `Mode=StrategyHost` output: `positions.parquet`, `events.parquet`,
    `trade_blotter.parquet`, `run_metadata.json` — emitted by the corrected C#
    `AvwapBounceModel.cs` running inside cTrader's engine via Docker/ctrader-cli.
  - Domain bars: 5m (strict), 1h/4h (`min_coverage=0.90`) — resampled internally
    by the C# strategy host from 1-minute cTrader feed data.
  - No chart-type views.
- **Candidate family / registry**: `CF-AVWAP-001/HYP-004-R` (re-screen of HYP-004),
  same registry slot as EXP-028.
- **Comparison target**: EXP-028 results (`python/experiments/EXP-028/results/`):
  per-domain event-level effects, CIs, Holm-p, and verdicts.
- **Parameters**:
  - instruments: BTCUSD, EURUSD, USTEC, XAUUSD (match EXP-028);
  - domains: 5m (strict), 1h (min_coverage=0.90), 4h (min_coverage=0.90);
  - strategy parameters: identical to EXP-023/028 (MA fast=20, slow=50; band
    multiplier=1.0; AVWAP weight exponent=0.75);
  - cTrader backtest range: full available data, fenced by `AnalysisEndUtc` per
    instrument (same endpoints as EXP-023: BTCUSD 2025-06-17, EURUSD 2025-05-09,
    USTEC 2025-05-12, XAUUSD 2025-05-12);
  - inference: EXP-027 event-level method (regime-cluster bootstrap 1000 resamples,
    stratified sign-permutation 1000 resamples, Holm across 3 domains, α₀=0.05);
  - fixed seeds; deterministic generation.
- **Time range**: Full dataset with nested chronological split. cTrader runs are
  fenced by `AnalysisEndUtc` (first 70% only). Python re-asserts the holdout fence.
- **Global holdout**: The final 30% of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any capacity.
  cTrader strategy-host runs must emit no row at or after `AnalysisEndUtc`.
- **Look-ahead bias prevention**:
  - C# strategy processes bars sequentially in cTrader's engine (no look-ahead).
  - All temporal ordering by domain-bar `CloseTime` / `SourceCloseTime`.
  - Event-level inference uses only information available at the event timestamp.
- **Real-price outcome discipline**: All event-level returns are direction-signed
  log returns on real domain `Close` prices emitted by cTrader (`RealClose`),
  in bps. No synthetic chart prices.
- **C# code corrections from EXP-023** (position/completion side only — the bounce
  *event* stream, including pyramids, is already emitted and tagged):
  1. Open a position for each pyramid bounce. Currently a bounce triggering while a
     position is active records `pyramid_skipped` (zero size) and opens no second
     position; the model holds a single position (`_position`, `_favorableTarget`,
     `_adverseTarget`). Replace that single-position state with a set of
     concurrently-tracked positions so a pyramid bounce opens its own position with
     its own frozen targets.
  2. Track each active position's completion (band-target/trend-change)
     independently — each position has its own entry price, targets, and exit bar.
     Multiple simultaneous positions are permitted.
  3. Expose `is_pyramid_bounce` on the emitted table EXP-029 consumes for per-event
     returns. The model already computes `isPyramid = _bounceCount > 1` and tags the
     event (`bounce_pyramid`); ensure the per-position/per-event record serializes it,
     matching the EXP-028 diagnostic split.
  4. **Serialize the C#-executed completion per bounce (F01).** When a position
     completes, backfill its source `AvwapEventDetail` row with the executed exit:
     `ExitIdx`, `ExitTime`, `ExitClose`, `ExitReason`
     (`favorable`/`adverse`/`trend_change`/`open`), `ExitBars`, and the
     direction-signed `ExitLifetimeBps`. This is serialization of already-computed
     completion state (the exit is computed in `MaybeCompletePosition` regardless) and
     lets the Python harness **grade** the corrected concurrent-completion code per
     event against its own `scan_lifetime`, instead of only re-scanning exits in
     Python (which would leave the new C# exit logic unvalidated).
  5. No other changes to the C# signal logic. The regime detector, AVWAP
     computation, band spread, bounce trigger/tag, and re-arm rules are identical to
     EXP-023; only position opening, completion tracking, and the executed-exit
     serialization change.
- **Python code**:
  - A new `run_experiment.py` under `python/experiments/EXP-029/code/` that:
    1. Invokes `tools/ctrader-cli/run-exp029-backtests.sh` (or equivalent) to
       orchestrate the cTrader Docker backtests.
    2. Loads the emitted `events.parquet` and `positions.parquet` from
       `data/strategy_runs/`.
    3. Reconstructs per-event returns (entry trigger close to completion close,
       direction-signed log bps) **and** the symmetric own-exit matched controls
       for each cTrader event — exactly as EXP-022/EXP-027/EXP-028 construct them
       (`role=control` rows per `(instrument, domain, regime_id, event_trigger_idx)`,
       each completed under the same exit rule from its own non-trigger start). The
       binding PRIMARY estimand is per-event matched-control **excess**
       (`event_lifetime_bps − mean(control_lifetime_bps)`) — the cTrader run emits
       only the strategy's positions, not controls, so the controls must be rebuilt
       here so EXP-029 compares the **same estimand** EXP-028 reports, not raw
       per-event return.
    4. Runs the frozen EXP-027 event-level inference tail (imported unchanged,
       hash-guarded — and the hash is **hard-asserted equal to EXP-028's**
       `ea261b9ee0a8aca3`, F05) on the cTrader-derived per-event excess.
    5. Compares per-domain effects, CIs, verdicts, **and the predeclared magnitude /
       count / pyramid / exit-parity / signal-layer gates** against EXP-028 artifacts.
    6. **Grades the C# completion code (F01).** For every Python-scanned event,
       compares the C#-executed completion (`ExitIdx`/`ExitReason`/`ExitLifetimeBps`)
       against the Python `scan_lifetime` completion on the same feed; writes
       `exit_parity.csv` and a per-domain pass/fail used by the disposition.
    7. **Reconciles the signal layer (F03).** Compares the C# 5m event set against the
       EXP-020 `avwap_events.csv` substrate (trigger-set match fraction + matched
       frozen-target agreement); writes `signal_reconciliation.csv` and a 5m
       pass/fail used by the disposition.
- **Exclusions**:
  - Any change to the EXP-027 event-level inference method (it is frozen;
    EXP-029 uses it unchanged);
  - Any strategy parameter tuning, band multiplier sweep, exit-rule redesign,
    stop/target logic, position sizing, or cost/slippage modeling;
  - Detector/anchor branches (`/LB`, `/MB`, `/ATR`, `/ANCHOR`), `/ALPHA`,
    `/BAND`, cross-timeframe variants (all deferred as in Phase 006);
  - HYP-001 (direct AVWAP line S/R) — remains untested, out of scope;
  - The frozen per-bar qualification suite (this is an event-level parity check,
    not a re-screening through the per-bar referee);
  - Percentage improvement against a zero or near-zero baseline — report bps
    effects, absolute rates, and CIs.

## Parity Criteria

> **Adversarial-review strengthening (2026-06-09).** The original criteria were a
> coarse "verdict + CI-overlap" read that could only *confirm or fail to confirm*
> EXP-028 — a magnitude divergence or a bug in the corrected C# completion code could
> not actually flip the disposition. The criteria below add four binding gates so a
> genuine execution-path divergence can downgrade EXP-028, and so the new C# code is
> graded rather than merely run. All thresholds are predeclared here, before any
> cTrader result exists (D8: no goalpost-moving).

A domain is **CONSISTENT** only when **all** of the following hold:

1. **Verdict agreement** — EXP-029 PRIMARY verdict == EXP-028 PRIMARY verdict
   (`EVIDENCE_FOR` / `EVIDENCE_AGAINST` / `INCONCLUSIVE_*`).
2. **Magnitude equivalence (F02)** — the EXP-029 vs EXP-028 effect difference is
   inside the predeclared margin `|Δ| ≤ max(2 bps, 25%·|EXP-028 effect|)`. This is the
   principled replacement for the demoted "point estimate inside EXP-028 CI" check;
   CI overlap is retained only as a diagnostic. (Overlapping CIs is a lax agreement
   test and cannot bound the actual effect-size disagreement.)
3. **Count alignment (F04)** — EXP-029 vs EXP-028 total count, bull/bear balance, **and
   pyramid split** each within ±10%. The pyramid split is the direct signature of the
   multi-position correction and is now inside the gate (previously omitted).
4. **Exit-parity (F01)** — the C#-executed completion reproduces the Python
   `scan_lifetime` completion (exit bar, reason, signed bps) on the **same feed** for
   ≥99% of completed events. This grades the corrected concurrent-completion code
   itself, which the binding estimand's symmetric Python re-scan would otherwise leave
   unchecked.
5. **Signal-layer 5m (F03, 5m only)** — the C# 5m AVWAP event set reproduces the
   EXP-020 substrate (≥98% of EXP-020 5m triggers matched; matched frozen targets'
   median relative difference ≤1e-3). On 5m the cTrader feed reproduces local bars to
   float precision (VAL-002), so this isolates *signal-layer* parity from feed drift.

A domain is **INCONSISTENT** when any of:
- the verdict disagrees, EXP-029 produced a **finite** effect, **and** the CIs do not
  overlap (a real, powered contradiction — an *underpowered* EXP-029 domain is
  INCONCLUSIVE, not INCONSISTENT);
- the effect difference exceeds the larger margin `max(2 bps, 50%·|EXP-028 effect|)`
  (a material magnitude divergence);
- exit-parity fails (the C# completion code does not reproduce the rule on the same
  feed — this is a code-correctness failure, independent of statistical power).

A domain is **INCONCLUSIVE** otherwise — e.g. counts differ by >20%, the verdict
differs but CIs overlap (power-limited), or the domain is underpowered.

**Overall disposition.** **INCONSISTENT** if any domain is INCONSISTENT (it vetoes an
upgrade). Else **CONSISTENT** iff all five gates hold on ≥2 of 3 domains **and** the
5m signal-layer reconciliation passes. Else **INCONCLUSIVE**.

Note: per-event returns / membership may still differ slightly from EXP-028 because
cTrader resamples its **own feed** (VAL-002: 5m float-exact; 1h/4h ≤1.83 bps). Such
1h/4h feed-coverage differences are expected and benign — absorbed by the ±10% count
tolerance — and are **not**, on their own, grounds for INCONSISTENT. They are *not*
charged to the signal layer, which is reconciled only on the feed-exact 5m domain.

If INCONSISTENT, the C# code and Python re-analysis are both investigated to locate
the source of divergence. The Python-only EVAL_SUPPORTED is downgraded to
`EVAL_UNCONFIRMED` until the divergence is resolved.

## Success / Failure Criteria

- **Parity CONFIRMED** (all five binding gates hold on ≥2 of 3 domains **and** 5m
  signal-layer OK, with no INCONSISTENT domain): EXP-028's Python-only EVAL_SUPPORTED
  is upgraded to cTrader-confirmed. The faithful AVWAP strategy has cTrader per-bar
  streaming evidence of event-level edge under the EXP-027 yardstick — entry signal,
  pyramid handling, **and** the executed completion code all graded — consistent with
  the Python re-analysis.
- **Parity INCONCLUSIVE** (counts diverge >20%, power-limited domains, or a 5m
  signal-layer divergence that is not itself a hard inconsistency): document the
  discrepancies and their likely cause. The Python-only verdict stands as-is.
- **Parity INCONSISTENT** (any domain: powered verdict flip with non-overlapping CIs,
  a magnitude divergence beyond the larger margin, **or** an exit-parity failure):
  escalate. The C# per-bar execution disagrees with the Python re-analysis or the
  completion code does not reproduce the rule. EXP-028 is downgraded to
  `EVAL_UNCONFIRMED` pending root-cause.

### Deliberate deviation from EXP-028 (F07, documented)

EXP-028 drew the {1,3,6}-horizon secondary-stability inputs from EXP-021's
`reaction_observations.csv` (EXP-021's horizon-aware control rule). EXP-029 instead
computes the same fixed-horizon paired excess from its **cTrader-feed** events and the
EXP-022 lifetime controls (`_fixed_horizon_rows`). This is the correct cTrader-feed
analog (using local EXP-021 observations would be a feed mismatch) and is a different
control-selection rule from EXP-028's only for this **non-binding** secondary-stability
downgrade guard — it never enters the binding primary effect. Recorded here as a
deliberate, justified deviation, not a silent change.

## Complexity Budget

- Max statistical tests: **3** (regime-cluster bootstrap CI; stratified sign-permutation
  + Holm; parity comparison metrics — reuses tests 1-2's machinery). The added
  exit-parity, signal-layer, and magnitude-equivalence checks are **deterministic
  comparison metrics** under the parity-comparison test, **not** new statistical tests
  (no new bootstrap/permutation/estimator), so the budget is unchanged.
- Max visualisations: **3** (cTrader-vs-Python effect comparison forest;
  event-count / pyramid diagnostic; per-domain verdict / gate alignment table — the
  new gates are surfaced as columns in the existing table, no new plot).
- Max new code modules: **1** (`python/experiments/EXP-029/code/run_experiment.py`);
  plus the C# pyramid-handling + executed-exit-serialization correction in
  `AvwapBounceModel.cs`. No new or modified shared `python/src/xen/` module.

## Data Requirements

### Required Upstream Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| EXP-027 validation | `python/experiments/EXP-027/results/run_metadata.json` | Must be METHOD_VALID |
| EXP-028 results | `python/experiments/EXP-028/results/event_level_results.csv` | Comparison target |
| EXP-028 metadata | `python/experiments/EXP-028/results/run_metadata.json` | overall_verdict + frozen hash (F05) |
| EXP-028 diagnostics | `python/experiments/EXP-028/results/event_diagnostics.csv` | Per-domain pyramid counts (F04 gate) |
| EXP-020 substrate | `python/experiments/EXP-020/results/avwap_events.csv` | 5m signal-layer reconciliation (F03) |
| cTrader CLI | `tools/ctrader-cli/` | Backtest orchestration |
| C# StrategyHost | `StrategyHost/AvwapBounceModel.cs` (corrected) | Strategy execution |

### C# Code Correction Required

The pyramid fix in `AvwapBounceModel.cs`:

- Current EXP-023 behavior: the bounce *event* (including pyramids) is already
  emitted and tagged (`bounce_pyramid` / `isPyramid`), but when a bounce triggers
  while a position is active the model records `pyramid_skipped` (zero size) and
  opens no second position; it tracks one position at a time.
- Required EXP-029 behavior: when a bounce triggers while a position is active, open
  a new position (with `is_pyramid_bounce=true` on its position/trade record) and
  track its completion independently alongside the prior position(s).
- The completion scan (band-target/trend-change) evaluates each active position
  independently. Multiple simultaneous positions are permitted.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
RUNS_DIR = DATA_DIR / "strategy_runs"
EXP028_RESULTS = Path("python/experiments/EXP-028/results")

# Load cTrader-emitted data
events = pl.read_parquet(sorted(RUNS_DIR.glob("avwap_baseline_*/events.parquet"))[-1])
positions = pl.read_parquet(sorted(RUNS_DIR.glob("avwap_baseline_*/positions.parquet"))[-1])

# Load EXP-028 comparison target
ref = pl.read_csv(EXP028_RESULTS / "event_level_results.csv")
```

## Suggested Direction

1. **C# correction**: Update `AvwapBounceModel.cs` so each pyramid bounce opens its
   own independently-tracked position with its own completion scan (the bounce
   events are already emitted/tagged; the change is on the position/completion side).
2. **cTrader run**: Orchestrate `tools/ctrader-cli/` backtests for all 4
   instruments × 3 domains (12 cells). The existing `run-exp023-backtests.sh`
   script can be adapted (new strategy mode or parameter to enable pyramids).
3. **Harness**: `run_experiment.py` loads cTrader-emitted events, reconstructs
   per-event returns (entry trigger close to completion close), applies the
   EXP-027 inference tail unchanged, and compares per-domain results against
   EXP-028.
4. **Comparison**: Per-domain effect forest plot overlaying cTrader and Python
   point estimates with CIs. Verdict alignment table. Event-count diagnostic.
5. **Interpretation**: If CONSISTENT on ≥2 of 3 domains, EXP-028 is confirmed
   on cTrader per-bar streaming. If INCONSISTENT, investigate divergence before
   any programme-level conclusion.
