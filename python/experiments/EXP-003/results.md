# Results: Experiment EXP-003 (Keystone)

## Summary

The Phase 001 keystone measurement is **complete**: both referees have a fully
characterised, usable-precision operating-characteristic map on all three domains.
The headline is the measured **stringency↔sensitivity trade-off**. The minimal
baseline behaves as a calibrated single test — its FPR tracks α (1h: 0.005 /
0.025 / 0.049 at α = 0.01 / 0.05 / 0.10) and its economic MDE is small (0.5–2.0
bps). The 5-check gate stack is the opposite extreme — its FPR is **0.0 at every
domain and every α** (0/4000 nulls passed), bought at a substantially **inflated
MDE** (5m 1.0, 1h 4.0, 4h 12.0 bps at α = 0.05, vs the baseline's 0.5/0.5/2.0).
The per-leg diagnostic localises both effects: the FPR collapse is driven jointly
by L3/L4/L5 (each rejects 100% of nulls), and the MDE inflation is dominated by
**L5 materiality**, the binding leg at every domain's MDE. All 18 (domain,
referee, α) cells meet the precision targets and yield a finite MDE — including
4h. `run_metadata.json` records `overall_status: COMPLETE`, `mde_cells: 18`,
`mde_status_counts: {PASS: 18}`.

## Detailed Findings

### Finding 1 — Minimal baseline: FPR ≈ α, small MDE

- **Observation**: The minimal baseline's FPR sits at (just under) α everywhere.
- **Evidence** (`fpr_summary.csv`): at α = 0.05, FPR = 0.0228 (5m), 0.0248 (1h),
  0.0323 (4h); at α = 0.10, 0.0478 / 0.0493 / 0.060; all ≤ α with Wilson
  half-widths ≤ 0.0074 (n = 4000). MDE (`mde_summary.csv`, α = 0.05): 0.5 (5m),
  0.5 (1h), 2.0 (4h) bps.
- **Interpretation**: A single block-bootstrap CI test is a well-calibrated,
  sensitive referee — it controls false positives at the nominal rate and detects
  small edges, but offers no margin beyond α.

### Finding 2 — Gate stack: FPR = 0, inflated MDE

- **Observation**: The gate stack rejects **every** null at **every** α; its MDE
  is several times the baseline's.
- **Evidence**: gate FPR = 0.0 (0/4000) in all 9 (domain, α) cells
  (`fpr_summary.csv`); gate MDE = 1.0 (5m), 4.0 (1h), 12.0 (4h) bps at α = 0.05,
  identical across the α grid. TPR rises monotonically to 1.0 (`tpr_summary.csv`),
  confirming the stack does pass genuine edges once large enough.
- **Interpretation**: The conjunctive 5-leg stack is extremely conservative. It
  essentially never passes an edge-free candidate, at the cost of being blind to
  small real edges — the measured price of stringency.

### Finding 3 — The trade-off is the deliverable

- **Observation**: Stringency and sensitivity move in opposite directions between
  the two referees, quantified per domain.

  | Domain | Gate FPR | Min FPR (α=0.05) | Gate MDE | Min MDE | MDE inflation |
  |--------|----------|------------------|----------|---------|---------------|
  | 5m | 0.0 | 0.023 | 1.0 | 0.5 | ×2 |
  | 1h | 0.0 | 0.025 | 4.0 | 0.5 | ×8 |
  | 4h | 0.0 | 0.032 | 12.0 | 2.0 | ×6 |

- **Interpretation**: This table is the PS§6 "measured stringency" deliverable.
  The gate stack buys an FPR reduction from ~α to ~0 by accepting an MDE 2–8×
  larger. A "reject" from the gate stack means "no edge, or an edge below
  ~1/4/12 bps net (per domain)" — X is now measured.

### Finding 4 — L5 materiality dominates the gate stack's blind spot

- **Observation**: Among the five legs, materiality (L5) is the binding constraint
  that sets the gate MDE; the FPR collapse is a joint L3+L4+L5 effect.
