# Handoff for the SIGNAL-SIGNED designer — Checkpoint 014 progress

**Audience:** designer of `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` (the normative auction-structure + signed-bar framework).  
**Purpose:** state what we implemented and tested from your document, how we adapted it to this research stack, what held, and what failed — so you can judge mechanism, sequence, and remaining claims without Xen process jargon.  
**Date of work:** 2026-07-20 → 2026-07-21  
**Family label here:** CF-SIGAUC-001 (Signed Auction Structure)  
**Status of this note:** phases 0–5 of your Appendix B plan are complete on Bybit 1m + exact taker split. Family status (keep vs close) is still an operator retrospective act; this note is evidence, not that decision.

---

## 1. One-page summary

We treated your document as **normative for signal definitions, falsifiers, and phase order**, and mapped Stages I–II spine/breadth onto our research lanes without reordering your kill path.

| Your phase | What we ran | Outcome in plain terms |
|---|---|---|
| **0** — freeze, A8 provenance, A5 baselines | INFR-017 | **Pass.** Taker split reconciles bit-exactly to raw trades; aggressor side correct. Seasonal baselines frozen. Spread column **unusable as cost/spread**. |
| **1–3** — anchor, A6 discriminator, instruments | INFR-018 | **Instruments frozen** (US open × 15m IB; A6 = D4-t50-w30, δ=0; K-UNIFORM). Integrity clean. Selection contrasts weak — parameters, not edge. |
| **4** — statistical spine (S1+S2), master go/no-go | SPDR-007 | **No-go for tradability.** Protection quantile **reproduces**, but accepted breaks add **≈0** over matched unconditional entries and **lose after cost** on majors. Classic “price has quantiles” null (our P-01). |
| **5** — breadth + S3 trap-load (Δ+) | SPDR-008 | **No-go for the signed S3 warrant.** Trap-load monotonicity is a **powered null** on IB / prior VA / prior extreme. Only reproducing edge is **unsigned** failed-break bounce (~30–55 bps MFE), not load-dependent. |
| **6–7** — S9/S14/… signals and M1–M5 models | not run | Explicitly deferred; **not pre-judged as tested**, but share premises with the S3 null (see §6). |

**Net:** the measuring stack for your tier is real and audited. The **price-only session spine** and the **measured trap-load refinement** both failed as strategy-relevant edges on this venue/band under honest matched controls. We spent **zero** programme holdout / TEST shots.

---

## 2. How we designed the programme around your document

### 2.1 Fidelity rule

- **You stay normative for content** (S1–S16, M1–M5, A5–A8, falsifiers, phase order).
- **We own packaging** (lane machinery, fences, cost floor, multiplicity, catalog). Packaging may not reorder your Phase 6→7 kill order if that work is ever opened.

### 2.2 Declared deviations (signed, on the record)

These are adaptations of *research budget*, not rewrites of signal meaning:

1. **Your “strict holdout” → TRAIN-internal CONFIRM bank**  
   - DESIGN: `2021-06-29 → 2023-03-01` (fit / race / freeze)  
   - CONFIRM: `2023-03-01 → 2023-12-18` (verify once per phase; never used to re-select freezes)  
   - Programme TEST and global holdout: **never queried** in this checkpoint  
   Reason: our lifetime TEST/holdout budget cannot fund four Stage-I confirmations. CONFIRM is labelled **train-internal**, not OOS in the programme sense.

2. **Anchors pooled first, with a few-asset spot-check**  
   Full per-symbol races over hundreds of names explode multiplicity under thin depth. Pooled race freezes; BTC/ETH/SOL spot-check was mandatory. Divergence was cosmetic → freeze kept.

3. **Passive-limit entries admitted with dual capture**  
   Programme default bans pure limit-fill expectancy claims; for *this family* we overrode that to admit your S13(a)/M3 style, but any limit claim must also emit market-on-confirm (or next-open) twin so fill ≠ prediction.

4. **Kernel calibration**  
   Your finer-reference calibration was required; if none available, explicit SKIP-NO-REFERENCE. We **did** calibrate: **K-UNIFORM** won on DESIGN days.

