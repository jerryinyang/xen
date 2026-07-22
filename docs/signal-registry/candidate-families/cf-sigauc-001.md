# CF-SIGAUC-001 — Signed Auction Structure from 1-Minute Bars

**Status:** **`CLOSED`** — **2026-07-22, checkpoint-015 retrospective, operator-directed.** 0 slots · 0 counted TEST reads · holdout SEALED throughout the family's life. Closed on **three independent powered nulls**: SPDR-007 (price-only session spine — NOT_WORTH, P-01), SPDR-008 (S3 measured trap-load — powered null on all 3 boundaries), **SPDR-009 (S9 signed-absorption marginal value — powered null at D1 1d/1m; +1.81 bps vs MDE 5.5, ρ +0.008, median 0.0 bps vs an 11.3–13.0 bps floor; MIRROR arm larger than S9 at 325 vs 311)**. **Power states at close, binding on how "closed" is read: D1 POWERED-NULL · D2 INCONCLUSIVE (16 events) · D3 INCONCLUSIVE (2) · D4 INCONCLUSIVE (0, pre-declared power-limited).** **D8 (2026-07-22)** amended the D7 closure minimum from "D1 **and** D2" to "**D1**, with every pair's power state named" — D2's shortfall is a structural event-rate fact on this venue/band, not a sampling accident. **`CLOSED` is not "tested everywhere": S14 (CVD–price divergence) was NEVER RUN**, and the structural + funding-cadence horizons were never screened. **Grades at close:** S1 **DEMOTED** (operational anchor only); S3 Δ+ **and S9** **DELETED** (binary-mechanism rule — no re-parameterisation); S2 / S3-base / A6 / A8 **CONFIRMED as measurement/characterisation** (none a strategy edge); §2.5 spread layer UNAVAILABLE (INFR-019 never built → no net claim was ever admissible). **Durable assets survive the close:** signed-bar catalog lane, A5 baselines 1m `1b7244c8…` + MTF `5f170b71…`, instrument registry `5c386984…`, `xen.sigbar.trap`, `xen.sigbar.absorb`. Retrospective: `docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/retrospective.md`.
**Family ID:** CF-SIGAUC-001
**Chapter:** 04 (NautilusTrader + Bybit USDT-perp primary, INFR-010+)
**Route:** **INFR (instrument build) → SPDR (spine + breadth) → full XENA** — EXP lane not used
**Source methodology:** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` (normative for signal definitions, falsifiers, and phase order; this card fixes class, constraints, and Xen-lane mapping only)
**Checkpoint container:** `docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/`

---

## 1. Thesis

Auction structure — where a session's participation concentrated, which boundaries were accepted or rejected, and **which side's aggression was rewarded or absorbed** — conditions forward price resolution on Bybit USDT perpetuals.

The family's distinguishing input is **exact per-bar taker aggressor delta** (Δ = BuyVolume − SellVolume), available natively from Bybit's trade archives. This is a measurement, not a price-derived estimate: it observes *who initiated* each minute's volume, which no construction in the programme's history has had. Three consequences:

- Absorption (heavy measured aggression producing no price result) becomes observable rather than inferred.
- CVD–price divergence — structurally invisible to any price-derived sign estimator, because such estimators go flat exactly where price does — becomes measurable.
- Every unsigned effort/result class gains a signed refinement whose value is testable **as a marginal contribution over the unsigned base**.

**Not claimed a priori:** that session logic pays on a 24/7 venue (the anchor must be *selected*, A7); that the signed refinements beat their unsigned bases (that is the central falsifiable claim); that any of it survives cost.

---

## 2. Mechanism class (for CAL / checkpoint scoping)

| Attribute | Value |
|---|---|
| Class | **Session-anchored auction events** (breakout / trap / acceptance) + **located signed-flow triggers** |
| Information source | 1m OHLCV **+ exact taker buy/sell volume** + per-bar spread proxy + calendar |
| Event cadence | Sparse, session-scale — order 1–3 primary events per symbol-session |
| Hold horizon | micro (1–10 bars) · session (remainder of anchored session) · structural (1–5 sessions) |
| Adjudication shape | Multi-candidate portfolio (XENA); breadth-first per source §6.12 |
| Cost sensitivity | High — session-horizon holds; taker RT 11.0 bps dominates, funding ≤ ~3 bps at ≤24h |
| CAL implication | **Existing pin `abbb1842…` (CLS-FILTER low + CLS-EPISODE low) is not established for this class** — a CAL leg shaped to sparse session-event objects is a checkpoint-015 prerequisite, not a checkpoint-014 blocker |

---

## 3. Data tier — verified on disk 2026-07-20

Source doc's required tier is **1m bars carrying O,H,L,C,V + taker-buy volume + taker-sell volume + a spread-proxy column, plus a calendar**. Present at `python/experiments/INFR-011/data/staging/bars/*.parquet` (904 symbols):

| Doc primitive | Column | Verified |
|---|---|---|
| P1 bars | `Open High Low Close Volume` | present |
| P2 signed split (exact) | `BuyVolume` `SellVolume` | present; `Buy+Sell ≡ Volume` to float epsilon (max rel dev 3.8e-16 across BTC/ETH/SOL, 0 nulls) |
| P3 CVD | derived from P2 | computable |
| P4 spread proxy | `SpreadAbs` `SpreadBps` | present, **has nulls** on the TRAIN band (BTC 158, ETH 4,543, SOL 6,951 minutes) — A8 must pin gap handling |
| Part 5 "cheap upgrade" (trade count) | `NTrades` | present |

**Binding gap — the family's one hard dependency.** These columns are **not engine-readable**. `data/catalog/` holds Nautilus `Bar` (OHLCV only), and all strategy logic must run in the Nautilus engine (price-primary, binding). A signed-bar catalog lane is required before any candidate emission. `xen.orderflow` (INFR-013) already ships custom Data types + catalog schemas with round-trip proven — bounded work, not new architecture. **INFR-017 owns it.**

**Two provenance caveats carried into A8 (source §2.2 A8, §6.4):**
1. `Buy+Sell ≡ Volume` is an **internal-consistency** check, not the A8 audit. A8 requires reconciliation against **raw trades** for a sample window. Bulk raw trades were not retained (INFR-013 deleted its sample after verification) — a sample-window re-download is expected.
2. `SpreadBps` is derived from **the same aggressor split** as Δ (dataset-reference: "Buy ≈ ask, Sell ≈ bid"). The source doc treats P2 and P4 as independent (streams 3/4 vs the §2.5 regime layer); they share a source. The correlation must be pinned and disclosed at A8, and §2.5 spread reads may not be presented as independent corroboration of a Δ read until it is.

---

## 4. Hard bans

1. **Non-causal construction.** Closed windows only; decisions at bar open on confirmed data ≤ t−1; entries at signal-bar close at the earliest (source §6.8).
2. **Per-level signed attribution** — barred by the source itself (§2.1, Part 5). Per-BAR Δ is exact; per-LEVEL Δ is estimate-grade. No signal may depend on delta-at-price, footprint-imbalance analogs, or intra-bar sign placement.
3. **Sub-minute ordering.** S15's sequencing is bar-level and stops there (A2).
4. **~~Passive-limit ban~~ OVERRIDDEN for this family (operator 2026-07-20).** Programme P-10 does **not** hard-ban source limit-style entries. Source S13(a) "fade the defense" and M3 balance-edge fades are **admitted as written**. When a cell claims a passive-limit fill, it **must also emit the market-on-confirmed-event twin** (and/or L-27 next-open control) so fill advantage vs prediction is decomposed — dual capture for comparison, not a veto of the source mechanism. Never present limit-only expectancy as pure prediction without the twin.
5. **Unit lies across seams** — every normalised effect states its normaliser object exactly (indicator, period, timeframe, lag); any money claim re-derives the divisor from screen code, never memory (L-21 / P-15).
6. **Costless success claims.** Net cost binds any selection objective testing selectivity (L-26); spread is a verdict leg, never disclosure-only (L-22).
7. **A screen as a tradability or deployability claim.** SPDR outputs dispositions only.
8. **Re-parameterising a refuted mechanism.** Source Part 3 mechanism doctrine: grades may be demoted; **mechanisms are binary** — a mechanism refuted by data is deleted, not re-tuned. Binding here.
9. **Stage II results on unfrozen Stage I instruments** — unattributable by construction; they re-run (source Appendix B).
10. **Single-lottery-cell family wins.** Promotes require a cluster, never a grid maximum.

---

## 5. Distinctness vs the pitfalls ledger (operator signs at checkpoint-014 D6)

| Pitfall | Assessment |
|---|---|
| **P-07** — tick-volume construction inert, *"re-open only if a flow source that is not broker-reported tick volume (true order-book / volume-at-price)"* | **CLEARED, and this is the family's principal warrant.** Exchange-native taker aggressor volume from Bybit trade archives is not broker-reported tick volume. It is the first genuinely non-price-derived information source the programme has held — the KB terminal-branch statement names exactly this class as the remaining frontier. |
| **P-01** — single-instrument event-driven **directional price-geometry** entries, dead twice; re-open needs a new information source, screened availability-first | **Tight — requires operator sign-off.** The S1/S2 spine (anchored breakout + excursion quantiles) uses **no volume at all** and is single-instrument and directional. Distinctness argument: (a) the conditioning object is a *calendar-anchored participation window*, not a candlestick geometry — never tested here; (b) the target is an excursion-**quantile** with an explicit direction rule, not a fixed geometric endpoint; (c) it is screened availability-first, TRAIN-only, with matched unconditional baselines (source §6.3); (d) new universe and stack. Against: at base it is price on one instrument. **Mitigation, binding:** Phase 4 is scoped as an availability screen against matched unconditional base rates and cannot itself promote the family; a spine result that reproduces only unconditionally is a P-01 confirmation, recorded as such. |
| **P-10** — passive-limit MR fades | **Overridden for this family (operator 2026-07-20).** Source limit-style entries kept; dual capture (limit vs market-on-confirm / L-27) mandatory when limit fills are claimed — comparison, not ban. XENA-003 fill-print lesson still measured, not used as a hard veto of S13(a)/M3. |
| **P-14 / P-15** — HTF conditioning sub-cost; screen→graduation unit seam | Not this mechanism, but the money-unit floor (§7) and L-21 unit pin bind at every seam. |
| **P-12** — banded-rebalance / capped symmetric grid | Not in family. No grid object. |

---

## 6. Money-unit floor (binding first design act)

The programme's dominant recorded killer is cost, not signal (CF-HTFDI-001 ≈1–4 bps vs cost; XENA-003 breakeven 0.705 bps; CF-HTFCAP-001 real gross edge dead against an ~18 bps wall). The floor arithmetic is therefore computed **before** any availability screen, not after.

| Term | Value (`xen.evaluation`) |
|---|---|
| Taker fee | 5.5 bps/side → **11.0 bps RT** |
| Maker fee | 2.0 bps/side → 4.0 bps RT |
| Funding (conservative) | 1.0 bps/8h → **≤ ~3 bps** at ≤24h session-horizon holds |
| Spread | per-symbol measured pin from the T1 pseudo-quote series (`t1_round_trip_spread_bps`); **the binding term across the breadth cross-section** |

**Rule.** Before the Phase-4 disposition, the Protection Level (TP1) is converted to bps/trade using the actual normaliser object and compared against `taker RT + measured spread RT + funding`. A spine whose TP1 sits at or below the floor is recorded as **market science, not strategy** — which is the source's own framework-level falsifier ("surviving edges vanish inside costs at their horizons"). It may still route forward, but only re-framed as characterisation.

---

## 7. Hypotheses (family level)

Mapped from the source's framework-level falsifiers (§6.10). Stage I gates are hypotheses and carry full rigor even though Stage I *tuning* is free.

| ID | Phase | Question | Failure meaning |
|---|---|---|---|
| HYP-I1 | 0 | Does the taker split reconcile against raw trades, and can the spread column's definition be pinned? | Validity attestation — failure means *fix the data*, never *no edge* |
| HYP-I2 | 1 | Does at least one session anchor show stable breakout expectancy on this 24/7 venue? | No anchor ⇒ defer to the Phase-5 breadth sweep before abandoning |
| HYP-I3 | 2 | Does any A6 acceptance discriminator separate trap-type from acceptance-type outcomes out-of-sample? | Framework falsifier — the transition branch is untradeable; only balance-rotation survives |
| HYP-I4 | 3 | Profile kernel calibrated against a finer reference (or explicit SKIP-NO-REFERENCE)? Do §2.3 signed classes cluster where the mechanism predicts? | Instruments unvalidated ⇒ no downstream signal is attributable |
| **HYP-S1** | **4** | **Does a ~65–70%-class Protection quantile reproduce locally at the correct (1−p) percentile, per selected anchor, with the Δ-coherence stratification holding?** | **MASTER go/no-go — framework falsifier #1; the whole document demotes one notch** |
| HYP-S2 | 5 | Across the venue's full cross-section, where does auction-structure logic pay at all? | Allocation map for later phases; grades nothing by itself |

**Deferred to checkpoint-015 (not opened here):** signal-level marginal-value tests (trap load-monotonicity; **signed absorption's marginal value over its unsigned base** — the tier's central claim; CVD-divergence resolution; drive asymmetries; S16 boxes; S15 ordering premium) and model assembly (M1/M2/M3/M4/M5).

---

## 8. Kill / park criteria

| Stage | Kill / park |
|---|---|
| Phase 0 (A8) | Taker split fails to reconcile → **park the family**; the tier's entire warrant is the column's integrity |
| Phase 1 | No stable anchor on any candidate → park pending the Phase-5 breadth read |
| Phase 2 | No discriminator separates at any parameterisation → framework falsifier; family reduces to balance-rotation only |
| Phase 3 | Classes fire uniformly, or kernel neither calibrated nor SKIP-NO-REFERENCE → instruments unvalidated; stop before spending Stage II |
| **Phase 4** | **No Protection quantile at the correct percentile → master no-go; family closes on the source's own falsifier** |
| Phase 4 | Spine reproduces but TP1 sits at/below the money floor → characterisation only, no tradability route |
| Phase 5 | No instrument stratum pays → terminal-branch confirmation for this tier |
| Infra | Signed-bar catalog lane cannot be built causally → park, don't book |

---

## 9. Infrastructure dependencies

| Dependency | Role | Blocks |
|---|---|---|
| **Signed-bar catalog lane** (custom Data type + ingest; `xen.orderflow` lineage) | Engine-readable Δ | everything — INFR-017 |
| A8 provenance audit (raw-trade sample re-download) | Validity of the tier | INFR-017 |
| Seasonal baselines (A5): minute-of-day × day-of-week residuals for V, range, \|Δ\|, Δ/V, spread | Every threshold in the framework | INFR-017 |
| Frozen instrument set (pooled anchor + few-asset spot-check table, A6 rule, kernel with calibration-or-SKIP note, class thresholds) — hash-pinned | Stage II attributability | INFR-018 |
| Bybit cost stack (fees + measured spread + funding) | Money floor, XENA net | SPDR-007 floor; XENA binding |
| **XENA CAL shaped to sparse session-event objects** | Counted portfolio path | checkpoint-015 only — **not** a checkpoint-014 blocker |

---

## 10. Evidence ledger

| Date | Item |
|---|---|
| 2026-07-20 | D0 complete from `SIGNAL-SIGNED.md`. Data tier verified on disk (signed columns present, `Buy+Sell ≡ Volume` to 3.8e-16, spread nulls + shared-source caveat recorded). Registration proposed at checkpoint-014 (D1). 0 slots, 0 reads. |
| 2026-07-20 | **Operator: family scope is SINGLE.** All Part-3 signal statements (S1–S16) and all Part-4 model compositions (M1–M5) are **distinct strategies within this one family**, not separate families. Information streams (statistics / profile / bar-flow / session-flow) are sub-mechanisms that may individually die without closing the family. No stream-based family split. |
| 2026-07-20 | **Operator: source-adherence resolutions.** CONFIRM-bank holdout accepted; pooled anchors + few-asset per-instrument spot-check; P-10 ban lifted — source passive-limit admitted with dual capture for comparison; Phase-3 kernel calibration gap closed (finer reference or SKIP-NO-REFERENCE); thin local history accepted; source Appendix B plan preserved under XENA packaging. |
| 2026-07-20 | **REGISTERED — checkpoint-014 D1–D6 operator-signed.** Family APPROVED. Registry row REGISTERED in `multiplicity-registry.md`; P-01 distinctness signed (D6a); IDs assigned INFR-017/018 + SPDR-007/008. Test-read ledger unchanged (no TEST contact). 0 slots, 0 counted reads, holdout SEALED. INFR-017 authorised to design. |

---

| 2026-07-20 | **Operator rulings post-INFR-017:** holdout touch **CLEARED** (disclosure stands; holdout SEALED, no shot consumed); **SPDR-008 sized to 296** TRAIN-readable instruments (ckpt-014 AMENDMENT-1, NEUTRAL) with the survivorship caveat binding on every breadth read. |
| 2026-07-20 | **INFR-017 COMPLETE — QA APPROVE (run 4).** Kill-gate **HYP-I1 PASS**: the stored taker split reproduces bit-exactly from raw Bybit trades (20/20 symbol-days, worst relative deviation 0.0), and the archive `side` column is confirmed the **AGGRESSOR** side (Buy-PlusTick 26.2:1, unanimous) — **delta = buy − sell is verified as exact net taker aggression with the correct sign; the family's founding premise holds.** Frozen for INFR-018: `results/seasonal_baselines.parquet` sha `1b7244c8…` (A5 baselines, 194 instruments, full 10,080-cell grid, DESIGN bank only), `results/column_pins.json` `pin_sha256 e3b9fd9b…`, `SignedBar` contract + `data/catalog_sigbar/`. **`SpreadBps` pinned UNUSABLE** as a spread or cost input. Two defects found and fixed in-flight (aliased seasonal grid; a holdout-crossing scan behind the design's headline figures — corrected and disclosed, **operator adjudication pending**). Breadth limit recorded: 296 of 894 admitted instruments have TRAIN data, 197 reach the DESIGN bank. 0 slots, 0 counted reads, holdout SEALED. Report `python/experiments/INFR-017/report.md`. |
| 2026-07-21 | **INFR-018 COMPLETE — operator accepted instrument registry.** Stage I freeze only (parameters, not edge): registry `pin_sha256 5c386984…` — anchor **A-USOPEN · L=15**, A6 **D4-t50-w30 · δ=0**, kernel **K-UNIFORM** (calibrated on DESIGN days), class residual thresholds pinned; §2.5 spread regime still **UNAVAILABLE**. DESIGN races 140 symbols / 609 days; CONFIRM train-internal recorded. Integrity: I2 future-shift + I3 path-swap both collapse (do not survive); both leak plants fire. QA runs 1–7 REVISE → run 8 APPROVE. Family status unchanged (REGISTERED). 0 slots, 0 counted TEST reads, holdout SEALED. Report `python/experiments/INFR-018/report.md`. Next: **SPDR-007**. |
| 2026-07-21 | **SPDR-007 COMPLETE — operator disposition NOT_WORTH (price-only S1/S2 spine; a P-01 confirmation, HYP-S1 master gate).** The Protection quantile REPRODUCES on CONFIRM (pooled calib_err +0.030/+0.028, both ≤0.05; source framework-falsifier #1 **not** triggered on reproduction), **but adds ≈0 over a matched cross-session unconditional entry**: R2 race contrast −0.010 sits at gross breakeven and is **below the cost-adjusted breakeven on all 5 majors** (w−p0ᶜ −0.05 to −0.14); R5 excursion-asym contrast +0.090, day-clustered CI [−0.23,+0.32] (WASH, MDE 0.50); R3 finite-only ≈0; R4 negligible. P-01 confirmed (control q̂ within ~10% of signal; control hits signal level 67.5%). Per-symbol heterogeneity: SOL R1 **BROKEN** (+0.105) masked by pooling (L-03). Integrity clean: tripwire **NO_MATERIAL_EDGE** (material-edge precondition, D-2), bite corr 0.77; freeze/fence/causal/no-per-level-Δ/no-local-accounting asserted. QA run 1 (design) REVISE→resolved; runs 2–3 (code+analyst) APPROVE. Two deviations ratified: D-1 cross-session control, D-2 material-edge tripwire (design amendments 10–11; 0L/6T/5N). **Scope: signed flow (Δ) UNTESTED — the family's central warrant is deferred to checkpoint-015; tested the daily US-open session / 15-min IB / single-session (~23h) hold on 1-min bars only — not the 8h funding cadence, not micro/structural holds, no higher-timeframe resampling.** Family status **unchanged (REGISTERED)** — close/keep is a retrospective act. 0 slots, 0 counted reads, holdout SEALED. Report `python/experiments/SPDR-007/report.md`; disposition `analysis.md` §6. **Next: SPDR-008** (signed-trap breadth, S1+S3). |
| 2026-07-21 | **SPDR-008 COMPLETE — operator disposition NOT_WORTH (S3 signed-trap breadth; the family's deferred SIGNED warrant).** Measured trap-load monotonicity (`trap_load = poke_side × Σ delta_ratio_resid`, signed by the aggressor split) is a **powered null** on all three boundary types tested INDEPENDENTLY (IB opening-range / PVA prior value-area / PRIOR prior extreme): T1 ρ −0.015/+0.023/−0.033, MDE ≈0.02 on 4.6–10.9k events/cell; the one whiff (PVA DESIGN p=0.052) sits below its own MDE and **flips negative on CONFIRM**; T2 HIGH−LOW tier CI spans zero on every boundary/band, sign-unstable. **K=3 ruled NOISE** — IB 6/96 "supported" but 7 total qualifiers vs 6.0 null expectation and vs 10 anti-monotone mirror cells; scattered non-connected names; weak sign-only CONFIRM reproduction (winner's-curse); pooled IB ρ itself negative. The **only reproducing edge is UNSIGNED P-01 geometry** — traps revert ~30–55 bps more than matched random-timing entries (T4, PVA/PRIOR both bands) and ~+0.97 IBw more than ordinary touches (T3), but NOT load-dependent → failed-break price geometry, already NOT_WORTH at SPDR-007, twice-dead (P-01), non-promotable; **measured flow adds nothing over price shape.** Integrity clean: causal ≤t−1 verified on all 16,669 events, tripwire NO_MATERIAL_EDGE (correct — no signed edge) with bite 0.53–0.92, no-per-level-Δ + no-local-accounting + frozen-pin all PASS, emission VALID. 194 A5-fitted signed universe (breadth denom 296; survivorship caveat binding), 16,669 DESIGN / 26,348 CONFIRM traps. New shared module `xen.sigbar.trap` (IB byte-identical to frozen apparatus). Amendments 1–8 (0L/5T/3N). QA runs 1–3 (design REVISE→APPROVE; code REVISE→operator-directed full adjudication machinery + tripwire fix → re-run). **The signed-value block (S9 absorption / S14 CVD divergence) is a DISTINCT claim (ckpt-015 Phase 6) — this NOT_WORTH does not pre-judge it.** Family status **unchanged (REGISTERED)** — keep/close is the checkpoint-014 retrospective. 0 slots, 0 counted reads, holdout SEALED. Report `python/experiments/SPDR-008/report.md`; disposition `analysis.md` §6. |
| 2026-07-21 | **Designer Addendum v1.1 received** (`checkpoints/2026-07-20-014-signed-auction-structure/signed_bar_framework_addendum_v1_1.md`). Converts framework grades from hypothesis to empirical state (Part 1: S1 DEMOTED→operational-anchor; S3 Δ+ DELETED; S2/S3-base/A6/A8 CONFIRMED-as-measurement; §2.5 UNAVAILABLE; M1 SUSPENDED / M4 claim-2 deleted). Adds 10 protocol-hardening rules (Part 2 §2.1–2.10) — master-gate conjunction, mirror-tail multiplicity, per-symbol census, control-family spec, finite guards, robust excursion stats, anchor vocabulary, leak-tripwire interpretation, breadth+net prerequisite, horizon-menu closure. Revised experimental path (Part 3) supersedes Appendix B Phase 6 onward. **Addendum GOVERNS the base document where they conflict.** |
| 2026-07-21 | **Checkpoint-014 CLOSED — operator-directed retrospective** (`checkpoints/2026-07-20-014-signed-auction-structure/retrospective.md`). Phases 0–5 complete; four TRAIN-only items; 0 counted reads; holdout SEALED. **Family KEPT `REGISTERED` — no transition** (closure gated on the S9 3rd-null per Addendum §3.3). Signal-level grades carried onto this card's status header. **Next: checkpoint-015** (`checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md`, DRAFT — operator D1–D5 pending): **SPDR-009** S9 absorption marginal-value screen (master go/no-go, gate-free/location-qualified, signed−unsigned on identical events), **SPDR-010** S14 divergence (memo-gated rider), **INFR-019** tick-floored spread reconstruction (parallel, non-blocking). |
| 2026-07-22 | **Ckpt-015 D7 SIGNED — pair set held at four; closure rule restated.** INFR-020's count-only candidate census (an upper bound on event supply, before τ/refractory/arm split) measures D1 95,836 · D2 9,497 (5,226 on its 72-symbol core) · D3 2,974 (933 on 47) · **D4 640 (162 on 31, carried by 12 instruments)**. Two consequences: D6's motivating "19 events" was a **ten-instrument sample**, not a property of 1d/1m — the widening now rests on its economic argument (hold-invariant ~11 bps fee, more time to clear it), not on event supply; and **D4 is pre-declared power-limited**, running for horizon coverage with an UNPOWERED/INCONCLUSIVE outcome expected and explicitly not a null. Closure rule accordingly restated (see preconditions). No status transition, no read, no slot. |
| 2026-07-22 | **INFR-020 COMPLETE — operator accepted Run-10 apparatus pin `5f170b71…`.** Checkpoint-015 D6 four-pair prerequisite is frozen: 194-symbol 1m/5m/15m/1h baselines/thresholds, sessions, causal 1m structural levels, shared candidate availability, coverage, and count-only zone censuses. QA Runs 1–9 REVISE → Run 10 APPROVE; all nine hashes and full battery pass. Apparatus only: no outcome, no slot, no TEST/holdout read, and no family status change. **SPDR-009 developer implementation next.** Report `python/experiments/INFR-020/report.md`. |
| 2026-07-22 | **SPDR-009 COMPLETE — operator disposition NOT_WORTH (S9 signed-absorption marginal value; the family's flagship "signed value where price is blind" claim).** Four pre-registered domain pairs under one frozen design (D1 1d/1m · D2 1h/5m · D3 4h/15m · D4 1d/1h), 1-minute outcomes and levels in all four (D6.3), money floor first. **D1 is a powered null on every leg of the §4 conjunction:** T1 marginal contrast **+1.81 bps** CI [−3.62,+7.09] vs **MDE 5.5** (H5) and −3.41 bps (H10) on 7,186 events / 311 S9 / 6,550 BASE / 162 symbols / 169 days; S9−MIRROR +5.29 vs MDE 7.5 (WASH); **T2 ρ = +0.008** (p 0.263) inside a 2,000-seed derangement null; T4 vs matched random timing +2.39 bps CI through zero; T5 bare-touch +1.50 CI through zero; **S9 median return 0.0 bps against an 11.3–13.0 bps floor** (AT_OR_BELOW_FLOOR). Both zone sensitivities agree and the **tighter** pool is *more* negative (P_WIDE −8.31/−13.18 bps; retained 0.25×ib_width +0.60/−3.19) — the zone-dilution escape is closed. **D2/D3/D4 UNPOWERED** at 16 / 2 / 0 S9 events (recorded horizon-covered but inconclusive; D4 exactly as pre-declared under D7). Candidate supply collapses 95,836 → 5,226 → 933 → 162 on the pairs' liquid cores, so coarsening buys wall-clock against the hold-invariant ~11 bps fee and destroys the events — the D6 economic rescue fails structurally. **Most informative negative:** the MIRROR arm is *larger* than S9 (325 vs 311) and behaves identically — the measured split does not name a losing side at the flat-price, high-volume bar the mechanism singles out. Integrity clean (fences, causal ≤t−1, COMPLETE-window, no per-level Δ, no local accounting, frozen-hash re-verify); tripwire **NO_MATERIAL_EDGE ×4** with bite passing and **CF\* UNDERIVABLE** — explicitly *not* a clean bill of health (Addendum §2.8). Caveats on the record: **78% of located D1 events dropped** for no contiguous 1-minute outcome path (activity conditioning, post-entry selection); **16.3% of retained events return exactly 0.0 bps** at H5 (micro horizon is partly dead air); analyst stage **waived** by the operator (no `analysis.md`); CONFIRM band not spent. 0 slots, 0 counted reads, holdout SEALED. Report `python/experiments/SPDR-009/report.md`. |
| 2026-07-22 | **Checkpoint-015 CLOSED — family CF-SIGAUC-001 `REGISTERED` → `CLOSED`** (operator-directed retrospective; `checkpoints/2026-07-21-015-signed-value-absorption-screen/retrospective.md`). **D8 SIGNED:** close on the D1 powered null, amending the D7 minimum from "D1 and D2" to "D1 with every pair's power state named" — D2's 16 events are a structural event-rate fact, so the D7 form made the family unclosable by construction (the same defect D7 corrected for D4). Third powered null delivered ⇒ Addendum §3.3 closure condition met on the session + micro horizons. **S9 DELETED** under the binary-mechanism rule. **Recorded costs of the close:** SPDR-010 (S14 CVD divergence) **never run** — untested, not covered by this close, and a reopening entry point; INFR-019 tick-floored spread **never built** — no net claim in this family was ever admissible; structural and funding-cadence horizons never screened (Addendum §2.10 only partially satisfied). Durable apparatus retained. 0 slots, 0 counted reads, holdout SEALED. |

---

## 11. Operator sign-off

| Item | Status |
|---|---|
| D0 content freeze | **Complete** (2026-07-20) |
| Family scope: single family, signals/models = strategies within it | **Signed** (operator, 2026-07-20) |
| Register family in live ledger | **Done** — checkpoint-014 D1 APPROVED (operator, 2026-07-20) |
| P-01 distinctness sign-off (§5) | **Signed** — checkpoint-014 D6 APPROVED, option (a) with the stated mitigation (operator, 2026-07-20) |
| Assign experiment IDs | **Assigned** — INFR-017, INFR-018, SPDR-007, SPDR-008 (checkpoint-014 §4) |
| Source-adherence resolutions (6 items) | **Signed** (operator, 2026-07-20) — checkpoint-014 § Adherence-review resolutions |
| Checkpoint-014 close + KEEP REGISTERED + grade conversion (Addendum v1.1) | **Operator-directed 2026-07-21** — retrospective CLOSED; family kept; grades recorded |
| Checkpoint-015 open (S9 absorption screen path) | **SIGNED D1–D7** — INFR-020 Run-10 pin `5f170b71…` accepted 2026-07-22; rollover deferred indefinitely; SPDR-009 implementation next |
| Closure rule in force (D7, 2026-07-22) | ~~Powered null on **every pair that reaches power at realised n, minimum D1 and D2**~~ — **SUPERSEDED by D8.** |
| **Closure rule as applied (D8, 2026-07-22)** | **Powered null at D1, with every pair's power state named in the closure statement.** D2's 16-event shortfall is a structural event-rate fact on this venue/band, so the D7 "minimum D1 and D2" form made the family unclosable by construction — the same defect D7 itself corrected for D4. |
| **Checkpoint-015 close + family CLOSED** | **Operator-directed 2026-07-22** — retrospective CLOSED; family `REGISTERED` → `CLOSED` on the third powered null (SPDR-009 D1); S9 DELETED. Recorded costs: **S14 never run**, INFR-019 never built, structural/funding-cadence horizons never screened. `CLOSED` ≠ "tested everywhere". |
