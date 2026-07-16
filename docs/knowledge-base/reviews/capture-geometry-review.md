# Capture Geometry — Cross-Chapter Analytic Extraction

**Purpose.** Independent-review brief on every modality and mechanism the programme has used to
attack **"availability exists, but cannot be captured properly"** — the highest-frequency
disqualifier of strategies across Chapters 01–03.

**Status.** Extraction only. No new claims; no new experiments. Sources: knowledge-base canon,
signal-registry family cards, chapter archive family indexes, and phase retrospectives.

**Reading map.**

| Need | Where |
|---|---|
| This extraction (modalities + observations) | **this file** |
| Family dispositions | [families-explored.md](../families-explored.md) |
| Dead ends (do-not-re-run) | [pitfalls-ledger.md](../pitfalls-ledger.md) |
| Lessons with mechanism | [lessons-and-amendments.md](../lessons-and-amendments.md) |
| Methods that earned keep | [methodology-canon.md](../methodology-canon.md) |

---

## 1. Problem statement — what "capture geometry" means here

### 1.1 The diagnosis arc (how the problem was named)

| Stage | Belief | Evidence that moved it |
|---|---|---|
| Early AVWAP (Phases 004–009) | Edge is weak / holdout inconclusive / maybe wrong params | Gross bounce real; net cost-dominated; EURUSD-4h TEST-pass non-upgradable |
| Phase 010–011 exits | Exit choice can rescue absolute net | EXIT_FLAT; per-instrument exit training empty membership |
| Phase 013 (EXP-047) | "Move is too small" | **Refuted.** Lifetime median MFE ≈ 5–9× the frozen cost floor in 51/51 cells; event MFE ≈ matched-control MFE |
| Naming | Binding wall = **capture geometry** (peak → realizable net capture), not move availability | Phase 013 retrospective; CF-CAPGEO-001 thesis |
| Phase 018 (EXP-081/084) | Capture geometry is *the* lever | **Exit-invariant NOT_CONFIRM.** Gross favourable availability ≈ random; 0/11 exit arms OOS CI_low > 0 |
| Re-framing | For single-series directional price geometry, the binding wall is **upstream** (no signal-conditional move beyond random) | P-01 / P-02; availability-first rule |
| Chapter 02 MR / harvest | Same abstract wall under new vehicles | Cost/capture veto, entry-seam mismatch, structure failure, passive-limit print artifact |
| Chapter 03 XENA | Cost-fatal reversion print; filters cannot manufacture capture | P-10 fifth vehicle |

**One-sentence definition used in this programme:**

> Capture geometry = the conversion of a **peak or path-available favourable excursion** into a
> **deterministic, causal, cost-surviving exit P&L** — including barrier placement, time caps,
> partials, trails, proactive limits, and position-management — such that the conversion is not
> an artifact of look-ahead, entry-seam mismatch, or selection-region overlap.

### 1.2 Three failure modes that look the same from the outside

Independent reviewers should not collapse these:

| Failure mode | Symptom | Canonical evidence | Implication |
|---|---|---|---|
| **A. No availability** | Signal-conditional MFE/MAE ≈ matched random | EXP-047, EXP-081 | Exit work cannot create edge (P-02) |
| **B. Availability without capturable residue** | Lifetime MFE ≫ cost, but every exit nets ≤ 0 | AVWAP Phases 010–011; CF-MR-003 | Cost/horizon geometry, not creativity, is binding |
| **C. Capture that is not the claimed mechanism** | Gross/net positive under a defect or print artifact | L-01 EXIT-RCT look-ahead; XENA-003 passive-limit print; CF-MR-004 limit-touch vs confirmed-breach | Falsify execution/entry-seam before claiming exit success |

Mode A was diagnosed *late* (after building families). Mode B drove the CAPGEO family.
Mode C produced the programme's only false `DEPLOYABLE_CONFIRMED` and several chapter-02 confounds.

---

## 2. Taxonomy of modalities explored

Every capture attempt falls into one or more of these modality classes.

### 2.1 Barrier / target geometry (symmetric and asymmetric)

