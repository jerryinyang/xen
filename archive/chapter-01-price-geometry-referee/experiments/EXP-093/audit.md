# Audit Report: Experiment EXP-093

**Phase:** 021 (CF-MR-001 batch 2) · **Family / HYP:** `CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Experiment verdict under audit:** `TEST_CONFIRMED` — **8 CONFIRM / 3 INCONCLUSIVE** (routes G-021 TRADABLE).

## Summary

- **Verdict: PASS** (trust the implementation and the numbers).
- **Critical Issues: 0**
- **Warnings: 1** (the INCONCLUSIVE-vs-EVIDENCE_AGAINST label mapping for net-negative cells — non-verdict-material; route to the analyst for Stage 6).
- **Info Notes: 3**

Independent re-derivation reproduces every headline number from raw data; holdout safety, the 11 counted-read
accounting, the Holm-11 procedure, and determinism all check out. The verdict is real and faithfully computed.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Mirrors EXP-092 `sequence_cell` for the resolve/cost/keep path; adds the TEST loader + Holm + adjudication. Re-derived independently (below). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Loads `[0, int(total·0.7))` only; holdout `[analysis_cutoff, total)` never sliced; fill clips at `train_edge_epoch == analysis_edge` (engine `intrabar_fill.py:215` defensive fence). |
| `code/run_experiment.py` | Look-ahead / timestamp | PASS | Entries selected by domain `CloseTime` epoch ≥ `ts_lo`; fill walk causal, by epoch, never bar index. |
| `code/run_experiment.py` | Real-price discipline | PASS | `net_return_atr` on real touched fill prices + real OHLC, ATR(14) units. No HA/Renko synthetic prices. |
| `code/run_experiment.py` | Type safety / docstrings | PASS | Typed public fns; dataclass `CellTest`; docstrings present. |
| `code/run_experiment.py` | NaN / edge cases | PASS | Explicit `keep` mask; `n_resolved<2`→INDETERMINATE; empty entries→INDETERMINATE; NaN p excluded from Holm family. |
| `code/run_experiment.py` | Determinism | PASS | Fixed seeds; replay USTEC-1h+EURUSD-4h frame-identical; `ci_low` bit-identical to shared `xen.ass`. |
| `code/run_experiment.py` | Organization / import side effects | PASS | VAL-001 sectioning; dirs created in `run()`; EXP-090 import `main`-guarded, reads no data. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy `scan_parquet().sort("CloseTime").slice(0, analysis_cutoff).collect()`; no holdout collection. |
| `code/run_experiment.py` | Per-stratum verdict | PASS | Binding verdict emitted per cell (`test_adjudication.csv`); `experiment_verdict` is an explicit routing readout, not a collapsed binding boolean. |
| `code/run_experiment.py` | Progress / logging | PASS | `tqdm` over 11 cells; concise logging; helpers return data. |
| `code/run_experiment.py` | Plot reuse | PASS | 4 plots from collected summaries; no reloads. |

## Numerical Validation

### Spot checks (independent re-derivation from raw data — not via `test_cell`)

Re-loaded the analysis set, rebuilt the EXP-090 context, selected TEST entries by timestamp, resolved EXIT-RCT,
applied the `D0-amendment-003` cost, and ran `xen.ass.moving_block_bootstrap_cis` directly:

| Cell | n_resolved (audit / table) | net_mean (audit / table) | net_ci_low (audit / table) | Match |
|---|---|---|---|---|
| EURUSD-4h (CONFIRM) | 454 / 454 | +0.12949 / +0.12949 | +0.09371 / +0.09371 | ✓ exact |
| GBPUSD-1h (INCONCLUSIVE) | 1653 / 1653 | −0.08030 / −0.08030 | −0.10270 / −0.10270 | ✓ exact |

Holm-11 re-derived independently from the 11 `boot_p`: **8 holm-sig at adj-p = 0.001100**, 3 at 1.000000 —
matches `test_adjudication.csv` exactly. `terminal_fav ≈ 0.989–0.995` (RCT target reached ~99% of events).

### Range / statistical sanity

| Metric | Expected | Actual | Pass |
|---|---|---|---|
| net_ci_low (CONFIRM cells) | > margin (0.025/0.0125) | 0.039–0.094 | ✓ |
| Holm-adj p (CONFIRM) | ≤ 0.05 | 0.0011 | ✓ |
| n_resolved (4h / 1h) | ~370–470 / ~1600–1700 | 388–458 / 1613–1677 | ✓ (≈0.43× TRAIN, as scoped) |
| holdout rows loaded | 0 | 0 (≈561k not loaded per file) | ✓ |
| counted_test_reads | 11 | 11 | ✓ |

## Assumption Validation

| Method | Assumption | Holds | Evidence |
|---|---|---|---|
| Moving-block bootstrap | serial-dependence-preserving, non-parametric | YES | block length `round(n^{1/3})`; no normality/i.i.d. assumption; estimator calibrated in EXP-090/094 |
| Holm–Bonferroni (one-sided, m=11) | valid family of one-sided p | YES | family = 11 finite `boot_p`; step-down re-derived; carrying all 11 is the conservative direction |
| Margin = EXP-090/094 MDE | power-confirmed materiality floor | YES | per-cell, data-derived; re-read with drift assertions |

## Verdict Forensics

### Per-stratum re-derivation & masking check

The headline is **already per-stratum** (8 CONFIRM / 3 INCONCLUSIVE) — no pooled/aggregated number is presented
as the verdict, so there is nothing to mask. Re-derived per cell:

| Stratum | net_ci_low | margin | net_median | per-cell verdict | Masking? |
|---|---|---|---|---|---|
| EURUSD-4h | +0.0937 | 0.025 | +0.060 | CONFIRM | — |
| USDCHF-4h | +0.0616 | 0.025 | +0.056 | CONFIRM | — |
| XAUUSD-4h | +0.0724 | 0.025 | +0.085 | CONFIRM | — |
| AUDJPY-4h | +0.0565 | 0.025 | +0.026 | CONFIRM | — |
| GBPJPY-4h | +0.0390 | 0.025 | +0.018 | CONFIRM | — |
| EURJPY-4h | +0.0441 | 0.025 | +0.015 | CONFIRM | — |
| US2000-1h | +0.0734 | 0.0125 | +0.004 | CONFIRM | — |
| USTEC-1h | +0.0457 | 0.0125 | **−0.026** | CONFIRM (mean-carried) | shape disclosed (see below) |
| NZDUSD-1h | −0.0154 | 0.0125 | −0.060 | INCONCLUSIVE (near-zero) | — |
| EURUSD-1h | −0.0325 | 0.0125 | −0.092 | INCONCLUSIVE (negative) | label (W1) |
| GBPUSD-1h | −0.1027 | 0.0125 | −0.152 | INCONCLUSIVE (negative) | label (W1) |

**Affirmative masking check:** the 8 CONFIRMs span **7 distinct instruments across BOTH domains** (4h: EURUSD,
USDCHF, XAUUSD, AUDJPY, GBPJPY, EURJPY; 1h: USTEC, US2000) — not a single-instrument or single-domain fluke.
The G-021 TRADABLE route (≥1 CONFIRM) is satisfied with breadth. The 1h-vs-4h skew (6/8 are 4h) is **not**
masking — it is the known, disclosed cost-geometry mechanism (below), reproduced OOS, and the per-stratum table
shows it transparently. The 1h tier's partial reversal (3/5 non-confirming) is likewise disclosed per stratum,
not hidden behind a pooled pass.

### Mechanism (why the verdict came out this way)

The confirm is driven by the **robust-core cells**, where the EXP-091/094/092 mechanism reproduces
out-of-sample: the RCT reversion-completion target (~0.28 ATR) is reached ~99% of events (`terminal_fav` 0.99),
and net stays positive after the conservative cost because the fixed-bps round-trip is a **small ATR fraction on
the larger-ATR 4h domain** (and on the cheapest 1h cells, USTEC/US2000). The 4h cells clear by the widest
margin (ci_low 0.039–0.094 ≫ 0.025) for exactly this cost-geometry reason — not because the 4h signal is
stronger (gross is ~domain-invariant). The **fragile 1h tier reversed** (TRAIN ci_low +0.004…+0.047 → TEST
−0.103…−0.015): these were the median-negative / mean-carried / pre-disqualified cells whose thin TRAIN margins
did not survive the selection-overlap shrinkage (`train_vs_test.csv`: every cell shrank, Δ net_ci_low −0.005 to
−0.107; the robust core's larger TRAIN bounds absorbed the shrink, the fragile tier did not). This is the honest
prior (availability ≠ capturable edge; EXP-084-style fold reversal) realized exactly as predeclared.

### Gate-shape check

- **Binding gate:** the **mean** net per-event expectancy lower bound (D5 — a location gate). **Effect shape:**
  a location/mean effect (tradable per-event P&L) — the gate is the **right instrument**; it is not blind to a
  tail/bimodal effect it should be catching.
- **Disclosed shape caveat (not a mismatch):** the median is co-reported (D5). Among the 8 CONFIRMs, the six 4h
  members are **mean-AND-median positive** (the cleanest, most robust confirms); **USTEC-1h confirms on the mean
  but has a negative TEST median (−0.026)** and US2000-1h's median is barely positive (+0.004) — i.e. the two 1h
  confirms are **mean-carried** (favourable-tail-driven) on TEST, the family's known median-fragility. This is
  surfaced by the co-reported median, not masked. The interpreter (Stage 6) should weight the six mean-AND-median
  4h confirms as the strongest evidence and flag the 1h confirms as mean-carried. No gate retro-edit.

## Scope Compliance

- Analysis plan followed: **YES** (TEST loader, RCT resolve, cost, net lower bound + boot_p, Holm-11,
  adjudication, 4 plots, determinism). Deviations: **none**.
- Complexity budget: **1 binding test** + companions / 1; **4 plots** / 4; **0 new modules** / 0. ✓
- Holdout exclusion verified: **YES** (analysis-TEST stratum read; global holdout never loaded —
  `holdout_untouched=true`, ~561k holdout rows not loaded per file, fence at the analysis edge).
- Counted-read accounting verified: **YES** (`counted_test_reads=11`; each carried stratum 0→1; cap 2/stratum
  honored; must be entered in `test-read-ledger.md` at Stage 7).

## Issues

### Critical
None.

### Warning

1. **INCONCLUSIVE label conflates power-limited with well-powered net-negative.**
   - File: `code/run_experiment.py`, `adjudicate()` (the `if net_ci_low <= 0.0: return "INCONCLUSIVE"` branch).
   - Description: all three non-confirming cells are labeled `INCONCLUSIVE`, but **GBPUSD-1h** (n=1653,
     net_mean −0.080, net_ci_low −0.103, median −0.152) and **EURUSD-1h** (n=1619, net_mean −0.010, ci_low
     −0.032) are **well-powered and net-negative** — `EVIDENCE_AGAINST`, not "power-limited / spans zero." Only
     **NZDUSD-1h** (net_mean +0.003, ci_low −0.015) is genuinely near-zero/spans-zero. The plan's predeclared
     INCONCLUSIVE was "spans zero **with wide CI** / power-limited"; the code maps every `ci_low ≤ 0` to
     INCONCLUSIVE regardless of power, coarsening the disposition.
   - Materiality (why NOT Critical): cannot move any verdict-bearing number. `experiment_verdict` is
     `TEST_CONFIRMED` whenever ≥1 cell CONFIRMs (relabeling these three FAIL/EVIDENCE_AGAINST leaves the routing
     `TEST_CONFIRMED` unchanged), the 8 binding CONFIRM strata are untouched, all 11 counted reads are spent
     regardless of per-cell label, and the underlying numbers (`net_ci_low`, `net_mean`, `net_median`, `boot_p`)
     are all correct and present in `test_adjudication.csv`. No sample-membership, denominator, metric, causal,
     or binding-stratum change. **Document-and-proceed justified.**
   - Fix (interpretation, not code-rerun): the analyst (Stage 6) should re-label per the actual bounds in
     `results.md` — GBPUSD-1h / EURUSD-1h as **EVIDENCE_AGAINST** (well-powered net-negative, OOS reversal),
     NZDUSD-1h as **INCONCLUSIVE/near-zero** — and the file-drawer record should reflect that. No re-execution
     required (numbers unchanged).

### Info

1. **Domain skew in the confirm set is the cost-geometry mechanism, not signal strength.** 6/8 CONFIRMs are 4h;
   gross is ~domain-invariant, net favours 4h because fixed-bps cost is a smaller ATR fraction there (EXP-091/092
   mechanism). Disclose in the report so 4h dominance is not read as "the signal is stronger on 4h."
2. **USTEC-1h confirm is mean-carried (TEST median −0.026).** Already covered in gate-shape; the six 4h confirms
   are the mean-AND-median-positive core.
3. **GBPUSD-1h read spent as predeclared.** `D0-amendment-006 §2` flagged it a near-certain non-confirm; the
   counted read (GBPUSD-1h 0→1) is spent regardless, as ratified. No surprise.

## Materiality & Re-Audit Requirements

- **No blocking findings.** No Critical; the single Warning (W1) is shown unable to move any verdict-bearing
  number (the `TEST_CONFIRMED` routing, the 8 binding CONFIRM strata, the counted-read count, and every
  underlying statistic are all invariant to the label) → no fix-and-rerun required; routed to the analyst as an
  interpretation correction for `results.md`.
- **Re-audit:** not required. The verdict (`TEST_CONFIRMED`; 8 CONFIRM across 7 instruments and both domains) is
  reproduced from raw data, holdout-clean, deterministic, and Holm-correct.
