# Phase 005 - AVWAP Exit Design & Branch Exploration

> **HALTED 2026-06-08 — superseded.** This phase was stopped before Stage B/C
> after operator review found its diagnosis inherited an unexamined premise: a
> ~6 %-active event signal was being screened/diagnosed through a per-bar
> continuous-position referee calibrated only for ≥80 %-active series. See
> [retrospective.md](retrospective.md) and the root-cause review
> `docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.
> Superseded by `2026-06-08-006-avwap-evaluation-correction`. Stage B (`/EXIT`,
> EXP-026) is shelved; Stage C (`/LB` `/MB` `/ATR` `/ANCHOR`) is deferred. The
> design below is retained as-written for the record.

**Checkpoint type:** Research phase design.
**Date finalized:** 2026-06-08.
**Status:** **HALTED 2026-06-08** (was ACTIVE) — see banner above and retrospective.
**Candidate family:** `CF-AVWAP-001` - Anchored VWAP on regime pivots (continued from Phase 004).

## 1. Provenance

Phase 004 Batch 004-A closed **BASELINE_BRANCH_REFUTED**:

- EXP-020 SUPPORTED_FULL - the AVWAP event substrate is deterministic, look-ahead-safe, and non-degenerate.
- EXP-021 SUPPORTED - bounce events carry real fixed-horizon reaction (+3.8 / +9.1 / +37.6 bps on 5m/1h/4h).
- EXP-022 SUPPORTED - the band-target/trend-change lifetime method shows a favorable-completion advantage (+23.9 / +21.9 / +26.4 pp).
- **EXP-023 REFUTED** - the always-on baseline overlay passed **0/12** frozen-suite cells; standalone and incremental effects sit far below every floor.

The family is **not retired** (design §8 of Phase 004 retired it only on substrate failure or both reaction *and* lifetime failing - neither happened). Follow-up requires new registered, predeclared scopes.

Two observations from EXP-023 drive this phase:

1. **The conditional event edge does not survive as a continuously held position.** A 60-80% favorable-target rate collapses to ~0-to-negative net realized expectancy.
2. **The collapse is not only a cost artifact.** Gross model means were also tiny (-0.563 to +0.137 bps) versus the EXP-021 reaction of +3.8/+9.1/+37.6 bps. The edge dissipates *before* cost, somewhere between the event window and the held position.

The gaps analysis `docs/code-reviews/2026-06-08-avwap-original-vs-experiment-gaps.md` adds:

- The foundational claim that **price reacts at the AVWAP line as support/resistance** was never tested directly; EXP-021/022 tested bounce-*continuation* and target-*completion* instead (gap #4).
- The baseline anchor is a **running segment extreme**, not a structural/significant pivot (gap #1).
- Only **1 of 4 registered trend detectors** has been built (gap #2).

## 2. Objective

Localize *why* a real conditional event edge fails as a held strategy, convert that finding into an empirically-grounded exit operationalization, screen it once through the frozen suite, and only then explore the deferred AVWAP design branches - all under unbroken anti-overfitting discipline.

This phase does **not** sweep parameters and does **not** tune any rule against analysis-set P&L. Exit rules are derived from event *structure*, predeclared, and measured once.

Diagnostic measurements may motivate a later candidate rule, but they do not themselves qualify a tradable variant. Any `/EXIT` rule derived from EXP-024 must either use a predeclared design/evaluation split inside the first-70% analysis set, with candidate-screen evaluation on untouched in-analysis test rows, or be labelled exploratory rather than qualifying.

## 3. Phase Structure (Stage A -> B -> C)

The phase runs in three dependent stages. Each later stage is conditional on the prior stage's result.

```
Stage A  Diagnosis (Python-only, no suite, no screening slot)
         -> where does the EXP-021 edge go, and does price respect the line?
Stage B  Empirically-designed EXIT screen (cTrader -> frozen suite)
         -> only if Stage A says a holding/exit fix is plausible
Stage C  Branch exploration (deferred detectors / anchor quality)
         -> detector and anchor-quality alternatives, each its own chain
