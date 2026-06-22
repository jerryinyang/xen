# Analysis Plan: Experiment EXP-080

**Phase 018 / CF-CAPGEO-001 — Substrate/Exit Readiness (HYP-001).** Stage 2 artifact.
Companion: [`scope.md`](scope.md). This plan is **readiness/validation**, not edge measurement:
the deliverables are a determinism + look-ahead-invariant + coverage map over 192 substrate-cells,
**one** statistical test (the moving-block null-FPR machinery sanity), and four bounded plots. No
exit, return, capture, expectancy, or P&L metric is produced (those begin at EXP-081).

## Objective

Determine, for every one of the **192 substrate-cells** (4 frozen substrates × 16 instruments ×
{15m, 1h, 4h}), whether the frozen entry detector reproduces **deterministically**,
**look-ahead-safe**, and **invariant-clean** on the VAL-005-admitted 5-year first-70% analysis slice
under the holdout-fenced `build_domain_bars` construction; quantify each cell's realized entry count
against the Phase-017 `ASS`-discovery bracket **[15, 8000]** (D7); confirm the moving-block bootstrap
controls FPR at the new 5-year data scale; and disclose whether the two harami substrates share an
identical entry population. Output is a `READINESS_DELIVERED` map plus the `SUBSTRATE_REFUTED`
halt-check — **no market-edge claim**.

The methodology is dominated by **deterministic checks** (boolean invariants, exact two-pass
equality, raw counts). Only one item is a statistical test (Step 6). This matches the EXP-043/048
readiness precedent and the Descriptive/EDA complexity tier.

---

## Methodology

### Step 0: Lazy load + holdout-fenced domain construction

- **Method**: Per instrument, `pl.scan_parquet` the single VAL-005-admitted 5-year file; read
  `total_rows` from metadata; `analysis_rows = int(total_rows * 0.7)`; collect only the first
  `analysis_rows` file-order 1-minute rows; assert `CloseTime` sorted; set `analysis_end_ts` = last
  collected `CloseTime`. Build 15m/1h/4h domain bars by **reusing the VAL-005-validated
  `build_domain_bars`** (`aggregate_ohlc(min_coverage=0.90)` + analysis-boundary fence: drop any
  window whose label exceeds `analysis_end_ts`).
- **Why this method**: The fence is the ratified VAL-005 G1 finding; CF-CAPGEO-001 *inherits* it.
  Re-deriving domain construction would risk divergence from the validated path.
- **Simpler alternative considered**: Plain `aggregate_ohlc` without the fence — rejected: VAL-005
  G1 showed the tolerant 0.90 path emits a trailing partial window whose nominal label crosses into
  holdout-minute timestamps; the fence is mandatory to keep domain bars holdout-clean.
- **Assumptions**: 1-minute file order is chronological (VAL-005 G1 verified); first-70% prefix is
  the analysis set (programme split rule). Holds for this dataset.
- **Expected output**: per (instrument × domain) a fenced domain-bar frame + the dropped-window
  fraction + `analysis_end_ts`; the final-30% holdout is never materialized (only metadata read).

> **Implementation note (binding):** `build_domain_bars` currently lives in
> `python/experiments/VAL-005/code/run_experiment.py`. The developer must **reuse the identical
> validated logic** — either import it or promote it verbatim to a shared `xen` helper — and a
> regression check must confirm EXP-080's domain-bar counts reconcile to VAL-005's for at least one
> shared (instrument × domain) cell **before** any substrate read. Do not re-implement the fence.

### Step 1: Frozen substrate entry generation (4 detectors, ported — not re-derived)

