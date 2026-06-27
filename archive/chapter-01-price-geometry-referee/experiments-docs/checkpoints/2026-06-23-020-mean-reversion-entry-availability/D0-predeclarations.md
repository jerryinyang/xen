# Phase 020 D0 — Predeclarations (CF-MR-001 Mean-Reversion Entry Availability Screen)

> **AMENDED — see `D0-amendment-001-mr-horizon-and-regime-matched-control.md` (2026-06-23).** The first EXP-089
> run was a deviation (audit C-1 ATR-normalization confound + C-2 trend-length horizon mismatch). The amendment
> supersedes **D1 (control), D2b (per-cell test + regime null), D3 (endpoint cap), D5 (verdict rule)** and the
> `xen.vol_regime` leg-2 machinery: the trend cap → a **causal MR-tempo cap**; the control → **regime-matched,
> horizon-matched**; **leg-2 retired** (all 6 sub-screens become single-test leg-1). Sections below marked by
> the amendment are superseded; the question, member set, multiplicity budget, and registry are unchanged.

**Status:** **FROZEN — G0 RATIFIED (2026-06-23, operator-authorized).** The D2b admission-gate **bite-check is
GREEN** at the family's **6-sub-screen** structure and C=46 (`bite-check/bite_check.py` →
`bite_check_report.json`, sha256 `f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65`,
byte-identical second pass): the shipped `xen.availability_gate` routes noise→EXONERATED / planted→ADMITTED
with the argmax naming the lever (A); the joint-max-of-6 controls family FWER across {0.025,0.05,0.10}
(noise Wilson-hi ≤ 0.051) without losing power (planted power 1.0, argmax-correct 99.7%) (B); necessity is
shown — the single-sub-screen S\* inflates family error to 0.40, the joint-max-of-6 S\* restores it to 0.043
(C); S\* stable 1000↔5000, no routing flip (D). D1–D7 below are **FROZEN**.

**Leg-2 design correction (2026-06-23, operator-directed, applied in place):** the three `/VOLREGIME`
sub-screens now test leg 2 with a **binding conjunction** — a regime cell counts only if it **beats random AND
beats the pooled CORE** (`Δ̂_core > 0`, the additive edge the unconditioned entry lacks) — under a
**regime-membership-shuffle-within-CORE** null; the foreign *regime-matched* control is removed
(ATR-normalisation already removes the regime scale). This conjunctive statistic + regime null is a **new
per-cell test** the prior bite did not exercise, so the **bite-check is extended and re-confirmed GREEN before
EXP-089 runs** (the single-test legs remain GREEN at sha `f01a000b…`). **EXP-089 is authorized once the
extended bite is GREEN.** No further amendment without a dated `D0-amendment-*` file in this directory.

**Checkpoint:** `2026-06-23-020-mean-reversion-entry-availability` · **Governing design:** `design.md`.
**Scope:** a single TRAIN-only availability screen of a **new entry-side family** (mean-reversion), opened by
**explicit operator override** of the G-019 price→non-price routing (design §1; `cf-mr-001.md` §0).
**Discipline (binding):** TRAIN sub-split only on VAL-005 5-year data; real-price metrics; deterministic
(fixed seeds, byte-identical second pass); no parameter tuned against TEST/holdout; per-stratum reporting
(LESSON-001). **0 candidate slots, 0 counted TEST reads, holdout never touched.**

---

## D1 — Entry, global filter, control, member cells (frozen) — CANDIDATE VALUES

**Dataset:** VAL-005-admitted 5-year 1-minute bars, 16 instruments (DE30 dropped), holdout-fenced
`build_domain_bars`; domains **{15m, 1h, 4h}**. **TRAIN sub-split `[0, int(analysis_rows·0.7))` only**;
analysis-TEST + final-30% holdout never sliced. All metrics in **ATR(14) units** on real OHLC. Master seed
`20260623`; per-draw seed = deterministic hash of `(sub_screen, instrument, domain, replicate)`.

