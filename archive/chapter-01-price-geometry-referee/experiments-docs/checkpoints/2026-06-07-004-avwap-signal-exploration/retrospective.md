# Phase 004 - AVWAP Signal Exploration - Retrospective

**Phase number:** 004
**Design finalised:** 2026-06-07
**Retrospective written:** 2026-06-08
**Status:** COMPLETED - Batch 004-A baseline chain executed and governance-reviewed. **Phase outcome: BASELINE_BRANCH_REFUTED** - the first CF-AVWAP-001 branch produced supported component evidence, then failed the full frozen-suite candidate screen.

**Design reference:** [design.md](design.md)
**Registry:** [multiplicity-registry.md](../../../signal-registry/multiplicity-registry.md)
**Candidate family:** `CF-AVWAP-001` - Anchored VWAP on regime pivots
**Experiments:** EXP-020, EXP-021, EXP-022, EXP-023 - see `python/experiments/<ID>/report.md`.

---

## 1. Phase Objective Recap

Phase 004 opened the first real signal-exploration phase after the qualification
suite was frozen and the cTrader strategy-host branch was validated. The phase
had a deliberately narrow first batch:

1. Register exactly one candidate family, `CF-AVWAP-001`, before measurement.
2. Decompose the broad AVWAP thesis into component gates before any full
   strategy screen.
3. Test event-substrate readiness, fixed-horizon bounce reaction, and the
   original band-target/trend-change lifetime method.
4. Only if the component evidence supported proceeding, run the baseline branch
   through the frozen suite using cTrader-emitted real OHLC prices.
5. Keep the final 30 percent global holdout sealed.

The batch was not designed to find the best AVWAP variant. It was designed to
test the registered first branch honestly, record negative outcomes, and prevent
silent parameter or exit-rule search.

---

## 2. Outcomes vs Objectives

| EXP | Role | Verdict | One-line outcome |
| --- | --- | --- | --- |
| EXP-020 | Event-substrate readiness | SUPPORTED_FULL | All 12 instrument/domain cells reportable; all 192 invariant checks pass; deterministic replay matches; all 3 domains ready. |
| EXP-021 | Fixed-horizon bounce reaction | SUPPORTED | Primary 3-bar matched-control effects positive on all domains: +3.8/+9.1/+37.6 bps on 5m/1h/4h, Holm p=0.0003. |
| EXP-022 | Band-target/trend-change lifetime method | SUPPORTED | Event favorable-completion advantage positive on all domains: +23.9/+21.9/+26.4 percentage points, Holm p=0.0003. |
| EXP-023 | Baseline cTrader candidate screen | REFUTED | 12/12 cTrader cells admitted and C# smoke PASS, but 0/12 strict, 0/12 ratified-loose, and 0/12 revised-incremental passes. |

The chain reached the intended terminal screen. The terminal screen was cleanly
negative.

---

## 3. Headline Synthesis

**The AVWAP first branch produced real conditional event evidence, but the
registered baseline did not become a qualifying tradable strategy.**

This is not a contradiction. EXP-021 and EXP-022 asked conditional event
questions: when a bounce event occurs, does price behave better than a matched
non-event control? Both answers were yes. EXP-023 asked a different question:
does the baseline strategy, emitted by cTrader and evaluated on real closes,
qualify under the frozen suite after costs, holding periods, trend-change exits,
and portfolio-fitness rules are imposed? The answer was no.

The baseline branch is therefore refuted; `CF-AVWAP-001` as a candidate family is
not retired. The checkpoint design retired the family only for substrate failure
or both reaction and lifetime operationalizations failing. Neither happened.

---

## 4. What Held

### EXP-020 - substrate readiness

The AVWAP state machine passed the gate that mattered for any later component
study:

- all three domains ready;
- all 12 instrument/domain cells reportable;
- 0 invariant failures across 192 checks;
- deterministic replay matches in 12/12 cells;
- no holdout violation.

This validated the implementation substrate, not market edge. It removed the
possibility that later positive event results were caused by a degenerate event
generator.

### EXP-021 - bounce reaction

The fixed-horizon reaction result was broad and statistically strong:

| Domain | N events | Primary effect | 95% CI | Holm p |
| --- | ---: | ---: | --- | ---: |
| 5m | 16,249 | +3.8 bps | [+3.5, +4.1] | 0.0003 |
| 1h | 1,207 | +9.1 bps | [+5.1, +13.3] | 0.0003 |
| 4h | 246 | +37.6 bps | [+22.3, +52.7] | 0.0003 |

