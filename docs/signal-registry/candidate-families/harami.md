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
**014-B slate status (2026-06-17):** EXP-053 EVIDENCE_FOR; EXP-054 fill-model IMMATERIAL (P15 adopted); EXP-055 AVAILABILITY_GOOD; EXP-056 EVIDENCE_AGAINST (favourable geometry); EXP-057 EVIDENCE_FOR (`/ADV-NONE`); EXP-058 EVIDENCE_AGAINST (third barrier); EXP-059 EVIDENCE_FOR (`/EXIT-PARTIAL` V2A); EXP-059B EVIDENCE_AGAINST (`/EXIT-TRAIL-UNCAPPED`, closed); EXP-060 CHARACTERISED_NOT_VIABLE_ELIGIBLE (combined system; champion 0/99 wins). **EXP-060B (HYP-013b) SUBSTRATE_LEAD_FOUND (2026-06-17, audit PASS)** — the conditioned harami expresses a **real median edge on the MA(20,50) substrate** it does **not** on ZigZag (M3 beats its own-substrate matched-random in 85/99 cells; reverses ZigZag's 3/99), so MA dominance is **partly a real signal effect, not solely a geometry/drift artifact** → the single 014-B **G2 must not close CF-HA-HARAMI-001** without a scoped MA-substrate follow-up. **But the lead is median-only and narrow** (M3 gross mean ≈0/negative, mean-viable 14/99; ADV-NONE skew gap 1.20 ATR; 8/14 lead cells low-n 4h) — the binding obstacle is now the **skew/mean**, so the follow-up must target a bounded-downside geometry, not re-run V2A×ADV-NONE. 0 slots, 0 TEST reads throughout. See `multiplicity-registry.md` (Phase 014-B batch) and `checkpoints/.../014-B-EXP-060B-ma-substrate-dominance-addendum.md`.
**G2 adjudicated 2026-06-17 — NO_PROCEED_TO_SCREEN, family NOT CLOSED** (`checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G2-gate-review.md`; operator routing "Open MA-substrate follow-up"; Phase 014 retrospective written): no combined definition clears P11 vs the P13 two-baseline conjunction on the registered ZigZag substrate → `014-B CHARACTERISED_NOT_VIABLE on ZigZag as configured`; but EXP-060B's SUBSTRATE_LEAD_FOUND forbids a clean close, so the **family is carried OPEN** on the real MA-substrate median edge. **0 candidate slots, 0 TEST reads** spent in all of 014-B; holdouts sealed; ledger unchanged. **Status: `REGISTERED` / OPEN.** Routing: a scoped MA-substrate follow-up (new phase, own D0/G0) — bounded-downside adverse geometry (1:1, `/ADV-EXTREME-rr1`), **mean** as a co-primary endpoint, confronting the 8/14-low-n-4h lead concentration; candidate registration only at the follow-up's own PROCEED gate.

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

**HYP-013 completed (EXP-060, 2026-06-17) — CHARACTERISED_NOT_VIABLE_ELIGIBLE:** The combined event system (V2A×ADV-NONE champion A3) produces 0 champion_wins across 99 cells: 69/99 viable individually, 3 beat matched-random, **0 beat MA(20,50)**. MA-baseline dominance is a substrate property — ZigZag single-point entries cannot match multi-segment MA(20,50) trend holds. Both geometric levers (V2A, ADV-NONE) independently improve expectancy additively (interaction near zero). Full 014-B surface measured; feeds the single G2 desk adjudication. Audit PASS.

**HYP-017 (EXP-064) — CHARACTERISED (dual-object, 2026-06-18): EVIDENCE_AGAINST on both objects.** Favourable-target geometry on the MA(20,50) substrate (Phase 015 S1): 7 alternative variants (VP-POC, VP-NEAR, VP-FAR via `/VPTARGET`; MAG-0.5×5/1.0×5/0.5×20/1.0×20 via `/MAGTARGET`) vs the benchmark 50%-of-`M_sofar`. **Native — 0/7 compose at P11+P6**: VP variants beat benchmark geometrically (10–11 cells beats_bench) but fail RM attribution (VP improvement is substrate-driven, not harami-specific); MAG-0.5×20 beats RM at P11 (8 cells/7 instr, genuinely harami-specific) but beats benchmark in only 3 cells. **Hybrid — 0/7 compose**: max 3 wins (VP-FAR), well below quorum. 99/99 cells powered. P4 trimmed means negative for VP-FAR (−0.029 native, −0.060 hybrid). Consistent with EXP-056 (ZigZag substrate, 0/8). Favourable-target lever measured-negative on both substrates and both objects. Objects never pooled; family stays OPEN; feeds terminal G-015. Audit PASS (0C/0W/3I). 0 slots, 0 TEST reads.

**HYP-018 (EXP-065) — CHARACTERISED (dual-object, 2026-06-18): EVIDENCE_AGAINST (native) / INCONCLUSIVE (hybrid).** Third-barrier geometry on the MA(20,50) substrate (Phase 015 S2): 4 alternative variants (`/THIRD-TIME` floors 12/24/48, `/THIRD-EVENT` next-MA-segment-rd-confirm with 8× backstop) vs the benchmark floor-6 adaptive cap. **Native — 0/4 compose at P11**: all alt variants median-viable (8–9 cells) and beat RM (8–9 cells), but beats_bench maxes at 3 cells (T48: EURUSD-5m/EURUSD-4h/GBPJPY-5m; EVENT: GBPUSD-1h/GBPJPY-2h/US2000-4h) — none at P11 quorum. Replicates EXP-058 (ZigZag) finding on MA. **Hybrid — INCONCLUSIVE_POWER_LIMITED**: max 4 powered cells (< P11 quorum); question cannot be answered on TRAIN slice with 3202-class population. Censoring cost bounded (TIMECAP fraction ~0.12–0.34 across variants). `/THIRD-EVENT` event_bound_frac = 1.0 for all cells. Third-barrier lever closed on MA for Phase 015. Family stays OPEN; feeds terminal G-015. Audit PASS (0C/0W/2I). 0 slots, 0 TEST reads.

**HYP-021 (EXP-068) — CHARACTERISED (2026-06-18): PROCEED_TO_SCREEN-candidate (G-015 input; gate NOT adjudicated here, P9).** Native combined champion (Phase 015 S4/native; mirrors EXP-060) — assembles the per-layer native surface winners into three binding arms and tests them under the **G-015 conjunction** (per cell: median CI_low>0 AND raw-mean CI_low>0 AND beats-`RM-native` CI_low>0), composed at P11+P6. **Both predeclared champion arms compose:** `N-PARTIAL-V2A` (S3 winner; PARTIAL-V2A + 1:1 stop) — 9 cells/5 instr/7 non-4h, P4=PARTIAL_RECOVERY; `N-V2A×ADV-NONE` (EXP-060B champion geometry with partial scaling, never previously computed; no adverse stop, MA cap is the sole stop-out, adv_count=0) — 14 cells/9 instr/6 non-4h, P4=TAIL_DRIVEN (63/99). This is the **first Phase 015 native read where the mean co-primary composes** (EXP-066 S3 was median+RM only). The mean-positive, RM-beating edge is present even at the single-leg BENCH (6 non-4h FX cells), so it is not a partial-exit/ADV-NONE artifact; the robust non-4h core is ~5 FX cells (GBPUSD/NZDUSD/GBPJPY, also at BENCH). **Caveats for the gate:** mean breadth is narrow (mean-positive 11–14/99 vs median-viable 45–89); `N-V2A×ADV-NONE`'s composition is 4h-concentrated (8/14) and tail-driven → the bounded-downside `N-PARTIAL-V2A` is the cleaner candidate definition; the negative mean is **not structural** for either arm (Phase 015 mean-recoverability thesis supported, narrowly). Reconciliation 99/99 to EXP-061 M0/H0 + EXP-066 native PARTIAL-V2A at 1e-9; determinism/causality/invariants clean. Hybrid disclosed EVIDENCE_AGAINST across EXP-061–066, never pooled — the edge is matched-substrate-specific. Family stays **REGISTERED, OPEN**; candidate registration only at G-015 (no slot here). Audit PASS (0C/0W/3I). 0 slots, 0 TEST reads.

**HYP-020 (EXP-067) — DROPPED (`D0-amendment-002-drop-exp067.md`, 2026-06-18, operator direction).** The hybrid combined champion is not run: the hybrid object is EVIDENCE_AGAINST across the entire individual surface (L1 EXP-061 1 cell; S1 EXP-064 0/7; S3 EXP-066 0 arms) and INCONCLUSIVE at S2 (EXP-065), a combined champion can only assemble per-layer winners (hybrid has none that compose), and the levers are additive-not-synergistic (EXP-060) — so EXP-067 is near-certain CHARACTERISED_NOT_VIABLE and **gates nothing** (G-015 PROCEED requires ≥1 combined definition on **either** object; native EXP-068 already qualifies). The hybrid object is adjudicated at the single terminal **G-015** on the **disclosed surface reads** (EVIDENCE_AGAINST dominant) — a documented inference, not a dedicated measurement; reinstatable as its own scope if the gate judges the inference insufficient. Item retained in the ledger, never deleted or reused. **The Phase 015 experiment slate is COMPLETE → single terminal G-015 (operator-adjudicated, both objects judged individually).** 0 slots, 0 TEST reads.

**HYP-014 (EXP-061) — CHARACTERISED (dual-object re-run COMPLETE 2026-06-17 under `D0-amendment-001-dual-parallel-substrate.md`; supersedes the prior single-object result in place).** The benchmark 3-barrier geometry (50%×1:1×adaptive cap) on the MA(20,50) substrate, measured **per conditioning object, individually (never pooled):**
- **Native object `M0` (MA-segment `/STRONG-STAT`, 8360-class) — EVIDENCE_FOR.** Signal-attributable median edge in **8 cells across 6 instruments, all outside 4h** (EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m); P11+P6 compose, not fragile; P12 reconciles to EXP-060B 99/99 @1e-9. **This confirms the prior EXP-061 EVIDENCE_FOR, now correctly attributed to the native object** (the prior `M0` arm had been mislabelled "hybrid").
- **Hybrid object `H0` (ZigZag `/STRONG-STAT` × MA geometry, 3202-class — the *genuinely-new* object, computed here for the first time) — EVIDENCE_AGAINST.** Generalises in only 1 cell (NZDUSD-5m, marginal); powered grid composes (99 cells) ⇒ genuine negative, not power-limited. Conditioning-mask reconciles exactly to EXP-053 via `Z0`.

**Headline:** the EXP-060B MA-substrate edge is a *matched-substrate* conditioning property — it generalises only when the `/STRONG-STAT` filter is computed on the same MA segment that defines the outcome geometry, not on the ZigZag move. **Phase verdict EVIDENCE_FOR (stronger object = native).** Family stays **REGISTERED, OPEN**; the surface runs regardless (P9). Disclosed `Z0` beats `RZ0` in 7 cells (indices/higher TFs). 0 candidate slots, 0 TEST reads; characterisation readout feeds the single terminal G-015 (no closure/registration here). Audit PASS (0C/0W/2I).

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
- `CF-HA-HARAMI-001/MA-SUBSTRATE` *(Phase 015, 2026-06-17; G0 PASS)* — **MA(20,50) crossover
  segmentation on real close** used as the conditioned harami's move/direction/favourable-target/
  adaptive-cap **substrate** (replacing ATR-ZigZag for outcome geometry); MA(20,50) **fixed/ratified,
  not swept** (MA-parameter sensitivity out of scope). In Phase 014 MA(20,50) was a P13 *baseline*;
  as a substrate it is a new countable item, registered after EXP-060B found the conditioned harami
  expresses a real median edge on it (85/99 vs matched-random, reversing ZigZag's 3/99). Two
  countable conditioning modes, **both parallel first-class substrates carrying the full surface,
  reported individually** *(elevated by `D0-amendment-001-dual-parallel-substrate.md`, 2026-06-17)*:
  **`hybrid`** (entry events = the EXP-053 ZigZag-`/STRONG-STAT` population, MA supplies only
  geometry — a **genuinely new** object, no outcome anchor) and **`native`** (`/STRONG-STAT`
  recomputed on confirmed MA segments — new entry population; **this is the object the EXP-060B/061
  `M`-arms actually measured**, reconciles to EXP-060B `M0/M3` 1e-9). The two objects are never
  pooled. Median binding (P14); **mean a diagnostic co-primary, not a disqualifier**. Spec:
  `checkpoints/2026-06-17-015-ma-substrate-conditioned-harami-full-surface/` (`design.md`,
  `D0-predeclarations.md`, `D0-amendment-001-dual-parallel-substrate.md`);
  `multiplicity-registry.md` Phase 015 batch (EXP-061–068; EXP-069 dropped).
  0 candidate slots, 0 TEST reads; candidate registration only at G-015 PROCEED.

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
