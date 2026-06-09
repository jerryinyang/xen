# Phase 007 — AVWAP Tradability & Edge Isolation

**Checkpoint type:** Research phase design.
**Date finalized:** 2026-06-09.
**Status:** ACTIVE — design opened; no Phase 007 result exists.
**Candidate family:** `CF-AVWAP-001` — Anchored VWAP on regime pivots (continued
from Phases 004/005/006).
**Follows:** `2026-06-08-006-avwap-evaluation-correction` (COMPLETED —
EVAL_SUPPORTED, cTrader-confirmed).

## 1. Provenance

Phase 006 closed `EVAL_SUPPORTED`/cTrader-confirmed: under a fit-for-purpose
event-level yardstick (EXP-027 METHOD_VALID), the faithful selective AVWAP strategy
shows positive per-event matched-control excess on all three domains
(+5.78 / +23.38 / +69.02 bps on 5m/1h/4h, Holm p=0.003), and the corrected
pyramid-inclusive C# robot reproduces it bar-by-bar on cTrader (EXP-029 CONSISTENT).

Two facts bound that result and define this phase:

1. **The Phase 006 edge is gross of costs.** Every EXP-028/029 number is a
   matched-control *excess*, not a net P&L. EXP-023's per-bar `REFUTED` — which
   included "~0/negative net expectancy from trend-change exits + cost" — was **not**
   overturned; it was screened through a non-substitutable yardstick. Whether the
   per-event edge survives realistic costs is **unresolved**, and the two yardsticks
   currently point opposite directions (event-level EVIDENCE_FOR vs per-bar REFUTED).
2. **The edge is not yet decomposed.** The reported excess is the *whole strategy*
   (AVWAP bounce entry timing + EXP-022 band-target/trend-change exit). How much is
   entry-timing vs exit-rule is unknown; the retained EXP-024 finding (trend-change
   exits cut losers, not winners) suggests the exit may be doing material work.

This phase answers tradability and decomposes the edge, before any holdout release.

## 2. Objective

1. **Tradability (EXP-030):** determine whether the Phase 006 per-event edge survives
   an explicitly-scoped, predeclared cost/slippage model on the analysis set, on each
   domain. This is the gate that decides whether `CF-AVWAP-001` has a tradable
   candidate at all.
2. **Edge isolation (EXP-031):** decompose the measured excess into entry-timing and
   exit-rule contributions, to learn *where* the edge lives — information that is
   valuable for subsequent strategies **regardless of the tradability outcome**.

This phase does **not** release the global holdout, sweep parameters, tune any rule
against analysis-set performance, or build new detector/anchor branches. Predeclared
once, measured once. Holdout sealed.

## 3. Dependency structure (LOCKED)

The blocking relationships are fixed for this phase and must not be relaxed without an
operator amendment:

```
EXP-030 (Tradability) ──── HARD GATE ────▶ Holdout release (EXP-032, deferred)
        │
        └── independent of ──┐
                             │  (no blocking either direction)
EXP-031 (Isolation) ─────────┘
```

- **EXP-030 and EXP-031 are mutually independent and may run in parallel.** Neither
  blocks the other.
- **EXP-031 (isolation) does NOT block on EXP-030, and is NOT cancelled by an EXP-030
  failure.** Isolation runs regardless of the tradability verdict. Rationale
  (operator decision, 2026-06-09): the mechanism decomposition is useful information
  for subsequent strategies even if this specific candidate fails on costs — a
  cost-failed strategy that localizes its edge to, say, the exit rule still informs
  future scopes. We deliberately do not throw that information away.
- **EXP-030 (tradability) IS a hard gate for holdout release.** The final 30% global
  holdout is a one-shot resource and is **not** released to confirm a gross edge. A
  holdout-release experiment (provisionally EXP-032) is admissible only if EXP-030
  returns tradability EVIDENCE_FOR on ≥1 domain, and is scoped as its own checkpoint
  with its own governance. It is **deferred out of Phase 007**.

## 4. Scope discipline — what is and is not in scope

**In scope:**
- **EXP-030** — cost/slippage-bearing tradability of the EXP-028 faithful strategy,
  unchanged trade logic, evaluated on the analysis set under a predeclared event-level
  cost model.
- **EXP-031** — entry-timing vs exit-rule contribution decomposition of the same
  faithful strategy.

**Out of scope (carried, not worked):**
- **Holdout release (EXP-032)** — deferred; gated on EXP-030; separate checkpoint +
  governance.
- **HYP-001** (direct AVWAP line as support/resistance) — remains **open and
  explicitly NOT confirmed** by EXP-028/029 (see §8). Held as a parallel/fallback
  mechanism branch; not worked here.
- Stage-C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) — deferred; reconsidered if
  EXP-030 fails (family-review path).
- `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` parameter branches — remain deferred/registered.

## 5. Phase structure (EXP-030 ∥ EXP-031, gated holdout)

```
EXP-030  Cost-bearing tradability of the faithful AVWAP strategy
         -> does the per-event edge survive a predeclared cost/slippage model
            on each domain? (analysis set; gross excess -> net)
EXP-031  Edge isolation: entry-timing vs exit-rule contribution
         -> where does the measured excess live? (runs regardless of EXP-030)
[EXP-032 Holdout release — DEFERRED, gated on EXP-030 EVIDENCE_FOR]
```

### EXP-030 — Cost-bearing tradability

- **Falsifiable question:** under a predeclared per-event cost/slippage model, does the
  faithful selective AVWAP strategy retain positive **net** per-event expectancy
  (and/or net equity advantage over the exposure-matched baseline) on at least one
  domain, on the first-70% analysis set?
