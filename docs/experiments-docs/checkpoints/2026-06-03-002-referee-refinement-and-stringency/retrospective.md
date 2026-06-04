# Phase 002 — Referee Refinement & Stringency Characterization — Retrospective

**Phase number:** 002
**Design finalised:** 2026-06-03
**Retrospective written:** 2026-06-04
**Status:** COMPLETED — all seven planned experiments (EXP-005…011) executed, governance-APPROVED. Core success criteria (§9 a–d) met; both optional/context items (EXP-009, EXP-010) also delivered, not deferred.

**Design reference:** [design.md](design.md)
**Predecessor retrospective:** [Phase 001](../2026-06-01-001-thesis-qualification-calibration/retrospective.md)
**Experiments:** EXP-005 (spine), EXP-006, EXP-007, EXP-008, EXP-009, EXP-010, EXP-011 (synthesis) — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

Phase 001 delivered a *calibrated* referee — the per-domain FPR / TPR / economic-MDE map (EXP-003) — but left **one open item**: H-keystone was *bounded, not closed*. The EXP-004 dogfood anchor was a **null** anchor (untuned Donchian/MA carry ≈0 edge), so the gate's rejections were confirmed true negatives, but no realistic candidate carrying a *real* edge near the MDE had ever been tested. Whether the gate was structurally **blind** to weak-but-real edges was undecided.

Phase 002's job was to take that calibrated referee and make it **usable and trustworthy**, without adopting anything:

1. **Close the open keystone** — test whether the gate detects a *realistic* (imperfect) candidate carrying a real edge near its MDE (EXP-005, the spine).
2. **Characterize the one stringency lever** Phase 001 identified — the L5 materiality leg — by sweeping its threshold (EXP-006) and testing a structurally lenient variant (EXP-007).
3. **Sharpen the map** — de-pool MDE per instrument (EXP-008) and broaden the real-strategy effect-size distribution (EXP-009).
4. **Stress-test the inference** — compare split protocols against the mandated single chronological split (EXP-010).
5. **Synthesize** all of it through a predeclared loss into a **recommended** operating point per domain (EXP-011).

The binding constraint, restated from D-posture: **this is a characterization phase, not an optimization phase.** It *recommends*; it does not adopt or freeze any new referee. Adoption is deferred to a dedicated **Phase 003 decision phase** on *fresh* synthetic draws (the meta-Goodhart guardrail). Success was defined (§9) as *stating these characteristics and landing a recommendation* — not the gate passing anything.

---

## 2. Outcomes vs objectives

| EXP | Role | Verdict | One-line outcome |
| --- | --- | --- | --- |
| 005 | **Keystone closure (spine)** | SUPPORTED | Gate detects the realistic near-MDE candidate on every domain — the MDE map is an **honest detection floor**, not structural blindness. |
| 006 | L5 lever curve (exploratory) | MEASUREMENT COMPLETE | Lower L5 τ ⇒ lower MDE at FPR=0; τ=1 reproduces EXP-003 exactly; zero-buffer endpoint = 0.5/2/8 bps. |
| 007 | Lenient-L5 variant | **REFUTED** | Lenient L5 is not a distinct mechanism — it *equals* the EXP-006 τ=0 endpoint and drop-L5, verdict-for-verdict. |
| 008 | Per-instrument de-pooling | SUPPORTED | 3 slower-domain cells have materially **lower** per-instrument MDEs; the pooled map is conservative, not permissive. |
| 009 | Broadened dogfood (exploratory) | MEASUREMENT COMPLETE | 72/72 cells below MDE, medians ≈ −1 bps net — the null/lower anchor holds; simple untuned strategies are net losers. |
| 010 | Split-protocol robustness | **PARTIALLY REFUTED** | Robust on 5m/1h; 4h falsified only — and toward a *lower* MDE under more-OOS protocols (sample-size effect, not logic). |
| 011 | **Loss synthesis & recommendation** | RECOMMENDATION DELIVERED | Primary loss ⇒ τ 0.75/0.25/0.5 on 5m/1h/4h; 1h robust, 5m/4h loss-sensitive; adoption deferred to Phase 003. |

