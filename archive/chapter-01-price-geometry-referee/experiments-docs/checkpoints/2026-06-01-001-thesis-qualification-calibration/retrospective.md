# Phase 001 — Thesis-Qualification System: Referee Calibration — Retrospective

**Phase number:** 001
**Design finalised:** 2026-06-01
**Retrospective written:** 2026-06-03
**Status:** COMPLETED — all four planned experiments executed, governance-APPROVED, SUPPORTED.

**Design reference:** [design.md](design.md)
**Experiments:** EXP-001, EXP-002, EXP-003 (keystone), EXP-004 — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

Build a **referee** — the operator's 5-check gate stack — that judges whether a candidate
trading thesis deserves scarce validation resources, and in the same phase **measure what
that referee can and cannot see**: its per-domain false-positive rate (FPR), true-positive
rate (TPR), economic minimum detectable effect (MDE), and per-leg pass rates, on the 5m / 1h
/ 4h domains. The deliverable is a validation **methodology**, not a market edge.

The phase was structured so the gate stack is the *object under measurement, not the
conclusion*. Design §11 sets the bar explicitly: **success is *stating* the operating
characteristics — not the gate stack passing anything.** Two gating experiments (validated
substrate, correct referee logic) precede the keystone measurement, which is then
reality-checked against real strategies.

---

## 2. Outcomes vs objectives

| EXP | Role | Verdict | One-line outcome |
| --- | --- | --- | --- |
| 001 | H-substrate (gates the phase) | SUPPORTED | Substrate validated; gate PASS — downstream measurement is trustworthy. |
| 002 | Referee correctness (gates EXP-003) | SUPPORTED | Both referees correct; gate stack exposes all 5 legs, no short-circuit. |
| 003 | **Keystone — the measurement** | SUPPORTED | Per-domain stringency↔sensitivity map produced with usable precision. |
| 004 | Empirical anchor | SUPPORTED | Real dogfood consistent with the map, but turned out to be a *null* anchor. |

**EXP-001 — Synthetic Substrate Validation.** P0 aggregation integrity 56/56 PASS at the
{5, 240}-minute parameterizations this phase uses (extending VAL-001's {1, 15, 60}-minute
coverage). Both known-null generators produced gross oracle effects in [−0.087, +0.103] bps
with CIs bracketing zero; known-positives recovered the planted edge `m` within
`max(0.5 bps, 15% of m)`, to machine precision on high-sample cells. Five sub-material 4h
cells (BTCUSD m=1,2; USTEC m=1,2; XAUUSD m=1) were under-powered (INCONCLUSIVE) but all sit
below the 4h 3.0 bps materiality threshold, so the shortfall is economically immaterial —
exactly the precision limit §11 predeclared for 4h. **Substrate gate: PASS.**

**EXP-002 — Referee Golden-Fixture Correctness.** 10/10 verdict checks and 25/25
leg-exposure checks PASS on five deterministic fixtures; the gate stack records all five
legs for every fixture with no short-circuit; gate effect equals minimal effect minus the
1.0 bps cost in every row. Each leg's pass/fail path is isolated by a fixture, so EXP-003's
per-leg pass rates are well-defined. **Referee logic approved for measurement.**

**EXP-003 — Referee Operating-Characteristic Calibration (keystone).** The measured
stringency↔sensitivity trade-off, at α = 0.05:

| Domain | Gate FPR | Minimal FPR | Gate MDE | Minimal MDE | MDE inflation |
| --- | --- | --- | --- | --- | --- |
| 5m | 0.0 (0/4000) | ≈ α (0.023) | 1.0 bps | 0.5 bps | ×2 |
| 1h | 0.0 (0/4000) | ≈ α (0.025) | 4.0 bps | 0.5 bps | ×8 |
| 4h | 0.0 (0/4000) | ≈ α (0.032) | 12.0 bps | 2.0 bps | ×6 |

Gate FPR is 0 at every domain and every α in {0.10, 0.05, 0.01}. TPR rises monotonically to
1.0 across the edge grid; all 18 (domain, referee, α) MDE cells reach the usable-precision
gate (Wilson half-widths ≤ 0.03 FPR / ≤ 0.05 TPR) and yield a finite MDE. On nulls the
outcome legs each reject 100% of draws (L1 = L2 = 1.0; L3 = L4 = L5 = 0.0). **L5 materiality
is the binding leg** on positives near the MDE, which makes the gate MDE **α-invariant** —
the α grid moves only the minimal baseline's MDE. This table is the PS§6 "measured
stringency" deliverable: a gate "reject" now means *"no edge, or a net edge below ~1 / 4 /
12 bps per domain,"* with the blind-spot magnitude measured.

**EXP-004 — Real Dogfood Consistency Anchor.** All 48 cells (4 instruments × 3 domains × 2
strategies × 2 referees) returned REJECT and were classified consistent (`matched_reject`);
0 inconsistent, 0 inconclusive. Untuned Donchian(20) and MA(20,50) carry no positive edge
even gross of cost — gross effects span ≈ [−2.20, +1.32] bps/trade with every CI bracketing
or below zero. `block_length = 1` for all 48 cells (negligible per-bar autocorrelation; the
stationary bootstrap reduced to i.i.d. resampling). No synthetic-vs-real distribution gap
was surfaced.

---

## 3. Keystone reading (headline)

**H-keystone is BOUNDED, NOT CLOSED.**

The phase's central falsifiable claim asks, per domain: *is the gate stack's economic MDE
below the magnitude of plausibly-real intraday edges* — i.e., is the referee structurally
blind to real edges that matter?

- EXP-003 delivered the measured MDE map. This **is** the design's stated success
  deliverable (§11), and it was met: we now know the referee's blind-spot magnitude on every
  domain.
