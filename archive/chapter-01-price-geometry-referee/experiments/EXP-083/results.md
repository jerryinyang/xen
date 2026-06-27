# Results: EXP-083 — TRAIN-Only Candidate Screen Behind the Separability Gate (CF-CAPGEO-001 Phase 018 / HYP-004a)

**Verdict:** `SCREEN_DELIVERED` — ≥1 `{candidate × stratum}` survives both TRAIN gates.
**Binding run:** `valid_set_sha256 = fa4035f3…`, `n_valid = 26`, 2070 `{substrate × cell × candidate}` rows, `determinism_ok = true`, `holdout_untouched = true`, `counted_test_reads = 0`. (Supersedes the first-pass `0796530c…`/28-survivor run; see `audit.md` Re-Audit.)

**This is a TRAIN-only eligibility result, not an edge or tradability claim.** No TEST stratum was sliced, no holdout touched, no counted read spent, and the cost-calibrated frozen referee suite was **not** invoked (gross screen). The binding adjudication and the lifetime counted read are the deferred, reserved-conditional **EXP-084** — opened only on operator ratification.

---

## Headline (read per-stratum, not flat)

`SCREEN_DELIVERED` is honestly true but **must not be read as "26 candidates work."** The 26 survivors decompose into two qualitatively different groups, and **only 4 cleared the binding shape-guard (S2):**

| Group | Count | Cells | n | S2 (binding shape-guard) | Reading |
|---|---|---|---|---|---|
| **S2-PASS (fully gated)** | **4** | `SUB-HARAMI-V2A × AUDUSD × 1h` (one cell) | 988 | **Evaluated, PASS** | The only TRAIN-eligible candidates adjudicated by the complete gate. |
| **S2-DEFERRED (S2 unadjudicated)** | **22** | `SUB-AVWAP × {NZDUSD, USDCAD, USTEC} × 4h` (three cells) | 44–78 (<120 floor) | **Not evaluated** | Eligible on G-018a ∧ S1 only; carried *flagged*, neither survivors-by-default nor failures. |

All 26 survivors trace to just **4 underlying instrument×domain×substrate cells**. Breadth is **narrow**: one well-powered harami-1h cell with full adjudication, plus three low-n AVWAP-4h cells whose binding tail-guard was deferred. Per LESSON-001 no cross-stratum pooling is treated as binding; "26" is a candidate-count over strata, not population breadth.

**98.2% of the surface (2033/2070) died at the cheap G-018a gross screen** before separability was reached. The expensive separability machinery (S1∧S2) was the deciding leg for only **8 strata** (7 fail@S2, 1 fail@S1). The screen behaved exactly as designed ("fail cheaply first") — the gross matched-random-excess screen did almost all the filtering.

---

## Mechanism — favourable-capture attribution, NOT the EXP-082 trap

The pre-registered crux (EXP-082) was that the derived adverse leg would reproduce the CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" geometry — edge manufactured by stop-truncation rather than a real entry signal. **The survivors refute that as their mechanism:**

- `x_fav > 0` for **all 26** survivors (min 0.81, mean **1.33 ATR**) — the favourable-target + time-cap leg independently beats the per-cell matched-random control (S1 passes on genuine favourable attribution).
- `x_tail ≤ 0` for **all 26** (range −0.199 … 0.0) — the adverse stop **subtracts** expectancy, never manufactures it. **Zero** survivors are tail-truncation artifacts (`x_fav ≤ 0`) and **zero** are tail-dominated (`|x_tail| > |x_fav|`).

So the surviving edge is attributable to the **entry** (harami-1h and AVWAP-4h favourable capture beating random), with the exit's adverse leg a small drag. The driver is real capture, not a capture-bound/tail artifact.

### Derived (D1/D2/D3) vs conventional benchmarks — the family thesis is *not* supported on TRAIN

The CF-CAPGEO-001 thesis is specifically whether **data-derived** exits beat **conventional** ones. The screen says they do not distinctively, and on the only adjudicated cell they do not survive at all:

