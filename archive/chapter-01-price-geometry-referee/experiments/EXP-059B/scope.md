# Experiment: EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-059B is a **follow-up to EXP-059** (HYP-012,
> P14/P15/P18) that closes a measurement gap: EXP-059 ran every trailing/combined arm under the
> benchmark adaptive time cap. The four mandatory rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object is the **live `/STRONG`-conditioned HA harami**
>   (identical population to EXP-053/059, binding `/STRONG-STAT`, `/STRONG-HA` disclosed). Only the
>   **adverse-exit model** changes (trailing structure with no cap, no initial stop); the signal,
>   anchor, and favourable benchmark level are held at benchmark where an exit layer does not replace
>   them.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, never
>   the ZigZag trend-change confirmation.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. No position metric is
>   used as a filter. Every exit (secondary-pivot trailing ratchet, partial favourable legs) is acted
>   on at a bar known forward-in-time; no unconfirmed pivot is referenced.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross
>   per-event expectancy** (P14, ATR-normalised, P15 fills) of the position-weighted realised return.
>   First-hit `r` is undefined for these multi-exit/trailing arms and is reported only for the
>   single-leg BENCH reference.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · `CF-HA-HARAMI-001/HYP-012b` —
EXP-059B (registered `SCOPED`, Phase 014-B batch, `multiplicity-registry.md`). Exercises the new
countable branch `CF-HA-HARAMI-001/EXIT-TRAIL-UNCAPPED` (the standalone trailing adverse-exit model:
no time-cap backstop, no initial stop), with `CF-HA-HARAMI-001/EXIT-PARTIAL` (V2A legs) in the
combined arm.
**Surface role:** Follow-up read on the 014-B position-management surface (sibling of EXP-059). EXP-059
measured `/EXIT-TRAIL-STRUCT` and `/EXIT-PARTIAL` **within the benchmark 3-barrier horizon** (every arm
inherited the P4 adaptive cap, floor=6); even `TRAIL-TP-NOINIT` retained the cap. The family thesis
treats the trailing stop as a **separate adverse-exit model that replaces the 3-barrier geometry**, not
a barrier swap. EXP-059B measures that model on its own terms: does an **uncapped, no-initial-stop**
structure trailing stop — alone (`TRAIL-PURE-UNCAPPED`) or alongside V2A partial favourable legs
(`COMBINED-UNCAPPED-V2A`) — produce higher gross per-event median expectancy than the benchmark single
fixed exit? Output joins the single 014-B **G2** (no intermediate gate, no closure here).
**Governing design:** `014-B-design.md` (§5 slate, §10 addendum) + `014-B-EXP-059B-uncapped-trailing-addendum.md`
+ `014-B-D0-addendum.md` (P14/P15/P18/P20/P21); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the
family spec `candidate-families/harami.md`.
**Verification basis (recorded before any data contact):** the EXP-059 gap was verified directly in
`python/src/xen/position_exits.py` and `python/experiments/EXP-059/code/run_experiment.py` — see
§"Verified gap" below.
**Reuses:** the EXP-053/059 conditioned-signal construction, benchmark levels, P15 fills, P14 median
bootstrap, paired/independent contrasts, ZigZag (primary `atr_mult=1.0`, secondary `atr_mult=0.5`),
harami, `/STRONG-STAT`/`/STRONG-HA`, confirmation indices, and the `xen.position_exits` partial-leg /
trailing machinery (extended with a **new uncapped entry point** — see Complexity Budget).

## Verified gap (recorded before any data contact)

1. **Time cap is universal in EXP-059.** `xen.position_exits.resolve_legs` / `_scan_event` bound the
   forward scan at `cap_end = ei + n_ev` and emit an explicit `PX_TIMECAP` exit for any leg still open
   at the cap; `run_experiment.resolve_arm` passes `bench_n` (the P4 adaptive cap) as `n_event` to both
   `build_active_stops` and `resolve_legs` for **every** arm, trailing and combined included.
2. **Initial stop.** `build_active_stops` seeds the stop at the benchmark 1:1 `adv` unless
   `trail_init_none=True`. Among trailing arms only `TRAIL-TP-NOINIT` sets `trail_init_none=True`;
   `TRAIL-PURE`, `TRAIL-TP-INIT`, and all `COMBINED-*` keep the 1:1 initial stop.
