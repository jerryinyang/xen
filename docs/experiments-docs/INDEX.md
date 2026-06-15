# Experiments Index (Comprehensive)

## Current Infrastructure Tasks

| Task | Status | Focus | Document |
| --- | --- | --- | --- |
| **INFR-002 — New-Universe Data Collection** (2026-06-10, Phase 010 Track C) | **COMPLETE 2026-06-11 — ADMITTED via VAL-003 PASS** (0 FAIL / 0 INCONCLUSIVE; 24/24 negative controls detected; VAL-001 rev. 3 suite unchanged). | 13 new instruments collected via `tools/ctrader-cli/run-infr002-collection.sh` (Mode=TimeBars, m1, 2023-01-03 → 2026-06-11): GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225. ~1.0–1.28M rows each. **Disclosures:** DE30 truncated (broker m1 history ends 2026-01-16 — ~5 months short; boundaries derive from its own timeline; optional re-collection under an alternative broker symbol before first analytical use); duplicate GBPUSD file from the pre-fix run verified content-identical and removed. **Holdout sealed per file at first touch; the final-30% holdout seal carries forward unread.** (No new-universe row had been read for analysis at admission; Phase 011 EXP-043/044/045 subsequently read new-universe first-70% rows for readiness/calibration/training.) The new universe is the programme's confirmation ground for TEST-capped existing-asset candidates; confirmation design is a future checkpoint. | [VAL-003](../../python/experiments/VAL-003/) · [Phase 010 design §5/C1](checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md) |
| **INFR-001 — cTrader Branch & Strategy-Host Integration** (2026-06-06) | **COMPLETE — all VAL-class gates PASS (2026-06-06)** via VAL-002; closed under design.md v2 (§0 execution-model correction). | **Task A COMPLETE — it was the sole focus; the hard block is now lifted.** All four acceptance gates pass (design §6): (1) **transcription** — 108/108 C# ports vs Python references PASS; (2) **end-to-end integration** — all 12 cells (4 instruments × 3 domains) of real `Mode=StrategyHost` cTrader runs reproduce EXP-004/009 (24/24 REJECT, gate-stack `below_MDE`, `matched_reject`) through the unchanged frozen suite via the `xen.signals` ingestion harness; (3) **holdout fence** respected in every cell (in-robot self-guard + harness re-assertion); (4) **reproducibility** behavioral — 5m reproduces the console oracle to full float precision, 1h/4h differ ≤1.83 bps on cTrader's own feed (all far below MDE), per-run config recorded. The frozen qualification suite `{strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}` was carried in untouched. **Phase 004 / AVWAP signal exploration may now open**, behind its mandatory programme-level multiplicity-registry precondition (P3-§11, a Task-B artifact). Governed by VAL-class validation, not per-hypothesis governance. | [design.md](checkpoints/2026-06-06-INFR-001-ctrader-branch-integration/design.md) · [retrospective.md](checkpoints/2026-06-06-INFR-001-ctrader-branch-integration/retrospective.md) |

## Current Checkpoint Status

