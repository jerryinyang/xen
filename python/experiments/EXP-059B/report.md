# Experiment Report: EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)

## Status: EVIDENCE_AGAINST

**Date**: 2026-06-16
**Instruments**: 17 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); secondary ZigZag (`atr_mult=0.5`) for trailing ratchet; `/STRONG-STAT` live magnitude-percentile filter; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint

---

## Question

Does the structure trailing adverse-exit model, run **as designed** (no time-cap backstop, no initial 1:1 stop), raise the conditioned HA harami's gross per-event median expectancy vs the benchmark — and, vs its capped no-init sibling, how much of any difference is attributable specifically to removing the cap?

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move), an **uncapped structure trailing adverse-exit model** — no benchmark time-cap backstop and no initial 1:1 stop — either standalone (`TRAIL-PURE-UNCAPPED`) or combined with V2A partial favourable legs (`COMBINED-UNCAPPED-V2A`), produces **higher gross per-event median expectancy** (P14, ATR-normalised, position-weighted, P15 fills, real prices) than the **benchmark single fixed exit** (50% fav / 1:1 stop / adaptive cap).

Falsifiable: if neither uncapped arm clears P11 (≥5 cells over ≥3 instruments with CI_low > 0 on its own median expectancy) **and** beats BENCH (paired contrast CI_low > 0), then removing the cap/initial-stop does **not** improve conditioned capture.

## Method Summary

5-arm OAT sweep on the adverse-exit model over 99 cells: 2 binding uncapped arms (pure trailing with no cap/no init stop; V2A partial legs + uncapped trailing), 2 disclosed capped no-init siblings (cap-isolation contrast), and BENCH (reproduces EXP-053). Per-cell median bootstrap (10,000 draws, moving-block, `b=round(m^(1/3))`), arm−BENCH paired contrast on the common qualifying subset, and cap-isolation divergent-subset contrast. P11 composition (≥5 cells/≥3 instruments). TRAIN-only, 0 TEST reads, 0 candidate slots. Predeclared invariants all pass; determinism OK. [analysis-plan.md](analysis-plan.md)

## Key Findings

### Finding 1: No binding arm clears P11 — EVIDENCE_AGAINST

- **0 of 2 binding arms** produce a single winning cell (viable + beats BENCH). Hypothesis is falsified per the predeclared mechanical rule.
- `composition_readout.json`: verdict `EVIDENCE_AGAINST`, `n_pass: 0`, `passing_arms: []`.
- All 5 arms powered in all 99 cells. The INCONCLUSIVE_POWER_LIMITED scenario (scope's "materially more likely" outcome) did **not** materialize — total DATA_CENSORED is 15–22 events, negligible against tens of thousands of qualifying events. The EVIDENCE_AGAINST verdict is informative, not power-limited.

### Finding 2: Removing the initial stop dominates the result

- `TRAIL-PURE-UNCAPPED` has **0 viable cells** in 99 — uniformly negative median expectancy. Best cell (BTCUSD-5m) median = −0.41 ATR. Without the 1:1 initial stop, every position is exposed to unbounded adverse excursions before the first secondary ZigZag pivot (0.5× ATR) confirms — often 1–3 bars in fast markets.
- The mean is +0.10 in BTCUSD-5m (fat right tail from rare runners), confirming the P14 median is the correct endpoint for this widened distribution.

### Finding 3: V2A partial legs help but not enough

- `COMBINED-UNCAPPED-V2A` raises median vs pure trailing (BTCUSD-5m median = +0.08, CI_low = 0.01 — 1 viable cell) but **0 wins** — paired vs-BENCH contrast CI_low < 0 in that cell. The V2A fraction targets capture partial favourable excursion, but when the trailing stop binds on remaining weight, it fills at a worse level than the fixed 1:1 exit.

### Finding 4: Cap-isolation confirms the cap was not the constraint

- Even among the 35–48% of paired events the uncapped arm holds past the benchmark cap (divergent subset), the uncapped model does **not** systematically beat its capped no-init sibling: **0/96 divergent-positive cells** for TRAIL-PURE, **2/89** for COMBINED. The trailing stop, given enough rope, eventually fills at a worse price than the cap would have. The trailing mechanism's secondary-pivot ratchet is the bottleneck, not the horizon.

### Finding 5: BENCH itself is weak — important caveat

- BENCH is viable in only **9/99** cells (7 instruments). In 90/99 cells, BENCH's own CI spans 0 — the conditioned signal is not detectably positive under the simplest exit model. The EVIDENCE_AGAINST verdict describes "uncapped trailing does not beat the benchmark" but in most cells the benchmark itself is indistinguishable from zero. Audit Warning #1 records this caveat for G2.

## Conclusion

**EVIDENCE_AGAINST** — The hypothesis is falsified. Removing the benchmark time cap and initial stop from the structure trailing model does not improve conditioned HA harami capture. The trailing mechanism itself, not the horizon, is the binding constraint. The deliverable label is **UNCAPPED_TRAILING_CHARACTERISED** as a measured-negative characterization. Routing deferred to the single 014-B G2.

## Registry Disposition

**Updates applied.** Registry-relevant characterization of HYP-012b (`/EXIT-TRAIL-UNCAPPED`):
- `multiplicity-registry.md`: HYP-012b / EXP-059B updated from SCOPED to CHARACTERISED — EVIDENCE_AGAINST.
- `candidate-families/harami.md`: `/EXIT-TRAIL-UNCAPPED` branch status updated to reflect completed characterization.
- `test-read-ledger.md`: No changes — 0 TEST reads.

## Limitations

- **BENCH itself is weak** in 90/99 cells. The EVIDENCE_AGAINST verdict should be read alongside BENCH's own viability map at G2.
- **No initial stop widens the return distribution.** The median endpoint (P14) is correct, but the mean is positive in some cells where the median is negative.
- **`ATR_MULT_TRAIL = 0.5` is frozen.** A finer-pivot secondary ZigZag (e.g., 0.3× ATR) might ratchet faster and contain adverse excursions sooner. This sensitivity is out of scope.
- **Only V2A partials are tested.** Other partial-exit schemes were not paired with uncapped trailing.
- **Gross only** — no cost model. Higher trailing-stop fill frequency and longer holds likely widen the gap further.

## Implications for Future Research

- **Close `/EXIT-TRAIL-UNCAPPED`** as a characterized negative. No further investment in the single-uncapped-trailing branch for the conditioned HA harami population under the `atr_mult=0.5` secondary pivot ratchet.
- **Route to G2.** The full 014-B position-management surface (EXP-056/057/058/059/059B) is now characterised. G2 should assess the combined readout.
- **Do not pursue a finer-pivot ratchet** (`/THIRD-TIME`-analog grid) for the trailing stop on this population without re-evaluating the signal's MFE profile (EXP-055).

## Recommended Next Experiments

1. **Route to 014-B G2**: The remaining uncapped trailing question is answered; G2 should combine with EXP-056/057/058/059 and EXP-060 once available.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Composition Readout | [results/composition_readout.json](results/composition_readout.json) |
| Run Metadata | [results/run_metadata.json](results/run_metadata.json) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
