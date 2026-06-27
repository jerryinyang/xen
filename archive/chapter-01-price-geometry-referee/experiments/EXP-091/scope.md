# Experiment: EXP-091 — Phase 021 Exit / Capture-Geometry Screen (RSI-2 Fade, gross + EXP-085 cost, 20 member cells)

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 fade capture-geometry & tradability; checkpoint
`2026-06-23-021-mr-fade-capture-geometry`, **G0 RATIFIED 2026-06-23**, **D0 FROZEN**; `D0-amendment-001`
clarifications + `D0-amendment-002` EXP-090 confound fixes applied) · **Family:** **CF-MR-001 — bare RSI-2
mean-reversion fade (CORE)**, admitted at G-020 · **HYP:** `CF-MR-001/HYP-002` (tradability of the admitted
lever) · **Registry:** Phase 021 batch (`multiplicity-registry.md` §828–878); CF-MR-001 `ADMITTED (BINDING)`,
first candidate slot consumed at G-020 (`candidate-families/cf-mr-001.md`); the **exit families screened here
are registered countable items** (Phase 021 batch §847–854: EXIT-RCT, EXIT-ERT, RSI-revert-on-close, fixed-bar,
ATR triple-barrier, favourable partial/trail) · **Candidate slots:** 0 (the first slot was consumed at G-020;
Phase 021 consumes none) · **TEST reads:** 0 counted (TRAIN-sub-split only; no analysis-TEST stratum sliced, no
stratum-specific TEST inference — TRAIN-only disclosure per the ledger; all 48 strata stay 0/2 open).

**This is the TRAIN-only exit / capture-geometry screen (design §4 EXP-091 row).** It is the first Phase 021
experiment to **resolve the real bare-fade exit outcomes** (EXP-090 never read them — `real_fade_outcomes_
resolved=false`). It computes **gross and net (post-EXP-085-cost) per-event expectancy** for every frozen exit
arm on every member cell, applies the frozen D6 net-clear + quorum screen rule, and reports the native-vs-
contrast comparison. It is **not** a tradability/edge confirmation: the binding TEST read is EXP-093. It does
**not** select a final candidate set or fix a Holm rule (that is EXP-092), and it spends **no** counted TEST read.

---

## Signal-registry precondition (Stage-1 check — programme file-drawer control)

- **Family registered + admitted.** `CF-MR-001` is `ADMITTED (BINDING)` (G-020, 2026-06-23) in
  `candidate-families/cf-mr-001.md`; first candidate slot consumed; lever = the bare RSI-2 fade (CORE). Phase 021
  consumes **no additional slot**.
- **Countable items registered.** The six exit families this screen evaluates are all entered in the Phase 021
  multiplicity batch (`multiplicity-registry.md` §854, "Exit families (countable)") **before** measurement:
  **native pair** EXIT-RCT + EXIT-ERT (primary) and **conventional contrast** RSI-revert-on-close, fixed-bar,
  ATR triple-barrier (`1.0×ATR` tgt / `2.0×ATR` stop, time barrier = MR-tempo cap per `D0-amendment-001`),
  favourable partial/trail (EXP-059 V2A). Each is a **single frozen parameter point — no grid**. No new countable
  item is introduced by this scope; the EXP-090 two-leg partial/trail deferral lands here.
- **No TEST-stratum read.** EXP-091 reads only the **TRAIN sub-split** (`[0, train_cutoff)`,
  `train_cutoff = int(int(total_rows·0.7)·0.7)`; EXP-080/089/090 convention). The analysis-TEST stratum (last 30%
  of the analysis set) and the final-30% global holdout are **never sliced or materialized**. Current ledger
  tally for every stratum that *would* be read at EXP-093: **0/2 counted reads, open** (`test-read-ledger.md`
  Active Ledger, re-materialized 2026-06-21 on VAL-005 PASS). EXP-091 spends **0**.
- **No new selection statistic ⇒ no bite-check.** The binding gate is the frozen referee suite (D4); the screen
  statistic is the established net `ci_low_1s>0` moving-block bootstrap lower bound (EXP-046/056 quorum, EXP-085
  cost). No novel selection statistic is introduced (D0 header), so no bite-check is required.

## Gating preconditions (Stage-1)