All seven post-experiment governance reviews returned **APPROVE**.

---

## 3. Keystone reading (headline)

**H-blindness is CLOSED for the EXP-005 candidate class. The strict gate is an honest detection floor — it is NOT structurally blind for a realistic imperfect candidate (`p_active = 0.80`, `q_match = 0.75`) carrying a real edge near the MDE on the tested 5m/1h/4h domains.**

Broader non-blindness across *other* candidate structures and noise regimes is **not** claimed here — it would need new candidate-construction tests (reserved for Phase 004; see §10). This is the central result of the phase and the resolution of the single item Phase 001 left open. EXP-005 engineered exactly the anchor Phase 001's retrospective said was missing: a substrate-validated edge planted at a predeclared grid of {0.5, 1.0, 1.5, 2.0}× the gate MDE per domain, carried not by the perfect oracle but by a **realistic imperfect candidate** (`p_active = 0.80`, `q_match = 0.75`, calibrated so the expected all-eligible-row net edge equals the target). The candidate-construction sanity passed tightly (active rate 0.7999, match rate 0.7500), so the keystone-closure verdict is interpretable rather than a tautology.

At each domain's EXP-003 gate MDE, the frozen gate stack detected it with FPR held at 0:

| Domain | Gate FPR (α₀) | TPR @ 1.0× MDE | TPR @ 0.5× MDE | Verdict |
| --- | --- | --- | --- | --- |
| 5m  | 0/4000 | 1.0000 | 0.024 | DETECTED_FLOOR |
| 1h  | 0/4000 | 0.9850 | 0.371 | DETECTED_FLOOR |
| 4h  | 0/4000 | 0.9465 | 0.502 | DETECTED_FLOOR |

All three domains clear the TPR ≥ 0.80 / FPR ≤ α₀ bar at the MDE, and **all 12 per-instrument headline rows** classify `DETECTED_FLOOR` (weakest BTCUSD/4h, TPR 0.828) — so the pooled pass is not masking an instrument-level blindness. The oracle-calibrated MDE is therefore an *honest* detection floor for realistic candidates: a candidate carrying ≥ MDE of real net edge **is** caught.

**The crucial qualifier — it is a floor, not a guarantee below it.** Detection at 0.5× MDE fails on every domain (5m 0.024, 1h 0.371, 4h 0.502). The map honestly reports what the gate can see; it does not promise to see edges below the line. A gate "reject" still means *"no edge, or a net edge below ~1 / 4 / 12 bps per domain"* — but we now know that boundary is real and detectable from above, not an artifact of oracle calibration. The Phase 001 blind-spot magnitude has been **confirmed as a true sensitivity floor, not understated**.

---

## 4. The stringency lever: characterized and shown one-dimensional

Phase 001 identified L5 materiality as the binding, α-invariant determinant of the gate's MDE. Phase 002 mapped that lever end to end and discovered it has **only one degree of freedom**.

**EXP-006 (the lever curve).** Sweeping `L5_τ = ci_lower_bps > τ·materiality` across {0…2.0}× traced a clean monotone frontier at FPR = 0/4000 in every cell (63/63 PASS):

| τ multiplier (α₀=0.05) | 5m MDE | 1h MDE | 4h MDE |
| --- | --- | --- | --- |
| 0.0 (zero-buffer) | 0.5 | 2.0 | 8.0 |
| 1.0 (strict = EXP-003) | 1.0 | 4.0 | 12.0 |
| 2.0 (high) | 2.0 | 8.0 | 16.0 |

The strict `τ=1` rows reproduced EXP-003 **exactly** (0 draw mismatches), anchoring the sweep to the frozen reference. Lowering τ buys MDE reduction without inflating pooled FPR on the scoped null substrate.

