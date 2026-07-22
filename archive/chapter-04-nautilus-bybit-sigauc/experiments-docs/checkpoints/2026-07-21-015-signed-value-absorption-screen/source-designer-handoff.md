# Handoff for the SIGNAL-SIGNED designer — Checkpoint 015 progress

**Audience:** designer of `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` and of `signed_bar_framework_addendum_v1_1.md` (which governs where the two conflict).
**Purpose:** state what we built and measured for **Phase 6′ (S9 absorption marginal value)**, how we adapted it, what held, what failed, and which of your claims are now closed versus still open — without Xen process jargon.
**Date of work:** 2026-07-21 → 2026-07-22
**Family label here:** CF-SIGAUC-001 (Signed Auction Structure)
**Status of this note:** the S9 screen has **run on the DESIGN bank across all four domain pairs**. Formal analysis and the operator's disposition are **not yet recorded**. This note is evidence and reading, not a family decision.
**Predecessor:** `../2026-07-20-014-signed-auction-structure/source-designer-handoff.md` (Phases 0–5).

---

## 1. One-page summary

Checkpoint-014 killed the price-adjacent arms (S1/S2 spine as P-01; S3 trap-load a powered null). Your own framing was that those failures said little about the mechanisms that are **invisible to price**. Checkpoint-015 exists to test the flagship one: **S9 absorption — heavy measured aggression that produces no price result at a level.**

| Your phase | What we ran | Outcome in plain terms |
|---|---|---|
| **6′ apparatus** — multi-timeframe baselines, sessions, thresholds, coverage | **INFR-020** | **Complete, frozen** (pin `5f170b71…`). Seasonal baselines + p90/p10 cuts + operational anchors at 5m/15m/1h; per-pair usable universes measured. |
| **6′** — S9 marginal value, master go/no-go | **SPDR-009** | **The signed signature adds nothing.** On the only pair that reached power (1d/1m), signed-minus-unsigned is **+1.8 bps at 5 min (CI −3.6…+7.1, MDE 5.5)** and **−3.4 bps at 10 min** — a **powered null**. Dose-response ρ = **+0.008**. Beats matched random timing by **+2.4 bps, CI through zero**. Signal-arm median return **0.0 bps against an 11.3–13.0 bps cost floor.** |
| **6′b** — S14 CVD divergence | not run | Memo-gated rider; unaffected by this note except in kill-order reasoning (§6). |
| §3.4 — tick-floored spread (INFR-019) | not run | Parallel, non-blocking; still the prerequisite for any *net* breadth claim. |

**Net:** your S9 mechanism, operationalised exactly as written and tested at four detection scales, produces **no marginal information over the identical unsigned climax-hold events at the same levels**, on this venue and band, with power adequate to say so at 1d/1m. The three coarser pairs are **inconclusive by event supply**, not by evidence. Zero counted TEST reads; holdout untouched.

---

## 2. What we built for this phase (and what it cost)

### 2.1 INFR-020 — the multi-timeframe apparatus

Your document specifies signals, not scales. The operator widened SPDR-009 to four **domain pairs** (session framing / detection bar): **D1** 1d/1m, **D2** 1h/5m, **D3** 4h/15m, **D4** 1d/1h. That required apparatus you did not have to specify but which anyone replicating will need:

- A5 seasonal baselines at 5m / 15m / 1h (the 1-minute pin from Phase 0 stays sole authority at 1m).
- Per-(symbol, timeframe) p90/p10 residual cuts, by the unmodified frozen rule.
- Operational hour and 4-hour anchors, plus a generalised initial-balance definition per pair.
- A **coverage census** — and this is the finding that matters.

**The coverage census is a first-class result, not plumbing.** A COMPLETE detection window is one in which the instrument traded *every* source minute inside it. Median retention across 194 instruments:

| pair | detection bar | median COMPLETE-window retention | instruments above a 0.50 floor |
|---|---|---|---|
| D1 | 1m | (full 1m path) | **194** |
| D2 | 5m | **0.385** | **72** |
| D3 | 15m | **0.202** | **47** |
| D4 | 1h | **0.089** | **31** |

