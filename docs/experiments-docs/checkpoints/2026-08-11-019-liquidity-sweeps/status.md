# Checkpoint 019 — Current status

**Recorded:** 2026-09-02 (EXP-101–104 close); EXP-100 block unchanged from 2026-08-13
**Checkpoint:** OPEN
**Family:** `CF-LIQSWP-001` — `REGISTERED` (unchanged)

## EXP-100 disposition

EXP-100 is completed and operator-approved on the retained 264-cell AMENDMENT-14 TRAIN run.
The binding operator verdict is:

> “retain the current run; ATR-undefined excursion values are limited/invalid and must be excluded from all interpretations; make no implementation changes; perform no reruns/emissions.”

Accordingly, ATR-undefined excursion values are excluded. Coverage, chronology, lifecycle,
status, attribution, and the future-destroy result for its finite normalized population are
retained. The future-destroy control is unaffected because ATR-undefined rows are outside that
population.

Prevalence: 780/9,840,478 emitted raid rows affected (0.007926%); 390 unique affected objects
after method deduplication; 84 affected primary/completed rows; median understatement among
affected rows 71.43%.

## EXP-101–104 disposition (2026-09-02)

Operator completed the four characterisation experiments on the retained EXP-100 TRAIN
emission. Binding operator call: treat 101–104 as descriptions of selected completed
raids, not as an edge; annotate 102/104 to ATR/strong-move only; keep 101/103
inconclusive; do not change family status.

| ID | Operator record |
|---|---|
| EXP-101 | INCONCLUSIVE |
| EXP-102 | COMPLETED — leftover ATR / strong-move description only; duration does not confirm |
| EXP-103 | INCONCLUSIVE |
| EXP-104 | COMPLETED — leftover ATR / strong-move description only; duration and frequency do not confirm |

Independent physical settings collapse BB/LC (about 132, not 264 methods). VAL-009/010/011
are the supporting characterisation reads.

## Checkpoint boundary

- These are experiment-level completions, not a family promotion, retirement, or closure.
- `CF-LIQSWP-001` remains `REGISTERED`; no checkpoint family decision exists.
- No retrospective is issued because checkpoint 019 remains open.
- No TEST or holdout read was used; counted TEST reads remain 0.

See [EXP-100 report](../../../../python/experiments/EXP-100/report.md),
[EXP-101](../../../../python/experiments/EXP-101/report.md),
[EXP-102](../../../../python/experiments/EXP-102/report.md),
[EXP-103](../../../../python/experiments/EXP-103/report.md),
[EXP-104](../../../../python/experiments/EXP-104/report.md), and
[family detail](../../families/cf-liqswp-001.md).
