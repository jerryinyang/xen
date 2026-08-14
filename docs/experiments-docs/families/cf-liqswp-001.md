# CF-LIQSWP-001 — Liquidity Sweeps

This Chapter 06 working-family index points to the binding
[candidate-family contract](../../signal-registry/candidate-families/cf-liqswp-001.md) and
[checkpoint-019 design](../checkpoints/2026-08-11-019-liquidity-sweeps/design.md).

Status: `REGISTERED` (unchanged). EXP-100 is complete and operator-approved with a scoped
ATR-undefined exclusion. EXP-101–104 remain separate readiness items. No family promotion,
retirement, or closure has occurred.

## Contents

- [EXP-100 — Liquidity-sweep streaming apparatus](#exp-100--liquidity-sweep-streaming-apparatus)

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
