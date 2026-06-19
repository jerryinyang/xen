# Experiment: EXP-070 — Event-Level Method Calibration (EXP-027-Analog, TRAIN-only)

> **Amended 2026-06-18 (D0-amendment-003).** After the first run returned `METHOD_DEFECT`
> on the median-leg FPR object, the operator directed an amendment: the **binding FPR
> object is now the full conjunction** (`median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-RM
> CI_low>0`) — the exact P4/P9 EXP-071 cell-acceptance event — and the **Null B `beats-RM`
> arm is symmetrized**. The median-leg FPR is retained as a **disclosed, non-binding**
> diagnostic. All numeric thresholds (α₀=0.05, 0.06 tolerance, >2/3 defect rule) are
> unchanged; only the object they apply to changes. See
> `docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-003-binding-fpr-object-and-symmetric-null-b.md`.
> First-run artifacts are archived under `results_v1/` (the `METHOD_DEFECT` record is preserved).

> **Amended 2026-06-18 (D0-amendment-004).** After the second run (post amendment-003)
> returned `METHOD_DEFECT` with Null-B conjunction FPRs inflated in 5 of 6 cells
> (0.161–0.773) despite Null-A conjunction FPRs all ≤ 0.035, an investigation established
> the inflation is a **structural geometry artifact** — STRONG-STAT conditioning creates a
> systematic barrier-geometry advantage that block rotation cannot remove (the geometry
> is a property of the entry point, not the forward path). The operator directed
> **Option 3**: **Null-A (matched-random placement) is the sole binding null** for FPR
> control. Null-B is demoted to an **advisory contextual diagnostic** — still computed and
> reported, but not a gating condition. All thresholds (α₀=0.05, 0.06 tolerance, >2/3
> defect rule) are unchanged; they now apply to Null-A only. **No re-run.** Under this
> amendment all six cells pass Null-A FPR control; verdict is **CALIBRATION_DELIVERED**.
> See `docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-004-null-b-demoted-to-advisory.md`.

## Hypothesis

