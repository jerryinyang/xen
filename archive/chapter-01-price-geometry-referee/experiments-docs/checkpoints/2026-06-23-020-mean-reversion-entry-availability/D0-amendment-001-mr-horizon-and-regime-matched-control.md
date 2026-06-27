# Phase 020 D0 — Amendment 001 (MR-tempo horizon + regime-matched control; leg-2 retired)

**Date:** 2026-06-23 · **Status:** RATIFIED (operator-directed) · **Supersedes (in part):**
`D0-predeclarations.md` D1 (control), D2b (per-cell test + regime null), D3 (endpoint cap), D5 (verdict rule),
and the `xen.vol_regime` leg-2 machinery. **Authority:** the D0 freeze clause — "No further amendment without a
dated `D0-amendment-*` file in this directory." This is that file.

**Scope of amendment:** unchanged single falsifiable question (CF-MR-001 mean-reversion entry **availability**;
6 sub-screens; 46 cells; TRAIN-only; **0 slots, 0 counted TEST reads, holdout sealed**). What changes is the
**operationalization** of the availability endpoint and its control — not the question, the member set, the
multiplicity budget, or the registry. No new countable item; the multiplicity-registry Phase-020 batch is
unchanged (still the same 6 sub-screens). The experiment ID **remains EXP-089** (the first run is voided, below).

---

## 0. Why this amendment exists — the deviation found at audit

The first EXP-089 run (`SCREEN_DELIVERED`, provisional **ADMITTED**, `S_fam=27` driven entirely by
CORE-VOL-LOW, axis perm-p≈0.0002) was audited and found to rest on **two verdict-material confounds**
(`python/experiments/EXP-089/audit.md`, findings C-1 and C-2). Both are properties of the **frozen D0 design**,
not code bugs — a rerun of the identical code reproduces the artifact. The run is therefore a **deviation**: its
numbers cannot be carried to G-020 and would contaminate the family disposition and the signal registry if
retained. They are **voided and hard-deleted** (§4).

- **C-1 — ATR-normalization confound (binding stratum).** The endpoint normalizes forward favourable excursion
  by **entry-bar ATR(14)**, and the `/VOLREGIME` label *is* the entry-bar ATR percentile. Volatility
  mean-reverts over the forward window, so LOW-regime entries divide a normal-vol forward move by a depressed
  denominator (inflated MFE) and HIGH by an elevated one (deflated). The realized numbers are the signature: a
  symmetric, monotone, **baseline-independent** ladder (LOW +0.55 / MED ≈0 / HIGH −0.52 ATR), with leg-1 (vs
  all-bars random) ≈ leg-2 (vs pooled CORE), universal across ~91% of cells. The original control was **not**
  regime-matched (D1 argued ATR-normalization made matching unnecessary — an argument that overlooked forward
  vol mean-reversion). The leg-2 conjunction + regime-membership null are **structurally blind** to this
  confound (shuffling labels destroys exactly the entry-ATR↔label correlation that drives it), so its z=115 is
  the strength of a structural label-correlate, not a tradable edge.

- **C-2 — horizon / construct mismatch.** The endpoint measured MFE over the **trend-length adaptive cap**
  (`adaptive_time_caps_by_epoch`: `max(6, round(1.5 × median of last 20 MA(20,50)-segment durations))`, typical
  caps ~30–100 bars). RSI-2 mean reversion is a **1–5 bar** phenomenon. MFE is monotone increasing in horizon,
  so over a trend-length window the credited "favourable availability" is dominated by **post-reversion forward
  drift**, not the reversion bounce — i.e., the first run tested a *different strategy* than the MR family it
  claims to screen. The long window also maximizes the time for vol to revert, compounding C-1.

## 1. Amended D3 — availability endpoint over a **causal MR-tempo cap** (replaces the trend cap)

The favourable-excursion endpoint is retained (entry-signed `MFE_med`, ATR(14)-normalised, real OHLC), but the
measurement window is replaced by a **causal mean-reversion-tempo cap** matched to the family's actual holding
horizon:

- **Reversion episode (tempo source, per cell, causal):** a long episode opens at a bar with `RSI₂ < 10` and
  closes at the first later bar with `RSI₂ ≥ 50`; a short episode opens at `RSI₂ > 90` and closes at the first
  later bar with `RSI₂ ≤ 50`. Episode **duration** = `close_idx − open_idx` (domain bars). Defined on the full
  causal RSI-2 series; only episodes whose close is **strictly before** an entry contribute to that entry's cap.
- **Per-event cap:** `cap_i = clamp(round(K_MULT × median(durations of the last W completed reversion episodes
  closed strictly before t_i)), FLOOR, CAP_MAX)`. Fewer than `MIN_EPISODES` completed episodes before `t_i`
  → **warmup**, event excluded and disclosed (never silently capped).
- **Constants** `{K_MULT, W, FLOOR, MIN_EPISODES, CAP_MAX}` are pinned, **justified, and frozen pre-data** by
  the amended analysis-plan (Stage 2). Recommended anchors mirroring the retired cap's structure: `K_MULT=1.0`,
  `W=20`, `MIN_EPISODES=5`, a small `FLOOR` (e.g. 2–3 bars), `CAP_MAX` a generous guard only. **No tuning
  against realized availability.** The cap basis recorded in `run_metadata.frozen_constants.cap_basis` changes
  from the MA-segment tempo to the RSI-2 reversion tempo.
- **Look-ahead:** the cap at `t_i` uses only episodes confirmed strictly before `t_i`; the path is read over
  `[entry+1, entry+cap]` clipping at the TRAIN edge. Causal and streaming-safe.

## 2. Amended D1/D2b control — **regime-matched, horizon-matched; leg-2 retired (leg-1 only)**

