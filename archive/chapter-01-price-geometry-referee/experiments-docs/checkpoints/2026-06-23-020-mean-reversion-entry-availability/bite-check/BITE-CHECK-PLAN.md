# Phase 020 D2b Admission-Gate Bite-Check (precondition for the EXP-089 run)

**Status:** **PASS on the single-test legs (sha256 `f01a000b…`, 2026-06-23); EXTENSION REQUIRED before the
run** for the leg-2 conjunctive regime test. The binding D2b admission gate
(`xen.availability_gate.run_sub_screen` → `combine_axis`) was confirmed GREEN at the **CF-MR-001 6-sub-screen**
structure and C=46 for the single-test (beats-random) legs and the joint-max-of-6 FWER control. The **leg-2
design correction** (the three `/VOLREGIME` sub-screens now require **beats-random ∧ beats-CORE** under a
**regime-membership-shuffle-within-CORE** null) introduces a **new per-cell statistic and a new null** the
prior bite did not exercise — so checks **6–7** below are added and the whole bite is **re-run GREEN (new
sha)** before EXP-089. The single-test legs (checks 1–5) already passed.

**Deliverables:** `bite-check/bite_check.py` (Stage-3 developer artifact) → `bite-check/bite_check_report.json`
(byte-identical second pass), SEED `20260623`. **Nothing here reads market data, spends a slot, or touches the
holdout** — all fixtures are synthetic.

---

## Required checks (all must pass for `OVERALL: GREEN`)

1. **Not vacuous — pure-noise family.** Build a family of **six** pure-noise sub-screens (random conditioning,
   per-cell event counts preserved) over C=46 synthetic cells; run the joint-max permuted-axis gate. The
   family-level admission rate must be **≤ FWER (0.05)** (Wilson-hi ≤ ~0.075). This is the key new leg: the
   joint max across **6** sub-screens must not inflate the family admission above FWER (Phase 019 axes carried
   ≤4 sub-screens; CF-MR-001 carries 6).

2. **Not impossible — planted family.** Plant a **+0.20-ATR** favourable-availability lift on **≥5
   well-powered cells in exactly ONE** of the six sub-screens (the other five pure noise); confirm the family
   is **ADMITTED with high power** and the argmax sub-screen is the planted one (the lever is correctly
   named).

3. **Routing invariant across the sensitivity band.** Re-run checks 1–2 at FWER ∈ {0.025, 0.05, 0.10}
   (`S*` = Q975/Q95/Q90 of the joint null); the noise admission rate stays ≤ FWER and the planted family stays
   admitted with the same argmax at every level.

4. **MC stability.** The joint `S*` and the planted-family perm_p are stable between `N_PERM` 1000 and 5000
   (no routing flip); production runs use 5000.

5. **Determinism.** Byte-identical `bite_check_report.json` on a second pass at the fixed seed (permutation
   stream included).

6. **Leg-2 not vacuous — pure-noise regime.** In a `/VOLREGIME`-style sub-screen, assign regime membership at
   **random within each cell's CORE population** (preserving per-regime counts); confirm the conjunctive
   statistic `S = #(beats-random ∧ beats-CORE)` admits the sub-screen at **≤ FWER** (a noise regime adds ~0
   beats-CORE wins — `Δ̂_core ≈ 0` by construction, so the leg-2 conjunction does not manufacture admissions).

7. **Leg-2 not impossible — planted additive-edge regime.** Plant a regime subset carrying a **+0.20-ATR lift
   over the pooled CORE** on **≥5 cells** (CORE itself ≈ random, so the lift is genuinely additive, not
   inherited); confirm the `/VOLREGIME` sub-screen is **ADMITTED with power** and is named the argmax lever.
   Re-run checks 6–7 across the FWER band {0.025, 0.05, 0.10} and at `N_PERM` 1000 vs 5000 (no routing flip).

## Anchoring notes

- Reuse the Phase-019 fixture scaffold and `availability_gate` for the single-test legs verbatim; the leg-2
  conjunction + regime-membership null are the thin extension exercised by checks 6–7 (the same hooks
  `xen.vol_regime` adds for the production run). Do not re-implement the single-test gate.
- The realized C may drop below 46 if EXP-089 excludes RSI-MR cells on the D7 coverage **floor** (≥15; no upper
  bound); the bite is run at C=46 (the EXP-080-READY member count) and the gate self-calibrates `S*` to the
  realized C at run time.
- If any check fails, re-anchor `N_PERM` / `Q95` / the joint-null or the leg-2 statistic and record the change
  in a dated `D0-amendment-*`; do **not** loosen the FWER to force GREEN.

**On GREEN (extended):** record the new report sha256 in the Phase 020 D0 (`D0-predeclarations.md` status line)
and the multiplicity-registry Phase 020 batch; EXP-089 is then authorized.
