# Pre-Execution Governance Review — EXP-014

**Experiment:** EXP-014 — Incremental Referee Golden-Fixture Correctness (Track B logic gate)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-04
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/incremental_referee.py`
**Phase:** 2026-06-04-003-ratification-and-incremental-unit (ACTIVE)

---

## Track B predeclaration confirmation (operator-gated)

On **2026-06-04** the operator confirmed **D-incr-form / D-incr-substrate /
D-incr-legs** as implemented (see EXP-013 review for the full record). EXP-014 is the
correctness gate for the **D-incr-legs** mapping specifically — the confirmed orthogonal
legs (L2 = standalone-C significance, L3 = incremental-beyond-R significance, L4 = no
material sign-reversal across segments, L5 = point-magnitude > materiality).

```text
PHASE003-TRACKB-PREDECLARATION-CONFIRMED
```

(Satisfies `find_predeclaration_token()` in EXP-014's `run_experiment.py`.)

---

## Verdict

```text
VERDICT: APPROVE
```

Execution preconditions: EXP-013 `overall_status == PASS` (hard-gated in
`require_exp013_pass()`) and the Track B token above. Both are enforced in `main()`,
which writes BLOCKED metadata and replays no fixtures otherwise.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Hypothesis quality | Deterministic logic-correctness claim; falsifiable on any verdict/leg mismatch or missing leg exposure. | PASS |
| Coverage matrix ↔ code | The 7 fixtures' expected verdicts and L1–L5 states match the `scope.md` coverage matrix exactly (`all_pass`, L1–L5 single-leg fails, `redundant_shared_structure`). | PASS |
| Leg exposure (no short-circuit) | `evaluate_fixture` iterates all five `LEG_NAMES` and records `exposed`/`actual`/`expected` per leg regardless of earlier failures; `all_legs_exposed_no_short_circuit` asserted. | PASS |
| L3 reference-control generalization | `l3_reference_control_fail` (standalone-looking edge, no incremental) and `redundant_shared_structure` reachable because L3/L5 are orthogonal (wide-CI point > materiality with CI-lower ≤ 0). | PASS |
| Holdout / data | In-memory deterministic fixtures; no Parquet read; holdout untouched. | PASS |
| Real-price discipline | Fixture returns represent real-price return contributions; no chart-construction prices. | PASS |
| Determinism | Seeded `np.random.default_rng(fixture.seed)` + fixed `BOOTSTRAP_SEED`; reproducible. | PASS |
| Complexity budget | 2 checks (verdict reproduction, leg exposure) / 3 plots / 0 new modules — within 2/3/1. | PASS |
| Code conventions | Imports→constants→fixtures→evaluation→plotting→`main()`; output dirs in orchestration; concise logging. | PASS |
| Phase alignment | Matches design §8 EXP-014, §4 H-incr-correct, D-incr-legs. | PASS |

## Note for the auditor (Stage 5, non-blocking)

- The fixture expected leg states depend on the fixed construction seeds and
  `BOOTSTRAP_SEED`. Stage 5 should confirm each expected state follows from the
  fixture's construction parameters (drifts/noise/reversal switch) by first principles,
  not merely by reproducing the code's own output — i.e. that the fixtures genuinely
  isolate each leg.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-014 - Incremental Referee Golden-Fixture Correctness
Code: python/experiments/EXP-014/code/run_experiment.py
Expected output: python/experiments/EXP-014/results/

Replays 7 deterministic golden fixtures through the incremental referee, checking every
hand-reasoned verdict and L1-L5 leg state reproduces and all five legs are exposed
(no short-circuit).

Please run the experiment code and confirm when complete (EXP-014 must reach
overall_status PASS before EXP-015).
```
