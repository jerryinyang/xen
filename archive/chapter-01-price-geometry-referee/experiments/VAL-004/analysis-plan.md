# Analysis Plan: Experiment VAL-004

15m/30m Domain Temporal-Integrity Validation (Phase 014 [VAL] gate).

## Objective

Determine whether the **15m and 30m** clock-aligned OHLC domains, constructed by
`xen.bar_aggregator.aggregate_ohlc` from the first-70% analysis slice of each
chronologically ordered 1-minute base file in **both** strict (`min_coverage=None`)
and tolerant (`min_coverage=0.90`) modes, preserve temporal alignment and
row-level no-look-ahead guarantees across the time-bar, timeframe, and chart-type
views — for **all 17** VAL-003-admitted instruments — and disclose the per-cell
dropped-window fraction under tolerant retention. This is the Phase 014 design §5
construction gate: a 15m/30m instrument×domain cell is admissible to EXP-048 only
on a VAL PASS for that cell.

This is a VAL-series rerun of **VAL-001 (rev. 3)**. The check logic, probe bounds,
negative-control catalogue, chart parameters, and pass/fail semantics are reused
**byte-for-byte** from the approved VAL-001 rev. 3 harness. The only changes,
exactly as authorized in `scope.md`, are:

1. **Timeframe set** `SOURCE_TIMEFRAMES = [15, 30]` — `30` is new; `15` strict is
   re-run purely as a **determinism reconfirmation anchor** against the
   VAL-001/VAL-003 record.
2. **Tolerant-mode pass** for periods {15, 30} at `min_coverage=0.90`, with the
   `SourceBars` valid-range parameterization and a per-cell dropped-window-fraction
   disclosure.

No statistical test, strategy P&L, signal, or edge claim is in scope. The final
30% global holdout is sealed at first touch and never inspected.

## Definitions: cells, modes, and the mode matrix

- A **cell** is one `instrument × domain × mode` triple. Domains are {15m, 30m};
  modes are {strict, tolerant}. 17 instruments × 2 domains × 2 modes = **68
  aggregated cells**, each running the full integrity + chart-view battery.
- The 1-minute base frame is loaded once per instrument and base-integrity-checked
  as a **sanity anchor** (it is the unavoidable load + holdout-slice step); it is
  **not** a new claim and period 1 is not in the resample loop.
- Negative controls and golden fixtures are **suite-level** (run once on synthetic
  inputs), not per-cell.

| Domain | strict (`min_coverage=None`) | tolerant (`min_coverage=0.90`) |
|---|---|---|
| **15m** | **Determinism anchor** — full battery; must reconcile to VAL-001 (4 core) / VAL-003 (13 new) `15m` record. | New tolerant claim + dropped-fraction disclosure. |
| **30m** | New strict claim — full battery. | New tolerant claim + dropped-fraction disclosure. |

**`source_timeframe` label convention (preserves the 9-column ValidationCheck
schema; encodes the mode without a new column):**

| Cell | `source_timeframe` token |
|---|---|
| 15m strict | `15m`  *(literal match to VAL-001/VAL-003 — the anchor)* |
| 15m tolerant | `15m@0.90` |
| 30m strict | `30m` |
| 30m tolerant | `30m@0.90` |

Using the literal `15m` token for 15m strict makes the determinism-anchor
reconciliation a direct per-row string match against the prior record.

## The tolerant-mode parameterization (the one substantive change)

Under `min_coverage=0.90`, `aggregate_ohlc` retains a clock-aligned window iff
`SourceBars >= floor`, where `floor = max(2, ceil(0.90 * period_minutes))`, and
`SourceBars` can never exceed `period_minutes`. Therefore:

- **15m:** `floor = max(2, ceil(13.5)) = 14` → valid `SourceBars ∈ [14, 15]`.
- **30m:** `floor = max(2, ceil(27.0)) = 27` → valid `SourceBars ∈ [27, 30]`.

Two existing artifacts must track this range so the tolerant pass tests the same
function the tolerant generator computes, not a different one:

