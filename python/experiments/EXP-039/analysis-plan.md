# Analysis Plan: Experiment EXP-039

## Objective

Measure, on the TRAIN stratum only, the per-event **net** expectancy (frozen
EXP-030 CONSERVATIVE costs + Phase 008 financing) of each registered candidate
exit rule (E1–E5, with E3/E5 parameter grids) on the unchanged AVWAP
bounce-entry substrate, and apply the predeclared mechanical qualification rule
(design §8.1) against the reference exits R-BTC and R-FH(12). The deliverable
is a qualification table and a frozen qualifying set (≤2 exits total) for the
provisional EXP-041 one-shot TEST confirmation — **no market-edge verdict, no
binding hypothesis test, no TEST read**.

## Frozen vs. rebuilt components

| Reused unchanged | Rebuilt / defined here |
|---|---|
| Frozen EXP-027 tail: `build_strata` (cluster strata), `holm_adjust` (unused here, hash-guarded for lineage only) — `inspect.getsource` hash over named symbols, abort `FROZEN_INFERENCE_MODIFIED` on mismatch | Exit-rule library `xen.exit_rules` (E1–E5 + R-BTC + R-FH as pure per-event streaming functions) |
| EXP-020 AVWAP event substrate definition (MA 20/50, `TickVolume**0.75`, MAD ×1.0) — rebuilt deterministically, count-reconciled | Descriptive regime-cluster bootstrap with **event-weighted pooled aggregator** (scope-binding pooling; see Step 5 note) |
| EXP-030 cost constants (RT_cons per instrument) + Phase 008 financing rates and day-count convention (EXP-037 form: adverse-side daily rate × fractional calendar days, entry-confirmation close → exit close) | Containment/intersection population logic (Step 3) |

The binding screen statistics use a **different pooled aggregator** than the
frozen `domain_effect` (which equal-weights instruments): the scope predeclares
event-weighted pooling over the surviving instruments. Because EXP-039 carries
no binding inference, this is a descriptive-statistic definition, not a
modification of the frozen suite; the frozen-style equal-weight aggregate is
also reported as a cross-check column so the two pooling conventions are both
visible.

## Methodology

### Step 1 — Dependency gate and reconciliation anchors (before any candidate read)

- **Method**, all hard-fail on miss:
  1. Frozen-tail source-hash guard (named symbols, EXP-030 convention).
  2. Rebuilt 1h/4h domain-bar counts on the analysis set == EXP-020
     `run_metadata.json` counts, exact.
  3. **R-BTC per-event reconciliation:** the rebuilt substrate + R-BTC exit
     simulation, restricted to TRAIN (trigger close ≤ `train_end_ts`, R1.3
     convention), must reproduce EXP-022 `lifetime_observations.csv`
     `lifetime_bps` event-by-event (join on instrument, domain, trigger
     timestamp; tolerance ≤ 0.01 bps; count match exact).
  4. **R-FH(12) reconciliation (4h):** contained-TRAIN FH(12) all_legs net per
     instrument must reproduce the EXP-033 FH-curve artifacts (and the EXP-037
     freeze values) within ≤ 0.01 bps.
