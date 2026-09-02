# VAL-011 — TPO geometry and volatility-state characterisation

## Frozen source and question

Read-only re-analysis of EXP-100. It asks: **do continuous TPO geometry and causal volatility-state transitions describe different emitted raid populations and later-swing distributions, and what is the design-faithful all-raid frequency by state?**

MECHANISM: The binary tight-gap label may proxy profile scale or geometry, while a single raid-time volatility label may omit subsequent state transitions. The frozen profile and bar-mark records permit a descriptive separation of those emitted states. Frequency must count every `raid_id` start against preceding-mark exposure, rather than mix all starts with completed-primary counts.
DERIVED: estimand=defined-profile geometry quantiles and completed-primary outcome summaries; raid→confirmation→endpoint regime-transition census; all-raid starts per preceding-regime mark; null=no causal or deployable claim; horizon=profile formation and raid terminal event; test=descriptive stratified tables.

## Identity, scope, and analysis

OBJECT-IDENTITY:
  measurement object == trading object: N/A — no trade/P&L object; emitted raid/profile/mark objects only.
  measured conditioning event == traded entry event: N/A — no entry rule.
  effect-splitting windows non-overlapping: YES — one profile and one terminal raid record per source-cell raid.

- Source: EXP-100 `raids.parquet`, `tpo_profiles.parquet`, and `bar_marks.parquet`; left join profiles on `(raid_id, profile_generation)` within each cell.
- Geometry: retain undefined-profile reasons; defined rows use `gap_span_va`, `gap_span_atr`, `va_width`, profile duration, and `tight_gap`.
- Regimes: retain LOW/MID/HIGH/WARMUP/ATR_UNDEFINED in census; only ATR-defined completed primaries enter ATR/strong-move outcome summaries.
- Frequency: denominator is every preceding observation mark in a named LOW/MID/HIGH regime; numerator is every raid start at the next mark, counted once per source-cell `raid_id`; sides are separate.
- BB/LC duplicates are collapsed to one physical grid before outcome and frequency summaries; raw counts are parity-only. Frequency is descriptive and is not used to support a mechanism while outcome channels disagree.

## Integrity and interpretation

HARD (block): EXP-100 gate, source/profile left-join reconciliation, TRAIN fence, zero-cost compliance, no holdout read.
INFORMATIVE: geometry, transition and frequency tables. No machine verdict.

CONTROL: Existing future-destroy validates the source outcome alignment; no new causal or predictive result is asserted here.
TRIPWIRE: N/A — no new edge claim.

SAMPLE-SIZE:
  expected events per stratum: all source rows/marks retained with n and exposure.
  declared_fixed_comparator: none; this is a characterisation, not an adaptive arm.
  channels: profile geometry, regime transition, all-raid starts/exposure, swing_atr and strong_move summaries.
  strata predeclared thin: all retained and reported.

BANDS (per stratum): operator-only descriptive language. Pooled figures are disclosure-only.

ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission, or swap enters any calculation. Realised results would differ (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped experiment; the directive is recorded in that experiment's design.md.
