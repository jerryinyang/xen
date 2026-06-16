# Analysis Plan: Experiment EXP-052

**Phase 014-A · HYP-005 · `CF-HA-HARAMI-001/CONFIRM` · characterisation (0 candidate
slots, 0 TEST reads) · gross · TRAIN-only · 99 EXP-048-READY cells.**

This plan operationalises `scope.md` without adding scope. Every constant (P1 ATR
14/1.0, P2 favourable fraction 0.50, P4 cap `max(6, round(1.5×median(trailing-20
durations)))` with the `<5`-move warmup, P5 LOOKBACK=1, power floor 30, MBB
`N_BOOT=10_000`) is D0-/operator-frozen and treated here as a fixed constant, never
tuned. HYP-005 has **no viability gate**: the experiment delivers descriptive
frequency/timing/outcome distributions for the two entry arms and a single
**non-binding** comparison readout. No selection, no routing, no slot, no branch
registration.

## Objective

For each EXP-048-READY cell (instrument × domain), on the population of HA harami
signals, measure and compare the **direct** entry (at the harami signal bar) and the
**signal+confirmation** (`/CONFIRM` stop-order) entry along three descriptive axes —
**frequency** (fill rate), **timing** (lead in bars over the ZigZag trend-change
confirmation), and **subsequent outcome distribution** (direction-signed MFE/MAE on
real prices, ATR-normalized, primary; symmetric fav-before-adv `r` reusing
`xen.capture_barriers`, secondary/disclosed) — and emit a predeclared **non-binding**
paired CONFIRM−DIRECT shift readout with a P11-style composition count. Deliver the
per-cell tables and the disclosed warmup/censoring breakdowns whatever the
helps/hurts/flat mix. The experiment emits the readout; it self-adjudicates nothing.

## Unit of analysis, event set, and per-cell denominators

- **Unit:** one HA harami event from `xen.ha_harami.detect_ha_harami` on the cell's
  HA candles, mapped to its real domain-bar index `s` by exact `CloseTime` match,
  ordered by `HA0Time` (the causal clock for this experiment).
- **Confirmed-move context:** `xen.zigzag.generate_zigzag(bars, atr_period=14,
  atr_mult=1.0)` (P1, frozen) on the cell's real domain OHLC (TRAIN-fenced) supplies
  `StartTime/EndTime/ConfirmTime/Direction/StartPrice/EndPrice` per confirmed move,
  ordered by `ConfirmTime`.
- **Reversal direction (causal):** `rd = Direction(most recent move with ConfirmTime
  ≤ HA0Time)`, found by `searchsorted` on the move `ConfirmTime` array (right side,
  then `−1`). Derivation in `scope.md` §"Reversal-direction assignment":
  `rd = +1` ⇒ bullish reversal (buy-stop), `rd = -1` ⇒ bearish (sell-stop). A harami
  with **no** confirmed move at/before `HA0Time` → `NO_TREND_CONTEXT` (excluded,
  disclosed).
- **Per-event P4 cap (causal):** `N_event = max(6, round(1.5 × median(durations of
  the up-to-20 confirmed moves at or before HA0Time — i.e. through the reference move
  `j`, inclusive; every such duration is realized at a `ConfirmTime ≤ HA0Time`, so it
  is causal)))`, durations =
  `diff(ConfirmTime indices)` (reuse the `THIRD_BARRIER_*` constants from
  `xen.capture_barriers`). `< 5` trailing confirmed moves ⇒ `P4_WARMUP` (no defined
  cap → excluded, disclosed). Frozen at the signal bar; **identical `N_event` for both
  arms** (the cap is a property of the harami, not of the entry bar).
- **Qualifying-harami set `n_signals` (common DIRECT denominator):** haramis with
  defined `rd`, defined `N_event`, and a **non-censored DIRECT outcome window**
  (`s + N_event ≤ n_bars − 1`). `NO_TREND_CONTEXT`, `P4_WARMUP`, and
  `DIRECT_DATA_CENSORED` counts are excluded and disclosed separately, never silently
  defaulted.
- **`n_fills` (CONFIRM subset ⊆ `n_signals`):** qualifying haramis whose stop
  triggered inside the validity window (below). CONFIRM outcome may be independently
  censored (`CONFIRM_DATA_CENSORED`, see Step 4).

## Methodology

### Step 1 — Reversal direction, DIRECT entry, P4 cap (causal)