1. **Independent oracle retention predicate.** VAL-001's `independent_resample_oracle`
   (pandas right-closed/right-labelled resample) drops any window with
   `SourceBars != period_minutes`. Reused verbatim in tolerant mode it would report
   `rows_only_in_production` for **every** legitimately-retained partial window — a
   false FAIL. The oracle must be parameterized by `min_coverage` and apply the
   **same** retention predicate (`SourceBars >= floor`) as the generator. OHLC
   values are still direct source selections (first/max/min/last), so equality on
   matched windows stays **exact**, and the oracle stays an *independent*
   reimplementation (pandas vs the Polars epoch-bucket production path).

2. **Output-side `SourceBars` check predicate.** `resample_output_failures`'
   `wrong_sourcebars` count is parameterized by mode:
   - **strict:** `SourceBars != period_minutes` (byte-identical to VAL-001).
   - **tolerant:** `(SourceBars < floor) | (SourceBars > period_minutes)`.

**Binding implementation rule:** `floor` is computed with the **same expression**
`max(2, math.ceil(min_coverage * period_minutes))` used inside `aggregate_ohlc`,
not a hardcoded literal — so the check range can never drift from the generator's
retention rule. The developer asserts the derived floors equal the documented
`[14, 15]` / `[27, 30]` as a guard. No other check logic changes in either mode.

## Methodology

### Step 1: Universe enforcement, holdout-safe inventory, 1m base sanity anchor

- **Universe enforcement (first)**: `reconcile_universe` maps the files present to
  the scoped 17 `EXPECTED_INSTRUMENTS` by filename inference. Each expected
  instrument must map to exactly one file — missing or duplicate ⇒ a FAIL check
  (mirroring the VAL-003 duplicate-file resolution); files inferred outside the set
  are disclosed (`universe_unexpected_files_disclosed`, non-failing) and **not
  processed**. After load, two guards confirm content: `loaded_symbol_matches_filename`
  and `instrument_not_duplicated` (no two processed files share a `Symbol`). The
  reconciliation is recorded in `run_metadata.json` (`instrument_universe`,
  `processed_files`). This prevents a PASS-like run over a missing, duplicated, or
  pre-sliced instrument set.
- **Method**: Reuse `load_analysis_data` verbatim — lazy Polars scan, sort by
  `CloseTime`, read schema + total row count (metadata only), collect only the first
  `int(total_rows * 0.7)` rows; the final 30% row contents are never collected.
  Record total/analysis/train/test counts and analysis-set timestamp boundaries. Run
  `base_timebar_failures` (null/non-increasing/duplicate `CloseTime`, OHLC bounds,
  null OHLC) on the 1m frame as a sanity anchor.
- **Why**: Architectural integrity is a deterministic property; an inventory plus
  rule-based base checks suffice. The holdout slice is enforced at the single load
  point, re-asserted in code and re-checked in audit.
- **Simpler alternative considered**: Skipping the 1m base checks since VAL-003
  validated base integrity. Rejected — the load happens anyway and re-anchoring the
  base frame is free insurance that the 15m/30m inputs are clean.
- **Assumptions**: One completed 1-minute OHLC bar per row, ordered by `CloseTime`.
  No stationarity/normality/i.i.d. assumption.
- **Expected output**: `analysis_slice_loaded`, `single_symbol_per_file`, and the
  five base-timebar rows per instrument in `validation_checks.csv` (`source_timeframe="1m"`).

### Step 2: Strict-mode timeframe integrity for 15m and 30m

- **Method**: For each instrument, construct `aggregate_ohlc(frame, P)` for
  `P ∈ {15, 30}` (strict). Run the unchanged `validate_timeframe` battery:
  `resample_matches_independent_oracle` (strict oracle, retention `SourceBars==P`),
  `resample_no_future_timestamp`, `resample_strict_sourcebars` (`SourceBars==P`),
  `resample_close_time_unique`.
