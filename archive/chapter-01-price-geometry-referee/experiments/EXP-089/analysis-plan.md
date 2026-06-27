# Analysis Plan: Experiment EXP-089 (AMENDED — D0-amendment-001)

**CF-MR-001 Mean-Reversion Entry Availability Screen — directional favourable-availability, TRAIN-only, gross.
Amended in place after the first run was found to be a deviation (audit C-1/C-2): MR-tempo measurement horizon,
regime-matched + horizon-matched control, and a single-test leg-1 gate across all 6 sub-screens (leg-2
retired).**

Phase 020 · Mean-Reversion Entry Availability Screen · Family **CF-MR-001** · `CF-MR-001/HYP-001` · 0 candidate
slots · 0 counted TEST reads. Companions: `scope.md` (bannered) + `D0-amendment-001` (authoritative); Phase 020
D0 (`docs/experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/D0-predeclarations.md`,
bannered) + `design.md` §3 + `G-020-gate-criteria.md`; **single-test** bite-check GREEN
(`…/bite-check/bite_check.py` → `bite_check_report.json`, sha256 `f01a000b…`).

> **Amendment summary (authoritative = `D0-amendment-001`).** Three design elements change; everything else is
> frozen from D0. **(1) Horizon (fixes C-2):** the trend-length MA-segment adaptive cap is replaced by a
> **causal MR-tempo cap** — the favourable excursion is measured over a window set by the cell's own RSI-2
> reversion tempo, not its trend tempo. **(2) Control (fixes C-1) + parity:** the three `/VOLREGIME` sub-screens
> use a **regime-matched** random control (same-regime bars), and the MR-tempo cap rule is applied **identically**
> to signal and control so the comparison is matched on count + direction + regime + horizon. **(3) Gate:** the
> **leg-2 beats-CORE conjunction and the regime-membership-shuffle null are RETIRED**; all 6 sub-screens become
> **single-test leg-1** through `run_sub_screen`, and regime-dependence is read from *which regimes pass*.

> **RUN PRECONDITION (binding; flag for Stage-4 governance + the manual execution gate).** Retiring leg-2
> returns the gate to the **single-test joint-max-of-6** structure that is **already GREEN** at sha `f01a000b…`
> (D0 checks A–D: noise→EXONERATED, planted→ADMITTED with power, joint-max-of-6 restores family FWER to 0.043,
> MC-stable 1000↔5000). The MR-tempo cap and the regime-matched control are **upstream geometry** — they change
> the per-event `MFE` arrays fed *into* the gate, **not** the gate's null calibration (the null is the
> signal-shuffle over the per-cell pool, unchanged). **Therefore no bite extension or re-confirmation is
> required**; the leg-2 bite extension (`07cec052…`) is **moot and dropped**. Stage-3 must ensure
> `bite_check.py` is at the single-test `f01a000b…` scope and the D0/scope sha reference points to `f01a000b…`.
> Integrity of the new inputs is enforced by the Step-7 reconciliation guards (count/direction/regime
> membership), not by the gate bite.

## Objective

Produce, per member cell and per frozen sub-screen, the **directional favourable-availability statistics** that
the **G-020** rubric (D5, as amended) converts into an **admit / exonerate / inconclusive** disposition for the
CF-MR-001 mean-reversion family. The single binding decision rule is the **D2b multiplicity-adjusted
permuted-axis admission gate** combined as the **joint max over the 6 sub-screens** (no cross-axis Holm — single
family). The binding adjudication is **G-020**, not this experiment.

The experiment verdict is **`SCREEN_DELIVERED`** if all gate inputs are produced deterministically for the whole
member set; it HALTs only on non-determinism, a real-price/look-ahead/holdout-fence violation, or a
matched-random count/direction/regime reconciliation break. A **provisional** family disposition + argmax
sub-screen is reported, captioned **NON-BINDING pending G-020**.

All estimators are non-parametric / resampling-based (median, moving-block bootstrap, label-permutation). No
normality, stationarity, i.i.d., or constant-volatility assumption gates any verdict. Per-stratum reporting
throughout (LESSON-001); no pooled-as-verdict number is binding.

## Fixed inputs (frozen upstream — not re-derived here)

- **Member set:** the **46 EXP-080-READY** instrument×domain cells (16 instruments × {15m,1h,4h} **minus**
  US500-4h, JP225-4h `COVERAGE_EXCLUDED`). No DE30. Realized RSI-MR cell count must match the bite-check `C=46`;
  the gate self-recalibrates `S*` to the realized C if D7 excludes a cell.
