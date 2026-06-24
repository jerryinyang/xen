# Analysis Plan: Experiment EXP-090

**Phase 021 / CF-MR-001 batch 2 — RSI-2 Fade Exit-Substrate Readiness & Per-Cell Inference Calibration
(HYP-002).** Stage-2 artifact. Companion: [`scope.md`](scope.md). Frozen design:
`docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/` (`design.md`,
`D0-predeclarations.md`, `D0-amendment-001.md`, `G-021-gate-criteria.md`).

> **Revision 2026-06-23 (pre-execution, plan↔code reconciliation; Stage-4 REVISE cycle 1).** Two surgical
> edits below reconcile the plan prose to the estimand-preserving implementation (the plan's original
> literal method was computationally infeasible; **no code change**): **(1)** the Step 3 calibration
> draw-generation is the tractable **pooled-resolution + moving-block-resample-to-true-0** construction
> (per-draw 1m placement was ~10¹³ ops; the estimand — FPR at true-location-0, MDE at TPR≥0.80, serial
> dependence, two structurally-different nulls, translation-equivariance planted edge, cost-free by
> location-invariance — is unchanged); **(2)** EXP-090 resolves/calibrates the **five** unified-engine arms
> (RCT, ERT, ATR-barrier, RSI-revert-on-close, fixed-bar) and **defers the two-leg partial/trail arm to
> EXP-091**. Scope, thresholds, holdout/fence discipline, per-stratum doctrine, budget counts, and the
> binding MEMBER gate (finite MDE on ≥1 native arm RCT/ERT) are **unchanged**. Matches the documented code
> deviations in `xen.intrabar_fill` / `run_experiment.py` and `governance/pre-execution-review.md`.

This plan has **two cleanly separated deliverables**, mirroring the two analogs the scope names:

- **A. Readiness (deterministic; EXP-080 pattern).** The bare RSI-2 fade (CORE) entry substrate **and** the new
  1-minute intrabar exit-fill substrate (D2.5 + the D2.3 frozen adverse side) are constructible, deterministic,
  causal, timestamp-aligned, and holdout-fenced on the 32 member cells. **No expectancy, no cost, no exit
  selection.**
- **B. Per-cell event-level inference calibration (EXP-044 / EXP-070 pattern).** The binding D6 figure — the
  **mean** net per-event expectancy moving-block bootstrap one-sided lower bound (`Z=1.645`; median co-reported,
  D5) — has **controlled per-cell FPR** (≤ α₀ = 0.05 under two structurally-different nulls) and a **finite
  per-cell event-level MDE** (the EXP-093 margin, D6 4c) at each cell's realized event count, measured on
  **synthetic null / planted-edge draws over the real TRAIN scaffolding** (real fade **outcomes never read for an
  edge** — the EXP-044 anti-overfitting fence).

Output is a **`READINESS_CALIBRATION_DELIVERED`** map (32 cells: MEMBER / `COVERAGE_EXCLUDED` /
`CALIBRATION_UNDERPOWERED`) plus the process-level **HALT** check. **No market-edge claim, 0 candidate slots, 0
counted TEST reads, TRAIN-only.** The exit screen (EXP-091), sequence (EXP-092), and the one-shot TEST (EXP-093)
are downstream; EXP-090 only proves the machinery is constructible and powered on the member cells.

---

## Reused vs. new components

| Component | Source | Status in EXP-090 |
| --- | --- | --- |
| Holdout-fenced TRAIN load (first 49% file-order rows) + `build_domain_bars` (15m/1h, `min_coverage=0.90` + TRAIN-edge fence) | `xen.domain_bars`, EXP-080/089 path | reused unchanged; regression-checked vs EXP-080 domain-bar counts on ≥1 shared 15m/1h cell before any read |
| CORE bare RSI-2 fade entries (`mean_reversion_entries(...)["CORE"]`), `wilder_rsi`, `wilder_ema`, `mr_tempo_caps`, `reversion_episodes` | `xen.mean_reversion` (frozen Phase 020) | reused **unchanged**; CORE population only (no variants) — **the entry is the frozen object under test, never re-tuned** |
| Moving-block bootstrap **mean (expectancy) + median one-sided lower bounds in one pass** (`moving_block_bootstrap_cis`, `alpha=0.10` → 5th-pct lower bound = `Z=1.645`) + `default_block_length` | `xen.ass` | reused **unchanged** — the estimator being calibrated (the binding D6 inference); `expectancy_lo`=binding mean leg, `median_lo`=disclosed median leg |
| `seed_for` (deterministic per-(cell,arm,null,purpose,draw) seeding) | `xen.referee_calibration` | reused unchanged |
| `wilder_atr` (Wilder ATR(14)) | `xen.zigzag` | reused unchanged |
| Exit mechanisms for the 5 unified-engine arms (RCT/ERT trailing limits, ATR static barrier, RSI-revert close condition, fixed-bar cap) | composed in `run_experiment.py` over `xen.intrabar_fill` + `xen.mean_reversion` helpers | new composition; readiness + calibration only (no cost, no expectancy). The two-leg `xen.capgeo_cost.partial_two_leg_exit` arm is **deferred to EXP-091** |
| **`xen.intrabar_fill`** — timestamp-aligned domain→1m fill engine, causal order-of-touch, conservative adverse-first tie-break | **new (the one justified shared module, D2.5)** | new; reused by EXP-091 native + ATR-barrier arms |
| **`wilder_avg_gain_loss(close, 2)`** + **`reversion_completion_target(close, 2)`** (RCT) | **small additions** to `xen.mean_reversion` | new deterministic helpers (RCT closed-form from Wilder `(AG,AL)`); the ERT target reuses the existing `wilder_ema(Close,10)` — no new function |
| Per-cell two-null + planted-edge calibration substrate; FPR/MDE classifier; readiness battery | new | the experiment-local helper (within the ≤2 module budget) |

