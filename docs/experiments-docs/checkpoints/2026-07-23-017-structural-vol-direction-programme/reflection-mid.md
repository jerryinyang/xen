# Checkpoint 017 — Mid-checkpoint Reflection C

- **Date:** 2026-07-23
- **Family:** `CF-VOLDIR-001` (status remains `REGISTERED` — no family action here)
- **Authority:** RAW §3C; checkpoint-017 §5 Step C; chapter-06 governance
- **Inputs (binding, not re-run):**
  - `python/experiments/SPDR-012/analysis.md` §0 arm hand-off + reliability detail
  - `python/experiments/SPDR-013/analysis.md` §0–§10 expectancy + MFE + ZZ forecast
- **Status:** **OPERATOR DECISION RECORDED 2026-07-23** — O3 + Decision **A** (014 = Group 1 first; design 015/016 now)
- **Sequence SoT (100% compliance):** `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`
  — binding substance for SPDR-014/015/016/017; designs may narrow, not thin/contradict

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every money figure understates true cost; no fully-net / tradable / deployable claim
```

---

## 1. Evidence digest

### 1.1 SPDR-012 — volatility (HYP-A)

| Claim | Observation | Carry to C/D |
|---|---|---|
| **Reliable conditioner** | Range-based **vol level** on **H1/H4** — V-LEVEL IC ~0.34 (H1) / ~0.30 (H4) CONFIRM; Parkinson/GK beat close-to-close by ~+0.11 IC | **Keep** as primary SPDR-014 gate |
| **Persistence** | Multi-bar level persists; single-bar shock dies in ~0.4 bars; HAR weakest, collapses at D1 | Condition on **level**, not last-bar shock |
| **Simple model enough** | EWMA ≈ OLS ≈ ridge on V-LEVEL | Freeze **causal range-EWMA / level rank** — no fitted zoo |
| **Regime** | Markov HIGH−LOW gap ~+17 bps H1, ~93% sticky; usable binary flag, H1 only vs design bar | **Optional** secondary flag |
| **HMM** | Mis-named: shock detector (AUC 0.95–0.98 vs last return), ~2-bar life, mostly UNPOWERED | **Do not** use as slow regime |
| **Clock / XS / D1** | V-CLOCK null; V-XS weakest; D1 close-to-close within-month **backwards** (−0.13); D1 needs range measure | **Drop** calendar, XS primary, D1 cc-RV reliance |
| **Within-day skill** | After stripping between-month level: within-day IC ≈ 0 | No hour-resolution vol edge |
| **PASS/STOP** | AMENDMENT-T2: 012 makes **no** machine PASS/STOP | **This reflection owns the call** |

**A-call (this reflection’s recommended read):** vol is **reliable enough** to open a *vol-conditioned extraction* branch on H1/H4 range **level** — not “vol predicts the next hour’s path,” and not a free pass for signed direction.

### 1.2 SPDR-013 — direction expectancy (HYP-B)

| Claim | Observation | Carry to C/D |
|---|---|---|
| **Signed net** | **0 / 2940** cells SUPPORTED; net ≈ −9…−17 bps ≈ partial cost floor (~13.5) | Signed product **not adequate** for combination |
| **Sign timing** | Side-derangement: live ~50th %ile H1; **below** null on M15 | No net sign-timing edge |
| **Gross** | H1 trend arms gross ~breakeven to thin +ve (SMA25 off +5.1, D-ZZ +4.9); dies DESIGN→CONFIRM | Not a cost-surviving signed base |
| **ZZ vs SMA** | Median Δ ≈ 0 bps | Structure does not beat dumb benchmark on expectancy |
| **Capture shape** | Low `p_right`, large avail-when-right, smaller damage-when-wrong (TF shape present) | Geometry shape exists; **not** sufficient with dead sign |
| **Exit modes (A3)** | `combined ≈ signalflip` on net; stop/trail/time **100% UNPOWERED** (degenerate n / fat tails) | Do not re-read unpowered exits as expectancy; SPDR-014 must pre-power exit arms |
| **Mean vs median (E1)** | Mean propped by rare winners; median much worse (e.g. −2 vs −47) | Report **mean and median**; bands stay mean-driven with fat-tail disclosure |
| **MFE give-back** | Reached MFE then give-back 60–280 bps (worst on ZZ structural leg) | Looks like geometry failure **alone** |
| **MFE ambient** | signal horizon-MFE ÷ random-timing MFE ≈ **1.0** every arm | Favourable excursion is **ambient vol**, not signal-selected — **decisive** |
| **ZZ magnitude forecast** | OOS IC **0.34–0.46** (ridge ≥ AR1; M15 > H1; all 25 symbols) | **Only clean powered positive** — direction-agnostic |
| **ZZ path_noise forecast** | IC ≈ 0 | Do not use path_noise head as gate |

**B-call (this reflection’s recommended read):** signed direction is **not adequate** for a signed vol×direction product. Ambient magnitude + 012 vol level + ZZ mag forecast point to **direction-agnostic** extraction (RAW §3C / §5.2 conditional), not exit rescue of sign.

### 1.3 Joint facts (do not thin)

1. **Vol level real; sign skill not.**  
2. **Availability is ambient** — redefining signed exits lifts signal and random together.  
3. **ZZ next-swing magnitude is a separate positive** — when/how large, not which way.  
4. **Integrity:** both screens PASS integrity self-checks (012 causality on construction + re-derivation; 013 tripwire informative per T1/DEV-1).

---

## 2. Diagnosis framing (RAW language)

| Framing | Applies? | Why |
|---|---|---|
| **Signed-direction failure** | **Yes — primary** | Expectancy ≤ 0 under partial cost; no derangement edge; ZZ ≈ SMA; 0 SUPPORTED |
| **Capture geometry (Mode B alone)** | **Secondary / misleading if isolated** | Give-back is real, but MFE ÷ random ≈ 1 → not “directional residual squandered by exit” |
| **Compatibility / regime misalignment** | **Not the binding diagnosis for signed combo** | Would require both A and B *adequate in isolation* then failing together. B is not adequate in isolation |
| **Vol reliability stop** | **No** (for H1/H4 range level) | A supports a *vol-conditioned* path; fails only for hour skill / D1-cc / calendar / XS-primary / HMM-as-regime |
| **Stop the combination path entirely** | **Optional operator park** | Justified if operator declines to spend SPDR-014 on DA extraction; **not** forced by A failure |

**Programme state after A+B:**

```text
A (vol level H1/H4 range):  ADEQUATE for conditioning
B (signed direction):       NOT ADEQUATE for signed product
→ Default signed vol×direction: CLOSED by evidence
→ RAW conditional branch: direction-agnostic extraction IF risk-managed AND operator authorises
```

Per family contract §3: *“B expectancy ≤ 0 → no signed combination; direction-agnostic only if A (and optional ZigZag magnitude) supports it and operator authorises at C.”*  
A and ZZ magnitude **do** support that branch. Operator still decides spend vs park.

---

## 3. Options (consequences + recommendation)

| Option | What it freezes for Step D | One-line consequence |
|---|---|---|
| **O1 — STOP / park** | No SPDR-014 run; terminal structural package draft at retrospective | Saves a screen; leaves ambient-mag + vol-level residue untested as extraction |
| **O2 — Signed vol×direction** | HIGH vol × SMA/ZZ signed policy | **Not justified** by 013; re-spends on ambient MFE + cost-fatal sign |
| **O3 — Direction-agnostic extraction** | Vol (and/or ZZ mag) conditions **both-side / straddle-class / mag-timed** harvest; risk-managed exits | Tests the only path RAW still allows after B fail; can still die with clear diagnosis |
| **O4 — Hybrid staged** | Primary = O3; optional diagnostic signed×vol cell **report-only** (not a PASS path) | Confirms signed still dead under HIGH vol (compatibility check) without reopening O2 as product |

### Recommendation (marked)

**→ O3, with O4’s diagnostic cell allowed as disclosure-only.**

**Why:**  
- Evidence closed O2.  
- O1 parks without testing the residual RAW explicitly reserved.  
- O3 is the RAW-authorised branch: A supports + ZZ mag supports + ambient MFE = magnitude/vol harvest question.  
- O4 diagnostic is cheap insurance against “maybe sign works only in HIGH vol” — **not** a signed combination claim.

**Not recommended:** O2 as product.  
**Do not reopen:** CF-VOLCONV-001 / confirmed range-break primary direction.

---

## 4. Operator decision block

```
OPERATOR GATE — Reflection C (RECORDED 2026-07-23)
  [x] APPROVE O3 (direction-agnostic only; signed product closed)
  [x] Decision A — SPDR-014 = Group 1 (zone/event/MOMO-MR) first
  [x] Design + register SPDR-015 (Group 2) and SPDR-016 (Group 3) now
  [x] AMENDMENT-S1 — per-symbol sufficiency; multi-symbol = credibility only
  [ ] STOP / park (O1) — not chosen
  Sequence brief: .ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md

  Operator: signed in-session 2026-07-23
