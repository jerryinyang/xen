# Experiment: EXP-030 — Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy

## Hypothesis

Under a predeclared, event-level per-position cost/slippage model (conservative variant
binding), the faithful selective AVWAP strategy — trade logic identical to the
EXP-028/029 baseline — retains positive **net** per-event expectancy on at least one
domain (5m, 1h, 4h), on the first-70% analysis set.

## Question

The Phase 006 result (+5.78 / +23.38 / +69.02 bps per-event matched-control excess on
5m/1h/4h, EVAL_SUPPORTED, cTrader-confirmed) is **gross of all costs**. Does the edge
survive realistic spread/commission/slippage charged once per realized position
(pyramid legs included), or is it consumed by execution costs? This is the **hard gate**
for any future holdout-release experiment (EXP-032, deferred): the global holdout is
never released to confirm a gross edge.

## Execution Path (named explicitly, per Phase 006 lesson 1)

**Python re-analysis of the cTrader-confirmed upstream artifacts.** The per-event
lifetime outcomes are the EXP-020/EXP-022 substrate rows whose production-path parity
was confirmed bar-by-bar by EXP-029 (CONSISTENT, all 5 binding gates). No new cTrader
run is required or performed: the cost layer is a deterministic arithmetic overlay on
already-validated realized positions, and adding constants to per-event returns has no
execution-path component to diverge. This statement is the scope-level execution-path
declaration that EXP-028 omitted; Stage 4 governance must check it against the
faithfulness clause below.

## Strategy Definition (unchanged from EXP-028/029 — faithfulness constraint)

Identical to EXP-028 `scope.md` §Strategy Definition in every component: MA 20/50
regime detector, typical-price AVWAP with `TickVolume ** 0.75` weights, MAD band
multiplier 1.0, EXP-020 bounce arm/trigger, EXP-022 band-target/trend-change exit,
pyramid bounces included as independent positions (per the corrected EXP-029
`AvwapBounceModel`), binding per-event return = EXP-022 own-exit lifetime return
(direction-signed log bps on real domain Close).

**The only addition is the cost layer.** No strategy parameter, event filter, exit
rule, or inclusion rule may change. No parameter is a tuning lever.

## Predeclared Cost Model (frozen before any net number is read)

### Structure

1. **Charging unit:** each **realized position** is charged one entry and one exit.
   Each pyramid bounce is an independent position (EXP-029-corrected semantics) and
   bears its own full round-trip cost. Nothing is amortized across pyramid legs.
2. **Per-side cost** `c_i` (one-way, bps of price) is a single per-instrument constant
   covering half-spread + per-side commission + per-side slippage.
3. **Round-trip cost** `RT_i = 2 × c_i`, subtracted from each event's lifetime return:
   `net_lifetime_bps = lifetime_bps − RT_i`.
4. **Slippage scaling decision (fixed):** slippage is **spread-scaled and folded into
   `c_i`**, NOT band-width/ATR-scaled. Rationale: market-order slippage is a
   microstructure quantity at the fill moment; domain-bar ATR and band width grow with
   timeframe while fill slippage does not, so an ATR-scaled model would invent
   precision the 1-minute OHLC dataset (no ticks, no bid/ask) cannot support. The
   conservative variant is the guard against understating it.
5. **Two predeclared variants; CONSERVATIVE is binding.** BASE is reported as a
   diagnostic in all cases and never decides the verdict. No third variant may be
   computed, and neither table may be revised after any net result is read.

### Cost table (operator-declared constants)

The dataset carries no bid/ask, so these values **cannot be derived from data**. They
are operator-declared constants sourced from typical published cTrader retail CFD
all-in costs (raw-spread account: spread + commission; slippage allowance included),
stated in bps of price. **Stage 4 governance must obtain explicit operator
confirmation (or replacement) of this table before APPROVE** — after approval it is
frozen.

| Instrument | `c_i` one-way (bps) | BASE round trip (bps) | CONSERVATIVE round trip = 2× BASE (bps) |
|------------|--------------------:|----------------------:|----------------------------------------:|
| EURUSD | 0.75 | 1.5 | 3.0 |
| USTEC | 1.25 | 2.5 | 5.0 |
| XAUUSD | 1.50 | 3.0 | 6.0 |
| BTCUSD | 4.00 | 8.0 | 16.0 |

### Estimand and denominators (fixed before implementation)

- **Binding net metric — net per-event expectancy (absolute):**
  `mean(net_lifetime_bps)` per instrument (event-weighted), then equal-weight mean
  across reportable instruments per domain (identical aggregation to EXP-028 PRIMARY).
  Tradability is an absolute-P&L question: matched controls are counterfactual
  benchmarks, not traded, so the deployable quantity is the event leg net of its own
  costs. (EXP-024's retained finding — the edge is relative-not-absolute on 5m — makes
  this a real, not formal, distinction; a 5m net-negative is an expected outcome.)
