# Phase 021 Retrospective — RSI-2 Fade Capture-Geometry & Tradability (CF-MR-001 batch 2)

> ## ⚠ RETRACTED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead
> **The Phase 021 TRADABLE outcome below is RETRACTED.** EXP-093's `TEST_CONFIRMED` rests on a one-bar
> look-ahead in the EXIT-RCT favourable limit (`arm_levels` rests `rct_target[di]` — bar `di`'s own close —
> during bar `di`; live-actable is `rct[di-1]`; `EXP-090/code/run_experiment.py:305-310`,
> `mean_reversion.py:174`). Causalized, the bare RSI-2 fade + EXIT-RCT is net-negative even gross; exposed by
> the cTrader port + forward test (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`). The 11 EXP-093 counted
> TEST reads stay SPENT (spent-on-defect). **CF-MR-001 CLOSED — REFUTED**; EXP-089/G-020 availability stands.
> Full scope: `docs/experiments-docs/families/cf-mr-001/INDEX.md` §CLOSURE. *Text below retained verbatim.*

**Phase:** 021 · **Family:** CF-MR-001 (bare RSI-2 fade, CORE) · **HYP:** `CF-MR-001/HYP-002` (tradability)
**Opened:** 2026-06-23 (G0 RATIFIED, D0 FROZEN) · **Closed:** 2026-06-24 at **G-021 — TRADABLE**
([`G-021-gate-review.md`](G-021-gate-review.md)).
**One-line outcome:** the bare RSI-2 fade, exited by the native reversion-completion target **EXIT-RCT** and net
of conservative cost, **confirms a positive out-of-sample expectancy on 8 of 11 carried cells** (analysis-TEST
stratum) — the **programme's first net-positive price entry**.

---

## 1. Objectives vs outcomes

| Phase question (design §1) | Outcome |
| --- | --- |
| Does the fade's ~0.75-ATR / ~3-bar gross availability survive a real exit + conservative cost as a positive expectancy clearing the frozen referee — and hold on a counted TEST read? | **YES, on the robust core.** EXIT-RCT net-clears on TRAIN (EXP-091/094), pins 11 candidates (EXP-092), and **8/11 CONFIRM on the analysis-TEST stratum** (EXP-093): six 4h cells (mean-AND-median +) + USTEC-1h/US2000-1h (mean-carried). G-021 **TRADABLE**. |
| Do the native intrabar targets beat the reactive conventional contrast? | **YES, for RCT.** EXIT-RCT was the *only* exit to pass the screen; ERT + the 4 conventional arms died. RCT > RSI-revert-on-close 20/20 on TRAIN (Δ median +0.261 ATR). The far native target (ERT, return-to-EMA10) failed. |

**Verdict:** objectives met. The honest prior (*availability ≠ capturable edge*) held precisely — it killed the
15m domain (cost ≈ 2× gross) and the thin-margin 1h cells (OOS reversal), while the strongest cells survived.

## 2. The experiment arc (EXP-090 → 093)

| EXP | Role | Outcome |
| --- | --- | --- |
| EXP-090 | Exit-substrate readiness + per-cell inference calibration (TRAIN) | `READINESS_CALIBRATION_DELIVERED`; 20 MEMBER / 12 COVERAGE_EXCLUDED; new 1m intrabar fill engine validated (amended `D0-amendment-002`). |
| EXP-091 | Exit / capture-geometry screen (TRAIN, net of cost) | `SCREEN_DELIVERED`, non-empty — **EXIT-RCT only**, 5 cells / 5 instruments (all 1h); cost geometry, not signal strength, is the binding constraint. |
| EXP-094 | 4h falsification re-screen (TRAIN; `D0-amendment-004/005`) | `ADMIT_4H` — 6 powered 4h members beat a matched-distance oscillation null 6/6 → entry signal, not oscillation harvesting; corrected an over-claiming operator hunch (TEMP-091). |
| EXP-092 | Per-instrument cost-bearing sequence (TRAIN) | `SEQUENCE_DELIVERED` — 11/11 SEQUENCE_PASS, hash-pinned (sha256 `f6427e83…`) + Holm rule. |
| EXP-093 | **One-shot counted TEST confirmation** | **`TEST_CONFIRMED`** — 8/11 CONFIRM; 11 counted TEST reads spent (each carried stratum 0→1); holdout sealed. |

Audits: all PASS. EXP-090 (3 runs, 2 HALT-class confounds fixed), EXP-094 (1 Critical fixed-and-rerun, bite-check
RED→GREEN), EXP-093 (1 non-verdict-material Warning, re-labelled in interpretation).

## 3. Lessons learned

1. **The deviation-amendment discipline carried the phase.** Five dated `D0-amendment-*` files (1m-fill +
   Null-B fixes; Phase-021-local cost table; 4h opened; binding-null correction; carried-set ratification) kept
   every scope change governed and reversible-on-paper. In particular **`D0-amendment-005`** caught a
   *structurally biased* falsification null at Stage 3 (a signal-derived target that let real trivially beat
   random) — reinforcing [[falsification_null_design]]: never build a null around a signal-derived target.
2. **Cost geometry, not signal strength, decided tradability.** Gross expectancy is ~domain-invariant (~0.28
   ATR); the fixed-bps round-trip ÷ entry ATR makes the *same* edge lethal on 15m, marginal on 1h, and clean on
   4h. The 4h dominance of the confirm set is a cost-fraction artifact, **not** a stronger 4h signal — a framing
   trap the audit/forensics flagged explicitly so it is not over-read.
3. **The mean/median split is the honest shape read.** D5's binding-mean + co-reported-median design exposed
   that the 1h confirms are mean-carried (USTEC-1h TEST median −0.026) while the 4h core is mean-AND-median
   positive. The robust core is the six 4h cells; the 1h confirms are weaker and should be weighted as such.
4. **Selection-overlap shrinkage is real and uniform.** Every cell shrank TRAIN→TEST (Δ net_ci_low
   −0.005…−0.107). The phase survived because the robust core's TRAIN margins were *large enough* to absorb it —
   a reminder that TRAIN eligibility (EXP-092) is necessary-but-not-sufficient, and the margin condition (not
   just significance) is what separated the survivors from the reversers.
5. **Carrying the full SEQUENCE_PASS set (vs the smallest-defensible) was the conservative direction.** The
   operator-ratified `D0-amendment-006` widened the Holm family to 11; this can only make a true confirm harder,
   and it bought a complete per-stratum file-drawer record (incl. the 2 EVIDENCE_AGAINST + 1 INCONCLUSIVE) — at
   the cost of 11 (not 8) counted reads, all now 1/2.

## 4. Programme state after Phase 021

- **CF-MR-001 is the programme's first tradable price entry** — a genuine reversal (for this lever) of the G-019
  "price-derived information exhausted" routing. The G-019 mechanical adjudication (CF-VOLEXP-001, CF-XSECT-001
  closed/retained) is unchanged; the reversal is specific to the previously-unscreened mean-reversion mechanism.
- **Reads:** the 11 carried strata are each **1/2** lifetime counted reads (one remaining); the other 37 strata
  stay 0/2; the **final-30% global holdout is untouched** (no new-dataset holdout shot exists).
- **File drawer:** EXIT-RCT survives; EXIT-ERT + the 4 conventional arms died at the screen; the 3 non-confirming
  1h cells retained. The vol-regime partition (inert), TREND/FILTER variants (dead), and the contrarian / 25-75 /
  15m / cross-cut / tuning branches remain registered-but-deferred.

## 5. Proposed next direction (each its own checkpoint/D0 — not opened here)

1. **Global-holdout release for the 4h robust core** — the EXP-032-analog one-shot final confirmation on the six
   mean-AND-median-positive 4h cells; own checkpoint, D0, and governance. The highest-value de-risking move now
   that the analysis-TEST confirm is in hand.
2. **Realistic portfolio economics** — a time-aligned, equal-risk equity curve with cross-instrument correlation
   (honest annualized Sharpe / drawdown) to size the economic case *before* spending the holdout shot.
   (Descriptive companion already run on the 8 CONFIRM cells: per-trade Sharpe 0.14–0.32; pooled per-trade
   Sharpe 0.20; all 8 cells expectancy-positive — but win rate 47–61% and the 1h median-fragility mean the
   currency-P&L economics need the time-aligned construction before any deployment claim.)
3. **1h median-fragility diagnostic** — whether a shape-aware exit recovers the 1h median (new HYP, own D0).
4. **Deferred levers** — vol-regime, contrarian, 25/75, 15m capture, faster-cost sensitivity, each a dated
   `D0-amendment-*` + slot decision.

---

*Phase 021 CLOSED at G-021 TRADABLE (2026-06-24). Gate review: [`G-021-gate-review.md`](G-021-gate-review.md).
Design: [`design.md`](design.md). D0: [`D0-predeclarations.md`](D0-predeclarations.md) + amendments 001–006.*
