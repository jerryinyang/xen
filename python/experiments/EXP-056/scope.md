# Experiment: EXP-056 — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-056 is the **favourable-target geometry**
> surface read (HYP-009, P14/P16). The four mandatory rules are honoured as follows, recorded so
> Stage 4 can check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA
>   harami** (the actual family signal, identical population to EXP-053/054/055), not the raw harami
>   or the unconditioned ZigZag substrate. `/STRONG-STAT` (P7, live magnitude-percentile) is binding;
>   `/STRONG-HA` (P8) is a disclosed secondary arm. Only the **favourable-target geometry** is varied
>   (OAT); the signal, anchor, adverse model, third barrier, and fills are held at benchmark.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, the
>   family's claimed lead point — *not* the ZigZag trend-change confirmation (the EXP-049 anchor).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. Reference moves used to build favourable targets are **confirmed, completed**
>   moves (known at entry); no unconfirmed pivot enters any target, filter, or barrier.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross
>   per-event expectancy** (P14, ATR-normalised, P15 fills), with first-hit `r` retained as a
>   disclosed secondary only.
> EXP-056 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence
> against the family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`) · `CF-HA-HARAMI-001/HYP-009` — EXP-056
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 384). Exercises the
registered branches `CF-HA-HARAMI-001/VPTARGET` and `CF-HA-HARAMI-001/MAGTARGET`.
**Surface role:** Surface read 1 of the 014-B post-lead slate — favourable-target geometry comparison.
**Governing design:** `014-B-design.md` (§2/§3/§5 surface, §7, §8) + `014-B-D0-addendum.md`
(P14/P15/P16/P20); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec
`candidate-families/harami.md` (Favourable-target variants `/VPTARGET`, `/MAGTARGET`).
**Reuses:** the EXP-053 conditioned-signal construction and P15/P14 resolver
(`xen.expectancy.live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`resolve_path_ordered`, `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`,
`median_ci`, `contrast_ci`); ZigZag (`xen.zigzag`), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

**Operator scope decisions (2026-06-16, recorded before any data contact):**
- **This is a predeclared favourable-target *sweep*, not a single comparison** ("be not dismayed by
  the large exploration plane"). All variants are predeclared here; **no post-result variant
  selection** — every variant is reported and composed by P11; final routing is the single 014-B G2.
- **`/VPTARGET` level types — sweep all three:** near value-area edge, POC, far value-area edge.
- **`/VPTARGET` reference move = the prior *completed* move (LOOKBACK=1), not the in-progress move.**
  Operator rationale (recorded): the in-progress move's volume profile is path-dependent, noisy with
  few bars, and is a moving target biased toward the fade's adverse side — exactly what a fade against
  that move should treat with suspicion. **POC of the prior completed move is the VP baseline** against
  which the other VP variants are compared. The in-progress-move POC is retained as a **disclosed
  secondary** so the path-dependence concern is shown empirically, not merely asserted.
- **`/MAGTARGET` — predeclared grid covering the range:** favourable distance =
  `frac × median(magnitudes of the trailing `W` confirmed moves)`, over the grid
  `frac ∈ {0.5, 1.0} × W ∈ {5, 20}` (4 variants).
- **Adverse target is independent of the favourable target except under the 1:1 model.** EXP-056 holds
  the **benchmark adverse model (P3 = 1:1)**, which — being 1:1 — sets the adverse distance equal to
  whatever favourable distance the variant produces. Geometry-specific adverse models (`/ADV-EXTREME`,
  `/ADV-NONE`) and the structure trailing stop are **out of scope** here (EXP-057 / EXP-059). The third
  barrier stays the benchmark adaptive time cap (P4). This is pure OAT on the favourable-target leg.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). The `/VPTARGET` and `/MAGTARGET` branches are
  registered but consume a slot only when a future scope activates one as a screening candidate —
  which, per P21, cannot happen before G2 PROCEED_TO_SCREEN.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis
  set), identical fence to EXP-049/053/054/055. No `test-read-ledger.md` tally applies; no entry is
  created. The nested analysis-set **TEST stratum is not read**; the final-30% **global holdout** is
  never loaded, inspected, or touched. The conditioned HA-harami event population already had its first
  new-universe TRAIN contact in EXP-053 (same definition); no new stratum is opened and the holdout
  seal carries forward unchanged.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded
against the in-progress strong move), **at least one alternative favourable-target geometry**
(`/VPTARGET` volume-profile levels of the prior completed move; `/MAGTARGET` trailing-magnitude
distances) produces **higher gross per-event median expectancy** (P14, ATR-normalised, P15 fills, real
prices) than the **benchmark 50%-of-`M_sofar` favourable target** (P2), on the binding `/STRONG-STAT`
arm, with the adverse target held at the benchmark 1:1 model and the third barrier at the benchmark
adaptive cap (OAT on favourable geometry).

Falsifiable: if **no** alternative favourable-target variant clears the P11 quorum (≥5 cells over ≥3
instruments with CI_low > 0 on its own expectancy) **and** beats the benchmark variant (variant −
benchmark contrast CI_low > 0 in the quorum), then favourable-target geometry is **not** a lever that
improves conditioned capture on benchmark adverse/third geometry (a valid characterization result that
feeds G2 — never a closure inside 014-B).

## Question

Does changing only the **favourable target** — from the benchmark 50%-of-in-progress-magnitude level
to a volume-profile level of the prior completed move (`/VPTARGET`: near VA edge / POC / far VA edge)
or a trailing-magnitude distance (`/MAGTARGET`: `{0.5,1.0} × median(trailing-{5,20})`) — improve the
conditioned HA-harami's gross per-event median expectancy vs the benchmark, per cell and composed
across the grid, and which variant (if any) wins?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053/054/055/VAL-004) for the ZigZag substrate,
  confirmed moves, strong-move magnitudes, the favourable-target construction (volume profile and
  trailing magnitudes), barriers, fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami
  detection only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector). **No HA price enters
  any metric.**
- **`TickVolume`** (domain-bar, summed from the constituent 1-minute bars by `xen.bar_aggregator`) is
  the only volume input to `/VPTARGET`. It is **broker tick count, a proxy for traded volume**; this
  proxy limitation is disclosed in every `/VPTARGET` result (family spec; registry note).

### Event population (the live conditioned signal — identical to EXP-053/054/055)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the
  in-progress confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last
  *confirmed* pivot → harami real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes
  (P7, binding). `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no opposing wick) is a **disclosed
  secondary** arm run through the identical pipeline.
- **Trade / reversal direction** `rd = −trend_direction = Direction_k` of the last confirmed move
  (`xen.expectancy.live_in_progress_state`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` — the **same
  functions EXP-053 used** — so the binding population is byte-identical to EXP-053's conditioned events
  (verified by population reconciliation).

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly
before any ZigZag trend-change confirmation. Identical to EXP-053/055.

### Favourable-target variants (predeclared sweep; OAT on the favourable leg only)

All variants below define a **favourable price level** `fav` in the reversal direction `rd` from `C`; the
favourable distance is `fav_dist = rd·(fav − C)`. The **adverse** target is the benchmark 1:1 model
`adv = C − rd·fav_dist` (operator decision — benchmark adverse is 1:1, so adverse distance = favourable
distance for every variant). The **third barrier** is the benchmark P4 adaptive time cap
(`xen.expectancy.adaptive_time_caps_by_epoch`). Fills are P15. **Validity rule (all variants):** a
variant event is *valid* iff `fav_dist > 0` (the target is on the reversal side of `C`) **and** the
target/profile context is defined; events with `fav_dist ≤ 0` or an undefined profile are
**excluded-with-record** (a disclosed degenerate count per cell, mirroring EXP-049 degenerate
exclusions), never silently clamped.

1. **Benchmark (reference variant, P2):** `fav_dist = 0.50 × M_sofar`; `fav = C + rd·0.50·M_sofar`.
   Reproduces the EXP-053 benchmark favourable target via `xen.expectancy.benchmark_barriers` — the
   anchor every alternative is contrasted against.

2. **`/VPTARGET` — volume profile of the prior completed move (LOOKBACK=1), binding reference.** Build a
   volume profile from the **domain bars constituting the immediately preceding *completed* confirmed
   move** `M_k` (the last confirmed move, known at entry; its bars are
   `[confirm_idx[k−1]+1 … confirm_idx[k]]`). Each constituent bar's `TickVolume` is distributed
   **uniformly across its `[Low, High]` range** into fixed-width price bins (bin width `= 0.10 × ATR_entry`,
   predeclared; ≥1 bin). From this profile:
   - **POC** = centre of the maximum-volume bin (**VP baseline variant**).
   - **Value area = 70%** of total profile volume, the contiguous bin run grown outward from the POC;
     its low boundary `VAL` and high boundary `VAH`.
   - **near VA edge** = the VA boundary with the **smaller** valid `fav_dist`; **far VA edge** = the VA
     boundary with the **larger** valid `fav_dist` (among `{VAL, VAH}` with `rd·(level − C) > 0`).
   - **Insufficient-profile rule:** `M_k` with **< 3 domain bars** → no valid profile → event
     excluded-with-record (disclosed count); a level on the wrong side of `C` → that *level's* variant
     event excluded-with-record.
   - Three binding `/VPTARGET` variants: **VP-POC** (baseline), **VP-near-VA**, **VP-far-VA**.