3. **Therefore** the configuration with **no initial stop AND no time cap** ("pure trailing as
   designed") was never measured. `TRAIL-TP-NOINIT` is the closest existing arm (no init stop) but
   retained the cap. This experiment fills exactly that gap; it is a new countable variant, not an
   EXP-059 amendment (no scope expansion of an approved experiment).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum.
  `/EXIT-TRAIL-UNCAPPED` is registered (countable) but consumes a slot only when a future scope
  activates it as a screening candidate — which, per P21, cannot happen before G2 PROCEED_TO_SCREEN.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis
  set), identical fence to EXP-049/053–059. The TEST-read ledger requires no entry and none is created;
  the current counted-read tally is irrelevant because no TEST stratum is touched. The conditioned
  HA-harami population had its first new-universe TRAIN contact in EXP-053 (same definition); no new
  stratum is opened and the global-holdout seal carries forward unchanged. **Forward scans are unbounded
  to the TRAIN edge** and clipped to `train_end_ts`; a window that would extend past `train_end_ts` is
  `DATA_CENSORED`, never resolved against TEST/holdout rows.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close`), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded
against the in-progress strong move), an **uncapped structure trailing adverse-exit model** — no
benchmark time-cap backstop and no initial 1:1 stop (the position carries no adverse exit until the
first secondary-ZigZag `atr_mult=0.5` pivot confirms after entry, then ratchets monotonically) — either
standalone (`TRAIL-PURE-UNCAPPED`, no favourable target) or combined with V2A partial favourable legs
(`COMBINED-UNCAPPED-V2A`), produces **higher gross per-event median expectancy** (P14, ATR-normalised,
position-weighted, P15 fills, real prices) than the **benchmark single fixed exit** (50% fav / 1:1 stop
/ adaptive cap, single leg) on the binding `/STRONG-STAT` arm.

Falsifiable: if **neither** uncapped arm clears the P11 quorum (≥5 cells over ≥3 instruments with
CI_low > 0 on its own median expectancy) **and** beats BENCH (arm − BENCH paired contrast CI_low > 0 in
the quorum), then removing the cap/initial-stop from the trailing model does **not** improve conditioned
capture (a valid characterization result that feeds G2 — never a closure inside 014-B).

## Question

Does the trailing adverse-exit model, run **as designed** (no time-cap backstop, no initial stop), raise
the conditioned HA-harami's gross per-event median expectancy vs the benchmark — and, vs its **capped
no-init sibling**, how much of any difference is attributable specifically to removing the cap? At what
cost in qualifying-event **count** (unbounded windows raise `DATA_CENSORED` on late-TRAIN events) and in
**exit-reason composition** (TRAIL fill vs favourable legs vs DATA_CENSORED)?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053–059/VAL-004) for the primary ZigZag substrate
  (`atr_mult=1.0`), the **secondary trailing ZigZag** (`atr_mult=0.5`), confirmed moves, strong-move
  magnitudes, the benchmark favourable level, the benchmark cap (BENCH and the capped siblings only),
  all leg/stop levels, P15 fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only**
  (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector). **No HA price enters any metric.**

### Event population (the live conditioned signal — identical to EXP-053/059)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter:
  `M_sofar = |C − start_pivot|` (last *confirmed* primary pivot → harami real close `C`) is **≥ p75** of
  the trailing-20 confirmed-move magnitudes (P7, binding). `/STRONG-HA` (P8) is a **disclosed secondary**
  arm run through the identical pipeline.
- **Trade / reversal direction** `rd` = `Direction_k` of the last confirmed primary-ZigZag move
  (`xen.expectancy.live_in_progress_state`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` (the same functions
  EXP-053/059 used) so the binding population is byte-identical to EXP-053 (verified by population
  reconciliation).

### Entry anchor

The **harami confirmation-bar real close** `C`. Identical to EXP-053/059.

### Arms (predeclared; OAT on the adverse-exit model only)