Surviving windows carry **2.4×–27×** the volume of partial ones (universe median ~6.7× at 60m). So a coarse-bar read on this venue is not "the same signal at a slower scale" — it is **the same signal measured only during continuously-traded periods, unequally across the cross-section.** We state that on every coarse-pair reading.

### 2.2 The invariant that made the pairs comparable

One rule, enforced in code: **HTF and LTF govern session framing and event detection only. Every price-path and volume-at-price measurement stays on 1-minute bars in all four pairs.** Levels, profiles, returns and excursions never touch coarse bars. Without this, "D3 beats D1" would be a bar-aggregation artifact.

### 2.3 Declared deviations from your text (signed, on the record)

1. **Micro horizon scaled to the detection bar.** Your S9 horizon is "micro". We read H ∈ {5, 10} **detection bars** → 5/10 min at D1, 25/50 min at D2, 75/150 min at D3, 5/10 h at D4, plus session-remainder as disclosure.
2. **Contact zone on prior-session range, not IB width.** IB width collapses to a single bar at D3/D4. τ was re-picked per pair on **event counts only** (no outcome), frozen before any read. The original `0.25 × ib_width` zone was retained at D1 as a pre-registered sensitivity.
3. **Strict holdout → TRAIN-internal CONFIRM bank** (carried from ckpt-014). DESIGN `2021-06-29 → 2023-03-01`. TEST and global holdout never queried.
4. **S1 never used as an event qualifier** — per your Addendum §2.7, it is an operational anchor only. Code raises if any path consults it.
5. **D4 pre-declared power-limited** before the run, on the measured candidate census (162 candidates on 12 instruments). It runs for horizon coverage; an inconclusive D4 is not a null.

### 2.4 What we did not change

Per-bar Δ exact, per-level Δ forbidden. Money floor computed **before** any estimation. Marginal framing (`signed − unsigned on identical events`) as the primary read, never "signed absorption reverts". Mirror arm as a first-class control. Mechanisms binary — no re-parameterisation after a powered null.

---

## 3. The screen, as tested

**Event pool P** (per pair): a detection bar with top-decile seasonal **volume** residual, bottom-decile seasonal **range** residual, within τ of one of seven location-qualified levels (this session's IB edges; prior session's value-area edges, POC, and true extremes). Direction = sign of (level − close).

**Three arms inside that same pool:**

| arm | rule | D1 count |
|---|---|---|
| **S9** | large \|Δ\| residual **and** signed score into the level | **311** |
| **MIRROR** | equally large \|Δ\| pointing **away** from the level | **325** |
| **BASE** | everything else in P — the unsigned climax-hold class | **6,550** |

**Trade object:** single leg. Entry at the open of the next detection bar; side = away from the absorbed side; exit H bars later; return in bps of entry price on the 1-minute path.

**Reads:** T1 marginal contrast (S9 − BASE) and its mirror companion; T2 dose-response on the continuous score against a ≥2000-seed derangement; T3 the same contrast on **mid-range** bars with no level nearby (your own prediction: ≈ 0); T4 versus matched random-timing entries; T5 the level alone versus bare touches. Cost floor first. Future-destroy path-swap tripwire over the top.

---

## 4. Results

### 4.1 D1 (1d/1m) — the only pair that reached power

Pool P: **7,186 events, 162 symbols, 169 trading days.**

| read | H = 5 min | H = 10 min | reading |
|---|---|---|---|
| **T1** S9 − BASE | **+1.81 bps**, CI [−3.62, +7.09], MDE 5.5 | **−3.41 bps**, CI [−12.96, +5.00] | **powered null** |
| **T1** S9 − MIRROR | +5.29 bps, CI [−1.94, +12.22], MDE 7.5 | +4.15 bps, CI [−8.22, +15.46] | no direction effect |
| **T2** ρ(score, return) | **+0.008**, p = 0.263, MDE ρ 0.035 | −0.025, negative-side p = 0.023 | score carries nothing |
| **T4** vs matched random timing | +2.39 bps, CI [−2.91, +7.60] | −2.03 bps, CI through zero | no availability edge |
| **T5** location alone vs bare touch | +1.50 bps, CI [−0.93, +4.26] | — | the level alone gives nothing either |
| **Money** | S9 median **0.0 bps** | S9 median **0.0 bps** | floor **11.3–13.0 bps** |