| Modality | What it does | Where tested |
|---|---|---|
| **Fixed MAD band-target + trend-change (BTC)** | Favourable/adverse MAD bands frozen at entry; opposite-regime close ends the move | CF-AVWAP-001 baseline (EXP-022/028/029) |
| **Fixed-horizon (FH)** | Exit at bar close after H domain bars | AVWAP `/EXIT-FH` (EXP-033/037/038/039/045); CAPGEO `AVWAP-FH` |
| **RR fixed favourable/adverse** | Risk-reward multiples (1.5 / 2 / 3, etc.) | CAPGEO `/EXIT-RR`; harami adverse RR variants |
| **Triple-barrier (fav + adv + time)** | First-hit of three barriers; path-ordered fills | Harami Phases 014–015; CAPGEO derived D1/D2/D3 |
| **Benchmark 3-barrier** | Fav 50% of move, adv 1:1, adaptive time-cap | Harami default geometry |
| **Favourable-target variants** | `/VPTARGET` (POC / near / far), `/MAGTARGET` (0.5×/1.0× × W=5/20), 50% benchmark | EXP-056, EXP-064 |
| **Adverse-target variants** | 1:1 bench, `/ADV-EXTREME` (rr1 / raw), `/ADV-NONE` (unbounded) | EXP-057, EXP-063 |
| **Third-barrier variants** | Adaptive cap floors T12/T24/T48, `/THIRD-EVENT` (next segment confirm) | EXP-058, EXP-065 |
| **Data-derived triple-barrier** | Barriers = measured quantiles of TRAIN MFE/MAE/TTP (freeze the rule) | CAPGEO EXP-082 (`D1`/`D2`/`D3`) |
| **Symmetric two-barrier race** | Inward vs outward barrier race (availability, not P&L) | CF-MR-004 EXP-014b |

### 2.2 Trailing / structure / pattern exits

| Modality | What it does | Where tested |
|---|---|---|
| **HA harami size exhaustion (E1)** | Exit on HA harami size pattern | AVWAP EXP-039 |
| **HA trailing reference (E2)** | Exit when real close crosses HA high/low trail | AVWAP EXP-039 |
| **Last-X high/low trailing (E3)** | Exit when close crosses prior-X extreme | AVWAP EXP-039 |
| **Adverse-band stop (E4)** | Opposite MAD band as stop | AVWAP EXP-039 |
| **Target-conditional time-stop (E5)** | BTC target + time-stop hybridization | AVWAP EXP-039 |
| **Structure trailing (ZigZag ratchet)** | Monotone trail on secondary ZigZag | Harami `/EXIT-TRAIL-STRUCT` EXP-059/066 |
| **Uncapped structure trailing** | Trail without favourable cap | EXP-059B |
| **Market-structure / price trailing (CAPGEO)** | `/EXIT-TRAIL` benchmark family | Phase 018 screen |
| **Volume-profile targets** | POC / value-area (`TickVolume` proxy) | CAPGEO `/EXIT-VP` |

### 2.3 Partial / scaled position management

| Modality | What it does | Where tested |
|---|---|---|
| **Even-thirds favourable scaling (PARTIAL-V2A)** | Legs at {1/3, 2/3, 1}× fav distance + shared stop | Harami champion; CAPGEO reference arm |
| **PARTIAL V1 / V2B / V2C** | Alternate leg fractions / event-bound third leg | EXP-059, EXP-066 |
| **COMBINED partial + trail** | Scaled fav + structure trail | EXP-059, EXP-066 |
| **V2A × ADV-NONE** | Partials without adverse stop (cap is sole stop-out) | Harami N-V2A×ADV-NONE; CAPGEO substrate/arm |
| **Ladder / scale-in (entry-side)** | Deepening adds, shared frozen exit family | CF-MR-005 (capture *of* a ladder object) |

### 2.4 Proactive reversion targets (MR-native capture)

| Modality | What it does | Where tested |
|---|---|---|
| **EXIT-RCT reversion-completion target** | Closed-form RSI₂→50 completion price `P*`; proactive limit; 1m intrabar fill; trailing as Wilder state updates | CF-MR-001 Phase 021; CF-MR-002 causal re-run |
| **EXIT-ERT equilibrium-return target** | Price returns to equilibrium-mean (e.g. EMA); proactive trailing limit | CF-MR-001 EXP-091 (failed screen) |
| **Form-1 event-reversion exit** | Exit when *moving* anchor series recomputes back to mean | CF-MR-004 (proposal-named; dropped then restored) |
| **Form-2 refreshing anchor-mean limit** | Favourable limit at current anchor mean (must refresh) | CF-MR-004 EXP-014 |
| **Form-2 frozen-at-entry TP** | TP fixed at entry anchor mean (peer-side reversion never exits) | EXP-013 confound |
| **Limit-at-anchor fade entry + mean exit** | Live limit entry at band edge; exit at mean | CF-MR-003 concretization |
| **Symmetric barrier TP/SL matching measured object** | Frozen TP + outward SL + time-stop | CF-MR-004 EXP-014c E1–E3 |

### 2.5 Horizon / hold-period capture (non-barrier)

