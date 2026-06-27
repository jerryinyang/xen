# Analysis Plan: Experiment EXP-010

## Objective

Test H-split: whether the frozen referee's pooled-by-domain gate FPR and economic
MDE are robust to the train/test split protocol. Compare the mandated single
70/30 chronological split against anchored walk-forward (K=5) and
purged/embargoed K-fold CV (K=5), holding the referee, costs, materiality, and
bootstrap frozen and changing only the partition. A reference-reproduction check
anchors faithfulness against EXP-003.

## Methodology

### Step 1: Dependency gate and reference load

- **Method**: Assert `EXP-001` `overall_status == "PASS"` and `EXP-003`
  `overall_status == "COMPLETE"` with finite gate-stack MDE rows in
  `mde_summary.csv` and FPR rows in `fpr_summary.csv`. Load the single-split
  reference FPR/MDE per domain/alpha.
- **Why this method**: Artifact-based gate consistent with prior Phase-002 EXPs.
- **Simpler alternative considered**: None — the reference is required.
- **Assumptions**: EXP-003 is the frozen single-split reference.
- **Expected output**: Reference FPR/MDE map in memory.

### Step 2: Holdout-safe substrate and shared draws

- **Method**: Per instrument, `load_analysis_data` (first-70% only) →
  `build_domain_frames` → per-domain `t -> t+1` returns + shared split boundary.
  Regenerate draws with the **frozen** harness primitives and the EXP-003 seed
  discipline (`seed_for`): per instrument/domain, **250 null draws per null
  generator** (raw-return null with random candidate via
  `random_state_positions`; bar-permutation null via `permuted_returns`) and
  **250 positive draws per edge** over the EXP-003 edge grid, with state-aligned
  drift via `plant_positive_edge`. The per-draw return array and candidate
  position array are generated **once** and **reused across all three protocols**
  (only the partition differs), so the protocols are compared on identical draws.
- **Why this method**: Identical draws across protocols isolate the split effect;
  reusing the frozen generators keeps the substrate comparable to EXP-003.
- **Simpler alternative considered**: Reusing EXP-003's stored verdicts —
  rejected; verdicts do not carry the underlying return/position arrays needed to
  re-split, so the draws must be regenerated deterministically.
- **Assumptions**: Deterministic seeded generation reproduces a substrate
  statistically equivalent to EXP-003 (verified in Step 6, not assumed).
- **Expected output**: In-memory per-draw arrays; `tqdm` over instruments/domains.

### Step 3: Split-protocol index generators (new experiment-local module)

- **Method**: `python/experiments/EXP-010/code/split_protocols.py` exposes one
  function per protocol returning a list of `(train_idx, test_idx)` folds over the
  analysis-set row indices `[0, n)` of a domain (n = eligible `t -> t+1` rows):
  - **single**: one fold; `train_idx = [0, cut)`, `test_idx = [cut, n)` where
    `cut = domain_split_index` (the EXP-003 boundary).
  - **walk_forward_anchored (K=5)**: an initial warmup of `floor(0.5 * n)` train
    rows; the remaining rows are tiled into 5 contiguous test blocks; fold `k`
    trains on `[0, test_start_k)` and tests on block `k` (expanding/anchored).
  - **purged_cv_embargo (K=5)**: 5 contiguous folds tile `[0, n)`; for test fold
    `k`, `train_idx` = all other rows **minus** (a) the 1-bar label-overlap purge
    on each side of the test block and (b) an embargo of `max(1, block_length)`
    rows immediately after the test block. The embargo `block_length` is estimated
    **once per (instrument, domain) on the real domain return series**
    (draw-independent), so all protocol fold index sets are cell-level and reused
    unchanged across every draw and protocol. This guards serial-correlation
    leakage as a property of the market data, not of any one synthetic candidate.
  All index sets are strictly within `[0, n)` (the analysis set); no index can
  reference the global holdout.
- **Why this method**: Standard, well-documented protocols (anchored WF; López de
  Prado purged/embargoed CV) adapted to the 1-step label horizon; index-only
  generation keeps the referee untouched.
- **Simpler alternative considered**: Random K-fold without purge/embargo —
  rejected; it leaks serially-correlated neighbours across train/test and would
  not test the dependence concern honestly.
- **Assumptions**: 1-step label horizon ⇒ purge = 1 bar; embargo scaled to the
  estimated block length captures residual autocorrelation.
- **Expected output**: Deterministic fold index lists per protocol/domain.