- **Method**: Behind one uniform `entries(domain_bars, ha_candles?) -> events` interface, generate
  each substrate's entry events on the fenced domain bars:
  - `SUB-AVWAP` — `xen.avwap.generate_avwap_events(...)` with the CF-AVWAP-001 final frozen
    parameters (EXP-028/029); real domain OHLC.
  - `SUB-HARAMI-PARTIAL-V2A` / `SUB-HARAMI-V2A-ADVNONE` — the MA(20,50)-native
    `/STRONG-STAT`-conditioned HA-harami **entry**, ported from EXP-068 (composing
    `xen.heiken_ashi_generator`, `xen.ha_harami.detect_ha_harami`, `xen.zigzag`, `xen.strong_move`,
    and the MA(20,50) gating on real close). The entry is the object under test — **port, do not
    re-derive**.
  - `SUB-RANDOM` — a fixed-seed matched-random entry generator: per cell, draw entry timestamps at
    completed domain-bar closes only, count matched to each real substrate's realized count, seed
    `SEED_RANDOM` (frozen in `run_metadata.json`).
- **Why this method**: Reusing the closed families' frozen detectors guarantees the substrates are
  the *same objects* the prior families validated; a uniform interface keeps the readiness/
  determinism/counting logic identical across substrates.
- **Simpler alternative considered**: Re-deriving the harami entry inline — rejected: re-derivation
  risks silently changing the frozen entry population (an EXP-042-class framing risk).
- **Assumptions**: the ported detectors are streaming/causal (verified in their home families and
  re-checked in Step 3). Holds.
- **Expected output**: per substrate-cell an entry-event table (timestamps + structural fields),
  produced twice (Step 4 determinism).

### Step 2: Construction-integrity checks (deterministic)

- **Method**: Per (instrument × domain): OHLC consistency (`High ≥ max(Open,Close)`,
  `Low ≤ min(Open,Close)`); strictly increasing `CloseTime`; clock-aligned window boundaries; the
  **holdout-fence invariant** (no emitted window label > `analysis_end_ts`); dropped-window
  fraction vs the frozen bands (`<0.10` clean / `0.10–0.25` flagged / `>0.25` `COVERAGE_EXCLUDED`).
- **Why this method**: Direct boolean integrity checks — the readiness standard (EXP-043/048,
  VAL-005). No statistical inference appropriate or needed.
- **Simpler alternative considered**: trusting VAL-005's prior pass — rejected: domain construction
  must be re-asserted on the slice actually used here.
- **Assumptions**: none beyond the schema. Holds.
- **Expected output**: per-cell integrity record + dropped-fraction + construction status.

### Step 3: Entry-detector invariant battery (deterministic, look-ahead-safety)

- **Method**: Per substrate-cell, assert: all entry timestamps within `[analysis_start,
  analysis_end_ts]`; entries on completed-bar closes only; **causality** (no entry field derives
  from a bar with `CloseTime` after the entry timestamp); detector-specific structural invariants
  (AVWAP anchor/bounce conditions; harami `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0` with
  the reduced-form agreement, MA(20,50) + `/STRONG-STAT` gating reproduced); no NaN/null in emitted
  fields; events monotone in `CloseTime`; `SUB-RANDOM` entries land only on completed closes.
- **Why this method**: Look-ahead safety and structural correctness are boolean properties; this is
  the core readiness assurance that downstream edge reads will not be confounded by leakage.
- **Simpler alternative considered**: spot-checking a sample of events — rejected: readiness
  requires the invariants hold on *every* event, cheaply assertable.
- **Assumptions**: none. Holds.
- **Expected output**: per-substrate-cell pass/fail per invariant, with the first violating event
  recorded on any failure.

### Step 4: Determinism (exact two-pass)

- **Method**: Regenerate every cell's domain bars, HA candles (where applicable), and entry events a
  **second** time; assert the entry-event table compares **frame-identical** (exact) to the first
  pass. `SUB-RANDOM` byte-identical from `SEED_RANDOM`.
- **Why this method**: Determinism is a programme principle and a `SUBSTRATE_REFUTED` halt trigger;
  exact equality is the only acceptable bar.
- **Simpler alternative considered**: hashing only — acceptable but exact frame equality is clearer
  and equally cheap at this scale.