| Modality | What it does | Where tested |
|---|---|---|
| **Fixed-horizon signed reaction** | Direction-signed return at H ∈ {1,3,6} | AVWAP EXP-021 |
| **Bounded-hold decomposition** | Always-on vs event-hold diagnostics | EXP-024 |
| **Hold-period OR profit exit (float ATR)** | Close if profit ≥ 0.5 × *current* HTF ATR | CF-MTFCTX-001 CTRL-03 naive reversion |
| **Monthly-anchored capped grid / rebalance** | Inventory harvest structures | CF-VOLHARV-001 |

### 2.6 Sizing as a pseudo-capture lever (tested; not capture)

| Modality | Observation |
|---|---|
| **Volatility-adjusted sizing (`SIZE-VOLADJ`)** | Near-global rescale when stop ≈ constant ATR quantile; amplifies edge, cannot create one (Phase 018 lesson 3) |
| **ATR-normalised returns / fixed-risk** | Already the evaluation unit; not an independent capture fix |

### 2.7 Modalities registered but not productively binding

| Item | Status |
|---|---|
| HA pattern exits as standalone strategy overlays | Screened FLAT on AVWAP (E1/E2) |
| Tick-volume-weighted construction | Inert (P-07); VP targets inherit proxy caveat |
| `/MTF`, `/VOLREGIME` CAPGEO branches | Deferred; never became binding levers |
| HTF-DI T2 exit tier | **Not scoped** — no T1 survivors; analyst: trail cannot manufacture 10× magnitude gap |

---

## 3. Extraction by research arc

Each subsection: **intent → mechanisms tried → observations → disposition**.

---

### 3.1 CF-AVWAP-001 — "Move available; exit cannot net it"

**Arc.** Phases 004–013 · EXP-020–047 · CLOSED for in-family phases.

#### Mechanisms tried

1. **BTC lifetime exit** — MAD band fav/adv + trend-change completion (baseline).
2. **Fixed-horizon exit family** — H-grid, TRAIN-selected H\* (4h H\*=12 standing package).
3. **Entry-vs-exit isolation** (EXP-031/033) — decompose matched-control excess into entry timing vs exit rule.
4. **Clinical conditioning** (EXP-035) — session / %completion / trailing-vol terciles as selectivity (not exit).
5. **Structurally distinct exit families E1–E5** (EXP-039) — HA harami, HA trail, Last-X trail, adverse-band stop, target-conditional time-stop vs R-FH / R-BTC references.
6. **Per-instrument exit training** (EXP-045) — FH family + MAD-band family grids on 37 calibrated cells × 17 instruments.
7. **Anchor move-size diagnostic** (EXP-047) — does a ratified prominence anchor unlock larger moves?

#### Key observations

| Observation | Detail |
|---|---|
| Gross edge real | Bounce reaction +3.8 / +9.1 / +37.6 bps (domains); lifetime favourable-rate advantage 22–26 pp; 31/37 cells gross-proxy positive after per-instrument training |
| Net cost-dominated | EXP-030 net EVIDENCE_AGAINST under CONSERVATIVE RT; EXP-045 net medians −5…−7 bps at every grid point |
| Exit does not raise gross | Training reallocates the same few-bps gross; cannot lift it over the cost floor |
| EXIT_FLAT (Phase 010) | 0/10 exit×domain cells beat the FH reference; E2 (HA trail) within ~0.5 SE of FH on 4h n=86 — power wall, not FH optimality proof |
| Horizon-dependent exit value | EXP-031: BTC exit is loss-cutter at H=1 (EXIT_DOMINANT) and trend-truncator at H=6 (ENTRY_DOMINANT) — unresolved isolation |
| FH recovers some capture | EXP-037 EURUSD-4h: FH recovers ~+16 bps vs BTC on same TEST events — capture efficiency is a real lever *on that cell* but non-upgradable after holdout INCONCLUSIVE |
| Selectivity empty | EXP-035: 0 G1-qualified conditioning dimensions |
| **Move availability not scarce** | EXP-047: median lifetime peak MFE ≈ 5–9× cost floor in **all 51 cells**, both anchors; event MFE ≈ control MFE — bounce trigger does not access privileged move sizes |
| Anchor flat | Ratified k=1.0 ATR-prominence anchor collapses to running extreme (coincidence 94.6–98.5%) |

#### Disposition

**CLOSED.** Capture geometry named as the unsolved problem; family exits/entry/anchor all
CLOSED-MEASURED. EURUSD holdout permanently contaminated (EXP-032). Pitfall **P-03**.

---

### 3.2 CF-HA-HARAMI-001 — "Real median edge; mean killed by capture shape"

**Arc.** Phases 014–016 · EXP-048–075 · CLOSED at G-016.

#### Mechanisms tried (full barrier + position-management surface)

**014-A readiness / unconditioned (caution: many reads had `/STRONG` OFF):**

