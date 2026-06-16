# Results: Experiment EXP-056 — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)

## Summary

Favourable-target geometry is **not a lever** that improves conditioned capture on this surface. No alternative variant clears P11 (≥5 cells over ≥3 instruments) for WIN (viable on own median AND beats benchmark on paired contrast). The verdict is **EVIDENCE_AGAINST**, mechanically correct per the predeclared Interpretation Guide. The scope question is answered: changing the favourable target — to a volume-profile level of the prior completed move (`/VPTARGET`: POC, near-VA edge, far-VA edge) or a trailing-magnitude distance (`/MAGTARGET`: {0.5,1.0} × median trailing-{5,20}) — does not systematically raise gross per-event median expectancy above the benchmark 50%-of-`M_sofar` target under the 1:1 adverse model and adaptive cap.

---

## Detailed Findings

### 1. No variant beats the benchmark robustly

| Variant | Viable cells | WIN cells | WIN instruments | P11 met? |
|---------|-------------|-----------|-----------------|----------|
| BENCH | 8 | — | — | — |
| VP-POC | 7 | **0** | 0 | No |
| VP-NEAR | 6 | **0** | 0 | No |
| VP-FAR | 5 | **0** | 0 | No |
| MAG-0.5x5 | 4 | **2** | 2 | No |
| MAG-1.0x5 | 5 | **0** | 0 | No |
| MAG-0.5x20 | 4 | **2** | 2 | No |
| MAG-1.0x20 | 8 | **1** | 1 | No |

P11 threshold: ≥5 WIN cells over ≥3 instruments. **No variant passes.**

All 99 cells are powered (≥30 qualifying events) on all 8 variants — the failure is systematic, not power-limited.

### 2. VP variants consistently trail the benchmark

All three `/VPTARGET` variants (POC, near-VA edge, far-VA edge of the prior completed move) produce 0 WIN cells. The volume profile of the prior move does not provide a better favourable target than the adaptive 50%-of-`M_sofar` level. Plausible explanations:

- The 50% benchmark is already an effective central-tendency estimator of the reversal move's geometry. The VP levels track the completed move's price distribution, not the *reversal's* expected extent — so they are structurally orthogonal to the capture problem.
- The VP POC often lies near the move's midpoint (by construction), similar to the 50% level, so the difference is marginal rather than structural.
- Profile exclusions (insufficient reference bars, levels on the wrong side) reduce counts but are disclosed and do not drive the negative.

### 3. MAG variants produce sparse, scattered wins

The best performers (MAG-0.5x5 and MAG-0.5x20) each produce 2 WIN cells on 2 instruments (USDCHF-4h, AUDJPY-30m). MAG-1.0x20 is viable in 8 cells (more than BENCH's 8) but beats the benchmark in only 1 cell (USDCHF-5m, by a marginal +0.000165 ATR units on the paired contrast).

The scattered WIN cells are concentrated in:
- **USDCHF-4h**: 2 MAG variants win (both 0.5×, W=5 and W=20).
- **AUDJPY-30m**: 2 MAG variants win (both 0.5×, W=5 and W=20).
- **USDCHF-5m**: 1 MAG variant wins (1.0×, W=20, marginal).

This pattern — specific cells on specific instruments — is consistent with noise-level variation rather than a systematic improvement. No instrument or domain shows multi-variant concentration that would warrant follow-up.

### 4. BENCH viability reproduces EXP-053

The BENCH variant reproduces EXP-053's conditioned-signal benchmark exactly: 8 cells with CI_low > 0 on the median expectancy (EURUSD-1h +0.113, BTCUSD-5m +0.057, BTCUSD-30m +0.159, etc.), all within a similar pattern of viability concentrated in 4h and slower-domain cells. EXP-053 reconciliation: 99/99 cells match to machine precision (m and median). This anchor confirms the same signal population is being measured.

### 5. Integrity checks all pass

- **Determinism**: 17 cells re-run byte-identical (first usable cell per instrument).
- **Causality**: 0 violations across all cells.
- **Reconciliation**: 99/99 cells match EXP-053 (m and median).
- **Defects**: 0 — no SUBSTRATE/METHOD_DEFECT.

---

## Hypothesis Verdict

**EVIDENCE_AGAINST.** Favourable-target geometry — whether a volume-profile level of the prior completed move or a trailing-magnitude distance — is not a lever that improves conditioned capture on this surface.

The scope's falsifiable condition was: *If no alternative favourable-target variant clears P11 on WIN (≥5 cells over ≥3 instruments with CI_low > 0 on its own expectancy AND CI_low > 0 on the paired benchmark contrast), then favourable-target geometry is not a lever.* This condition is met. The characterization is a measured-negative: no alternative target meaningfully surpasses the 50%-of-`M_sofar` benchmark.

---

## Limitations

1. **TickVolume proxy.** `/VPTARGET` uses broker tick count as a traded-volume proxy. The proxy limitation is disclosed in every result. A systematic volume-profile effect could be masked if tick count diverges from true traded volume for some instruments or regimes.
2. **Prior-completed-move VP reference only.** The VP variants reference only the immediately prior completed move (LOOKBACK=1). A multi-move or multi-modal VP profile was not tested.
3. **Gross only.** All results are gross of costs. The characterization is about favourable-target geometry as a capture lever on gross returns; net tradability is deferred to a future cost-bearing screen.
4. **Paired contrast sensitivity.** Variants with conditioned-exclusion patterns that differ from the benchmark (VP: validity/profile exclusions) have smaller `|S|` (common qualifying subset), reducing the paired contrast's power. Disclosed via `contrast_bench_n` per cell; not a material factor (all cells ≥30).

---

## Alternative Explanations

- **The 50% benchmark is already near-optimal.** The adaptive 50%-of-`M_sofar` level may sit near the optimal favourable distance for this entry substrate, leaving little room for improvement by VP-traced price levels or trailing-magnitude estimates.
- **Favourable target may not be the binding constraint.** EXP-049 found the unconditioned capture problem was not target placement but the `r≈0.50` structural symmetry. With conditioning applied (EXP-053), the benchmark modestly improves, but the favourable-target leg may still be the wrong lever — adverse geometry (EXP-057), third-barrier configuration (EXP-058), or exit geometry (EXP-059/060) may be more consequential.

---

## Recommended Next Steps

1. **Proceed to EXP-057 (Adverse-Target Geometry).** The favourable leg is measured and closed. The next surface read tests the asymmetric lever (`/ADV-EXTREME`, `/ADV-NONE`) that can directly shift `r` off 0.50 — the structural constraint EXP-049 identified.
2. **Proceed to EXP-058 (Third-Barrier Geometry).** The adaptive time cap is near its floor in most cells; `/THIRD-EVENT` and `/THIRD-TIME` may be more consequential than the favourable target.
3. **Continue the 014-B slate.** EXP-056 is a measured-negative surface read feeding the single G2 (per the 014-B design forbidding intermediate gates). No mid-slate routing change is warranted.