No new shared `xen` module beyond `xen.intrabar_fill` and the two small native-target helpers. No frozen entry
generator or exit primitive is modified. **No new referee is built or tuned** (D4: the frozen suite stays binding
downstream; `ASS` is non-binding, not invoked here).

---

## Methodology

### Step 0 — Dependency gate + holdout-fenced TRAIN domain construction

- **Method.** Hard-fail unless EXP-080 `results/run_metadata.json` records `READINESS_DELIVERED` and
  `ready_map.csv` shows all 16 instruments × {15m,1h} READY (the 32 member cells; the only EXP-080
  `COVERAGE_EXCLUDED` cells are 4h, excluded by domain). Per instrument: `pl.scan_parquet`; read `total_rows`
  from metadata; `analysis_rows = int(total_rows·0.7)`; `train_cutoff = int(analysis_rows·0.7)`; collect only the
  first `train_cutoff` file-order 1-minute rows; assert `CloseTime` sorted; set `train_edge_ts` = last collected
  `CloseTime`. Build 15m/1h domain bars via `build_domain_bars` (`min_coverage=0.90` + drop any window whose
  label > `train_edge_ts`). **Regression check (binding, before any substrate read):** domain-bar counts
  reconcile to EXP-080 on ≥1 shared 15m/1h cell.
- **Why.** The fence is the ratified VAL-005 G1 finding CF-CAPGEO-001/CF-MR-001 inherit; re-deriving construction
  would risk divergence from the validated path. The 1m base series is retained (clipped at `train_edge_ts`) as
  the intrabar fill source.