| EXP | Mechanism | Observation |
|---|---|---|
| EXP-049 | Benchmark 3-barrier capture rate | 99/99 constructible; **0/99 VIABLE** (r ~ 0.50 null under defaults) |
| EXP-050 | Position-in-move context | Raw haramis front-loaded, not at exhaustion |
| EXP-051–052 | Strong-move filters / confirm | `/STRONG` carves different population; `/CONFIRM` worse than DIRECT |

**014-B conditioned surface (ZigZag substrate):**

| Lever | Result |
|---|---|
| Favourable-target alts (EXP-056) | Do **not** improve |
| Adverse `/ADV-NONE` (EXP-057) | **Improves** expectancy |
| Third-barrier alts (EXP-058) | Do **not** improve |
| PARTIAL V2A (EXP-059) | **Improves** expectancy |
| Structure trail / uncapped trail (EXP-059/059B) | Do **not** improve |
| Combined champion (EXP-060) | Individually viable 69/99; beats MA baseline **0/99** |

**MA substrate (014-B gap-fill + Phase 015 full re-surface):**

| Layer | Result |
|---|---|
| Lifetime availability (EXP-055/062) | AVAILABILITY_GOOD — median MFE ~3.84 ATR (MA) vs ~1.44 ATR (ZigZag); **not signal-attributable** (ambient MA-segment property; A−RM median −0.198 ATR) |
| Adverse geometry / mean (EXP-063) | Bounded variants can show positive raw means on own terms; formal recovery-vs-NONE contrast never clears zero systematically |
| Favourable targets VP/MAG (EXP-064) | VP improvement is **substrate property** — RM null benefits equally |
| Third barrier (EXP-065) | **REFUTED** — no alt improves over floor-6 adaptive cap; replicates ZigZag EXP-058 |
| Position management (EXP-066) | **Native PARTIAL-V2A** only arm that composes three-way conjunction (21 cells / 13 instruments / all non-4h); trails fail; hybrid fails |
| Combined champion (EXP-068) | N-PARTIAL-V2A mean-positive on TRAIN co-primary path → G-015 PROCEED |
| TEST (EXP-071) | Portfolio TEST **NOT_CONFIRMED** |
| Tail / filter design (EXP-074/075) | Exhaustion-cap can cut catastrophe tail **and** strip winners — median edge and mean-killing tail share one unfilterable driver |

#### Key observations

1. **Capture surface is not empty on the right substrate** — partials and uncapped adverse moved
   expectancy; favourable-target, third-barrier, and trailing did not.
2. **Asymmetric geometry manufactures the failure shape** — capped fav + uncapped adv maximises
   median and creates fat left tail (skew gap ~1.20 ATR on MA under ADV-NONE) → mean ≈ 0.
3. **First-hit `r` is blind to partials/trails** — 014-A lesson; do not judge capture models under
   a symmetric first-hit rate when the mechanism is asymmetric.
4. **Separability failure** — lever that removes the mean obstacle (filter the catastrophic
   exhaustion tail) also removes the median edge (two-family retrospective §4.1).
5. On **fresh 5-year data** (EXP-081 later), even strong-filtered harami favourable availability
   is **below random** (17/46) — shape signature (median+/mean~0) reproduces; move-edge does not.

#### Disposition

**CLOSED / marginal.** Real median edge on old-data MA substrate; not confirmable mean / OOS.
Pitfall lineage into **P-01** (availability) and CAPGEO re-use of frozen entries.

---

### 3.3 CF-CAPGEO-001 — Exit-first family; lever exonerated

**Arc.** Phases 017–018 · EXP-076–085 · RETIRED SCREENED at G-018.

#### Design posture (unique in the programme)

- Entries **frozen** (AVWAP final; harami PARTIAL-V2A; harami V2A-ADVNONE; matched RANDOM).
- Open axis = **exit / capture geometry + sizing only**.
- Reverse-direction question: *what does realized return structure say the exit should be?*
- Pipeline: readiness → characterize → derive → screen → cost gate → one OOS confirmation.
- Pre-TEST **separability gate** (S1 ∧ S2): binding expectancy must not be the same mechanism as
  the unfilterable obstacle.

#### Mechanisms tried

**Data-derived triple-barrier (freeze the rule, EXP-082):**

| Candidate | Favourable | Adverse | Horizon |
|---|---|---|---|
| `D1-MEDIAN-CAPTURE` | `MFE_med` | `m_anti` else `MAE_q90` | `TTP_q75` |
| `D2-TAIL-ROBUST` | `MFE_med` | `m_anti` (tightened; else MAE_q90) | `TTP_q75` |
| `D3-CAPTURE-EFFICIENT` | `MFE_q40` | `m_anti` else `MAE_q90` | `TTP_med` |

