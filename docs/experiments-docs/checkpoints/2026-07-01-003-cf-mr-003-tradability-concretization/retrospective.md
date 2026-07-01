# Phase 003 — CF-MR-003 Tradability Concretization (CONC-1) — Retrospective

**Phase number:** 003 (Chapter 02)
**Design ratified:** 2026-07-01 (G0)
**Retrospective written:** 2026-07-01
**Status:** COMPLETE — **CF-MR-003 CONCLUDED: SCREENED-ADMIT (availability) → NOT-TRADABLE (net) → family retired.** The cross-domain MR deviation-fade earns a real availability edge (EXP-009) that does **not** survive to net at either execution horizon tested (exec-1h EXP-010, exec-15m EXP-012). No tradable concretization exists; CONC-2+ axis sweep is moot (no P-02 dead-entry rescue).
**Slots/reads:** 1 candidate slot consumed (tradability exploration, opened EXP-010); 0 counted TEST reads; global holdout sealed throughout.

**Design reference:** [design.md](design.md)
**Experiments:** EXP-010 [CONC-1 T1, exec-1h], EXP-011 [E7 referee 15m-domain prereq], EXP-012 [CONC-1 T2, exec-15m] — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

EXP-009 advanced CF-MR-003 to **SCREENED-ADMIT** on availability (native target-based re-screen: does price return to the higher-domain anchor beyond a dislocation-matched control? — yes, per-stratum, leak-clean). Phase 003 asked the concretization question: **does that availability survive to a net-positive tradable edge?** The registered first concretization was the **form-2 limit-at-anchor fade** (`/TARGET`=mean, `/DIRECTION`=fade, `/REENTRY`=none, live-limit entry at the ≤t-1 `|z|≥2` band edge, favourable exit limit at the anchor mean fixed at entry, horizon-market fallback), run **price-primary in the cTrader engine** (L-01), adjudicated per-stratum under the **frozen referee** (L-12), binding-leg cost charged.

Honest prior: **LOW** — availability ≠ tradability; sister family CF-MR-002 (causal RSI-2 fade) was EXONERATED NOT-TRADABLE (Phase 001); shorter-horizon reversion earns a smaller move against the same round-trip cost. Phase 003 was **not** a rescue attempt — a powered NOT-TRADABLE is a definitive close, not a failure to test.

## 2. Outcomes vs objectives

| Objective | Outcome | Evidence |
|-----------|---------|----------|
| **T1 — exec-1h tradability** | **NOT-TRADABLE (UNPOWERED)** — 0/5 powered, 0/5 admit; VR∧HL∧\|z\|≥2 fires only 10–32 episodes/cell < 1h floor 20; net −0.70…+0.10 bps/active, CIs cover 0. | EXP-010 (audit PASS, 0 Critical). Availability does not survive to net; could-not-test-at-power, not a positive refutation. Left gate-debt: F-1 loose vehicle (z-selector corr 0.67), F-2 vacuous leak control. |
| **T2 prereq — 15m referee** | **FROZEN (FREEZE_LICENSED)** — 15m domain added to §10.3a+P\* referee, candidate-blind + hash-pinned before any CF-MR-003 read. | EXP-011/E7 (audit PASS, 0 Critical). Regression anchor 0/32 + P\*-identity 32/32 (1h/4h byte-unchanged); 15m battery 16/16 DET_DOMINANT, dogfood+skew FPR 0.000, band 112/112 0-flip. |
| **T2 — exec-15m tradability** | **NOT-TRADABLE (POWERED)** — 24/24 powered (episodes 70–390 ≥ 15m floor 25), 0/24 admit; every CI_low ≤ 0, net −0.77…+0.04 bps/active. | EXP-012 (audit PASS, 0 Critical). The **powered** definitive close. F-1 vehicle fidelity PASS all 24 (z_corr 1.00, Jaccard 0.97–0.99) — discharged EXP-010's debt; F-2 leak-resistance tested (plant 24/24 + valid live phase-shift future-destroy clean). |

