# Experiment: EXP-071 — One-Shot TEST Confirmation of the Full G-015 Passing Cell Set

> **Freeze-before-TEST protocol (D0 P8, binding):** The file
> `python/experiments/EXP-071/frozen_selection.json` must be written and hash-pinned
> **before any TEST row is loaded**. It records the binding TEST family, any EXP-070
> FPR exclusions (none — all 6 P5 cells PASS), the EXP-070 temporal stability flags,
> the composition threshold (P9), and the inference-method hash (bootstrap seed,
> N_BOOT, block-length rule). No amendment to the TEST family after the freeze file
> is written.

## Hypothesis

**HYP-024 (registered, `docs/signal-registry/multiplicity-registry.md` Phase 016 batch):**

On the TEST stratum (next 21% of each instrument's chronologically ordered 1-minute file,
after the TRAIN slice) of the predeclared full `N-PARTIAL-V2A` G-015 passing cell set —
excluding EURUSD instrument-wide — the MA(20,50)-native `/STRONG-STAT`-conditioned HA harami,
under the `N-PARTIAL-V2A` exit rule, shows per-event **gross** ATR-normalised expectancy with:

1. `median CI_low > 0` (Holm-adjusted across the declared 6-cell family at α = 0.05),
2. `raw-mean CI_low > 0`, and
3. `beats-RM-native contrast CI_low > 0` (Holm-adjusted),

each binding cell's point estimate exceeding its EXP-070-derived calibrated margin,
composing at the predeclared threshold (≥ 3 cells, ≥ 2 instruments, ≥ 2 non-4h).

This is the **first counted TEST read** in the harami family's history.

## Question

**Gross:** On the TEST stratum of the 6-cell predeclared EXP-071 binding family
(GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h), does the
MA-native conditioned harami under `N-PARTIAL-V2A` meet the full composition threshold
(§Success / Failure Criteria), and does the equal-weight composite portfolio metric confirm
positive gross signal at the family level?

## Scope Boundaries

### Data Views

- **Real domain time bars** per cell, clock-aligned from 1-minute **TEST rows only**
  (rows `[train_cutoff, analysis_cutoff)` per instrument, strict 1-minute-row-timestamp
  boundary) via `xen.bar_aggregator`. Domain per cell: 5m (GBPUSD-5m), 1h (GBPUSD-1h,
  NZDUSD-1h), 2h (NZDUSD-2h), 30m (GBPJPY-30m), 4h (US2000-4h). Coverage convention:
  `min_coverage = 0.90` for ≥15m domains, 5m strict — inherited from EXP-068.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for harami **detection only** on
  TEST domain bars. No HA-price outcome metric is ever computed.
- **MA(20,50) segments on real `Close`** (substrate for move/direction/favourable-
  target/adaptive-cap geometry) and **`/STRONG-STAT`** recomputed on confirmed MA segments
  (native conditioning object). Warmup bars carry no MA-state; causal throughout.
- **P12 reconciliation (binding pre-flight):** before any TEST row enters an inference,
  reproduce EXP-061 `M0` / EXP-068 `BENCH`+`PARTIAL-V2A` / EXP-066 `PARTIAL-V2A` on
  TRAIN at 1e-9 per cell using the same frozen machinery (hard-fail on any mismatch).
- No new chart-type views, no new derived modules in `python/src/xen/`.

### Parameters (all frozen, none tuned)

- **MA(20,50) on real close** — fixed (D0 P1; Phase 015 ratified).
- **`/STRONG-STAT` native**: `m_sofar ≥ p75` of trailing-20 confirmed MA-segment magnitudes; causal.
- **3-barrier geometry:** favourable 50% of `M_sofar`; adverse 1:1 stop; MA-adaptive cap;
  P15 path-ordered intrabar fills (bullish: O→L→H→C; bearish: O→H→L→C).
- **Binding arm `N-PARTIAL-V2A`:** three exit legs at cumulative `{1/3, 2/3, 1}×fav_dist`
  with shared 1:1 adverse stop and MA-adaptive cap. V2A = first close past 50% of
  `M_sofar` takes 1/3 position; second at fav target takes 1/3; remainder at cap or stop.