**Conventional benchmark grid:** `/EXIT-RR` (1.5/2/3), `/EXIT-TRAIL`, `/EXIT-VP`,
`/EXIT-PARTIAL` (incl. PARTIAL-V2A, V2A-ADVNONE, AVWAP-FH), `/SIZE-VOLADJ`.

**Qualifier infrastructure (Phase 017):** ASS (adaptive KDE + EB shrinkage) + WF-EXPANDING —
ASS demoted **DISCOVERY_ONLY** (shape-blind to median+/minority-catastrophe; k-fragile FPR).

#### Key observations (the cleanest negative in the programme)

| EXP | Result | Mechanism lesson |
|---|---|---|
| EXP-080 | 184/192 READY; 46-cell member set | Infrastructure ok |
| EXP-081 | **Gross fav availability ≈ random** (harami 17/46 below; AVWAP 28/46 coin-flip) | **Nothing to capture** — Mode A on the frozen entries themselves under 5-year data |
| EXP-082 | 552/552 valid barriers; D1≡D2 on 184/184; `m_anti` dormant 549/552 | Continuous catastrophe tail → adverse leg falls back to ~9 ATR MAE_q90 stop **at** catastrophe edge → **trap geometry re-derived** |
| EXP-083 | 98.2% die at gross screen; data-derived D1/D2/D3 earn **no distinctive TRAIN support** | "Data-derived beats conventional" unsupported on TRAIN |
| EXP-085 | 21/26 NET_POS — all in low-n S2-DEFERRED AVWAP-4h cells; only powered S2-PASS (AUDUSD-1h harami n=988) is **NET_INCONCLUSIVE** | Pooled NET_POS masks binding stratum (L-03) |
| EXP-084 | Portfolio AVWAP-4h `NOT_CONFIRM`; **0/11 exit arms** positive OOS CI_low | Exit-invariant failure; apparent TRAIN edge = selection-region overlap reversing in fresh folds |

#### Disposition

**RETIRED.** Capture-geometry lever **exonerated** for these signals (not proven irrelevant in
general). Next family must be entry-side with real Δ-over-random first. Pitfall **P-04**.

**Programme-level reframe after Phase 018:** for single-instrument directional price-geometry
entries, "capture geometry was never the binding constraint — the entry is."

---

### 3.4 CF-MR-001 / CF-MR-002 — Proactive reversion capture; false positive then causal null

**Arc.** Phase 020–022 (MR-001) · Chapter 02 Phase 001 (MR-002 causal re-run).

#### Mechanisms tried (Phase 021 screen slate)

| Arm | Type | Screen result (EXP-091) |
|---|---|---|
| **EXIT-RCT** | Native proactive reversion-completion limit + 1m fill | **Only arm to pass** (5 cells / 5 instruments, all 1h) |
| **EXIT-ERT** | Native equilibrium-return limit | 0 cells net-clear |
| RSI-revert-on-close | Reactive domain-close when RSI₂ crosses 50 | 0 cells |
| Fixed-bar | Close at ~3-bar horizon | 0 cells |
| ATR triple-barrier | Conventional barrier | 0 cells |
| Partial / trail | Favourable partial + trail contrast | 0 cells |

Also: 4h re-screen (EXP-094) admits 6 powered cells; SEQUENCE pins 11; TEST 8/11 CONFIRM;
portfolio/holdout arc to DEPLOYABLE_CONFIRMED — **then retracted**.

#### Key observations

| Observation | Detail |
|---|---|
| Availability real (G-020) | Bare RSI-2 fade gross `MFE_med` ADMITTED; ~0.75 ATR / ~3-bar; intraday; vol-regime inert |
| Availability ≠ capturable | 15m: cost ≈ 2× gross → all net-negative; same gross ~0.28 ATR is domain-invariant |
| Proactive beats reactive (on contaminated engine) | RCT − RSI-revert Δ median +0.261 ATR, 20/20 cells — **later invalidated by look-ahead** |
| Cost geometry decides domain | 4h looks "stronger" because ATR-normalized RT fraction is smaller — not a stronger signal |
| **L-01 look-ahead** | Favourable limit rested `rct[di]` during bar `di`; live-actable is `rct[di-1]`; inflate ~+0.25 ATR/trade |
| Causalized | Net-negative **even gross** |
| CF-MR-002 faithful re-run | cTrader-primary, `rct[di-1]`: **NOT-TRADABLE 34/34**; beats naive momentum but absolute net negative |

#### Disposition

**CF-MR-001 CLOSED — REFUTED** (P-05). Availability claim (gross MFE, no RCT) stands; tradability
does not. Counted reads + holdout **spent-on-defect**. CF-MR-002 **EXONERATED / NOT-TRADABLE**.

---

