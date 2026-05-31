# Deliverable #2 — Predeclared Reference-Stack Specification

**Type:** Pre-registration / predeclared specification (the object EXP-037 and EXP-038 calibrate)
**Phase:** 006 — Thesis-Qualification Referee Calibration
**Date:** 2026-05-31
**Status:** Pre-execution governance approved / frozen for EXP-037 scope
**Companions:** [`design.md`](design.md) · `docs/planning/charter.md` · `docs/planning/state-and-open-decisions.md`
**Provenance of the transcribed stack:** `python/experiments/EXP-036/code/run_experiment.py` (canonical Phase-005 instance; constants verified identical in EXP-034/035/036).

## 0. Purpose and predeclaration discipline

This document freezes the **baseline referee under test** and the **calibration harness** around it, *before any calibration code runs*. Per binding constraint 13, every evidentiary threshold here is **measured first and never tuned afterward to make theses pass**. Two classes of content are kept visibly distinct:

- **Part 1 — transcribed and frozen.** The existing stack's rules, read verbatim from EXP-036 with line provenance. Nothing here is a new choice; it is a faithful record of the gate that closed Phases 003–005.
- **Parts 2–4 — harness constructs now frozen by governance.** The four constructs the stack never contained (economic materiality + proxy costs, harness DoF + stopping rule, frozen battery + second-order holdout, compute budget) and the calibration methods (null construction, synthetic family). These carry concrete values; where a value is a judgement call rather than a transcription, it is named as a proxy or calibration design choice.

These values are locked for EXP-037/EXP-038. Any later change requires a dated predeclared amendment with a stated, non-outcome-driven rationale (§6).

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

## Part 2 — Constructs the stack lacks (frozen by governance)

These are added **around** the frozen stack, never **into** it. They do not alter E1–E7.

### 2.1 Economic materiality + proxy-cost regimes (constraint 11)

The frozen-stack verdict is computed exactly as EXP-036 computed it: **κ = 0, no cost gate, no altered contrast, no modified E5 rule**. This κ=0 verdict is the primary calibration object for the §5.6 ruling. It answers: what are the operating characteristics of the stack that actually closed Phases 003-005?

Economic materiality is added **around** that verdict as a separately labelled survival axis. It never changes whether the frozen stack returns `FOR`, `STATE_DIFFERENTIATION_ONLY`, `HORIZON_DEPENDENT`, `INCONCLUSIVE`, or `AGAINST`.

**Materiality statistic.** For each extreme-state trade, define the executable strategy return `s = d·r`, where `d ∈ {+1, -1}` and `r` is the real next-open -> next-close log return. For instrument `i`, proxy-cost regime `g`, and minimum net-surplus floor `η_i`, compute:

`StrategySurplus_{i,g} = mean_ext(s) - κ_{i,g} - η_i`

The CI for `StrategySurplus` is estimated by the same episode bootstrap convention as E4, but on the extreme-state strategy-return episodes only. A cell survives materiality for regime `g` iff the **test-segment bootstrap lower bound of `StrategySurplus_{i,g}` > 0** and the **train-segment point estimate of `StrategySurplus_{i,g}` > 0**. This is a P&L/materiality label, not an evidentiary-stack leg.

`Delta_neutral` and `Delta_control` remain unshifted contrasts. In particular, `Delta_control` is not charged a full round-trip cost because it is a contrast between two direction rules on the same traded bars, not a standalone strategy P&L.

**Frozen proxy round-trip costs `κ` and net-surplus floors `η`** (basis points of notional per round trip; 1 bp = 1e-4 ≈ 1e-4 in log-return):

| Instrument | Low κ | Central κ | Stress κ | Net-surplus floor η | Rationale |
|---|---:|---:|---:|---:|---|
| EURUSD | 0.4 bp | 1.0 bp | 2.5 bp | 0.5 bp | tight major FX spread; require sub-bp post-cost surplus |
| XAUUSD | 1.5 bp | 4.0 bp | 10 bp | 1.0 bp | metal spread + slippage wider than FX |
| USTEC | 1.0 bp | 3.0 bp | 8 bp | 1.0 bp | index CFD spread/slippage; require at least 1 bp net surplus |
| BTCUSD | 3.0 bp | 8.0 bp | 20 bp | 2.0 bp | crypto spread/slippage and weekend gaps; higher minimum surplus |

Report every power result in two columns: (a) frozen-stack verdict at κ=0 and (b) materiality survival under low/central/stress. If these disagree, the report says so directly rather than folding cost into the stack.

### 2.2 Harness degrees of freedom + explicit stopping rule (constraint 7)

