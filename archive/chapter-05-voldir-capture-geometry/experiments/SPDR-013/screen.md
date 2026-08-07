# SPDR-013 — screen summary (neutral quantification)

- **Family:** `CF-VOLDIR-001` / **HYP-B** · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Question (design §1):** do fast, simple direction policies (mid-term SMA benchmark; ATR
  ZigZag structure) deliver positive **expectancy in bps** — scored by availability-when-right /
  damage-when-wrong, not win-rate — under frozen cut-loser/let-winner capture geometry?
- **Status:** neutral quantification, **subordinate to `analysis.md`** (the binding fresh-context
  read). No verdict, no family status change, no tradability claim.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net understates true cost; reported expectancy overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

All bps are open-to-open per episode (§4 UNIT-PIN). Cost = fee 11.0 + funding 1.0×stamps +
allowance 2.0 (governing). Bands are **labels, never gates** (§7.2). DESIGN is primary; CONFIRM is
the TRAIN-internal verify. Run: 25 symbols × (6 D-SMA cells + D-ZZ) × 5 exit modes × 2 clocks ×
2 bands = **2940 cells, 1.64M episodes**. Integrity self-check **PASS** (`results/
integrity_selfcheck.json`).

## 0. Headline numbers (DESIGN band; medians across symbols)

| Read | Value | Where |
|---|---|---|
| Cells labelled **SUPPORTED** | **0** of 2940 | `expectancy_by_cell.parquet` |
| Cells labelled WASH | 0 | — |
| Cells CONTRADICTED / UNPOWERED | 323 / 2617 | — |
| Net expectancy, trend arms (combined/signalflip, H1) | **−12 to −13 bps** (median) | ≈ the 13.5 cost floor |
| **Gross** expectancy, same arms H1 | **+1.6 bps** (median) | breakeven-ish gross |
| ZZ structural leg (signalflip) H1 | gross **+9.4** / net **−6.5** bps | `signal=D-ZZ,exit=signalflip` |
| **ZZ next-swing MAGNITUDE forecast** (ridge, M15) | **OOS IC 0.46** (AR1 0.44) | `zz_forecast.json` |
| ZZ next-swing path_noise/vol forecast | **IC ≈ 0** (null) | `zz_forecast.json` |
| Signal-timing vs side-deranged null (net) | live percentile **0.40** | `controls.json` derangement |
| Matched random-entry (net) | live percentile 0.56 | `controls.json` matched_random |
| Capture give-back (reached MFE − realized gross), H1 combined | **60–70 bps** | `mfe_capture_by_arm.parquet` |
| Signal horizon-MFE ÷ random horizon-MFE (all arms) | **0.95–1.03** (ambient) | `mfe_signal_vs_random.parquet` |

## 1. Expectancy decomposition (§5), DESIGN, powered cells (n≥80), median over symbols

| exit_mode | clock | cells | exp_partial (mean) | exp_gross (mean) | avail_right | damage_wrong | p_right |
|---|---|---:|---:|---:|---:|---:|---:|
| combined | H1 | 110 | −12.0 | +1.6 | 223 | −118 | 0.369 |
| combined | M15 | 117 | −15.3 | −2.2 | 109 | −60 | 0.365 |
| signalflip | H1 | 110 | −12.6 | +1.6 | 311 | −124 | 0.334 |
| signalflip | M15 | 117 | −16.6 | −3.2 | 157 | −63 | 0.314 |
| time | H1 | 66 | −30.1 | −10.9 | 441 | −457 | 0.468 |
| time | M15 | 84 | −24.8 | −5.9 | 466 | −453 | 0.486 |
| stop | H1/M15 | 1/31 | −294 / −131 | −263 / −111 | 499 / 396 | −314 / −130 | 0.06 / 0.03 |
| trail | M15 | 28 | +66.1 | +86.0 | 120 | −100 | 0.873 |

- **Shape (trend arms):** low hit-rate (`p_right` ≈ 0.33–0.37) with large availability when right
  (≈ 220–310 bps H1) and smaller damage when wrong — the classic let-winners-run profile. Gross
  sits ≈ breakeven on H1, negative on M15. **Net is cost-fatal** (≈ −12 to −16 bps ≈ the 13.5 cost
  floor).
- **Fat tails (AMENDMENT-E1 mean vs median):** severe. Combined SMA14 SOL H1 mean −2 bps vs median
  −47 bps; `stop`/`trail` arms have tiny episode counts and one-tail means (all UNPOWERED).
- **125 cells** carry a positive mean `expectancy_partial` but **every one is UNPOWERED** (MDE
  > 10 bps and/or <30 dates and/or thirds-unstable) — mostly `time`/`trail` arms on BTC. None
  reaches SUPPORTED.

## 2. Exit-mode decomposition (AMENDMENT-A3)

- `combined` ≈ `signalflip` on net (the signal-flip exit dominates the combined stack; stop/trail/
  time rarely bind on the trend arms).
- `stop`-only and `trail`-only: tiny episode counts (winners run to band edge with no upper exit)
  → one-tail means, all UNPOWERED. Not interpretable as expectancy.
- `time`-only: symmetric avail≈|damage| (~450 bps each), `p_right`≈0.48 → a near-coin-flip on
  gross; net −25 to −30 bps.
- **Structural leg (D-ZZ signalflip):** H1 gross median **+9.4 bps** (per-symbol −150…+425), net
  −6.5; M15 gross −3.8, net −17.4. The structure offers thin positive gross on H1, swamped by the
  cost floor.

## 3. ZZ next-move forecast heads (§3.3, mandatory) — OOS IC, median over 25 symbols

