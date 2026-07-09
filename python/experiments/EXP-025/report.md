# Experiment Report: EXP-025 — CF-HTFDI-001/HYP-A Graduation: HTF-DI-Confirmed Breakout, 22-Symbol 1h/5min

## Status: COMPLETED

**Date**: 2026-07-09
**Instruments**: 22 loaded symbols (10 FX, 10 indices, XAUUSD, BTCUSD)
**Data Views**: 5min/1h clock-aligned resamples of canonical m1 time bars; engine emissions under `AnalysisEndUtc` fence

---

## Question

Does a CTRL-02 momentum breakout gated by last-closed 1h Wilder ±DI agreement carry a
net-of-commission per-trade directional edge on any instrument of the 22-symbol universe at
1h/5min — confirmed on a counted TEST read under per-instrument max-stat + Holm?

## Hypothesis

The last CLOSED 1h bar's ±DI direction conditions the sign of the 5min forward return
(continuation), magnitude-weighted, per the SPDR-001/002/003 corrected screen evidence
(USTEC 1h/5min dir_gap +0.09→+0.50 ATR).

## Method Summary

Full cTrader-primary pipeline: C# `HtfDiBreakoutModel` (decision on closed bars, fill at next
5min open, HTF leak guard hard-asserted), 440 T1 TRAIN runs (22 × X∈{2,3,4,5,8} ×
H∈{12,24,36,48}) + CTRL-REF-RANDOM reference arm + CTRL-NULLSENT sentinel; WF-EXPANDING folds
inside TRAIN; pre-registered SEL-NEIGHBOR selection gating a capped counted-TEST stage
(≤5 reads, Holm). Estimand: per-trade net open-to-open return (bps), `xen.adjudication`
per-leg. See [design.md](design.md).

## Key Findings

### Finding 1: T1-terminal — 0/440 cells qualify; the confirmatory machinery never engages

SEL-NEIGHBOR rule 1 (own F0 CI_low > 0) fails in every cell (best F0 CI_low −0.09, US500
x4h24). No battery-gated eligibility, no TEST read spent (cap 5 untouched; ledger unchanged).
The negative is **powered**: per-cell MDE 0.18–5.23 bps (median 0.4–1.3 by hold), all 440
cells n ≥ 1,332 (2,432,812 non-censored TRAIN trades). 0 cells UNPOWERED.

### Finding 2: The design's effect-size target was a units artifact — 4.1× inflated

Design §4/§8/§9 converted the screen's +0.26–0.50 ATR to "30–60 bps" using a **1h HTF
ATR(14)** divisor asserted from memory. The SPDR screens normalise by the **5-min LTF
ATR(14)[t−1]** (`spdr001_screen.py:204,299`). USTEC TRAIN-median: 1h ATR 33.9 bps vs 5min ATR
8.19 bps. Correct conversion of the screen effect ≈ **4 bps/trade at h48** (0.2–1 bps at
short holds). The apparatus was nonetheless powered for the true effect (USTEC MDE 0.2–1.3
bps), so the T1 negative stands as evidence.

### Finding 3: The screen effect is REAL and replicates — at the corrected size

Ref-arm dir_gap re-expressed in the screen's own units: 0.026 / 0.136 / 0.217 / 0.415 ATR_5m
at h12/24/36/48 vs the screen's +0.09→+0.50 (h48 0.42 vs 0.50, within CI). Operator-ordered
diagnostic battery (25-seed matched-cadence, 3 disclosure cells, 75 engine runs): US500
x4h24/x5h24 clear 2 seed-SD (z 2.62/2.31, pct 1.00); decomposition shows a genuine
direction-timing gap of +1.9–6.2 bps on traded slots, not static drift capture. The engine is
exonerated; the channel exists at ~1–3 bps/trade — an order of magnitude below tradeable size
net of spread, one-sided capture (≈ gap/2), and throttle dilution.

### Finding 4: The only positive grid structure is drift-shaped, without DI dose-response

Positive-mean cells concentrate entirely in equity indices; all 200 FX cells ≤ 0. Across all
200 index cells, 99% have their stronger direction side equal to the instrument's own
realized drift side. Low-|DI-margin| halves earn as much or more than high (payoff
flat-to-inverted in the conditioning variable). The 3 full-TRAIN CI-clear cells (HK50 x2h48
+3.18 [0.13, 6.20]; US500 x4h24/x5h24 +0.93) all FAIL F0 and flip sign by year; 3 CI-clear of
440 is below the ≈11 expected by chance at 2.5% one-sided.

### Finding 5 (integrity): All blocking gates pass

