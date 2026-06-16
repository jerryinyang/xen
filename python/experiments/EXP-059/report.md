# Experiment Report: EXP-059 — Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)

## Status: COMPLETED

**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); 12 predeclared position-management exit arms; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised position-weighted gross return endpoint

---

## Question

Does replacing the benchmark single fixed exit (50% favourable / 1:1 adverse / adaptive time cap, single leg) with favourable-side scaled take-profits (`/EXIT-PARTIAL`) and/or an adverse-side market-structure trailing stop (`/EXIT-TRAIL-STRUCT`, 0.5×ATR ZigZag) — individually and combined — raise the conditioned HA harami's gross per-event median position-weighted expectancy (P14) vs the benchmark, and which scheme (if any) wins?

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move, third barrier held at the benchmark adaptive time cap), at least one position-management exit scheme — favourable-side scaled exits (`/EXIT-PARTIAL` V1, V2A, V2B, V2C), adverse-side structure trailing (`/EXIT-TRAIL-STRUCT` PURE, TP-INIT, TP-NOINIT), or their combination (COMBINED-V1/V2A/V2B/V2C) — produces higher gross per-event median expectancy (P14, ATR-normalised, position-weighted realised return, P15 fills, real prices) than the benchmark single fixed exit (50% fav / 1:1 stop / adaptive cap, single leg), on the binding `/STRONG-STAT` arm.

## Method Summary

12-arm OAT sweep over the 99-cell conditioned-signal grid. Each arm's per-event position-weighted realised return was computed via P15 path-ordered fills from the new `position_exits.py` resolvers (multi-leg partial-exit resolver + causal monotone structure trailing-stop builder). Per-cell median expectancy was bootstrapped (regime-clustered moving-block, 10,000 draws), and each variant was compared against the benchmark via a paired-median contrast on the common qualifying-event subset. P11 composition (≥5 cells over ≥3 instruments, WIN = viable + beats benchmark) determined the verdict.

## Key Findings

### Finding 1: All four PARTIAL arms clear P11 — favourable-side scaled exits materially improve conditioned expectancy

| Arm | Powered | Viable | Wins (cells) | Wins (instruments) | P11 |
|-----|---------|--------|-------------|-------------------|-----|
| PARTIAL-V1 | 99 | 40 | 25 | 14 | YES |
| PARTIAL-V2A | 99 | 57 | 53 | 17 | YES |
| PARTIAL-V2B | 99 | 33 | 27 | 14 | YES |
| PARTIAL-V2C | 99 | 56 | 45 | 17 | YES |
| BENCH | 99 | 9 | 0 | 0 | — |

The mechanism hypothesis is confirmed: scaling out at intermediate favourable levels banks profit before reversal or time-cap expiry, capturing more of the available conditioned move than waiting for a single 50% target. V2A (even-thirds fractional targets at 33/66/100% of `fav_dist`) is the strongest, with 53 wins over benchmark across all 17 instruments.

### Finding 2: Structure trailing stop is uniformly detrimental within the benchmark horizon

| Arm | Powered | Viable | Wins | P11 |
|-----|---------|--------|------|-----|
| TRAIL-PURE | 99 | 0 | 0 | NO |
| TRAIL-TP-INIT | 99 | 0 | 0 | NO |
| TRAIL-TP-NOINIT | 99 | 0 | 0 | NO |
| COMBINED-V1/V2A/V2B/V2C | 99 each | 0 | 0 | NO |

All 7 arms with a structure trailing stop produce zero viable cells — 100% CI_SPANS_0 across the entire grid. The 0.5×ATR ZigZag retracement fires frequently within the 6-bar cap window, tightening the stop before favourable exits can realise. This is a clean OAT measurement within the scoped limitation: "trailing does not help within ~6 bars." The horizon × position-management interaction is EXP-060.

### Finding 3: Combined arms (partial fav + trail adverse) destroy partial-exit advantage

All 4 COMBINED arms produce 0 viable cells vs 25–53 wins for standalone PARTIAL arms. Replacing the fixed 1:1 stop with the structure trailing stop on partial-leg positions causes the trail to bind before partial legs can realise their value. The 1:1 fixed stop is the superior adverse-side treatment at this horizon.

