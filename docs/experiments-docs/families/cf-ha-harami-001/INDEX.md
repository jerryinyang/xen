# CF-HA-HARAMI-001 — Family Index

> Detailed per-experiment cards for the Heiken-Ashi harami candidate family (Phase 014).
> Live programme status and phase retrospectives: [master index](../../INDEX.md).
> Phase design/retrospective narratives: [`../../checkpoints/`](../../checkpoints/).
> Family spec: [`../../../signal-registry/candidate-families/harami.md`](../../../signal-registry/candidate-families/harami.md).
> Compact one-row registry of all experiments: [`python/experiments/INDEX.md`](../../../../python/experiments/INDEX.md).

**Status:** ACTIVE. Heiken Ashi harami at trend exhaustion, via the Phase 013 pre-committed routing on ANCHOR_MOVE_FLAT. Design brief (binding): the unsolved problem is **capture geometry, not move availability** — the mechanism is a structurally bounded favourable target, measured early. Detection on HA candles; every outcome metric on real prices. 102-cell grid; all work gross, 0 candidate slots, 0 TEST reads, holdouts sealed. 014-A primitives validated separately before any 014-B combined work.

## Experiments

- **EXP-048** — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)
- **EXP-049** — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 99 Cells)
- **EXP-050** — Phase 014-A Harami-in-Context Characterisation
- **EXP-051** — Phase 014-A Strong-Move Filter Characterisation

---

## EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)

