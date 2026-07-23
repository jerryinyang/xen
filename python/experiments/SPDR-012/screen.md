# SPDR-012 — screen summary (neutral quantification)

- **Family:** `CF-VOLDIR-001` / **HYP-A** · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Question (design §1):** is next-horizon volatility / absolute move predictable from causal
  lagged information, under predeclared metrics?
- **Status:** screen executed 2026-07-23. **0 counted reads, 0 slots. No TEST, no holdout.**
- **This file is subordinate to `analysis.md`** (SPDR lane stage 4 vs stage 5). It reports
  magnitudes and labels only. It contains **no disposition and no recommendation.**
- **Revised 2026-07-23** after the fresh-context analyst pass. `analysis.md` §8 lists ten places
  where an earlier version of this file over- or under-stated a figure; the corrections are folded
  in below. Two qualifications `analysis.md` establishes and this file does not attempt to
  reproduce: the headline IC is **span-dependent** (0.147 at a 15-date window vs 0.306 at 290,
  same data), and **26–75% of it is between-calendar-month level structure** — within a single day
  there is no skill (H1 +0.024, H4 −0.116).

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: any optional cost overlay understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

All bps figures below are the magnitude of an open-to-open move on the stated clock
(`abs_oo = 1e4·|O_{t+1}/O_t − 1|`, design §6.1 UNIT-PIN). **No P&L object exists in this
screen.** No direction, no combination, no XENA.

---

## 0. PER-ARM VERDICT (headline for Reflection C — full version in `analysis.md` §0)

**The most decision-relevant output of SPDR-012 is which volatility levers survive, not one
IC.** CONFIRM band; rank IC 0 = none, ~0.30 = strong.

| Arm | RAW §5.1 axis | Verdict |
|---|---|---|
| **V-PERSIST** | persistence | WORKS on the multi-bar level; single-bar shock dies in ~0.4 bars; **HAR is the weakest model, collapses at D1** |
| **V-LEVEL** *(primary)* | level forecasting | **STRONG intraday** (IC 0.338 H1 / 0.301 H4), WEAK D1; all model forms tie — **EWMA is enough** |
| **V-REGIME** | Markov regime | WORKS modestly (high−low +17 bps, ~93% sticky); clears the design bar on **H1 only** |
| **V-REGIME-HMM** | HMM regime | **MIS-NAMED — a single-bar shock detector, not a regime model**; 76/83 cells UNPOWERED |
| **V-MEASURE** | realised vs range | **RANGE MEASURES WIN** (+~0.11 IC, decisive at D1) |
| **V-CLOCK** | calendar | **NULL — adds nothing on any clock** |
| **V-XS** | cross-sectional rank | **WEAKEST axis** — clears in a minority of coins |
| **V-TAIL** | tails | WORKS intraday (extreme-move rate ~1.8× in high-vol state); unpowered D1 |

**Cross-cutting:** the usable signal is **day-to-week, never hour-to-hour** (no within-day skill);
the D1 clock needs a short-window range input, not close-to-close RV; the headline IC is
span-dependent, so the arm *ordering* above is the durable result. `analysis.md` §0 carries the
Keep / Drop / Re-label hand-off to Reflection C.

---

## 1. Integrity

`results/integrity_selfcheck.json` — **all hard checks PASS**.

| Check | Result |
|---|---|
| §7.1 every query TRAIN; max target ts < `train_end_utc` | PASS |
| §7.1b nothing at or after the TEST band start | PASS |
| §7.2 no row ≥ `holdout_start_utc` | PASS |
| §7.3 CONFIRM never enters an estimated coefficient | PASS |
| §7.3b DESIGN target **exit** price also inside DESIGN *(added by AMENDMENT-T1)* | PASS |
| §7.4 features ≤ origin; target strictly the next bar | PASS |
| §7.5 derangements fixed-point-free — **measured**, 0 of 360 000 seed draws | PASS |
| Universe: top-25 recompute over all 903 readable symbols == frozen family pin | PASS (exact) |
| §8 golden traces G1/G2/G3 | PASS |

