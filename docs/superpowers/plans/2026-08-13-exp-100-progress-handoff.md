# EXP-100 Progress Handoff — 264/264 TRAIN done; next = analysis

> **SUPERSEDED 2026-08-13 by AMENDMENT-13.**
> Resume at `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-rerun.md`.
> The two-bar / `AMBIGUOUS_INTRABAR` 264-cell set described below was deleted.
> TEST/holdout remains forbidden.

**Experiment:** EXP-100 — Liquidity-sweep streaming apparatus  
**Family:** `CF-LIQSWP-001/HYP-000`  
**Checkpoint:** `2026-08-11-019-liquidity-sweeps`  
**Pipeline stage:** official 264-cell TRAIN matrix **COMPLETE**

---

## One-line status

**264 / 264 cells published and integrity-passed.** Last cell
`ctrader-ustec-60m-level_close-4h-rolling_252` validated
`2026-08-13T08:10:49Z`. No workers, no leftover `.work` / `.publish`.
Do **not** relaunch the matrix. Next session enters at the estimand /
analysis step.

---

## What the next session must do first

```text
1. Resume via research-pipeline. Announce: execution done; analysis not started.
2. Do not rerun QA, preflight, or the 264-cell grid.
3. Do not inspect TEST / holdout.
4. Per-cell integrity already passed
   (python/experiments/EXP-100/results/execution/full/<cell_id>.json).
5. If a family-level estimand_validation.json is still required by the
   pipeline, run it over the 264 published dirs — do not re-emit.
6. Then data-analyst → analysis.md (coverage / reconciliation, not value).
7. Operator verdict, then experiment-documenter → report.md + indexes.
```

EXP-101–104 stay design-only until the operator opens them. They already
carry AMENDMENT-10/11/12 in the design bodies.

---

## Binding grain (do not relitigate)

| Path | Binding grain |
|---|---|
| Raid start / return / beyond / same-bar ambiguity | Observation bar (15m / 30m / 1h) |
| Confirmation + later endpoint | 1H (15m/30m); **1H and 4H** (1h) |
| TPO bins, max-excursion reset, post-confirm swing | 1-minute |
| Engine input / later fills | 1-minute (AMENDMENT-3) |
| Previous 1H / 4H | Contiguous completed StreamingOHLC window |
| Previous 1D / 1W | NY 17:00 trading day / Mon–Fri week (AMENDMENT-10) |

Golden T1: completed observation bar beyond the level, then a later
observation-bar return. A 1m wick that does not survive the observation OHLC
is not a raid.

---

## Binding methodology

| Item | Rule |
|---|---|
| AMENDMENT-6 | Close-all-eligible reference settlement |
| AMENDMENT-7 | cTrader only: EURUSD, XAUUSD, USTEC |
| AMENDMENT-8 | **NEUTRAL.** SoT raid grain on the cell TF |
| AMENDMENT-9 | **LOOSER** vs 1h→1D. 1h keeps 1H and 4H confirm strata |
| AMENDMENT-10 | **NEUTRAL.** 1D/1W = NY 17:00 trading day / Mon–Fri week |
| AMENDMENT-11 | **NEUTRAL.** Rolling **7 / 14 / 22 / 252**. Matrix **264** |
| AMENDMENT-12 | **NEUTRAL.** Tight if `gap_span < 0.50 * VA_width`. Gap selection stays emptiest **30%** of VA TPO |
| Leak check | One confirmed raid → `VACUOUS_SINGLETON`, not a crash |
| Ledger | **1 looser / 3 tighter / 7 neutral** |
| Integrity | TRAIN only; no holdout; zero-cost |

AMENDMENT-10 exists because contiguous 1,440 / 10,080-minute windows produced
**0** previous-day / previous-week levels on sessioned cTrader minutes. UTC
calendar days would mint Sunday stubs and flip the book at 00:00 UTC. 15m /
1H / 4H StreamingOHLC is unchanged.

AMENDMENT-12 was corrected after a swapped first cut: gap **selection** is
still the emptiest 30% of VA TPO; **tight** is span under 50% of VA width.
The published 264 cells use that corrected pair. Do not analyse any
pre-correction emission.

---

## 264-cell grid (finished)

```text
15m: 3 × 1H × 2 methods × 11 levels = 66
30m: 3 × 1H × 2 methods × 11 levels = 66
1h:  3 × (1H,4H) × 2 methods × 11 levels = 132
Total = 264
```

Levels: PREVIOUS_1H/4H/1D/1W, PREVIOUS_ASIA/EUROPE/AMERICA, ROLLING_7/14/22/252.

Run order used: all 15m, then all 30m, then all 1h. 6 workers, 6-hour cap.
Wall ~56 minutes (`2026-08-13T07:14:53Z` → `08:10:49Z`). 0 failed / timeout /
invalid. 264/264 per-cell gates `blocking_pass=true`.

---

## Artifacts

| Role | Path |
|---|---|
| Emissions | `data/nautilus_runs/EXP-100/full/<cell_id>/` |
| Per-cell gates | `python/experiments/EXP-100/results/execution/full/<cell_id>.json` |
| Journal | `python/experiments/EXP-100/results/execution/full-journal.jsonl` |
| Family `estimand_validation.json` | **absent** — next session may run it over the 264 dirs |
| `analysis.md` / `report.md` / `analysis_code/` | **absent** |

The AMENDMENT-9 288-cell set and its analysis artefacts were deleted before
this rerun. Resume must key off published dir + `blocking_pass=true`.

---

## Notes for analysis (not blockers)

1. `LEVEL_CLOSE` and `BREAKOUT_BAR` still use the same previous-reference
   high/low test. Separate strata; numeric overlap is disclosed.
2. Thin 1h rolling-252 cells can have 0–1 confirmed raids. Leak check is
   vacuous there; do not treat vacuity as a missing emission.
3. Same-bar `AMBIGUOUS_INTRABAR` is expected to dominate raid counts. Primary
   completed-raid estimand excludes those.
4. 1D/1W should now emit objects (AMENDMENT-10). Confirm coverage; do not
   assume the old empty-48 result.
5. QA run 9 judged AMENDMENT-8 / 216 / 1h→1D and is stale for AMENDMENT-10/11/12.
   Do not rewrite it. Fresh QA is not required to analyse already-emitted cells.

---

## Out of scope unless the operator amends again

- Relaunching the 264-cell matrix
- Restoring rolling 16/32/64/128/256
- Restoring contiguous-minute or UTC-calendar 1D/1W
- Changing 15m/1H/4H gap-reset
- Swapping AMENDMENT-12 back (gap 50% / tight 30%)
- TEST / holdout
- Opening EXP-101–104 without an operator ask

---

## Key paths

| Role | Path |
|---|---|
| This handoff | `docs/superpowers/plans/2026-08-13-exp-100-progress-handoff.md` |
| Amendment/rerun note | `docs/superpowers/plans/2026-08-13-exp-100-amendment-10-12-rerun.md` |
| QA log (append-only, stale for 10/11/12) | `python/experiments/EXP-100/qa-review.md` |
| Processor | `python/src/xen/exp100/processor.py` |
| 1D/1W clock | `python/src/xen/exp100/levels.py` |
| Control (singleton-vacuous) | `python/src/xen/exp100/control.py` |
| Matrix / runner | `python/experiments/EXP-100/code/run_matrix.py`, `run_experiment.py` |
| Checkpoint / SoT | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/` |
| Family card | `docs/signal-registry/candidate-families/cf-liqswp-001.md` |
| EXP designs | `python/experiments/EXP-10{0,1,2,3,4}/design.md` |
