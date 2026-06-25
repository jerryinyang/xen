# G-022a Gate Criteria — Pre-Holdout Freeze (CF-MR-001 deployment portfolio)

**Date:** 2026-06-25 · **Gate:** G-022a (Phase 022 pre-holdout freeze — the hard gate between the analysis-set
work (EXP-095/096) and the single sanctioned global-holdout release (EXP-097)).
**Status:** **ADJUDICATED — FREEZE (see [`G-022a-gate-review.md`](G-022a-gate-review.md), 2026-06-25).** This file
fixes the four D0 §D9 preconditions and the predeclarations G-022a freezes; the terminal holdout rubric is frozen
alongside in [`G-022-gate-criteria.md`](G-022-gate-criteria.md). No result-producing holdout code runs against
anything but these frozen predeclarations.
**Adjudication basis:** the D0 §D9 preconditions, the EXP-095 (construction + statistic calibration) and EXP-096
(noise infusion) analysis-set evidence, the inherited A4 MDE m\*, and the operator's 2026-06-25 A-vs-B holdout
decision. The final-30% global holdout is **not** loaded at this gate.

---

## 1. What G-022a decides (and what it does not)

G-022a decides **whether the holdout may be spent at all**, and if so, **freezes exactly what EXP-097 will read**:
the deployable set, the portfolio construction, the binding confirmation statistic + its predeclared band, the
A-vs-B adjudication structure, and the read accounting. It is a **freeze**, not an edge claim — no holdout number
exists yet.

It does **not**: load/inspect the final-30% global holdout; consume a candidate slot (the first was spent at
G-020); spend a counted analysis-TEST read (EXP-095/096 were disclosures; the 11 carried strata stay 1/2);
re-open the inert vol-regime partition, the dead TREND/FILTER variants, or any registered-but-deferred lever
(each needs its own dated `D0-amendment-*` + slot decision); or re-tune any entry/exit/adverse/cost/portfolio
parameter.

## 2. The four D0 §D9 preconditions (all must hold to FREEZE; else HALT, holdout preserved)

```
(i)   non-empty noise-survivor deployable set
(ii)  an analysis-set portfolio edge: the binding metric LB clears 0 with a material margin
(iii) the confirmation statistic calibrated (synthetic-null FPR <= 0.05) + a finite, clearable MDE (D6/A4)
(iv)  the predeclared holdout band fixed from the analysis-set estimate, set >= the gate MDE m*
```