- **Six sub-screens (frozen, D2b):** `CORE`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND`,
  `CORE+FILTER`.
- **Entry — RSI-2 mean reversion (frozen, D1; neither tuned):** `RSI(2)` Wilder on domain `Close`; **long iff
  `RSI₂(t) < 10`**, **short iff `RSI₂(t) > 90`**. Favourable direction = long→up, short→down. RSI exit not used.
- **Variant toggles (frozen, D1):** **TREND** — long `∧ Close>EMA₂₀`, short `∧ Close<EMA₂₀`; **RSI-FILTER** —
  long `∧ RSI₅>50`, short `∧ RSI₅<50` (`EMA(20)`, `RSI(5)` Wilder).
- **Global filter `/VOLREGIME` (frozen, D1):** `ATR(14)` Wilder on domain bars; **causal trailing rolling-50
  percentile** of current ATR; cuts **33/66** → `LOW(<p33) / MED / HIGH(>p66)`; thresholds per
  (instrument,domain), past-bars-only; partition on the bare CORE only.
- **Per-event ATR:** Wilder ATR(14) (`ATR_PERIOD=14`) on real domain bars (`xen.zigzag.wilder_atr`). Kept as the
  endpoint denominator; **benign under the amendment** because signal and its control are now drawn from the
  same regime (§Step 5 cancellation argument). Retained only for cross-cell comparability (the 46-cell map on
  one scale).
- **Gate constants (GREEN single-test bite, unchanged):** per-cell one-sided lower-bound test at `Z = 1.645`;
  family FWER `0.05`; `S* = Q95` of the joint permuted-axis null; sensitivity band FWER ∈ {0.025, 0.05, 0.10};
  `N_PERM = 5000` (1000 MC-stability cross-check). **No cross-axis Holm** (single family).
- **Read region:** TRAIN sub-split `[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)`.
  Analysis-TEST and final-30% holdout never sliced.
- **Master seed `20260623`;** per-draw seed = deterministic hash of `(sub_screen, instrument, domain,
  replicate)`.

### AMENDED frozen constants — the causal MR-tempo cap (pinned pre-data; not tuned)

The measurement window replaces `TIMECAP_*`/`_ma_segment_moves` with an RSI-2 reversion-tempo cap. Constants are
fixed here **before any result-producing run**, justified by structure (not by realized availability):

| Constant | Value | Justification (pre-data) |
|---|---|---|
| Reversion-episode close | `RSI₂ ≥ 50` (long) / `RSI₂ ≤ 50` (short) | "Reversion complete" = the oscillator has returned to its **neutral midline**. 50 is the parameter-free RSI midpoint already used by the RSI-FILTER variant — **no new tunable threshold**. Symmetric for long/short. |
| `K_MULT` | `1.0` | The window should span **one typical reversion**, not a multiple of it. The retired trend cap used `1.5×` to give a *trend* room to run; an MR window wants the reversion itself, so the median episode duration (×1.0) is the natural horizon. |
| `W` (episode window) | `20` | Trailing count of completed episodes used for the median tempo. Mirrors the retired `TIMECAP_WINDOW=20`: enough to stabilize a median, short enough to track drift in a cell's tempo. |
| `MIN_EPISODES` | `5` | Minimum completed episodes before `t_i` to form a tempo estimate; fewer ⇒ **warmup** (event excluded + disclosed). Mirrors `TIMECAP_MIN_MOVES=5`. |
| `FLOOR` | `3` bars | A reversion needs a few bars for any favourable excursion to register over `[i+1, i+cap]`; floor 3 prevents degenerate 1–2-bar windows. Binds only on extremely fast-tempo cells (disclosed). |
| `CAP_MAX` | `40` bars | Loose guard that **rarely binds** (reversion-to-neutral is fast by construction); prevents a pathological tempo estimate from re-introducing a trend-length window. The per-cell fraction of `CAP_MAX`-bound events is disclosed; frequent binding flags a non-MR-like tempo for that cell. |

**Look-ahead argument:** an episode contributes to entry `t_i`'s cap only if its **close index is strictly less
than `t_i`** (`< t_i`, not `≤`); the median is over the last `W` such completed episodes. The RSI-2 series is a
causal Wilder recurrence (bar `i` uses only closes `≤ i`). Therefore the cap at `t_i` uses only information
available at the entry bar. The path is then read over `[t_i+1, min(t_i+cap, train_edge_idx)]` — strictly
forward, clipped at the TRAIN edge. No future bar enters any cap or any excursion.

### AMENDED frozen control — regime-matched + horizon-matched `SUB-RANDOM`

- **CORE, CORE+TREND, CORE+FILTER (unchanged):** count+direction-matched all-bars `SUB-RANDOM`
  (`xen.capgeo_substrates.random_entries`), as in EXP-080/081/086/087. These sub-screens are not
  regime-conditioned.
- **CORE-VOL-LOW / MED / HIGH (AMENDED):** the matched-random control is drawn **only from bars carrying that
  regime label** (within TRAIN, ATR-defined, non-warmup tempo), matched on **count and direction** to that
  regime's signal subset. The permutation **pool** for each regime sub-screen is likewise drawn from
  same-regime bars (direction-proportioned). No all-bars control enters a regime read.
- **Horizon parity by construction:** the MR-tempo cap rule (above) is applied to **every** entry — signal and
  control alike — at its own timestamp. Because the cap depends only on pre-`t` episode history (not on whether
  the entry is a signal), a regime-matched control entry receives a cap drawn from the **same** cell-level tempo
  process, restricted to the same regime, as the signal. This is **causally equivalent to** resampling the
  signal's realized cap distribution for the control, but exact per-timestamp and simpler (no extra resampling
  step). Parity is thus on **count + direction + regime + horizon**.

---

## Methodology

### Step 1 — Cohort construction (per cell, per sub-screen)

- **Method:** lazy `pl.scan_parquet` per instrument; read `total_rows` from Parquet metadata; slice the first
  `train_cutoff` 1-minute rows; assert `CloseTime` sorted; build 15m/1h/4h bars via
  `xen.domain_bars.build_domain_bars` (`min_coverage=0.90` + analysis-boundary fence). On each cell's real
  domain `Close`, compute `RSI(2)`, `RSI(5)` (Wilder) and `EMA(20)` (`xen.mean_reversion`); derive **CORE**
  (long `RSI₂<10`, short `RSI₂>90`) and the two variant populations (`CORE+TREND`, `CORE+FILTER`) by
  intersecting CORE with the frozen toggle. Compute the `ATR(14)` rolling-50 causal-percentile regime label per
  bar (`xen.vol_regime.regime_labels`) and partition the **regime-eligible CORE** (CORE events at bars with a
  defined regime label) into `LOW/MED/HIGH`. Build the per-cell **reversion-episode duration series** (causal)
  for the MR-tempo cap (Step 2). For each of the 6 sub-screen signal populations draw its count+direction-matched
  `SUB-RANDOM` — **all-bars for CORE/variants, regime-restricted for the three `/VOLREGIME` sub-screens** — via
  `random_entries` over the appropriate candidate-bar index set (seed key = master-seed hash of `(sub_screen,
  instrument, domain, "random")`).
- **Why:** reuses the certified readiness scaffolding (EXP-080 member set, `random_entries`, domain generation)
  and swaps only (i) the conditioning to RSI-MR, (ii) the cap basis to MR tempo, and (iii) the regime control to
  same-regime draws. The mean-reversion entry and the vol-regime partition remain the two new levers.
- **Reconciliation guard (binding HALT):** per cell, per sub-screen, assert matched-random count equals the
  signal count and the long/short split matches; for the regime sub-screens assert every control entry's bar
  carries the **matching regime label** (regime-match integrity); assert all index arrays lie within
  `[0, train_edge_idx]`; assert `n_LOW+n_MED+n_HIGH == n_CORE_reg` (the regime partition is exhaustive over
  regime-eligible CORE). Any mismatch is a HALT (harness bug, not a data shape).
- **Simpler alternative considered:** one domain or the 4-instrument core. Rejected — 46 cells is the bite `C=46`
  and the G-020 D2a reference.
- **Assumptions:** deterministic generators (VAL-005/EXP-080) + deterministic causal RSI/EMA/regime/episode
  tempo; holds.
- **Output:** per (cell, sub-screen) signal + matched-random entry index/direction/epoch arrays; per-regime
  membership index arrays over `CORE_reg`; the causal episode-duration series; `recon_ok` (incl. regime-match).

### Step 2 — Per-event causal MR-tempo cap + entry direction (AMENDED)

- **Method:** per cell, build reversion episodes from the causal `RSI(2)` series (long opens `RSI₂<10`, closes
  first later bar `RSI₂≥50`; short opens `RSI₂>90`, closes first later bar `RSI₂≤50`); each completed episode's
  `duration = close_idx − open_idx` (bars). For each entry at index `i` (and each matched-random / pool entry),
  `cap_i = clip(round(K_MULT · median(durations of the last W episodes with close_idx < i)), FLOOR, CAP_MAX)`;
  fewer than `MIN_EPISODES` completed episodes before `i` ⇒ **warmup** (disclosed + excluded). Applied by entry
  index/epoch to **every** sub-screen's signal set, its (regime-matched where applicable) `SUB-RANDOM`, and the
  permutation pool. The entry direction `d ∈ {+1,−1}` is the RSI-MR side (long=+1 / short=−1) and drives the
  signed favourable excursion (Step 3).
- **Why:** the cap now matches the family's **actual reversion horizon** (audit C-2), so the favourable excursion
  credited is the reversion move, not post-reversion trend drift. The identical rule on the control gives horizon
  parity (above). The cap is cell-intrinsic and causal — not a free knob (constants frozen pre-data).
- **Disclosure:** per cell, the realized cap distribution (median/mean cap, % warmup, % `FLOOR`-bound, %
  `CAP_MAX`-bound) for the signal and control sets — a frequent `CAP_MAX` bind flags a non-MR-like tempo.
- **Output:** per-event integer cap, `warmup` mask, `d`, per (cell, sub-screen, set).

### Step 3 — Signed favourable excursion on real OHLC (reuse `xen.capgeo_geometry.lifetime_path_geometry`)

- **Method:** for each non-warmup, ATR-defined event with entry index `i`, cap `c`, window `W = [i+1,
  min(i+c, train_edge_idx)]` on **real** domain OHLC, call `lifetime_path_geometry(high, low, close, atr_entry,
  entry_idx, direction=d, cap, n_bars=train_edge_idx+1)`. With `direction=d` the returned `mfe` is the **signed
  favourable excursion in the entry-signed direction**, ATR(14)-normalised — the D3 endpoint. Events with an
  empty post-clip window (`n_clipped_empty`) or ATR-undefined (`n_atr_undefined`) are excluded and counted.
- **Why:** standard MFE path geometry, reused frozen module, no exit/barrier/target (availability only). Real
  prices only (no HA/Renko anywhere).
- **Vectorization discipline:** intra-window max/argmax vectorized in-module; the outer event loop is explicit
  and cap-bounded (causal). `tqdm` over the (cell × sub-screen) loop.
- **Output:** per-event signed-favourable `MFE` (ATR units) + `usable` mask + exclusion counts, per (cell,
  sub-screen, set); per-regime `MFE` arrays over `CORE_reg` (for the regime sub-screen signal sets) and the
  per-regime matched-control `MFE` arrays.

### Step 4 — Per-cell read statistics (per cell, per sub-screen)

Over each set's usable (non-warmup / ATR-defined / non-clipped) events:

- **(a) Endpoint `MFE_med`** = `Q50(signed-favourable MFE)` (ATR). Median, not mean — the heavy tail corrupts
  means (CF-VOLEXP-001 lesson). Computed for each sub-screen's **signal** set and its **matched-random** set
  (all-bars for CORE/variants; regime-matched for the three `/VOLREGIME` sub-screens).
- **(b) Per-cell event-count denominators** disclosed separately for the signal set and the matched-random set
  (and, for the regime sub-screens, the per-regime signal/control counts and `n_CORE_reg` for context). A cell
  with `< 15` usable signal events on a sub-screen is `COVERAGE_EXCLUDED` for that sub-screen and **excluded
  from its `S` count** — recorded, never dropped.
- **Zero-baseline / degenerate handling:** a set with `MAD = 0` or a single usable event reports its `MFE_med`
  with a `degenerate` flag and is treated under the coverage bracket, never `0/0`.
- **Output:** per (cell, sub-screen) `(MFE_med_signal, MFE_med_rand, n_signal, n_rand, degenerate,
  underpowered)`.

### Step 5 — Per-cell beats-random test (the per-cell gate input — single leg, all 6 sub-screens) (AMENDED)

- **Leg 1 — beats-random (all 6 sub-screens; reuse `xen.availability_gate.cell_se` exactly):**
  `Δ̂_rand = MFE_med(signal) − MFE_med(SUB-RANDOM)`; SE `s_rand` estimated **once per cell** by moving-block
  bootstrap on the signal series + iid bootstrap on the matched-random series
  (`cell_se(cond=signal, ctrl=random, stat_kind="median", …)`, `B_SE=2000`); **beats-random ⇔
  `Δ̂_rand − 1.645·s_rand > 0`**. This is the established EXP-086/087 per-cell test, **unchanged**, now applied
  uniformly to all 6 sub-screens. For the regime sub-screens the control is the **regime-matched** `SUB-RANDOM`.
- **The leg-2 beats-CORE conjunction is RETIRED.** No `Δ̂_core`, no `beats_core`, no `pass_conjunction`. A regime
  cell counts toward `S` purely on its **clean, regime-matched** beats-random test.
- **C-1 cancellation argument (why regime-matched leg-1 is unconfounded):** within a regime sub-screen, both the
  signal subset and its control are drawn from bars carrying the **same regime label**, hence share the
  entry-ATR(14) distribution. The endpoint divides forward excursion by entry ATR in **both** arms from the same
  distribution, so the cross-regime denominator displacement that drove the deviation (LOW inflated / HIGH
  deflated vs an all-bars baseline) **cancels** in `Δ̂_rand`. ATR-normalization is therefore benign here and is
  kept only to place the 46 cells on one comparable scale. Horizon parity (Step 2) removes the matching C-2
  confound. The regime read now isolates **MR entry-timing edge within the regime**, which is the intended
  construct.
- **Why this estimator (methodology decision — flag for Stage-4 governance):** `cell_se` holds `s_cell` fixed
  across permutations exactly as the GREEN bite holds `se` fixed; reused verbatim. A regime is read by **which
  regimes pass** their own clean leg-1 — the additive question ("does conditioning on LOW help vs bare MR") is
  answered descriptively by comparing the LOW sub-screen's `S`/cells to CORE's, **non-binding** (LESSON-001:
  cross-sub-screen comparisons are disclosure, the binding statistic is the joint-max gate).
- **Simpler alternative considered:** keep a redefined additive leg-2 vs a regime-matched reference. Rejected by
  the amendment — with a clean regime-matched leg-1 the additive signal is already visible in *which regimes
  pass*; a second binding statistic adds multiplicity and moving parts for no inferential gain.
- **Assumptions:** `s_rand` is approximately invariant under the signal-shuffle null (the null shifts the mean
  difference, not the cell's intrinsic dispersion) — the GREEN-bite assumption; conservative under positive
  autocorrelation.
- **Output:** per (cell, sub-screen) `(Δ̂_rand, s_rand, ci_low_rand, beats_random)`.

### Step 6 — Joint-max permuted-axis admission null (D2b — the single binding gate) (AMENDED)

- **Realized per-sub-screen `S` (over powered cells), all 6 single-test:** `S = #cells beats-random`.
- **Per-sub-screen permuted null — signal-shuffle (reuse `run_sub_screen` UNCHANGED for all 6).** Precompute a
  direction-matched random-timing **pool** per (cell, sub-screen) — raw draw
  `min(n_bars_eligible, max(POOL_RAW_MIN, POOL_RAW_MULT·n_signal), POOL_RAW_CAP)`
  (`POOL_RAW_MIN=3000`, `POOL_RAW_MULT=8`, `POOL_RAW_CAP=30000`; directions in the signal's long/short
  proportion) — **from all bars for CORE/variants, from same-regime bars for the three `/VOLREGIME` sub-screens**
  — with per-event signed-favourable `MFE` via Step 3 (one-time cost; pool entries use the same MR-tempo cap
  rule). Each permutation draws an `n_signal`-sized with-replacement subsample of the pool as the pseudo-signal,
  recomputes `Δ̂` and `beats` with the **same fixed `s_rand`**; `S_perm = Σ_cells beats`. This is the EXP-086/087
  null exactly (`_perm_beats`), preserving per-cell count + direction; for regime sub-screens it additionally
  preserves the **regime** (pool is regime-restricted).