- **Why**: 30m is a brand-new period; 15m strict is the reconfirmation anchor. The
  independent pandas oracle catches any clock-grid or OHLC-selection error.
- **Simpler alternative considered**: Trusting `aggregate_ohlc` because 15m passed
  before. Rejected — period 30 was never validated and the harness changed.
- **Assumptions**: 30 divides the 1440-minute day evenly (1440/30 = 48), so the
  pandas day-origin grid and the production `(epoch_s - 1) // (P*60)` grid coincide
  — the same divisibility property VAL-001 relied on for 15 and 60. Confirmed by the
  30m golden fixture (Step 6) and expected zero oracle disagreement on clean data.
- **Expected output**: four `timeframe`-view rows per instrument for each of `15m`
  and `30m`.

### Step 3: Tolerant-mode timeframe integrity + dropped-window-fraction (15m, 30m)

- **Method**: For each instrument, construct `aggregate_ohlc(frame, P, min_coverage=0.90)`
  for `P ∈ {15, 30}`. Run the same four `validate_timeframe` checks **with the
  tolerant parameterization** (Step "tolerant-mode parameterization"): the
  `min_coverage=0.90` oracle and the `SourceBars ∈ [floor, P]` range predicate.
  Additionally compute the per-cell dropped-window fraction (new helper, Step 5).
- **Why**: This is the construction mode Phase 014 consumes. The tolerant oracle +
  range check confirm partial-window retention is correct (legitimate partials
  retained, out-of-range `SourceBars` rejected), and the dropped fraction quantifies
  coverage loss.
- **Simpler alternative considered**: Reusing the strict checks unchanged in
  tolerant mode. Rejected — it would falsely FAIL every retained partial window
  (documented in `scope.md`).
- **Assumptions**: Tolerant retention understates window High/Low for partial
  windows; this is a known coverage/feature trade-off, not an integrity violation,
  and is disclosed, not corrected.
- **Expected output**: four `timeframe`-view rows per instrument for each of
  `15m@0.90` and `30m@0.90`, plus one `coverage_map.csv` row per (instrument, domain).

### Step 4: Chart-type alignment, look-ahead, determinism over the new domains

- **Method**: For each of the 68 cells, generate Heiken Ashi, Line Break (`level=3`),
  and Renko (`atr_period=14`) from that cell's aggregated frame and run the
  unchanged `validate_chart_view` battery: schema, timestamp alignment
  (`SourceCloseTime`/`CloseTime` mapping, no-future, close==source, source-count
  rules; HA real-price preservation + row-count + source-count==1), prefix-stability
  at head/middle/tail (`PREFIX_FRACTIONS = (0.34, 0.67, 0.95)`), and deterministic
  regeneration. Record event-density denominators.
- **Why**: Cross-view alignment is the binding cross-domain contract; prefix
  stability is the operational definition of no-look-ahead (more future data must
  not change earlier emitted rows); determinism guards reproducibility. These run
  identically to VAL-001 — the only difference is the source frame is a 15m/30m
  aggregation (strict or tolerant) rather than 1m/15m/60m.
- **Simpler alternative considered**: Position-based (bar-index) chart-to-source
  comparison. Rejected — sparse charts emit different counts and multiple rows at one
  `SourceCloseTime`; alignment must be by timestamp.
- **Assumptions / bounds**: 15m/30m analysis frames (≈23k–60k rows) are far below
  `PREFIX_WINDOW_ROWS = 150_000`, so `positioned_windows` returns a single `full`
  window and prefix stability still compares 3 genuine cuts. Determinism uses the
  head `DETERMINISM_ROWS = 50_000`. Generators are deterministic/streaming, so
  output is independent of how the source frame was constructed.
- **Real-price discipline**: HA `RealOpen/High/Low/Close` are validated to equal the
  aggregated bar's OHLC at the same `CloseTime`; no synthetic chart price is used for
  any outcome. No returns/P&L computed.
- **Expected output**: per-cell `chart_schema_expected`, alignment, three
  `no_lookahead_prefix_stability_{head,middle,tail}` (or `_full`), and
  `deterministic_regeneration` rows; density rows in `chart_view_summary.csv`.

