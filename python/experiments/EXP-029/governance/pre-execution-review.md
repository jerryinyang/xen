# Governance Review: Experiment EXP-029 — Pre-Execution

**Date**: 2026-06-09
**Review Type**: Pre-Execution (consolidated pipeline governance, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`code/event_method.py` (frozen copy), and the in-scope C# corrections
(`StrategyHost/AvwapBounceModel.cs`, `SignalRecords.cs`,
`StrategyRunParquetWriter.cs`, `Xen.cs`) + `tools/ctrader-cli/run-exp029-backtests.sh`.

## Executive Summary

APPROVE. The experiment is correctly scoped to a single parity question, reuses the
frozen EXP-027 inference tail unchanged (sha256 `ea261b9ee0a8aca3`, verified), and
reconstructs the **same** PRIMARY symmetric own-exit matched-control excess EXP-028
reports — closing both prior divergences (D1 execution-path, D2 estimand/framing).
The holdout fence is re-asserted, all alignment is by `SourceCloseTime`, and returns
use cTrader `RealClose` only. The C# emission extension (per-bar regime + the
`avwap_events.parquet` detail table) is serialization of already-computed model
state — not a signal-logic change — and is required to satisfy the scope's own
control-reconstruction clause without a Python signal oracle; it is disclosed as a
documented INFO below for the operator's awareness at the manual gate.

## Constraint Checks

### Phase Alignment

| Item | Verdict | Notes |
|------|---------|-------|
| Checkpoint alignment | PASS | EXP-029 is the appended Phase 006 experiment (design.md §9/§10), gated on EXP-027 METHOD_VALID + EXP-028 results — both satisfied. |
| Closes the recorded omission | PASS | Implements the cTrader per-bar streaming path the EXP-028 omission record mandates. |

### Scope Compliance

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable parity question; boundaries (instruments, domains, fence, exclusions) explicit; CONSISTENT/INCONCLUSIVE/INCONSISTENT criteria concrete; real-price (cTrader `RealClose`) rule stated; holdout excluded. |
| analysis-plan.md | PASS | Each step justified with method/simpler-alternative/assumptions; estimand reconstruction explicit; parity disposition predeclared; Divergences-To-Avoid table maps each guard to a check. |
| code | PASS | Implements Steps 0–7 exactly; no bonus analyses; complexity budget respected. |

### Complexity Budget

| Axis | Budget | Actual | Verdict |
|------|--------|--------|---------|
| Statistical tests | 3 | 2 reused (bootstrap CI, sign-permutation+Holm) + parity comparison reusing them | PASS |
| Visualisations | 3 | 3 (effect forest, count/pyramid diagnostic, parity table) | PASS |
| New code modules | 1 | 1 (`run_experiment.py`) + frozen `event_method.py` copy + in-scope C# correction | PASS |

### Principles Check

| Check | Verdict | Notes |
|-------|---------|-------|
| Data-driven / non-parametric | PASS | Regime-cluster bootstrap + sign-permutation (frozen EXP-027 tail); no parametric distributional assumptions. |
| Real-price discipline | PASS | Direction-signed log returns on cTrader `RealClose`; no synthetic chart prices anywhere. |
| Holdout excluded | PASS | Harness reads only `data/strategy_runs/` (fenced runs), never `data/timebars`; per-instrument `AnalysisEndUtc` fence re-asserted (`load_cell_frame`), strict-monotonic `SourceCloseTime` checked; final 30% never loaded. |
| Look-ahead / timestamp alignment | PASS | Events aligned to frame by `SourceCloseTime` (`load_event_detail`); emitted `TriggerIdx` cross-checked; no bar-index transfer across feeds; `scan_lifetime` uses only completed bars. |
| Frozen method integrity (D3) | PASS | `verify_frozen_inference` sha256 == `ea261b9ee0a8aca3`; `verify_control_matching` passes; tail imported unchanged. |
| Estimand fidelity (D2) | PASS | PRIMARY excess rebuilt via imported EXP-022 own-exit machinery (`scan_lifetime`/`transfer_targets`/`select_controls`/`regime_*`) + EXP-028 `build_primary_excess` aggregation; raw-return-vs-excess comparison absent. |
| No signal oracle (D4) | PASS | Regime/anchor/targets/pyramid come from the cTrader emission; the harness never re-runs the AVWAP state machine (regime LUT is a pure groupby on emitted per-bar `RegimeId`). |
| Zero-baseline (D7) | PASS | Effects in bps; unpowered → `None`/NaN; count-deltas use `max(|ref|,1)` denominator; no percentage-over-zero metric. |
| Safe optimization | PASS | Reconciliation vectorized per cell; `scan_lifetime` kept sequential (imported unchanged); per-event loop bounded by sparse event count; no membership/ordering/denominator change. |

### Code Quality

| Check | Verdict | Notes |
|-------|---------|-------|
| Compiles / imports | PASS | `py_compile` + guarded import OK; C# `dotnet build` 0 warnings / 0 errors. |
| Organization / sectioning | PASS | VAL-001-style sections; imports→path→constants→helpers→steps→plotting→save→main. |
| Import side effects | PASS | Output dirs created only in `main`/`save_outputs`; no I/O at import. |
| Type hints / docstrings | PASS | Public functions typed with Parameters/Returns docstrings. |
| Progress / logging | PASS | `tqdm` on the 12-cell loop; concise INFO logging; helpers return data. |
| Determinism | PASS | `seed_for` convention for all bootstrap/permutation draws; cTrader generation deterministic. |