### Step 4: Faithful multi-fold referee evaluation

- **Method**: A wrapper (same module) computes one verdict per draw per protocol
  by **reusing the frozen `xen.referee_calibration` primitives** and changing only
  the partition. For a given protocol's folds:
  1. Compute `strategy = strategy_return_bps(returns, positions, cost_bps)` and
     `naive = strategy_return_bps(returns, naive_momentum_positions(returns),
     cost_bps)` on the **full** series (cost/naive identical to the frozen gate).
  2. Form pooled in-sample (`train`) and out-of-sample (`test`) index sets by
     concatenating folds' `train_idx`/`test_idx`. For `single`, this is exactly
     the contiguous EXP-003 partition.
  3. `block_length = estimate_block_length(strategy[train_idx])`;
     `effective_n = len(test_idx) / max(block_length, 1)`.
  4. Neutral bootstrap: `block_bootstrap_means(strategy[test_idx], ...)`; vs-naive
     bootstrap: `block_bootstrap_means((strategy - naive)[test_idx], ...)` — the
     same two bootstraps and seeds the frozen `gate_stack_core` uses.
  5. Legs: **L1** readiness = `effective_n >= min_effective_n` and the min
     up/down **episode count summed per fold** (counted within each fold's train
     and test positions, then summed — so fold seams neither create nor destroy
     episodes) `>= min_state_count`; **L2** = True; **L3** = neutral CI lower > 0
     and naive CI lower > 0; **L4** = `mean(strategy[train_idx]) > 0` and
     `mean(strategy[test_idx]) > 0`; **L5** = neutral CI lower > `materiality_bps`.
     Verdict = L1∧L2∧L3∧L4∧L5. Minimal baseline = neutral-vs-zero CI on the gross
     (cost=0) strategy over `test_idx`.
- **Why this method**: It reproduces the frozen gate-stack leg-for-leg; only the
  index partition feeding block-length and the test bootstrap changes. The
  per-fold-then-sum episode rule preserves L1 semantics under concatenation.
- **Simpler alternative considered**: Editing `gate_stack_core` to accept index
  sets — rejected; modifying a shared validated module triggers P0/temporal
  re-validation. An experiment-local faithful wrapper avoids that and is guarded
  by the Step 6 reference check + Stage-5 audit.
- **Assumptions / caveat**: The pooled-OOS neutral bootstrap draws blocks over the
  concatenated test series. EXP-003 found `block_length = 1` throughout, so the
  stationary bootstrap reduces to i.i.d. resampling and fold seams introduce no
  bias; if any protocol's in-sample `block_length > 1`, the plan flags
  cross-seam blocks as a documented minor approximation and the result notes it.
- **Expected output**: `protocol_draw_verdicts.csv` (streamed in bounded batches).
- **Amendment 2026-06-03 (adversarial-review F02, pre-results).** Steps 2–4 above
  describe pooling the OOS test returns and estimating the block length on a
  *pooled in-sample union*; for multi-fold protocols that union overlaps the
  pooled OOS and is not a clean partition. The implemented rule instead evaluates
  the frozen referee **per fold** (block length and L4 train-mean on each fold's
  own disjoint train; neutral/vs-naive/minimal bootstraps on each fold's own
  test), then combines into one verdict per draw — pooled OOS returns for the
  effect/`effective_n`, concatenated per-fold bootstrap-mean distributions for the
  CI, per-fold-summed L1 episodes, max-of-fold block length. This reduces exactly
  to the frozen `evaluate_referees` for the single contiguous fold. See
  `scope.md` "Amendment 2026-06-03".

### Step 5: Pooled-by-domain FPR and MDE per protocol

- **Method**: Pool the four instruments per domain (matching EXP-003). FPR =
  null-draw pass rate with Wilson interval (`verdict_rate_rows`); TPR per edge
  likewise; MDE = smallest grid edge with pooled TPR `>= 0.80` at FPR `<= alpha`
  with D-prec precision (same rule as EXP-003/008).
- **Why this method**: Identical OC estimators to EXP-003 so cross-protocol
  numbers are comparable.
- **Simpler alternative considered**: Per-instrument OC — out of scope (that is
  EXP-008).
- **Assumptions**: Pooled draws exchangeable within a domain cell (as EXP-003).
- **Expected output**: `protocol_fpr_summary.csv`, `protocol_mde_summary.csv`.

### Step 6: Reference-reproduction check

