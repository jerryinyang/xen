# Results: EXP-064 — MA(20,50)-Substrate Favourable-Target Geometry (Dual-Object)

**Experiment:** EXP-064 · Phase 015 Surface S1 · `CF-HA-HARAMI-001/HYP-017`
**Objects:** native (MA-segment `/STRONG-STAT`; 8360-class) and hybrid (ZigZag `/STRONG-STAT` × MA geometry; 3202-class), reported individually, never pooled.
**Binding endpoint:** per-cell median per-event gross ATR-normalised return (P3/P14, P15 fills, real prices).
**Win criterion:** alternative variant is median-viable (CI_low_1s > 0, m ≥ 30) **AND** beats own-object matched-random-on-MA null (variant − RM contrast CI_low_1s > 0) **AND** beats that object's benchmark MA variant (variant − benchmark paired-contrast CI_low_1s > 0), composed by P11 with P6 non-4h rule (≥5 cells / ≥3 instruments / ≥3 non-4h cells).

---

## Summary

Neither the native nor the hybrid conditioning object produced a favourable-target variant that satisfies the full binding conjunction at P11 composition scale. Both objects yield **EVIDENCE_AGAINST**: no alternative favourable target — whether a volume-profile level of the prior completed MA segment (`/VPTARGET`: POC, near-VA, far-VA) or a trailing-MA-segment-magnitude distance (`/MAGTARGET`: frac × {0.5, 1.0} × W × {5, 20}) — simultaneously achieves median viability, signal attribution, and a benchmark improvement across the required breadth of the 99-cell grid.