### 3.5 CF-MR-003 / 004 / 005 — Same cost/capture wall under new vehicles

#### CF-MR-003 — limit-at-anchor fade

| Item | Content |
|---|---|
| Mechanism | Live limit entry at ≤t-1 \|z\|≥2 band; form-2 exit at anchor mean fixed at entry; horizon fallback |
| Availability | SCREENED-ADMIT (price returns to HTF anchor beyond dislocation-matched control) |
| Tradability | NOT-TRADABLE at 1h (unpowered) and 15m (powered 0/24 admit) |
| Observation | Moving to 15m multiplies episodes but **shrinks capturable move** vs **same** RT cost → powered null-to-negative |
| Disposition | RETIRED; re-open only with cheaper capture or lower-cost universe |

#### CF-MR-004 — cross-instrument spreads

| Item | Content |
|---|---|
| Mechanisms | Form-1 event-reversion + form-2 refreshing mean limit + horizon; E0–E3 exit decomposition; symmetric two-barrier object match |
| Confound (EXP-013) | Form-1 silently dropped; form-2 TP frozen → peer-side reversion never exits (L-14) |
| Faithful redo (EXP-014) | Exits fire; still 0/38 net- and gross-admit; capture-vs-dispersion wash |
| EXP-014c mechanism | **Entry-seam mismatch**, not exit failure: limit-touch fill ≠ measured confirmed-close-breach; adverse selection; TP-share 0.52 vs p_inward 0.696 |
| Exit decomposition | Freezing TP removes moving-target loss engine; SL subtracts value; time-stop benign; **no exit unlocks the entry** |
| Disposition | RETIRED CREDIBLE_NEGATIVE; P-10 lineage |

#### CF-MR-005 — ladder scale-in own-price harvest

| Item | Content |
|---|---|
| Mechanism | Deepening ladder adds on 4h dislocations; shared frozen exit family |
| Observation | Episode-net primary WASH; **matched-cadence random ladders reproduce per-leg CI_low>0 with no signal** (P-11) |
| Disposition | RETIRED; form is producible unconditioned |

---

### 3.6 CF-VOLHARV-001 — Structure failure of harvest capture

| Item | Content |
|---|---|
| Mechanisms | Banded rebalance premium; symmetric grid volatility harvest; monthly-anchored capped structures |
| Substrate | FX VR<1 (mean-reversion / oscillation) **exists** |
| Capture observation | Rebalance premium ~100× below design `w(1−w)σ²` estimate (UNPOWERED); grid fills at 5–28% of implied cadence; **cap-locks + censored inventory erase 100–155% of harvest** |
| Framing | Negative is **structure / capture geometry of the harvest vehicle**, not substrate absence |
| Disposition | RETIRED (P-12); within-episode-clearing structure = NEW family if revisited |

---

### 3.7 CF-HTFDI-001 — Magnitude after capture dilution

| Item | Content |
|---|---|
| Mechanism | HTF ±DI sign-conditioning of LTF continuation |
| Observation | Channel REAL and blind-replicates; true effect ≈ **1–4 bps/trade after capture dilution** — below commission on FX; ~1/10 selection bar on indices |
| Exit tier | T2 **never scoped** — no T1 survivors; trail cannot manufacture a 10× gap |
| Disposition | RETIRED (P-14); unit-pin lesson L-21 on screen→graduation inflation |

---

### 3.8 CF-MTFCTX-001 / XENA-003 — Passive-limit "capture" is a print

| Item | Content |
|---|---|
| Exit on naive reversion control | Hold-period OR profit ≥ 0.5 × *current* HTF ATR; no adverse target; native limit entries |
| Gross | +1.958 bps/leg real |
| Capture reality | **91.2% of edge is the passive-limit print**, not predictive timing (discriminating control: re-price entries to adjacent grid open collapses F̂) |
| Cost | Cost-fatal at ~0.71 bps breakeven |
| Disposition | RETIRED substrate-exhaustion; fifth P-10 vehicle |

---

### 3.9 CF-CSRR-001 — Closed before capture work

Residual reverts (VR<1) but **no hedged construction clears multiplicity** — idiosyncratic
component ≈ 0. Retired at availability; no exit surface spent (correct fail-cheaply).

---

## 4. Cross-cutting findings (for independent review)

### 4.1 What repeatedly worked as *methodology*

1. **Fail-cheaply inverted inference** — TRAIN gross screen → net → one OOS read. Phase 018
   killed 98.2% of candidates at gross for 0 counted reads.
2. **Matched-random / oscillation / phase-shift controls** — separate signal from ambient
   swing, print artifact, or own-price auto-reversion.
3. **Exit-set diff at pre-exec** (L-14) — proposal-named exits must be implemented or the
   vehicle is incomplete.
