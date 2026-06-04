# Experiment: EXP-010 - Split-Protocol Robustness of the Referee

## Hypothesis

**H-split:** Alternative within-analysis-set split protocols (anchored
walk-forward; purged/embargoed K-fold cross-validation) do **not materially**
change the frozen referee's operating characteristics — pooled-by-domain
gate-stack FPR and economic MDE — versus the mandated single chronological 70/30
split.

The null is **robustness**. H-split is **falsified (and interesting) on a domain**
if a protocol materially shifts that domain's gate FPR or MDE, where "materially"
is the predeclared, frozen criterion below.

**Frozen material-difference criterion (set before any EXP-010 result is read,
per design §2 ⚠ discipline).** For a protocol vs the single-split reference on a
domain at `alpha0 = 0.05`, the protocol materially changes operating
characteristics if **either**:
- `|MDE_protocol(domain) - MDE_single(domain)| >= max(0.5 bps, 20% of MDE_single(domain))`
  (same margin family as EXP-008 / the EXP-001 recovery band), **or**
- the protocol's pooled gate FPR Wilson interval at `alpha0` is disjoint from the
  single-split reference FPR Wilson interval, **or** its FPR Wilson lower bound
  exceeds `alpha0`.

This criterion may be changed only by a dated amendment authored before any
EXP-010 result is read.

## Question

If we replace the single chronological train/test split with an anchored
walk-forward or a purged/embargoed K-fold cross-validation — keeping the frozen
referee legs, costs, materiality, and bootstrap unchanged — does the referee's
per-domain FPR and economic MDE stay put, or does the inference protocol itself
move the operating characteristics?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled to 5m, 1h, and 4h OHLC
  domains via the frozen `xen.referee_calibration` harness. No chart-type views.
  This experiment requires **new market-data measurement** (regenerated draws),
  evaluated under three split protocols.
- **Protocols under test (predeclared, frozen)**: All three operate **only within
  the first-70% analysis set**; none touches the global holdout. The split unit is
  the shared 1-minute `CloseTime` boundary mapped into each domain (never a
  per-timeframe row fraction, per design §7).
  1. **Single chronological split (reference)** — the mandated 70/30 train/test
     within the analysis set; identical protocol to EXP-003. This arm is the
     baseline and the correctness anchor.
  2. **Anchored (expanding) walk-forward, K = 5** — an initial chronological
     training warmup, then 5 contiguous expanding test folds tiling the
     post-warmup analysis set; each fold trains on all analysis rows strictly
     before its test block. Out-of-sample (OOS) = the concatenation of the 5 test
     folds.
  3. **Purged K-fold CV with embargo, K = 5** — 5 contiguous folds; for each test
     fold, training rows whose `t -> t+1` label window overlaps the test fold are
     **purged** (purge = 1 label bar), and an **embargo** of `max(1, in-sample
     block length)` bars after the test fold is removed from training to bound
     serial-correlation leakage (López de Prado purged/embargoed CV, adapted to
     the 1-step label). OOS = the concatenation of the 5 held-out folds.
- **Per-draw verdict aggregation (predeclared, faithful to the frozen referee)**:
  For each draw under a multi-fold protocol, pool the OOS test returns across
  folds into a single OOS series, estimate the bootstrap block length on the
  corresponding pooled in-sample training returns, run **one** block bootstrap on
  the pooled OOS series, and apply the **frozen** 5-check gate-stack and minimal
  legs (L1-L5, costs, materiality, naive control, 1000 resamples) to that pooled
  partition — producing exactly one verdict per draw, directly comparable to the
  single-split verdict. **Faithfulness constraint:** the referee leg logic, cost
  model, materiality constants, naive control, and bootstrap are reused unchanged
  from `xen.referee_calibration`; *only* the train/test partition feeding
  block-length estimation and the test bootstrap changes across protocols. The
  experiment changes the split, never the referee.
- **Reference-reproduction (correctness) check**: At the EXP-010 draw budget, the
  single-split arm's pooled gate FPR and MDE must be **statistically consistent**
  with EXP-003 (overlapping Wilson intervals / same grid MDE within grid
  uncertainty). Because EXP-010 uses fewer draws than EXP-003 for tri-protocol
  tractability, this is a consistency check, not bit-identity. Failure of this
  check is Evidence AGAINST (the harness was not reused faithfully).