- **Assumptions**: fixed seeds + ordered input ⇒ identical output. Verified by the test itself.
- **Expected output**: per-cell determinism PASS/FAIL.

### Step 5: Entry coverage & D7 bracket (descriptive)

- **Method**: Per substrate-cell, report entry count and entries per 1,000 fenced domain bars
  (denominator = cell domain-bar count, disclosed); classify the **D7 bracket**: `IN_BRACKET` iff
  `15 ≤ count ≤ 8000`, else `OUT_LOW` (<15) / `OUT_HIGH` (>8000).
- **Why this method**: Descriptive coverage is exactly what readiness must report; the bracket flag
  is the predeclared D7 gate for whether `ASS` discovery is in its validated regime (binding
  adjudication remains the frozen suite regardless).
- **Simpler alternative considered**: counts only without the bracket — rejected: D7 explicitly
  requires the [15,8000] check be emitted here.
- **Assumptions**: bracket bounds are the Phase-017-validated synthetic span (frozen). Holds.
- **Expected output**: entry-count + rate + bracket-flag table (192 rows).

### Step 6: Moving-block null-FPR sanity — **the one statistical test**

- **Method**: A **moving-block bootstrap one-sided false-positive-rate** check at the 5-year data
  scale. Null carrier (predeclared): **block-permuted, mean-centered domain-bar returns** (a
  non-tradable machinery probe — *not* a substrate/strategy/capture return; centering enforces the
  mean=0 null, block permutation preserves real serial dependence / volatility clustering). For each
  of `N_NULL` replicates at the realized per-cell length `n` (using the Step-5 domain-bar counts to
  cover the small-`n` 4h end and the large-`n` 15m end), draw a moving-block bootstrap of the
  one-sided 90% lower CI of the mean and record `CI_low > 0`. **FPR = fraction of replicates with
  `CI_low > 0`; report the Wilson 95% upper bound.** Reuse `xen.ass.default_block_length`,
  `xen.ass` bootstrap, and the `xen.wf._resample_fold(kind="block")` moving-block resampler — do not
  re-implement the bootstrap.
- **Why this method**: A non-parametric moving-block bootstrap is the programme-standard inference
  for serially-dependent financial returns; the readiness question is whether its FPR remains
  controlled at the ~2× longer 5-year per-cell sample sizes before any real read (Phase-017
  EXP-077/078 showed FPR is n-sensitive). One test, the predeclared `m_cell` family.
- **Simpler alternative considered**: an i.i.d. (flat) bootstrap — rejected: it ignores serial
  dependence and would *understate* the FPR on real-structured data, defeating the purpose of the
  sanity. Parametric/normal CI — rejected (academic-finance pitfall: normality/i.i.d.).
- **Assumptions**: moving blocks preserve short-range serial dependence; blocks exchangeable under
  the centered null. Reasonable for intraday returns; the test itself measures whether FPR holds.
- **Expected output**: FPR point estimate + Wilson-hi at representative small/mid/large `n`
  (denominator = `N_NULL`, disclosed). **`CONTROLLED` (halt-binding) iff Wilson-hi ≤ 0.075 at
  every tested `n` in the operating regime `n ≥ 120`** (D0 §D9 frozen operating floor).
  Rows at `n < 120` are recorded as disclosure (`regime="small_n_disclosed"`) — the small-`n`
  percentile-bootstrap FPR inflation is a known, disclosed property (Phase-017 EXP-077/078;
  D0 §D6 Guard (i) defers to median at effective-`n` ≤ 60), **not** a halt trigger.

### Step 7: Harami entry-population identity (disclosure)

- **Method**: Per cell, compare the `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` entry
  timestamp sets for exact equality; report identical / differing (with the count delta if any).
- **Why this method**: The two substrates differ only by *exit* (applied later); confirming the
  entry sets coincide is a cheap, decision-relevant disclosure (their entry-level counted-read
  accounting then coincides).
