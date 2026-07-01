# Family Index — CF-MR-003 (Cross-Domain Mean-Reversion, deviation-from-higher-domain-anchor)

Operator-ratified probe against the terminal-branch prior (Phase 001 §6), admitted only for a
distinguishing information source: **cross-domain deviation + MR-screen-as-selector**, gated
availability-first at zero cost. Registry: `docs/signal-registry/candidate-families/cf-mr-003.md`.
Governing checkpoint: `docs/experiments-docs/checkpoints/2026-07-01-002-cross-domain-mean-reversion/`.

**Status:** REGISTERED — **EXP-008 closed as a METHODOLOGY FINDING (2026-07-01); NOT exonerated / NOT
admitted.** The screen used a vehicle inherited from the price-geometry family (fixed-horizon MFE +
random-timing null), **indicated** non-native to MR: a reactive vehicle diagnostic separates native target
metrics (anchor-hit +2.9 pp, fraction-recovered +2.7 pp) under a dislocation-matched null while MFE is
blind → the EXONERATE is **held, not booked**. Preliminary **positive native evidence**; native re-screen =
**EXP-009** (target-based estimand + dislocation-binned null). L-13. 0 slots / 0 counted TEST reads;
holdout sealed.

## Exploration axes & concretization roadmap

Full family surface registered post-ADMIT (2026-07-01). Authoritative detail + dispositions:
`docs/signal-registry/candidate-families/cf-mr-003.md` (§Exploration axes, §Concretization roadmap).
Origin: operator dumps `.ignore/dumps/0-phase002-thoughts.md`, `0-mean-reversion-screening-framework.md`.

**Axes.** A `MR-screen stack` (VR + half-life in use; Hurst-DFA REFUTED-on-levels A1; ADF/KPSS AVOID
parametric; lag-1 autocorr / LOESS deferred; OU characterisation-only). B `/SERIES` (S5 SPREAD ADMIT-robust,
S3 DETREND ADMIT-moderate, S4 OU weak, S1/S2 positive-hint precision-limited, new constructions OPEN).
C `/EXTREME` (robust-z/z/quantile — sweep deferred). D `/DIRECTION` (extreme-primary used; trend/regime
secondary open). E execution machinery **DEFERRED to price-primary**: live-limit entries, `/REENTRY`
none/allow/extend, `/TARGET` mean(screened)/opposite-extreme(deferred), `/EXIT` form-1/form-2/plane.

**Roadmap.** (1) **CONC-1** (next, price-primary, operator-gated) — form-2 limit-at-anchor, target=mean,
live-limit entries, in-engine on S5_SPREAD→S3_DETREND, binding-leg cost, frozen-referee: first tradability
test; counted read/holdout gated on it. (2) **CONC-2+** — sweep deferred axes on a tradable base (no
dead-entry rescue, P-02). (3) **Robustness debt** — constant-n thirds test; S1/S2 less-trend-contaminated-z.