- **The 4 binding (S2-PASS) survivors are all conventional arms:** `AVWAP-FH` (fixed-horizon, `/EXIT-PARTIAL`) and `RR-1.5 / RR-2 / RR-3` (fixed RR triple-barrier, `/EXIT-RR`). **None** of the data-derived `D1-MEDIAN-CAPTURE / D2-TAIL-ROBUST / D3-CAPTURE-EFFICIENT` survive on the well-powered harami-1h cell.
- **The derived D1/D2/D3 survive only in the S2-DEFERRED AVWAP-4h cells** (NZDUSD-4h, USDCAD-4h; n≈77), where the binding tail-guard was never evaluated — and they appear there *alongside* the conventional arms, not in preference to them.
- On the one cell where S2 actually bound, conventional fixed-horizon and RR exits cleared the full gate and the bespoke derived exits did not. **The derived-exit hypothesis earns no distinctive TRAIN support; if anything the conventional arms are the stronger eligible set.**

---

## Gate-shape caveat (carry to EXP-084 / cost layer)

The 3 RR S2-passers clear S2 by **mechanical stop truncation, not a benign tail**: their post-exit `tailmass = 0` and `q05_post = q05_control = −MAE_q90 ≈ −7.28 ATR` exactly — the fixed adverse stop clips both candidate and control left tails to a point mass at the stop level, so the tailmass leg sees "no continuous tail" and the relative-q05 leg ties at the stop. **S2 is a *shape* guard (separated continuous catastrophe mode), not a *magnitude* guard.** It correctly certifies "no separated catastrophe mode" but is **silent on the −7.28-ATR-per-stop loss size.** That magnitude/cost question is exactly what this GROSS screen defers to EXP-084's cost-calibrated frozen referee suite — it is not a gap in the screen, but it means the RR survivors' eligibility is "shape-clean, magnitude-unpriced." `AVWAP-FH` is the one binding survivor that passes S2 on a genuine continuous-tail measurement (`tailmass 0.022`, `q05_post −6.30 > q05_control −6.76`), since as a no-stop exit it has no truncation point mass.

---

## Pre-registered interpretation outcome

Against the analysis-plan Interpretation Guide:

- **`SCREEN_DELIVERED` + non-empty valid set:** met. Survival is **narrow** (4 cells), and the binding (S2-adjudicated) evidence is **a single well-powered cell** (AUDUSD-1h harami) where only **conventional** exits survive.
- **Where candidates die:** overwhelmingly at G-018a (no gross edge over matched-random) — the EXP-081 "capture availability ≈ random" finding carried into realized exits for 98.2% of the surface. The binding S2 trap-guard bound for only 7 strata; S1 for 1.
- **Derived vs benchmark:** the data-derived exits do **not** beat conventional exits; they are absent from the only fully-gated cell and merely co-survive (deferred) elsewhere. The family's central "data-derived is better" claim is **unsupported on TRAIN**.

---

## Recommendation on EXP-084 (the deferred counted read) — requires operator ratification

This is advisory; spending a lifetime TEST read is an operator decision.

- **The case for opening EXP-084 is weak-to-marginal.** The binding (S2-passed) eligible set is conventional `AVWAP-FH + RR-1.5/2/3` on a **single** instrument×domain×substrate cell (AUDUSD-1h harami). The derived exits — the actual family hypothesis — earned **no** binding support. A counted read spent here would test conventional exits on one cell, not the data-derived thesis.
- **If the operator ratifies EXP-084 at all,** the defensible subset is the **4 S2-passed conventional arms on AUDUSD-1h** under the frozen Holm-over-grid rule — explicitly framed as a test of *conventional capture-geometry exits on one well-powered harami cell*, **not** a vindication of the derived exits. The 22 S2-deferred AVWAP-4h candidates should **not** anchor a counted read (binding shape-guard never evaluated; n<120).
- **A clean alternative is to close HYP-004 at G-018 on the TRAIN screen** with the reading "the data-derived exits do not distinctively beat conventional exits, and survival is narrow and largely S2-unadjudicated," spending **0 lifetime reads** — consistent with the falsification-first / file-drawer-control posture. The reserved-conditional EXP-084 exists precisely so this can be declined cheaply.
- **Either way, the GROSS→cost gap is decisive for the RR arms:** their S2 pass is magnitude-unpriced (−7.28 ATR/stop), so any EXP-084 must let the cost-calibrated referee suite bind before any tradability claim.

*(Per pipeline rules, follow-up work — a per-event cost/slippage+financing layer, or a faithful per-event VP profile — is a new scope at its own D0, not an extension here.)*

---

## ASS discovery overlay (NON-BINDING — G-017 `DISCOVERY_ONLY`)

