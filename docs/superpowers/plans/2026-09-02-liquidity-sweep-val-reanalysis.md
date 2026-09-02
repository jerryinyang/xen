# Liquidity-sweep VAL re-analysis plan

**Goal:** Characterise the frozen EXP-100 raid emission more deeply without changing EXP-100–104, emitting new evidence only.

**Source:** `data/nautilus_runs/EXP-100/full/`; TRAIN-only; family gate `python/experiments/EXP-100/results/estimand_validation.json` must pass before every read.

## Boundaries

- No engine execution, TEST, holdout, costs, P&L, tradability, family disposition, or edits to EXP-100–104.
- Exclude every `profile_undefined_reason=ATR_UNDEFINED` row from ATR-normalised and `strong_move` reads.
- Keep `BREAKOUT_BAR` / `LEVEL_CLOSE` as duplicate source representations, not independent replication.

## Tasks

1. VAL-009: describe selection/lifecycle, competition sets, level age, and exact repeat count.
   Verify: unit test on a small raid frame; full source attestation; machine-readable results.
2. VAL-010: decompose later swing into initial excursion, later swing, surplus, and path-retrace status.
   Verify: unit test on a hand-built completed-primary frame; full source attestation; machine-readable results.
3. VAL-011: describe continuous TPO geometry, regime transitions, and a design-faithful all-raid frequency census.
   Verify: unit test on a one-mark/one-raid frame; full source attestation; machine-readable results.
4. Assemble three neutral analyses with evidence for and against each stated question; no verdict or family action.
