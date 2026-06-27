# Audit Report: Experiment EXP-087

**Screen X — cross-sectional relative-strength / directional-favourable availability (Phase 019 family-selection).**
EXP-081/EXP-086 clone, information axis swapped to cross-sectional conditioning; TRAIN-only, gross, 0 candidate slots, 0 counted TEST reads.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

The implementation faithfully realizes the approved scope and analysis plan. The experiment verdict
`SCREEN_DELIVERED` is sound: per-cell + axis statistics are produced deterministically for the whole
46-cell × 2-primitive member set, determinism (metrics + permutation stream) holds, matched-random
count + direction-mix reconciliation holds for all 92 cell-primitives, the causal forward-fill is
backward-only by construction, real prices are used throughout, and the holdout is never touched
(`counted_test_reads=0`, TRAIN sub-split only). The provisional `NOT_ADMITTED (NON-BINDING)`
disposition is well-supported and not masking per-stratum heterogeneity (see Verdict Forensics). No
verdict-material finding. The two Info notes cannot move any verdict-bearing number.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Cross-section per domain → per-cell conditioned/control/pool directional MFE → reused D2b gate. Logic matches plan Steps 1–6. |
| `code/run_experiment.py` | Edge cases | PASS | Empty entry sets, warmup, ATR-undefined, clipped-empty all handled via geometry `usable` mask and `_directional_mfe` early returns. |
| `code/run_experiment.py` | Type safety | PASS | Type hints + docstrings on public functions; frozen dataclass for metrics. |
| `code/run_experiment.py` | NaN handling | PASS | `long_frac` NaN-guarded; non-finite `s_cell`/`ci_low` → `beats=False`; quantile RuntimeWarnings suppressed only around all-NaN rows. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `train_cutoff = int(frame.height*0.7)` over VAL-005 `load_first70` frame (already first 70%); geometry/pool clip at `n_bars` (TRAIN domain-bar count). No row at/beyond analysis-set edge materialized. |
| `code/run_experiment.py` | Loader ordering | PASS | VAL-005 lazy loader sorts by `CloseTime`; `is_sorted()` asserted on TRAIN frame and again in `build_cross_section`. |
| `code/run_experiment.py` | Memory/performance | PASS | Domain frames built then released per domain (`del domain_bars, xs_all`); pool drawn once per (cell,primitive); permutation vectorized in batches. |
| `code/run_experiment.py` | Safe optimization | PASS | Vectorized union-grid/fill/decile/permutation preserve sample membership, causal ordering, denominators. Only explicit loops are bounded cell/primitive and the reused causal path loop. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on domains + per-domain cells. |
| `code/run_experiment.py` | Logging/output | PASS | Concise single-line verdict log; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path → constants → types → pure → plotting → orchestration → `main()`. Dirs created only in `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All plots from collected `subs`/`axis`/`metrics` summaries; no reload or re-generation. |
| `code/run_experiment.py` | Docstrings | PASS | Module + all public functions documented. |
| `src/xen/cross_sectional.py` | Causality | PASS | `trailing_logret` uses bars ≤ t; `_build_grid` forward-fill is `searchsorted(side='right')-1` (strictly backward); events fire only at own completed-bar closes (`own_idx`); alignment by `CloseTime` epoch, never bar index. |
| `src/xen/cross_sectional.py` | Decile membership | PASS | Inclusive boundary on realized cross-section per timestamp; degenerate all-equal rows resolved to no-fire deterministically; `MIN_XS_INSTR=8` gate enforced. |
| `src/xen/availability_gate.py` (reused, unchanged) | Gate logic | PASS | Module hash recorded; `S=#beats`, joint max-statistic null, `S*=Q95`, add-one perm-p — matches GREEN bite-check. |

## Numerical Validation

### Spot Checks

- **per_event_geometry denominator:** conditioned-only export rows = 617,446 == Σ `n_cond` over all 92
  cell-primitives (exact). Confirms the per-event parquet contains exactly the usable conditioned events
  that feed each cell's `MFE_med`.
- **Favourable MFE range:** `fav_mfe` all finite, range [0.0, 88.0] ATR. Non-negative as required (max
  favourable excursion in the entry direction; 0 when price never moves favourably within the cap). The
  88-ATR maximum is a plausible single-event tail and does not enter the median endpoint.