- **Disclosed arm `N-V2A×ADV-NONE`:** same partial-exit with no adverse stop; MA cap is
  sole stop-out (`adv_count = 0`).
- **Disclosed signal-check `N-BENCH`:** single-leg benchmark (50%×M_sofar fav, 1:1 adv, MA cap).
- **`RM-native`** matched-random-on-MA null: same draw count as the signal arm per cell,
  drawn from the eligible MA-regime pool (causal, non-harami entries).
- **Bootstrap:** regime-clustered moving-block, `b = round(m^(1/3))`, `N_BOOT = 10_000`,
  deterministic per-`(instrument, domain)` seed (`BASE_SEED = 20260616`, EXP-068 convention).
- **Winsorized mean:** 10% symmetric (`TRIM_FRAC = 0.10`); point-estimate disclosed co-primary
  (D0 P4); same implementation as EXP-068 `_winsorized_mean`.
- **Holm adjustment:** across the 6-cell binding family at α = 0.05 (per-cell Holm-adjusted
  p-values; same two-sided convention as EXP-068).
- **Power floor:** ≥ 30 events per cell; cells below floor excluded from composition with record.
- **Composite seed (portfolio disclosure):** predeclared in `frozen_selection.json` as
  `[BASE_SEED, 999, "composite"]`; used for the portfolio-aggregate bootstrap only.

### Instruments and Cells (binding TEST family)

**Source:** EXP-070 CALIBRATION_DELIVERED (D0-amendment-004). All 6 predeclared P5 cells PASS
under the amended Null-A-only binding rule. No FPR-exclusion cells. Temporal stability flags
and calibrated margins (from EXP-070 Null-A Null-A calibration) carried forward:

| Cell | Instrument | Domain | Type | Null-A FPR | Temporal flag | Calibrated margin (ATR) |
| --- | --- | --- | --- | --- | --- | --- |
| GBPUSD-5m | GBPUSD | 5m | non-4h | 0.035 | GROWING | 0.0533 |
| GBPUSD-1h | GBPUSD | 1h | non-4h | 0.014 | DECAYING | 0.1263 |
| NZDUSD-1h | NZDUSD | 1h | non-4h | 0.031 | DECAYING | 0.1496 |
| NZDUSD-2h | NZDUSD | 2h | non-4h | 0.031 | STABLE | 0.1678 |
| GBPJPY-30m | GBPJPY | 30m | non-4h | 0.014 | DECAYING | 0.0722 |
| US2000-4h | US2000 | 4h | 4h | 0.018 | STABLE | 0.1614 |

**EURUSD excluded instrument-wide** (TEST-capped; holdout-contaminated via EXP-032).
**Hybrid object excluded** (CHARACTERISED_NOT_VIABLE; D0 P1). Objects never pooled.

### Time Range

- **TRAIN** (`[0, train_cutoff)` 1-minute rows per file) = first 49% — used only for P12
  reconciliation pre-flight and for constructing MA/STRONG-STAT/barrier warmup state that
  carries into the TEST slice (no TRAIN events enter binding TEST inference).
- **TEST** (`[train_cutoff, analysis_cutoff)` 1-minute rows per file) = next 21% — the
  binding stratum for all EXP-071 inferences. Loaded only after the freeze file (P8) is
  written and hash-pinned.
- **Global holdout** (`[analysis_cutoff, total)`) = final 30% — **never loaded, inspected,
  emitted, plotted, counted, or used in any capacity.**

Split boundary (per instrument):
```
analysis_cutoff = int(total_1m_rows * 0.7)
train_cutoff    = int(analysis_cutoff * 0.7)   # ≈ 49% of total
# TEST slice: [train_cutoff, analysis_cutoff)
# holdout:    [analysis_cutoff, total)   — NEVER LOADED
```

Domain bars are built from TEST 1-minute rows only; MA/STRONG-STAT/ATR state that requires
look-back beyond the TEST window must be seeded from TRAIN rows (TRAIN loaded for state
only — no TRAIN event enters composition).

