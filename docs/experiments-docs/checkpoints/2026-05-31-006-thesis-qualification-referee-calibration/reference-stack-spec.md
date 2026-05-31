# Deliverable #2 — Predeclared Reference-Stack Specification

**Type:** Pre-registration / predeclared specification (the object EXP-037 and EXP-038 calibrate)
**Phase:** 006 — Thesis-Qualification Referee Calibration
**Date:** 2026-05-31
**Status:** Draft for pre-execution governance review (charter deliverable #2)
**Companions:** [`design.md`](design.md) · `docs/planning/charter.md` · `docs/planning/state-and-open-decisions.md`
**Provenance of the transcribed stack:** `python/experiments/EXP-036/code/run_experiment.py` (canonical Phase-005 instance; constants verified identical in EXP-034/035/036).

## 0. Purpose and predeclaration discipline

This document freezes the **baseline referee under test** and the **calibration harness** around it, *before any calibration code runs*. Per binding constraint 13, every evidentiary threshold here is **measured first and never tuned afterward to make theses pass**. Two classes of content are kept visibly distinct:

- **Part 1 — transcribed and frozen.** The existing stack's rules, read verbatim from EXP-036 with line provenance. Nothing here is a new choice; it is a faithful record of the gate that closed Phases 003–005.
- **Parts 2–4 — drafted for review.** The four constructs the stack never contained (economic materiality + proxy costs, harness DoF + stopping rule, frozen battery + second-order holdout, compute budget) and the calibration methods (null construction, synthetic family). These carry **proposed concrete values** and are the substance of the governance review. Where a value is a judgement call rather than a transcription, it is tagged **[REVIEW]**.

Once this document passes pre-execution governance, the values in it are locked for EXP-037/EXP-038. Any later change requires a dated predeclared amendment with a stated, non-outcome-driven rationale (§6).

---

## Part 1 — The baseline referee, transcribed and frozen

The stack is specified in two layers (constraint 9). **Calibration varies the evidentiary layer only; the admissibility layer is held fixed** and is never assigned an operating characteristic.

### 1.1 Admissibility layer (validity preconditions — FIXED, not calibrated)

| Precondition | Rule | Provenance |
|---|---|---|
| Holdout exclusion | Final 30% global holdout removed from the 1-minute series *before* aggregation/feature/return | `load_analysis_timebars` / strict slice |
| No look-ahead | Descriptor observed at bar close; earliest entry = next bar open; forward bars taken within the same segment (segment-boundary bars are return-ineligible) | `_add_returns_and_control` L155–185 |
| Real-price outcomes | All returns are log returns of **real** OHLC; no synthetic (HA/Renko) price in any measured return | `_add_returns_and_control` L170–178 |
| Inference unit | Independent state **episode** = maximal run of consecutive equal, non-null buckets (a null breaks the run); naive row-level resample is **diagnostic only** | `_episode_ids` L218–232; `_bar_level_agg` L357–367 |
| Temporal alignment | `CloseTime` on aggregated real bars; never bar index | throughout |
| Aggregation | Strict clock-aligned (`min_coverage=None`, exactly-N-bar windows) | `STRICT_MIN_COVERAGE` L60 |
| Train/test split | Nested chronological 0.70 train fraction *inside* the analysis set | `ANALYSIS_TRAIN_FRACTION` L59, `_add_segment` L92–104 |
| Predeclaration | All parameters/thresholds/baselines fixed before outcomes inspected | this document |

These do not move during calibration. A calibration procedure that softens any of them (look-ahead, holdout contamination, synthetic-price returns, index alignment) is a category error and is rejected, not measured.

### 1.2 Evidentiary layer (the objects whose error profiles are measured)

All values transcribed verbatim; **frozen**.

**(E1) Representation floors** — per state, per segment (`_floor_ok` L391–395):

| | Train | Test |
|---|---|---|
| Rows (return-eligible) | ≥ 100 | ≥ 50 |
| Independent episodes | ≥ 30 | ≥ 15 |

Provenance: `MIN_ROWS_TRAIN=100`, `MIN_ROWS_TEST=50`, `MIN_EPISODES_TRAIN=30`, `MIN_EPISODES_TEST=15` (L65–68). Adjudicability (`_contrast_adjudicable` L398–403): the **neutral** contrast requires *both* extreme buckets **and** the middle bucket to clear floors; the **control** contrast requires *both* extremes. A contrast that is not adjudicable in *both* segments is excluded from the tally (returns `None`), not counted as a failure (`_replicates` L479–497).

**(E2) Neutral-baseline gate** — `Delta_neutral` (`_stat_values` L334–351):
`Delta_neutral = mean_ext(d·r) − mu_mid·mean_ext(d)`, where `d ∈ {+1 (top), −1 (bottom)}` is the predeclared directional implication, `r` the executable next-bar log return, and `mu_mid` the **measured** middle-bucket mean. Estimated by a **two-sample episode bootstrap** that resamples extreme episodes and middle episodes independently with replacement and **recomputes `mu_mid` on each draw**, so the baseline's sampling error enters the CI (`_episode_bootstrap` L277–331).

**(E3) Matched-control gate** — `Delta_control` (`_stat_values` L343):
`Delta_control = mean_ext((d − c)·r)`, where `c = sign(close − prior_close)` is a deliberately naive prior-bar-momentum-sign control (information available at bar *i*; `_add_returns_and_control` L179–182). Paired head-to-head on the descriptor's own traded bars.

**(E4) Inference & CI** — episode-level bootstrap, **B = 10,000** resamples, fixed seed 42 with deterministic per-cell offsets, two-sided **95% CI** via the 2.5%/97.5% empirical quantiles (`BOOTSTRAP_N` L71; quantiles L328–329; cell-budget cap 2,000,000 index cells L73).

**(E5) Replication / sign-preservation rule** (`_replicates` L479–497): a contrast *replicates* for an instrument×timeframe iff **test-segment CI lower bound > 0 AND train-segment point estimate > 0** (same-signed, test CI excludes zero positively).

**(E6) Replication breadth** — **k = 2 distinct instruments** (`QUALIFYING_INSTRUMENT_FLOOR=2` L69); the independence unit is the **instrument**. Multiple timeframes/horizons of one instrument do not count as independent replication.

**(E7) Secondary horizon** — a single predeclared **4-bar** hold (`SECONDARY_HOLD=4` L62), enter next open / exit close of the 4th subsequent bar, under asymmetric semantics: it **cannot manufacture a primary pass** (it can only reopen at the longer horizon).

**Fixed feature parameters** (part of the stack as applied, not separately tunable here): lookback 20 bars (L56); buckets bottom ≤ 0.20 / top ≥ 0.80 / middle otherwise (L57–58).

### 1.3 The verdict ladder (already graded — constraint 12 in embryo)

Predeclared outcomes (`_verdict` L526–562), evaluated on the per-timeframe maxima of the passing-instrument tallies:

| Outcome | Condition |
|---|---|
| **FOR** (edge candidate) | next-bar `Delta_neutral` AND `Delta_control` both replicate on ≥2 instruments |
| **STATE_DIFFERENTIATION_ONLY** | next-bar `Delta_neutral` replicates on ≥2 but `Delta_control` does not |
| **HORIZON_DEPENDENT** | next-bar both-contrast fails but the 4-bar both-contrast replicates on ≥2 |
| **INCONCLUSIVE** | best next-bar both-contrast pass = 1, or <2 instruments are adjudicable for the control gate |
| **AGAINST** (refuted) | ≥2 instruments adjudicable for control, but <2 replicate at either horizon |

### 1.4 Canonical-version note

EXP-036 is fixed as **the canonical reference version**. The closure stack drifted in shape across earlier phases (e.g. EXP-020/030 did not expose the same named floor/k constants). This calibration measures the EXP-036 form; the §5.6 ruling therefore reads *"the EXP-036 closure stack is/isn't passable,"* and any claim about Phases 003–004 inherits the caveat that those phases used a structurally-adjacent but not byte-identical instance.

---

## Part 2 — Constructs the stack lacks (drafted for review)

These are added **around** the frozen stack, never **into** it. They do not alter E1–E7.

### 2.1 Economic materiality + proxy-cost regimes (constraint 11)

The stack tests "different from zero," not "larger than costs." The data carries no spread/slippage fields, so frictions are expressed as **predeclared per-instrument proxy round-trip costs** in three regimes. A pass must clear the materiality bar *in addition to* E5, and survival is reported **per regime**, never under one hidden cost.

**Materiality rule (proposed).** For a given proxy round-trip cost `κ` (in log-return units, charged once per next-bar trade), recompute the net contrast `Delta_neutral^net = Delta_neutral − κ` and require the **test-CI-lower of the net effect > 0 AND train net point > 0** (E5 applied to the cost-shifted statistic). Report the verdict ladder separately for each of low/central/stress.

**Proposed proxy round-trip costs `κ` [REVIEW]** (basis points of notional per round trip; 1 bp = 1e-4 ≈ 1e-4 in log-return):

| Instrument | Low | Central | Stress | Rationale |
|---|---|---|---|---|
| EURUSD | 0.4 bp | 1.0 bp | 2.5 bp | tight major FX spread; stress = news/illiquid session |
| XAUUSD | 1.5 bp | 4.0 bp | 10 bp | metal spread + slippage wider than FX |
| USTEC | 1.0 bp | 3.0 bp | 8 bp | index CFD ~1 pt on ~2e4 + slippage |
| BTCUSD | 3.0 bp | 8.0 bp | 20 bp | crypto spread/slippage and weekend gaps |

These four rows are the **primary governance-review item**: the numbers are judgement calls, not transcriptions. They are deliberately conservative-leaning; the central regime is the headline, low/stress bracket it. No κ may be re-tuned after results are seen.

### 2.2 Harness degrees of freedom + explicit stopping rule (constraint 7)

The calibrator has its own researcher DoF; left unbounded, the regress is infinite (a meta-calibrator for the calibrator, ad infinitum). The regress is stopped **at one level**, declared now:

- **Pre-registered DoF (fixed before any run):** (a) null-construction method and its block-length grid (§3); (b) the synthetic-effect family — mechanisms and parameter grid (§4); (c) inner-bootstrap B and CI level (inherited from E4); (d) RNG seed ranges (§2.3).
- **Stopping rule (predeclared):** we run the **fixed, enumerated** synthetic family **once**. The H0/H1 verdict *is* the observed sensitivity of apparent MDE across that fixed family (charter §2). We **do not** iterate the generator, add families, or re-tune effect sizes after seeing whether power looks stable — doing so would be exactly the "rescue the cure" move the charter forbids. We **do not** build a meta-generator to calibrate the generator; instead we *report* the family-sensitivity as the finding and bound it. If sensitivity is large, that is H0 (a result), not a prompt to search for a more flattering family.
- **Audit:** the generator config, seeds, and effect grid are emitted to `results/` as a manifest so the harness DoF are auditable after the fact.

### 2.3 Frozen calibration battery + second-order holdout (constraint 10)

To prevent the referee from overfitting its own calibration suite, the battery is **versioned and frozen**, and a **second-order holdout** of calibration cases is reserved.

**Battery definition (v1, frozen on governance approval).** A *case* = (instrument, timeframe, null-or-effect configuration, RNG seed). The battery is the full predeclared grid of cases over the 4 instruments × {1h, 4h} × the null/effect configs of §3–§4.

**Partition [REVIEW]:**

- **Development battery** — used while building/debugging the harness: instruments {EURUSD, XAUUSD} and **even** seed indices.
- **Second-order holdout** — *never* inspected during harness development; the reported operating characteristics are drawn from it: instruments {USTEC, BTCUSD} and **odd** seed indices, plus a reserved block of effect-parameter cells (the highest-magnitude row of each mechanism) held out entirely.

Operating characteristics from the development battery are labelled **in-sample**; **trust attaches only to the second-order-holdout numbers.** The partition is fixed here and never re-drawn to improve a result. (Note: this is distinct from, and additional to, the untouched 30% global *market* holdout, which neither battery touches.)

### 2.4 Compute budget (constraint 6 / D7)

The harness must be affordable relative to the research it referees. Anchored to EXP-036's cost (B=10,000 inner resamples, 2M-cell cap), the budget is bounded **[REVIEW]**:

| Quantity | Budget |
|---|---|
| Part A null realizations (per instrument×tf) | 2,000 |
| Part B effect grid | ≤ 5 mechanisms × 4 magnitudes × 3 regimes (§4) |
| Inner bootstrap B during calibration | 2,000 (reduced from 10,000 for the *outer* calibration loop; the *stack's own* E4 = 10,000 is preserved only for the single observed-stack reference run) |
| Wall-clock target | ≤ 12 CPU-hours total for Part A + Part B |
| Downscale rule | if the target is exceeded, reduce Part A null realizations to 1,000 before reducing any effect-family coverage; the family's diversity is protected over replication count, because family diversity *is* the H0 test |

A calibration regime that cannot fit this budget without gutting family diversity is itself a reportable design finding (the cure costs more than the disease), not a silent overrun.

---

## Part 3 — Null construction for Part A (EXP-037)

Trustworthy half. The null must **break the candidate's conditioning relationship while preserving** serial dependence, volatility clustering, calendar structure, and cross-market correlation (charter §3).

- **Method (predeclared):** stationary / circular-block bootstrap of the real per-instrument return series, composed with a **permutation of the descriptor labels** relative to returns so the bucket→return conditioning is destroyed while the marginal return process is preserved. For cross-series structure, blocks are drawn on a common time index across instruments (preserving cross-market correlation).
- **Block-length grid [REVIEW]:** mean block length `L ∈ {20, 60, 240}` bars, reported separately — block length is a null-realism DoF and its effect on FPR is itself a diagnostic, not a single hidden choice.
- **Preserved / destroyed ledger (reported):** preserved = return autocorrelation, volatility clustering, calendar/session effects, cross-instrument correlation; destroyed = the descriptor→return relationship. A null that visibly damages a preserved property (checked by summary diagnostics vs the real series) is flagged; the FPR estimate's trust is exactly the realism of this null.
- **Outputs:** empirical **FPR** of the full stack at its declared thresholds, and the **per-leg false-pass rate** of each of E1/E2/E3/E5/E6 individually (which legs leak, which over-reject).

---

## Part 4 — Synthetic-effect family for Part B (EXP-038)

Fragile half. Plant effects of **known** magnitude/structure into the real (or null-resampled) series, varied by **mechanism and parameter** (charter §4). The headline is the **sensitivity of apparent MDE to the family**, plus a power **surface** — never a scalar.

**Mechanisms (≤5, enumerated, fixed) [REVIEW]:**

1. **Directional drift** — a small state-conditioned mean shift in `d·r`.
2. **Volatility/risk filtering** — the state predicts lower variance, not mean (tests whether a directional-return gate is blind to a risk edge).
3. **Timing improvement** — the same total move, better entry timing within the bar window.
4. **Sizing information** — the state predicts the *magnitude* of the move, not its sign.
5. **Marginal contribution** — the state adds information *beyond* the naive momentum control `c` (directly probes the matched-control leg E3).

Mechanisms 2–4 are the load-bearing ones: they expose whether the stack is structurally blind to a whole *kind* of edge, which is the §5.6 question.

**Parameter axes (grid):** magnitude (4 levels spanning sub- to supra-threshold), regime location, persistence/decay (ties to constraint 5, alpha decay), cross-unit correlation of the planted effect.

**Planting protocol:** effects are injected on the holdout-excluded analysis series only; the stack is run unchanged against each planted case; for each (mechanism × magnitude × regime) cell we record whether the stack returns FOR and at what replication breadth, giving TPR and the empirical detectable-effect frontier per mechanism. **The MDE is read per mechanism and the spread across mechanisms is the H0/H1 statistic.**

---

## Part 5 — What each experiment computes

| Experiment | Computes | Headline output | Trust |
|---|---|---|---|
| **EXP-037** (Part A) | stack FPR + per-leg false-pass under the §3 nulls (× block-length grid) | FPR table + per-leg leak/over-reject profile | trustworthy |
| **EXP-038** (Part B) | TPR / power surface over §4 family; MDE per mechanism; cross-mechanism sensitivity | power surface + family-sensitivity = the H0/H1 verdict | fragile, conditioned |

Both report results **per proxy-cost regime** (§2.1) for the materiality-adjusted variant, and label every number as development-battery (in-sample) or second-order-holdout (trusted) per §2.3.

---

## Part 6 — Predeclaration & change control

- All Part 1 values are transcriptions and are not subject to change (changing them would mean calibrating a different stack).
- All `[REVIEW]` values (proxy costs §2.1, battery partition §2.3, compute budget §2.4, block grid §3, mechanism/parameter grid §4) are fixed by this document **once governance approves it**, and thereafter only by a dated amendment in this file stating a non-outcome-driven rationale (constraint 13). No value is ever changed because a thesis — or the stack — "kept failing."
- The harness DoF manifest (§2.2) is emitted with results so the predeclaration is auditable.

## Open items for governance review

1. **Proxy-cost numbers (§2.1)** — the four-instrument κ grid is the main judgement call; confirm or replace before approval.
2. **Battery partition (§2.3)** — holding out USTEC+BTCUSD by instrument trades realism for a clean second-order reserve; confirm this is the right axis (vs holding out by time block).
3. **Compute budget (§2.4)** — confirm the 12-CPU-hour target and the diversity-over-replication downscale priority.
4. **Block-length and mechanism grids (§3, §4)** — confirm the enumerated families are diverse *enough* to make the H0 sensitivity test honest without breaching the budget.

On approval, this document is frozen and EXP-037 (Part A null) is scoped against it.