Sensitivities agree, both directions:

- **Tighter pool (P_WIDE, τ = 0.005 of prior-session range, p25 range residual):** 1,911 events, 127 signal. T1 = **−8.3 bps** (H5) / **−13.2 bps** (H10), CI through zero. A tighter-contact variant does **not** rescue the null.
- **Original `0.25 × ib_width` zone:** 5,014 events, 227 signal. T1 = **+0.60 / −3.19 bps**, CI through zero. The zone change did not create the null.
- **T3 mid-range** (your location-necessity prediction): +0.01 bps, CI through zero — **≈ 0 as predicted, but uninformative**, because the located contrast is also ≈ 0 (§7.4).
- **Time stability:** the H10 contrast by chronological third is **+17.8 / −7.7 / −2.0 bps** on **3 / 53 / 255** signal events. The one positive third rests on three events.

### 4.2 D2, D3, D4 — inconclusive by event supply

| pair | usable universe | pool P | S9 | MIRROR | T1 state |
|---|---|---|---|---|---|
| **D2** 1h/5m | 72 | 493 | **16** | 9 | **UNPOWERED** — no plant in the 0–30 bps grid resolved |
| **D3** 4h/15m | 47 | 95 | **2** | 0 | UNPOWERED |
| **D4** 1d/1h | 31 | 14 | **0** | 0 | UNPOWERED (as pre-declared) |

Two D2 cells carry a "CONTRADICTED" label — the mirror contrast at H5 (16 vs 9 events, two shared days) and the dose-response ρ = −0.098. Both lean **against** the mechanism, and neither is worth citing: the first has no paired-day structure, the second is a single tail on 493 events. What D2 does show unambiguously is money: signal-arm median **−27.0 bps** at H5 against a floor near 11 bps.

**The economic argument for coarsening did not survive contact with event supply.** The widening's motivation was sound — a hold-invariant ~11 bps fee gets 2.5 hours to be earned back at D3 versus 10 minutes at D1. But the raw candidate population collapses **95,836 → 9,497 → 2,974 → 640** across D1→D4 on the full 194, and **95,836 → 5,226 → 933 → 162** on each pair's liquid core. Coarser detection buys wall-clock and destroys events. It is not a scale-free trade.

### 4.3 Integrity

| check | outcome |
|---|---|
| Frozen-input hashes re-verified at every entry | pass |
| Band fence, causal ≤ t−1, IB completion refusals, prior-session-only levels | pass, code-asserted |
| 1-minute-only outcome and level construction | pass, raises otherwise |
| Future-destroy path swap | **NO_MATERIAL_EDGE on all four pairs**, positive-control bite passed |
| CF\* (survival threshold) | **UNDERIVABLE** — see §7.6 |
| Counted TEST reads | **0**; holdout sealed |

---

## 5. What worked (durable)

1. **The mechanism is constructible and was constructed faithfully.** Effort-without-result at a location-qualified level, with the side named by the measured taker split — built end to end, at four scales, on 194 instruments, from your definitions.
2. **The apparatus generalises.** Seasonal baselines, class cuts, anchors and level sets now exist at 1m/5m/15m/1h, hash-pinned. Any later multi-scale work in this family is apparatus-free.
3. **The marginal framing did its job.** The screen never asked "does signed absorption revert" — it asked whether the sign adds anything to the same events. That question has a clean answer at D1.
4. **The mirror arm was the sharpest instrument in the design.** It is nearly the same size as the signal arm (325 vs 311) and the contrast between them is a wash. See §7.5 — this is a mechanism finding, not a statistical one.
5. **Cost-first discipline held.** Money floors were published before estimation. The signal arm's median return is exactly zero at the horizon the mechanism specifies.
6. **Cheap again.** One apparatus item plus one screen, TRAIN-only, zero reads spent.

---

## 6. What did not work

