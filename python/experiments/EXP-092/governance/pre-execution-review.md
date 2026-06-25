# EXP-092 — Pre-Execution Governance Review

**Stage 4 (research-pipeline).** Reviews `scope.md`, `analysis-plan.md`, `code/run_experiment.py` against the
bundled governance constraints, the developer code conventions, and the Phase 021 checkpoint `design.md` /
`D0-predeclarations.md` (+ amendments 003/004/005). Per-experiment governance only — phase governance is the
G-021 gate.

---

## Signal-registry precondition (Stage 1/Stage 4 gate)

- **Family `CF-MR-001` is `ADMITTED (BINDING)`** (G-020; first slot consumed) — `candidate-families/cf-mr-001.md`. ✓
- **EXP-092 is registered** in `multiplicity-registry.md` Phase 021 batch (line 891, `PLANNED`, 0/0). ✓
- **No new countable item** — EXP-092 is a TRAIN-only sequence over the *already-screened* EXIT-RCT survivors
  (EXP-091 1h, EXP-094 4h). No new variant / detector / parameter branch / candidate ⇒ **no multiplicity-registry
  addition required**. ✓
- **No TEST-stratum read** (TRAIN-only). `test-read-ledger.md` unchanged; the 11 carried strata are all 0/2 open
  (incl. the six 4h strata admitted by EXP-094); the scope states this. No counted read until EXP-093. ✓

## Phase-alignment (checkpoint `design.md` §4 / `D0` §D6)

- EXP-092 is the design §4 **per-instrument cost-bearing tradability sequence**; it carries **EXIT-RCT** (the
  sole screen survivor — EXP-091 1h 5/5 + EXP-094 4h `ADMIT_4H` 6/6) and produces the **hash-pinned
  `SEQUENCE_PASS` candidate set (sha256) + the sized phase Holm rule** for EXP-093. Exactly the predeclared role. ✓
- **Sequence rule matches D0 §D6/4b**: per-cell `SEQUENCE_PASS` iff net `ci_low_1s > 0` at α=0.05 one-sided
  (Z=1.645, moving-block bootstrap), power-confirmed by the finite EXP-090/094 MDE. The EXP-093 margin condition
  (`ci_low > MDE`, 4c) is co-reported **descriptively** and does **not** gate the sequence — the faithful
  4b/4c reading. ✓
- **No new selection statistic** — the binding estimator is the existing EXP-090/091 net lower bound; the Holm
  rule is standard multiplicity control for the *EXP-093* TEST. Per D0 §D4, **no bite-check is required**. ✓
- 4h handled per `D0-amendment-004`/`-005` (admitted domain expansion, 0 new slots); cost per `D0-amendment-003`
  (Phase-021-local table; shared `COST_CONSTANTS` not mutated). ✓

## Scope (`scope.md`)

| Check | Verdict |
|---|---|
| Single, falsifiable question | ✓ which carried cells `SEQUENCE_PASS` → candidate set + Holm rule |
| Boundaries explicit | ✓ 11 cells (5×1h, 6×4h), EXIT-RCT only, TRAIN-only `[0, 0.7·analysis)`, ATR(14) units |
| Success/failure/inconclusive concrete + measurable | ✓ `SEQUENCE_DELIVERED` / `SEQUENCE_EMPTY` / `SEQUENCE_INDETERMINATE`; attainability checked (lower bound vs 0, no zero-baseline %) |
| Complexity budget | ✓ 1 test / ≤4 plots / 0 modules — matches design §5 |
| Holdout exclusion | ✓ explicit (final-30% never loaded, incl. 1m bars) |
| Real-price outcome rule | ✓ real OHLC, ATR units; no synthetic prices |
| Gate-threshold calibration | ✓ `net ci_low>0`, α=0.05, margins 0.0125/0.025 — all frozen D0 / EXP-090/094 data-derived, not magic constants |

## Analysis plan (`analysis-plan.md`)

