# EXP-098 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-25 · **Reviewer:** research-pipeline consolidated governance · **Artifacts reviewed:**
`scope.md`, `analysis-plan.md`, `code/run_experiment.py`, against `governance-constraints.md`, the active Phase 022
`design.md`, `D0-amendment-002`, and the developer code conventions.

## Summary

EXP-098 is a **non-binding cross-broker & aggregation-method robustness replication** of the G-022a-frozen RSI-2
fade deployment portfolio, reusing the EXP-097/096/095/090 construction verbatim and changing only (a) the data
source (independent broker, `data/timebars/pps/`) and (b) the Arm-2 aggregation timestamp label. All core
constraints pass. One reviewed, operator-ratified methodological judgment (full-PPS-timeline read) is documented
below and found sound. No Critical or Warning issues.

## Constraint checks

**Scope (scope.md)**
- Single falsifiable question, per-arm: ✅ — primary Portfolio B clears the inherited band (Sharpe LB > 2.00 AND
  Calmar LB > 0) under Arm 1 (broker) and Arm 2 (aggregation).
- Boundaries explicit (PPS dataset, 8 carry-8 cells, full timeline, INFR-003 + its holdout excluded): ✅.
- Measurable criteria (ROBUST/DEGRADED/INCONCLUSIVE per arm; CROSS_BROKER / AGGREGATION_ROBUST overall): ✅.
- Gate-threshold calibration: ✅ — the bands (1.75 / 2.00) are **inherited verbatim** (the EXP-095 A4 MDE m\*),
  disclosed as borrowed-from-EXP-097, which is the correct reuse for a same-bar robustness check; not a magic
  constant, not re-derived.
- Real-price outcome rule stated (real OHLC only; no HA/Renko): ✅.
- Complexity budget (1 statistic × 2 arms, ≤5 plots, 0 new modules): ✅.

**Analysis plan (analysis-plan.md)**
- Per-method "why / simpler alternative / assumptions" present; methods are the verbatim-reused frozen statistic +
  descriptive disclosure (moving-block bootstrap — non-parametric, serial-dependence-robust; no normality / i.i.d.
  / stationarity assumption): ✅.
- Cross-view alignment by `CloseTime` timestamp, never bar index: ✅.
- Pre-registered interpretation guide (if-X-then-Y) before results: ✅.
- Per-stratum doctrine: the binding estimand is the **portfolio** (the deployment object), adjudicated **per arm**;
  per-cell PPS outcomes disclosed + a **drop-one masking check** guards heterogeneity (LESSON-001), exactly the
  EXP-097 precedent. The overall `CROSS_BROKER_ROBUST` / `AGGREGATION_ROBUST` are explicit named composites, not a
  collapsed binding PASS hiding strata. ✅.
- Budget compliance: ✅.

**Code (code/run_experiment.py)**
- Plan compliance — implements exactly the plan, nothing extra: ✅.
- INFR-003 holdout never loaded: ✅ — `load_full_pps_1m` guards `path.parent == PPS_DIR`; `infr003_holdout_loaded
  = false` asserted in outputs/metadata. Only `data/timebars/pps/` is opened.
- Look-ahead / causality: ✅ — `H_eval` is the covariance-warmup boundary (`LOOKBACK_STEPS`), not a data fraction;
  causal-weight and causal-fill assertions are exercised **in the evaluable region** per arm; the frozen
  substrate's streaming semantics are untouched (Arm-2 change is a pure relabel of the aggregation group-by).
- Real-price outcomes: ✅ — all P&L via the frozen real-OHLC substrate.
- Verdict representation per-stratum: ✅ — per-arm labels emitted separately; masking check + per-cell disclosure
  present; no collapsed cross-arm binding flag.
- Type hints, docstrings, NaN handling (NaN-not-inf guards inherited; `<2`-event → NaN+flag; insufficient-grid
  raises), edge cases, separation of concerns, no import-time side effects (dir creation only in orchestration;
  the `E96 = _load_exp096()` import is the established import-safe reuse pattern), `tqdm` on cell×arm loops,
  concise logging, bounded plot inputs, seeded determinism: ✅.
- Static validation performed: byte-compiles; module wiring resolves; PPS discovery maps all 8 instruments; the
  Arm-2 aggregation reproduces canonical OHLC exactly, differing only in the `CloseTime` label.

## Reviewed methodological judgment (documented, not a violation)

**Full-PPS-timeline read vs the standard 70/30 holdout convention.** The OOS holdout rule (final-30% never
loaded) protects the **canonical analysis dataset (INFR-003)** against selection/training contamination. EXP-098
performs **no selection or tuning** — the model is fully frozen at G-022a — and reads an **independent broker
dataset** that was never used for any training. The INFR-003 global holdout remains sealed and is provably not
loaded. The operator explicitly ratified the full-timeline slice (`D0-amendment-002`), and the scope honestly
records that PPS is hereby "touched" as a robustness dataset (any future *binding* use needs its own governance).
The spirit of the constraint — no overfitting/selection contamination — is fully preserved. This is the correct
treatment for a frozen-model replication and is **not** a holdout violation.

## Verdict

```text
VERDICT: APPROVE
```