4. **Separability gate** — if fixing the obstacle kills the edge, do not spend TEST.
5. **Per-stratum adjudication** — pooled NET_POS / pooled PASS is a disclosure, not a verdict.
6. **Per-fold freshness disclosure** on walk-forward — exposed selection-overlap as the entire
   EXP-084 "edge."
7. **cTrader-primary / causal provenance** — only reliable defense against vectorized look-ahead
   in shared outcome modules (L-01).

### 4.2 What repeatedly failed as *capture mechanism*

| Claim | Evidence against |
|---|---|
| "A better stop/target will unlock the edge" | AVWAP EXIT_FLAT + empty membership; CAPGEO exit-invariance; MR-004 exit decomposition |
| "Data-derived barriers beat conventional" | EXP-083: D1/D2/D3 no distinctive TRAIN support |
| "Partials / trails will harvest the peak" | Trails systematically weak on harami; partials help median but manufacture skew failure |
| "Proactive reversion limits are the fix" | Contaminated success then causal net-negative; faithful engine null |
| "Faster timeframe = more capturable episodes" | 15m multiplies n but shrinks move vs fixed RT cost (MR-003) |
| "Harvest structure captures oscillation" | Cap-lock / censored inventory erases harvest (VOLHARV) |
| "Passive limits capture MR" | Edge is the print (XENA-003); adverse selection at band touch (MR-004) |
| "Sizing is capture" | Near-global rescale; no sign change |

### 4.3 The binding inequalities (compact)

Across chapters, tradability failed one of:

```
(1)  E[MFE_signal]  ≉  E[MFE_random]          → Mode A: nothing to capture
(2)  E[captured_net] ≤ 0  despite  MFE ≫ cost → Mode B: conversion / cost-horizon
(3)  E[captured_net] > 0  only under defect    → Mode C: not real capture
```

CAPGEO established (1) for frozen AVWAP/harami entries on 5-year data.
AVWAP Phases 010–011 established (2) under the older "move is big" narrative (later partially
revised by (1) on matched controls).
L-01 and XENA-003 established (3).

### 4.4 When is capture geometry still a live lever?

Programme rule after Phase 018 / Chapter 02:

> Capture geometry and risk-sizing are **live levers only after** a first-order
> **signal-conditional favourable excursion** (Δ-over-matched-random) is demonstrated,
> and only on a vehicle whose **entry conditioning event matches the measured object**.

That implies:

- Do **not** open a new CAPGEO-style family on another single-series price pattern without
  availability admission (P-01 / P-02).
- Do **not** re-run exit grids on CF-AVWAP / harami / MR-001..005 substrates without a genuinely
  new information source or cost regime.
- **Do** treat capture as first-class design *after* SPDR/XENA-style availability or a new data
  frontier (Bybit USDT-perp / orderflow under INFR-010) admits a real move-edge.
- Structure-failure cases (VOLHARV) remain open only under a **new within-episode-clearing**
  structure with its own D0 — not a re-parameterisation of capped monthly grids.

---

## 5. Mechanism catalogue (quick reference)

| ID | Mechanism name | Family / EXP | Outcome class |
|---|---|---|---|
| M-BTC | MAD band + trend-change lifetime | AVWAP | Gross+ / net− |
| M-FH | Fixed-horizon exit | AVWAP, CAPGEO | Best AVWAP absolute attempt; non-general; CAPGEO OOS fail |
| M-E1..E5 | HA / trail / Last-X / band-stop / time-stop | AVWAP EXP-039 | FLAT vs FH reference |
| M-PGRID | Per-instrument FH + MAD grids | AVWAP EXP-045 | 0/37 members |
| M-3B-BENCH | 50% / 1:1 / adaptive cap | Harami | Median-viable conditioned; r~0.5 unconditioned |
| M-ADV-NONE | Uncapped adverse | Harami | Helps median; kills mean |
| M-PARTIAL-V2A | Even-thirds fav scaling | Harami champion | Best surface arm; OOS not confirm |
| M-TRAIL-ZZ | Structure trail | Harami | Does not improve |
| M-VP / M-MAG | VP / magnitude fav targets | Harami | Substrate, not signal, improvement |
| M-3RD | Third-barrier time/event | Harami | Powerless lever (both substrates) |
| M-D1/D2/D3 | Quantile-derived triple-barrier | CAPGEO | No distinctive TRAIN support; trap geometry reappears |
| M-RR | Fixed RR targets | CAPGEO | S2-pass sometimes via stop truncation-to-point-mass |
| M-RCT | Reversion-completion proactive limit | MR-001/002 | Contaminated success → causal null |
| M-ERT | Equilibrium-return proactive limit | MR-001 | Screen death |
| M-F1/F2 | Moving anchor event + refreshing mean limit | MR-004 | Faithful still wash; entry-seam is binding |
| M-LIM-ANCH | Limit-at-anchor fade | MR-003 | Availability yes; capturable move < cost |
| M-LADDER | Scale-in ladder | MR-005 | Reproduced by random timing |
| M-GRID/REB | Symmetric grid / rebalance harvest | VOLHARV | Structure erases harvest |
| M-DI-COND | HTF DI continuation | HTFDI | Real but sub-cost after dilution |
| M-PASSIVE | Native trailing limit + float ATR profit | MTFCTX | Print artifact |

