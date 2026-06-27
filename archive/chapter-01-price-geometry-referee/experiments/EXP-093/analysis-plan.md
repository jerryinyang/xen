# Analysis Plan: Experiment EXP-093

**Phase:** 021 (CF-MR-001 batch 2) · **Family / HYP:** `CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Type:** one-shot counted-TEST confirmation (the phase's single binding tradability read; analog EXP-037/038/032)
**Inputs:** [`scope.md`](scope.md) · D0 §D6/4c, §D7 · `D0-amendment-006` (carried set = 11, Holm-11) ·
EXP-092 pinned candidate set (sha256 `f6427e83…`) · the verbatim EXP-090 substrate.

## Objective

Determine, **per carried (instrument, domain) cell on the analysis-TEST stratum**, whether the bare RSI-2 fade
with EXIT-RCT produces a net-of-cost per-event expectancy that **CONFIRMS** under the frozen rule — `Holm-adj p
≤ 0.05 AND net ci_low_1s > margin` (margin = the cell's EXP-090/094 MDE: 1h 0.0125 / 4h 0.025 ATR). The Holm
family is the **11 carried cells**. EXP-093 emits the per-cell adjudication; G-021 reads it against
`G-021-gate-criteria.md`. The honest prior is **availability ≠ capturable edge**: a TRAIN sequence pass is
necessary-but-not-sufficient, and the TEST stratum is a genuine falsification (selection/overfitting shrinkage
expected, à la EXP-084 fold reversal).

**No method, threshold, cost, margin, referee, or Holm sizing is chosen or changed after seeing any TEST number.**
Everything below is frozen before the read.

## Methodology

### Step 0 — Analysis-TEST slice (holdout-safe; the binding correctness point)

- **Method:** chronological nested split per file. `total_rows` = sorted 1m bars; `analysis_cutoff =
  int(total_rows·0.7)`; `train_cutoff = int(analysis_cutoff·0.7) = int(int(total_rows·0.7)·0.7)`. The
  **analysis-TEST stratum** = 1m rows `[train_cutoff, analysis_cutoff)`; its timestamp bounds are
  `ts_lo = CloseTime[train_cutoff]`, `ts_hi = CloseTime[analysis_cutoff]` (1-minute-row timestamp boundary, R1.3).
- **Load only `[0, analysis_cutoff)`** (the full first-70% analysis set). The `[0, train_cutoff)` TRAIN region
  is loaded **as indicator warmup / history only** (RSI(2), ATR(14), EMA(10), MR-tempo state are causal and need
  pre-TEST bars); **no TRAIN entry enters the binding estimand**. The **final-30% global holdout
  `[analysis_cutoff, total_rows)` is never loaded, sliced, or materialized** (incl. its 1m bars).
- **Binding estimand population:** CORE fade entries whose **domain-bar `CloseTime ∈ [ts_lo, ts_hi)`** (the TEST
  stratum). The forward 1m intrabar fill walk is **clipped by timestamp at `ts_hi`** (the analysis-set right
  edge), never by 1m index — an event whose MR-tempo-cap window would cross `ts_hi` is right-censored
  (unresolved) and excluded by the `keep` mask, exactly as EXP-090–092 clipped at the TRAIN edge.
- **Why sufficient:** this is the standard nested split (pipeline config "OOS Holdout Rules"); the counted read
  is precisely "the stratum's events entering binding inference" (ledger definition). The TRAIN-as-warmup read
  was already disclosed in EXP-090–092 and carries no new counted read.
- **Expected output:** per cell, the TEST-stratum resolved-event count `n_resolved` (expected ≈ 0.43× the TRAIN
  counts since TEST rows ≈ 21/49 of TRAIN rows → 1h ≈ 1600–1700, 4h ≈ 370–470 resolved; **realized counts
  supersede and are disclosed**), `ts_lo`/`ts_hi`, holdout-untouched assertion.

### Step 1 — Resolve real EXIT-RCT exits on TEST (substrate reuse, verbatim)

- **Method:** reuse the audited EXP-090 substrate (`build_cell_context`, `resolve_arm`/RCT, `xen.intrabar_fill`,
  `net_return_atr`) **unchanged**; the only delta vs EXP-092 is the Step-0 loader (analysis-TEST instead of
  TRAIN). RCT target `P*_t = Close_t + (AL_t − AG_t)` (long; short symmetric), trailing; adverse `2.0×ATR(14)`
  stop + MR-tempo cap; conservative adverse-first 1m order-of-touch tie-break; real touched fill price.
- **Why this method / simpler alternative:** the geometry is frozen (D2); re-deriving it identically on TEST is
  the only faithful confirmation. No simpler alternative exists that preserves byte-identity to the screen.
- **Assumptions:** causal (only bars at/after entry); deterministic. Holds for time-ordered data by construction.
- **Expected output:** per cell, direction-signed gross ATR return per resolved event, holding days, tie-break
  fraction, terminal-favourable fraction.

### Step 2 — Cost overlay (frozen D3 / D0-amendment-003)

- **Method:** `event_costs(..., rt_bps=RT_i, fin_bps_day=0)` with the Phase-021-local CONSERVATIVE table (hash
  `fa7c887…`); net = gross − cost, ATR units. Shared `xen.capgeo_cost.COST_CONSTANTS` not mutated.
- **Why sufficient:** identical cost model to EXP-085/091/092; re-estimating cost on TEST would be goalpost-moving.
- **Expected output:** per resolved event, net ATR return; per cell net mean and net median.

### Step 3 — Binding inference: net expectancy lower bound + one-sided bootstrap p (per cell)

- **Method:** **moving-block bootstrap** (`xen.ass`, `n_boot=10_000`, seeds via `seed_for(EXP-093,...)`) on the
  per-event net series. Report (a) the one-sided lower bound `net ci_low_1s` (Z=1.645, the `expectancy_lo` at
  `alpha=0.10`), identical estimator to EXP-092; and (b) a **one-sided bootstrap p-value** `boot_p` for
  `H0: net expectancy ≤ 0`, computed from the **same moving-block resampling stream** as the CI (EXP-032/037/038
  convention): `boot_p = (1 + #{bootstrap mean ≤ 0}) / (1 + n_boot)`.
- **Why this method:** moving-block preserves the serial dependence of intraday per-event returns (no i.i.d. /
  normality assumption — programme principle); it is the frozen estimator already calibrated for FPR/MDE in
  EXP-090/094. **Simpler alternative considered:** a plain percentile bootstrap or a t-test — rejected (ignores
  serial dependence; t-test assumes normality, a methods-catalog "avoid").
- **Assumptions:** approximate exchangeability of blocks; block length inherited from the calibrated `xen.ass`
  setting (unchanged). Weakness: at the smallest 4h counts the block bootstrap is wider — surfaced by the
  power/INCONCLUSIVE branch, not hidden.
- **Expected output:** per cell `net_ci_low`, `boot_p`, `net_mean`, `net_median`, `n_resolved`.

### Step 4 — Phase Holm family (D0-amendment-006: 11 cells)

- **Method:** Holm–Bonferroni, **one-sided, α=0.05**, over the **11** carried cells' `boot_p` values →
  `holm_adj_p` per cell. (Carrying all 11 widens the family vs the robust 8 → strictly **more conservative** FPR
  control; it cannot make a true CONFIRM easier.)
- **Why sufficient:** Holm is the predeclared phase multiplicity control (D6/4c); the family is fixed at 11 by
  `D0-amendment-006` before the read.
- **Expected output:** per cell `holm_adj_p`; the family size and ordering recorded.

### Step 5 — Per-cell adjudication (frozen D6/4c)

```
CONFIRM       iff holm_adj_p <= 0.05  AND  net_ci_low > margin
FAIL          iff holm_adj_p  > 0.05  OR   net_ci_low <= margin           (significant-but-immaterial -> FAIL)
INCONCLUSIVE  iff n_resolved < power floor / the bound spans zero (net_ci_low <= 0 with wide CI) at the
              realized TEST count (a la EXP-032); a cell with < 2 resolved events is INDETERMINATE (reported)
```

- **Expected output:** `test_adjudication.csv` — per cell {n_resolved, net_mean, net_median, net_ci_low, margin,
  boot_p, holm_adj_p, clears_margin, holm_sig, verdict ∈ {CONFIRM, FAIL, INCONCLUSIVE, INDETERMINATE}}.

### Step 6 — Descriptive companions (non-binding; honesty reads)

- **TRAIN→TEST shrinkage** per cell: `net_ci_low_TEST − net_ci_low_TRAIN` and `net_mean_TEST − net_mean_TRAIN`
  (the EXP-092 TRAIN values are the pinned reference). Expectation: shrinkage toward zero; a sign flip is the
  EXP-084-style selection-overlap reversal — disclosed, informs INCONCLUSIVE vs FAIL.
- Gross expectancy (sanity vs EXP-092), net median (the D5 median-fragility shape read), MAE/`q05` adverse tail,
  holding days, tie-break incidence, terminal-favourable fraction — all per cell.

### Step 7 — Determinism replay (D9)

- **Method:** re-run ≥1 cell per domain (e.g. USTEC-1h + EURUSD-4h); assert `net_ci_low`, `boot_p`,
  `holm`-inputs, and `n_resolved` byte-identical (incl. the 1m walk + bootstrap stream).
- **Expected output:** `determinism_pass=true`; `non_deterministic=[]`.

## Visualisations (4 / budget 4)

1. **TEST per-cell `net_ci_low` vs 0 and vs margin** (barh, sorted by domain then bound; CONFIRM/FAIL colored) —
   the binding read at a glance.
2. **CONFIRM map** (instrument × domain grid, per-stratum verdict) — which cells carry a TRADABLE verdict
   (LESSON-001 per-stratum view).
3. **TRAIN vs TEST `net_ci_low` per cell** (paired bars) — the shrinkage/reversal honesty read (selection-overlap
   diagnostic).
4. **Per-cell net-expectancy bootstrap distributions** (small multiples or overlaid) with 0 and the margin marked
   — shows power/width and where the bound sits.

## Interpretation Guide (predeclared, before results exist)

- If **≥1 carried cell CONFIRMS** (`holm_adj_p ≤ 0.05 ∧ net_ci_low > margin`) → **evidence the fade is net-tradable
  on TEST** on that stratum → routes G-021 **TRADABLE**. The robust-core cells (8) are the expected carriers;
  CONFIRM there is the strongest reading.
- If **every carried cell FAILS** the margin/Holm → **the TRAIN edge does not survive out-of-sample** → routes
  G-021 **NOT_TRADABLE**; with regime inert and variants dead, CF-MR-001 effectively exhausted (returns to the
  G-019 non-price frontier).
- If the binding read(s) are **power-limited / span zero** → **INCONCLUSIVE** (à la EXP-032): neither confirmed
  nor refuted; the remaining 1/2 read per stratum is a separate future decision.
- **GBPUSD-1h:** a FAIL is the **expected** result (below its margin already on TRAIN, median-negative); it is
  **not** new evidence against the lever — its read is spent for completeness per `D0-amendment-006 §2`.
- **EURUSD-1h / NZDUSD-1h:** the binding gate is the **mean**; a CONFIRM with negative median is a mean-carried
  (tail-shaped) pass — reported with the median as the disclosed shape caveat, not down-weighted post hoc.
- A large TRAIN→TEST shrinkage that pushes a robust-core cell below margin **without** spanning zero is a FAIL
  (significant-but-immaterial); one that spans zero at low power is INCONCLUSIVE. The distinction is the bound,
  fixed here, not chosen after seeing it.

## Implementation safety constraints (for experiment-developer)

- **Holdout (hard):** never load/slice/materialize `[analysis_cutoff, total_rows)`; assert
  `holdout_untouched=true` and that no 1m row with `CloseTime ≥ ts_hi` enters any fill walk. Build domain bars
  with the holdout-fenced `build_domain_bars` over the analysis set (drop any right-labelled window beyond the
  analysis edge).
- **Counted reads:** the binding estimand reads the analysis-TEST stratum of all 11 strata →
  `counted_test_reads=11`, `candidate_slots=0` in `run_metadata.json`. The ledger entry is recorded at Stage 7
  in the same change as the result.
- **Timestamp alignment, never bar index:** domain→1m mapping and the TRAIN/TEST/analysis boundaries are by
  `CloseTime`; entries selected by domain-bar `CloseTime ∈ [ts_lo, ts_hi)`.
- **Denominator = resolved events** (`keep` mask identical to EXP-092 `sequence_cell`: resolved ∧ finite gross ∧
  finite positive entry ATR ∧ finite non-negative holding days). `n_resolved < 2` → INDETERMINATE (no forced
  number). No zero-baseline ratio is computed.
- **No tuning / no new module:** import the EXP-090 module; add only the analysis-TEST loader (`load_test_1m`
  analog of `load_train_1m`) and the per-cell Holm/adjudication. Reuse `xen.ass`, `xen.capgeo_cost`,
  `xen.intrabar_fill`, `xen.referee_calibration.seed_for`. Seeds fixed; second pass byte-identical.
- **Bounded loops / progress:** `tqdm` over the 11 cells; bootstrap vectorized inside `xen.ass`; bounded pandas
  only for the 4 plots from collected summaries (no re-loads). Block length and `n_boot` inherited unchanged.
- **Drift assertions:** re-derive the carried set + per-cell margins from the upstream EXP-090/091/094 artifacts
  with the same hard-fail drift checks EXP-092 used, and assert the carried set hashes to the pinned
  `f6427e83…` membership; hard-fail if the carried set ≠ the 11 ratified cells.

## Complexity Check

- Statistical tests: **1 binding** (per-cell moving-block net lower bound + one-sided bootstrap p under Holm-11)
  + descriptive companions / **budget 1 + companions** ✓
- Visualisations: **4 / 4** ✓
- New modules: **0 / target 0** (substrate reuse; one new in-script loader function, not a module) ✓