**Family disposition:** CF-MR-003 = availability-real, net-nil at both 1h and 15m ⇒ **RETIRED (SCREENED-ADMIT, NOT-TRADABLE)**. Retained in the registry (never deleted); all outcomes on the books.

## 3. Mechanism — why availability did not survive to net

The anchor-reversion edge is real (price does drift back toward the higher-domain anchor) but the **capturable** portion at a tradable horizon is smaller than the round-trip cost. Moving from 1h to 15m execution multiplied the reversion-episode count (~4× bars → 70–390 vs 10–32 episodes, clearing the higher 15m power floor) but **shrank the per-trade move** proportionally, against the **same** per-instrument round-trip cost — so net moved from untestable-null to a **powered** null-to-negative. This is the same cost-vs-capture veto that closed CF-MR-002 and the AVWAP family (available lifetime move ≫ cost, but capture geometry cannot realize it). Availability was the right screen; it was necessary, not sufficient.

## 4. Lessons (for chapter-rollover Extract)

1. **Availability real ≠ tradable — the cost/horizon veto (candidate pitfall).** A family that passes a native availability screen (EXP-009 SCREENED-ADMIT) can still be **powered NOT-TRADABLE at every execution horizon** because the capturable move shrinks with horizon against a fixed round-trip cost. Do not re-run CF-MR-003 concretizations by re-parameterizing the exit/anchor/sizing (P-02); re-opening requires a genuinely cheaper capture mechanism or a lower-cost universe, not another downstream-stack tune. → fold as a Chapter-02 pitfall at rollover.
2. **Test at the horizon where the effect is powered.** EXP-010's UNPOWERED gap was resolved not by weakening the floor but by moving to the exec grid with more episodes (behind a candidate-blind referee freeze, EXP-011). A powered close is worth the referee-extension cost.
3. **F-1 vehicle fidelity is horizon/vehicle-specific.** The single-symbol S3 path (no basket carry-forward) achieved z_corr 1.00 / Jaccard 0.97–0.99 where EXP-010's basket-carry-forward vehicle was loose (0.67 / 0.30). Prefer the least-carry-forward faithful vehicle; verify fidelity, don't assume it ([[evaluation_vehicle_must_be_native]]).
4. **A permutation of realized P&L is a vacuous future-destroy for a mean referee** (mean-invariant) — EXP-012 false-tripped REJECT_LEAK on it. A valid Python-side leak control must break the position↔return alignment causally (permute positions + re-assemble), or defer to the in-engine phase-shift shuffle. Captured in project memory `permutation_destroy_mean_invariant`.

## 5. Governance ledger

- **Slots:** 1 candidate slot consumed (EXP-010 opened tradability exploration); T2 (EXP-012) opened 0 new slots (same concretization). No slot released.
- **Counted TEST reads:** 0. All three experiments TRAIN-only disclosures; the counted TEST read / holdout release stayed gated on a TRAIN net-positive that never occurred.
- **Holdout:** sealed throughout (final-30% never sliced; per-symbol first-49% TRAIN fence on all price-primary runs).
- **Referee (L-12):** untouched by any candidate. E7/EXP-011 extended + froze the 15m domain candidate-blind and hash-pinned *before* the first CF-MR-003 15m read; `referee_pstar 1fd06b28` == E6 unchanged.
- **Audits:** EXP-010 PASS, EXP-011 PASS, EXP-012 PASS — all 0 Critical.
- **Registry:** `cf-mr-003.md` → SCREENED-ADMIT → CONC-1 NOT-TRADABLE, family RETIRED; `multiplicity-registry.md` Phase-003 batch records both tracks; refuted/inconclusive branches retained.

## 6. Status: CLOSED

CF-MR-003 tradability concretization is concluded. No further in-family phase is warranted without a new capture mechanism or cheaper universe (candidate pitfall above). The cross-domain MR **availability** finding stands as durable knowledge; the **tradability** claim is closed NOT-TRADABLE at 1h and 15m.
