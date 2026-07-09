# Amendment-003 — EXP-014b streamlined rerun: S8-only, symmetry availability control, 2 domains, both-leg

**Date:** 2026-07-02 · **Family:** CF-MR-004 · **Hypothesis:** HYP-003 (opened here) · **Operator-directed.**
**Supersedes:** the current EXP-014b results (amendment-002, exit-set-faithfulness redo) — **archive, do not
delete** (retained per programme discipline). EXP-014b **keeps its ID**; results/emissions are replaced.

## Why (what the audit + two independent analyses forced)

1. **The availability control was invalid** (`.ignore/temp/dumps/finding-availability-control-degenerate.md`).
   The dislocation-matched control drew from the **|z|≥2 signal population itself** (`dislocation_bin` returns
   −1 below 2.0, so the pool is only extreme bars) → it compared the signal to itself → "0/38 availability"
   was **vacuous**, not a family reading. And the naive repair (ordinary |z|<2 bars) is also wrong: by the MR
   premise ordinary bars sit near the mean and trivially "revert." We trade **outliers**; the control must hold
   the outlier fixed and ask *does it revert beyond a coin flip*. → **replace with the symmetry two-barrier
   first-passage control** (null = 0.5). This is **fix-and-rerun level**.
2. **Exit axis collapses to the moving-mean.** The faithful fixed entry-referential limit structurally cannot
   capture **peer-side** reversion (audit M1): the spread reverts mainly through the moving anchor, so form-1
   market-exit cannibalizes the fixed form-2 (FX cells fill form-2 **0×**). The moving-anchor form-2 (the
   "artifact" of EXP-014) is the object that actually captures reversion — adopt it as the single exit; drop
   the fix/trail split.
3. **Both-leg architecture** (audit-2): the single traded-instrument limit can't book peer-side reversion;
   entering **both** sides (short A + long the basket) captures the spread reversion regardless of which side
   moves. Operator: **include now** as a variant (accepting ~N× cost).
4. **S8 only** — the least-random series (VR 0.27–0.37 FX, HL ≈ 2–10 bars, mildest form-1 loss). S5/S6/S7
   drop (S6 ≈ random walk, S5/S7 index cells negative-gross).
5. **Domain axis {1h, 4h}** — probe the sparsity effect directly (4h has too few episodes: only 11/38 powered
   last run). 15m excluded (unlikely to clear fees). 1h referee **is frozen** (`DOMAIN_SPECS['1h']`,
   min_state=20; 4h min_state=8) and its cost map exists — tradability binding on both.

## Locked change-set (operator)

| # | Delta | Spec |
|---|---|---|
| A1 | **S8 only** | basket − RollingMedian₉₀, 11 cells (7 FX + 4 IDX). Drop S5/S6/S7. |
| A2 | **Availability control replaced** | symmetry two-barrier first-passage, null=0.5, availability iff `ci_low(p_inward)>0.5`. Spec §Availability in design.md. |
| A3 | **Exit = moving-mean** | single-leg exit = refreshing form-2 at moving anchor mean + form-1 event-reversion. **No fix/trail axis. No horizon.** |
| A4 | **Both-leg variant** | short A + long equal-weight peer basket (N mate legs); joint spread position, dual-side precalc entry, joint form-1 exit at mean; reentry=none; cost over all N+1 legs (binding, L-02). |
| A5 | **Reentry {none,allow,extend}, R only** | single-leg lifecycle arms; drop the S (place-once) recalc axis (014b Q11: inconclusive). |
| A6 | **Conditioners = slices** | trend-strength + vol-regime emitted per bar; Python partitions on **both** availability and tradability. Not gates. |
| A7 | **Domains {1h, 4h}** | two decision domains (m1 fills unchanged). Per-(cell,domain) strata; per-domain frozen power floor. |
| A8 | **Co-primary reads** | availability (A2) AND tradability (frozen referee) both binding. |
| A9 | **Deviation-magnitude axis z\*** | entry band = z\*·σ, z\* ∈ {2.0 faithful default, 1.5 aggressive/less-extreme}; reentry ladder derived {z\*, z\*+0.5, z\*+1.0}. Availability read at |z|≥{2.0,1.5} from one emission (`Z` band-independent, verified). PRIMARY = z\*=2.0. |
| A10 | **Both-leg = 2 entry sub-axes** | `bothleg-limit` (rest limits all N+1 legs, cancel-on-partial — faithful, desync disclosed) + `bothleg-market` (market-fill all legs on the spread trigger — clean group). |

**Matrix:** 2 domains × 11 cells × (3 single-leg + 2 both-leg) × 2 z\* = **220 runs** (was HYP-002 456).
Single-leg z\*-cross = **132 runs runnable now**; both-leg 88 runs land with Increment B.

## Smoke-surfaced fix (S8:US500 4h, 2026-07-02)

- **Trend-strength band miscalibrated** → **per-cell tercile.** The inherited fixed `|trend_z|≥1.0`
  "strong" band never triggers: `trend_z=(EMA20−EMA50)/σ_close(200)` caps at ~0.98 because the 200-bar
  `σ_close` is inflated by the trend it's meant to measure. This structurally emptied the counter/with-
  trend slices — the operator's own fade-counter-trend hypothesis (`newer.md`) was untestable. Fix
  (analysis-only, no re-emission): "strong" = `|trend_z|` top tercile per (cell,domain), matching the
  vol-regime tercile bucketing. Design §6 updated.

## Carried-forward audit fixes (fold into the rerun)

- **F1** — per-stratum UNPOWERED labeling per predeclared criteria (strata = (cell,domain,arm)); no global
  `tot_powered==0` shortcut.
- **F2** — bite-check scoped **per admitting cell** (not a global `all()` over every cell).
- **W3** — correct the stale `Xen.cs` exit comments (no horizon; exit=moving-mean); remove/neutralise the
  dormant planner horizon or clearly mark it unused.

## What stays FROZEN / unchanged (governance)

Frozen referee **untuned** (L-12); holdout final-30% **sealed**, first-49% TRAIN fence (same UTC timestamp
both domains); **0 counted TEST reads, 0 slots**; from-scratch family code (L-13); ≤ t-1, open-to-open,
`CloseTime`/`SourceCloseTime` alignment, engine-realized m1 fills; real-price outcomes; per-stratum binding
(L-03); cost realism binding early (L-02, both-leg sums all legs).

## Detail + interpretation criteria: see `python/experiments/EXP-014b/design.md` (rewritten under this amendment).
</content>