**Status**: READINESS_DELIVERED
**Date**: 2026-06-14
**Instruments**: all 17 (BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225)
**Data Views / Feature Categories**: 1-minute time bars aggregated to 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`) OHLC domains; Heiken Ashi candles from domain bars via `xen.heiken_ashi_generator`; ATR-ZigZag sequential streaming substrate on real bars (Wilder ATR-14, `ATR_MULT=1.0`); HA harami shift-1 vectorized detector on HA candles; no chart-type views

### Hypothesis Tests

1. **Hypothesis** (exploratory readiness, no market-edge claim): For every one of the 102 cells (17 instruments × {5m, 15m, 30m, 1h, 2h, 4h}), the ATR-ZigZag trend substrate (real bars) **and** the HA harami detector (HA candles) can each be computed deterministically, look-ahead-safe, and invariant-clean on the TRAIN analysis stratum; and their measured per-cell move/event rates and `/BARCFG` coverage quantify per-cell context for the downstream capture read (EXP-049).

### Scope

- **Instruments**: all 17 VAL-003/VAL-004-admitted instruments (4 core + 13 new-universe). DE30 with truncated history disclosure.
- **Data Views / Feature Categories**: 6 OHLC domains (5m strict; 15m/30m/1h/2h/4h at 0.90 coverage). HA candles per cell.
- **Primitives** (two independent, frozen defaults): ATR-ZigZag (Wilder ATR-14, `ATR_MULT=1.0`, real bars, sequential streaming) — proof that the substrate is causal and deterministic; HA harami detector (body-inside-prior-body, reduced-form `HAClose₀ ∈ (PrevBodyMin, PrevBodyMax)`, shift-1 vectorized) — proof the detector is invariant-clean.
- **Per-cell checks**: construction integrity (OHLC consistency, monotonic `CloseTime`, dropped-fraction gate); ZigZag invariant battery (alternation, causality, timestamps, threshold breach, monotonic confirmation, no NaN); HA harami invariant battery (reduced-form agreement, adjacency, monotonicity, no NaN); determinism replay (full second pass, frame-identical comparison).
- **Parameters**: `ATR_MULT=1.0`, `atr_period=14`. No sweep, no tuning, no combined event.
- **Time range**: TRAIN only (first 49% via F01 prefix; nested analysis-set TEST + final-30% holdout sealed).
- **Exclusions**: no combined harami-at-trend-exhaustion event (014-B / EXP-050+); no 3-barrier capture, returns, MFE/MAE, expectancy, or edge of any kind; no strong-move filters; no sweep or selection; no TEST/holdout contact; no outcome metrics.

### Results / Observations

- **Status distribution**: 86 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED (US500-4h, JP225-2h, JP225-4h), 0 CONSTRUCTED_EMPTY, 0 NOT_READY (any type).
- **COVERAGE_EXCLUDED**: US500-4h (dropped 0.286), JP225-2h (0.257), JP225-4h (0.297) — market-hour gap × longest aggregation windows.
- **READY_FLAGGED**: 13 cells across US500, US2000, DE30, JP225, XAUUSD, USTEC — dropped ∈ [0.10, 0.25], all well below the 0.25 exclusion gate.
- **All invariant violations**: 0 on every cell (12 invariant keys, both primitives).
- **All determinism failures**: 0 (102/102 cells PASS frame-identical replay).
- **Move rates** (ATR-ZigZag confirmed moves per 1k domain bars): range [170.2, 207.0] across all non-excluded cells. All 99 cells ≥30 moves (minimum 336).
- **Harami event rates** (per 1k HA candles): range [229.6, 261.4]. All 99 cells ≥30 events (minimum 401).
- **`/BARCFG` coverage** (pooled fractions across domains): UP_UP ~33–35%, DN_DN ~31–34%, UP_DN ~16–18%, DN_UP ~15–17%. Near-symmetric same-direction dominance, consistent with the family's construction-derived reduction.
- **DE30 disclosure**: truncated history (broker ends 2026-01-16); all counts/rates from its own timeline. Rates per 1k comparable; absolute counts systematically lower.
- **SUBSTRATE_REFUTED criteria**: unmet (no non-determinism, no systematic invariant failure on ≥3 instruments).
- **Audit PASS**: 0 Critical, 1 Warning (latent `/BARCFG` null bug — zero-harami guard not exercised in this run), 2 Info.

### Hypothesis-Specific Conclusion

**READINESS_DELIVERED**

Both primitives are mechanically valid across all 99 non-excluded cells: zero invariant violations (both batteries), zero determinism failures (102/102), and the per-cell readiness map, move/event-rate table, and `/BARCFG` coverage table are produced as scoped. The 13 READY_FLAGGED and 3 COVERAGE_EXCLUDED cells are coverage outcomes (dropped-fraction disclosures), not primitive defects. The 99 non-excluded cells clear the substrate/detector gate for EXP-049 capture read. No market-edge claim is tested or implied.

### Hypothesis-Agnostic Observations

- **COVERAGE_EXCLUDED follow EXP-043 pattern**: US500-4h, JP225-2h/4h — market-hour gap × longest aggregation windows. Consistent with the EXP-043 convention; these are permanent cell-level exclusions under the frozen coverage gate.
- **Move rates are instrument-stable**: ATR-ZigZag at `ATR_MULT=1.0` on Wilder ATR-14 produces a narrow 170–207/1k range across 17 instruments × 6 domains — a fixed-parameter pivot-threshold property, not market-structure variation.
- **Harami incidence is near-constant**: ~230–261/1k across all cells — a construction-derived consequence of the reduced-form constraint on `HAClose₀`, not a market signal. Incidence is independent of instrument, domain, or volatility regime.
- **`/BARCFG` near-symmetric**: UP_UP ~33–35% vs DN_DN ~31–34% dominance, expected from the family's reduced-form proof. UP_UP > DN_DN asymmetry consistent with mild bullish TRAIN-period drift.
- **DE30 short history**: Truncated broker history means DE30 bar counts are ~20–30% lower than full-history instruments, though rates per 1k remain comparable. All DE30 cells are READY or READY_FLAGGED (no exclusions from span alone); DE30 pass-through to EXP-049 with disclosure.

---

## EXP-049 — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 99 Cells)

**Status**: CAPTURE_READINESS_DELIVERED
**Date**: 2026-06-15
**Instruments**: all 17; 99 member cells = EXP-048 READY ∪ READY_FLAGGED (3 COVERAGE_EXCLUDED cells excluded per scope)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; ATR-ZigZag trend-change confirmation anchor (Wilder ATR-14, `ATR_MULT=1.0`); P1–P5 Phase 014 benchmark 3-barrier system on real bars; no HA candles, no harami detector

### Hypothesis Tests

1. **Hypothesis (HYP-002)**: For every EXP-048-READY cell, the 3-barrier capture system (P2 favourable, P3 1:1 adverse, P4 adaptive time cap, P5 LOOKBACK=1) can be constructed deterministically and causally on real prices; and the per-cell gross favourable-before-adverse capture rate `r = P(fav before adv | resolved)` is measured under the predeclared default barriers (two geometries: G1 distance-based primary, G2 retracement-level secondary), with P12 viability (`r ≥ 0.55`, `CI_low > 0.50`, `resolved ≥ 30`) and P11 composition (≥5 cells over ≥3 instruments) applied as a mechanical readout.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views (5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`); ZigZag trend-change substrate (frozen `xen.zigzag`, unchanged); barrier module `xen.capture_barriers` (new).
- **Features**: per-event favourable/adverse/time-cap/data-censored outcome on real High/Low; per-cell capture rate `r` with regime-clustered moving-block bootstrap CI (MBB, `b=round(m^(1/3))`, `N_BOOT=10_000`); invariant battery (causality, fence, determinism, NaN, G1 well-formedness).
- **Parameter ranges**: P1 ATR-14/1.0; P2 X=50%; P3 1:1; P4 `N=max(6,round(1.5·median(trailing-20 durations)))`; P5 LOOKBACK=1; G1 (distance-based, primary), G2 (retracement-level, secondary).
- **Exclusions**: no HA harami detector or combined harami entry (014-B); no `/CONFIRM` model; no alternative barrier variants (`/VPTARGET`, `/MAGTARGET`, etc.); no strong-move filters; no costs; no TEST/holdout contact; no candidate slot consumption; no returns or edge claims.