- **Draw generation**: Regenerate known-null and known-positive draws with the
  frozen harness primitives (`random_state_positions`, `permuted_returns`,
  `plant_positive_edge`, the EXP-003 seed discipline via `seed_for`) on the
  first-70% analysis returns. Draw counts are **held identical across all three
  protocol arms** so cross-protocol comparison holds draw count constant:
  predeclared **250 null draws per null generator per instrument per domain**
  (two null generators) and **250 positive draws per edge per instrument per
  domain**; 1000 inner block-bootstrap resamples per verdict. (Reduced from
  EXP-003's 500 for tractability across three protocols; D-prec governs
  reportability.)
- **Parameters**: Domains `{5m, 1h, 4h}`; coverage 5m strict, 1h/4h
  `min_coverage=0.90`; alpha grid `{0.10, 0.05, 0.01}`, primary `alpha0=0.05`;
  EXP-003 edge grid `{0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps
  for FPR (edge 0) and MDE summaries; walk-forward `K=5`; purged CV `K=5`,
  purge `=1` bar, embargo `=max(1, in-sample block length)` bars.
- **Referees**: Frozen 5-check gate stack is the headline referee (H-split is
  about its OC); frozen minimal baseline is an optional diagnostic reference.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, **pooled by domain** to match
  how EXP-003 calibrated the MDE (this experiment is about the referee's
  per-domain OC, not per-instrument heterogeneity — that is EXP-008).
- **Dependencies**: EXP-001 `run_metadata.json` `overall_status == "PASS"`;
  EXP-003 `run_metadata.json` `overall_status == "COMPLETE"` with finite
  gate-stack MDE rows in `mde_summary.csv` (the single-split reference target).
- **Time range**: Full dataset with nested chronological split per instrument
  file; first 70% = analysis set; final 30% = global holdout and is never used.
  All three protocols partition only the analysis set.
- **Global holdout**: The final 30% of each source file must not be loaded,
  inspected, or used in any capacity. No split protocol — single, walk-forward,
  or purged CV — may extend any train or test fold past the 70% analysis cutoff.
- **Look-ahead bias prevention**: Within every protocol, training rows are
  strictly causal relative to their test fold (walk-forward trains only on prior
  rows; purged CV purges overlapping labels and embargoes post-fold rows). All
  draws use only `t -> t+1` real Close-to-Close returns; block length is
  estimated on in-sample training returns only.
- **Real-price outcome discipline**: All draw returns are real domain `Close`
  returns plus the predeclared known-positive drift (same substrate as EXP-003).
  No Heiken Ashi or Renko synthetic prices are in scope.
- **Exclusions**: Adopting or recommending any split protocol (that is EXP-011 /
  Phase 003); per-instrument de-pooling (EXP-008); the broadened strategy set
  (EXP-009); the near-MDE realistic candidate (EXP-005); the L5 threshold sweep
  (EXP-006) or lenient variant (EXP-007); referee redesign or any change to the
  frozen leg logic, costs, materiality, or bootstrap; chart-type signals;
  parameter tuning; touching the global holdout; and using any split protocol on
  the holdout for any purpose.

## Success / Failure Criteria

- **Evidence FOR (H-split supported on a domain)**: With usable precision
  (D-prec met) at `alpha0`, neither alternative protocol meets the frozen
  material-difference criterion on that domain (FPR and MDE stay within the
  criterion versus the single split) — the referee's OC is robust to the split
  protocol there.
- **Evidence AGAINST (H-split falsified on a domain)**: With usable precision at
  `alpha0`, at least one alternative protocol meets the frozen material-difference
  criterion on that domain (it materially shifts FPR or MDE).
- **Inconclusive (per domain/cell)**: A cell misses the D-prec precision target
  (FPR Wilson half-width `> 0.03` or TPR Wilson half-width `> 0.05`) or yields no
  finite MDE over the edge grid under a protocol — expected most likely on 4h,
  where folding further shrinks per-fold effective sample. Reported as
  under-powered with honest CIs, never forced to a verdict. The experiment is
  overall inconclusive only if the reference-reproduction check is the sole
  passing measurement.

## Complexity Budget

- Max statistical tests: 4 (per-protocol pooled FPR Wilson intervals; per-protocol
  MDE determination; material-difference comparison vs single split;
  reference-reproduction consistency check)
- Max visualisations: 4
- Max new code modules: 1 (an experiment-local module under
  `python/experiments/EXP-010/code/` providing the split-protocol index
  generators and a faithful multi-fold referee-evaluation wrapper that reuses the
  frozen `xen.referee_calibration` primitives; **no shared `python/src/xen`
  module is modified**, so no P0/temporal re-validation is triggered)

## Data Requirements

Load only the first 70% chronological analysis slice per 1-minute source file via
the frozen harness `load_analysis_data`, build `{5m, 1h, 4h}` domains via
`build_domain_frames`, derive `t -> t+1` returns and the shared split boundary,
regenerate the predeclared draws, and evaluate the frozen referees under each of
the three protocols.

Required upstream artifacts:

- `python/experiments/EXP-001/results/run_metadata.json`
- `python/experiments/EXP-003/results/run_metadata.json`
- `python/experiments/EXP-003/results/mde_summary.csv`
- `python/experiments/EXP-003/results/fpr_summary.csv`

Primary expected outputs:

- `protocol_draw_verdicts.csv` (per draw x protocol; bounded/streamed to disk)
- `protocol_fpr_summary.csv` (pooled-by-domain FPR per protocol/alpha)
- `protocol_mde_summary.csv` (pooled-by-domain MDE per protocol/alpha)
- `protocol_comparison.csv` (each protocol vs single split, with `material` flag)
- `reference_reproduction_check.csv` (single-split arm vs EXP-003)
- `run_metadata.json`

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
```

