# EXP-092 — Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors)

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 Fade Capture-Geometry & Tradability) · **Family / HYP:**
`CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Verdict:** **`SEQUENCE_DELIVERED`** — non-empty hash-pinned candidate set; **11/11 carried cells
`SEQUENCE_PASS`** · **0 counted TEST reads · 0 candidate slots · holdout sealed · audit PASS (0C/0W/4I).**
**Artifacts:** [scope](scope.md) · [analysis-plan](analysis-plan.md) · [code](code/run_experiment.py) ·
[results/](results/) · [audit](audit.md) · [results.md](results.md) ·
[pre-exec governance](governance/pre-execution-review.md)

## Research question

Of the **only exit that survived the EXP-091/094 screen — EXIT-RCT** (the native RSI₂→50
reversion-completion target) — which `(instrument, domain)` cells reach a **TRAIN-only `SEQUENCE_PASS`** (net
per-event expectancy one-sided lower bound `net ci_low_1s > 0` at α=0.05, power-confirmed by the EXP-090/094
MDE), and what **hash-pinned candidate set + phase Holm rule** does that produce for the one-shot EXP-093 TEST?
This is the predeclared candidate-freeze step (design §4, D0 §D6/4b; analog EXP-034/083) — **necessary-but-not-
sufficient for TEST**; it decides no G-021 verdict.

## Scope & exclusions

- **Carried set (frozen by upstream verdicts):** EXIT-RCT on **11 cells** — 1h {EURUSD, GBPUSD, NZDUSD, US2000,
  USTEC} (EXP-091 quorum) + 4h {AUDJPY, EURJPY, EURUSD, GBPJPY, USDCHF, XAUUSD} (EXP-094 `ADMIT_4H` members).
  EXIT-ERT + the 4 conventional arms died at the screen (retained in the file drawer, not reopened); 15m
  contributes nothing (RCT 0/10 on 15m).
- **Data:** VAL-005 INFR-003 5-year 1m bars; domain bars 1h (60-min) + 4h (240-min); real OHLC, ATR(14) units.
- **TRAIN sub-split only** `[0, int(analysis_rows·0.7))`; 1m fill clipped at the TRAIN edge by timestamp. The
  **final-30% global holdout was never loaded**; the analysis-TEST stratum was never sliced (`holdout_untouched=true`,
  `counted_test_reads=0`).
- **No tuning:** RSI 2/10/90, EXIT-RCT target, 2.0×ATR stop, MR-tempo cap, the `D0-amendment-003` cost table,
  Z=1.645, n_boot=10_000 — all frozen. Shared `xen.capgeo_cost.COST_CONSTANTS` not mutated.

## Method

Verbatim reuse of the audited EXP-090 substrate (`build_cell_context`, `resolve_arm`/RCT, the 1-minute intrabar
fill engine, `net_return_atr`) on the 11 carried cells (4h patches `DOMAINS["4h"]=240` as EXP-094): resolve
real EXIT-RCT exits → overlay the conservative cost → **moving-block bootstrap net one-sided lower bound**
(`xen.ass`, seeds fixed). `SEQUENCE_PASS` iff `net ci_low_1s > 0 ∧ finite MDE`. The passing cells (ranked by
`net_ci_low` desc) are written to `candidate_set.csv` and **SHA-256-pinned**; the EXP-093 margin condition
(`ci_low > MDE`) and the mean/median split are co-reported as a non-binding pre-read. Determinism replay on one
1h + one 4h cell. **1 binding test, 4 plots, 0 new modules.**

## Key results

**All 11 carried cells `SEQUENCE_PASS`** (`net ci_low_1s` +0.0044 … +0.135 ATR); candidate set pinned at
`f6427e8342400d46…`. Re-derivation matches the independent EXP-091/094 runs within **≤6.2e-4** on
byte-identical resolved-event counts (1h ~3845–3984, 4h 855–1088), `terminal_fav` ~0.99.

The binding count masks a quality split the margin pre-read exposes (`margin_preread.csv`):

| Tier | Cells | net_ci_low | clears margin | mean & median +? |
|---|---|---|---|---|
| **Robust core (8)** | EURUSD-4h, USDCHF-4h, AUDJPY-4h, XAUUSD-4h, **USTEC-1h**, **US2000-1h**, GBPJPY-4h, EURJPY-4h | +0.050 … +0.135 | ✓ all | ✓ all |
| Mean-carried 1h (2) | EURUSD-1h, NZDUSD-1h | +0.039 … +0.047 | ✓ | ✗ (median −0.005 / −0.010) |
| Fragile 1h (1) | **GBPUSD-1h** | +0.0044 | ✗ (< 0.0125) | ✗ (median −0.052) |

**Mechanism:** the carried cells *were* the upstream net-clearers, so the same bound reproduces `SEQUENCE_PASS`;
4h dominates the ranking because ATR-normalized cost is smaller on the slower domain (gross ~0.27 ATR is
domain-invariant; fixed-bps RT ÷ larger 4h ATR ⇒ smaller cost fraction) — net tradability is set by **cost
geometry**, not signal strength (the EXP-091/094 mechanism, one step further). All six 4h members are mean-AND-
median positive (robust); the 1h tier carries the family's known median-fragility.

Key plots: [`net_ci_low_vs_thresholds.png`](plots/net_ci_low_vs_thresholds.png) (binding bound vs 0 and vs
margin) · [`mean_vs_median.png`](plots/mean_vs_median.png) (the robust-core split) ·
[`robustness_ranking.png`](plots/robustness_ranking.png) (the pinned ranking).

## Audit caveats (audit PASS, 0C/0W/4I)

- The **11/11** count is a benign, *disclosed* two-tier set — the masking check is satisfied because the per-cell
  margin + mean/median flags are reported columns, not hidden. The binding read is per-cell (LESSON-001).
- **Gate-shape:** the binding gate is the **mean** (a location gate); the family is median-fragile on 1h. D5
  designates the mean as binding and co-reports the median, so the shape is visible — the gate is the right
  instrument, with the median as the disclosed shape read.
- **GBPUSD-1h** is pinned (passes the sequence) but **below its EXP-093 margin and median-negative** → should
  **not** be carried to TEST.
- net_ci_low ≤6.2e-4 from upstream (independent seeds); all cells same-sign incl. the boundary cell. Faithful
  reuse, not a coincidental pass.

## Conclusion

**`SEQUENCE_DELIVERED`.** EXIT-RCT's gross availability converts to a power-confirmed, net-of-conservative-cost
TRAIN expectancy lower bound above break-even on **all 11 carried cells**, frozen as a hash-pinned candidate set
+ sized Holm rule. The screen is non-empty, so Phase 021 **advances to the one-shot EXP-093 TEST** rather than
closing at G-021 NOT_TRADABLE. This is a TRAIN eligibility set, **not** an out-of-sample edge claim; the binding
tradability read is EXP-093.

## Signal-registry disposition (registry-relevant)

- **`multiplicity-registry.md`** Phase 021 batch: EXP-092 advanced `PLANNED → SEQUENCE_DELIVERED` (candidate set
  hash `f6427e83…`, 11/11 SEQUENCE_PASS; robust core 8). No new countable item; no item refuted.
- **`candidate-families/cf-mr-001.md`**: EXP-092 outcome section added (candidate set + robust core for EXP-093).
- **`test-read-ledger.md`**: EXP-092 entered as a **TRAIN-only disclosure, not a counted read** — all 48 strata
  (incl. the 11 carried) remain **0/2 open**; the first counted read is the EXP-093 TEST.

## Follow-up (separate future scopes)

1. **EXP-093 (planned one-shot TEST):** carry the **smallest-defensible robust core** from this pinned set
   (mean-AND-median-positive, margin-clearing: USTEC-1h, US2000-1h, the six 4h members), ≤1–2 cells per
   surviving exit/domain at EXP-093's D0, sized to the phase Holm rule. **Exclude GBPUSD-1h.** Each carried
   `(instrument, domain)` stratum spends 1 counted TEST read (0→1; EURUSD-1h and EURUSD-4h are distinct strata).
2. **Deferred (registered):** faster-turnover cost sensitivity, the inert vol-regime partition, the contrarian
   arm, 15m capture — each needs its own dated `D0-amendment-*` + slot decision.
