# G-022a Gate Review — Pre-Holdout Freeze ADJUDICATED (CF-MR-001 deployment portfolio)

> ## ⚠ RETRACTED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead
> **The G-022a pre-holdout freeze below is RETRACTED** (with G-022). It froze a deployment portfolio whose edge
> is the EXP-093 EXIT-RCT one-bar exit look-ahead (`arm_levels` rests `rct_target[di]` — bar `di`'s own close —
> during bar `di`; live-actable is `rct[di-1]`; `EXP-090/code/run_experiment.py:305-310`, `mean_reversion.py:174`).
> Causalized, the bare RSI-2 fade is net-negative even gross; the analysis-set Sharpe the band was calibrated
> against is look-ahead-inflated. Exposed by the cTrader port + forward test
> (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`). **CF-MR-001 CLOSED — REFUTED**; the EXP-097 holdout shot
> it gated stays SPENT (spent-on-defect). Full scope: `docs/experiments-docs/families/cf-mr-001/INDEX.md`
> §CLOSURE. *Text below retained verbatim.*

**Date:** 2026-06-25 · **Gate:** G-022a (Phase 022 pre-holdout freeze).
**Adjudicated outcome:** **FREEZE — proceed to EXP-097.** All four D0 §D9 preconditions hold on the analysis-set
evidence; the deployable set, construction, confirmation statistic + band, A-vs-B structure, and read accounting
are frozen ([`G-022a-gate-criteria.md`](G-022a-gate-criteria.md)) and the terminal rubric is frozen alongside
([`G-022-gate-criteria.md`](G-022-gate-criteria.md)).
**Inputs:** EXP-095 (`COMPLETED`, D0-amendment-001 rerun, re-audit PASS) + EXP-096 (`COMPLETED`, audit PASS
0C/0W/5I) — both analysis-set, 0 counted reads, holdout untouched. **Operator decision (2026-06-25):** both A and
B are read on the holdout as **one** read (no optimization/tuning).
**Holdout:** **NOT loaded** at this gate.

---

## 1. Decision

**FREEZE.** The four D0 §D9 preconditions are met; G-022a freezes the EXP-097 read and routes to it. Had any
precondition failed, the rule was HALT (holdout preserved) — it did not fire.

## 2. Precondition adjudication (per D0 §D9 / `G-022a-gate-criteria.md` §2)

| # | Precondition | Verdict | Evidence |
| --- | --- | --- | --- |
| (i) | non-empty noise-survivor deployable set | **MET** | EXP-096: under the binding v2 fill all **8 cells net-positive**; per-cell v2 Sharpe LBs all > 0 (min 0.130 EURJPY-4h). |
| (ii) | analysis-set portfolio edge, material margin | **MET** | EXP-096 v2 portfolio Sharpe LB **A 5.147 / B 4.897 ≫ 0**; benefit vs cross-cell-median single-cell LB (2.554) **A +2.59 / B +2.34 > sampling band 1.35/1.39**; co-binding Calmar LB ADDS_VALUE; broad-based (portfolio LB > best single cell). |
| (iii) | statistic calibrated + finite clearable MDE | **MET** | EXP-095 A4: synthetic-null **FPR A 0.000 / B 0.002 ≤ 0.05**; **MDE m\* = 1.75 / 2.00** finite; EXP-096: realized v2 LB clears m\* (`statistic_clearable_under_noise=true`, A +3.40 / B +2.90). |
| (iv) | predeclared band ≥ m\*, from analysis estimate | **MET** | Band frozen at **m\*** (band_A 1.75 / band_B 2.00 — the A4 floor); realized v2 LB sits ~2.9–3.4 above (over-confirmation context, EXP-032 lesson). |

## 3. What is frozen (binding on EXP-097)

1. **Deployable set: carry-8** (all G-021-confirmed cells). **EURJPY-4h is flagged `NOISE_DEGRADED` but
   net-positive → carried** under the ratified portfolio-only membership rule (dropping a non-broken cell would be
   an un-predeclared noise-driven prune). *Operator-ratifiable: trim to 7 before EXP-097 if preferred; default is
   carry-8.*
2. **Construction:** the EXP-095/096 binding-**v2** noise-aware ERC portfolio, verbatim (LW-90d covariance,
   weekly rebalance, 10%-vol anchor, 1.5× cap, intra-1h MTM; v2 entry fill; EXIT-RCT/adverse/cost frozen; seed
   `20260624`). No tuning; v1/v3 and the covariance-window bracket stay disclosure-only.
3. **A-vs-B (operator decision):** **both** A and B adjudicated on **one** holdout read; **primary = Portfolio
   B** (analysis-set justification: B ≈ A at the binding v2 but B is large tail-insurance at the v3 stress
   ceiling — weakly dominant deployment choice at ≈zero cost; chosen pre-holdout, not tuned). A co-reported; **no
   OR rescue** of the family verdict.
4. **Confirmation statistic + band:** per portfolio, holdout annualized-Sharpe MBB one-sided LB (block = weekly
   cadence, N_BOOT 10_000, α 0.10, seed 20260624) + co-binding Calmar LB; **CONFIRM(P) iff Sharpe_LB > band_P AND
   Calmar_LB > 0**, band_A 1.75 / band_B 2.00.
5. **Read accounting:** EXP-097 = **one** global-holdout-governance event (single sanctioned shot, à la EXP-032);
   the holdout is materialized once, both A and B computed from it; recorded in `test-read-ledger.md` +
   `multiplicity-registry.md` in the same change; **outside** the analysis-TEST ledger (11 carried strata stay
   1/2); 0 counted analysis-TEST reads, 0 candidate slots; non-repeatable / non-upgradable.

## 4. Operator-decision note — both A and B on one read (multiplicity honesty)

The operator (2026-06-25) authorized reading **both** A and B on the holdout as **one read**. This is governance-
honest because: (a) A and B are weightings of the **same** per-cell return streams, computed from a **single**
holdout materialization — no extra data contact; (b) the A-vs-B deployment choice is fixed **now** from
analysis-set evidence (B primary), **not** selected by peeking at the holdout, so there is **no optimization or
tuning**; and (c) the terminal verdict keys off the **primary (B) only** — an A-confirm cannot rescue a B-fail,
so there is **no OR-multiplicity inflation** of the family verdict. A's outcome is a pre-declared robustness
disclosure on the same shot.

## 5. Integrity affirmations carried to EXP-097

- **Holdout virginity:** no final-30% bar (incl. 1-minute) loaded before this freeze; EXP-097 is the first and
  only contact.
- **Frozen-rule discipline:** set / construction / primary / band / rule are **not** re-edited after the holdout
  outcome is seen.
- **Determinism / real-price / causality:** byte-identical second pass; real touched fills; causal weights/MTM;
  per-stratum disclosure (LESSON-001).
- **File drawer:** A and B holdout outcomes and every per-cell outcome retained whatever the verdict.

## 6. Routing

**→ EXP-097 (the single sanctioned global-holdout release), gated behind this freeze.** It runs the frozen
construction on the final-30% global holdout, computes the §3.4 statistic for A and B from one materialization,
and the terminal **G-022** adjudication ([`G-022-gate-criteria.md`](G-022-gate-criteria.md)) reads the realized
numbers against the frozen rubric → DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE.

---

*Companion documents: [`G-022a-gate-criteria.md`](G-022a-gate-criteria.md) · [`G-022-gate-criteria.md`](G-022-gate-criteria.md) ·
[`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) · [`D0-amendment-001.md`](D0-amendment-001.md) ·
EXP-095 [`report`](../../../../python/experiments/EXP-095/report.md) · EXP-096
[`report`](../../../../python/experiments/EXP-096/report.md) · family spec
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).*
