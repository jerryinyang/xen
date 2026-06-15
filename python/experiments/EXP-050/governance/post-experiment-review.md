# EXP-050 — Post-Experiment Governance Review

**Phase 014-A · `CF-HA-HARAMI-001` / HYP-003 · Harami-in-Context Characterisation.**

Reviewed artifacts: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`. Checked against the bundled governance constraints and the active checkpoint `design.md` (§6) + `D0-predeclarations.md` (P3–P9, P11, P13.2).

```text
VERDICT: APPROVE
```

## Constraint Checks

| # | Constraint | Check | Result |
|---|------------|-------|--------|
| 1 | Simplicity over complexity | One inferential method (MBB); exact closed-form FT_rand (no Monte Carlo noise); assignment is one vectorized interval-join. No model, no net, no costs. | **PASS** |
| 2 | No academic-finance pitfalls | Non-parametric MBB; no normality/i.i.d./stationarity assumption; exact FT_rand is a population rate, not a distributional model. | **PASS** |
| 3 | Strict scoping | Single exploratory question (harami position-in-move + FT vs FT_rand); all boundaries, views, instruments, exclusions defined; 1 test / 4 plots / 1 module within budget; no bonus analyses. | **PASS** |
| 4 | Framework principles | Data-driven; real-price discipline (RealClose for signal price, HA for detection only); timestamp alignment by CloseTime/epoch. | **PASS** |
| 5 | OOS holdout | F01 prefix loader: only first train_rows (~49%) collected; all HA0Time/ConfirmTime timestamps fenced to train_end_ts; TEST and final-30% never read. Verified in audit. | **PASS** |
| 6 | Look-ahead prevention | Predeclared descriptive-allowance carve-out: terminal pivot referenced for position-in-move (hindsight, completed moves only). No P&L, signal, or capture computation exists anywhere — bound honored. | **PASS** |
| 7 | Real-price discipline | All metrics on real domain prices. HA candles used for detection only; no HA price enters any metric. | **PASS** |
| 8 | Safe performance/memory | Lazy scans + projection; per-cell bounded memory; MBB batched; plots from collected scalars (no data reload); tqdm outer loop. | **PASS** |
| 9 | Audit integrity | Audit PASS: 0 Critical, 0 Warning, 1 Info. Code, data handling, numerical outputs, holdout, look-ahead carve-out, and scope compliance all verified. Determinism replay confirmed on 99/99 cells. | **PASS** |
| 10 | Results interpretation | Honest reporting: negative result clearly stated (0/99 CLUSTERED, all Δ < 0), power adequate, limitations acknowledged (look-ahead carve-out, no filter, ZigZag-specific). No overclaiming. | **PASS** |
| 11 | Report and indexes | report.md is self-contained with artifact links. INDEX.md updated with concise entry. Comprehensive INDEX.md updated with full section + checkpoint status updated. | **PASS** |
| 12 | Pre-execution handover | Pre-execution info notes (i) FT_rand closed-form refinement and (ii) descriptive carve-out both applied correctly and documented in results/report. | **PASS** |

## Artifact Consistency

All artifacts are internally consistent:
- audit.md findings (all invariants 0, determinism True, range checks pass) match results.md data.
- results.md interpretation matches the output CSVs and composition_readout.json (0 CLUSTERED, all NOT_CLUSTERED).
- report.md matches results.md and audit.md.
- INDEX entries match report.md conclusion.
- Checkpoint status line updated to reflect EXP-050 completion.

## Verdict

All checks pass. No Critical or Warning issues. The experiment is complete and documented.
```text
VERDICT: APPROVE
```
