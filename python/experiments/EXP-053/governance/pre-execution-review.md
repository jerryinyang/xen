# Pre-Execution Governance Review — EXP-053

**Experiment:** EXP-053 — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion, Harami-Anchored)
**Family / item:** `CF-HA-HARAMI-001` / `HYP-006` (Phase 014-B lead 1)
**Stage:** 4 (pre-execution). Pipeline resumed at Stage 4 — `scope.md`, `analysis-plan.md`, and
`code/run_experiment.py` present; `governance/pre-execution-review.md` absent.
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, new module
`python/src/xen/expectancy.py` (reused EXP-054–060).
**Reference context read:** `_pipeline-config.md`, `dataset-reference.md`, `architecture.md`,
`governance-constraints.md`, `014-B-design.md`, `014-B-D0-addendum.md` (P14–P21),
`014-A-conditioning-gap-and-validation-lessons.md`, `G1-gate-review.md`, `candidate-families/harami.md`,
`multiplicity-registry.md` (Phase 014-B batch).

```text
VERDICT: APPROVE
```

## Signal-registry / multiplicity preconditions

- **Family REGISTERED:** `CF-HA-HARAMI-001` is `REGISTERED`. ✓
- **Item registered:** `CF-HA-HARAMI-001/HYP-006 — EXP-053` appears in `multiplicity-registry.md`
  Phase 014-B batch (PLANNED, 0 slots / 0 TEST). ✓ No new countable item is introduced beyond the
  registered conditioned-efficacy read (both filter arms, both geometries, and all secondaries are
  disclosed forms of registered branches `/STRONG-STAT`, `/STRONG-HA`; G1≡G2 collapse proven, one
  geometry computed).
- **TEST stratum:** none read — TRAIN-only (first 49% = 0.7×0.7 of the 1-minute base). No
  `test-read-ledger.md` tally applies; no entry required. ✓
- **Mandatory 014-B reading precondition:** `scope.md` records that
  `014-A-conditioning-gap-and-validation-lessons.md` was read and confirms (a) conditioning applied,
  (b) harami anchor, (c) position-in-move descriptive-only, (d) expectancy endpoint. ✓ (Hard Stage-1
  precondition satisfied — not REVISE.)

## Guardrail compliance (G1 review + 014-B design + D0 addendum)

| Guardrail | Disposition |
| --- | --- |
| Conditioned signal ON (`/STRONG-STAT` live magnitude-percentile, P16) | `live_strong_stat` binding p75; not the unconditioned object EXP-049/052 measured. ✓ |
| Entry **anchored at the harami** (lead over ZigZag giveback) | `entry_idx` at harami CloseTime; `entry_close` = harami real close; in-progress state from last *confirmed* move (`side="right"-1`). ✓ |
| Position-in-move **never a live filter** | EXP-050's metric is absent from the pipeline; only the live percentile detector conditions. ✓ |
| Binding endpoint = **median** expectancy (P14); `r` disclosed | `signal_stat` median bootstrap binds; `r_firsthit`, mean, win-rate, timecap-frac disclosed. ✓ |
| **P15 path-ordered fills** replace worst-case tie-break (P15) | `_scan_path`: bullish `O→L→H→C`, bearish `O→H→L→C`; documented intrabar approximation, disclosed in metadata; EXP-054 bounds its effect. ✓ |
| Single G2, no early closure inside 014-B | Emits a characterization readout (EVIDENCE_*), adjudicates no gate; readout feeds G2. ✓ |

## Core-constraint checks

- **Holdout / look-ahead:** loader takes Parquet metadata (`pl.len()`) then a lazy
  `scan→select→slice(0, train_rows)→collect`; full file never sorted/collected; `is_sorted()`
  asserted (file order == chronological per the integrity rule); every domain bar fenced to
  `CloseTime ≤ train_end_ts`; forward first-touch scans clipped to the data edge → DATA_CENSORED.
  TEST and the final-30% holdout are never materialized. ✓
- **Causality:** in-progress state is a causal as-of map (`searchsorted`, side="right"−1, with an
  explicit assertion guard); `/STRONG-STAT` window uses only moves with `ConfirmTime ≤ t_i`; the
  time cap uses only moves confirmed *strictly before* `t_i` (`side="left"−1`); barriers use only
  `C` and the known start pivot; the path scan starts at `entry_idx+1`. No leg references a future
  bar. ✓
- **Vectorization discipline:** the path-dependent objects under test — the P15 first-touch
  resolver (`resolve_path_ordered`/`_scan_path`), the `/STRONG-STAT` windowed retention, and the
  `/STRONG-HA` run scan — are explicit bounded loops. The in-progress-state as-of map and bootstrap
  index construction are vectorized; both are causally equivalent and preserve sample membership,
  ordering, and denominators. (Audit note below.) ✓
- **Real-price discipline:** HA prices enter only `generate_heiken_ashi` / `detect_ha_harami` /
  `annotate_ha_impulse`; `C`, `M_sofar`, barriers, fills, `ATR_entry`, returns, `r`, win-rate are all
  computed on real domain OHLC. ✓
- **Timestamp alignment:** harami→bar and move ConfirmTime/EndTime→bar mapped by exact epoch match
  with equality asserts; never by bar index. ✓
- **Zero-baseline / denominators:** qualifying population = built-barrier FAV/ADV/TIMECAP;
  `< 30` → `NOT_VIABLE_BY_POWER` (no ratio); `M_sofar=0`, NaN/≤0 ATR, warmup excluded with disclosed
  counts. ✓
- **Determinism:** per-cell-per-purpose RNG `default_rng([BASE_SEED, cell_index, purpose])`;
  determinism replay (byte-identical) + reconciliation anchor (independent FAV/ADV + r_e check) run
  once as SUBSTRATE/METHOD_DEFECT guards. ✓
- **Complexity budget:** 4 stat tests (signal median bootstrap, matched-random, MA-seg, contrast CI),
  4 plots, 1 new module (`expectancy.py`). Within the comparative budget; matches scope. ✓
  Confirmed `capture_barriers.py` is reused unchanged (committed); only `expectancy.py` is new for
  EXP-053.
- **Code conventions:** imports → path setup → constants → I/O → pure computation → plotting →
  orchestration → `main()`; `mkdir` only in `run()` (no import side effects); helpers return data,
  `LOGGER`/`tqdm` only in orchestration; lazy Polars + column projection + bounded per-cell memory
  (`del train_1m`); bounded plot inputs (summaries + viable-cell pooled events); type hints and
  docstrings throughout. ✓ (Local `xen.*` imports placed after path constants with `noqa: E402` — a
  minor ordering nit, not a side effect; Info only.)

## Notes routed to the audit (Stage 5) — not blockers

1. Numerically confirm `bootstrap_median_distribution` block construction is identical to
   `xen.capture_barriers.block_bootstrap_ci` (only the statistic — `np.median` — should differ).
2. Confirm the vectorized in-progress-state as-of map reproduces a sequential per-entry walk
   (the determinism replay + causality assertion already guard this; a spot reconciliation suffices).
3. Verify the G1≡G2 collapse holds in code (single geometry is intentional and proven in the plan).

## Routing

No `FAILING_ARTIFACT`. Scope, analysis plan, and implementation are mutually consistent, registry-
and guardrail-compliant, holdout- and look-ahead-safe, and within budget. Proceed to the manual
execution gate.
