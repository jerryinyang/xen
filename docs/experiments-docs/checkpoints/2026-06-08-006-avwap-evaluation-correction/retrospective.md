# Phase 006 Retrospective — EVAL_SUPPORTED (Evaluation-Framing Corrected, cTrader-Confirmed)

**Checkpoint:** `2026-06-08-006-avwap-evaluation-correction`
**Status:** **COMPLETED 2026-06-09** — all three experiments executed and
post-governance APPROVED; phase objective fully satisfied.
**Outcome class:** `EVAL_SUPPORTED` (design §7) — EXP-027 validated the corrected
yardstick, EXP-028 found event-level edge under it, EXP-029 confirmed parity on the
cTrader production path.
**Supersedes:** `2026-06-08-005-avwap-exit-and-branch-exploration` (HALTED).
**Root-cause review:**
`docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.
**Omission record (closed):** `EXP-028-omission.md` in this checkpoint directory.

---

## 1. Why this phase existed

Phase 005 was halted (`HALTED_FRAMING_INVALID`) once operator review found that the
entire EXP-023/024/025 chain inherited an **unexamined premise**: that the frozen
qualification suite — a **per-bar continuous-position referee** calibrated for
**≥80 %-active** series in EXP-005 — is the right vehicle to screen a **~6 %-active
event signal**. It is not. The strategy *position rule* in EXP-023 was ~faithful to
the original HYP-002 sequence; **the defect was the evaluation yardstick, not the
trade logic.**

Phase 006 was scoped narrowly to repair exactly that: (1) define and **calibrate** a
fit-for-purpose event-level evaluation method, then (2) re-screen the **faithful**
selective AVWAP strategy under it. No parameter sweeps, no exit overlays, no
detector/anchor branches, no metric-shopping. Predeclared once, measured once,
holdout sealed.

## 2. Experiments executed and their verdicts

| EXP | Role | Verdict | Headline |
| --- | --- | --- | --- |
| **EXP-027** | Event-level evaluation method: definition + sparse-regime calibration (methodology; no candidate-screening slot) | **METHOD_VALID** | FPR ≤ α₀ = 0.05 in every domain under both null generators across the {3 %, 6 %, 12 %} activity bracket (max per-domain FPR 0.034 at α₀); finite event-level MDE in every domain (5m 1 bps, 1h 4 bps, 4h 32 bps); determinism + precision gates PASS. |
| **EXP-028** | Faithful selective AVWAP re-screen under the frozen EXP-027 method (Python re-analysis of EXP-020/022 substrate) | **EVAL_SUPPORTED** | All three domains PRIMARY `EVIDENCE_FOR`: +5.78 bps (5m, n=12 795), +23.38 bps (1h, n=924), +69.02 bps (4h, n=187); Holm p = 0.003 each; equity companion consistently positive (advantage_rate 1.0). |
| **EXP-029** | cTrader per-bar streaming parity for the corrected, pyramid-inclusive C# strategy | **CONSISTENT** (parity) | All three domains land in the CONSISTENT band (\|Δeffect\| = 0.007 / 0.054 / 0.000 bps); all five binding gates pass; EXP-028 upgraded to **cTrader-confirmed**. |

The verdict chain reads cleanly against the design's outcome table: EXP-027
METHOD_VALID unlocked EXP-028; EXP-028 EVIDENCE_FOR on ≥1 domain delivered
`EVAL_SUPPORTED`; EXP-029 CONSISTENT converted the Python-only result into a
production-path-confirmed one.

## 3. What the phase established

- **The EXP-023 negative was a framing/dilution artifact, not absence of signal.**
  Under an in-envelope event-level yardstick, the *same* faithful strategy shows a
  positive per-event matched-control excess on all three domains, with effects
  rising monotonically 5m → 4h — the same shape EXP-021/022 found per event.
- **The corrected yardstick is honest, not permissive.** EXP-027 was calibrated on
  synthetic null + planted-edge substrates only (anti-overfitting fence), froze
  before EXP-028 read any real outcome, and demonstrated controlled FPR *and*
  recovery. The EXP-021/022 inference machinery (regime-cluster bootstrap +
  stratified sign-permutation + Holm + Evidence-FOR rule) transfers to the sparse
  regime — validating the Phase 006 framing-correction thesis directly.
- **The result survives the production code path.** EXP-029 ran the corrected C#
  `AvwapBounceModel` bar-by-bar inside cTrader and graded three production layers
  independently — entry signal (≥99.8 % of EXP-020 5m triggers reproduced), pyramid
  position opening (counts within ±0.5 %; pyramids ≈49 % of PRIMARY events), and the
  executed completion code (`MaybeCompletePosition` vs Python `scan_lifetime`,
  match rate 1.000, max discrepancy ~1.8e-11 bps). This extends VAL-002-style
  pipeline parity from the MA-crossover dogfood to the AVWAP baseline strategy.

## 4. What changed vs the original design

The design opened with a two-experiment plan (EXP-027 → EXP-028, gated). It was
**amended on 2026-06-09 (design §9–§10)** to append a third experiment:

- **The omission.** EXP-028 was implemented — transparently, per its approved
  `scope.md` — as a **pure Python re-analysis** of upstream artifacts (EXP-020
  events, EXP-022 lifetimes). It never invoked EXP-023's C# `AvwapBounceModel.cs`,
  never ran a cTrader `Mode=StrategyHost` backtest, and never ingested cTrader-emitted
  `positions.parquet`. The design's faithfulness clause — *"the only change vs.
  EXP-023 is the evaluation method, not the trade logic"* — carried an **implicit
  "same execution path" requirement** (EXP-023's trade logic *was* a cTrader run),
  and neither the EXP-028 scope nor Stage 4 governance carried that requirement
  forward. The result was internally consistent against its own scope but bypassed
  the cTrader-in-the-loop validation the faithfulness clause assumed.
- **The correction (EXP-029).** Rather than re-litigate EXP-028 — whose edge
  measurement on the canonical EXP-020 substrate remains valid — a new
  **parity-confirmation** experiment was appended to close the gap: correct
  `AvwapBounceModel.cs` so pyramid bounces open and track independent positions
  (it previously `pyramid_skipped` with a single concurrent position), run it on
  cTrader, and grade it through the frozen EXP-027 inference tail.
- **EXP-029 was itself hardened before execution.** A pre-execution adversarial
  review found the first EXP-029 design would *run* the corrected C# but not *grade*
  it — the binding estimand re-scanned exits in Python, so a CONSISTENT result would
  certify only signal emission, not the new concurrent-completion code. EXP-029 was
  strengthened (F01–F05): the C# now serializes its executed completion for per-event
  exit-parity grading, a feed-exact 5m signal-layer reconciliation was added, a
  magnitude-equivalence gate (so divergence can *downgrade*, not merely fail to
  upgrade), a pyramid split in the count gate, and a hard-asserted frozen-method
  hash. This closed the omission in spirit (the production completion code is
  validated), not only in letter (the code runs).

No EXP-IDs were renamed or reused. EXP-027 consumed no candidate-screening
multiplicity slot; EXP-028/029 corrected and confirmed the existing `CF-AVWAP-001`
HYP-004 baseline screen without opening a new candidate-family slot.

## 5. The framing-correction narrative

Read end to end, Phases 004–006 are a single arc about getting the **unit of
analysis** right:

1. **Phase 004** built supported *per-event* evidence (EXP-020 substrate, EXP-021
   bounce reaction, EXP-022 lifetime completion), then screened the strategy through
   the *per-bar* frozen suite (EXP-023) and read the negative as terminal
   (`BASELINE_BRANCH_REFUTED`).
2. **Phase 005** tried to diagnose *where within the overlay* the edge dissipated —
   and in doing so inherited the very premise it should have questioned. Operator
   review caught it; the phase was halted before compounding the defect across
   Stages B/C.
3. **Phase 006** stopped diagnosing the signal and instead **fixed the vehicle**:
   build a yardstick whose activity envelope brackets the ~6 % signal (EXP-027), then
   re-screen the unchanged strategy under it (EXP-028), then confirm the whole thing
   on the code that would actually run in production (EXP-029).

The arc resolves the way the framing review predicted: the conditional AVWAP event
edge was real all along; what changed is that it is now measured with an instrument
in calibration for the signal it measures — and confirmed on the production path, not
just in re-analysis.

## 6. Open items

- **HYP-001 (direct AVWAP line as support/resistance) remains untested and open.**
  EXP-025 was confounded (its metric conflated the bounce-trigger definition with the
  line-rejection signal) and Phase 006 deliberately did not address it — operator
  decision was that the faithful strategy redo is the sole in-scope strategy. It is
  recorded as an open foundational question, not retired.
- **The global holdout remains sealed.** Every Phase 006 result is first-70 %
  analysis-set only; the final 30 % was never loaded (in-robot fence + Python
  re-assertion in EXP-029). No out-of-sample confirmation exists yet.
- **Costs are not deducted anywhere in Phase 006.** All effects are gross
  event-level matched-control excess. Cost/slippage-bearing *tradability* is out of
  scope and unanswered.
- **Event-level edge ≠ per-bar-suite tradability.** Phase 006 does **not** overturn
  EXP-023's per-bar `REFUTED` — they are different, non-substitutable yardsticks. The
  frozen per-bar suite remains the programme standard for ≥80 %-active candidates and
  is unchanged.

These bound the disposition: `EVAL_SUPPORTED` is "first fairly-evaluated positive
result for `CF-AVWAP-001`," not "tradable strategy." Per design §7, the next move is
operator-selected — robustness/fresh-regime planning, cost-bearing tradability, or
the HYP-001 / detector / anchor branches Phase 005 deferred.

## 7. Lessons learned

1. **A faithful re-screen must state its execution path explicitly in scope.** This
   is the central process lesson, recorded in `EXP-028-omission.md`. "Change only
   the evaluation method, not the trade logic" is ambiguous when the original trade
   logic *is* a specific execution path (cTrader per-bar streaming of the C# robot).
   EXP-028 silently substituted a Python re-analysis of upstream artifacts for that
   path and was internally consistent — so the gap was invisible to a scope-relative
   audit. Going forward: any "faithful re-screen" scope must name its execution path
   (cTrader per-bar streaming vs. Python re-analysis of upstream artifacts), and
   **Stage 4 pre-execution governance must check that path against the lineage the
   faithfulness clause references.** Add this as an explicit pre-execution check.
2. **A confirmation experiment must be able to fail.** The first EXP-029 design was a
   confirmation-only "verdict + CI-overlap" read that re-scanned exits in Python,
   making CONSISTENT close to foreordained for the new completion code. The F01–F05
   hardening — grade the *executed* C# completion, add a magnitude gate that can
   downgrade, reconcile the signal layer feed-exact — made the parity claim
   falsifiable. A parity test that cannot produce INCONSISTENT validates nothing.
3. **Fix the vehicle before diagnosing the signal.** Phase 005's failure mode was
   asking "where does the edge go *within* the overlay" instead of "is the overlay
   the right vehicle." Phase 006 succeeded by inverting that order. Keep at least one
   diagnostic per chain pointed at the framing itself — and when a framing defect is
   found, repair the instrument before any further within-signal diagnosis.
4. **Calibrate the referee to the signal's activity regime — and prove the
   machinery transfers.** EXP-027 did not invent new inference; it re-used the
   EXP-021/022 bootstrap/permutation/Holm machinery and re-calibrated its operating
   characteristics for the sparse envelope, on synthetic substrates, frozen before
   reading real outcomes. That is the reusable pattern for screening any
   out-of-envelope signal: same inference object, re-validated operating
   characteristics, anti-overfitting fence intact.

## 8. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-027 | METHOD_VALID | Frozen event-level evaluation method for the sparse (~6 %-active) regime; MDE map 1 / 4 / 32 bps (5m/1h/4h). Methodology experiment; no candidate-screening slot. |
| EXP-028 | EVAL_SUPPORTED → **cTrader-confirmed** | Faithful AVWAP re-screen; first fairly-evaluated positive for `CF-AVWAP-001`. Edge measurement on EXP-020 substrate stands; upgraded by EXP-029 parity. |
| EXP-029 | CONSISTENT (parity) | Production-path confirmation; closes the EXP-028 omission. Entry/pyramid/completion code independently graded against the Python re-analysis. |
| EXP-028-omission | OMISSION_RECORDED → **closed by EXP-029** | Retained as the process-lesson record (faithful re-screens must state execution path). |
| HYP-001 (line S/R) | OPEN | Untested; recorded for operator decision, not retired. |
| Global holdout | SEALED | Never loaded in Phase 006. |

## 9. Redirect

Phase 006 closes `EVAL_SUPPORTED`/cTrader-confirmed with the evaluation vehicle
repaired and the faithful strategy positive on all three domains under it. The
multiplicity registry retains EXP-027 (methodology), EXP-028 (HYP-004-R re-screen),
and EXP-029 (parity confirmation) with 0 new candidate-family slots consumed.

The open foundational questions are now sharply posed and operator-gated:

1. **Out-of-sample** — a deliberate one-shot holdout-release confirmation of the
   event-level edge (its own governance; holdout currently sealed).
2. **Cost-bearing tradability** — re-evaluate under an explicitly-scoped cost model
   and an appropriate referee; the question EXP-029 deliberately does not answer.
3. **HYP-001** — a confound-free direct AVWAP line-S/R test (the gap EXP-025 could
   not close).
4. **Stage-C branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) deferred from Phase 005,
   reconsidered now that the faithful redo is read.

No tuning was performed; no metric was reselected after results; predeclared once,
measured once. Holdout remains sealed.
