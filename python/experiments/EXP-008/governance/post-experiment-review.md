VERDICT: APPROVE

Review basis:
- Audit: `python/experiments/EXP-008/audit.md`
- Results interpretation: `python/experiments/EXP-008/results.md`
- Final report: `python/experiments/EXP-008/report.md`
- Index updates: `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

Checks:
- Audit reports no critical issues or warnings.
- Results interpretation applies the pre-specified 15-minute, 15-minute-window criterion and treats 1-minute outputs as exploratory.
- Report states the negative result clearly: Renko confirmation lowers AE but also lowers FE and improves log FE/AE on only 1 of 4 instruments.
- Same-or-prior Renko confirmation prevents look-ahead.
- Outcomes use real 1-minute time-bar prices, not Renko construction prices.
- The final 30% global holdout remains excluded.
- Index entries record the REFUTED verdict and the coverage/compression trade-off.