A post-hoc disclosure overlay (`results/ass_overlay.*`, `plots/06_ass_overlay.png`) scores **every** member
stratum's post-exit distribution with the real `ASS` transform — adaptive-KDE + empirical-Bayes shrinkage
(pool = cross-cell within `{substrate, candidate}`, `k = median-n`, the EXP-076 deployed convention) + the
D2.5 shape diagnostic. 2068 strata, reconciled to the screen (n exact, raw mean within 1e-9). **No screen
decision reads `ASS`; the frozen artifacts (`valid_candidate_set.json` sha `fa4035f3…`, `screen_results.*`,
`run_metadata.json`) are untouched.** `ASS` shrinkage pools across strata — the per-stratum-discipline
tension (LESSON-001) that demoted it — so this is a discovery read, never a binding verdict.

- **`ASS` agrees with the binding screen on direction where it matters.** All **26/26 survivors stay positive**
  under `ASS`-shrunk expectancy (min 0.164 ATR); **zero** survivor sign-flips. The **136 `ASS`-vs-screen sign
  disagreements are entirely within the already-failed population**, all on near-zero raw estimates (median
  |raw| = 0.038 ATR), concentrated in the uniformly-weak `/EXIT-TRAIL` (54). `ASS` overturns no strong call.
- **`ASS`'s added value: it independently discounts the inflated small-n deferred survivors.** The 22
  S2-deferred survivors (n=44–78) have a median shrink weight of **0.19** — they regress ~81% toward the pool,
  dropping expectancy by a median **−0.97 ATR (up to −1.39)**; the 4 binding S2-pass survivors (n=988,
  weight ~0.46) shrink to −0.51 and stay clearly positive (~0.34–0.40). This **reinforces the masking
  finding**: the deferred AVWAP-4h survivors are magnitude-inflated; the trustworthy evidence is the one
  well-powered AUDUSD-1h cell.
- **`ASS` flags 84% (1740/2068) of strata as bimodal/asymmetric** — the pervasive median-positive/mean-killed
  shape. **3/4 binding S2-passers are `ASS`-shape-flagged** (the RR arms, dip_p≈0); `AVWAP-FH` (no-stop) is
  not. This is a **coherent cross-lens, not a contradiction**: the stop-truncation-to-point-mass that lets the
  RR arms clear S2's *catastrophe-residual* leg (tailmass=0) is exactly the bimodality `ASS`'s dip-test
  detects — S2 says "no continuous catastrophe residual," `ASS` says "but the truncation is bimodal," both
  true. Per EXP-078 this is `ASS` catching *gross* bimodality (which it can), not a re-test of its subtle
  `B_zero`/`B_pos` blind spot.

**Bottom line (non-binding):** the demoted qualifier corroborates the screen's directional calls, adds a
useful small-n discount that strengthens the "narrow, low-n-inflated breadth" reading, and changes **no**
verdict, eligibility, or the G-018 decision.

---

## Caveats carried from the audit (non-binding)

- **W2 — VP-POC selection-on-geometry:** `/EXIT-VP` is scored on a geometry-selected subsample (events whose cell-level TickVolume POC sits favourable-side; AUDUSD-1h VP-POC `n_resolved 590` vs 988). It survives only at USDCAD-4h (deferred, 1 candidate) and does **not** touch the 4 binding survivors. The cell-level TickVolume POC is a disclosed screen-stage proxy; a faithful per-event reference-move profile is EXP-084/parity work.
- **Harami slate consolidation (for Stage-7 registry):** the two registered harami substrates (`PARTIAL-V2A`, `V2A-ADVNONE`) were screened as **one** stratum here (they are entry-identical and the screen applies the full candidate surface to both, so they were fully redundant). The multiplicity-registry Phase 018 harami count must be consolidated accordingly; refuted/blocked items remain in the ledger.
- **New binding artifact:** `valid_candidate_set.json` sha256 = **`fa4035f3…`** (with the Holm-over-grid rule + EXP-080/081/082 provenance) is the frozen EXP-084 hand-off; EXP-084 imports it verbatim and asserts this hash before any TEST row.
- **Gross screen:** all expectancy/median/tail metrics are gross matched-control excess; cost-calibrated floors bind only at EXP-084.

## Disposition

TRAIN-only eligibility delivered. The data-derived exit hypothesis is **unsupported on TRAIN** (no derived arm in the binding S2-passed set; survival narrow and mostly S2-deferred). Route to the operator for the G-018 decision: **decline EXP-084 and close HYP-004 at G-018 (0 reads)**, or ratify a **narrowly-scoped EXP-084 on the 4 conventional AUDUSD-1h survivors** under the pinned Holm rule and cost-calibrated referee suite. No edge/tradability claim is made here.
