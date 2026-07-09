# CF-HTFDI-001 — HTF-DI Conditioning (Family Detail Index)

**Status: RETIRED (2026-07-09, operator-signed, checkpoint-010/011 retrospective)** — EXP-025
NOT SUPPORTED (magnitude, not existence); channel real at ≈4 bps/trade, untradable; 0 slots,
0 counted TEST reads, holdout sealed. Retrospective:
`../../checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/retrospective.md`.

Higher-timeframe Wilder ±DI direction conditioning the sign of the LTF forward return
(continuation thread, USTEC 1h/5min established stratum). Registered 2026-07-08 from the
SPDR-001/002/003 corrected series (checkpoint
`2026-07-08-010-htf-di-conditioning-spdr-series`, operator-signed); family card:
`docs/signal-registry/candidate-families/cf-htfdi-001.md`.

## Experiments

- [EXP-025 — HYP-A graduation: HTF-DI-confirmed breakout, 22 symbols, 1h/5min](#exp-025--hyp-a-graduation-htf-di-confirmed-breakout-22-symbols-1h5min)

---

## EXP-025 — HYP-A graduation: HTF-DI-confirmed breakout, 22 symbols, 1h/5min

**Status**: COMPLETED
**Date**: 2026-07-09
**Instruments**: 22 loaded symbols (10 FX, 10 indices, XAUUSD, BTCUSD)
**Data Views / Feature Categories**: 5min/1h clock resamples of m1; engine per-trade emissions; 1h Wilder ADX/±DI/ATR(14)

### Hypothesis Tests

1. **Hypothesis**: a CTRL-02 momentum breakout gated by last-closed 1h ±DI agreement carries
   a net-of-commission per-trade directional edge on some instrument at 1h/5min, confirmed on
   a counted TEST read (per-instrument max-stat over holds + Holm); vol-regime interaction
   measured as an amplifier (never a sign-setter).

### Scope

- **Instruments**: full 22-symbol loaded universe (operator-directed).
- **Vehicle**: X-bar HH/LL close breakout (X ∈ {2,3,4,5,8}), DI-gate, fixed holds H ∈
  {12,24,36,48} 5min bars; 1-unit notional, one position at a time; engine costless, costs
  analyst-injected (FTMO table).
- **Protocol**: T1 TRAIN 440 runs → SEL-NEIGHBOR (WF-EXPANDING folds) → T2 exits (survivors
  only) → capped counted TEST (≤5 reads, Holm). Controls: 25-seed matched-cadence
  random-direction battery, random-entry reference arm (dir_gap), ADX-only null sentinel;
  +60-bar HTF phase-shift tripwire (post-selection).
- **Exclusions**: no 1d/1h, no 4h/1h, no fade priors, no sizing, no exit re-tuning after
  TEST contact.

### Results / Observations

- 2,432,812 non-censored TRAIN trades over 440 cells; per-symbol n ≈ 48k–141k. All 22 (+75
  battery) estimand gates `blocking_pass: true`.
- SEL-NEIGHBOR: **0/440 qualify**; rule 1 (own F0 CI_low > 0) fails in every cell (best
  −0.09, US500 x4h24). MDE 0.18–5.23 bps per cell; 0 UNPOWERED.
- Full-TRAIN CI-clear cells: 3/440 (HK50 x2h48 +3.18 [0.13, 6.20]; US500 x4h24 +0.93
  [0.07, 1.80]; US500 x5h24 +0.93 [0.07, 1.81]) vs ≈11 expected by chance; all three FAIL F0
  and flip sign by year.
- Units reconciliation: USTEC TRAIN-median 1h ATR = 33.9 bps; 5min ATR = 8.19 bps. Ref-arm
  dir_gap in screen units: 0.026/0.136/0.217/0.415 ATR_5m at h12/24/36/48 (screen:
  +0.09→+0.50; h48 within CI). True screen effect ≈ 4 bps/trade at h48.
- Diagnostic battery (3 disclosure cells): US500 x4h24 z=2.62, x5h24 z=2.31 (both pct 1.00);
  HK50 x2h48 z=1.97 (marginal). Direction-timing gap on traded slots +1.9 (US500) / +6.2
  (HK50) bps; static side-imbalance ≈ 0.
- Direction split: 99% of 200 index cells have the stronger side = the instrument's realized
  drift side; FX 200/200 cells ≤ 0. No DI dose-response (low-margin halves ≥ high-margin).
- Sentinel family-wise: 1/22 CI-clear vs binomial 95th-pct threshold 3.

### Hypothesis-Specific Conclusion

**NOT SUPPORTED (magnitude, not existence)** — operator verdict 2026-07-09 (analyst
recommendation identical). No cell reaches pre-registered TEST eligibility; the negative is
powered against both the (fictitious) 30–60 bps design target and the corrected ~4 bps true
effect. The conditioning channel exists at ~1–3 bps/trade after capture dilution — below
commission on FX and ~1/10 of the noise-robust selection bar on indices.

### Hypothesis-Agnostic Observations

- The screen→graduation unit conversion was the failure seam (1h-ATR divisor asserted vs
  5min-ATR actual, 4.1×): codified as **L-21** with a binding unit-pin + money-unit-floor
  amendment in `docs/references/spdr-lane.md`.
- Two external reviews (2026-07-09) confirmed the chain and yielded **L-22** (spread must be
  a binding SUPPORTED tier), **L-23** (amendment-direction ledger; all seven 2026-07-08
  pre-measurement amendments loosened toward ADMIT), **L-24** (regime-stability eligibility,
  battery-under-exit* null, derived tripwire thresholds, MDE-consistent read floor +
  shrinkage-aware power math).
- h48 is systematically the friendliest hold across indices — mechanical drift capture
  growing with H, not a 1h-DI horizon story.
- DE40/STOXX50 missing from `xen.evaluation.FTMO_COSTS` under those keys (flagged).