- **The key scoping decision — the cost model — is the part requiring the most care.**
  Do **not** re-use the frozen per-bar suite (wrong activity envelope — the EXP-023
  trap), and do **not** naively subtract a flat constant from the event excess. The
  cost model must be event-level and predeclared: per-event entry+exit cost charged
  once per realized position (including pyramids), spread/commission/slippage
  components stated explicitly with their per-instrument values and sources, applied
  to the EXP-028/029 lifetime estimand. Sub-decisions to fix before measurement:
  whether slippage scales with band-width/ATR; how pyramid legs are charged; the
  net-expectancy denominator; the zero-baseline / break-even behavior.
- **Faithfulness requirement:** trade logic identical to EXP-028; the *only* addition
  is the cost layer. No parameter change is a tuning lever.
- **Anti-trap guard:** a 5m domain that goes net-negative is an expected, informative
  outcome (the +5.78 bps gross is likely below cost), not a failure of the experiment.

### EXP-031 — Edge isolation (entry-timing vs exit-rule)

- **Falsifiable / exploratory question:** of the measured per-event excess, how much is
  attributable to AVWAP bounce **entry timing** versus the EXP-022 band-target/
  trend-change **exit rule**? Predeclared decomposition (e.g. entry-only vs
  control-exit, exit-rule-on-control-entries) using the frozen EXP-027 inference tail.
- **Runs regardless of EXP-030.** Its value is mechanism information for future scopes;
  it is not gated by, and does not gate, tradability.
- **Faithfulness:** the decomposition legs are predeclared, structural, measured once —
  no sweep, no post-result reselection of which leg "counts."

## 6. Multiplicity & registry gate

The first Phase 007 artifact is a registry amendment in
`docs/signal-registry/multiplicity-registry.md` that:

1. opens a Phase 007 batch section and records the Phase 006 close
   (EVAL_SUPPORTED/cTrader-confirmed);
2. registers **EXP-030** as a cost-bearing tradability screen of `CF-AVWAP-001`
   (HYP-004 lineage) — it does **not** consume a new candidate-family slot; it
   evaluates the already-registered baseline under an added cost layer;
3. registers **EXP-031** as an edge-decomposition diagnostic (no candidate-screening
   slot);
4. records **EXP-032 holdout release** as DEFERRED + gated, not yet registered.

## 7. Methodological guardrails

- The final 30% global holdout is excluded from all Phase 007 analysis. No holdout
  release in this phase.
- Time bars order by `CloseTime`; cross-view alignment is by timestamp, never bar
  index. All outcomes use **real OHLC** prices only.
- **No tuning against Phase 007 outcomes.** The cost model and decomposition legs are
  predeclared and frozen before reading results; strategy parameters are unchanged
  from the EXP-028 baseline. No threshold/metric/parameter sweep; no post-result
  reselection.
- A net-negative tradability result (EXP-030) or any isolation result (EXP-031) is a
  valid outcome, not permission to try another cost model or another strategy variant.
- The cost model must be event-level and in-envelope for the ~6%-active signal; the
  frozen per-bar suite is **not** the tradability vehicle.

## 8. HYP-001 disposition (open; explicitly NOT confirmed)

The Phase 006 result does **not** confirm or imply HYP-001 (the AVWAP line as direct
support/resistance), and this phase does not close it. Recorded reasoning:

- The strategy edge is **conditioned on the bounce event** (the EXP-020 bounce
  definition already encodes the reaction), so it cannot estimate the line's S/R
  property — that needs `P(reaction | approach)`, including the approaches-that-did-not-
  react denominator the strategy never observes. Inferring S/R from triggered events is
  the EXP-025 conflation.
- A good **trigger location** is not a **price barrier**: the lifetime excess could be a
  continuation/regime effect with the line playing no reflective role. The strategy
  working does not logically require line-S/R.

**Testable framing (for a future HYP-001 experiment, not this phase):** event = *line
approach* defined independently of the bounce trigger (price comes within ε of the
line, in band-width/ATR units); outcome = a **bounce**, i.e. price exits the
ε-neighborhood of the line in the **direction opposite to its entry** (entered
bearish/falling into the line → exits bullish/rising, and vice-versa — the reaction is
simply the directional inverse of the approach); control = matched non-AVWAP reference
levels at the same distance/regime distribution; HYP-001 holds iff
`P(bounce | approach to AVWAP) > P(bounce | approach to control)`. The bounce-trigger
definition must appear nowhere in the metric — the event is the *approach*, not the
triggered bounce.

## 9. Phase outcome criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| TRADABLE | EXP-030 net per-event edge EVIDENCE_FOR on ≥1 domain. | First cost-bearing tradable AVWAP candidate. Holdout-release checkpoint (EXP-032) becomes admissible. EXP-031 mechanism read informs robustness scope. |
| NOT_TRADABLE | EXP-030 net EVIDENCE_AGAINST/INCONCLUSIVE on every domain. | The faithful strategy has real gross edge but no net edge under costs. No holdout release. EXP-031 still delivers mechanism information; pivot to Stage-C branches / HYP-001 / family review. |
| ISOLATION_READ | EXP-031 attributes the excess (entry-dominant / exit-dominant / mixed). | Independent of tradability; feeds future scope design either way. |

## 10. Non-goals

- Holdout release (deferred, gated on EXP-030).
- Parameter sweeps, exit-overlay redesign, detector/anchor branches.
- Re-running EXP-025's confounded HYP-001 metric.
- Any change to the frozen per-bar suite, the frozen EXP-027 method, or their calibration.
- Any use of the global holdout.