### Step 5: Dropped-window-fraction metric (tolerant coverage disclosure)

- **Method**: New bounded helper `dropped_window_fraction(source_1m, P, min_coverage=0.90)`.
  Bucket the 1m analysis frame on the **same** grid expression the generator uses
  (`(CloseTime.epoch("s") - 1) // (P*60)`); `candidate_windows` = number of distinct
  buckets (every bucket holds ≥1 source bar by construction); `retained_windows` =
  the tolerant aggregated row count; `dropped_windows = candidate_windows -
  retained_windows`; `dropped_fraction = dropped_windows / candidate_windows`. Also
  report the strict dropped fraction (`SourceBars==P` retained) for context.
- **Why**: This is the Phase 014 §5 coverage disclosure and the admission lever. It
  is computed in **window** units (not the bar units of `coverage_summary`), so a new
  helper is required.
- **Denominator / zero-baseline (binding)**: `candidate_windows` is the denominator.
  A cell with **zero** candidate windows (degenerate/empty slice) is **INCONCLUSIVE**,
  never reported as `0/0` or a silent 0.0.
- **Admission rule (mirrors the JP225-2h convention, EXP-043)**:
  - `dropped_fraction ≤ 0.25` and all integrity checks PASS → **ADMITTED** (PASS).
  - `dropped_fraction > 0.25`, integrity checks otherwise PASS → **COVERAGE_EXCLUDED**:
    a **recorded exclusion**, the cell is blocked from Phase 014 admission, but this
    is **not** a suite FAIL and **not** an integrity failure.
  - `candidate_windows == 0` → **INCONCLUSIVE** (cell deferred, recorded).
- **Expected output**: `coverage_map.csv` (one row per instrument × {15m, 30m}) with
  `candidate_windows, retained_windows, dropped_windows, dropped_fraction_tolerant,
  dropped_fraction_strict, admission_status`.

### Step 6: Detection-power controls (golden fixtures + negative controls)

- **Method**: Reuse `run_negative_controls` and `validate_resample_golden` from
  VAL-001 unchanged, with two faithful extensions tied strictly to the two scoped
  changes:
  1. **30m strict golden fixture** — hand-anchored first-window equality
     (`aggregate_ohlc(synthetic_source(60), 30).row(0)` vs a plain-Python 30-bar
     window). Mirrors the existing 15m fixture for the new period.
  2. **Tolerant `SourceBars`-range controls** — exercise the new range predicate's
     **lower** boundary that strict mode lacks:
     - inject a retained window with `SourceBars = floor - 1` (13 for 15m / 26 for
       30m) and require the tolerant range check to **flag** it (below-floor);
     - confirm the existing above-`P` injection (`SourceBars = 99`) is flagged under
       the tolerant predicate too (`99 > P`);
     - **must-not-overfire assertion**: a legitimate in-range partial
       (`SourceBars = floor`, i.e. 14 for 15m / 27 for 30m) is **PASSED** by the
       tolerant range check — the precise failure the tolerant change exists to
       prevent.
- **Why**: rev. 3's binding principle is that **every** data-integrity/alignment
  check has a negative control proving detection power. The single parameterized
  check (the `SourceBars` range) gets a control for its new lower boundary, plus a
  positive must-not-overfire assertion. All other controls are byte-identical.
- **Suite-level fail rule**: a missed control (injected fault not detected) fails the
  **whole run** regardless of every positive check — a real fault could otherwise pass
  unnoticed. The must-not-overfire assertion firing (legit partial flagged) is also a
  run FAIL (the tolerant change is unsafe).
- **Expected output**: one `negative_control` row per control in
  `validation_checks.csv` (PASS = fault detected), plus `negative_controls.csv`; the
  15m and 30m golden-fixture rows; the must-not-overfire row.

### Step 7: 15m determinism-anchor reconciliation