- **EXP-090 `READINESS_CALIBRATION_DELIVERED`** (2026-06-24, audit PASS, amended `D0-amendment-002`). The
  **member set is the 20 EXP-090 MEMBER cells** (read-only from `EXP-090/results/member_map.csv`); the 12
  `COVERAGE_EXCLUDED` cells are not screened. Each member carries its EXP-090 per-(cell,arm) MDE — the **EXP-093
  margin** (RCT 0.0125 / ERT 0.025 ATR; downstream only, not used in the EXP-091 screen rule).
- **Frozen substrate.** The new `xen.intrabar_fill` engine (built + validated in EXP-090: fill-validity /
  timestamp-alignment / determinism TRUE on all 32 cells × 5 arms; resolution 0.991–1.000; tie-break ≤0.18%) is
  reused unchanged. The `D0-amendment-002` fixes (window anchoring to each bar's own `(close−period, close]`;
  gap-throughs fill at the touching 1m open) are inherited.
- **Cost model frozen.** The EXP-085 CONSERVATIVE round-trip (`2× BASE`) + per-instrument bar-count financing
  (`xen.capgeo_cost` / `xen.financing`), the per-instrument `(RT_i, F_i)` table inherited unchanged (D3). Costs
  are **not** re-estimated to suit the fade.

---

## Hypothesis / Falsifiable Question

**Primary (capture-geometry tradability screen, TRAIN-only, net of conservative cost):** over the frozen D2 exit
slate, evaluated on the 20 member cells under the EXP-085 conservative cost model —

1. **Does any exit net-clear the floor in a quorum?** An (exit × cell) **net-clears** iff its net (post-cost)
   per-event expectancy one-sided lower bound (`ci_low_1s`, `Z=1.645`, moving-block bootstrap) **> 0** (D6/4a).
   An **exit passes the screen** iff it net-clears in **≥ 5 cells over ≥ 3 instruments** (the EXP-046/056
   quorum). **Empty screen (no exit passes) ⇒ G-021 NOT_TRADABLE at 0 TEST reads** (the lever closes).
2. **Do the native intrabar targets beat the reactive contrast?** Descriptive attribution within the verdict
   (not a separate gate): does the native pair (EXIT-RCT / EXIT-ERT) net-clear more cells than the reactive arms
   — in particular **RCT vs RSI-revert-on-close**, the clean intrabar-resting-vs-exit-on-close A/B that isolates
   what proactive resting + intrabar fill buys?

**Honest prior (binding on interpretation, carried from the programme and the phase design §1):** *availability
≠ capturable edge.* The fade's gross favourable availability is small (`MFE_med`≈0.75 ATR) over a short ~3-bar
horizon, so conservative cost/slippage bite hardest exactly where the edge lives. This is a genuine falsification
attempt; an empty screen is an expected and fully-reportable outcome, not a defect. The verdict is read on the
realized per-stratum numbers (LESSON-001) — no pooled boolean is binding.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **{15m, 1h}**
  clock-aligned domain bars via the **holdout-fenced `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90`
  **plus** the VAL-005 G1 analysis-boundary fence — drop any window whose right-labelled `CloseTime` exceeds the
  last available TRAIN source bar). The **1-minute base series** is the intrabar fill source (D2.5), read **only
  within the TRAIN region** (clipped by timestamp at the TRAIN edge, never by 1m index). **No Heiken Ashi / Line
  Break / Renko** — real-OHLC indicator family; synthetic prices never enter any metric.
- **Entry — bare RSI-2 fade (CORE), inherited frozen (D1; NO re-tuning):** `RSI(2)` Wilder on domain `Close`;
  **long `RSI₂(t) < 10`**, **short `RSI₂(t) > 90`** (period 2, extremes 10/90). Favourable = long→up, short→down.
  CORE population only — `/VOLREGIME`, TREND, RSI-FILTER variants **NOT** carried (inert/dead at EXP-089,
  registered-but-deferred). Reuse `xen.mean_reversion.mean_reversion_entries(...)["CORE"]` unchanged.
