# Experiment: EXP-053 — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion, Harami-Anchored)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. This experiment honours its rules:
> (a) it applies the family **conditioning** (`/STRONG`-filtered harami) that 014-A left untested as a
> conjunction; (b) it **anchors entry at the harami confirmation-bar close**, to capture the lead over
> the ZigZag `ATR_MULT × ATR` giveback — *not* at the ZigZag trend-change confirmation (the EXP-049
> anchor); (c) it treats **position-in-move (EXP-050) as descriptive-only — never a live filter**; the
> live "end-of-move" condition is the magnitude-percentile test `/STRONG-STAT`; (d) it uses the
> **gross per-event expectancy** endpoint (P14, median binding), not first-hit `r`, as the binding
> metric (`r` retained as a disclosed secondary). It does **not** treat the EXP-049 `r≈0.50` null or
> the EXP-050 front-loading as evidence against the family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`) · `CF-HA-HARAMI-001/HYP-006` — EXP-053
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md`).
**Lead role:** Lead 1 of the 014-B slate — the actual family hypothesis, run through an outcome read.
**Governing design:** `014-B-design.md` (§2/§3/§5/§7/§8) + `014-B-D0-addendum.md` (P14–P21);
inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec `candidate-families/harami.md`.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum. A
  candidate branch is registered only at G2 PROCEED_TO_SCREEN — never inside 014-B.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis
  set). No test-read-ledger tally applies; no entry is created. The final-30% global holdout is never
  loaded; no new-universe row is read under the HA-harami event definition (the conditioned event
  definition is new — its first contact with new-universe TRAIN rows is permitted; holdout/TEST sealed).
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` / domain-bar real OHLC), never HA prices.

---

## Hypothesis

A Heiken Ashi harami detected at the **probabilistic exhaustion of a strong impulsive move**
(`/STRONG-STAT`: in-progress move magnitude-so-far ≥ p75 of the trailing-20 confirmed-move
magnitudes), entered at the **harami confirmation-bar close** and traded as a **reversal of the
in-progress move** under the benchmark 3-barrier geometry (P2 50% favourable / P3 1:1 adverse / P4
adaptive time-cap) with **path-ordered intrabar fills (P15)**, produces **positive gross per-event
expectancy** (P14, median, ATR-normalised, real prices) that **clears P11** (≥5 cells over ≥3
instruments with CI_low > 0 and ≥30 events) and **exceeds matched-control baselines** (P13).

Falsifiable: if the conditioned, harami-anchored signal does **not** clear the P11 quorum on the
binding endpoint, or does not exceed matched controls, the family's central efficacy claim is
**not supported on benchmark geometry** (a valid characterization result that feeds G2 — never a
closure inside 014-B).

## Question

Does the live, causal, `/STRONG`-conditioned HA harami — anchored at the harami and faded against the
in-progress strong move under benchmark barriers and realistic intrabar fills — have a positive,
matched-control-beating gross per-event expectancy, per cell and composed across the grid?

---

## Scope Boundaries

- **Data Views**:
  - Real domain bars (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator`, `min_coverage=0.90`) for
    the ZigZag substrate, strong-move magnitudes, barriers, fills, ATR normalisation, and **all
    outcome metrics**.
  - Heiken Ashi candles (`xen.heiken_ashi_generator`, from the same domain bars) for **harami
    detection only**. No HA price enters any metric.
- **Event population (the conditioned signal)**:
  - HA harami (frozen detector, `xen.ha_harami.detect_ha_harami`, EXP-048) **AND**
  - the in-progress confirmed-ZigZag move's **magnitude-so-far** (last *confirmed* pivot → harami
    price, real prices) is **≥ p75** of the trailing-20 confirmed-move magnitudes (`/STRONG-STAT`,
    binding, P7), with **`/STRONG-HA`** (P8: run of X=3 large-body HA bars, no opposing wick) as a
    **disclosed secondary** filter arm.
  - **Trade direction** = reversal of the in-progress move (`rd = −trend_direction`). No `/BARCFG`
    isolation (a separate registered branch); all qualifying haramis count.
- **Entry anchor**: the **harami confirmation-bar close** (real domain-bar close at the harami
  timestamp), strictly *before* any ZigZag trend-change confirmation. This is the family's claimed
  lead point.
