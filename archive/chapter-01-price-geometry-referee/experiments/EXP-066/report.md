# Experiment Report: EXP-066 — MA(20,50)-Substrate Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined; Dual Conditioning Object: Hybrid and Native), Phase 015 Surface S3

## Status: COMPLETED

**Date**: 2026-06-18
**Instruments**: all 17 VAL-003-admitted instruments; 99 member cells (3 COVERAGE_EXCLUDED: US500-4h, JP225-2h/4h)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; MA(20,50) crossover substrate (real close); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20) — computed on MA segments for native object, on ZigZag moves for hybrid object; 12 position-management exit arms: BENCH (50% single-leg / 1:1 stop / adaptive cap), PARTIAL-V1/V2A/V2B/V2C, TRAIL-PURE/TP-INIT/TP-NOINIT, COMBINED-V1/V2A/V2B/V2C; P15 path-ordered intrabar fills; P14 median ATR-normalised position-weighted gross return (binding endpoint)

---

## Question

On the MA(20,50) substrate, for each conditioning object individually (hybrid and native), does replacing the benchmark single fixed exit with scaled favourable take-profits (`/EXIT-PARTIAL`: event-trigger or fraction-of-target legs, with/without reversal-event runner) and/or an adverse-side market-structure trailing stop (`/EXIT-TRAIL-STRUCT`: secondary 0.5×ATR ZigZag monotone ratchet, with/without fixed favourable target and with/without initial 1:1 stop) — or their combination — raise the conditioned HA-harami's gross per-event median expectancy vs that object's MA benchmark, per cell and composed across the grid, beat the same-object matched-random-on-MA null, and which scheme (if any) wins — per object?

## Hypothesis

`HYP-019` (Phase 015 Surface S3): For at least one of the 11 alternative exit scheme arms, the conjunction of (a) median viability (CI_low_1s > 0, m ≥ 30), (b) signal attribution over the same-object matched-random-on-MA null (arm − RM contrast CI_low_1s > 0; P5), and (c) benchmark improvement (arm − benchmark paired-contrast CI_low_1s > 0) composes at P11 (≥5 cells / ≥3 instruments / ≥3 non-4h) for at least one conditioning object (hybrid or native). The two objects are judged individually (P2), never pooled; the phase-level reading is the stronger object's outcome.

## Method Summary

Four statistical methods as predeclared (reuses EXP-064 dual-object pipeline + EXP-059 `xen.position_exits`): (1) moving-block bootstrap median CI per cell per arm per object (b = max(1, round(m^(1/3))), N_BOOT = 10,000, per-cell fixed seed); (2) P4 mean diagnostic (raw mean + 10% trimmed mean + worst-5% tail-share — disclosed non-binding co-primary); (3) arm−RM independent contrast CI (signal attribution, P5); (4) arm−benchmark paired-contrast CI (benchmark improvement). All computed per object, never pooled. P11 composition enforced with the P6 non-4h breadth rule. Reconciliation: native M-BENCH against EXP-061 M0; hybrid H-BENCH against EXP-061 H0 — 99/99 cells to RECON_TOL = 1e-9. See `analysis-plan.md` for full method details.

## Key Findings

### Finding 1: Native PARTIAL-V2A clears the binding conjunction (EVIDENCE_FOR)

**The only winning arm across both 12-arm grids:** Native PARTIAL-V2A scores 21 `arm_wins` cells (median-viable ∧ beats-RM ∧ beats-bench) over 13 instruments, all 21 cells non-4h — well above the P11 quorum (≥5 cells / ≥3 instruments / ≥3 non-4h):

| Metric | Count |
|--------|-------|
| median-viable cells | 45/99 (13 instruments) |
| beats-RM (signal-attributable) | 41/99 (13 instruments) |
| beats-bench (lever) | 56/99 (17 instruments) |
| **arm_wins (conjunction)** | **21/99 (13 instruments, 21 non-4h)** |

Winning cells span 13 instruments across all domains: BTCUSD (5m/30m/1h), EURUSD (5m/15m), XAUUSD (5m/15m), GBPUSD (5m/15m), USDJPY (5m/30m), USDCHF (5m), USDCAD (5m/15m), AUDUSD (5m), NZDUSD (5m), EURJPY (5m), GBPJPY (5m), AUDJPY (5m/15m), US2000 (5m). The effect is broad-based and not 4h-carried (0 of 21 winning cells are 4h).

Other native EXIT-PARTIAL variants (V1, V2B, V2C) are median-viable and beat both RM and benchmark individually at P11, but **none composes the three-way conjunction** — each fails on at least one leg at the cell level.

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

TRAIL-PURE has 0 powered cells across both objects — the secondary-ZigZag trailing structure (atr_mult=0.5), even with an initial 1:1 stop, never delivers median-positive returns on the MA substrate. The pattern replicates EXP-059's ZigZag-substrate finding and extends it to the MA substrate.

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

## Conclusion

**Hypothesis SUPPORTED (native) / REFUTED (hybrid) → Phase verdict: EVIDENCE_FOR (native).**