- **Family statistic + joint null (reuse `combine_axis` UNCHANGED):** feed all 6 `SubScreenResult` objects (all
  from `run_sub_screen`, each carrying a length-`N_PERM` `s_perm` at the **shared permutation index**) to
  `combine_axis`. `S_fam = max_sub S`; joint null `S_perm_max[p] = max_sub S_perm[p]`; `S* = Q95(S_perm_max)`;
  axis perm-p `= (1 + #{S_perm_max ≥ S_fam}) / (1 + N_PERM)`. **No cross-axis Holm** (single family — the
  joint-max-of-6 absorbs the within-family multiplicity).
- **Provisional disposition (NON-BINDING, captioned for G-020):** `ADMITTED iff S_fam > S* ∧ axis perm_p ≤
  0.05`; `EXONERATED iff every sub-screen S within the D2a band`; `INCONCLUSIVE iff S* ≥ max attainable S at the
  realized powered-cell count`. `combine_axis` emits the numbers and a disposition string referencing "G-019
  cross-axis Holm" — **that caption is cosmetic and superseded**: the experiment writes its own
  `provisional_disposition` captioned **"NON-BINDING — pending G-020 (no cross-axis Holm; single family)"** in
  `family_admission.json`, derived from `(S_fam, S*, perm_p)`. The frozen module is **not edited**.
