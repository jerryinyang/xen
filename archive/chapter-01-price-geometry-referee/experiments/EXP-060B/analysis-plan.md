# Analysis Plan: EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact?

**Scope:** `python/experiments/EXP-060B/scope.md` (read in full).
**Forks:** `python/experiments/EXP-060/code/run_experiment.py` (the entire per-cell pipeline) and reuses
`python/experiments/EXP-060/scope.md` conventions.
**Binding endpoint (unchanged, P14):** median per-event position-weighted gross expectancy (ATR-normalised,
P15 fills), regime-clustered moving-block bootstrap, CI_low_1s > 0, ≥30 events, P11-composed. The **mean** is
the P14-sanctioned disclosed secondary and the central characterisation lens (the median≫mean skew is the
object under study). No new binding gate contradicts P14 — see §6.
**Stratum:** TRAIN only (first 70% of first-70%), 99-cell member grid; population byte-identical to
EXP-053/060; TEST + final-30% holdout never read.

> **Implementation correction (2026-06-17, Stage-3/4; surfaced at first execution).** Method 3
> below and §6 describe the `M3 − RM3` (and disclosed `Z3 − RZ3`) discriminator as a **paired**
> contrast (`paired_median_contrast_ci`) "on the common qualifying subset." That is methodologically
> impossible here: the harami signal arm (M3/Z3, indexed over haramis) and its **matched-random**
> control (RM3/RZ3, indexed over *disjoint* random in-regime draws that explicitly **exclude** the
> signal bars) share **no** per-event subset and have different lengths — a paired contrast raised a
> shape-mismatch at runtime. The discriminator is therefore computed with the **independent**
> bootstrap contrast `xen.expectancy.contrast_ci` on the stored median (binding) and mean (disclosed)
> bootstrap distributions — which is *exactly* the plan's stated intent ("**mirror EXP-060's own
> champion-vs-random test**"): EXP-060 computed `beats_random` as `contrast_ci(sig.dist,
> matched_random.dist)`. Independent is the correct method for disjoint, independent samples (and is
> the more conservative one). Net method count drops to **3** (median CI; mean CI; independent
> `contrast_ci`, used for both the binding M3−RM3 discriminator and the disclosed P13-baseline
> continuity) — within the budget of 4. The binding *semantics* (does M3 beat its own matched-random
> at the median, CI_low>0) are unchanged. All other Method-3/§6 statements stand.

---

## 1. Question → measurement map

EXP-060 returned `CHARACTERISED_NOT_VIABLE_ELIGIBLE` with its closure resting on MA(20,50) median dominance
read as a real substrate edge. EXP-060B adjudicates that read via three diagnostics, all on the binding
`/STRONG-STAT` conditioned HA harami:

| Diagnostic | Sub-question | Object measured |
| --- | --- | --- |
| **D1 skew** | Does the MA champion (M3) have median ≫ mean like the ZigZag champion (Z3)? Which lever (V2A capped upside vs `/ADV-NONE` uncapped downside) drives it? | Per-cell **median** and **mean** (each bootstrap-CI'd) for the 8 signal arms {Z3,Z2,Z1,Z0,M3,M2,M1,M0}; gap `median−mean`; ADV-NONE-vs-1:1 attribution. |
| **D2 redundancy (binding discriminator)** | Does the MA-substrate harami beat a matched-random control **on the MA substrate**? | `M3 − RM3` paired-median contrast (binding); `M3 − RM3` paired-mean contrast + `Z3 − RZ3` (disclosed). |
| **D3 mechanism** | Is MA also TIMECAP-dominated (the EXP-060 trap, Z3 ≈ 64% TIMECAP) or does it convert weight to FAV? | Exit-reason composition (weight via each V2A leg / 1:1 stop / time cap) for Z3 vs M3 vs the nulls. |

The 10 measured objects (8 signal arms + 2 matched-random nulls) and their construction are fixed in the scope
(`Predeclared object set`). RM3 (`V2A-NONE-MA-random`) is the **one genuinely new computation**; everything
else is EXP-060 machinery, with MA mean + MA exit-composition now emitted (EXP-060 dropped them).

## 2. Statistical methods (4 — within the scope budget)

All resampling is the regime-clustered **moving-block bootstrap** already used in EXP-053–060
(`block_len = round(m^(1/3))`, `N_BOOT = 10_000`, fixed per-cell/per-purpose seed), so dependence structure is
preserved identically. Methods 2 and the mean-variants of method 3 are the **same machinery applied to a
different statistic** — not new methods (exactly the precedent set by EXP-060's `interaction_ci`).

### Method 1 — Per-cell median CI (binding; existing)
- **Question:** is an arm's median expectancy > 0 per cell?
- **Tool:** `xen.expectancy.bootstrap_median_distribution` + `median_ci` (via `_summarize_arm`, byte-identical
  to EXP-060 — see reproduction invariants §7).
- **Sufficiency / simpler alternative:** the median is the P14 endpoint; a simpler point estimate gives no
  uncertainty. **Assumption:** weak dependence beyond `block_len`; appropriate for time-ordered returns and
  identical to the established 014-B standard.
- **Output:** per cell × arm: `median`, `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, viability flag.

