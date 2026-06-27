# Results: Experiment EXP-066

**MA(20,50)-Substrate Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined; Dual Conditioning Object: Hybrid and Native)**
Phase 015 surface S3 · CF-HA-HARAMI-001/HYP-019 · dual-object re-run under D0-amendment-001

## Summary

Position-management exits on the MA(20,50) substrate produce **EVIDENCE_FOR on the native conditioning object (MA-segment `/STRONG-STAT`, 8360-class)** via PARTIAL-V2A (even-thirds favourable scaling: 21 cells/13 instruments/21 non-4h at the P11+P6 conjunction) and **EVIDENCE_AGAINST on the hybrid object (ZigZag `/STRONG-STAT`, 3202-class)** — no alternative arm clears the combined (median-viable ∧ beats-RM ∧ beats-benchmark) quorum. The divergence reproduces the EXP-061 native-vs-hybrid conditioning property: favourable-side scaling benefits the MA-native object (the edge bearer) but TRAIL-PURE and all COMBINED arms fail across both objects. The EXP-060B champion favourable side (V2A) is the single winning scheme, and it is also raw-mean-positive on 11 native cells (7 non-4h, P11-composes for mean diagnostic) — the strongest possible surface input to G-015.

## Detailed Findings

### Finding 1: Native PARTIAL-V2A clears the binding conjunction (EVIDENCE_FOR)

**The only winning arm across both 12-arm grids:** Native PARTIAL-V2A scores 21 `arm_wins` cells (median-viable ∧ beats-RM ∧ beats-bench) over 13 instruments, all 21 cells non-4h — well above the P11 quorum (≥5 cells/≥3 instruments/≥3 non-4h):

| Metric | Count |
|--------|-------|
| median-viable cells | 45/99 (13 instruments) |
| beats-RM (signal-attributable) | 41/99 (13 instruments) |
| beats-bench (lever) | 56/99 (17 instruments) |
| **arm_wins (conjunction)** | **21/99 (13 instruments, 21 non-4h)** |

Winning cells span 13 instruments across all domains: BTCUSD (5m/30m/1h), EURUSD (5m/15m), XAUUSD (5m/15m), GBPUSD (5m/15m), USDJPY (5m/30m), USDCHF (5m), USDCAD (5m/15m), AUDUSD (5m), NZDUSD (5m), EURJPY (5m), GBPJPY (5m), AUDJPY (5m/15m), US2000 (5m). The effect is broad-based and not 4h-carried (0 of 21 winning cells are 4h).

Other native `EXIT-PARTIAL` variants (V1, V2B, V2C) are median-viable and beat both RM and benchmark individually at P11, but **none composes the three-way conjunction** — each fails on at least one leg at the cell level (e.g., V2B median-viable in 23 cells and beats-bench in 26, but arm_wins in 0 because no cell simultaneously clears all three).

### Finding 2: All TRAIL-STRUCT and COMBINED arms fail on native

| Arm type | median-viable cells | beats-RM cells | beats-bench cells | arm_wins cells |
|----------|---------------------|----------------|-------------------|----------------|
| TRAIL-PURE | 0/99 | 0/99 | 2/99 | 0/99 |
| TRAIL-TP-INIT | 0/99 | 0/99 | 2/99 | 0/99 |
| TRAIL-TP-NOINIT | 0/99 | 0/99 | 2/99 | 0/99 |
| COMBINED-V1 | 0/99 | 0/99 | 3/99 | 0/99 |
| COMBINED-V2A | 0/99 | 0/99 | 2/99 | 0/99 |
| COMBINED-V2B | 0/99 | 0/99 | 2/99 | 0/99 |
| COMBINED-V2C | 0/99 | 0/99 | 2/99 | 0/99 |

TRAIL-PURE has 0 powered cells across both objects — the secondary-ZigZag trailing structure (atr_mult=0.5), even with an initial 1:1 stop, never delivers median-positive returns on the MA substrate. The pattern replicates EXP-059's ZigZag-substrate finding (trailing detrimental) and extends it to the MA substrate.

### Finding 3: Hybrid object EVIDENCE_AGAINST — no arm composes the conjunction

Hybrid PARTIAL-V2A is median-viable in 28 cells (14 instruments) and beats-bench in 30 cells, but beats-RM in only 4 cells — the signal is not attributable to the harami conditioning on the ZigZag substrate when evaluated against the MA-geometry matched-random null. This reproduces the central EXP-061 finding (native expresses the edge, hybrid does not) now on the position-management exit axis.

Hybrid TRAIL-TP-NOINIT is median-viable in 15 cells (11 instruments) and beats-bench in 7 cells, but beats-RM in only 1 cell. No hybrid arm clears the three-way conjunction.

