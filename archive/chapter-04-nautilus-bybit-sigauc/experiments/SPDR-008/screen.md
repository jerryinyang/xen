# SPDR-008 — screen quantification (neutral; subordinate to `analysis.md`)

**Item:** SPDR-008 · CF-SIGAUC-001 signed-trap breadth (S3 Δ+) · SPDR lane, TRAIN-only, 0 reads.
**Status:** screen run complete; **disposition deferred to the fresh-context analyst (`analysis.md`) and the operator.** This file is quantification only — no verdict, no tradability claim (spdr-lane §Stage 5). Magnitudes below are pooled/per-boundary; the per-stratum table lives in `results/` (`allocation_map.parquet`, `layers.json`).

## Run scope
- Universe: **194 A5-fitted symbols** (signed-read universe; design breadth denominator 296 — survivorship caveat binding, ckpt-014 AMENDMENT-1). DESIGN **16,669** traps / CONFIRM **26,348**, across IB/PVA/PRIOR.
- Frozen inputs verified at entry: registry `5c386984…`, baselines `1b7244c8…`, kernel K-UNIFORM; `assert_ib_matches_frozen` passes (IB path byte-identical to the frozen apparatus). Golden traces reproduce exactly (`design_derivations/gt_output.txt`).
- Full adjudication machinery (design §4, amendments 7–8): T1 monotonicity + 2000-seed derangement + MDE; T2 tier contrast + day-clustered CI + MDE; T3 ordinary-touch; T4 availability + day-clustered CI + MDE; reversal_path_swap tripwire (signed-read collapse + bite + material-edge precondition); per-cell derangement + K=3 scan.

## T1 — load-monotonicity (PRIMARY signed) — `ρ(trap_load, mfe_rev_norm)`

| boundary | DESIGN ρ | one-sided p | MDE_ρ | CONFIRM ρ | SUPPORTED |
|---|---|---|---|---|---|
| IB | −0.015 | 0.90 | 0.020 | +0.0001 | no |
| PVA | +0.023 | 0.052 | 0.023 | −0.006 | no |
| PRIOR | −0.033 | 0.99 | 0.023 | +0.004 | no |

The single sub-0.05 cell (PVA/DESIGN) sits **at** its MDE and does not reproduce on CONFIRM. Raw-bps disclosure ρ (I-3 normaliser guard) is emitted alongside in `layers.json`.

## T2 — HIGH−LOW tier marginal (signed) — paired-day contrast
All six (boundary × band) paired-day CIs **span zero**; MDEs 0.25–0.75 IB-widths. `unpaired_diff` −0.27 to +0.34.

## T3 / T4 — unsigned base (P-01 disclosure) and availability
- T4 (trap vs matched cross-session random-timing control): contrast **+0.07 to +0.48** IB-widths; day-clustered CI excludes zero on PVA (both bands) and PRIOR (both bands); IB mixed. `mde_ibw` published per cell.
- T3 (trap vs ordinary non-trap boundary touch): `contrast_geometry` **+0.70 to +0.97** IB-widths.
- These availability lifts are **not load-dependent** (T1/T2 flat) — the analyst adjudicates whether they are failed-break price geometry (P-01) or otherwise.

## Tripwire — reversal_path_swap (future-destroy, HARD)
Status **NO_MATERIAL_EDGE** on all cells: with no material signed edge (T1 ρ≈0, T2 CI spans 0) the collapse ratio is noise/noise and not adjudicated (design §4.3 material-edge precondition; SPDR-007 D-2). Pooled bite `corr(swapped price MFE, donor real MFE)` **0.53–0.92 (>0.5)** — the swap has teeth. It adjudicates the SIGNED reads (T1 ρ / T2 tier collapse under swap); the T4 mean is not swap-adjudicated (B-6 mean-vacuity) — its causality rests on ≤t−1 + the matched control.

## K=3 cluster scan (per-cell derangement + CONFIRM sign-agreement)

| boundary | powered cells (n≥20) | signed-supported | ρ>+0.10 | ρ<−0.10 | raw K=3 flag |
|---|---|---|---|---|---|
| IB | 96 | 6 | 20 | 19 | met (raw count) |
| PVA | 69 | 1 | 21 | 14 | not met |
| PRIOR | 76 | 0 | 17 | 23 | not met |

The per-boundary positive/negative ρ split is ~symmetric. The IB "6/96" is a raw count of cells passing (per-cell p≤0.05 ∧ ρ≥MDE ∧ CONFIRM sign>0); **whether it exceeds the null false-qualifier budget, and whether the 6 form a connected region, is the analyst's multiplicity adjudication (L-03 / §12) — not settled here.**

## Money floor (§6.1 / L-21)
Per-symbol DESIGN-median `ib_width_bps` + cost floor (taker RT 11 + funding ≈3 + tick/flip spread; `SpreadBps` UNUSABLE) emitted to `results/floor_table.json`. Availability ≠ tradability (SPDR lane).

---
*Binding read is `analysis.md` (fresh-context analyst). Disposition is the operator's, on the analyst's evidence.*