22/22 emissions `blocking_pass: true`; provenance ≤ t−1 hard-asserted + QA golden trace
byte-consistent (5,486 trades); holdout and TEST quarantine intact; tripwire not required
(no verdict-bearing positive); no local accounting. Sentinel family-wise read 1/22 CI-clear
vs binomial 95th-pct threshold 3 — apparatus healthy.

## Conclusion

**Operator final verdict (signed 2026-07-09): NOT SUPPORTED (magnitude, not existence).**
Analyst recommendation was identical.

The HTF-DI conditioning channel exists, replicates end-to-end (screen → ref-arm → battery),
and is now precisely sized at ~1–3 bps/trade after capture dilution — roughly 1/10 of the
noise-robust selection bar and below commission on FX. The hypothesis under test — a
net-of-commission tradable directional edge confirmed at TEST — fails on magnitude: no cell
reaches the pre-registered eligibility, and the design's own protocol ends the experiment at
T1. This is a magnitude falsification, not an existence falsification: the SPDR observation
was honest; the graduation design mis-translated its units.

## External reviews (2026-07-09, post-analysis)

Two independent external reviews were adjudicated at the verdict gate. Both confirm the
units-artifact chain and the engine's fidelity; neither changes the verdict (no finding
produces a false qualifier — 0/440 qualified even under the amended gates). Their design-gap
findings were codified the same day:

| Finding | Disposition |
|---|---|
| ATR-unit convention unpinned at the screen→graduation seam; no money-magnitude check before graduation | **Codified L-21**; binding amendment in `docs/references/spdr-lane.md` (unit pin + conversion pin + money-unit floor at disposition) |
| SUPPORTED band net-of-commission only; spread (dominant cost at 5min holds on 0-commission indices) never binds (F01) | **Codified L-22**: 1× spread scenario becomes a binding tier for any future SUPPORTED claim |
| All seven 2026-07-08 pre-measurement amendments loosened toward ADMIT; joint false-qualification rate never re-derived (F03) | **Codified L-23**: amendment-direction ledger + final-gate-set false-qual re-derivation; streak ≥3 flags the operator |
| Seed-SD blind to regime concentration (F02); exit*-stat null cadence mismatch (F04); tripwire retention threshold asserted not derived (F06); n≥50 read floor MDE-inconsistent (F07); winner's-curse shrinkage absent from power math (F05) | **Codified L-24** (bundled future-design rules); all moot for this experiment's verdict |

## Registry Disposition

**Evidence rows only — no family status transition** (reserved for the checkpoint-010-series
retrospective, operator-signed): `multiplicity-registry.md` `CF-HTFDI-001/HYP-A` row updated
with the EXP-025 outcome; evidence appended to
`docs/signal-registry/candidate-families/cf-htfdi-001.md` without touching its status field.
`test-read-ledger.md` unchanged — **0 counted TEST reads spent**; 0 slots.

## Limitations

- TRAIN-terminal by protocol: TEST band never read (correctly — eligibility failed), so the
  ~1–3 bps effect size is a TRAIN-only estimate.
- Residual 0.42-vs-0.50 ATR_5m ref-arm gap unpinned (likely event-population difference; a
  same-events dual-pipeline diff on USTEC x3 would resolve it — not run, low value).
- T2 exit stage and tripwire never exercised (no survivors); the E6 DI-gated exit branch is
  implemented but unexercised code.
- Live spread unpinned throughout (moot with no qualifying cell).
- DE40/STOXX50 absent from `xen.evaluation.FTMO_COSTS` under those keys (treated 0-commission
  index-class per design §10) — flagged to the cost-table maintainer.

## Implications for Future Research

- The screen→graduation unit seam now has a binding gate (L-21/spdr-lane.md); any future SPDR
  graduation states divisor object + measured bps value + resulting effect, verifiable.
- Exit-method (T2) rescue is NOT recommended: no exit multiplies a ~2 bps conditional gap
  past costs without leveraging the same noise.
- CF-HTFDI-001 disposition (retire vs re-scope) belongs to the checkpoint retrospective; the
  mechanism is real but ~4 bps gross at its best hold in this vehicle class.

## Recommended Next Experiments

None from this thread. Optional zero-read forensic: same-events dual-pipeline diff (USTEC x3)
to pin the residual screen-vs-engine event-population gap — only if the family is re-scoped.

## Artifacts

| Artifact | Path |
|----------|------|
| Design (scope + analysis plan) | [design.md](design.md) |
| QA review (append-only) | [qa-review.md](qa-review.md) |
| Code (C# refs + confs notes) | [code/](code/) |
| Analysis (binding evidence record) | [analysis.md](analysis.md) |
| Analyst scripts | [analysis_code/](analysis_code/) |
| Results (incl. 22 + 75 estimand gates, battery, MDE, cell stats) | [results/](results/) |
| Emissions | `data/strategy_runs/EXP-025-*/` |
