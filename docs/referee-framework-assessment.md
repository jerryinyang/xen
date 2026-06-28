# Xen Referee / Evaluation Framework — Assessment & Improvement Proposals

**Companion to** `docs/referee-framework-design-manual.md` (the neutral design description). This
document holds the **evaluative** content: documented weaknesses, problem statements, the
manual-author's observations, candidate improvement directions, a scope clarification, and the open
questions blocking the Chapter-02 Phase-001 G0 gate. It is **opinion-bearing by design** — keep it
separate from the design manual when soliciting an unbiased external description.

Section numbering continues from the design manual (which ends at §8).

---

## 9. Documented weaknesses (keystone L-12, plus supporting lessons)

The frozen referee is a **conjunction of fixed-threshold legs**, and that *shape* produced three
recurring failure modes that wrongly killed — or could not even test — real candidates. Patched ad
hoc each time across the chapter; never structurally fixed. This is lesson **L-12**
(`docs/knowledge-base/lessons-and-amendments.md`), the Chapter-02 renew target.

**Mode 1 — Conjunctive fragility.** Requiring all legs simultaneously drives FPR≈0 *but at a 2–8×
larger MDE* (EXP-003 keystone trade-off). A real-but-modest, tail-only, or sparse edge that any
*single* leg is structurally blind to is vetoed by the AND. The gate is theoretically ideal (no
false positives) yet a near-impossible bar that also rejects true positives — selection that favours
only large, location-shaped, dense edges.

**Mode 2 — Structurally-impossible legs.** A leg can have **no finite MDE** in a regime — no true
effect could ever satisfy it there, so it is an automatic fail, *not a test*. EXP-015's incremental
unit was REFUTED for exactly this (standalone-L2 had no finite MDE in high-overlap synchronous-null
cells) and the revised unit had to **drop** the leg; many CF-MR-001 cells were `COVERAGE_EXCLUDED`
for the same "no finite MDE on the carried arm" reason. Power was conflated with evidence-against.

**Mode 3 — Fixed thresholds mis-scaled to the candidate.** A threshold calibrated to a reference
vehicle mis-rejects a candidate of different sparsity/shape/instrument: the fixed per-bar MDE floor
wrongly REFUTED a ~6%-active signal via ~16× dilution (L-04); per-instrument MDEs run *below* the
pooled floor (EXP-008); inside CF-MR-001 a **fixed Sharpe=1.0 bite** and a **SUB-RANDOM-entry null**
both had to be swapped mid-family for an **MDE-curve co-designed with the band** (EXP-095) and a
**matched-distance** null (`D0-amendment-005`). The repeated manual fix had the same shape every
time: replace a fixed plant with a candidate-matched, power-aware construction.

**Supporting lessons.**
- **L-03** — a pooled/`.all()` verdict masks the binding stratum; emit per-stratum, pooled is
  disclosure-only until homogeneity is shown.
- **L-04** — vehicle mismatch (sparse vs per-bar) and gross→net cost erosion; match the vehicle,
  charge cost early.
- **L-06** — pooled-OOS CI must scale with pooled-OOS size (a multi-fold concatenation artifact
  inflated MDE).
- **L-08** — never build a null around a signal-derived target (biases toward ADMIT); bite-checks are
  two-sample MDE-curves, not fixed plants.
- **L-11** — framing/parity: a binary verdict overstates a within-noise wash; control/horizon parity
  must match the candidate's mechanism.

**Additional manual-author observations (not yet in canon — for review):**
- **a. Spec/implementation drift.** The L1–L5 leg names in `evaluation-framework.md` differ from the
  implemented legs (design manual §3): canon says "standalone-significance / CI-vs-naive"; code folds
  both into `L3_outcome` and renders `L2_integrity = True`. A gate whose specification and
  implementation disagree on what a leg means is a latent audit risk; the canon should be reconciled
  to the code.
- **b. The naive control is one fixed strawman.** L3 compares only against prior-return-sign
  momentum. A candidate could beat that specific control yet not a stronger one; the control is not
  candidate-matched.
- **c. Close-to-close legacy.** The frozen referee uses close-to-close returns; the Chapter-02
  standing convention is open-to-open on `≤ t-1`. The renew should decide whether to re-baseline.
- **d. Equal-weight pooling across instruments** within a domain can let one high-cost instrument
  (BTCUSD) dominate or veto (a Mode-1 / L-03 interaction).

---

## 10. Candidate improvement directions to experiment on

Predeclarable redesign levers for Phase-001 objective O1. Each must clear the freeze protocol
(design manual §5) on *fresh* draws and must **not** be tuned on the live benchmark candidate
(CF-MR-002).

1. **Power-aware leg gating (fixes Mode 2).** Before applying a leg, compute its finite-MDE in the
   cell; if no finite MDE exists, mark the leg **UNPOWERED** and exclude it from the verdict — never
   auto-fail. Report coverage explicitly. Generalizes the EXP-015→017 drop into a rule.
2. **Candidate-matched thresholds (fixes Mode 3).** Replace the pooled fixed MDE map with an
   **MDE-curve co-designed with the candidate** per vehicle/shape/instrument (generalize the EXP-095
   band pattern, L-08). Use per-instrument MDEs (known < pooled, EXP-008) where powered.
3. **Replace the hard AND with a calibrated composite (fixes Mode 1).** Forms to test (pick by a
   predeclared criterion):
   - **(a) Validity-then-economics sequencing** — validity/power legs (L1, coverage) gate
     *admissibility*; a *single* binding economic statistic (incremental net CI lower) decides edge.
     No structurally-blind leg can veto.
   - **(b) Calibrated soft-vote** — a weighted score over legs with a threshold set by the
     dogfood-negative FPR target; no single leg is a hard veto.
   - **(c) Single sufficient statistic + power guards** — the incremental net edge is the verdict;
     the others become reported diagnostics, not gates.
