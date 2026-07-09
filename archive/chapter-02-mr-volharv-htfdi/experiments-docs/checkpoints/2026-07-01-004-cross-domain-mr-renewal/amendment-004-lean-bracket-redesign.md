# Amendment-004 — EXP-014c lean single-leg bracket: trade exactly what the two-barrier measured

**Date:** 2026-07-03 · **Family:** CF-MR-004 · **Hypothesis:** HYP-004 (opened here) · **Operator-directed.**
**Relation:** EXP-014b (amendment-003) audit + adjudication are COMPLETE and stand (`REJECT_LEAK`,
labels corrected post C1/C2). This amendment does **not** supersede them — it opens a **new experiment
EXP-014c** on the audit's exploratory findings. EXP-014b Stage-5 documentation is deferred by operator
direction; one consolidated report will cover 014b + 014c.

## Why (what the EXP-014b audit forensics showed)

1. **The confirmed edge is an availability shape the traded exit-set never expressed.** The symmetry
   two-barrier read (frozen entry anchor, ±D symmetric barriers, horizon 3·HL) is collapse-verified
   real at **4h JP225** (p_inward 0.696, ci_low 0.638, shift→0.541; replicated at z1.5) and weakly at
   4h EURUSD. The traded strategies instead used a **moving**-anchor target: f2 small wins vs f1
   anchor-drift losses (−20…−216 bps, MAE to −220) → gross ≈ 0 everywhere. The measurement and the
   strategy were different objects.
2. **Every bloat axis is now evidence-settled:** 1h = specificity leak (basket *dilutes* own-price MR;
   EURUSD live 0.508 vs shift 0.688); z1.5 = weaker per-event edge, no new verdicts; extend/allow =
   own-price MR harvesting (net halves but persists under decorrelation → leak); both-leg =
   median-positive but mean-killed by an unhedged ~50-bar loss tail + N+1 costs; moving-mean exit =
   the loss engine. Strip all of it.
3. **EV headroom where availability is real** (analysis-only estimate from the emitted 014b events,
   symmetric bracket ± D, time-stop at H): JP225 4h ≈ +119 bps/event net (D_med ≈ 323 bps vs 4 bps
   cost; censored events +111 avg), EURUSD ≈ +8, NZDUSD ≈ +1, AUDUSD ≈ −8. In-sample and
   overlapping-event based — a power calculation, not evidence; the verdict must come from the engine.
4. **Selection-bias control:** JP225 is 1 strong cell out of 44 (cell,domain,z\*) reads of one model.
   Defenses carried into EXP-014c: all 11 cells still emitted (same conf cost), JP225+EURUSD
   **prespecified** as binding primaries, cross-cell Holm, phase-shift tripwire binding, session-hour
   clustering disclosure (JP225-vs-US session structure could manufacture dislocations). TRAIN cannot
   confirm itself — any pass leads to the operator-gated counted TEST read, not a deployability claim.

## Locked change-set (operator; revised after operator pushback 2026-07-03)

Operator pushback folded in: (i) the frozen-TP/SL/time-stop rules are *measurement-implied but never
traded* → run them as decomposed **variants against the faithful moving-mean baseline**, not as a
replacement; (ii) reentry and z\* axes were characterisation axes, not defects → **retained**, and
they must also characterise the new exit rules.

| # | Delta | Spec |
|---|---|---|
| B1 | **New EXP-014c** (EXP-014b untouched) | price-primary, native cTrader m1, S8_RVINDEX, 11 cells. |
| B2 | **4h only** | 1h retired for this family (leak-settled: basket dilutes own-price MR). Frozen 4h referee, min_state=8. |
| B3 | **z\* axis retained** | z ∈ {2.0, 1.5} (entry band = z\*·σ; ladder {z\*, z\*+0.5, z\*+1.0} where reentry=extend). |
| B4 | **Single-leg only; reentry axis retained** | reentry ∈ {none, allow, extend} (R refresh). Both-leg dropped (tail-failure settled; separate follow-up if ever revisited). |
| B5 | **EXIT axis (the new object)** — 4 arms | **E0 moving-mean** = faithful 014b baseline (form-1 + refreshing form-2 at moving anchor; **already emitted** — 014b 4h single-leg runs are reused, not rerun). **E1 frozen-TP**: TP limit frozen at the entry-time anchor `a` (per leg, set at fill; never modified); no SL, no time-stop; form-1 disabled (the frozen TP *is* the exit thesis). **E2 frozen-TP + SL**: adds a stop frozen at `o ± D` (outward barrier, D=\|o−a\|, o=entry fill). **E3 full bracket** = E2 + hard time-stop ⌈3·HL_entry⌉ domain bars (cap 48) → market exit next open. E3 = the exact object the two-barrier measured. |
| B6 | **Entry unchanged from 014b** (resting bracket limits at anchor±z\*·σ, armed ≤t-1, m1 fills) for E1-E3 comparability with E0; per-leg D and HL frozen at each leg's fill. |
| B7 | **Binding strata** | PRIMARY = (none, z2.0, **E3**) on **JP225 + EURUSD** (prespecified from 014b collapse-verified availability); all 11 cells emitted per arm; cross-cell Holm per (arm,z\*) family over 11 cells; every other (reentry, z\*, exit) combination = disclosure/characterisation; a disclosure admit that matters → follow-up primary with its own multiplicity. |
| B8 | **Leak tripwire (binding)** | peer-feed phase-shift (`BasketPhaseShiftHours=60`) twins for the PRIMARY conf (+ any admitting disclosure arm, generated on demand); net must collapse per cell. Bite-check per admitting cell (frozen referee, +8bps plant). |
| B9 | **Disclosures** | session-hour histogram of entries/exits (JP225 session-artifact check); TP-vs-SL-vs-timeout exit mix vs the availability p_inward (consistency: E3's win rate should reproduce ≈p_inward on decided legs); per-exit-reason P&L split; with-trend/vol_low slices (informative); E0-vs-E1-vs-E2-vs-E3 attribution table (which rule moves net). |
| B10 | **Fence/reads** | EXP-013 first-49% TRAIN cutoffs verbatim; final-30% sealed; 0 counted TEST reads; CF-MR-004 stays REGISTERED (HYP-004 recorded in the registry before execution). |

## Cost/scale

New emissions: 3 exit arms (E1-E3) × 3 reentry × 2 z\* = 18 confs × 11 cells = 198 native 4h runs
+ PRIMARY shift twin (11). E0 baseline (6 confs' worth) reused from 014b — no rerun. 4h-only keeps
wall-clock well under 014b (which was dominated by the 1h + both-leg legs).

## Success criteria (frozen before contact)

- **Tradable-on-TRAIN (per primary cell, none/z2.0/E3 on JP225 or EURUSD):** frozen 4h referee net
  ci_low>0 (Holm over 11) AND net collapses under phase-shift AND bite-check detects the plant →
  operator-gated counted TEST read.
- **Credible negative:** powered + non-vacuous referee fail on the primaries → the family's
  availability is real but not extractable even by the measurement-matched bracket → **retire
  CF-MR-004 fixed-parameter thesis** (strongest possible negative; the family had its best shot).
- **UNPOWERED:** episodes < 8 per cell → episode-starved, no verdict.
- **Attribution read (characterisation, disclosure):** E0→E1 isolates the frozen-vs-moving target;
  E1→E2 the outward stop; E2→E3 the time-stop; reentry × exit crosses test whether the extend
  ladder's own-price harvest persists when the TP is frozen (its phase-shift behavior per cell).
- Non-primary cell admits: disclosure only (registry-recorded, new primary in a follow-up if pursued).