### Results / Observations

- **CAPTURE_READINESS_DELIVERED**: 99/99 member cells pass all invariant batteries (0 causality, 0 fence, 0 NaN, 0 G1 fav_dist violations); 0 non-deterministic cells (frame-identical second-pass replay); 0 systematic invariant failures.
- **G1 capture rate (primary/distance-based)**: `r` ranges [0.4545, 0.5343] across all 99 cells, tightly clustered around the 0.50 symmetric-barrier null. **0/99 cells VIABLE** — all `BELOW_R` (r < 0.55). `composition_met = false` (0 cells, 0 instruments). Sensitivity at relaxed bars also `false`.
- **G2 capture rate (secondary/retracement-level)**: `r` ranges [0.3257, 0.4389]. **0/99 VIABLE**. 52–60% of events degenerate (entry at/through midpoint), correctly excluded and disclosed.
- **Power**: all member cells `resolved ≥ 30` (min 128). **0 NOT_VIABLE_BY_POWER** cells.
- **Time-cap censoring (unresolved fraction)**: 22–33% across cells. Data-truncation < 0.5%. Adaptive P4 cap binds at 6-bar floor in 96/99 cells.
- **Determinism**: PASS (full-frame replay, identical CI bounds, 0 degenerate bootstrap resamples in any cell).
- **Audit PASS**: 0 Critical, 0 Warning, 4 Info notes.
- **Verdict stage**: the experiment does not self-adjudicate G1; `composition_met = false` is consistent with design §10 CHARACTERISED_NOT_VIABLE on the capture leg. Desk adjudication combining EXP-048 (leg a), EXP-049 (leg b), and future 014-B (leg c) is pending.

### Hypothesis-Specific Conclusion

**CAPTURE_READINESS_DELIVERED**

Barrier construction is valid on 99/99 cells. The G1 capture-rate readout is uniform negative: 0 VIABLE cells under P12. The capture geometry under benchmark defaults (50% favourable fraction, 1:1 R:R, adaptive time-cap) does not produce a favourable-before-adverse bias above the 0.55 viability bar in any cell of the 17×6 grid. The G2 secondary geometry is systematically weaker due to ~52–60% degeneracy and also 0/99 VIABLE.

### Hypothesis-Agnostic Observations

- **r ≈ 0.50 is a genuine null, not a power failure**: with symmetric equidistant barriers on either side of a ZigZag-confirmation entry, price has approximately equal probability of hitting either target first on this substrate. The null is consistent with a near-random-walk path.
- **G2 degeneracy is structural**: the entry-mostly-inside-midpoint pattern means ZigZag confirmations occur after ~50% giveback of the prior move, so the midpoint is often inside the entry-exit range. This is not a model defect but a property of the `ATR_MULT=1.0` pivot threshold.
- **Adaptive cap binds at floor**: median N_event = 6.0 (floor) in 96/99 cells. The P4 adaptive mechanism delivers no per-cell variation beyond the floor for this substrate — the `/THIRD-TIME` sensitivity branch would be informative only at barrier ratios or k-values above the floor.
- **Barrier system is reusable**: `xen.capture_barriers` passed construction validation and determinism on 99 cells × 2 geometries. Any 014-B variant can reuse it without re-validation.

---

## EXP-050 — Phase 014-A Harami-in-Context Characterisation

