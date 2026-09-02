# Handoff — liquidity-sweep VAL re-analysis (2026-09-02)

## Objective

Read-only TRAIN-only re-analysis of frozen EXP-100, without editing EXP-100–104:

- VAL-009: selection/lifecycle and exact repeat count.
- VAL-010: later-swing anatomy.
- VAL-011: TPO geometry, regime transitions, all-raid frequency.

## Safety anchors

- Gate: `VAL-009/results/estimand_validation.json`, `blocking_pass=true`, 264 cells, EURUSD/XAUUSD/USTEC.
- No TEST, holdout, engine run, cost model, P&L claim, or family-status action.
- `ATR_UNDEFINED` stays out of ATR/strong-move reads.
- BB/LC is a duplicate source pair. Raw 264-cell counts are parity only. Breadth = 132 physical settings.
- Contrast tables that say `n_strata=264` are **132 physical settings × 2 sides**, not independent BB/LC replication.
- Duration and all-raid frequency do **not** confirm the strong-move / ATR pattern.

## Completed

1. Designs + this plan: `docs/superpowers/plans/2026-09-02-liquidity-sweep-val-reanalysis.md`.
2. Tests: `python/tests/liquidity_sweep_val/test_val_reanalysis.py` (11 passed).
3. VAL-009 physical grid: 4,920,239 raids; selection sets 394,916 with exactly one primary; 76.2% compete; COMPLETED is 8.0% of rows; prior count 2+ is 78.2% of **all** raids. Raw rows are exactly 2×.
4. VAL-010 physical completed primaries: n=394,607; mean excursion 1.603 ATR; mean swing 3.685; mean surplus 2.082; strong-move 0.831; median duration 5 h. Repeat 1 vs 0: strong-move lower on 255/264 side-strata (mean Δ −0.240); duration split 130/134 (not confirmatory).
5. VAL-011: 132 physical cells; profile join 4,920,239; all-raid starts/1,000 marks HIGH 1451.3, MID 1276.6, LOW 1244.5. HIGH vs MID: strong-move **down** (257/264), duration **up** (219/264). Confirmation regime is null in the nine largest transition buckets.
6. Live-load bug: VAL-011 omitted `swing_duration_ns` so the contrast helper crashed after unit tests. Fixed (`RAID_COLUMNS`); regression test added; script rerun OK.
7. Analysis notes written: `VAL-009/analysis.md`, `VAL-010/analysis.md`, `VAL-011/analysis.md`. No `report.md` — that waits for an operator verdict.

## Current stop / next action

Analyst artefacts for the three VALs are in place. Safest next step is **operator read of the three `analysis.md` files**.

Optional follow-ups (not started):

- Why `confirmation_regime` is null on most VAL-011 rows (emission field vs projection).
- Index / `report.md` only after an operator verdict.
- Do not treat a new EXP-105 as required for these questions; they used the frozen emission.

## Verify

```
uv run --directory python pytest tests/liquidity_sweep_val/test_val_reanalysis.py -q
# last: 11 passed
uv run --directory python python ../python/experiments/VAL-011/analysis_code/interrogate.py
# last: exit 0, wrote outcome_regime_contrasts
```

## Commit hygiene

- EXP-101–104 completed artefacts: `184304d`.
- VAL work (designs, scripts, results JSON, analysis.md, tests, this handoff) is a **separate** commit from those artefacts.
- Do **not** stage: `.jspace/`, `python/experiments/_live-101-104.exit`, or the four ~404 MB `EXP-101..104/results/analysis_results.json` files unless an operator explicitly wants them.
