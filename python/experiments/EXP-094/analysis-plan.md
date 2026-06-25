# Analysis Plan: Experiment EXP-094

**4h Readiness + Falsification Re-Screen (RSI-2 fade / EXIT-RCT) · Phase 021 · `CF-MR-001/HYP-002` · governed by
`D0-amendment-004`.** TRAIN-only · 0 slots · 0 counted TEST reads · holdout sealed · real OHLC · deterministic.

## Objective

Determine whether the bare RSI-2 fade's net-of-cost EXIT-RCT edge on **4h** (the archived `TEMP-091` hunch:
RCT net-clears 12/12 instruments, mean & median positive) reflects the **fade entry signal** or is **generic
ATR-normalized oscillation harvesting** that EXP-089's 4h dead-by-absence (1/14) correctly flagged. Three
TRAIN-only legs produce the binding admission rule of `D0-amendment-004` §4: (a) 4h readiness/MDE; (b) the
frozen net exit screen; (c) the **matched-random/shuffled-entry RCT falsification null** (the crux). A 1h
positive control assures the falsification test has power.

The whole substrate (`build_cell_context` / `resolve_arm` / `xen.intrabar_fill` / `xen.capgeo_cost`) is reused
**verbatim** from EXP-090/091; 4h is patched into `DOMAINS` as 240-minute bars (as `TEMP-091` did). No frozen
constant is re-tuned.

---

## Methodology

### Step (a) — 4h member-cell readiness & per-cell RCT MDE (EXP-090 analog)

- **Method.** For each of the 13 `D0-amendment-003` cost-table instruments × 4h: build the cell context
  (`E90.build_cell_context`), count RSI-MR CORE events, confirm substrate determinism and fill-validity, and
  compute the **per-cell event-level MDE on EXIT-RCT** under the frozen referee calibration
  (`xen.referee_calibration`, the EXP-090 routine), with both nulls' FPR. A cell is a **MEMBER** iff
  `n_events ≥ 15` (EXP-080 floor) ∧ deterministic ∧ **finite RCT MDE**; else `COVERAGE_EXCLUDED` (retained,
  with the exclusion reason recorded). JP225-4h is expected excluded a priori (failed to build in `TEMP-091`;
  US500-4h/JP225-4h were `COVERAGE_EXCLUDED` on 4h at EXP-080).
- **Why sufficient.** Identical to the EXP-090 readiness/calibration that powered the 15m/1h members; 4h was
  never put through it, so the member set and the EXP-093-eligible margins must be established here. No new
  method.
- **Simpler alternative considered.** Skip readiness, screen all 13 cells (what `TEMP-091` did). Rejected: a
  cell with no finite MDE cannot bound a confirmation (EXP-044/090 precedent) and would launder an unpowered
  cell toward a counted TEST read.
- **Assumptions.** The EXP-090 calibration's null-FPR machinery is valid at 4h n-scales (it is in the binding
  n ≥ 120 regime; small-n inflation disclosed/non-binding, as EXP-090 §D6). 4h event counts are large
  (`TEMP-091`: n_resolved 855–1088/cell) → no thin-cell power concern expected.
- **Expected output.** `readiness_4h.csv` (per cell: n_events, n_resolved, resolved_frac, determinism,
  fill_valid, RCT MDE, FPR under both nulls, MEMBER/COVERAGE_EXCLUDED + reason); the member set for (b)/(c).

### Step (b) — Frozen net exit screen on 4h (EXP-091 analog; D6/4a)

- **Method.** On the (a)-member cells, resolve the **full frozen D2 exit slate** (EXIT-RCT primary; EXIT-ERT,
  ATR-barrier, RSI-revert-on-close, fixed-bar, partial/trail — for the file drawer) through the EXP-090
  engine, overlay the `D0-amendment-003` conservative cost (`event_costs`, `RT_i` per instrument,
  `fin_bps_day=0`), and compute **net per-event expectancy** in ATR(14) units. Binding figure: the net
  per-event expectancy **moving-block bootstrap one-sided lower bound** (`net ci_low_1s`, Z=1.645, `alpha=0.10`,
  `n_boot=10_000`) via `xen.ass.moving_block_bootstrap_cis` — exactly the EXP-091 statistic. A cell **net-clears**
  iff `net ci_low_1s > 0`; an arm **passes** iff it net-clears in **≥5 cells over ≥3 instruments** (D6/4a,
  unchanged). Co-report gross, net mean **and median**, resolved/tie-break fractions, terminal mix,
  `holding_days`, and the RT/2 faster-cost companion (disclosure, as EXP-091).
