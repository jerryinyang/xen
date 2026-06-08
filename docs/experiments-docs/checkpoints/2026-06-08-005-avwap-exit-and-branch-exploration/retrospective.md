# Phase 005 Retrospective — HALTED (Evaluation-Framing Divergence)

**Checkpoint:** `2026-06-08-005-avwap-exit-and-branch-exploration`
**Status:** **HALTED 2026-06-08** before Stage B/C — superseded by correction
checkpoint `2026-06-08-006-avwap-evaluation-correction`.
**Outcome class:** `HALTED_FRAMING_INVALID` (not a normal phase completion).
**Root-cause review:**
`docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.

---

## 1. Why this phase was halted

Phase 005 was scoped to (A) diagnose where the EXP-021 event edge dissipates,
(B) design an exit screen if a holding fix looked plausible, and (C) explore
detector/anchor branches. Stage A completed (EXP-024 `MIXED_OR_INCONCLUSIVE`,
EXP-025 `INCONCLUSIVE`) and the design correctly required operator handling of the
mixed result before Stage B/C.

Operator review of the completed Stage A surfaced a **root cause upstream of the
fork question Phase 005 was built to answer**: the entire diagnosis inherited an
**unexamined premise** — that the frozen qualification suite (a **per-bar
continuous-position referee** calibrated for **≥80 %-active** series in EXP-005)
is the right vehicle to screen and diagnose a **~6 %-active event signal**. It is
not. Per the review:

- **EXP-023's** negative screen is dominated by ~16× per-bar denominator dilution
  and an out-of-calibration application of the suite — not by absence of signal.
- **EXP-024's** fork-(b) leg compares a cumulative multi-bar per-event hold return
  against a per-bar floor — a category mismatch that makes fork (b) close to
  foreordained and low-information.
- **EXP-025's** metric conflates the bounce-trigger definition with the
  line-rejection signal, so it was structurally biased to a negative result and
  did **not** test HYP-001.

Because Phase 005 Stages B and C (EXIT / LB / MB / ATR / ANCHOR) would each be
screened through the **same per-bar suite**, every downstream branch would
mis-fire for the identical reason. Proceeding would compound the defect rather
than resolve it. The phase is therefore halted and replaced with a checkpoint that
fixes the evaluation vehicle first.

## 2. What Stage A actually established (corrected reading)

- The EXP-021/022 **per-event** evidence is **not invalidated** — it stands.
- The event edge is **relative, not absolute** (EXP-024 retained finding):
  bounces fall less than matched controls but do not themselves rise.
- **Trend-change exits cut losers, not winners** (EXP-024 retained finding),
  weakening the "hold-too-long" exit-repair story.
- Whether a **selective event vehicle** with proper event-level evaluation carries
  tradable edge is **untested**.
- **HYP-001** (direct AVWAP line S/R) is **untested** — EXP-025 was confounded.

## 3. Disposition of Phase 005 artifacts (supersede + retain)

| Item | Prior status | New disposition |
| --- | --- | --- |
| EXP-023 | REFUTED (FULL screen) | **SUPERSEDED (framing-corrected)** — valid as a per-bar screen; not a tradability test of the original selective vehicle. Retained in ledger. |
| EXP-024 | MIXED_OR_INCONCLUSIVE | **RETAINED, fork leg discounted** — relative-not-absolute edge and trend-change-cuts-losers findings stand; fork (b) verdict is low-information. |
| EXP-025 | INCONCLUSIVE | **INCONCLUSIVE retained, annotated non-informative for HYP-001** — confounded metric; HYP-001 remains open. |
| EXP-026 `/EXIT` (HYP-005) | PLANNED (reserved) | **SHELVED** — never scoped; EXP-ID retired, not reused. |
| Stage C `/LB` `/MB` `/ATR` `/ANCHOR` | PLANNED | **DEFERRED** — out of correction scope; reconsidered only after the evaluation vehicle is fixed and the faithful redo is read. |

No EXP-IDs are renamed or reused; no result is erased. The multiplicity registry
retains all rows with corrected dispositions.

## 4. Lessons learned

1. **Calibrate the referee to the signal's activity regime before screening.**
   The suite's MDE map is only valid inside the activity envelope it was validated
   on (≥80 % active). Sparse event signals need their own calibrated operating
   mode; applying a per-bar floor to a ~6 %-active signal is an out-of-envelope
   extrapolation. Add this as a Stage 4 pre-execution governance check.
2. **Preserve the unit of analysis across a chain.** EXP-020/021/022 were
   per-event; the screen silently switched to per-bar. A chain must screen on the
   same estimand its component evidence was built on, or convert explicitly with a
   validated mapping.
3. **A confounded metric is a design failure, not a result.** EXP-025's confound
   was derivable from the trigger definition before execution; predeclaring "one
   primary metric" is not sufficient if that metric is structurally biased.
4. **Diagnostics can inherit the premise they should be testing.** Stage A asked
   "where does the edge go *within* the overlay" instead of "is the overlay the
   right vehicle." Keep one diagnostic per chain pointed at the framing itself.

## 5. Redirect

Superseded by **`2026-06-08-006-avwap-evaluation-correction`**:

- **EXP-027** — define + calibrate an event-level evaluation method (per-event
  expectancy + equity-curve vs. buy-hold; predeclared decision rule reusing the
  EXP-021/022 control/bootstrap/Holm machinery; null/control for error control).
- **EXP-028** — faithful AVWAP selective-strategy redo screened under EXP-027.
  This is the **only strategy in scope** for checkpoint 006.

Holdout remains sealed throughout. No tuning; predeclared once, measured once.
