# Audit Report: Experiment EXP-086

**Screen M — single-series magnitude / non-directional availability (Phase 019 family-selection, axis M, `CF-VOLEXP-001/HYP-001`).** TRAIN-only, gross, 0 slots / 0 counted reads. Experiment verdict `SCREEN_DELIVERED`; provisional **NON-BINDING** disposition `ADMITTED` (binding admit/exonerate is at G-019).

## Summary

- **Verdict**: PASS (with findings)
- **Critical Issues**: 0
- **Warnings**: 2 (both shown non-material to any verdict-bearing number)
- **Info Notes**: 4

The implementation faithfully executes the approved scope/plan; every headline number reproduces **exactly** from the raw outputs; all integrity flags (determinism, matched-random reconciliation, holdout fence) are clean. Verdict forensics confirm the pooled axis ADMIT is **genuine, conservative, and the opposite of masking** — the tailmass lift is broadly present across domains but only statistically powered at 15m. No finding can move `S_M`, `S*`, `perm_p`, the three `beats_random` flags, or the `SCREEN_DELIVERED` integrity verdict in the false-admit direction.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| run_experiment.py | Correctness | PASS | Geometry assembly, gate wiring, output writers all match the plan; spot-checks reproduce. |
| run_experiment.py | Holdout exclusion | PASS | `load_first70` returns first 70% of file (VAL-005:289); `build_all_metrics:318-319` re-slices first 70% of that = first 49% of file = TRAIN sub-split. Forward windows clip at `n_bars-1` (capgeo_geometry:120,129). analysis-TEST + holdout never materialized. `holdout_untouched=true`. |
| run_experiment.py | Look-ahead / causality | PASS | NR7 causal (trailing-window TR min, only bars ≤ i); HA harami detection-only mapped to confirming domain bar; adaptive cap on confirmed segments; path window `[i+1, min(i+cap, last)]`. |
| run_experiment.py | Real-price discipline | PASS | `range_sym`/`signed_outcome`/ATR all on `_real_ohlc`; HA used only inside `harami_raw_entries` for entry location; NR7 on real OHLC. |
| run_experiment.py | Timestamp alignment | PASS | epoch/`CloseTime`; `is_sorted()` assert (line 320); harami→confirming domain bar; no bar-index alignment. |
| availability_gate.py | Gate logic | PASS | per-cell `Δ̂ − 1.645·s_cell > 0`; max-stat joint null; perm-p add-one form. Reproduces. |
| compression_primitives.py | Determinism | PASS | NR7 deterministic sliding-window TR-min; harami via frozen `detect_ha_harami`. |
| all | Memory/perf, progress, organization | PASS | pool computed once/cell; permutations subsample (no per-perm path scan); `tqdm` over (cell×primitive); bounded plot inputs; no import-time side effects. |
| all | Type safety / docstrings / NaN | PASS | type hints + docstrings present; warmup/ATR-undefined/clipped/mad-zero all explicitly handled and disclosed. |

## Numerical Validation

### Spot Checks (reproduced from `results/` with the project venv)

**Tailmass (binding tail statistic), recomputed from `per_event_geometry.parquet` via `median − 3·MAD`:**

| Cell (NR7, tail) | n_cond | recomputed tailmass | reported `theta_cond` | `theta_ctrl` | `delta_hat` | `ci_low` |
|---|---|---|---|---|---|---|
| NZDUSD-15m | 10151 | 0.049749 | 0.049749 | 0.040063 | 0.009686 | 0.001662 |
| USTEC-15m  | 9716  | 0.084500 | 0.084500 | 0.074143 | 0.010357 | 0.001736 |
| US2000-15m | 10080 | 0.085119 | 0.085119 | 0.074283 | 0.010836 | 0.001524 |

Exact match. `ci_low = delta − 1.645·s_cell` verified (NZDUSD: 0.009686 − 1.645·0.004877 = 0.001663). All three `> 0` ⇒ `beats_random = True`.