### Method 2 — Per-cell mean CI (disclosed; the skew readout — new statistic, same machinery)
- **Question:** is an arm's **mean** expectancy > 0 per cell, and how far below the median does it sit?
- **Tool:** a local `bootstrap_mean_distribution` helper that reuses the **identical** moving-block index
  construction as `bootstrap_median_distribution` but applies `np.mean` per resample, then a `mean_ci`
  (5th / 2.5th / 97.5th percentiles). Implemented in the experiment code (not a new `xen/` module) and drawn
  from a **dedicated RNG purpose** so the median path's RNG stream is untouched (reproduction safety, §7).
- **Sufficiency / simpler alternative:** the mean is the quantity the capped-up/uncapped-down geometry
  distorts; a parametric (t) interval is rejected — the no-stop left tail is fat and asymmetric, violating
  normality. The block bootstrap is distribution-free and consistent with the programme's non-parametric
  default. **Assumption / caveat:** the mean is tail-sensitive, so its CI will be **wider** than the median's
  and may be the binding power constraint — this is informative (it quantifies the skew), not a defect.
- **Output:** per cell × arm: `mean`, `mean_ci_low_1s`, `mean_ci_lo_2s`, `mean_ci_hi_2s`, mean-viability flag,
  and `gap = median − mean`.

### Method 3 — Paired contrast CI (binding for M3−RM3; existing machinery)
- **Question:** does the MA-substrate harami beat its own matched-random control (D2)?
- **Tool:** `xen.favourable_targets.paired_median_contrast_ci` on the **common qualifying subset**, entry-index
  ordered (via the existing `paired_contrast` wrapper). Binding: `M3 − RM3` (median). Disclosed: `Z3 − RZ3`
  (median, the ZigZag analog that reproduces EXP-060), and the **mean** variants of both (same paired
  moving-block construction with `np.mean`).
- **Sufficiency / simpler alternative:** a paired design controls for the common-event matching between the
  harami arm and its random control; an unpaired contrast would inflate variance. **Assumption:** common-subset
  pairing is meaningful — yes, because matched-random shares the cell/regime/direction context by construction.
- **Output:** per cell: `m3_rm3_median_low_1s` (+ 2s bounds, common_m), `m3_rm3_mean_low_1s` (disclosed),
  `z3_rz3_median_low_1s` (disclosed).

### Method 4 — Independent contrast CI vs P13 baselines (disclosed context; existing)
- **Question:** for continuity with EXP-060, how do the arms sit vs the two registered P13 baselines?
- **Tool:** `xen.expectancy.contrast_ci` on the bootstrap distributions (as `_arm_record` in EXP-060).
- **Sufficiency:** disclosed-only continuity; not part of the verdict fork.
- **Output:** `contrast_random_low`, `contrast_ma_low` per arm (reproduces EXP-060 columns).

**Descriptive (always included, not counted):** per-arm `m`, `win_rate`, `data_censored`/warmup counts,
exit-reason weights, single-leg first-hit `r`, and the **median−mean gap** tables and ADV-NONE-vs-1:1
attribution (descriptive comparison of per-cell gaps; no formal 5th test).

## 3. RM3 construction (the one new computation) — precise specification

RM3 mirrors EXP-060's `matched_random_arm` but on the **MA substrate**, so the developer implements
`ma_matched_random_arm` by substituting the MA segmentation everywhere `matched_random_arm` uses ZigZag `mv`:

1. **MA in-progress state over all bars:** `state_all_MA = live_in_progress_state(ohlc.epoch, ohlc.close,
   seg.confirm_epoch, seg.end_price, seg.end_epoch, seg.direction)` where `seg = ma_segment_moves(ohlc)`
   (identical to `ma_seg_arm`). MA warmup via `adaptive_time_caps_by_epoch(..., seg.confirm_idx)`.
