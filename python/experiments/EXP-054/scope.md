# Experiment: EXP-054 — Intrabar Fill-Model Correction (Benchmark Capture Re-Read vs EXP-049 Worst-Case Tie-Break)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-054 is a **measurement-method validation**
> (HYP-007), not a conditioned-efficacy read, so the four mandatory rules apply as follows — recorded
> explicitly so Stage 4 can check the honouring:
> - **(a) conditioning** and **(b) harami-anchor** are *intentionally inverted* here, by the 014-B design's
>   own instruction: EXP-054 "**re-reads the EXP-049 benchmark**" (`014-B-design.md` §5 slate, Lead 2). The
>   object under test is precisely the **unconditioned, ZigZag-trend-change-anchored** benchmark capture
>   read — `/STRONG` OFF, no harami — because the question is whether EXP-049's `r≈0.50` / 0-of-99 null
>   was partly a **tie-break artifact**. Applying conditioning or re-anchoring at the harami would change
>   the object and defeat the apples-to-apples comparison. The conditioned, harami-anchored signal is
>   EXP-053's object, not this one.
> - **(c) position-in-move is descriptive-only / never a live filter** — honoured: EXP-050's position
>   metric is not used at all.
> - **(d) expectancy endpoint (P14)** — honoured *as a disclosed secondary*: the **binding comparison
>   metric is first-hit `r`** (it must match EXP-049's readout to be a valid re-read), and **P14 median
>   per-event gross expectancy under both fill rules** is reported as a disclosed secondary so the result
>   is also legible on the family's binding endpoint. Lessons §8.6 ("match the metric to the mechanism")
>   is satisfied because the mechanism under test *is* the first-hit barrier resolution — there are no
>   partial exits or trailing stops in the benchmark.
> EXP-054 does **not** treat the EXP-049 `r≈0.50` null as evidence against the family; it audits how much
> of that null is the worst-case fill assumption versus a genuine symmetric-path property.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`) · `CF-HA-HARAMI-001/HYP-007` — EXP-054
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 382).
**Lead role:** Lead 2 of the 014-B slate — the dedicated fill-rule method validation the registry
deferred ("intrabar exit fills DEFERRED behind a dedicated fill-rule method validation", Phase-010
carried item).
**Governing design:** `014-B-design.md` (§5 Lead 2, §7, §8 SUBSTRATE/METHOD_DEFECT) +
`014-B-D0-addendum.md` (P15 fill model, P14 endpoint); inherits Phase 014 `design.md` §8 D0 (P1–P5
benchmark barriers) and the family spec `candidate-families/harami.md`.
**Source experiment re-read:** **EXP-049** (`CAPTURE_READINESS_DELIVERED`, audit PASS) — its scope,
`capture_barriers.py`, the 99-cell member grid, and the per-cell `r` / VIABLE readout are the fixed
comparison baseline.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/method-validation per the 014-B D0 addendum.
  A candidate branch is registered only at G2 PROCEED_TO_SCREEN — never inside 014-B.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis
  set), identical to EXP-049. No `test-read-ledger.md` tally applies; no entry is created. The nested
  analysis-set TEST stratum is not read; the final-30% **global holdout** is never loaded, inspected,
  or touched. No new-universe row is read under any *new* event definition (EXP-054 re-reads the exact
  EXP-049 ZigZag-confirmation benchmark, which already touched new-universe TRAIN rows in EXP-049; no
  new stratum is opened).
- All work is **gross** (no costs). All barriers, fills, and outcome metrics on **real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC). No HA price enters any metric (the harami detector is
  not used in EXP-054 at all).

---

## Hypothesis

**Method-validation hypothesis (HYP-007).** Replacing EXP-049's blanket worst-case same-bar tie-break
(every same-bar fav∧adv double-touch → ADVERSE) with the **P15 path-ordered intrabar fill model**
(bullish bar `Close ≥ Open`: `Open → Low → High → Close`; bearish bar `Close < Open`:
`Open → High → Low → Close`; first level reached along that path fills) on the **identical** EXP-049
benchmark events, barriers, cells, and TRAIN stratum does **not materially change** the benchmark
capture readout — i.e. the EXP-049 `r≈0.50` / 0-of-99-VIABLE null is a property of symmetric 1:1
barriers on the unconditioned substrate, **not** an artifact of the worst-case fill assumption.

**Falsifiable (the METHOD_DEFECT branch).** If, under P15, the benchmark G1 capture read **flips
materially** — meeting P11 (≥5 VIABLE cells over ≥3 instruments) where EXP-049 had 0/99 — then the
EXP-049 benchmark null was (at least partly) a tie-break artifact, and the benchmark must be
re-baselined on P15 fills before the 014-B G2 adjudication (`014-B-design.md` §8
SUBSTRATE/METHOD_DEFECT). Either outcome is a valid method result; neither closes the phase.

**Structural note (stated before data contact, not an assumption to test).** The tie-break touches
*only* same-bar fav∧adv double-touch events. EXP-049 FAV events are unambiguous single-touches and
remain FAV under P15; EXP-049 single-touch ADV events remain ADV; only EXP-049 ADV events that were
same-bar double-touches can be reassigned, and only to FAV. Therefore **`r_P15 ≥ r_EXP049` cell-by-cell
by construction** (monotone non-decreasing). The empirical questions are (i) the per-cell same-bar
double-touch fraction, (ii) the magnitude of `Δr = r_P15 − r_EXP049 ≥ 0`, and (iii) whether any cell or
the composition crosses the P12/P11 viability bars. This monotonicity is a built-in correctness check,
not a finding.

## Question

For the exact EXP-049 benchmark (every confirmed ZigZag trend-change as one capture event, P1–P5
benchmark barriers, both favourable geometries, 99-cell member grid, TRAIN-only), resolved under the
**P15 path-ordered fill model** instead of the worst-case tie-break:

a. What is the per-cell **same-bar double-touch fraction** among resolved events (the only events the
   fill rule can move), and how is it distributed across cells/instruments/domains?
b. What is the per-cell **`r_P15`**, its regime-clustered bootstrap CI, and `Δr = r_P15 − r_EXP049`
   (≥ 0 by construction) on the **primary G1 distance geometry**?
c. Does the benchmark **flip materially** under P15 — does G1 now meet **P11** (≥5 VIABLE cells over
   ≥3 instruments) where EXP-049 had 0/99? Which cells become **TIE_BREAK_SENSITIVE** (VIABLE-status
   flip OR `Δr ≥ 0.05`)?
d. Disclosed in parallel: the same re-read on the **secondary G2 retracement-level geometry**
   (degenerate events excluded as in EXP-049), and the **P14 median per-event gross ATR-normalised
   expectancy under both fill rules** (worst-case vs P15) per cell.

---

## Scope Boundaries

### Data Views

- **Real domain bars only.** 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`),
  aggregated to 5m, 15m, 30m, 1h, 2h, 4h clock-aligned domain bars via `xen.bar_aggregator.aggregate_ohlc`
  — **5m strict coverage** (`min_coverage=None`); **15m/30m/1h/2h/4h at `min_coverage=0.90`** — identical
  to EXP-048/EXP-049/VAL-004. **No Heiken Ashi, Line Break, or Renko views; the HA harami detector is
  NOT used** (EXP-054 re-reads the ZigZag-confirmation benchmark, which has no harami dependency).