Use `tqdm` progress over the instrument x domain x protocol x draw loops, stream
verdict rows to disk in bounded batches, and reuse the per-draw return/position
arrays across protocols rather than regenerating them per protocol.

## Suggested Direction

Treat this as a robustness measurement of the *inference protocol*, not a search
for a better split. Hold the referee frozen and change only the partitioning;
report FPR/MDE deltas in absolute bps and FPR terms against the single-split
reference, and leave any protocol recommendation to EXP-011 / Phase 003. If the
operating characteristics are stable across protocols, that strengthens
confidence in the EXP-003 single-split map; if a protocol moves them materially,
flag it as a measured finding for the synthesis, not a change to adopt here.

## Amendment 2026-06-03 — adversarial-review corrections (pre-results, §2 ⚠-compliant)

**Status.** Dated amendment authored **before any EXP-010 result exists** (no
`results/`, `audit.md`, or `report.md` present). It references no EXP-010
measurement and changes only the items below; H-split (§ Hypothesis), the frozen
material-difference criterion, the protocols, `K`, purge, embargo, draw counts,
and every referee leg/cost/materiality/bootstrap stay **exactly as predeclared
above**. Source:
`docs/code-reviews/2026-06-03-194448-exp-008-010-adversarial-review.md` and its
validation `docs/code-reviews/2026-06-03-exp-008-010-review-validation.md`.

1. **Per-draw multi-fold aggregation (F02) — predeclaration changed.** The
   "Per-draw verdict aggregation" bullet above pools the out-of-sample test
   returns and estimates the block length on a *pooled in-sample union*. For
   multi-fold protocols that union **overlaps** the pooled OOS (a row out-of-sample
   in one fold re-enters the in-sample union via another fold), so the wrapper is
   not a clean train/test partition. **Corrected rule:** evaluate the frozen
   referee **per fold** — block length on each fold's own (disjoint) training
   rows, the neutral / vs-naive / minimal bootstraps on that fold's own test rows —
   then combine to one verdict per draw: the effect and `effective_n` use the
   pooled OOS returns (each row scored once), the CI is taken over the
   concatenation of the per-fold bootstrap-mean distributions, L1 episodes are
   summed per fold, L4 uses the size-weighted train mean over all fold trains and
   the pooled-OOS mean, and the reported block length is the per-fold max. For the
   single contiguous fold this reduces **bit-for-bit** to the frozen
   `evaluate_referees`, so the reference-reproduction anchor is unchanged.
2. **FPR materiality independence (F01) — criterion unchanged, code corrected.**
   The frozen material criterion is an OR of three sub-conditions; FPR materiality
   (disjoint FPR interval, or FPR Wilson lower > α₀) is now evaluated **independent
   of MDE reportability**, gated only on FPR precision (D-prec). MDE materiality
   keeps a separate reportability flag.
3. **Timestamp-mapped fold boundaries (F05) — code corrected to match this scope.**
   Walk-forward warmup/test and purged-CV fold boundaries are computed as shared
   1-minute `CloseTime` boundaries mapped into each domain (as this scope already
   requires), never per-timeframe row fractions.
4. **Bounded/streamed verdict output (F06) — code corrected to match this scope.**
   `protocol_draw_verdicts.csv` is streamed to disk with bounded FPR/TPR pooled
   pass-count accumulators; the full verdict list is never held in memory.