**Deviation (operator-signed 2026-07-23, `design.md` AMENDMENT-T1):** the future-destroy
tripwire is **no longer a hard gate**; it is a report layer with no pass field. Two reasons,
both measured: the pinned within-month destroy leaves the between-month component intact so
its null is not centred at zero (median 0.109 against a live 0.259) and adjudicating collapse
on it failed 33/90 cells including the strongest; and no outcome-side destroy can detect
look-ahead at all, since `E[Spearman(pred, deranged y)] = 0` for any fixed predictor.
**SPDR-012 therefore ships with no hard leak gate.** The no-look-ahead claim rests on the §7
construction checks above and on two independent fresh-context re-derivations of the
walk-forward path: `qa-review.md` (max abs difference 0.0 over 608 OOS rows on BTCUSDT H4) and
`analysis.md` §1.3 (~1e-12 bps across five cells spanning 554–7 852 OOS rows). A deliberately
leaky variant — fit window extended to include the rows it predicts — differs by 13.8–52.4 bps,
so the comparison discriminates by ~12 orders of magnitude.

Code pinned by sha256 in `results/integrity_selfcheck.json.code_sha256`.

## 2. Coverage — what the universe actually delivers

| | |
|---|---|
| Pinned symbols (AMENDMENT-U1) | 25 |
| Symbols producing a fitted forecast | **15** |
| Symbols with zero DESIGN estimation history | **10** (listed after the DESIGN window; CONFIRM may not be fitted on, design §7.3) |
| Symbols with no origin in either band | 3 (TIA, PYTH, 1000RATS) — emitted as explicit `UNPOWERED` rows, not dropped |
| Cells | 8 arms × 3 clocks × 25 symbols; 1 022 distinct (arm, symbol, clock, band) cells; 15 143 metric rows |

**Realised sample vs design §6.5 expectation.** The catalog carries a trailing 4-year history
cap, so the earliest 1-minute bar is 2022-07-15 for every symbol except MATICUSDT — most of the
frozen DESIGN band `[2021-06-29, 2023-03-01)` predates the data.

| Band | Median unique dates per cell | Design §6.5 expectation |
|---|---|---|
| DESIGN | 99–102 | 500+ |
| CONFIRM | 286–292 | — |

§6.3 declares a cell UNPOWERED when `MDE = 1.5/√n_dates > 0.10`, i.e. below ~225 unique dates.
DESIGN therefore lands almost entirely in UNPOWERED **by the design's own rule**, irrespective
of effect size.

**Target horizon contiguity** (`target_contiguous_frac`): median 0.96–0.98 per cell, min 0.598
(1000LUNC D1) — 2–40% of targets on the thinnest cells span a longer-than-clock horizon. The
same IC restricted to exactly-one-bar horizons is emitted per cell
(`oos_ic_contiguous_subset`) and tracks the headline closely — CONFIRM medians 0.343 vs 0.338
(H1), 0.304 vs 0.301 (H4), 0.211 vs 0.196 (D1); DESIGN 0.281 vs 0.283 (H1), 0.202 vs 0.202
(H4), 0.105 vs 0.093 (D1) — so the non-adjacent horizons are not carrying the result.

## 3. V-LEVEL — the primary object

Ridge (α=1.0) on `{rv20, ewma_vol, parkinson, gk}`, walk-forward monthly re-fit, forecasting
the next bar's `|open→open|` move. Full per-symbol table: `results/metrics_by_cell.parquet`.

**Out-of-sample rank IC, per band × clock** (15 symbols each):

| Band | Clock | Median IC | Range | Cells with CI-low > 0 | Design label | Disclosure label |
|---|---|---|---|---|---|---|
| CONFIRM | H1 | 0.338 | 0.317 … 0.385 | 15/15 | 15 SUPPORTED | 15 SUPPORTED |
| CONFIRM | H4 | 0.301 | 0.257 … 0.367 | 15/15 | 14 SUPPORTED, 1 UNPOWERED | 15 SUPPORTED |
| CONFIRM | D1 | 0.196 | −0.216 … 0.374 | 13/15 | 13 SUPPORTED, 1 CONTRADICTED, 1 UNPOWERED | 13 SUPPORTED, 1 CONTRADICTED, 1 INDETERMINATE |
| DESIGN | H1 | 0.283 | 0.160 … 0.414 | 15/15 | 1 SUPPORTED, 14 UNPOWERED | 15 SUPPORTED |
| DESIGN | H4 | 0.202 | −0.006 … 0.355 | 12/15 | 1 SUPPORTED, 14 UNPOWERED | 12 SUPPORTED, 3 UNPOWERED |
| DESIGN | D1 | 0.093 | −0.145 … 0.257 | 2/15 | 1 SUPPORTED, 14 UNPOWERED | 2 SUPPORTED, 3 INDETERMINATE, 10 UNPOWERED |

The two label columns differ only in the UNPOWERED rule: `band_label` is the literal §6.3
threshold (prospective MDE), `band_label_detected` is the disclosure companion that calls a
cell unpowered only when the observed effect is below its own detection floor. Every other
threshold is identical. **Both are labels, never gates.**