- Every barrier, fill, capture outcome, `r`, and expectancy figure is computed on **real** domain OHLC.

### Capture Event & Barriers (FROZEN — identical to EXP-049; nothing re-tuned)

The event definition, entry anchor, reference move, and all P1–P5 benchmark barrier definitions are
**byte-for-byte the EXP-049 benchmark** and are re-used unchanged from `xen.capture_barriers`:

- **Event** = each confirmed ZigZag trend-change from `xen.zigzag.generate_zigzag(bars,
  atr_period=14, atr_mult=1.0)` (P1, frozen) on each cell's real domain bars (TRAIN-only).
- **Entry** `C` = the confirmation bar's real close (`ConfirmClose`) at `ConfirmIdx`. **(Not the
  harami — by design; see the mandatory-reading box.)**
- **Reference move (P5 `LOOKBACK=1`)** = the just-confirmed move; `M = |E − S|` (`M = 0` excluded);
  reversal direction `rd = −Direction`.
- **G1 (distance, PRIMARY / binding):** `fav_dist = 0.50·M`; `fav = C + rd·fav_dist`;
  `adv = C − rd·fav_dist` (1:1, P3).
- **G2 (retracement-level, SECONDARY / disclosed):** `level = E − Direction·0.50·M`;
  `fav_dist = rd·(level − C)`; degenerate iff `fav_dist ≤ 0` (excluded with record, as EXP-049);
  else `fav = level`, `adv = C − rd·fav_dist`.
