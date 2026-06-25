# Results: Experiment EXP-093

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 Fade Capture-Geometry & Tradability) · **Family / HYP:**
`CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Type:** one-shot counted-TEST confirmation (the phase's single binding tradability read) ·
**Audit:** PASS (0 Critical / 1 Warning / 3 Info).

## Summary

On the **analysis-TEST stratum**, the bare RSI-2 fade exited by **EXIT-RCT** (the native reversion-completion
target) **confirms a positive net-of-cost per-event expectancy in 8 of 11 carried cells** — `Holm-adj p =
0.0011`, each `net ci_low_1s` above its EXP-090/094 margin — under the frozen referee, the phase Holm-11 rule,
and the conservative `D0-amendment-003` cost (`F=0`). The confirms span **7 instruments across both domains**
(4h: EURUSD, USDCHF, XAUUSD, AUDJPY, GBPJPY, EURJPY; 1h: USTEC, US2000). The remaining three 1h cells did **not**
confirm: GBPUSD-1h and EURUSD-1h are well-powered **net-negative** (out-of-sample reversal), NZDUSD-1h is
**near-zero**. This is the **first net-positive out-of-sample price entry in the programme's history** —
pending the separate G-021 adjudication, which routes **TRADABLE** on ≥1 confirmed cell. The global-30% holdout
remains sealed; each carried stratum now stands at 1/2 lifetime counted reads.

## Detailed Findings

### F1 — The robust core (six 4h cells) confirms cleanly, mean-AND-median positive

| Cell | n_resolved | net_mean | net_median | net_ci_low | margin | Holm-adj p | verdict |
|---|---|---|---|---|---|---|---|
| EURUSD-4h | 454 | +0.129 | +0.060 | **+0.094** | 0.025 | 0.0011 | CONFIRM |
| XAUUSD-4h | 388 | +0.107 | +0.085 | +0.072 | 0.025 | 0.0011 | CONFIRM |
| USDCHF-4h | 458 | +0.098 | +0.056 | +0.062 | 0.025 | 0.0011 | CONFIRM |
| AUDJPY-4h | 457 | +0.087 | +0.026 | +0.057 | 0.025 | 0.0011 | CONFIRM |
| EURJPY-4h | 430 | +0.086 | +0.015 | +0.044 | 0.025 | 0.0011 | CONFIRM |
| GBPJPY-4h | 453 | +0.071 | +0.018 | +0.039 | 0.025 | 0.0011 | CONFIRM |

- **Evidence:** all six clear the binding mean gate **and** the co-reported median gate; `net_ci_low` is
  1.6–3.7× the 0.025 margin. `terminal_fav ≈ 0.985–0.996` (the RCT target is touched ~99% of events);
  `tie_break_frac = 0` (no intrabar target/stop ambiguity); holding ≈ 0.20 days (~5h, the ~3-bar MR tempo).
- **Interpretation:** these are the strongest, least-ambiguous confirmations — the favourable reversion target
  is captured almost always and survives conservative cost with positive central tendency on both mean and
  median. Per the predeclared guide (≥1 cell CONFIRMS → TRADABLE), HYP-002 tradability is **SUPPORTED** here.

### F2 — Both 1h confirms are real but mean-carried (median-fragile)

| Cell | n_resolved | net_mean | net_median | net_ci_low | margin | verdict |
|---|---|---|---|---|---|---|
| US2000-1h | 1613 | +0.093 | +0.004 | +0.073 | 0.0125 | CONFIRM (median ≈ 0) |
| USTEC-1h | 1668 | +0.065 | **−0.026** | +0.046 | 0.0125 | CONFIRM (mean-carried) |

- **Evidence/Interpretation:** both clear the binding **mean** gate comfortably (D5 designates the mean as
  binding), but USTEC-1h has a **negative TEST median** and US2000-1h's median is barely positive — the edge is
  carried by the favourable tail, not the typical trade. This is the family's known median-fragility (EXP-089
  median-positive/mean-fragile signature, here inverted on 1h). The confirms are valid but **weaker** than the
  4h core; weight them accordingly. (Audit gate-shape note: the mean gate is the right instrument for a tradable
  P&L claim; the median is co-reported and exposes the shape — not masked.)

### F3 — The three non-confirming 1h cells (audit W1 re-label)

| Cell | n_resolved | net_mean | net_median | net_ci_low | disposition (re-labeled) |
|---|---|---|---|---|---|
| NZDUSD-1h | 1677 | +0.003 | −0.060 | −0.015 | **INCONCLUSIVE** (near-zero; bound spans 0) |
| EURUSD-1h | 1619 | −0.010 | −0.092 | −0.032 | **EVIDENCE_AGAINST** (well-powered net-negative) |
| GBPUSD-1h | 1653 | −0.080 | −0.152 | −0.103 | **EVIDENCE_AGAINST** (well-powered net-negative) |

- Per audit W1, the code's blanket `INCONCLUSIVE` label (every `ci_low ≤ 0`) is coarse: **GBPUSD-1h and
  EURUSD-1h are well-powered (n≈1.6k) and net-negative** — the fade with RCT is genuinely *unprofitable*
  out-of-sample on these cells, not merely power-limited. **NZDUSD-1h** is genuinely near-zero (mean +0.003,
  bound spans zero). None of this changes the G-021 verdict (rests on the 8 confirms); it is the honest
  per-stratum file-drawer record.
- **GBPUSD-1h** was pre-disqualified at `D0-amendment-006 §2` (below its margin already on TRAIN); its
  EVIDENCE_AGAINST outcome is expected, and its counted read was spent as ratified.

### F4 — Mechanism: cost geometry + selection-overlap shrinkage (not signal strength)

- **Why 4h dominates the confirm set (6/8):** gross expectancy is ~domain-invariant (`gross_mean` ≈ 0.22–0.31
  ATR on both domains); the conservative fixed-bps round-trip is a **smaller ATR fraction on the larger-ATR 4h
  domain**, so net clears by a wider margin there. The 1h confirms (USTEC/US2000) are the cheapest 1h cells.
  This is the EXP-091/092 cost-geometry mechanism reproduced out-of-sample — **not** a stronger 4h signal.
- **Why the fragile 1h tier reversed:** `train_vs_test.csv` shows **every** cell shrank from TRAIN to TEST
  (Δ `net_ci_low` −0.005 to −0.107) — the expected selection-overlap shrinkage (EXP-084 pattern). The robust
  core's larger TRAIN bounds (0.05–0.135) absorbed the shrink and stayed above margin; the thin-margin 1h cells
  (TRAIN 0.004–0.047) shrank below zero. The honest prior — *availability ≠ capturable edge, and TRAIN
  eligibility is not OOS edge* — realized exactly as predeclared, while the strongest cells held.

## Hypothesis Verdict

**SUPPORTED** (HYP-002 tradability of the admitted bare RSI-2 fade lever).

The frozen one-shot TEST confirms net-of-cost positive expectancy on 8 of 11 carried (instrument, domain) cells
under Holm-11 + the per-cell margin, with the six 4h cells mean-AND-median positive and the breadth spanning 7
instruments and both domains. Per the predeclared D6/4c rule and G-021 §2, **≥1 carried cell CONFIRMS → the
fade is net-tradable out-of-sample**, routing G-021 **TRADABLE**. The result is reproduced from raw data,
holdout-clean, deterministic, and Holm-correct (audit PASS). This is the programme's first net-positive price
entry — a genuine reversal of the G-019 "price-derived information exhausted" routing for this lever.

## Limitations

- **Analysis-TEST stratum, not the global holdout.** This is the sanctioned counted-TEST read (each carried
  stratum 0→1; 1/2 remaining), **not** a final-30% global-holdout confirmation. The global holdout stays sealed;
  releasing it is a separate, later gate.
- **4h dominance is cost-geometry.** Do not read 6/8-being-4h as "the signal is stronger on 4h" — gross is
  domain-invariant; net favours 4h via the cost fraction.
- **1h confirms are mean-carried.** USTEC-1h (median −0.026) and US2000-1h (median ≈ 0) pass on the mean but not
  robustly on the median; the 1h edge is favourable-tail-driven and partially reverses across the tier.
- **Single OOS read.** TRAIN→TEST shrinkage was uniform; a second independent confirmation (or the global
  holdout) would further de-risk the 4h core, but each stratum has only 1 counted read remaining.

## Alternative Explanations

- **Residual selection effect on the 4h core.** The 4h cells were selected on TRAIN; although they survived OOS
  with wide margins, some of the 4h advantage could still reflect favourable-period overlap. Mitigant: the
  effect is consistent across 6 independent 4h instruments and the mechanism (≈99% target capture, small 4h cost
  fraction) is structural, not cell-specific.
- **Mean-carried 1h confirms could be tail artifacts.** The negative/near-zero 1h medians leave open that the 1h
  mean edge is a few large winners; the 4h core (mean-AND-median positive) does not share this ambiguity.

## Recommended Next Steps (new scopes — not extensions of EXP-093)

1. **Global-holdout release decision for the 4h robust core** — a separate, governed one-shot gate (à la
   EXP-032), scoped to the mean-AND-median-positive 4h cells only, with its own checkpoint/D0.
2. **1h median-fragility diagnostic** — a TRAIN-only characterisation of whether the 1h fade edge is
   tail-carried and whether a shape-aware exit recovers the median (new HYP, own D0).
3. **Deferred levers, each own dated `D0-amendment-*` + slot decision** — faster-turnover cost sensitivity, the
   inert vol-regime partition, the contrarian arm, the 25/75 scheme, 15m capture. None are in EXP-093's scope.
