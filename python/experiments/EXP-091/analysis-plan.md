# Analysis Plan: Experiment EXP-091

**Phase 021 (CF-MR-001 batch 2) — RSI-2 fade exit / capture-geometry screen, gross + EXP-085 cost, 20 member
cells.** Scope frozen at [`scope.md`](scope.md); methods here only operationalize the **frozen D0/D6 rules** — no
new statistic, threshold, or selection rule is introduced (D0 header; no bite-check required).

## Objective

Over the frozen D2 exit slate (native pair **EXIT-RCT / EXIT-ERT** + conventional contrast **RSI-revert-on-close,
fixed-bar, ATR triple-barrier, favourable partial/trail**), evaluated on the **20 EXP-090 MEMBER cells** net of
the **EXP-085 conservative cost**, determine on TRAIN only:

1. **(binding)** Does **any** exit **net-clear** (`net ci_low_1s > 0`, `Z=1.645`, moving-block bootstrap) in a
   **quorum of ≥5 cells over ≥3 instruments** (D6/4a)? Empty screen ⇒ deliverable `SCREEN_EMPTY` → routes G-021
   **NOT_TRADABLE at 0 TEST reads**.
2. **(descriptive attribution)** Do the native intrabar targets beat the reactive contrast — especially **RCT vs
   RSI-revert-on-close**, the clean intrabar-resting-vs-exit-on-close A/B?

The honest prior is *availability ≠ capturable edge* (small ~0.75-ATR gross / ~3-bar horizon vs conservative
cost); an empty screen is an expected, fully-reportable outcome. **Per-stratum doctrine (LESSON-001): no pooled
boolean is binding; the per-(cell × arm) net-clears and the per-arm quorum are the verdict.**

## Methodology

### Step 1 — Resolve real per-event exit outcomes (first read of the real fade outcomes in Phase 021)

- **Method**: For each of the 20 member cells, build CORE fade entries
  (`xen.mean_reversion.mean_reversion_entries(...)["CORE"]`, frozen) on the TRAIN {15m,1h} domain bars; resolve
  each of the 6 frozen arms per event through the **EXP-090 `xen.intrabar_fill` engine** (reused verbatim,
  including the `D0-amendment-002` window-anchoring + gap-through-fill-at-1m-open fixes) to a terminal
  (favourable fill / adverse stop / cap-close). Record per event: terminal type, **gross** signed real-price
  return `dir·(fill_price − entry_price)/ATR_entry` in ATR(14) units, realized hold (bars + `holding_days`),
  MAE/`q05` adverse tail, favourable-capture fraction, tie-break flag.
- **Why this method**: Identical resolution path to EXP-090 (already determinism/fill-validity/timestamp-validated
  on all 32 cells × 5 arms) — the only addition is reading the real gross return off each terminal. The two-leg
  partial/trail (deferred from EXP-090) resolves via `xen.capgeo_cost.partial_two_leg_exit`.
- **Simpler alternative considered**: A bar-close-only resolution (no 1m engine) — rejected: it cannot resolve
  intrabar order-of-touch between favourable target and adverse stop, which is the entire point of the native
  intrabar targets (the EXP-054 fill-model question at 1m granularity) and would bias the RCT/ERT-vs-on-close A/B.
- **Assumptions**: causal 1m forward walk from entry; conservative adverse-first tie-break when both barriers lie
  in one 1m bar; real touched fill price ∈ `[Low,High]` (or gap-through 1m open). No distributional assumption.
- **Expected output**: `screen_per_cell_arm.csv` per-event roll-ups (n_events, resolution rate, tie-break
  incidence, terminal-type mix, gross mean+median).

### Step 2 — EXP-085 conservative cost overlay → net per-event return

- **Method**: Subtract the EXP-085 CONSERVATIVE cost per event via `xen.capgeo_cost` / `xen.financing` —
  round-trip transaction = `2× BASE` + per-instrument adverse-side financing bps/day on `holding_days` — using
  the inherited per-instrument `(RT_i, F_i)` table unchanged (D3). `net = gross − cost` in ATR units, per event.
