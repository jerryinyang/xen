# SPDR-009 — Report: signed absorption marginal value (S9), four domain pairs

**Item:** SPDR-009 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 015 §3 seq 1 (§D6/D7)
**Lane:** SPDR — TRAIN-only availability screen · **Bands:** DESIGN only · **Counted TEST reads: 0** · **Holdout: SEALED**
**Status:** **COMPLETE 2026-07-22 — operator disposition `NOT_WORTH`**
**Role:** the checkpoint's master go/no-go — framework-falsifier #3 (does the measured signed signature add value where price is blind?)

---

## 1. Disposition

**`NOT_WORTH`** — on identical location-qualified events, the signed absorption signature adds **no**
marginal reversal information over the unsigned climax-hold class at the same levels. At the one
domain pair that reached power (**D1**, 1d/1m) this is a **powered null**. The three coarser pairs
are **inconclusive by event supply**, not by evidence.

The design's three-leg soil conjunction (§4) fails on all three legs at D1:

| leg | requirement | measured |
|---|---|---|
| (i) the signal's own claim reproduces | T1 positive, exceeding its mirror, T2 surviving derangement, T3 ≈ 0 | **T1 WASH** (+1.81 bps, MDE 5.5); mirror contrast WASH; **T2 ρ = +0.008**, inside the derangement null; T3 ≈ 0 but uninformative (§5.4) |
| (ii) beats a matched unconditional control | T4 positive | **WASH** — +2.39 bps, CI [−2.91, +7.60] |
| (iii) clears the measured cost floor | S9 median return above floor | **AT_OR_BELOW_FLOOR** — median **0.0 bps** against **11.3–13.0 bps** |

**Process note (operator-directed).** The operator dispositioned directly on the emitted report
layers; the `data-analyst` stage was **waived**, so this item has no `analysis.md`. The evidence
below is read from the emitted artifacts, not from an analyst pass. Recorded as a deviation, not
as a completed analysis stage.

---

## 2. What was run

Four pre-registered **domain pairs** (session framing / detection bar) under one frozen design:
**D1** 1d/1m · **D2** 1h/5m · **D3** 4h/15m · **D4** 1d/1h. Binding invariant (D6.3): HTF and LTF
govern session framing and event detection only — **every price path, level and profile stays on
1-minute bars in all four pairs.**

**Event pool P** per pair: top-decile seasonal volume residual **and** bottom-decile seasonal range
residual (effort without result), within `τ × prior-HTF-session-range` of one of seven
location-qualified levels (this session's IB edges; prior session's VA edges, POC, true extremes).
τ re-picked per pair on **event counts only**, frozen to `results/pool_cuts.json` before any read.

**Three arms inside that pool:** **S9** (large |Δ| residual with the signed score pointing *into*
the level) · **MIRROR** (equally large |Δ| pointing *away*) · **BASE** (the unsigned remainder).

**Object:** single-leg micro reversal — entry at the next detection bar's open, side away from the
absorbed side, exit at H ∈ {5, 10} detection bars, return in bps of entry price on the 1-minute path.

**Universe:** the INFR-020 0.50-retention core per pair — **194 / 72 / 47 / 31** instruments
(breadth denominator 296, survivorship caveat binding). Frozen inputs: registry `5c386984…`,
1m baselines `1b7244c8…`, column pins `e3b9fd9b…`, catalog fence `35d3375e…`, INFR-020 manifest
`5f170b71…` — all re-hashed at entry.

---

## 3. Evidence — D1 (1d/1m), the only powered pair

Pool P: **7,186 events · 311 S9 · 325 MIRROR · 6,550 BASE · 162 symbols · 169 days.**