- **Exit slate (frozen, D2 — all six arms SCREENED here).** Every arm shares the **same adverse side** (D2.3:
  stop `2.0×ATR(14)` from entry + the EXP-089 causal MR-tempo cap `mr_tempo_caps` (mult 1.0, FLOOR 3, MAX 40,
  EPISODE_WINDOW 20), exit-on-close at cap) and the **same 1m intrabar fill engine** (D2.5) — only the favourable
  leg varies ⇒ a win is attributable to the target, not the stop or hold window (EXP-057 isolation):
  - **Native (primary hypothesis):** **EXIT-RCT** — reversion-completion target
    `P*_t = Close_t + (AL_t − AG_t)` long / `Close_t − (AG_t − AL_t)` short, from the Wilder period-2 average
    gain/loss `(AG_t, AL_t)`, recomputed each domain bar after entry (trailing limit, 1m intrabar fill).
    **EXIT-ERT** — equilibrium-return target `M_t = wilder_ema(Close, 10)`, recomputed each domain bar (trailing
    limit, 1m intrabar fill).
  - **Conventional contrast (tested, not expected to dominate):** **RSI-revert-on-close** (exit at the domain
    close when RSI₂ crosses 50 — the reactive, non-intrabar analog of RCT); **fixed-bar** (close at the MR-tempo
    cap horizon, `xen.exit_rules.fixed_horizon_exit_idx`); **ATR triple-barrier** (`1.0×ATR` favourable /
    `2.0×ATR` adverse, intrabar-filled via the same engine, time barrier = the same MR-tempo cap per
    `D0-amendment-001`); **favourable partial/trail** (EXP-059 V2A-style two-leg,
    `xen.capgeo_cost.partial_two_leg_exit`, as the primitive allows).
  - **Single frozen parameter point per arm — no grid** (multiplicity discipline).
- **Cost model (binding, D3):** the EXP-085 CONSERVATIVE model applied unchanged to every resolved exit path —
  round-trip transaction = `2× BASE` + per-instrument adverse-side **financing bps/day** on realized holding
  duration (`holding_days`, `event_costs` in `xen.capgeo_cost` / `xen.financing`). **Net = gross − cost** in ATR
  units. A **faster-turnover round-trip sensitivity** is a disclosed companion (D3), **not** a re-estimation of
  the binding model and **not** a screen input.
