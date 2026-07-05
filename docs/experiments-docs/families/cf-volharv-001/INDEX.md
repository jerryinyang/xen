# CF-VOLHARV-001 — Two-Sided Oscillation/Volatility Harvest (Family Detail Index)

**Status:** RETIRED 2026-07-05 (checkpoint-008 retrospective, operator-signed) — HYP-001
ARTIFACT_CONFIRMED + HYP-002 NOT SUPPORTED; 0 slots / 0 counted reads lifetime.
**Registered:** 2026-07-04 (operator-directed; falsification-first — HYP-001 is a kill test of
the founding anomaly, not a screen of a believed edge). **Chapter:** 02.
**Family card:** `docs/signal-registry/candidate-families/cf-volharv-001.md`.
**Checkpoints:** `checkpoints/2026-07-04-007-cf-volharv-001-falsification-first-screen/`,
`checkpoints/2026-07-05-008-cf-volharv-001-structure-harvest/`.

Origin: convergence of the EXP-018 random-timing destroy-arm residue (NZDUSD rt +31.5 bps/leg
with no signal) and CF-VOLEXP-001's Chapter-01 long-vol hint. Stage 1 (HYP-001) kills or
escalates the anomaly; Stage 2 (HYP-002, gated) tests structure-borne harvest
(rebalance/grid) against measured cost floors and the VR substrate.

## Experiments

