# EXP-005 — Pre-Execution Governance Review

**Experiment:** EXP-005 — Near-MDE Realistic-Candidate Detection Anchor (Phase 002 keystone closure)
**Stage:** 4 (pre-execution)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/candidate.py`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

---

## Operator predeclaration confirmation (design §2 ⚠ gate)

The Phase 002 design requires recorded operator confirmation (or a pre-results
amendment) of the three freeze items **before any EXP-005 measurement exists**.
The operator confirmed all three as the design `§2` defaults on 2026-06-03,
before any Phase 002 result was produced:

- **D-nearMDE** (EXP-005 realistic candidate): `p_active = 0.80`, `q_match = 0.75`,
  edge grid `{0.5, 1.0, 1.5, 2.0} × domain gate MDE`, drift planted on the latent
  state via the closed-form `delta_bps = (target + p_active·cost)/(p_active·(2·q_match−1))`,
  active-bar TPR/FPR denominators, frozen per-instrument costs. Confirmed.
- **D-lenientL5** (EXP-007): L5 passes when the net-of-cost effect CI lower bound
  exceeds 0, with mandatory economically-sub-material pass-rate reporting against
  the EXP-006 frontier. Confirmed (frozen for the phase; not exercised by EXP-005).
- **D-loss** (EXP-011): per-domain cost-weighted penalty on false positives and
  missed material edges, predeclared in full in the EXP-011 scope before any
  operating point is read. Confirmed (frozen for the phase; not exercised by EXP-005).

This confirmation freezes all three for the phase. Any later change requires a
new dated amendment authored **before** the dependent experiment's results are
read, referencing only predeclared reasoning (never EXP-005/EXP-006 outcomes).

**PHASE002-PREDECLARATION-CONFIRMED** — operator confirmation recorded; EXP-005
may execute. (`run_experiment.py` checks for this token before producing any
measurement.)

---

## Pre-execution corrections applied before this review

The scope and analysis-plan were reviewed for compliance/correctness and five
pre-results clarifications were applied (none alter the predeclared construction
parameters, hypothesis, criteria, or methodology):

1. **Dependency-gate correctness (bug-preventer):** EXP-003 records
   `overall_status == "COMPLETE"` (a measurement run), not `"PASS"`. The gate now
   requires EXP-001 `== "PASS"` and an artifact-based EXP-003 gate
   (`"COMPLETE"` + finite gate MDE), mirroring EXP-004. Gating on
   `EXP-003 == "PASS"` would have crashed the run.
2. **MDE read from artifact**, not hardcoded: the `{0.5,1,1.5,2}×` grid is built
   from EXP-003 `mde_summary.csv` (gate_stack, α=0.05); `1/4/12 bps` are the
   asserted-finite predeclared expected values; a missing/non-finite domain MDE
   is reported inconclusive.
3. **Units clarity:** drift injected in fractional units (`delta_bps/10_000`).
4. **Per-instrument cost** in the `delta` formula (`cost_bps_for(instrument,domain)`).
5. **Frozen-harness reuse:** the candidate construction lives in the
   experiment-local `code/candidate.py`; `xen.referee_calibration` is reused
   unchanged (D-reuse), so no P0/temporal-integrity re-validation is triggered.

---

## Artifact review against governance constraints

### Scope (`scope.md`)

| Check | Result |
| --- | --- |
| Single falsifiable hypothesis | PASS — H-blindness: gate detects a realistic near-MDE candidate (TPR ≥ 0.80 at FPR ≤ α₀) per domain; either outcome resolves the Phase 001 open item. |
| Concrete success/failure/inconclusive criteria | PASS — Evidence-FOR/AGAINST/Inconclusive defined with Wilson precision targets and the 1.0× headline. |
| Boundaries (views, instruments, params, exclusions) | PASS — 5m/1h/4h domains, 4 instruments, α grid, edge grid, draw counts, exclusions all explicit. |
| Complexity budget | PASS — 4 tests / 5 plots / 1 experiment-local module; within the checkpoint's comparative budget. |
| Holdout exclusion | PASS — first-70% only; final 30% explicitly never loaded. |
| Real-price outcome rule | PASS — real domain `Close` returns plus the known-truth planted drift (a substrate, not a synthetic chart price); no HA/Renko/Line Break prices. |

### Analysis plan (`analysis-plan.md`)

| Check | Result |
| --- | --- |
| Method justification (why / simpler alternative) | PASS — each step documents method, rationale, simpler-alternative, assumptions, expected output. |
| Assumptions valid for time-ordered data | PASS — non-parametric Wilson/block-bootstrap; block length on train only; no normality/stationarity assumption. |
| Cross-view alignment | PASS (N/A by timestamp) — only time-bar domains; shared 1m `CloseTime` split boundary; no bar-count alignment. |
| Visualisations purposeful | PASS — 5 plots each map to a sub-question (TPR curve, FPR, candidate diagnostics, pooled-vs-instrument masking, effect distribution). |
| Interpretation guide pre-defined | PASS — if-then detection-floor classification predeclared. |
| Budget compliance | PASS — 4/5/1. |

### Code (`code/run_experiment.py`, `code/candidate.py`)

| Check | Result |
| --- | --- |
| Plan compliance | PASS — implements exactly the 5 plan steps; no out-of-scope analyses. |
| Holdout exclusion | PASS — loads via frozen `load_analysis_data` (lazy scan → project → sort `CloseTime` → first-70% slice → collect); `analysis_metadata.csv` records `analysis_end`. No holdout path. |
| Look-ahead prevention | PASS — candidate state at `t` uses no future data; scored on `t→t+1` real returns; block length on train only; generators causal/per-bar. |
| Real-price discipline | PASS — `next_log_returns_from_bars` Close-to-Close real returns + planted drift; cost via frozen `ROUND_TRIP_COST_BPS`. |
| Frozen-harness reuse | PASS — `xen.referee_calibration` imported unchanged; only `candidate.py` is new and experiment-local. |
| Determinism | PASS — all seeds via `seed_for(...)`; workers seed-deterministic; canonical sort makes CSV output worker-count-independent. |
| Type hints / docstrings | PASS — public functions typed and documented. |
| NaN / edge handling | PASS — finite guards on rates; missing-MDE domains skipped→inconclusive; empty-file guard; `RuntimeError` if no reportable domains. |
| Separation of concerns | PASS — pure helpers / summaries / plotting / orchestration / `main()` sectioned VAL-001 style. |
| Import side effects | PASS — no dir creation/IO/load at import (`ensure_output_dirs()` in `main()`). One `sys.path.insert` before the local helper import, documented and required for spawn workers. |
| Progress / logging | PASS — `tqdm` on load and the 36k-draw simulation; helpers quiet; concise INFO summary. |
| Plot memory | PASS — plots consume small summary rows or bounded filtered verdict rows (≤2000/domain); no millions-row pandas conversion; no second data/generation pass. |
| Zero-baseline metrics | PASS — FPR/TPR are absolute Wilson proportions; calibration uses absolute bps; no percentage-over-zero. |
| Safe optimization / vectorization | PASS — candidate construction vectorized and causally equivalent; the only heavy loop is the parallel simulation (the inference unit), bounded and tqdm-tracked. |
| Duplicate-source denominators | N/A — no chart-type events in scope (time-bar domains only). |

**Lightweight pre-execution checks performed (not the experiment run):** both
modules byte-compile; `ruff` clean; a synthetic in-memory verification (no data,
no holdout, no `main()`) confirmed active_rate≈0.8007, match_rate≈0.7498, and
the closed-form `delta` recovers the target net edge to ~0.01 bps across the
per-instrument cost range, with the null net ≈ −cost·p_active (gate will reject
nulls). The keystone correctness anchor is empirically validated.

---

## Info notes (non-blocking)

- 4h per-instrument cells may miss the D-prec Wilson precision target and will be
  reported as under-powered (`under_powered=true`) rather than forced to a
  verdict — this is the predeclared expected behaviour, not a defect.
- `realistic_candidate_draws.csv` is verdict-level (~216k rows, comparable to
  EXP-003's `draw_verdicts.csv`); per-bar simulated returns are not persisted.
- `overall_status` is `COMPLETE`/`INCONCLUSIVE` (a measurement run); per-domain
  DETECTED_FLOOR / STRUCTURALLY_BLIND / INCONCLUSIVE_* statuses live in
  `detection_summary.csv`. A structurally-blind domain is a valid finding, not a
  run failure.

---

## Conclusion

Scope, analysis-plan, and code satisfy all governance constraints with no
Critical or Warning issues. The operator predeclaration freeze is recorded.
**APPROVE** — proceed to the manual execution gate.