All instrument/direction cells were positive. The result supports the claim that
the bounce event carries directional information relative to same-regime
non-event controls. It does not, by itself, claim tradable P&L.

### EXP-022 - lifetime method

The registered band-target/trend-change lifetime method also held:

| Domain | Event favorable rate | Control favorable rate | Rate difference | Holm p |
| --- | ---: | ---: | ---: | ---: |
| 5m | 68.5% | 44.6% | +23.9 pp | 0.0003 |
| 1h | 67.2% | 45.3% | +21.9 pp | 0.0003 |
| 4h | 67.8% | 41.5% | +26.4 pp | 0.0003 |

Event lifetime expectancy was also positive versus matched controls on every
domain. This cleared the design's `PROCEED_TO_SCREEN` condition together with
EXP-020 and EXP-021.

---

## 5. What Failed

### EXP-023 - baseline strategy screen

The cTrader screen was admissible:

- dependencies 34/34 PASS;
- cTrader cells admitted 12/12;
- candidate/reference same-feed check 12/12 with max OHLC diff 0.0;
- holdout fence respected for candidate and reference in 12/12 cells;
- C# AVWAP transcription smoke PASS on 5m/1h/4h;
- all 12 suite cells reportable;
- no blockers.

The suite result was unambiguous:

| Component | Passes |
| --- | ---: |
| Strict standalone gate stack | 0/12 |
| Ratified-loose / strict-fallback standalone referee | 0/12 |
| Revised portfolio-fitness unit vs Donchian(20) | 0/12 |

The largest standalone point estimate was EURUSD/4h at +0.21 bps, against a 12
bps strict floor and a 1.5 bps loose tau. The largest incremental point was
XAUUSD/4h at +6.05 bps, against a 32 bps incremental floor, with CI lower below
zero. The only positive incremental CI lower was EURUSD/4h at +0.31 bps, still
far below the 32 bps floor. No cell was close to qualification.

The metric book explains the mechanical gap:

- completed target success was high, 60.5%-80.0% by cell;
- across all cells, 20,904 bounce events produced 17,478 entries because 3,426
  pyramid opportunities were skipped while already active;
- favorable target success among completed moves was 69.1%;
- 12.3% of entries exited by trend change;
- model net mean was approximately zero to negative in every domain;
- gross model means were also tiny, from -0.563 to +0.137 bps, so the refutation
  is not just a cost artifact.

The baseline did not turn the event signal into a cost-bearing, continuously held
strategy that clears the frozen floors.

---

## 6. The Guardrails Worked

The phase's process did what it was built to do.

1. **The registry prevented file-drawer drift.** The first candidate family,
   component hypotheses, and full-screen hypothesis were registered before
   measurement. EXP-023's negative result is now recorded in the file-drawer
   ledger rather than disappearing behind new variants.
2. **Component decomposition made the failure interpretable.** A one-shot
   strategy backtest would only have said "AVWAP failed." The chain instead
   says: substrate works, bounce events carry conditional information, lifetime
   completion is favorable, but the baseline position overlay fails under cost,
   holding, trend-change exits, and suite floors.
3. **The cTrader branch behaved as intended.** Strategy generation occurred in
   cTrader; Python ingested and validated. The fixed-Parquet smoke validated the
   AVWAP C# port against the Python reference, and the live run stayed on emitted
   real OHLC.
4. **The frozen suite stayed frozen.** EXP-023 did not change thresholds,
   costs, denominators, reference-book identity, or pass logic after seeing the
   result. The negative is therefore meaningful.
5. **Negative results were handled as results.** The baseline branch was not
   tuned inside EXP-023 after failing. Follow-up work is explicitly routed to new
   scopes.

---

## 7. Caveats Carried Forward

1. **The global holdout remains sealed.** All results are on the first-70%
   analysis slice. No fresh-regime confirmation is claimed.
2. **The baseline was intentionally untuned.** It fixed MA(20,50), typical-price
   AVWAP, `TickVolume ** 0.75`, MAD band multiplier 1.0, and the registered
   lifetime exits. Other AVWAP branches may behave differently, but none may be
   selected silently after this outcome.