- **Attribution companion — net matched-control excess (non-binding):**
  `(lifetime_bps − RT_i) − mean(control_lifetime_bps)` = EXP-028 gross excess shifted
  by `RT_i`, with controls uncosted. Reported per domain for continuity with Phase 006;
  never decides the verdict.
- **Break-even diagnostic (descriptive only):** per instrument×domain, the round-trip
  cost level at which net expectancy crosses zero (= gross per-event expectancy). A
  table, not a gate; computed from gross quantities so it cannot motivate cost-model
  revision.
- **Zero-baseline rule:** all effects reported in bps per event with CIs. No
  percentage-improvement-vs-zero-baseline metrics anywhere.
- **Units guard:** `lifetime_bps` is `10000 × direction × ln(exit/entry)`; `RT_i` is
  in the same bps units and is subtracted directly.

### Inference (frozen machinery, predeclared)

- 95% regime-cluster bootstrap CI on net per-event expectancy (1000 resamples,
  `regime_id` clusters within instrument×direction strata — the frozen EXP-027/028
  bootstrap unchanged; subtracting per-instrument constants commutes with cluster
  resampling).
- One-sided bootstrap p-value for `net expectancy > 0`, Holm-adjusted across the
  3 domains; α₀ = 0.05.
- The stratified sign-permutation leg of the EXP-027 method is **not applicable** to
  the absolute net estimand (no symmetric paired null) and is deliberately not used as
  a binding test here; the binding inference is the bootstrap CI + Holm. The EXP-028
  gross PRIMARY (which carries the permutation-exact significance) is the already-read
  upstream result this experiment conditions on. Stage 2 may refine the p-value
  mechanics but may not weaken the CI_low > 0 requirement.
- Reportability thresholds identical to EXP-028: ≥30 events/domain, ≥8 per direction,
  ≥3 of 4 instruments; fixed seeds; determinism replay check.

## Scope Boundaries

- **Data Views**:
  - Per-event lifetime outcomes: `python/experiments/EXP-022/results/lifetime_observations.csv`
    (`role=event` rows — the EXP-028 PRIMARY event set, pyramids included; `role=control`
    rows for the non-binding attribution companion).
  - Event/pyramid metadata: `python/experiments/EXP-020/results/avwap_events.csv`.
  - Regime scaffolding for the bootstrap strata: EXP-020 state summary, as in EXP-028.
  - Real 5m/1h/4h domain bars rebuilt from the first-70% slice of 1-minute time bars
    (`xen.bar_aggregator`) only if needed for the equity companion; no chart-type views.
- **Candidate family / registry**: `CF-AVWAP-001/HYP-004-T` — cost-bearing tradability
  screen of the registered HYP-004-R baseline. Registered in the Phase 007 batch of
  `docs/signal-registry/multiplicity-registry.md`. Consumes **0** new candidate-family
  slots (added cost layer on an already-screened baseline).
- **Parameters**: domains 5m (strict) / 1h / 4h (`min_coverage = 0.90`); instruments
  BTCUSD, EURUSD, USTEC, XAUUSD; cost table above; α₀ = 0.05, α grid {0.10, 0.05, 0.01}
  reported descriptively; 1000 bootstrap resamples; Holm across 3 domains; fixed seeds.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis
  set; final 30% = global holdout, never used.
- **Global holdout**: The final 30% of each chronologically ordered source file must
  not be loaded, inspected, emitted, plotted, counted, or used in any capacity. This
  experiment is analysis-set tradability only; holdout release is EXP-032, deferred
  and separately governed.
- **Look-ahead bias prevention**: All upstream events/exits were generated by the
  look-ahead-safe EXP-020/022 machinery (EXP-029-confirmed). The cost overlay uses
  only quantities known at position open/close. Temporal ordering by `CloseTime`;
  cross-view alignment by timestamp, never bar index.
- **Real-price outcome discipline**: All returns are direction-signed log returns on
  real domain `Close` prices. No synthetic chart prices in any role.
- **Exclusions**:
  - The frozen per-bar qualification suite and any per-bar MDE floor as the
    tradability vehicle (the EXP-023 trap — wrong activity envelope);
  - Any second look at the cost model: no alternative cost tables, no slippage-model
    variants beyond the two predeclared, no post-result cost re-selection (a
    net-negative result is a valid outcome, not permission to try another model);
  - Any strategy-parameter change, event filter, exit overlay, sweep, or tuning;
  - Stage-C branches, `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN`, HYP-001 (all carried, not
    worked);
  - Holdout release in any form (EXP-032 is out of this experiment and this phase);
  - Position sizing, leverage, financing/swap costs, and portfolio construction
    (per-event expectancy only; financing is duration-dependent and would require a
    separately scoped model — recorded as a stated limitation, not silently included);
  - Percentage improvement against zero baselines.

## Success / Failure Criteria

