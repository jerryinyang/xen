# Audit Report: Experiment EXP-066

**Independent second-opinion audit** (the implementation and the pre-execution
review were produced by a different agent; this audit re-derives every check from
the code and the emitted results rather than trusting the prior PASS table).

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-066 (dual-object MA(20,50)-substrate position-management exits) is correct and
trustworthy. The binding P12 reconciliation is **genuine** (all 198 BENCH cells
reproduce EXP-061 M0/H0 to exactly 0.0 in both count and median, on 99 checked
cells), the RNG purpose blocks are arithmetically disjoint, every predeclared
structural invariant holds in the emitted data, all causality/determinism gates
pass, and the headline verdict (native **EVIDENCE_FOR** via PARTIAL-V2A; hybrid
**EVIDENCE_AGAINST**) reproduces independently from `per_cell_expectancy.parquet`.
The pre-execution `last_train_idx` fix is present in the code.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | 12-arm × 2-object grid built correctly; BENCH uses the frozen `resolve_path_ordered` EXP-061 path, alt arms use `xen.position_exits`. Conjunction `arm_wins = median_viable ∧ beats_rm ∧ beats_bench` verified row-by-row (0 violations). |
| `code/run_experiment.py` | Pre-exec fix present | PASS | `matched_random_arm` declares `last_train_idx: int` as final param (line 710) and is passed at the call site in `_resolve_objects` (line 938). Not merely claimed — confirmed in source. |
| `code/run_experiment.py` | Edge cases | PASS | `_empty_arm`, empty-cell handling, `n<2` MA crossover guards, `m==0` short-circuits, NaN-safe contrast/paired returns. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` reads only Parquet row count (metadata) + `slice(0, train_rows)`; never sorts/collects the full file; asserts chronological; every domain bar fenced `CloseTime ≤ train_end_ts`. TEST/final-30% never read. |
| `code/run_experiment.py` | Loader ordering | PASS | F01 file-order prefix is the project convention for this lineage (EXP-049/053–065); chronological order is *asserted* (`is_sorted`), not imposed by a post-slice sort. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-instrument `ProcessPoolExecutor`, native threads pinned to 1 before numpy/polars import, per-cell `del`, forward scans bounded by `bench_N`, plots from collected summary rows only. |
| `code/run_experiment.py` | Safe optimization | PASS | Sequential causal resolvers (`_scan_event`, `build_active_stops`) kept explicit; vectorization (bootstrap block matrix, leg-level broadcast) does not touch temporal ordering or look-ahead. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over `INSTRUMENTS` in both sequential and pooled paths. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER.info` confined to `main()`; helpers return data. |
| `code/run_experiment.py` | Organization / import side-effects | PASS | Thread-env → imports → path setup → constants → helpers → orchestration → `main`. Output dirs created only in `run()`. No module-level writes. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 5 plotters consume the already-collected `rows`; no reloads/regeneration. |
| `code/run_experiment.py` | Docstrings/type hints | PASS | Public functions typed and documented. |

### Reused `xen/` modules (calling convention + semantics preserved)

- `xen.position_exits.resolve_legs` / `_scan_event` — shared-stop "binds-all-open-legs"
  invariant (`_close_open`) and P15 path order (bullish `O→L→H→C`, bearish `O→H→L→C`)
  are intact; EXP-066 passes **real** OHLC arrays only. ✔
- `xen.position_exits.build_active_stops` — monotone ratchet, seeds at `adv` (or NaN
  for `trail_init_none`), advances only on secondary-confirm bars `ConfirmIdx ≤ i`,
  uses the *previous* confirmed pivot (causal). Called with the secondary
  (`atr_mult=0.5`) ZigZag arrays. ✔
