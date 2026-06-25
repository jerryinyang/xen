# G-021 Gate Review — RSI-2 Fade Capture-Geometry & Tradability (Terminal)

**Date:** 2026-06-24
**Gate:** G-021 (Phase 021 terminal gate — **tradable / not-tradable / inconclusive** verdict on the **bare
RSI-2 fade (CORE)** admitted at G-020, by a net-of-cost capture-geometry screen + a one-shot counted TEST read).
**Adjudication basis:** the predeclared **D6 decision rules** (`D0-predeclarations.md` §D6/4c) over the **frozen
referee suite** (D4), cost from the **EXP-085 conservative model** (D3, `D0-amendment-003`); carried set + Holm
sizing per **`D0-amendment-006`**. Rubric frozen pre-run in [`G-021-gate-criteria.md`](G-021-gate-criteria.md).
The `ASS` qualifier is **non-binding** (G-017).
**Outcome:** **TRADABLE.** The one-shot EXP-093 TEST confirms **8 of 11 carried (instrument, domain) cells**
under the frozen referee + phase Holm-11 + the per-cell margin (`Holm-adj p = 0.0011 ∧ net ci_low_1s > margin`),
across **7 instruments and both domains**. Per the mechanical rule (`TRADABLE iff ≥ 1 carried cell CONFIRMS`),
the bare RSI-2 fade with EXIT-RCT is the programme's **first net-positive out-of-sample price entry**.
**Reads / holdout:** EXP-093 spent **11 counted TEST reads** (one per carried stratum, each 0→1; cap 2/stratum
honored); the **final-30% global holdout was never loaded**. `test-read-ledger.md` updated in the same change
(other 37 strata stay 0/2). **0 additional candidate slots** (the first was consumed at G-020).

> **Scope note.** G-021 decides tradability on the **analysis-TEST stratum** under the frozen suite. It does
> **not** release the final-30% global holdout (a separate, later one-shot gate) and does **not** re-open the
> inert vol-regime partition, the dead TREND/FILTER variants, or any registered-but-deferred branch (each needs
> its own D0-amendment + slot decision).

---

## 1. Decision

