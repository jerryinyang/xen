# Audit Report: Experiment EXP-057

**Experiment:** EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)
**Audit Date:** 2026-06-16
**Phase:** 014-B (HA Harami Substrate & Capture)
**Family:** CF-HA-HARAMI-001 / HYP-010
**Verdict:** PASS

---

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

All scope, data-integrity, causality, determinism, reconciliation, invariant, and numerical checks pass. The implementation is correct, the results are internally consistent, and the EVIDENCE_FOR verdict (ADV-NONE wins with 23 cells / 15 instruments clearing P11) is mechanically correct.

---

## 1. Scope Compliance

| Check | Result | Evidence |
|---|---|---|
| Variant set matches scope | PASS | 4 binding variants: BENCH, ADV-EXTREME-raw, ADV-EXTREME-rr1, ADV-NONE. Code: `BINDING_VARIANTS` at `run_experiment.py:139-144`. |
| OAT on adverse leg only | PASS | Favourable target held at benchmark 50% (`benchmark_barriers`) for all variants; only adverse level varies. |
| 0 candidate slots, 0 TEST reads | PASS | TRAIN-only; no `test-read-ledger.md` tally; global holdout sealed. |
| 99-cell grid | PASS | 17 instruments × 6 domains − 3 EXCLUDED cells = 99 member cells. |
| Real-price discipline | PASS | HA prices only in `detect_ha_harami`/`annotate_ha_impulse`; all metrics (`C`, `M_sofar`, faded extreme, barriers, fills, returns, ATR) on real OHLC. |
| Complexity budget (4 methods / 5 plots / 1 module) | PASS | 4 stat methods (variant median CI, baseline median CI, paired contrast CI, independent contrast CI); 5 plots; 1 new module `xen/adverse_targets.py`. |
| Analysis plan followed | PASS | Code implements Steps 1-9 exactly as specified in `analysis-plan.md`. |

---

## 2. Data Handling & Holdout Exclusion

### Loading Pattern

`load_train_1m` (`run_experiment.py:204-220`) correctly:
1. Uses `pl.scan_parquet(path)` — lazy scan, no full file materialization
2. Reads total row count from lazy metadata only: `int(pl.scan_parquet(path).select(pl.len()).collect().item())`
3. `analysis_rows = int(total_rows * 0.7)`, `train_rows = int(analysis_rows * 0.7)` — first 49% of file-order rows
4. `pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()` — only TRAIN rows collected; **never sorts or collects the full file**

### Chronological Assertion

```python
if not train.get_column("CloseTime").is_sorted():
    raise RuntimeError(...)
```

Every cell's domain bars fenced to `CloseTime <= train_end_ts` via `build_domain` (`run_experiment.py:240-246`). Forward excursion scans clipped to data edge → `DATA_CENSORED`. **TEST and final-30% global holdout never read.**

**Verdict: PASS**

---

## 3. Causality / Look-Ahead Bias

### Entry-time quantities

Every quantity at `t_i` uses only bars `≤ t_i` and moves with `ConfirmTime ≤ t_i`:
- `M_sofar = |C − start_price|` — uses the known start pivot price and harami real close
- Faded-move extreme span: `[start_idx+1 … entry_idx]` inclusive — all bars with `CloseTime ≤ t_i` (`start_idx` = `EndTime_k` of a move confirmed `≤ t_i`)
- Favourable target, adverse level, adaptive cap: use only confirmed moves strictly before `t_i`

### Causality gates

`cell_causality_ok` (`run_experiment.py:586-609`) asserts:
1. Strictly increasing `CloseTime` in domain bar grid (`np.all(np.diff(epoch) > 0)`)
2. Reference move end epoch **strictly before** entry epoch (`end_epoch[k] < entry_epoch`)
3. Entry bar's `CloseTime ≤ t_i` (`epoch[entry_idx] ≤ entry_epoch`)
4. Reference move end bar **at or before** entry bar (`end_idx[k] ≤ entry_idx`)

### Forward scan

