# CF-HTFCAP-001 — Higher-Timeframe Context × Capture Scale

**Status:** `CLOSED — CHARACTERISED` (2026-07-19, checkpoint-013 retrospective, operator-signed) — **NOT refuted.** XENA-HTFCAP-001 (EXPLORATORY, TRAIN+TEST, no reserved OOS) found a **real, gate-attributable, sign-null-clearing GROSS edge** on BTC `DI_ADX×VOL_HI adx25` H32/H64 (embargoed gross LCB +8..+18, sign p 0.02–0.05) — but **net-of-cost 0/72 cells resolve above zero** (~18 bps taker+GAP+funding wall at 8–16h holds). Cost, not signal, is the wall. 1/2 gate slots (exploratory TEST spend); holdout SEALED. **Re-open path = a new design** (lower-cost/maker entries, or denser cadence with a HIGH-cadence CAL pin), not this family's continuation. *(History: `REGISTERED` 2026-07-16 ckpt-013 D2; SPDR-004/006 WORTH_EXPLORING 2026-07-17.)*  
**Working name:** REF-A  
**Family ID:** CF-HTFCAP-001  
**Chapter:** 04 (NautilusTrader + Bybit USDT-perp primary, INFR-010+)  
**Route:** **SPDR → full XENA** if `WORTH_EXPLORING` (**EXP lane not used**)  
**Companions:**  
- SPDR pack: removed from live `docs/references/` (family closed; pack was SPDR-004 era)  

- Open-Q log: `docs/signal-registry/candidate-families/proposal-ref-ab-open-questions.md`  
- Sibling family: CF-EPSOSC-001  

**Re-open lineage (not a re-run):** CF-HTFDI-001 / P-14 (real thin HTF-DI channel, sub-cost at short grain); CF-MTFCTX-001 capture-scale *intent* (longer holds in design — not a fair HTF-DI monetisation proof). **New D0, new stack, new universe.**

---

## 1. Thesis

Higher-timeframe (HTF) market state can change the **conditional quality and/or economic scale** of lower-timeframe (LTF) trades. Legacy evidence found a **real but thin** directional-conditioning channel and **failed monetisation** at short grain / weak bases. This family re-asks the question on **Bybit USDT linear perps** with:

- unlocked multi-variant exploration (no fixed entry/exit rule set)  
- capture scale (hold / grain) as a first-class axis  
- qualification by **SPDR family justification** then **XENA portfolio contribution under cost**  

**Not claimed a priori:** that USTEC HTF-DI bps transfer to crypto, or that multi-day holds dominate.

---

## 2. Mechanism class (for CAL / checkpoint scoping)

| Attribute | Value |
|---|---|
| Class | **Conditioning / context filters on LTF bases** + **hold-scale capture** |
| Information source | Price OHLCV (optional volume for vol-regime features) |
| Adjudication shape | Multi-candidate portfolio (XENA); not single-cell EXP gates |
| Cost sensitivity | High at short hold (legacy Mode B); funding material at multi-session |
| CAL implication | Binder must support **selectivity under net cost** (L-26 class); pre-search gross-bps floor; funding in cost stack |

---

## 3. Binding decisions (frozen 2026-07-16)

| Item | Decision |
|---|---|
| Pipeline | SPDR (multi-variant, minimal promote) → XENA if promising; **no EXP** |
| Rules | **Not locked** — hypers + sub-modalities in SPDR and XENA |
| SPDR universe | **n = 10** assets via **instrument selection rules** (membership rule-defined; implementation may use `xen.nautilus.universe_selection` once codified) |
| Promote cluster K | **K = 3** |
| Scheduling vs EPSOSC | **Parallel**, separate SPDR packs and separate XENA universes |
| SPDR vs full INFR | SPDR may run on available Bybit 1m OHLCV with TRAIN fence in code once data integrity passes; **XENA waits for Nautilus emission path + cost model + CAL shaped to this class** (CAL is gated on this D0, not the reverse) |
| Funding | **Disclose** at SPDR; **bind** in XENA cost stack + selection |
| SPDR LTF bases | Unfiltered + naive momentum breakout + random-sign control |
| Hold axis | **Must include** 2× and 4× HTF-span holds; short holds (0.5×, 1×) allowed |
| Market priors | Soft (shape grid/diagnostics); hard process bans only |
| Legacy residue | Prior only — re-measure on Bybit |

---

## 4. Hard bans

