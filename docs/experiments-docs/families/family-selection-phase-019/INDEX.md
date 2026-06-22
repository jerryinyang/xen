# Family-Selection Phase 019 — Detail Index

**Family-agnostic selection phase** (not a candidate family). Governing checkpoint:
[`../../checkpoints/2026-06-22-019-family-selection-availability-screen/`](../../checkpoints/2026-06-22-019-family-selection-availability-screen/design.md)
(`design.md`, `D0-predeclarations.md`, `D0-amendment-001-screen-m-primitive-freeze.md`, `G-019-gate-criteria.md`, GREEN bite-check).
Candidate slate: [`../../../signal-registry/candidate-families/family-selection-phase-019.md`](../../../signal-registry/candidate-families/family-selection-phase-019.md).

## Overview

Phase 019 screens untested entry-side **information axes** for forward availability against a matched
within-instrument random control, before committing a candidate slot — institutionalising the fix for the
programme's historical "measure availability last" mistake. Each screen is **TRAIN-only, gross, 0 candidate
slots, 0 counted TEST reads**, holdout never touched. The binding decision rule is the **D2b
multiplicity-adjusted permuted-axis admission gate** (per-cell one-sided CI_low>0 → `S = #cells-beat-random`
→ permuted-axis null `S* = Q95` → cross-axis Holm at FWER 0.05), bite-checked GREEN before G0. Each screen
emits realized statistics and a **provisional, NON-BINDING** disposition; the binding admit / exonerate /
inconclusive adjudication is the terminal **G-019** gate, after the slate, under a cross-axis Holm step-down.
Every outcome — admit, exonerate, inconclusive — is **retained** in the registry, never deleted; every
`ADMITTED` axis is eventually opened (best-first by the Δ-over-random ranking).

The dead cell of the availability 2×2 is **single-series × directional** (EXP-047/081 availability ≈ random;
EXP-084 exit-invariant). The three untested cells are screened as: **Screen M** single-series magnitude
(`CF-VOLEXP-001`, EXP-086), **Screen X** cross-sectional relative strength (`CF-XSECT-001`, EXP-087),
**Screen F** order-flow / liquidity imbalance (`CF-FLOW-001`, EXP-088, reserved-conditional).

## Phase status: CLOSED — G-019 TERMINAL, NO FAMILY PROMOTED (2026-06-23)

**G-019 adjudicated 2026-06-23 ([`G-019-gate-review.md`](../../checkpoints/2026-06-22-019-family-selection-availability-screen/G-019-gate-review.md)):
ALL SCREENED AXES NOT ADMITTED → TERMINAL BRANCH.** The binding cross-axis Holm step-down over the realized
axis-level permutation p-values admitted no axis:

- **Axis M (`CF-VOLEXP-001`) — NOT ADMITTED.** `S_M=3 > S*=2` holds, but Holm-adjusted axis p = 2·0.0326 =
  **0.0652 > 0.05**: EXP-086's *single-axis* provisional ADMIT does **not** survive the cross-axis multiplicity
  control the slate exists to enforce. Typical-range read dead; NR7-tail thread tiny (~0.5–1.1 events/100),
  long-vol, fails FWER. Single-series × magnitude cell **CLOSED**.
- **Axis X (`CF-XSECT-001`) — NOT ADMITTED, dead-by-absence.** `S_X=1 ≤ S*=1`, p=0.323; `S=1` below the D2a
  coin-flip band [17,28]; conditioning *degrades* availability at fast domains. Cross-sectional × directional
  cell **CLOSED**.
- **Axis F (`CF-FLOW-001`) — NOT OPENED** (reserved-conditional; operator did not request a third comparison).

**Routing → terminal branch (a priori):** price-derived information — single-series **magnitude** *and*
cross-sectional **relational** — is exhausted on this dataset; the frontier is **non-price data acquisition**
(operator decision), reached at **0 candidate slots, 0 counted TEST reads**. Both families CLOSED and retained
(file-drawer, never reopened by re-parameterization). Holdout untouched; `test-read-ledger.md` unchanged
(all 48 strata 0/2 open).

## Contents

