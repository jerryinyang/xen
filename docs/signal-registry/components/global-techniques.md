# Global Technique Notes

This file records reusable components that may become future registered
candidate branches. Nothing in this file is eligible for measurement until it is
promoted into `multiplicity-registry.md` with a candidate or component ID.

## Trigger Components (can be for exits or entries)

### Heiken Ashi Exhaustion Patterns

These are possible exit overlays. If used, signal decisions may inspect Heiken
Ashi features, but P&L and return evaluation must use real time-bar prices.

#### Pattern 1: Harami Size Pattern

- Latest HA bar: `bar_0`.
- Previous HA bar: `bar_1`.
- Signal condition:
  `max(close_1, open_1) > max(close_0, open_0)` and
  `min(close_1, open_1) < min(close_0, open_0)`.
- Deferred variants:
  - signal direction follows `bar_0`;
  - signal direction independent of bar color.

#### Pattern 2: Trailing Exit Price

- Short-exit reference: HA high or `max(HAOpen, HAClose)`.
- Long-exit reference: HA low or `min(HAOpen, HAClose)`.
- Deferred execution variants:
  - stop-style trigger;
  - bar-close market-style trigger.

### Last-X High/Low

- Long-exit reference: lowest low over the last X traditional candles.
- Short-exit reference: highest high over the last X traditional candles.
- `X` is not registered. Any value or sweep must be predeclared before use.




## Position Management Components

### Pyramiding

- Adds entries in the same direction as an existing position.
- Required parameter: maximum open positions.
- Not registered for Phase 004 Batch 004-A.





## Risk Management Components

### Volatility-Adjusted Sizing (`SIZE-VOLADJ`)

- **Promoted 2026-06-20** to `multiplicity-registry.md` (Phase 018 batch, CF-CAPGEO-001).
- Per-signal position weight scales inversely with a causal volatility estimate (e.g. ATR or
  realized vol over a predeclared lookback) so the return series reflects realistic, unequal
  signal sizing rather than equal-weighted raw returns.
- **Hypothesis, not assumption:** tested against the raw-return (equal-weight) baseline; never
  assumed superior. Returns and P&L evaluated on real time-bar prices.

## Evaluation & Qualification Components (CF-CAPGEO-001)

Promoted 2026-06-20 to `multiplicity-registry.md` (Phase 017 batch). **Validate-first:** none is
eligible to *adjudicate* a candidate until Phase 017 returns G-017 `ASS_VALIDATED`; otherwise the
frozen referee suite remains binding and these are discovery-only. Specs: `.ignore/dump/ass.md`,
`.ignore/dump/wf-model.md`.

> **G-017a recovery leg — VALIDATED (EXP-076, 2026-06-20).** The `ASS` estimator core recovers known
> ground truth: expectancy & median unbiased (`median|err|/SE` < 0.85 on all 198 synthetic `(type,n)`
> cells, incl. negative-median skews), 90% bootstrap CIs calibrated at **n≥30**, shrinkage monotone
> with the designed sparse-pull/rich-stability behaviour. **Caveat:** the percentile-bootstrap
> **expectancy** CI under-covers at **n<30** (intrinsic small-sample floor of the mean — *not* an `ASS`
> defect; median CI in-band at all n) → downstream rule: no expectancy edge-calls on types with
> effective n<30 (weakened-evidence / defer to median) pending the EXP-077 small-n FPR check. Full
> G-017 `ASS_VALIDATED` still requires EXP-077 (FPR/MDE/reliability) + EXP-078 (shape + `k`).

