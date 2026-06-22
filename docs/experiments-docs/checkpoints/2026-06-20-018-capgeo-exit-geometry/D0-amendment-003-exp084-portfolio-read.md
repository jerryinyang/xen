# Phase 018 D0-amendment-003 — EXP-084 as an AVWAP-4h PORTFOLIO confirmation read (RATIFIED)

**Status:** **RATIFIED — operator-directed 2026-06-22 (both legs resolved).** This is the **leg-(b)
ratification** that D0-amendment-002 requires before EXP-084 (the reserved-conditional counted-read
confirmation) may open. **Operator ratified 2026-06-22:** §6(1) pinned exit = `AVWAP-FH`; §6(2)
portfolio-disclosure accounting accepted (0 counted reads; basket-only binding claim; the three strata become
disclosed). It does **not** itself authorize a TEST read; EXP-084 now runs the full 8-stage pipeline (scope →
… → manual execution gate). **No TEST stratum or holdout is touched until that gate.**

EXP-085 returned `NET_SURVIVES` (leg (a) satisfied). The operator has elected to confirm — but **narrowed and
reframed** the read from the original "Holm over the full {valid-candidate × stratum} grid, per stratum"
(D0-predeclarations §D4/§D5) to a **single portfolio basket** over the AVWAP-4h survivors, with per-stratum
and per-arm reads carried as **disclosure on the side**. This amendment fixes that design; **nothing in the
frozen referee suite, the D4 conjunction, the D4/D9 separability constants, the WF-EXPANDING schedule, the
cost model, or the 2-lifetime-read cap changes** — only the **unit of analysis** (portfolio, not per-stratum)
and the consequent ledger accounting.

**Governing:** `D0-predeclarations.md` (§D4 conjunction, §D5 WF-EXPANDING, §D4.1 counted-read rule),
`D0-amendment-001` (HYP-004 split), `D0-amendment-002` (TRAIN cost read-gate / EXP-085), EXP-085
(`results.md`, `report.md`, `audit.md`).

---

## 1. Why this amendment

EXP-085 (`NET_SURVIVES`, per-stratum-masked; audit PASS) showed that the net edge among the 26 survivors
lives **entirely in the S2-DEFERRED low-n 4h `SUB-AVWAP` cells** (NZDUSD/USDCAD/USTEC, n=44–78), robust across
exit rule (fixed-horizon, RR, partial, no-stop, VP), while the only S2-PASS well-powered stratum (AUDUSD-1h
harami, n=988) was net-inconclusive. The operator reads the cross-exit robustness as a signal that the edge is
in the **AVWAP-4h entry/availability**, not in a tuned exit, and accepts the low-frequency sparseness on a
"sparse but higher signal/noise" prior.

Two structural facts make a **portfolio** read the disciplined way to act on that:

1. **Portfolio pooling makes the binding shape-guard S2 adjudicable.** S2 has a frozen operating floor
   **n ≥ 120** (§D4); that is exactly why it was deferred on every 4h cell. Pooled across the three
   instruments, **TRAIN n ≈ 200 > 120**, so S2 — the catastrophe-tail non-residual gate EXP-085 could not
   evaluate — becomes binding. The portfolio resolves the largest open gap, not merely the power deficit.
2. **A portfolio read costs 0 counted reads** under the established **portfolio-aggregate rule**
   (`test-read-ledger.md`; Phase-011 Track-C EXP-018 precedent): a portfolio-level read makes no per-stratum
   claim and is entered against each member stratum as a **disclosure**, not a counted read. The 2-lifetime
   cap per stratum is preserved.

## 2. The portfolio read (binding design)