The frozen Phase 015 / EXP-068 event-level inference machinery — per-event **gross**
ATR-normalised expectancy under the **`N-PARTIAL-V2A`** arm on **MA(20,50)-native
`/STRONG-STAT`-conditioned HA harami** events, with a regime-clustered moving-block
bootstrap CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`, deterministic per-`(instrument,
domain)` seed), the raw-mean co-primary CI, the `beats-RM-native` median contrast, and
Holm adjustment across the declared family — **applied per cell** on the six predeclared
Phase 016 D0 P5 TEST-family cells, exhibits:

1. **controlled per-cell false-positive rate** (empirical FPR ≤ α₀ = 0.05 on the
   **binding full conjunction** `median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-RM CI_low>0`
   — the P4/P9 cell-acceptance event; D0-amendment-003 — under **two
   structurally-different** matched-structure null generators; the median-leg FPR is
   reported as a disclosed, non-binding diagnostic), and
2. **finite recovery** — a non-degenerate bootstrap CI width **and** a finite per-cell
   planted-edge MDE at TPR ≥ 0.80, and
3. **deterministic byte-identical replay**,

at each cell's realized TRAIN event count, **using TRAIN rows only and reading zero TEST
or holdout rows**. Cells where all three hold are eligible to enter the binding EXP-071
TEST family; cells where FPR control fails are excluded from that family with record.

This is a **methodology / calibration experiment** (`CF-HA-HARAMI-001` Phase 016,
EXP-027-analog; HYP-023, registered in `docs/signal-registry/multiplicity-registry.md`
Phase 016 batch). It consumes **0 candidate-screening slots and 0 TEST reads**. It must
PASS before any TEST contact (EXP-071) is authorised (Phase 016 design §5; D0 P7/P8).

## Question

For each of the six predeclared P5 TEST-family cells — **GBPUSD-5m, GBPUSD-1h,
NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h** (ex-EURUSD) — does the **unchanged**
EXP-068 `N-PARTIAL-V2A` event-level inference, evaluated **standalone per cell** on the
MA-native conditioned-harami event population at that cell's realized TRAIN event count,
control FPR (under two distinct nulls), retain finite power (non-degenerate CI + finite
planted-edge MDE), replay deterministically, and what is each cell's temporal-stability
classification on a TRAIN-only walk-forward — so that EXP-071's first-ever harami TEST
read rests on a measured per-cell operating-characteristic map rather than on the
Phase 015 viability counts, which were never error-controlled on this exact population?

## Scope Boundaries

- **Data Views**:
  - Real domain time bars per cell, clock-aligned from 1-minute TRAIN rows via
    `xen.bar_aggregator` — domain set by the cell (5m, 30m, 1h, 2h, 4h; `min_coverage =
    0.90` for ≥15m domains, 5m strict — the EXP-048/EXP-068 construction convention).
  - **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for harami **detection only**.
  - **MA(20,50) segments on real `Close`** (substrate for move/direction/favourable-
    target/adaptive-cap geometry) and **`/STRONG-STAT`** recomputed on confirmed MA
    segments (native conditioning object). No HA-price outcome is ever computed.
  - No new chart-type views; no real-event registry/screening verdict is produced (this
    is calibration, not a candidate screen).
- **Parameters** (all **inherited and frozen** from Phase 016 D0 / EXP-068 — none tuned):
  - MA(20,50) on real close — fixed, not swept (D0 P1).
  - `/STRONG-STAT` native: magnitude-so-far ≥ p75 of trailing-20 confirmed MA-segment
    magnitudes; causal.
  - 3-barrier geometry: favourable 50% of `M_sofar`; adverse 1:1 stop; MA-adaptive cap;
    P15 path-ordered intrabar fills.
  - Arm: `N-PARTIAL-V2A` (3-leg `{1/3, 2/3, 1}×fav_dist`; shared 1:1 adverse stop; MA
    cap) — the binding lead arm. `RM-native` is the matched-random-on-MA null for the
    `beats-RM` contrast.
  - Inference: regime-clustered moving-block bootstrap, `b = round(m^(1/3))`,
    `N_BOOT = 10_000`, deterministic per-`(instrument, domain)` seed (`BASE_SEED =
    20260616`, EXP-068 convention); raw-mean co-primary; 10% symmetric winsorized mean
    (`TRIM_FRAC = 0.10`, point-estimate disclosed co-primary, D0 P4); Holm across the
    declared family at α = 0.05.
  - FPR operating point α₀ = 0.05 (secondary {0.10, 0.01} reporting permitted within
    budget); power floor ≥ 30 reportable events per cell (D0 P3).
  - Walk-forward temporal-stability diagnostic (D0 P7 Leg 4): rolling **6-month** window
    on the TRAIN timeline, step = 1 window, TRAIN rows only.
  - Draw counts, bootstrap-batching, planted-edge bps grid, and the two null generators'
    exact construction are **fixed in Stage 2 before any measurement** (precision targets
    below).
- **Instruments / cells**: exactly the **six** frozen P5 cells — GBPUSD-5m, GBPUSD-1h,
  NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h. No other instrument, domain, or cell is
  calibrated. (EURUSD is TEST-capped instrument-wide and excluded; D0 P1/P5.)
- **Time range**: **TRAIN stratum only** — the first 49% of each instrument's
  chronologically ordered 1-minute file (= first 70% of the first-70% analysis slice),
  strict 1-minute-row-timestamp boundary per file (D0 P8/§9 guardrails). Domain bars are
  built from TRAIN 1-minute rows only.
- **Global holdout (mandatory exclusion)**: the final 30% of each chronologically ordered
  source file is never loaded, inspected, emitted, plotted, counted, or used in any
  capacity.
- **TEST stratum (mandatory exclusion for EXP-070)**: the next 21% (TEST) is **never
  loaded**. EXP-070 is TRAIN-only and incurs **0 counted TEST reads**; the six P5 strata
  remain at **0 counted reads** (current tally per `docs/signal-registry/test-read-ledger.md`,
  verified 2026-06-18) and stay there until EXP-071.
- **Look-ahead bias prevention**: MA segmentation, `/STRONG-STAT`, harami detection, and
  all barrier thresholds use only data available at or before each event's timestamp
  (causal, streaming-compatible — inherited from EXP-068, which is governance-clean on
  this axis). Planted-edge drift (TPR leg) is added to event **outcomes only**, never to
  event placement or matched-control selection.
- **Real-price outcome discipline**: every per-event return is a direction-signed
  ATR-normalised real-price excursion under the arm's exit rule. **No metric is computed
  from HA prices.** No costs, stops-as-P&L, slippage, sizing, or financing (gross
  calibration, not strategy P&L).
- **Exclusions**:
  - any TEST or holdout 1-minute row;
  - any real-event candidate-screening verdict or registry disposition (EXP-070 produces
    a calibration map, not a screen — the screen is EXP-071);
  - the cost model (gross only, D0 P12) — costs are an EXP-072 object;
  - EURUSD (any domain);
  - the **hybrid** conditioning object (CHARACTERISED_NOT_VIABLE; native only, D0 P1);
  - cross-instrument pooling or cross-cell aggregation in any **binding** per-cell
    calibration statistic (per-cell unit; an equal-weight composite is a separate
    EXP-071 disclosure, not part of EXP-070);
  - any sweep, parameter tuning, metric reselection, or grid extension after results are
    seen (a failed calibration is a valid result, not license to re-pick the method);
  - percentage improvement against a zero baseline.

## Success / Failure Criteria

**Precision thresholds** (EXP-003/005/027/044 precedent): a cell's calibration is usable
only if the FPR Wilson 95% half-width ≤ 0.03 and the TPR Wilson 95% half-width ≤ 0.05 at
the budgeted draw counts. Cells failing precision are reported `CALIBRATION_UNDERPOWERED`
and excluded from PASS/EXCLUDE claims pending an operator precision-only re-run decision
(draw-count increase only; no object change).

**Per-cell verdicts:**

- **PASS (calibration-clean; eligible for the binding EXP-071 family)** — all hold:
  - empirical per-cell **conjunction-FPR** ≤ α₀ = 0.05 on the binding **full conjunction**
    (`median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-RM CI_low>0`; D0-amendment-003) under
    **both** null generators (Wilson precision met); **and**
  - a **non-degenerate** bootstrap CI width (D0 P7 Leg 2); **and**
  - a **finite per-cell planted-edge MDE** at TPR ≥ 0.80 on the predeclared bps grid
    (operator-elected power-context diagnostic, additive to D0 Leg 2).
- **FPR_EXCLUDED (excluded from the binding family with record)** — **conjunction-FPR**
  exceeds 0.06 (α₀ + 0.01 tolerance, D0 P7 Leg 1 / amendment-003) in an adequately powered
  cell under **either** null; the exclusion is recorded and disclosed in EXP-071's freeze
  file (D0 P8). (The disclosed median-leg FPR is reported alongside but does not exclude.)
- **MDE_UNRESOLVED** — FPR controlled but no finite planted-edge MDE exists on the
  predeclared grid at TPR ≥ 0.80 (a disclosed power limitation; the cell may still satisfy
  the lighter D0 Leg-2 finite-CI requirement — its disposition for the binding family is
  flagged for the EXP-071 freeze decision, not silently dropped).
- **CALIBRATION_UNDERPOWERED** — precision thresholds unmet at budgeted draw counts.

**Temporal-stability flag (disclosed, non-excluding; D0 P7 Leg 4):** each cell is
classified `DECAYING` / `STABLE` / `GROWING` from the TRAIN-only walk-forward
(`DECAYING` iff the final-window point estimate is > 1 bootstrap SE below the full-TRAIN
point estimate). `DECAYING` is a disclosed flag carried into the EXP-071 D0; it does
**not** exclude a cell on this ground alone.

**Experiment-level outcomes:**

- **Evidence FOR — `CALIBRATION_DELIVERED`**: the six-cell map is produced with every
  cell classified, the per-cell MDE table recorded, every cell's temporal-stability flag
  assigned, the P12 reconciliation passing (reproduce EXP-061 `M0` / EXP-068
  `BENCH`+`PARTIAL-V2A` / EXP-066 `PARTIAL-V2A` at 1e-9), and the determinism replay
  byte-identical. (Deliverable criterion — the experiment succeeds by producing the
  honest map, however many cells PASS.)
- **Evidence AGAINST — `METHOD_DEFECT`** (gate-blocking, D0 P7 / design §7): **binding
  conjunction-FPR** control fails in **> 2/3 of the six declared cells** (i.e. ≥ 5 cells
  exceed conjunction-FPR 0.06 under either null; D0-amendment-003), **or** any retained
  cell has a degenerate (zero-width) CI, **or** the determinism replay is not
  byte-identical. Consequence: **fix the calibration and re-run EXP-070 before any TEST
  contact**; does not consume counted reads (design §7 METHOD_DEFECT row).
- **Inconclusive**: the map is produced but a material fraction (> 1/3, i.e. ≥ 3) of the
  six cells is `CALIBRATION_UNDERPOWERED`, leaving the binding-family membership undecidable
  at budgeted precision. Consequence: operator decides a precision-only re-run vs.
  accepting a reduced binding family for EXP-071.

Expected (honest prior, not a target): the single 4h cell (US2000-4h) and any thin
non-4h cell may carry a large finite MDE or fail recovery — that is exactly the power
information the EXP-071 freeze decision needs; an `MDE_UNRESOLVED` 4h tail is a valid,
informative outcome, not a calibration defect.

## Complexity Budget

- **Max statistical tests: 4** — (1) regime-clustered moving-block bootstrap CI (median +
  raw-mean); (2) the `beats-RM-native` contrast under the same bootstrap; (3) Wilson
  FPR/TPR intervals; (4) grid-defined per-cell planted-edge MDE determination. No Holm
  *inside* the FPR/MDE calibration (the declared-family Holm at α=0.05 is reproduced as
  the inference-under-test, consistent with EXP-068, not added as a new test).
- **Max visualisations: 5** — (1) per-cell FPR map (6 cells × 2 nulls, with Wilson
  bounds); (2) per-cell planted-edge MDE vs realized TRAIN event count; (3) TRAIN-only
  walk-forward temporal-stability panel; (4) CI-width / calibration-precision diagnostic;
  (5) coverage-verdict summary.
- **Max new code modules: 1** experiment-local helper under
  `python/experiments/EXP-070/code/` (per-cell matched-structure null + planted-edge
  substrate + per-cell inference wrapper). **Reuse of EXP-068 / EXP-066 / EXP-061 code by
  import or copy is preferred**; **no new or modified shared `python/src/xen/` module**
  without explicit governance approval.

## Metric Denominators and Zero-Baseline Behavior

- **Per-cell FPR denominator**: number of completed null draws for that
  cell × generator × α (predeclared count, fixed in Stage 2; draws failing the
  reportability/event-floor rule are recorded against a draw-completion floor, never
  silently dropped).
- **Per-cell TPR denominator**: number of completed planted-edge draws for that
  cell × edge × α.
- **Per-event expectancy denominator within a draw**: number of **reportable matched
  events** (valid outcome window, ≥ 30-event power floor, matched-random control
  available) — **never a bar count**.
- **Null per-event expectancy = exactly 0** (ATR-normalised). The `beats-RM` contrast is
  measured against the `RM-native` distribution (a non-zero matched-random control), not
  against zero. All effects are reported as ATR-unit / bps differences with CIs; **no
  ratio or percentage improvement against a zero or near-zero baseline anywhere.**
- **Zero-event handling**: a cell or draw with fewer than 30 reportable events is recorded
  as below-floor with a finite, explicit disposition (excluded from the binding
  conjunction-FPR numerator/denominator, counted in the draw-completion accounting) — never
  NaN-propagated and never counted as a silent zero.

## Data Requirements

Read-only upstream artifacts (hard dependency gates — fail fast if missing or inconsistent):

- `python/experiments/EXP-068/results/g015_verdict.json` — the P5 cell membership source
  (`native_per_arm["PARTIAL-V2A"]["g015_passes"]["cells"]`, ex-EURUSD); verified to equal
  the six frozen P5 cells before any computation.
- `python/experiments/EXP-068/results/per_cell_expectancy.parquet` and
  `run_metadata.json`, `python/experiments/EXP-066/results/…` and
  `python/experiments/EXP-061/results/…` — the **P12 reconciliation anchors** (reproduce
  EXP-061 `M0` / EXP-068 `BENCH`+`PARTIAL-V2A` / EXP-066 `PARTIAL-V2A` at 1e-9 before any
  new result is reported; D0 P1).
- EXP-068 `code/run_experiment.py` — the frozen `N-PARTIAL-V2A` / `RM-native` /
  winsorized-mean / bootstrap machinery, reused unchanged in semantics.
- 1-minute source files under `data/timebars/` for the four P5 instruments (GBPUSD,
  NZDUSD, GBPJPY, US2000), **TRAIN-sliced (first 49%) before any domain-bar construction.**

### Standard Loading Pattern (TRAIN-only, holdout- and TEST-safe)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")

def load_train_1m(instrument: str) -> pl.DataFrame:
    path = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument}_*.parquet"))[-1]
    scan = pl.scan_parquet(path).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total * 0.7)          # first 70% = analysis set
    train_cutoff = int(analysis_cutoff * 0.7)   # first 70% of analysis = TRAIN (≈49%)
    # TEST = [train_cutoff, analysis_cutoff)  — NOT loaded by EXP-070
    # holdout = [analysis_cutoff, total)       — NEVER loaded
    return scan.slice(0, train_cutoff).collect()
```

