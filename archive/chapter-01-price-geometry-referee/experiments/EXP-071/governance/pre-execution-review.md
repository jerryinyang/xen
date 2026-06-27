# EXP-071 — Pre-Execution Governance Review (Stage 4)

**Reviewed:** 2026-06-18
**Artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Checkpoint:** `2026-06-18-016-harami-candidate-screening` (`design.md`,
`D0-predeclarations.md` P1-P15, `D0-amendment-003`, `D0-amendment-004`)

```text
VERDICT: APPROVE
```

---

## Signal-registry precondition (programme file-drawer control)

| Check | Result |
| --- | --- |
| Candidate family registered & OPEN | PASS — `CF-HA-HARAMI-001` REGISTERED / OPEN; `CAND-001` first candidate active (G-015, 2026-06-18). |
| Hypothesis registered | PASS — HYP-024 / EXP-071 in `multiplicity-registry.md` (Phase 016 batch, line 554). Its `PENDING — EXP-070 PASS required` precondition is now cleared (EXP-070 = CALIBRATION_DELIVERED, D0-amendment-004). |
| No unregistered countable item | PASS — no new variant/detector/parameter branch; the binding arm, disclosed arms, RM-native null, and composition threshold all pre-exist in D0 P2/P4/P9. |
| TEST-stratum tally stated | PASS — scope states the 6 binding strata at **0 counted reads**; `test-read-ledger.md` confirms (cap = 2 lifetime/stratum). EURUSD excluded instrument-wide. |

## Holdout, look-ahead, and real-price discipline

| Check | Result |
| --- | --- |
| Holdout never loaded | PASS — `load_test_1m` slices `[0, analysis_cutoff)` only; `analysis_cutoff = int(total*0.7)`; the final 30% is never materialized. Forward scans clip at the analysis-set edge → `DATA_CENSORED`. |
| Chronological split | PASS — lazy scan sorted by `CloseTime`; TRAIN = first 49%, TEST = next 21% by 1-minute-row boundary; sortedness asserted on both slices. |
| Look-ahead prevention | PASS — combined TRAIN+TEST domain series is causal and asserted strictly increasing at the seam; only `entry_epoch > train_end_epoch` events enter the binding inference; matched-random pool restricted to TEST-window bars; freeze file written before any TEST load. |
| Real-price outcomes | PASS — HA candles used for harami detection only (`harami_entry_indices`); every return is computed by the frozen real-price machinery (`signal_arm`/`matched_random_arm` on `RealOpen/High/Low/Close`). No HA-price metric anywhere. |
| Timestamp alignment | PASS — domain alignment by `CloseTime` epoch; no bar-index alignment. |

## Freeze-before-TEST (D0 P8)

PASS. `run()` enforces strict ordering: (1) dependency gates → (2) P12 reconciliation on
TRAIN only (`load_train_1m`) → (3) `write_freeze_file` (atomic `.tmp` + `os.replace`, SHA-256
appended) → (4) TEST inference. `load_test_1m` additionally hard-fails if the freeze file is
absent, so no code path can touch a TEST row before the freeze exists and is hash-pinned. The
freeze payload records the 6-cell family, FPR exclusions (none), Null-A/Null-B FPR, calibrated
margins, temporal flags, composition threshold verbatim, inference params, and composite seed.

## Binding FPR object (D0-amendment-004) — correct handling

PASS, and notably correct. EXP-070's `calibration_map.csv` was **not regenerated** after
D0-amendment-004 (the amendment changed interpretation only); its `verdict` column still reads
`FPR_EXCLUDED` for 5 cells under the superseded both-nulls rule. The code **does not** gate on
that stale column — `assert_dependency_gates` keys the binding PASS criterion on
`fpr_conj_nullA ≤ 0.05` (all six: 0.035/0.014/0.031/0.031/0.014/0.018 → all PASS), with the
stale verdict recorded for provenance only. Null-B FPR is carried as advisory. This matches the
amended binding rule exactly.

## Reuse fidelity (frozen inference machinery)

PASS. `signal_arm`, `matched_random_arm`, `contrast` semantics, `_summarize_arm`,
`bootstrap_median_distribution`, `median_ci`, `bootstrap_stat_distribution`, and
`_winsorized_mean` are imported unchanged from EXP-068 (verified: that module has no
import-time side effects). The matched-random TEST-window restriction is achieved **without
modifying frozen code** — by marking TRAIN-region bars ineligible in the `warmup` mask passed
to `matched_random_arm` (the only effect is restricting the draw pool to TEST bars). P12
reconciliation re-runs the frozen `compute_cell` on TRAIN and asserts reproduction of EXP-068
BENCH+PARTIAL-V2A, EXP-061 M0, and EXP-066 PARTIAL-V2A at 1e-9 — the freeze-faithfulness proof
required before any TEST contact (D0 P1). TEST family set-equality (`g015` ex-EURUSD == the 6
P5 cells) is asserted.

## Scope, criteria, complexity budget

| Check | Result |
| --- | --- |
| Single falsifiable question | PASS — one TEST-confirmation question; verdict space exhaustive (CONFIRMED / INCONCLUSIVE / NOT_CONFIRMED). |
| Criteria attainable, measurable | PASS — `≥3 clear / ≥2 instruments / ≥2 non-4h` is attainable on a 6-cell / 4-instrument / 5-non-4h family; no percentage-vs-zero baseline; effects in ATR units with bootstrap CIs. |
| Event denominators defined | PASS — qualifying TEST harami events per cell; ≥30 power floor; below-floor cells excluded with explicit `below_floor` disposition (never NaN-propagated). |
| Complexity budget | PASS — 4 statistical tests (bootstrap median/mean CI; beats-RM contrast; Holm; deterministic margin check), 5 plots, 1 experiment-local module; no new/modified `python/src/xen/` module. |
| Code organization & standards | PASS — VAL-001 sectioning; type hints/docstrings; output dirs created in `run()` only; no import-time side effects; `tqdm` on the bounded outer loops; lazy scan + projection + slice; plots from bounded collected summaries; deterministic seeds with a full second-pass byte comparison (D0 P7 Leg 3). |

## Info notes (non-blocking; for Stage 5 audit / Stage 6 interpretation)

1. **Portfolio pooling (D0 P10, non-binding).** The composite pools per-event returns across
   powered cells (each event weight 1) with block `b = round(m_total^(1/3))`, matching the
   plan's stated bootstrap. The phrase "equally weighted by cell" is interpreted as "no
   per-cell portfolio weight applied," consistent with `m_total^(1/3)`. Since this is a
   disclosure that gates nothing, the interpretation is acceptable; the Stage 6 analyst should
   read it as an event-pooled composite.
2. **Holm family size.** The implementation applies Holm over the powered binding cells and
   records `holm_family_size`. With all six cells expected powered (TRAIN counts ≥152), this is
   k=6 in practice; below-floor cells carry no testable p-value. Transparent and recorded.
3. **Registry row text lag.** The `multiplicity-registry.md` HYP-024 row uses the earlier
   "non-4h FX core" framing; the binding family is the D0 P5/P9 six cells (incl. US2000-4h, with
   the ≥2-non-4h sub-rule). The code follows the authoritative D0 spec. Reconcile the registry
   row text at Stage 7 documentation.
4. **Minor redundant loads.** `instrument_meta` re-loads a TEST slice already loaded inside
   `resolve_test_cell`; bounded (≤4 instruments, 6 cells) and not a correctness concern.

No Critical or Warning issues. Scope, plan, and code are mutually consistent and faithful to
the frozen D0 predeclarations and amendments.
