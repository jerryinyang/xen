# Checkpoint 017 — Retrospective (CLOSED)

- **Opened:** 2026-07-23
- **Closed:** 2026-07-25 — operator-signed
- **Family:** `CF-VOLDIR-001` — remains **`REGISTERED`** (no status change; see §6)
- **End-state reached:** **neither of the two frozen end-states cleanly** — see §5. Closed as
  **STRUCTURAL PACKAGE DELIVERED / EXTRACTION UNRESOLVED-AT-POWER**, with the residue routed to
  checkpoint-018 rather than parked.
- **Reads:** TRAIN only. **0 counted TEST reads.** Global holdout sealed throughout.
- **Successor:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md`
- **Successor SoT:** `.ignore/what-next/alts/opportunity.md`

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every money figure in this checkpoint understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. What the checkpoint asked

Procedurally separate the claims — (A) how reliably volatility is modelled, (B) whether fast
direction models have positive expectancy in bps, (C) operator reflection, (D) extraction from
combination or authorised direction-agnostic structure — so that failure is **diagnosable**
(volatility / direction / capture geometry / compatibility) rather than vague.

That question was answered. The checkpoint delivered its diagnostic product.

---

## 2. Execution record

| Item | Vehicle | Outcome |
|---|---|---|
| Step A — vol characterisation | `SPDR-012` | **COMPLETE** — H1/H4 range-based vol level reliable (rank IC 0.338 / 0.301); no within-day skill; D1 close-to-close backwards |
| Step B — direction expectancy | `SPDR-013` | **COMPLETE** — signed direction not adequate (0/2940 SUPPORTED, net ≈ cost floor); ZZ next-swing magnitude IC 0.34–0.46 |
| Step C — mid reflection | *(no emission)* | **SIGNED 2026-07-23** — O3 (direction-agnostic only) + Decision A |
| Step D1 — zone / event / MOMO–MR | `SPDR-014` | **SCREEN COMPLETE** — INCONCLUSIVE / UNPOWERED_NOT_NULL (B-5); `residual_status=NONE`; 0/927 powered cells |
| Step D2 — conditioner science | `SPDR-015` | **SCREEN COMPLETE — WORTH_EXPLORING (per-arm)** — swing-size gate + vol level-state labels + multi-bar gate route on |
| Step D3a — refine 014 residual | `SPDR-016` | **CLOSED — SUPERSEDED, NEVER RUN** (§4) |
| Step D3b — independent mispricing | `SPDR-017` | **CLOSED — NOT_WORTH** — model IC ≈ 0; DERIVED layer inert; destroys indistinguishable; M-ZONE ≤ Z-VOL |
| Step E — XENA | `XENA-VOLDIR-001` | **RESERVED, never opened** — no graduated base |

Integrity: every screen passed its own hard self-check (golden traces, TRAIN fence, universe pin,
causal lag, derangement fixed-point-free). No screen was adjudicated on a value gate.

---

## 3. What the checkpoint established

### 3.1 Powered positives (carry forward)

| Result | Magnitude | Source |
|---|---|---|
| Range-based vol **level** is reliable on H1/H4 | rank IC 0.338 / 0.301, 15/15 cells CI-low > 0 | SPDR-012 V-LEVEL |
| Range measures beat close-to-close | +0.09…+0.13 IC on D1; level intraday | SPDR-012 V-MEASURE |
| Next-swing **magnitude** is forecastable | OOS IC 0.34–0.46, all 25 symbols | SPDR-013 §7 |
| Ordinal swing-size gate **T-GT-CUR** | hit 0.683 vs 0.475 base (+0.21), IC 0.37, 21/21 coins × 3 models | SPDR-015 arm 2b |
| Multi-bar vol-state gate **R-MARKOV k=4/12** | ΔBrier −0.025 / −0.114, 16/16 coins, CI excl 0 | SPDR-015 arm 2a |
| HMM HIGH/LOW as a size **label** | next-\|oo\| gap +35 bps vs +16 bps | SPDR-015 |

### 3.2 Measured nulls (closed; do not re-spend)

Unconditional / trend direction on net (0/2940 SUPPORTED, no sign-timing edge, ZigZag ≈ SMA);
availability is ambient (`sig_over_rand` 0.95–1.03); calendar/session features; cross-sectional rank
as a primary lever; close-to-close RV at D1; HAR; k=1 next-bar vol forecasting as a gate; R-HMM-RV
as a forecaster; path-noise forecasting; the DERIVED error-dynamics feature layer; model-predicted-
price mispricing zones (M-ZONE ≤ Z-VOL, model IC ≈ 0).

### 3.3 Unpowered-but-coherent residue (routed, not parked)

| Lead | Magnitude | n | Source |
|---|---|---:|---|
| Shock-conditioned MOMO | +71.6 mean / +29.3 median bps, pooled CI [+11.9, +134.9] | 235 | SPDR-014 §6 |
| `L→H` vol-flip → MOMO | `p_momo` 0.55–0.58, median ~+40 bps, coherent across k=2 and k=3 | 33–210 | SPDR-014 §4.4 |
| E-TOUCH / E-CLOSE asymmetry | ~18–20 bps split by breach type | — | SPDR-014 §4.3 |

**B-5 holds:** these are power statements, not negatives. They are the sole reason checkpoint-018
exists.

---

## 4. SPDR-016 disposition — CLOSED, SUPERSEDED, NEVER RUN

`SPDR-016` was designed as Group 3a (refine the named 014 residual with error-dynamics features) and
was **OPENED by signed operator override** on 2026-07-24 — explicitly on 014's coherent SUGGESTIVE
leads, **not** on a powered residual (`residual_status=NONE`, 0 powered cells). It was never
authorised for execution and never run. **0 reads consumed.**

**Closed as SUPERSEDED for two recorded reasons:**

1. **Its premise was independently measured inert.** `SPDR-017` tested the same error-dynamics
   ("DERIVED") feature layer against the proven-feature baseline and found it **fails to lift**
   (A1 − A0 median **−5.8 bps**; only 5/16 symbols improve). The feature class 016 was built on
   carries no information on this substrate.
2. **Its actual target — powering the 014 leads — is carried forward with a strictly better
   design.** `SPDR-018` estimates the same leads as **un-nested bar-level conditioners**, which
   raises n by ~60–100× and reaches MDE ≤ 10 bps by construction; 016's event-nested framing needed
   ~13.6× more events than exist in the `LH` stratum and was probably unreachable even pooled.

**Nothing is discarded:** the override's intent (pursue the SUGGESTIVE leads) is preserved verbatim
as `SPDR-018`'s declared lead list. This is a supersede-and-retain, not an erasure — the 016 design
stays on disk with this disposition recorded against it.

---

## 5. Why neither frozen end-state was reached cleanly

The checkpoint froze two end-states: a **terminal structural package**, or a **graduated base for
XENA**. Neither is honestly claimable:

- **Not a graduated base.** No cost-surviving extraction object emerged. Every money read is
  negative on partial cost; `SPDR-014` gross ≈ 0; `SPDR-017` gross ≈ 0.
- **Not a terminal package either.** A terminal package requires the extraction failure to be
  *established*. It was not — `SPDR-014` produced **0 powered cells of 927** with MDE 20 / 172 / 796
  bps against a ≤10 bps floor. Under B-5 that is **unpowered, not negative**. Declaring the branch
  dead on an unpowered screen would be exactly the error the lane forbids.

**Closed as `STRUCTURAL PACKAGE DELIVERED / EXTRACTION UNRESOLVED-AT-POWER`.** The diagnostic
product (which volatility levers survive; that unconditional direction is dead; that availability is
ambient) is complete and durable. The extraction question is unresolved **for a measurable reason**
— insufficient power at the cell resolution used — and that reason has a design fix, which is the
successor checkpoint.

---

## 6. Family disposition

`CF-VOLDIR-001` remains **`REGISTERED`**. No status change.

- Nothing in this checkpoint retires the family: its Step A claim (volatility is a reliable object)
  was **confirmed**, and its Step D claim is unpowered rather than refuted.
- Nothing in this checkpoint graduates it: no base cleared a cost floor, `XENA-VOLDIR-001` stays
  RESERVED and unopened.
- The programme's own stop rules are respected — the signed vol×direction product stays **closed**
  (SPDR-013 evidence), and checkpoint-018 does not reopen it.

---

## 7. Lessons (candidates for the knowledge base)

1. **Power is a design parameter, not a data property.** SPDR-014's leads were invisible only
   because they were measured inside a 6,000-cell event grid. The same objects measured as
   bar-level conditioners are powered by construction. **Before declaring an object unpowered, ask
   whether the conditioning grammar — not the data — is what destroyed n.**
2. **A conditioner is not an event.** Nesting a bar-level conditioner inside an event definition
   multiplies the multiplicity cost and divides the sample, for no gain when the conditioner does
   not depend on the event.
3. **Exit/sizing optimisation on a driftless signed path is analytically zero-expectancy** — Xen has
   now booked this twice (`CF-VOLHARV-001/HYP-001` analytically, `SPDR-013` empirically). Any future
   capture-geometry proposal must name its signed term **before** the exit design, or it is refused
   by construction.
4. **An operator override is not evidence.** SPDR-016 was opened by override on coherent leads and
   closed unrun when an independent screen measured its feature layer inert. The override was
   correctly attributed at the time (`016_start_basis=OPERATOR_OVERRIDE`, `residual_status` left at
   NONE), which is exactly why closing it cost nothing.
5. **Un-nesting beats pooling.** Faced with an unpowered stratum, the first lever is not "add more
   symbols" — it is "remove the conditioning that is not load-bearing," then normalise variance,
   then pool.

---

## 8. Ledger

| Field | Value |
|---|---|
| Counted TEST reads | **0** |
| Holdout contact | **none** (Bybit global holdout sealed; cTrader holdout never opened) |
| Multiplicity slots consumed | **0** |
| Family status change | **none** (`REGISTERED` → `REGISTERED`) |
| XENA opened | **no** (`XENA-VOLDIR-001` RESERVED) |
| Screens completed | SPDR-012, 013, 014, 015, 017 |
| Screens closed unrun | SPDR-016 (SUPERSEDED, §4) |
| Infrastructure delivered | INFR-021 cTrader catalog (EURUSD / XAUUSD / USTEC) |

---

## 9. Route out

Checkpoint-018 (`2026-07-25-018-trade-opportunity-capture-geometry`) opens as an **extension**, not
a replacement. It inherits this checkpoint's powered predictors as ready inputs, its measured nulls
as refusals, and its unpowered residue as its opening gate.

Governing SoT: `.ignore/what-next/alts/opportunity.md`.

The binding premise carried across the boundary:

> **Unconditional direction is dead. Conditional direction is unpowered, not refuted. Volatility is
> a multiplier on a direction term, never a substitute for it.**