Four cells are negative. Only one clears its interval: **INJUSDT D1 CONFIRM**, IC −0.216,
CI [−0.339, −0.090] — CONTRADICTED under both label rules. The other three (INJ H4 DESIGN
−0.004, DYDX H4 DESIGN −0.006, DYDX D1 DESIGN −0.145) straddle zero and are UNPOWERED under
both.

**Error reduction against the design's unconditional-mean baseline** (`dmae_vs_uncond`,
positive = model better, bps of |move|):

| Band | H1 | H4 | D1 |
|---|---|---|---|
| CONFIRM | +6.8 (15/15 CI-low > 0) | +11.9 (15/15) | +14.6 (7/15) |
| DESIGN | +5.3 (13/15) | +9.1 (10/15) | +0.5 (2/15) |

Out-of-sample R² against the same baseline: CONFIRM medians 0.151 (H1), 0.142 (H4), 0.019 (D1);
DESIGN 0.115 (H1), 0.087 (H4), −0.061 (D1).

**Model comparison** (median OOS IC on the next |move|):

| Band | Clock | ridge | OLS | EWMA(λ=0.94) |
|---|---|---|---|---|
| CONFIRM | H1 | 0.338 | 0.338 | 0.309 |
| CONFIRM | H4 | 0.301 | 0.301 | 0.282 |
| CONFIRM | D1 | 0.196 | 0.195 | 0.182 |
| DESIGN | H1 | 0.283 | 0.282 | 0.258 |
| DESIGN | H4 | 0.202 | 0.202 | 0.169 |
| DESIGN | D1 | 0.093 | 0.090 | −0.016 |

OLS tracks ridge to within 0.003 IC everywhere — α=1.0 is a negligible penalty at these sample
sizes, so the band cells would be unchanged under either. The parameter-free EWMA(λ=0.94)
carries most of the intraday signal on its own (within 0.03 IC of the fitted models on H1/H4)
but collapses on DESIGN D1.

**`rv_next` target — mechanically predictable, not a skill result.** The design's alternative
target `rv_next_i = rv20_{i+1}` shares 19 of its 20 return terms with the `rv20` feature at the
origin. Median OOS IC 0.968 (DESIGN) / 0.978 (CONFIRM), and an out-of-sample R² of 0.967.
**Every** metric row on that target — `oos_ic`, `oos_mae`, `oos_mae_uncond_baseline`,
`dmae_vs_uncond`, `oos_r2_vs_uncond` — plus `V-PERSIST ic_rv20_vs_rv_next` carries
`target_overlaps_feature = true` and an explanatory note (0 unflagged rows). **These numbers are
not evidence of forecast skill and must not be read as such.**

## 4. Other arms

**V-PERSIST.** Median lag-1 autocorrelation of `|r|`: 0.24–0.28 (H1), 0.19–0.20 (H4),
0.15–0.28 (D1), decaying by lag 5 to 0.09–0.15. Median lag-1 autocorrelation of `rv20`:
0.97–0.98 on every clock (a 20-bar rolling window overlaps 19/20 at lag 1 — mechanical).
Median AR(1) half-life of `|r|`: 0.38–0.55 bars, i.e. the single-bar shock decays within one
bar while the 20-bar level persists. HAR (rv20 + 6-bar + 24-bar means) is the **weakest fitted
model in the screen**: arm-level median OOS IC 0.297 / 0.253 / **0.062** (CONFIRM H1/H4/D1) and
0.245 / 0.145 / **−0.022** (DESIGN), materially below V-LEVEL everywhere and collapsing at D1.
Since HAR is the canonical specification named in RAW §5.1, its daily failure is a result, not a
footnote — `analysis.md` §6.3 traces it to the close-to-close 20-bar input being stale at a
one-day horizon.

**V-MEASURE.** Median univariate IC against the next |move|:

| Band | Clock | rv20 | Parkinson | Garman–Klass | EWMA |
|---|---|---|---|---|---|
| CONFIRM | H1 | 0.299 | **0.322** | 0.320 | 0.309 |
| CONFIRM | H4 | 0.255 | 0.267 | 0.269 | **0.278** |
| CONFIRM | D1 | 0.169 | 0.244 | **0.258** | 0.182 |
| DESIGN | H1 | 0.303 | 0.298 | 0.295 | **0.317** |
| DESIGN | H4 | 0.268 | **0.279** | 0.269 | 0.277 |
| DESIGN | D1 | 0.081 | **0.215** | 0.190 | 0.074 |

