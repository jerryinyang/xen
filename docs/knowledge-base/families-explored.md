# Families Explored — Dispositions

Every candidate family the programme opened, and where it landed. Live status: the
signal-registry; full cards: `archive/chapter-01-*/` and `archive/chapter-02-*/`
under `docs/experiments-docs/families/`.

## The availability 2×2 (the frame for what's open)

The decisive lesson of Chapter 01: single-instrument, event-driven, **price-geometry**
entries carry **no signal-conditional favourable excursion beyond a matched random control**
(availability ≈ random). Established twice with matched-control designs (EXP-047, EXP-081).
The programme's historical error was measuring availability *last*, after building a whole
family. The frame for future families:

```
                  DIRECTIONAL target              MAGNITUDE / range target
single-series  │  TESTED → DEAD                 │  screened (CF-VOLEXP-001): typical range
               │  (EXP-047/081/084)             │  flat, only a tail-only hint
cross-section  │  screened (CF-XSECT-001):      │  UNTESTED
               │  NOT_ADMITTED (below band)     │
```

The one thing the evidence forecloses: another entry whose distinguishing feature is its
single-instrument price-geometry *pattern* on a *directional* target. That cell is dead twice
over. The frontier is cross-sectional/magnitude/flow — or **non-price data acquisition** if
those also null out.

## Family dispositions

| Family | What it was | Disposition |
|---|---|---|
| **framework-referee** | The evaluation suite itself (EXP-001–019) | **CONCLUDED / FROZEN** — under Chapter-02 **adaptivity renew** (gate rigidity, [lessons-and-amendments.md](lessons-and-amendments.md) L-12; Phase 001). Frozen suite stays binding until a redesign is FPR-recalibrated and re-ratified. See [evaluation-framework.md](evaluation-framework.md). |
| **CF-AVWAP-001** | Anchored-VWAP bounce on regime pivots (trend-continuation pullback entry) | **CLOSED.** Components positive gross (bounce reaction +3.8/+9.1/+37.6 bps; lifetime move supported) but **cost-dominated**: net tradability INCONCLUSIVE (EXP-030); the one sanctioned holdout shot was INCONCLUSIVE (EXP-032, n=27, +20.6 bps, margin-insufficient). Exits (010/011), entry params (012), and the anchor (013) all measured **flat**. EURUSD holdout permanently contaminated. |
| **CF-HA-HARAMI-001** | HA-harami exhaustion reversal, conditioned on strong-move | **CLOSED / marginal.** Conditioned efficacy EVIDENCE_FOR on benchmark geometry (EXP-053) but on fresh 5-year disjoint data separation from random is **≈ chance** (25/46 cells; favourable availability *below* random). Portfolio TEST (EXP-071) NOT_CONFIRMED. A real edge on old data under one geometry that is marginal-to-absent on fresh data and reverses OOS. |
| **CF-CAPGEO-001** | Capture geometry — triple-barrier exits over compression substrates (the pivot after "move availability was never the constraint; capture geometry is", EXP-047) | **CLOSED.** HYP-004 confirmation read (EXP-084, portfolio NZDUSD/USDCAD/USTEC-4h) **NOT_CONFIRM** — basket separates on TRAIN but all economic OOS legs fail; the apparent edge was selection-region overlap and reverses in held-back folds. |
| **CF-MR-001** | RSI-2 mean-reversion fade + EXIT-RCT favourable-limit exit | **CLOSED — REFUTED (retracted).** Availability ADMITTED (G-020, gross MFE, no RCT limit — *unaffected*). But TRADABLE (G-021) and DEPLOYABLE_CONFIRMED (G-022, EXP-097 holdout shot) were **RETRACTED 2026-06-26**: an uncaught one-bar look-ahead in the EXIT-RCT favourable limit inflated the edge ~+0.25 ATR/trade; causalized, the strategy is net-negative even gross. **The 11 EXP-093 counted TEST reads and the EXP-097 holdout shot are SPENT-ON-DEFECT (non-refundable).** See [lessons-and-amendments.md](lessons-and-amendments.md) L-01. |
| **CF-VOLEXP-001** | Screen M — single-series magnitude/volatility-expansion availability | **Provisionally ADMITTED (non-binding).** Typical range is *flat* vs random; only a tail-only hint. A "pass" on the tail read is a long-vol finding, not a tradable directional edge; routes to a properly scoped vol-expansion family under the §3 harvest model (two-sided cost). |
| **CF-XSECT-001** | Screen X — cross-sectional relative-strength directional availability | **NOT_ADMITTED** (below the multiplicity-adjusted admission band on the screen). Remains the a-priori mechanism favourite but did not earn admission on the directional-favourable endpoint. |
| **infrastructure-validation** | VAL-/INFR-series: substrate validation, universe collection, 5-year re-collection | Ongoing infra. VAL-003 admitted the 17-instrument universe; INFR-003 re-materialized the 5-year 16-instrument dataset (VAL-005 PASS); VAL-002 = behavioral-suite reproduction for cTrader ports. |