P15 first-touch resolver starts at `entry_idx + 1` and reads only up to `min(entry_idx+N, last_idx)`. Events truncated by the TRAIN data edge → `DATA_CENSORED` (excluded from median, disclosed as count).

**Results:** 0 causality violations across all 99 cells. `run_metadata.json: "causality_violations": []`.

**Verdict: PASS**

---

## 4. Determinism

### Seed architecture

Fixed master seed: `BASE_SEED = 20260615`. Per-(cell, variant, purpose) RNG:
```python
def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    return np.random.default_rng([BASE_SEED, cell_index, purpose])
```

Distinct purpose bases (lines 150-152):
- PB_STAT=1000, PB_HA=2000, PB_STATMAD=3000 (signal-arm bootstraps)
- PB_PC_STAT=4000, PB_PC_HA=5000, PB_PC_STATMAD=6000 (paired contrasts)
- PB_RAND_DRAW=7000, PB_RAND_BOOT=8000, PB_MASEG=9000 (baselines)

Per-variant offset `v.idx` (0-3) ensures each variant within an arm uses a different stream. No overlap between purpose bases: 1000-3000, 4000-6000, 7000-9000 with ≤4 variants max → streams are unique.

### Replay

`determinism_replay` (`run_experiment.py:944-961`) re-runs the first usable 5m cell per instrument end-to-end and asserts byte-identical outputs for all binding variants' stat arms + both baselines. 17 cells replayed; all pass.

**Results:** `run_metadata.json: "determinism_ok": true`, `"non_deterministic": []`.

**Verdict: PASS**

---

## 5. EXP-053 Reconciliation (Benchmark Anchor)

### Population match

`exp053_reconciliation` (`run_experiment.py:978-993`) cross-checks every member cell's BENCH variant against EXP-053's recorded per-cell `(m, median)`. Both count and median must match to `1e-9` absolute tolerance.

**Results:** 99/99 cells checked; all match exactly. Example (BTCUSD-5m):
- `bench_m = 3117, exp053_m = 3117, m_match = true`
- `bench_median = 0.05697336449019767, exp053_median = 0.05697336449019767, median_match = true`

`composition_readout.json: "exp053_mismatch": []`.

The conditioned population (`/STRONG-STAT` binding arm) is byte-identical to EXP-053, confirming the reuse of `live_in_progress_state` + `live_strong_stat` produces an identical filtered event set.

**Verdict: PASS**

---

## 6. Predeclared Invariant Checks

### 6a. BENCH reproduces EXP-053 (invariant 1)

Verified in §5 above. All 99 cells match. No mismatch.

### 6b. Raw ≤ rr1 adverse distance (invariant 2)

`cell_invariants` (`run_experiment.py:612-627`): asserts `adv_dist(ADV-EXTREME-raw) ≤ adv_dist(ADV-EXTREME-rr1) + 1e-9` element-wise on the conditioned buildable intersection.

**Results:** 0 violations. The `max(adv_dist_raw, fav_dist)` widening in `adverse_extreme_rr1` (`adverse_targets.py:173`) can only increase the distance, so this invariant is structurally guaranteed for every event.

### 6c. ADV-NONE yields 0 ADV outcomes (invariant 3)

`_none_adv_count` (`run_experiment.py:682-687`) sums ADV outcomes across all arms (stat, ha, statmad) and both baselines (matched_random, ma_seg) for ADV-NONE. Sentinel is `-inf` (rd=+1) / `+inf` (rd=-1) — `adv_hit` can never fire in the P15 resolver.

**Results:** `run_metadata.json: "none_adv_violations": []`. ADV count for ADV-NONE = 0 by construction across all 99 cells.

### 6d. Raw adverse-side ordering (invariant 4)

`cell_invariants` (`run_experiment.py:612-627`): asserts `adv_dist > 0.0` for all valid ADV-EXTREME-raw events. By construction `adv_dist ≥ 0.25·ATR_entry > 0` across all finite-ATR events. **Results:** 0 violations.

**Verdict: PASS**

---