- **Simpler alternative considered**: assuming identity — rejected: the scope requires it be
  measured, not assumed.
- **Assumptions**: none. Holds.
- **Expected output**: per-cell identity flag + a one-line summary disclosure.

### Step 8: Per-cell classification + experiment verdict (deterministic aggregation)

- **Method**: Classify each substrate-cell `READY` (construction PASS incl. fence ∧ 0 invariant
  violations ∧ determinism PASS), `NOT_READY` (any invariant/determinism/construction FAIL incl.
  `COVERAGE_EXCLUDED`), or `CONSTRUCTED_EMPTY` (slice shorter than detector warmup). Counts/bracket
  do **not** affect READY. Aggregate to the experiment verdict and evaluate the `SUBSTRATE_REFUTED`
  halt triggers: non-determinism on *any* cell, the same invariant failing on **≥3 instruments**
  for any one substrate, or null-FPR Wilson-hi > 0.075 **at any `n ≥ 120` (the operating regime;
  D0 §D9 frozen floor)**. Null-FPR rows at `n < 120` are disclosed (`small_n_disclosed`), **not**
  halt-binding — the small-`n` inflation is the known Phase-017 EXP-077/078 property (D0 §D6
  Guard (i)).
- **Why this method**: deterministic rule application of the scope's predeclared criteria; no
  post-hoc thresholds.
- **Expected output**: 192-cell status map; `READINESS_DELIVERED` or `SUBSTRATE_REFUTED`.

---

## Visualisations (4 / 4)

1. **READY-status heatmap, small-multiple (4 panels, one per substrate)** — 16 instruments × 3
   domains, colored READY / NOT_READY / COVERAGE_EXCLUDED / CONSTRUCTED_EMPTY. Answers "where does
   any substrate fail to reproduce?"
2. **Entry-rate heatmap by substrate** — entries per 1,000 domain bars (16 × 3, faceted). Answers
   "how dense is each substrate's entry stream per cell?"
3. **D7-bracket map** — per substrate-cell IN_BRACKET / OUT_LOW / OUT_HIGH. Answers "which cells
   leave the [15,8000] `ASS`-discovery regime?"
4. **Entry-count distribution vs the bracket band** — histogram (log-x) of the 192 counts with the
   [15, 8000] band shaded. Answers "how far from the bracket edges does the mass sit?"

All plots are built from the already-collected per-cell summaries (no data reloads).

---

## Interpretation Guide (pre-defined, before results exist)

- **READINESS_DELIVERED (expected)**: the 192-cell map + entry-count/bracket table + null-FPR result
  + harami-identity disclosure are produced. READY cells proceed to EXP-081; NOT_READY /
  COVERAGE_EXCLUDED / CONSTRUCTED_EMPTY cells are excluded *with record*.
- **A cell is READY** iff construction integrity passes (dropped ≤ 0.25 **and** fence held) ∧ zero
  entry-detector invariant violations ∧ determinism PASS. Sparse / dense / out-of-bracket cells are
  **disclosures, not failures** (the lenient EXP-043/048 convention).
- **OUT_LOW / OUT_HIGH bracket** means: `ASS` *discovery* readouts are outside their validated regime
  for that cell → excluded from `ASS` discovery with disclosure at EXP-081/083; **the frozen referee
  suite remains the binding gate regardless** (no readiness consequence).
- **Null-FPR CONTROLLED** (Wilson-hi ≤ 0.075 at every tested `n` in the operating regime
  `n ≥ 120`) ⇒ the moving-block inference machinery holds at the 5-year scale. **UNCONTROLLED at
  any `n ≥ 120`** ⇒ `SUBSTRATE_REFUTED` halt (the downstream WF inference cannot be trusted at that
  scale until addressed). Rows at `n < 120` are recorded as disclosure (`small_n_disclosed`) and do
  **not** trigger the halt: the small-`n` percentile-bootstrap FPR inflation is the ratified,
  disclosed Phase-017 property (EXP-077/078; D0 §D9 operating floor `n ≥ 120`; §D6 Guard (i) defers
  to median at effective-`n` ≤ 60) — halting on it would contradict binding D0 constants.