4. **Activity-rate-aware vehicle routing (fixes L-04).** A pre-leg classifier auto-routes per-bar vs
   event-level by measured active fraction, so the vehicle is never mismatched to sparsity.
5. **Reuse the partially-validated adaptive machinery (CF-CAPGEO-001 `ASS`/`WF`).** The
   Adaptive-Signal-Scoring estimator (`xen.ass`) — KDE + hierarchical empirical-Bayes shrinkage +
   bootstrap CI, reporting **expectancy + median + tail/bimodality** and `P(return > X)` — is
   **VALIDATED_WITH_GUARDS** (EXP-076/077): unbiased recovery, calibrated CIs at n≥30, with a
   ratified small-n guard (no expectancy edge-calls / defer to median at effective n≤60 on
   bimodal/asymmetric mean-null strata). The `WF-EXPANDING` walk-forward protocol is its companion.
   A candidate power-aware, shape-aware composite backbone. (Not yet fully ratified — terminal G-017
   awaits EXP-078; treat as a candidate, not a settled tool.)
6. **Per-stratum verdict representation by construction (fixes L-03).** Bake the per-stratum binding
   verdict + masking check into the gate output, not into downstream audit.

**Recommended posture.** Run the redesign **in parallel** with the retained frozen suite (dual
disclosure) until the new gate clears the freeze protocol on fresh draws. The success bar is
**improve, or at least preserve, FPR** on the dogfood-negative *while* gaining finite power on the
synthetic-positive cases the frozen gate failed (modest / tail-only / sparse). If no redesign beats
that frontier, the ratified outcome is a *documented decision that the frozen suite is not improvable
without losing FPR control* — itself a valid Phase-001 result.

---

## 11. Scope clarification — two distinct senses of "portfolio evaluation"

The word *portfolio* names two different things in this programme; keep them separate when
soliciting external opinions.

1. **Inside the frozen referee** — the **revised portfolio-fitness / incremental unit** (design
   manual §4, `incremental_referee.py`, EXP-013–019; MDE 12/16/32 bps). It answers: *does a single
   candidate C add incremental net edge beyond a reference signal R already in the book?* It is
   **portfolio fitness of one candidate**, not a multi-asset book evaluator. This is the referee
   framework's portfolio-evaluation component.
2. **Downstream of the referee (deployment stage)** — `xen.portfolio.py` (CF-MR-001 / EXP-095): a
   causal **equal-risk-contribution (ERC)** book over many per-cell net-return streams, with
   Ledoit-Wolf-shrunk covariance, a global vol anchor, a concurrent-risk cap, and an optional
   circuit-breaker, judged on **Sharpe / Calmar** bands with intra-position mark-to-market (L-09).
   This is a **multi-asset book-level evaluator** specific to a family that reached deployment — it
   is **not part of the frozen referee suite**.

Improving the *referee's* portfolio-fitness leg (sense 1) is a Phase-001 concern; the ERC deployment
portfolio (sense 2) is out of Phase-001 scope.

---

## 12. Open questions blocking G0 (operator decisions needed)

Predeclarations the O1 redesign needs before the G0 gate can pass. Genuine choices, not derivable
from the code:

1. **FPR target — the number.** The frozen suite's dogfood-negative FPR is ≈0. "Improve, or at least
   keep, FPR" needs an operational definition: (a) require new-gate FPR **≤** frozen (≈0) and seek
   power purely from power-aware exclusion/matching; or (b) **budget a small FPR** (e.g. ≤ α) in
   exchange for materially more power on modest/sparse edges. Which frontier do we commit to?
2. **Synthetic-positive battery.** Exact edge **shapes** the redesign must gain power on — dense vs
   tail-only vs sparse; sizes (sub-MDE to super-MDE); which instruments/domains. Must target the
   cases the frozen gate failed, predeclared so power is not cherry-picked.
3. **Dogfood-negative draws.** Reuse the EXP-019 dogfood construction or draw fresh? How many draws /
   what seed policy, so FPR is estimated with a stated Wilson half-width?
4. **Composite form commitment.** Predeclare *one* redesign shape (§10.3 a/b/c) or test several and
   select by a predeclared criterion (and if so, what criterion — and how is the multiplicity of
   trying several gates itself controlled)?
5. **Threshold-derivation rule.** If we adopt candidate-matched thresholds (§10.2), the *rule* that
   derives a threshold from a candidate must be fixed in advance (per-instrument MDE? band-co-designed
   MDE-curve?) — otherwise it is a tuning knob.
6. **Scope universe.** Recalibrate on the original 4-core (EURUSD/XAUUSD/BTCUSD/USTEC) or the
   17-instrument universe? Which domains (legacy 5m/1h/4h, or the CF-MR-002-relevant 1h/4h)?
7. **Return convention.** Re-baseline the referee to open-to-open `≤ t-1` (Chapter-02 standing
   convention) or keep the frozen close-to-close for parity with the retained suite? (§9c)
8. **Decision rule for "not improvable."** The explicit criterion under which Phase 001 concludes the
   frozen suite cannot be improved without losing FPR control (so the null outcome is falsifiable
   too).

---

*Companion design description: `docs/referee-framework-design-manual.md`. Weakness ledger:
`docs/knowledge-base/lessons-and-amendments.md` (L-12 keystone).*
