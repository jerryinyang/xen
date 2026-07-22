# SPDR-007 — screen.md (neutral quantification)

**Item:** SPDR-007 · **Family:** CF-SIGAUC-001 · **Lane:** SPDR (TRAIN-only) · **Run:** 2026-07-21 (re-emit after QA run 2 fixes)
**Bands:** DESIGN estimate → CONFIRM verify (both TRAIN-INTERNAL). **0 counted reads · TEST untouched · holdout SEALED.**
**This file is quantification only — no verdict.** Interpretation is the fresh-context analyst's `analysis.md` (mandatory, SPDR stage 5); the operator signs the disposition. Numbers are magnitudes, not adjudications.

Frozen inputs verified at entry: instrument registry `5c386984…`, A5 baselines `1b7244c8…`, `SpreadBps` UNUSABLE. Hard integrity asserted (no local accounting; per-level Δ barred).

## Population (measured, frozen rule D4-t50-w30 δ=0)

| Band | Panel symbols | A6-accepted events (evaluable spine) |
|---|---|---|
| DESIGN | 140 | **7,070** (= 7,148 accepts − 78 missing entry) |
| CONFIRM | 187 | **11,375** |

## R0 — money floor (computed first; CONVERSION-PIN = DESIGN-session median)

Cost floor ≈ 14.2–16.0 bps round-trip (taker 11.0 + spread + funding). Divisor object = **all DESIGN sessions with ib_width>0** (not accept-event medians). Majors match design pin: BTC 48.745 · ETH 69.958 · SOL 96.217 · DOGE 86.969 · XRP 60.753 bps.

Protection Level TP1 (pooled p70) = **1.796 IB widths**. TP1-must-exceed floor (IB widths): BTC 0.292 · ETH 0.204 · SOL 0.153 · DOGE 0.178 · XRP 0.263. **The floor is not the binding constraint for this family.** Per-symbol table: `results/floor_table.json`; plot `plots/05_money_floor.png`.

## R1 — Protection-quantile reproduction (the master gate)

Estimated on DESIGN, verified once on CONFIRM (pooled + per-symbol).

| p (nominal hit) | q̂ (IB widths, DESIGN) | realised CONFIRM hit rate | calibration error |
|---|---|---|---|
| 0.65 | 2.175 | 0.680 | **+0.030** |
| 0.70 | 1.796 | 0.728 | **+0.028** |

Pooled within REPRODUCES (|err| ≤ 0.05). **Per-symbol (p70) includes SOL calib_err +0.105 (BROKEN label)** — pooled masks this; full table in `layers.json` → `R1_calibration_master_gate.per_symbol`. Plot `plots/02_calibration_master_gate.png`.

## R2–R5 — does the acceptance conditioning add over a matched unconditional entry?

Matched control = same phase, same side, other session, unconditional on acceptance (cross-session; D-1). Horizons match (signal/control median **1391 / 1391** min; full disclosure in layers).

| Read | Signal | Control | Contrast | Note |
|---|---|---|---|---|
| **R2 race win-rate** p65 | 0.342 | 0.340 | **+0.002** | gross breakeven = 0.333 |
| **R2 race win-rate** p70 | 0.333 | 0.343 | **−0.010** | cost-adj p0ᶜ (BTC) ≈ 0.44; pooled median p0ᶜ ≈ 0.38; MDE in w-units = 0.03 |
| **R5 excursion asym** (day-clustered) | — | — | **CI [−0.23, +0.32]** | includes zero; MDE 0.50 (WASH) |
| **R3 regime** ρ(ib_width_pctl, mfe_norm) | −0.220 | −0.350 | **+0.130** | contrast-only (normaliser guard) |
| **R4 Δ-coherence** mfe top−bottom | 3.708 | 3.632 | **+0.077 IBw** | n=6,961 |
| **R4 Δ-coherence** race w top−bottom | — | — | **+0.012** | same TP1 (p70) |

Time stability (three DESIGN chronological thirds, n≈2356 each): reported in `layers.json` → `time_stability_thirds` (not gated).

Spread-scale routing: **2 / 140** symbols `t1_undecidable` (3× RT-spread threshold); remainder T1-decidable on this contrast scale. Full table in `layers.json` → `spread_scale_routing`.

## Integrity (HARD — all clean)

| Check | Result |
|---|---|
| Future-destroy tripwire (R2/R3/R4/R5 contrasts) | **NO_MATERIAL_EDGE** — no material raw edge; not a hard fail |
| Tripwire positive-control bite | **corr 0.77** |
| Band fences / freeze-before-CONFIRM / causal ≤ t−1 | asserted, clean |
| `check_no_local_accounting` + `assert_no_per_level_delta` | **invoked at runner entry**, raise on fail |
| D-1 control disjoint (GT-4e replacement) | asserted; 0 control entries inside event session |

## Power notes (report layers)

- Per-symbol median ~34 (DESIGN) / ~51 (CONFIRM) events; most per-symbol strata predeclared UNPOWERED (B-5) — pooled reads are primary here.
- **Side-derangement control is UNPOWERED:** only a small derangeable subset within calendar-day blocks. Reported as power, not a negative.
- R2 MDE plant published in **w-contrast units** (MDE = 0.03).

## Two developer deviations (operator-ratified 2026-07-21)

- **D-1 — matched control is CROSS-SESSION** (within-session phase match is infeasible; reintroduces horizon confound).
- **D-2 — HARD tripwire fires only on a MATERIAL raw edge** (interval excludes zero); bite still required.

Raw data: `results/spine_events_{DESIGN,CONFIRM}.parquet`, `spine_control_DESIGN.parquet`, `layers.json`, `tripwire.json`, `protection_freeze.json`, `floor_table.json`.