- **Method:** per harami, `searchsorted(ConfirmTime, HA0Time, side="right") − 1` →
  index of the most recent confirmed move; `rd = Direction[that]`. DIRECT entry bar
  `e_d = s`, entry price `p_d = RealClose[s]`. Compute `N_event` from the trailing-20
  confirmed-move durations (moves with index ≤ that move index).
- **Why sufficient / simpler alternative:** the assignment is a direct read of the
  frozen ZigZag state; a re-derivation of trend from raw bars was rejected (the
  generator is the single source of truth and is already validated).
- **Assumptions:** none distributional; relies only on the causal ZigZag ordering
  (`ConfirmTime` strictly later than the pivot it confirms).
- **Output:** per harami: `rd`, `s`, `p_d`, `N_event`, status ∈
  `{OK, NO_TREND_CONTEXT, P4_WARMUP}`.

### Step 2 — CONFIRM stop level, validity window, causal fill scan

- **Method:** stop level `p_c = RealHigh[s]` if `rd=+1` else `RealLow[s]`. Window end
  `window_end = min(next_confirm_idx − 1, s + N_event)`, where `next_confirm_idx` =
  index of the first `ConfirmTime` **strictly after** `HA0Time` (searchsorted; if none
  in TRAIN, `next_confirm_idx = +∞` → bounded by `s + N_event`). **Explicit causal
  first-touch scan** over `i ∈ (s, window_end]`: trigger at the first `i` with
  `High[i] ≥ p_c` (`rd=+1`) or `Low[i] ≤ p_c` (`rd=-1`); `trigger_idx = i`,
  CONFIRM entry `e_c = i`, entry price `= p_c` (gross, no slippage). No trigger ⇒
  `NO_FILL`.
- **Why an explicit loop (not vectorised):** first-touch is genuinely sequential
  (the answer is the *first* crossing); keep it a bounded explicit scan, exactly as
  `xen.capture_barriers._scan_window` does. Window length ≤ `N_event` (bounded).
- **Look-ahead discipline:** the stop level is the signal bar's own real extreme
  (known at `s`); each scanned bar's High/Low is used only at that bar.
  `next_confirm_idx` is a forward reference used **only** to bound a descriptive
  window (declared completed-move allowance, §"Look-ahead/Causality") and is itself
  capped by the strictly-causal `s + N_event`.
- **Output:** per harami: `fill ∈ {FILL, NO_FILL}`, `trigger_idx` (if FILL),
  `next_confirm_idx`, `window_end`.

### Step 3 — Frequency (fill rate) and timing (lead)

- **Frequency:** per cell `n_signals`, `n_fills`, `fill_rate = n_fills / n_signals`
  (`n_fills = 0 ⇒ fill_rate = 0`, never `0/0`).
- **Timing (descriptive distributions over the relevant event set):**
  `lead_direct = next_confirm_idx − s` (over qualifying haramis with a defined
  `next_confirm_idx`); `lead_confirm = next_confirm_idx − trigger_idx` and
  `time_to_fill = trigger_idx − s` (over fills). Report per-cell median + IQR of each;
  haramis with no in-TRAIN subsequent confirmation have undefined `lead_*` (excluded
  from the lead summary, disclosed count).
- **Method/assumptions:** descriptive summary statistics (methods-catalog
  "Descriptive Methods, always include"); no distributional assumption. Invariant
  checks (Step 7) enforce `lead_confirm ≥ 1`, `lead_direct ≥ 1`,
  `lead_confirm ≤ lead_direct` on every fill.

### Step 4 — Outcome distribution: direction-signed MFE/MAE (PRIMARY)

- **Method:** for each arm's entry `(e, p)` (DIRECT `e_d=s, p_d`; CONFIRM `e_c, p_c`)
  over the bounded forward window `[e+1, e+N_event]` (same `N_event`; fenced to
  `n_bars−1`): favourable excursion at bar `i` = `RealHigh[i] − p` if `rd=+1` else
  `p − RealLow[i]`; adverse = the opposite side. `MFE = max(0, max_i favourable)`,
  `MAE = max(0, max_i adverse)`. **ATR-normalize:** `MFE_atr = MFE / ATR[e]`,
  `MAE_atr = MAE / ATR[e]` (Wilder ATR-14 at the entry bar; `ATR[e] > 0` guaranteed by
  warmup). Raw price and bps (`/p × 1e4`) disclosed.