3. **`/VPTARGET` — in-progress-move POC (disclosed secondary only).** Identical construction but the
   profile is built from the **in-progress move's** domain bars `[start_idx+1 … entry_idx]`. Retained to
   **empirically expose** the operator's path-dependence concern; **never binding**, reported as a
   disclosed secondary.

4. **`/MAGTARGET` — trailing-magnitude distance (LOOKBACK>1; predeclared grid).**
   `fav_dist = frac × median(magnitudes of the trailing W confirmed moves confirmed strictly before the
   harami)`, `fav = C + rd·fav_dist`, over the grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}` (4 variants:
   MAG-0.5×5, MAG-1.0×5, MAG-0.5×20, MAG-1.0×20). Magnitude estimate only — no absolute price level
   (family spec). Warmup: **fewer than `W` confirmed moves** before the harami → event excluded-with-record
   for that variant (disclosed). `fav_dist > 0` always holds (magnitudes are positive), so the validity
   rule excludes nothing here beyond warmup.

**Total predeclared favourable-target variants:** 1 benchmark + 3 binding `/VPTARGET` + 4 `/MAGTARGET`
= **8 binding variants**; plus 1 disclosed-secondary in-progress VP-POC. Each variant runs on the
binding `/STRONG-STAT` arm (binding) and the `/STRONG-HA` arm (disclosed), with both P13 baselines.

### Adverse target, third barrier, fills (benchmark; held fixed)

- **Adverse (P3, benchmark 1:1):** `adv = C − rd·fav_dist` — distance equals the variant's favourable
  distance (operator decision; benchmark adverse model is 1:1).
- **Third barrier (P4, benchmark adaptive cap):** per-cell `N = max(6, round(1.5 × median(duration_bars
  of the trailing 20 moves confirmed strictly before the harami)))` real bars after entry;
  `< 5` trailing durations → warmup-excluded (no barrier). Reuse
  `xen.expectancy.adaptive_time_caps_by_epoch`.
- **Fill model (P15, method standard):** when a single domain bar could touch more than one level, fills
  resolve in path order — bullish bar (`Close ≥ Open`): `Open → Low → High → Close`; bearish
  (`Close < Open`): `Open → High → Low → Close`. TIMECAP exits at the cap bar's real close. Reuse
  `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed in every result.

### Parameters (all frozen D0; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3`
(P8); benchmark favourable `X = 50%` of `M_sofar` (P2); adverse 1:1 (P3); time-cap `(k=1.5, window=20,
floor=6, statistic=median)` (P4); ATR-normalisation divisor = Wilder ATR(14) at the harami entry bar
(P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14). **New predeclared
favourable-target parameters (this scope):** VP reference = prior completed move (LOOKBACK=1); VP bin
width `= 0.10 × ATR_entry`; VP value area `= 70%`; VP insufficient-profile floor `= 3` domain bars;
`/MAGTARGET` grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}`, statistic = median. None is tuned against outcomes;
sensitivity is not swept beyond the predeclared grid.

### Instruments / cells

The **99-cell EXP-049/053/054/055 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition (≥5
cells over ≥3 instruments) for any "winning variant" claim. Full-grid breadth required by P11 and the
"no blanket assumptions" principle. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per
cell, F01 file-order-prefix convention identical to EXP-049/053/054/055:
`train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows).
TEST (last 30% of the analysis set) and the final-30% **global holdout** are **not** read.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) run through the **identical favourable-target + barrier + resolver pipeline** for each
  variant — does a given favourable geometry beat random entries under the same geometry?
