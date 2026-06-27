# Experiment Report: EXP-061 — MA(20,50)-Substrate Benchmark-Geometry Conditioned Efficacy (Dual Conditioning Object: Hybrid + Native, Phase 015 L1)

## Status: COMPLETED (dual-object re-run)

**Date**: 2026-06-17
**Instruments**: all 17; 99 EXP-060B member cells (3 COVERAGE_EXCLUDED: US500-4h, JP225-2h/4h)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; MA(20,50) crossover substrate (real close); `/STRONG-STAT` strong-move filter (computed on ZigZag move for hybrid, on MA segment for native); benchmark 3-barrier geometry (favourable 50%, adverse 1:1, adaptive time-cap); P15 path-ordered intrabar fills; P14 median ATR-normalised gross-return endpoint

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md`** — supersedes the prior EXP-061 in place.
> The prior result measured a single MA arm labelled "hybrid" that actually conditioned on the **MA
> segment** (the *native* object, 8360-class). This re-run emits **both** conditioning objects
> individually — genuine **hybrid** (ZigZag-`/STRONG-STAT` × MA geometry, 3202-class) and **native**
> (MA-segment-`/STRONG-STAT` × MA geometry) — each with its own matched-random null, never pooled.

---

## Question

For **each** conditioning object individually, does the benchmark-geometry conditioned HA harami express
a signal-attributable median edge on the MA(20,50) substrate (`H0 ≻ RH0`? `M0 ≻ RM0`?) the way the
EXP-060B 85/99 edge appeared at the V2A × `/ADV-NONE` champion — i.e. does that edge generalise beyond
the champion to the simplest stop-bearing geometry, and does it depend on **where** the strong-move
filter is computed (ZigZag move vs MA segment)?

## Method Summary

Forked the EXP-060/060B per-cell pipeline. Six arms over the 99-cell member grid, TRAIN only (first 49%,
F01 prefix): **hybrid** `H0` (ZigZag `/STRONG-STAT` conditioning mask applied to the MA-segment benchmark
geometry) + its matched-random null `RH0`; **native** `M0` (MA-segment `/STRONG-STAT` × same MA geometry)
+ `RM0`; and disclosed `Z0`/`RZ0` (ZigZag substrate). Entry = harami confirmation-bar real close in both
objects; outcome geometry is the MA segment (`rd`/`M_sofar`/fav=0.50·M_sofar/adverse 1:1/adaptive cap).
Binding endpoint = per-cell **median** position-weighted gross ATR return (regime-clustered moving-block
bootstrap, fixed per-cell seed, 10,000 draws); mean + 10% trimmed mean + worst-5% tail-share are the P4
disclosed diagnostic. Per object: median-viable (CI_low>0, ≥30 events) AND beats own null (independent
contrast CI_low>0) AND P11 (≥5 cells/≥3 instruments/≥3 non-4h). Objects judged **individually, never
pooled**; the phase verdict is the stronger object's. Corrected P12 reconciliation: native `M0` ↔
EXP-060B BENCH-MA and `Z0` ↔ EXP-053/060B BENCH-ZZ to 1e-9; the anchorless hybrid `H0` conditioning mask
verified transitively via `Z0`. Second full pass for determinism.

## Key Findings

### Finding 1: The native object generalises (EVIDENCE_FOR); the hybrid object does not (EVIDENCE_AGAINST)

The two objects diverge cleanly at the benchmark geometry:

| Object | generalises (cells/instr/non-4h) | P11 | Verdict |
|--------|----------------------------------|-----|---------|
| **Native `M0`** (MA-segment `/STRONG-STAT`) | 8 / 6 / 8 | composes | **EVIDENCE_FOR** |
| **Hybrid `H0`** (ZigZag `/STRONG-STAT` × MA geom) | 1 / 1 / 1 | fails | **EVIDENCE_AGAINST** |

Native generalises on EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m — 6
liquid FX instruments, all outside 4h, not fragile. The hybrid object's only generalising cell is
NZDUSD-5m, and it clears both legs marginally (contrast CI_low = 0.0035). The hybrid powered grid composes
(99 cells), so its failure is a genuine negative, not power-limited.

![Per-object signal-vs-null forest](plots/signal_null_forest.png)

### Finding 2: Where the strong-move filter is computed matters

The hybrid arm conditions on the **ZigZag** move but is scored on **MA** geometry; the native arm
conditions on the **MA** segment that defines the geometry. Only the native (matched-substrate) object
generalises. The disclosed `Z0` ZigZag contrast beats `RZ0` in 7 cells on a different set (indices/higher
TFs). The benchmark geometry distinguishes the conditioning substrate — the EXP-060B edge is an
MA-segment-conditioning property, not a generic "strong-move-conditioned harami" property.

![Hybrid-vs-native viability map](plots/hybrid_native_viability_map.png)

### Finding 3: Native P4 mean diagnostic is favourable; integrity clean

Native `M0` is mean-viable in 10 cells; the 10% trimmed mean is positive in all 8 native binding cells,
tail-share a modest 0.23–0.28 — the benchmark 1:1 stop bounds the downside, a favourable preview for the
L3 mean-recovery investigation (EXP-063). All defect gates pass: native `M0`↔EXP-060B and `Z0`↔EXP-053
reconcile 99/99 at 1e-9; the hybrid conditioning mask verifies via `Z0` 99/99; determinism 17/17
byte-identical; 0 causality / 0 invariant violations; `is_defect: false`.

![Median vs mean by object](plots/median_vs_mean_by_object.png)

## Conclusion

**Phase verdict: EVIDENCE_FOR (stronger object = native).** The MA-segment-conditioned (native) harami's
edge generalises from the EXP-060B champion to the benchmark 3-barrier geometry — confirming the prior
EXP-061 result, now correctly attributed to the native object. The genuinely-new hybrid (ZigZag-conditioned)
object, computed here for the first time, does **not** generalise: the edge depends on conditioning the
strong-move filter on the same substrate (MA) whose geometry defines the outcome. The two objects are
reported individually; the family stays OPEN and the surface runs regardless (P9, no early closure). This
is a per-object characterisation readout feeding the single terminal G-015 after the full Phase 015 slate
— no closure or candidate registration here.

## Registry Disposition

Registry-relevant for **supersession bookkeeping** (the re-run resolves the SUPERSEDED status), not for
closure. 0 candidate slots consumed, 0 TEST reads, holdouts sealed.
- `multiplicity-registry.md` — `CF-HA-HARAMI-001/HYP-014 (EXP-061)`: SUPERSEDED → **CHARACTERISED
  (dual-object): native EVIDENCE_FOR, hybrid EVIDENCE_AGAINST**; item retained, feeds G-015.
- `candidate-families/harami.md` — HYP-014 card updated to the dual-object outcome; family stays
  **REGISTERED, OPEN**.
- `test-read-ledger.md` — unchanged; no HA-harami TEST stratum exists or was touched (verified).

## Limitations

1. **TRAIN-only** (first 49%); TEST and final-30% holdout sealed for G-015.
2. **Gross only**; P15 intrabar fills approximate, not replay, 1-minute sequences (EXP-054 bounds it).
3. **Native edge concentrated on FX majors** (EURUSD/GBPUSD/USDCHF/AUDUSD/NZDUSD/GBPJPY); indices show none.
4. **MODERATE native breadth** (8/99); composes P11+P6 without fragility but modest in absolute count.
5. **Hybrid lone cell (NZDUSD-5m) is marginal** — does not alter the EVIDENCE_AGAINST reading.

## Implications for Future Research

The native/hybrid divergence is the central new fact for Phase 015: the MA-substrate edge is a
matched-substrate conditioning property. Every remaining surface read (L2/L3/S1–S4) must carry both
objects so G-015 can adjudicate on the object that actually expresses the edge (native), while documenting
that the hybrid object — the one the family literature originally claimed — does not generalise.

## Recommended Next Experiments

1. **EXP-062 (L2)** — champion-geometry MA-substrate comparison, per object (benchmark→champion uplift).
2. **EXP-063 (L3)** — mean-recovery decomposition on the native object.
3. **EXP-064–068 (S1–S4 + combined champions)** — full surface on both objects, per the Phase 015 D0 slate.

## Artifacts

- `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
- `results/`: `object_efficacy_map.csv`, `per_cell_expectancy.parquet`, `substrate_contrast.csv`,
  `reconciliation.csv`, `readiness.csv`, `generalisation_readout.json`, `run_metadata.json`
- `plots/`: `signal_null_forest.png`, `hybrid_native_viability_map.png`, `substrate_contrast_by_domain.png`,
  `median_vs_mean_by_object.png`, `p11_composition_by_object.png`
- `audit.md`, `results.md`, `governance/pre-execution-review.md`, `governance/post-experiment-review.md`