The verdict is adjudicated by the predeclared D6/4c mechanical rule over the 11 carried cells (Holm-11,
one-sided α=0.05; margin = the cell's EXP-090/094 MDE):

```
Cell CONFIRMS    iff Holm-adj p <= 0.05  AND  net ci_low_1s > margin
G-021 TRADABLE   iff >= 1 carried cell CONFIRMS
```

| Carried cell | n_resolved | net_ci_low | margin | Holm-adj p | per-cell verdict |
| --- | --- | --- | --- | --- | --- |
| EURUSD-4h | 454 | +0.094 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| XAUUSD-4h | 388 | +0.072 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| USDCHF-4h | 458 | +0.062 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| AUDJPY-4h | 457 | +0.057 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| EURJPY-4h | 430 | +0.044 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| GBPJPY-4h | 453 | +0.039 | 0.025 | 0.0011 | **CONFIRM** (mean-AND-median +) |
| US2000-1h | 1613 | +0.073 | 0.0125 | 0.0011 | **CONFIRM** (mean-carried, median ≈ 0) |
| USTEC-1h | 1668 | +0.046 | 0.0125 | 0.0011 | **CONFIRM** (mean-carried, median −0.026) |
| NZDUSD-1h | 1677 | −0.015 | 0.0125 | 1.000 | INCONCLUSIVE (near-zero) |
| EURUSD-1h | 1619 | −0.032 | 0.0125 | 1.000 | EVIDENCE_AGAINST (net-negative OOS) |
| GBPUSD-1h | 1653 | −0.103 | 0.0125 | 1.000 | EVIDENCE_AGAINST (net-negative OOS) |

| Family statistic | Value |
| --- | --- |
| Carried cells (Holm family) | **11** (`D0-amendment-006` — full EXP-092 SEQUENCE_PASS set) |
| Cells CONFIRMing | **8** (6×4h + USTEC-1h + US2000-1h) |
| Holm-adj p (each confirm) | **0.0011** (= 11 × 9.999e-5, monotone step-down) |
| Breadth | 7 distinct instruments, **both** domains |
| Counted TEST reads spent | **11** (each carried stratum 0→1; cap 2/stratum honored) |
| Candidate slots | **0** (first consumed at G-020) |

**The TRADABLE conjunction holds** (≥ 1 carried cell CONFIRMS — 8 do, with breadth). Per the D6 routing table
this is the programme's **first net-positive out-of-sample price entry**.

## 2. Relationship to the predeclared D6 verdict rule (mechanical)

`D0-predeclarations.md` §D6/4c and `G-021-gate-criteria.md` §2 fix the rule **before** any cell's outcome was
seen: `TRADABLE iff ≥1 carried cell CONFIRMS (Holm-adj p ≤ 0.05 ∧ ci_low_1s > margin); NOT_TRADABLE iff the
screen is empty or every carried cell fails; INCONCLUSIVE iff the binding reads are power-limited / span zero.`
The realized counts resolve the rule to **TRADABLE** with no discretion: 8 confirms, Holm-correct, each above
margin, power-confirmed (n 388–1677 ≫ the EXP-090/094-calibrated floors). No threshold, cost, margin, referee,
or Holm sizing was retro-edited (§3.8 no goalpost-moving).

## 3. Adjudication checklist (G-021-gate-criteria.md §3 — affirmatively confirmed)

1. **Substrate readiness (EXP-090/094).** Member set = the 15m/1h EXP-090 members + the 4h EXP-094 ADMIT_4H
   members; carried cells all have finite per-cell MDE; realized counts quoted (supersede design figures). ✓
2. **Screen integrity (EXP-091/094).** Net computed under the EXP-085 conservative cost (`D0-amendment-003`);
   EXIT-RCT the only arm to pass the quorum; native-vs-contrast reported (RCT > RSI-revert-on-close). ✓
3. **Candidate set (EXP-092).** `SEQUENCE_PASS` set hash-pinned (sha256 `f6427e83…`) + Holm rule fixed before
   the TEST read; carried set ratified at `D0-amendment-006` (all 11; Holm-11). ✓
4. **Fill-model honesty.** 1m fills by timestamp alignment, causal order-of-touch (conservative adverse-first;
   `tie_break_frac ≈ 0`), real touched fill prices; RCT model-derived-target caveat carried. ✓
5. **TEST discipline (EXP-093).** Each carried (instrument, domain) cell spent **exactly 1 counted TEST read** on
   the **analysis-TEST stratum**, recorded in `test-read-ledger.md` in the same change; **2-lifetime cap honored
   (each 0→1)**; the **final-30% global holdout never loaded** (audited: ~561k holdout rows/file not read; fill
   clipped at the analysis edge); margin condition applied alongside Holm. ✓
6. **Referee fidelity.** The binding gate was the frozen estimator family (moving-block net lower bound + Holm),
   not retro-edited; `ASS` non-binding; no new referee tuned. ✓
7. **Integrity.** Determinism byte-identical (replay + independent raw re-derivation reproduced the headline
   numbers bit-for-bit via `xen.ass`); real-price ATR metrics; no parameter tuned against TEST/holdout; no
   deviation. ✓
8. **No goalpost-moving.** Frozen D2/D3/D6 not retro-edited after seeing any cell's outcome. ✓

## 4. Mechanism (why TRADABLE, and what carries it)

The confirm is driven by the **robust core** — the six 4h cells, mean-AND-median positive — where the
EXP-091/092 mechanism reproduces out-of-sample: the RCT reversion-completion target (~0.28 ATR) is reached ~99%
of events, and net stays positive after conservative cost because the fixed-bps round-trip is a **small ATR
fraction on the larger-ATR 4h domain**. The two 1h confirms (USTEC, US2000) clear the binding **mean** gate but
are **mean-carried** (USTEC TEST median −0.026) — the family's known median-fragility, 1h-specific. The fragile
1h tier **reversed OOS** (EURUSD-1h/GBPUSD-1h net-negative; NZDUSD-1h near-zero): these had the thinnest TRAIN
margins and did not survive the uniform TRAIN→TEST selection-overlap shrinkage (Δ net_ci_low −0.005…−0.107),
exactly the honest *availability ≠ capturable edge* prior — with the strongest cells holding. GBPUSD-1h's
EVIDENCE_AGAINST was pre-flagged at `D0-amendment-006 §2`; its read was spent as ratified.

## 5. Programme routing (mechanical consequence)

**TRADABLE** → the bare RSI-2 fade (CORE) with EXIT-RCT is the programme's **first net-positive price entry**.
Next moves, each a **separate** gate/scope (not part of G-021):

- A sanctioned **global-holdout release** decision for the mean-AND-median-positive **4h robust core** (the
  EXP-032-analog one-shot final confirmation; its own checkpoint/D0/governance). Each carried stratum has **1/2**
  counted reads remaining.
- A **realistic time-aligned, equal-risk portfolio** diagnostic (cross-instrument correlation; annualized
  Sharpe/drawdown) to size the economic case before spending the holdout shot.
- The **deferred levers** (vol-regime, contrarian, 25/75, 15m capture, faster-cost sensitivity), each under its
  own dated `D0-amendment-*` + slot decision.

## 6. Integrity expectations at adjudication (carried — all met)

- **Holdout sealed** throughout Phase 021; the final-30% global holdout never loaded (incl. its 1m bars). ✓
- **TEST discipline:** counted reads only at EXP-093, analysis-TEST stratum, 1/carried-stratum, cap 2/stratum
  honored, recorded in `test-read-ledger.md` in the same change. ✓
- **Determinism / real-price:** byte-identical replay; raw re-derivation matched bit-for-bit; ATR-unit metrics. ✓
- **No goalpost-moving:** frozen D2/D3/D6 not retro-edited; per-stratum doctrine (LESSON-001) enforced — the
  binding verdict is per cell, the routing readout is a disclosure. ✓
- **File drawer:** every exit-family and cell outcome (EXIT-RCT survives; ERT + 4 conventional arms died at
  EXP-091/094; the 3 non-confirming 1h cells) is **retained** in the registry and the Phase 021 multiplicity
  batch, never deleted or reopened by re-parameterization. ✓

---

*Companion documents: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) §D6 ·
[`G-021-gate-criteria.md`](G-021-gate-criteria.md) · [`D0-amendment-006.md`](D0-amendment-006.md) ·
EXP-093 [`report.md`](../../../python/experiments/EXP-093/report.md). Phase 021 retrospective:
[`retrospective.md`](retrospective.md).*