- **MA(20,50) segmentation** (alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  expectancy under MA-segmented moves for each variant, disclosed.
- Baselines are disclosed secondaries; the binding readout is each variant's own expectancy and the
  variant − benchmark contrast.

### Look-ahead / causality discipline (binding)

- ZigZag pivots are future information until confirmed. The signal (harami + `/STRONG-STAT`), `M_sofar`,
  and every favourable target use **only confirmed, completed prior moves and the entry bar's own real
  close** — never an unconfirmed pivot or any future bar. The VP reference move `M_k` is confirmed at
  entry; its bars are all `CloseTime ≤ C`'s bar. `/MAGTARGET` magnitudes are from moves confirmed
  strictly before the harami. Barriers/time cap use only moves confirmed strictly before the harami.
- Excursion scans read only bars `[entry_idx+1, cap]`, fenced `CloseTime ≤ train_end_ts`; an event whose
  window is truncated by the TRAIN edge before resolution is `DATA_CENSORED` (excluded, disclosed),
  never measured against truncated data.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, the volume profile (real-bar prices + `TickVolume`), trailing
magnitudes, ATR normalisation, fav/adv levels, fills, expectancy, `r`, win rate, and censoring all on
real domain-bar OHLC. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Favourable-target geometry only.** No `/ADV-EXTREME`/`/ADV-NONE` (EXP-057), no `/THIRD-EVENT`/
  `/THIRD-TIME` (EXP-058), no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059), no combined system
  (EXP-060). No `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*.
- No parameter tuning; **no post-result variant selection** (all predeclared variants reported); no gate
  adjudication (single G2 after the full 014-B slate — EXP-056 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The
binding endpoint is **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap,
one-sided 95%) **AND ≥ 30 qualifying events**.

- **EVIDENCE_FOR (a favourable-target lever helps):** ≥1 alternative variant **(a)** clears P11 on its
  own median expectancy **AND (b)** beats the benchmark variant on the **variant − benchmark contrast**
  (contrast CI_low > 0) within the P11 quorum (matched cells). The winning variant(s) and their margin
  over benchmark are the deliverable; no candidate registration (G2 only).
- **EVIDENCE_AGAINST (favourable geometry is not a lever):** no alternative variant both clears P11 and
  beats the benchmark contrast. Recorded as a measured-negative characterization; routing deferred to
  G2 across the full slate.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on
  the variants of interest (validity/warmup exclusions deplete counts), no correctness failure.
  Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.

The deliverable label is **FAVOURABLE_TARGET_CHARACTERISED** carrying the per-cell + P11 readout for
every variant, the EVIDENCE_* classification, the benchmark contrast per variant, both filter arms, both
P13 baselines, and all disclosed secondaries (in-progress VP-POC, `r`, win rate, censoring/exclusion
counts, `/VPTARGET` `TickVolume`-proxy disclosure). No phase closure or candidate registration here.

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a
  variant's median expectancy per cell; (2) same on each P13 baseline; (3) variant − benchmark contrast
  CI; (4) variant − baseline contrast CI. These four methods are applied across the predeclared
  favourable-target variant grid (a parameterised sweep over one experiment, not new methods per
  variant) — consistent with the 014-B surface design and the `/THIRD-TIME`-style predeclared grids.
- **Max visualisations: 5** — (i) per-variant median-expectancy forest/CI per cell vs benchmark;
  (ii) variant − benchmark contrast heatmap (variants × cells, or a per-variant composition summary);
  (iii) expectancy distribution by variant (pooled); (iv) P11 composition / "wins-over-benchmark" map
  across variants; (v) per-cell qualifying-event / exclusion-fraction map. Secondary tables to CSV.
- **Max new code modules: 1** — a **favourable-target geometry** module (`favourable_targets.py` or a
  bounded extension of `xen.expectancy`) supplying: the volume-profile builder (TickVolume-into-bins,
  POC, 70% value area, near/far edges), the trailing-magnitude target, and a generalized
  `barriers_from_fav(C, rd, fav_level)` that sets `adv` 1:1. The resolver, fills, realised returns,
  qualifying mask, and median bootstrap are **reused** from `xen.expectancy`; ZigZag, harami,
  strong-move, time-cap, and confirmation-index machinery are reused. Orchestration in
  `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant
  — those with a built barrier (valid `fav_dist > 0`, profile/warmup defined, not warmup-excluded) whose
  outcome is `FAV`, `ADV`, or `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry` (`xen.expectancy.
  realised_returns`), where `exit_price` is the P15 path-ordered fill (target level for FAV/ADV; cap-bar
  real close for TIMECAP) and `ATR_entry` = Wilder ATR(14) at the harami entry bar.