| target | model | H1 | M15 |
|---|---|---:|---:|
| next-swing **magnitude** (bps) | AR(1) | 0.343 | 0.436 |
| next-swing **magnitude** (bps) | ridge | 0.372 | **0.457** |
| next-swing **path_noise** (vol) | AR(1) | −0.037 | −0.022 |
| next-swing **path_noise** (vol) | ridge | −0.002 | −0.000 |

- **Next-swing magnitude is forecastable** (IC 0.34–0.46; ridge ≥ AR1; M15 > H1). The largest
  single positive, powered signal in the screen.
- **Next-swing path_noise/volatility is not** (IC ≈ 0 both models, both clocks).

## 4. Controls (§6) — combined arm, net expectancy

| Control | Read (median over 588 powered cells) |
|---|---|
| DIRECTION-DERANGEMENT (sides shuffled within symbol×third) | live percentile vs null **0.40** — live at/below the side-deranged null; +20 bps bite plant detected |
| MATCHED-RANDOM-ENTRY (random timing, same side dist/cap) | live percentile **0.56** — marginally above random; +20 bps bite plant detected |
| SMA-BENCHMARK Δ (ZZ − SMA14/25) | `controls.json` `sma_benchmark_delta` (disclosure) |
| PATH-FUTURE-DESTROY tripwire | **INFORMATIVE only (DEV-1)**; 1 survivor of 100 powered D-SMA14 cells (SOL SMA14 H1 CONFIRM, live −2.23, not a positive-edge claim) |

- On **net** expectancy the signed signal does **not** beat its own side-deranged null (percentile
  0.40) and only marginally beats random timing (0.56). No net signal-timing edge is visible.

## 5. Capture geometry & availability (MFE — operator question 2026-07-23)

Per-episode maximum favourable / adverse excursion added to the emission (`mfe_oo_bps`,
`mae_oo_bps`, `mfe_hi_bps`; fixed-horizon `horizon_*` over entry→entry+cap). **All MFE reads are
non-tradable ceilings** (they peek at the within-window peak). Artifacts:
`results/mfe_capture_by_arm.parquet`, `mfe_signal_vs_random.parquet`, `analysis_code/mfe_capture.py`.

**(a) The geometry gives back reached favourable ground** (DESIGN, median over symbols):

| arm (H1) | reached favourable MFE_oo | realized gross | give-back | net ceiling (MFE−13.5) |
|---|---:|---:|---:|---:|
| SMA14 combined | +25 | −40 | 64 | +11 |
| SMA25 combined | +30 | −40 | 71 | +17 |
| D-ZZ signalflip (structural leg) | **+194** | −86 | **280** | **+180** |

Arms reach favourable excursion, then round-trip it into losses. Worst on the ZZ structural leg and
the long-hold arms.

**(b) But that favourable excursion is AMBIENT, not signal-granted** — signal horizon-MFE ÷
random-timing (50/50 side) horizon-MFE:

| | H1 | M15 |
|---|---:|---:|
| `sig_over_rand` (every arm) | **0.95–1.03** | 0.97–0.99 |

Signal entries reach **no more** forward favourable excursion than random entries. The ~300–370 bps
horizon availability is 48-bar crypto volatility, available to any entry. Consistent with the
derangement percentile ≈ 0.5.

**Read (neutral):** the give-back is real, but it is ambient volatility the direction signal fails
to *select* — a better exit would lift the signal and random entries equally. Capturing it is a
**direction-agnostic / volatility-harvest** question, not a rescue of signed direction.

## 6. Integrity (self-check PASS)

| Check | Result |
|---|---|
| TRAIN-only, max exit < train_end; no holdout | PASS |
| Entry strictly after signal bar; ATR[t−1]; features ≤ signal bar | PASS (construction) |
| Engine parity (sequential == batch, §4) | PASS (`max_rel 0.0`) |
| Universe top-25 pin recompute == both pin files | PASS |
| Golden G1 (SMA flip) / G2 (stop) / G3 (ZZ features) + independent fixture | PASS |
| Derangements fixed-point-free (L-28) | PASS |
| Future-destroy tripwire | INFORMATIVE only (DEV-1); no positive-edge survivor |
| Deviations operator-signed | DEV-1 signed 2026-07-23 |
| Parallel==sequential determinism (`--jobs`) | PASS (spawn; 2256 fields bit-identical, 0 mismatch) |

Full clause map: `results/compliance_trace.md`. Amendments (operator-signed 2026-07-23): DEV-1/
AMENDMENT-T1 (tripwire→informative), AMENDMENT-A3 (exit modes), AMENDMENT-E1 (medians).

## 7. What this hands Reflection C (neutral)

- Signed **direction net expectancy is cost-fatal and shows no net timing edge** on the frozen
  arms — 0 SUPPORTED cells; derangement percentile ≈ 0.5 (H1) / <0.5 (M15).
- **Gross** direction availability is thin and real on H1 (breakeven-ish; structural leg +9 gross);
  it dies at the ~13.5 bps cost floor.
- **MFE:** the geometry gives back reached favourable ground (give-back 60–280 bps), but that
  availability is **ambient, not signal-granted** (`sig_over_rand` ≈ 1.0) → a direction-agnostic
  harvest question, not a signed-direction fix.
- The one clearly powered positive is the **ZZ next-swing magnitude forecast (IC ~0.34–0.46)**;
  path_noise/vol is not forecastable.

These are magnitudes, not a verdict. `analysis.md` interrogates them per stratum; the operator
takes the direction-readiness call at Reflection C.