- **Simpler alternative considered.** Plain `aggregate_ohlc` without the fence — rejected (VAL-005 G1: the
  tolerant 0.90 path leaks a trailing partial window's nominal label past the slice; the fence is mandatory).
- **Output.** Per (instrument × domain): fenced domain frame + the 1m TRAIN slice + `train_edge_ts`; dependency
  + reconciliation confirmations in `run_metadata.json`. The final-30% global holdout (and its 1m bars) is never
  materialized — only Parquet metadata locates the split.

### Step 1 — Frozen CORE fade entries + invariant battery (deterministic; readiness A.1)

- **Method.** Per cell, generate the **CORE** fade entry population via `mean_reversion_entries(close, ...)["CORE"]`
  on the fenced domain `Close` (long `RSI₂<10`, short `RSI₂>90`; period 2/extremes 10/90, frozen). Assert: all
  entry timestamps within `[analysis_start, train_edge_ts]`; entries on completed-bar closes only; the RSI₂
  threshold condition holds at each entry (recompute and check); **causality** (no entry field derives from a bar
  with `CloseTime` after the entry); MR-tempo-cap warmup events (`< MR_MIN_EPISODES` completed episodes) excluded
  and disclosed; no NaN/null; events monotone in `CloseTime`.
- **Why.** Look-ahead safety and structural correctness are boolean properties — the readiness standard
  (EXP-080). The entry is the frozen object under test; **port, never re-derive** (EXP-042 framing lesson).
- **Output.** Per-cell entry table (indices, direction, entry close, entry ATR, MR-tempo cap), produced twice
  (Step 5 determinism); per-cell pass/fail per invariant with the first violating event on any failure.

### Step 2 — Exit-substrate construction (the new D2.5 component; readiness only — NO expectancy)

Build the **frozen D2 exit slate** and the **`xen.intrabar_fill`** engine, then resolve every member event
through every arm for **readiness only** (no net/gross return, no cost, no selection).

- **Native targets (primary hypothesis).**
  - **EXIT-RCT** — `P*_t = Close_t + (AL_t − AG_t)` (long) / `Close_t − (AG_t − AL_t)` (short), where
    `(AG_t, AL_t)` come from a new deterministic `wilder_avg_gain_loss(close, 2)` helper (the additive Wilder
    period-2 average gain/loss arrays underlying `wilder_rsi`). Recomputed each domain bar after entry → trailing
    limit. **Correctness invariant (readiness check):** on a bounded sample of post-entry bars, assert the RSI₂
    implied by reaching `P*_t` equals **50** within tolerance (`|rsi2_at(P*) − 50| ≤ 1e-6`) — the closed-form's
    defining identity, validating the new helper + formula.
  - **EXIT-ERT** — `M_t = wilder_ema(Close, 10)` (param #1), recomputed each domain bar → trailing limit.
- **Conventional contrast (built + calibrated here through the unified engine).** RSI-revert-on-close (favourable
  exit at the domain close when RSI₂ crosses 50); fixed-bar (cap-only — close at the MR-tempo-cap horizon);
  ATR triple-barrier (`1.0×ATR` favourable / `2.0×ATR` adverse, **time barrier = the MR-tempo cap** per
  `D0-amendment-001`). **The two-leg favourable partial/trail arm (`capgeo_cost.partial_two_leg_exit`) is DEFERRED
  to EXP-091** — its two-leg favourable resolver is structurally different from the unified single-favourable-touch
  `xen.intrabar_fill` engine, and EXP-090's binding MEMBER gate keys only on the native arms (RCT/ERT), so the
  five unified-engine arms (RCT, ERT, ATR-barrier, RSI-revert, fixed-bar) cover the readiness + calibration need.
  EXP-091 builds and screens partial/trail with its two-leg resolver + cost together.
- **Adverse side (frozen, identical across ALL arms, D2.3):** stop `2.0×ATR(14)` from entry + the EXP-089 causal
  MR-tempo cap (`mr_tempo_caps`, mult 1.0, FLOOR 3, MAX 40, EPISODE_WINDOW 20); exit-on-close at cap.
- **`xen.intrabar_fill` engine (new).** Map each domain bar → its constituent 1-minute bars **by timestamp**
  (`CloseTime` within `[domain.OpenTime, domain.CloseTime]`; assert — **never bar index**). Walk 1m bars forward
  from entry in chronological order; within each 1m bar test whether the favourable target and/or the adverse
  stop lie in `[Low, High]`; if both, resolve by the **conservative adverse-first tie-break** (the EXP-054
  fill-model question at 1m granularity). Fill price = the target/stop **level** (assert ∈ `[Low, High]` of the
  touching 1m bar — a real touched price, never the 1m close, never synthetic). Causal: only 1m bars with
  `CloseTime` ≤ `train_edge_ts` and ≥ entry; **assert no 1m bar past `train_edge_ts` is read** (holdout-fence).
- **Readiness battery (deterministic, per cell × arm):**
  1. **Resolution completeness** — every member event resolves to exactly one terminal (favourable fill / adverse
     stop / cap-close); resolution rate reported (denominator = member events); an unresolved event is a flag, not
     a silent drop.
  2. **Timestamp alignment** — assert the 1m→domain mapping is by `CloseTime`, never index (a deliberate
     bar-index variant must mismatch — a negative control on the mapping).
  3. **Causality + fence** — assert no 1m bar past entry-or-`train_edge_ts` is consulted.
  4. **Fill-price validity** — every fill ∈ `[Low, High]` of its touching 1m bar.
  5. **Tie-break incidence** — fraction of events whose terminal 1m bar held both barriers (conservative
     adverse-first applied); recorded per cell × arm.
- **Why.** EXP-091's native intrabar targets and the ATR-barrier arm depend on this engine; readiness must prove
  it resolves deterministically, causally, by timestamp, with real fill prices, before any edge read.
- **Explicit non-goal.** **No net or gross expectancy, no `capgeo_cost`/`financing` overlay, no exit selection,
  no quorum** — those are EXP-091. Step 2 emits only the resolution/timestamp/tie-break readiness records.
- **Output.** `exit_substrate_readiness.csv` (per cell × arm: resolved fraction, tie-break incidence, fill-price
  validity, fence flags, determinism), produced twice (Step 5).

### Step 3 — Per-cell calibration substrate: two structurally-different nulls + planted edge (the only new inference logic)

The binding object is the **mean** net per-event expectancy moving-block bootstrap one-sided lower bound
(`Z=1.645`; D5/D6); the **median** lower bound is co-reported (the family is median-positive / mean-fragile,
EXP-089 — both legs disclosed, never pooled, LESSON-001). The calibration is a **pure estimator
operating-characteristic** measurement: at each cell's realized event count and the real exit-resolved
return-shape, how often does the lower bound exceed 0 when the true location is 0 (FPR), and what is the smallest
true location detectable at TPR ≥ 0.80 (MDE)?

- **Per-event return shape (fence-clean; pooled once, not per-draw).** The estimand is the
  operating-characteristic of the moving-block bootstrap lower bound on the real exit-resolved per-event
  net-return SHAPE at the realized count. Per-draw matched-random placement + 1m resolution (EXP-070 style) is
  **computationally infeasible here** — the new 1-minute intrabar walk makes it ~10¹³ ops. So the **matched-random
  pool is resolved ONCE per (cell × arm × path)** through the actual frozen exit machinery + the `xen.intrabar_fill`
  engine into the **pooled per-event net-return series in entry-time order** (the real heavy-tailed,
  exit-geometry-shaped distribution EXP-091 will see), and the calibration **draws are moving-block resamples of
  that pooled series** (below). The pool is matched-random fade-direction entries from the **eligible bar pool**
  (completed domain closes, non-warmup for RSI/EMA/ATR/MR-tempo, ≥ `MR_CAP_MAX` forward domain bars so any cap
  fits, **excluding the real CORE fade entries**), capped at `N_POOL_MAX = 6000` by a deterministic
  time-order-preserving systematic subsample. **Real FADE-entry outcomes are never resolved or read by EXP-090**
  (the random entries are not the signal — anti-overfitting fence).
- **Null A — real exit path, true-location-0 (moving-block resample of the pooled shape).** Resolve the pool on
  the **real** 1m path → `R_real`; recentre to exactly 0 by subtracting the pooled mean `μ̂_base` (a fixed
  per-(cell × arm) baseline — the EXP-044 "matched-control subtraction → true 0" principle as a fixed-baseline
  recentre), preserving the real dispersion/tail shape. Each of the 1000 draws is a **moving-block resample of
  length `n_cal`** from the centred `R_real` (block length `xen.ass.default_block_length(len(R_real))`),
  preserving serial dependence. The bootstrap lower-bound FPR is then a clean type-I object at true-location-0.
- **Null B — block-rotated path, true-location-0.** Resolve the **same** matched-random pool against a
  **block-circular-rotated** 1m path (whole bars rotated in contiguous blocks by a random offset; each bar stays
  internally valid — `High ≥ max(O,C)`, `Low ≤ min(O,C)` — while the entry↔path alignment is broken) → `R_rot`;
  recentre by its own `μ̂_base`; draws are moving-block resamples of `R_rot`. Null A holds the path (resampling
  the real-path shape); Null B permutes the **path** before resolution (a structurally different dependence
  channel), both true-location-0 (the EXP-001/027/044/070 two-null requirement). **This draw-generation
  (pooled-resolution + moving-block-resample-to-true-0) is the only divergence from the original plan text; it
  preserves the estimand exactly** — FPR at true-0, MDE at TPR≥0.80, real shape + serial dependence, two
  structurally-different nulls — and only avoids the infeasible per-draw 1m re-placement (deviation flagged in
  `governance/pre-execution-review.md`).
- **Planted edge (recovery / MDE).** Base = Null-A `g = 0` draws. Add a known **direction-signed ATR-normalised
  drift `g`** to each event's per-event return (outcomes only — never placement/matching), via
  `referee_calibration.plant_positive_edge`. **Edge grid (ATR units, geometric, fixed now to avoid post-hoc
  extension):** `g ∈ {0, 0.0125, 0.025, 0.05, 0.10, 0.20, 0.40, 0.80}` ATR. Rationale: the fade's gross
  favourable `MFE_med` ≈ 0.75 ATR but net per-event expectancy is far smaller (most excursion uncaptured, cost
  bites); a plausible net edge is ~0.05–0.30 ATR — the grid's centre — with `0.0125` for the dense 15m cells
  (n up to ~10⁴ can detect tiny edges) and `0.80` declared for thin cells with large MDEs.
- **Translation-equivariance shortcut (compute structure only; no statistical object changes).** The moving-block
  bootstrap **mean and median are translation-equivariant**: adding `g` to every per-event return shifts the
  whole bootstrap distribution (and `ci_low_1s`) by exactly `+g`. Therefore `ci_low_1s(g) = ci_low_1s(0) + g`,
  and `TPR(g) = fraction of Null-A draws with ci_low_1s(0) > −g`. **The bootstrap runs once per draw at `g = 0`**;
  the whole grid is read off the stored `ci_low_1s(0)` — exact, not approximate (EXP-070's shortcut). **This same
  equivariance is why the calibration is faithfully cost-free** (scope exclusion: cost enters at EXP-091): cost is
  a per-event location shift, and the FPR (true-location-0 type-I rate) and the MDE (a CI-**width** property) are
  invariant to a location shift — so the gross-shape calibration yields a valid MDE for the **net** statistic.
- **Draws.** **1000 moving-block resamples per (cell × arm × null)**, each of length `n_cal`; the same 1000
  Null-A draws are reused for every `g` (translation shortcut). Seeds via
  `seed_for(EXP-090, instrument, domain, arm, null, purpose, draw_index)` (master seed `20260623`), disjoint
  purpose-blocks for the pool, the per-draw resample, and the inner bootstrap. **Precision (met by construction at
  1000 complete draws):** Wilson 95% half-width ≈ **0.0135** at FPR = 0.05 (≤ 0.03 target) and ≈ **0.025** at
  TPR = 0.80 (≤ 0.05 target).
- **Compute cap (conservative tier).** `n_cal = min(realized usable count, N_CAL_MAX = 4000)`; the
  matched-random pool that supplies the shape is capped at `N_POOL_MAX = 6000`. Capping `n_cal` is conservative:
  fewer events → wider CI → **larger** MDE and a more-stressed FPR, so the reported margin is an upper bound on
  the realized-count margin and no cell is wrongly admitted. Both caps are declared, recorded per cell, never
  silent. (EXP-044/070 realized-count precedent, with the draw being a resample rather than a re-placement.)
- **Per-draw reportability.** A draw is reportable iff its resample length ≥ `POWER_FLOOR = 15` (the D8 floor) and
  the inner moving-block bootstrap is defined; below floor → excluded from FPR/TPR numerators and denominators.
  The pool itself must have ≥ 15 finite resolved returns for the (cell × arm × null) point to compute.
  **Draw-completion floor:** a (cell × arm × null) point is usable only if ≥ 90% of its 1000 draws are
  reportable; else the point — and, if a native-arm point, the (cell) — is `CALIBRATION_UNDERPOWERED` with the
  rate recorded. No silent drops.
- **Output.** `calibration_draws.parquet` (bounded: cell, arm, MDE, fpr_controlled_both, the per-`g` TPR row) and
  `fpr_mde_per_cell.csv` (per cell × arm × null: binding mean FPR + disclosed median FPR with Wilson bounds,
  pool size, completion, event-level MDE + margin).

### Step 4 — Per-cell operating characteristics + member classification

- **Binding FPR (per cell × arm × null).** `FPR_mean` = fraction of reportable null draws with
  `mean_ci_low_1s > 0`; Wilson 95% interval. Primary α₀ = 0.05; {0.10, 0.01} reported within budget. The
  **median-leg FPR** (`median_ci_low_1s > 0`) is co-reported as a disclosed diagnostic (D5 co-report; never
  gates).
- **TPR / MDE (per cell × arm).** Via the translation shortcut on Null-A draws: `TPR_mean(g)`; **per-cell × arm
  event-level MDE(α₀)** = the smallest `g` with `TPR_mean ≥ 0.80` while the **binding mean FPR ≤ α₀ under both
  nulls**; non-finite (`null`, never 0) if no grid point qualifies or the FPR is uncontrolled. The median-leg MDE
  is co-reported (diagnostic).
- **Calibrated margin (the EXP-093 input, D6 4c).** For each (cell × arm), `margin_atr` = the cell × arm
  **event-level MDE** under the binding mean statistic — this is the exact "EXP-090-calibrated MDE" the EXP-093
  PASS rule uses (`ci_low_1s > margin`). Recorded in `member_map.csv` and `run_metadata.json`.
- **Precision gate.** Wilson half-width on the **binding mean FPR** ≤ 0.03 and on TPR ≤ 0.05; else
  `CALIBRATION_UNDERPOWERED` (precision/variance only, fixable by a draw-count-only re-run — never a
  point-estimate failure).
- **Per-cell verdict (exhaustive, unambiguous):**
  - **MEMBER** (carries to EXP-091): construction integrity PASS (dropped ≤ 0.25, fence held) ∧ 0 entry-invariant
    violations ∧ exit-substrate readiness PASS for all arms (resolve, deterministic, timestamp-aligned, fence
    held, fill prices valid) ∧ coverage `IN_FLOOR` (≥ 15 non-warmup events) ∧ **binding mean FPR ≤ α₀ under both
    nulls on ≥ 1 native arm** ∧ a **finite event-level MDE on ≥ 1 native arm** (RCT or ERT — the primary
    hypothesis must be powered). All 5 unified-engine arms' FPR/MDE recorded (partial/trail deferred to EXP-091);
    the carried margin is the carried (cell, arm) MDE.
  - **`COVERAGE_EXCLUDED`** (excluded from EXP-091–093, with record): construction FAIL (dropped > 0.25), or
    coverage `OUT_LOW` (< 15), or no finite MDE on **either** native arm, or binding mean FPR uncontrolled
    (> 0.05 point estimate, precision-adequate) on **both** native arms. Recorded with the failing check.
  - **`CALIBRATION_UNDERPOWERED`**: precision or draw-completion-floor shortfall only.
  - **`CONSTRUCTED_EMPTY`** (cell-level inconclusive): TRAIN slice shorter than detector warmup; recorded, not
    NOT_READY.
- **Two-null disagreement diagnostic (caveat, not an auto-defect).** Non-overlapping Wilson 95% FPR intervals at
  α₀ with both precision-adequate. Before reading disagreement as a method problem, check whether Null-B excess
  tracks low event count / few rotation blocks (rotation distortion is worse with fewer blocks) — a count-graded
  pattern points to a rotation artifact, a flat pattern to genuine method failure (EXP-044/070 lesson).
- **Output.** `fpr_mde_per_cell.csv` (per cell × arm × null: binding mean FPR + disclosed median FPR, Wilson
  bounds, completion; event-level MDE + margin), `member_map.csv` (verdict + machine-readable reason + carried
  margins).

### Step 5 — Determinism replay + metadata

- **Method.** Re-run two fixed cells (one high-count 15m, one lower-count 1h) with identical seeds; assert
  frame-identical entry tables, frame-identical exit-resolution tables (all arms, incl. the 1m walk), and
  identical per-draw calibration verdicts / FPR / MDE (`determinism_pass`). A **full second pass** reproduces every
  headline output **byte-identical** (D9); SHA-256 of the headline outputs recorded (hash-pin). `run_metadata.json`
  records the edge grid, seeds/purpose-blocks, draw and `N_BOOT` counts, block lengths, `N_CAL_MAX`, the
  dependency + reconciliation + fence confirmations, per-cell headline, `holdout_untouched=true`,
  `counted_test_reads=0`, `candidate_slots=0`, and the experiment verdict.

---

## Visualisations (4 / 4 budget)

1. **MEMBER-status heatmap** (16 × 2, 15m/1h) — MEMBER / `COVERAGE_EXCLUDED` / `CALIBRATION_UNDERPOWERED` /
   `CONSTRUCTED_EMPTY`. Answers "which cells carry to EXP-091?"
2. **Entry-rate + coverage map** (16 × 2) — entries per 1,000 domain bars with the ≥ 15 non-warmup floor marked.
   Answers "how dense is the fade stream, and which cells fall below floor?"
3. **Per-cell event-level MDE heatmap** (16 × 2, native arms RCT/ERT faceted; `COVERAGE_EXCLUDED` hatched,
   FPR-uncontrolled cells cross-hatched) with an inset **MDE vs realized event count** scatter — the recovery read
   and the EXP-093-margin map.
4. **Exit-substrate readiness + tie-break summary** (per arm: resolution rate and tie-break incidence across
   cells) paired with the **binding mean FPR** distribution (vs the α₀ line, both nulls). Answers "does the 1m
   engine resolve cleanly, and is the binding estimator error-controlled?"

All plots built from the single analysis pass's bounded summaries (no data reloads).

---

## Interpretation Guide (pre-defined, before results exist)

- **`READINESS_CALIBRATION_DELIVERED` (expected).** The 32-cell MEMBER / `COVERAGE_EXCLUDED` /
  `CALIBRATION_UNDERPOWERED` map, the entry-coverage table, the per-arm exit-substrate readiness + tie-break
  table, the per-cell × arm FPR + event-level MDE + carried margins, and the byte-identical determinism replay are
  produced — whatever the mix. MEMBER cells (with their carried margins) define the EXP-091 grid; `COVERAGE_EXCLUDED`
  cells are excluded **with record** (a thin/fast `COVERAGE_EXCLUDED` cell is a valid, expected outcome —
  information, not defect; this is the EXP-093-margin power map the phase needs).
- **A finite MDE alongside a controlled mean FPR** is the designed reading: the binding mean lower bound recovers
  a planted edge at the cell's count and does not over-fire at true-0. A **non-finite MDE** (no grid point reaches
  TPR ≥ 0.80 at controlled FPR) means the cell cannot bound a confirmation at its realized count → `COVERAGE_EXCLUDED`
  (à la EXP-044 BTCUSD-4h) — the honest power verdict, never a defect to "fix" by re-picking the statistic.
- **Process-level HALT (Evidence AGAINST).** Predeclared triggers — **fix + full rerun (dated `D0-amendment-*`
  if a frozen-design confound), 0 reads spent:** non-determinism on **any** cell or calibration draw; the same
  entry/exit invariant violated on **≥ 3 instruments**; the two nulls disagree on binding-mean-FPR control beyond
  tolerance in **≥ 3 instruments**, or a systematic mean-FPR excess across an entire domain in precision-adequate
  cells (the per-cell estimator itself invalid, à la EXP-044 `METHOD_NOT_TRANSFERABLE`); the moving-block null-FPR
  uncontrolled (Wilson-hi > 0.075) at any `n ≥ 120`; **or** any timestamp-vs-index misalignment, look-ahead, or
  holdout-fence breach in the 1m engine. Any of these halts Phase 021 pending a fix.
- **`INCONCLUSIVE`.** The map is produced but **> 1/3 of cells** (≥ 11) are `CALIBRATION_UNDERPOWERED` — operator
  decides a precision-only re-run (more draws, no object change) vs. a reduced EXP-091 grid.
- Report ATR-unit effects and absolute rates with CIs; non-finite MDE reported as such (never 0); **never a
  percentage over the 0-ATR null baseline.** Per-stratum doctrine (LESSON-001): no collapsed cross-cell boolean is
  binding; pooled counts are disclosure only.

**Predeclared interpretation caveats (read before any verdict):**

1. **The calibration certifies the estimator, not a market edge.** A MEMBER verdict says the binding mean
   lower-bound estimator is error-controlled and has a finite MDE on this cell's event population at a
   representative per-event scale — it makes **no** claim that the real fade has any edge (that is EXP-091/092/093,
   on real outcomes). The fence guarantees no real fade outcome informed the calibration.
2. **Cost-free calibration is faithful by translation-equivariance.** Cost is a per-event location shift; the FPR
   (true-0 type-I rate) and the MDE (a CI-**width** property) are location-invariant, so the gross-shape
   calibration yields a valid **net** MDE/margin. The actual EXP-085 cost model enters the **real** statistic at
   EXP-091 — never here (scope exclusion).
3. **The median leg is co-reported, non-binding.** D5/D6 make the **mean** net-expectancy lower bound binding
   (tradability needs a positive mean net of cost); EXP-089 flagged the family median-positive / mean-fragile, so
   the mean leg is deliberately the hard bar. The median FPR/MDE are disclosed context, never a gate, and the two
   are never pooled.
4. **Null B is a different dependence structure, not the same with more noise.** Block rotation preserves per-bar
   OHLC validity but breaks entry↔path continuity; with few blocks (thin 1h) it distorts more. Grade any two-null
   disagreement against event/block count before declaring a method failure (Step 4 diagnostic).
5. **`N_CAL_MAX` is conservative.** Calibrating a high-count 15m cell at 4000 events yields a **wider** CI and a
   **larger** MDE/margin than its realized count would — a higher (harder) EXP-093 bar, never an admission
   shortcut. Recorded per cell.

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout / TEST.** Load only `floor(0.7·floor(0.7·total))` file-order 1-minute rows (TRAIN sub-split) before
  any domain/1m-fill construction; the analysis-TEST stratum and the final-30% global holdout (incl. its 1m bars)
  are **never** loaded — only Parquet metadata locates the split. Assert the fence (no domain label and no
  consulted 1m bar past `train_edge_ts`) per cell. **0 counted TEST reads** — verified against
  `test-read-ledger.md` (all 48 strata stay 0/2).
- **Anti-overfitting fence (binding).** Real **fade-entry** outcomes are **never** read by EXP-090; the
  calibration reads only **matched-random-entry** exit-resolved returns (random placement, not the signal) for the
  return shape. Planted drift touches **outcomes only**, never placement/matching. Placement uses only
  bar-time information (eligible pool, direction, ATR/MR-tempo state ≤ entry).
- **Temporal ordering / alignment.** Order and align by `CloseTime` only; the 1m→domain mapping is by timestamp
  (assert; a bar-index mapping must fail the Step-2 negative control). Never bar index. Assert input sorted before
  slicing.
- **Real-price discipline.** Every excursion / fill / stop / ATR / calibration-return figure is on **real** OHLC
  (`RealOpen/High/Low/Close`; real 1m OHLC for fills). RCT is a **model-derived target price**, but the **fill
  price is a real touched level** (assert ∈ `[Low,High]`) — not synthetic, not the 1m close. No HA/Renko metric.
- **No cost / no expectancy / no selection in EXP-090.** `xen.capgeo_cost` / `xen.financing` are **not** imported;
  no net/gross strategy expectancy on real fade outcomes; no exit screened/ranked/selected; no quorum, candidate
  set, or Holm rule. (Those are EXP-091/092.)
- **Determinism.** All randomness via `seed_for` / the recorded seed convention; replay asserted on two cells and
  a byte-identical full second pass (incl. the 1m walk + the calibration draws); headline SHA-256 hash-pinned.
- **Performance / vectorization.** Precompute per cell once: domain bars, the 1m slice, RSI(2)/EMA(10)/ATR(14),
  the MR-tempo cap, the eligible pool, and the `μ̂_base` baseline; per draw reduces to index selection + the reused
  resolver + the chunked moving-block bootstrap (`BOOT_BATCH`), with the planted grid read off the stored
  `ci_low_1s(0)` (no re-bootstrap). The 1m intrabar walk must stay **sequential / causal** (no look-ahead
  vectorization that consults future 1m bars). Vectorize loading/aggregation/summary only. Ceiling: 32 cells × 6
  arms × 2 nulls × 1000 draws × `N_BOOT=10_000`, with the `N_CAL_MAX=4000` event cap and the bootstrap-once-per-draw
  shortcut bounding cost; `tqdm` over the (cell × arm × null) outer loop with per-cell postfix; concise logging;
  helpers return data; bounded per-cell memory (do not retain all 32 domain/1m frames simultaneously).
- **No silent drops.** Unreportable draws, below-floor cells, capped cells, two-null disagreements, unresolved
  exit events, and any reconciliation/fence-gate failure are recorded with reasons.

---

## Complexity Check

- **Statistical tests: 1 binding / 1 budget.** The single binding object is the **moving-block bootstrap
  one-sided lower bound** (mean, binding; median co-reported) — the D6 inference under calibration. Its
  operating-characteristic measurements (Wilson FPR/TPR intervals, grid-defined MDE) are calibration readouts of
  that one estimator, not additional market-edge hypothesis tests (EXP-080/044 framing). **None gates a market
  edge** (readiness/calibration; design §5 "EXP-090 0").
- **Visualisations: 4 / 4** as listed.
- **New modules: ≤ 2 / 2** — (a) `xen.intrabar_fill` (the timestamp-aligned 1m fill engine, D2.5); (b) the small
  native-target helpers added to `xen.mean_reversion` (`wilder_avg_gain_loss` + `reversion_completion_target`),
  plus the experiment-local calibration/readiness logic in `python/experiments/EXP-090/code/run_experiment.py`.
  Reuse `xen.mean_reversion`, `xen.domain_bars`, `xen.ass` (moving-block bootstrap mean+median lower bounds),
  `xen.referee_calibration` (`seed_for`), and `xen.zigzag.wilder_atr` unchanged. (The ERT EMA-10 target reuses
  the existing `wilder_ema`; `xen.capgeo_cost.partial_two_leg_exit` is **not** imported here — the partial/trail
  arm is deferred to EXP-091.) **No new referee; no edits to frozen entry/exit generators.**

## Expected Output Files

```text
python/experiments/EXP-090/results/
- member_map.csv               # per-cell MEMBER / COVERAGE_EXCLUDED / CALIBRATION_UNDERPOWERED / CONSTRUCTED_EMPTY + reason + carried margins
- entry_coverage.csv           # entry count, entries/1k bars, non-warmup ATR-defined count, D8 flag, denominators
- exit_substrate_readiness.csv # per cell × arm: resolved fraction, tie-break incidence, fill-validity, fence/determinism flags
- fpr_mde_per_cell.csv         # per cell × arm × null: binding mean FPR + disclosed median FPR (Wilson) + event-level MDE + margin
- calibration_draws.parquet    # bounded per-draw rows (cell, arm, null/g, draw, count, mean_ci_low_1s(0), median_ci_low_1s(0), reportable)
- null_fpr_sanity.json         # moving-block null-FPR machinery sanity (n≥120 binding; small-n disclosed) — subsumed by per-cell FPR
- run_metadata.json            # status, dependency/reconciliation/fence gates, seeds, grid, draw/N_BOOT counts, block lengths,
                               #   N_CAL_MAX, determinism hash, holdout_untouched=true, counted_test_reads=0, candidate_slots=0, verdict
python/experiments/EXP-090/plots/
- member_status_heatmap.png
- entry_coverage_map.png
- mde_per_cell_heatmap.png
- exit_readiness_fpr_summary.png
```
