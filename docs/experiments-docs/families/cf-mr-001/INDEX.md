# CF-MR-001 — Mean-Reversion Entry (RSI-2) — Detail Index

**Status:** `ADMITTED (BINDING) — G-020 adjudicated 2026-06-23; first candidate slot consumed` (EXP-089
`SCREEN_DELIVERED`, 2026-06-23, amended `D0-amendment-001`; G-020 ADMITTED). First candidate family opened
after the Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price routing.
The availability screen consumed **0 counted TEST reads, holdout sealed**; **G-020 ADMITTED** (`S_fam=28 > S*=7`,
perm-p≈0.0002, FWER-robust, MC-stable) → **CF-MR-001 has now consumed its first candidate slot**, the
programme's first non-random price entry. The admitted lever is the **bare RSI-2 fade (CORE)** (the vol-regime
partition is inert; variants counter-productive); effect is **intraday (15m/1h)**, ~3-bar horizon.

**Batch 2 — Phase 021 OPEN** (G0 RATIFIED 2026-06-23, D0 FROZEN): the
**availability→tradability** step for the bare fade — exit / capture geometry / cost, intraday-first. See
[`../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md).
Planned EXP-090 (readiness/calibration) → EXP-091 (exit screen) → EXP-092 (cost-bearing sequence) → EXP-093
(one-shot TEST). **Primary exit hypothesis = a native intrabar reversion-target pair** — **EXIT-RCT**
(operator-proposed; closed-form RSI₂→50 reversion-completion price `P*=Close+(AL−AG)`, proactive limit, 1m
intrabar fill) and **EXIT-ERT** (Claude-designed; price-returns-to-equilibrium-mean target) — measured against
conventional reactive contrast arms (RSI-revert-on-close, fixed-bar, ATR-barrier, partial/trail), adverse side
held fixed. The vol-regime / variant / contrarian / 25-75 / tuning / expansion branches remain deferred (each
needs its own dated `D0-amendment-*` + slot decision).

**Family spec:** [`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md)
· **Phase 020 checkpoint:** [`../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md)
(design · D0 · G-020 criteria · bite-check plan).

---

## What this family tests

The programme's first **mean-reversion (fade)** entry — every prior family was continuation/pullback. Plus a
**global, strategy-agnostic volatility-regime partition** treated as part of the signal definition (cell =
`asset+domain+regime`) — the hypothesis that *a filter can become the signal*. Opened over G-019's
price-exhausted verdict by operator override; the honest prior is **availability ≈ random**, so the screen is
a cheap falsification attempt (0 reads / 0 slots) reusing the Phase-019 admission gate.

## Frozen batch-1 surface (Phase 020 D0)

- **Entry:** `RSI(2)` Wilder, long `RSI₂<10` / short `RSI₂>90` (2 / 10 / 90 frozen).
- **Global filter `/VOLREGIME`:** `ATR(14)` causal rolling-50 percentile, 33/66 → Low/Med/High;
  per-(instrument,domain) thresholds; **partition on the bare core only**.
- **Variants (pooled):** TREND `EMA(20)`, RSI-FILTER `RSI(5)≷50`.
- **Six sub-screens → joint-max gate:** `CORE`, `CORE-VOL-LOW/MED/HIGH`, `CORE+TREND`, `CORE+FILTER`.
- **Endpoint (AMENDED `D0-amendment-001`, 2026-06-23):** entry-signed favourable `MFE_med`, ATR-normalised, over
  a **causal MR-tempo cap** (RSI-2 reversion-episode tempo, ~3-bar horizon; replaces the original trend-length
  MA-segment cap). **All 6 sub-screens are single-test leg-1** `Δ̂_rand` vs a matched `SUB-RANDOM` —
  **regime-matched** (same-regime bars) for the three `/VOLREGIME` sub-screens, all-bars for CORE/variants.
  TRAIN-only, 46 EXP-080-READY cells × {15m,1h,4h}.
- **RETIRED by `D0-amendment-001`:** the leg-2 beats-CORE conjunction + regime-membership-shuffle null (audit
  C-1: an ATR-normalization confound the leg-2 gate was blind to) and the trend-length cap (audit C-2). The
  regime-dependence question is now read directly from *which regimes' leg-1 passes* (answer: all three,
  uniformly — the regime adds nothing).
- **Deferred (registered, uncounted):** CONTRARIAN arm, 25/75 scheme, regime×variant cross-cuts, parameter
  tuning, expansion.

## Experiment cards

| EXP | HYP | Title | Status | Key finding |
| --- | --- | --- | --- | --- |
| EXP-089 | `CF-MR-001/HYP-001` | RSI-MR Availability Screen (bare core + vol-regime partition + 2 variants; 6 sub-screens; TRAIN-only; AMENDED) | **SCREEN_DELIVERED → G-020 ADMITTED (BINDING) 2026-06-23** | `S_fam=28 > S*=7`, perm-p≈0.0002, FWER-robust, MC-stable; driver = **CORE** (bare fade, z=17.3); vol-regime **inert** (LOW/MED/HIGH ≈22/25/20, flat Δ̂); variants kill it (0,1); intraday (15m 16/16, 1h 11/16, 4h 1/14); ~3-bar horizon. First run voided (deviation, audit C-1/C-2); amended (`D0-amendment-001`) — confounds confirmed removed. |

### EXP-089 — detailed card (`CF-MR-001/HYP-001`)

- **Hypothesis tests:** does the RSI-2 fade — bare, vol-regime-partitioned, or trend/momentum-filtered — beat
  the multiplicity-adjusted joint-max permuted-axis availability gate (`S_fam > S* ∧ axis perm-p ≤ 0.05`) on any
  of 6 sub-screens? (One binding test: the D2b gate.)
- **Scope:** TRAIN-only, gross, real-OHLC; 46 EXP-080-READY cells × {15m,1h,4h}; entry-signed favourable
  `MFE_med` (ATR units) over a causal MR-tempo cap; leg-1 single-test all 6 sub-screens; regime-matched control
  for `/VOLREGIME`. 0 slots, 0 counted TEST reads, holdout sealed. Amended in place (`D0-amendment-001`).
- **Results / observations:** `SCREEN_DELIVERED`; `S_fam=28`, `S*=7`, axis perm-p≈0.0002, ADMITTED across FWER
  {0.025/0.05/0.10}, MC-stable. Per sub-screen S — CORE **28**, VOL-LOW 22, VOL-MED 25, VOL-HIGH 20, TREND 0,
  FILTER 1. Regime `Δ̂_rand` flat (LOW 0.050 / MED 0.080 / HIGH 0.045 ATR); CORE 0.060. Per-domain CORE passes
  15m 16/16, 1h 11/16, 4h 1/14; all 16 instruments represented; effective ~3-bar horizon (77% caps at FLOOR=3);
  favourable `MFE_med` ≈0.75 ATR. Determinism/recon/holdout-fence clean; bite GREEN `f01a000b…`. Audit PASS
  (0C/0W/3I).
- **Hypothesis-specific conclusion (NON-BINDING — G-020 binding):** provisional **ADMITTED**, driven by the
  **bare RSI-2 fade (leg 1, CORE)** — *not* the vol-regime partition (inert) and *not* a variant
  (counter-productive). On admit, G-020 opens the bare fade, intraday, first. Availability ≠ tradability.
- **Hypothesis-agnostic observations:** (1) imposing trend/momentum agreement on a fade destroys its favourable
  availability (TREND/FILTER → S 0/1) — direct, unambiguous. (2) The short-horizon reversion availability is a
  higher-frequency phenomenon, monotone-decaying 15m→1h→4h and absent by 4h. (3) The result is conservative
  w.r.t. ATR-normalization (extremes carry elevated entry ATR, deflating the signal metric).

## Gate

| Gate | Status | Outcome |
| --- | --- | --- |
| G-020 | **ADMITTED — adjudicated 2026-06-23** ([`G-020-gate-review.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md); criteria [`G-020-gate-criteria.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-criteria.md)) | **ADMITTED** — `S_fam=28 > S*=7`, axis perm-p≈0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm). Lever = **bare RSI-2 fade (CORE)**, intraday; vol-regime inert, variants dead. **CF-MR-001 consumes its first candidate slot.** Next scope (future G0/D0): capture-geometry / exit / cost for the bare fade. 0 counted TEST reads; holdout sealed; ledger unchanged. |
