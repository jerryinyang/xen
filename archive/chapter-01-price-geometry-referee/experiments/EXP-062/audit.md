# Audit — EXP-062 (dual-object re-run)

**Scope:** validate `code/run_experiment.py` (+ unchanged `code/availability.py`) and the regenerated
`results/` for the dual-object lifetime-availability re-run under D0 Amendment 001.
**Verdict: PASS** (0 Critical, 0 Major; 1 cosmetic note fixed).

## Integrity gates (from `run_metadata.json` / `composition_readout.json` / `reconciliation.csv`)

| Gate | Result |
|------|--------|
| `is_defect` | **False** |
| Determinism (first-usable-cell replay, all arms + contrasts + both digests) | **PASS** — 17/17 cells replayed byte-identical; `non_deterministic: []` |
| Causality (`_causality_ok` MA + ZigZag; `window_invariants_ok`) | **PASS** — `causality: []` |
| Matched-count (P5, per object) | **PASS** — `invariant_violations: []` |
| Reconciliation vs EXP-055 (P12, corrected roles) | **PASS** — 99/99 checked, all `consistent=true`, `reconciliation_mismatch: []` |

**Reconciliation spot-check (exact, RNG-independent point estimates):** native `A_MA_nat` reproduces
EXP-055 `ma_seg` to full float precision — BTCUSD-5m m=10667, median MFE 3.010160223752588, median MAE
2.4839955320752165, all matching the EXP-055 anchor columns identically; the disclosed `A_ZZ` reproduces
EXP-055 `stat` (BTCUSD-5m m=3117, median MFE 1.2087988573296764). The genuinely-new hybrid `A_MA_hyb`
carries its own qualifying count (BTCUSD-5m m=3041) with **no** outcome anchor, as designed — its
ZigZag-`/STRONG-STAT` conditioning is the same mask defining `A_ZZ`'s population (transitive verification).

## Code correctness

- **Holdout fence:** `load_train_1m` reads only metadata + the first `train_rows` file-order rows; full
  file never sorted/collected; domain bars fenced to `train_end_ts`; M_b-incomplete events `DATA_CENSORED`.
  TEST + final-30% holdout never touched. Confirmed in code.
- **Dual-object separation:** `_resolve_arms` computes `a_ma_nat` (mask `ma["stat"]["retained_p75"]`) and
  `a_ma_hyb` (mask `zz["stat"]["retained_p75"]` through the shared MA context via `_ctx_arm`); the
  `compute_cell` assert (`np.array_equal(ma["entry_idx"], zz["entry_idx"])`) guarantees the cross-substrate
  mask aligns to the same harami entries. Nulls `rm_ma_nat`/`rm_ma_hyb` are matched to their own object's
  count and exclude their own signal entries, on disjoint RNG purposes. Per-object `_classify_object` and
  `_object_readout`; **no pooling** anywhere. Verified.
- **Real-price discipline:** all excursions/ATR/MA on real OHLC; HA candles for detection only.
- **Determinism / RNG:** native arm/null/contrast purposes unchanged from the prior EXP-062; hybrid arms on
  fresh purposes (9400-series / 9500-series / 5200-series). Byte-identical across `--workers` by
  construction (order-independent per-cell RNG + fixed merge).
- **Zero-baseline:** `< 30` → NOT_VIABLE_BY_POWER; tail-share finite; NaN bootstrap → not-available /
  not-attributable.

## Numerical findings (validated, not interpreted here)

- **Native:** 91/99 `MOVE_AVAILABLE` (P11+P6 composes), median MFE ≈ 3.84 ATR / median MAE ≈ 2.92 ATR; but
  `SIGNAL_ATTRIBUTABLE` (A_MA_nat − RM_MA_nat MFE CI_low > 0) in only **4/99** cells (does **not** compose;
  the contrast median CI_low ≈ −0.88, i.e. the conditioned MFE is typically *not* above matched-random).
- **Hybrid:** 94/99 `MOVE_AVAILABLE` (composes), median MFE ≈ 3.77 ATR; attributable in only **2/99**
  (does not compose; contrast median CI_low ≈ −0.98).
- **MAE tail (the L3 input):** worst-5% share ≈ 0.23 (native) / 0.24 (hybrid); raw-mean MAE ≈ 4.60 vs
  10%-trimmed ≈ 3.52 (native) — a moderately top-heavy adverse tail, not a thin truncatable spike.

## Notes

- **(fixed, cosmetic)** `plot_forest` drew the MAE marker with `facecolors="none", edgecolors=colour` on an
  unfilled `x` marker, emitting a benign Matplotlib `UserWarning` (it rendered correctly using the
  facecolor). Changed to `color=colour`; no figure-content change. Re-render on the next run is clean.

```text
AUDIT VERDICT: PASS
```