| Checkpoint | Status | Focus | Documents |
| --- | --- | --- | --- |
| 2026-06-14-014-ha-harami-substrate-and-capture | **ACTIVE — G0 PASS 2026-06-14; VAL-004 COMPLETE 2026-06-14; EXP-048 READINESS_DELIVERED 2026-06-14; EXP-049 CAPTURE_READINESS_DELIVERED 2026-06-15; EXP-050 CONTEXT_CHARACTERISATION_DELIVERED 2026-06-15; EXP-051 STRONG_FILTER_CHARACTERISATION_DELIVERED 2026-06-15** (D0 ratified, P1–P13 frozen in [D0-predeclarations.md](checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/D0-predeclarations.md); VAL-004 PASS — full Suite PASS, all 68 cells ADMITTED). New candidate family **`CF-HA-HARAMI-001`** (Heiken Ashi harami at trend exhaustion), via the Phase 013 pre-committed routing on ANCHOR_MOVE_FLAT. Design brief (Phase 013 retrospective, binding): the unsolved problem is **capture geometry, not move availability** — the mechanism is a structurally bounded favourable target, measured early (HYP-002/EXP-049), not assumed. 102-cell grid (17 instruments × {5m,15m,30m,1h,2h,4h}); all work **gross, 0 candidate slots, 0 TEST reads, holdouts sealed**. Pipeline entry point: **VAL-004 PASSED** → **EXP-048** → **EXP-049** → **EXP-050** → **EXP-051 STRONG_FILTER_CHARACTERISATION_DELIVERED 2026-06-15; EXP-052 pending**. 014-A primitives (EXP-048–052) validated separately before any 014-B combined event/barrier-model work. **EXP-048:** 86/102 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED — no substrate defect, 0 invariant violations, 0 determinism failures; 99 member cells cleared for EXP-049. **EXP-049:** 99/99 cells barrier-constructible, G1 r ~0.50 null → 0/99 VIABLE, G2 systematically degenerate; capture geometry under benchmark defaults does not favour. **EXP-050:** raw HA harami position-in-move uniformly front-loaded (Δ −0.12 to −0.18, 0/99 CLUSTERED); front-loading is ZigZag-specific; baseline for conditional/selected harami screening. **EXP-051:** both /STRONG-STAT (p75) and /STRONG-HA (primary) identify materially different move populations (99/99 MATERIAL, both P11 pass, ρ≥1.5 & f∈[0.10,0.50] in every cell); disclosed forms agree (0 flips); invariants 0, determinism PASS. | **HA-harami family from first principles.** Validate each primitive (ATR-ZigZag substrate on real bars, HA harami detector on HA candles, 3-barrier capture geometry) separately, then assemble only survivors. Capture geometry is first-class — a gross favourable-before-adverse capture read lands in 014-A (EXP-049), not deferred. Detection on HA candles; every outcome metric on real prices. | [design.md](checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/design.md) · [D0-predeclarations.md](checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/D0-predeclarations.md) · [family spec](../signal-registry/candidate-families/harami.md) · [VAL-004](../../python/experiments/VAL-004/) |
| 2026-06-12-013-substrate-revision-anchor-move-size | **CLOSED 2026-06-12 — ANCHOR_MOVE_FLAT** (G1a 51/51 READY; G1b adjudicated **0/51 SHIFTED_VIABLE** in [G1-gate-review.md](checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/G1-gate-review.md); retrospective written 2026-06-12; **`CF-AVWAP-001` closed for new in-family phases** — exits (010–011), entry parameters (012), and the ratified `/ANCHOR` (013) all CLOSED-MEASURED; `/LB` `/MB` `/ATR` DEFERRED with no candidate status; pre-committed routing executed: programme routes to a **new candidate family** — Phase 014, own design/D0, fresh EXP-020/027/029-analog scaffolding, design brief targets **capture geometry**, not move availability). Phase history: **G0 PASS 2026-06-12** (D0 P1–P8 operator-ratified: ATR prominence `k=1.0`, floor multiple `M=2`; registry amended, Phase 013 batch; no row read under any `/ANCHOR` definition before ratification). **EXP-047 COMPLETE 2026-06-12 — DIAGNOSTIC_DELIVERED, hypothesis REFUTED, audit PASS 0C/2W (interpretive):** mechanical G1b input **ANCHOR_MOVE_FLAT** — 0/51 SHIFTED_VIABLE (relaxed sensitivity thresholds ≥4/≥2 and ≥3/≥2 also unmet). Central finding (audit-verified): the ratified k=1.0 ATR-prominence anchor **collapses to the baseline running extreme by qualification** — anchor coincidence 94.6–98.5% vs fallback only 0–2% (the predeclared fallback disclosure missed the dominant collapse path); 13/51 cells produced literally identical event populations; Δ median MFE −2.7…+0.9 bps, all inside noise. Unanticipated descriptive read: P5 leg 2 passes 51/51 — median lifetime peak MFE ≈5–9× the frozen cost floor on **both** anchors (1h ≈24, 2h ≈36, 4h ≈64 bps vs floors ≈5–7 bps) — **move availability was never the binding constraint; capture geometry is**. Integrity clean: P8 regression gate 15/15 before first TRAIN read, 51/51 READY, reconciliation 125/125 vs EXP-043 counts + EXP-046 gross(H=8) at diff exactly 0.0, determinism everywhere. **0 slots, 0 TEST reads, holdouts sealed, ledger unchanged.** Verdict conditional on the ratified k=1.0; pre-committed routing on FLAT: new candidate family (own design/D0). | **Substrate pivot opener: TRAIN-only, gross, exit-agnostic move-size diagnostic** deciding between an in-family `/ANCHOR` revision and a full new-family pivot, per the Phase 012 §1.4.2 operator pre-commitment. Compares the available per-event favorable move (lifetime MFE) under the running-extreme vs ATR-prominence anchors against the frozen per-cell cost floor across the full 17×{1h,2h,4h} grid (readiness-defined membership). | [design.md](checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/design.md) · [D0-predeclarations.md](checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/D0-predeclarations.md) · [G1-gate-review.md](checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/G1-gate-review.md) · [retrospective.md](checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/retrospective.md) · [EXP-047](../../python/experiments/EXP-047/) |
| 2026-06-12-012-entry-side-gross-screen | **CLOSED 2026-06-12 — ENTRY_GROSS_FLAT** (G1 adjudicated in [G1-gate-review.md](checkpoints/2026-06-12-012-entry-side-gross-screen/G1-gate-review.md): no non-baseline `/ALPHA` or `/MA-DOMAIN` OAT variant meets the P6 composition threshold — best 3 clearing cells (alpha_1.0 3/3 instruments; ma_40_100 3/2) vs ≥5 cells over ≥3 instruments; **0 slots, 0 TEST reads, ledger unchanged, holdouts sealed**; routing per the design §1.4.2 operator pre-commitment: programme pivots to substrate revision — Phase 013 design starts from the Stage-C branches (`/LB` `/MB` `/ATR` `/ANCHOR`) or a new candidate family; retrospective written 2026-06-12). Phase history: **G0 PASS 2026-06-12** (D0 P1–P8 operator-ratified as drafted; registry amended; variant count corrected 8→7 pre-data-contact). **EXP-046 COMPLETE 2026-06-12 — SCREEN_DELIVERED, hypothesis REFUTED, audit PASS 0C/0W/3 Info, post-experiment governance APPROVE (single pipeline pass, no revision cycles):** 7 variants × 37 cells; 14 CLEAR / 235 NO_CLEAR / 10 BELOW_FLOOR; variant H=8 cross-cell medians −2.35 to +0.28 bps vs floors ~5–20 bps (the gross shortfall is a substrate property, not a parameterization property); 12/14 CLEAR rows in the predeclared 4h/index false-positive channel (US2000-4h clears under 5 variants — hypothesis-generating only); all 10 BELOW_FLOOR rows are slow-MA 4h cells (breadth-for-quality trade-off); integrity clean — reconciliation 259/259 at 1e-9 bps vs the EXP-043 counts and EXP-045 FH anchor, determinism 259/259 (full-frame replay), P8 regression gate green (24/24 incl. baseline-fixture invariance at default α/MA). Entry-parameter lever measured and exhausted on this substrate; `/ALPHA` and `/MA-DOMAIN` CLOSED-MEASURED. | [design.md](checkpoints/2026-06-12-012-entry-side-gross-screen/design.md) · [D0-predeclarations.md](checkpoints/2026-06-12-012-entry-side-gross-screen/D0-predeclarations.md) · [G1-gate-review.md](checkpoints/2026-06-12-012-entry-side-gross-screen/G1-gate-review.md) · [retrospective.md](checkpoints/2026-06-12-012-entry-side-gross-screen/retrospective.md) · [EXP-046](../../python/experiments/EXP-046/) |
| 2026-06-11-011-per-instrument-foundation | **CLOSED 2026-06-11 — FOUNDATION_NON-TUNABLE** (G2 adjudicated FAIL in [G2-gate-review.md](checkpoints/2026-06-11-011-per-instrument-foundation/G2-gate-review.md): EXP-045 membership 0/37 vs P5 ≥5 cells over ≥3 instruments; Tracks C/D never opened; **0 of ≤6 TEST reads spent, ledger unchanged**; EXP-018 P1 threshold unspent; retrospective written 2026-06-11 — routing per design §9: `/ENTRY` exploration or substrate change, next phase design pending). Phase history: **G0 PASS 2026-06-11; Track A0 removed after EXP-042 FRAMING_ERROR** (D0 predeclarations frozen; EXP-042 set aside with 0 slots and 0 TEST reads; entry reverts to the frozen AVWAP-line arm/trigger; band multiplier is only a Track B exit parameter). **Track A readiness (EXP-043) COMPLETE 2026-06-11 — READINESS_DELIVERED, audit PASS:** 50/51 cells READY (0 invariant violations, 0 determinism failures, no substrate alert); JP225-2h NOT_READY on the frozen >25% 2h dropped-fraction gate (excluded from Track B); realized event-rate table supersedes design §7.4 power figures (1h 151–273, 2h 86–143, 4h 32–86 TRAIN events; all ≥30 floor). **G1 adjudicated 2026-06-11 (PARTIAL → CLOSED same day)** ([G1-gate-review.md](checkpoints/2026-06-11-011-per-instrument-foundation/G1-gate-review.md), adjudication 1 of 2): readiness leg (i) SATISFIED on 50 cells; calibration leg (ii) **measured — EXP-044 COMPLETE 2026-06-11, CALIBRATION_DELIVERED, audit PASS**: 37/50 cells COVERED, 13 NOT_COVERED (11 marginal FPR excess, USDCAD-2h material, BTCUSD-4h no finite MDE); median per-cell MDE 16/32/64 bps on 1h/2h/4h; substrate triggers not fired; **G1 CLOSED 2026-06-11** (adjudication 2 of 2 in G1-gate-review.md): Track B authorization GRANTED on the 37-cell COVERED grid; 13 NOT_COVERED cells excluded with record (11 marginal FPR, USDCAD-2h material, BTCUSD-4h no finite MDE); per-cell MDE table is the binding Track B/D power context; EXP-029-analog parity remains the pre-TEST-read requirement for 2h/new-universe strata. **Track B (EXP-045) COMPLETE 2026-06-11 — TRAINING_DELIVERED, EMPTY MEMBERSHIP, audit PASS:** 0/37 member cells (35 NON_TUNABLE, 2 FLOOR_FAIL with negative plateaus); net medians −5 to −7 bps at every grid point of both exit families under frozen CONSERVATIVE costs; G2 composition (P5) NOT met — **G2 adjudicated FAIL 2026-06-11 → phase CLOSED FOUNDATION_NON-TUNABLE; Tracks C/D never opened; 0 of ≤6 TEST reads spent.** The failure is economic, not methodological: gross proxy positive in 31/37 cells; frozen CONSERVATIVE costs consume the few-bps gross edge. The per-instrument exit-side lever is measured and exhausted on this substrate. EXP-029-analog parity dispositioned as a pre-TEST-read requirement for 2h/new-universe strata, not a G1 condition. | **Per-instrument foundation and strategic reset.** Tests whether the AVWAP baseline entry with per-instrument-trained exits across 17 instruments × {1h, 2h, 4h} can pass the portfolio-fitness primary endpoint and any top-k per-cell secondary confirmations. 5m retired; holdouts sealed; EURUSD-4h at TEST-read cap; total phase TEST budget ≤6 one-shot reads. | [design.md](checkpoints/2026-06-11-011-per-instrument-foundation/design.md) · [D0](checkpoints/2026-06-11-011-per-instrument-foundation/D0-predeclarations.md) · [G1](checkpoints/2026-06-11-011-per-instrument-foundation/G1-gate-review.md) · [G2](checkpoints/2026-06-11-011-per-instrument-foundation/G2-gate-review.md) · [retrospective.md](checkpoints/2026-06-11-011-per-instrument-foundation/retrospective.md) |
| 2026-06-10-010-exit-exploration-and-line-sr | **CLOSED 2026-06-11 — EXIT_FLAT (Track A) / HYP-001 INCONCLUSIVE (Track B); INFR-002 COMPLETE same day (VAL-003 PASS, new universe admitted)** (EXP-039 FLAT 0/10 cells, EXP-041 reserved-inactive slot unused; EXP-040 1h Δ=+1.55 pp CI spans zero, 4h below floor, moving-copy arm resolves the kinematic confound; both audits PASS; retrospective written 2026-06-11). **Operator decision (design §9):** Phase 011 proceeds on the Phase 008 frozen package (FH H\*=12, all_legs); Stage-C family review deferred until the new universe can power it. | **Exit exploration, line-S/R science, new-universe groundwork.** Track A screened five structurally distinct exit families (E1–E5) against R-FH(12)/R-BTC on TRAIN — nothing qualified; the capture-efficiency lever beyond FH is exhausted at this substrate's power (~86 4h events, SEs 7–30 bps); 1h triply confirmed non-viable. Track B ran HYP-001 in the confound-free approach-conditioned framing — INCONCLUSIVE, hypothesis stays OPEN as a permanent mechanism record. Track C (INFR-002, 13 new instruments) carried OPEN: collection script + VAL-003 admission validation scaffolded; holdout sealed at first touch. | [design.md](checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md) · [retrospective.md](checkpoints/2026-06-10-010-exit-exploration-and-line-sr/retrospective.md) |
| 2026-06-10-009-avwap-holdout-release | **EXECUTED 2026-06-10 — HOLDOUT_INCONCLUSIVE, shot SPENT** (EXP-032 complete, audit PASS: n=27, net +20.60 bps, ci_low_1s 2.71 ≤ margin 4.32, boot_p 0.029, two-sided CI spans zero). The p-gate passed; the calibrated margin condition failed (uncorrected null FPR 0.0715 at this structure — the margin prevented an over-claim). TEST evidence stands, permanently non-upgradable; EURUSD holdout contaminated-by-disclosure; BTCUSD/USTEC/XAUUSD seal intact. Tier-C routing per Phase 008 design §9; **COMPLETED 2026-06-10 — retrospective written.** | **The programme's single sanctioned read of the global holdout, for the operator-selected Package B.** EXP-032: EURUSD-4h AVWAP bounce events, FH H\*=12 all_legs exit (EXP-037 freeze, hash-pinned), frozen CONSERVATIVE costs (RT 3.0 bps) + financing (0.6 bps/day), frozen EXP-027 inference tail. Minimal unsealing: EURUSD 1-minute rows past the analysis cutoff only; BTCUSD/USTEC/XAUUSD holdout stays sealed. Two-phase freeze-before-outcome (H1 entry-attribute manifest + R1.2-analog calibration margin → H2 one-shot inference), no-second-read guard, analysis-stratum reconciliation against the EXP-037 population (27 TRAIN / 12 TEST), EXP-037 TEST reproduction anchor. Verdict mechanical: HOLDOUT_CONFIRMED iff ci_low_1s > m_cell and one-sided p ≤ 0.05; REFUTED iff CI_high < 0; else INCONCLUSIVE — **shot spent on any outcome**. Expected holdout n ≈ 15–18 (power-limited; INCONCLUSIVE honest). If confirmed: first holdout-confirmed AVWAP candidate; next step cTrader FH-exit parity (analysis set only). | [design.md](checkpoints/2026-06-10-009-avwap-holdout-release/design.md) · [retrospective.md](checkpoints/2026-06-10-009-avwap-holdout-release/retrospective.md) |
| 2026-06-10-008-avwap-clinical-tradability | **COMPLETED 2026-06-10 — CLINICAL_TRADABLE** (G2 SATISFIED, [G2-gate-review.md](checkpoints/2026-06-10-008-avwap-clinical-tradability/G2-gate-review.md); retrospective written 2026-06-10): EURUSD-4h passes the binding phase Holm-4 family on both routes (EXP-038 BTC-exit baseline adj_p≈0.004, ci_low_1s 15.43 > margin 3.78; EXP-037 FH H\*=12 exit adj_p≈0.004, ci_low_1s 21.94 > 8.42); XAUUSD margin-bound, USTEC fail. Operator selected Package B; the Phase 009 holdout shot returned **HOLDOUT_INCONCLUSIVE, SPENT** — TEST evidence stands, permanently non-upgradable; Tier C is now the path. | **Tests the three admissible levers for a real-but-cost-dominated edge on the existing entry substrate: selectivity, instrument selection, capture efficiency.** Tiered, gated path: D0 disclosure-synthesis memo (free) → Tier A in parallel: EXP-034 per-instrument net tradability screen (declared 6-cell family, Holm, frozen EXP-030 costs + predeclared financing EURUSD 0.6/USTEC 1.2/XAUUSD 1.2/BTCUSD 10.0 bps/day), EXP-033 TRAIN-only horizon sweep (DIAG-004; closes EXP-031's unresolved flip; mechanical one-SE H\* rule), EXP-035 TRAIN-only conditioning characterisation (DIAG-005; %completion-to-target, session, vol regime; quantified G1 criteria) → lenient gate G1 → Tier B: ≤2 one-shot TEST confirmations (EXP-036 `/COND`, EXP-037 `/EXIT-FH` incl. TRAIN-frozen pyramid policy; 1 slot each) → strict gate G2 (net CI_low>0, Holm) → single holdout-release checkpoint (EXP-032, reserved) admissible. Tier C fallback: Stage-C branches; HYP-001 as parallel science. Two-speed gating: lenient to continue exploring, strict to spend the one-shot holdout. TRAIN/TEST nested split is the anti-overfitting backbone; cost model frozen, no iteration; holdout sealed. | [design.md](checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md) · [retrospective.md](checkpoints/2026-06-10-008-avwap-clinical-tradability/retrospective.md) · [G1](checkpoints/2026-06-10-008-avwap-clinical-tradability/G1-gate-review.md) · [G2](checkpoints/2026-06-10-008-avwap-clinical-tradability/G2-gate-review.md) |
| 2026-06-09-007-avwap-tradability-and-isolation | **COMPLETED 2026-06-10 — NOT_TRADABLE** (design §9; EXP-030 INCONCLUSIVE, EXP-031 ISOLATION_READ_UNRESOLVED; both post-governance APPROVE; retrospective written 2026-06-10) | **Tradability and edge isolation answered for Phase 007.** EXP-030 INCONCLUSIVE: no domain tradable under CONSERVATIVE costs (5m/1h EVIDENCE_AGAINST, 4h INCONCLUSIVE). Holdout release (EXP-032) gated on EXP-030 EVIDENCE_FOR — gate NOT passed. EXP-031 ISOLATION_READ_UNRESOLVED: entry-vs-exit attribution flips between H=1 (EXIT_DOMINANT) and H=6 (ENTRY_DOMINANT) on all domains — horizon-dependent pattern is the central finding. HYP-001 remains open. | [design.md](checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md) · [retrospective.md](checkpoints/2026-06-09-007-avwap-tradability-and-isolation/retrospective.md) |
| 2026-06-08-006-avwap-evaluation-correction | **COMPLETED 2026-06-09 — EVAL_SUPPORTED (cTrader-confirmed)**; supersedes Phase 005. Amended 2026-06-09: EXP-028 omission recorded and EXP-029 appended. All three experiments complete (EXP-027 METHOD_VALID, EXP-028 EVAL_SUPPORTED, EXP-029 CONSISTENT/cTrader-confirmed); phase objective fully satisfied; retrospective written 2026-06-09. | **Fixes the evaluation vehicle Phases 004/005 mis-applied, then re-screens the faithful strategy.** Operator review found EXP-023/024/025 screened/diagnosed a ~6%-active event signal through a per-bar continuous-position referee calibrated only for ≥80%-active series (EXP-005). The strategy position rule was ~faithful; the **yardstick** was wrong. Three experiments: **EXP-027** defines + calibrates an event-level evaluation method (METHOD_VALID); **EXP-028** re-screens the faithful AVWAP strategy under it (Python-only; EVAL_SUPPORTED); **EXP-029** closed the cTrader per-bar streaming omission — the corrected C# strategy run on cTrader reproduced EXP-028 PRIMARY excess on all 3 domains (parity **CONSISTENT**; all 5 binding gates pass), upgrading EXP-028 to **cTrader-confirmed**. HYP-001 (line S/R) recorded as open, not in scope. Holdout sealed; no tuning. Root cause: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. Omission (now closed): `checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md`. | [design.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/design.md) · [retrospective.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/retrospective.md) · [EXP-028-omission.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md) |
| 2026-06-08-005-avwap-exit-and-branch-exploration | **HALTED 2026-06-08** (was ACTIVE) — superseded by Phase 006 before Stage B/C. Stage A diagnostics (EXP-024 MIXED_OR_INCONCLUSIVE, EXP-025 INCONCLUSIVE) inherited an evaluation-framing defect; EXP-026 `/EXIT` shelved; Stage C deferred. See [retrospective.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/retrospective.md) and the framing-divergence review. | **Continues `CF-AVWAP-001` after Batch 004-A closed BASELINE_BRANCH_REFUTED.** Three dependent stages. **(A) Diagnosis** (Python-only, no suite, no multiplicity slot): EXP-024 edge-dissipation decomposition completed with diagnostic `MIXED_OR_INCONCLUSIVE` — primary 5m resolves fork (b) entry/position dilution (+0.370 bps best bounded hold < 0.5 bps floor), 1h/4h unresolved due wide CIs, and no domain supports fork (a); EXP-025 direct AVWAP-line S/R test remains pending (gap #4 — never tested directly; EXP-021/022 tested continuation and completion, not reaction-at-line). **(B) EXIT screen**: EXP-026 `CF-AVWAP-001/EXIT` is **not automatically justified by EXP-024 alone**; mixed/inconclusive output requires explicit operator/governance handling before any `/EXIT` screen. **(C) Branch exploration**: `/LB` `/MB` `/ATR` detectors (gaps #2) and new `/ANCHOR` running-extreme-vs-significant-pivot (gap #1). `/ALPHA` `/BAND` parameter sensitivity deferred out of phase. Knife-edge guardrail: exit/detector rules come from structure, predeclared, measured once — no sweep, no post-result reselection. Holdout sealed. | [design.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md) |
| 2026-06-07-004-avwap-signal-exploration | COMPLETED — Batch 004-A baseline chain complete: EXP-020 SUPPORTED_FULL; EXP-021 SUPPORTED; EXP-022 SUPPORTED; **EXP-023 REFUTED**. | **First real signal-exploration phase; baseline branch screened to a clean negative.** The mandatory programme-level multiplicity/file-drawer registry is documented in `docs/signal-registry/multiplicity-registry.md`, and Batch 004-A registers only `CF-AVWAP-001` (Anchored VWAP on regime pivots). EXP-020 validated the first-branch substrate across all three domains; EXP-021 confirmed fixed-horizon bounce reaction (all 3 domains EVIDENCE_FOR, +3.8/+9.1/+37.6 bps); EXP-022 confirmed the band-target/trend-change lifetime method (rate diffs +23.9/+21.9/+26.4 pp, Holm p=0.0003). EXP-023 then screened the cTrader strategy-host AVWAP baseline through the **frozen suite** on emitted real prices: 12/12 cells admitted, C# transcription smoke PASS, but **0/12 strict, 0/12 ratified-loose, 0/12 revised-incremental passes → REFUTED** (effects ≪ frozen floors; high favorable-target rate 0.60–0.80 but ~0/negative net expectancy from trend-change exits + cost). This is a **baseline-branch negative, not COMPONENT_REFUTED** of CF-AVWAP-001 (design §8). Next AVWAP work requires new scoped experiments on registered non-baseline branches (LB/MB/ATR/ALPHA/BAND/EXIT), with no in-place baseline tuning. | [design.md](checkpoints/2026-06-07-004-avwap-signal-exploration/design.md) · [retrospective.md](checkpoints/2026-06-07-004-avwap-signal-exploration/retrospective.md) |
| 2026-06-05-003b-incremental-unit-redesign | COMPLETED — REVISED_UNIT_VALIDATED (EXP-017-019 executed and post-governance APPROVED 2026-06-05; retrospective written 2026-06-05) | **Track B follow-up succeeded.** EXP-017 validated the revised incremental-referee logic (7/7 fixture verdicts, 28/28 retained-leg checks, L2 absent). EXP-018 validated the revised portfolio-fitness unit on the construction-accepted dependence grid: FPR controlled in 126/126 accepted cells, finite worst-case MDEs 12/16/32 bps on 5m/1h/4h, and the EXP-015 synchronous/high-overlap/null_R stress corner passes in every domain; 36 infeasible high-rho/low-overlap cells are disclosed as construction-invalid. EXP-019 exercised both assembled-suite paths: EXP-009 dogfood rejects and synthetic positive passes across all domains. The concluded suite is now **{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}**. Phase 004 may open after its mandatory programme-level multiplicity registry precondition is documented. **Not a new programme phase — a revision; Phase 004 remains reserved for signal exploration.** | [design.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/design.md) · [retrospective.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/retrospective.md) |
| 2026-06-04-003-ratification-and-incremental-unit | COMPLETED — PARTIAL_SUCCESS (EXP-012-016 executed and reviewed; amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) applied and Track B re-validated; retrospective written 2026-06-05) | **Framework-conclusion attempt did not reach FULL_FRAMEWORK_CONCLUDED (outcome: PARTIAL_SUCCESS).** Track A succeeded: EXP-012 ratified and adopted the EXP-011 loose point on fresh seeds for 5m/1h/4h. Track B validated the substrate and logic gates (EXP-013/014) but EXP-015 refuted portfolio-fitness calibration because every domain had qualifying dependence cells with no finite MDE. EXP-016 correctly blocked before composition measurement because the incremental unit was not COMPLETE and the dogfood reference book was undefined. **Adversarial review (amendment A1) corrected the incremental inference layer (F04 contiguous-series block length), the EXP-013 redundancy verdict (F01 across-draw distribution + `UNDER_POWERED` class), and EXP-015 diagnosability (F03 per-leg/per-instrument tables); EXP-013→014→015 re-validated 2026-06-04/05 — direction unchanged: Track A SUPPORTED, Track B substrate/logic PASS (EXP-013 PASS with 3 cells now `UNDER_POWERED`; EXP-014 PASS, `effective_n` episode-aware), EXP-015 REFUTED with the failure attributed to the L2 standalone-significance leg driven by BTCUSD.** The concluded suite ships as **two referees only** (frozen strict + ratified-loose); the incremental/fitness unit is carried to a follow-up. **Operator decision recorded 2026-06-05 (retrospective §11): Path B — open a new incremental-unit follow-up checkpoint and fix the L2/BTCUSD calibration failure (and resolve the A1/F02 L4/L5 freeze precondition) before Phase 004**, rather than rescoping Phase 004 to standalone-only. Phase 004 stays blocked until that follow-up delivers a validated+calibrated incremental unit. | [design.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/design.md) · [retrospective.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/retrospective.md) |
| 2026-06-03-002-referee-refinement-and-stringency | COMPLETED (7/7 EXP executed, governance-APPROVED; retrospective written 2026-06-04) | Keystone spine item closed for the scoped realistic candidate (EXP-005); L5 threshold frontier measured (EXP-006); lenient-L5 structural-gain claim refuted because lenient equals the EXP-006 zero-buffer endpoint and drop-L5 (EXP-007); per-instrument MDE heterogeneity found in EURUSD/XAUUSD slower-domain cells (EXP-008); broadened simple-strategy dogfood stayed below every domain MDE (EXP-009); split robustness held on 5m/1h with only 4h falsified — and there the more-OOS protocols detect a lower MDE (EXP-010, corrected 2026-06-04: the original 1h/4h walk-forward MDE inflation was a multi-fold CI artifact); predeclared-loss synthesis recommends tau 0.75/0.25/0.5 on 5m/1h/4h, with adoption deferred to Phase 003 fresh draws (EXP-011). Characterization phase - recommends, does not adopt. | [design.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/design.md) · [retrospective.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/retrospective.md) |
| 2026-06-01-001-thesis-qualification-calibration | COMPLETED | Build the 5-check gate-stack referee + calibration harness; measure per-domain (5m/1h/4h) FPR/TPR/economic-MDE for it and a minimal baseline (EXP-001→004). | [design.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/design.md) · [retrospective.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/retrospective.md) |


## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-06-12-012-entry-side-gross-screen | CLOSED 2026-06-12 — **ENTRY_GROSS_FLAT** (G1 mechanical; EXP-046 complete, audit PASS, governance APPROVE; 0 TEST reads) | Neither entry lever moves the gross edge: across α ∈ {0.0…1.0} and MA (10,25)…(60,150), typical cell gross moves ~1–2 bps against ~5–20 bps cost floors — with exits (Phases 010–011) and entries (Phase 012) both measured flat, the AVWAP-bounce substrate's registered parameter space is exhausted and the programme pivots to substrate revision (operator pre-commitment; Stage-C branches or new family). Validated patterns carried forward: gross-screen-before-net-machinery ordering, pre-committed routing, predeclared false-positive channel, 1e-9 bps external anchoring. | [retrospective.md](checkpoints/2026-06-12-012-entry-side-gross-screen/retrospective.md) |
| 2026-06-11-011-per-instrument-foundation | CLOSED 2026-06-11 — **FOUNDATION_NON-TUNABLE** (G2 FAIL; EXP-043/044/045 complete, audits PASS; Tracks C/D never opened; 0 of ≤6 TEST reads spent; retrospective written 2026-06-11) | **The fair fight was held; costs won.** The universal-parameter critique (Phases 001–010 ran on untrained placeholder parameters) is now answered: with per-instrument exits trained over two families × 8-point grids on the 37 calibrated cells of the 17-instrument × {1h,2h,4h} universe, **no cell clears frozen CONSERVATIVE costs** — 35 NON_TUNABLE, 2 tunable-but-FLOOR_FAIL with negative plateaus (EURUSD-1h FH(3) −3.45 bps; US500-2h MAD(1.0) −0.37). The binding constraint is gross edge vs the cost floor, not exit choice: gross proxy positive in 31/37, net medians −5 to −7 bps everywhere — exit training reallocates gross edge, it cannot raise it. 4h gross positives (US500 +76.7, US2000 +53.4, DE30 +46.7 bps best-grid net) are unverifiable at 32–86 events vs 32–128 bps MDEs. The stability-plane machinery refused to certify noise (the Phase 008 `h_star_stable=false` symptom never recurred); the inverted-inference structure made a fully negative phase cost **zero** TEST reads. Real methodological discovery: per-cell N1>N2 FPR offset (EXP-044, 35/50 cells, p≈0.001) — pooled two-null agreement does not replicate per cell. Track A0/EXP-042 framing error caught and set aside before any decision consumed it (registry branch definitions are the authority). Routing per design §9: entry-side levers (`/ENTRY`, `/ALPHA`, `/MA-DOMAIN` — never swept) or substrate/execution-cost revision; MTF premise weakened (no tradable cells). New-universe infrastructure (VAL-003, 51-cell grid, readiness + calibration maps) carries forward. | [retrospective.md](checkpoints/2026-06-11-011-per-instrument-foundation/retrospective.md) · [G2](checkpoints/2026-06-11-011-per-instrument-foundation/G2-gate-review.md) |
| 2026-06-10-010-exit-exploration-and-line-sr | CLOSED 2026-06-11 — **EXIT_FLAT / HYP-001 INCONCLUSIVE** (EXP-039 + EXP-040 complete, audits PASS; EXP-041 slot unused; INFR-002 carried OPEN; retrospective written 2026-06-11) | **The screen worked; the lever is empty.** Five exit families failed the predeclared G1 rule — best candidate E2 (+31.9 bps) sits ~0.5 SE behind the TEST-confirmed R-FH(12) bar (+37.3 bps), so the question is power-bound, not mechanism-resolved; the real finding is the ~86-event 4h TRAIN power wall (SEs 7–30 bps) that blinds any further substrate-bound comparison. 1h is triply dead (EXP-030/033/039: even R-BTC is net-negative — the events, not the exits, are the problem). The mechanical gates preserved the one-shot TEST slot from a fragile near-miss (E3(3) raw +39.9 bps, split-half sign flip). HYP-001 stays OPEN: 1h CI spans zero, 4h below floor; the moving-copy arm resolved the kinematic confound (1h premium not explained by kinematics; 4h negative was artifact). Operator: Phase 011 on the Phase 008 frozen package; Stage-C deferred to a powered (new-universe) setting; INFR-002 + VAL-003 are the critical path. | [retrospective.md](checkpoints/2026-06-10-010-exit-exploration-and-line-sr/retrospective.md) |
| 2026-06-10-009-avwap-holdout-release | COMPLETED 2026-06-10 — **HOLDOUT_INCONCLUSIVE, shot SPENT** (EXP-032 executed once, audit PASS 0C/0W, post-governance APPROVE; retrospective written 2026-06-10) | **The programme's single sanctioned holdout read is spent without confirmation or refutation — and the calibration margin is what kept the books honest.** EXP-032 on the 27 holdout-stratum EURUSD-4h events (vs ≈15–18 expected): net per-event expectancy **+20.60 bps**, two-sided 95% CI [−0.39, +42.15]; one-sided bootstrap p = 0.029 PASSED, but ci_low_1s = +2.71 bps ≤ predeclared margin m_cell = 4.32 bps FAILED → mechanically HOLDOUT_INCONCLUSIVE. The margin did its R1.2 job: the frozen bootstrap's uncorrected dual rule had a *measured* null FPR of 0.0715 at this exact 16-cluster layout — an uncalibrated read would have over-claimed CONFIRMED. Out of sample the effect attenuated (vs analysis-era +32.87, EXP-037 TEST +40.56), not reversed — by design indistinguishable from a lucky zero-effect stratum; the limit was per-event dispersion (~60–70 bps), not stratum size. Non-binding companion: BTC-exit net +2.35 bps on identical events — the FH(12)-over-BTC mechanism replicated descriptively. One-shot machinery held end to end (two-invocation H1 freeze → H2, verdict-file-last, no-second-read guard, one file opened; BTCUSD/USTEC/XAUUSD seal intact; no post-freeze amendment; no hard stop). **Consequences:** Package-B TEST evidence stands, permanently non-upgradable; EURUSD holdout contaminated-by-disclosure; no second read for any package ever. **Process lessons:** calibrate the verdict rule to the realized cell layout before outcome contact and let it bind; never quote small-n boot_p without its measured calibration; predeclaring INCONCLUSIVE-spends-the-shot removed all near-miss argument; the no-selection-lever rule (H2 runs regardless of H1 attributes) keeps the freeze from becoming a peek; check confirmable-effect-size against expected winner's-curse attenuation before spending an irreversible read. Redirect: Tier C per Phase 008 §9 — HYP-001 direct S/R test first, Stage-C branches, optional analysis-set-only FH-exit cTrader parity. | [retrospective.md](checkpoints/2026-06-10-009-avwap-holdout-release/retrospective.md) |
| 2026-06-10-008-avwap-clinical-tradability | COMPLETED 2026-06-10 — **CLINICAL_TRADABLE** (G2 SATISFIED; all Tier-A/B experiments post-governance APPROVE; retrospective written 2026-06-10) | **Of the three admissible levers for a cost-dominated edge, only capture efficiency delivered — and only on EURUSD-4h.** Selectivity is empty: EXP-035 qualified 0/9 domain×dimension cells (no conditioning bin reaches positive absolute net; closest 5m %completion SNR 1.42 but candidate net −7.07 bps) → EXP-036 `/COND` never opened. Instrument selection alone insufficient: EXP-034 EURUSD-4h strict pass (+11.77 bps, boot_p 0.009) was demoted pre-execution (F02) to necessary-but-not-sufficient. Capture efficiency real: EXP-033 closed the EXP-031 attribution puzzle (stable crossover 5m H=3 / 1h H=4; 4h FH grid max +45.79 bps, H\* fragile → R1.4 mechanical robustness tie-break → H\*=12 all_legs), and EXP-037 confirmed one-shot on TEST: EURUSD-4h net +40.56 bps, ci_low_1s 21.94 > margin 8.42, phase Holm-4 adj_p ≈ 0.004; EXP-038 confirmed the BTC-exit baseline on the same stratum (+24.27, 15.43 > 3.78). XAUUSD-4h margin-bound fail (11.45 < 54.2 — R1.2 small-n calibration changed the verdict); USTEC fail; 5m/1h closed for this substrate under all three levers. G2 SATISFIED → operator selected Package B (exclusive, shares events with A) → Phase 009 spent the holdout shot **INCONCLUSIVE**: the TEST evidence is the final, permanently non-upgradable word. **Process lessons:** demote in-sample gate routes before results exist; adjudicate multi-experiment gates once at phase level on desk (R1.1 Holm-4, no self-declared `g2_satisfied`); calibrate small-n bootstrap at the realized cell structure (R1.2 margins flipped XAUUSD and later kept the holdout honest); handle selection fragility with predeclared mechanical tie-breaks (R1.4); two-speed gating worked — nothing closed on a wide CI, nothing promoted on one; G2-scale TEST estimates carry winner's-curse attenuation (+40.56 → +20.60 out of sample). Redirect: Tier C — HYP-001 direct S/R test, Stage-C branches. | [retrospective.md](checkpoints/2026-06-10-008-avwap-clinical-tradability/retrospective.md) |
| 2026-06-09-007-avwap-tradability-and-isolation | COMPLETED 2026-06-10 — **NOT_TRADABLE** (design §9; EXP-030/031 executed, both post-governance APPROVE; retrospective written 2026-06-10) | **The Phase-006 edge is real but cost-dominated in absolute P&L terms; its attribution is horizon-dependent.** EXP-030 INCONCLUSIVE (phase read NOT_TRADABLE): under the predeclared CONSERVATIVE event-level cost model, equal-weight cross-instrument net per-event expectancy is −6.74 bps [−7.04,−6.38] (5m) and −6.04 bps [−11.02,−1.53] (1h) — EVIDENCE_AGAINST — and +2.60 bps [−14.87,+19.28] (4h) — INCONCLUSIVE_SPANS_ZERO (n=187, power-limited). **Holdout-release gate (EXP-032) NOT passed; holdout stays sealed.** Central economics: the edge is *relative, not absolute* — gross absolute per-event returns (+0.76/+1.46/+10.10 bps) are an order of magnitude below the matched-control excess (+5.78/+23.38/+69.02 bps), so absolute P&L carries costs the control subtraction nets out; the non-binding companion (net matched-control excess) stays FOR on 1h/4h — Phase-006 gross edge not overturned. BTCUSD (16 bps RT) dominates the equal-weight cost drag; EURUSD-4h net +12.38 bps [+2.67,+21.46] survives descriptively (multiplicity-uncontrolled, not promoted). EXP-031 ISOLATION_READ_UNRESOLVED: ENTRY_DOMINANT at H=6 (s_entry 1.53/1.13/1.41 — BTC exit is a differential drag) but EXIT_DOMINANT at H=1 (exit cuts early losers) on all domains; additivity machine-precision; reconciles EXP-028 exactly. The exit is two mechanisms in one rule: short-horizon loss-cutter, long-horizon trend-truncator — the binding constraint on any future `/EXIT` redesign. **Process lessons:** predeclare the binding-vs-companion estimand split before costs; equal-weight aggregation lets one high-cost instrument veto a domain; two predeclared horizons + an UNRESOLVED class turned a would-be overconfident attribution into the true finding; check power vs estimand at scope time (4h was near-foreordained INCONCLUSIVE); post-run result-aware diffs route through Stage 4 (EXP-030 Revision 1). Redirect (operator-gated): per-instrument tradability screen w/ multiplicity control + financing, horizon-sweep diagnostic (EXP-033/DIAG-004), then `/EXIT` redesign or HYP-001 direct S/R test. | [retrospective.md](checkpoints/2026-06-09-007-avwap-tradability-and-isolation/retrospective.md) |
| 2026-06-08-006-avwap-evaluation-correction | COMPLETED — **EVAL_SUPPORTED (cTrader-confirmed)** (EXP-027/028/029 executed, all post-governance APPROVE; retrospective written 2026-06-09) | **The correction phase repaired the evaluation vehicle Phases 004/005 mis-applied, then re-screened the faithful strategy positive — confirmed on the production code path.** EXP-027 METHOD_VALID: a predeclared event-level method (per-event matched-control expectancy reusing the EXP-021/022 bootstrap/permutation/Holm machinery, recalibrated for the sparse regime on synthetic substrates only) shows controlled FPR (≤0.05 across the {3,6,12}% activity bracket) and finite MDE (1/4/32 bps on 5m/1h/4h) — the EXP-021/022 inference transfers to ~6%-active signals. EXP-028 EVAL_SUPPORTED: the unchanged faithful strategy is PRIMARY EVIDENCE_FOR on all three domains (+5.78/+23.38/+69.02 bps, Holm p=0.003) — the EXP-023 negative was a framing/dilution artifact, not absence of signal. EXP-029 CONSISTENT: the corrected, pyramid-inclusive C# `AvwapBounceModel` run bar-by-bar on cTrader reproduces EXP-028's PRIMARY excess on all three domains (\|Δeffect\|=0.007/0.054/0.000 bps; all five binding gates pass — entry signal ≥99.8% of EXP-020 triggers, pyramid counts ±0.5%, executed completion match rate 1.000), upgrading EXP-028 to cTrader-confirmed and extending VAL-002 pipeline parity to the AVWAP baseline. **Process lesson** (`EXP-028-omission.md`): a "faithful re-screen" must state its execution path (cTrader per-bar vs Python re-analysis) explicitly in scope; Stage 4 governance must check it against the lineage the faithfulness clause assumes. Open: HYP-001 (line S/R) untested; costs not deducted; holdout sealed. Does **not** overturn EXP-023's per-bar REFUTED (non-substitutable yardsticks). | [retrospective.md](checkpoints/2026-06-08-006-avwap-evaluation-correction/retrospective.md) |
| 2026-06-08-005-avwap-exit-and-branch-exploration | **HALTED 2026-06-08** — `HALTED_FRAMING_INVALID` (before Stage B/C; superseded by Phase 006) | **Halted because Stage A diagnosed the signal *within* the wrong evaluation vehicle instead of questioning the vehicle.** EXP-023/024/025 screened/diagnosed a ~6%-active event signal through a per-bar continuous-position referee calibrated only for ≥80%-active series (EXP-005); EXP-023's negative is dominated by ~16× denominator dilution, EXP-024's fork-(b) leg is a per-bar-floor category mismatch, and EXP-025's metric is confounded by the trigger definition (HYP-001 still untested). EXP-021/022 per-event evidence is **not** invalidated. Retained findings: edge is relative-not-absolute; trend-change exits cut losers. Dispositions: EXP-023 SUPERSEDED, EXP-024 RETAINED (fork discounted), EXP-025 INCONCLUSIVE (non-informative for HYP-001); EXP-026 `/EXIT` SHELVED; Stage C deferred. Redirect → Phase 006 (fix evaluation vehicle, then re-screen). Review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. | [retrospective.md](checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/retrospective.md) |
| 2026-06-07-004-avwap-signal-exploration | COMPLETED — **BASELINE_BRANCH_REFUTED** (EXP-020-023 executed; EXP-023 post-governance APPROVE; retrospective written 2026-06-08) | **The first real signal-exploration cycle reached its terminal screen and closed negative for the registered baseline branch.** EXP-020 SUPPORTED_FULL: the AVWAP state machine is deterministic and look-ahead safe, 12/12 cells reportable, 0 invariant failures. EXP-021 SUPPORTED: fixed-horizon bounce reaction positive on all domains (+3.8/+9.1/+37.6 bps, Holm p=0.0003). EXP-022 SUPPORTED: band-target/trend-change lifetime completion advantage positive on all domains (+23.9/+21.9/+26.4 pp, Holm p=0.0003). EXP-023 REFUTED: 12/12 cTrader cells admitted, same-feed Donchian reference aligned, holdout fence and C# smoke PASS, but 0/12 strict, 0/12 ratified-loose, and 0/12 revised-incremental passes; effects far below frozen floors. **Synthesis:** conditional AVWAP event evidence is real in this analysis set, but the untuned baseline position/exit overlay does not qualify as a cost-bearing tradable strategy. This is a baseline-branch negative, not a retirement of `CF-AVWAP-001`; follow-up requires new registered scopes such as EXIT, LB, MB, ATR, ALPHA, or BAND. | [retrospective.md](checkpoints/2026-06-07-004-avwap-signal-exploration/retrospective.md) |
| 2026-06-05-003b-incremental-unit-redesign | COMPLETED — **REVISED_UNIT_VALIDATED** (EXP-017-019 executed, pre+post governance APPROVE; pre-execution amendment B1 applied before any results) | **The framework conclusion is completed — Phase 004 unlocks.** Phase 003b removed the **L2 standalone-significance leg** that A1/F03 diagnosed as the EXP-015/BTCUSD refutation cause, leaving the portfolio-fitness gate `L1 ∧ L3 ∧ L4′ ∧ L5` (strict-L5 binding, L3 its precondition), and resolved the A1/F02 L4′/L5 freeze precondition by operator decision. Predeclared once, measured once (D-no-retune held; B1 changed no predeclared object). **EXP-017** SUPPORTED: 7/7 fixture verdicts, 28/28 retained-leg states, L2 absent 7/7, former-L2-fail fixture now passes. **EXP-018** SUPPORTED (the claim EXP-015 refuted, now holding): 126/126 construction-accepted cells PASS, FPR 0.0–0.004, finite worst-case MDEs 12/16/32 bps on 5m/1h/4h, EXP-015 synchronous/high-overlap/null_R corner PASS across all ρ in every domain; 36 high-ρ/low-overlap cells disclosed as construction-invalid. **EXP-019** SUPPORTED: dogfood rejects across all domains (0 strict/loose/incremental passes); nonredundant synthetic positive passes all three components in every domain. Concluded suite **{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 validated revised incremental/fitness unit}** is frozen — D-adopt (P3) satisfied. **Honest caveat:** the incremental screen is the coarsest (12/16/32 vs strict 1/4/12 and loose 0.5/2/8) — correct portfolio-fitness semantics bought at a higher detection floor; validation is on synthetic dependence draws, not real candidates or fresh regimes (holdout sealed). **Phase 004 unlocks behind its mandatory programme-level multiplicity-registry precondition (P3-§11).** | [retrospective.md](checkpoints/2026-06-05-003b-incremental-unit-redesign/retrospective.md) |
| 2026-06-04-003-ratification-and-incremental-unit | COMPLETED — **PARTIAL_SUCCESS** (EXP-012-016 executed; amendment A1 applied + Track B re-validated 2026-06-04/05) | **Two referees concluded; the fitness check is not.** Track A: EXP-012 ratified the EXP-011 loose point on fresh disjoint seeds (`payload_overlap_count=0`) and **adopted** τ 0.75/0.25/0.5 on 5m/1h/4h — FPR 0/4000, fresh MDEs reproduce Phase 002 to the grid (0.5/2/8 bps), 4h split gate agrees; the meta-Goodhart freeze Phase 002 deferred is now executed. Track B mirrored EXP-001→003: substrate PASS (EXP-013: 108/108 recovery, no phantom; 3 cells honestly `UNDER_POWERED` under A1/F01) and logic PASS (EXP-014: 7/7 verdicts, L3→reference-control, episode-aware `effective_n`), but the keystone **REFUTED** (EXP-015): FPR controlled yet no finite MDE in any domain, attributed by A1/F03 diagnostics to the **L2 standalone-significance leg driven by BTCUSD** (standalone TPR 0.0–0.136 at the 32 bps ceiling). EXP-016 correctly BLOCKED (refuted dependency + undefined dogfood book). Adversarial review (A1: F01 across-draw redundancy verdict, F03 diagnostics, F04 contiguous block length, F02 leg-conservatism freeze precondition) made passing *harder* and did not flip any verdict. Against §9 this is **PARTIAL_SUCCESS** — the suite ships as two referees only; the incremental unit goes to a follow-up. **Operator decision (2026-06-05, §11): Path B — open an incremental-unit follow-up checkpoint and fix the L2/BTCUSD failure (+ A1/F02 L4/L5 freeze precondition) before Phase 004**; Phase 004 stays blocked until that follow-up validates+calibrates the unit. | [retrospective.md](checkpoints/2026-06-04-003-ratification-and-incremental-unit/retrospective.md) |
| 2026-06-03-002-referee-refinement-and-stringency | COMPLETED (7/7 EXP executed; §9 a–d met + EXP-009/010 delivered) | **Keystone CLOSED: the strict gate is an honest detection floor, not structurally blind** — EXP-005's realistic near-MDE candidate is detected on every domain (TPR 1.000/0.985/0.947 at 1.0× MDE, FPR=0; all 12 per-instrument rows DETECTED_FLOOR), though detection below the MDE is unreliable (0.5× MDE TPR 0.024/0.371/0.502). The L5 stringency lever is one-dimensional (EXP-006 frontier; lenient L5 ≡ τ=0 ≡ drop-L5, EXP-007 REFUTED) and lower τ buys MDE partly with sub-material passes (5m ≈0.50 at zero-buffer). Pooled map is conservative — per-instrument MDEs only lower (EXP-008: EURUSD/1h, EURUSD+XAUUSD/4h). Untuned simple strategies remain net losers below every MDE (EXP-009). Split-robust on 5m/1h; 4h toward a *lower* MDE under more-OOS protocols (EXP-010, corrected). EXP-011 recommends τ 0.75/0.25/0.5 (1h robust, 5m/4h loss-sensitive); **nothing adopted** — fresh-draw ratification is Phase 003. Framework characterization concluded; finalization (freeze) deferred. | [retrospective.md](checkpoints/2026-06-03-002-referee-refinement-and-stringency/retrospective.md) |
| 2026-06-01-001-thesis-qualification-calibration | COMPLETED (4/4 EXP SUPPORTED) | Referee operating characteristics measured (design's success deliverable met): gate-stack FPR=0 at all domains/α vs minimal FPR≈α, bought with 2–8× economic MDE (net 1/4/12 bps on 5m/1h/4h); L5 materiality is the binding, α-invariant leg. H-keystone is **bounded, not closed** — EXP-004 dogfood is a null anchor (untuned Donchian/MA carry ~0 edge below every MDE), so structural blindness is true-negative-confirmed but the gate's detection of a weak *real* edge near the MDE is untested. Next: EXP-005 near-MDE detection anchor. | [retrospective.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/retrospective.md) |



## EXP-001 — Synthetic Substrate Validation

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains via `xen.bar_aggregator.aggregate_ohlc`

### Hypothesis Tests

1. **Hypothesis**: The known-null generators produce no oracle-recoverable edge, and the known-positive generator carries the planted oracle-recoverable net edge, on real analysis-set prices for each of the 5m, 1h, and 4h domains.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% 1-minute analysis slice. No chart-type views.
- **Features**: Close-to-Close next-step real returns; oracle state-following positions; known-null (bar-permutation, random-signal) and known-positive (state-aligned drift) generators; P0 aggregation-integrity checks with negative controls; coverage retention grid.
- **Parameter ranges**: domains {5, 60, 240} min; coverage grid {strict, 0.90, 0.80}; net edge grid `m ∈ {0, 0.5, 1, 2, 4, 8, 12, 16, 24, 32}` bps; 200 null draws/generator, 100 positive draws/edge.
- **Exclusions**: final 30% global holdout, chart-type signals, referee operating-characteristic measurement, Donchian/MA dogfood, parameter tuning, bid/ask spread estimation, data-inferred costs.
- **Constraints**: first-70% analysis slice only; shared `CloseTime` split across domains; fixed seeds; real-price outcome discipline; closed-form injection `delta = m + cost`.

### Results / Observations

- `p0_aggregation_checks.csv`: 56/56 PASS at {5, 240} min (4 instruments), including all 4 negative controls detected per period; 0 oracle OHLC mismatches.
- `run_metadata.json`: `overall_status: PASS`, `p0_pass: true`, `substrate_pass: true`, `inconclusive_cells: 0`, `underpowered_cells: 5`.
- Known-null cells (24): mean gross oracle effect ∈ [−0.087, +0.103] bps, every percentile CI brackets zero (200 draws/cell).
- Known-positive recovery: all non-zero cells recover planted `m` within `max(0.5 bps, 15% of m)`; high-sample domains recover to <0.01 bps (e.g. EURUSD/5m m=32 → 32.0005).
- `underpowered_cells.csv`: 5 per-cell INCONCLUSIVE cells, all 4h — BTCUSD m=1,2; USTEC m=1,2; XAUUSD m=1 — recovered mean but across-draw CI straddles zero; all below the 4h materiality threshold (3.0 bps).
- `analysis_metadata.csv`: post-slice analysis rows reproduce VAL-001 exactly (BTCUSD 1,088,960; EURUSD 872,242; USTEC 830,541; XAUUSD 830,671).
- Coverage retention worsens 5m→4h and improves as `min_coverage` relaxes; 4h/0.90 dropped-window fraction 0.025–0.131.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Every P0 check passes, every known-null is indistinguishable from zero, and every known-positive recovers the planted edge within tolerance; the only shortfalls are five 4h sub-material cells, classified by the predeclared §11/D-prec criteria as under-powered (INCONCLUSIVE), not failures. The substrate gate is PASS, so EXP-002/003 may build on it.

### Hypothesis-Agnostic Observations

- 4h effective sample (~2,700–4,400 returns/instrument) bounds attainable precision; EXP-003's 4h power curve near materiality will carry wide CIs.
- Two structurally different nulls agreeing at ≈0 makes accidental recoverable structure implausible.
- The known-positive "significance" leg measures across-draw recovery precision, not single-series detectability — the latter is EXP-003's measurement.

---

## EXP-002 — Referee Golden-Fixture Correctness

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: EURUSD label only (fixture diagnostics; no market data read)
**Data Views / Feature Categories**: Deterministic in-memory return-space golden fixtures; EXP-001 dependency metadata

### Hypothesis Tests

1. **Hypothesis**: The minimal baseline referee and the 5-check gate-stack referee reproduce predeclared hand-computed verdicts on deterministic golden fixtures, while the gate stack records every leg independently.

### Scope

- **Instruments**: EURUSD label only (referee-logic test, not market behaviour).
- **Data Views / Feature Categories**: five deterministic return-space fixtures (positive oracle, null/negative, one-sided readiness, sub-material, naive-equivalent).
- **Features**: minimal-baseline and gate-stack verdicts; L1–L5 leg states; block-bootstrap CI; cost/materiality application.
- **Parameter ranges**: `alpha = 0.05`; `n_bootstrap = 1000`; EURUSD/5m cost 1.0 bps, materiality 0.5 bps.
- **Exclusions**: FPR/TPR/MDE measurement, real candidates, parameter tuning, chart-type signals, any raw Parquet load, holdout.
- **Constraints**: EXP-001 must record `overall_status == PASS`; fixed deterministic seeds; gate stack must evaluate all five legs without short-circuit.

### Results / Observations

- `golden_fixture_results.csv`: 10/10 verdict checks PASS. positive_oracle (min PASS/gate PASS, +6.0 net), null_negative_edge (REJECT/REJECT, −3.0), readiness_one_sided (PASS/REJECT, +7.0), materiality_too_small (PASS/REJECT, +0.2), naive_equivalent (PASS/REJECT, +1.667). Gate effect = minimal effect − 1.0 bps cost in every row.
- `leg_exposure_matrix.csv`: 25/25 leg-exposure checks PASS; all five legs recorded for every fixture (no short-circuit).
- Leg isolation: L1 via readiness_one_sided (0 down-episodes), L5 via materiality_too_small, L3 via naive_equivalent (`ci_vs_naive_lower = 0`), L3+L5 via null_negative_edge, all-pass via positive_oracle.
- `run_metadata.json`: `overall_status: PASS`. Independent reproduction matched all rows bit-for-bit.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Both referees reproduce every predeclared golden-fixture verdict and the gate stack exposes all five legs without short-circuiting, satisfying the scope's Evidence-FOR criteria; the referee logic is approved for EXP-003.

### Hypothesis-Agnostic Observations

- The `materiality_too_small` minimal row reports a degenerate `effective_n = 0.9` (block-length capped at the limit) because its series is constant to floating-point dust; deterministic, immaterial to the verdict, and impossible on real returns.
- The same data yielding minimal-PASS but gate-REJECT (readiness_one_sided, materiality_too_small) cleanly demonstrates what each extra gate leg buys over the minimal baseline.

---

## EXP-003 — Referee Operating-Characteristic Calibration (Keystone)

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains

### Hypothesis Tests

1. **Hypothesis**: The 5-check gate stack has a measurable empirical economic MDE at FPR ≤ α₀ = 0.05 on each domain, and its operating characteristics can be compared against the minimal baseline referee without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: paired known-null (bar-permutation, random-signal) and known-positive (state-aligned drift) draws; minimal-baseline and gate-stack verdicts with all five legs; block-bootstrap CIs; Wilson-interval FPR/TPR; empirical MDE.
- **Parameter ranges**: α grid {0.10, 0.05, 0.01}; edge grid {0,0.5,1,2,4,8,12,16,24,32} bps; 500 null draws/generator (n=4000/cell pooled over instruments), 500 positive draws/edge (n=2000/cell), 1000 inner bootstrap resamples/verdict.
- **Exclusions**: Donchian/MA dogfood interpretation, referee redesign, loss-function tuning, walk-forward, chart-type candidates, parameter optimization, holdout.
- **Constraints**: EXP-001 and EXP-002 must PASS; first-70% slice only; shared `CloseTime` split across domains; real-price `Close` outcomes; block length on train only; identical (paired) draws to both referees.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `mde_cells: 18`, `mde_status_counts: {PASS: 18}`.
- Gate-stack FPR = 0.0 (0/4000) at every domain and every α (`fpr_summary.csv`); minimal-baseline FPR ≈ α and ≤ α (e.g. 1h: 0.005 / 0.0248 / 0.0493 at α = 0.01 / 0.05 / 0.10).
- Empirical MDE at α = 0.05 (`mde_summary.csv`): gate stack 1.0 (5m) / 4.0 (1h) / 12.0 (4h) bps; minimal baseline 0.5 / 0.5 / 2.0 bps. Gate MDE identical across the α grid; minimal-baseline 4h MDE moves 4.0 → 2.0 → 1.0 across α = 0.01 / 0.05 / 0.10.
- Per-leg null pass rates (α = 0.05, all domains): L1 = L2 = 1.000, L3 = L4 = L5 = 0.000. Near the MDE, L5 is the lagging leg (4h m=2 → L5 = 0.006; 1h m=2 → L5 = 0.371; 4h m=12 → L5 = 0.935; 1h m=4 → L5 = 0.977).
- TPR monotone non-decreasing to 1.0 across the grid (`tpr_summary.csv`); all 18 cells meet FPR half-width ≤ 0.03 and TPR half-width ≤ 0.05.
- Effective N (blocks) reported per cell (e.g. BTCUSD 4h ≈ 1335). An independent end-to-end reproduction of a BTCUSD/4h cell matched `draw_verdicts.csv` bit-for-bit.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Both referees have a usable-precision operating-characteristic map on all three domains; all 18 cells yield a finite MDE at controlled FPR (Evidence-FOR criteria met). The measured keystone result is the per-domain stringency↔sensitivity trade-off: the gate stack drives FPR from ≈ α to 0 at the cost of a 2–8× larger economic MDE.

### Hypothesis-Agnostic Observations

- L5 materiality dominates the gate stack's false negatives and sets its MDE, making the gate MDE α-invariant; the α grid moves only the minimal baseline's MDE.
- Per-domain rates pool four instruments of heterogeneous cost (1–10 bps) and dispersion, so each MDE is a domain aggregate; per-instrument MDEs could be lower (relevant to EXP-004).
- Whether the gate MDE sits above where plausibly-real edges live (structural blindness) is not decided here — it needs the EXP-004 dogfood anchor. The 4h gate MDE (12 bps) exceeds the 4h materiality threshold (3 bps).

---

## EXP-004 — Real Dogfood Consistency Anchor

**Status**: SUPPORTED
**Date**: 2026-06-02
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Real Donchian-channel breakout (lookback 20) and MA-crossover (fast 20, slow 50) verdicts are consistent with where their measured net effect sizes fall on the calibrated per-domain MDE map from EXP-003.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: fixed Donchian(20) breakout and MA(20,50) crossover positions; minimal-baseline (gross) and 5-check gate-stack (net-of-cost) referee verdicts at α=0.05; block-bootstrap effect CIs; consistency vs the EXP-003 MDE map.
- **Parameter ranges**: α=0.05; 1000 inner block-bootstrap resamples/verdict; Donchian lookback 20; MA fast 20 / slow 50; fixed and untuned.
- **Exclusions**: final 30% global holdout, parameter optimization, strategy improvement, chart-type candidates, stop/target logic, walk-forward, and any revision of referee rules based on dogfood results.
- **Constraints**: EXP-003 MDE artifact must exist (cell inconclusive where MDE missing/imprecise); first-70% slice only; shared 1-minute `CloseTime` train/test boundary across domains; real domain `Close` outcomes with flat scoped costs; look-ahead-safe positions (Donchian prior windows, MA closes at bar `t`), evaluated on `t→t+1` returns.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, α=0.05, 1000 bootstrap resamples, Donchian 20, MA 20/50.
- `dogfood_consistency.csv`: 48/48 cells `consistency_status = PASS`, all `reason = matched_reject`; 0 FAIL, 0 INCONCLUSIVE.
- `dogfood_effects.csv`: all 48 verdicts REJECT (both referees). Gate-stack (net) effects range −12.199 (BTCUSD/4h/MA) to +0.045 (EURUSD/4h/Donchian) bps; minimal-baseline (gross) effects range ≈ [−2.20, +1.32] bps with every CI bracketing or below zero (e.g. XAUUSD/4h/MA +1.317 [−1.445, +4.035]; USTEC/1h/Donchian +0.226 [−0.178, +0.680]).
- EXP-003 α=0.05 MDE map (loaded, audit-verified): gate stack 1.0/4.0/12.0 bps and minimal baseline 0.5/0.5/2.0 bps for 5m/1h/4h; grid uncertainty 0.25/1.0/2.0 (gate) and 0.25/0.25/0.5 (minimal). Every measured effect sits below its domain MDE.
- Effective N: 5m ~49,608–65,144; 1h ~4,155–5,430; 4h ~902–1,335. `block_length = 1` for all 48 cells.
- Cost accounting verified: minimal(gross) − gate(net) effect = cost × active-bar fraction (exact per-instrument cost for always-active MA; in `[0, cost]` for frequently-flat Donchian).
- `analysis_metadata.csv`: per-instrument `analysis_end` precedes each source file's end date, confirming the final 30% holdout was not loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Every cell meets the predeclared Evidence-FOR criterion — a reject with the measured effect below its domain MDE — with no Evidence-AGAINST and no inconclusive cells, so real Donchian/MA verdicts agree with their positions on the EXP-003 calibrated MDE map (48/48 consistent) and no synthetic-vs-real DGP gap is surfaced.

### Hypothesis-Agnostic Observations

- The dogfood set is a **null/lower anchor** for H-keystone: untuned Donchian/MA carry no statistically positive edge even gross of cost, so they locate simple intraday edges at ≈0 beneath every per-domain MDE; this is consistent with the gate stack's rejections (true negatives) but does not, on its own, resolve whether the gate MDE sits above genuinely weak real edges — structural blindness is bounded, not closed.
- The gate stack's systematic negativity is mechanical (cost charged to active bars), not a negative edge; the gross minimal-baseline read is the cleaner edge test and is also non-positive.
- `block_length = 1` across all cells means per-bar Donchian/MA strategy returns showed negligible autocorrelation, so the stationary bootstrap reduced to i.i.d. resampling and effective N equals the raw test-bar count.

---

## EXP-005 — Near-MDE Realistic-Candidate Detection Anchor

**Status**: SUPPORTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: On each scoped domain, the frozen Phase 001 5-check gate stack detects an imperfect realistic candidate whose expected net real-price edge is at least the EXP-003 gate-stack MDE, with pooled-domain TPR >= 0.80 at `FPR <= alpha0 = 0.05`.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: latent state `S_t in {-1,+1}`; imperfect candidate `C_t in {-1,0,+1}` with `p_active=0.80` and `q_match=0.75`; paired null draws (raw returns and bar-permutation); known-positive latent-state drift calibrated so the candidate's expected all-eligible-row net edge equals the target edge; minimal-baseline and gate-stack verdicts; Wilson FPR/TPR summaries; pooled-domain and per-instrument detection rows.
- **Parameter ranges**: alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0=0.05`; EXP-003 gate MDE map at alpha0 = 5m `1.0`, 1h `4.0`, 4h `12.0` bps; edge multipliers `{0.5, 1.0, 1.5, 2.0}`; 500 positive draws per edge/instrument/domain; 500 null draws per null generator/instrument/domain; 1000 bootstrap resamples/verdict.
- **Exclusions**: final 30% global holdout, chart-type signals, real strategy tuning, loss-function tuning, referee redesign, threshold sweeping, lenient-L5 variants, walk-forward validation, stop/target logic, bid/ask spread estimation, and any use of Phase 002 outcomes to alter the candidate construction.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE + finite MDE artifacts required; Phase 002 predeclaration confirmation recorded before measurement; first-70% slice only; shared 1-minute `CloseTime` train/test boundary across domains; real domain `Close` outcomes plus predeclared known-positive drift; frozen `xen.referee_calibration` harness reused unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{exp001_status: PASS, exp003_status: COMPLETE}`, `candidate_sanity.sanity_pass: true`, `domain_status: {5m: DETECTED_FLOOR, 1h: DETECTED_FLOOR, 4h: DETECTED_FLOOR}`.
- Candidate construction sanity passed: overall active rate `0.799997`, active match rate `0.750005`; per-cell active-rate range `0.798518` to `0.800561`; per-cell match-rate range `0.749482` to `0.750623`; positive calibration absolute error range `0.000005` to `0.129769` bps.
- Gate-stack pooled FPR at `alpha0=0.05` is `0/4000` in every domain, Wilson half-width `0.000480`; minimal-baseline diagnostic FPR is `0.02375` (5m), `0.02350` (1h), and `0.02500` (4h).
- Gate-stack pooled TPR at `1.0 x` MDE: 5m `1.0000` (2000/2000, half-width `0.000959`), 1h `0.9850` (1970/2000, half-width `0.005403`), 4h `0.9465` (1893/2000, half-width `0.009890`).
- Gate-stack TPR at `0.5 x` MDE remains below target: 5m `0.024`, 1h `0.371`, 4h `0.502`; at `1.5 x` and `2.0 x` it is effectively saturated in all domains.
- All 12 per-instrument headline rows at `1.0 x` MDE classify `DETECTED_FLOOR` with `under_powered=false`; weakest headline cell is BTCUSD/4h with TPR `0.828` and half-width `0.0330`.
- Audit verdict PASS: result tables internally consistent; independent recomputation of FPR/TPR summaries from 216,000 verdict rows found zero mismatches; no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The frozen gate stack detects the predeclared imperfect realistic candidate at each domain's EXP-003 MDE while controlling FPR. EXP-005 therefore closes the Phase 001 open keystone for this candidate class: the oracle-calibrated MDE map is an honest detection floor here, not evidence of structural blindness.

### Hypothesis-Agnostic Observations

- The strict gate remains conservative: zero pooled null passes for the gate stack, while the minimal baseline sits near nominal but below `alpha0`.
- The exact-MDE pass does not imply reliable detection below the MDE; all three `0.5 x` rows fail the TPR target, especially 5m (`0.024`).
- The pooled-domain pass is not masking an instrument-level headline failure under the approved precision rule, but EXP-008 remains needed because EXP-005 does not estimate per-instrument MDE.
- `block_length = 1` across all verdict rows means the stationary bootstrap reduced to i.i.d. resampling under the frozen estimator; this does not invalidate EXP-005 but preserves the value of EXP-010 split/dependence stress testing.

---

## EXP-006 — L5 Materiality Threshold Sweep

**Status**: SUPPORTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through EXP-003 draw artifacts)
**Data Views / Feature Categories**: EXP-003 draw-level gate-stack verdicts for 5m, 1h, and 4h OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis / exploratory question**: How do the frozen gate stack's FPR and economic MDE vary as the L5 materiality threshold magnitude is swept per domain?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003.
- **Data Views / Feature Categories**: EXP-003 verdict-level artifacts only; no new market-data measurement.
- **Features**: Gate-stack draw pass states, L1-L4 leg states, `ci_lower_bps`, `materiality_bps`, swept `L5_tau = ci_lower_bps > tau_bps`, Wilson FPR/TPR, grid-defined MDE.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; threshold multipliers `{0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00}`; EXP-003 planted-edge grid including `0.0` through `32.0` bps.
- **Exclusions**: Lenient-L5 mechanism from EXP-007, near-MDE realistic candidates, per-instrument MDE de-pooling, loss-function selection, threshold adoption, chart-type signals, and referee redesign.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; result-level post-processing preferred; final 30% global holdout never loaded; L1-L4, costs, materiality constants, sample membership, denominators, and real-price EXP-003 outcomes unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `strict_reference_pass: true`, `gate_draw_rows: 216000`, 7 threshold multipliers.
- `strict_reference_check.csv`: 9/9 domain/alpha rows matched EXP-003 exactly; `draw_mismatch_count = 0` and `mde_match = true` for every row.
- `threshold_draw_verdicts.csv`: 1,512,000 rows (`216,000 x 7`).
- `threshold_fpr_summary.csv`: every domain/alpha/threshold cell has FPR `0/4000`, Wilson half-width `0.000480`.
- `threshold_mde_summary.csv`: 63/63 rows `status = PASS`.
- At `alpha0=0.05`, strict `tau=1.0` MDEs were 5m `1.0`, 1h `4.0`, and 4h `12.0` bps; zero-buffer `tau=0.0` MDEs were 5m `0.5`, 1h `2.0`, and 4h `8.0` bps.
- At `alpha0=0.05`, high-threshold `tau=2.0` MDEs rose to 5m `2.0`, 1h `8.0`, and 4h `16.0` bps.
- TPR at the alpha0 zero-buffer MDE was 5m `1.000` at `0.5` bps, 1h `0.924` at `2.0` bps, and 4h `0.902` at `8.0` bps.
- Audit verdict PASS: no critical or warning issues; independent CSV aggregation verified row counts, denominators, strict-reference equality, and selected FPR/TPR rates.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The exploratory measurement delivered the scoped L5 lever curve with usable precision in every cell. Lower L5 thresholds reduced MDE without increasing pooled FPR on the EXP-003 draw substrate, and the strict `tau=1.0` rows reproduced EXP-003 exactly.

### Hypothesis-Agnostic Observations

- L5 threshold magnitude is a practical stringency lever, but EXP-006 does not adopt an operating point.
- The zero-buffer endpoint is the key input to EXP-007 and EXP-011.
- FPR staying zero likely reflects other gate legs remaining restrictive on the scoped null generators; fresh-draw adoption remains a later-phase decision.
- Results are pooled by domain, so EXP-008 remains necessary for instrument-level heterogeneity.

---

## EXP-007 — Lenient-L5 Referee Variant

**Status**: REFUTED
**Date**: 2026-06-03
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through EXP-003/EXP-006 draw artifacts)
**Data Views / Feature Categories**: EXP-003 gate-stack draw verdicts plus EXP-006 threshold frontier artifacts for 5m, 1h, and 4h OHLC domains; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The predeclared lenient L5 variant lowers the gate stack's economic MDE relative to the frozen strict gate while holding `FPR <= alpha0 = 0.05`, beyond what is achieved by the EXP-006 threshold-magnitude frontier.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003 and EXP-006.
- **Data Views / Feature Categories**: EXP-003 draw-level verdict artifacts and EXP-006 threshold-frontier artifacts; no new market-data measurement.
- **Features**: `L5_lenient = ci_lower_bps > 0.0`, unchanged L1-L4, strict and lenient pass states, verdict-level equality against EXP-006 `tau=0`, Wilson FPR/TPR, grid-defined MDE, and economically sub-material pass rates.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; EXP-003 planted-edge grid; EXP-006 threshold frontier for comparison.
- **Exclusions**: Adoption/freezing of the lenient variant, loss-function selection, changing L1-L4, changing costs/materiality constants, adding thresholds after reading EXP-006, chart-type signals, and referee redesign.
- **Constraints**: EXP-001 PASS, EXP-003 COMPLETE, and EXP-006 COMPLETE with `strict_reference_pass = true`; final 30% global holdout never loaded; real-price EXP-003 outcomes reused unchanged; sub-material denominator is lenient positive passes per domain/alpha/edge.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `structural_equivalence_pass: true`, headline alpha0 verdict `EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN` for 5m, 1h, and 4h.
- `lenient_draw_verdicts.csv`: 216,000 rows.
- `structural_equivalence_check.csv`: 9/9 rows have `lenient_vs_dropl5_mismatch = 0`, `lenient_vs_exp006_tau0_mismatch = 0`, `lenient_vs_exp006_tau0_unmatched = 0`, `draws_match_dropl5 = true`, `draws_match_exp006_tau0 = true`, and `lenient_eq_tau0_mde = true`.
- `lenient_fpr_summary.csv`: lenient FPR `0/4000` in every domain/alpha row, Wilson half-width `0.000480`.
- At `alpha0=0.05`, lenient MDEs were 5m `0.5`, 1h `2.0`, and 4h `8.0` bps versus strict `1.0`, `4.0`, and `12.0` bps. These lenient MDEs equal the EXP-006 zero-buffer and best acceptable frontier MDEs.
- At the alpha0 lenient MDE, TPR was 5m `1.000` (`2000/2000`), 1h `0.924` (`1848/2000`), and 4h `0.902` (`1804/2000`).
- At the alpha0 lenient MDE, economically sub-material pass rates were 5m `0.4965`, 1h `0.054654`, and 4h `0.0`.
- `lenient_vs_frontier.csv`: all 9 domain/alpha rows have `improves_beyond_frontier = false` and `verdict = EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN`.
- Audit verdict PASS: no critical or warning issues; independent CSV aggregation verified row counts, denominators, structural-equivalence counts, and selected FPR/TPR/sub-material rates.