```

### Stage A - Diagnosis

Diagnostic, descriptive, look-ahead-safe. Reuses the validated EXP-020 event substrate and EXP-022 lifetime tables. Runs no qualification suite, emits no pass/fail verdict, and **consumes no candidate-screening multiplicity slot**. Its job is to make Stage B's exit design evidence-driven rather than guessed.

| EXP | Title | Falsifiable question | Output |
| --- | --- | --- | --- |
| EXP-024 | AVWAP Event-Edge Dissipation Decomposition | Between EXP-021's fixed-horizon reaction and EXP-023's ~0 realized gross expectancy, is the edge lost to **(a)** holding past the reaction horizon / trend-change truncation (a fixable exit problem), or **(b)** entry/position-construction dilution so severe that no scoped bounded-hold exit remedy is justified for the always-on overlay? | Signed-gross-return-by-holding-horizon decay curve vs the EXP-021 reaction; trend-change-exit return distribution (does it cut winners or save losers?); holding-period and exposure/flat-fraction distributions; pre-cost vs cost attribution; explicit (a)/(b)/inconclusive verdict under fixed criteria. |
| EXP-025 | AVWAP Line Support/Resistance Direct Test (gap #4) | Does price measurably react *at* the AVWAP line itself (reduced penetration / direction-signed reversal at the line) beyond a look-ahead-safe matched control, independent of the bounce-trigger continuation already shown in EXP-021? | Reaction-at-line metric vs matched control by instrument/domain/direction; tests whether the bounce mechanism rests on a real S/R effect or is a regime-gated continuation artifact. |

**Sequencing within Stage A:** EXP-024 is the binding diagnostic for exit design and runs first. EXP-025 tests the foundational thesis and may run in parallel or immediately after; it is not a gate on EXP-024 but its result conditions how much to invest in this family vs alternative operationalizations.

**Scope discipline:** EXP-024 and EXP-025 are each one organizing question. If either grows a second qualification-style claim, split it. Neither may load the holdout.

**EXP-024 fork rule:** the EXP-024 scope must keep the horizon grid fixed before measurement, compare absolute gross bps against the frozen ratified-loose floors (5m 0.5, 1h 2, 4h 8 bps), use common completed-event denominators for bounded-vs-lifetime contrasts, and avoid percentage improvement over a zero baseline. Fork (a) requires a floor-clearing positive bounded-hold edge and a material advantage over the lifetime hold on the common event set. Fork (b) requires every adequately powered scoped horizon to remain below its floor. High-but-underpowered or floor-straddling horizons are INCONCLUSIVE, not fork (b).

**EXP-025 minimum scope requirements:** before implementation, EXP-025 must define exactly one primary reaction-at-line metric, its event denominator, matched-control dimensions, horizon, zero-baseline behavior, and reportability rules. Secondary penetration/reversal diagnostics are allowed only if bounded in the complexity budget and cannot become post-hoc primary criteria.

### Stage B - Empirically-designed EXIT screen

Opens **only if** EXP-024 returns fork **(a)** under its fixed criteria (or a mixed result where governance explicitly scopes Stage B to the supporting domain(s)). If EXP-024 returns fork **(b)**, Stage B is skipped and the phase routes directly to Stage C (or to a redirect retrospective), because the scoped bounded-hold exit remedy is not justified for the always-on overlay.

| EXP | Title | Question | Requires |
| --- | --- | --- | --- |
| EXP-026 | `CF-AVWAP-001/EXIT` Candidate Screen | Does a single principled exit overlay, derived from EXP-024 event structure and predeclared before measurement, let the AVWAP baseline qualify under at least one frozen-suite component? | Registry amendment registering `/EXIT` with concrete rules; cTrader strategy-host generation; frozen suite unchanged. |

**The knife-edge (binding governance constraint):** the exit rule must be *derived from the diagnostic's structural findings* by a predeclared mapping - **not** selected to maximize analysis-set P&L. If EXP-024 identifies a measured peak horizon, that value may seed EXP-026 only through an explicit dated registry amendment and an EXP-026 scope that states the design/evaluation split or exploratory status. The rule is predeclared in the EXP-026 scope, registered, and measured once. No exit-parameter sweep, no post-result reselection. If more than one *structurally distinct* exit mechanism is warranted, each is a separately registered hypothesis with its own multiplicity slot - never a parameter grid.

### Stage C - Branch exploration (deferred design branches)

Opens after Stage A/B deliver their lessons, so detector/anchor priority is informed rather than arbitrary. Each branch is its own predeclared chain. The EXP-020/021/022 machinery is reusable (only the regime detector or anchor rule changes), so these chains are cheaper than the Phase 004 baseline chain - a detector branch may combine substrate-readiness + reaction + screen into a short chain rather than four separate experiments only if the scope exposes sequential stop gates. Readiness and look-ahead safety are admission gates; reaction evidence is a component gate; candidate screening starts only after those gates pass. If the branch asks more than one market-edge question, split it before implementation.

Registered branches in scope for Stage C (priority set when the stage opens):

- `CF-AVWAP-001/LB` - Line Break direction regime detector (gap #2).
- `CF-AVWAP-001/MB` - Market Bias regime detector (gap #2).
- `CF-AVWAP-001/ATR` - ATR pivot-reversal regime detector (gap #2).
- `CF-AVWAP-001/ANCHOR` (new) - significant-pivot anchor vs running-extreme anchor (gap #1). Requires a registry addition; the anchor rule is distinct from the trend detector.

**Excluded from Phase 005** (operator decision, 2026-06-08): `CF-AVWAP-001/ALPHA` (tick-volume exponent) and `CF-AVWAP-001/BAND` (band multiplier). The Phase 004 failure was not localized to these parameters, so parameter sensitivity is low expected information at this stage and is deferred.

## 4. Multiplicity & Registry Gate

This phase continues `CF-AVWAP-001`. The first Phase 005 artifact is a **registry amendment** in `docs/signal-registry/multiplicity-registry.md` that:

1. opens a Phase 005 batch section;
2. registers EXP-024 and EXP-025 as diagnostic (no candidate-screening slot consumed; no qualification verdict);
3. registers the planned `CF-AVWAP-001/EXIT` hypothesis (HYP-005) with the note that its concrete exit rules will be fixed in the EXP-026 scope and amended in before measurement;
4. registers the Stage C detector/anchor branches as planned, each requiring its own dedicated scope before measurement;
5. records that `/ALPHA` and `/BAND` are deferred out of Phase 005.

No cTrader candidate screen (Stage B/C) is admissible until its candidate hypothesis, parameter branch, and EXP-ID appear in the registry first. Negative, blocked, and inconclusive outcomes stay in the file-drawer ledger.

## 5. Methodological Guardrails

- The final 30 percent global holdout is excluded from all Stage A/B/C analysis.
- Time bars order by `CloseTime`; cTrader strategy runs emit `SourceCloseTime`; cross-view alignment is by timestamp, never bar index.
- All reaction, lifetime, and strategy outcomes use **real OHLC** prices only.
- Diagnosis (Stage A) is Python-only; candidate screening (Stage B/C) must use the cTrader strategy-host branch and the **unchanged** frozen suite (strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised portfolio-fitness unit; floors 1/4/12, 0.5/2/8, 12/16/32 bps).
- **No tuning against Phase 005 outcomes.** Exit rules and detector/anchor definitions are derived from structure and predeclared, then measured once. No threshold, exit, detector, or anchor sweep; no post-result variant reselection.
- A failed diagnostic, exit screen, or branch screen is a valid result, not permission to silently try a new variant.
- Stage B is gated on the EXP-024 fork; Stage C priority is informed by Stage A/B but each branch stands or falls on its own predeclared scope.

## 6. Phase Outcome Criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| EXIT_QUALIFIES | EXP-024 returns fork (a); EXP-026 passes >=1 frozen-suite component on supported domains under predeclared rules. | First qualifying AVWAP candidate; proceed to robustness / fresh-regime planning (holdout still sealed until a separate confirmation phase is designed). |
| EXIT_REFUTED | EXP-024 returns fork (a) but EXP-026 fails all suite components. | `/EXIT` branch closed negative; route to Stage C detector/anchor branches. |
| OVERLAY_WRONG_VEHICLE | EXP-024 returns fork (b): no scoped bounded-hold exit remedy is justified for the always-on overlay. | Skip EXP-026; either redirect to a non-always-on operationalization (new scope) or proceed to Stage C with that constraint recorded. |
| DETECTOR/ANCHOR_RESULT | Each Stage C branch yields SUPPORTED / REFUTED / INCONCLUSIVE on its own predeclared criteria. | Registered in the ledger; informs whether the family continues. |
| FAMILY_REVIEW | If EXIT and all attempted Stage C branches close negative without a qualifying cell. | Operator review of whether `CF-AVWAP-001` should be retired or carried with a narrower thesis. |

## 7. Non-Goals

- Parameter-sensitivity sweeps (`/ALPHA`, `/BAND`) - deferred out of Phase 005.
- Exit-parameter optimization or post-result exit reselection.
- Multi-signal reference books beyond the existing dogfood reference setup.
- Execution-realism research (fills, spread, slippage, latency) as qualification inputs.
- Cross-timeframe (`/XTF`) and domain-scaled MA maps (`/MA-DOMAIN`) - remain registered but out of this phase's scope.
- Any use of the global holdout.

## 8. Immediate Next Step

1. Amend `docs/signal-registry/multiplicity-registry.md` to open the Phase 005 batch and register EXP-024/025 (diagnostic) plus the planned `/EXIT` and Stage C branches.
2. Run the research pipeline for **EXP-024** (Stage 1 scope first): the dissipation decomposition is the binding diagnostic and gates Stage B.
3. EXP-025 (line S/R direct test) follows or runs alongside.
4. Hold Stage B/C until Stage A delivers its fork verdict and exit-design inputs.
