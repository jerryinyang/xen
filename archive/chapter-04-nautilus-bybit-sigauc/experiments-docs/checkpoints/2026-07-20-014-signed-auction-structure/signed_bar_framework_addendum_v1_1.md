# Addendum v1.1 — Empirical State Update to the Signed-Bar Strategy Framework
## Verdicts from Checkpoint 014 (Phases 0–5), Protocol Hardening, and the Revised Experimental Path

*Status: this addendum converts the framework's grades from hypothesis to empirical state for the first time, per the versioning clause (Part 6.10b of the base document). Evidence: Checkpoint 014 (INFR-017, INFR-018, SPDR-007, SPDR-008), executed 2026-07-20 → 2026-07-21 on Bybit USDT linear perpetuals, 1-minute bars with exact taker split. Zero programme holdout consumed. Every verdict below is scoped to the tested object — **the anchored daily session (US open, 15-min IB, ~24h single-session hold)** — unless stated otherwise. The base document is unchanged; where this addendum conflicts with it, the addendum governs.*

---

# Part 1 — Grade Register: Verdicts

## 1.1 Confirmed

**A8 — Data provenance: CONFIRMED.** Taker buy/sell columns reconcile bit-exactly to raw trades (20/20 symbol-days, worst relative deviation 0.0); the archive's side field is the aggressor. The tier's founding premise — per-bar delta is a measurement, not an estimate — is verified end-to-end. The family was not parked on A8.

