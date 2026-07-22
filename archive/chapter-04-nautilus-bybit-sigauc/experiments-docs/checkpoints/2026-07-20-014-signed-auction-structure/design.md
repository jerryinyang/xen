# Checkpoint 014 — Signed Auction Structure: Instrument Build → Spine → Breadth (design)

**Opened:** 2026-07-20 · **Status:** **DESIGN SIGNED** — operator decisions D1–D6 recorded 2026-07-20 (§Operator decisions); CF-SIGAUC-001 **APPROVED + REGISTERED** (§2 executed). No status transitions (those remain retrospective acts). Execution proceeds item-by-item under the §4 gates.
**Container for:** INFR-017 (signed-bar lane + provenance + baselines), INFR-018 (instrument build + freeze), SPDR-007 (statistical spine — master go/no-go), SPDR-008 (breadth sweep).
**Family:** CF-SIGAUC-001 — `docs/signal-registry/candidate-families/cf-sigauc-001.md` (D0 COMPLETE, registration proposed §2).
**Source methodology:** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — normative for signal definitions, falsifiers, and phase order. This checkpoint maps its Appendix B phase plan onto Xen lanes (INFR → SPDR → XENA); **the source experiment plan is preserved and only adapted for lane machinery** — it does not re-decide signal content.
**Lane:** INFR → SPDR → XENA (XENA deferred to checkpoint-015).
**Operator resolutions (2026-07-20 adherence review):** (1) CONFIRM-bank holdout adaptation accepted; (2) pooled anchors primary, with few-asset per-instrument spot-checks; (3) P-10 passive-limit ban **lifted for this family** — source limit-style entries admitted; dual capture (limit vs market-on-confirm) for comparison; (4) Phase-3 kernel gap closed (§4 HYP-I4); (5) thin local history accepted with pooling; (6) Xen scaffolding fine so long as Appendix B order/claims survive.

## Preconditions (verified on disk 2026-07-20)

| Item | State |
|---|---|
| Checkpoint-013 | **CLOSED 2026-07-19** (operator-signed); CF-EPSOSC-001 RETIRED, CF-HTFCAP-001 CLOSED-CHARACTERISED |
| Engine | nautilus_trader==1.230.0 pinned |
| Catalog | `data/catalog/` — 894 ADMITTED, 672M bars, fence PINNED `35d3375e…`; **Bar = OHLCV only** |
| Signed columns | `INFR-011/data/staging/bars/*.parquet` — 904 symbols with `BuyVolume`/`SellVolume`/`NTrades`/`SpreadAbs`/`SpreadBps`; **not in catalog, not engine-readable** |
| Orderflow apparatus | `xen.orderflow` (INFR-013) — custom Data types + catalog schemas, round-trip proven; no bulk collection, detectors stubbed |
| Governance | INFR-012 rebind 10/10; estimand gate v2 (STUB fails); INFR-016 report layers active |
| XENA pin | `abbb1842…` = CLS-FILTER low + CLS-EPISODE low — **neither class established for sparse session-event objects** |
| Holdout | SEALED (≥ 2025-01-08); both sanctioned shots spent on legacy datasets; **no TEST contact anywhere in this checkpoint** |
| Chapter | 04 open. Rollover was flagged available at ckpt-013 §6.3 — **deferred, operator's call; not a blocker** |

## Objectives

1. Register CF-SIGAUC-001 as a formal REGISTERED family (§2).
2. Build and validate the measuring instruments before any hypothesis is tested — the source's governing principle: *never test a hypothesis whose measuring instrument is itself untested* (§3, §4).
3. Reach the source's **master go/no-go** (Phase 4 statistical spine) at the earliest honest point, with the money-unit floor computed before it (§4).
4. Map where the logic pays across the cross-section (Phase 5) — the tier's stated comparative advantage (§4).
5. Resolve the holdout mapping and universe rules for this family as written, reproducible declarations (§5, §6).

---

## §1 Phase mapping — source Appendix B → Xen lanes

The source defines nine phases in three stages. This checkpoint takes **Stage I plus the master gate and the breadth survey**; the expensive hypothesis-bound work sits behind them, in checkpoint-015.

