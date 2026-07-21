# CF-SIGAUC-001 — Signed Auction Structure from 1-Minute Bars

**Status:** **`REGISTERED` (2026-07-20, checkpoint-014 D1 — operator-signed)** — registration act only, no status transition. 0 slots · 0 counted TEST reads · holdout SEALED. Active sequence: INFR-017 ✅ → INFR-018 ✅ → **SPDR-007** (master gate) → SPDR-008.
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
