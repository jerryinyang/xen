# Experiment: EXP-040 — HYP-001 Direct AVWAP Line Support/Resistance Test

**Registry:** `CF-AVWAP-001/HYP-001` (measurement) — 0 candidate slots
(mechanism science; never gates Track A).
**Governing design:** `docs/experiments-docs/checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md` (§5/B1, §8.3).
**Framing authority:** Phase 007 design §8 (binding); EXP-025 post-mortem
(its event-bar penetration metric is inadmissible).
**Date scoped:** 2026-06-10.

## Hypothesis

**HYP-001:** price approaching the anchored VWAP line reacts at the line as
support/resistance beyond what matched non-AVWAP price levels show —
`P(bounce | approach to AVWAP) > P(bounce | approach to matched control level)`
on the 1h and/or 4h domain.

## Question

Is the AVWAP line itself a price barrier, or is the Phase 006–008 edge a
continuation/regime effect for which the line is merely a trigger location?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 1h and 4h OHLC domains via
  `xen.bar_aggregator`; the canonical EXP-020 AVWAP state machine (frozen
  definition: MA 20/50 detector, `TickVolume**0.75` weight, MAD band
  multiplier 1.0) supplying the live line and band-width state. No other chart
  types.
- **Event definition (approach — binding, trigger-free)**: an approach episode
  begins at the first domain-bar close whose distance to the live AVWAP line is
  ≤ ε, having entered from outside the ε-neighborhood, and carries the entry
  direction (from above = falling into the line; from below = rising into it).
  ε is expressed in **band-width (MAD) units** — candidate value ε = 0.25 ×
  band-width, fixed by Stage 2 before any outcome computation. Contiguous
  in-neighborhood bars belong to one episode (one denominator count);
  a new episode requires a full exit beyond a predeclared hysteresis radius
  (Stage 2; candidate 2ε) — this is the duplicate-source rule.
- **Outcome (bounce — binding)**: the episode resolves as a bounce iff price
  exits the ε-neighborhood in the direction **opposite** to its entry
  (approached from above → exits upward; from below → exits downward), within
  a predeclared maximum episode length (Stage 2; candidate 24 domain bars —
  episodes unresolved at the cap or at the analysis boundary are disclosed,
  not silently dropped). The EXP-020 **bounce-trigger definition appears
  nowhere in event or outcome** — the EXP-025 conflation is inadmissible.
- **Control (matched non-AVWAP levels)**: for each AVWAP approach population,
  control levels carrying no AVWAP information, with approaches matched on the
  realized approach covariates — entry direction, trailing-volatility tercile,
  approach-speed tercile (distance-at-open is controlled by construction: both
  arms condition on `|Close − level| ≤ ε`; band-width tercile is collected and
  balance-reported but not a stratum key) — (Stage 2 fixes the construction;
  candidate: horizontal price levels at randomized offsets from the
  contemporaneous AVWAP in band-width units, resampled to match the approach
  covariate distribution; look-ahead-safe — controls computable at or before
  each approach timestamp). The binding estimand is the rate difference
  `Δ = P(bounce | AVWAP approach) − P(bounce | control approach)` in
  **percentage points** (never a relative % against a possibly-zero baseline).
- **Secondary control (shifted moving copies — descriptive only; design §11/8)**:
  a second control arm of **moving** levels `AVWAP(t) + δ·BW(t)` (identical δ
  construction, spawn grid, and lifetime as the primary frozen-horizontal arm;
  offsets keep these copies outside the ±1.0 trading band) isolates the
  moving-vs-static kinematic confound: these levels share the line's
  kinematics but carry an offset. The AVWAP-vs-moving-copy contrast `Δ_m` is
  **descriptive** — point estimate with cluster-bootstrap CI only; no
  permutation p, no Holm membership; the binding family remains the 2 pooled
  static-control domain contrasts. Joint reading is predeclared: Δ > 0 with
  Δ_m ≈ 0 → the effect is moving-level kinematics, not the line; Δ > 0 with
  Δ_m > 0 → line-specific S/R beyond both level geometry and kinematics;
  Δ_m alone never produces or upgrades a verdict.
- **Parameters**: domains {1h, 4h}; ε, hysteresis, episode cap, and the control
  construction fixed in Stage 2 **before** any outcome computation, single
  values each (no sweep — parameter sensitivity is a future scope).
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD — all four (mechanism science;
  no cost model, so no break-even exclusion). Per-instrument cells descriptive;
  binding inference on the pooled per-domain contrast.
- **Time range**: full **analysis set** (first 70% of each dataset), per the
  design §5/B1. No TRAIN/TEST split is binding here (no selection is
  performed); the chronological split-half check below uses analysis-set
  halves.
- **Global holdout**: the final 30% of every dataset must not be loaded,
  inspected, or used in any capacity.
- **Look-ahead bias prevention**: the line, band-width, approach detection,
  and control levels use only data at or before each bar close; the AVWAP
  state is the streaming state; alignment by `CloseTime` only.
