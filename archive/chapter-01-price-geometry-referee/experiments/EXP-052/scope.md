# Experiment: EXP-052 — Phase 014-A Signal-Interpretation Characterisation: Direct Harami vs Signal+Confirmation (`/CONFIRM`) Frequency, Timing & Outcome (ATR-ZigZag + HA Harami, 99 Cells)

**Phase:** 014 (HA-harami substrate & capture geometry; checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture`, G0 PASS 2026-06-14) ·
**Sub-phase:** 014-A · **HYP:** HYP-005 · **Registry:**
`CF-HA-HARAMI-001/HYP-005`, variant `CF-HA-HARAMI-001/CONFIRM` (multiplicity-registry
Phase 014 batch, line 325/332) · **Candidate slots:** 0 (characterization) ·
**TEST reads:** 0 (TRAIN-only; no ledger entry; nested analysis-set TEST stratum
unread; current EXP-052 counted-read tally for every member stratum = 0, and this
experiment adds none).

**Analog:** EXP-051 / EXP-050 99-cell substrate/loader pattern (F01 prefix loader,
per-cell loop, determinism replay, bounded plots). **Reuse (frozen, unchanged):**
`xen.zigzag.generate_zigzag` (P1 substrate, confirmed moves),
`xen.heiken_ashi_generator.generate_heiken_ashi` (HA candles for harami detection),
`xen.ha_harami.detect_ha_harami` (core signal), `xen.bar_aggregator.aggregate_ohlc`,
`xen.capture_barriers` (`resolve_first_touch`, `block_bootstrap_ci`,
`summarize_geometry`, `time_caps` — P4 caps and the regime-clustered MBB, for the
disclosed fav-before-adv secondary), `xen.move_position.assign_to_moves` (pivot
tiling, for the disclosed position-in-move secondary). **New module (≤1):**
`python/src/xen/confirm_entry.py` — the `/CONFIRM` stop-order arm (reversal-direction
assignment from confirmed ZigZag context, stop level at the signal bar's real
extreme, causal in-window fill scan) plus the per-arm direction-signed MFE/MAE
measurement; reusable in 014-B. If the developer/analyst judge it not yet reusable it
may instead live as an experiment-local helper under `code/`.

**Gating precondition (satisfied):** EXP-052 consumes the per-cell readiness map
from **EXP-048 (HYP-001)**, which reached **READINESS_DELIVERED** with **audit PASS**
and post-experiment **APPROVE** (closed). Cell membership = EXP-048
**READY ∪ READY_FLAGGED** cells only (**99 cells**: 86 READY + 13 READY_FLAGGED); the
3 **COVERAGE_EXCLUDED** cells (US500-4h, JP225-2h, JP225-4h) are excluded with record.
EXP-052 is **independent of EXP-049 / EXP-050 / EXP-051** as gates; it reuses the
frozen `xen.capture_barriers` machinery validated by EXP-049 (no re-validation
required) but waits on none of their *outcomes*.

## Operator Framing Decisions (recorded 2026-06-15, pre-data-contact)

The `/CONFIRM` rule is **not pinned by D0 (P1–P13)**. Three interpretive choices that
materially change what HYP-005 measures were put to the operator before this scope was
written; all are pre-data-contact and tune nothing against outcomes:

1. **Confirmation threshold (stop-order level) = the harami signal bar's real
   extreme in the predicted reversal direction.** For a harami at `HA0Time` (signal
   bar index `s`) with predicted reversal direction `rd` (see §"Reversal-direction
   assignment"): `rd = +1` (bullish reversal) ⇒ **buy-stop = `RealHigh[s]`**, fills
   when a later real bar's `High ≥` stop; `rd = -1` (bearish reversal) ⇒
   **sell-stop = `RealLow[s]`**, fills when a later real bar's `Low ≤` stop. The
   confirm-arm entry price is the stop level itself (gross, no slippage). Simplest,
   fully causal, no extra parameter.
2. **Confirmation validity window = until the next ZigZag trend-change confirmation,
   capped at the P4 adaptive horizon.** The stop is live over real bars
   `(s, window_end]` with `window_end = min(next_confirm_idx − 1, s + N_event)`,
   where `next_confirm_idx` is the index of the first ZigZag `ConfirmTime` strictly
   after `HA0Time` and `N_event` is this event's P4 adaptive cap (§P4). If the stop
   is not triggered inside the window ⇒ **NO_FILL** (counted in the fill-rate
   denominator). This makes the fill condition the family's core question: *does the
   harami's confirmation trigger before the ZigZag's own `ATR_MULT × ATR` giveback
   confirms the reversal?*
3. **Outcome metric = direction-signed MFE/MAE over the P4 horizon (PRIMARY) +
   EXP-049 symmetric fav-before-adv (SECONDARY, disclosed).** Primary descriptive
   outcome is per-arm MFE/MAE on real prices over `[entry+1, entry+N_event]`,
   ATR-normalized. Secondary disclosed view reuses `xen.capture_barriers` symmetric
   1:1 barriers (fav distance = `0.50 ×` magnitude of the LOOKBACK=1 preceding
   confirmed move) anchored at each arm's entry, reported as `r = P(fav before adv |
   resolved)` directly comparable to EXP-049's G1.

**Defaults adopted (all derived from ratified D0 items; nothing tuned):** P1 ZigZag
Wilder/14/`ATR_MULT=1.0`; P4 adaptive cap `N_event = max(6, round(1.5 × median(trailing-20
confirmed-move durations)))` with the `< 5`-trailing-moves warmup exclusion; P5
`LOOKBACK=1` (the immediately preceding confirmed move) for the secondary barrier
reference; P6 strong-move filter OFF (base harami — no `/STRONG-*` here); detection on
HA candles, **every outcome on real prices**.

## Hypothesis

Exploratory signal-interpretation characterisation (gross, descriptive, **no
selection**, no market-edge *screen*): for every EXP-048-READY cell (17 instruments ×
{5m, 15m, 30m, 1h, 2h, 4h}), both the **direct** harami entry and the
**signal+confirmation** (`/CONFIRM` stop-order) entry can be computed
deterministically and look-ahead-safely (the per-bar fill check and all entry
references use only data at/before that bar; the window endpoint and outcome use the
predeclared completed-move allowance), and their per-cell **frequency** (fill rate),
**timing** (lead in bars over the ZigZag confirmation), and **subsequent outcome
distribution** (direction-signed MFE/MAE primary; symmetric fav-before-adv secondary,
real prices) are measured and compared. There is **no viability/pass threshold for
HYP-005** — it is a descriptive comparison; a predeclared, **non-binding** P11-style
readout flags where CONFIRM's outcome distribution exceeds DIRECT's.

## Question

For each EXP-048-READY cell, taking every qualifying HA harami as one event:

a. Can each harami be assigned a **deterministic, causal** predicted reversal
   direction `rd` from confirmed ZigZag context, a direct-arm entry (signal-bar real
   close), and a confirm-arm stop level + in-window fill decision — with a
   deterministic second-pass replay?
b. **Frequency:** per cell, `n_signals` (qualifying haramis = the common DIRECT
   event set) and `n_fills` (the CONFIRM subset whose stop triggered in-window);
   `fill_rate = n_fills / n_signals`.
c. **Timing:** per arm, the **lead** in bars over the ZigZag trend-change
   confirmation (`lead_direct = next_confirm_idx − s`;
   `lead_confirm = next_confirm_idx − trigger_idx` on filled events) and the
   confirm-arm **time-to-fill** (`trigger_idx − s`).
d. **Outcome distribution (primary):** per arm, the direction-signed **MFE/MAE**
   over `[entry+1, entry+N_event]` on real prices, ATR-normalized (medians, IQR,
   and `median(MFE−MAE)`), with regime-clustered MBB CIs.
e. **Outcome distribution (secondary, disclosed):** per arm, the EXP-049 symmetric
   fav-before-adv `r = P(fav before adv | resolved)` from each arm's entry, with the
   resolved/time-cap/censored split and MBB CI.
f. **Comparison readout (non-binding):** per cell, the CONFIRM−DIRECT shift in the
   outcome statistics (paired on filled, both-non-censored events) with CIs, and a
   P11-style composition count (`≥ 5` cells over `≥ 3` instruments where the shift's
   CI_low > 0) — **explicitly a descriptive readout, not a gate or selection.**

## Scope Boundaries

### Data Views

- 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to 5m,
  15m, 30m, 1h, 2h, 4h via `xen.bar_aggregator.aggregate_ohlc`. **5m strict coverage**
  (`min_coverage=None`); **15m/30m/1h/2h/4h at `min_coverage=0.90`** — identical to
  EXP-048/049/050/051/VAL-004.
- **The ZigZag substrate, all entry references, stop levels, MFE/MAE excursions, and
  barriers are computed on real domain OHLC.** The **harami detector runs on Heiken
  Ashi candles** (`generate_heiken_ashi` of the same real domain bars) — detection
  only. **No metric uses HA prices.** No Line Break / Renko views.

### Confirmed-move substrate & harami events (the population)

- Run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` (P1, frozen) on
  each cell's real domain bars (TRAIN-only). Confirmed moves carry `StartTime`,
  `EndTime` (pivot), `ConfirmTime`, `Direction`, `StartPrice`, `EndPrice`.
- Run `xen.heiken_ashi_generator.generate_heiken_ashi` then
  `xen.ha_harami.detect_ha_harami` (both frozen) on the same domain bars; each harami
  carries `HA0Time` (signal bar close time). Map `HA0Time` to its real domain-bar
  index `s` by exact `CloseTime` match.

### Reversal-direction assignment (causal, binding)

- `rd = Direction(most recent confirmed move with ConfirmTime ≤ HA0Time)`.
  Derivation: after an up-move (`+1`) confirms, the ZigZag tracks a down-trend, so the
  in-progress (prevailing) move is down and the harami at its exhaustion predicts a
  down reversal (`rd = -1`); symmetrically after a down-move. Hence
  `prevailing_trend = −Direction(last confirmed)` and `rd = −prevailing_trend =
  Direction(last confirmed)`. `rd = +1` ⇒ bullish reversal (buy-stop);
  `rd = -1` ⇒ bearish reversal (sell-stop).
- A harami with **no** confirmed move at/before `HA0Time` (ZigZag warmup) has **no
  defined trend context** → excluded from `n_signals`, disclosed (mirrors EXP-050).

### DIRECT arm

- Entry at the signal bar `s`; entry price `= RealClose[s]`. Direction-signed by `rd`.

### CONFIRM arm (`/CONFIRM`, stop-order)

- Stop level: `rd = +1` → `RealHigh[s]` (buy-stop); `rd = -1` → `RealLow[s]`
  (sell-stop). Live window `(s, window_end]`,
  `window_end = min(next_confirm_idx − 1, s + N_event)`. **Causal fill scan:** the
  first bar `i` in the window with `High[i] ≥` buy-stop (`rd=+1`) / `Low[i] ≤`
  sell-stop (`rd=-1`) is the trigger; entry price `=` stop level. No trigger ⇒
  `NO_FILL`. (Same-bar both-side ambiguity cannot arise: a single directional stop.)
- `next_confirm_idx` = index of the first ZigZag `ConfirmTime` **strictly after**
  `HA0Time` (the confirmation of the predicted reversal/continuation). Used **only**
  to bound the descriptive window — see the completed-move allowance below.

### Outcome — MFE/MAE (PRIMARY, real prices, direction-signed)

- For each arm's entry bar `e` (DIRECT `e=s`, CONFIRM `e=trigger_idx`) and entry price
  `p`, over the forward window `[e+1, e+N_event]` (fenced to `n_bars−1`):
  favourable excursion at bar `i` = `rd=+1`: `RealHigh[i] − p`; `rd=-1`:
  `p − RealLow[i]`. Adverse = the opposite side. `MFE = max(0, max favourable)`,
  `MAE = max(0, max adverse)`.
- **Normalization:** `MFE_atr = MFE / ATR[e]`, `MAE_atr = MAE / ATR[e]` (Wilder ATR-14
  at the entry bar; scale-free within instrument). Raw price and bps disclosed.
- **Censoring:** an event whose `[e+1, e+N_event]` window extends past the TRAIN edge
  is `DATA_CENSORED` (excluded from that arm's outcome distribution, disclosed) —
  mirrors EXP-049. Censoring is per-arm (CONFIRM's later anchor can censor when DIRECT
  does not).

### Outcome — symmetric fav-before-adv (SECONDARY, disclosed)

- Reuse `xen.capture_barriers`: from each arm's entry `(e, p)`, symmetric 1:1 barriers
  with fav distance `= 0.50 × |EndPrice − StartPrice|` of the LOOKBACK=1 preceding
  confirmed move (the same move that set `rd`); adverse distance equal, opposite side.
  Resolve first-touch over `[e+1, e+N_event]` via `resolve_first_touch`; report
  `r = fav/(fav+adv)` per arm with the resolved/time-cap/censored split and the
  regime-clustered MBB CI (`block_bootstrap_ci`). Degenerate (`magnitude = 0`)
  excluded. Directly comparable to EXP-049 G1 (`r ≈ 0.50` null reference). **Disclosed,
  never the binding endpoint.**

### Look-ahead / Causality Discipline (binding)

- **Entry references and the per-bar fill scan are causal:** the stop level is the
  signal bar's own real extreme (known at `s`); each window bar's High/Low is used
  only at that bar; `rd` uses only moves confirmed at/before `HA0Time`; ATR at bar `e`
  uses bars `≤ e`; the P4 cap uses only moves confirmed at/before `HA0Time` (its
  trailing window runs through the reference move `j` inclusive, whose realized
  duration is known at `ConfirmTime[j] ≤ HA0Time`).
- **Descriptive completed-move allowance (binding, declared).** Two quantities use a
  forward/terminal reference: (i) `window_end`'s `next_confirm_idx` (the next ZigZag
  confirmation), and (ii) the secondary barrier's `EndPrice` of the preceding
  confirmed move (already known at `s`, so (ii) is in fact causal; only (i) is
  forward). This is permitted **only** because HYP-005 is a descriptive
  characterisation of completed moves — *no live trading, signal, capture, or P&L
  decision uses `next_confirm_idx`*; it bounds a descriptive window only, and is
  capped by the strictly-causal `s + N_event`. This is the same family allowance
  EXP-050/051 declared and is disclosed in every result.
- **TRAIN fence:** every move `ConfirmTime`, every HA bar / harami `HA0Time`, every
  fill `trigger_idx`, and every forward-window bar has `CloseTime ≤ train_end_ts`; no
  row beyond the TRAIN edge is read (events whose window crosses it are `DATA_CENSORED`).
  Ordering/alignment by `CloseTime`, never bar index across views.

### Instruments (17)

BTCUSD, EURUSD, USTEC, XAUUSD (core) + GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD,
EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225. **DE30 disclosure:** truncated
broker history (ends 2026-01-16); counts/rates derive from its own realized timeline,
not span-comparable. Cells included only if EXP-048 marked them READY/READY_FLAGGED
(99 cells; 3 COVERAGE_EXCLUDED dropped).

### Time range

**TRAIN stratum only** — the first 70% of each instrument's first-70% analysis slice
(first 49% of the file), by the EXP-043/EXP-048 F01 file-order-prefix convention
(`train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)`
file-order 1-minute rows). The nested analysis-set **TEST stratum is not read**; the
final-30% **global holdout** is never loaded, counted, or touched (only Parquet
metadata + the TRAIN prefix are read).

## Readiness / Invariant Battery

Per cell, an invariant battery (mirrors EXP-048/049/050/051, keyed by invariant name;
all counts must be 0 unless noted as disclosed):

1. **Event well-formedness:** every qualifying harami (defined `rd`, defined P4 cap,
   non-censored window) gets a defined DIRECT entry and a defined CONFIRM decision
   (`FILL` with a `trigger_idx ∈ (s, window_end]`, or `NO_FILL`). Warmup-excluded
   (no trend context), P4-warmup (`< 5` trailing moves), and `DATA_CENSORED` counts
   are disclosed, not silently defaulted. `n_fills ⊆ n_signals`.
2. **Stop / fill validity:** a recorded `FILL` satisfies the directional trigger
   exactly (`High[trigger] ≥` buy-stop / `Low[trigger] ≤` sell-stop) and
   `s < trigger_idx ≤ window_end`; `lead_confirm ≥ 1`, `lead_direct ≥ 1`,
   `lead_confirm ≤ lead_direct` on every filled event.
3. **MFE/MAE validity:** `MFE, MAE ≥ 0` and finite on every non-censored event;
   `ATR[e] > 0` (warmup guarantees ≥14 bars); no normalization by zero.
4. **Causality / TRAIN fence:** every `ConfirmTime`, `HA0Time`, `trigger_idx`, and
   forward-window bar `CloseTime ≤ train_end_ts`; the per-bar fill scan and entry
   references use no future bar beyond the declared completed-move allowance for
   `next_confirm_idx`.
5. **Determinism:** a full second pass (re-aggregate, re-HA, re-detect harami,
   re-ZigZag, re-assign `rd`, re-scan fills, re-measure MFE/MAE, re-resolve barriers,
   re-bootstrap with the same fixed seed) compares **frame-identical** to the first
   pass (including CI bounds).

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Common denominator** `n_signals` = qualifying haramis per cell (defined `rd`,
  defined P4 cap, DIRECT window non-censored). **Fill rate** `fill_rate = n_fills /
  n_signals`; `n_fills = 0` ⇒ `fill_rate = 0` (never `0/0`).
- **Outcome distributions** are reported on each arm's **non-censored** event set
  (DIRECT over its non-censored `n_signals`; CONFIRM over its non-censored `n_fills`).
  Per-arm medians/IQR of `MFE_atr`, `MAE_atr`, `MFE−MAE`; secondary `r` over resolved
  events only (symmetric-barrier null `r = 0.50`).
- **Power floor = 30.** A cell with `n_signals < 30` is **NOT_REPORTABLE-by-power**
  for the DIRECT outcome and the comparison (recorded, excluded from the §f readout).
  Independently, `n_fills < 30` ⇒ the CONFIRM outcome distribution for that cell is
  NOT_REPORTABLE-by-power (fill-rate and timing are still reported). Mirrors
  EXP-049/050/051; `resolved < 30` ⇒ secondary `r` NOT_REPORTABLE-by-power, never an
  undefined ratio.
- **Comparison shift** (paired, §f): per cell, `Δ = stat(CONFIRM) − stat(DIRECT)` on
  the subset of events that are **filled and non-censored in both arms** (paired);
  `stat ∈ {median(MFE−MAE)_atr, r_secondary}`. Reported with a fixed-seed MBB CI. No
  metric is expressed as a percentage improvement over a zero baseline; DIRECT is the
  explicit reference arm.

## Comparison & Composition (non-binding descriptive readout — there is NO gate)

- HYP-005 has **no viability threshold**: it characterises frequency/timing/outcome.
  To give the qualitative "confirmation helps / hurts" claim a mechanical bar (per the
  programme no-unquantified-claim principle) **without** introducing a gate, the
  experiment emits a predeclared **non-binding** readout: a cell "shows a positive
  confirmation shift" iff its paired `Δ` (for the stated stat) has bootstrap
  `CI_low > 0`; the family-level descriptive statement holds iff this occurs in
  **≥ 5 cells over ≥ 3 instruments** (P11 convention). The symmetric negative-shift
  readout (`CI_high < 0`) is reported in parallel.
- This readout **selects nothing, routes nothing, and consumes no slot.** Any 014-B
  combined-event registration or routing is checkpoint desk work, never self-declared
  by this experiment.

## Success / Failure / Inconclusive Criteria

- **Experiment verdict — CONFIRM_CHARACTERISATION_DELIVERED:** the per-cell frequency
  (`n_signals`, `n_fills`, `fill_rate`), timing (`lead_direct`, `lead_confirm`,
  time-to-fill), and outcome (per-arm MFE/MAE primary; fav-before-adv `r` secondary)
  tables — with the disclosed warmup/P4-warmup/censoring/excluded fractions and the
  non-binding §f comparison readout — are produced, whatever the helps/hurts mix.
- **Evidence AGAINST (CHARACTERISATION_REFUTED — halts 014-A pending a fix):** a
  **systematic** construction defect, predeclared threshold: **non-determinism on any
  cell**, **or** an event-well-formedness / stop-fill-validity / MFE-MAE-validity /
  causality-TRAIN-fence invariant (battery items 1–4) violated on **≥ 3 instruments**.
  The two arms cannot be characterised on a broken construction.
- **Inconclusive (cell-level only):** a cell with `n_signals < 30`
  (NOT_REPORTABLE-by-power), or `n_fills < 30` for the CONFIRM-outcome leg only;
  recorded, excluded from the §f readout, not a failure.
- The **helps/hurts outcome** (whether confirmation shifts the distribution) is **not**
  an experiment verdict — it is descriptive output read at the §10 checkpoint desk.

## Complexity Budget

- **Max statistical tests: 2** — (1) fixed-seed regime-clustered moving-block
  bootstrap CIs (reuse `xen.capture_barriers.block_bootstrap_ci`) on the per-arm
  outcome statistics (`median(MFE−MAE)_atr` and the secondary `r`); (2) the same MBB
  on the per-cell paired `Δ` (CONFIRM−DIRECT) shift. Both are CI **estimations**, not
  NHST viability gates. No other inferential test.
- **Max visualisations: 4** — (i) `fill_rate` heatmap (17×6); (ii) lead-time
  distribution DIRECT vs CONFIRM (pooled/small-multiple, bars); (iii) per-arm
  `MFE_atr` / `MAE_atr` distribution summary (box/violin by arm); (iv) per-cell
  paired-`Δ` outcome shift vs `fill_rate` scatter, with the non-binding composition
  readout marked. All other forms (raw/bps outcomes, secondary `r` table, censoring
  fractions, position-in-move secondary) go to CSV. Bounded plot inputs from the
  analysis pass — no reloads.
- **Max new code modules: 1** under `python/src/xen/` — `confirm_entry.py`
  (reversal-direction assignment, stop level, causal in-window fill scan, per-arm
  direction-signed MFE/MAE; reusable in 014-B), **or** an experiment-local helper
  under `code/` if not yet reusable. Reuse `xen.zigzag`, `xen.heiken_ashi_generator`,
  `xen.ha_harami`, `xen.bar_aggregator`, `xen.capture_barriers`, `xen.move_position`
  unchanged (no edits).

## Data Requirements

Per instrument: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect
only the first `train_rows` file-order 1-minute rows (F01 prefix; never sort/collect
the full file, never read TEST or holdout); assert chronological; `train_end_ts` =
last `CloseTime`. Aggregate each EXP-048-READY domain (5m strict; others
`min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`; run `xen.zigzag`
(confirmed moves) and `time_caps` (P4); generate HA candles + detect haramis; assign
`rd`, DIRECT entry, CONFIRM stop + fill; compute per-arm MFE/MAE and the secondary
barrier resolution; bootstrap CIs (fixed seed); collect per-cell records; second full
pass for determinism. Outputs (`results/`): `per_cell_confirm.parquet` (per-cell
frequency/timing/outcome rows, both arms, both-pass flag, reportable flags),
`outcome_primary.csv` (per-arm `MFE_atr`/`MAE_atr`/`MFE−MAE` medians+IQR+CI),
`outcome_secondary_r.csv` (per-arm fav-before-adv `r`, resolved/time-cap/censored
split, CI), `timing.csv` (`lead_direct`/`lead_confirm`/time-to-fill summaries),
`comparison_readout.csv` (paired `Δ`, CI, positive/negative-shift flags),
`excluded_fractions.csv` (warmup / P4-warmup / censored / degenerate),
`composition_readout.json`, `run_metadata.json`; four bounded plots from the collected
per-cell summaries (no reloads). `tqdm` over the instrument/cell outer loop; per-cell
bounded memory (do not retain all domain frames). Expected runtime: minutes (READY
cells × 2 passes; the MBB reuses the EXP-049 batched implementation).

## Exclusions

- No 3-barrier capture-geometry *viability* read (EXP-049 / HYP-002 — the barrier
  machinery is reused only for the disclosed secondary `r`), no `/STRONG-STAT` or
  `/STRONG-HA` filter (EXP-051; P6 OFF), no `/BARCFG` isolation, no `/ATRMULT`,
  `/LOOKBACK`, `/VPTARGET`, `/MAGTARGET`, `/ADV-*`, `/THIRD-*` variant.
- No combined harami-at-trend-exhaustion *screening* event; EXP-052 characterises the
  two entry interpretations descriptively and registers **no** candidate branch (that
  is 014-B).
- No costs (gross throughout); no net P&L, expectancy, Sharpe, or equity curve. MFE/MAE
  and `r` are descriptive gross excursions on real prices, feeding no tradability claim.
- No returns or prices from HA/Renko construction values; all entries, stops, MFE/MAE,
  and barriers are real-bar prices; HA candles are used only for harami detection.
- No parameter tuned, selected, or frozen against any EXP-052 output; no
  cross-instrument or cross-domain pooling for any per-cell metric; no selection
  between the two arms; no TEST or holdout contact; no candidate slot consumed; no
  TEST read; no signal-registry status advance (descriptive characterization).

## Suggested Direction (non-binding)

Mirror the EXP-051 orchestration (F01 loader, per-cell loop, determinism replay,
bounded plots). Build the confirmed-move array and `confirm_indices`/`time_caps`
(P4) once per cell; detect haramis; for each harami resolve `rd` from the confirmed
moves via a causal `searchsorted` on `ConfirmTime ≤ HA0Time`; compute the CONFIRM
fill with a bounded sequential scan over `(s, window_end]` (keep it an explicit causal
loop — do not vectorize the first-touch fill); measure MFE/MAE with a bounded forward
slice; reuse `resolve_first_touch` + `block_bootstrap_ci` for the secondary. Keep the
ZigZag / HA / harami / barrier generation calls frozen and unedited. Emit the
descriptive frequency/timing/outcome tables and the **non-binding** §f readout; do
**not** self-adjudicate any gate or register any branch.