| Source phase | Nature | Xen item | In this checkpoint |
|---|---|---|---|
| 0 — freeze; A8 provenance audit; seasonal baselines | procedure | **INFR-017** | ✅ |
| 1 — anchor selection (24/7 venue: mandatory) | calibration | **INFR-018** | ✅ |
| 2 — race the A6 acceptance discriminator | calibration | **INFR-018** | ✅ |
| 3 — validate instruments (kernel, class clustering) | calibration | **INFR-018** | ✅ |
| 4 — reproduce the statistical spine (S1+S2) | hypothesis — **master go/no-go** | **SPDR-007** | ✅ |
| 5 — breadth sweep (S1+S3 across cross-section) | screening survey | **SPDR-008** | ✅ |
| 6 — signal-level tests (incl. the signed-value block; kill order as source Phase 6) | hypothesis | XENA universe(s) — claims order unchanged | ⛔ ckpt-015 |
| 7 — model assembly (M1–M5 distinct claims only; M5 last) | hypothesis | XENA universe(s) | ⛔ ckpt-015 |
| 8 — deployment calibration | monitoring | programme ops if ever promoted | ⛔ out of programme research scope |

**Why the boundary sits after Phase 5.** The source states it directly: Phases 0–4 are where the project dies honestly and cheaply, and Phase 5 spends breadth before depth so the expensive phases run only where breadth found soil. Cutting the checkpoint here means a dead family costs four TRAIN-only items and **zero counted reads**. Checkpoint-015 must still run Phase 6 then 7 **in source order** (S3 load-monotonicity → … → signed-value block → S15 last → M1–M5 with M5 last) inside XENA; lane change is packaging, not reordering.

**Stage-rigor rule (binding, source Appendix B).** A Stage I output is a *parameter or a validated instrument*, never evidence that anything works. Tuning inside INFR-017/018 is free; each phase's **kill-gate is a hypothesis** and carries full rigor. A Stage II result computed with an unfrozen Stage I instrument is unattributable and re-runs.

## §2 REGISTERED ledger rows — CF-SIGAUC-001 (D1)

Registration-before-screening is a hard constraint: rows must exist before SPDR-007/008 run. This is an **append/registration act**, not a status transition, and is therefore permitted mid-checkpoint (checkpoint-013 §2 precedent).

1. `docs/signal-registry/multiplicity-registry.md` — new Chapter 04 section recording: family ID, D0 card path, route INFR→SPDR→XENA (no EXP), universe rules (§6), promote rule (§4 SPDR-008), TRAIN-only, hard bans per card §4, money floor per card §6, 0 slots / 0 counted reads.
2. Card status header: `D0 COMPLETE` → `REGISTERED (2026-07-20, checkpoint-014)`; evidence row appended; experiment IDs recorded.
3. Test-read ledger: **no entries** — no TEST contact anywhere in this checkpoint.

## §3 INFR-017 — signed-bar lane, provenance, seasonal baselines (Phase 0)

**Goal.** Make the signed tier real, audited, and engine-readable. Until this lands, no candidate in this family can be emitted causally.

| Work item | Exit condition |
|---|---|
| **A8 provenance audit** | Taker split reconciled against **raw trades** for a declared sample window (must match to rounding). Bulk trades were not retained → sample re-download expected. On-disk `Buy+Sell ≡ Volume` (max rel dev 3.8e-16, BTC/ETH/SOL) is an internal-consistency check and **does not** substitute. |
| **Spread-proxy pin** | The column's exact definition pinned in writing, plus **null/gap handling** (measured on TRAIN: BTC 158, ETH 4,543, SOL 6,951 null minutes — corrected 2026-07-20 from full-history counts that crossed the holdout; see INFR-017 design.md §3(b) disclosure). Until pinned it is a *relative* liquidity-stress feature only (source P4). |
| **Shared-source disclosure** | `SpreadBps` derives from the same aggressor split as Δ. The dependence is measured and recorded; §2.5 spread reads may not be presented as independent corroboration of a Δ read. |
| **Trade-count check** | `NTrades` present — confirm usability as a z-scored participation multiplier (source Part 5 cheap upgrade). Never a standalone signal. |
| **Signed-bar catalog lane** | Custom Data type + ingest so the engine reads Δ causally, under the pinned fence, with an attestation. Built on `xen.orderflow` contracts. Round-trip + causality asserted in code. |
| **Seasonal baselines (A5)** | Fitted minute-of-day × day-of-week residual baselines per instrument for volume, range, \|Δ\|, **Δ/V separately**, and spread. Frozen artifact, hash-pinned. |
| **Admission** | Signed lane gets its own admission pass (904 staging files vs 894 catalog ADMITTED — the delta is reconciled, not assumed). |