**EXP-007 (the lenient mechanism — REFUTED).** The pre-registered erratum (2026-06-03, authored from frozen code and Phase-001 draws only, before any EXP-006/007 result existed) predicted this. Because the frozen strict leg is `ci_lower_bps > materiality_bps` and **L3 already enforces `ci_lower_bps > 0`**, the lenient leg `ci_lower_bps > 0` is exactly the EXP-006 `τ=0` endpoint, and a gate with maximal L5 leniency is algebraically a gate with L5 *removed*. EXP-007 confirmed both equivalences verdict-for-verdict across all 216,000 draws (9/9 rows, 0 mismatches): lenient MDE = 0.5/2/8 = EXP-006 τ=0 = drop-L5. **H-lenient's structural-gain claim is refuted** — there is no separate "mechanism" lever, only the threshold magnitude.

**The cost of leniency — sub-material passes.** The MDE number alone is misleading at low τ. At the lenient/zero-buffer MDE the economically sub-material pass rate is **5m 0.4965, 1h 0.0547, 4h 0.0** — i.e. on 5m, nearly half the passes at the lower MDE are net-positive but economically negligible (below cost + materiality buffer). This is the materiality caveat D-lenientL5 mandated, and it is why a lower MDE here is *not* a free sensitivity gain. EXP-011 reads τ* with its sub-material rate precisely for this reason.

**Net:** the lever is fully characterized, it is one-dimensional (L5 threshold magnitude), and its lenient endpoint is a known, accounted-for point on the EXP-006 frontier — not a new referee.

---

## 5. Map sharpening and robustness

**EXP-008 — per-instrument MDE (H-pool SUPPORTED).** De-pooling the EXP-003 draws by instrument found three cells differing materially (margin = max(0.5 bps, 20% of pooled)) from the pooled domain MDE — and **all three differences are in the lower-MDE direction**:

| Cell | Per-instrument MDE | Pooled MDE | Δ / margin |
| --- | --- | --- | --- |
| EURUSD/1h | 2.0 | 4.0 | −2.0 / 0.8 |
| EURUSD/4h | 8.0 | 12.0 | −4.0 / 2.4 |
| XAUUSD/4h | 8.0 | 12.0 | −4.0 / 2.4 |

All 5m per-instrument MDEs equal the pooled 1.0 bps. The operational reading: the pooled map is **conservative**, under-claiming achievable sensitivity for EURUSD (1h/4h) and XAUUSD (4h) — a refinement opportunity, not a masked blind spot.

**EXP-009 — broadened dogfood (lower anchor held).** Broadening from 2 to 6 untuned simple-strategy families (Donchian, MA, RSI, Bollinger, MACD, ROC) left every one of 72 gate-stack cells **below** its domain MDE, with net-effect medians ≈ −1 bps and the single largest positive point estimate (EURUSD/4h Donchian, +0.045 bps) still far below the 12-bps 4h MDE. The Phase 001/EXP-004 null/lower anchor is not an artifact of two strategy choices: simple untuned standalone strategies are net losers after cost, *not* small positive edges sitting just under the floor. Any future near-MDE *real* candidate must come from tuned / ensemble / incremental-information units, not naive standalone signals.

**EXP-010 — split-protocol robustness (H-split PARTIALLY REFUTED, and instructively).** Robust on 5m and 1h (single = walk-forward = purged CV); falsified only on 4h — where the more-OOS protocols give a one-grid-step *lower* MDE (8 vs 12 bps), with FPR controlled throughout. This is an **OOS-sample-size effect**, not a referee-logic change: the data-poorest domain detects a smaller edge when more rows go to OOS. Notably, this conclusion is the *corrected* one — the original run's 1h/4h walk-forward MDE inflation was an adversarial-review-caught CI artifact (multi-fold bootstrap-mean concatenation, F01); the fixed test-size-weighted pooled-OOS estimator is bit-identical to the frozen referee on a single fold and shows CI widths that shrink with effective N. The robustness story for synthesis: **5m/1h split-robust; 4h split-sensitive in the safe (more-sensitive) direction.**

---

## 6. Synthesis & recommendation (EXP-011)

