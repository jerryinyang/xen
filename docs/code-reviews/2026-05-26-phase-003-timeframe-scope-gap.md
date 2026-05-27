# Phase 003 Scope Gap Review: ICT Concepts Tested at 1-Minute Resolution

**Review date:** 2026-05-26  
**Review type:** Methodology scope gap analysis  
**Scope:** Phase 003 experiment design (EXP-012 through EXP-028)  
**Raised at:** Phase 003 retrospective synthesis, prior to Phase 004 design finalization  

---

## 1. Summary

All Phase 003 ICT component experiments detected and evaluated structural features — FVG/IFVG zones, displacement candles, breaker order blocks, and sweep events — at 1-minute bar resolution. ICT methodology as practiced applies these structural concepts on 15-minute to 4-hour timeframes, using shorter timeframes only for entry trigger precision. Testing structural ICT concepts at 1-minute resolution produces artificially high event counts, low per-event structural significance, and confirmation windows that do not correspond to the conceptual definitions. Several Phase 003 conclusions may be partially or wholly artifacts of this resolution mismatch rather than genuine evidence about the ICT concepts under study.

This document identifies which experiments are affected, grades the severity of the resolution impact on each, and describes the pre-phase experiment plan that Phase 004 uses to assess whether the gap materially changes the findings before branch work proceeds.

---

## 2. Domain Context

ICT (Inner Circle Trader) multi-timeframe analysis operates on a defined timeframe hierarchy:

| Role | Typical Timeframes | Content |
| --- | --- | --- |
| Structural bias and liquidity identification | Daily, 4-hour | PDH/PDL, weekly highs/lows, premium/discount zones, major order blocks |
| Signal generation | 1-hour, 30-minute, 15-minute | FVGs, IFVGs, breaker blocks, displacement, market structure shifts |
| Entry trigger | 5-minute, 1-minute | Precise entry candle, second-candle-open timing |

This hierarchy is not a stylistic preference. It is functional: on 1-minute bars, candle bodies are small, gaps are frequent micro-artifacts of short bursts, and structural patterns like breaker blocks and FVGs reflect noise rather than supply/demand zones that liquidity providers defend. On 15-minute bars, each candle aggregates 15 minutes of price activity; an FVG at that resolution represents a genuine market imbalance of meaningful duration.

Phase 003 applied structural signal detection at 1-minute throughout. Liquidity level identification (PDH/PDL/ONH/ONL from EXP-014) is resolution-independent because these are daily levels — unaffected. Every other structural detector ran at 1-minute.

---

## 3. Impact by Experiment

### 3.1 EXP-014 — PDH/PDL/ONH/ONL Reproducibility

**Impact: None.**

Daily liquidity levels are computed from daily sessions regardless of detection resolution. The train/test availability findings (0.989–1.000) are valid at any detection timeframe.

### 3.2 EXP-015 — Sweep Reversal Behavior

**Impact: Low to moderate.**

Sweep detection — first 1-minute bar close that breaches a daily level and then closes back — is the highest-resolution detection that makes sense for a daily structural level. Detecting sweeps on 15-minute bars changes the event definition (a 15-minute bar body must breach and reclaim the level), producing fewer, higher-significance events. Whether the refutation holds at 15-minute is unknown.

The EURUSD Test partial positive (+0.134, CI [0.001, 0.267]) is the most interesting open question: does sweep reversal evidence improve at 15-minute, where each detected event represents a 15-minute candle rejecting a daily level? EXP-030 tests this directly.

### 3.3 EXP-018 — Displacement Confirmation

**Impact: Moderate.**

Displacement was defined as the first 1-minute candle whose body size exceeds 1.5× the prior 100-bar median absolute body size. At 1-minute resolution, 100 bars is approximately 1.7 hours. The threshold selected for standard aggressive 1-minute candles, which are common during news events, session opens, and trend continuations. Retention was 82–87% across instruments, indicating the filter was not very selective.

At 15-minute resolution, the same body threshold applied to 15-minute candles is substantially more demanding: a 15-minute candle's body must exceed 1.5× the prior 100-bar median (approximately 25 hours of trading history). This threshold would fire less frequently, and each displacement event would represent a genuinely powerful 15-minute move. The 82–87% retention rate observed at 1-minute would likely drop considerably.

### 3.4 EXP-020 / EXP-021 — FVG/IFVG Detection and Entry Quality

**Impact: High.**

This is the most severely affected experiment group.

