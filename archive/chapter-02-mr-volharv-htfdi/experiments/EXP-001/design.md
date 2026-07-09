# EXP-001 — E1 Cost-Control Arm (referee renew, D-referee)

**Branch:** `referee-renew-phase-001`. **Checkpoint:** Phase-001 §D0 (E1).
**Classification:** **analysis-only** (synthetic substrates + frozen referee primitives; generates no
price edge). **Reads/slots:** 0 counted TEST reads, 0 candidate slots, global holdout sealed.
**Consumes E0 (frozen):** `referee_adaptive.ROUND_TRIP_COST_BPS_17`, open-to-open `≤t-1` returns.

## Question (one, falsifiable)

**How much of Component A's economic-MDE inflation is the per-held-bar cost convention (F3) rather than
the conjunctive gate shape?** Concretely: for a **persistent (low-turnover)** signal, does charging the
round-trip **once per holding episode** (B-style amortization) instead of **on every held bar** (the
frozen `strategy_return_bps`) lower the gate-stack MDE at equal-or-better FPR — and by how much, per
stratum?

This isolates the **accounting** contribution to L-12 Mode-1 *before* any gate-shape redesign (E3). If
amortized cost recovers most of the lost power on persistent signals, the composite redesign only needs
to target the genuine tail-only/sparse residue.

## Why this is the right first arm

Auditor-2 (code-verified F3/F9): A charges `cost_bps` on **every active bar** (`strategy_return_bps:538`);
B amortizes `cost_bps/episode_length` (`incremental_referee.py:131`). For a signal that holds a direction
across an episode of length `L`, A pays ≈`L×` the round-trip it actually incurs. Worst on high-cost
instruments (BTCUSD 10 bps). The "pooled-domain veto" the assessment blamed on the AND / equal-weight
pooling is partly A over-charging turnover.

## Data views / substrate

- **Real returns:** open-to-open `≤t-1` (E0 primitive) per instrument×domain, first-70% analysis slice
  only, on the **17-instrument universe × {1h, 4h}** (Q6). Block length estimated on the train P&L series
  (frozen rule). Holdout never loaded.
- **Positions (the critical design choice):** **blockwise-persistent** states of domain episode length
  `L ∈ EPISODE_LENGTHS` (`1h:8, 4h:4`), reusing `incremental_referee._blockwise_state`. This makes
  turnover `< 1/bar`, so the two cost conventions **diverge**. **Negative control = strictly-alternating
  positions** (`+1,-1,+1,...`): there every active bar is a fresh entry so the conventions coincide
  exactly (verified). NB (smoke-test 2026-06-28): iid `random_state_positions` is **not** a coincide-
  control — it has run structure (mean run ~2), so it is a *persistence level*, not L=1.