**S2 — The excursion object: CONFIRMED as measurement, with a mandatory census clause.** The Protection quantile reproduces pooled at the ~65–70% class (calibration error +0.028, inside the ±0.05 band) at the correct (1−p) percentile — the quantile machinery and the quantile-direction rule both work as specified. **New mandatory clause:** pooled calibration must always co-report the per-symbol census; the pooled pass concealed 51 reproduces / 25 drifted / 21 broken of 97 (SOL p70 broken at +0.105). A pooled pass is never a per-symbol pass. What S2 no longer claims: that reaching its levels constitutes conditional skill (see S1's verdict).

**S3 base (unsigned failed-break geometry): CONFIRMED as characterization, not as strategy.** Failed breaks reverse more than matched random-timing entries and more than ordinary non-trap touches on prior-VA and prior-extreme boundaries (~30–55 bps MFE-scale; ~0.3–1.0 IB-widths). The trapped-inventory mechanism leaves a real, reproducible footprint in the data. Caveats that bind: the estimate is a mean of favorable-excursion tails and therefore an upper-ish bound pending the trimmed/median re-read (§3.4); it does not clear cost as a session trade; it belongs to the same reproduction-without-skill class as the spine.

**A6 — The discriminator: CONFIRMED as constructible.** Acceptance-type and trap-type outcomes are separable in real time under the frozen rule (D4-t50-w30, δ=0, price-only — the flow-augmented variants lost the race), and the separation collapses under planted future-leaks (positive-control bite confirmed). The framework-falsifier "the transition branch is untradeable as specified" did **not** fire.

**Appendix B — The experimental path itself: CONFIRMED.** The budget-shape claim ("an absent edge is discovered in weeks, not quarters") resolved in two days, four TRAIN-only items, zero holdout reads, at 296-name production scale, with freeze discipline intact. The meta-hypothesis about how to run this work passed harder than any market hypothesis.

## 1.2 Demoted

**S1 — Anchored session breakout, as a tradable edge on the tested object: DEMOTED to `==`.** The quantile reproduces, but accepted breaks add ≈0 over matched cross-session unconditional entries (0.333 vs 0.343 win rate) and sit below cost-adjusted breakeven on all five majors (w − p₀ᶜ ≈ −0.05 to −0.14). Reproduction without control separation is the "price has quantiles" null. **S1 is retained in a reduced role: an *operational anchor* — a frozen clock for measurement and session construction — not an *edge-bearing gate*.** This distinction is now permanent vocabulary (§2.7). Scope of the demotion: the daily US-open session object only; funding-cadence anchors, micro (1–10 bar) holds, structural multi-session holds, and higher-TF bars are untested — but the prior on them is lowered, not neutral.

**A7 — Anchor selection: reframed.** The pooled race froze A-USOPEN×15m legitimately as a parameter, but the selection contrast was small (E ≈ +0.10, CI through zero, near MDE). The framework previously conflated "a stable anchor exists" with "an anchor with proven breakout expectancy exists." Only the former was demonstrated. Phase-1-style gates in any future work must state which of the two they certify.

**§2.5 — Spread regime layer: UNAVAILABLE, demoted until rebuilt.** The stored spread column is a mean-print differential, negative in ~32–40% of BTC/ETH TRAIN minutes — not a spread, not a cost input. The entire §2.5 layer (stress demotion, vacuum corroboration, regime conditioning) is suspended. Reinstatement requires a per-symbol, tick-floored quote/spread reconstruction as a hard Phase-0-class exit criterion (§3.9). Until then, every net read across breadth carries an unmeasured spread term — small on majors, potentially dominant exactly where a breadth map would claim soil.

## 1.3 Deleted

**S3 Δ+ (trap-load monotonicity): DELETED under the mechanism doctrine.** The claim — reversal is monotone in measured trap load — is a powered null on three independently tested boundaries (IB ρ ≈ −0.015; prior-VA ρ ≈ +0.023 flipping negative on CONFIRM; prior extreme ρ ≈ −0.033; all inside MDE at n in the tens of thousands; HIGH−LOW tiers CI through zero). The cluster scan's 7 positive cells against 6.0 expected, with **10 anti-monotone mirror cells**, is dispositive multiplicity noise. Per the binary-mechanism rule: the statement is deleted, not re-parameterized. Any future signed-trap proposal must carry a **written mechanism that is not "more measured aggression ⇒ more forced unwind"** — new load formulas, residuals, or holds under the same mechanism are re-tuning a dead mechanism and are barred.

## 1.4 Cascaded consequences

- **M1 (Anchored Breakout & Block Retest): SUSPENDED on this object.** Its direction layer (S1 as edge-bearing gate) is dead here; its three claims are unfalsifiable as composed. The S7 block remains a valid location construct for other compositions.
- **M4 (Trap and Rotate): claim 2 (load monotonicity) deleted with S3 Δ+; claim 1 survives only as the non-promotable unsigned characterization.** The model as a strategy is closed on this object.
- **M2's router claims: untested and unaffected as measurement**, but any "router-aligned outperformance" test must now use the router against outcomes, not against the dead S1 gate.
- **Phase 6's gating premise is broken and redesigned (§3.1):** signals specified "under an open gate" cannot lean on a gate that showed no conditional skill. S9/S14 screens run **gate-free**, qualified by location context (balance edges, prior-value edges, defended bands) — which is also where the mechanisms were always predicted to matter most.
- **Untouched — neither confirmed nor refuted:** S4, S5, S6, S8, S9, S10, S11, S13, S14, S15, S16, M3, M5, and the micro/structural horizon menu. S3's null is *adjacent* evidence against S9/S14 (it lowers priors), not a test of them: trap load was the most price-adjacent signed claim in the catalog — a Δ tag on geometry price already sees — while S9 (effort without result at a shelf) and S14 (CVD decoupling from price) are the mechanisms definitionally invisible to price alone. Framework-falsifiers #3 and #4 remain open, and family closure before they are exercised would violate the framework's own closure logic.

---

# Part 2 — Protocol Hardening (amendments to Part 6 of the base document)

**2.1 Master gate rewrite (supersedes falsifier #1's wording).** The spine gate is a conjunction, each leg co-equal: (i) the Protection quantile calibrates at the (1−p) percentile; **(ii) conditioned entries beat a matched unconditional control; (iii) the resulting edge clears the measured cost floor.** Reproduction alone can pass while the framework is worthless — price paths have quantiles. A gate that can pass on calibration alone is defective by construction.

**2.2 Mirror-tail multiplicity rule (mandatory for all cell-grid promotes).** Count both tails, always. A promote requires the positive tail to **materially exceed its anti-monotone mirror**, not merely exceed null expectation. A positive count near expectation with a heavier negative mirror is dispositive noise; a single-tail "≥k winners" rule would have mis-promoted in SPDR-008 and is retired.

**2.3 Per-symbol census clause.** Every pooled calibration or pooled effect co-reports its per-symbol census (reproduces / drifted / broken). Claims inherit the census, not the pool.

**2.4 Control-family specification.** Each event class declares its preferred control family in the design, so replications are comparable: matched random-timing for availability; matched unconditional (cross-session where within-session phase-matching is infeasible — and say so) for conditioning skill; derangement nulls for sign/side reads. **Sparse-session events break day-block derangement** (SPDR-007: 60 of 7,070 events derangeable; the rest day-singletons or one-side-dominant) — for session-scale events, blocks must be wider than the calendar day or a different control family chosen. Unpowered ≠ negative, and must be reported as unpowered.

**2.5 Finite-value guards.** Every correlation/regression path guards `is_finite` explicitly; null-dropping that passes float NaN silently is a known live bug class (a 27%-polluted Spearman flipped sign from +0.130 to −0.040 in SPDR-007).

**2.6 Robust statistics for excursion claims.** Means of favorable-excursion tails are fragile; every excursion-based effect co-reports median and trimmed variants. A mean-only excursion claim is an upper bound, labeled as such.

**2.7 Anchor vocabulary.** "Operational anchor" (a frozen clock certified stable for measurement) and "edge-bearing anchor" (an anchor with demonstrated conditional expectancy) are distinct certifications; every anchor freeze states which it is.

**2.8 Leak-tripwire interpretation rule.** A NO_MATERIAL_EDGE tripwire outcome on a null result means the gate had teeth and nothing to bite — it is **not** evidence that a live edge is leak-free, and may not be cited as such.

**2.9 Breadth honesty + net-claim prerequisite.** "Full cross-section" means *listings with readable history under the trailing cap* (296 of 894 here) and every breadth map carries the survivorship note. **No net (post-cost) breadth claim is admissible until the per-symbol tick-floored spread reconstruction exists** — the unmeasured spread term concentrates precisely where breadth maps place their soil.

**2.10 Horizon-menu closure clause.** A whole-family close requires either at least one screen per untested horizon class (micro; structural) or an explicit scoping statement that the close applies to the tested horizon only. Phases 0–5 exercised the session horizon exclusively; the current kills are so scoped.

---

# Part 3 — The Revised Experimental Path (supersedes Appendix B's Phase 6 onward)

## 3.0 State of the board

| Item | Status | Pins |
|---|---|---|
| Phases 0–3 (instruments) | CLOSED — frozen, audited | baselines 1b7244c8…, registry 5c386984… |
| Phase 4 (spine) | CLOSED — NOT_WORTH on the session object | SPDR-007 |
| Phase 5 (breadth + S3 Δ+) | CLOSED — powered null on the signed arm | SPDR-008 |
| Holdout / TEST budget | Untouched | — |

## 3.1 Phase 6′ — the absorption screen (next spend; cheap, TRAIN-only)

**Question:** framework-falsifier #3 — does signed absorption (S9) add marginal value over the unsigned Climax-hold class on the same events?

Design constraints, all inherited from Checkpoint 014's lessons:
- **Gate-free qualification.** Levels qualified by location context only — balance edges, prior-value edges, defended bands (S13 detection), completed-profile HVN edges — never by the demoted S1 session gate. This is simultaneously the honest design and the mechanism's predicted habitat (M3 context).
- **Marginal framing (Part 6.5).** The read is signed-S9 minus unsigned-class on identical events; "the signed version fires" is not a result.
- **Controls per §2.4**: matched bare-level touches; unsigned-class events without the Δ signature; derangement blocks wider than the day or an alternative null, pre-declared.
- **§2.2 mirror-tail promote, §2.3 census, §2.5 finite guards, §2.6 robust stats** — all binding.
- Budget class: same as SPDR-008 (one screen, TRAIN-only, zero holdout).

## 3.2 Phase 6′b — S14 divergence (rides along if the harness allows)

Framework-falsifier #4. **Opening condition (mechanism-differentiation memo, one paragraph, written before the run):** state why integration across bars, location anchoring at held levels, and multi-bar structure create information that bar-level trap load did not — S14 shares the Δ measurement with the deleted S3 arm, and running it without this memo is S3-null laundering through a new name. The memo exists so that if S14 also nulls, the *mechanism family* is cleanly dead rather than endlessly reformulable.

## 3.3 Family closure rule

- **Third independent powered null** (S9 marginal ≈ 0 under §3.1's design) ⇒ close the family on the session horizon, per §2.10's scoping. Residual value: the audited stack (signed-bar lane, seasonal baselines, acceptance/trap modules, frozen registry), and the market-science characterizations (S2's object, S3's unsigned bounce).
- **Soil found** ⇒ the sparse-session calibration spend is then warranted, followed by the surviving Phase 6 remainder in revised order — S10/S11 as marginal contributions, S13 races, S16 (boxes defined by whichever of S9/S10 survived), S15 strictly last (its ordering premium needs both components standing) — then Phase 7 restricted to models whose direction layer is alive: **M3 and M5 first** (neither depends on the dead spine), M2's router claims against outcomes.

## 3.4 Parallel and pending items (non-blocking for §3.1)

- **Spread reconstruction** (per-symbol, tick-floored): data engineering, prerequisite for §2.5 reinstatement and for ANY net breadth claim; blocks nothing at the mechanism-screen stage.
- **Trimmed/median re-read of the unsigned failed-break bounce**: cheap; converts the 30–55 bps characterization from upper bound to estimate (or kills it).
- **Horizon-menu screens** (micro holds; structural multi-session; funding-cadence anchors): required before any *whole-family* close per §2.10; not required before §3.1.

## 3.5 Sequencing rationale

The order preserves the property that made Phases 0–5 cost four items and zero reads: the cheapest test of the largest remaining claim goes first, and the claim on the table is the tier's actual thesis — that exact delta pays *where price is blind*. S3 could not test that thesis (its signed tag rode on price-visible geometry); S9 is the purest available statement of it. One screen now carries the family's fate honestly: either the flagship mechanism shows soil and the depth spend is justified, or the third powered null closes the family with its stack, its characterizations, and its dignity intact.
