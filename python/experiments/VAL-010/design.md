# VAL-010 — Later-swing anatomy characterisation

## Frozen source and question

Read-only re-analysis of EXP-100. It asks: **when `strong_move` differs across the level and repeat strata studied in EXP-101/102, is the difference located in initial excursion, post-confirmation swing, their surplus, or the emitted post-confirmation path?**

MECHANISM: `strong_move` is defined as `swing_atr > max_excursion_atr`; a lower rate can arise from either side of that inequality. Decomposing both terms and the emitted `pre_mfe_retrace` state identifies the anatomy without treating any realised post-confirmation field as an entry condition.
DERIVED: estimand=completed-primary, ATR-defined distributions of `max_excursion_atr`, `swing_atr`, `swing_atr-max_excursion_atr`, duration, and retrace status; null=no causal selection or trade claim; horizon=confirmation to endpoint; test=descriptive distributions by frozen configuration and exact repeat count.

## Identity, scope, and analysis

OBJECT-IDENTITY:
  measurement object == trading object: N/A — no trading object; this is a raid/swing event study.
  measured conditioning event == traded entry event: N/A — no entry rule.
  effect-splitting windows non-overlapping: YES — each completed primary contributes its own confirmation-to-endpoint interval.

- Source: EXP-100 `raids.parquet`, TRAIN only; outcome population is `COMPLETED && primary_attribution && primary_completed`.
- Exclude `ATR_UNDEFINED` from all ATR and strong-move views. No rows are silently removed from census tables.
- Group by frozen `config`, side, instrument, timeframe, confirmation method/reference, and exact prior count; duplicate BB/LC results are marked as duplicated source objects.
- `pre_mfe_retrace` is outcome anatomy only: it must not be presented as an ex-ante filter.
- Every anatomy table uses the physical-grid view that collapses only the duplicated BB/LC source pair; raw rows remain as a parity receipt. A pattern in one component is not called a mechanism unless the other components are shown beside it.

## Integrity and interpretation

HARD (block): EXP-100 estimand gate, TRAIN fence, timestamp ordering, zero-cost compliance, and no holdout access.
INFORMATIVE: each distribution and all configuration/count contrasts. No machine verdict.

CONTROL: The existing future-destroy is retained as source validity only. No new causal effect is claimed by this descriptive decomposition.
TRIPWIRE: N/A — no new future-alignment claim.

SAMPLE-SIZE:
  expected events per stratum: all completed-primary ATR-defined raid rows, printed with n.
  declared_fixed_comparator: none in this characterisation; EXP-101/102 comparators remain their own registered analyses.
  channels: max_excursion_atr, swing_atr, surplus_atr, strong_move, swing_duration_ns, retrace status.
  strata predeclared thin: all retained and reported.

BANDS (per stratum): operator-only descriptive language; no pass/fail and no pooled finding without homogeneity.

ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission, or swap enters any calculation. Realised results would differ (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped experiment; the directive is recorded in that experiment's design.md.
