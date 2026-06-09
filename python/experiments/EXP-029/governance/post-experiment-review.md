# Post-Experiment Governance Review: EXP-029

**Experiment**: EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy
**Stage**: 8 (consolidated post-experiment governance)
**Date**: 2026-06-09
**Reviewer**: research-pipeline (consolidated governance)
**Artifacts reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md` + `docs/experiments-docs/INDEX.md` updates (against `results/` and `run_metadata.json`).

---

## Constraint Review

| Constraint | Verdict | Evidence |
|------------|---------|----------|
| 1. Simplicity over complexity | PASS | No new estimator; the frozen EXP-027 tail is reused unchanged; the added gates are deterministic comparison metrics, not new statistical tests. 3/3 tests, 3/3 plots, 1/1 new module — within budget. |
| 2. No academic-finance pitfalls | PASS | Non-parametric throughout (regime-cluster bootstrap, stratified sign-permutation); no normality/stationarity/i.i.d./constant-vol assumption introduced. Inherited from the calibrated EXP-027 method. |
| 3. Strict experiment scoping | PASS | Single falsifiable parity question; boundaries, exclusions, and predeclared tolerances explicit; no scope creep (detector/anchor branches, costs, HYP-001, per-bar suite all excluded and honored). |
| 4. Framework principles | PASS | Conclusions data-driven; cross-feed alignment by `SourceCloseTime` (never bar index); real-price `RealClose` returns only. |
| 5. OOS holdout rule | PASS | Per-instrument `AnalysisEndUtc` fence enforced in-robot (`AssertCanEmit` on positions AND event-detail) and re-asserted in Python (`load_cell_frame`); per-cell max `SourceCloseTime` < fence in `run_metadata.json`; final 30% never loaded. |
| 6. Look-ahead bias prevention | PASS | C# processes bars sequentially; completion evaluated before regime reset using only `bar.Close`; alignment by timestamp; audit confirmed `load_event_detail` hard-fails on missing/disagreeing trigger timestamps. |
| 7. Real/synthetic-price discipline | PASS | Returns are direction-signed log returns on cTrader `RealClose`; no HA/Renko/brick prices anywhere. |
| 8. Safe performance/memory | PASS | Per-cell lazy reads, `tqdm` over 12 cells, vectorized reconciliation that preserves membership/ordering/denominators; `scan_lifetime` kept genuinely sequential (imported EXP-022 unchanged). |

## Artifact-Specific Review

- **audit.md** — Thorough and evidence-based: holdout, look-ahead, estimand faithfulness (D2), no-Python-signal-oracle (D4), frozen-hash identity (F05), gate falsifiability, and numerical reconciliation all checked with line/value references. Severity classification appropriate (0 Critical, 0 Warning, 4 Info). The bit-identical 4h finding was investigated and correctly cleared as feed coincidence rather than reuse. **Compliant.**
- **results.md** — Anchored to the predeclared interpretation guide; reports values, CIs, sample sizes, and uncertainty honestly; does not overreach (explicitly states event-level ≠ per-bar tradability, gross/no-costs, holdout sealed, equity companion non-gating, HYP-001 untested); carries all audit caveats; follow-ups framed as new scopes, not extensions. **Compliant.**
- **report.md** — Self-contained, embeds the two decisive plots (effect forest, parity table) with captions, honest about limitations, links all artifacts by relative path. **Compliant.**
- **Index updates** — Brief `INDEX.md` row updated SCOPE_DESIGN → CONSISTENT (cTrader-confirmed) with an accurate one-line finding; comprehensive `INDEX.md` gains a full five-field section, the Phase 006 checkpoint line reflects all three experiments complete, and the EXP-028 cTrader caveat is correctly marked RESOLVED. Values cross-checked against `run_metadata.json`/CSVs. **Compliant.**

## Integrity Cross-Checks

- `frozen_inference_hash` = `ea261b9ee0a8aca3`, hard-asserted equal to EXP-028's and to the predeclared constant (F05) — a CONSISTENT result cannot be an artifact of a changed estimator.
- `reconciliation_bad` = 0; `control_matching_equivalence_pass` = true.
- Estimand is the same symmetric own-exit matched-control excess EXP-028 reports (D2); controls rebuilt on the cTrader feed (the documented requirement), not imported from the local-feed EXP-022 observations.
- Disposition logic is genuinely falsifiable: a magnitude divergence, exit-parity failure, or powered verdict conflict forces INCONSISTENT and would have *downgraded* EXP-028. It did not fire because the data agree.

## No Goalpost-Moving

All parity tolerances, gates, and the disposition rule were predeclared in `scope.md`/`analysis-plan.md` and approved at Stage 4 (D8). The reported disposition applies them unchanged.

---

## Verdict

```text
VERDICT: APPROVE
```

EXP-029 is methodologically sound, scope-compliant, holdout-clean, and free of look-ahead or synthetic-price violations. The audit is PASS with no Critical or Warning findings; the interpretation and report are honest and anchored to the predeclared guide; the indexes are correctly updated. The CONSISTENT parity disposition and the resulting upgrade of EXP-028 `EVAL_SUPPORTED` to cTrader-confirmed are well-supported. No revision required.
