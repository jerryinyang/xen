# Data Analysis: VAL-009

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled **observed** (read from `raids.parquet` via `analysis_code/interrogate.py`) or
**inference** (a mechanism reading that is not itself measured). The recommendation in §7
is non-final and applies only to VAL-009's characterisation question. No TEST, holdout,
engine rerun, EXP-100–104 edit, or family-status change.

ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.

**Grid rule.** Raw 264 source cells duplicate `BREAKOUT_BAR` / `LEVEL_CLOSE`. Breadth claims
use the physical grid (132 settings). Raw counts are parity only.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation | **PASS** | `python/experiments/VAL-009/results/estimand_validation.json`: `blocking_pass=true`, `n_cells=264`, instruments EURUSD/XAUUSD/USTEC |
| Zero-cost | **PASS** | gate `no_cost_charged`; no `ok: false` in this copy |
| Provenance | **PASS for TRAIN fence** | `sweep_ts_ns <= 1700611200e9`; no TEST/holdout path |
| Leak tripwire | **N/A as a new claim** | inherited EXP-100 future-destroy remains source-validity only |
| Holdout untouched | **PASS** | `data/nautilus_runs/EXP-100/full` only |
| Price-primary | **PASS as event-study emission** | Nautilus raid rows; `n_fills` not used |
| No local accounting | **PASS** | no `VAL-009/code/`; analyst script only |

## 2. Question list

1. Gate / zero-cost / TRAIN fence? **ANSWERED** §1.
2. P&L / occupancy / Sharpe / PSR? **UNANSWERED — N/A** (no trade object).
3. Lifecycle mix on the physical grid? **ANSWERED** §3–4.
4. Is primary selection a singleton per competition set? **ANSWERED** §3.
5. How common is competition, and how old are levels? **ANSWERED** §3.
6. Exact prior-raid count mix? **ANSWERED** §3.
7. Do raw 264-cell counts double the physical facts? **ANSWERED** §4.
8. What would make headlines wrong? **ANSWERED** §5.

## 3. Evidence FOR the characterisation question

Observed, physical grid (`selection_summary.json`):

| Fact | Value |
|---|---|
| Raid rows | 4,920,239 |
| Status mix | FAILED_BREAKOUT 2,351,450 (47.8%); CONFIRMED_NON_PRIMARY 2,158,300 (43.9%); COMPLETED 394,663 (8.0%); RIGHT_CENSORED_* 15,826 |
| Selection sets | 394,916; **exactly one primary in every set** |
| Competing sets | 300,982 / 394,916 (76.2%); max set size 331 |
| Exact prior count | 0: 562,058 (11.4%); 1: 508,372 (10.3%); 2+: 3,849,809 (78.2%) |
| Level age | median 7.5 h; mean 8.65 d; p95 34.7 d |

**Inference (not measured as a trade rule):** completed primaries are a selected minority sitting on top of a much larger failed/non-primary population. Outcome studies that start from completed primaries are not a census of all emitted raids.

## 4. Evidence AGAINST over-reading the same facts

- Raw source rows are exactly 2× physical (`n=9,840,478`; sets 789,832). Treating “264 cells agree” as independent replication **overstates breadth**.
- Repeat-count 2+ is the majority of **all raid rows**, not of completed primaries. VAL-010’s completed-primary repeat bands are a different population.
- Level-age mean ≫ median: a long tail of old levels; a pooled “typical age” is not homogeneous.
- Competition-set size 331 is a tail; most competing sets can be small. This census does not describe within-set composition beyond “exactly one primary”.
- No ATR / strong-move / duration claim is licensed here.

## 5. What would make the headline numbers wrong (N7)

| Headline | Probe | Result |
|---|---|---|
| Exactly one primary per set | merge sets across cells or sides | unit test: different `source_cell` stay separate; non-primary terminal maps to primary confirmation |
| Physical n = raw/2 | fail to collapse only BB/LC | observed exact 2.0 ratio |
| TRAIN-only | rows with `sweep_ts_ns` after fence | filter is in `interrogate.py` |

## 6. Anomalies & open questions

- Why 76% of selection sets compete, yet only 8% of rows complete: composition of competing sets (how many non-primaries per primary) is not tabulated beyond max size.
- Exact count 2+ is coarse; a trade-facing “first raid vs later raid” rule still needs VAL-010’s completed-primary anatomy, not this all-row mix.

## 7. Recommended verdict (characterisation only — NOT final, NOT family)

- Recommendation: the selection question is **answered as a description**. Completed primaries are an 8% selected slice; every selection set has exactly one primary; most sets compete; most emitted raids are not first raids.
- Driven by: status mix; singleton-primary sets; raw=2× physical.
- Would change if: a join-key defect merged distinct cells, or BB/LC failed to collapse.
- Hand-off: operator decides whether EXP-101–104 language should cite this selected-slice fact. No family action.