With every characterization input frozen, EXP-011 applied three fully predeclared loss functions (A/B/C) to the EXP-006 τ-frontier, overlaying EXP-005 (non-blindness), EXP-007 (sub-material), EXP-008 (per-instrument), EXP-009 (real-effect location), and EXP-010 (split) context. The primary-loss **recommendation**:

| Domain | Recommended τ | MDE @ τ* | Sub-material rate | Cross-loss | Driver |
| --- | --- | --- | --- | --- | --- |
| 5m | 0.75 | 0.5 bps | 0.398 | **LOSS_SENSITIVE** | sub_material |
| 1h | 0.25 | 2.0 bps | 0.026 | **ROBUST** | — |
| 4h | 0.5 | 8.0 bps | 0.000 | **LOSS_SENSITIVE** | blind_band |

1h is robust across Loss A/B/C; 5m and 4h are loss-sensitive (5m because nearly 40% of passes at τ* are sub-material; 4h because the choice sits in a blind band where the loss weighting decides). The recorded conditional adoption rule and `adoption_rule.json` flag **only 4h** as requiring stricter Phase 003 split-ratification (under corrected EXP-010), and note Loss C degenerates toward the lenient endpoint on the zero-FPR substrate. **No operating point is adopted in Phase 002** — the recommendation goes to Phase 003 for ratification on fresh draws.

---

## 7. State of the testing framework — is it "concluded"?

The operator's standing question (design §5/§10/§12: signal exploration begins only "after the testing framework is concluded"; chart-type signals are one example family among several the operator will define later). Phase 002's honest answer:

**Plain terms: the strict referee is ready to use right now. Only an *optional* sensitivity upgrade is still pending.** The strict gate stack (the default τ=1.0 setting) is the frozen, validated reference — its logic is correct (EXP-002), it has zero false positives (EXP-003), it is an honest detection floor rather than blind (EXP-005), and it is split-robust (EXP-010). It needs **no further confirmation**; a real candidate run through it today yields a trustworthy verdict (a PASS means high-confidence-real; a REJECT means no edge, or an edge below the per-domain floor of ~1/4/12 bps). The machinery to run a real candidate through it already exists and was exercised by EXP-004 and EXP-009.

**What is *not* finalized is the looser operating point** — the EXP-011 recommendation (τ 0.75/0.25/0.5) that would catch slightly smaller edges. It was *chosen* by reading the same Phase 002 synthetic draws used to characterize it, so before it is trusted it must be re-confirmed ("ratified") on a **fresh, independent synthetic batch** (the meta-Goodhart guardrail: never lock in a setting using the very data used to pick it). That ratification is the only thing standing between "characterized" and "finalized," and it is cheap (re-run the existing harness on a new seed).

Distinguishing the two precisely — the referee is now a fully mapped, trustworthy instrument:

- It is an **honest detection floor**, not structurally blind **for the EXP-005 candidate construction** (EXP-005) — the property that was undecided at the end of Phase 001 (broader candidate/noise regimes remain a Phase 004 question).
- Its **single stringency lever is fully traced** and shown one-dimensional; the "lenient mechanism" collapsed into it (EXP-006/007).
- Its **per-instrument heterogeneity is known** and conservative-leaning (EXP-008).
- It **robustly rejects untuned simple strategies as net losers** — confirmed not a blindness artifact (EXP-009).
- It is **split-robust on 5m/1h**, and 4h's sensitivity moves in the safe direction (EXP-010).
- A **recommended operating point per domain plus a conditional adoption rule** exists (EXP-011).

What remains, deliberately deferred under D-posture and the meta-Goodhart guardrail, is the **freeze**: ratifying the looser operating point on *fresh* draws so Goodhart bites where it can be controlled, not in the phase that characterized the options. That is the Phase 003 decision step.

So: the strict referee is **concluded and usable today**; the looser referee is **one fresh-draw ratification away** from the same status. The operator has chosen (see §11) to run that ratification, plus build the incremental-information / portfolio-fitness unit, in Phase 003 — completing the qualification suite before signal exploration begins.

---

## 8. Lessons learned