The range-based measures (Parkinson, Garman–Klass) beat close-to-close `rv20` on D1 by a wide
margin (+0.09 to +0.13) and are level with it intraday.

**V-CLOCK.** Median incremental OOS R² of session and day-of-week dummies over V-LEVEL alone is
negative at every median, but the magnitude splits in two. On **H1/H4 it is a wash** (−0.0001 to
−0.012 against a base R² of 0.09–0.15; roughly half the cells are positive) — calendar structure
adds nothing and costs nothing. On **D1 the penalty is real** (−0.026 to −0.054) because seven
day-of-week dummies are fitted on ~100 daily observations, i.e. overfitting on a thin sample
rather than evidence the calendar is harmful. Session is structurally degenerate on D1 (all D1
bars open 00:00 UTC) and emits exactly 0.0000. Per design §4 this arm is not a standalone edge
claim.

**V-REGIME** (2-state, rolling-median split on `rv20`). Median HIGH−LOW gap in next |move|.
**Read every bps gap against its own clock's mean |move|** (67.7 / 136.3 / 349.0 bps on CONFIRM
H1/H4/D1): the *relative* separation is flat at 0.22–0.28 across clocks and D1 is the **lowest**,
so the raw bps column below must not be read as "D1 is the strongest regime axis".

| Band | H1 | H4 | D1 |
|---|---|---|---|
| CONFIRM | +16.8 bps (21/22 CI-low > 0) | +32.9 bps (17/21) | +64.6 bps (5/21) |
| DESIGN | +20.7 bps (15/15) | +29.4 bps (6/15) | +89.2 bps (4/15) |

State persistence is high and stable: `P(HIGH|HIGH)` median 0.93–0.95 on every band × clock.
Under the §6.3 gap bands, 8 cells are SUPPORTED, 5 WASH, 9 INDETERMINATE, the rest UNPOWERED —
the §6.3 gap rule leaves 10–15 bps unlabelled, which is where several CONFIRM H1 cells land.

**V-REGIME-HMM** (2-state Gaussian HMM, Baum–Welch, causal forward filtering only). Median
HIGH−LOW gap **larger** than the Markov split on every intraday cell: CONFIRM +54.2 bps (H1),
+75.0 bps (H4); DESIGN +35.9 (H1), +33.3 (H4). D1 is noisy (CONFIRM median +107.7 bps but only
4/13 cells with CI-low > 0, DESIGN range −234 to +307). The HMM state agrees with the
rolling-median state only 51–62% of the time, so the two regime arms are **not** measuring the
same partition. HMM self-transition is much lower (median `P(stay HIGH)` 0.68–0.74) than the
median-split persistence — the HMM switches far more often and still separates magnitude more
sharply.

**V-XS** (same-timestamp cross-sectional `rv20` rank across available universe symbols,
terciles). **Per-symbol** median top-minus-bottom-tercile gap, POOLED row excluded: CONFIRM
+20.7 bps (H1), +41.4 (H4), +65.1 (D1); DESIGN +30.3, +53.1, +74.5. Cells with CI-low > 0:
13/22 (CONFIRM H1), 5/22 (H4), 2/21 (D1); 0/15 on DESIGN D1. Per-symbol dispersion is wide
(H1 CONFIRM range −65 to +58 bps). This is the **weakest** conditioning axis in the screen.
POOLED rows (+62 to +291 bps, all clearing) are disclosure-only (L-03) and are excluded from
every figure above.

**V-TAIL.** HIGH-state minus LOW-state exceedance of the unconditional threshold:

| Band | Clock | above P90 | above P95 |
|---|---|---|---|
| CONFIRM | H1 | +0.06 (20/22 CI-low > 0) | +0.03 (20/22) |
| CONFIRM | H4 | +0.05 (16/21) | +0.03 (12/21) |
| CONFIRM | D1 | +0.04 (2/21) | +0.02 (0/21) |
| DESIGN | H1 | +0.06 (14/15) | +0.04 (14/15) |

A +0.06 exceedance difference against a 0.10 base rate is a ~60% relative increase in the rate
of large moves in the HIGH state, intraday.

## 5. Controls (design §5)

`results/controls.json`, 90 powered cells.

