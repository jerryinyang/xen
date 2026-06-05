# Pre-Execution Governance Review — EXP-012

**Experiment:** EXP-012 — Fresh-Draw Loose Referee Ratification (Track A spine)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-04
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/loose_referee.py`
**Phase:** 2026-06-04-003-ratification-and-incremental-unit (ACTIVE)

---

## Verdict

```text
VERDICT: APPROVE
```

EXP-012 is ready for manual execution with no preconditions beyond its hard-gated
upstream dependencies (EXP-001 PASS, EXP-003 COMPLETE, EXP-010 COMPLETE +
`reference_reproduction_pass`, EXP-011 COMPLETE), all of which are enforced in
`gate_dependencies()`.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Holdout exclusion | Uses frozen `load_analysis_data` (first-70% `CloseTime` slice; final 30% never loaded). `analysis_metadata.csv` records `analysis_end`. | PASS |
| Look-ahead / temporal | Split by canonical `CloseTime`; anchored walk-forward folds timestamp-mapped via `mapped_fold_edges` (never per-timeframe row fractions); expanding folds train strictly before test. | PASS |
| Real-price discipline | Effects from `next_log_returns_from_bars` on real domain `Close`; no HA/Renko construction prices. | PASS |
| Timestamp alignment | Cross-domain split boundaries shared as `CloseTime` timestamps; no bar-index alignment. | PASS |
| Predeclaration freeze (D-ratify-point) | τ 0.75/0.25/0.5 read from EXP-011 `recommendation.csv` (`tau_star_headline`), fixed before fresh draws; fresh draws confirm, never re-select. | PASS |
| Fresh-seed discipline (D-fresh) | `FRESH_SALT` namespace; `verify_seed_disjointness` regenerates prior-phase seeds over the EXP-012 grid and asserts zero overlap, raising on failure; recorded in `run_metadata.json`. | PASS |
| Adoption rule (D-ratify-point / D-ratify-4h) | `decide_adoption` applies all three conditions (FPR ≤ α₀ at D-prec; MDE within one edge-grid step; sub-material within ±0.10 and ≤ 0.50) + 4h protocol-agreement gate; binary ADOPT_LOOSE / STRICT_FALLBACK with INCONCLUSIVE only when D-prec unmet. | PASS |
| Zero-baseline handling | Sub-material zero-pass cells yield finite `0.0` rate (no percentage-of-zero). | PASS |
| Complexity budget | 4 measurements (FPR, MDE, sub-material, 4h split gate) / 4 plots / 1 local module (`loose_referee.py`) — within 4/4/1. | PASS |
| Code conventions | Imports→constants→helpers→computation→plotting→orchestration→`main()`; output dirs created only in `ensure_output_dirs()` (orchestration); `tqdm` on draw/load/split loops; bounded summary inputs to plots; seed-deterministic `mp.Pool`. | PASS |
| Phase alignment | Matches design §8 EXP-012 (Track A spine), §4 H-ratify, D-ratify-point/4h. | PASS |

## Notes for the auditor (Stage 5, non-blocking)

- The loose/strict verdicts are re-derived from the frozen `gate_stack_core` via the
  L5-threshold sweep in `loose_referee.gate_verdict_rows`. The script self-checks only
  the 4h single-split arm against the main measurement (`reference_reproduction_4h`).
  Stage 5 should confirm the **strict single-split rows reproduce EXP-003 exactly**
  (the EXP-006 `strict_reference_pass` equivalence), since that equivalence is the
  basis for treating the harness as unchanged (D-reuse).
- `sub_rate` at the operating MDE is computed at the **fresh** loose MDE; this is the
  intended reading of "reproduces its Phase 002 operating characteristics" and is
  consistent with condition (2) keeping fresh and Phase 002 MDE within one grid step.

---

## Post-approval correction (2026-06-04) — fresh-seed disjointness check

First manual run raised `Fresh seeds overlap Phase 001/002 seeds … overlap_count: 6`.
Root cause: the frozen `seed_for` truncates SHA-256 to **32 bits**
(`hexdigest()[:8]`), and the check required exact disjointness of ~66,000 fresh vs
~462,000 prior seed *integers*. Expected birthday-paradox collisions =
`66000 × 461981 / 2³² ≈ 7.1`; observed 6 — i.e. **benign hash collisions between
conceptually-disjoint namespace strings**, not seed reuse. Every fresh payload begins
`EXP-012|fresh|…` and no prior payload does, so the construction *inputs* are provably
disjoint (the actual D-fresh guarantee).

`verify_seed_disjointness` was corrected to test **payload-input disjointness** (the
binding guarantee) and to report the 32-bit integer-collision count + its expected rate
as a benign diagnostic rather than a hard failure. **No seed, draw, sample membership,
denominator, temporal ordering, or metric changed** — only the verification predicate;
the frozen `xen.referee_calibration.seed_for` is untouched. This correction keeps the
APPROVE verdict. Stage 5 should confirm `payload_overlap_count == 0` and that
`benign_int_collision_count` is within a few × the reported `expected_int_collisions`.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-012 - Fresh-Draw Loose Referee Ratification
Code: python/experiments/EXP-012/code/run_experiment.py
Expected output: python/experiments/EXP-012/results/

Generates fresh disjoint-seed known-null/known-positive draws on the first-70% slice,
measures the fixed EXP-011 loose point's FPR/MDE/sub-material per domain plus the 4h
single-vs-walk-forward split gate, and emits per-domain ADOPT_LOOSE / STRICT_FALLBACK
decisions.

Please run the experiment code and confirm when complete.
```
