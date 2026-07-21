# Data Analysis: SPDR-008 — signed-trap breadth screen (CF-SIGAUC-001, S3 Δ+)

Fresh-context data-analyst pass (SPDR stage 5, mandatory). I did not build this screen.
All numbers recomputed from the raw emissions (`results/*.parquet|json`) via my own
`analysis_code/interrogate.py`; no experiment-local analysis code imported. This is a
TRAIN-only breadth SCREEN — availability/disposition only, 0 counted reads, no TEST/holdout
contact, no tradability claim, registers nothing. Disposition is the operator's; mine is a
recommendation on the experiment's hypothesis only.

**Hypothesis under test (S3 SIGNED warrant):** after a poke beyond a session boundary fails
acceptance (frozen A6=D4-t50-w30) and reclaims inside (a "trap"), reversal excursion toward
the opposite edge is **MONOTONE in the MEASURED trap load** (`trap_load = poke_side × Σ
delta_ratio_resid`, signed by the taker aggressor split — not price geometry), and HIGH-load
traps rotate further than LOW-load traps of the same geometry. Tested INDEPENDENTLY per
boundary type {IB, PVA, PRIOR}. The screen exists because the price-only spine (SPDR-007)
came back NOT_WORTH/P-01: SPDR-008 asks whether *measured flow* adds what geometry cannot.

---

## 1. Integrity gate (SPDR substitute — code-asserted fences + causal self-check)

SPDR lane: no `estimand_validation.json` gate (no P&L booked). The integrity substitute is the
code-asserted band fence + causal ≤t−1 self-check + no-local-accounting + derangement discipline.
All HARD checks below were traced in the shipped code AND re-verified against the raw emission.

| Check | Result | Evidence |
|---|---|---|
| Band fences (DESIGN/CONFIRM only; TEST≥2023-12-18 & holdout≥2025-01-08 raise) | PASS | `fences.assert_band`/`load_bars` (`fences.py:80-140`): filters `[start,end)`, raises on holdout. `assert_frozen_inputs` re-hashes 4 pins at entry. |
| Causal ≤t−1 (entry after reclaim; outcome after entry) | PASS | Recomputed on all 16,669 DESIGN events: `entry_ts != reclaim_ts+1min` = 0; `reclaim_ts < poke_ts` = 0; `n_post≤0` = 0. Trap load summed over poke bars ≤ reclaim_ts (`trap.py:260-265`). PVA/PRIOR levels from the PRIOR closed session (`trap.boundary_levels`). |
| Leak tripwire collapsed + non-vacuous (bite>0.5) | PASS (NO_MATERIAL_EDGE, correct) | `reversal_path_swap` (future-destroy, HARD). Bite `corr(swapped price MFE, donor real MFE)` = 0.53 / 0.82 / 0.92 / 0.57 / 0.62 / 0.67 across the 6 cells — all >0.5, swap has teeth. Adjudicates SIGNED reads only (T1 ρ, T2 tier); status NO_MATERIAL_EDGE because no signed read is material (T1 ρ≈0, T2 CI spans 0). Correct: a destroy cannot leak-test an edge that does not exist. |
| Holdout untouched | PASS | Only DESIGN/CONFIRM bands loaded; `assert_band` seals ≥2025-01-08. |
| Price-primary / vehicle | N/A (SPDR) | Vectorised Python screen, operator-sanctioned lane; no cTrader/estimand gate. A `WORTH_EXPLORING` would graduate into the Nautilus pipeline where those bind. |
| No per-level Δ (card ban 2) | PASS | `fences.assert_no_per_level_delta` guards the profile kernel (Volume-only); trap load reads per-BAR `delta_ratio_resid`. |
| No experiment-local accounting | PASS | `check_no_local_accounting` run on `screen_code`+`analysis_code` at `main()` start; excursions computed in `xen.sigbar`, no booked P&L. |
| Frozen apparatus unchanged / IB regression | PASS | `assert_ib_matches_frozen` (byte-identical to SPDR-007's IB reject set) runs on DESIGN and passes; golden trace reproduces all 4 GT events exactly (QA-3 verified). |
| Derangements zero fixed points (L-28) | PASS | `trap.derange` / `spine` derangements regenerate until 0 fixed points, asserted. |

Verdict on validity: the emission is VALID. The null signed result is a genuine "no edge", not
an invalidity. No integrity firewall is breached; nothing corrupt is validated.

Non-invalidating deviations noted (do not change validity, flagged for honesty):
- Entry-bar inclusion in the excursion window. `trap.find_traps` measures MFE/MAE over
  `OpenTime > reclaim_ts` (= `[entry_ts, session_end)`, includes the entry bar), while the matched
  control / ordinary-touch arms (`spine.evaluate_entries`) use `OpenTime > entry_ts` (excludes it).
  The design table says `(reclaim_ts, session_end)`, so the code matches the table; the "entry bar
  excluded" annotation in §2 is loose. Causal (you hold through the entry bar after entering at its
  open). Materiality: one bar of a median 1,342-bar window = 0.07% — immaterial to a running max/min.