- **Method**: The 15m **strict** cell carries the `source_timeframe="15m"` token,
  identical to VAL-001/VAL-003. Reconciliation has two legs:
  1. **Within-run determinism**: the existing `deterministic_regeneration` check
     (two regenerations byte-identical) for every 15m strict view, plus a per-cell
     `aggregated_fingerprint` = sha256 over the canonically serialized 15m strict
     aggregated frame (sorted `CloseTime, Open, High, Low, Close, SourceBars`),
     recorded in `determinism_anchor.csv`.
  2. **Cross-run reconciliation (in-code)**: the run loads the pinned VAL-001 (4
     core) and VAL-003 (13 new) `validation_checks.csv` records (prior check
     outcomes — not holdout data), filters to `source_timeframe == "15m"`, and for
     each instrument compares every prior `(instrument, view, check)` key against
     VAL-004's `15m` row: each prior key must be present and PASS in VAL-004 and
     every VAL-004 `15m` check must be PASS. A missing key, a status mismatch, or a
     non-PASS row emits a per-instrument `anchor_15m_reconciles_prior` FAIL that
     gates the run exit code (so the run cannot exit PASS with a perturbed 15m
     path). An instrument with no prior record reconciles as NO_PRIOR (INCONCLUSIVE).
     Data-derived denominators are recorded in the check detail for audit but are not
     themselves a failure trigger (legitimate data refresh may grow them). The
     auditor confirms the reconciliation outcome.
- **Why**: The anchor proves the timeframe-set extension and tolerant pass did not
  alter the previously validated 15m strict behavior — the precondition for trusting
  the new 30m and tolerant claims produced by the same code path.
- **Expected output**: `determinism_anchor.csv` (per instrument: 15m strict
  aggregated row count, fingerprint, `deterministic_regeneration` status); the auditor
  records the cross-run match in `audit.md`.

## Per-cell adjudication (PASS / FAIL / INCONCLUSIVE / COVERAGE_EXCLUDED)

Adjudicated per `instrument × domain × mode` cell, reusing
`status_from_failures` (denominator ≤ 0 → INCONCLUSIVE; any failure → FAIL; else PASS):

- **PASS (ADMITTED)**: all integrity checks PASS for the cell; (tolerant) the
  dropped fraction is disclosed and ≤ 0.25; determinism byte-identical. Cell is
  admissible to EXP-048.
- **COVERAGE_EXCLUDED** (tolerant only): all integrity checks PASS but dropped
  fraction > 0.25. Recorded exclusion; cell blocked from Phase 014; **not** a suite
  FAIL.
- **FAIL**: any integrity/alignment check fails for the cell → cell blocked from
  Phase 014 admission. (Suite-level: also FAIL if any negative control is missed or
  the must-not-overfire assertion fires.)
- **INCONCLUSIVE**: insufficient rows to power a prefix/determinism probe, or zero
  candidate windows for the coverage metric, with no integrity failure → cell
  deferred, recorded.

**Exit-code contract (single contract across scope / plan / code):**
- **PASS (exit 0) = full Suite PASS**: no FAIL and no INCONCLUSIVE check — universe
  reconciles to the 17 expected instruments, the 15m anchor reconciles to the
  VAL-001/VAL-003 record on every instrument, every cell is ADMITTED or a recorded
  COVERAGE_EXCLUDED, zero integrity failures, all negative controls detected, both
  golden fixtures and both must-not-overfire assertions PASS. A COVERAGE_EXCLUDED
  cell (dropped > 0.25) is a recorded exclusion, **not** a check FAIL, and does not
  block exit 0.
- **INCONCLUSIVE (exit 2) = PASS-with-deferrals**: no FAIL, but ≥1 INCONCLUSIVE check
  (a cell with too few rows to power a probe, or zero candidate windows). The
  deferred cell is recorded and **not** admitted; ADMITTED cells in the same run
  remain individually valid for EXP-048.
- **FAIL (exit 1)**: any integrity check FAIL, missed negative control, must-not-
  overfire firing, anchor divergence, or universe non-reconciliation. A
  universe/anchor FAIL blocks the whole gate; a per-cell integrity FAIL blocks only
  that cell's admission.