- **`N_PERM`:** **5000** (production) with a **1000-vs-5000 MC-stability disclosure** (`S*` and perm-p at both;
  routing invariant). Sensitivity band: `S*` at FWER ∈ {0.025, 0.05, 0.10} (`Q975/Q95/Q90`); report the
  disposition at each — a pre-registered robustness sweep, not a selection.
- **Argmax lever (on admit):** the sub-screen attaining `S_fam` names the lever (bare MR / a specific vol regime
  / a variant), ranked by the **frozen** sub-screen-level permutation z-score `z_ss = (S_ss − mean(S_perm_ss)) /
  sd(S_perm_ss)`, tie-broken by trimmed-mean per-cell Δ of the driving sub-screen (D5). A `/VOLREGIME` argmax now
  means the MR edge is **regime-dependent** (present in that regime's clean leg-1, weak/absent elsewhere).
- **Output:** per sub-screen `(S, S*_sub, perm_p_sub, z_ss)`; family `(S_fam, S*, axis perm_p, rank_z, argmax
  sub-screen)`; FWER band; MC-stability table; provisional disposition (G-020-captioned).

### Step 7 — Determinism & integrity guards (binding HALT conditions)

- **Method:** a second full pass (including the permutation stream at its fixed seed-stream); assert the per-cell
  statistics table **and** the `(S, S_fam, S*, perm_p)` family statistics are frame-identical (exact). Assert:
  holdout never sliced (Parquet metadata only); no domain-bar label crosses the analysis-slice boundary; every
  path window's last index ≤ `train_edge_idx`; the Step-1 matched-random **count/direction/regime-membership**
  reconciliation and the `n_LOW+n_MED+n_HIGH == n_CORE_reg` partition identity hold for all cells; every
  regime-control entry carries the matching regime label. Record all seeds (master `20260623`, `SUB-RANDOM`,
  `B_SE`, permutation seed-stream) and the MR-tempo cap constants.
- **Why:** determinism + reconciliation + holdout-fence are the binding HALT conditions (scope; D6). A break is
  an implementation bug, not a data shape — route to `experiment-developer`, do not interpret.
- **Output:** `determinism_ok`, `recon_all_ok`, `regime_match_recon_ok`, `holdout_untouched` in
  `run_metadata.json`.

---

## Visualisations (≤ 4)

1. **Per-cell signed-Δ map** — `Δ̂_rand` across the 46 cells × 6 sub-screens (small-multiple by domain),
   beats-random cells marked; where the conditioned signed favourable MFE exceeds the matched (regime-matched
   for `/VOLREGIME`) control.
2. **Regime split panel** — `CORE` vs `CORE-VOL-{LOW,MED,HIGH}`: per-cell `MFE_med(signal)` and `Δ̂_rand` vs the
   **regime-matched** control, beats-random cells marked. This is the amended visual of *does the MR edge depend
   on the regime* — read directly from which regimes pass, **with the C-1 denominator confound removed** (signal
   and control share the regime).
3. **Per-sub-screen `S` vs `S*`** — the 6 realized `S` with each sub-screen's own `S*` and the joint `S*`
   overlaid, the argmax highlighted; the per-stratum transparency view (LESSON-001).
4. **Joint permuted-axis null distribution** — histogram of `S_perm_max` with realized `S_fam`, `S*` (Q95), and
   the FWER-band thresholds overlaid; this *is* the admission decision.

All plots from the single analysis pass's bounded summaries (and the bounded per-event/per-regime arrays for
plot 2) — no data reloads or re-generation for plotting.