- `xen.position_exits.reversal_event_targets` — module docstring is written generically
  ("primary-ZigZag"), but the function is substrate-agnostic; EXP-066 correctly feeds it
  the **MA-segment** `confirm_epoch/confirm_idx/direction` (scope's one P8 substitution),
  plus the per-object conditioned-harami arrays for the opposing-harami trigger. Reversal
  bar = first of {next MA seg `Direction==rd`, next opposing conditioned harami `-rd`},
  bounded by `bench_N`. ✔
- `xen.expectancy.{resolve_path_ordered, realised_returns, qualifying_mask, contrast_ci,
  bootstrap_median_distribution, median_ci, benchmark_barriers, live_in_progress_state,
  live_strong_stat, adaptive_time_caps_by_epoch}` — used verbatim. The experiment's local
  `bootstrap_stat_distribution` (mean/trim) replicates the median bootstrap's block
  construction byte-for-byte (same `b`, `n_blocks`, `max_start`, `offsets`, `idx`), with a
  dedicated RNG stream, so the median path is untouched. ✔
- `xen.favourable_targets.paired_median_contrast_ci` — called on the common qualifying
  subset (`arm.qual & bench.qual`), `n_common ≥ 30` gated. ✔

---

## Numerical Validation

### Spot checks (independently recomputed from `results/`)

**P12 reconciliation (the binding SUBSTRATE/METHOD_DEFECT gate).** Joined EXP-066 BENCH
to EXP-061 `M0`/`H0` on (instrument, domain):

- 198 BENCH cells joined (99 native + 99 hybrid), 0 unmatched.
- `max |m diff| = 0`, `max |median diff| = 0.0`, 0 cells exceeding `RECON_TOL=1e-9`.
- Populations are genuinely distinct per object (e.g. BTCUSD-5m native m=10667 vs hybrid
  m=3044), confirming the reconciliation is not vacuously comparing one object to itself.
- `exp061_checked_cells = 99`, anchor parquet path exists, `exp061_mismatch = []`. The
  gate is real and passing.

**Composition tally (independent recompute vs metadata).** Recomputed every alt-arm P11+P6
tally (`≥5 cells / ≥3 instruments / ≥3 non-4h`) directly from the parquet `arm_wins` flags:
0 mismatches vs `per_object_arm_composition`. The single composing winner is **native
PARTIAL-V2A** (21 cells / 13 instruments / 21 non-4h) — the EXP-060B champion favourable
side, exactly the predicted lever. Hybrid has no composing arm → EVIDENCE_AGAINST.

**Invariants (recomputed over all 2,376 member rows):**

| Invariant | Result |
|-----------|--------|
| `arm_wins == median_viable ∧ beats_rm ∧ beats_bench` (alt arms) | 0 violations |
| BENCH never flagged `arm_wins` | 0 violations |
| matched-count `rm_draw_count == signal m` | 0 violations |
| `rm_m ≤ rm_draw_count` (null resolves ≤ drawn) | 0 violations |
| exit-reason weights sum to 1.0 (m>0 rows, tol 1e-9) | 0/2376 off |
| power floor: `median_viable` with m<30 | 0 |
| `r_firsthit` non-null only on BENCH | confirmed (BENCH only) |
| tail-share finite, ∈ [0.16, 0.50], no inf/NaN | confirmed |
| `readiness.construction_pass` / `causality_ok` all True (99 cells) | confirmed |
| `reconciliation.consistent` + per-object m/median match all True | confirmed |

### Mechanism firing (exit-reason composition, native, m>0 cells)

Each exit pathway fires only on the arms that define it:

- `ew_REVERSAL>0` → only PARTIAL-V1/V2C, COMBINED-V1/V2C (the 4 reversal arms).
- `ew_FIRST_PROFIT>0` → only PARTIAL-V1, COMBINED-V1.
- `ew_TRAIL>0` → only the 7 TRAIL-*/COMBINED-* arms.
- COMBINED arms show `ew_ADV = 0` (structure trail correctly **replaces** the fixed 1:1
  stop that binds open legs), TRAIL-PURE ≈ 0.995 trail / 0.005 timecap.
- BENCH ≈ FAV 0.364 / ADV 0.364 / TIMECAP 0.272 — balanced first-hit consistent with the
  EXP-061 `r≈0.5` replication.

### Range / structure checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| objects | {nat, hyb}, never pooled | exactly nat/hyb; no pooled key in any output | YES |
| arms | 12 per object | 12 | YES |
| member cells | 99 (17×6 − 3 COVERAGE_EXCLUDED) | 99 | YES |
| parquet rows | 99·2·12 member + 3·2·12 excluded = 2448 | 2448 | YES |
| `is_defect` / `determinism_ok` / `causality_ok` | False / True / True | matches | YES |

---

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Median moving-block bootstrap CI | within-block exchangeability; non-parametric | YES | Inherited frozen estimator; `b=round(m^{1/3})`, 10,000 resamples. |
| `arm − RM` independent contrast | signal/null bootstrap distributions independent (disjoint pools) | YES | Pool excludes the object's own conditioned entries; null drawn on a dedicated RNG stream; underpowered null → NaN bound → `beats_rm=False`. |
| `arm − BENCH` paired contrast | same events, different exit machinery | YES | Computed on `arm.qual & bench.qual`, `n_common ≥ 30` gated. |
| Determinism (P3/P12) | identical output per `(seed, cell, purpose)`, any worker count | YES | `determinism_replay` recomputes the first usable cell per instrument and asserts byte-identical r_e/median/CIs/contrasts; 17/17 pass; RNG seeded order-independently. |

**RNG purpose disjointness (verified arithmetically).** BENCH reuses EXP-061 purposes
(native ≤ 64000, hybrid ≤ 85000). Non-BENCH arms use `OBJ_BLOCK[obj] + idx·10 + off`,
`off∈0..7`, `idx∈1..11` → native 100010–100117, hybrid 200010–200117. No overlap with the
EXP-061 stream space (≤87000), no overlap between objects, and the `idx·10` stride with 8
used offsets leaves a gap between arms. The BENCH↔EXP-061 byte-identity (proven by the 0.0
reconciliation) is the empirical confirmation that the BENCH streams were not perturbed.

---

## Results Plausibility

Outputs are internally consistent and domain-plausible: native expresses the edge while
hybrid does not — the **predicted EXP-061 divergence**, here surfaced through the exit
axis, with the winning arm being the EXP-060B champion favourable side (PARTIAL-V2A). This
is the expected shape, not an anomaly. The dual-object structure is preserved end-to-end
(every row carries an `object` tag; no pooled aggregate is emitted).

---

## Scope Compliance

- Analysis plan followed: **YES** (4 statistical methods, dual-object, per-object
  composition, P11+P6 non-4h, P12 reconciliation, P4 mean/trim/tail diagnostic).
- Deviations: none.
- Complexity budget: 4/4 stat methods, 5/5 plots, 0/≤1 new `xen/` modules (pure
  orchestration fork of EXP-064; no new analysis module).
- Holdout exclusion verified: **YES** (TRAIN-only F01 prefix; TEST/holdout never read;
  forward scans clipped to `train_end_ts` with `DATA_CENSORED` tagging).
- Real-price discipline: **YES** (HA used only for harami detection; all levels/legs/stops/
  ATR/returns/exit-composition on `Real*` OHLC; MA(20,50) on real close; opposing-harami
  reversal arm uses HA only to *locate* the bar then exits at that bar's real close).
- Registry: 0 candidate slots, 0 TEST reads; characterisation feeding the single terminal
  G-015 (no closure/registration here) — consistent with `run_metadata.json`.

---

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Secondary-ZigZag warmup gate never exercised in this run.**
   - `warmup_excluded == 0` for every TRAIL-*/COMBINED-* cell across both objects. This is
     benign and expected: the secondary `atr_mult=0.5` ZigZag confirms its first pivot well
     before essentially all conditioned harami entries, so `secondary_history` is True for
     all qualifying events. The gate (`pop_arm = pop_base & sec_hist`) is correctly wired and
     correctly disclosed as 0 in `secondary_map.csv` / `per_cell_expectancy.parquet`; no
     events are silently dropped. No action required — noted only so a future re-run with a
     sparser trailing structure is not mistaken for a regression.

2. **`population` column for TRAIL-*/COMBINED-* arms reports the pre-warmup base.**
   - For non-BENCH arms the reported `population` field is `pop = buildable ∧ cond_mask ∧
     (fav_dist>0)`, whereas TRAIL/COMBINED arms actually resolve on `pop_base ∧ sec_hist`.
     Because `fav_dist = 0.5·m_sofar` and `buildable` already requires `m_sofar>0`, the
     `fav_dist>0` term is redundant, so `population == pop_base`; the only gap vs the arm's
     true resolution base is the secondary-warmup count, which is **0 everywhere in this
     run** (Info 1), so the reported value is exact here. The arm's actual qualifying count
     (`m`), censored count, and `warmup_excluded` are all reported separately, so no
     information is lost. Purely diagnostic — not used in any viability/composition flag.
     Worth tightening only if a future run has nonzero warmup and the `population` column is
     consumed downstream.

## Re-Audit Requirements

None — PASS. Both Info notes are observations, not conditions.
