# Experiment: EXP-033 — TRAIN-Only Horizon Sweep: Attribution Crossover and FH(H) Net Curve

**Registry ID:** `CF-AVWAP-001/DIAG-004` (diagnostic; 0 candidate slots).
**Phase:** 008 (`docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`, §5/A2).
**Depends on:** EXP-031 (method + event population), EXP-030 (frozen cost model),
EXP-027 (frozen inference tail), D0 memo (instrument-set choice for H\*).

## Hypothesis

Exploratory (diagnostic — no candidate verdict). Two predeclared questions:

1. **Attribution:** how does the entry share s_entry(H) = X_entry(H)/X_full of the
   EXP-028 per-event matched-control excess evolve over H ∈ {1, 2, 3, 4, 6, 8, 12, 24}
   domain bars, per domain, on TRAIN? Where is the crossover (s_entry = 0.5), and does
   attribution stabilize beyond it?
2. **Capture efficiency:** what is the TRAIN per-event **absolute net** expectancy of
   the FH(H)-exit variant (entry and pyramids unchanged; exit replaced by a fixed
   H-bar horizon) at each H, per domain — and what H\*_d and pyramid policy do the
   predeclared mechanical rules select for EXP-037 (B2)?

## Question

At what evaluation horizon does the AVWAP edge shift from exit-driven to
entry-driven, and is there a fixed-horizon exit that makes the strategy's absolute
net expectancy positive on TRAIN?

## Scope Boundaries

- **Data Views**: EXP-022 `results/lifetime_observations.csv` (event + control rows;
  the EXP-028 PRIMARY population); EXP-020 `results/avwap_events.csv` (trigger
  timestamps via join on instrument/domain/regime_id/trigger index); rebuilt 5m/1h/4h
  OHLC domain series from 1-minute time bars via `xen.bar_aggregator` (identical
  rebuild to EXP-031 — same parameters, deterministic).
- **Parameters**: horizon grid H ∈ {1, 2, 3, 4, 6, 8, 12, 24} domain bars (LOCKED);
  frozen EXP-030 CONSERVATIVE round-trip costs (EURUSD 3.0 / USTEC 5.0 / XAUUSD 6.0 /
  BTCUSD 16.0 bps); predeclared financing rates (EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 /
  BTCUSD 10.0 bps per calendar day, adverse-side); frozen EXP-027 inference
  (regime-cluster bootstrap, 1000 resamples; stratified sign-permutation for
  matched-control legs; pinned hash `e50873d12a9f68d9`).
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for all attribution and disclosure
  outputs. **H\*-selection objective uses the equal-weight mean over EURUSD, USTEC,
  XAUUSD only (BTCUSD excluded — D0 §4, data-dependent choice, recorded).**
- **Time range**: full dataset with nested chronological split. First 70% = analysis
  set; **this experiment reads TRAIN only = first 70% of the analysis set** (cutoff at
  70% of analysis-set domain bars per instrument/domain, by `CloseTime`).
  **TRAIN-window containment rule (amended 2026-06-10, F08, pre-execution):** an
  event/control row is included iff (a) its trigger bar index plus the maximum
  horizon (24 bars) lies at or before the TRAIN cutoff index, **and** (b) its BTC
  lifetime `completion_idx` lies at or before the TRAIN cutoff index. Clause (b) is
  a predeclared correction to the originally locked rule, which omitted it: the BTC
  lifetime is also an outcome, and a lifetime completing past the TRAIN boundary
  would leak TEST prices into the X_full leg (EXP-035's scope already carries the
  equivalent clause). No outcome window may read a bar past the TRAIN boundary.
  Excluded-row counts are disclosed per domain and clause.
- **Global holdout**: the final 30% of the full dataset must not be loaded, inspected,
  or used in any capacity. The TEST segment (last 30% of the analysis set) must also
  not be read by this experiment.
- **Look-ahead bias prevention**: all outcomes use bars strictly after the trigger
  bar, within the H-bar window; all event covariates are known at trigger time;
  domain bars order by `CloseTime`.
- **Real-price outcome discipline**: all returns from real OHLC domain `Close`; no
  synthetic prices in scope.