## Output schema

Reuse the VAL-001 result files unchanged in schema (mode encoded in the
`source_timeframe` token), plus two new disclosure tables:

| File | Schema | Notes |
|---|---|---|
| `results/validation_checks.csv` | VAL-001 9-col `ValidationCheck` | All per-cell + control + golden + anchor rows; mode in `source_timeframe`. |
| `results/instrument_summary.csv` | VAL-001 grouped | by instrument. |
| `results/timeframe_summary.csv` | VAL-001 grouped | by instrument × source_timeframe × view. |
| `results/chart_view_summary.csv` | VAL-001 `EventDensity` | density denominators over the new domains. |
| `results/negative_controls.csv` | VAL-001 `NegativeControl` | unchanged catalogue + tolerant-range control. |
| `results/coverage_map.csv` | **new** | instrument, domain, candidate_windows, retained_windows, dropped_windows, dropped_fraction_tolerant, dropped_fraction_strict, admission_status. |
| `results/determinism_anchor.csv` | **new** | instrument, agg_rows_15m_strict, fingerprint, determinism_status, prior_reconciled (PASS/FAIL/NO_PRIOR vs the pinned record). |
| `results/run_metadata.json` | VAL-001 metadata | + `source_timeframes=[15,30]`, `min_coverage_modes=[null, 0.9]`, derived `sourcebars_valid_range` per period, `instrument_universe` reconciliation, `processed_files`, holdout rule. |

The universe reconciliation rows (`universe_*`, `loaded_symbol_matches_filename`,
`instrument_not_duplicated`) and the per-instrument `anchor_15m_reconciles_prior`
rows live in `validation_checks.csv` and gate the run exit code.

## Visualisations (exactly 2 — scope budget)

1. **Per-cell dropped-fraction map (15m/30m).** Grouped horizontal bars of
   `dropped_fraction_tolerant` by instrument, faceted/colored by domain {15m, 30m},
   with the **0.25 admission threshold** drawn as a reference line and the strict
   dropped fraction overlaid for context. Answers: which cells are ADMITTED vs
   COVERAGE_EXCLUDED, and how much coverage tolerance recovers vs strict.
   → `plots/dropped_fraction_map.png`.
2. **Check-pass heatmap.** Instrument (rows) × `source_timeframe×view` (columns)
   colored by cell status (PASS / FAIL / INCONCLUSIVE), including the negative-control
   group (all-PASS = every injected fault detected). Answers: do any failures or
   inconclusives concentrate in a domain, mode, view, or instrument, and is detection
   power intact. → `plots/check_pass_heatmap.png`.

Plot inputs are the aggregated result tables (bounded), never raw market data; no
price/outcome metric is plotted.

## Implementation safety constraints (for `experiment-developer`)

- **Holdout fence**: reuse `load_analysis_data` verbatim — sort by `CloseTime`,
  collect only `int(total_rows*0.7)`; never collect or inspect the final 30%. All
  aggregation, oracles, dropped-fraction, charts, and fingerprints derive from the
  first-70% frame only. Re-assert the fence in code; the auditor re-checks it.
- **Timestamp ordering**: `CloseTime` for time/timeframe bars; `SourceCloseTime`
  (LB/Renko) and `CloseTime` (HA) for chart alignment. **Never** align by bar index.
- **Tolerant floor derivation**: compute `floor = max(2, math.ceil(min_coverage *
  period_minutes))` — the **same** expression as `aggregate_ohlc` — for both the
  oracle retention predicate and the range check; assert it equals the documented
  `[14,15]`/`[27,30]`. Do not hardcode the range in the predicate.
- **Oracle independence preserved**: keep the pandas resample path; only its
  retention filter is parameterized (`== P` strict, `>= floor` tolerant). OHLC
  equality stays exact.
