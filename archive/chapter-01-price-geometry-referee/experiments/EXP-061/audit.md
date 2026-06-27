# Audit Report: Experiment EXP-061 (dual-object re-run)

> **Re-audit of the dual-object re-run** under `D0-amendment-001-dual-parallel-substrate.md`
> (2026-06-17). Supersedes the prior single-object (native-only, mislabelled "hybrid") audit in
> place. Results regenerated 2026-06-17 21:40; this audit covers the 6-arm output
> (`H0`/`RH0` hybrid, `M0`/`RM0` native, `Z0`/`RZ0` disclosed ZigZag contrast).

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Benchmark geometry (50%×1:1×cap) via the EXP-060/060B resolver; **two binding objects measured individually** — hybrid `H0` (ZigZag `/STRONG-STAT` conditioning mask × MA-segment geometry) and native `M0` (MA-segment `/STRONG-STAT` × MA geometry) — each with its own matched-random null (`RH0`/`RM0`); `Z0`/`RZ0` disclosed contrast. 6-object set exactly as scoped. Hybrid and native **never pooled** in any metric. |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami sets / <30 events → `NOT_VIABLE`-by-power per arm; zero negative mass → `tail_share = 0.0` (finite); MA/ZZ segmentation with <2 confirmed pivots → empty; `DATA_CENSORED` + warmup excluded, disclosed as counts per object per cell. |
| `code/run_experiment.py` | Type safety | PASS | Public helpers typed; `ArmSpec`/`ArmResult` frozen dataclasses with typed array fields; conditioning mask passed explicitly so `bench_signal_arm` shares geometry while varying the population. |
| `code/run_experiment.py` | NaN handling | PASS | `ci_low_1s` None checks before comparisons; `_nan_eq` contrast NaN equality; `_float_match` with `RECON_TOL = 1e-9` for reconciliation. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` uses `pl.scan_parquet().slice(0, train_rows).collect()` — lazy scan, only first 49% by F01 file-order prefix; no full-file sort/collect; no TEST or holdout contact. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan, F01 prefix; `CloseTime.is_sorted()` assertion after collect; `train_end_ts` fence on every domain bar. |
| `code/run_experiment.py` | Memory/performance | PASS | Bounded per-cell forward scans (`bench_n ≈ 6`); column-pruned 1m loader; per-cell arrays released after summarisation; per-instrument `ProcessPoolExecutor`. |
| `code/run_experiment.py` | Safe optimization | PASS | Order-independent RNG `(BASE_SEED, cell_index, purpose)`; `M0/RM0/Z0/RZ0` keep the original purposes (byte-identical to EXP-060B); new hybrid arms use **disjoint dedicated purposes** (`H0`: `PB_HSEG*`; `RH0`: `PB_RH0_*`) — no existing stream shifts; fixed `INSTRUMENTS` merge order → byte-identical for any `--workers`. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over 17-instrument loop; workers via `as_completed`; no per-row logging. |
| `code/run_experiment.py` | Logging/output | PASS | Concise `main()` summary — per-object verdict, P11 tallies, defect flag; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports→path→constants→types→I/O→pure-compute→plotting→orchestration→`main`; output dirs created only in `run()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 5 plots from collected per-cell summaries (`efficacy`, `contrast`, `readout` lists); no reloads or regeneration. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring (question, design reference, 6-object set, dual-object individuality, binding endpoint); dataclasses + major helpers documented. |

## Numerical Validation

### Spot Checks

**Cell EURUSD-30m — native binding discriminator (`M0`).**
- `M0` qualifying m = 1281, median = 1.693 ATR, CI_low(1s) = 1.008 > 0 — median-viable. ✓
- `M0 − RM0` independent contrast median CI_low(1s) = 0.932 > 0 — beats `RM0`. ✓ → native `generalises = true`.

**Cell GBPUSD-30m — hybrid median-viable-but-not-attributable (`H0`).**
- `H0` m = 619, median = 0.120 ATR, CI_low(1s) = 0.008 > 0 — median-viable. ✓
- `H0 − RH0` contrast median CI_low(1s) = −0.146 ≤ 0 — does **not** beat `RH0`. ✓ → `MEDIAN_VIABLE_NOT_GENERALISE`. The hybrid edge here is not separable from a matched-random-on-MA draw.

**Cell NZDUSD-5m — the sole hybrid generalising cell (`H0`).**
- `H0` m = 3127, median = 0.089, CI_low(1s) = 0.026 > 0 — median-viable. ✓
- `H0 − RH0` contrast median CI_low(1s) = 0.0035 > 0 — beats `RH0` (marginally). ✓ → hybrid `generalises = true` (1 cell only).

