# VAL-009 — Raid selection and lifecycle characterisation

## Frozen source and question

Read-only re-analysis of the 264-cell EXP-100 TRAIN emission. It asks: **how do raid lifecycle transitions, primary selection, level age, and exact prior-raid count co-occur in the emitted population?**

MECHANISM: Primary attribution retains the latest eligible returned raid; therefore outcome-only rows can be a selected subset. A complete lifecycle census can distinguish the emitted selection mechanism from a broad claim about all raids. This is descriptive object characterisation, not a trade signal.
DERIVED: estimand=per-cell and per-stratum census proportions, selection-set sizes, level age, and exact-count outcome summaries; null=no causal or predictive claim; horizon=raid start through terminal status; test=descriptive distributions with counts.

## Identity, scope, and analysis

OBJECT-IDENTITY:
  measurement object == trading object: N/A — no trading object or P&L claim; measurement object is an emitted level-linked raid.
  measured conditioning event == traded entry event: N/A — no entry rule.
  effect-splitting windows non-overlapping: YES — one terminal record per `raid_id` per source cell.

- Source: `data/nautilus_runs/EXP-100/full/*/raids.parquet`; 264 cells, cTrader TRAIN only.
- Population: every raid row for lifecycle tables; completed, primary rows only for later-swing summaries.
- Main views: status funnel; groups sharing a `confirmation_ts_ns`; level age `sweep_ts_ns-level_creation_ts_ns`; exact `prior_raid_count`; fixed broad bins are disclosure-only.
- Per instrument/timeframe/config/side first. Cross-cell pooled totals are labelled disclosure-only.
- Every table is emitted twice where relevant: raw source rows and a physical-grid view that collapses only the `BREAKOUT_BAR`/`LEVEL_CLOSE` duplicate pair. The raw 264-cell counts are never described as independent agreement.
- `ATR_UNDEFINED` remains in count tables but is excluded from ATR/strong-move summaries.
- No adaptive choice, no ranking, no P&L or deployability inference.

## Integrity and interpretation

HARD (block): inherited EXP-100 gate remains `blocking_pass=true`; pinned TRAIN fence; zero-cost compliance; no holdout read; source timestamp order remains valid.
INFORMATIVE: all counts, proportions, age and repeat summaries. No machine verdict.

CONTROL: N/A. This study asserts no aligned future-outcome effect; it characterises emitted state and selection. Existing EXP-100 future-destroy evidence remains source-validity evidence, not a new control for this description.
TRIPWIRE: N/A — no new edge or future-dependent estimand is asserted.

SAMPLE-SIZE:
  expected events per stratum: retain every emitted row and print n.
  declared_fixed_comparator: none; no treatment comparison.
  channels: lifecycle counts, selection-set size, level age, exact prior-raid count.
  strata predeclared thin: all retained and reported.

BANDS (per stratum): operator may describe a pattern after reviewing counts; no machine tags. Pooled figures are disclosure-only.

ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission, or swap enters any calculation. Realised results would differ (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped experiment; the directive is recorded in that experiment's design.md.
