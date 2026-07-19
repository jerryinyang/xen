# Checkpoint-013 Retrospective — Chapter 04 Open: HTFCAP + EPSOSC + Fresh XENA CAL

> **STATUS: SIGNED — checkpoint-013 CLOSED (operator-approved 2026-07-19).** §4 family-status
> transitions are EXECUTED: **CF-EPSOSC-001 → RETIRED (REFUTED)**, **CF-HTFCAP-001 → CLOSED
> (CHARACTERISED, not refuted)**. Ledger sign columns (`xena-runs.md`) and family-card status
> headers updated accordingly.

**Checkpoint:** 013 · **Opened:** 2026-07-16 (design SIGNED, D1–D5) · **CLOSED:** 2026-07-19
**Families in scope:** CF-HTFCAP-001 (REF-A) · CF-EPSOSC-001 (REF-B)
**Lane:** SPDR → XENA (EXP lane not used, D0-frozen)
**One-line outcome:** both families' XENA runs resolved **negative for deployment** — EPSOSC
**refuted twice** (drift pedestal, not the mechanism), HTFCAP a **real but sub-cost gross edge on
BTC** (not deployable at these holds). The chapter also rebuilt the whole XENA apparatus on the
Bybit stack (fresh CAL pin) and retired the arbitrary value gates (report-layer framework).

---

## 1. Objectives vs outcomes (checkpoint design §Objectives)

| Checkpoint objective | Outcome |
|---|---|
| 1. Ratify VAL-008 stack lessons L-28…L-31 into the KB | **DONE** — L-28..L-31 signed + skill clauses patched (commit `f41ba32`); L-32 added later (INFR-016) |
| 2. Register CF-HTFCAP-001 + CF-EPSOSC-001 as REGISTERED families | **DONE** — D2 rows appended 2026-07-16, consistent with D0 cards (0 unexplained deltas) |
| 3. INFR-014 fresh Bybit CAL → new hash-pinned XENA registry + smoke S1 | **DONE** — pin `ac8a1eb6…` (CLS-FILTER LOW_ONLY_CERTIFY; CLS-EPISODE TERMINAL); S1 A-vs-B PASS multi-instrument single-node |
| 4. Execute the family experiment sequence (SPDR → XENA) | **DONE** — SPDR-004/005/006 all WORTH_EXPLORING; both XENA universes ran to operator verdicts |
| 5. Codify instrument selection rules (Q1: n=10, online, ≤ t−1) | **DONE** — §5 online-volume rule frozen; anti-survivorship binding project-wide |

Two objectives grew mid-chapter (both operator-authorized, both clean):
- **INFR-015** — CLS-EPISODE binder amendment (overlap blocks + derived leg floor F*=16); amended
  pin `abbb1842…` supersedes `ac8a1eb6…`, unblocking EPSOSC LOW-only.
- **INFR-016** — retired the arbitrary value gates; value/quality/significance reads became
  **report layers** (`observed/ideal/interpretation`), only future-destroy/holdout/causal/estimand
  stay hard. This directly changed how HTFCAP was read (below).

## 2. The experiment arc

| ID | Role | Outcome |
|---|---|---|
| L-28..L-31 | VAL-008 stack lessons ratified | signed into KB + skills |
| SPDR-004 | CF-HTFCAP-001 TRAIN-only screen | **WORTH_EXPLORING** — SOL DI_ADX hold-ladder 5.9→50.1 bps monotone (single-symbol caveat) |
| SPDR-006 | CF-HTFCAP-001 vol-regime facet | **WORTH_EXPLORING** — DI×VOL_HI / DI_ADX×VOL_HI amplifier, BTC+SOL (two-name concentration caveat) |
| SPDR-005 | CF-EPSOSC-001 screen | **WORTH_EXPLORING** — VOLARM×15m cluster, +54–60 bps/episode (pooled-median-negative caveat) |
| INFR-014 | fresh Bybit CAL + registry | pin `ac8a1eb6…`; CLS-FILTER LOW certified; smoke S1 PASS |
| INFR-015 | CLS-EPISODE binder amendment | amended pin `abbb1842…`; LOW CERTIFIED, HIGH FAIL_COV; audit SOUND |
| INFR-016 | arbitrary-gate retirement | report-layer machinery; L-32; retired 5 auto-verdicts |
| **XENA-EPSOSC-001** | first VOLARM universe | **NOT SUPPORTED** — top-1 REJECT-class (leak collapse 0.395); only survivor AKRO single-symbol on a drift pedestal, seed-fragile, pre-mass band. Motivated 002 |
| **XENA-EPSOSC-002** | mass-aligned cross-symbol successor | **NOT SUPPORTED (refuted)** — certified 4-symbol subset fails stage-2 gross LCB (−68) AND derangement (drift-adjusted collapse 0.135); AKRO-concentrated drift pedestal **reproduced**. Edge = volatility-window clustering, not arm→reversion |
| **XENA-HTFCAP-001** | interaction-filter universe (EXPLORATORY) | **EXPLORATORY, NOT deployable** — real gate-attributable sign-null-clearing GROSS edge on BTC `DI_ADX×VOL_HI adx25` H32/H64 (embargoed gross LCB +8..+18, sign p 0.02–0.05); **net-of-cost 0/72 cells resolve above zero** (~18 bps taker+GAP+funding wall at 8–16h holds) |

## 3. Reads + holdout state (unchanged where it matters)

- **Global 30% holdout (≥ 2025-01-08): SEALED throughout.** Never loaded on any run
  (holdout-safety self-tests PASS; HTFCAP boundary-mark trim receipt clean).