- **Direction-mix reconciliation:** `long_frac == ctrl_long_frac` exactly for all 92 cells — `_assign_directions`
  reproduces the conditioned per-cell LONG fraction on the matched-random draw, so Δ isolates conditioning, not direction.
- **Event floor:** 0 powered cells below 30 events; 0 cells ≥30 flagged underpowered. Smallest cell
  `n_cond=274` (EURUSD-4h), so all 46 cells are powered → `n_powered_cells=46` in both sub-screens (matches
  the bite-check `C=46` calibration).

### Range / Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| `S_X` | 1 | YES | 2 of 92 cell-reads beat random; max over 2 sub-screens = 1 per sub-screen. |
| `S*` (Q95 joint null) | 1 | YES | Under pure-noise conditioning the joint max regularly yields 1 beat at C=46. |
| axis perm-p | 0.323 | YES | `S_X=1` sits at/below the null ceiling — far from separation. |
| ranking z | 1.26 | YES | <1.65; consistent with non-admission. |
| MC stability (1000) | S*=1, p=0.313 | YES | Routing invariant 1000-vs-5000 (both NOT_ADMITTED). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap SE | Conditioned events cluster serially → block preserves autocorrelation | YES | `cell_se` block-resamples conditioned, iid-resamples random control. Non-parametric. |
| Permuted-axis null | Pseudo-signal = with-replacement pool subsample preserves per-cell count + direction mix | YES | `_perm_beats`; documented immateriality of ~10% within-draw repeats for null calibration. |
| Forward-filled union grid | Last-completed-bar fill is causal | YES | `searchsorted(side='right')-1`; `own_idx` set only on exact bar-close coincidence. |

## Results Plausibility

All outputs within domain ranges; favourable MFE ≥ 0; deciles fire on the synchronized cross-section
(`n_grid_excluded` 20–21 per domain, a negligible fraction of 4,375–72,187 grid timestamps). Pattern is
coherent (see mechanism below).

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

Re-derived per (domain × primitive) from `cell_availability.csv`:

| Stratum | cells | beats | Δ̂ mean | cells Δ̂>0 | Per-stratum verdict | Agrees with pooled `S_X=1`? |
|---------|-------|-------|---------|-----------|---------------------|------------------------------|
| 15m / COND-XSRANK | 16 | 0 | −0.279 | 2/16 | no separation (degrades) | YES |
| 15m / COND-XSDIV | 16 | 0 | −0.244 | 2/16 | no separation (degrades) | YES |
| 1h / COND-XSRANK | 16 | 0 | −0.152 | 5/16 | no separation | YES |
| 1h / COND-XSDIV | 16 | 0 | −0.140 | 5/16 | no separation | YES |
| 4h / COND-XSRANK | 14 | 1 | −0.024 | 6/14 | 1 marginal beat | YES |
| 4h / COND-XSDIV | 14 | 1 | +0.084 | 8/14 | 1 marginal beat | YES |

- **Pooled headline:** `S_X=1`, `NOT_ADMITTED`. **Masking heterogeneity? NO.** The per-stratum picture is
  uniformly consistent — cross-sectional conditioning does **not** improve directional-favourable availability
  at any domain, and at the fast domains (15m, 1h) it *degrades* it (mean Δ̂ negative; only 2–5 of 16 cells
  positive). There is no hidden stratum that separates and is being averaged away; the headline is, if
  anything, generous to the axis.