- **SUBSTRATE_REFUTED (halt)** iff: non-determinism on any cell, OR the same invariant violated on
  ≥3 instruments for one substrate, OR null-FPR uncontrolled — a systematic detector/aggregation/
  port/machinery defect, not a data quirk. Halts Phase 018 pending a fix.
- **Harami entry identity**: if the two harami substrates' entry sets are exactly equal in every
  cell, disclose that their entry-level counted-read accounting coincides (an efficiency, not a
  finding); any differing cell is recorded with the delta.
- **No edge interpretation is in scope.** Entry counts/rates are coverage descriptors; nothing here
  supports or refutes any exit/expectancy claim.

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout**: never load, count, or materialize the final 30%; only Parquet metadata + the
  first-70% prefix are read. Assert the fence invariant (no domain label > `analysis_end_ts`) per
  cell. The nested analysis-set partitions are **not** separately selected or inferred upon (0
  counted reads; readiness exposure = disclosure).
- **Temporal ordering**: order and align by `CloseTime` only; never bar index. Assert input sorted
  before slicing.
- **Determinism**: fix and record `SEED_RANDOM` + all bootstrap seeds in `run_metadata.json`; the
  full second pass must be exactly reproducible (frame-identical entries; byte-identical SUB-RANDOM).
- **Reuse, do not re-derive**: import/promote the VAL-005 `build_domain_bars` (regression-checked
  vs VAL-005 on ≥1 shared cell before substrate reads); port the EXP-068 harami entry and the
  EXP-028/029 AVWAP entry from their frozen sources; reuse `xen.ass`/`xen.wf` for the moving-block
  bootstrap. No edits to `xen` generators.
- **Denominators / zero-baseline**: entry rate denominator = cell domain-bar count (disclosed); 0
  entries → rate `0.0` with denominator (never `0/0`); null-FPR denominator = `N_NULL` (disclosed);
  CONSTRUCTED_EMPTY guard for slices shorter than detector warmup.
- **No returns/edge**: compute **no** substrate return, capture, MFE/MAE, expectancy, or P&L. The
  Step-6 null carrier is an explicitly non-tradable, mean-centered, block-permuted machinery probe —
  not a substrate outcome.
- **Performance / progress**: lazy scans, column projection, bounded per-cell memory (do not retain
  all 192 domain frames simultaneously); `tqdm` over the 192-cell outer loop and the two passes.
  Vectorize loading/aggregation/summary only; keep the streaming detectors' sequential semantics
  intact (causality is the property under test).
- **Outputs**: per-substrate-cell summary parquet, READY-map CSV, entry-count + D7-bracket CSV,
  null-FPR JSON, `run_metadata.json` (seeds, hashes, module versions, `analysis_end_ts` per
  instrument), and the four plots from collected summaries.

---

## Complexity Check

- **Statistical tests: 1 / 1** — the moving-block null-FPR sanity (Step 6). Steps 2–5, 7–8 are
  deterministic checks / descriptive counts, not statistical tests.
- **Visualisations: 4 / 4** — READY heatmap (4-panel), entry-rate heatmap, D7-bracket map, count
  distribution vs bracket.
- **New modules: ≤ 2 / 2** — (a) a frozen substrate-entry harness (uniform `entries()` interface
  wrapping the existing AVWAP + harami detectors), and (b) a fixed-seed matched-random entry
  generator — only if they do not fit cleanly in the experiment script. Reuse
  `xen.bar_aggregator`, `xen.heiken_ashi_generator`, `xen.avwap`, `xen.ha_harami`, `xen.zigzag`,
  `xen.strong_move`, `xen.ass`, `xen.wf`, and the VAL-005 `build_domain_bars` unchanged.

Within budget (Descriptive/EDA + a single readiness test).