### Global Holdout (mandatory exclusion)

The final 30% of each chronologically ordered source file is **never loaded**. The
`load_test_1m` helper (see §Data Requirements) enforces this at load time.

### Look-Ahead Bias Prevention

- MA segmentation, `/STRONG-STAT`, harami detection, and all barrier thresholds use only
  data available at or before each event's timestamp — causal, streaming-compatible
  (inherited from EXP-068; governance-clean).
- State seeded from TRAIN is carried forward in a single sequential pass into TEST; no
  TEST bar reaches back to a TRAIN bar's future information.
- The freeze file is written before any TEST row is loaded (P8); the matched-random draw
  seed per cell is predeclared in the freeze file, not derived from TEST results.

### Real-Price Outcome Discipline

- Every per-event return is a **direction-signed ATR-normalised real-price excursion**
  under the arm's exit rule. No metric is computed from HA prices.
- Barriers are evaluated on `RealOpen/RealHigh/RealLow/RealClose` (domain bars from real
  1-minute time bars). No costs, stops-as-P&L, slippage, sizing, or financing (gross only;
  costs enter EXP-072).

### Exclusions

- Any TRAIN event entering binding composition inference (TRAIN used only for state and P12).
- Any holdout or TEST row loaded before the freeze file is written and hash-pinned (P8 gate).
- Any EURUSD stratum, any domain or instrument outside the 6-cell binding family.
- The hybrid conditioning object.
- Cross-cell pooling in any binding per-cell statistic (per-cell unit); the equal-weight
  composite (P10) is a separate portfolio-disclosure object, not a per-cell replacement.
- Costs, cost-adjustment, or net metrics (gross only; D0 P12).
- Any sweep, parameter tuning, metric reselection, or grid extension after TEST results
  are seen. The TEST family is frozen in the freeze file.
- Percentage improvement against a zero baseline; all effects reported as ATR-unit
  differences with bootstrap CIs.
- Any TEST family amendment after the freeze file is hash-pinned without a dated
  D0-amendment and operator re-ratification.

## Success / Failure Criteria

### Per-Cell Composition Threshold (D0 P9)

A cell **clears the composition threshold** iff **all** of:
1. `median CI_low > 0` (Holm-adjusted across the 6-cell binding family, α = 0.05)
2. `raw-mean CI_low > 0`
3. `beats-RM-native contrast CI_low > 0` (Holm-adjusted across the binding family)
4. Binding-arm (`N-PARTIAL-V2A`) median point estimate > per-cell calibrated margin (ATR)
   from EXP-070 Null-A calibration (listed above)

### Experiment-Level Verdict (D0 P9)

- **`TEST_CONFIRMED`** (Evidence FOR): ≥ 3 binding cells clear the full composition threshold,
  spanning ≥ 2 instruments, of which ≥ 2 clearing cells are non-4h. No EXP-070 method
  defect in the binding cells (none: all 6 PASS).
  *Consequence:* CAND-001 advances; open EXP-072 and EXP-073 conditional on operator
  direction; record counted TEST reads in `test-read-ledger.md` in the same commit as results.

- **`TEST_INCONCLUSIVE`** (Inconclusive): the composite CI spans zero (power-limited; no
  systematic negative), or the cell count falls below the threshold with wide CIs.
  *Consequence:* record evidence; family stays OPEN; counted reads consumed; a targeted
  follow-up may be scoped separately.

- **`TEST_NOT_CONFIRMED`** (Evidence AGAINST): the predeclared family fails the composition
  threshold with `median CI_low ≤ 0` in the majority of binding cells (systematic negative,
  not power-limited).
  *Consequence:* CAND-001 retired on this scope; family stays OPEN; counted reads consumed.

**Shot rule:** counted reads are consumed regardless of verdict — the TEST contact is
one-shot and irrevocable per D0 P6 / design §8.

### Disclosures (non-binding, same data contact, P11)

The following are run alongside the binding arm and disclosed:
1. `N-V2A×ADV-NONE` per-cell results on the same TEST strata (not a gate input; MEAN_RECOVERABLE
   diagnostic — `winsorm+ ∧ mean−` cells are EXP-072 tail-filter candidates).
