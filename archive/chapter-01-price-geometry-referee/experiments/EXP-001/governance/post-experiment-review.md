# Post-Experiment Governance Review: EXP-001

**Stage**: 8 (post-experiment)
**Artifacts reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

---

## Constraint Checks

| Constraint | Result | Evidence |
|------------|--------|----------|
| Single hypothesis / strict scoping | PASS | One falsifiable substrate-validity hypothesis; budget 2/2 tests, 4 viz (3 files), 1/1 module — within limits. |
| OOS holdout untouched | PASS | `load_analysis_data` sorts by `CloseTime` then slices `[0, int(total_rows*0.7)]`; post-slice `analysis_rows` reproduce VAL-001 exactly. Holdout never collected. |
| Chronological split | PASS | Shared `CloseTime` analysis/train cut derived once on the 1m base, inherited by all domains. |
| Look-ahead prevention | PASS | Random states independent of returns; positions at `t` evaluated on `t→t+1` returns; permutation null does not leak order into the candidate. |
| Real-price discipline | PASS | Returns computed from real resampled `Close`; no chart-type/synthetic prices in scope. |
| Timestamp alignment | PASS | Domains aligned by `CloseTime`, never bar index. |
| Determinism | PASS | All draws seeded via `seed_for` (SHA-256) + `np.random.default_rng`; byte-stable. |
| No academic-finance pitfalls | PASS | Non-parametric percentile intervals over fixed-seed draws; no normality/stationarity assumption. |
| Safe optimization | PASS | `int32` block indices and `finite_values` fast path verified bit-identical by audit; no membership/denominator/temporal change. |
| Audit thoroughness & evidence | PASS | Correctness, holdout, look-ahead, NaN, ranges, and spot-checks all covered with line/value evidence; 0 Critical, 0 Warning, 4 Info. |
| Results honesty & verdict support | PASS | SUPPORTED verdict tied to predeclared §11/D-prec criteria; 4h under-power reported as immaterial, not smoothed; next steps are new scopes. |
| Report self-contained & linked | PASS | Question→method→findings→conclusion with 2 key plots; all artifacts linked. |
| Indexes updated | PASS | Brief `INDEX.md` row added; comprehensive `INDEX.md` five-field section added. |
| Phase alignment | PASS | Matches checkpoint §4 H-substrate (gating) and §10 EXP-001; substrate gate PASS unblocks EXP-002/003. |

## Findings

No Critical or Warning issues. The audit's four Info notes (sub-material 4h
under-power, recovery-precision vs detectability framing, negative
`dropped_window_fraction` reporting artifact, `min_effective_n` gate semantics)
are correctly characterized and do not affect trust in the result. They are
carried forward as interpretation context for EXP-003.

## Verdict

```text
VERDICT: APPROVE
```

EXP-001 is complete and the substrate gate is satisfied. Downstream experiments
(EXP-002 correctness, EXP-003 keystone) may rely on the validated substrate, with
the 4h domain's recorded under-power treated as a known operating characteristic.
