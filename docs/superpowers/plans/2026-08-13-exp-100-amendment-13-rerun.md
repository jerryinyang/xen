# EXP-100 AMENDMENT-13 rerun — same-bar pierce stays live

> **SUPERSEDED 2026-08-13T14:10Z.**
> Resume at `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-analysis-handoff.md`.
> The 264-cell AMENDMENT-13 TRAIN matrix described below is COMPLETE.
> TEST/holdout remains forbidden.

**Experiment:** EXP-100 — Liquidity-sweep streaming apparatus
**Family:** `CF-LIQSWP-001/HYP-000`
**Checkpoint:** `2026-08-11-019-liquidity-sweeps`
**Change:** AMENDMENT-13 (LOOSER). Ledger **2L / 3T / 7N**.

## Rule

A completed observation bar that goes **strictly beyond** the level starts a
live raid. Same-bar return is recorded and does **not** close it.
`AMBIGUOUS_INTRABAR` is retired. Confirmation or fail on the reference clock
settles the raid. A 1-minute wick that is not the observation OHLC is still
not a raid (AMENDMENT-8 grain unchanged).

The previous 264-cell TRAIN set used the two-bar / same-bar-close object. Those
emissions and their analysis outputs are deleted. Do not mix them with the new
run.

## Why a rerun

Same-bar rows were closed on the spot. The old files have the pierce and
nothing after it. Later confirmation cannot be rebuilt from those cells.

## Next session

```text
1. Do not restore the deleted two-bar emissions.
2. If the matrix is still running, wait; do not launch a second copy.
3. After 264/264 VALIDATED, run family estimand_validation, then analysis.
4. EXP-101–104 stay design-only until the operator opens them.
```

## Binding grain (unchanged except raid lifetime)

| Path | Binding grain |
|---|---|
| Raid start / return / beyond | Observation bar (15m / 30m / 1h) |
| Same-bar return | Recorded; raid stays live (AMENDMENT-13) |
| Confirmation + later endpoint | 1H (15m/30m); 1H and 4H (1h) |
| TPO bins, max-excursion reset, post-confirm swing | 1-minute |
| Previous 1D / 1W | NY 17:00 trading day / Mon–Fri week |

## Key paths

| Role | Path |
|---|---|
| This note | `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-rerun.md` |
| Processor | `python/src/xen/exp100/processor.py` |
| Matrix / runner | `python/experiments/EXP-100/code/run_matrix.py`, `run_experiment.py` |