2. `N-BENCH` per-cell results on the same strata (signal-check anchor).
3. `RM-native` matched-random per-cell distribution on the TEST strata (attribution reference).
4. Per-cell 10% symmetric winsorized mean point estimates for both arms (D0 P4).
5. Per-cell EXP-070 temporal stability flags (carried from EXP-070 results; disclosed).
6. Per-cell EXP-070 Null-A conjunction FPR (carried from EXP-070 results; disclosed).
7. Null-B advisory FPR from EXP-070 (contextual; not a gate input; disclosed in freeze file).

**Yellow-flag note (D0 P4):** for `N-PARTIAL-V2A` (binding): a cell that is `median+` ∧
`beats-RM` ∧ `winsorm+` ∧ `raw-mean−` receives a **yellow-flag** note in results — the
raw-mean failure is more informative in a PARTIAL_RECOVERY cell and should be investigated.

### Portfolio Disclosure (D0 P10, non-binding, non-gating)

EXP-071 emits a gross equal-weight composite ATR-normalised expectancy CI across all 6
binding cells (pooling per-event returns equally across cells):
- Composite median and mean (raw and winsorized) with moving-block bootstrap CI
  (`b = round(m_total^(1/3))`, `N_BOOT = 10_000`, seed predeclared in freeze file as
  `[BASE_SEED, 999, "composite"]`).
- This metric is entered in `test-read-ledger.md` as a **disclosure** against all 6 member
  strata — not a counted read, not a gate condition.
- The portfolio disclosure informs G-016 and is the gross anchor for EXP-073.

## Complexity Budget

- **Max statistical tests: 4** — (1) regime-clustered moving-block bootstrap CI (median +
  raw-mean + winsorized mean); (2) two-sample `beats-RM-native` bootstrap contrast; (3) Holm
  adjustment across the binding family (α = 0.05); (4) per-cell margin check (deterministic
  quantile comparison against EXP-070 outputs — not a new statistical test). No additional
  inference layers.
- **Max visualisations: 5** — (1) per-cell median effect vs calibrated margin (forest-plot
  style, all 6 cells); (2) composition outcome heatmap (cell × arm × conjunction leg);
  (3) `beats-RM` contrast per cell with CI; (4) portfolio-aggregate composite CI; (5) winsorized
  mean diagnostic per cell (binding vs disclosed arm).
- **Max new code modules: 1** experiment-local module under `python/experiments/EXP-071/code/`
  (TEST-slice loading, freeze-file writing, arm resolution, composition classifier, portfolio
  aggregation). Reuse frozen EXP-068 inference machinery by import; no new or modified
  shared `python/src/xen/` module without explicit governance approval.

## Metric Denominators and Zero-Baseline Behavior

- **Per-cell denominator:** number of **reportable TEST events** per cell (qualifying harami
  entries with valid outcome window within TEST stratum; ≥ 30 event power floor; cells below
  floor excluded from composition with record and disclosed).
- **Portfolio composite denominator:** total reportable events pooled from all 6 binding cells.
- **`beats-RM` contrast denominator:** paired (signal_arm, matched_random_arm) return sets;
  the contrast is a matched excess (signal − matched-random) whose true null value is 0.
- **Zero-event handling:** a cell with fewer than 30 reportable TEST events is recorded as
  `below-floor`, excluded from the composition with explicit disposition — never NaN-propagated
  or silently counted.
- **No ratio or percentage improvement against a zero baseline anywhere.** All effects
  reported as ATR-unit differences with bootstrap CIs.

## Data Requirements

Hard dependency gates (fail fast if missing or inconsistent):
- `python/experiments/EXP-070/results/calibration_map.csv` — per-cell calibrated margins
  and FPR verdicts; verify all 6 P5 cells PASS (Null-A conjunction FPR ≤ 0.05) before
  proceeding.
- `python/experiments/EXP-070/results/temporal_stability.csv` — per-cell DECAYING/STABLE/GROWING
  flags; carried into the freeze file.