> **G-017 error-control + protocol legs — VALIDATED_WITH_GUARDS (EXP-077, 2026-06-20).** Under
> `WF-EXPANDING`: **MDE finite ∀ n≥30**; **`P(>X)` reliability** holds at X=0/0.05/1.0; **counted-read
> accounting** honors the 2-read cap (8/8 scenarios); real-bar **dogfood** completes on 12/12 cells with
> the first-49% fence held and 0 counted reads; determinism + estimator anchor exact. Two bounded
> per-stratum guards confirm the EXP-076 caveat and add one: **(i)** the EXP-077 small-n FPR check
> closes — the percentile-bootstrap expectancy-FPR inflates mildly on the **bimodal mean-null at
> effective n≤60** under the 5-fold protocol (B_zero FPR 0.059 at n=30/60, decaying to ~0 by n≥120) →
> ratify *no expectancy edge-calls / defer to median at effective n≤60* on bimodal/asymmetric mean-null
> strata (location-null `U0` is controlled — its point crossings are MC noise around a margin calibrated
> to 0.05, all Wilson-hi≤0.075); **(ii)** the D2.4 calibration **slope** sub-gate is structurally
> inapplicable when predicted `P(>X)` is compressed near zero (X=2.0: max-gap 0.017, corr 0.934, but
> slope 0.652 over a 0.056-wide range) → bind on max-gap there. No `PROTOCOL_DEFECT`. Guards are
> disclosures to terminal G-017 (decided after EXP-078); the frozen D0/D2.4 gates were not retro-edited.

### Adaptive Signal Scoring (`ASS`, a.k.a. Expectancy-Robust Qualifier / ERQ)

- **Pipeline:** per signal type, take raw entry-to-exit **real-price** returns → adaptive-bandwidth
  KDE (k-nearest-neighbor bandwidth, widening in sparse regions) → hierarchical empirical-Bayes
  **shrinkage** toward the pooled (all-signals) KDE, weight `n / (n + k)` with `k` defaulting to the
  median sample size across signal types (the single tunable knob) → bootstrap CI (resample within
  signal type, recompute, 5th/95th pct).
- **Scoring posture (binding deviation from the raw draft):** report **expectancy + median + an
  explicit tail/bimodality diagnostic** — never expectancy (a smoothed mean) alone. Expectancy and
  `P(return > X)` are not interchangeable rankings and are not collapsed into one composite without a
  separately justified rule.
- **Probability-of-return extension:** `P(return > X)` per threshold X ∈ {0, breakeven, 1R, 2R} via
  the shrinkage-weighted fraction of (bootstrapped) trades > X; reliability/calibration check on a
  held-out period.
- **Shrinkage target (default, override with justification):** each (entry-substrate × instrument ×
  domain) cell is a signal type, pooled toward the per-substrate population.

### Expanding-Window Walk-Forward Protocol (`WF-EXPANDING`)

- **Primary protocol:** `Train A → Test_A`; `Train A + Test_A + Train B → Test_B`; … Including a
  completed Test fold in the next training set is **not leakage** (those observations are historical
  at the next train time). Rolling 1y/2y/3y windows are a disclosed comparison.
- **Binding governance interaction:** the per-fold counted-read accounting must honor the
  TEST-read-ledger **2-lifetime-counted-reads-per-stratum** cap; this accounting is predeclared and
  validated at G-017 before any Phase 018 TEST contact. The final-30% global holdout is never a fold.

## Selection Components

### Neighbour-Stability Selection (`SEL-NEIGHBOR`)

- **Promoted 2026-07-08** to `multiplicity-registry.md` (Chapter 02 · Phase 010 batch,
  CF-HTFDI-001; first bound use: EXP-025 design §7). 0 slots, 0 reads at registration.
- Plateau selection on a predeclared ordered parameter grid: a cell qualifies only if
  (1) its own selection-fold statistic clears, (2) the **median** of its ±1-step
  neighbourhood (adjacent grid positions, same stratum) clears, and (3) the **pooled**
  later-validation-fold statistic shares the selection-fold sign with no single fold
  significantly contradicted (CI_high < 0) — raw per-fold sign agreement on small folds
  is coin-flip fragile (amended 2026-07-08). Isolated maxima are disqualified
  (they fail the neighbourhood median). Contradicted neighbours (CI_high < 0) are a
  **disclosure, not a disqualifier** — the median is the robust smoother; a hard
  single-neighbour veto is outlier-fragile in the opposite direction (amended
  2026-07-08 pre-measurement, operator-directed).
- Tie/edge rules: even-count medians use the lower median; boundary cells (one
  neighbour) require sign agreement of both cells. Winner = highest **neighbourhood
  median** (not own value); remaining ties → the simpler/smaller parameter.
- TRAIN-only, mechanical, predeclared before measurement; never applied after TEST
  contact. Each experiment binds its own grid, statistic, and fold structure in
  `design.md` before QA.

## Notes

These notes are intentionally non-operative. Treat them as backlog material, not
as experiment authorization.