## 7. Code Correctness — Detailed Review

### 7a. New module: `xen/adverse_targets.py`

| Function | Verdict | Notes |
|---|---|---|
| `faded_move_extreme` | PASS | Bounded per-event loop over causal span `[start_idx+1..entry_idx]`. Edge case: `start_idx==entry_idx` → entry bar alone. `min(Low)` for rd=+1, `max(High)` for rd=-1. NaN for unavailable. |
| `adverse_extreme_raw` | PASS | `adv = faded_extreme - rd·0.25·ATR_entry`. Degeneracy floor `adv_dist ≥ 0.10·ATR_entry` applied with `errstate(invalid='ignore')`. Warmup/degenerate/validity exclusion masks correct. |
| `adverse_extreme_rr1` | PASS | Calls `adverse_extreme_raw`, then `adv_dist = max(raw_adv_dist, fav_dist)`. No degeneracy floor (always ≥ fav_dist > 0). |
| `adverse_none_sentinel` | PASS | `adv = -inf` (rd=+1) / `+inf` (rd=-1); `adv_dist = inf`; `has_stop=False`. No extra exclusions. Comparison semantics safe: `low ≤ -inf` = False, `high ≥ +inf` = False in P15 resolver. |
| `barriers_with_adverse` | PASS | Correctly pairs benchmark favourable with supplied adverse. `ok = fav_dist > 0` for stop-less; `ok = fav_dist>0 & isfinite(adv) & isfinite(adv_dist) & adv_dist>0` for stopped. |

### 7b. Orchestration code: `code/run_experiment.py`

| Area | Verdict | Notes |
|---|---|---|
| TRAIN-only loader | PASS | Lazy scan, file-order prefix, no full-collect. |
| Domain aggregation | PASS | 5m strict; others `min_coverage=0.90` (frozen EXP-048/053). |
| HA harami → real bar mapping | PASS | Exact `CloseTime` match via `searchsorted` + equality assert (`_map_to_grid`). |
| Live in-progress state | PASS | `live_in_progress_state` reused verbatim from EXP-053. |
| `/STRONG-STAT` binding | PASS | p75 percentile over trailing-20 confirmed-move magnitudes (`live_strong_stat`). |
| `/ADV-EXTREME` prep | PASS | `faded_extreme_for` correctly maps `k` to `end_idx[k]` with guard for `k<0`. |
| Target construction | PASS | `build_variant_targets` dispatches by `v.kind`. BENCH via `benchmark_barriers`; others via the new module. |
| P15 path-ordered resolution | PASS | `resolve_path_ordered` reused; bounded sequential scan. |
| Realised returns | PASS | `r_e = rd·(exit−C)/ATR_entry`; ATR from `wilder_atr(14)`. |
| Bootstrap CI | PASS | Moving-block, `b=round(m^(1/3))`, `N_BOOT=10k`, fixed seed. |
| Paired contrast | PASS | `paired_median_contrast_ci` on common qualifying subset `S`; correct pairing logic. |
| P11 composition | PASS | `_variant_composition` → `_win_tally` → `_evidence_label`. Mechanical EVIDENCE_* fork per the interpretation guide. |
| Plots | PASS | 5 bounded plots from collected summaries + pooled viable-cell returns; no reloads. |
| Edge cases | PASS | Empty haramis, moves, MA windows, pools, degeneracy, DATA_CENSORED all handled explicitly. |

### 7c. Potential Issue: `_zero_reasons` duplication

The `_zero_reasons` helper is defined in both `adverse_targets.py:99-103` and `run_experiment.py:384-387`. The `run_experiment.py` copy is used in `build_variant_targets`. This is harmless duplication, not imported from the module. **Info note** — affects no correctness.

### 7d. Potential Issue: `TickVolume` loaded but unused

`TickVolume` is loaded in `load_train_1m` to match the column schema used by EXP-053/056's `aggregate_ohlc`, ensuring byte-identical aggregation (the BENCH reconciliation anchor). It enters no metric. **Info note** — pre-approved in governance review.