- **Why sufficient.** Reproduces the binding EXP-091 screen on the new domain with the same frozen rule and
  cost; the moving-block bootstrap is the programme's non-parametric workhorse for serially dependent
  per-event series (no normality/i.i.d. assumption).
- **Simpler alternative considered.** A plain bootstrap or t-interval. Rejected — ignores serial dependence;
  the moving-block bootstrap is the frozen phase choice.
- **Assumptions.** Stationarity within the TRAIN block only locally; the moving-block design absorbs
  short-range dependence. Resolved-event denominator (finite gross, ATR>0, valid hold) per (cell × arm).
- **Expected output.** `screen_per_cell_arm_4h.csv`, `quorum_per_arm_4h.csv`, `cost_decomposition_4h.csv`,
  `cost_sensitivity_faster_4h.csv` (EXP-091 schema, 4h).

### Step (c) — Matched favourable-target-distance oscillation null (THE CRUX, binding — `D0-amendment-005`)

This is the leg that reconciles the EXP-089 contradiction. **`D0-amendment-005` (2026-06-24) corrected the
binding null**: the original SUB-RANDOM-entry RCT null is structurally biased toward admission (the RCT target
`P*=Close+(AL−AG)` is signal-derived, so at random non-extreme bars it is wrong-side and the engine instant-fills
it — the random arm has no comparable target regardless of the truth). The binding null is now a
**matched favourable-target-distance oscillation null** that gives the random arm a genuine, comparable target by
construction, holding the adverse side / fill / cost identical.

- **Construction (frozen, deterministic). Per member cell, for EXIT-RCT:**
  1. **Real arm (unchanged):** the frozen EXIT-RCT resolved through the verbatim `E90.resolve_arm(... "RCT" ...)`
     engine (= leg (b)). Record each real resolved event's **favourable target-distance multiple**
     `μ_k = (P*_{entry_k} − Close_{entry_k})·direction_k / ATR(14)_{entry_k}` (`ctx.rct_target[entry_k]` vs
     `ctx.close[entry_k]`); positive by construction at real extremes.
  2. **Matched-distance random arm (the null):** take the cell's real RCT resolved count `n` and direction
     multiset; draw `n` distinct bars via `xen.capgeo_substrates.random_entries(bars, instrument=…, domain="4h",
     n_target=n, rng=seed_for(EXP-094, instrument, "4h", "RCT", "randentry"))` (SUB-RANDOM, without replacement,
     look-ahead-safe); **shuffle the real direction multiset** onto them (seed `…"randdir"`); place a **static
     favourable limit** `entry_close + direction · m · ATR(14)_entry`, where `m` is **resampled with replacement
     from the real cell's `{μ_k}`** (seed `…"randdist"`). Resolve through the identical adverse side
     (`2.0×ATR` stop + MR-tempo cap) + 1m intrabar fill + `D0-amendment-003` cost. **Implementation: reuse the
     EXP-090 `ATR-BARRIER` static-favourable-level branch (`entry_close + d·mult·atr_e`) with a per-event
     resampled `mult` in place of the fixed `1.0×ATR`** — favourable by construction, so **no wrong-side /
     degenerate instant-fill is possible.**
  - Report per cell: realized `n`, the `{μ_k}` summary (mean/median target multiple), the random arm's
    `resolved_frac` and terminal mix (mechanism / fairness disclosure).
- **Paired-Δ statistic & bound.** Per cell, `Δ_cell = mean(real RCT net) − mean(matched-distance-random net)`
  (ATR units).
  Uncertainty by a **two-sample moving-block bootstrap of the difference of means**: independently
  moving-block-resample the real net series and the random net series (same block length rule as
  `xen.ass.moving_block_bootstrap_cis`, `n_boot=10_000`), form `Δ* = mean_real* − mean_random*`, take the
  **5th percentile** as the one-sided lower bound `Δ_lo` (Z=1.645). A cell **real-beats-random** iff
  `Δ_lo > 0`. (Real and random arms are distinct event sets ⇒ the pairing is at the **cell** level, not
  per-event — explicitly disclosed.)