### Expected Output Files

```text
python/experiments/EXP-070/results/
- calibration_map.csv     # per-cell verdict: PASS / FPR_EXCLUDED / MDE_UNRESOLVED / CALIBRATION_UNDERPOWERED + reasons
- fpr_per_cell.csv        # FPR by cell × null generator × alpha, with Wilson bounds
- tpr_mde_per_cell.csv    # TPR by cell × planted edge; per-cell planted-edge MDE @ TPR≥0.80
- ci_width_per_cell.csv   # bootstrap CI width (median + raw-mean) per cell — Leg-2 finite check
- temporal_stability.csv  # per-cell walk-forward point estimates + DECAYING/STABLE/GROWING flag
- reconciliation.csv      # P12: EXP-061 M0 / EXP-068 BENCH+PARTIAL-V2A / EXP-066 PARTIAL-V2A @1e-9
- run_metadata.json       # status, determinism hash, dependency gates, seeds, draw counts
python/experiments/EXP-070/plots/   # ≤5 per the budget
```

## Suggested Direction

Treat EXP-070 as **EXP-027/EXP-044 re-run at the per-cell unit, on the MA-native
`N-PARTIAL-V2A` harami population, over the six frozen P5 cells** — same
nulls-on-real-scaffold construction, same frozen decision rule, with the EXP-068 arm
machinery reused unchanged and the event count set to each cell's realized TRAIN
population. Two structurally-different nulls (operator-elected) bound the FPR claim so a
pass is not an artifact of one null's construction; the additional planted-edge MDE curve
(operator-elected) supplies each cell's detectable-effect power context **before** EXP-071
spends its counted TEST read. The binding question is where per-cell inference stops
controlling error or recovering signal across the six cells — especially the single 4h
cell (US2000-4h) and the thin non-4h cells — and the resulting FPR + MDE + temporal-
stability map is simultaneously the D0 P7 gate verdict, the EXP-071 binding-family
membership input, and the EXP-071 power context. Computational tractability (6 cells × 2
nulls × draws × `N_BOOT`) is a Stage 2/3 design problem: prefer vectorized draw batching
over cutting draw counts below the precision thresholds.
