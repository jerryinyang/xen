# EXP-002 — E2 Synthetic-Positive Battery + Fresh Dogfood (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-001 §E2 (ladder line 133; Q2 118–120, Q3 121–122, Q5 123–124).
**Classification:** **analysis-only** (synthetic position substrates + planted edges + frozen referee
primitives; generates no price edge). **Reads/slots:** 0 counted TEST reads, 0 candidate slots; global
holdout sealed. **Consumes E0 (frozen):** `referee_adaptive.adaptive_cost_bps_for` (17-map),
open-to-open `≤t-1` returns. **Reuses E1:** `gate_stack_core_costfn` seam, `cost_conventions`,
the EXP-001 FPR/MDE harness scaffolding.

## Question (one, falsifiable)

**Does the frozen conjunctive 5-leg gate retain FINITE POWER on non-constant true edges (tail-only,
sparse/event, state-dependent), or is it structurally blind to any edge shape that is not
dense+location?** Concretely, per stratum × shape: at a calibrated FPR, is there a finite MDE on
`EDGE_GRID_BPS` for the same economic edge magnitude — or does the gate never detect it (no finite
MDE = UNPOWERED), while the DENSE anchor detects?

This builds the **EXP-019-style calibration substrate** (dogfood-negative for FPR + synthetic-positive
for power) that **E3's adaptive gate will be measured against**. E2 **characterizes the frozen gate
only** — it builds **no** adaptive gate and **tunes nothing** (the referee stays FROZEN until E5).

## Why this is the right second arm

L-12 names three failure modes of the conjunctive AND gate; E1 closed the **accounting** slice of
Mode-1 (per-held over-charge, ΔMDE 1–11.5 bps). The residual L-12 claim is **shape blindness**: a
real-but-modest, tail-only, or sparse edge that any single leg cannot see is vetoed by the AND
(L-12 §1/§2; L-04 sparse dilution; L-11 gate-shape). E2 measures that residue directly — same
economic magnitude, varied shape — so E3 knows **which** shapes the composite must rescue and which
the gate already handles.

## Cost convention (predeclared design decision)

**Bind on the amortized (accounting-clean) convention; report per-held in parallel as disclosure.**
E1 proved per-held injects a turnover-cost confound that inflates MDE **independent of shape**;
binding the shape-blindness read on per-held would conflate F3 accounting with shape sensitivity.
Amortized (`gate_stack_core_costfn(strategy_fn=strategy_return_bps_turnover)`) removes that confound,
isolating shape. The literal frozen gate is the per-held read — reported per stratum×shape for
continuity, but the **blindness map binds on amortized**. (Both are the *frozen* legs; only the
signal-leg cost accounting differs — the seam is the E1, audit-verified, bit-identical-at-`strategy_return_bps` wrapper. No leg threshold is changed.)

## Data views / substrate

- **Real returns:** open-to-open `≤t-1` (E0) per instrument×domain, **first-70% analysis slice only**,
  16-instrument 5-year era × {1h,4h} (DE30 has no 5-year file → absent, logged). Domain bars via
  `aggregate_ohlc(min_coverage=0.90)` + analysis-boundary fence (EXP-001 path). Holdout never loaded.
- **Position substrates (per shape, see menu):** blockwise-persistent `_blockwise_state` at the E0
  episode length `L` (`1h:8, 4h:4`) for DENSE/TAIL/STATE; a **sparse** low-activity substrate for
  SPARSE/EVENT (predeclared activity rate, below).
- **Block length** estimated on the train P&L series (frozen rule, `estimate_block_length`).

## Q2 synthetic-positive shape menu (fixed, minimal — extends `plant_positive_edge`, F6)

All shapes inject a **direction-aligned** drift whose **mean net edge over the shape's denominator
equals the grid level `e`** (`EDGE_GRID_BPS`), so the comparison is *same economic magnitude, different
shape* (matched-magnitude, per L-08/L-11). Denominator stated per shape (zero-baseline: `e=0` row is
the no-edge guard).