**Entry — RSI-2 mean reversion (frozen):** `RSI(2)` Wilder on domain `Close`; **long `RSI₂<10`**, **short
`RSI₂>90`** (period 2, extremes 10/90 frozen). Favourable direction = long→up, short→down. The RSI exit is
**not used** (availability is excursion-based; exit is deferred capture geometry).

**Global filter `/VOLREGIME` (frozen):** `ATR(14)` Wilder on domain bars; **causal trailing rolling-50
percentile** of current ATR; cuts **33/66** → `LOW (<p33) / MED / HIGH (>p66)`. Strategy-agnostic rule;
thresholds computed **per (instrument, domain) from past bars only** (no future bar enters a regime label).
Window **50**, scheme **33/66**, **no tuning**. **Applied as a partition on the bare core only.**

**Variant toggles (frozen; pooled sub-screens only in batch 1):** **TREND** — long `∧ Close>EMA₂₀`, short
`∧ Close<EMA₂₀`; **RSI-FILTER** — long `∧ RSI₅>50`, short `∧ RSI₅<50`.

**Matched-random control (frozen, reused unchanged):** the EXP-080/081 `SUB-RANDOM` construction —
random-timing entries matched on **count and direction** within the same cell, **identical for every
sub-screen** (no regime-matching: ATR(14)-normalisation already divides out a regime's larger absolute moves,
so the all-bars direction-matched control is the correct non-confounded baseline). The regime's *additive*
contribution is isolated by the binding leg-2 `Δ̂_core` differential (D3/D5), not by the control. This is the
per-cell Δ-over-random baseline (D2a), distinct from the binding permuted-axis null (D2b).

**Member cells:** the EXP-080-READY **46** instrument×domain cells (US500-4h, JP225-4h `COVERAGE_EXCLUDED`).
RSI-MR is a new event definition → EXP-089 re-confirms event coverage (D7 **≥15-event floor, no upper bound**)
on the RSI-MR population per cell; any cell failing coverage or determinism is `COVERAGE_EXCLUDED` with record (event
counts supersede design power figures).

## D2 — Two thresholds (no magic numbers; bite-calibrated) — CANDIDATE VALUES

**D2a — Descriptive per-cell null band (reporting only, NON-BINDING).** A cell "beats random" when its paired
favourable `MFE_med` Δ-over-random one-sided lower bound > 0. Reference noise bands at C=46: the median-sign
coin-flip band is Binomial(46, 0.5) ≈ **[17, 29]**; the beats-random (CI_low>0) noise ceiling is
Binomial(46, 0.05) Q95 ≈ **5**. Reported for transparency; does **not** decide admission.

**D2b — Binding multiplicity-adjusted admission gate (THE decision; bite-checked before G0).** Reuse
`xen.availability_gate` exactly as in EXP-086/087:

- **Six sub-screens:** `CORE`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND`, `CORE+FILTER`.
- **Per-cell test — leg 1 (all sub-screens):** `Δ̂_rand = favourable MFE_med(signal) − MFE_med(SUB-RANDOM)`,
  one-sided lower bound via moving-block bootstrap; **beats-random iff lower bound > 0**.
- **Per-cell test — leg 2 (the three `/VOLREGIME` sub-screens only, BINDING):** `Δ̂_core = MFE_med(regime
  subset) − MFE_med(pooled CORE)` in the same cell; **beats-CORE iff one-sided lower bound > 0**. This is *the
  regime adds favourable availability the unconditioned entry lacks* — leg 2 at full strength, no deferral.
- **Per-sub-screen `S` (over powered cells):** `CORE`/`CORE+TREND`/`CORE+FILTER` → `S = #cells beats-random`;
  `CORE-VOL-{LOW,MED,HIGH}` → `S = #cells (beats-random ∧ beats-CORE)`. (Variants also report `Δ̂_core` vs CORE
  descriptively, non-binding.)