- **Censoring:** an arm whose `[e+1, e+N_event]` window exceeds `n_bars−1` is
  `*_DATA_CENSORED` (excluded from that arm's outcome distribution, disclosed).
  DIRECT censoring is already excluded by the `n_signals` definition; CONFIRM is
  censored independently (its later anchor `e_c`).
- **Per-cell statistics, per arm:** median and IQR of `MFE_atr`, `MAE_atr`, and the
  paired-per-event `MFE−MAE` (`= (MFE−MAE)/ATR[e]`); also `median(MFE_atr)`,
  `median(MAE_atr)`. **Reportable** iff the arm's non-censored event count `≥ 30`
  (DIRECT uses `n_signals`; CONFIRM uses non-censored `n_fills`); else
  `NOT_REPORTABLE_BY_POWER`.
- **Why MFE/MAE (not a barrier hit) as primary:** it characterises the *full
  excursion shape* of each arm's reversal trade without committing to a barrier
  target (target geometry is 014-B); ATR-normalization makes it scale-free within and
  comparable across cells. Simpler alternative (fixed-horizon signed return at one
  horizon) rejected — it collapses the favourable-vs-adverse asymmetry that is the
  point of comparing the two arms.
- **Assumptions:** none distributional (medians/IQR are rank-based). Serial dependence
  of excursions is expected and is why Step 6's CI uses a block bootstrap.

### Step 5 — Outcome distribution: symmetric fav-before-adv `r` (SECONDARY, disclosed)

- **Method:** reuse `xen.capture_barriers` unchanged. For each arm, build symmetric
  1:1 targets from entry `(e, p)`: favourable distance `fav_dist = 0.50 × |EndPrice −
  StartPrice|` of the LOOKBACK=1 preceding confirmed move (the same move that set
  `rd`; magnitude known at `s`), adverse distance equal, opposite side
  (`fav_target = p + rd·fav_dist`, `adv_target = p − rd·fav_dist`). Resolve via
  `resolve_first_touch(High, Low, confirm_idx=e_array, fav_target, adv_target, rd,
  n_event=N_event_array, defined, n_bars)`; tally with `summarize_geometry` and the
  regime-clustered `block_bootstrap_ci` (clustering unit = event in `HA0Time` order).
  Report per arm: `fav, adv, timecap, censored, resolved, r = fav/(fav+adv)`,
  `ci_low_1s/ci_lo_2s/ci_hi_2s`. Degenerate (`magnitude = 0`) excluded.
- **Power / zero-baseline:** `resolved < 30` (`RESOLVED_FLOOR`) ⇒ `r`
  NOT_REPORTABLE_BY_POWER (null, never `0/0`). Symmetric-barrier null `r = 0.50`
  (`NULL_R`) is the descriptive reference — directly comparable to EXP-049 G1
  (`r ≈ 0.50` on the ZigZag-confirmation anchor).
- **Why disclosed only:** it imposes a specific barrier target (a 014-B object); kept
  as colour comparable to EXP-049, never the binding endpoint. The binding descriptive
  outcome is the target-free MFE/MAE of Step 4.

### Step 6 — Statistical method 1: MBB CIs on per-arm outcome statistics

- **Question:** how much sampling uncertainty surrounds each arm's per-cell outcome
  point estimate? **Method:** moving-block bootstrap over the `HA0Time`-ordered
  sequence of the arm's non-censored events, block length `L = max(1,
  round(n**(1/3)))`, `B = 10_000`, **fixed seed** (recorded). Applied to: (a) per-arm
  `median(MFE−MAE)_atr` [primary] — resample `(MFE−MAE)_atr` tuples in contiguous
  blocks, recompute the median, CI = (2.5, 97.5) pct; (b) per-arm secondary `r` —
  exactly `xen.capture_barriers.block_bootstrap_ci` (reused, not reimplemented).
- **Why block (not iid) bootstrap:** excursions/outcomes are serially dependent
  (volatility clustering); an iid bootstrap understates uncertainty. A rank test
  (Mann-Whitney) would answer a different question and risk goalpost drift — rejected.
- **Assumptions:** approximate within-block stationarity; reported as colour, never a
  gate. Computed only for reportable arms. Determinism: fixed seed/`B`/`L`/percentile
  method ⇒ bit-identical CI across the two passes.

### Step 7 — Statistical method 2: paired CONFIRM−DIRECT shift readout (NON-BINDING)

- **Paired set:** events that are **FILL and non-censored in both arms** (CONFIRM
  fills are a subset of DIRECT events; intersect with CONFIRM-non-censored). Per cell,
  the **primary** paired statistic is `Δ = median((MFE−MAE)_atr | CONFIRM entry) −
  median((MFE−MAE)_atr | DIRECT entry)` over this paired set (each event contributes
  both its DIRECT and CONFIRM excursion, measured from its own entry).
- **CI:** moving-block bootstrap over the `HA0Time`-ordered paired-event sequence
  (same `L`-rule, `B = 10_000`, fixed seed); resample event-blocks, recompute Δ.
  Flags: `positive_shift` iff `CI_low > 0`; `negative_shift` iff `CI_high < 0`;
  else `flat`. **Disclosed parallel:** the same paired Δ on the secondary `r`
  (events resolved in both arms) — colour, not the primary readout.
- **Reportable** iff the paired set has `≥ 30` events; else
  `NOT_REPORTABLE_BY_POWER` (excluded from the §8 composition count).
- **Why paired:** the two arms share the same underlying haramis; pairing removes
  cross-event variance and isolates the entry-interpretation effect. This is the
  Wilcoxon-signed-rank setting (paired, methods-catalog), realised here as a
  block-bootstrap CI on the paired median difference to respect serial dependence.

### Step 8 — P11 composition + cross-cell consistency (non-binding readout)

- **Composition (descriptive):** `n_pos` = # reportable cells with `positive_shift`;
  `n_pos_instruments` = # distinct instruments among them; the descriptive statement
  "confirmation improves the outcome distribution" *as a readout* holds iff
  `n_pos ≥ 5 ∧ n_pos_instruments ≥ 3` (P11 convention). The symmetric
  `negative_shift` composition is reported in parallel. **This selects nothing and
  routes nothing.**
- **Cross-cell consistency (descriptive, no test):** distributions across reportable
  cells of `fill_rate`, `lead_direct`/`lead_confirm` medians, per-arm
  `median(MFE−MAE)_atr`, and Δ (median, IQR, min, max); per-domain breakdown of the
  shift sign. Describes robustness; not a gate.

### Step 9 — Determinism replay + invariant battery

- **Determinism:** run the entire per-cell pipeline a second time (re-aggregate,
  re-HA, re-detect harami, re-ZigZag, re-assign `rd`/`N_event`, re-scan fills,
  re-measure MFE/MAE, re-resolve barriers, re-bootstrap with the same seed) and assert
  the full `per_cell_confirm` frame is **frame-identical** (`pl.DataFrame.equals`;
  all integer counts and float stats/CIs bit-identical). Any mismatch on any cell ⇒
  `CHARACTERISATION_REFUTED`.
- **Invariant battery (scope §Readiness; counts must be 0 unless a disclosed
  exclusion):** (1) event well-formedness (every qualifying harami has a defined
  DIRECT entry and a CONFIRM `{FILL with trigger ∈ (s, window_end], NO_FILL}`
  decision; `n_fills ⊆ n_signals`; exclusion trichotomy exhaustive); (2) stop/fill
  validity (`High[trigger] ≥ p_c` / `Low[trigger] ≤ p_c` exactly; `s < trigger_idx ≤
  window_end`; `1 ≤ lead_confirm ≤ lead_direct`); (3) MFE/MAE validity (`MFE,MAE ≥ 0`
  finite; `ATR[e] > 0`); (4) causality/TRAIN-fence (every `ConfirmTime`, `HA0Time`,
  `trigger_idx`, forward-window bar `CloseTime ≤ train_end_ts`). A battery item (1–4)
  breached on **≥ 3 instruments**, or any non-determinism, ⇒ `CHARACTERISATION_REFUTED`.

## Visualisations (4 / 4 — bounded inputs from the analysis pass, no reloads)

1. **`fill_rate` heatmap** — 17 instruments × 6 domains, colour = `fill_rate`;
   NOT_REPORTABLE / COVERAGE_EXCLUDED greyed/annotated. *Answers frequency (b).*
2. **Lead-time distribution, DIRECT vs CONFIRM** — paired box/violin of `lead_direct`
   and `lead_confirm` (and `time_to_fill`), pooled with a per-domain small-multiple.
   *Answers timing (c): how much lead confirmation costs.*
3. **Per-arm MFE/MAE outcome summary** — box/violin of `MFE_atr` and `MAE_atr` by arm
   (DIRECT | CONFIRM), pooled with the symmetric-`r` reference annotated. *Answers
   outcome (d/e).*
4. **Paired-Δ shift vs fill-rate scatter** — per reportable cell, x = `fill_rate`,
   y = paired `Δ median(MFE−MAE)_atr` with CI whiskers; zero line and the P11
   composition tally in the title; point shape by shift sign. *Answers comparison (f).*

All other forms (raw/bps outcomes, secondary `r` table, censoring/warmup fractions,
position-in-move secondary if computed) go to CSV/JSON, not plots.

## Output tables

- `per_cell_confirm.parquet` — one row per (instrument, domain): `n_haramis_total,
  n_no_trend_context, n_p4_warmup, n_signals, n_fills, fill_rate,
  n_direct_censored, n_confirm_censored, lead_direct_med, lead_direct_iqr,
  lead_confirm_med, lead_confirm_iqr, time_to_fill_med, direct_mfe_atr_med,
  direct_mae_atr_med, direct_mmm_med (median MFE−MAE), confirm_mfe_atr_med,
  confirm_mae_atr_med, confirm_mmm_med, direct_mmm_ci_low/high,
  confirm_mmm_ci_low/high, paired_delta_mmm, paired_delta_ci_low/high, shift_sign,
  direct_reportable, confirm_reportable, paired_reportable, both_pass, status`.
- `outcome_primary.csv` — per arm: `mfe_atr_med, mfe_atr_iqr, mae_atr_med,
  mae_atr_iqr, mmm_med, mmm_ci_low, mmm_ci_high, n_used, reportable`.
- `outcome_secondary_r.csv` — per arm: `fav, adv, timecap, censored, resolved, r,
  ci_low_1s, ci_lo_2s, ci_hi_2s, reportable` (EXP-049-comparable).
- `timing.csv` — `lead_direct_{med,iqr}, lead_confirm_{med,iqr}, time_to_fill_{med,iqr},
  n_lead_defined`.
- `comparison_readout.csv` — `paired_delta_mmm, ci_low, ci_high, shift_sign,
  paired_delta_r (disclosed), n_paired, paired_reportable`.
- `excluded_fractions.csv` — `n_haramis_total, n_no_trend_context, n_p4_warmup,
  n_direct_censored, n_confirm_censored, n_degenerate_ref`.
- `composition_readout.json` — `n_reportable, n_pos, n_pos_instruments,
  p11_pos_readout, n_neg, n_neg_instruments, p11_neg_readout`; consistency block
  (fill_rate / lead / Δ distribution summaries, per-domain shift sign).
- `run_metadata.json` — instruments, domains+coverage, ATR params, P2/P4/P5
  constants, power floor 30, MBB `B`/`L`-rule/seed/percentile method, `train_end_ts`
  per instrument, EXP-048 readiness source, library versions, two-pass determinism
  result.

## Interpretation Guide (pre-defined, before results exist)

- **Experiment verdict is delivery, not "confirmation helps".** If Steps 1–9 produce
  the per-cell frequency/timing/outcome tables and the §8 readout with determinism
  PASS and no battery breach on ≥3 instruments ⇒ `CONFIRM_CHARACTERISATION_DELIVERED`,
  regardless of the helps/hurts/flat mix.
- **Frequency:** a low `fill_rate` means most haramis are *not* confirmed before the
  ZigZag's own ATR giveback — the confirmation is selective; a high `fill_rate` means
  the stop usually triggers first. Either is a valid descriptive finding; read with
  the lead distribution.
- **Timing:** `lead_confirm < lead_direct` by construction — the gap quantifies the
  lead the confirmation *spends*. If `lead_confirm` collapses toward 0, confirmation
  arrives essentially at the ZigZag turn (little informational advantage retained).
- **Outcome (primary):** if CONFIRM's `median(MFE−MAE)_atr` exceeds DIRECT's with
  paired `CI_low > 0` in ≥5 cells over ≥3 instruments, the **readout** is that
  requiring confirmation improves the gross excursion balance — input to 014-B, **not**
  a tradability or selection claim (gross, no costs, no fill-rate penalty priced).
  The fill-rate cost must be read jointly (Plot 4): a positive shift at very low
  fill-rate trades frequency for quality.
- **Outcome (secondary `r`):** comparability to EXP-049 — DIRECT `r ≈ 0.50`
  replicating EXP-049's null on a harami (rather than ZigZag-confirmation) anchor
  would corroborate that the benchmark symmetric geometry is ~random on this substrate
  regardless of the entry signal; a CONFIRM `r` lifted above 0.50 with `ci_low_1s >
  0.50` would be disclosed colour, never a gate.
- **`CHARACTERISATION_REFUTED`** only on non-determinism or a construction-invariant
  breach on ≥3 instruments — never because confirmation "doesn't help".
- **No goalpost movement:** the stop rule, window rule, `N_event`, power floor 30,
  P11 5/3, and the MBB settings are fixed; no per-cell or post-hoc retuning; no arm is
  selected.

## Implementation safety constraints (for `experiment-developer`)

- **Temporal order:** sort the 1-minute TRAIN prefix by `CloseTime` before
  aggregation; never reorder ZigZag/HA generator input; order moves by `ConfirmTime`
  and haramis by `HA0Time`; align all views by `CloseTime`, never bar index. Map
  `HA0Time → s`, `ConfirmTime → idx` by exact `CloseTime` match (`searchsorted` with
  membership assertion, as `xen.capture_barriers.confirm_indices` does).
- **Holdout/TRAIN fence:** F01 prefix only — `train_rows = int(int(total*0.7)*0.7)`
  file-order 1-minute rows; never sort/collect the full file; never read TEST or the
  final-30% holdout (Parquet metadata + TRAIN prefix only). Assert every emitted
  timestamp `≤ train_end_ts`; any forward window crossing the edge ⇒ `*_DATA_CENSORED`.
- **Causality:** `rd`/`N_event` use only moves confirmed ≤ `HA0Time`; the stop level
  is the signal bar's own extreme; the fill scan and MFE/MAE use only bars in the
  bounded forward window; `next_confirm_idx` bounds the window only (declared
  completed-move allowance) and never enters an entry/price decision. Keep the
  first-touch fill scan an **explicit bounded loop** (sequential semantics); do not
  vectorise it.
- **Denominators:** `n_signals` = qualifying haramis (defined `rd`, defined
  `N_event`, DIRECT non-censored); `fill_rate` over `n_signals`; outcome stats over
  each arm's non-censored set; secondary `r` over resolved only. `NO_TREND_CONTEXT`,
  `P4_WARMUP`, `*_DATA_CENSORED`, `degenerate-ref` excluded and counted, never
  silently defaulted.
- **Zero-baseline / NaN:** `n_fills = 0 ⇒ fill_rate = 0`; `n_used < 30 ⇒
  NOT_REPORTABLE_BY_POWER`; `resolved < 30 ⇒ r null`; bootstrap resamples with empty
  resolved ⇒ dropped with a disclosed count (as in `block_bootstrap_ci`); `ATR[e] > 0`
  asserted before normalization (never divide by zero); paired Δ null when paired set
  `< 30`.
- **Vectorisation that is safe:** `rd` assignment (searchsorted), `N_event` (vectorised
  rolling median over the duration array), MFE/MAE (bounded forward `max` per event),
  and the symmetric-barrier resolution (reuse `resolve_first_touch`). The ZigZag
  state machine and the CONFIRM first-touch fill stay explicit/sequential.
- **Bounded iteration / progress:** `tqdm` over the (instrument × domain) outer loop
  (≤ 99 cells × 2 passes); `B = 10_000` resamples per reportable cell-arm (fixed,
  batched per `BOOT_BATCH`); per-cell bounded memory — do not retain all domain frames
  or all bootstrap arrays; helpers return data, no helper-level prints.
- **Module budget:** one new `python/src/xen/confirm_entry.py` (`rd` assignment, P4
  cap at a signal index, CONFIRM stop/window/fill, per-arm direction-signed MFE/MAE),
  reusing `xen.zigzag`, `xen.heiken_ashi_generator`, `xen.ha_harami`,
  `xen.bar_aggregator`, `xen.capture_barriers`, `xen.move_position` unchanged. Output
  dirs created only in orchestration, never at import.

## Complexity Check

- **Statistical tests: 2 / 2** — (1) moving-block bootstrap CIs on per-arm outcome
  statistics (`median(MFE−MAE)_atr` + reused `block_bootstrap_ci` for secondary `r`);
  (2) moving-block bootstrap CI on the per-cell paired CONFIRM−DIRECT shift. Both are
  CI estimations (disclosed colour for the readout), not NHST viability gates.
- **Visualisations: 4 / 4** — fill_rate heatmap; lead-time DIRECT vs CONFIRM; per-arm
  MFE/MAE summary; paired-Δ vs fill-rate scatter.
- **New modules: 1 / 1** — `python/src/xen/confirm_entry.py`.