| Shape | Construction (drift added to returns, aligned to positions) | Denominator | Tests |
|---|---|---|---|
| **DENSE** (anchor) | constant `e` on every active bar = `plant_positive_edge` (E1) | active bars | baseline; gate is built for this |
| **TAIL-ONLY** | on a random fraction `f_tail=0.10` of active bars, drift `e/f_tail`; 0 elsewhere → same mean `e`, mass in the tail | active bars | L-12 §1 / L-11: location-mean leg sees mean; does L4 stability / CI lower collapse under tail concentration? |
| **SPARSE/EVENT** | positions active on only `a_sparse≈0.06` of bars (event substrate); drift `e` on those active bars | **active bars** (sparse) | L-04: per-bar floor vs sparse denominator dilution; finite MDE or UNPOWERED |
| **STATE-DEPENDENT** | latent 2-state (blockwise, `frac_A=0.5`); drift `e` on state-A active bars only, 0 in state-B | **state-A active bars** (per-state magnitude) | L-03 pooling: edge present in a sub-state; does the pooled gate detect it? report pooled-dilution |

Each shape swept over the full `EDGE_GRID_BPS` (0→32 bps; sub→super-MDE). `f_tail`, `a_sparse`,
`frac_A` are **frozen constants** declared here (performance-independent, Q5), never tuned on outcomes.
Menu size = 4 (justified: one anchor + the three L-12-named blind shapes). No further shapes.

## Q3 dogfood-negative (fresh nulls; FPR must stay controlled)

Two families, both **known-null**, run through the gate at the **same alpha** as the positives; FPR =
PASS rate, reported with **`wilson_interval` half-width + explicit draw count** (reuse
`referee_calibration.wilson_interval` / `verdict_rate_rows`; never "≈0"):

1. **Abstract nulls (fresh draws):** (a) **block-permuted returns** + persistent positions (L-07: permute
   returns, never rotate the path); (b) **reblock-random positions** on real returns. No planted edge.
2. **Real dogfood-negative (EXP-019 spirit):** real null **signals** known sub-MDE — `donchian_breakout_positions`
   (the EXP-009 reference R) and `ma_crossover_positions(20,50)` (both exist in the frozen suite) on real
   domain returns, **no planted edge**. Established below every MDE in Chapter 01 → expected standalone
   rejections. (rsi/bollinger/macd/roc generators are not in the post-rollover suite; not resurrected —
   scope discipline. The two retained families + the two abstract nulls are sufficient for an FPR read.)

FPR is **per stratum** (16×2) per null family per convention. Calibrated-FPR for the power/MDE read =
the alpha at which the dogfood FPR Wilson-upper ≤ the frozen suite's earned control (report the realized
FPR; do not retune the gate to hit a target — that would be E3).

## Method (per stratum × shape × convention)

Frozen gate via `gate_stack_core_costfn` / `gate_stack_row` (unchanged legs), at `ALPHA=0.05`:
- **FPR** per stratum per null family (Wilson half-width, draw count). Binds on the dogfood + abstract
  nulls jointly.
- **Power / MDE** per shape: detection rate = fraction of planted draws PASS at each `e`; **MDE =
  smallest `e>0` with detection ≥ `POWER_TARGET=0.5`** (DETECTED_FLOOR). No finite MDE on the grid →
  **UNPOWERED** for that cell (reported, **never** "fail" — L-12 §2 / Mode-2 discipline).
- **Blindness classification** per stratum×shape: **DETECTED** (finite MDE), **UNPOWERED** (no finite
  MDE while FPR is controlled), or **DENSE-ONLY-BLIND** (DENSE detects but shape UNPOWERED in the same
  cell → structural shape-blindness, the L-12 signature).