| Item | Specification |
|---|---|
| **Unit of analysis** | ONE portfolio basket = events pooled across **NZDUSD-4h + USDCAD-4h + USTEC-4h `SUB-AVWAP`**, ordered by event close-time. |
| **Pinned exit (single, a-priori)** | **`AVWAP-FH`** (fixed-horizon, parameter-free). Pinned on principle, **before** any TEST contact: (i) it is the least-tunable exit (no RR ratio, no stop placement); (ii) the cross-exit robustness says the specific arm should not matter, so pick the simplest; (iii) **its EXP-083 S2 pass was on a genuine continuous tail** (`tailmass 0.022`), whereas the RR arms cleared S2 only by stop-truncation-to-point-mass (magnitude-unpriced −7.28 ATR/stop) — so `AVWAP-FH` is the arm whose shape-guard pass was real, not mechanical. **Not** selected on net magnitude (no TEST- or selection-on-outcome). |
| **Net basis** | NET, carrying the **EXP-085 operator-ratified cost model verbatim** (RT/F = NZDUSD 4.5/0.8, USDCAD 4.0/0.7, USTEC 5.0/1.2 bps; bar-count financing; ATR-unit). |
| **TRAIN gates (re-confirm on the pooled basket)** | G-018a gross + **S1** attribution + **S2** tail non-residual — **S2 now adjudicated** at pooled TRAIN n ≈ 200 (frozen `K_tail=3.0, τ_tail=0.06, δ=0.40`). |
| **TEST read** | one frozen pre-declared **WF-EXPANDING** run (§D5: initial train 0.50, 5 expanding folds of 0.10, min fold ≥ 30) on the pooled-basket TEST series → **frozen referee suite (binding)** + beats matched-random, NET. |
| **Binding verdict (G-018 conjunction, §D4, at the portfolio level)** | basket CONFIRMS iff **(1)** frozen referee suite PASS on the aggregate WF verdict **∧ (2)** beats matched-random (`CI_low > 0`) **∧ (3)** separability S1 ∧ S2 PASS on TRAIN **∧** net co-primary (expectancy ∧ median) `CI_low_1s > 0`. `ASS` disclosure-only (G-017). |
| **Disclosure (non-binding, "on the side")** | per-stratum net reads (NZDUSD/USDCAD/USTEC individually) **and** per-arm net reads (the other 10 exits) — reported for transparency, carrying **no** binding claim and **no** stratum-specific inference. |
| **Provenance** | the EXP-083 valid set sha `fa4035f3…` and the EXP-085 cost constants asserted before any read; frozen-module hashes recorded. |

## 3. Ledger accounting (binding — the trade-off the operator accepts)

- **Portfolio-aggregate rule → DISCLOSURE, 0 counted reads.** EXP-084 makes a **portfolio** claim and no
  per-stratum claim, so it is entered against NZDUSD-4h, USDCAD-4h, USTEC-4h as a **disclosure**; **all 48
  strata remain 0/2 counted** (caps preserved). The per-stratum reads in §2 are disclosure by construction.
- **Trade-off (accepted):** (a) the binding result is a **basket** claim ("AVWAP-4h reversals are net-tradable
  as a portfolio"), **not** a per-instrument tradability claim; (b) the three strata become **disclosed** —
  per the EXP-032 contaminated-by-disclosure precedent, a future *clean* per-instrument counted read on these
  three strata is permanently mildly weakened. The operator judges the basket claim the appropriate one given
  the cross-exit/cross-instrument robustness, and accepts the disclosure cost.
- **Holdout** (final 30% global) is **never** touched — outside this read entirely.

## 4. Power pre-registration (honest, before the read)

Pooled TEST n is **modest** — order ~80–100 basket events (vs ~30 per cell), to be confirmed at execution.
This materially improves on the per-cell power that produced `INCONCLUSIVE_SPANS_ZERO` at n=27 (EXP-032), but
**`INCONCLUSIVE` remains a possible and acceptable honest outcome** and is **not** a failure. Pre-registered:
a non-confirming or inconclusive portfolio read closes HYP-004 at G-018 with the basket disclosed and 0
counted reads spent; it does not trigger a per-instrument counted read.

## 5. What does NOT change (frozen)

The frozen referee suite as the binding qualifier (`ASS` non-binding, G-017); the D4 G-018 conjunction; the
D4/D9 separability legs and constants (`K_tail=3.0, τ_tail=0.06, δ=0.40`, S2 floor n≥120); the WF-EXPANDING
schedule (§D5) and the D4.1 one-WF-run rule; the 2-lifetime-read cap; the EXP-083 hash-pinned valid set; the
EXP-085 cost model. This amendment changes only the **unit of analysis** (portfolio) and the pinned arm, and
records the consequent disclosure accounting.

## 6. Operator ratification (RESOLVED 2026-06-22)

1. **Pinned exit = `AVWAP-FH`** — **RATIFIED** (per §2 rationale: parameter-free; genuine continuous-tail S2
   pass, not stop-truncation-to-point-mass).
2. **Ledger accounting = portfolio-disclosure** (0 counted, strata disclosed, basket-only binding claim) —
   **RATIFIED** (§3 trade-off accepted).

Both legs resolved → status RATIFIED. The multiplicity-registry EXP-084 row is updated (unit = portfolio,
leg (b) satisfied, disclosure accounting), and EXP-084 enters the pipeline at Stage 1 (scope). **No TEST data
is read before the manual execution gate.**