### Finding 4: P4 mean diagnostic — native V2A also mean-positive (diagnostic co-primary)

Native PARTIAL-V2A is raw-mean-positive (CI_low>0) in 11 cells over 6 instruments (7 non-4h), P11-composing for the disclosed mean diagnostic. This is the strongest possible P4 reading: the median-viable winning arm is also raw-mean-positive, so the mean gap (EXP-060B's central concern: median-positive/mean≈0) is partially closed by even-thirds scaling on the MA substrate. The trimmed mean (10%) widens the positive mean set slightly; the worst-5% tail-share is 0.16–0.50 across cells — finite, not catastrophic.

### Finding 5: Exit-reason composition confirms mechanism

Native PARTIAL-V2A's weight exits predominantly via the even-thirds favourable targets (leg-1 ~1/3-dist, leg-2 ~2/3-dist, leg-3 ~fav target), with the shared 1:1 stop binding only ~0.8% of weight and the time cap under 5%. BENCH arm shows the expected balanced first-hit pattern (FAV ~36%, ADV ~36%, TIMECAP ~27%), replicating EXP-061's r≈0.5. COMBINED arms show ~0% adverse-stop weight (structure trail correctly replaces the fixed stop), but their median expectancies are negative — the trailing stop tightens on favourable-side movement and kills the edge.

### Finding 6: P12 reconciliation — binding gate passes (0 mismatches)

| Check | Result |
|-------|--------|
| Native M-BENCH vs EXP-061 M0 | 99/99 cells match (count + median at 1e-9) |
| Hybrid H-BENCH vs EXP-061 H0 | 99/99 cells match (count + median at 1e-9) |
| Populations genuinely distinct | Confirmed (e.g., BTCUSD-5m: native m=10667, hybrid m=3044) |
| Invariants (exit-reason weights, matched-count, fav_dist>0) | 0/2376 violations |

## Hypothesis Verdict

**EVIDENCE_FOR (Phase 015 S3 lever) — via native object.**

On the MA(20,50) substrate, **for the native conditioning object** (MA-segment `/STRONG-STAT` p75, 8360-class), at least one position-management exit scheme — PARTIAL-V2A (even-thirds favourable scaling) — produces higher gross per-event median expectancy than the MA benchmark single fixed exit, beats its own matched-random-on-MA null, and composes at P11+P6 (21 cells/13 instruments/21 non-4h). For the hybrid object (ZigZag `/STRONG-STAT`, 3202-class), the lever is **EVIDENCE_AGAINST** — no scheme clears the binding conjunction. The divergence is the deliverable: the exit-machinery benefit is a matched-substrate conditioning property.

## Limitations

1. **Gross only** — costs not deducted. The median effect of PARTIAL-V2A expressed in ATR units; conversion to bps and net-of-cost tradability is a future step (EXP-068 native combined-champion).
2. **TRAIN-only** — this is a diagnostic surface read. No TEST/holdout confirmation. All forward windows clipped to TRAIN edge with DATA_CENSORED tagging.
3. **Single trailing structure** — the secondary ZigZag atr_mult=0.5 was the sole trailing mechanism. A secondary-MA trailing structure is out of scope (disclosed).
4. **Single MA benchmark cap** — the MA adaptive cap (k=1.5, window=20, floor=6) may bound or truncate longer-horizon exit mechanisms. Reversal-event legs and runner targets are bounded by the same cap for clean OAT.
5. **Secondary-warmup gate never exercised** — audit Info: the atr_mult=0.5 ZigZag confirms its first pivot before essentially all entries, so the secondary-history warmup exclusion is 0 everywhere in this run.

## Alternative Explanations

- **MA-interval drift, not harami signal** — survived: PARTIAL-V2A beats its own matched-random-on-MA null (RM) in 41/99 native cells. The edge is attributable to the conditioned harami, not MA substrate drift.
- **Benchmark cap truncation** — BENCH and all alt arms share the same MA adaptive cap, so the comparison is fair. Favourable scaling could act primarily by exiting before the cap rather than capturing more move — the exit-reason composition shows leg triggers absorb ~95% of weight.

## Recommended Next Steps

1. **EXP-068 (native combined-champion system)** — combine PARTIAL-V2A with ADV-NONE (EXP-063's winning adverse geometry) on the native object, per Phase 015 slate G-015.
2. **EXP-067 (hybrid combined-champion)** — run PARTIAL-V2A × ADV-NONE on the hybrid object; expected negative given hybrid EVIDENCE_AGAINST here.
3. **G-015 terminal adjudication** — after both combined champions complete, the single Phase 015 gate: PROCEED to candidate registration or CLOSE.