- [EXP-086 — Screen M: Single-Series Magnitude / Non-Directional Availability](#exp-086--screen-m-single-series-magnitude--non-directional-availability)
- [EXP-087 — Screen X: Cross-Sectional Relative-Strength / Directional-Favourable Availability](#exp-087--screen-x-cross-sectional-relative-strength--directional-favourable-availability)
- *EXP-088 — Screen F (order-flow) — reserved-conditional, NOT OPENED at G-019*
- **G-019 — terminal ranked inventory — ADJUDICATED 2026-06-23: no axis admitted (above)**

---

## EXP-086 — Screen M: Single-Series Magnitude / Non-Directional Availability

**Status**: COMPLETED — `SCREEN_DELIVERED`; provisional `ADMITTED` (NON-BINDING) → **G-019 binding: NOT ADMITTED** (Holm-adj p=0.0652>0.05; CF-VOLEXP-001 CLOSED, retained)
**Date**: 2026-06-22 (screen) · 2026-06-23 (G-019)
**Instruments**: 16 (VAL-005 universe) × {15m, 1h, 4h} = 46 EXP-080-READY member cells (US500-4h, JP225-4h `COVERAGE_EXCLUDED`)
**Data Views / Feature Categories**: 1-minute time bars → 15m/1h/4h domain bars (real OHLC); two single-series compression primitives — raw HA-harami inside-bar (`COND-HARAMI`, HA for detection only) and real-OHLC NR7 (`COND-NR7`). TRAIN sub-split only; final-30% holdout never touched.

### Hypothesis Tests

1. **Hypothesis** (`CF-VOLEXP-001/HYP-001`, the magnitude cell of the availability 2×2): conditioned on existing single-series compression primitives, does forward **non-directional** availability beat a matched within-instrument random control by more than the multiplicity-adjusted permuted-axis null (D2b) at the realized cell count — on **either** of two strictly-separate reads (typical-range; tail/bimodality) — and does any predictable range clear a **two-sided** cost? (A pooled `|move|` number is prohibited — D3.M.)

### Scope

- **Instruments**: 16 × {15m, 1h, 4h}, 46 member cells (EXP-080 READY set).
- **Data Views / Feature Categories**: real domain OHLC; HA candles for harami detection only; NR7 on real OHLC.
- **Features**: `COND-HARAMI`, `COND-NR7`; matched `SUB-RANDOM` control; per-event adaptive time cap (frozen `TIMECAP_*`); Wilder ATR(14); typical-range = median `max(MFE,MAE)`; tail = `tailmass` (`median − 3·MAD`) of regime-signed outcome; `q05`, dip-p, `msofar_atr` rank-biserial (descriptive); two-sided magnitude-budget (frozen EXP-085 cost table).
- **Parameter ranges**: none tuned — all constants frozen at D0 / D0-amendment-001 (NR lookback 7, `K_tail=3.0`, event floor 30, `Z=1.645`, FWER 0.05 band {0.025,0.05,0.10}, `N_PERM=5000` + 1000 MC-stability).
- **Exclusions**: no exit/barrier/target/stop, no edge/tradability claim, no parameter sweep, no cross-instrument pooling as a binding statistic, no TEST/holdout contact, no directional re-use of a tail-only result.
- **Constraints**: TRAIN-only (`[0, int(int(total·0.7)·0.7))` = first 49% of file); real-price discipline (every range/outcome/ATR on real OHLC); causal/look-ahead-safe; deterministic.

### Results / Observations

- **Integrity**: `SCREEN_DELIVERED` — `determinism_ok=true`, `recon_all_ok=true`, `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`. 46 cells, all powered (n_cond min 382, median 3337).
- **Axis statistic**: `S_M = 3`, `S* = 2` (FWER 0.05), axis `perm_p = 0.0326`, `ranking_z = 2.62`, driver `COND-NR7/tail`.
- **Sub-screen `S` (of 46)**: HARAMI-typical 0, HARAMI-tail 0, NR7-typical 0, **NR7-tail 3** (single-sub perm_p 0.0066).
- **Three beats-random cells (all 15m)**: NZDUSD-15m (tailmass 0.0497 vs 0.0401, Δ +0.0097, ci_low +0.0017), USTEC-15m (0.0845 vs 0.0741, Δ +0.0104, ci_low +0.0017), US2000-15m (0.0851 vs 0.0743, Δ +0.0108, ci_low +0.0015).
- **Typical-range read**: null on both primitives; NR7 conditioned median range *below* random (`Δ̂` median ≈ −0.28 ATR).
- **Per-domain NR7-tail breadth** (tailmass `Δ̂`>0 / cells): 15m 15/16 (median Δ +0.0052, S=3), 1h 10/16 (+0.0024, S=0), 4h 7/14 (+0.0006, S=0); median `s_cell` 0.0050 / 0.0085 / 0.0211.
- **FWER sensitivity**: admitted at 0.05 (S*=2) and 0.10 (S*=2); **not admitted at 0.025** (S*=3). MC-stable 1000 vs 5000 (S*=2, perm_p≈0.033–0.038).
- **Magnitude-budget (disclosure, necessary-not-sufficient)**: NZDUSD-15m net +8.27 ATR, USTEC-15m +11.40 ATR; US2000-15m `cost_available=false`.

> Note: No interpretation — preserve what the data shows. Pooled figures are disclosure-only.

### Hypothesis-Specific Conclusion

**PROVISIONAL `ADMITTED` (NON-BINDING) — borderline, tail-only ⇒ long-vol.** The single-series magnitude cell is not uniformly dead: a small, real, broadly-present NR7 compression → rare-tail-expansion signal provisionally clears the multiplicity-adjusted gate at FWER 0.05 but **fails at 0.025**. Typical/normal range is dead. By the harvest-model guard a tail-driven admission is **long-vol / two-sided-cost**, never a directional edge. The binding admit/exonerate is deferred to **G-019** (cross-axis Holm over {M, X, (F)} can only raise `perm_p = 0.0326`; little headroom under 0.05). Audit PASS-with-findings (0C / 2W / 4I; both Warnings non-material).

### Hypothesis-Agnostic Observations

- The pooled axis statistic is **conservative / anti-masking**: the tailmass lift is positive in the large majority of NR7 cells in every domain but only 15m has the event count (~10k) to power the one-sided bound; 4h cells with larger raw lifts fail on SE. `S_M = 3` understates a broadly-present-but-underpowered effect.
- NR7 (narrowest TR in 7 bars) is the **stronger** compression primitive for the tail; HARAMI shows the same-sign but weaker lift that never clears its SE.
- The mechanism is **tail-only, not location**: a quiet bar suppresses the near-term median range while slightly fattening the rare adverse catastrophe tail — the classic compression→expansion fingerprint, matching the low/tail-concentrated `CF-VOLEXP-001` prior.
- Gate-shape note: the binding tail statistic is left-tail-only on a regime-signed outcome (by design); a purely favourable (right-tail) magnitude expansion would be only partially visible.

Artifacts: [`python/experiments/EXP-086/`](../../../../python/experiments/EXP-086/) — report.md, results.md, audit.md, scope.md, analysis-plan.md, governance/pre-execution-review.md, results/, plots/.

---

## EXP-087 — Screen X: Cross-Sectional Relative-Strength / Directional-Favourable Availability

**Status**: COMPLETED — `SCREEN_DELIVERED`; provisional `NOT_ADMITTED` (NON-BINDING) → **G-019 binding: NOT ADMITTED, dead-by-absence** (S=1≤S*=1, p=0.323; CF-XSECT-001 CLOSED, retained)
**Date**: 2026-06-22 (screen) · 2026-06-23 (G-019)
**Instruments**: 16 (VAL-005 universe, no DE30) × {15m, 1h, 4h} = 46 EXP-080-READY member cells (US500-4h, JP225-4h `COVERAGE_EXCLUDED`)
**Data Views / Feature Categories**: 1-minute time bars → 15m/1h/4h domain bars (real OHLC); two cross-sectional relative-strength conditioning primitives — trailing-20-bar-return rank (`COND-XSRANK`) and divergence-from-equal-weight-basket-mean (`COND-XSDIV`), both top/bottom decile LONG/SHORT, on a causal forward-filled union timestamp grid across the 16 instruments. TRAIN sub-split only; final-30% holdout never touched.

### Hypothesis Tests

1. **Hypothesis** (`CF-XSECT-001/HYP-001`, the cross-sectional × directional cell of the availability 2×2): conditioned on cross-sectional relative strength (basket-relative momentum/divergence rank across the synchronized 16-instrument universe), does an entry's signal-conditional **directional-favourable** availability (`MFE_med`, ATR-normalised, real prices, traded in the decile-sign direction) beat a matched within-instrument random control by more than the multiplicity-adjusted permuted-axis null (D2b) at the realized cell count?

### Scope

- **Instruments**: 16 × {15m, 1h, 4h}, 46 member cells (EXP-080 READY set).
- **Data Views / Feature Categories**: real domain OHLC; cross-sectional conditioning computed from real-price log returns (no synthetic chart type).
- **Features**: `COND-XSRANK`, `COND-XSDIV` (lookback 20, both tails, decile cutoff 0.10, `MIN_XS_INSTR=8`); causal forward-filled union grid; matched `SUB-RANDOM` control with the conditioned per-cell LONG/SHORT mix; per-event adaptive time cap (frozen `TIMECAP_*`); Wilder ATR(14); directional-favourable `MFE_med` Δ-over-random; D2b joint-max permuted-axis admission gate.
- **Parameter ranges**: none tuned — all constants frozen at D0 / D0-amendment-002 (lookback 20, decile 0.10, `MIN_XS_INSTR=8`, event floor 30, `Z=1.645`, FWER band {0.025,0.05,0.10}, `N_PERM=5000` + 1000 MC-stability).
- **Exclusions**: no exit/barrier/target/stop, no portfolio/market-neutral construction, no edge/tradability/candidate claim, no parameter sweep, no cross-instrument pooling as a binding statistic, no TEST/holdout contact, no Screen-M magnitude-budget (Screen X is directional-favourable only).
- **Constraints**: TRAIN-only (`[0, int(int(total·0.7)·0.7))` = first 49% of file); real-price discipline; causal (trailing return/rank/divergence at t use only bars ≤ t; forward-fill backward-only; alignment by `CloseTime`, never bar index); deterministic (seeded, byte-identical second pass).

### Results / Observations

- **Integrity**: `SCREEN_DELIVERED` — `determinism_ok=true` (metrics + permutation stream), `recon_all_ok=true`, `causal_fill_ok=true`, `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`. 46 cells, all powered (smallest n_cond=274); per_event rows 617,446 == Σ n_cond (exact); direction-mix exact match all 92 cells.
- **Axis statistic**: `S_X = 1`, `S* = 1` (FWER 0.05), axis `perm_p = 0.323`, `ranking_z = 1.26`, driver `COND-XSRANK/favourable`.
- **Sub-screen `S` (of 46)**: COND-XSRANK 1 (perm_p 0.113), COND-XSDIV 1 (perm_p 0.236); n_powered_cells 46 each. Neither in the D2a band [17,28] — **below** it.
- **Two beats-random cells (both 4h, smallest cells)**: GBPUSD-4h COND-XSRANK (Δ̂ +1.19 ATR, ci_low +0.0235, n_cond 353), NZDUSD-4h COND-XSDIV (Δ̂ +0.54 ATR, ci_low +0.0234, n_cond 450).
- **Per-domain mean Δ̂ (ATR)**: 15m −0.279 (XSRANK) / −0.244 (XSDIV), 2/16 cells Δ̂>0; 1h −0.152 / −0.140, 5/16; 4h −0.024 / +0.084, 6–8/14.
- **FWER sensitivity**: not admitted at 0.025, 0.05, 0.10 (all S*=1). **MC-stable** 1000 vs 5000 (S*=1, perm_p 0.313 vs 0.323) — routing invariant.

> Note: No interpretation — preserve what the data shows. Pooled figures are disclosure-only.

### Hypothesis-Specific Conclusion

**PROVISIONAL `NOT_ADMITTED` (NON-BINDING) — dead-by-absence, not exonerated.** Cross-sectional relative strength shows no directional-favourable availability over a direction-matched random control on any domain, and degrades it at 15m/1h; `S_X=1 ≤ S*=1`, axis perm_p=0.323 at every FWER level and both N_PERM scales. `S=1` falls **below** the D2a coin-flip band [17,28], so the cell is provisionally dead-by-absence (underperforms coin-flip), distinct from `EXONERATED`. The binding admit/exonerate is **G-019** (cross-axis Holm over {M, X, (F)} can only raise perm_p=0.323 → no admission reachable). Audit PASS (0C / 0W / 2I; both Info non-material).

### Hypothesis-Agnostic Observations

- The pooled axis statistic is **not masking heterogeneity** — the per-stratum picture is uniformly negative, not an average hiding a separating stratum; `S_X=1` is if anything generous to the axis.
- **Mechanism**: a decile event fires *after* the trailing 20-bar relative move has occurred (late entry into relative strength/weakness); the extreme does not extend favourably beyond a direction-matched random clock — short-horizon mean-reversion / exhaustion of intraday cross-sectional momentum.
- The two beats are small-cell multiplicity artefacts (lower bounds barely above zero in the two smallest 4h cells) — the joint permuted-axis null reproduces the same `S*=1` ceiling, so the gate correctly does not credit them. The multiplicity caution the scope flagged (ranking over 16 instruments manufactures the most cells) is exactly what the gate absorbs.
- Gate-shape: location read on a location effect, unsaturated (max attainable S=46, S*=1) — a genuine "no effect," not an effect the gate cannot see.
- Programme note: with Screen M (EXP-086) provisionally admitted only on a borderline tail-only signal and Screen X not admitted, the slate evidence points toward price-derived information — single-series geometry *and* cross-sectional relational — being largely exhausted on this dataset; G-019 formalises this against the frozen D5 rule.

Artifacts: [`python/experiments/EXP-087/`](../../../../python/experiments/EXP-087/) — report.md, results.md, audit.md, scope.md, analysis-plan.md, governance/pre-execution-review.md, results/, plots/.
