# Governance Review: Experiment EXP-083 — Pre-Execution

**Date**: 2026-06-22
**Review Type**: Pre-Execution (consolidated Stage-4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/capgeo_screen.py`, `D0-amendment-001-split-exp083-train-screen.md`,
multiplicity-registry Phase 018 slate, Phase 018 `design.md` / `D0-predeclarations.md`.

## Executive Summary

EXP-083 is the **TRAIN-only candidate screen** (HYP-004a, per D0-amendment-001): it applies the 3 frozen
derived exits + the enumerated benchmark grid to the 4 frozen substrates on the TRAIN region, runs the
G-018a gross screen + the binding separability gate (S1 ∧ S2), and freezes/hash-pins the surviving
valid-candidate set for the deferred counted-read confirmation (EXP-084). **No TEST stratum, no holdout,
0 counted reads, frozen referee suite not invoked.** The artifacts are causally sound, holdout-clean,
per-stratum, shape-aware, and within budget. **VERDICT: APPROVE**, with disclosed screen-stage
deviations ratified here and routed to the Stage-5 auditor for a materiality confirmation.

## Constraint Checks

### Scope-Compliance Check (phase + registry alignment)

| Item | Verdict | Notes |
|------|---------|-------|
| Phase alignment | PASS | HYP-004a is the Phase 018 screen step; D0-amendment-001 (operator-directed 2026-06-22) split EXP-083 into the TRAIN screen + reserved-conditional EXP-084, recorded in the checkpoint and the multiplicity registry before measurement. |
| Registry precondition | PASS | `CF-CAPGEO-001` REGISTERED/OPEN; the 3 `/EXIT-DERIVED` candidates + `/EXIT-RR /EXIT-TRAIL /EXIT-VP /EXIT-PARTIAL /SIZE-VOLADJ` branches registered at D0; no new countable item; EXP-ID split consumes no slot. |
| TEST-read precondition | PASS | TRAIN-only; all 48 strata stay 0/2 open; ledger unchanged (disclosure, EXP-074/075/080/081 precedent). Scope states the tally. |
| Single question | PASS | One screening question (which `{candidate × stratum}` survive both TRAIN gates); multi-candidate surface is the screen, not compound hypotheses (EXP-046/060 precedent). |

### Holdout / Look-Ahead / Real-Price Check

| Check | Verdict | Evidence |
|------|---------|----------|
| Holdout untouched | PASS | `load_first70` loads only the first-70% analysis slice; the screen slices `[0, int(analysis_rows*0.7))` (TRAIN); the analysis-TEST stratum and final-30% holdout are never sliced. `holdout_untouched=True`, `test_stratum_touched=False` asserted in metadata. |
| Look-ahead / causality | PASS | Exit resolvers (`capgeo_screen`) read only `entry+1..cap`, fenced to `n_bars-1`, adverse-first (P15) tie-break; censored (TRAIN-edge-truncated) events excluded with record (never marked at the edge); derived barriers from the pinned causal `derive_barriers`; substrate detection is the frozen streaming-safe `capgeo_substrates`. Unit-validated (FAV/ADV/TIMECAP/CENSORED edge cases). |
| Real-price discipline | PASS | All returns/tail metrics on real domain OHLC in ATR units; no HA/Renko brick price enters any P&L/return. |
| Timestamp alignment | PASS | Entries aligned by `entry_epoch`/index into the cell's own bars; no cross-view bar-index alignment. |

### Principles / Method Check

| Check | Verdict | Notes |
|------|---------|-------|
| Non-parametric / no academic-finance pitfalls | PASS | Moving-block bootstrap (mean/median, two-sample diff, m_cell synthetic null), matched-control contrasts, tail-mass shape legs — no normality/stationarity/i.i.d./constant-vol assumption. |
| Per-stratum verdict | PASS | Binding outcome is per `{substrate × cell × candidate}`; the valid-candidate set is per-stratum; the experiment verdict (`SCREEN_DELIVERED`/`ALL_CANDIDATES_FAIL`) is a count over per-stratum valid flags, **not** a collapsed cross-stratum PASS. No pooled statistic is binding (LESSON-001 honored; EXP-076 C1 precedent respected). |
| Shape-aware + robust/raw endpoints | PASS | S2 (tailmass + relative-q05) is the predeclared shape-aware read alongside the G-018a location guard; both median and mean (expectancy) emitted — the robust-vs-raw gap is available (the CF-HA-HARAMI-001 split cannot recur undetected). |
| Gate-threshold calibration | PASS | The **binding** gate constants (`K_tail=3.0, τ_tail=0.06, δ=0.40, n≥120, m_cell=Q95(null CI_low), EVENT_FLOOR=30`) are all frozen at the D9 bite-check (calibrated, not magic). Benchmark-surface params (RR∈{1,1.5,2,3}, ATR-k∈{1,2,3}, leg 0.5, VP bin 0.25·ATR) are **conventional/data-anchored candidate-definition** constants (not binding gates), documented in constants. |

### Code Conventions Check (developer)

| Check | Verdict | Notes |
|------|---------|-------|
| Organization / sectioning | PASS | Imports → path setup → constants → types → pure helpers → candidate surface → gate evaluation → orchestration → plotting → `main()`; VAL-001-style separators; ruff-clean. |
| Import side effects | PASS | No dir creation / I/O / load / plot at import; `RESULTS_DIR`/`PLOTS_DIR` created in `main()`. |
| Lazy load + holdout slice | PASS | Reuses VAL-005 `load_first70` (lazy first-70%); TRAIN slice before any heavy work; EXP-081 summary is a small parquet. |
| tqdm / logging | PASS | `tqdm` over the member-cell outer loop; concise `logging`; helpers return data. |
| NaN / edge / zero-baseline | PASS | Explicit finite masks; underpowered (`n<30`) → recorded, no candidate; tailmass a fraction over `n_resolved` (never `0/0`); all effects are **differences** (no ratio-vs-zero). |
| Determinism | PASS | All seeds fixed/recorded; second-pass replay fingerprint compared (`determinism_ok`). |
| Reuse-first / module count | PASS | 1 new `src` module (`capgeo_screen`); imports pinned `derive_barriers` (sha256 asserted == EXP-082 `34d03f45…`) + frozen substrates/geometry/loader unchanged. |
| Complexity budget | PASS | 4 stat-method families / 5 plots / 1 new module — within the scope's ≤4 / ≤5 / ≤2. |

## Findings

### Critical

None.

### Warning

None that block execution. (The items below are disclosed design choices appropriate to a TRAIN screen;
they do not touch holdout, causality, denominators, or any binding gate constant, so they are Info — but
each is explicitly routed to the Stage-5 auditor for a materiality confirmation.)

### Info (ratified screen-stage deviations — auditor to confirm non-materiality)

1. **GROSS screen** (operator decision 2026-06-22): expectancy/median/tail are gross matched-control;
   cost-calibrated floors (frozen referee suite) + a dedicated cost layer are the EXP-084 / conditional
   follow-up concern. Matches the Phase-016 EXP-071 precedent. Recorded in `deviations`.
2. **Benchmark-arm fidelity (screen-stage proxies, disclosed):** `/EXIT-VP` uses a **cell-level**
   TickVolume POC target (not a per-event reference-move profile; VA arm folded to POC for this screen);
   `/EXIT-TRAIL` structure arm uses a rolling swing-window trail as a ZigZag-pivot proxy. Faithful
   reproductions are a post-screen / EXP-084-parity concern. **Auditor:** confirm these arms' resolutions
   are causal and cannot inflate any survivor (they are additional benchmark coverage, not the family
   hypothesis).
3. **`/SIZE-VOLADJ` non-distinct in the ATR-normalized frame:** returns are already vol-normalized (ATR
   units), so vol-adjusted sizing coincides with the default basis; recorded as a disclosure rather than a
   degenerate duplicate gate candidate. **Auditor:** confirm this is a correct observation, not a dropped
   test that could have changed the survivor set.
4. **`m_cell` calibration budget:** computed once per substrate-cell (mean kind, from the canonical
   mfe_med no-stop control reference) at `NULL_REPS=200 × N_BOOT_NULL=1000` and reused across that cell's
   candidates; the binding edge-call CIs use `N_BOOT=10_000` (default; `EXP083_N_BOOT` override recorded).
   **Auditor (materiality):** confirm the per-cell canonical `m_cell` does not mis-calibrate S1 for the
   larger-target arms (e.g. RR-3) in a way that could flip a `valid` flag; if it could, that is
   verdict-material and routes back to the developer.
5. **Determinism replay** re-runs the full screen (≈2× runtime); the manual run is expected to take tens
   of minutes — `EXP083_MAX_CELLS=3 EXP083_N_BOOT=2000` is the recommended smoke subset before the full
   run.

## Verdict

```
VERDICT: APPROVE
```

The scope, plan, and code implement a causally-sound, holdout-clean, per-stratum, shape-aware TRAIN-only
screen within budget; the slate split is properly amended and registered before measurement; 0 counted
reads are spent. The disclosed screen-stage deviations are ratified and routed to the Stage-5 auditor for
a materiality confirmation (item 4 — `m_cell` reuse on S1 — is the one most worth an explicit per-stratum
re-derivation in the audit's verdict forensics).
