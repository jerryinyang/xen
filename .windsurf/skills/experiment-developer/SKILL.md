---
name: experiment-developer
description: Implement approved Xen experiment designs as C# cTrader StrategyHost models with ctrader-cli configs. Use when implementing a design, creating or modifying an ISignalModel strategy, adding an experiment .conf, building emission columns, implementing engine-side controls or tripwires, or fixing implementation findings from QA — files under StrategyHost/, tools/ctrader-cli/, or python/src/xen. Trigger on implement, write code, build the model, code the strategy, add the conf, or fix the implementation.
---

# Experiment Developer

Translate an approved `design.md` into an engine implementation. Implement only the approved
design — and when the design is ambiguous, STOP and ask; never resolve ambiguity silently.

**Every experiment is price-primary (INFR-001).** All strategy logic — signals, entries,
exits, controls that need engine-side variants (e.g. shifted-feed twins) — is a C#
`ISignalModel` in `StrategyHost/`, run via `tools/ctrader-cli/run-experiment.sh`, emitting
`data/strategy_runs/<ID>/` under the `AnalysisEndUtc` fence. There is **no Python analysis
implementation in this role**: analysis of emitted data belongs to the `data-analyst`, who
writes their own code against the canonical `xen` library. The Python-side replication runs
this role used to build are abolished — they duplicated (and pre-empted) the analyst's job.

Python is in scope ONLY for: ingestion/validation helpers promoted into `python/src/xen`
(contract-reviewed, tested), and fixes to canonical `xen` modules requested through QA.

## Start

1. Read the shared pipeline config: the file ending `/research-pipeline/_pipeline-config.md`.
2. Read `python/experiments/<ID>/design.md` — including the golden-trace spec, tripwire(s),
   and emission column requirements.
3. Read `tools/ctrader-cli/README.md` (harness recipe) and an existing model
   (e.g. `DonchianBreakoutModel.cs`) as the structural template.
4. Read this skill's `references/code-conventions.md` for anything touching `python/src/xen`.

## Silent-deviation rule (binding — the A-1 fix)

Three consecutive experiments shipped verdict-material design-to-code drift silently
(frozen form-2 exit, moving-anchor TP, size-confounded placebo). Therefore:

- If any design requirement is ambiguous, unimplementable as written, or in tension with the
  engine's mechanics → **STOP and elicit the operator** before coding. Plain-language
  standard: one plain sentence per question, concrete options, one-line consequences,
  recommendation marked. No jargon walls.
- Any deviation you believe is forced must be (a) raised before implementation, (b) recorded
  in a `DEVIATIONS` block at the top of the model file and in your completion summary.
  An unrecorded deviation discovered later is a REJECT-class process violation.

## Implementation workflow

1. Map every design clause to a code location; keep the mapping — QA will trace it
   clause-by-clause in a fresh context.
2. Implement the C# model: `OnBar()` uses only current-and-past confirmed bars (`≤ t-1`
   conditioning is structural); decisions at bar open; native cTrader orders + m1 fills for
   limit strategies (StrategyHost self-fills on aggregated OHLC are not valid fills — L-14/
   EXP-013 NativeOrders).
3. Emit everything the design's estimand and the analyst need: per-leg ledger
   (`cis_trades.parquet` with fills, `RealizedBps`, `Censored`), per-bar state incl.
   `OpenLegs`, provenance columns. The emission must be sufficient for
   `xen.estimand_validation` to pass — run it on a smoke cell before handing off.
4. Register the model in the `Xen.cs` `XenStrategy` enum + `CreateStrategyModel()`; add
   `tools/ctrader-cli/experiments/<ID>.conf` (+ engine-side control variants, e.g. `-shift`).
5. Implement the design's leak tripwire variant(s).
6. **Do not generate the golden trace.** The design's golden-trace events are QA's diff
   material; producing "expected" values from your own implementation would make the check
   circular. Just ensure the emission contains the columns needed to evaluate them.

## Prohibitions

- No Python backtest, replication, or analysis of the strategy — REJECT-class.
- No accounting primitives in experiment dirs: `assemble_realized_bps` and successors live
  only in `xen.adjudication` (`check_no_local_accounting` gates this).
- No scope extension, no extra emissions/analyses beyond the design.
- No holdout contact; emissions end at the `AnalysisEndUtc` fence.
- No synthetic prices in any emitted outcome column.

## Completion summary

- files created/modified; conf names; how to run each cell;
- design-clause → code-location map (QA input);
- deviations raised and their resolutions (or "none");
- smoke-cell `xen.estimand_validation` result.

Execution itself is operator-gated: report ready-to-run; do not launch credentialed/
cost-bearing runs yourself.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config (`research-pipeline/_pipeline-config.md`) | Always |
| `python/experiments/<ID>/design.md` | Always |
| `tools/ctrader-cli/README.md` | Always |
| `references/code-conventions.md` (bundled) | Touching `python/src/xen` |