**Verdict: PASS (2 Info notes)**

---

## 8. Numerical Validation

### 8a. Spot check: BTCUSD-5m BENCH

```
m = 3117
fav = 745, adv = 728, timecap = 1644
fav + adv + timecap = 745 + 728 + 1644 = 3117 = m ✓
r = 745 / (745 + 728) = 0.5058 ≈ 0.50 ✓ (consistent with EXP-049/053 null)
Positive returns = 1613, negative returns = 1504
1613 + 1504 = 3117 = m ✓
positive_returns (1613) ≥ fav (745) ✓ (some TIMECAP returns positive)
negative_returns (1504) ≥ adv (728) ✓ (some TIMECAP returns negative)
```

### 8b. Spot check: BTCUSD-5m ADV-EXTREME-raw

```
m = 3117, median = -0.368, r_firsthit = 0.278
fav = 627, adv = 1631, timecap = 859
fav + adv + timecap = 627 + 1631 + 859 = 3117 = m ✓
r = 627 / (627 + 1631) = 0.278 — well below 0.50 ✓ (tight stop → many ADV hits)
Median negative (-0.368) — consistent with many tight stop-outs ✓
```

### 8c. Spot check: BTCUSD-5m ADV-EXTREME-rr1

```
m = 3117, median = 0.059, r_firsthit = 0.509
fav = 748, adv = 722, timecap = 1647
r ≈ 0.509 — similar to BENCH (both are 1:1 R:R) ✓
Widening the extreme stop to ≥1:1 restores the r ≈ 0.50 baseline ✓
```

### 8d. Spot check: BTCUSD-5m ADV-NONE

```
m = 3117, median = 0.163, r_firsthit = 1.0
fav = 802, adv = 0, timecap = 2315
adv = 0 by sentinel construction ✓ (invariant: none_adv_violations = [])
r = 1.0 (degenerate by construction, disclosed) ✓
Median 0.163 > BENCH 0.057 — more FAV (802 vs 745), more TIMECAP (2315 vs 1644),
but positive expected value dominates the negative timecap tail ✓
```

### 8e. Paired contrast: ADV-NONE vs BENCH (BTCUSD-5m)

```
contrast_bench_low = 0.083 > 0 → beats_bench = true ✓
contrast_bench_n = 3117 ≥ 30 ✓
```

### 8f. P11 composition verification

| Variant | POWERED (≥30) | VIABLE (CI_low>0) | WIN (viable+beats) | P11 met? |
|---|---|---|---|---|
| BENCH | 99/17 | 8/7 | 0/0 (reference) | N/A |
| ADV-EXTREME-raw | 99/17 | 0/0 | 0/0 | No |
| ADV-EXTREME-rr1 | 99/17 | 8/7 | 0/0 | No |
| ADV-NONE | 99/17 | 27/15 | 23/15 | **YES** |

ADV-EXTREME-raw is never better than benchmark (0 viable cells — all CI spans 0). ADV-EXTREME-rr1 is viable in 8 cells but never beats benchmark (extreme anchoring alone does not outperform the 1:1 benchmark). ADV-NONE wins in 23 cells over 15 instruments — a robust result well above the P11 quorum (5 cells / 3 instruments), not fragile.

### 8g. EVIDENCE_* classification

Mechanically correct per the interpretation guide:
- `passers = ["ADV-NONE"]` → EVIDENCE_FOR ✓
- Not SUBSTRATE/METHOD_DEFECT (`is_defect = false`)
- Not INCONCLUSIVE (abundant power: 99/17 powered for every variant)
- Not EVIDENCE_AGAINST (≥1 alternative passes)

**Verdict: PASS — all numerical checks consistent**

---

## 9. Statistical Assumptions