The calibrator has its own researcher DoF; left unbounded, the regress is infinite (a meta-calibrator for the calibrator, ad infinitum). The regress is stopped **at one level**, declared now:

- **Pre-registered DoF (fixed before any run):** (a) null-construction method and its block-length grid (§3); (b) the synthetic-effect family — mechanisms and parameter grid (§4); (c) inner-bootstrap B and CI level (inherited from E4); (d) RNG seed ranges (§2.3).
- **Stopping rule (predeclared):** we run the **fixed, enumerated** synthetic family **once**. The H0/H1 verdict *is* the observed sensitivity of apparent MDE across that fixed family (charter §2). We **do not** iterate the generator, add families, or re-tune effect sizes after seeing whether power looks stable — doing so would be exactly the "rescue the cure" move the charter forbids. We **do not** build a meta-generator to calibrate the generator; instead we *report* the family-sensitivity as the finding and bound it. If sensitivity is large, that is H0 (a result), not a prompt to search for a more flattering family.
- **Audit:** the generator config, seeds, and effect grid are emitted to `results/` as a manifest so the harness DoF are auditable after the fact.

### 2.3 Frozen calibration battery + second-order holdout (constraint 10)

To prevent the referee from overfitting its own calibration suite, the battery is **versioned and frozen**, and a **second-order holdout** of calibration cases is reserved.

**Battery definition (v1, frozen on governance approval).** A *case* = (instrument, timeframe, null-or-effect configuration, RNG seed). The battery is the full predeclared grid of cases over the 4 instruments × {1h, 4h} × the null/effect configs of §3–§4.

**Partition (frozen).** The partition is by seed/configuration, not by instrument, so the trusted battery retains all four instruments and preserves the stack's `k = 2 of 4` replication behavior.

- **Development battery** — used while building/debugging the harness: all instruments and both timeframes, **even** seed indices, excluding the reserved highest-magnitude effect row for every mechanism.
- **Second-order holdout** — never inspected during harness development: all instruments and both timeframes, **odd** seed indices, plus the reserved highest-magnitude effect row for every mechanism under all seeds.

Operating characteristics from the development battery are labelled **in-sample**. **Trust attaches only to the second-order-holdout numbers.** The partition is fixed here and never re-drawn to improve a result. (Note: this is distinct from, and additional to, the untouched 30% global *market* holdout, which neither battery touches.)

### 2.4 Compute budget (constraint 6 / D7)

The harness must be affordable relative to the research it referees. The frozen stack's E4 bootstrap remains **B = 10,000** for every calibration evaluation; reducing B would calibrate a different, noisier CI-boundary object.

**Budget unit.** One full-stack equivalent (FSE) = one evaluation across 4 instruments × 2 timeframes × 2 horizons × 2 segments = 32 episode-bootstrap cells, each with B = 10,000 and the EXP-036 2,000,000 index-cell cap.

| Quantity | Budget |
|---|---:|
| Part A null realizations | 150 FSE per block length × 3 block lengths = 450 FSE per pass; **≤ 2 passes (≤ 900 FSE)** incl. the EXP-040 re-run (AM-1.A4) |
| Part B power grid | 5 mechanisms × 4 magnitudes × 3 regime locations × 12 trusted seeds = 720 FSE |
| Decay/correlation stress slices | ≤ 120 additional FSE, only at the central magnitude row |
| Total phase calibration cap | **≤ 1,740 FSE** (AM-1.A4; was ≤ 1,290 FSE) |
| Wall-clock target | ≤ 30 CPU-hours total for Part A + Part B (≈1.1 CPU-h at the measured ≈2.2 CPU-s/FSE) |

**Derivation.** The 30 CPU-hour target implies an average cap of about 84 CPU-seconds per FSE (`30h × 3600 / 1290`). EXP-037 must profile the first 10 FSE before any long run. If the median profiled cost is >84 CPU-seconds/FSE, the predeclared downscale is: Part A falls to 100 realizations per block length and Part B trusted seeds fall from 12 to 8, preserving all mechanisms, magnitudes, regimes, and the second-order holdout. If the downscaled plan still profiles above the 30 CPU-hour target, the experiment stops before execution and reports compute infeasibility as a design finding.

The downscale rule protects family diversity over replication count because family diversity is the H0/H1 test. No mechanism may be dropped for speed after results are seen.

---

## Part 3 — Null construction for Part A (EXP-037)