1. **Closing a blindness question requires planting a *real* edge carried by an *imperfect* signal.** Phase 001's null anchor failed because it leaned on real strategies that turned out to carry no edge. EXP-005's calibrated imperfect-candidate construction (real planted edge × noisy position series) was the right shape and converted "undecided" into a clean "honest floor." This construction pattern is reusable for any future detection-floor test.
2. **When L3 already enforces net-positivity, L5 has exactly one knob: its materiality buffer.** There is no separate lenient *mechanism* — the lenient leg is the buffer→0 limit. Reading the frozen code carefully (the pre-registered erratum) pre-empted a wasted mechanism claim *before* EXP-006/007 ran. Lesson: derive structural equivalences from frozen code, not from measurements, and predeclare the expected refutation.
3. **An MDE number is incomplete without its sub-material pass rate.** Lower τ buys a smaller MDE partly with economically negligible passes (5m ≈ 0.50 at zero-buffer). Sensitivity claims must be read jointly with materiality, which is exactly what drove 5m's loss-sensitivity in EXP-011.
4. **Pooling here is conservative, not permissive.** Every material per-instrument deviation (EXP-008) was a *lower* MDE — the pooled map under-claims sensitivity for some slower-domain cells. Pooling caveats are not automatically "the map hides a blind spot"; check the direction.
5. **Simple untuned strategies are robust net losers.** Broadening to six families did not surface a near-MDE candidate. The framework will not be exercised against a real near-MDE edge by naive standalone signals — that must come from tuned/ensemble/incremental-information units (the Phase 003 seed).
6. **Multi-fold protocol comparisons need a CI-scaling sanity check.** EXP-010's original artifact (per-fold CI on a pooled-OOS estimate) inverted the conclusion until adversarial review F01 caught it. The corrected estimator's CI shrinks with effective N. This is now a **standing audit requirement**: any pooled-OOS bootstrap must show CI width decreasing with pooled OOS size. The governance/adversarial layer worked — it caught a wrong-direction result before it reached synthesis.
7. **`block_length = 1` everywhere, again.** As in Phase 001, the stationary bootstrap reduced to i.i.d. resampling across every Phase 002 cell — negligible per-bar autocorrelation in the return/effect series. EXP-010 confirms this i.i.d. reduction is not hiding split-exposable dependence (5m/1h robust). A durable empirical fact for future inference-unit choices.
8. **Process discipline held end to end.** Operator confirmation of the three ⚠ items before EXP-005; the dated erratum authored from Phase-001-only artifacts; deps hard-gated; no referee adopted or frozen in a characterization phase. The meta-Goodhart guardrail is intact going into Phase 003's fresh-draw adoption.

---

## 9. Phase verdict vs §9 criteria

**SUCCEEDED — all core deliverables met, both optional items also delivered.**

- (a) **EXP-005 returns an interpretable per-domain blindness verdict with usable precision, pooled and per-instrument** — ✓ DETECTED_FLOOR on all three domains and all 12 per-instrument headline rows; honest floor confirmed.
- (b) **L5 stringency lever characterized (EXP-006 curve + EXP-007 lenient operating characteristics incl. sub-material pass rate)** — ✓ frontier traced 63/63 PASS; lenient shown ≡ τ=0 with sub-material accounting.
- (c) **Per-instrument MDE map produced (EXP-008)** — ✓ 36/36 PASS, three material lower-MDE cells identified.
- (d) **EXP-011 yields a predeclared-loss-minimising recommended operating point per domain + recorded conditional adoption rule** — ✓ τ 0.75/0.25/0.5 with robustness flags and adoption rule.
- **Optional/context (EXP-009, EXP-010)** — ✓ both delivered, not deferred; they strengthened the lower anchor and the robustness picture respectively.

Neither failure condition triggered: substrate/harness was reused unchanged (no P0 re-validation trigger), and the keystone-closure machinery worked on every domain. The two non-SUPPORTED headline verdicts (EXP-007 REFUTED, EXP-010 PARTIALLY REFUTED) are **clean predeclared findings**, not phase failures — EXP-007 confirmed a predicted structural equivalence, and EXP-010's 4h falsification points toward greater sensitivity, not a referee defect.