3. **The incremental screen is coarse.** The revised portfolio-fitness floors are
   12/16/32 bps on 5m/1h/4h. A smaller marginal edge beyond Donchian(20) would
   not qualify through that unit.
4. **EXP-021/022 are not P&L claims.** They measure conditional event behavior
   against matched controls. They justify a screen; they do not substitute for
   the screen.
5. **Execution realism remains out of scope.** The qualification uses emitted
   real closes and fixed cost assumptions, not fills, spread, slippage, latency,
   or order-type modeling.

---

## 8. Lessons Learned

1. **Event quality and strategy quality are separate claims.** A high conditional
   hit rate can vanish once positions are held through full lifecycle rules and
   evaluated under cost. Future scopes should keep this distinction explicit.
2. **Exit mechanics are the binding AVWAP question now.** The event signal was
   not the obvious failure point. Trend-change exits, active-bar cost, sparse
   exposure, and skipped pyramid opportunities are where the baseline lost the
   event advantage.
3. **Component gates are worth the extra work.** Because EXP-020-022 were run
   first, EXP-023's refutation is not a black box. The failure is localized to
   the baseline position/exit overlay and suite qualification, not to substrate
   validity or event existence.
4. **The frozen-suite floors provide a useful brake.** Small positive points
   appeared in a few 4h incremental cells, but the suite prevented reading
   sub-floor, weakly uncertain effects as qualification.
5. **The file-drawer ledger is now operational.** Phase 004 has its first full
   candidate-screen negative recorded. That is the discipline the registry was
   created to enforce.
6. **"Not retired" must not mean "keep searching in-place."** The family remains
   open only through new predeclared branches. The baseline itself is not a
   parameter-tuning sandbox.

---

## 9. Phase Verdict vs Design Criteria

Mapping to [design.md](design.md) section 8:

- **PROCEED_TO_SCREEN - reached.** EXP-020 supported substrate readiness, EXP-021
  and EXP-022 completed with benchmarked Evidence-FOR results, and governance
  approved EXP-023.
- **NARROW_DOMAINS - not triggered.** EXP-020 supported all three domains with
  all four instruments reportable.
- **COMPONENT_REFUTED - not triggered.** There was no substrate failure, and both
  reaction and lifetime operationalizations supported proceeding.
- **INCONCLUSIVE - not triggered.** Coverage and uncertainty were sufficient for
  all four experiments, and EXP-023 had no blockers.

The design criteria governed whether the baseline should be screened. The screen
then produced the terminal Batch 004-A result: **BASELINE_BRANCH_REFUTED**. That
is a narrower conclusion than family retirement and a stronger conclusion than
inconclusive.

---

## 10. Recommended Next Direction

Do not tune or revise the EXP-023 baseline inside the completed experiment.
Future work must open a new scoped experiment under the registry.

If the operator wants to stay within AVWAP, the highest-information follow-up is
probably an explicitly scoped `CF-AVWAP-001/EXIT` diagnostic or candidate branch,
because EXP-023 points to trend-change and cost drag as the binding failure.
That follow-up must define concrete exit rules before measurement and must not
reuse EXP-023 outcomes to sweep exits silently.

Other registered branches remain legitimate alternatives:

- `CF-AVWAP-001/LB` - Line Break direction regime detector;
- `CF-AVWAP-001/MB` - Market Bias regime detector;
- `CF-AVWAP-001/ATR` - ATR pivot-reversal regime detector;
- `CF-AVWAP-001/ALPHA` - predeclared tick-volume exponent sensitivity;
- `CF-AVWAP-001/BAND` - predeclared band-multiplier sensitivity;
- `CF-AVWAP-001/MA-DOMAIN` - domain-scaled MA period map, once specified;
- `CF-AVWAP-001/XTF` - cross-timeframe relationship and granular-entry refinements.

Each needs one falsifiable scope, pre-execution governance, and registry status
before measurement. The final 30 percent global holdout remains sealed.

---

## 11. Final Disposition

Phase 004 Batch 004-A is complete:

- AVWAP substrate readiness: supported.
- AVWAP fixed-horizon bounce reaction: supported.
- AVWAP lifetime method: supported.
- AVWAP baseline full candidate screen: refuted.

This is the first real signal-exploration cycle run through the frozen
qualification suite and programme-level file-drawer discipline. The baseline
branch is closed negative; the family remains open only through new registered,
predeclared branches.