- **Real-price outcome discipline**: all distances and outcomes use real
  domain-bar OHLC. The AVWAP line/band values are conditioning features, never
  return or P&L inputs (no P&L exists in this experiment — gross reaction
  rates only).
- **Exclusions**: any cost/financing layer; any tradability or strategy claim;
  the EXP-025 event-bar penetration metric; 5m; the bounce-trigger definition
  in any metric role; TEST-vs-TRAIN selection of any kind; new-universe data;
  parameter sweeps over ε/hysteresis/cap.

## Inference (binding family predeclared)

- Per domain: pooled-instrument contrast Δ with the regime-cluster bootstrap CI
  and a permutation p (label permutation of AVWAP-vs-control over matched
  approach strata), reusing the EXP-021/027 machinery conventions.
- **Binding family: the 2 pooled domain contrasts (1h, 4h), Holm at α = 0.05.**
  All 8 per-instrument×domain cells are descriptive (CIs disclosed,
  multiplicity-uncontrolled, never promoted).
- Stability disclosure (non-binding): chronological split-half of the analysis
  set — sign of Δ in both halves per domain.

## Success / Failure Criteria

- **Evidence FOR (per domain)**: Δ > 0 with bootstrap CI_low > 0 and Holm-
  adjusted permutation p ≤ 0.05. HYP-001 is SUPPORTED if ≥1 domain is FOR
  (domains reported individually; no cross-domain pooling).
- **Evidence AGAINST (per domain)**: CI entirely ≤ 0, or **AGAINST-as-
  immaterial**: CI entirely below the predeclared materiality threshold
  (CI_high < +2 pp) with CI_low ≤ 0 — i.e. FOR is not met and all material
  effects are excluded, regardless of the sign of the point estimate (a tight
  CI around an immaterially positive Δ is AGAINST, not INCONCLUSIVE). Stage 2
  fixes the materiality threshold (2 pp).
- **Inconclusive**: CI spans zero without meeting either condition, or the
  approach population is below the reportability floor (n < 100 episodes per
  arm per domain — disclosed, no verdict).
- Verdict classes have **no gate consequence** (design §8.3): the result is a
  permanent mechanism record and a Phase 011 / Stage-C family-review input. A
  NO closes the line-S/R mechanistic story and reframes the edge as relative
  momentum around pivots.

## Power / Fragility Statement (mandatory before any binding read)

Episode counts are unknowable before detection, so this statement is
structural, plus an ordering-enforced realized check:

- At the n = 100/arm reportability floor, the unclustered worst-case (p = 0.5)
  binomial SE of Δ is ≈ 7.1 pp; a one-sided 95% FOR at the floor therefore
  requires Δ ≳ 12 pp — and cluster dependence only inflates this. Floor-level
  cells can support FOR only for very large effects.
- AGAINST-as-immaterial (CI_high < +2 pp) requires CI half-width < 2 pp:
  ≳ 4,800 matched episodes per arm per domain unclustered (more with
  clustering). Cells below that scale are structurally incapable of an
  immateriality verdict; for them the reachable outcomes are FOR (large
  effect), AGAINST (CI ≤ 0), or INCONCLUSIVE.
- The implementation must persist `results/power_statement.csv` — realized
  matched episode counts per arm×domain and the implied minimal detectable Δ
  (unclustered binomial bound, flagged as optimistic under clustering), with
  per-cell flags for verdict classes structurally out of reach — **before**
  the binding contrast is computed (write-ordering asserted, as in EXP-039),
  and the results must state which verdicts were reachable at realized n.

## Complexity Budget

- Max statistical tests: 2 binding (the two pooled domain contrasts; bootstrap
  CIs + permutation p inside each) — within the comparative budget.
- Max visualisations: 4 (approach/episode count accounting; Δ forest plot
  per domain with per-instrument descriptive cells; bounce-rate vs entry
  direction breakdown; split-half stability)
- Max new code modules: 2 (`xen.line_approach` episode detector + matched
  control construction; experiment orchestration under `code/`)

## Data Requirements

- 1-minute Parquet under `data/timebars/`; lazy scan, `CloseTime` sort,
  analysis slice before collection.
- The EXP-020 AVWAP state machine reused unchanged for line/band state;
  deterministic replay required (fixed seeds for control-level randomization,
  byte-identical binding tables on rerun).
- Episode denominators: approaches (episodes), never bars; both arms use the
  identical episode/hysteresis/cap machinery so denominators are symmetric by
  construction.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_<SYMBOL>_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()   # analysis set only
```

## Suggested Direction

Build the episode detector as a single streaming pass over domain bars per
instrument (state: in/out of neighborhood, entry direction, episode age),
emitting one row per resolved episode for each arm; run the identical detector
over AVWAP and control levels so any definitional artifact cancels in Δ. Match
controls on the realized approach covariates (entry direction, band-width
regime, trailing-vol tercile) by stratified resampling before the contrast.
Keep the permutation strictly within matched strata to respect the matching.