**Binding endpoints (per stratum — non-pooled, L-03):** the per-(stratum,shape) MDE / UNPOWERED label
and the per-stratum FPR. **Pooled/aggregate** shape-blindness counts are **disclosure-only** until
cross-stratum homogeneity is shown.

## Predeclared interpretation criteria

- **SHAPE-BLIND (per cell):** DENSE has a finite MDE but the non-constant shape is UNPOWERED at the same
  stratum and controlled FPR → the frozen gate is structurally blind to that shape there. A blindness
  map dominated by TAIL/SPARSE/STATE UNPOWERED while DENSE detects **confirms L-12 §1/§2** and scopes
  the E3 composite to those shapes.
- **SHAPE-ROBUST (per cell):** the shape has a finite MDE within ~1 grid step of DENSE → the gate already
  handles it; E3 need not rescue it.
- **MDE-INFLATED (per cell):** finite MDE but ≥2 grid steps above DENSE → partial blindness (degraded,
  not absent); report the inflation factor.
- **Shape-aware read:** report MDE(shape) − MDE(DENSE) per stratum and the UNPOWERED-rate per shape across
  strata; relate to instrument cost and domain `L`. Disagreement between conventions (per-held vs
  amortized) is itself reported (E1 accounting interacts with shape).
- **FPR control (must hold):** dogfood + abstract null FPR Wilson-upper ≤ the frozen suite's control on
  every stratum. A null family that **passes** materially is a calibration break → investigate (not a
  positive result).

## Leak tripwire(s)

- **Future-destroying control (per synthetic-positive):** after planting shape-`e`, **block-permute the
  returns** (destroy the position↔return alignment) and re-run — detection must **collapse to FPR**. A
  shape that still "detects" after future-destruction is an artifact, not power → REJECT-class.
- **Dogfood-negative = the standing FPR null:** must stay controlled (above).
- **No-plant guard (per substrate, EXP-001-corrected):** `e=0` / no drift → PASS rate ≈ FPR on every
  shape and convention (no phantom positive from the shape construction or the cost change).

## Complexity budget

Comparative (across shapes × strata × 2 conventions): **stat work** = FPR (2 null families) + MDE-curve
per (16×2 × 4 shapes × 2 conventions); **visualisations 3** — (1) blindness map (stratum×shape → MDE /
UNPOWERED heatmap, amortized-binding; per-held disclosure panel), (2) MDE-vs-shape curves (pooled
disclosure), (3) FPR-vs-stratum with Wilson bars (dogfood + abstract nulls); **new code modules 1** —
`edge_shapes` (the 3 non-constant planters + sparse/state position substrates) + the E2 harness in
`code/` (reuses the EXP-001 runner scaffolding). No new shared `xen` module beyond the shape helpers
(candidate for `referee_adaptive` only if E3 reuses them).

## Success / failure / inconclusive

- **Success:** a per-stratum × shape blindness map (DETECTED / UNPOWERED / MDE-inflated) with FPR
  controlled and the future-destroying control collapsing every planted detection — answering "which
  shapes is the frozen gate blind to." Either outcome (blind or robust) is informative and scopes E3.
- **Failure:** FPR uncontrolled on a null family (calibration break), or a planted detection survives
  future-destruction (leak) → bug, fix + rerun (Stage-4 material).
- **Inconclusive:** bootstrap/seed noise swamps the DETECTED/UNPOWERED boundary at the chosen
  `N_PLANT`/`N_BOOTSTRAP` for a cell → raise resamples or report the bound (UNPOWERED-with-CI).

## Metric denominators / zero-baseline

MDE in bps on `EDGE_GRID_BPS`; FPR a Wilson-bounded proportion over a stated draw count. Each shape's
mean-edge denominator is fixed in the menu table (active bars; sparse-active; state-A-active). The `e=0`
draw is the null guard. A cell with no finite MDE under a convention is **UNPOWERED** (reported, not
failed). No percentage-of-zero metrics.