- **Why this method**: Cost is the binding economic layer for a ~3-bar fade; the frozen EXP-085 model is the
  programme's ratified intraday cost model (not re-estimated to suit the fade — governance prohibition).
- **Simpler alternative considered**: A flat per-event cost — rejected: ignores holding-duration financing, which
  differs materially across arms (RCT/RSI-revert tend short; fixed-bar/cap longer), confounding the A/B.
- **Assumptions**: cost is a per-event ATR-unit **location shift** (additive), so the bootstrap location inference
  is valid on the net series. ATR-unit normalization makes the per-instrument bps cost commensurable.
- **Expected output**: `cost_decomposition.csv` (per cell × arm: gross → net, transaction vs financing,
  mean `holding_days`).

### Step 3 — Net-clear test: moving-block bootstrap one-sided lower bound (the binding screen figure)

- **Method**: Per (cell × arm), compute the **net per-event expectancy moving-block bootstrap one-sided lower
  bound** `net ci_low_1s` (`Z=1.645`; circular moving-block resample, block length `round(n**(1/3))` — the
  EXP-044/085/090 convention preserving serial dependence; `N_BOOT = 10000`, fixed seed). **Net-clears iff
  `net ci_low_1s > 0`** (D6/4a). Co-compute the **gross** `ci_low_1s` (descriptive sanity) and the net + gross
  **median** per-event expectancy (the family is median-positive / mean-fragile per EXP-089 — both legs disclosed,
  never pooled across cells; the binding figure is the mean lower bound, matching EXP-090's binding statistic).
- **Why this method**: Non-parametric, distribution-free, serial-dependence-preserving — the programme-standard
  expectancy lower bound (EXP-046/056 quorum, EXP-085 cost read). It is the exact statistic EXP-090 calibrated
  (FPR-controlled, finite per-cell MDE), so each member cell is powered for it by construction.
- **Simpler alternative considered**: i.i.d. bootstrap / analytic t-interval — rejected: fade-event returns are
  serially dependent (clustered entries) and non-normal; an i.i.d./normal interval would understate uncertainty
  and inflate false net-clears. (Methods-catalog: prefer bootstrap CI; avoid t-test without cross-validation.)
- **Assumptions**: events within a cell are exchangeable in blocks (block bootstrap handles within-block
  dependence); `n` per cell is in the powered regime (EXP-090 membership already guarantees a finite MDE at the
  realized count; `n<120` cells carry the EXP-077/078 small-n disclosure, not a control failure).
- **Expected output**: `screen_per_cell_arm.csv` columns `gross_exp_mean, gross_exp_median, net_exp_mean,
  net_exp_median, gross_ci_low_1s, net_ci_low_1s, net_clear (bool)`.

### Step 4 — Per-arm quorum (the screen pass rule)

- **Method**: Per exit arm, count net-clearing cells and the **distinct instruments** among them. **Arm PASSES
  iff net-clears in ≥5 cells over ≥3 instruments** (frozen D6/4a quorum). Tabulate per arm.
- **Why this method**: The established EXP-046/056 breadth rule — a lucky single cell or instrument cannot pass an
  arm; replication across instruments is required.
- **Assumptions**: none beyond Step 3. The denominators (20 member cells, 13 instruments) are disclosed; an arm
  with `UNRESOLVED_EMPTY` on a cell simply does not net-clear there.
- **Expected output**: `quorum_per_arm.csv` (per arm: net-clearing cell count, distinct-instrument count,
  PASS/FAIL). The set of (passing arm, net-clearing cells) is the EXP-092 hand-off (no selection performed here).

### Step 5 — Native-vs-contrast attribution (descriptive; not a gate)

- **Method**: (a) Compare per-arm net-clear counts (native pair vs reactive contrast). (b) For the clean
  **RCT vs RSI-revert-on-close** A/B, compute the **per-cell paired net-expectancy delta** (Δ = net_exp_mean[RCT]
  − net_exp_mean[RSI-revert] on the same cell's matched events) across the 20 cells; summarize with a
  **Wilcoxon signed-rank** test (paired, non-parametric) and the median Δ with a bootstrap CI — **reported as
  attribution only**, never gating the verdict.
- **Why this method**: Wilcoxon signed-rank is the non-parametric paired comparison (methods-catalog) appropriate
  for matched per-cell deltas without a normality assumption; it answers "does proactive resting + intrabar fill
  buy net capture over reactive exit-on-close?" descriptively. This is the ≤2nd binding-budget test slot but is
  **explicitly non-binding** (the verdict is the Step-4 quorum).
- **Simpler alternative considered**: Sign test — weaker; or pooling all events across cells — rejected
  (LESSON-001: no cross-cell pooling as a binding/relied-upon statistic; paired-by-cell respects stratification).
- **Assumptions**: paired deltas are matched by cell (same instrument/domain/entry population, different
  favourable leg — the adverse side is identical by D2.3, so Δ isolates the favourable target). Symmetric-
  difference assumption is weak but acceptable for a descriptive read.
- **Expected output**: `native_vs_contrast.csv` (per-cell Δ for RCT−RSI-revert and the other native−contrast
  pairs; Wilcoxon W, p, median Δ + CI as a disclosure summary).

### Step 6 — Faster-turnover cost sensitivity (disclosed companion, non-binding)

- **Method**: Re-run Steps 2–4 under a single predeclared **faster round-trip** cost variant (fixed before
  measurement: round-trip = `1× BASE` instead of `2× BASE`, financing unchanged), reporting net `ci_low_1s` and
  the per-arm quorum. Reported **alongside** the binding result, never substituted.
- **Why this method**: Bounds how sensitive an empty/non-empty screen is to the conservative cost assumption
  (D3 disclosed companion) without re-estimating the binding model.
- **Expected output**: `cost_sensitivity_faster.csv`.

### Step 7 — Determinism replay

- **Method**: Full second regeneration of every cell's entries, the complete 1m exit resolution for all arms, the
  cost overlay, and the bootstrap stream (fixed master seed `20260623`; per-(cell,arm) seed = deterministic hash
  of `(cell, arm, replicate)`); assert the per-event and per-(cell × arm) tables compare **frame-identical**
  (exact); SHA-256 hash-pin the headline outputs.
- **Expected output**: `run_metadata.json` (`determinism_ok=true`, hashes, seeds, module versions,
  `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`).

## Visualisations (≤ 4, from the single analysis pass's bounded plot inputs — no reloads)

1. **Per-arm net-clear quorum bar** — net-clearing cells (and distinct instruments) per arm vs the ≥5/≥3 rule
   lines. *Answers: does any arm pass, and which?*
2. **Per-(cell × arm) net `ci_low_1s` heatmap** (20 cells × 6 arms) with the 0 line / sign marked. *Answers:
   where does net edge survive cost, and is it concentrated or broad?*
3. **Gross → net cost decomposition** per arm (gross `ci_low_1s` vs net, with transaction/financing split).
   *Answers: does cost kill the gross edge, and via transaction or financing?*
4. **RCT vs RSI-revert-on-close paired net-expectancy scatter** (one point per cell, y=x line). *Answers: the
   intrabar-resting-vs-exit-on-close A/B.*

## Interpretation Guide (predefined, before results exist)

- **≥1 arm PASSES the quorum (≥5 cells / ≥3 instruments net-clear)** ⇒ `SCREEN_DELIVERED` with a non-empty
  surviving set → the surviving arm(s) + their net-clearing cells carry to EXP-092 (per-instrument sequence +
  hash-pinned candidate set). *Capture lever is non-empty on TRAIN net-of-cost.*
- **No arm passes the quorum** ⇒ `SCREEN_DELIVERED` + `SCREEN_EMPTY` → routes **G-021 NOT_TRADABLE at 0 TEST
  reads**. *The fade's gross availability does not convert to a net edge on this dataset; with regime inert and
  variants dead, CF-MR-001 is effectively exhausted (design §6).* This is a valid, expected outcome.
- **Native beats contrast** (RCT/ERT net-clear more cells than the reactive arms; RCT > RSI-revert-on-close on the
  paired Δ, Wilcoxon p small, median Δ CI > 0) ⇒ proactive intrabar resting buys net capture — the phase's
  organizing hypothesis is supported *descriptively* (not a gate). **Contrast ≥ native** ⇒ the intrabar machinery
  earns nothing; report plainly.
- **A cell net-clears gross but not net** ⇒ cost is the binding constraint (the expected ~3-bar-horizon failure
  mode); attribute to transaction vs financing via Step 2.
- **Mean-vs-median split** (median > 0 but mean `ci_low_1s` ≤ 0) ⇒ the EXP-089 median-positive/mean-fragile
  signature persists into the net exit; the **mean lower bound is binding** (matches EXP-090) — disclose the
  median, do not promote on it.
- **Process-level HALT** (timestamp-vs-index misalignment, look-ahead, holdout-fence breach, non-determinism,
  fill outside `[Low,High]`, real-price violation) ⇒ stop; dated `D0-amendment-*` + hard-delete + full rerun if a
  frozen-design confound (programme norm, as EXP-090).

## Implementation Safety Constraints (for experiment-developer)

- **Holdout:** read only `[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)`, via metadata-located
  slice; assert `CloseTime` sorted; set `train_edge_ts`; **never slice the analysis-TEST stratum or the final-30%
  global holdout** (incl. 1m fill bars — clip the 1m walk by `train_edge_ts` timestamp, never by 1m index).
- **Timestamp alignment:** domain→1m mapping by `CloseTime`/`SourceCloseTime` only; assert no bar-index alignment
  (carry the EXP-090 assertion). Cross-view never by bar count.
- **Causality:** RSI(2)/EMA(10)/ATR(14)/MR-tempo cap use bars `≤ i`; RCT uses Wilder `(AG_t,AL_t)` through bar
  *t*; ERT uses EMA-10 through bar *t*; the 1m fill walk consults only bars at/after entry. RNG/bootstrap never
  consult future data.
- **Real-price discipline:** all returns/fills/stops/ATR on real OHLC (`RealOpen/High/Low/Close`, real 1m OHLC);
  no HA/Renko synthetic price anywhere; assert every fill ∈ `[Low,High]` of its touching 1m bar (or the
  gap-through open) — the EXP-090 D2.5 invariant, re-checked here.
- **Denominators / zero-baseline:** per-cell expectancy denominator = resolved member events (never a bar count);
  `0` resolved events ⇒ `UNRESOLVED_EMPTY` with denominator shown, never `0/0`; net-clear is the absolute
  `net ci_low_1s > 0` at threshold exactly 0 — never a % improvement over a zero baseline.
- **Bounded iteration / progress:** single 20-cell outer loop with `tqdm`; per-cell memory bounded (do not retain
  all domain frames simultaneously); `N_BOOT=10000` fixed; vectorize the bootstrap draw batching (NumPy) but keep
  the causal 1m forward walk explicit/sequential — do not vectorize it in a way that breaks order-of-touch or
  causal semantics (governance: no optimization that changes sample membership, ordering, denominators, or
  causal/streaming semantics).
- **Reuse, do not re-load:** the analysis pass returns bounded plot inputs; do not regenerate domain bars / 1m
  resolution solely for plotting. Reuse `xen.intrabar_fill`, `xen.mean_reversion`, `xen.domain_bars`,
  `xen.exit_rules`/`xen.position_exits`/`xen.capture_barriers`/`xen.capgeo_cost`/`xen.financing`,
  `xen.expectancy`, and the EXP-090 moving-block bootstrap estimator unchanged. **No edits to frozen
  entry/exit/cost generators; no new referee.** At most one small screen-orchestration helper if needed.
- **Dependency gate:** hard-fail if `python/experiments/EXP-090/results/member_map.csv` is missing or EXP-090
  `run_metadata.json` does not record `READINESS_CALIBRATION_DELIVERED`; screen exactly the 20 MEMBER cells.

## Complexity Check

- **Statistical tests:** 2 / ≤2 budget — (1) net `ci_low_1s` moving-block bootstrap lower bound (**binding** net-
  clear figure); (2) Wilcoxon signed-rank for the native-vs-contrast paired Δ (**descriptive, non-binding**). No
  new selection statistic ⇒ no bite-check.
- **Visualisations:** 4 / ≤4 budget.
- **New modules:** 0–1 / target 0–1 (reuse the EXP-090 / capgeo stack; at most one small orchestration helper).
