# G-016 Gate Review — CF-HA-HARAMI-001 / CAND-001 Terminal Adjudication

**Date:** 2026-06-19
**Gate:** G-016 (Phase 016 terminal gate — candidate screening of CF-HA-HARAMI-001/CAND-001)
**Adjudication:** desk review, **operator-directed** (2026-06-19, "close the family")
**Outcome:** **CLOSE_FAMILY** — `CF-HA-HARAMI-001` moved to **CLOSED**; CAND-001 retired.
**Holdout:** never touched at any point in Phase 016. **0 counted TEST reads beyond EXP-071's 6.**

---

## 1. Decision

`CF-HA-HARAMI-001` (Heiken Ashi Harami at Trend Exhaustion) is **CLOSED**. Its sole candidate
branch `CAND-001` (MA(20,50)-native conditioned harami, `N-PARTIAL-V2A` lead arm) is **retired**.
No further in-family experiment is authorized; no holdout read is warranted. All file-drawer items
(hypotheses, variants, refuted/inconclusive outcomes) are **retained in the registry, never deleted
or reused**, per programme discipline. The family is **reopenable only by a genuinely new,
separately-registered lever** that is not on the already-exhausted registered surface (see §5).

## 2. Relationship to the predeclared G-016 criteria (stated honestly)

The Phase 016 `design.md` §7 G-016 table maps the **EXP-071 outcome** mechanically:

> **TEST_NOT_CONFIRMED** → "CAND-001 retired on the tested scope; **family stays OPEN** (hybrid
> object reinstatable…; other native arms may be registered separately). Counted reads consumed."

EXP-071 returned TEST_NOT_CONFIRMED (2026-06-19; 0/6 binding cells, 4/6 median CI_low ≤ 0). **Under
the letter of that table, the mechanical consequence was "family stays OPEN," and that is the status
the family held immediately after EXP-071.** The family was kept open for one specific reason: a
positive median tilt + the lone GBPUSD-5m survivor + the EXP-060B real MA-substrate median edge
argued there might still be a removable obstacle (the raw-mean/loss-tail failure), so the operator
authorized a TRAIN-only diagnostic + design follow-up to test exactly that, under append-only
amendments (D0-amendment-005/006 → EXP-074; D0-amendment-007 → EXP-075).

**This closure therefore goes beyond the mechanical EXP-071→OPEN mapping.** It is an
operator-directed terminal adjudication on the **augmented Phase 016 slate** (EXP-071 + the EXP-074
diagnostic + the EXP-075 design follow-up), made with the new evidence in full view. G-016 was
predeclared as adjudicated "after the full Phase 016 slate"; the slate was extended in-phase by the
amendments, and the gate is decided on the extended slate. The decision is recorded as a judgment,
not as a mechanical table lookup — consistent with G-015's desk-adjudicated, operator-ratified
posture.

## 3. Evidence base (the closed arc)

| Experiment | Result | What it established |
| --- | --- | --- |
| **EXP-070** (HYP-023) | CALIBRATION_DELIVERED | Event-level method FPR-controlled on the 6 TEST cells; the TEST read was methodologically sound (no METHOD_DEFECT). |
| **EXP-071** (HYP-024) | **TEST_NOT_CONFIRMED** | First counted TEST contact: 0/6 binding cells clear the composition conjunction; 4/6 median CI_low ≤ 0 (systematic negative, not power-limited). The raw-mean leg is the binding failure; `mean_recoverable=false` → the loss tail is entry-structural, survives removing the adverse stop. |
| **EXP-074** (HYP-027) | CHARACTERISATION_DELIVERED | Located the driver: entry exhaustion magnitude (`msofar_atr`) separates the extreme q05 loss tail near-universally (AUC ≈ 0.84–0.90, 100% of powered cells), but is gate-masked because the effect is tail-shaped (bimodal), not location-monotone. H2 (polarity) refuted; `favdist_atr` redundant. |
| **EXP-075** (HYP-028) | **FILTER_INEFFECTIVE** | The one identified lever — an entry-time exhaustion **cap** — is **not actionable**: M-GLOBAL adds 0 improved cells in every band-core domain across the whole pre-declared grid; M-PERCELL (overfit ceiling) tops out at 30m +0.118 < 0.15. The cap strips big winners together with the q05 losers (bimodality), netting a wash/negative on the joint four-leg economic criterion. |