- **Binding admission quorum.** EXIT-RCT's real entry **passes the falsification** iff it real-beats-random in
  **≥5 cells over ≥3 instruments** (same quorum shape as the net screen).
- **Disclosed companions (non-binding).** Two sensitivities, neither gating: (1) the original **SUB-RANDOM-entry
  RCT** null (`D0-amendment-005`) with the wrong-side guard (`wrongside_frac` reported); (2) the **realized-capture
  matched-distance** null (audit §5) — identical to the binding null but the limit distance is resampled from the
  real RCT **realized favourable capture** `{κ_k}` (~0.27 ATR) rather than the entry-bar target `{μ_k}` (~0.5 ATR),
  reported as `delta_lo_realized` / `beats_realized`. It bounds the mild anti-conservatism of the entry-bar-target
  match (a farther target handicaps the null); if real still beats this nearer-target null in quorum, admission is
  robust to the distance choice.
- **Why sufficient.** The matched-distance null gives the random arm a comparable favourable target by
  construction, so the contrast tests the actual oscillation hypothesis; it reuses the validated SUB-RANDOM
  generator + the EXP-090 ATR-BARRIER static-level construction + the EXP-091 resolution path. Non-parametric.
- **Simpler alternative considered.** SUB-RANDOM-entry RCT as the *binding* null — rejected (`D0-amendment-005`):
  biased toward admission (signal-derived target degenerate at random bars) — retained only as the companion.
  Compare real net `ci_low` to 0 only (leg b) — rejected: that is what `TEMP-091` did and cannot distinguish
  signal from oscillation.
- **Expected output.** `falsification_paired_delta_4h.csv` (per cell: n_real, n_rand, real_net_mean,
  rand_net_mean, mu_mean, mu_median, Δ_cell, Δ_lo, beats_random, rand_resolved_frac, rand_terminal_mix, plus the
  companion SUB-RANDOM-entry `delta_lo_companion` + `wrongside_frac`), `falsification_quorum.csv`.

### Step (d) — 1h positive control (disclosed companion; power assurance, non-binding)

- **Method.** Run the identical Step (c) real-vs-random RCT paired-Δ on the **EXP-091 1h clearing cells**
  (EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h), where EXP-089 *did* find availability (1h 11/16). Expectation: real
  beats random (`Δ_lo > 0`) on most/all of them.
- **Interpretation role.** If real does **not** beat random where a true signal is known to exist, test (c)
  lacks power ⇒ EXP-094 reads **INCONCLUSIVE** rather than refuting 4h. This guards against a false
  `4H_CLOSED_OSCILLATION` from an under-powered null.
- **Expected output.** `positive_control_1h.csv` (5 cells: Δ_cell, Δ_lo, beats_random).

### Step (e) — D0 bite-check of the §4(c) matched-distance paired-Δ statistic (GREEN required before any result run)

The paired-Δ falsification quorum is a **new selection statistic** ⇒ `D0-amendment-004` §5 requires a GREEN
bite-check **before** EXP-094 produces any binding result. Design (synthetic, no market verdict read):

- **FPR leg (controlled false admission).** Under a same-distribution null (two **independent block-resamples of
  the same matched-distance-null net series**), the **mean per-cell `beats_random` rate** must be ≤ the nominal
  α (≤ 0.10) **and** the ≥5/≥3 **quorum-fire rate** ≤ 0.10, over `BITE_REPLICATES` synthetic replicates. Confirms
  the gate does not manufacture a false 4h admission.