| read | H = 5 min | H = 10 min | label |
|---|---|---|---|
| **T1** S9 − BASE (primary) | **+1.81 bps**, CI [−3.62, +7.09], MDE 5.5 | **−3.41 bps**, CI [−12.96, +5.00] | **WASH** (powered null) |
| **T1** S9 − MIRROR | +5.29 bps, CI [−1.94, +12.22], MDE 7.5 | +4.15 bps, CI [−8.22, +15.46] | WASH |
| **T2** ρ(signed_score, ret) | **+0.008**, one-sided p 0.263, MDE ρ 0.035 | −0.025, negative-side p 0.023 | WASH |
| **T3** mid-range (location necessity) | +0.01 bps, CI [−14.23, +12.13] | +4.78 bps, CI spans zero | WASH |
| **T4** vs matched random timing | +2.39 bps, CI [−2.91, +7.60] | −2.03 bps, CI spans zero | WASH |
| **T5** level alone vs bare touch | +1.50 bps, CI [−0.93, +4.26] | — | WASH |
| **Money** | S9 median **0.0 bps** | S9 median **0.0 bps** | floor 11.3–13.0 bps |

**Sensitivities — both directions, both null.**

- **P_WIDE** (p25 range residual, τ = 0.005): 1,911 events / 127 S9. T1 = **−8.31** (H5) / **−13.18**
  (H10) bps, CI spans zero, MDE 18.5. A tighter-contact variant does not rescue the null — it is
  *more negative*, which closes the usual zone-dilution escape.
- **`0.25 × ib_width` retained census** (the originally QA-approved zone): 5,014 events / 227 S9.
  T1 = **+0.60 / −3.19** bps, CI spans zero. The zone change did not create the null.
- **Time stability:** the H10 contrast by chronological third is **+17.8 / −7.7 / −2.0** bps on
  **3 / 53 / 255** S9 events. The single positive third rests on three events.

---

## 4. Evidence — D2, D3, D4

| pair | usable | pool P | S9 | MIRROR | T1 (both pools) | money |
|---|---|---|---|---|---|---|
| **D2** 1h/5m | 72 | 493 | **16** | 9 | **UNPOWERED** — no plant in the 0–30 bps grid resolved | S9 median **−27.0 bps** (H5) |
| **D3** 4h/15m | 47 | 95 | **2** | 0 | UNPOWERED | — |
| **D4** 1d/1h | 31 | 14 | **0** | 0 | UNPOWERED (as pre-declared, D7) | — |

Two D2 cells carry a `CONTRADICTED` label — the mirror contrast at H5 (16 vs 9 events, **2 shared
days**, unpaired) and T2 ρ = −0.098. Both lean *against* the mechanism and neither is citable.

**The economic case for coarsening did not survive event supply.** The candidate population
collapses **95,836 → 9,497 → 2,974 → 640** across D1→D4 on the full 194, and
**95,836 → 5,226 → 933 → 162** on each pair's liquid core. Coarser detection buys wall-clock
against a hold-invariant ~11 bps fee and destroys the events needed to measure anything.

---

## 5. Reading rules applied (and one that binds hard)

**5.1 UNPOWERED is never a null.** D2/D3/D4 are recorded as *horizon-covered but inconclusive*.
D4's silence was pre-declared as expected (checkpoint D7) and contributes nothing either way.

**5.2 The leak tripwire had teeth and nothing to bite.** All four pairs return
`NO_MATERIAL_EDGE`; the positive-control bite passed everywhere. **CF\* is `UNDERIVABLE`** — at D1
the 1× MDE plant produced no material contrast on any of 200 seeds, and the 2×/3× plants give
1.12 / 0.70, a 0.42 spread. Per Addendum §2.8 this is the correct integrity outcome for a null and
**may not be cited as evidence that anything is leak-free.**

**5.3 Activity conditioning is on the reading, not just the universe.** **25,247 of 32,433 located
D1 events (78%) were dropped** for lack of a contiguous 1-minute outcome path (D2 1,031/1,524;
D3 116/211; D4 31/45). This is the venue, not a defect — but it means every figure here is
conditioned on continuously-traded windows, and it is selection on **post-entry** activity. It
applies to both arms, so the marginal contrast is largely protected; the **absolute** returns and
the floor comparison are not.

**5.4 T3 ≈ 0 confirmed the source's prediction and told us nothing.** Unqualified mid-range
absorption is ≈ 0, exactly as S9 predicts — but the *located* contrast is also ≈ 0, so the
necessity prediction cannot discriminate. Recorded as a design lesson, not as support.