> **AMENDED 2026-05-31 (AM-1) for the EXP-040 re-run — see §6 Amendment Log.** EXP-037 reached the predeclared "Evidence AGAINST measurement validity" branch: the descriptor resampler below (method item 1) and the return-autocorrelation diagnostic below both fail realism *structurally* (not from data or the stack). The mid-phase reflection ([`mid-phase-reflection.md`](mid-phase-reflection.md)) supersedes method item 1 with a first-order Markov episode-label descriptor null (AM-1.A1) and the autocorr-sign diagnostic with a noise-floored gate (AM-1.A2), and adds a control-leg construct-validity sub-check (AM-1.A3). The descriptor diagnostic tolerances (±5% / ±10%), the cross-correlation gate (Frobenius ≤ 0.20), the block grid `L ∈ {20,60,240}`, the 150-realization count, the second-order-holdout trust partition, and the κ=0 FPR definition are **unchanged**. The frozen stack (Part 1) is untouched. The original text is retained below for provenance; for EXP-040 read it through AM-1.

Trustworthy half. The null must **break the candidate's conditioning relationship while preserving** serial dependence, volatility clustering, calendar structure, and cross-market correlation (charter §3).

- **Method (predeclared):** independently resample two causal streams, then pair them:
  1. the descriptor stream `(Bucket, D)` is resampled in circular blocks whose boundaries are snapped to complete state episodes, preserving the descriptor's own run/episode structure;
  2. the return/control stream `(RetNextBar, RetFourBar, Control)` is resampled in circular time blocks using common start indices across instruments, preserving serial dependence, volatility clustering, calendar/session structure, and cross-instrument return correlation.

  The descriptor-stream seed and return-stream seed are independent, so the state→return conditioning relationship is broken while each stream's own dependence structure is retained. Naive row shuffles are diagnostic-only and cannot supply the trusted FPR.
- **Block-length grid:** mean return-stream block length `L ∈ {20, 60, 240}` bars. The headline Part A result is the **FPR envelope across all valid L values**, not a selected favorite L. Per-L results are still reported.
- **Null-validity diagnostics:** before any FPR is trusted, the null must pass diagnostics per instrument×timeframe: descriptor episode count within ±5% of observed, median and p90 episode length within ±10% of observed, return lag-1/lag-5 autocorrelation signs unchanged, and cross-instrument return-correlation matrix Frobenius distance ≤0.20 versus observed. A null realization family that fails the episode diagnostics is invalid for trusted FPR; a return-diagnostic failure is reported and the FPR for that L is labelled untrusted.
- **Preserved / destroyed ledger (reported):** preserved = descriptor episode structure, return autocorrelation, volatility clustering, calendar/session effects, cross-instrument correlation; destroyed = the descriptor→return relationship. The trustworthiness of the null calibration is exactly the realism shown by this ledger.
- **Outputs:** empirical **FPR** of the full frozen stack at κ=0; representation/adjudicability pass rates for E1; cell-level neutral and control false-pass rates among adjudicable cells; both-contrast cell pass rate; and aggregate false-pass rates for the E5∧E6 replication conjunction. E6 is reported only as an aggregate stack-level event, not as a per-cell leg.

---

## Part 4 — Synthetic-effect family for Part B (EXP-038 + EXP-039)

Fragile half. Plant effects of **known** magnitude/structure into accepted null-resampled series from Part A, varied by **mechanism and parameter** (charter §4). Power therefore conditions on the null's realism and never pretends that latent real structure has been removed from raw data by assumption. The headline is the **sensitivity of apparent MDE to the family**, plus a power **surface** — never a scalar.

Part B is split across experiments so each stays inside the per-experiment complexity budget and asks one falsifiable question (the mid-phase reflection fixes the final grouping off the EXP-037 null profile): **EXP-038** carries mechanism 1 (directional drift) — the canonical, easiest-to-detect case that validates the harness and anchors the MDE comparison; **EXP-039** carries the structural-blindness mechanisms 2–5 and reports how far each diverges from the drift MDE. That cross-mechanism divergence is the H0/H1 statistic. EXP-039 may be split further by the reflection if the budget requires.

**Mechanisms (≤5, enumerated, fixed).** Every mechanism included in the H0/H1 sensitivity statistic must alter the real OHLC path that the stack consumes, so a zero-power result is not tautological. Mechanisms that the next-open -> next-close metric provably cannot observe are reported only as construct-validity diagnostics and are excluded from the MDE-spread statistic.

