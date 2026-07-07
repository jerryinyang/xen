# CF-CSRR-001 — Cross-Sectional Consensus-Residual Reversion (basket)

**Status:** `RETIRED (2026-07-07, operator-signed, checkpoint-009 retrospective)` — availability
kill criterion met: substrate reverts on both baskets (VR<1) but no mechanism-faithful (hedged)
construction clears multiplicity/the hardened CI on either basket, and the best lead (USTEC,
EXP-024) is effect-at-MDE. Retired at **0 slots / 0 counted TEST reads**, holdout sealed. Model
selection never met → EXP-023 (tradability) + HYP-004 (confirmatory) never scoped. Retrospective:
`docs/experiments-docs/checkpoints/2026-07-06-009-cf-csrr-001-cross-sectional-residual-reversion/retrospective.md`.
Prior status: `REGISTERED (2026-07-06). G0 PENDING`.
**Family ID:** CF-CSRR-001. **Chapter:** 02 (cTrader-primary era).
**Baskets:** Currencies (10, VAL-005, ready) + Indices (10; 4 loaded, 6 pending
INFR-005/VAL-007 — **Indices arm design-gated on VAL-007 PASS**). **Domain:** 4-hour only.
**Family directory / origin (faithful variant provenance):**
`docs/experiments-docs/families/cf-csrr-001/origin.md`.
**Suggestion provenance:** `.ignore/temp/new-family/{r1-dlc,r2-ksd,r3-mlg,r4-tpg,verdict}.md`.

## Thesis