- T4 CI treats the control mean as a fixed constant (no control-side resampling) → understates
  uncertainty on the contrast. T4 is P-01/disclosure anyway.

---

## 2. Question list (every question answered)

1. Signed warrant supported anywhere (T1/T2, per boundary, pooled+per-symbol, UNPOWERED first)? → §3/§4 A1–A4. No.
2. PVA DESIGN p=0.052 whiff — real or boundary-of-MDE artifact? → §4 A3. Artifact; below its own MDE, flips negative on CONFIRM.
3. K=3 IB 6/96 — signal or noise? → §4 A4 (THE call). Noise.
4. T4/T3 availability edge — P-01 geometry or measured-flow contribution? → §3 F1 / §4 A5. Unsigned P-01 geometry; PVA/PRIOR reproduce, IB does not; not load-dependent.
5. Integrity/tripwire valid? → §1. Valid; NO_MATERIAL_EDGE correct; bite>0.5; no leak.
6. Money floor / L-21 — reversal above/below ~14 bps floor? → §4 A6. Signed marginal value is a wash (no CI clears 0, sign-unstable); unsigned availability ceiling ~30–56 bps > floor but is MFE (not realized) and P-01.
7. Estimator honesty of the T4 "excludes zero" flags? → §4 A5. IB's flag is a day-weighting artifact; PVA/PRIOR robust.
8. Outlier/tail sensitivity of the mean contrasts (L-20)? → §5. Means tail-driven (median 3.5 vs mean 5.5, q99 ~30); contrasts of means fragile, but the signed null holds on ranks (ρ).

---

## 3. Evidence FOR the hypothesis

Assembled with equal diligence. The supporting evidence is thin and does not survive scrutiny.

- F1 (unsigned, P-01) — a real failed-break reversal availability edge on PVA/PRIOR. Confirmed
  traps revert more than matched random-timing entries (T4) and more than ordinary non-trap touches (T3):
  - T4 pooled event-weighted contrast (IB-width units): PVA +0.479 (DESIGN) / +0.295 (CONFIRM);
    PRIOR +0.484 / +0.270 — both bands positive, day-clustered CI excludes zero on both, both
    estimators agree. ≈ +31 to +56 bps at the 116.5 bps median IB width.
  - T3 (trap vs ordinary touch), DESIGN: IB +0.78, PVA +0.97, PRIOR +0.97 IB-widths.
  - Genuine turning-point excursion — BUT UNSIGNED (any load), failed-break price geometry = the
    P-01 base the card bars from being the family warrant.
- F2 — IB per-cell positive lean. 6/96 cells pass the per-cell signed gate (per_cell_p≤0.05 AND
  CONFIRM ρ>0), all 6 with high_low_diff>0, vs an analytic per-boundary null expectation ~2.4.
- F3 — PVA DESIGN monotonicity whiff. T1 ρ(PVA, DESIGN)=+0.0229, one-sided derangement p=0.052 —
  the single read closest to significance in the whole screen.

Every one of F1–F3 is refuted or reframed in §4.

---

## 4. Evidence AGAINST the hypothesis

### A1 — Pooled T1 load-monotonicity is ≈0 and powered-null on all three boundaries.
ρ(trap_load, mfe_rev_norm) vs its ≥2000-seed derangement null. n = 4,600–10,900 per cell; POWERED
(MDE ~0.02), all `UNPOWERED=false` (B-5 checked first).

| Boundary | DESIGN ρ (p) | MDE | CONFIRM ρ (p) | Reads |
|---|---|---|---|---|
| IB | −0.015 (0.90) | 0.020 | +0.00005 (0.48) | null both bands |
| PVA | +0.023 (0.052) | 0.023 | −0.006 (0.69) | DESIGN whiff below MDE, flips negative on CONFIRM |
| PRIOR | −0.033 (0.99) | 0.023 | +0.004 (0.36) | anti-monotone DESIGN, null CONFIRM |

