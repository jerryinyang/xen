# EXP-030 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-09
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Phase alignment:** `2026-06-09-007-avwap-tradability-and-isolation` (design.md §5 EXP-030,
the cost-bearing tradability gate). No misalignment with checkpoint objectives.

---

## VERDICT: APPROVE

All governance constraints pass. The single Stage-4 precondition stated in the scope —
explicit operator confirmation of the predeclared cost table — was obtained on
2026-06-09 ("Confirm as predeclared"). The cost table is now **frozen** for this run:
one-way `c_i` = EURUSD 0.75 / USTEC 1.25 / XAUUSD 1.50 / BTCUSD 4.00 bps; BASE round-trip
= 2·c_i; CONSERVATIVE round-trip (binding) = 4·c_i.

---

## Constraint checks

### Scope (scope.md)
- **Single falsifiable hypothesis** ✓ — net per-event expectancy > 0 under CONSERVATIVE
  costs on ≥1 domain, first-70% analysis set.
- **Boundaries explicit** ✓ — domains 5m/1h/4h, instruments, cost table, α₀, seeds,
  exclusions all stated.
- **Concrete FOR / AGAINST / INCONCLUSIVE criteria** ✓ — bind on CONSERVATIVE; AGAINST
  power from in-experiment CI half-width + counts, not the EXP-027 MDE (avoids the
  unattainable-criteria / undefined-denominator REVISE triggers).
- **Holdout exclusion** ✓ — explicit; analysis-set only; EXP-032 release deferred out of
  phase.
- **Real-price discipline** ✓ — all returns are direction-signed log returns on real
  domain Close (inherited from EXP-022/028/029).
- **Zero-baseline rule** ✓ — bps effects with CIs; no percentage-vs-zero metric.
- **Complexity budget** ✓ — tests ≤3, plots ≤4, modules 1.
- **No-tuning fence** ✓ — single cost model, two predeclared variants, no post-result
  re-selection; a net-negative is a valid outcome.

### Analysis plan (analysis-plan.md)
- **Method justification** ✓ — every step has why/simpler-alternative/assumptions/output.
- **Binding-metric discipline** ✓ — the plan correctly binds on the **absolute** net
  estimand (`mean(lifetime_bps) − RT_i`), explicitly distinguishing it from the EXP-028
  matched-control *excess* and demoting excess-minus-cost to a non-binding companion.
  This resolves a latent ambiguity in the scope's "Suggested Direction" prose and is a
  strengthening clarification, consistent with the scope's explicit Estimand section.
- **Inference soundness** ✓ — regime-cluster bootstrap CI (frozen) + one-sided bootstrap
  p (replacing the sign-permutation leg, which is invalid for an absolute,
  non-paired-symmetric estimand) + Holm; `CI_low > 0` preserved (scope-authorized
  refinement of p-value mechanics).
- **Cross-view alignment** ✓ — N/A by construction (pure overlay; no frame rebuild);
  temporal/real-price discipline inherited from EXP-022.
- **Interpretation guide pre-defined** ✓; **budget compliance** ✓ (1/3, 4/4, 1/1).

### Code (code/run_experiment.py)
- **Plan compliance** ✓ — all 7 steps; binding = `net_cons` absolute; BASE/gross/
  attribution as diagnostics; 4 scoped plots.
- **Holdout / look-ahead** ✓ — no Parquet or holdout access; inherited fence (inputs are
  EXP-022 first-70% rows); cost overlay uses only frozen constants.
- **Integrity guards** ✓ — frozen-tail `inspect.getsource` hash guard over the 5 named
  EXP-027 functions; reconciliation guard (recomputed gross excess must reproduce EXP-028
  to ≤0.01 bps); commute check (`net == gross − mean_inst(RT)` elementwise in the
  bootstrap). These substitute soundly for EXP-028's frame-alignment assertion.
- **Type safety / docstrings / sectioning / separation of concerns** ✓.
- **NaN & edge cases** ✓ — `<3` reportable instruments → UNDER_POWERED; empty cells
  skipped; plot values None-guarded / nan-filled.
- **Determinism** ✓ — `seed_for` seeding; one-domain replay assertion recorded.
- **Import side effects** ✓ — no dir creation / file write / data load at import;
  `ensure_output_dirs` only in orchestration; loading the pure EXP-027 function module is
  a dependency import (matches EXP-028).
- **No magic numbers** ✓ — cost table and thresholds are documented named constants.

## Info-level note (non-blocking)
- No `tqdm`: the per-domain / per-variant / per-instrument loops are ≤12 fast iterations
  with a vectorized internal bootstrap (seconds total) and section-level `LOGGER.info`
  progress. `tqdm` would add noise without value here (contrast EXP-028's 100-draw placebo
  loop, where it was warranted). Acceptable.

## No REVISE / REJECT triggers
No holdout contamination, no look-ahead, no synthetic-price P&L, no bar-index alignment,
no unsafe optimization (the commute check actively proves overlay correctness), no scope
creep. Criteria are attainable and denominators defined.