**Status**: CONTEXT_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for harami detection; real domain prices for all metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, where in a ZigZag move do raw HA harami signals occur, and does the per-cell final-third rate FT exceed the direction-matched random-timing baseline FT_rand by ≥ 10pp (P9 materiality)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: HA candles (via `xen.ha_candles`); real-domain OHLC for positioning; ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged).
- **Features**: harami detection (`xen.ha_harami`); pivot-tiling interval join for move-assignment; price-excursion position `pos = (P − S_i) / (E_i − S_i)`; FT = P(pos ≥ 0.67); direction-stratified random baseline FT_rand; regime-clustered MBB CI on Δ = FT − FT_rand; P9/P11 mechanical readout; MA(20,50) alternative-segmentation secondary.
- **Parameter ranges**: P3 position-in-move with D0-ratified 0.67 threshold; P4 ZigZag ATR 14/1.0; P5 direction-matched random baseline (in-move cardinality, 2,000 bootstrap draws); P6 OFF (no /BARCFG filter); P7 `cluster_by_move` bootstrap; P8 two-pass deterministic replay; P9 materiality 10pp; P11 composition ≥5 cells ≥3 instruments FT ≥ 0.50; P13.2 MA(20,50) secondary segmentation.
- **Exclusions**: no ZigZag confirmation filter; no /BARCFG or strong-move filter; no combined harami+barrier event (014-B); no costs; no TEST/holdout contact; no candidate consumption; no returns or edge claims; no direction differentiation in FT (pooled across up/down).

### Results / Observations

- **Verdict**: CONTEXT_CHARACTERISATION_DELIVERED. **0/99 cells CLUSTERED** (all NOT_CLUSTERED). Composition readout: 0 cells, 0 instruments, `composition_met = false` at every support tier and every sensitivity threshold.
- **FT**: range [0.210, 0.312] across 99 cells. FT_rand: range [0.334, 0.432]. Δ = FT − FT_rand: every cell negative; median approximately −0.12 to −0.18 across domains.
- **MA(20,50) secondary (P13.2)**: Δ_ma_vs_rand ≈ 0 (range [−0.041, +0.010]). Front-loading attenuates under MA regime segmentation — it is a ZigZag-specific phenomenon.
- **All invariants pass**: 0 detector self-check, 0 assignment well-formedness, 0 TRAIN fence violations; all 99 cells deterministic; all reportable (min n_assigned = 393).
- **P11 composition**: not met at any sensitivity threshold (strawman 0.50 fails on both FT and FT_rand for every cell).
- **Secondary disclosure**: FT, FT_rand, Δ, FT_ma, FT_rand_ma, Δ_ma recorded per cell in `secondary_disclosure.csv`.

### Hypothesis-Specific Conclusion

**CONTEXT_CHARACTERISATION_DELIVERED.** The raw unfiltered HA harami signal does not cluster near exhaustion on the ATR-ZigZag substrate. Harami timing is systematically front-loaded relative to random in-move timing. This is a clean baseline measurement: the null landscape any filter or confirmation rule must beat is known (Δ ≈ −0.12 to −0.18).

### Hypothesis-Agnostic Observations

- **Front-loading is ZigZag-specific**: under MA(20,50) segmentation, delta clusters near zero. ZigZag defines move starts at pivot extremes; haramis (small consolidations) appear soon after. MA regimes define moves by crossover timing — haramis have no systematic position bias there.
- **Selection force requirement**: a filter must shift the position distribution rightward by ~12–18pp just to reach Δ = 0, and ~22–28pp to meet the P9 materiality threshold.
- **FT never reaches 0.50**: even the unconditioned raw-timing baseline FT_rand is typically 0.33–0.43 (direction-matched uniform draw is the third of the move ≈ 1 − 0.67). The deterministic position-in-move metric therefore cannot resolve a cell in the upper half of the unit interval for this ZigZag geometry.
- **Implication for 014-B**: any combined harami+barrier event definition cannot rely on harami position-in-move as a timing filter — capture barriers (EXP-049/014-B) must manage outcome structurally. EXP-051 (strong-move filters) and EXP-052 (confirmation) should test whether selection can shift the distribution rightward.

---

## EXP-051 — Phase 014-A Strong-Move Filter Characterisation