1. Non-causal HTF/LTF (forming-bar HTF; look-ahead).  
2. Unit lies (ATR screen → bps claim without pin).  
3. Costless net-edge claims; cadence-max as sole success when testing filters.  
4. Passive-limit “edge” without fill-vs-prediction decomposition / MM framing.  
5. SPDR as tradability/deployability.  
6. Chapter-03 XENA registry pins on Bybit without fresh CAL.  
7. Counting a family win from a single multiplicity lottery cell (promote = cluster K≥3).

---

## 5. Soft priors (do not auto-reject crypto novelty)

- Prefer reporting **bps** early; watch sub-cost short-hold clusters.  
- Hold-scaling in ATR on legacy USTEC is a **hint**, not a Bybit fact.  
- Liquid majors via selection rules first; delisted/full archive is XENA/anti-survivorship later unless rules include them.  
- Drift/beta disclosure on directional bases.

---

## 6. D0 exploration plane

### 6.1 SPDR (thin grid — pack is normative)

See `spdr-pack-htfcap-001.md`. Summary:

| Axis | Frozen default |
|---|---|
| Symbols | 10, rule-selected |
| Domains | Include ≥2 of {1h/5m, 4h/15m, 1d/1h} with ≥1 longer-grain pair |
| HTF state | ±DI continuation; ADX gate; optional vol regime — confirmed HTF only |
| LTF base | Unfiltered; naive momentum; random-sign control |
| Hold | 0.5×, 1×, **2×, 4×** HTF span |
| Polarity | with-HTF vs unfiltered (against-HTF optional disclosure) |

**Promote:** WORTH_EXPLORING iff cluster K≥3 on primary **bps** lift vs baseline, neighbourhood rule, TRAIN-only, dependence-honest uncertainty (full text in SPDR pack).

### 6.2 XENA (wide grid — design at universe registration)

After SPDR promote, a dedicated XENA universe (e.g. XENA-HTFCAP-001) expands:

- broader modality × hyper × instrument × domain × hold product  
- **all cells enter** (no per-cell quality gate)  
- cost stack: spread model + fees + **funding**  
- selection: portfolio contribution under **post-CAL cost-aware binder**  
- pre-search: median gross bps/trade vs breakeven band (XENA-003 lesson)  
- finite sizing denominator (`SlPrice` or Nautilus equivalent contract)

Exact XENA manifest is a **later design.md** once CAL hash exists; this D0 fixes **class and constraints** only.

---

## 7. Hypotheses (family-level)

| ID | Question | Stage |
|---|---|---|
| HYP-S1 | On TRAIN Bybit-10, does any coherent HTFCAP variant **cluster** show bps lift over matched baselines (SPDR promote rule)? | SPDR |
| HYP-X1 | Under cost-aware XENA selection, does a portfolio of HTFCAP candidates exhibit structure beyond battery null with net cost binding? | XENA |
| HYP-X2 (disclosure) | Do longer holds (2×/4×) systematically improve bps economics vs short holds within selected portfolios? | XENA / analysis |

No counted TEST until XENA gate rules under the new ledger allow.

---

## 8. Kill / park criteria

| Stage | Kill / park |
|---|---|
| SPDR | NOT_WORTH — no K≥3 cluster; pure noise under multiplicity |
| SPDR | INCONCLUSIVE — underpowered / data not ready (not a negative) |
| XENA | Noise-like under honest binder; or only cadence/print artifacts; or entire mass sub-breakeven pre-search |
| Infra | Cannot emit causally or pin costs — park, don’t book |

---

## 9. Infrastructure dependencies (honest)

| Dependency | Role | Blocks |
|---|---|---|
| Bybit 1m OHLCV + integrity | SPDR | SPDR run |
| TRAIN fence in code | SPDR/XENA | any screen |
| Instrument selection rules (n=10) | Universe membership | SPDR design freeze of ticker list; **codified selector can follow** (parked apparatus OK if rules written in design.md) |
| Nautilus emission contract | XENA candidates | XENA |
| Bybit cost model (fees, spread, funding) | XENA net | XENA selection honesty |
| **XENA CAL + frozen registry** for conditioning/filter class | XENA gate | XENA counted path — **CAL is sequenced after this D0** |
| Optional: multi-instrument single-engine smoke | Engineering confidence | not scientific D0 |

---

## 10. Distinctness (pitfalls)

| Pitfall | Why this is not a re-run |
|---|---|
| P-14 / CF-HTFDI | New stack, new universe, multi-modality, XENA portfolio path, capture axis mandatory |
| CF-MTFCTX | Not the same base-exhaustion package as sole design; cost-aware binder required; no costless filter theater |
| P-01 geometry | Conditioning/context, not single-series pattern entry as the thesis |
| P-10 passive MR | Passive-limit MR not a primary SPDR cell |

