# SPDR-008 — Report: signed-trap breadth (S3 Δ+), CF-SIGAUC-001 Phase-5 sweep

**Item:** SPDR-008 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4 seq 4 (source Phase 5) · **Lane:** SPDR (TRAIN-only screen)
**Operator disposition (signed 2026-07-21):** **`NOT_WORTH`** — for the S3 **signed** warrant (measured trap-load monotonicity). A screen disposition, not a family status change; family stays **REGISTERED** (keep/close is a checkpoint-014 retrospective act).
**Analyst recommendation:** NOT_WORTH (matches). **0 counted reads · holdout SEALED · no TEST contact · registers nothing.**

---

## 1. Question & mechanism

Does the **measured** taker-flow of a failed breakout add reversal-predictive information that price geometry does not? Mechanism (source S3): a poke beyond a session boundary that fails acceptance (frozen A6=D4-t50-w30) and closes back inside traps the aggressors; their forced unwind fuels a reversal toward the opposite edge. The data-tier-new, falsifiable claim: reversal excursion is **monotone in the measured trap load** (`trap_load = poke_side × Σ delta_ratio_resid`, signed by the aggressor split — not geometry), and HIGH-load traps rotate further than LOW-load traps of the same geometry. This screen exists because the **price-only** spine (SPDR-007) came back NOT_WORTH/P-01; SPDR-008 tests the deferred signed warrant.

## 2. Scope

- **Boundaries tested INDEPENDENTLY:** IB (opening-range edge), PVA (prior value-area edge, K-UNIFORM proxy profile), PRIOR (prior session extreme). No cross-boundary pooling; a K=3 cluster must live within one boundary type.
- **Universe:** 194 A5-fitted signed-universe symbols (design breadth denominator 296; **survivorship caveat binding** — the covered set is instruments listed before train_end). DESIGN **16,669** traps / CONFIRM **26,348**.
- **Bands:** DESIGN `[2021-06-29, 2023-03-01)` estimation; CONFIRM `[2023-03-01, 2023-12-18)` verification, TRAIN-INTERNAL. TEST/holdout never touched.
- **Frozen inputs:** registry `5c386984…`, baselines `1b7244c8…`, kernel K-UNIFORM. IB reuses the frozen apparatus byte-identically (`assert_ib_matches_frozen` passes); golden traces reproduce exactly.

## 3. Method

Vectorised Python screen (SPDR lane). One new shared module `xen.sigbar.trap` (IB reuses `acceptance.*` unmodified; PVA/PRIOR add regression-guarded level-generalised plumbing). Reads (report layers, INFR-016): **T1** load-monotonicity ρ vs 2000-seed derangement null + MDE; **T2** HIGH−LOW tier contrast + day-clustered CI + MDE; **T3** ordinary-touch (P-01 disclosure); **T4** availability vs matched cross-session random-timing control + CI; **reversal_path_swap** tripwire (future-destroy, HARD) with pooled bite; per-cell derangement + K=3 scan. Money floor per L-21. Full machinery added at amendment 7; tripwire corrected at amendment 8.

## 4. Key evidence (per stratum; pooled disclosure-only — L-03)

### Signed warrant — NOT supported (powered null)

| Boundary | T1 ρ DESIGN (p) | MDE_ρ | T1 ρ CONFIRM | T2 HIGH−LOW CI |
|---|---|---|---|---|
| IB | −0.015 (0.90) | 0.020 | +0.0001 | spans 0 |
| PVA | +0.023 (0.052) | 0.023 | −0.006 | spans 0 |
| PRIOR | −0.033 (0.99) | 0.023 | +0.004 | spans 0 |

All `SUPPORTED=false`. n = 4,600–10,900/cell → POWERED (MDE ≈ 0.02): a genuine "no signed edge", not "cannot see" (B-5). The single sub-0.05 read (PVA/DESIGN) sits **below its own MDE** and **flips negative on CONFIRM**. Raw-bps ρ (I-3 guard) is also ≈0/negative → not a normaliser artifact. T2 tier contrast is a wash on every boundary/band, sign-unstable DESIGN↔CONFIRM.

### K=3 cluster — ruled NOISE (the multiplicity call)