**Population separation (EURUSD-5m).** Hybrid `H0` m = 3089 (3202-class, ZigZag-conditioned), native `M0` m = 8360 (8360-class, MA-segment-conditioned) — the two objects qualify materially different populations, confirming they are genuinely distinct, not a relabelling. ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Native `M0` qualifying count | ≥ 0, integer | [113, 10667] | YES |
| Hybrid `H0` qualifying count | ≥ 0, integer | [≈169 … <`M0`] per cell | YES |
| `M0` median | ℝ (ATR units) | within EXP-060B range | YES |
| `RH0`/`RM0`/`RZ0` draw_count | == matched object `.m` | per cell, per object | YES |
| Tail-share worst-5% | [0, 1] | ≈ [0.16, 0.34] | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| Native `M0` generalises composes? | YES (8 cells / 6 instruments / 8 non-4h) | YES | Above the P11 quorum (5/3/3). Identical to the prior (native-labelled) result. |
| Hybrid `H0` generalises composes? | NO (1 cell / 1 instrument / 1 non-4h) | YES | Powered grid composes (99 cells) ⇒ **EVIDENCE_AGAINST**, not INCONCLUSIVE. |
| P12 native `M0` reconciliation | 99/99 match (1e-9) | YES | `m0_match=true` all cells; max \|median diff\| = 0.0. |
| P12 `Z0` reconciliation | 99/99 match (1e-9) | YES | `z0_match=true` all cells. |
| P12 hybrid `H0` anchor | none; verified via `Z0` | YES | `h0_has_outcome_anchor=false`; `h0_cond_verified_via_z0=true` all cells (ZigZag `/STRONG-STAT` mask = EXP-053 retained set via `Z0` `n_conditioned`). |
| Causality violations | 0 | YES | All 99 member cells pass strict causal gate (ZigZag + MA reference ends ≤ entry; matched-random causal). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap | Within-block exchangeability of regime-clustered events | YES | Inherited EXP-049/053–060B; `b = round(m^(1/3))`, floor-validated by prior experiments. |
| Independent contrast (`H0−RH0`, `M0−RM0`, `Z0−RZ0`) | Bootstrap distributions independent | YES | Signal (haramis) and null (non-harami random in-regime) are disjoint pools by construction. |
| Mean + 10% trimmed mean | Tail-sensitive CI — wider is the measurement | YES | Per cell: mean CI wider than median CI; trimmed CI narrower than raw-mean CI. |

## Results Plausibility

- The native (`M0`) result is **byte-identical** to the prior EXP-061 result and reconciles to EXP-060B 99/99 — confirming the re-run correctly re-derived the native object the prior run had mislabelled. ✓
- The hybrid (`H0`) object qualifies a smaller, genuinely-different population (3202-class vs native 8360-class) and **fails to generalise** (1 cell). The genuinely-new hybrid object behaves differently from native — exactly the disambiguation Amendment 001 was raised to obtain. ✓
- The single hybrid generalising cell (NZDUSD-5m) clears both legs only marginally (contrast CI_low = 0.0035), reinforcing the EVIDENCE_AGAINST reading rather than contradicting it. ✓
- `Z0` beats `RZ0` in 7 cells on a different set (indices / higher TFs) — the disclosed substrate contrast reproduces the EXP-053/060 pattern. ✓

## Scope Compliance

- Analysis plan followed: YES (the dual-object fork; per-object P11/EVIDENCE_* never pooled).
- Deviations: none.
- Complexity budget: 3 methods / 3 budgeted; 5 plots / 5 budgeted; 0 new `xen/` modules / 0 budgeted (one thin orchestration change for `H0`/`RH0`).
- Holdout exclusion verified: YES — lazy `slice(0, train_rows)`; no full-file sort/collect; `CloseTime ≤ train_end_ts` fence.
- Registry preconditions satisfied: `MA-SUBSTRATE` + both modes (`hybrid`, `native`) REGISTERED (Phase 015 G0 / Amendment 001); HYP-014 listed; 0 candidate slots, 0 TEST reads. No new countable item. No TEST stratum read.
- Phase alignment: ✓ — EXP-061 is the Phase 015 lead L1 (design §3/§5/§7; D0-predeclarations P1–P12; Amendment 001).

## Signal-Registry Compliance

- Registry-relevant? Per-object characterisation readout feeding the **single terminal G-015** after the full Phase 015 slate; no closure or candidate registration here. The supersession status, however, **is** registry-bookkeeping-relevant and must be advanced (the prior entry is marked SUPERSEDED — the re-run resolves it).
- Disposition recorded: YES — `run_metadata.json` and `generalisation_readout.json` both carry the `registry` note (both modes parallel first-class per Amendment 001; 0 candidate slots, 0 TEST reads; feeds G-015).

## Issues

### Critical
None.

### Warning
None.

### Info

1. **P15 intrabar approximation noted.** The benchmark P15 fill path approximates unobserved intrabar motion (1-minute base bars not replayed). EXP-054 bounds the approximation. Inherited programme convention — not an EXP-061 defect.

2. **DE30 truncated history disclosure.** DE30 broker m1 history ends 2026-01-16; counts derive from its own realized timeline and are not span-comparable (VAL-003). Disclosed in `run_metadata.json`. No binding generalisation cell (native or hybrid) is on DE30 — no effect on either verdict.

## Re-Audit Requirements

None — PASS with no conditions.