## Interpretation Guide (pre-defined, before results exist)

The experiment verdict is about completeness + integrity; the **admit/exonerate is G-020**. EXP-089 reports a
**provisional, NON-BINDING** disposition under the (amended) D5 rule.

- **`SCREEN_DELIVERED`** iff, for all 6 sub-screens across all 46 member cells, the per-cell `MFE_med` and
  Δ-tables, the per-cell beats-random test, the per-sub-screen `S`/`S*`/perm-p, the family `S_fam`/`S*`/axis-p,
  the FWER band, the MC-stability table, the cap-distribution disclosure, and the descriptive D2a band are
  produced; determinism passes; matched-random (count/direction/regime) reconciliation holds; holdout untouched —
  *whatever* the numbers look like.
- **Provisional `ADMITTED (NON-BINDING — pending G-020)`** iff `S_fam > S*` **and** axis `perm_p ≤ 0.05`. Record
  **which** sub-screen drove it: a **`/VOLREGIME`** drive ⇒ the MR edge is **regime-dependent** (clean
  regime-matched leg-1 in that regime); a **CORE** drive ⇒ bare mean-reversion; a **variant** drive ⇒ the native
  toggle. The argmax + `z_ss` ranking names the lever G-020 would open first.
- **Provisional `EXONERATED (NON-BINDING — pending G-020)`** iff every sub-screen's `S` falls within the D2a null
  band — the single-series-directional cell is then provisionally dead under mean-reversion too (terminal-frontier
  input to G-020).