## Implementation safety constraints (for the developer)

- Frozen gate via `gate_stack_core_costfn` (E1 seam) — **do not** modify any frozen leg or threshold.
- Open-to-open `≤t-1`; first-70% minute slice + domain fence before any aggregation; never collect the
  final 30%. `CloseTime` ordering; no bar-index alignment.
- All shape/null generators **deterministic** under explicit seeds; same input+seed → identical output.
- Matched-magnitude: every shape's mean drift over its declared denominator equals `e` (assert at
  construction). `f_tail`, `a_sparse`, `frac_A` are module constants, never read from outcomes.
- Reuse `wilson_interval` / `verdict_rate_rows`; do not re-roll a local Wilson.
- `tqdm` on the stratum loop; bounded `N_PLANT`/`N_NULL`/`N_BOOTSTRAP` constants (scale on inconclusive).

This experiment **does not** build or tune the adaptive gate (E3), adjudicate any candidate, change the
frozen gate, or touch the global holdout. It characterizes the frozen gate's shape sensitivity to
scope E3.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + checkpoint §E2 (ladder:133; Q2 118–120;
Q3 121–122; Q5 123–124; hard guards 143–146):
- **Single question** — frozen-gate finite-power-vs-shape. The two cost conventions are one binding
  endpoint (amortized) + one disclosure (per-held), not a second question. ✓
- **Classification** analysis-only — correct (synthetic substrates + frozen primitives; no price→signal). ✓
- **Holdout** sealed; first-70% minute slice + domain fence. ✓ **Reads/slots** 0; referee-renew
  methodological branch (registered Phase-001 G0); no candidate adjudicated → no slot. ✓
- **Per-stratum binding** (MDE/UNPOWERED per stratum×shape; FPR per stratum), pooled disclosure-only
  (L-03). ✓ **Matched-magnitude** shapes (mean drift = `e` over each shape's declared denominator) —
  the L-08/L-11 discipline that makes "same edge, different shape" a fair contrast. ✓
- **UNPOWERED-not-FAIL** classification (L-12 §2 / Mode-2). ✓ **Shape-aware read** is the experiment. ✓
- **Nulls** block-permute returns (L-07), not path rotation; FPR via reused `wilson_interval`/
  `verdict_rate_rows` with draw counts (never "≈0"). ✓
- **Leak tripwires** (3) predeclared: future-destroying control (block-permute post-plant → detection
  collapses to FPR); dogfood-negative as the standing FPR null; no-plant guard (EXP-001-corrected). ✓
- **Cost-convention bind on amortized** — justified: isolates shape-blindness from the E1-quantified
  F3 over-charge; both legs frozen (only signal-leg accounting differs, via the audited bit-identical
  seam); per-held reported in parallel. Approved as predeclared. ✓
- **Budget** — plots 3 / modules 1 (shape helpers + harness) / comparative stat work; within the
  comparative budget. ✓

**Info (non-blocking):**
1. Shape constants `f_tail=0.10`, `a_sparse=0.06` (borrowed from the L-04 ~6% AVWAP activity rate —
   disclosed), `frac_A=0.5` are pre-registered, performance-independent, never tuned on outcomes
   (Q5-compliant). A sensitivity sweep on them is an **E4-robustness** item, not E2.
2. Compute is heavy (16×2×4×2 cells × MDE-curve + future-destroy + FPR). Bound `N_PLANT`/`N_NULL`/
   `N_BOOTSTRAP` as constants; the **future-destroying control may run at the detected-MDE level +
   one super-MDE level per shape** (sufficient to prove collapse) rather than the full grid — a
   permitted efficiency, the predeclared "detection must collapse" requirement is unchanged.

No REVISE issues. Proceed to Stage 2 (implement the `edge_shapes` module + E2 harness; reuse the
EXP-001 runner scaffolding and the `gate_stack_core_costfn` seam).
