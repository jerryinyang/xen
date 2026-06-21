# Handoff Note — G-017 Gate Review + Phase 017 Retrospective

**From:** Phase 017 pipeline review (2026-06-21)
**Scope:** Adjudicate G-017 for CF-CAPGEO-001 (`ASS` qualifier + `WF-EXPANDING` protocol) and write the Phase 017 retrospective. Slate EXP-076/077/078 is complete; no `G-017-gate-review.md` exists yet.

## 1. Mechanical verdict — apply D5 (`D0-predeclarations.md` §D5), do not re-argue it

The D5 conjunction for `ASS_VALIDATED` requires **all** legs. Two binding legs FAIL → the verdict is **`DISCOVERY_ONLY`** (not `ASS_VALIDATED`, not `PROTOCOL_DEFECT` — determinism held byte-identically, so no protocol defect). Record it mechanically; the explanation is not predeclared (freeze the rule, not the story).

| D5 leg | Source | Result |
|---|---|---|
| Recovery in tolerance, all types | EXP-076 | **PASS** (198/198 cells; worst 0.722 vs 0.85·SE) |
| Shrinkage monotone in n | EXP-076 / 078 K1 | **PASS** (K1 invariant across k-grid) |
| FPR ≤ 0.05 margin-calibrated, all nulls | EXP-077 | **PASS** (U0 crossings are MC noise at z≤+0.41; Wilson-hi sub-gate holds) |
| MDE finite per domain | EXP-077 | **PASS** |
| `P(>X)` reliability in band | EXP-077 | **PASS at X=0/0.05/1R**; X=2R slope-gate artifact (max-gap excellent) — disclose as gate-shape, do not retro-edit |
| Counted-read accounting honors 2-read cap | EXP-077 | **PASS** (8/8 scenarios; 0 counted reads) |
| **Shape diagnostic discriminates, controlled false-flag** | EXP-078 | **FAIL** — blind to subtle median-positive bimodals `B_zero`(\|g\|=0.25)/`B_pos`(\|g\|=0.067); U false-flag >0.05 at n=30 |
| **k-sensitivity routing-invariant (or bounded+disclosed)** | EXP-078 | **FAIL** — K2 edge-call FPR routing-flip at **k=240 (the 2× grid point)**, unbounded (→1.0 at k=500) |

**Verdict: `DISCOVERY_ONLY`.** `ASS` is non-binding discovery use in Phase 018; the **frozen referee suite remains the binding gate**. The multiplicity registry already records EXP-078 as `SHAPE_DISCRIMINATION_FAIL + k_FRAGILE (DISCOVERY_ONLY input)` — make the gate doc consistent with that.

## 2. Critical caveat to record in the verdict — synthetic-only external validity

The binding legs validated `ASS` against **known synthetic ground truth**, which is the *correct and only* method for recovery/coverage/MDE/FPR (no ground truth exists on real returns). **Do not weaken the gate over "it wasn't tested on real data."** But the gate doc and retrospective **must** record two genuine limits, because they bound what `DISCOVERY_ONLY` (and any future re-validation) can claim:

1. **i.i.d.-synthetic ≠ serially-dependent real.** All binding legs are i.i.d. by construction. The dependence-aware **moving-block bootstrap — the one bridge to real data — was exercised only in EXP-077's non-binding dogfood, with no ground-truth coverage check.** It is the least-validated component in the phase.
2. **Reliability (D2.4) was binding-on-synthetic / non-binding-on-real**, despite being the one leg that needs no ground truth and *could* run bindingly on real first-70% TRAIN folds.

Framing for the retrospective: synthetic is the **easy** case, so EXP-078's failure is a **lower bound** — real data cannot rescue it, which makes `DISCOVERY_ONLY` robust. The phrase "validated under `WF-EXPANDING`" in the EXP-077 docs slightly oversells; prefer "validated on i.i.d. synthetic strata carried by `WF-EXPANDING`."

## 3. Binding carry-forward conditions to attach to the `DISCOVERY_ONLY` verdict

Record these as conditions on any future re-validation of `ASS` to binding status (candidate EXP-079, for the retrospective/operator to decide — do **not** initiate):

- **C1:** validate moving-block CI coverage against a **dependent** synthetic DGP with known truth (e.g. GARCH / regime-switch), not just i.i.d.
- **C2:** make the D2.4 `P(>X)` reliability check **binding on real first-70% TRAIN folds**.
- **C3 (from EXP-076/077/078 guards):** carry the two per-stratum guards — defer expectancy edge-calls to the median at effective-n ≤ 60; bind reliability on max-gap when predicted-prob range is compressed — and treat **k as load-bearing** (the routing flips at the 2× grid point; do not assume robustness).
- **C4 (existing §7.1):** the bracket condition stands — any `ASS` use is valid only for realized per-cell `n ∈ [15, 8000]`, re-confirmed at the Phase 018 D0 once INFR-003 lands.

## 4. Process notes for the retrospective (not gate-blocking)

- **The gate doc is the overdue step.** Slate complete (EXP-078 post-exec governance done 2026-06-21), but no `G-017-gate-review.md` had been written — this note exists to unblock that.
- **Uncommitted work:** EXP-076/077/078, VAL-005, all three new checkpoints (017/018/INFR-003), and the registry edits are untracked on `main`, while every prior experiment was committed as its own unit. The registry dispositions are on disk but not committed.
- **Governing `design.md` was amended mid-phase** (2026-06-20 14:32) to add `LESSON-001` / the §8 per-stratum-verdict guardrail, retrofitted from EXP-076's C1 audit. Legitimate reactive hardening; note it as a lesson (freeze design alongside D0 next time).
- **Phase 018 skeleton** is correctly `DRAFT — GATED, NOT OPENED` and self-blocks on `(INFR-003 ∧ VAL-005) ∧ G-017 ASS_VALIDATED`. Since G-017 = `DISCOVERY_ONLY`, the retrospective must update the Phase 018 precondition: it opens with the **frozen referee suite as the binding gate and `ASS` as a non-binding discovery overlay**, not "once `ASS_VALIDATED`."