| Claim / hope from the source | Evidence |
|---|---|
| The signed absorption signature adds information over the unsigned climax-hold class | **+1.8 bps, CI −3.6…+7.1, MDE 5.5** at D1 — powered null |
| The measured aggression score is monotone with reversal | ρ = **+0.008**, inside a 2000-seed derangement null |
| Absorption events resolve away from the absorbed side over the micro horizon | Signal-arm mean **−2.0 bps** at 10 min; median **0.0** |
| Absorption events at least *go somewhere* (availability) | Beats matched random timing by **+2.4 bps, CI through zero** |
| The location itself carries the effect | Bare-touch contrast **+1.5 bps, CI through zero** |
| Coarser detection scales buy the economics to clear the fee floor | Candidate supply collapses 95,836 → 162; D2–D4 all unpowered |
| A tighter contact zone would find the precise-contact effect | P_WIDE at τ = 0.005 is **more negative**, not less |

**Not claimed refuted by this work**

- **S14** CVD–price divergence (untested; memo-gated).
- **S10 / S11 / S13 / S15 / S16** and the M1–M5 assembly.
- Horizons other than the micro one your S9 specifies — structural multi-session, funding-cadence.
- Absorption at **D2/D3/D4** on a venue or band with enough continuously-traded coarse windows to reach power. On Bybit 2021–2023 there are not enough.

---

## 7. Design notes for you (observations, not demands)

**7.1 The micro horizon is partly dead air.** **16.3%** of D1 pool-P events have a forward return of **exactly 0.0 bps** at 5 minutes (11.1% at 10 minutes) — the price does not move at all. The signal arm's median return is 0.0 for that reason. If S9's prediction is "the level holds and price resolves away", the horizon needs to be defined in units where price is capable of moving (an ATR or session-range multiple, or a first-touch event), not a fixed count of detection bars. A fixed-bar micro horizon on an instrument that is flat by construction at the event bar is a horizon that can only measure noise.

**7.2 Detection scale and hold length should be decoupled.** The economic case for coarsening is real — the fee leg is hold-invariant, so a longer hold earns it back. But we coarsened **detection** in order to lengthen the **hold**, and that destroyed the event population two orders of magnitude. If a future revision wants the economics, it should say: detect at the finest scale where the residual class is calibrated, and hold for the wall-clock the cost structure requires. Those are independent choices and the source currently ties them together.

**7.3 State the activity conditioning as part of the signal.** **78% of located D1 events (25,247 of 32,433) were dropped for lack of a contiguous 1-minute outcome path.** That is not a bug — it is what a 24/7 venue with illiquid alts looks like. It means every reading here is conditioned on continuously-traded windows, and it is selection on *post-entry* activity. It hits both arms alike, so the marginal contrast is largely protected; the **absolute** returns and the floor comparison are not. Any absorption claim on a gappy venue must state this, and any framework that assumes continuous quoting should say so explicitly.

**7.4 Pair every "X is necessary" prediction with a positive control.** Your T3-equivalent prediction — unqualified mid-range absorption should be ≈ 0 — **came true** (+0.01 bps). It carries no information, because the *located* contrast is also ≈ 0. A necessity prediction can only discriminate if the framework also predicts something that must fire. Consider naming, for each signal, the one cell the framework says **must** be non-null.

**7.5 The sign is nearly symmetric in the event census, and that is a mechanism problem.** At D1 the mirror arm (**325**) is *larger* than the signal arm (**311**); at the ten-instrument design census it was 31 versus 19. Your mechanism says the measured split **names the losing side** at a flat-price high-volume bar. If it did, you would expect the into-level tail to be structurally distinguishable from the away-from-level tail at qualified levels. Instead the two tails are the same size and their forward returns are a wash. Either the projection of Δ onto "into the level" is not the right direction operator, or the flat-price bar's split is symmetric noise. That is the single most useful negative datum in this screen.

**7.6 The leak gate could not be calibrated, and the reason is instructive.** CF\* is meant to be derived by planting a known causal effect at 1× the published MDE and seeing how much survives the destroy. At D1 the 1× plant **never produced a material contrast** (no usable seed), and at 2×/3× the threshold swung **1.12 → 0.70**. On D2–D4 no strictly positive MDE existed at all. So the tripwire ran, its positive control bit, and it had nothing to bite: **NO_MATERIAL_EDGE on all four pairs.** As in ckpt-014, this is the correct integrity outcome for a null — **it is not evidence that anything is leak-free**, and it must not be cited as one.