### Hypothesis-Specific Conclusion

**REFUTED**

Lenient L5 controlled FPR and lowered strict MDE, but it did not lower MDE beyond the EXP-006 threshold frontier. It exactly matched EXP-006 `tau=0` and drop-L5 at the verdict and MDE levels, so H-lenient's structural-gain claim is refuted by the predeclared Evidence-AGAINST criterion.

### Hypothesis-Agnostic Observations

- The useful object for synthesis is the EXP-006 zero-buffer endpoint plus EXP-007's sub-material accounting, not a distinct lenient-L5 mechanism.
- The 5m sub-material rate at the lenient MDE (`0.4965`) is just below the `0.50` cutoff, so 5m zero-buffer sensitivity should be treated cautiously in EXP-011.
- Because L3 already requires `ci_lower_bps > 0`, removing L5's materiality buffer makes L5 redundant under the frozen harness.
- No Phase 002 result adopts or freezes a new referee; Phase 003 fresh-draw ratification remains required for any operating-point change.

---

## EXP-008 - Per-Instrument MDE De-Pooling

**Status**: SUPPORTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-003 gate-stack draw verdicts for 5m, 1h, and 4h OHLC domains, de-pooled by instrument; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Per-instrument gate-stack economic MDEs differ materially from the Phase 001 four-instrument pooled domain MDEs, where material means `|per_instrument_MDE - pooled_MDE| >= max(0.5 bps, 20% of pooled_MDE)` at `alpha0 = 0.05`.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: EXP-003 verdict-level artifacts only; no new market-data measurement.
- **Features**: Gate-stack draw pass states, per-instrument Wilson FPR/TPR, grid-defined per-instrument MDE, pooled-vs-instrument material-difference flag.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; EXP-003 edge grid; TPR target `0.80`; frozen material margin `max(0.5 bps, 20% of pooled_MDE)`.
- **Exclusions**: Fresh draw generation, new market-data measurement, chart-type signals, referee redesign, strategy candidates, split-protocol comparison, loss-function selection, and operating-point adoption.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; final 30% global holdout never loaded; EXP-003 sample membership, denominators, costs, materiality, and real-price outcomes reused unchanged.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `gate_draw_rows: 216000`, `hpool_rollup: {hpool_verdict: SUPPORTED, reportable_cells_alpha0: 12, material_cells_alpha0: 3}`.
- `per_instrument_mde_summary.csv`: 36/36 instrument/domain/alpha rows `status = PASS`.
- At `alpha0=0.05`, gate FPR was `0/1000` in every instrument/domain cell, Wilson half-width `0.001913`; TPR rows used `n=500`, max Wilson half-width `0.043182`.
- Material alpha0 differences:
  - EURUSD/1h: per-instrument MDE `2.0` bps vs pooled `4.0` bps; delta `-2.0`; margin `0.8`.
  - EURUSD/4h: per-instrument MDE `8.0` bps vs pooled `12.0` bps; delta `-4.0`; margin `2.4`.
  - XAUUSD/4h: per-instrument MDE `8.0` bps vs pooled `12.0` bps; delta `-4.0`; margin `2.4`.
- All 5m per-instrument MDEs equaled the pooled 5m MDE of `1.0` bps.
- Audit verdict PASS: independent regrouping from EXP-003 draw verdicts found 0 FPR mismatches and 0 TPR mismatches.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The predeclared Evidence-FOR criterion is met because at least one reportable per-instrument cell differs materially from the pooled MDE. The pooled EXP-003 MDE map masks lower per-instrument MDEs in EURUSD/1h and EURUSD/XAUUSD 4h.

### Hypothesis-Agnostic Observations

- 5m shows no visible per-instrument heterogeneity at the EXP-003 grid resolution.
- The material differences are in the lower-MDE direction, making the pooled map conservative for those cells rather than overly permissive.
- EXP-008 sharpens the map for EXP-011 but does not adopt per-instrument thresholds.

---

## EXP-009 - Broadened Untuned Strategy Effect-Size Distribution

**Status**: MEASUREMENT COMPLETE (exploratory)
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; six fixed untuned simple strategy families; no chart-type views

### Hypothesis Tests

1. **Hypothesis / exploratory question**: Where do the net and gross effect sizes of a broadened set of untuned, fixed-parameter simple strategies sit relative to each domain's EXP-003 MDE?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: Donchian(20), MA(20/50), RSI(14), Bollinger(20, 2.0), MACD(12,26,9), ROC(20) positions; frozen minimal-baseline and gate-stack referee effects; MDE location classification; domain/family distribution summaries.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; 1000 bootstrap resamples; fixed strategy parameters as named.
- **Exclusions**: Strategy tuning, ensembling, stops/targets, chart-type signals, per-instrument MDE estimation, split-protocol variation, loss-function selection, referee redesign, and any per-strategy qualification verdict.
- **Constraints**: EXP-003 COMPLETE and EXP-004 PASS required; first-70% analysis slice only; shared `CloseTime` split; `t -> t+1` real `Close` returns; all warmup/NaN positions flat, not dropped.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{exp003_status: COMPLETE, exp004_status: PASS}`.
- `strategy_verdicts.csv`: 432 rows = 6 strategies x 4 instruments x 3 domains x 2 referees x 3 alphas.
- `strategy_effects.csv`: 144 alpha0 effect rows; 72 gate-stack rows.
- Gate-stack MDE location: 72/72 cells `below_MDE`; 0 `near_MDE`; 0 `at_or_above_MDE`.
- Domain gate-stack net-effect summaries:
  - 5m median `-1.018395` bps, IQR `[-3.007847, -0.406185]`, range `[-9.987340, -0.069953]`.
  - 1h median `-0.998325` bps, IQR `[-2.878832, -0.383782]`, range `[-10.949345, -0.080834]`.
  - 4h median `-0.952547` bps, IQR `[-2.318087, -0.098853]`, range `[-13.029254, +0.045022]`.
- Largest positive gate-stack point estimate: EURUSD/4h Donchian(20) `+0.045022` bps, CI `[-0.390681, +0.514643]`, below 4h gate MDE `12.0` bps.
- Effective N ranged from `902` to `65144`; `block_length = 1` for all 72 gate cells.
- Audit verdict PASS: no critical or warning issues; output dimensions, ranges, causal indicator construction, and real-price discipline verified.

### Hypothesis-Specific Conclusion

**MEASUREMENT COMPLETE (exploratory)**

EXP-009 is exploratory, but its scoped deliverable was produced. The broadened fixed simple-strategy distribution sits below every domain MDE, strengthening the EXP-004 lower anchor rather than surfacing a near-MDE real candidate. The cells are mostly **net-negative** after cost (medians ~ -1 bps), so this is a lower anchor of net losers, not small positive edges sitting just under the floor.

### Hypothesis-Agnostic Observations

- Simple untuned standalone strategies remain a lower anchor (mostly net-negative after cost) after broadening from 2 to 6 strategy definitions.
- Cost-applied net effects are frequently negative, especially active BTCUSD trend/momentum cells.
- The result does not refute tuned, ensemble, or incremental-information candidates; those require new predeclared scopes.

---

## EXP-010 - Split-Protocol Robustness of the Referee

**Status**: PARTIALLY REFUTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain)
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; regenerated known-null and known-positive referee-calibration draws; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: Alternative within-analysis-set split protocols - anchored walk-forward and purged/embargoed CV - do not materially change the frozen referee's pooled-by-domain gate-stack FPR and economic MDE versus the mandated single chronological split.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain to match EXP-003.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: Single chronological split, anchored walk-forward K=5, purged/embargoed CV K=5, regenerated known-null and known-positive draws, frozen minimal-baseline and gate-stack verdicts, Wilson FPR/TPR, grid MDE, reference-reproduction check.
- **Parameter ranges**: Alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; EXP-003 edge grid; 250 null draws per null generator; 250 positive draws per edge; 1000 bootstrap resamples; walk-forward K=5; purged CV K=5; purge 1 bar; embargo `max(1, block_length)`.
- **Exclusions**: Protocol adoption, per-instrument de-pooling, broadened strategy set, near-MDE candidate, L5 threshold/lenient variants, referee redesign, chart-type signals, and holdout use.
- **Constraints**: EXP-001 PASS and EXP-003 COMPLETE required; all protocols operate only within the first-70% analysis set; fold boundaries mapped from shared 1-minute `CloseTime`; referee costs/materiality/legs/bootstrap frozen.

### Results / Observations

> **Corrected 2026-06-04 (adversarial review F01).** The original multi-fold wrapper combined folds by concatenating per-fold bootstrap-mean distributions, giving multi-fold protocols a per-fold-sized CI on a pooled-OOS estimate and spuriously inflating walk-forward MDE on 1h/4h. The wrapper now uses a test-size-weighted, per-resample average of per-fold bootstrap means (stratified pooled-OOS bootstrap); single-fold is bit-identical to the frozen referee. The numbers below are the corrected re-run.

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `reference_reproduction_pass: true`, `hsplit_verdict_by_domain: {5m: SUPPORTED, 1h: SUPPORTED, 4h: FALSIFIED}`.
- `protocol_draw_verdicts.csv`: 594,000 rows, matching the scoped draw/protocol/referee/alpha budget.
- `reference_reproduction_check.csv`: 9/9 domain/alpha rows have `fpr_consistent = true` and `mde_consistent = true`.
- At `alpha0=0.05`, gate FPR was `0/2000` for every domain/protocol, Wilson half-width `0.000959`.
- At `alpha0=0.05`, gate MDEs:
  - 5m: single `1.0`, walk-forward `1.0`, purged CV `1.0` bps.
  - 1h: single `4.0`, walk-forward `4.0`, purged CV `4.0` bps.
  - 4h: single `12.0`, walk-forward `8.0`, purged CV `8.0` bps.
- `protocol_comparison.csv`: 5m and 1h non-material for both alternatives; 4h walk-forward and purged CV both material with delta `-4.0` vs margin `2.4` (lower MDE — more OOS rows).
- Matched-draw CI widths now decrease with `effective_n` (single 2.57 @1056 > walk-forward 1.74 @1760 > purged-CV 1.24 @3515), confirming the artifact is fixed. Re-audit verdict PASS.

### Hypothesis-Specific Conclusion

**PARTIALLY REFUTED**

H-split is SUPPORTED on 5m and 1h and FALSIFIED only on 4h. Unlike the original run, the falsification is a single domain and points the other way: the more-OOS alternative protocols (walk-forward ~0.5n, purged CV ~all n) detect a one-grid-step smaller edge than the conservative single split (~0.3n OOS) at the data-poorest domain. This is an OOS-sample-size effect (adversarial-review F02), not a referee-logic change, and FPR stays controlled.

### Hypothesis-Agnostic Observations

- Walk-forward and purged CV agree at 4h, so the effect tracks OOS sample size, not a specific protocol; a common-OOS-window ablation would isolate it (out of predeclared scope).
- The single-split reference reproduction (bit-identical to the frozen referee) makes the protocol deltas interpretable; a multi-fold-specific check (CI scales with pooled-OOS size) is now a standing audit requirement.
- EXP-010 supplies corrected robustness context for EXP-011: 5m/1h split-robust, 4h split-sensitive in the more-sensitive direction.

---

## EXP-011 - Predeclared-Loss Operating-Point Synthesis & Recommendation

**Status**: RECOMMENDATION DELIVERED (exploratory)
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (pooled by domain through upstream calibration artifacts)
**Data Views / Feature Categories**: Result-level artifacts from EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, and EXP-010; no market-data or chart-type views loaded

### Hypothesis Tests

1. **Hypothesis / exploratory question**: Given three loss functions predeclared in full, which L5 threshold multiplier on the frozen EXP-006 tau-frontier should Phase 002 recommend per domain, and is that recommendation robust across Loss A/B/C?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, pooled by domain for headline recommendation.
- **Data Views / Feature Categories**: Frozen result-level artifacts only; no raw market data, no chart-type views, no new draws, and no referee rerun.
- **Features**: EXP-006 tau-frontier MDE/FPR/TPR; EXP-003 draw-level effect estimates for sub-material reconstruction; EXP-007 tau=0 sub-material check; EXP-008 per-instrument overlay; EXP-009 real-effect location overlay; EXP-010 split overlay; EXP-005 non-blindness context.
- **Parameter ranges**: Domains `{5m, 1h, 4h}`; primary `alpha0=0.05`; tau frontier `{0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0}` times materiality; materiality buffers 0.5/1.5/3.0 bps; Loss A/B/C fixed as in `scope.md`.
- **Exclusions**: Adoption/freezing of a new referee, loss reweighting, new thresholds, per-instrument headline recommendations, walk-forward re-selection, chart-type signals, and incremental-information candidate design.
- **Constraints**: EXP-003/005/006/007/008/009/010 dependency tokens complete; final 30% global holdout never loaded; result tables inherit real-price `Close` outcome discipline from upstream calibration experiments; EXP-011 recommendation is a Phase 002 recommendation only.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, `submaterial_repro_check: true`, `inconclusive_domains: []`, and all dependency tokens `COMPLETE`.
- `decision_table.csv`: 21 rows = 3 domains x 7 tau multipliers; every row reportable with FPR Wilson upper `0.000959478516832434`.
- `sub_material_by_tau.csv`: 210 rows; audit confirmed the decision-table `sub_rate` values match the reconstructed operating-MDE rows.
- `recommendation.csv`:
  - 5m: headline tau `0.75`, MDE `0.5` bps, sub-material rate `0.39759036144578314`, Loss A/B `0.75`, Loss C `0.25`, `LOSS_SENSITIVE`, driver `sub_material`.
  - 1h: headline tau `0.25`, MDE `2.0` bps, sub-material rate `0.026223776223776224`, Loss A/B `0.25`, Loss C `0.0`, `ROBUST`.
  - 4h: headline tau `0.5`, MDE `8.0` bps, sub-material rate `0.0`, Loss A/B `0.5`, Loss C `0.0`, `LOSS_SENSITIVE`, driver `blind_band`.
- `adoption_rule.json` (re-run, data-derived caveats): EXP-005 detection `DETECTED_FLOOR` for all domains; EXP-009 `n_at_or_above_mde = 0` for every domain; per-instrument material overlays on EURUSD (1h) and EURUSD/XAUUSD (4h); walk-forward materiality false on 5m and 1h and true on 4h (corrected EXP-010). `run_metadata.method_notes` records the Loss C zero-FPR degeneracy and the Loss A MDE-before-sub-material trade; `scoped_overlays_complete = true`.
- Re-audit verdict PASS: independent loss recomputation matched all saved Loss A/B/C selections; deps hard-gated; sub-material tau=0 reproduction PASS.

### Hypothesis-Specific Conclusion

**RECOMMENDATION DELIVERED (exploratory)**

EXP-011 has no pass/fail hypothesis, but its scoped deliverable is complete. The primary predeclared loss recommends tau `0.75` (5m), `0.25` (1h), and `0.5` (4h); 1h is cross-loss robust, while 5m and 4h are loss-sensitive. No operating point is adopted in Phase 002.

### Hypothesis-Agnostic Observations

- The strict gate is already an honest detection floor on the EXP-005 scoped realistic candidate, so sub-strict tau recommendations are sensitivity-headroom choices, not corrections for demonstrated blindness.
- EXP-009 found no scoped untuned strategy effect at or above any domain MDE, so the recommendation affects calibration sensitivity more than a currently observed real candidate.
- Under the corrected EXP-010, only **4h** requires stricter Phase 003 ratification for split sensitivity (1h is now split-robust); the 4h shift is toward a lower MDE under more-OOS protocols.
- Loss C is a weak corroborator on the zero-FPR substrate (monotone toward the lenient endpoint), and Loss A can recommend a tau* with a non-trivial sub-material rate (5m) — read tau* with its sub_rate.
- Per-instrument overlays suggest pooled recommendations may mask lower achievable sensitivity in EURUSD/1h and EURUSD/XAUUSD 4h.

---

## EXP-012 - Fresh-Draw Loose Referee Ratification

**Status**: SUPPORTED
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; fresh synthetic known-null and known-positive draws; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: On each domain, the EXP-011-recommended loose operating point reproduces its Phase 002 operating characteristics on fresh synthetic draws: gate FPR <= alpha0 at D-prec precision, MDE within one edge-grid step of Phase 002, sub-material pass rate within tolerance and below the 0.50 ceiling, and for 4h, split-protocol agreement.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type views.
- **Features**: fresh known-null and known-positive draws, fixed EXP-011 tau point, loose and strict referee verdicts, FPR/TPR/MDE summaries, sub-material pass-rate reconstruction, 4h single-vs-anchored-walk-forward split gate.
- **Parameter ranges**: tau multipliers 5m `0.75`, 1h `0.25`, 4h `0.5`; alpha grid `{0.10, 0.05, 0.01}`; primary `alpha0=0.05`; 500 null draws per generator, 500 positive draws per edge; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: tau re-selection, threshold tuning, real candidate signals, chart-type candidates, bid/ask spread inference, and global holdout use.
- **Constraints**: EXP-001 PASS and EXP-003/EXP-010/EXP-011 COMPLETE required; first-70% slice only; real domain `Close` returns; fresh seed payloads disjoint from Phase 001/002 inputs.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `measurements_produced: true`, dependencies `{EXP-001: PASS, EXP-003: COMPLETE, EXP-010: COMPLETE, EXP-011: COMPLETE}`.
- Fresh seed check: `payload_overlap_count = 0`; 6 benign 32-bit integer collisions versus about 7.1 expected by chance.
- `adoption_decisions.csv`: all domains `ADOPT_LOOSE`.
- At `alpha0=0.05`, loose FPR = `0/4000` in 5m, 1h, and 4h; Wilson half-width `0.000479739`.
- Fresh loose MDEs exactly match Phase 002: 5m `0.5`, 1h `2.0`, 4h `8.0` bps.
- Sub-material rates: 5m `0.3991389913899139` vs Phase 002 `0.39759036144578314`; 1h `0.027469316189362946` vs `0.026223776223776224`; 4h `0.0` vs `0.0`.
- 4h split gate: single and anchored walk-forward loose MDE both `8.0` bps, FPR both `0.0`, `protocols_agree = true`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All three domains satisfy the frozen adoption rule. Phase 003 adopts the EXP-011 loose referee point for 5m/1h/4h rather than falling back to strict.

### Hypothesis-Agnostic Observations

- The fresh-draw ratification addresses synthetic seed-selection Goodhart risk, not fresh market-regime risk.
- 5m still carries a material sub-material pass rate (~0.40), but it stayed within the predeclared adoption rule and below the 0.50 ceiling.
- Later candidate screens can report strict plus adopted-loose outputs, but programme-level multiplicity remains outside this suite.

---

## EXP-013 - Incremental Substrate Validation

**Status**: SUPPORTED — re-validated 2026-06-04 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F01 across-draw redundancy verdict + `UNDER_POWERED` class; F04 contiguous-series block length). Remains PASS with three high-cost cells reclassified `UNDER_POWERED`. Numbers below reflect the rerun.
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; seeded R/C incremental known-truth substrate

### Hypothesis Tests

1. **Hypothesis**: The incremental substrate recovers a planted marginal edge within `max(0.5 bps, 15% of m)` and reads no phantom positive incremental edge for the redundancy null where R and C share structure but C adds no marginal edge.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice.
- **Features**: seeded blockwise latent state, R-only/C-change/overlap/inactive masks, model-free marginal net P&L, positive planted marginal edge, redundancy null, bootstrap intervals, denominator and cost accounting.
- **Parameter ranges**: episode lengths 5m `24`, 1h `8`, 4h `4`; 100 positive draws per edge; 100 redundancy draws; inherited edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: incremental MDE calibration, golden fixtures, real candidate signals, chart-type candidates, linear residualization as qualifying evidence, and global holdout use.
- **Constraints**: EXP-001 PASS and Track B predeclaration token required; first-70% slice only; real domain `Close` returns; denominator is rows where C changes the combined book relative to R-alone.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `measurements_produced: true`, `recovery_fail: false`, `phantom_edge: false`, `powered_null_cells: 9`, `insufficient_return_cells: 0`, `redundancy_verdict_basis: across_draw_distribution`.
- `positive_recovery.csv`: 108/108 cells PASS. Maximum absolute recovery error `0.39608151988927` bps, below tolerance.
- `redundancy_null.csv`: 8 `PASS`, 3 `UNDER_POWERED` (BTCUSD/1h, BTCUSD/4h, USTEC/4h), 1 `NULL_COST_DOMINATED` (XAUUSD/4h); 0 `PHANTOM_EDGE`.
- Verdict basis is the across-draw distribution (F01): the most positive across-draw mean across all 12 cells is `-0.041182` bps, so no cell has even a positive point estimate; the 3 `UNDER_POWERED` cells have across-draw CI half-width ≥ materiality.
- `substrate_integrity.csv`: C-change denominator fraction range `0.24983388704318937` to `0.2504520795660036`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The Track B incremental substrate is validated. It recovers planted marginal edge and does not manufacture positive incremental evidence from shared R-C structure.

### Hypothesis-Agnostic Observations

- The redundancy-null cells read negative (cost drag) under the confirmed incremental cost model, not as phantom positives; one cell (XAUUSD/4h) is adequately-powered cost-dominated, and three (BTCUSD/1h, BTCUSD/4h, USTEC/4h) are under-powered (CI too wide to bound a phantom) and disclosed rather than passed.
- The substrate gate passes, but later calibration still needs to prove finite MDE under dependence stress.

---

## EXP-014 - Incremental Referee Golden-Fixture Correctness

**Status**: SUPPORTED — re-validated 2026-06-04 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F04 contiguous-series block length): 7/7 verdicts and 35/35 leg states reproduced unchanged; `effective_n` now episode-aware (`276.9` on `all_pass`); EXP-013 dependency re-confirmed PASS.
**Date**: 2026-06-04
**Instruments**: Fixture labels only; no market data read
**Data Views / Feature Categories**: Deterministic in-memory return-space and R/C position fixtures

### Hypothesis Tests

1. **Hypothesis**: The incremental referee reproduces predeclared hand-computed verdicts on deterministic golden fixtures, exposes all gate legs without short-circuiting, and correctly generalizes L3 from naive control to reference control.

### Scope

- **Instruments**: Fixture labels only.
- **Data Views / Feature Categories**: deterministic fixture arrays; no Parquet market-data load.
- **Features**: seven fixture verdicts, L1-L5 expected states, no-short-circuit leg exposure, L3 reference-control isolation.
- **Parameter ranges**: primary `alpha0=0.05`; 1000 bootstrap resamples; fixtures `all_pass_incremental`, L1-L5 fail fixtures, and `redundant_shared_structure`.
- **Exclusions**: MDE calibration, dependence-grid measurement, real candidate signals, chart-type candidates, and global holdout use.
- **Constraints**: EXP-013 PASS and Track B predeclaration token required.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `verdicts_reproduced: true`, `leg_states_reproduced: true`, `all_legs_exposed_no_short_circuit: true`.
- `fixture_results.csv`: 7/7 fixture verdicts match expected.
- `leg_exposure_matrix.csv`: 35/35 L1-L5 checks PASS; all legs exposed for every fixture.
- `l3_reference_control_fail` rejects despite standalone-looking edge, isolating the incremental-beyond-R requirement.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The incremental referee logic is correct under the confirmed leg mapping and may be used for EXP-015 calibration.

### Hypothesis-Agnostic Observations

- This experiment validates logic wiring only; it does not measure operating characteristics.
- The fixture suite should remain a regression target if the incremental unit is revised.

---

## EXP-015 - Incremental Referee Portfolio-Fitness Calibration

**Status**: REFUTED — re-validated 2026-06-05 under amendment [A1](checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F03 per-leg + per-instrument diagnostics; F04 no-op for the per-row grid). Outcome stands REFUTED; the failure is now attributed to the L2 standalone-significance leg driven by BTCUSD. Numbers below reflect the rerun.
**Date**: 2026-06-04
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; incremental R/C dependence-grid known-truth draws

### Hypothesis Tests

1. **Hypothesis**: The incremental referee has a finite portfolio-fitness MDE at FPR <= `alpha0` on each domain, and redundancy-null FPR remains controlled under the checkpoint's R-C dependence grid.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice.
- **Features**: redundancy-null FPR, positive TPR/MDE, rho/overlap/lag/reference-strength dependence grid, construction diagnostics, denominator summaries, worst-case domain MDE rule.
- **Parameter ranges**: rho labels `{independent, moderate, high}`; overlap `{low, medium, high}`; lag `{synchronous, c_lags_r_1, c_leads_r_1}`; reference strength `{null_R, R_at_strict_mde}`; alpha grid `{0.10, 0.05, 0.01}`; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps.
- **Exclusions**: real candidate signals, chart-type candidates, re-tuning estimator or leg mapping, standalone referee ratification, suite integration, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-014 PASS, and EXP-003 strict MDE map required; first-70% slice only; real domain `Close` returns; construction-invalid cells reported explicitly.

### Results / Observations

- `run_metadata.json`: `overall_status: REFUTED`, dependencies `{EXP-013: PASS, EXP-014: PASS, EXP-003: FOUND}`.
- `domain_mde_summary.csv`:
  - 5m: finite MDE cells `41`, failing cells `1`, construction-invalid/underpowered cells `12`, status `REFUTED`.
  - 1h: finite MDE cells `40`, failing cells `2`, construction-invalid/underpowered cells `12`, status `REFUTED`.
  - 4h: finite MDE cells `40`, failing cells `2`, construction-invalid/underpowered cells `12`, status `REFUTED`.
- Failing cells are all synchronous high-overlap `null_R` contexts: high rho/high overlap on 5m; moderate and high rho/high overlap on 1h and 4h.
- Accepted-cell FPR is controlled: max FPR `0.0` on 5m and `0.01` on 1h/4h; no cell exceeds `alpha0 = 0.05`.
- `construction_diagnostics.csv`: 12 construction-invalid cells per domain, all high-rho low/medium-overlap combinations marked `target_rho_infeasible_for_overlap`.
- F03 attribution (`leg_pass_rates.csv`, `tpr_by_instrument.csv`): in every failing cell the verdict pass rate equals the L2 standalone-significance pass rate (5m/high `0.75`, 1h/mod `0.784`, 1h/high `0.716`, 4h/mod `0.63`, 4h/high `0.382`) with L1/L4/L5 at `1.0` and L3 ≥ `0.97`; BTCUSD's standalone TPR is `0.0`–`0.136` at the 32 bps ceiling versus the other instruments at/near `1.0`, holding the pooled rate below the `0.80` power floor.
- Worst finite PASS-cell MDEs are 5m `32.0`, 1h `24.0`, 4h `32.0` bps, but these are not adoptable because failing cells exist.
- Audit verdict PASS: results are valid for interpretation; no critical or warning issues.

### Hypothesis-Specific Conclusion

**REFUTED**

The incremental referee controls FPR in accepted cells but fails the finite-MDE requirement in every domain. The Track B portfolio-fitness unit is not validated and cannot be frozen for Phase 004 use.

### Hypothesis-Agnostic Observations

- The refutation is sensitivity-driven, not false-positive-driven, and is localized to the L2 leg / BTCUSD by the F03 diagnostics — not a substrate or logic defect.
- EXP-013 and EXP-014 still stand: the substrate and logic are valid, but this calibrated operating point fails under dependence stress.
- Phase 003 cannot reach FULL_FRAMEWORK_CONCLUDED without a new incremental-unit follow-up or an explicit standalone-only rescope.

---

## EXP-016 - Assembled Suite Composition Anchor

**Status**: BLOCKED
**Date**: 2026-06-04
**Instruments**: Not measured
**Data Views / Feature Categories**: Blocker manifest only; no suite-composition measurement produced

### Hypothesis Tests

1. **Exploratory question**: Does the assembled strict, ratified-loose, and incremental suite wire both reject and pass paths end to end on the EXP-009 dogfood negative path and a synthetic positive suite-level fixture?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for the planned dogfood path; not measured in the blocked run.
- **Data Views / Feature Categories**: planned 5m/1h/4h dogfood domains and synthetic positive fixture; blocked run emits only dependency and blocker manifests.
- **Features**: suite dependency manifest, dogfood reference-book precondition, positive fixture precondition, blocker report.
- **Parameter ranges**: not measured.
- **Exclusions**: inventing the dogfood reference book, changing EXP-012 adoption decisions, changing EXP-015 calibration, real signal exploration, chart-type candidates, and global holdout use.
- **Constraints**: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-015 COMPLETE, and `inputs/dogfood_reference_book.csv` required before measurement.

### Results / Observations

- `run_metadata.json`: `overall_status: BLOCKED`, `measurements_produced: false`.
- `dependency_manifest.csv`: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-015 metadata `REFUTED`, upstream result files found, dogfood reference book MISSING.
- `blocker_report.csv`: two blockers:
  - EXP-015 `overall_status='REFUTED'`, required `COMPLETE`.
  - missing `python/experiments/EXP-016/inputs/dogfood_reference_book.csv`.
- No suite manifest, expected-output matrix, positive fixture, standalone verdicts, incremental verdicts, or composition summary was produced.
- Audit verdict PASS for blocked-state handling.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE / BLOCKED**

The composition question is unanswered. EXP-016 correctly stopped before measurement because the suite was not assembleable under the approved scope.

### Hypothesis-Agnostic Observations

- The blocked result confirms governance discipline: the script does not invent an undefined dogfood reference book and does not proceed after EXP-015 refutes the incremental unit.
- Phase 003 cannot be reported as full-framework concluded from the current EXP-016 artifact set.

---

## EXP-017 - Revised Incremental Referee Golden-Fixture Correctness

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: Fixture labels only; no market data read
**Data Views / Feature Categories**: Seeded-deterministic in-memory return-space and R/C position fixtures

### Hypothesis Tests

1. **Hypothesis**: The revised incremental referee, with L2 removed and retained legs L1, L3, L4', and strict L5, reproduces predeclared fixture verdicts, exposes every retained leg without short-circuiting, omits L2 from gate output, and verifies the former standalone-L2 failure fixture now passes under the revised formula.

### Scope

- **Instruments**: Fixture labels only; not a market-behavior experiment.
- **Data Views / Feature Categories**: Deterministic return-space and R/C position fixtures; no market Parquet load.
- **Features**: seven fixture verdicts, retained-leg states for L1/L3/L4'/L5, L2-absence checks, legacy-L2 diagnostic, mismatch report.
- **Parameter ranges**: `alpha = 0.05`, 1000 bootstrap resamples, revised gate `L1 and L3 and L4_prime and strict_L5; L2 absent`.
- **Exclusions**: Operating-characteristic calibration, MDE measurement, real candidate signals, chart-type candidates, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-014 PASS, and active Phase 003b design confirmations required; fixtures are seeded-deterministic rather than closed-form analytic.

### Results / Observations

- `run_metadata.json`: `overall_status: PASS`, `verdicts_reproduced: true`, `retained_leg_states_reproduced: true`, `all_retained_legs_exposed_no_short_circuit: true`, `l2_absent_from_revised_gate_output: true`.
- `fixture_results.csv`: 7/7 fixture verdicts PASS; `mismatch_details.csv` is empty.
- `leg_exposure_matrix.csv`: 28/28 retained-leg checks PASS, all retained legs exposed.
- `l2_absence_check.csv`: 7/7 PASS; emitted revised-gate legs contain L1, L3, L4', L5, and supporting numeric fields only.
- `l2_absent_former_standalone_fail`: legacy L2 diagnostic fails (`legacy_l2_pass_diagnostic = false`, `legacy_l2_ci_lower_bps = -3.3855586505512987`) while revised verdict PASS.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

EXP-017 validates the revised incremental-referee logic gate. It confirms L2 removal, retained-leg exposure, and expected fixture behavior, so EXP-018 may use EXP-017 as a PASS dependency.

### Hypothesis-Agnostic Observations

- This is a logic correctness gate only; it does not measure false-positive risk, power, or MDE.
- The fixture suite should remain the regression test for any future change to `revised_incremental_gate_row()`.

---

## EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; seeded R/C dependence-grid known-truth draws

### Hypothesis Tests

1. **Hypothesis**: The revised incremental referee has a finite portfolio-fitness MDE at FPR <= `alpha0` on each domain across the construction-accepted unchanged P3-D-dependence grid, and redundancy-null FPR remains controlled at the synchronous/high-overlap/null_R corner where EXP-015 failed.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice; no chart-type candidates.
- **Features**: redundancy-null FPR, positive-edge TPR/MDE, retained-leg pass rates, per-instrument TPR, denominator summaries, construction diagnostics, explicit binding-corner summary.
- **Parameter ranges**: rho `{independent, moderate, high}`; overlap `{low, medium, high}`; lag `{synchronous, c_lags_r_1, c_leads_r_1}`; reference strength `{null_R, R_at_strict_mde}`; alpha grid `{0.10, 0.05, 0.01}`; edge grid `{0.5,1,2,4,8,12,16,24,32}` bps; 125 draws per instrument/cell.
- **Exclusions**: Real candidate signals, chart-type candidates, retuning the revised gate, changing strict or ratified-loose referees, suite integration, and global holdout use.
- **Constraints**: EXP-013 PASS, EXP-017 PASS, and EXP-003 strict MDE map required; headline domain MDE is worst-case finite accepted-cell MDE.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`; domain statuses all `SUPPORTED_WITH_UNDERPOWERED_CELLS`; domain MDEs 5m `12.0`, 1h `16.0`, 4h `32.0` bps.
- `construction_diagnostics.csv`: 810,000 construction rows; 630,000 accepted and 180,000 invalid. Invalid reason is `target_rho_infeasible_for_overlap`.
- `fpr_summary.csv`: 126 accepted cells PASS, 36 construction-invalid cells; accepted-cell FPR range `0.0` to `0.004`, max FPR Wilson half-width `0.006684203250090802`.
- `cell_mde_summary.csv`: 126 PASS cells, 36 CONSTRUCTION_INVALID cells; 0 FPR or no-finite-MDE failures.
- `domain_mde_summary.csv`: each domain has 42 finite MDE cells, 0 failing cells, 12 construction-invalid/underpowered cells, total 54 cells.
- `binding_corner_summary.csv`: all nine synchronous/high-overlap/null_R corner rows PASS. Moderate/high-rho stress MDEs are 5m `1.0`, 1h `8.0`, and 4h `24.0` bps.
- Audit recomputation: FPR and TPR counts from `draw_verdicts.csv` match summary files with 0 mismatches; domain MDE recomputation matches `domain_mde_summary.csv`.
- Audit verdict PASS: no critical or warning issues.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The revised incremental / portfolio-fitness unit validates on every construction-accepted dependence-grid cell. FPR is controlled, finite MDEs exist in all domains, and the explicit EXP-015 stress corner now passes.