- **Regime-matched random control (fixes C-1).** For the three `/VOLREGIME` sub-screens the matched-random
  control is drawn **from same-regime bars only** (random timing restricted to bars carrying that regime label),
  matched on **count and direction** within the cell. Because signal and control now share the regime — hence
  the entry-ATR distribution — the ATR(14) denominator **cancels within the comparison**, removing C-1. `CORE`
  and the two variant sub-screens keep the established **all-bars** count+direction-matched `SUB-RANDOM` (no
  regime conditioning applies to them).
- **Horizon parity by construction.** The MR-tempo cap rule (§1) is applied **identically** to signal and
  control entries (the cap is a cell-level causal clock evaluated at each entry's timestamp), so both arms are
  measured over the same horizon rule — full parity (count + direction + regime + horizon) **without**
  resampling. (The analysis-plan confirms this is causally equivalent to, and simpler than, resampling the
  signal's realized cap distribution.)
- **Leg-2 retired.** The binding **beats-CORE conjunction** (`Δ̂_core`), the **regime-membership-shuffle null**,
  and the associated `xen.vol_regime` machinery (`beats_core_se`, `_regime_perm_conjunction`,
  `run_regime_sub_screens`) are **removed**. With a clean regime-matched leg-1, "the regime adds availability the
  unconditioned entry lacks" is read **directly** from *which regimes' leg-1 passes* (e.g. LOW passes, MED/HIGH
  do not) — no confounded additive statistic is needed. **All 6 sub-screens become single-test leg-1**
  (`Δ̂_rand = MFE_med(signal) − MFE_med(matched control)`, one-sided lower bound > 0) routed through
  `xen.availability_gate.run_sub_screen` **unchanged**, with the standard signal-shuffle null (preserving
  per-cell count + direction; for regime sub-screens the pool is the regime-restricted random pool).

## 3. Amended D2b/D5 — gate and verdict rule (single-test across all 6)

- **Per-sub-screen `S` (all 6):** `S_ss = #cells beats-random` (powered cells only). No conjunction anywhere.
- **Family statistic / gate (unchanged machinery):** `S_fam = max_sub S_ss`; **joint-max-of-6** permuted-axis
  null via `combine_axis` (shared permutation index), `S* = Q95`, axis perm-p. **`ADMITTED iff S_fam > S* AND
  axis perm_p ≤ 0.05`** (FWER 0.05, no cross-axis Holm — single family). `INCONCLUSIVE` iff the joint null
  cannot separate at the realized cell count. The argmax sub-screen names the lever (bare MR / a vol regime / a
  variant); a regime "wins" by passing **clean regime-matched leg-1**, not by inheriting CORE.
- **Bite-check.** Retiring leg-2 returns the gate to the **single-test joint-max-of-6** structure already
  proven **GREEN** at sha `f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65`
  (D0-predeclarations checks A/B/C/D: noise→EXONERATED, planted→ADMITTED with power, joint-max restores FWER to
  0.043, MC-stable). The extended leg-2 bite (`07cec052…`) is **moot** under this amendment. The amended
  analysis-plan re-confirms the single-test bite still anchors `N_PERM=5000` / `Q95` for the 6-single-test
  structure; the MR-tempo cap and regime-matched control are **upstream geometry** (they produce the MFE arrays)
  and do not change the gate's null calibration.

## 4. Disposition of the first (deviation) run

- The first-run artifacts under `python/experiments/EXP-089/results/` and `python/experiments/EXP-089/plots/`
  (`cell_availability.{csv,parquet}`, `family_admission.json`, `per_event_geometry.parquet`,
  `run_metadata.json`, the 4 plots) are **hard-deleted** — they are a deviation and would contaminate the G-020
  read and the registry if retained. The forensic record of *what they showed and why they are void* is
  preserved in `audit.md` (C-1/C-2) and in §0 here.
- `audit.md` is annotated **VOID — superseded by amendment-001**; a fresh audit follows the rerun.
- No registry or ledger change: still 0 slots, 0 counted TEST reads, all 48 strata 0/2 open; holdout sealed.

## 5. Unchanged (still frozen from D0)

Entry RSI-2 (10/90), variant toggles (EMA-20 TREND, RSI-5 50-cross FILTER), the `/VOLREGIME` labeller (ATR-14
causal rolling-50 percentile, 33/66, per-(instrument,domain), past-bars-only), the 46-cell member set
(US500-4h/JP225-4h `COVERAGE_EXCLUDED`), the `EVENT_FLOOR=15` / no-upper-bound coverage bracket, `N_PERM=5000`,
FWER 0.05, master seed `20260623`, determinism + real-price discipline, and the TRAIN-only disclosure
accounting (D4) are **unchanged**. No parameter is tuned against TEST/holdout.

## 6. Required downstream actions (this amendment triggers a full re-run of the pipeline for EXP-089)

1. Banner `D0-predeclarations.md` and `scope.md` pointing here (done with this amendment).
2. **Stage 2 — analysis-plan.md** revised (`experiment-quant-analyst`): pin + justify the MR-tempo cap
   constants; specify the regime-matched control draw and its SE; confirm horizon parity without resampling;
   define the 6 single-test sub-screens and the joint-max gate; restate the verdict rule.
3. **Stage 3 — code** revised (`experiment-developer`): replace the cap with the causal MR-tempo cap; add the
   regime-restricted matched-random/pool draws; remove the leg-2 conjunction + regime-null machinery from
   `xen.vol_regime` (keep `regime_labels`); route all 6 sub-screens through `run_sub_screen`.
4. **Stage 4 — pre-execution governance** re-run; then the manual execution gate (operator runs the rerun).
5. **Stages 5–8** — fresh audit, interpretation, documentation, post-experiment governance on the rerun.
