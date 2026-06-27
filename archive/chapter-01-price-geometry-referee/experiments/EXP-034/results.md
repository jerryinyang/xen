# Results: Experiment EXP-034

## Summary

**A1 strict pass: EURUSD-4h SEQUENCE_PASS_ALPHA05.** Under frozen CONSERVATIVE costs plus the predeclared financing layer, EURUSD-4h retains positive net per-event expectancy of +11.77 bps [one-sided 95% lower bound = 3.90 bps, boot_p = 0.009]. The sequence stopped at the second declared cell (USTEC-4h INCONCLUSIVE_SPANS_ZERO, as predeclared by the power statement). XAUUSD-1h was not tested.

Per design §8.4 as amended 2026-06-10 (F02), this A1 strict pass is **necessary-but-not-sufficient** for holdout release — it routes EURUSD-4h into a one-shot Tier-B TEST-stratum confirmation.

## Detailed Findings

### Finding 1: EURUSD-4h Strict Pass

- **Observation**: EURUSD-4h net point = +11.77 bps, one-sided 95% lower bound = +3.90 bps, one-sided bootstrap p = 0.009. Both prongs of the binding rule pass (p ≤ 0.05 AND CI_low_1s > 0).
- **Evidence**: `results/sequence_verdicts.csv` row 1. Pre-financing net_cons = +12.38 bps (EXP-030); financing = 0.61 bps mean per event (multi-day holds). Plot: `plots/declared_cells_net.png`, `plots/financing_waterfall.png`.
- **Interpretation**: The EXP-030 disclosure (EURUSD-4h net_cons = +12.38 bps with CI_low = +2.67) survives the financing layer. 4h holds are multi-day (~1–2 calendar days), so the financing charge (~0.6 bps/day × 1-2 days) is small relative to the RT cost (3.0 bps) and far below the headroom. The pass is not a marginal near-zero outcome — the point (11.77 bps) is well clear of zero, the one-sided lower bound (3.90 bps) is positive, and p = 0.009 is decisive. On n=39 events, the regime-cluster bootstrap CI width (~18.4 bps) is wide but the effect is large enough to resolve.

### Finding 2: USTEC-4h INCONCLUSIVE as Predeclared

- **Observation**: USTEC-4h net point = +8.90 bps, two-sided CI = [−21.10, +35.09], boot_p = 0.281. The CI spans zero by a wide margin.
- **Evidence**: `results/sequence_verdicts.csv` row 2. Plot: `plots/declared_cells_net.png`.
- **Interpretation**: Exactly as the predeclared power statement forecast: n=36 events, CI half-width ≈ 28 bps, the ≈ +10 bps point cannot resolve. This is a power limitation, not evidence of absence. The cell carries G1-lenient continuation (point = +8.90 > 0, CI_high = +35.09 > 0) but is not eligible for strict G2 consideration from A1 alone.

### Finding 3: XAUUSD-1h Not Tested (Sequence Stopped)

- **Observation**: Sequence stopped at USTEC-4h failure, so XAUUSD-1h carries `NOT_TESTED_SEQUENCE`. Descriptive label: INCONCLUSIVE_SPANS_ZERO (net = −0.35 bps, CI = [−5.18, +4.51], boot_p = 0.563).
- **Evidence**: `results/sequence_verdicts.csv` row 3.
- **Interpretation**: Per the power statement, this was expected: the pre-financing net was ≈ 0.00 bps, financing (~0.35 bps) pushed the net point negative, and the CI spans a wide range. G1-lenient continuation flag is `false` (point ≤ 0).

### Finding 4: All-12-Cell Descriptive Map

- **Observation**: All non-declared cells are EVIDENCE_AGAINST (net CIs entirely below 0) or INCONCLUSIVE_SPANS_ZERO. No cell outside the declared family has positive net.
- **Evidence**: `results/cell_inference.csv`. Plot: `plots/all_cells_map.png`.
- **Interpretation**: Confirms the EXP-030 picture: the only headroom is EURUSD-4h. USTEC-4h has a positive point (+8.90 bps) but is power-limited. Every 5m and 1h cell is clearly negative. BTCUSD dominates the cost drag as in EXP-030.

## Verdict

**A1 STRICT PASS (TEST CONFIRMATION REQUIRED)**

EURUSD-4h passes the binding one-sided α = 0.05 test (SEQUENCE_PASS_ALPHA05). Per design §8.4 (amended F02, 2026-06-10): this is necessary-but-not-sufficient for holdout release. The pass routes EURUSD-4h into a one-shot Tier-B TEST-stratum confirmation of the same registered baseline estimand. Only that TEST result can satisfy G2 and make EXP-032 admissible.

## Limitations

- n=39 for EURUSD-4h is small — the bootstrap CI half-width is ~9.2 bps. The strict pass is well-resolved but precision is limited.
- This is an analysis-set read (same population as EXP-028/030). Selection of the declared family from EXP-030 disclosures is data-dependent; the TEST confirmation at Tier B is the out-of-sample read.
- Financing rates are predeclared constants (EURUSD 0.6 bps/day). Real swap costs vary.
- The binding verdict uses the one-sided bootstrap p and one-sided 95% lower bound, which agree up to percentile interpolation. For results away from the boundary (boot_p = 0.009, CI_low_1s = 3.90 bps), the distinction is immaterial.

## Alternative Explanations

- EURUSD-4h's small sample (39 events) could be regime-specific — 39 events from 2026 H1 may not represent the long-run process. The Tier-B TEST confirmation partially addresses this.
- Financing at 0.6 bps/day for EURUSD is conservative (adverse-side regardless of direction). Actual swap costs for long EURUSD positions may be lower or negative (earn rather than pay), making the true net expectancy higher.

## Recommended Next Steps

- Register EURUSD-4h TEST confirmation in Tier B (0 new slots; same registered baseline estimand on the held-back TEST segment). Predeclare the TEST protocol before reading TEST rows.
- If TEST confirms, the holdout-release checkpoint (EXP-032) becomes admissible behind G2.