```

**Design freeze:** COMPLETE for SPDR-014/015/016/017.  
**Execution:** per operator gate each SPDR. Family status: **no change** (`REGISTERED`). No XENA from design alone.

| ID | Group | Design path | Start gate |
|---|---|---|---|
| SPDR-014 | 1 zone/event | `python/experiments/SPDR-014/design.md` | execution authority |
| SPDR-015 | 2 conditioners | `python/experiments/SPDR-015/design.md` | execution authority (order flexible) |
| SPDR-016 | 3a refine 014 residual | `python/experiments/SPDR-016/design.md` | **014 residual pin** + execution authority |
| SPDR-017 | 3b independent #3 mispricing | `python/experiments/SPDR-017/design.md` | execution authority only (**not** 014-gated) |

---

## 5. SPDR-014 hypothesis freeze draft (what D tests / must not re-open)

### 5.1 One question (SPDR-014 Group 1 — frozen)

> Given a horizon band from proven absolute-vol / ZZ-magnitude forecasts, does price breach that
> band at a non-ambient rate, and after breach does the path continue (MOMO) or revert (MR) with
> a conditional residual ≠ random — without assuming either?

SPDR-015/016 questions: see sequence brief §4 and each `design.md` §1.

### 5.2 Mechanism sketch (SPDR-014; detail in design.md)

```text
MECHANISM: Range-based vol level and/or ZZ magnitude forecast define a likelihood zone.
  Breach = makeshift mispricing event. Post-event MOMO vs MR is measured, not assumed.
  Direction-aware extraction only after residual is named; not signed SMA/ZZ product.