- **Planted positive:** `plant_positive_edge` (constant drift, the existing substrate — the non-constant
  Q2 battery is E2's job) added on the persistent states across `EDGE_GRID_BPS`.
- **Null (FPR):** `permuted_returns` (bar-permutation) and `random_state_positions` re-blocked to length
  `L`, no planted edge — the dogfood-negative analog available pre-E2.

## Method (per stratum: instrument × domain × episode-length)

Two cost conventions, identical everything else (same draws, seeds, split, bootstrap):

1. **A-per-held-bar** — frozen `strategy_return_bps` (cost on every active bar).
2. **A-amortized** — new `strategy_return_bps_turnover`: charge `cost_bps` **once per entry** (position
   change into a non-zero state), zero on held bars. Total = one round-trip per holding episode = B's
   economic convention for a standalone signal. (Equivalent total to `cost/L` per bar; per-turnover is
   the faithful standalone analog.)

For each convention measure, on the frozen gate stack (`gate_stack_core`/`row`, unchanged):
- **FPR** per stratum on the null substrates (Wilson half-width reported; draw count stated — never "≈0").
- **MDE** = smallest `EDGE_GRID_BPS` level the gate passes at the calibrated FPR (DETECTED_FLOOR style).
- **DET point** = (FPR, MDE) per stratum.

**Binding comparison (per stratum, non-pooled — L-03):** `ΔMDE = MDE_perheld − MDE_amortized` at
matched FPR. Pooled/aggregate ΔMDE is **disclosure-only** until cross-stratum homogeneity is shown.

## Predeclared interpretation criteria

- **ACCOUNTING_MATERIAL** (per stratum): amortized DET-**dominates** per-held-bar — `MDE_amortized <
  MDE_perheld` at FPR_amortized ≤ FPR_perheld. Report the ΔMDE distribution across strata and its
  dependence on cost (expect largest ΔMDE on BTCUSD / high-cost, longest `L`).
- **ACCOUNTING_IMMATERIAL** (per stratum): `ΔMDE ≈ 0` within bootstrap noise → for that cell Mode-1 is
  gate-shape, not accounting.
- **NEGATIVE-CONTROL CHECK (must hold):** on the **strictly-alternating** arm the two conventions coincide
  exactly (every active bar an entry → identical net series, `ΔMDE = 0`, FPR identical). A divergence
  there = implementation bug → fix + rerun (Stage-4 material). (Verified at smoke-test.)
- **Shape-aware read:** report ΔMDE vs cost_bps and vs `L`; a monotone increase is the F3 signature.

This experiment **does not** adjudicate any candidate, change the frozen gate, or claim deployability. It
quantifies one accounting effect to inform E3's composite scope.

## Leak tripwire(s)

- **Cost-monotonicity tripwire:** amortized cost ≤ per-held-bar cost for every stratum by construction
  (one round-trip ≤ `L` round-trips); any stratum where amortized FPR or MDE is **worse** with `L>1` is a
  bug. (Charging less cannot raise the economic floor.)
- **Strictly-alternating control** (above): the conventions must coincide exactly at `L=1`.
- **No-real-edge guard:** planted edge is the *only* source of signal; with edge 0 on real returns both
  conventions must reject at the null FPR (no phantom positive from the cost change).

## Complexity budget

Comparative experiment: **stat work** = FPR + MDE per (17×2×{persistent,flip}×2 conventions);
**visualisations** 3 (ΔMDE vs cost; ΔMDE vs L; DET per-stratum); **new code modules** 1
(`strategy_return_bps_turnover` + the E1 harness in `code/`). No new shared `xen` module beyond the one
turnover-cost helper (candidate for `referee_adaptive` if reused).

## Success / failure / inconclusive

- **Success:** a per-stratum ΔMDE map with the negative control holding, answering "how much of Mode-1 is
  accounting." Either outcome (material or immaterial) is informative.
- **Failure:** negative control breaks (conventions diverge at `L=1`) or the monotonicity tripwire fires →
  bug, fix + rerun.
- **Inconclusive:** bootstrap noise swamps ΔMDE at the chosen `N_BOOT` → raise resamples or report the
  bound.

## Metric denominators / zero-baseline

MDE in bps on the EDGE_GRID; FPR as a Wilson-bounded proportion over a stated draw count. Active-bar
denominator unchanged from the frozen gate. Zero-edge draws define the null; a stratum with no finite MDE
under a convention is **UNPOWERED** for that convention (reported, not failed — Mode-2 discipline, E3 rule
previewed).

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-28)

Checked against `references/governance-constraints.md` + checkpoint §D0:
- **Classification** analysis-only — correct (synthetic substrates + frozen primitives; no price edge). ✓
- **Holdout** sealed; first-70% only. ✓ **Reads/slots** 0; no candidate adjudicated → no registry slot. ✓
- **Per-stratum binding** ΔMDE, pooled disclosure-only (L-03). ✓ **Leak tripwires** shipped (monotonicity,
  persistent-vs-flip control, no-real-edge guard). ✓
- **Scope** tight on the cost-convention question; no gate-shape change (that is E3). ✓
- **Substrate caveat (noted, not blocking):** uses the constant-drift plant — correct for E1 (non-constant
  battery is E2); ΔMDE conclusions are conditioned on the persistent blockwise position shape, as scoped.
- **Mode-2 preview:** UNPOWERED-not-FAIL reporting for no-finite-MDE cells. ✓

No REVISE issues. Proceed to Stage 2 (implement `strategy_return_bps_turnover` + the E1 harness).