**FVG count at 1-minute:** EXP-020 found EURUSD with 76,629 FVGs and 65,339 IFVGs in the analysis set. At 1-minute resolution, the FVG pattern (bar `i` creates a gap with bar `i-2`) fires whenever any brief liquidity imbalance produces a 1-minute wick gap. This is a structural property of 1-minute data: rapid price moves at news events, session opens, or short-term order flows all produce momentary gaps that close within minutes. These are not the supply/demand imbalances that ICT FVG analysis is designed to detect.

**Inversion rate at 1-minute:** The 84–85% IFVG inversion rate (FVG close-through within 120 bars) is consistent with 1-minute resolution. A 120-bar window at 1-minute = 2 hours. Almost all 1-minute micro-gaps are revisited within 2 hours simply because price is mean-reverting at that granularity. The inversion rate is not measuring whether liquidity was genuinely rebalanced; it is measuring whether price returned to any point within a 2-hour window, which it usually does.

**Consequence for EXP-021:** The IFVG confirmation layer in EXP-021 retained nearly the full displacement event set (7 of 8 instrument-segment rows had identical counts). This is consistent with a 1-minute artifact: if almost every FVG inverts within 120 bars, then after any displacement there is almost always a recently formed IFVG nearby, making the confirmation essentially unconditional.

At 15-minute resolution:
- FVG count would fall by roughly an order of magnitude (each 15-minute gap represents a genuine imbalance).
- The 120-bar IFVG window at 15-minute = 30 hours of trading time, covering approximately 2 trading days. A genuine structural IFVG at this resolution either gets revisited within 2 days (in which case it can serve as confirmation) or it does not (in which case it is a clean rejection signal).
- The inversion rate would likely drop materially, potentially making the existing IFVG rule selective without any definition change.

### 3.5 EXP-022 / EXP-023 — Breaker Reproducibility and Trade Quality

**Impact: High.**

Candidate A's definition — the last opposite-direction 1-minute candle within a 30-bar lookback window preceding the displacement — defines the breaker boundary from a single 1-minute candle body. At 1-minute resolution, this lookback spans 30 minutes of recent price action. The "order block" boundary is set by a minute-scale candle that may have no structural significance.

At 15-minute resolution, the same 30-bar lookback spans 7.5 hours. The last opposite-direction 15-minute candle within that window represents a meaningful supply or demand candle — the kind of structural reference that ICT breaker theory describes. The breaker boundary price would be set from a candle with actual structural weight.

The USTEC Candidate A positive in EXP-023 (+1.756R vs displacement -2.414R on test) is the single most important number in Phase 003. Whether this survives at 15-minute is critical. Two interpretations are possible:

1. The positive reflects genuine USTEC breaker structure that will persist or strengthen at 15-minute because the breaker boundaries are more meaningful.
2. The positive is a 1-minute artifact — the 30-minute lookback happened to capture useful recent structure in USTEC specifically, and at 15-minute the events are too sparse or the definition no longer applies cleanly.

EXP-031 distinguishes these. Until it runs, the USTEC result should be treated as conditional on resolution.

### 3.6 EXP-013 — Macro Window Characterization

**Impact: Low, but for a different reason.**

Macro windows are defined in real clock time (e.g., AM1 07:50–08:10 = 20 minutes). At 15-minute bar resolution, the 20-minute AM1 window contains approximately 1–2 complete 15-minute bars, making statistical analysis of window-level behavior nearly impossible. The EXP-013 refutation at 1-minute is arguably the most resolution-appropriate test for a time-defined window concept. Testing macro windows at 15-minute would not produce better evidence; it would produce sparser evidence with wider intervals. The refutation stands.

### 3.7 EXP-016 — Macro Window Interaction with Sweep Outcomes

**Impact: Not incremental.**

EXP-016 was underpowered by the matched-control design, not by resolution. The inside-macro-window sweep counts were too small (EURUSD Test: 24, BTCUSD Test: 21) regardless of bar resolution. A 15-minute rerun would produce equal or fewer matched events. Not a productive avenue.

---

## 4. Summary Table

| Experiment | Concept | Resolution Impact | Phase 004 Action |
| --- | --- | --- | --- |
| EXP-014 | PDH/PDL/ONH/ONL levels | None | No rerun needed |
| EXP-015 | Sweep reversal | Low-moderate | EXP-030 retests at 15-minute |
| EXP-018 | Displacement confirmation | Moderate | EXP-031 tests 15-min displacement as part of USTEC chain |
| EXP-020/021 | FVG/IFVG | High | EXP-029 tests 15-min selectivity; EXP-035 uses finding |
| EXP-022/023 | Breaker | High | EXP-031 retests USTEC breaker chain at 15-minute |
| EXP-013 | Macro windows | Low (different reason) | No rerun; refutation holds |
| EXP-016 | Macro-sweep interaction | Not resolution-driven | No rerun; design was underpowered |

