# Phase 021 D0 — Amendment 002 (post-execution confound fixes: 1m fill engine + Null B)

**Date:** 2026-06-24 (operator-authorized). **Status:** APPLIED to `xen.intrabar_fill` + `EXP-090/code/run_experiment.py`.
**Nature:** **Two frozen-design confounds surfaced by EXP-090 execution.** Per the programme deviation norm
(post-run confound ⇒ dated amendment + **hard-delete of stale results + full rerun**), the EXP-090 `results/` and
`plots/` were hard-deleted and the experiment was fully re-run after each fix. **No ratified parameter-table value
is changed** (RSI 2/10/90, ATR 14, adverse 2.0×ATR, MR-tempo cap, ATR-barrier 1.0/2.0×ATR, α₀=0.05, Z=1.645,
N_BOOT=10000, N_DRAWS=1000, N_CAL_MAX=4000, coverage floor 15, edge grid — all unchanged). These restore the
D2.5 / two-null specifications to their **intended** behaviour; they do not retune anything.

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Amends:** `D0-predeclarations.md` §D2.5 (fill engine),
§D6/calibration (Null B construction). **Audit trail:** the first EXP-090 run HALTed on fill-price validity (32/32
cells); root cause traced + reproduced before each fix.

---

## Fix 1 — 1-minute intrabar fill engine: window anchoring + gap-through fills (D2.5)

**Confound.** `xen.intrabar_fill` violated the D2.5 "fill price = a real touched level ∈ `[Low, High]`" invariant
on essentially every cell × arm (the predeclared HALT). Two distinct defects:

1. **Window over-assignment.** `minute_bounds_for_domain` mapped each domain bar to the 1-minute bars since the
   **previous *kept* domain close** (`(dce[k-1], dce[k]]`). Because `build_domain_bars` drops coverage/fence
   windows and markets have session gaps, `dce` is non-contiguous, so a bar absorbed 1-minute bars from
   dropped/gap windows whose prices lie outside its own `[Low, High]`. (Reproduced: 817/60,026 EURUSD-15m bars;
   up to ~22% dropped on JP225.) Stops/targets then "touched" at prices the domain bar never traded.
2. **Limit/stop gap-throughs.** Even with the window fixed, ~2.5% of favourable fills recorded the **level** when
   price gapped *past* it within the touching 1-minute bar (level outside that bar's `[Low, High]`).

**Resolution.**

1. Each domain bar's 1-minute window is anchored to its **own** resample window `(dce[k] − period_s, dce[k]]`
   (matching `aggregate_ohlc`'s `(epoch−1)//period` bucket with right label `(bucket+1)·period`), located by
   `searchsorted` — never bar index, never the previous-kept close. Gap-proof by construction.
2. A stop/limit that **gaps** beyond the touching 1-minute bar fills at that bar's **open** — a real, marketable
   price in `[Low, High]` — the standard gap-through convention; the level is used only when the bar traded
   through it. The engine now takes `minute_open` (threaded through `resolve_arm`, the pool resolver, and the
   Null-B path; the open is rotated/handled with its bar).

**Effect on D2.5 intent:** none beyond restoring it — every fill is now a real touched price in `[Low, High]`,
causal, timestamp-aligned, holdout-fenced. The post-fix run passes fill-validity on all 32 cells × 5 arms.

## Fix 2 — Null B reverts to block-permuted **returns** (scope.md form), not block-rotated path (D6 calibration)

**Confound.** `scope.md` specified the second calibration null (Null B) as **"block-permuted real returns"** (the
EXP-001/027/044 form). The Stage-2 analysis-plan substituted a **block-rotated 1-minute *path*** (the EXP-070
form). Resolving matched-random entries against a rotated price path matches each entry to **wrong-era prices**;
the ATR-normalised return `dir·(fill − entry)/ATR_entry` then uses a fill from one price regime and an
entry/ATR from another, **inflating per-event return variance 30–145×** (e.g. BTCUSD-1h RCT std 0.29→9.25 ATR;
EURUSD-1h ERT 0.46→67.4 ATR). The recentred-to-0 mean is unaffected (no injected expectancy — verified ≈1e-16),
but the heavy-tailed, regime-mismatched distribution makes the **binding mean** moving-block lower bound
unstable, miscalibrating Null B's FPR (up to 0.25). EXP-070 tolerated path-rotation only because its binding
statistic was the **median** (robust to such outliers); EXP-090's binding statistic is the **mean**.
Consequence: 14 cells that pass the faithful null A with a finite MDE were excluded **only** by the pathological
Null B.

**Resolution.** Null B is the **circular moving-block resample of the resolved REAL return series**
(`_block_permute_returns`, the EXP-044 `block_permute_returns` construction): block length `round(n**(1/3))`, real
return marginal/magnitude **preserved**, long-range serial dependence **broken** (the structurally-different
dependence channel the two-null requirement wants). Both nulls resolve the real 1-minute path; only their
dependence structure differs. Post-fix: Null B std matches the real null (0.29→0.32, 0.46→0.47), centred mean 0.

**Effect on D6 intent:** none beyond restoring it — two structurally-different, true-location-0, real-magnitude
nulls per the original scope; the binding mean FPR is no longer corrupted by a cross-regime artifact.

---

## Also recorded (performance, non-confound, non-binding)

The **disclosed median lower-bound leg (D5, "co-reported, never gates")** is **dropped** in EXP-090 for
performance (~86% of bootstrap cost was its `np.median`). The **binding mean** lower bound is bit-identical to the
shared `xen.ass` estimator (the median consumed no randomness). This is an output reduction of a non-binding
diagnostic, recorded in `run_metadata.json` (`median_leg`), not a methodology change — noted here for completeness.

---

*Both confound fixes were reproduced before fix and re-validated after; the stale first/second-run artifacts were
hard-deleted and EXP-090 fully re-run under each. The binding parameter table is untouched. `run_metadata.json`
records `fill_engine_fix`, `null_b_construction`, and `median_leg`.*