- **`INCONCLUSIVE`** iff the joint permuted null cannot separate at the realized powered-cell count (no power) —
  disclosed; neither admit nor exonerate.
- **HALT (process-level, route to `experiment-developer`)** iff *any*: second-pass statistics differ
  (non-determinism); a real-price/look-ahead/holdout-fence violation; or a matched-random / regime-membership
  reconciliation break. Implementation bugs, not data shapes.
- **Descriptive disclosures (reported, NON-BINDING):** the D2a cells-beat-random count per sub-screen vs the
  coin-flip band Binomial(46,0.5) ≈ [17,29] and the beats-random noise ceiling Binomial(46,0.05) Q95 ≈ 5; the
  cross-sub-screen `S` comparison (does conditioning on a regime raise `S` over bare CORE — *descriptive*, since
  cross-sub-screen comparison is disclosure not verdict). `NOT_ADMITTED ≠ EXONERATE`: `S` **below** the D2a band
  is dead-by-absence, not exonerated-by-coin-flip (EXP-087 LESSON).
- **Prior (stated, does not move goalposts):** the programme-level null is **availability ≈ random**; no prior
  family's outcome — including the **voided deviation run** — is imported as a biasing expectation. The analysis
  reads the realized numbers on their own terms.
- **No goalpost movement:** the entry definition (RSI 2/10/90), variant toggles, the regime rule
  (ATR14/window50/33-66), the ≥15 floor, the **MR-tempo cap constants** (`K_MULT=1.0`, `W=20`, `MIN_EPISODES=5`,
  `FLOOR=3`, `CAP_MAX=40`, close at RSI 50), the regime-matched control, the gate constants (`Z=1.645`, `S*=Q95`,
  FWER band, `N_PERM=5000`), and the joint-max-of-6 single-test no-Holm rule are frozen by D0 + `D0-amendment-001`
  + this plan; G-020 freezes the *rule*, not the story the numbers tell.