| Check | Verdict |
|---|---|
| Method justification (why + simpler alternative) | ✓ each step; bootstrap lower bound justified over t/MWU (academic-finance pitfalls), substrate-reuse over transcription |
| Assumptions listed, time-ordered fit | ✓ moving-block preserves serial dependence; the ratified estimator |
| Cross-view alignment by timestamp | ✓ domain→1m by `CloseTime`, never bar index |
| Visualisations purposeful (≤4) | ✓ 4 plots each answer a sub-question |
| Interpretation guide pre-defined | ✓ mechanical if-X-then-Y before results |
| Per-stratum endpoints | ✓ binding read per cell; no pooled binding boolean |
| Shape-aware / robust+raw | ✓ net mean AND median co-reported per cell; robust core = mean-AND-median positive; median-fragile cells flagged |
| Budget compliance | ✓ 1/≤4/0 |

## Code (`code/run_experiment.py`)

| Check | Verdict |
|---|---|
| Plan compliance | ✓ exactly the 5 steps + 4 plots; nothing extra |
| Holdout exclusion | ✓ loads via `E90.load_train_1m` (audited TRAIN-only loader); 1m walk clips at TRAIN edge; no holdout path |
| Look-ahead prevention | ✓ reuses the EXP-090 causal `resolve_arm` / 1m engine verbatim; only bars at/after entry |
| Real-price outcome | ✓ `net_return_atr` on real OHLC; ATR units; no HA/Renko prices |
| Timestamp alignment | ✓ engine maps domain→1m by timestamp |
| Type safety / docstrings | ✓ public functions typed + documented; `CellSeq` frozen dataclass |
| NaN handling explicit | ✓ finite guards on every bound; `<2` resolved → `SEQUENCE_INDETERMINATE`, never coerced to pass |
| Edge cases | ✓ empty set → `SEQUENCE_EMPTY`; missing upstream → `FileNotFoundError`; upstream drift → `ValueError`; missing MDE/cost → `ValueError` |
| Separation of concerns | ✓ pure computation / aggregation / plotting / orchestration sectioned (VAL-001 style) |
| No magic numbers | ✓ all constants frozen + documented; margins **loaded from upstream artifacts**, not hardcoded |
| Verdict per-stratum | ✓ emits per-cell `sequence_pass`; `SEQUENCE_DELIVERED`/`EMPTY` is a deliverable-status flag (candidate set exists), **not** a collapsed cross-cell edge PASS/FAIL; candidate set is per-cell. LESSON-001 respected |
| Import side effects | ✓ no dir creation / file write / data load at import (dirs in `run()`); the `E90` import is import-safe (audited EXP-091/094 precedent); `DOMAINS["4h"]=240` is an in-memory patch (EXP-094 precedent) |
| Logging / progress | ✓ `logging` + `tqdm` outer loop; helpers return data; `print` only in `main()` summary |
| Plot memory / no reload | ✓ plots from collected `CellSeq` summaries; no second load/generation |
| Determinism | ✓ seeds via `seed_for("EXP-092",…)`; replay of one 1h + one 4h cell; output + candidate-set sha256 pinned |
| Safe optimization / vectorization | ✓ the sequential 1m engine is untouched; only aggregation/bootstrap vectorized (inside `xen.ass`); `iter_rows` only on ≤16-row upstream summaries |

## Notes (Info — non-blocking)

- **GBPUSD-1h boundary fragility (expected, faithfully handled).** EXP-091 `net_ci_low ≈ 0.0043` (< its 0.0125
  margin). Under EXP-092's independent bootstrap seeds this cell may flip ≤0 → the code records `SEQUENCE_FAIL`
  and excludes it from the pinned set (a **disclosed** boundary finding, not a defect); if it passes, it is
  pinned but **flagged below the EXP-093 margin**. Either path is the honest design and feeds EXP-093 cell
  selection correctly.
- **Candidate-set hash provenance.** `candidate_set.csv` and the canonical-serialization sha256 are both pinned;
  the deterministic sort + per-cell determinism replay make the pin reproducible. Adequate for the EXP-093
  hand-off.

## Verdict

```text
VERDICT: APPROVE
```

No Critical or Warning issues. Scope is single-hypothesis, fully bounded, holdout-fenced, and registry-clean;
the analysis plan uses the ratified non-parametric estimator with pre-defined per-stratum interpretation; the
code implements exactly the plan on the verbatim audited substrate, is holdout-fenced and deterministic, and
emits the binding read per stratum. The sequence rule, cost model, and thresholds are the frozen D0 values
(no goalpost-moving, no new statistic ⇒ no bite-check). Cleared for the manual execution gate.