- **Power leg (detects a true effect) — corrected per audit §4 (first run).** *Evaluate PER-CELL detection*
  (not the quorum-compounded fire rate — which compounds per-cell power and is structurally too stringent), and
  plant a **two-sample-appropriate** effect (not the sub-threshold single-arm MDE — the two-sample statistic's
  per-cell detection threshold ≈ 1.645·√2·σ/√n ≈ 0.048 ATR ≫ the 0.025 single-arm MDE, so planting the MDE gives
  power 0 by construction). Plant a grid `g ∈ {0.05, 0.10, 0.15, 0.20}` ATR; **GREEN-power iff per-cell
  detection at the fixed material reference `BITE_POWER_REF_ATR = 0.10 ATR` (set a priori — no result-peeking)
  reaches `BITE_TPR_TARGET = 0.80`.** Report the full `power_by_g` curve, the two-sample per-cell MDE (smallest g
  ≥ target), and the observed median real−null Δ for context. (The statistic's empirical power is independently
  confirmed by the 1h positive control 5/5 and the 4h members 6/6.)
- **Verdict.** **GREEN** iff FPR-controlled ∧ per-cell power ≥ target at the reference effect; recorded as
  `bite_check.json` (seeded). RED halts EXP-094 to the pipeline before any 4h binding read.
- **Why here.** Mirrors the EXP-080/086/089 bite-check convention. Reuses the bootstrap machinery; adds no new
  market read. *(First-run RED + correction: see `audit.md` §4.)*

---

## Visualisations (≤ 4)

1. **4h net `ci_low` heatmap** (member cells × 6 arms), green > 0 = net-clear — Step (b); shows the 4h screen
   surface and that only RCT clears (the `TEMP-091` pattern).
2. **Real-vs-random paired Δ per 4h cell (RCT)** — horizontal bars of `Δ_cell` with `Δ_lo` whiskers, zero line,
   cells with `Δ_lo>0` marked, the ≥5/≥3 quorum annotated — Step (c), the **headline falsification plot**.
3. **Mechanism quorum bar** — per arm/per construction: real net-clear cells vs **real-beats-random** cells vs
   **random-entry net-clear** cells. If random-entry RCT *also* net-clears broadly, the bar makes the
   oscillation-harvest reading visible at a glance.
4. **1h positive control scatter** — real vs random RCT net per cell on the 5 EXP-091 clearing cells, y=x line —
   Step (d); visual power assurance.

## Interpretation Guide (pre-registered; from `D0-amendment-004` §4)

- If **(b) RCT passes the ≥5/≥3 quorum AND (c) real-beats-random passes ≥5/≥3** → **ADMIT_4H**: the 4h net edge
  is signal-driven; EXP-089's 4h dead-by-absence is a metric-specific false negative (the ~3-bar MFE_med
  statistic missed the RCT-capturable geometry). 4h RCT cells (the real-beats-random ones, smallest-defensible)
  become eligible for EXP-092/093 — no new slot.
- If **(b) passes BUT (c) fails** (real does not beat random in quorum) → **4H_CLOSED_OSCILLATION**: the 4h
  net-clear is generic oscillation/exit-geometry harvesting, not the fade. 4h stays **closed, retained**;
  EXP-089 reaffirmed and now mechanistically explained. *(Also raises a mechanism question for the 1h pass —
  recorded, not acted on here.)* — **conditional on the (d) positive control passing**; if (d) fails, read
  **INCONCLUSIVE** instead.
- If **(b) fails** → **4H_EMPTY**: 4h net screen empty; retained.
- If member cells after (a) are too few to reach a ≥5/≥3 quorum, or (d) fails → **INCONCLUSIVE** (disclosed;
  neither admit nor refute).
- Co-reported, non-binding: net **median** alongside the mean (EXP-089 mean-fragile signature); the RT/2 cost
  companion; `wrongside_frac` and the random arm's terminal mix (mechanism).

## Methodology risk & routing flag — RESOLVED by `D0-amendment-005` (2026-06-24)

The originally-frozen §4(c) null (SUB-RANDOM-entry RCT) is **biased toward admission**: the RCT target
`P*=Close+(AL−AG)` is signal-derived, so at random non-extreme bars it is wrong-side and the engine instant-fills
it (`xen/intrabar_fill.py:220`) — the random arm has no comparable favourable target regardless of whether the
real 4h edge is signal or oscillation, so real beats it even under pure oscillation harvesting. **Confirmed at
the engine level during Stage 3.** Operator-ratified resolution (`D0-amendment-005`): the **binding** §4(c) null
is now the **matched favourable-target-distance oscillation null** (Step (c) above) — the random arm gets a
favourable limit at a distance resampled from the real cell's `{μ_k}`, so the contrast tests the real EXP-089
worry. The SUB-RANDOM-entry RCT null (with wrong-side guard) is **retained as a disclosed companion**, never
gating.

