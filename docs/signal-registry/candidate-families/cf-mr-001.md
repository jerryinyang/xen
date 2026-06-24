# CF-MR-001 — Mean-Reversion Entry (RSI-2), with Global Volatility-Regime Partition

**Status:** `ADMITTED (BINDING) — G-020 adjudicated 2026-06-23; first candidate slot consumed; lever = bare
RSI-2 fade (CORE), intraday` (EXP-089 `SCREEN_DELIVERED`, 2026-06-23; G-020 ADMITTED). First candidate family
opened **after** the Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price
routing (see §0). The family's first read was a **TRAIN-only availability screen** (EXP-089, `CF-MR-001/HYP-001`):
**0 counted TEST reads, holdout never touched.** **G-020 ADMITTED** (`S_fam=28 > S*=7`, axis perm-p≈0.0002,
FWER-robust, MC-stable) — **CF-MR-001 has now consumed its first candidate slot** and is the programme's first
non-random price entry to clear the family-selection availability gate. See
[`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).

> **AMENDED — `D0-amendment-001` (2026-06-23).** The first EXP-089 run was a deviation (audit C-1
> ATR-normalization confound + C-2 trend-length horizon). The leg-2 **beats-CORE conjunction and the
> regime-membership-shuffle null are RETIRED**; the endpoint is measured over a **causal MR-tempo cap** and the
> `/VOLREGIME` controls are **regime-matched**; all 6 sub-screens are single-test leg-1. The §"Global
> volatility filter" leg-2 description below is **superseded** by the amendment. **Realized outcome (§Outcome):
> the lever is the bare RSI-2 fade; the vol-regime partition is inert.**

**Governing phase (batch 1, CLOSED at G-020 ADMIT):** [`../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md)
· D0 [`D0-predeclarations.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/D0-predeclarations.md)
· gate [`G-020-gate-criteria.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-criteria.md)
· review [`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).
**Active phase (batch 2 — availability→tradability):** [`Phase 021 design`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md)
· [D0-predeclarations](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-predeclarations.md)
*(FROZEN, G0-RATIFIED 2026-06-23)* · [G-021 gate criteria](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-criteria.md)
— exit / capture geometry / cost for the bare RSI-2 fade, intraday-first (15m/1h); native intrabar reversion
targets **EXIT-RCT** (RSI₂→50 completion price) + **EXIT-ERT** (return-to-EMA10) vs conventional contrast;
planned EXP-090→093 (TRAIN-only until a one-shot TEST under the 2/stratum cap). The deferred
levers (regime, contrarian, 25/75, cross-cuts, tuning, expansion) are NOT in Phase 021 — each needs its own
dated `D0-amendment-*` + slot decision.
**Real-price / holdout discipline (binding):** all excursion/range metrics on real prices
(`RealOpen/High/Low/Close`); the final-30% global holdout is never read in screening or any future
readiness/characterization; counted TEST reads are spent only at a future binding confirmation under the
2-lifetime-per-stratum cap.

---

## 0. Provenance and the operator override (recorded, not implied)

Phase 019 (G-019, 2026-06-23) adjudicated the family-agnostic availability slate and routed the programme to
a **terminal branch**: *price-derived information — single-series magnitude and cross-sectional relational —
exhausted on this dataset; frontier = non-price data acquisition.* The single-series × **directional**
price-geometry cell is dead three families over (CF-AVWAP-001, CF-HA-HARAMI-001, CF-CAPGEO-001); the
magnitude cell (CF-VOLEXP-001) and the cross-sectional cell (CF-XSECT-001) closed at G-019.

**This family reopens the price-derived surface by explicit operator decision (2026-06-23).** The registry
rule is that a closed cell reopens only on a **genuinely new lever**, never a re-parameterization. The stated
new-lever basis is **two** items, and the family's honesty depends on holding to them:

1. **Mean-reversion entry mechanism (the strong leg).** Every prior family was **continuation / trend /
   pullback** (AVWAP pullback, HA-harami in trend, capgeo on those substrates). A **fade** entry — buy
   oversold, sell overbought — is the *opposite* signal generator and has **never been screened**. The
   "single-series directional is dead" verdict was established only on continuation entries.
2. **Strategy-agnostic volatility-regime partition as signal definition (a co-primary new lever).** A
   **strategy-agnostic** ATR regime filter — one *intrinsic to the market* rather than native to any strategy
   (unlike a strategy-fitted conditioner) — is applied as a *partition* of the entry population, so "RSI-MR in
   high-vol" is treated as a **distinct core signal** (cell = `asset+domain+regime`), not a post-hoc plugin.
   The bet is that making such an intrinsic filter a **cell-differentiating factor of the core signal itself**,
   rather than an add-on bolted onto a finished entry, is the ingredient prior families lacked. This is a
   genuinely new lever — not a re-try of an add-on filter — and the phase exists to disprove (or not) exactly
   that bet.

**Honest prior (binding on interpretation).** The programme-level null is **availability ≈ random** — the
hypothesis the screen tries to reject, not a prediction of failure. **Both** legs carry the override on their
own merits: leg 1 a genuinely new entry mechanism (fade), leg 2 a genuinely new *kind* of filter
(strategy-agnostic, intrinsic to the market, made part of the signal definition rather than bolted on). The
screen is therefore a **fully-committed falsification attempt at 0 reads / 0 slots**: if bare MR and its
vol-regime partitions come out ≈ random, that is a strong additional nail and the single-series-directional
cell is then dead under *both* continuation and mean-reversion; if any sub-screen admits, it is the
programme's first non-random price entry. The analysis and documentation read the realized numbers on their
own terms — no prior family's outcome is imported as an expectation that biases this verdict in either
direction.

---

## CF-MR-001 — definition (frozen at Phase 020 D0)

**2×2 cell:** single-series × directional, via a **mean-reversion (fade)** mechanism (distinct generator from
the dead continuation entries) + a **global volatility-regime partition**.

**Thesis (one falsifiable sentence):** *A short-period RSI mean-reversion entry — alone, or partitioned by a
strategy-agnostic ATR volatility regime that becomes part of the signal definition — produces
signal-conditional favourable excursion beyond a regime- and direction-matched random control.*

### Entry — RSI-2 mean reversion (frozen)

- **Indicator:** `RSI(2)`, Wilder smoothing, on domain `Close`. Parameters frozen: period **2**, extremes
  **10 / 90**. No tuning until the first batch shows promise (D0 §D6).
- **Long signal** at bar *t*: `RSI₂(t) < 10` (fade oversold; favourable = upward excursion).
- **Short signal** at bar *t*: `RSI₂(t) > 90` (fade overbought; favourable = downward excursion).
- **Availability endpoint (this family's screen):** signed favourable excursion `MFE_med` over the
  per-event adaptive cap (EXP-081 geometry), **ATR(14)-normalised, real OHLC**, vs the matched random
  control. The RSI exit (cross to the opposite extreme) is **not used** in the availability screen — it is a
  capture-geometry question deferred to a future post-admission phase (§exclusions).

### Global volatility filter — `/VOLREGIME` (frozen; distinct from the closed CF-VOLEXP-001)

- **Estimator:** `ATR(14)`, Wilder, on domain bars.
- **Regime:** causal trailing **rolling-50-domain-bar** percentile rank of the current `ATR(14)`; cuts at
  **33 / 66** → `LOW (<p33) / MED / HIGH (>p66)`. **Strategy-agnostic rule**; the percentile thresholds are
  computed **per (instrument, domain)** from **past bars only** (no future bar enters a regime label —
  streaming-safe). Window **50**, **33/66** scheme, **no tuning** in batch 1.
- **Applied as a PARTITION on the bare core only** (batch 1): each core entry is assigned to its regime. The
  regime sub-screen is tested by a **binding additive-edge conjunction** — a cell counts only if the regime
  subset **beats the standard direction-matched random control (`Δ̂_rand > 0`) AND beats the pooled CORE
  (`Δ̂_core > 0`)**, under a **regime-membership-shuffle-within-CORE** null. This operationalizes leg 2 *at
  full strength in batch 1, no deferral*: the regime must **add** favourable availability the unconditioned
  entry lacks, not merely inherit the core's. The control is the **same all-bars direction-matched
  `SUB-RANDOM`** as every other sub-screen — **no regime-matched control** (the endpoint is ATR(14)-normalised,
  so a regime's larger absolute moves are already divided out; the regime's additive value is what `Δ̂_core`
  isolates).
- **Distinct from CF-VOLEXP-001** (closed): that axis asked whether *volatility magnitude itself* predicts
  forward realized range (volatility as the signal); here volatility is a **signal-defining partition of a
  different entry** (RSI-MR), tested for the *additive* directional-favourable availability it contributes
  over the unconditioned core within each regime.

### Variant toggles (frozen definitions; batch-1 scope = pooled, NOT regime-cross-cut)

| Toggle | Long rule | Short rule | Batch-1 scope |
| --- | --- | --- | --- |
| **TREND** (`EMA(20)`) | `RSI₂<10 ∧ Close>EMA₂₀` | `RSI₂>90 ∧ Close<EMA₂₀` | pooled sub-screen `CORE+TREND` |
| **RSI-FILTER** (`RSI(5)`) | `RSI₂<10 ∧ RSI₅>50` | `RSI₂>90 ∧ RSI₅<50` | pooled sub-screen `CORE+FILTER` |

### Batch-1 sub-screens (the 6 reads → joint-max family statistic)

`CORE-pooled`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND-pooled`, `CORE+FILTER-pooled`.
Per-sub-screen `S` = `#cells beats-random` for `CORE`/variants (leg 1) and `#cells (beats-random ∧
beats-CORE)` for the three `/VOLREGIME` sub-screens (leg 2, binding). Within-family multiplicity over the 6
sub-screens is controlled by the **joint max** of the permuted-axis null
(`xen.availability_gate.combine_axis`) — the EXP-086/087 machinery, with a thin extension for the leg-2
conjunctive statistic and the regime-membership null (re-confirmed by the extended bite-check). No cross-axis
Holm (single family).

## Hypotheses (registered; EXP-IDs assigned at promotion)

- `CF-MR-001/HYP-001` — *Availability screen* (Phase 020, **EXP-089**): does the bare RSI-MR core, any of its
  three vol-regime partitions, or either pooled variant beat the multiplicity-adjusted admission gate
  (`S_fam > S*` ∧ axis perm_p ≤ 0.05)? Admit/exonerate, **0 slots, 0 reads**.
- `CF-MR-001/HYP-002+` — readiness / characterization / capture-geometry / net screen — **only if admitted**,
  at a future G0/D0.

## Kill / pass

- **EXONERATE** the family iff every batch-1 sub-screen `S` falls within the D2a noise band (no sub-screen
  beats the permuted-axis null) → the single-series-directional cell is dead under mean-reversion too; the
  programme returns to the G-019 terminal frontier (non-price data). 0 reads / 0 slots.
- **ADMIT** iff `S_fam > S*` ∧ axis perm_p ≤ 0.05; the winning sub-screen names the lever (bare MR vs a
  specific vol regime vs a variant). CF-MR-001 then consumes its first candidate slot and opens batch 2 at a
  future G0/D0.
- **INCONCLUSIVE** iff the permuted null cannot separate at the realized cell count (no power) — disclosed,
  neither admitted nor exonerated.

## Multiplicity caution (BINDING)

Six sub-screens × 46 cells manufactures cells; the **joint-max permuted-axis null** (D2b) is the binding
control — a lucky single cell or sub-screen must not admit the family. The batch-1 surface is held
deliberately small (one entry, one regime scheme, two variants, partition on the bare core only). All
**deferred** branches are registered now in the multiplicity ledger and consume no count until scoped:
**CONTRARIAN toggle** (flip direction on the RSI-filter axis), **25/75 regime scheme**, **regime × variant
cross-cuts**, **RSI/EMA/ATR/window parameter tuning**, and **instrument/domain/variant expansion**. Adding
any of them requires a dated `D0-amendment-*` and states whether it consumes a new slot.

## Exclusions / deferred

- **No exit / capture-geometry / sizing / cost / P&L work** until availability is admitted (the downstream
  stack is exonerated upstream — EXP-084 — and returns only after a first-order availability edge exists).
- The RSI mean-reversion exit, parameter tuning, the contrarian arm, the 25/75 scheme, and any regime×variant
  cross-cut are **registered-but-deferred** (multiplicity ledger), opened only on ADMIT at a future D0.
- A regime partition earns a leg-2 win only by the **binding beats-random ∧ beats-CORE conjunction** — it must
  *add* favourable availability over the unconditioned core (`Δ̂_core > 0`), never inherit it; the control is
  the standard all-bars direction-matched `SUB-RANDOM` (no regime-matched control — ATR-normalisation removes
  the regime scale).

## G-020 adjudication (BINDING) — 2026-06-23

**ADMITTED.** The predeclared D5 mechanical rule resolves in favour of admission on the realized EXP-089
statistics: `S_fam = 28 > S* = 7` **and** axis perm-p ≈ 0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm — single
family). The argmax sub-screen — and therefore the admitted **lever** — is **CORE, the bare RSI-2 fade**.
**CF-MR-001 consumes its first candidate slot.** The vol-regime partition is **inert** (low-priority follow-up);
the TREND/FILTER variants are dead-by-absence and not carried. On admit, the next scope opens the **bare RSI-2
fade, intraday (15m/1h), first** at a future G0/D0 — the availability→tradability (capture-geometry / exit /
cost) step. Admission consumes a **candidate slot, not a counted TEST read**; the holdout stays sealed and
`test-read-ledger.md` is unchanged (all 48 strata 0/2 open). Full adjudication:
[`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).

## Outcome — EXP-089 (`CF-MR-001/HYP-001`), amended run, 2026-06-23

**`SCREEN_DELIVERED` · provisional ADMITTED (NON-BINDING at screen time; made BINDING ADMITTED at G-020 above).**
Joint-max availability gate:
`S_fam = 28 > S* = 7`, axis perm-p ≈ 0.0002, ADMITTED across FWER {0.025, 0.05, 0.10}, MC-stable. Per sub-screen
`S`: **CORE 28**, CORE-VOL-LOW 22, CORE-VOL-MED 25, CORE-VOL-HIGH 20, CORE+TREND 0, CORE+FILTER 1.

- **Lever = the bare RSI-2 fade (CORE), not the regime partition.** The argmax sub-screen is CORE (z=17.3). The
  three `/VOLREGIME` sub-screens pass uniformly with flat per-cell `Δ̂_rand` (LOW 0.050 / MED 0.080 / HIGH 0.045
  ATR ≈ CORE's 0.060): conditioning on the volatility regime **adds nothing** the unconditioned entry lacks.
  **Leg 2 (the "filter-becomes-the-signal" bet) is empirically inert** on this evidence.
- **Variants are counter-productive:** TREND S=0, FILTER S=1 (trend/momentum agreement contradicts the fade).
- **Effect is intraday and short-lived:** CORE passes 15m 16/16, 1h 11/16, 4h 1/14 (all 16 instruments
  represented); effective ~3-bar horizon; favourable `MFE_med` ≈ 0.75 ATR (Δ̂ ≈ 0.06), measured conservatively.
- **Availability, not tradability** — no exit/cost, gross, TRAIN-only. The binding admit/exonerate is **G-020**.

This is the programme's first non-random price entry to (provisionally) clear the family-selection availability
gate after the Phase 019 terminal branch. On ADMIT, G-020 would open the **bare RSI-2 fade, intraday, first**;
the vol-regime lever is a low-priority follow-up given its inertness here. Artifacts:
[`../../../python/experiments/EXP-089/report.md`](../../../python/experiments/EXP-089/report.md).

## Outcome — EXP-090 (`CF-MR-001/HYP-002`, Phase 021 batch 2), 2026-06-24

**`READINESS_CALIBRATION_DELIVERED` · 20 MEMBER / 12 COVERAGE_EXCLUDED · 0 slots · 0 counted TEST reads · holdout
sealed · audit PASS · AMENDED `D0-amendment-002`.** The availability→tradability step's first experiment: the
bare-fade entry substrate, the new 1-minute intrabar exit-fill engine (`xen.intrabar_fill`), and the binding
mean net-expectancy referee are constructible, deterministic, causal, timestamp-aligned, holdout-fenced, and
**powered** on **20 of 32** cells (10 × 15m + 10 × 1h), which carry to EXP-091 with calibrated margins (RCT
0.0125 / ERT 0.025 ATR = the EXP-093 margins).

- **The 12 excluded cells all fail for the same power reason** — *no finite MDE on either native arm* (cannot
  bound a confirmation at their realized count). NOT an FPR, engine, or coverage failure: every cell is
  `IN_FLOOR`, fill-validity/timestamp/determinism are TRUE on every cell × arm, and the per-cell FPR is
  symmetric and controlled (native-arm median 0.048–0.051; every member's carried arm ≤ 0.050 under **both**
  nulls).
- **No edge is claimed or computed.** The real fade outcomes were never resolved
  (`real_fade_outcomes_resolved: false`) — EXP-091 is the first to read them. The calibration certifies the
  *estimator*, cost-free by translation-equivariance (a valid net margin).
- **Audit trail (3 runs; `D0-amendment-002`):** Run 1 HALTed on a 1-minute fill-engine bug (per-bar window
  over-assignment across dropped/session-gap windows + limit/stop gap-throughs → fills outside `[Low,High]`);
  Run 2 found the analysis-plan's Null B (block-rotated **path**) pathological — it matched entries to wrong-era
  prices, inflating ATR-normalised return variance 30–145× (mean exactly 0), wrongly excluding 14 cells on the
  binding mean. Both fixed and fully re-run: window anchored to each bar's own `(close − period, close]`,
  gap-throughs fill at the touching 1m **open**; Null B reverted to block-permuted **resolved returns** (the
  EXP-001/027/044 form `scope.md` originally specified). The disclosed median leg (D5, non-binding) was dropped
  for performance (binding mean bit-identical to `xen.ass`; runtime 8 h → 67 min).
- **Member-set note vs the intermediate broken-Null-B run (12 members):** 9 robust (member in both), 11
  newly-admitted (the rotation-artifact casualties), 3 boundary-noise dropouts (Null B FPR 0.051–0.057). The
  hard ≤ 0.05 gate (±0.014 Wilson noise at 1000 draws) flips marginal cells; the 9 robust cells are the safest
  EXP-091 evidence.

No countable exit item is screened or refuted here (that is EXP-091). Artifacts:
[`../../../python/experiments/EXP-090/report.md`](../../../python/experiments/EXP-090/report.md) · amendment
[`../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-002.md`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-002.md).

---

*All outcomes — admit, exonerate, inconclusive — are **retained** in this file and the Phase 020
multiplicity-registry batch, never deleted or reused. A refuted family is closed and not silently reopened by
re-parameterization.*