- **Third barrier (P4):** per-cell adaptive cap `N = max(6, round(1.5 · median(duration_bars of the
  trailing 20 moves confirmed strictly before the event)))` real bars after `ConfirmIdx`; `< 5`
  trailing durations → warmup-excluded (no barrier). Re-used verbatim from `xen.capture_barriers.time_caps`.

**The ONLY thing that changes from EXP-049 is the same-bar resolution rule** — see below.

### Resolution Rule — the one experimental change (P15 path-ordered fills)

Forward window = real domain bars `i ∈ [ConfirmIdx+1, min(ConfirmIdx+N, train_last_idx)]` (strictly
after the confirmation bar; clipped to the TRAIN edge — never reads TEST or holdout), identical to
EXP-049. Per bar, fav/adv hits are tested with real `High_i`/`Low_i` exactly as in EXP-049. The change
is **only** how a bar that registers **both** a fav-hit and an adv-hit is resolved:

- **EXP-049 (baseline, reproduced for reconciliation):** same-bar double-touch → **ADVERSE**
  (blanket worst case).
- **EXP-054 (P15, the experimental rule):** resolve the same-bar double-touch by **intrabar path
  order**, using the bar's real `Open` and `Close` to choose the path:
  - **bullish bar** (`Close ≥ Open`): path `Open → Low → High → Close` — the **Low side** is reached
    before the **High side**;
  - **bearish bar** (`Close < Open`): path `Open → High → Low → Close` — the **High side** is reached
    before the **Low side**.
  The first of {fav level, adv level} encountered along that path fills first and resolves the event.
  Single-touch bars (only fav, or only adv) are unaffected and resolve exactly as in EXP-049.

Outcome classes are unchanged: `FAV`, `ADV`, `TIMECAP` (neither by `N`), `DATA_CENSORED` (window
truncated by the TRAIN edge before any hit). `TIMECAP`/`DATA_CENSORED` remain **unresolved** and out
of the `r` denominator.

The P15 assumption is a **documented approximation** of unobserved intrabar motion (1-minute base bars
are not replayed inside the domain bar). It is disclosed in every EXP-054 result; quantifying its
effect vs the worst-case baseline is the entire purpose of this experiment.

### Look-ahead / causality discipline (binding, unchanged from EXP-049)

- All barrier thresholds use only the just-confirmed move and strictly-prior confirmed moves
  (`ConfirmTime ≤` the event `ConfirmTime`). No unconfirmed pivot, no future bar.
- Forward resolution uses only bars strictly after `ConfirmIdx`, fenced to `CloseTime ≤ train_end_ts`.
  The P15 path order uses **only** the resolving bar's own `O/H/L/C` (all known at that bar's close) —
  it introduces **no** look-ahead (it does not peek at later bars; it disambiguates within the single
  bar that already triggered the double-touch).
- Ordering/alignment by `CloseTime`, never bar index across views.

### Instruments / cells (the 99-cell EXP-049 member grid)

The **exact EXP-049 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h) = **99 cells**. No cell is added or dropped.
DE30 carries the truncated-coverage disclosure (broker history ends 2026-01-16); counts derive from
its own realized timeline.

