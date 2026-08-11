# EXP-103 — TPO value gaps and tight gaps

- **Family:** `CF-LIQSWP-001/HYP-003`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design complete; fresh QA pending
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-5; no experiment-specific amendment. Counts: **0L / 1T / 3N**.

## Mechanism

```text
MECHANISM: A sweep whose excursion-to-confirmation path leaves a concentrated,
low-density TPO value gap may have a different subsequent swing distribution.
The gap is known at same-direction confirmation and is therefore a conditioning
label for the later swing, not a live prediction of the raid.
DERIVED: estimand=defined-profile and tight-gap versus non-tight-gap outcome
contrasts; null=future-destroyed post-confirmation outcomes; horizon=confirmation
to opposing event or censor; test=direct, per-stratum ATR-normalised comparisons.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the profile belongs to the same
    level-linked sweep record whose later swing is measured.
  measured conditioning event == traded entry event: N/A — “tradable” is tested
    only as an observed descriptive label; no deployment P&L is claimed.
  effect-splitting windows non-overlapping: YES — profile ends at confirmation;
    the later-swing outcome begins after confirmation.
```

## Frozen profile algorithm

- Source: closed 1m bars, one TPO time bracket per bar.
- Interval: maximum-excursion-setting 1m bar through the completed same-direction
  confirmation close.
- Bin width: `0.10 × causal observation-timeframe Wilder ATR(14)`, frozen when
  the active profile begins.
- Contribution: one count in every bin intersecting the bar’s inclusive low-high.
- POC: lowest-price maximum-count bin.
- VA: contiguous expansion from POC to at least 70% of total TPO count, upper-first
  on ties.
- Gap: lowest-density VA bins reaching at least 30% of VA TPO count; exact mask
  and outer span emitted.
- Tightness:

```text
VA_width  = VAH - VAL
gap_span  = gap_high - gap_low
tight_gap = gap_span < 0.30 * VA_width
```

The profile is maintained online. A new maximum excursion resets the active
profile at that bar; no historical vectorised rebuild is permitted.

## Required checks

Synthetic and real-run checks must cover TPO count conservation, fixed bin
assignment, POC tie-breaking, VA 70% coverage, gap 30% TPO-mass coverage,
strict tightness boundary, `VA_width <= 0`, minimum-bin resolution, zero ATR,
empty profile, reset-on-new-maximum, and deterministic replay. The exact selected
bin mask must reconcile with the reported gap span.

## Control and tripwire

```text
CONTROL FUTURE_DESTROY:
  question answered: does tight-gap conditioning relate to the aligned later path?
  population: completed raids with defined profiles; post-confirmation blocks are
    deranged within asset × timeframe × confirmation/level configuration.
  bite: changes later swing outcomes but not gap labels or profile fields.
  non-vacuity: swing_atr, duration, and strong_move move under the destroy.
  expected outcome if H true: tight/non-tight contrast collapses; if H false: it remains.
  disclosure: fixed-point count and destroy/raw contrast ratio.
  destroy form: DERANGEMENT, zero fixed points.

TRIPWIRE: future-destroyed post-confirmation blocks
  must collapse the gap/outcome contrast;
  vacuity check: profile labels are held fixed while outcomes change;
  derangement=YES;
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

## Interpretation and sample size

```text
BANDS (operator-only): higher, overlapping, or lower tight/non-tight outcomes;
  “tradable” is not a machine field and cannot mean deployable under this design.
SAMPLE-SIZE:
  expected events per stratum: measured by preflight; no count gate.
  minimum_n_for_primary_inference: none.
  declared_fixed_comparator: non-tight defined profiles within the same named
    venue × asset × timeframe × method × level stratum; all-profile baseline retained.
  channels: swing_atr (outcome_level); strong_move (paired_delta).
  strata predeclared thin: every profile-defined cell, including zero/undefined
    reason counts.
```

## Golden trace

```text
GOLDEN-TRACE:
  A synthetic profile has VAH=110 and VAL=100. Its selected low-density bins
  occupy the outer envelope 104–106. The emitted VA width is 10, gap span is 2,
  gap_span_va=0.20, and tight_gap=true. A profile with the same VA but selected
  bins spanning 101–109 emits tight_gap=false. The later swing is not used to
  define either label.
```

## Hard versus informative

```text
HARD (block): profile causality, TPO/VA/gap invariants, fence/holdout, outcome
  reconciliation, future-destroy integrity, deterministic replay, and zero-cost.
INFORMATIVE: tight/non-tight contrasts, gap span distributions, profile reason
  counts, ATR outcomes, duration, PSR where applicable, and cross-venue replication.
```

## Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission,
    or swap enters any calculation. Realised results would differ (likely worse) under any
    real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped
    experiment; the directive is recorded in that experiment's design.md.
```
