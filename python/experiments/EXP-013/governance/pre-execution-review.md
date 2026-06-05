# Pre-Execution Governance Review — EXP-013

**Experiment:** EXP-013 — Incremental Substrate Validation (Track B P0 gate)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-04
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/incremental_referee.py`
**Phase:** 2026-06-04-003-ratification-and-incremental-unit (ACTIVE)

---

## Track B predeclaration confirmation (operator-gated)

The Phase 003 design (`§2`, ⚠ items) requires operator confirmation or override of
**D-incr-form**, **D-incr-substrate**, and **D-incr-legs** before any Track B
measurement exists. On **2026-06-04** the operator **confirmed all three as
implemented** in `python/src/xen/incremental_referee.py`, including the two refinements
of the literal checkpoint defaults:

- **D-incr-form** — incremental cost charged as `cost_bps / episode_length`; the
  redundancy null therefore reads a small **negative** cost-drag (never a phantom
  positive), and high-cost short-episode cells (e.g. BTCUSD 1h/4h) are reported as
  `NULL_COST_DOMINATED` rather than tight-≈0. The binding control — **no phantom
  POSITIVE incremental edge from shared structure** — holds regardless.
- **D-incr-substrate** — blockwise latent state (episode lengths 5m=24/1h=8/4h=4),
  four equal-share masks (R_only/C_change/overlap/inactive), C-change denominator,
  redundancy null = no planted marginal drift.
- **D-incr-legs** — orthogonal leg mapping (L2 = standalone-C significance,
  L3 = incremental-beyond-R significance, L4 = no material sign-reversal across
  segments, L5 = point-magnitude > materiality).

This confirmation freezes the three items for Phase 003. Any later change requires a
new dated design amendment authored before the dependent experiment's results are read.

```text
PHASE003-TRACKB-PREDECLARATION-CONFIRMED
```

(The token above satisfies `find_predeclaration_token()` in EXP-013's
`run_experiment.py`, unblocking measurement.)

---

## Verdict

```text
VERDICT: APPROVE
```

Execution precondition: EXP-001 PASS (hard-gated in `require_exp001_pass()`) and the
Track B token above. EXP-013 is the Track B P0 gate; EXP-014/015 depend on it PASSing.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Holdout exclusion | `load_analysis_data` first-70% slice; `analysis_metadata.csv` records `analysis_end`; holdout never loaded. | PASS |
| Look-ahead / temporal | R/C positions blockwise from seeded latent state (independent of returns); marginal series chronological; bootstrap block length on train, CI on test. | PASS |
| Real-price discipline | Marginal edge from real domain `Close` returns; planted positive drift is the standard closed-form substrate injection (EXP-001 family), labelled known-truth. No HA/Renko prices. | PASS |
| Redundancy-null control (binding) | `redundancy_null_rows` flags PHANTOM_EDGE iff CI-lower > materiality, or point > tol with entirely-positive CI; cost-drag-negative cells = `NULL_COST_DOMINATED` (reported, not a failure). Verdict counts only recovery FAIL or PHANTOM_EDGE as substrate breakage — matches H-incr-substrate's falsification (spurious *positive*). | PASS |
| Recovery tolerance | `max(0.5 bps, 15% of m)` (EXP-001 family); across-draw mean vs planted m. | PASS |
| Zero-baseline handling | Empty denominator → finite `nan`/`0.0` guards; no percentage-of-zero. | PASS |
| Predeclaration gate enforced in code | `main()` writes BLOCKED metadata and produces no measurement if the token is absent. | PASS |
| Complexity budget | 3 checks (recovery, redundancy, integrity) / 4 plots / 1 module — within 3/4/1. | PASS |
| Code conventions | Imports→constants→helpers→checks→plotting→`main()`; output dirs in orchestration; `tqdm` on instrument loop; bounded plot inputs. | PASS |
| Phase alignment | Matches design §8 EXP-013 (Track B P0), §4 H-incr-substrate, D-incr-substrate. | PASS |

## Note for the auditor (Stage 5, non-blocking)

- The symmetric scope null-tolerance band is partly superseded by the predeclared
  negative cost-drag (D-incr-form). Stage 5 should confirm every reported
  `NULL_COST_DOMINATED` cell has a CI-lower ≤ 0 (no positive phantom) and that no cell
  silently flips to a positive reading.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-013 - Incremental Substrate Validation
Code: python/experiments/EXP-013/code/run_experiment.py
Expected output: python/experiments/EXP-013/results/

Builds seeded known-truth R/C substrates on the first-70% slice; recovers each planted
marginal edge on the C-change denominator within max(0.5 bps, 15% of m) and checks the
redundancy null reads no phantom positive incremental edge.

Please run the experiment code and confirm when complete (EXP-013 must reach
overall_status PASS before EXP-014).
```