- [EXP-019 — HYP-001 seed/fill falsification](#exp-019)
- [EXP-020 — HYP-002 structure-harvest screen (rebalance + grid)](#exp-020)

---

## EXP-019 — CF-VOLHARV-001/HYP-001: seed/fill falsification of the random-timing harvest anomaly {#exp-019}

**Status:** COMPLETED 2026-07-05 — **SUPPORTED / ARTIFACT_CONFIRMED (operator verdict)**.
Artifacts: `python/experiments/EXP-019/{design,qa-review,analysis,report}.md`.

**Hypothesis Tests**
- H_artifact (predeclared prior): the EXP-018 rt per-leg positive (NZDUSD +31.5 bps/leg,
  CI_low +13.7) is a sampling draw — a fixed-unit random-direction random-timing fixed-hold
  leg has E[gross]=0 by construction (analytic null; empirically exercised by 25 disjoint
  ex-ante seeds/instrument).
- Bands: ARTIFACT_CONFIRMED / PROCESS_ASYMMETRY (≥MDE ∧ ≥20/25 seed-sign ∧ coherent
  same-direction split → fill forensics, never an edge) / WASH / UNPOWERED; COST_FLOOR and
  VR substrate booked regardless.

**Scope**
- 16 instruments (VAL-003 universe minus DE30), 4h, TRAIN only (EXP-013/018 49% fences —
  band identity with the anomaly; amendment A1). 25 seeds × 16 = 400 live runs +
  16 calendar pre-runs + 25 NZDUSD +1-bar delay twins (441 total), Mode=NativeOrders, m1.
- New lean `RandomHold` C# model: unconditional market entries at pre-scheduled bar opens
  (schedules from (seed, engine bar calendar) ONLY — never prices), exits = matched-hold
  market close at entry+H, H round-robin {6,12,24,48}; no TP/SL/refresh; cap 6 (cap_skip).
- Estimand: per-leg gross bps (`xen.adjudication.per_leg_net`); seed-level battery inference
  per (instrument × hold) stratum. 0 slots, 0 counted reads, holdout sealed.

**Results / Observations**
- 286,476 live legs + 17,839 twin legs, **0 censored** (drop-can't-complete tail rule A2);
  estimand gates blocking_pass on all 425 cells (~1e-12 reconciliation).
- NZDUSD battery (gross bps/leg): H6 −0.73 (MDE 1.44) / H12 +1.04 (2.85) / H24 −2.85 (3.94)
  / H48 +2.20 (5.31); pooled per-seed means span [−11.5, +8.6] → **EXP-018's +31.5 above the
  entire 25-seed distribution**.
- Global: 1,600 seed-stratum means average −0.017 bps; median |mean|/MDE 0.31; 2/64 strata
  beyond MDE (BTCUSD-48 +36.6, 13/25 seed signs, 2021-concentrated, UNPOWERED; EURUSD-12
  +2.18 vs MDE 2.00, 15/25) — ≈3 chance exceedances expected.
- Direction splits track ±μ̂·H with opposite signs (drift shape) in 63/64 strata.
- Tripwires: schedule regeneration byte-identical (50/50 CSVs); fills never early (~2%
  first-tick-of-session lags, direction-symmetric); delay twin indistinguishable (max
  pair-diff +0.74 bps ≤1.6×SE). Bootstrap calibration 2.6% vs 2.5% nominal; planted +15 bps
  battery-detectable in 61/64 strata.
- COST_FLOOR: FTMO commission RT — FX 0.47–1.04 bps, XAUUSD 0.28, BTCUSD 13.0, indices 0;
  **spread unpinned** (live-only; `xen.evaluation.round_trip_cost_bps` raises until pinned).
- VR substrate: FX block genuinely mean-reverting (NZDUSD 0.92/0.88/0.80/0.80 at
  H=6/12/24/48; AUDUSD →0.76; GBPUSD/USDCAD/US500/USTEC similar); BTCUSD/USDJPY/XAUUSD/USDCHF
  ≈ random walk.

**Hypothesis-Specific Conclusion**
- ARTIFACT_CONFIRMED in all powered strata: the anomaly is a draw of a zero-mean
  construction; the MR arc's last positive residue carries no evidential weight. No stratum
  meets the PROCESS_ASYMMETRY triple. Family disposition (retire vs HYP-002/EXP-020 design on
  the booked cost floor + VR profile) belongs to the checkpoint-007 retrospective.

**Hypothesis-Agnostic Observations**
- Seed batteries share one price window per instrument: across-seed dispersion understates
  window-level uncertainty for common-path shocks — window-level bootstrap needed before
  reading any cross-seed "coherent" positive (drove the BTCUSD-48 WASH).
- Per-seed CI plant criteria are power-infeasible in high-σ strata; specify bite checks at
  the aggregation level actually read (battery), not per draw.
- Engine 4h grid is broker-server-aligned (UTC+2/+3, DST-switching): schedule timestamps must
  come from the engine's own calendar (calendar-emission pre-runs), not a UTC clock grid.

---

## EXP-020 — CF-VOLHARV-001/HYP-002: structure-borne oscillation harvest (rebalance + grid) {#exp-020}

**Status:** COMPLETED 2026-07-05 — **NOT SUPPORTED (operator verdict), USDCAD flagged exception.**
Artifacts: `python/experiments/EXP-020/{design,qa-review,analysis,report}.md`.
Checkpoint: `docs/experiments-docs/checkpoints/2026-07-05-008-cf-volharv-001-structure-harvest/`.

**Hypothesis Tests**
- HYP-002: do rebalanced-exposure (ARM R) / symmetric grid (ARM G) structures convert the
  EXP-019 FX-block oscillation (VR 0.76–0.92) into net-positive harvest at capped inventory,
  vs their own unconditioned/inverted twin, where the unconditioned fixed-hold object cannot?
- Discriminating prediction: net > costs only on the MR block (NZDUSD/AUDUSD/GBPUSD/USDCAD);
  RW block (BTCUSD/JPY crosses/gold/CHF) ≈ −costs; any RW-block CI-positive = artifact alarm.
- Bands (§9): SUPPORTED / WASH / CONTRADICTED / ARTIFACT_ALARM / UNPOWERED, per instrument
  per arm; inverted-twin sign-flip required for ARM G SUPPORTED; ≤60% single-year/top-5-episode.

**Scope**
- 16 instruments (universe minus DE30), 4h decisions (ARM G m1 fills, native pending orders,
  Mode=3); TRAIN only, EXP-019 per-instrument fences (band identity). 68 cells: R/R-twin/G/
  G-invert × 16 + 4 delay twins (NZDUSD/USDCAD × both arms = tripwire 1).
- Params candidate-blind from EXP-019 (`code/derive_exp020_params.py`, amendment A1;
  byte-reproducible = tripwire 2): b_w = 0.25·σ12, g = σ12; monthly anchor = prior-month close;
  cap 8 legs. New C# `RebalanceHarvestModel` + `GridHarvestModel` (`Xen.StructureHarvest.cs`).
- Cost framing: engine gross; reads at gross / gross-minus-commission (FTMO) / weekend-ceiling
  stress. **Net-at-live-spread BLOCKED** (spread pin outstanding; EURJPY unpinned even at ceiling).
- 0 slots, 0 counted reads, holdout sealed.

**Results / Observations**
- Integrity gate OPEN: 68/68 estimand blocking_pass; ARM R provenance clean (0 trigger
  violations / 2,119 trade-bars, fill=next open 99.95%, weight restored 100%); ARM G m1
  fill-causality clean (2 benign USDCAD anomalies ≤3.8 bps); **+2 bps/rebalance plant detected
  before the real read**; tripwire 1 graceful everywhere (object ratios 1.01–1.06 — no
  fill-seam edge, no seam inflation).
- ARM R premium (bps/bar, block bootstrap): NZDUSD +0.0048 [−0.019,+0.029] MDE 0.024; AUDUSD
  +0.0055 MDE 0.019; GBPUSD +0.0064 MDE 0.016; USDCAD +0.0029 MDE 0.0045 — **all 4 MR cells
  MDE > effect ⇒ UNPOWERED**, right sign, ~40% of theory. Only US2000 (mid) CI-positive
  (+0.0455 [+0.012,+0.077]). Design §8 over-stated the classical `w(1−w)σ²` premium ~100×
  (true ~0.04–0.07%/yr — negligible). ARM R cost drag ≤4e-4 bps/bar (never binding).
- ARM G twin spread /mo (drift-robust, gross incl. censored MTM): **MR-block 1/4 positive** —
  USDCAD +132 [+43,+257] survives commission/weekend-×4/top-3/both-halves; NZDUSD −56;
  GBPUSD wash (sign-flips on top-3 removal); AUDUSD −104 with the **momentum twin beating the
  MR grid**. Realized RT mean = +g in every cell (mechanism real, artifact check PASS) but rare.
- Artifact alarms: (1) **cadence collapse** — fills at 5–28% of A1-implied crossings; 3/4 MR
  cells cap-locked; NZDUSD traded nothing after 2022-04 (cap-lock + stale monthly anchor);
  occupancy ~98–100% in-market (a mostly-frozen levered inventory carrier, not an oscillation
  harvester). (2) **Censored-inventory dominance** — the ≤8 fence-open legs erase 100–155% of
  realized harvest on NZDUSD/AUDUSD (VAL-006 survivorship); the month-net object is mostly an
  inventory-MTM object. (3) RW alarm scan clean: USDCHF twin spread CI-negative; BTCUSD level
  reads drift-contaminated (+78k MR/+69k momentum) — only the twin spread is drift-robust.
- USDCAD's +132/mo fails two SUPPORTED requirements: inverted-twin sign-flip (momentum twin
  +3,491 — same sign, not flipped) and the 60% cleanliness bar (2022 = 67% of funding).
- Re-run under hardened `block_bootstrap_ci` (INFR-004/L-20 seed battery + F1 sparse-block fix):
  verdict unchanged; 2 borderline temporal-half flips, both verdict-immaterial (USDCAD half-1 →
  CI-positive; US2000 half-2 → straddles 0). Load-bearing cells stable.

**Hypothesis-Specific Conclusion**
- NOT SUPPORTED: the MR block does not act as a block, the inverted-twin sign-flip prediction
  fails everywhere (incl. USDCAD), MR-vs-RW does not separate, ARM R is structurally UNPOWERED.
  Read as **structure failure (cap-lock / cadence collapse), not clean substrate absence** —
  under UNPOWERED discipline this does NOT license "no oscillation harvest exists." Survivors
  (USDCAD, US2000-disclosure) are single-stratum, attribution-flagged, cost-unpinned. Family
  disposition (retire / iterate structure to fix cadence+cap-lock / next-hypothesis) is reserved
  for the checkpoint-008 retrospective, operator-signed.

**Hypothesis-Agnostic Observations**
- A fixed monthly anchor + hard inventory cap can silently convert an "always-on harvester" into
  a mostly-frozen inventory carrier: measure realized fill cadence against the design's implied
  crossing rate before reading any grid harvest (here 5–28% of implied; NZDUSD went inert).
- Grid month-net is dominated by censored end-inventory MTM unless the cap and horizon are set
  so inventory clears within the episode — report realized-vs-censored decomposition (VAL-006),
  never the month total alone.
- Level-based grid P&L is a drift carrier on trending (VR≈1) instruments; only the direction-
  inverted twin spread is drift-robust and admissible as the harvest read.
- Infra: unbounded per-symbol container parallelism (16-way) crashes the cTrader console at
  startup ("Message expected"); `run-experiment.sh parallel` now bounded to 4 + 10s stagger
  (`CTRADER_MAX_PARALLEL`). Killed containers can leave truncated parquets — full-file integrity
  scan (not just gate-required files) before gating.