**7.7 The tighter zone is more negative than the wider one.** Zone-dilution asymmetry usually protects a null from over-reading: a wide zone dilutes a precise-contact effect. Here the tighter pool is *worse* (−8.3 / −13.2 bps). That closes the standard escape hatch for this particular null.

---

## 8. Where the family stands (and the one open decision)

The checkpoint's closure rule, as amended on 2026-07-22, is: **close the family only on a powered null on every pair that reaches power, and at minimum on D1 and D2.**

What the run delivered:

- **D1 — powered null.** T1 wash on both pools at both holds, with MDEs published at realised n, mirror-clean, floor not cleared.
- **D2 — inconclusive.** T1 unpowered on both pools (16 signal events). Not a null.
- **D3, D4 — inconclusive**, D4 exactly as pre-declared.

So the screen **kills S9 as a strategy-relevant signed refinement at 1d/1m** but does **not**, as written, satisfy the closure rule. The operator's open question is whether D1's powered null suffices — our reading is that D2's shortfall is a **structural event-rate fact on this venue and band**, not a sampling accident, and that no additional DESIGN-band data will fix it. Reaching power at D2 would need a different venue, a longer band, or a redefinition of the coarse-bar event.

**Recommended kill order from here (unchanged in spirit from ckpt-014's addendum):**

1. Record S9's D1 powered null; do not re-parameterise (binary-mechanism rule).
2. **S14 may still run** — it is the last cheap test of "signed value where price is blind", and its object (integration across bars, decoupling from price) is genuinely different from both the S3 trap load and the S9 single-bar split. Its differentiation memo now has a harder bar to clear: it must explain why *cumulative* delta carries information when both the **failed-break Δ tag** (S3) and the **flat-bar Δ split** (S9) do not.
3. If S14 also nulls, the signed mechanism family is cleanly dead on this horizon menu, and the residual value is what it was: an audited stack, an exactly reconciled taker split, and two market-science characterisations.

---

## 9. Artifacts map

| Item | Root |
|---|---|
| Checkpoint design (incl. decisions D1–D7) | `docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md` |
| Ckpt-014 handoff (Phases 0–5) | `../2026-07-20-014-signed-auction-structure/source-designer-handoff.md` |
| Family card | `docs/signal-registry/candidate-families/cf-sigauc-001.md` |
| Multi-timeframe apparatus | `python/experiments/INFR-020/` (pin `5f170b71…`) |
| S9 screen — design, QA, code, results | `python/experiments/SPDR-009/` |
| Screen reads | `SPDR-009/results/layers.json`, `power_census.json`, `pool_cuts.json`, `floor_table.json`, `mde_curves.json`, `tripwire_cf_D*.json` |
| Per-event emissions | `SPDR-009/results/events_DESIGN_D*_{P,P_WIDE,MID_RANGE}.parquet` |
| Shared implementation | `python/src/xen/sigbar/absorb.py` |
| Source (normative) | `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` + Addendum v1.1 |

**Provenance caveat on the numbers above:** they are read from the completed DESIGN-band emission of 2026-07-22 06:33 UTC. A re-run was started later that day and stopped after the D1 event build; the reported layers were not regenerated by it. Confirm the snapshot before quoting these figures externally.

---

## 10. Bottom line for the designer

We built your multi-scale apparatus, then ran the cleanest available statement of the framework's flagship claim: **does the measured taker split add reversal information at a flat-price, high-volume bar sitting on a qualified level, over the identical unsigned events at those same levels?**

At the one scale with the power to answer: **no.** +1.8 bps against an MDE of 5.5 and a cost floor of 11.3. Dose-response ρ of +0.008. The into-level and away-from-level tails are the same size and behave the same way. The signal arm's median return over the mechanism's own horizon is exactly zero.

The most useful thing we can hand back is not the null itself but **§7.5**: at the event class your mechanism singles out as definitionally invisible to price, the measured split does not appear to name a losing side. If the framework has a reply to that, it is the reply that decides whether anything downstream of S9 is worth building.

---

*Prepared as a research handoff from the Xen checkpoint-015 execution record. The screen's formal analysis and the family's keep/close decision remain the programme operator's acts.*