**S per sub-screen** (re-derived by summing `beats_random`): HARAMI-typical 0, HARAMI-tail 0, NR7-typical 0, **NR7-tail 3** — matches `axis_admission.json`. `S_M = max = 3`. `n_underpowered = 0` (all 46 cells ≥ floor).

**Axis null arithmetic:** `perm_p = (1+k)/(1+5000) = 0.032593` ⇒ k = 162 permutations reach `S_perm_max ≥ 3` (3.24%). 3.24% < 5% ⇒ `S* = Q95 = 2` ✓; 3.24% > 2.5% ⇒ `S*(FWER 0.025) = 3` ⇒ not admitted at 0.025 ✓. Internally consistent with the reported FWER sensitivity band and `ranking_z = 2.62`.

### Range / Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|---|---|---|---|
| tailmass (all cells) | 0.04–0.09 | YES | rare-tail fraction near the ~1/ (heavy-tail) regime; matches EXP-081 (~0.05). |
| typical-range `delta_hat` median | HARAMI −0.019, **NR7 −0.280** | YES | conditioned median range **below** random — NR7 is a quiet state, so near-term range is compressed; confirms "no positive location effect," not a zeroing bug. |
| axis perm_p | 0.0326 | YES | clears 0.05, fails 0.025 — borderline, as designed. |
| determinism / recon | true / true | YES | two-pass metrics + permutation-stream fingerprints identical; `recon_all_ok`. |

## Scope Compliance

- Analysis plan followed: **YES**. Deviations: none (the Stage-4-reconciled pool formula `min(n_bars, max(3000, 8·n_entries), 30000)` + with-replacement pseudo-signal is implemented as predeclared: run_experiment.py:118-119,234-235; availability_gate.py:199).
- Complexity budget: **3/3 tests** (per-cell block-bootstrap beats-random; Hartigan dip [descriptive]; permuted-axis null), **5/5 plots**, **2/2 new modules**. `msofar_atr` rank-biserial discards the M-W p (effect size only); magnitude-budget is arithmetic.
- Holdout exclusion verified: **YES**.

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

The binding headline is a single axis statistic `S_M = 3 > S* = 2`, `perm_p = 0.0326`, driven entirely by **one sub-screen of four** (COND-NR7 / tail) and **three cells of 46**, all on the 15m domain. This is exactly the configuration where pooled-masking must be ruled out. Per-domain re-derivation of the driving sub-screen (NR7 / tail):

| Domain | cells | median n_cond | median `Δ̂` (tailmass lift) | cells with `Δ̂ > 0` | median `s_cell` | S (beats) |
|---|---|---|---|---|---|---|
| 15m | 16 | 10254 | +0.0052 | **15 / 16** | 0.0050 | **3** |
| 1h  | 16 | 2514  | +0.0024 | 10 / 16 | 0.0085 | 0 |
| 4h  | 14 | 430   | +0.0006 | 7 / 14 | 0.0211 | 0 |

**Is the pooled ADMIT masking heterogeneity? NO — and the inverse is true.** The tailmass lift (`Δ̂ > 0`) is **positive in the large majority of NR7 cells in every domain** (15/16, 10/16, 7/14), strongest at 15m and decaying with domain. What gates `beats_random` is `Δ̂` vs `s_cell`: `s_cell` scales ~1/√n, so 4h cells with **larger** raw lifts (EURJPY-4h Δ̂ +0.0219, USTEC-4h +0.0126) fail (`s_cell ≈ 0.02` ⇒ `ci_low < 0`), while 15m cells with **smaller** lifts (~0.010) clear (`s_cell ≈ 0.005`). The three winners are 15m **because that is where the event count powers the one-sided bound**, not because the effect is 15m-specific. The pooled `S_M = 3` therefore *understates* a broadly-present-but-underpowered effect; it is conservative, not masking.