---

## 6. Source index (primary artifacts)

### Knowledge base

- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/pitfalls-ledger.md` (P-02, P-03, P-04, P-05, P-10–P-14)
- `docs/knowledge-base/lessons-and-amendments.md` (L-01, L-05, L-14, L-15, L-21, L-26)
- `docs/knowledge-base/methodology-canon.md`
- `docs/knowledge-base/memory/availability-first.md`
- `docs/knowledge-base/memory/look-ahead-rct-pattern.md`

### Live registry

- `docs/signal-registry/candidate-families/cf-capgeo-001.md`
- `docs/signal-registry/candidate-families/avwap.md`
- `docs/signal-registry/candidate-families/harami.md`
- `docs/signal-registry/candidate-families/cf-mr-001.md` … `cf-mr-005.md`
- `docs/signal-registry/candidate-families/cf-volharv-001.md`
- `docs/signal-registry/candidate-families/cf-htfdi-001.md`
- `docs/signal-registry/candidate-families/cf-mtfctx-001.md`
- `docs/signal-registry/components/global-techniques.md`

### Chapter 01 archives (high-signal)

- `archive/chapter-01-…/experiments-docs/reflections/2026-06-19-two-family-retrospective-reflections.md`
- `archive/chapter-01-…/checkpoints/2026-06-10-010-exit-exploration-and-line-sr/retrospective.md`
- `archive/chapter-01-…/checkpoints/2026-06-11-011-per-instrument-foundation/retrospective.md`
- `archive/chapter-01-…/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/` (EXP-047)
- `archive/chapter-01-…/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/retrospective.md`
- `archive/chapter-01-…/checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md`
- `archive/chapter-01-…/checkpoints/2026-06-23-021-mr-fade-capture-geometry/retrospective.md` (RETRACTED banner)

### Chapter 02 archives (high-signal)

- `archive/chapter-02-…/checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/retrospective.md`
- `archive/chapter-02-…/checkpoints/2026-07-01-004-cross-domain-mr-renewal/retrospective.md`
- `archive/chapter-02-…/checkpoints/2026-07-05-008-cf-volharv-001-structure-harvest/retrospective.md`
- `archive/chapter-02-…/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/retrospective.md`

### Chapter 03

- `docs/signal-registry/candidate-families/cf-mtfctx-001.md`
- `archive/chapter-03-xena-mtfctx/experiments-docs/` (XENA-001..003; ckpt-011 retirement)

---

## 7. One-page brief for an independent reviewer

**Question the programme thought it was answering (mid Chapter 01):**  
*The move is there; how do we exit to keep it net of cost?*

**What the programme actually found:**

1. On the first two price-geometry families, **peak availability was real in raw MFE units**
   but **not signal-conditional** vs matched random (Mode A established later on 5-year data).
2. Exhaustive exit grids (conventional, structure, partial, trail, data-derived, proactive
   reversion) **never produced a stable, causal, OOS net edge** attributable to exit design.
3. The one near-miss tradable claim (EXIT-RCT) was a **look-ahead** (Mode C).
4. Later vehicles failed at **cost/horizon**, **entry-seam**, **structure**, or **print** —
   different mechanisms, same abstract disqualification: *availability without legitimate
   capture*.
5. Standing policy: **availability-first**; never tune the downstream stack on a dead entry
   (P-02); capture work resumes only after a new information source or vehicle admits a real
   Δ-over-random move-edge.

**If you are reviewing a new strategy that claims to solve capture geometry, demand:**

1. Explicit Mode A/B/C classification with matched controls.
2. Causal provenance on every exit level (no `rct[di]`-class patterns).
3. Entry conditioning event ≡ measured availability object (no limit-touch vs breach mismatch).
4. Exit-invariance or exit-ablation — does varying the exit move the verdict?
5. Cost charged on the binding leg, early; gross is never tradability.
6. Per-stratum OOS with freshness / selection-overlap disclosure.

---

*Document distilled 2026-07-16 from Chapters 01–03 knowledge base and archives. Append-merge at
future rollovers if new capture modalities are tested under a genuine availability-admitted
signal.*