---

## 10. Proposed next research direction

*(These were the options proposed at retrospective time. The operator has since chosen the direction — see §11, which governs. The Phase 003 `design.md` formalises it.)*

**Recommended Phase 003 spine — the decision phase (D-posture / §10 / §11):**

- **Fresh-draw ratification of the EXP-011 recommendation.** Re-measure the recommended per-domain operating points (τ 0.75/0.25/0.5) on *fresh* synthetic draws, never the Phase 001/002 paired draws, and execute the conditional adoption rule. This is where the meta-Goodhart freeze happens cleanly. 4h carries the explicit split-sensitivity flag from corrected EXP-010 and should get the stricter ratification path.
- **Incremental-information unit (Phase 002 §11 seed).** Redefine the unit of qualification from a standalone directional signal to the edge a candidate adds *beyond* a reference signal (generalising L3's naive control into the unit). Open design questions already recorded: known-truth substrate for incremental edges (analogue of EXP-001), how the gate legs map onto a conditional/marginal claim, cross-unit dependence when reference and candidate share structure.

**Now-unblocked track (operator-gated):**

- **Chart-type candidate signals** (Line Break / Renko / Heiken Ashi). Deferred by operator decision "until the testing framework is concluded." Phase 002 concludes the framework's *characterization*; the validated VAL-001 data layer and the now-honest referee are both ready. Whether this becomes a Phase 003 parallel track or follows ratification is an **operator decision** — flagged here because EXP-009 establishes that the referee's first *real* near-MDE candidate is unlikely to come from naive standalone signals, so a genuine signal-exploration track is the natural source of one.

**Programme-level deferrals still standing:** tunable context-dependent loss beyond the single predeclared form; non-stationary / drifting planted edges; full cross-market k-of-N replication beyond L4; programme-level multiplicity / file-drawer registry.

---

## 11. Operator decision (2026-06-04) — Phase 003 direction & framework conclusion

**Decision recorded.** The operator confirms:

1. **The strict referee is validated and adopted as-is** — no further work needed on it.
2. **The looser referee will not be left open-ended.** Phase 003 **proceeds with fresh-draw ratification** of the EXP-011-recommended operating point (τ 0.75/0.25/0.5 on 5m/1h/4h), with the 4h split-sensitivity flag (corrected EXP-010) getting the stricter ratification path. Outcome: an *adopted* loose referee alongside the strict one, or a recorded decision not to adopt if ratification fails OOS.
3. **The incremental-information / portfolio-fitness unit is built and validated in Phase 003** (promoted from the Phase 002 §11 design-only seed to an executed track). The operator's rationale: signal exploration is most effective when a candidate can be (a) screened by **both referees** (strict + ratified-loose) for standalone edge, and (b) evaluated for **portfolio fitness** — the incremental edge it adds beyond already-validated strategies. The **"two referees + fitness check" suite** is the target instrument.
4. **Phase 003 concludes the framework programme on its FULL_FRAMEWORK_CONCLUDED outcome** (Phase 003 design §9 — which requires a *validated* fitness unit, not merely an attempted one). On that outcome the suite is complete and frozen and **Phase 004 becomes the first real signal-exploration phase**, in which the operator defines and brings the candidate model families to test (chart-type signals being one example among several, to be specified then) under a mandatory programme-level multiplicity registry. A partial Phase 003 (e.g. the fitness unit proves unbuildable) ships the two referees only and does not, by itself, unlock Phase 004.

**Process note (meta-Goodhart preserved):** the ratification and the incremental-unit calibration are each measured **once on fresh / purpose-built substrates** and frozen before any real candidate is judged by them in Phase 004. Phase 003 *builds and freezes* the suite; Phase 004 *uses* it. The strict gate remains the frozen reference throughout.

The Phase 003 design is recorded at [`../2026-06-04-003-ratification-and-incremental-unit/design.md`](../2026-06-04-003-ratification-and-incremental-unit/design.md).