5. **Thin local history**  
   Majors only have ~1.4y readable TRAIN under our trailing cap. We accepted pooling and stated scope limits rather than claiming your local-depth DEPENDS-ON as met.

### 2.3 What we *did not* change

- Per-bar Δ exact; per-level Δ forbidden.  
- Acceptance close-based; flow-augmented A6 *raced*, not presumed.  
- Money floor **before** spine disposition.  
- Stage I outputs = parameters only; Stage II never ran on unfrozen instruments.  
- Mechanisms binary: grades demote; refuted mechanisms delete (not re-tune).

### 2.4 Venue & data

| Item | Choice |
|---|---|
| Venue | Bybit USDT linear perpetuals (24/7) |
| Bar | 1-minute OHLCV + BuyVolume / SellVolume / NTrades / spread columns |
| Engine rule | Live strategy edge generation is event-driven; SPDR screens may be vectorised **only** as TRAIN availability screens, not tradability claims |
| Breadth | Thesis is cross-section; SPDR-008 universe = **296** admitted names with TRAIN bars (not 894) — survivorship-shaped older listings |
| Cost | Taker ~11 bps RT + measured spread + funding ≤ ~3 bps at ≤24h |

---

## 3. Phase-by-phase: what was built and measured

### Phase 0 — Provenance & baselines (INFR-017)

**Your kill-gate:** split fails A8 → park the family.

| Check | Result |
|---|---|
| HYP-I1: Vb/Vs vs raw trades | **PASS** — 20/20 symbol-days, worst relative deviation 0.0 |
| Archive `side` = aggressor? | **Yes** (Buy-PlusTick ~26:1, unanimous) |
| Buy+Sell ≡ Volume | Already tight; does **not** replace A8 (we treated it as internal consistency only) |
| A5 seasonal baselines | Frozen, 194 instruments, full minute×dow grid, DESIGN-only fit |
| Signed-bar lane | Built (`SignedBar` + catalog lane) so Δ is engine-readable |

**What worked**
- Founding premise of the document: **per-bar delta is a measurement** — verified end-to-end on this stack.
- Seasonal residual machinery is on disk and hash-pinned.

**What did not**
- **`SpreadBps` is unusable** as a spread or cost input: it is a mean-print differential, **negative** in ~32–40% of BTC/ETH TRAIN minutes; our shared round-trip helper can pass negatives through unfloored.  
  Consequence: your **§2.5 spread-regime layer is UNAVAILABLE** for Stage II. Stress/precision demotion by spread cannot run until a real floor exists.
- Breadth ceiling is structural: only ~1/3 of admitted names have TRAIN history.

---

### Phases 1–3 — Instruments (INFR-018)

Frozen registry pin: `5c386984…`

| Instrument | Frozen choice | Notes |
|---|---|---|
| Anchor (A7) | **A-USOPEN · L = 15 min** | Pooled winner; BTC/ETH/SOL spot-check cosmetic |
| A6 acceptance | **D4-t50-w30 · δ = 0** (price-only) | Flow-augmented variants raced; this form froze |
| Profile kernel | **K-UNIFORM** (calibrated) | PERFORMED, not SKIP |
| Class residual thresholds | Per-symbol p90/p10 in registry | Sparse tails as designed |
| §2.5 spread bands | **UNAVAILABLE** | Inherited from Phase 0 |

**Integrity (your spirit: constructions must not leak future)**
- Future IB-level shift and outcome path-swap **collapse** honest rules; planted leaks fire. Gates have teeth.

**What worked**
- Full Stage I freeze at production scale (140 symbols / 609 DESIGN days), not a smoke demo.
- Acceptance vs trap separation is *constructible*; path-swap kills fake separation.

**What did not / soft**
- Anchor selection contrast was **small** (E ≈ +0.10) with CI through zero / near MDE — we froze a **parameter**, not a proven anchor edge.  
- CONFIRM re-ranks would prefer other cells if we cheated and re-selected; we did **not** — freezes stay DESIGN-only (your intent preserved under our CONFIRM mapping).

---