| # | Precondition | Evidence (EXP-095/096; analysis-set) | Met? |
| --- | --- | --- | --- |
| (i) | non-empty noise-survivor set | Under the binding v2 fill (EXP-096), **all 8 cells are net-positive**; per-cell v2 Sharpe LBs all > 0 (min 0.130 EURJPY-4h). Set non-empty. | **YES** |
| (ii) | analysis-set portfolio edge, material margin | v2 portfolio Sharpe LB **A 5.147 / B 4.897 ≫ 0**; like-for-like benefit vs cross-cell-median single-cell LB (2.554) **A +2.59 / B +2.34 > sampling band 1.35/1.39**; co-binding Calmar LB ADDS_VALUE. (Noise-free EXP-095 LB ~10.2 for context.) | **YES** |
| (iii) | statistic calibrated + finite clearable MDE | EXP-095 A4: synthetic-null **FPR A 0.000 / B 0.002 ≤ 0.05**; **MDE m\* = 1.75 (A) / 2.00 (B)** finite; EXP-096 re-confirmed the realized v2 edge clears it (`statistic_clearable_under_noise=true`). | **YES** |
| (iv) | predeclared band ≥ m\*, from analysis-set estimate | Band frozen at **m\*** (§4): band_A = 1.75, band_B = 2.00 — the A4 floor (a band below the gate's own MDE may not be frozen); the realized v2 LB (A 5.15 / B 4.90) sits ~2.9–3.4 above, the over-confirmation context (EXP-032 margin lesson). | **YES** |

All four hold → **FREEZE** (proceed to EXP-097). Any failure → **HALT** (holdout preserved; the analysis-set
findings stand as disclosure).

## 3. Frozen predeclarations (binding on EXP-097)

### 3.1 Deployable set — **all 8 cells (carry-8)**
EURUSD-4h, XAUUSD-4h, USDCHF-4h, AUDJPY-4h, EURJPY-4h, GBPJPY-4h, USTEC-1h, US2000-1h. Per the **portfolio-only
membership** rule ratified at EXP-095/096 (keep all confirmed cells unless noise *demonstrably breaks* one):
**EURJPY-4h is flagged `NOISE_DEGRADED`** (v2 net ci_low 0.0079 < its 0.025 detectability margin) **but remains
net-positive** — it is not broken, so dropping it would be a noise-driven prune contrary to the ratified
philosophy and would itself be an (un-predeclared) selection. **Carried.** *(Operator-ratifiable: trim to 7 by
excluding EURJPY-4h before EXP-097 if preferred; the default frozen here is carry-8.)*

### 3.2 Construction — **the EXP-095/096 binding-v2 noise-aware ERC portfolio, verbatim**
ERC weights from a causal trailing-90-day Ledoit-Wolf covariance, **weekly** rebalance, **10% annualized-vol**
anchor, **1.5×** concurrent-risk cap, **intra-1h mark-to-market** of open positions (amendment-001 A1), on the
1h common grid. Entries filled under the **binding v2** model (next-1m-open + 0.05×ATR adverse slippage); exit
EXIT-RCT, adverse 2.0×ATR + MR-tempo cap, EXP-085/`D0-amendment-003` cost (`F=0`) — all frozen byte-for-byte.
Master seed `20260624`. **No parameter is tuned; the v1/v3 fill variants and the covariance-window bracket remain
disclosure-only.**

### 3.3 A-vs-B — **both adjudicated on one read; B is the primary deployment portfolio** (operator decision 2026-06-25)
The operator approved **both A (static ERC) and B (ERC + circuit-breaker) to be read on the holdout, counted as
ONE read** — valid because (a) A and B are weightings of the *same* per-cell return streams, computed from a
single holdout materialization (no extra data contact), and (b) the A-vs-B deployment choice is fixed **now**
from analysis-set evidence, **not** selected by peeking at the holdout (no optimization/tuning).

- **Primary binding = Portfolio B.** Justification (analysis-set, pre-holdout): EXP-096 found B ≈ A at the binding
  v2 (neutral — d Sharpe LB +0.25, d MaxDD +0.0013) **and** B provides large tail insurance at the v3 stress
  ceiling (de-allocates the fragile 1h cells, holding MaxDD 6.0% where static-A blows up to 40.9%). B therefore
  weakly dominates A as a deployment choice at ≈zero cost. The terminal family verdict (§G-022) **keys off B**.
- **Co-adjudicated & reported = Portfolio A**, on the **same single read**, against its own frozen band. A's
  CONFIRM/DECAYED status is recorded and disclosed, but **does not rescue the family verdict via an OR** (no
  multiplicity loophole): a confirm on A while B fails does **not** make the family DEPLOYABLE_CONFIRMED.
- Bands are pre-declared per portfolio (§4); no after-the-fact selection between A and B occurs.

### 3.4 Binding confirmation statistic + band
For each portfolio P ∈ {A, B}, on the holdout slice, the **annualized-Sharpe moving-block one-sided lower bound**
(block = rebalance cadence = weekly in 1h-grid steps; N_BOOT = 10_000; α = 0.10; seeded off master `20260624`),
with a **co-binding Calmar** moving-block one-sided lower bound (same block/N_BOOT). Predeclared bands (= the
inherited A4 MDE m\*, the floor allowed by D6/A4):

```
band_A = m*_A = 1.75     band_B = m*_B = 2.00
CONFIRM(P)  iff  holdout Sharpe_LB(P) > band_P  AND  holdout Calmar_LB(P) > 0
```

### 3.5 Read accounting (frozen)
EXP-097 is the **single sanctioned global-holdout release** — **one** holdout-governance event (à la EXP-032):
the final-30% holdout is materialized **once**; both A and B curves are computed from that single materialization.
Recorded in `test-read-ledger.md` and `multiplicity-registry.md` in the **same change** as the result. It is
**outside** the analysis-TEST 48-stratum ledger (the 11 carried strata stay 1/2; the global holdout is a separate
reserve, sealed since VAL-005). **Per the operator decision 2026-06-25, reading both A and B is ONE read.**
**Non-repeatable, non-upgradable** (EXP-032 precedent). No counted analysis-TEST read; 0 candidate slots.

## 4. Integrity expectations carried into EXP-097

- **Holdout virginity until EXP-097:** no final-30% bar (incl. 1-minute) is loaded before this freeze; EXP-097
  loads it for the first time and only after the freeze. Assert max-touched holdout consistency in
  `run_metadata.json`.
- **Same construction as the analysis set:** the holdout portfolio is built with the identical frozen pipeline
  (no re-fit, no re-tune); causal weights/MTM/fills; real touched prices only; determinism byte-identical.
- **No goalpost-moving:** the band (m\*), the deployable set, the primary designation, and the confirmation rule
  are frozen here and **not** re-edited after seeing the holdout outcome.
- **Per-cell disclosure (LESSON-001):** per-cell holdout outcomes are reported alongside the binding portfolio
  estimand; no cell result is hidden inside the aggregate.

---

*Companion documents: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) §D4/§D6/§D7/§D9 ·
[`D0-amendment-001.md`](D0-amendment-001.md) (A1–A4) · terminal rubric [`G-022-gate-criteria.md`](G-022-gate-criteria.md) ·
adjudication [`G-022a-gate-review.md`](G-022a-gate-review.md) · family spec
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).*
