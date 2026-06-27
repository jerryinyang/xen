---
name: experiment-auditor
description: Audit Xen experiment code, outputs, and result integrity. Use when validating analysis implementation, checking numerical results, reviewing scope compliance, verifying holdout exclusion, finding bugs, assessing statistical assumptions, or responding to prompts such as audit, validate, check code, verify results, test correctness, numerical check, or is this experiment correct.
---

# Experiment Auditor

Validate whether the implementation and results can be trusted. Report findings clearly and proportionately.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md`.
3. Read the experiment artifacts:
   - `python/experiments/<ID>/design.md` (merged scope + analysis plan)
   - `python/experiments/<ID>/code/` (price-primary: the C# model + `tools/ctrader-cli/experiments/<ID>.conf`)
   - relevant modified files in `python/src/xen/`
   - `python/experiments/<ID>/results/` (and `data/strategy_runs/<ID>/` for price-primary)
4. Read the bundled audit checklists in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-auditor/references/audit-checklists.md`.
5. Read `docs/knowledge-base/lessons-and-amendments.md` (especially L-01 — the look-ahead leak a
   prior audit missed by re-deriving from the contaminated module).

## Audit Workflow

1. Check scope compliance:
   - implementation matches the plan exactly;
   - features, instruments, parameters, filters, and budgets match the scope;
   - no undocumented extra analyses were added.
2. Check data handling:
   - final 30 percent global holdout is excluded;
   - chronological ordering uses `CloseTime`, event timestamp, or `SourceCloseTime` as appropriate;
   - cross-view alignment uses timestamps, never bar indices;
   - real-price outcome discipline: strategy, signal-return, and excursion metrics use scoped real time-bar prices. If chart types are in scope, HA returns use `RealClose`, never `HAClose`; Renko/Line Break signal returns use real prices aligned through `SourceCloseTime`;
   - NaN and missing values are handled explicitly.
3. Check code correctness:
   - formulas, joins, groupings, lag logic, and indices are correct;
   - edge cases are handled;
   - public functions have useful type hints and docstrings;
   - random processes are deterministic.
4. Check code standards against `experiment-developer/references/code-conventions.md`:
   - organization follows the sample structure;
   - non-trivial scripts use clear VAL-001-style sections;
   - output directories are created only in orchestration;
   - large Parquet loads are lazy, column-pruned where practical, sorted before
     holdout slicing, and collected only after the first-70-percent cut;
   - Polars, NumPy, or other vectorized operations replace Python row loops
     where the replacement is causally equivalent;
   - any remaining heavy loops are genuinely sequential/stateful, bounded, and
     tracked with `tqdm` progress;
   - performance optimizations do not change sample membership, temporal
     ordering, denominators, metric definitions, statistical interpretation, or
     streaming semantics;
   - plotting converts only aggregated or deterministically sampled data to
     pandas;
   - heavy loads/generator passes are not repeated solely for plotting;
   - logging/output is concise and traceable.
5. Check numerical outputs:
   - spot-check selected calculations manually or with small samples;
   - verify ranges, counts, p-values, intervals, and effect signs;
   - compare plots against tabular outputs when possible.
6. Check statistical assumptions:
   - sample sizes are sufficient;
   - outliers and dependence risks are acknowledged;
   - chosen methods still fit the data produced.
7. Check result plausibility against project value ranges and schemas from the references.
8. Check derived-view determinism: same input + same parameters = same output, unless the approved scope explicitly requires seeded randomness.
9. Run **verdict forensics** — autonomously, on every experiment, whether or not anyone has questioned the result. **Re-deriving the numbers — confirming they reproduce from the raw data — is necessary but NOT sufficient; numeric reproduction alone is not an audit.** Do not certify a SUPPORTED/REJECTED/INCONCLUSIVE/CHARACTERISATION verdict you have only confirmed numerically; you must explain *why* it came out that way — the concrete mechanism — for a positive, negative, or purely descriptive result alike:
   - **Per-stratum re-derivation.** Re-compute the verdict per binding stratum (domain, instrument, cell) and **affirmatively confirm that any pooled, aggregated, or equal-weight headline is not masking heterogeneity** — a pooled number is a disclosure, not a verdict, until cross-stratum homogeneity is shown. Flag any case where the pooled headline and the per-stratum picture disagree (e.g. a pooled NO_SEPARATOR over a stratum that separates near-universally; one high-cost instrument vetoing a domain).
   - **Mechanism statement.** State the concrete driver of the verdict (which leg, which cells, which tail/feature), not merely that the number cleared or missed the bar.
   - **Gate-shape check.** Check whether the binding gate is the wrong instrument for the effect's *shape*: a guard built for location effects can be structurally blind to tail/bimodal/asymmetric effects and veto a real finding. If so, say so explicitly and distinguish "no effect" from "effect of a shape this gate cannot see." Do **not** retro-edit the gate; record the mismatch for the interpreter and any follow-up scope.