- **Binding gate (D4):** the **frozen qualification suite** — strict gate stack + EXP-012 ratified-loose referee
  + EXP-018 revised incremental/fitness unit (`xen.incremental_referee`, `xen.referee_calibration`) — remains the
  binding tradability gate, exactly as it stayed binding for Phase 018 after G-017 `DISCOVERY_ONLY`. The screen's
  advancement figure is the **net per-event expectancy moving-block bootstrap lower bound** (the established
  EXP-046/056 quorum statistic over that suite's net endpoint). The **`ASS` qualifier is NON-BINDING discovery
  overlay only** (G-017) — may be reported, never gates. **No referee is built or tuned.**
- **Member set / grid:** the **20 EXP-090 MEMBER cells** (10 × 15m + 10 × 1h), read from
  `EXP-090/results/member_map.csv`. **15m (10):** GBPUSD, USDJPY, USDCHF, AUDUSD, GBPJPY, AUDJPY, XAUUSD, USTEC,
  US2000, JP225. **1h (10):** EURUSD, GBPUSD, USDJPY, USDCHF, NZDUSD, EURJPY, GBPJPY, AUDJPY, USTEC, US2000.
  **13 distinct instruments** represented (the ≥3-instrument quorum is well-supported). The 12
  `COVERAGE_EXCLUDED` cells are **not** screened. **4h not carried** (dead-by-absence at EXP-089).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows·0.7)`, `analysis_rows = int(total_rows·0.7)`) — the nested TRAIN sub-split.
  The analysis-TEST stratum is **not** sliced; no strategy inference on it ⇒ **0 counted TEST reads**.
- **Global holdout:** the final 30% of each file is **never** loaded, inspected, counted, plotted, or used
  (including its 1m bars). Only Parquet **metadata** (`scan.select(pl.len())`) locates the split. The holdout
  fence (no domain-bar label and no intrabar-fill 1m bar crosses the TRAIN edge) is a checked invariant.
- **Look-ahead bias prevention:** domain aggregation emits completed windows only; RSI(2)/EMA(10)/ATR(14) and the
  MR-tempo cap are sequential/causal (bars `≤ i`); RCT uses the Wilder `(AG_t, AL_t)` state through bar *t* only;
  ERT uses EMA-10 through bar *t* only; both recompute each domain bar after entry with no future bar. The 1m
  intrabar fill walks 1-minute bars **forward from entry in chronological order**, timestamp-mapped to the domain
  bar (never bar index), with the **conservative adverse-first tie-break** when both barriers lie in one 1m bar;
  fill price = the target/stop **level** (a real touched price ∈ `[Low,High]`, or the gap-through 1m **open** per
  `D0-amendment-002`), never the 1m close, never synthetic. All ordering uses `CloseTime`/`SourceCloseTime`.
- **Real-price discipline (binding):** every excursion, fill, stop, ATR, cost, and expectancy figure is on
  **real** OHLC (`RealOpen/High/Low/Close`; real 1m OHLC for fills). No HA/Renko synthetic-price metric anywhere.
- **Exclusions:** no candidate set or Holm rule, no `SEQUENCE_PASS` adjudication (EXP-092); no TEST read or
  holdout contact (EXP-093); no `/VOLREGIME`, TREND, RSI-FILTER, contrarian, 25/75, regime×variant, or 4h
  expansion (registered-but-deferred — each needs its own `D0-amendment-*`); no parameter sweep or tuning of any
  frozen constant (RSI 2/10/90, ERT EMA-10, adverse 2.0×ATR, MR-tempo cap, ATR-barrier 1.0/2.0×ATR, EXP-085 cost
  table, the D6 thresholds); no cross-instrument/cross-domain pooling as a binding statistic (per-stratum,
  LESSON-001 — any pooled figure is disclosure only); nothing tuned or frozen against any EXP-091 output. The
  EXP-093 margin (EXP-090 MDE) is **carried, not applied** here.

## Screen Procedure (the measurement)

Per member cell, per exit arm (single 20-cell outer loop; `tqdm`):

1. **Resolve real exit outcomes.** Build CORE fade entries (reuse `mean_reversion_entries`), then resolve each
   frozen arm per event through `xen.intrabar_fill` to a terminal (favourable fill / adverse stop / cap-close),
   causal and TRAIN-edge-clipped. Record per-event **gross** signed real-price return in ATR(14) units, realized
   hold (bars + `holding_days`), fill/stop/cap terminal type, MAE/`q05` adverse tail, favourable-capture fraction,
   and tie-break incidence. (This is the first read of the real fade outcomes in Phase 021.)
2. **Apply EXP-085 cost.** Subtract the conservative round-trip + financing cost per event (`xen.capgeo_cost`) →
   per-event **net** return in ATR units. Gross is retained for the descriptive sanity readout.
3. **Net-clear test (binding figure).** Compute the net per-event expectancy **moving-block bootstrap one-sided
   lower bound** (`ci_low_1s`, `Z=1.645`). The (exit × cell) **net-clears** iff `ci_low_1s > 0` (D6/4a). Co-report
   the gross `ci_low_1s` (descriptive) and the net + gross **median** expectancy (the family is median-positive /
   mean-fragile per EXP-089 — both legs disclosed, never pooled across cells).
4. **Quorum.** Per exit arm: count net-clearing cells and the distinct instruments among them. An exit **passes**
   iff net-clears in **≥ 5 cells over ≥ 3 instruments**.
5. **Native-vs-contrast attribution (descriptive).** Tabulate net-clear counts per arm; compare the native pair
   (RCT/ERT) against the reactive contrast, with the **RCT vs RSI-revert-on-close** A/B called out explicitly
   (per-cell paired net-expectancy delta, disclosure only).
6. **Determinism.** A full second regeneration of every cell's entries, the complete 1m exit resolution for all
   arms, the cost overlay, and the bootstrap stream (fixed seed) compares **frame-identical** (exact) to the first
   pass; headline outputs SHA-256 hash-pinned.
7. **Faster-turnover cost sensitivity (disclosed companion, non-binding):** re-evaluate net `ci_low_1s` and the
   quorum under a predeclared faster round-trip variant (fixed in Stage 2); reported alongside the binding result,
   never substituted for it.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Per-event gross/net return** = signed `dir·(fill_price − entry_price)/ATR_entry` in ATR(14) units, real OHLC;
  per-cell expectancy denominator = the cell's resolved member events (never a bar count). A cell with 0 resolved
  events for an arm reports that arm `UNRESOLVED_EMPTY` with its denominator, never `0/0`.
- **Net `ci_low_1s`** denominator = reportable matched events entering the moving-block bootstrap for that
  (cell × arm); block length per the EXP-044 `round(n**(1/3))` convention.
- **Net-clear** is the boolean `net ci_low_1s > 0` — an absolute ATR-unit threshold at exactly **0**, never a
  percentage improvement against a zero/near-zero baseline (governance prohibition).
- **Quorum** = (# net-clearing cells, # distinct instruments among them) per exit, vs the fixed `≥5 / ≥3` rule;
  both denominators (20 member cells, 13 instruments) disclosed.
- **Cost** = ATR-unit location shift per event (transaction + financing on `holding_days`); reported per cell ×
  arm with the gross→net decomposition, never as a ratio.
- **Tie-break incidence** = (events whose terminal 1m bar contained both barriers) / resolved events, per arm.
- **Resolution rate** = resolved events / member events, per arm; an unresolved event (no fill/stop before the
  cap, then exit-on-close fallback) is itself recorded with its denominator, never silently dropped.
- All effects reported as ATR-unit differences with CIs. **No ratios against zero baselines anywhere.**

## Frozen Constants (predeclared at D0/G0; recorded here pre-data-contact)

- **Entry:** `RSI(2)` Wilder, extremes 10/90 (CORE only). Not varied.
- **Native exit targets:** RCT from the Wilder period-2 `(AG_t, AL_t)`; ERT `M_t = wilder_ema(Close, 10)`. Not
  varied.
- **Adverse side (all arms):** stop `2.0×ATR(14)`; max-hold = the EXP-089 MR-tempo cap (mult 1.0, FLOOR 3,
  MAX 40, EPISODE_WINDOW 20), exit-on-close at cap. ATR-barrier favourable `1.0×ATR`, time barrier = the same cap.
- **ATR:** Wilder ATR period **14**. All distances in ATR(14) units.
- **Cost:** EXP-085 CONSERVATIVE round-trip = `2× BASE` + per-instrument financing bps/day, inherited unchanged.
- **Screen rule (D6/4a):** net-clear iff net `ci_low_1s > 0` (`Z=1.645`, moving-block bootstrap); exit passes iff
  net-clears in **≥5 cells / ≥3 instruments**. Empty ⇒ G-021 NOT_TRADABLE at 0 reads.
- **Seeds:** master seed `20260623`; per-cell/per-arm bootstrap seed = deterministic hash of `(cell, arm,
  replicate)`; recorded in `run_metadata.json`; a second full pass (incl. the 1m walk + bootstrap) is
  byte-identical (D9).
- **Domain construction:** `build_domain_bars`, `min_coverage=0.90` + TRAIN-edge boundary fence.

## Success / Failure / Inconclusive Criteria

- **Exit PASSES the screen:** net-clears (`net ci_low_1s > 0`) in **≥5 cells over ≥3 instruments**. The surviving
  exit(s) and their net-clearing cells carry to EXP-092 (the per-instrument sequence + hash-pinned candidate set).
- **Exit FAILS the screen:** net-clears in fewer than the quorum. Recorded in the file drawer; not silently
  reopened by re-parameterization.
- **Empty screen (no exit passes) ⇒ deliverable `SCREEN_EMPTY` → routes G-021 NOT_TRADABLE at 0 TEST reads** —
  the capture lever is empty; the fade's availability does not convert to a net edge on this dataset (design §6).
- **Experiment verdict — `SCREEN_DELIVERED`:** the per-(cell × arm) gross + net expectancy + net `ci_low_1s`
  table, the per-arm quorum tally, the native-vs-contrast attribution (incl. RCT vs RSI-revert-on-close), the
  cost decomposition + faster-turnover companion, the tie-break/resolution tables, and the determinism replay are
  produced — whatever the mix of passing/failing exits (deliverable criterion; success is the honest map).
- **Cell-level INCONCLUSIVE:** a (cell × arm) whose net `ci_low_1s` spans zero is simply not a net-clear (counted
  as such); a cell whose realized resolved-event count is too thin for a stable bootstrap is disclosed
  power-limited (the EXP-090 finite-MDE membership already bounds this) — neither inflates nor blocks the quorum.
- **Evidence AGAINST (process-level — HALT):** any timestamp-vs-index misalignment, look-ahead, holdout-fence
  breach, non-determinism, fill price outside `[Low,High]` (the EXP-090 D2.5 invariant), or real-price-discipline
  violation in the 1m engine / cost overlay → halts pending a fix (dated `D0-amendment-*` + hard-delete + full
  rerun if a frozen-design confound, programme norm — as for EXP-090).

## Complexity Budget (design §5: EXP-091 ≤ 2 binding tests, ≤ 4 plots, target 1–2 new modules)

- **Binding statistical tests: ≤ 2** — (i) the net `ci_low_1s` moving-block bootstrap lower bound (the binding
  net-clear figure); (ii) the native-vs-contrast paired per-cell comparison is descriptive attribution, not a
  separate gate. No new selection statistic ⇒ no bite-check.
- **Visualisations: ≤ 4** — (i) per-arm net-clear quorum bar (cells / instruments vs the ≥5/≥3 rule); (ii)
  per-(cell × arm) net `ci_low_1s` heatmap (20 cells × 6 arms) with the 0 line marked; (iii) gross→net cost
  decomposition per arm; (iv) RCT vs RSI-revert-on-close paired net-expectancy scatter (the intrabar-vs-on-close
  A/B). All from the single analysis pass's bounded plot inputs (no reloads).
- **New code modules: target 0–1.** **Reuse unchanged:** `xen.intrabar_fill` (EXP-090 engine), `xen.mean_
  reversion` (CORE entries, `mr_tempo_caps`, `wilder_rsi`, `wilder_ema`, `wilder_avg_gain_loss`),
  `xen.domain_bars`, `xen.exit_rules` / `xen.position_exits` / `xen.capture_barriers` / `xen.capgeo_cost`
  (`partial_two_leg_exit`, cost) / `xen.financing`, `xen.expectancy`, the frozen referee
  (`xen.incremental_referee`, `xen.referee_calibration`), and the moving-block bootstrap (`xen.ass` / EXP-090
  estimator). At most one small screen-orchestration helper if a clean reuse is not available; **no edits to
  frozen entry/exit/cost generators; no new referee.**

## Data Requirements

Per instrument (member cells only): lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total
row count from metadata; `analysis_rows = int(total_rows·0.7)`; `train_cutoff = int(analysis_rows·0.7)`; collect
only the first `train_cutoff` file-order 1-minute rows (assert sorted by `CloseTime`); set the TRAIN-edge
timestamp; build {15m,1h} domain bars via `build_domain_bars` (fence drops boundary-crossing windows); compute
RSI(2)/EMA(10)/ATR(14) and the MR-tempo cap on real OHLC (causal); derive CORE fade entries; resolve every frozen
arm per event via `xen.intrabar_fill` (timestamp-mapped, causal, TRAIN-edge-clipped); compute gross + EXP-085-net
per-event ATR returns; run the moving-block net `ci_low_1s` per (cell × arm); apply the quorum; run the bounded
determinism second pass. **Read-only upstream artifact:** `python/experiments/EXP-090/results/member_map.csv`
(dependency gate: the 20-cell member set + per-arm margins; hard-fail if missing or if EXP-090 `run_metadata.json`
does not record `READINESS_CALIBRATION_DELIVERED`).

**Outputs:**
```text
python/experiments/EXP-091/results/
- screen_per_cell_arm.csv      # per (cell × arm): n_events, resolution rate, tie-break incidence, gross/net
                               #   mean+median expectancy, gross/net ci_low_1s, net-clear bool, terminal-type mix