On the MA(20,50) substrate, **for the native conditioning object** (MA-segment `/STRONG-STAT` p75, 8360-class), at least one position-management exit scheme — PARTIAL-V2A (even-thirds favourable scaling) — produces higher gross per-event median expectancy than the MA benchmark single fixed exit, beats its own matched-random-on-MA null, and composes at P11+P6 (21 cells/13 instruments/21 non-4h). For the hybrid object (ZigZag `/STRONG-STAT`, 3202-class), the lever is EVIDENCE_AGAINST — no scheme clears the binding conjunction. The divergence is the deliverable: the exit-machinery benefit is a matched-substrate conditioning property.

The divergence replicates EXP-061's native-vs-hybrid conditioning property: favourable-side scaling benefits the MA-native object (the edge bearer) but TRAIL-PURE and all COMBINED arms fail across both objects. The EXP-060B champion favourable side (V2A) is the single winning scheme, and it is also raw-mean-positive on 11 native cells (7 non-4h, P11-composes for mean diagnostic) — the strongest possible surface input to G-015.

Family stays OPEN (P9 no-early-closure); the surface runs regardless. EXP-066 feeds the terminal G-015 after EXP-067 (native combined-champion) and EXP-068 (hybrid combined-champion).

## Registry Disposition

Registry-relevant result (`CF-HA-HARAMI-001/HYP-019`, EXP-066):

- **`docs/signal-registry/multiplicity-registry.md`**: HYP-019 updated to **CHARACTERISED** — native EVIDENCE_FOR (PARTIAL-V2A, 21 cells/13 instruments/21 non-4h), hybrid EVIDENCE_AGAINST (0 arms compose conjunction). Retained in the ledger (never deleted or renamed).
- **`docs/signal-registry/candidate-families/harami.md`**: EXP-066 result noted under the `/MA-SUBSTRATE` branch — position-management exit lever on MA characterised for both objects; no signal-registry registration or change needed (0 TEST reads, no countable-item promotion).
- **Candidate-family status**: `CF-HA-HARAMI-001` remains `REGISTERED / OPEN` — no closure here; P9 applies; G-015 adjudicates after the full slate.
- **TEST reads / candidate slots**: 0 TEST reads; 0 candidate slots consumed. No `test-read-ledger.md` entry required.

## Limitations

1. **Gross only** — costs not deducted. The median effect of PARTIAL-V2A expressed in ATR units; conversion to bps and net-of-cost tradability is a future step (EXP-067 native combined-champion).
2. **TRAIN-only** — this is a diagnostic surface read. No TEST/holdout confirmation. All forward windows clipped to TRAIN edge with DATA_CENSORED tagging.
3. **Single trailing structure** — the secondary ZigZag atr_mult=0.5 was the sole trailing mechanism. A secondary-MA trailing structure is out of scope (disclosed).
4. **Single MA benchmark cap** — the MA adaptive cap (k=1.5, window=20, floor=6) may bound or truncate longer-horizon exit mechanisms. Reversal-event legs and runner targets are bounded by the same cap for clean OAT.
5. **Secondary-warmup gate never exercised** — audit Info: the atr_mult=0.5 ZigZag confirms its first pivot before essentially all entries, so the secondary-history warmup exclusion is 0 everywhere in this run.

## Implications for Future Research

- **Divergence is the deliverable**: native EXIT-PARTIAL is EVIDENCE_FOR; hybrid is EVIDENCE_AGAINST. The exit-machinery benefit is a matched-substrate conditioning property — the edge bearer (MA-native) responds to favourable-side scaling; the hybrid (ZigZag-conditioned) object does not.
- **PARTIAL-V2A is also mean-positive on MA**: unlike EXP-060B's V2A×ADV-NONE champion (median-positive, mean≈0), the V2A even-thirds scaling on the MA substrate with the 1:1 benchmark stop produces both a winning median and a positive raw mean in 11 cells — the strongest possible P4 diagnostic. The mean gap (EXP-060B) does not reproduce here.
- **Trailing is uniformly detrimental on MA**: TRAIL-*/COMBINED arms replicate EXP-059's ZigZag finding on the MA substrate — the secondary ZigZag (atr_mult=0.5) trailing mechanism tightens on favourable movement and destroys the edge.

## Recommended Next Experiments

1. **EXP-067 (native combined-champion)** — combine PARTIAL-V2A with ADV-NONE (EXP-063's winning adverse geometry) on the native object, per Phase 015 slate S4/G-015.
2. **EXP-068 (hybrid combined-champion)** — run PARTIAL-V2A × ADV-NONE on the hybrid object; expected negative given hybrid EVIDENCE_AGAINST here.
3. **G-015 terminal adjudication** — after S4 completes, the single Phase 015 gate: PROCEED to candidate registration or CLOSE.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/run_experiment.py](code/run_experiment.py) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Pre-Execution Governance | [governance/pre-execution-review.md](governance/pre-execution-review.md) |
| Post-Experiment Governance | [governance/post-experiment-review.md](governance/post-experiment-review.md) |
| Plots | [plots/](plots/) |
| Per-Cell Results | [results/per_cell_expectancy.parquet](results/per_cell_expectancy.parquet) |
| Composition Readout | [results/composition_readout.json](results/composition_readout.json) |
| Reconciliation | [results/reconciliation.csv](results/reconciliation.csv) |
| Run Metadata | [results/run_metadata.json](results/run_metadata.json) |