- `python/experiments/EXP-068/results/g015_verdict.json` — binding TEST family source;
  `native_per_arm["PARTIAL-V2A"]["g015_passes"]["cells"]` ex-EURUSD must equal exactly the
  6 P5 cells (assert set equality).
- `python/experiments/EXP-068/results/per_cell_expectancy.parquet`, `run_metadata.json`;
  `python/experiments/EXP-066/results/…`; `python/experiments/EXP-061/results/…` — P12
  reconciliation anchors (reproduce at 1e-9 before any TEST inference).
- EXP-068 `code/run_experiment.py` — the frozen `N-PARTIAL-V2A` / `N-V2A×ADV-NONE` /
  `N-BENCH` / `RM-native` / `_winsorized_mean` / bootstrap machinery, reused unchanged.
- 1-minute source files under `data/timebars/` for GBPUSD, NZDUSD, GBPJPY, US2000.

### Standard Loading Pattern (TEST-only, holdout- and TRAIN-safe for inference)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")

def load_test_1m(instrument: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return (train_1m, test_1m) slices; holdout never loaded."""
    path = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument}_*.parquet"))[-1]
    scan = pl.scan_parquet(path).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total * 0.7)          # first 70% = analysis set
    train_cutoff    = int(analysis_cutoff * 0.7) # first 70% of analysis = TRAIN (≈49%)
    # holdout = [analysis_cutoff, total)  — NEVER LOADED
    train_1m = scan.slice(0, train_cutoff).collect()
    test_1m  = scan.slice(train_cutoff, analysis_cutoff - train_cutoff).collect()
    return train_1m, test_1m
```

TRAIN is loaded for state carry-in (MA warmup, STRONG-STAT history, ATR) and for the P12
reconciliation pre-flight only. No TRAIN event enters a binding TEST inference.

### Expected Output Files

```text
python/experiments/EXP-071/
├── frozen_selection.json        ← written and hash-pinned BEFORE any TEST load (P8)
├── results/
│   ├── per_cell_results.csv     ← per cell × arm: median, mean, winsorm, CI bounds,
│   │                               beats_rm, composition verdict, margin_clear
│   ├── portfolio_results.csv    ← equal-weight composite: median/mean/winsorm CI + verdict
│   ├── composition_verdict.json ← TEST_CONFIRMED / TEST_INCONCLUSIVE / TEST_NOT_CONFIRMED
│   │                               + per-cell conjunction flags + clearing cell list
│   ├── test_read_manifest.csv   ← per stratum: instrument, domain, counted_reads_consumed
│   └── run_metadata.json        ← status, P12/fence/freeze gates, seeds, N_BOOT,
│                                   determinism hash, verdict, dependency gates
└── plots/                       ← ≤5 per budget
```

## Suggested Direction

Treat EXP-071 as **EXP-037/EXP-038** for the harami family — the final one-shot TEST confirmation
after a calibrated method (EXP-070) and a predeclared TEST family (D0 P5). The code reuses the
frozen EXP-068 `signal_arm` / `matched_random_arm` / `_summarize_arm` / `contrast` / bootstrap
pipeline unchanged in semantics; the only new logic is:
(a) the TEST-slice loader with TRAIN carry-in for state,
(b) the freeze-file writer (written before TEST is touched),
(c) the Holm-adjusted composition classifier (pure deterministic logic from the per-cell CIs),
(d) the equal-weight portfolio aggregator, and
(e) the TEST-read manifest emitter (inputs for ledger update).

The four DECAYING cells (GBPUSD-1h, NZDUSD-1h, GBPJPY-30m) are noted; their decay was measured
on TRAIN and is disclosed context for interpreting the TEST verdict, not a pre-exclusion criterion.
GBPUSD-5m is GROWING; NZDUSD-2h and US2000-4h are STABLE. The composition threshold (≥3/≥2/≥2-non-4h)
does not require all cells to clear — a partial confirmation is valid as long as the conjunction
and instrument thresholds are met.

The freeze file must be written atomically (to a `.tmp` file, then renamed) with its SHA-256
hash appended, before `load_test_1m` is called for any instrument. This is the P8 contract.
