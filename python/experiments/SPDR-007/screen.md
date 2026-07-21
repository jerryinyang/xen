# SPDR-007 — screen.md (neutral quantification)

**Item:** SPDR-007 · **Family:** CF-SIGAUC-001 · **Lane:** SPDR (TRAIN-only) · **Run:** 2026-07-21
**Bands:** DESIGN estimate → CONFIRM verify (both TRAIN-INTERNAL). **0 counted reads · TEST untouched · holdout SEALED.**
**This file is quantification only — no verdict.** Interpretation is the fresh-context analyst's `analysis.md` (mandatory, SPDR stage 5); the operator signs the disposition. Numbers are magnitudes, not adjudications.

Frozen inputs verified at entry: instrument registry `5c386984…`, A5 baselines `1b7244c8…`, `SpreadBps` UNUSABLE. Protection freeze pin `b0871cf0…`.

## Population (measured, frozen rule D4-t50-w30 δ=0)

| Band | Panel symbols | A6-accepted events (population) |
|---|---|---|
| DESIGN | 140 | **7,070** |
| CONFIRM | 187 | **11,375** |

## R0 — money floor (computed first)

Cost floor ≈ 14.2–16.9 bps round-trip (taker 11.0 + spread + funding). Protection Level TP1 (pooled p70) = **1.796 IB widths** ≈ 90–170 bps on the majors — well above the floor. **The floor is not the binding constraint for this family** (unlike prior chapter-04 families). Per-symbol table: `results/floor_table.json`; plot `plots/05_money_floor.png`.

## R1 — Protection-quantile reproduction (the master gate)

Estimated on DESIGN, verified once on CONFIRM. **The quantile reproduces out of its estimation band:**

| p (nominal hit) | q̂ (IB widths, DESIGN) | realised CONFIRM hit rate | calibration error |
|---|---|---|---|
| 0.65 | 2.175 | 0.680 | **+0.030** |
| 0.70 | 1.796 | 0.728 | **+0.028** |

Both within the design's REPRODUCES label (|err| ≤ 0.05). Plot `plots/02_calibration_master_gate.png`. Source framework-falsifier #1 ("no anchor reproduces a ~65–70% Protection quantile") is **not** triggered on reproduction grounds. **Caveat, binding (design §0, D6):** reproduction alone can hold on any distribution with quantiles — the conditioning question is R2–R5 below.

## R2–R5 — does the acceptance conditioning add over a matched unconditional entry?

Matched control = same phase, same side, arbitrary session, unconditional on acceptance (cross-session; see DEVIATION D-1). Every read is signal **minus** that control.

| Read | Signal | Control | Contrast | Note |
|---|---|---|---|---|
| **R2 race win-rate** p65 | 0.342 | 0.340 | **+0.002** | gross breakeven = 0.333 |
| **R2 race win-rate** p70 | 0.333 | 0.343 | **−0.010** | signal sits **at** gross breakeven |
| **R5 excursion asym** (day-clustered) | — | — | **CI [−0.23, +0.32]** | includes zero; MDE 0.50 (WASH) |
| **R3 regime** ρ(ib_width_pctl, mfe_norm) | −0.220 | −0.350 | **+0.130** | contrast-only (normaliser guard); raw-MFE disclosure ρ = +0.119 |
| **R4 Δ-coherence** top−bottom tercile | 3.708 | 3.632 | **+0.077 IBw** | n=6,961; small |

Plots: `03_regime_terciles.png`, `04_coherence_terciles.png`, `01_mfe_distribution_protection.png`.

## Integrity (HARD — all clean)

| Check | Result |
|---|---|
| Future-destroy tripwire (outcome-path-swap) | **NO_MATERIAL_EDGE** — raw excursion contrast CI includes zero, so nothing material to leak-test; not a hard fail |
| Tripwire positive-control bite | **corr 0.77** (swap installs the donor outcome; genuine teeth) |
| Band fences / freeze-before-CONFIRM / causal ≤ t−1 / no per-level Δ / no local accounting | asserted, clean |

## Power notes (report layers)

- Per-symbol median ~34 (DESIGN) / ~51 (CONFIRM) events; most per-symbol strata predeclared UNPOWERED (B-5) — pooled reads are primary here.
- **Side-derangement control is UNPOWERED:** only 60 of 7,070 events were derangeable within calendar-day blocks (2,694 singleton-day + 4,316 one-side-dominant dropped and counted). Its collapse fraction is not interpretable. Reported as power, not a negative.

## Two developer deviations from design (require operator ratification — see `code/` DEVIATIONS + report)

- **D-1 — matched control is CROSS-SESSION, not within-session.** The design's within-session phase-matched control is infeasible (the event occupies the early-session phase = the exclusion band; a within-session draw is forced mid-session, reintroducing the horizon confound QA I-2 fixed — measured 723 vs 1391 min). The control now draws donor sessions at the event's own phase/side. Direction: removes the confound.
- **D-2 — the HARD tripwire fires only on a MATERIAL raw edge** (its interval excludes zero). A future-destroy cannot leak-test an edge that does not exist; the positive-control bite still proves teeth regardless. Direction: soundness precondition; a material surviving edge still hard-fails.

Raw per-event data for the analyst: `results/spine_events_{DESIGN,CONFIRM}.parquet`, `spine_control_DESIGN.parquet`, `layers.json`, `tripwire.json`, `protection_freeze.json`, `floor_table.json`.