- **Gate slots:** CF-EPSOSC-001 **0/2** (no counted TEST gate on either 001 or 002).
  CF-HTFCAP-001 **1/2** — one exploratory TEST-band read (AMENDMENT-4/5, no reserved OOS);
  recorded in `test-read-ledger.md` as a read disclosure, **not a certification**.
- **Registry:** `xena-runs.md` rows carry eval_count + distinct_subsets for all three universes;
  `multiplicity-registry.md` + candidate-family cards carry the evidence rows. All items RETAINED
  (never deleted).
- **Apparatus:** chapter-03 pins stay VOID on Bybit; the active certified set is the INFR-015
  pin `abbb1842…` (CLS-FILTER low + CLS-EPISODE low).

## 4. PROPOSED family-status transitions — operator signs here

The pipeline separation is binding: **family status changes happen only at this retrospective,
operator-signed.** Two decisions, each with its evidence and a marked recommendation.

### 4a. CF-EPSOSC-001 (Episode-Clearing Oscillation Harvest)
- **Evidence:** SPDR-005 WORTH_EXPLORING (substrate available) → **refuted twice at XENA.** Both
  001 and 002 reproduce an **AKRO-concentrated directional-drift pedestal**, not the armed
  return-to-anchor mechanism. 002's certified cross-symbol subset fails both the certification leg
  (gross LCB −68) and the derangement tripwire (drift-adjusted collapse 0.135). The edge is
  volatility-window clustering, not the thesis signal.
- **Recommended disposition: RETIRE — REFUTED.** The harvest object was falsified on the mass-aligned
  cross-symbol re-run; the drift pedestal is the whole apparent edge. A genuinely new within-episode
  clearing object on unseen data would be a **new family**, not a re-open of this one
  ([[cf_volharv_001_registration]] precedent).

### 4b. CF-HTFCAP-001 (HTF Context × Capture Scale)
- **Evidence:** SPDR-004/006 WORTH_EXPLORING → XENA EXPLORATORY. A **real, gate-attributable,
  sign-null-clearing gross edge exists** on BTC mid-threshold `DI_ADX×VOL_HI adx25` at 8–16h holds —
  a genuine finding the retired top-1 gate framing had hidden. But **net-of-cost nothing resolves
  above zero**; the ~18 bps taker+GAP+funding wall kills it at these hold lengths. Ranking-fold
  instability (worst_F negative 10/10, Jaccard 0.0) confirms the certified top-1 was an overfit
  selection artifact.
- **Recommended disposition: CLOSE — CHARACTERISED (not refuted).** The mechanism is not dead: it
  carries real directional content, just sub-cost at these holds. Close the chapter-04 XENA leg with
  this characterisation on the record. **Re-open path is a new design, not this family's continuation:**
  (i) lower-cost capture (maker entries / cheaper venue), or (ii) denser-cadence variants where a
  smaller edge compounds (needs a HIGH-cadence CAL pin; current pin is LOW-only).
- *Distinction the operator should weigh:* RETIRE-REFUTED would over-state the result — the gross
  edge is real. CHARACTERISED-CLOSED keeps the honest record that cost, not signal, was the wall.

### 4c. Checkpoint close
- On signing 4a + 4b: mark checkpoint-013 CLOSED; update `xena-runs.md` operator-sign columns
  (EPSOSC-001/002, HTFCAP-001) from `pending` to the signed disposition; add the retrospective row
  to the master `docs/experiments-docs/INDEX.md` § Checkpoint Retrospectives.

## 5. Lessons

1. **Retiring the arbitrary gates changed a verdict, honestly.** HTFCAP's old top-1 gate framing
   reported the *worst* corner and called the family leak-class NOT SUPPORTED. Reporting all 72 cells
   (INFR-016) surfaced the real BTC gross edge the machinery had hidden — while the binding net-of-cost
   read stayed the same (still not deployable). The framework change improved the *characterisation*
   without inventing an edge. [[arbitrary_gate_retirement_infr016]]
2. **A drift pedestal survives a re-run if the fix does not remove the drift.** EPSOSC-002 mass-aligned
   the window and forced cross-symbol breadth, but the AKRO drift pedestal reproduced because the
   harvest object still monetises unconditional drift, not the arm signal. Falsification, not a tuning
   miss. [[permutation_destroy_mean_invariant]]
3. **Cost geometry decided both families, again.** HTFCAP's edge is real gross and dies on funding+taker
   at 8–16h holds — the same "cost fraction, not signal strength" wall that recurs across the programme.
   Funding is the crypto-native slice that FX-era intuition understates.
4. **SPDR WORTH_EXPLORING is availability, never tradability.** Both families cleared SPDR and both
   failed the deployable question at XENA — exactly the honest-prior split the SPDR carve-out is designed
   to expose cheaply before a full universe spends reads.

## 6. Proposed next directions (each its own D0 / checkpoint — not opened here)

1. **HTFCAP lower-cost / denser-cadence re-ask** — a NEW family/design testing whether the real BTC
   directional edge clears under maker entries or compounds at denser cadence. Needs a HIGH-cadence CAL
   pin first (current pin LOW-only).
2. **CAL HIGH-cadence certification** — INFR follow-up to certify the HIGH class the current pin fails,
   prerequisite for any denser-cadence family.
3. **Chapter-04 rollover** — with both registered families closed and the apparatus rebuilt (Bybit CAL,
   report layers), the chapter is at a natural boundary; extract lessons + reset per the rollover skill
   when the operator chooses.

---

*DRAFT pending operator signature on §4. Evidence: `xena-runs.md`, `multiplicity-registry.md`,
`test-read-ledger.md`, candidate-family cards, and the three XENA reports
(`python/experiments/XENA-EPSOSC-001/analysis.md`, `XENA-EPSOSC-002/report.md`,
`XENA-HTFCAP-001/report.md`). Checkpoint design: [`design.md`](design.md).*