- **Permuted-axis null:** `CORE`/variants shuffle which timestamps are "signal" (preserving per-cell count +
  direction — the EXP-086/087 null); `/VOLREGIME` shuffle **regime membership within each cell's CORE entry
  population** (preserving per-regime counts) and recompute the beats-random ∧ beats-CORE conjunction (under the
  null a regime is a random subset of CORE → `Δ̂_core ≈ 0`). `S_perm` per permutation; `N_PERM = 5000`
  production (MC-stable vs 1000 at the bite scale).
- **Family statistic `S_fam = max_sub S`**; the **joint** permuted null is the per-permutation max across the
  six sub-screens at a shared permutation index (`combine_axis`) — this controls the **within-family**
  multiplicity over the 6 reads. `S* = Q95(joint S_perm)`; axis permutation p = fraction of permutations with
  joint `S_perm ≥ S_fam`.
- **`ADMITTED` iff `S_fam > S*` AND axis perm_p ≤ 0.05** (FWER 0.05 at the family level). **No cross-axis
  Holm** — single family (the joint-max already absorbs the across-sub-screen multiplicity).
- **`INCONCLUSIVE` iff** the joint permuted `S*` ceiling sits at or above the maximum attainable `S` at the
  realized cell count (no power).

**Bite/fixture check (REQUIRED before the run; extended for leg 2):** run the gate at the **6-sub-screen**
structure and C=46 on (i) a pure-noise family — admission rate ≤ FWER (not vacuous; the 6-sub-screen joint max
does not inflate); (ii) a planted **beats-random** family (a +0.20-ATR lift on ≥5 cells in ONE single-test
sub-screen) — admitted with power; (iii) **leg-2 fixtures:** a **pure-noise regime** (random membership within
CORE) adds **0** conjunctive wins (the `Δ̂_core` leg is not vacuous), and a **planted additive-edge regime** (a
subset with +0.20-ATR over CORE on ≥5 cells) is detected with power; (iv) routing invariant across FWER ∈
{0.025, 0.05, 0.10}; MC-stable 1000↔5000. Record the bite output (`bite_check_report.json`, byte-identical
second pass). Re-anchor `N_PERM`/`Q95` if any leg fails.

## D3 — Availability endpoint (frozen) — CANDIDATE VALUES

**Directional-favourable excursion.** Per-cell `MFE_med` in the **entry-signed direction** (long → upward MFE,
short → downward MFE), ATR(14)-normalised, over the per-event adaptive cap (EXP-081 geometry, reused). Two
per-cell reads: **leg 1** `Δ̂_rand = MFE_med(signal) − MFE_med(SUB-RANDOM)` (all sub-screens, beats-random);
**leg 2** `Δ̂_core = MFE_med(regime subset) − MFE_med(pooled CORE)` (the three `/VOLREGIME` sub-screens,
binding beats-CORE; variants descriptive). The control is the all-bars direction-matched `SUB-RANDOM` for every
sub-screen — ATR-normalisation removes the regime scale, so no regime-matching is needed; the regime's additive
value is `Δ̂_core`. No magnitude/two-sided read in batch 1 (this is a directional family; magnitude is the
closed CF-VOLEXP-001 surface and is not reopened here).

## D4 — TRAIN-only disclosure accounting (binding — preserves 0 counted TEST reads)

The screen reads the **TRAIN sub-split only** (`[0, int(analysis_rows·0.7))`); the next-21% analysis-TEST
stratum and the final-30% holdout are **never sliced or materialized** (forward path resolution clips at the
TRAIN edge). It makes **no stratum-specific selection or inference** — it computes family availability
disclosures over the full TRAIN region of each cell (EXP-080/081/086/087 convention). Therefore the screen is
a **disclosure, not a counted read**: all 48 strata remain **0 counted reads / open**; `test-read-ledger.md`
is **unchanged** by Phase 020. The permuted-axis null shuffles conditioning labels *within* the same TRAIN
region — it reads no additional data. Holdout sealed throughout.