## Implementation Safety Constraints (for `experiment-developer`)

- **RUN PRECONDITION (amended):** the gate is the **single-test joint-max-of-6** already GREEN at sha
  `f01a000b…`; **no bite extension or re-confirmation is required**. Ensure `bite_check.py` is at the single-test
  `f01a000b…` scope (the leg-2 extension is moot/dropped) and the D0/scope sha reference points to `f01a000b…`.
  Integrity of the MR-tempo cap and regime-matched control is enforced by the Step-7 reconciliation guards, not
  by the gate bite.
- **Sectioning:** imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration →
  `main()` (VAL-001-style). No directory creation / file writes / data loads / plotting at import time.
- **Temporal ordering:** all ordering/alignment by `CloseTime`/epoch, never bar index; assert `CloseTime` sorted
  after slicing. RSI(2)/RSI(5)/EMA(20)/ATR(14), the rolling-50 regime percentile, **and the reversion-episode
  tempo** are sequential/causal (use only bars `≤ i`; the percentile uses only the trailing 50 completed bars;
  the cap median uses only episodes closed strictly before `t_i`).
- **Holdout discipline:** read only the first `train_cutoff` 1-minute rows
  (`train_cutoff = int(int(total_rows·0.7)·0.7)`); locate the split via Parquet metadata only; never materialize
  a row at/beyond `analysis_rows`; forward path windows clip at `train_edge_idx`; the random pool, the
  (regime-matched) `SUB-RANDOM` draw, and the episode tempo all draw only from `[0, train_edge_idx]`.
- **Real-price discipline:** every `MFE`/`ATR`/regime/episode figure on real domain OHLC
  (`RealOpen/High/Low/Close`). No HA/Renko synthetic-price metric anywhere (D6).
- **Reuse, don't edit:** `xen.domain_bars` (`build_domain_bars`), `xen.capgeo_substrates` (`random_entries`,
  `_real_ohlc`, `ATR_PERIOD`, `EntrySet`), `xen.capgeo_geometry` (`lifetime_path_geometry`),
  `xen.availability_gate` (`CellReadInput`, `cell_se`, `run_sub_screen`, `combine_axis`), `xen.ass`
  (`default_block_length`), `xen.zigzag` (`wilder_atr`) — all unchanged. **`xen.expectancy.adaptive_time_caps_by_epoch`
  and `_ma_segment_moves` are NO LONGER USED** by EXP-089 (replaced by the MR-tempo cap).
