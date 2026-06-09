# Phase 004 Multiplicity Registry

**Status:** ACTIVE under Phase 007 (tradability & edge isolation). Phase 006 **CLOSED 2026-06-09** — `EVAL_SUPPORTED`/cTrader-confirmed: EXP-027 METHOD_VALID, EXP-028 EVIDENCE_FOR on all 3 domains, EXP-029 CONSISTENT parity. Phase 007 opened 2026-06-09 to answer cost-bearing tradability (EXP-030) and entry-vs-exit edge isolation (EXP-031); holdout release (EXP-032) is DEFERRED and hard-gated on EXP-030. Phase 005 **HALTED 2026-06-08** before Stage B/C — operator review found EXP-023/024/025 inherited an evaluation-framing defect (a ~6%-active event signal screened/diagnosed through a per-bar continuous-position referee calibrated only for ≥80%-active series). Dispositions corrected by **supersede + retain** (no ID reuse, no erasure): EXP-023 SUPERSEDED (framing-corrected), EXP-024 RETAINED (fork leg discounted), EXP-025 INCONCLUSIVE (non-informative for HYP-001); EXP-026 `/EXIT` SHELVED; Stage C deferred. Root-cause review: `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`. Phase 006 opened to fix the evaluation vehicle (EXP-027) then re-screen the faithful strategy (EXP-028).
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
| `CF-AVWAP-001/ANCHOR` | TBD | Significant-pivot anchor vs running-extreme anchor (gap #1). | 1 | **DEFERRED** | As above. |

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
| `CF-AVWAP-001/HYP-004-T` | EXP-030 | Under a predeclared per-event cost/slippage model (conservative variant binding), does the faithful selective AVWAP strategy retain positive **net** per-event expectancy on ≥1 domain (first-70% analysis set)? | 0 (cost layer on registered HYP-004-R baseline) | SCOPED | **Hard gate for holdout release (EXP-032).** Trade logic identical to EXP-028/029; the only addition is the cost layer. Cost model is event-level (the frozen per-bar suite is NOT the vehicle — EXP-023 trap). A net-negative 5m is an expected, informative outcome, not experiment failure. No cost-model re-selection after reading results. |
| `CF-AVWAP-001/DIAG-003` | EXP-031 | Of the EXP-028 measured per-event excess, how much is attributable to AVWAP bounce **entry timing** vs the EXP-022 band-target/trend-change **exit rule**? | 0 (diagnostic) | SCOPED | Runs regardless of EXP-030 outcome; does not gate and is not gated by it. Decomposition legs and dominance thresholds predeclared in scope; frozen EXP-027 inference tail; no post-result leg reselection. |
| — (holdout release) | EXP-032 | *(deferred)* One-shot holdout confirmation of the event-level edge. | — | **DEFERRED / NOT REGISTERED** | Admissible only on EXP-030 EVIDENCE_FOR (≥1 domain); own checkpoint + governance required. The global holdout is never released to confirm a gross edge. |

### Carried, not worked (Phase 007)

| Item | Status |
| --- | --- |
| HYP-001 (AVWAP line as direct S/R) | OPEN, explicitly NOT confirmed by EXP-028/029 (design §8); parallel/fallback mechanism branch; not worked this phase. |
| Stage-C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) | DEFERRED; reconsidered via family review if EXP-030 fails. |
| `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` | Remain deferred/registered; no slot consumed. |

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