2. **Non-signal eligible pool:** `eligible = state_all_MA.valid & (m_sofar>0) & isfinite(atr_all) & (atr_all>0)
   & ~warmup_all_MA`, **excluding the MA-conditioned harami entries** (the M3 qualifying set:
   `entry_idx[stat.retained_p75]` under the MA state) — the MA analog of EXP-060's `signal_idx` exclusion.
3. **Matched count:** `draw_count = M3.m` (the MA champion's qualifying count), exactly mirroring EXP-060's
   `draw = stat_arms[a.aid].m` convention — so RM3 controls M3, not Z3. (Note MA qualifies ≈3–4× more events
   than ZigZag; the pool is correspondingly larger.)
4. **Resolve:** `benchmark_barriers` + adaptive cap from the drawn entries' MA sub-state, then `resolve_arm`
   with the V2A×ADV-NONE×cap config — identical exit pipeline to M3.
5. **Dedicated RNG purposes:** new `PB_*` constants for the RM3 draw and bootstrap so **no existing EXP-060 RNG
   stream shifts** (reproduction safety).

## 4. Plots (5 — within budget; from collected per-cell summaries, no reloads)

1. **Median vs mean, per arm × substrate** (8 arms × {ZZ, MA}): paired markers with CI whiskers; **M3 and Z3
   highlighted.** Answers D1 headline — is M3 a median-only mirage?
2. **median−mean gap by arm, grouped by adverse model** (ADV-NONE: Z3,Z1,M3,M1 vs 1:1: Z2,Z0,M2,M0), both
   substrates. Answers D1 attribution — is uncapped downside the entry-agnostic skew source?
3. **`M3 − RM3` paired-contrast forest per cell** (median CI_low, sorted), with `Z3 − RZ3` overlaid disclosed.
   Answers D2 — does the harami beat random on MA?
4. **Exit-reason composition Z3 vs M3** (stacked TIMECAP / FAV-legs / ADV / DATA_CENSORED) by domain, with the
   two nulls. Answers D3.
5. **MA-substrate viability map** across the 99 cells: per-cell status {median-viable, beats-RM3, mean-viable,
   lead-cell} grid/heatmap. The artifact-vs-lead picture feeding the verdict.

## 5. Output artifacts (`results/`)

`per_cell_expectancy.parquet` (per cell × arm: median+mean & CIs, gap, exit weights, m, censoring/warmup, win
rate, viability flags); `skew_map.csv` (D1); `ma_control_map.csv` (D2: M3 vs RM3 median+mean contrasts, M3
median/mean viability, per-cell lead flag + P11 tally); `exit_reason_map.csv` (D3: Z3/M3/RZ3/RM3);
`secondary_map.csv` (`/STRONG-HA` rerun of M3/Z3, single-leg `r`, P13-baseline contrasts);
`composition_readout.json` (the verdict fork → G2 input); `population_reconciliation.csv` (Z3↔EXP-060 A3 and
M3↔EXP-060 `maseg_median` exact); `run_metadata.json` (seeds, frozen constants, EXP-060 source paths/hashes).

## 6. Interpretation criteria (predefined — before results exist)

**Per-cell flags** (binding `/STRONG-STAT`, `m ≥ 30`):
- `m3_median_viable` = M3 median `ci_low_1s > 0`
- `m3_mean_viable` = M3 mean `ci_low_1s > 0`
- `m3_beats_rm3` = `(M3 − RM3)` paired-**median** contrast `ci_low_1s > 0`
- `m3_lead_cell` = `m3_median_viable ∧ m3_beats_rm3 ∧ m3_mean_viable`

**P11 composition** = ≥5 cells over ≥3 instruments.

**P14 posture (no goalpost move):** the binding viability remains the **median**. The mean and the
matched-random control are used only to make the "lead" criterion **stricter** (conservative — they can block
a false lead, never manufacture one). This is consistent with P14: we never declare a candidate viable *on*
the mean.

| Verdict | Mechanical condition | Meaning / G2 consequence |
| --- | --- | --- |
| **SUBSTRATE_LEAD_FOUND** | `m3_lead_cell` composes P11 (median-viable **and** beats RM3 **and** mean-viable, ≥5 cells/≥3 instruments). | Genuine MA-conditioned harami lead. G2 must **not** close CF-HA-HARAMI-001 without a new scoped MA-substrate experiment (registration there, never here). |
| **ARTIFACT_CONFIRMED** | `m3_median_viable` composes P11 (MA dominance is real at the median, as EXP-060 saw) **AND** the lead fails — i.e. `m3_mean_viable` fails P11 **(skew)** **and/or** `m3_beats_rm3` fails P11 **(redundancy)**. | MA dominance is a capped-up/uncapped-down left-skew and/or entry-redundant artifact. EXP-060 `CHARACTERISED_NOT_VIABLE` strengthened. Sub-flag records which (skew / redundancy / both). |
| **INCONCLUSIVE** | M3 or RM3 fails to reach the P11 quorum at ≥30 events (power-limited), no correctness failure; **or** `m3_median_viable` itself fails P11 in a way inconsistent with EXP-060 (investigate as possible reproduction issue before concluding). | Record; new scope for follow-up. |
| **SUBSTRATE/METHOD_DEFECT** | Any reproduction/determinism/causality/invariant failure (§7). | Fix before reporting; no G2 input until clean. |

**D1 attribution (descriptive sub-readout):** the skew is attributed to the **uncapped downside (`/ADV-NONE`)**
if the pooled per-cell `median−mean` gap for ADV-NONE arms (Z3,Z1,M3,M1) materially exceeds that for 1:1 arms
(Z2,Z0,M2,M0) with consistent sign across cells, on **both** substrates (entry-agnostic). Reported as
characterisation; never enters the verdict.

## 7. Implementation safety constraints (for `experiment-developer`)

- **Reproduction (binding invariants):** (i) **Z3** median, qualifying count, and exit-reason composition
  reproduce EXP-060 A3 (`V2A-NONE`) to float tolerance; (ii) **M3** median reproduces EXP-060's
  `maseg_median` for `V2A-NONE` exactly; (iii) population reconciliation vs EXP-060 exact for all signal arms.
  Achieve this by **not perturbing existing RNG streams** — the mean bootstrap and RM3 use **new dedicated
  `PB_*` purposes**; the median path stays byte-identical.
- **Causality:** M3, RM3, and all MA arms construct the MA in-progress state, `M_sofar`, barriers, and caps
  from **only pre-entry confirmed MA crossovers** (`live_in_progress_state` / `adaptive_time_caps_by_epoch` on
  `seg`, the trailing `_sma`); extend EXP-060's `_causality_ok` gate to the MA arms and RM3. No exit references
  a future bar; forward scan `[entry_idx+1, min(entry_idx+N, last_train_idx)]`, `CloseTime ≤ train_end_ts`.
- **Invariants:** leg weights sum to 1.0; the `/ADV-NONE` sentinel **never** fires an `ADV` exit on
  Z3/Z1/M3/M1/RZ3/RM3 (only FAV/TIMECAP/DATA_CENSORED); the shared 1:1 stop (Z0/Z2/M0/M2) closes all open legs
  at the same bar/level; **matched count** `RM3.draw_count == M3.m`; every exit price is a real-bar P15 fill.
- **Mean bootstrap:** identical moving-block construction to the median path (`block_len = round(m^(1/3))`,
  `N_BOOT = 10_000`); compute only when `m ≥ POWER_FLOOR (30)`; `np.mean` per resample; dedicated RNG.
- **Zero-baseline / power:** `m < 30` → NOT_VIABLE-by-power for that arm/metric (median **and** mean), never an
  undefined or infinite ratio; depleted cells disclosed, never defaulted.
- **Determinism:** second full pass byte-identical, including the new mean distributions and RM3.
- **Real-price discipline:** detection on HA candles; MA(20,50) on **real close**; every metric on real-price
  OHLC. No HA price in any metric.
- **Performance / housekeeping:** `tqdm` over the 99-cell grid; lazy Polars TRAIN-prefix slicing (never sort or
  collect the full file; never read TEST/holdout); per-cell bounded memory (retain `r_e_all`/`qual`/`dist` per
  arm as EXP-060 already does for the paired contrasts; do not retain all bootstrap draws beyond what the
  contrasts need); output directories created only in orchestration; no heavy reload for plotting.

## 8. Complexity budget check

- **Statistical methods: 4** ✓ (median CI; mean CI [same machinery, new statistic]; paired contrast
  [median binding + mean/Z3−RZ3 disclosed]; independent baseline contrast). Consistent with EXP-056–060.
- **Visualisations: 5** ✓ (§4).
- **New code modules: 0 new `xen/`** ✓ — local helpers only (`bootstrap_mean_distribution`/`mean_ci`,
  `ma_matched_random_arm`) inside `code/run_experiment.py`, forking EXP-060. Within the scope's "≤1 thin
  wrapper" allowance.