## D5 — G-020 mechanical verdict rule

```
Family CF-MR-001 (sub-screens SS = {CORE, CORE-VOL-LOW, CORE-VOL-MED, CORE-VOL-HIGH, CORE+TREND, CORE+FILTER}):

  S_ss = #cells beats-random                     for ss in {CORE, CORE+TREND, CORE+FILTER}   (leg 1)
       = #cells (beats-random AND beats-CORE)     for ss in {CORE-VOL-LOW, -MED, -HIGH}        (leg 2, binding)
  S_fam = max_{ss in SS} S_ss
  ADMITTED      iff  S_fam > S*  (joint permuted-axis Q95 over SS, D2b)  AND  axis perm_p <= 0.05  (FWER 0.05)
                     [argmax names the lever: bare MR (leg 1) / a vol regime (leg 2) / a variant;
                      a regime wins only by ADDING edge over CORE, never by inheriting it]
  EXONERATED    iff  every S_ss is within the D2a noise band (no sub-screen beats the joint permuted null)
                     [single-series x directional is dead under mean-reversion too]
  INCONCLUSIVE  iff  the joint permuted null cannot separate at the realized cell count (no power)

Programme routing:
  ADMITTED   -> CF-MR-001 consumes its first candidate slot; a future G0/D0 opens batch 2 (readiness ->
                characterization -> capture geometry -> TEST), expanding to regime x variant cross-cuts, the
                25/75 scheme, and the contrarian arm, best-lever-first.
  EXONERATED -> the single-series-directional cell is dead under continuation AND mean-reversion; return to
                the G-019 terminal frontier (non-price data acquisition, operator decision); 0 reads / 0 slots.
  INCONCLUSIVE -> disclosed; neither admitted nor exonerated; re-scope is a separate future decision.
```

The verdict is mechanical and predeclared; the explanation it produces is not (freeze the rule, not the
story). Ranking metric if admitted (which lever to open first): the sub-screen-level permutation z-score
`(S_ss − mean(S_perm_ss)) / sd(S_perm_ss)`, tie-broken by trimmed-mean per-cell Δ.

## D6 — Determinism & real-price discipline; no tuning

- All RNG seeds fixed and recorded; a second full pass (including the permutation null at a fixed
  permutation seed-stream) is byte-identical.
- All excursion/range metrics on **real prices** (`RealOpen/High/Low/Close`); no HA/Renko synthetic-price
  returns anywhere.
- **No tuning in batch 1:** RSI period 2, extremes 10/90, RSI-filter 5/50, EMA 20, ATR 14, regime window 50,
  cuts 33/66 are all **frozen**. Parameter tuning, the 25/75 scheme, the contrarian arm, and regime×variant
  cross-cuts are **registered-but-deferred** (multiplicity ledger); opening any requires a dated amendment
  stating whether it consumes a new slot.

## D7 — Member-cell readiness bracket

RSI-MR event coverage per cell must clear a **floor of ≥15 events** (EXP-080 floor retained for power); cells
below 15 (or nondeterministic, or with a look-ahead invariant failure) are `COVERAGE_EXCLUDED` with record and
removed from the gate's member set. **No upper bound** — the EXP-080 `8000` ceiling was a sparse-substrate
coverage sanity cap and is **dropped** for this dense oscillator family (RSI-2 fires far more often, especially
at 15m; more events = more power, so a high count is never an exclusion). Realized counts supersede design
power estimates and are disclosed per cell (conditioned, control, and per-regime).

## Slot & TEST accounting

- **0 candidate slots** — availability screen; CF-MR-001 promotes to a slot only on ADMIT at a future G0/D0.
- **0 counted TEST reads** — TRAIN sub-split only; analysis-TEST + final-30% holdout never sliced;
  `test-read-ledger.md` unchanged (all 48 strata stay 0/2 open).
- Holdout sealed throughout.
