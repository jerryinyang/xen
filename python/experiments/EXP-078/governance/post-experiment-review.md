# EXP-078 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS`/VAL-003, Phase 017 CF-CAPGEO-001)
**Reviewer:** research-pipeline consolidated governance
**Date:** 2026-06-21
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-capgeo-001/INDEX.md`, `docs/experiments-docs/INDEX.md`, `docs/signal-registry/{multiplicity-registry.md, candidate-families/cf-capgeo-001.md, test-read-ledger.md}`
**Governing D0:** `checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md` (FROZEN)

---

## Constraint evaluation

### Core constraints
- **Simplicity / no academic-finance pitfalls** ✓ MC false-positive/true-positive rates with Wilson
  intervals + paired k-sweep of existing dispositions; distribution-free dip-test + robust gap; no
  normality/stationarity/iid assumption (synthetic known-truth substrate).
- **Strict scoping** ✓ Single question (shape discrimination + `k`-robustness); 3/3 checks, 4/4 plots,
  0 new modules + 1 in-family extension — within budget; no bonus analyses.
- **OOS holdout / look-ahead / real-price** ✓ N/A-synthetic, stated and verified: code imports
  `from xen import ass` only, no timebars loader; no HA/Renko prices; ATR-unit synthetic. Determinism
  enforced; `k` never enters a draw seed.
- **Safe performance** ✓ bounded memory, `tqdm`, order-stable parallelism, byte-identical second pass.

### Audit (`audit.md`) — verdict forensics confirmed present and autonomous
- **Verdict forensics present** ✓ Run autonomously (not contingent on anyone questioning the result).
- **Per-stratum masking check** ✓ The audit affirmatively re-derived the pooled "B detection FAIL" and
  exposed the masked 2-way shape split (`B_neg`/`B_strong` detect; `B_zero`/`B_pos` structurally blind,
  decay to 0 with n), and confirmed U false-flag is an n=30-floor-only effect (n≥60 passes). It did **not**
  accept the pooled verdict at face value.
- **Mechanism statement** ✓ Both legs blind to the subtle shape: gap leg because true |g|<τ_gap=0.30
  (re-derived 0.25 / 0.067), dip leg because not dip-bimodal (dip_p≈0.99). K2 flip = shrinkage pulling the
  null toward a positive pooled prior (pool_mean=+0.518) against a margin frozen at k=120.
- **Gate-shape check** ✓ Explicitly identifies the diagnostic as the wrong instrument for the *subtle*
  version of its target shape — "effect of a shape this gate cannot see," not "no effect" — and records it
  for the interpreter without retro-editing the frozen gate.
- **Materiality & blocking** ✓ 0 Critical; the audit independently reproduced every binding number to rule
  out a bug manufacturing a spurious FAIL (mixture means to 1e-4, U0 false-flag exactly, sub-0.30 true
  gaps, K2 mechanism) → double-FAIL is implementation-faithful. The 2 Warnings each carry explicit
  materiality reasoning showing they cannot move the binding verdict (W1 K2 self-calibration noise on
  deployed-k labels; W2 the un-swept CI-coverage k-leg — routing already FLIPs on K2, and a missing
  disposition can only add flips). No verdict-material finding was documented-and-down-classified.

### Verdict representation (per-stratum) ✓
The binding verdict is the per-stratum `strata` dict; `collapsed_convenience_flag=false` is explicitly
NON-BINDING (LESSON-001 / EXP-076 audit C1 honored). No collapsed cross-cell boolean is binding.

### Gate-threshold calibration ✓
`τ_gap=0.30` is the frozen D0 bite-check ROC operating point (measured here, not re-tuned); the `k`-grid is
a pre-registered sensitivity band; the borrowed Wilson-hi 0.075 ceiling is disclosed (EXP-077 convention).
No unjustified magic constant.

### Results / report honesty ✓
`results.md` reports the FAIL plainly, maps to the pre-registered DISCOVERY_ONLY criteria, quantifies
uncertainty (Wilson intervals, true |g| values), carries both audit Warnings, and proposes follow-ups only
as new scopes (not extensions). `report.md` leads with the gate-shape headline and embeds the key plots.

### Registry & ledger disposition ✓
- **`multiplicity-registry.md`** — `ASS/VAL-003`/EXP-078 advanced `PENDING → SHAPE_DISCRIMINATION_FAIL +
  k_FRAGILE → DISCOVERY_ONLY input (2026-06-21)`; item **retained** (file-drawer negative). G-017 gate line
  annotated with the EXP-078 input and the pre-registered DISCOVERY_ONLY routing.
- **`candidate-families/cf-capgeo-001.md`** — gate row advanced to SLATE COMPLETE → routes to
  DISCOVERY_ONLY; three documented qualifier limitations recorded (subtle-bimodal blind spot; n≥60
  false-flag floor; k-fragile edge-call FPR). Family status correctly **unchanged** (REGISTERED —
  SCREENING-GATED): a qualifier-validation outcome, not a candidate screen.
- **`test-read-ledger.md`** — **UNCHANGED, 0 counted TEST reads** (synthetic only), stated explicitly. 0
  candidate slots.
- **Indexes** — `python/experiments/INDEX.md` row added; family detailed card + status added; master
  Family Indexes row + Current Checkpoint Status updated (no per-experiment card in master, per convention).

---

## Verdict

```text
VERDICT: APPROVE
```

All core and artifact-specific constraints pass. The audit carried full verdict forensics (per-stratum
masking check, mechanism, gate-shape) run autonomously; no verdict-material finding was down-classified
(0 Critical; both Warnings shown unable to move the verdict); the binding verdict is per-stratum with the
collapsed flag explicitly non-binding; and a complete signal-registry disposition was recorded for this
registry-relevant result (multiplicity-registry outcome retained, candidate-family limitations documented,
0 TEST reads confirmed). Determinism held → no PROTOCOL_DEFECT. The substantive DISCOVERY_ONLY outcome —
`ASS`'s shape leg only partially closes the EXP-074 gap — is faithfully recorded and routed to terminal
G-017 for adjudication at the Phase-017 checkpoint gate review.
```text
No Critical or Warning governance findings. Two audit Warnings carried as documented, materiality-justified
limitations.
```