### Hypothesis-Agnostic Observations

- The validated revised-unit MDE map is materially conservative: 12/16/32 bps on 5m/1h/4h.
- The 36 disclosed non-PASS cells are construction-infeasible high-rho/low-overlap contexts, not failed inference cells.
- The EXP-015 refutation was repaired by removing standalone L2; the revised unit now tests portfolio fitness, not standalone C significance.

---

## EXP-019 - Assembled Suite Composition Anchor

**Status**: SUPPORTED
**Date**: 2026-06-05
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for dogfood path; EURUSD fixture label for synthetic positive path
**Data Views / Feature Categories**: 5m, 1h, and 4h OHLC domains for dogfood path; deterministic synthetic positive fixture for pass path

### Hypothesis Tests

1. **Exploratory integration claim**: Conditional on EXP-018 validation and the confirmed dogfood reference book, the assembled suite of frozen strict referee, EXP-012 ratified-loose referee, and EXP-018 revised incremental unit composes end to end on both the EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD for real dogfood path; EURUSD fixture label for synthetic positive path.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice for dogfood; in-memory synthetic arrays for positive fixture.
- **Features**: strict and loose/fallback standalone verdicts, revised incremental verdicts, dogfood reference-book manifest, suite manifest, expected-output matrix, positive fixture manifest, composition summary.
- **Parameter ranges**: strict MDEs 1/4/12 bps; EXP-012 effective loose MDEs 0.5/2/8 bps; EXP-018 revised incremental MDEs 12/16/32 bps on 5m/1h/4h; dogfood reference book `donchian_20`; candidates `ma_20_50`, `rsi_14`, `bollinger_20_2`, `macd_12_26_9`, `roc_20`.
- **Exclusions**: New real signal exploration, chart-type candidates, suite retuning, changing upstream adoption decisions, programme-level multiplicity control, and global holdout use.
- **Constraints**: EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-018 COMPLETE with finite domain MDEs, and predeclared dogfood reference book required before measurement.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`; all six domain/path statuses expected.
- `dependency_manifest.csv`: EXP-009, EXP-012, and EXP-018 metadata COMPLETE; strict MDE map, dogfood artifacts, adoption decisions, EXP-018 domain MDE summary, dogfood reference book, and dogfood reference manifest FOUND.
- `suite_manifest.csv`: strict MDEs 1/4/12 bps, ratified-loose effective MDEs 0.5/2/8 bps, revised incremental MDEs 12/16/32 bps on 5m/1h/4h.
- `suite_composition_summary.csv`: dogfood negative path has 0 strict passes, 0 loose/fallback passes, 0 incremental passes in every domain; status `REJECT_PATH_EXERCISED` for 5m/1h/4h.
- `suite_composition_summary.csv`: synthetic positive path has 1 strict pass, 1 loose/fallback pass, 1 incremental pass in every domain; status `PASS_PATH_EXERCISED` for 5m/1h/4h.
- `positive_fixture_manifest.csv`: 3/3 rows `nonredundancy_ok = true`, active overlap fraction `0.0`, signed R-C rho near zero.
- Audit verdict PASS: no critical or warning issues. Audit notes a stale earlier `blocker_report.csv`, superseded by current completed metadata and manifests.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The assembled suite composes end to end. The dogfood negative path rejects across all domains, and the synthetic positive path passes strict, ratified-loose, and revised incremental components across all domains.

### Hypothesis-Agnostic Observations

- EXP-019 is an integration anchor, not Phase 004 signal exploration.
- The concluded suite can now be recorded as `{frozen strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental / fitness unit}`.
- Phase 004 remains gated on documenting the programme-level multiplicity registry before real candidate screening begins.

---

## VAL-001 - Data Architecture Temporal Integrity Validation

**Status**: SUPPORTED (rev. 3)
**Date**: 2026-06-01
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break level 3; Renko ATR period 14; Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: The available Xen data architecture preserves temporal alignment across scoped time-bar, timeframe, and chart-type views — with no future-timestamp or cross-view misalignment in any emitted row, and no structural look-ahead in prefix-stability probes positioned at the head, middle, and tail of the analysis slice — when every derived view is generated only from the first 70% of each chronologically ordered base dataset.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: Base 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break, Renko, and Heiken Ashi generated from each scoped source timeframe.
- **Features**: Required time-bar schema, OHLC integrity, `CloseTime`, `SourceCloseTime`, `SourceCount`, Heiken Ashi real OHLC preservation, prefix stability, deterministic regeneration, and negative-control detection.
- **Parameter ranges**: Line Break `level=3`; Renko `atr_period=14`; timeframe periods `1`, `15`, and `60` minutes.
- **Exclusions**: Final 30% global holdout, tick data, bid/ask spread, trading costs, strategy backtests, return forecasting, parameter tuning, randomized tests, and persisted generated chart-type datasets.
- **Constraints**: All validation uses the first 70% chronological analysis slice only. Time bars align by `CloseTime`; Line Break and Renko align by `SourceCloseTime`; Heiken Ashi aligns by `CloseTime`. No P&L or return metrics are in scope.

### Results / Observations

- `validation_checks.csv`: 416 PASS, 0 FAIL, 0 INCONCLUSIVE (rev. 3).
- Real-instrument checks: BTCUSD 98/98 PASS; EURUSD 98/98 PASS; USTEC 98/98 PASS; XAUUSD 98/98 PASS.
- Synthetic control checks: 24/24 PASS, including 23/23 detected negative controls (one per data-integrity and alignment check) plus 1 golden fixture.
- Prefix-stability look-ahead probes: 60 checks (head/middle/tail for 1-minute views, `full` for 15m/60m), 0 diverged cuts; determinism: 36/36 PASS.
- Analysis rows after first-70% slicing (unchanged from rev. 2): BTCUSD 1,088,960; EURUSD 872,242; USTEC 830,541; XAUUSD 830,671.
- Resample oracle comparisons: 0 rows only in production, 0 rows only in oracle, and 0 OHLC mismatches for every 15-minute and 60-minute instrument comparison.
- Heiken Ashi density: 1.0 for every instrument/timeframe combination.
- Line Break event-density range: 0.195149 to 0.275556 event rows per source row.
- Renko event-density range: 0.222171 to 0.298266 event rows per source row.
- Renko duplicate-source denominator context: 107,824 duplicate `SourceCloseTime` groups and 128,556 extra same-source rows across all scoped outputs.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The current data layer passed the temporal-integrity readiness gate. The conclusion is supported because every scoped positive check passed and every injected negative control was detected, satisfying the predefined success criteria.

### Hypothesis-Agnostic Observations

- Renko same-source duplicate rows are common enough to require explicit denominator reporting in future chart-type experiments.
- Future downstream strategy or signal experiments can rely on timestamp alignment as validated here, but they must still evaluate returns and P&L on real time-matched prices.
- Changes to data-loading conventions, chart generators, or `aggregate_ohlc()` should trigger a new VAL rerun before dependent research uses the changed layer.
- rev. 3 hardened the suite's detection power: every base-integrity, resample, sparse-chart, Heiken Ashi, schema, look-ahead, and determinism check now has a matching negative control, and look-ahead is probed at the head/middle/tail of each slice. Byte-identical reproduction of rev. 2 generator outputs confirms deterministic generation; future VAL reruns should keep this control-per-check standard.
- The Line Break and Renko generators were manually verified against `architecture.md`; note Xen Renko intentionally differs from classic TradingView Renko (SMA-of-TR ATR, 1-brick symmetric reversal, first-close anchor).

---

## EXP-020 — AVWAP Event-Substrate Readiness

**Status**: SUPPORTED_FULL
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains; registered CF-AVWAP-001 first-branch AVWAP state machine; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The Phase 004 Batch 004-A AVWAP definition can be implemented as a deterministic, look-ahead-safe event substrate with usable bounce-event coverage on at least one predeclared domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from the first-70% analysis slice. No chart-type views.
- **Features**: Sequential state machine: MA(20,50) regime detector, viable-pivot anchor selection, anchored VWAP (typical price weighted by TickVolume^0.75), MAD band (multiplier 1.0), arm/trigger bounce logic, invariant checks, deterministic replay, event-coverage readiness classification.
- **Parameter ranges**: fast MA 20, slow MA 50; TickVolume exponent 0.75; band multiplier 1.0; domains 5m/1h/4h; readiness thresholds: ≥30 total events, ≥8 per direction, ≥3 reportable instruments per domain.
- **Exclusions**: Market-edge claims, frozen-suite screening, cTrader strategy-host runs, alternative regime detectors, volume/band sweeps, exits/stops/targets, chart-type signals, parameter changes after results.
- **Constraints**: First-70% slice only; CloseTime ordering; sequential look-ahead-safe state machine; no returns, P&L, or excursion computation; zero-weight TickVolume skipped without division-by-zero; zero denominators reported as null.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED_FULL`, `ready_domain_count: 3`, `ready_domains: [5m, 1h, 4h]`, `invariants_ok: true`, `determinism_pass: true`, `holdout_violation_count: 0`, `total_events: 20911`.
- `domain_readiness.csv`: all three domains ready (4/4 reportable instruments each).
- `event_coverage.csv`: all 12 cells reportable. 5m: 4,327–5,978 events per instrument (density ~260–276 per 10k bars). 1h: 287–421 events (density ~207–242). 4h: 61–109 events (density ~199–246).
- `direction_balance.csv`: bull fractions 0.46–0.56 across all 12 cells; widest gap EURUSD/4h (39 bull, 31 bear).
- `invariant_checks.csv`: 192/192 checks PASS with 0 violations (16 checks × 12 cells).
- `determinism_check.csv`: 12/12 cells match event hashes and regime hashes between main and replay pass.
- `analysis_metadata.csv`: each instrument at exactly 70.00% analysis rows (BTCUSD 1,088,960/1,555,658; EURUSD 872,242/1,246,061; USTEC 830,541/1,186,488; XAUUSD 830,671/1,186,674).
- Audit: PASS, 0 critical, 0 warnings, 1 info note (EURUSD/4h moderate direction imbalance — both directions still reportable).

### Hypothesis-Specific Conclusion

**SUPPORTED_FULL**

All Evidence-FOR criteria are met: all invariant checks pass for every instrument/domain (0 violations across 192 checks), deterministic replay produces identical event tables and summary hashes (12/12 cells match), and all three domains are ready (4/4 reportable instruments). EXP-021 and EXP-022 may scope reaction and lifetime-move studies on any subset of the ready domains.

### Hypothesis-Agnostic Observations

- Event density is consistent across instruments and domains, with 5m providing the highest absolute counts.
- Direction balance is reasonable across all 12 cells; no domain or instrument shows degenerate single-direction coverage.
- The AVWAP state machine's re-arm sequencing is validated by the `rearm_monotonic` invariant (0 violations), confirming that the scope's arm/trigger/re-arm discipline is correctly implemented.
- The moderate EURUSD/4h direction gap (0.557 bull fraction) is a descriptive note for EXP-021 scoping, not a correctness issue.

---

## EXP-021 — AVWAP Bounce Reaction Study

**Status**: SUPPORTED
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 AVWAP bounce event substrate (CF-AVWAP-001 first branch)

### Hypothesis Tests

1. **Hypothesis**: AVWAP bounce events from the supported CF-AVWAP-001 first branch show better fixed-horizon direction-signed real-price reaction than matched non-event controls on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 events and regime summary. No chart-type views.
- **Features**: Same-regime matched controls (up to 5, min 3, by nearest anchor age/timestamp, 6-bar exclusion window around triggers), direction-signed log returns at 1/3/6 completed bars, instrument-averaged equal-weight domain effect estimator, regime-cluster bootstrap CI (10k resamples), stratified paired sign-permutation p-value (10k flips), Holm adjustment across 3 domains.
- **Parameter ranges**: primary horizon 3; secondary 1 and 6; MAX_CONTROLS=5; MIN_CONTROLS=3; EXCLUSION_BARS=6; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; alpha=0.05; N_BOOT=10,000; N_PERM=10,000.
- **Exclusions**: cTrader strategy-host screening or frozen-suite candidate qualification (EXP-023); lifetime target/trend-change outcomes (EXP-022); full strategy backtests, exits, stops, pyramiding, risk management, or position sizing; alternative AVWAP branches; parameter tuning or horizon selection after reading outcomes; percentage improvement against a zero baseline.
- **Constraints**: EXP-020 must be SUPPORTED_FULL with ready domains {5m, 1h, 4h}, 0 invariant violations, and deterministic replay match; first-70% slice only; CloseTime ordering; real domain Close outcomes; same-regime matching makes regime_id exact dependence clusters.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED`, dependency gate PASSED (EXP-020 SUPPORTED_FULL).
- `domain_reaction_tests.csv`:
  - 5m: effect +3.8 bps, CI [+3.5, +4.1], n=16,249, Holm p=0.0003, EVIDENCE_FOR.
  - 1h: effect +9.1 bps, CI [+5.1, +13.3], n=1,207, Holm p=0.0003, EVIDENCE_FOR.
  - 4h: effect +37.6 bps, CI [+22.3, +52.7], n=246, Holm p=0.0003, EVIDENCE_FOR.
- All three domains EVIDENCE_FOR. No secondary horizon is negative in any domain (all 1-bar and 6-bar effects positive).
- All 24 instrument×direction cells have positive mean paired differences at the primary horizon.
- `control_match_diagnostics.csv`: all 4 instruments reaction-reportable in all 3 domains. Mean controls per reportable event 4.5–5.0. Non-reportable events primarily `insufficient_same_regime_controls`.
- Audit verdict PASS: 0 critical, 0 warnings, 1 info note (4h effect partly driven by extreme BTCUSD control means).
- Cash in the analysis set only; holdout never loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All four Evidence-FOR criteria are met: (1) EXP-020 dependency gate passes; (2) all three domains are reaction-reportable with ≥4 reportable instruments each; (3) all three domains have primary effect > 0 bps, 95% CI lower bound > 0 bps, and Holm-adjusted p ≤ 0.05; (4) no domain has both secondary horizons negative. The fixed-horizon bounce reaction operationalization of CF-AVWAP-001/HYP-002 is supported.

### Hypothesis-Agnostic Observations

- The effect scales with domain (5m < 1h < 4h), consistent with larger per-bar moves at longer horizons.
- BTCUSD contributes the largest per-instrument effects, especially at 4h where same-regime controls have extreme negative means (−75 to −94 bps over 3 bars), inflating the paired contrast. The equal-weight domain estimator mitigates single-instrument dominance.
- The same-regime control restriction is binding (costing 8–14 events per 4h direction cell) but all domains still reach full reportability.
- Secondary horizons (1-bar, 6-bar) are positive and monotonic, ruling out a one-bar fluke or reversal artifact.

## EXP-022 — AVWAP Original Lifetime Move Study

**Status**: SUPPORTED
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 AVWAP event substrate (CF-AVWAP-001 first branch); band-target/trend-change lifetime method

### Hypothesis Tests

1. **Hypothesis**: Under the registered band-target/trend-change lifetime definition, AVWAP bounce events from the supported CF-AVWAP-001 first branch produce more favorable completed-move outcomes than matched non-event lifetime analogs on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 events and regime summary with frozen favorable/adverse targets at trigger. No chart-type views.
- **Features**: Same-regime matched controls (up to 5, min 3, by nearest anchor age/timestamp, 6-bar exclusion window around triggers), frozen event target distance transfer to control close (log bps), lifetime completion scan (favorable target, adverse target, trend-change, unfinished), instrument-averaged equal-weight domain rate-difference estimator (pp), regime-cluster bootstrap CI (10k resamples), stratified paired permutation p-value (10k flips), Holm adjustment across 3 domains, volatility-context ratio diagnostic (20-bar MAD of typical-price log returns).
- **Parameter ranges**: MAX_CONTROLS=5; MIN_CONTROLS=3; EXCLUSION_BARS=6; MIN_TARGET_COMPLETED=30; DOMAIN_MIN_INSTRUMENTS=3; LOCALVOL_WINDOW=20; VOL_CONTEXT_BOUNDS=[0.5, 2.0]; alpha=0.05; N_BOOT=10,000; N_PERM=10,000.
- **Exclusions**: Fixed-horizon reaction testing (EXP-021); cTrader strategy-host screening or frozen-suite candidate qualification (EXP-023); full strategy backtests, optimized exits, stops, pyramiding, risk management, or position sizing; alternative AVWAP branches; parameter tuning after reading lifetime outcomes; percentage improvement against a zero baseline.
- **Constraints**: EXP-020 must be SUPPORTED_FULL with ready domains {5m, 1h, 4h}, 0 invariant violations, and deterministic replay match; first-70% slice only; CloseTime ordering; real domain Close outcomes; trend-change is nearest later opposite MA(20,50) regime confirmation; same-regime matching makes regime_id exact dependence clusters; targets frozen at trigger time.

### Results / Observations

- `run_metadata.json`: `overall_status: SUPPORTED`, dependency gate PASSED (EXP-020 SUPPORTED_FULL), all 4/4 instruments reportable in all 3 domains.
- `domain_lifetime_tests.csv`:
  - 5m: rate diff +23.9 pp, 95% CI [22.7, 25.1], expectancy diff +6.5 bps, median vol ratio 0.986, Holm p=0.0003, EVIDENCE_FOR.
  - 1h: rate diff +21.9 pp, 95% CI [17.2, 26.6], expectancy diff +27.0 bps, median vol ratio 1.024, Holm p=0.0003, EVIDENCE_FOR.
  - 4h: rate diff +26.4 pp, 95% CI [17.7, 35.3], expectancy diff +79.6 bps, median vol ratio 0.987, Holm p=0.0003, EVIDENCE_FOR.
- All three domains EVIDENCE_FOR. All domains have positive expectancy point estimates.
- Event favorable rates: 67–69% across domains. Control favorable rates: 42–45%.
- All median volatility-context ratios within [0.5, 2.0]; unfinished event fraction 0.0 for all domains.
- `lifetime_observations.csv`: 85,816 rows (events + controls across all cells).
- `control_lifetime_diagnostics.csv`: 24 instrument×direction rows. Insufficient same-regime controls: range 2–373 (5m dominates, as expected).
- Integrity counters: 4,604 invalid_target_events (geometrically impossible targets, excluded correctly), 0 tie_completions, 0 events_no_future_bars.
- Audit verdict PASS: 0 critical, 0 warnings, 2 info notes.
- Cash in the analysis set only; holdout never loaded.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All predeclared Evidence-FOR criteria are met: (1) EXP-020 dependency gate passes; (2) all three domains are lifetime-reportable with ≥3 of 4 reportable instruments each; (3) all three domains have rate diff > 0 pp, 95% CI lower bound > 0 pp, and Holm-adjusted p ≤ 0.05; (4) all domains have positive expectancy point estimates; (5) no domain is volatility-context-confounded or censored. The original band-target/trend-change lifetime operationalization of CF-AVWAP-001/HYP-003 is supported on all three domains.

### Hypothesis-Agnostic Observations

- The favorable rate advantage is large (22–26 pp) and nearly identical across domains, suggesting the lifetime method captures a genuine event property rather than a domain-specific artifact.
- Expectancy scales with domain width (6.5 → 27.0 → 79.6 bps for 5m/1h/4h), reflecting larger per-move returns on wider targets.
- The volatility-context diagnostic (all medians within 0.986–1.024) confirms that matched controls face comparable target difficulty, ruling out a volatility-mismatch confound.
- The ~4,600 excluded invalid-target events carry useful information: they represent cases where the AVWAP target at trigger time is already beyond the adverse direction, which happens when the A/VWAP band is very narrow or price is very close to the band — this is structural to the first branch's MAD-band construction.

---

## EXP-023 — AVWAP Baseline Candidate Screen

> **SUPERSEDED (framing-corrected) 2026-06-08.** The REFUTED verdict below is valid
> **only as a per-bar continuous-position screen**, not as a tradability test of the
> original selective event vehicle: a ~6%-active signal was scored against a per-bar
> MDE floor calibrated for ≥80%-active series (EXP-005), so the result is dominated
> by ~16× denominator dilution, not absence of signal. Record retained; conclusion
> corrected. Re-screened faithfully under an event-level method in **EXP-028**
> (Phase 006). Review:
> `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.

**Status**: REFUTED → SUPERSEDED (framing-corrected)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: cTrader `Mode=StrategyHost` AVWAP-baseline runs (CF-AVWAP-001/HYP-004 first branch) and aligned Donchian(20) reference on 5m/1h/4h domains, evaluated on emitted real OHLC (`RealClose`); first-70% analysis slice only; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The registered CF-AVWAP-001 baseline signal can qualify under at least one component of the frozen Phase 004 suite — standalone strict, standalone ratified-loose/fallback, or revised portfolio-fitness against the existing D-dogfood-book Donchian(20) reference — while reporting the original AVWAP strategy metric book, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4 × 3 domains = 12 cells).
- **Data Views / Feature Categories**: cTrader strategy-host AVWAP-baseline and Donchian(20) outputs (positions/events/trade blotter/metadata); fixed first-70% source-Parquet smoke output only to validate the C# AVWAP port against the `xen.avwap` Python reference. No chart-type views.
- **Features**: standalone strict gate stack and EXP-012 ratified-loose/strict-fallback referee at α₀=0.05; EXP-018 revised portfolio-fitness unit (`clip(R+C,−1,+1)−R` marginal estimator) vs Donchian(20); original metric book on real `RealClose` (bounce prevalence, executed-entry/non-executed-pyramid counts, favorable/adverse/trend-change/unfinished completions, expectancy, robust mean/MAD and mean/std risk levels, raw-return comparison); same-feed reference identity, holdout-fence, and C#/Python transcription checks.
- **Parameter ranges**: regime MA(20,50) on domain `RealClose`; AVWAP source `(RealHigh+RealLow+RealClose)/3`; weight `TickVolume**0.75`; MAD band ×1.0; frozen suite settings loaded from artifacts — strict MDE 1/4/12, ratified-loose τ 0.375/0.375/1.5 with MDE 0.5/2/8, revised-incremental MDE 12/16/32 bps (5m/1h/4h); α₀=0.05; n_bootstrap=1000.
- **Exclusions**: alternative AVWAP branches/detectors/weights/bands; parameter or domain/instrument tuning after reading outcomes; chart-type variants; unregistered exit overlays, stops, targets, trailing exits, sizing, pyramiding, portfolio weighting, risk management; changes to strict/loose/incremental referee logic or the D-dogfood-book reference; execution-realism claims; the final 30% global holdout.
- **Constraints**: EXP-020 SUPPORTED_FULL (ready {5m,1h,4h}, 0 invariant/holdout violations, deterministic replay), EXP-021/022 SUPPORTED, VAL-002 PASS, EXP-012/018/019 frozen-suite identity — all verified value-based from artifacts; cTrader emits no row at/after `AnalysisEndUtc`; Python ingests/validates only and never regenerates the candidate signal for screening; real `RealClose` return basis; `SourceCloseTime` temporal alignment; zero denominators null/non-reportable.

### Results / Observations

