# Results: Experiment EXP-001

## Summary

The Phase 001 synthetic calibration substrate is **valid**. Across all four
instruments and all three domains (5m/1h/4h), both known-null generators produce
no oracle-recoverable edge (every null mean within ±0.1 bps of zero, all CIs
bracketing zero), and the known-positive injection recovers the planted net edge
`m` almost exactly (closed-form, machine-precision recovery). The P0 aggregation
precondition for the new {5, 240}-minute parameterizations passes fully (56/56
checks PASS, all 4 negative controls detected per period). Five known-positive
cells — all on the 4h domain, at sub-material edges (`m` = 1, 2 bps) — recover
the planted mean but cannot separate it from zero across draws; per the
predeclared design §11/D-prec these are first-class **under-powered**
(per-cell INCONCLUSIVE) results, not substrate failures. The substrate gate is
**PASS**: EXP-002/003 may build on it, with the 4h domain's reduced power
recorded as a known, economically-immaterial limitation.

## Detailed Findings

### Finding 1 — P0 aggregation precondition passes for 5m and 240m

- **Observation**: All 56 P0 checks PASS (`p0_aggregation_checks.csv`); 0 FAIL.
- **Evidence**: Per instrument × period {5, 240}: independent strict pandas
  resample oracle matches `aggregate_ohlc` with 0 OHLC mismatches and 0
  rows-only-in-either; strict and 0.90 outputs show 0 future rows, 0
  below-floor coverage rows, 0 duplicate `CloseTime`; and all four negative
  controls (oracle mismatch, future row, low coverage, duplicate close-time) are
  detected. This extends VAL-001 (which covered {1,15,60}m) to the periods this
  phase actually uses, satisfying checkpoint precondition P0 (§9).
- **Interpretation**: The 5m and 4h domains are built on a verified aggregation
  path; downstream domain construction is trustworthy.

### Finding 2 — Known-null generators carry no recoverable edge

- **Observation**: For every (instrument, domain), both `bar_permutation` and
  `random_signal` nulls have mean gross oracle effect ≈ 0 with percentile CIs
  bracketing zero.
- **Evidence** (`substrate_summary.csv`): null `mean_effect_bps` ranges
  [−0.087, +0.103] across all 24 null cells; every CI satisfies
  `ci_lower ≤ 0 ≤ ci_upper`; `|mean| ≤ 1.0` bps tolerance met everywhere
  (200 draws/cell). Two structurally different nulls agreeing confirms the
  near-zero result is not an artifact of one construction.
- **Interpretation**: A referee tested against these nulls is being fed genuinely
  edge-free inputs — the false-positive measurements in EXP-003 will be measuring
  the referee, not a contaminated substrate.

### Finding 3 — Known-positive injection recovers the planted edge

- **Observation**: Recovered net effect tracks planted `m` across the full grid
  `{0, 0.5, …, 32}` bps on every domain.
- **Evidence**: Audit re-derivation shows `strategy_bps = s·r·1e4 + m` exactly,
  reproduced to machine epsilon (`|diff| ≤ 2.2e-16`). In `substrate_summary.csv`,
  high-effective-sample domains recover tightly (e.g. EURUSD/5m: `0.5→0.5007`,
  `32→32.0005`; XAUUSD/5m: `1→1.0000`). All non-zero positive cells satisfy the
  recovery tolerance `max(0.5 bps, 15% of m)`.
- **Interpretation**: The MDE map EXP-003 will build rests on a generator whose
  planted magnitude is recovered without bias — the magnitude axis is calibrated.

### Finding 4 — 4h sub-material edges are under-powered (reported, not failed)

- **Observation**: 5 cells are per-cell INCONCLUSIVE: BTCUSD 4h `m`=1,2;
  USTEC 4h `m`=1,2; XAUUSD 4h `m`=1 (`underpowered_cells.csv`).
- **Evidence**: Each recovers the planted mean (e.g. BTCUSD 4h `m`=2 →
  mean 2.057) but its across-draw percentile CI straddles zero
  (`ci_lower` = −2.72 to −0.12). The 4h domain retains only ~2,700–4,400 returns
  per instrument and BTC/XAU per-bar dispersion is large, so the draw-mean noise
  (several bps) swamps a 1–2 bps signal. Critically, all five sit **below the 4h
  economic materiality threshold of 3.0 bps**, so non-separability here is
  economically immaterial.
- **Interpretation**: This is exactly the precision shortfall §11 predeclared as
  "expected most likely on the 4h domain." It is a property of effective sample
  size, not a broken substrate. It does flag that EXP-003's 4h power curve near
  the materiality boundary will carry wide uncertainty.

## Hypothesis Verdict

**SUPPORTED**

The hypothesis — known-null generators produce no oracle-recoverable edge, and
the known-positive generator carries the planted oracle-recoverable net edge, on
real analysis-set prices for each of 5m/1h/4h — holds. Every P0 check passes;
every null is indistinguishable from zero; every positive recovers `m` within
tolerance. The only shortfalls are 4h sub-material significance cells, which the
predeclared criteria classify as under-powered INCONCLUSIVE (not failures). Per
the scope's overall-status rule (`FAIL` only on a P0 failure or a broken cell;
else `INCONCLUSIVE` only if a domain could not be measured at all; else `PASS`),
the substrate gate is **PASS**. `run_metadata.json` records
`overall_status: PASS`, `p0_pass: true`, `substrate_pass: true`,
`inconclusive_cells: 0`, `underpowered_cells: 5`.

## Limitations

- **Recovery precision, not single-series detectability.** The known-positive
  "significance" sub-test measures whether the across-draw mean clears zero
  (Monte-Carlo recovery precision under random states), not whether one series'
  edge is detectable by an inference unit. EXP-003 power curves are the proper
  detectability measurement; EXP-001 only certifies the substrate.
- **4h effective sample is small.** ~2,700–4,400 returns per 4h instrument bound
  the precision attainable on the long domain; sub-3 bps effects there are not
  reliably separable from zero.
- **Cost/materiality defaults are frozen, not data-derived.** The data layer
  stores no spread; per-instrument/domain round-trip costs are predeclared
  conservative constants (`referee_calibration.ROUND_TRIP_COST_BPS`). The
  substrate's validity does not depend on them (recovery is closed-form), but the
  economic units everything is reported in do.

## Alternative Explanations

- Could near-zero null means hide a structured edge? Two independent null
  constructions (permutation vs random-signal) agree at ≈0, and the random state
  is provably independent of returns (spot-checked), so an accidental recoverable
  state is implausible.
- Could the 4h INCONCLUSIVE cells indicate a recovery bug rather than low power?
  No — the *means* recover `m` correctly; only the across-draw CIs are wide. A
  recovery bug would bias the mean, which it does not.

## Recommended Next Steps

1. **Proceed to EXP-002** (referee golden-fixture correctness) — the substrate
   gate is satisfied; no new scope needed.
2. **EXP-003 (keystone)**: report 4h power curves with explicit effective-N and
   honest wide CIs near the materiality boundary; treat 4h under-power as a
   measured operating characteristic, consistent with this experiment.
3. **Future scope (new EXP)**: if a tighter 4h MDE is ever required, a dedicated
   experiment could test whether a longer outcome horizon or a different 4h
   inference atom raises 4h effective sample — out of scope for Phase 001.