**Status**: STRONG_FILTER_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for /STRONG-HA impulse-run detection; real domain prices for all magnitude metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, do /STRONG-STAT (p75) and /STRONG-HA (primary same-direction) each carve a materially different move sub-population by P10 (ρ ≥ 1.5 and f ∈ [0.10, 0.50]), and does each meet P11 (≥5 cells over ≥3 instruments)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged); new `xen.strong_move` module for both filter forms.
- **Features**: /STRONG-STAT trailing-window p75 filter (window ≤20, warmup 5; binding form) + median+1×MAD alternative (disclosed); /STRONG-HA qualifying 3-bar impulse-run detection + run→move mapping (primary same-direction binding; any-direction sensitivity disclosed); per-cell ρ/f/P10 point criterion; P11 composition readout; moving-block bootstrap CI on ρ (disclosed); harami-overlap secondary (disclosed); two-pass determinism replay.
- **Parameter ranges**: P7 trailing window 20, warmup floor 5, p75 (binding) + median+1×MAD (disclosed); P8 run length X=3, HA trailing body-median window 20, warmup floor 5 HA bars; P10 ρ ≥ 1.5 ∧ f ∈ [0.10, 0.50]; P11 composition ≥5 cells ≥3 instruments; P6 OFF (no /BARCFG filter).
- **Exclusions**: no 3-barrier capture geometry (EXP-049), no position-in-move (EXP-050), no /CONFIRM entry model (EXP-052), no combined harami+barrier event, no /BARCFG isolation, no costs, no returns/P&L, no TEST/holdout contact, no candidate consumption.

### Results / Observations

- **Verdict**: STRONG_FILTER_CHARACTERISATION_DELIVERED. **Both binding forms clear P11** with 99/99 MATERIAL cells across all 17 instruments.
- **/STRONG-STAT (p75)**: ρ range [1.72, 2.19], median 1.92, IQR [1.86, 1.97]; f range [0.25, 0.32], median 0.27. 99/99 MATERIAL, 17/17 instruments.
- **/STRONG-HA (primary)**: ρ range [1.62, 2.08], median 1.80, IQR [1.76, 1.86]; f range [0.15, 0.24], median 0.20. 99/99 MATERIAL, 17/17 instruments.
- **Alternative-form agreement**: 0 flips between p75↔MAD; 0 flips between primary↔sensitivity. Disclosed forms agree exactly on materiality status.
- **All invariants pass**: 0 filter well-formedness, 0 magnitude validity, 0 HA self-consistency, 0 causality/TRAIN fence violations; determinism PASS; all 99 cells reportable (n_defined 331–31,431).
- **Harami overlap (disclosed)**: overlap_A 65–87% (/STRONG-STAT) and 74–91% (/STRONG-HA); overlap_B 24–46% across both filters.
- **P11 composition**: material_per_domain = 17/17/17/17/16/15 (5m/15m/30m/1h/2h/4h); 3 COVERAGE_EXCLUDED cells (US500-4h, JP225-2h/4h) not in member-cell set.

### Hypothesis-Specific Conclusion

**STRONG_FILTER_CHARACTERISATION_DELIVERED.** Both /STRONG-STAT (p75) and /STRONG-HA (primary) filters identify materially different move populations from the ATR-ZigZag confirmed-move substrate, meeting the P10 bar in every cell and clearing P11 with 99 material cells across all 17 instruments. The disclosed alternative forms agree (0 flips). The experiment verdict is delivery; G1 adjudication is checkpoint desk work.

### Hypothesis-Agnostic Observations

- **p75 mechanical selectivity**: The trailing-window p75 retains ~25% (modulo ties), mechanically inside [0.10, 0.50]. ρ ≥ 1.5 reflects the heavy right tail of move magnitudes — the median of the top quartile is ~1.9× the full median. Uniform 99/99 materiality may partly be a property of the substrate's magnitude distribution, not a special filter property.
- **HA impulse runs as large-move proxy**: The /STRONG-HA detector selects moves containing 3 consecutive strong HA impulse bars. Lower ρ (~1.80 vs ~1.92) suggests HA impulse bars can occur mid-move without the move being in the top magnitude quartile.
- **Both filters viable for 014-B**: The narrow cross-cell IQR (ρ ~0.06–0.10, f ~0.01–0.02 within each form) suggests uniform behaviour across instruments/domains, allowing simpler global parameterisation in 014-B.
- **Overlap_B baseline**: Most haramis (54–76%) occur outside strong moves. A combined-event definition must handle this asymmetry — either by filtering harami detection to strong-move windows or using the strong-move condition as a post-hoc selector on captured haramis.

---