- quorum_per_arm.csv           # per arm: net-clearing cell count, distinct-instrument count, PASS/FAIL vs ≥5/≥3
- native_vs_contrast.csv       # per-cell paired net deltas (RCT−RSI-revert-on-close et al.); attribution summary
- cost_decomposition.csv       # per (cell × arm): gross→net, transaction vs financing, holding_days
- cost_sensitivity_faster.csv  # disclosed companion: net ci_low_1s + quorum under the faster round-trip variant
- run_metadata.json            # status, verdict (SCREEN_DELIVERED + per-arm PASS/FAIL; SCREEN_EMPTY if none),
                               #   determinism, EXP-090 dependency gate, seeds/hashes, module versions,
                               #   holdout_untouched=true, counted_test_reads=0, candidate_slots=0
python/experiments/EXP-091/plots/   # ≤4 per the budget
```
`tqdm` over the 20-cell outer loop; per-cell memory bounded (do not retain all domain frames simultaneously).
Expected runtime: minutes–tens-of-minutes (the per-(cell × arm) bootstrap is the main cost — prefer vectorized
draw batching over cutting draw counts below stability).

## Suggested Direction (non-binding)

Mirror EXP-090's 20-cell loop and reuse its `xen.intrabar_fill` resolution path verbatim, but now (a) read the
**real** per-event gross return off each resolved terminal, (b) overlay the EXP-085 cost to get net, (c) compute
the net `ci_low_1s` per (cell × arm) and apply the `≥5/≥3` quorum, and (d) tabulate the native-vs-contrast
attribution. Everything per-stratum (LESSON-001); any pooled figure is disclosure only. An empty screen is a
complete, honest deliverable that routes G-021 NOT_TRADABLE without spending a TEST read.