- The blind-vs-not-blind reading was designed to be finalised against an **empirical anchor**
  — EXP-004's real Donchian/MA effect sizes (design §4 / §10 / D-ceiling). That anchor turned
  out to be a **null / lower anchor**: the dogfood strategies carry ≈ 0 edge, sitting below
  every per-domain MDE. The gate's rejections of them are therefore **consistent with true
  negatives for qualification purposes** — no material positive edge was detected (gross
  effects' CIs bracket or fall below zero), so the gate does not false-positive on these
  strategies — but because no positive real edge was present near the MDE boundary, the data
  **cannot** show whether the gate would *detect* a genuinely weak real edge there, nor rule
  out a small edge below the detection threshold.

So H-keystone was **neither falsified nor positively confirmed**. Structural blindness is
**bounded** (no false positives observed; simple real edges demonstrably live below the MDE)
but **not closed** (no positive real edge was probed at the boundary). This open item is the
phase's headline finding, and it directly defines the next phase.

---

## 4. Lessons learned

1. **The anchor was the wrong shape.** The dogfood-anchor design assumed simple real
   strategies would *locate where plausibly-real edges live*. In fact untuned Donchian/MA
   have no detectable edge, yielding a null anchor instead of a positive one. Closing
   H-keystone requires a **substrate-validated candidate carrying a small *real* edge
   straddling each domain's gate MDE** — a near-MDE detection anchor.
2. **L5 materiality is the stringency lever.** The gate's stringency is almost entirely the
   economic-materiality leg: L5 is the lagging leg on positives and makes the gate MDE
   α-invariant. The statistical α knob barely moves the gate. Any future effort to retune
   gate sensitivity (the deferred loss-function phase) should target L5, not α.
3. **4h is power-bound, as predeclared.** With ~900–4,400 returns/instrument, the 4h gate MDE
   (12 bps) sits well above its materiality threshold (3 bps). 4h was fully resolved only at
   pooled (4-instrument) precision; per-instrument 4h would be under-powered.
4. **MDEs are domain aggregates.** Each MDE pools four instruments of heterogeneous cost
   (1–10 bps) and dispersion. Per-instrument MDEs could be lower — a natural refinement for a
   sharper dogfood comparison.
5. **Process discipline held.** The predeclaration-freeze / meta-Goodhart guardrail worked:
   referees were frozen before EXP-003, measured once, and never iterated against synthetic
   results. The EXP-001 → EXP-002 → EXP-003 gating chain functioned as designed. A reusable
   `python/src/xen/referee_calibration.py` module (both referees, paired-draw evaluation,
   block-bootstrap CIs, Wilson FPR/TPR, empirical MDE) is now available for future phases.
   `block_length = 1` everywhere is a useful empirical fact for future inference-unit choices.
6. **The chart-type data layer is still unused as a candidate source.** This phase ran
   entirely on time-bar OHLC domains (5m / 1h / 4h). The Line Break, Renko, and Heiken Ashi
   generators validated in VAL-001 were deliberately excluded as candidate signals
   (design §5 / §12). The referee is now calibrated and ready to judge chart-type candidates.

---

## 5. Phase verdict vs §11 criteria

**SUCCEEDED on its deliverable.** Each §11 success condition was met:

- (a) **Reject known-nulls at a measured FPR with usable precision** — ✓ gate FPR = 0,
  Wilson half-widths within the D-prec target.
- (b) **Trace TPR(m) per domain yielding a finite economic MDE at the α grid** — ✓ 18/18 MDE
  cells PASS.
- (c) **Per-leg diagnostics for the gate stack** — ✓ L5 identified as the binding,
  α-invariant leg.
- (d) **Dogfood strategies receive interpretable, consistent verdicts** — ✓ 48/48
  `matched_reject`.

Neither failure condition triggered: the synthetic substrate did **not** fail (EXP-001
PASS), and H-keystone was **not** falsified on any domain. The single open item — a positive
near-MDE anchor for the blind-vs-not-blind reading — is itself a clean, recorded finding, not
a failure of the phase.

---

## 6. Proposed next research direction

*(Proposed for operator decision — not committed. The next checkpoint's `design.md` will
formalise and require approval before any new experiment begins.)*

**Recommended spine — close the open keystone item:**

- **EXP-005 (proposed) — Near-MDE detection anchor.** Engineer a candidate that carries a
  small, real, predeclared edge straddling each domain's gate MDE, validated with the EXP-001
  substrate machinery, then run it through the frozen referees. This converts the null anchor
  into a near-MDE anchor and **directly tests the gate stack's structural blindness at the
  boundary** — the most direct way to close the one item Phase 001 left open.

**Secondary refinements (sharpen the existing map):**

- Per-instrument MDE map to resolve the four-instrument pooling caveat.
- Broadened untuned dogfood distribution (more lookbacks and strategy families) to
  characterise where simple real intraday edges actually sit.
- Materiality-threshold sweep tracing gate MDE vs L5 — the empirical groundwork for tuning
  gate stringency. 

**Programme-level deferrals now in view (design §12):**

- Tunable loss-function / operating-point phase — L5 is the identified lever.
- Walk-forward / regime-stratified split-protocol comparison — the Masters-style MCPT
  specimen is the natural first addition.
- Chart-type candidate signals — the validated Line Break / Renko / Heiken Ashi data layer
  is still unused as a candidate source.
- Incremental-information / ensemble candidate unit (beyond the standalone directional unit).

**Operator decision required:** which of these becomes the next checkpoint's spine. The
EXP-005 near-MDE anchor is recommended first, because it closes the single open keystone
question before the map is extended in any other direction.
