# Experiment: EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)

## Hypothesis

This is a **diagnostic decomposition**, not a single falsifiable edge claim and not a
qualification screen. Predeclared exploratory question, per domain:

Of the EXP-028 measured per-event matched-control excess (+5.78 / +23.38 / +69.02 bps
on 5m / 1h / 4h, PRIMARY EVIDENCE_FOR), how much is attributable to **AVWAP bounce
entry timing** versus the **EXP-022 band-target/trend-change exit rule**? The verdict
is a per-domain attribution label — ENTRY_DOMINANT / EXIT_DOMINANT / MIXED /
INCONCLUSIVE — under a predeclared, sign-complete classification rule.

## Question

The EXP-028 PRIMARY excess differences an event leg and a matched-control leg that
**both use the band-target/trend-change (BTC) exit** — so the exit rule is held
constant inside that contrast and the measured number is entry-timing *as expressed
through the BTC exit*. To learn where the edge actually lives, we re-express the same
events and controls under a **neutral fixed-horizon exit** and ask: how much of the
excess survives a neutral exit (entry-timing edge), and how much is the BTC exit's
*differential* value on bounce-entered positions beyond control-entered ones
(exit-rule edge)? This supersedes the discounted EXP-024 fork-(b) leg (which compared
a per-event hold to a per-bar floor — a category mismatch) with a same-pairs
matched-excess construction.

## Relationship to phase gating (design §3)

EXP-031 is **mutually independent** of EXP-030 (tradability). It does not gate, and is
not gated by, the cost result, and is **not cancelled** by an EXP-030 failure
(operator decision 2026-06-09): the entry/exit mechanism read informs future scopes
regardless of whether this specific candidate survives costs. Registered as
`CF-AVWAP-001/DIAG-003` (diagnostic, **0** candidate-screening slots) in the Phase 007
batch of `docs/signal-registry/multiplicity-registry.md`.

## Execution Path (named explicitly, per Phase 006 lesson 1)

**Python re-analysis of the cTrader-confirmed upstream artifacts**, identical class to
EXP-024/028. The event/control set and BTC lifetime returns are the EXP-020/EXP-022
substrate (production-path parity confirmed by EXP-029). The only added computation is
a **deterministic fixed-horizon return recompute on the same `start_idx` bars** within
the analysis set — no new cTrader run, no new event/exit logic. This statement is the
scope-level execution-path declaration Stage 4 governance must check against the
faithfulness clause.

## Decomposition Construction (predeclared, frozen before reading results)

For every EXP-022 `lifetime_observations.csv` row (both `role=event` and
`role=control`, pyramids included — the exact EXP-028 PRIMARY population), each row
carries a `start_idx`, `start_close`, `direction`, and its BTC lifetime return
`lifetime_bps`. On the **same** `start_idx`, compute a neutral fixed-horizon return
from the rebuilt domain Close series (deterministic, as EXP-024 rebuilt domains):

```
fh_bps(row, H) = 10000 * direction * ln( close[start_idx + H] / start_close )
```

reportable only when `start_idx + H` lies inside the first-70% analysis slice.

Three per-event paired quantities, all matched-control–differenced over each event's
own controls (identical aggregation to EXP-028 PRIMARY: per-instrument event-weighted
mean → equal-weight mean across reportable instruments per domain):