## Implementation safety constraints (for `experiment-developer`)

- **TRAIN-only / holdout fence.** Read the TRAIN sub-split `[0, int(analysis_rows·0.7))` only; clip the 1m fill
  slice by **timestamp** at the TRAIN edge; never load the analysis-TEST or final-30% holdout. Assert
  `holdout_untouched`.
- **Real prices only.** All P&L/excursion on real OHLC (`RealOpen/High/Low/Close`, real 1m for fills); no
  HA/Renko prices in any metric. Cross-view alignment by `CloseTime`/`SourceCloseTime`, never bar index.
- **Determinism.** All seeds via `seed_for(EXP-094, …)`; second full pass (incl. the 1m walk, random-entry
  draws, direction shuffles, and both bootstraps) byte-identical; replay ≥2 cells; SHA-pin headline CSVs.
- **Denominators / zero-baseline.** Per-arm resolved-event denominators (finite gross, ATR>0, valid hold);
  paired Δ is a **difference of ATR-unit means**, compared to the absolute floor 0 (no ratio, no percentage vs
  a zero baseline). Report realized random `n` and any shortfall vs the matched target.
- **Binding matched-distance arm is favourable by construction** (static `entry_close + dir·m·ATR`, `m>0`
  resampled from real `{μ_k}`) ⇒ **no wrong-side / instant-fill regime** — the defect that sank the original
  null cannot occur in the binding test. **Wrong-side handling applies only to the SUB-RANDOM-entry companion**
  (`D0-amendment-005`): a non-favourable `P*` is NOT a favourable target → resolve via stop/cap only, never
  instant-fill; report `wrongside_frac`. Keep the companion strictly non-gating.
- **Bounded iteration / progress.** `tqdm` over the (≤13) member cells; `n_boot=10_000` fixed; no full-data
  collection before the holdout slice; bounded pandas only for the ≤4 plots (no heavy reloads for plotting).
- **No shared-state mutation.** Pass the Phase-021 `RT_i` / `fin_bps_day=0` into `event_costs`; do **not** edit
  `xen.capgeo_cost.COST_CONSTANTS` (Phase-018 integrity). Patch 4h into a **local** `DOMAINS` copy as `TEMP-091`
  did; do not mutate the imported EXP-090 module's globals beyond the documented `DOMAINS["4h"]=240` addition.
- **Safe performance (no result change).** (i) **Readiness cache** — leg (a) is deterministic in (EXP-090 code,
  source file, domain, seed); cache its output keyed by a content hash of exactly those inputs (any change ⇒
  miss ⇒ recompute; holdout never read either way). `--refresh-readiness` forces a clean recompute for the
  official record; `_cache_hit` provenance is recorded. (ii) **Bite-check power grid** computed by the EXACT
  identity `Δ_lo(null+g, null) = Δ_lo(null, null) + g` (adding a constant shifts every block-resample mean and
  percentile by g), so one same-distribution diff bootstrap per (replicate, cell) serves the FPR leg and the
  whole power grid. Both are byte-identical to the unoptimised computation; `n_boot`, block length, seeds,
  denominators, and the binding statistic are unchanged.

## Complexity Check

- **Statistical tests (binding):** 2 / ≤3 — (b) net-screen moving-block bootstrap; (c) paired-Δ two-sample
  moving-block bootstrap. *(Companions, non-binding: 1h positive control (d) — same statistic; RT/2 cost
  sensitivity; D0 bite-check (e) is calibration, not a market test.)*
- **Visualisations:** 4 / ≤4.
- **New modules:** 0–1 / ≤1 — at most one minimal two-sample moving-block **difference-of-means lower-bound**
  helper if `xen.ass` lacks one (check first; reuse `moving_block_bootstrap_cis` internals). Everything else
  (substrate, fill engine, cost, SUB-RANDOM generator, referee calibration) is reused verbatim.