**Kill-gate (HYP-I1).** Split fails to reconcile → **park the family**. The tier's entire warrant is the column's integrity; a framework built on an unaudited column inherits its silent errors.

**Not in scope:** L2/MBP collection, detector implementation. This is bar-tier only.

## §4 Planned experiment sequence

| Seq | ID | What | Gate to start | Depends on |
|---|---|---|---|---|
| 1 | **INFR-017** | Signed-bar lane + A8 audit + A5 baselines (§3) | own design.md → QA → operator execution approval | catalog fence |
| 2 | **INFR-018** | Instrument build + freeze: anchor race (Ph 1), A6 discriminator race (Ph 2), kernel + class validation (Ph 3) → **hash-pinned instrument registry** | INFR-017 exit; own design.md → QA → approval | 1 |
| 3 | **SPDR-007** | **Statistical spine (Ph 4)** — Protection quantile at the correct (1−p) percentile per selected anchor, regime conditioning, Δ-coherence stratification. Money floor computed **first**. Master go/no-go | INFR-018 pin exists; own design.md → approval | 2 |
| 4 | **SPDR-008** | **Breadth sweep (Ph 5)** — S1 + S3 across the **296 TRAIN-readable admitted instruments** (§6 AMENDMENT-1) | SPDR-007 disposition ≠ no-go | 3 |

**Sequencing is strict.** The source is explicit: any result obtained out of sequence is unattributable and re-runs in order. INFR-018 must not begin before INFR-017's baselines freeze; SPDR-007 must not begin before INFR-018 pins.

**INFR-018 kill-gates** (each a hypothesis, full rigor):
- **HYP-I2** (anchor): ≥1 candidate anchor shows stable breakout expectancy. Candidates: UTC-0/daily settlement, funding timestamps (00/08/16 UTC), US and EU equity opens. **Selection across k candidates is k hypotheses** — pre-registered, multiplicity-disclosed, confirmed on the CONFIRM bank (§5). **Primary method:** pooled/hierarchical across the cross-section (source S1 is per-instrument; full per-symbol race over hundreds of instruments is a multiplicity explosion this family cannot afford under thin depth — §7). **Mandatory spot-check:** after the pooled freeze, re-run the same candidate race **per-instrument on a small pre-declared liquid set** (default: BTC, ETH, SOL; n ≤ 5, named in INFR-018 design.md). Purpose: detect major divergence between pooled winner and local winners. Material divergence → record as scope limit and escalate before freezing; cosmetic divergence → freeze pooled with the table disclosed. Spot-check is a sensitivity read, not a second free selection budget.
- **HYP-I3** (A6): candidate operationalisations — n closes beyond; close + follow-through; value migration; time-outside; **and the flow-augmented variants** (acceptance + same-direction Δ) — raced on out-of-sample power to separate trap-type from acceptance-type outcomes. Freeze the winner; everything downstream inherits it. Failure is a framework falsifier: stop.
- **HYP-I4** (proxies / instruments — source Phase 3 + §6.4): three exit conditions, all required:
  1. **Profile kernel calibration** against a finer-grained reference when available (source §2.1 / Phase 3). Prefer any retained trade-level or sub-bar reconstruction for a declared sample window; if no finer reference can be obtained, state **SKIP-NO-REFERENCE** with reason in the pin artifact — do not silently treat an uncalibrated kernel as validated. Kernel choice still freezes once.
  2. **§2.3 signed classes** cluster at structural edges rather than uniformly; warning prints behave as flagged.
  3. Delta needs no truth window — it *is* truth at bar scale — but its seasonal baselines and spread regime bands finalise here.

**SPDR-007/008 lane rules bind** (`docs/references/spdr-lane.md`): TRAIN fence code-asserted, causal t−1 lag, matched-control + seed battery (≥25 seeds, percentile read), per-stratum reporting with pooled figures disclosure-only, mandatory Stage-5 fresh-context analyst pass, L-21 unit pin, disposition-only. **A SPDR result is never a tradability claim.**