| Control | Form | Seeds | Result |
|---|---|---|---|
| TIME-SHUFFLE-PREDICTORS | circular shift of the predictor series, `U{1..n−1}` | 101–300 (200) | live IC outside the shuffle central 90% in **73 of 90** cells |
| TARGET-LABEL-DERANGEMENT | derangement inside symbol × calendar-month, 0 fixed points | 31000–32999 (**2000**, the design's optional upgrade — wall clock 9.3 min, under the 30-min ceiling) | one-sided p < 0.05 in **68 of 90** cells |
| UNCONDITIONAL-MEAN-BASELINE | nested constant forecast | — | see `dmae_vs_uncond` in §3 |
| Bite / MDE plant | +0.25 rank-correlation synthetic monotone predictor | 50 per form | achieved plant IC ≈ 0.286; destroyed by both forms in every cell |

**TARGET-FUTURE-DESTROY — report layer, no pass field** (AMENDMENT-T1). Under an unrestricted
derangement of every target the null centres at zero (median −0.0002, max |median| 0.005 across
90 cells) while live ICs reach 0.41. Interpretation labels: `COLLAPSED_AS_EXPECTED` 71 cells,
`LIVE_INSIDE_DESTROYED_NULL` 19 cells (live IC within 3 null standard deviations of the
destroyed centre — concentrated on the thin DESIGN D1 cells). Reference bars are expressed in
units of the null's own dispersion, so no bespoke IC constant is asserted.

## 6. Stability across DESIGN thirds (design §6.2)

Both readings are emitted; neither is dropped.

| Reading | Cells with ≥2 of 3 thirds positive | Cells with only one powered third |
|---|---|---|
| `calendar` (literal §6.2 thirds of `[2021-06-29, 2023-03-01)`) | 3 of 45 | **42 of 45** |
| `sample` (equal elapsed time over each cell's own scored span) | 38 of 43 | 1 |

The literal calendar reading is near-vacuous for the reason in §2: its first third lies entirely
before the catalog history cap.

## 7. Design §6.4 clauses on all three candidate bases — **no recommendation**

Operator decision 2026-07-23 (`design.md` AMENDMENT-T2, QA finding F-4): the frozen §6.4
recommendation is **not computed**. The clauses are unsatisfiable as written — the DESIGN band
cannot clear §6.3's date requirement and the sign-stability clause has no second non-empty
calendar third. All three candidate bases are reported side by side; the PASS/STOP call belongs
to the operator at the gate.

| Basis | What it is | Clause 1 (V-LEVEL SUPPORTED ≥10 of 25) | Clause 3 (sign stable in ≥2/3 thirds) | Caveat |
|---|---|---|---|---|
| **A** | CONFIRM window, literal §6.3 labels | **met** — 15 symbols, 43/45 powered cells, 97.8% of cells positive | not defined (thirds are a DESIGN-band object) | §0 designates CONFIRM a verification read, not the estimation read |
| **B** | DESIGN window, literal §6.3 labels — the frozen basis | **not met** — 1 symbol (MATICUSDT), 3/45 powered cells, 93.3% of cells positive | **not evaluable** — 42/45 cells have one powered third | the frozen basis, unsatisfiable for data-availability reasons |
| **C** | DESIGN window, disclosure labels + sample thirds | **met** — 15 symbols, 32/45 powered cells | met — 38/43 cells | both variants are disclosure companions the design never froze |

Clause 2 (destroy controls) is common to all three and is met on the reported counts: 73/90
cells outside the shuffle central 90%, 68/90 with block-derangement p < 0.05.

## 8. Multiplicity (disclosed)

8 arms × 3 clocks × 25 symbols ≈ 600 primary cells as declared in design §4; 1 022 distinct
(arm, symbol, clock, band) cells and 15 143 metric rows are emitted in full to
`results/metrics_by_cell.parquet`. No arm was invented after the run; no cell is hidden behind a
pooled count. Pooled figures appear only as the explicitly-labelled V-XS `POOLED` rows.

## 9. Artifacts

| Artifact | Path |
|---|---|
| Per-origin features, targets and forecasts | `results/vol_reliability.parquet` |
| Per-cell metrics (every arm × clock × symbol × band) | `results/metrics_by_cell.parquet` |
| Block × seed CI grid per bootstrapped metric | `results/ci_grid.json` |
| Control envelopes + future-destroy report layer | `results/controls.json` |
| Integrity self-check, interpretation notes, deviations, code hashes | `results/integrity_selfcheck.json` |
| Universe recompute + pin assertion | `results/universe_recomputed.json` |
| Golden traces G1–G3 | `results/golden_traces.json` |
| Cell diagnostics + model/re-fit log | `results/cell_diagnostics.json` |
| Cross-sectional panel | `results/xs_panel.parquet` |
| Design → code compliance matrix | `results/compliance_trace.md` |
| Fresh-context QA review | `qa-review.md` |
| Full-facet analysis (binding read) | `analysis.md` |