- **Barrier geometry (benchmark, frozen P2/P3/P4)** — measured from **magnitude-so-far** `M_sofar`
  (operator-ratified causal reference, 2026-06-15), `M_sofar = |harami_price − confirmed_start_pivot|`:
  - **Favourable target (G1 distance, primary)**: `fav_dist = 0.50 × M_sofar`;
    `fav = C + rd·fav_dist`. **G2 (retracement-level)** retained as a disclosed secondary geometry
    (degenerate cases excluded with record, as in EXP-049).
  - **Adverse target (P3)**: 1:1 — `adv = C − rd·fav_dist`.
  - **Third barrier (P4)**: per-cell adaptive time cap
    `N = max(6, round(1.5 × median(duration_bars of the trailing 20 moves confirmed strictly before
    the harami)))`, measured in completed real bars after the entry bar; `< 5` trailing durations →
    warmup-excluded (no barrier), never silently capped. Reuse `xen.capture_barriers.time_caps`
    semantics, re-anchored to the harami entry index.
- **Fill model (P15, method standard — replaces EXP-049 worst-case tie-break)**: when a single domain
  bar could touch more than one level, fills resolve in **path order** under the fixed intrabar-motion
  assumption — bullish bar (`Close ≥ Open`): `Open → Low → High → Close`; bearish bar (`Close < Open`):
  `Open → High → Low → Close`. First level reached along that path fills first. TIMECAP exits at the
  cap bar's real close. Documented approximation (1-minute base bars are not replayed inside the domain
  bar); disclosed in every result; its effect vs the worst-case baseline is quantified separately by
  EXP-054.
- **Parameters (all frozen D0; no tuning)**: ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1);
  `LOOKBACK = 1` (P5); favourable `X = 50%` (P2); adverse 1:1 (P3); time-cap `(k=1.5, window=20,
  floor=6, statistic=median)` (P4); `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` X=3 (P8);
  ATR-normalisation divisor = Wilder ATR(14) at the **harami confirmation bar** (P14); bootstrap
  `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14).
- **Instruments / cells**: the **99-cell EXP-049 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h}
  minus the 3 COVERAGE_EXCLUDED cells: US500-4h, JP225-2h, JP225-4h). Per-cell first, then P11
  composition (≥5 cells over ≥3 instruments). Full-grid breadth is required by P11 and by the
  "no blanket assumptions" principle; the 4-instrument core is insufficient for a composition claim.
- **Time range**: Full dataset, nested chronological split. **TRAIN only** = first 70% of the
  first-70% analysis set (per-cell, on `CloseTime`-sorted domain bars). TEST (last 30% of the analysis
  set) and the final-30% global holdout are **not** read.
- **Global holdout**: final 30% never loaded, inspected, or used.
- **Look-ahead / causality**: ZigZag pivots are future information until confirmed; the strong-move
  filter and the magnitude-so-far reference use only the **confirmed start pivot** (known) and the
  **current price** (known) at the harami timestamp. Barriers and the time cap use only moves confirmed
  strictly before the harami. No leg references a future bar. Strong-move thresholds computed over
  completed confirmed moves only.
- **Real-price outcome discipline**: harami detected on HA candles; expectancy, fills, barriers, ATR
  normalisation, `r`, win rate, and censoring all computed on real domain-bar OHLC. No HA price in any
  metric.
- **Exclusions**: no costs (gross only); no `/BARCFG`/`/CONFIRM` overlays; no favourable/adverse/third
  *alternative* geometries (those are EXP-056–058); no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059);
  no parameter tuning or post-result variant selection; no gate adjudication (single G2 after the full
  014-B slate — this experiment delivers a characterization readout only).

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The
binding endpoint is **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` × G1** arm; per-cell viable iff **CI_low > 0** (regime-clustered moving-block
bootstrap, one-sided 95%) **AND ≥ 30 qualifying events**.

- **EVIDENCE_FOR (conditioned efficacy supported)**: the `/STRONG-STAT` × G1 signal clears P11 (≥5
  viable cells over ≥3 instruments) **AND** the signal's per-cell median expectancy exceeds both P13
  baselines (matched-random and MA(20,50) segmentation) in the same composition (signal viable where
  baselines are not, or signal − baseline CI_low > 0 in the P11 quorum).
- **EVIDENCE_AGAINST (not supported on benchmark geometry)**: the signal fails the P11 quorum on the
  binding endpoint, **or** does not exceed matched controls (baselines viable/equal where the signal
  is). Recorded as a measured-negative characterization; routing deferred to G2 across the full slate.
- **INCONCLUSIVE (power-limited)**: conditioning drops too many cells below 30 events (fewer than the
  P11 quorum of cells reach ≥30 qualifying events) with no correctness failure — coverage insufficient
  to adjudicate. Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT**: any determinism, causality, or invariant failure → fix before reporting.