**SPDR-008 promote rule (predeclare in its design.md).** Cluster **K = 3** — ≥3 cells in a connected grid region (same anchor family and signal, varying symbol and/or hold) positive vs matched unconditional baselines on the primary bps facet, with dependence-honest uncertainty; best cell not the only positive in its neighbourhood; cluster median gross bps reported against the measured floor.

**Applicable KB constraints carried in:** destroys are **derangements** (L-28); fill-ts = decision-bar close, anchor check mandatory (L-29); `dispose_on_completion=False` (L-30); one BacktestNode per process (L-31); value/quality reads are **report layers**, not gates (L-32/INFR-016); block ≥ H on overlapping windows; no local accounting primitives.

## §5 Holdout mapping — a declared deviation (D3)

**The conflict.** The source demands *one strict holdout untouched through ALL tuning, including anchor selection*, with survivors replicating there before any grade above one notch stands (§6.7). Xen's global 30% holdout is **SEALED with both sanctioned shots spent**, and TEST reads are capped at 2 per stratum for a lifetime. Four Stage-I confirmations against that budget would exhaust the programme's read capacity before a single strategy was tested.

**Resolution.** The two documents mean different objects by "holdout": the source's is a **per-phase selection device**; Xen's is a **programme-lifetime device**. Map the source's holdout onto a **TRAIN-internal confirm bank**, code-asserted:

| Band | Range | Use |
|---|---|---|
| **DESIGN bank** | `2021-06-29T06:53:00Z → 2023-03-01T00:00:00Z` | all Stage I tuning, racing, fitting, selection |
| **CONFIRM bank** | `2023-03-01T00:00:00Z → 2023-12-18T00:00:00Z` | untouched during that phase's tuning; each kill-gate confirms here |
| TEST band | `2023-12-18T00:00:00Z → 2025-01-08T00:00:00Z` | **reserved** — a single counted XENA gate at checkpoint-015; untouched in this checkpoint |
| Global holdout | `≥ 2025-01-08T00:00:00Z` | **never queried** |

This satisfies the source's intent — a genuinely untouched band per selection — at **zero counted reads**. The deviation is declared here, not buried: Stage I confirmations are TRAIN-internal and must be labelled as such in every artifact; they are not out-of-sample in the programme's sense. **Operator (2026-07-20): accepted as a complete adaptation** — no further holdout redesign required.

## §6 Universe rules (D4)

Checkpoint-013 §5 froze an online selection rule (top-10 by trailing 24h volume, ≤ t−1 causal, no fixed pre-run list, anti-survivorship binding project-wide). That rule carries; **the n differs for this family, because breadth is the thesis** (source §6.12: validate across the full cross-section *first*, to map where the logic pays, before spending depth).

| Stage | Universe | Rationale |
|---|---|---|
| INFR-017 (lane + baselines) | All admitted signed-lane symbols | Baselines are per-instrument apparatus |
| INFR-018 (instrument build) | **n = 20**, online rule, daily 00:00 UTC re-evaluation, volume ≤ t−1 | Calibration needs liquid depth (A4 liquidity floor); 20 > the ckpt-013 default of 10 because anchor selection is pooled and needs cross-sectional support |
| SPDR-007 (spine) | Same n = 20 | Comparability with the frozen instruments |
| SPDR-008 (breadth) | **The 296 admitted instruments with readable TRAIN data**, point-in-time, **delisted included** (AMENDED 2026-07-20 — see below) | The breadth advantage is the tier's stated comparative advantage; anti-survivorship binds |

**AMENDMENT-1 (2026-07-20, operator-signed) — SPDR-008 universe sized to 296. Direction: NEUTRAL** (a factual correction of a universe count, neither loosening nor tightening a decision rule; L-23 ledger 0L/0T/1N).

The original wording ("full ADMITTED cross-section") overstated available breadth. Measured at INFR-017 W7 and emitted to `python/experiments/INFR-017/results/admission_reconciliation.json` under `band_coverage`:

