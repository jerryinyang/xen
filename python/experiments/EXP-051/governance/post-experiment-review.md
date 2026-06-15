# EXP-051 — Post-Experiment Governance Review

**Phase 014-A · `CF-HA-HARAMI-001` / HYP-004 · Strong-Move Filter Characterisation.**

Reviewed artifacts: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`. Checked against the bundled governance constraints and the active checkpoint `design.md` (§6) + `D0-predeclarations.md` (P3–P9, P11, P13.2).

```text
VERDICT: APPROVE
```

## Constraint Checks

| # | Constraint | Check | Result |
|---|------------|-------|--------|
| 1 | Simplicity over complexity | Deterministic P10 point criterion is the binding test; MBB bootstrap CI is explicitly **non-binding** disclosed support. No model, no net, no costs. | **PASS** |
| 2 | No academic-finance pitfalls | Non-parametric throughout (medians, percentiles, MAD, block bootstrap). No normality/i.i.d./stationarity assumption. | **PASS** |
| 3 | Strict scoping | Single exploratory question (materially-different move populations); two filter forms (STRONG-STAT, STRONG-HA) each with one binding + one disclosed alternative; all boundaries, views, instruments, exclusions defined; 1 statistical method / 4 plots / 1 module. | **PASS** |
| 4 | Framework principles | Data-driven; real-price discipline (real prices for all magnitude metrics; HA for detection only); timestamp alignment by CloseTime/epoch. | **PASS** |
| 5 | OOS holdout | F01 prefix loader: `train_rows=int(int(total*0.7)*0.7)`, `slice(0, train_rows)`; full file never sorted/collected; TEST + final-30% never read; every emitted timestamp fenced `≤ train_end_ts`. Verified in audit. | **PASS** |
| 6 | Look-ahead prevention | Filter decisions causal: STRONG-STAT trailing window strictly prior; STRONG-HA qualify uses `body.shift(1).rolling_median` + own bar. ZigZag frozen/sequential. Completed-move magnitude uses terminal pivot — pre-approved descriptive completed-move carve-out (same as EXP-050). | **PASS** |
| 7 | Real-price discipline | All metrics on real domain prices. HA candles used for detection only; no HA price enters any metric. | **PASS** |
| 8 | Safe performance/memory | Bounded per-cell loops (STRONG-STAT variable-window quantile sequential; STRONG-HA cumsum vectorised); MBB batched; plots from collected scalars; tqdm outer loop. | **PASS** |
| 9 | Audit integrity | Audit PASS: 0 Critical, 0 Warning, 3 Info (F01 file-order pre-approved; retained&defined masking scope-compliant; DE30 truncated history disclosed). Determinism confirmed on 99/99 cells. | **PASS** |
| 10 | Results interpretation | Honest reporting: mechanical characterisation verdict (STRONG_FILTER_CHARACTERISATION_DELIVERED) not an overclaim; limitations acknowledged (uniformity may reflect substrate, not special filter property; HA impulse runs mid-move possible without top-quartile magnitude; 0 flips across disclosed forms). | **PASS** |
| 11 | Report and indexes | report.md is self-contained with artifact links. INDEX.md updated with concise entry. Comprehensive INDEX.md updated with full section + checkpoint status updated. | **PASS** |
| 12 | Pre-execution handover | All 7 pre-execution findings (F01–F07) dispositioned as documented in pre-execution-review.md: F01 no action, F02 kept exact, F03 fixed doc, F04 no change, F05 no change, F06 added invariant, F07 added guard. None altered methodology or scope. | **PASS** |

## Artifact Consistency

All artifacts are internally consistent:
- audit.md findings (all invariants 0, determinism True, range checks pass) match results.md data.
- results.md interpretation matches the output CSVs and composition_readout.json (99/99 MATERIAL both forms, both P11 pass, 0 flips).
- report.md matches results.md and audit.md.
- INDEX entries match report.md conclusion.
- Checkpoint status line updated to reflect EXP-051 completion.

## Verdict

All checks pass. No Critical or Warning issues. The experiment is complete and documented.
```text
VERDICT: APPROVE
```