## Chapter 02 family dispositions (2026-06-27 → 2026-07-09)

Chapter 02 opened seven arcs; **every candidate family closed negative** — but each closed
*for a mechanistic reason*, recorded here so no re-run happens without a genuinely new object.
Full cards: `archive/chapter-02-mr-volharv-htfdi/docs/experiments-docs/families/`.

| Family | What it was | Disposition (mechanism) |
|---|---|---|
| **Referee-renew (E-series + E7)** | Chapter-02 rebuild of the referee gate | **COMPLETE / FROZEN.** §10.3a (validity→economics) at q\*=0.75 DET-dominates the Chapter-01 frozen gate 32/32; variant-c (single statistic, no absolute floor) REFUTED. E6 added the P\*-capable gate (engine-realized fill series); E7 added the 15m domain (additive rows, gate logic byte-unchanged). Hash-pinned in `python/experiments/EXP-005..007,011/results/freeze_manifest.json`. INFR-004 later hardened `block_bootstrap_ci` (seed battery, block sweep) without touching gate logic. |
| **CF-MR-002** — causal RSI-2 fade | cTrader-primary benchmark of the rollover | **EXONERATED / NOT-TRADABLE 34/34** (EXP-006). Fade beats a naive momentum baseline but is net-negative in absolute terms; binding leg = L3 absolute neutral floor. Leak-clean on the faithful engine fill. |
| **CF-MR-003** — deviation-from-HTF-anchor MR | Anchor-reversion fade, limit-at-anchor | **RETIRED.** Availability SCREENED-ADMIT (EXP-009, native dislocation-matched null) but NOT-TRADABLE at 1h (unpowered) and 15m (powered, 0/24 admit): capturable move < round-trip cost. EXP-008's EXONERATE was a **vehicle artifact** (L-13). |
| **CF-MR-004** — cross-instrument fixed-param spreads | S5–S8 anchor series, limit entries | **RETIRED (CREDIBLE_NEGATIVE, EXP-014c).** Both powered primaries net-fail; mechanism = **entry-seam mismatch** — the limit-touch fill is a different conditioning event than the measured confirmed-close-breach (adverse selection); exits exonerated, no rescue possible. EXP-014b: 1h arm was own-price auto-reversion leak. Extend-arm field spun out → CF-MR-005. |
| **CF-MR-005** — 4h ladder scale-in own-price harvest | The EXP-014c extend-arm discovery | **RETIRED (EXP-018).** Episode-net primary WASH in all residue cells; **random-timing matched-cadence ladders reproduce per-leg CI_low>0 with no signal** (the anomaly's form is producible unconditioned); surviving US2000 cell = 2022 long-drift carry. Arc also produced L-16 (estimand↔object match) and L-17 (referee short-band blindness); EXP-016's 3 TEST reads SPENT_ON_DEFECT (critical-017). |
| **CF-VOLHARV-001** — two-sided oscillation harvest | Rebalance premium + symmetric grid | **RETIRED.** HYP-001: the EXP-018 NZDUSD per-leg positive is a sampling draw of a zero-mean construction (441-run seed battery; analytic E[gross]=0). HYP-002 (EXP-020): rebalance premium real but ~100× smaller than designed (UNPOWERED); grid fills at 5–28% of implied cadence, cap-locked, censored-inventory erases 100–155% of harvest — **structure failure, not substrate absence**. FX MR substrate (VR<1) genuinely exists. A within-episode-clearing structure = NEW family. |
| **CF-CSRR-001** — cross-sectional consensus-residual reversion | Basket-hedged fade of member deviation from USD-strength / equity consensus | **RETIRED (availability).** The consensus residual **does** mean-revert on both baskets (VR(2)<1, 28/28 FX and 40/40 index cells) but no mechanism-faithful (hedged) construction clears multiplicity — the tradable idiosyncratic component is ≈0; survivors are drift/beta. Disclosed leads (AUDUSD/USDCAD, USTEC session-open) all effect-at-MDE, retired at 0 cost. |
| **CF-HTFDI-001** — HTF ±DI continuation conditioning | USTEC 1h/5min sign-conditioning from the SPDR screen lane | **RETIRED (magnitude, not existence — EXP-025).** The conditioning channel is REAL and replicates blind, but true effect ≈1–4 bps/trade after capture dilution — below commission on FX, ~1/10 the selection bar on indices; index positives 99% drift-side aligned, no DI dose-response. The "30–60 bps" graduation target was a **4.1× ATR-unit inflation** at the screen→graduation seam (L-21). T1-terminal powered negative: 0/440 qualifiers, MDE ≤5.2 bps on 2.43M trades. |

### The updated availability frame

Chapter 02 extends the Chapter-01 2×2 verdicts:
- **Own-price directional reversion (single + cross-instrument anchors): CLOSED** — availability
  sometimes admits, but the capturable move never survives the capture/cost seam (CF-MR-002..005,
  four different vehicles, same veto).
- **Cross-sectional reversion endpoint: CLOSED at availability** — the factor residual reverts but
  the hedged (idiosyncratic) component is untradably small (CF-CSRR-001).
- **HTF conditioning of LTF sign: REAL but sub-cost** at the tested granularity (CF-HTFDI-001).
- **Volatility harvest: substrate exists (FX VR<1), tested structures fail mechanically**
  (CF-VOLHARV-001) — the one cell where the negative is about structure, not substrate.

## Chapter 03 family dispositions (2026-07-09 → 2026-07-14)

One family arc — the first run through the XENA portfolio-adjudication lane — plus the
referee-redesign infrastructure it forced. Full card:
`docs/signal-registry/candidate-families/cf-mtfctx-001.md`; archived docs:
`archive/chapter-03-xena-mtfctx/experiments-docs/`.

| Family | What it was | Disposition (mechanism) |
|---|---|---|
| **CF-MTFCTX-001** — MTF context filters on naive controls | HTF context (V01–V18 filter variants) over three control substrates (RANDOM / naive momentum / naive reversion via native limits), adjudicated by XENA portfolio selection across 12 instruments, 2,736 candidates each | **RETIRED 2026-07-14 (substrate-exhaustion; operator-signed, ckpt-011).** The negative filter-structure read (V00 never under-selected; 4.0× **over**-represented on reversion) is **confounded** by the costless cadence-maximizing objective (L-26) and is explicitly NOT the grounds. Grounds: all three substrates independently exhausted — RANDOM is noise; momentum shows no detectable structure even unfiltered (+0.26 vs random control, inside dispersion 2.90); reversion is real gross (+1.958 bps/leg) but **cost-fatal** and 91.2% passive-limit print artifact (P-10 fifth vehicle). Prior P-14 (HTF conditioning ~1–4 bps, sub-cost) unmoved. A fair conditioning test needs a cost-surviving base edge + the net-bound objective = **NEW family with a new D0**, never a re-run of these controls. |
| **XENA referee (INFR-006 → INFR-009)** | The portfolio-adjudication layer itself | **INFR-006 v3 extensive-F/plateau adjudicator SUPERSEDED** (L-25: absolute floor on an extensive statistic, calibrated at 24 cands/400 budget, inoperative at live scale — RANDOM certified 4/12 finalists vs 0.75% null). **INFR-009 exit-(c) two-stage binder RESTORED the route 2026-07-14** (DUAL_CERTIFY α̂ 5.0%; net 1.0 bps bound into the objective; pin `db87dc1a…`). Registry **VOID on the INFR-010 Nautilus/Bybit stack** — binder form + CAL discipline carry, constants must be re-calibrated. |

Chapter 03 frame update: the XENA-002/003 substrate reads extend the chapter-02 closures —
naive momentum and naive reversion on the index/commodity CFD basket are dead as base edges
(no structure / cost-fatal print artifact). The chapter-02 terminal-branch statement stands;
the programme's answer is the INFR-010 pivot to a **new data frontier** (full Bybit USDT-perp
universe, anti-survivorship, orderflow store deferred) rather than another price-geometry
family on the exhausted dataset.