---

## 11. Evidence ledger

| Date | Item |
|---|---|
| 2026-07-16 | D0 complete from what-next REF-A discussion + operator Q freeze (Q1=10 rule-selected; Q2–Q5/Q-A* = recommendations) |
| 2026-07-16 | REGISTERED at checkpoint-013 (D2, operator-signed); SPDR-004 assigned; registry row appended (`multiplicity-registry.md` Chapter 04) |
| 2026-07-16 | D3/D5 operator decisions: anti-survivorship binding project-wide (SPDR most-liquid-10 acceptable as justification-only); universe selection is ONLINE (trailing 24h volume, ≤ t−1, rule + rebalance frequency frozen — no fixed list) |
| 2026-07-17 | **SPDR-004 DISPOSITION: WORTH_EXPLORING (operator-signed)** — SOL 4h/15m UNF DI_ADX hold-ladder cluster (5.9→50.1 bps/trade monotone, CI-honest, leak-clean, h2/h4 above floor); caveats: single-symbol, rest sub-floor P-14-shaped, GAP-spread floors, 1d unpowered; XENA-HTFCAP-001 design permitted once INFR-014 pin lands (caveats binding on that design) |
| 2026-07-17 | **SPDR-006 registered + design COMPLETE** — vol-regime facet (VOL_HI/VOL_LO + DI×VOL_HI + DI_ADX×VOL_HI amplifier; pack-optional axis, budget-cut from SPDR-004); separate grid/K per L-23; DI-only variants frozen in SPDR-004, not re-run; amplifier claim requires interaction > frozen direction-only cell; screen not run (`python/experiments/SPDR-006/design.md`) |
| 2026-07-17 | **SPDR-006 DISPOSITION: WORTH_EXPLORING (operator-signed)** — K=3 met on 4h/15m UNF interaction clusters (DI×VOL_HI BTC+SOL all-hold ladder med lift +26.6; DI_ADX×VOL_HI BTC full + SOL h1–h4 med +28.5); amplifier vs frozen SPDR-004 holds (160/164 powered CI+ above direction-only; BTC frozen CI-fail → 4-hold CI+ under VOL_HI gate); standalone vol NOT a promote mechanism; caveats binding on XENA-HTFCAP-001: interaction-only scope, BTC+SOL two-name concentration (drop-both kills K≥3; ETH single seed-fragile cell), holds ≥1× for money, SOL destroy-collapse incomplete 0.55–0.78, no per-year split; XENA gate still blocked on INFR-014 (`python/experiments/SPDR-006/analysis.md` §10) |
| 2026-07-16 | **SPDR-004 design.md COMPLETE** — grid + promote K=3 + L-21 unit pin + §5 selection (daily 00:00 UTC rebalance, trailing 24h volume, ≤ t−1) frozen; P-14 distinctness stated; L-28..L-31 cited; 0 slots / 0 reads; screen execution not started (`python/experiments/SPDR-004/design.md`) |
| 2026-07-19 | **XENA-HTFCAP-001 COMPLETE — operator verdict EXPLORATORY, NOT deployable** (analysis re-done under INFR-016 report layers). Real, gate-attributable, sign-null-clearing GROSS edge on BTC mid-threshold `DI_ADX×VOL_HI adx25` H32/H64 (embargoed gross LCB +8 to +18, sign p 0.02–0.05, collapse ~0.9) — a genuine finding the old top-1 gate framing had hidden. **Net-of-cost: ZERO of 72 cells and ZERO subsets resolve above zero** (~18 bps taker+GAP+funding wall at 8–16h holds; best net LCB −4.6). Binder certified top-1 was a selection artifact (worst corner); SOL v1.5/adxna/H64 suggestive on full window (24.9 bps, p 0.224) but strongly negative on embargoed band. EXPLORATORY window (TRAIN+TEST, no reserved OOS) → **1/2 slots spent, holdout SEALED**. Follow-ups (maker/lower-cost entries, denser-cadence) are NEW designs. Report `python/experiments/XENA-HTFCAP-001/report.md`. **Family status unchanged — transition deferred to checkpoint-013 retrospective.** |

---

## 12. Operator sign-off

| Item | Status |
|---|---|
| D0 content freeze | **Complete** (2026-07-16) |
| Checkpoint-013 include family in agenda | **Done** (ckpt-013 design, 2026-07-16) |
| Assign SPDR-### | **SPDR-004** (2026-07-16) |
| Register family in live ledger | **Done** (D2 operator-signed, 2026-07-16) |
