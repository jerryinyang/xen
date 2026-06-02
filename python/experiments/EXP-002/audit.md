# Audit Report: Experiment EXP-002

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-002 checks that the two frozen referees reproduce predeclared golden-fixture
verdicts and expose all five gate legs without short-circuiting. I re-ran all
five fixtures against the current `referee_calibration` module: every
minimal-baseline verdict, gate-stack verdict, effect size, and per-leg state
reproduces the committed CSVs bit-for-bit, and the recorded `overall_status =
PASS` is correct. The dependency gate (EXP-001 must PASS) is enforced and no raw
data / holdout is touched.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Fixture construction, dual-referee evaluation, and leg parsing match the plan; reproduced exactly. |
| `code/run_experiment.py` | Edge cases | PASS | Dependency gate fails fast on missing/non-PASS EXP-001; fixtures fixed length 600/1200. |
| `code/run_experiment.py` | Type safety | PASS | `Fixture` dataclass; public helpers typed. |
| `code/run_experiment.py` | NaN handling | PASS | Fixtures finite by construction; referee CIs via `finite_values`. |
| `code/run_experiment.py` | Holdout exclusion | PASS | No Parquet read; only `EXP-001/results/run_metadata.json` consulted. |
| `code/run_experiment.py` | Memory/performance | PASS | 5 fixtures × 1000 resamples; small frames to pandas for the one figure. |
| `code/run_experiment.py` | Safe optimization | PASS | No optimization shortcuts; deterministic seeds throughout. |
| `code/run_experiment.py` | Progress tracking | PASS | Trivial loop (5 fixtures); `tqdm` not required. |
| `code/run_experiment.py` | Logging/output | PASS | Concise `logging`; results written to CSV/JSON. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Dirs created in `ensure_output_dirs()` from `main()`; no import-time effects. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions documented. |
| `src/xen/referee_calibration.py` | No short-circuit | PASS | `gate_stack_core` evaluates L1–L5 unconditionally; every fixture records all 5 legs. |

## Numerical Validation

### Spot Checks

Reproduced all five fixtures with the current module (`minimal_baseline_verdict`,
`gate_stack_verdict`, seeds `seed_for("EXP-002", name, …)`):

| Fixture | Min exp/act | Gate exp/act | Gate effect | Isolated leg(s) | Reproduces CSV? |
|---------|-------------|--------------|-------------|-----------------|-----------------|
| positive_oracle | PASS/PASS | PASS/PASS | +6.0 | all 5 True (happy path) | YES |
| null_negative_edge | REJECT/REJECT | REJECT/REJECT | −3.0 | L3=F, L5=F (also L4=F) | YES |
| readiness_one_sided | PASS/PASS | REJECT/REJECT | +7.0 | L1=F only (min PASS, gate REJECT) | YES |
| materiality_too_small | PASS/PASS | REJECT/REJECT | +0.2 | L5=F only | YES |
| naive_equivalent | PASS/PASS | REJECT/REJECT | +1.667 | L3=F (candidate == its naive control) | YES |

Hand-reasoning confirmed for the discriminating cases:
- **L1 isolation** (`readiness_one_sided`): positions all `+1` ⇒ 0 down-episodes
  `< min_state_count`(30) ⇒ L1 False; minimal has no readiness gate ⇒ PASS. The
  same data yielding minimal-PASS / gate-REJECT proves L1 is what the gate adds.
- **L5 isolation** (`materiality_too_small`): net +0.2 bps `< materiality`(0.5) ⇒
  L5 False; gross +1.2 bps `> 0` ⇒ minimal PASS.
- **L3 isolation** (`naive_equivalent`): candidate equals `sign(prev return)`, so
  `ci_vs_naive_lower = 0.0` ⇒ L3 False even though gross beats neutral.
- **No short-circuit**: fixtures with an early failing leg still record the later
  legs (e.g. `readiness_one_sided` records L3/L4/L5 despite L1=False) — required
  for EXP-003 per-leg pass rates.

### Range / Sanity Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Fixture verdict checks | 10/10 PASS | 10/10 PASS | YES |
| Leg exposure checks | 25/25 PASS | 25/25 PASS | YES |
| Gate effect = minimal effect − cost(1.0) | exact | 7→6, −2→−3, 8→7, 1.2→0.2, 2.667→1.667 | YES |
| `overall_status` | PASS | PASS | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Golden fixtures | margins large enough that bootstrap noise doesn't decide verdicts | YES | Constant/near-constant fixtures give zero-width CIs; only `naive_equivalent` has spread, still unambiguous. |
| Dependency order | EXP-001 PASS is a sufficient pre-calibration signal | YES | `require_exp001_pass()` enforces it before any fixture runs. |

## Results Plausibility

All outputs land exactly where the hand-reasoned design predicts; the gate adds
exactly the legs the minimal baseline lacks (readiness, naive control,
materiality). The five fixtures jointly exercise every leg's pass and fail path.

## Scope Compliance

- Analysis plan followed: YES (dependency gate → verdict check → leg-exposure check).
- Deviations: none.
- Complexity budget: 1/1 test, 2 visualisations in 1 figure file (≤2), 0/0 new modules.
- Holdout exclusion verified: YES (no raw data loaded).

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Degenerate block-length on a near-constant fixture.** For
   `materiality_too_small`, the minimal-baseline gross series is constant up to
   floating-point dust (`std ≈ 2.2e-16`), so `estimate_block_length` never sees
   the ACF drop below `1/e` and caps at the limit (200), giving the misleading
   `effective_n = 0.9` in `golden_fixture_results.csv`. This is deterministic
   (reproduces exactly) and affects **no** verdict or leg — the minimal referee
   has no effective-N gate and the CI is zero-width at +1.2 bps. It cannot arise
   on the non-constant real returns of EXP-003; flagged so the interpreter does
   not mistake it for a sample-size signal.

2. **`build_fixtures()` invoked twice.** `main()` calls it once for evaluation
   and again to list fixture names in `run_metadata.json` (`run_experiment.py:331,
   349`). Fixtures are cheap and deterministic, so this is harmless; noted only
   for tidiness.

## Re-Audit Requirements

None. Verdict is PASS; no fixes required.
