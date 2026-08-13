# CF-LIQSWP-001 — Liquidity Sweeps

This is the Chapter 06 working-family pointer. The binding family contract is
[cf-liqswp-001.md](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/docs/signal-registry/candidate-families/cf-liqswp-001.md), and the governing checkpoint design is
[checkpoint-019 design](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/design.md).

Status: `REGISTERED`, EXP-100 complete with HYP-000 upheld by operator;
EXP-101–104 remain separate design/readiness items. No family status transition
has occurred.

## Contents

- [EXP-100 — Liquidity-sweep streaming apparatus](#exp-100--liquidity-sweep-streaming-apparatus)

## EXP-100 — Liquidity-sweep streaming apparatus

**Status:** Completed — HYP-000 upheld by operator  
**Date:** 2026-08-13  
**Instruments:** `EURUSD`, `XAUUSD`, `USTEC` cTrader TRAIN  
**Data views:** 1-minute engine input; 15m/30m/1h observation bars; 1H/4H confirmation references; online TPO/profile state

### Hypothesis Tests

1. **HYP-000:** the AMENDMENT-13 streaming apparatus preserves causal level,
   raid, confirmation, breakout/failure, TPO, and later-outcome identity across
   the frozen 264-cell TRAIN matrix.

### Scope

- **Cells:** 66 15m, 66 30m, 132 1h; 11 level configurations.
- **Exclusions:** Bybit/crypto, TEST, global holdout, deployability, tradability,
  costs, and P&L claims.
- **Control:** zero-fixed-point future-destroy of later outcome blocks;
  validity bite `INTEGRITY_Z × bootstrap_SE`, `INTEGRITY_Z=2.8`.
- **Estimator:** emitted-state coverage, chronology, reconciliation, and
  deterministic replay; no trade ledger.

### Results / Observations

- Family and per-cell estimand gates: `blocking_pass=true` for 264/264 cells.
- Raids: 9,840,478; duplicate level/raid IDs: 0; missing/extra profiles: 0.
- Future-destroy: 264/264 changed, zero fixed points; same-bar returns:
  7,669,654.
- 1D anchor counts: 640–644 per cell; 1W: 129 per cell; weekend anchor keys: 0.
- Undefined TPO profiles: 46,410 (0.47%); right-censored excursions: 30,520.

### Hypothesis-Specific Conclusion

**Operator verdict: UPHELD.** The operator approved and confirmed the analyst
recommendation. The validity evidence supports the apparatus hypothesis, with
the golden-probe indexing caveat retained in [analysis.md](../../../python/experiments/EXP-100/analysis.md).

### Hypothesis-Agnostic Observations

- Same-bar returns are common (median fraction 0.780; range 0.752–0.799).
- The emission does not retain the 1-minute path needed to answer a later
  retracement-into-gap question.
- `LEVEL_CLOSE` and `BREAKOUT_BAR` are numerically identical on 132 shared
  method pairs; the strata remain separate and the overlap is disclosed.

See the full [EXP-100 report](../../../python/experiments/EXP-100/report.md)
and [analysis](../../../python/experiments/EXP-100/analysis.md).