| Population | Count |
|---|---|
| ADMITTED instruments | 894 |
| …with any bars before `train_end_utc` (2023-12-18) | **296** ← SPDR-008 universe |
| …with any bars before the DESIGN-bank end (2023-03-01) | **197** ← INFR-018 / SPDR-007 draw pool |
| A5 baselines actually fitted | 194 (3 lost to corrupt staging parquets, returned to INFR-011) |

The 4-year trailing history cap plus late listings leave two thirds of the admitted universe with no readable TRAIN data at all. **Binding consequences:**
- SPDR-008 runs on **296**, not 894; any breadth claim states that denominator.
- The n=20 calibration and spine sets draw from the **197** with DESIGN-bank coverage.
- **Survivorship caveat is binding and must be carried in every breadth read:** the covered set is precisely the instruments listed before the bank end, so it is a survivorship-shaped subset of the venue. A "where does auction logic pay" map built on it describes older listings, not the venue as a whole.
- 296 remains an order of magnitude more breadth than any prior family in this programme (which ran 10–20), so the tier's comparative advantage survives — at a stated, smaller size.

Rule and rebalance frequency are declared as a binding block in each design.md before any cell runs; deterministic and reproducible from catalog data alone; tie-break lexicographic.

## §7 Known constraint — per-symbol depth is thin; breadth carries the family

Measured 2026-07-20: BTC and ETH staging bars start **2022-07-15**, SOL **2022-07-14** (4-year trailing cap). Against `train_end` 2023-12-18 that is **~1.43 years of readable TRAIN on the majors**, split further into DESIGN ~0.63y and CONFIRM ~0.80y.

Consequence, recorded before any read: at 1–3 primary session events per symbol-session, a single major yields order-hundreds of events per bank — thin for a per-symbol quantile estimate. This is the same depth wall that forced XENA-HTFCAP-001 into an exploratory TRAIN+TEST window. **This family does not take that route.** Instead:

- anchor selection and quantile estimation **pool across the cross-section** with per-symbol reads as strata (L-03: per-stratum binding, pooled disclosure-only);
- **HYP-I2 spot-check:** per-instrument anchor race on a few liquid assets (BTC/ETH/SOL by default) to confirm the pooled method does not hide major local differences (§4);
- per-symbol UNPOWERED is reported as power, never folded into a negative (B-5);
- if the spine is only estimable pooled, that is stated as a scope limit of the read, not papered over.

---

## Success criteria (checkpoint level)

- CF-SIGAUC-001 REGISTERED with rows consistent with the D0 card; 0 unexplained deltas.
- INFR-017 ends with an A8 verdict, a pinned spread definition, frozen A5 baselines, and an engine-readable signed lane — or a recorded park.
- INFR-018 ends with a **hash-pinned instrument registry** (anchor + pooled-vs-spot-check table, A6 rule, kernel with calibration-or-SKIP-NO-REFERENCE note, class thresholds) or a recorded framework-falsifier stop.
- SPDR-007 ends in an operator-signed disposition on the master gate, with the money floor computed **before** it. A no-go is a clean outcome.
- SPDR-008, if reached, ends in an operator-signed disposition plus the instrument allocation map.
- Every item: 0 counted TEST reads, holdout SEALED, per-stratum reads, report layers not gates.
- Family status changes (if any) happen only at this checkpoint's retrospective, operator-signed.

## Constraints carried in

Holdout sealed · no TEST contact this checkpoint · registration before screening · per-stratum reads, pooled disclosure-only · no scope expansion after QA APPROVE · no auto-verdicts (value reads are report layers, INFR-016) · integrity gates hard (future-destroy, holdout, causal ≤t−1, estimand reconciliation) · SPDR never touches TEST, spends no reads, registers nothing by itself · card §4 hard bans (P-10 **lifted for this family** — source passive-limit admitted; dual capture for comparison when limit fills are claimed) · mechanism doctrine (refuted mechanisms deleted, not re-parameterised) · source Appendix B experiment plan preserved under XENA packaging · chapter-03 XENA pins remain VOID on Bybit.

---

## Operator decisions — SIGNED 2026-07-20