Notation: `C` = entry close; `rd` = trade direction; `M_sofar` = magnitude-so-far;
`fav_dist = 0.50·M_sofar` (P2); `fav = C + rd·fav_dist`; `adv = C − rd·fav_dist` (benchmark 1:1);
`bench_N` = benchmark P4 adaptive cap (floor=6). Every leg/stop is evaluated on **real prices** under
the **P15 path model**. The **uncapped** arms scan `[entry_idx+1, last_train_idx]` (TRAIN-fenced, no
`bench_N` bound); the **capped** arms scan `[entry_idx+1, entry_idx+bench_N]` exactly as EXP-059. A
window truncated by the TRAIN edge before resolution is `DATA_CENSORED` (excluded-with-record).

| # | Arm id | Favourable side | Adverse model | Cap | Initial stop | Role |
|---|--------|-----------------|---------------|-----|--------------|------|
| 1 | `BENCH` | 50% fav (1 leg) | 1:1 fixed | adaptive cap | 1:1 | Reference; reproduces EXP-053/059 BENCH (invariant). **Binding paired-contrast anchor.** |
| 2 | `TRAIL-PURE-UNCAPPED` | none (let it run, 1 leg) | structure trail | **none** | **none** | **BINDING.** Pure trailing as designed. |
| 3 | `COMBINED-UNCAPPED-V2A` | V2A legs {1/3, 2/3, 1}×fav_dist | structure trail (on still-open weight) | **none** | **none** | **BINDING.** Partial favourable legs + uncapped no-init trailing. |
| 4 | `TRAIL-PURE-NOINIT-CAPPED` | none (1 leg) | structure trail | adaptive cap | none | **Disclosed sibling** — isolates the cap effect (differs from #2 only by the cap). |
| 5 | `COMBINED-V2A-NOINIT-CAPPED` | V2A legs | structure trail (on still-open weight) | adaptive cap | none | **Disclosed sibling** — isolates the cap effect for the combined arm. |

**Adverse-exit model (arms 2–5).** The monotone structure trailing stop on the **secondary
`atr_mult=0.5` ZigZag** (P18 ratchet rule, unchanged from EXP-059): on a newly confirmed secondary move
whose `Direction == rd` (an up-move for a long fade, mirror for a short), set
`stop ← max(stop, previous secondary pivot EndPrice)` for a long, `min(...)` for a short. **No initial
stop** in all four arms (NaN until the first post-entry secondary confirmation). The stop level in force
at bar `t` uses only secondary moves with `ConfirmIdx ≤ t` (causal). For the combined arms the partial
favourable legs close at their fixed `C + rd·frac·fav_dist` levels when touched (P15); the trailing stop
manages all **still-open** weight and, when it binds, closes every still-open leg at that level/bar.

**Why V2A for the combined arm.** PARTIAL-V2A was the simplest broad performer in the capped EXP-059
results and uses only fixed favourable price levels (no reversal-event leg), so the combined arm needs
**no** `bench_N`-bounded reversal-event locator — consistent with "the cap is not used."

**Per-event realised return (binding endpoint input).** `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`
with `Σ_l w_l = 1` and `ATR_entry` = Wilder ATR(14) at the harami entry bar (P14). Single-leg arms (BENCH,
TRAIL-PURE-*) are the `w=1` case. Each `exit_px_l` is its P15 fill (favourable level, trailing-stop fill,
or — for the capped siblings only — the cap-bar real close). Uncapped arms have **no TIMECAP exit**: a
still-open leg/position at `last_train_idx` is `DATA_CENSORED`. `R_event` is the per-event value fed to
the median bootstrap and the paired contrasts — same machinery as EXP-056/057/058/059.

### Parameters (all frozen D0 / predeclared; no tuning)

Primary ZigZag Wilder ATR(14) `ATR_MULT = 1.0` (P1); **secondary trailing ZigZag Wilder ATR(14)
`ATR_MULT_TRAIL = 0.5` (P18)**; `/STRONG-STAT` trailing-20 ≥p75 (P7); `/STRONG-HA` `X=3` (P8); benchmark
favourable 50% of `M_sofar` (P2); benchmark adverse 1:1 (P3, BENCH only); benchmark cap
`(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` (P4, BENCH + capped siblings only);
ATR-normalisation = Wilder ATR(14) at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`,
`N_BOOT = 10_000`, fixed seed (P14). V2A fractions `{1/3, 2/3, 1}`; 3 equal legs (`w=1/3`) for combined
arms; monotone ratchet to the most-recent confirmed secondary pivot; **no initial stop** in all trailing
arms. The **uncapped** arms use no `bench_N` bound; `ATR_MULT_TRAIL` is the frozen P18 default (no
sensitivity grid here). Nothing is tuned against outcomes.

### Instruments / cells

The **99-cell EXP-049/053–059 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** (≥5 cells over ≥3
instruments) for any "winning arm" claim. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per
cell, F01 file-order-prefix convention identical to EXP-049/053–059). TEST and the final-30% **global
holdout** are **not** read. All forward windows are clipped to `train_end_ts`; an unresolved truncated
window is `DATA_CENSORED` (disclosed), never resolved past the edge.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) through the **identical uncapped exit pipeline** for each binding arm — does the uncapped
  trailing scheme beat random entries under the same scheme?
- **MA(20,50) segmentation** (alternative trend substrate) through the identical per-arm pipeline; the
  secondary trailing structure for the MA-seg baseline uses the same `atr_mult=0.5` ZigZag (a real-bar
  construct independent of the entry segmentation).
- Baselines are disclosed secondaries; the binding readout is each arm's own median expectancy and the
  arm − BENCH paired contrast.

### Look-ahead / causality discipline (binding)

- Primary and secondary ZigZag pivots are future information until confirmed. The signal
  (harami + `/STRONG-STAT`), `M_sofar`, the favourable benchmark level, the V2A leg levels, and (for
  BENCH + capped siblings) the benchmark cap use **only** confirmed prior moves and **real bars at or
  before the entry bar** for construction at entry.
- Every exit is a **forward** event acted on at a bar known going forward: fractional-target touch
  (intrabar P15), and the structure trailing stop (the level in force at bar `t` uses only secondary
  moves with `ConfirmIdx ≤ t` — the stop moves at the confirmation bar, never the retroactive pivot bar).
- The trailing ratchet is monotone (never loosens) and uses only confirmed secondary pivots. The uncapped
  forward scan reads bars `[entry_idx+1, last_train_idx]`, fenced `CloseTime ≤ train_end_ts`; a window
  truncated before resolution is `DATA_CENSORED`.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, all benchmark/leg/stop levels, the secondary
trailing ZigZag, P15 fills, weighted expectancy, win rate, and exit-reason composition on real domain-bar
OHLC. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Uncapped trailing adverse-exit model only.** The favourable benchmark level (50%, where present) is
  held at benchmark; the favourable target geometry (EXP-056), other adverse models (EXP-057), and the
  third-barrier horizon variants (EXP-058) are out of scope. No `ATR_MULT_TRAIL` sensitivity grid
  (frozen 0.5). No `/BARCFG`/`/CONFIRM` overlays; no position-in-move filter.
- No parameter tuning; **no post-result variant selection** (all 5 arms reported); no gate adjudication
  (single G2 after the full 014-B slate — EXP-059B emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The
binding endpoint is **median per-event position-weighted gross expectancy** `E_cell` (ATR units, P15
fills), on the **`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block
bootstrap, one-sided 95%) **AND ≥ 30 qualifying events**.