The experiment's deliverable label is **CONDITIONED_EFFICACY_DELIVERED** carrying the per-cell +
P11 readout, the EVIDENCE_* classification, both filter arms, both geometries, and all disclosed
secondaries. No phase closure or candidate registration occurs here.

## Complexity Budget

- **Max statistical tests: 4** — (1) regime-clustered moving-block bootstrap CI on the signal's median
  expectancy per cell; (2) same on the matched-random baseline; (3) same on the MA(20,50)-segmentation
  baseline; (4) the signal − baseline contrast CI. (Comparative experiment per the budget table.)
- **Max visualisations: 4** — e.g. per-cell median-expectancy forest/CI plot (signal vs baselines);
  expectancy distribution by arm; conditioned event-count / retained-fraction map; P11 composition
  summary heatmap.
- **Max new code modules: 1** — a path-ordered intrabar fill + realised-gross-return / expectancy
  resolver (P15 standard + P14 endpoint), reused across the 014-B slate (EXP-054–060). All ZigZag,
  harami, strong-move, time-cap, and bootstrap machinery is **reused** (`xen.zigzag`, `xen.ha_harami`,
  `xen.strong_move`, `xen.capture_barriers`); the orchestration lives in `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event — those
  with a built barrier (not warmup-excluded) whose outcome is `FAV`, `ADV`, or `TIMECAP`. Return =
  `rd · (exit_price − entry_close) / ATR_entry`, where `exit_price` is the P15 path-ordered fill price
  (target level for FAV/ADV; cap-bar real close for TIMECAP) and `ATR_entry` = Wilder ATR(14) at the
  harami entry bar. `DATA_CENSORED` (window truncated by the TRAIN edge before resolution) and warmup
  events are **excluded** from the median and disclosed as counts.
- **Endpoint denominator**: `E_cell = median` over the qualifying-event return population.
- **Zero-baseline / power**: a cell with **< 30 qualifying events** is **NOT_VIABLE-by-power**
  (non-reportable for the readout), never an undefined or infinite ratio. Conditioning will reduce
  counts vs the unconditioned base (EXP-051 retained fraction f ≈ 0.20–0.27); cells dropping below 30
  after conditioning are disclosed.
- **Disclosed secondaries (never binding)**: mean per-event return; first-hit `r = fav/(fav+adv)`
  (EXP-049 comparability); win rate (fraction of qualifying events with return > 0); the third-barrier
  censoring (TIMECAP) fraction; `/STRONG-HA` arm and the G2 geometry under the identical pipeline.

## Data Requirements

Per cell (instrument × domain): build domain bars (lazy Polars, TRAIN slice only); generate HA
candles; run the ZigZag substrate; detect haramis on HA candles aligned by `CloseTime` to real bars;
compute confirmed-move magnitudes-so-far at each harami timestamp; apply `/STRONG-STAT` (binding) and
`/STRONG-HA` (disclosed); build benchmark barriers from `M_sofar` re-anchored at the harami entry
index; resolve outcomes under the P15 path-ordered fill model; compute per-event ATR-normalised gross
returns; bootstrap the per-cell median; compute both P13 baselines through the identical metric;
compose by P11. `tqdm` over the 99-cell grid; bounded per-cell memory; fixed seed; deterministic.

### Standard Loading Pattern (TRAIN slice, per cell)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)      # first 70% = analysis set
train_cutoff = int(analysis_cutoff * 0.7)    # first 70% of analysis = TRAIN
train_bars = scan.slice(0, train_cutoff).collect()   # TEST + holdout never sliced
# domain aggregation (xen.bar_aggregator) applied to train_bars for 15m+/30m+/1h+/2h+/4h
```

## Suggested Direction

Compose the existing primitives rather than rebuilding: `xen.zigzag.generate_zigzag` →
confirmed moves; `xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami` → harami timestamps;
`xen.strong_move.strong_stat_decisions` / `annotate_ha_impulse` → the two filter arms;
`xen.capture_barriers.time_caps` (re-anchored) for P4. The single new module supplies the **P15
path-ordered fill resolver** and the **P14 realised-gross-return / median-expectancy** computation
(the EXP-049 `resolve_first_touch` worst-case tie-break is *not* reused for the binding read; `r` is
recomputed from the same fills for comparability). Reuse `xen.capture_barriers.block_bootstrap_ci`
machinery for the regime-clustered moving-block bootstrap on the median. Matched-random and MA(20,50)
baselines run through the same resolver with the conditioning removed / the segmentation swapped.
```