| # | Question | Operator decision (2026-07-20) |
|---|---|---|
| **D1** | Register CF-SIGAUC-001 now (card + registry row), before any screen? | **APPROVED (a)** — family APPROVED; §2 rows executed. Card status → `REGISTERED (2026-07-20, checkpoint-014)`; registry row → REGISTERED. Append/registration act only; no status transition. |
| **D2** | Does checkpoint-014 stop after the breadth sweep (source Phases 0–5)? | **APPROVED (a)** — stop after Phase 5. Phases 6–7 to checkpoint-015, **in source order** (kill-order preserved; M5 last). |
| **D3** | Map the source's "strict holdout" onto a TRAIN-internal CONFIRM bank (§5)? | **APPROVED (a)** — accepted as a **complete adaptation**, recorded as an explicit declared deviation from source §6.7. TEST band reserved; global holdout never queried. No further holdout redesign. |
| **D4** | Universe: n=20 for calibration and spine, full cross-section for breadth (§6)? | **APPROVED (a)** as proposed. |
| **D5** | Approve INFR-017 building the signed-bar catalog lane as a family prerequisite? | **APPROVED (a)** — INFR-017 proceeds to design → QA → execution. |
| **D6** | Sign the P-01 distinctness argument for the price-only S1/S2 spine (card §5)? | **APPROVED (a)** — accepted as distinct with the stated mitigation (Phase 4 scoped as an availability screen against matched unconditional base rates; cannot itself promote the family). |

### Adherence-review resolutions — SIGNED 2026-07-20

Operator review of draft fidelity to the source methodology. Six items; all resolved.

| # | Finding | Operator resolution | Where applied |
|---|---|---|---|
| 1 | **Holdout (§6.7)** — CONFIRM bank replaces the source's strict holdout | **Accepted as a complete adaptation.** Declared deviation on the record, not a fidelity claim | §5, D3 |
| 2 | **Anchor grain** — pooled/hierarchical vs the source's per-instrument race | **Accepted with addition:** pooled stays primary; **mandatory per-instrument spot-check on a few named liquid assets** (default BTC/ETH/SOL, n ≤ 5) to confirm pooling hides no major local divergence. Sensitivity read, not a second selection budget | §4 HYP-I2, §7 |
| 3 | **Passive-limit overlay** — programme P-10 banned source S13(a)/M3 limit entries | **Xen law OVERRIDDEN for this family.** Source limit-style entries admitted as written; **dual capture** — any cell claiming a passive-limit fill must also emit the market-on-confirm twin and/or the L-27 next-open control, so fill advantage is decomposed from prediction. Not a veto of the source mechanism | Card ban 4, registry, Constraints |
| 4 | **Phase-3 kernel calibration** — thinner than source; no reference tier stated | **Gap closed.** Kernel calibrates against a finer-grained reference where obtainable; where none exists, an explicit **SKIP-NO-REFERENCE** note is written into the pin artifact. Silent uncalibrated freeze banned | §4 HYP-I4.1 |
| 5 | **S2 history depth** — majors carry ~1.43y vs the source's ≥1–2y local requirement | **Accepted with pooling.** Adherence is *aware + mitigated*, not "meets DEPENDS-ON as written"; scope limit stated in the read, never papered over | §7 |
| 6 | **Xen scaffolding** (SPDR K=3, CAL pin, INFR split, n=20, Phase 8 out of scope) | **Accepted as mapping layers.** Binding condition: the **source experiment plan is preserved** — Appendix B order and claims survive adaptation; lane packaging may not reorder Phase 6/7 | §1, Constraints |

### Operator rulings — 2026-07-20 (post-INFR-017)

| Item | Ruling |
|---|---|
| **Holdout touch** behind INFR-017's original §3(b) figures (exploratory scan across the full staging file; one data-quality column's distribution; corrected to TRAIN; no sanctioned shot consumed) | **CLEARED.** Disclosure stands permanently in `INFR-017/design.md` §3(b) and `report.md` §7b. Holdout remains SEALED for all evidential purposes. |
| **SPDR-008 universe size** | **SIZED TO 296** — AMENDMENT-1 above (§6). Survivorship caveat binding on every breadth read. |

**Standing fidelity claim, as signed:** these drafts are a *faithful Xen mapping of source Phases 0–5*, not a reprint. Items 1–3 are explicit deviations on the record; items 4–6 are closures or packaging. Signal and model definitions (S1–S16, M1–M5) remain untouched — the source stays normative for content.