- **EVIDENCE_FOR (uncapped trailing helps):** ≥1 binding arm (`TRAIL-PURE-UNCAPPED` or
  `COMBINED-UNCAPPED-V2A`) **(a)** clears P11 on its own median expectancy **AND (b)** beats BENCH on the
  **arm − BENCH paired contrast** (paired CI_low > 0 on the common qualifying-event subset) within the
  P11 quorum. The winning arm(s) and their margin over benchmark are the deliverable; no candidate
  registration (G2 only).
- **EVIDENCE_AGAINST (uncapping is not a lever):** neither uncapped arm both clears P11 and beats the
  BENCH contrast. Recorded as a measured-negative characterization; routing deferred to G2.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the
  uncapped arms because unbounded windows raise `DATA_CENSORED` (late-TRAIN depletion), no correctness
  failure. Disclosed; never defaulted to a ratio. **This is a materially more likely outcome than in
  EXP-059** because the cap no longer guarantees bounded resolution.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  Invariant checks: (i) BENCH reproduces EXP-053/059 per-cell median expectancy and qualifying count to
  tolerance; (ii) population reconciliation vs EXP-053 exact; (iii) leg weights sum to 1.0; a degenerate
  single-trigger uncapped arm reproduces the equivalent single-leg uncapped arm to float precision;
  (iv) the trailing stop is monotone and changes level **only** on secondary-ZigZag confirmation bars
  (`ConfirmIdx ≤ CloseTime`); (v) every exit price is a real-bar P15 fill and every exit bar has
  `CloseTime ≤ train_end_ts`; (vi) the uncapped arms emit **no** `TIMECAP` class (only TRAIL, FAV, or
  DATA_CENSORED); a still-open position at `last_train_idx` is DATA_CENSORED; (vii) the trailing stop
  binds all still-open partial legs at the same bar/level.

