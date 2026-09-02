# CF-LIQSWP-001 — Liquidity Sweeps

This Chapter 06 working-family index points to the binding
[candidate-family contract](../../signal-registry/candidate-families/cf-liqswp-001.md) and
[checkpoint-019 design](../checkpoints/2026-08-11-019-liquidity-sweeps/design.md).

Status: `REGISTERED` (unchanged). EXP-100 is complete and operator-approved with a scoped
ATR-undefined exclusion. EXP-101–104 are complete as experiment records (2026-09-02).
No family promotion, retirement, or closure has occurred.

## Contents

- [EXP-100 — Liquidity-sweep streaming apparatus](#exp-100--liquidity-sweep-streaming-apparatus)
- [EXP-101 — Level configuration and later-swing outcomes](#exp-101--level-configuration-and-later-swing-outcomes)
- [EXP-102 — Repeated raids and prior-raid count](#exp-102--repeated-raids-and-prior-raid-count)
- [EXP-103 — TPO value gaps and tight-gap outcomes](#exp-103--tpo-value-gaps-and-tight-gap-outcomes)
- [EXP-104 — Causal volatility regime and later-swing outcomes](#exp-104--causal-volatility-regime-and-later-swing-outcomes)

## EXP-100 — Liquidity-sweep streaming apparatus

**Status:** COMPLETED — operator-approved with scoped exclusion
**Date:** 2026-08-13
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN
**Data views:** 1-minute engine input; 15m/30m/1h observation bars; 1H/4H confirmation references; online TPO/profile state

### Hypothesis Tests

1. **HYP-000:** the AMENDMENT-14 streaming apparatus preserves causal level, raid,
   confirmation, breakout/failure, TPO, and later-outcome identity across the frozen
   264-cell TRAIN matrix.

### Scope

- **Cells:** 66 15m, 66 30m, 132 1h; eleven level configurations.
- **Exclusions:** Bybit/crypto, TEST, global holdout, costs, P&L, tradability, and deployment.
- **Control:** zero-fixed-point future-destroy on the finite normalized primary population;
  validity bite `INTEGRITY_Z × bootstrap_SE`, `INTEGRITY_Z=2.8`.
- **Estimator:** emitted-state coverage, chronology, reconciliation, lifecycle, status, and
  attribution; no trade ledger.
- **Mandatory value exclusion:** every ATR-undefined excursion and derived value is excluded
  from interpretation.

### Results / Observations

- Published family gate: `blocking_pass=true`; 264/264 cells. Independent follow-up limits
  that attestation by excluding the scoped ATR-undefined excursion path.
- Raids: 9,840,478; duplicate raid/level IDs, missing/extra profiles, chronology failures,
  active residuals, and attribution failures: 0.
- Statuses: 4,702,900 `FAILED_BREAKOUT`; 4,316,600 `CONFIRMED_NON_PRIMARY`; 789,326
  `COMPLETED`; 30,520/626/506 excursion/confirmation/endpoint right-censors.
- TPO profiles: 9,794,210 defined; 46,268 undefined (`45,400 GAP_UNDEFINED`,
  `868 ATR_UNDEFINED`). Same-bar returns: 7,669,654.
- ATR-undefined excursion defect: **780/9,840,478 emitted rows affected (0.007926%)**;
  **390 unique affected objects after method deduplication**; **84 affected primary/completed
  rows**; **71.43% median understatement among affected rows**.
- Future-destroy remains valid for its 789,646 aligned finite-primary pairs because
  ATR-undefined rows are excluded from that population; 264/264 cells changed, zero fixed points.
- Retained evidence: coverage, chronology, lifecycle, status, attribution, and finite-population
  control findings. Excluded evidence: ATR-undefined excursion and derived values.

### Hypothesis-Specific Conclusion

**COMPLETED — OPERATOR-APPROVED WITH SCOPED EXCLUSION.** Binding operator verdict:
“retain the current run; ATR-undefined excursion values are limited/invalid and must be excluded
from all interpretations; make no implementation changes; perform no reruns/emissions.” The
analyst separately assigned no replacement verdict and found the exact-state hypothesis not clean
for the excluded maximum-excursion path.

### Hypothesis-Agnostic Observations

- BREAKOUT_BAR and LEVEL_CLOSE have identical identities/statuses in all 132 paired strata.
- Same-bar returns dominate returned raids; longer-lived returns are a minority.
- No orders, fills, P&L, mean-trade/leg bps, or PSR exist; no economic claim follows.
- AMENDMENT-14 retrace ambiguity/no-MFE states are explicit, not silently numeric.

See the full [EXP-100 report](../../../python/experiments/EXP-100/report.md),
[analysis](../../../python/experiments/EXP-100/analysis.md), and
[checkpoint status](../checkpoints/2026-08-11-019-liquidity-sweeps/status.md).

## EXP-101 — Level configuration and later-swing outcomes

**Status:** INCONCLUSIVE
**Date:** 2026-09-02
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN
**Data views:** frozen EXP-100 completed-primary leftovers vs declared config comparators

### Hypothesis Tests

1. **HYP-001:** higher-degree / longer-window level configs have different later-swing
   ATR, duration, or strong-move rate than the fixed same-stratum comparators.

### Scope

- **Cells:** 264 source cells; physical grid collapses BB/LC.
- **Exclusions:** TEST, holdout, costs, P&L, tradability.
- **Comparator:** Family A `PREVIOUS_1H`; Family B `PREVIOUS_ASIA`; Family C `ROLLING_7`.

### Results / Observations

- Family A strong-move: 144/144 labelled strata CI below 0 vs `PREVIOUS_1H`.
- Family C strong-move: 132/144 CI below 0 vs `ROLLING_7`.
- Family B strong-move: 2/96 CI exclude 0.
- Mean `swing_atr` CI overlaps 0 in 346/384 strata; duration overlaps 0 in 368/384.
- BB/LC contrasts identical; independent grids ≈ half the labelled count.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE.** Operator 2026-09-02: a strong-move rate drop on some families is not a
general higher-degree leftover-swing mechanism. Analyst recommendation matched.

### Hypothesis-Agnostic Observations

- Completed primaries are ~8% of emitted raids (VAL-009).
- Where ATR separates it is smaller; where duration separates it is often longer.

See [EXP-101 report](../../../python/experiments/EXP-101/report.md).

## EXP-102 — Repeated raids and prior-raid count

**Status:** COMPLETED — descriptive ATR / strong-move only
**Date:** 2026-09-02
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN
**Data views:** prior-raid count bands 1 and 2+ vs count 0

### Hypothesis Tests

1. **HYP-002:** later-swing outcomes differ by prior-raid count versus first raids.

### Scope

- **Population:** completed primary, ATR-defined.
- **Exclusions:** TEST, holdout, costs, P&L, tradability.
- **Channels:** `swing_atr`, `swing_duration_ns`, `strong_move` kept separate.

### Results / Observations

- 1-vs-0 strong-move: 438/528 labelled strata CI below 0; 0 above; median contrast ≈ −0.245.
- 2+-vs-0 `swing_atr`: 354/528 CI below 0 vs 2 above; median contrast ≈ −1.23 ATR.
- VAL-010 physical side-strata: 1-vs-0 strong-move lower on 255/264; duration 130 shorter / 134 longer.
- Duration median remains ~5 h.

### Hypothesis-Specific Conclusion

**PARTIALLY SUPPORTED as a description of leftover ATR / strong-move; duration does not
confirm.** Operator 2026-09-02 narrowed the analyst’s SUPPORTED tag. Not a trade.

### Hypothesis-Agnostic Observations

- Second raids often have a larger first push and a smaller leftover surplus (VAL-010).
- Labelled 528 strata double-count BB/LC.

See [EXP-102 report](../../../python/experiments/EXP-102/report.md).

## EXP-103 — TPO value gaps and tight-gap outcomes

**Status:** INCONCLUSIVE
**Date:** 2026-09-02
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN
**Data views:** tight vs non-tight DEFINED TPO profiles

### Hypothesis Tests

1. **HYP-003:** tight DEFINED gaps have different later-swing ATR and duration than
   non-tight DEFINED gaps in the same stratum.

### Scope

- **Comparator:** non-tight DEFINED, same named stratum.
- **Exclusions:** TEST, holdout, costs, P&L, tradability.

### Results / Observations

- Tight mean ATR < non-tight in 504/528 labelled strata; 344/528 CI entirely below 0; 0 above.
- Tight arm ≈ 6% of the outcome population (46,528 vs 742,516).
- Duration CI overlaps 0 in 436/528.
- 264/264 BB/LC pairs identical on this contrast.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE.** Operator 2026-09-02: smaller tight-arm ATR is not the declared
later-swing pair and is a rare slice. Analyst recommendation matched.

### Hypothesis-Agnostic Observations

- Strong-move rate is often *higher* on tight while mean ATR is *smaller*.
- VAL-011 `gap_span_va` piles between 0.5 and 1.0.

See [EXP-103 report](../../../python/experiments/EXP-103/report.md).

## EXP-104 — Causal volatility regime and later-swing outcomes

**Status:** COMPLETED — descriptive ATR / strong-move only
**Date:** 2026-09-02
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN
**Data views:** LOW/HIGH vs MID leftover swings; all-raid start rate by preceding regime

### Hypothesis Tests

1. **HYP-004:** LOW and HIGH differ from MID in later-swing outcomes **and** raid frequency.

### Scope

- **Outcome population:** completed primary, ATR-defined.
- **Frequency:** all raid starts vs preceding marks (VAL-011 rebuild).
- **Exclusions:** TEST, holdout, costs, P&L, tradability.

### Results / Observations

- LOW−MID leftover ATR: interval above 0 in 400/528 labelled strata; HIGH−MID below 0 in 434/528.
- VAL-011 HIGH vs MID: strong-move down 257/264; duration **up** 219/264 (mean Δ +2.2 h).
- VAL-011 LOW vs MID: leftover ATR up 263/264; duration **down** 217/264 (mean Δ −0.9 h).
- Physical start rates / 1,000 marks: HIGH 1451, MID 1277, LOW 1244.

### Hypothesis-Specific Conclusion

**PARTIALLY SUPPORTED as a description of leftover ATR / strong-move; duration and
frequency do not confirm.** Operator 2026-09-02 narrowed the analyst’s SUPPORTED tag.
Not a trade.

### Hypothesis-Agnostic Observations

- HIGH starts more raids and then shows weaker completed leftovers.
- Confirmation-regime is null on the bulk of VAL-011 transition rows.

See [EXP-104 report](../../../python/experiments/EXP-104/report.md).
