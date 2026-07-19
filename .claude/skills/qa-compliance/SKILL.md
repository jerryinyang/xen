---
name: qa-compliance
description: Fresh-context pre-execution review of a Xen experiment — clause-by-clause design-to-code fidelity trace, governance compliance, and shared-code boundary checks, producing an append-only qa-review.md. Use when reviewing an implementation before execution, running QA, checking design-to-code fidelity, pre-exec review, compliance review, or verifying an experiment is ready to run. MUST run in a fresh context (new session or dedicated subagent) — refuse if this conversation already contains the implementation work.
---

# QA / Compliance (pre-execution, fresh context)

Independent pre-execution reviewer. Exists because three consecutive experiments shipped
verdict-material design-to-code drift through same-session review (A-1, INFR-001): a reviewer
who watched the code being written already "knows" it is right. Independence here is
structural, not attitudinal.

## Fresh-context requirement (binding)

- This skill runs ONLY in a context that did not produce the implementation: either the
  operator invokes it in a **new session**, or the orchestrator spawns it as a **subagent**.
- **Self-check before starting:** if this conversation contains the implementation of the
  experiment under review (its diffs, its development discussion), STOP and refuse:
  "QA requires a fresh context. Spawn me as a subagent or run me in a new session."
- Record the run mode in the review header: `mode: operator-session | subagent`, timestamp,
  and reviewed git state (`git rev-parse HEAD` + dirty-file list).
- **Rerunnable:** the operator may run QA any number of times pre-execution. `qa-review.md`
  is append-only — each run adds a dated section; never rewrite a previous run's findings.
- Execution remains the operator's gate: QA APPROVE does not launch anything.

## Inputs

1. `python/experiments/<ID>/design.md` (with its GATE/approval state).
2. The implementation: Nautilus strategy/runner under `python/experiments/<ID>/code/`,
   emission contract v1 artifacts, any `python/src/xen` changes.
3. Shared pipeline config (file ending `/research-pipeline/_pipeline-config.md`) and
   `research-pipeline/references/governance-constraints.md`.
4. The developer's design-clause → code-location map (from the completion summary), if
   present — verify it, do not trust it.

## Review protocol

### 1. Design-fidelity trace (the core — A-1 fix)

Clause-by-clause: every design requirement (entries, exits, parameters, tripwires, emission
columns, cells) → the code lines implementing it → verdict MATCHES / DEVIATES / MISSING.
Derive expected behaviour **from the design text**, then read the code — not the reverse.
Table format:

| Design clause (§ref) | Code (file:line) | Verdict | Notes |

Special attention to the three shipped failure shapes: an exit that never updates (frozen
computation), a reference that moves when the design says fixed (anchor drift), a comparator
that differs from the design's control in size/population (confounded placebo).

### 2. Golden-trace diff

Evaluate the design's golden-trace events against the implementation logic by hand (and
against a smoke emission if one exists). Expected values come from the DESIGN, never from
running the implementation to produce its own expectations.

### 3. Governance & boundary checks

- design.md contains all mandatory declaration blocks (`quant-designer/references/
  design-requirements.md`): mechanism, object-identity, control validity proofs, tripwire,
  bands, power, golden trace, hard/informative split.
- `check_no_local_accounting("python/experiments/<ID>/code")` passes; no accounting
  primitives outside `xen.adjudication`.
- No Python strategy backtest anywhere in the experiment.
- Registry preconditions (family registered; any planned counted TEST read states the tally).
- Screen-effect conversion pin (L-21): if the design cites SPDR/screen evidence in money
  units, the `CONVERSION-PIN` block exists and each line is verified against data — divisor
  object matches the screen code verbatim, the measured TRAIN-median value is recomputed (not
  recalled), the resulting bps/trade effect and cost-floor comparison follow arithmetically;
  §5 bands and §6 power use the pinned effect (`docs/references/spdr-lane.md`).
- T1 spread-scale routing (INFR-010 §4): design must declare `SPREAD-SCALE-ROUTING`; if
  `t1_undecidable: YES`, tradability/SUPPORTED bands on T1 alone are a REVISE.