| Method | Assumption | Holds? | Evidence |
|---|---|---|---|
| Moving-block bootstrap median CI | Local temporal dependence, blocks preserve series structure | YES | Non-parametric; `b = round(m^(1/3))` adapts to sample size; does not assume i.i.d. or normality |
| Paired moving-block bootstrap | Common-event coupling removes event-level noise | YES | Both variant and benchmark scored on same entries → paired design correct |
| Independent bootstrap contrast (baselines) | Independent event sets | YES | Baselines at different timestamps → independent design correct |
| Median as location estimator | Robust to fat tails | YES | ATR-normalised returns are fat-tailed (FAV/ADV cluster, TIMECAP spreads, ADV-NONE heavy negative tail) |
| Regime clustering via contiguous blocks | Price regimes persist over time | YES | Block sampling preserves regime structure within each resample |

No violations. The statistical approach is appropriate and well-justified.

---

## 10. Results Plausibility

| Observation | Expected? | Notes |
|---|---|---|
| BENCH r ≈ 0.506 (99 cells) | Yes | Consistently ≈0.50 across cells, replicating EXP-049/053 |
| ADV-EXTREME-raw r well below 0.50 | Yes | Tight stop → r ≪ 0.50 as predicted in scope |
| ADV-EXTREME-raw median negative | Yes | Converts wins to losses |
| ADV-EXTREME-rr1 r ≈ 0.50 and median ≈ BENCH | Yes | 1:1 R:R restores benchmark-like behaviour; extreme anchoring alone doesn't help |
| ADV-NONE r = 1.0 degenerate | Yes | By construction; disclosed |
| ADV-NONE median > BENCH median | Plausible | Removing the stop lets events run → more FAV hits compensate negative timecaps |
| ADV-NONE beats benchmark on 23/99 cells | Plausible | Widespread effect across 15 instruments |
| ADV-EXTREME-raw never beats benchmark (0 WIN cells) | Plausible | The tight stop destroys expectancy by converting winners to stop-outs faster than it saves on loser tails |

All outcomes are internally consistent and within expected qualitative ranges.

---

## 11. Issues

### Critical (0)

None.

### Warning (0)

None.

### Info (2)

1. **Duplicated `_zero_reasons` helper**
   - Files: `code/run_experiment.py:384-387` and `python/src/xen/adverse_targets.py:99-103`
   - Description: The `_zero_reasons` function for building exclusion masks is defined independently in both modules. The `run_experiment.py` copy is used in `build_variant_targets` (which does not import the private function from `adverse_targets.py`). Both implementations are identical. No correctness impact.

2. **`TickVolume` loaded in TRAIN frame**
   - File: `code/run_experiment.py:210`
   - Description: `TickVolume` column is loaded to maintain byte-identical aggregation with EXP-053/056 (required for BENCH reconciliation). It enters no barrier, fill, return, expectancy, or any other metric. Pre-approved in governance review.

---

## 12. Re-Audit Requirements

None. This is a final PASS.

---

## 13. Summary for Interpretation Stage

EXP-057 is a clean experiment with no defects.

**Key findings to carry forward:**
- **Verdict: EVIDENCE_FOR** — `/ADV-NONE` (removing the adverse barrier) improves conditioned HA harami gross median expectancy vs the benchmark 1:1 adverse target, on 23 cells over 15 instruments (robustly above the P11 quorum, not fragile).
- `/ADV-EXTREME-raw` (tight faded-move extreme stop, R:R free) destroys expectancy — 0 viable cells, median negative everywhere.
- `/ADV-EXTREME-rr1` (extreme-anchored, ≥1:1) is viable in 8 cells but **never beats the benchmark** — extreme anchoring alone, at the same R:R, does not beat the 1:1 reference. This isolates the mechanism: the ADV-NONE improvement comes from removing the stop entirely, not from repositioning it.
- The `r` narrative is confirmed: ADV-EXTREME-raw pushes `r ≪ 0.50` (tight-stop, many ADV hits) while ADV-NONE produces degenerate `r=1.0` — both are disclosed secondaries; the binding endpoint (median expectancy) correctly captures the timecap tail that `r` misses.
- 0 candidate slots consumed, 0 TEST reads, global holdout sealed.
- EVIDENCE_FOR is not a phase closure — routing deferred to the single 014-B G2 across the full slate.
