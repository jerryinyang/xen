# Audit Report: Experiment EXP-029

cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

EXP-029 closes the EXP-028 omission by running the **corrected** C# `AvwapBounceModel`
(pyramid bounces opened as independent positions, executed completion serialized) on
cTrader per-bar streaming, then evaluating the emitted runs through the **same**
estimand and the **same** frozen EXP-027 inference tail EXP-028 used. The
implementation matches the approved scope/plan, the holdout fence is enforced in two
places (in-robot + Python re-assertion), the binding gates are genuinely falsifiable,
and every result CSV reconciles against `run_metadata.json` and against the EXP-028
reference under independent recomputation. The reported `CONSISTENT` disposition
(all 3 domains CONSISTENT + EVIDENCE_FOR) is trustworthy.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Estimand, alignment, inference, and gate logic all correct (detail below). |
| `code/run_experiment.py` | Edge cases | PASS | Empty cells, underpowered domains (`effect=None`→`UNDER_POWERED`, cannot be INCONSISTENT), open/right-censored positions, no-control events all handled explicitly. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions; explicit `int`/`float`/`Boolean` casts on emitted columns. |
| `code/run_experiment.py` | NaN handling | PASS | `ExitLifetimeBps`=NaN for open positions handled in `build_exit_parity`; `nansum`/`nanmean` in equity companion; non-recovered effects are `None`, never 0 (D7). |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_cell_frame` re-asserts `max(SourceCloseTime) < AnalysisEndUtc` per instrument (D5); final 30% never loaded; C# `_fence.AssertCanEmit` also fences positions and event-detail rows. |
| `code/run_experiment.py` | Loader ordering | PASS | Per-cell lazy `read_parquet` then `sort("SourceCloseTime")`; strict-monotonic assert; no full-dataset materialization. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-cell loop (`tqdm`); per-cell vectorized reconciliation; only bounded aggregates reach plotting/pandas. |
| `code/run_experiment.py` | Safe optimization | PASS | `scan_lifetime` kept genuinely sequential per event/control (imported EXP-022 unchanged); vectorization only on index selection/reconciliation — no membership/ordering/denominator change. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over the 12-cell outer loop. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports→path→constants→helpers→orchestration→`main`; output dirs created only in `ensure_output_dirs` (orchestration). |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots consume already-computed `primary_res`/`primary`/`ref`; no heavy reload. |
| `code/run_experiment.py` | Docstrings | PASS | Module + all functions documented with rationale and D/F-guard references. |
| `code/event_method.py` | Frozen identity | PASS | sha256 over named `FROZEN_FUNCTIONS` hard-asserted `== ea261b9ee0a8aca3` AND `== EXP-028 recorded hash`; mismatch aborts (F05). |
| `StrategyHost/AvwapBounceModel.cs` | Pyramid correction | PASS | Single-position state replaced by `List<OpenPosition>`; every bounce (incl. `isPyramid`) opens an independently-tracked position with its own frozen targets; `pyramid_skipped` removed. |
| `StrategyHost/AvwapBounceModel.cs` | Completion / exit-parity | PASS | `MaybeCompletePosition` evaluates each position independently (favorable→adverse→trend_change precedence, same as EXP-022); backfills `ExitIdx/Time/Close/Reason/Bars/LifetimeBps`; `ExitLifetimeBps = 10000·dir·(ln Close − ln EntryClose)` — identical formula to the Python scan. |
| `StrategyHost/SignalRecords.cs` | Schema | PASS | `RegimeId`/`RegimeDirection` added with sentinels (-1/0) → backward-compatible for MA/Donchian models. |
| `StrategyHost/StrategyRunParquetWriter.cs` | Serialization/fence | PASS | `avwap_events.parquet` written with all 21 contract columns; `SetAvwapEventDetails` fence-asserts every `TriggerTime` before write. |
| `Xen.cs` | Wiring | PASS | Serializes `EventDetails` on dispose only for `AvwapBounceModel`. |

## Numerical Validation

### Spot Checks (independent recompute vs CSV)

Parity arithmetic recomputed from the two experiments' `event_level_results.csv` and
pyramid counts (auditor script):

| Domain | \|Δeffect\| | equiv margin `max(2,25%·ref)` | equiv | divergent (`>max(2,50%·ref)`) | count Δ | pyramid Δ |
|--------|------------|------------------------------|-------|-------------------------------|---------|-----------|
| 5m | 0.007126 | 2.000 | True | False | 0.00086 | 0.00064 |
| 1h | 0.053861 | 5.846 | True | False | 0.00325 | 0.00451 |
| 4h | 0.000000 | 17.254 | True | False | 0.00000 | 0.00000 |

All reproduce `parity_comparison.csv` (`magnitude_equivalent=true`, `magnitude_divergent=false`,
`count_within_10pct=true`) to the printed digits. `effect_delta_bps` (0.00713 / 0.05386 / 0.0)
matches exactly.

- Exit-parity (F01): `match_rate=1.0` on all domains with `max_bps_discrepancy`
  1.78e-11 (5m) / 1.39e-13 (1h) / 0.0 (4h). The **non-zero** residuals confirm the
  grade compares two genuinely independent computations (C# float vs Python) rather
  than a tautology — a real multi-position completion bug would have dropped the rate.
- Signal-layer 5m (F03): trigger match 0.9990/0.9978/0.9998/1.0 (all ≥0.98); matched
  frozen-target median rel-diff 0.0 (≤1e-3). `signal_5m_ok=true`.
- Reconciliation: `reconciliation_bad=0` (every PRIMARY event's `lifetime_bps`
  reproduces the cTrader-frame log-return recompute within 1e-3 bps).

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `direction` | {+1,-1} | bull/bear split present every cell | YES |
| Effect (bps) | finite ℝ, sign per hypothesis | +5.79 / +23.33 / +69.02, all CI_low>0 | YES |
| Holm p | ≤ α=0.05 for EVIDENCE_FOR | 0.002997 all domains | YES |
| `SourceCloseTime` | strictly increasing, < AnalysisEndUtc | asserted in `load_cell_frame`; cell `max_source_close_time` < fence in metadata | YES |
| pyramid split sum | == metadata total | 6254+445+84=6783 == `pyramid_split.pyramid` | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| 4h CI half-width | 20.53 bps (n=187) | YES | Wide as expected for sparse 4h; consistent with EXP-001/003 4h power notes. |
| Holm p floor | 0.002997 = 3/1001 | YES | Permutation resolution floor (N_PERM=1000), identical to EXP-028. |
| Effect monotone in domain | 5.79<23.33<69.02 | YES | Same ordering and magnitude band as EXP-028. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Frozen EXP-027 tail | mean-zero / sign-symmetric paired-excess null | YES (inherited) | symmetric own-exit estimand; not re-tested here (EXP-027 METHOD_VALID gate). |
| Matched-control excess | controls drawn & completed on the **same** cTrader feed as events | YES | controls rebuilt in Python via imported EXP-021/022 helpers on the cTrader `RealClose` frame (D2). |
| Timestamp alignment | event triggers map to frame indices by `SourceCloseTime` | YES | `load_event_detail` hard-fails on missing/disagreeing trigger timestamps and on emitted-`TriggerIdx` mismatch (D6). |

## Results Plausibility

All three domains EVIDENCE_FOR with CI_low>0 and Holm p well below α, effects in the
same band as EXP-028, counts within ±0.5%, pyramid split within ±0.5%. The
`CONSISTENT` disposition and the EXP-028 → cTrader-confirmed upgrade are
well-supported by the artifacts.

## Scope Compliance

- Analysis plan followed: **YES** (Steps 0–7 all implemented as written; F01–F05
  hardenings present and binding; F07 deviation implemented as documented).
- Deviations: **F07 (documented, non-binding)** — secondary-horizon {1,3,6} stability
  inputs are computed from the cTrader feed (`_fixed_horizon_rows`) rather than drawn
  from EXP-021's `reaction_observations.csv` as EXP-028 did. This is the correct
  cTrader-feed analog and feeds only the non-binding `decide_label` stability guard;
  it never enters the PRIMARY effect. (See Info #2.)
- Complexity budget: 3/3 statistical tests (bootstrap CI; sign-permutation+Holm;
  parity comparison reusing 1–2), 3/3 plots, 1/1 new Python module + the
  scope-permitted C# correction. Within budget.
- Holdout exclusion verified: **YES** (in-robot fence + Python re-assertion; final 30%
  never loaded; local timebars never read for the estimand).

## Issues

### Critical

None.

### Warning

None.

### Info

1. **4h PRIMARY effect is bit-identical to EXP-028 (`69.0156543344473`), while 5m/1h
   differ slightly.** This is stronger than feed-drift expectations (VAL-002: 5m
   float-exact, 1h/4h ≤1.83 bps). Verified it is **not** data reuse: `compare_parity`
   reads the EXP-029 figure from `primary_res` (computed from the cTrader frames) and
   the EXP-028 figure from the reference CSV — there is no code path copying the
   reference into the EXP-029 column, and the two CIs differ (49.32 vs 46.84,
   different `seed_for` draws). The most likely cause is that the cTrader 4h resampled
   feed coincided exactly with the local 4h bars for all 187 events + controls within
   the fence (the coarsest domain, fewest bars). It strengthens, not weakens, the
   CONSISTENT verdict; the interpreter should present it as such and not over-read it.

2. **Secondary-horizon numbers in `event_level_results.csv` are not directly comparable
   to EXP-028's** (F07). e.g. 4h `sec_h6_bps` 94.01 (EXP-029) vs 83.22 (EXP-028);
   `event_diagnostics.csv` `fixedh_*` likewise differ. This is the intended,
   documented control-selection difference and affects only the non-binding stability
   guard — all verdicts remain EVIDENCE_FOR. The **PRIMARY** effect is the sole parity
   object. Documenter/interpreter should state this so the secondary divergence is not
   mistaken for a parity discrepancy.

3. **`exit_parity.csv` n_events (15027/1038/236) exceeds PRIMARY n_events
   (12784/927/187) by design, not by bug.** Exit-parity (F01/F06) grades the full
   valid-target event population (`role=="event"` in the lifetime table), whereas
   PRIMARY additionally requires a completed outcome, per-instrument reportability,
   and ≥`MIN_CONTROLS` controls. The funnel is coherent: ~19.2k emitted 5m bounces →
   15027 valid-target events (after `fav_bps>0 ∧ adv_bps<0`) → 12784 reportable
   PRIMARY events. No double-counting.

4. **Regimes without events get a placeholder `anchor_idx`** in `build_regimes_cell`
   (`anchor_by_regime.get(cur, i)`). Confirmed harmless: such regimes have no events,
   so their LUT anchor is never referenced by `build_cell_lifetimes` (which raises if
   an event's `regime_id` is absent from the summary). Noted for awareness only.

## Re-Audit Requirements

None — verdict is PASS with no Critical or Warning findings. The four Info notes are
context for the interpreter/documenter (especially #1 and #2, which should be
surfaced in `results.md`/`report.md`), not fixes.
