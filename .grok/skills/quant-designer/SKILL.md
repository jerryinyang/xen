---
name: quant-designer
description: Design Xen experiments mechanism-first — scope, estimand, analysis plan, controls, and interpretation bands derived from the candidate's own mechanism. Use when designing an experiment, writing design.md, choosing statistical methods, defining success criteria, planning controls or nulls, selecting a referee/test variant, or responding to prompts such as design the experiment, analysis plan, what test, scope this idea, or methodology.
---

# Quant Designer

Design experiments. Successor to the experiment-quant-analyst (INFR-001): that skill was a
generic methods checklist, and every Category-B failure of EXP-014→017 — degenerate control
(B-1), measured-object ≠ traded-object (B-4), per-event ≠ episode estimand (B-8), overlapping
effect windows (B-9), unpowered negatives (B-5), binary reads hiding partial attenuation (B-2)
— walked straight through it. This skill exists to make those impossible to ship silently.

Design only: interpretation of completed experiments belongs to the `data-analyst` (evidence)
and the operator (verdict). Implementation belongs to `experiment-developer`.

## Start

1. Read the shared pipeline config: the file ending `/research-pipeline/_pipeline-config.md`.
2. Read `docs/knowledge-base/INDEX.md`, `lessons-and-amendments.md`, `pitfalls-ledger.md` —
   never re-propose a dead end or re-learn a recorded lesson.
3. Read `docs/references/dataset-reference.md`; check `docs/signal-registry/` preconditions.
4. Read this skill's `references/design-requirements.md` (the mandatory declarations) and
   `references/methods-catalog.md`.

## Mechanism first (the ordering rule)

Write the **mechanism statement before anything else**: what physical/behavioural regularity
the candidate exploits, at what horizon, on what event cadence, producing P&L through which
object (leg, episode, per-bar carry). Every other design element is *derived from* this
statement — estimand, null, horizon, controls, test variant, power target. A design whose
evaluation machinery could be copy-pasted onto a different mechanism unchanged is not
mechanism-native and gets rejected at QA (L-13: the evaluation vehicle must be native).

## design.md — required content

One artifact, dense (tables/bullets), ~300-line budget. All items below are REQUIRED; QA
(pre-exec, fresh context) rejects a design missing any.

1. **One falsifiable question** + the mechanism statement.
2. **Object identity declarations** (each an explicit line, not implied):
   - measurement object == trading object (the estimand measures what the strategy trades —
     episode-level for multi-leg, L-16/L-18);
   - measured conditioning event == traded entry event (if the strategy fills a resting limit
     at the band touch, availability conditions on the band touch, not on a close-breach — B-4);
   - causally distinct effects get non-overlapping measurement windows (B-9).
3. **Estimand**: canonical `xen.adjudication` objects (per-leg / episode / exposure-correct
   per-bar). Never a bespoke accounting construction; the estimand-validation gate
   (`xen.estimand_validation`) must be runnable on the planned emission.
4. **Scope**: instruments/domains/parameters/time range/exclusions; mandatory final-30%
   holdout exclusion; complexity budget; Nautilus strategy + run config + catalog fence
   attestation (all edge-generating experiments run in Nautilus `BacktestNode` — no vectorised
   Python backtests). Declare **SPREAD-SCALE-ROUTING** block on T1 (§10 design-requirements).
5. **Controls, each with a validity proof** (see `design-requirements.md`):
   - non-degeneracy: the control population is disjoint from the signal population and could
     produce a different answer (B-1);
   - bite/MDE: demonstrate, at design time, the control can detect an effect of the expected
     size (an MDE curve or synthetic plant co-designed with the band — not a fixed plant);
   - non-vacuity: the destroy control moves the metric's sufficient statistic (a permutation
     that preserves the mean cannot referee a mean — B-6/EXP-012);
   - ≥1 future-destroying leak tripwire that MUST collapse the edge.
6. **Test selection, candidate-aware**: pick significance/robustness tests matched to the
   trading style and effect shape (mean-reversion vs outlier-fade vs trend-following get
   different noise models; tail/asymmetric effects get shape-aware reads, not location-only
   gates). Fixed pre-designed referee stacks are prohibited; compose from the toolbox and
   justify each piece against the mechanism.
7. **Interpretation bands, not binaries**: predeclared effect-size bands per stratum
   (supported / wash-within-noise / contradicted / unpowered), collapse-fraction disclosure
   for every control, pooled figures labelled disclosure-only.
8. **Power statement**: expected event counts per stratum, minimum detectable effect, and the
   explicit list of strata that will be UNPOWERED (an unpowered cell can never be reported as
   a negative).
9. **Golden-trace spec**: 2-3 hand-computable events (timestamps + expected entry/exit/fill
   behaviour derived from this design) that QA will diff against the emission.

## Hard gates vs informative reads (binding frame)

- **Integrity checks are hard** (leak tripwire, holdout, causality, reconciliation): design
  them in; they block.
- **Everything about signal QUALITY is informative**: no materiality thresholds, no readiness
  floors, no multi-gate conjunctions, no auto-RETIRE conditions in the design. The design
  states what will be measured and the bands for reading it; the operator judges worth.

## Constraints

- No holdout contact; no goalpost moves after results exist; new questions → new experiments.
- Non-parametric/bootstrap first; parametric only with non-parametric cross-check.
- Real-price outcomes only (RealOpen/High/Low/Close); open-to-open returns; `≤ t-1`
  conditioning throughout.
- Experiment-level only: no family dispositions in a design.
- **XENA runs**: the design declares the universe manifest (candidate grid — models ×
  params × instruments × domains), per-candidate cost from `bybit_round_trip_cost_bps`
  (chapter 04) or archived FTMO table (chapter-03 VAL only), the
  pre-registered band boundaries (search/ranking/gate, 50/30/20 shape), and cites the
  frozen registry hash — it never re-derives or proposes threshold values (X, F_floor,
  gate threshold are pinned; L-12 clause). Per-candidate quality gates are forbidden:
  every grid cell enters the universe. Spec: `docs/references/xena-lane.md`.
- Operator questions follow the plain-language elicitation standard: one plain sentence per
  question, concrete options, one-line consequences, recommendation marked. If anything in
  the request is ambiguous, ask BEFORE writing the design — never resolve ambiguity silently.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config (`research-pipeline/_pipeline-config.md`) | Always |
| `references/design-requirements.md` (bundled) | Always — the mandatory declarations |
| `references/methods-catalog.md` (bundled) | Method selection |
| `docs/knowledge-base/` | Always, before designing |
| `docs/signal-registry/` | Registry preconditions |
