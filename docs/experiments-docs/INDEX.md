# Xen Experiments — Master Index (Chapter 02)

Live status + family navigation for the current chapter. Chapter 01 is archived at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first).

## Current Checkpoint Status
**Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark** — DRAFT, G0 PENDING (2026-06-27).
`checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/design.md`. Dual purpose: (1) referee
renew (fix gate rigidity, KB L-12); (2) end-to-end benchmark of the rollover via the causal RSI-2
fade (CF-MR-002). 0 slots / 0 reads; global holdout sealed.

**Referee-renew E-series (D-referee):**
- **E1 — EXP-001 COMPLETE (2026-06-28, audit PASS).** ACCOUNTING_MATERIAL: the frozen per-held-bar
  cost convention over-charges turnover ~L× on persistent signals; amortizing recovers ΔMDE
  1.0–11.5 bps/stratum (median 1.5), scaling with cost & L. L-12 Mode-1 partly accounting. Seam
  additive (`referee_adaptive.gate_stack_core_costfn`); frozen suite byte-unchanged.
- **E2 — EXP-002 COMPLETE (2026-06-29, audit PASS).** Frozen conjunctive gate is SHAPE-BLIND:
  structurally blind to SPARSE/event edges (**L1 readiness** veto, edge-independent, L-12 §2),
  degraded on STATE/sub-population (**L5 materiality** on the pooled-diluted mean, L-03), robust to
  DENSE+TAIL. FPR=0/32 both conventions + dogfood 0/64; leak tripwires held. Confirms L-12 §1/§2 and
  localizes blindness to **two named legs**. This is the EXP-019-style calibration substrate E3 is
  measured against.

- **E3a — EXP-003 COMPLETE + Amendment A1 (2026-06-29, re-audit PASS) — DET-DOMINANT 32/32.** The
  economic-leg adaptation (amortized + power-aware L3/L5 + **studentized** sub-pop L5 + L2 removed;
  **L1 proven bit-identical/rigid**) **DET-dominates the frozen gate on all 32 strata**: strictly
  lower MDE on **STATE** (ΔMDE median 7.5, max 23.5 bps) + recovers **sparse 28/32**, at dogfood FPR
  **0/32** ≤ frozen, no DENSE/TAIL loss, leak-clean (future-destroy collapses on the studentized
  path). D0 success met. **Design "sparse UNPOWERED" predeclaration REFUTED** (recovery is economic-
  leg, not L1); **E2's "sparse=L1 veto" was domain-conflated** (true 1h, false 4h). *A1 story:* the
  original raw-bps sub-pop q\*-quantile over-fired on high-σ 4h nulls (brittle "15 DET / 17
  FPR_BROKEN", 16/17 within Wilson noise of 0) → operator amend-in-place: **studentize** the sub-pop
  statistic (`q*-quantile/std > Q_STUD_MIN=Φ⁻¹(q\*)≈0.674`, candidate-blind) + Wilson-resolved verdict
  → cured the FPR leak **at the gate** (passes 0/162 on the prior-worst strata) with STATE recovery
  retained. This **pulls E3b's return-series/Sharpe-LB unit forward**. Frozen suite byte-unchanged.

**Next: E4 (robustness) → E5 (freeze) — the defect that blocked freezing is cured.**
- **E4 (next):** robustness sweep — `q*` sensitivity (DET-dominance + FPR=0 stable across
  `q*∈{0.6,0.7,0.8}`), bootstrap-count / seed stability, residual skew-FPR (A1.2). Due-diligence that
  licenses the freeze; don't freeze on an untested knob.
- **E5:** DET-adjudicate + **FREEZE** the adaptive gate, **with a mandatory folded Q4 composite-form
  check** (§10.3a vs single-statistic variant-c — predeclared, non-skippable, folded from E3b): freeze
  §10.3a only if it matches-or-beats variant-c, record variant-c as the rejected alternative.
- **E3b — FOLDED (2026-06-29):** return-series unit → E3a (A1); Q4 composite-form → E5. Dissolved as a
  standalone rung; retained in the registry as the record.

## Current Infrastructure Tasks
_(none)_

## Family Indexes
| Family | EXP range | Status |
|--------|-----------|--------|
| CF-MR-002 — causal RSI-2 fade (cTrader-primary) | _(EXP-IDs at promotion)_ | REGISTERED — G0 PENDING (Phase 001) |

## Checkpoint Retrospectives
_(none yet)_