- **Per-cell endpoint (binding):** `E_cell = median` over the variant's qualifying-event return
  population. `DATA_CENSORED`, warmup-excluded, and validity-excluded (`fav_dist ≤ 0` / insufficient
  profile) events are **excluded** from the median and **disclosed as counts** per cell per variant.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant is
  **NOT_VIABLE-by-power** for that variant (non-reportable for its readout), never an undefined or
  infinite ratio. Conditioning + per-variant validity/warmup exclusions reduce counts vs the
  unconditioned base; depleted cells are disclosed.
- **Disclosed secondaries (never binding):** mean per-event return; first-hit `r = fav/(fav+adv)`
  (EXP-049 comparability); win rate (fraction with return > 0); TIMECAP/censoring fraction; the
  in-progress VP-POC variant; the `/STRONG-HA` arm; both P13 baselines; the MAD `/STRONG-STAT`
  sensitivity arm; per-variant validity/profile-exclusion counts; `/VPTARGET` `TickVolume`-proxy note.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m
strict; others `min_coverage=0.90`, carrying `TickVolume`); fence to `CloseTime ≤ train_end_ts`;
generate HA candles; run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed
moves + `xen.capture_barriers.confirm_indices`; detect haramis on HA candles aligned by `CloseTime`;
build the live in-progress state + `/STRONG-STAT`/`/STRONG-HA` conditioning (`xen.expectancy`); for each
qualifying harami compute every predeclared favourable target (benchmark, 3 VP-prior, 4 MAG, +
disclosed in-progress VP-POC), set adverse 1:1 and the adaptive cap, resolve each under P15, compute
ATR-normalised gross returns, bootstrap the per-cell median per variant, compute both P13 baselines
through the identical per-variant pipeline, compose by P11; second full pass for determinism. `tqdm`
over the 99-cell grid; bounded per-cell memory (do not retain all domain frames or all bootstrap
draws); fixed seed; deterministic. Outputs (`results/`): `per_cell_expectancy.parquet` (per cell ×
variant: median/CI expectancy, contrast vs benchmark, n_qualifying, exclusion counts, `r`, win rate,
TIMECAP fraction, baseline medians/contrasts, viability flag); `favourable_target_map.csv` (binding
`/STRONG-STAT` summary per variant); `secondary_map.csv` (`/STRONG-HA`, in-progress VP-POC, MAD arm,
baselines); `composition_readout.json` (per-variant P11, wins-over-benchmark, EVIDENCE_* fork);
`population_reconciliation.csv` (binding conditioned population vs EXP-053); `run_metadata.json` (seed,
frozen + new predeclared constants, EXP-053 source paths/hashes). Bounded plots from the collected
per-cell summaries (no reloads).

### Standard Loading Pattern (TRAIN slice, per cell)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

scan = pl.scan_parquet(path)                      # F01 file-order prefix; no full sort/collect
total_rows = int(scan.select(pl.len()).collect().item())
analysis_rows = int(total_rows * 0.7)             # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)             # first 70% of analysis = TRAIN
train_bars = scan.slice(0, train_rows).collect()  # TEST + holdout never sliced
# assert chronological; train_end_ts = train_bars["CloseTime"].max()
# domain aggregation (xen.bar_aggregator, carrying TickVolume) for 5m strict / others min_coverage=0.90
```

## Suggested Direction

Compose existing primitives; the only new code is the favourable-target geometry module (volume profile
+ trailing-magnitude target + generalized `barriers_from_fav`). Pipeline per cell:
`xen.zigzag.generate_zigzag` → confirmed moves + `xen.capture_barriers.confirm_indices`;
`xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami` → harami entry bars (aligned by
`CloseTime`); `xen.expectancy.live_in_progress_state` + `live_strong_stat` → the binding conditioned
population and `rd` (identical to EXP-053; cross-checked by `population_reconciliation`);
`xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` arm. For each qualifying harami: compute the
benchmark target (`xen.expectancy.benchmark_barriers`), the VP targets (new module, prior-completed-move
reference + disclosed in-progress) and MAG targets (new module); set `adv` 1:1 and the adaptive cap
(`xen.expectancy.adaptive_time_caps_by_epoch`); resolve each variant via
`xen.expectancy.resolve_path_ordered` → `realised_returns` → `qualifying_mask`; bootstrap per-cell median
per variant (`xen.expectancy.bootstrap_median_distribution`, `median_ci`); contrast vs benchmark and vs
baselines (`xen.expectancy.contrast_ci`). Emit the layered per-variant P11 / wins-over-benchmark /
EVIDENCE_* readout; **do not adjudicate §8** (single 014-B G2 after the full slate).