- Spread verdict leg (L-22, chapter 04): binds on `bybit_round_trip_cost_bps` (fees + 1×
  pseudo-quote spread + funding); FTMO table only for archived VAL re-analysis.
- Amendment-direction ledger (L-23): every pre-measurement amendment carries a
  LOOSER/TIGHTER/NEUTRAL declaration + running directional count; the final gate set carries
  a re-derived false-qualifier expectation; a one-directional streak ≥3 is flagged to the
  operator at the execution gate.
- XENA VOID on new stack (INFR-010 R4): any design routing to XENA on Bybit/crypto data
  without a post-CAL hash-pinned registry is a REJECT (chapter-03 pins are archive-only).
- Battery/eligibility/null rules (L-24): for any battery-gated, multi-cell, or capped-read
  design, trace the four clauses of `quant-designer/references/design-requirements.md` §12 —
  time-stability eligibility, exit-matched nulls, derived tripwire thresholds,
  MDE-consistent read floors.
- Derangement destroy (L-28): any permutation-based leak tripwire, attribution control, or
  null battery arm must be a **derangement** (zero fixed points) — plain permutations leak
  signal (VAL-008: 11.1% alignment → collapse 0.87). Design CONTROL/TRIPWIRE block states
  `destroy form: DERANGEMENT`; code regenerates/rejects draws with fixed points. Missing
  derangement on a permutation destroy = REVISE.
- One BacktestNode per process (L-31): multi-cell runners must be **subprocess-per-cell** (or
  equivalent process boundary). A design/runner that constructs a second `BacktestNode` in the
  same process (Rust logging init panic) = REVISE. Multi-instrument single-engine is unproven
  until INFR-014 smoke S1.
- Holdout: no code path can touch the final 30%; conf fence set.
- Any `DEVIATIONS` block: each deviation was operator-approved (evidence, not assertion).
- **Operator-facing communication (binding):** questions, status, and the APPROVE/REVISE/REJECT
  summary to the human are concise and de-jargonified (see
  `research-pipeline/_pipeline-config.md` § *Operator-facing communication*). Plain meaning
  first; issues listed as what is wrong + what must change; technical file:line detail may
  stay in `qa-review.md` tables.
- **XENA runs (INFR-006 clauses; spec `docs/references/xena-lane.md`):** (a) frozen
  registry verified — `xen.xena.calibration.verify_frozen_registry` passes and the run's
  thresholds/params match the pinned values byte-for-byte (any mismatch = REJECT: frozen
  values are never re-derived per run); (b) every candidate leg carries finite `SlPrice`
  and the universe's `xena_candidate_gate.json` is passing and non-stale; (c) band
  boundaries (search/ranking/gate) are pre-registered in the run design and folds do not
  overlap the search band; (d) `new_data_attestation` appears ONLY as an operator-supplied
  string — an agent-authored attestation is a REJECT; (e) gate ledger state checked before
  any gate approval (cap 2/universe; identical-failed-subset rule).

### 4. Verdict

- **APPROVE** — ready for the operator's execution gate.
- **REVISE** — enumerated issues, each with design §, code line, and required change; route
  to `experiment-developer` (implementation) or `quant-designer` (design defect).
- **REJECT** — fundamental (holdout contact, causality violation, unapproved silent
  deviation, missing tripwire). Cannot be overridden in-session; goes to the operator.

When reporting the verdict in chat: one plain line for the result, then the few issues that
block progress in ordinary language (detail stays in `qa-review.md`).

## Output — `python/experiments/<ID>/qa-review.md` (append-only)

```markdown
## QA run <n> — <UTC timestamp> — mode: <operator-session|subagent> — HEAD <sha>
Verdict: APPROVE | REVISE | REJECT
### Design-fidelity trace
<table>
### Golden-trace diff
<events, expected (from design) vs implemented logic, verdict each>
### Governance & boundary
<checklist with evidence>
### Issues
<numbered, severity, design§ + file:line + required change>
```

## Constraints

- Read-only: QA never edits implementation or design files.
- Pre-execution only; post-run evidence quality belongs to the `data-analyst`.
- Experiment-level only; no family or registry status changes.
- Verify claims independently — the developer's summary is a map to check, not evidence.