| # | Mechanism | Observable planting into OHLC | Attribution rule |
|---|---|---|---|
| 1 | **Directional drift** | For each eligible extreme-state observation at bar `t`, shift the next bar's close so `r_{t+1}' = r_{t+1} + d·m`; adjust high/low minimally to contain open/close. | If undetected, attribute to gate stringency or insufficient magnitude. |
| 2 | **Risk-filtered directional drift** | Plant the same positive `d·r` mean as #1 only inside the predeclared volatility regime and reduce adverse-tail realizations by the same magnitude budget; OHLC remains valid. Pure variance-only filtering is a separate construct-validity diagnostic, not an MDE mechanism. | If mean-shift variant is detected but pure variance-only is not, attribute pure-variance miss to metric construct mismatch. |
| 3 | **Entry-timing improvement** | Improve the next executable open by `d·m` while holding the next close path fixed, so the stack's own next-open -> next-close return sees the entry advantage; adjust high/low minimally. Intrabar timing that does not change the next executable open is construct-mismatch only. | If the observable open-improvement variant is undetected, attribute to stringency; if only true intrabar timing is invisible, attribute to metric construct mismatch. |
| 4 | **Signed magnitude information** | Amplify favorable `d·r` tail realizations and cap unfavorable tail realizations within the same magnitude budget, producing an observable direction-adjusted mean change. Pure unsigned magnitude with zero `d·r` mean is construct-mismatch only. | Include the signed variant in MDE; report the pure unsigned variant outside H0/H1. |
| 5 | **Marginal contribution beyond control** | Plant `d·r` improvement only where descriptor direction `d` disagrees with or is orthogonal to control sign `c`, increasing `mean((d - c)·r)` without granting the control the same edge. | Directly probes E3; if undetected, attribute to matched-control gate stringency. |

**Parameter grid.**

- Magnitude `m ∈ {0.5, 1.0, 2.0, 4.0} × (central κ_i + η_i)` by instrument.
- Regime location `∈ {all eligible extremes, high-volatility tercile, low-volatility tercile}`, where volatility terciles are computed on the train segment and applied chronologically.
- Decay/correlation stress slices are not part of the full grid: at the central magnitude row only, run `{no decay, 50% test-segment decay}` and `{independent-by-instrument, common cross-instrument planted shock}`. These slices satisfy constraint 5 without exploding the grid.

**Planting protocol:** effects are injected on the holdout-excluded analysis series only. The global market holdout remains absent before aggregation, resampling, and effect planting. The stack is run unchanged against each planted OHLC case. For each mechanism × magnitude × regime cell, record frozen-stack verdict, replication breadth, materiality survival by proxy-cost regime, and trusted second-order-holdout TPR.

**MDE and founding-thesis decision rule.**

- Per mechanism, the empirical MDE is the smallest magnitude whose trusted second-order-holdout `FOR` TPR is ≥0.80 and whose Wilson 90% lower bound is ≥0.60. If no tested magnitude meets that rule, the mechanism's MDE is `> max_grid`.
- Sensitivity statistic: `S = max(MDE_m) / min(MDE_m)` across the five observable mechanisms, treating any `> max_grid` mechanism as exceeding the largest finite MDE.
- **H1-stable:** the directional-drift anchor has finite MDE, every observable mechanism has finite MDE, and `S ≤ 2.0`.
- **H0-family-dependent:** the directional-drift anchor has finite MDE and either any observable mechanism has `MDE > max_grid` or `S > 2.0`.
- **Near-impassable / inconclusive for H1:** the directional-drift anchor itself has `MDE > max_grid`; this is reported as conjunctive-stringency evidence, not as license to loosen gates.

---

## Part 5 — What each experiment computes

| Experiment | Computes | Headline output | Trust |
|---|---|---|---|
| **EXP-037** (Part A) | stack FPR + adjudicability/cell/aggregate false-pass under the §3 nulls (× block-length grid); also builds the shared harness | FPR envelope + leak/over-reject profile | trustworthy if null diagnostics pass |
| *(mid-phase reflection)* | reads the null/per-leg profile → fixes the Stage B mechanism grouping and targets | Stage B directive | — |
| **EXP-038** (Part B, drift) | TPR / power surface for the directional-drift mechanism over the §4 parameter axes; anchor MDE | drift power surface + anchor MDE | fragile, conditioned |
| **EXP-039** (Part B, blind-spot) | per-mechanism power surface + MDE for mechanisms 2–5; divergence from the drift MDE | cross-mechanism MDE sensitivity = the H0/H1 verdict | fragile, conditioned |

Every power experiment reports the frozen-stack verdict at κ=0 and the separate **materiality-survival axis** per proxy-cost regime (§2.1). Every number is labelled development-battery (in-sample) or second-order-holdout (trusted) per §2.3.

---

## Part 6 — Predeclaration & change control

- All Part 1 values are transcriptions and are not subject to change (changing them would mean calibrating a different stack).
- All formerly review-tagged values (proxy costs and surplus floors §2.1, battery partition §2.3, compute budget §2.4, block grid §3, mechanism/parameter grid and H0/H1 cutoff §4) are fixed by this document and thereafter only by a dated amendment in this file stating a non-outcome-driven rationale (constraint 13). No value is ever changed because a thesis — or the stack — "kept failing."
- The harness DoF manifest (§2.2) is emitted with results so the predeclaration is auditable.

### Amendment Log

**AM-1 — 2026-05-31 — Null-construction correction for the EXP-040 Stage-A re-run.**
Issued by the Phase 006 mid-phase reflection ([`mid-phase-reflection.md`](mid-phase-reflection.md)) after EXP-037 hit its predeclared "Evidence AGAINST measurement validity" branch (`DescriptorPass = 0/450`, `ReturnAutocorrPass = 0/450`). Non-outcome-driven rationale: both failures are structural properties of the *null method*, provable from the resampler/gate definitions and reproduced by EXP-037 audit SC-2, independent of any FPR or stack verdict. No evidentiary threshold or admissibility rule (Part 1) is changed; the frozen stack is byte-for-byte the EXP-036 stack.

- **A1 (supersedes §3 method item 1 — descriptor stream).** The descriptor `(Bucket, D)` stream is resampled by a **first-order Markov episode-label model with empirical per-label durations**: estimate the zero-diagonal episode-label transition matrix `P` per instrument×timeframe×segment, generate a same-length (`n_ep`) label sequence on an independent descriptor RNG, draw each episode's duration with replacement from the observed per-label pool, expand to per-row buckets, truncate/pad to the segment length, and map bucket→`D` deterministically. Same-bucket adjacency is structurally forbidden, so `_episode_ids` snapping is a no-op. The descriptor diagnostic tolerances (±5% count, ±10% median/p90) are **unchanged** — the construction is raised to clear the existing bar.
- **A2 (supersedes §3 diagnostics — return-autocorr gate).** Replace "lag-1/lag-5 autocorrelation signs unchanged across all 64 cells" with a **noise-floored sign-agreement gate**: evaluate sign agreement only on cells with `|ρ_obs| > ρ_floor`, `ρ_floor = 1.96/√N_seg`, requiring zero mismatches among those above-floor cells; below-floor cells are excluded (a sampling-zero autocorrelation has no sign to preserve); a segment with no above-floor cell is "no testable autocorr structure" and does not block trust.
- **A3 (adds an EXP-040 diagnostic — control leg).** Once a valid `L` exists, decompose `Delta_control` under the null into its `mean_ext(d·r)` and `mean_ext(c·r)` components to test whether EXP-037's untrusted control-leg elevation is the control's own preserved `c·r` structure vs descriptor→return leakage. Reported diagnostic only; **not** a change to E3 and not a trust gate.
- **A4 (amends §2.4 compute budget).** Part A allowance raised from one pass (450 FSE) to ≤ 2 passes (≤ 900 FSE) to account for the EXP-040 re-run; phase total cap raised ≤1,290 → **≤ 1,740 FSE**. EXP-037 profiled at ≈2.2 CPU-s/FSE, so the full phase remains ≈1.1 CPU-hours, ≪ the 30 CPU-hour target; constraint 6 disclosure, not absorption. The profile-first-10-FSE / downscale-to-100-realizations rule is unchanged and inherited by EXP-040.

**Regress bound.** AM-1 is the single null correction permitted by the §2.2 stopping rule. If the corrected null also fails its (unchanged) realism diagnostics, the phase reports dependence-preserving-null infeasibility for this descriptor/stack as an H0-adjacent finding (honesty clause C4); no third null is constructed.

## Governance lock decisions

1. **Proxy-cost numbers and materiality floors (§2.1)** are frozen as proxy regimes, not broker-validated cost estimates.
2. **Battery partition (§2.3)** is seed/config based and retains all four instruments in the second-order holdout so `k = 2 of 4` remains observable.
3. **Compute budget (§2.4)** keeps B = 10,000, caps the phase at 1,290 FSE / 30 CPU-hours, and defines the pre-execution downscale/stop rule.
4. **Null construction (§3)** preserves descriptor episodes and reports the FPR envelope across valid block lengths.
5. **Synthetic family (§4)** includes only observable OHLC mechanisms in the H0/H1 MDE-spread statistic and predeclares the numeric stability cutoff `S ≤ 2.0`.

This document is frozen by pre-execution governance approval, and EXP-037 (Part A null calibration) may now be scoped against it.