---

## 5. Pre-Phase Plan

Phase 004 introduces three targeted pre-phase experiments before the branch work begins. They are the minimum necessary to determine whether Phase 003 conclusions are resolution-stable.

### EXP-029: 15-Minute FVG/IFVG Selectivity Check

Run the existing FVG/IFVG detector (same three-candle rule and 120-bar lifecycle as EXP-020) on synthetic 15-minute OHLC bars generated from 1-minute base data. Measure IFVG inversion rate and FVG count across all four instruments.

**Key question:** Does the inversion rate drop materially from 84–85 percent? If yes, the non-selectivity problem is a resolution artifact, and Branch B can start from the existing rule at 15-minute rather than redesigning the rule definition from scratch.

### EXP-030: 15-Minute Sweep Reversal Behavior

Apply the EXP-015 sweep/breach framework to 15-minute bars using the same PDH/PDL/ONH/ONL level definitions (EXP-014 levels are resolution-independent). Measure sweep vs. breach 60-minute reversal probability difference across all four instruments.

**Key question:** Does the EXP-015 refutation replicate at 15-minute, or does the sweep reversal pattern strengthen when each detected event represents a full 15-minute candle rejecting a daily level? The EURUSD partial positive is the most important sub-result to watch.

### EXP-031: 15-Minute USTEC Breaker Chain

Apply the full sweep → displacement → Candidate A breaker chain to 15-minute USTEC bars. Compare trade quality outcomes to Phase 003 EXP-023 at 1-minute.

**Key question:** Does the USTEC Candidate A positive survive at 15-minute? If yes, Branch A is resolution-robust and likely reflects genuine structure. If no, the Phase 003 result was a 1-minute artifact and Branch A's rationale must be revised.

**Event count caveat:** USTEC trades approximately 390 minutes per day (26 fifteen-minute bars). After the analysis-set holdout exclusion and train/test split, feasible Candidate A breaker events at 15-minute may be significantly fewer than the 205/86 train/test counts from EXP-022 at 1-minute. If event floors are not met, EXP-031 documents this as a resolution cost and the reflection directive accounts for it.

---

## 6. Mid-Checkpoint Reflection Gate

After EXP-029, EXP-030, and EXP-031 complete, a reflection document issues a directive from the decision matrix in the Phase 004 design before any Phase 004B scope is written. The two most consequential outcomes are:

**If EXP-029 shows material inversion rate drop:** Branch B's EXP-035 redesign exercise may be unnecessary. A timeframe switch alone could solve the selectivity problem. This is a positive finding that simplifies Phase 004B.

**If EXP-031 shows USTEC positive disappears at 15-minute:** Branch A loses its primary evidence base. The reflection must decide whether to close Branch A, reframe it (e.g., explicitly 1-minute-only with a documented domain caveat), or replace it with whatever EXP-030 finds. This is the highest-stakes pre-phase outcome.

---

## 7. What This Gap Does Not Invalidate

Phase 003 completed with correct governance, no holdout violations, and clean pre/post-execution verdicts. The timeframe gap is a scope limitation, not a procedural failure.

The following Phase 003 findings are resolution-independent and stand regardless of the pre-phase outcomes:

- PDH/PDL and ONH/ONL are reproducible and well-covered (EXP-014).
- Fixed macro windows do not show persistent range advantage over controls at 1-minute; this is likely robust because the macro-window concept fails even at the most favorable resolution for detection (EXP-013).
- Second-candle-open timing is non-inferior to confirmation-close at 1-minute (EXP-024). This is an entry-timing result, appropriate at 1-minute.
- Fixed 2R is not justified for the current entry chain (EXP-025). An exit-logic result that does not depend on structural detection resolution.
- Candidate A breaker is deterministic and count-eligible (EXP-022). The reproducibility finding holds regardless of resolution; what changes at 15-minute is the structural significance and event count.

The resolution gap specifically affects the structural signal detection experiments: FVG/IFVG (EXP-020/021), displacement stringency (EXP-018), breaker outcome quality (EXP-023), and to a lesser degree sweep reversal (EXP-015).

---

## 8. Relationship to Phase 004 Design

This gap review directly informs the Phase 004 design document at `docs/experiments-docs/checkpoints/2026-05-26-004-ustec-breaker-ifvg-selectivity/design.md`. The pre-phase experiments (EXP-029 through EXP-031) and the mid-checkpoint reflection gate were added in response to the concerns documented here. Phase 004B branch plans (EXP-032 through EXP-038) are explicitly contingent on the pre-phase reflection directive and may be revised before any Phase 004B scope is created.
