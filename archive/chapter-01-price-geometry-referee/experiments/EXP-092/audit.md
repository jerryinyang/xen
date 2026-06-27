# Audit Report: Experiment EXP-092

**Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors) → hash-pinned candidate set + Holm rule**
Phase 021 · `CF-MR-001` · `HYP-002` · TRAIN-only · 0 reads / 0 slots · holdout sealed.

## Summary

- **Verdict**: **PASS**
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4
- **Experiment verdict reproduced**: `SEQUENCE_DELIVERED` — **11/11 carried cells `SEQUENCE_PASS`**;
  candidate set sha256 `f6427e83…` (re-derived from the canonical serialization, **MATCH**); determinism PASS
  (USTEC-1h, EURUSD-4h); `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`.

The implementation is a faithful, deterministic re-derivation of the binding net lower bound on the inherited
EXIT-RCT survivor cells, with a correctly hash-pinned candidate set + margin pre-read. Numeric reproduction is
exact-to-seed against the independent upstream computations. No verdict-material finding.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | SEQUENCE_PASS logic = `net_ci_low>0 ∧ finite margin` verified consistent on all 11 cells; ranking monotone-desc; margin/mean-median flags logically correct (re-derived below) |
| `code/run_experiment.py` | Edge cases | PASS | `<2` resolved → `SEQUENCE_INDETERMINATE`; empty set → `SEQUENCE_EMPTY`; missing upstream → `FileNotFoundError`; **upstream-drift → `ValueError`** (carried set re-derived from EXP-091/094 and asserted == frozen); missing MDE/cost → `ValueError` |
| `code/run_experiment.py` | Type safety / docstrings | PASS | public functions typed + documented; `CellSeq` frozen dataclass |
| `code/run_experiment.py` | NaN handling | PASS | finite guards on every bound; no silent coercion to pass |
| `code/run_experiment.py` | Holdout exclusion | PASS | loads via audited `E90.load_train_1m` (TRAIN-only slice); 1m walk clips at TRAIN edge by timestamp; no holdout path; metadata `holdout_untouched=true` |
| `code/run_experiment.py` | Loader ordering | PASS | inherited EXP-090 loader sorts by `CloseTime` before the first-70% / TRAIN slice |
| `code/run_experiment.py` | Look-ahead / temporal | PASS | reuses the EXP-090 causal `resolve_arm` + 1m engine verbatim; only bars at/after entry; domain→1m by timestamp, never bar index |
| `code/run_experiment.py` | Real-price discipline | PASS | `net_return_atr` on real OHLC; ATR(14) units; no HA/Renko/synthetic prices |
| `code/run_experiment.py` | Memory / performance | PASS | per-cell summaries collected; plots from `CellSeq` (no reload); `iter_rows` only on ≤16-row upstream CSVs |
| `code/run_experiment.py` | Safe optimization | PASS | sequential 1m engine untouched; only aggregation/bootstrap vectorized inside `xen.ass` |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` outer loop over 11 cells; helpers quiet |
| `code/run_experiment.py` | Logging/output | PASS | `logging` + concise `main()` summary |
| `code/run_experiment.py` | Organization / import side effects | PASS | VAL-001 sectioned; dirs created only in `run()`; `E90` import is import-safe (EXP-091/094 precedent); `DOMAINS["4h"]=240` is an in-memory patch (EXP-094 precedent) |
| `code/run_experiment.py` | Plot data reuse | PASS | 4 plots from collected summaries; no heavy reload |
| `code/run_experiment.py` | Determinism | PASS | seeds via `seed_for("EXP-092",…)`; replay of one 1h + one 4h cell byte-identical; candidate sha256 stable |
| `code/run_experiment.py` | Scope/plan compliance | PASS | exactly the 5 plan steps + 4 plots; RCT-only; no extra analyses; 1 test / 4 plots / 0 modules |

## Numerical Validation

### Spot checks / independent re-derivation

- **SEQUENCE_PASS logic** re-evaluated from `sequence_per_cell.csv`: `sequence_pass == (net_ci_low>0 ∧
  margin>0)` for **all 11/11** cells. ✓
- **Cross-check vs independent upstream computations** (EXP-091 1h, EXP-094 4h — separate runs, separate
  seeds): per-cell `net_ci_low` agrees within **|Δ| ≤ 6.2e-4** (max EURUSD-4h −0.00062; EURUSD-1h Δ=+2e-5),
  **every cell same sign**. The seed-level difference is the only delta — confirms the substrate reuse is
  faithful and the bound is not an artifact. ✓
- **Resolved-event counts are byte-identical** to upstream: 1h {EURUSD 3845, GBPUSD 3889, NZDUSD 3984, US2000
  3883, USTEC 3898} == EXP-091; 4h {AUDJPY 1088, EURJPY 1045, EURUSD 1004, GBPJPY 969, USDCHF 1011, XAUUSD
  855} == EXP-094. The entry/exit/fill machinery reproduces the exact same populations. ✓
- **Candidate ranking** monotone non-increasing by `net_ci_low` (n=11). ✓
- **Margin pre-read + mean-median flags** re-derived: `clears_margin == (net_ci_low>margin)` and
  `mean_and_median_pos == (net_mean>0 ∧ net_median>0)` correct on all 11; the only `clears_margin=false` cell
  is GBPUSD-1h (0.00441 < 0.0125); the three `mean_and_median_pos=false` cells are EURUSD-1h / NZDUSD-1h /
  GBPUSD-1h (median<0). ✓
- **Candidate sha256 reproduces** from the canonical serialization → `f6427e83…` == metadata. ✓

### Range checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `resolved_frac` | (0,1], ~0.99 (RCT) | 0.986–0.998 | YES |
| `terminal_fav` | ~0.99 (RCT hits target) | 0.990–0.997 | YES |
| `tie_break_frac` | ~0 (adverse-first ties rare) | 0.0–0.0005 | YES |
| `net_ci_low` (carried) | > 0 (net-cleared upstream) | +0.0044…+0.135 | YES |
| `holding_days_mean` | 1h ~0.05d, 4h ~0.2d | 1h 0.049–0.052; 4h 0.20–0.22 | YES |

### Statistical sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| 11/11 net_ci_low>0 | all carried cells | YES | carried set = upstream net-clearers by construction; re-derivation reproduces |
| 4h dominates ranking | ranks 1–4,7,8 = 4h | YES | larger 4h ATR ⇒ fixed-bps cost is a smaller ATR fraction ⇒ larger net + tighter bound (EXP-091/094 mechanism) |
| GBPUSD-1h weakest | ci 0.0044, med −0.052 | YES | matches EXP-091 boundary-fragile flag |

## Verdict Forensics

**Mechanism (why `SEQUENCE_DELIVERED`, 11/11).** The carried cells are, by construction, the EXP-091 1h
net-clearing quorum (5/5) and the EXP-094 4h powered members (6/6, `ADMIT_4H`). EXP-092 re-derives the *same*
binding net-expectancy lower bound on the *same* resolved-event populations (counts byte-identical), so every
carried cell reproduces `net_ci_low>0` → `SEQUENCE_PASS`. The candidate set is the union of the two upstream
survivor sets, ranked by `net_ci_low`. The 4h cells rank highest because ATR-normalized cost is smaller on the
slower domain (gross ≈ domain-invariant ~0.27 ATR; fixed-bps RT ÷ larger 4h ATR ⇒ smaller cost fraction) —
the identical cost-geometry mechanism EXP-091/094 established. Nothing new is discovered here; this is the
predeclared candidate-freeze step.

**Per-stratum re-derivation + masking check (REQUIRED — done autonomously).** The binding adjudication is
**per cell**, not a pooled boolean — each of the 11 strata was re-derived independently above and the verdict
holds cell-by-cell. The pooled headline **"11/11 SEQUENCE_PASS" does mask a real two-tier quality split**, and
the experiment **affirmatively surfaces it** (not hidden) via `margin_preread.csv` + the candidate flags:
- **Robust core (8 cells)** — all six 4h members + USTEC-1h + US2000-1h — clear the EXP-093 margin **AND** are
  mean-AND-median positive.
- **Mean-carried / fragile 1h tier (3 cells)** — EURUSD-1h & NZDUSD-1h clear the margin but are **median-negative**
  (mean-carried); **GBPUSD-1h** is **below its margin (0.0044<0.0125) AND median-negative** — the single
  weakest cell, exactly the EXP-091 boundary-fragile flag.
The masking is benign and disclosed: SEQUENCE_PASS correctly admits all net-clearers into the *pinned set*
(D6/4b is `net_ci_low>0`, mean), and the per-cell margin + mean/median flags hand EXP-093's D0 the basis to
carry only the **smallest-defensible robust subset**. No cell where the pooled and per-stratum pictures
disagree *silently* — the disagreement is itself a reported column.

**Gate-shape check.** The binding gate is the **net mean** lower bound — a **location** gate. The family is
median-fragile (mean>0, median<0 on 3 of the 5 1h cells), an asymmetric/right-skewed outcome shape. Is the
mean-gate the wrong instrument? **No** — D5 designates the mean net expectancy as the binding figure for
advancement and **co-reports the median** as the disclosed shape read; EXP-092 emits `net_mean`, `net_median`,
and `mean_and_median_pos` per cell, so the shape is visible to the interpreter and EXP-093, not masked. The
gate sees the location effect it is built for; the co-reported median catches the shape. Recorded for the
interpreter (Stage 6) and EXP-093 D0: **prefer the mean-AND-median-positive robust core**; do not retro-edit
the gate.

## Findings

**No Critical. No Warning.** Materiality reasoning for the Info notes (each shown unable to move any
verdict-bearing number):

- **Info-1 — two-tier candidate set (robust core 8 vs mean-carried/fragile 1h 3).** This is the masking-check
  disclosure, fully captured in `candidate_set.csv` / `margin_preread.csv`. It does **not** change EXP-092's
  deliverable (the full `SEQUENCE_PASS` set + per-cell quality flags is exactly the predeclared output); it is
  *selection guidance* for EXP-093, not an EXP-092 verdict change. Non-material.
- **Info-2 — GBPUSD-1h `SEQUENCE_PASS` but below EXP-093 margin (0.0044<0.0125) and median-negative.** Correct
  per the frozen 4b/4c split (4b admits on `net_ci_low>0`; 4c margin is the *TEST* gate). It is pinned-but-flagged;
  EXP-093 D0 should not carry it. Does not move EXP-092's set membership rule. Non-material.
- **Info-3 — EURUSD appears on both 1h and 4h (distinct strata).** Both are eligible candidates; per D7 each
  carried stratum spends its **own** counted TEST read at EXP-093 (EURUSD-1h and EURUSD-4h are separate 0/2
  strata). A note for EXP-093 read-accounting, not an EXP-092 defect. Non-material.
- **Info-4 — `net_ci_low` differs from upstream by ≤6.2e-4 (independent bootstrap seeds).** Expected and
  correct; all cells stay same-sign incl. the boundary cell GBPUSD-1h (+0.00426→+0.00441). Confirms faithful
  reuse; does not move any pass/fail. Non-material.

## Integrity / discipline

- **Holdout sealed** — `holdout_untouched=true`; loads only via the TRAIN-only `E90.load_train_1m`; 1m walk
  clipped at the TRAIN edge by timestamp. ✓
- **TRAIN-only, 0 reads / 0 slots** — `counted_test_reads=0`, `candidate_slots=0`; no analysis-TEST slice. ✓
- **Determinism** — replay PASS; output + candidate-set hashes pinned and reproduced. ✓
- **No goalpost-moving / no tuning** — frozen D0 sequence rule, cost table (`D0-amendment-003`), margins
  (EXP-090/094); no new selection statistic ⇒ no bite-check required (D0 §D4). ✓
- **Per-stratum doctrine (LESSON-001)** — binding read per cell; the pooled count is disclosure with the
  quality split exposed. ✓

**Audit verdict: PASS.** Cleared for Stage 6 (interpretation). Recommendation carried to the interpreter and
EXP-093 D0: the defensible candidate subset is the **mean-AND-median-positive, margin-clearing robust core**
(USTEC-1h, US2000-1h, and the six 4h members); GBPUSD-1h should not be carried to TEST.
