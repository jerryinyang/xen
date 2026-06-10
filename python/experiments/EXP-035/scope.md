# Experiment: EXP-035 — TRAIN-Only Conditioning Characterisation (Clinical-Trade Dimensions)

**Registry ID:** `CF-AVWAP-001/DIAG-005` (diagnostic; 0 candidate slots).
**Phase:** 008 (`docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`, §5/A3, §8.1).
**Depends on:** EXP-022/020 (event population + band geometry at trigger), EXP-030
(frozen cost model), EXP-027 (frozen inference tail), D0 memo.

## Hypothesis

Exploratory (characterisation — hard no-selection rule). Question: does the faithful
strategy's per-event **absolute net** expectancy (frozen CONSERVATIVE costs +
predeclared financing) vary **materially and stably** across three predeclared
event-time dimensions on TRAIN — enough to qualify a dimension for a single frozen
conditioning rule in Tier B (EXP-036 `/COND`) under the design §8.1 gate?

## Question

Are there predeclared, causally-available-at-confirmation event characteristics
that identify "clinical" subsets of bounce events whose net expectancy is positive —
without post-hoc stratum shopping?

## Scope Boundaries

- **Data Views**: EXP-022 `results/lifetime_observations.csv` (`role = event` rows;
  pyramids included); EXP-020 `results/avwap_events.csv` (trigger time, trigger
  close, band spread, favorable target — all at-trigger quantities); rebuilt 5m/1h/4h
  domain series (EXP-031-identical rebuild) for completion timestamps and the ATR
  covariate.
- **Parameters (FROZEN):** EXP-030 CONSERVATIVE costs; predeclared financing rates
  (EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 / BTCUSD 10.0 bps/day, adverse-side, fractional
  calendar days trigger→completion); frozen EXP-027 inference machinery (pinned hash
  `e50873d12a9f68d9`); G1 gate constants α_G1 = 0.10, SNR floor = 1.0 (design §8.1).
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (all four — heterogeneity structure
  is informative even on cost-excluded instruments; verdict-free).
- **Time range**: first 70% = analysis set; **this experiment reads TRAIN only =
  first 70% of the analysis set** (cutoff at 70% of analysis-set domain bars per
  instrument/domain by `CloseTime`). **Containment rule:** an event is included iff
  its `completion_idx` lies at or before the TRAIN cutoff index (the BTC-exit
  lifetime must complete inside TRAIN; no outcome reads past the boundary).
  Excluded-event counts disclosed per domain.
- **Global holdout**: never loaded, inspected, or used. TEST (last 30% of the
  analysis set) also never read here.
- **Look-ahead bias prevention**: all three covariates are computable strictly from
  data at or before the trigger timestamp (definitions below); outcomes use only the
  event's own lifetime.
- **Real-price outcome discipline**: real-OHLC `lifetime_bps` outcomes only.
- **Exclusions**: no stratum promotion or rule selection (G1 qualification flags are
  emitted; rule-freezing happens at Tier-B scope time, not here); no additional
  dimensions beyond the three below; no interaction/conjunction analysis; no
  matched-control estimands (absolute net only — this is a tradability-conditioning
  diagnostic); no exit variants; no TEST/holdout reads; outcome is never hit rate.

## Predeclared dimensions and bins (LOCKED before any TRAIN read)

1. **C1 — %completion-to-target at confirmation** (ordered):
   `c1 = 1 − dir_adjusted(favorable_target_at_trigger − trigger_close) /
   band_spread_at_trigger`, where the numerator is the direction-signed remaining
   favorable distance (positive when the target is ahead). Higher c1 = closer to
   target at confirmation. Causal: every term is an at-trigger column of
   `avwap_events.csv`. Bins: **TRAIN-quantile terciles, pooled per domain**
   (band-spread normalization makes c1 cross-instrument comparable). Tercile
   boundaries are computed once on TRAIN, recorded in results, and frozen.
   *Warning encoded in design §5/A3: c1 is mechanically coupled to remaining-move
   size — the outcome below is net expectancy, never hit rate.*
2. **C2 — Session** (unordered): trigger_time UTC hour → Asia [00:00, 08:00),
   London [08:00, 16:00), NY [16:00, 24:00). Fixed bins, no estimation.