- **Exclusions**: no TEST or holdout reads; no change to entry logic, bounce
  definition, costs, or the frozen inference; no stratum/conditioning analysis
  (EXP-035's scope); no candidate verdict — outputs are a diagnostic map plus two
  mechanically-frozen selections for B2.

## Predeclared mechanical selection rules (LOCKED — no discretion at read time)

1. **H\*_d (per domain):** on the TRAIN FH(H) net curve (equal-weight over
   EURUSD/USTEC/XAUUSD), H\*_d = the **smallest** H whose net is within one bootstrap
   SE of the grid maximum. If the grid maximum ≤ 0 for domain d, **B2 does not run on
   d** (record `B2_ELIGIBLE_d = false`).
2. **Pyramid policy (per eligible domain):** at H\*_d, compute TRAIN net under
   {all-legs, first-leg-only, pyramid-legs-only}. Select the **first** policy in that
   preference order whose net is within one bootstrap SE of the best policy's net.
3. Both selections are emitted to `results/b2_selection.json` and freeze on emission;
   EXP-037 consumes them verbatim.
4. **Selection-stability disclosure (added 2026-06-10, F07, pre-execution):** a
   chronological split-half check (per-domain median trigger time; point-estimate
   curves per half; the full-TRAIN bootstrap SE as the comparison scale) records
   `eligibility_stable` / `h_star_stable` / `policy_stable` flags per eligible
   domain in `b2_selection.json`. **Disclosure only** — it does not alter the
   mechanical selection; it exists so the EXP-037 scope and Stage-4 governance can
   weigh selection fragility on power-thin domains (4h especially) before a Tier-B
   slot is spent.

## Definitions

- **FH(H) absolute net return (event e, instrument i):**
  `net_e(H) = fh_return_bps(e, H) − RT_cons_i − financing_i(e, H)` where
  `fh_return_bps` is the direction-signed Close-to-Close return from the trigger bar
  close to the close H domain bars later, and
  `financing_i(e, H) = rate_i × elapsed_calendar_days(trigger_close_time,
  close_time_at(trigger_idx + H))` (fractional days from rebuilt-series timestamps —
  includes weekends/closures, which is both more accurate and more conservative than
  bar-count approximation).
- **Attribution legs at H:** X_full (BTC exit), X_entry (FH(H) exit), X_exit =
  X_full − X_entry, all matched-control-differenced on the common-control
  intersection per the EXP-031 method, gross (no costs — attribution is a gross
  decomposition; costs enter only the FH net curve above).
- **Denominators / zero-baseline:** per-instrument means are event-weighted over
  included TRAIN events; domain values are equal-weight cross-instrument means (4 for
  attribution/disclosure, 3 for the H\* objective). A cell with fewer than 30 (5m/1h)
  or 15 (4h) included events per instrument is marked `unreportable` and excluded
  from the equal-weight mean with disclosure. s_entry is reported only where
  |X_full| > its bootstrap SE (otherwise the share is ill-defined; report legs, not
  the ratio).

## Success / Failure Criteria

Diagnostic — the outcome classes are about measurement delivery, not edge:

- **MEASUREMENT_COMPLETE**: all reportable domains have CIs on all legs at all H;
  crossover characterization delivered (crossover location or "none in grid");
  `b2_selection.json` emitted with H\*_d + pyramid policy or `B2_ELIGIBLE = false`
  per domain.
- **PARTIAL**: ≥1 domain unreportable after the containment rule (expected risk: 4h,
  where TRAIN ≈ 130 events minus 24-bar exclusions); deliver remaining domains and
  disclose.
- **Inconclusive**: inference tail fails its hash pin or determinism replay — hard
  stop, no selection emitted.

## Complexity Budget

- Max statistical test families: 2 (regime-cluster bootstrap CIs; stratified
  sign-permutation for matched-control legs).
- Max visualisations: 4 (s_entry(H) per domain; FH(H) net curve per domain with
  one-SE band and H\* markers; decomposition stacked bars at H\*; pyramid-policy
  comparison at H\*).
- Max new code modules: 1 (extend/reuse EXP-031 `event_method.py`; one orchestration
  script).

## Data Requirements

Join EXP-022 lifetime observations to EXP-020 events for trigger timestamps; rebuild
domain series exactly as EXP-031 (assert per-domain bar-count equality with EXP-031
run metadata as a reconciliation guard). Reconciliation gates before any sweep
output: at H ∈ {1, 6}, X_full/X_entry/X_exit must reproduce EXP-031's TRAIN-subset
values recomputed under the containment rule — exact for X_full's event set
identity, and the H ∈ {1,6} legs on the full analysis set must reproduce EXP-031's
published numbers to ≤ 0.01 bps when the containment rule is relaxed to EXP-031's
inclusion rule (one-time check, then TRAIN-only thereafter).

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
# TRAIN = first 70% of the rebuilt domain-bar series; TEST never read here.
```

## Suggested Direction

Vectorize the FH(H) return computation as a single shifted-Close join over the
rebuilt series per instrument/domain (one pass for all H), then reuse the EXP-031
matched-control differencing on the precomputed per-event FH returns. `tqdm` over
instrument × domain. The bootstrap can resample event indices once per domain and
evaluate all H columns simultaneously to keep resampling consistent across the grid
(this also makes the one-SE band internally coherent).
