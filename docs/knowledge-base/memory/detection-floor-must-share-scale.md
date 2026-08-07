---
name: detection-floor-must-share-scale
description: A detection floor must be built from the same SE family as the row's own CI, and an algebraically knowable estimand ceiling is computed in the design.
metadata: { type: lesson, chapter: 5 }
---
SPDR-024's first emission returned "unresolvable" on essentially every read — the signature of a
floor on the **wrong scale**, not thin data. `MDE_Z = 2.8` (a sample-size target) was used as a
significance bar beside a bootstrap SE the floor ignored, while for a pure SIZE device the
σ̂-normalised estimand is arithmetically pinned to the baseline's **per-trade Sharpe**
(0.032–0.059 here). Clearing the floor needed 2,270–7,501 independent blocks; **3 of 4 cells
could not resolve anything before the run started.** The emission was purged and fully re-run.

AMENDMENT-7, now programme-wide:
- **R1/R5** preflight power counts and historical effect bands are context, never thresholds.
- **R2** `mde = MDE_Z × bootstrap_SE` of the **same estimator as that row's CI**.
- **R3** no row is dropped, demoted or labelled by its floor; `WASH`/`UNPOWERED` as row verdicts
  are withdrawn.
- **R4** every channel declares its `sigma_denominator`; channels with different denominators are
  never ranked on one ladder.
- **Design-time ceiling check:** where the estimand's algebraic maximum is knowable beforehand,
  compute it and the implied block requirement **per cell in the design**, and declare incapable
  cells before they run.

Diagnostic heuristic: a floor calibrated to the data fails *some* reads; a floor on the wrong
scale fails *all* of them. Universal failure is the alarm. See [[per-notional-blind-to-size]].
