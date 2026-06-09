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

---

# Revision 1 — Stage-4 re-review of post-run code modifications (2026-06-09)

## VERDICT: APPROVE (revision; mandatory re-run before Stage 5)

## Context

After the original APPROVE and the manual run, an adversarial review (F01–F07) found
that `code/run_experiment.py` carried uncommitted, result-aware modifications made
**after** the binding net results were read, that the on-disk `run_metadata.json` was
produced by the pre-modification code (stale relative to the working tree), and that
the frozen-tail guard was self-referential. This revision routes those modifications
through governance as a formal revision cycle (cycle 1 of 2).

## Scope of the approved diff (verified change-by-change)

1. **Disclosure diagnostics only — no binding change.** `pyramid_net_split` (F05
   disclosure), `seed_robustness` (F06 disclosure), per-instrument
   `headroom_cons_bps` / `net_cons_survives_nonbinding` columns (F01 disclosure),
   row-set fence count assertion in `reconcile_gross_excess`, and the
   `review_notes` block in run metadata. None of these touches the binding metric,
   cost table, event set, seeds, aggregation, or decision rule.
2. **`phase_outcome` rewrite** — verified behaviorally equivalent to the approved
   version for all reachable verdict combinations (the dropped clause was redundant:
   `decide_label` never returns `None` for a domain present in `DOMAINS`, and
   UNDER_POWERED exclusion is unchanged). Editing verdict-assembly code post-read is
   a process breach in form; it is accepted only because equivalence is verifiable
   and the re-run must reproduce the identical per-domain verdicts and
   `phase_outcome` (see re-run conditions).
3. **F02 fix:** frozen-tail guard now asserts against the pinned hash
   `e50873d12a9f68d9`, independently recomputed from
   `EXP-027/code/event_method.py` and git-verified unchanged since commit
   `5387a3b` (EXP-027/028 close-out). The previous self-comparing reload could not
   fail and is removed as the binding check.
4. **F07 fixes:** unused `tqdm` import removed; `attribution_companion.csv` now
   carries `binding=false` and `companion_label` (instead of `verdict`) so the
   non-binding companion's EVIDENCE_FOR labels cannot be grepped as a tradability
   verdict.
5. **F06 wording:** run-metadata `significance` field now states that the FOR
   criterion is effectively the bootstrap CI excluding zero (one-sided ≈0.025),
   Holm-screened, and that `boot_p` is a CI-equivalent annotation, not a
   null-calibrated p-value.

## Binding conditions of this APPROVE

- **Re-run required.** The experiment must be re-executed manually from the revised
  code so that results/metadata provenance matches the committed code. The re-run
  must reproduce, byte-identically, every binding output of the recorded run:
  per-domain CONSERVATIVE/BASE `effect_bps`, CIs, Holm-p, verdicts, reconciliation
  residuals, commute deviations, and `phase_outcome = INCONCLUSIVE`. Any deviation
  is a hard stop and a REVISE.
- **Read-once budget is consumed.** The binding net results have been read. No
  change to the cost table, variants, estimand, decision rule, or inference settings
  is admissible for EXP-030 under any future cycle — including changes motivated by
  the INCONCLUSIVE outcome. Remaining revision capacity (1 cycle) covers mechanical
  defects only.
- **Carry-forward to Stage 6/7 and any EXP-032 discussion (F04):** the INCONCLUSIVE
  binds the predeclared equal-weight cross-instrument estimand only. The
  per-instrument table (e.g. EURUSD-4h net_cons CI > 0) is descriptive and
  multiplicity-uncontrolled; no cell is promoted. A per-instrument tradability
  question requires a new pre-registered experiment with explicit multiplicity
  control.
- **Carry-forward to any EXP-032 admissibility argument (F05):** the cost model
  excludes financing/swap, which is duration-correlated and material on 1h/4h
  lifetime holds. Any future TRADABLE/holdout-release argument on those domains
  must first pass a separately scoped financing-inclusive net check.

## Pipeline state correction (F03)

The experiment is **not** at the pre-execution gate: execution occurred and results
were read. Post-re-run, the pipeline resumes at **Stage 5 (audit)**. The audit must
verify the re-run's byte-identity claim and the freeze evidence above.