All `SUPPORTED=false`. Un-normalised bps disclosure ρ(trap_load, MFE_rev_bps) is also ≈0 to mildly
negative everywhere (−0.023 to −0.055) → null is not a normaliser-mechanic artifact.

### A2 — T2 signed marginal value (HIGH−LOW) is a wash on every boundary and band.
Paired-day block-bootstrap CI on HIGH−LOW `mfe_rev_norm` spans zero in all six cells; sign unstable:

| Boundary | DESIGN HIGH−LOW (bps) | CONFIRM HIGH−LOW (bps) | CI excl 0? |
|---|---|---|---|
| IB | −0.308 ibw (−36) | +0.001 ibw (+0.1) | No / No |
| PVA | +0.027 ibw (+3) | +0.469 ibw (+55) | No / No |
| PRIOR | −0.220 ibw (−26) | +0.083 ibw (+10) | No / No |

Large-looking bps swings, none distinguishable from zero, DESIGN/CONFIRM signs disagree. No signed marginal value.

### A3 — The PVA p=0.052 whiff is a boundary-of-MDE artifact that does not reproduce.
ρ=+0.0229 sits below its own MDE (0.0234) — at best SUGGESTIVE, never SUPPORTED. On CONFIRM it flips
to ρ=−0.0058 (p=0.69). A real monotone effect reproduces in sign; this inverts. One draw at the edge
of a 2,000-seed null, exactly what a null throws up ~5% of the time.

### A4 — THE K=3 CALL: the IB 6/96 is within the two-sided null budget → NOISE.
Per-cell gate ≈ [DESIGN ρ top 5% of own derangement null] AND [CONFIRM ρ>0] ≈ 0.05×0.5 = 0.025
false-qualifier prob per powered cell. Null budget two ways:
- Analytic: 241 powered cells × 0.025 = 6.0 expected false qualifiers. Observed = 7 (IB 6 + PVA 1 + PRIOR 0). At budget.
- Empirical symmetric-null (mirror gate = anti-monotone [DESIGN ρ bottom 5%] AND [CONFIRM ρ<0]):
  observed 7 supported vs 10 mirror. Positive tail NOT enriched over negative (PRIOR alone: 0 vs 6).

| Boundary | powered | p≤.05 → SUPPORTED | mirror (anti) | analytic null exp |
|---|---|---|---|---|
| IB | 96 | 8 → 6 | 2 | 2.4 |
| PVA | 69 | 1 → 1 | 2 | 1.7 |
| PRIOR | 76 | 2 → 0 | 6 | 1.9 |
| Total | 241 | 7 | 10 | 6.0 |

Reinforcing evidence the IB cluster is noise:
- Pooled IB T1 ρ = −0.015 (negative, p=0.90) — aggregate IB monotonicity is null/negative.
- IB per-cell ρ split symmetric: 20 with ρ>+0.10, 19 with ρ<−0.10; median ρ = +0.002.
- The 6 symbols are scattered, unrelated names (1000BONK, LTC, BCH, FLOW, DYDX, SOL) at a single
  hold (session). Design K=3 requires ≥3 CONNECTED cells + "best cell not the only positive in its
  neighbourhood." One hold, no symbol adjacency ⇒ no neighbourhood structure ⇒ design's K=3 is
  unsatisfiable by construction here. The code's `cluster_K3_met=True` is a raw count ≥3, not the connectivity rule.
- CONFIRM reproduction is sign-only and weak. DESIGN ρ for the 6 = 0.16–0.42; CONFIRM ρ = 0.016–0.168
  (median 0.0585) — shrunk ~1/4–1/10. Smallest-n cells (FLOW n=24 ρ=0.42, BONK n=28 ρ=0.33, BCH n=33
  ρ=0.37) have the largest DESIGN ρ and near-zero CONFIRM ρ. Textbook winner's-curse selection.

Ruling: no real cluster survives. IB 6/96 is a null false-qualifier count (7 vs 6 expected, fewer
than the 10 anti-monotone mirror cells), scattered non-connected names, weak sign-only reproduction,
atop a pooled IB ρ that is itself negative.

### A5 — The only reproducing edge (T4/T3 availability) is UNSIGNED, P-01, and IB doesn't reproduce.
- Not load-dependent (T1/T2 wash) — failed-break geometry, the P-01 base. SPDR-007 already
  dispositioned the price-only spine NOT_WORTH → twice-dead, non-promotable (design §4).