- **New code only in two modules (≤2):** **`xen.mean_reversion`** — Wilder `RSI(2)`/`RSI(5)`, `EMA(20)`, the
  RSI-MR entry generator (long/short + TREND/RSI-FILTER toggles), **and the causal reversion-episode duration /
  MR-tempo cap** (RSI-2 episodes → per-entry cap; close at RSI 50). **`xen.vol_regime`** — **reduced to** the
  `ATR(14)` causal rolling-50-percentile regime labeller (`regime_labels`) and a **regime-matched random-draw /
  pool helper** (restrict `random_entries` to same-regime candidate bars). **REMOVE** `beats_core_se`,
  `_regime_perm_conjunction`, `run_regime_sub_screens`, `RegimeCellInput`, and the `B_SE`/`PERM_BATCH`/`FWER`/
  `STAT_MEDIAN`/`Z_ONE_SIDED`/`CellReadResult`/`SubScreenResult` imports they required. All 6 sub-screens now
  route through `run_sub_screen`.
- **Denominators / zero-baseline:** beats-random denominators = per-cell usable-event counts (disclosed: signal,
  matched-random; per-regime where applicable); `MAD=0`/single-event sets flagged `degenerate` (never `0/0`);
  warmup / ATR-undefined / clipped-empty / regime-warmup / tempo-warmup counted and excluded (never folded into
  a statistic); permuted-p uses the `(1+·)/(1+N_PERM)` add-one form; no metric as a percentage over a zero
  baseline; ≥15-event floor (no upper bound).
- **Bounded iteration / progress / performance:** `tqdm` over the (cell × sub-screen) outer loop; the random
  pool computed **once** per (cell, sub-screen); permutations draw a with-replacement subsample — **no
  per-permutation path scan**; per-cell memory bounded (do not retain all domain frames); `N_PERM=5000`,
  `N_PERM_STABILITY=1000`, `B_SE=2000`; all seeds + cap constants in `run_metadata.json`.
- **Vectorization discipline:** vectorize intra-window max/argmax (module-internal) and the
  subsample-and-aggregate inner loop with NumPy; keep the outer event loop and every causal step
  (RSI/EMA/ATR/percentile recurrences, episode tempo, cap-by-index) explicit — no transformation that changes
  sample membership, temporal ordering, denominators, metric definitions, or causal/streaming semantics. The
  null preserves per-cell count + direction (and regime, via the regime-restricted pool) by construction.
- **Outputs:** `results/cell_availability.parquet`/`.csv` (per cell × sub-screen: `MFE_med` signal/random,
  `Δ̂_rand`, `s_rand`, `ci_low_rand`, `beats_random`; `n_signal`, `n_rand`, cap-distribution fields,
  `degenerate`, `underpowered`/`COVERAGE_EXCLUDED`; **no** `delta_core`/`beats_core`/`pass_conjunction`);
  `results/family_admission.json` (per sub-screen `S`/`S*`/perm-p/`z_ss`; family `S_fam`/`S*`/axis-p/`rank_z`/
  argmax; FWER band; MC-stability 1000-vs-5000; provisional disposition captioned **NON-BINDING pending
  G-020**); `results/per_event_geometry.parquet` (bounded, for plot 2; signal + regime-matched control signed
  MFE with regime label); `results/run_metadata.json` (seeds, MR-tempo cap constants, module hashes, frozen
  constants, bite report sha256 `f01a000b…`, `determinism_ok`/`recon_all_ok`/`regime_match_recon_ok`/
  `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`); the ≤4 plots under `plots/`.

## Complexity Check

- **Binding statistical tests: 1 / 1** — the D2b joint-max permuted-axis admission gate (`combine_axis` over 6
  single-test sub-screens). Descriptive companions (not counted): the per-cell `Δ̂_rand` moving-block-bootstrap
  lower bound and the descriptive D2a band. No leg-2 conjunction (retired); no dip test / magnitude-budget
  (directional family; magnitude is the closed CF-VOLEXP-001 surface, not reopened).
- **Visualisations: 4 / 4.**
- **New modules: 2 / 2** — `xen.mean_reversion` (now incl. the MR-tempo cap), `xen.vol_regime` (reduced to the
  labeller + regime-matched draw). All other logic reuses existing frozen modules; `bite_check.py` stays at the
  single-test `f01a000b…` scope (not a new `xen.` module).