On a basket of co-moving instruments, one member's move away from the **cross-sectional
consensus** of the basket is dominated by transient idiosyncratic flow (session opens,
rebalances, one leg's thin liquidity, lagged information propagation) rather than genuine
member-specific repricing, and therefore **reverts toward the consensus** within a bounded
horizon. The consensus is a non-parametric statistic (median / equal-weight / weighted-implied)
computed across the basket at each bar — no beta, covariance, cointegration, or rolling z-score.
The edge, if any, is the residual-reversion **net of honest round-trip cost at a non-adverse
fill**; availability (does the residual revert) is screened first and family-agnostically.

This targets the **cross-sectional / relative-value cell** of the availability 2×2 — the open
frontier after single-series directional price-geometry was refuted twice (KB
`families-explored.md`). It is a *reversion* endpoint, distinct from CF-XSECT-001's
*directional relative-strength* endpoint (NOT_ADMITTED).

## Registered variants (5) — one component per axis to characterise

Full verbatim source text: `families/cf-csrr-001/origin.md`. Summary:

| ID | Name | Source | Distinguishing component |
|---|---|---|---|
| V1 | Median-Basket Deviation, single-worst-only | r1-dlc S2 | **median** consensus; **single-worst** selection; median-index hedge |
| V2 | Consensus Residual Basket | r4-tpg §2 | **equal-weight mean of normalized moves** ("one vote each") |
| V3 | Implied Fair-Price Level | r4-tpg closing obs | **weighted implied price-level** consensus (non-equal weights) |
| V4 | Cross-Sectional Z-Spread | r2-ksd I1 | **÷ cross-sectional dispersion σ_t** (z-normalized residual) |
| V5 | Active-Entry / Passive-Exit (remodel) | programme | **active confirmed-breach entry + passive rolling-consensus exit + time-only stop** |

Shared 7-axis component space (A consensus estimator · B residual normalization · C selection ·
D hedge · E entry execution · F exit/stop · G threshold): see origin.md table. The family bet is
that **characterising each axis individually selects one model** that survives net of cost.

## Fixed first-branch definitions (G0)

1. **Basket state per bar:** each member's log return from a causal **rolling session/daily
   anchor** — `r_i(t) = ln(P_i(t)/anchor_i)`, anchor = most recent daily/session rollover 4h
   close (own timeline, causal reset). The residual **accumulates** intraday; reversion = the
   accumulated gap closing (matches the thesis + V1/V2/V5 — NOT a one-bar return). Accumulation
   horizon pinned to the **measured residual half-life** (disclose the HL fit; extend the anchor
   if HL runs multi-day). Decisions on confirmed bars only (`≤ t-1`), acted at next bar open;
   open-to-open returns. *(Corrects the earlier terse "prior 4h close" G0 line, which was a
   1-bar definition inconsistent with the accumulated-dislocation mechanism; pre-measurement,
   0 slots — clean definition fix. The 1-bar / V4 residual-return-autocorrelation build is a
   distinct mechanism, registered as a deferred branch below, not this baseline.)*
2. **Consensus `m(t)`** = the axis-A estimator over the basket members present at t
   (median / equal-weight mean / weighted-implied). Residual `s_i(t) = r_i(t) − m(t)`
   (axis-B normalization optional: raw or `÷ σ_t`).
3. **Selection:** axis-C — single-worst `max|s_i|` (V1/V5) or all `|s_i|>k` (V2/V3/V4).
4. **Hedge:** axis-D — median-index 1:1 (V1/V5), basket, or within-basket long/short.
5. **Currencies consensus (§ below):** USD-strength alignment, not naive quote median.
6. **Domain:** 4-hour only. Baskets: Currencies (ready) + Indices (VAL-007-gated).
7. **TRAIN-only** for the whole checkpoint (first-70%→TRAIN slice); TEST band never emitted;
   holdout sealed; 0 slots, 0 counted reads at screen + validatory stages by construction.

## Currencies consensus construction (operator decision 2026-07-06)

The consensus-residual premise assumes **one dominant common factor**. The Indices basket has
one (global equity risk). The Currencies basket (EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD,
AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY) mixes USD-quoted majors and JPY crosses with opposing
USD exposure — a naive cross-sectional median of raw quotes is factor-incoherent. **Binding
first-branch rule for the Currencies arm:** align every leg to a common **USD-strength factor**
(sign USD-base vs USD-quote pairs consistently; handle JPY crosses explicitly by decomposing to
their USD legs where possible) before forming the consensus/residual. The USD-strength
alignment is itself a **registered component** whose coherence is validated in EXP-021 (if the
aligned residual is not mean-reverting, the Currencies arm dies there). A naive-median contrast
is a registered non-baseline branch (disclosure only).

## Execution model (V5, selected as the tradability vehicle — lessons-driven)

The MR arc retired CF-MR-003/004 at the **entry seam**: a passive limit resting at the deviation
price is *adverse selection* (fills when divergence continues). V1–V4 all use passive-limit
entry. The family's tradability experiments therefore use the **V5 execution split**:
- **Entry ACTIVE** on the confirmed-breach event we measure (market at next open), not a resting
  limit at the extreme.
- **Exit PASSIVE** at the rolling consensus parity `anchor_i·e^(m(t))`, re-pegged each bar
  (reversion arrives toward the resting order = favourable selection).
- **Time-stop only**, no price stop (adverse-selection magnet); catastrophic guard ≈3× entry
  residual, disclosed.
- **Single-worst, one position, median-index 1:1 hedge, no hard leg cap** (cap-lock was the
  CF-MR-005 killer; single-position makes it structurally impossible).

Availability screens (EXP-021/022) are execution-agnostic — they characterise whether the
residual reverts, independent of fill. Execution axis E is decided at the validatory tier.

## Parameters & allowed domains

| Param | Role | Allowed | Fixed at |
|---|---|---|---|
| consensus estimator (axis A) | fair-value | {median, equal-wt mean, weighted-implied} | swept in EXP-021/022 |
| normalization (axis B) | residual scale | {raw, ÷σ_t, range-scaled} | swept |
| selection (axis C) | position count | {single-worst, all>k} | swept |
| hedge (axis D) | reference leg | {median-index, basket, within-L/S} | swept |
| threshold k (axis G) | trigger | {trailing-median max|s|, fixed-bps, fixed σ-mult} | coarse; pre-registered |
| time-stop T (axis F) | exit horizon | {1, 2, 3 sessions} in 4h bars | pre-registered validatory |
| domain | bar | **4h only** | fixed |

Post-hoc parameter changes = new registered branches (multiplicity rule 4), not revisions.

## Hypotheses

| ID | Question | EXP | Status |
|---|---|---|---|
| HYP-001 | **Currencies availability + component characterisation.** On the Currencies basket (USD-strength consensus), 4h TRAIN, execution-agnostic: is the consensus-residual mean-reverting (VR<1 / residual autocorr<0), and which (A×B×C×D) combination maximises signal-conditional residual-reversion Δ over a matched random-index + random-timing control? | EXP-021 | **COMPLETED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Substrate reverts (VR(2)<1 on 28/28 4h cells, HL~1.4); but 0 hedged (mechanism-faithful) cells survive max-stat multiplicity on any instrument — sole family-wise survivor AUDUSD *unhedged* +9.4 bps fw_p .008 = market drift (hedged twin fw_p .68). AUDUSD/USDCAD = disclosed leads (not booked). Leak-clean, holdout sealed, 0 reads/slots. |
| HYP-002 | **Indices availability + component characterisation** (mirror of HYP-001 on the native single-factor equity basket). Indices basket 10/10 admitted (VAL-007 PASS 2026-07-06). | EXP-022 | **COMPLETED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Substrate MR confirmed; no hedged construction clears primary max-stat (0/9 fw_p<.05); US-cash powered null generalises to HK50 (Addendum A1); EU50 UNPOWERED; USTEC disclosed member-specific lead. Family status unchanged — disposition → checkpoint-009 retrospective. |
| HYP-002b | **US-bloc session-anchor availability primary** (pre-registered follow-up to the EXP-022 USTEC lead). Frozen construction (R_US bloc {USTEC,US500,US2000,US30}, session-open anchor, median/raw/hedged, all>k, h=2·HL); multiplicity family = the 4 members (Holm); binding bar = the hardened block-boot CI USTEC failed in EXP-022. Resolves (a) power vs effect-dilution and (b) bloc mechanism vs USTEC-only artifact. Controlled thesis-shopping from a disclosed lead — TRAIN-only, in-sample-honest. | EXP-024 | **COMPLETED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Substrate reverts; no member clears the hardened CI at the binding all>k/hedged construction (all powered UNPOWERED-by-MDE; §8 dilution confirmed). Single-worst continuity reproduces the EXP-022 USTEC pattern (p_perm 0.009 but hardened ci_low −1.15) — lead is effect-at-MDE, USTEC-specific, retired at 0 cost. No sibling reproduces. Read-out does NOT graduate USTEC to EXP-023. **Family status UNCHANGED** — disposition → checkpoint-009 retrospective. |
| HYP-003 | **Tradability of the selected model.** Take the single model constructed from EXP-021/022 observations; implement price-primary in cTrader with the V5 active-entry/passive-exit/time-only execution model; net of honest round-trip cost; vs the three-twin control battery (random-timing, random-index, momentum-signed inverted); TRAIN robustness (block bootstrap, both halves). | EXP-023 | **NOT SCOPED — family RETIRED at checkpoint-009 (2026-07-07).** Model-selection gate never met (no mechanism-faithful construction cleared availability on either basket); no tradability read run. 0 reads, 0 slots. |
| HYP-004 | **Confirmatory TEST read** of the frozen selected model per stratum. **PRE-DECLARED gate only; not scoped, no read spent** until HYP-003 survives validation. | — | **NEVER SCOPED — family RETIRED (2026-07-07).** Gate not reached; 0 reads spent, holdout sealed. |

## Exploratory / validatory / confirmatory staging (operator decision 2026-07-06)

- **Exploratory (TRAIN-only, 0 reads):** EXP-021 (Currencies), EXP-022 (Indices, VAL-007-gated)
  — substrate + component characterisation; select one model.
- **Validatory (TRAIN-only, 0 reads):** EXP-023 — tradability of the selected model under honest
  cost + the three-twin battery + TRAIN out-of-sample robustness. **Cost requirement:** charge
  `xen.evaluation.round_trip_cost_bps` against the **netted episode/turnover** object, never
  per-signal (per-signal costing overstates fees under signal overlap); pin `commission_basis`
  (per_side vs round_turn) and any cross `base_usd_rate` before the binding read. See
  knowledge-base `evaluation-framework.md` § Trading-cost model.
- **Confirmatory (pre-declared, NOT spent this checkpoint):** HYP-004 — a single counted TEST
  read (cap 2/stratum) on the frozen, hash-pinned selected model, **only if** EXP-023 clears the
  pre-declared gate. Holdout remains sealed; deployability is a separate, later, governed step.

## Kill criteria (predeclared, checkpoint-level)

- **Substrate:** if the aligned consensus-residual is not mean-reverting on a basket (VR≥1 /
  autocorr≥0 across the swept estimators) → that basket's arm dies at 0 slots.
- **Availability:** if no (A×B×C×D) combination separates from BOTH the random-index and
  random-timing twins beyond the multiplicity-adjusted permuted-axis null at the realized cell
  count → family retires at the retrospective, 0 reads spent.
- **Attribution:** any candidate positive that the **momentum-signed inverted twin** matches or
  beats is drift-carry, not reversion (the USDCAD lesson) → not booked.
- **Cost/capture:** if the residual-reversion capture < honest round-trip at a non-adverse fill
  on every stratum → NOT-TRADABLE (the CF-MR-002/003 cost wall) → retire.
- **Integrity:** any tripwire failure (holdout touch, estimand reconciliation, causal-fill,
  provenance) → REJECT the run, fix, rerun; never book around it.

## Confirmatory gate (HYP-004, pre-declared — spend nothing until met)

A counted TEST read is authorised only if ALL hold on TRAIN validation (EXP-023):
1. selected model net-of-cost per-stratum CI_low > 0 on ≥ a pre-registered minimum stratum count;
2. beats all three twins (random-timing, random-index, momentum-inverted) per stratum;
3. survives block-bootstrap CI (INFR-004/L-20 hardened) + both-temporal-halves;
4. effect ≥ pre-registered MDE (bite-valid, L-12/L-17 short-band caveat checked);
5. model + params hash-pinned before the read; stratum counted-read tally stated (cap 2).

## Distinctness from retired families (P-01/P-02 compliance)

- **Not CF-MR-002..005:** those are single-instrument / own-price entry-conditioned directional
  reversion. CF-CSRR-001 conditions on a **cross-sectional** residual (member vs basket
  consensus), not own-price state. The reference is other instruments, not the instrument's own
  history.
- **Not CF-XSECT-001:** that screened a **directional relative-strength** endpoint (momentum-
  shaped, NOT_ADMITTED). This is a **reversion** endpoint with a consensus anchor and a
  non-adverse execution model.
- **Not CF-VOLHARV-001:** that is unconditioned two-sided path-structure harvest (E[gross]=0
  founding object). This is entry-conditioned on a measured cross-sectional dislocation.
- Pitfalls-ledger re-open standard ("a genuinely new mechanism, not another price-pattern on a
  directional target") is met: cross-sectional consensus residual, reversion target,
  active-entry/passive-exit execution that no prior family used.

## Implementation path

Python characterisation first (execution-agnostic availability, EXP-021/022) → cTrader
strategy-host price-primary for tradability (EXP-023, native orders, m1 fills, V5 execution) →
`xen.adjudication` canonical estimands; no local accounting. Real prices; `CloseTime`/
`SourceCloseTime` alignment; open-to-open returns; global holdout never loaded.

## Evidence ledger

| Date | Item | EXP | Result |
|---|---|---|---|
| 2026-07-06 | Registration (G0 pending); origin document + checkpoint-009 scope | — | Family REGISTERED; 5 variants + 7-axis decomposition booked; Currencies-first, Indices VAL-007-gated; confirmatory pre-declared not spent. `families/cf-csrr-001/origin.md`, checkpoint-009 design.md |
| 2026-07-06 | HYP-002 Indices availability + A×B×C×D component screen (native single-factor equity basket, 4h TRAIN, execution-agnostic; all 3 builds × 2 anchors + Addendum A1 coverage correction) | EXP-022 | **NOT SUPPORTED (availability; operator verdict).** Native equity mirror confirms EXP-021. Substrate MR unanimous (VR(2)<1 on 40/40 primary cells, HL ~0.8–1.9 4h-bars; 90% across builds). Signal-conditional **idiosyncratic (hedged) reversion does NOT separate** at primary (N×P): 0/74 powered cells clear uncorrected ci_low>0; max-stat over 16 cells → 0/9 instruments fw_p<0.05 (best JP225 0.33). Every primary cell UNPOWERED for the ≥1 bp band (MDE 3.9–21.7; `argmax\|s\|` concentrates events). 90%-coverage 4h filter → EU50/HK50 0 events (US-cash sub-basket; EU/Asia UNPOWERED not contradicted, B-5). **Addendum A1** (min_coverage 0.90→0.50) powered HK50 (0→519) = clean null → US-cash NOT-SUPPORTED **generalises**; EU50 structurally UNPOWERED (4h+1D). **USTEC (R_US bloc + session-open anchor, hedged) = disclosed member-specific lead**: +4.7–4.8 bps, p_perm .002, genuinely idiosyncratic (α+4.71 vs raw+0.30, β1.19; siblings null), tripwire-clean, but underpowered (hardened ci_low<0, effect≈MDE) + non-primary → registered-branch candidate, NOT support (parallels AUDUSD/USDCAD). Leak-clean (tripwire ρ→0), holdout sealed, 0 counted reads, 0 slots. **Family status UNCHANGED** — availability kill not literally met (USTEC separates in a non-primary construction), substrate kill NOT triggered; disposition reserved for checkpoint-009 retrospective. `python/experiments/EXP-022/report.md`, `families/cf-csrr-001/INDEX.md` |
| 2026-07-06 | HYP-001 Currencies availability + A×B×C×D component screen (USD-strength consensus, 4h TRAIN, execution-agnostic) | EXP-021 | **NOT SUPPORTED (availability; operator verdict).** Substrate MR confirmed (VR(2)<1 on 28/28 4h cells, HL~1.4 4h-bars; VR<1 on 1D). Signal-conditional idiosyncratic reversion does NOT clear the max-stat multiplicity: **0 hedged (mechanism-faithful) cells survive on any instrument**; sole family-wise survivor AUDUSD *unhedged* +9.4 bps fw_p .008 = market **drift** (hedged twin +4.5 fw_p .68). Heterogeneous — USDJPY continues (−2.4, 0/16 cells+, dominates single-worst 635 events = 2021-23 JPY trend). Variants V1/V2/V4 pooled ~0.4-0.8 bps, 0/7 survive; V3/V5-execution untested. Alpha/beta: AUD/NZD ~half beta; USDCAD cleanest alpha (+3.3, still fw_p .54). Leak-clean (tripwire ρ→0), holdout sealed, 0 counted reads, 0 slots. **AUDUSD/USDCAD = disclosed leads** (moderate ~17-21% AUDUSD 4h time-in-market; not booked as support). Disclosures: h=2·HL not load-bearing (sign stable 1/2/3×HL); 1D (NON-REGISTERED branch) reverts but UNPOWERED. **Family status UNCHANGED** — disposition reserved for checkpoint-009 retrospective (the literal availability kill criterion is not met: AUDUSD unhedged separates). `python/experiments/EXP-021/report.md`, `families/cf-csrr-001/INDEX.md` |
| 2026-07-06 | HYP-002b US-bloc session-anchor availability primary (controlled follow-up to the EXP-022 USTEC lead; R_US bloc, session-open anchor, median/raw/all>k/hedged, 4h TRAIN, execution-agnostic; binding bar = hardened block-boot CI) | EXP-024 | **NOT SUPPORTED (availability; operator verdict).** Controlled re-test resolves the EXP-022 open question (underpowered vs effect-at-MDE) → **effect-at-MDE.** Substrate reverts (VR(2)<1 all 4 members, HL ~1.5-1.8 4h-bars). Binding all>k/hedged: **no member clears the hardened CI** — USTEC +1.08 bps ci [−3.75,+5.88] MDE 4.83; US2000 +0.65 MDE 5.08; US30 +0.10; US500 n=39 UNPOWERED (B-5). All powered members UNPOWERED-by-MDE; §8 pre-declared trade-off confirmed (all>k dilutes per-event effect from single-worst +4.26 → +1.08 bps, landing at the MDE). Single-worst continuity **reproduces EXP-022's USTEC pattern exactly** (+4.26 bps, p_perm 0.009, hardened ci_low −1.15 — still fails the binding bar); no sibling reproduces (US2000 0.205, US30 0.831). Lead = real, reproducible cross-sectional i→i linkage at the detection floor, USTEC-specific — not a tradable/hardened-CI-surviving edge. **EXP-022 USTEC lead retired at 0 cost.** Leak-clean (tripwire ρ→0), holdout sealed, 0 counted reads, 0 slots. Read-out does NOT graduate USTEC to EXP-023. **Family status UNCHANGED** — disposition reserved for checkpoint-009 retrospective. `python/experiments/EXP-024/report.md`, `families/cf-csrr-001/INDEX.md` |
