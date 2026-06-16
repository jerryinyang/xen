# Candidate Family: CF-HA-HARAMI-001 — Heiken Ashi Harami at Trend Exhaustion

**Status:** `REGISTERED` — 2026-06-14 (Phase 014 G0 PASS). All promotion conditions
met: (a) fixed first-branch primitives frozen as predeclared D0 defaults
(`docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/D0-predeclarations.md`);
(b) family and variant surface entered in
`docs/signal-registry/multiplicity-registry.md` (Phase 014 batch); (c) Phase 014
`design.md` finalized. Eligible for scoping; first EXP is EXP-048 (gated on VAL-004).
**Primary registry:** `docs/signal-registry/multiplicity-registry.md`
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/design.md`
**014-A experiments completed:** EXP-048 (READINESS_DELIVERED), EXP-049 (CAPTURE_READINESS_DELIVERED), EXP-050 (CONTEXT_CHARACTERISATION_DELIVERED), EXP-051 (STRONG_FILTER_CHARACTERISATION_DELIVERED) and EXP-052 (CONFIRM_CHARACTERISATION_DELIVERED).
**014-A G1 adjudicated 2026-06-15** (`checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G1-gate-review.md`): primitives READY; benchmark capture `CHARACTERISED_NOT_VIABLE` **on the unconditioned object only** — the **conditioned** family hypothesis (strong-move-qualified harami, anchored at the harami) was never run through an outcome read in 014-A, so it is **untested**. Family **OPEN**; operator directed proceed to **Phase 014-B** (no closure). The benchmark null, the missed conditioning, the reasoning trail, and the binding process lessons are recorded in `checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md` — **mandatory reading before scoping any 014-B experiment.**
**014-B opened 2026-06-15; G0-B PASS 2026-06-15** (`.../014-B-design.md`, `.../014-B-D0-addendum.md`): full conditioned barrier + position-management surface, **median** per-event expectancy endpoint (mean disclosed), intrabar fill correction, long-horizon availability; no intermediate gates, single G2 after the full slate. Next: scope EXP-053 (conditioned efficacy) after the mandatory lessons read.

This is a candidate family, not a proven strategy. Phase-plan content (014-A/B
experiment split, gate definitions, programme principles) lives in the Phase 014
`design.md`, not here.

## Thesis

A Heiken Ashi (HA) harami observed at the exhaustion of a strong impulsive move
marks a confirmed trend reversal with enough lead over the trend-change
confirmation to be tradable. The harami is the family **core**; the trend
substrate, strong-move filter, signal-confirmation variant, and 3-barrier
reversal framework exist only to qualify, contextualize, or capture the reversal
the harami predicts.

### Methodological inheritance (not a follow-up)

This family is defined by its core signal, not as a continuation of
`CF-AVWAP-001`. The prior family's closure shapes only *how* we validate here.
CF-AVWAP-001 exhausted every registered lever across nine phases; its binding
constraint was diagnosed as **capture geometry, not move availability** — median
lifetime peak MFE was ≈5–9× the frozen cost floor in every cell, yet no
deterministic exit converted that available move into net-of-cost P&L
(`docs/experiments-docs/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/retrospective.md`).
The lesson carried forward: **capture geometry is a first-class primitive in this
family — the 3-barrier reversal framework is validated with the same breadth as
the signal, including a gross capture-rate read in the first checkpoint, not
deferred as a late overlay.**

## Brainstorming Provenance

Promoted from the operator's harami draft. Original ideas and their registry
treatment:

| Original idea | Registry treatment |
| --- | --- |
| HA harami (prior HA body engulfs the latest HA body) as a reversal/exhaustion core signal. | Preserved as the fixed first-branch detector; reduced to its binding constraint below. |
| Categorise by the four bar-direction configurations (bull/bear → bull/bear). | Registered variant `CF-HA-HARAMI-001/BARCFG`; reachability/coverage derived analytically below, measured at readiness, never assumed uniform. |
| Direct signal vs signal+confirmation ("threshold" reached confirms reversal; stop-order entry). | Registered variant `CF-HA-HARAMI-001/CONFIRM`; both arms measured descriptively before any selection. |
| ATR-based ZigZag trend/move substrate on real bars. | Preserved as the fixed first-branch trend substrate (Wilder ATR, period 14, `ATR_MULT` 1.0). |
| Strong/impulsive-move and "end of trend" filters (statistical significance; HA-impulse run). | Registered variants `CF-HA-HARAMI-001/STRONG-STAT` and `/STRONG-HA`; off by default in the first branch. |
| 3-barrier reversal framework (favourable target, adverse target, third barrier) with `LOOKBACK` reference set. | Preserved as a first-class primitive; benchmark models fixed in the first branch, alternatives registered as variants below. |
| Volume-profile (POC / value-area) favourable targets. | Registered variant `CF-HA-HARAMI-001/VPTARGET`; lower priority — only `TickVolume` (broker tick *count*, not traded volume) is available; proxy limitation disclosed in any result that uses it. |
| Concept Characterization Analysis (prevalence/behaviour/outcome mapping per concept). | Adopted as the Phase 014-A/B methodology in the `design.md`; descriptive, no candidate-screening slot, no TEST reads. |

## Fixed First-Branch Definition

The "first branch" here is a set of **frozen primitive definitions**, not a frozen
end-to-end strategy — consistent with the build-from-primitives intent: validate
each primitive separately, then assemble only survivors. Each parameter below is a
**governance parameter** fixed per scope and ratified at the Phase 014 D0/G0; it is
never tuned against analysis-set outcomes. Sensitivity over any parameter is a
separate registered branch, not an in-place revision.

### Data Views

- Base source: 1-minute time bars from `data/timebars/`.
- Domains: 5m, 15m, 30m, 1h, 2h, 4h. **15m and 30m are new domains** requiring
  aggregation construction and VAL-001-style temporal-integrity validation before
  any analytical use (hard gate; see `design.md` §VAL gate).
- Domain construction: 5m strict coverage; 15m/30m/1h/2h/4h with
  `min_coverage=0.90`, matching the EXP-004/009 convention.
- Instruments: all 17 VAL-003-admitted instruments (BTCUSD, EURUSD, USTEC, XAUUSD,
  GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500,
  US2000, DE30, JP225). DE30 carries a truncated-coverage disclosure (broker
  history ends 2026-01-16). JP225-2h may carry a dropped-fraction disclosure under
  the harami event definition.
- **Total cells:** 17 × 6 = 102. Per the operator's "no blanket assumptions"
  decision, readiness **and** characterization run on all 102 cells from day one;
  no cell is excluded by assumption at the family level.

The final 30 percent global holdout is never loaded, inspected, run in cTrader, or
used for any registry decision. No new-universe row has been read under the HA-harami
event definition (VAL-003 admission and Phase 011 readiness/calibration/training read
new-universe first-70% rows for prior, non-harami work); the global holdout seal
carries forward unchanged.

### HA Harami Detector (core signal)

Computed on Heiken Ashi candles (`xen.heiken_ashi_generator`). Detection is
independent of the ZigZag substrate.

- `HA_0` = latest HA candle, `HA_1` = previous HA candle.
- `BODY_MAX = max(HAOpen, HAClose)`, `BODY_MIN = min(HAOpen, HAClose)`.
- Harami: `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0` (latest body strictly
  inside the prior body).

**Construction-derived reduction (binding constraint).** HA pins each candle's
open to the midpoint of the prior body:
`HA_Open_0 = (HA_Open_1 + HA_Close_1)/2`, the exact centre of `[BODY_MIN_1,
BODY_MAX_1]` and therefore strictly interior whenever the prior body is
non-degenerate. One endpoint of the latest body is engulfed *by construction*, so
the harami condition reduces to a single binding constraint:

> `HA_Close_0 ∈ (BODY_MIN_1, BODY_MAX_1)` — the latest HA close stays inside the
> prior body.

Consequences for the variant taxonomy (`/BARCFG`):

- HA harami is **not** a symmetric two-body comparison; it is "a small, reversing
  HA close contained within the prior body."
- The latest-bar colour is a *deterministic function* of where `HA_Close_0` lands
  relative to the prior-body centre: `HA_Close_0 ∈ (centre, BODY_MAX_1)` ⇒ bullish
  `HA_0`; `HA_Close_0 ∈ (BODY_MIN_1, centre)` ⇒ bearish `HA_0`.
- All four `{HA_1 dir} × {HA_0 dir}` variants are geometrically reachable, but
  their frequencies are **inherited** from the conditional distribution of
  `HA_Close_0` (= real-bar HLC4) given trend context — they are not free and not
  assumed uniform. `/BARCFG` coverage is measured at EXP-048 readiness, not
  assumed.

### Trend Substrate — ATR-Based ZigZag (real bars)

Computed on traditional (non-HA) bars. A trend-direction and move-boundary
substrate with no harami dependency.

- ATR estimator: **Wilder**, `atr_period = 14`. Warmup: no pivot/threshold defined
  until ATR is defined (≥ `atr_period` completed bars); pre-warmup bars carry no
  trend state.
- `ATR_MULT = 1.0`.
- Seeding (first defined bar): bullish bar (`Close > Open`) → trend Bullish, pivot
  = `High`; bearish bar → trend Bearish, pivot = `Low`.
- Tracking: maintain `pivot ∓ ATR_MULT × ATR` (`−` in bullish trends, `+` in
  bearish), updated every confirmed bar. A **trend-change confirmation** occurs at
  the first completed bar that closes beyond that level adversely to the current
  trend; the cycle then alternates. Moves are always alternating in direction.

**Causality discipline (binding).** A ZigZag pivot is confirmed only
*retroactively* (once price travels `ATR_MULT × ATR` away), so the pivot location
is future information relative to the bars between it and the prior confirmed pivot.

- Pivots may be used **only** for (a) reversal thresholds measured from a
  *confirmed, already-known prior* move, and (b) pivot-to-pivot grouping of
  *completed* moves for volume profiles.
- Signal detection, "end of trend" judgments, and entry/confirmation logic use
  **only data available at that timestamp**. Never reference an unconfirmed pivot.
- The operative point-in-time reference for evaluating a harami is the
  **trend-change confirmation bar**, never the retroactively-located pivot. The
  measurable question is: *did a harami fire before the trend-change confirmation,
  and how much earlier than the `ATR_MULT × ATR` giveback the ZigZag itself costs?*
  The harami's only edge is detecting the turn earlier than that giveback.

### Strong-Move / End-of-Trend Filter

**First-branch default: OFF (base harami).** Filters are registered variants,
varied one-at-a-time against predeclared defaults. Any statistical filter computes
over **only completed, confirmed prior moves** (inherits the ZigZag causality
rule); the HA-impulse filter is purely causal by construction.

- `/STRONG-STAT`: significance of move magnitude vs a rolling window of prior
  *confirmed* moves (percentile / MAD-multiple / ATR-multiple). Window length and
  threshold predeclared.
- `/STRONG-HA`: a run of `X` consecutive HA bars with large real bodies and no
  opposing wick (no lower wick for bullish, no upper wick for bearish). `X`
  predeclared.

Application (when on): exclude moves below threshold; and exclude signals that
occur before significance is confirmed, or after a retracement pulls them back
within the threshold range.

### Reversal — 3-Barrier Capture Geometry (first-class primitive)

The event the family predicts. `LOOKBACK` is the count of historical *confirmed*
moves used as the reference set. `LOOKBACK = 1` (default) uses the immediately
preceding move as an absolute price reference; `LOOKBACK > 1` yields magnitude
estimates only (no absolute target levels). All barriers are frozen at the
confirmation bar and evaluated only on **real prices** (never HA prices).

First-branch (benchmark) models:

- **Favourable target:** retrace `X%` of the immediately preceding confirmed move
  after signal confirmation. First-branch default `X` is a **D0/G0 item to ratify**
  (proposed 50%, chosen for measurable capture-rate at readiness, not 100%).
- **Adverse target:** 1:1 risk-to-reward (distance equal to the favourable
  target).
- **Third barrier:** per-cell **adaptive** time cap
  `N = max(6, round(1.5 × median duration of trailing 20 confirmed moves))` bars,
  derived structurally from each cell's characteristic move tempo — not a
  hand-set per-domain constant. Governance knobs `(k=1.5, window=20, floor=6,
  statistic=median)` frozen at G0; k-sensitivity is `/THIRD-TIME`. Warmup: < 5
  confirmed moves → insufficient context, excluded with disclosure.
  `/THIRD-EVENT` (opposing-signal) is the registered structural alternative.

Registered alternative barrier models (variants, see below): volume-profile and
statistical-magnitude favourable targets; previous-move-extreme and no-adverse
adverse targets; event-based (opposing-signal) third barrier.

## Hypotheses and Experiment Sequence

Registry HYP numbering is local to this family. EXP-IDs are assigned in the Phase
014 `design.md`; the chain begins at **EXP-048**. Gate definitions and outcome
criteria live in the `design.md`.

| HYP | Question | EXP | Gate | Status |
| --- | --- | --- | --- | --- |
| HYP-001 | Can the ZigZag substrate **and** the HA harami detector each be computed deterministically, look-ahead-safe, and with adequate per-cell coverage across all 102 cells? `/BARCFG` coverage measured, not assumed. | EXP-048 | Required before any characterization. | **READINESS_DELIVERED** — 86/102 READY, 3 COVERAGE_EXCLUDED. |
| HYP-002 | Can the 3-barrier capture geometry be computed deterministically and **causally** (thresholds only from confirmed prior moves), **and** what is the gross favourable-before-adverse capture rate per cell under predeclared default barriers? | EXP-049 | First-class capture-geometry read; required before barrier-model comparison. | **CAPTURE_READINESS_DELIVERED** — 99/99 barrier-constructible, G1 0/99 VIABLE (r~0.50 null). |
| HYP-003 | Where in a ZigZag move do harami signals occur (near exhaustion vs early/mid), and is "near exhaustion" more frequent than predeclared baselines (random timestamps, alternative trend definitions)? | EXP-050 | Characterization; informs combined-event registration. | **CONTEXT_CHARACTERISATION_DELIVERED** — 0/99 CLUSTERED, Δ uniformly −0.12 to −0.18. |
| HYP-004 | Do the strong-move filters (`/STRONG-STAT`, `/STRONG-HA`) identify materially different move populations, per the predeclared mechanical threshold, consistently across cells? | EXP-051 | Characterization. | **STRONG_FILTER_CHARACTERISATION_DELIVERED** — 99/99 MATERIAL, both filters P11-clear, 17/17 instruments. |
| HYP-005 | Direct signal vs signal+confirmation (`/CONFIRM`): descriptive frequency, timing, and subsequent outcome distribution of each. | EXP-052 | Characterization. | **CONFIRM_CHARACTERISATION_DELIVERED** — 99/99 negative shift, paired Δ median −0.62 ATR, confirm arm universally worse. |
| HYP-006 | `/STRONG`-conditioned HA harami, anchored at the harami, benchmark 3-barrier geometry: does the live conditioned signal produce positive gross per-event median expectancy (P14) that clears P11 and exceeds matched controls? | EXP-053 | Lead conditioning read; feeds 014-B G2. | **CHARACTERISED — EVIDENCE_FOR** — 7 viable cells over 6 instruments, 6 over 5 beat both baselines, 0 defects. |
| HYP-007 | Path-ordered intrabar fills (P15) vs the worst-case tie-break: does the benchmark capture readout change materially vs EXP-049? | EXP-054 | Fill-model method validation; quantifies P15 effect; adopted as 014-B fill standard. | **FILL_MODEL_CHARACTERISED (IMMATERIAL)** — median Δr 0.010, 0/99 VIABLE, 0 TIE_BREAK_SENSITIVE. |

Phase 014-B (conditioned-signal efficacy, capture-geometry comparison, and combined-event
characterization) registers **HYP-006–HYP-013** against **EXP-053–EXP-060** — the conditioned
efficacy read (HYP-006, harami-anchored, `/STRONG`-filtered), the intrabar fill-model
correction (HYP-007), the long-horizon availability diagnostic (HYP-008), the favourable
(HYP-009), adverse (HYP-010), and third-barrier (HYP-011) geometry comparisons, the
position-management exits `/EXIT-PARTIAL` and `/EXIT-TRAIL-STRUCT` (HYP-012), and the combined
event system (HYP-013). All gross, 0 slots, 0 TEST reads, expectancy endpoint (P14), no
intermediate gates. Full specification: the Phase 014-B design + D0 addendum and the Phase
014-B batch in `multiplicity-registry.md`. G0-B operator ratification precedes any
result-producing code.

**HYP-012 completed (EXP-059, 2026-06-16):** `/EXIT-PARTIAL` EVIDENCE_FOR — 4 PARTIAL arms
clear P11 (V2A strongest: 53 wins over benchmark, all 17 instruments). `/EXIT-TRAIL-STRUCT`
uniformly detrimental within the benchmark adaptive cap (0 viable cells across all trailing and
combined arms). 0 defects, 0 Critical, audit PASS. Registry-relevant result — multiplicity-registry
updated; passes to EXP-060 (combined event system). The uncapped trailing variant
(`/EXIT-TRAIL-UNCAPPED`) is separately registered for EXP-059B.

## Real-Price and Holdout Discipline

- HA prices are synthetic. The harami is *detected* on HA candles; every return,
  capture-rate, barrier-outcome, and P&L figure is computed on time-matched
  **real** prices (`RealOpen/High/Low/Close`). No metric is computed from HA prices.
- ZigZag, thresholds, and barriers are evaluated on real prices.
- `TickVolume` is broker tick count, a proxy for traded volume; volume-profile
  targets are lower priority and disclose the proxy limitation.
- The final 30% global holdout is excluded from all analysis; no new-universe row has
  been read under the HA-harami event definition; the global holdout seal carries forward.

## Exclusions

- No frozen end-to-end strategy screen in Phase 014. All work is gross
  (no costs); the frozen cost model enters only at a future tradability screen of a
  registered candidate branch, following the Phase 004 sequence.
- No parameter tuned or frozen against analysis-set outcomes (OAT against
  predeclared defaults only; no premature optimization).
- No qualitative claim ("materially different", "near exhaustion", meaningful
  baseline gap) without a predeclared mechanical threshold and a declared baseline.
- No combined event definition (harami + trend context + reversal targets) tested
  before each primitive is measured separately.
- No use of HA or Renko construction prices for any outcome metric.
- No use of the global holdout for any purpose.

## Registered Non-Baseline Branches

Each requires a dedicated scope and EXP-ID before measurement; negative, blocked,
and inconclusive outcomes remain in the file-drawer ledger.

- `CF-HA-HARAMI-001/BARCFG` — bar-direction configuration filtering/isolation.
- `CF-HA-HARAMI-001/CONFIRM` — signal+confirmation (threshold-then-confirm; stop-order entry model).
- `CF-HA-HARAMI-001/STRONG-STAT` — statistical strong-move filter.
- `CF-HA-HARAMI-001/STRONG-HA` — HA-impulse strong-move filter.
- `CF-HA-HARAMI-001/VPTARGET` — volume-profile favourable target (TickVolume proxy).
- `CF-HA-HARAMI-001/MAGTARGET` — statistical-magnitude favourable target (`LOOKBACK > 1`).
- `CF-HA-HARAMI-001/ADV-EXTREME` — previous-move-extreme adverse target (optional ≥1:1 R:R constraint).
- `CF-HA-HARAMI-001/ADV-NONE` — no adverse target.
- `CF-HA-HARAMI-001/THIRD-EVENT` — event-based third barrier (opposing signal / trend-reversal event).
- `CF-HA-HARAMI-001/THIRD-TIME` — adaptive time-cap sensitivity (the `k`/window/floor of the duration-derived fixed-holding barrier; predeclared grid, no post-result selection).
- `CF-HA-HARAMI-001/ATRMULT` — `ATR_MULT` sensitivity (predeclared grid, no post-result selection).
- `CF-HA-HARAMI-001/LOOKBACK` — reference-set size sensitivity (predeclared grid).
- `CF-HA-HARAMI-001/EXIT-PARTIAL` *(Phase 014-B, 2026-06-15)* — favourable-side scaled/partial
  exits: full entry weight split into ≤3 parts; Variant #1 {first-profitable-close, calculated
  target, reversal-event}, Variant #2 percentage-to-final-target splits. Take-profit only;
  adverse-target model unchanged. Spec: `014-B-D0-addendum.md` P17.
- `CF-HA-HARAMI-001/EXIT-TRAIL-STRUCT` *(Phase 014-B, 2026-06-15)* — adverse-side structure
  trailing stop on a smaller-`ATR_MULT` ZigZag (default `ATR_MULT_TRAIL = 0.5`): new pivot high
  → trail to recent low (long), new pivot low → trail to recent high (short); exit on fill.
  Spec: `014-B-D0-addendum.md` P18.
- `CF-HA-HARAMI-001/EXIT-TRAIL-UNCAPPED` *(Phase 014-B, 2026-06-16; characterized by EXP-059B 2026-06-16)* — the structure trailing
  stop run as a **standalone adverse-exit model**, not a barrier swap: **no benchmark time-cap
  backstop and no initial 1:1 stop**. The position carries no adverse exit until the first
  secondary-ZigZag (`ATR_MULT_TRAIL`) pivot confirms after entry, then ratchets monotonically
  (P18 rule unchanged); the forward window is unbounded to the TRAIN data edge and the only
  censoring is `DATA_CENSORED` past `train_end_ts`. Distinct from `/EXIT-TRAIL-STRUCT` (which
  retained the 3-barrier cap) and from `/THIRD-TIME` (cap sensitivity *within* the 3-barrier
  model). Registered after EXP-059 was found to have measured every trailing/combined arm under
  the benchmark adaptive cap. Spec: `014-B-EXP-059B-uncapped-trailing-addendum.md`.
  **EXP-059B result — EVIDENCE_AGAINST:** 0/2 binding arms clear P11 (TRAIL-PURE-UNCAPPED 0 viable, 0 WIN — uniformly negative; COMBINED-UNCAPPED-V2A 1 viable cell, 0 WIN). Cap-isolation confirms cap was not the constraint (0/96 divergent-positive pure TRAIL, 2/89 COMBINED). Closes the branch as a characterized negative; route to G2.

**Fill-model standard (Phase 014-B, P15):** outcome reads involving more than one barrier on a
bar resolve fills by intrabar path order (bullish `O→L→H→C`, bearish `O→H→L→C`), superseding the
EXP-049 worst-case tie-break. A documented approximation (1-minute base bars are not replayed
inside the domain bar); disclosed per result; effect quantified by EXP-054.

## Implementation Path

1. Python characterization builds the ZigZag substrate, the HA harami detector, and
   the 3-barrier capture machinery; produces per-cell readiness, coverage, and
   characterization tables (Phase 014-A/B). Reuse the EXP-047 `move_size.py`
   MFE/MAE/matched-control machinery where applicable.
2. Only a viable combined event definition surviving 014-B may be registered as a
   candidate branch for screening.
3. Candidate screening (event-level method calibration → EVAL_SUPPORTED →
   tradability → holdout) follows the established pipeline and uses the cTrader
   strategy-host branch once the work reaches suite validation.