IB shows 6/96 "signed-supported" cells (raw count ≥3). But across all 241 powered cells: **7 pass the positive gate vs 6.0 expected under the null** (241 × 0.05 × ½-CONFIRM), and **10 pass the anti-monotone mirror gate** — the positive tail is not even enriched over the negative. The 6 IB names are scattered/unconnected at a single hold (the design's connectivity K=3 is unsatisfiable here), CONFIRM ρ shrinks ~5× (sign-only, winner's-curse), and pooled IB ρ is itself negative. No cluster survives.

### Only reproducing edge is UNSIGNED P-01 geometry

Traps revert more than matched random-timing entries (T4: PVA +0.48/+0.30, PRIOR +0.48/+0.27 IB-widths, both bands, CI excludes 0) and more than ordinary non-trap touches (T3: PVA/PRIOR ≈+0.97). **≈ +30–56 bps** at the 116.5 bps median IB width. But it is **not load-dependent** (T1/T2 wash) → failed-break price geometry, the P-01 base SPDR-007 already dispositioned NOT_WORTH. IB availability does not even reproduce (CONFIRM pooled negative; DESIGN CI is a day-weighting artifact). Measured flow adds nothing over price shape.

## 5. Integrity (HARD checks)

- **Causal ≤ t−1:** verified on all 16,669 events (entry = reclaim bar +1min; outcome strictly after; trap load from poke bars ≤ reclaim; PVA/PRIOR levels from the prior closed session). PASS.
- **Leak tripwire:** `reversal_path_swap` bite `corr(swapped, donor MFE)` = 0.53–0.92 (>0.5, real teeth); status **NO_MATERIAL_EDGE** — correct, no material signed edge exists to leak-test (SPDR-007 D-2 precedent). Adjudicates the signed reads (T1 ρ / T2 tier collapse under swap); T4 mean not swap-adjudicated (B-6 mean-vacuity). PASS (valid, no leak).
- **Fences / no-per-level-Δ / no-local-accounting / frozen-pin / derangement zero-fixed-point:** all PASS. Emission VALID — the null is genuine, not a defect.
- Non-invalidating notes: entry-bar-inclusion (0.07% of window, immaterial); T4 CI omits control-side resampling (T4 is P-01/disclosure). Both flagged in `analysis.md` §1/§5.

## 6. Disposition (operator, signed)

**`NOT_WORTH`** for the S3 signed warrant. Powered null on all three boundaries; K=3 within the two-sided null budget (no cluster); the only reproducing edge is unsigned P-01 geometry, not the family warrant. The unsigned availability bounce (~30–55 bps MFE on PVA/PRIOR) is recorded as **market-science characterisation, not a tradability claim**. Would flip only on a connected, derangement-adjusted cluster whose positive tail materially exceeds its mirror and whose CONFIRM ρ reproduces in magnitude — none present.

**No family status change** (REGISTERED). Keep/close of the signed thread is a checkpoint-014 retrospective act.

## 7. Amendments & QA

- **Amendments 1–8:** running count **0 LOOSER / 5 TIGHTER / 3 NEUTRAL** (design §10). 1–5 pre-execution (QA-1: signed-flow load fix, frozen-reuse guard, concrete golden trace, money-floor value, clarity); 6 golden-trace residual pin (build-time); 7 full adjudication machinery (per operator, post QA-3); 8 tripwire donor-pool/vacuity fix (per operator).
- **QA:** run 1 design REVISE→resolved, run 2 design APPROVE, run 3 code REVISE (missing adjudication machinery) → operator directed full machinery → implemented + re-run.

## 8. Follow-ups (as separate future work — none revive the signed warrant)

- Median/trimmed T4 re-read to tighten the unsigned P-01 characterisation (tail-fragile means).
- The signed value block (S9 absorption marginal value, S14 CVD divergence) is checkpoint-015 Phase 6 — a distinct claim from S3 trap load; this NOT_WORTH does not pre-judge it.

## 9. Links

`design.md` · `qa-review.md` (runs 1–3) · `analysis.md` (binding read, disposition §6) · `screen.md` (neutral quantification) · `xen.sigbar.trap` · `screen_code/trap_screen.py` · `design_derivations/gt_derive.py` (+ `gt_output.txt`) · `analysis_code/interrogate.py` · `results/{layers,trap_load_cuts,floor_table}.json`, `{trap_DESIGN,trap_CONFIRM,allocation_map}.parquet`.

**Registry:** applicable — evidence row appended to `docs/signal-registry/candidate-families/cf-sigauc-001.md` §10 (NO status transition); `multiplicity-registry.md` disclosure row; **0 counted TEST reads** (`test-read-ledger.md` unchanged).