DERIVED: estimand=event rates + post-event residual + optional partial_net under residual policy;
  null=uncond-σ band + time-shuffled events; horizon=H and post-hold h on H1.
```

### 5.3 Frozen ingredients from observations (not pre-hope)

| Ingredient | Source | Role in D |
|---|---|---|
| Parkinson / GK **range level** on **H1** (H4 co-report) | 012 Keep | Primary HIGH/LOW conditioner |
| Causal level EWMA / expanding percentile | 012 “simple enough” | Gate construction |
| Optional Markov binary HIGH (H1) | 012 V-REGIME | Secondary gate sensitivity |
| ZZ next-swing **magnitude** forecast | 013 only powered + | Mag-gate / sizing feature |
| Ambient MFE fact | 013 §5 | Justifies DA, forbids signed rescue narrative |
| Drop list | 012 | No calendar, no XS primary, no D1-cc, no HMM-as-regime, no hour skill claim |

### 5.4 Explicitly out of SPDR-014 scope

- Signed vol×direction as **product** (O2) — closed unless operator amends  
- Range-break primary direction / CF-VOLCONV re-open  
- Win-rate as primary metric  
- XENA / Nautilus graduation until D operator gate  
- Historical TEST / holdout  
- Re-running 012/013  
- Monthly capped inventory grid re-parameterisation of CF-VOLHARV-001 (P-12)  
- Assuming MOMO or MR without characterisation  

### 5.5 If D1 (014) fails — diagnosis labels (predeclared)

| Label | When |
|---|---|
| **No event structure** | Breach rate / residual ≈ unconditional-σ and time-shuffle nulls |
| **Geometry** | Residual exists in path but risk rules + partial cost kill money cells |
| **Compatibility** | Residual only in empty/rare strata; gates misalign with harvestable path |
| **Substrate dead for extraction** | MOMO≈MR≈ambient under all primary cells |
| **Not used:** “markets empty” without one of the above |

### 5.6 Implementation pointers

| ID | Design |
|---|---|
| SPDR-014 | `python/experiments/SPDR-014/design.md` |
| SPDR-015 | `python/experiments/SPDR-015/design.md` |
| SPDR-016 | `python/experiments/SPDR-016/design.md` (014-gated refine) |
| SPDR-017 | `python/experiments/SPDR-017/design.md` (operator original #3) |
| Sequence SoT | `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md` |

Do not re-decide C inside implementation — only operator amend.

---

## 6. Checkpoint status after C (procedural)

| Step | Status |
|---|---|
| A SPDR-012 | COMPLETE |
| B SPDR-013 | COMPLETE |
| C Reflection | **SIGNED — O3 + Decision A** |
| D1 SPDR-014 design | **COMPLETE** (Group 1); run unauthorised |
| D2 SPDR-015 design | **COMPLETE** (Group 2); run unauthorised |
| D3a SPDR-016 design | **COMPLETE** (3a refine); start-gated on 014 residual |
| D3b SPDR-017 design | **COMPLETE** (3b independent #3); not 014-gated |
| E XENA-VOLDIR-001 | RESERVED until a graduated base + separate authority |

**Next:** operator execution authority for **SPDR-014** (first). 015 flexible. 016 only after 014 residual pin.