## Findings

### Critical
None.

### Warnings
None.

### Info

1. **C# emission extension (disclosed, scope-faithful).** The corrected C# emits two
   things beyond the scope's literally-enumerated minimal correction (pyramids +
   `is_pyramid_bounce`): per-bar `RegimeId`/`RegimeDirection` on `positions.parquet`
   and the `avwap_events.parquet` detail table. Both are **serialization of
   already-computed model state** (the `AvwapEventDetail` record and `_regimeId`/
   `_activeRegime` already exist; signal logic is untouched and the build is
   0-warning/0-error). They are *required* to satisfy the scope's own clause —
   "controls must be rebuilt here ... role=control rows per (instrument, domain,
   regime_id, event_trigger_idx) ... for each cTrader event" — without re-deriving
   the AVWAP signal in Python (which the architecture forbids). This is the
   resolution the approved analysis-plan §"C# Behavioral & Emission Contract"
   predeclared. Recorded for operator awareness; not a signal-logic change.

2. **Multi-position `positions.parquet` semantics.** With pyramids opened
   independently, the AVWAP `Position` field can exceed ±1 in magnitude and the
   trade blotter records one `enter_*`/`exit_*` per position. This is intended
   (pyramids are now tradable) and affects only the AVWAP runs; MA/Donchian
   emissions are unchanged (sentinel regime defaults). EXP-029's binding estimand
   does not use the `Position` magnitude (it uses `RealClose` + regime + event
   detail), so there is no consumer breakage.

3. **Fixed-horizon secondary-stability input.** EXP-028 drew the {1,3,6}-horizon
   stability inputs from EXP-021's local reaction observations; EXP-029 computes the
   same fixed-horizon paired excess from its **cTrader-feed** events and controls
   (`_fixed_horizon_rows`). This is the correct cTrader-feed analog (using local
   EXP-021 obs would be a feed mismatch) and feeds only the `decide_label`
   secondary-stability downgrade guard, never the binding primary effect.

4. **Exit-alignment diagnostic is coarse.** Per-position entry→exit pairing is
   ambiguous in the generic multi-position blotter, so `exit_alignment.csv` reports
   count agreement only (cTrader `exit_*` trades vs Python-scanned completions). It
   is explicitly non-binding and never enters a verdict.

## Verdict

```
VERDICT: APPROVE
```

---

## Post-review revision addendum (2026-06-09)

After the APPROVE above, a pre-execution **adversarial review** of EXP-029 found the
parity design — though scope-faithful — was *confirmation-biased*: the binding
disposition rested on a coarse "verdict + CI-overlap" read that could not be falsified
by a magnitude divergence, the binding estimand's Python exit re-scan left the
**corrected C# concurrent-completion code itself ungraded**, count drift was
pre-attributed to "benign feed coverage" with no signal-layer check, the pyramid
split was not in the count gate, and the frozen-hash equality was documented but not
enforced in code. Because EXP-029 had **not yet executed** (no `results/`, no cTrader
runs), the design was strengthened in place and all new criteria were **predeclared
before any result exists** (D8 preserved). Changes, all of which *tighten* the gates:

| Finding | Change | Artifacts |
|---------|--------|-----------|
| F01 (Critical) | Binding **exit-parity** grading of the C# completion per event vs the Python scan on the same feed; C# now serialises its executed exit (`Exit*`) onto the event-detail row | `AvwapBounceModel.cs`, `StrategyRunParquetWriter.cs`, `run_experiment.py` (`build_exit_parity`, Step 4b), scope/plan |
| F02 (Major) | **Magnitude-equivalence** gate with an INCONSISTENT divergence band; CI-overlap demoted to diagnostic | `run_experiment.py` (`compare_parity`), scope/plan |
| F03 (Major) | **5m signal-layer reconciliation** vs the EXP-020 substrate; blocks a CONSISTENT upgrade on a feed-exact divergence | `run_experiment.py` (`reconcile_signal_layer`, Step 3b), scope/plan |
| F04 (Major) | **Pyramid split** added to the ±10% count gate (loads EXP-028 `event_diagnostics.csv`) | `run_experiment.py`, scope/plan |
| F05 (Minor) | Frozen hash **hard-asserted** == EXP-028's `ea261b9ee0a8aca3` (was a non-gating boolean) | `run_experiment.py` (Step 0) |
| F06 (Minor) | Coarse count-only `exit_alignment` **replaced** by the binding per-event exit-parity (matched population) | `run_experiment.py` |
| F07 (Minor) | Secondary-stability {1,3,6} control-rule deviation **documented** as deliberate | scope.md |

**Budget impact:** none. The added exit-parity / signal-layer / magnitude checks are
deterministic comparison metrics under the existing parity-comparison test (no new
bootstrap/permutation/estimator); the new gates are surfaced as columns in the existing
parity table (no new plot); still 1 Python module + the in-scope C# correction. The C#
build remains 0-warning / 0-error and the harness imports + unit-smoke-tests pass.

**Disposition of original INFO #4** (exit-alignment is coarse / count-only): **resolved**
— superseded by the binding per-event exit-parity grading enabled by the C# executed-exit
serialisation.

**Verdict unchanged: APPROVE** (now on the strengthened, falsifiable design).