## Experiments
- [EXP-008 — cross-domain MR availability screen (HYP-001; methodology finding)](#exp-008)
- [EXP-009 — native re-screen: does price return to the anchor? (HYP-001; SCREENED-ADMIT)](#exp-009)

---

## EXP-009 {#exp-009}

**Status**: COMPLETED — SCREENED-ADMIT (per-stratum, native vehicle) · **Date**: 2026-07-01 · audit PASS,
0 Critical · ANALYSIS-ONLY, TRAIN-only, 0 counted reads, holdout sealed.

### Hypothesis Tests
1. **CF-MR-003/HYP-001 (native)** — among `|z|≥2` bars at matched dislocation, does the VR∧HL screen pick
   entries whose price **returns to the higher-domain anchor** more (anchor-hit / fraction-recovered /
   time-to-anchor) than a dislocation+regime-matched **screen-fail** control?

### Scope
- 16 inst × 5 anchor series × 3 domain pairs. Selector = 2-leg VR∧HL (from EXP-008 A1). Event-specific
  horizon `H_i=min(48,3·half-life_i)`, horizon-matched control pairing. Endpoint floors E1 hit 0.03 / E2
  frac 0.05 (Amendment B2). Binding leak = pass/fail label-permutation; time-reversal diagnostic-only (B1).
- Exclusions: no strategy/entry/exit/P&L (availability only); TEST + holdout never loaded.

### Results / Observations
- **36 leak-clean per-stratum passes** (any_pass, label-perm collapses): **S5_SPREAD 20** (EURUSD, USDJPY,
  NZDUSD, USDCHF, GBPUSD across pairs), **S3_DETREND 14**, **S4_OU 2**.
- Positive hit-Δ medians all 5 series: S1 +5.2pp, S2 +8.2pp, S3 +6.2pp, S4 +8.8pp, S5 +2.2pp.
- Dispositions: POWERED_PASS 49, POWERED_FAIL 26, UNPOWERED_HINT 253, UNPOWERED_NULL 104.
- Null contrast (passing cells): screen-fail +5pp / random-extreme +2.5pp / random-timing −29pp.
- Sole binding gate = precision (6-gate cascade: Gates 1–4 ≈0; Gate 5 MDE the bottleneck). Screen-fail
  "starvation" hypothesis empirically refuted (fail pool 2000+, D>0 drop 0%).
- Robustness: S5_SPREAD 18–20 (robust), S3_DETREND 8–16 (moderate) across m/H_CAP/z-edges/horizon-method;
  recent-third → 0 (power).

> No interpretation — see report.md.

### Hypothesis-Specific Conclusion
**SCREENED-ADMIT (per-stratum, native vehicle).** CF-MR-003 not exonerated; a broad leak-clean
reversion-to-anchor availability edge (robust S5_SPREAD, moderate S3_DETREND). Availability, not
tradability. EXP-008's EXONERATE was a vehicle artifact (L-13).

### Hypothesis-Agnostic Observations
- Evaluation-vehicle choice (metric + null) determined the sign: MR-native (target-based, dislocation-
  matched, half-life horizon) surfaced the edge the EXP-008 excursion/random-timing vehicle masked.
- S1/S2 UNPOWERED = binary-hit precision at low extreme counts, not no-signal (positive hints).

---

## EXP-008 {#exp-008}

**Status**: INCONCLUSIVE (underpowered) · **Date**: 2026-07-01 · **Instruments**: 16 (INFR-003 5-year,
VAL-003 minus DE30) · **Data Views**: real time-bar OHLC → domain bars {15m,1h,4h,1D}; analysis-only,
TRAIN-only.

### Hypothesis Tests

1. **CF-MR-003/HYP-001** — Do exec-domain entries conditioned on a cross-domain deviation series
   characterised mean-reverting at `≤ t-1` show a favourable reversion excursion toward the
   higher-domain anchor exceeding a matched-random, matched-count, matched-regime within-instrument
   control — for **any** of 5 anchor constructions × 3 domain pairs, per stratum? Edge = Δ-over-random.

### Scope

- **Instruments**: 16-instrument INFR-003 5-year canonical.
- **Anchor-series axis (5)**: S1 CENTER (rolling median), S2 RANGE (Donchian midline), S3 DETREND
  (rolling-OLS-trendline residual), S4 OU (Ornstein-Uhlenbeck equilibrium on HLC3, `0<φ<1` guard),
  S5 SPREAD (rolling-β asset-class basket, cross-instrument).
- **Domain-pair axis (3)**: 4h/1h, 4h/15m, 1D/1h (anchor:exec 4:1 / 16:1 / 24:1).
- **MR screen (selector, `≤ t-1`)**: `VR(q=4)<0.90 ∧ half-life∈(0,48] ∧ Hurst-DFA<0.45`; extreme probe
  `|robust-z| ≥ 2.0`. ADF/KPSS dropped (parametric).
- **Endpoints (per stratum, L-03)**: (L) median excursion; (S) upper-tailmass `#{θ≥1 ATR}/n`.
- **Control**: within-instrument regime-matched (ATR tercile) random timing, matched count.
- **Multiplicity**: cross-axis Holm max-statistic permuted-axis over 15 series×domain axes
  (`xen.availability_gate`). **Effect floor** Δ*=0.10 ATR; `N_min=100`; axis eligible at ≥4 powered cells.
- **Exclusions**: no strategy machinery / cost / P&L / in-engine run; TEST band + global holdout never
  loaded; final-30% sealed.
- **Leak tripwires**: conditioning-label permutation; forward-excursion time-reversal.

### Results / Observations

- **0 / 15 axes eligible; 0 powered instrument-cells** (both endpoints); per-cell **max 18 events**
  (median 7.5); only 33/240 cells cleared the ≥2-event inclusion floor (S3:1, S4:30, S5:1; S1/S2: 0).
- **Drop-one-leg disclosure** (total events over 240 cells / cells ≥100 events): VR 433,790 / 222; HL
  609,626 / 234; **VR+HL 315,644 / 216**; **Hurst-only 792 / 0**; VR+Hurst 528 / 0; HL+Hurst 339 / 0;
  **ALL3 (design) 280 / 0**. On EURUSD·4h/1h S1 the extreme-bar per-leg passes: VR=446, HL=1202,
  **Hurst=0**.
- DFA validated correct (white noise α≈0.52, random walk α≈1.48).
- Leak tripwires shipped + wired (100% finite); no admitting cell to fire on. Holdout sealed; every
  decision input `≤ t-1` (audit provenance trace PASS). Audit **PASS, 0 Critical**.

> No interpretation in this block — see report.md.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE (underpowered).** Per design §7 (`>½ axes ineligible-UNPOWERED`), the MR-screen selects
too few events to test availability. Not EXONERATE — the axes were never powered. CF-MR-003 is neither
admitted nor exonerated; the terminal-branch prior is untested on this vehicle.

### Hypothesis-Agnostic Observations

- The **Hurst-DFA<0.45 leg** is the sole binding constraint: `Hurst<0.5` (increment anti-persistence)
  is mis-applied to mean-reverting deviation **level** series, which are locally **persistent**
  (Hurst>0.5) — contradicting the VR/half-life legs. This is the **L-12 §3 near-impossible-conjunctive-leg**
  pattern reappearing **inside the screen** (not the referee).
- Dropping Hurst (2-leg VR ∧ half-life) powers **216/240** cells — the availability question is testable
  under a corrected selector (new dated-D0 experiment; §7 forbids a goalpost move here).

**Links**: [design.md](../../../../python/experiments/EXP-008/design.md) ·
[report.md](../../../../python/experiments/EXP-008/report.md) ·
[audit.md](../../../../python/experiments/EXP-008/audit.md)