### Time range

**TRAIN stratum only** — identical to EXP-049: the first 70% of each instrument's first-70% analysis
slice, by the EXP-043/EXP-048/EXP-049 F01 file-order-prefix convention (`train_end_ts` = last
`CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). The nested
analysis-set **TEST stratum is not read**; the final-30% **global holdout** is never loaded, counted,
or touched (only Parquet metadata + the TRAIN prefix are read).

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Binding comparison endpoint (per cell, per geometry):** first-hit capture rate
  `r = FAV / (FAV + ADV)` over **resolved** events — the EXP-049 readout, recomputed under P15 fills.
  `resolved = FAV + ADV`; `TIMECAP`/`DATA_CENSORED` excluded from the denominator. Symmetric 1:1
  barriers ⇒ zero-edge null `r = 0.50`.
- **Δr** `= r_P15 − r_EXP049` per cell (≥ 0 by construction; a negative `Δr` on any cell is a
  **correctness failure** → SUBSTRATE/METHOD_DEFECT, since the fill rule can only reassign ADV→FAV).
- **Same-bar double-touch fraction** `dt_frac = (same-bar double-touch events) / resolved` per cell —
  the mechanism diagnostic (the only events the fill rule can move).
- **Power / zero-baseline (P12):** a cell with **`resolved < 30`** is **NOT_VIABLE-by-power** —
  non-reportable for routing, never an undefined or infinite ratio; `resolved = 0` ⇒
  NOT_VIABLE-by-power, not `0/0`.
- **VIABLE cell (P12, primary G1):** `r_P15 ≥ 0.55` **AND** regime-clustered bootstrap **CI_low > 0.50**
  **AND** `resolved ≥ 30` — the identical EXP-049/`capture_barriers.viable_status` rule, applied to the
  P15 fills.
- **Disclosed secondaries (never the binding comparison):**
  - **P14 median per-event gross ATR-normalised expectancy** under **both** fill rules (worst-case and
    P15), per cell. Per-event return `= rd·(exit_price − C)/ATR_entry`, `exit_price` = the realized
    fill level (target level for FAV/ADV; cap-bar real close for TIMECAP), `ATR_entry` = Wilder ATR(14)
    at the confirmation bar. Qualifying events = those with a built barrier resolving to FAV/ADV/TIMECAP
    (DATA_CENSORED + warmup excluded, disclosed as counts). Median over qualifying events; cell with
    < 30 qualifying events is NOT_VIABLE-by-power for the expectancy disclosure.
  - **G2 retracement-level** `r_P15`, `Δr`, and `dt_frac`, with degenerate (`fav_dist ≤ 0`) events
    excluded and disclosed (count + fraction per cell), exactly as EXP-049.
  - `fav_all = FAV / defined`, time-cap censoring fraction, data-truncation fraction, warmup-excluded
    counts — recomputed under P15 for comparability.
- No metric is expressed as a percentage improvement over a zero baseline; the null is the explicit
  `r = 0.50` symmetric-barrier reference and the EXP-049 per-cell `r` is the fixed comparison anchor.

## "Material change" criterion (predeclared, layered — operator-ratified 2026-06-15)

Adjudicated mechanically; this experiment **emits** the readout, it does not self-declare the §8
routing.

- **Family-material (the METHOD_DEFECT trigger, binding):** under P15 the **primary G1 benchmark meets
  P11** — **≥ 5 VIABLE cells over ≥ 3 instruments** — where EXP-049 reported **0/99 VIABLE**. If met,
  the EXP-049 benchmark null was materially a tie-break artifact → the benchmark is re-baselined on
  P15 fills before the 014-B G2 adjudication (`014-B-design.md` §8).
- **Per-cell `TIE_BREAK_SENSITIVE` (graded readout):** a cell is flagged iff its **VIABLE status flips**
  (NOT_VIABLE → VIABLE under P15) **OR** `Δr ≥ 0.05` (crosses a meaningful share of the 0.50→0.55
  viability gap). The count and identity of sensitive cells, and the `Δr`/`dt_frac` distributions, are
  reported regardless of the family-level verdict.
- **Method-confirmed (immaterial):** P11 is **not** met under P15 **and** no cell is
  TIE_BREAK_SENSITIVE (or only isolated cells are) — the EXP-049 benchmark null stands as a genuine
  symmetric-path property, not a fill artifact; P15 is adopted as the 014-B fill standard for the
  remaining slate with its (bounded) effect quantified.

## Success / Failure / Inconclusive Criteria

- **Experiment verdict — FILL_MODEL_CHARACTERISED (the deliverable):** the per-cell
  `dt_frac` / `r_P15` / `Δr` / VIABLE map (G1 binding), the G2 disclosed table, the dual-fill expectancy
  table, the TIE_BREAK_SENSITIVE cell list, and the family-material readout (P11 under P15) are
  produced — whatever the material/immaterial mix. Carries the **MATERIAL** vs **IMMATERIAL**
  classification per the predeclared criterion above.
- **SUBSTRATE/METHOD_DEFECT (halts pending a fix):** **non-determinism on any cell**; **or** the
  EXP-049 reconciliation gate fails (re-running the worst-case tie-break does not reproduce EXP-049's
  per-cell `r` exactly); **or** any cell shows `Δr < 0` (the fill rule reassigned a FAV to ADV or an ADV
  to single-touch FAV→ADV, which is impossible under correct P15 logic); **or** a causality/TRAIN-fence
  invariant is violated on ≥ 3 instruments.
- **Inconclusive (cell-level only):** a cell with `resolved < 30` (NOT_VIABLE-by-power); recorded,
  excluded from the P11 numerator, not a failure.
- The **routing outcome** (benchmark re-baseline vs P15-adopted-as-standard) is the **§8 G2-area desk
  adjudication** on this readout — never self-declared by the experiment.

## Reconciliation & Determinism Anchors (binding correctness gates)

1. **EXP-049 reconciliation (apples-to-apples proof):** EXP-054 computes outcomes under **both** the
   worst-case tie-break and P15 in the **same** pass on the **same** events/barriers. The worst-case
   leg must reproduce EXP-049's per-cell `r`, `FAV`, `ADV`, `resolved`, and outcome classes from
   `EXP-049/results/per_cell_capture.parquet` / `capture_rate_map.csv` **exactly** (to full float
   precision on `r`; exact integer match on counts). This proves the only delta is the fill rule.
2. **Determinism:** a full second pass (re-aggregate, re-run ZigZag, re-build barriers, re-resolve under
   both rules) compares **frame-identical** to the first pass.
3. **Monotonicity:** `r_P15 ≥ r_EXP049` and `FAV_P15 ≥ FAV_EXP049` on every cell and geometry; any
   violation is a METHOD_DEFECT.

## Complexity Budget

- **Max statistical tests: 1** — the regime-clustered moving-block bootstrap CI for `r` under P15
  (the frozen `xen.capture_barriers.block_bootstrap_ci` layer; one method, applied to G1 and G2). The
  expectancy disclosure reuses the same bootstrap machinery on the median (no new inferential method).
- **Max visualisations: 4** — (i) per-cell `Δr` heatmap (17×6); (ii) per-cell same-bar double-touch
  fraction `dt_frac` heatmap; (iii) VIABLE-status heatmap under P15 (VIABLE / r<0.55 / CI-spans-0.50 /
  NOT_VIABLE-by-power / excluded), with TIE_BREAK_SENSITIVE cells marked; (iv) paired EXP-049-vs-P15
  `r` scatter (one point per cell, diagonal reference). Secondary G2 and expectancy tables go to CSV.
- **Max new code modules: 0** — reuse `xen.zigzag`, `xen.bar_aggregator`, and `xen.capture_barriers`
  unchanged. The P15 path-ordered same-bar resolver is a small addition; per the family standard it
  belongs in `xen.capture_barriers` (it is the shared 014-B fill standard, P15). **If** a new public
  function is added to `capture_barriers.py` (e.g. `resolve_first_touch_pathorder`), it is an *additive*
  helper that does not alter the existing worst-case `resolve_first_touch` (which EXP-054 still calls
  for the reconciliation leg). This is not a new module; it extends the existing capture primitive with
  the registered P15 standard. No edits to `zigzag`/`bar_aggregator`/generators. The orchestration lives
  in `code/run_experiment.py` and mirrors the EXP-049 loader/replay pattern.

## Data Requirements

Per instrument: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each EXP-049-member domain
(5m strict; others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`; run
`xen.zigzag`; build barriers (both geometries) with `xen.capture_barriers`; resolve forward under
**both** the worst-case and P15 rules in one pass; collect per-cell records; second full pass for
determinism. Outputs (`results/`): `per_cell_fill_compare.parquet` (per cell: G1/G2 r_p15, r_exp049,
delta_r, dt_frac, FAV/ADV/resolved both rules, VIABLE both rules, tie_break_sensitive flag);
`fill_compare_map.csv` (G1 binding summary); `fill_compare_secondary.csv` (G2 + degenerate counts);
`expectancy_dual_fill.csv` (median expectancy both rules per cell); `reconciliation.csv` (worst-case
leg vs EXP-049 per-cell, max abs diff); `composition_readout.json` (P11 under P15 G1, material verdict,
TIE_BREAK_SENSITIVE list); `run_metadata.json` (seed, frozen constants, EXP-049 source hashes/paths).
Four bounded plots from the collected per-cell summaries (no reloads). `tqdm` over the instrument/cell
outer loop; per-cell bounded memory (do not retain all domain frames). Expected runtime: minutes
(99 cells × 2 fill rules × 2 determinism passes), comparable to EXP-049.

## Exclusions

- No HA harami detector, no `/STRONG` filters, no `/CONFIRM` entry model, no harami anchor, no
  position-in-move filter, no `/BARCFG` — EXP-054 re-reads the **unconditioned ZigZag-confirmation
  benchmark** by design (the comparison object is EXP-049).
- No alternative barrier models (`/VPTARGET`, `/MAGTARGET`, `/ADV-EXTREME`, `/ADV-NONE`,
  `/THIRD-EVENT`, `/THIRD-TIME`, `/ATRMULT`, `/LOOKBACK`) — those are EXP-056–058 with their own scopes.
  Only the frozen P1–P5 benchmark defaults and the two EXP-049 favourable geometries.
- No `/EXIT-PARTIAL` / `/EXIT-TRAIL-STRUCT` (EXP-059); the P15 fill model is validated here so those
  experiments can rely on it.
- No costs (gross throughout); no exit rule beyond the benchmark barriers; no net P&L screen.
- No returns from HA/Renko prices; every metric on real prices.
- No parameter tuned, selected, or frozen against any EXP-054 output; no cross-instrument or
  cross-domain pooling for the binding endpoint; no TEST or holdout contact; no candidate slot
  consumed; no TEST read; no gate adjudication (single G2 after the full 014-B slate).

## Suggested Direction (non-binding)

Mirror the EXP-049 orchestration (F01 loader, per-cell loop, determinism replay, bounded plots).
Add a single path-ordered same-bar resolver to `xen.capture_barriers` that, given the resolving bar's
`O/H/L/C`, the fav/adv targets, and `rd`, returns FAV vs ADV for a same-bar double-touch — and feed it
into a `resolve_first_touch` variant that calls it on the tie bar instead of the blanket-ADVERSE
branch. Resolve every event **twice** (worst-case + P15) in one window scan to keep the reconciliation
and the comparison exactly aligned. Recompute `r` from each fill set with the existing
`summarize_geometry` / `viable_status` / `block_bootstrap_ci`; compute median expectancy from the same
fills. Carry G2 and all censoring as disclosed columns. Emit the layered material readout; do not
adjudicate §8.