| Leg | Per-event quantity | Meaning |
|-----|--------------------|---------|
| **X_full** | `event_BTC − mean_c(control_BTC)` | The full strategy excess. **Reproduces the EXP-028 PRIMARY exactly** (validation anchor: must match EXP-028 within numerical tolerance). |
| **X_entry(H)** | `event_FH(H) − mean_c(control_FH(H))` | Entry-timing edge under a **neutral** fixed-horizon exit (exit rule neutralized — same fixed horizon on both legs). |
| **X_exit(H)** | `X_full − X_entry(H)` | Exit-rule's **differential** contribution = (event's BTC-minus-FH exit-substitution effect) − (controls' mean exit-substitution effect). |

By construction `X_full = X_entry(H) + X_exit(H)` per event, so the decomposition is
**additive and exhaustive** — no residual term is hidden.

**Why a neutral fixed-horizon exit is the right control exit:** it is the
already-frozen EXP-027 secondary-stability comparator (no new method object), it
carries no AVWAP/band information (so it cannot smuggle the exit rule's logic into the
"entry" leg), and it is computed on the identical (event, control) pairs so the only
varied factor is the exit. The frozen horizons are `H ∈ {1, 6}` (the EXP-027
secondary-horizon slots). **H = 6 is the predeclared PRIMARY** neutral exit; **H = 1
is a predeclared robustness companion** — both are reported, neither is selected from
results. Reporting both is a sensitivity check, not a sweep: a classification that
flips between H = 1 and H = 6 is itself a reported finding (pushes toward MIXED), not
grounds to pick the favorable horizon.

## Frozen Inference (EXP-027 tail, unchanged)

Each leg's per-event paired series is pushed through the frozen EXP-027/028 inference:

- 95% regime-cluster bootstrap CI (1000 resamples, `regime_id` clusters within
  instrument×direction strata) — unchanged machinery.
- Stratified paired sign-permutation one-sided p-value (1000 resamples). For X_full
  and X_entry the null is the symmetric matched-control mean-zero null (as
  EXP-028/EXP-021). For X_exit the null is "the BTC exit's incremental value is the
  same on bounce-entries and control-entries" — sign-permutation on the per-event
  paired exit-substitution differences (exact under that exchangeability; stated as
  the leg's assumption).
- Holm adjustment of leg p-values within the {entry, exit} × {reportable domains}
  family; X_full significance reproduces EXP-028's Holm-across-3-domains claim.
- α₀ = 0.05; reportability identical to EXP-028 (≥30 events/domain, ≥8/direction,
  ≥3 of 4 instruments; Wilson/CI half-width precision gates); fixed seeds; determinism
  replay check. A leg is **leg-significant** iff bootstrap `CI_low > 0` **and**
  Holm-adjusted sign-permutation `p ≤ 0.05` (the EXP-028 dual requirement).

## Predeclared Attribution Rule (sign-complete; frozen before results)

Per domain, evaluated at the PRIMARY neutral horizon **H = 6**, **only when X_full is
Evidence-FOR on that domain** (CI_low > 0 AND Holm p ≤ 0.05 — i.e. there is a real
total to attribute). Let `s_entry = X_entry / X_full`, `s_exit = X_exit / X_full`
(`s_entry + s_exit = 1`). The rule covers every sign/significance combination so there
is **zero post-hoc latitude**:

| Condition (evaluated in order) | Label |
|--------------------------------|-------|
| X_full CI_low ≤ 0 or below reportable power | **INCONCLUSIVE** (no significant total to attribute) |
| X_entry leg-significant AND X_exit leg-significant AND s_entry ≥ 0.67 | **ENTRY_DOMINANT** |
| X_entry leg-significant AND X_exit leg-significant AND s_exit ≥ 0.67 | **EXIT_DOMINANT** |
| X_entry leg-significant AND X_exit leg-significant AND max(s_entry, s_exit) < 0.67 | **MIXED** |
| Only X_entry leg-significant (X_exit CI includes 0) | **ENTRY_DOMINANT** (exit contribution indistinguishable from 0) |
| Only X_exit leg-significant (X_entry CI includes 0) | **EXIT_DOMINANT** (entry contribution indistinguishable from 0) |
| X_entry < 0 (entry edge negative under neutral exit; exit carries > 100%) | **EXIT_DOMINANT** (note: entry leg negative — BTC exit creates the differential edge) |
| X_exit < 0 (BTC exit is a net drag on the differential; entry carries > 100%) | **ENTRY_DOMINANT** (note: exit rule is a differential drag) |
| Neither leg leg-significant though X_full is FOR | **MIXED_UNRESOLVED** (real total, split below this experiment's resolution) |

The 0.67 (two-thirds) dominance cut is a predeclared convention, fixed before any leg
result is read.

## Scope Boundaries

- **Data Views**:
  - Per-event/control lifetime rows: `python/experiments/EXP-022/results/lifetime_observations.csv`
    (`role ∈ {event, control}`, pyramids included — the EXP-028 PRIMARY population).
  - Event metadata / regime scaffolding: `python/experiments/EXP-020/results/avwap_events.csv`,
    `avwap_state_summary.csv` (bootstrap strata).
  - Rebuilt real 5m/1h/4h domain Close series from the first-70% slice of 1-minute
    time bars (`xen.bar_aggregator`), reproducing EXP-020/022/024 domain construction
    exactly (verify domain row counts reproduce EXP-020 metadata before use). Used only
    for the fixed-horizon recompute. No chart-type views.
  - EXP-021 `reaction_observations.csv` — cross-check that X_entry at H ∈ {1,6}
    reconciles with the EXP-021 fixed-horizon reaction excess (sanity anchor, not a
    binding gate).
- **Candidate family / registry**: `CF-AVWAP-001/DIAG-003`, diagnostic, **0** slots.
  Registered in the Phase 007 batch.
- **Parameters**: domains 5m (strict) / 1h / 4h (`min_coverage = 0.90`); instruments
  BTCUSD, EURUSD, USTEC, XAUUSD; neutral exit horizons `H ∈ {1, 6}` (H=6 primary);
  dominance cut 0.67; α₀ = 0.05; 1000 bootstrap + 1000 permutation resamples; Holm as
  above; fixed seeds.
- **Primary domain (predeclared, for resolution):** **5m** — largest reportable event
  count (best decomposition resolution), consistent with EXP-024's primary choice. All
  three domains are reported in full; a **cross-domain divergence in the entry/exit
  split is itself a reportable finding**, never averaged away or reconciled to a single
  number.
- **Time range**: Full dataset, nested chronological split. First 70% = analysis set;
  final 30% = global holdout, never used.
- **Global holdout**: The final 30% must not be loaded, inspected, emitted, plotted,
  counted, or used. Fixed-horizon returns use only analysis-set closes; an event/control
  with no real close at `start_idx + H` inside the analysis slice is **non-reportable
  at that horizon** (drops out of that horizon's N), never extended into the holdout.
- **Look-ahead bias prevention**: events/exits are the look-ahead-safe EXP-020/022
  machinery (EXP-029-confirmed); fixed-horizon returns use only closes at or after the
  start bar up to the evaluated horizon; targets/AVWAP frozen at trigger; no future
  information selects horizons (fixed a priori). Temporal ordering by `CloseTime`;
  alignment by timestamp, never bar index.
- **Real-price outcome discipline**: all returns (BTC lifetime and fixed-horizon) are
  direction-signed log returns on **real domain Close** prices. No synthetic chart
  prices (HA, Renko, Line Break) in any role.
- **Exclusions**:
  - **Costs / slippage** — this is a gross mechanism decomposition; net tradability is
    EXP-030's separate question. Adding costs to both legs would shift levels without
    informing the entry/exit split. (Stated limitation, not an omission.)
  - The frozen per-bar qualification suite and any per-bar MDE floor (the EXP-023 trap);
  - Any horizon **sweep** beyond the two predeclared H values, any post-result horizon
    selection, any alternative neutral-exit definition chosen after seeing leg results;
  - Any strategy-parameter, detector, anchor, band, or alpha change; any exit-overlay
    *redesign* (this measures the existing exit's contribution, it does not design a
    new one — EXP-026 `/EXIT` remains shelved);
  - HYP-001 (line S/R), Stage-C branches, `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN`
    (carried, not worked);
  - Holdout release (EXP-032, deferred, separate governance);
  - Percentage-improvement-against-zero-baseline metrics (the shares s_entry/s_exit are
    ratios of a leg to the **significant, nonzero** X_full total — only computed when
    X_full CI_low > 0, so no division by a near-zero or zero baseline).

## Success / Failure Criteria

The "result" is the per-domain attribution label under the predeclared rule. There is
no SUPPORTED/REFUTED edge verdict — EXP-031 cannot fail in the edge sense (it
decomposes an already-established excess), but it **can be inconclusive** (the
falsifiable content is whether the split resolves):

- **ISOLATION_READ — resolved**: at least the primary domain (5m) yields a definite
  label (ENTRY_DOMINANT, EXIT_DOMINANT, or MIXED) under the rule, with the H=1
  robustness companion not contradicting the H=6 classification. Phase outcome
  ISOLATION_READ delivered; feeds future-scope design (e.g., an EXIT_DOMINANT read
  argues an exit-overlay branch carries the edge; an ENTRY_DOMINANT read argues the
  bounce-entry detector does).
- **ISOLATION_READ — unresolved / INCONCLUSIVE**: the primary domain returns
  INCONCLUSIVE or MIXED_UNRESOLVED, or H=1 and H=6 give contradictory labels. Reported
  honestly as "edge present but split not resolved at this power/construction"; **does
  not authorize** a new horizon, a new neutral-exit definition, or a re-run with
  different legs.
- **Validation anchor (must hold or the experiment is REVISE-blocked):** X_full must
  reproduce the EXP-028 PRIMARY effects within numerical tolerance on all three
  domains. If it does not, the decomposition substrate is mis-wired and no attribution
  is read until it reconciles.

## Complexity Budget

- Max statistical tests: **3** (the three legs X_full / X_entry / X_exit through the
  shared frozen bootstrap + sign-permutation + Holm machinery; X_full reuses EXP-028's,
  X_entry largely reuses EXP-021's). The attribution rule is a predeclared threshold
  classifier, not an additional NHST.
- Max visualisations: **4**
  1. Per-domain stacked decomposition: X_full = X_entry + X_exit with CIs, at H=6
     (primary) and H=1 (companion).
  2. Per-domain s_entry / s_exit shares with the 0.67 dominance band marked.
  3. Exit-substitution effect (BTC − fixed-horizon) for event vs control legs, per
     domain — the mechanism behind X_exit (reconciles with EXP-024's "exit cuts
     losers" finding).
  4. Attribution summary dashboard (per-domain labels, H=6 vs H=1 agreement).
- Max new code modules: **1** experiment-local script
  `python/experiments/EXP-031/code/run_experiment.py`. Reuse the frozen EXP-027/028
  inference machinery by import or unchanged copy, and the EXP-024-style fixed-horizon
  grid helper. No new or modified shared `python/src/xen/` module.

## Data Requirements

### Required Upstream Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| EXP-028 verdict + effects | `python/experiments/EXP-028/results/run_metadata.json`, `event_level_results.csv` | Dependency gate (EVAL_SUPPORTED); X_full reconciliation anchor |
| EXP-029 parity | `python/experiments/EXP-029/results/run_metadata.json` | Dependency gate (CONSISTENT / cTrader-confirmed) |
| EXP-022 lifetime observations | `python/experiments/EXP-022/results/lifetime_observations.csv` | Event/control rows, `start_idx`, BTC `lifetime_bps` |
| EXP-020 events + state summary | `python/experiments/EXP-020/results/avwap_events.csv`, `avwap_state_summary.csv` | Event metadata, regime strata |
| EXP-021 reaction observations | `python/experiments/EXP-021/results/reaction_observations.csv` | X_entry sanity reconciliation at H ∈ {1,6} |
| EXP-027/028 inference code | `python/experiments/EXP-027/code/event_method.py` (+ EXP-028 reuse) | Frozen bootstrap/permutation/Holm machinery |
| 1-minute time bars | `data/timebars/timebars_*.parquet` | Domain Close rebuild for fixed-horizon recompute |

### Anti-Overfitting / No-Tuning Fence

The legs, neutral horizons {1,6}, primary horizon (6), dominance cut (0.67),
classification rule, and inference settings are all fixed by this scope **before any
leg result is read**. The experiment reads leg results once and applies the frozen
classifier. No horizon, neutral-exit definition, threshold, or leg may be changed,
added, or reselected afterward.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()  # holdout never loaded
```

### Expected Output Files

```
python/experiments/EXP-031/results/
- decomposition_results.csv      # per-domain X_full / X_entry / X_exit, CIs, Holm-p, shares, label (H=6 and H=1)
- decomposition_by_instrument.csv# instrument-level leg effects
- xfull_reconciliation.csv       # X_full vs EXP-028 PRIMARY, numerical-tolerance check
- run_metadata.json              # status, dependencies, frozen-method hash, labels, seeds
python/experiments/EXP-031/plots/
- decomposition_stacked.png      # X_full = X_entry + X_exit, per domain, H=6 & H=1
- attribution_shares.png         # s_entry / s_exit with 0.67 dominance band
- exit_substitution.png          # event vs control BTC-minus-FH effect per domain
- attribution_summary.png        # per-domain labels and H-agreement
```

## Suggested Direction

Load EXP-022 `lifetime_observations.csv` (events + controls), rebuild the domain Close
series (verify against EXP-020 metadata), compute `fh_bps` at H ∈ {1,6} on each row's
`start_idx`, and form the three matched-control–differenced legs per event. Push each
leg through the frozen EXP-027 inference tail with the EXP-028 aggregation. First
reconcile X_full against EXP-028's PRIMARY (hard anchor). Then apply the predeclared
sign-complete classifier per domain at H=6, report H=1 as robustness, and read the
per-domain attribution — reporting any cross-domain divergence as a finding. No
horizon sweep, no alternative neutral exit, no post-hoc leg reselection.