3. **C3 — Trailing volatility regime** (ordered): ATR(14, domain bars) at the
   trigger bar, expressed as its percentile rank within the trailing 90-calendar-day
   window of the same instrument×domain series (strictly ≤ trigger timestamp;
   minimum 30 calendar days of history required, else the event is excluded from C3
   only, with disclosure). Bins: TRAIN-quantile terciles of the percentile, pooled
   per domain.

## Outcome and denominators (LOCKED)

- **Per-event outcome:** `net_e = lifetime_bps_e − RT_cons_i − financing_e`
  (faithful BTC-exit strategy, absolute, identical construction to EXP-034).
- **Per-bin statistic:** event-weighted mean of `net_e` over the bin's TRAIN events,
  per domain (pooled across instruments; instrument composition per bin disclosed).
- **Reportability floors (zero-baseline guard):** a bin with < 30 events (5m, 1h) or
  < 15 events (4h) is `unreportable`; a domain×dimension with any unreportable bin
  reports legs descriptively but is **ineligible for G1 qualification**. Expected:
  4h terciles (~40 events each) sit near the floor — 4h reads are disclosed but
  likely underpowered; this is predeclared, not a failure.

## G1 qualification test per domain × dimension (design §8.1, LOCKED)

- **Contrast:** ordered dims (C1, C3) — top-vs-bottom tercile difference Δ in mean
  net, with regime-cluster bootstrap CI and a one-sided permutation p (bin labels
  permuted within regime-cluster strata, 1000 permutations). Session (C2) — omnibus
  permutation heterogeneity test (between-bin spread statistic, labels permuted
  within strata); the candidate bin = max-net bin.
- **Qualify iff ALL of:**
  - (i) *Material*: Δ ≥ its own 95% bootstrap CI half-width (SNR ≥ 1) **and**
    top/candidate-bin TRAIN net point estimate > 0;
  - (ii) *Structured*: C1/C3 — weak monotone ordering of the three bin means;
    C2 — omnibus test significant;
  - (iii) *Stable*: chronological split-half of TRAIN — same top/candidate bin in
    both halves AND Δ > 0 in both halves;
  - (iv) *Multiplicity*: permutation p survives Holm across the 3 dimensions within
    the domain at α_G1 = 0.10.
- Output: `results/g1_qualification.csv` with one row per domain×dimension carrying
  every sub-criterion verdict and the final QUALIFIED flag. **No rule, threshold, or
  stratum is selected in this experiment.**

## Success / Failure Criteria

- **CHARACTERISATION_DELIVERED**: all reportable domain×dimension cells carry the
  full §8.1 read (contrast, CI, p, stability, flag); tercile boundaries and
  exclusion counts recorded.
- **PARTIAL**: ≥1 domain entirely unreportable after floors/containment (expected
  risk: 4h); deliver the rest, disclose.
- **Inconclusive**: frozen-tail hash or determinism replay fails — hard stop.

Any pattern of QUALIFIED flags (including none) is a valid outcome. Zero qualified
dimensions routes the phase toward FLAT/Tier-C per design §9 — it is not permission
to add dimensions or bins.

## Complexity Budget

- Max statistical test families: 3 (bootstrap CI on Δ; permutation tests — pairwise
  one-sided and omnibus, counted as one family; split-half stability check).
- Max visualisations: 5 (per-dimension bin-mean net with CIs × 3; split-half
  stability panel; qualification summary matrix).
- Max new code modules: 1 (covariate construction + characterisation orchestration;
  reuse the EXP-031 rebuild and the EXP-034 financing helper).

## Data Requirements

Join lifetime observations (`role = event`, `reportable_event = true`) to
`avwap_events.csv` on instrument/domain/regime_id/trigger index and pyramid flag —
the join must be 1:1 with zero unmatched events (hard assert; unmatched rows are a
data defect, not a filter). ATR(14) computed on the rebuilt domain series with the
standard true-range definition; the trailing percentile window advances by calendar
time, not bar count.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
# TRAIN = first 70% of rebuilt domain bars; TEST and holdout never read.
```

## Suggested Direction

Build one tidy per-event TRAIN frame (event id, domain, instrument, regime cluster,
c1, c2, c3, net_e) in a single pass, then run the §8.1 battery as pure functions of
that frame. The split-half check reuses the same frame with a time-median split per
domain. Keep the permutation strata identical to the bootstrap clustering so the
two inference legs agree on the dependence structure.