- **Why**: EXP-039 must rebuild the substrate (new exits need bar-level
  simulation, unlike EXP-030's pure overlay); event-level reconciliation
  against two independent validated artifacts proves the rebuild before any
  new number exists. This is the scope's reference reproduction guard.
- **Simpler alternative considered**: aggregate-level reconciliation only.
  Rejected — per-event join catches alignment bugs aggregates can hide
  (the EXP-027 lesson).
- **Assumptions**: EXP-022 CSV and EXP-033/037 artifacts are immutable
  post-verdict; `train_end_ts` from the shared loader convention.
- **Expected output**: `results/reconciliation.csv` + flags in
  `run_metadata.json`.

### Step 2 — Exit simulation over the shared TRAIN substrate

- **Method**: generate the event substrate once per instrument×domain on TRAIN
  (sequential streaming pass; entries, pyramids, all_legs policy identical to
  EXP-028/030). For each of the 13 exit evaluations (E1, E2, E3×{3,5,8}, E4,
  E5×{8,12,24}, R-BTC, R-FH(12) on 4h), resolve each event's exit
  **sequentially** under bar-close semantics: the exit fires at the first
  domain-bar close (strictly after the entry-confirmation close) satisfying
  its condition; fill price = that bar's real `Close`. Per event:
  `lifetime_bps = 10000 · direction · ln(exit/entry)`,
  `net = lifetime_bps − RT_cons,i − financing_i(holding_days)`.
  E4/E5 retain the band-target leg: exit = min(first target hit, first
  failure-leg fire). HA columns (E1/E2 triggers) come from
  `xen.heiken_ashi_generator` over the domain bars; HA values never enter
  prices.
- **Why**: one shared substrate guarantees every exit is evaluated on
  identical entries; sequential per-event resolution is the causally correct
  implementation for state-dependent exits (trailing references), and the
  scope's streaming-compatibility requirement for the future cTrader port.
- **Simpler alternative considered**: vectorized first-crossing search per
  exit. Permitted only where causally equivalent (fixed-level rules E3/E4/E5
  can use windowed vector scans); E1/E2 trailing state stays an explicit
  bounded loop.
- **Assumptions**: bar-close fills (scope-fixed); one round-trip charge per
  realized position including each pyramid leg; financing per the Phase 008
  convention.
- **Expected output**: tidy per-event table
  `(instrument, domain, exit_id, param, regime_id, direction,
  is_pyramid_bounce, trigger_ts, exit_ts, holding_days, lifetime_bps,
  net_bps, resolved_flag)`.

### Step 3 — Containment and intersection populations

- **Method**: per candidate, the **contained set** = events whose exit
  resolves at or before `train_end_ts`; unresolved-at-boundary events are
  excluded from selection with per-cell counts disclosed. All
  candidate-vs-reference gap statistics are computed on the **intersection
  population**: events contained under the candidate AND both applicable
  references (4h: R-BTC and R-FH(12); 1h: R-BTC), so every gap is a
  same-events comparison. Per-cell tables report both the own-contained and
  intersection sample sizes.
- **Why**: mirrors EXP-033's F08 containment (TEST-price-blind selection) and
  removes population-composition artifacts from the reference gaps — a
  slow-resolving exit must not look better merely by dropping different
  events.
- **Simpler alternative considered**: own-contained populations per exit.
  Rejected — gaps would mix exit effect with population effect.
- **Assumptions**: containment exclusion biases toward faster-resolving exits;
  accepted and disclosed (scope).
- **Expected output**: `results/containment_accounting.csv`.

### Step 4 — Within-grid parameter selection (E3, E5)

- **Method**: per domain, for each gridded exit, select one parameter point by
  **max-min worst-half net** (event-weighted pooled net over surviving
  instruments, computed separately on the two chronological TRAIN halves;
  pick the point whose worse half is best), tie → smaller parameter. Selection
  happens **before** any qualification comparison; the full grid is disclosed
  in tables and one plot.
- **Why**: the predeclared mechanical rule (design §5/A1); max-min directly
  targets the fragility the 4h event count creates (R1.4 lesson).
- **Simpler alternative considered**: argmax of full-TRAIN net. Rejected —
  selects fragile peaks on ~90-event cells.
- **Expected output**: `results/grid_selection.csv` (all points, both halves,
  selected flag).

### Step 5 — Qualification rule (design §8.1, mechanical)

- **Method**: per domain d, candidate E at its selected point qualifies iff
  (evaluation population pinned per criterion — scope §Mechanical Selection):
  - (i) per-instrument net point estimate > 0 for every surviving instrument
    (EURUSD, USTEC, XAUUSD on both domains; BTCUSD descriptive only),
    computed on the candidate's **own boundary-contained** population;
  - (ii) event-weighted pooled net (surviving instruments, **intersection
    population**) > the better reference (4h: max(R-FH(12), R-BTC); 1h: R-BTC)
    on the same events;
  - (iii) split-half stability: pooled net > 0 (**own-contained** population)
    AND sign(reference gap) (**intersection** population) constant across both
    chronological TRAIN halves.
  Cells with intersection n < 30 are descriptive-only and cannot qualify
  (reportability floor). Uncertainty context: descriptive 95% regime-cluster
  bootstrap CIs (resample `regime_id` clusters within instrument×direction
  strata via frozen `build_strata` structure, N_BOOT = 1000, event-weighted
  aggregator) attached to every pooled net and reference gap — **descriptive
  only, no p-values, no binding test**.
- **Why**: the rule is predeclared in the design; bootstrap CIs give honest
  scale context without converting a screen into a hypothesis test (the
  binding inference is EXP-041's, with R1.2 calibration).
- **Simpler alternative considered**: qualify on point estimates alone.
  Rejected — CI context is needed for the fragility statement and costs
  nothing extra.
- **Assumptions**: regime clusters as dependence units (validated upstream);
  split-half halves by event chronological order within domain.
- **Expected output**: `results/qualification_table.csv` — per
  (domain, exit_id): per-instrument nets, pooled net + CI, reference nets,
  gap + CI, split-half columns, floor flags, qualify flag, plus two
  **descriptive disclosure columns** (G1 desk-review input, not part of the
  mechanical rule): the EURUSD share of the pooled net (EURUSD is permanently
  TEST-capped per design §7.3, so qualification evidence concentrated there
  has reduced confirmatory value) and the pooled net recomputed ex-EURUSD.

### Step 6 — Ranking, cap, and frozen qualifying set

- **Method**: rank qualifiers by max-min worst-half pooled net **recomputed on
  the within-domain qualifier-intersection population** (events contained
  under every qualifying candidate of the domain and the applicable
  references), so the ranking that decides what consumes the EXP-041 slot is a
  same-events comparison. The per-candidate-population numbers are disclosed
  alongside in `results/ranking_table.csv`; any rank reversal between the two
  computations sets a `rank_reversal` flag in `run_metadata.json` and
  **escalates to operator adjudication before the EXP-041 freeze** (the
  qualifying set is still emitted, marked provisional). Tie-breaks: fewer
  parameters, then shorter mean holding time. Cap: ≤2 per domain, ≤2 total
  across domains (cross-domain comparison uses each qualifier's within-domain
  intersection statistic). Emit `results/qualifying_set.json` (exit
  definitions, selected parameters, domains, instrument families, containment
  populations, content hash) — written exactly once, after the qualification
  table, before any plot. This file is EXP-041's freeze input; **no TEST
  contact occurs here**.
- **Expected output**: `qualifying_set.json` + `screen_outcome` ∈
  {QUALIFIED, FLAT} in `run_metadata.json`.

### Step 7 — Power/fragility statement (ordering-enforced)

- **Method**: before the qualification table is evaluated, compute and persist
  per-cell minimal stably-selectable gaps = bootstrap SE of the pooled net and
  of each reference gap (from Step 5's descriptive bootstrap); flag every cell
  whose realized reference gap is < 1 SE as structurally fragile, and every
  cell incapable of qualifying (floor or sign) as such. Persisted to
  `results/power_statement.csv` with a write-timestamp ordering assertion
  (power file mtime < qualification read).
- **Why**: the scope mandates the fragility read precede the qualification
  read so a marginal "winner" cannot be narrated as robust post hoc.

### Step 8 — Determinism

- **Method**: all randomness via `seed_for(EXPERIMENT_ID, domain, purpose)`
  (EXP-028 convention); full same-seed replay of one domain must reproduce all
  binding CSVs byte-identically; recorded in `run_metadata.json`.

## Visualisations (5 / 5)

1. `plots/net_by_exit_forest.png` — per domain: pooled net per exit (selected
   points) with descriptive CIs, references as vertical lines, BTCUSD-included
   pooled shown greyed. Answers: who beats the bar, by how much.
2. `plots/reference_gap_stability.png` — per (domain, exit): full-TRAIN gap vs
   the two split-half gaps. Answers: §8.1(iii) at a glance.
3. `plots/holding_time_dist.png` — holding-time distributions per exit vs
   references. Answers: financing exposure and mechanism (loss-cut vs
   trend-ride).
4. `plots/containment_accounting.png` — own-contained vs intersection counts
   and boundary exclusions per cell. Answers: population integrity.
5. `plots/grid_curves.png` — E3 X-grid and E5 H_ts-grid net curves, both
   halves. Answers: grid-selection transparency.

## Interpretation Guide

- ≥1 cell passes §8.1 → **QUALIFIED**: the named exits (≤2) proceed to
  EXP-041 scope freeze; no edge claim is made — TRAIN qualification is a
  selection event, fully exposed to winner's curse, which EXP-041's calibrated
  one-shot TEST exists to discipline.
- No cell passes → **FLAT**: capture-efficiency beyond FH is exhausted on this
  substrate per design §9 (EXIT_FLAT); the EXP-041 slot is unused. A FLAT with
  most cells fragile-flagged is reported as power-limited FLAT, not evidence
  the exits are worthless.
- Reference gaps are reported in **bps (absolute differences)**; never as a
  percentage of a near-zero reference net (1h R-BTC net is expected ≈ 0 or
  negative — zero-baseline rule). Floor cells (n < 30) carry no statement
  beyond their descriptive row.
- Expected base case (recorded now): on 4h, beating R-FH(12) (TRAIN grid max
  +45.79 bps) is a high bar — most candidates failing it is the honest prior;
  on 1h, any exit with all-instrument-positive net would already be new
  information regardless of ranking.

## Implementation Safety Constraints

- TRAIN boundary by `train_end_ts` (R1.3); TEST and holdout never read; lazy
  scan → sort → analysis slice → TRAIN slice before collection.
- Sequential exit resolution explicit for state-dependent rules (E1/E2);
  vectorized crossing scans admissible only for fixed-level rules where
  causally equivalent; no vectorization that changes event membership,
  ordering, or denominators.
- One round-trip + one financing charge per realized position (pyramid legs
  independent); costs/financing constants content-hashed; no iteration.
- Denominators: events (per containment definition); intersection populations
  for all gap statistics; all counts disclosed; no silent deduplication.
- HA values trigger-only; all fills/P&L on real domain `Close`; timestamps
  (`CloseTime`) for all alignment.
- `tqdm` over instrument×domain×exit; helpers return data (no prints); output
  dirs created in orchestration only; bounded memory (per-instrument
  processing; no full-dataset pandas conversion).
- `qualifying_set.json` written once; power statement persisted before
  qualification evaluation; determinism replay required.

## Complexity Check

- Statistical tests: **0 binding / 0 budget** — descriptive bootstrap CIs only
  (one machinery, reused across cells); compliant with the scope's
  zero-binding-test declaration.
- Visualisations: 5 / 5.
- New code modules: 2 / 2 — `python/src/xen/exit_rules.py` and
  `python/experiments/EXP-039/code/run_experiment.py`.