- IB T4 "excludes zero" is a day-weighting artifact. Reported `contrast` is event-weighted pooled;
  `day_clustered_ci` is centered on the unweighted day-mean. IB DESIGN pooled = +0.043 (≈0) while
  day-mean = +0.702 → CI [0.24, 1.21] driven entirely by day weighting. IB CONFIRM pooled is NEGATIVE
  (−0.494), CI includes zero. IB availability does NOT reproduce. Only PVA/PRIOR robust (pooled +
  day-mean agree, both bands positive), and even those rest on a CI ignoring control sampling variance.

### A6 — Money floor: nothing signed clears it; the unsigned availability that does is a ceiling, not a return.
- Median `design_median_ib_width_bps` across 189 symbols = 116.5 bps (q25 99, q75 146). Cost floor
  ex-spread = 14 bps (taker 11 + funding 3) + per-symbol spread at graduation.
- Signed marginal value (T2 HIGH−LOW): −36 to +55 bps but no CI clears zero, signs flip DESIGN↔CONFIRM.
  Not reliably above or below the floor — a wash.
- Unsigned availability (T4, PVA/PRIOR): ~31–56 bps gross > 14 bps floor — but MFE (availability
  ceiling, not realized exit) and P-01 geometry. Availability ≠ tradability (SPDR lane). Cannot support the signed warrant.

---

## 5. Anomalies & open questions

- Heavy right tails on `mfe_rev_norm` (median 3.2–3.6 vs mean 4.9–5.5, q99 ~25–32, max 141–211
  IB-widths) — small-IB-width sessions inflate normalised excursion. Every mean-based contrast
  (T2/T3/T4) is tail-fragile; the rank-based T1 ρ (the primary) is immune and is cleanly null. A
  median/trimmed T4 re-read would tighten the P-01 characterisation but cannot revive the signed warrant.
- T4 estimator mismatch (event-weighted point vs day-mean CI). If T4 is ever a headline number,
  align point and CI on one weighting and add control-side resampling. Does not affect disposition.
- 5 symbol skips (DESIGN: BUSD/CKB/NKN/PAXG; CONFIRM: BUSD/DENT/PAXG/SUN) from missing
  anchor_ts/schema — logged in run_log and counted in `layers.symbols_skipped` (4/4). Minor, disclosed.
- Survivorship caveat (binding, ckpt-014 AMENDMENT-1): the 189 symbols with events (of 194 A5-fitted,
  of 296 breadth denominator) are precisely instruments listed before train_end — an older-listing
  subset, not the venue as a whole. Every breadth read carries this.

---

## 6. Recommended disposition (experiment hypothesis only — NOT final, NOT family)

Recommended: NOT_WORTH (for the S3 SIGNED warrant — measured trap-load monotonicity).

Powered (pooled T1 MDE ≈ 0.02 on thousands of events; not UNPOWERED/B-5) → genuine "no signed edge",
not "cannot see" → NOT_WORTH, not INCONCLUSIVE.

Driven by the 3 decisive magnitudes:
1. Pooled load-monotonicity is powered-null on all three boundaries: T1 ρ = −0.015 (IB), +0.023
   (PVA), −0.033 (PRIOR); MDE ~0.02; the whiff (PVA p=0.052) is below its own MDE and flips to −0.006
   on CONFIRM. T2 HIGH−LOW CI spans zero everywhere with sign-unstable DESIGN↔CONFIRM.
2. K=3 IB 6/96 within the two-sided multiplicity null budget: 7 "supported" vs 6.0 analytic-null
   expectation and vs 10 anti-monotone mirror cells; scattered/non-connected names, weak sign-only
   CONFIRM reproduction, negative pooled IB ρ. No cluster survives.
3. The only reproducing edge is unsigned P-01 geometry (T4/T3 availability, ~31–56 bps on PVA/PRIOR;
   IB does not reproduce), not load-dependent, twice-dead (SPDR-007). Measured flow adds nothing price geometry did not.

Would change if: a per-cell derangement-adjusted CONNECTED cluster showed a positive tail materially
exceeding its anti-monotone mirror AND CONFIRM ρ reproducing in magnitude (not just sign) — none present.

The unsigned availability edge (PVA/PRIOR, ~30–55 bps MFE-availability) is genuine and worth recording
as market science, but it is not the family warrant and not a tradability claim.

Final verdict is the operator's.

---
*Persisted by the orchestrator from the stage-5 fresh-context analyst's returned deliverable (the
subagent report-file guard blocked its own write). Reproducible from `analysis_code/interrogate.py`
against `results/`.*