### Finding 4: BENCH reproduces EXP-053 exactly

All 99 cells: `m_match=true`, `median_match=true`, `r_match=true` — byte-identical per-cell median expectancy, qualifying count, and first-hit `r`. 0 defects, 0 invariant violations, 0 causality violations across all 12 arms. Determinism verified on all 17 instruments.

## Conclusion

**EVIDENCE_FOR** — At least one position-management exit scheme (`/EXIT-PARTIAL`) clears P11 on its own median expectancy and beats the benchmark on the paired contrast within the quorum. The `/EXIT-TRAIL-STRUCT` branch (adverse-side structure trailing) does not improve capture within the benchmark horizon — a measured-negative characterization that is a valid input to G2.

The PARTIAL-V2A (even-thirds) scheme is the strongest at 53 wins over benchmark across all 17 instruments. Within the benchmark adaptive cap (6-bar floor in 96/99 cells), partial exits consistently outperform the single-leg fixed exit. The trailing stop mechanism requires a longer horizon to be viable — the horizon × position-management interaction is deferred to EXP-060.

## Registry Disposition

**Registry-relevant** — HYP-012 of CF-HA-HARAMI-001 (position-management exits). The `/EXIT-PARTIAL` branch is EVIDENCE_FOR; `/EXIT-TRAIL-STRUCT` is characterized as uniformly detrimental within the benchmark horizon. Updates applied:
- `multiplicity-registry.md`: HYP-012 status updated from PLANNED to EVIDENCE_FOR with 4 passing arms
- `candidate-families/harami.md`: HYP-012 narrative updated with completed result
- No TEST reads consumed (TRAIN-only); test-read-ledger.md unchanged

## Limitations

1. **Benchmark cap bounds runner/reversal legs.** The P4 adaptive cap collapsed to the 6-bar floor in 96/99 cells, limiting the reversal-event legs (V1, V2C), the V2B 1.5× runner, and all TRAIL arms to ~6 bars. The clean-OAT measurement is valid, but the horizon × position-management interaction is deferred to EXP-060.

2. **`ATR_MULT_TRAIL = 0.5` is frozen.** The trailing structure sensitivity to the ZigZag ATR multiplier is not tested here; a coarser trail might behave differently.

3. **Gross only; no costs.** Partial exits incur more trades (3 fills per event vs 1), increasing cost drag at a future tradability screen.

4. **P15 fill approximation.** Intrabar motion is modelled by the P15 path order; 1-minute base bars are not replayed. EXP-054 bounds this error.

5. **DE30 truncated broker history** (2026-01-16). Its counts derive from its own realised timeline.

## Implications for Future Research

- Favourable-side scaled exits are a validated lever: partial profit-taking within a short horizon captures more gross edge than single-target exits.
- Structure trailing stops on the adverse side require room to run — they are not viable within a ~6-bar cap window. The mechanism may become beneficial with longer horizons (EXP-060).
- The clean-OAT design confirmed that adverse-side trailing and partial-leg favourable exits are antagonistic within the benchmark cap: combining them (COMBINED arms) destroys the partial-exit advantage.

## Recommended Next Steps

1. **EXP-060 (combined event system):** Pair the best partial-exit scheme (V2A) with the best EXP-058 third barrier (`/THIRD-TIME` or `/THIRD-EVENT`) to test whether a longer horizon allows partial-exit advantage to compound and whether the trailing stop becomes viable with more room to run.

2. **EXP-059B (uncapped trailing):** Measure `/EXIT-TRAIL-UNCAPPED` as a standalone adverse-exit model with no time-cap backstop and no initial 1:1 stop — the pure trailing design that EXP-059 could not measure within the benchmark cap.

3. **`ATR_MULT_TRAIL` sensitivity sweep:** Test trail at coarser ZigZag multipliers (e.g., 0.75, 1.0, 1.5) to see if a looser trailing structure becomes beneficial.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Composition Readout | [results/composition_readout.json](results/composition_readout.json) |
| Run Metadata | [results/run_metadata.json](results/run_metadata.json) |