The deliverable label is **UNCAPPED_TRAILING_CHARACTERISED** carrying the per-cell + P11 readout for all
5 arms, the EVIDENCE_* classification, the binding BENCH contrast per binding arm, the **disclosed
cap-isolation contrast** (uncapped arm − its capped no-init sibling, paired, common subset), both filter
arms (`/STRONG-STAT` binding, `/STRONG-HA` disclosed), both P13 baselines, and all disclosed secondaries
(per-arm qualifying-event count; **uncapped `DATA_CENSORED` disclosed separately from capped censoring**;
warmup exclusion counts; exit-reason composition; win rate; mean per-event return; BENCH first-hit `r`;
median/percentile **holding duration** per arm — bars from entry to exit — to show how much longer the
uncapped arms hold than BENCH/capped siblings). No phase closure or candidate registration here.

## Complexity Budget

- **Max distinct statistical methods: 4** — identical to EXP-056/057/058/059: (1) regime-clustered
  moving-block bootstrap CI on an arm's median expectancy per cell; (2) the same on each P13 baseline;
  (3) paired-median contrast CI (`xen.favourable_targets.paired_median_contrast_ci`, common
  qualifying-event subset) — applied for both the binding vs-BENCH contrast and the disclosed
  cap-isolation (uncapped − capped-sibling) contrast (same method, different arm pair, not a new method);
  (4) arm − baseline contrast CI (`xen.expectancy.contrast_ci`).
- **Max visualisations: 5** — (i) per-arm median-expectancy forest/CI per cell vs BENCH; (ii) arm − BENCH
  contrast heatmap (arms × cells); (iii) cap-isolation contrast (uncapped − capped sibling) by cell;
  (iv) P11 / wins-over-benchmark map across arms; (v) exit-reason composition + holding-duration and
  `DATA_CENSORED`-rate by arm (the mechanism/censoring diagnostic). Secondary tables to CSV.