- **Are the 2 beats genuine or boundary artefacts?** Both sit in the **smallest** cells of the screen
  (GBPUSD-4h COND-XSRANK, `n_cond=353`, ci_low=0.0235; NZDUSD-4h COND-XSDIV, `n_cond=450`, ci_low=0.0234) with
  one-sided lower bounds *barely* above 0 — exactly the few-events-per-cell regime where multiplicity
  manufactures lucky cells. The joint permuted-axis null reproduces the same `S*=1` ceiling, so the gate
  correctly does **not** credit them. This is the multiplicity caution the scope flagged ("a lucky single cell
  must not admit the axis") working as designed.

### Mechanism

Why the verdict came out `NOT_ADMITTED`: entering on **cross-sectional return extremes** (top/bottom-decile
trailing-20-bar relative strength, traded in the decile-sign direction) yields directional-favourable
excursion **no better than — and at 15m/1h worse than — a random-timing entry carrying the same
direction-mix**. The driver is that the decile event fires *after* the 20-bar relative move has already
occurred, so the conditioned entry buys late into relative strength / sells late into relative weakness;
over the subsequent adaptive-cap window the relative-strength extreme does not extend favourably more than a
direction-matched random clock, consistent with short-horizon mean-reversion / exhaustion of
cross-sectional momentum at intraday domains. The effect is a genuine *absence* of directional-favourable
continuation, concentrated as a mild degradation at fast domains and a wash at 4h — not a single binding leg
or cell that the gate vetoed.

### Gate-shape check

- **Binding gate:** D2b permuted-axis admission null on `S = #cells-beat-random`, per-cell read =
  one-sided lower bound of the **median favourable-MFE** Δ (a location read). **Effect shape:** location
  (directional-favourable availability is directional/location by construction — D3.X; Screen X deliberately
  has no tail/bimodal split or magnitude-budget).
- **Is the gate the wrong instrument for the shape? NO.** The endpoint is a location read and the gate measures
  exactly a location effect; there is no tail/asymmetric structure the median could be blind to here.
- **Saturated/floored?** `S_X=1` and `S*=1` are both low, but the gate is **not** saturated: max attainable
  `S=46` (all cells powered), `S* = 1 << 46`, so the `INCONCLUSIVE` (no-power) branch does not trigger and the
  statistic retains full 0–46 dynamic range. The realized `S=1` lands right at the Q95 null ceiling because the
  signal is genuinely absent — this is "no effect," correctly distinguished from "an effect of a shape the gate
  cannot see."

## Scope Compliance

- Analysis plan followed: **YES** (Steps 1–6 implemented as written; max-statistic within-axis control over 2
  primitives; provisional disposition captioned NON-BINDING).
- Deviations: none.
- Complexity budget: **2/2 tests** (per-cell beats-random bootstrap LB; permuted-axis null), **4/4 plots**,
  **1/1 new module** (`xen.cross_sectional`). All other logic reuses frozen modules (hashes recorded).
- Holdout exclusion verified: **YES** — TRAIN sub-split only; `holdout_untouched=true`; `counted_test_reads=0`;
  `candidate_slots=0`. Ledger unchanged (no stratum-specific inference).

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Stale `S_M` label in the provisional-disposition string (display-only).**
   - File: `src/xen/availability_gate.py` line 293 (reused unchanged from EXP-086 Screen M); surfaces in
     `results/axis_admission.json` `provisional_disposition` and `run_metadata.json`
     `provisional_disposition_NON_BINDING` as `"NOT_ADMITTED (NON-BINDING — S_M <= S* but outside null band on >=1 read)"`.
   - Description: the human-readable string says `S_M` (Screen-M name) for axis X. The binding fields are
     correctly labelled (`"S_X": axis.s_m`, `S_star`, `axis_perm_p`, `ranking_z`, per-sub-screen block).
   - Materiality: **cannot move any verdict-bearing number** — it is a prose label, not an input to S/S*/perm-p.
     The gate module is the frozen, hash-recorded EXP-086 artifact; retro-editing the string would change its
     hash and break the EXP-086 freeze, so it should **not** be edited here. The documenter/interpreter should
     read it as `S_X` for EXP-087.

2. **`causal_fill_ok` is a static `True` constant, not a runtime assertion.**
   - File: `code/run_experiment.py` line 549 (`causal_fill_ok = True  # ...backward-only`).
   - Description: the flag is justified by the construction of `_build_grid` (`searchsorted(side='right')-1`,
     verified at `cross_sectional.py:131`) rather than re-checked at runtime.
   - Materiality: **cannot move any verdict-bearing number** — the forward-fill backward-only property is
     structurally guaranteed by the searchsorted construction and is exercised by the new-module unit tests; the
     flag merely reports a statically-true fact. No causal leak exists.

## Materiality & Re-Audit Requirements

- **No blocking (Critical) findings.** Every finding above is Info with explicit reasoning that it cannot move
  sample membership, a denominator, a metric value, temporal/causal validity, the verdict, or the binding
  stratum.
- **No re-execution required.** The `SCREEN_DELIVERED` verdict and the provisional `NOT_ADMITTED (NON-BINDING)`
  disposition are numerically reproduced and mechanistically explained; per-stratum re-derivation confirms the
  pooled headline is not masking heterogeneity; the gate is shape-appropriate and unsaturated. Cleared for
  Stage 6 (interpretation).