## Chapter 04 family dispositions (2026-07-14 → 2026-07-22)

Chapter 04 established the Nautilus/Bybit substrate and opened three families. Full live cards
remain in `docs/signal-registry/candidate-families/`; experiments move with the chapter archive.

| Family | What it was | Disposition (mechanism) |
|---|---|---|
| **CF-HTFCAP-001** — HTF direction × volatility × capture scale | DI/ADX direction conditioned by high volatility, with 8–16h hold ladders | **CLOSED—CHARACTERISED, not refuted.** BTC `DI_ADX×VOL_HI` H32/H64 produced real gross LCB +8..+18 bps and sign p≈0.02–0.05, but **0/72 cells and 0 subsets net-positive**; best net LCB −4.6 under the run's ~18 bps taker/GAP/funding wall. Volatility is an amplifier of directional drift/continuation, not a standalone signal. The exact family has no untouched OOS and cannot be called deployable; a fixed lower-cost intraday product is a new D0, not continuation. |
| **CF-EPSOSC-001** — vol-expansion arm → episode reversion | RET_ANCHOR/HYBRID episode clearing after volatility expansion | **RETIRED—REFUTED.** SPDR's positive tail concentrated in a few names; XENA-001 selected an AKRO short/downtrend pedestal; mass-aligned XENA-002 failed overlap-aware gross LCB (−68.2) and net LCB (−102.1), with live performance below the matched-drift P95. The apparent edge was volatility-window clustering/unconditional drift, not the armed reversion mechanism. |
| **CF-SIGAUC-001** — signed auction structure | Session spine, signed trap load and effort-without-result absorption using exact taker buy/sell volume | **CLOSED.** Three independent negatives: SPDR-007 price spine reproduced a quantile but not skill versus matched unconditional timing; SPDR-008 signed trap-load was powered null on IB/PVA/PRIOR; SPDR-009 D1 signed absorption was powered null (+1.81 bps, CI [−3.62,+7.09], MDE 5.5, score ρ +0.008, median 0 below 11.3–13.0 bps floor). D2/D3/D4 were event-rate-inconclusive (16/2/0); S14 and structural/funding-cadence horizons were untested. S3 and S9 are deleted, not threshold-remineable. Exact taker-side volume and its apparatus survive as data infrastructure, not edge. |
| **Nautilus/Bybit infrastructure (INFR-010..020, VAL-008)** | Engine migration, fenced catalog, emission/reconciliation, signed bars, Bybit calibration and report-layer correction | **COMPLETE as apparatus; Chapter-05 no-spread amendment QA-approved.** VAL-008 passed 39/39. Raw aggressor split reconciled 20/20 symbol-days. Stored `SpreadBps` is not quote spread and is pinned `UNUSABLE`; no replacement spread proxy is used. Spread cost is unavailable and not charged, so reported cost understates total cost. |