- `run_metadata.json`: `overall_status: REFUTED`, `admitted_cells: 12/12`, `blockers: []`, `smoke_status: [PASS, PASS, PASS]`, `pass_tally: {strict:0, loose:0, incremental:0, suite_pass:0, reportable:12}`.
- `dependency_manifest.csv`: 34/34 PASS. `csharp_avwap_smoke_checks.csv`: 5m/1h/4h PASS, 0 field mismatch, `max_abs_price_diff=0.0`, event counts 5978/421/109 identical (C# vs `xen.avwap`).
- `run_manifest.csv`: all 12 `admitted=true`, `same_feed_ok=true`, `feed_max_abs_diff=0.0`, `n_time_mismatch=0`. `holdout_fence_checks.csv`: candidate and reference max `SourceCloseTime` < `AnalysisEndUtc` in every cell.
- `standalone_suite_verdicts.csv`: 0/12 strict, 0/12 effective-loose. Net effects −1.41 (BTCUSD/4h) to +0.21 bps (EURUSD/4h) vs strict MDE 1/4/12; every `ci_lower` below loose τ (max −0.127, EURUSD/1h).
- `portfolio_fitness_verdicts.csv`: 0/12 `positive_incremental`; all 12 reportable, `n_reference_unaligned=0`, denominators 155–15,951; incremental edges −11.90 (USTEC/4h) to +6.05 bps (XAUUSD/4h), all ≪ floors 12/16/32; small positive 4h points EURUSD/4h +4.39 (ci_lower +0.31) and XAUUSD/4h +6.05 (ci_lower −3.62) below floor.
- `strategy_metric_book.csv`: `successful_bounce_rate` 0.605–0.800; `model_net_bps` ~0-to-negative (BTCUSD/5m −0.740, BTCUSD/4h −1.362; EURUSD/4h +0.081); `lifetime_expectancy_bps` mostly negative (BTCUSD/4h −30.3; EURUSD/4h +8.0); `model_robust_ratio` null in all cells (MAD=0; strategy flat ~92.6% of bars, BTCUSD/5m); model mean/std negative vs small positive raw mean/std.
- `event_trade_diagnostics.csv`: long+short entries reconcile to metric-book `n_entries` per cell (audit cross-check).
- Audit verdict PASS: 0 critical, 0 warnings, 6 info; independent recomputation of BTCUSD/5m metric-book risk metrics matched bit-exact.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**REFUTED**

The predeclared Evidence-AGAINST criteria are met in full: all dependency and run-admission checks passed, all 12 instrument/domain cells are reportable against an aligned same-feed Donchian(20) reference, no suite component (strict, ratified-loose/fallback, or revised portfolio-fitness) passes any cell, and both standalone and incremental effects lie below their frozen domain detection floors in every cell. The baseline CF-AVWAP-001/HYP-004 signal does not qualify under the frozen Phase 004 suite on the first-70% analysis set. This is an admissible negative (not BLOCKED/INCONCLUSIVE) and a baseline-branch result, not a COMPONENT_REFUTED retirement of CF-AVWAP-001 (checkpoint `design.md` §8).

### Hypothesis-Agnostic Observations

- Conditional-event evidence (EXP-021 reaction, EXP-022 lifetime) did not carry through to a tradable, always-on, cost-bearing position judged by a stringent frozen referee — a documented gap between conditional event behavior and continuously-held strategy P&L.
- A 60–80% favorable-target rate co-exists with ~0/negative net expectancy because `successful_bounce_rate` excludes trend-change exits while net expectancy and lifetime returns include them; trend-change exits plus per-active-bar cost erode the edge.
- The robust mean/MAD risk level is structurally undefined for a strategy flat ~93% of the time (MAD=0) — handled per the scope zero-baseline rule as a null, with the mean/std diagnostic used for the model-vs-raw comparison.

---

## EXP-024 — AVWAP Event-Edge Dissipation Decomposition

> **RETAINED, fork leg discounted (2026-06-08).** The fork-(b) leg compared a
> cumulative per-event hold return against a per-bar floor — a category mismatch
> that makes fork (b) near-foreordained and low-information. **Retained findings
> stand:** the edge is relative-not-absolute (raw hold ~0 vs +3.8 bps EXP-021
> control-excess on 5m), and trend-change exits cut losers not winners
> (−2.79/−8.76/−17.59 bps). See the framing-divergence review.

**Status**: MIXED_OR_INCONCLUSIVE (RETAINED; fork leg discounted)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-020 AVWAP bounce events (CF-AVWAP-001 first branch), EXP-021 fixed-horizon reaction observations, EXP-022 lifetime observations, and 5m/1h/4h real OHLC domain bars rebuilt from the first-70% analysis slice; diagnostic only, no frozen suite

### Hypothesis Tests

1. **Diagnostic fork question**: Between EXP-021's positive fixed-horizon bounce reaction and EXP-023's ~0-to-negative always-on strategy expectancy, is the edge lost to fork (a) a fixable holding/exit problem, or fork (b) entry/position dilution that makes the always-on/bounded-hold overlay the wrong vehicle?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domain bars rebuilt from first-70% 1-minute analysis slices; EXP-020 `avwap_events.csv`; EXP-021 `reaction_observations.csv` for matched cross-check; EXP-022 event-role `lifetime_observations.csv` for completed lifetime reference.
- **Features**: direction-signed real-close gross returns over fixed bounded-hold horizons; completed common-set lifetime returns; bounded-vs-lifetime paired contrasts; regime-cluster bootstrap CIs; Holm adjustment across the horizon grid; trend-change return distribution; holding/exposure descriptors; secondary cost attribution.
- **Parameter ranges**: horizon grid `{1,2,3,4,5,6,8,10,12,16,20,24}` completed domain bars; loose floors 0.5/2/8 bps for 5m/1h/4h; margin `max(0.5 bps, 0.25 x floor)`; primary domain 5m; `N_BOOT=10,000`; `DOMAIN_MIN_COMPLETED=100`.
- **Exclusions**: frozen qualification suite; cTrader candidate screen; parameter/exit/detector tuning; global holdout; ALPHA/BAND sensitivity; EXP-025 direct line-S/R question.
- **Constraints**: first-70% analysis slice only; real domain Close returns; no synthetic prices; no percentage improvement over zero baseline; common completed-event denominators for bounded-vs-lifetime contrasts; EXP-020/021/022 substrate consistency required.

### Results / Observations

- `run_metadata.json`: `overall_status=COMPLETE`, `domain_verdicts={5m:FORK_B_DILUTION, 1h:INCONCLUSIVE_UNRESOLVED, 4h:INCONCLUSIVE_UNRESOLVED}`, `phase_verdict=MIXED_OR_INCONCLUSIVE`, `exp021_matched_crosscheck_max_abs_diff_bps=0.0`, event join row counts preserved, duplicate join rows 0.
- `domain_reconstruction_check.csv`: 12/12 EXP-020 metadata checks pass.
- `event_join_diagnostics.csv`: joined event rows 5m 19,242 / 1h 1,360 / 4h 309; completed common-set rows 5m 15,037 / 1h 1,033 / 4h 235; row counts preserved and duplicate join keys 0.
- `exp021_crosscheck.csv`: exact matched-event return reproduction for EXP-021 horizons `{1,3,6}`; matched event counts 5m 16,249, 1h 1,207, 4h 246/246/244; max row and mean absolute difference 0.0 bps.
- `fork_verdict.csv`:
  - 5m: `h*=16`, `g*=+0.370` bps, floor 0.5, CI `[-0.396,+1.164]`, `g_life=+0.058`, `delta=+0.312`, `n=15,037`, verdict `FORK_B_DILUTION`.
  - 1h: `h*=24`, `g*=+4.248` bps, floor 2.0, CI `[-10.190,+18.417]`, `delta=+6.197`, `n=1,033`, verdict `INCONCLUSIVE_UNRESOLVED`.
  - 4h: `h*=8`, `g*=+8.137` bps, floor 8.0, CI `[-22.769,+39.747]`, `delta=+16.840`, `n=233`, verdict `INCONCLUSIVE_UNRESOLVED`.
- `trend_change_returns.csv`: trend-change lifetime means 5m -2.79 bps (`[-3.32,-2.32]`), 1h -8.76 (`[-15.03,-3.24]`), 4h -17.59 (`[-40.38,+3.68]`); negative fractions 65.8%, 56.9%, 54.0%.
- `holding_exposure.csv`: event prevalence 2.68% / 2.26% / 2.21% of domain bars (5m/1h/4h); reconstructed active-bar fractions 6.17% / 5.73% / 5.67%; pyramid bounces 9,679/19,242 (5m), 636/1,360 (1h), 146/309 (4h).
- `cost_attribution.csv`: 5m `g*` gross +0.370 bps becomes -4.651 net; 1h +4.248 becomes -0.597; 4h +8.137 becomes +2.793 after mean round-trip costs.
- Audit verdict PASS: 0 critical, 2 warnings (1h/4h precision; mixed/inconclusive Stage-B handling), 3 info notes.

### Hypothesis-Specific Conclusion

**MIXED_OR_INCONCLUSIVE**

The primary 5m domain resolves to fork (b): bounded-hold gross returns do not reach the loosest suite floor, even before cost. The 1h and 4h domains remain inconclusive because above-floor point estimates have wide CIs that fail the floor-clearance rule. No domain supports fork (a), so EXP-026 `/EXIT` is not automatically justified by EXP-024 alone; any `/EXIT` continuation requires explicit mixed/inconclusive governance handling.

### Hypothesis-Agnostic Observations

- EXP-021's matched event-vs-control reaction and EXP-024's all/completed-event bounded-hold return are different estimands; the corrected cross-check proves the return formula matches on identical rows while showing that the positive matched-control component signal dilutes in the all-event vehicle.
- Trend-change exits are negative on average, which weakens the simple "holding too long gives back winners" explanation for EXP-023's failure.
- Sparse exposure (about 5.7-6.2% active bars) and many pyramid bounces contextualize why conditional event evidence can fail to become a cost-bearing always-on strategy.

---

## EXP-025 — AVWAP Line Support/Resistance Direct Test

> **INCONCLUSIVE — non-informative for HYP-001 (2026-06-08).** The event-bar
> line-rejection metric is structurally confounded: bounce triggers cross AVWAP
> intrabar by definition, inflating adverse penetration and biasing the metric
> negative before any data. It did **not** test HYP-001 (line as S/R), which
> remains untested. Carries zero weight in synthesis. See the framing-divergence
> review.

**Status**: INCONCLUSIVE (non-informative for HYP-001)
**Date**: 2026-06-08
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% 1-minute analysis slices via EXP-020 conventions; EXP-020 avwap_events.csv event definitions; same-regime non-event controls with line-proximity matching.

### Hypothesis Tests

1. **Hypothesis**: AVWAP bounce trigger bars from the supported CF-AVWAP-001 first branch show a larger event-bar AVWAP line-rejection score than matched same-regime non-event control bars on at least one EXP-020 ready domain, without touching the global holdout.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% 1-minute analysis slices; EXP-020 AVWAP event and regime tables; causal per-bar AVWAP replay for control matching.
- **Features**: Event-bar line-rejection score (close_rebound_bps - adverse_penetration_bps) with bullish/bearish direction formulas; matched same-regime line-proximate non-event controls (up to 5, min 3); regime-cluster bootstrap CI; stratified paired sign permutation test; Holm adjustment.
- **Parameter ranges**: Domains {5m, 1h, 4h}; max 5 controls, min 3; line-proximity rule abs(close_to_avwap_bps) <= max(1.0, band_spread_bps); 6-bar exclusion around triggers; 10,000 bootstrap/permutation resamples.
- **Exclusions**: frozen-suite candidate qualification, cTrader strategy-host generation, EXP-021 fixed-horizon return continuation, EXP-022 lifetime outcomes, EXP-024 bounded-hold decomposition, threshold sweeps, percentage improvement against zero baseline, final 30% global holdout.
- **Constraints**: dependency gate (EXP-020 SUPPORTED_FULL + EXP-024 documented); domain OHLC rebuilt from exact EXP-020 source files with metadata validation; causal AVWAP replay; event-bar h=0 only; no future returns; event-weighted cell means, equal-weight instrument domain estimator.

### Results / Observations

| Domain | Effect (bps) | CI Low | CI High | n | Holm p | Decision | Balance |
|--------|-------------|--------|---------|---|--------|----------|---------|
| 5m | -4.41 | -4.85 | -4.00 | 10,432 | 1.0 | EVIDENCE_AGAINST | OK (1.99 bps) |
| 1h | -16.94 | -22.12 | -11.77 | 763 | 1.0 | EVIDENCE_AGAINST | Broken (6.58 bps) |
| 4h | -6.77 | -34.13 | +22.80 | 120 | 1.0 | INCONCLUSIVE_SPANS_ZERO | Broken (27.57 bps) |

- All 24 reportable instrument/domain/direction cells show events with lower (more negative) line-rejection scores than matched controls.
- 0 events lost to invalid AVWAP or score; all non-reportable events due to <3 line-proximate controls.
- Domain reconstruction PASS (all 12 cells match EXP-020 metadata exactly).
- Audit: CONDITIONAL PASS (0 critical, 2 warnings: BTCUSD 5m proximity imbalance masked by domain pooling, 4h bootstrap degenerate clusters).

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

No domain meets Evidence FOR (all effects are negative). Evidence AGAINST does not apply because the 4h domain CI spans zero. The 5m domain is the cleanest read (unbroken balance, n=10,432, tight CIs) and shows clear EVIDENCE_AGAINST, but the predeclared criteria require all reportable domains to have CI upper bound ≤ 0 for Evidence AGAINST. The negative effect is structurally consistent: bounce triggers cross AVWAP by definition, so adverse intrabar penetration is inherent to the metric design.

### Hypothesis-Agnostic Observations

- The scoped metric likely conflates the trigger definition with the line-rejection signal: a bounce trigger cannot occur without adverse penetration (the intrabar crossover), so the line-rejection score systematically penalizes events versus non-crossing controls.
- EXP-025 does not invalidate EXP-021/022 positive component evidence (bounce continuation, lifetime outcomes), which test different constructs (regime-gated continuation and completion rather than bar-level line reaction).
- Phase 005 Stage A now completes with all three diagnostics resolved: EXP-023 REFUTED, EXP-024 MIXED_OR_INCONCLUSIVE, EXP-025 INCONCLUSIVE. No diagnostic provides a clean Stage A positive that automatically justifies Stage B.

---

## EXP-027 — Event-Level Evaluation Method: Definition and Sparse-Regime Calibration

**Status**: METHOD_VALID
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domains rebuilt from first-70% analysis slice of 1-minute time bars; EXP-020 regime intervals as matched-control scaffolding; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: A predeclared event-level evaluation method — with per-event matched-control expectancy as the binding decision statistic (reusing the EXP-021/022 regime-cluster bootstrap + stratified paired sign-permutation + Holm inference and Evidence-FOR rule), and an exposure-aware equity-curve-vs-buy-hold companion — exhibits controlled false-positive error (empirical FPR ≤ α₀ = 0.05 under known-null sparse event processes) and recovery (a finite empirical event-level MDE at TPR ≥ 0.80 while FPR ≤ α₀) across the 5m / 1h / 4h domains, within a sparse activity envelope bracketing the real AVWAP signal ({~3%, ~6%, ~12%} active).

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains from first-70% analysis slice. No chart-type views.
- **Features**: Per-event direction-signed log bps matched-control excess; regime-cluster bootstrap CI (1,000 resamples); stratified paired sign-permutation p-value (1,000 flips); Holm adjustment across 3 domains; Evidence-FOR rule (effect > 0 AND CI low > 0 AND Holm p ≤ α); exposure-aware equity-curve vs matched-control baseline companion; two null generators (placebo-on-real, block-permuted-returns); planted-edge additive drift.
- **Parameter ranges**: Activity grid {0.03, 0.06, 0.12}; primary p_trig=0.06; edge grid {0, 1, 2, 4, 8, 16, 32, 64} bps; α grid {0.10, 0.05, 0.01}, primary α₀=0.05; primary horizon H=3 with secondary H=1, 6; MAX_CONTROLS=5, MIN_CONTROLS=3, EXCLUSION_BARS=6; n_draws=500/cell; n_bootstrap=1,000; n_permutation=1,000; TPR target=0.80; FPR half-width max=0.03; TPR half-width max=0.05.
- **Exclusions**: Real AVWAP bounce-event outcomes (anti-overfitting fence — only synthetic signals used); frozen per-bar suite as evaluator; equity-curve companion as a pass-gate; any metric/parameter reselection against Phase 006 outcomes; HYP-001, exit overlays, detector/anchor branches, ALPHA/BAND/XTF/MA-DOMAIN sensitivity; activity outside {3%, 12%} (out-of-envelope); percentage improvement against zero baseline.
- **Constraints**: EXP-020 SUPPORTED_FULL dependency gate; first-70% analysis slice only (final 30% global holdout never loaded); real domain Close outcomes; same-regime control matching; look-ahead-safe placement/matching (timestamp, regime direction, anchor age only); fixed seeds via `seed_for(...)`; deterministic generation with replay check; vectorized control matching equivalence-guarded against EXP-021 reference.

### Results / Observations

- `run_metadata.json`: `overall_status: METHOD_VALID`, `fpr_controlled_primary: true`, `bracket_fpr_ok: true`, `recovered_domains: [5m, 1h, 4h]`, `all_domains_recovered: true`, `determinism_pass: true`, `companion_null_sane: true`, `control_matching_equivalence_pass: true`.

- **FPR summary** (fpr_summary.csv, 54 per-domain cells + 18 family-wise rows):
  - At α₀=0.05, primary p_trig=0.06: 5m placebo 0.016 [0.008, 0.031], 5m block 0.030 [0.018, 0.049]; 1h placebo 0.018 [0.009, 0.034], 1h block 0.034 [0.021, 0.054]; 4h placebo 0.030 [0.018, 0.049], 4h block 0.034 [0.021, 0.054].
  - Max per-domain FPR at any α/p_trig/null: 0.042 (1h, placebo, p_trig=0.03, α=0.10); at α₀=0.05: max 0.038.
  - Family-wise any-domain FPR at α₀=0.05: 0.064 (placebo, p_trig=0.06), 0.094 (block, p_trig=0.06).
  - All 54 cells precision-ok (max Wilson half-width 0.018, well below 0.03 ceiling).
  - No systematic FPR increase at higher activity; 5m/placebo/0.12 gives FPR=0.000.

- **TPR / MDE summary** (tpr_summary.csv, mde_summary.csv):
  - 5m MDE = 1.0 bps (TPR=1.000 [0.992, 1.000], TPR at g=0 = 0.016).
  - 1h MDE = 4.0 bps (TPR=0.818 [0.782, 0.849], TPR at g=2 = 0.302).
  - 4h MDE = 32.0 bps (TPR=0.998 [0.989, 1.000], TPR at g=16 = 0.738).
  - All 9 mde_summary rows recovered=true; all 72 tpr_summary rows precision-ok (max TPR Wilson half-width 0.041, below 0.05 ceiling).
  - TPR at α=0.01: 5m MDE=1.0, 1h MDE=8.0, 4h MDE=32.0 bps.

- **Equity companion** (equity_companion_summary.csv, 24 rows):
  - Null advantage rates: 5m 0.358, 1h 0.522, 4h 0.442 (near chance; no systematic false advantage).
  - Null mean equity advantage negative in all domains: 5m −533 bps, 1h −38 bps, 4h −179 bps.
  - Under planted edge: advantage rate and mean equity advantage monotonically increasing with g; rate reaches 1.000 at g=1 (5m), g=8 (1h), g=32 (4h).
  - Sortino-style risk-adjusted ratio tracks the same monotonic pattern.

- **Determinism**: Byte-identical FPR/TPR on a fixed (5m, p_trig=0.06, placebo_on_real) replay cell.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**METHOD_VALID**

All predeclared Evidence-FOR criteria from scope.md are met: (1) FPR ≤ α₀ = 0.05 in every domain at the primary p_trig=0.06 under both null generators (max per-domain FPR = 0.034 at α₀=0.05; all Wilson upper bounds ≤ 0.054); (2) FPR does not materially exceed α₀ across the {0.03, 0.06, 0.12} bracket (max bracket FPR = 0.038 at α₀=0.05); (3) a finite event-level MDE exists in every domain at p_trig=0.06 (5m: 1 bps, 1h: 4 bps, 4h: 32 bps); (4) determinism replay passes; (5) the equity-curve companion shows no systematic false advantage under null and monotonic edge detection under planted drift. The event-level method is a fit-for-purpose yardstick for the sparse (~6% active) regime. EXP-028 may proceed under this method.

### Hypothesis-Agnostic Observations

- The MDE gradient across domains (5m=1 < 1h=4 < 4h=32 bps) is consistent with the event-count gradient (~20,800 / ~1,750 / ~400 events/draw) — event count, not signal quality, is the binding constraint on power.
- The 5m MDE of 1 bps is driven by very high event count (~20,800/draw), not signal strength; the 1h and 4h MDEs (4 and 32 bps) are more informative for EXP-028 planning because they better approximate the real event count.
- The 4h MDE jump from TPR=0.738 at g=16 to TPR=0.998 at g=32 bps means the true MDE lies between 16 and 32 bps — a finer grid ({16, 20, 24, 28, 32}) would improve resolution.
- The FPR being well below α₀ in many cells (e.g. 0.000 at 5m/0.12 placebo_on_real) reflects conservatism from the Holm adjustment and three-condition Evidence-FOR rule — desirable for a screening yardstick (errs on the side of not declaring false edges), at the cost of slightly reduced power.
- The two null generators agree within tolerance across all cells, making accidental structure in the placebo-on-real generator an implausible explanation for the FPR control.
- The method is calibrated only on synthetic substrates; real-signal performance is unknown until EXP-028 (anti-overfitting fence — by design).

---

## EXP-028 — Faithful Selective AVWAP Strategy Re-Screen

**Status**: EVAL_SUPPORTED
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: Real 5m (strict), 1h and 4h (`min_coverage=0.90`) OHLC domain bars from first-70% analysis slice; EXP-020 AVWAP bounce events; EXP-022 lifetime completion outcomes; no chart-type views.

### Hypothesis Tests

1. **Hypothesis**: Under the frozen EXP-027 event-level evaluation method, the faithful selective AVWAP strategy — unchanged from the EXP-023 baseline — shows positive event-level edge (per-event matched-control expectancy > 0) on at least one domain (5m, 1h, or 4h), using only the first-70% analysis set and predeclared inference.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: Real 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-020 AVWAP events; EXP-022 lifetime observations; EXP-021 reaction observations for secondary-stability inputs.
- **Features**: PRIMARY (binding): symmetric own-exit matched-control lifetime excess reusing EXP-022 observations (event and control both completed under band-target/trend-change exit). SECONDARY (non-binding): endogenous-exit vs fixed-window control, gated by predeclared placebo-null calibration. Exposure-matched equity companion. Frozen EXP-027 inference tail: regime-cluster bootstrap CI, stratified paired sign-permutation, Holm across 3 domains.
- **Parameter ranges**: Alpha₀=0.05; N_BOOT=1000; N_PERM=1000; N_PLACEBO_DRAWS=100; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; fixed seeds with determinism replay.
- **Exclusions**: The frozen per-bar qualification suite as evaluation vehicle; asymmetric construction as binding gate; sweep/tuning/metric reselection; exit/detector/anchor branches; HYP-001; percentage improvement against zero baseline; costs/stops/sizing.
- **Constraints**: EXP-020 SUPPORTED_FULL and EXP-027 METHOD_VALID dependency gate; first-70% slice only; CloseTime ordering; real domain Close returns; pyramid bounces included as closer-to-original and absorbed by regime-cluster bootstrap; frozen inference tail hash-guarded against EXP-027 source drift.

### Results / Observations

- `overall_verdict`: EVAL_SUPPORTED. Binding gate PRIMARY symmetric own-exit lifetime excess.
- PRIMARY per-domain:
  - 5m: effect +5.78 bps, CI [5.39, 6.13], Holm p=0.003, n=12,795, EVIDENCE_FOR.
  - 1h: effect +23.38 bps, CI [17.40, 29.32], Holm p=0.003, n=924, EVIDENCE_FOR.
  - 4h: effect +69.02 bps, CI [46.84, 90.52], Holm p=0.003, n=187, EVIDENCE_FOR.
- SECONDARY: 1h calibrated (FPR=0.03), EVIDENCE_FOR; 5m/4h NOT_CALIBRATED as expected.
- Equity companion: all domains advantage_rate=1.0, positive Sortino differences.
- Fixed-horizon secondary-stability: all h1/h6 excesses positive (no secondary horizon instability).
- Audit PASS: 0 critical, 0 warnings, 3 info.
- Pyramid split: 6,785 pyramid / 7,121 non-pyramid (5m/1h/4h combined).
- Dependency gate PASS (EXP-020 SUPPORTED_FULL, EXP-027 METHOD_VALID).
- Frozen inference hash PASS, alignment 12/12 cells, reconciliation 0 bad.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**EVAL_SUPPORTED**

All predeclared Evidence-FOR criteria are met: (1) dependency gate passes; (2) at least one domain (all three) is PRIMARY Evidence-FOR at α₀=0.05 with effect > 0, CI_low > 0, and Holm p ≤ 0.05; (3) secondary-horizon stable (no domain has both h1 and h6 negative). The faithful selective AVWAP strategy shows positive event-level edge on all three domains under the fit-for-purpose, in-envelope EXP-027 method. The EXP-023 negative was a framing/dilution artifact caused by applying a per-bar floor to a ~6%-active event strategy.

> **Caveat (cTrader parity) — RESOLVED 2026-06-09 by EXP-029.** This EVAL_SUPPORTED originally rested on a Python re-analysis of the canonical EXP-020 event substrate, with the faithful strategy not yet executed through its cTrader C# per-bar streaming path. **EXP-029 closed this:** the corrected `AvwapBounceModel.cs` (pyramids opened as independent positions, executed completion serialized) was run on cTrader per-bar streaming and reproduced this PRIMARY excess on all 3 domains (parity CONSISTENT; all 5 binding gates pass, incl. exit-parity match_rate=1.0). EXP-028 is therefore **cTrader-confirmed**. See `checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md` and the EXP-029 entry below.

### Hypothesis-Agnostic Observations

- The effect increases monotonically 5m < 1h < 4h (+5.78 / +23.38 / +69.02 bps), matching the EXP-021/022 domain gradient and reflecting larger absolute moves over longer holds.
- The binding PRIMARY gate uses the symmetric construction that EXP-027 actually calibrated; the asymmetric secondary gate is correctly non-binding where uncalibrated (5m FPR=1.0, 4h FPR=0.26).
- Pyramid bounces (~50% of events) do not drive the result — the regime-cluster bootstrap absorbs within-regime dependence — but including them is faithful to the original concept.
- This is the first fairly-evaluated positive result for CF-AVWAP-001 under a correct yardstick; the next stage is operator review (FAMILY_REVIEW or robustness/protocol testing).
- HYP-001 (AVWAP line S/R) remains untested and open.

---

## EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

**Status**: CONSISTENT (parity confirmed — EXP-028 upgraded to cTrader-confirmed)
**Date**: 2026-06-09
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: cTrader `Mode=StrategyHost` per-bar streaming output (`positions.parquet`, `avwap_events.parquet`) from the corrected C# `AvwapBounceModel`, on real 5m (strict), 1h and 4h (`min_coverage=0.90`) domain bars resampled in-engine from the 1-minute cTrader feed, first-70% analysis slice; no chart-type views.

### Hypothesis Tests

1. **Hypothesis**: The corrected C# AVWAP strategy (pyramid bounces opened as independent positions; executed completion serialized) running on cTrader via per-bar streaming produces event-level results consistent with the Python-only EXP-028 re-analysis — per-domain PRIMARY verdicts and effect directions agree and effects fall inside the predeclared parity tolerances — confirming the Python re-analysis faithfully represents the cTrader execution path. Same estimand (symmetric own-exit matched-control excess) and same frozen EXP-027 inference (hash `ea261b9ee0a8aca3`) as EXP-028; first-70% analysis set only.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: cTrader-emitted corrected-model runs (12 cells); PRIMARY estimand rebuilt on the cTrader `RealClose` feed; matched controls rebuilt in Python via imported EXP-021/022 helpers (analysis construct — never a Python signal oracle); regime/anchor/frozen-targets/pyramid tag taken from the C# emission.
- **Features**: PRIMARY (binding): per-event symmetric own-exit matched-control lifetime excess (`event_lifetime_bps − mean(control_lifetime_bps)`, direction-signed log bps on cTrader `RealClose`). Five predeclared binding parity gates: verdict-match, magnitude-equivalence (F02), count ±10% incl. pyramid split (F04), exit-parity grading of the C# completion code (F01), 5m signal-layer reconciliation vs the EXP-020 substrate (F03). Non-binding: fixed-horizon {1,3,6} secondary-stability (cTrader-feed analog, F07); exposure-matched equity companion.
- **Parameter ranges**: α₀=0.05; N_BOOT=1000; N_PERM=1000; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; effect-equiv margin max(2 bps, 25%·|ref|), divergence margin max(2 bps, 50%·|ref|); count tol ±10%/±20%; exit-parity ≥99%; signal-match ≥98% / target rel-diff ≤1e-3; fixed seeds; per-instrument `AnalysisEndUtc` fence (BTCUSD 2025-06-17T22:38Z, EURUSD 2025-05-09T16:55Z, USTEC 2025-05-12T04:54Z, XAUUSD 2025-05-12T03:35Z).
- **Exclusions**: Any change to the frozen EXP-027 inference; strategy parameter tuning / band sweep / exit redesign / sizing / costs; detector/anchor branches (`/LB`,`/MB`,`/ATR`,`/ANCHOR`), `/ALPHA`,`/BAND`, cross-timeframe variants; HYP-001; the frozen per-bar qualification suite as the vehicle (this is an event-level parity check, not a per-bar re-screen); percentage improvement against a zero baseline.
- **Constraints**: EXP-027 METHOD_VALID and EXP-028 results present (dependency gate); frozen-inference hash hard-asserted `== ea261b9ee0a8aca3 ==` EXP-028's; estimand evaluated on the same cTrader feed the C# executed on; holdout fence in-robot (`AssertCanEmit`) + Python re-assertion; cross-feed alignment by `SourceCloseTime`, never bar index; real-price `RealClose` returns only.

### Results / Observations

- `overall_parity_disposition`: **CONSISTENT**; per-domain bands 5m/1h/4h all CONSISTENT; no INCONSISTENT domain.
- PRIMARY per-domain (EXP-029 cTrader vs EXP-028 Python):
  - 5m: +5.79 bps CI [5.37, 6.18] vs +5.78 [5.39, 6.13]; |Δ|=0.007; Holm p=0.003; n=12,784 vs 12,795; both EVIDENCE_FOR.
  - 1h: +23.33 bps CI [17.46, 28.91] vs +23.38 [17.40, 29.32]; |Δ|=0.054; Holm p=0.003; n=927 vs 924; both EVIDENCE_FOR.
  - 4h: +69.02 bps CI [49.32, 90.38] vs +69.02 [46.84, 90.52]; |Δ|=0.000 (bit-identical point estimate, differing CIs); Holm p=0.003; n=187 vs 187; both EVIDENCE_FOR.
- Binding gates (all domains): verdict-match ✔; magnitude-equivalent ✔ (no magnitude-divergent); count ±10% ✔ (total/bull/bear/pyramid within ±0.5%); exit-parity ✔ (`match_rate`=1.0 on 15,027/1,038/236 events; max bps discrepancy 1.8e-11/1.4e-13/0.0); 5m signal-layer ✔ (per-instrument EXP-020 trigger match 0.9990/0.9978/0.9998/1.0, all ≥0.98; matched-target median rel-diff 0.0).
- Pyramid split: 6,254/445/84 (EXP-029) vs 6,258/443/84 (EXP-028).
- Integrity: `frozen_inference_hash`=`ea261b9ee0a8aca3` (== EXP-028, hard-asserted); `control_matching_equivalence_pass`=true; `reconciliation_bad`=0; holdout fence respected (per-cell max `SourceCloseTime` < `AnalysisEndUtc`).
- Equity companion (non-gating): advantage 5m +20,115 / 1h +5,819 / 4h +3,755 bps; advantage_rate 1.0; positive Sortino differences.
- Audit PASS: 0 critical, 0 warnings, 4 info.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**CONSISTENT (parity confirmed).**

All five binding gates hold on all three domains (≥2/3 required) and the 5m signal-layer passes with no INCONSISTENT domain, so under the predeclared disposition rule EXP-028's Python-only EVAL_SUPPORTED is **upgraded to cTrader-confirmed**. The corrected C# strategy executed on cTrader per-bar streaming reproduces EXP-028's per-event excess, verdicts, counts, and pyramid split, with the entry signal (F03), pyramid handling (F04), and executed completion code (F01) all independently graded. The Phase 006 objective is fully satisfied and the EXP-028 omission is closed.

### Hypothesis-Agnostic Observations

- Exit-parity match_rate=1.0 with non-zero residuals (~1e-11/1e-13) shows the C# completion code and the Python `scan_lifetime` are genuinely independent implementations that agree to float precision — a real cross-implementation grade, not a tautology.
- The 4h PRIMARY point estimate is bit-identical to EXP-028 while 5m/1h differ slightly; audit-verified as cTrader 4h feed coinciding with the local feed for the fenced window (separate code paths, differing CIs), consistent with VAL-002's ≤1.83 bps drift being an upper bound, not a guaranteed difference.
- Secondary-horizon {1,3,6} numbers intentionally differ from EXP-028 (F07): computed from the cTrader feed and feeding only the non-binding stability guard; the PRIMARY excess is the sole parity object.
- This is event-level parity, not per-bar-suite tradability: EXP-023's per-bar REFUTED is not overturned, all effects are gross (no costs), and the holdout remains sealed. HYP-001 remains untested and open.
- Process lesson recorded: a "faithful re-screen" must state its execution path (cTrader per-bar vs Python re-analysis) explicitly in scope, and Stage 4 governance must check it against the lineage the faithfulness clause assumes.

## EXP-030 — Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy

**Status**: INCONCLUSIVE (phase outcome — no domain clears the tradability gate)
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: Per-event lifetime outcomes from EXP-022 (`lifetime_observations.csv`, first-70% analysis set); cost overlay as per-instrument round-trip bps constants (CONSERVATIVE binding: EURUSD 3.0 / USTEC 5.0 / XAUUSD 6.0 / BTCUSD 16.0 bps). No domain-bar reconstruction. No chart-type views.

### Hypothesis Tests

1. **Hypothesis**: Under a predeclared, event-level per-position cost/slippage model (CONSERVATIVE variant binding), the faithful selective AVWAP strategy — trade logic identical to the EXP-028/029 baseline — retains positive **net** per-event expectancy on at least one domain (5m, 1h, 4h), on the first-70% analysis set.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: Per-event lifetime outcomes from EXP-022 (`lifetime_observations.csv`, `role=event` + `reportable_event=true` + completed outcomes; pyramids included); per-event matched-control means for the non-binding attribution companion; per-instrument regime scaffolding from EXP-020 for bootstrap strata.
- **Features**: Binding: absolute net per-event expectancy `mean(lifetime_bps − RT_i)` per instrument (event-weighted), equal-weighted across reportable instruments per domain. Non-binding: net matched-control excess (gross excess shifted by RT_i). Per-instrument break-even RT table (descriptive). Four scoped plots: net expectancy forest, gross→net waterfall, break-even heatmap, verdict summary.
- **Parameter ranges**: α₀=0.05; N_BOOT=1000; domains 5m/1h/4h; instruments BTCUSD/EURUSD/USTEC/XAUUSD; cost table (operator-declared, frozen); MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; DOMAIN_MIN_INSTRUMENTS=3; fixed seeds.
- **Exclusions**: The frozen per-bar suite as tradability vehicle (EXP-023 trap); any second/alternative cost table; strategy parameter change, event filter, exit overlay, sweep, or tuning; Stage-C branches; HYP-001; holdout release (EXP-032 deferred); financing/swap costs; position sizing/leverage/portfolio; percentage improvement against zero baselines.
- **Constraints**: (1) Binding metric = absolute net, not excess-minus-cost. (2) Frozen EXP-027 inference tail imported hash-guarded (pinned `e50873d12a9f68d9`). (3) Sign-permutation leg invalid for absolute estimand; significance = one-sided bootstrap p + `CI_low > 0` + Holm. (4) Reconciliation guard: recomputed gross excess must reproduce EXP-028 to ≤0.01 bps. (5) Commute check: net bootstrap = gross − mean_inst(RT) elementwise. (6) Holdout fence inherited (all rows are EXP-022 first-70% outputs). (7) Cost table frozen pre-net-read; a net-negative is a valid outcome. (8) Determinism replay.

### Results / Observations

- Phase outcome: **INCONCLUSIVE**.
- CONSERVATIVE binding net per-event expectancy (equal-weight cross-instrument domain mean):
  - 5m: −6.74 bps [−7.04, −6.38], Holm p=1.000 → EVIDENCE_AGAINST; n=12,795
  - 1h: −6.04 bps [−11.02, −1.53], Holm p=1.000 → EVIDENCE_AGAINST; n=924
  - 4h: +2.60 bps [−14.87, +19.28], Holm p=1.000 → INCONCLUSIVE_SPANS_ZERO; n=187
- Gross absolute per-event expectancy (pre-cost): 5m=+0.76, 1h=+1.46, 4h=+10.10 bps.
- Per-instrument net (CONSERVATIVE): EURUSD-4h = +12.38 bps [CI: +2.67, +21.46] — non-binding individual cell excluding 0. All 5m/1h cells negative with CI < 0. BTCUSD RT_cons=16 bps dominates the equal-weight mean.
- Non-binding attribution companion (net matched-control excess): 1h/4h CONSERVATIVE EVIDENCE_FOR (Holm p=0.003); 5m CONSERVATIVE EVIDENCE_AGAINST.
- Integrity guards: reconciliation exact match (0.00 bps vs EXP-028), commute check machine-epsilon (max 7e−15 bps), frozen inference hash verified (e50873d12a9f68d9), determinism replay PASS, seed robustness PASS (8 seeds, stable CI boundaries).
- Audit: PASS (0 critical, 0 warnings, 1 info).
- Plots: `net_expectancy.png`, `gross_to_net_waterfall.png`, `breakeven_heatmap.png`, `verdict_summary.png`.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE** (per scope phase-outcome definition). The cost-bearing tradability gate for EXP-032 (holdout release) is **not passed**. No domain reaches EVIDENCE_FOR on the binding absolute net metric under CONSERVATIVE costs.

5m and 1h are cleanly EVIDENCE_AGAINST (gross absolute ≪ any instrument's RT_cons). 4h is INCONCLUSIVE_SPANS_ZERO (point estimate +2.60 bps, but CI half-width ~17 bps with n=187). EURUSD-4h individually survives costs (descriptive, uncontrolled multiplicity), but the binding equal-weight cross-instrument metric does not resolve positively.

The Phase-006 gross edge is not overturned: the non-binding attribution companion (net matched-control excess) is EVIDENCE_FOR on 1h/4h, confirming the relative edge survives costs. The distinction is that costs are charged against the absolute P&L leg (the deployable quantity), which must carry the control discount that the matched-control estimator removes.

### Hypothesis-Agnostic Observations

- **Absolute-vs-relative gap**: The binding absolute metric (INCONCLUSIVE/AGAINST) and the non-binding companion (FOR on 1h/4h) diverge because costs are charged against the raw event P&L, not against the excess. The edge is predominantly relative (control selection) rather than absolute raw P&L on 5m/1h; on 4h the gross absolute is larger and the distinction matters less.
- **BTCUSD cost dominance**: At 16 bps round-trip, BTCUSD produces 4× the drag of EURUSD (3 bps) in the equal-weight mean. A per-instrument tradability test with multiplicity control could reveal a different conclusion on low-cost instruments.
- **4h power limitation**: The absolute estimand's wider CI (no control-differencing) means n=187 cannot resolve a +2.60 bps net effect. This is an honest limitation, not evidence of no edge.
- **The 5m gross absolute is ~0.76 bps**: Confirms EXP-024's retained finding that the 5m edge is entirely relative (control discount), making 5m untradable under any realistic cost model.

---

## EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)

**Status**: COMPLETED (ISOLATION_READ_UNRESOLVED)
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: Rebuilt 5m/1h/4h OHLC domain bars from first-70% analysis slice; EXP-022 lifetime observations (event + control, pyramids included); fixed-horizon recompute at H∈{1,6} on rebuilt domain Close series; frozen EXP-027 inference tail

### Hypothesis Tests

1. **Exploratory question (diagnostic decomposition)**: Of the EXP-028 measured per-event matched-control excess (+5.78 / +23.38 / +69.02 bps on 5m/1h/4h), how much is attributable to AVWAP bounce entry timing versus the EXP-022 band-target/trend-change exit rule? Per-domain attribution label under a predeclared sign-complete classifier.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% 1-minute analysis slice (EXP-020 convention); EXP-022 `lifetime_observations.csv` (PRIMARY population, pyramids included); rebuilt domain Close series for fixed-horizon recompute at H∈{1,6}; frozen EXP-027 inference tail imported unchanged.
- **Features**: Three additive matched-control–differenced per-event legs — X_full (BTC exit, replicates EXP-028 PRIMARY), X_entry (neutral fixed-horizon exit at H=6 primary / H=1 companion), X_exit (X_full − X_entry, the exit-rule's differential value). Per-event additive decomposition verified to machine precision. Predeclared sign-complete classifier (ENTRY_DOMINANT / EXIT_DOMINANT / MIXED / MIXED_UNRESOLVED / INCONCLUSIVE) with 0.67 dominance cut.
- **Parameter ranges**: Domains 5m (strict) / 1h / 4h (`min_coverage=0.90`); neutral exit horizons H∈{1,6} (H=6 PRIMARY); dominance cut 0.67; α₀=0.05; N_BOOT=1000; N_PERM=1000; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30; MIN_DIRECTION_EVENTS=8; fixed seeds via `seed_for`.
- **Exclusions**: Costs/slippage (EXP-030's separate question); the frozen per-bar suite; horizon sweep beyond {1,6}; post-result leg reselection; HYP-001; exit-overlay redesign; holdout release (EXP-032 deferred); percentage-improvement-against-zero-baseline metrics (shares computed only when X_full CI_low > 0).
- **Constraints**: First-70% slice only; rebuilt domain bars validated against EXP-020 metadata (12/12 cells match); X_full reconciled against EXP-028 (exact 0.0 bps abs diff on all domains); frozen inference tail hash-verified against EXP-027; additive decomposition enforced (max residual 3.55e-15 bps); events with start_idx+H beyond analysis-set boundary are non-reportable at that horizon; real domain Close returns only; no synthetic prices.

### Results / Observations

- Phase outcome: **ISOLATION_READ_UNRESOLVED** — all domains flip between ENTRY_DOMINANT (H=6) and EXIT_DOMINANT (H=1); no domain has H=1 and H=6 in agreement.
- X_full reconciliation: 0.0 bps abs diff on all domains vs EXP-028 PRIMARY (5m: 5.7785, 1h: 23.3839, 4h: 69.0157 bps).
- **H=6 (PRIMARY) — all domains ENTRY_DOMINANT**:
  - 5m: X_entry=+8.84, X_exit=−3.06 bps (exit not signif.), s_entry=1.53
  - 1h: X_entry=+26.53, X_exit=−3.15 bps (exit not signif.), s_entry=1.13
  - 4h: X_entry leg-significant [37.89, 112.30], exit not signif.
- **H=1 (companion) — all domains EXIT_DOMINANT**:
  - 5m: X_entry=+1.16, X_exit=+4.61 bps (both signif.), s_exit=0.80
  - 1h: X_entry not signif., X_exit=+23.37 bps (s_exit=1.00)
  - 4h: X_entry not signif., X_exit=+61.03 bps (s_exit=0.88)
- Exit-substitution mechanism: at H=1, BTC exit outperforms FH(1) on events (+0.42 bps) and underperforms on controls (−4.19 bps). At H=6, the sign flips: event dH=−0.60 bps vs control dH=+2.47 bps.
- Additivity verified: max domain-level residual 3.55e-15 bps.
- Audit: CONDITIONAL PASS (1 warning: NaN passthrough in Polars is_not_null for 4h H=6 companion-horizon only — classification unaffected).

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**ISOLATION_READ_UNRESOLVED.** The entry/exit attribution is unresolved because the predeclared resolution condition (H=1 and H=6 agree on the primary domain) is not met. ALL domains show entry-dominant at H=6 but exit-dominant at H=1 — a horizon-dependent pattern that is itself the central finding. The BTC exit is a differential benefit at short horizons (loss-cutting) but a differential drag at longer horizons (trend-truncation). The edge is real (X_full confirmed) but its decomposition is horizon-sensitive. This mechanism information constrains future scope design: an exit redesign must account for the horizon-dependent trade-off.

### Hypothesis-Agnostic Observations

- Entry timing carries >100% of the H=6 excess on 5m (s_entry=1.53) because the BTC exit is a net drag on bounce-entries relative to the fixed-horizon exit at that horizon.
- At H=1, the exit dominates (s_exit=0.80 on 5m) — the BTC exit's loss-cutting function adds differential value on bounce-entries vs controls at very short horizons.
- The horizon flip is consistent across all three domains, suggesting it is a structural property of the BTC exit, not a noise artifact.
- The unresolved isolation does not invalidate EXP-028's positive edge; it merely shows the edge is not cleanly attributable to either entry or exit individually.
- The 4h companion-horizon results carry a NaN point-estimate caveat for BTCUSD (audit Warning 1); the label (ENTRY_DOMINANT) uses CI-based logic and is unaffected.

---

## EXP-033 — TRAIN-Only Horizon Sweep (Attribution Crossover + FH(H) Net Curve)

**Status**: MEASUREMENT_COMPLETE
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-022 lifetime observations (5m/1h/4h OHLC domains); rebuilt domain series via `xen.bar_aggregator`; EXP-020 event timestamps; no chart-type views

### Hypothesis Tests

1. **Diagnostic deliverable (DIAG-004, 0 slots)**: (A) Characterise the attribution crossover horizon(s) where the AVWAP edge shifts from exit-driven to entry-driven, resolving EXP-031's horizon-dependent flip. (B) Measure the FH(H) absolute net curve on TRAIN and emit mechanical B2 selections (one-SE H\*, pyramid policy) for Tier-B /EXIT-FH planning.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice; EXP-022 `lifetime_observations.csv` (events + controls); EXP-020 event timestamps.
- **Features**: Attribution decomposition — three additive matched-control–differenced per-event legs (X_full, X_entry at fixed-horizon exit H, X_exit = X_full − X_entry), s_entry share, crossover horizon marker. FH(H) absolute net curve — fixed-horizon variant of the BTC exit at H ∈ {1,2,3,4,6,8,12,24} domain bars under frozen costs + financing, mechanical one-SE H\* and pyramid-policy selections, split-half stability disclosure. Reconciliation anchors against EXP-031 H∈{1,6}.
- **Parameter ranges**: Domains 5m/1h/4h; H grid {1,2,3,4,6,8,12,24}; regression horizon H_reg = 4 (attribution); objective set excludes BTCUSD (D0 §4); TRAIN nested 70% of domain bars; N_BOOT=1000; MIN_CONTROLS=3; MIN_REPORTABLE_EVENTS=30.
- **Exclusions**: TEST/holdout validation, cost-model iteration, conditioning analysis, real-signal re-screening, parameter tuning after reading results, HYP-001, any Tier-B slot consumption.
- **Constraints**: TRAIN-only (first 70% of first-70% analysis slice); real domain Close returns; frozen EXP-027 inference tail (pinned `e50873d12a9f68d9`); reconciliation anchors against EXP-031 before any sweep output; additivity verified (max residual 3.55e-15 bps).

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `deliverable_a_complete: true`, `deliverable_b_complete: true`, `dependencies_ok: true`, `reconciliation_pass: true`.
- **Attribution crossover**: 5m crosses s_entry = 0.5 at H=3 (STABLE_CROSSOVER); 1h crosses at H=4 (STABLE_CROSSOVER). 4h UNPOWERED (~90 TRAIN events across 4 instruments).
- **FH(H) net curve**:
  - 5m: B2-ineligible (grid max = −3.72 bps at H=24, ≤ 0).
  - 1h: B2-ineligible (grid max = −0.99 bps at H=6, ≤ 0).
  - 4h: B2-eligible H\*=8 (first within one SE of grid max +45.79 bps at H=24), net_at_H\* = +31.30 bps, pyramid policy = all_legs. Stability disclosure: `eligibility_stable = true`, `h_star_stable = false` (argmax shifts between H=12 and H=24 across halves), `policy_stable = true`.
- Reconciliation: EXP-031 H=1/5m exact match (0.0 bps diff).
- Audit PASS: 0 critical, 0 warnings, 0 info.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**MEASUREMENT_COMPLETE.** Both diagnostic deliverables produced. Attribution resolves the Phase-7 open question: the horizon-dependent flip is structural (loss-cutter at short horizons, trend-truncator at long). The capture-efficiency path (B2) is viable only on 4h, with a stability caveat. The selectivity lever (B1) is the remaining Tier-B path for 5m/1h.

### Hypothesis-Agnostic Observations

- The crossover at H=3 (5m) / H=4 (1h) is earlier than the EXP-031 H=6 entry-dominant horizon because the fixed-horizon exit at those H already replaces the BTC exit's long-horizon drag — entry becomes the dominant carrier as soon as the exit's differential edge fades.
- 5m/1h FH(H) net curves confirm the fixed-horizon exit cannot rescue absolute net on powered domains; the base absolute is already negative even before considering the exit swap.
- The 4h H\* fragility flag (`h_star_stable = false`) is a descriptive point-estimate disclosure, not a formal test. EXP-037 scope should weigh it before spending a Tier-B slot.
- BTCUSD excluded from the objective set per D0 §4; all per-instrument FH(H) curves are disclosed for completeness.

---

## EXP-034 — Per-Instrument Cost-Bearing Tradability Screen (with Financing)

**Status**: A1_STRICT_PASS (TEST CONFIRMATION REQUIRED)
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-022 lifetime observations (5m/1h/4h OHLC domains); EXP-020 event timestamps; rebuilt domain series for completion timestamps; no chart-type views

### Hypothesis Tests

1. **Hypothesis**: In the D0-declared fixed sequence (EURUSD-4h → USTEC-4h → XAUUSD-1h), at least one instrument×domain cell retains positive per-event net expectancy after subtracting frozen CONSERVATIVE RT costs plus adverse-side financing, under FWER control at one-sided α = 0.05.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4, but only family EURUSD-4h, USTEC-4h, XAUUSD-1h tested in sequence).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice; EXP-022 lifetime observations; EXP-020 event timestamps for completion-calendar-days computation.
- **Features**: Per-event net = `lifetime_bps − RT_cons_i − financing_i`, where `financing_i = rate_i × elapsed_calendar_days(trigger_close, completion_close)` (adverse-side, fractional calendar days). Fixed-sequence Holm procedure. Binding rule (F01 amendment): one-sided bootstrapped p ≤ α AND one-sided 95% CI lower bound > 0. Reconciliation guards (identical counts, no-financing nets vs EXP-030). All-12-cell descriptive map.
- **Parameter ranges**: Domains 5m/1h/4h; α=0.05 (one-sided); declared sequence order EURUSD-4h → USTEC-4h → XAUUSD-1h; RT_cons table EURUSD=3.0, USTEC=5.0, XAUUSD=6.0, BTCUSD=16.0 bps; financing rates EURUSD=0.6, USTEC=1.2, XAUUSD=1.2, BTCUSD=10.0 bps/day; N_BOOT=1000; MIN_REPORTABLE_EVENTS=30.
- **Exclusions**: Strategy changes, cost-model iteration, exit redesign, conditioning analysis, holdout load, HYP-001, percentage improvement baselines.
- **Constraints**: Frozen EXP-027 inference tail (pinned `e50873d12a9f68d9`); fixed sequence predeclared D0 before measurement; reconciliation against EXP-030 to ≤0.01 bps; financing computed only for events with valid completion timestamps; adverse-side bounds real swap regardless of direction.

### Results / Observations

- Phase outcome: **A1_STRICT_PASS — EURUSD-4h SEQUENCE_PASS_ALPHA05**.
- Cell 1 (EURUSD-4h): net = +11.77 bps [one-sided 95% lower bound = +3.90 bps, boot_p = 0.009] → PASS. n=39 events, mean financing = 0.61 bps/event.
- Cell 2 (USTEC-4h): net = +8.90 bps, CI [−21.10, +35.09], boot_p = 0.281 → INCONCLUSIVE (predeclared power-limited). G1-lenient flag = true.
- Cell 3 (XAUUSD-1h): NOT_TESTED (sequence stopped). Descriptive: net = −0.35 bps, CI [−5.18, +4.51], boot_p = 0.563. G1-lenient flag = false.
- All-12-cell descriptive map: no cell outside declared family has positive net (all EVIDENCE_AGAINST or INCONCLUSIVE_SPANS_ZERO).
- Reconciliation: no-financing nets match EXP-030 to machine precision (max abs diff 3.55e-15 bps).
- Audit PASS: 0 critical, 0 warnings, 0 info.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**A1_STRICT_PASS (TEST CONFIRMATION REQUIRED).** EURUSD-4h passes the binding one-sided α = 0.05 test. Per design §8.4 (F02 amendment, 2026-06-10): this is necessary-but-not-sufficient for holdout release. EURUSD-4h routes to a one-shot Tier-B TEST-stratum confirmation of the same registered baseline estimand.

### Hypothesis-Agnostic Observations

- The A1 pass is the only positive net-equity cell across all 12 instrument×domain combinations, confirming the EXP-030 picture: the only headroom is EURUSD-4h.
- Financing is a small deduction (mean 0.61 bps/event on multi-day 4h holds) relative to the gross absolute headroom (~12.38 bps pre-financing), so the financing layer changes no verdicts.
- USTEC-4h's +8.90 bps point is not resolvable with n=36, as predeclared. If the cell were individually tested with more events (Tier B or later analysis), the ≈+9 bps point would be worth revisiting.
- The first-cell pass is a genuine economic finding: EURUSD-4h net expectancy (~12 bps) is several multiples of the 4h strict gate MDE (12 bps) and well above the loose MDE (8 bps), so it is not a marginal near-zero outcome.

---

## EXP-035 — TRAIN-Only Conditioning Characterisation (Clinical Dimensions)

**Status**: CHARACTERISATION_DELIVERED (zero G1-qualified dimensions)
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: EXP-022 lifetime observations (5m/1h/4h OHLC domains); EXP-020 band geometry at trigger; rebuilt domain series for ATR covariate; no chart-type views

### Hypothesis Tests

1. **Diagnostic deliverable (DIAG-005, 0 slots)**: Identify predeclared, causally-available-at-confirmation event characteristics (%completion-to-target terciles, session, trailing-vol percentile) that identify clinical subsets of bounce events with positive net expectancy under frozen costs + financing — quantified via the G1 conjunction (§8.1: materiality ∧ structure ∧ stability ∧ multiplicity, Holm α_G1 = 0.10). Hard no-selection rule.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all 4).
- **Data Views / Feature Categories**: 5m/1h/4h OHLC domains rebuilt from first-70% analysis slice; EXP-022 lifetime observations; EXP-020 event timestamps and band geometry; rebuilt domain Close series for C3 trailing ATR.
- **Features**: Three predeclared dimensions: C1 (%completion-to-target at confirmation, TRAIN-quantile terciles), C2 (session: Asia/London/NY UTC hour bins), C3 (trailing 252-bar ATR percentile, TRAIN-quantile terciles). Joint cluster-bootstrap contrast CI (F06), selection-aware stratified permutation (F05). G1 conjunction: (i) materiality — SNR ≥ 1 AND candidate-bin net > 0; (ii) structure — weak monotonic ordering; (iii) stability — same candidate bin in both TRAIN halves; (iv) multiplicity — Holm α_G1 = 0.10 on permutation p.
- **Parameter ranges**: Domains 5m/1h/4h; TRAIN nested 70% of domain bars; ATR period 14 (Wilder SMA); trailing window 252 bars; N_BOOT=10000; N_PERM=10000; MIN_EVENTS_PER_BIN=30; MIN_DIRECTION_EVENTS=8; α_G1=0.10.
- **Exclusions**: Interaction/conjunction analysis, TEST/holdout validation, cost-model iteration, parameter tuning, post-hoc dimension selection, real-signal re-screening, HYP-001.
- **Constraints**: TRAIN-only (first 70% of first-70% analysis slice); real domain Close returns; frozen EXP-027 inference tail (pinned `e50873d12a9f68d9`); frozen costs + financing constants; hard no-selection rule — dimensions not promoted to Tier B without a fresh TEST read.

### Results / Observations

- Phase outcome: **CHARACTERISATION_DELIVERED — zero G1-qualified dimensions**.
- All 9 domain×dimension cells fail materiality (§8.1i): no candidate-bin mean net > 0 under frozen costs + financing.
- Closest cell: 5m/c1_completion (SNR=1.42, structured+stable+multiplicity all pass) but candidate mean net = −7.07 bps — still negative.
- 5m/c1 shows genuine relative separation (higher %completion → less negative outcomes, perm_p=0.010, holm_p=0.030) within a net-negative regime.
- 4h all cells underpowered (CI half-widths 42–64 bps, n=125 TRAIN events across 4 instruments).
- Audit PASS: 0 critical, 0 warnings, 0 info.

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**CHARACTERISATION_DELIVERED — zero G1-qualified dimensions.** Per design §9, this maps to FLAT: no selectivity lever (B1 /COND) opens. The phase outcome leans entirely on capture efficiency (B2 from EXP-033's 4h eligibility) and Tier C.

### Hypothesis-Agnostic Observations

- The consistent materiality failure (best bin still net-negative) is structurally consistent with Phase 007's core finding: the edge is relative (control discount), not absolute P&L, so no conditioning subset produces positive absolute net under costs+financing.
- The %completion gradient on 5m (higher completion → less negative) is real and stable — hypothesis-generating, not a rule. If a future exit redesign reduces cost drag, this gradient may become actionable.
- The hard no-selection rule is the correct discipline: a relative gradient within a net-negative regime is not a clinical path.
- 4h is simply underpowered for conditioning characterisation (~10 events/tercile/instrument) — no informative conclusion possible.
- With selectivity empty and capture efficiency (4h B2) fragile, Tier C (Stage-C branches or HYP-001) is the natural next direction per design §9.

---

## EXP-036 — /COND Selectivity Tier-B TEST (NOT EXECUTED)

**Status**: NOT_EXECUTED (precondition not met)
**Date**: 2026-06-10
**Instruments**: Not applicable — slot not consumed
**Data Views / Feature Categories**: Not applicable

### Background

EXP-036 was the Tier-B selectivity confirmation slot for `/COND` (conditioning-based clinical subset selection), reserved in the Phase 008 design (§8.2). Its precondition was G1-qualified dimensions from EXP-035 — at least one clinical dimension with positive net candidate-bin expectancy under frozen costs + financing.

### Scope

- **Instruments**: N/A (not executed)
- **Data Views / Feature Categories**: N/A
- **Features**: N/A
- **Parameter ranges**: N/A
- **Exclusions**: N/A
- **Constraints**: EXP-035 G1-qualified dimensions required as precondition.

### Results / Observations

EXP-035 found zero G1-qualified dimensions (all candidate-bin nets negative). The selectivity precondition was never met, so EXP-036 was not executed. The one-shot Tier-B slot was not consumed and is available if a future experiment identifies an actionable conditioning dimension.

### Hypothesis-Specific Conclusion

**NOT_EXECUTED.** Slot not consumed. Precondition failure preserves the slot for future use; no stage-gate impact on the Phase 008 path.

---

## EXP-037 — `/EXIT-FH` Fixed-Horizon-Exit Capture-Efficiency Variant (4h, one-shot TEST)

**Status**: ROUTE_PASS_PROVISIONAL_PENDING_PHASE_HOLM
**Date**: 2026-06-10
**Instruments**: EURUSD (provisional pass), USTEC (inconclusive), XAUUSD (margin-bound); BTCUSD excluded by break-even map
**Data Views / Feature Categories**: 4h OHLC domain; EXP-022 lifetime events (PRIMARY population); rebuilt 4h Close series for FH exit-bar prices; EXP-027 frozen regime-cluster bootstrap

### Hypothesis Tests

1. **Hypothesis**: On the 4h domain, replacing the band-target/trend-change (BTC) exit with a fixed-horizon exit at a single TRAIN-frozen horizon H\* yields positive net per-event expectancy (absolute estimand, frozen CONSERVATIVE costs + financing) that survives a one-shot TEST-stratum confirmation with Holm across the phase-level G2 family.

### Scope

- **Instruments**: EURUSD, USTEC, XAUUSD (3 cells; BTCUSD excluded by D0 break-even map).
- **Data Views / Feature Categories**: 4h OHLC domain from first-70% analysis slice; EXP-022 lifetime events (role=event, reportable_event=true, completed); rebuilt 4h Close series.
- **Features**: H\* selection via mechanical tie-break over {4,6,8,12} (stability filter + max-min worst-half criterion); pyramid policy by EXP-033 one-SE rule. TEST: one-shot regime-cluster bootstrap (1000 resamples) of FH(H\*) net per-event expectancy. R1.2 synthetic-null calibration (R=2000 Gaussian cluster-model replicates; margin = max(0, Q95 null ci_low_1s)). Within-route Holm cell-level multiplicity. FH-vs-BTC matched-control companion.
- **Parameter ranges**: H grid {4,6,8,12}; primary α=0.05; N_BOOT=1000; N_CALIB=2000; R1.1 phase-level Holm family (≤4 members: EXP-037's 3 cells + EXP-038's 1 cell); N_CROSS=2000; N_NULL_CALIB=2000; frozen cost + financing constants.
- **Exclusions**: 5m/1h domains (G1-B2 ineligible); BTCUSD; secondary FINAL exit overlay; EXP-032 (holdout release); H\* re-selection or policy re-tuning after TEST read; HYP-001; percentage-improvement-over-zero baselines.
- **Constraints**: Freeze-before-TEST barrier; TRAIN nested 70% of domain bars; real domain Close returns; frozen EXP-027 inference tail; one-shot TEST read per cell; FH exit consumes no future bar beyond the active 4h completed bar; events beyond the TRAIN/TEST boundary never seen during H\* selection.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `route_outcome: ROUTE_PASS_PROVISIONAL`, `phase_verdict_defers_to: G2-gate-review.md`, `h_star = 12`, `pyramid_policy = all_legs`, `b2_no_robust_hstar = false`, `freeze_before_test_violation = false`.
- H\* tie-break: all 4 horizons retained (N>0, N1>0, N2>0). Max-min selected H\*=12 (worst-half 41.07 bps). All_legs was the only feasible policy (n≥15 floor maintained).
- Null calibration margins: EURUSD 8.4, USTEC 30.3, XAUUSD 54.2 bps. FPR uncorrected: EURUSD 0.105, USTEC 0.104, XAUUSD 0.163.
- TEST results:
  - EURUSD: n=12, net=+40.56 bps, ci_low_1s=21.94 > margin 8.42, raw boot_p=0.001, within-route Holm p=0.003 → **route_pass_provisional**.
  - USTEC: n=11, CI [−72.6, +158.7], boot_p=0.244 → INCONCLUSIVE (predeclared power-limited).
  - XAUUSD: n=8, boot_p=0.001 but ci_low_1s 11.45 < margin 54.2 → MARGIN_BOUND (correct calibration blocks the pass).
- FH-vs-BTC companion: EURUSD-4h FH added +16.29 bps on same TEST events.
- `B2_NO_ROBUST_HSTAR` not triggered: both TRAIN halves select H\*=12, all_legs.
- Integrity: freeze-before-TEST barrier PASS (0 violations); seed robustness PASS (5 seeds, all sign-stable); N_calib DRAW consistency PASS; TEST events never seen during TRAIN.
- Audit: PASS (0 critical, 0 warnings, 0 info).

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**ROUTE_PASS_PROVISIONAL_PENDING_PHASE_HOLM.** EURUSD-4h meets the provisional pass criteria (ci_low_1s > margin AND boot_p ≤ 0.05 WITHIN route's own Holm multiplicity correction). The binding G2 verdict — phase-level Holm across the ≤4-member family (EXP-037's 3 cells + EXP-038's 1 cell) at α=0.05 — is deferred to `G2-gate-review.md`. `B2_NO_ROBUST_HSTAR` was not triggered. The FH exit recovers substantial capture efficiency (+16 bps vs BTC exit on the same TEST events).

### Hypothesis-Agnostic Observations

- The H\*=12 all_legs selection is the only feasible policy on n=4 candidate horizons with an n≥15 floor; this is a descriptive property of the TRAIN sample, not a claim of optimality.
- Both USTEC and XAUUSD TEST cells are small-n (11 and 8); the null calibration is doing honest work — screening both cells correctly despite the pass signal in XAUUSD's raw boot_p.
- The FH-vs-BTC companion gap (+16 bps on TEST events) confirms the EXP-031 exit-drag diagnosis on an independent TEST slice — capture efficiency is a genuine economic lever for this entry substrate on EURUSD-4h.
- The binding phase-level verdict in G2-gate-review.md is the appropriate governance step: single-cell provisional pass does not yet unlock the holdout.

---

## EXP-038 — EURUSD-4h A1-Cell TEST-Stratum Temporal-Stability Subsample Check (one-shot)

**Status**: A1_CELL_TEST_PASS_PROVISIONAL_PENDING_PHASE_HOLM
**Date**: 2026-06-10
**Instruments**: EURUSD (4h domain only)
**Data Views / Feature Categories**: 4h OHLC domain; EXP-022 lifetime events (PRIMARY population); EXP-034 cost/financing/inference path reused verbatim; EXP-027 frozen regime-cluster bootstrap

### Hypothesis Tests

1. **Hypothesis**: On the TEST stratum (last 30% of the analysis set by trigger time), EURUSD-4h retains positive net per-event expectancy (the same registered baseline estimand as EXP-034: BTC exit, pyramids included, frozen CONSERVATIVE cost + financing).

### Scope

- **Instruments**: EURUSD (4h domain only).
- **Data Views / Feature Categories**: 4h OHLC domain from first-70% analysis slice; EXP-022 lifetime events; EXP-034 cost overlay and financing path imported verbatim.
- **Features**: Reuse of EXP-034's exact pipeline (filters, cost overlay, financing, frozen inference tail with hash pin). Partition by trigger close time vs the 1-minute train_end_ts boundary (TEST iff trigger > boundary; ties → TRAIN). Pre-TEST R1.2 null calibration (R=2000 Gaussian cluster-model replicates) produces binding margin m = max(0, Q95 null ci_low_1s). One-shot regime-cluster bootstrap (1000 resamples) on TEST events. Provisional rule: ci_low_1s > m AND boot_p ≤ 0.05. LOCO fragility diagnostic accompanies the read.
- **Parameter ranges**: α=0.05; N_BOOT=1000; N_CALIB=2000; N_LOCO=9 (9 regime clusters); N_SEED_ROBUST=8; R1.1 phase-level Holm family (≤4 members); frozen cost + financing constants.
- **Exclusions**: 5m/1h domains; BTCUSD/USTEC/XAUUSD; EXP-037 EXIT-FH design space; second-cost overlay; secondary FINAL exit; holdout release (EXP-032 deferred); HYP-001; percentage-improvement-over-zero baselines.
- **Constraints**: EXP-034 A1_STRICT_PASS dependency; first-70% analysis slice only; CloseTime ordering for TRAIN/TEST partition; tie-break assignment of boundary-equal triggers to TRAIN; TEST stratum = last 30% of events; no event-level TRAIN/TEST overlap; real domain Close returns; frozen EXP-027 inference tail imported hash-guarded from EXP-034.

### Results / Observations

- `run_metadata.json`: `overall_status: COMPLETE`, `verdict: A1_CELL_TEST_PASS_PROVISIONAL`, `full_cell_n: 39`, `full_cell_net_mean: 11.77`, `reproduction_vs_exp034_max_abs_diff: 0.0`, `test_stratum_n: 12`, `test_stratum_net_mean: 24.27`.
- Full-cell reproduction: full-cell net mean 11.77 bps reproduces EXP-034 to 0.0 bps. Bootstrap CI replay with EXP-034's own seed reproduces to ≤ 8.9e-16.
- Null calibration margin: 3.78 bps (FPR uncorrected 0.0975 at n=12, 9 clusters).
- TEST: n=12 (3 bull, 9 bear), net=+24.27 bps, ci_low_1s=15.43 > margin 3.78, raw boot_p=0.001 → **provisional pass**.
- LOCO: all 9 regime-cluster drops above margin (min ci_low_1s 13.25 bps). The pass is not driven by a single cluster.
- Seed robustness (8 seeds): ci_low_1s range [14.59, 15.66], all sign-stable positive.
- TRAIN net point: +6.22 > 0 bps → nomination precondition met.
- Integrity: frozen EXP-027 inference hash matches EXP-034; holdout fence respected; determinism PASS; seed robustness PASS.
- Audit: PASS (0 critical, 0 warnings, 0 info).

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**A1_CELL_TEST_PASS_PROVISIONAL_PENDING_PHASE_HOLM.** EURUSD-4h retains positive TEST-stratum net expectancy. Per R1.7, this is a dependent subsample check: TEST events contributed to both D0 cell selection and the EXP-034 A1 pass estimate, so this is NOT an independent out-of-sample confirmation. The LOCO and seed-robustness diagnostics confirm the pass is not a sampling artifact. The binding G2 verdict — phase-level Holm across ≤4 cells — is deferred to `G2-gate-review.md`.

### Hypothesis-Agnostic Observations

- The TEST effect is *larger* than the full-cell effect (+24.27 vs +11.77 bps), meaning later-period events (late 2024–early 2025) had larger price moves or more favorable exit outcomes. This is consistent with temporal non-stationarity but does not invalidate the test — the one-shot TEST read is on the distribution as realized.
- LOCO robustness (min ci_low_1s 13.25 across 9 cluster drops, all above the 3.78 bps margin) is strong evidence against single-regime-driven fragility.
- The R1.2 null calibration margin (3.78 bps) is modest compared to the observed TEST signal (15.43 bps ci_low_1s), suggesting the TEST read is well-powered for this cell despite small n=12 — an honest outcome, not power-bound.
- Per R1.7 and the design §8.4 caveat, this TEST check is NOT an independent replication like EXP-037; it is a subsample robustness guard. Both EXP-037 and EXP-038 enter the phase-level Holm family for the G2 verdict.


## EXP-032 — One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs)

**Status**: INCONCLUSIVE (binding `HOLDOUT_INCONCLUSIVE` — **holdout shot SPENT**)
**Date**: 2026-06-10
**Instruments**: EURUSD (4h domain only)
**Data Views / Feature Categories**: full EURUSD 1-minute series (analysis + the programme's single sanctioned holdout read, Phase 009 design §5); EXP-031-identical 4h rebuild; frozen EXP-020/022 AVWAP event stream; registry `CF-AVWAP-001/HOLDOUT-B`

### Hypothesis Tests

1. **Hypothesis**: On the global holdout stratum (final 30%, never previously read), the Package-B cell — EURUSD-4h AVWAP bounce events, FH exit at H\*=12 domain bars, all_legs pyramid policy, frozen CONSERVATIVE RT 3.0 bps + financing 0.6 bps/day (adverse-side, fractional calendar days) — has positive net per-event expectancy: `ci_low_1s > m_cell` AND one-sided bootstrap p ≤ 0.05 (family of 1, no Holm; the shot is spent on any outcome).

### Scope

- **Instruments**: EURUSD only; BTCUSD/USTEC/XAUUSD holdout rows never loaded (seal assertion PASS — one data file opened).
- **Data Views / Feature Categories**: full-series 4h rebuild; frozen sequential event generator over the full series; analysis-stratum reconciliation as lineage proof.
- **Features**: per-event `net_12 = fh_bps(12) − 3.0 − 0.6 × elapsed_calendar_days`; real-OHLC returns only.
- **Parameter ranges**: none — every parameter inherited frozen (EXP-037 `frozen_selection.json` hash-pinned `2bbbf65b…770b0fea`; EXP-027 tail `e50873d12a9f68d9`); zero selection inside EXP-032.
- **Exclusions**: all other instruments/domains/horizons/cost variants; conditioning; per-bar suite; any second holdout read; BTC exit as a binding quantity (descriptive companion only).
- **Constraints**: two-phase freeze-before-outcome (H1 entry-attribute manifest, content-hashed, margin embedded → H2 one-shot inference, separate invocation, R1.6 recovery semantics); no-second-read guard keyed on `holdout_verdict.csv`; mechanical verdict; no amendment path after scope freeze.

### Results / Observations

- Binding cell (n = 27 holdout events; expected ≈15–18, deviation disclosure-only): net **+20.5969 bps**, two-sided 95% CI **[−0.3888, +42.1531]**, one-sided 95% lower bound **+2.7086 bps**, one-sided boot_p **0.0290**, margin **m_cell = 4.3189 bps** → `ci_low_1s ≤ m_cell` → **HOLDOUT_INCONCLUSIVE**; descriptive **INCONCLUSIVE_SPANS_ZERO**.
- Pre-outcome null calibration at the holdout structure (16 clusters): uncorrected dual-rule null FPR **0.0715**; with margin **0.050**; σ_b = 57.85, σ_w = 29.98 bps (from the 39 disclosed analysis nets).
- Decomposition (non-binding): gross FH +25.2635 − RT 3.00 − financing 1.6667 = net +20.5969 bps; truncated share 1/27.
- BTC-exit companion (non-binding, same 27 events, 27/27 completed): net **+2.3492 bps** vs +20.60 for FH(12).
- Context: analysis-era mean +32.87 bps (n=39) vs holdout +20.60 (n=27); 13 positive / 14 negative events, range [−98.2, +133.7] bps.
- Integrity: all 7 reconciliation checks PASS (EXP-022 keys+flags identical; 39-event manifest reproduced; 27/12 partition exact; EXP-037 TEST anchor reproduced to 3.6e-7 bps; 4h prefix-equality; seal); manifest hash-verified; determinism replay drift 0.0. Audit PASS (0 critical, 0 warnings).

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE (HOLDOUT_INCONCLUSIVE — shot SPENT).** The predeclared dual rule failed on the margin condition (2.71 ≤ 4.32 bps) while the p-gate passed (0.029 ≤ 0.05) and the two-sided CI spans zero. Per the locked Phase 009 rules: no second holdout read ever for Package B (or A); the EXP-037 TEST evidence stands but is permanently non-upgradable; routing follows the REFUTED path for resources (Tier C, Phase 008 design §9). Mandatory R1 disclosures: the estimand conditions on ex-post reportability (filter bound nothing here: 27 pre = 27 post; F04), and the calibration margin transports analysis-era variance onto the holdout layout (F05 — load-bearing only for CONFIRMED, which did not occur).

### Hypothesis-Agnostic Observations

- The calibrated margin was decisive: an uncalibrated `ci_low_1s > 0 AND p ≤ 0.05` rule would have "confirmed" at a measured null FPR of 0.0715 — the R1.2-analog machinery demonstrably prevented an over-claim on the programme's most expensive read.
- Out-of-sample attenuation without reversal: holdout +20.60 vs analysis-era +32.87 and TEST +40.56 bps at the identical estimand — consistent with winner's-curse shrinkage of a selected cell; not separable from a lucky zero-effect draw at this power.
- Third consecutive consistent reading that the BTC (trend-change) exit drags long-horizon capture on this population (+2.35 vs +20.60 bps on identical events), after EXP-031/033/037 — exit design remains the dominant P&L lever on this substrate.
- The holdout stratum yielded 27 reportable events vs the ≈15–18 expectation, and the limiting factor was per-event dispersion (~60–70 bps) rather than sample count.

---

## EXP-039 — `/EXIT-X` TRAIN-Only Exit Screen (DIAG-006)

**Status**: MEASUREMENT_COMPLETE — FLAT
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (surviving: EURUSD, USTEC, XAUUSD)
**Data Views / Feature Categories**: 1-minute time bars resampled to 1h and 4h OHLC domains; Heiken Ashi candles (for E1/E2 triggers); AVWAP bounce-entry substrate (MA 20/50, TickVolume^0.75, MAD band 1.0)

### Hypothesis Tests

1. **Exploratory question (diagnostic screen, DIAG-006, 0 slots)**: On the unchanged AVWAP bounce-entry substrate, does any registered candidate exit rule (E1–E5, with E3/E5 parameter grids) deliver TRAIN per-event net expectancy under frozen CONSERVATIVE costs + Phase 008 financing that is positive and exceeds both reference exits (4h: R-FH(12) and R-BTC; 1h: R-BTC), stably, on the 4h (primary) or 1h (secondary) domain — qualifying mechanically (§8.1 rule) for the provisional EXP-041 one-shot TEST confirmation?

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (descriptive per-instrument tables for all four; binding screen statistics use surviving instruments EURUSD, USTEC, XAUUSD per EXP-030/D0 break-even map). BTCUSD excluded from binding statistics.
- **Data Views / Feature Categories**: 1h and 4h OHLC domains from first-70% TRAIN slice of the analysis set; Heiken Ashi candles for E1/E2 trigger conditions; AVWAP bounce-entry substrate unchanged from EXP-028/030/037.
- **Candidate exits (registered; frozen at scope freeze)**:
  - **E1** — HA Harami size exhaustion (no parameters)
  - **E2** — HA trailing reference (no parameters)
  - **E3** — Last-X high/low trailing, X ∈ {3, 5, 8}
  - **E4** — Adverse-band stop (no parameters)
  - **E5** — Target-conditional time-stop, H_ts ∈ {8, 12, 24}
- **Reference exits (fixed)**: R-BTC (band-target/trend-change); R-FH = FH(H\*=12, all_legs) on 4h only (EXP-037 freeze, hash-pinned). 1h is FH-ineligible per EXP-033.
- **Parameter ranges**: Domains {1h, 4h}; exit rules as above with E3/E5 parameter grids; TRAIN nested 70% of domain bars.
- **Exclusions**: TEST/holdout reads; any binding inference or verdict on market edge (that is EXP-041); stop-style/intrabar triggers; pyramid-policy variation; cost/financing iteration; entry-signal changes; 5m domain; new-universe data; any post-hoc addition of exit rules or parameter points.
- **Constraints**: TRAIN-only (first 70% of analysis set); boundary containment per candidate (events unresolved at `train_end_ts` excluded); intersection populations for all reference-gap comparisons; real-price outcome discipline (HA trigger-only; fills on real domain Close); per-event net after frozen CONSERVATIVE costs + Phase 008 financing; power statement persisted before qualification.

### Results / Observations

- **Screen outcome**: **FLAT** — 0 qualifiers across 10 evaluated cells (5 exits × 2 domains). Qualifying set empty. EXP-041 slot unused.

- **4h domain (primary, n=86 intersection)**:
  - R-FH(12) reference pooled net = +37.3 bps (bootstrap SE 17.9 bps). R-BTC = +7.2 bps.
  - Best candidate: E2 (HA trailing) at +31.9 bps, gap −5.4 bps vs R-FH(12). Passes per-instrument positivity and split-half stability but fails criterion (ii) — negative gap.
  - E3(3): highest raw pooled net (+39.9 bps) but selected point E3(8) yields +26.9 bps, fails per-instrument positivity (XAUUSD −1.7 bps).
  - E3(8) split-half gap sign flips (h1 +24.9 bps, h2 −19.7 bps) — fails stability.
  - E5(8) at +11.3 bps passes per-instrument positivity but gaps R-FH(12) by −26.0 bps.
  - E1, E4, E5(12), E5(24): all below R-FH(12).
  - All 4h events resolve within boundary (0 unresolved).

- **1h domain (secondary, n=443 intersection)**:
  - R-BTC pooled net = −2.5 bps. All candidates net negative (−6.1 to −0.9 bps).
  - Best candidate: E2 at −1.5 bps. No candidate passes per-instrument positivity.
  - All 1h candidates fail split-half stability (sign changes between halves).

- **Power and fragility**:
  - 4 of 10 evaluated cells flagged gap_fragile (|gap| < bootstrap SE): 4h/E2, 4h/E3(8), 1h/E2, 1h/E3(8).
  - Bootstrap SEs: 7.2–30.0 bps (4h), 1.5–5.5 bps (1h).

- **Determinism replay**: PASS (max drift = 0.0).

- **Reconciliation**: R-BTC per-event vs EXP-022: max diff 0.0 bps. R-FH(12) per-instrument vs EXP-033: max diff 2.1e-14 bps.

- **Qualification table**: qualification_table.csv confirms 0/10 cells qualify.

- **Power statement**: power_statement.csv confirms 4/10 cells fragile.

- **EURUSD disclosure**: EURUSD TEST-cap share ranges −0.05 to 0.52 across 4h candidates. Pooled ex-EURUSD nets generally higher (e.g. E2 from +31.9 to +37.1 bps).

- **Audit**: PASS (0 critical, 1 warning: determinism replay checks bootstrap drift rather than full CSV byte-identity).

### Hypothesis-Specific Conclusion

**FLAT** (diagnostic screen outcome). No (exit, domain) cell satisfies the §8.1 mechanical qualification rule. The capture-efficiency lever beyond R-FH(12) is exhausted on the AVWAP bounce-entry substrate across the tested exit families (HA-based, trailing, Last-X, adverse band, target-conditional time-stop). The EXP-041 provisional one-shot TEST slot remains unused. Per Phase 010 design §9, Track A is EXIT_FLAT.

### Hypothesis-Agnostic Observations

- The 4h R-FH(12) benchmark (+37.3 bps) is a high bar — the scope's predeclared expectation ("beating R-FH(12)... is a high bar — most candidates failing it is the honest prior") was confirmed.
- E2 HA trailing (no parameters) was the closest candidate on 4h at +31.9 bps, −5.4 bps behind R-FH(12) — approximately 0.5 SE, consistent with power-limited resolving not mechanism-driven gap.
- The 1h domain is structurally non-viable on this substrate: even the reference exit (R-BTC) is net-negative, and no candidate escapes this. This is consistent with EXP-033's finding that 1h FH grid max ≤ 0.
- TRAIN-only selection with ~86 events per 4h cell is fundamentally power-limited for exit comparison at SEs of 7–30 bps — the split-half and max-min ranking correctly identified fragile cells but could not overcome the underlying event count.
- The FLAT outcome means the operator should review design §9 EXIT_FLAT consequences and consider Stage-C family review before opening new exit work on this substrate.
- EURUSD TEST-capped disclosure correctly contextualises that 4h E2's qualification evidence (had it occurred) would depend on USTEC and XAUUSD replication.

---

## EXP-040 — HYP-001 Direct AVWAP Line Support/Resistance Test

**Status**: INCONCLUSIVE
**Date**: 2026-06-10
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 1h and 4h OHLC domains via `xen.bar_aggregator`; EXP-020 AVWAP state machine (frozen: MA 20/50 detector, TickVolume^0.75 weight, MAD band multiplier 1.0); episode-based approach detection

### Hypothesis Tests

1. **Hypothesis (HYP-001)**: Price approaching the anchored VWAP line reacts at the line as support/resistance beyond what matched non-AVWAP price levels show — `P(bounce | approach to AVWAP) > P(bounce | approach to matched control level)` on the 1h and/or 4h domain.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all four; per-instrument descriptive, binding inference on pooled per-domain contrast).
- **Data Views / Feature Categories**: 1h and 4h OHLC domain bars from the first-70% analysis slice; EXP-020 AVWAP state machine supplying live line and MAD band-width; no chart-type views.
- **Features**: Approach-episode detection via sequential streaming pass (ε = 0.25 × MAD band-width, hysteresis 2ε, episode cap 24 domain bars); matched non-AVWAP control levels (horizontal price snapshots at random offsets ±[1.5, 3.5] band-width units from contemporaneous AVWAP, lifetime 100 bars); outcome classification (bounce, pass-through, unresolved); covariate matching on (entry direction, trailing-volatility tercile, approach-speed tercile); rate-difference estimand Δ = P(bounce | AVWAP) − P(bounce | control) in percentage points.
- **Parameter ranges**: Domains {1h, 4h}; ε = 0.25; hysteresis = 2ε; episode cap = 24 bars; control δ ~ U(±[1.5, 3.5]) BW; control spacing = 25 bars; control lifetime = 100 bars; N_perm = 2000; N_boot = 1000; Holm α = 0.05 on 2 pooled domain contrasts; materiality threshold = 2 pp; reportability floor = 100 episodes/arm.
- **Exclusions**: Any cost/financing layer; any tradability or strategy claim; the EXP-025 event-bar penetration metric (explicitly inadmissible per Phase 007 design §8); 5m; TRAIN/TEST selection; parameter sweeps over ε/hysteresis/cap; holdout.
- **Constraints**: Analysis set (first 70%) only; identical sequential-pass episode detector shared verbatim between both arms (any definitional artifact cancels in Δ); power statement persisted before any contrast read; episodes (approaches) as denominator — never bars; hysteresis as duplicate-source rule; unresolved episodes excluded from rates but counted and disclosed; Δ in percentage points per the zero-baseline rule; determinism replay.

### Results / Observations

**Binding contrasts (static control):**

| Domain | Δ (pp) | 95% CI | Holm p | n AVWAP | n Control | n Strata | Verdict |
|--------|--------|--------|--------|---------|-----------|----------|---------|
| 1h | +1.55 | [−4.52, +8.43] | 0.585 | 1,594 | 339 | 70 | INCONCLUSIVE_SPANS_ZERO |
| 4h | −24.67 | [−44.63, −4.40] | 0.980 | 50 | 22 | 7 | BELOW_FLOOR_NO_VERDICT |

**Moving-copy control arm (descriptive, design §11/8):**

| Domain | Δ_m (pp) | 95% CI | n AVWAP | n moving | Note |
|--------|----------|--------|---------|----------|------|
| 1h | +3.41 | [−1.23, +8.35] | 1,647 | 522 | Larger than static Δ; kinematic confound does not explain premium |
| 4h | +0.09 | [−12.68, +11.95] | 166 | 103 | Essentially zero; negative static Δ was entirely kinematic artifact |

- **Overall HYP-001 verdict**: INCONCLUSIVE — neither FOR nor REFUTED reached on either domain.
- Per-instrument 1h (descriptive, non-binding): BTCUSD +5.4 [−4.9, +16.8], EURUSD −5.4 [−17.5, +6.1], USTEC +2.8 [−11.1, +15.8], XAUUSD +3.0 [−9.5, +15.6] pp — all CIs span zero. 4h cells below floor.
- Censoring sensitivity 1h: extreme imputations bracket Δ = +1.55 in [−2.47, +3.04] pp. Unresolved imbalance (95 AVWAP / 59 control).
- Split-half 1h (non-binding): h1 = −2.26 (n=967), h2 = +1.02 (n=966) — opposite signs consistent with noise around zero.
- Power statement: unclustered MDE ≈ 4.9 pp (1h, optimistic under clustering). Immateriality verdict structurally unreachable at realized n.
- Determinism replay: PASS (max drift = 0.0).
- Audit: PASS (0 critical, 0 warnings, 2 info — permutation scoped at instrument level rather than within matched strata, minor/conservative; no programmatic write-ordering assertion for power statement).

### Hypothesis-Specific Conclusion

**INCONCLUSIVE.** Neither domain met the FOR criteria (Δ > 0, CI_low > 0, Holm p ≤ 0.05) nor the AGAINST criteria (CI ≤ 0, or CI_high < +2 pp with CI_low ≤ 0). The 1h CI symmetrically straddles zero (Δ = +1.55 pp). The 4h result is below the reportability floor (n=50/22 < 100/arm). Per the scope, an INCONCLUSIVE verdict means HYP-001 remains open — no re-parameterization within this scope is permitted. Per design §8.3, the result is a permanent mechanism record and a Phase 011 / family-review input with no gate consequence.

### Hypothesis-Agnostic Observations

- The small positive 1h Δ (+1.55 pp), if real, could reflect relative momentum around pivots (price approaches the line during a move, then reverses as the move exhausts, coincidentally near the line) rather than the line itself exerting a barrier effect — the core ambiguity the experiment was designed to resolve.
- The 4h negative Δ (−24.67 pp) is consistent with the control arm's expected upward bias from the unmatched price-stretch regime (caveat 5: control approaches occur 1.5–3.5 BW from VWAP, a location AVWAP approaches never occupy; generic mean reversion inflates control bounce rates). The floor correctly prevents a verdict.
- The unmatched price-stretch regime bias direction is against HYP-001 (conservative for a FOR read), but the 1h CI cannot exclude zero, so this conservatism does not change the inconclusive outcome.
- The moving-vs-static kinematic confound (caveat 4) was resolved in-scope via the shifted-moving-copy secondary arm (design §11/8). On 1h Δ_m = +3.41 pp — larger than the static Δ, meaning the kinematic confound does not explain the premium. On 4h Δ_m = +0.09 pp — essentially zero, confirming the negative static Δ was a kinematic artifact.
- HYP-001 remains open. A REFUTED (NO) would close the line-S/R mechanistic story and reframe the edge as relative momentum around pivots; that closure was not achieved.

## EXP-042 — Phase 011 Track A0 Band-Selection Scan

**Status**: FAILED
**Date**: 2026-06-11
**Instruments**: full 17-instrument Phase-011 universe
**Data Views / Feature Categories**: 1h/2h/4h clock-aligned domain bars; arm-at-adverse-band AVWAP entry-band scan on TRAIN only; 0 TEST reads

> **SET ASIDE — FRAMING_ERROR (2026-06-11).** Post-execution review
> (`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`) found the
> arm-at-adverse-band entry rule applied the band multiplier as an **entry
> filter**, when across Phases 004–010 it was always an **exit parameter**
> (favorable/adverse targets frozen at trigger; registry `/BAND` is an
> exit/structural branch). EXP-042 measured a filtered deep-pullback
> subpopulation; the band=1.0 "selection" and the DEGENERATE_FLOOR verdict
> are artifacts of event starvation under the wrong framing. No decision is
> based on these results. **Track A0 is removed from Phase 011**; the band
> multiplier moves entirely to Track B exit training (design §5.4 Family 2,
> where it was already correctly scoped). Phase 011 entries revert to the
> frozen baseline arm/trigger at the AVWAP line, so the §7.4 baseline event
> rates govern power, not the EXP-042 power statement. Code, results, and
> run_metadata retained as a negative-process record; 0 slots, 0 TEST reads.
> The summary below records the non-governing measurements from the set-aside
> run; it is retained to explain why the result carries zero weight.

### Scope / Disposition

EXP-042 scanned the AVWAP arm-at-adverse-band entry rule over b ∈ {1.0, 1.5,
2.0, 2.5, 3.0} across 17 instruments × {1h, 2h, 4h} on TRAIN only. Post-run
review found the scan had no valid Phase 011 decision object: the multiplier
was historically an exit-target parameter, not an entry parameter. The run is
therefore a retained negative-process record only. The original scope,
analysis plan, code, raw outputs, audit, and governance files remain under
`python/experiments/EXP-042/` for traceability, but no downstream scope may use
the selected band, pending adjudication path, or EXP-042 power statement.

### Results / Observations

- **Band 1.0 selected** — median rank 2.0; every wider band 5.0. Floor-imputed cell fractions: 0.41 / 0.65 / 0.88 / 0.98 / 1.00 across the grid.
- **DEGENERATE_FLOOR fired** (>50% imputation at every band ≥ 1.5) under the original scope; this adjudication path is now moot because the whole Track A0 object was removed.
- Wider bands lost on **event starvation, not measured gross** — where populated, wider-band per-event gross is often higher (the conjectured deeper-pullback effect), but event supply collapses (e.g., 100% of cells floored at b=3.0). The "best per-event economics across bands" question is unpowered and stays open (F02 proxy disclosure).
- **Power statement (b=1.0):** 1h 17/17 cells ≥ 30 TRAIN events (median 69; projected TEST ~30); 2h 13/17 (median 37; ~16); **4h 0/17** (median 19; ~8). These counts describe the filtered EXP-042 population only and do not govern Phase 011 power planning.
- Audit PASS: independent rule re-implementation 0 mismatches; end-to-end cell regeneration exact; denominators monotone 255/255; determinism replay identical; F01-fixed loader never lets TEST/holdout rows enter the scan engine. Substrate parameterization regression-tested (`python/tests/test_avwap_band_param.py`; 20/20 project tests).

### Conclusion

**MEASUREMENT_COMPLETE — FRAMING_ERROR.**

The implementation and original rule execution were audited as correct, but
the measurement framed an exit parameter as an entry filter. EXP-042 therefore
does not select or freeze any band, does not reset Phase 011 power
expectations, and does not require DEGENERATE_FLOOR adjudication. Phase 011
moves on with the frozen baseline AVWAP-line entry; Track A measures readiness
for that baseline event population, and Track B trains the MAD-band multiplier
only as an exit parameter.

## EXP-043 — Phase 011 Track A Substrate Readiness (Baseline Entry, 51 Cells)

**Status**: SUPPORTED
**Date**: 2026-06-11
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD + GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30 (truncated), JP225 — full 17-instrument Phase-011 universe
**Data Views / Feature Categories**: 1-minute time bars aggregated to 1h/2h/4h clock-aligned domain bars (`min_coverage=0.90`; first-ever 2h construction); frozen baseline AVWAP bounce events (`xen.avwap.generate_avwap_events` defaults — the Phases 004–010 entry, bit-for-bit). TRAIN stratum only (R1.3 1-minute-row boundary, F01 file-order loading). No chart-type views; no return metric of any kind.

### Hypothesis Tests

1. **Exploratory readiness question** (no market-edge claim): the frozen baseline AVWAP event substrate is deterministic, invariant-clean, and constructible on all 51 instrument×domain cells, and its measured TRAIN event rates quantify per-cell power for Track B exit training. Feeds gate G1 (Phase 011 design §8.2); replaces the non-transferable EXP-042 power statement.

### Scope

- **Instruments**: the 17-instrument Phase-011 universe (DE30 carried with the P8 truncation disclosure on every output row).
- **Data Views / Feature Categories**: 1h/2h/4h domain bars from TRAIN-only 1-minute slices; baseline events with all parameters frozen (MA 20/50, exponent 0.75, MAD band multiplier 1.0 as exit-context columns only, EXP-020 bounce definition).
- **Features**: per-cell construction-integrity predicates (OHLC consistency, strict chronology, bucket-membership clock alignment, coverage bounds, TRAIN fence, 2h dropped-window fraction); 7-family event/regime invariant battery; full second-regeneration determinism comparison; TRAIN event counts, events per 1,000 TRAIN domain bars, heuristic TEST projections.
- **Parameter ranges**: none varied (readiness, not selection). Frozen pre-data-contact thresholds (Revision 1, operator-ratified): 2h dropped fraction <10% clean / 10–25% flagged disclosure (READY-eligible) / >25% NOT_READY; systematic-failure halt iff non-determinism on any cell or the same invariant violated on ≥3 instruments; 2h/1h bar-count ratio disclosure-only band [0.45, 0.55].
- **Exclusions**: TEST and holdout never read (projections = `TRAIN × 30/70`, labeled uniformity heuristic, no TEST contact including row counts); no returns/expectancy/edge; no exit training or selection; no band-multiplier variation; no `min_coverage`/MA tuning; no cross-instrument pooling.
- **Constraints**: 0 statistical tests / 3 plots / 0 new modules (budget ≤1); defaults-only generator call anchored by `python/tests/test_avwap_band_param.py`.

### Results / Observations

- **Cell verdicts: 50 READY / 1 NOT_READY / 0 CONSTRUCTED_EMPTY.** Zero invariant violations across all events in all 51 cells; zero determinism failures (in-run second pass frame-identical; audit's independent third pass reproduces two cells exactly); `substrate_alert: false`.
- **JP225-2h NOT_READY** on the frozen dropped-fraction gate only: 0.2566 > 0.25 (96 events, 89 regimes, all invariants clean and recorded — a session-structure/coverage outcome, not a generator defect). Excluded from Track B per design §8.2.
- **Event rates scale-stable**: 16.5–34.0 events per 1,000 TRAIN domain bars in every cell, every domain. Realized TRAIN counts: 1h 151–273, 2h 86–143, 4h 32–86; **0 cells below the 30-TRAIN-event floor** (min 32, JP225-4h); 11/17 4h cells have only 32–55 events; heuristic TEST projections put most 4h cells below 30 projected events.
- **2h construction quality**: forex dropped fractions 0.02–0.05; flagged band (10–25%, READY-eligible) US2000 0.103, DE30 0.163, US500 0.196; 2h/1h bar ratio 0.475–0.498 everywhere (never flagged). Un-gated 4h index retention reaches 0.20–0.30 (JP225 0.297, US500 0.286) — above the old-universe 4h range 0.025–0.131 (audit Info-1 disclosure).
- **Anchors**: BTCUSD/EURUSD/USTEC/XAUUSD analysis-row boundaries reproduce VAL-001/EXP-001 exactly (1,088,960 / 872,242 / 830,541 / 830,671). Audit PASS (0 Critical / 0 Warning / 4 Info): two cells independently re-implemented and reproduced to the last digit; all 51 verdicts re-derived with 0 mismatches; all rate/projection arithmetic exact.

### Hypothesis-Specific Conclusion

**READINESS_DELIVERED** (predeclared criterion: the 51-cell READY/NOT_READY map plus the event-rate/power table is produced). Substrate-level Evidence AGAINST not triggered. The Track B substrate is certified on 50 cells; this power table supersedes the design §7.4 planning figures (1h realized 151–273 vs "~350–400" planned; 4h 32–86 vs "~90"). G1 completion still requires the EXP-027-analog calibration and EXP-029-analog parity items.

### Hypothesis-Agnostic Observations

- The bounce definition yields near-constant per-bar event density across timeframes (16.5–34 per 1,000 bars), consistent with the scale-free MA(20,50) regime detector — 2h delivers its intended power middle ground (~2× the 4h counts).
- Clock-aligned windowing at `min_coverage=0.90` interacts with index session structure progressively: retention loss grows with window size (clean at 1h, flagged at 2h, 0.20–0.30 at 4h for indices), so partial-window High/Low understatement is a standing caveat for index slow domains.

## EXP-044 — Phase 011 Track A Per-Cell Event-Level Inference Calibration (EXP-027-Analog)

**Status**: SUPPORTED
**Date**: 2026-06-11
**Instruments**: full 17-instrument Phase-011 universe (BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225)
**Data Views / Feature Categories**: 1h/2h/4h clock-aligned domain bars from F01 TRAIN-only 1-minute rows; frozen baseline AVWAP regime/event scaffolding used for placement only (real event outcomes never computed or read); synthetic placebo + planted-edge substrates. Track A methodology experiment — 0 candidate slots, 0 TEST reads (registered 2026-06-11, multiplicity registry).

### Hypothesis Tests

1. **Hypothesis**: the frozen EXP-027 event-level inference (per-event direction-signed matched-control excess, regime-cluster bootstrap CI, stratified paired sign-permutation p, Evidence-FOR rule), applied standalone per instrument×domain cell (no cross-instrument pooling, no Holm), exhibits controlled per-cell FPR ≤ α₀ = 0.05 under two structurally different known-null generators and a finite per-cell event-level MDE (TPR ≥ 0.80) at each of the 50 READY cells' realized TRAIN event counts (1h 151–273, 2h 86–143, 4h 32–86). COVERED cells satisfy G1 leg (ii); NOT_COVERED cells are excluded from Track B with record.

### Scope

- **Instruments**: the 50 READY cells from EXP-043 `readiness_map.csv` (JP225-2h excluded, NOT_READY under G1 leg (i)).
- **Data Views / Feature Categories**: real TRAIN domain bars; EXP-043-certified scaffolding regenerated bit-for-bit (per-cell event-count consistency gate, hard-fail); source-identity binding to the EXP-043 boundary record (file name, row counts, TRAIN-end timestamp).
- **Features**: N1 placebo-on-real and N2 block-permuted nulls at each cell's exact realized bull/bear counts (largest-remainder allocation, pool-restricted pyramids, 100% exact placement); planted edges g ∈ {1, 2, 4, 8, 16, 32, 64, 128} bps; frozen single-cell decision rule (effect > 0 ∧ CI_low > 0 ∧ p ≤ α); H_cal = 8 bars; 500 draws per point, 1000 bootstrap / 1000 permutation resamples; Wilson precision gates (FPR half-width ≤ 0.03, TPR ≤ 0.05); 90% draw-completion floor.
- **Parameter ranges**: none tuned — all method constants frozen from EXP-027; α grid {0.10, 0.05, 0.01} with primary α₀ = 0.05.
- **Exclusions**: real AVWAP event outcomes (anti-overfitting fence — trigger locations used only as exclusions, outcomes NaN-masked); TEST and final-30% holdout never loaded; cross-cell aggregation; per-bar suite/floor; Holm in-experiment; grid extension after results.
- **Constraints**: 4/4 tests, 5/5 plots, 1/1 new module; deterministic via `seed_for`; two-cell full determinism replay (BTCUSD-1h, JP225-4h).

### Results / Observations

- **Coverage: 37 COVERED / 13 NOT_COVERED / 0 CALIBRATION_UNDERPOWERED** (by domain: 1h 14/3, 2h 12/4, 4h 11/6). 100% draw completion; max FPR Wilson half-width 0.0225 (≤ 0.03); max TPR half-width 0.0436 (≤ 0.05); determinism replay frame-identical; placement exact in 100% of 250,000 draw rows.
- **FPR at α₀ = 0.05**: mean 0.041 (N1) / 0.031 (N2). 12 cells NOT_COVERED on FPR point excess — 11 marginal (0.052–0.062, Wilson lower bound < α₀: AUDUSD-1h/4h, BTCUSD-1h, USTEC-1h/2h, GBPJPY-2h, XAUUSD-2h, EURUSD-4h, EURJPY-4h, NZDUSD-4h, USDJPY-4h), 1 material (USDCAD-2h, N1 = 0.070, Wilson lower bound > α₀). BTCUSD-4h NOT_COVERED on no finite MDE (TPR at 128 bps = 0.64).
- **MDE among COVERED cells**: 1h median 16 bps (range 8–32, 151–266 events); 2h median 32 bps (16–128, 86–143 events); 4h median 64 bps (32–128, 32–86 events). Four cells at the 128 bps grid endpoint. TPR curves monotone within Monte-Carlo noise.
- **Substrate check**: two-null Wilson disagreement in 2 instruments (AUDUSD, USDCAD; both N1 > N2), below the ≥3-instrument trigger; no domain-wide FPR excess. Estimated block length = 1 in every cell. Secondary α = 0.01 anti-conservative (mean FPR 0.0225).
- **Audit PASS** (0 Critical / 1 latent Warning / 4 Info): all 100 cell×generator FPRs, all 50 classifications, and the substrate triggers independently recomputed from `draw_verdicts.parquet` with 0 mismatches; Wilson intervals reproduced to full precision.

### Hypothesis-Specific Conclusion

**CALIBRATION_DELIVERED (Evidence FOR, predeclared deliverable criterion)**: every cell classified at budgeted precision, MDE table recorded, determinism PASS; METHOD_NOT_TRANSFERABLE and INCONCLUSIVE triggers not met. G1 leg (ii) is satisfied for the 37 COVERED cells (the Track B grid); the 13 NOT_COVERED cells are excluded with record.

### Hypothesis-Agnostic Observations

- Pooled-domain FPR control (EXP-027) does not automatically transfer to single cells: three high-count old-universe 1h cells (AUDUSD, BTCUSD, USTEC) show marginal per-cell FPR excess despite 192–273 events.
- The EXP-027 pooled-scale two-null agreement does not replicate per cell: N1 (placebo-on-real) is systematically anti-conservative relative to N2 (block-permuted, effectively i.i.d. at block length 1), consistent with within-regime real-return dependence rather than event sparsity; the predeclared both-nulls rule makes the stricter N1 binding.
- Per-cell MDE scales smoothly with event count (no cliff down to 32 events); thin 4h cells certify only large effects (32–128 bps), and BTCUSD carries the largest MDE at every domain — a volatility effect, not a method defect.
- Calibration is at H_cal = 8 only and N2's dependence stress is weak (block length 1 everywhere); a targeted second-horizon FPR check is the predeclared follow-up if Track D selects exits far from H≈8.

## EXP-045 — Phase 011 Track B Per-Cell Exit Training (37-Cell COVERED Grid)

**Status**: TRAINING_DELIVERED
**Date**: 2026-06-11
**Instruments**: the 37 COVERED cells from EXP-044 `coverage_map.csv` (16 instruments across {1h, 2h, 4h}; DE30 rows carry the D0 P8 truncated-history disclosure verbatim)
**Data Views / Feature Categories**: F01 TRAIN-only 1-minute rows → 1h/2h/4h clock-aligned domain bars (P7) → frozen baseline AVWAP bounce events (`generate_avwap_events` defaults); per-event direction-signed net log-bps under the frozen D0 P2 CONSERVATIVE cost model (RT + per-calendar-day financing, ns-exact timestamps). Track B selection/measurement — 0 slots, 0 TEST reads.

### Hypothesis Tests

1. **Exploratory selection question** (no market-edge hypothesis): for each COVERED cell, is either G0-frozen exit family — FH(H) ∈ {2,3,4,6,8,11,16,23} or MAD-band-target(m) ∈ {0.5,0.7,1.0,1.4,2.0,2.8,4.0,5.7} (P6) — tunable on TRAIN under the n-neighbour stability plane (k = 1, interior-only; endpoint-dominance, 1×SE separation, chronological split-half agreement), and does the cell clear the P4 membership floor S(θ\*) ≥ +1×SE? G2 readout: P5 composition (≥5 member cells over ≥3 instruments) authorizing Track C.

### Scope

- **Cells**: the 37 COVERED cells read from EXP-044 at run time (13 NOT_COVERED + JP225-2h structurally unreachable); EXP-043 source-identity binding and per-cell event-count consistency gates.
- **Exit semantics (predeclared)**: completed-close fills; MAD favorable target frozen at trigger (`avwap ± m×spread`), exit at first close at/beyond target or first opposite MA(20,50) confirmation strictly after the trigger, no stop; TRAIN-end forced closes flagged and included (>20% per grid point = disclosure).
- **Selection constants**: all G0-frozen (grids, k=1, 1×SE separation, P4 floor, P5 rule, P2 costs incl. the EURUSD 3.0 RT correction); operational details (tie-breaks, SE definition at θ\*, split-half minima) predeclared in scope pre-data.
- **Exclusions**: any TEST/holdout contact; entry-parameter changes; grid extension or re-ranking after curves; stops/sizing; cross-instrument pooling; per-cell significance claims; cost-model iteration.
- **Constraints**: 2 tests (cluster-bootstrap SE; split-half check) / 5 plots / 1 module — met exactly.

### Results / Observations

- **Membership: 0 / 37** — 35 NON_TUNABLE, 2 FLOOR_FAIL, `G2_COMPOSITION_MET = false`. Verdict TRAINING_DELIVERED; determinism replay (GBPUSD-1h, JP225-4h) frame-identical; elapsed 1.3 s.
- **Failure reasons** (74 family-cells): `endpoint_argmax` 42 (side-mixed — FH 12 low / 8 high; MAD 11/11), `flat_plane` 30, tunable 2. The two tunable cells carry negative plateaus: EURUSD-1h FH(3) S(θ\*) = −3.45 bps (SE 0.92); US500-2h MAD(1.0) S(θ\*) = −0.37 bps (SE 6.19).
- **Net levels**: median net per-event expectancy −5 to −7 bps at every grid point of both families; 20/37 cells net-negative at all 16 grid points; only 17/37 have any net-positive point. Gross proxy (best net + RT) positive in 31/37.
- **Domain pattern**: median best-grid-point net +13.8 bps at 4h (US500-4h +76.7, US2000-4h +53.4, DE30-4h +46.7) vs −2.0 (1h) and −3.4 bps (2h); 4h bootstrap SEs reach ~41 bps, so no 4h positive is certifiable (consistent with the EXP-044 4h MDE range 32–128 bps).
- **Integrity**: 0 forced-close disclosure points; split-half halves ≥16 events everywhere; audit PASS (0C/0W/3 Info) — EURUSD-1h reproduced from raw 1-minute data to full float precision (FH(3) −3.5104978875450863; MAD(1.0) to 1e-14); all 592 stability values and all 37 verdicts re-derived with 0 mismatches.

### Hypothesis-Specific Conclusion

**TRAINING_DELIVERED — empty membership; G2 composition NOT met.** Under the frozen CONSERVATIVE cost model no cell has a tunable exit with a positive stable plateau in either family. Per design §8.3 the phase path is FOUNDATION_NON-TUNABLE with no TEST read spent (G2 gate review adjudicates); Tracks C and D never open.

### Hypothesis-Agnostic Observations

- Exit training cannot manufacture net edge that gross does not contain: the Phase 008/010 cost lesson extends to the full 17-instrument universe, the 2h domain, and per-instrument-trained exits.
- The design-§6 stability machinery's no-signal detection worked as intended — it declined to select on flat/noisy surfaces where the Phase-008 one-SE rule would have picked a point (42 endpoint + 30 flat-plane failures, side-mixed dominance).
- Index-CFD 4h cells hold the only net-positive grid points (up to +76.7 bps) but at SEs (~41 bps) and event counts (32–86) where they are statistically uncertifiable — characterisation targets only if gross per-event edge is first raised (entry-side levers) or costs lowered.

---

## EXP-046 — Phase 012 Entry-Side Gross Screen (`/ALPHA` × `/MA-DOMAIN` OAT, 37-Cell Grid)

**Status**: COMPLETED (hypothesis REFUTED — mechanical G1 readout ENTRY_GROSS_FLAT)
**Date**: 2026-06-12
**Instruments**: the 17 instruments of the Phase 011 37-cell COVERED grid (EXP-044 `coverage_map.csv` verbatim)
**Data Views / Feature Categories**: 1-minute time bars → 1h/2h/4h domain bars (frozen `xen.bar_aggregator`); AVWAP bounce events via the parameterized frozen `xen.avwap`; TRAIN stratum only (0 TEST reads)

### Hypothesis Tests

1. **Hypothesis**: at least one predeclared OAT entry-parameter variant of the frozen AVWAP bounce substrate — tick-volume exponent α ∈ {0.0, 0.375, 1.0} or MA pair ∈ {(10,25), (40,100), (60,150)} — raises TRAIN gross per-event expectancy at H=8 domain bars to ≥ the frozen per-cell cost floor + 1×SE, with positive gross at H=4 and H=16, in ≥5 cells spanning ≥3 instruments of the 37-cell COVERED grid.

### Scope

- **Cells**: the 37 COVERED cells (EXP-044) verbatim; 14 excluded cells never loaded; EXP-043 boundary/count binding enforced at load.
- **Variants**: 7 incl. baseline (α=0.75, MA=(20,50)), OAT only; all other substrate elements frozen (arm/trigger, MAD band, anchor rule, pyramid handling).
- **Rule (all D0-frozen)**: CLEAR iff gross(H=8) ≥ floor + 1×SE ∧ gross(4) > 0 ∧ gross(16) > 0 ∧ ≥30 evaluable events ∧ determinism replay; floor = RT + financing × (8·hours(d)/24), P2 CONSERVATIVE table; one event population per cell×variant (H=16 window inside TRAIN); regime-cluster bootstrap SE (frozen EXP-027 layer, descriptive, seeded).
- **Exclusions**: exit training/selection; net or cost-adjusted return columns; structural entry changes; α×MA combinations; grid extension; TEST/holdout contact; 5m; cross-instrument pooling for clearance; any binding significance claim.
- **Constraints**: 0 binding tests / 4 plots / 1 new module — met exactly.

### Results / Observations

- **Clearance partition**: 14 CLEAR / 235 NO_CLEAR / 10 BELOW_FLOOR over 259 cell×variant rows. Per-variant: baseline 3 cells / 3 instruments; alpha_1.0 3/3; ma_40_100 3/2; alpha_0.0 2/2; alpha_0.375 2/2; ma_60_150 1/1; ma_10_25 0/0. `composition_met = false` for every variant → mechanical readout ENTRY_GROSS_FLAT; verdict SCREEN_DELIVERED.
- **Gross levels**: per-variant H=8 cross-cell medians (n=37 each): baseline −1.15 bps; alpha_0.0 −2.35; alpha_0.375 −1.27; alpha_1.0 −1.62; ma_10_25 −0.54; ma_40_100 −0.16; ma_60_150 +0.28. Floors ~5–20 bps.
- **CLEAR composition**: 12/14 CLEAR rows at 4h, 2 at 2h; US2000-4h clears under 5 variants (largest margin alpha_0.0 +26.04 bps, n=60, SE 26.25); smallest clearing margin alpha_1.0 DE30-4h +0.85 bps. One row passed the margin leg but failed H=4/H=16 sign (ma_40_100 USDCHF-4h, +1.69 bps).
- **BELOW_FLOOR**: all 10 rows are MA variants on 4h cells (ma_60_150 ×8, n=12–28; ma_40_100 ×2, n=13–17).
- **Integrity**: reconciliation 259/259 legs PASS at 1e-9 bps (37 EXP-043 event-count identities; 111 EXP-045 FH-net anchors at θ ∈ {4,8,16}; 111 internal gross-path cross-checks); determinism 259/259 (full-frame replay equality); P8 regression gate green (24/24 tests incl. baseline-fixture invariance at default α/MA); audit PASS (0 critical / 0 warnings / 3 info) with all 259 floors, margins, verdicts, and the rollup independently reproduced.

### Hypothesis-Specific Conclusion

**REFUTED — ENTRY_GROSS_FLAT.** Best non-baseline variant clears 3 cells against the predeclared ≥5-cells/≥3-instruments threshold, on a fully valid grid. Per the ratified Phase 012 operator pre-commitment the entry-parameter lever is exhausted and the programme pivots to substrate revision; G1 is adjudicated in the Phase 012 checkpoint `G1-gate-review.md`.

### Hypothesis-Agnostic Observations

- The gross shortfall is a substrate property, not a parameterization property: the full sampled ranges of both entry levers move the typical cell's gross by ~1–2 bps against ~5–20 bps floors, and no variant adds clearing breadth over baseline.
- Slowing the regime detector trades breadth for a small quality gain: ma_60_150 has the highest median gross (+0.28 bps) but collapses 8 4h cells below the 30-event floor.
- Clearances concentrate exactly where the plan predeclared the false-positive channel (4h index CFDs, SEs 6–28 bps, correlated bloc; calendar-day floor understates weekend financing there) — US2000-4h's repeated clearance is hypothesis-generating only.

---

## EXP-047 — Phase 013 `/ANCHOR` Move-Size Diagnostic (ATR-Prominence Pivot vs Running-Extreme Anchor)

**Status**: REFUTED (mechanical G1b input: ANCHOR_MOVE_FLAT; adjudication at checkpoint)
**Date**: 2026-06-12
**Instruments**: full 17-instrument × {1h, 2h, 4h} grid (51 cells; DE30 truncation disclosed)
**Data Views / Feature Categories**: 1-minute time bars aggregated to 1h/2h/4h via frozen `xen.bar_aggregator` conventions; AVWAP bounce events from frozen `xen.avwap` with a parameterised anchor rule (baseline running-extreme vs `/ANCHOR` ATR(14)-prominence pivot, k=1.0); no chart-type views

### Hypothesis Tests

1. **Hypothesis**: The ratified ATR-prominence significant-pivot anchor materially shifts the TRAIN gross available move-size (lifetime MFE) distribution rightward — ≥1×SE_diff over baseline, to ≥2× the frozen cost floor, MAE shift not erasing the gain — in ≥5 READY cells over ≥3 instruments.

### Scope

- **Registry**: `CF-AVWAP-001/DIAG-007`, 0 slots, 0 TEST reads (TRAIN-only, gross-only diagnostic).
- **Parameters** (Phase 013 D0, RATIFIED pre-data): `/ANCHOR` rule = most price-extreme segment pivot with a completed ≥1×ATR(14) counter-move by the regime-confirmation bar (ties → most recent; running-extreme fallback with `anchor_fallback` disclosure); MFE/MAE on the EXP-022 lifetime boundary, excursions floored at 0; matched-control MFE (EXP-021/027 convention); P4 floor = RT + financing × days(median lifetime), binding = max of the two arms' floors; P5 five-leg SHIFTED_VIABLE rule (M=2); P6 composition ≥5 cells over ≥3 instruments.
- **Time range**: TRAIN only (1-minute-row `train_end_ts`, R1.3); both anchors on identical slices.
- **Exclusions**: any net/cost-adjusted column; exit machinery; EXP-027/029 analogs; TEST/holdout contact; `/LB` `/MB` `/ATR`; re-parameterisation after data contact; 5m; pooling.
- **Constraints**: P8 regression gate (baseline fixture invariance, `/ANCHOR` look-ahead/determinism smoke, fallback path) green before first TRAIN read; blocking reconciliation vs EXP-043 counts and EXP-046 baseline gross(H=8).

### Results / Observations

- `readiness_map.csv`: 51/51 READY (0 invariant violations, determinism replay drift 0, all look-ahead truncation probes pass, all cells ≥30 events).
- `reconciliation.csv`: 125/125 checks pass; gross(H=8) recompute matches EXP-046 persisted values at diff exactly 0.0.
- `shift_classification.csv`: **0/51 SHIFTED_VIABLE**; leg 1 (MFE shift ≥1×SE_diff) 0/51 — Δ median MFE −2.7…+0.9 bps, 29/51 exactly 0.0, best margin −1.67 bps (EURUSD-1h), no `leg1_borderline` flags; leg 2 (median MFE ≥ 2×floor) **51/51**; sensitivity thresholds (≥4/≥2, ≥3/≥2) unmet.
- `audit_anchor_coincidence.csv` (audit artifact): anchor coincidence with baseline 97.8%/98.3%/98.5% mean (min 94.6%) on 1h/2h/4h vs fallback rate only 0.7–1.5%; 13/51 cells with literally identical event populations.
- Move-size levels (anchor arm, per-domain medians): MFE ≈ 24/36/64 bps on 1h/2h/4h vs binding floors ≈ 4.9/5.3/7.2 bps; censored fractions ≤3.1%; matched-control MFE ≈ event MFE (1h controls slightly higher).
- Audit PASS (0 Critical / 2 Warning — both interpretive: the fallback disclosure misses the qualification-collapse path; the FLAT verdict is conditional on k=1.0).

### Hypothesis-Specific Conclusion

**REFUTED**

At the ratified k=1.0, the ATR-prominence rule selects the baseline running extreme in ~95–99% of regimes (the segment extreme almost always has a completed ≥1×ATR counter-move by MA(20,50) confirmation and is the most price-extreme candidate), so the two arms' event populations are nearly or exactly identical and no MFE shift exists outside noise in any cell. Mechanically ANCHOR_MOVE_FLAT; per the operator pre-commitment this routes the programme to a new candidate family. The verdict closes the ratified `/ANCHOR` definition only — it is not evidence that anchor placement is irrelevant under a binding prominence threshold.

### Hypothesis-Agnostic Observations

- The available peak move was never the scarce quantity: median lifetime MFE is ≈5–9× the frozen cost floor in all 51 cells on both anchors. Combined with the Phase 010/011 exit-side negatives, the binding constraint on this substrate is capture geometry (peak → realizable exit, net of cost), not move availability — a direct input to the new-family design brief.
- Collapse-toward-baseline disclosures for parameterised event definitions must measure outcome coincidence (anchor coincidence rate), not just the explicit fallback path; the predeclared `fallback_rate` column read ~0 while the rule was ~98% inert.
- Bounce-event lifetime MFE is comparable to matched in-regime control bars (descriptive) — consistent with the established relative-not-absolute character of the bounce edge.

---

## EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)

**Status**: READINESS_DELIVERED
**Date**: 2026-06-14
**Instruments**: all 17 (BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225)
**Data Views / Feature Categories**: 1-minute time bars aggregated to 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`) OHLC domains; Heiken Ashi candles from domain bars via `xen.heiken_ashi_generator`; ATR-ZigZag sequential streaming substrate on real bars (Wilder ATR-14, `ATR_MULT=1.0`); HA harami shift-1 vectorized detector on HA candles; no chart-type views

### Hypothesis Tests

1. **Hypothesis** (exploratory readiness, no market-edge claim): For every one of the 102 cells (17 instruments × {5m, 15m, 30m, 1h, 2h, 4h}), the ATR-ZigZag trend substrate (real bars) **and** the HA harami detector (HA candles) can each be computed deterministically, look-ahead-safe, and invariant-clean on the TRAIN analysis stratum; and their measured per-cell move/event rates and `/BARCFG` coverage quantify per-cell context for the downstream capture read (EXP-049).

### Scope

- **Instruments**: all 17 VAL-003/VAL-004-admitted instruments (4 core + 13 new-universe). DE30 with truncated history disclosure.
- **Data Views / Feature Categories**: 6 OHLC domains (5m strict; 15m/30m/1h/2h/4h at 0.90 coverage). HA candles per cell.
- **Primitives** (two independent, frozen defaults): ATR-ZigZag (Wilder ATR-14, `ATR_MULT=1.0`, real bars, sequential streaming) — proof that the substrate is causal and deterministic; HA harami detector (body-inside-prior-body, reduced-form `HAClose₀ ∈ (PrevBodyMin, PrevBodyMax)`, shift-1 vectorized) — proof the detector is invariant-clean.
- **Per-cell checks**: construction integrity (OHLC consistency, monotonic `CloseTime`, dropped-fraction gate); ZigZag invariant battery (alternation, causality, timestamps, threshold breach, monotonic confirmation, no NaN); HA harami invariant battery (reduced-form agreement, adjacency, monotonicity, no NaN); determinism replay (full second pass, frame-identical comparison).
- **Parameters**: `ATR_MULT=1.0`, `atr_period=14`. No sweep, no tuning, no combined event.
- **Time range**: TRAIN only (first 49% via F01 prefix; nested analysis-set TEST + final-30% holdout sealed).
- **Exclusions**: no combined harami-at-trend-exhaustion event (014-B / EXP-050+); no 3-barrier capture, returns, MFE/MAE, expectancy, or edge of any kind; no strong-move filters; no sweep or selection; no TEST/holdout contact; no outcome metrics.

### Results / Observations

- **Status distribution**: 86 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED (US500-4h, JP225-2h, JP225-4h), 0 CONSTRUCTED_EMPTY, 0 NOT_READY (any type).
- **COVERAGE_EXCLUDED**: US500-4h (dropped 0.286), JP225-2h (0.257), JP225-4h (0.297) — market-hour gap × longest aggregation windows.
- **READY_FLAGGED**: 13 cells across US500, US2000, DE30, JP225, XAUUSD, USTEC — dropped ∈ [0.10, 0.25], all well below the 0.25 exclusion gate.
- **All invariant violations**: 0 on every cell (12 invariant keys, both primitives).
- **All determinism failures**: 0 (102/102 cells PASS frame-identical replay).
- **Move rates** (ATR-ZigZag confirmed moves per 1k domain bars): range [170.2, 207.0] across all non-excluded cells. All 99 cells ≥30 moves (minimum 336).
- **Harami event rates** (per 1k HA candles): range [229.6, 261.4]. All 99 cells ≥30 events (minimum 401).
- **`/BARCFG` coverage** (pooled fractions across domains): UP_UP ~33–35%, DN_DN ~31–34%, UP_DN ~16–18%, DN_UP ~15–17%. Near-symmetric same-direction dominance, consistent with the family's construction-derived reduction.
- **DE30 disclosure**: truncated history (broker ends 2026-01-16); all counts/rates from its own timeline. Rates per 1k comparable; absolute counts systematically lower.
- **SUBSTRATE_REFUTED criteria**: unmet (no non-determinism, no systematic invariant failure on ≥3 instruments).
- **Audit PASS**: 0 Critical, 1 Warning (latent `/BARCFG` null bug — zero-harami guard not exercised in this run), 2 Info.

### Hypothesis-Specific Conclusion

**READINESS_DELIVERED**

Both primitives are mechanically valid across all 99 non-excluded cells: zero invariant violations (both batteries), zero determinism failures (102/102), and the per-cell readiness map, move/event-rate table, and `/BARCFG` coverage table are produced as scoped. The 13 READY_FLAGGED and 3 COVERAGE_EXCLUDED cells are coverage outcomes (dropped-fraction disclosures), not primitive defects. The 99 non-excluded cells clear the substrate/detector gate for EXP-049 capture read. No market-edge claim is tested or implied.

### Hypothesis-Agnostic Observations

- **COVERAGE_EXCLUDED follow EXP-043 pattern**: US500-4h, JP225-2h/4h — market-hour gap × longest aggregation windows. Consistent with the EXP-043 convention; these are permanent cell-level exclusions under the frozen coverage gate.
- **Move rates are instrument-stable**: ATR-ZigZag at `ATR_MULT=1.0` on Wilder ATR-14 produces a narrow 170–207/1k range across 17 instruments × 6 domains — a fixed-parameter pivot-threshold property, not market-structure variation.
- **Harami incidence is near-constant**: ~230–261/1k across all cells — a construction-derived consequence of the reduced-form constraint on `HAClose₀`, not a market signal. Incidence is independent of instrument, domain, or volatility regime.
- **`/BARCFG` near-symmetric**: UP_UP ~33–35% vs DN_DN ~31–34% dominance, expected from the family's reduced-form proof. UP_UP > DN_DN asymmetry consistent with mild bullish TRAIN-period drift.
- **DE30 short history**: Truncated broker history means DE30 bar counts are ~20–30% lower than full-history instruments, though rates per 1k remain comparable. All DE30 cells are READY or READY_FLAGGED (no exclusions from span alone); DE30 pass-through to EXP-049 with disclosure.

---

## EXP-049 — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 99 Cells)

**Status**: CAPTURE_READINESS_DELIVERED
**Date**: 2026-06-15
**Instruments**: all 17; 99 member cells = EXP-048 READY ∪ READY_FLAGGED (3 COVERAGE_EXCLUDED cells excluded per scope)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; ATR-ZigZag trend-change confirmation anchor (Wilder ATR-14, `ATR_MULT=1.0`); P1–P5 Phase 014 benchmark 3-barrier system on real bars; no HA candles, no harami detector

### Hypothesis Tests

1. **Hypothesis (HYP-002)**: For every EXP-048-READY cell, the 3-barrier capture system (P2 favourable, P3 1:1 adverse, P4 adaptive time cap, P5 LOOKBACK=1) can be constructed deterministically and causally on real prices; and the per-cell gross favourable-before-adverse capture rate `r = P(fav before adv | resolved)` is measured under the predeclared default barriers (two geometries: G1 distance-based primary, G2 retracement-level secondary), with P12 viability (`r ≥ 0.55`, `CI_low > 0.50`, `resolved ≥ 30`) and P11 composition (≥5 cells over ≥3 instruments) applied as a mechanical readout.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views (5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`); ZigZag trend-change substrate (frozen `xen.zigzag`, unchanged); barrier module `xen.capture_barriers` (new).
- **Features**: per-event favourable/adverse/time-cap/data-censored outcome on real High/Low; per-cell capture rate `r` with regime-clustered moving-block bootstrap CI (MBB, `b=round(m^(1/3))`, `N_BOOT=10_000`); invariant battery (causality, fence, determinism, NaN, G1 well-formedness).
- **Parameter ranges**: P1 ATR-14/1.0; P2 X=50%; P3 1:1; P4 `N=max(6,round(1.5·median(trailing-20 durations)))`; P5 LOOKBACK=1; G1 (distance-based, primary), G2 (retracement-level, secondary).
- **Exclusions**: no HA harami detector or combined harami entry (014-B); no `/CONFIRM` model; no alternative barrier variants (`/VPTARGET`, `/MAGTARGET`, etc.); no strong-move filters; no costs; no TEST/holdout contact; no candidate slot consumption; no returns or edge claims.

### Results / Observations

- **CAPTURE_READINESS_DELIVERED**: 99/99 member cells pass all invariant batteries (0 causality, 0 fence, 0 NaN, 0 G1 fav_dist violations); 0 non-deterministic cells (frame-identical second-pass replay); 0 systematic invariant failures.
- **G1 capture rate (primary/distance-based)**: `r` ranges [0.4545, 0.5343] across all 99 cells, tightly clustered around the 0.50 symmetric-barrier null. **0/99 cells VIABLE** — all `BELOW_R` (r < 0.55). `composition_met = false` (0 cells, 0 instruments). Sensitivity at relaxed bars also `false`.
- **G2 capture rate (secondary/retracement-level)**: `r` ranges [0.3257, 0.4389]. **0/99 VIABLE**. 52–60% of events degenerate (entry at/through midpoint), correctly excluded and disclosed.
- **Power**: all member cells `resolved ≥ 30` (min 128). **0 NOT_VIABLE_BY_POWER** cells.
- **Time-cap censoring (unresolved fraction)**: 22–33% across cells. Data-truncation < 0.5%. Adaptive P4 cap binds at 6-bar floor in 96/99 cells.
- **Determinism**: PASS (full-frame replay, identical CI bounds, 0 degenerate bootstrap resamples in any cell).
- **Audit PASS**: 0 Critical, 0 Warning, 4 Info notes.
- **Verdict stage**: the experiment does not self-adjudicate G1; `composition_met = false` is consistent with design §10 CHARACTERISED_NOT_VIABLE on the capture leg. Desk adjudication combining EXP-048 (leg a), EXP-049 (leg b), and future 014-B (leg c) is pending.

### Hypothesis-Specific Conclusion

**CAPTURE_READINESS_DELIVERED**

Barrier construction is valid on 99/99 cells. The G1 capture-rate readout is uniform negative: 0 VIABLE cells under P12. The capture geometry under benchmark defaults (50% favourable fraction, 1:1 R:R, adaptive time-cap) does not produce a favourable-before-adverse bias above the 0.55 viability bar in any cell of the 17×6 grid. The G2 secondary geometry is systematically weaker due to ~52–60% degeneracy and also 0/99 VIABLE.

### Hypothesis-Agnostic Observations

- **r ≈ 0.50 is a genuine null, not a power failure**: with symmetric equidistant barriers on either side of a ZigZag-confirmation entry, price has approximately equal probability of hitting either target first on this substrate. The null is consistent with a near-random-walk path.
- **G2 degeneracy is structural**: the entry-mostly-inside-midpoint pattern means ZigZag confirmations occur after ~50% giveback of the prior move, so the midpoint is often inside the entry-exit range. This is not a model defect but a property of the `ATR_MULT=1.0` pivot threshold.
- **Adaptive cap binds at floor**: median N_event = 6.0 (floor) in 96/99 cells. The P4 adaptive mechanism delivers no per-cell variation beyond the floor for this substrate — the `/THIRD-TIME` sensitivity branch would be informative only at barrier ratios or k-values above the floor.
- **Barrier system is reusable**: `xen.capture_barriers` passed construction validation and determinism on 99 cells × 2 geometries. Any 014-B variant can reuse it without re-validation.

---

## EXP-050 — Phase 014-A Harami-in-Context Characterisation

**Status**: CONTEXT_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for harami detection; real domain prices for all metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, where in a ZigZag move do raw HA harami signals occur, and does the per-cell final-third rate FT exceed the direction-matched random-timing baseline FT_rand by ≥ 10pp (P9 materiality)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: HA candles (via `xen.ha_candles`); real-domain OHLC for positioning; ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged).
- **Features**: harami detection (`xen.ha_harami`); pivot-tiling interval join for move-assignment; price-excursion position `pos = (P − S_i) / (E_i − S_i)`; FT = P(pos ≥ 0.67); direction-stratified random baseline FT_rand; regime-clustered MBB CI on Δ = FT − FT_rand; P9/P11 mechanical readout; MA(20,50) alternative-segmentation secondary.
- **Parameter ranges**: P3 position-in-move with D0-ratified 0.67 threshold; P4 ZigZag ATR 14/1.0; P5 direction-matched random baseline (in-move cardinality, 2,000 bootstrap draws); P6 OFF (no /BARCFG filter); P7 `cluster_by_move` bootstrap; P8 two-pass deterministic replay; P9 materiality 10pp; P11 composition ≥5 cells ≥3 instruments FT ≥ 0.50; P13.2 MA(20,50) secondary segmentation.
- **Exclusions**: no ZigZag confirmation filter; no /BARCFG or strong-move filter; no combined harami+barrier event (014-B); no costs; no TEST/holdout contact; no candidate consumption; no returns or edge claims; no direction differentiation in FT (pooled across up/down).

### Results / Observations

- **Verdict**: CONTEXT_CHARACTERISATION_DELIVERED. **0/99 cells CLUSTERED** (all NOT_CLUSTERED). Composition readout: 0 cells, 0 instruments, `composition_met = false` at every support tier and every sensitivity threshold.
- **FT**: range [0.210, 0.312] across 99 cells. FT_rand: range [0.334, 0.432]. Δ = FT − FT_rand: every cell negative; median approximately −0.12 to −0.18 across domains.
- **MA(20,50) secondary (P13.2)**: Δ_ma_vs_rand ≈ 0 (range [−0.041, +0.010]). Front-loading attenuates under MA regime segmentation — it is a ZigZag-specific phenomenon.
- **All invariants pass**: 0 detector self-check, 0 assignment well-formedness, 0 TRAIN fence violations; all 99 cells deterministic; all reportable (min n_assigned = 393).
- **P11 composition**: not met at any sensitivity threshold (strawman 0.50 fails on both FT and FT_rand for every cell).
- **Secondary disclosure**: FT, FT_rand, Δ, FT_ma, FT_rand_ma, Δ_ma recorded per cell in `secondary_disclosure.csv`.

### Hypothesis-Specific Conclusion

**CONTEXT_CHARACTERISATION_DELIVERED.** The raw unfiltered HA harami signal does not cluster near exhaustion on the ATR-ZigZag substrate. Harami timing is systematically front-loaded relative to random in-move timing. This is a clean baseline measurement: the null landscape any filter or confirmation rule must beat is known (Δ ≈ −0.12 to −0.18).

### Hypothesis-Agnostic Observations

- **Front-loading is ZigZag-specific**: under MA(20,50) segmentation, delta clusters near zero. ZigZag defines move starts at pivot extremes; haramis (small consolidations) appear soon after. MA regimes define moves by crossover timing — haramis have no systematic position bias there.
- **Selection force requirement**: a filter must shift the position distribution rightward by ~12–18pp just to reach Δ = 0, and ~22–28pp to meet the P9 materiality threshold.
- **FT never reaches 0.50**: even the unconditioned raw-timing baseline FT_rand is typically 0.33–0.43 (direction-matched uniform draw is the third of the move ≈ 1 − 0.67). The deterministic position-in-move metric therefore cannot resolve a cell in the upper half of the unit interval for this ZigZag geometry.
- **Implication for 014-B**: any combined harami+barrier event definition cannot rely on harami position-in-move as a timing filter — capture barriers (EXP-049/014-B) must manage outcome structurally. EXP-051 (strong-move filters) and EXP-052 (confirmation) should test whether selection can shift the distribution rightward.

---

## EXP-051 — Phase 014-A Strong-Move Filter Characterisation

**Status**: STRONG_FILTER_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for /STRONG-HA impulse-run detection; real domain prices for all magnitude metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, do /STRONG-STAT (p75) and /STRONG-HA (primary same-direction) each carve a materially different move sub-population by P10 (ρ ≥ 1.5 and f ∈ [0.10, 0.50]), and does each meet P11 (≥5 cells over ≥3 instruments)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged); new `xen.strong_move` module for both filter forms.
- **Features**: /STRONG-STAT trailing-window p75 filter (window ≤20, warmup 5; binding form) + median+1×MAD alternative (disclosed); /STRONG-HA qualifying 3-bar impulse-run detection + run→move mapping (primary same-direction binding; any-direction sensitivity disclosed); per-cell ρ/f/P10 point criterion; P11 composition readout; moving-block bootstrap CI on ρ (disclosed); harami-overlap secondary (disclosed); two-pass determinism replay.
- **Parameter ranges**: P7 trailing window 20, warmup floor 5, p75 (binding) + median+1×MAD (disclosed); P8 run length X=3, HA trailing body-median window 20, warmup floor 5 HA bars; P10 ρ ≥ 1.5 ∧ f ∈ [0.10, 0.50]; P11 composition ≥5 cells ≥3 instruments; P6 OFF (no /BARCFG filter).
- **Exclusions**: no 3-barrier capture geometry (EXP-049), no position-in-move (EXP-050), no /CONFIRM entry model (EXP-052), no combined harami+barrier event, no /BARCFG isolation, no costs, no returns/P&L, no TEST/holdout contact, no candidate consumption.

### Results / Observations

- **Verdict**: STRONG_FILTER_CHARACTERISATION_DELIVERED. **Both binding forms clear P11** with 99/99 MATERIAL cells across all 17 instruments.
- **/STRONG-STAT (p75)**: ρ range [1.72, 2.19], median 1.92, IQR [1.86, 1.97]; f range [0.25, 0.32], median 0.27. 99/99 MATERIAL, 17/17 instruments.
- **/STRONG-HA (primary)**: ρ range [1.62, 2.08], median 1.80, IQR [1.76, 1.86]; f range [0.15, 0.24], median 0.20. 99/99 MATERIAL, 17/17 instruments.
- **Alternative-form agreement**: 0 flips between p75↔MAD; 0 flips between primary↔sensitivity. Disclosed forms agree exactly on materiality status.
- **All invariants pass**: 0 filter well-formedness, 0 magnitude validity, 0 HA self-consistency, 0 causality/TRAIN fence violations; determinism PASS; all 99 cells reportable (n_defined 331–31,431).
- **Harami overlap (disclosed)**: overlap_A 65–87% (/STRONG-STAT) and 74–91% (/STRONG-HA); overlap_B 24–46% across both filters.
- **P11 composition**: material_per_domain = 17/17/17/17/16/15 (5m/15m/30m/1h/2h/4h); 3 COVERAGE_EXCLUDED cells (US500-4h, JP225-2h/4h) not in member-cell set.

### Hypothesis-Specific Conclusion

**STRONG_FILTER_CHARACTERISATION_DELIVERED.** Both /STRONG-STAT (p75) and /STRONG-HA (primary) filters identify materially different move populations from the ATR-ZigZag confirmed-move substrate, meeting the P10 bar in every cell and clearing P11 with 99 material cells across all 17 instruments. The disclosed alternative forms agree (0 flips). The experiment verdict is delivery; G1 adjudication is checkpoint desk work.

### Hypothesis-Agnostic Observations

- **p75 mechanical selectivity**: The trailing-window p75 retains ~25% (modulo ties), mechanically inside [0.10, 0.50]. ρ ≥ 1.5 reflects the heavy right tail of move magnitudes — the median of the top quartile is ~1.9× the full median. Uniform 99/99 materiality may partly be a property of the substrate's magnitude distribution, not a special filter property.
- **HA impulse runs as large-move proxy**: The /STRONG-HA detector selects moves containing 3 consecutive strong HA impulse bars. Lower ρ (~1.80 vs ~1.92) suggests HA impulse bars can occur mid-move without the move being in the top magnitude quartile.
- **Both filters viable for 014-B**: The narrow cross-cell IQR (ρ ~0.06–0.10, f ~0.01–0.02 within each form) suggests uniform behaviour across instruments/domains, allowing simpler global parameterisation in 014-B.
- **Overlap_B baseline**: Most haramis (54–76%) occur outside strong moves. A combined-event definition must handle this asymmetry — either by filtering harami detection to strong-move windows or using the strong-move condition as a post-hoc selector on captured haramis.

---

## VAL-004 — 15m/30m Domain Temporal-Integrity Validation (Phase 014 Gate)

**Status**: SUPPORTED (PASS)
**Date**: 2026-06-14
**Instruments**: AUDJPY, AUDUSD, BTCUSD, DE30, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NZDUSD, US2000, US500, USDCAD, USDCHF, USDJPY, USTEC, XAUUSD (all 17 VAL-003-admitted)
**Data Views / Feature Categories**: 1-minute time bars → aggregated OHLC (15m and 30m, each in strict and tolerant `min_coverage=0.90` modes); Heiken Ashi, Line Break (level 3), Renko (ATR 14) chart views over the new domains.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments.
- **Data Views / Feature Categories**: 15m and 30m OHLC domains in strict and tolerant (`min_coverage=0.90`) modes; chart-type alignment checks (Line Break level 3, Renko ATR 14, Heiken Ashi) over the new domains.
- **Features**: VAL-001 rev. 3 check battery — future-timestamp, monotonic `CloseTime`, `SourceBars`/coverage semantics, OHLC bounds, cross-view timestamp alignment, head/middle/tail prefix-stability probes, determinism replay, negative controls; per-cell dropped-window-fraction for tolerant mode.
- **Parameters**: `SOURCE_TIMEFRAMES = [15, 30]` (15 = determinism anchor); `min_coverage ∈ {None (strict), 0.90}`.
- **Exclusions**: final 30% global holdout sealed at first touch; no Phase 014 signal/harami logic; no strategy or edge claim; no parameter tuning.
- **Constraints**: byte-identical check logic to VAL-001 rev. 3 in strict mode; `SourceBars` valid-range parameterized for tolerant mode; deterministic generation; `tqdm` over the 17-instrument outer loop.

### Results / Observations

- **Suite PASS**: 2,279 validation checks, 0 FAIL, 0 INCONCLUSIVE; 28/28 negative controls detected; 2/2 golden fixtures PASS; 2/2 must-not-overfire assertions PASS; floor guard PASS.
- **Universe reconciliation**: 17/17 expected instruments present, 0 missing/duplicates; 1 unexpected group (ANALYSIS70, 4 pre-sliced files) disclosed and excluded.
- **15m determism anchor**: all 17 instruments reconcile to the pinned VAL-001/VAL-003 record (every prior key present and PASS in VAL-004).
- **68/68 cells ADMITTED** (all dropped fractions ≤ 0.133, well below the 0.25 gate).
- **Dropped fractions**: 0.003–0.133 (tolerant); 0.012–0.277 (strict). Highest tolerant: JP225-15m (0.133); lowest: USTEC-30m (0.003). Index-instrument dropped fractions are higher (0.08–0.13) reflecting market-hour gaps, but all below the gate.
- **Chart densities**: HA 1.0 everywhere; LB 0.20–0.30; Renko 0.22–0.28 — consistent with prior VAL-001 patterns.
- **Plots**: `plots/dropped_fraction_map.png`, `plots/check_pass_heatmap.png`.

### Hypothesis-Specific Conclusion

**SUPPORTED (PASS)**

The 15m/30m domains in both strict and tolerant modes preserve temporal alignment, OHLC integrity, cross-view timestamp alignment, and deterministic regeneration across all 17 instruments. The §5 VAL gate in the Phase 014 checkpoint design is PASSED. All 17 instruments × {15m, 30m} cells are individually admissible to EXP-048.

### Hypothesis-Agnostic Observations

- Tolerant-mode dropped fractions are consistently lower than strict fractions (tolerant retains legitimate partial windows), confirming the coverage trade-off is measured, not assumed.
- Index instruments (DE30, JP225, US500) have higher dropped fractions reflecting session gaps, but all clear the 0.25 admission gate — consistent with the Phase 011 2h dropped-fraction convention (JP225-2h was excluded at >0.25; no 15m/30m cell reaches that threshold).