- **Evidence** (`leg_pass_rates.csv`, α = 0.05): on nulls, L1 = L2 = 1.000 and
  L3 = L4 = L5 = 0.000 at every domain (each outcome leg rejects all 4000 nulls).
  On positives near the MDE, L5 is the lagging leg: 4h m=2 → L5 = 0.006 (vs L3 =
  0.337, L4 = 0.812); 1h m=2 → L5 = 0.371 (vs L3 = 0.924); 4h m=12 → L5 = 0.935;
  1h m=4 → L5 = 0.977.
- **Interpretation**: This directly answers the design's "which leg dominates
  false negatives" (PS-T2/T9): **L5**. Because L5 requires the CI lower bound to
  clear a fixed per-domain materiality threshold, the gate's MDE is set by
  materiality, which is why it is **α-invariant** (Finding 2). The α grid only
  moves the minimal baseline's MDE (4h: 4.0 → 2.0 → 1.0 across α = 0.01/0.05/0.10).

### Finding 5 — 4h is fully measured, not inconclusive

- **Observation**: Every 4h cell met the precision targets and produced a finite
  MDE.
- **Evidence**: 4h FPR Wilson half-widths ≤ 0.0074; TPR half-widths at the MDE
  ≤ 0.014; 6/6 4h MDE cells PASS.
- **Interpretation**: Unlike EXP-001's per-cell 4h under-power (which concerned the
  *per-draw recovery* distribution), EXP-003's rates pool 2000 draws/cell, so the
  *binomial rate* precision is tight even on 4h. The two are different quantities;
  4h is well-resolved at the rate level here.

## Hypothesis Verdict

**SUPPORTED**

The 5-check gate stack has a measurable empirical economic MDE at FPR ≤ α₀ = 0.05
on every domain (5m 1.0, 1h 4.0, 4h 12.0 bps), and its operating characteristics
were compared to the minimal baseline without touching the holdout. Per the
scope's Evidence-FOR criteria — for every reportable cell, FPR Wilson half-width
≤ 0.03, TPR half-width ≤ 0.05, FPR ≤ α, and a finite MDE at TPR ≥ 0.80 — all 18
cells qualify (`mde_status_counts: {PASS: 18}`). The keystone map exists with
usable precision; the design's success condition ("stating the operating
characteristics") is met.

## Limitations

- **Per-domain rates pool four instruments** of different cost (1–10 bps) and
  dispersion, so each MDE is a domain aggregate dragged toward the harder
  instruments (audit Info 1). Per-instrument MDEs could be lower; EXP-004 evaluates
  per-instrument dogfood and must interpret accordingly.
- **Blind/not-blind is not decided here.** EXP-003 reports the MDE map; whether
  a domain MDE sits above where plausibly-real edges live (H-keystone) requires the
  EXP-004 empirical anchor. The 4h gate MDE of 12 bps vs a 4h materiality of 3 bps
  means the gate would reject material 4h edges below ~12 bps — flagged for EXP-004.
- **Stationary fixed-magnitude planted edges only** (design D-edge). Non-stationary
  / drifting edges are deferred; the MDE is for the cleanest edge structure.
- **MDE is grid-resolution limited** (uncertainty reported as a grid half-step in
  `mde_summary.csv`).

## Alternative Explanations

- Is gate FPR = 0 a bug (always-reject)? No — EXP-002's `positive_oracle` fixture
  passes the gate, and here gate TPR rises to 1.0 at large `m`. The gate passes
  genuine edges; it rejects edge-free nulls by conjunctive construction.
- Could the MDE inflation be a different leg? The per-leg pass rates isolate L5 as
  the lagging leg near every MDE, with L3 secondary on 4h; L1/L2 never bind.

## Recommended Next Steps

1. **Proceed to EXP-004** — anchor this MDE map against the measured net effect
   sizes of the real Donchian / MA dogfood strategies (the empirical ceiling), to
   decide blind-vs-not-blind per domain (H-keystone).
2. **Future scope (new EXP)**: a per-instrument operating-characteristic map would
   resolve the pooling caveat (Info 1) — relevant if the dogfood anchor lands near
   the domain MDE for some instruments but not others.
3. **Future scope (new EXP)**: vary the materiality threshold to trace how the
   gate MDE moves with L5 (since L5 is the binding leg) — a direct lever on
   stringency, deferred to the loss-function phase.