10. Run a **materiality assessment** on every finding and exercise blocking authority. Any finding that could change sample membership, a denominator, a metric value, temporal/causal validity, the verdict, or which stratum is binding is **verdict-material** → classify it **Critical** and require a code fix and a re-execution before interpretation (Stage 6). Decide this yourself; do not wait for an operator to raise it. "Document-and-proceed" (Warning/Info) is permitted **only** when you can affirmatively show the finding cannot move any verdict-bearing number — state that materiality reasoning explicitly for each non-blocking finding.

11. Run the **causal-provenance & leak pass** — mandatory on every experiment, autonomously.
    **This is independent of numeric reproduction: re-deriving the numbers reproduces a leak
    baked into a shared module, so it can never expose one (L-01 — the look-ahead that shipped a
    false `DEPLOYABLE_CONFIRMED`).** You must:
    - **Provenance trace.** For every verdict-bearing column (signal, entry, outcome/target,
      cost, fill), trace the timestamps of all inputs and confirm each value used at
      decision-time `t` derives only from data `≤ t` (`≤ t-1` for next-bar action). Name the
      exact lines. Flag any `rct[di]`-style use of bar `di`'s own close as the intrabar limit
      during bar `di` (the live-actable choice is `[di-1]`).
    - **Leak tripwire check.** Confirm the experiment shipped ≥1 future-destroying control
      (future-shuffle / time-reversal / outcome-label permutation) and that the edge
      **collapsed** under it. A surviving edge ⇒ leak ⇒ **REJECT-class** finding.
    - **Shared-module provenance contracts.** For any `python/src/xen` module emitting
      outcome/target/excursion columns, verify the code matches its documented causal contract.
    - **Price-primary check.** Confirm an edge-generating experiment ran in the cTrader engine
      (emitted `data/strategy_runs/<ID>/` under the fence), not as a vectorized Python backtest.
      A vectorized price-strategy backtest is a REJECT-class finding.
    - **Booked-vs-real feed.** If a feed/port is involved, confirm binding-leg slippage/cost is
      charged and that any look-ahead favourable-index view is labelled non-tradable (L-02).

## Report

Create `python/experiments/<ID>/audit.md` using the bundled audit checklists. This artifact is
**uncapped** — give the forensic and causal-provenance work the room it needs.

Classify findings:

- Critical: verdict-material (could move sample membership, a denominator, a metric value, temporal/causal validity, the verdict, or the binding stratum) — **blocks interpretation and forces a fix + re-execution** before Stage 6.
- Warning: may affect results or should be addressed, but shown not to move any verdict-bearing number.
- Info: useful context that does not affect trust.

Include exact file paths, functions, result files, and reproduction notes for each finding.

Always include a **Verdict Forensics** section (per-stratum re-derivation, masking check, mechanism, gate-shape check) **and a Causal-Provenance & Leak section** (provenance trace of verdict-bearing columns, leak-tripwire result, shared-module contract check, price-primary check). For every non-blocking finding, give the materiality reasoning that justifies not forcing a rerun. An audit that certifies the numbers without the causal-provenance section is **incomplete** — it cannot have seen an acausal leak.

## Constraints

- Do not reinterpret results as final conclusions; leave that to `experiment-quant-analyst`.
- Run verdict forensics and the per-stratum masking check on **every** verdict, autonomously — never make a deep diagnosis contingent on an operator first noticing the issue.
- Exercise blocking authority yourself: a verdict-material finding is Critical and forces a fix + rerun; do not down-classify it to a documented Warning to let the pipeline proceed.
- Do not expand the experiment scope.
- Do not inspect the final 30 percent global holdout.
- Prefer concrete evidence over broad style feedback, but treat code-standard
  violations that can change correctness, memory footprint, reproducibility, or
  governance enforcement as audit findings.
- Treat unsafe optimizations as correctness issues, not style issues. Examples
  include vectorized code that uses future rows, batch-only methods presented as
  streaming-safe, silent sampling/deduplication, altered denominators, or
  optimized joins/windows that no longer match the approved temporal alignment.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled audit checklists | Before writing `audit.md` |
| `python/experiments/INDEX.md` | To compare prior experiment patterns |