All verdicts bind on the **CONSERVATIVE** cost variant and the **binding net metric**
(net per-event expectancy). BASE-variant and attribution-companion results annotate
but never decide.

- **Evidence FOR — TRADABLE** (per domain; phase outcome TRADABLE if ≥1 domain):
  net per-event expectancy > 0 AND bootstrap CI_low > 0 AND Holm-adjusted one-sided
  p ≤ 0.05, under CONSERVATIVE costs, on a reportable domain. Consequence: the
  holdout-release checkpoint (EXP-032) becomes admissible (its own governance; a
  thin-n domain such as 4h, n≈187, must be weighed there).
- **Evidence AGAINST — NOT_TRADABLE** (phase outcome): every reportable domain has
  CONSERVATIVE net expectancy ≤ 0, or a CI excluding a material positive net effect,
  with adequate in-experiment power (CI half-width and event counts; the EXP-027
  numeric MDE is not the lifetime power threshold — same bound as EXP-028).
  Consequence: no holdout release; family review / Stage-C / HYP-001 pivot per design
  §9. A 5m-only failure with 1h/4h passing is TRADABLE, not NOT_TRADABLE.
- **Inconclusive**: no domain reaches FOR, but power limitations or a BASE/CONSERVATIVE
  straddle (BASE clearly positive, CONSERVATIVE CI spanning 0) prevent a clean AGAINST.
  Reported as INCONCLUSIVE with the straddle stated; this does not authorize a third
  cost variant.

## Complexity Budget

- Max statistical tests: **3** (regime-cluster bootstrap CI + Holm on the binding net
  metric; the same machinery re-run for the BASE diagnostic; attribution-companion
  shift check — reuses test 1's machinery).
- Max visualisations: **4** (per-domain net expectancy with CIs, BASE vs CONSERVATIVE;
  gross→net waterfall per domain/instrument; break-even cost table heatmap; verdict
  summary).
- Max new code modules: **1** experiment-local script
  `python/experiments/EXP-030/code/run_experiment.py`. Reuse the frozen EXP-027/028
  bootstrap machinery by import or unchanged copy. No new or modified shared
  `python/src/xen/` module.

## Data Requirements

### Required Upstream Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| EXP-028 verdict | `python/experiments/EXP-028/results/run_metadata.json` | Dependency gate: must be EVAL_SUPPORTED |
| EXP-029 parity | `python/experiments/EXP-029/results/run_metadata.json` | Dependency gate: must be CONSISTENT (cTrader-confirmed) |
| EXP-022 lifetime observations | `python/experiments/EXP-022/results/lifetime_observations.csv` | Per-event/control lifetime returns |
| EXP-020 AVWAP events | `python/experiments/EXP-020/results/avwap_events.csv` | Event/pyramid metadata, regime scaffolding |
| EXP-020 state summary | `python/experiments/EXP-020/results/avwap_state_summary.csv` | Bootstrap cluster strata |
| EXP-027/028 inference code | `python/experiments/EXP-027/code/event_method.py` (and EXP-028 reuse) | Frozen bootstrap machinery, unchanged |
| 1-minute time bars | `data/timebars/timebars_*.parquet` | Domain bars for the equity companion only |

### Anti-Overfitting / No-Tuning Fence

The cost table, charging rules, estimand, decision rule, and inference settings are
fixed by this scope (pending the single Stage 4 operator confirmation of the cost
table) **before any net number is computed**. The experiment reads the net results
once. No cost value, variant, metric, or threshold may be changed afterward.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

### Expected Output Files

```
python/experiments/EXP-030/results/
- net_expectancy_results.csv     # per-domain net effect (BASE + CONSERVATIVE), CI, Holm-p, verdict
- net_by_instrument.csv          # instrument-level net expectancy and break-even table
- attribution_companion.csv      # net matched-control excess (non-binding)
- run_metadata.json              # status, dependencies, cost table hash, verdict, seeds
python/experiments/EXP-030/plots/
- net_expectancy.png             # per-domain net effect with CIs, both variants
- gross_to_net_waterfall.png     # gross → cost → net per domain/instrument
- breakeven_heatmap.png          # break-even RT cost per instrument×domain
- verdict_summary.png            # headline verdict per domain
```

## Suggested Direction

Load EXP-022 `lifetime_observations.csv` (`role=event`), join the per-instrument
CONSERVATIVE/BASE round-trip costs, subtract per event, and push the net per-event
series through the frozen regime-cluster bootstrap aggregation exactly as EXP-028's
PRIMARY (instrument event-weighted mean → equal-weight domain mean), with a one-sided
bootstrap p and Holm across domains. Compute the attribution companion as the EXP-028
gross excess shifted by `RT_i`. Expect 5m to be the stress case (+5.78 bps gross vs
3–16 bps conservative round trips) and treat a 5m net-negative as informative, not as
failure. No second cost model, ever.