- **Max new code modules: 0 new modules — extend the existing `xen.position_exits`** with a **new
  uncapped entry point** (e.g. `resolve_legs_uncapped` + a lazy trailing-stop helper) that (a) ends the
  scan at `last_train_idx` (no `bench_N` bound), (b) emits **no** `TIMECAP` class (only TRAIL, FAV, or
  DATA_CENSORED), and (c) computes the trailing stop **lazily inside the forward scan** (advancing the
  secondary-pivot pointer as bars advance) — it **must not** call the dense `build_active_stops`, whose
  `(n, max(n_event)+1)` array would blow up to `O(n × train_len)` when uncapped. **Do not modify the
  existing `resolve_legs` / `build_active_stops` / `_scan_event`** — EXP-059's frozen results depend on
  them; add alongside. Orchestration in `code/run_experiment.py`. The capped sibling arms (#4, #5) reuse
  the existing EXP-059 capped resolver with `trail_init_none=True`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event`, defined for every
  **qualifying** event of an arm — barriers/legs constructible (`fav_dist > 0`, finite positive
  `ATR_entry`, secondary ZigZag available) and the position/every leg reaches a finite P15 exit
  (favourable trigger, trailing-stop fill, or — capped siblings — cap close) **within the TRAIN-fenced
  window**. `DATA_CENSORED` and construction-warmup events are **excluded** from the median and
  **disclosed as counts** per cell per arm.
- **Per-cell endpoint (binding):** `E_cell = median` over the arm's qualifying-event `R_event`.
- **Censoring disclosure (binding requirement):** the uncapped arms' `DATA_CENSORED` rate is reported
  **separately** from the capped arms' (BENCH/capped-sibling) censoring. The paired contrasts run on the
  **common qualifying subset** (events qualifying under both arms of the pair); the qualifying-subset
  size and the per-arm exclusions are disclosed so the contrast is interpretable.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm is **NOT_VIABLE-by-power**
  for that arm (non-reportable for its readout), never an undefined/infinite ratio. Uncapped censoring
  depletes counts on shallow-history/late-TRAIN cells; depleted cells are disclosed, never defaulted.
- **Exit-reason composition** and **holding duration** are computed and reported per arm as disclosed
  secondaries (mechanism diagnostics); never enter viability.
- **First-hit `r`** is defined only for the single-leg **BENCH** arm (`r = n_FAV/(n_FAV+n_ADV)`, TIMECAP
  excluded, EXP-049 convention; expected ≈0.50). Undefined for the trailing/combined arms; not a
  viability input.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows =
int(total_rows*0.7)`; `train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows`
file-order rows (F01 prefix; never sort/collect the full file, never read TEST/holdout); assert
chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict; others
`min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run the **primary**
`generate_zigzag(atr_mult=1.0)` + `confirm_indices` and the **secondary** `generate_zigzag(atr_mult=0.5)`
+ secondary confirm indices; detect haramis (aligned by `CloseTime`); build the live in-progress state +
`/STRONG-STAT`/`/STRONG-HA`; compute the benchmark favourable level (+ cap for BENCH/capped siblings);
for each of the 5 arms compute per-event exits — BENCH via `resolve_path_ordered`; the two **uncapped**
arms via the new uncapped entry point (lazy trailing, no cap, DATA_CENSORED at edge); the two **capped
siblings** via the existing EXP-059 capped resolver with `trail_init_none=True` — the weighted `R_event`,
the qualifying mask, bootstrap the per-cell median per arm, both P13 baselines through the identical
per-arm pipeline, compose by P11; second full pass for determinism. `tqdm` over the 99-cell grid;
**bounded per-cell memory** — the uncapped per-event scan is `O(last_train_idx − entry_idx)` worst case
(no dense stop array); fixed seed; deterministic. Outputs (`results/`):
`per_cell_expectancy.parquet` (per cell × arm: median/CI expectancy, paired contrast vs BENCH, paired
cap-isolation contrast, n_qualifying, `DATA_CENSORED`/warmup counts, exit-reason composition, holding
duration, win rate, baseline medians/contrasts, viability flag); `uncapped_trailing_map.csv` (binding
`/STRONG-STAT` summary per arm); `secondary_map.csv` (`/STRONG-HA`, baselines, BENCH `r`, exit-reason
composition, holding-duration percentiles); `composition_readout.json` (per-arm P11,
wins-over-benchmark, cap-isolation summary, EVIDENCE_* fork); `population_reconciliation.csv` (binding
conditioned population vs EXP-053; BENCH expectancy/`r`/count vs EXP-053/059);
`run_metadata.json` (seed, frozen + predeclared constants, EXP-053/059 source paths/hashes). Bounded
plots from the collected per-cell summaries (no reloads).

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
# domain aggregation (xen.bar_aggregator) for 5m strict / others min_coverage=0.90
```

## Suggested Direction

Reuse the EXP-059 per-cell pipeline wholesale (population, benchmark levels, secondary ZigZag, P13
baselines, bootstrap, contrasts). The **only** new code is an uncapped entry point in
`xen.position_exits`: a lazy sequential P15 scan from `entry_idx+1` to `last_train_idx` that maintains
the trailing stop incrementally (advance a secondary-confirmation pointer as bars advance; seed NaN until
the first post-entry secondary confirmation; ratchet monotonically), closes V2A partial legs at their
fixed P15 levels, binds all still-open weight when the trailing stop fills, and marks any still-open
position at the TRAIN edge `DATA_CENSORED` (no `TIMECAP`). The capped siblings reuse the existing capped
resolver with `trail_init_none=True`. Emit the per-arm P11 / wins-over-BENCH / cap-isolation / EVIDENCE_*
readout plus the binding exit-reason, holding-duration, and separated `DATA_CENSORED` disclosures; **do
not adjudicate G2** (single 014-B G2 after the full slate).
