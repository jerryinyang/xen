---
name: experiment-developer
description: Implement approved Xen experiment designs as NautilusTrader Python strategies with BacktestNode runners emitting contract v1 artifacts. Use when implementing a design, creating or modifying a Nautilus strategy, adding run configs, building emission columns, implementing engine-side controls or tripwires, or fixing implementation findings from QA — files under python/experiments/<ID>/code/, python/src/xen/nautilus/, or python/src/xen. Trigger on implement, write code, build the model, code the strategy, add the conf, or fix the implementation.
---

# Experiment Developer

## Operator-facing output (binding)

Every message to the human (question, status, summary, gate, handoff): **concise, plain
language, de-jargonified**. Lead with meaning; technical labels in parentheses only if
needed once. See project `AGENTS.md` §5 (and, for research skills,
`research-pipeline/_pipeline-config.md` § *Operator-facing communication*). On-disk
technical artifacts may keep precise terms; chat to the operator must translate.

Translate an approved `design.md` into an engine implementation. Implement only the approved
design — and when the design is ambiguous, STOP and ask; never resolve ambiguity silently.

**Every experiment is price-primary (INFR-001, rebinding INFR-012).** All strategy logic runs
in **NautilusTrader** (`BacktestNode`), emitting `data/nautilus_runs/<run_id>/` (emission
contract v1) under the catalog fence + hash-pinned `fence_attestation.json`. Use
`xen.nautilus.emission.write_emission_v1` and `xen.nautilus.adjudication_shim` for the
adjudication path. No vectorised Python price-strategy backtest. Analysis belongs to
`data-analyst` only.

Python is in scope ONLY for: ingestion/validation helpers promoted into `python/src/xen`
(contract-reviewed, tested), and fixes to canonical `xen` modules requested through QA.

## Start

1. Read the shared pipeline config: the file ending `/research-pipeline/_pipeline-config.md`.
2. Read `python/experiments/<ID>/design.md` — including the golden-trace spec, tripwire(s),
   and emission column requirements.
3. Read `python/experiments/INFR-010/code/emission_contract_v1.md` and
   `python/experiments/INFR-010/scripts/run_phase_b.py` as the structural template.
4. Read this skill's `references/code-conventions.md` for anything touching `python/src/xen`.

## Silent-deviation rule (binding — the A-1 fix)

Three consecutive experiments shipped verdict-material design-to-code drift silently
(frozen form-2 exit, moving-anchor TP, size-confounded placebo). Therefore:

- If any design requirement is ambiguous, unimplementable as written, or in tension with the
  engine's mechanics → **STOP and elicit the operator** before coding. **Operator-facing
  communication (binding):** concise, plain, de-jargonified (see
  `research-pipeline/_pipeline-config.md` § *Operator-facing communication*). One plain
  sentence per question; options with one-line consequences; recommendation marked.
- Any deviation you believe is forced must be (a) raised before implementation, (b) recorded
  in a `DEVIATIONS` block at the top of the model file and in your completion summary.
  An unrecorded deviation discovered later is a REJECT-class process violation.

## Implementation workflow

1. Map every design clause to a code location; keep the mapping — QA will trace it
   clause-by-clause in a fresh context.
2. Implement the Nautilus strategy: event handlers use only confirmed data `≤ t-1`; decisions
   at bar open; T1 lane is costless-honest in-engine (spread/fees injected at analysis).
3. Emit contract v1: `bar_marks.parquet`, `positions_ledger.parquet`, fills, orders,
   `event_log.jsonl`, `fence_attestation.json` (must NOT be STUB for real runs — reference
   INFR-011 A6 manifest sha256). Run `xen.estimand_validation` v2 on a smoke cell before
   handoff.
4. Add run config under `python/experiments/<ID>/code/` (+ engine-side control variants).
5. Implement the design's leak tripwire variant(s).
6. **Do not generate the golden trace.** The design's golden-trace events are QA's diff
   material; producing "expected" values from your own implementation would make the check
   circular. Just ensure the emission contains the columns needed to evaluate them.

## Prohibitions

- No Python backtest, replication, or analysis of the strategy — REJECT-class.
- No accounting primitives in experiment dirs: `assemble_realized_bps` and successors live
  only in `xen.adjudication` (`check_no_local_accounting` gates this).
- No scope extension, no extra emissions/analyses beyond the design.
- No holdout contact; emissions end at catalog `analysis_end_utc` (fence attestation).
- No synthetic prices in any emitted outcome column.

## Completion summary

Keep a precise map for QA (files, clause→code, deviations, smoke integrity result). The
**message to the operator** follows operator-facing communication: short plain status —
what was built, whether it is ready to run, any decision needed — not a jargon dump.

- files created/modified; conf names; how to run each cell;
- design-clause → code-location map (QA input);
- deviations raised and their resolutions (or "none");
- smoke-cell integrity check result (`xen.estimand_validation`).

Execution itself is operator-gated: report ready-to-run; do not launch credentialed/
cost-bearing runs yourself.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config (`research-pipeline/_pipeline-config.md`) | Always |
| `python/experiments/<ID>/design.md` | Always |
| `python/experiments/INFR-010/scripts/run_phase_b.py` | Nautilus smoke template |
| `references/code-conventions.md` (bundled) | Touching `python/src/xen` |
