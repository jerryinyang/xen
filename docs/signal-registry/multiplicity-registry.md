# Phase 004 Multiplicity Registry

**Status:** Phase 013 **CLOSED 2026-06-12 — ANCHOR_MOVE_FLAT** (substrate-revision pivot: anchor move-size diagnostic; governing design: `docs/experiments-docs/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/design.md`; G1a 51/51 READY; G1b adjudicated **0/51 SHIFTED_VIABLE** in the checkpoint `G1-gate-review.md`; retrospective written 2026-06-12). **EXP-047 COMPLETE — DIAGNOSTIC_DELIVERED, hypothesis REFUTED, audit PASS:** the ratified k=1.0 ATR-prominence anchor collapses to the baseline running extreme by qualification (anchor coincidence 94.6–98.5%, fallback only 0–2%; 13/51 identical event populations; Δ median MFE −2.7…+0.9 bps, all inside noise). Unanticipated descriptive read: median lifetime peak MFE ≈5–9× the frozen cost floor in all 51 cells on both anchors — **move availability was never the binding constraint; capture geometry is**. Integrity clean (reconciliation 125/125 at diff 0.0, determinism everywhere, P8 gate 15/15). **0 slots, 0 TEST reads, ledger unchanged, holdouts sealed.** `/ANCHOR` is **CLOSED-MEASURED as ratified** (k=1.0; re-opening requires a new D0 with a demonstrably binding threshold); **`CF-AVWAP-001` is closed for new in-family phases** — exits (010–011), entry parameters (012), and the anchor (013) all measured flat; `/LB` `/MB` `/ATR` stay DEFERRED with no candidate status. **Pre-committed routing executed: the programme routes to a NEW CANDIDATE FAMILY** (Phase 014, own design/D0, fresh EXP-020/027/029-analog scaffolding; design brief targets capture geometry, not move availability). Phase history: **G0 PASS 2026-06-12** One TRAIN-only diagnostic (**EXP-047**, `CF-AVWAP-001/DIAG-007`, 0 slots / 0 TEST reads) exercising the registered `/ANCHOR` branch (gap #1, deferred since Phase 005): replace the running-extreme AVWAP anchor with an **ATR-prominence significant pivot** (`k=1.0 × ATR(14)` confirmation, running-extreme fallback; operator-ratified `D0-predeclarations.md`) and compare the gross **available favorable move-size** (MFE) distribution vs the baseline anchor against the frozen P2 cost floor, over the full 17-instrument × {1h,2h,4h} universe (readiness-defined membership). **Corrected substrate framing (verified `python/src/xen/avwap.py:390–421`):** the substrate is a **trend-continuation pullback entry**, not a fade — entry direction is sound (Phase 011 gross 31/37), the failure is economic (captured move < cost), so this phase tests the only registered lever that changes *move geometry*. Verdicts: **ANCHOR_MOVE_VIABLE** (≥5 SHIFTED_VIABLE cells over ≥3 instruments; SHIFTED_VIABLE = ≥1×SE rightward MFE shift ∧ `median_MFE(/ANCHOR) ≥ 2×floor` ∧ no MAE-erasure ∧ ≥30 events ∧ determinism) → future in-family `/ANCHOR` viability phase (own D0; EXP-027/029 analogs + net training + TEST endpoint); or **ANCHOR_MOVE_FLAT** → move-size ceiling intrinsic to the AVWAP family → new candidate family (own D0). `/ANCHOR` is a new event definition → hard EXP-020-analog readiness gate (P2) precedes any move-size read. **G0 PASS 2026-06-12** (D0 P1–P8 operator-ratified, `k=1.0`/`M=2` decided, registry amended, 0 slots, 0 TEST reads by construction; holdouts sealed). See the Phase 013 Batch section. Prior: Phase 012 **CLOSED 2026-06-12 — ENTRY_GROSS_FLAT** (entry-side gross screen; governing design: `docs/experiments-docs/checkpoints/2026-06-12-012-entry-side-gross-screen/design.md`. **EXP-046 SCREEN_DELIVERED — hypothesis REFUTED:** no `/ALPHA` or `/MA-DOMAIN` OAT variant meets the P6 composition threshold (best non-baseline 3 clearing cells vs ≥5 over ≥3 instruments; variant H=8 cross-cell medians move gross only ~1–2 bps vs ~5–20 bps floors; 12/14 CLEAR rows in the predeclared 4h/index false-positive channel — US2000-4h hypothesis-generating only). Integrity clean: reconciliation 259/259 at 1e-9 bps vs the EXP-043/045 anchors, determinism 259/259, audit PASS, post-experiment governance APPROVE. G1 adjudication: `docs/experiments-docs/checkpoints/2026-06-12-012-entry-side-gross-screen/G1-gate-review.md`; retrospective in the same checkpoint. **0 slots consumed; 0 TEST reads; ledger unchanged; holdouts sealed.** `/ALPHA` and `/MA-DOMAIN` are **CLOSED-MEASURED** on this substrate (swept and flat; no slot ever consumed; re-opening requires a new substrate). **Routing per the design §1.4.2 operator pre-commitment: the programme pivots to substrate-level revision** — the Phase 013 design starts from the Stage-C registered branches (`/LB` `/MB` `/ATR` `/ANCHOR`, deferred since Phase 005) or a new candidate family; any new event definition requires fresh readiness/calibration/parity passes (EXP-020/027/029 analogs) under its own design/D0. Phase history: **G0 PASS 2026-06-12** — operator §9 routing decision (Route 1, entry-side exploration via TRAIN-only gross screen, EXP-046, 0 slots, 0 TEST reads by construction; pre-committed ENTRY_GROSS_FLAT fallback = substrate pivot, no second entry-parameter phase on this substrate; structural `/ENTRY` arm/trigger changes out of scope, assigned to the pivot branch). See the Phase 012 Batch section.) Prior: Phase 011 **CLOSED 2026-06-11 — FOUNDATION_NON-TUNABLE** (G2 FAIL: EXP-045 Track B membership **0/37** vs the P5 floor of ≥5 cells over ≥3 instruments; 35 NON_TUNABLE + 2 FLOOR_FAIL with negative plateaus; net medians −5 to −7 bps at every grid point of both exit families under frozen CONSERVATIVE costs while a gross proxy is positive in 31/37 — the failure is economic, not methodological. **Tracks C/D never opened; 0 of ≤6 TEST reads spent; ledger unchanged.** G2 adjudication: `docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/G2-gate-review.md`; retrospective in the same checkpoint. Routing per design §9: `/ENTRY` exploration or substrate change becomes the path; next phase design pending.) Phase history: **G0 PASS 2026-06-11** (D0 closed, predeclarations frozen). **Track A0 REMOVED 2026-06-11 — EXP-042 set aside (MEASUREMENT_COMPLETE — FRAMING_ERROR):** the band multiplier is an exit parameter, not an entry parameter; the arm-at-adverse-band entry rule is rescinded, entry reverts to the frozen baseline arm/trigger at the AVWAP line, and the band lives entirely in Track B per-cell exit training (see the Phase 011 Batch section and `docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`) — per-instrument foundation & strategic reset (governing design: `docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/design.md`; supersedes the original Phase-011 MTF scoping). See the Phase 011 Batch section. Prior: Phase 010 **CLOSED 2026-06-11 — EXIT_FLAT (Track A) / HYP-001 INCONCLUSIVE (Track B); INFR-002 carried OPEN** (governing design: `docs/experiments-docs/checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md`; retrospective in the same checkpoint). EXP-039 `/EXIT-X` TRAIN screen **MEASUREMENT_COMPLETE — FLAT** (0/10 cells qualify under §8.1; best 4h candidate E2 +31.9 bps vs R-FH(12) +37.3 bps, gap −5.4 bps ≈ 0.5 SE; 1h all net-negative incl. R-BTC). G1 never opened; **EXP-041 reserved-inactive, slot unused, no TEST row read this phase.** EXP-040 HYP-001 **INCONCLUSIVE** (1h Δ=+1.55 pp CI[−4.52,+8.43] Holm p=0.585; 4h below the 100-episode floor; moving-copy arm descriptive: 1h Δ_m=+3.41 pp — kinematic confound does not explain the premium; HYP-001 remains OPEN as a permanent mechanism record). **Operator decision (design §9 EXIT_FLAT, recorded 2026-06-11):** Phase 011 proceeds on the **Phase 008 frozen package** (FH H\*=12, all_legs, EXP-037 freeze, hash-pinned); Stage-C family review **deferred** — any Stage-C variant would face the same ~86-event 4h TRAIN power wall EXP-039 documented; revisit once the new universe can power it. INFR-002 (new-universe collection) **COMPLETE 2026-06-11 — VAL-003 PASS**: all 13 instruments collected and admitted (1,396 checks, 0 FAIL, 0 INCONCLUSIVE, 24/24 negative controls detected); holdout sealed per file at first touch; DE30 coverage truncated (data ends 2026-01-16 vs 2026-06-11 for the other 12 — disclosed, see batch row). See the Phase 010 Batch section. Phase 009 holdout shot **SPENT 2026-06-10 — HOLDOUT_INCONCLUSIVE** (`CF-AVWAP-001/HOLDOUT-B`, EXP-032: n=27, net +20.60 bps, ci_low_1s 2.71 ≤ margin 4.32, boot_p 0.029; no second holdout read ever for Package B or A; EXP-037/038 TEST evidence permanently non-upgradable; EURUSD holdout contaminated-by-disclosure, other instruments sealed; Tier-C routing per Phase 008 design §9). Previously ACTIVE under Phase 008 (clinical tradability: selectivity, instrument selection, capture efficiency) — opened 2026-06-10, governing design: `docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`. Phase 007 **CLOSED 2026-06-10 — NOT_TRADABLE** (design §9; retrospective: `docs/experiments-docs/checkpoints/2026-06-09-007-avwap-tradability-and-isolation/retrospective.md`). EXP-030 **COMPLETE 2026-06-10** — INCONCLUSIVE: net tradability not resolved on any domain (5m/1h EVIDENCE_AGAINST, 4h INCONCLUSIVE_SPANS_ZERO). Holdout-release gate (EXP-032) not passed. EXP-031 **COMPLETE 2026-06-10** — ISOLATION_READ_UNRESOLVED: entry-dominant at H=6, exit-dominant at H=1 on all domains; horizon contradiction triggers unresolved outcome. Phase 006 **CLOSED 2026-06-09** — `EVAL_SUPPORTED`/cTrader-confirmed: EXP-027 METHOD_VALID, EXP-028 EVIDENCE_FOR on all 3 domains, EXP-029 CONSISTENT parity. Phase 007 opened 2026-06-09 to answer cost-bearing tradability (EXP-030) and entry-vs-exit edge isolation (EXP-031); holdout release (EXP-032) is DEFERRED and hard-gated on EXP-030 — gate not passed. Phase 005 **HALTED 2026-06-08** before Stage B/C — operator review found EXP-023/024/025 inherited an evaluation-framing defect (a ~6%-active event signal screened/diagnosed through a per-bar continuous-position referee calibrated only for ≥80%-active series). Dispositions corrected by **supersede + retain** (no ID reuse, no erasure): EXP-023 SUPERSEDED (framing-corrected), EXP-024 RETAINED (fork leg discounted), EXP-025 INCONCLUSIVE (non-informative for HYP-001); EXP-026 `/EXIT` SHELVED; Stage C deferred. Root-cause review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. Phase 006 opened to fix the evaluation vehicle (EXP-027) then re-screen the faithful strategy (EXP-028).
**Opened:** 2026-06-07 (Phase 004); extended 2026-06-08 (Phase 005, HALTED); corrected 2026-06-08 (Phase 006)
**Governing phases:**
- `docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration/design.md`
- `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md` (HALTED)
- `docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/design.md` (COMPLETED 2026-06-09)
- `docs/experiments-docs/checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md`

## Purpose

This file is the Phase 004 programme-level file-drawer ledger. The frozen
three-component suite controls per-candidate qualification error; this registry
controls the programme risk created by trying many candidates, variants, or
definitions and only remembering the winners.

No Phase 004 candidate screening is admissible unless the candidate family,
hypothesis, parameter branch, and EXP-ID appear here first.

## Frozen Qualification Suite

| Component | Source | Detection floor by domain |
| --- | --- | --- |
| Strict gate stack | EXP-003 / EXP-005 | 5m: 1 bps; 1h: 4 bps; 4h: 12 bps |
| Ratified-loose referee | EXP-012 | 5m: 0.5 bps; 1h: 2 bps; 4h: 8 bps |
| Revised portfolio-fitness unit | EXP-018 | 5m: 12 bps; 1h: 16 bps; 4h: 32 bps |

The suite is frozen. Phase 004 scopes may report all three components, but may
not retune thresholds, losses, costs, denominators, or pass logic after seeing
candidate outcomes.

## Batch 004-A Budget

| Field | Predeclared value |
| --- | --- |
| Candidate-family count | 1 |
| Candidate family | `CF-AVWAP-001` |
| First-branch trend detector | Simple MA crossover, fast 20 / slow 50, on domain `Close` |
| First-branch AVWAP weight | `TickVolume ** 0.75` |
| First-branch band rule | Median absolute deviation from the anchored typical-price series, multiplier 1.0 |
| Domains | 5m, 1h, 4h |
| Instruments | BTCUSD, EURUSD, USTEC, XAUUSD |
| Candidate-screening starts only after | EXP-020 substrate readiness, EXP-021 fixed-horizon reaction study, and EXP-022 original lifetime move study, if supported or explicitly ruled sufficient by governance |

The original band-target/trend-change lifetime method and brainstorming metric
book are part of Batch 004-A. Original non-baseline AVWAP concepts are
registered in `candidate-families/avwap.md`; each requires a dedicated scope and
EXP-ID before measurement. Unregistered exit overlays, position-management
rules, cross-timeframe variants, or separate signal families still require a
registry update before measurement.

## Candidate Ledger

| Candidate ID | Family | Hypothesis | EXP-ID | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/HYP-001` | Anchored VWAP on regime pivots | The frozen AVWAP definition can be built as a deterministic, look-ahead-safe event substrate with usable event coverage. | EXP-020 | SCREENED | SUPPORTED_FULL: readiness/substrate experiment supported on all three domains; not a market-edge claim; clears EXP-021/022 scoping. |
| `CF-AVWAP-001/HYP-002` | Anchored VWAP on regime pivots | AVWAP bounce events have better fixed-horizon direction-signed real-price reaction than matched non-event controls. | EXP-021 | SCREENED | SUPPORTED: fixed-horizon bounce reaction EVIDENCE_FOR on all 3 domains (+3.8/+9.1/+37.6 bps, 5m/1h/4h); component result, not a full-strategy qualification. |
| `CF-AVWAP-001/HYP-003` | Anchored VWAP on regime pivots | Under the original band-target/trend-change lifetime definition, AVWAP bounces produce favorable completed-move outcomes. | EXP-022 | SCREENED | SUPPORTED: original band-target/trend-change lifetime method supported on all 3 domains (rate diffs +23.9/+21.9/+26.4 pp, Holm p=0.0003); component result, not a full-strategy qualification. |
| `CF-AVWAP-001/HYP-004` | Anchored VWAP on regime pivots | The baseline AVWAP signal can pass standalone or portfolio-fitness qualification under the frozen suite while reporting the original strategy metric book. | EXP-023 | **SUPERSEDED (framing-corrected)** | Original REFUTED verdict (0/12 frozen-suite passes) is **valid only as a per-bar continuous-position screen**, not as a tradability test of the original selective event vehicle: a ~6%-active signal was scored against a per-bar MDE floor calibrated for ≥80%-active series (EXP-005), so the result is dominated by ~16× denominator dilution, not absence of signal. Record retained; conclusion corrected. Re-screened faithfully under an event-level method in EXP-028 (Phase 006). Review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. |

## File-Drawer Ledger

The first Phase 004 FULL candidate-screening result now exists (EXP-023, REFUTED). Component results and the full screen are recorded below.

| Date | Candidate ID | EXP-ID | Result | Disposition |
| --- | --- | --- | --- | --- |
| 2026-06-08 | `CF-AVWAP-001/HYP-001` | EXP-020 | SUPPORTED_FULL | Substrate readiness supported: all 12 cells reportable, all three domains ready, zero invariant violations, deterministic replay. Proceed to EXP-021/022 component scopes; no market-edge claim. |
| 2026-06-08 | `CF-AVWAP-001/HYP-002` | EXP-021 | SUPPORTED | Fixed-horizon bounce reaction EVIDENCE_FOR on all 3 domains (+3.8/+9.1/+37.6 bps); component result, not a full-strategy qualification. |
| 2026-06-08 | `CF-AVWAP-001/HYP-003` | EXP-022 | SUPPORTED | Original band-target/trend-change lifetime method supported on all 3 domains (rate diffs +23.9/+21.9/+26.4 pp, Holm p=0.0003); component result, not a full-strategy qualification. |
| 2026-06-08 | `CF-AVWAP-001/HYP-004` | EXP-023 | REFUTED → **SUPERSEDED (framing-corrected)** | First FULL candidate screen through the frozen suite on emitted real prices; 0/12 suite passes; effects below all frozen floors. **Corrected disposition (2026-06-08):** valid as a per-bar continuous-position screen, but **not** a tradability test of the original selective event vehicle — a ~6%-active signal scored against a per-bar floor calibrated for ≥80%-active series. Result retained in ledger; superseded by EXP-028 (faithful re-screen under an event-level method). See Phase 005 retrospective and the framing-divergence review. |
| 2026-06-09 | `CF-AVWAP-001/HYP-004-R` | EXP-028 | **EVAL_SUPPORTED** (Python-only) | Faithful re-screen of the EXP-023 baseline under the frozen EXP-027 event-level method (per-event symmetric own-exit matched-control lifetime excess; pyramids included as closer-to-original, absorbed by the regime-cluster bootstrap). All 3 domains PRIMARY EVIDENCE_FOR (+5.78/+23.38/+69.02 bps on 5m/1h/4h, CI_low>0, Holm p=0.003); audit PASS. Resolves the EXP-023 ambiguity — the negative was a per-bar-floor framing/dilution artifact, not absence of signal. Consumes **no** new slot (amended evaluation of HYP-004). First fairly-evaluated positive CF-AVWAP-001 result. **Caveat (RESOLVED 2026-06-09 by EXP-029):** measured on the canonical EXP-020 Python event substrate, not the cTrader C# per-bar streaming path; production-path parity was confirmed by EXP-029 (CONSISTENT on all 3 domains → cTrader-confirmed). See `docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md`. |
| 2026-06-09 | `CF-AVWAP-001/HYP-004-R` (parity) | EXP-029 | **CONSISTENT (EXP-028 cTrader-confirmed)** | cTrader per-bar streaming parity confirmation of the EXP-028 re-screen. The corrected C# `AvwapBounceModel` (pyramid bounces opened as independent positions; executed completion serialized) was run on cTrader and rebuilt the **same** symmetric own-exit matched-control excess estimand under the **same** frozen EXP-027 inference (hash `ea261b9ee0a8aca3`, hard-asserted == EXP-028). All 3 domains CONSISTENT (+5.79/+23.33/+69.02 vs +5.78/+23.38/+69.02 bps, EVIDENCE_FOR, Holm p=0.003); all 5 binding gates pass (verdict-match, magnitude-equiv, count ±10% incl. pyramid split, exit-parity match_rate=1.0, 5m signal-layer ≥99.8%) — entry signal, pyramid handling, and completion code all graded. Consumes **no** new slot. Audit PASS; post-governance APPROVE. EXP-028 omission closed. |
| 2026-06-10 | `CF-AVWAP-001/HYP-004-T` | EXP-030 | **INCONCLUSIVE** | Cost-bearing tradability screen of the faithful AVWAP strategy. Net per-event expectancy under CONSERVATIVE costs: 5m EVIDENCE_AGAINST (−6.74 bps, CI [−7.04, −6.38]), 1h EVIDENCE_AGAINST (−6.04 bps, CI [−11.02, −1.53]), 4h INCONCLUSIVE_SPANS_ZERO (+2.60 bps, CI [−14.87, +19.28]). Phase outcome INCONCLUSIVE — no domain clears the tradability gate. Non-binding attribution companion (net matched-control excess) remains FOR on 1h/4h. Holdout release (EXP-032) gate not passed. BTCUSD RT_cons=16 bps dominates the equal-weight mean; EURUSD-4h individually ∼positive (descriptive). All integrity guards pass (reconciliation exact, commute at machine epsilon, frozen hash verified). Audit PASS; post-governance APPROVE. |

## Phase 005 Batch (Exit Design & Branch Exploration) — HALTED 2026-06-08

**Opened:** 2026-06-08 · **HALTED:** 2026-06-08 (before Stage B/C)
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md` (HALTED; see its `retrospective.md`)
**Halt reason:** EXP-024/025 inherited an evaluation-framing defect — they diagnosed a ~6%-active event signal *within* the per-bar continuous-position referee instead of questioning whether that referee (calibrated for ≥80%-active series) is the right vehicle at all. Superseded by Phase 006. Root-cause review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.
**Slot accounting:** EXP-024 and EXP-025 were diagnostic (no candidate-screening slot). `CF-AVWAP-001/EXIT` (HYP-005, EXP-026) **never consumed its reserved slot** — it was shelved before scoping; the slot is released and the EXP-ID retired (not reused). Stage C branches remain planned-but-deferred and consume no slot until scoped under a future phase.

### Diagnostic registrations (no slot)

| Diagnostic ID | EXP-ID | Question | Status |
| --- | --- | --- | --- |
| `CF-AVWAP-001/DIAG-001` | EXP-024 | Edge-dissipation decomposition: is the EXP-021 reaction lost to holding/exit (fork a, fixable) or entry/position dilution (fork b, overlay wrong)? | **COMPLETED — RETAINED, fork leg discounted.** Original diagnostic `MIXED_OR_INCONCLUSIVE`. The fork-(b) leg compared a cumulative per-event hold return against a per-bar floor (category mismatch → low-information). **Retained findings:** the event edge is relative-not-absolute (raw hold return ~0 while EXP-021 control-excess was positive); trend-change exits cut losers, not winners (−2.79/−8.76/−17.59 bps). |
| `CF-AVWAP-001/DIAG-002` | EXP-025 | Does price react at the AVWAP line as S/R beyond a look-ahead-safe matched control (gap #4)? | **COMPLETED — INCONCLUSIVE, non-informative for HYP-001.** Metric conflates the bounce-trigger definition with the line-rejection signal (triggers cross AVWAP intrabar by definition), so it was structurally biased to a negative result. **HYP-001 (line as S/R) remains untested.** Carries zero weight in synthesis. |

### Planned candidate branches — shelved/deferred

| Candidate ID | EXP-ID | Hypothesis | Slot | Status | Note |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/HYP-005` (`/EXIT`) | EXP-026 | A single principled exit overlay lets the AVWAP baseline pass ≥1 frozen-suite component. | 0 (reservation released) | **SHELVED 2026-06-08** | Never scoped; no artifacts. EXP-026 ID retired, not reused. Exit design is premature until the evaluation vehicle is fixed (Phase 006). |
| `CF-AVWAP-001/LB` | TBD | Line Break direction regime detector. | 1 | **DEFERRED** | Reconsidered only after the EXP-028 faithful re-screen is read. |
| `CF-AVWAP-001/MB` | TBD | Market Bias regime detector. | 1 | **DEFERRED** | As above. |
| `CF-AVWAP-001/ATR` | TBD | ATR pivot-reversal regime detector. | 1 | **DEFERRED** | As above. |
| `CF-AVWAP-001/ANCHOR` | EXP-047 | Significant-pivot anchor vs running-extreme anchor (gap #1). | 1 (reservation released — never consumed) | **CLOSED-MEASURED (as ratified, Phase 013)** | Exercised by the Phase 013 TRAIN-only move-size diagnostic (EXP-047, DIAG-007, 0 slots): ANCHOR_MOVE_FLAT — the ratified k=1.0 ATR-prominence rule coincides with the running extreme in ~95–99% of regimes; no MFE shift in any of 51 cells. Re-opening requires a new D0 with a demonstrably binding prominence threshold. |

## Phase 006 Batch (Evaluation Correction)

**Opened:** 2026-06-08
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/design.md`
**Purpose:** Fix the evaluation vehicle that Phases 004/005 mis-applied, then re-screen the faithful selective AVWAP strategy under it. The strategy is unchanged; the **evaluation method** is the corrected/amended item. The frozen per-bar suite is unchanged and remains the standard for ≥80%-active candidates — it is simply not the vehicle for this sparse event strategy.
**Slot accounting:** EXP-027 is a methodology/calibration experiment (no candidate-screening slot). EXP-028 does **not** consume a new candidate-family slot — it corrects the `CF-AVWAP-001/HYP-004` baseline screen under a fit-for-purpose method (amended evaluation, unchanged strategy). EXP-029 (appended 2026-06-09) is a cTrader per-bar streaming **parity confirmation** of the EXP-028 re-screen and likewise consumes **no** new slot — same `CF-AVWAP-001/HYP-004-R` item; the only changes are the strategy's execution path (cTrader C# robot vs. Python re-analysis) and a C# pyramid-position correction. See `docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/EXP-028-omission.md`.

| ID | EXP-ID | Question | Slot | Status | Precondition |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/METHOD-001` | EXP-027 | Does a predeclared event-level evaluation method (per-event expectancy + equity-curve vs buy-hold; EXP-021/022 control/bootstrap/Holm inference) have controlled error and recovery on a sparse (~6%-active) event regime? | 0 (methodology) | **METHOD_VALID** | All 3 domains FPR-controlled (max 0.034), finite event-level MDE (5m=1/1h=4/4h=32 bps), determinism PASS. Frozen for EXP-028/029. |
| `CF-AVWAP-001/HYP-004-R` | EXP-028 | Under the frozen EXP-027 method, does the faithful selective AVWAP strategy show event-level edge on ≥1 domain (first-70% analysis set)? | 0 (re-screen of HYP-004; amended evaluation) | **EVAL_SUPPORTED → cTrader-confirmed (EXP-029)** | All 3 domains PRIMARY EVIDENCE_FOR (+5.78/+23.38/+69.02 bps, CI_low>0, Holm p=0.003). Strategy identical to EXP-023 baseline; holdout sealed; no tuning. **cTrader per-bar parity CONFIRMED by EXP-029 (2026-06-09): CONSISTENT on all 3 domains, all 5 binding gates pass.** |
| `CF-AVWAP-001/HYP-004-R` (parity) | EXP-029 | Does the corrected C# strategy on cTrader per-bar streaming reproduce EXP-028's event-level findings? | 0 (parity confirmation of EXP-028; no new slot) | **CONSISTENT (EXP-028 cTrader-confirmed)** | Parity CONSISTENT on all 3 domains: corrected C# `AvwapBounceModel` (pyramids opened as independent positions; executed completion serialized) run on cTrader per-bar streaming reproduced EXP-028 PRIMARY excess (+5.79/+23.33/+69.02 vs +5.78/+23.38/+69.02 bps, all EVIDENCE_FOR, Holm p=0.003). All 5 binding gates pass — verdict-match, magnitude-equiv, count ±10% incl. pyramid, exit-parity match_rate=1.0, 5m signal-layer ≥99.8% — so entry signal, pyramid handling, and completion code are all graded. Frozen hash == EXP-028; reconciliation_bad=0; holdout sealed. Audit PASS; post-governance APPROVE. EXP-028 omission closed. |

### Deferred out of Phase 005

| Branch | Reason |
| --- | --- |
| `CF-AVWAP-001/ALPHA` | Tick-volume exponent sensitivity. The Phase 004 failure was not localized to this parameter; low expected information now. |
| `CF-AVWAP-001/BAND` | Band-multiplier sensitivity. Same rationale. |
| `CF-AVWAP-001/MA-DOMAIN`, `CF-AVWAP-001/XTF` | Remain registered; out of Phase 005 scope. |

Negative, blocked, and inconclusive outcomes for any Phase 005 item stay in the file-drawer ledger.

## Phase 007 Batch (Tradability & Edge Isolation)

**Opened:** 2026-06-09
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md`
**Phase 006 close recorded:** `EVAL_SUPPORTED`/cTrader-confirmed (EXP-027 METHOD_VALID; EXP-028 PRIMARY EVIDENCE_FOR on all 3 domains, +5.78/+23.38/+69.02 bps, Holm p=0.003; EXP-029 CONSISTENT parity). All Phase 006 effects are **gross** matched-control excess; tradability and edge attribution are unanswered — that is this batch.
**Purpose:** (1) determine whether the Phase 006 per-event edge survives a predeclared event-level cost/slippage model (EXP-030); (2) decompose the measured excess into entry-timing vs exit-rule contributions (EXP-031). EXP-030 and EXP-031 are **mutually independent** — neither blocks the other, and EXP-031 is **not cancelled** by an EXP-030 failure (operator decision 2026-06-09: mechanism information is retained regardless of tradability).
**Slot accounting:** EXP-030 is a **cost-bearing tradability screen** of the already-registered `CF-AVWAP-001/HYP-004-R` baseline — unchanged trade logic, added cost layer only — and consumes **no** new candidate-family slot. EXP-031 is an **edge-decomposition diagnostic** (no candidate-screening slot). **EXP-032 (holdout release) is DEFERRED and NOT registered** — it becomes admissible only if EXP-030 returns tradability EVIDENCE_FOR on ≥1 domain, and requires its own checkpoint and governance before registration.

| ID | EXP-ID | Question | Slot | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/HYP-004-T` | EXP-030 | Under a predeclared per-event cost/slippage model (conservative variant binding), does the faithful selective AVWAP strategy retain positive **net** per-event expectancy on ≥1 domain (first-70% analysis set)? | 0 (cost layer on registered HYP-004-R baseline) | **COMPLETED — INCONCLUSIVE** | **Holdout-release gate (EXP-032) NOT passed.** 5m/1h CONSERVATIVE EVIDENCE_AGAINST (net CIs entirely <0; gross absolute ≪ RT_cons), 4h INCONCLUSIVE_SPANS_ZERO (CI half-width ~17 bps, n=187). EURUSD-4h individually ∼positive net (descriptive, non-binding). The non-binding attribution companion (net matched-control excess) remains FOR on 1h/4h — the Phase-006 gross edge is not overturned, but costs dominate the absolute P&L leg. Audit PASS; post-governance APPROVE. Family review per Phase 007 design §9 triggered. |
| `CF-AVWAP-001/DIAG-003` | EXP-031 | Of the EXP-028 measured per-event excess, how much is attributable to AVWAP bounce **entry timing** vs the EXP-022 band-target/trend-change **exit rule**? | 0 (diagnostic) | **ISOLATION_READ_UNRESOLVED** | Entry-dominant at H=6 (PRIMARY) on all domains, exit-dominant at H=1 on all domains — horizon contradiction triggers predeclared unresolved outcome. Audit PASS (NaN fix applied, determinism replay passed). Classification unchanged by fix. See `python/experiments/EXP-031/`. |
| — (holdout release) | EXP-032 | *(deferred)* One-shot holdout confirmation of the event-level edge. | — | **DEFERRED / NOT REGISTERED** | Admissible only on EXP-030 EVIDENCE_FOR (≥1 domain); own checkpoint + governance required. The global holdout is never released to confirm a gross edge. |

### Carried, not worked (Phase 007)

| Item | Status |
| --- | --- |
| HYP-001 (AVWAP line as direct S/R) | OPEN, explicitly NOT confirmed by EXP-028/029 (design §8); parallel/fallback mechanism branch; not worked this phase. |
| Stage-C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) | DEFERRED; reconsidered via family review if EXP-030 fails. |
| `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` | Remain deferred/registered; no slot consumed. |

## Phase 008 Batch (Clinical Tradability: Selectivity, Instrument Selection, Capture Efficiency)

**Opened:** 2026-06-10
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`
**Phase 007 close recorded:** NOT_TRADABLE (EXP-030 INCONCLUSIVE — 5m/1h net EVIDENCE_AGAINST, 4h INCONCLUSIVE_SPANS_ZERO; holdout gate not passed. EXP-031 ISOLATION_READ_UNRESOLVED — entry-dominant at H=6, exit-dominant at H=1 on all domains).
**Purpose:** test the three admissible levers for a real-but-cost-dominated edge — selectivity (conditioning), instrument selection (per-instrument verdicts), capture efficiency (fixed-horizon exit + pyramid policy) — on the existing entry substrate, under the **frozen EXP-030 CONSERVATIVE cost model plus a predeclared financing layer**. Anti-overfitting backbone: TRAIN-only characterisation with mechanical selection rules; one-shot TEST confirmation per registered variant. Two-speed gating: lenient G1 to continue exploration, strict G2 to spend the one-shot holdout.
**Data-dependent design disclosure:** the A1 declared-cell set, the B2 pyramid-policy menu, and the B2 expectation set derive from EXP-030/031 disclosure reads (per-instrument breakeven map, `pyramid_net_split`, exit-substitution profile). Recorded per design §7.4.
**Slot accounting:** EXP-033/EXP-035 are diagnostics (0 slots). EXP-034 is a per-instrument estimand of the registered `CF-AVWAP-001/HYP-004-R` baseline + frozen cost layer (0 slots). EXP-036 `/COND` and EXP-037 `/EXIT-FH` are **reserved** Tier-B registered variants (1 candidate slot each), activated only on G1 qualification. **EXP-032 (holdout release) remains DEFERRED / NOT REGISTERED**, admissible only behind strict gate G2 (net CI_low > 0, Holm) with its own checkpoint and governance.

**Revision R1 (2026-06-10, pre-execution adversarial review of EXP-037/038 — design §11):** (1) **Phase-level G2 family:** all realized binding one-sided TEST p-values (≤4: EXP-037's 3 cells + EXP-038's 1 cell) form ONE Holm family at α=0.05, adjudicated mechanically in `G2-gate-review.md` after both runs — neither experiment declares `g2_satisfied` itself; the two routes are dependent (near-identical EURUSD-4h events under different exits) and per-route α would have run union FPR near 2α. (2) **Small-n calibration:** each binding TEST cell carries a pre-TEST synthetic-null calibration of the frozen bootstrap at matched cluster structure, with the mechanical margin `m = max(0, Q95 null ci_low_1s)` on the binding bound. (3) **EXP-037's H\* tie-break is second-generation data-dependent:** it replaced A2's one-SE rule after EXP-033 disclosed `h_star_stable=false` and the full N(H) curve — recorded as a design §5/B2 amendment (R1.4), selection remains TRAIN-only/mechanical. (4) **EXP-038 relabeled** "TEST-stratum temporal-stability subsample check" (its TEST events are a dependent subsample of the disclosures that selected the cell); holdout nomination additionally requires TRAIN-stratum directional consistency, and a LOCO fragility diagnostic accompanies any pass. (5) One TEST boundary convention for the phase (1-minute-row timestamp, `train_end_ts`).

**G1 gate outcome (2026-06-10, `docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/G1-gate-review.md`):** Tier A complete (EXP-033/034/035 all post-governance APPROVE). **G1 = QUALIFIED** (not FLAT). (a) G1-A3 (EXP-035): **0 conditioning dimensions qualify** → `/COND` (EXP-036) does **not** activate; its 1 slot is **unused** (ID reserved-inactive, not retired). (b) G1-A1 (EXP-034): **EURUSD-4h** A1 strict pass → routes to a one-shot TEST-stratum confirmation (new **EXP-038**, 0 slots, §8.4); USTEC-4h continues leniently only. (c) G1-B2 (EXP-033): **4h** eligible (TRAIN FH grid max +45.79 bps) → `/EXIT-FH` (EXP-037) **activates** (1 slot consumed), 5m/1h ineligible. **Tier-B docket: EXP-037 (`/EXIT-FH` 4h, 1 slot) + EXP-038 (EURUSD-4h A1-cell TEST confirmation, 0 slots).** Both scoped Stage 1, 2026-06-10; both are one-shot TEST reads requiring full predeclaration before any TEST row is read. Slot budget: 1 of ≤2 Tier-B slots consumed.

| ID | EXP-ID | Question | Slot | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/DIAG-004` | EXP-033 | TRAIN-only horizon sweep: where does the entry/exit attribution s_entry(H) cross over (H ∈ {1,2,3,4,6,8,12,24}), and what is the FH(H) net curve per domain? | 0 (diagnostic) | **COMPLETE — MEASUREMENT_COMPLETE (APPROVE, 2026-06-10)** | Closes EXP-031's unresolved read. H\*_d frozen by mechanical one-SE rule (smallest H within one bootstrap SE of grid max); feeds B2. If grid max ≤ 0 on a domain, B2 does not run there. |
| `CF-AVWAP-001/HYP-004-TI` | EXP-034 | Does any declared instrument×domain cell retain positive **net** per-event expectancy under frozen CONSERVATIVE costs + predeclared financing (EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 / BTCUSD 10.0 bps/day, adverse-side)? | 0 (per-instrument estimand of registered baseline + frozen cost layer) | **COMPLETE — A1_STRICT_PASS / TEST REQUIRED (APPROVE, 2026-06-10)** | **Declared family FIXED by D0 (mechanical rule: EXP-030 net_cons point > 0): EURUSD-4h (primary) → USTEC-4h → XAUUSD-1h, fixed-sequence at one-sided α=0.05 (FWER 0.05; replaces the design's 6-cell/Holm default — see D0 §1.1–1.2).** 5m and BTCUSD cells excluded by break-even map; all 12 cells' descriptive CIs disclosed. Power statement in scope: USTEC-4h expected INCONCLUSIVE (n=36), XAUUSD-1h expected fail; the live cell is EURUSD-4h. **Amended 2026-06-10 (F01/F02):** binding rule is a genuine one-sided α=0.05 (5th-percentile lower bound + bootstrap p); a strict pass is **necessary-but-not-sufficient** for G2 — it routes the cell into a one-shot Tier-B TEST-stratum confirmation (0 slots), and only that TEST result opens holdout admissibility (design §8.4 as amended). |
| `CF-AVWAP-001/DIAG-005` | EXP-035 | TRAIN-only conditioning characterisation: does per-event **net** expectancy vary materially and stably across %completion-to-target at confirmation, session (UTC tertiles of day), and trailing-vol regime? | 0 (diagnostic) | **COMPLETE — CHARACTERISATION_DELIVERED, 0 qualified dims (APPROVE, 2026-06-10)** | Predeclared bins; outcome = net expectancy (never hit rate); G1-A3 qualification per design §8.1 (SNR ≥ 1 spread + top-bin net > 0 + monotone/omnibus + split-half stable + Holm 3 dims/domain at α_G1=0.10). Hard no-selection rule inside A3. |
| `CF-AVWAP-001/COND` | EXP-036 (provisional) | Does a TRAIN-frozen conditioned variant (≤1 rule per G1-qualifying dimension) retain positive net expectancy on one-shot TEST confirmation? | **1 (reserved, UNUSED)** | **NOT ACTIVATED (G1-A3 did not qualify, 2026-06-10)** | EXP-035 returned 0 G1-qualified dimensions (all 9 cells fail materiality — best bin net ≤ 0). `/COND` does not open this phase; slot unused, ID reserved-inactive (not retired). |
| `CF-AVWAP-001/EXIT-FH` | EXP-037 | Does a fixed-horizon-exit variant (H\* on 4h; pyramid policy ∈ {all, first-leg-only, pyramid-legs-only} TRAIN-frozen by one-SE rule) retain positive net expectancy on one-shot TEST confirmation? | **1 (consumed)** | **ACTIVATED + SCOPED (Stage 1, 2026-06-10; revised R1, pre-execution)** — G1-B2 qualified 4h | 4h only (EXP-033 TRAIN FH grid max +45.79 > 0; 5m/1h ineligible). H\* fragility (`h_star_stable=false`) handled by a **TRAIN tie-break over H ∈ {4,6,8,12}** (stability filter: full + both split-halves net > 0; max-min select; smaller-H tiebreak; computed on the spill-contained TRAIN subset per R1.5) → **single** binding H\* on TEST. **The tie-break is SECOND-GENERATION DATA-DEPENDENT** (replaced A2's one-SE rule after the EXP-033 disclosure read; authorized by design amendment R1.4). Pyramid policy TRAIN-frozen with TEST-cell entry-attribute feasibility (R1.6). Declared 4h TEST family {EURUSD, USTEC, XAUUSD}; BTCUSD excluded. Binding: raw one-sided p's enter the **phase-level Holm family (R1.1)**; bound must clear the calibrated margin (R1.2). Boundary = 1-minute-row timestamp (R1.3). |
| `CF-AVWAP-001/HYP-004-TI-TEST` | EXP-038 | Does EURUSD-4h's A1 strict pass survive a one-shot read on the held-back TEST stratum (last 30% of analysis set) under the **same registered baseline estimand** (BTC exit) + frozen costs/financing? | 0 (TEST-stratum **temporal-stability subsample check** of an A1 strict-pass cell; §8.4 route, relabeled R1.7) | **REGISTERED + SCOPED (Stage 1, 2026-06-10; revised R1, pre-execution)** — from EXP-034 EURUSD-4h `SEQUENCE_PASS_ALPHA05` | New ID (no reuse). Single cell. **Not an independent out-of-sample read:** TEST events are a dependent subsample of the disclosures that selected the cell (R1.7). Stratum membership by causal trigger timestamp (1-minute-row boundary). Power statement: TEST n≈12 → INCONCLUSIVE is a likely, honest outcome. Binding: raw one-sided p enters the **phase-level Holm family (R1.1)**; bound must clear the calibrated margin (R1.2); LOCO fragility diagnostic accompanies any pass; holdout nomination additionally requires TRAIN-stratum directional consistency. Only the G2-gate-review adjudication (not the in-sample A1 pass) can open EXP-032. |
| `CF-AVWAP-001/HOLDOUT-B` | EXP-032 | Does Package B (EURUSD-4h, FH H\*=12 all_legs exit, frozen CONSERVATIVE costs + 0.6 bps/day financing) retain positive net per-event expectancy on the global holdout stratum (final 30%, first sanctioned read)? | **holdout shot (1-of-1, programme-level) — SPENT 2026-06-10** | **COMPLETE — HOLDOUT_INCONCLUSIVE (shot SPENT, 2026-06-10)** — executed under checkpoint `2026-06-10-009-avwap-holdout-release`; audit PASS | n=27 holdout events: net **+20.60 bps**, two-sided CI [−0.39, +42.15], `ci_low_1s` **2.71 ≤ m_cell 4.32** (boot_p 0.029 passed; margin condition failed) → INCONCLUSIVE_SPANS_ZERO. Pre-outcome calibration measured uncorrected null FPR 0.0715 at this structure — the margin prevented an over-claim. All integrity guards PASS (lineage reconciliation exact; EXP-037 TEST anchor reproduced to 3.6e-7 bps; freeze-before-outcome + no-second-read enforced; determinism replay drift 0.0; only the EURUSD file opened). **Consequences (locked):** no second holdout read ever for Package B or A; EXP-037/038 TEST evidence stands but is permanently non-upgradable; EURUSD holdout contaminated-by-disclosure for any EURUSD-4h event-level claim; BTCUSD/USTEC/XAUUSD seal intact. BTC-exit companion +2.35 bps (non-binding, never promotable). Routing: Tier C per Phase 008 design §9. |

### Carried, not worked (Phase 008)

| Item | Status |
| --- | --- |
| HYP-001 (AVWAP line as direct S/R) | OPEN; Tier-C parallel science (Phase 007 design §8 framing preserved); never gates Tiers A/B. |
| Stage-C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) | DEFERRED; Tier-C fallback, opened only on Phase 008 FLAT or CHARACTERISED_NOT_CONFIRMED outcomes. |
| `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` | Remain deferred/registered; no slot consumed. |

## Phase 010 Batch (Exit Exploration, Line-S/R Science, New-Universe Groundwork)

**Opened:** 2026-06-10
**Closed:** 2026-06-11 — **EXIT_FLAT** (Track A) / **HYP-001 INCONCLUSIVE** (Track B); INFR-002 carried OPEN. Operator decision (design §9): Phase 011 proceeds on the Phase 008 frozen package (FH H\*=12, all_legs); Stage-C family review deferred until the new universe can power it. File-drawer entries: EXP-039 FLAT (negative screen, retained); EXP-040 INCONCLUSIVE (mechanism record, HYP-001 stays OPEN); EXP-041 reserved-inactive (slot unused, never activated).
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md`
**Phase 009 close recorded:** HOLDOUT_INCONCLUSIVE, shot SPENT (EXP-032: n=27, net +20.60 bps, ci_low_1s 2.71 ≤ m_cell 4.32). Locked consequences: no second holdout read ever for any `CF-AVWAP-001` package; EXP-037/038 TEST evidence permanently non-upgradable; EURUSD holdout contaminated-by-disclosure; BTCUSD/USTEC/XAUUSD seal intact.
**Purpose:** (1) `/EXIT-X` — screen a registered family of structurally distinct exit rules on the unchanged AVWAP bounce-entry substrate (TRAIN-only, frozen EXP-030 CONSERVATIVE costs + Phase 008 financing, references R-BTC and R-FH(12) on 4h), with at most one one-shot TEST confirmation of ≤2 qualifying exits; a G2 pass freezes a hash-pinned carry-forward package — **no holdout consequence exists or is implied**. (2) HYP-001 — direct AVWAP-line S/R test in the Phase 007 design §8 confound-free approach-conditioned framing (mechanism science; never gates Track A). (3) INFR-002 — cTrader 1-minute collection for the new universe with holdout sealed at first touch; no Phase 010 analysis of new-universe data.
**Operator decisions recorded (2026-06-10, pre-design):** HYP-001 runs as parallel science; the new-asset universe is the programme's confirmation path (existing-asset results accepted as TEST-capped); exit-screen domains 4h primary / 1h secondary with 5m retired as a primary signal source; multi-timeframe model deferred to Phase 011 behind its own EXP-027-analog method calibration.
**Data-dependent design disclosure (per Phase 008 §7.4 convention):** the exit-screen domain choice, the surviving-instrument sets (BTCUSD excluded by the EXP-030/D0 break-even map), the R-FH(12) reference (EXP-037 freeze), the dual-mechanism design input (EXP-031/033 crossovers), and the dropped unconditional time-stop (duplicates the EXP-033/037 FH sweep) all derive from prior-phase disclosure reads.
**Slot accounting:** EXP-039 diagnostic (DIAG-006, 0 slots). EXP-040 mechanism measurement of the registered HYP-001 (0 candidate slots). EXP-041 `/EXIT-X` **reserved** (1 slot), activated only on G1 qualification; if Track A is FLAT the slot is unused and the ID reserved-inactive. INFR-002 carries no EXP-ID (infrastructure; VAL-class admission required before any new-universe data enters an experiment).
**Amendments (2026-06-10, pre-execution adversarial review; design §11):** EXP-039 — qualification populations pinned (per-candidate containment; reference-intersection gaps; ranking and cap on the within-domain qualifier-intersection population, rank reversals escalate to operator adjudication before the EXP-041 freeze); EURUSD-share + ex-EURUSD disclosure columns added. EXP-040 — binding Holm family fixed at the 2 pooled domain contrasts (per-instrument cells descriptive); AGAINST-as-immaterial symmetrized (CI_high < +2 pp ∧ CI_low ≤ 0); power statement added (structural + ordering-enforced realized counts file); censoring-sensitivity bracket added; matching covariates pinned (direction/vol/speed terciles; band-width tercile balance-reported); moving-vs-static kinematic confound and unmatched price-stretch regime carried as verbatim caveats. No TRAIN/analysis-set outcome was read before these amendments. **2026-06-11 (design §11/8, pre-read):** EXP-040 gains a secondary **moving-copy** control arm (`AVWAP(t) + δ·BW(t)`, identical construction/grid/lifetime, own seed); the AVWAP-vs-moving contrast Δ_m is descriptive only (bootstrap CI, no permutation, no Holm) — the binding family remains the 2 pooled static-control contrasts; predeclared joint Δ/Δ_m reading recorded in the design.

### Registered exit family (frozen at EXP-039 scope freeze; bar-close trigger and bar-close fill only)

| Exit ID | Definition | Parameters (declared grid) | Composition |
| --- | --- | --- | --- |
| E1 | HA Harami size exhaustion (global-techniques Pattern 1, direction-independent) on domain-bar HA values | none | Full exit-rule replacement |
| E2 | HA trailing reference — real close crosses prior bar's `min(HAOpen,HAClose)` (long) / `max(HAOpen,HAClose)` (short); bar-close market-style trigger | none (stop-style variant deferred) | Full exit-rule replacement |
| E3 | Last-X high/low trailing — real close crosses prior-X domain bars' lowest low (long) / highest high (short) | X ∈ {3, 5, 8} | Full exit-rule replacement |
| E4 | Adverse-band stop — band-target leg retained; trend-change leg replaced by exit when real close crosses the adverse-side MAD band (multiplier 1.0, registered band definition) | none | Target kept; failure leg replaced |
| E5 | Target-conditional time-stop — band-target leg retained; trend-change leg replaced by hard exit after H_ts domain bars without target hit | H_ts ∈ {8, 12, 24} | Target kept; failure leg replaced |

**Dropped (disposition recorded):** the unconditional time-stop — it is the FH exit already swept in EXP-033 and TEST-read in EXP-037; re-registering it would respend a slot on a tested mechanism. Pyramid policy is fixed at **all_legs** (Phase 008 frozen winner); policy variation is out of scope this phase.

| ID | EXP-ID | Question | Slot | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/DIAG-006` (`/EXIT-X` screen) | EXP-039 | TRAIN-only: does any registered exit E1–E5 deliver per-event net expectancy (frozen costs + financing) that is positive on every surviving instrument, beats the better reference (4h: max(R-FH(12), R-BTC); 1h: R-BTC), and is split-half stable, on 4h or 1h? | 0 (diagnostic) | **COMPLETE 2026-06-10 — MEASUREMENT_COMPLETE, FLAT** | 0/10 cells qualify under §8.1. 4h: R-FH(12) +37.3 bps is the binding bar; best candidate E2 +31.9 bps (gap −5.4 bps ≈ 0.5 SE, power-limited not mechanism-resolved); E3(8) split-half sign flip caught by criterion (iii). 1h: all candidates and R-BTC net-negative — structurally non-viable on this substrate (third independent confirmation after EXP-030/033). Determinism PASS; reconciliation to EXP-022/033 at machine precision. Audit PASS. File-drawer: negative screen retained. |
| `CF-AVWAP-001/HYP-001` (measurement) | EXP-040 | Does `P(bounce \| approach to AVWAP)` exceed `P(bounce \| approach to matched non-AVWAP control levels)` on 1h/4h (analysis set, gross, real prices)? | 0 (mechanism science) | **COMPLETE 2026-06-10 — INCONCLUSIVE** | Binding pooled contrasts: 1h Δ=+1.55 pp CI[−4.52,+8.43] Holm p=0.585 (INCONCLUSIVE_SPANS_ZERO); 4h n=50/22 < 100/arm floor (BELOW_FLOOR_NO_VERDICT). Moving-copy arm (design §11/8, descriptive): 1h Δ_m=+3.41 pp [−1.23,+8.35] — kinematic confound does not explain the premium; 4h Δ_m≈0 — negative static Δ was kinematic artifact. HYP-001 remains OPEN; permanent mechanism record per §8.3; no re-parameterization within this scope. Audit PASS. |
| `CF-AVWAP-001/EXIT-X` | EXP-041 (provisional) | Do the ≤2 TRAIN-frozen qualifying exits retain positive net expectancy on a one-shot TEST read (Holm phase family + R1.2 calibrated margins)? | **1 (reserved)** | **RESERVED-INACTIVE (2026-06-11)** — G1 never opened (EXP-039 FLAT); slot unused; no TEST row read this phase; ID never reusable | Freeze-before-TEST (`frozen_selection.json`, hash-pinned); R1.2 matched-structure null calibration per cell; R1.3 boundary; R1.6 recovery semantics; binding adjudication in the checkpoint's `G2-gate-review.md`. Every TEST cell carries the prior-read disclosure (Phase 008 read this stratum under FH/BTC exits) and the EURUSD TEST-cap note. G2 pass ⇒ frozen carry-forward package only — **no holdout read**. |
| — (infrastructure) | INFR-002 | Collect 1-minute time bars for GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (USTEC already local). | — | **COMPLETE 2026-06-11 — ADMITTED (VAL-003 PASS)** | All 13 instruments collected (`run-infr002-collection.sh`, Mode=TimeBars; realized coverage 2023-01-03 → 2026-06-11 per file). **VAL-003 PASS:** 0 FAIL / 0 INCONCLUSIVE across all per-instrument checks (98 each); 24/24 negative controls detected; VAL-001 rev. 3 suite unchanged. **Disclosures:** (1) DE30 coverage truncated — broker m1 history ends 2026-01-16 13:11 (~5 months short of the other 12); its 70/30/holdout boundaries derive from its own realized timeline; operator may re-collect under an alternative broker symbol before first analytical use. (2) A pre-fix duplicate GBPUSD file (content-identical, verified row-for-row) was removed 2026-06-11; the surviving file was validated. **Holdout sealed per file at first touch:** final 30% of each file's chronologically ordered rows is global holdout and remains sealed (no new-universe row read for analysis at admission; Phase 011 subsequently read new-universe first-70% rows for readiness/calibration/training). |

### Carried, not worked (Phase 010)

| Item | Status |
| --- | --- |
| Stage-C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) | DEFERRED (operator decision 2026-06-11, post-EXIT_FLAT): family review postponed — Stage-C variants on the existing universe face the same ~86-event 4h TRAIN power wall (EXP-039 SEs 7–30 bps); revisit when the new universe can power it. |
| `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` | Remain deferred/registered; no slot consumed. |
| Stop-style/intrabar exit fills | DEFERRED behind a dedicated fill-rule method validation. |
| Multi-timeframe model (signal 4h / execution 5m–30m) | CLEARED for Phase 011 (operator decision 2026-06-11): builds on the Phase 008 frozen package (FH H\*=12, all_legs — Phase 010 produced no successor exit); still gated on an EXP-027-analog method calibration for any new execution domain before binding reads. |
| EXP-036 `/COND` | Reserved-inactive (Phase 008); not reopened. |

## Phase 011 Batch (Per-Instrument Foundation & Strategic Reset)

**Opened:** 2026-06-11 (D0 desk work; EXP-042 Track A0 data contact later set aside as FRAMING_ERROR)
**Closed:** 2026-06-11 — **FOUNDATION_NON-TUNABLE** (G2 FAIL, `G2-gate-review.md`): EXP-045 delivered empty membership (0/37 vs P5); Tracks C/D never opened; the registered `PORTFOLIO-011` and `TOPK-011` TEST families were never activated and no slot or read was consumed; the EXP-018 P1 threshold predeclaration is unspent (frozen record only). File-drawer entries: EXP-042 FRAMING_ERROR (set aside), EXP-045 EMPTY MEMBERSHIP (negative training result, retained). TEST-read ledger unchanged from the D0 backfill. Retrospective: `docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/retrospective.md`.
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/design.md`
**Phase 010 close recorded:** EXIT_FLAT / HYP-001 INCONCLUSIVE; INFR-002 closed by VAL-003 PASS 2026-06-11 (13 new instruments admitted; DE30 truncated-coverage disclosure).
**Purpose:** determine whether AVWAP — with the **frozen baseline entry** (arm/trigger at the AVWAP line; ~~data-selected global band multiplier, Track A0~~ removed 2026-06-11, FRAMING_ERROR) and **per-instrument-trained exits** (Track B, 17 instruments × {1h, 2h, 4h} = 51 cells; band multiplier selected per cell as an exit parameter) — is tradable as a portfolio (Track C, EXP-018 vs Donchian(20), PRIMARY) and on any standalone top-5 cell (Track D, Holm-5, SECONDARY). Inference inverted vs Phases 007–010: membership decided on TRAIN; **phase TEST budget ≤ 6 one-shot reads** (1 portfolio + ≤5 cells), governed by the new TEST-read ledger.
**New governance:** `docs/signal-registry/test-read-ledger.md` materialized 2026-06-11 (2-counted-read lifetime cap per stratum; EURUSD-4h AT CAP via EXP-037/038; portfolio reads enter as disclosures). Predeclarations fixed at D0: `checkpoints/2026-06-11-011-per-instrument-foundation/D0-predeclarations.md` (P1 EXP-018 threshold first; P2 17-instrument cost model — records the §7.3 EURUSD RT transcription-error correction, EXP-030 CONSERVATIVE 3.0 bps is authoritative; P3 A0 horizons/floor now moot; P4 stability floor; P5 G2 composition; P6 MAD grid; P7 2h `min_coverage=0.90`; P8 DE30 as-is with disclosure). **G0 passed; no Track A/B read before G0. Track A0 was removed after EXP-042 and is not a current gate.**
**Band-variant registration — SUPERSEDED 2026-06-11 (FRAMING_ERROR):** the original registration below is rescinded. Post-execution review of EXP-042 (`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`) established that the band multiplier was always an **exit parameter** (favorable/adverse target levels frozen at trigger; registry `/BAND` branch is exit/structural) — an entry-level band selection has no object, so Track A0 is removed and no `/BAND` slot was consumed. The **entry-rule amendment is rescinded**: Phase 011 events use the frozen baseline arm/trigger at the AVWAP line, identical to Phases 004–010 (the `xen.avwap` parameterization is retained, defaults reproduce the baseline bit-for-bit; the non-default arm rule is unused). The band multiplier is exercised exclusively in **Track B Family 2** (per-cell MAD-band-target exit, P6 grid {0.5,0.7,1.0,1.4,2.0,2.8,4.0,5.7}), where it always belonged — TRAIN-only, 0 slots, per the existing Track B registration. Entry signal MA(20,50) and exponent 0.75 remain deliberately frozen (`/ENTRY`, `/ALPHA`, `/MA-DOMAIN` deferred). With the baseline entry unchanged, design §7.5 entry-population non-comparability no longer applies. *(Original registration, retained for the record: Track A0-selected global band over {1.0, 1.5, 2.0, 2.5, 3.0}, working candidate 2.0, `/BAND` 1 slot on selection ≠ 1.0, arm-at-adverse-band entry rule — see the Phase 011 design amendment log.)*
**Data-dependent design disclosure (Phase 008 §7.4 convention):** the rescoping itself derives from the Phases 004–010 record (universal-parameter discovery); the 5m retirement from EXP-030/033/039; the FH grid geometry and stability-plane method from the EXP-033/037 `h_star_stable=false` disclosure; the EURUSD-4h cap and EXP-037/038 tallies from the ledger backfill; band working-candidate 2.0 from prior band-width observations. None of these is Phase-011 data contact.
**Slot accounting:** ~~Track A0 scan~~ (removed; EXP-042 consumed 0 slots), Track A readiness/calibration/parity analogs, and Track B 51-cell exit training are 0-slot (TRAIN-only / diagnostic). Track C is the registered EXP-018 portfolio read (1 one-shot TEST read; primary endpoint). Track D is a registered ≤5-read one-shot TEST family (Holm-5; at-cap strata ineligible — currently EURUSD-4h). EXP-IDs assigned at Stage-1 scoping (next free ID per `python/experiments/INDEX.md`; EXP-036/EXP-041 remain reserved-inactive, never reused).

| ID | Track | Question | Slot / TEST reads | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| D0 (this entry) | Tier 0 | Registry amendment, ledger, cost model, predeclarations. | 0 / 0 | **CLOSED 2026-06-11 — G0 PASS (operator-ratified)** | All §8.5 items frozen in `D0-predeclarations.md`; EXP-018 threshold fixed first; Track A/B data contact authorized. Track A0 later removed; P3 retained as moot record only. |
| `CF-AVWAP-001/BAND` (A0 selection) | A0 (**REMOVED**) | Which global band ∈ {1.0,1.5,2.0,2.5,3.0} best ranks by gross-per-event at H=8 across 51 TRAIN cells? | 0 (no slot consumed) / 0 TEST | **EXP-042: MEASUREMENT_COMPLETE — FRAMING_ERROR (set aside 2026-06-11)** | Band applied as entry filter; it was always an exit parameter — measured a filtered deep-pullback subpopulation; band=1.0 "selection" was event-availability artifact; DEGENERATE_FLOOR adjudication moot, freeze never granted. Zero weight in Phase 011. Track A0 removed; entry-rule amendment rescinded (baseline arm/trigger restored); band lives in Track B Family 2. Code/results retained (file-drawer, negative-process record). Review: `docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`. |
| Track A readiness (EXP-020-analog) — **EXP-043** | A | Substrate readiness for the frozen baseline entry on all 51 cells (first-ever 2h construction): event determinism, construction integrity, domain artifacts, realized TRAIN event rates. | 0 / 0 | **COMPLETE 2026-06-11 — READINESS_DELIVERED, audit PASS** | **G1 leg (i) SATISFIED, 50/51 READY** ([G1-gate-review.md](../experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/G1-gate-review.md), adjudication 1 of 2): 0 invariant violations, 0 determinism failures, no substrate alert. **JP225-2h NOT_READY** (frozen >25% 2h dropped-fraction gate, 0.2566 — coverage outcome, not a generator defect) → excluded from Track B with record; Track B grid is **50 cells**. Realized TRAIN counts (1h 151–273, 2h 86–143, 4h 32–86; all ≥30 floor) supersede design §7.4 power figures and the set-aside EXP-042 statement. Disclosures: 11/17 4h cells at 32–55 events; index 2h dropped fractions flagged (US500 0.196, DE30 0.163, US2000 0.103); DE30 ~5-month-shorter history. |
| Track A calibration (EXP-027-analog) — **EXP-044** | A | Event-level inference method calibration covering the 50 READY cells' event populations (per-instrument; EXP-027 machinery unchanged, re-used). | 0 / 0 | **COMPLETE 2026-06-11 — CALIBRATION_DELIVERED** (37/50 COVERED, 13 NOT_COVERED excluded with record; audit PASS; governance APPROVE Rev. 1) | **G1 leg (ii) — the binding remaining condition (design §8.2).** On completion, G1 closes via adjudication 2 of 2 in `G1-gate-review.md`; cells whose populations calibration cannot cover are excluded with record. |
| Track A parity (EXP-029-analog) | A | C#/Python parity re-verification for the 2h domain and the new-universe instruments (established parity covers neither; event definition is the unchanged frozen baseline). | 0 / 0 | **NOT EXECUTED — moot this phase** (no TEST read occurred; G2 FAIL closed the phase) | **Not a G1 condition** (G1-gate-review disposition 2026-06-11): the requirement **re-binds** before any future binding TEST read on a 2h or new-universe stratum. |
| `CF-AVWAP-001/PI-EXIT` (37-cell training) — **EXP-045** | B | Per cell: FH {2,3,4,6,8,11,16,23} and MAD-band (P6 grid) exits trained on TRAIN; n-neighbour stability plane (k=1, interior-only); tunability + P4 floor → membership. | 0 / 0 | **COMPLETE 2026-06-11 — TRAINING_DELIVERED, EMPTY MEMBERSHIP, audit PASS** | **G2 adjudicated FAIL 2026-06-11** ([G2-gate-review.md](../experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/G2-gate-review.md)): 0/37 members (35 NON_TUNABLE — 42 `endpoint_argmax` / 30 `flat_plane` of 74 family-cells; 2 FLOOR_FAIL with negative plateaus: EURUSD-1h FH(3) −3.45 bps, US500-2h MAD(1.0) −0.37) vs P5 ≥5 cells over ≥3 instruments → **FOUNDATION_NON-TUNABLE, no TEST spent**. Net medians −5 to −7 bps everywhere; gross proxy positive 31/37 — costs consume the edge. Negative training result retained (file drawer). |
| `CF-AVWAP-001/PORTFOLIO-011` | C | Does candidate portfolio C add incremental net edge over Donchian(20) (P1 rule)? | 1 one-shot TEST read (PRIMARY) | **NEVER OPENED — G2 FAIL 2026-06-11** (membership empty; 0 reads consumed) | P1 threshold predeclaration unspent — frozen record only; any future portfolio read requires its own registration and predeclaration. |
| `CF-AVWAP-001/TOPK-011` | D | Do the top-5 member cells (TRAIN stability rank; at-cap strata skipped) hold net CI_low > 0 one-shot on TEST (Holm-5 + R1.2 margins)? | ≤5 one-shot TEST reads (SECONDARY) | **NEVER OPENED — G2 FAIL 2026-06-11** (membership empty; no ranking exists; 0 reads consumed) | Family never activated; standalone-deployment claims require a future registration. |

**Out of scope (recorded):** MTF (deferred); `/ENTRY`/`/ALPHA`/`/MA-DOMAIN` sweeps; any 5m analysis; per-instrument entry-band tuning; E1–E5 re-test on the new population; any holdout read; cross-instrument pooling for per-cell verdicts; post-result cost iteration; grid extension after curves are seen.

## Phase 012 Batch (Entry-Side Gross Screen)

**Opened:** 2026-06-12 (D0 desk work; G0 PASS 2026-06-12 — operator-ratified `D0-predeclarations.md`, no data contact before ratification)
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-12-012-entry-side-gross-screen/design.md`
**Phase 011 close recorded:** FOUNDATION_NON-TUNABLE (G2 FAIL, 0/37 membership; gross proxy positive 31/37, net medians −5 to −7 bps — costs consume the edge; 0 of ≤6 TEST reads spent; ledger unchanged).
**Purpose:** the §9 routing decision (Route 1, operator 2026-06-12). One TRAIN-only diagnostic: does any predeclared entry-parameter variant — `/ALPHA` exponent {0.0, 0.375, 0.75\*, 1.0} or `/MA-DOMAIN` pair {(10,25), (20,50)\*, (40,100), (60,150)}, one-at-a-time around the frozen baseline (\*), 7 variants incl. baseline — raise **gross** per-event expectancy (H ∈ {4,8,16} reference horizons; H=8 binding) above the frozen P2 per-cell cost floor (`RT_i + financing_i × days(8,d)`) by ≥1×SE, with sign robustness at H=4/16, in ≥5 cells over ≥3 instruments (P6)? Verdicts: **ENTRY_GROSS_VIABLE** → Phase 013 (net/exit/portfolio machinery on the winning variant, own D0) or **ENTRY_GROSS_FLAT** → substrate pivot (operator pre-commitment; Stage-C branches `/LB` `/MB` `/ATR` `/ANCHOR` become the path).
**Amendment-rule compliance:** MA windows and volume exponent change *within this registered screen only* — registered here before any measurement, per the rules below. **Slot statement: 0 slots consumed.** The screen is diagnostic across the long-registered `/ALPHA` and `/MA-DOMAIN` branches; a slot is consumed only if a follow-on phase activates a selected variant as a candidate (Phase 013 D0 would register that explicitly, with the selected-on-TRAIN disclosure).
**Data-dependent design disclosure (Phase 008 §7.4 convention):** the routing itself derives from the Phase 011 gross-vs-net decomposition (EXP-045); the 37-cell universe from EXP-043/044; the reference-horizon convention from the EXP-045 gross proxy; the cost floor from frozen P2. None is Phase-012 data contact. A 2026-06-12 broker-pricing review (IC Markets raw) confirmed the frozen cost model is realistic-to-conservative; no cost value changed.
**TRAIN/TEST discipline:** TRAIN only (R1.3 boundary); 0 TEST reads by construction; ledger untouched; holdouts sealed.

| ID | Track | Question | Slot / TEST reads | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| D0 (this entry) | Tier 0 | Registry amendment + predeclarations (P1–P8). | 0 / 0 | **CLOSED 2026-06-12 — G0 PASS (operator-ratified)** | All items frozen in `D0-predeclarations.md`; TRAIN contact authorized behind the P8 regression-suite gate. |
| `CF-AVWAP-001/ENTRY-GROSS` (screen) — **EXP-046** | A | Does any `/ALPHA` or `/MA-DOMAIN` OAT variant clear the P4/P5 gross-vs-floor rule in ≥5 cells over ≥3 instruments (P6) on TRAIN? | 0 (diagnostic) / 0 TEST | **COMPLETE 2026-06-12 — SCREEN_DELIVERED, hypothesis REFUTED (ENTRY_GROSS_FLAT)** | No variant meets P6: best non-baseline 3 clearing cells (alpha_1.0 3 cells/3 instruments; ma_40_100 3/2) vs ≥5/≥3; 14 CLEAR / 235 NO_CLEAR / 10 BELOW_FLOOR over 259 rows; variant H=8 medians −2.35 to +0.28 bps vs floors ~5–20 bps. Integrity: reconciliation 259/259 at 1e-9 bps (EXP-043 counts + EXP-045 FH anchor + internal cross-check), determinism 259/259, P8 gate green, audit PASS 0C/0W, governance APPROVE. G1 adjudicated ENTRY_GROSS_FLAT (`G1-gate-review.md`) → substrate pivot per the §1.4.2 pre-commitment. `/ALPHA`, `/MA-DOMAIN` CLOSED-MEASURED on this substrate; 0 slots consumed. |

**Out of scope (recorded):** exit training/selection; any net or portfolio machinery; structural `/ENTRY` arm/trigger redefinition (pivot branch); `/ALPHA`×`/MA-DOMAIN` cross-grid or combined variants; grid extension after curves are seen; cost-model iteration; 5m; the 14 excluded cells; any TEST or holdout contact; MTF.

## Phase 013 Batch (Substrate Revision: Anchor Move-Size Diagnostic)

**Opened:** 2026-06-12 (D0 desk work; G0 PASS 2026-06-12 — operator-ratified `D0-predeclarations.md`, no data contact before ratification)
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/design.md`
**Phase 012 close recorded:** ENTRY_GROSS_FLAT (G1 mechanical; `/ALPHA` and `/MA-DOMAIN` CLOSED-MEASURED; 0 slots, 0 TEST reads). The entry-parameter lever is exhausted; the operator pre-commitment (Phase 012 §1.4.2 / §10) routes the programme to substrate-level revision.
**Corrected substrate framing (load-bearing, verified `python/src/xen/avwap.py:390–421`):** the `CF-AVWAP-001` substrate is a **trend-continuation pullback entry** (arm on a completed close to the adverse side of the AVWAP; trigger on reclaim **in the regime direction**), not a mean-reversion fade. Prior negatives are not a wrong-side signal — Phase 011 showed the gross proxy positive in 31/37 cells (entry direction sound); the failure is **economic** (the captured move is thinner than round-trip cost). This batch tests the only registered lever that changes *move geometry* rather than reshuffling the same events.
**Purpose:** one TRAIN-only diagnostic (EXP-047, `DIAG-007`). Exercise the registered `CF-AVWAP-001/ANCHOR` branch (gap #1, deferred since Phase 005): replace the running-extreme anchor with an **ATR-prominence significant pivot** (P1: `k × ATR(14)` counter-move confirmation, `k=1.0`, running-extreme fallback). Per READY cell, compare the gross **available favorable move-size** distribution (MFE, exit-agnostic, real prices) of the `/ANCHOR` anchor vs the current baseline anchor, against the frozen P2 cost floor (reference line; never subtracted). Verdicts: **ANCHOR_MOVE_VIABLE** (P5/P6: ≥5 SHIFTED_VIABLE cells over ≥3 instruments, where SHIFTED_VIABLE requires a ≥1×SE rightward MFE shift, `median_MFE(/ANCHOR) ≥ 2 × floor`, no MAE-erasure, ≥30 events, determinism) → a future in-family `/ANCHOR` **viability** phase (own D0; needs EXP-027/029 analogs + net training + TEST endpoint); or **ANCHOR_MOVE_FLAT** → the move-size ceiling is intrinsic to the AVWAP family → route to a **new candidate family** (own D0; fresh EXP-020/027/029-analog scaffolding).
**Slot accounting:** **0 slots consumed.** EXP-047 is a TRAIN-only diagnostic (`DIAG-007`) across the long-registered `/ANCHOR` branch; the `/ANCHOR` 1-slot reservation (Phase 005 deferred table) is consumed only if a future viability phase activates `/ANCHOR` as a candidate, registered explicitly there with the selected-on-TRAIN disclosure. The diagnostic measures an *available-move ceiling*, never an edge claim.
**Data-dependent design disclosure (Phase 008 §7.4 convention):** the routing derives from the Phase 011/012 gross-vs-net decomposition; the full 17-instrument × {1h,2h,4h} universe from EXP-043/VAL-003; the lifetime boundary from EXP-022; the cost floor from frozen P2. The corrected substrate framing is a code-reading of the existing frozen generator, not Phase-013 data contact. None is Phase-013 data.
**TRAIN/TEST discipline:** TRAIN only (R1.3 1-minute-row `train_end_ts` boundary); 0 TEST reads by construction; ledger untouched (EURUSD-4h AT CAP, all else unchanged); holdouts sealed. `/ANCHOR` is a **new event definition** → a hard EXP-020-analog readiness gate (P2) precedes any move-size read; EXP-027/029 analogs are deferred to a future net phase.

| ID | Track | Question | Slot / TEST reads | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| D0 (this entry) | Tier 0 | Registry amendment + predeclarations (P1–P8). | 0 / 0 | **CLOSED 2026-06-12 — G0 PASS (operator-ratified)** | All items frozen in `D0-predeclarations.md`; ATR prominence `k=1.0` (P1) and floor multiple `M=2` (P5) operator-ratified; remaining items inherit Phase 011/012 conventions. TRAIN contact authorized behind the P8 regression-suite gate. |
| `CF-AVWAP-001/ANCHOR` (move-size diagnostic) — **EXP-047** (`DIAG-007`) | A | On TRAIN, gross: does the ATR-prominence `/ANCHOR` anchor materially shift the available favorable move-size (MFE) distribution above the cost floor (P5) vs the baseline anchor, in ≥5 READY cells over ≥3 instruments (P6)? | 0 (diagnostic) / 0 TEST | **COMPLETE 2026-06-12 — REFUTED (ANCHOR_MOVE_FLAT; G1a 51/51 READY, G1b 0/51 SHIFTED_VIABLE)** | Two sub-steps: (1) `/ANCHOR` readiness (EXP-020 analog, full-universe grid; READY membership) → G1a; (2) move-size distribution comparison vs baseline anchor → G1b. Baseline-anchor arm reconciles against the EXP-045/046 gross proxies on shared cells. Verdict mechanical; FLAT positively authorizes the new-family pivot. |

**Phase 013 close recorded (2026-06-12):** ANCHOR_MOVE_FLAT (G1a 51/51 READY; G1b 0/51 SHIFTED_VIABLE, mechanical). `/ANCHOR` CLOSED-MEASURED as ratified; its 1-slot reservation is **released, never consumed** (the viability phase that would have consumed it is foreclosed by the FLAT verdict). `CF-AVWAP-001` closed for new in-family phases. Routing executed per the pre-commitment: new candidate family (Phase 014, own design/D0). Gate record: `docs/experiments-docs/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/G1-gate-review.md`; retrospective in the same checkpoint.

**Out of scope (recorded):** any net or cost-adjusted move-size column (gross only); exit training/selection/portfolio machinery; inference calibration (EXP-027 analog) or cTrader parity (EXP-029 analog) — deferred to a future net phase; the other Stage-C detectors `/LB` `/MB` `/ATR` (regime-timing levers, not move-geometry; entry-timing already gross-flat per Phase 012); new-family design (a routing destination, not work here); anchor re-parameterisation, threshold change, or cell re-selection after a distribution is seen; 5m; any TEST or holdout contact; MTF; execution-cost work.

## Phase 014 Batch (New Candidate Family: HA Harami Substrate & Capture Geometry)

**Opened:** 2026-06-14 (D0 desk work). **G0 PASS 2026-06-14** — operator-ratified
`D0-predeclarations.md` (P1–P13; P4 revised to the adaptive duration-derived time
cap before ratification). No row read under any harami event definition before
ratification; pipeline ran VAL-004 → EXP-048 → EXP-049 → EXP-050 → EXP-051 → EXP-052
(all complete, audits PASS) by 2026-06-15. **014-A G1 adjudicated 2026-06-15**
(`G1-gate-review.md`): primitives READY; benchmark capture `CHARACTERISED_NOT_VIABLE` **on
the unconditioned object only**; the conditioned family hypothesis is untested → family
**OPEN**; operator directed proceed to **Phase 014-B** (no closure). See the Phase 014-B
batch section.
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/design.md`
**Family spec:** `docs/signal-registry/candidate-families/harami.md` (status `REGISTERED` — Phase 014 G0 PASS 2026-06-14).
**Phase 013 close recorded:** ANCHOR_MOVE_FLAT → `CF-AVWAP-001` closed for new
in-family phases; pre-committed routing to a new candidate family executed here.
**Design brief (Phase 013 retrospective, binding):** available move was ≈5–9× the
cost floor in every AVWAP cell, but no deterministic exit captured it — the unsolved
problem is **capture geometry, not move availability**. The mechanism chosen here is
a **structurally bounded favourable target** (fraction of the confirmed prior move);
whether that bound solves favourable-before-adverse is measured early (HYP-002), not
assumed.
**Operator decisions recorded (2026-06-14, pre-design):** (1) readiness **and**
characterization run on all 102 cells (17 instruments × {5m,15m,30m,1h,2h,4h}) — no
blanket assumptions, per-cell from day one; (2) 014-A tests both barrier
computability **and** a gross favourable-before-adverse capture-rate read (not
deferred to 014-B); (3) ZigZag first-branch = Wilder ATR, period 14, `ATR_MULT` 1.0;
(4) family ID `CF-HA-HARAMI-001`; registry doc and phase design split.
**Slot accounting:** all Phase 014-A/B experiments are **characterization/diagnostic
— 0 candidate slots, 0 TEST reads** by construction. A candidate branch for
screening is registered only at the close of 014-B (own entry, with the
selected-on-TRAIN disclosure). The variant branches below are registered (countable)
but consume a slot only when a future scope activates one as a screening candidate.
**Infrastructure precondition [VAL]:** 15m and 30m are new domains; a VAL-001-style
temporal-integrity validation (VAL-004) across all 17 instruments must PASS before
those cells enter EXP-048. Holdout sealed per file at first touch; no new-universe row
has been read under the HA-harami event definition (Phase 011 read new-universe
first-70% rows for prior, non-harami readiness/calibration/training); the global
holdout seal carries forward.
**TRAIN/TEST discipline:** gross throughout; no cost model; 0 TEST reads; holdouts
sealed; no HA-price outcome metric (detection on HA candles, all outcomes on real
prices).

| ID | HYP | Question | Slot / TEST reads | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| D0 (this entry) | Tier 0 | Registry amendment + predeclarations (`D0-predeclarations.md` P1–P13). | 0 / 0 | **CLOSED 2026-06-14 — G0 PASS (operator-ratified)** | All P1–P13 frozen. P1 Wilder/14/1.0, P2 favourable 50%, P4 per-cell adaptive duration-derived time cap (`max(6, round(1.5 × median trailing-20 confirmed-move duration))`), P12 capture-viability `r≥0.55`/CI_low>0.50/≥30 resolved. VAL-004 precedes any 15m/30m read; no data contact occurred before ratification. |
| VAL-004 | — | Do 15m and 30m aggregated OHLC pass VAL-001-style temporal integrity across all 17 instruments? | 0 / 0 | **COMPLETE 2026-06-14 — SUPPORTED (PASS)** | Full Suite PASS: 2,279 checks, 0 FAIL, 0 INCONCLUSIVE, 28/28 negative controls detected. 68/68 cells ADMITTED. |
| `CF-HA-HARAMI-001/HYP-001` — **EXP-048** | HYP-001 | ZigZag substrate + HA harami detector readiness across 102 cells: determinism, look-ahead safety, invariants, per-cell coverage, `/BARCFG` coverage measured. | 0 / 0 | **COMPLETE 2026-06-14 — READINESS_DELIVERED** | 86/102 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED. 0 invariant violations, 0 determinism failures. 99 member cells cleared for EXP-049. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-002` — **EXP-049** | HYP-002 | 3-barrier capture readiness + **gross favourable-before-adverse capture rate** per cell under default barriers (causal, exit-agnostic). | 0 / 0 | **COMPLETE 2026-06-15 — CAPTURE_READINESS_DELIVERED** | Barrier construction PASS 99/99. G1 r ~0.50 null → 0/99 VIABLE. G2 0/99 (structural degeneracy). Audit PASS. |
| `CF-HA-HARAMI-001/HYP-003` — **EXP-050** | HYP-003 | Where in a ZigZag move do harami signals occur vs predeclared baselines (random timestamps, alt trend defs)? | 0 / 0 | **COMPLETE 2026-06-15 — CONTEXT_CHARACTERISATION_DELIVERED** | 0/99 CLUSTERED (all NOT_CLUSTERED). Δ −0.12 to −0.18 uniformly. Front-loading is ZigZag-specific. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-004` — **EXP-051** | HYP-004 | Do `/STRONG-STAT` and `/STRONG-HA` identify materially different move populations, cross-cell consistent? | 0 / 0 | **COMPLETE 2026-06-15 — STRONG_FILTER_CHARACTERISATION_DELIVERED** | Both filters P11-clear. /STRONG-STAT ρ 1.72–2.19, f 0.25–0.32; /STRONG-HA ρ 1.62–2.08, f 0.15–0.24. 99/99 MATERIAL, 17/17 instruments. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-005` — **EXP-052** | HYP-005 | Direct signal vs signal+confirmation (`/CONFIRM`): descriptive frequency/timing/outcome. | 0 / 0 | **COMPLETE 2026-06-15 — CONFIRM_CHARACTERISATION_DELIVERED** | CONFIRM_CHARACTERISATION_DELIVERED: 99/99 cells negative shift (P11_neg_readout=true), paired delta median −0.62 ATR, confirm arm universally worse than direct on gross excursion balance. Audit PASS. |

### Registered variant surface (countable; slot consumed only on screening activation)

| Branch | Lever | Status |
| --- | --- | --- |
| `CF-HA-HARAMI-001/BARCFG` | bar-direction configuration isolation | REGISTERED (characterization) |
| `CF-HA-HARAMI-001/CONFIRM` | signal+confirmation (stop-order entry) | REGISTERED (characterization) |
| `CF-HA-HARAMI-001/STRONG-STAT` | statistical strong-move filter | REGISTERED |
| `CF-HA-HARAMI-001/STRONG-HA` | HA-impulse strong-move filter | REGISTERED |
| `CF-HA-HARAMI-001/VPTARGET` | volume-profile favourable target (TickVolume proxy) | REGISTERED |
| `CF-HA-HARAMI-001/MAGTARGET` | statistical-magnitude favourable target (`LOOKBACK>1`) | REGISTERED |
| `CF-HA-HARAMI-001/ADV-EXTREME` | previous-move-extreme adverse target | REGISTERED |
| `CF-HA-HARAMI-001/ADV-NONE` | no adverse target | REGISTERED |
| `CF-HA-HARAMI-001/THIRD-EVENT` | event-based third barrier | REGISTERED |
| `CF-HA-HARAMI-001/THIRD-TIME` | adaptive time-cap sensitivity (`k`/window/floor) | REGISTERED |
| `CF-HA-HARAMI-001/ATRMULT` | `ATR_MULT` sensitivity (predeclared grid) | REGISTERED |
| `CF-HA-HARAMI-001/LOOKBACK` | reference-set size sensitivity (predeclared grid) | REGISTERED |
| `CF-HA-HARAMI-001/EXIT-PARTIAL` | favourable-side scaled/partial exits (≤3 splits; event-trigger or %-to-target) | **REGISTERED (Phase 014-B; 2026-06-15)** |
| `CF-HA-HARAMI-001/EXIT-TRAIL-STRUCT` | adverse-side structure trailing stop on a smaller-`ATR_MULT` ZigZag | **REGISTERED (Phase 014-B; 2026-06-15)** |
| `CF-HA-HARAMI-001/EXIT-TRAIL-UNCAPPED` | structure trailing stop run as a *standalone adverse-exit model* — **no benchmark time-cap backstop and no initial 1:1 stop** (the position carries no adverse exit until the first secondary-ZigZag pivot confirms after entry, then ratchets; the only censoring is `DATA_CENSORED` at the TRAIN data edge). Replaces the 3-barrier geometry rather than swapping one barrier; distinct from `/EXIT-TRAIL-STRUCT` (capped) and from `/THIRD-TIME` (cap sensitivity within the 3-barrier model). | **REGISTERED (Phase 014-B; 2026-06-16)** |

**Out of scope (recorded):** any net/cost-adjusted metric (gross only this phase);
any HA-price outcome metric; any combined event definition before each primitive is
measured separately; parameter tuning or post-result variant selection; any TEST or
holdout contact; cTrader screening before 014-B registers a candidate branch.

## Phase 014-B Batch (Conditioned Signal, Capture Geometry & Position-Management Surface)

**Opened:** 2026-06-15 (014-A G1 hand-off). **G0-B PASS 2026-06-15** — operator ratified
`014-B-D0-addendum.md` (P14–P21; P14 binding endpoint = **median** per-event expectancy, mean
disclosed; P18 `ATR_MULT_TRAIL = 0.5`, tunable later). No 014-B data contact (no `results/`
under EXP-053+) occurred before ratification.
**Governing design:** `docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-B-design.md`
**D0 addendum:** same dir, `014-B-D0-addendum.md` (P14–P21).
**Mandatory reading (binding):** every 014-B scope must record that
`014-A-conditioning-gap-and-validation-lessons.md` was read and honoured (conditioning,
harami-anchor, descriptive-only position, expectancy endpoint) — Stage-4 REVISE if absent.
**014-A G1 recorded:** primitives READY; benchmark capture `CHARACTERISED_NOT_VIABLE` **on
the unconditioned object only** (EXP-049 anchored on the ZigZag confirmation, `/STRONG` OFF,
6-bar-floor horizon, worst-case tie-break; EXP-052 raw harami; EXP-050 non-live position base
rate). The **conditioned** family hypothesis (strong-move-qualified harami, harami-anchored)
is **untested** → family **OPEN**; operator directed proceed-to-014-B, no closure
(`G1-gate-review.md`).
**Binding endpoint (P14):** gross per-event **expectancy** (ATR-normalised, P15 fills),
CI_low > 0, ≥30 events, P11-composed. First-hit `r` (P12) demoted to disclosed secondary.
**No intermediate gates (operator):** the full surface is measured before a single **G2**;
no early-closure path inside 014-B. **0 candidate slots, 0 TEST reads, holdouts sealed**
throughout; a candidate branch is registered only at G2 PROCEED_TO_SCREEN.

| ID | HYP | Question | Slot / TEST | Status | Gate / Note |
| --- | --- | --- | --- | --- | --- |
| D0-B (this entry) | Tier 0 | Registry amendment + `014-B-D0-addendum.md` (P14–P21); register `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, fill-model standard. | 0 / 0 | **CLOSED 2026-06-15 — G0-B PASS (operator-ratified)** | P14 median binding (mean disclosed); P18 `ATR_MULT_TRAIL = 0.5` tunable later. No 014-B data contact before ratification. EXP-053 scoping authorized behind the mandatory lessons read. |
| `CF-HA-HARAMI-001/HYP-006` — **EXP-053** | HYP-006 | **Conditioned-signal efficacy (lead):** `/STRONG`-conditioned harami, **anchored at the harami**, gross per-event expectancy under benchmark barriers vs matched controls, P11. | 0 / 0 | **CHARACTERISED — EVIDENCE_FOR (2026-06-15)** | 7 viable cells over 6 instruments (P11 met), 6 over 5 beat both baselines; 0 defects, 99/99 powered. Conditioned family hypothesis supported on benchmark geometry. 0 slots/0 TEST. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-007` — **EXP-054** | HYP-007 | **Fill-model method (lead):** path-ordered intrabar fills (P15) vs the worst-case tie-break — does the benchmark capture readout change materially vs EXP-049? | 0 / 0 | **FILL_MODEL_CHARACTERISED (IMMATERIAL) — 2026-06-16** | P15 effect bounded at median Δr 0.010, 0/99 G1 VIABLE, 0 TIE_BREAK_SENSITIVE; P15 adopted as 014-B fill standard. |
| `CF-HA-HARAMI-001/HYP-008` — **EXP-055** | HYP-008 | **Long-horizon availability (lead, AVWAP-analog):** conditioned-signal lifetime favourable MFE vs adverse MAE (gross) vs cost-floor-analog reference. | 0 / 0 | **AVAILABILITY_GOOD (2026-06-16)** | AVWAP situation confirmed: move available (74/99 MOVE_AVAILABLE over 17 instruments, P11=True), not a signal problem; 99/99 powered, 0 defects. Settles AVWAP analog — "move available, capture missing." |
| `CF-HA-HARAMI-001/HYP-009` — **EXP-056** | HYP-009 | **Favourable-target geometry:** `/VPTARGET`, `/MAGTARGET` vs benchmark 50%, expectancy. | 0 / 0 | **CHARACTERISED — EVIDENCE_AGAINST (2026-06-16)** | No alternative favourable-target variant clears P11 WIN (max 2 WIN cells/2 instruments; MAG-1.0×20 a lone 1-WIN cell, USDCHF-5m marginal). VP variants 0 WIN; benchmark 50%-of-`M_sofar` competitive or superior on every comparison. 99/99 powered, 0 defects. 0 slots, 0 TEST. Audit PASS. TickVolume proxy disclosed for `/VPTARGET`. |
| `CF-HA-HARAMI-001/HYP-010` — **EXP-057** | HYP-010 | **Adverse-target geometry:** `/ADV-EXTREME`, `/ADV-NONE` vs benchmark 1:1, expectancy. | 0 / 0 | **CHARACTERISED — EVIDENCE_FOR (2026-06-16)** | ADV-NONE wins P11 (23 WIN/15 instr); EXTREME-raw destructive; EXTREME-rr1 ties benchmark. 0 slots, 0 TEST. |
| `CF-HA-HARAMI-001/HYP-011` — **EXP-058** | HYP-011 | **Third-barrier geometry:** `/THIRD-EVENT`, `/THIRD-TIME` vs benchmark adaptive cap, expectancy + censoring. | 0 / 0 | **CHARACTERISED — EVIDENCE_AGAINST (2026-06-16)** | No variant clears P11 (max 3 WIN cells). Raising floor depletes viability 8→6→4→2→1. THIRD-EVENT weakest (1 viable, 0 WIN). 99/99 powered. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-012` — **EXP-059** | HYP-012 | **Position-management exits:** `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined, expectancy. | 0 / 0 | **CHARACTERISED — EVIDENCE_FOR (2026-06-16)** | `/EXIT-PARTIAL` EVIDENCE_FOR: 4 PARTIAL arms clear P11 (V2A strongest 53 wins/17 instr). `/EXIT-TRAIL-STRUCT` uniformly detrimental within benchmark cap (0 viable cells across all 7 trailing/combined arms). 0 defects, 0 Critical. 0 slots, 0 TEST reads. Passes to EXP-060. |
| `CF-HA-HARAMI-001/HYP-012b` — **EXP-059B** | HYP-012 (follow-up) | **Uncapped structure trailing (EXP-059 gap-fill):** the `/EXIT-TRAIL-UNCAPPED` model — trailing adverse with **no time-cap backstop and no initial stop** — measured as `TRAIL-PURE-UNCAPPED` and `COMBINED-UNCAPPED-V2A` vs `BENCH`; capped no-init siblings re-run for cap-isolation (disclosed). Expectancy (P14). | 0 / 0 | **CHARACTERISED — EVIDENCE_AGAINST (2026-06-16)** | 0/2 binding arms clear P11. TRAIL-PURE-UNCAPPED 0 viable, 0 WIN (uniformly negative). COMBINED-UNCAPPED-V2A 1 viable (BTCUSD-5m), 0 WIN. Cap-isolation: 0/96 divergent-positive (TRAIL-PURE), 2/89 (COMBINED) — cap was not the constraint. BENCH viable in only 9/99 (audit Warning #1 — interpretation caveat for G2). 0 defects, 0 Critical, 1 Warning, 5 Info. Audit PASS. Registry-relevant; closes `/EXIT-TRAIL-UNCAPPED` as characterized negative. 0 slots, 0 TEST reads. |
| `CF-HA-HARAMI-001/HYP-013` — **EXP-060** | HYP-013 | **Combined event system:** best per-layer geometry + conditioned signal; per-cell hit/miss/expectancy vs P13 baselines. | 0 / 0 | **CHARACTERISED — CHARACTERISED_NOT_VIABLE_ELIGIBLE (2026-06-17)** | 0 champion_wins (99/99 cells powered, 69/99 viable individually, 3 beat matched-random, 0 beat MA(20,50)). Both geometric levers (V2A, ADV-NONE) independently improve expectancy additively; interaction near zero. **Interpretation caveat (added 2026-06-17):** the "MA-baseline dominance is a substrate property" reading is *provisional* — post-hoc investigation of the generated results found (i) the champion's gross **mean** is ≈0 or negative on 5/6 domains despite positive median (capped V2A upside + uncapped ADV-NONE downside ⇒ left-skew mirage), and (ii) MA's median advantage was never tested against a matched-random control on the MA substrate, nor was MA's mean/exit-composition emitted. **EXP-060B (HYP-013b) resolves both before G2 adjudicates.** Full 014-B surface measured; G2 desk adjudicates after EXP-060B. Audit PASS. |
| `CF-HA-HARAMI-001/HYP-013b` — **EXP-060B** | HYP-013 (follow-up) | **MA(20,50) substrate dominance: genuine lead or skew artifact? (EXP-060 gap-fill).** Re-instruments EXP-060's already-computed MA(20,50) arm to emit **mean + exit-reason composition** (EXP-060 emitted MA median only), and adds the one new control — a **matched-random entry on the MA substrate (RM3)** through the identical V2A×ADV-NONE×cap pipeline. Binding discriminator: does the MA-substrate harami (M3) clear P11 median viability **and beat its own-substrate matched-random (M3−RM3 CI_low>0)** with mean clearing P11 (genuine lead), or is MA's median dominance the same median≫mean / entry-redundant artifact as the ZigZag champion (artifact)? Skew attribution via ADV-NONE-vs-1:1 arms on both substrates; median binding (P14), mean disclosed. | 0 / 0 | **CHARACTERISED — SUBSTRATE_LEAD_FOUND (2026-06-17)** | Audit PASS (0C/2W/3I), reconciliation exact 99/99, all integrity gates pass. On the MA substrate the conditioned harami expresses a **real median edge** it does **not** on ZigZag: M3 median ≈1.16 vs RM3 ≈0.38 (non-degenerate control = geometry baseline); **M3 beats RM3 in 85/99 cells** (reverses EXP-060's ZigZag 3/99); M3 median-viable 89/99. **But median-only:** M3 gross **mean** median ≈ −0.065 (mean-viable only 14/99); skew is ADV-NONE-driven (MA median−mean gap **1.20 ATR** for ADV-NONE vs 0.49 for 1:1). **Lead = 14 cells/9 instruments (P11 met) but 8/14 are low-n 4h.** Net: a real-but-narrow median edge that is **not yet tradeable** (mean ≈0). Qualifies EXP-060's "substrate property" reading — the MA advantage is partly a real signal effect, not solely geometry/drift. **0 new countable item; 0 candidate slots, 0 TEST reads** (composes registered `/EXIT-PARTIAL` V2A, `/ADV-NONE`, benchmark cap, two P13 baselines; the MA matched-random is a null). Family stays REGISTERED/OPEN — no candidate registered here. Full spec/results: `python/experiments/EXP-060B/{scope,results,report}.md`; checkpoint addendum `014-B-EXP-060B-ma-substrate-dominance-addendum.md`. |

**G2 (after full slate, now incl. EXP-060B):** PROCEED_TO_SCREEN (≥1 EXP-060 combined definition clears P11
expectancy viability vs P13 baselines → register a candidate branch, first slot, EXP-027-analog
calibration next) / CHARACTERISED_NOT_VIABLE (full conditioned surface measured, none clears →
closure well-supported) / SUBSTRATE-METHOD_DEFECT / INCONCLUSIVE. EXP-IDs are the registered
plan; final IDs assigned at Stage-1 per `python/experiments/INDEX.md`.
**EXP-060B RESULT — SUBSTRATE_LEAD_FOUND (2026-06-17):** EXP-060B adjudicated EXP-060's
"MA dominance is a substrate property" reading and returned **SUBSTRATE_LEAD_FOUND** (audit PASS).
The conditioned harami expresses a **real median edge on the MA substrate** (M3 beats its own-substrate
matched-random in 85/99 cells; reverses ZigZag's 3/99) — so the MA advantage is **partly a real signal
effect, not solely a geometry/drift artifact.** **Therefore the single 014-B G2 must NOT close
CF-HA-HARAMI-001 on a clean CHARACTERISED_NOT_VIABLE** — a scoped MA-substrate follow-up is warranted.
**However**, the lead is **median-only and narrow**: M3's gross **mean** is ≈0/negative (mean-viable
14/99; ADV-NONE skew gap 1.20 ATR), and the P11 lead leans on 8/14 low-n 4h cells. The binding obstacle
to viability is now the **skew/mean**, not the signal's existence — so the follow-up must target a
bounded-downside geometry that recovers a positive mean, **not** re-run the current V2A×ADV-NONE geometry
(which inherits the mean≈0 problem). Candidate registration would occur at that follow-up's gate, never in
EXP-060B (0 slots, 0 TEST reads). Family stays **REGISTERED/OPEN**.

**G2 ADJUDICATED 2026-06-17 — NO_PROCEED_TO_SCREEN, FAMILY NOT CLOSED**
(`docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G2-gate-review.md`;
operator routing ratified "Open MA-substrate follow-up"). The terminal G2 on the full slate:
**PROCEED_TO_SCREEN NOT met** (champion A3 0/99 beats MA(20,50); EXP-060B's MA edge is
median-only/mean≈0 and is a characterisation read that cannot register a candidate);
**SUBSTRATE/METHOD_DEFECT NOT met** (EXP-054 IMMATERIAL, integrity all-pass);
**INCONCLUSIVE NOT met** (99/99 powered); **CHARACTERISED_NOT_VIABLE criterion met on the
ZigZag substrate only** — a clean close is **forbidden** by EXP-060B SUBSTRATE_LEAD_FOUND.
Net: **014-B CHARACTERISED_NOT_VIABLE on ZigZag as configured; family carried OPEN** on the
real MA-substrate median edge whose binding obstacle is now the **skew/mean**. **0 candidate
slots, 0 TEST reads spent in all of 014-B; holdouts sealed; ledger unchanged.** Phase 014
closes at G2; retrospective written. **Routing:** a scoped MA-substrate follow-up (new phase,
own D0/G0) targeting bounded-downside adverse geometry (1:1, `/ADV-EXTREME-rr1`) with the
**mean** as a co-primary endpoint — not a re-run of V2A×ADV-NONE — and confronting the
8/14-low-n-4h lead concentration; no TEST/holdout contact; candidate registration only at the
follow-up's own PROCEED gate.

**Out of scope (recorded):** any net/cost-adjusted metric (gross only); any HA-price outcome
metric; position-in-move as a *live* filter (descriptive-only); parameter tuning or
post-result variant selection; any intermediate early-closure gate; any TEST or holdout
contact; cTrader screening before G2 registers a candidate branch.

## Phase 015 Batch (MA(20,50)-Substrate Conditioned Harami — Full-Surface Characterisation)

**Status:** **CLOSED 2026-06-18 at G-015 — PROCEED_TO_SCREEN (native object); first candidate slot
consumed.** Was ACTIVE (G0 PASS 2026-06-17, operator). Continuation of `CF-HA-HARAMI-001`
(REGISTERED, OPEN) opened by the Phase 014 G2 routing ("Open MA-substrate follow-up"). Governing
design + D0: `docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-conditioned-harami-full-surface/`
(`design.md`, `D0-predeclarations.md` P1–P12; `D0-amendment-001-dual-parallel-substrate.md`;
`D0-amendment-002-drop-exp067.md`; `G-015-gate-review.md`). **All Phase 015 *experiments* were gross,
0 candidate slots, 0 TEST reads; the G-015 PROCEED registered the first candidate slot (the MA-native
branch) at gate close — see the G-015 block below.** TEST reads remain 0; holdouts sealed; no
new-universe row read under the HA-harami event definition. No Phase 015 data contact occurred before
G0.

**Why:** Phase 014 mapped the full capture/exit surface on the ZigZag substrate, where the
conditioned harami is redundant vs random (3/99); EXP-060B then found the signal is *real* on the
MA(20,50) substrate (beats own-substrate matched-random 85/99) but at one geometry only (V2A ×
`/ADV-NONE`), median-only with mean ≈ 0. Phase 015 re-derives the 014-B surface on the MA substrate
to learn whether the MA edge is a robust substrate property or a single-geometry artifact, and —
mean as a *diagnostic* not a disqualifier — why the mean is negative and whether bounded-downside
geometry recovers it.

**New countable items (registered before any result-producing code):**

| Item | Definition | Status |
| --- | --- | --- |
| `CF-HA-HARAMI-001/MA-SUBSTRATE` | MA(20,50) crossover segmentation on real close as the conditioned harami's move/direction/favourable-target/adaptive-cap substrate (replacing ATR-ZigZag for outcome geometry). MA(20,50) **fixed/ratified, not swept** (MA-parameter sensitivity out of scope). Semantics bound to the EXP-060/060B `ma_seg_arm`/`ma_segment_moves` construction (P1; P12 reconciliation). | **REGISTERED (Phase 015; 2026-06-17)** |
| `CF-HA-HARAMI-001/MA-SUBSTRATE` — mode `hybrid` | Entry events = the EXP-053/060 ZigZag-`/STRONG-STAT`-conditioned haramis (byte-identical population, the EXP-060B object + reconciliation anchor); MA supplies only the outcome geometry. **Primary**; full surface. | **REGISTERED (Phase 015; 2026-06-17)** |
| `CF-HA-HARAMI-001/MA-SUBSTRATE` — mode `native` | `/STRONG-STAT` magnitude filter **recomputed on confirmed MA segments** (qualify if MA-segment magnitude-so-far ≥ p75 of trailing-20 confirmed MA-segment magnitudes; causal). This is the object the EXP-060B/061 `M`-arms actually measured (reconciles to EXP-060B `M0/M3` 1e-9). **Parallel first-class substrate carrying the full surface, reported individually** *(elevated by `D0-amendment-001-dual-parallel-substrate.md`, 2026-06-17 — no longer "co-investigated, bounded")*. | **REGISTERED (Phase 015; 2026-06-17)** |

The bounded-downside adverse arms (benchmark 1:1, `/ADV-EXTREME` with rr1) and the reused
favourable/third/exit OAT variants (`/VPTARGET`, `/MAGTARGET`, `/THIRD-TIME`, `/THIRD-EVENT`,
`/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`) are already registered (Phase 014/014-B batches); Phase 015
records their MA-substrate reuse. `/ADV-NONE` is retained as a disclosed unbounded reference (the
skew source under study), not a viability candidate.

**Binding posture (P1–P12):** median per-event gross ATR-normalised expectancy is the binding
viability endpoint (CI_low>0, ≥30 events, P11 with a non-4h breadth rule of ≥3 qualifying cells
outside 4h); the **mean** is a **diagnostic co-primary** (raw + 10% trimmed + worst-5% tail-share,
each CI'd) — a median-viable/mean-negative result does **not** close the family; closure needs a
positive demonstration of structural mean-irrecoverability (trimmed mean also negative ∧ persists
under bounded-downside ∧ not removable-tail-driven). **Matched-random null per object, every read,
reported individually (`RM-hybrid`, `RM-native`); the two objects are never pooled** (Amendment 001).
Fixed per-cell bootstrap seed. Detection on HA candles; all outcome metrics on real prices.

**AMENDED 2026-06-17 — `D0-amendment-001-dual-parallel-substrate.md`.** Both conditioning modes
(`hybrid`, `native`) are now **parallel first-class substrates carrying the full surface, reported
individually**. Root cause: EXP-060B/061 `M`-arms condition on MA-segment `/STRONG-STAT` and so **are
the native object** (the 85/99 edge was native); the genuine hybrid object was never computed.
Reconciliation flips (P12): native → EXP-060B `M0/M3` 1e-9; hybrid → EXP-053 population + determinism
+ causality + invariants. EXP-061/062/063 are **re-run dual-object, superseding in place**. EXP-067 =
hybrid combined champion; EXP-068 = **native** combined champion (HYP-021 reassigned, merges old
N1+N2); **HYP-022/EXP-069 DROPPED** (retained, never deleted). No new countable item (`native` already
countable at G0).

| Experiment (planned) | Object | Mirrors | Question | Slots / TEST | Status |
| --- | --- | --- | --- | --- | --- |
| `CF-HA-HARAMI-001/HYP-014` — EXP-061 | hybrid **+** native (L1), individually | EXP-049 + EXP-053 | MA-substrate 3-barrier capture readiness + benchmark-geometry median expectancy, each object vs its own matched null. | 0 / 0 | **CHARACTERISED (dual-object, re-run 2026-06-17): native EVIDENCE_FOR (8 cells/6 instr, all non-4h; reconciles EXP-060B 99/99 @1e-9 — confirms the prior mislabelled result) / hybrid EVIDENCE_AGAINST (genuine ZZ-conditioned 3202-class × MA geom generalises in 1 cell only). Phase verdict EVIDENCE_FOR (stronger=native).** Objects never pooled; item retained, feeds terminal G-015; no closure/registration here. |
| `CF-HA-HARAMI-001/HYP-015` — EXP-062 | hybrid **+** native (L2), individually | EXP-055 | Lifetime availability (MFE/MAE) on MA segments, each object — room to bound the downside while keeping favourable capture? | 0 / 0 | **CHARACTERISED (dual-object, re-run 2026-06-17): AVAILABILITY_GOOD — 91/99 MOVE_AVAILABLE (17 instr/77 non-4h, P11+P6 composes); 4/99 SIGNAL_ATTRIBUTABLE — the abundant room is a generic MA-segment-length property, not harami-specific. MAE tail bounded-recoverable (tail-share ~0.23) sizing L3. Both objects measured individually; never pooled. Supersedes prior single-object result in place.** |
| `CF-HA-HARAMI-001/HYP-016` — EXP-063 | hybrid **+** native (L3), individually | EXP-057 + mean diag | Bounded-downside adverse geometry (1:1, `/ADV-EXTREME-rr1`) vs `/ADV-NONE` + tail-share/trimmed-mean/recovery, each object. | 0 / 0 | **CHARACTERISED (dual-object, re-run 2026-06-17): EVIDENCE_FOR (nuanced) — V-BENCH generalises (8 cells/6 instr/8 non-4h) AND mean_viable composes (10 cells/6 instr/7 non-4h) per P4 closure rule; but recovery_positive=0 for all cells (formal bounded-vs-NONE contrast never crosses zero). Self-mean-viable but not recovery-positive; V-RR1 62% attribution gap. Both objects measured individually; never pooled. Supersedes prior single-object result in place.** |
| `CF-HA-HARAMI-001/HYP-017` — EXP-064 | hybrid **+** native (S1), individually | EXP-056 | Favourable-target geometry on MA (50% vs `/VPTARGET`, `/MAGTARGET`), each object. | 0 / 0 | **CHARACTERISED (dual-object, 2026-06-18): native EVIDENCE_AGAINST (0/7 variants compose at P11+P6; VP variants beat benchmark geometrically 10–11 cells but fail RM attribution; MAG-0.5×20 beats RM at P11 — 8 cells/7 instr — but beats benchmark in only 3 cells) / hybrid EVIDENCE_AGAINST (0/7 variants, max 3 wins — VP-FAR). 99/99 cells powered. Consistent with EXP-056 (ZigZag substrate). Favourable-target lever measured-negative on both substrates. Objects never pooled; family stays OPEN; feeds terminal G-015. 0 slots, 0 TEST reads. Audit PASS.** |
| `CF-HA-HARAMI-001/HYP-018` — EXP-065 | hybrid **+** native (S2), individually | EXP-058 | Third-barrier geometry on MA (adaptive cap vs `/THIRD-TIME`, `/THIRD-EVENT`), each object. | 0 / 0 | **CHARACTERISED (dual-object, 2026-06-18): native EVIDENCE_AGAINST (0/4 alt variants compose at P11 — max 2 wins vs 5 quorum; replicates EXP-058 ZigZag finding on MA substrate); hybrid INCONCLUSIVE_POWER_LIMITED (max 4 powered cells < P11 quorum). Third-barrier lever closed on MA for Phase 015. Family stays OPEN; feeds terminal G-015. 0 slots, 0 TEST reads. Audit PASS.** |
| `CF-HA-HARAMI-001/HYP-019` — EXP-066 | hybrid **+** native (S3), individually | EXP-059 | Position-management exits on MA (`/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually + combined), each object. | 0 / 0 | **CHARACTERISED (2026-06-18) — native EVIDENCE_FOR via PARTIAL-V2A (21 cells/13 instr/21 non-4h, also mean-positive 11 cells/6 instr); hybrid EVIDENCE_AGAINST (0 arms compose). Dual-object re-run under D0-amendment-001. 0 slots, 0 TEST reads. Audit PASS.** |
| `CF-HA-HARAMI-001/HYP-020` — EXP-067 | **hybrid** combined champion | EXP-060 | Combined hybrid MA champion vs `RM-hybrid` + disclosed native & ZigZag champions — integrative readout feeding G-015. | 0 / 0 | **DROPPED (Amendment 002, 2026-06-18)** — the hybrid object is EVIDENCE_AGAINST across the entire individual surface (L1 EXP-061 1 cell; S1 EXP-064 0/7; S2 EXP-065 INCONCLUSIVE; S3 EXP-066 0 arms), a combined champion can only assemble per-layer winners (hybrid has none that compose), and the levers are additive-not-synergistic (EXP-060). EXP-067 gates nothing — the native PROCEED-candidate (EXP-068) is the independently-judged G-015 path. Hybrid adjudicated at G-015 on the **disclosed surface reads**. Item retained in the ledger, never deleted or reused. 0 slots, 0 TEST reads. |
| `CF-HA-HARAMI-001/HYP-021` — EXP-068 | **native** combined champion *(merges old N1+N2)* | EXP-060 | Combined native MA champion vs `RM-native` + disclosed hybrid champion — native integrative readout feeding G-015. | 0 / 0 | **CHARACTERISED (2026-06-18) — PROCEED_TO_SCREEN-candidate (G-015 input; gate NOT adjudicated here, P9).** Both predeclared champion arms clear the full G-015 conjunction (median-viable ∧ raw-mean-positive ∧ beats-`RM-native`) at P11+P6: `N-PARTIAL-V2A` 9 cells/5 instr/7 non-4h (P4=PARTIAL_RECOVERY); `N-V2A×ADV-NONE` 14 cells/9 instr/6 non-4h (P4=TAIL_DRIVEN, 63/99; adv_count=0). First Phase 015 native read where the mean co-primary composes (EXP-066 S3 did not require it). Signal present even at single-leg BENCH (6 non-4h FX cells); robust non-4h core ~5 FX cells (GBPUSD/NZDUSD/GBPJPY). Caveats: narrow mean breadth (mean-positive 11–14/99 vs median-viable 45–89); ADV-NONE composition 4h-concentrated and tail-driven → bounded-downside `N-PARTIAL-V2A` is the cleaner candidate definition. Reconciliation 99/99 to EXP-061 M0/H0 + EXP-066 native PARTIAL-V2A at 1e-9; determinism/causality/invariants clean. Hybrid disclosed EVIDENCE_AGAINST (EXP-067 DROPPED, Amendment 002 — hybrid adjudicated at G-015 on the disclosed surface reads), never pooled. 0 slots, 0 TEST reads. Audit PASS (0C/0W/3I). Family stays OPEN — candidate registration only at G-015. |
| `CF-HA-HARAMI-001/HYP-022` — ~~EXP-069~~ | ~~native (N2)~~ | — | **DROPPED (Amendment 001)** — native efficacy/availability/adverse/geometry now covered by the dual-object L1–S3 reads; the native combined champion is EXP-068. Item retained in the ledger, never deleted or reused. | 0 / 0 | **DROPPED** |

**G-015 ADJUDICATED 2026-06-18 — PROCEED_TO_SCREEN (native object); CHARACTERISED_NOT_VIABLE (hybrid
object); phase outcome PROCEED_TO_SCREEN** (`docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-conditioned-harami-full-surface/G-015-gate-review.md`;
desk review, routing operator-ratified 2026-06-18 "PROCEED; register both native arms"). The **native**
object (EXP-068) satisfies the full predeclared conjunction with **both** champion arms — `N-PARTIAL-V2A`
(9 cells/5 instr/7 non-4h, P4=PARTIAL_RECOVERY) and `N-V2A×ADV-NONE` (14 cells/9 instr/6 non-4h,
P4=TAIL_DRIVEN) — each median-viable ∧ raw-mean-positive (CI_low>0) ∧ beats-`RM-native`, composed at
P11+P6; signal present even at single-leg BENCH (6 non-4h FX cells); mean **not structural** (closure-on-mean
rule unmet → family not closed). The **hybrid** object is CHARACTERISED_NOT_VIABLE on the disclosed surface
(EVIDENCE_AGAINST L1/S1/S3, INCONCLUSIVE S2; EXP-067 dropped, inferential disposition); judged individually,
never pooled; does not govern the phase (strongest object governs, design §7). Integrity all-pass (99/99
reconciliation @1e-9; determinism/causality/invariants). **First candidate slot consumed at this gate**
(see candidate-slot row below). **TEST reads spent: 0** (`test-read-ledger.md` unchanged; the first counted
TEST read occurs at the screening scope, not here); holdouts sealed.

**Candidate registration (G-015 PROCEED, 2026-06-18):**

| Candidate ID | Definition | Slot | Status |
| --- | --- | --- | --- |
| `CF-HA-HARAMI-001/CAND-001` (MA-SUBSTRATE / native) | MA(20,50)-native `/STRONG-STAT` conditioned HA harami, MA-segment 3-barrier geometry; **two registered champion arms** — lead `N-PARTIAL-V2A` (PARTIAL-V2A + 1:1 stop, bounded-downside) and disclosed `N-V2A×ADV-NONE` (EXP-060B champion geom + partial scaling, MA cap sole stop-out). Conditioning-object = **native**. | **1 (first slot consumed)** | **RETIRED — family CLOSED at G-016 (2026-06-19, CLOSE_FAMILY, operator-directed)**. Registered 2026-06-18 (G-015 PROCEED); SCREENED TEST_NOT_CONFIRMED at EXP-071/HYP-024 (0/6 binding cells, 4/6 median CI_low ≤ 0; D0 P9); held OPEN for the EXP-074/075 exhaustion-cap follow-up, then **retired** when EXP-075 returned FILTER_INEFFECTIVE (the exhaustion cap is not a lever — bimodality strips winners with losers; EXP-074 located the driver). Real MA-substrate median edge but **no TEST-confirmable tradable edge** (binding raw-mean leg and median edge share one unfilterable driver); registered surface exhausted (Phases 014–016). Slot + all variants retained in the ledger (refuted-on-scope, never deleted/reused). 6 counted TEST reads spent (each binding stratum 1/2); holdout never touched. Reopenable only by a genuinely new lever not on the exhausted surface (own scope/D0/G0). See `G-016-gate-review.md`. EURUSD was TEST-capped instrument-wide (excluded). |

The unbounded-downside arm is disclosed (TAIL_DRIVEN, 4h-concentrated); the bounded-downside
`N-PARTIAL-V2A` is the lead definition. The hybrid mode and the dropped EXP-067/069 items are retained
in this ledger, never deleted or reused.

**G-015 outcome menu (for the record):** PROCEED_TO_SCREEN (met, native) / CHARACTERISED_NOT_VIABLE
(structural mean-irrecoverability on **both** objects — unmet; native mean not structural) /
MEAN_RECOVERABLE—FOLLOW-UP (unmet; the raw-mean co-primary composes at CI_low>0) /
SUBSTRATE-METHOD_DEFECT / INCONCLUSIVE (unmet; native fully powered 99/99).

**Out of scope (recorded):** any net/cost-adjusted metric (gross only); MA-parameter sensitivity
(MA(20,50) fixed); fully-MA-native conditioning's *full* geometry surface (a promotion follow-up,
not this phase); any HA-price outcome metric; position-in-move as a live filter; parameter tuning
or post-result variant selection beyond the predeclared OAT grids; any intermediate early-closure
gate; any TEST or holdout contact; candidate registration before G-015 PROCEED.

## Phase 016 Batch (CF-HA-HARAMI-001 Candidate Screening)

**Opened:** 2026-06-18 (Phase 016 design; **G0 PASS 2026-06-18**, D0 ratified).
**Governing design:** `docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/design.md`
**Candidate:** `CF-HA-HARAMI-001/CAND-001` (MA-native, first slot consumed at G-015 2026-06-18).
**Lead arm:** `N-PARTIAL-V2A` (bounded-downside, P4=PARTIAL_RECOVERY). Disclosed arm: `N-V2A×ADV-NONE`.
**Why:** Phase 015 returned PROCEED_TO_SCREEN on the MA-native object (both champion arms
satisfy the full G-015 conjunction at P11+P6). Phase 016 is the **first TEST contact** in the
family's history. Its job: (1) calibrate the evaluation method on the MA-native harami population
(TRAIN-only), (2) confirm the non-4h FX core in the one-shot TEST stratum, (3) conditional
cost-aware follow-up if the TEST confirms.
**No new variant branches or families registered in Phase 016** — all branch registrations
occurred in Phase 014/015. Phase 016 exercises already-registered branches; the hypotheses here
are about out-of-sample evidence, not new parameter or detector variants.

### Hypothesis ledger

| Hypothesis | EXP-ID | Object / scope | Analogous prior | Slot | Status |
| --- | --- | --- | --- | --- | --- |
| HYP-023: method calibration — does the per-event gross `N-PARTIAL-V2A` evaluation method have controlled FPR (≤0.05/cell), finite MDE, and determinism on the MA-native harami event population in the predeclared TEST family cells? | EXP-070 | MA-native harami events, TRAIN-only, predeclared TEST family cells | EXP-027 (AVWAP), EXP-044 (Phase 011) | 0 / 0 TEST reads | **PENDING — G0 required** |
| HYP-024: one-shot TEST confirmation — on the TEST stratum of the predeclared non-4h FX core (excluding EURUSD), does `N-PARTIAL-V2A` show per-event gross expectancy CI_low>0, beat RM-native, and compose at the predeclared composition threshold (≥3 cells/≥2 instruments, Holm α=0.05 + calibrated margin)? | EXP-071 | MA-native harami events, **first counted TEST read** per predeclared stratum | EXP-037/038 (AVWAP Phase 008) | 0 slots / **6 counted TEST reads spent** (GBPUSD-5m/1h, NZDUSD-1h/2h, GBPJPY-30m, US2000-4h) | **TEST_NOT_CONFIRMED (2026-06-19)** — 0/6 cells clear the conjunction; 4/6 median CI_low ≤ 0 (majority directional negative). CAND-001 retired on this scope; family OPEN. Composite positive but event-pooled/GBPUSD-5m-dominated (non-binding disclosure). Audit PASS; post-gov APPROVE. Routes to EXP-074/HYP-027. |
| HYP-025 (conditional): under the frozen per-instrument cost model, does the EXP-071 confirmed cell set retain CI_low>0 net per-event expectancy, and does a targeted tail-filter/capped-downside treatment recover net positivity in the `N-V2A×ADV-NONE` TAIL_DRIVEN cells? | EXP-072 | MA-native harami events, frozen cost model, TEST strata from EXP-071 | EXP-030 (AVWAP Phase 007) | 0 / further TEST reads by D0 | **CONDITIONAL — opened only if EXP-071 TEST_CONFIRMED and explicit operator direction; own D0 required** |
| HYP-026 (conditional): across the EXP-071 confirmed cell set, which portfolio weighting scheme (equal-weight, inverse-ATR-volatility, instrument-cluster, domain-stratified) delivers the best gross portfolio-level expectancy on TRAIN and does it hold in the TEST stratum? Does the combined portfolio pass the programme's portfolio fitness gate (EXP-018 analog) on the harami event population? | EXP-073 | MA-native harami events, multiple weighting schemes (TRAIN selection), TEST portfolio-aggregate disclosure | EXP-018 (portfolio fitness), Phase 008 Package A/B selection | 0 / TEST portfolio disclosure (no new per-stratum counted reads) | **CONDITIONAL — opened only if EXP-071 TEST_CONFIRMED; may run in parallel with EXP-072; own D0 required** |
| HYP-027 (diagnostic): on the TRAIN stratum, **across the full 99-cell MA-native harami substrate**, which causal entry-time features separate the large-loss tail of `N-PARTIAL-V2A` per-event returns from the rest — in particular an exhaustion-magnitude upper bound (`m_sofar/atr`) and harami-polarity↔reversal-direction agreement (both currently unconditioned) — and do they replicate across a material share of the substrate? Characterization only; no filter selected, no parameter tuned. | EXP-074 | MA-native harami events, **TRAIN-only**, **full 99-cell MA-substrate matrix** (GBPUSD-5m a named continuity cell, no longer the binding object); surface = 14 features × 3 framings × 99 cells, file-drawer control = **per-domain** dual-metric verdict (per-cell any-feature separability rate + per-feature single-lever breadth ≥50% of the domain's powered cells + within-domain median CI; pooled-substrate disclosed-only) + 2 pre-registered leads | EXP-050 (harami-in-context characterization), EXP-070 (TRAIN-only calibration) | 0 / **0 TEST reads (TRAIN-only)** | **CHARACTERISATION_DELIVERED (2026-06-19; audit CONDITIONAL PASS 0C/2W/3I, post-gov APPROVE).** 99/99 cells resolved (237,698 events; 67 powered, 2h/4h = 0). **Binding per-domain verdict = no location-monotone uniform lever** (5m NO_SEPARATOR sep_rate 0.35; 15m/30m/1h SEPARABLE_NO_UNIFORM_LEVER 0.88/0.71/0.94; 2h/4h INCONCLUSIVE_POWER); disclosed pooled NO_SEPARATOR. **But this masks the real finding:** H1 `msofar_atr` separates the **extreme q05 tail** at rank-biserial 0.68–0.80 (AUC ~0.84–0.90), 100% of powered cells in every powered domain (median 0.70–0.79) — disqualified as a "candidate separator" solely by the pre-registered **all-framing consistency gate**, which is structurally blind to tail-shape (bimodal) effects: the feature explaining the EXP-071 mean failure is the one the gate rejects. **H2 (polarity) REFUTED** (median ~0, 0% clear bar). `favdist_atr` ≡ 0.5·`msofar_atr` exactly (V2A geometry; effective surface 13 not 14). Binding verdict **stands as written**; gate **not** retro-edited (goalpost-moving on a pre-registered criterion) — resolution = framing + routing. Item retained (diagnostic outcome, never deleted/reused). Scoped under `D0-amendment-005` (GBPUSD-5m + 5) then widened to 99 cells under `D0-amendment-006`. **0 candidate slots, 0 counted TEST reads; holdout untouched.** Routes to EXP-075/HYP-028. |
| HYP-028 (TRAIN-design, conditional on EXP-074 SEPARATOR_FOUND(exhaustion)): on the TRAIN stratum, across the full 99-cell MA-substrate, does an exhaustion-cap entry filter (upper bound on `m_sofar/atr`) materially improve the `N-PARTIAL-V2A` harami — lifting the raw-mean leg that failed EXP-071 without destroying the median edge, beats-RM, or tradable event count — and how much of any gain is captured by a single uniform (deployable) rule vs per-cell overfit? Designs and **locks** the filter on TRAIN only; no holdout/TEST read. 4 design arms (F1/F2 form × M-GLOBAL/M-PERCELL selection), pre-declared U-grid pooled p85/p90/p95. M-PERCELL is diagnostic-only (overfit ceiling), never deployed. | EXP-075 | MA-native harami events under an exhaustion-cap gate, **TRAIN-only**, full 99-cell matrix | EXP-068/074 (TRAIN-design machinery), Phase 008 A1/A2 TRAIN-design rules | 0 / **0 TEST reads (TRAIN-only)** | **FILTER_INEFFECTIVE (2026-06-19; audit CONDITIONAL PASS 0C/1W/2I, post-gov APPROVE).** ACTIVATED on EXP-074's framing-resolved q05-tail evidence (the formal SEPARATOR_FOUND was not literally returned — the all-framing consistency gate vetoed the H1 lead; proceed operator-ratified under `D0-amendment-007` with the tail framing pre-registered a priori, `favdist_atr` dropped, H2 not pursued). **The exhaustion cap is not a lever:** M-GLOBAL (deployable) adds **0 improved cells in every band-core domain** at the locked U and across the whole pre-declared grid (`u_sensitivity` = 0 improved domains at p85/p90/p95, both forms F1/F2); M-PERCELL (overfit ceiling) tops out at 30m **+0.118 < 0.15** uplift (15m −0.059, 1h 0.000). Mechanism (EXP-074 bimodality, shown economically): high `msofar_atr` entries are bimodal — an upper cap strips big winners with the q05 losers (e.g. USTEC-1h mean +0.167→−0.089), netting a wash/negative on the joint four-leg criterion; the q05-tail separator is real but **not actionable as an entry cap**. Disposition robust to the 0.15 bar (FILTER_OVERFIT at 0.10 routes identically — do not spend the holdout). Baseline `r_e` reconciled to EXP-074 @1e-9; 67 powered (=EXP-074); `undef_share≡0` on the qual set; determinism by construction. Locked filter frozen (`deployable=false`, sha256-pinned) but NON-CONFIRMATORY and carried nowhere — **no holdout read warranted.** **Closes the exhaustion-cap route**; CF-HA-HARAMI-001 stays REGISTERED/OPEN; family-closure decision → G-016. Item retained (refuted outcome, never deleted/reused). **0 candidate slots, 0 counted TEST reads; holdout untouched.** |

### TEST-stratum accounting (Phase 016)

- **At Phase 016 open (2026-06-18):** 0 counted TEST reads in any harami stratum.
- **After EXP-070 PASS:** the binding TEST family is frozen (predeclared from EXP-068
  `N-PARTIAL-V2A` non-4h cells, excluding EURUSD); the freeze file is hashed before any
  TEST row is loaded.
- **After EXP-071 (SPENT 2026-06-19):** 6 binding strata each incurred 1 counted read in
  `test-read-ledger.md` (GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h) —
  each now at 1/2 lifetime, all still open. The EXP-071 equal-weight portfolio composite is a
  disclosure against all 6 member strata — no additional per-stratum counted reads. (Budget was
  ≤9 strata = the full `N-PARTIAL-V2A` G-015 passing count ex-EURUSD; the binding family froze at
  6 cells, all read.) EXP-073 not opened (conditional on TEST_CONFIRMED).
- **EURUSD excluded instrument-wide:** ineligible for any harami stratum-specific TEST
  confirmation; EURUSD strata in EXP-068 `N-PARTIAL-V2A` are not in the declared TEST
  family. 4h cells from other instruments are included (no domain exclusion).

### Disposition (G-016 pending; EXP-071 result recorded 2026-06-19)

EXP-071 returned **TEST_NOT_CONFIRMED** (0/6 cells clear; 4/6 median CI_low ≤ 0). Per the
predeclared options this **retires CAND-001 on this scope; the family stays OPEN**. G-016 desk
adjudication still pending — to ratify the readout, the event-pooled/GBPUSD-5m-dominated composite
caveat, and the EXP-074/HYP-027 TRAIN-only diagnostic routing. EXP-072/073 not opened (each was
conditional on TEST_CONFIRMED).

## Phase 017 Batch (CF-CAPGEO-001 Qualifier & Protocol Validation — "validate the yardstick")

**Opened:** 2026-06-20 (Phase 017 design; **G0 PENDING** — D0 ratification required before any
result-producing code).
**Governing design:** `docs/experiments-docs/checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md`
**Purpose:** Before the new Expectancy-Robust qualifier (`ASS`) or the expanding-window walk-forward
protocol (`WF-EXPANDING`) may adjudicate any CF-CAPGEO-001 candidate, validate them framework-style
— mirroring the 001–003b "harden the yardstick before measuring any signal" era. This is
**methodology validation, not candidate screening**: **0 candidate slots, 0 counted TEST reads**
(synthetic substrates + current-data dogfood, TRAIN-only). Components registered in
`components/global-techniques.md` (`ASS`, `WF-EXPANDING`).
**Why now:** the deepest retrospective lesson is that expectancy is a smoothed mean, fragile to the
bimodal/tail structure that killed both prior families (§4.2); a new qualifier must be trusted before
it can bind a verdict (§5.1). Scoring posture is therefore **expectancy + median + tail diagnostic**,
and the qualifier is binding **only** on G-017 PASS.

### Component-validation ledger (no candidate slots)

| ID | EXP-ID | Question | Slot | TEST | Status |
| --- | --- | --- | --- | --- | --- |
| `ASS/VAL-001` | EXP-076 | **Synthetic-substrate recovery:** does `ASS` recover known expectancy/median/tail to predeclared (fixture-calibrated) tolerance across unimodal, skewed, bimodal, and sparse/uneven synthetic signal types, and does shrinkage pull sparse types toward the pooled prior while leaving rich types alone? | 0 | 0 (synthetic) | **RECOVERY_VALIDATED_G017a (2026-06-20)** — recovery PASS all 198 (type,n) cells (expectancy+median, worst ratio 0.72<0.85); coverage in-band ∀ n≥30, only n=15 expectancy sub-band (disclosed sparse-stress diagnostic = intrinsic small-sample bootstrap floor of the mean, not a defect); shrinkage monotone + sparse-pull OK, sole literal breach the predeclared n=2000 rich-pull marginal (120/2120=0.0566). Two governance dispositions → G-017 (coverage n≥30 binding; downstream n<30 expectancy guard + EXP-077 small-n FPR stratum). Audit CONDITIONAL PASS (1C-resolved: verdict made per-stratum, no recompute). Item retained. |
| `ASS/VAL-002` | EXP-077 | **Dogfood + calibration under `WF-EXPANDING`:** FPR control (≤0.05) on known-null synthetic populations, finite per-domain MDE, and reliability of `P(return>X)` — all measured **under the expanding-window walk-forward protocol**, with the per-fold counted-read accounting against the 2-read cap validated. Current-data dogfood is TRAIN-only. | 0 | 0 (TRAIN-only) | **VALIDATED_WITH_GUARDS (per-stratum, 2026-06-20)** — error-control + protocol legs validated under `WF-EXPANDING`. **MDE finite ∀ n≥30; counted-read accounting 8/8 (cap honored); dogfood 12/12 cells (fence held, 0 reads); determinism+anchor PASS.** `verdict.json` leg flags FPR=FAIL/reliability=FAIL are faithful to the frozen D0 gates but NOT whole-qualifier failures (audit re-derived all numbers, PASS 0C/1W/3I): **FPR-U0** binding crossings (n=120/1000/2000, 0.051–0.052) are MC noise around a margin calibrated TO 0.05 (binomial P(≥edges\|p=0.05)=0.36–0.43; all binding cells Wilson-hi≤0.075); **FPR-B_zero** mild inflation n=30/60 (0.059) decays to ~0 by n≥120 — the EXP-076 small/mid-n bimodal under-coverage → **Guard (i): defer expectancy edge-calls to median at effective-n≤60** on bimodal/asymmetric mean-null strata. **Reliability** holds X=0/0.05/1.0; X=2.0 fails the slope sub-gate ONLY (0.652) while max-gap=0.017 & corr=0.934 → **Guard (ii): D2.4 slope sub-gate inapplicable at compressed predicted-P range (bind on max-gap)**; D2.4 gate NOT retro-edited. No PROTOCOL_DEFECT. Two guards are disclosures to terminal G-017 (decided after EXP-078), not acted on in Phase 017. Item retained. |
| `ASS/VAL-003` | EXP-078 | **Shape discrimination:** does the tail/bimodality diagnostic actually flag bimodal vs unimodal populations (directly closing the EXP-074 "guard blind to tail-shape" gap), and how sensitive is `ASS` to its one tunable knob `k` (shrinkage constant)? | 0 | 0 (synthetic) | **SHAPE_DISCRIMINATION_FAIL + k_FRAGILE → DISCOVERY_ONLY input (per-stratum, 2026-06-21)** — binding double-FAIL. **Shape FAIL both legs:** U false-flag fails the n=30 binding floor (0.135–0.152; passes ≤0.046 n≥60); B detection is a **2-way shape split** (pooled FAIL masks it) — strongly-separated bimodals detect (`B_strong` \|g\|=0.60 dip-bimodal PASS; `B_neg` \|g\|=0.50 0.76@n30→1.0) but the **subtle median-positive minority-catastrophe shape `B_zero` (\|g\|=0.25) / `B_pos` (\|g\|=0.067) — the CF-HA-HARAMI-001 failure shape — is structurally undetectable and decays to 0 with n** (both legs blind: true \|g\|<τ_gap=0.30 AND not dip-bimodal, dip_p≈0.99). **`k`-sensitivity ROUTING_FLIP:** K1 shrinkage INVARIANT; K2 shrunk-expectancy null edge-call FPR k-fragile — flips CONTROLLED→INFLATED at the 2× multiplier k=240 (shrinkage pulls the null toward the positive SP prior pool_mean=+0.518 vs a margin frozen at k=120). Determinism byte-identical (**NOT PROTOCOL_DEFECT**); integrity anchors diff 0.0 to EXP-076/077; mad_zero=0; diptest 0.11.0. Audit **PASS-trust (0C/2W/4I)** — double-FAIL independently reproduced (mixture means to 1e-4, U0 false-flag exactly, sub-0.30 true gaps, K2 shrink-toward-prior mechanism) → **implementation-faithful, no fix-and-rerun**; W1 K2 deployed-k labels self-calibration noise (read across-k fragility), W2 CI-coverage k-leg not swept (2/3 dispositions) — both non-material. **`ASS` shape leg only PARTIALLY closes the EXP-074 gap.** Item retained (methodology-validation negative; file-drawer record). |

`EXP-079` reserved (inactive) for a dedicated `WF-EXPANDING` isolation read should EXP-077's dogfood
show the protocol needs to be validated apart from the qualifier. Threshold/tolerance constants are
**calibrated via a fixture/bite check** (retrospective §5.3), not hand-set.

### Gate

**G-017** (terminal, after EXP-076/077/078): **`ASS_VALIDATED`** (recovery within tolerance ∧ FPR
controlled + finite MDE + reliable `P(return>X)` under `WF-EXPANDING` ∧ shape diagnostic
discriminates) → `ASS` is **binding-eligible** for CF-CAPGEO-001 (Phase 018). Else **`DISCOVERY_ONLY`**
→ `ASS` non-binding; the frozen referee suite remains the binding gate. Nothing in Phase 018 spends a
counted read on `ASS`-based adjudication until G-017 PASS.

**G-017 ADJUDICATED 2026-06-21 — `DISCOVERY_ONLY`** (`G-017-gate-review.md`; predeclared D5 mechanical
routing). Phase 017 slate complete: EXP-076 RECOVERY_VALIDATED_G017a ✓; EXP-077 VALIDATED_WITH_GUARDS
(two bounded per-stratum guards) ✓; **EXP-078 SHAPE_DISCRIMINATION_FAIL + k_FRAGILE ✗.** Six of eight
`ASS_VALIDATED` legs hold; the two EXP-078 legs FAIL (shape diagnostic structurally blind to the subtle
median-positive minority-catastrophe shape; shrunk edge-call FPR `k`-fragile), so the conjunction cannot
hold → **`ASS` non-binding (discovery use only); the frozen referee suite remains the binding gate for
Phase 018.** No `PROTOCOL_DEFECT` (determinism held byte-identically; accounting cap honored 8/8).
**Carried forward:** the EXP-077 guards (defer-to-median at effective-n≤60 on bimodal mean-null strata;
bind reliability on max-gap at compressed predicted-P) and the EXP-078 limitations (subtle-bimodal blind
spot; clean-unimodal false-flag needs n≥60; `k`-fragile edge-call FPR), plus the gate's external-validity
bound (binding legs are i.i.d.-synthetic; moving-block CI coverage on dependent real data is unvalidated)
and re-validation conditions C1–C4 (gate §10). 0 candidate slots, 0 counted TEST reads; ledger unchanged.

## Phase 018 Batch (CF-CAPGEO-001: Data-Derived Exit / Capture Geometry) — GATED

**Registered:** 2026-06-20 (family `REGISTERED`, SCREENING-GATED).
**Opens only when:** INFR-003 complete (5-year data + holdout re-seal + VAL-005 PASS). **G-017 resolved
2026-06-21 — `DISCOVERY_ONLY`:** the binding qualifier is therefore the **frozen referee suite**, with
`ASS` admitted as a non-binding discovery overlay (not `ASS_VALIDATED`). **BOTH PRECONDITIONS MET
2026-06-21** (INFR-003 COMPLETE ∧ VAL-005 PASS; G-017 `DISCOVERY_ONLY`). **Phase 018 D0 RATIFIED —
G0 PASS 2026-06-21** (`D0-predeclarations.md`) — carries the Phase-017 guards (§D6), the §D7 `[15,8000]`
bracket re-confirmation, the frozen EXP-082 derivation rule (§D3), and the separability gate + G-018
conjunction (§D4). **G0 closed:** D9 bite-check GREEN (separability constants FROZEN `K_tail=3.0,
τ_tail=0.06, δ=0.40, m=m_cell`, floor n≥120; `B_pos` blind spot dispositioned benign — `bite-check/`);
D2 (no per-variant rationing) + D8 (EURUSD eligible, clean slate) operator-ratified. **Phase 018 OPEN;
pipeline opens at EXP-080** (HYP-001 readiness, 0 slots / 0 TEST reads).
**D0-amendment-001 (operator-directed 2026-06-22):** HYP-004 (EXP-083) is **split** — EXP-083 becomes the
**TRAIN-only candidate screen** (G-018a + separability gate; emits the hash-pinned valid-candidate set;
**0 counted TEST reads**), and the counted `WF-EXPANDING` confirmation (which spends **counted read #1**)
is deferred to a **reserved-conditional EXP-084**, opened only on a non-empty EXP-083 valid set + operator
ratification. No frozen constant/rule/gate/verdict changes; the D4.1 freeze-and-hash-pin-before-TEST
legitimacy is preserved as an inter-experiment hand-off. See
`checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-amendment-001-split-exp083-train-screen.md`.
**Governing design:** Phase 018 [`design.md`] + [`D0-predeclarations.md`]
(`checkpoints/2026-06-20-018-capgeo-exit-geometry/`).
**Candidate family:** `CF-CAPGEO-001` — data-derived exit / capture geometry on four frozen entry
substrates. Family spec: `candidate-families/cf-capgeo-001.md`.

### Predeclared surface (countable items — entered now per the file-drawer rule)

| Field | Predeclared value |
| --- | --- |
| Candidate-family count | 1 (`CF-CAPGEO-001`) |
| Entry substrates (frozen, never tuned) | `SUB-AVWAP`, `SUB-HARAMI-PARTIAL-V2A`, `SUB-HARAMI-V2A-ADVNONE`, `SUB-RANDOM` (matched-control) |
| Domains | 15m, 1h, 4h |
| Instruments | **16** — VAL-003 universe **minus DE30** (dropped at INFR-003 §3.1; broker m1 stale). *(Amended at Phase 018 D0, 2026-06-21; "all 17" → 16; removes one instrument, consumes no new slot.)* 5-year, post-INFR-003, VAL-005-admitted. |
| Open axis | exit / capture geometry + sizing only |
| Registered exit/sizing branches | `/EXIT-DERIVED`, `/EXIT-RR`, `/EXIT-TRAIL`, `/EXIT-VP`, `/EXIT-PARTIAL`, `/SIZE-VOLADJ` (`/MTF`, `/VOLREGIME` deferred) |
| Derived candidates (Phase 018 D0, under `/EXIT-DERIVED`) | `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` — triple-barrier exits whose barriers are mechanically set from EXP-081 cell statistics (D0-predeclarations §D3; freeze-the-rule). Carried to EXP-083; refuted/blocked/inconclusive variants retained in the ledger. |
| Binding qualifier | **frozen referee suite** (G-017 resolved `DISCOVERY_ONLY` 2026-06-21); `ASS` is a non-binding discovery overlay |
| Co-primary endpoint | expectancy + median + tail diagnostic (real prices) |
| Binding pre-TEST gate | **separability check** (binding net-expectancy leg and favourable signal not driven by one unfilterable mechanism — retrospective §4.1) |
| Protocol | `WF-EXPANDING` (counted-read accounting honors the 2-read cap; holdout never a fold) |
| Candidate slots | reserved; consumed only per derived/benchmark exit variant at the Phase 018 screening gate |
| TEST reads | 0 spent at registration; counted reads only at the Phase 018 screening gate, on the new 5-year strata, after the separability gate |

No candidate slot is consumed by registration. Each derived or benchmark exit variant carried to a
binding read is a countable item registered at the Phase 018 D0 with its own EXP-ID. Refuted,
blocked, and inconclusive variants remain in the file-drawer ledger — never deleted or reused.

### Phase 018 experiment outcomes

| EXP | HYP | Role | Slots / TEST | Status |
| --- | --- | --- | --- | --- |
| **EXP-080** | HYP-001 | Substrate/exit **readiness** (4 frozen substrates × 16 instruments × {15m,1h,4h} = 192 substrate-cells, 5-year data): determinism, look-ahead invariants, coverage map, D7 `[15,8000]` bracket re-confirmation, moving-block null-FPR machinery sanity, harami entry-identity. | 0 / 0 | **COMPLETE 2026-06-22 — READINESS_DELIVERED; re-audit PASS.** 184/192 substrate-cells READY. **2 cells `COVERAGE_EXCLUDED` (retained, never deleted): US500-4h (dropped 0.251), JP225-4h (0.281)** — genuine 4h cash-equity-index coverage sparsity (invariants+determinism pass; US500-4h borderline; EXP-043 index-coarse-domain precedent) → excluded from EXP-081 with record. **Member set for EXP-081 = 46 instrument×domain cells.** D7 **192/192 IN_BRACKET** (`ASS` discovery in its validated regime ∀ cell; frozen referee suite binding regardless — D0 §D7). Null-FPR machinery **CONTROLLED in the binding operating regime n≥120** (wilson_hi 0.064–0.068) at the validated m_cell scale (N_NULL=5000, N_BOOT=10000); small-n (n<120) inflation disclosed/non-binding (D0 §D6 Guard (i)/§D9). 0 nondeterministic, 0 invariant failures; **harami entry-identity holds ∀ cells** (both harami substrates share one MA-native conditioned HA-harami entry → entry-level counted-read accounting coincides; they remain distinct downstream by exit). Regression vs VAL-005 frame-identical (85839 rows). **0 candidate slots, 0 counted TEST reads** (full-analysis-slice readiness exposure = disclosure, entered in `test-read-ledger.md`); holdout sealed. Initial run was SUBSTRATE_REFUTED on two verdict-material audit defects (dropped-fraction metric mis-denominatored vs a 24/7 clock; null-FPR probe under-scaled) — both fixed, Stage-5 governance ruled re-scale to the validated machinery, re-run + re-audit PASS. |
| **EXP-081** | HYP-002 | **Characterize** (TRAIN-only, gross): per-substrate realized return-structure features over the per-event adaptive cap (real prices) — the **frozen D3 inputs** for the `/EXIT-DERIVED` candidates `D1-MEDIAN-CAPTURE` / `D2-TAIL-ROBUST` / `D3-CAPTURE-EFFICIENT`. 4 substrates × 46 member cells = 184 substrate-cells. | 0 / 0 | **COMPLETE 2026-06-22 — CHARACTERISATION_DELIVERED; audit PASS (0C/1W/3I).** No new countable item; no item refuted — this experiment **locks the D3 inputs** the registered derived candidates consume at EXP-082/083. 184/184 cells delivered; 0 underpowered (n_usable 46–5535, median 1083), 0 nondeterministic, harami PARTIAL-V2A ≡ V2A-ADVNONE geometry exact, EXP-080 entry reconciliation 184/184 (TRAIN ≤ full), holdout untouched. **D3 EXP-082-ready:** T_fav=MFE_med/MFE_q40 (~3.2–3.4 ATR), S_adv=m_anti else MAE_q90 (m_anti NaN 183/184 → MAE_q90 fallback ~9–9.7 ATR, exactly as D9 anticipated), H_cap=TTP_q75/TTP_med (~37–52 bars); no cell below the 30-event floor. **Mechanism (per-cell paired vs within-cell SUB-RANDOM): gross capture availability ≈ random** (harami median MFE below random 17/46, AVWAP coin-flip 28/46, outcome-median edge ~chance 23–25/46) — move availability is NOT the differentiator (AVWAP-situation/EXP-047 echo on 5-year data); the only structure is the **outcome shape** — harami **median +0.135 / mean ≈ 0.000, 33/46 cells median>mean** (catastrophic left-tail drag, tailmass 0.0526 > random 0.0437) = **CF-HA-HARAMI-001 median-positive/mean-killed signature reproduced on disjoint 5-year data**; AVWAP roughly symmetric (mean +0.157 ≈ median +0.150); random baseline median +0.085. m_anti resolves 1/184 (US500-1h AVWAP) — catastrophe a heavy continuous tail, not a separated mode (dip genuinely exercised, dip_p median 0.976). `ASS` discovery NON-BINDING (G-017). **Consequence:** EXP-082 derived-exit value must come from the adverse/tail leg (S_adv truncating the catastrophe); EXP-083 separability gate is the crux. **0 candidate slots, 0 counted TEST reads** (TRAIN-only disclosure, entered in `test-read-ledger.md`); holdout sealed. |
| **EXP-082** | HYP-003 | **Derive** (TRAIN-only, deterministic): apply the frozen D0 §D3 mechanical rule to the EXP-081 cell statistics → triple-barrier exits for the registered `/EXIT-DERIVED` candidates `D1-MEDIAN-CAPTURE` / `D2-TAIL-ROBUST` / `D3-CAPTURE-EFFICIENT`. 3 candidates × 184 member cells. | 0 / 0 | **COMPLETE 2026-06-22 — DERIVATION_DELIVERED; audit PASS (0C/1W/3I).** **No new countable item; no item refuted** — this experiment **locks the parameterization** of the already-registered `/EXIT-DERIVED` items (`D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT`) that EXP-083 carries to TEST. **552/552 valid triple-barrier exits** (184 cells × 3 candidates); 0 underpowered, 0 degenerate; determinism byte-identical; harami triple-identity holds (46×3 bit-identical); EXP-081 provenance fingerprint asserted 8/8; the binding derivation function `xen.capgeo_exits.derive_barriers` is **sha256-pinned** (`34d03f45…`) — EXP-083 imports it and re-fits the barriers per WF fold-TRAIN (causal re-fit, no human selection; D3/D5/D4.1). **Mechanism caveats (carried; not verdict-material — the rule was applied faithfully, the dormancy is the honest D9-anticipated output):** (a) the 3 registered candidates collapse to **2 distinct exit definitions on this snapshot** — D1≡D2 on 184/184 cells because `m_anti` resolves in only 1/184 (US500-1h `SUB-AVWAP`) and there `m_anti`=1.79<`MAE_q90`=9.0, so `D2`'s `min(m_anti,MAE_q90)`=D1's value (D1/D2 remain **distinct functions** — diverge iff `m_anti>MAE_q90`; an EXP-083 fold subsample could separate them; account them distinct in the {candidate × stratum} Holm grid); (b) the D3 rule's catastrophe-engaging `m_anti` instrument is **dormant 549/552** (the catastrophe is a heavy *continuous* tail, dip_p median 0.976, not a separated mode) so the adverse leg reverts to a generic `MAE_q90` stop ~9 ATR; (c) that stop sits **at** the catastrophe edge `|q05|` (median `S_adv−|q05|`=−0.008, stop outside catastrophe ~50% of cells) in a wide-stop/modest-target geometry (`T_fav/S_adv`≈0.35) = the **CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" geometry reproduced in the derived exit** → **EXP-083's separability gate (S2) is the crux.** No edge/tradability claim. **0 candidate slots, 0 counted TEST reads** (derivation off TRAIN-only inputs — no market data read; disclosure entered in `test-read-ledger.md`); holdout sealed. |
| **EXP-083** | HYP-004a | **TRAIN-only candidate screen** (D0-amendment-001, 2026-06-22): apply the 3 derived candidates (`D1`/`D2`/`D3`, frozen `derive_barriers`) **and the full enumerated benchmark grid** (`/EXIT-RR`, `/EXIT-TRAIL`, `/EXIT-VP`, `/EXIT-PARTIAL` incl. named PARTIAL-V2A/V2A-ADVNONE/AVWAP-FH arms, `/SIZE-VOLADJ` vs raw baseline) to the frozen-substrate held positions on the **TRAIN region only**; run the **G-018a gross screen** (expectancy + median + tail vs `SUB-RANDOM` + per-cell matched-random) and the **binding separability gate (S1 ∧ S2)**; emit + **hash-pin** the surviving **valid-candidate set** + the Holm rule. No TEST row read. 4 substrates × 46 member cells × {3 derived + benchmark grid}. | 0 / **0 (TRAIN-only)** | **COMPLETE 2026-06-22 — SCREEN_DELIVERED; re-audit PASS.** No new countable item (benchmark/derived variants registered at D0); EXP-ID split consumed no new slot. **TRAIN-only eligibility, NOT an edge claim**; valid set hash-pinned (sha256 `fa4035f3…`) + Holm-over-grid rule = the binding EXP-084 hand-off. **n_valid=26 = 4 S2-PASS (all `SUB-HARAMI-V2A` × AUDUSD × 1h, n=988) + 22 S2-DEFERRED (`SUB-AVWAP` 4h NZDUSD/USDCAD/USTEC, n<120, binding S2 not evaluated); 4 underlying cells; 98.2% (2033/2070) died at the cheap G-018a gross screen.** **Per-item outcomes (refuted/inconclusive items RETAINED in the ledger, never deleted):** `/EXIT-DERIVED` `D1-MEDIAN-CAPTURE`/`D2-TAIL-ROBUST`/`D3-CAPTURE-EFFICIENT` — **NOT in the binding S2-passed set; non-distinctive / inconclusive on TRAIN** (survive only in the deferred AVWAP-4h cells, alongside not over conventional arms) → **the data-derived-beats-conventional thesis is unsupported on TRAIN**; `/EXIT-RR` (`RR-1.5/2/3`) + `/EXIT-PARTIAL` (`AVWAP-FH`) — the 4 binding S2-passed survivors (conventional arms); `/EXIT-VP` (`VP-POC`) — 1 deferred survivor (USDCAD-4h; selection-on-geometry disclosed — scored on the favourable-side-POC subsample); `/EXIT-TRAIL` (ATR k=1/2/3 + struct) + `/SIZE-VOLADJ` (non-distinct in the ATR-normalized frame) — **0 survivors**. Mechanism: genuine favourable-capture attribution (all 26 x_fav>0 mean 1.33 ATR, x_tail≤0; 0 tail-truncation artifacts) — NOT the EXP-082 trap; RR S2-passes are stop-truncation-to-point-mass (magnitude-unpriced −7.28 ATR/stop, deferred to EXP-084 cost layer). **Harami slate consolidation (audit C1 fix, operator-directed):** the two registered harami substrates `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` are **entry-identical** and, because this screen applies the full candidate surface to every substrate, were fully redundant (byte-identical candidate returns) — scored against *different* random nulls (control seeded by substrate index), which let control-draw noise flip a survivor's valid flag. They are **deduped to ONE canonical screened stratum `SUB-HARAMI-V2A`** for this screen (4→3 screened substrates; n_rows 2760→2070); both registry substrate entries are **retained** (screen-stage redundancy collapse, not a deletion). W1 fix: per-candidate `m_cell` calibration (was per-cell reuse, anti-conservative for large-target RR). **0 candidate slots, 0 counted TEST reads (TRAIN-only disclosure; ledger unchanged, all 48 strata 0/2 open); holdout sealed; determinism byte-identical.** **HYP-004b EXP-084 (counted read) RESERVED-CONDITIONAL — NOT OPENED; G-018 decision pending operator ratification** (decline → close HYP-004 at 0 reads, or ratify a narrow EXP-084 on the 4 conventional AUDUSD-1h survivors). |
| **EXP-085** | HYP-004 cost read-gate | **TRAIN-only gross→net cost read-gate** (D0-amendment-002, operator-directed 2026-06-22): apply a predeclared per-event cost/slippage + holding-time financing model (conservative, data-anchored, never tuned; exact constants frozen at EXP-085 scope before any TRAIN read) to the realized exit paths of **all 26 EXP-083 hash-pinned valid `{candidate × stratum}` survivors** (the 4 S2-PASS **and** the 22 S2-DEFERRED, per operator decision — complete net picture), TRAIN region only; re-evaluate **net** per-event expectancy + median per stratum (moving-block bootstrap one-sided `CI_low`) + net matched-random excess companion. Asserts the `fa4035f3…` sha256 first; reads the valid set verbatim (no re-screen). **Stop before any TEST row.** | **0 counted TEST reads / 0 candidate slots** — cost layer on the registered survivors (EXP-030 precedent; no new countable candidate item). | **COMPLETE 2026-06-22 — `NET_SURVIVES` (per-stratum-masked; audit PASS 0C/2W/3I).** 21/26 NET_POS, 5 NET_INCONCLUSIVE, 0 NET_NEG — rule-correct (≥1 net exp_lo>0 ∧ med_lo>0) but the pooled count **masks heterogeneity (audit-confirmed):** all 21 NET_POS are S2-DEFERRED low-n 4h `SUB-AVWAP` cells (n=44–78, separability never adjudicated); the **only S2-PASS well-powered stratum (AUDUSD-1h, n=988) is NET_INCONCLUSIVE in all 4 cells** (passes expectancy exp_lo +0.057…+0.081, fails median med_lo −0.020…−0.047). Cost did **not** kill the gross edge (contrast EXP-030/045) — 4h gross magnitudes (1–2 ATR mean) dwarf cost (~0.15–0.35 ATR) — but the edge lives entirely in shape-unadjudicated low-n cells. **Read-gate input to G-018; authorizes nothing** (does not close/open the family). Item RETAINED. TRAIN-only disclosure; holdout sealed; ledger unchanged (all 48 strata 0/2). 0 candidate slots, 0 counted TEST reads. |
| **EXP-084** | HYP-004b | **Counted-read `WF-EXPANDING` confirmation** (reserved-conditional; D0-amendment-001; **re-gated by D0-amendment-002**): run the single frozen WF confirmation on **exactly** the EXP-083 hash-pinned valid-candidate set, adjudicated by the **frozen referee suite (binding)** under the D4 G-018 conjunction, Holm over the frozen `{valid-candidate × stratum}` grid. **Spends counted TEST read #1.** | per surviving variant / **1 counted read per member stratum carrying a valid candidate** (≤ 2 lifetime cap) — **actual: 0 counted (portfolio-aggregate disclosure)** | **COMPLETE 2026-06-22 — `NOT_CONFIRM` (portfolio unit; audit PASS 0C/0W/3I). HYP-004 CLOSES at G-018. 0 candidate slots; no new countable item; outcome RETAINED.** The single sanctioned OOS read (D0-amendment-003 portfolio reframing): one frozen `WF-EXPANDING` read of a hash-pinned basket (NZDUSD-4h + USDCAD-4h + USTEC-4h `SUB-AVWAP`, pinned exit `AVWAP-FH`, NET on the EXP-085 cost model), under the frozen referee suite (`xen.wf` aggregate + FPR margin) + D4 G-018 conjunction. **Result `NOT_CONFIRM`** (n_pool=303, n_train_sep=152, n_oos=151): the basket **separates on TRAIN** — S1 attribution s1_excess_lo=1.109>m; **S2 finally adjudicated at pooled n=152 (the key gain) and PASSES** (tailmass 0.0263 ≤ 0.06; validates the `AVWAP-FH` genuine-continuous-tail pin) — **but all three economic OOS legs FAIL** (expectancy exp_lo −1.045<m −0.0396; median med_lo −0.821<0; beats-random beats_lo −0.656<0). **Mechanism:** the apparent edge is **selection-region overlap and reverses OOS** — per-fold net positive in the non-fresh [50–70%] selection-overlap folds (+1.866/+0.068), negative in all three fresh [70–100%] held-back folds (−1.002/−1.250/−0.754); Risk-1 realized. Not masking a positive stratum (all 3 net-negative); exit-invariant (no arm clears zero at CI_low); well-powered → NOT_CONFIRM, not INCONCLUSIVE. The data-derived-beats-conventional thesis is unsupported on TRAIN and now additionally **unconfirmed OOS as a portfolio**. **Ledger:** portfolio-aggregate rule → **DISCLOSURE against the 3 member strata, 0 counted reads** (caps preserved, all 48 strata stay **0/2 open**; the 3 strata become *disclosed* — basket claim only, future clean per-instrument read weakened per the EXP-032 precedent). Global holdout never touched and **NOT** released. Read-gate sequence completed: EXP-083 (screen) → EXP-085 (TRAIN cost gate, NET_SURVIVES) → G-018 (operator ratified portfolio read) → **EXP-084 (NOT_CONFIRM, HYP-004 closed)**. EXP-084 ID reserved, never reused. |

## Phase 019 Batch (Family-Selection Availability Screen) — family-agnostic, OPEN-PENDING-G0

**Registered:** 2026-06-22. **This is NOT a candidate family** — it is a family-agnostic *selection* phase
(analogous to Phase 017 being a methodology phase): TRAIN-only availability screens over untested entry-side
*information axes*, whose deliverable is a **ranked admit/exonerate inventory** selecting the next family to
open. **0 candidate slots, 0 counted TEST reads, holdout never touched** (TRAIN sub-split only; the screens
are availability disclosures, not stratum-specific inferences — EXP-080/081 precedent; `test-read-ledger.md`
unchanged, all 48 strata stay 0/2 open).
**Opened by:** operator selection of the next direction (2026-06-22), after CF-CAPGEO-001 RETIRED at G-018.
**Status:** **CLOSED — G-019 ADJUDICATED 2026-06-23: ALL SCREENED AXES NOT ADMITTED → TERMINAL BRANCH.**
Cross-axis Holm step-down over the realized axis-level permutation p-values admitted **no axis**: **M**
(`CF-VOLEXP-001`) Holm-adj p = 2·0.0326 = **0.0652 > 0.05** — EXP-086's single-axis provisional ADMIT
(`S_M=3>S*=2`) does **not** survive cross-axis multiplicity → single-series-magnitude cell CLOSED; **X**
(`CF-XSECT-001`) `S_X=1≤S*=1`, p=0.323 → dead-by-absence, cell CLOSED; **F** (`CF-FLOW-001`) **not opened**.
**Both families CLOSED and retained** (file-drawer, never deleted/reused). Routing → **terminal branch (a
priori): price-derived information — single-series magnitude AND cross-sectional relational — exhausted on this
dataset; frontier = non-price data acquisition (operator decision), reached at 0 reads / 0 slots.** Holdout
untouched; `test-read-ledger.md` unchanged (all 48 strata stay 0/2 open). See
[`G-019-gate-review.md`](../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/G-019-gate-review.md).
**Prior — OPEN — G0 PASS (2026-06-22).** Phase 019 D0 ratified and frozen; the **D2 admission-gate
bite-check is GREEN** (`bite-check/`, SEED 20260622, report sha256 `208dfb3f…`, byte-identical second pass):
the multiplicity-adjusted permuted-axis gate is not-vacuous (pure-noise axis admitted 0.0248 ≤ FWER 0.05,
Wilson-hi 0.0295), not-impossible (planted +0.20-ATR/8-cell axis admitted power 1.0), band-invariant
{0.025,0.05,0.10}, and self-calibrating under inflated per-cell FP. **EXP-086 (Screen M) COMPLETE 2026-06-22 — `SCREEN_DELIVERED` + provisional `ADMITTED` (NON-BINDING; audit PASS):** axis M provisionally admitted into the slate (`S_M=3 > S*=2`, perm_p=0.0326, driver NR7/tail; typical-range dead; tail-only ⇒ long-vol; borderline, fails FWER 0.025); binding admit/exonerate at G-019. **EXP-087 (Screen X) COMPLETE 2026-06-22 — `SCREEN_DELIVERED` + provisional `NOT_ADMITTED` (NON-BINDING; audit PASS):** axis X cross-sectional relative strength earns no admission (`S_X=1 ≤ S*=1`, perm_p=0.323, ranking z=1.26; both primitives S=1; homogeneous/not-masking; degrades at fast domains; 2/92 beats are small-cell artefacts; mechanism late-entry-after-the-move ⇒ no continuation); **`S=1` below the D2a band ⇒ dead-by-absence, not exonerated**; binding admit/exonerate at G-019 (Holm can only raise perm_p). **Next: ± EXP-088 (Screen F, reserved-conditional) → G-019 ranked inventory.**
**Governing design:** [`../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/design.md`](../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/design.md)
+ [`D0-predeclarations.md`] + gate [`G-019-gate-criteria.md`].
**Candidate families under consideration (DRAFT — PENDING-SELECTION; full discussion):**
[`candidate-families/family-selection-phase-019.md`](candidate-families/family-selection-phase-019.md).

**Invariant motivating the phase (re-derived from primary evidence — autopsy/reconciliation):**
single-instrument, event-driven, price-geometry entries on a directional target carry **no
signal-conditional favourable availability beyond a matched random control** (EXP-047 AVWAP MFE≈control;
EXP-081 harami `MFE_med` Δ −0.140, 17/46; AVWAP +0.061, 28/46), and the whole downstream stack is exonerated
(EXP-084 exit-invariant). The dead cell of the availability 2×2 is **single-series × directional**; Phase 019
screens the three untested cells.

### Predeclared surface (countable items — entered now per the file-drawer rule)

| Field | Predeclared value |
| --- | --- |
| Phase type | Family-agnostic **selection** phase (no CF opened; no slot consumed) |
| Information axes screened (countable) | **M** single-series magnitude (`CF-VOLEXP-001`, EXP-086), **X** cross-sectional relative strength (`CF-XSECT-001`, EXP-087), **F** order-flow / liquidity imbalance (`CF-FLOW-001`, EXP-088, reserved-conditional) |
| Dataset / domains / instruments | VAL-005 5-year, {15m,1h,4h}, 16 instruments (DE30 dropped); TRAIN sub-split `[0, int(analysis_rows·0.7))` only |
| Matched-random control | EXP-080/081 `SUB-RANDOM` (per-cell descriptive null) |
| Binding admission gate | **multiplicity-adjusted permuted-axis null** at the realized cell count + cross-axis Holm (FWER 0.05); **bite-checked before G0** (not vacuous / not impossible) — D2b. The single-axis ≈17/46–28/46 band is descriptive only. |
| Screen-M endpoint | **SPLIT** typical-range AND tail/bimodality (never pooled) + two-sided-cost magnitude-budget; a tail-only admission is **long-vol**, not directional |
| Verdict | per-axis **ADMITTED / EXONERATED / INCONCLUSIVE**, ranked best-first by the frozen Δ-over-random metric (D5); every ADMITTED axis is eventually opened (ranking orders, never prunes) |
| Candidate slots | **0** — a family promotes to a slot only at its own future G0/D0 on ADMIT |
| TEST reads | **0** — TRAIN-only availability disclosures; ledger unchanged |
| Terminal branch | all-EXONERATED ⇒ price-derived information exhausted ⇒ frontier = non-price data acquisition (operator decision), reached at 0 reads / 0 slots |

No candidate slot is consumed by registration. Each screened axis is a countable item; its outcome
(admit / exonerate / inconclusive) is **retained** here and in `candidate-families/family-selection-phase-019.md`,
never deleted or reused. A promoted family registers its own CF-XXX spec + EXP-IDs at its future G0/D0.

### Phase 019 experiment outcomes

| EXP | Axis / HYP | Role | Slots / TEST | Status |
| --- | --- | --- | --- | --- |
| **EXP-086** | M — `CF-VOLEXP-001/HYP-001` | **Screen M** (TRAIN-only): single-series magnitude availability — SPLIT typical-range + tail/bimodality vs matched random, on compression primitives (HA-harami inside-bar + NR/inside-bar), incl. the two-sided magnitude-budget; admit/exonerate vs the D2b multiplicity-adjusted gate. | 0 / 0 | **`SCREEN_DELIVERED` — provisional `ADMITTED` (NON-BINDING) 2026-06-22 (audit PASS 0C/2W/4I; integrity clean — determinism/recon/holdout).** `S_M=3 > S*=2` (FWER 0.05), axis perm_p=0.0326, ranking z=2.62, driver **COND-NR7/tail** (sub-screen S = {HARAMI-typ 0, HARAMI-tail 0, NR7-typ 0, NR7-tail 3}). **Typical/normal range DEAD** (NR7 conditioned median range *below* random, Δ̂ med ≈ −0.28 ATR); live thread = NR7 **rare-tail mass** (compression→expansion, tail-only not location). 3 beats-random cells **all 15m** (NZDUSD/USTEC/US2000) but **conservative/anti-masking** (tailmass Δ>0 in 15/16·15m, 10/16·1h, 7/14·4h — broadly present, only 15m-powered). **Borderline** (admits FWER 0.05/0.10, fails 0.025; MC-stable 1000-vs-5000). **Tail-only ⇒ LONG-VOL (harvest-model guard), never directional; tiny effect (~0.5–1.1 extra catastrophe events/100).** Magnitude-budget net_atr necessary-not-sufficient (NOT an edge; US2000-15m cost-unavailable). **Binding admit/exonerate deferred to G-019** (cross-axis Holm can only raise perm_p; little headroom under 0.05). Retained, never deleted. 0 slots / 0 counted reads; holdout untouched; all 48 strata stay 0/2 open. |
| **EXP-087** | X — `CF-XSECT-001/HYP-001` (countable primitives: `COND-XSRANK` + `COND-XSDIV`) | **Screen X** (TRAIN-only): cross-sectional relative-strength favourable availability (basket-relative momentum/divergence rank over 16 instruments) vs matched random; admit/exonerate vs the D2b gate. | 0 / 0 | **`SCREEN_DELIVERED` — provisional `NOT_ADMITTED` (NON-BINDING) 2026-06-22 (audit PASS 0C/0W/2I; integrity clean — determinism/recon/causal-fill/holdout).** Both countable primitives evaluated: `S_X=1 ≤ S*=1` (FWER 0.05), axis perm_p=0.323, ranking z=1.26, driver `COND-XSRANK/favourable`; sub-screens S=1 each (COND-XSRANK perm_p=0.113, COND-XSDIV perm_p=0.236), n_powered 46 each. Only 2/92 cell-reads beat random (GBPUSD-4h XSRANK, NZDUSD-4h XSDIV — smallest 4h cells, ci_low barely >0; small-cell multiplicity artefacts the joint permuted-axis null absorbs at S*=1). Per-domain mean Δ̂ 15m −0.26 / 1h −0.15 / 4h ≈0 — cross-sectional conditioning does **not** improve and *degrades* favourable availability at fast domains; **homogeneous, not masking**. Mechanism: decile fires *after* the trailing-20-bar relative move (late entry) ⇒ no favourable continuation beyond a direction-matched random clock (short-horizon mean-reversion/exhaustion of intraday cross-sectional momentum). Routing invariant across N_PERM {1000,5000} and FWER {0.025,0.05,0.10}. **`NOT_ADMITTED` ≠ `EXONERATE`: `S=1` BELOW the D2a band [17,28] ⇒ dead-by-absence (underperforms coin-flip), not exonerated-by-coin-flip.** **Binding admit/exonerate deferred to G-019** (cross-axis Holm can only raise perm_p=0.323 → no admission reachable). Both primitives **retained, never deleted**. 0 slots / 0 counted reads; holdout untouched; all 48 strata stay 0/2 open. |
| **EXP-088** | F — `CF-FLOW-001/HYP-001` | **Screen F** (TRAIN-only, reserved-conditional): order-flow / liquidity-imbalance availability vs matched random; admit/exonerate vs the D2b gate. | 0 / 0 | **NOT OPENED at G-019** — reserved-conditional; operator did not request a third comparison. The one price-adjacent cell left unmeasured; available as a future cheap screen, not required for the terminal verdict. Retained. |
| **G-019** | — | Terminal gate: emit the ranked admit/exonerate/inconclusive inventory; route per the D5 mechanical rule. | 0 / 0 | **ADJUDICATED 2026-06-23 — ALL SCREENED AXES NOT ADMITTED → TERMINAL BRANCH** (`G-019-gate-review.md`). Cross-axis Holm over the realized axis-level perm p-values: **M** Holm-adj p=2·0.0326=**0.0652>0.05** (single-axis `S_M=3>S*=2` does NOT survive cross-axis multiplicity → CF-VOLEXP-001 single-series-magnitude cell **CLOSED**: typical-range dead + NR7-tail thread tiny/long-vol/fails-FWER); **X** `S_X=1≤S*=1`, p=0.323 → CF-XSECT-001 cross-sectional cell **CLOSED, dead-by-absence** (below coin-flip band). ADMITTED set **empty** ⇒ no family promoted, 0 slots / 0 reads. **Price-derived information — single-series magnitude AND cross-sectional relational — exhausted on this dataset; frontier = non-price data acquisition (operator decision).** Both families retained (file-drawer), never reopened by re-parameterization. Bite-check GREEN precondition met; both EXP audits PASS; determinism byte-identical; ledger unchanged (all 48 strata 0/2). |

## Phase 020 Batch (CF-MR-001 Mean-Reversion Entry Availability Screen) — G-020 ADMITTED (BINDING); first candidate slot consumed

> **EXP-089 COMPLETE 2026-06-23 (amended `D0-amendment-001`) — `SCREEN_DELIVERED`; G-020 ADMITTED (BINDING)
> 2026-06-23.** Joint-max gate `S_fam=28 > S*=7`, axis perm-p≈0.0002, FWER-robust, MC-stable → **ADMITTED**
> (D5 rule; no cross-axis Holm — single family). Per sub-screen S: **CORE 28** (the lever), CORE-VOL-LOW 22 /
> -MED 25 / -HIGH 20 (**pass but INERT** — flat Δ̂_rand 0.05–0.08 ATR, add nothing over CORE), CORE+TREND 0 /
> CORE+FILTER 1 (**dead** — variants contradict the fade). Driver = bare RSI-2 fade (z=17.3); intraday
> (15m 16/16, 1h 11/16, 4h 1/14); ~3-bar horizon. **G-020 consequence: CF-MR-001 consumes its first candidate
> slot** (the lever = bare RSI-2 fade, opened intraday-first at a future G0/D0 — capture-geometry / exit / cost,
> the availability→tradability step). **Amendment (`D0-amendment-001`): the leg-2 beats-CORE conjunction +
> regime-membership-shuffle null are RETIRED** (audit C-1 ATR-normalization confound; C-2 trend-length horizon)
> — the regime-conjunction is **no longer a countable item**; all 6 sub-screens are single-test leg-1 over a
> causal MR-tempo cap with regime-matched controls. The first run was a deviation (voided/deleted). **All items
> retained; 0 counted TEST reads, holdout sealed, all 48 strata stay 0/2 open.** Admission consumed a
> **candidate slot, not a TEST read**. Adjudication: `G-020-gate-review.md`.

**Registered:** 2026-06-23. **First candidate family opened after the Phase 019 terminal branch, by explicit
operator override of the G-019 price→non-price routing** (`candidate-families/cf-mr-001.md` §0; Phase 020
design §1). The phase's sole experiment (EXP-089) is a **TRAIN-only availability screen** of a **new entry-side
family** — RSI-2 **mean reversion** (a fade mechanism; every prior family was continuation/pullback) with a
**global, strategy-agnostic ATR volatility-regime partition** treated as part of the signal definition (cell =
`asset+domain+regime`). **0 candidate slots, 0 counted TEST reads, holdout never touched** (TRAIN sub-split
only; availability disclosure, not a stratum-specific inference — EXP-080/081/086/087 precedent;
`test-read-ledger.md` unchanged, all 48 strata stay 0/2 open).
**Honest prior (binding on interpretation):** the programme-level null is availability ≈ random (three closed
families + Phase 019) — the hypothesis the screen tries to reject, not a prediction of failure. Both legs
carry the override on their own merits: leg 1 a new entry mechanism (fade), leg 2 a new *kind* of filter —
strategy-agnostic, intrinsic to the market, made a cell-differentiating part of the signal definition rather
than a bolt-on plugin. The screen is a fully-committed falsification attempt at 0 reads / 0 slots; the
analysis imports no prior family's outcome as a biasing expectation.
**Status:** **OPEN — G0 RATIFIED (2026-06-23, operator-authorized).** D0 FROZEN (`D0-predeclarations.md`); the
**D2b admission-gate bite-check is GREEN on the single-test legs** at the family's **6-sub-screen** structure
and C=46 (`bite-check/bite_check.py` → `bite_check_report.json`, sha256
`f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65`, byte-identical second pass). **Leg-2
design correction (2026-06-23, operator-directed, applied in place):** the three `/VOLREGIME` sub-screens now
test a **binding beats-random ∧ beats-CORE conjunction** (`Δ̂_core > 0`, the additive edge over the pooled
core) under a **regime-membership-shuffle-within-CORE** null — a new per-cell statistic + null requiring the
**bite-check to be extended and re-confirmed GREEN (new sha) before EXP-089 runs**. EXP-089 authorized on that
extended GREEN.
**Governing design:** [`../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md`](../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md)
+ [`D0-predeclarations.md`] + gate [`G-020-gate-criteria.md`].
**Family spec (FROZEN, G0-RATIFIED):**
[`candidate-families/cf-mr-001.md`](candidate-families/cf-mr-001.md).

### Predeclared surface (countable items — entered now per the file-drawer rule)

| Field | Predeclared value |
| --- | --- |
| Candidate family (countable) | **`CF-MR-001`** — RSI-2 mean-reversion entry + global `/VOLREGIME` partition. Consumes a candidate slot only on ADMIT at a future G0/D0; the availability screen consumes 0. |
| Entry (frozen) | `RSI(2)` Wilder on domain Close; long `RSI₂<10`, short `RSI₂>90` (period 2, extremes 10/90) |
| Global filter `/VOLREGIME` (frozen) | `ATR(14)` causal trailing rolling-50 percentile, cuts 33/66 → Low/Med/High; per-(instrument,domain); **partition on the bare core only**, tested by the **binding leg-2 beats-CORE conjunction** (the regime must *add* favourable availability over the pooled core) |
| Variant toggles (frozen; pooled in batch 1) | TREND `EMA(20)`; RSI-FILTER `RSI(5)≷50` |
| Batch-1 sub-screens (countable; joint-max controlled) | `CORE`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND`, `CORE+FILTER` |
| Dataset / domains / instruments | VAL-005 5-year, {15m,1h,4h}, 16 instruments; TRAIN sub-split `[0, int(analysis_rows·0.7))` only; member cells = EXP-080-READY 46 (US500-4h, JP225-4h `COVERAGE_EXCLUDED`) |
| Matched-random control | EXP-080/081 `SUB-RANDOM`, matched on **count + direction** — the same all-bars control for every sub-screen (no regime-matching: ATR-normalisation removes the regime scale; the regime's additive value is isolated by `Δ̂_core`) |
| Binding admission gate | `xen.availability_gate` 6-sub-screen **joint-max** permuted-axis null at the realized cell count; per-sub-screen `S` = `#beats-random` (CORE/variants, leg 1) / `#(beats-random ∧ beats-CORE)` (`/VOLREGIME`, leg 2 binding); null = signal-shuffle / regime-membership-shuffle-within-CORE; `ADMITTED iff S_fam > S* (Q95) ∧ axis perm_p ≤ 0.05` (FWER 0.05); no cross-axis Holm (single family); **bite-checked GREEN, extended for leg-2, before the run** (D2b) |
| Endpoint | favourable `MFE_med`, ATR-normalised, directional — leg 1 `Δ̂_rand` vs `SUB-RANDOM` (all sub-screens); leg 2 `Δ̂_core` vs pooled CORE (`/VOLREGIME` binding, variants descriptive) (D3) |
| Verdict | **ADMITTED** (argmax sub-screen names the lever) / **EXONERATED** (single-series-directional dead under mean-reversion too → G-019 non-price frontier) / **INCONCLUSIVE** (D5) |
| Candidate slots | **1 (CONSUMED at G-020 ADMIT, 2026-06-23)** — the screen itself consumed 0; the binding G-020 admission promoted CF-MR-001 to its first candidate slot (lever = bare RSI-2 fade) |
| TEST reads | **0** — TRAIN-only availability disclosure; ledger unchanged |
| **Deferred branches (registered, uncounted)** | **CONTRARIAN** toggle (flip direction on the RSI-filter axis); **25/75** regime scheme; **regime × variant** cross-cuts; RSI/EMA/ATR/window **parameter tuning**; instrument/domain/variant **expansion**. Each requires a dated `D0-amendment-*` stating whether it consumes a new slot. |

No candidate slot is consumed by registration. `CF-MR-001` and each batch-1 sub-screen is a countable item;
its outcome (admit / exonerate / inconclusive) is **retained** here and in `candidate-families/cf-mr-001.md`,
never deleted or reused. A refuted family is closed and not silently reopened by re-parameterization.

### Phase 020 experiment outcomes

| EXP | HYP | Role | Slots / TEST | Status |
| --- | --- | --- | --- | --- |
| **EXP-089** | `CF-MR-001/HYP-001` | **Availability screen** (TRAIN-only, AMENDED `D0-amendment-001`): RSI-2 mean-reversion favourable-excursion availability — 6 sub-screens (`CORE`, `CORE-VOL-{LOW,MED,HIGH}`, `CORE+TREND`, `CORE+FILTER`) over 46 member cells × {15m,1h,4h}; **all single-test leg-1 beats-`SUB-RANDOM`** (regime-matched for `/VOLREGIME`; **leg-2 conjunction RETIRED**) over a **causal MR-tempo cap**; admit/exonerate vs the D2b joint-max permuted-axis gate. | 0 / 0 | **COMPLETE 2026-06-23 — `SCREEN_DELIVERED`, provisional ADMITTED (NON-BINDING at screen time → made BINDING ADMITTED at G-020 2026-06-23); audit PASS (0C/0W/3I).** `S_fam=28 > S*=7`, perm-p≈0.0002, FWER-robust, MC-stable. **CORE 28 (lever)**; VOL-LOW/MED/HIGH 22/25/20 **inert** (add nothing over CORE); TREND/FILTER 0/1 **dead**. Bare RSI-2 fade, intraday (15m 16/16, 1h 11/16, 4h 1/14), ~3-bar horizon. First run was a deviation (audit C-1/C-2), voided/deleted, amended in place — confounds confirmed removed. Determinism/recon/holdout-fence clean; bite GREEN `f01a000b…`. **0 slots, 0 counted TEST reads, ledger unchanged.** Items retained. |
| **G-020** | — | Terminal gate: admit (lever named) / exonerate (→ non-price frontier) / inconclusive, per D5. | 1 slot / 0 TEST | **ADMITTED — adjudicated 2026-06-23** (`G-020-gate-review.md`). `S_fam=28 > S*=7`, axis perm-p≈0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm). Lever = **bare RSI-2 fade (CORE)**, intraday; vol-regime inert, variants dead. **CF-MR-001 consumes its first candidate slot**; next scope opens the bare fade (capture-geometry / exit / cost) at a future G0/D0. Admission = a candidate slot, **not** a counted TEST read — ledger unchanged (48 strata 0/2), holdout sealed. |

## Phase 021 Batch (CF-MR-001 batch 2 — RSI-2 Fade Capture-Geometry & Tradability) — CLOSED, REFUTED 2026-06-26

> ### ⚠ SUPERSEDED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead. G-021 TRADABLE RETRACTED.
> The entire EXIT-RCT tradability result (EXP-091/092/094 screen+sequence, **EXP-093 `TEST_CONFIRMED`**) is
> invalidated by a one-bar look-ahead in the EXIT-RCT favourable limit: `arm_levels`
> (`EXP-090/code/run_experiment.py:305-310`) rests `rct_target[di]` — computed from bar `di`'s **own** close
> (`mean_reversion.py:174`) — as the intrabar limit *during* bar `di`; the live-actable limit is `rct_target[di-1]`.
> The off-by-one inflates captured edge by ~+0.25 ATR/trade; causalized (`rct[di-1]`) the bare fade is net-negative
> even gross. Exposed by the cTrader port + forward test (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`). **The
> 11 EXP-093 counted TEST reads stay SPENT, now recorded spent-on-defect** (a discovered defect does not refund a
> read; see `test-read-ledger.md`). **G-021 TRADABLE is RETRACTED.** EXP-089/G-020 availability is NOT affected
> (gross MFE_med, no RCT limit). All rows below are **retained** per the file-drawer rule; family **not reopenable
> by re-parameterization**. Full mechanism + scope: `candidate-families/cf-mr-001.md` §CLOSURE.

> **G0 RATIFIED 2026-06-23 (operator-authorized).** Batch 2 of CF-MR-001 — the **availability→tradability**
> step for the **bare RSI-2 fade (CORE)** admitted at G-020. **D0 FROZEN** (`D0-predeclarations.md`); no new
> selection statistic ⇒ **no bite-check required** (the binding gate is the existing frozen referee suite; if
> EXP-091/092 introduce a novel selection statistic it must be bite-checked GREEN first). The **first candidate
> slot was already consumed at G-020**; Phase 021 consumes **no additional slot**. TRAIN-only through EXP-092
> (0 counted reads); the one-shot **EXP-093 TEST** spends ≤1 counted read per carried (instrument,domain) cell
> on the **analysis-TEST stratum** (cap 2/stratum; all 48 strata currently 0/2 → carried strata go 0→1),
> recorded in `test-read-ledger.md` in the same change. **The final-30% global holdout is never loaded** (a
> holdout release is a separate later gate). Items retained per the file-drawer rule.

**Registered:** 2026-06-23. **Scope:** exit / capture geometry / cost for the bare RSI-2 fade, **intraday
{15m, 1h}**; **4h OPENED 2026-06-24 (`D0-amendment-004`, 0 new slots) — gated behind the EXP-094 falsification
re-screen** (originally excluded as dead-by-absence at EXP-089, 1/14). The entry is **inherited frozen**
(`RSI(2)` 2/10/90; no re-tuning); the only open axis is the **exit + cost layer**.

> **AMENDED — `D0-amendment-004` (2026-06-24, FROZEN/operator-ratified).** Triggered by an operator hunch
> (archived `TEMP-091`, unaudited: EXIT-RCT net-clears 12/12 instruments on 4h, mean-and-median positive). The
> **4h domain is OPENED as a domain expansion of the admitted CORE-fade + EXIT-RCT lever (0 new candidate
> slots)** but **not admitted**: no 4h cell reaches EXP-092/093 until **EXP-094** (TRAIN-only, 0 reads) clears a
> binding **falsification re-screen** = 4h readiness (EXP-090 analog) + frozen net exit screen (EXP-091 analog)
> + a **matched-random/shuffled-entry RCT null** reconciling the EXP-089 4h dead-by-absence. Real-fade entry
> must beat random entry on net per-event expectancy in a **≥5-cell/≥3-instrument quorum**; else the 4h
> net-clear is exit-geometry/oscillation harvesting (not the fade) and **4h stays closed, retained**. The §4(c)
> paired-Δ shuffled-entry null is a new falsification statistic ⇒ **bite-checked GREEN at EXP-094 D0** before it
> runs. All other deferred levers remain deferred. See `D0-amendment-004.md`.
**Governing design:** [`../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md`](../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md)
+ [`D0-predeclarations.md`] + gate [`G-021-gate-criteria.md`].
**Family spec:** [`candidate-families/cf-mr-001.md`](candidate-families/cf-mr-001.md).

### Predeclared surface (countable items — entered now per the file-drawer rule)

| Field | Predeclared value |
| --- | --- |
| Candidate slots | **0 additional** — the first CF-MR-001 slot was consumed at G-020; Phase 021 spends no new slot |
| Entry (inherited frozen) | `RSI(2)` Wilder, long `RSI₂<10` / short `RSI₂>90` (2/10/90); no re-tuning |
| Domains / member cells | {15m, 1h}: 16 instruments × 2 = **32 cells**; **+ 4h ADMITTED (`D0-amendment-004`+`005`, EXP-094)** — 6 powered 4h members (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h; 7 COVERAGE_EXCLUDED, retained), carried to EXP-092/093 (0 new slots) |
| **Exit families (countable — the capture-geometry slate)** | **Native pair (primary):** **EXIT-RCT** (RSI₂→50 reversion-completion price `P*=Close+(AL−AG)`, proactive limit, 1m intrabar fill) · **EXIT-ERT** (return-to-`EMA(10)` equilibrium target, 1m intrabar fill). **Conventional contrast:** RSI-revert-on-close · fixed-bar · ATR triple-barrier (`1.0×ATR` tgt / `2.0×ATR` stop) · favourable partial/trail (EXP-059 V2A). **Single frozen parameter point each — no grid.** |
| Adverse side (frozen, all arms) | stop `2.0×ATR(14)` + the EXP-089 causal MR-tempo cap (mult 1.0, FLOOR 3, MAX 40); exit-on-close at cap |
| Intrabar fill (new module) | `xen.intrabar_fill` — timestamp-aligned domain→1m, causal order-of-touch (conservative adverse-first tie-break), real touched fill prices; TRAIN-clip by timestamp |
| Cost model (binding) | EXP-085 CONSERVATIVE round-trip (2×BASE) + per-instrument financing (`xen.capgeo_cost`/`xen.financing`), unchanged |
| Binding gate | the **frozen referee suite** (strict + ratified-loose + revised incremental); `ASS` **non-binding** (G-017) |
| Endpoint | net per-event expectancy (mean + median), ATR units, real prices, after cost; binding figure = net `ci_low_1s` |
| EXP-091 rule | net-clear iff net `ci_low_1s`>0; exit passes iff ≥5 cells / ≥3 instruments; **empty screen ⇒ G-021 NOT_TRADABLE at 0 reads** |
| EXP-092 rule | per-cell `SEQUENCE_PASS` at α=0.05 one-sided → hash-pinned candidate set (sha256) + phase Holm rule |
| EXP-093 rule (TEST) | carried cell CONFIRMS iff Holm-adj p≤0.05 ∧ `ci_low_1s` > margin (margin = EXP-090 MDE) |
| Verdict | **TRADABLE** (≥1 carried cell confirms on TEST) / **NOT_TRADABLE** (empty screen, or all carried cells fail) / **INCONCLUSIVE** (TEST power-limited) (G-021) |
| TEST reads | **0 through EXP-092**; EXP-093 ≤1/carried-stratum (cap 2/stratum; carried strata 0→1); analysis-TEST only, holdout sealed |
| **Deferred branches (registered, uncounted)** | the inert **vol-regime partition**, the dead **TREND/FILTER** variants, the **CONTRARIAN** arm, the **25/75** scheme, **regime×variant** cross-cuts, parameter **tuning**, instrument **expansion**. Each requires a dated `D0-amendment-*` stating whether it consumes a new slot. **The 4h domain is no longer deferred — OPENED → ADMITTED 2026-06-24 (`D0-amendment-004`+`005`, EXP-094 `ADMIT_4H`, 0 new slots); 6 powered cells carried to EXP-092.** |

Each exit family is a countable item; its outcome (clears / dies / inconclusive) is **retained** here and in
`candidate-families/cf-mr-001.md`, never deleted or reused. A refuted exit is not silently reopened by
re-parameterization.

### Phase 021 experiment outcomes

| EXP | HYP | Role | Slots / TEST | Status |
| --- | --- | --- | --- | --- |
| **EXP-090** | `CF-MR-001/HYP-002` | Exit-substrate readiness & per-cell inference calibration (TRAIN) — member set, event coverage, finite per-cell MDE under the frozen referee | 0 / 0 | **COMPLETE 2026-06-24 — `READINESS_CALIBRATION_DELIVERED`; AMENDED `D0-amendment-002`; audit PASS.** **20 MEMBER / 12 COVERAGE_EXCLUDED** (10×15m + 10×1h members carry to EXP-091 with margins RCT 0.0125 / ERT 0.025 ATR). All 12 excluded for the same power reason — *no finite MDE on either native arm* (every cell IN_FLOOR; fill-validity/timestamp/determinism TRUE ∀ cell×arm; resolution 0.991–1.000; FPR symmetric+controlled, every member arm ≤0.050 under both nulls). Two HALT-class confounds found+fixed+rerun (`D0-amendment-002`): (1) 1m fill engine — window over-assignment across dropped/gap windows + limit gap-throughs (fills outside `[Low,High]`); (2) Null B block-rotated *path* matched entries to wrong-era prices, inflating ATR-returns 30–145× (mean 0) → reverted to block-permuted *returns* (EXP-044 form). Median leg dropped (D5 non-binding; mean bit-identical to `xen.ass`). Determinism byte-identical (EURUSD-15m, AUDJPY-1h); SHA-pinned. New module `xen.intrabar_fill`. **0 slots, 0 counted TEST reads** (TRAIN-only readiness/calibration disclosure; ledger unchanged, all 48 strata 0/2 open); holdout sealed. Member set vs the broken-NullB intermediate run: 9 robust / 11 newly-admitted / 3 boundary-noise dropouts (hard ≤0.05 gate, ±0.014 noise). No countable exit item screened here (EXP-091). |
| **EXP-091** | `CF-MR-001/HYP-002` | TRAIN-only exit/capture-geometry screen (gross + EXP-085 cost) over the §3 slate; native pair vs conventional contrast | 0 / 0 | **COMPLETE 2026-06-24 — `SCREEN_DELIVERED`, non-empty; audit PASS (0C/3W/3I).** Exit-family outcomes (file-drawer, retained — never reopened by re-parameterization): **EXIT-RCT CLEARS the screen quorum** (net-clears 5 cells / 5 instruments, all 1h: EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h) → carried to EXP-092. **EXIT-ERT, ATR triple-barrier, RSI-revert-on-close, fixed-bar, favourable partial/trail each net-clear 0 cells → DIE at the screen.** Pure ATR-normalized cost geometry: gross ≈ domain-invariant (~0.28 ATR; both natives gross-clear 20/20) but fixed-bps RT ÷ entry ATR(14) = ~0.6 ATR on 15m vs ~0.24–0.30 on 1h → 15m all net-negative; RCT 0/10 on 15m, 5/10 on 1h (*availability ≠ capturable edge* realized). Native A/B: RCT > RSI-revert-on-close 20/20 (Δ median +0.261 ATR, Wilcoxon p≈1.9e-6, descriptive); ERT fails. Caveats binding on EXP-092 (audit forensics): pass is 1h-only, boundary-fragile (GBPUSD-1h net_ci_low +0.0043), mean/tail-carried on 3/5 (only USTEC-1h & US2000-1h mean-and-median-positive = robust core). Faster-cost companion (RT/2): 14 clears → cost-dominated, not signal-absent. Cost table Phase-021-local (`D0-amendment-003`, hash `fa7c887…`); shared `xen.capgeo_cost.COST_CONSTANTS` not mutated (Phase-018 integrity). Determinism PASS; **0 slots, 0 counted TEST reads** (TRAIN-only disclosure; all 48 strata stay 0/2 open); holdout sealed. Screen non-empty ⇒ advances to EXP-092, NOT G-021 NOT_TRADABLE. |
| **TEMP-091** | (hunch — not a countable experiment) | **File-drawer disclosure** (`D0-amendment-004`): unaudited, non-governed operator side-test = EXP-091 frozen slate on **4h only**, 13 cost-table instruments, TRAIN-only, EXP-090 substrate reused verbatim (4h = 240-min). **Archived** to `python/experiments/_archive/temp-exp-091/` (not deleted). | 0 / 0 | **RECORDED 2026-06-24 (non-binding, unaudited).** EXIT-RCT net-clears **12/12 instruments on 4h** (JP225-4h failed to build), every clearing cell **mean *and* median positive** (net_median +0.08…+0.16) — more robust than the 1h EXP-091 pass; the other 5 arms net-clear 0 cells; **reactive RSI-revert-on-close net-negative on all 12**. Determinism replay PASS; holdout untouched. **Tension (verdict-material for admission):** EXP-089 found 4h dead-by-absence (1/14) — only the proactive small-limit RCT is positive while the reactive same-signal analog is negative ⇒ possible **exit-geometry/oscillation harvesting, not the fade**. Superseded by the governed **EXP-094** falsification re-screen (which adds the matched-random/shuffled-entry RCT null TEMP-091 lacked). Recorded regardless of outcome per file-drawer rule. |
| **EXP-094** | `CF-MR-001/HYP-002` | **4h readiness + falsification re-screen** (`D0-amendment-004`, null corrected by **`D0-amendment-005`**; TRAIN-only): (a) 4h member readiness + per-cell finite RCT MDE (EXP-090 analog); (b) frozen net exit screen on 4h (EXP-091 analog, amendment-003 cost); (c) **matched favourable-target-distance oscillation null** (binding) — real-fade EXIT-RCT must beat a favourable limit placed at a distance resampled from the real RCT target multiples, fired at random times, on net per-event expectancy (paired Δ lower bound > 0) in a **≥5-cell/≥3-instrument quorum** to admit 4h; the original SUB-RANDOM-entry RCT null (biased toward admission) retained as a non-binding companion; 1h positive control (disclosed). | 0 / 0 | **COMPLETE 2026-06-24 — `ADMIT_4H`; audit PASS (re-audit; 1 CRITICAL fixed-and-rerun, 1 Warning closed).** Readiness: **6 MEMBER / 7 COVERAGE_EXCLUDED** (6 "no finite RCT MDE": AUDUSD/GBPUSD/NZDUSD/US2000/USDJPY/USTEC-4h; JP225-4h build-fail) — **TEMP-091's naive "RCT 12/12 on 4h" over-claimed** (half those cells cannot bound a confirmation; retained in the file drawer). On the 6 powered cells (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h): leg (b) net-clears **6/6**; leg (c) real beats the binding matched-distance oscillation null **6/6** (`delta_lo` 0.19–0.27) **and** the realized-capture sensitivity null **6/6** → the 4h edge is the **entry signal, not oscillation harvesting** (mechanism: reversion-completion hit rate ~65% at random timing → ~99% at real extremes, identical exit/stop/fill/cost; null nets −0.09…−0.18, real +0.07…+0.16). 1h positive control 5/5. **Bite-check GREEN** (per-cell power leg corrected after a first-run RED — a miscalibration that planted the sub-threshold single-arm MDE; the binding statistic is FPR-controlled and powered). All 6 members **mean-AND-median net-positive** (robust core). Determinism PASS; holdout sealed; **0 candidate slots, 0 counted TEST reads** (TRAIN-only disclosure; all 48 strata incl. 4h stay 0/2 open). **4h domain OPENED → ADMITTED (domain expansion).** → EXP-092 carries the 6 powered 4h cells. |
| **EXP-092** | `CF-MR-001/HYP-002` | Per-instrument cost-bearing tradability sequence → hash-pinned candidate set + Holm rule | 0 / 0 | **COMPLETE 2026-06-24 — `SEQUENCE_DELIVERED`; audit PASS (0C/0W/4I).** EXIT-RCT (the sole EXP-091/094 survivor) sequenced on its 11 carried cells (5×1h EXP-091 + 6×4h EXP-094): **all 11 `SEQUENCE_PASS`** (net `ci_low_1s` +0.0044…+0.135 ATR > 0 at α=0.05, power-confirmed by the EXP-090/094 MDE) → **hash-pinned candidate set (sha256 `f6427e8342400d46…`) + sized phase Holm rule** for EXP-093. Re-derivation matches independent EXP-091/094 within ≤6.2e-4 (independent seeds; byte-identical resolved counts). **Disclosed two-tier split (masking check): robust core (8)** = all six 4h members (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h) + USTEC-1h + US2000-1h (margin-clearing AND mean-AND-median positive); **mean-carried 1h (2)** EURUSD-1h, NZDUSD-1h (median<0); **fragile (1) GBPUSD-1h** (net_ci_low 0.0044 < 0.0125 margin, median −0.052 → pinned but should NOT carry to TEST). 4h dominates the ranking (smaller ATR-normalized cost); gate-shape OK (binding mean + co-reported median, D5). No new countable item; no item refuted. Determinism PASS; holdout sealed; **0 slots, 0 counted TEST reads** (TRAIN-only disclosure; 11 carried strata stay 0/2). → EXP-093 carries the smallest-defensible robust core. |
| **EXP-093** | `CF-MR-001/HYP-002` | One-shot TEST confirmation under phase Holm + margin (carried set = all 11 SEQUENCE_PASS cells, Holm-11, operator-ratified `D0-amendment-006` — superseding the §8.3 smallest-defensible sizing) | **11 counted TEST reads** (one per carried stratum, each 0→1; 0 slots) | **COMPLETE 2026-06-24 — `TEST_CONFIRMED` → routes G-021 TRADABLE; audit PASS (0C/1W non-material/3I).** The binding tradability read on the **analysis-TEST stratum** of all 11 carried cells (frozen D6/4c: `CONFIRM iff Holm-adj p≤0.05 ∧ net ci_low_1s > margin`). **8/11 CONFIRM** at `Holm-adj p=0.0011`, across **7 instruments and both domains** — the **programme's first net-positive out-of-sample price entry.** Per-cell outcomes (all retained): **CONFIRM (8)** = the six 4h members (EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h, net_ci_low 0.039–0.094 vs 0.025 margin, **mean-AND-median positive**) + USTEC-1h (+0.046) & US2000-1h (+0.073) (**mean-carried**; USTEC TEST median −0.026); **EVIDENCE_AGAINST (2)** = GBPUSD-1h (net_mean −0.080, ci_low −0.103, n=1653; pre-disqualified `D0-amendment-006 §2`) & EURUSD-1h (−0.010, −0.032, n=1619), well-powered net-negative OOS reversal; **INCONCLUSIVE (1)** = NZDUSD-1h (+0.003, −0.015), near-zero. Mechanism: RCT target hit ~99%; 4h nets clear by cost geometry (smaller ATR-cost fraction), not stronger signal; uniform TRAIN→TEST shrinkage (Δ ci_low −0.005…−0.107) — robust core absorbed it, thin 1h tier reversed. No new countable item. Determinism PASS; numbers reproduced from raw data. **11 counted TEST reads recorded in `test-read-ledger.md` same change (each carried stratum 0→1; cap 2/stratum; other 37 strata 0/2); final-30% global holdout never loaded; 0 candidate slots.** G-021 routes TRADABLE (mechanical rule, ≥1 CONFIRM); formal adjudication `G-021-gate-review.md` pending at the checkpoint. |
| **G-021** | — | Terminal gate: tradable / not-tradable / inconclusive, per D6. | 0 slot / — | **ADJUDICATED TRADABLE 2026-06-24** (`G-021-gate-review.md`; mechanical D6/4c rule, 8/11 CONFIRM). Phase 021 CLOSED. Routes to **Phase 022** (portfolio + noise + global-holdout release) — separate checkpoint/D0; deferred levers each their own slot/D0. |

## Phase 022 Batch (CF-MR-001 batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release) — CLOSED, REFUTED 2026-06-26

> ### ⚠ SUPERSEDED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead. G-022 DEPLOYABLE_CONFIRMED RETRACTED.
> The deployment portfolio (EXP-095/096) and the global-holdout confirmation (**EXP-097 `DEPLOYABLE_CONFIRMED`**)
> inherit the EXP-093 EXIT-RCT exit look-ahead (`rct[di]` rested during bar `di`; see the Phase 021 banner above
> and `candidate-families/cf-mr-001.md` §CLOSURE). EXP-096's "survives v2 slippage" rests on the inflated
> look-ahead gross; live-causal the bare fade is net-negative even gross, so the high portfolio Sharpe is not a
> deployable edge. A secondary cBot-port defect (the XRSI-V1 REAL stream also omitted the v2 0.05·ATR entry
> slippage the research charges) compounds it. **The single sanctioned final-30% global-holdout shot (EXP-097)
> stays SPENT, now recorded spent-on-defect** (non-refundable; `test-read-ledger.md`). **G-022a freeze and G-022
> DEPLOYABLE_CONFIRMED are RETRACTED.** EXP-098 cross-broker/aggregation robustness replicated a look-ahead-biased
> portfolio and carries no deployment weight. All rows below are **retained**; family **CLOSED — not reopenable by
> re-parameterization**. Live-backtest observations may seed a **new family** only after the EXIT-RCT limit is
> causalized, under its own D0.

> **G0 RATIFIED 2026-06-24 (operator-authorized).** Batch 3 of CF-MR-001 — the **deployment-economics &
> OOS-final** step for the G-021-confirmed bare RSI-2 fade + EXIT-RCT. **D0 FROZEN**
> (`checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md`). **No new candidate slot** (the
> portfolio/risk model is a deployment wrapper on the admitted lever, not a new signal). EXP-095/096 are
> **0 counted TEST reads** (portfolio-aggregate disclosure reusing the EXP-093 already-resolved analysis-TEST
> series — the per-stratum reads were spent at EXP-093; the 11 carried strata stay **1/2**). **EXP-097 spends
> the single sanctioned final-30% global-holdout release** — outside the analysis-TEST ledger entirely, recorded
> as a holdout-governance event (à la EXP-032), and only after the **G-022a** pre-holdout freeze. A **new binding
> gate statistic** (the portfolio-level holdout confirmation rule) is introduced ⇒ **synthetic-null calibration
> + bite-check GREEN in EXP-095** before G-022a freezes it.

**Registered:** 2026-06-24. **Governing design:** `checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md`.
**Phase 021 close recorded:** G-021 TRADABLE (8/11 carried cells confirm OOS; bare RSI-2 fade + EXIT-RCT is the
programme's first net-positive price entry). **HYP:** `CF-MR-001/HYP-003` (deployment economics &
global-holdout-final).

### Predeclared surface (countable items — entered now per the file-drawer rule)

| Field | Predeclared value |
| --- | --- |
| Candidate family (countable) | **`CF-MR-001`** (no new family); **0 new candidate slots** — deployment wrapper on the admitted CORE-fade + EXIT-RCT lever |
| Deployable set (study) | the **8 G-021-confirmed cells**: EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h + USTEC-1h + US2000-1h. The 3 non-confirming 1h cells (EURUSD-1h/NZDUSD-1h/GBPUSD-1h) excluded, retained in file drawer. Holdout-frozen set = noise-survivors (decided at G-022a). |
| Risk model (frozen, parameter-free) | **ERC (equal risk contribution)** on a causal **trailing-90-day Ledoit-Wolf covariance**, **weekly** rebalance, **10% annualized vol** target (Sharpe-invariant scalar), **1.5×** concurrent risk-aware cap, + an online **circuit-breaker** (de-allocate a cell whose trailing-50-trade mean net < 0). **Portfolio A** (static ERC) vs **B** (ERC+circuit-breaker), run in parallel. Brackets disclosed (D0 ratified table), **never tuned**. |
| Noise model (frozen) | entry-fill ladder: **v1** next-1m-open (mild floor), **v2 next-1m-open + 0.05×ATR(14) adverse slippage (BINDING)**, **v3** worst-of-next-`k=3` 1m bars (stress ceiling). Only the entry execution price changes; exit/stop/cost frozen. |
| Binding holdout statistic (NEW ⇒ bite-check) | **portfolio** annualized-Sharpe / pooled-expectancy moving-block one-sided lower bound > the **G-022a-predeclared margin band**; synthetic-null FPR ≤ 0.05; bite-checked GREEN in EXP-095. Per-cell holdout outcomes disclosed (non-binding). |
| Dataset / domains / instruments | VAL-005 5-year, {1h, 4h}, the 8 deployable instruments×domains; TRAIN + EXP-093 analysis-TEST series (disclosure) for EXP-095/096; **final-30% global holdout for EXP-097 only**. |
| Candidate slots | **0 additional** (first consumed at G-020) |
| Counted TEST reads | **0 in EXP-095/096** (portfolio-aggregate disclosure; 11 carried strata stay 1/2). EXP-097 = the **global-holdout shot** (outside this ledger; recorded separately). |
| **Deferred branches (registered, uncounted)** | the inert **vol-regime partition**, the dead **TREND/FILTER** variants, the **CONTRARIAN** arm, the **25/75** scheme, **15m** capture, **regime×variant** cross-cuts, parameter **tuning**, instrument/domain **expansion**, **faster-cost** sensitivity. Each requires a dated `D0-amendment-*` stating whether it consumes a new slot. None enters Phase 022. |

No candidate slot is consumed by registration. The portfolio/risk-model hyperparameters and noise variants are
countable design choices entered here at their frozen values (file-drawer control); brackets are disclosed
sensitivity, never selection. Refuted/inconclusive items (Portfolio A/B, any broken-by-noise cell, any per-cell
holdout outcome) are **retained**, never deleted or reused.

### Phase 022 experiment outcomes

| EXP | Hypothesis | Role | Slots / reads | Status |
| --- | --- | --- | --- | --- |
| **EXP-095** | `CF-MR-001/HYP-003` | Portfolio construction & online-adaptive risk model (analysis set, noise-free): causal ERC **A** vs circuit-breaker **B** vs deployment-realistic single-cell baseline (annualized Sharpe/Calmar LB); **calibrate + MDE-check the portfolio holdout statistic**. | 0 / 0 | **COMPLETE 2026-06-25 (D0-amendment-001 amend-in-place rerun; re-audit PASS; 0 reads/0 slots, holdout untouched).** The rerun restored the D0 §D2.1 **intra-1h mark-to-market** (the prior flat-at-exit booking inflated Sharpe/MaxDD differentially across 1h/4h — a verdict-material defect), re-specified the benefit criterion (like-for-like LB + cross-cell-median baseline), made Calmar/CVaR/Ulcer co-binding, and replaced the fixed-Sharpe=1.0 bite with an **MDE-curve**. **Corrected dispositions:** **(1) Portfolio benefit SUPPORTED** — A Sharpe 11.69 (lo 10.24) / B 11.57 (lo 10.19); A/B Sharpe LB clears EVERY baseline (median-cell LB 4.99 +5.25; best-cell point 8.73; best-cell LB 7.53 +2.71; naive-IV LB 10.07) + co-binding Calmar LB (+53); mechanism = genuine moment-to-moment diversification of 8 low-correlation cells (mean |corr| 0.10) → portfolio MaxDD 0.034 below every constituent (the benefit flat-at-exit lumping hid). **(2) ERC ≈ naive-IV** (marginally ahead; the prior "refuted" no longer holds). **(3) Circuit-breaker NEUTRAL (adaptability not supported)** — A ≈ B within noise (Sharpe LB 10.24 vs 10.19; MaxDD 3.44% vs 3.75%; B marginally *better* on Ulcer), so no *material* de-risking; the prior "de-risks −22.4% MaxDD" was a flat-at-exit artifact (B still de-allocates fragile cells but buys no drawdown reduction). A wash, not a degradation. **(4) Gate statistic READY** — FPR controlled (A 0.000/B 0.002), MDE m*=1.75(A)/2.00(B) finite, realized LB 10.24 ≫ m* ⇒ `statistic_ready_for_g022a=true`; fixes the recurring fixed-plant unattainability (EXP-094-class); **G-022a must freeze the band ≥ m***. **Scale caveat:** Sharpe ~11-12 is in-sample favorable-selected, NOT deployment-realistic; binding read = EXP-097. Verified faithful (MTM conservation exact, marks causal, A1-A4 predeclared — not goalpost-moving). Outcomes retained. — *Prior (SUPERSEDED, flat-at-exit) record retained for file-drawer integrity: portfolio benefit NOT MET / within-noise; circuit-breaker reported de-risking; gate NOT READY — all overturned by the MTM correction above.* A Sharpe **9.87 (MBB lo 8.59)** / B **9.34 (lo 8.15)** / naive-IV **10.11 (lo 8.81)** / best cell US2000-1h **8.68**. **Portfolio-benefit criterion NOT MET (faithful negative):** A/B **point** Sharpes beat every cell, but their **lower bounds (8.59/8.15) sit just below** the best-cell point (8.68) — only naive-IV's lower bound clears it; **ERC does NOT beat naive-IV** in-sample (10.11>9.87>9.34, sub-thesis refuted — retained). **Adaptability SUPPORTED (descriptive):** circuit-breaker **B** de-allocates the fragile 1h cells (USTEC 12.0% / US2000 5.4% of grid steps), cuts **MaxDD 22.4%** (0.0769→0.0596) + lifts **Calmar 20.3→26.3** at −0.52 Sharpe, ann-return unchanged. **NEW portfolio-level confirmation statistic = NOT READY for G-022a:** synthetic-null **FPR controlled (A 0.000/B 0.001 ≤0.05)** but **bite-check RED** (planted-fire 0.10/0.15 vs 0.80 floor) ⇒ `statistic_ready_for_g022a=false` — a structural power artifact at the n=79-week holdout-equivalent (generic Sharpe=1.0 plant), **not "no edge"** → routes a **G-022a gate-scale decision** (re-scale the bite plant to the G-022a band before freezing). **C1 fix re-audited PASS** (cap on un-anchored weights → 1/vol² targeting → fixed to vol-anchor-first; realized vol ~1%→13%, gross-leverage CV 0.99→0.25, cap now dormant, Sharpe scale-invariant 1.8e-15). **0 candidate slots, 0 counted TEST reads** (portfolio-aggregate disclosure reusing the EXP-093 series; 11 carried strata stay 1/2, 37 stay 0/2); `holdout_untouched=true`; provenance reconciled abs-diff 0.0; determinism + causal-weight PASS. Analysis-set only — no holdout verdict (EXP-097). Outcomes retained. |
| **EXP-096** | `CF-MR-001/HYP-003` | Noise infusion — realistic 1-minute entry fill (v1/v2-binding/v3); re-derive the portfolio under v2; decide the G-022a holdout-frozen deployable set. | 0 / 0 | **COMPLETE 2026-06-25 (analysis-set, NO holdout verdict; audit PASS 0C/0W/5I; 0 reads/0 slots, holdout untouched).** Pure entry-leg perturbation of the EXP-095 construction (only the entry execution price changes; exit target/stop/cost frozen; exit path + keep mask reused verbatim from EXP-093; new `xen.intrabar_fill.resolve_entry_fills`); portfolio re-derived under the binding **v2** (next-1m-open + 0.05×ATR adverse slippage) with intra-1h MTM; m\* **inherited** from EXP-095 (not recomputed). **Fill-realism leg SURVIVES at v2:** A v2 Sharpe 6.50 (MBB LB **5.147**) / B 6.29 (LB 4.90) / naive-IV 6.44 (LB 5.09); benefit (like-for-like LB vs cross-cell-median single-cell LB **2.554**) A **+2.59 > sampling band 1.35 = ADDS_VALUE**, co-binding Calmar LB +4.28; **broad-based** (all 8 per-cell v2 Sharpe LBs positive 0.13–3.65; portfolio LB > best cell); ERC ≈ naive-IV. **Mechanism:** v1 latency-neutral + a flat 0.05×ATR tick subtracting an EXACT −0.05 ATR/event uniformly → halves BOTH the portfolio LB AND the baseline → relative diversification margin preserved (keep mask byte-identical to EXP-093). **Ladder (A Sharpe LB):** ideal 10.28 → v1 10.31 → v2 5.15 → v3 −1.65 (A BREAKS, MaxDD 40.9%); **v3 B +1.83 (MaxDD 6.0%)** — v3 a deliberately harsh STRESS CEILING (disclosure-only). **A-vs-B (G-022a input):** circuit-breaker NEUTRAL at binding v2 (A≈B; reproduces EXP-095) but large TAIL-INSURANCE at v3 (de-allocates fragile 1h cells USTEC 26.1%/US2000 21.7%; prevents 40.9%→6.0% MaxDD) → argues for Portfolio B. **Gate re-check (inherited m\*):** v2 A LB 5.15 ≥ 1.75, B LB 4.90 ≥ 2.00 → `statistic_clearable_under_noise=true` → G-022a band ≥ m\*. **EURJPY-4h flagged NOISE_DEGRADED** (v2 net ci_low 0.0079 < 0.025 margin) but net-positive, **RETAINED** (portfolio-only membership; G-022a decides set). Integrity: provenance abs_diff 0.0 vs EXP-093 all 8; MTM conservation ≤1.4e-14; determinism/causal-fill/causal-weight PASS; ideal variant reproduces EXP-095 A Sharpe point 11.691 exactly. Portfolio-aggregate / cost-re-resolution disclosure (EXP-085 precedent) — 11 carried strata stay 1/2, 37 stay 0/2; holdout never loaded. Outcomes retained. Next: G-022a freeze → EXP-097 global-holdout release. |
| **G-022a** | — | Pre-holdout freeze: non-empty deployable set + analysis-set portfolio edge + calibrated/bite-checked statistic + predeclared band ⇒ freeze `G-022a-gate-criteria.md` + `G-022-gate-criteria.md`; else HALT (holdout preserved). | 0 / 0 | **FREEZE — ADJUDICATED 2026-06-25** (`G-022a-gate-review.md`). All four D0 §D9 preconditions MET on EXP-095/096 evidence. Frozen: deployable set **carry-8** (EURJPY-4h flagged NOISE_DEGRADED but net-positive → carried; ratifiable trim-to-7); construction = EXP-095/096 binding-**v2** noise-aware ERC + intra-1h MTM, verbatim; **A-vs-B both read on ONE holdout shot (operator decision 2026-06-25), primary = Portfolio B** (no OR rescue; chosen pre-holdout, no tuning); **CONFIRM(P) iff holdout Sharpe_LB > band_P AND Calmar_LB > 0**, band_A 1.75 / band_B 2.00 (= inherited A4 m\*); read accounting = one global-holdout-governance event (outside the analysis-TEST ledger; 11 carried strata stay 1/2; 0 counted reads / 0 slots; non-repeatable). → EXP-097. |
| **EXP-097** | `CF-MR-001/HYP-003` | Global-holdout release — one-shot OOS-final confirmation of the frozen noise-aware portfolio (binding) on the final-30% global holdout. | **1 global-holdout shot SPENT / 0 slots** | **COMPLETE 2026-06-25 — `DEPLOYABLE_CONFIRMED` (G-022 terminal).** The single sanctioned global-holdout shot is SPENT (non-repeatable, non-upgradable; recorded as a holdout-governance event in `test-read-ledger.md` in the same change). Both A and B read from one holdout materialization = ONE read; terminal G-022 keyed off primary **Portfolio B**: holdout Sharpe LB **4.762 > band 2.00** AND Calmar LB **10.731 > 0** → CONFIRM; A co-confirms (LB 4.250 > 1.75), no OR rescue. 7/8 cells positive holdout net ci_low (EURJPY-4h net-negative, pre-flagged, smallest contributor — no masking). counted_test_reads=0 (analysis-TEST ledger untouched; 11 carried strata stay 1/2); candidate_slots=0. Audit PASS (0C/0W/4I). The bare RSI-2 fade is the programme's first deployment-grade price strategy. |
| **G-022** | — | Terminal gate: DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE, per the G-022a band. | 0 / — | **DEPLOYABLE_CONFIRMED 2026-06-25** (EXP-097; primary Portfolio B holdout Sharpe LB 4.762 > band 2.00, Calmar LB 10.731 > 0). |
| **EXP-098** (`D0-amendment-002`) | `CF-MR-001/HYP-003` (robustness companion) | **Non-binding cross-broker & aggregation-method robustness replication.** Rerun the G-022a-frozen deployment portfolio **verbatim** on an **independent broker's** 1-minute data (`data/timebars/pps/`, same 8 instruments + span), under two bar-aggregation timestamping methods — **Arm 1 `PPS-CANON`** (bucket-boundary label, deployed) and **Arm 2 `PPS-ALTAGG`** (`AGG-LASTCLOSE`, last-source-close label). Full PPS timeline; criterion = the inherited EXP-097 band (primary B: Sharpe LB > 2.00 AND Calmar LB > 0), per arm. Tests broker-overfit (Arm 1) and aggregation-overfit (Arm 1 vs 2). | **0 / 0** (PPS robustness read — outside the analysis-TEST ledger and the INFR-003 global holdout; recorded as a robustness governance disclosure; **cannot upgrade/revoke EXP-097**) | **COMPLETE 2026-06-25 — `CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST` (non-binding; audit PASS 0C/0W/3I).** Both arms ROBUST: primary Portfolio B PPS Sharpe LB 5.97 (CANON) / 6.10 (ALTAGG) > band 2.00, Calmar LB 12.5 / 13.3 > 0 (n=251 evaluable weeks; A co-confirms). Broad-based (8/8 cells net-positive both arms; EURJPY-4h recovers from the INFR-003 holdout net-negative to +0.026); drop-one masking holds (no flip). Aggregation near-inert (arms differ only by ±1 trailing 1h bar; 4h nets identical to ~1e-5). Integrity PASS (conservation ≤2.8e-14, determinism + causal-weight/fill); INFR-003 holdout never loaded; `counted_test_reads=0`, `candidate_slots=0` (11 carried strata stay 1/2, 37 stay 0/2). Recorded as a robustness governance disclosure (`test-read-ledger.md`). `AGG-LASTCLOSE` retained (file-drawer); PPS registered + now "touched" as a robustness data source (future binding use needs its own governance). **EXP-097 `DEPLOYABLE_CONFIRMED` UNCHANGED — strengthening companion, not an upgrade.** |

## Chapter 02 · Phase 001 Batch (Referee-Gate Adaptivity Renew + Causal RSI-2 Benchmark, CF-MR-002) — REGISTERED, G0 PENDING

**Opened:** 2026-06-27 (first Chapter-02 phase; cTrader-primary era).
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/design.md`.
**Provenance.** Opens after the Chapter 01→02 rollover (tag `chapter-01-close`). CF-MR-001 is
**CLOSED — REFUTED** (EXIT-RCT `rct[di]` exit look-ahead; G-021/G-022 retracted) and not reopenable
by re-parameterization; its closure note authorises a **new family under a new D0 only after the
`rct[di-1]` causal fix** — that family is **CF-MR-002** (`candidate-families/cf-mr-002.md`).
**Purpose (dual).** (1) **Referee renew** — fix the gating-system rigidity uncovered across Chapter 01
(KB **L-12**: conjunctive fragility / structurally-impossible legs / fixed thresholds mis-scaled to the
candidate); investigate a power-aware, candidate-matched adaptive gate that **keeps the earned FPR
control**, FPR-recalibrated on the dogfood-negative + synthetic-positive (EXP-019 protocol) and
**frozen before** it judges any candidate. (2) **Architecture benchmark** — push the causal RSI-2 fade
(CF-MR-002) end-to-end through the new lean cTrader-primary pipeline to measure correctness + speed/
token efficiency vs the Chapter-01 8-stage baseline.
**Binding governance.** The frozen Chapter-01 suite stays binding and is reported in parallel until a
redesign is re-ratified on fresh draws. The adaptive gate must **not** be tuned on CF-MR-002 (the L-12
selection-bias trap). The final-30% global holdout is **not** in scope for Phase 001.
**Slot accounting.** Registration consumes **0 candidate slots** (first slot consumed only at a future
ADMIT, per CF-MR-001 precedent) and **0 counted TEST reads**; holdout sealed.

| ID | Hypothesis | Role | Slot | Status |
| --- | --- | --- | --- | --- |
| `CF-MR-002/HYP-001` | Causal tradability screen | Does the causal (`rct[di-1]`) RSI-2 fade, run in-engine under bar-open / open-to-open execution, net-clear the referee on TRAIN with the leak tripwire collapsing the future-destroying control? Also the architecture-benchmark vehicle. | 0 (screen) | **REGISTERED — G0 PENDING (2026-06-27).** 0 reads, holdout sealed. Honest prior: causalized the bare fade is not net-tradable (L-01). |
| Referee-adaptivity redesign | methodological | Power-aware / candidate-matched gate (L-12); FPR-recalibrated on dogfood-negative + synthetic-positive; frozen before any live read. | 0 (methodology) | **REGISTERED — G0 PENDING.** Frozen suite retained in parallel until re-ratified. E-series substrate work below. |

**Referee-renew E-series disposition (methodological substrate; 0 slots, 0 reads each).** These
characterize the renew levers; they screen **no** candidate and touch **no** candidate slot or TEST
read. `referee_calibration.py` stays byte-frozen — seams are additive in `referee_adaptive.py`.

| EXP | Arm | Outcome (audit) | Slot/Reads |
| --- | --- | --- | --- |
| **EXP-001** | **E1 — cost convention (per-held-bar vs amortized)** | **COMPLETE 2026-06-28 — ACCOUNTING_MATERIAL (audit PASS).** Per-stratum (16 inst × {1h,4h}): ΔMDE = MDE_perheld − MDE_amortized ≥ 0 on all 32 strata (per-held-net-edge grid units; pool median 1.5, max 11.5 bps BTCUSD/4h — disclosure-only L-03), scaling with cost & L. Per-held over-charges turnover ~L×; **L-12 Mode-1 is partly accounting, not solely gate shape** → E3 adopts amortized accounting, targets only the tail-only/sparse residue. Seam `gate_stack_core_costfn` bit-identical to frozen core at `strategy_return_bps`; analysis-only; holdout sealed. One mis-specified guard fixed+rerun (ΔMDE bit-identical, orthogonality proven). | 0 / 0 |
| **EXP-002** | **E2 — synthetic-positive battery + dogfood (shape blindness)** | **COMPLETE 2026-06-29 — SHAPE-BLIND map delivered (audit PASS).** Binding=amortized, 16×{1h,4h}×4 shapes. **DENSE/TAIL DETECTED 32/32; SPARSE ~uniformly blind** (23 DENSE_ONLY_BLIND + 9 finite only at grid-top 32 bps); **STATE 15 DETECTED + 17 MDE_INFLATED** (~2–4× dense). Leg-level mechanism (audit-confirmed): **SPARSE → L1_readiness structural veto** (≈6% activity, test 16/27 < min_state_count 20; L1=False at every e incl. 32 — L-12 §2 structurally-impossible leg, edge-independent); **STATE → L5_materiality on the pooled-diluted mean** (frac_A=0.5, L-03); **TAIL robust** (matched mean + dense activity). FPR=0/32 both conventions + dogfood (Donchian R + MA 20/50, causally lagged ≤t-1) 0/64; future-destroy collapsed all detections. Confirms L-12 §1/§2; localizes blindness to **L1+L5**. EXP-019-style calibration substrate E3 is measured against. **Reconciled with binding D0 (operator 2026-06-29):** the sparse-L1-veto is the **validity floor** (correct UNPOWERED refusal of a ~6%-activity vehicle), NOT a target — D0 keeps L1 rigid; E3 adapts **only L3/L5** (sub-population L5 recovers the STATE loss). NOT a generic tail fix. Turnover helpers promoted to `referee_adaptive` (behaviorally identical); frozen `referee_calibration.py` byte-untouched. | 0 / 0 |

**E3 split (operator decision 2026-06-29 — honor binding D0, no D0 amendment).** D0 (checkpoint:102–103)
keeps L1+coverage **rigid** (validity floor, FPR≈0) and adapts **only** the economic legs L3/L5. E2's
sparse-L1-veto is the floor working as intended (UNPOWERED refusal of a ~6%-activity vehicle), not a
Mode-1 false-reject; loosening L1 would forfeit the FPR≈0 guarantee, and the honest sparse fix is a
different evaluation vehicle (L-04), out of Phase-001 gate scope. E3 is split to keep each rung
single-question and in budget:

| EXP | Arm | Role | Slot/Reads | Status |
| --- | --- | --- | --- | --- |
| **EXP-003** | **E3a — economic-leg adaptation** | Power-aware **L3/L5** (apply where finite MDE) + **sub-population L5** (recover the STATE loss) + amortized accounting (E1) + **remove the L2 no-op** (F4). **L1 rigid.** FPR-recalibrate on the E2 dogfood-negative + synthetic-positive; success = **DET-dominance** (strictly lower economic MDE at FPR ≤ frozen). Sparse stays UNPOWERED by design. | 0 / 0 | **COMPLETE 2026-06-29 — CHARACTERISATION (audit PASS, 0 Critical).** Adaptive recovers **STATE** (ΔMDE frozen−adaptive finite all 32, median 10.5, max 24.0 bps) and — unplanned — **sparse 28/32** (design "sparse UNPOWERED" predeclaration **REFUTED**); both **leak-clean** (no_plant ≤0.05, future-destroy collapses ≤0.05) and **D0-compliant**: L1 proven **bit-identical** frozen vs adaptive (rigid; the earlier "amortized shifts effective_n→L1" mechanism refuted — recovery lives in L3/L5). Frozen sparse blindness on 4h was the economic composite (L4+pooled-L5), not L1 → **E2's "sparse=L1 structural veto" was domain-conflated** (true 1h min_state=20, false 4h min_state=8). Predeclared split **15 DET_DOMINANT / 17 FPR_BROKEN** is **BRITTLE** (strict `FPR_adaptive>0`, one 1/162 noise pass trips it): **16/17 FPR_BROKEN within Wilson noise of 0; only JP225/4h (6/162=0.037) Wilson-resolved >0** → genuine FPR break = **1/32**. Mechanism localised: every dogfood FP passes via the **q\*=0.75 sub-population L5 path exclusively** (pooled rejects all); the same leg is the single engine of **both** recovery and FPR (4h-concentrated, high-dispersion 75th-pct clears materiality on noise). `referee_calibration.py` byte-frozen; provenance clean; perf opts bit-identical. **0 slots / 0 TEST reads; holdout sealed.** **→ AMENDMENT A1 (2026-06-29, operator amend-in-place; re-audit PASS, 0 Critical) SUPERSEDES the above as the binding result:** studentized the sub-pop L5 (PASS = `q*-quantile/std` bootstrap CI-lower > `Q_STUD_MIN=Φ⁻¹(q\*)≈0.674` **AND** raw-bps CI-lower > materiality; `Q_STUD_MIN` candidate-blind, from q\* alone) + Wilson-resolved verdict rule + retracted the mis-specified sparse-UNPOWERED tripwire. Full 32-stratum rerun: **DET-DOMINANT 32/32**; adaptive dogfood FPR **0/32** (was max 0.037); STATE ΔMDE median 7.5 max 23.5 (retained); SPARSE 28/32, zero per-shape regressions. Cure verified **at the gate** (audit R1): prior-worst nulls (JP225/GBPUSD/AUDJPY 4h) now `passes_adaptive=0/162` — the previously-passing draws clear raw materiality but fail the studentized floor (stud_ci 0.15–0.52 < 0.674). Recovery = pooled-OR-studentized-subpop, both load-bearing (EURUSD/4h 17/17 via subpop alone), no abstain loophole; future-destroy collapses on the studentized path (STATE fd 0.000, sparse ≤0.050). **The brittle "15/17" raw-bps result is retained as the diagnostic that drove A1.** A1 **pulls E3b's return-series/Sharpe-LB unit forward** (the studentized stat IS the dispersion-normalized materiality). `referee_calibration.py` still byte-frozen; L1 still bit-identical/rigid. → routes **E5 (freeze)**. |
| **E3b** | **composite-form selection (Q4)** | Q4 composite-form (validity→economics §10.3a vs single-statistic variant c) adjudicated by DET-dominance. **Scope reduced 2026-06-29 (A1):** the Q9/F10 return-series materiality unit (Sharpe LB / dispersion-normalized) was **pulled forward into E3a** as the studentized sub-pop L5; E3b is now composite-form selection only. | 0 / 0 | **FOLDED 2026-06-29 — return-series half → E3a (A1); Q4 composite-form half → E5 (see below).** E3b dissolves as a standalone rung; retained here as the record. No separate EXP-ID activated. |
| **EXP-004** | **E4 — robustness sweep** | Stability of the E3a DET-dominance to the one remaining free choice + resampling: **`q*` sensitivity** (DET-dominance + FPR=0 stable across `q* ∈ {0.6,0.7,0.8}`; `Q_STUD_MIN=Φ⁻¹(q*)` tracks q*), **bootstrap-count / seed stability** (ΔMDE + FPR boundary not resample-noise), **residual skew-FPR** (the A1.2 predeclared right-skew-null risk on the studentized floor, measured explicitly). | 0 / 0 | **COMPLETE 2026-06-29 — FREEZE LICENSED (RANGE-BOUNDED) (audit PASS, 0 Critical).** 9 configs × 32 strata = 288 per-stratum verdicts. **Regression anchor** (q\*=0.75, nb=500, off=0) reproduces EXP-003 (A1) **0/32 mismatches** → harness correct. **Baseline q\*=0.75 = 32/32 DET_DOMINANT**, adaptive dogfood FPR **0.0**, zero per-shape regressions, STATE ΔMDE median 7.5 (min 4.0) retained; q\*=0.7 equally clean → **safe q\* range {0.7,0.75}**; extremes q\*=0.6 / q\*=0.8 each flip **1** stratum. **Residual skew-FPR (A1.2) REFUTED:** R3 right-skew null (sample skew ≈3.6, mean ≈0) → **0/32** adaptive passes (frozen arms also 0.0 ⇒ null well-formed); the studentized floor `Q_STUD_MIN=Φ⁻¹(q*)` holds because skew lifts the *raw* but not the *studentized* q\*-quantile → **no `Q_STUD_MIN` bump warranted**. **All 6 FPR_BROKEN are single 1/162 dogfood passes** (`wilson_lower(1,162)=0.0011>0` trips the A1.3 rule vs a *zero* frozen baseline) — gate true FPR ≤0.62% ≪ 2α=0.10 control, none survive future-destroy (max 0.050) ⇒ a verdict-**label** artifact, **not** an FPR leak → recorded **E5 freeze-adjudication precondition** (min-pass-count ≥2 / compare to 2α not 0; derived candidate-blind, not from E4 outcomes). Bootstrap/seed stable (R2 94/96, the 2 breaks same artifact); D-regime recent-third 30/32; 4h sub-pop CI non-degenerate 0.83–8.87 bps over 144–231 episodes (L-06). `referee_adaptive.py`+`referee_calibration.py` **byte-frozen** (git); only runtime `Q_STUD_MIN=Φ⁻¹(q)` set per config (candidate-blind); frozen STATE-MDE q-invariant. Analysis-only; **0 slots / 0 TEST reads; holdout sealed.** → routes **E5 (freeze at q\*=0.75)**. |
| **EXP-005** | **E5 — DET-adjudication + FREEZE (+ folded Q4 form-check)** | Adjudicate the E3a adaptive gate (post-A1, DET-dominant 32/32) and **FREEZE** it as the renewed referee. **MANDATORY folded Q4 form-check (from E3b, 2026-06-29 operator decision — must NOT be skipped):** before freezing, run the **composite-form selection** — compare the §10.3a validity→economics composite (the form E3a uses) against the **single-statistic variant-c** on the E2/E3a substrate via DET-dominance; freeze §10.3a only if it matches-or-beats variant-c, else freeze the winner. Record variant-c on the freeze rationale as the rejected alternative either way. | 0 / 0 | **COMPLETE 2026-06-29 — RENEWED REFEREE FROZEN (audit PASS, 0 Critical).** 3-form DET (frozen / §10.3a / variant-c) at the single E4-validated point (q\*=0.75, NB=500, off=0), 16×{1h,4h}=32 strata. **§10.3a (`gate_stack_adaptive`+`adaptive_row`) MATCHES-OR-BEATS variant-c 32/32** under DET-dominance (lower MDE at equal-or-better FPR); §10.3a **leak-clean 32/32** (dogfood FPR 0/32, future-destroy max 0.050). **variant-c (`adaptive_row_variant_c`, single statistic = incremental-net vs-naive CI-lower>0; L5/sub-pop demoted to diagnostics) REFUTED:** no absolute edge floor ⇒ admits anything less-bad than the net-negative naive-momentum baseline ⇒ dogfood FPR **0.062–1.000** (all 16 1h ≈1.0) and **survives future-destroy** (max 1.0; BTCUSD/USDJPY/XAUUSD 4h) — DET-ineligible on every stratum. **Mechanism-general** (any single-statistic form omitting an absolute floor inherits the "beats a losing baseline" leak); §10.3a's neutral-CI + materiality + studentized-subpop legs supply exactly the FPR control the single statistic lacks. **FROZEN at §10.3a, q\*=0.75** (`results/freeze_manifest.json`; `sha256(referee_adaptive.py)=b4fd6cb1…ae847`; pins Q_STUD_MIN=Φ⁻¹(0.75), materiality 1.5/3.0, 17-cost map, open-to-open ≤t-1); **variant-c recorded as the rejected alternative** (its `adaptive_row_variant_c` carries a "⚠ REJECTED — never call as a gate" banner). **E4-derived less-brittle freeze-adjudication FPR rule** (`MIN_FPR_PASSES=2`/`2α`; adjudication-harness only, gate byte-unchanged) adopted candidate-blind — retires the single-1/162 label artifact. Regression anchor **0/32** reproduces EXP-003(A1)/EXP-004; `adaptive_row_variant_c` **additive** (`referee_adaptive.py` 70+/0−; `adaptive_row`/`gate_stack_adaptive`/constants byte-unchanged); `referee_calibration.py` byte-frozen. **Freeze is BEFORE any live read (L-12 honored); not tuned on CF-MR-002.** Mid-run fix to the adjudication/freeze *classification* logic (DET-dominance-at-equal-FPR; §10.3a-only leak gating) applied before the binding rerun; underlying numbers unchanged, anchor passed both runs. Screens no candidate; no slot/TEST read. **0 slots / 0 TEST reads; holdout sealed.** → **D-benchmark** (CF-MR-002 causal in-engine; operator-gated). |

**Deferred branches (registered, uncounted).** The CF-MR-001 levers do **not** carry over implicitly —
vol-regime partition, CONTRARIAN arm, 25/75 scheme, 15m capture, regime×variant cross-cuts, parameter
tuning, instrument/domain expansion: each needs its own dated D0-amendment + slot decision under
CF-MR-002. Holdout release and deployment economics are out of Phase-001 scope. All outcomes retained.

## Chapter 02 · Phase 002 Batch (Cross-Domain Mean-Reversion Availability, CF-MR-003) — EXP-008 METHODOLOGY FINDING (verdict held); native re-screen = EXP-009

**Update (2026-07-01, Amendment A2).** EXP-008 is closed as a **methodology finding**, not a family
verdict. Its 3-leg screen (INCONCLUSIVE) and 2-leg VR∧HL screen (EXONERATE) both used an evaluation vehicle
inherited from the price-geometry family (fixed-horizon MFE + Δ-over-regime-matched-**random-timing**) that
is **non-native to MR**. A vehicle diagnostic (analysis-only, 0 reads; reactive, not pre-registered)
**indicates** the EXONERATE is vehicle-dependent: under a **dislocation-matched** null the native target metrics separate (anchor-hit
+2.9 pp, fraction-recovered +2.7 pp, CIs exclude 0) while MFE is blind. **EXONERATE HELD, not booked.**
CF-MR-003 stays `REGISTERED` with **preliminary positive native evidence**; the native re-screen is
**EXP-009** (new D0, target-based estimand + dislocation-binned null). Lesson **L-13**. Still **0 slots /
0 counted TEST reads; holdout sealed**. The HYP-001 row below records the original 3-leg run for the
file-drawer; its verdict is superseded by this methodology finding (not a family closure).

**Opened:** 2026-07-01 (G0 ratified). **Governing checkpoint:**
`docs/experiments-docs/checkpoints/2026-07-01-002-cross-domain-mean-reversion/design.md`.
**Family:** CF-MR-003 (`candidate-families/cf-mr-003.md`) — operator-ratified probe against the
terminal-branch prior, admitted only for a distinguishing information source (cross-domain deviation +
MR-screen-as-selector), gated availability-first at zero cost.

**Multiplicity design:** 16 inst × 5 anchor series × 3 domain pairs ≤ 240 cells, controlled by
**cross-axis Holm over the 15 series×domain axes** (max-statistic permuted-axis admission, G-019 pattern,
`xen.availability_gate`). Per-stratum binding (L-03); pooled = disclosure-only.

| Candidate ID | Hypothesis | EXP-ID | Slot | Status |
| --- | --- | --- | --- | --- |
| `CF-MR-003/HYP-001` | Availability screen — does MR-screen-conditioned entry produce a reversion excursion toward the higher-domain anchor beyond a matched-random, matched-count, matched-regime control on TRAIN, for any of 5 anchor series × 3 domain pairs? | EXP-008 | 0 (availability screen) | **COMPLETE 2026-07-01 — SCREENED-INCONCLUSIVE (underpowered; audit PASS, 0 Critical).** 0/15 axes eligible, 0 powered instrument-cells (both endpoints), max 18 events/cell (N_min=100); only 33/240 cells cleared the ≥2-event floor. **Root cause (drop-one disclosure):** the design's 3-leg MR selector (VR∧half-life∧**Hurst-DFA<0.45**) is vetoed by the Hurst leg — every leg-combo *with* Hurst → ≤792 total events & **0/240** powered; *without* it (VR+HL) → 315,644 events & **216/240** powered. `Hurst<0.45` (increment anti-persistence) mis-applied to the mean-reverting deviation **level** series (locally persistent, Hurst>0.5), contradicting the VR/half-life legs — the **L-12 §3 near-impossible-conjunctive-leg** pattern reappearing inside the *screen* (DFA validated correct: WN α≈0.52, walk α≈1.48). Per design §7 (`>½ axes ineligible-UNPOWERED`) → **INCONCLUSIVE**, not EXONERATE (axes never powered → availability never *tested*). **CF-MR-003 retained, neither admitted nor exonerated;** terminal-branch prior untested on this vehicle. Leak-clean (2 tripwires shipped — conditioning-label permutation + forward-excursion time-reversal; no admitting cell to fire on). Analysis-only, TRAIN-only, every decision input ≤t-1. **0 slots / 0 counted TEST reads; holdout sealed; not tuned on the referee (L-12).** All 15 series×domain axes UNPOWERED. Fix = a corrected re-screen (2-leg VR+HL, or Hurst-on-increments) under a **new dated-D0** experiment — not amend-in-place (no contamination; honestly underpowered). |

**EXP-009 — CF-MR-003/HYP-001 native re-screen (2026-07-01) — SCREENED-ADMIT (per-stratum, audit PASS, 0
Critical).** After EXP-008's methodology finding (vehicle non-native to MR, L-13), EXP-009 re-screened with
a **native** vehicle: target-based estimands (anchor-hit / fraction-recovered / time-to-anchor,
event-specific half-life horizon) against a **screen-fail dislocation-matched** null (operator-ratified
pass-vs-fail), per-stratum (L-03; axis-majority rule relaxed on operator direction). **36 leak-clean
per-instrument passes** (label-permutation collapses): **S5_SPREAD 20** (FX majors), **S3_DETREND 14**,
**S4_OU 2**; pervasive positive hits on S1/S2 (precision-limited, UNPOWERED_HINT). Robust on S5_SPREAD
(18–20 across horizon/floor/z-edges), moderate on S3_DETREND (8–16); recent-third unconfirmed (power).
**CF-MR-003 → SCREENED-ADMIT.** Amendments A1 (drop Hurst leg, EXP-008), A2 (vehicle mismatch, EXP-008),
B1 (time-reversal → diagnostic), B2 (endpoint floors + precision-aware disposition + per-stratum). Still
**availability, not tradability**; **0 slots / 0 counted TEST reads; holdout sealed; referee untouched
(L-12)**. Concretization = the family's **form-2 limit-at-anchor (target=mean)** in a separate
**price-primary** experiment (new D0, operator-gated) — the tradability test; a counted TEST read / holdout
release remains gated on that.

**Deferred (registered, uncounted).** Strategy machinery (`/DIRECTION /REENTRY /TARGET /EXIT`), cost/net
tradability, counted TEST reads, and holdout release are all out of Phase-002 scope — each needs its own
dated D0 + slot decision. The EXP-009 ADMIT advances CF-MR-003 to the concretization gate; no slot/read
consumed. All outcomes retained.

## Chapter 02 · Phase 003 Batch (CF-MR-003 Tradability Concretization, CONC-1) — EXP-010 (T1) + EXP-012 (T2) NOT-TRADABLE → TRADABILITY CLOSED

**Opened + closed:** 2026-07-01 (Track 1 = EXP-010, Track 2 = EXP-012). **Family:** CF-MR-003. **Governing checkpoint:**
`docs/experiments-docs/checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/`. **Governing experiments:**
EXP-010 (T1 exec-1h) + EXP-012 (T2 exec-15m; referee prereq E7/EXP-011). **Slot accounting: 1 candidate slot CONSUMED**
(first tradability exploration on CF-MR-003; **T2 opened 0 new slots** — same concretization); **0 counted TEST reads**;
holdout sealed; frozen referee untouched (L-12).

**EXP-012 — CF-MR-003 CONC-1 Track 2 (2026-07-01) — NOT-TRADABLE (POWERED); price-primary in-engine; audit PASS, 0
Critical.** The same **form-2 limit-at-anchor** fade on the **24 EXP-009 exec-15m admits**, adjudicated under the
**frozen 15m referee** (EXP-011, §10.3a q\*=0.75 + E6 P\*-gate, `min_state_count=25`), **one Holm family, two explicit
sub-families**: **T2a = 14 S3_DETREND single-symbol** (rolling-OLS log-price trendline-residual anchor, W=200; new
single-symbol path, S3 OLS bit-parity vs `cross_domain_mr.rolling_ols_fit`, Δ 1.8e-15) + **T2b = 10 S5_SPREAD basket**
(exec-grid-β, in-engine `MarketData.GetBars`). **Result: 24/24 POWERED** (reversion episodes 70–390 ≥ 15m floor 25 —
the ~4× 15m bars clear the higher floor that stranded T1), **0/24 admit, 0/24 Holm-admit**; every CI_lower ≤ 0 (net
−0.77…+0.04 bps/active — best GBPUSD +0.04 / US2000 +0.02, both CI_low<0; worst BTCUSD −0.77, USTEC(T2b) −0.54). T2a
0/14, T2b 0/10 — sub-families agree, **no pooled masking**. **Mechanism:** shorter-horizon reversion captures a smaller
favourable move against the **same** per-instrument round-trip cost → the powered definitive close the LOW prior
predicted (not UNPOWERED like T1). **EXP-010 gate-debt DISCHARGED:** F-1 vehicle fidelity **PASS all 24** (z_corr 1.00,
Jaccard 0.97–0.99 — the S3 single-symbol path carries no basket carry-forward; clears the tightened 0.90/0.70 tol vs
T1's 0.67/0.30); F-2 leak-resistance now **tested and non-vacuous via the live control**: planted-positive (+8 bps)
detected **24/24** (power real) + **valid future-destroy** (live phase-shifted-basket shuffle, `EXP-012-t2b-shuffle`)
**CLEAN** (`shuffle_survivors=[]`, `tripwire_pass=True`). **Control caveat (audit, non-verdict-moving):** the raw-script
`REJECT_LEAK` headline was a **false trip** — the *Python* F-2 "future-destroy" permutes the realized-bps array, but a
mean statistic is **permutation-invariant**, so an additive-positive plant can never collapse under it (23/24
`destroyed_pass=True`); superseded by `results/verdict_corrected.json`, no re-run (verdict NOT-TRADABLE either way).
Follow-up (methodology): a Python-side leak control for a mean referee must break the position↔return alignment causally
(permute positions + re-assemble), never permute P&L. Causal-provenance PASS (≤t-1 decision inputs; fills in-range;
fence sealed — 0 rows at/after `AnalysisEndUtc` on all 34 runs). **CF-MR-003 → CONC-1 NOT-TRADABLE at 1h (T1) AND 15m
(T2) ⇒ TRADABILITY CLOSED:** availability (EXP-009 SCREENED-ADMIT) does **not** survive to net at either execution
horizon; with sister CF-MR-002 EXONERATED, no CONC-2 axis sweep is warranted (moot; no P-02 rescue). Family **retained**,
all outcomes kept. A counted TEST read / holdout release stays gated on a TRAIN net-positive (none occurred).

**EXP-010 — CF-MR-003 CONC-1 Track 1 (2026-07-01) — NOT-TRADABLE (UNPOWERED; price-primary in-engine; audit PASS,
0 Critical).** Concretized the EXP-009-admitted S5_SPREAD to net: **form-2 limit-at-anchor** (`/TARGET`=mean,
`/DIRECTION`=fade, `/REENTRY`=none), **exec-grid-β** anchor computed **in-engine** (multi-symbol
`MarketData.GetBars`, XRSI pattern; `StrategyHost/CrossDomainMrLimitModel.cs`), adjudicated under the frozen 1h
referee (§10.3a q\*=0.75 + E6 P\*-gate). **Member set = 5 DISTINCT S5 exec-1h cells** under **phase Holm(5)**:
AUDUSD, GBPUSD, NZDUSD (FX_MAJORS basket), US2000, US500 (INDICES basket). **Member-set correction (substrate
override of design prose):** EXP-009's "S5_SPREAD 20 admits" double-counts the exec-1h **1D/4h-anchor label**,
which is byte-identical for exec-grid-β S5 (`per_cell.parquet` max|Δn_events|=0) → the family has **15 distinct**
S5 strategies (5 exec-1h + 10 exec-15m), not 20; T1 = 5, not the design's earlier 10. **Result: 0/5 powered,
0/5 admit** — the VR∧HL∧|z|≥2 conjunction fires only 10–32 reversion episodes/cell → below the 1h referee floor
`min_state_count=20` (per cell: 3/11/7/7/15); net −0.70…+0.10 bps/active bar, all CIs cover 0 (only GBPUSD
fractionally +). **Availability does NOT survive to net** — UNPOWERED ("could not test at power"), not a positive
refutation; consistent with the honest LOW prior + CF-MR-002 exoneration. **Leak tripwire** (phase-shifted basket,
`EXP-010-shuffle`) `surviving-under-shuffle=[]` → PASS **but vacuous** (null live edge; the control read *more*
positive, unpowered noise) → leak-resistance UNTESTED (audit F-2). **Gate-debt (audit F-1, binding before any
future powered-positive booking):** the in-engine vehicle is a **loose replica** of the screen — anchor *level*
corr 0.99 (β correct) but residual `dev` corr 0.73 / `z`-selector corr 0.67, |z|≥2 Jaccard 0.30 (real cTrader 1h
bars + basket carry-forward-≤t vs the screen's m1-aggregation + exact-`CloseTime` join). Causal-provenance PASS
(decide-before-fold `≤ t-1`; fills executable in-range after a smoke-caught gap-through-fill fix; fence sealed —
0 rows at/after `AnalysisEndUtc` on all 10 runs). **CF-MR-003 → SCREENED-ADMIT / CONC-1 NOT-TRADABLE.** Track 1
consumes 1 slot / 0 reads; **T2a (14 S3 exec-15m) + T2b (10 S5 exec-15m) DEFERRED behind E7/EXP-011** (frozen
referee 15m-domain extension). A counted TEST read / holdout release remains gated on a TRAIN net-positive (none
occurred). All outcomes retained.

## Chapter 02 · Phase 004 Batch (CF-MR-004 Cross-Instrument Spread MR) — EXP-013 CONFOUNDED (retained) → EXP-014 (HYP-002) faithful redo NOT-TRADABLE

**Opened:** 2026-07-02. **Family:** CF-MR-004. **Governing checkpoint:**
`docs/experiments-docs/checkpoints/2026-07-01-004-cross-domain-mr-renewal/`. **Slot accounting: 0 candidate
slots consumed, 0 counted TEST reads** (TRAIN-only disclosure throughout). Holdout sealed; frozen referee untuned (L-12).

| Candidate ID | Hypothesis | EXP-ID | Slot | Status |
|---|---|---|---|---|
| `CF-MR-004/HYP-001` | Does the precalc limit-order cross-instrument MR fade (4 series) produce availability + net edge per stratum on TRAIN? | EXP-013 | 0 | **DOWNGRADED CONFOUNDED (amendment 2026-07-02) — retained, never deleted.** As-run 0/32 admit, but form-1 exit absent + form-2 TP frozen → not the proposed strategy; not a family reading. Superseded by EXP-014. Lesson **L-14**. |
| `CF-MR-004/HYP-002` | Does the **faithful** full-exit strategy (form-1 event-reversion + refreshing form-2 + horizon; reentry none/allow/extend; trend/vol conditioners) produce availability + net edge per stratum on TRAIN, and if not which leg fails? | EXP-014 | 0 | **COMPLETE 2026-07-02 — NOT-TRADABLE (faithful; audit PASS, 0 Critical).** 152/152 cells (4 series × 4 arms). Both proposal-named exits fire (form-1 281 / refreshing form-2 1898 / horizon 1266, primary) → **L-14 discharged**. Frozen 4h referee per stratum: **0/38 net- AND gross-admit, homogeneous (no masking)**; availability does not separate at 4h (native reversion-completion Δ vs dislocation-matched control ci_low<0 on ~all cells). Mechanism = **capture-vs-dispersion wash** (per-trade −57…+29 bps; net ci_low<0) — same cost/capture veto as CF-MR-002/003. Power caveat: 19/38 cells bite-fail (per-cell referee underpowered on a discrete round-trip bracket, L-12 mode-2); credible null on the bite-passing subset (also all reject). Leak tripwires moot (0 admits); label-perm mean-invariant/vacuous. Independent 6-stage MR screen booked pre-verdict (VR<1 on S7/S8 baskets; S6 pairs near random walk). **Disposition: RETIRE CF-MR-004 recommended, OPERATOR-GATED.** All outcomes retained; every decision input ≤ t-1; holdout sealed. |
| `CF-MR-004/HYP-003` | On S8 (basket−median₉₀), 1h+4h, does the outlier revert beyond a coin flip (symmetry two-barrier) and does any single-leg or both-leg config clear the frozen referee per (cell,domain,arm,z\*)? | EXP-014b | 0 | **COMPLETE 2026-07-03 — REJECT_LEAK, 0 TRADABLE / 220 strata (audited; C1 label logic + C2 both-leg weighting fixed analysis-only).** 1h availability raw-passes all survive peer-feed phase-shift (own-price auto-reversion; the basket dilutes it) → S8-at-1h retired. Collapse-verified availability only 4h JP225 (p_inward 0.696, ci 0.638; replicated z1.5) + weakly 4h EURUSD — not tradable there (moving-mean exit = small-f2-wins / large-f1-anchor-drift-losses ≈ 0 gross). extend admits = own-price MR harvest. Both-leg killed by the ~50-bar loss tail + N+1 costs. → HYP-004 lean-bracket last shot. 0 slots, 0 counted reads, holdout sealed. **⚠ MULTI-LEG ROWS SUPERSEDED_BY_VAL-006 (2026-07-04):** allow/extend/both-leg per-bar adjudications used the corrupted estimand (`critical-017.md`; superseded_status: REJECT_LEAK/NET_ADMIT per-bar reads). Corrected per-leg statuses: `python/experiments/VAL-006/analysis.md` §3. Single-leg (`none`) verdicts stand. |
| `CF-MR-004/HYP-004` | Does the exit-set matching the measured two-barrier object (TP@entry anchor, symmetric outward SL, ⌈3·HL⌉ time-stop; E0→E3 decomposition; reentry + z\* axes) extract the collapse-verified 4h availability on the prespecified primaries (JP225, EURUSD)? | EXP-014c | 0 | **COMPLETE 2026-07-03 — CREDIBLE_NEGATIVE_RETIRE (audit PASS, 0 Critical; raw-emission re-derivation).** Both primaries powered + bite-valid + net-fail (JP225 +0.26 ci −1.84; EURUSD +0.28 ci −0.46); 0 Holm admits in the binding family. Mechanism = **entry-seam mismatch**: limit-touch fill ≠ the measured confirmed-breach conditioning event (JP225 TP-share 0.52 vs p_inward 0.696); exits exonerated (frozen TP recovers the E0 loss engine, SL negative value, time-stop benign). Disclosure retained: 4 REJECT_LEAK extend/z15 cells (own-price; shift survives 50–85%); US2000 "collapse" = materiality-leg flip on a CI-positive shifted edge → no construction-specific claim (W3 collapse-fraction rule, KB lesson-candidate); **extend-arm field 61 cells net ci_low>0 (53 non-admitted), all extend/allow, year-stable 2021–24 → spun out to CF-MR-005**. **FAMILY RETIRED (operator D1, 2026-07-03).** 0 slots, 0 counted reads, holdout sealed, referee untuned. **⚠ MULTI-LEG DISCLOSURES SUPERSEDED_BY_VAL-006 (2026-07-04):** the 61-cell field, the 4 REJECT_LEAK extend/z15 cells, and the shift-survival fractions were computed on the corrupted per-bar estimand (`critical-017.md`). Corrected: 8 legitimate CI-positive cells (US2000 e0/e2 cluster + US500 both-leg), 44 e1 survivorship artifacts, no year stability, incoherent shift fractions — `python/experiments/VAL-006/analysis.md`. Single-leg primaries (the binding CREDIBLE_NEGATIVE) stand. |

**Family close-out (2026-07-03):** CF-MR-004 **RETIRED** on HYP-004's credible negative — the fourth
MR family closed at the capture/attribution seam (CF-MR-001/002/003 precedent). All outcomes
retained, never deleted. Re-opening requires a new entry object (confirmed-breach conditioning)
under a new D0.

## Chapter 02 · CF-MR-005 Registration (2026-07-03) — 4h Ladder Scale-In Own-Price MR Harvest

**Opened:** 2026-07-03 (operator decision D2 — EXP-014c disclosure spin-out). **Family:**
CF-MR-005 (`candidate-families/cf-mr-005.md`). **Slot accounting: 0 slots consumed at
registration; 0 counted TEST reads.** No experiments yet — Stage-1 design pending. Binding
first-branch constraints: mechanism characterisation first (operator D2/D3); basket-free trigger;
cost realism binding early (CF-MR-001/002/003 cost-vs-capture precedent; P-02 bars exit-stack
rescues); native availability definition (L-13 — the single-entry two-barrier race is the wrong
object for a multi-add ladder); attribution controls disclose collapse fractions (EXP-014c W3);
phase-shift-semantics study deferred behind characterisation (operator D3). Evidence base =
EXP-014b/014c extend-arm field disclosure (TRAIN-only; motivates registration, pre-admits nothing).

| Candidate ID | Hypothesis | EXP-ID | Slot | Status |
|---|---|---|---|---|
| `CF-MR-005/HYP-001` | Mechanism characterisation of the 4h ladder scale-in own-price MR harvest under a basket-free trigger (own-price `S = log P − Median₉₀`, z-depth bins): what reverts, at what depth/horizon (M1 recovery vs dislocation-matched control); depth gradient (M2); drift/vol/reversion attribution incl. per-level collapse fractions (M3, W3); left-tail census (M4); cost-stress disclosure (M5). Block-permuted-returns destroy binding (L-07). No tradability claim — HYP-002 gated on MECHANISM_SUPPORTED. | EXP-015 | 0 | **COMPLETE 2026-07-03 — NO_MECHANISM_EVIDENCE (audit PASS, 0 open Critical).** 0/11 cells MECHANISM_SUPPORTED: 10 powered bin-1 ΔR₂₄ CIs straddle 0 (US2000 significantly NEGATIVE −0.295 [−0.44,−0.007]); M2 depth-slope straddles 0 in 11/11; depth bins 2–4 structurally unpowered (max n=28 < 30 floor) — **event-mass mismatch**: own-price trigger fires ~30–60 de-clustered episodes/cell vs ~750 engine extend legs (the ladder cadence was the S8 basket construction's). L-07 permute null: no surviving edge (3/44 exceedances, all unpowered bins). Part-A anatomy: P&L scale-in-dependent (≥2-leg share med 0.68), heavy left tail, shift-collapse fractions heterogeneous (disclosed, L-15); M3b drift split design-degenerate (audit W2). **HYP-002 NOT admissible on the per-event read; retire recommendation SUPERSEDED by EXP-016 (per-event object only — L-16).** 0 slots, 0 counted reads, holdout sealed. `python/experiments/EXP-015/report.md`. |
| `CF-MR-005/TEST-001` | Operator-directed one-shot TEST persistence read: does the TRAIN-passing variant (e3/extend/z15, prespecified) retain net edge in the untouched TEST band (rows 49%→70%) on US2000/AUDUSD/NZDUSD-4h? | EXP-016 | 0 slots; **3 counted TEST reads** (ledger-entered pre-result; strata now 1/2) | **COMPLETE 2026-07-03 — PERFORMANCE_RETAINED (numerically, 3/3 cells; formal referee inapplicable — L-17).** TRAIN legs reproduce EXP-014c exactly (3.98/4.00/10.90). TEST net EXCEEDS TRAIN in all 3: US2000 **+11.83** (ci_low **+5.33**, boot_p 0.0001, 20 epi), NZDUSD +4.68 (ci_low +0.59, p 0.0064, Holm ✓), AUDUSD +5.50 (p 0.066, 5 epi). Referee UNPOWERED on all 3 — sole failing leg **L1_readiness** (effective_n 333 vs full-sample floor; bite plant fails the same leg ⇒ gate provably blind on a 1,110-bar band, its negative void) → **L-17**. Shift collapse fractions (disclosure): AUDUSD 0.94 / NZDUSD 1.06 (own-price OOS too) / US2000 0.56 (still mixed). **Consequence: EXP-015's retire recommendation WITHDRAWN — its per-event estimand could not see the multi-leg P&L object (L-16); family OPEN, mechanism question open; second (final) TEST read per stratum reserved for a repaired, predeclared short-band instrument.** Caveats: one 9-month window; tail population untested; AUDUSD individually n.s. Holdout sealed. `python/experiments/EXP-016/report.md`. **⚠ VOID — SPENT_ON_DEFECT (2026-07-04):** PERFORMANCE_RETAINED rests on the corrupted multi-leg per-bar estimand (`critical-017.md`); the 3 counted TEST reads stay spent (strata 1/2, NOT refunded) and support no retention claim; TRAIN side also has no valid edge (US2000 e3/extend/z15 per-leg CI [−15.9,+32.0] at zero cost — `VAL-006/analysis.md` P4). superseded_status: PERFORMANCE_RETAINED. |
| `CF-MR-005/HYP-002` | Episode-native mechanism probe (L-16-compliant): is episode P&L attributable to the scale-in structure (ladder vs paired passive same-window exposure, M2) and predictable from episode-START ≤t−1 information (M3, feature-label permutation null with collapse fractions), per stratum (US2000/AUDUSD/NZDUSD e3/extend/z15 primary)? No frozen-referee reads (L-17); TRAIN bands only (EXP-016 TEST rows excluded outright). | EXP-017 | 0 (0 counted reads) | **SCOPED 2026-07-03 — design gated (pre-exec GATE: APPROVE, `python/experiments/EXP-017/design.md`). ANALYSIS-ONLY** (episode reconstruction from existing emissions; passive comparator = labelled non-tradable price-path diagnostic). Frozen outcomes: MECHANISM_STATED / STRUCTURE_ONLY / EXPOSURE_VERDICT / UNPOWERED. In progress. **⚠ A1 Δ CORRUPTED (critical-017, 2026-07-04):** the episode net side consumed the defective per-bar series; any rerun must rebuild episodes via `xen.adjudication.build_episodes` (corrected base: `VAL-006/analysis.md`). |

| `CF-MR-005/HYP-003` | Deliberate ladder-harvest disposition probe of the VAL-006 residue: dislocation-conditioned, exposure-honest, regime-robust EPISODE economics in US2000 (A/extend, A/allow, B/extend) + US500 both-leg A, and NOT in the NZDUSD negative control; kill test = seeded random-timing matched-cadence/matched-hold ladder destroy; entry-delay +1 tripwire; 60h shift disclosure. Registered pre-execution 2026-07-04 (checkpoint-006 sanction, controlled thesis-shopping). | EXP-018 | 0 slots; 0 counted reads (TRAIN only) | **COMPLETE 2026-07-04 — NOT SUPPORTED (operator verdict; first full INFR-001 pass, QA APPROVE, estimand gate 1e-12).** Episode primary WASH ×4 residue cells (US500 both-leg well-powered zero −2.5 [−26,+24]; US2000 A/extend +381.9 [−122,+809] powered vs residue ~575); NZDUSD control passed (−273.6). Random-timing destroy unfalsified: US2000 collapse 0.49, diff CI straddles 0; **NZDUSD rt per-leg +31.5 CI_low +13.7 > 0 from pure random timing** (the residue's per-leg evidentiary form needs no signal). Surviving US2000 per-leg +36.8 CI_low +9.2 = 2022 long-drift carry (sole CI+ year; longs +72.7 vs shorts +7.2; top-5 episodes 82% of net; peak 43 legs, return on peak exposure ≈ B&H). Delay tripwire graceful. **Family RETIRED (checkpoint-006 retrospective, operator-signed).** `python/experiments/EXP-018/report.md`. |

## Chapter 02 · CF-VOLHARV-001 Registration (2026-07-04) — Two-Sided Oscillation/Volatility Harvest — RETIRED 2026-07-05

**Status:** **RETIRED 2026-07-05** (checkpoint-008 retrospective, operator-signed) — HYP-001
ARTIFACT_CONFIRMED + HYP-002 NOT SUPPORTED; both core hypotheses closed negative; 0 slots,
0 counted TEST reads, holdout sealed lifetime. A within-episode-clearing structure (rolling
anchor / no hard cap) on an unseen band is a NEW family (own D0), not a re-open (P-01/P-02).
**Opened:** 2026-07-04 (operator-directed; sanctioned route from checkpoint-006 retrospective —
"vol-harvest reframing"). **Family:** CF-VOLHARV-001 (`candidate-families/cf-volharv-001.md`).
**Slot accounting: 0 slots consumed at registration; 0 counted TEST reads.** Origin residues:
EXP-018 rt-arm anomaly (NZDUSD per-leg +31.5 CI_low +13.7 from pure random timing) +
CF-VOLEXP-001 tail hint (Chapter 01). **Falsification-first structure:** HYP-001 is a kill
test with an analytic null (fixed-unit random-dir random-timing fixed-hold legs have
E[gross]=0 by construction — "both sides positive" is impossible in expectation), NOT a
screen of a believed edge. Binding first-branch constraints: causal ex-ante construction
only (no borrowed live-arm templates/holds); 25 seeds × 16 instruments, engine-run; hold grid
{6,12,24,48} round-robin; inventory cap 6; swap/financing from a declared version-pinned
analysis-layer table (1× binding + 2× stress) — new `xen.evaluation` component precedes any
read; seed/episode-level inference; collapse fractions per L-15; TRAIN-only. HYP-002
(rebalanced-exposure / grid harvest — the actual family bet) is design-gated on HYP-001's
cost-floor + VR disclosures at the checkpoint. Kill criteria predeclared in the family card.

| Candidate ID | Hypothesis | EXP-ID | Slot | Status |
|---|---|---|---|---|
| `CF-VOLHARV-001/HYP-001` | Seed/fill falsification of the EXP-018 random-timing per-leg positive under fully ex-ante construction (16 instruments × 25 seeds × hold grid {6,12,24,48}, 4h TRAIN, fixed unit, cap 6): does any (instrument × hold) stratum show an across-seed mean gross ≥ MDE against the analytic E[gross]=0 null? Deliverables regardless: swap-inclusive carrying-cost floor per stratum (1×/2×) + VR/oscillation substrate profile (disclosures). Tripwires: schedule regeneration byte-diff (price-independence), fill-causality audit, NZDUSD +1-bar delay twin. Bands: ARTIFACT_CONFIRMED (expected) / PROCESS_ASYMMETRY (→ fill forensics, never booked as edge) / WASH / UNPOWERED. | EXP-019 | 0 (0 counted reads, TRAIN only) | **COMPLETED 2026-07-05 — SUPPORTED / ARTIFACT_CONFIRMED (operator verdict).** QA APPROVE; 441 runs; estimand gates blocking_pass (~1e-12 recon). NZDUSD battery ≈ 0 in all strata (|mean| < MDE 1.4–5.3 bps); +31.5 above the entire 25-seed distribution ([−11.5,+8.6]); 2/64 strata beyond MDE (≈ chance); direction splits drift-shaped; BTCUSD-48/EURUSD-12 WASH; BTCUSD H∈{12,24,48} UNPOWERED. Delay twin indistinguishable. COST_FLOOR booked (FTMO commissions; spread unpinned — design §12/A5 superseded swap) + VR substrate (FX-block MR, NZDUSD 0.80 @H24). `python/experiments/EXP-019/report.md`. |
| `CF-VOLHARV-001/HYP-002` | Structure-borne oscillation harvest (rebalanced-exposure / symmetric grid) net of double-sided spread + swap at capped inventory, vs unconditioned twin + exposure-matched two-sided B&H. | EXP-020 | 0 (0 counted reads, TRAIN only) | **COMPLETED 2026-07-05 — NOT SUPPORTED (operator verdict), USDCAD flagged.** QA APPROVE; 68 cells, estimand gates blocking_pass; +2 bps plant detected pre-read; tripwire-1 delay graceful. ARM R (rebalance premium vs never-rebalanced twin): 4/4 MR cells UNPOWERED (MDE > effect; §8 over-stated the classical w(1−w)σ² premium ~100×, true ~0.04–0.07%/yr); only US2000 (mid) CI-positive. ARM G (MR grid vs momentum twin, drift-robust spread): MR-block 1/4 — USDCAD +132 bps/mo CI[+43,+257] survives commission/weekend-×4/top-3/both-halves BUT fails inverted-twin sign-flip (momentum twin +3,491) + 2022=67%>60% cleanliness; NZDUSD −56, GBPUSD wash, AUDUSD −104. Realized RT = +g every cell (mechanism real) but rare: fills 5–28% of A1-implied cadence, 3/4 MR cap-locked, NZDUSD dead after 2022-04; censored ≤8-leg inventory erases 100–155% of realized (VAL-006). RW alarm scan clean. Robust to hardened block_bootstrap_ci re-run (INFR-004/L-20; 2 immaterial half flips). **Structure failure, not substrate absence — does NOT license "no harvest exists."** Net-at-live-spread BLOCKED (spread pin; EURJPY unpinned even at ceiling). Family disposition → checkpoint-008 retrospective (operator-signed). `python/experiments/EXP-020/report.md`. |

## Chapter 02 · CF-CSRR-001 Registration (2026-07-06) — Cross-Sectional Consensus-Residual Reversion (basket)

**Status:** **RETIRED — 2026-07-07 (operator-signed, checkpoint-009 retrospective).** Availability
kill criterion met on both baskets + the controlled USTEC re-test (EXP-021/022/024 all NOT
SUPPORTED); model-selection gate never met → HYP-003/EXP-023 + HYP-004 NOT SCOPED. 0 slots, 0
counted TEST reads, holdout sealed. Retrospective: `docs/experiments-docs/checkpoints/2026-07-06-009-cf-csrr-001-cross-sectional-residual-reversion/retrospective.md`.
Prior: REGISTERED — G0 PENDING (operator-directed 2026-07-06). **Family:** CF-CSRR-001
(`candidate-families/cf-csrr-001.md`; origin `docs/experiments-docs/families/cf-csrr-001/origin.md`).
**Governing checkpoint:** checkpoint-009
(`docs/experiments-docs/checkpoints/2026-07-06-009-cf-csrr-001-cross-sectional-residual-reversion/design.md`).
**Slot accounting: 0 slots consumed at registration; 0 counted TEST reads; holdout sealed.**
**Baskets:** Currencies (10, VAL-005, ready) + Indices (10; 4 loaded, **6 pending
INFR-005/VAL-007 — Indices arm blocked until VAL-007 PASS**). **Domain: 4h only.**

**Provenance:** MR-arc post-mortem (`verdict.md`) selected the cross-sectional/relative-value
cell of the availability 2×2 as the open frontier. Four suggested variants (r1-dlc S2, r4-tpg §2,
r4-tpg closing obs, r2-ksd I1) + one programme remodel (V5 active-entry/passive-exit) registered
so each of the 7 shared component axes (A consensus estimator · B normalization · C selection ·
D hedge · E entry execution · F exit/stop · G threshold) is characterised individually before one
model is constructed. Full faithful variant text: origin.md.

**Binding first-branch constraints (G0):** (1) causal anchor `r_i=ln(P_i/anchor_i)`, decisions on
confirmed 4h bars ≤ t-1, open-to-open; (2) consensus is a non-parametric cross-sectional statistic
(no beta/covariance/cointegration/rolling-z beyond axis-B σ); (3) **Currencies consensus built on a
USD-strength alignment**, not a naive quote median (operator 2026-07-06; the aligned residual's
mean-reversion is itself validated in EXP-021, naive-median is a disclosure-only contrast branch);
(4) tradability vehicle = V5 execution (active confirmed-breach entry, passive rolling-consensus
exit, time-only stop, single-worst + median-index 1:1 hedge, no hard cap); (5) mandatory three-twin
control battery (random-timing L-18/19, random-index, momentum-signed inverted / USDCAD lesson);
(6) TRAIN-only throughout this checkpoint; (7) exploratory + validatory scoped now (0 reads),
confirmatory HYP-004 pre-declared but NOT spent.

**Distinctness (P-01/P-02):** cross-sectional residual entry (not own-price directional →
distinct from CF-MR-002..005); reversion endpoint (not CF-XSECT-001's directional relative-
strength); entry-conditioned on a measured dislocation (not CF-VOLHARV-001's E[gross]=0
unconditioned object). Re-open standard met.

| Candidate ID | Hypothesis | EXP | Slot | Status |
|---|---|---|---|---|
| `CF-CSRR-001/HYP-001` | Currencies (USD-strength consensus) 4h TRAIN, execution-agnostic: is the consensus-residual mean-reverting (VR<1 / residual autocorr<0), and which (A×B×C×D) combination maximises signal-conditional residual-reversion Δ over a matched random-index + random-timing control (multiplicity-adjusted permuted-axis null at realized cell count)? | EXP-021 | 0 (0 counted reads, TRAIN only) | **SCREENED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Substrate MR confirmed (VR(2)<1 on 28/28 4h cells, HL~1.4; VR<1 on 1D). But **0 hedged (mechanism-faithful) cells survive the max-stat multiplicity** on any instrument; sole family-wise survivor AUDUSD *unhedged* +9.4 bps fw_p .008 = market drift (hedged twin fw_p .68). Heterogeneous (USDJPY continues, 0/16 cells+, dominates single-worst). Leak-clean, holdout sealed, 0 reads/slots. AUDUSD/USDCAD = disclosed leads (not booked). Family status unchanged (disposition → checkpoint-009 retrospective). `families/cf-csrr-001/INDEX.md`, `python/experiments/EXP-021/report.md`. |
| `CF-CSRR-001/HYP-002` | Indices basket mirror of HYP-001 on the native single-factor equity basket. | EXP-022 | 0 (0 counted reads, TRAIN only) | **SCREENED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Substrate MR confirmed (VR(2)<1 on 40/40 primary cells, HL ~0.8–1.9 4h-bars; 90% across builds). Signal-conditional **idiosyncratic (hedged) reversion does NOT separate** at primary (N×P): 0/74 powered cells clear uncorrected ci_low>0; max-stat over 16 cells → **0/9 instruments fw_p<0.05** (best JP225 0.33). Every primary cell UNPOWERED for the ≥1 bp band (MDE 3.9–21.7; `argmax\|s\|` concentrates events, §8 ~10× optimistic). 90%-coverage 4h filter culled EU50/HK50 to 0 events → effectively a US-cash sub-basket (EU/Asia UNPOWERED, not contradicted, B-5). **Addendum A1** (operator-directed, min_coverage 0.90→0.50) powered HK50 (0→519) = **clean null → US-cash NOT-SUPPORTED generalises**; EU50 structurally UNPOWERED (4h+1D). **USTEC (R_US bloc + session-open anchor, hedged) = disclosed member-specific lead** (+4.7–4.8 bps, p_perm .002, genuinely idiosyncratic α+4.71/raw+0.30/β1.19, siblings null, tripwire-clean; underpowered hardened ci_low<0, effect≈MDE, non-primary → registered-branch candidate, NOT support; parallels EXP-021 AUDUSD/USDCAD). Leak-clean, holdout sealed, 0 reads/slots. Family status unchanged (disposition → checkpoint-009 retrospective). `families/cf-csrr-001/INDEX.md`, `python/experiments/EXP-022/report.md`. |
| `CF-CSRR-001/HYP-002b` | US-bloc session-anchor availability primary (pre-registered follow-up to the EXP-022 USTEC disclosed lead). FROZEN single construction — R_US bloc {USTEC,US500,US2000,US30}, session-open anchor, A=median/B=raw/D=hedged, C=all>k (power), h=2·HL; multiplicity family = the 4 members (Holm); BINDING bar = the hardened block-bootstrap CI USTEC FAILED in EXP-022 (ci_low −0.58, effect≈MDE 5.28) — NOT the permutation-only read. Resolves (a) does power push ci_low>0 or dilute to MDE, and (b) real bloc mechanism vs USTEC-only artifact (siblings hinted null). Controlled thesis-shopping from a disclosed lead — pre-registered, TRAIN-only, in-sample-honest (a pass only graduates USTEC to EXP-023, NOT confirmatory). New construction branch, multiplicity rule 4. | EXP-024 | 0 (0 counted reads, TRAIN only) | **COMPLETED — NOT SUPPORTED (availability; operator verdict 2026-07-06).** Controlled re-test of the EXP-022 USTEC lead. Substrate reverts; no member clears the hardened CI at the binding all>k/hedged construction (all powered UNPOWERED-by-MDE; §8 dilution confirmed — all>k dilutes the per-event effect from single-worst +4.26 → +1.08 bps to the MDE). Single-worst continuity reproduces EXP-022's USTEC pattern (p_perm 0.009 but hardened ci_low −1.15) — lead is effect-at-MDE, USTEC-specific, retired at 0 cost; no sibling reproduces. Read-out does NOT graduate USTEC to EXP-023. 0 counted TEST reads, 0 slots (TRAIN-only). Family status UNCHANGED — disposition → checkpoint-009 retrospective. `python/experiments/EXP-024/report.md` |
| `CF-CSRR-001/HYP-004` | Confirmatory single counted TEST read of the frozen, hash-pinned selected model per stratum (cap 2/stratum). | — | pre-declared; **0 reads (NOT spent)** | **NEVER SCOPED — family RETIRED 2026-07-07 (checkpoint-009 retrospective).** Model-selection gate never met → EXP-023 not run → confirmatory gate never reached. 0 reads, holdout sealed. |

**Registered non-baseline / deferred branches (countable, no slot until activated):** naive-median
Currencies consensus (contrast); weekly-anchor variant (timezone-sidestep, r1-dlc note); regional
sub-basket clustering (Asia/Europe/US, r3-mlg); vol-expansion-armed trigger (V-source r3-mlg S2,
treads CF-VOLEXP-001 — deferred); two-flanking-index half-notional hedge (r1-dlc). Each needs a
dated `D0-amendment-*` stating whether it consumes a new slot.

**Predeclared kill criteria (checkpoint-level):** family card §Kill criteria — substrate not MR /
no combination separates from both twins / momentum-twin matches any positive (drift-carry) /
capture < honest round-trip on every stratum / any integrity tripwire → REJECT+fix+rerun.

## Chapter 02 · Phase 010 Batch (CF-HTFDI-001 Higher-Timeframe DI Conditioning) — **RETIRED (2026-07-09, operator-signed, checkpoint-010/011 retrospective)**; promoted from the SPDR CTRL-01/02/03 series; CORRECTED 2026-07-08 (single thread)

**Retired:** 2026-07-09 — EXP-025 HYP-A NOT SUPPORTED (magnitude, not existence; powered
negative, 0/440 qualifiers). T2 exit tier + counted TEST reads NOT SCOPED / never spent
(0 reads, 0 slots). Retrospective:
`docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/retrospective.md`.
**Opened:** 2026-07-08. **Family:** CF-HTFDI-001 (`candidate-families/cf-htfdi-001.md`).
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/`
(binding **corrected** `synthesis.md`; audit + correction probe in `correction/`; origin
`origin-mtf.md`). **Slot accounting: 0 candidate slots consumed, 0 counted TEST reads** — the
promoting evidence is the SPDR speed-run screen (TRAIN-only, no engine, no estimand gate, no
read). Holdout sealed. **SPDR legs are NOT experiment slots** (lane spec): the screen legs
`SPDR-001/002/003` remain indexed in `python/experiments/INDEX.md`; they registered no family and
spent no read.

**Correction (2026-07-08, same day as registration):** independent audit found (1) SPDR-001 CIs
under-blocked (block=5 vs dependence ≈ H on the overlapping per-bar estimand) and (2) the SPDR-003
fade cell computed on the side-signed strategy × DI interaction, not the labelled raw-move
conditioning. Under corrected statistics no fade-signed cell is CI-clear anywhere; **HYP-B was
WITHDRAWN — NOT SUPPORTED**; EURUSD 1d/1h demoted from HYP-A anchor to power-up stratum. Affected
artifacts rewritten in place.

**Multiplicity disclosure (screen):** 960 cells/leg × 3 legs (4 instruments × 3 domain-pairs ×
4 holds × 20 filter variants). Per-stratum reads only; the graduation experiment carries a
pre-registered **per-instrument family-wise max-stat over holds** as the honest multiplicity test.

| Candidate ID | Thread / role | EXP-ID | Slot | Status |
|---|---|---|---|---|
| `CF-HTFDI-001/HYP-A` | **Thread A (sole thread) — HTF-DI continuation**: net-of-cost directional edge on USTEC 1h/5min (secondary: EURUSD 1d/1h power-up stratum), vol-regime **amplifier** measured, vs matched random battery | **EXP-025** (design 2026-07-08, `python/experiments/EXP-025/design.md`) | 0 | **EXP-025 COMPLETE 2026-07-09 — NOT SUPPORTED (magnitude, not existence; operator verdict).** T1-terminal powered negative: 0/440 SEL-NEIGHBOR qualifiers (rule 1 universal fail), 0 counted TEST reads spent, MDE ≤5.2 bps all cells. Reconciled: the design's "30–60 bps" target was a 4.1× ATR-units artifact (1h divisor asserted vs the screen's 5min LTF ATR(14)[t−1]); the channel is REAL and replicates screen→ref-arm→battery at ≈4 bps/trade h48 (~1–3 bps after capture dilution) — below FX commission, ~1/10 of the selection bar on indices; index positives drift-shaped, no DI dose-response. External reviews confirmed → KB L-21..L-24. Family status transition reserved for the checkpoint retrospective. `python/experiments/EXP-025/report.md`. *(Prior registration evidence:)* Corrected SPDR evidence: USTEC 1h/5min dir_gap +0.09→+0.50 ATR, CI-clear at all four holds under hold-matched blocks (random base) **and** CI-clear +0.26→+0.39 at H24–48 on the blind momentum base (non-overlapping trades); corrected breadth 9+/0− of 84 DI-axis cells; survives mis-aligned-HTF + phase-shift controls. |
| `CF-HTFDI-001/HYP-B` | ~~Thread B — HTF-DI fade (XAUUSD)~~ | — | 0 | **WITHDRAWN — NOT SUPPORTED (correction 2026-07-08).** All pillars failed re-derivation: 17/23 negative breadth → 4+/3− at block=H (under-blocking artifact); the −0.86 cell was the side-signed interaction (raw-move −0.083 [−0.68,+0.53] n.s., both half-splits n.s.); EUR-intraday & BTC-daily fade cells not CI-clear. Revival requires new pre-registered CI-clear negative dir_gap on the raw-move estimand with dependence-matched blocks. |

**Scope amendment (2026-07-08, operator-directed, pre-measurement):** HYP-A graduation scope fixed
in the family card §Phase 011 graduation scope — CTRL-02 breakout vehicle + DI confirm; full
22-symbol universe; 1h/5min only; variants `di` + 3 ATR×DI (ADX axis dropped); hyperparameters =
breakout lookback X + exit method (6-candidate set vs fixed-hold benchmark, capping exits measure
erosion); neighbour-stability selection (`SEL-NEIGHBOR`, to be registered before measurement);
`WF-EXPANDING` with optimisation inside TRAIN and TEST as counted confirmation reads under
per-instrument max-stat + Holm; sign prior USTEC-continuation only, all else two-sided. No slot or
read consumed by this amendment.

**EXP-025 design registration (2026-07-08, pre-measurement):** `SEL-NEIGHBOR` promoted from
`components/global-techniques.md` (plateau selection: own-cell clear + ±1-step neighbourhood
median clear + fold-sign persistence; contradicted neighbours are disclosure-only, not a
disqualifier — hostile-neighbour hard veto removed as outlier-fragile, amended 2026-07-08
pre-measurement, operator-directed; TRAIN-only, mechanical).
TRAIN plane disclosed: 22 instruments × X {2,3,4,5,8} × H {12,24,36,48} × 4 variant-strata =
4,400 conditioning cells + ≤60 exit cells (6-exit set vs fixed-hold benchmark) — all
selection-side, uncounted. **Counted-TEST pre-commitment: ≤5 counted reads** (1/instrument,
eligibility = SEL-NEIGHBOR (contains the CI_low>0 gate) + candidate > battery mean by ≥2
seed-SD (distributional read; replaced the ≥97.5-pct order statistic, amended 2026-07-08
pre-measurement) + projected TEST n≥50 + estimand gate + operator approval; Holm α=0.05 over instruments read; USTEC one-sided, rest
two-sided; overflow qualifies-unread → file-drawer). Controls pre-registered with seeds:
25-seed battery 1001–1025, random-entry reference arm 2001, ADX-only null sentinel (judged
family-wise, breach count vs binomial expectation); tripwire = +60-bar HTF phase-shift with a
pooled quantified REJECT criterion (pooled shifted effect >50% of raw, CI excluding ≤25%;
per-cell survivors disclosure-only — amended 2026-07-08 pre-measurement after independent
fragility review; MDE plant at 2× MDE). 0 slots, 0 reads at design.

**Controls (apparatus, NOT candidates — carried from the SPDR legs):** 25-seed matched-cadence
random battery (availability benchmark, Control-B role, costs modeled); random-entry reference arm
(re-measures the conditioning effect on TEST without base confound); ≥1 null sentinel (symmetric-sign
ADX/ATR-only gating, behaved null on TRAIN). All declared as named controls with pre-registered
seeds in the design doc (QA: no undeclared TEST-touching arm).

**Recorded NOT SUPPORTED (screen, corrected):** universal "HTF improves LTF" thesis; ATR as a
*direct* dispersion signal (~1.5× normaliser artifact; retained only as the amplifier
interaction); ATR as a sign-setter (low-vol branch not CI-clear); 4h/1h domain; BTC 1h/5min
continuation as an HTF-specific thread (shared with LTF autocorrelation); **XAUUSD fade thread
(withdrawn at the correction)**.
**Deferred design hypothesis (one-leg 002):** ADX conditions dispersion more cleanly than ATR.
**Separate exploration log line (NOT this family, not opened):** tail-managed naive base (both
informative bases median-positive / tail-killed).

**Binding design constraints (family card §Design constraints, corrected):** vol-regime
interaction measured as an AMPLIFIER hypothesis (high-vol amplifies; "ATR sets the sign" is not
carried); uncapped/horizon exits (or measured TP erosion); per-instrument max-stat over holds;
raw-bps/fixed-ATR for any dispersion claim; USTEC-continuation sign fixed a priori from TRAIN (no
other sign priors); dependence-matched uncertainty (block ≥ H on overlapping estimands).
**HTF-bar-boundary** (`CloseTime < Open(t)`) is the load-bearing leak guard, code-asserted +
golden-trace.

## Chapter 04 · VAL-008 Registration (2026-07-16) — INFR-010 Phase D Pipeline Dry Run (apparatus, throwaway)

**Status:** **COMPLETE 2026-07-16 — operator verdict SUPPORTED / Phase D PASS** (apparatus
test — NOT a candidate family; informative-only disposition). Gate 39/39 PASS on PINNED
attestation; planted leak caught 3/3 blind (BASELINE clear 0/3); destroys collapse
0.977–1.064; STUB negative correctly fails. Report: `python/experiments/VAL-008/report.md`.
**Vehicle:** SMA(20/100) 1m cross flip on BTCUSDT/ETHUSDT/SOLUSDT (Bybit USDT perps, new
Nautilus stack), TRAIN sub-window 2023-06-01 → train_end 2023-12-18. Purpose: end-to-end
pipeline integrity (INFR-010 §6 Phase D) — emission contract v1 on PINNED fence attestation,
estimand gate v2, leak battery (planted next-bar-sign oracle = bite plant; block-shuffle ×5
seeds 1000–1004/2000–2004 + causalizing lag must collapse it; predeclared blind leak-catch
protocol). Amendments 1–4 (2026-07-16, all NEUTRAL): gate invocation wrapper, seed labels,
overlap wording, shuffle→derangement control repair (L-10 amend-in-place, contaminated SHUF
emissions hard-deleted + rerun) — see design.md §Amendment ledger.
**Slot accounting: 0 slots; 0 counted TEST reads; TRAIN-only; holdout sealed.** No family
opened; no tradability claim permitted from any VAL-008 read. Design:
`python/experiments/VAL-008/design.md`.

## Chapter 04 · CF-HTFCAP-001 Registration (2026-07-16, checkpoint-013) — HTF Context × Capture Scale

**Status:** **REGISTERED 2026-07-16** (checkpoint-013 D2, operator-signed) — registration
act only, no status transition. D0 card: `candidate-families/cf-htfcap-001.md`; SPDR pack:
`docs/references/spdr-pack-htfcap-001.md`; frozen decisions:
`candidate-families/proposal-ref-ab-open-questions.md`.
**Route:** SPDR-004 → full XENA (XENA-HTFCAP-001) if `WORTH_EXPLORING`; **EXP lane not
used.** Mechanism class: conditioning/context filters on LTF bases + hold-scale capture.
**Universe:** 10 Bybit USDT linear perps via **online instrument selection rule** (default:
highest trailing 24h volume at each configured rebalance/asset-reset point; selection at t
uses volume ≤ t−1 only; no fixed pre-run ticker list — rule + frequency are the frozen
declarations). Anti-survivorship binds project-wide; at SPDR the currently-most-liquid 10
are acceptable (justification, not characterisation — operator D3 rationale 2026-07-16);
at XENA the point-in-time universe includes delisted symbols.
**Promote rule (SPDR pack §6 normative):** cluster K≥3 on primary bps lift vs matched
baselines (unfiltered + naive momentum + random-sign control), neighbourhood rule,
TRAIN-only, dependence-honest uncertainty. Hold axis must include 2× and 4× HTF-span holds.
Funding: disclose @ SPDR, bind @ XENA.
**Hard bans (card §4):** non-causal HTF/LTF; unit lies (L-21 pin at every seam); costless
net-edge claims / cadence-max on filter theses (L-26); passive-limit edge without
decomposition (P-10); SPDR as tradability; chapter-03 XENA registry pins on Bybit without
fresh CAL (INFR-010 R4 — INFR-014); single-lottery-cell family wins.
**XENA gate:** blocked until INFR-014 fresh CAL hash-pin exists.
**Slot accounting: 0 slots; 0 counted TEST reads; TRAIN-only; holdout sealed.** No
tradability claim permitted from any SPDR read.
**SPDR-004 design freeze (2026-07-16):** `python/experiments/SPDR-004/design.md` COMPLETE —
rebalance frequency frozen **daily 00:00 UTC**; online top-10 trailing 24h volume ≤ t−1;
thin grid 1h/5m·4h/15m·1d/1h × holds {0.5,1,2,4}× × bases {UNF,MOM,RAND} × HTF {NONE,DI,DI_ADX};
promote K=3; L-21 unit pin at screen; P-14 distinctness recorded; screen **uncounted**, not run.
AMENDMENT-1 (2026-07-16, NEUTRAL, pre-execution): UNF×filter baseline = RAND battery at UNF
cadence (UNF×NONE undefined — no intrinsic sign). AMENDMENTS 2–5 (2026-07-16, post-exec QA
runs 1–2; ledger in design.md): notional-volume selection (N, rerun), fixed-strata declaration
(N), two-sample lift CI (T), UNF-vs-battery both-arms bootstrap (T) — final count 0L/2T/3N.
**SPDR-004 DISPOSITION (2026-07-17, operator-signed): WORTH_EXPLORING** — K=3 met on
SOLUSDT × 4h/15m × UNF × DI_ADX × all 4 holds (monotone money-unit hold ladder 5.9→50.1
bps/trade, lift ci_low>0 each rung, battery rank 1.00, Control C collapse ≈1.0, h2/h4 clear
floors). Caveats binding on XENA-HTFCAP-001 design: single-symbol cluster (cross-symbol
neighbourhood fails; generalisation = XENA's question); rest of grid P-14-shaped sub-floor;
GAP spread overstated floors (measured pins from SPDR-006 on); 1d domain unpowered; no
tradability claim; XENA gate still blocked on INFR-014 pin. 0 slots, 0 reads consumed.
**SPDR-006 facet screen registered (2026-07-17):** vol-regime axis (VOL_HI/VOL_LO standalone +
DI×VOL_HI + DI_ADX×VOL_HI amplifier variants; pack's optional vol axis, cut from SPDR-004 for
budget) — SEPARATE grid + own K=3 (avoids post-results expansion of SPDR-004, L-23); DI-only
variants NOT re-run (SPDR-004 cells frozen as reference); 1440 cells; 0 slots, uncounted,
TRAIN-only; `python/experiments/SPDR-006/design.md`; screen not run.
**SPDR-006 DISPOSITION (2026-07-17, operator-signed): WORTH_EXPLORING** — K=3 met on 4h/15m
UNF interaction clusters: DI×VOL_HI (BTC+SOL, all 4 holds, med lift +26.6 bps) and
DI_ADX×VOL_HI (BTC full ladder + SOL h1–h4, med +28.5); monotone capture-scale ladders;
measured-spread floors cleared at h1+; amplifier claim vs frozen SPDR-004 holds (160/164
powered CI+ interaction cells above direction-only; BTC frozen DI CI-fail → full 4-hold CI+
under VOL_HI gating). Caveats binding on XENA-HTFCAP-001 design: interaction filters only
(standalone VOL_HI/VOL_LO weak/drift-contaminated); multi-name = BTC+SOL exactly (drop-both
probe kills K≥3; ETH = one seed-fragile cell); holds ≥1× HTF for money; SOL Control C
collapse incomplete (0.55–0.78); no per-year split; availability-only, XENA gate still
blocked on INFR-014 pin. Integrity 14/14; independent review pass reproduced all headline
numbers. 0 slots, 0 reads consumed.
**XENA-HTFCAP-001 OUTCOME (2026-07-19, operator verdict): EXPLORATORY — real sub-cost gross
edge, NOT deployable.** Analysis re-done under INFR-016 report layers. A real, gate-attributable,
sign-null-clearing GROSS edge exists on BTC mid-threshold `DI_ADX×VOL_HI adx25` H32/H64
(embargoed gross LCB +8 to +18, sign p 0.02–0.05, derangement collapse ~0.9) — hidden by the
old top-1 gate framing. **Net-of-cost: 0 of 72 cells and 0 subsets resolve above zero**
(~18 bps taker+GAP+funding wall at 8–16h holds; best net LCB −4.6). Binder certified top-1 was a
selection artifact (worst corner); SOL v1.5/adxna/H64 full-window-suggestive but embargoed-band
negative. Run was operator-authorized EXPLORATORY (TRAIN+TEST, **no reserved OOS** — AMENDMENT-4/5)
→ **1 TEST-band read spent (candidate slot 1/2)**; global holdout SEALED (self-test PASS).
Estimand gate v2 PASS 108/108. Not a certification, not deployability. Item RETAINED (not deleted).
Report `python/experiments/XENA-HTFCAP-001/report.md`. **Family status transition deferred to
checkpoint-013 retrospective (operator-signed).**

## Chapter 04 · CF-EPSOSC-001 Registration (2026-07-16, checkpoint-013) — Episode-Clearing Oscillation Harvest

**Status:** **REGISTERED 2026-07-16** (checkpoint-013 D2, operator-signed) — registration
act only, no status transition. D0 card: `candidate-families/cf-epsosc-001.md`; SPDR pack:
`docs/references/spdr-pack-epsosc-001.md`; frozen decisions:
`candidate-families/proposal-ref-ab-open-questions.md`.
**Route:** SPDR-005 → full XENA (XENA-EPSOSC-001) if `WORTH_EXPLORING`; **EXP lane not
used.** Mechanism class: episode-native path / oscillation harvest (structure search).
Parallel to CF-HTFCAP-001, separate packs/universes (Q3).
**Universe:** same online selection rule as CF-HTFCAP-001 (10 assets, trailing 24h volume,
≤ t−1 causal, rule + rebalance frequency frozen — no fixed list; D3/D5 as above).
**Promote rule (SPDR pack §6 normative):** cluster K≥3 on bps/episode (or declared
equivalent) vs matched random-timing / shuffled-episode controls; neighbourhood rule; not
banned-grid-like. Episode objects at SPDR: (1) stretch-from-rolling-anchor fade,
(2) vol-expansion arm → fade. One-sided required; two-sided ≤25% of cells. VR diagnostic
parallel facet, not a sole hard-gate. Funding: disclose @ SPDR, bind @ XENA.
**Hard bans (card §4):** non-causal construction; unit lies / local accounting; costless
net-edge theater; passive fill as free alpha without decomposition; **identical P-12 grid
object (banded rebalance + hard inventory cap symmetric grid) out of family**; SPDR as
deployability; void registry on Bybit without fresh CAL; single-lottery-cell promotes.
**XENA gate:** blocked until INFR-014 fresh CAL hash-pin exists.
**Slot accounting: 0 slots; 0 counted TEST reads; TRAIN-only; holdout sealed.** No
tradability claim permitted from any SPDR read.
**SPDR-005 design freeze (2026-07-16):** `python/experiments/SPDR-005/design.md` COMPLETE —
daily 00:00 UTC online top-10; objects STRETCH+VOLARM **market-on-confirmed-event only**
(0 resting-limit cells; P-10); P-12 dead grid banned + optional GRID_TWIN sentinel; primary
promote slice 15m/1h × W{96,192} × k{2.5,3.0} × clear{RET_ANCHOR,HYBRID} × one-sided;
L-16 bps/episode primary; L-21 unit pin; L-27 next-open control **forwarded to INFR-014**
battery if any limit-entry universe; VR parallel facet; screen **uncounted**, not run.
AMENDMENT-1 (2026-07-16, NEUTRAL, pre-execution): RET_ANCHOR episodes open at train_end =
CENSORED (excluded from mean bps/episode, fraction disclosed per cell, >20% flagged; silent
drop banned).
AMENDMENTS 2–3 (2026-07-17, post-exec QA run 1, operator-ratified): fixed top-10 strata by
full-TRAIN membership-days (LOOSER — hindsight universe reduction, caveat binding) + Control A
seed tiering 25 primary / 5 disclosure (NEUTRAL-promote/LOOSER-disclosure). Ledger 1L/0T/2N.
**SPDR-005 DISPOSITION (2026-07-17, operator-signed): WORTH_EXPLORING** — K≥3 clusters on
primary slice, strongest VOLARM×15m (23–25 cells, 4 symbols, both k & W, med lift +54–60
bps/episode, derangement collapse ≈0.95, block_h sign-stable 204/205); VR facet not flat
(half-symbol rule met all lags); GRID_TWIN not sole positive; cluster medians clear measured
spread floors. Counterweights carried: primary pooled median NEGATIVE (−11.4 mean / −9.2
lift); edge alt-concentrated (SHIB/XRP/DOGE/JASMY); 1h broadly negative; fixed-strata
hindsight selection (AMENDMENT-2); ~17-month effective window (membership starts 2022-07-15).
Caveats binding on XENA-EPSOSC-001 design: seed from VOLARM×15m×{RET_ANCHOR,HYBRID}×
k{2.5,3.0}×W{96,192} on cleared high-volume names; L-27 next-open control mandatory for any
limit-entry universe; no BONK/BTT centring; availability-only, XENA gate blocked on INFR-014
pin. 0 slots, 0 reads consumed. Disposition: `python/experiments/SPDR-005/analysis.md` §9.

**Evidence (2026-07-18) — XENA-EPSOSC-002 NOT SUPPORTED (refuted), 0 slots / 0 counted reads.**
Mass-aligned RET_ANCHOR cross-symbol redesign. Certified 4-symbol subset fails stage-2 gross LCB
(−68.2) and derangement tripwire (raw collapse 0.091, drift-adjusted 0.135); residual gross is
AKRO-concentrated unconditional drift (001 pedestal reproduced). Family status unchanged
(checkpoint-level). Report: `python/experiments/XENA-EPSOSC-002/report.md`.

## Chapter 04 · CF-SIGAUC-001 Registration (2026-07-20, checkpoint-014) — Signed Auction Structure

**Status:** **REGISTERED 2026-07-20** (checkpoint-014 D1, operator-signed) — registration act
only, no status transition. D1–D6 all signed; source-adherence resolutions (6 items) signed.
D0 card: `candidate-families/cf-sigauc-001.md`; checkpoint:
`docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/design.md`;
source methodology: `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` (normative for signal
definitions, falsifiers, phase order).
**Route:** INFR-017 ✅ (signed-bar lane) → INFR-018 ✅ (instrument build + freeze; registry
`pin_sha256 5c386984…`, 2026-07-21) → **SPDR-007** (statistical spine, master go/no-go) →
SPDR-008 (breadth sweep) → full XENA at checkpoint-015 if the spine holds. **EXP lane not used.** Mechanism class: sparse
session-anchored auction events (breakout / trap / acceptance) + located signed-flow triggers.
**Information source:** 1m OHLCV **+ exact taker buy/sell volume** (Δ = BuyVolume − SellVolume)
+ per-bar spread proxy + calendar. Verified on disk 2026-07-20 at
`python/experiments/INFR-011/data/staging/bars/*.parquet` (904 symbols; `Buy+Sell ≡ Volume`
to max rel dev 3.8e-16 on BTC/ETH/SOL, 0 nulls; `NTrades` present; `SpreadBps` has nulls —
TRAIN band: BTC 158 / ETH 4,543 / SOL 6,951 null minutes). **Not engine-readable** — catalog `Bar` is OHLCV
only; INFR-017 builds the signed catalog lane on `xen.orderflow` contracts.
**Universe:** online instrument selection rule (highest trailing 24h volume, selection at t
uses volume ≤ t−1 only, daily 00:00 UTC re-evaluation, tie-break lexicographic; rule +
frequency are the frozen declarations, no fixed pre-run list). **n = 20** for INFR-018
calibration and SPDR-007 spine (pooled anchor race needs cross-sectional support);
**the 296 admitted instruments with readable TRAIN data**, point-in-time, delisted included, for
SPDR-008 breadth (ckpt-014 AMENDMENT-1, operator-signed 2026-07-20, direction NEUTRAL; measured at
INFR-017 W7 → `admission_reconciliation.json.band_coverage`: 894 admitted / 296 with TRAIN data /
197 reaching the DESIGN bank). The n=20 calibration and spine sets draw from the 197.
**Survivorship caveat BINDING on every breadth read** — the covered set is precisely the instruments
listed before the bank end, so it describes older listings, not the venue as a whole.
Anti-survivorship binds project-wide.
**Band mapping (checkpoint-014 §5, declared deviation):** the source's per-phase "strict
holdout" maps to a TRAIN-internal **CONFIRM bank** — DESIGN `2021-06-29T06:53:00Z →
2023-03-01T00:00:00Z`, CONFIRM `2023-03-01T00:00:00Z → 2023-12-18T00:00:00Z`, untouched
during each phase's tuning. Stage I confirmations are TRAIN-internal and must be labelled as
such — they are NOT out-of-sample in the programme's sense. The TEST band is **reserved** for
a single counted XENA gate at checkpoint-015; global holdout never queried.
**Promote rule (SPDR-008, predeclared in its design.md):** cluster **K = 3** — ≥3 cells in a
connected grid region (same anchor family and signal, varying symbol and/or hold) positive vs
matched unconditional baselines on the primary bps facet, dependence-honest uncertainty;
best cell not the only positive in its neighbourhood; cluster median gross bps reported
against the measured cost floor.
**Money-unit floor (binding, computed BEFORE the Phase-4 disposition):** taker RT 11.0 bps +
measured per-symbol spread RT + funding ≤ ~3 bps at ≤24h session holds (`xen.evaluation`).
TP1 at/below floor ⇒ characterisation only, never a tradability route (L-21 / P-15).
**Hard bans (card §4):** non-causal construction (closed windows; ≤ t−1; entry at signal-bar
close earliest); **per-level signed attribution** (per-BAR Δ exact, per-LEVEL Δ estimate-grade —
barred by the source itself); sub-minute ordering (S15 sequencing is bar-level only);
**P-10 passive-limit ban OVERRIDDEN for this family** (operator 2026-07-20) — source S13(a)/M3
limit-style entries admitted; when a cell claims a passive-limit fill it must also emit the
market-on-confirm twin and/or L-27 next-open control (dual capture for comparison, not a veto);
unit lies across seams (L-21); costless net-edge claims / cost not binding selection (L-26, L-22);
screen as tradability; **re-parameterising a refuted mechanism** (source mechanism doctrine —
mechanisms are binary, grades are not); Stage II results on unfrozen Stage I instruments
(unattributable, re-run); single-lottery-cell family wins.
**Anchor method:** primary = pooled/hierarchical across the cross-section; mandatory few-asset
per-instrument spot-check (default BTC/ETH/SOL) to flag major pooled-vs-local divergence before
freeze. **Kernel (Phase 3):** calibrate against a finer-grained reference when available, else
explicit SKIP-NO-REFERENCE — no silent uncalibrated freeze.
**Distinctness:** **P-07 CLEARED and is the family's principal warrant** — exchange-native taker
aggressor volume is not broker-reported tick volume; it is the first non-price-derived
information source the programme has held, the class the KB terminal-branch statement names as
the remaining frontier. **P-01 tight, operator sign-off required (checkpoint-014 D6)** — the
S1/S2 spine uses no volume and is single-instrument directional; distinctness rests on the
calendar-anchored participation-window object, an excursion-quantile target, and
availability-first screening against matched unconditional base rates, with Phase 4 scoped so it
cannot itself promote the family. **P-10 overridden** (source passive-limit + dual capture).
P-12 not in family (no grid object). P-14/P-15 addressed by the money floor + unit pin.
**Experiment plan fidelity:** source Appendix B phase order and claims preserved; Xen lanes
(INFR→SPDR→XENA) are packaging only — Phase 6 kill-order and Phase 7 M1–M5 assembly (M5 last)
must not be reordered at checkpoint-015.
**XENA gate:** blocked — the active pin `abbb1842…` (CLS-FILTER low + CLS-EPISODE low)
establishes neither class for sparse session-event objects; a CAL leg shaped to this class is a
**checkpoint-015 prerequisite**, not a checkpoint-014 blocker.
**Slot accounting: 0 slots; 0 counted TEST reads; TRAIN-only; holdout sealed.** No tradability
claim permitted from any INFR or SPDR read in this checkpoint.

**Disposition — SPDR-007 (2026-07-21, uncounted screen; HYP-S1 master gate).** Operator
**NOT_WORTH** for the **price-only S1/S2 spine** — a P-01 confirmation. The Protection quantile
reproduces on the CONFIRM bank (pooled calib_err +0.030/+0.028; source falsifier #1 not
triggered on reproduction) but adds ≈0 over a matched cross-session unconditional entry: R2 race
contrast −0.010 at gross breakeven, below cost-adjusted breakeven on all 5 majors (w−p0ᶜ −0.05
to −0.14); R5 excursion-asym contrast +0.090 CI [−0.23,+0.32] WASH. Integrity clean (tripwire
NO_MATERIAL_EDGE, bite 0.77). **Signed flow (Δ) UNTESTED — the family warrant is deferred to
ckpt-015; only the daily US-open session / 15-min IB / single-session hold on 1-min bars was
exercised (not the 8h funding cadence, not micro/structural holds, no higher-timeframe
resampling).** Two developer deviations ratified (D-1 cross-session control; D-2 material-edge
tripwire). **No family status change** — retrospective act. Next: **SPDR-008** (S1+S3 signed-trap
breadth). Report `python/experiments/SPDR-007/report.md`.

**Disposition — SPDR-008 (2026-07-21, uncounted screen; S3 signed-trap breadth, the deferred SIGNED
warrant).** Operator **NOT_WORTH**. Measured trap-load monotonicity (`trap_load = poke_side × Σ
delta_ratio_resid`) is a **powered null** on all three boundary types tested INDEPENDENTLY (IB /
prior value-area / prior extreme): T1 ρ −0.015/+0.023/−0.033, MDE ≈0.02 on 4.6–10.9k events/cell;
the sole whiff (PVA DESIGN p=0.052) is below its own MDE and flips negative on CONFIRM; T2 HIGH−LOW
tier CI spans zero on every boundary/band. **Multiplicity (K=3) ruled NOISE:** across 241 powered
per-cell derangement gates, 7 pass the positive signed gate vs **6.0 expected under the null** and
vs **10 passing the anti-monotone mirror** — the positive tail is not enriched; IB's 6/96 are
scattered non-connected names with sign-only (winner's-curse) CONFIRM reproduction atop a negative
pooled IB ρ. Only reproducing edge = **unsigned P-01 geometry** (T4/T3 availability ~30–55 bps on
PVA/PRIOR, not load-dependent; the failed-break pattern already NOT_WORTH at SPDR-007) → measured
flow adds nothing over price shape; recorded as market-science characterisation, not tradability.
Integrity clean (causal ≤t−1 on all 16,669 events; tripwire NO_MATERIAL_EDGE with bite 0.53–0.92;
no-per-level-Δ + no-local-accounting + frozen-pin PASS; emission VALID). 194 A5-fitted signed
universe (breadth denom 296, survivorship binding), 16,669/26,348 traps. Amendments 1–8 (0L/5T/3N);
QA runs 1–3. **Signed-value block (S9 absorption / S14 CVD divergence) is a distinct claim
(ckpt-015 Phase 6) — not pre-judged.** **No family status change** — retrospective act. **0 counted
reads; holdout SEALED.** Report `python/experiments/SPDR-008/report.md`.

## Chapter 05 — CF-VOLCONV-001 (registered 2026-07-22)

**Checkpoint:** `2026-07-22-016-volatility-direction-conversion`
**Route:** one TRAIN-only `SPDR-011` artifact with five ordered report layers; conditional frozen-rule
`EXP-099`. No XENA, TEST or holdout. 0 counted reads.

| ID | Vehicle | Registered question / arm | Candidate slot | Status |
|---|---|---|---:|---|
| `CF-VOLCONV-001/HYP-001` | SPDR-011 L1 | Base HIGH-vol + completed breakout + fixed 4h episode; partial economics | 0 | **CLOSED — NOT SUPPORTED** (operator 2026-07-23); also UNPOWERED for ~10 bps; report `python/experiments/SPDR-011/report.md` |
| `CF-VOLCONV-001/HYP-002` | SPDR-011 L2 | HIGH vs disjoint MID/LOW absolute-movement increment | 0 | **NOT OPENED** — STOP after L1 |
| `CF-VOLCONV-001/HYP-003` | SPDR-011 L3 | HIGH signed residue vs identical unconditional breakout | 0 | **NOT OPENED** — STOP after L1 |
| `CF-VOLCONV-001/HYP-004` | SPDR-011 L4 | Fixed TOP2 add-on; TOP1/TOP3 distribution-only | 1 predeclared modifier | **NOT OPENED** — STOP after L1 |
| `CF-VOLCONV-001/HYP-005` | SPDR-011 L5 | Fixed upper-tercile aligned-flow add-on | 1 predeclared modifier | **NOT OPENED** — STOP after L1 |
| `CF-VOLCONV-001/HYP-006` | EXP-099 | Frozen-rule Nautilus membership/accounting/physicality reproduction | 0; implementation confirmation | **RESERVED / NOT AUTHORISED** — Run-1 evidence not accepted |

The base, TOP2 and flow variants are deterministic branches, not a search grid. Layers open in order
only after operator decisions. Failed/dropped arms remain recorded. No replacement threshold, symbol,
side, horizon or exit is permitted after outcome contact.

**AMENDMENT-A1:** remove all Chapter-05 spread proxies; report spread as unavailable/null and costs
as partial — **DIRECTION: LOOSER** economically. Running count: **1L / 0T / 0N**. The mandatory
understatement/overstatement caveat does not restore the omitted cost or authorize deployability.

---

## Chapter 06 — CF-VOLDIR-001 (registered 2026-07-23)

**Checkpoint:** `2026-07-23-017-structural-vol-direction-programme`  
**Route:** `SPDR-012` (vol reliability) → `SPDR-013` (direction expectancy) → mid reflection →
`SPDR-014` (combination) → conditional `XENA-VOLDIR-001`. TRAIN only; 0 counted reads; no XENA until D
graduates a base. **Not** a reopening of CF-VOLCONV-001.

| ID | Vehicle | Registered question / arm | Candidate slot | Status |
|---|---|---|---:|---|
| `CF-VOLDIR-001/HYP-A` | SPDR-012 | Vol predictability/reliability under frozen metrics (clustering, level, regime, realised measures, clock, XS rank, tail); **universe = top-25 30d USD volume** | 0 | DESIGN COMPLETE (+U1); execution unauthorised |
| `CF-VOLDIR-001/HYP-B` | SPDR-013 | Fast direction expectancy bps (SMA 14/25/≤50 + angle; ZigZag ATR + path-local features; magnitude and/or vol of next whole move) — **not win-rate**; **same top-25 universe** | 0 | DESIGN COMPLETE (+U1); default after SPDR-012 gate |
| `CF-VOLDIR-001/HYP-C` | Reflection | Mid-checkpoint freeze of combination / stop / direction-agnostic branch | 0 | REGISTERED; not result-producing |
| `CF-VOLDIR-001/HYP-D` | SPDR-014 | Vol×direction or authorised direction-agnostic extraction under partial-cost disclosure | 0 | SCREEN COMPLETE (2026-07-24) — INCONCLUSIVE / UNPOWERED_NOT_NULL (B-5); `residual_status=NONE` (0/927 powered); 0 counted reads; SPDR-016 opened by operator override on SUGGESTIVE leads |
| `CF-VOLDIR-001/HYP-E` | XENA-VOLDIR-001 | Portfolio/search on graduated D bases only | 0 | RESERVED; requires D graduation + separate design/QA/approval |

Failed/dropped arms remain recorded. No replacement primary direction device (including SPDR-011
range-break) without new predeclared evidence. No unbounded ML/indicator zoo after outcomes.

**AMENDMENT-A2:** match/time-stability thirds use the effective eligible DESIGN interval because the
catalog has no core data in the first two nominal thirds — **DIRECTION: NEUTRAL**. Running count:
**1L / 0T / 1N**.

**AMENDMENT-A3:** retain every located event; missing later marks become explicit null attrition and
never define eligibility — **DIRECTION: NEUTRAL**. Running count: **1L / 0T / 2N**.

**AMENDMENT-A4:** freeze exact control seed ranges, matching units/strata and the logical
DESIGN/CONFIRM artifact-bundle seal before outcome contact — **DIRECTION: NEUTRAL**. Running count:
**1L / 0T / 3N**.

**AMENDMENT-A5:** exclude the realised TOP2 pair from its L4 random-pair null so the control cannot
reproduce the live selection — **DIRECTION: TIGHTER**. Running count: **1L / 1T / 3N**.

**AMENDMENT-A6:** require a live signed-catalog tree re-hash, a binding supported-edge
future-destroy survival rule, and event-by-event theoretical-to-Nautilus fill reconciliation —
**DIRECTION: TIGHTER**. Running count: **1L / 2T / 3N**.

## Amendment Rules

An amendment is required before measurement if any of these change:

- adding a candidate family;
- adding an AVWAP variant or alternative trend detector;
- changing MA windows, volume exponent, band multiplier, bounce definition, or
  domains;
- changing the reference book used for portfolio-fitness screening;
- changing the registered EXP-021 fixed-horizon reaction metric family;
- changing the registered EXP-022 lifetime completion or metric family;
- dropping the original metric book from EXP-023;
- changing the planned EXP sequence or result gates;
- allowing an implementation to screen a candidate before its component
  characterization experiment is complete.

Amendments must state whether the changed item consumes a new multiplicity slot.
