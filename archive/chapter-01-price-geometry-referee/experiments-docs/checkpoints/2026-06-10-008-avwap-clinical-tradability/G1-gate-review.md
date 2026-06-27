# G1 Gate Review — Phase 008 Clinical Tradability (Tier A → Tier B)

**Gate:** G1 (lenient, exploration-continuation; design §8.1–8.3, §7.7 two-speed gating).
**Date:** 2026-06-10.
**Inputs:** EXP-033 (A2/DIAG-004), EXP-034 (A1, verdict-grade), EXP-035 (A3/DIAG-005).
**Dependency status:** all three Tier-A experiments post-experiment governance **APPROVE**.
**Outcome:** **G1 = QUALIFIED** (not FLAT). Tier B opens for the qualifying items only.

This is a mechanical application of the predeclared §8 criteria to frozen Tier-A
results. No new computation; numbers read directly from the named result artifacts.

---

## §8.1 G1-A3 — conditioning dimension qualification (EXP-035)

**Criterion:** dimension k qualifies on domain d iff Material (i) ∧ Structured (ii) ∧
Stable (iii) ∧ Multiplicity-survives-Holm (iv), at α_G1 = 0.10.

**Evidence:** `EXP-035/results/g1_qualification.csv` — `qualified = false` on all 9
domain×dimension cells. Binding leg is **materiality (i)**: `material_i = false` on
every row. The closest cell, 5m/c1_completion (SNR = 1.42, structured ✓, stable ✓,
Holm p = 0.030 ✓), still fails because the candidate-bin TRAIN **net** is **−7.07 bps**
(< 0). No bin reaches positive absolute net under frozen costs + financing.

**Result:** **0 dimensions qualify. B1 `/COND` (EXP-036) does NOT open — its 1 Tier-B
slot remains unused.** The selectivity lever is empty on this entry substrate.

---

## §8.2 G1-A1 — instrument-cell continuation (EXP-034)

**Criterion:** a declared cell continues iff net point > 0 **and** CI not entirely
below 0. (Strict §8.4 EVIDENCE_FOR is a separate, stronger bar.)

**Evidence:** `EXP-034/results/sequence_verdicts.csv`.

| Cell | net (bps) | CI / ci_low_1s | boot_p | lenient continue | strict A1 pass |
| --- | --- | --- | --- | --- | --- |
| EURUSD-4h | +11.77 | ci_low_1s +3.90 | 0.009 | ✓ | **✓ SEQUENCE_PASS_ALPHA05** |
| USTEC-4h | +8.90 | [−21.10, +35.09] | 0.281 | ✓ | ✗ (power-limited, predeclared) |
| XAUUSD-1h | −0.35 | [−5.18, +4.51] | 0.563 | ✗ (point ≤ 0) | ✗ (NOT_TESTED, sequence stopped) |

**Result:** **EURUSD-4h qualifies (strict + lenient); USTEC-4h continues leniently;
XAUUSD-1h does not continue.** Per §8.4 (as amended F02), the EURUSD-4h **strict** pass
is necessary-but-not-sufficient and routes the cell into a one-shot Tier-B **TEST-stratum
confirmation** of the same registered baseline estimand (0 new slots).

---

## §8.3 G1-B2 — capture-efficiency case (EXP-033)

**Criterion:** B2 opens on domain d iff the TRAIN FH net curve grid maximum > 0 for d
(§5/A2 one-SE rule).

**Evidence:** `EXP-033/results/b2_selection.json`.

| Domain | FH grid max (bps) | B2 eligible | H\* | pyramid policy |
| --- | --- | --- | --- | --- |
| 5m | −3.72 (H=24) | ✗ | — | — |
| 1h | −0.99 (H=6) | ✗ | — | — |
| 4h | **+45.79 (H=24)** | **✓** | **8** | **all_legs** |

**Result:** **B2 `/EXIT-FH` (EXP-037) opens on 4h only.** Selection disclosure flags
**H\* fragility**: `h_star_stable = false` (split-half argmax H=24 vs H=12);
`eligibility_stable = true`, `policy_stable = true`. The EXP-037 scope/governance must
weigh this — EXP-033 §Next-Steps recommends a predeclared H\* sensitivity window
(e.g. H ∈ {4,6,8,12}) rather than a single frozen H\*.

---

## Tier-B docket (qualifying items only; §3, §7.5 ≤2 variants)

| Tier-B item | Source gate | Domain/cell | Slots | Status |
| --- | --- | --- | --- | --- |
| **A1-cell TEST confirmation** | §8.2 strict + §8.4 | EURUSD-4h | 0 (registered within Tier B) | **OPEN** |
| **EXP-037 `/EXIT-FH`** | §8.3 | 4h (all instr.) | 1 | **OPEN** (H\*=8 all_legs; H\* fragile) |
| EXP-036 `/COND` | §8.1 | — | 1 | **DOES NOT OPEN** (slot unused) |

USTEC-4h's lenient continuation is realized through the domain-level 4h B2 variant; it
cannot trigger the §8.4 A1-cell TEST route (that requires a **strict** A1 pass).

**Slot budget:** 1 of ≤2 Tier-B slots consumed (EXP-037). The A1-cell TEST confirmation
uses 0 slots. Within budget.

---

## G2 implications (forward note, not adjudicated here)

Per §8.4 (strict), holdout release (EXP-032) becomes admissible only on a **TEST-stratum**
net CI_low > 0:
- EURUSD-4h A1-cell TEST confirmation at one-sided α = 0.05, **or**
- a Tier-B variant (EXP-037) net CI_low > 0 on TEST with Holm across its declared family.

The A1 strict pass alone is recorded as `A1_STRICT_PASS_TEST_CONFIRMATION_REQUIRED` and
does not open the holdout. Both 4h TEST reads are one-shot and must be predeclared before
any TEST row is read (§7.3).

---

## Decision

**G1 QUALIFIED.** Proceed to Tier B with exactly two registered reads, both on 4h:
1. **EURUSD-4h A1-cell TEST confirmation** (0 slots) — register protocol, predeclare,
   then one-shot TEST read.
2. **EXP-037 `/EXIT-FH` 4h** (1 slot) — scope with the H\* fragility disclosure handled.

`/COND` is closed for this phase. 5m and 1h are closed for Tier B (no qualifying item on
either domain). Phase outcome will resolve at G2 to CLINICAL_TRADABLE (≥1 TEST pass) or
CHARACTERISED_NOT_CONFIRMED (qualified but no TEST pass); FLAT is no longer reachable.
