# Xen Experiments — Master Index (Chapter 02)

Live status + family navigation for the current chapter. Chapter 01 is archived at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first).

## Current Checkpoint Status
**No active phase — Phase 003 CONCLUDED 2026-07-01; awaiting next-phase G0.**

**Phase 003 — CF-MR-003 Tradability Concretization (CONC-1) — CONCLUDED 2026-07-01: CF-MR-003 RETIRED (SCREENED-ADMIT → NOT-TRADABLE at 1h + 15m).** [Retrospective](checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/retrospective.md) · [design.md](checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/design.md). The form-2 limit-at-anchor MR fade was concretized to net on the EXP-009 availability admits under the frozen referee (L-12), price-primary in-engine, per-stratum: **T1 exec-1h (EXP-010) NOT-TRADABLE (UNPOWERED)** — 0/5 powered/admit, episode sparsity < 1h floor 20; **T2 exec-15m (EXP-012) NOT-TRADABLE (POWERED)** — 24/24 powered (episodes 70–390 ≥ 15m floor 25), 0/24 admit, every CI_low ≤ 0 (net −0.77…+0.04 bps/active); F-1 vehicle fidelity PASS all 24 (1.00 / 0.97–0.99, discharges EXP-010 debt); F-2 tested (plant 24/24 + valid live phase-shift future-destroy clean; raw `REJECT_LEAK` was a mean-invariant-permutation false trip, superseded). Prereq **E7/EXP-011** froze the referee's 15m domain candidate-blind + hash-pinned before any 15m read. **Availability (EXP-009 SCREENED-ADMIT) does NOT survive to net at either horizon** — the capturable move < round-trip cost (same cost/capture veto as CF-MR-002 + AVWAP); CONC-2+ moot (no P-02 rescue). 1 slot consumed, 0 counted reads, holdout sealed, referee untouched, all 3 audits PASS 0 Critical. Prior: **Phase 002 (availability) — EXP-009 SCREENED-ADMIT.**
**EXP-009 COMPLETE (2026-07-01) — SCREENED-ADMIT (per-stratum, native vehicle; audit PASS, 0 Critical).**
The native re-screen (target-based reversion-to-anchor: anchor-hit / fraction-recovered / time-to-anchor,
event-specific half-life horizon, **screen-fail dislocation-matched null**) records **36 leak-clean
per-stratum passes** — S5_SPREAD 20 (FX majors), S3_DETREND 14, S4_OU 2; label-permutation collapses on
all. Positive hits across all 5 series (S1/S2 precision-limited, +5–8pp, UNPOWERED_HINT). Robust on
S5_SPREAD (18–20 across horizon/floor/z-edges), moderate on S3_DETREND (8–16); recent-third unconfirmed
(power). Null-choice validated the vehicle fix (screen-fail +5pp / random-extreme +2.5pp / random-timing
−29pp). **CF-MR-003 → SCREENED-ADMIT; EXP-008's EXONERATE was a vehicle artifact (L-13).** Availability,
not tradability — concretization = the family's **form-2 limit-at-anchor (target=mean)**, price-primary,
new D0. 0 slots / 0 counted reads, holdout sealed, referee untouched (L-12). Operator-steered:
dislocation-matched null + event-specific horizon + per-stratum reading + precision fixes each load-bearing.
**EXP-008 CLOSED (2026-07-01) — METHODOLOGY FINDING; family verdict HELD, not booked (L-13).** EXP-008 ran
three times and its value is methodological: (1) 3-leg screen → INCONCLUSIVE (inherited `Hurst-DFA<0.45`
leg structurally unsatisfiable on deviation *levels* — forensic A1); (2) 2-leg VR∧HL → EXONERATE; (3) a
**vehicle diagnostic (A2)** showed that EXONERATE is a **vehicle artifact** — the evaluation stack
(fixed-horizon signed-MFE-toward-anchor + Δ-over-regime-matched-**random-timing**) was **inherited from the
price-geometry family and is non-native to mean-reversion**. Under a **dislocation-matched** null the native
target metrics separate (**anchor-hit +2.9 pp**, fraction-recovered +2.7 pp, CIs exclude 0) while the MFE
metric is **blind**; the random-timing null reads spuriously negative on near-anchor bars. **EXONERATE HELD,
not booked.** CF-MR-003 stays **REGISTERED** with **preliminary positive native evidence** (small, ~+2.9 pp,
not cost-tested). Native re-screen = **EXP-009** (new D0, operator-gated): target-based estimands (anchor-hit
/ time-to-anchor vs fitted half-life / fraction-recovered / deferred limit-at-anchor P&L) against a
dislocation-**binned** null. Lesson **L-13**; **0 slots / 0 counted reads, holdout sealed**, referee
untouched (L-12).

**Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark** — **COMPLETED** (2026-06-30). D-referee ladder renewed; referee FROZEN (2026-06-29). `checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/design.md` · [`retrospective.md`](checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/retrospective.md).
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

**E7 — EXP-011 COMPLETE + FROZEN (2026-07-01, audit PASS, 0 Critical) — 15m-DOMAIN ADDED.** The frozen
renewed referee (§10.3a q\*=0.75 + E6 P\*-gate) gained a **15m trading domain** so CF-MR-003's exec-15m
cells can be adjudicated (Phase-003 Track 2 prereq). The extension is **four additive dict rows**
(DomainSpec/materiality/cost/episode + ADAPTIVE_DOMAINS), gate logic byte-unchanged. **Regression anchor
0/32 mismatch + E6 P\*-reduction-identity 32/32** → 1h/4h reproduce E3/E6 bit-for-bit. **15m battery
(16 inst): 16/16 DET_DOMINANT, dogfood+skew FPR 0.000, DENSE-powered 16/16, §10.3a STATE recovery ΔMDE
med 5.5 (all+) + SPARSE 15/16** — the E3a shape-recovery signature survives the domain change (clean
peer of 1h/4h). Sensitivity band {M∈.5/.75/1, N∈75/90/105, S∈20/25/30} **112/112, 0 flips**. Constants
**mechanically derived candidate-blind** (materiality 0.75 = √-period reproducing 1h/4h; floors 90/25 +
episode 17 = log-period interp; cost inherits per-instrument 1h). **Frozen + hash-pinned BEFORE any
CF-MR-003 read (L-12):** `referee_adaptive 96c940b5…`, `referee_calibration d10e6a27…`,
`incremental_referee 1b33e70a…`; `referee_pstar 1fd06b28…` unchanged == E6. analysis-only, 0 reads/0
slots, holdout sealed; not a rescue (referee prereq only). → unblocked EXP-010 T2a/T2b, since run + concluded (EXP-012 NOT-TRADABLE POWERED; CF-MR-003 retired).

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
| CF-MR-003 — cross-domain MR (deviation-from-higher-domain-anchor) | EXP-008, EXP-009, EXP-010, EXP-012 (+E7/EXP-011 referee prereq) | **SCREENED-ADMIT (EXP-009) → CONC-1 T1 NOT-TRADABLE (UNPOWERED) (EXP-010) → CONC-1 T2 NOT-TRADABLE (POWERED) (EXP-012, 2026-07-01): 24/24 powered, 0/24 admit at exec-15m; F-1 vehicle fidelity PASS (fixes EXP-010 debt). TRADABILITY CLOSED — availability does not survive to net at 1h or 15m; 0 new slots, 0 reads, holdout sealed. EXP-008 vehicle mismatch (L-13)**; `families/cf-mr-003/INDEX.md` |
| Referee-renew (D-referee) — 15m-domain extension | EXP-011 (E7) | **COMPLETE + FROZEN (2026-07-01): 15m domain added to §10.3a+P\* referee, FREEZE_LICENSED, hash-pinned, 1h/4h byte-unchanged. Analysis-only, 0 reads/slots.** Tracked in the referee-renew E-series live-status block above; not a candidate family. |
| CF-MR-002 — causal RSI-2 fade (cTrader-primary) | EXP-006 | **SCREENED — EXONERATED (NOT-TRADABLE 34/34, D-benchmark 2026-06-30)**; `families/cf-mr-002/INDEX.md` |

## Checkpoint Retrospectives
- [Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark](checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/retrospective.md) — COMPLETED 2026-06-30
- [Phase 003 — CF-MR-003 Tradability Concretization (CONC-1)](checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/retrospective.md) — COMPLETED 2026-07-01 · **CF-MR-003 RETIRED (SCREENED-ADMIT → NOT-TRADABLE at 1h + 15m)**