**Synthesis:** the family's binding obstacle is now characterized on both sides. EXP-071 showed the
TEST confirmation fails on the raw-mean leg. EXP-074 showed the failure is driven by an **intrinsic
bimodality of the conditioned entry** (high exhaustion produces both the catastrophic losers and the
large winners). EXP-075 showed that bimodality is **not separable by the natural entry lever** (an
exhaustion cap), because removing the bad tail also removes the good tail. There is no remaining
registered lever with a credible path to lifting the mean without destroying the median edge.

## 4. Why the median edge no longer justifies keeping the family OPEN

The family was carried OPEN across G-015 and post-EXP-071 on the strength of a **real MA-substrate
median edge** (EXP-060B: 85/99 cells beat own-substrate matched-random) and a positive median tilt.
That edge is genuine and is **not** retracted. But Phase 016 has now established that it is **not
convertible into a TEST-confirmable tradable candidate**:

- the median edge exists, but the **raw mean is the binding TEST leg** and it fails (EXP-071);
- the mean fails because of an exhaustion-driven bimodal loss tail (EXP-074);
- that tail **cannot be removed at entry without removing the winners that create the median edge**
  (EXP-075) — the median edge and the catastrophic tail share the same driver.

A median-positive signal whose mean cannot be lifted without erasing the median is not a tradable
candidate. The registered surface (entry conditioning, favourable/adverse/third-barrier geometry,
position-management exits, and now the exhaustion cap) has been exhausted across Phases 014–016 with
no composing combined definition. Closure is the correct disposition.

## 5. What is retained and what could reopen the family

**Retained (never deleted/reused):**
- All HYP rows and variant registrations in `multiplicity-registry.md` keep their refuted/
  inconclusive/characterised outcomes on the record.
- The **hybrid object** (ZigZag-`/STRONG-STAT` × MA geometry) remains CHARACTERISED_NOT_VIABLE on
  the disclosed surface (EVIDENCE_AGAINST L1/S1/S3, INCONCLUSIVE S2); never pooled with native.
- The EXP-075 locked filter (`locked_filter.json`, `deployable=false`, sha256-pinned) is retained as
  a frozen negative artifact; it is **non-confirmatory and carried nowhere**.
- TEST-read ledger: the 6 EXP-071 counted reads stand (each binding stratum at 1/2 lifetime); the
  global holdout was never touched and remains sealed.

**Reopen condition (high bar):** CF-HA-HARAMI-001 may be reopened only by a **genuinely new lever
not on the exhausted registered surface** — e.g. a fundamentally different conditioning object, a
non-entry mechanism for the bimodality, or a new substrate — registered under its own scope/D0 with
its own G0. A new entry filter on the same surface, or a re-run of a refuted variant, does **not**
qualify. Absent such a lever, the family is terminally closed.

## 6. Integrity confirmation

- **Holdout sealed** throughout Phase 016; the global holdout (final 30% per instrument) was never
  loaded. The single sanctioned holdout shot remains SPENT only on EXP-032 (EURUSD-4h, unrelated).
- **TEST discipline:** 6 counted reads spent (EXP-071), each binding stratum at 1/2; EXP-070/074/075
  spent 0 counted reads (calibration / TRAIN-only). EURUSD excluded instrument-wide throughout.
- **No goalpost-moving:** EXP-074's pre-registered consistency gate was never retro-edited; EXP-075
  re-ran no separation gate and judged the cap on the strategy's own economic legs; the proceed to
  EXP-075 on framing-resolved evidence was operator-ratified with the "formal SEPARATOR_FOUND not
  met" conflict in full view (D0-amendment-007).
- **Audits:** EXP-070 PASS; EXP-071 audit PASS; EXP-074 CONDITIONAL PASS (0C/2W/3I); EXP-075
  CONDITIONAL PASS (0C/1W/2I). All post-experiment governance verdicts APPROVE.

## 7. Consequences

1. `CF-HA-HARAMI-001` → **CLOSED**; CAND-001 retired. Recorded in
   `docs/signal-registry/candidate-families/harami.md`, `docs/signal-registry/multiplicity-registry.md`,
   `docs/experiments-docs/INDEX.md`, and `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`.
2. **Phase 016 CLOSED** at G-016. Retrospective written
   (`retrospective.md`, this checkpoint).
3. No EXP-072/EXP-073 (were conditional on TEST_CONFIRMED — never opened). No holdout experiment.
4. Programme routing (next phase) is an operator decision outside this gate — a new candidate family
   or a return to the candidate backlog. This gate makes no claim on the next research direction.
