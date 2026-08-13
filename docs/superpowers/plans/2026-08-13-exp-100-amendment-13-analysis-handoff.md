# EXP-100 Progress Handoff — AMENDMENT-13 264/264 TRAIN done; next = analysis

> **Authoritative resume document as of 2026-08-13T14:10Z.**
> Replaces `2026-08-13-exp-100-amendment-13-rerun.md` and the older
> AMENDMENT-10/11/12 handoff. TEST/holdout remains forbidden.

**Experiment:** EXP-100 — Liquidity-sweep streaming apparatus
**Family:** `CF-LIQSWP-001/HYP-000`
**Checkpoint:** `2026-08-11-019-liquidity-sweeps`
**Pipeline stage:** AMENDMENT-13 official 264-cell TRAIN matrix **COMPLETE**

---

## One-line status

**264 / 264 cells published and integrity-passed.** Last cell validated
`2026-08-13T13:05:03Z`. Wall ~3h 16m (`09:49:16Z` → `13:05:03Z`).
No workers, no leftover `.work` / `.publish`. 0 failed / timeout / invalid.
Do **not** relaunch the matrix. Next session enters at the family estimand
gate, then analysis.

---

## What the next session must do first

```text
1. Resume via research-pipeline. Announce: AMENDMENT-13 execution done; analysis not started.
2. Do not rerun QA, preflight, or the 264-cell grid.
3. Do not inspect TEST / holdout.
4. Do not restore the deleted two-bar / AMBIGUOUS_INTRABAR emissions.
5. Per-cell integrity already passed
   (python/experiments/EXP-100/results/execution/full/<cell_id>.json).
6. Run family estimand_validation over the 264 published dirs — do not re-emit.
7. Then data-analyst → analysis.md (coverage / reconciliation, not value).
   Analyst scripts under python/experiments/EXP-100/analysis_code/ can be reused
   with light edits (AMBIGUOUS_INTRABAR is retired).
8. Operator verdict, then experiment-documenter → report.md + indexes.
```

EXP-101–104 stay design-only until the operator opens them. They already
carry AMENDMENT-13 in the design bodies. They read this emission; they do
not launch another Nautilus grid.

---

## Binding grain (do not relitigate)

| Path | Binding grain |
|---|---|
| Raid start / return / beyond | Observation bar (15m / 30m / 1h) |
| Same-bar return | Recorded; raid **stays live** (AMENDMENT-13) |
| Confirmation + later endpoint | 1H (15m/30m); **1H and 4H** (1h) |
| TPO bins, max-excursion reset, post-confirm swing | 1-minute |
| Engine input / later fills | 1-minute (AMENDMENT-3) |
| Previous 1H / 4H | Contiguous completed StreamingOHLC window |
| Previous 1D / 1W | NY 17:00 trading day / Mon–Fri week (AMENDMENT-10) |

A completed observation bar that goes **strictly beyond** the level starts a
live raid. Same-bar snap-back does **not** close it. `AMBIGUOUS_INTRABAR` is
retired. Confirmation or fail on the reference clock settles the raid. A 1m
wick that does not survive the observation OHLC is not a raid.

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
| AMENDMENT-13 | **LOOSER.** Beyond the level starts a live raid; same-bar return does not close it |
| Ledger | **2 looser / 3 tighter / 7 neutral** |
| Integrity | TRAIN only; no holdout; zero-cost |

The published 264 cells are the AMENDMENT-13 object. Do not analyse any
pre-13 emission.

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
Wall ~196 minutes. 264/264 per-cell gates `blocking_pass=true`.

---

## Artifacts

| Role | Path |
|---|---|
| Emissions | `data/nautilus_runs/EXP-100/full/<cell_id>/` |
| Per-cell gates | `python/experiments/EXP-100/results/execution/full/<cell_id>.json` |
| Journal | `python/experiments/EXP-100/results/execution/full-journal.jsonl` |
| Family `estimand_validation.json` | **absent** — next session runs it over the 264 dirs |
| `analysis.md` / `report.md` | **absent** |
| `analysis_code/` | present; reuse with AMENDMENT-13 edits |

---

## What this emission can and cannot answer

**Covered (no new engine run):** frozen EXP-101–104 — later-swing by level
degree, prior raid count, tight vs non-tight gap at confirmation, volatility
regime. Gap label + swing summaries are on the raid / TPO rows.

**Not stored:** the 1-minute price path from raid → confirm or confirm →
swing end. A “did price retrace into the value-gap box?” question needs a
new column or a later 1m catalog pass. Do not invent it from `swing_extreme`
alone.

`LEVEL_CLOSE` and `BREAKOUT_BAR` still use the same previous-reference
high/low test. Separate strata; numeric overlap is disclosed.

---

## Out of scope unless the operator amends again

- Relaunching the 264-cell matrix
- Restoring `AMBIGUOUS_INTRABAR` / two-bar raid close
- TEST / holdout
- Opening EXP-101–104 without an operator ask
- Adding path / gap-retrace columns mid-analysis

---

## Key paths

| Role | Path |
|---|---|
| This handoff | `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-analysis-handoff.md` |
| Amendment/rerun note | `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-rerun.md` |
| QA log (append-only, stale for 13) | `python/experiments/EXP-100/qa-review.md` |
| Processor | `python/src/xen/exp100/processor.py` |
| Matrix / runner | `python/experiments/EXP-100/code/run_matrix.py`, `run_experiment.py` |
| Checkpoint / SoT | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/` |
| Family card | `docs/signal-registry/candidate-families/cf-liqswp-001.md` |
| EXP designs | `python/experiments/EXP-10{0,1,2,3,4}/design.md` |