The native object is the stronger object (consistent with EXP-061's finding that the native MA-segment-conditioned harami is the expressing population). Native shows a geometrically coherent pattern: VP targets beat the benchmark in 10–11/14 viable cells, but those same cells do not beat the matched-random-on-MA null (only 2–4 cells), indicating the VP improvement is substrate-driven rather than signal-specific. MAG variants achieve signal attribution (beats_RM) in 5–8 cells but do not simultaneously beat the benchmark across the grid. No variant clears all three gates at P11 scale.

The result is consistent with EXP-056 (0/8 variants on the ZigZag substrate) and reinforces that the favourable-target geometry is not an active lever for the conditioned HA harami in either the ZigZag or the MA substrate. The Phase 015 S1 characterisation is complete; G-015 will adjudicate the surface slate after EXP-065 and EXP-066.

---

## Detailed Findings

### 1. Phase verdict and object hierarchy

- **Phase verdict: EVIDENCE_AGAINST.** Stronger object: **native** (consistent with EXP-061 M0 being the expressing population).
- **Native verdict: EVIDENCE_AGAINST.** 0/7 alternative variants compose at P11 + P6.
- **Hybrid verdict: EVIDENCE_AGAINST.** 0/7 alternative variants compose at P11 + P6.

The native object has materially higher power across all variants (max viable = 14 cells for VP-POC and VP-FAR vs. max 9 for hybrid VP-FAR). This is consistent with the native being the higher-count population (8360-class vs. 3202-class for hybrid) and the expressing object in EXP-061.

### 2. Benchmark arms reproduce EXP-061 anchors

The `M-BENCH` native arm reproduces EXP-061 `M0` and the `H-BENCH` hybrid arm reproduces EXP-061 `H0`, per-cell median and qualifying count to `RECON_TOL = 1e-9` across all 99 member cells (P12 verified). This confirms the implementation is the same MA-benchmark pipeline and that any difference in the alternative variants is attributable to the favourable-target change alone.

| Object | BENCH viable cells | BENCH beats_RM cells |
|--------|-------------------|---------------------|
| Native | 8 / 99 | 8 / 99 |
| Hybrid | 3 / 99 | 2 / 99 |

The native BENCH (= EXP-061 `M0`) remains the signal-attributable baseline: 8 cells where median CI_low > 0 that also beat RM, spread across 6 instruments (EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m). The hybrid BENCH has fewer cells, consistent with its lower power.

### 3. Native object: VP variants geometrically beat benchmark but fail RM attribution

VP targets (POC, near-VA, far-VA of the prior completed MA segment) are consistently geometrically superior to the 50%-of-`M_sofar` benchmark in many cells, but that superiority is not signal-specific:

| Variant | Viable cells | Beats RM | Beats benchmark | Wins |
|---------|-------------|----------|-----------------|------|
| VP-POC | 14 | **2** | 11 | 0 |
| VP-NEAR | 11 | **6** | 10 | 0 |
| VP-FAR | 14 | **4** | 11 | 0 |

VP targets tend to set the favourable level at a structural price cluster (the POC or value-area edge of the prior MA segment). These levels are further from entry than the 50%-of-`M_sofar` benchmark in cells where the prior segment was large. The MA-substrate momentum naturally tends to reach these levels on random in-regime entries as well — the matched-random-on-MA null benefits from the same geometric improvement. As a result, the variant−RM contrast is negative or insignificant in 10–12/14 viable cells: the VP advantage is a geometric property of the MA substrate, not a harami-signal property.

For VP-FAR in particular: 14 viable cells, 11 beat the benchmark (the paired contrast confirms VP-FAR targets are genuinely further and higher-payoff), but only 4 beat the RM null, and only 1 cell (BTCUSD-5m, native) satisfies viable ∧ beats_RM ∧ beats_bench — far short of the P11 quorum. VP-NEAR's beats_RM count (6 cells, composing as a standalone tally) and beats_bench count (10 cells) never co-occur enough: the intersection that is all three (variant_wins) is 0 cells.

### 4. Native object: MAG variants are signal-attributable in some cells but do not consistently beat the benchmark

MAG targets scale with the MA-segment magnitude history:

| Variant | Viable cells | Beats RM | Beats benchmark | Wins |
|---------|-------------|----------|-----------------|------|
| MAG-0.5×5 | 13 | 5 | 7 | 0 |
| MAG-1.0×5 | 7 | 5 | 5 | 0 |
| MAG-0.5×20 | 9 | **8** | 3 | 0 |
| MAG-1.0×20 | 5 | 6 | 5 | 0 |

MAG-0.5×20 is the only variant for which beats_RM composes at P11 + P6 (8 cells / 7 instruments / 7 non-4h ≥ quorum). This means the 0.5 × median(trailing-20 MA magnitudes) target consistently outperforms the random-in-regime baseline in a majority of powered cells — it is genuinely signal-specific. However, it beats the geometric benchmark in only 3 cells: MAG-0.5×20 typically sets a **shorter** favourable target than 50%-of-`M_sofar` (the 20-segment median magnitude may be smaller than the current in-progress `M_sofar` at the harami bar), and the median expectancy suffers from hitting the 1:1 adverse stop more frequently on these shorter targets.

MAG-1.0×20 also has beats_RM composing (6 cells / 5 instruments / 5 non-4h) but beats benchmark in only 5 cells, none in the conjunction. The 1.0× scaling sets a target equal to the median trailing magnitude, which is closer to the 50%-of-`M_sofar` benchmark but still does not consistently exceed it.

The pattern across MAG variants: shorter/scaled targets improve signal attribution (the harami-to-target fill rate vs. random baseline improves) but reduce the gross expectancy vs. the benchmark. Longer/larger targets beat the benchmark geometrically but are not demonstrably harami-specific.

### 5. Hybrid object: power-limited, consistent direction

Hybrid viable cell counts are lower for all variants (max 9 for VP-FAR), reflecting the smaller 3202-class population. The pattern is directionally consistent with native: VP-FAR (9 viable, 4 beats_RM, 7 beats_bench, 3 wins) has the highest individual-cell win count but still far below the P11 quorum of 5 cells. No hybrid variant composes on any of the three conditions individually at P11 scale. The hybrid object is expected to be more power-limited and cannot meaningfully contribute a positive signal here.

### 6. P4 mean diagnostic (disclosed, not a viability gate)

| Object / Variant | Median of cell-medians | Median of cell-means | Median of cell-trimmed-means |
|------------------|------------------------|---------------------|------------------------------|
| Native BENCH | +0.012 | +0.006 | −0.018 |
| Native VP-FAR | +0.019 | −0.078 | −0.029 |
| Hybrid VP-FAR | −0.009 | −0.094 | −0.060 |

The P4 pattern is consistent across variants: the median is near zero or slightly positive (ATR units), while the raw mean and trimmed mean are negative, especially for VP-FAR. The positive median is driven by occasional large gains in a minority of cells; the broader distribution (captured by the mean and trimmed mean) is negative. This indicates the geometry produces fat-tailed, right-skewed outcomes where the positive median is not backed by structural structural robustness across the cell grid. The trimmed mean being negative for native VP-FAR (−0.029) even after removing extreme tails confirms that the "typical" central outcome is marginally negative — the positive median is a high-water mark from a few outlying cells, not a stable central tendency.

### 7. Consistency with EXP-056 (ZigZag substrate, favourable axis)

EXP-056 found 0/8 variants winning on the ZigZag substrate. EXP-064 finds 0/8 variants winning on the MA substrate for both objects. Two different substrates, two different conditioning populations (ZigZag vs. MA-segment `/STRONG-STAT`), and two conditioning objects within the MA substrate all arrive at the same conclusion: **the favourable-target geometry is not a productive lever for the conditioned HA harami**. The signal's edge (where present, as in EXP-061 M0) operates through the benchmark 50%-of-`M_sofar` target geometry; changing the favourable leg does not improve and often harms signal attribution or geometric expectancy.

---

## Hypothesis Verdict

**REFUTED** (both objects: EVIDENCE_AGAINST)

The hypothesis that at least one alternative favourable-target geometry — `/VPTARGET` (volume-profile levels of the prior completed MA segment) or `/MAGTARGET` (trailing MA-segment-magnitude distances) — produces higher gross per-event median expectancy **and** is signal-attributable vs. the matched-random-on-MA null **and** beats the benchmark MA variant, composed by P11 with the P6 non-4h rule, is refuted for both the native and the hybrid conditioning objects.

The binding obstruction differs by variant class:
- **VP variants**: geometrically beat benchmark in many cells, but the improvement is substrate-driven (RM null also benefits). Signal attribution fails (VP improvement is MA-geometry, not harami-signal, property).
- **MAG variants**: are signal-specific in some cells (MAG-0.5×20 beats_RM at P11 scale), but set shorter targets that underperform the benchmark geometrically. Signal attribution exists but expectancy vs. benchmark is negative.

No variant achieves the conjunction. The result is consistent across the native and hybrid objects and across the MA and ZigZag substrates (EXP-056).

---

## Limitations

1. **TRAIN-only**: all cells operate on the first 49% of the dataset (first 70% of first 70%); the result is pre-TEST/holdout. The EVIDENCE_AGAINST verdict may not hold on the TEST stratum if the favourable-target geometry has a narrower domain of validity.
2. **`TickVolume` proxy**: the `/VPTARGET` volume profile uses broker tick count as a proxy for traded volume. Tick count is a noisy estimator of actual traded volume and may not reliably identify structural price clusters. This disclosed limitation applies to all VP variants and could explain why VP-level targets do not produce signal-specific expectancy improvements.
3. **LOOKBACK=1 (prior completed segment only)**: VP construction uses only the immediately preceding completed MA segment. A multi-segment profile or a longer lookback might produce different results. This is a pre-declared constraint, not a defect.
4. **Adverse held at benchmark 1:1**: the favourable target change is OAT (one-at-a-time); adverse and third barrier are fixed at the MA benchmark. Interaction effects between the favourable target choice and the adverse geometry are deferred to the combined system experiments (EXP-067/068).
5. **Power gap (hybrid)**: the hybrid object is materially power-limited (max 9 viable cells vs. 14 for native), limiting the resolution of the hybrid finding. An EVIDENCE_AGAINST result for hybrid could reflect insufficient power rather than a true null.
6. **No ZigZag-substrate favourable surface computed (deferred)**: the ZigZag-substrate analogue is a disclosed deferred secondary; the comparison between the two substrates' favourable surfaces is bounded to EXP-056's 0/8 result for the ZigZag benchmark geometry, not a matched repeat on the full 8-variant grid.

---

## Alternative Explanations

1. **Benchmark 50%-of-`M_sofar` is already the efficient target**: the MA substrate's in-progress magnitude may be a superior real-time estimate of where the move will complete, making static VP levels or historical MAG estimates less useful. The benchmark target is adaptive (it uses current-bar `M_sofar`), while VP/MAG references are derived from prior segments.
2. **VP cluster failure**: the MA segment's prior completed range may not produce reliable VP clusters because MA segments vary widely in length and the TickVolume proxy is noisy. Cluster-to-price alignment may be weaker for MA segments than for ZigZag segments (which respect structural swing levels).
3. **MAG warmup and validity exclusions deplete counts**: for /MAGTARGET with W = 20, many events are excluded because fewer than 20 prior MA segments are available. This reduces the effective sample for MAG-1.0×20 (viable in only 5 native cells). The result for long-window MAG variants may reflect insufficient power in those cells rather than a true null.

---

## Signal Registry Disposition

This experiment is **registry-relevant** (EVIDENCE_AGAINST on a registered hypothesis):
- `CF-HA-HARAMI-001/HYP-017` (EXP-064): **EVIDENCE_AGAINST** on both objects (native and hybrid). The `/VPTARGET` and `/MAGTARGET` branches on the `MA-SUBSTRATE` do not improve conditioned capture. Family status remains **OPEN** (no closure; P9 — surface runs regardless; G-015 adjudicates after the full slate).
- **Multiplicity registry outcome**: `HYP-017` is recorded as **measured-negative (characterisation)**; remains in the ledger (refuted/inconclusive items are never deleted or renamed).
- **No TEST stratum read; no candidate slot consumed; `test-read-ledger.md` requires no entry.**

---

## Recommended Next Steps

1. **EXP-065 (S2: third-barrier geometry, both objects)** — the next pre-declared surface read in the Phase 015 slate. If the third barrier (MA adaptive cap) can be improved, that is independently testable per P9.
2. **EXP-066 (S3: exit-strategy surface, both objects)** — the trailing/partial-exit variants are the S3 surface and are independent of the favourable-target result.
3. **EXP-067/068 (combined system, if any S1–S4 surface shows EVIDENCE_FOR)** — the combined system experiments are conditional on at least one surface showing a lever; with S1 as EVIDENCE_AGAINST, the combined system benefit from the favourable axis is unlikely, but the G-015 decision will account for all surfaces.
4. **Multi-segment VP / longer lookback (follow-up only if G-015 deems it valuable)** — a VP profile built from multiple prior MA segments (LOOKBACK > 1) or a density-weighted profile might produce more stable cluster estimates; this is a bounded follow-up only if the G-015 slate warrants further investigation of the favourable axis.