- **Zero-baseline / denominators**: `status_from_failures` already maps denominator
  ≤ 0 → INCONCLUSIVE (no silent pass). Dropped-fraction denominator is
  `candidate_windows`; `candidate_windows == 0` → INCONCLUSIVE, never `0/0`.
- **Bounded iteration & progress**: `tqdm` over the 17-instrument outer loop and the
  domain×mode / chart inner loops. Probe bounds `PREFIX_WINDOW_ROWS=150_000`,
  `DETERMINISM_ROWS=50_000` unchanged. No unbounded Python row loops; dropped-fraction
  via a single Polars `group_by` on the bucket expression (pure aggregation, causally
  safe).
- **Determinism / no side effects**: output dirs created only in orchestration;
  generators deterministic; fingerprint via a canonical serialization (stable column
  order + sort) so it is reproducible across runs.
- **No scope expansion**: no period other than {15, 30}; no `min_coverage` other than
  {None, 0.90}; no tuning; a failed cell is a recorded result, not a trigger to try a
  new variant.

## Complexity Check

- Statistical tests: **0 / 0**
- Visualisations: **2 / 2** (dropped-fraction map; check-pass heatmap)
- New modules: **0 / 0–1** (no new `xen` module; the timeframe-set extension,
  tolerant-mode pass, `dropped_window_fraction` helper, fingerprint, and the two new
  disclosure tables live in `VAL-004/code/run_experiment.py`, reusing every VAL-001
  rev. 3 check function)

## Data-view comparison considerations

- **Cross-view alignment**: aggregated 15m/30m bars align to their source by
  `CloseTime`; LB/Renko align by `SourceCloseTime`; HA aligns by `CloseTime` and
  preserves real OHLC. Event counts differ by view (sparse charts emit fewer rows;
  Renko may emit multiple rows at one `SourceCloseTime`) — both emitted-row and
  distinct-source-timestamp counts are reported, never deduplicated.
- **Mode comparison**: strict and tolerant are independent constructions of the same
  domain; the tolerant dropped fraction is by construction ≤ the strict dropped
  fraction. Phase 014 consumes the tolerant construction, so the tolerant dropped
  fraction is the gating coverage figure.
- **Real-price outcome discipline**: no strategy P&L, signal return, or forward
  outcome is computed. Synthetic chart prices are validated only as generator output
  fields, against real aggregated-bar OHLC at identical `CloseTime`.
- **Regime stratification**: none — this is an architecture/construction validation,
  not a market-behavior study.

## Interpretation Guide (pre-registered, before results exist)

- **Suite SUPPORTED** if: all negative controls detected, both golden fixtures PASS,
  every per-cell integrity check PASS, the 15m determinism anchor reconciles to
  VAL-001/VAL-003 on all 17 instruments, and every 15m/30m cell is ADMITTED,
  COVERAGE_EXCLUDED, or INCONCLUSIVE with no integrity failure. Each ADMITTED cell is
  then eligible for EXP-048.
- **Contradicted (cell-level FAIL)** if: a 30m/15m resample disagrees with the
  independent oracle, a chart violates prefix stability (look-ahead), regeneration is
  non-deterministic, a timestamp/real-price contract is violated, or a tolerant
  partial window with out-of-range `SourceBars` is retained. That cell is blocked.
- **Run-level FAIL** if: any negative control is missed, or the must-not-overfire
  assertion fires (the tolerant range falsely rejects a legitimate partial) — the
  suite cannot be trusted regardless of positive checks.
- **Anchor FAIL** if: a 15m strict row diverges from the VAL-001/VAL-003 record — the
  harness change perturbed previously validated behavior; the 30m/tolerant claims
  produced by the same path are not trustworthy until reconciled.
- **COVERAGE_EXCLUDED** (not a defect) if: a cell's tolerant dropped fraction > 0.25
  while all integrity checks PASS — recorded exclusion, cell deferred from Phase 014
  (cf. JP225-2h).
- **INCONCLUSIVE** if: a cell has too few rows to power the prefix/determinism probes,
  or zero candidate windows, with no integrity failure.