- **Method**: Compare the **single** protocol's pooled FPR and MDE against EXP-003
  at matching domain/alpha. PASS if the FPR Wilson intervals overlap and the MDE
  matches within the EXP-003 grid uncertainty. This is a consistency check (fewer
  draws than EXP-003), not bit-identity.
- **Why this method**: Validates that the regenerated substrate + faithful wrapper
  reproduce the frozen single-split harness before any protocol delta is trusted.
- **Simpler alternative considered**: Bit-identical reproduction — infeasible at a
  reduced draw count; statistical consistency is the right bar.
- **Assumptions**: None beyond Monte-Carlo sampling.
- **Expected output**: `reference_reproduction_check.csv`.

### Step 7: Material-difference comparison

- **Method**: For each protocol vs single per domain at `alpha0`, apply the frozen
  criterion: `material = (|MDE_protocol - MDE_single| >= max(0.5, 0.20 *
  MDE_single))` OR (FPR Wilson intervals disjoint) OR (FPR Wilson lower >
  alpha0). Record deltas and flags.
- **Why this method**: Operationalises the frozen H-split criterion; additive-bps
  floor avoids any zero-baseline ratio (MDE_single is 1/4/12 bps).
- **Simpler alternative considered**: Percent-only difference — rejected (unstable
  near small MDE; design froze the additive-floor form).
- **Assumptions**: MDE_single finite (asserted Step 1 / reproduced Step 6).
- **Expected output**: `protocol_comparison.csv`, `run_metadata.json`.

## Visualisations

1. **MDE per protocol, faceted by domain** — grouped bars with the single-split
   reference line and frozen margin band; the headline robustness view.
2. **FPR per protocol at `alpha0`, faceted by domain** — bars with `alpha0` line
   and Wilson error bars; shows whether folding inflates FPR.
3. **Pooled TPR vs edge per protocol, faceted by domain** — overlaid curves with
   the 0.80 target and each protocol's MDE marker.
4. **Material-flag + reference-check matrix** (protocol x domain) — categorical
   roll-up including the single-split reproduction status.

## Interpretation Guide

- **Per domain**: if neither alternative protocol meets the frozen material
  criterion (with D-prec met), **H-split is SUPPORTED** there — the referee OC is
  split-robust, strengthening confidence in the EXP-003 single-split map.
- If at least one protocol meets the material criterion (with D-prec met),
  **H-split is FALSIFIED** there — the inference protocol itself moves FPR/MDE; a
  measured finding for EXP-011, not a change to adopt.
- If the **reference-reproduction check FAILS**, the regenerated substrate/wrapper
  is not faithful → **Evidence AGAINST** at the experiment level (do not interpret
  protocol deltas).
- Cells missing D-prec (likely 4h, where folding shrinks per-fold effective
  sample) are **under-powered / inconclusive**, reported with honest CIs.

## Implementation Safety Constraints (for experiment-developer)

- **Holdout**: Every fold index set is bounded to `[0, n)` of the first-70%
  analysis domain; assert `max(test_idx) < n` and that no fold extends past the
  cutoff. The holdout is never loaded.
- **Look-ahead / causality**: WF trains only on prior indices; purged CV applies
  the 1-bar purge and block-length embargo; verify train and test index sets are
  disjoint and the purge/embargo gap is present.
- **Faithfulness**: Reuse harness primitives unchanged; the only change vs the
  frozen gate is the index partition. The Step 6 reference check must PASS before
  protocol deltas are interpreted.
- **Determinism**: Seed every draw via `seed_for(instrument, domain, scenario,
  generator, edge, draw)`; reuse the same arrays across protocols; record the seed
  scheme in `run_metadata.json`.
- **Denominators**: Draw-verdict counts per cell; no deduplication; report `n`.
- **Bounded memory / streaming**: Stream `protocol_draw_verdicts.csv` to disk in
  bounded batches; do not accumulate all verdict rows in memory. Reuse per-draw
  arrays across the three protocols.
- **Progress**: `tqdm` over the instrument x domain x protocol x draw loops;
  concise logging only.
- **Zero-baseline**: `max(0.5, 0.20 * MDE_single)` defined even if MDE_single were
  0; assert finite first.

## Complexity Check

- Statistical tests: 4 / 4 (per-protocol FPR Wilson; per-protocol MDE;
  material-difference comparison; reference-reproduction consistency check)
- Visualisations: 4 / 4
- New modules: 1 / 1 (experiment-local `split_protocols.py`; the frozen
  `xen.referee_calibration` is reused unchanged)
