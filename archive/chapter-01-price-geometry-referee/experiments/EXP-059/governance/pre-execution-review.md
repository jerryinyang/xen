# EXP-059 — Pre-Execution Governance Review

**Experiment:** EXP-059 — Position-Management Exits (Conditioned HA Harami;
`/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-012` — EXP-059 (PLANNED, Phase 014-B batch)
**Stage:** 4 (consolidated pre-execution governance)
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/position_exits.py` (new module)
**Reference framework:** `research-pipeline/references/governance-constraints.md`;
`_pipeline-config.md`; `014-B-design.md` + `014-B-D0-addendum.md` (P14–P21);
`014-A-conditioning-gap-and-validation-lessons.md`.

---

## 1. Mandatory-reading precondition (014-B, hard Stage-1 gate)

`014-A-conditioning-gap-and-validation-lessons.md` was read in full before scoping
(confirmed; ingested this session). `scope.md` records the four binding rules and
how each is honoured. Verified against the code:

| Rule | Requirement | Verdict |
| --- | --- | --- |
| (a) conditioning | Object = live `/STRONG-STAT`-conditioned HA harami (not raw harami / unconditioned ZigZag). | **PASS** — `compute_cell` builds `conditioned = buildable & stat["retained_p75"]`; `/STRONG-HA` + STAT-MAD disclosed only. |
| (b) harami-anchor | Entry = harami confirmation-bar real close `C`, not the ZigZag confirmation. | **PASS** — `entry_close = ohlc["close"][entry_idx]`, `entry_idx` from `harami_entry_indices`; ZigZag direction only supplies `rd`. |
| (c) position-in-move descriptive-only | EXP-050 position metric never a live filter. | **PASS** — not referenced anywhere; every exit is a forward-confirmed event. |
| (d) expectancy endpoint (P14) | Binding metric = median position-weighted gross expectancy, not first-hit `r`. | **PASS** — `weighted_returns` → `bootstrap_median_distribution`/`median_ci`; first-hit `r` reported for BENCH only, `None` for multi-leg arms. |

A 014-B scope omitting this confirmation is REVISE; it is present and faithful. **Cleared.**

## 2. Signal-registry precondition (programme file-drawer control)

- Family `CF-HA-HARAMI-001` is `REGISTERED` / OPEN (`candidate-families/harami.md`).
- `HYP-012` / EXP-059 is registered **PLANNED** in `multiplicity-registry.md`
  (line 387, Phase 014-B batch); the two exercised branches
  `CF-HA-HARAMI-001/EXIT-PARTIAL` and `/EXIT-TRAIL-STRUCT` are **REGISTERED**
  (lines 347–348, 2026-06-15) and listed in `candidate-families/harami.md`
  (lines 268–272). The 12 predeclared arms are all compositions of these two
  registered branches (no unregistered countable item is introduced).
- **No TEST stratum is read** (TRAIN-only; first 49% file-order prefix). The
  `test-read-ledger.md` requires **no entry** and none is created; the current
  counted-read tally is irrelevant because no TEST stratum is touched. 0 candidate
  slots, 0 TEST reads, per the 014-B D0 addendum slot/ledger accounting.

**Cleared.** No `REVISE`-triggering registry gap.

## 3. Core constraint checks

### 5/6 — OOS holdout & look-ahead (the binding correctness gates)

- **Holdout fence (PASS).** `load_train_1m` reads only Parquet metadata + the first
  `train_rows = int(int(total_rows*0.7)*0.7)` **file-order** rows via
  `scan.slice(0, train_rows).collect()`; the full file is never sorted or
  collected, and TEST / final-30% holdout rows are never sliced. Every domain bar
  is fenced `CloseTime <= train_end_ts` in `build_domain`. Identical fence to
  EXP-049/053–058 — this is what makes the conditioned population reconcile with
  EXP-053 (invariant ii, enforced in-code).
- **Forward-scan TRAIN clipping (PASS).** Every new forward construct is clipped to
  `last_train_idx`: `_scan_event` scans `[ei+1, min(ei+n_ev, last_train_idx)]` and
  emits `DATA_CENSORED` (never a fabricated exit) when the window is truncated by
  the edge; `build_active_stops` and `reversal_event_targets` only read confirmed
  events with index ≤ the current bar / within the cap. Invariant (v) ("every exit
  bar `CloseTime <= train_end_ts`") holds by construction.
- **Look-ahead / causality (PASS).** The two genuinely new path-dependent objects
  were audited specifically:
  - *Structure trailing stop* (`build_active_stops`): the active stop at bar `i`
    uses only secondary-ZigZag moves with `ConfirmIdx <= i`; on a matching-direction
    confirmation (pivot high for a long) it trails to `sec_end_price[ptr-1]`, the
    **prior** opposite pivot, whose `ConfirmIdx < ConfirmIdx[ptr] <= i` — a
    fully-confirmed past pivot. The ratchet is monotone (`max` long / `min` short),
    so the stop never loosens. Verified by the synthetic monotonicity test and the
    in-run invariant (iv).
  - *Reversal-event locator* (`reversal_event_targets`): the ZigZag arm reuses the
    causal `xen.third_barrier.third_event_caps` forward-locator
    (`searchsorted(..., side="right")` lower bound ⇒ strictly-after-entry confirm);
    the opposing-harami arm scans the conditioned stream strictly after the entry
    bar. A `Direction==-rd` ZigZag confirm is **not** a take-profit trigger (it is
    the adverse event, handled by the stop) — the directional-encoding correction
    in `scope.md` §Operator decisions is implemented exactly (`Direction == rd` for
    the take-profit completion).
- **Timestamp alignment (PASS).** Primary ZigZag, secondary ZigZag, HA candles, and
  real bars are aligned by exact `CloseTime` epoch (`_map_to_grid` raises on any
  mismatch); never by bar index across views.

### 7 — Real-price / synthetic-price discipline (PASS)

Every barrier, leg level, stop level, P15 fill, ATR normalisation, and outcome is
on real domain-bar OHLC (`RealOpen/High/Low/Close`). HA prices enter only the
harami detector (`harami_entry_indices`), the `/STRONG-HA` retention
(`strong_ha_retention`), and to *locate* the opposing-harami reversal bar — which
then exits at that bar's **real** close. No HA price enters any metric.

### 8 — Safe performance / memory (PASS)

Lazy `pl.scan_parquet` with column projection; per-cell `del cell` / `del train_1m`;
bounded bootstrap batching (`BOOT_BATCH` in `xen.expectancy`); `tqdm` over the
17-instrument outer loop. The two new resolvers (`resolve_legs`, `_scan_event`) are
explicit bounded **sequential** loops carrying a "do not vectorize" contract — their
causal/streaming semantics are the object under test (mirrors
`resolve_path_ordered`). Per-event cost is `O(bench_N * n_legs)` (~6 bars in 96/99
cells). The trailing-stop step array is `(n_harami, max(n_event)+1)`, transient and
freed per arm. No optimisation alters membership, ordering, denominators, or metric
definitions.

### 1/3/4 — Simplicity, scoping, framework principles (PASS)

- **Single question** (does position-management exit machinery raise conditioned
  gross median expectancy vs the benchmark fixed exit?), one falsifiable hypothesis,
  concrete EVIDENCE_FOR / AGAINST / INCONCLUSIVE / DEFECT criteria.
- **Complexity budget respected:** 4 statistical methods (median bootstrap; baseline
  bootstrap; paired arm−benchmark contrast; independent arm−baseline contrast) —
  the **same** method set as EXP-056/057/058 applied across the predeclared 12-arm
  sweep, not new methods per arm; 5 visualisations; **1** new module
  (`position_exits.py`). All other machinery reused.
- **Non-parametric by default:** regime-clustered moving-block bootstrap on the
  median (fat-tailed returns); no normality / stationarity / i.i.d. assumption is
  introduced beyond the disclosed block-bootstrap caveat.
- **No post-result selection:** all 12 arms are predeclared in `ARMS` and every arm
  is reported; routing is the single 014-B G2 after the full slate (no intermediate
  gate, no early closure) — consistent with P21.

### Zero-baseline / denominators (PASS)

A cell with `< 30` qualifying events for an arm is `NOT_VIABLE_BY_POWER`
(non-reportable), never an undefined or infinite ratio. `DATA_CENSORED` and trailing
warmup events are excluded-with-record and disclosed as counts. First-hit `r` is
finite-or-`None` (BENCH only). Exit-reason composition is a disclosed mechanism
diagnostic and never enters viability.

## 4. Code conventions (developer self-check, verified at Stage 4)

| Convention | Status |
| --- | --- |
| Organisation: imports → path setup → constants → I/O → pure computation → plotting → orchestration → `main()` | PASS (both files VAL-001-sectioned) |
| Output dirs created in orchestration only (no import side effects) | PASS (verified: import creates no `results/`/`plots/`) |
| Lazy scan → file-order TRAIN slice → collect; column projection | PASS |
| No silent `.unique()` / dedup; no full-data collect before holdout exclusion | PASS |
| `tqdm` on the long outer loop; helpers quiet and return data; `logging` in `main()` | PASS |
| Type hints + docstrings on public functions; functions bounded (~30 lines) | PASS |
| Real-price discipline; no HA price in any metric | PASS |
| Determinism: fixed `BASE_SEED`, two-pass replay guard | PASS |
| `ruff check` on both files | **All checks passed** (E741/F401/F841 fixed) |
| `py_compile` + proper module import | PASS (all names/imports resolve) |
| Synthetic correctness of the new module | PASS — single-leg == `resolve_path_ordered`; degenerate 3-leg == single-leg (≤1e-12); shared 1:1 stop closes all legs at `adv`; trailing stop monotone; P15 tie-break agrees with the reused resolver |

The four predeclared in-run invariants beyond determinism/reconciliation
(single-leg match, degenerate match, shared-stop, trailing-monotone) are asserted
per-cell in `_cell_invariants` and gate `is_defect`; the BENCH↔EXP-053 reconciliation
(invariant i/ii) is enforced against `EXP-053/results/outcome_primary.csv`.

## 5. Plan-compliance spot check

Code implements exactly the analysis plan: Step 1 loader; Steps 2–3 conditioned
population + benchmark geometry held at benchmark for every arm; Step 4 multi-leg P15
resolver; Step 5 causal monotone trailing stop; Step 6 reversal-event locator; Step 7
weighted realised return + qualifying mask; Steps 8–10 the four bootstrap methods;
Step 11 P11 + EVIDENCE_* fork; Step 12 disclosed secondaries (exit-reason composition,
`/STRONG-HA`, MAD, baselines, BENCH `r`); Step 13 determinism + six invariants. No
out-of-plan analyses or extra plots. The OAT discipline is honoured — only the
position-management exit machinery varies; favourable 50%, adverse 1:1 (where not
replaced by the trailing stop), and the third barrier (adaptive cap) are benchmark
for every arm. The benchmark-cap-bounds-the-runner-legs limitation is disclosed in
both `scope.md` and `run_metadata.json` (horizon × position-management is EXP-060).

## 6. Issues

None at Critical or Warning severity. Info notes (non-blocking):

- **(Info)** The trailing-stop step function is rebuilt per (arm, signal-arm,
  baseline) rather than cached per cell — a performance cost, not a correctness
  issue; per-cell work stays bounded by `bench_N`. No change required.
- **(Info)** Three-equal-leg weights are `1/3` floats summing to
  `0.9999999999999999`; the `weights_sum_ok` invariant tolerance (`1e-12`) and the
  per-event weighting absorb this; immaterial.

---

## VERDICT

```text
VERDICT: APPROVE
```

All governance constraints pass. The mandatory 014-A lessons read is recorded and
faithfully implemented (conditioning, harami-anchor, descriptive-position,
expectancy endpoint); the registry precondition holds (HYP-012 PLANNED, both
branches REGISTERED, 0 slots / 0 TEST reads, no ledger entry required); the holdout
fence, forward-scan TRAIN clipping, look-ahead/causality discipline (new trailing
stop + reversal locator audited specifically), real-price discipline, complexity
budget, zero-baseline handling, and code conventions are all satisfied; the new
module's correctness is corroborated by synthetic invariant tests and is guarded
in-run by the predeclared invariants + EXP-053 reconciliation. Proceed to the manual
execution gate.
```text
```