Chapter 04 updates the availability frame: a genuinely non-price input was acquired and tested,
but the first signed transforms added no marginal directional value. The repeatable material
gross effects remained drift, beta and volatility clustering. If the product permits systematic
directional exposure, test that product honestly with risk and costs rather than defining its
only durable return source away; this is not evidence that a net edge already exists.

## Chapter 05 family dispositions (2026-07-22 → 2026-08-07)

Checkpoints 016, 017 and 018. One family, three checkpoints, `0` counted TEST reads and `0`
multiplicity slots across the entire chapter. `XENA-VOLDIR-001` was reserved and never opened.

| Family | What it was | Disposition (mechanism) |
|---|---|---|
| **CF-VOLCONV-001** — assumed volatility + late range-break direction | The L1 conversion path opened at the chapter-05 boundary | **CLOSED.** SPDR-011 L1 NOT SUPPORTED. Superseded by the structural decomposition programme, which separates the volatility claim from the direction claim rather than assuming the first and testing the second. |
| **CF-VOLDIR-001** — structural volatility + direction programme | Separate the claims — (A) is volatility modellable, (B) does fast direction have positive expectancy in bps, (C) capture geometry, (D) cost — so that failure is *diagnosable* rather than vague. Two independent universes: 25 Bybit USDT-perps and 3 cTrader instruments (EURUSD/XAUUSD/USTEC, INFR-021 fence). Vehicles SPDR-012…018B, 021…024 | **RETIRED — CHARACTERISED, NOT TRADABLE (2026-08-07, operator-signed).** Structure measured at power on both universes, not merely rejected. **(1) The joint sits at net break-even and nothing clears it** — `0 of 1,413` powered crypto cells, `0 of 315` powered cTrader cells, with **91% (crypto) to 96% (cTrader) of the distance being COST, not rate**. Crypto `p` 0.3887 vs `p_be_net` 0.4992 (`edge` −0.0728); cTrader `p` 0.4868 vs `p_be` 0.4855, gross mean −0.080 bps = **0.006σ**. The identity reconciles to 1.46e-11 bps and the structure replicates **more tightly on the second universe**, which shares no instrument, venue, cost model or vendor with the first. **(2) `W/L` is not a free lever** — it is ~97% the arithmetic mirror of `p` (R² 0.9667 crypto / **0.9746** cTrader, slope 0.9656); exit geometry moves it 36–67× while `p` moves inversely and the mean does not improve; 82.8%/93% of cells are indistinguishable from the driftless mirror. The whole capture-geometry premise rested on this handle being independent. It is not. **(3) Adaptive capture geometry adds nothing** — the MOMO and MR breach screens are the same trades sign-flipped (r = −0.98, fixed baselines cancel to exactly zero symbol by symbol), so "native geometry effect" was a **direction artifact**; admission rules move shared-trade value by **exactly zero on ~2.3M paired rows**; vol-gated hold is inert (0.03–0.60× its floor, 6/6 cells), vol-gated stop distance is **worse** than a fixed one (shrinks the loss-severity effect 1.3–18×), vol-scaled trails give back more when wider, and nothing recovers after a vol-adapted stop. **(4) The one surviving lever was measured and did not clear** — vol-aware SIZE reduces drawdown depth with a consistent sign (236/236 resolving rows, 6/6 cells) but a magnitude below its own detection floor (est/MDE 0.20–0.97); SPDR-024 rebuilt the estimand specifically to see it (capital-normalised, regime-labelled, counterfactual-bearing) and its scale-channel intervals still cross zero at the governing treatment, with gate-permutation p-values frequently failing to reject exchangeability with a **random** gate. **(5) Vol state is not a selectivity filter** — `HIGH − LOW` never clears zero on mean or Sharpe at any cell's pooled level. **Booked as terminal `NOT_RESOLVABLE`, never refuted: C2 shock-MOMO** (018B's comparator is not a neutral yardstick — its own mean runs +0.97 EU → +12.05 Asia, the Asia null lies entirely above zero and is blind upward, and an independent rebuild flipped `P-MR` 0.067 → 0.826; P1 skipped by operator, no 018C) **and C3** (unpowerable in its registered form — all 1,946 unresolved cells fully levered, median 81× short, median cell needs **201 years** of 25-symbol history). C9/D3/D4 OPEN and never run; P6 (Asia magnitude × shock) an unregistered lead. **Re-opening requires a new information source** — not a new exit rule, volatility transform, or re-parameterisation of the same lattice. The binding precondition is cost: spread is uncharged programme-wide and the entire measured deficit is cost. |

### What Chapter 05 changed about the frame

Chapter 04 left the question "can an intentionally directional, risk-managed volatility exposure
clear exact intraday costs?" Chapter 05 answered the **capture** half of it and the answer is
structural rather than empirical: on this substrate the win/loss ratio and the hit rate are very
nearly the same number, so the two-dimensional search space the capture programme assumed is
approximately one-dimensional, and moving along it does not move the mean. That is not a statement
about volatility conditioning being weak — it is a statement about the geometry of the exit
problem, and it replicated on two unrelated universes.

The practical consequence for the next chapter: **do not open a family whose thesis is that a
better exit, hold, trail or size rule converts a break-even joint into a positive one.** That
class is now refuted at power. And because 91–96% of the measured gap is cost, no successor on
this substrate is evaluable at all while spread remains uncharged — the cost precondition binds
before any modelling question does.

## Selection discipline going forward

Open the next family by **screening availability first** (TRAIN-only Δ-over-matched-random,
0 slots, 0 reads), gating admission on a **multiplicity-adjusted permuted-axis null at the
realized cell count**, and letting the numbers set exploration order — explore every admitted
axis eventually, best-first. See [methodology-canon.md](methodology-canon.md).