**Max-statistic multiplicity (one of four sub-screens driving the max):** correctly controlled. On its own, NR7-tail has single-sub `perm_p = 0.0066`; the joint max-statistic null inflates this to the binding `perm_p = 0.0326` — the honest penalty for screening 4 sub-screens and keeping the best. Construction verified: `combine_axis` vstacks the four `s_perm` arrays and takes the per-index max (availability_gate.py:266-267). The four sub-screen nulls are generated with **independent** RNG streams (`default_rng([SEED_GATE, p_idx, r_idx])`, run_experiment.py:350) — see Warning 1; this makes the max-stat bar **conservative** (max over independent ≥ max over positively-dependent), so it cannot have produced a false admit.

### Mechanism

**Why ADMITTED:** NR7 (narrowest true-range in 7 bars) is a genuine low-volatility **compression** state. Conditioned on it, the regime-signed realized outcome over the adaptive cap shows a small but consistent **excess of rare large adverse-signed moves** (catastrophe-tail mass `median−3·MAD`) versus matched random-timing entries — the classic compression→expansion fingerprint — present across all domains but only powered at 15m (n≈10k). Simultaneously the **typical/median range is *below* random** (NR7 conditioned typical-range `Δ̂` median −0.28): a quiet bar is followed by a compressed near-term median range, with the action confined to the rare tail. So the signal is **tail-only, not location** — precisely the low, tail-concentrated `CF-VOLEXP-001` prior (EXP-081 `tailmass` 0.0526 vs 0.0437). HARAMI shows the same-sign but weaker tail lift (best Δ̂ +0.0073) that never clears its SE ⇒ S=0. The effect size is economically tiny: ~0.5–1.1 extra catastrophe events per 100 (Δ tailmass 0.005–0.011 at 15m).

### Gate-shape check

