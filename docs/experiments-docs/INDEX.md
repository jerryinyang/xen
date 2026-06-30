# Xen Experiments — Master Index (Chapter 02)

Live status + family navigation for the current chapter. Chapter 01 is archived at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first).

## Current Checkpoint Status
**Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark** — D-referee COMPLETE; renewed
referee FROZEN (2026-06-29). `checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/design.md`.
Dual purpose: (1) **referee renew (DONE — gate frozen at E5, §10.3a, q\*=0.75)**; (2) end-to-end
benchmark of the rollover via the causal RSI-2 fade (CF-MR-002). 0 slots / 0 reads; global holdout sealed.

**D-benchmark COMPLETE (2026-06-30) — EXP-006 NOT-TRADABLE 34/34, CF-MR-002 EXONERATED (audit PASS, 0
Critical).** The causal RSI-2 fade (engine-realized `P*` intrabar fill) adjudicated under 3 referees
(frozen Chapter-01 / §10.3a position-state proxy / **E6 P\*-capable gate** `referee_pstar.gate_stack_pstar`)
on 17×{1h,4h}: **all gates REJECT every cell**; net P&L negative on all 34 (−0.03…−9.66 bps/active bar);
the faithful P\*-realized gate's ci_lower<0 everywhere. Binding leg = **L3 absolute neutral floor** (the
fade beats a naive momentum baseline — vs-naive +0.87 @ EURUSD/1h — but is **net-negative in absolute
terms**: exactly the floor §10.3a has and variant-c lacked, E5/L-12). **T1 future-destroy 0.000/34, T2
provenance 34/34 → leak-clean**: the L-01 falsification lands on the *faithful* mechanism (real engine
intrabar fill, not a capped proxy). **O3:** Chapter-02's first price-primary run exposed + fixed 3 latent
`run-experiment.sh` infra bugs (stamp-suffix completion detection; flush race; report-json completion
gate) + 1 op note (parallel-rerun symlink race) + the frozen suite's 4-core cost-map limit (gate A 8/34,
renewed §10.3a generalizes). 0 reads/slots; holdout sealed; not tuned (L-12). The blocking that inserted
EXP-007 (E6) is resolved. (Prior block note retained in EXP-006 amendments A1/A2.)

**E6 — EXP-007 FROZEN (2026-06-29, audit PASS, 0 Critical) — ADOPT ratified at operator freeze sign-off;
`referee_pstar.gate_stack_pstar` hash-pinned (`results/freeze_manifest.json`, `referee_pstar.py
sha256=1fd06b28…4f23`; prior suites byte-unchanged, `referee_adaptive b4fd6cb1…ae847` == E5,
`referee_calibration 04f933f6…7994`). D-benchmark (EXP-006) resumes.**
Additive `referee_pstar.gate_stack_pstar` = §10.3a with the signal leg sourced from an injected
engine-realized series (one change; `referee_adaptive`/`referee_calibration` byte-unchanged, hash == E5).
Arm R reduction identity **32/32 bit-identical**; Arm N realized-fill FPR controlled (N1 symmetric 0/32,
N3 dogfood 0/32, N2 future-destroy max 1/80 single-draw artifacts ≤ 2α); Arm P finite power 32/32. Honest
caveat: returns-space bracket caps (not captures) — true intrabar `P*` capture is exercised by the real
engine in EXP-006. **Next (operator-gated):** FREEZE + hash-pin `gate_stack_pstar` → then **D-benchmark
(EXP-006) resumes**, adjudicating CF-MR-002 under frozen old suite + §10.3a proxy + the E6 P*-gate
(parallel disclosure). 0 reads/slots; holdout sealed; CF-MR-002 not tuned (L-12).

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

**D-referee ladder COMPLETE (E0→E5); renewed referee FROZEN. Next: D-benchmark (operator-gated).**
- **E4 — EXP-004 COMPLETE (2026-06-29, audit PASS, 0 Critical) — FREEZE LICENSED (RANGE-BOUNDED).**
  Baseline q\*=0.75 = **32/32 DET_DOMINANT** (adaptive dogfood FPR 0.0); safe q\* range **{0.7,0.75}**
  (extremes 0.6/0.8 each flip 1 stratum). Residual skew-FPR (A1.2) **refuted** — a strong right-skew
  null (skew≈3.6) gives **0/32** adaptive passes (studentized floor holds; no `Q_STUD_MIN` bump). All
  6 FPR_BROKEN across the sweep are single 1/162 label artifacts (`wilson_lower(1,162)>0` vs a zero
  frozen baseline) — gate true FPR ≤0.62% ≪ control, future-destroy max 0.050, leak-clean → recorded
  **E5 freeze-adjudication precondition** (min-pass-count≥2 / control-relative FPR rule), NOT a gate
  defect. Regression anchor 0/32 reproduces EXP-003; `referee_*` byte-frozen; bootstrap/seed stable;
  D-regime recent-third 30/32; 4h sub-pop CI non-degenerate (L-06). 0 reads, holdout sealed.
- **E5 — EXP-005 COMPLETE (2026-06-29, audit PASS, 0 Critical) — RENEWED REFEREE FROZEN.** Q4
  composite-form adjudicated by DET-dominance: **§10.3a (validity→economics, `adaptive_row`)
  matches-or-beats the single-statistic variant-c 32/32**; §10.3a leak-clean 32/32 (dogfood FPR 0/32,
  future-destroy ≤0.050). **variant-c REFUTED** — the single statistic (incremental-over-naive
  CI-lower>0) has **no absolute floor**, so it admits anything less-bad than a money-losing momentum
  baseline (dogfood FPR up to 1.0; **survives future-destroy** on BTCUSD/USDJPY/XAUUSD 4h);
  mechanism-general. §10.3a's neutral-CI + materiality + studentized-subpop legs are exactly what
  supply the FPR control the single statistic lacks. Renewed referee **FROZEN at §10.3a, q\*=0.75**
  (`freeze_manifest.json`, `sha256=b4fd6cb1…ae847`); variant-c recorded as the rejected alternative.
  **E4-derived less-brittle freeze-adjudication FPR rule** (`MIN_FPR_PASSES=2` / `2α`) adopted
  candidate-blind (adjudication only; gate byte-unchanged). Regression anchor **0/32** reproduces
  EXP-003/E4; variant-c added **additively** (70+/0−); `referee_calibration.py` byte-frozen. 0 reads /
  0 slots; holdout sealed; not tuned on CF-MR-002. Freeze is **before** any live read (L-12 honored).
- **E3b — FOLDED (2026-06-29):** return-series unit → E3a (A1); Q4 composite-form → E5. Dissolved as a
  standalone rung; retained in the registry as the record.

## Current Infrastructure Tasks
_(none)_

## Family Indexes
| Family | EXP range | Status |
|--------|-----------|--------|
| CF-MR-002 — causal RSI-2 fade (cTrader-primary) | EXP-006 | **SCREENED — EXONERATED (NOT-TRADABLE 34/34, D-benchmark 2026-06-30)**; `families/cf-mr-002/INDEX.md` |

## Checkpoint Retrospectives
_(none yet)_