**5.5 The micro horizon is partly dead air.** **16.3%** of D1 pool-P events return *exactly*
0.0 bps at 5 minutes (11.1% at 10 minutes). That is why the S9 median is 0.0.

**5.6 The sign is nearly symmetric.** MIRROR (325) is *larger* than S9 (311) at D1, and the two
behave alike. The mechanism claims the measured split **names the losing side** at a flat-price,
high-volume bar; the event census shows two tails of equal size and equal forward behaviour. This
is the screen's most informative negative datum.

---

## 6. Integrity

| check | outcome |
|---|---|
| Frozen-input hashes (INFR-017/018/020) re-verified at entry | PASS |
| Band fence (DESIGN only; TEST/holdout unreachable) | PASS, code-asserted |
| Causal ≤ t−1; IB-completion refusals; prior-session-only levels | PASS, raises otherwise |
| D6.3 — outcomes and levels on 1-minute bars only | PASS, raises otherwise |
| COMPLETE-window-only candidates | PASS |
| Window disjointness + within-(symbol, pair) refractory | PASS |
| No per-level Δ; no local accounting; no S1 acceptance gate | PASS |
| Future-destroy path swap | `NO_MATERIAL_EDGE` ×4, bite PASS, CF\* UNDERIVABLE |
| Counted TEST reads / slots | **0 / 0**; holdout SEALED |

**Provenance caveat (recorded, not resolved).** The reads above come from the completed DESIGN-band
emission of **2026-07-22 06:33 UTC** (`results/layers.json`, `mde_curves.json`, event parquets). A
re-run was started at 12:14 and stopped after the D1 event build; `power_census.json`,
`pool_cuts.json` and `floor_table.json` carry the later timestamps while the layers do not. The
census figures in those three files are count-only and consistent with the layers, but the
timestamps are not aligned. Anyone re-quoting these numbers should re-run the screen end to end
first. This did not affect the disposition — the D1 null holds on both the sample and full-universe
censuses.

**CONFIRM band:** not exercised. The design permits one verify pass; the operator closed on the
DESIGN-band powered null without spending it.

---

## 7. Scope of this negative

**What is dead:** S9 as a signed refinement with marginal value over the unsigned climax-hold class,
on Bybit USDT perpetuals, DESIGN band 2021-06-29 → 2023-03-01, at the micro horizon the source
specifies (5 and 10 detection bars), at detection scales 1m / 5m / 15m / 1h, with the money floor
computed first.

**What this does not test:** S14 (CVD–price divergence, never run); structural multi-session and
funding-cadence horizons; absorption on a venue or band with enough continuously-traded coarse
windows to power D2–D4; any of S10/S11/S13/S15/S16 or the M1–M5 assembly.

**Binary-mechanism rule applies.** S9 is not re-parameterisable after a powered null — a future
absorption proposal needs a new written mechanism, not a new threshold, zone or hold.

---

## 8. Artifacts

| Artifact | Path |
|---|---|
| Design (frozen, D6 four-pair + D7) | `python/experiments/SPDR-009/design.md` |
| QA (append-only, runs 1–13) | `python/experiments/SPDR-009/qa-review.md` |
| Screen runner | `python/experiments/SPDR-009/screen_code/absorb_screen.py` |
| Shared module | `python/src/xen/sigbar/absorb.py` (+ `python/tests/test_sigbar_absorb.py`) |
| Report layers (all reads) | `results/layers.json` |
| Power / pools / floors / MDE | `results/power_census.json`, `pool_cuts.json`, `floor_table.json`, `mde_curves.json` |
| Tripwire | `results/tripwire_cf_D{1..4}.json` |
| Per-event emissions | `results/events_DESIGN_D{1..4}_{P,P_WIDE,MID_RANGE}.parquet` |
| Designer handoff | `docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/source-designer-handoff.md` |

---

## 9. Family consequence

**None taken by this item.** A screen produces evidence and an item-level disposition; family status
is a retrospective act. The checkpoint-015 retrospective records the family decision — see
`docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/retrospective.md`.