- **Binding gate = per-cell one-sided lower bound on Δ-tailmass** (a tail/shape statistic). It **can** see the effect's shape — and did: the admit is driven by the tail read, while the location read (median of `max(MFE,MAE)`) is correctly null. **Right instrument for the shape present.**
- The typical-range S=0 is a **true "no positive location effect"** (median range at/below random), not a wrong-instrument miss — confirmed by the negative median `Δ̂` and direction-agnostic `d=+1` geometry (run_experiment.py:188-189; only `np.maximum(mfe,mae)` enters the typical read, plan Step 3 honoured). The tail read is regime-signed (`signed_outcome = rd · outcome`, run_experiment.py:193).
- **Recorded shape note for the interpreter (Info 3):** the binding tail statistic is **left-tail-only on a regime-signed outcome** (adverse catastrophe). A rare *favorable*-signed (right-tail) magnitude expansion would be only partially visible (median typical-range won't catch a rare tail; tailmass counts the left tail; the `q05` companion is non-binding). This is by design (catastrophe-tail = the documented long-vol harvest target) and does not affect the present admit, but it bounds what "magnitude availability" this screen could detect.

## Issues

### Critical

None. No finding can change sample membership, a denominator, a metric value, temporal/causal validity, the provisional disposition, or the driving stratum in the false-admit direction.

### Warning

1. **Max-statistic joint null uses independent per-sub-screen RNG streams.**
   - File: `python/experiments/EXP-086/code/run_experiment.py:350`; `python/src/xen/availability_gate.py:266-267`.
   - Description: plan Step 6.3 frames the joint null as "the same permutation index across sub-screens." The code generates each sub-screen's `s_perm` with an independent stream (`default_rng([SEED_GATE, p_idx, r_idx])`) and takes the per-index max. A literally-shared pseudo-signal across **primitives** is not even well-defined (HARAMI events ≠ NR7 events), so the independent construction is the sensible one.
   - **Materiality (non-material → document-and-proceed):** the max over **independent** nulls stochastically dominates the max over positively-dependent nulls, so `S* = Q95(S_perm_max)` is, if anything, **too high** (conservative). The admit at `S_M = 3 > S* = 2`, `perm_p = 0.0326` therefore cleared a bar at least as hard as the shared-permutation construction would set. It **cannot** have caused a false admit and does not move `S_M` or the realized `beats_random` flags. No rerun required; recommend the documenter note the construction explicitly.

2. **Magnitude-budget `net_atr` is a necessary-not-sufficient qualifier and is misleadingly large; one driving cell lacks a cost constant.**
   - File: `python/experiments/EXP-086/code/run_experiment.py:269-290`; `capgeo_cost.COST_CONSTANTS`.
   - Description: for the tail read, `harvestable_atr = |q05|` (the *size* of the rare adverse move, several ATR) and `net_atr = |q05| − cost2` ⇒ large positives (NZDUSD-15m +8.27, USTEC-15m +11.40 ATR). This is the magnitude of a tail you must *first be positioned to monetize* (the long-vol thesis itself), not a realized edge. US2000-15m (one of the 3 winners) is `cost_available = false` (US2000 ∉ the EXP-085 4-instrument table) ⇒ `net_atr = NaN`.
   - **Materiality (non-material → document-and-proceed):** the magnitude-budget is **not** part of the admission gate (`S_M` vs `S*`); it cannot move `S_M`, `S*`, `perm_p`, or any `beats_random` flag. The missing US2000 cost constant likewise moves no verdict-bearing number. Impact is purely interpretive — `results.md` must not present `net_atr` as an edge. Recommend the interpreter frame it as "rare-move size exceeds frictional cost — necessary, not sufficient" and flag the 1/3 cost gap.

### Info

1. **The admit is power-gated, not 15m-specific (anti-masking).** Tailmass `Δ̂ > 0` in 15/16 (15m), 10/16 (1h), 7/14 (4h) NR7 cells; only 15m has the event count to clear the one-sided bound. Pooled `S_M` understates the effect's breadth.
2. **The ≥30 event floor is generous for a rare-tail fraction**, but the moving-block bootstrap `s_cell` is the real power gate — 4h cells pass the floor yet correctly fail on SE (`s_cell ≈ 0.02`). No cell is falsely credited.
3. **Gate-shape note (see above):** binding tail statistic is left-tail-only on a regime-signed outcome; favorable-only expansion is only partially covered. By design; recorded for the interpreter and any follow-up scope.
4. **Self-calibration confirmed:** realized `theta_cond` and the permutation pseudo-signals are both compared to the same matched-random `theta_ctrl` with the same fixed `s_cell`; under the random-timing null the conditioned and pseudo statistics are exchangeable, so the gate self-calibrates (bite §C). The with-replacement pseudo-signal draw (~10% within-draw repeats) is a faithful, scan-free realization of the D0 §D2b "shuffle which timestamps are signal" null and is more D0-faithful than the bite-check's sign-flip abstraction.

## Materiality & Re-Audit Requirements

- **No blocking (Critical) findings.** Both Warnings are shown unable to move any verdict-bearing number (W1 is conservative w.r.t. the admit; W2 is downstream of and disjoint from the admission gate). No fix-and-rerun is required.
- **Re-audit:** not required. The provisional `ADMITTED (NON-BINDING)` is sound, reproduces exactly, and is conservative. Hand-off notes for Stage 6 (interpreter): (a) frame the admit as **borderline** (fails FWER 0.025) and **tail-only ⇒ long-vol, never directional** (harvest-model guard); (b) state the effect is small (~0.5–1 extra catastrophe per 100) and broadly-present-but-15m-powered; (c) do not present `net_atr` as an edge; (d) the binding admit/exonerate remains G-019, where the cross-axis Holm step-down over {M, X, (F)} can only raise `perm_p` (0.0326 has little headroom under 0.05).

**Overall: PASS (with findings). Advance to Stage 6 (Interpretation).**