### Phase 4 — Statistical spine S1+S2 (SPDR-007) — master gate

**Your question (framework falsifier #1, roughly):** does a ~65–70% Protection quantile reproduce at the correct (1−p) percentile for the selected anchor, with useful conditioning structure?

**How we tested (design choices you should know)**
- Event = every A6-accepted poke under the frozen pin (~7k DESIGN / ~11k CONFIRM).  
- Protection Level = DESIGN (1−p) quantile of favourable excursion in **IB-width units**, frozen, verified once on CONFIRM.  
- **Binding contrast** is not “does a quantile exist?” but **signal − matched cross-session unconditional entry** (same phase/side spirit; within-session phase match was infeasible, so cross-session control was ratified).  
- Money floor computed first: cost ~14–16 bps RT; TP1 size **above floor** on majors (target *size* is large enough if hit rates were edge-bearing).  
- **No Δ in this phase** — pure statistics stream, as your S1/S2 base before signed upgrades.

**Results**

| Read | Outcome |
|---|---|
| Quantile reproduction (pooled) | **Reproduces** — p70 hit ≈ 0.73, calib_err ≈ +0.028 (≤ 0.05 band) |
| Per-symbol | Heterogeneous — e.g. SOL p70 **broken** (+0.105); pooling masks local failure |
| Race win-rate vs control | **≈0** lift (signal 0.333 vs control 0.343) |
| Race vs cost-adjusted breakeven (majors) | **Below** on all 5 (w − p0ᶜ ≈ −0.05 to −0.14) |
| Excursion asymmetry vs control | WASH (CI through 0; effect far below designed MDE) |
| Control also “has” a Protection quantile | **Yes** — within ~10% of signal level; control hits signal’s level ~67.5% |

**Disposition:** **NOT_WORTH** for the price-only spine as a strategy candidate.  
**Interpretation in your language:** framework falsifier #1 is **not** triggered on the strict “quantile fails to reproduce” reading. The **programme-binding** failure is the **matched-unconditional / cost** reading: acceptance conditioning does not buy resolution skill; reproduction is what price paths do (our P-01 pattern). That is consistent with your own discipline that grades must beat matched unconditional base rates — the spine fails that bar even though the quantile exists.

**Scope of this kill (important)**
- **One object only:** daily ~24h session from **US open**, 15-min IB, single-session hold (~23h), 1m bars.  
- Not tested: 8h funding cadence, micro 1–10 bar holds, structural multi-session holds, higher-TF bars.

---

### Phase 5 — Breadth + S3 trap-load Δ+ (SPDR-008)

**Your S3 claim (falsifiable core we measured):** after a failed break, reversal is **monotone in measured trap load**  
`trap_load = poke_side × Σ delta_ratio_resid`  
(signed by aggressor split — not geometry), and HIGH-load traps rotate further than LOW-load traps of the same geometry.

**Why this phase existed after Phase 4 failed**  
Price-only spine died as P-01. Your document’s distinguishing warrant is signed flow’s *marginal* value. S3 is the simplest Δ+ refinement of failed-break geometry. If load does nothing, the “measured trapped side” story is empty at this event class.

**Design**
- Boundaries tested **independently:** IB edge, prior value-area (K-UNIFORM proxy), prior session extreme. No cross-boundary pooling for the promote rule.  
- Universe: 194 A5-fitted symbols (breadth denom 296); **16,669** DESIGN / **26,348** CONFIRM traps.  
- Promote rule (our K=3): connected multi-cell cluster, not a single lottery cell.  
- Matched random-timing control for availability; derangement null for load monotonicity; future path-swap tripwire on signed reads.

**Results — signed warrant**

| Boundary | Load–reversal ρ (DESIGN) | Power | CONFIRM | HIGH−LOW tier |
|---|---|---|---|---|
| IB | ≈ −0.015 | MDE ~0.02, n thousands | ~0 | CI through 0 |
| Prior VA | ≈ +0.023 (p≈0.05 whiff) | same | **flips negative** | CI through 0 |
| Prior extreme | ≈ −0.033 | same | ~0 | CI through 0 |

- All primary signed cells: **not supported**.  
- Effect sizes are inside / below MDE with huge n → **powered null** (“no signed edge”), not “cannot see.”  
- Cluster scan: ~7 “winners” vs ~6 expected under null; **more anti-monotone mirror cells than winners** → multiplicity noise.

**Results — only edge that reproduces**

- Failed breaks **do** reverse more than matched random-timing entries and more than ordinary non-trap touches on PVA/PRIOR (~**+30–55 bps** MFE-scale; ~+0.3–1.0 IB-widths).  
- **Not load-dependent** → pure **unsigned failed-break geometry**.  
- That is your S3 *base* without the Δ+ refinement — and it is the same P-01 class already dispositioned dead at Phase 4 for tradability.

**Disposition:** **NOT_WORTH** for the S3 **signed** warrant. Unsigned bounce recorded as market-science characterisation, not a tradability claim.

---

## 4. What worked (keep as durable findings)

1. **Data-tier premise is true on Bybit.** Exact per-bar taker aggression is recoverable and correctly signed. The family was not parked on A8.  
2. **Your Stage I discipline is executable.** Freeze → confirm-once → Stage II only with pins works at hundreds of symbols.  
3. **Acceptance/trap machinery is real and leak-tested.** A6 rules can be operationalised; destroy controls collapse fakes.  
4. **Protection quantiles exist and largely reproduce** at pooled ~65–70% class — your S2 *object* is not imaginary; it just is not *conditional skill*.  
5. **Unsigned failed-break availability is real** on prior VA / prior extreme (characterisation). Geometry of traps is not null; **signed load on traps is**.  
6. **Cheap death path worked.** Four TRAIN-only items, zero counted TEST reads — matches your “die honestly in Phases 0–5” intent.  
7. **Shared code assets** now exist for any later auction work: signed-bar lane, seasonal baselines, acceptance/trap modules, frozen instrument registry.

---

## 5. What did not work (relative to the document’s hopes)

| Claim / hope | Evidence |
|---|---|
| S1 acceptance conditioning beats unconditional base rates (session object we tested) | Matched control wash; race at gross breakeven |
| S1/S2 spine clears cost as a session trade | Below cost-adjusted breakeven on all majors tested |
| Protection reproduction ⇒ tradable framework | Reproduction without control separation = P-01 |
| S3 Δ+ trap load predicts more reversal | Powered ρ ≈ 0 on three independent boundaries |
| Breadth will “find soil” where majors do not | Cross-section cluster count sits inside null budget; no connected signed cluster |
| §2.5 spread regime as independent stream | Column broken; layer unavailable |
| Stable 24/7 anchor with clear expectancy | Frozen by rule, but selection contrast weak |

**Not claimed refuted by this work**
- S9 absorption marginal value over unsigned base  
- S14 CVD–price divergence  
- S10/S11/S15 sequences, S16 boxes, full M1–M5 assembly  
- Funding-session anchors, micro or structural horizons  

Those remain **untested**. Whether they remain *worth testing* is a mechanism judgement (next section), not an automatic continuation.

---

## 6. How to read remaining claims after S3’s null

Your document’s central tier claim is that **signed refinements add marginal value over unsigned bases**.  

- S3 is the cleanest, highest-n test of “measured aggression intensity of the poke ⇒ more forced unwind.”  
- It failed hard under power.  

**Implication for S9 / S14 (if you care about efficient kill order):**
- **S9** (absorption): still a different object (effort without result *at a level*, not failed-break load). It can survive S3’s death *if* the mechanism is truly “failed aggression at a shelf,” not “more Δ in a failed poke.”  
- **S14** (CVD–price divergence): session-flow stream; partially correlated with bar Δ by construction in your Part 0. After S3, any proposal should show why **integration / location / multi-bar structure** creates information that **bar-level trap load** does not.  
- **Re-parameterising S3** (new load formula, new residual, new hold) after a powered null would violate your own binary-mechanism rule unless the mechanism statement changes.

We did **not** auto-open Phase 6. Our recommendation to the operator: open only with a **written mechanism that does not rely on “more measured aggression ⇒ more trap unwind” as the sole engine**.

---

## 7. Design notes for you (if you revise the source or a sequel)

These are observations from implementation, not demands:

1. **Master go/no-go wording.** Strict “quantile reproduces” can pass while “beats unconditional + cost” fails. If the intent of falsifier #1 is *framework tradability*, consider elevating the matched-base-rate and cost bars into the written master gate, not only calibration error.  
2. **Control definition for session breaks.** Within-session phase-matched unconditional entries are hard on sparse events; we used cross-session matched controls. Worth specifying preferred control families in the source so replications are comparable.  
3. **P4 spread.** The framework assumes a usable liquidity proxy. On this feed, the stored spread column is not one. Either define a tick-floored construction as mandatory Phase 0 exit, or demote §2.5 until a real quote/spread exists.  
4. **24/7 anchor expectancy.** Selection may produce a stable *clock* without stable *edge*. The document might distinguish “operational anchor for measurement” from “anchor with proven breakout expectancy.”  
5. **Horizon menu.** We only exercised the middle (session) horizon. Micro and structural remain open; if they are first-class in the source, a minimal design might require at least one screen per horizon class before a whole-family close.  
6. **Survivorship vs “full cross-section.”** Trailing history caps make “full venue breadth” aspirational. Breadth maps describe **older listings with history**, not the live board.

---

## 8. Artifacts map (if you want the numbers raw)

| Your phase | Artifact roots |
|---|---|
| Checkpoint design | `docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/design.md` |
| Family card | `docs/signal-registry/candidate-families/cf-sigauc-001.md` |
| Phase 0 | `python/experiments/INFR-017/` (`report.md`, baselines pin `1b7244c8…`) |
| Phases 1–3 | `python/experiments/INFR-018/` (`report.md`, registry `5c386984…`) |
| Phase 4 spine | `python/experiments/SPDR-007/` (`report.md`, `analysis.md`) |
| Phase 5 S3 breadth | `python/experiments/SPDR-008/` (`report.md`, `analysis.md`, `xen.sigbar.trap`) |
| Source (normative) | `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` |

---

## 9. Bottom line for the original designer

We ran **your** Phases 0–5, in order, on exact taker-signed 1m bars, with honest matched controls, cost floor first, and no holdout burn.

- **Instruments and data premise:** solid.  
- **S1/S2 session spine as edge:** fails (reproduction without conditional skill; dies after cost).  
- **S3 measured trap load:** fails (powered null; only unsigned geometry lives).  
- **Later signed/model phases:** untested; mechanism bar for reopening is now higher because the simplest Δ+ claim already died under power.

If you revise the framework, the highest-value feedback we can give is: **treat “beats matched unconditional base rate after cost” as co-equal to “Protection quantile calibrates,”** and treat **Δ+ marginal value** as something that must clear a bar *over* unsigned failed-break geometry — which we already measured as real but non-promotable.

---

*Prepared as a research handoff from the Xen checkpoint-014 execution record. Family keep/close remains the programme operator’s retrospective decision.*

---

## Addendum (added 2026-07-21) — implementation notes, statistical teeth, and continue/close order

Detail not in the body above, added after a second read of the two screen reports. Nothing here changes a disposition; it is the material a careful replication or a source revision would want.

### A. Statistical-method findings worth carrying

**A.1 The real multiplicity test was the *mirror-cell* count, not "7 vs 6 expected."**
The K=3 cluster was ruled noise on a sharper argument than raw excess. Across **241 powered cells**, **7** passed the positive load-monotonicity gate against **6.0** expected under the null — already unremarkable. The decisive read: **10** cells passed the *anti-monotone mirror* gate (load predicts *less* reversal). The positive tail is not even enriched over its own negative mirror. **Durable lesson for the framework:** on a wide cell grid, count both tails; a positive count near null expectation *with a heavier negative tail* is dispositive noise, and a single-tail "≥3 winners" rule (our first-draft K=3) would have mis-promoted here. We hardened the promote rule to require the positive tail to materially exceed the mirror before it counts.

**A.2 Two screen bugs were found; both are logged so a replication does not inherit them silently.**
- **R3 regime Spearman (SPDR-007):** the screen used a `drop_nulls` that does **not** drop float `NaN`, so ~1,930 warm-up `NaN` (27% of events) polluted the correlation and reported ρ-contrast **+0.130**. Finite-only recompute is **−0.040** — a sign flip. R3 ≈ 0 either way, so the disposition stands, **but any graduation that leans on a regime read must guard `is_finite` first.**
- **SPDR-008 minor, non-invalidating:** entry-bar inclusion affects 0.07% of the window (immaterial); the T4 availability CI omits control-side resampling (acceptable only because T4 is P-01/disclosure, not a promote read). Both are flagged in that screen's `analysis.md`.

**A.3 Sparse session events break the sign/side-derangement null's power.**
The S1 side-control could only derange **60 of 7,070** events within calendar-day blocks — **2,694 were day-singletons** and **4,316 were one-side-dominant** (dropped and counted, per our unpowered-not-negative rule). For session-scale events there is almost nothing to shuffle inside a day. **If the source wants a sign/side null on sparse events, the block must be wider than the calendar day, or a different control family is needed** — this is a control-design finding, not a result.

**A.4 The unsigned failed-break bounce is real but tail-fragile.**
The ~30–55 bps reversal advantage (T3/T4) is a **mean** of favourable excursion, and excursion-tail means are fragile. A **median/trimmed re-read is the pending follow-up.** If the framework leans on unsigned failed-break availability as characterisation, treat the point estimate as an upper-ish bound until the robust-stat re-read confirms it.

### B. Two reads a replication must **not** misinterpret

**B.1 "Leak tripwire: NO_MATERIAL_EDGE" is *not* "the edge survived a leak test."**
On both screens the future-destroy tripwire returned **NO_MATERIAL_EDGE** with strong positive-control bite (SPDR-007 corr **0.77**; SPDR-008 corr **0.53–0.92**). Meaning: the gate genuinely installs the donor outcome when one exists (real teeth), but here **there was no material raw edge to leak-test.** This is the correct integrity outcome for a *null* result — do not cite it as evidence that a live edge is leak-free.

**B.2 Pooled reproduction hides per-symbol breakage.**
The Protection quantile reproduced *pooled* (calib_err +0.028), but per-symbol the census was **51 REPRODUCES / 25 DRIFTED / 21 BROKEN of 97** (SOL p70 **+0.105 BROKEN**). A pooled calibration pass is not a per-symbol pass; any per-symbol claim must read the census, not the pool.

### C. Concrete continue/close order (the operator recommendation, in plain terms)

Two powered nulls do **not** by themselves close the family, and the next step is **not** the expensive XENA model assembly either. The cheapest honest move:

1. **Close the price-only spine (S1/S2) and the S3 trap-load arms** — three-way dead: P-01 at Phase 4, powered signed null at Phase 5.
2. **Before spending any sparse-session portfolio calibration, run a cheap TRAIN-only availability screen on S9 absorption's marginal value over the unsigned base** (optionally S14 CVD-divergence) — same breadth-before-depth discipline that made Phases 0–5 cost four items and zero reads.
3. **Close the family only on a third independent powered null.** If the absorption screen shows soil, *then* the sparse-session CAL spend is warranted.

Rationale the source should weigh: **S3 is price-adjacent** (a signed tag on a failed-break geometry), so its null is *weaker* evidence against S9/S14 than the raw count suggests. S9/S14 are the mechanisms that are genuinely invisible to price (effort-without-result at a shelf; CVD–price divergence). They are where the exact-delta measurement could pay where price cannot — and they are still untested.

**One cost caveat that binds any future net claim:** because `SpreadBps` is UNUSABLE (Phase 0), every net read across the 296-name breadth currently carries an **unmeasured spread term**. On the majors that is small; on illiquid alts it can dominate and is exactly where a breadth map would place its "soil." A tick-floored per-symbol quote/spread reconstruction is a **hard prerequisite before any net breadth claim**, and it is a separate problem from the mechanism question.
