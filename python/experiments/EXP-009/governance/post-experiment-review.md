VERDICT: APPROVE

Review basis:
- Audit: `python/experiments/EXP-009/audit.md`
- Results interpretation: `python/experiments/EXP-009/results.md`
- Final report: `python/experiments/EXP-009/report.md`
- Index updates: `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

Checks:
- Audit reports no critical issues or warnings.
- Results interpretation follows the pre-specified criteria and does not move the success threshold after seeing results.
- Report states the negative finding clearly: HA reduces 15-minute direction-change count but does not improve log FE/AE on any instrument with a CI excluding zero.
- Synthetic price discipline is preserved; HA prices define signal state only and all outcomes use real 1-minute prices.
- The final 30% global holdout remains excluded.
- Scope was not expanded beyond 15-minute HA versus time-bar direction-change signals.
- Index entries record the REFUTED verdict and key finding without overclaiming.
